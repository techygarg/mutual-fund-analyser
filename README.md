# Mutual Fund Analyser

![CI Pipeline](https://github.com/techygarg/mutual-fund-analyser/workflows/CI%20Pipeline/badge.svg)
![Quick Check](https://github.com/techygarg/mutual-fund-analyser/workflows/Quick%20Check/badge.svg)
[![codecov](https://codecov.io/gh/techygarg/mutual-fund-analyser/branch/main/graph/badge.svg)](https://codecov.io/gh/techygarg/mutual-fund-analyser)

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

## Prerequisites

Before you can run the Mutual Fund Analyser, ensure you have the following installed:

### 🐍 **Python Requirements**
- **Python 3.10 or higher** - Check with `python --version` or `python3 --version`
- **pip** - Python package manager (usually included with Python)

### 💻 **System Requirements**

**Additional Tools:**
- **Make** (optional) - For using Makefile commands

### 🔍 **Quick Check**

Verify your system is ready:

```bash
# Check Python version (should be 3.10+)
python --version
# or
python3 --version

# Check pip is available
pip --version
# or  
pip3 --version

# Check make is available (optional)
make --version
```

**Expected output:**
```
Python 3.10.0 (or higher)
pip 23.0.0 (or similar)
GNU Make 4.3 (or similar)
```

### 🚨 **Installation Help**

**If Python 3.10+ is not installed:**
- **macOS**: Install via [Homebrew](https://brew.sh/) → `brew install python@3.10`
- **Linux**: `sudo apt update && sudo apt install python3.10 python3.10-venv`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

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

### 3. Run Analysis

```bash
# Scrape funds for a specific category
make scrape CATEGORY=midCap

# Analyze the scraped data  
make analyze CATEGORY=midCap

# Or run both steps together
make pipeline CATEGORY=midCap

# Launch interactive dashboard
make dashboard
# Open http://localhost:8787 in your browser
```

## What Happens When You Run Commands

Understanding what each command does behind the scenes:

### 🕷️ **Scraping (Data Collection)**

```bash
# Process specific category
make scrape CATEGORY=midCap

# Process ALL categories (default behavior)
make scrape
```

**What happens:**
1. **Reads Configuration**: Loads fund URLs from `config/config.yaml`
2. **Creates Output Structure**: 
   ```
   outputs/extracted_json/YYYYMMDD/
   ├── largeCap/     # If processing all categories
   ├── midCap/       # Your target category
   └── smallCap/     # If processing all categories
   ```
3. **Browser Automation**: Opens browser session (shared across all categories for efficiency)
4. **Fund Scraping**: For each fund URL:
   - Navigates to fund page
   - Extracts fund info (name, AUM, expense ratio, etc.)
   - Scrapes top 10 holdings with allocation percentages
   - Saves as `coin_FUND_ID_fund-name.json`
5. **Session Cleanup**: Properly closes browser after all scraping

**Output Files Created:**
```
outputs/extracted_json/20250827/midCap/
├── coin_INF179K01XQ0_hdfc-mid-cap-fund-direct-growth.json
├── coin_INF174K01LT0_kotak-midcap-fund-direct-growth.json
├── coin_INF200K01TP4_sbi-midcap-fund-direct-growth.json
└── ... (one file per fund)
```

**Default Behavior:**
- **No CATEGORY**: Processes **all categories** defined in config
- **Automatic Dating**: Uses current date (YYYYMMDD format)
- **Respectful Scraping**: 1-second delay between requests (configurable)

### 📊 **Analysis (Pattern Detection)**

```bash
# Analyze specific category and date
make analyze DATE=20250827 CATEGORY=midCap

# Analyze specific category (uses today's date)
make analyze CATEGORY=midCap

# Analyze ALL categories for today (default behavior)
make analyze
```

**What happens:**
1. **Input Discovery**: Scans for extracted JSON files
   - **Default Date**: Uses current date if not specified
   - **Default Category**: Processes all available categories if not specified
2. **File Processing**: Reads all fund JSON files in target directory
3. **Data Aggregation**: 
   - Normalizes company names (handles duplicates like "HDFC Bank" vs "HDFC BANK")
   - Filters out non-stock holdings (TREPS, CASH, etc.)
   - Calculates total weights and fund counts per company
4. **Pattern Analysis**:
   - Finds companies appearing in most funds
   - Identifies highest total weight allocations
   - Discovers common holdings across ALL funds
5. **Output Generation**: Creates analysis summary JSON

**Input Files Used:**
```
outputs/extracted_json/20250827/midCap/*.json  # All fund files
```

**Output Files Created:**
```
outputs/analysis/20250827/
├── largeCap.json    # If processing all categories
├── midCap.json      # Your analysis results
└── smallCap.json    # If processing all categories
```

**Default Behavior:**
- **No DATE**: Uses **current date** (looks for today's scraped data)
- **No CATEGORY**: Analyzes **all categories** found in the date folder
- **Automatic Cleanup**: Excludes treasury instruments, cash holdings, etc.

### ⚡ **Pipeline (Complete Workflow)**

```bash
# Run scrape + analyze for specific category
make pipeline CATEGORY=midCap

# Run scrape + analyze for ALL categories
make pipeline
```

**What happens:**
1. Runs scraping first
2. Automatically runs analysis on the freshly scraped data
3. Creates both extracted JSON files AND analysis summaries

### 🌐 **Dashboard (Visualization)**

```bash
make dashboard
# Open http://localhost:8787
```

**What happens:**
1. **Starts Web Server**: FastAPI server on port 8787
2. **Serves Analysis Data**: Reads from `outputs/analysis/` directory
3. **Interactive UI**: 
   - Date picker (shows available analysis dates)
   - Category selector (shows categories for selected date)
   - Analysis tab: Charts and tables of fund overlaps
   - Funds tab: Individual fund composition charts

**Data Sources Used:**
- `outputs/analysis/*/` - For analysis charts and tables
- `outputs/extracted_json/*/` - For individual fund details

### 🔄 **Typical Workflow**

```bash
# Daily analysis routine
make scrape               # Scrape all categories (takes 10-15 min)
make analyze              # Analyze all categories (takes <1 min)  
make dashboard            # Launch dashboard to explore results

# Quick single-category check
make pipeline CATEGORY=midCap    # Scrape + analyze midCap only
```

### 4. CLI Usage (Alternative)

You can also use CLI commands directly:

```bash
# Scraping
mfa-orchestrate --category midCap    # specific category
mfa-orchestrate                      # all categories

# Analysis  
mfa-analyze --category midCap        # specific category (today's date)
mfa-analyze --date 20250826          # specific date (all categories)
mfa-analyze --date 20250826 --category midCap  # specific date + category

# Full pipeline
mfa-pipeline --category midCap       # scrape + analyze specific category
mfa-pipeline                         # scrape + analyze all categories
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
- All categories: `make scrape`
- Specific category: `make scrape CATEGORY=midCap`

## Data Formats and Structure

### 📄 **Extracted Fund Data** 
*Location: `outputs/extracted_json/YYYYMMDD/category/coin_*.json`*

One JSON file per fund containing raw scraped data:

```json
{
  "schema_version": "1.0",
  "extraction_timestamp": "2025-08-26T10:11:46.924835",
  "source_url": "https://coin.zerodha.com/mf/fund/INF179K01XQ0/hdfc-mid-cap-fund-direct-growth",
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
      { 
        "rank": 1, 
        "company_name": "Max Financial Services Ltd.", 
        "allocation_percentage": "4.59%" 
      },
      { 
        "rank": 2, 
        "company_name": "Federal Bank", 
        "allocation_percentage": "3.42%" 
      }
      // ... up to 10 holdings
    ]
  }
}
```

**📊 What this contains:**
- **Fund metadata**: Name, AUM, expense ratio, NAV, fund manager details
- **Top 10 holdings**: Company names and their allocation percentages
- **Scraping metadata**: When and how the data was extracted

### 📈 **Analysis Summary Data**
*Location: `outputs/analysis/YYYYMMDD/category.json`*

One JSON file per category containing aggregated insights:

```json
{
  "schema_version": "1.0",
  "total_files": 7,
  "total_funds": 7,
  "unique_companies": 54,
  "funds": [
    { "name": "HDFC Mid Cap Fund", "aum": "₹83,847.39 Cr." },
    { "name": "Kotak Midcap Fund", "aum": "₹57,375.20 Cr." }
    // ... all funds in category
  ],
  "top_by_fund_count": [
    {
      "name": "Federal Bank",
      "fund_count": 4,           // Appears in 4 out of 7 funds
      "total_weight": 9.68,     // Combined allocation across all funds
      "avg_weight": 2.42,       // Average allocation per fund
      "sample_funds": [         // Which funds hold this stock
        "HDFC Mid Cap Fund",
        "SBI Midcap Fund",
        "Axis Midcap Fund",
        "Nippon India Growth Mid Cap Fund"
      ]
    }
    // ... ranked by number of funds holding the stock
  ],
  "top_by_total_weight": [
    {
      "name": "Trent",
      "fund_count": 1,
      "total_weight": 7.84,     // Highest total allocation
      "avg_weight": 7.84,
      "sample_funds": [ "Motilal Oswal Midcap Fund" ]
    }
    // ... ranked by total allocation percentage
  ],
  "common_in_all_funds": [
    // Companies that appear in ALL funds (rare but valuable insight)
    {
      "name": "HDFC Bank",
      "fund_count": 7,          // All 7 funds hold this
      "total_weight": 15.23,
      "avg_weight": 2.17
    }
  ]
}
```

**🎯 What this contains:**
- **Portfolio overlap analysis**: Which stocks appear in multiple funds
- **Concentration insights**: Highest allocated stocks across the category
- **Common holdings**: Stocks that ALL funds in the category hold
- **Fund summaries**: Basic info about each fund analyzed
- **Statistical insights**: Total companies, fund counts, allocation patterns

### 📁 **File Naming Conventions**

**Extracted files:**
- Pattern: `coin_{FUND_ID}_{fund-name-slug}.json`
- Example: `coin_INF179K01XQ0_hdfc-mid-cap-fund-direct-growth.json`
- Purpose: Unique identifier per fund, easy to trace back to source URL

**Analysis files:**
- Pattern: `{category}.json`
- Example: `midCap.json`, `largeCap.json`, `smallCap.json`
- Purpose: One summary per category, easy dashboard consumption

**Directory structure:**
- **Date-based**: `YYYYMMDD` folders allow historical tracking
- **Category-based**: Separate analysis by fund type (large/mid/small cap)
- **Hierarchical**: Clear separation between raw data and processed insights

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

## Command Reference

### Development Commands
- `make init` - Setup virtual environment and install dependencies
- `make format` - Auto-format code with Ruff
- `make lint` - Run code linting and type checking
- `make clean` - Clean build artifacts and caches

### Analysis Commands
| Command | What it does | Default behavior |
|---------|--------------|------------------|
| `make scrape` | Scrape all fund categories | Processes **all categories** from config |
| `make scrape CATEGORY=midCap` | Scrape specific category | Processes only midCap funds |
| `make analyze` | Analyze today's data | Uses **current date**, processes **all categories** |
| `make analyze CATEGORY=midCap` | Analyze specific category | Uses **current date**, processes only midCap |
| `make analyze DATE=20250826` | Analyze specific date | Processes **all categories** for that date |
| `make pipeline` | Scrape + analyze | Runs both steps for **all categories** |
| `make pipeline CATEGORY=midCap` | Scrape + analyze category | Runs both steps for specific category |
| `make dashboard` | Start web dashboard | Serves analysis results at http://localhost:8787 |

### CLI Alternatives
After `pip install -e .`, you can use these commands directly:
```bash
mfa-orchestrate [--category CATEGORY]    # Scraping
mfa-analyze [--date DATE] [--category CATEGORY]  # Analysis  
mfa-pipeline [--category CATEGORY]       # Both steps
```

### Output Structure
**After Orchestration:**
```
outputs/extracted_json/YYYYMMDD/
├── largeCap/
│   ├── coin_fund1.json
│   └── coin_fund2.json
├── midCap/
│   ├── coin_fund3.json
│   └── coin_fund4.json
└── smallCap/
    ├── coin_fund5.json
    └── coin_fund6.json
```

**After Analysis:**
```
outputs/analysis/YYYYMMDD/
├── largeCap.json    # Summary: top holdings, overlaps, patterns
├── midCap.json      # Summary: top holdings, overlaps, patterns  
└── smallCap.json    # Summary: top holdings, overlaps, patterns
```

## Example Workflows

### 📅 **Daily Analysis Routine**
```bash
# Monday morning: Get fresh data for all categories
make scrape                      # Scrapes all funds (~15 min)
make analyze                     # Analyzes all categories (~1 min)
make dashboard                   # Launch dashboard to explore
# Open http://localhost:8787 to see results
```

### 🎯 **Quick Category Check**
```bash
# Just check midCap funds today
make pipeline CATEGORY=midCap   # Scrape + analyze midCap only (~3 min)
make dashboard                   # View results
```

### 🔍 **Historical Analysis**
```bash
# Compare today vs last week
make analyze DATE=20250820       # Analyze last week's data
make analyze                     # Analyze today's data
make dashboard                   # Switch between dates in UI
```

### 🔧 **Development Workflow**
```bash
# Setting up for development
make init                        # Setup environment
make format                      # Format code
make lint                        # Check code quality

# Testing configuration changes
make scrape CATEGORY=midCap      # Test with small dataset
make analyze CATEGORY=midCap     # Verify analysis works
```

## Understanding the Output

### 📊 **What the Analysis Tells You**

**Top by Fund Count**: 
- Shows which stocks are **most popular** across funds
- High fund count = broad consensus among fund managers
- Example: "Federal Bank appears in 4 out of 7 midCap funds"

**Top by Total Weight**:
- Shows which stocks have **highest combined allocations**
- High total weight = significant collective investment
- Example: "Trent has 7.84% total allocation (mostly from one fund)"

**Common in All Funds**:
- Shows stocks that **every fund** in the category holds
- Rare but valuable = core holdings for that category
- Empty list is normal (perfect overlap is uncommon)

### 🌐 **Dashboard Features**

**Analysis Tab**:
- Interactive charts showing top holdings patterns
- Sortable tables with detailed breakdowns
- Visual representation of fund overlaps

**Funds Tab**:
- Individual fund composition charts
- Compare holdings across different funds
- See fund-specific allocation patterns

## Troubleshooting

**💡 First check:** If you're having basic setup issues, review the **[Prerequisites section](#prerequisites)** to ensure all required software is installed correctly.

### 🔧 **Setup Issues**
| Problem | Solution |
|---------|----------|
| `python: command not found` | Install Python 3.10+ - see [Prerequisites section](#prerequisites) |
| `make: command not found` | Install Make or use CLI commands directly - see [Prerequisites section](#prerequisites) |
| `git: command not found` | Install Git - see [Prerequisites section](#prerequisites) |
| `ModuleNotFoundError: No module named 'mfa'` | Run `pip install -e ".[dev]"` in activated venv |
| `playwright` command not found | Run `python -m playwright install` |
| Virtual environment issues | Delete `venv/` folder and run `make init` |
| Permission errors | Check file permissions, avoid running as root |
| `Python version too old` | Upgrade to Python 3.10+ - see [Prerequisites section](#prerequisites) |

### 🕸️ **Scraping Issues**
| Problem | Solution |
|---------|----------|
| Empty holdings data | Set `headless: false` in config to debug browser |
| Timeout errors | Increase `timeout_seconds` in config.yaml |
| Rate limiting | Increase `delay_between_requests` in config |
| "Address already in use" for dashboard | Kill existing process: `pkill -f uvicorn` |

### 📊 **Analysis Issues**
| Problem | Solution |
|---------|----------|
| "No analysis data found" | Ensure scraping completed successfully |
| Dashboard shows empty charts | Check that analysis JSON files exist and aren't empty |
| Wrong date in dashboard | Verify folder names match YYYYMMDD format |
| Missing categories | Check that extracted JSON folders contain data |

### 🔍 **Data Issues**
| Problem | Solution |
|---------|----------|
| Unexpected company names | Check `exclude_from_analysis` in config |
| Too many/few results | Adjust `max_companies_in_results` in config |
| Duplicate companies | Analysis auto-normalizes names (HDFC vs HDFC Bank) |
| Missing recent data | Ensure scraping used correct date folder |

## Documentation

### 📚 **Additional Resources**

For more detailed information about the framework:

- **[📐 Architecture Guide](docs/ARCHITECTURE.md)** - Technical architecture overview, design patterns, and module structure
- **[🚀 Upcoming Features](docs/UPCOMING_FEATURES.md)** - Planned enhancements including Historical Trend Analysis and Date-to-Date Comparison