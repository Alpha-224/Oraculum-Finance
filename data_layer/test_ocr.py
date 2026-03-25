import unittest
from unittest.mock import patch, MagicMock
from ocr_parser import parse_image
import os
import json

class TestOCRParser(unittest.TestCase):
    def setUp(self):
        os.environ["GEMINI_API_KEY"] = "fake_key"
        # Create a fake image so validation passes
        with open("fake_receipt.jpg", "wb") as f:
            f.write(b"fake image data")

    def tearDown(self):
        if os.path.exists("fake_receipt.jpg"):
            os.remove("fake_receipt.jpg")
            
    def _mock_api_response(self, score, doc_type="receipt"):
        return {
            "merchant": "Test Vendor",
            "total_amount": 100.0,
            "date": "2026-03-25",
            "category": "catering",
            "type": doc_type,
            "raw_text": "Test receipt raw text",
            "confidence_score": score
        }

    @patch("ocr_parser._call_gemini_vision")
    def test_rejected_confidence(self, mock_gemini):
        mock_gemini.return_value = self._mock_api_response(0.5)
        res = parse_image("fake_receipt.jpg")
        
        self.assertEqual(res["status"], "rejected")
        self.assertEqual(len(res.get("transactions", [])), 0)
        self.assertEqual(len(res.get("hand_written_docs", [])), 0)

    @patch("ocr_parser._call_gemini_vision")
    def test_low_confidence(self, mock_gemini):
        mock_gemini.return_value = self._mock_api_response(0.8)
        res = parse_image("fake_receipt.jpg")
        
        self.assertEqual(res["status"], "low_confidence")
        self.assertEqual(len(res["hand_written_docs"]), 1)
        self.assertEqual(len(res.get("transactions", [])), 0)
        
        doc = res["hand_written_docs"][0]
        self.assertFalse(doc["is_processed"])
        self.assertIsNone(doc["linked_record_id"])
        self.assertIsNone(doc["linked_table"])

    @patch("ocr_parser.add_manual_transaction")
    @patch("ocr_parser._call_gemini_vision")
    def test_high_confidence_transaction(self, mock_gemini, mock_add_txn):
        mock_gemini.return_value = self._mock_api_response(0.95, "receipt")
        
        # Mock add_manual_transaction response
        mock_add_txn.return_value = {
            "success": True,
            "record": {"transaction_id": "txn_123"}
        }
        
        res = parse_image("fake_receipt.jpg")
        
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["hand_written_docs"]), 1)
        self.assertEqual(len(res["transactions"]), 1)
        
        doc = res["hand_written_docs"][0]
        self.assertTrue(doc["is_processed"])
        self.assertEqual(doc["linked_record_id"], "txn_123")
        self.assertEqual(doc["linked_table"], "transactions")

    @patch("ocr_parser.add_manual_obligation")
    @patch("ocr_parser._call_gemini_vision")
    def test_high_confidence_obligation(self, mock_gemini, mock_add_obl):
        mock_gemini.return_value = self._mock_api_response(0.95, "invoice_owed")
        
        # Mock add_manual_obligation response
        mock_add_obl.return_value = {
            "success": True,
            "record": {"obligation_id": "obl_123"}
        }
        
        res = parse_image("fake_receipt.jpg")
        self.assertEqual(res["status"], "success")
        
        doc = res["hand_written_docs"][0]
        self.assertTrue(doc["is_processed"])
        self.assertEqual(doc["linked_record_id"], "obl_123")
        self.assertEqual(doc["linked_table"], "obligations")

    @patch("ocr_parser.add_manual_receivable")
    @patch("ocr_parser._call_gemini_vision")
    def test_high_confidence_receivable(self, mock_gemini, mock_add_recv):
        mock_gemini.return_value = self._mock_api_response(0.95, "invoice_recv")
        
        # Mock add_manual_receivable response
        mock_add_recv.return_value = {
            "success": True,
            "record": {"receivable_id": "rec_123"}
        }
        
        res = parse_image("fake_receipt.jpg")
        self.assertEqual(res["status"], "success")
        
        doc = res["hand_written_docs"][0]
        self.assertTrue(doc["is_processed"])
        self.assertEqual(doc["linked_record_id"], "rec_123")
        self.assertEqual(doc["linked_table"], "receivables")

if __name__ == "__main__":
    unittest.main()
