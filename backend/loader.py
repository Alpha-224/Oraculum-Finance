"""
loader.py — Loads master_financial_data.json from the data_layer directory.

The backend is READ-ONLY for the ledger. This module never writes to the file.
"""

import json
from pathlib import Path

from .config import logger

# Path resolves from repo root — not from /backend/
MASTER_JSON_PATH: Path = Path(__file__).parent.parent / "data_layer" / "master_financial_data.json"


def load_master_json(path: str | None = None) -> dict:
    """Loads and returns the master financial JSON as a Python dict.

    Args:
        path: Optional override path to a JSON file. If None, uses the
              default MASTER_JSON_PATH resolved from the repo root.

    Returns:
        The parsed JSON as a dict with keys: metadata, transactions,
        obligations, receivables.

    Raises:
        FileNotFoundError: If the file is absent.
        json.JSONDecodeError: If the file is corrupt.
    """
    target = Path(path) if path else MASTER_JSON_PATH
    logger.info(f"Loading master JSON from: {target.resolve()}")

    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(
        f"Loaded: {len(data.get('transactions', []))} transactions, "
        f"{len(data.get('obligations', []))} obligations, "
        f"{len(data.get('receivables', []))} receivables"
    )
    return data
