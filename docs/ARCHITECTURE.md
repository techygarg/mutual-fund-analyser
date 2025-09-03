# Architecture Guide

**For developers contributing to the Mutual Fund Analyzer.**

## 🏛️ Core Principles

- **Clean Architecture**: Business logic isolated from infrastructure
- **Dependency Injection**: All components receive dependencies via constructor
- **Factory Pattern**: Extensible component creation
- **Interface Segregation**: Clear contracts between components
- **Configuration-Driven**: Behavior controlled by YAML, not code

## 📁 Project Structure

```
src/mfa/
├── cli/              # Command-line interfaces
├── analysis/         # Core analysis logic
│   ├── interfaces.py # Abstract base classes
│   ├── factories.py  # Component factories
│   ├── analyzers/    # Analysis implementations
│   └── scraping/     # Scraping coordinators
├── orchestration/    # Workflow orchestration
├── scraping/         # Browser automation
├── storage/          # File I/O operations
├── config/           # Configuration management
├── core/             # Shared utilities
└── web/              # Dashboard interface
```

## 🔧 Key Components

### Analysis System
- **`IAnalyzer`**: Interface for all analysis implementations
- **`BaseAnalyzer`**: Common functionality for analyzers
- **`HoldingsAnalyzer`**: Main analysis implementation
- **`AnalyzerFactory`**: Creates analyzer instances

### Scraping System
- **`IScrapingCoordinator`**: Interface for scraping strategies
- **`CategoryScrapingCoordinator`**: Scrapes funds by category
- **`TargetedScrapingCoordinator`**: Scrapes specific fund lists
- **`ScrapingCoordinatorFactory`**: Creates coordinator instances

### Configuration
- **`ConfigProvider`**: Singleton configuration access
- **`MFAConfig`**: Pydantic configuration model
- **YAML-driven**: All behavior controlled by `config/config.yaml`

## 🚀 Development Workflow

### Adding New Analysis Types

1. **Create analyzer class** in `analysis/analyzers/`:
```python
@register_analyzer("portfolio-analysis")
class PortfolioAnalyzer(BaseAnalyzer):
    def __init__(self, config_provider: ConfigProvider):
        super().__init__(config_provider, "portfolio-analysis")
        # Your initialization

    def get_data_requirements(self) -> DataRequirement:
        # Define what data you need
        return DataRequirement(...)

    def analyze(self, data_source: dict, date: str) -> AnalysisResult:
        # Your analysis logic
        return AnalysisResult(...)
```

2. **Add configuration** in `config/config.yaml`:
```yaml
analyses:
  portfolio-analysis:
    enabled: true
    type: portfolio-analysis
    params:
      custom_param: value
```

### Adding New Scraping Strategies

1. **Create coordinator** in `analysis/scraping/`:
```python
@register_coordinator("custom-strategy")
class CustomScrapingCoordinator(BaseScrapingCoordinator):
    def scrape_for_requirement(self, requirement: DataRequirement) -> dict:
        # Your scraping logic
        return scraped_data
```

2. **Update configuration** to use new strategy:
```yaml
analyses:
  holdings:
    data_requirements:
      scraping_strategy: custom-strategy
```

### Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test end-to-end workflows
- **Mock Dependencies**: Use dependency injection for testability

### Code Quality Standards

- **Type Hints**: All functions and methods must have type annotations
- **Docstrings**: Comprehensive documentation for public APIs
- **Linting**: Must pass `make lint` before merging
- **Testing**: 90%+ code coverage for new features
