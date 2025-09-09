"""
Portfolio-specific validation for integration tests.

Uses JSON Schema for structure validation + portfolio-specific business logic validation.
"""

from pathlib import Path
from typing import Any, Dict, List

from tests.helpers.schema_validator import SchemaValidator


def validate_portfolio_directory_structure(analysis_dir: Path) -> Path:
    """
    Validate portfolio-specific directory structure.

    Args:
        analysis_dir: Base analysis directory

    Returns:
        Path to portfolio analysis directory
    """
    # Find date directories
    date_dirs = [d for d in analysis_dir.iterdir() if d.is_dir()]
    assert len(date_dirs) >= 1, "Should create analysis date directories"

    # Find portfolio directory
    portfolio_dir = date_dirs[0] / "portfolio"
    assert portfolio_dir.exists(), "Should create portfolio analysis directory"

    return portfolio_dir


def validate_portfolio_output_files(portfolio_dir: Path) -> List[Path]:
    """
    Validate portfolio output files exist.

    Args:
        portfolio_dir: Portfolio analysis directory

    Returns:
        List of analysis files found
    """
    analysis_files = list(portfolio_dir.glob("*.json"))
    assert len(analysis_files) >= 1, "Should create portfolio analysis files"

    print(f"📊 Found {len(analysis_files)} portfolio analysis files")
    return analysis_files


def validate_portfolio_analysis_content(analysis_files: List[Path]) -> List[Dict[str, Any]]:
    """
    Validate portfolio analysis file content using JSON Schema + business logic.

    Args:
        analysis_files: List of analysis files to validate

    Returns:
        List of validated analysis data
    """
    validated_data = []

    for analysis_file in analysis_files:
        print(f"🔍 Validating {analysis_file.name}...")

        # Schema validation (replaces 90% of manual checks!)
        data = validate_portfolio_analysis_file(analysis_file)

        # Portfolio-specific business logic validation
        validate_portfolio_business_logic(data)

        validated_data.append(data)

    print(f"✅ Validated {len(analysis_files)} portfolio analysis files")
    return validated_data


def validate_portfolio_extracted_data(extracted_dir: Path) -> None:
    """
    Validate portfolio extracted JSON files using JSON Schema.

    Args:
        extracted_dir: Directory containing extracted JSON files
    """
    print("📄 Validating portfolio extracted data...")

    # Find date directories
    date_dirs = [d for d in extracted_dir.iterdir() if d.is_dir()]
    assert len(date_dirs) >= 1, "Should create extracted data date directories"

    # Find portfolio directory
    portfolio_dir = date_dirs[0] / "portfolio"
    assert portfolio_dir.exists(), "Should create portfolio extracted data directory"

    # Validate JSON files in portfolio directory
    json_files = list(portfolio_dir.glob("*.json"))
    total_validated = 0
    for json_file in json_files:
        # Schema validation replaces all manual checks
        validate_portfolio_extracted_file(json_file)
        total_validated += 1

    print(f"✅ Validated {total_validated} portfolio extracted files")


# =============================================================================
# Portfolio-Specific Business Logic Validation
# =============================================================================

def validate_portfolio_business_logic(data: Dict[str, Any]) -> None:
    """
    Validate portfolio-specific business logic rules.

    Args:
        data: Portfolio analysis data (already schema-validated)

    Raises:
        AssertionError: If business logic validation fails
    """
    _validate_portfolio_value_consistency(data)
    _validate_portfolio_allocation_sorting(data)
    _validate_portfolio_percentage_calculations(data)


def _validate_portfolio_value_consistency(data: Dict[str, Any]) -> None:
    """Validate that portfolio values are mathematically consistent."""
    portfolio_summary = data["portfolio_summary"]
    funds = data["funds"]
    
    # Check that total_value matches sum of fund values
    expected_total = sum(fund["value"] for fund in funds)
    actual_total = portfolio_summary["total_value"]
    
    # Allow small rounding differences (within 1% or 100 units)
    tolerance = max(100, actual_total * 0.01)
    assert abs(actual_total - expected_total) <= tolerance, (
        f"Portfolio total value ({actual_total}) should match sum of fund values ({expected_total})"
    )
    
    # Check fund_count matches actual number of funds
    assert portfolio_summary["fund_count"] == len(funds), (
        f"Fund count ({portfolio_summary['fund_count']}) should match actual funds ({len(funds)})"
    )


def _validate_portfolio_allocation_sorting(data: Dict[str, Any]) -> None:
    """Validate that portfolio allocations are sorted correctly."""
    company_allocations = data["company_allocations"]
    top_companies = data["top_companies"]
    
    # Validate company_allocations are sorted by amount (descending)
    if len(company_allocations) >= 2:
        for i in range(len(company_allocations) - 1):
            current = company_allocations[i]
            next_item = company_allocations[i + 1]
            assert current["amount"] >= next_item["amount"], (
                "company_allocations should be sorted by amount desc"
            )
    
    # Validate top_companies are subset of company_allocations (top N items)
    portfolio_summary = data["portfolio_summary"]
    top_n = portfolio_summary["top_n"]
    expected_top_companies = company_allocations[:top_n]
    
    assert len(top_companies) <= top_n, (
        f"top_companies should have at most {top_n} items"
    )
    
    # Validate top_companies match the first N from company_allocations
    for i, (expected, actual) in enumerate(zip(expected_top_companies, top_companies)):
        assert expected["company_name"] == actual["company_name"], (
            f"top_companies[{i}] should match company_allocations[{i}]"
        )


def _validate_portfolio_percentage_calculations(data: Dict[str, Any]) -> None:
    """Validate portfolio percentage calculations are correct."""
    portfolio_summary = data["portfolio_summary"]
    company_allocations = data["company_allocations"]
    total_value = portfolio_summary["total_value"]
    
    if total_value == 0:
        # If total value is 0, all percentages should be 0
        for company in company_allocations:
            assert company["percentage"] == 0, (
                f"Company {company['company_name']} should have 0% when total value is 0"
            )
        return
    
    # Check percentage calculations
    for company in company_allocations:
        expected_percentage = (company["amount"] / total_value) * 100
        actual_percentage = company["percentage"]
        
        # Allow small rounding differences (within 0.1%)
        assert abs(actual_percentage - expected_percentage) <= 0.1, (
            f"Company {company['company_name']} percentage calculation incorrect: "
            f"expected ~{expected_percentage:.2f}%, got {actual_percentage}%"
        )


def _validate_portfolio_fund_contributions(data: Dict[str, Any]) -> None:
    """Validate fund contribution data is consistent."""
    company_allocations = data["company_allocations"]
    
    for company in company_allocations:
        from_funds = company["from_funds"]
        
        # Check that sum of contributions equals company amount
        total_contributions = sum(fund["contribution"] for fund in from_funds)
        company_amount = company["amount"]
        
        # Allow small rounding differences
        assert abs(total_contributions - company_amount) <= 10, (
            f"Company {company['company_name']} contributions ({total_contributions}) "
            f"should sum to company amount ({company_amount})"
        )


# =============================================================================
# Portfolio Schema Validation Functions
# =============================================================================

def validate_portfolio_analysis_file(json_file: Path) -> Dict[str, Any]:
    """
    Validate portfolio analysis output file using JSON Schema.

    Args:
        json_file: Path to analysis JSON file

    Returns:
        Validated analysis data

    Raises:
        jsonschema.ValidationError: If validation fails
    """
    validator = SchemaValidator()
    return validator.validate_file(json_file, "portfolio/analysis_output.json")


def validate_portfolio_extracted_file(json_file: Path) -> Dict[str, Any]:
    """
    Validate portfolio extracted data file using JSON Schema.

    Args:
        json_file: Path to extracted JSON file

    Returns:
        Validated extracted data

    Raises:
        jsonschema.ValidationError: If validation fails
    """
    validator = SchemaValidator()
    return validator.validate_file(json_file, "portfolio/extracted_data.json")
