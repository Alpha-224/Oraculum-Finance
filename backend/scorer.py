"""
scorer.py — Obligation Scoring Engine.

Every obligation is assigned a composite priority score S ∈ [0, 1] based on
four equally-weighted dimensions: Urgency, Monetary, Operational, Rigidity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from .config import URGENCY_DECAY_K, VITALITY_MAP, logger


@dataclass
class ScoredObligation:
    """An obligation enriched with its four sub-scores and composite score."""

    obligation_id: str
    vendor: str
    amount: float
    due_date: str
    score: float             # S ∈ [0, 1]
    urgency: float           # U sub-score
    monetary: float          # M sub-score
    operational: float       # O sub-score
    rigidity: float          # R sub-score
    dominant_factor: str     # 'urgency' | 'monetary' | 'operational' | 'rigidity'
    days_to_due: int
    is_overdue: bool
    # Keep original obligation dict for downstream modules
    obligation: dict


class ObligationScorer:
    """Scores all obligations and returns ScoredObligation objects.

    Args:
        obligations: List of obligation dicts from master JSON.
    """

    def __init__(self, obligations: list[dict]) -> None:
        self._obligations = obligations

    def score_all(self) -> list[ScoredObligation]:
        """Score every obligation and return sorted list (highest first).

        Returns:
            List of ScoredObligation, sorted descending by composite score S.
        """
        scored: list[ScoredObligation] = []
        for obl in self._obligations:
            scored.append(self._score_one(obl))

        scored.sort(key=lambda s: s.score, reverse=True)
        logger.info(f"Scored {len(scored)} obligations")
        return scored

    def _score_one(self, obl: dict) -> ScoredObligation:
        """Compute the composite score for a single obligation."""
        days = self._days_to_due(obl)
        is_overdue = days < 0

        u = self._urgency_score(days)
        m = self._monetary_score(obl)
        o = self._operational_score(obl)
        r = self._rigidity_score(obl)
        s = 0.25 * (u + m + o + r)
        dominant = self._dominant_factor(u, m, o, r)

        return ScoredObligation(
            obligation_id=obl["obligation_id"],
            vendor=obl["vendor"],
            amount=float(obl["amount"]),
            due_date=obl["due_date"],
            score=round(s, 4),
            urgency=round(u, 4),
            monetary=round(m, 4),
            operational=round(o, 4),
            rigidity=round(r, 4),
            dominant_factor=dominant,
            days_to_due=days,
            is_overdue=is_overdue,
            obligation=obl,
        )

    # ─── Sub-score computations ─────────────────────────────────────────

    @staticmethod
    def _days_to_due(obl: dict) -> int:
        """Compute days until due date from today."""
        due = date.fromisoformat(obl["due_date"])
        return (due - date.today()).days

    @staticmethod
    def _urgency_score(days_to_due: int) -> float:
        """U — Exponential decay. Overdue (negative days) → clamp to 0 → U=1.0."""
        clamped = max(0, days_to_due)
        return math.exp(-URGENCY_DECAY_K * clamped)

    @staticmethod
    def _monetary_score(obl: dict) -> float:
        """M — Ratio of late_fee to amount, capped at 1.0."""
        amount = float(obl.get("amount", 0))
        late_fee = float(obl.get("late_fee", 0.0))
        if amount <= 0:
            return 0.0
        return min(1.0, late_fee / amount)

    @staticmethod
    def _operational_score(obl: dict) -> float:
        """O — Vitality based on is_critical flag and relationship_tier."""
        if obl.get("is_critical", False):
            vitality = 10
        else:
            tier = obl.get("relationship_tier", "standard")
            vitality = VITALITY_MAP.get(tier, 5)
        return vitality / 10.0

    @staticmethod
    def _rigidity_score(obl: dict) -> float:
        """R — Inverse flexibility. Rigid vendor = high R."""
        flexibility = float(obl.get("flexibility_score", 0.5))
        flexibility = max(0.0, min(1.0, flexibility))
        return 1.0 - flexibility

    @staticmethod
    def _dominant_factor(u: float, m: float, o: float, r: float) -> str:
        """Return the name of the highest sub-score."""
        scores = {
            "urgency": u,
            "monetary": m,
            "operational": o,
            "rigidity": r,
        }
        return max(scores, key=scores.get)  # type: ignore[arg-type]
