"""
validators.py — Validation, duplicate detection, and data type checks.
"""

import hashlib
from config import TABLE_SCHEMAS, VALID_TXN_TYPES, VALID_TIERS, VALID_PERIODICITIES, logger


# ─── Required Field Validation ───────────────────────────────────────────────

def validate_required_fields(record: dict, table_type: str) -> list:
    """
    Check that all required fields are present and non-empty.
    Returns list of error messages (empty = valid).
    """
    schema = TABLE_SCHEMAS[table_type]
    errors = []

    for field, spec in schema.items():
        # Skip auto-generated fields
        if field in ("transaction_id", "obligation_id", "receivable_id",
                      "running_balance", "is_duplicate", "is_overdue"):
            continue

        if spec["required"] and spec["default"] is None:
            val = record.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append(f"Missing required field: '{field}'")

    # Conditional: periodicity required if recurring_payment is True
    if record.get("recurring_payment") and not record.get("periodicity"):
        errors.append("'periodicity' is required when 'recurring_payment' is True")

    return errors


# ─── Data Type Validation ────────────────────────────────────────────────────

def validate_data_types(record: dict, table_type: str) -> list:
    """
    Validate data types match schema expectations.
    Returns list of error messages (empty = valid).
    """
    errors = []

    # Amount must be numeric
    amount_field = "amount"
    if amount_field in record:
        try:
            float(record[amount_field])
        except (ValueError, TypeError):
            errors.append(f"'{amount_field}' must be numeric, got: {record[amount_field]}")

    # Transaction type validation
    if table_type == "transactions" and "type" in record:
        if record["type"] not in VALID_TXN_TYPES:
            errors.append(
                f"Invalid transaction type '{record['type']}'. "
                f"Must be one of: {VALID_TXN_TYPES}"
            )

    # Tier validation
    for tier_field in ("relationship_tier", "client_tier"):
        if tier_field in record and record[tier_field] is not None:
            if record[tier_field] not in VALID_TIERS:
                errors.append(
                    f"Invalid tier '{record[tier_field]}'. Must be one of: {VALID_TIERS}"
                )

    # Periodicity validation
    if "periodicity" in record and record["periodicity"] is not None:
        if record["periodicity"] not in VALID_PERIODICITIES:
            errors.append(
                f"Invalid periodicity '{record['periodicity']}'. "
                f"Must be one of: {VALID_PERIODICITIES}"
            )

    # Probability range
    if "probability" in record and record["probability"] is not None:
        try:
            prob = float(record["probability"])
            if not 0.0 <= prob <= 1.0:
                errors.append(f"'probability' must be 0.0–1.0, got: {prob}")
        except (ValueError, TypeError):
            errors.append(f"'probability' must be numeric, got: {record['probability']}")

    # Flexibility score range
    if "flexibility_score" in record and record["flexibility_score"] is not None:
        try:
            flex = float(record["flexibility_score"])
            if not 0.0 <= flex <= 1.0:
                errors.append(f"'flexibility_score' must be 0.0–1.0, got: {flex}")
        except (ValueError, TypeError):
            errors.append(f"'flexibility_score' must be numeric")

    return errors


# ─── Duplicate Detection ─────────────────────────────────────────────────────

def compute_fingerprint(record: dict, table_type: str) -> str:
    """
    Generate a fingerprint hash for duplicate detection.
    Fingerprint = hash(date + description + amount).
    """
    if table_type == "transactions":
        date_val = record.get("date", "")
    elif table_type == "obligations":
        date_val = record.get("due_date", "")
    else:
        date_val = record.get("expected_date", "")

    desc = str(record.get("description", "")).lower().strip()
    amount = str(record.get("amount", ""))

    composite = f"{date_val}|{desc}|{amount}"
    return hashlib.sha256(composite.encode()).hexdigest()[:16]


def check_duplicate(fingerprint: str, existing_fingerprints: set) -> bool:
    """Check if a fingerprint already exists."""
    return fingerprint in existing_fingerprints


def collect_existing_fingerprints(records: list, table_type: str) -> set:
    """Build a set of fingerprints from existing records."""
    fps = set()
    for record in records:
        fp = compute_fingerprint(record, table_type)
        fps.add(fp)
    return fps


# ─── Full Validation Pipeline ─────────────────────────────────────────────────

def validate_record(record: dict, table_type: str) -> list:
    """
    Run all validations on a record.
    Returns list of error messages (empty = valid).
    """
    errors = []
    errors.extend(validate_required_fields(record, table_type))
    errors.extend(validate_data_types(record, table_type))
    return errors
