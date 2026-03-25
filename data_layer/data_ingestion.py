"""
data_ingestion.py — CLI entrypoint for the Oraculum Data Ingestion Module.

Usage:
    python data_ingestion.py process <file> --type <transactions|obligations|receivables>
    python data_ingestion.py report
    python data_ingestion.py add-transaction --date ... --description ... --amount ... --type ...
    python data_ingestion.py add-obligation --vendor ... --description ... --amount ... --due-date ...
    python data_ingestion.py add-receivable --client ... --description ... --amount ... --expected-date ...
"""

import argparse
import sys
import os
import json

# Ensure imports work when running from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import logger, MASTER_JSON_PATH
from parsers import detect_format, parse_csv, parse_json, parse_txt_gemini
from ocr_parser import parse_image
from cleaners import CLEANERS, apply_defaults
from validators import validate_record
from id_generator import generate_id
from master_json import load_master, save_master, merge_records
from manual_entry import (
    add_manual_transaction,
    add_manual_obligation,
    add_manual_receivable,
)


# ─── File Processing Pipeline ─────────────────────────────────────────────────

def process_file(filepath: str, table_type: str) -> None:
    """
    Full ingestion pipeline for a file:
    1. Detect format
    2. Parse
    3. Clean & normalize each record
    4. Validate
    5. Generate IDs
    6. Merge into master JSON
    7. Print validation report
    """
    logger.info(f"{'═' * 60}")
    logger.info(f"Processing: {os.path.basename(filepath)}")
    logger.info(f"Table type: {table_type}")
    logger.info(f"{'═' * 60}")

    # 1. Detect format
    fmt = detect_format(filepath)
    logger.info(f"  Format detected: {fmt.upper()}")

    # 2. Parse
    if fmt == "csv":
        raw_records = parse_csv(filepath)
        _process_records(raw_records, table_type, os.path.basename(filepath))

    elif fmt == "json":
        raw_records = parse_json(filepath)
        _process_records(raw_records, table_type, os.path.basename(filepath))

    elif fmt == "txt":
        api_key = os.environ.get("GEMINI_API_KEY")
        parsed = parse_txt_gemini(filepath, api_key)

        # TXT can contain mixed types — process each
        source = os.path.basename(filepath)
        total_added = 0
        total_skipped = 0

        for ttype in ("transactions", "obligations", "receivables"):
            records = parsed.get(ttype, [])
            if records:
                logger.info(f"\n  ── {ttype.upper()} ({len(records)} found) ──")
                report = _process_records(records, ttype, source)
                total_added += report["added"]
                total_skipped += report["skipped"]

        logger.info(f"\n  TXT total: {total_added} added, {total_skipped} skipped")
        return

    elif fmt == "image":
        parsed = parse_image(filepath)
        
        source = os.path.basename(filepath)
        total_added = 0
        
        for ttype in ("transactions", "obligations", "receivables"):
            records = parsed.get(ttype, [])
            if records:
                logger.info(f"\n  ── {ttype.upper()} ({len(records)} auto-processed) ──")
                total_added += len(records)
                
        hw_docs = parsed.get("hand_written_docs", [])
        if hw_docs:
            logger.info(f"\n  ── HAND_WRITTEN_DOCS ({len(hw_docs)} processed) ──")
            logger.info(f"  Status: {parsed.get('status')} | Message: {parsed.get('message')}")
            
        logger.info(f"\n  IMAGE total auto-integrated: {total_added}")
        return

    logger.info(f"{'═' * 60}")


def _process_records(raw_records: list, table_type: str, source: str) -> dict:
    """Clean, validate, generate IDs, and merge records."""
    cleaner = CLEANERS.get(table_type)
    if not cleaner:
        logger.error(f"Unknown table type: {table_type}")
        return {"added": 0, "skipped": 0, "errors": [f"Unknown type: {table_type}"]}

    id_field = {
        "transactions": "transaction_id",
        "obligations": "obligation_id",
        "receivables": "receivable_id",
    }[table_type]

    date_field = {
        "transactions": "date",
        "obligations": "due_date",
        "receivables": "expected_date",
    }[table_type]

    cleaned_records = []
    error_count = 0

    for i, raw in enumerate(raw_records):
        row_label = f"Row {i + 1}"
        try:
            # Set source
            raw["source"] = raw.get("source", source)

            # Clean
            cleaned = cleaner(raw)

            # Apply defaults
            cleaned = apply_defaults(cleaned, table_type)

            # Generate ID
            date_val = cleaned.get(date_field, "")
            cleaned[id_field] = generate_id(table_type, date_val)

            # Validate
            errors = validate_record(cleaned, table_type)
            if errors:
                for err in errors:
                    logger.warning(f"  ⚠ {row_label}: {err}")
                error_count += 1
                continue

            cleaned_records.append(cleaned)
            logger.info(f"  ✓ {row_label}: {cleaned.get('description', 'N/A')[:50]}")

        except Exception as e:
            logger.error(f"  ✗ {row_label}: {e}")
            error_count += 1

    # Merge into master JSON
    master = load_master()
    report = merge_records(master, cleaned_records, table_type, source)
    save_master(master)

    # Print summary
    logger.info(f"\n  ── Summary ──")
    logger.info(f"  Processed: {len(raw_records)} rows")
    logger.info(f"  Added:     {report['added']}")
    logger.info(f"  Skipped:   {report['skipped']} (duplicates)")
    logger.info(f"  Errors:    {error_count}")

    return report


# ─── Validation Report ────────────────────────────────────────────────────────

def print_report() -> None:
    """Print a validation report of the current master JSON."""
    master = load_master()

    print(f"\n{'═' * 60}")
    print(f"  ORACULUM — Master JSON Validation Report")
    print(f"{'═' * 60}")

    meta = master["metadata"]
    print(f"\n  Created:      {meta.get('created_at', 'N/A')}")
    print(f"  Last Updated: {meta.get('last_updated', 'N/A')}")
    print(f"  Source Files:  {', '.join(meta.get('source_files', [])) or 'None'}")

    counts = meta.get("record_counts", {})
    total = sum(counts.values())
    print(f"\n  ── Record Counts ──")
    print(f"  Transactions:  {counts.get('transactions', 0)}")
    print(f"  Obligations:   {counts.get('obligations', 0)}")
    print(f"  Receivables:   {counts.get('receivables', 0)}")
    print(f"  Total:         {total}")

    # Check for issues
    issues = 0

    # Validate all transactions have running balances
    for txn in master.get("transactions", []):
        if "running_balance" not in txn:
            issues += 1

    # Validate all IDs are unique
    for table_type in ("transactions", "obligations", "receivables"):
        id_field = table_type[:-1] + "_id"
        if table_type == "transactions":
            id_field = "transaction_id"
        elif table_type == "obligations":
            id_field = "obligation_id"
        else:
            id_field = "receivable_id"

        ids = [r.get(id_field) for r in master.get(table_type, [])]
        if len(ids) != len(set(ids)):
            issues += 1
            print(f"  ⚠ Duplicate IDs found in {table_type}!")

    if issues == 0:
        print(f"\n  ✅ NO ISSUES FOUND — {total} records, 0 duplicates, 0 errors.")
    else:
        print(f"\n  ⚠ {issues} issue(s) found. Review recommended.")

    # Show last few transactions with balances
    txns = master.get("transactions", [])
    if txns:
        print(f"\n  ── Recent Transactions ──")
        for txn in txns[-5:]:
            print(f"  {txn['date']} │ {txn['description'][:30]:<30} │ "
                  f"{'%+.2f' % txn['amount']:>10} │ "
                  f"Balance: {txn['running_balance']:>10.2f}")

    print(f"\n{'═' * 60}\n")


# ─── CLI Argument Parser ──────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data_ingestion",
        description="Oraculum Data Ingestion Module — CashFlow Guardian",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── process ──
    proc = subparsers.add_parser("process", help="Process a data file")
    proc.add_argument("file", help="Path to the data file")
    proc.add_argument(
        "--type", "-t",
        choices=["transactions", "obligations", "receivables"],
        help="Data type (required for CSV/JSON, auto-detected for TXT)",
    )

    # ── report ──
    subparsers.add_parser("report", help="Print validation report")

    # ── add-transaction ──
    add_txn = subparsers.add_parser("add-transaction", help="Add a manual transaction")
    add_txn.add_argument("--date", required=True)
    add_txn.add_argument("--description", required=True)
    add_txn.add_argument("--amount", required=True, type=float)
    add_txn.add_argument("--type", required=True,
                         choices=["income", "expense", "transfer", "starting"])
    add_txn.add_argument("--category", default=None)

    # ── add-obligation ──
    add_obl = subparsers.add_parser("add-obligation", help="Add a manual obligation")
    add_obl.add_argument("--vendor", required=True)
    add_obl.add_argument("--description", required=True)
    add_obl.add_argument("--amount", required=True, type=float)
    add_obl.add_argument("--due-date", required=True)
    add_obl.add_argument("--is-critical", action="store_true", default=False)
    add_obl.add_argument("--category", default="other")
    add_obl.add_argument("--recurring", action="store_true", default=False)
    add_obl.add_argument("--periodicity", default=None)
    add_obl.add_argument("--flexibility-score", type=float, default=0.5)

    # ── add-receivable ──
    add_rec = subparsers.add_parser("add-receivable", help="Add a manual receivable")
    add_rec.add_argument("--client", required=True)
    add_rec.add_argument("--description", required=True)
    add_rec.add_argument("--amount", required=True, type=float)
    add_rec.add_argument("--expected-date", required=True)
    add_rec.add_argument("--probability", type=float, default=0.9)
    add_rec.add_argument("--client-tier", default="standard")
    add_rec.add_argument("--recurring", action="store_true", default=False)
    add_rec.add_argument("--periodicity", default=None)

    return parser


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "process":
        filepath = os.path.abspath(args.file)

        fmt = detect_format(filepath)
        table_type = args.type

        # For TXT/IMAGE files, type is auto-detected (mixed content)
        if fmt in ("txt", "image"):
            if table_type:
                logger.info(f"Note: {fmt.upper()} files may contain mixed types. "
                            f"--type will be ignored; all types extracted.")
            process_file(filepath, "transactions")  # table_type unused for TXT/IMAGE
        else:
            if not table_type:
                # Interactive prompt
                print("\nWhat type of data is this?")
                print("  (1) Transactions")
                print("  (2) Obligations")
                print("  (3) Receivables")
                choice = input("\nSelect [1/2/3]: ").strip()
                type_map = {"1": "transactions", "2": "obligations", "3": "receivables"}
                table_type = type_map.get(choice)
                if not table_type:
                    print("Invalid choice. Aborting.")
                    sys.exit(1)

            process_file(filepath, table_type)

    elif args.command == "report":
        print_report()

    elif args.command == "add-transaction":
        result = add_manual_transaction(
            date=args.date,
            description=args.description,
            amount=args.amount,
            txn_type=args.type,
            category=args.category,
        )
        if result["success"]:
            print(f"\n✅ Transaction added: {result['record']['transaction_id']}")
            print(f"   Balance: {result['record']['running_balance']:.2f}")
        else:
            print(f"\n❌ Failed: {result['errors']}")

    elif args.command == "add-obligation":
        result = add_manual_obligation(
            vendor=args.vendor,
            description=args.description,
            amount=args.amount,
            due_date=args.due_date,
            is_critical=args.is_critical,
            category=args.category,
            recurring_payment=args.recurring,
            periodicity=args.periodicity,
            flexibility_score=args.flexibility_score,
        )
        if result["success"]:
            print(f"\n✅ Obligation added: {result['record']['obligation_id']}")
        else:
            print(f"\n❌ Failed: {result['errors']}")

    elif args.command == "add-receivable":
        result = add_manual_receivable(
            client=args.client,
            description=args.description,
            amount=args.amount,
            expected_date=args.expected_date,
            probability=args.probability,
            client_tier=args.client_tier,
            recurring_payment=args.recurring,
            periodicity=args.periodicity,
        )
        if result["success"]:
            print(f"\n✅ Receivable added: {result['record']['receivable_id']}")
        else:
            print(f"\n❌ Failed: {result['errors']}")


if __name__ == "__main__":
    main()
