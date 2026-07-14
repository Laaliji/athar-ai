"""
Ingestion CLI — fetches articles and builds the knowledge base.

Usage:
    python scripts/ingest.py
    python scripts/ingest.py --max 20
    python scripts/ingest.py --overwrite
    python scripts/ingest.py --topics "Ancient Rome" "Byzantine Empire"
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from athar.ingestion.ingest import run_ingestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Athar AI — knowledge base ingestion")
    parser.add_argument("--topics", nargs="+", default=None,
                        help="Specific article titles to fetch")
    parser.add_argument("--max", type=int, default=40, dest="max_articles",
                        help="Maximum articles to fetch (default: 40)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Drop existing vectors and rebuild from scratch")
    args = parser.parse_args()

    print("\nAthar AI - Ingestion Pipeline")
    print("=" * 40)

    result = run_ingestion(
        topics=args.topics,
        max_articles=args.max_articles,
        overwrite=args.overwrite,
    )

    if result["success"]:
        print("\nDone!")
        print(f"  Articles fetched : {result['articles_fetched']}")
        print(f"  Chunks created   : {result['chunks_created']}")
        print(f"  Duration         : {result['duration_seconds']:.1f}s")
        print("\nStart the server: cd backend && uvicorn athar.main:app --reload")
    else:
        print(f"\nFailed: {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
