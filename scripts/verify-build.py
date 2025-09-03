#!/usr/bin/env python3
"""
MFA Build Verification Script

This script performs comprehensive validation of the Mutual Fund Analyzer project
to ensure it builds correctly and all components are functioning properly.

Usage:
    python scripts/verify-build.py
    make verify-all
"""

import sys
import importlib
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class BuildVerifier:
    """Comprehensive build verification for MFA project."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []

    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.errors.append(message)
        print(f"❌ {message}")

    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.warnings.append(message)
        print(f"⚠️  {message}")

    def log_success(self, message: str) -> None:
        """Log a success message."""
        self.successes.append(message)
        print(f"✅ {message}")

    def verify_imports(self) -> bool:
        """Verify all critical imports work."""
        print("\n📦 Verifying imports...")

        critical_imports = [
            # Core modules
            ("mfa.core.exceptions", "Custom exception hierarchy"),
            ("mfa.core.schemas", "Pydantic data models"),

            # Config system
            ("mfa.config.settings", "Configuration provider"),
            ("mfa.config.models", "Configuration models"),

            # Analysis system
            ("mfa.analysis.factories", "Factory patterns"),
            ("mfa.analysis.interfaces", "Interface definitions"),
            ("mfa.analysis.analyzers.holdings_analyzer", "Holdings analyzer"),

            # Storage system
            ("mfa.storage.json_store", "JSON storage operations"),
            ("mfa.storage.path_generator", "Path generation service"),

            # Orchestration
            ("mfa.orchestration.analysis_orchestrator", "Main orchestrator"),

            # CLI
            ("mfa.cli.analyze", "Analysis CLI"),
        ]

        success_count = 0
        for module, description in critical_imports:
            try:
                importlib.import_module(module)
                self.log_success(f"{description} ({module})")
                success_count += 1
            except ImportError as e:
                self.log_error(f"Failed to import {description} ({module}): {e}")
            except Exception as e:
                self.log_error(f"Unexpected error importing {module}: {e}")

        return success_count == len(critical_imports)

    def verify_config_loading(self) -> bool:
        """Verify configuration system works."""
        print("\n⚙️ Verifying configuration loading...")

        try:
            from mfa.config.settings import create_config_provider
            from mfa.core.exceptions import ConfigurationError

            # Test config provider creation
            config_provider = create_config_provider()
            self.log_success("ConfigProvider creation")

            # Test config loading
            config = config_provider.get_config()
            self.log_success("Configuration loading")

            # Test key configuration sections
            required_sections = ["paths", "scraping", "analyses"]
            for section in required_sections:
                if hasattr(config, section):
                    self.log_success(f"Configuration section: {section}")
                else:
                    self.log_error(f"Missing configuration section: {section}")

            return len(self.errors) == 0

        except Exception as e:
            self.log_error(f"Configuration verification failed: {e}")
            return False

    def verify_factory_patterns(self) -> bool:
        """Verify factory patterns work correctly."""
        print("\n🏭 Verifying factory patterns...")

        try:
            from mfa.analysis.factories import AnalyzerFactory
            from mfa.config.settings import create_config_provider

            config_provider = create_config_provider()

            # Test analyzer factory
            available_types = AnalyzerFactory.get_available_types()
            if available_types:
                self.log_success(f"Available analyzer types: {available_types}")

                # Test creating an analyzer
                if "fund-holdings" in available_types:
                    analyzer = AnalyzerFactory.create_analyzer("fund-holdings", config_provider)
                    self.log_success("Analyzer factory creation")
                else:
                    self.log_error("fund-holdings analyzer type not found")
            else:
                self.log_error("No analyzer types available")

            return len(self.errors) == 0

        except Exception as e:
            self.log_error(f"Factory verification failed: {e}")
            return False

    def verify_type_safety(self) -> bool:
        """Verify type annotations are valid."""
        print("\n🔎 Verifying type safety...")

        try:
            import mypy.api

            # Run mypy on source code
            result = mypy.api.run([
                "src/mfa/",
                "--ignore-missing-imports",
                "--no-error-summary"
            ])

            if result[2] == 0:  # Exit code 0 means no errors
                self.log_success("Type checking passed")
                return True
            else:
                self.log_warning(f"Type checking found issues: {result[0]}")
                return True  # Don't fail on type warnings

        except ImportError:
            self.log_warning("mypy not available for type checking")
            return True
        except Exception as e:
            self.log_error(f"Type verification failed: {e}")
            return False

    def verify_file_structure(self) -> bool:
        """Verify project file structure."""
        print("\n📁 Verifying file structure...")

        required_files = [
            "pyproject.toml",
            "config/config.yaml",
            "src/mfa/__init__.py",
            "src/mfa/core/__init__.py",
            "Makefile",
        ]

        for file_path in required_files:
            path = Path(__file__).parent.parent / file_path
            if path.exists():
                self.log_success(f"Required file: {file_path}")
            else:
                self.log_error(f"Missing required file: {file_path}")

        # Check for important directories
        required_dirs = [
            "src/mfa/core",
            "src/mfa/analysis",
            "src/mfa/storage",
            "src/mfa/config",
            "tests",
        ]

        for dir_path in required_dirs:
            path = Path(__file__).parent.parent / dir_path
            if path.is_dir():
                self.log_success(f"Required directory: {dir_path}")
            else:
                self.log_error(f"Missing required directory: {dir_path}")

        return len(self.errors) == 0

    def verify_dependencies(self) -> bool:
        """Verify Python dependencies."""
        print("\n📦 Verifying dependencies...")

        try:
            import subprocess

            # Check if all dependencies can be imported
            critical_deps = [
                ("pydantic", "Data validation"),
                ("orjson", "JSON processing"),
                ("loguru", "Logging"),
                ("playwright", "Web scraping"),
            ]

            success_count = 0
            for module, description in critical_deps:
                try:
                    importlib.import_module(module)
                    self.log_success(f"{description} ({module})")
                    success_count += 1
                except ImportError:
                    self.log_error(f"Missing dependency: {module} ({description})")

            return success_count == len(critical_deps)

        except Exception as e:
            self.log_error(f"Dependency verification failed: {e}")
            return False

    def generate_report(self) -> None:
        """Generate a summary report."""
        print("\n" + "="*60)
        print("🎯 MFA BUILD VERIFICATION REPORT")
        print("="*60)

        print(f"\n✅ Successes: {len(self.successes)}")
        for success in self.successes:
            print(f"   • {success}")

        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   • {warning}")

        if self.errors:
            print(f"\n❌ Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"   • {error}")

        print("\n" + "="*60)

        if not self.errors:
            print("🎉 VERIFICATION PASSED - Project is ready!")
            return 0
        else:
            print("❌ VERIFICATION FAILED - Fix errors before proceeding")
            return 1

    def run_all_verifications(self) -> int:
        """Run all verification checks."""
        print("🔬 Starting comprehensive MFA build verification...")

        checks = [
            self.verify_file_structure,
            self.verify_dependencies,
            self.verify_imports,
            self.verify_config_loading,
            self.verify_factory_patterns,
            self.verify_type_safety,
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                self.log_error(f"Verification check failed: {e}")
                traceback.print_exc()

        return self.generate_report()


def main() -> int:
    """Main entry point."""
    verifier = BuildVerifier()
    return verifier.run_all_verifications()


if __name__ == "__main__":
    sys.exit(main())
