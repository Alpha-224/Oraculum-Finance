"""
cleaners.py — Data cleaning & normalization.
Handles dates, amounts, categories, and default filling.
"""

import re
from datetime import datetime, date
from config import (
    DATE_FORMATS, VALID_CATEGORIES, VALID_TXN_TYPES,
    VALID_TIERS, VALID_PERIODICITIES, TABLE_SCHEMAS, logger,
)


# ─── Date Standardization ────────────────────────────────────────────────────

def standardize_date(raw) -> str:
    """
    Convert any date format to YYYY-MM-DD.
    Supports: multiple string formats, Unix timestamps, datetime objects.
    """
    if raw is None:
        raise ValueError("Date cannot be empty")

    # Already a date/datetime object
    if isinstance(raw, (date, datetime)):
        return raw.strftime("%Y-%m-%d")

    raw = str(raw).strip()
    if not raw:
        raise ValueError("Date cannot be empty")

    # Try Unix timestamp (integer or float string)
    try:
        ts = float(raw)
        if ts > 1e9:  # looks like a Unix timestamp
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except (ValueError, OSError):
        pass

    # Try each known date format
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Last resort: dateutil-style flexible parse
    # Try extracting date-like patterns
    match = re.search(r'(\w+ \d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?)', raw)
    if match:
        cleaned = re.sub(r'(st|nd|rd|th)', '', match.group(1))
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(cleaned.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue

    raise ValueError(f"Cannot parse date: '{raw}'")


# ─── Amount Normalization ─────────────────────────────────────────────────────

def normalize_amount(raw) -> float:
    """Strip $, commas, whitespace. Convert to float."""
    if isinstance(raw, (int, float)):
        return float(raw)

    raw = str(raw).strip()
    # Remove currency symbols, commas, spaces
    cleaned = re.sub(r'[$€£₹,\s]', '', raw)
    if not cleaned:
        raise ValueError("Amount cannot be empty")

    return float(cleaned)


def ensure_expense_negative(amount: float, txn_type: str) -> float:
    """Expenses must be negative, income must be positive."""
    txn_type = str(txn_type).lower().strip()
    if txn_type == "expense" and amount > 0:
        return -amount
    if txn_type == "income" and amount < 0:
        return abs(amount)
    return amount


# ─── Category Mapping ────────────────────────────────────────────────────────

def map_category(raw) -> str:
    """Map to standard taxonomy or default to 'uncategorized'."""
    if raw is None:
        return "uncategorized"

    cleaned = str(raw).lower().strip()

    if cleaned in VALID_CATEGORIES:
        return cleaned

    # Fuzzy mapping for common synonyms
    synonyms = {
        "food": "catering", "meal": "catering", "dining": "catering",
        "electric": "utilities", "water": "utilities", "gas": "utilities",
        "power": "utilities", "internet": "utilities", "phone": "utilities",
        "salary": "other", "wage": "other", "payroll": "other",
        "supply": "inventory", "stock": "inventory", "material": "inventory",
        "lease": "rent", "office": "rent",
        "revenue": "sales", "payment": "sales", "income": "sales",
        "sub": "subscription", "membership": "subscription",
    }
    for keyword, category in synonyms.items():
        if keyword in cleaned:
            return category

    return "uncategorized"


# ─── Boolean Normalization ───────────────────────────────────────────────────

def normalize_bool(raw) -> bool:
    """Convert various truthy/falsy values to bool."""
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    raw = str(raw).lower().strip()
    return raw in ("true", "yes", "1", "t", "y")


# ─── Apply Defaults ──────────────────────────────────────────────────────────

def apply_defaults(record: dict, table_type: str) -> dict:
    """
    Fill missing optional fields with documented defaults.
    Returns a new dict with all schema fields present.
    """
    schema = TABLE_SCHEMAS[table_type]
    result = {}

    for field, spec in schema.items():
        if field in record and record[field] is not None:
            result[field] = record[field]
        elif spec["default"] is not None:
            result[field] = spec["default"]
            logger.debug(f"Applied default: {field} = {spec['default']}")
        elif not spec["required"]:
            result[field] = spec["default"]  # None for optional with no default
        else:
            result[field] = record.get(field)  # Keep None — validator will catch it

    return result


# ─── Full Record Cleaning ─────────────────────────────────────────────────────

def clean_transaction(record: dict) -> dict:
    """Clean and normalize a transaction record."""
    record["date"] = standardize_date(record.get("date"))
    record["amount"] = normalize_amount(record.get("amount"))
    record["type"] = str(record.get("type", "expense")).lower().strip()
    record["amount"] = ensure_expense_negative(record["amount"], record["type"])
    record["category"] = map_category(record.get("category"))
    record["is_duplicate"] = normalize_bool(record.get("is_duplicate", False))
    record["description"] = str(record.get("description", "")).strip()
    return record


def clean_obligation(record: dict) -> dict:
    """Clean and normalize an obligation record."""
    record["due_date"] = standardize_date(record.get("due_date"))
    record["amount"] = normalize_amount(record.get("amount"))
    record["amount"] = abs(record["amount"])  # obligations are always positive
    record["category"] = map_category(record.get("category"))
    record["is_critical"] = normalize_bool(record.get("is_critical", False))
    record["recurring_payment"] = normalize_bool(record.get("recurring_payment", False))
    record["flexibility_score"] = float(record.get("flexibility_score", 0.5))
    record["late_fee"] = float(record.get("late_fee", 0))
    record["grace_days"] = int(record.get("grace_days", 0))
    record["vendor"] = str(record.get("vendor", "")).strip()
    record["description"] = str(record.get("description", "")).strip()
    if record.get("relationship_tier"):
        record["relationship_tier"] = str(record["relationship_tier"]).lower().strip()
    return record


def clean_receivable(record: dict) -> dict:
    """Clean and normalize a receivable record."""
    record["expected_date"] = standardize_date(record.get("expected_date"))
    record["amount"] = normalize_amount(record.get("amount"))
    record["amount"] = abs(record["amount"])  # receivables are always positive
    record["category"] = map_category(record.get("category"))
    record["probability"] = float(record.get("probability", 0.9))
    record["recurring_payment"] = normalize_bool(record.get("recurring_payment", False))
    record["client"] = str(record.get("client", "")).strip()
    record["description"] = str(record.get("description", "")).strip()

    # Compute is_overdue
    try:
        expected = datetime.strptime(record["expected_date"], "%Y-%m-%d").date()
        record["is_overdue"] = expected < date.today()
    except (ValueError, KeyError):
        record["is_overdue"] = False

    if record.get("client_tier"):
        record["client_tier"] = str(record["client_tier"]).lower().strip()
    return record


CLEANERS = {
    "transactions": clean_transaction,
    "obligations":  clean_obligation,
    "receivables":  clean_receivable,
}
