import os
import json
import base64
import urllib.request
import urllib.error
import uuid
from datetime import datetime
from config import logger
from id_generator import generate_id
from manual_entry import (
    add_manual_transaction,
    add_manual_obligation,
    add_manual_receivable
)

OCR_PROMPT = """You are a receipt/invoice parser. Extract data from the image.
Return a structured JSON object exactly like this:
{
  "merchant": "Vendor Name",
  "total_amount": 123.45,
  "date": "YYYY-MM-DD",
  "category": "standardized category or 'other'",
  "type": "receipt" | "invoice_owed" | "invoice_recv",
  "raw_text": "Extracted text snippet...",
  "confidence_score": 0.95
}
"""

def _call_gemini_vision(image_path: str, api_key: str) -> dict:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    mime = "image/png" if image_path.endswith(".png") else "image/jpeg"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [
            {"text": OCR_PROMPT},
            {"inlineData": {"mimeType": mime, "data": image_data}}
        ]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
    })
    
    req = urllib.request.Request(url, data=payload.encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            response = json.loads(resp.read().decode("utf-8"))
        content = response["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(content)
    except Exception as e:
        raise RuntimeError(f"Gemini API failure: {e}")

def parse_image(filepath: str, master_path: str = None) -> dict:
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png"}:
        return {"status": "error", "message": "Only .jpg and .png supported"}

    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key: raise ValueError("GEMINI_API_KEY not set")
        
        parsed = _call_gemini_vision(filepath, api_key)
        
        date_str = datetime.now().strftime("%Y%m%d")
        doc_id = f"ocr_{date_str}_{uuid.uuid4().hex[:8]}"
        doc = {
            "doc_id": doc_id,
            "extracted_text": parsed.get("raw_text", ""),
            "merchant": parsed.get("merchant", ""),
            "total_amount": parsed.get("total_amount", 0.0),
            "date": parsed.get("date", ""),
            "category": parsed.get("category", "other"),
            "type": parsed.get("type", ""),
            "confidence_score": parsed.get("confidence_score", 0.0),
            "is_processed": False,
            "user_verified": False,
            "linked_record_id": None,
            "linked_table": None
        }
        
        conf = doc["confidence_score"]
        res = {"hand_written_docs": [], "transactions": [], "obligations": [], "receivables": []}
        
        if conf < 0.7:
            res.update({"status": "rejected", "message": "Low confidence score"})
            return res
            
        res["hand_written_docs"].append(doc)
        
        if 0.7 <= conf <= 0.9:
            res.update({"status": "low_confidence", "message": "Stored for manual review"})
            return res
            
        # > 0.9 Auto-process
        doc_type = doc["type"]
        auto_res = {}
        
        if doc_type == "receipt":
            auto_res = add_manual_transaction(doc["date"], doc["merchant"], doc["total_amount"], "expense", doc["category"], master_path)
            if auto_res.get("success"):
                doc["linked_record_id"] = auto_res["record"]["transaction_id"]
                doc["linked_table"] = "transactions"
                res["transactions"].append(auto_res["record"])
        elif doc_type == "invoice_owed":
            auto_res = add_manual_obligation(doc["merchant"], doc["extracted_text"][:50], doc["total_amount"], doc["date"], False, doc["category"], False, None, 0.5, master_path)
            if auto_res.get("success"):
                doc["linked_record_id"] = auto_res["record"]["obligation_id"]
                doc["linked_table"] = "obligations"
                res["obligations"].append(auto_res["record"])
        elif doc_type == "invoice_recv":
            auto_res = add_manual_receivable(doc["merchant"], doc["extracted_text"][:50], doc["total_amount"], doc["date"], 0.9, "standard", False, None, master_path)
            if auto_res.get("success"):
                doc["linked_record_id"] = auto_res["record"]["receivable_id"]
                doc["linked_table"] = "receivables"
                res["receivables"].append(auto_res["record"])
                
        if doc["linked_record_id"]:
            doc["is_processed"] = True
            
        res.update({"status": "success", "message": "Auto-processed successfully"})
        return res

    except Exception as e:
        logger.error(f"Image parse error: {e}")
        return {"status": "error", "message": str(e)}
