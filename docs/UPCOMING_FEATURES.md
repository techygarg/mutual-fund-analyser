# Upcoming Features

This document outlines the planned enhancements for the Mutual Fund Analyser framework. These features are designed to transform the tool from a static snapshot analyzer into a comprehensive time-series investment research platform.

## 🚀 **What's Coming Next**

We're constantly working to make fund analysis more powerful and actionable. Here's what you can expect in upcoming releases:

---

## 📈 **Historical Trend Analysis**

**Coming in:** Next Major Release

**What it does:**
Track how fund holdings evolve over time, giving you insights into fund manager behavior and market trends that static snapshots can't reveal.

### Key Features

**📊 Holding Evolution Tracking**
- See when stocks enter or exit fund portfolios
- Monitor how allocation percentages change over time
- Identify which holdings are gaining or losing favor among fund managers

**📈 Popularity Trends**
- Track which stocks are becoming more/less popular across all funds
- Spot emerging investment themes before they become mainstream
- Identify consensus shifts in the fund management community

**🆕 New Entry Detection**
- Automatically highlight recently added holdings across funds
- Track which funds are early adopters of new stocks
- Monitor fresh investment opportunities

### What You'll Get

**Enhanced Dashboard:**
- Time-series charts showing holding popularity over time
- Trend indicators (📈 increasing, 📉 decreasing, ➡️ stable)
- "Trending Now" section highlighting hot/cold stocks

**New Analysis Files:**
```
outputs/trends/
├── largeCap_trends.json     # Historical data for large cap funds
├── midCap_trends.json       # Historical data for mid cap funds
└── smallCap_trends.json     # Historical data for small cap funds
```

**Sample Insights:**
- "HDFC Bank gained popularity: +2 funds in last week"
- "Tech sector allocation increased by 15% across midCap funds"
- "Emerging trend: 4 funds added renewable energy stocks"

### Use Cases

✅ **Spot Investment Themes Early**
- Identify sectors gaining institutional attention
- Follow fund manager consensus before retail investors catch on

✅ **Time Your Investments**
- See if funds are accumulating or disposing of specific stocks
- Make entry/exit decisions based on institutional activity

✅ **Track Fund Manager Behavior**
- Understand which fund managers are trend-setters vs followers
- Identify funds with consistent vs volatile holding patterns

---

## 🔄 **Date-to-Date Comparison Engine**

**Coming in:** Next Major Release

**What it does:**
Compare fund holdings between any two dates to see exactly what changed, enabling you to understand market dynamics and fund manager decisions.

### Key Features

**📊 Side-by-Side Analysis**
- Visual comparison of holdings between two dates
- Clear highlighting of additions, removals, and weight changes
- Summary statistics of overall portfolio shifts

**🔍 Change Detection**
- **New Holdings**: Stocks that entered fund portfolios
- **Removed Holdings**: Stocks that fund managers sold off
- **Weight Changes**: How allocation percentages shifted
- **Fund Switches**: Which funds made the biggest changes

**🏆 Movement Rankings**
- Biggest gainers/losers in popularity
- Most volatile holdings (frequent weight changes)
- Consensus builders (stocks gaining broad adoption)

### What You'll Get

**New Commands:**
```bash
# Compare specific dates
make compare FROM=20250820 TO=20250827 CATEGORY=midCap

```

**Enhanced Dashboard:**
- "Compare Dates" tab with intuitive date pickers
- Green/red diff views for easy change spotting
- Interactive charts showing movement patterns
- "What Changed?" summary widgets

**New Analysis Output:**
```
outputs/comparisons/
├── 20250820_vs_20250827_midCap.json
└── weekly_changes_summary.json
```

### Sample Insights

**Holdings Changes:**
- "📈 Added: Zomato (3 funds), Nykaa (2 funds)"
- "📉 Removed: Yes Bank (2 funds), Vodafone Idea (1 fund)"
- "⚖️ Weight Changes: HDFC Bank +1.2%, Infosys -0.8%"

**Fund Activity:**
- "Most Active: HDFC Mid Cap Fund (5 changes)"
- "Biggest Shift: SBI Midcap Fund (+3.2% in Banking sector)"
- "New Consensus: 4 funds added renewable energy stocks"

### Use Cases

✅ **React to Market Changes**
- Understand what fund managers are buying/selling after market events
- Spot shifts in sector preferences quickly

✅ **Monitor Your Holdings**
- See if funds you own are making significant changes
- Understand if fund strategy is shifting

✅ **Research Investment Ideas**
- Find stocks gaining institutional interest
- Identify potential opportunities before they become obvious

✅ **Risk Management**
- Spot when funds are reducing exposure to specific stocks/sectors
- Get early warning signals of potential problems

---