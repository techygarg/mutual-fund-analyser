# Mutual Fund Analyser

A clean, configurable framework to analyze mutual fund holdings:
- **Extract** structured data from mutual fund pages (Zerodha Coin) via Playwright
- **Analyze** the data to find common holdings, overlaps, and investment patterns
- **Visualize** results through a simple web dashboard

Built with clean architecture, modular design, and user-friendly configuration.

## Overview

Three-step pipeline:
1) Extract: Scrape fund pages into JSON artifacts under a dated/category folder structure
2) Analyze: Read all extracted JSONs for a date/category and produce a per-category analysis JSON
3) Dashboard: Interactive UI to explore analysis outputs

## Getting Started

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-username/mutual-fund-analyser.git
cd mutual-fund-analyser

# Setup virtual environment and install dependencies
make init

# Activate the virtual environment
source venv/bin/activate

# Install Playwright browsers (required for scraping)
python -m playwright install
```

### 2. Configure (Optional)

The framework works out of the box, but you can customize `config/config.yaml`:

```bash
# Edit configuration to adjust scraping behavior, analysis settings, or add custom funds
nano config/config.yaml
```

### 3. Run Analysis

```bash
# Scrape funds for a specific category
make orchestrate CATEGORY=midCap

# Analyze the scraped data  
make analyze CATEGORY=midCap

# Or run both steps together
make pipeline CATEGORY=midCap

# Launch interactive dashboard
make dashboard
# Open http://localhost:8787 in your browser
```

### 4. CLI Usage (Alternative)

You can also use CLI commands directly:

```bash
# Scraping
mfa-orchestrate --category midCap    # specific category
mfa-orchestrate                      # all categories

# Analysis  
mfa-analyze --category midCap        # specific category
mfa-analyze --date 20250826          # specific date

# Full pipeline
mfa-pipeline --category midCap       # scrape + analyze
```

## Project Layout

```
mutual-fund-analyser/
  config/config.yaml             # simplified user configuration
  outputs/
    extracted_json/<YYYYMMDD>/<category>/*.json   # scraped fund data
    analysis/<YYYYMMDD>/<category>.json           # analysis results
  src/mfa/
    cli/                         # thin CLI layer (argument parsing only)
      orchestrate.py             # fund scraping entry point
      analyze.py                 # analysis entry point
      pipeline.py                # combined scrape + analyze
      scrape.py                  # direct scraping utility
    orchestration/               # business logic for fund data collection
      orchestrator.py            # coordinates scraping across categories
    analysis/                    # business logic for holdings analysis
      analyzer.py                # processes scraped data, finds patterns
    storage/                     # file I/O operations
      json_store.py              # JSON save/load with error handling
    scraping/                    # site-specific scrapers
      core/playwright_scraper.py # reusable browser automation
      zerodha_coin.py            # Zerodha Coin specific scraper
    web/                         # dashboard components
      server.py                  # FastAPI backend + static file serving
      static/index.html          # frontend (Chart.js + vanilla JS)
    config/settings.py           # configuration management
    logging/logger.py            # structured logging setup
    models/schemas.py            # data models and validation
  pyproject.toml                 # project metadata and CLI scripts
  Makefile                       # development workflow automation
  README.md                      # this documentation
```

## Configuration

The framework is configured via `config/config.yaml`. Here are the key settings you can customize:

```yaml
# Directory paths
paths:
  output_dir: outputs/extracted_json
  analysis_dir: outputs/analysis

# Scraping behavior
scraping:
  headless: false              # Show browser window (useful for debugging)
  timeout_seconds: 30          # Page load timeout
  delay_between_requests: 1.0  # Delay between scraping each fund (be respectful)

# Analysis preferences
analysis:
  max_companies_in_results: 100          # Limit results for readability
  max_sample_funds_per_company: 5        # Example funds shown per company
  exclude_from_analysis:                 # Holdings to ignore
    - "TREPS"        # Treasury Repo
    - "CASH"         # Cash holdings
    - "T-BILLS"      # Treasury Bills

# Output formatting
output:
  filename_prefix: "coin_"               # Prefix for scraped files
  include_date_in_folder: true           # Organize by date

# Fund categories and URLs (add your own!)
funds:
  largeCap:
    - https://coin.zerodha.com/mf/fund/INF204K01XI3/nippon-india-large-cap-fund-direct-growth
    # ... more funds
  midCap:
    - https://coin.zerodha.com/mf/fund/INF179K01XQ0/hdfc-mid-cap-fund-direct-growth
  customCategory:
    - https://coin.zerodha.com/mf/fund/YOUR_FUND_ID/your-fund-name
```

**Quick commands:**
- All categories: `make orchestrate`
- Specific category: `make orchestrate CATEGORY=midCap`

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

## Key Design Points

**🏗️ Clean Architecture**
- **Thin CLI layer** - Only handles argument parsing, delegates to business logic
- **Separated concerns** - Orchestration, analysis, storage in dedicated modules
- **Configuration-driven** - User-friendly YAML config, sensible defaults

**🛠️ Modular Components**
- **Orchestrator** - Coordinates fund data collection across categories
- **Analyzer** - Processes holdings data to find patterns and overlaps
- **Storage** - Centralized JSON operations with error handling
- **Scrapers** - Site-agnostic base + site-specific implementations

**🔧 Quality & Reliability**
- **Type safety** - Pydantic models for all data structures
- **Error handling** - Custom exceptions and graceful failure recovery
- **Comprehensive logging** - Structured logging with Loguru
- **Testable design** - Easy to unit test individual components

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
