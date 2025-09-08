"""Company name normalization utilities."""

from __future__ import annotations

import re


class CompanyNameNormalizer:
    """Utility class for normalizing company names across different formats."""

    # Common suffix mappings
    SUFFIX_MAPPINGS = {
        "ltd.": "limited",
        "ltd": "limited",
        "limited.": "limited",
        "corp.": "corporation",
        "corp": "corporation",
        "corporation.": "corporation",
        "inc.": "incorporated",
        "inc": "incorporated",
        "incorporated.": "incorporated",
        "co.": "company",
        "co": "company",
        "company.": "company",
        "pvt.": "private",
        "pvt": "private",
        "private.": "private",
        "llc.": "llc",
        "llc": "llc",
        "&": "and",
        "and": "and",
    }

    # Common company name variations
    NAME_VARIATIONS = {
        # HDFC variations
        "hdfc bank limited": "hdfc bank ltd",
        "hdfc bank ltd.": "hdfc bank ltd",
        "hdfc bank ltd": "hdfc bank ltd",
        # ICICI variations
        "icici bank limited": "icici bank ltd",
        "icici bank ltd.": "icici bank ltd",
        "icici bank ltd": "icici bank ltd",
        # Infosys variations
        "infosys technologies limited": "infosys limited",
        "infosys technologies ltd": "infosys limited",
        "infosys technologies ltd.": "infosys limited",
        # Tata variations
        "tata consultancy services limited": "tata consultancy services ltd",
        "tata consultancy services ltd.": "tata consultancy services ltd",
        # NTPC variations
        "ntpc limited": "ntpc ltd",
        "ntpc ltd.": "ntpc ltd",
        # Ambuja variations
        "ambuja cements limited": "ambuja cements ltd",
        "ambuja cements ltd.": "ambuja cements ltd",
    }

    @classmethod
    def normalize(cls, company_name: str) -> str:
        """Normalize a company name to a standard format."""
        if not company_name:
            return ""

        # Convert to lowercase for processing
        name = company_name.lower().strip()

        # Remove extra whitespace
        name = re.sub(r"\s+", " ", name)

        # Apply specific name variations first
        if name in cls.NAME_VARIATIONS:
            return cls.NAME_VARIATIONS[name]

        # Remove common suffixes and replace with standard forms
        words = name.split()
        normalized_words = []

        for word in words:
            # Remove trailing periods and normalize suffixes
            clean_word = word.rstrip(".")
            if clean_word in cls.SUFFIX_MAPPINGS:
                normalized_words.append(cls.SUFFIX_MAPPINGS[clean_word])
            else:
                normalized_words.append(clean_word)

        # Join words back
        normalized = " ".join(normalized_words)

        # Apply name variations again after suffix normalization
        if normalized in cls.NAME_VARIATIONS:
            return cls.NAME_VARIATIONS[normalized]

        return normalized

    @classmethod
    def add_variation(cls, original: str, canonical: str) -> None:
        """Add a new company name variation mapping."""
        cls.NAME_VARIATIONS[original.lower()] = canonical.lower()

    @classmethod
    def get_canonical_name(cls, variations: list[str]) -> str:
        """Get the canonical name from a list of variations."""
        if not variations:
            return ""

        # Normalize all variations and find the most common form
        normalized = [cls.normalize(v) for v in variations]
        if normalized:
            return max(set(normalized), key=normalized.count)

        return variations[0]
