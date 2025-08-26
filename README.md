# Mutual Fund Analyser

A production-grade, modular pipeline to:
- Extract structured data from mutual fund pages (Zerodha Coin) via Playwright
- Aggregate the extracted JSONs to compute insights (e.g., most-owned stocks, total weights)
- Visualize results through a simple web dashboard

The codebase emphasizes clean architecture, strong boundaries, Pydantic models, robust logging, and an extensible scraping core.

## Overview

Three-step pipeline:
1) Extract: Scrape fund pages into JSON artifacts under a dated/category folder structure
2) Analyze: Read all extracted JSONs for a date/category and produce a per-category analysis JSON
3) Dashboard: Interactive UI to explore analysis outputs

## Quickstart

1) Create and activate a virtual environment and install deps
```bash
make init
# Then activate for this shell:
source venv/bin/activate
```

2) Configure
```bash
cp .env.example .env        # optional if you use env vars
# Update config/config.yaml with fund URLs (by category)
```

3) Install Playwright browsers (first time only)
```bash
python -m playwright install
```

4) Run orchestrator (scraping) for a category
```bash
# Using Makefile (reads categories from config/config.yaml)
make orchestrate CATEGORY=midCap

# Or via installed CLI after `pip install -e .`
mfa-orchestrate --category midCap
mfa-orchestrate                # all categories
```

5) Run analyzer to generate per-category analysis JSONs
```bash
# Analyze for a given date (YYYYMMDD) and optional category
make analyze DATE=20250826 CATEGORY=midCap

# Or via CLI
mfa-analyze --date 20250826 --category midCap
mfa-analyze --date 20250826   # all categories for that date
mfa-analyze                   # defaults to current date, all categories
```

6) Launch the dashboard
```bash
make dashboard
# Open http://localhost:8787
```

## Project Layout

```
mutual-fund-analyser/
  config/config.yaml             # central config (paths, scraping, funds by category)
  outputs/
    extracted_json/<YYYYMMDD>/<category>/*.json   # raw per-fund extractions
    analysis/<YYYYMMDD>/<category>.json           # aggregated analysis per category
  dashboard/
    server.py                    # FastAPI backend (serves API + static UI)
    static/index.html            # Frontend (Chart.js + vanilla JS)
  src/mfa/
    cli/                         # CLI entrypoints
      orchestrate.py             # Orchestrates scraping for configured categories
      scrape.py                  # Direct scrape (if needed)
      analyze.py                 # Aggregation/analysis
      pipeline.py                # Convenience: extract + analyze
    config/settings.py           # Pydantic settings and config provider
    logging/logger.py            # Loguru setup
    models/schemas.py            # Pydantic models (extraction + analysis)
    scraping/
      core/playwright_scraper.py # Reusable Playwright session + helper methods
      zerodha_coin.py            # Site-specific scraper extending core
    utils/paths.py
  pyproject.toml                 # project metadata, dependencies, CLI scripts (mfa-*)
  Makefile                       # dev workflow (init, orchestrate, analyze, dashboard)
  README.md                      # this file
```

## Configuration

Edit `config/config.yaml`:
```yaml
paths:
  output_dir: outputs/extracted_json
  analysis_dir: outputs/analysis

scraping:
  engine: playwright
  playwright:
    headless: false

funds:
  largeCap:
    - https://coin.zerodha.com/mf/fund/...
  midCap:
    - https://coin.zerodha.com/mf/fund/...
  smallCap:
    - https://coin.zerodha.com/mf/fund/...
```
- Run all categories: `make orchestrate`
- Run specific category: `make orchestrate CATEGORY=midCap`

## Data formats

- Extraction JSON (one file per fund):
```json
{
  "schema_version": "1.0",
  "extraction_timestamp": "2025-08-26T10:11:46.924835",
  "source_url": "https://coin.zerodha.com/mf/fund/...",
  "provider": "playwright",
  "data": {
    "fund_info": {
      "fund_name": "HDFC Mid Cap Fund",
      "current_nav": "₹213.977",
      "cagr": "",
      "expense_ratio": "0.74%",
      "aum": "₹83,847.39 Cr.",
      "fund_manager": "Mr. X",
      "launch_date": "",
      "risk_level": "Very High"
    },
    "top_holdings": [
      { "rank": 1, "company_name": "Max Financial Services Ltd.", "allocation_percentage": "4.59%" }
      // up to 10
    ]
  }
}
```

- Analysis JSON (one file per category per date): `outputs/analysis/<date>/<category>.json`
```json
{
  "schema_version": "1.0",
  "total_files": 7,
  "total_funds": 7,
  "funds": [ { "name": "HDFC Mid Cap Fund", "aum": "₹83,847.39 Cr." } ],
  "unique_companies": 123,
  "top_by_fund_count": [ { "company": "HDFC Bank", "fund_count": 6, "total_weight": 8.4, "avg_weight": 1.4 } ],
  "top_by_total_weight": [ ... ],
  "common_in_all_funds": [ ... ]
}
```

## Key design points

- Clean architecture: site-agnostic base (`PlaywrightScraper`) + site-specific scraper (`ZerodhaCoinScraper`)
- Pydantic models for all inputs/outputs (type-safe, versioned schemas)
- One class per file; reusable helpers live in the core scraper
- Robust Playwright usage: reusable session, tab selection, lazy session open, graceful waits
- Logging via Loguru (debug, info, warnings; file rotation is configured)

## Common commands

- Initialize dev env: `make init`
- Orchestrate scrape: `make orchestrate CATEGORY=midCap`
- Analyze outputs: `make analyze DATE=YYYYMMDD CATEGORY=midCap`
- Full pipeline: `make pipeline`
- Dashboard: `make dashboard` then open http://localhost:8787
- Lint/format/test: `make lint`, `make format`, `make test`

CLI (via pyproject installed scripts): `mfa-orchestrate`, `mfa-analyze`, `mfa-scrape`, `mfa-pipeline`

## Troubleshooting

- Playwright browsers not installed: run `python -m playwright install`
- Empty holdings: ensure the scraper can click "Holdings" and "Show all"; try headless=false in config
- Venv issues after moving folders: delete `venv/` and run `make init`
- Dashboard not loading data: ensure `outputs/analysis/<date>/<category>.json` exists and is valid

## License
MIT
