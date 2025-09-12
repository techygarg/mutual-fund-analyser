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
from mfa.scraping.core.http_client import HTTPClient, HTTPClientError


class ZerodhaAPIFundScraper:
    """
    API-based scraper for Zerodha Coin mutual fund data.

    Uses Zerodha's static assets API to fetch fund holdings data directly,
    providing faster and more reliable data extraction than browser automation.
    """

    # API Configuration
    API_BASE_URL = "https://staticassets.zerodha.com/coin/scheme-portfolio"
    NAV_API_BASE_URL = "https://staticassets.zerodha.com/coin/historical-nav"

    # HTTP Client Configuration
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 0.5

    # Response Validation
    SUCCESS_STATUS = "success"
    REQUIRED_API_FIELDS = 8  # Minimum fields in holdings array
    DATA_FIELD = "data"

    # Asset Filtering
    EQUITY_ASSET_TYPE = "Equity"

    # Fund URL Patterns
    FUND_ID_PATTERN = r"/fund/([A-Z0-9]+)/"
    FUND_NAME_PATTERN = r"/fund/[A-Z0-9]+/(.+?)(?:\?|$)"

    # Holdings Data Indices (API response array positions)
    HOLDINGS_COMPANY_NAME_IDX = 1
    HOLDINGS_SECTOR_IDX = 2
    HOLDINGS_ASSET_TYPE_IDX = 3
    HOLDINGS_PERCENTAGE_IDX = 5

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
            self._http_client = self._initialize_http_client()
        return self._http_client

    def _initialize_http_client(self) -> HTTPClient:
        """Initialize HTTP client with standardized settings."""
        return HTTPClient(
            timeout=self.DEFAULT_TIMEOUT,
            max_retries=self.DEFAULT_MAX_RETRIES,
            backoff_factor=self.DEFAULT_BACKOFF_FACTOR,
        )

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

            # Extract fund ID and fetch data
            fund_id = self._extract_fund_id_from_url(url)
            api_data, current_nav = self._fetch_all_fund_data(fund_id)

            # Transform and build document
            fund_name, metadata, holdings = self._transform_api_data(
                api_data, max_holdings, url, current_nav
            )
            document = self._build_document(url, fund_name, metadata, holdings, storage_config)

            logger.info(f"✅ Successfully scraped {len(holdings)} holdings via API")
            return document

        except Exception as e:
            logger.error(f"❌ API scraping failed for {url}: {e}")
            raise ZerodhaAPIError(f"Failed to scrape {url}") from e

    def _fetch_all_fund_data(self, fund_id: str) -> tuple[dict[str, Any], float]:
        """
        Fetch both holdings and NAV data for a fund.

        Args:
            fund_id: Fund identifier

        Returns:
            Tuple of (api_data, current_nav)
        """
        # Fetch data from API
        api_data = self._fetch_fund_data_from_api(fund_id)

        # Fetch current NAV
        current_nav = self._fetch_current_nav(fund_id)

        return api_data, current_nav

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
        match = re.search(self.FUND_ID_PATTERN, url)

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
        match = re.search(self.FUND_NAME_PATTERN, url)

        if not match:
            logger.warning(f"⚠️ Could not extract fund name from URL: {url}")
            return "Unknown Fund"

        fund_name_slug = match.group(1)
        formatted_name = self._format_fund_name_from_slug(fund_name_slug)

        logger.debug(f"🏷️ Extracted fund name: '{formatted_name}' from slug: '{fund_name_slug}'")
        return formatted_name

    def _format_fund_name_from_slug(self, fund_name_slug: str) -> str:
        """
        Format fund name slug into proper fund name.

        Args:
            fund_name_slug: URL slug (e.g., "hdfc-large-cap-fund-direct-growth")

        Returns:
            Formatted fund name (e.g., "HDFC Large Cap Fund")
        """
        # Convert slug to proper fund name
        # e.g., "hdfc-large-cap-fund-direct-growth" -> "HDFC Large Cap Fund Direct Growth"
        words = fund_name_slug.replace("-", " ").split()
        formatted_name = " ".join(word.capitalize() for word in words)

        # Remove "Direct Growth" suffix for cleaner name
        formatted_name = re.sub(r"\s*Direct\s*Growth\s*$", "", formatted_name, flags=re.IGNORECASE)

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
            self._validate_api_response(response_data, fund_id)

            logger.debug(f"✅ Successfully fetched API data for fund {fund_id}")
            return response_data

        except HTTPClientError as e:
            raise ZerodhaAPIError(f"HTTP request failed for fund {fund_id}: {e}") from e

    def _validate_api_response(self, response_data: dict[str, Any], fund_id: str) -> None:
        """
        Validate API response structure and status.

        Args:
            response_data: API response data
            fund_id: Fund identifier for error context

        Raises:
            ZerodhaAPIError: If response is invalid
        """
        if response_data.get("status") != self.SUCCESS_STATUS:
            raise ZerodhaAPIError(f"API returned error status for fund {fund_id}")

        if self.DATA_FIELD not in response_data:
            raise ZerodhaAPIError(f"API response missing data field for fund {fund_id}")

    def _transform_api_data(
        self, api_data: dict[str, Any], max_holdings: int, source_url: str, current_nav: float = 0.0
    ) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        """
        Transform API response to standard format.

        Args:
            api_data: Raw API response
            max_holdings: Maximum holdings to extract
            source_url: Source URL to extract fund name from
            current_nav: Current NAV value

        Returns:
            Tuple of (fund_name, metadata, holdings)
        """
        holdings_data = api_data.get(self.DATA_FIELD, [])
        logger.debug(f"📊 Processing {len(holdings_data)} holdings from API")

        # Extract fund name from URL
        fund_name = self._extract_fund_name_from_url(source_url)

        # Build metadata
        metadata = self._build_metadata(current_nav)

        # Transform holdings
        holdings = self._process_holdings_data(holdings_data, max_holdings)

        logger.debug(f"✅ Transformed {len(holdings)} holdings (max: {max_holdings})")
        return fund_name, metadata, holdings

    def _build_metadata(self, current_nav: float) -> dict[str, Any]:
        """
        Build fund metadata dictionary.

        Args:
            current_nav: Current NAV value

        Returns:
            Metadata dictionary with standardized fields
        """
        return {
            "current_nav": str(current_nav) if current_nav > 0 else "",
            "cagr": "",
            "expense_ratio": "",
            "aum": "",
            "fund_manager": "",
            "launch_date": "",
            "risk_level": "",
        }

    def _process_holdings_data(
        self, holdings_data: list[Any], max_holdings: int
    ) -> list[dict[str, Any]]:
        """
        Process raw holdings data into standardized format.

        Args:
            holdings_data: Raw holdings data from API
            max_holdings: Maximum holdings to extract

        Returns:
            List of processed holdings
        """
        holdings = []
        rank = 1

        for item in holdings_data:
            if not self._validate_holdings_item(item):
                continue

            if not self._should_include_holding(item):
                continue

            holding_dict = self._create_holding_dict(item, rank)
            holdings.append(holding_dict)

            rank += 1

            # Respect max_holdings limit
            if len(holdings) >= max_holdings:
                break

        return holdings

    def _validate_holdings_item(self, item: list[Any]) -> bool:
        """
        Validate holdings item structure.

        Args:
            item: Holdings item from API

        Returns:
            True if item is valid for processing
        """
        if len(item) < self.REQUIRED_API_FIELDS:
            logger.warning(f"⚠️ Skipping malformed holding: {item}")
            return False
        return True

    def _should_include_holding(self, item: list[Any]) -> bool:
        """
        Check if holding should be included in results.

        Args:
            item: Holdings item from API

        Returns:
            True if holding should be included
        """
        # Extract fields from API array
        company_name = item[self.HOLDINGS_COMPANY_NAME_IDX]
        asset_type = item[self.HOLDINGS_ASSET_TYPE_IDX]

        # Only include equity holdings
        if asset_type != self.EQUITY_ASSET_TYPE:
            return False

        # Skip empty or invalid entries
        if not company_name or company_name.strip() == "":
            return False

        return True

    def _create_holding_dict(self, item: list[Any], rank: int) -> dict[str, Any]:
        """
        Create holding dictionary from API item.

        Args:
            item: Holdings item from API
            rank: Rank position

        Returns:
            Standardized holding dictionary
        """
        # Extract fields from API array
        # [unit, company_name, sector, asset_type, shares, percentage, value_crores, empty]
        company_name = item[self.HOLDINGS_COMPANY_NAME_IDX]
        sector = item[self.HOLDINGS_SECTOR_IDX]
        percentage = item[self.HOLDINGS_PERCENTAGE_IDX]

        return {
            "rank": rank,
            "company_name": company_name,
            "allocation_percentage": f"{percentage}%",
            "sector": sector,  # Additional field from API
        }

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
        fund_info = self._create_fund_info(fund_name, metadata)
        top_holdings = self._create_top_holdings(holdings)
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

    def _create_fund_info(self, fund_name: str, metadata: dict[str, Any]) -> FundInfo:
        """
        Create FundInfo object from fund data.

        Args:
            fund_name: Fund name
            metadata: Fund metadata

        Returns:
            FundInfo schema object
        """
        return FundInfo(
            fund_name=fund_name,
            current_nav=metadata.get("current_nav", ""),
            cagr=metadata.get("cagr", ""),
            expense_ratio=metadata.get("expense_ratio", ""),
            aum=metadata.get("aum", ""),
            fund_manager=metadata.get("fund_manager", ""),
            launch_date=metadata.get("launch_date", ""),
            risk_level=metadata.get("risk_level", ""),
        )

    def _create_top_holdings(self, holdings: list[dict[str, Any]]) -> list[TopHolding]:
        """
        Create TopHolding objects from holdings data.

        Args:
            holdings: Holdings data

        Returns:
            List of TopHolding schema objects
        """
        return [
            TopHolding(
                rank=h["rank"],
                company_name=h["company_name"],
                allocation_percentage=h["allocation_percentage"],
            )
            for h in holdings
        ]

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
        nav_url = f"{self.NAV_API_BASE_URL}/{fund_id}.json"

        try:
            http_client = self._get_http_client()
            response_data = http_client.get_json(nav_url)

            # Validate NAV response
            self._validate_nav_response(response_data, fund_id)

            # Extract latest NAV
            current_nav, nav_date = self._extract_latest_nav(response_data, fund_id)

            logger.debug(f"💰 Fetched NAV for {fund_id}: ₹{current_nav} (as of {nav_date})")
            return current_nav

        except HTTPClientError as e:
            logger.warning(f"⚠️ Failed to fetch NAV for {fund_id}: {e}")
            return 0.0  # Return 0 if NAV fetch fails, will fallback to units calculation
        except (ValueError, IndexError) as e:
            logger.warning(f"⚠️ Invalid NAV data for {fund_id}: {e}")
            return 0.0

    def _validate_nav_response(self, response_data: dict[str, Any], fund_id: str) -> None:
        """
        Validate NAV API response.

        Args:
            response_data: NAV API response
            fund_id: Fund identifier for error context

        Raises:
            ZerodhaAPIError: If response is invalid
        """
        if response_data.get("status") != self.SUCCESS_STATUS:
            raise ZerodhaAPIError(f"NAV API returned error status for fund {fund_id}")

        nav_data = response_data.get(self.DATA_FIELD, [])
        if not nav_data:
            raise ZerodhaAPIError(f"No NAV data found for fund {fund_id}")

    def _extract_latest_nav(self, response_data: dict[str, Any], fund_id: str) -> tuple[float, str]:
        """
        Extract latest NAV value and date from response.

        Args:
            response_data: NAV API response
            fund_id: Fund identifier for error context

        Returns:
            Tuple of (current_nav, nav_date)

        Raises:
            ZerodhaAPIError: If NAV data is invalid
        """
        nav_data = response_data.get(self.DATA_FIELD, [])

        # Get the latest NAV (last entry in array)
        latest_entry = nav_data[-1]
        if len(latest_entry) < 2:
            raise ZerodhaAPIError(f"Invalid NAV data format for fund {fund_id}")

        current_nav = float(latest_entry[1])
        timestamp = int(latest_entry[0])

        # Convert timestamp to readable date for logging
        nav_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

        return current_nav, nav_date

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
