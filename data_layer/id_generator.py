"""
id_generator.py — Self-generating unique IDs.
Format: {prefix}_{YYYYMMDD}_{uuid4[:8]}
No external DB dependency.
"""

import uuid
from config import ID_PREFIXES


def generate_id(table_type: str, date_str: str) -> str:
    """
    Generate a unique ID for a record.

    Args:
        table_type: 'transactions', 'obligations', or 'receivables'
        date_str:   Date in YYYY-MM-DD format (already cleaned)

    Returns:
        e.g. 'txn_20240325_a3f2b1c9'
    """
    prefix = ID_PREFIXES[table_type]
    date_compact = date_str.replace("-", "")
    uid = uuid.uuid4().hex[:8]
    return f"{prefix}_{date_compact}_{uid}"
