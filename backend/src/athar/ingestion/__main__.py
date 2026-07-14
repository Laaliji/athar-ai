"""Run knowledge-base ingestion."""

from __future__ import annotations

import argparse
import logging

from athar.ingestion.ingest import run_ingestion


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Athar RAG knowledge base")
    parser.add_argument("--topics", nargs="+", help="Specific Wikipedia article titles")
    parser.add_argument("--max", dest="max_articles", type=int, default=40)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Discard existing vectors and rebuild the collection",
    )
    parser.add_argument(
        "--without-met",
        action="store_true",
        help="Skip Met Museum records during default ingestion",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    result = run_ingestion(
        topics=args.topics,
        max_articles=args.max_articles,
        overwrite=args.overwrite,
        include_met=not args.without_met,
    )
    if not result["success"]:
        raise SystemExit(result["message"])
    print(result["message"])


if __name__ == "__main__":
    main()
