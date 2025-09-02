# MFA Design Principles & Architectural Guidelines

This document captures the core design principles and architectural decisions for the Mutual Fund Analyzer (MFA) project. These principles should guide all future development and refactoring efforts.

## 🏛️ Core Architectural Philosophy

### 1. Complete Migration, No Legacy Support
- **Principle**: When migrating to new patterns, completely remove old/legacy code
- **No**: Deprecated methods, backward compatibility layers, old ways of doing things  
- **Yes**: Clean, complete migrations with single, modern approaches
- **Example**: Removed all string-based config access in favor of typed Pydantic models

### 2. Type Safety First
- **Principle**: Use strong typing everywhere, avoid string-based access patterns
- **Configuration**: Pydantic models instead of `config.get("key.path")`
- **Interfaces**: Abstract base classes with clear contracts
- **Data Models**: Structured classes for all data exchange
- **Benefits**: IDE support, refactoring safety, compile-time error detection

### 3. Analysis-Driven Architecture
- **Principle**: Scraping and data collection are dictated by analysis requirements
- **Pattern**: Analysis defines `DataRequirement` → Coordinator fulfills → Scraper executes
- **Flexibility**: Different analyses can request different data (categories vs targeted funds)
- **Extensibility**: New analysis types can define their own data needs

### 4. Clean Architecture & SOLID Principles
- **Single Responsibility**: Each class has one clear purpose
- **Composition over Inheritance**: Build complex behavior from smaller, focused components
- **Dependency Injection**: Use factories and interfaces for loose coupling
- **Small Methods**: Methods should be small, focused, and well-named
- **Readable Code**: Code should be self-documenting and easily understood

## 🏗️ Architectural Patterns

### Factory Pattern
- **When**: Creating instances based on configuration or type strings
- **Examples**: `AnalyzerFactory`, `ScrapingCoordinatorFactory`
- **Benefits**: Extensible, testable, configurable component creation

### Strategy Pattern  
- **When**: Different algorithms or approaches for the same task
- **Examples**: `ScrapingStrategy` (categories vs targeted_funds)
- **Benefits**: Runtime selection of behavior, easy to add new strategies

### Composition Pattern
- **When**: Building complex functionality from smaller components
- **Examples**: `HoldingsAnalyzer` composes `DataProcessor`, `Aggregator`, `OutputBuilder`
- **Benefits**: Testable components, clear separation of concerns

### Interface Segregation
- **Principle**: Clear, focused interfaces for different responsibilities
- **Examples**: `IAnalyzer`, `IScrapingCoordinator`, `IDataStore`
- **Benefits**: Easy mocking, clear contracts, loose coupling

## 🔧 Configuration Management

### Typed Configuration Models
```python
# ✅ CORRECT: Type-safe access
config = config_provider.get_config()
timeout = config.scraping.timeout_seconds
analysis = config.get_analysis("holdings")

# ❌ AVOID: String-based access
timeout = config.get("scraping.timeout_seconds")
```

### Configuration Structure
- **Pydantic Models**: All config represented as typed models
- **Validation**: Let Pydantic handle validation and type conversion
- **Extensibility**: Easy to add new config sections and parameters
- **Environment Variables**: Support for `${VAR}` substitution

## 🎨 Code Organization

### Directory Structure
```
src/mfa/
├── analysis/
│   ├── interfaces.py          # Core abstractions
│   ├── factories.py           # Factory pattern implementations
│   ├── analyzers/             # Analysis implementations
│   └── scraping/              # Scraping coordinators
├── config/
│   ├── models.py              # Typed configuration models
│   └── settings.py            # Configuration provider
├── orchestration/             # High-level orchestration
└── scraping/                  # Core scraping functionality
```

### Naming Conventions
- **Interfaces**: Prefix with `I` (e.g., `IAnalyzer`)
- **Factories**: Suffix with `Factory` (e.g., `AnalyzerFactory`)
- **Models**: Suffix with `Config` for configuration (e.g., `ScrapingConfig`)
- **Methods**: Use clear, verb-based names (`analyze`, `scrape_for_requirement`)

## 🔄 Extension Patterns

### Adding New Analysis Types
1. Create analyzer class implementing `IAnalyzer`
2. Register with `@register_analyzer("type-name")`
3. Define data requirements in `get_data_requirements()`
4. Implement analysis logic in `analyze()`

### Adding New Scraping Strategies
1. Create coordinator class implementing `IScrapingCoordinator`
2. Register with `@register_coordinator("strategy-name")`
3. Implement `scrape_for_requirement()` method
4. Update configuration model if needed

### Adding New Configuration
1. Add fields to appropriate Pydantic model in `config/models.py`
2. Update YAML configuration files
3. Access via typed properties: `config.section.field`

## 🧪 Testing Strategy

### Unit Tests
- Test individual components in isolation
- Use dependency injection for mocking
- Focus on business logic and edge cases

### Integration Tests
- Test end-to-end workflows
- Use temporary directories and test configurations
- Verify actual file outputs and analysis results

### Configuration Tests
- Validate configuration loading and type conversion
- Test environment variable substitution
- Ensure proper error handling for invalid configs

## 🚀 Performance Considerations

### Scraping Efficiency
- **Parameterized**: `max_holdings` based on analysis needs
- **In-Memory Processing**: Process scraped data without intermediate file storage
- **Session Reuse**: Share browser sessions across multiple scrapes
- **Configurable Delays**: Respectful scraping with configurable delays

### Memory Management
- **Streaming**: Process large datasets in chunks when possible
- **Cleanup**: Proper resource cleanup in finally blocks
- **Caching**: Cache configuration and expensive computations

## ⚡ Quick Reference

### Adding a New Analysis
1. Create analyzer class in `analysis/analyzers/`
2. Implement `IAnalyzer` interface
3. Register with decorator
4. Add configuration to YAML
5. Write tests

### Adding Configuration
1. Add to Pydantic model in `config/models.py`
2. Update YAML files
3. Access via `config.section.field`
4. No string keys allowed!

### Debugging
- Use structured logging with context
- Include relevant metadata in log messages
- Prefer specific error messages over generic ones

## 📚 References

- **Pydantic Documentation**: https://pydantic-docs.helpmanual.io/
- **Clean Architecture**: Robert C. Martin
- **Design Patterns**: Gang of Four
- **SOLID Principles**: Robert C. Martin

---

**Remember**: When in doubt, prefer the cleaner, more typed, more explicit approach. Code should be easy to read, understand, and extend.
