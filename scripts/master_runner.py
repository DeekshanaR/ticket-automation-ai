"""Batch 'master script': processes a CSV of incoming tickets end-to-end.

For every row it creates a ticket, classifies it with AI, auto-assigns it and
then simulates the work (IN_PROGRESS -> RESOLVED -> CLOSED), logging each step.
Designed to be run from a Linux terminal or a cron job.

Usage:  python -m scripts.master_runner --input data/incoming_tickets.csv
"""
import argparse
import csv
import logging
import sys

from app import service

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("master_runner")


def run(input_path: str, auto_close: bool = True) -> dict:
    ok = failed = review = 0
    with open(input_path, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                ticket = service.create_ticket(row["title"], row["description"])
                log.info("Ticket #%s -> %s | %s priority | team=%s | status=%s",
                         ticket["id"], ticket["category"], ticket["priority"],
                         ticket["assignee"], ticket["status"])
                if ticket["needs_review"]:
                    review += 1
                elif auto_close:
                    for status in ("IN_PROGRESS", "RESOLVED", "CLOSED"):
                        service.transition(ticket["id"], status, "Automated by master_runner")
                ok += 1
            except Exception as exc:
                failed += 1
                log.error("Row %s failed: %s", line_no, exc)
    summary = {"processed": ok, "failed": failed, "manual_review": review}
    log.info("SUMMARY %s", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="CSV with columns: title,description")
    parser.add_argument("--no-close", action="store_true", help="leave tickets assigned")
    args = parser.parse_args()
    result = run(args.input, auto_close=not args.no_close)
    sys.exit(1 if result["failed"] else 0)
