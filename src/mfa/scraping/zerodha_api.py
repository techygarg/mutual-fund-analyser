"""
Zerodha API-based mutual fund scraper.

This module provides API-based scraping for Zerodha Coin mutual fund data,
offering a faster and more reliable alternative to Playwright-based scraping.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from loguru import logger
from pydantic import HttpUrl

from mfa.core.schemas import ExtractedFundDocument, FundData, FundInfo, TopHolding
from mfa.scraping.http_client import HTTPClient, HTTPClientError


class ZerodhaAPIFundScraper:
    """
    API-based scraper for Zerodha Coin mutual fund data.

    Uses Zerodha's static assets API to fetch fund holdings data directly,
    providing faster and more reliable data extraction than browser automation.
    """

    API_BASE_URL = "https://staticassets.zerodha.com/coin/scheme-portfolio"

    def __init__(self, delay_between_requests: float = 1.0) -> None:
        """
        Initialize API scraper.

        Args:
            delay_between_requests: Delay between API requests in seconds
        """
        self.delay_between_requests = delay_between_requests
        self._http_client: HTTPClient | None = None

    def _get_http_client(self) -> HTTPClient:
        """Get or create HTTP client instance."""
        if self._http_client is None:
            self._http_client = HTTPClient(timeout=30, max_retries=3, backoff_factor=0.5)
        return self._http_client

    def scrape(
        self,
        url: str,
        max_holdings: int = 50,
        storage_config: dict[str, Any] | None = None,
    ) -> ExtractedFundDocument:
        """
        Scrape mutual fund data using Zerodha API.

        Args:
            url: Zerodha Coin fund URL
            max_holdings: Maximum number of holdings to extract
            storage_config: Storage configuration (optional)

        Returns:
            Extracted fund document

        Raises:
            ZerodhaAPIError: If scraping fails
        """
        try:
            logger.debug(f"🌐 Starting API scrape for: {url}")

            # Extract fund ID from URL
            fund_id = self._extract_fund_id_from_url(url)
            logger.debug(f"📊 Extracted fund ID: {fund_id}")

            # Fetch data from API
            api_data = self._fetch_fund_data_from_api(fund_id)

            # Fetch current NAV
            current_nav = self._fetch_current_nav(fund_id)

            # Transform to standard format
            fund_name, metadata, holdings = self._transform_api_data(
                api_data, max_holdings, url, current_nav
            )

            # Build document
            document = self._build_document(url, fund_name, metadata, holdings, storage_config)

            logger.info(f"✅ Successfully scraped {len(holdings)} holdings via API")
            return document

        except Exception as e:
            logger.error(f"❌ API scraping failed for {url}: {e}")
            raise ZerodhaAPIError(f"Failed to scrape {url}") from e

    def _extract_fund_id_from_url(self, url: str) -> str:
        """
        Extract fund ID from Zerodha Coin URL.

        Args:
            url: Zerodha Coin fund URL

        Returns:
            Fund ID (e.g., 'INF204K01XI3')

        Raises:
            ZerodhaAPIError: If fund ID cannot be extracted
        """
        # Pattern: https://coin.zerodha.com/mf/fund/INF204K01XI3/fund-name
        pattern = r"/fund/([A-Z0-9]+)/"
        match = re.search(pattern, url)

        if not match:
            raise ZerodhaAPIError(f"Cannot extract fund ID from URL: {url}")

        fund_id = match.group(1)
        logger.debug(f"🔍 Extracted fund ID '{fund_id}' from URL")
        return fund_id

    def _extract_fund_name_from_url(self, url: str) -> str:
        """
        Extract and format fund name from Zerodha Coin URL.

        Args:
            url: Zerodha Coin fund URL

        Returns:
            Formatted fund name (e.g., "HDFC Large Cap Fund")
        """
        # Pattern: https://coin.zerodha.com/mf/fund/INF204K01XI3/fund-name-slug
        pattern = r"/fund/[A-Z0-9]+/(.+?)(?:\?|$)"
        match = re.search(pattern, url)

        if not match:
            logger.warning(f"⚠️ Could not extract fund name from URL: {url}")
            return "Unknown Fund"

        fund_name_slug = match.group(1)

        # Convert slug to proper fund name
        # e.g., "hdfc-large-cap-fund-direct-growth" -> "HDFC Large Cap Fund Direct Growth"
        words = fund_name_slug.replace("-", " ").split()
        formatted_name = " ".join(word.capitalize() for word in words)

        # Remove "Direct Growth" suffix for cleaner name
        formatted_name = re.sub(r"\s*Direct\s*Growth\s*$", "", formatted_name, flags=re.IGNORECASE)

        logger.debug(f"🏷️ Extracted fund name: '{formatted_name}' from slug: '{fund_name_slug}'")
        return formatted_name

    def _fetch_fund_data_from_api(self, fund_id: str) -> dict[str, Any]:
        """
        Fetch fund data from Zerodha API.

        Args:
            fund_id: Fund identifier

        Returns:
            API response data

        Raises:
            ZerodhaAPIError: If API request fails
        """
        api_url = f"{self.API_BASE_URL}/{fund_id}.json"

        try:
            http_client = self._get_http_client()
            response_data = http_client.get_json_with_delay(
                api_url, delay=self.delay_between_requests
            )

            # Validate API response
            if response_data.get("status") != "success":
                raise ZerodhaAPIError(f"API returned error status for fund {fund_id}")

            if "data" not in response_data:
                raise ZerodhaAPIError(f"API response missing data field for fund {fund_id}")

            logger.debug(f"✅ Successfully fetched API data for fund {fund_id}")
            return response_data

        except HTTPClientError as e:
            raise ZerodhaAPIError(f"HTTP request failed for fund {fund_id}: {e}") from e

    def _transform_api_data(
        self, api_data: dict[str, Any], max_holdings: int, source_url: str, current_nav: float = 0.0
    ) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        """
        Transform API response to standard format.

        Args:
            api_data: Raw API response
            max_holdings: Maximum holdings to extract
            source_url: Source URL to extract fund name from

        Returns:
            Tuple of (fund_name, metadata, holdings)
        """
        holdings_data = api_data.get("data", [])
        logger.debug(f"📊 Processing {len(holdings_data)} holdings from API")

        # Extract fund name from URL
        fund_name = self._extract_fund_name_from_url(source_url)

        # Build metadata with current NAV
        metadata = {
            "current_nav": str(current_nav) if current_nav > 0 else "",
            "cagr": "",
            "expense_ratio": "",
            "aum": "",
            "fund_manager": "",
            "launch_date": "",
            "risk_level": "",
        }

        # Transform holdings
        holdings = []
        rank = 1

        for item in holdings_data:
            if len(item) < 8:
                logger.warning(f"⚠️ Skipping malformed holding: {item}")
                continue

            # Extract fields from API array
            # [unit, company_name, sector, asset_type, shares, percentage, value_crores, empty]
            company_name = item[1]
            sector = item[2]
            asset_type = item[3]
            percentage = item[5]

            # Only include equity holdings
            if asset_type != "Equity":
                continue

            # Skip empty or invalid entries
            if not company_name or company_name.strip() == "":
                continue

            holdings.append(
                {
                    "rank": rank,
                    "company_name": company_name,
                    "allocation_percentage": f"{percentage}%",
                    "sector": sector,  # Additional field from API
                }
            )

            rank += 1

            # Respect max_holdings limit
            if len(holdings) >= max_holdings:
                break

        logger.debug(f"✅ Transformed {len(holdings)} holdings (max: {max_holdings})")
        return fund_name, metadata, holdings

    def _build_document(
        self,
        url: str,
        fund_name: str,
        metadata: dict[str, Any],
        holdings: list[dict[str, Any]],
        storage_config: dict[str, Any] | None = None,
    ) -> ExtractedFundDocument:
        """
        Build standardized fund document.

        Args:
            url: Source URL
            fund_name: Fund name
            metadata: Fund metadata
            holdings: Holdings data
            storage_config: Storage configuration

        Returns:
            Standardized fund document
        """
        # Convert to schema objects
        fund_info = FundInfo(
            fund_name=fund_name,
            current_nav=metadata.get("current_nav", ""),
            cagr=metadata.get("cagr", ""),
            expense_ratio=metadata.get("expense_ratio", ""),
            aum=metadata.get("aum", ""),
            fund_manager=metadata.get("fund_manager", ""),
            launch_date=metadata.get("launch_date", ""),
            risk_level=metadata.get("risk_level", ""),
        )

        top_holdings = [
            TopHolding(
                rank=h["rank"],
                company_name=h["company_name"],
                allocation_percentage=h["allocation_percentage"],
            )
            for h in holdings
        ]

        fund_data = FundData(fund_info=fund_info, top_holdings=top_holdings)

        document = ExtractedFundDocument(
            schema_version="1.0",
            extraction_timestamp=datetime.now(),
            source_url=HttpUrl(url),
            provider="zerodha-api",
            data=fund_data,
        )

        # Save if storage config provided
        if storage_config and storage_config.get("should_save", False):
            self._save_document(document, storage_config)

        return document

    def _save_document(
        self, document: ExtractedFundDocument, storage_config: dict[str, Any]
    ) -> None:
        """Save document to file using storage configuration."""
        from mfa.config.settings import ConfigProvider
        from mfa.storage.json_store import JsonStore
        from mfa.storage.path_generator import PathGenerator

        try:
            # Generate file path
            config_provider = ConfigProvider()
            path_generator = PathGenerator(config_provider)
            file_path = path_generator.generate_scraped_data_path(
                url=str(document.source_url),
                category=storage_config.get("category", ""),
                analysis_config=storage_config,
            )

            # Save document
            store = JsonStore()
            store.save(document.model_dump(mode="json"), file_path)

            logger.debug(f"💾 Saved API document to: {file_path}")

        except Exception as e:
            logger.error(f"❌ Failed to save document: {e}")

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

            nav_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

            logger.debug(f"💰 Fetched NAV for {fund_id}: ₹{current_nav} (as of {nav_date})")
            return current_nav

        except HTTPClientError as e:
            logger.warning(f"⚠️ Failed to fetch NAV for {fund_id}: {e}")
            return 0.0  # Return 0 if NAV fetch fails, will fallback to units calculation
        except (ValueError, IndexError) as e:
            logger.warning(f"⚠️ Invalid NAV data for {fund_id}: {e}")
            return 0.0

    def close(self) -> None:
        """Close HTTP client and clean up resources."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None


class ZerodhaAPIError(Exception):
    """Exception raised by Zerodha API scraper."""

    def __init__(self, message: str) -> None:
        """Initialize with error message."""
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation of the error."""
        return self.message
