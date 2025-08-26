from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


# NOTE: This file defines two sets of models:
# 1) Extraction models used for per-fund JSON artifacts
# 2) Analysis models used for per-category analysis outputs


# --- Extraction models ---

class TopHolding(BaseModel):
    rank: int
    company_name: str
    allocation_percentage: str


class FundInfo(BaseModel):
    fund_name: str = ""
    current_nav: str = ""
    cagr: str = ""
    expense_ratio: str = ""
    aum: str = ""
    fund_manager: str = ""
    launch_date: str = ""
    risk_level: str = ""


class FundData(BaseModel):
    fund_info: FundInfo
    top_holdings: List[TopHolding] = Field(default_factory=list)
    


class ExtractedFundDocument(BaseModel):
    schema_version: str = "1.0"
    extraction_timestamp: datetime
    source_url: HttpUrl
    provider: str
    data: FundData


# --- Analysis models ---

class FundRef(BaseModel):
    name: str
    aum: str = ""


class CompanyStat(BaseModel):
    company: str
    fund_count: int
    total_weight: float
    avg_weight: float
    sample_funds: List[str] = Field(default_factory=list)


class CategoryAnalysis(BaseModel):
    schema_version: str = "1.0"
    total_files: int
    total_funds: int
    funds: List[FundRef] = Field(default_factory=list)
    unique_companies: int
    top_by_fund_count: List[CompanyStat] = Field(default_factory=list)
    top_by_total_weight: List[CompanyStat] = Field(default_factory=list)
    common_in_all_funds: List[CompanyStat] = Field(default_factory=list)


# --- Extra extraction models (none) ---


__all__ = [
    # extraction
    "TopHolding",
    "FundInfo",
    "FundData",
    "ExtractedFundDocument",
    # analysis
    "FundRef",
    "CompanyStat",
    "CategoryAnalysis",
]


