# Holdings Analysis

## 🎯 What is Holdings Analysis?

Holdings analysis helps you understand what stocks are held across different mutual fund categories. This is valuable when you want to:

- **Avoid over-concentration** - See if multiple funds hold the same stocks
- **Find popular stocks** - Identify which companies are favored across fund managers
- **Make informed decisions** - Understand fund composition before investing

## 💡 Why Use Holdings Analysis?

**Example scenario:** You're considering investing in multiple mid-cap funds. Holdings analysis will show you:
- Which stocks appear in most mid-cap funds (high conviction picks)
- How much overlap exists between different funds
- Whether diversifying across multiple funds actually gives you diversification

## 🔧 Configuration

Edit the `holdings` section in `config/config.yaml`:

```yaml
analyses:
  holdings:
    enabled: true
    data_requirements:
      scraping_strategy: categories    # Organize funds by categories
      scraper_type: api               # Use API for faster scraping
      categories:
        largeCap:                     # Category name (customizable)
          - https://coin.zerodha.com/mf/fund/INF204K01XI3/nippon-india-large-cap-fund-direct-growth
          - https://coin.zerodha.com/mf/fund/INF179K01YV8/hdfc-large-cap-fund-direct-growth
        midCap:
          - https://coin.zerodha.com/mf/fund/INF179K01XQ0/hdfc-mid-cap-fund-direct-growth
        smallCap:
          - https://coin.zerodha.com/mf/fund/INF204K01K15/nippon-india-small-cap-fund-direct-growth
        myCustomFunds:                # Create any category you want
          - https://coin.zerodha.com/mf/fund/YOUR_FUND_ID/your-fund
    params:
      max_holdings: 50                    # Top 50 holdings per fund
      max_companies_in_results: 100       # Show top 100 companies in results
      max_sample_funds_per_company: 10    # Show up to 10 example funds per company
      exclude_from_analysis:              # Ignore these holdings
        - "TREPS"        # Treasury Repo
        - "CASH"         # Cash holdings
```

### Key Configuration Points:

- **Categories are fully customizable** - Create `largeCap`, `midCap`, `myFavorites`, or any name you want
- **Add any number of funds** - Each category can have multiple fund URLs
- **Flexible parameters** - Adjust `max_holdings` and result limits based on your needs

## 📊 What You Get

**Analysis Output:**
- **Company Rankings** - Stocks ranked by how many funds hold them
- **Fund Overlap Analysis** - See which funds have similar holdings  
- **Category Insights** - Understand patterns within each fund category
- **Interactive Dashboard** - Visual charts and detailed tables

**Example insights:**
- "Reliance Industries appears in 8 out of 10 large-cap funds"
- "HDFC Bank is the most popular holding across mid-cap funds"
- "Your selected funds have 40% overlap in top holdings"

## 🚀 Running Holdings Analysis

```bash
# Run holdings analysis
mfa-analyze holdings

# View results
make dashboard
# Open http://localhost:8787
```

## 💡 Use Cases

1. **Fund Selection** - Compare funds before investing to avoid overlap
2. **Portfolio Review** - Understand your current fund holdings composition  
3. **Market Research** - See which stocks fund managers are betting on
4. **Diversification Check** - Ensure your funds provide real diversification
