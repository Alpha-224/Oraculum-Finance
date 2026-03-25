"""
config.py — Constants, schemas, defaults, and category taxonomy.
Single source of truth for all data ingestion configuration.
"""

import os
import logging

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_JSON_PATH = os.path.join(BASE_DIR, "master_financial_data.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")
SAMPLE_DATA_DIR = os.path.join(BASE_DIR, "sample_data")

# ─── Logging ──────────────────────────────────────────────────────────────────
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "ingestion.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("oraculum")

# ─── Supported Formats ───────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".csv", ".json", ".txt", ".png", ".jpg", ".jpeg"}

# ─── Standard Category Taxonomy ──────────────────────────────────────────────
VALID_CATEGORIES = {
    "inventory", "rent", "utilities", "sales", "catering",
    "subscription", "other", "uncategorized",
}

# ─── Date Formats (tried in order) ───────────────────────────────────────────
DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%B %d, %Y",      # March 25, 2024
    "%b %d, %Y",      # Mar 25, 2024
    "%d %B %Y",        # 25 March 2024
    "%d %b %Y",        # 25 Mar 2024
]

# ─── Transaction Types ───────────────────────────────────────────────────────
VALID_TXN_TYPES = {"income", "expense", "transfer", "starting"}

# ─── Periodicity Values ──────────────────────────────────────────────────────
VALID_PERIODICITIES = {"daily", "weekly", "monthly"}

# ─── Relationship / Client Tiers ──────────────────────────────────────────────
VALID_TIERS = {"critical", "standard", "minor"}

# ─── Table Schemas ────────────────────────────────────────────────────────────
# (field_name, type, required, default_value_or_None)

TRANSACTION_SCHEMA = {
    "transaction_id":   {"type": "str",   "required": True,  "default": None},
    "date":             {"type": "date",  "required": True,  "default": None},
    "description":      {"type": "str",   "required": True,  "default": None},
    "amount":           {"type": "float", "required": True,  "default": None},
    "type":             {"type": "str",   "required": True,  "default": None},
    "running_balance":  {"type": "float", "required": False, "default": 0.0},
    "source":           {"type": "str",   "required": True,  "default": None},
    "category":         {"type": "str",   "required": False, "default": "uncategorized"},
    "is_duplicate":     {"type": "bool",  "required": True,  "default": False},
}

OBLIGATION_SCHEMA = {
    "obligation_id":    {"type": "str",   "required": True,  "default": None},
    "vendor":           {"type": "str",   "required": True,  "default": None},
    "description":      {"type": "str",   "required": True,  "default": None},
    "amount":           {"type": "float", "required": True,  "default": None},
    "due_date":         {"type": "date",  "required": True,  "default": None},
    "invoice_id":       {"type": "str",   "required": False, "default": ""},
    "category":         {"type": "str",   "required": True,  "default": "other"},
    "is_critical":      {"type": "bool",  "required": True,  "default": False},
    "late_fee":         {"type": "float", "required": False, "default": 0.0},
    "grace_days":       {"type": "int",   "required": False, "default": 0},
    "flexibility_score":{"type": "float", "required": False, "default": 0.5},
    "relationship_tier":{"type": "str",   "required": False, "default": "standard"},
    "recurring_payment":{"type": "bool",  "required": True,  "default": False},
    "periodicity":      {"type": "str",   "required": False, "default": None},
    "source":           {"type": "str",   "required": False, "default": "manual_entry"},
}

RECEIVABLE_SCHEMA = {
    "receivable_id":    {"type": "str",   "required": True,  "default": None},
    "client":           {"type": "str",   "required": True,  "default": None},
    "description":      {"type": "str",   "required": True,  "default": None},
    "amount":           {"type": "float", "required": True,  "default": None},
    "expected_date":    {"type": "date",  "required": True,  "default": None},
    "invoice_id":       {"type": "str",   "required": False, "default": ""},
    "category":         {"type": "str",   "required": False, "default": "other"},
    "probability":      {"type": "float", "required": True,  "default": 0.9},
    "client_tier":      {"type": "str",   "required": False, "default": "standard"},
    "payment_terms":    {"type": "str",   "required": False, "default": "Net 30"},
    "is_overdue":       {"type": "bool",  "required": True,  "default": False},
    "recurring_payment":{"type": "bool",  "required": True,  "default": False},
    "periodicity":      {"type": "str",   "required": False, "default": None},
    "source":           {"type": "str",   "required": False, "default": "manual_entry"},
}

TABLE_SCHEMAS = {
    "transactions": TRANSACTION_SCHEMA,
    "obligations":  OBLIGATION_SCHEMA,
    "receivables":  RECEIVABLE_SCHEMA,
}

# ─── ID Prefixes ─────────────────────────────────────────────────────────────
ID_PREFIXES = {
    "transactions": "txn",
    "obligations":  "obl",
    "receivables":  "rec",
}

# ─── Master JSON Skeleton ────────────────────────────────────────────────────
def empty_master():
    """Return a fresh master JSON skeleton."""
    return {
        "metadata": {
            "created_at": None,
            "last_updated": None,
            "source_files": [],
            "record_counts": {
                "transactions": 0,
                "obligations": 0,
                "receivables": 0,
            },
        },
        "transactions": [],
        "obligations": [],
        "receivables": [],
    }
