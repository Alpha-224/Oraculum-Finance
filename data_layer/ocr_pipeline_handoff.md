# 🚀 Oraculum OCR Pipeline: Developer Handoff Guide

Welcome! This document outlines the newly implemented OCR Image Parsing module ([ocr_parser.py](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/ocr_parser.py)) for the CashFlow Guardian app. It is designed to get the next developer up to speed on the architecture, the data storage strategy, the confidence-based routing logic, and the exact steps to proceed.

---

## 1. What Was Built
We successfully integrated **Gemini 2.0 Flash Vision API** to process photographed receipts and invoices (`.jpg`, `.png`). 
Instead of building an entirely separate data flow, the OCR pipeline completely plugs into the existing **Append-Only Master JSON Pipeline**.

### Key Files Created & Modified
* **[data_layer/ocr_parser.py](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/ocr_parser.py) (NEW)**: The core engine. It reads the image, calls Gemini Vision with a strict JSON schema prompt, and handles the logic for storing the extracted representation.
* **[data_layer/test_ocr.py](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/test_ocr.py) (NEW)**: An automated feedback loop & unit test suite using `unittest.mock`. It proves the routing logic for all confidence tiers without wasting real Gemini API calls.
* **[data_layer/data_ingestion.py](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/data_ingestion.py) (MODIFIED)**: Wired to recognize `.png` and `.jpg` payloads, passing them straight to [parse_image](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/ocr_parser.py#53-126).
* **[data_layer/config.py](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/config.py) & [parsers.py](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/parsers.py) (MODIFIED)**: Registered image file extensions so the existing format-detector intercepts visual documents seamlessly.

---

## 2. Core Data & Database Principles to Keep in Mind

### 🚫 NO SQLite / Relational DBs
This is critical: **The app relies on a Single Source of Truth — `master_financial_data.json`.** 
Do *not* attempt to use SQLite, PostgreSQL, or ORMs. 

### 📂 The `hand_written_docs` Transient State
When the OCR extracts text from an image, the data first materializes as a generic object called `"hand_written_docs"`.
**Schema Requirements for `hand_written_docs`**:
* `doc_id`: Unique identifier (e.g., `ocr_YYYYMMDD_uuid8`)
* `extracted_text`: Raw block of text from Gemini
* `merchant`, `total_amount`, `date`, `category`, `type`, `confidence_score`
* `is_processed`: Boolean (True if automatically merged into the master ledger)
* `user_verified`: Boolean (For future UI approval)
* `linked_record_id` & `linked_table`: Relational pointers into the master JSON once the data is merged.

---

## 3. The 3-Tier Confidence Routing Logic
The prompt sent to Gemini demands a `confidence_score` (0-1). The [parse_image](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/ocr_parser.py#53-126) function uses this to determine safe automation:

1. **`Score < 0.7` (REJECTED)**
   - The document is too blurry or nonsensical.
   - **Result**: Nothing is saved. Returns `"status": "rejected"`.
   
2. **`0.7 <= Score <= 0.9` (MANUAL REVIEW)**
   - The parser extracted text, but it's risky to auto-deduct/inject money.
   - **Result**: Creates and returns the `"hand_written_docs"` record *only*. Does NOT hit the master JSON. Returns `"status": "low_confidence"`. 
   - *Next Step for UI*: Present this to the user for manual approval.
   
3. **`Score > 0.9` (AUTO-PROCESSED)**
   - The AI is confident.
   - **Result**: 
     * Creates the `"hand_written_docs"` record.
     * Fires [add_manual_transaction()](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/manual_entry.py#16-68), [add_manual_obligation()](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/manual_entry.py#70-127), or [add_manual_receivable()](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/manual_entry.py#129-188) depending on the parsed `type` (receipt vs invoice).
     * This safely subjects the record to the pipeline's exact cleaning, ID generation, duplication, and balance calculation.
     * The new real ID (e.g., `txn_...`) is mapped back to the `hand_written_docs` record as `linked_record_id`.
     * `is_processed` is flipped to `True`.

---

## 4. Testing & The Automated Feedback Loop
To ensure your new features don't break existing logic, we established **[test_ocr.py](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/test_ocr.py)**. 
Whenever you tweak the pipeline, run:
```bash
python data_layer/test_ocr.py
```
This suite actively mocks out the Gemini Vision API response. It tests all three confidence thresholds and validates that IDs are correctly mapped back without destroying the local environment. **Do not disabled these tests.**

---

## 5. How to Proceed (Next Steps for the Team)

With the backend pipeline finalized, you can proceed with the following synchronised steps:

1. **Frontend / UI Wiring (Flutter/Flask):**
   - The UI needs to send image bytes or file paths to [parse_image()](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/ocr_parser.py#53-126).
   - When the backend returns `"status": "low_confidence"`, the Frontend needs to pop open a modal showing the extracted `hand_written_docs` JSON and ask the user to verify/correct it.
   - Once verified, the Frontend should manually trigger [add_manual_transaction](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/manual_entry.py#16-68) (or the equivalent API call).

2. **Environment Variables:**
   - Ensure the server/system running this has `GEMINI_API_KEY` actively exported in its environment block. Without it, the image parsing throws a `ValueError`.

3. **Expanding PDF Scans (Future Scope):**
   - We currently support `.png` and `.jpg`. Scanned [.pdf](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/Oraculum_OCR_Ingestion_PRD_v1.pdf) documents will need to be sliced into `.jpg` frames via a library like `pdf2image` before feeding them into this exact same [_call_gemini_vision](file:///d:/Ableton/codes/Oraculum/Oraculum-Finance/data_layer/ocr_parser.py#29-52) loop. You will not need to rewrite the AI logic.

Good luck! Keep the master JSON clean and rely heavily on the existing `cleaners.py` and `validators.py` for data sanitization!
