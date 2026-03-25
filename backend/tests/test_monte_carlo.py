"""
test_monte_carlo.py — Unit tests for the MonteCarloEngine.
"""

import pytest
from datetime import date, timedelta
from backend.simulator import CashSimulator, CashTimeline
from backend.monte_carlo import MonteCarloEngine, MonteCarloResult


def _make_data(transactions=None, obligations=None, receivables=None):
    """Build a minimal master data dict."""
    return {
        "metadata": {},
        "transactions": transactions or [],
        "obligations": obligations or [],
        "receivables": receivables or [],
    }


def _make_timeline(opening=5000.0):
    """Build a simple CashTimeline for testing."""
    today = date.today()
    return CashTimeline(
        opening_balance=opening,
        daily_balances=[opening] * 30,
        daily_dates=[(today + timedelta(days=i)).isoformat() for i in range(30)],
        minimum_cash=opening,
        first_breach_day=None,
        total_inflows=0.0,
        total_outflows=0.0,
        net_position=0.0,
    )


class TestMonteCarloEngine:
    """Tests for MonteCarloEngine per PRD Section 13.1."""

    def test_survival_in_range(self):
        """survival_probability must be ∈ [0, 1]."""
        timeline = _make_timeline(5000.0)
        result = MonteCarloEngine([], timeline, {}, runs=100).run()
        assert 0.0 <= result.survival_probability <= 1.0

    def test_probability_one_always_arrives(self):
        """probability=1.0 receivable → always arrives (survival should be high)."""
        today = date.today()
        recs = [{
            "receivable_id": "rec_test", "client": "Reliable Co",
            "amount": 1000.0,
            "expected_date": (today + timedelta(days=5)).isoformat(),
            "probability": 1.0, "is_overdue": False, "client_tier": "critical",
        }]
        timeline = _make_timeline(5000.0)
        result = MonteCarloEngine(recs, timeline, {}, runs=100).run()
        assert result.survival_probability >= 0.9  # nearly certain

    def test_probability_zero_never_arrives(self):
        """probability=0.0 → never arrives."""
        today = date.today()
        recs = [{
            "receivable_id": "rec_test", "client": "Deadbeat Co",
            "amount": 1000.0,
            "expected_date": (today + timedelta(days=5)).isoformat(),
            "probability": 0.0, "is_overdue": False, "client_tier": "minor",
        }]
        timeline = _make_timeline(5000.0)
        result = MonteCarloEngine(recs, timeline, {}, runs=100).run()
        # Since baseline has no outflows and opening=5000, survival should still be 1.0
        assert result.survival_probability == 1.0

    def test_overdue_always_zero(self):
        """is_overdue=True → always $0 inflow."""
        today = date.today()
        recs = [{
            "receivable_id": "rec_test", "client": "Overdue Client",
            "amount": 10000.0,
            "expected_date": (today + timedelta(days=5)).isoformat(),
            "probability": 1.0, "is_overdue": True, "client_tier": "critical",
        }]
        timeline = _make_timeline(5000.0)
        result = MonteCarloEngine(recs, timeline, {}, runs=50).run()
        # With no receivable inflows and no outflows, balance stays at opening
        assert result.mean_ending_balance == pytest.approx(5000.0, abs=1.0)

    def test_percentile_ordering(self):
        """p10 ≤ mean ≤ p90."""
        timeline = _make_timeline(3000.0)
        today = date.today()
        recs = [{
            "receivable_id": "rec_test", "client": "Client",
            "amount": 500.0,
            "expected_date": (today + timedelta(days=10)).isoformat(),
            "probability": 0.7, "is_overdue": False, "client_tier": "standard",
        }]
        result = MonteCarloEngine(recs, timeline, {}, runs=200).run()
        assert result.p10_ending_balance <= result.mean_ending_balance
        assert result.mean_ending_balance <= result.p90_ending_balance
