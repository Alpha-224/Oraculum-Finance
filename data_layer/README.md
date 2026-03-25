# Oraculum — Data Ingestion Module

**CashFlow Guardian — Financial GPS for Small Vendors**

## Quick Start

```bash
cd data_layer

# 1. Process sample CSV (transactions)
python data_ingestion.py process sample_data/sample_transactions.csv --type transactions

# 2. Process obligations
python data_ingestion.py process sample_data/sample_obligations.csv --type obligations

# 3. Process JSON receivables
python data_ingestion.py process sample_data/sample_receivables.json --type receivables

# 4. Process unstructured text (uses Gemini API or regex fallback)
python data_ingestion.py process sample_data/sample_note.txt

# 5. Add manual transaction
python data_ingestion.py add-transaction --date 2024-03-10 --description "Test Payment" --amount -100.00 --type expense

# 6. Add manual obligation
python data_ingestion.py add-obligation --vendor "Supplier X" --description "Monthly supply" --amount 500 --due-date 2024-04-15

# 7. Add manual receivable
python data_ingestion.py add-receivable --client "Client Y" --description "Invoice payment" --amount 2000 --expected-date 2024-04-20

# 8. Print validation report
python data_ingestion.py report
```

## Gemini API (Optional)

Set `GEMINI_API_KEY` environment variable for AI-powered TXT parsing:
```bash
set GEMINI_API_KEY=your_api_key_here   # Windows
export GEMINI_API_KEY=your_api_key_here # Mac/Linux
```

Without the key, TXT files fall back to regex extraction (lower confidence).

## Architecture

```
Input Layer → Format Detection → Parser → Cleaning → Validation → Master JSON
```

| Layer | Module | Responsibility |
|-------|--------|---------------|
| Config | `config.py` | Schemas, defaults, taxonomy |
| IDs | `id_generator.py` | `txn_YYYYMMDD_uuid4[:8]` |
| Cleaning | `cleaners.py` | Dates, amounts, categories |
| Validation | `validators.py` | Required fields, types, dedup |
| Parsing | `parsers.py` | CSV, JSON, TXT (Gemini/regex) |
| Balance | `balance.py` | Running balance computation |
| Storage | `master_json.py` | Load/save/merge master JSON |
| API | `manual_entry.py` | Flutter integration functions |
| CLI | `data_ingestion.py` | Command-line interface |

## Output

All data is stored in `master_financial_data.json` with three tables:
- **transactions** — Past money movement (income/expense/transfer)
- **obligations** — Upcoming payments owed
- **receivables** — Expected incoming payments

## Flutter Integration

Import and call directly:
```python
from manual_entry import add_manual_transaction, add_manual_obligation, add_manual_receivable
```

## Requirements

- Python 3.8+
- No external dependencies for core functionality
- Optional: `GEMINI_API_KEY` for AI-powered text extraction
