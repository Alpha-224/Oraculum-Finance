"""
parsers.py — Format detection and file parsing.
Deterministic for CSV/JSON, Gemini API fallback for unstructured TXT.
"""

import csv
import json
import re
import os
from config import SUPPORTED_EXTENSIONS, logger


# ─── Format Detection ─────────────────────────────────────────────────────────

def detect_format(filepath: str) -> str:
    """
    Detect file format from extension + content signature.
    Returns: 'csv', 'json', 'txt', or raises ValueError.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # Content-based verification
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(1024)

    if ext == ".json":
        sample_stripped = sample.strip()
        if sample_stripped.startswith(("{", "[")):
            return "json"
        logger.warning(f"File has .json extension but doesn't look like JSON. "
                       f"Treating as TXT.")
        return "txt"

    if ext == ".csv":
        # Quick check for comma/tab-separated structure
        if "," in sample or "\t" in sample:
            return "csv"
        logger.warning(f"File has .csv extension but doesn't look comma-separated. "
                       f"Attempting CSV parse anyway.")
        return "csv"

    if ext in (".png", ".jpg", ".jpeg"):
        return "image"

    return "txt"


# ─── CSV Parser (Deterministic — 100% accuracy) ──────────────────────────────

def parse_csv(filepath: str) -> list:
    """
    Parse a CSV file into a list of dicts.
    Auto-detects headers. Ignores extra/unknown columns.
    """
    records = []
    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)

        # Clean header names: lowercase, strip whitespace
        if reader.fieldnames:
            reader.fieldnames = [h.strip().lower().replace(" ", "_")
                                for h in reader.fieldnames]

        for i, row in enumerate(reader):
            # Strip all values
            cleaned_row = {k.strip(): v.strip() if v else v
                          for k, v in row.items() if k}
            if any(v for v in cleaned_row.values()):  # skip completely empty rows
                records.append(cleaned_row)

    logger.info(f"  CSV parsed: {len(records)} rows from {os.path.basename(filepath)}")
    return records


# ─── JSON Parser (Deterministic — 100% accuracy) ─────────────────────────────

def parse_json(filepath: str) -> list:
    """
    Parse a JSON file into a list of dicts.
    Handles: single object, array of objects, or wrapped in a key.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # If it's already a list of dicts, return directly
    if isinstance(data, list):
        records = [r for r in data if isinstance(r, dict)]
        logger.info(f"  JSON parsed: {len(records)} records from "
                    f"{os.path.basename(filepath)}")
        return records

    # If it's a single dict, could be a single record or a wrapper
    if isinstance(data, dict):
        # Check if it looks like a master JSON (has 'transactions', etc.)
        for key in ("transactions", "obligations", "receivables"):
            if key in data and isinstance(data[key], list):
                logger.info(f"  JSON parsed: master format detected, "
                            f"extracting '{key}'")
                return data[key]

        # Assume it's a single record
        logger.info(f"  JSON parsed: 1 record from {os.path.basename(filepath)}")
        return [data]

    raise ValueError(f"Unexpected JSON structure in {filepath}")


# ─── TXT Parser — Gemini API (with regex fallback) ───────────────────────────

GEMINI_EXTRACTION_PROMPT = """You are a financial data extraction assistant. Extract ALL financial records from this text.

For each record found, determine if it's a transaction (past), obligation (owed), or receivable (owed to you).

Return a JSON object with three arrays:
{{
  "transactions": [
    {{"date": "YYYY-MM-DD", "description": "...", "amount": 0.00, "type": "income|expense"}}
  ],
  "obligations": [
    {{"vendor": "...", "description": "...", "amount": 0.00, "due_date": "YYYY-MM-DD", "is_critical": false, "category": "other"}}
  ],
  "receivables": [
    {{"client": "...", "description": "...", "amount": 0.00, "expected_date": "YYYY-MM-DD"}}
  ]
}}

Rules:
- Expenses/payments made = transactions with type "expense" and negative amounts
- Future payments owed = obligations with positive amounts
- Expected incoming payments = receivables with positive amounts
- Dates should be YYYY-MM-DD format
- If year is not specified, use {current_year}
- Amount should be a number (no $ signs)

TEXT TO EXTRACT FROM:
{text}"""


def parse_txt_gemini(filepath: str, api_key: str = None) -> dict:
    """
    Use Gemini API to extract financial data from unstructured text.

    Returns dict with keys: 'transactions', 'obligations', 'receivables'
    (each a list of dicts).
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read().strip()

    if not text:
        logger.warning(f"Empty file: {filepath}")
        return {"transactions": [], "obligations": [], "receivables": []}

    # Try Gemini API
    api_key = api_key or os.environ.get("GEMINI_API_KEY")

    if api_key:
        try:
            result = _call_gemini(text, api_key)
            if result:
                logger.info(f"  Gemini extraction successful from "
                            f"{os.path.basename(filepath)}")
                return result
        except Exception as e:
            logger.warning(f"  Gemini API failed: {e}. Falling back to regex.")

    # Fallback to regex extraction
    logger.info(f"  Using regex fallback for {os.path.basename(filepath)}")
    return parse_txt_regex_fallback(filepath)


def _call_gemini(text: str, api_key: str) -> dict:
    """Call Gemini API for structured extraction."""
    import urllib.request
    import urllib.error
    from datetime import datetime

    current_year = datetime.now().year
    prompt = GEMINI_EXTRACTION_PROMPT.format(
        text=text, current_year=current_year
    )

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"gemini-2.0-flash:generateContent?key={api_key}")

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        }
    })

    req = urllib.request.Request(
        url,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            response = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Gemini API HTTP {e.code}: {e.read().decode()}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Gemini API connection failed: {e}")

    # Extract JSON from response
    try:
        content = response["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(content)
        return {
            "transactions": parsed.get("transactions", []),
            "obligations":  parsed.get("obligations", []),
            "receivables":  parsed.get("receivables", []),
        }
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to parse Gemini response: {e}")


# ─── TXT Regex Fallback (low confidence) ─────────────────────────────────────

def parse_txt_regex_fallback(filepath: str) -> dict:
    """
    Basic regex extraction for structured-ish text.
    Extracts amounts and dates, creates 'low confidence' records.
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    from datetime import datetime
    current_year = datetime.now().year

    results = {
        "transactions": [],
        "obligations": [],
        "receivables": [],
    }

    # Pattern: look for lines with amounts ($X,XXX.XX or XXXX.XX)
    amount_pattern = re.compile(
        r'(?:paid|owe|owed|expecting|received|pay|due|invoice)\s+.*?'
        r'\$?([\d,]+\.?\d*)',
        re.IGNORECASE
    )

    # Date patterns
    date_patterns = [
        (re.compile(r'(\w+ \d{1,2}(?:st|nd|rd|th)?)'), '%B %d'),
        (re.compile(r'(\d{1,2}/\d{1,2}/\d{2,4})'), None),
        (re.compile(r'(\d{4}-\d{2}-\d{2})'), '%Y-%m-%d'),
    ]

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Find amount
        amount_match = amount_pattern.search(line)
        if not amount_match:
            continue

        amount = float(amount_match.group(1).replace(',', ''))

        # Find date
        found_date = None
        for pattern, fmt in date_patterns:
            date_match = pattern.search(line)
            if date_match:
                date_str = re.sub(r'(st|nd|rd|th)', '', date_match.group(1))
                try:
                    if fmt:
                        parsed = datetime.strptime(date_str.strip(), fmt)
                        parsed = parsed.replace(year=current_year)
                        found_date = parsed.strftime('%Y-%m-%d')
                    else:
                        found_date = date_str
                except ValueError:
                    continue
                break

        if not found_date:
            found_date = datetime.now().strftime('%Y-%m-%d')

        # Classify the record
        line_lower = line.lower()
        if any(w in line_lower for w in ('paid', 'bought', 'purchased', 'spent')):
            results["transactions"].append({
                "date": found_date,
                "description": line[:100],
                "amount": -amount,
                "type": "expense",
                "confidence": "low",
            })
        elif any(w in line_lower for w in ('owe', 'need to pay', 'due', 'pay')):
            results["obligations"].append({
                "vendor": _extract_entity(line),
                "description": line[:100],
                "amount": amount,
                "due_date": found_date,
                "is_critical": False,
                "category": "other",
                "confidence": "low",
            })
        elif any(w in line_lower for w in ('expecting', 'owed', 'receivable', 'incoming')):
            results["receivables"].append({
                "client": _extract_entity(line),
                "description": line[:100],
                "amount": amount,
                "expected_date": found_date,
                "confidence": "low",
            })
        else:
            # Default: treat as expense transaction
            results["transactions"].append({
                "date": found_date,
                "description": line[:100],
                "amount": -amount,
                "type": "expense",
                "confidence": "low",
            })

    total = sum(len(v) for v in results.values())
    logger.info(f"  Regex fallback extracted {total} records from "
                f"{os.path.basename(filepath)}")
    return results


def _extract_entity(text: str) -> str:
    """Try to extract a vendor/client name from text."""
    # Look for capitalized words (likely entity names)
    words = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text)
    # Filter out common non-entity words
    stop_words = {"Paid", "Need", "Also", "Expecting", "March", "April",
                  "May", "June", "January", "February", "July", "August",
                  "September", "October", "November", "December", "Monday",
                  "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
    entities = [w for w in words if w not in stop_words and len(w) > 2]
    return entities[0] if entities else "Unknown"
