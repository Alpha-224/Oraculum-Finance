# Oraculum Data Ingestion Module — Developer Documentation

**CashFlow Guardian — Financial GPS for Small Vendors**
**Module:** Oraculum Core Input Pipeline • **Version:** 2.0 • **Last Updated:** 2026-03-25

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture & Data Flow](#2-architecture--data-flow)
3. [File Structure](#3-file-structure)
4. [Master JSON — The Single Source of Truth](#4-master-json--the-single-source-of-truth)
5. [Data Table Schemas (Complete Reference)](#5-data-table-schemas-complete-reference)
6. [Module-by-Module Reference](#6-module-by-module-reference)
7. [Key Conventions & Rules](#7-key-conventions--rules)
8. [How to Add a New Parser (e.g., OCR / PDF)](#8-how-to-add-a-new-parser-eg-ocr--pdf)
9. [Flutter Integration Guide](#9-flutter-integration-guide)
10. [CLI Usage](#10-cli-usage)
11. [Environment & Dependencies](#11-environment--dependencies)
12. [Testing Checklist](#12-testing-checklist)
13. [Known Limitations & Next Steps](#13-known-limitations--next-steps)

---

## 1. Project Overview

### What Has Been Built

A **complete data ingestion pipeline** that accepts financial data from multiple formats (CSV, JSON, TXT, manual entry), normalizes it, validates it, and stores it in a **single master JSON file** — no database required.

### What It Does

```
Raw Input  →  Format Detection  →  Parsing  →  Cleaning  →  Validation  →  Master JSON
(CSV/JSON/     (extension +        (deterministic   (dates,       (required      (append,
 TXT/manual)    content sniff)       or AI-based)     amounts,      fields,        deduplicate,
                                                      categories)   types,         recompute
                                                                    duplicates)    balances)
```

### What Still Needs to Be Done

- **PDF parsing** (tabular PDFs via `pdfplumber`, scanned PDFs via Gemini Vision)
- **Image/OCR processing** (receipt photos, scanned documents)
- Both should **plug into the existing pipeline** — the cleaning, validation, ID generation, and master JSON merge stages are already built and reusable.

---

## 2. Architecture & Data Flow

### Six-Layer Pipeline

| Layer | Name | Module | What It Does |
|-------|------|--------|-------------|
| 1 | **Input** | `data_ingestion.py` | Accepts files via CLI or function calls from Flutter |
| 2 | **Format Detection** | `parsers.py` → `detect_format()` | Reads extension + content signature, routes to correct parser |
| 3 | **Parsing** | `parsers.py` | Converts raw file into `list[dict]` — one dict per record |
| 4 | **Cleaning** | `cleaners.py` | Standardizes dates, amounts, categories, booleans |
| 5 | **Validation** | `validators.py` | Checks required fields, data types, generates duplicate fingerprints |
| 6 | **Storage** | `master_json.py` | Merges validated records into `master_financial_data.json` |

### Parser Selection Logic (Current + Planned)

| File Type | Parser | Accuracy | Gemini API? | Status |
|-----------|--------|----------|-------------|--------|
| CSV | Deterministic (`parse_csv`) | 100% | Never | ✅ Done |
| JSON | Deterministic (`parse_json`) | 100% | Never | ✅ Done |
| TXT (messy) | Gemini API + regex fallback | ~90% | Yes (with fallback) | ✅ Done |
| Manual Entry | Direct function call | 100% | Never | ✅ Done |
| **PDF (tabular)** | **Hybrid (regex + pdfplumber)** | **~80%** | **Fallback only** | ⬜ TODO |
| **Image/PDF (scanned)** | **Gemini Vision API** | **~85%** | **Always** | ⬜ TODO |

### Data Flow Diagram

```
                    ┌──────────────┐
                    │   CLI / API   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ detect_format │  ← parsers.py
                    └──────┬───────┘
                           │
          ┌────────┬───────┼───────┬──────────┐
          ▼        ▼       ▼       ▼          ▼
      parse_csv  parse_  parse_   [NEW]     [NEW]
                 json    txt_     parse_    parse_
                         gemini   pdf       image
          │        │       │       │          │
          └────────┴───────┴───────┴──────────┘
                           │
                    ┌──────▼───────┐
                    │   cleaner()   │  ← cleaners.py (per table type)
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  validate()   │  ← validators.py
                    │  generate_id  │  ← id_generator.py
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ merge_records │  ← master_json.py
                    │ + balance     │  ← balance.py (transactions only)
                    └──────┬───────┘
                           │
                    ┌──────▼───────────────┐
                    │ master_financial_data │
                    │       .json          │
                    └──────────────────────┘
```

---

## 3. File Structure

```
data_layer/
├── __init__.py                 # Package init
├── config.py                   # ⭐ ALL schemas, constants, defaults — start here
├── id_generator.py             # ID generation: txn_YYYYMMDD_uuid4[:8]
├── cleaners.py                 # Date/amount/category/boolean normalization
├── validators.py               # Required field checks, type validation, dedup
├── parsers.py                  # CSV, JSON, TXT parsers + Gemini integration
├── balance.py                  # Running balance computation
├── master_json.py              # Load/save/merge for master JSON
├── manual_entry.py             # 3 API functions for Flutter
├── data_ingestion.py           # CLI entrypoint (argparse)
├── master_financial_data.json  # ⭐ Generated output — THE source of truth
├── README.md                   # Quick-start guide
├── DEVELOPER_DOCS.md           # This file
├── logs/
│   └── ingestion.log           # Auto-generated log file
└── sample_data/
    ├── sample_transactions.csv # 5 rows: 1 starting balance + 4 transactions
    ├── sample_obligations.csv  # 3 rows: vendor obligations
    ├── sample_note.txt         # Unstructured text (Gemini/regex test)
    └── sample_receivables.json # 2 JSON receivables (with recurring flags)
```

### Repo Territories (from `repo-instructions.md`)

| Team | Directory | Notes |
|------|-----------|-------|
| **Data Team** | `/data_layer` | All ingestion code lives here |
| **Backend/Logic** | `/backend` | Consumes `master_financial_data.json` |
| **Frontend** | `/frontend/lib` | Flutter app, calls manual entry APIs |

> **Rule:** Never push directly to `main`. Use `feature/feature-name` branches.

---

## 4. Master JSON — The Single Source of Truth

There is **no database**. Everything is stored in a single file: `master_financial_data.json`.

### Structure

```json
{
  "metadata": {
    "created_at": "2026-03-25T17:09:03Z",
    "last_updated": "2026-03-25T17:13:28Z",
    "source_files": ["sample_transactions.csv", "sample_note.txt"],
    "record_counts": {
      "transactions": 7,
      "obligations": 4,
      "receivables": 3
    }
  },
  "transactions": [ ... ],
  "obligations":  [ ... ],
  "receivables":  [ ... ]
}
```

### Critical Rules for Master JSON

| Rule | Detail |
|------|--------|
| **Append only** | New records are appended. Updates/edits are **NOT** supported — re-ingest to correct. |
| **Duplicate skip** | If a record's fingerprint (`hash(date + description + amount)`) matches an existing one, it is silently skipped. |
| **Source tracking** | Every source file name is tracked in `metadata.source_files[]`. |
| **Atomic writes** | The file is written to a `.tmp` first, then renamed — prevents corruption on crash. |
| **Balance recompute** | Every time transactions are modified, `running_balance` is recalculated from scratch. |
| **No foreign keys** | Each record is self-contained. No joins, no references between tables. Flutter can read and render directly. |

---

## 5. Data Table Schemas (Complete Reference)

### Table 1 — `transactions`

Records of money that has **already moved**.

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `transaction_id` | string | Yes | Auto-generated | Format: `txn_YYYYMMDD_uuid4[:8]` |
| `date` | string | Yes | — | Always `YYYY-MM-DD` |
| `description` | string | Yes | — | Raw description text |
| `amount` | float | Yes | — | **+income / −expense** |
| `type` | string | Yes | — | `income` / `expense` / `transfer` / `starting` |
| `running_balance` | float | No | 0.0 | **Computed, never trusted from input** |
| `source` | string | Yes | — | Filename or `"manual_entry"` |
| `category` | string | No | `"uncategorized"` | From standard taxonomy |
| `is_duplicate` | bool | Yes | `false` | Computed at merge |

### Table 2 — `obligations`

Upcoming payments the business **owes**.

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `obligation_id` | string | Yes | Auto-generated | Format: `obl_YYYYMMDD_uuid4[:8]` |
| `vendor` | string | Yes | — | Who you owe |
| `description` | string | Yes | — | Payment purpose |
| `amount` | float | Yes | — | **Always positive** |
| `due_date` | string | Yes | — | `YYYY-MM-DD` |
| `invoice_id` | string | No | `""` | Reference number |
| `category` | string | Yes | `"other"` | Standard taxonomy |
| `is_critical` | bool | Yes | `false` | Business halts if unpaid |
| `late_fee` | float | No | `0.0` | Penalty if late |
| `grace_days` | int | No | `0` | Days before penalty |
| `flexibility_score` | float | No | `0.5` | 0–1 negotiability |
| `relationship_tier` | string | No | `"standard"` | `critical` / `standard` / `minor` |
| `recurring_payment` | bool | Yes | `false` | Auto-repeating |
| `periodicity` | string | Conditional | `null` | Required if `recurring_payment=true`. Values: `daily` / `weekly` / `monthly` |
| `source` | string | No | `"manual_entry"` | Origin |

### Table 3 — `receivables`

Expected **incoming** payments.

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `receivable_id` | string | Yes | Auto-generated | Format: `rec_YYYYMMDD_uuid4[:8]` |
| `client` | string | Yes | — | Who owes you |
| `description` | string | Yes | — | Payment purpose |
| `amount` | float | Yes | — | **Always positive** |
| `expected_date` | string | Yes | — | `YYYY-MM-DD` |
| `invoice_id` | string | No | `""` | Your invoice number |
| `category` | string | No | `"other"` | Standard taxonomy |
| `probability` | float | Yes | `0.9` | 0–1 on-time likelihood |
| `client_tier` | string | No | `"standard"` | `critical` / `standard` / `minor` |
| `payment_terms` | string | No | `"Net 30"` | Net 30, Net 15, etc. |
| `is_overdue` | bool | Yes | `false` | **Computed**: `expected_date < today` |
| `recurring_payment` | bool | Yes | `false` | Auto-repeating |
| `periodicity` | string | Conditional | `null` | Required if `recurring_payment=true` |
| `source` | string | No | `"manual_entry"` | Origin |

### Standard Category Taxonomy

All categories must be one of:
```
inventory | rent | utilities | sales | catering | subscription | other | uncategorized
```

`cleaners.py` has a fuzzy synonym mapper (e.g., `"food"` → `"catering"`, `"electric"` → `"utilities"`). If adding new categories, update **both** `VALID_CATEGORIES` in `config.py` and the synonym map in `cleaners.py`.

---

## 6. Module-by-Module Reference

### `config.py` — Start Here

**The single source of truth for all configuration.** Any new parser or feature should read its constants from here.

Key exports:
- `MASTER_JSON_PATH` — where the master JSON lives
- `SUPPORTED_EXTENSIONS` — add `.pdf`, `.png`, `.jpg` here when implementing OCR
- `TABLE_SCHEMAS` — dict of all three schemas with type/required/default info
- `ID_PREFIXES` — `{"transactions": "txn", "obligations": "obl", "receivables": "rec"}`
- `logger` — configured logger, use `from config import logger` everywhere
- `empty_master()` — returns a blank master JSON skeleton

### `id_generator.py`

```python
generate_id("transactions", "2024-03-25")  # → "txn_20240325_a3f2b1c9"
generate_id("obligations", "2024-04-01")   # → "obl_20240401_d4e5f6a7"
generate_id("receivables", "2024-03-22")   # → "rec_20240322_b8c9d0e1"
```

Uses `uuid4().hex[:8]` — globally unique, no DB needed.

### `cleaners.py`

Functions you'll reuse for any new parser:
- `standardize_date(raw)` → `"YYYY-MM-DD"` — handles 10+ formats including natural language
- `normalize_amount(raw)` → `float` — strips `$`, commas, spaces
- `ensure_expense_negative(amount, type)` → ensures sign matches type
- `map_category(raw)` → standard taxonomy string
- `normalize_bool(raw)` → handles `true/false/yes/no/1/0/True/False`
- `apply_defaults(record, table_type)` → fills missing optional fields from schema defaults
- `clean_transaction(record)` / `clean_obligation(record)` / `clean_receivable(record)` — full per-table cleaning
- `CLEANERS` dict — maps `"transactions"` → `clean_transaction`, etc.

### `validators.py`

- `validate_required_fields(record, table_type)` → list of error strings
- `validate_data_types(record, table_type)` → checks amounts, types, ranges
- `compute_fingerprint(record, table_type)` → `sha256(date|description|amount)[:16]`
- `check_duplicate(fingerprint, existing_set)` → bool
- `collect_existing_fingerprints(records, table_type)` → set of fingerprints
- `validate_record(record, table_type)` → runs all validations, returns error list

### `parsers.py`

- `detect_format(filepath)` → `"csv"` / `"json"` / `"txt"`
- `parse_csv(filepath)` → `list[dict]`
- `parse_json(filepath)` → `list[dict]`
- `parse_txt_gemini(filepath, api_key)` → `{"transactions": [...], "obligations": [...], "receivables": [...]}`
- `parse_txt_regex_fallback(filepath)` → same structure, `"confidence": "low"` flag

**This is where you add `parse_pdf()` and `parse_image()`.**

### `balance.py`

```python
compute_running_balances(transactions_list)  # sorts by date, recalculates all balances
```

Rules:
1. Sort by date ascending
2. If first record is `type="starting"`, its `amount` is the starting balance
3. Each subsequent: `running_balance = previous_balance + amount`
4. **Always overwrites** any `running_balance` from input — it is never trusted

### `master_json.py`

- `load_master(path=None)` → loads existing JSON or returns empty skeleton
- `save_master(data, path=None)` → atomic write (tmp + rename)
- `merge_records(master, new_records, table_type, source_file)` → dedup + append + recompute balances

### `manual_entry.py`

Three functions exposed for the Flutter frontend:

```python
add_manual_transaction(date, description, amount, txn_type, category=None)
add_manual_obligation(vendor, description, amount, due_date, is_critical=False, ...)
add_manual_receivable(client, description, amount, expected_date, probability=0.9, ...)
```

Each returns: `{"success": bool, "record": dict|None, "errors": list}`

---

## 7. Key Conventions & Rules

### Naming & Style
- All field names: **snake_case**
- All dates: **YYYY-MM-DD** strings (never datetime objects in JSON)
- All amounts: **float** (expenses negative, income/obligations/receivables positive)
- All IDs: `{prefix}_{YYYYMMDD}_{uuid4hex[:8]}`
- Logging: always use `from config import logger`
- No function should exceed ~50 lines

### Data Integrity Rules
- **Running balance** is ALWAYS computed, never trusted from input
- **`is_duplicate`** is computed via fingerprint at merge time
- **`is_overdue`** (receivables) is computed by comparing `expected_date < today`
- **Expenses** are always negative amounts; the cleaner enforces this
- **Obligations and receivables** amounts are always positive (absolute value enforced)

### Error Handling Pattern
Every function follows this pattern:
```python
try:
    # clean → validate → process
    errors = validate_record(record, table_type)
    if errors:
        return {"success": False, "errors": errors}
    # ... proceed
except Exception as e:
    logger.error(f"Context: {e}")
    return {"success": False, "errors": [str(e)]}
```

### Merge Strategy
| Operation | Behavior |
|-----------|----------|
| New record | Append to array |
| Duplicate | Skip silently (fingerprint match) |
| Update | **NOT supported** — re-ingest to correct |
| Source tracking | Add filename to `metadata.source_files[]` |

---

## 8. How to Add a New Parser (e.g., OCR / PDF)

This is the **recommended procedure** for the next developer adding PDF/Image support.

### Step 1: Update `config.py`

```python
# Add to SUPPORTED_EXTENSIONS
SUPPORTED_EXTENSIONS = {".csv", ".json", ".txt", ".pdf", ".png", ".jpg", ".jpeg"}
```

### Step 2: Add Parser Function in `parsers.py`

Your parser must return **the same format** as existing parsers:

**Option A (for single-type files like a bank statement PDF):**
Return `list[dict]` — each dict is one record matching the table schema.

```python
def parse_pdf(filepath: str) -> list:
    """
    Parse a tabular PDF into a list of dicts.
    Uses pdfplumber for table extraction, Gemini Vision as fallback.
    """
    # 1. Try pdfplumber first (deterministic)
    # 2. If table extraction fails, try Gemini Vision API
    # 3. Return list of dicts with at minimum: date, description, amount
    records = []
    # ... your extraction logic ...
    return records
```

**Option B (for mixed-type files like a scanned document with both expenses and receivables):**
Return `dict` with three keys, same as `parse_txt_gemini`:

```python
def parse_image(filepath: str) -> dict:
    """Parse scanned document via Gemini Vision."""
    return {
        "transactions": [...],
        "obligations": [...],
        "receivables": [...],
    }
```

### Step 3: Update Format Detection

In `parsers.py`, update `detect_format()`:

```python
if ext in (".pdf",):
    return "pdf"
if ext in (".png", ".jpg", ".jpeg"):
    return "image"
```

### Step 4: Wire Into the Pipeline

In `data_ingestion.py`, add handling in `process_file()`:

```python
elif fmt == "pdf":
    raw_records = parse_pdf(filepath)
    _process_records(raw_records, table_type, os.path.basename(filepath))

elif fmt == "image":
    parsed = parse_image(filepath)
    # Same mixed-type handling as TXT
    for ttype in ("transactions", "obligations", "receivables"):
        records = parsed.get(ttype, [])
        if records:
            _process_records(records, ttype, source)
```

### Step 5: You Get All This For Free

Once your parser returns `list[dict]`, the existing pipeline handles:
- ✅ Cleaning (dates, amounts, categories)
- ✅ Default filling
- ✅ ID generation
- ✅ Validation
- ✅ Duplicate detection
- ✅ Running balance computation (if transactions)
- ✅ Master JSON merge
- ✅ Logging

### Recommended Libraries

| Purpose | Library | Install |
|---------|---------|---------|
| Tabular PDF extraction | `pdfplumber` | `pip install pdfplumber` |
| Scanned PDF/Image OCR | Gemini Vision API | Already integrated (see `_call_gemini` in `parsers.py`) |
| Fallback OCR | `pytesseract` | `pip install pytesseract` (requires Tesseract binary) |
| Image preprocessing | `Pillow` | `pip install Pillow` |

### Gemini Vision API Pattern

Adapt the existing `_call_gemini()` function in `parsers.py`. For images, you need to:
1. Base64-encode the image
2. Send as `inlineData` in the Gemini API payload
3. Use the same structured extraction prompt (already defined as `GEMINI_EXTRACTION_PROMPT`)

```python
import base64

def _call_gemini_vision(image_path: str, api_key: str) -> dict:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    mime = "image/png" if image_path.endswith(".png") else "image/jpeg"

    payload = {
        "contents": [{
            "parts": [
                {"text": GEMINI_EXTRACTION_PROMPT.format(text="[see image]", current_year=2026)},
                {"inlineData": {"mimeType": mime, "data": image_data}}
            ]
        }],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
    }
    # ... same HTTP call pattern as _call_gemini() ...
```

### Adding a `confidence` Field (Optional But Recommended)

For AI-parsed records, add `"confidence": "low"|"medium"|"high"` to each record dict. The cleaners and validators will ignore unknown fields, so this is safe to add without modifying existing code.

---

## 9. Flutter Integration Guide

### For the Frontend Team

The Flutter app communicates with the data layer via **function calls** (if running Python locally) or via **HTTP API** (if wrapped in Flask/FastAPI).

#### Direct Import (Python-side)

```python
from manual_entry import add_manual_transaction, add_manual_obligation, add_manual_receivable

# Returns: {"success": True, "record": {...}, "report": {"added": 1, "skipped": 0}}
result = add_manual_transaction(
    date="2024-03-25",
    description="Coffee purchase",
    amount=-45.00,
    txn_type="expense",
    category="catering"
)
```

#### Reading Data (Flutter-side)

```dart
// Flutter reads master_financial_data.json directly
final file = File('path/to/master_financial_data.json');
final data = jsonDecode(await file.readAsString());

List transactions = data['transactions'];
List obligations  = data['obligations'];
List receivables  = data['receivables'];
```

**No parsing needed** — the JSON schema is designed to be consumed directly.

---

## 10. CLI Usage

```bash
# Process files
python data_ingestion.py process <file> --type <transactions|obligations|receivables>
python data_ingestion.py process sample_data/sample_note.txt   # TXT auto-detects all types

# Manual entry
python data_ingestion.py add-transaction --date 2024-03-10 --description "Payment" --amount -100 --type expense
python data_ingestion.py add-obligation  --vendor "Supplier" --description "Order" --amount 500 --due-date 2024-04-15
python data_ingestion.py add-receivable  --client "Client" --description "Invoice" --amount 2000 --expected-date 2024-04-20

# Validation report
python data_ingestion.py report
```

---

## 11. Environment & Dependencies

### Required
- **Python 3.8+**
- No external pip packages for core functionality (CSV, JSON, TXT regex)

### Optional
- `GEMINI_API_KEY` environment variable — for AI-powered TXT extraction
- `pdfplumber` — for tabular PDF extraction (to be added)
- `Pillow` — for image preprocessing (to be added)

### Setting Gemini API Key

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY = "your_key_here"

# Windows (CMD)
set GEMINI_API_KEY=your_key_here

# Mac/Linux
export GEMINI_API_KEY=your_key_here
```

The Gemini model used is `gemini-2.0-flash` (fast, cost-efficient). Change in `parsers.py` → `_call_gemini()` if needed.

---

## 12. Testing Checklist

Run these commands sequentially from `data_layer/` to verify everything works:

```bash
# 1. Clean start
del master_financial_data.json    # or: rm master_financial_data.json

# 2. Ingest CSV transactions → expect 5 records, correct running balances
python data_ingestion.py process sample_data/sample_transactions.csv --type transactions

# 3. Ingest CSV obligations → expect 3 records
python data_ingestion.py process sample_data/sample_obligations.csv --type obligations

# 4. Ingest JSON receivables → expect 2 records
python data_ingestion.py process sample_data/sample_receivables.json --type receivables

# 5. Ingest TXT (regex fallback) → expect 1-3 records across tables
python data_ingestion.py process sample_data/sample_note.txt

# 6. Duplicate test → re-ingest CSV, expect 0 new records
python data_ingestion.py process sample_data/sample_transactions.csv --type transactions

# 7. Manual entry test
python data_ingestion.py add-transaction --date 2024-03-10 --description "Test" --amount -100 --type expense

# 8. Validation report → should show NO ISSUES FOUND
python data_ingestion.py report
```

### Expected Running Balance Chain (Transactions)

```
Opening Balance  +5000.00  → Balance: 5000.00
Coffee Beans      -850.00  → Balance: 4150.00
Square Payment    +425.00  → Balance: 4575.00
March Rent       -2000.00  → Balance: 2575.00
Catering Payment +1250.00  → Balance: 3825.00
```

---

## 13. Known Limitations & Next Steps

### Current Limitations
- **No PDF/Image support** — parsers for `.pdf`, `.png`, `.jpg` are not yet implemented
- **No automated recurring payment generation** — `recurring_payment` flag is stored, but next instances are not auto-created
- **No update/edit** — records can only be appended, not modified in place
- **No multi-tenant** — single master JSON per instance
- **TXT regex fallback** — works but has low accuracy for ambiguous text; entity extraction (vendor/client names) is basic

### Immediate Next Steps (OCR/PDF)
1. Add `.pdf`, `.png`, `.jpg`, `.jpeg` to `SUPPORTED_EXTENSIONS` in `config.py`
2. Implement `parse_pdf()` using `pdfplumber` in `parsers.py`
3. Implement `parse_image()` using Gemini Vision API in `parsers.py`
4. Add sample PDF and image files to `sample_data/`
5. Wire new parsers into `data_ingestion.py` → `process_file()`
6. Test with real bank statement PDFs and receipt photos

### Post-Hackathon Roadmap
- Bank API integration (Plaid/Yodlee)
- Cron job for recurring payment auto-generation
- ML-based probability model for receivables
- Web upload dashboard
- Multi-tenant support with auth layer
- Audit trail / immutable event log

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│                  ORACULUM CHEAT SHEET                    │
├─────────────────────────────────────────────────────────┤
│ Config & constants     →  config.py                     │
│ Add new file format    →  config.py + parsers.py        │
│ Add new field          →  config.py (schema) +          │
│                           cleaners.py (cleaning logic)  │
│ Add new category       →  config.py + cleaners.py       │
│ Master JSON location   →  data_layer/master_financial   │
│                           _data.json                    │
│ Logs                   →  data_layer/logs/ingestion.log │
│ ID format              →  {prefix}_{YYYYMMDD}_{uuid8}   │
│ Date format            →  YYYY-MM-DD (always)           │
│ Amounts                →  float (- expense, + income)   │
│ Duplicate detection    →  sha256(date|desc|amount)[:16] │
│ Gemini API model       →  gemini-2.0-flash              │
│ Gemini API key env     →  GEMINI_API_KEY                │
└─────────────────────────────────────────────────────────┘
```
