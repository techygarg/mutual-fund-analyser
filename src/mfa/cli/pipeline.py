from __future__ import annotations

from mfa.cli.analyze import main as analyze_main
from mfa.cli.scrape import main as scrape_main


def main() -> None:
    scrape_main()
    analyze_main()


if __name__ == "__main__":
    main()
