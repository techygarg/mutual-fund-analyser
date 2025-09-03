# Usage Guide

Complete guide to using the Mutual Fund Analyzer with detailed examples and command reference.

## 📋 Quick Reference

### Core Commands
```bash
make analyze CATEGORY=midCap     # Extract and analyze fund data (recommended)
make dashboard                   # View results in browser
mfa-analyze --help               # Show all command options
```

### Available Categories
- `largeCap` - Large cap funds
- `midCap` - Mid cap funds
- `smallCap` - Small cap funds
- `all` - All categories (default when no category specified)

## 📊 Understanding the Analysis

### What the Tool Does

1. **Scrapes** fund data from Zerodha Coin pages
2. **Analyzes** holdings across multiple funds to find patterns
3. **Identifies** common investments and overlaps
4. **Ranks** companies by popularity and allocation

### Analysis Results

The tool generates insights like:
- **Top by Fund Count**: "HDFC Bank appears in 4 out of 7 midCap funds"
- **Top by Weight**: "Federal Bank has 9.68% combined allocation"
- **Common Holdings**: Stocks held by ALL funds in the category

## 🎯 Command Examples

### Basic Usage

**Analyze mid-cap funds:**
```bash
make analyze CATEGORY=midCap
```

**Analyze all categories:**
```bash
make analyze  # Analyzes all enabled categories
```

**View results:**
```bash
make dashboard  # Opens at http://localhost:8787
```

### Advanced Usage

**Analyze specific date:**
```bash
make analyze DATE=20250827 CATEGORY=midCap
```

**Using CLI directly:**
```bash
mfa-analyze holdings --category midCap --date 20250827 --verbose
```

**Check system status:**
```bash
mfa-analyze --status    # Show configuration status
mfa-analyze --list      # List available analysis types
```

## 📁 File Structure

### Input/Output Files

**Scraped Data (Raw):**
```
outputs/extracted_json/
├── 20250827/
│   ├── largeCap/
│   │   ├── coin_INF204K01XI3_nippon-india-large-cap-fund-direct-growth.json
│   │   └── coin_INF179K01YV8_hdfc-large-cap-fund-direct-growth.json
│   └── midCap/
│       ├── coin_INF179K01XQ0_hdfc-mid-cap-fund-direct-growth.json
│       └── coin_INF174K01LT0_kotak-midcap-fund-direct-growth.json
```

**Analysis Results:**
```
outputs/analysis/
├── 20250827/
│   ├── largeCap.json
│   ├── midCap.json
│   └── smallCap.json
```

### File Naming Convention

**Individual Fund Files:**
```
coin_{FUND_ID}_{fund-name-slug}.json
```

**Example:**
```
coin_INF179K01XQ0_hdfc-mid-cap-fund-direct-growth.json
```

**Analysis Summary Files:**
```
{category}.json
```

## 🌐 Dashboard Features

### Starting the Dashboard
```bash
make dashboard
# Open http://localhost:8787 in your browser
```

### Dashboard Tabs

**📊 Analysis Tab:**
- Interactive charts showing stock overlaps
- Sortable tables ranking companies
- Visual representation of investment patterns
- Date and category selectors

**💼 Funds Tab:**
- Individual fund composition details
- Side-by-side comparison of holdings
- Allocation percentages per stock

### Dashboard Controls

**Date Picker:** Shows available analysis dates
**Category Selector:** Choose fund category (largeCap, midCap, smallCap)
**Search/Filter:** Find specific stocks or funds
**Export:** Download data as CSV/JSON

## ⚙️ Configuration Examples

### Custom Fund Categories

Add your own fund categories in `config/config.yaml`:

```yaml
funds:
  # Built-in categories
  largeCap: [...]
  midCap: [...]
  smallCap: [...]

  # Your custom categories
  bankingFunds:
    - https://coin.zerodha.com/mf/fund/FUND_ID_1/banking-fund-1
    - https://coin.zerodha.com/mf/fund/FUND_ID_2/banking-fund-2

  techFunds:
    - https://coin.zerodha.com/mf/fund/FUND_ID_3/tech-fund-1
    - https://coin.zerodha.com/mf/fund/FUND_ID_4/tech-fund-2
```

**Usage:**
```bash
make analyze CATEGORY=bankingFunds
```

### Scraping Configuration

Optimize scraping for your needs:

```yaml
scraping:
  headless: true           # Run in background (faster)
  timeout_seconds: 30      # Page load timeout
  delay_between_requests: 1.0  # Respectful delay between requests

  # Debug mode (slower but visible)
  headless: false          # Show browser window
  timeout_seconds: 60      # More time for slow connections
  delay_between_requests: 2.0  # Extra delay
```

### Analysis Configuration

Customize analysis output:

```yaml
analysis:
  max_companies_in_results: 50     # Limit results (faster)
  max_sample_funds_per_company: 3  # Fewer examples per company
  exclude_from_analysis:           # Ignore these holdings
    - "TREPS"
    - "CASH"
    - "T-BILLS"
    - "LIQUID FUNDS"
```

## 🔄 Workflow Examples

### Daily Analysis Routine
```bash
# Morning: Get fresh data for all categories
make analyze                  # Extract + analyze all categories (~15 minutes)
make dashboard                # Review results
```

### Quick Category Check
```bash
# Just check midCap funds today
make analyze CATEGORY=midCap  # Extract + analyze midCap only (~3 minutes)
make dashboard                # View results
```

### Historical Analysis
```bash
# Compare today vs last week
make analyze DATE=20250820 CATEGORY=midCap  # Last week's data
make analyze CATEGORY=midCap                 # Today's data
make dashboard                               # Compare in dashboard
```

### Development Workflow
```bash
# Test configuration changes
make analyze CATEGORY=midCap  # Test with small dataset
make dashboard                # Check results
```

## 📊 Understanding Results

### Analysis Output Structure

**Sample Analysis JSON:**
```json
{
  "schema_version": "1.0",
  "total_files": 7,
  "total_funds": 7,
  "unique_companies": 54,
  "funds": [
    {
      "name": "HDFC Mid Cap Fund",
      "aum": "₹83,847.39 Cr."
    }
  ],
  "top_by_fund_count": [
    {
      "name": "Federal Bank",
      "fund_count": 4,
      "total_weight": 9.68,
      "avg_weight": 2.42,
      "sample_funds": ["HDFC", "SBI", "Kotak"]
    }
  ],
  "top_by_total_weight": [
    {
      "name": "Trent",
      "fund_count": 1,
      "total_weight": 7.84,
      "avg_weight": 7.84,
      "sample_funds": ["Motilal Oswal"]
    }
  ],
  "common_in_all_funds": [
    {
      "name": "HDFC Bank",
      "fund_count": 7,
      "total_weight": 15.23,
      "avg_weight": 2.17
    }
  ]
}
```

### Key Metrics Explained

**Fund Count:** Number of funds holding this stock
- Higher = More popular among fund managers
- Shows consensus in the investment community

**Total Weight:** Combined allocation percentage across all funds
- Higher = Significant collective investment
- Indicates market confidence

**Average Weight:** Typical allocation per fund
- Shows typical position sizing
- Useful for diversification analysis

**Sample Funds:** Which specific funds hold this stock
- Helps identify fund manager preferences
- Useful for fund selection

## 🔧 CLI Commands (Alternative)

If you prefer not to use Make, you can use CLI commands directly:

### After Installation
```bash
pip install -e .
```

### CLI Usage
```bash
# Basic usage (analysis_type is required)
mfa-analyze holdings                         # Analyze holdings specifically
mfa-analyze holdings --category midCap       # Analyze specific category
mfa-analyze holdings --date 20250826         # Analyze specific date
mfa-analyze holdings --verbose               # Enable detailed logging

# Informational commands (no analysis_type needed)
mfa-analyze --list                          # List available analysis types
mfa-analyze --status                        # Show configuration status
```

### CLI Help
```bash
mfa-analyze --help
```

## 📈 Advanced Usage

### Custom Date Ranges
```bash
# Analyze specific date
make analyze DATE=20250815 CATEGORY=midCap

# Analyze date range (requires future feature)
# make analyze FROM=20250801 TO=20250815 CATEGORY=midCap
```

### Batch Processing
```bash
# Process multiple categories
for category in largeCap midCap smallCap; do
    echo "Processing $category..."
    make analyze CATEGORY=$category
done
```

### Monitoring Progress
```bash
# Watch logs during scraping
tail -f outputs/mfa.log

# Check disk usage
du -sh outputs/

# Count processed files
find outputs/extracted_json/ -name "*.json" | wc -l
```

### Performance Optimization
```bash
# Reduce analysis scope for faster results
# Edit config/config.yaml:
analysis:
  max_companies_in_results: 25     # Fewer results
  max_sample_funds_per_company: 2  # Fewer examples
```

## 🎯 Best Practices

### For Regular Use
1. **Use `make analyze`** - Combines scraping + analysis efficiently
2. **Start with small categories** - Test with `midCap` before full analysis
3. **Check logs** - Monitor `outputs/mfa.log` for issues
4. **Use dashboard** - Best way to explore results interactively

### For Development
1. **Use `make test-unit`** - Verify changes don't break existing functionality
2. **Test with small datasets** - Use single category for faster iteration
3. **Check configuration** - Validate `config/config.yaml` after changes
4. **Monitor resource usage** - Watch memory and disk space during scraping

### For Production
1. **Schedule regular runs** - Use cron jobs for daily analysis
2. **Monitor disk space** - Clean old data periodically
3. **Backup important results** - Save valuable analysis outputs
4. **Update regularly** - Pull latest changes and update dependencies
