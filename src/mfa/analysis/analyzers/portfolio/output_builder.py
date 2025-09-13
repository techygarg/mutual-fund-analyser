from __future__ import annotations

from typing import Any

from mfa.config.settings import ConfigProvider

from ..utils.output_builder_utils import OutputBuilderUtils


class PortfolioOutputBuilder:
    """Builds final JSON output for portfolio analysis."""

    def __init__(self, config_provider: ConfigProvider):
        self.config_provider = config_provider

    def build_output(
        self, aggregation: dict[str, Any], funds: list[dict[str, Any]], params: Any
    ) -> dict[str, Any]:
        """
        Build portfolio output using focused helper methods.

        Args:
            aggregation: Aggregated portfolio data
            funds: List of fund data
            params: Portfolio parameters

        Returns:
            Complete portfolio output structure
        """
        # Extract core data
        company_amounts = aggregation["company_amounts"]
        company_sources = aggregation["company_sources"]
        total_value = float(aggregation["total_value"]) if aggregation else 0.0
        chart_top_n = int(params.chart_top_n or 20)

        # Build company allocations
        companies = self._build_company_allocations(company_amounts, company_sources, total_value)

        # Format fund information
        funds_out = self._format_fund_information(funds)

        # Build final structure
        return self._build_portfolio_structure(companies, funds_out, total_value, chart_top_n)

    def _build_company_allocations(
        self,
        company_amounts: list[tuple[str, float]],
        company_sources: dict[str, list[dict[str, Any]]],
        total_value: float,
    ) -> list[dict[str, Any]]:
        """Build company allocation information with percentages and fund sources."""
        companies = []

        for name, amount in company_amounts:
            pct = (amount / total_value) * 100.0 if total_value > 0 else 0.0

            # Format fund contributions
            formatted_from_funds = [
                OutputBuilderUtils.format_fund_contribution(
                    fund_info["fund_name"], fund_info["contribution"]
                )
                for fund_info in company_sources.get(name, [])
            ]

            companies.append(
                {
                    "company_name": name,
                    "amount": OutputBuilderUtils.format_currency_value(amount),
                    "percentage": OutputBuilderUtils.format_percentage(pct),
                    "from_funds": formatted_from_funds,
                }
            )

        return companies

    def _format_fund_information(self, funds: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format fund information for output."""
        return [
            {
                "fund_name": f.get("fund_name", ""),
                "url": f.get("url", ""),
                "units": f.get("units", 0.0),
                "nav": f.get("nav", 0.0),
                "value": OutputBuilderUtils.format_currency_value(f.get("fund_value", 0.0)),
            }
            for f in funds
        ]

    def _build_portfolio_structure(
        self,
        companies: list[dict[str, Any]],
        funds_out: list[dict[str, Any]],
        total_value: float,
        chart_top_n: int,
    ) -> dict[str, Any]:
        """Build the final portfolio structure."""
        top_companies = OutputBuilderUtils.limit_results(companies, chart_top_n)

        return {
            "portfolio_summary": {
                "total_value": OutputBuilderUtils.format_currency_value(total_value),
                "fund_count": len(funds_out),
                "unique_companies": len(companies),
                "top_n": chart_top_n,
            },
            "funds": funds_out,
            "company_allocations": companies,
            "top_companies": top_companies,
        }
