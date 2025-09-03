# Troubleshooting Guide

Common issues and solutions for the Mutual Fund Analyzer.

## 🚨 Quick Diagnosis

### Check System Status
```bash
# 1. Python version
python --version

# 2. Virtual environment
which python  # Should show venv path

# 3. MFA installation
python -c "import mfa; print('✅ MFA installed')"

# 4. Configuration
python -c "from mfa.config.settings import create_config_provider; cp = create_config_provider(); print('✅ Config loaded')"

# 5. Playwright browsers
python -m playwright install --dry-run
```

## 🐍 Python & Environment Issues

### "python: command not found"
```bash
# Check if python3 exists
python3 --version

# Create alias (Linux/macOS)
echo "alias python=python3" >> ~/.bashrc
source ~/.bashrc

# Or use python3 directly
python3 --version
```

### "ModuleNotFoundError: No module named 'mfa'"
```bash
# Install in development mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"

# Check installation
python -c "import mfa; print('Installed successfully')"
```

### Virtual Environment Issues

**Cannot create venv:**
```bash
# Install venv module
python -m pip install virtualenv

# Create venv
python -m venv venv
```

**Cannot activate venv (Windows):**
```bash
# Use correct path
venv\Scripts\activate
```

**Cannot activate venv (Linux/macOS):**
```bash
# Check permissions
ls -la venv/bin/activate

# Fix permissions if needed
chmod +x venv/bin/activate
source venv/bin/activate
```

## 🌐 Playwright & Browser Issues

### "Browser installation failed"
```bash
# Try manual installation
python -m playwright install chromium --force

# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# Install system dependencies (macOS)
brew install --cask google-chrome

# Check installation
python -m playwright install --dry-run
```

### "Page load timeout"
```bash
# Increase timeout in config/config.yaml
scraping:
  timeout_seconds: 60  # Increase from 30

# Or run with debugging
# Edit config to set headless: false
make scrape CATEGORY=midCap
```

### Browser crashes or hangs
```bash
# Enable debug mode
# Edit config/config.yaml:
scraping:
  headless: false  # Show browser window

# Increase delays
scraping:
  delay_between_requests: 2.0  # Increase from 1.0
```

## 📊 Scraping Issues

### "No data scraped" or empty results
```bash
# 1. Check if fund URLs are valid
curl -I "https://coin.zerodha.com/mf/fund/INF179K01XQ0/hdfc-mid-cap-fund-direct-growth"

# 2. Enable debug mode to see browser
# Edit config/config.yaml:
scraping:
  headless: false

# 3. Check logs
tail -f outputs/mfa.log
```

### Rate limiting or blocks
```bash
# Increase delays between requests
# Edit config/config.yaml:
scraping:
  delay_between_requests: 3.0  # Increase delay

# Or add random delays (future feature)
```

### "Address already in use" for dashboard
```bash
# Kill existing processes
pkill -f uvicorn
pkill -f "python.*dashboard"

# Or use different port
# Edit dashboard code to use port 8788
```

## 📈 Analysis Issues

### "No analysis data found"
```bash
# 1. Check if scraping completed
ls -la outputs/extracted_json/

# 2. Check date directories
ls outputs/extracted_json/  # Should show YYYYMMDD folders

# 3. Check if files exist
find outputs/extracted_json/ -name "*.json" | head -5

# 4. Run analysis for today's date
make analyze CATEGORY=midCap
```

### Analysis runs but shows no results
```bash
# Check raw data quality
head -20 outputs/extracted_json/20250827/midCap/*.json

# Check for excluded holdings
# Edit config/config.yaml to see exclude_from_analysis
```

### Wrong date in analysis
```bash
# Check system date
date

# Force specific date
make analyze DATE=20250827 CATEGORY=midCap

# Check file timestamps
ls -la outputs/analysis/
```

## ⚙️ Configuration Issues

### "Configuration file not found"
```bash
# Check if config exists
ls -la config/config.yaml

# Check current directory
pwd  # Should be mutual-fund-analyser/

# Create default config
cp config/config.yaml.example config/config.yaml
```

### Configuration changes not taking effect
```bash
# 1. Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# 2. Restart any running processes
pkill -f uvicorn

# 3. Check if config is being loaded
python -c "from mfa.config.settings import create_config_provider; cp = create_config_provider(); print(cp.get_config().scraping.headless)"
```

### Custom fund URLs not working
```bash
# 1. Validate URL format
curl -I "YOUR_FUND_URL"

# 2. Check if it's a Zerodha Coin URL
# Should start with: https://coin.zerodha.com/mf/fund/

# 3. Test with known working URL first
# Add a known working URL to test
```

## 📁 File System Issues

### Permission denied when writing files
```bash
# Fix permissions on outputs directory
chmod -R 755 outputs/

# Or recreate directories
rm -rf outputs/
mkdir -p outputs/extracted_json outputs/analysis
```

### Disk space issues
```bash
# Check disk usage
df -h

# Check project size
du -sh outputs/

# Clean old data
find outputs/ -name "*.json" -mtime +30 -delete  # Delete files older than 30 days
```

### File corruption or incomplete files
```bash
# Check file sizes
ls -lh outputs/extracted_json/20250827/midCap/

# Validate JSON files
for file in outputs/extracted_json/20250827/midCap/*.json; do
    python -c "import json; json.load(open('$file'))" && echo "$file: ✅" || echo "$file: ❌"
done
```

## 🌐 Dashboard Issues

### Dashboard not loading
```bash
# 1. Check if server is running
ps aux | grep uvicorn

# 2. Start dashboard
make dashboard

# 3. Check port availability
netstat -an | grep 8787

# 4. Try different port
# Edit server.py to use port 8788
```

### Charts not displaying data
```bash
# 1. Check if analysis files exist
ls -la outputs/analysis/

# 2. Validate JSON format
python -c "import json; json.load(open('outputs/analysis/20250827/midCap.json'))"

# 3. Check browser console for errors
# Open DevTools (F12) and look for JavaScript errors
```

### Dashboard shows wrong data
```bash
# 1. Clear browser cache
# Ctrl+Shift+R (or Cmd+Shift+R on Mac)

# 2. Check if dashboard is reading latest files
tail -f outputs/mfa.log  # Look for file access logs

# 3. Restart dashboard
pkill -f uvicorn
make dashboard
```

## 🧪 Testing Issues

### Unit tests failing
```bash
# Run specific test
make test-unit TEST=tests/unit/test_config_system.py::TestConfigProvider::test_config_loading

# Check test logs
make test-unit 2>&1 | grep -A5 -B5 "FAILED"
```

### Integration tests failing
```bash
# Run integration tests with verbose output
make test-integration VERBOSE=1

# Check test workspace
ls -la tests/integration/test_workspace/

# Check test configuration
cat tests/integration/test_config.yaml
```

### Test data issues
```bash
# Check test fund URLs are accessible
curl -I "https://coin.zerodha.com/mf/fund/INF179K01XQ0/hdfc-mid-cap-fund-direct-growth"

# Update test URLs if needed
# Edit tests/integration/test_config.yaml
```

## 🔧 Development Issues

### Code changes not taking effect
```bash
# Reinstall in development mode
pip install -e .

# Or restart Python interpreter
# Kill any running Python processes
pkill -f python
```

### Import errors during development
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Add current directory to path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Linting errors
```bash
# Run linter
make lint

# Fix specific issues
ruff check src/mfa/
ruff format src/mfa/
```

## 📊 Performance Issues

### Scraping too slow
```bash
# 1. Check internet connection
speedtest-cli

# 2. Reduce timeout
# Edit config/config.yaml:
scraping:
  timeout_seconds: 15

# 3. Use headless mode
scraping:
  headless: true
```

### Analysis too slow
```bash
# Reduce analysis scope
# Edit config/config.yaml:
analysis:
  max_companies_in_results: 25
  max_sample_funds_per_company: 2
```

### Memory usage high
```bash
# Monitor memory usage
top -p $(pgrep -f python)

# Check for memory leaks
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# Reduce batch sizes (future feature)
```

### Disk I/O slow
```bash
# Check disk performance
hdparm -Tt /dev/sda  # Linux
diskutil info disk0  # macOS

# Use faster storage if available
# Move outputs/ to SSD or faster disk
```

## 🚨 Critical Errors

### "Database locked" or file access errors
```bash
# Check file locks
lsof outputs/

# Kill processes holding locks
pkill -f python

# Clean up temporary files
find . -name "*.tmp" -delete
```

### "Out of memory" errors
```bash
# Increase system memory or
# Reduce analysis scope
analysis:
  max_companies_in_results: 10

# Process in smaller batches
```

### Network connectivity issues
```bash
# Test connectivity
ping -c 3 coin.zerodha.com

# Check DNS resolution
nslookup coin.zerodha.com

# Use different DNS
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
```

## 📞 Getting Help

### Debug Information to Provide
```bash
# System info
uname -a
python --version
pip list | grep -E "(mfa|playwright|pydantic)"

# Configuration (sanitize sensitive data)
head -20 config/config.yaml

# Recent logs
tail -50 outputs/mfa.log

# File structure
find outputs/ -type f | head -20
```

### Common Debug Commands
```bash
# Full system check
python -c "
import sys
print('Python:', sys.version)
import mfa
print('MFA: OK')
from mfa.config.settings import create_config_provider
cp = create_config_provider()
print('Config: OK')
import playwright
print('Playwright: OK')
"

# Quick health check
make test-unit TEST=tests/unit/test_config_system.py -v
```

### When to Report Issues
- **Bug reports**: Include full error traceback and system info
- **Performance issues**: Include timing data and system specs
- **Feature requests**: Describe use case and expected behavior
- **Documentation issues**: Specify what's unclear or missing

### Support Channels
1. **GitHub Issues**: For bugs and feature requests
2. **Documentation**: Check docs/ for detailed guides
3. **Logs**: Enable debug logging for troubleshooting
