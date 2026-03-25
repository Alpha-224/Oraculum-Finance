"""
explainer.py — Explanation Engine.

Generates deterministic, template-based plain-English reasoning for every
action in every strategy. No AI inference, no LLM calls — same inputs
always produce the same text.
"""

from __future__ import annotations

from .config import LOW_CASH_THRESHOLD, logger
from .scorer import ScoredObligation
from .simulator import CashTimeline


# ─── Templates: (action_label, dominant_factor) → template ──────────────────

EXPLANATION_TEMPLATES: dict[tuple[str, str], str] = {
    # PAY_NOW
    ("PAY_NOW", "urgency"):       "Payment to {vendor} is due in {days} day(s) — immediate action required.",
    ("PAY_NOW", "operational"):   "{vendor} is a critical supplier; service interruption risk is high if delayed.",
    ("PAY_NOW", "monetary"):      "Late fee of {late_fee} on {vendor} payment exceeds the cost of paying now.",
    ("PAY_NOW", "rigidity"):      "{vendor} has zero flexibility — full on-time payment is the only option.",

    # PAY_SCHEDULED
    ("PAY_SCHEDULED", "urgency"):     "{vendor} payment is due in {days} day(s) — scheduled for on-time payment.",
    ("PAY_SCHEDULED", "operational"): "{vendor} is operationally important — scheduled for timely payment.",
    ("PAY_SCHEDULED", "monetary"):    "Paying {vendor} on schedule avoids a {late_fee} late fee.",
    ("PAY_SCHEDULED", "rigidity"):    "{vendor} requires on-time payment — scheduled as planned.",

    # PARTIAL
    ("PARTIAL", "urgency"):       "Partial payment preserves cash while meeting {vendor}'s imminent deadline.",
    ("PARTIAL", "operational"):   "Partial payment keeps {vendor} operational without draining full reserves.",
    ("PARTIAL", "monetary"):      "Partial payment to {vendor} reduces late fee exposure while preserving liquidity.",
    ("PARTIAL", "rigidity"):      "Partial payment to {vendor} balances obligation rigidity with cash constraints.",

    # DELAY
    ("DELAY", "urgency"):         "{vendor} has {days} days remaining and {grace} grace days — safe to defer.",
    ("DELAY", "operational"):     "{vendor} is non-critical — deferral has minimal operational impact.",
    ("DELAY", "monetary"):        "Delaying {vendor} incurs minimal penalty relative to preserving cash position.",
    ("DELAY", "rigidity"):        "{vendor}'s high flexibility score ({flex}) allows payment renegotiation.",

    # NEGOTIATE
    ("NEGOTIATE", "urgency"):     "{vendor} has {days} days remaining — negotiate extended terms.",
    ("NEGOTIATE", "operational"): "{vendor} is flexible enough to accept renegotiation without service impact.",
    ("NEGOTIATE", "monetary"):    "Negotiating with {vendor} avoids {late_fee} penalty while preserving the relationship.",
    ("NEGOTIATE", "rigidity"):    "{vendor} is open to negotiation (flexibility {flex}) — request an extension.",
    ("NEGOTIATE", "flexibility"): "{vendor} is open to negotiation (flexibility {flex}) — request an extension.",
}

# ─── Strategy-level summaries ───────────────────────────────────────────────

STRATEGY_SUMMARIES: dict[str, str] = {
    "Penalty Minimizer":      "Prioritizes full payment of high-penalty obligations to minimize total late fees.",
    "Operation Protector":    "Ensures all business-critical vendors are paid in full, protecting daily operations.",
    "Relationship Preserver": "Focuses on rigid, long-term vendors to maintain supplier trust and credit terms.",
}


class ExplanationEngine:
    """Generates deterministic explanations for actions and strategies.

    Args:
        timeline: CashTimeline for cash pressure checks.
    """

    def __init__(self, timeline: CashTimeline) -> None:
        self._timeline = timeline

    def explain_strategies(
        self,
        strategies: list,
        scored_map: dict[str, ScoredObligation],
    ) -> None:
        """Fill reasoning for all actions and descriptions for all strategies.

        Mutates the strategy and action objects in-place.

        Args:
            strategies: List of Strategy objects from the planner.
            scored_map: Dict mapping obligation_id → ScoredObligation.
        """
        pressure_note = self._cash_pressure_narrative()

        for strat in strategies:
            # Action-level reasoning
            for action in strat.actions:
                scored = scored_map.get(action.obligation_id)
                if scored:
                    action.reasoning = self._generate_action_reason(action, scored)
                else:
                    action.reasoning = "Payment decision based on composite priority score."

            # Strategy-level description
            base_desc = STRATEGY_SUMMARIES.get(strat.name, "Balanced payment strategy.")
            if pressure_note:
                strat.description = f"{pressure_note} {base_desc}"
            else:
                strat.description = base_desc

    def _generate_action_reason(
        self, action, scored_obl: ScoredObligation
    ) -> str:
        """Generate a one-sentence reasoning for a single action."""
        key = (action.action_label, scored_obl.dominant_factor)
        template = EXPLANATION_TEMPLATES.get(
            key,
            "Payment decision based on composite priority score of {score:.2f}.",
        )

        obl = scored_obl.obligation
        late_fee = float(obl.get("late_fee", 0.0))
        grace = int(obl.get("grace_days", 0))
        flexibility = float(obl.get("flexibility_score", 0.5))

        try:
            reason = template.format(
                vendor=scored_obl.vendor,
                days=max(0, scored_obl.days_to_due),
                late_fee=f"${late_fee:.2f}",
                grace=grace,
                flex=f"{flexibility:.0%}",
                score=scored_obl.score,
            )
        except (KeyError, IndexError):
            reason = f"Payment to {scored_obl.vendor} prioritized based on score {scored_obl.score:.2f}."

        return reason

    def _cash_pressure_narrative(self) -> str:
        """Generate cash pressure warning if applicable."""
        if self._timeline.opening_balance <= 0:
            return ""

        min_bal = min(self._timeline.daily_balances)
        threshold = LOW_CASH_THRESHOLD * self._timeline.opening_balance

        if min_bal < threshold:
            min_day = self._timeline.daily_balances.index(min_bal)
            return (
                f"WARNING: Cash is projected to fall to ${min_bal:.2f} "
                f"on day {min_day} — liquidity is critically low."
            )
        return ""
