"""
Holdings-specific validation for integration tests.

Uses JSON Schema for structure validation + holdings-specific business logic validation.
"""

from pathlib import Path
from typing import Any, Dict, List

from tests.helpers.schema_validator import (
    validate_holdings_analysis_file,
    validate_holdings_extracted_file,
)


def validate_holdings_directory_structure(analysis_dir: Path) -> Path:
    """
    Validate holdings-specific directory structure.

    Args:
        analysis_dir: Base analysis directory

    Returns:
        Path to holdings analysis directory
    """
    # Find date directories
    date_dirs = [d for d in analysis_dir.iterdir() if d.is_dir()]
    assert len(date_dirs) >= 1, "Should create analysis date directories"

    # Find holdings directory
    holdings_dir = date_dirs[0] / "holdings"
    assert holdings_dir.exists(), "Should create holdings analysis directory"

    return holdings_dir


def validate_holdings_output_files(holdings_dir: Path) -> List[Path]:
    """
    Validate holdings output files exist.

    Args:
        holdings_dir: Holdings analysis directory

    Returns:
        List of analysis files found
    """
    analysis_files = list(holdings_dir.glob("*.json"))
    assert len(analysis_files) >= 1, "Should create holdings analysis files"

    print(f"📊 Found {len(analysis_files)} holdings analysis files")
    return analysis_files


def validate_holdings_analysis_content(analysis_files: List[Path]) -> List[Dict[str, Any]]:
    """
    Validate holdings analysis file content using JSON Schema + business logic.

    Args:
        analysis_files: List of analysis files to validate

    Returns:
        List of validated analysis data
    """
    validated_data = []

    for analysis_file in analysis_files:
        print(f"🔍 Validating {analysis_file.name}...")

        # Schema validation (replaces 90% of manual checks!)
        data = validate_holdings_analysis_file(analysis_file)

        # Business logic validation
        validate_holdings_business_logic(data)

        # Dashboard compatibility validation
        validate_holdings_dashboard_compatibility(data)

        validated_data.append(data)

    print(f"✅ Validated {len(analysis_files)} holdings analysis files")
    return validated_data


def validate_holdings_extracted_data(extracted_dir: Path) -> None:
    """
    Validate holdings extracted JSON files using JSON Schema.

    Args:
        extracted_dir: Directory containing extracted JSON files
    """
    print("📄 Validating holdings extracted data...")

    # Find date directories
    date_dirs = [d for d in extracted_dir.iterdir() if d.is_dir()]
    assert len(date_dirs) >= 1, "Should create extracted data date directories"

    # Find holdings directory
    holdings_dir = date_dirs[0] / "holdings"
    assert holdings_dir.exists(), "Should create holdings extracted data directory"

    # Find category directories (largeCap, midCap, etc.)
    category_dirs = [d for d in holdings_dir.iterdir() if d.is_dir()]
    assert len(category_dirs) >= 1, "Should create category directories"

    # Validate JSON files in each category using schema validation
    total_validated = 0
    for category_dir in category_dirs:
        json_files = list(category_dir.glob("*.json"))
        for json_file in json_files:
            # Schema validation replaces all manual checks
            validate_holdings_extracted_file(json_file)
            total_validated += 1

    print(f"✅ Validated {total_validated} holdings extracted files")


# =============================================================================
# Holdings-Specific Business Logic Validation
# =============================================================================


def validate_holdings_business_logic(data: Dict[str, Any]) -> None:
    """
    Validate holdings-specific business logic rules.

    Args:
        data: Holdings analysis data (already schema-validated)

    Raises:
        AssertionError: If business logic validation fails
    """
    _validate_holdings_sorting_rules(data)
    _validate_holdings_common_funds_logic(data)


def validate_holdings_dashboard_compatibility(data: Dict[str, Any]) -> None:
    """
    Validate holdings-specific dashboard compatibility requirements.

    Args:
        data: Holdings analysis data to validate

    Raises:
        AssertionError: If dashboard compatibility validation fails
    """
    # Ensure company objects have both 'name' and 'company' fields with same value
    # These are holdings-specific field names
    company_arrays = ["top_by_fund_count", "top_by_total_weight", "common_in_all_funds"]

    for array_name in company_arrays:
        companies = data[array_name]
        for company in companies:
            assert company["name"] == company["company"], (
                f"Company in {array_name} should have matching 'name' and 'company' fields"
            )


def _validate_holdings_sorting_rules(data: Dict[str, Any]) -> None:
    """Validate that holdings-specific arrays are sorted correctly."""
    # Validate top_by_fund_count sorting (fund_count desc, then total_weight desc)
    top_by_fund_count = data["top_by_fund_count"]
    if len(top_by_fund_count) >= 2:
        for i in range(len(top_by_fund_count) - 1):
            current = top_by_fund_count[i]
            next_item = top_by_fund_count[i + 1]
            assert current["fund_count"] > next_item["fund_count"] or (
                current["fund_count"] == next_item["fund_count"]
                and current["total_weight"] >= next_item["total_weight"]
            ), "top_by_fund_count should be sorted by fund_count desc, then total_weight desc"

    # Validate top_by_total_weight sorting (total_weight desc)
    top_by_total_weight = data["top_by_total_weight"]
    if len(top_by_total_weight) >= 2:
        for i in range(len(top_by_total_weight) - 1):
            current = top_by_total_weight[i]
            next_item = top_by_total_weight[i + 1]
            assert current["total_weight"] >= next_item["total_weight"], (
                "top_by_total_weight should be sorted by total_weight desc"
            )


def _validate_holdings_common_funds_logic(data: Dict[str, Any]) -> None:
    """Validate holdings-specific logic for companies that appear in all funds."""
    total_funds = data["total_funds"]
    common_companies = data["common_in_all_funds"]

    for company in common_companies:
        assert company["fund_count"] == total_funds, (
            f"Companies in common_in_all_funds should appear in ALL {total_funds} funds, "
            f"but {company['name']} appears in {company['fund_count']} funds"
        )
