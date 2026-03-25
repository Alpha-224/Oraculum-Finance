"""
test_simulator.py — Unit tests for the CashSimulator.
"""

import pytest
from datetime import date, timedelta
from backend.simulator import CashSimulator, CashTimeline


def _make_data(transactions=None, obligations=None, receivables=None):
    """Build a minimal master data dict for testing."""
    return {
        "metadata": {},
        "transactions": transactions or [],
        "obligations": obligations or [],
        "receivables": receivables or [],
    }


class TestCashSimulator:
    """Tests for CashSimulator per PRD Section 13.1."""

    def test_empty_transactions_opening_balance_zero(self):
        """Empty transactions[] → C(0) = 0.0."""
        data = _make_data()
        timeline = CashSimulator(data, 30).run()
        assert timeline.opening_balance == 0.0
        assert len(timeline.daily_balances) == 30

    def test_opening_balance_from_last_transaction(self):
        """C(0) should be the running_balance of the last sorted transaction."""
        txns = [
            {"date": "2026-03-20", "amount": 1000, "type": "starting", "running_balance": 1000.0},
            {"date": "2026-03-25", "amount": -200, "type": "expense", "running_balance": 800.0},
        ]
        data = _make_data(transactions=txns)
        timeline = CashSimulator(data, 30).run()
        assert timeline.opening_balance == 800.0

    def test_thirty_day_timeline_length(self):
        """Timeline should always have exactly 30 entries."""
        txns = [{"date": "2026-03-25", "amount": 5000, "type": "starting", "running_balance": 5000.0}]
        data = _make_data(transactions=txns)
        timeline = CashSimulator(data, 30).run()
        assert len(timeline.daily_balances) == 30
        assert len(timeline.daily_dates) == 30

    def test_overdue_receivable_zero_inflow(self):
        """Overdue receivables (is_overdue=True) → $0 inflow."""
        today = date.today()
        txns = [{"date": "2026-03-25", "amount": 1000, "type": "starting", "running_balance": 1000.0}]
        recs = [{
            "receivable_id": "rec_test", "client": "Test", "amount": 500.0,
            "expected_date": (today + timedelta(days=5)).isoformat(),
            "probability": 0.95, "is_overdue": True, "client_tier": "standard",
        }]
        data = _make_data(transactions=txns, receivables=recs)
        timeline = CashSimulator(data, 30).run()
        # Balance should not increase since receivable is overdue
        assert all(b <= 1000.0 for b in timeline.daily_balances)

    def test_cash_breach_sets_first_breach_day(self):
        """Cash going negative should set first_breach_day."""
        today = date.today()
        txns = [{"date": "2026-03-25", "amount": 100, "type": "starting", "running_balance": 100.0}]
        obls = [{
            "obligation_id": "obl_test", "vendor": "Test", "amount": 500.0,
            "due_date": (today + timedelta(days=1)).isoformat(),
            "is_critical": False, "late_fee": 0, "grace_days": 0,
            "flexibility_score": 0.5, "relationship_tier": "standard",
            "recurring_payment": False,
        }]
        data = _make_data(transactions=txns, obligations=obls)
        timeline = CashSimulator(data, 30).run()
        assert timeline.first_breach_day is not None
        assert isinstance(timeline.first_breach_day, int)

    def test_no_breach_returns_none(self):
        """If cash never goes negative, first_breach_day should be None."""
        txns = [{"date": "2026-03-25", "amount": 10000, "type": "starting", "running_balance": 10000.0}]
        data = _make_data(transactions=txns)
        timeline = CashSimulator(data, 30).run()
        assert timeline.first_breach_day is None
