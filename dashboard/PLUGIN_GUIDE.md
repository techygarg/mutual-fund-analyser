# MFA Dashboard Plugin Architecture Guide

## 🎯 Overview

The MFA Dashboard uses a plugin-based architecture that allows easy addition of new analysis types without disrupting existing functionality. This guide explains how to create new analysis plugins.

## 🏗️ Architecture

### Plugin Framework Components

1. **AnalysisPlugin (Abstract Base Class)**: Defines the interface for all analysis plugins
2. **Plugin Registry**: Auto-discovers and manages available plugins
3. **Dynamic UI**: Frontend automatically adapts to available analysis types
4. **Extensible API**: Backend endpoints work with any registered plugin

### Current Plugins

- **HoldingsPlugin**: Analyzes mutual fund holdings across categories
- **PortfolioPlugin**: Analyzes personal portfolio composition

## 🔧 Creating a New Analysis Plugin

### Step 1: Create Plugin Class

Create a new plugin class that inherits from `AnalysisPlugin`:

```python
from dashboard.server import AnalysisPlugin, ANALYSIS_PLUGINS

class MyNewPlugin(AnalysisPlugin):
    @property
    def analysis_type(self) -> str:
        return "my_analysis"  # Unique identifier
    
    @property
    def display_name(self) -> str:
        return "My Analysis"  # Human-readable name
    
    @property
    def icon(self) -> str:
        return "🔬"  # Icon/emoji for UI
    
    @property
    def requires_category(self) -> bool:
        return True  # True if analysis needs category selection
    
    def get_categories(self, date: str) -> List[str]:
        # Return available categories for this analysis
        # For holdings: ["largecap", "midcap", etc.]
        # For portfolio: [] (no categories)
        pass
    
    def get_analysis_data(self, date: str, category: Optional[str] = None) -> Dict[str, Any]:
        # Return main analysis data from JSON files
        # Path typically: outputs/analysis/{date}/{category}.json
        pass
    
    def get_funds_data(self, date: str, category: Optional[str] = None) -> Dict[str, Any]:
        # Return funds composition data
        # Path typically: outputs/extracted_json/{date}/{analysis_type}/
        pass
    
    def transform_for_ui(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Transform raw analysis data for UI consumption
        # Add chart data, format values, etc.
        pass

# Register the plugin
ANALYSIS_PLUGINS["my_analysis"] = MyNewPlugin()
```

### Step 2: Add Frontend UI Components

Add analysis-specific UI panels in `static/index.html`:

```html
<!-- Add analysis panel -->
<div id="myAnalysisPanel" class="analysis-panel" style="display:none;">
  <div class="charts">
    <div class="card">
      <h2>My Analysis Chart</h2>
      <canvas id="myAnalysisChart" height="220"></canvas>
    </div>
  </div>
  
  <div class="grid">
    <div class="card">
      <h2>My Analysis Table</h2>
      <table id="myAnalysisTable">
        <thead>
          <tr>
            <th>Column 1</th>
            <th>Column 2</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</div>

<!-- Add funds panel if needed -->
<div id="myAnalysisFundsPanel" class="funds-panel" style="display:none;">
  <div class="card">
    <h2>My Analysis Funds</h2>
    <div id="myAnalysisFundsGrid"></div>
  </div>
</div>
```

### Step 3: Add JavaScript Rendering Logic

Add rendering functions in the JavaScript section:

```javascript
// Add to updateAnalysisDisplay() function
if (currentAnalysisType === 'my_analysis') {
  renderMyAnalysis();
}

// Add to updateFundsDisplay() function  
if (currentAnalysisType === 'my_analysis') {
  renderMyAnalysisFunds();
}

// Add rendering functions
function renderMyAnalysis(){
  const data = analysisData.my_custom_data || [];
  
  // Update UI elements
  const chart = document.getElementById('myAnalysisChart');
  const table = document.querySelector('#myAnalysisTable tbody');
  
  // Render chart using Chart.js
  if(charts.my_analysis?.chart) charts.my_analysis.chart.destroy();
  charts.my_analysis = charts.my_analysis || {};
  charts.my_analysis.chart = new Chart(chart, {
    type: 'bar',
    data: {
      labels: data.map(d => d.name),
      datasets: [{
        data: data.map(d => d.value),
        backgroundColor: PALETTE
      }]
    }
  });
  
  // Render table
  table.innerHTML = '';
  data.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${item.name}</td><td>${item.value}</td>`;
    table.appendChild(tr);
  });
}

function renderMyAnalysisFunds(){
  // Similar pattern for funds view
}
```

### Step 4: Register Global Charts Object

Add your analysis to the global charts object:

```javascript
let charts = { 
  holdings: {}, 
  portfolio: {}, 
  my_analysis: {}  // Add this
};
```

## 📁 File Structure Requirements

### Analysis Output Files

Your analysis should output files in this structure:

```
outputs/
├── analysis/
│   └── {date}/
│       └── my_analysis.json     # Main analysis results
└── extracted_json/
    └── {date}/
        └── my_analysis/         # Raw scraped data (if needed)
            ├── file1.json
            └── file2.json
```

### Data Format Standards

#### Analysis JSON Structure
```json
{
  "type": "my_analysis",
  "summary": {
    "total_items": 100,
    "custom_metric": 456
  },
  "main_data": [
    {"name": "Item 1", "value": 123},
    {"name": "Item 2", "value": 456}
  ],
  "charts": {
    "distribution": [
      {"name": "Category A", "value": 60, "percentage": 60.0},
      {"name": "Category B", "value": 40, "percentage": 40.0}
    ]
  }
}
```

#### Funds Data Structure (if applicable)
```json
{
  "funds": [
    {
      "fund_name": "Example Fund",
      "custom_metric": "some_value",
      "items": [
        {"name": "Item 1", "metric": 123},
        {"name": "Item 2", "metric": 456}
      ]
    }
  ]
}
```

## 🎨 UI Guidelines

### Design Consistency

1. **Colors**: Use the predefined `PALETTE` array for charts
2. **Cards**: Wrap content in `.card` class for consistent styling
3. **Tables**: Follow existing table structure with sortable headers
4. **Charts**: Use Chart.js with consistent styling options

### Responsive Design

- Use grid layouts that adapt to screen size
- Ensure charts are readable on mobile devices
- Test with different data volumes

### Example Chart Options
```javascript
const chartOptions = {
  indexAxis: 'y',  // Horizontal bars
  plugins: { legend: { display: false } },
  scales: { 
    x: { grid: { color: '#223154' } }, 
    y: { grid: { display: false } }
  }
};
```

## 🔍 Testing Your Plugin

### 1. Backend Testing
```bash
# Test plugin discovery
curl "http://localhost:8787/api/analysis-types?date=20250908"

# Test data retrieval
curl "http://localhost:8787/api/data?date=20250908&analysis_type=my_analysis"
```

### 2. Frontend Testing
1. Run the dashboard: `cd dashboard && python server.py`
2. Open http://localhost:8787
3. Select your analysis type from dropdown
4. Verify UI renders correctly
5. Test tab switching between Analysis/Funds views

### 3. Error Handling
- Ensure graceful handling of missing data files
- Test with empty datasets
- Verify category logic (if applicable)

## 🚀 Deployment Checklist

- [ ] Plugin class implemented with all required methods
- [ ] Plugin registered in `ANALYSIS_PLUGINS` dictionary
- [ ] UI panels added to HTML
- [ ] JavaScript rendering functions implemented
- [ ] Charts object updated
- [ ] Data files generated in correct structure
- [ ] Backend API tested
- [ ] Frontend UI tested
- [ ] Error cases handled gracefully

## 🔮 Future Extensions

### Dynamic Plugin Loading
Future versions could support:
- Plugin discovery from separate files
- Hot-reloading of plugins
- Plugin configuration files
- Plugin-specific assets/styles

### Advanced Features
- Cross-analysis comparisons
- Real-time data updates
- Export functionality per analysis
- Custom visualization types

## 📚 Examples

See existing implementations:
- `HoldingsPlugin` in `server.py` (lines 79-168)
- `PortfolioPlugin` in `server.py` (lines 171-279)
- Frontend panels in `index.html` (lines 91-198)
- JavaScript rendering in `index.html` (lines 354-599)

---

This plugin architecture ensures that adding new analysis types is:
- **Non-disruptive**: Existing analyses continue working unchanged
- **Consistent**: All analyses follow the same patterns
- **Scalable**: Easy to add unlimited new analysis types
- **Maintainable**: Clear separation of concerns and standardized interfaces
