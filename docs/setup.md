# Setup Guide

Complete setup guide to get MFA running on your system.

## 🚀 Quick Setup

```bash
# 1. Clone repository
git clone https://github.com/techygarg/mutual-fund-analyser.git
cd mutual-fund-analyser

# 2. Install dependencies  
make init
source venv/bin/activate
# 3. Configure your analysis (see Configuration section below)
# Edit config/config.yaml

# 4. Run analysis
mfa-analyze holdings    # For holdings analysis
mfa-analyze portfolio   # For portfolio analysis

# 5. View results
make dashboard
# Open http://localhost:8787
```

## 📋 Requirements

- **Python 3.10+**
- **Git** 
- **Make** (optional, for using Makefile commands)

**Verify your setup:**
```bash
python --version  # Should show 3.10 or higher
```

## 🔧 Configuration

### Holdings Analysis Configuration

Edit the `holdings` section in `config/config.yaml`:

```yaml
analyses:
  holdings:
    enabled: true
    data_requirements:
      scraping_strategy: categories
      scraper_type: api
      categories:
        largeCap:
          - https://coin.zerodha.com/mf/fund/INF204K01XI3/nippon-india-large-cap-fund-direct-growth
          - https://coin.zerodha.com/mf/fund/INF179K01YV8/hdfc-large-cap-fund-direct-growth
        midCap:
          - https://coin.zerodha.com/mf/fund/INF179K01XQ0/hdfc-mid-cap-fund-direct-growth
        myCustomCategory:  # Create any category name
          - https://coin.zerodha.com/mf/fund/YOUR_FUND_ID/your-fund-name
    params:
      max_holdings: 50
      max_companies_in_results: 100
```

**How to find fund URLs:**
1. Go to [Zerodha Coin](https://coin.zerodha.com/mf)
2. Search and navigate to your fund
3. Copy the URL from browser address bar

### Portfolio Analysis Configuration  

Edit the `portfolio` section in `config/config.yaml`:

```yaml
analyses:
  portfolio:
    enabled: true
    data_requirements:
      scraping_strategy: targeted_funds
      scraper_type: api
      funds:
        - units: 1000  # Your units in this fund
          url: https://coin.zerodha.com/mf/fund/INF204K01XI3/nippon-india-large-cap-fund-direct-growth
        - units: 500
          url: https://coin.zerodha.com/mf/fund/INF179K01YV8/hdfc-large-cap-fund-direct-growth
    params:
      max_holdings: 50
      chart_top_n: 20
```

## 🎯 Running Analysis

```bash
# Holdings analysis
mfa-analyze holdings

# Portfolio analysis  
mfa-analyze portfolio

# View results in dashboard
make dashboard
```

## 🔧 Makefile Commands

For additional commands, check the Makefile:
```bash
make help    # See all available commands
```

## 🚨 Troubleshooting

**"python: command not found"**
```bash
python3 --version  # Try python3 instead
```

**"make: command not found"**
```bash
# Use Python directly
python -m pip install -e ".[dev]"
python -m mfa.cli.analyze holdings
```

## ✅ Verification

After setup, verify everything works:
```bash
python -c "import mfa; print('✅ MFA installed successfully')"
mfa-analyze --help
```
