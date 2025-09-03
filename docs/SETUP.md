# Setup Guide

This guide covers detailed installation and configuration of the Mutual Fund Analyzer.

## 🐍 Python Installation

### Check Current Python Version
```bash
python --version
python3 --version
```

**Required:** Python 3.10 or higher

### Install Python (if needed)

**macOS (using Homebrew):**
```bash
brew install python@3.10
# Add to PATH in ~/.zshrc or ~/.bash_profile:
# export PATH="/usr/local/opt/python@3.10/bin:$PATH"
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-pip
```

**Windows:**
- Download from [python.org](https://www.python.org/downloads/)
- Choose Python 3.10.x installer
- Check "Add Python to PATH" during installation

## 📥 Installation

### 1. Clone Repository
```bash
git clone https://github.com/techygarg/mutual-fund-analyser.git
cd mutual-fund-analyser
```

### 2. Setup Environment
```bash
# Create virtual environment and install dependencies
make init

# Or manually:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Install Playwright
```bash
# Install browser automation
python -m playwright install

# Install specific browsers (if needed)
python -m playwright install chromium
```

### 4. Verify Installation
```bash
# Check everything is working
python -c "import mfa; print('✅ MFA installed successfully')"

# Run basic tests
make test-unit
```

## ⚙️ Configuration

### Basic Configuration

The tool works out-of-the-box with default settings. For customization, edit `config/config.yaml`:

```yaml
# Basic settings
paths:
  output_dir: outputs/extracted_json
  analysis_dir: outputs/analysis

scraping:
  headless: true
  timeout_seconds: 30
  delay_between_requests: 1.0

analysis:
  max_companies_in_results: 100
  max_sample_funds_per_company: 5
```

### Adding Custom Funds

Edit the `funds` section in `config/config.yaml`:

```yaml
funds:
  largeCap:
    - https://coin.zerodha.com/mf/fund/INF204K01XI3/nippon-india-large-cap-fund-direct-growth
    - https://coin.zerodha.com/mf/fund/INF179K01YV8/hdfc-large-cap-fund-direct-growth

  midCap:
    - https://coin.zerodha.com/mf/fund/INF179K01XQ0/hdfc-mid-cap-fund-direct-growth
    - https://coin.zerodha.com/mf/fund/INF174K01LT0/kotak-midcap-fund-direct-growth

  smallCap:
    - https://coin.zerodha.com/mf/fund/YOUR_FUND_ID/your-small-cap-fund

  # Add your custom categories
  myFunds:
    - https://coin.zerodha.com/mf/fund/FUND_ID_1/custom-fund-1
    - https://coin.zerodha.com/mf/fund/FUND_ID_2/custom-fund-2
```

### How to Find Fund URLs

1. Go to [Zerodha Coin](https://coin.zerodha.com/mf)
2. Navigate to a mutual fund
3. Copy the URL from your browser's address bar
4. Add it to your `config/config.yaml`

**Example URL format:**
```
https://coin.zerodha.com/mf/fund/INF179K01XQ0/hdfc-mid-cap-fund-direct-growth
```

## 🔧 Advanced Configuration

### Scraping Options

```yaml
scraping:
  headless: false          # Set to false to see browser window (useful for debugging)
  timeout_seconds: 60      # Increase if pages load slowly
  delay_between_requests: 2.0  # Increase for slower/safer scraping
  save_extracted_json: true   # Keep intermediate JSON files
```

### Analysis Options

```yaml
analysis:
  max_companies_in_results: 50         # Limit results for performance
  max_sample_funds_per_company: 3      # Fewer examples per company
  exclude_from_analysis:               # Holdings to ignore
    - "TREPS"
    - "CASH"
    - "T-BILLS"
    - "LIQUID FUNDS"
```

### Path Configuration

```yaml
paths:
  output_dir: outputs/extracted_json    # Where raw data is stored
  analysis_dir: outputs/analysis        # Where analysis results go
```

## 🧪 Testing Setup

### Run All Tests
```bash
make test
```

### Run Specific Test Types
```bash
make test-unit        # Unit tests only
make test-integration # Integration tests only
```

### Test Configuration
Integration tests use `tests/integration/test_config.yaml`. This file contains:
- Test fund URLs (smaller dataset for faster testing)
- Modified timeouts for CI/CD environments
- Test-specific output directories

## 🚨 Troubleshooting Setup Issues

### Common Installation Problems

**"python: command not found"**
```bash
# Check if python3 exists
python3 --version

# Create alias if needed
echo "alias python=python3" >> ~/.bashrc
source ~/.bashrc
```

**"pip: command not found"**
```bash
# Install pip
python -m ensurepip --upgrade
# or
python3 -m ensurepip --upgrade
```

**"make: command not found"**
```bash
# macOS
brew install make

# Ubuntu/Debian
sudo apt install make

# Use Python directly instead
python -m pytest tests/
python -c "import mfa.cli.analyze; mfa.cli.analyze.main()"
```

### Playwright Issues

**"Browser installation failed"**
```bash
# Try manual installation
python -m playwright install chromium --force

# Or install system dependencies
# Ubuntu/Debian:
sudo apt install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# macOS:
brew install --cask google-chrome  # For fallback
```

### Permission Issues

**"Permission denied" when writing files**
```bash
# Fix output directory permissions
chmod -R 755 outputs/
mkdir -p outputs/extracted_json outputs/analysis
```

### Virtual Environment Issues

**"venv: command not found"**
```bash
# Use python module instead
python -m venv venv
```

**"Cannot activate virtual environment"**
```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

## 🔄 Updating

### Update the Tool
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -e ".[dev]"

# Update playwright if needed
python -m playwright install
```

### Update Configuration
When updating, check if `config/config.yaml` has new options. Compare with the latest version in the repository.

## ✅ Verification

After setup, verify everything works:

```bash
# 1. Check Python environment
python --version
which python

# 2. Check MFA installation
python -c "import mfa; print('MFA imported successfully')"

# 3. Check configuration
python -c "from mfa.config.settings import create_config_provider; cp = create_config_provider(); print('Config loaded')"

# 4. Test basic functionality
make analyze CATEGORY=midCap
make dashboard
```

**Expected output:**
- Python 3.10+ version shown
- MFA imports without errors
- Configuration loads successfully
- Analysis completes without errors
- Dashboard starts on http://localhost:8787
