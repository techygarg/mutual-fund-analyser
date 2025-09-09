"""
HTTP client utilities for API-based scraping.

This module provides a robust HTTP client with retry logic, timeout handling,
and proper error management for fetching mutual fund data from APIs.
"""

from __future__ import annotations

import time
from typing import Any

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from urllib3.util.retry import Retry


class HTTPClient:
    """Robust HTTP client with retry logic and timeout handling."""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: list[int] | None = None,
    ) -> None:
        """
        Initialize HTTP client with retry configuration.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
            status_forcelist: HTTP status codes to retry on
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.status_forcelist = status_forcelist or [500, 502, 503, 504]

        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=self.status_forcelist,
            backoff_factor=self.backoff_factor,
            allowed_methods=["GET"],  # Only retry GET requests
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update(
            {
                "User-Agent": "MFA-Portfolio-Analyzer/1.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            }
        )

        return session

    def get_json(self, url: str, **kwargs: Any) -> dict[str, Any]:
        """
        Perform GET request and return JSON response.

        Args:
            url: URL to fetch
            **kwargs: Additional arguments passed to requests.get()

        Returns:
            JSON response as dictionary

        Raises:
            HTTPClientError: If request fails after retries
        """
        try:
            logger.debug(f"🌐 Fetching JSON from: {url}")

            response = self._session.get(url, timeout=self.timeout, **kwargs)

            # Raise exception for bad status codes
            response.raise_for_status()

            # Parse JSON response
            json_data: dict[str, Any] = response.json()
            logger.debug(f"✅ Successfully fetched {len(str(json_data))} bytes of JSON data")

            return json_data

        except Timeout as e:
            error_msg = f"Request timeout after {self.timeout}s: {url}"
            logger.error(error_msg)
            raise HTTPClientError(error_msg) from e

        except ConnectionError as e:
            error_msg = f"Connection error: {url}"
            logger.error(error_msg)
            raise HTTPClientError(error_msg) from e

        except HTTPError as e:
            error_msg = f"HTTP error {e.response.status_code}: {url}"
            logger.error(error_msg)
            raise HTTPClientError(error_msg) from e

        except ValueError as e:  # JSON decode error
            error_msg = f"Invalid JSON response from: {url}"
            logger.error(error_msg)
            raise HTTPClientError(error_msg) from e

        except RequestException as e:
            error_msg = f"Request failed: {url} - {e}"
            logger.error(error_msg)
            raise HTTPClientError(error_msg) from e

    def get_json_with_delay(self, url: str, delay: float = 1.0, **kwargs: Any) -> dict[str, Any]:
        """
        Perform GET request with delay (for rate limiting).

        Args:
            url: URL to fetch
            delay: Delay in seconds before request
            **kwargs: Additional arguments passed to get_json()

        Returns:
            JSON response as dictionary
        """
        if delay > 0:
            logger.debug(f"⏳ Waiting {delay}s before request...")
            time.sleep(delay)

        return self.get_json(url, **kwargs)

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            logger.debug("🔒 HTTP session closed")

    def __enter__(self) -> HTTPClient:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


class HTTPClientError(Exception):
    """Exception raised by HTTP client operations."""

    def __init__(self, message: str) -> None:
        """Initialize with error message."""
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation of the error."""
        return self.message
