# Design Principles

**Core principles guiding MFA development.**

## 🎯 Core Principles

### 1. Complete Migration Philosophy
**When refactoring, completely remove old code. No legacy support.**

- ✅ Clean migrations with single, modern approaches
- ❌ No backward compatibility layers or deprecated methods
- Example: Removed all string-based config access for typed Pydantic models

### 2. Type Safety First
**Strong typing everywhere - no string-based access patterns.**

- ✅ Pydantic models for configuration
- ✅ Type annotations on all functions/methods
- ✅ Interface contracts with clear signatures
- Benefits: IDE support, refactoring safety, compile-time error detection

### 3. Analysis-Driven Design
**Scraping dictated by analysis requirements.**

- Pattern: `Analysis → DataRequirement → Coordinator → Scraper`
- Different analyses can request different data
- New analysis types define their own data needs

### 4. Clean Code Principles
- ✅ **Single Responsibility** - Each class has one clear purpose
- ✅ **Composition over Inheritance** - Small, focused components
- ✅ **Dependency Injection** - Loose coupling via constructor injection
- ✅ **Small Methods** - Focused, well-named functions
- ✅ **Readable Code** - Self-documenting with clear naming

## 🏗️ Key Patterns

### Factory Pattern
**For creating instances based on configuration:**
```python
@register_analyzer("holdings")
class HoldingsAnalyzer(BaseAnalyzer):
    def __init__(self, config_provider):
        super().__init__(config_provider, "holdings")

analyzer = AnalyzerFactory.create_analyzer("holdings", config_provider)
```

### Strategy Pattern
**For different algorithms/approaches:**
```python
coordinator = ScrapingCoordinatorFactory.create_coordinator("categories", config_provider)
```

### Composition Pattern
**Building complex behavior from smaller components:**
```python
class HoldingsAnalyzer(BaseAnalyzer):
    def __init__(self, config_provider):
        self.data_processor = HoldingsDataProcessor(config_provider)
        self.aggregator = HoldingsAggregator(config_provider)
```

## ⚙️ Configuration

### Type-Safe Access
```python
# ✅ CORRECT: Type-safe access
config = config_provider.get_config()
timeout = config.scraping.timeout_seconds

# ❌ AVOID: String-based access
timeout = config.get("scraping.timeout_seconds")
```

## 🚀 Quick Reference

### Adding New Analysis
1. Create analyzer class with `@register_analyzer("type-name")`
2. Implement `IAnalyzer` interface
3. Add configuration to YAML
4. Write tests

### Adding New Configuration
1. Add to Pydantic model in `config/models.py`
2. Update YAML files
3. Access via `config.section.field`
4. **No string keys allowed!**

### Code Standards
- **Type Hints**: All functions must have type annotations
- **Docstrings**: Comprehensive documentation for public APIs
- **Linting**: Must pass `make lint` before merging
- **Testing**: 90%+ code coverage for new features

---

**Remember**: Prefer the cleaner, more typed, more explicit approach. Code should be easy to read, understand, and extend.