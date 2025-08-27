# Architecture

This project follows a **clean, modular architecture** with clear separation of concerns:

## 🏗️ High-Level Structure

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Layer     │    │  Business Logic │    │  Infrastructure │
│                 │    │                 │    │                 │
│ • orchestrate   │───▶│ • Orchestrator  │───▶│ • JsonStore     │
│ • analyze       │    │ • Analyzer      │    │ • PlaywrightScr │
│ • pipeline      │    │ • ZerodhaScraper│    │ • Config        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Design Principles:**
- **Thin CLI** - Only argument parsing, delegates to business logic
- **Single Responsibility** - Each module has one clear purpose  
- **Configuration-Driven** - User-friendly YAML configuration
- **Testable** - Business logic separated from I/O and CLI concerns

## 📦 Module Overview

### CLI Layer (`src/mfa/cli/`)
**Purpose:** Thin interface layer that only handles argument parsing

- `orchestrate.py` - Entry point for fund data collection
- `analyze.py` - Entry point for holdings analysis  
- `pipeline.py` - Combined scrape + analyze workflow
- `scrape.py` - Direct scraping utility

### Business Logic

#### Orchestration (`src/mfa/orchestration/`)
**Purpose:** Coordinates fund data collection across categories

- `orchestrator.py` - Main orchestration logic
  - Validates configuration and fund categories
  - Manages scraping sessions and rate limiting
  - Handles errors and provides comprehensive logging
  - Returns structured results with success/failure statistics

#### Analysis (`src/mfa/analysis/`)  
**Purpose:** Processes scraped data to find patterns and overlaps

- `analyzer.py` - Core analysis engine
  - Aggregates holdings across multiple funds
  - Normalizes company names and filters excluded holdings
  - Builds ranked lists by fund count and total weight
  - Identifies companies common across all funds

#### Storage (`src/mfa/storage/`)
**Purpose:** Centralized file I/O operations

- `json_store.py` - JSON persistence layer
  - Save/load operations with error handling
  - File validation and size reporting
  - Consistent JSON formatting across the application

### Infrastructure

#### Scraping (`src/mfa/scraping/`)
**Purpose:** Browser automation and site-specific data extraction

- `core/playwright_scraper.py` - Reusable browser automation
  - Session management with lazy initialization
  - Navigation helpers (goto, click, wait)
  - Table parsing and data extraction utilities
- `zerodha_coin.py` - Site-specific scraper implementation
  - Extends base scraper for Zerodha Coin specifics
  - Handles fund page navigation and holdings extraction

#### Web Interface (`src/mfa/web/`)
**Purpose:** Dashboard and visualization

- `server.py` - FastAPI backend serving API + static files
- `static/index.html` - Interactive frontend with Chart.js

#### Configuration & Support
- `config/settings.py` - Configuration management via Pydantic
- `logging/logger.py` - Structured logging with Loguru
- `models/schemas.py` - Type-safe data models

## 🔧 Key Architectural Benefits

**1. Testability**
- Business logic is isolated from CLI and I/O concerns
- Each module can be unit tested independently
- Clear interfaces between components

**2. Maintainability**  
- Single responsibility principle applied throughout
- Clear separation between configuration and code
- Modular structure allows independent evolution

**3. Extensibility**
- Easy to add new scrapers by extending base classes
- Configuration-driven fund management
- Plugin-style architecture for new analysis features

**4. User Experience**
- Simple YAML configuration with sensible defaults
- Comprehensive error messages and logging
- Progress tracking and success/failure reporting
