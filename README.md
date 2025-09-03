# Mutual Fund Analyzer

[![CI Pipeline](https://github.com/techygarg/mutual-fund-analyser/workflows/CI%20Pipeline/badge.svg)](https://github.com/techygarg/mutual-fund-analyser/actions)
[![codecov](https://codecov.io/gh/techygarg/mutual-fund-analyser/branch/main/graph/badge.svg)](https://codecov.io/gh/techygarg/mutual-fund-analyser)

**Analyze mutual fund holdings to find investment patterns and overlaps.**

- 📊 **Extract** fund data from Zerodha Coin
- 🔍 **Analyze** holdings across multiple funds
- 📈 **Discover** investment trends and overlaps
- 🌐 **Visualize** results in an interactive dashboard

## 🚀 Quick Start

Get analyzing mutual funds in 5 minutes:

```bash
# 1. Clone and setup
git clone https://github.com/techygarg/mutual-fund-analyser.git
cd mutual-fund-analyser
make init

# 2. Install browser automation
python -m playwright install

# 3. Run your first analysis
make analyze CATEGORY=midCap

# 4. View results
make dashboard
# Open http://localhost:8787
```

## 📋 Requirements

- **Python 3.10+**
- **Git** (to clone repository)
- **Make** (optional, for using Makefile commands)

**Check your setup:**
```bash
python --version  # Should show 3.10 or higher
```

## 📖 Usage

### Basic Commands

```bash
# Run complete analysis (scrape + analyze)
make analyze CATEGORY=midCap

# View results in browser
make dashboard

# Check available options
mfa-analyze --help
```

### Categories Available
- `largeCap` - Large capitalization funds
- `midCap` - Mid capitalization funds
- `smallCap` - Small capitalization funds

### What You Get

**📁 Data Files:**
```
outputs/extracted_json/20250827/midCap/
├── coin_INF179K01XQ0_hdfc-mid-cap-fund-direct-growth.json
└── ... (one JSON per fund)

outputs/analysis/20250827/
└── midCap.json  # Analysis results
```

**🌐 Dashboard:**
- Interactive charts showing stock overlaps
- Tables ranking companies by popularity
- Individual fund composition details

### Command Line Interface

```bash
# Basic usage (analysis_type is required)
mfa-analyze holdings                         # Analyze holdings specifically
mfa-analyze holdings --category midCap       # Analyze specific category
mfa-analyze holdings --date 20250827         # Analyze for specific date

# Informational commands (no analysis_type needed)
mfa-analyze --list                          # List available analyses
mfa-analyze --status                        # Show configuration status
mfa-analyze --help                          # Show all options
```

## ⚙️ Configuration

### Customize Fund Categories

Edit `config/config.yaml` to add your own funds:

```yaml
funds:
  largeCap:
    - https://coin.zerodha.com/mf/fund/INF204K01XI3/nippon-india-large-cap-fund-direct-growth
    - https://coin.zerodha.com/mf/fund/INF179K01YV8/hdfc-large-cap-fund-direct-growth
  midCap:
    - https://coin.zerodha.com/mf/fund/INF179K01XQ0/hdfc-mid-cap-fund-direct-growth
  customCategory:
    - https://coin.zerodha.com/mf/fund/YOUR_FUND_ID/your-custom-fund
```

### Scraping Settings

```yaml
scraping:
  headless: true          # Run browser in background
  timeout_seconds: 30     # Page load timeout
  delay_between_requests: 1.0  # Respectful scraping delay
```

## 📚 Documentation

- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[Usage Guide](docs/USAGE.md)** - Complete command reference and examples
- **[Architecture](docs/ARCHITECTURE.md)** - Technical architecture overview
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Built with ❤️ for mutual fund investors**