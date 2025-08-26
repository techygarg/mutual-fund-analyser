from __future__ import annotations

import json
from pathlib import Path
from typing import List

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


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/dates")
def list_dates() -> JSONResponse:
    if not ANALYSIS_ROOT.exists():
        return JSONResponse(content={"dates": []})
    dates: List[str] = sorted([p.name for p in ANALYSIS_ROOT.iterdir() if p.is_dir()])
    return JSONResponse(content={"dates": dates})


@app.get("/api/categories")
def list_categories(date: str) -> JSONResponse:
    date_dir = ANALYSIS_ROOT / date
    if not date_dir.exists():
        return JSONResponse(content={"categories": []})
    cats = sorted([p.stem for p in date_dir.glob("*.json")])
    return JSONResponse(content={"categories": cats})


@app.get("/api/data")
def get_data(date: str, category: str) -> JSONResponse:
    fp = ANALYSIS_ROOT / date / f"{category}.json"
    if not fp.exists():
        # graceful empty structure
        return JSONResponse(content={
            "total_files": 0,
            "total_funds": 0,
            "funds": [],
            "unique_companies": 0,
            "top_by_fund_count": [],
            "top_by_total_weight": [],
            "common_in_all_funds": [],
        })
    data = json.loads(fp.read_text(encoding="utf-8"))
    return JSONResponse(content=data)


@app.get("/api/funds")
def get_funds(date: str, category: str) -> JSONResponse:
    date_dir = EXTRACTED_ROOT / date / category
    if not date_dir.exists():
        return JSONResponse(content={"funds": []})
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
                # parse percent
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
    return JSONResponse(content={"funds": items})


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8787, reload=True)


