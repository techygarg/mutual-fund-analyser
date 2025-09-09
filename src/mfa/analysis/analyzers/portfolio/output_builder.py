from __future__ import annotations

from typing import Any

from mfa.config.settings import ConfigProvider


class PortfolioOutputBuilder:
    """Builds final JSON output for portfolio analysis."""

    def __init__(self, config_provider: ConfigProvider):
        self.config_provider = config_provider

    def build_output(
        self, aggregation: dict[str, Any], funds: list[dict[str, Any]], params: Any
    ) -> dict[str, Any]:
        company_amounts = aggregation["company_amounts"]
        company_sources = aggregation["company_sources"]
        total_value = float(aggregation["total_value"]) if aggregation else 0.0

        chart_top_n = int(params.chart_top_n or 20)

        companies = []
        for name, amount in company_amounts:
            pct = (amount / total_value) * 100.0 if total_value > 0 else 0.0

            # Format from_funds with integer contributions
            formatted_from_funds = []
            for fund_info in company_sources.get(name, []):
                formatted_from_funds.append(
                    {
                        "fund_name": fund_info["fund_name"],
                        "contribution": int(round(fund_info["contribution"])),
                    }
                )

            companies.append(
                {
                    "company_name": name,
                    "amount": int(round(amount)),
                    "percentage": round(pct, 2),
                    "from_funds": formatted_from_funds,
                }
            )

        top_companies = companies[:chart_top_n]

        funds_out = [
            {
                "fund_name": f.get("fund_name", ""),
                "url": f.get("url", ""),
                "units": f.get("units", 0.0),
                "nav": f.get("nav", 0.0),
                "value": int(round(f.get("fund_value", 0.0))),
            }
            for f in funds
        ]

        return {
            "portfolio_summary": {
                "total_value": int(round(total_value)),
                "fund_count": len(funds_out),
                "unique_companies": len(companies),
                "top_n": chart_top_n,
            },
            "funds": funds_out,
            "company_allocations": companies,
            "top_companies": top_companies,
        }
