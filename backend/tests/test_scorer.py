"""
test_scorer.py — Unit tests for the ObligationScorer.
"""

import pytest
from datetime import date, timedelta
from backend.scorer import ObligationScorer, ScoredObligation


def _make_obligation(**overrides):
    """Build a minimal obligation dict with defaults."""
    today = date.today()
    base = {
        "obligation_id": "obl_20260326_test1234",
        "vendor": "Test Vendor",
        "description": "Test obligation",
        "amount": 1000.0,
        "due_date": (today + timedelta(days=5)).isoformat(),
        "is_critical": False,
        "late_fee": 0.0,
        "grace_days": 0,
        "flexibility_score": 0.5,
        "relationship_tier": "standard",
        "recurring_payment": False,
    }
    base.update(overrides)
    return base


class TestObligationScorer:
    """Tests for ObligationScorer per PRD Section 13.1."""

    def test_overdue_obligation_urgency_one(self):
        """Overdue obligation → U = 1.0."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        obl = _make_obligation(due_date=yesterday)
        scored = ObligationScorer([obl]).score_all()
        assert scored[0].urgency == 1.0

    def test_no_late_fee_monetary_zero(self):
        """No late_fee → M = 0.0."""
        obl = _make_obligation(late_fee=0.0)
        scored = ObligationScorer([obl]).score_all()
        assert scored[0].monetary == 0.0

    def test_is_critical_operational_one(self):
        """is_critical=True → O = 1.0."""
        obl = _make_obligation(is_critical=True)
        scored = ObligationScorer([obl]).score_all()
        assert scored[0].operational == 1.0

    def test_flexibility_one_rigidity_zero(self):
        """flexibility_score=1.0 → R = 0.0."""
        obl = _make_obligation(flexibility_score=1.0)
        scored = ObligationScorer([obl]).score_all()
        assert scored[0].rigidity == 0.0

    def test_score_in_range(self):
        """All scores must be ∈ [0, 1]."""
        obl = _make_obligation(
            late_fee=500.0, is_critical=True, flexibility_score=0.0
        )
        scored = ObligationScorer([obl]).score_all()
        s = scored[0]
        assert 0.0 <= s.score <= 1.0
        assert 0.0 <= s.urgency <= 1.0
        assert 0.0 <= s.monetary <= 1.0
        assert 0.0 <= s.operational <= 1.0
        assert 0.0 <= s.rigidity <= 1.0

    def test_dominant_factor_valid(self):
        """dominant_factor must be one of the four sub-score names."""
        obl = _make_obligation()
        scored = ObligationScorer([obl]).score_all()
        assert scored[0].dominant_factor in ("urgency", "monetary", "operational", "rigidity")

    def test_relationship_tier_minor_operational(self):
        """relationship_tier='minor' → O = 0.1."""
        obl = _make_obligation(relationship_tier="minor", is_critical=False)
        scored = ObligationScorer([obl]).score_all()
        assert scored[0].operational == 0.1

    def test_monetary_capped_at_one(self):
        """late_fee > amount → M = 1.0 (capped)."""
        obl = _make_obligation(amount=100.0, late_fee=200.0)
        scored = ObligationScorer([obl]).score_all()
        assert scored[0].monetary == 1.0
