### Architecture

This project follows a clean, extensible structure inspired by a 4-layer approach:
- Application: CLI entrypoints orchestrate workflows (scrape, analyze, pipeline)
- Scraper (Tooling layer): Base Playwright helpers + site-specific scraper
- Models: Pydantic schemas for extraction and analysis
- Providers/Config: Centralized Pydantic-based settings and YAML-backed config

#### Scraping
- Core: `mfa/scraping/core/playwright_scraper.py` provides
  - `PlaywrightSession` for reusable browser/context/page handling (lazy-open)
  - Navigation helpers: goto(), click_holdings_tab(), click_show_all(), find_holdings_table()
  - Parsing helpers: parse_holdings_from_table(), parse_holdings_from_any_table()
- Site-specific: `mfa/scraping/zerodha_coin.py` implements `ZerodhaCoinScraper.scrape(url)`
  - Uses base helpers to navigate, reveal "Top holdings", and parse the table
  - Builds `ExtractedFundDocument` via Pydantic models

#### Data
- Extraction JSON: one file per fund, versioned schema
- Analysis JSON: one file per category per date with aggregate metrics

#### Orchestration
- `mfa/cli/orchestrate.py` reads `config/config.yaml` for categories and URLs
- Outputs to `outputs/extracted_json/<date>/<category>/`

#### Analysis
- `mfa/cli/analyze.py` walks per-date/category extractions, normalizes company names, aggregates, and writes
  `outputs/analysis/<date>/<category>.json`

#### Dashboard
- `dashboard/server.py` (FastAPI) serves API endpoints and static UI
- `dashboard/static/index.html` uses Chart.js for bar charts and interactive tables

#### Logging
- Loguru configured in `mfa/logging/logger.py` with rotating files and console output

#### Principles
- One class per file; keep site-specific logic minimal
- Pydantic ensures type safety and JSON serialization
- Explicit boundaries between scraping, analysis, and presentation layers
