from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mfa.config.settings import config
from mfa.logging.logger import logger
from mfa.scraping.core.playwright_scraper import PlaywrightSession
from mfa.scraping.zerodha_coin import ZerodhaCoinScraper
from mfa.storage.json_store import JsonStore

# Constants
DEFAULT_OUTPUT_DIR = "outputs/extracted_json"
SCRAPER_TIMEOUT_MS = 3000
FILENAME_PREFIX = "coin_"
DATE_FORMAT = "%Y%m%d"


@dataclass
class CategoryResult:
    """Result of processing a single category."""
    category: str
    total_urls: int
    successful: int
    failed: int
    duration_seconds: float

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_urls == 0:
            return 0.0
        return (self.successful / self.total_urls) * 100


@dataclass
class OrchestrationResult:
    """Overall result of orchestration process."""
    total_funds: int
    processed_count: int
    category_results: list[CategoryResult]
    output_directory: Path

    @property
    def overall_success_rate(self) -> float:
        """Calculate overall success rate as percentage."""
        if self.total_funds == 0:
            return 0.0
        return (self.processed_count / self.total_funds) * 100


class OrchestrationError(Exception):
    """Custom exception for orchestration errors."""
    pass


class Orchestrator:
    """
    Handles orchestration of fund data collection.

    Coordinates the scraping of mutual fund data across different categories,
    manages the scraping session, handles errors, and provides comprehensive
    logging and result tracking.
    """

    def __init__(self):
        self._config = config
        self._scraper: ZerodhaCoinScraper | None = None

    def run(self, category: str | None = None) -> OrchestrationResult:
        """
        Run the orchestration process for specified category or all categories.

        Args:
            category: Specific category to process, or None for all categories

        Returns:
            OrchestrationResult with processing statistics

        Raises:
            OrchestrationError: When configuration is invalid or processing fails
        """
        self._log_welcome_message()

        output_root = self._get_output_directory()
        funds = self._load_funds_configuration()
        selected_categories = self._select_categories(funds, category)

        self._log_processing_overview(selected_categories, output_root)

        return self._execute_orchestration(selected_categories, output_root)

    def _log_welcome_message(self) -> None:
        """Log the welcome banner."""
        logger.info("\n" + "="*60)
        logger.info("🎭 MFA ORCHESTRATOR - Fund Data Collection")
        logger.info("="*60)

    def _get_output_directory(self) -> Path:
        """Get the configured output directory."""
        output_dir = self._config.get("paths.output_dir") or DEFAULT_OUTPUT_DIR
        return Path(str(output_dir))

    def _load_funds_configuration(self) -> dict[str, list[str]]:
        """Load and validate funds configuration."""
        funds: dict[str, list[str]] = self._config.get("funds", {}) or {}

        if not funds:
            logger.error("❌ No funds configured under 'funds' in config.yaml")
            logger.info("💡 Please add fund URLs to your config.yaml file")
            raise OrchestrationError("No funds configured in config.yaml")

        return funds

    def _select_categories(self, funds: dict[str, list[str]], category: str | None) -> dict[str, list[str]]:
        """Select which categories to process based on input."""
        if category:
            return self._select_single_category(funds, category)
        else:
            return self._select_all_categories(funds)

    def _select_single_category(self, funds: dict[str, list[str]], category: str) -> dict[str, list[str]]:
        """Select and validate a single category."""
        if category not in funds:
            available_categories = sorted(funds.keys())
            logger.error("❌ Unknown category: '{}'", category)
            logger.info("📂 Available categories: {}", ", ".join(f"'{cat}'" for cat in available_categories))
            logger.info("💡 Use: make orchestrate CATEGORY=<category_name>")
            raise OrchestrationError(f"Unknown category: {category}")

        logger.info("🎯 Processing single category: '{}'", category)
        return {category: funds[category]}

    def _select_all_categories(self, funds: dict[str, list[str]]) -> dict[str, list[str]]:
        """Select all available categories."""
        logger.info("🌟 Processing all {} categories", len(funds))
        return funds

    def _log_processing_overview(self, selected_categories: dict[str, list[str]], output_root: Path) -> None:
        """Log overview of what will be processed."""
        total_urls = sum(len(urls) for urls in selected_categories.values())

        logger.info("\n🚀 Starting fund data collection...")
        logger.info("📊 Categories: {}", ", ".join(f"'{cat}'" for cat in sorted(selected_categories.keys())))
        logger.info("📈 Total funds to process: {}", total_urls)
        logger.info("📁 Output directory: {}", output_root)
        logger.info("-" * 50)

    def _execute_orchestration(self, selected_categories: dict[str, list[str]],
                              output_root: Path) -> OrchestrationResult:
        """Execute the main orchestration process."""
        total_urls = sum(len(urls) for urls in selected_categories.values())
        processed_count = 0
        category_results = []

        for category_idx, (cat_name, urls) in enumerate(selected_categories.items(), 1):
            cat_result = self._process_category(
                category=cat_name,
                urls=urls,
                category_index=category_idx,
                total_categories=len(selected_categories),
                output_root=output_root
            )
            category_results.append(cat_result)
            processed_count += cat_result.successful

        result = OrchestrationResult(
            total_funds=total_urls,
            processed_count=processed_count,
            category_results=category_results,
            output_directory=output_root
        )

        self._log_final_summary(result)
        return result

    def _process_category(self, category: str, urls: list[str], category_index: int,
                         total_categories: int, output_root: Path) -> CategoryResult:
        """Process all URLs in a single category."""
        self._log_category_start(category, urls, category_index, total_categories, output_root)

        category_start_time = datetime.now(UTC)
        stats = {"successful": 0, "failed": 0}

        self._create_scraper()

        try:
            self._process_category_urls(category, urls, output_root, stats)
        finally:
            # Scraper cleanup is handled by context manager in scraper itself
            pass

        duration = (datetime.now(UTC) - category_start_time).total_seconds()
        result = CategoryResult(
            category=category,
            total_urls=len(urls),
            successful=stats["successful"],
            failed=stats["failed"],
            duration_seconds=duration
        )

        self._log_category_summary(result)
        return result

    def _log_category_start(self, category: str, urls: list[str], category_index: int,
                           total_categories: int, output_root: Path) -> None:
        """Log the start of category processing."""
        target_dir = self._get_category_directory(output_root, category)
        logger.info("\n📂 [{}/{}] Processing category: '{}'", category_index, total_categories, category)
        logger.info("🔗 URLs in category: {}", len(urls))
        logger.info("💾 Saving to: {}", target_dir)

    def _create_scraper(self) -> ZerodhaCoinScraper:
        """Create and configure a scraper instance."""
        session = PlaywrightSession(headless=True, nav_timeout_ms=SCRAPER_TIMEOUT_MS)
        return ZerodhaCoinScraper(session=session)

    def _process_category_urls(self, category: str, urls: list[str],
                              output_root: Path, stats: dict[str, int]) -> None:
        """Process all URLs in a category."""
        target_dir = self._get_category_directory(output_root, category)
        scraper = self._create_scraper()

        for url_index, url in enumerate(urls, 1):
            try:
                self._process_single_url(url, url_index, len(urls), target_dir, scraper)
                stats["successful"] += 1
            except Exception as exc:
                self._handle_url_processing_error(url, exc)
                stats["failed"] += 1

    def _process_single_url(self, url: str, url_index: int, total_urls: int,
                           target_dir: Path, scraper: ZerodhaCoinScraper) -> None:
        """Process a single URL and save the result."""
        fund_name = self._extract_fund_name_from_url(url)
        self._log_url_processing_start(url, url_index, total_urls, fund_name)

        start_time = datetime.now(UTC)
        result = scraper.scrape(url)
        duration = (datetime.now(UTC) - start_time).total_seconds()

        output_file = self._save_scraping_result(url, result, target_dir)
        holdings_count = self._extract_holdings_count(result)

        self._log_url_processing_success(holdings_count, duration, output_file)

    def _extract_fund_name_from_url(self, url: str) -> str:
        """Extract a human-readable fund name from URL."""
        safe_name = self._create_safe_filename_from_url(url)
        return safe_name.replace("_", " ").title()

    def _log_url_processing_start(self, url: str, url_index: int, total_urls: int, fund_name: str) -> None:
        """Log the start of processing a single URL."""
        logger.info("\n  📊 [{}/{}] Processing: {}", url_index, total_urls, fund_name)
        logger.info("  🌐 URL: {}", url)

    def _save_scraping_result(self, url: str, result: dict[str, Any], target_dir: Path) -> Path:
        """Save scraping result to file."""
        filename = f"{FILENAME_PREFIX}{self._create_safe_filename_from_url(url)}.json"
        output_file = target_dir / filename
        JsonStore.save(result, output_file)
        return output_file

    def _extract_holdings_count(self, result: dict[str, Any]) -> int:
        """Extract the number of holdings from scraping result."""
        return len(result.get("data", {}).get("top_holdings", []))

    def _log_url_processing_success(self, holdings_count: int, duration: float, output_file: Path) -> None:
        """Log successful URL processing."""
        logger.info("  ✅ Success! Scraped {} holdings in {:.1f}s", holdings_count, duration)
        logger.info("  💾 Saved: {}", output_file.name)

    def _handle_url_processing_error(self, url: str, error: Exception) -> None:
        """Handle and log URL processing errors."""
        fund_name = self._extract_fund_name_from_url(url)
        logger.error("  ❌ Failed to process: {}", fund_name)
        logger.error("  🚨 Error: {}", str(error))
        logger.debug("  🔍 Full traceback:", exc_info=True)

    def _get_category_directory(self, root: Path, category: str) -> Path:
        """Create and return category directory path."""
        category_dir = root / self._get_today_string() / category
        category_dir.mkdir(parents=True, exist_ok=True)
        return category_dir

    def _get_today_string(self) -> str:
        """Get today's date as formatted string."""
        return datetime.now(UTC).strftime(DATE_FORMAT)

    def _create_safe_filename_from_url(self, url: str) -> str:
        """Extract safe filename components from URL."""
        parts = url.rstrip("/").split("/")
        tail = parts[-2:] if len(parts) >= 2 else parts
        return "_".join(tail)

    def _log_category_summary(self, result: CategoryResult) -> None:
        """Log summary for a completed category."""
        logger.info("\n📋 Category '{}' Summary:", result.category)
        logger.info("  ✅ Successful: {}/{}", result.successful, result.total_urls)
        logger.info("  ❌ Failed: {}", result.failed)
        logger.info("  📊 Success Rate: {:.1f}%", result.success_rate)
        logger.info("  ⏱️  Duration: {:.1f}s", result.duration_seconds)
        logger.info("-" * 30)

    def _log_final_summary(self, result: OrchestrationResult) -> None:
        """Log the final summary of orchestration."""
        logger.info("\n" + "="*60)
        logger.info("🎉 ORCHESTRATION COMPLETE!")
        logger.info("📊 Total funds processed: {}/{}", result.processed_count, result.total_funds)
        logger.info("📈 Overall success rate: {:.1f}%", result.overall_success_rate)
        logger.info("📁 Results saved to: {}", result.output_directory)
        logger.info("="*60 + "\n")
