#!/usr/bin/env python3
"""Patch to add NAV fetching to zerodha_api.py"""

# Read the current file
with open('src/mfa/scraping/zerodha_api.py', 'r') as f:
    content = f.read()

# Define the new NAV method
nav_method = '''
    def _fetch_current_nav(self, fund_id: str) -> float:
        """
        Fetch current NAV for a fund from Zerodha historical NAV API.

        Args:
            fund_id: Fund identifier (e.g., 'INF204K01XI3')

        Returns:
            Current NAV value as float

        Raises:
            ZerodhaAPIError: If NAV request fails
        """
        nav_url = f"https://staticassets.zerodha.com/coin/historical-nav/{fund_id}.json"

        try:
            http_client = self._get_http_client()
            response_data = http_client.get_json(nav_url)

            # Validate NAV response
            if response_data.get("status") != "success":
                raise ZerodhaAPIError(f"NAV API returned error status for fund {fund_id}")

            nav_data = response_data.get("data", [])
            if not nav_data:
                raise ZerodhaAPIError(f"No NAV data found for fund {fund_id}")

            # Get the latest NAV (last entry in array)
            latest_entry = nav_data[-1]
            if len(latest_entry) < 2:
                raise ZerodhaAPIError(f"Invalid NAV data format for fund {fund_id}")

            current_nav = float(latest_entry[1])
            timestamp = int(latest_entry[0])
            
            # Convert timestamp to readable date for logging
            from datetime import datetime
            nav_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            
            logger.debug(f"💰 Fetched NAV for {fund_id}: ₹{current_nav} (as of {nav_date})")
            return current_nav

        except HTTPClientError as e:
            logger.warning(f"⚠️ Failed to fetch NAV for {fund_id}: {e}")
            return 0.0  # Return 0 if NAV fetch fails, will fallback to units calculation
        except (ValueError, IndexError) as e:
            logger.warning(f"⚠️ Invalid NAV data for {fund_id}: {e}")
            return 0.0
'''

# Insert before the close method
close_method_pos = content.find('    def close(self) -> None:')
if close_method_pos != -1:
    new_content = content[:close_method_pos] + nav_method + '\n' + content[close_method_pos:]
    
    # Write back to file
    with open('src/mfa/scraping/zerodha_api.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Added NAV fetching method to zerodha_api.py")
else:
    print("❌ Could not find insertion point")
