from __future__ import annotations

from pathlib import Path


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def project_root() -> Path:
    return Path.cwd()
