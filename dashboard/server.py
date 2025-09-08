from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_ROOT = ROOT / "outputs" / "analysis"
EXTRACTED_ROOT = ROOT / "outputs" / "extracted_json"
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="MFA Dashboard", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== ANALYSIS PLUGIN FRAMEWORK ====================

class AnalysisPlugin(ABC):
    """Base class for analysis plugins."""
    
    @property
    @abstractmethod
    def analysis_type(self) -> str:
        """Return the analysis type identifier (e.g., 'holdings', 'portfolio')."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return the human-readable display name."""
        pass
    
    @property
    @abstractmethod
    def icon(self) -> str:
        """Return the icon/emoji for the analysis."""
        pass
    
    @property
    @abstractmethod
    def requires_category(self) -> bool:
        """Return True if this analysis requires category selection."""
        pass
    
    @abstractmethod
    def get_categories(self, date: str) -> List[str]:
        """Get available categories for this analysis on a given date."""
        pass
    
    @abstractmethod
    def get_analysis_data(self, date: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Get the main analysis data."""
        pass
    
    @abstractmethod
    def get_funds_data(self, date: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Get the funds composition data."""
        pass
    
    @abstractmethod
    def transform_for_ui(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform analysis data for UI consumption."""
        pass


class HoldingsPlugin(AnalysisPlugin):
    """Plugin for holdings analysis."""
    
    @property
    def analysis_type(self) -> str:
        return "holdings"
    
    @property
    def display_name(self) -> str:
        return "Holdings Analysis"
    
    @property
    def icon(self) -> str:
        return "📊"
    
    @property
    def requires_category(self) -> bool:
        return True
    
    def get_categories(self, date: str) -> List[str]:
        date_dir = ANALYSIS_ROOT / date / "holdings"
        if not date_dir.exists():
            return []
        # For holdings, categories are JSON files
        categories = []
        for file_path in date_dir.glob("*.json"):
            categories.append(file_path.stem)
        return sorted(categories)
    
    def get_analysis_data(self, date: str, category: Optional[str] = None) -> Dict[str, Any]:
        if not category:
            raise HTTPException(status_code=400, detail="Category required for holdings analysis")

        file_path = ANALYSIS_ROOT / date / "holdings" / f"{category}.json"
        if not file_path.exists():
            return self._empty_holdings_structure()

        return json.loads(file_path.read_text(encoding="utf-8"))
    
    def get_funds_data(self, date: str, category: Optional[str] = None) -> Dict[str, Any]:
        if not category:
            return {"funds": []}
        
        date_dir = EXTRACTED_ROOT / date / "holdings" / category
        if not date_dir.exists():
            return {"funds": []}

        items = []
        for fp in sorted(date_dir.glob("*.json")):
            try:
                raw = json.loads(fp.read_text(encoding="utf-8"))
                d = raw.get("data") or {}
                fund = d.get("fund_info") or {}
                holdings = d.get("top_holdings") or []
                
                parsed = []
                for h in holdings[:10]:
                    name = (h.get("company_name") or "").strip()
                    w = h.get("allocation_percentage") or ""
                    try:
                        wv = float(str(w).replace('%','').strip())
                    except Exception:
                        wv = 0.0
                    parsed.append({"company": name, "weight": wv})
                
                items.append({
                    "fund_name": fund.get("fund_name") or fp.stem,
                    "aum": fund.get("aum") or "",
                    "holdings": parsed,
                })
            except Exception:
                continue
        
        return {"funds": items}
    
    def transform_for_ui(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Holdings data is already in the correct format
        return data
    
    def _empty_holdings_structure(self) -> Dict[str, Any]:
        return {
            "total_files": 0,
            "total_funds": 0,
            "funds": [],
            "unique_companies": 0,
            "top_by_fund_count": [],
            "top_by_total_weight": [],
            "common_in_all_funds": [],
        }


class PortfolioPlugin(AnalysisPlugin):
    """Plugin for portfolio analysis."""
    
    @property
    def analysis_type(self) -> str:
        return "portfolio"
    
    @property
    def display_name(self) -> str:
        return "Portfolio Analysis"
    
    @property
    def icon(self) -> str:
        return "💼"
    
    @property
    def requires_category(self) -> bool:
        return False
    
    def get_categories(self, date: str) -> List[str]:
        # Portfolio doesn't use categories
        return []
    
    def get_analysis_data(self, date: str, category: Optional[str] = None) -> Dict[str, Any]:
        file_path = ANALYSIS_ROOT / date / "portfolio" / "portfolio.json"
        if not file_path.exists():
            return self._empty_portfolio_structure()

        return json.loads(file_path.read_text(encoding="utf-8"))
    
    def get_funds_data(self, date: str, category: Optional[str] = None) -> Dict[str, Any]:
        date_dir = EXTRACTED_ROOT / date / "portfolio"
        if not date_dir.exists():
            return {"funds": []}

        items = []
        for fp in sorted(date_dir.glob("*.json")):
            try:
                raw = json.loads(fp.read_text(encoding="utf-8"))
                d = raw.get("data") or {}
                fund = d.get("fund_info") or {}
                holdings = d.get("top_holdings") or []

                # For portfolio, show different structure - fund value, NAV, etc.
                fund_name = fund.get("fund_name") or fp.stem
                nav = fund.get("current_nav") or 0.0

                parsed = []
                for h in holdings[:10]:
                    name = (h.get("company_name") or "").strip()
                    pct = h.get("allocation_percentage") or ""
                    try:
                        pct_val = float(str(pct).replace('%','').strip())
                    except Exception:
                        pct_val = 0.0
                    parsed.append({"company": name, "percentage": pct_val})

                items.append({
                    "fund_name": fund_name,
                    "nav": nav,
                    "holdings": parsed,
                })
            except Exception:
                continue

        return {"funds": items}
    
    def transform_for_ui(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform portfolio data for UI consumption."""
        if not data:
            return self._empty_portfolio_structure()
        
        summary = data.get("portfolio_summary", {})
        funds = data.get("funds", [])
        allocations = data.get("company_allocations", [])
        top_companies = data.get("top_companies", [])
        
        return {
            "type": "portfolio",
            "summary": {
                "total_value": summary.get("total_value", 0),
                "fund_count": summary.get("fund_count", 0),
                "unique_companies": summary.get("unique_companies", 0),
                "formatted_value": f"₹{summary.get('total_value', 0):,}"
            },
            "funds": funds,
            "company_allocations": allocations[:50],  # Top 50 for UI
            "top_companies": top_companies,
            "charts": {
                "fund_distribution": [
                    {"name": f["fund_name"], "value": f["value"], "percentage": round((f["value"] / summary.get("total_value", 1)) * 100, 2)}
                    for f in funds
                ],
                "top_companies": [
                    {"name": c["company_name"], "amount": c["amount"], "percentage": c["percentage"]}
                    for c in allocations[:10]
                ]
            }
        }
    
    def _empty_portfolio_structure(self) -> Dict[str, Any]:
        return {
            "type": "portfolio",
            "summary": {"total_value": 0, "fund_count": 0, "unique_companies": 0},
            "funds": [],
            "company_allocations": [],
            "top_companies": [],
            "charts": {"fund_distribution": [], "top_companies": []}
        }


# Plugin Registry
ANALYSIS_PLUGINS: Dict[str, AnalysisPlugin] = {
    "holdings": HoldingsPlugin(),
    "portfolio": PortfolioPlugin(),
}


def get_plugin(analysis_type: str) -> AnalysisPlugin:
    """Get plugin by analysis type."""
    if analysis_type not in ANALYSIS_PLUGINS:
        raise HTTPException(status_code=404, detail=f"Analysis type '{analysis_type}' not found")
    return ANALYSIS_PLUGINS[analysis_type]


# ==================== API ENDPOINTS ====================

@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/dates")
def list_dates() -> JSONResponse:
    """Get available analysis dates."""
    if not ANALYSIS_ROOT.exists():
        return JSONResponse(content={"dates": []})
    dates: List[str] = sorted([p.name for p in ANALYSIS_ROOT.iterdir() if p.is_dir()])
    return JSONResponse(content={"dates": dates})


@app.get("/api/analysis-types")
def list_analysis_types(date: str) -> JSONResponse:
    """Get available analysis types for a given date."""
    if not ANALYSIS_ROOT.exists():
        return JSONResponse(content={"analysis_types": []})
    
    date_dir = ANALYSIS_ROOT / date
    if not date_dir.exists():
        return JSONResponse(content={"analysis_types": []})
    
    available_types = []
    for analysis_type, plugin in ANALYSIS_PLUGINS.items():
        # Check if this analysis type has data for the given date
        try:
            # Try to get analysis data - if successful, this type is available
            plugin.get_analysis_data(date, None if not plugin.requires_category else "dummy")
            available_types.append({
                "type": analysis_type,
                "display_name": plugin.display_name,
                "icon": plugin.icon,
                "requires_category": plugin.requires_category
            })
        except (HTTPException, FileNotFoundError):
            # For holdings, we need to check if any categories exist
            if plugin.requires_category:
                categories = plugin.get_categories(date)
                if categories:
                    available_types.append({
                        "type": analysis_type,
                        "display_name": plugin.display_name,
                        "icon": plugin.icon,
                        "requires_category": plugin.requires_category
                    })
    
    return JSONResponse(content={"analysis_types": available_types})


@app.get("/api/categories")
def list_categories(date: str, analysis_type: str = "holdings") -> JSONResponse:
    """Get available categories for a specific analysis type and date."""
    plugin = get_plugin(analysis_type)
    categories = plugin.get_categories(date)
    return JSONResponse(content={"categories": categories})


@app.get("/api/data")
def get_analysis_data(date: str, analysis_type: str, category: Optional[str] = None) -> JSONResponse:
    """Get analysis data for a specific type and date."""
    plugin = get_plugin(analysis_type)
    
    # Validate category requirement
    if plugin.requires_category and not category:
        raise HTTPException(status_code=400, detail=f"Category required for {analysis_type} analysis")
    
    try:
        raw_data = plugin.get_analysis_data(date, category)
        ui_data = plugin.transform_for_ui(raw_data)
        return JSONResponse(content=ui_data)
    except FileNotFoundError:
        # Return appropriate empty structure
        empty_data = plugin.transform_for_ui({})
        return JSONResponse(content=empty_data)


@app.get("/api/funds")
def get_funds_data(date: str, analysis_type: str, category: Optional[str] = None) -> JSONResponse:
    """Get funds composition data for a specific analysis type and date."""
    plugin = get_plugin(analysis_type)
    
    # Validate category requirement
    if plugin.requires_category and not category:
        raise HTTPException(status_code=400, detail=f"Category required for {analysis_type} analysis")
    
    try:
        funds_data = plugin.get_funds_data(date, category)
        return JSONResponse(content=funds_data)
    except FileNotFoundError:
        return JSONResponse(content={"funds": []})


# ==================== LEGACY ENDPOINTS (for backward compatibility) ====================

@app.get("/api/legacy/categories")
def legacy_list_categories(date: str) -> JSONResponse:
    """Legacy endpoint - redirects to holdings categories."""
    return list_categories(date, "holdings")


@app.get("/api/legacy/data")
def legacy_get_data(date: str, category: str) -> JSONResponse:
    """Legacy endpoint - redirects to holdings data."""
    return get_analysis_data(date, "holdings", category)


@app.get("/api/legacy/funds")
def legacy_get_funds(date: str, category: str) -> JSONResponse:
    """Legacy endpoint - redirects to holdings funds."""
    return get_funds_data(date, "holdings", category)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8787, reload=True)


