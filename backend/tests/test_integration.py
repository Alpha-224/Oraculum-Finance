"""
test_integration.py — Golden Response integration test.

Runs the entire Decision Engine end-to-end against the real master data
and validates the response shape.
"""

import pytest
from backend.loader import load_master_json
from backend.simulator import CashSimulator
from backend.scorer import ObligationScorer
from backend.planner import BeamSearchPlanner
from backend.serializer import ResponseSerializer


def _run_decision_engine(data: dict) -> dict:
    """Run the full engine pipeline and return the response dict."""
    timeline = CashSimulator(data, 30).run()
    scored = ObligationScorer(data["obligations"]).score_all()
    strategies = BeamSearchPlanner(timeline, scored, data["receivables"]).generate_strategies()
    return ResponseSerializer(timeline, strategies, data).build()


class TestGoldenResponse:
    """Integration test — full pipeline on real data."""

    def test_golden_response_shape(self):
        """End-to-end: response has correct structure and values."""
        data = load_master_json()
        response = _run_decision_engine(data)

        # Top-level keys
        assert "generated_at" in response
        assert "timeline" in response
        assert "strategies" in response
        assert "survival_probability" in response
        assert "risk_label" in response
        assert "obligation_summary" in response
        assert "metadata" in response

        # Strategy count
        assert len(response["strategies"]) == 3
        assert response["strategies"][0]["name"] == "Penalty Minimizer"
        assert response["strategies"][1]["name"] == "Operation Protector"
        assert response["strategies"][2]["name"] == "Relationship Preserver"

        # Survival probability
        assert 0.0 <= response["survival_probability"] <= 1.0

        # Timeline
        assert len(response["timeline"]["balances"]) == 30
        assert len(response["timeline"]["dates"]) == 30
        assert all(isinstance(b, float) for b in response["timeline"]["balances"])

        # Each strategy
        for strat in response["strategies"]:
            assert "actions" in strat
            assert "survival_probability" in strat
            assert "risk_metrics" in strat
            for action in strat["actions"]:
                assert action["reasoning"] != ""
                assert action["action_label"] != ""
                assert action["paid_amount"] <= action["amount"] + 0.01

    def test_json_serializable(self):
        """Response must be fully JSON-serializable."""
        import json
        data = load_master_json()
        response = _run_decision_engine(data)
        raw = json.dumps(response)
        assert isinstance(raw, str)
        assert len(raw) > 100
