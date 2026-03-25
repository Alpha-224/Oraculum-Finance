"""
test_planner.py — Unit tests for the BeamSearchPlanner.
"""

import pytest
from datetime import date, timedelta
from backend.simulator import CashSimulator, CashTimeline
from backend.scorer import ObligationScorer, ScoredObligation
from backend.planner import BeamSearchPlanner


def _make_data(balance=5000.0, obligations=None, receivables=None):
    """Build a master data dict for planner testing."""
    txns = [{"date": "2026-03-25", "amount": balance, "type": "starting", "running_balance": balance}]
    return {
        "metadata": {},
        "transactions": txns,
        "obligations": obligations or [],
        "receivables": receivables or [],
    }


def _make_obligation(obl_id, vendor, amount, days_ahead=5, **overrides):
    """Build a test obligation dict."""
    today = date.today()
    base = {
        "obligation_id": obl_id,
        "vendor": vendor,
        "description": f"Test {vendor}",
        "amount": amount,
        "due_date": (today + timedelta(days=days_ahead)).isoformat(),
        "is_critical": False,
        "late_fee": 50.0,
        "grace_days": 3,
        "flexibility_score": 0.5,
        "relationship_tier": "standard",
        "recurring_payment": False,
    }
    base.update(overrides)
    return base


class TestBeamSearchPlanner:
    """Tests for BeamSearchPlanner per PRD Section 13.1."""

    def test_always_three_strategies(self):
        """Must produce exactly 3 strategies."""
        obls = [
            _make_obligation("obl_1", "Vendor A", 500.0, days_ahead=2, is_critical=True),
            _make_obligation("obl_2", "Vendor B", 300.0, days_ahead=10, flexibility_score=0.8),
            _make_obligation("obl_3", "Vendor C", 200.0, days_ahead=20, flexibility_score=0.1),
        ]
        data = _make_data(balance=5000.0, obligations=obls)
        timeline = CashSimulator(data, 30).run()
        scored = ObligationScorer(obls).score_all()
        strategies = BeamSearchPlanner(timeline, scored, []).generate_strategies()
        assert len(strategies) == 3

    def test_strategy_names(self):
        """Strategies must have the correct names."""
        obls = [_make_obligation("obl_1", "Vendor A", 500.0)]
        data = _make_data(balance=5000.0, obligations=obls)
        timeline = CashSimulator(data, 30).run()
        scored = ObligationScorer(obls).score_all()
        strategies = BeamSearchPlanner(timeline, scored, []).generate_strategies()
        names = {s.name for s in strategies}
        assert "Penalty Minimizer" in names
        assert "Operation Protector" in names
        assert "Relationship Preserver" in names

    def test_action_count_matches_obligations(self):
        """Each strategy must have one action per obligation."""
        obls = [
            _make_obligation("obl_1", "A", 100.0),
            _make_obligation("obl_2", "B", 200.0),
        ]
        data = _make_data(balance=5000.0, obligations=obls)
        timeline = CashSimulator(data, 30).run()
        scored = ObligationScorer(obls).score_all()
        strategies = BeamSearchPlanner(timeline, scored, []).generate_strategies()
        for strat in strategies:
            assert len(strat.actions) == 2

    def test_valid_action_labels(self):
        """All action labels must be valid."""
        obls = [_make_obligation("obl_1", "Vendor", 500.0)]
        data = _make_data(balance=5000.0, obligations=obls)
        timeline = CashSimulator(data, 30).run()
        scored = ObligationScorer(obls).score_all()
        strategies = BeamSearchPlanner(timeline, scored, []).generate_strategies()
        valid = {"PAY_NOW", "PAY_SCHEDULED", "PARTIAL", "DELAY", "NEGOTIATE"}
        for strat in strategies:
            for action in strat.actions:
                assert action.action_label in valid

    def test_fractions_ten_percent_increments(self):
        """Paid fractions must be 10% increments."""
        obls = [
            _make_obligation("obl_1", "A", 300.0, flexibility_score=0.8),
            _make_obligation("obl_2", "B", 200.0, flexibility_score=0.2),
        ]
        data = _make_data(balance=5000.0, obligations=obls)
        timeline = CashSimulator(data, 30).run()
        scored = ObligationScorer(obls).score_all()
        strategies = BeamSearchPlanner(timeline, scored, []).generate_strategies()
        valid_fracs = {0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0}
        for strat in strategies:
            for action in strat.actions:
                assert action.paid_fraction in valid_fracs

    def test_paid_amount_not_exceeds_obligation(self):
        """paid_amount must never exceed obligation amount."""
        obls = [_make_obligation("obl_1", "Vendor", 1000.0)]
        data = _make_data(balance=5000.0, obligations=obls)
        timeline = CashSimulator(data, 30).run()
        scored = ObligationScorer(obls).score_all()
        strategies = BeamSearchPlanner(timeline, scored, []).generate_strategies()
        for strat in strategies:
            for action in strat.actions:
                assert action.paid_amount <= action.amount + 0.01

    def test_survival_probability_in_range(self):
        """Survival probability must be ∈ [0, 1]."""
        obls = [_make_obligation("obl_1", "Vendor", 500.0)]
        data = _make_data(balance=5000.0, obligations=obls)
        timeline = CashSimulator(data, 30).run()
        scored = ObligationScorer(obls).score_all()
        strategies = BeamSearchPlanner(timeline, scored, []).generate_strategies()
        for strat in strategies:
            assert 0.0 <= strat.survival_probability <= 1.0

    def test_zero_obligations_empty_actions(self):
        """Zero obligations → strategies with empty actions[]."""
        data = _make_data(balance=5000.0, obligations=[])
        timeline = CashSimulator(data, 30).run()
        strategies = BeamSearchPlanner(timeline, [], []).generate_strategies()
        assert len(strategies) == 3
        for strat in strategies:
            assert len(strat.actions) == 0
            assert strat.survival_probability == 1.0
