# Oraculum Data Ingestion Module — Walkthrough

## What Was Built

A complete, production-ready Python data ingestion pipeline for CashFlow Guardian, living in `data_layer/`.

### Module Structure

| File | Responsibility |
|------|---------------|
| [config.py](file:///w:/Vault/Codes/fintechSNUChacks26/oraculum%202/Oraculum-Finance/data_layer/config.py) | Schemas, defaults, taxonomy, logging |
| [id_generator.py](file:///w:/Vault/Codes/fintechSNUChacks26/oraculum%202/Oraculum-Finance/data_layer/id_generator.py) | `txn_YYYYMMDD_uuid4[:8]` style IDs |
| [cleaners.py](file:///w:/Vault/Codes/fintechSNUChacks26/oraculum%202/Oraculum-Finance/data_layer/cleaners.py) | Date/amount/category normalization |
| [validators.py](file:///w:/Vault/Codes/fintechSNUChacks26/oraculum%202/Oraculum-Finance/data_layer/validators.py) | Required fields, types, fingerprint dedup |
| [parsers.py](file:///w:/Vault/Codes/fintechSNUChacks26/oraculum%202/Oraculum-Finance/data_layer/parsers.py) | CSV/JSON (deterministic) + TXT (Gemini/regex) |
| [balance.py](file:///w:/Vault/Codes/fintechSNUChacks26/oraculum%202/Oraculum-Finance/data_layer/balance.py) | Running balance computation |
| [master_json.py](file:///w:/Vault/Codes/fintechSNUChacks26/oraculum%202/Oraculum-Finance/data_layer/master_json.py) | Atomic load/save/merge for master JSON |
| [manual_entry.py](file:///w:/Vault/Codes/fintechSNUChacks26/oraculum%202/Oraculum-Finance/data_layer/manual_entry.py) | 3 Flutter-ready API functions |
| [data_ingestion.py](file:///w:/Vault/Codes/fintechSNUChacks26/oraculum%202/Oraculum-Finance/data_layer/data_ingestion.py) | CLI entrypoint with argparse |

## Verification Results

All tests passed end-to-end:

| Test | Result |
|------|--------|
| CSV transactions (5 rows) | ✅ All ingested, running balances correct |
| CSV obligations (3 rows) | ✅ Categories mapped (inventory, rent, utilities) |
| JSON receivables (2 records) | ✅ Parsed with recurring payment flags |
| TXT note (regex fallback) | ✅ Extracted 1 txn + 1 obligation + 1 receivable |
| Duplicate detection | ✅ Re-ingesting CSV added 0 new records |
| Manual transaction entry | ✅ Added `txn_20240310_beceb2b5`, balance recalculated |
| Running balance chain | ✅ 5000 → 4150 → 4575 → 2575 → 3825 → 3725 → 2775 |
| Master JSON schema | ✅ All 3 tables + metadata correct |

### Final Master JSON State After Full Test Run

- **7 transactions** from CSV + manual + TXT
- **4 obligations** from CSV + TXT
- **3 receivables** from JSON + TXT
- **5 source files** tracked in metadata

## Quick Start

```bash
cd data_layer
python data_ingestion.py process sample_data/sample_transactions.csv --type transactions
python data_ingestion.py report
```

Full documentation in [README.md](file:///w:/Vault/Codes/fintechSNUChacks26/oraculum%202/Oraculum-Finance/data_layer/README.md).
