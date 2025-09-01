from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mfa.config.settings import ConfigProvider
from mfa.logging.logger import logger
from mfa.storage.json_store import JsonStore

# Technical constants (not user-configurable)
DATE_PATTERN = r"\d{8}"  # Technical regex


@dataclass
class AnalysisResult:
    """Result of analyzing a single category."""

    category: str
    total_files: int
    total_funds: int
    unique_companies: int
    output_file: Path

    @property
    def average_companies_per_fund(self) -> float:
        """Calculate average number of companies per fund."""
        if self.total_funds == 0:
            return 0.0
        return self.unique_companies / self.total_funds


@dataclass
class FundAnalysisResult:
    """Overall result of fund analysis process."""

    categories_analyzed: int
    total_categories: int
    category_results: list[AnalysisResult]
    output_directory: Path

    @property
    def success_rate(self) -> float:
        """Calculate analysis success rate as percentage."""
        if self.total_categories == 0:
            return 0.0
        return (self.categories_analyzed / self.total_categories) * 100


@dataclass
class HoldingsData:
    """Container for aggregated holdings data."""

    company_to_funds: dict[str, set[str]]
    company_total_weights: dict[str, float]
    company_examples: dict[str, list[str]]
    funds_info: dict[str, str]
    processed_files_count: int
    skipped_files_count: int

    @property
    def total_funds(self) -> int:
        """Get total number of unique funds."""
        return len(self.funds_info)

    @property
    def unique_companies_count(self) -> int:
        """Get total number of unique companies."""
        return len(self.company_to_funds)


@dataclass
class CompanyAnalysis:
    """Analysis data for a single company."""

    name: str
    fund_count: int
    total_weight: float
    avg_weight: float
    sample_funds: list[str]


class AnalysisError(Exception):
    """Custom exception for analysis errors."""

    pass


class FundAnalyzer:
    """
    Handles analysis of fund holdings data.

    Processes extracted fund data to generate insights about company holdings,
    fund overlaps, and investment patterns across different fund categories.
    """

    def __init__(self):
        self._config = ConfigProvider.get_instance()

    def analyze(self, date: str | None = None, category: str | None = None) -> FundAnalysisResult:
        """
        Analyze fund holdings for specified date and category.

        Args:
            date: Specific date (YYYYMMDD) or None for latest
            category: Specific category or None for all categories

        Returns:
            FundAnalysisResult with analysis statistics

        Raises:
            AnalysisError: When configuration is invalid or analysis fails
        """
        self._log_welcome_message()

        input_dir, analysis_dir = self._setup_directories()
        scan_root = self._determine_scan_root(input_dir, date)
        categories = self._select_categories(scan_root, category)

        self._log_analysis_overview(categories)

        return self._execute_analysis(categories, scan_root, analysis_dir)

    def _get_analysis_settings(self) -> dict:
        """Get simple analysis settings from config."""
        return {
            "max_companies": self._config.get("analysis.max_companies_in_results", 100),
            "max_samples": self._config.get("analysis.max_sample_funds_per_company", 5),
            "excluded_holdings": set(self._config.get("analysis.exclude_from_analysis", [])),
        }

    def _log_welcome_message(self) -> None:
        """Log the welcome banner."""
        logger.info("\n" + "=" * 60)
        logger.info("📋 MFA ANALYZER - Fund Holdings Analysis")
        logger.info("=" * 60)

    def _setup_directories(self) -> tuple[Path, Path]:
        """Setup and return input and analysis directories."""
        input_dir = Path(str(self._config.get("paths.output_dir")))
        analysis_dir = Path(str(self._config.get("paths.analysis_dir")))
        analysis_dir.mkdir(parents=True, exist_ok=True)

        logger.info("📁 Input directory: {}", input_dir)
        logger.info("💾 Analysis output: {}", analysis_dir)

        return input_dir, analysis_dir

    def _determine_scan_root(self, input_dir: Path, date: str | None) -> Path:
        """Determine the root directory to scan based on date parameter."""
        if date:
            return self._validate_specific_date(input_dir, date)
        else:
            return self._find_latest_date_directory(input_dir)

    def _validate_specific_date(self, input_dir: Path, date: str) -> Path:
        """Validate and return specific date directory."""
        scan_root = input_dir / date
        if not scan_root.exists():
            available_dates = self._get_available_dates(input_dir)
            logger.error("❌ Date folder '{}' not found", date)
            logger.info("📅 Available dates in {}: {}", input_dir, available_dates)
            raise AnalysisError(f"Date folder '{date}' not found")

        logger.info("📅 Using specified date: {}", date)
        return scan_root

    def _find_latest_date_directory(self, input_dir: Path) -> Path:
        """Find and return the latest date directory."""
        latest_dir = self._get_latest_date_dir(input_dir)
        logger.info("📅 Using latest date folder: {}", latest_dir.name)
        return latest_dir

    def _get_available_dates(self, input_dir: Path) -> list[str]:
        """Get list of available date directories."""
        return [p.name for p in input_dir.iterdir() if p.is_dir() and p.name.isdigit()]

    def _select_categories(self, scan_root: Path, category: str | None) -> list[str]:
        """Select which categories to analyze."""
        if category:
            return self._validate_single_category(scan_root, category)
        else:
            return self._get_all_categories(scan_root)

    def _validate_single_category(self, scan_root: Path, category: str) -> list[str]:
        """Validate and return single category."""
        if not (scan_root / category).exists():
            available_categories = self._get_available_categories(scan_root)
            logger.error("❌ Category '{}' not found", category)
            logger.info("📂 Available categories in {}: {}", scan_root.name, available_categories)
            logger.info("💡 Use: make analyze CATEGORY=<category_name>")
            raise AnalysisError(f"Category '{category}' not found")

        logger.info("🎯 Analyzing single category: '{}'", category)
        return [category]

    def _get_all_categories(self, scan_root: Path) -> list[str]:
        """Get all available categories."""
        categories = [p.name for p in scan_root.iterdir() if p.is_dir()]
        logger.info("🌟 Analyzing all {} categories", len(categories))
        return categories

    def _get_available_categories(self, scan_root: Path) -> list[str]:
        """Get list of available category directories."""
        return [p.name for p in scan_root.iterdir() if p.is_dir()]

    def _log_analysis_overview(self, categories: list[str]) -> None:
        """Log overview of what will be analyzed."""
        if not categories:
            raise AnalysisError("No categories found to analyze")

        logger.info("\n🚀 Starting analysis...")
        logger.info("📊 Categories to analyze: {}", ", ".join(f"'{cat}'" for cat in categories))
        logger.info("-" * 50)

    def _execute_analysis(
        self, categories: list[str], scan_root: Path, analysis_dir: Path
    ) -> FundAnalysisResult:
        """Execute the main analysis process."""
        date_dir = analysis_dir / scan_root.name
        date_dir.mkdir(parents=True, exist_ok=True)

        successful_analyses = 0
        category_results = []

        for cat_idx, category in enumerate(categories, 1):
            try:
                result = self._analyze_single_category(
                    category, scan_root, date_dir, cat_idx, len(categories)
                )
                category_results.append(result)
                successful_analyses += 1
            except Exception as e:
                logger.error("  ❌ Failed to analyze category '{}': {}", category, str(e))
                logger.debug("  🔍 Full traceback:", exc_info=True)

        result = FundAnalysisResult(
            categories_analyzed=successful_analyses,
            total_categories=len(categories),
            category_results=category_results,
            output_directory=date_dir,
        )

        self._log_final_summary(result)
        return result

    def _analyze_single_category(
        self, category: str, scan_root: Path, date_dir: Path, cat_idx: int, total_categories: int
    ) -> AnalysisResult:
        """Analyze a single category and return results."""
        logger.info("\n📂 [{}/{}] Analyzing category: '{}'", cat_idx, total_categories, category)

        json_files = self._get_category_json_files(scan_root, category)
        if not json_files:
            return self._create_empty_analysis_result(category)

        logger.info("  📄 Found {} JSON files", len(json_files))

        holdings_data = self._aggregate_holdings_data(json_files, category)
        analysis_output = self._build_analysis_output(holdings_data)
        output_file = self._save_analysis_result(analysis_output, category, date_dir)

        return AnalysisResult(
            category=category,
            total_files=holdings_data.processed_files_count,
            total_funds=holdings_data.total_funds,
            unique_companies=holdings_data.unique_companies_count,
            output_file=output_file,
        )

    def _get_category_json_files(self, scan_root: Path, category: str) -> list[Path]:
        """Get all JSON files for a category."""
        category_dir = scan_root / category
        return list(self._iter_json_files(category_dir))

    def _create_empty_analysis_result(self, category: str) -> AnalysisResult:
        """Create an empty analysis result for categories with no data."""
        logger.warning("  ⚠️  No JSON files found for category: {}", category)
        return AnalysisResult(
            category=category, total_files=0, total_funds=0, unique_companies=0, output_file=Path()
        )

    def _aggregate_holdings_data(self, json_files: list[Path], category_name: str) -> HoldingsData:
        """Aggregate holdings data from multiple JSON files."""
        logger.info("🔍 Analyzing fund holdings for category: '{}'", category_name)

        holdings_data = HoldingsData(
            company_to_funds=defaultdict(set),
            company_total_weights=defaultdict(float),
            company_examples=defaultdict(list),
            funds_info={},
            processed_files_count=0,
            skipped_files_count=0,
        )

        for json_file in json_files:
            self._process_single_fund_file(json_file, holdings_data)

        self._log_aggregation_summary(holdings_data)
        return holdings_data

    def _process_single_fund_file(self, json_file: Path, holdings_data: HoldingsData) -> None:
        """Process a single fund JSON file and update holdings data."""
        try:
            fund_data = JsonStore.load(json_file)
        except Exception as e:
            holdings_data.skipped_files_count += 1
            logger.debug("  ⚠️  Skipped invalid file: {} ({})", json_file.name, str(e))
            return

        fund_info = self._extract_fund_info(fund_data, json_file)
        holdings = fund_data.get("data", {}).get("top_holdings", [])

        self._update_fund_registry(fund_info, holdings_data)
        self._process_fund_holdings(holdings, fund_info["name"], holdings_data)

        holdings_data.processed_files_count += 1
        logger.debug("  📄 Processing: {} ({} holdings)", fund_info["name"], len(holdings))

    def _extract_fund_info(self, fund_data: dict[str, Any], json_file: Path) -> dict[str, str]:
        """Extract fund information from fund data."""
        data_section = fund_data.get("data", {})
        fund_info_section = data_section.get("fund_info", {})

        return {
            "name": fund_info_section.get("fund_name") or json_file.stem,
            "aum": str(fund_info_section.get("aum") or "").strip(),
        }

    def _update_fund_registry(self, fund_info: dict[str, str], holdings_data: HoldingsData) -> None:
        """Update the fund registry with fund information."""
        fund_name = fund_info["name"]
        if fund_name not in holdings_data.funds_info:
            holdings_data.funds_info[fund_name] = fund_info["aum"]

    def _process_fund_holdings(
        self, holdings: list[dict[str, Any]], fund_name: str, holdings_data: HoldingsData
    ) -> None:
        """Process all holdings for a single fund."""
        for holding in holdings:
            company_name = self._normalize_company_name(holding.get("company_name", ""))

            if not self._is_valid_company(company_name):
                continue

            weight = self._parse_percentage(holding.get("allocation_percentage", ""))
            self._update_company_data(company_name, fund_name, weight, holdings_data)

    def _is_valid_company(self, company_name: str) -> bool:
        """Check if company name is valid for analysis."""
        if not company_name:
            return False

        analysis_settings = self._get_analysis_settings()
        return company_name.upper() not in analysis_settings["excluded_holdings"]

    def _update_company_data(
        self, company_name: str, fund_name: str, weight: float, holdings_data: HoldingsData
    ) -> None:
        """Update company data with new fund information."""
        holdings_data.company_to_funds[company_name].add(fund_name)
        holdings_data.company_total_weights[company_name] += weight

        # Add to examples if not already maxed out
        analysis_settings = self._get_analysis_settings()
        max_samples = analysis_settings["max_samples"]
        if len(holdings_data.company_examples[company_name]) < max_samples:
            if fund_name not in holdings_data.company_examples[company_name]:
                holdings_data.company_examples[company_name].append(fund_name)

    def _log_aggregation_summary(self, holdings_data: HoldingsData) -> None:
        """Log summary of data aggregation."""
        logger.info("  📁 Files processed: {}", holdings_data.processed_files_count)
        if holdings_data.skipped_files_count > 0:
            logger.info("  ⚠️  Files skipped: {}", holdings_data.skipped_files_count)
        logger.info("  📈 Funds analyzed: {}", holdings_data.total_funds)
        logger.info("  🏢 Unique companies found: {}", holdings_data.unique_companies_count)

        common_companies = self._find_companies_in_all_funds(holdings_data)
        if common_companies:
            logger.info("  🎆 Companies in ALL funds: {}", len(common_companies))

    def _find_companies_in_all_funds(self, holdings_data: HoldingsData) -> list[CompanyAnalysis]:
        """Find companies that appear in all funds."""
        if holdings_data.total_funds == 0:
            return []

        companies_by_count = self._build_companies_by_fund_count(holdings_data)
        return [comp for comp in companies_by_count if comp.fund_count >= holdings_data.total_funds]

    def _build_analysis_output(self, holdings_data: HoldingsData) -> dict[str, Any]:
        """Build the final analysis output dictionary."""
        analysis_settings = self._get_analysis_settings()
        max_companies = analysis_settings["max_companies"]

        companies_by_count = self._build_companies_by_fund_count(holdings_data)
        companies_by_weight = self._build_companies_by_total_weight(holdings_data)
        common_companies = self._find_companies_in_all_funds(holdings_data)

        return {
            "total_files": holdings_data.processed_files_count,
            "total_funds": holdings_data.total_funds,
            "funds": self._build_funds_list(holdings_data.funds_info),
            "unique_companies": holdings_data.unique_companies_count,
            "top_by_fund_count": [comp.__dict__ for comp in companies_by_count[:max_companies]],
            "top_by_total_weight": [comp.__dict__ for comp in companies_by_weight[:max_companies]],
            "common_in_all_funds": [comp.__dict__ for comp in common_companies],
        }

    def _build_companies_by_fund_count(self, holdings_data: HoldingsData) -> list[CompanyAnalysis]:
        """Build list of companies sorted by fund count."""
        analysis_settings = self._get_analysis_settings()
        max_samples = analysis_settings["max_samples"]
        companies = []

        for company_name, funds_set in holdings_data.company_to_funds.items():
            total_weight = holdings_data.company_total_weights[company_name]
            fund_count = len(funds_set)

            company_analysis = CompanyAnalysis(
                name=company_name,
                fund_count=fund_count,
                total_weight=round(total_weight, 3),
                avg_weight=round(total_weight / max(fund_count, 1), 3),
                sample_funds=sorted(funds_set)[:max_samples],
            )
            companies.append(company_analysis)

        return sorted(companies, key=lambda x: (x.fund_count, x.total_weight), reverse=True)

    def _build_companies_by_total_weight(
        self, holdings_data: HoldingsData
    ) -> list[CompanyAnalysis]:
        """Build list of companies sorted by total weight."""
        analysis_settings = self._get_analysis_settings()
        max_samples = analysis_settings["max_samples"]
        companies = []

        for company_name, total_weight in holdings_data.company_total_weights.items():
            fund_count = len(holdings_data.company_to_funds[company_name])

            company_analysis = CompanyAnalysis(
                name=company_name,
                fund_count=fund_count,
                total_weight=round(total_weight, 3),
                avg_weight=round(total_weight / max(fund_count, 1), 3),
                sample_funds=sorted(holdings_data.company_examples[company_name])[:max_samples],
            )
            companies.append(company_analysis)

        return sorted(companies, key=lambda x: (x.total_weight, x.fund_count), reverse=True)

    def _build_funds_list(self, funds_info: dict[str, str]) -> list[dict[str, str]]:
        """Build sorted list of fund information."""
        return [{"name": name, "aum": aum} for name, aum in sorted(funds_info.items())]

    def _save_analysis_result(
        self, analysis_data: dict[str, Any], category: str, date_dir: Path
    ) -> Path:
        """Save analysis result to file."""
        output_file = date_dir / f"{category}.json"
        JsonStore.save(analysis_data, output_file)

        file_size_kb = output_file.stat().st_size / 1024
        logger.info(
            "  ✅ Analysis complete! Saved to: {} ({:.1f} KB)", output_file.name, file_size_kb
        )

        return output_file

    def _iter_json_files(self, root: Path) -> Iterator[Path]:
        """Iterate over JSON files in directory."""
        yield from sorted(root.rglob("*.json"))

    def _get_latest_date_dir(self, root: Path) -> Path:
        """Get the latest date directory."""
        if not root.exists():
            return root

        date_dirs = [p for p in root.iterdir() if p.is_dir() and re.fullmatch(DATE_PATTERN, p.name)]
        if not date_dirs:
            return root

        return max(date_dirs, key=lambda p: p.name)

    def _parse_percentage(self, value: str) -> float:
        """Parse percentage string to float."""
        if not value:
            return 0.0
        match = re.search(r"(\d{1,3}(?:\.\d+)?)%", str(value))
        return float(match.group(1)) if match else 0.0

    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for consistent analysis."""
        normalized = name.strip()

        # Remove common suffixes
        normalized = re.sub(
            r"\b(pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited)\b", "", normalized, flags=re.I
        )

        # Normalize spacing
        normalized = re.sub(r"\s*&\s*", " & ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)

        # Clean up punctuation
        normalized = re.sub(r"^[\s\.,:;\-]+", "", normalized)
        normalized = re.sub(r"[\s\.,:;\-]+$", "", normalized)
        normalized = normalized.replace(" ", " ")  # Replace non-breaking spaces

        return normalized.strip()

    def _log_final_summary(self, result: FundAnalysisResult) -> None:
        """Log the final analysis summary."""
        logger.info("\n" + "=" * 60)
        logger.info("🎉 ANALYSIS COMPLETE!")
        logger.info(
            "📊 Categories analyzed: {}/{}", result.categories_analyzed, result.total_categories
        )
        logger.info("📈 Success rate: {:.1f}%", result.success_rate)
        logger.info("💾 Analysis results saved to: {}", result.output_directory)
        logger.info("=" * 60 + "\n")
