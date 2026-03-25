"""
master_json.py — Load, save, and merge logic for master_financial_data.json.
Single source of truth — no database.
"""

import json
import os
from datetime import datetime, timezone
from config import MASTER_JSON_PATH, empty_master, logger
from validators import compute_fingerprint, collect_existing_fingerprints
from balance import compute_running_balances


def load_master(path: str = None) -> dict:
    """Load existing master JSON or return empty skeleton."""
    path = path or MASTER_JSON_PATH

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded master JSON: {path}")
            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Corrupt master JSON, starting fresh: {e}")
            return empty_master()
    else:
        logger.info("No existing master JSON found — creating new.")
        return empty_master()


def save_master(data: dict, path: str = None) -> None:
    """Save master JSON atomically (write to temp, then rename)."""
    path = path or MASTER_JSON_PATH

    # Update metadata
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if data["metadata"]["created_at"] is None:
        data["metadata"]["created_at"] = now
    data["metadata"]["last_updated"] = now
    data["metadata"]["record_counts"] = {
        "transactions": len(data["transactions"]),
        "obligations":  len(data["obligations"]),
        "receivables":  len(data["receivables"]),
    }

    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Atomic replace
    if os.path.exists(path):
        os.replace(temp_path, path)
    else:
        os.rename(temp_path, path)

    logger.info(f"Saved master JSON: {path} "
                f"(txn={len(data['transactions'])}, "
                f"obl={len(data['obligations'])}, "
                f"rec={len(data['receivables'])})")


def merge_records(master: dict, new_records: list, table_type: str,
                  source_file: str = "manual_entry") -> dict:
    """
    Merge new records into master JSON.

    Rules (from PRD):
    - New Record: Append to corresponding array.
    - Duplicate: Skip silently, mark is_duplicate=True in report.
    - Update: NOT supported (re-ingest to correct).
    - Source tracking: add source file to metadata.source_files[].

    Returns: dict with 'added', 'skipped', 'errors' counts.
    """
    existing = master[table_type]
    existing_fps = collect_existing_fingerprints(existing, table_type)

    added = 0
    skipped = 0
    errors = []

    for record in new_records:
        fp = compute_fingerprint(record, table_type)

        if fp in existing_fps:
            skipped += 1
            logger.info(f"  ⊘ Duplicate skipped: {record.get('description', 'N/A')}")
            continue

        existing.append(record)
        existing_fps.add(fp)
        added += 1

    # Recompute running balances if transactions were modified
    if table_type == "transactions" and added > 0:
        master["transactions"] = compute_running_balances(master["transactions"])

    # Track source file
    if source_file and source_file not in master["metadata"]["source_files"]:
        master["metadata"]["source_files"].append(source_file)

    report = {"added": added, "skipped": skipped, "errors": errors}

    logger.info(f"  Merge complete: {added} added, {skipped} duplicates skipped")

    return report
