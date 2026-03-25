"""
manual_entry.py — Manual entry functions for Flutter integration.
Three functions exposed as API endpoints.
"""

from config import logger
from id_generator import generate_id
from cleaners import (
    standardize_date, normalize_amount, ensure_expense_negative,
    map_category, normalize_bool, apply_defaults,
)
from validators import validate_record
from master_json import load_master, save_master, merge_records


def add_manual_transaction(
    date: str,
    description: str,
    amount,
    txn_type: str,
    category: str = None,
    master_path: str = None,
) -> dict:
    """
    Add a single transaction via manual entry.
    Validate → generate ID → calc balance → append to master JSON.

    Returns: dict with 'success', 'record', and 'report' keys.
    """
    logger.info(f"Manual transaction: {description} | {amount} | {txn_type}")

    try:
        # Clean fields
        clean_date = standardize_date(date)
        clean_amount = normalize_amount(amount)
        clean_amount = ensure_expense_negative(clean_amount, txn_type)
        clean_category = map_category(category)
        clean_type = str(txn_type).lower().strip()

        # Build record
        record = {
            "transaction_id": generate_id("transactions", clean_date),
            "date": clean_date,
            "description": str(description).strip(),
            "amount": clean_amount,
            "type": clean_type,
            "running_balance": 0.0,
            "source": "manual_entry",
            "category": clean_category,
            "is_duplicate": False,
        }

        # Validate
        errors = validate_record(record, "transactions")
        if errors:
            return {"success": False, "errors": errors, "record": None}

        # Merge into master
        master = load_master(master_path)
        report = merge_records(master, [record], "transactions", "manual_entry")
        save_master(master, master_path)

        return {"success": True, "record": record, "report": report}

    except Exception as e:
        logger.error(f"Manual transaction failed: {e}")
        return {"success": False, "errors": [str(e)], "record": None}


def add_manual_obligation(
    vendor: str,
    description: str,
    amount,
    due_date: str,
    is_critical: bool = False,
    category: str = "other",
    recurring_payment: bool = False,
    periodicity: str = None,
    flexibility_score: float = 0.5,
    master_path: str = None,
) -> dict:
    """
    Add a single obligation via manual entry.
    Validate → generate ID → append to master JSON.

    Returns: dict with 'success', 'record', and 'report' keys.
    """
    logger.info(f"Manual obligation: {vendor} | {description} | {amount}")

    try:
        clean_date = standardize_date(due_date)
        clean_amount = abs(normalize_amount(amount))

        record = {
            "obligation_id": generate_id("obligations", clean_date),
            "vendor": str(vendor).strip(),
            "description": str(description).strip(),
            "amount": clean_amount,
            "due_date": clean_date,
            "invoice_id": "",
            "category": map_category(category),
            "is_critical": normalize_bool(is_critical),
            "late_fee": 0.0,
            "grace_days": 0,
            "flexibility_score": float(flexibility_score),
            "relationship_tier": "standard",
            "recurring_payment": normalize_bool(recurring_payment),
            "periodicity": periodicity,
            "source": "manual_entry",
        }

        record = apply_defaults(record, "obligations")

        errors = validate_record(record, "obligations")
        if errors:
            return {"success": False, "errors": errors, "record": None}

        master = load_master(master_path)
        report = merge_records(master, [record], "obligations", "manual_entry")
        save_master(master, master_path)

        return {"success": True, "record": record, "report": report}

    except Exception as e:
        logger.error(f"Manual obligation failed: {e}")
        return {"success": False, "errors": [str(e)], "record": None}


def add_manual_receivable(
    client: str,
    description: str,
    amount,
    expected_date: str,
    probability: float = 0.9,
    client_tier: str = "standard",
    recurring_payment: bool = False,
    periodicity: str = None,
    master_path: str = None,
) -> dict:
    """
    Add a single receivable via manual entry.
    Validate → generate ID → append to master JSON.

    Returns: dict with 'success', 'record', and 'report' keys.
    """
    logger.info(f"Manual receivable: {client} | {description} | {amount}")

    try:
        clean_date = standardize_date(expected_date)
        clean_amount = abs(normalize_amount(amount))

        from datetime import datetime, date as date_type
        expected_dt = datetime.strptime(clean_date, "%Y-%m-%d").date()
        is_overdue = expected_dt < date_type.today()

        record = {
            "receivable_id": generate_id("receivables", clean_date),
            "client": str(client).strip(),
            "description": str(description).strip(),
            "amount": clean_amount,
            "expected_date": clean_date,
            "invoice_id": "",
            "category": "other",
            "probability": float(probability),
            "client_tier": str(client_tier).lower().strip(),
            "payment_terms": "Net 30",
            "is_overdue": is_overdue,
            "recurring_payment": normalize_bool(recurring_payment),
            "periodicity": periodicity,
            "source": "manual_entry",
        }

        record = apply_defaults(record, "receivables")

        errors = validate_record(record, "receivables")
        if errors:
            return {"success": False, "errors": errors, "record": None}

        master = load_master(master_path)
        report = merge_records(master, [record], "receivables", "manual_entry")
        save_master(master, master_path)

        return {"success": True, "record": record, "report": report}

    except Exception as e:
        logger.error(f"Manual receivable failed: {e}")
        return {"success": False, "errors": [str(e)], "record": None}
