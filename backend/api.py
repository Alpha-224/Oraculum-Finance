"""
api.py — Flask REST API for the Decision Engine.

Exposes POST /api/decision and GET /api/health endpoints.
Runs on port 5001 with CORS enabled.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

# Ensure the backend package is importable when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.loader import load_master_json, MASTER_JSON_PATH
from backend.simulator import CashSimulator
from backend.scorer import ObligationScorer
from backend.planner import BeamSearchPlanner
from backend.serializer import ResponseSerializer
from backend.config import FLASK_PORT, logger

app = Flask(__name__)
CORS(app)


@app.route("/api/decision", methods=["POST"])
def decision():
    """Generate a 3-strategy decision response from the master ledger.

    Request Body:
        Optional JSON: {"horizon_days": 30}

    Returns:
        HTTP 200 + DecisionResponse JSON on success.
        HTTP 500 + {"error": "...", "trace": "..."} on failure.
    """
    try:
        master = load_master_json()
        horizon = (request.json or {}).get("horizon_days", 30)

        timeline = CashSimulator(master, horizon).run()
        scored = ObligationScorer(master["obligations"]).score_all()
        planner = BeamSearchPlanner(timeline, scored, master["receivables"])
        strategies = planner.generate_strategies()
        response = ResponseSerializer(timeline, strategies, master).build()

        return jsonify(response), 200

    except Exception as e:
        logger.exception(f"Decision endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "trace": traceback.format_exc(),
        }), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint.

    Returns:
        HTTP 200 + health status JSON.
    """
    try:
        exists = MASTER_JSON_PATH.exists()
        record_counts = {"transactions": 0, "obligations": 0, "receivables": 0}
        last_updated = ""

        if exists:
            data = load_master_json()
            meta = data.get("metadata", {})
            last_updated = meta.get("last_updated", "")
            record_counts = meta.get("record_counts", record_counts)

        return jsonify({
            "status": "ok",
            "master_json_exists": exists,
            "last_updated": last_updated,
            "record_counts": record_counts,
        }), 200

    except Exception as e:
        logger.exception(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
        }), 500


if __name__ == "__main__":
    logger.info(f"Starting Decision Engine API on port {FLASK_PORT}")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
