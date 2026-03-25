"""
planner.py — Beam Search Strategy Planner.

Generates candidate payment plans via beam search, evaluates them using the
objective function J, runs Monte Carlo on each, and selects three distinct
strategies optimized for different objectives.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .config import (
    BEAM_WIDTH,
    HORIZON_DAYS,
    INSOLVENCY_PENALTY,
    PARTIAL_FRACTIONS,
    TIER_WEIGHTS,
    DISTINCT_THRESHOLD,
    logger,
)
from .explainer import ExplanationEngine
from .monte_carlo import MonteCarloEngine, MonteCarloResult
from .scorer import ScoredObligation
from .simulator import CashTimeline


@dataclass
class Action:
    """A single payment action for one obligation within a strategy."""

    obligation_id: str
    vendor: str
    amount: float           # total obligation amount
    paid_amount: float      # amount × paid_fraction
    paid_fraction: float    # 0.0 – 1.0
    action_label: str       # PAY_NOW | PAY_SCHEDULED | PARTIAL | DELAY | NEGOTIATE
    due_date: str
    reasoning: str = ""     # filled by ExplanationEngine


@dataclass
class RiskMetrics:
    """Subset of MonteCarloResult exposed in strategy output."""

    mean_ending_balance: float
    p10_ending_balance: float
    p90_ending_balance: float
    expected_shortfall: float


@dataclass
class Strategy:
    """A complete payment plan with associated metrics."""

    name: str
    description: str
    actions: list[Action]
    total_payments: float
    total_deferred: float
    total_late_fees: float
    objective_score: float
    survival_probability: float
    risk_label: str
    risk_metrics: RiskMetrics


# ─── Internal beam state ────────────────────────────────────────────────────

@dataclass
class _BeamState:
    """Internal state of a beam candidate during search."""

    cash: float
    payments: dict[str, float]   # obligation_id → paid_fraction
    financial_loss: float = 0.0
    operational_loss: float = 0.0
    relationship_loss: float = 0.0
    j_score: float = 0.0


class BeamSearchPlanner:
    """Generates 3 distinct strategies via beam search.

    Args:
        timeline: CashTimeline from the deterministic simulator.
        scored_obligations: List of ScoredObligation from scorer.
        receivables: List of receivable dicts from master JSON.
    """

    def __init__(
        self,
        timeline: CashTimeline,
        scored_obligations: list[ScoredObligation],
        receivables: list[dict],
    ) -> None:
        self._timeline = timeline
        self._scored = scored_obligations
        self._receivables = receivables

    def generate_strategies(self) -> list[Strategy]:
        """Run beam search, evaluate terminal states, select 3 strategies.

        Returns:
            List of exactly 3 Strategy objects.
        """
        if not self._scored:
            return self._empty_strategies()

        terminal_states = self._beam_search()
        strategies = self._select_three(terminal_states)

        # Fill reasoning via ExplanationEngine
        scored_map = {s.obligation_id: s for s in self._scored}
        explainer = ExplanationEngine(self._timeline)
        explainer.explain_strategies(strategies, scored_map)

        return strategies

    # ─── Beam Search ────────────────────────────────────────────────────

    def _beam_search(self) -> list[_BeamState]:
        """Execute the beam search algorithm."""
        root = _BeamState(
            cash=self._timeline.opening_balance,
            payments={},
        )
        beam = [root]

        # Expand one obligation at a time (sorted by score descending)
        for scored_obl in self._scored:
            next_beam: list[_BeamState] = []

            for state in beam:
                expansions = self._expand_state(state, scored_obl)
                next_beam.extend(expansions)

            # Prune: keep top BEAM_WIDTH by lowest J
            for s in next_beam:
                s.j_score = self._compute_j(s)

            next_beam.sort(key=lambda s: s.j_score)
            beam = next_beam[:BEAM_WIDTH]

        return beam

    def _expand_state(
        self, state: _BeamState, scored_obl: ScoredObligation
    ) -> list[_BeamState]:
        """Expand a beam state for one obligation into pay/partial/delay branches."""
        obl = scored_obl.obligation
        amount = scored_obl.amount
        flexibility = float(obl.get("flexibility_score", 0.5))
        expansions: list[_BeamState] = []

        # Branch 1: Pay in full (fraction = 1.0)
        if state.cash >= amount:
            new = self._clone_state(state)
            new.cash -= amount
            new.payments[scored_obl.obligation_id] = 1.0
            expansions.append(new)

        # Branch 2: Partial payment (best valid fraction)
        if flexibility > 0.0:
            fraction = self._choose_optimal_fraction(amount, state.cash)
            if 0.0 < fraction < 1.0:
                new = self._clone_state(state)
                new.cash -= amount * fraction
                new.payments[scored_obl.obligation_id] = fraction
                self._accrue_partial_loss(new, scored_obl, fraction)
                expansions.append(new)

        # Branch 3: Delay (fraction = 0.0) — always available
        new = self._clone_state(state)
        new.payments[scored_obl.obligation_id] = 0.0
        self._accrue_delay_loss(new, scored_obl)
        expansions.append(new)

        return expansions

    def _choose_optimal_fraction(
        self, amount: float, available_cash: float
    ) -> float:
        """Select the largest fraction f such that amount × f ≤ available_cash."""
        for f in reversed(PARTIAL_FRACTIONS):
            if amount * f <= available_cash:
                return f
        return 0.0

    def _accrue_partial_loss(
        self, state: _BeamState, scored_obl: ScoredObligation, fraction: float
    ) -> None:
        """Accrue proportional losses for a partial payment."""
        obl = scored_obl.obligation
        unpaid_fraction = 1.0 - fraction
        late_fee = float(obl.get("late_fee", 0.0))
        state.financial_loss += late_fee * unpaid_fraction

        tier = obl.get("relationship_tier", "standard")
        flexibility = float(obl.get("flexibility_score", 0.5))
        state.relationship_loss += (1.0 - flexibility) * unpaid_fraction

    def _accrue_delay_loss(
        self, state: _BeamState, scored_obl: ScoredObligation
    ) -> None:
        """Accrue full losses for delaying an obligation."""
        obl = scored_obl.obligation
        late_fee = float(obl.get("late_fee", 0.0))
        grace_days = int(obl.get("grace_days", 0))
        days_to_due = scored_obl.days_to_due

        # Only accrue late fee if delay exceeds grace period
        if days_to_due <= grace_days:
            state.financial_loss += late_fee

        tier = obl.get("relationship_tier", "standard")
        is_critical = obl.get("is_critical", False)

        if is_critical or tier == "critical":
            state.operational_loss += TIER_WEIGHTS.get(tier, 0.5)

        flexibility = float(obl.get("flexibility_score", 0.5))
        state.relationship_loss += 1.0 - flexibility

    def _compute_j(self, state: _BeamState) -> float:
        """Compute the objective function J for a beam state."""
        total_amount = sum(s.amount for s in self._scored) or 1.0
        n_obls = len(self._scored) or 1

        fin_norm = state.financial_loss / max(1.0, total_amount)
        ops_norm = state.operational_loss / max(1, n_obls)
        rel_norm = state.relationship_loss / max(1, n_obls)

        j = (fin_norm + ops_norm + rel_norm) / 3.0

        # Insolvency penalty: if cash went negative
        if state.cash < 0:
            j += INSOLVENCY_PENALTY

        return j

    @staticmethod
    def _clone_state(state: _BeamState) -> _BeamState:
        """Deep-copy a beam state."""
        return _BeamState(
            cash=state.cash,
            payments=dict(state.payments),
            financial_loss=state.financial_loss,
            operational_loss=state.operational_loss,
            relationship_loss=state.relationship_loss,
            j_score=state.j_score,
        )

    # ─── Strategy Selection ─────────────────────────────────────────────

    def _select_three(self, terminals: list[_BeamState]) -> list[Strategy]:
        """Select 3 distinct strategies from terminal states."""
        if not terminals:
            return self._empty_strategies()

        # Compute loss components for each terminal
        scored_terms = []
        for t in terminals:
            total_amount = sum(s.amount for s in self._scored) or 1.0
            n_obls = len(self._scored) or 1
            fin = t.financial_loss / max(1.0, total_amount)
            ops = t.operational_loss / max(1, n_obls)
            rel = t.relationship_loss / max(1, n_obls)
            scored_terms.append((t, fin, ops, rel))

        # Select best for each objective
        pen_min = self._select_best(scored_terms, key_idx=1)
        op_prot = self._select_best(scored_terms, key_idx=2, exclude=[pen_min])
        rel_pres = self._select_best(scored_terms, key_idx=3, exclude=[pen_min, op_prot])

        # Build strategies with MC
        strategies = [
            self._build_strategy("Penalty Minimizer", pen_min),
            self._build_strategy("Operation Protector", op_prot),
            self._build_strategy("Relationship Preserver", rel_pres),
        ]

        return strategies

    def _select_best(
        self,
        scored_terms: list[tuple],
        key_idx: int,
        exclude: list[_BeamState] | None = None,
    ) -> _BeamState:
        """Select the terminal with lowest loss for the given component."""
        exclude = exclude or []
        exclude_ids = {id(e) for e in exclude}

        candidates = [
            (t, losses)
            for t, *losses in scored_terms
            if id(t) not in exclude_ids
        ]

        if not candidates:
            # Fall back to any available terminal
            return scored_terms[0][0]

        # Sort by the relevant loss component
        candidates.sort(key=lambda x: x[1][key_idx - 1])
        return candidates[0][0]

    def _build_strategy(self, name: str, state: _BeamState) -> Strategy:
        """Build a Strategy from a terminal beam state."""
        actions = self._build_actions(state)
        total_payments = sum(a.paid_amount for a in actions)
        total_deferred = sum(a.amount - a.paid_amount for a in actions)
        total_late_fees = state.financial_loss

        # Run Monte Carlo
        mc_result = self._run_mc(state)
        survival = mc_result.survival_probability
        risk_label = self._risk_label(survival)

        return Strategy(
            name=name,
            description="",  # filled by ExplanationEngine
            actions=actions,
            total_payments=round(total_payments, 2),
            total_deferred=round(total_deferred, 2),
            total_late_fees=round(total_late_fees, 2),
            objective_score=round(state.j_score, 4),
            survival_probability=round(survival, 4),
            risk_label=risk_label,
            risk_metrics=RiskMetrics(
                mean_ending_balance=round(mc_result.mean_ending_balance, 2),
                p10_ending_balance=round(mc_result.p10_ending_balance, 2),
                p90_ending_balance=round(mc_result.p90_ending_balance, 2),
                expected_shortfall=round(mc_result.expected_shortfall, 2),
            ),
        )

    def _build_actions(self, state: _BeamState) -> list[Action]:
        """Build Action list from a terminal beam state."""
        actions: list[Action] = []

        for scored_obl in self._scored:
            obl_id = scored_obl.obligation_id
            fraction = state.payments.get(obl_id, 0.0)
            amount = scored_obl.amount
            paid_amount = round(amount * fraction, 2)
            label = self._classify_action(scored_obl, fraction)

            actions.append(Action(
                obligation_id=obl_id,
                vendor=scored_obl.vendor,
                amount=amount,
                paid_amount=paid_amount,
                paid_fraction=fraction,
                action_label=label,
                due_date=scored_obl.due_date,
            ))

        return actions

    def _classify_action(
        self, scored_obl: ScoredObligation, fraction: float
    ) -> str:
        """Classify an action per PRD Section 8.5."""
        obl = scored_obl.obligation
        flexibility = float(obl.get("flexibility_score", 0.5))

        if fraction == 1.0:
            if scored_obl.days_to_due <= 3:
                return "PAY_NOW"
            return "PAY_SCHEDULED"
        elif fraction > 0.0:
            return "PARTIAL"
        else:
            # fraction = 0.0
            if flexibility >= 0.7:
                return "NEGOTIATE"
            return "DELAY"

    def _run_mc(self, state: _BeamState) -> MonteCarloResult:
        """Run Monte Carlo simulation for a terminal state."""
        engine = MonteCarloEngine(
            self._receivables,
            self._timeline,
            state.payments,
            runs=200,  # Reduced for speed during planning; full 1000 in final
        )
        return engine.run()

    @staticmethod
    def _risk_label(survival: float) -> str:
        """Map survival probability to risk label."""
        if survival >= 0.85:
            return "LOW_RISK"
        elif survival >= 0.60:
            return "MODERATE_RISK"
        elif survival >= 0.40:
            return "HIGH_RISK"
        else:
            return "CRITICAL_RISK"

    # ─── Edge case: no obligations ──────────────────────────────────────

    def _empty_strategies(self) -> list[Strategy]:
        """Return 3 strategies with empty actions when there are no obligations."""
        empty_mc = MonteCarloResult(
            survival_probability=1.0,
            mean_ending_balance=self._timeline.opening_balance,
            p10_ending_balance=self._timeline.opening_balance,
            p90_ending_balance=self._timeline.opening_balance,
            expected_shortfall=0.0,
            breach_day_distribution=[],
        )
        metrics = RiskMetrics(
            mean_ending_balance=self._timeline.opening_balance,
            p10_ending_balance=self._timeline.opening_balance,
            p90_ending_balance=self._timeline.opening_balance,
            expected_shortfall=0.0,
        )
        names = ["Penalty Minimizer", "Operation Protector", "Relationship Preserver"]
        return [
            Strategy(
                name=n, description="", actions=[],
                total_payments=0.0, total_deferred=0.0, total_late_fees=0.0,
                objective_score=0.0, survival_probability=1.0,
                risk_label="LOW_RISK", risk_metrics=metrics,
            )
            for n in names
        ]
