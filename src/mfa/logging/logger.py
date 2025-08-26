from __future__ import annotations

from pathlib import Path
from loguru import logger


def setup_logging(log_dir: str | Path = "outputs") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))
    logger.add(
        Path(log_dir) / "mfa.log",
        rotation="10 MB",
        retention=10,
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        level="INFO",
    )


__all__ = ["logger", "setup_logging"]


