# Portfolio Analysis

## 🎯 What is Portfolio Analysis?

Portfolio analysis tracks your personal mutual fund investments in real-time. Provide your fund URLs and units, and get:

- **Current portfolio value** - Based on today's NAV prices
- **Stock-level breakdown** - See exactly which stocks your money is invested in
- **Allocation insights** - Understand how your money is distributed across companies

## 💡 Why Use Portfolio Analysis?

**Real-world scenario:** You have invested in 5 different mutual funds with different amounts. Portfolio analysis tells you:
- Total current value of your investments
- Which individual stocks you're actually invested in (through the funds)
- How much of your money is in each company
- Whether you're over-exposed to certain stocks across funds

This is especially valuable because **you might unknowingly have high concentration** in certain stocks across different funds.

## 🔧 Configuration

Edit the `portfolio` section in `config/config.yaml`:

```yaml
analyses:
  portfolio:
    enabled: true
    data_requirements:
      scraping_strategy: targeted_funds   # Focus on specific funds you own
      scraper_type: api                  # Use API for current NAV data
      funds:
        - units: 1000                    # Your units in this fund
          url: https://coin.zerodha.com/mf/fund/INF204K01XI3/nippon-india-large-cap-fund-direct-growth
        - units: 500                     # Different units for each fund
          url: https://coin.zerodha.com/mf/fund/INF179K01YV8/hdfc-large-cap-fund-direct-growth
        - units: 750
          url: https://coin.zerodha.com/mf/fund/INF204K01K15/nippon-india-small-cap-fund-direct-growth
    params:
      max_holdings: 50                  # Analyze top 50 holdings per fund
      chart_top_n: 20                   # Show top 20 companies in charts
```

### Configuration Steps:

1. **Find your fund URLs** - Go to Zerodha Coin, navigate to your fund, copy URL
2. **Add your units** - Check your investment account for exact units owned
3. **Update the funds list** - Add all funds you want to track

## 📊 What You Get

**Portfolio Analysis Output:**
- **Total Portfolio Value** - Current worth based on today's NAV
- **Fund-wise Breakdown** - Value contribution from each fund
- **Stock-level Analysis** - Which companies you're invested in and how much
- **Concentration Report** - Identify if you're over-invested in certain stocks
- **Interactive Dashboard** - Visual representation of your portfolio

**Example insights:**
- "Your portfolio is worth ₹2,45,000 today"
- "25% of your money is in Reliance Industries (across 3 funds)"
- "Your largest holding is HDFC Bank at ₹35,000"
- "You have exposure to 45 different companies"

## 🚀 Running Portfolio Analysis

```bash
# Run portfolio analysis
mfa-analyze portfolio

# View results in dashboard
make dashboard
# Open http://localhost:8787
```

## 💡 Use Cases

1. **Portfolio Tracking** - Monitor your investment value in real-time
2. **Risk Management** - Identify concentration risks across funds
3. **Rebalancing Decisions** - Understand current allocation before making changes
4. **Tax Planning** - See which funds contribute most to your portfolio value
5. **Investment Review** - Regular analysis of your fund performance and allocation

## 🔍 Understanding Your Results

The dashboard will show:
- **Portfolio Summary** - Total value and fund breakdown
- **Top Holdings Chart** - Your biggest stock exposures
- **Detailed Tables** - Complete breakdown by company and fund
- **Allocation Pie Charts** - Visual representation of your money distribution