from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

import orjson

from mfa.config.settings import config  
from mfa.logging.logger import logger, setup_logging


def _iter_json_files(root: Path):
    # Support nested structure: output/date/category/*.json
    for path in sorted(root.rglob("*.json")):
        yield path


def _latest_date_dir(root: Path) -> Path:
    if not root.exists():
        return root
    date_dirs = [p for p in root.iterdir() if p.is_dir() and re.fullmatch(r"\d{8}", p.name)]
    if not date_dirs:
        return root
    latest = max(date_dirs, key=lambda p: p.name)
    return latest


def _parse_percent(value: str) -> float:
    if not value:
        return 0.0
    m = re.search(r"(\d{1,3}(?:\.\d+)?)%", str(value))
    return float(m.group(1)) if m else 0.0


def _normalize_company(name: str) -> str:
    n = name.strip()
    # Remove common suffixes and punctuation variants
    n = re.sub(r"\b(pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited)\b", "", n, flags=re.I)
    # Normalize ampersand spacing
    n = re.sub(r"\s*&\s*", " & ", n)
    # Collapse multiple spaces
    n = re.sub(r"\s+", " ", n)
    # Trim leading/trailing spaces and punctuation (including '.')
    n = re.sub(r"^[\s\.,:;\-]+", "", n)
    n = re.sub(r"[\s\.,:;\-]+$", "", n)
    n = n.replace(" ", " ")  # non-breaking space
    return n.strip()


def _load(path: Path) -> dict:
    with open(path, "rb") as fh:
        return orjson.loads(fh.read())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze fund holdings JSONs")
    parser.add_argument("--date", help="YYYYMMDD date folder under outputs/extracted_json")
    parser.add_argument("--category", help="Category to analyze (e.g., largeCap)")
    return parser.parse_args()


def main() -> None:
    config.ensure_directories()
    setup_logging("outputs")

    input_dir = Path(str(config.get("paths.output_dir")))
    analysis_dir = Path(str(config.get("paths.analysis_dir")))
    analysis_dir.mkdir(parents=True, exist_ok=True)

    args = _parse_args()
    # Choose date folder
    if args.date:
        scan_root = input_dir / args.date
        if not scan_root.exists():
            logger.error("Date folder {} not found under {}", scan_root.name, input_dir)
            return
    else:
        scan_root = _latest_date_dir(input_dir)

    def aggregate(files_iter):
        company_to_fund_set: Dict[str, set] = defaultdict(set)
        company_total_weight: Dict[str, float] = defaultdict(float)
        company_examples: Dict[str, List[str]] = defaultdict(list)
        funds_seen: set = set()
        funds_info: Dict[str, str] = {}
        processed_files: List[Path] = []
        for fp in files_iter:
            try:
                data = _load(fp)
            except Exception:
                continue
            d = data.get("data") or {}
            fund_info = d.get("fund_info") or {}
            fund_name = fund_info.get("fund_name") or fp.stem
            fund_aum = str(fund_info.get("aum") or "").strip()
            holdings = d.get("top_holdings") or []
            processed_files.append(fp)
            funds_seen.add(fund_name)
            if fund_name not in funds_info:
                funds_info[fund_name] = fund_aum
            for h in holdings:
                name = _normalize_company(h.get("company_name") or "")
                if not name:
                    continue
                if name.upper() in {"TREPS", "CASH", "T-BILLS", "REVERSE REPO", "REPO"}:
                    continue
                weight = _parse_percent(h.get("allocation_percentage") or "")
                company_to_fund_set[name].add(fund_name)
                company_total_weight[name] += weight
                if len(company_examples[name]) < 5:
                    company_examples[name].append(fund_name)
        by_count = sorted(
            (
                {
                    "company": name,
                    "fund_count": len(funds),
                    "total_weight": round(company_total_weight[name], 3),
                    "avg_weight": round(company_total_weight[name] / max(len(funds), 1), 3),
                    "sample_funds": sorted(list(funds))[:5],
                }
                for name, funds in company_to_fund_set.items()
            ),
            key=lambda x: (x["fund_count"], x["total_weight"]),
            reverse=True,
        )
        by_weight = sorted(
            (
                {
                    "company": name,
                    "fund_count": len(company_to_fund_set[name]),
                    "total_weight": round(w, 3),
                    "avg_weight": round(w / max(len(company_to_fund_set[name]), 1), 3),
                    "sample_funds": sorted(company_examples[name])[:5],
                }
                for name, w in company_total_weight.items()
            ),
            key=lambda x: (x["total_weight"], x["fund_count"]),
            reverse=True,
        )
        total_funds = len(funds_seen)
        common_in_all = [c for c in by_count if c["fund_count"] >= total_funds and total_funds > 0]
        return {
            "total_files": len(processed_files),
            "total_funds": total_funds,
            "funds": [
                {"name": name, "aum": funds_info.get(name, "")}
                for name in sorted(funds_info.keys())
            ],
            "unique_companies": len(company_to_fund_set),
            "top_by_fund_count": by_count[:100],
            "top_by_total_weight": by_weight[:100],
            "common_in_all_funds": common_in_all,
        }

    # Per-category selection
    if args.category:
        categories = [args.category] if (scan_root / args.category).exists() else []
        if not categories:
            logger.error("Category '{}' not found under {}", args.category, scan_root)
            return
    else:
        categories = [p.name for p in scan_root.iterdir() if p.is_dir()]

    # Build per-category aggregates and write to analysis/<date>/<category>.json
    date_dir = analysis_dir / scan_root.name
    date_dir.mkdir(parents=True, exist_ok=True)
    for cat in categories:
        cat_dir = scan_root / cat
        payload = aggregate(_iter_json_files(cat_dir))
        out_path = date_dir / f"{cat}.json"
        with open(out_path, "wb") as fh:
            fh.write(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        logger.info("Wrote analysis for category '{}' to {}", cat, out_path)


if __name__ == "__main__":
    main()


