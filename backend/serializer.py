"""
serializer.py — Response Serializer.

Assembles the complete DecisionResponse JSON structure per PRD Section 10.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from .config import ENGINE_VERSION, HORIZON_DAYS, MC_RUNS, BEAM_WIDTH, logger
from .planner import Strategy, Action, RiskMetrics
from .simulator import CashTimeline


class ResponseSerializer:
    """Builds the final DecisionResponse JSON from engine outputs.

    Args:
        timeline: CashTimeline from the simulator.
        strategies: List of 3 Strategy objects from the planner.
        master_data: The full master JSON dict.
    """

    def __init__(
        self,
        timeline: CashTimeline,
        strategies: list[Strategy],
        master_data: dict,
    ) -> None:
        self._timeline = timeline
        self._strategies = strategies
        self._data = master_data

    def build(self) -> dict:
        """Build the complete DecisionResponse dict.

        Returns:
            A JSON-serializable dict matching the PRD Section 10 schema.
        """
        first_strat = self._strategies[0] if self._strategies else None

        response = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "horizon_days": HORIZON_DAYS,
            "opening_balance": self._timeline.opening_balance,
            "timeline": self._build_timeline(),
            "survival_probability": first_strat.survival_probability if first_strat else 1.0,
            "risk_label": first_strat.risk_label if first_strat else "LOW_RISK",
            "strategies": [self._serialize_strategy(s) for s in self._strategies],
            "obligation_summary": self._build_obligation_summary(),
            "metadata": self._build_metadata(),
        }

        return response

    # ─── Private section builders ───────────────────────────────────────

    def _build_timeline(self) -> dict:
        """Build the timeline section (PRD 10.2)."""
        return {
            "dates": self._timeline.daily_dates,
            "balances": [round(b, 2) for b in self._timeline.daily_balances],
            "minimum_cash": round(self._timeline.minimum_cash, 2),
            "first_breach_day": self._timeline.first_breach_day,
            "total_inflows": round(self._timeline.total_inflows, 2),
            "total_outflows": round(self._timeline.total_outflows, 2),
            "net_position": round(self._timeline.net_position, 2),
        }

    def _serialize_strategy(self, strategy: Strategy) -> dict:
        """Serialize a single strategy (PRD 10.3)."""
        return {
            "name": strategy.name,
            "description": strategy.description,
            "total_payments": strategy.total_payments,
            "total_deferred": strategy.total_deferred,
            "total_late_fees": strategy.total_late_fees,
            "objective_score": strategy.objective_score,
            "survival_probability": strategy.survival_probability,
            "risk_label": strategy.risk_label,
            "risk_metrics": {
                "mean_ending_balance": strategy.risk_metrics.mean_ending_balance,
                "p10_ending_balance": strategy.risk_metrics.p10_ending_balance,
                "p90_ending_balance": strategy.risk_metrics.p90_ending_balance,
                "expected_shortfall": strategy.risk_metrics.expected_shortfall,
            },
            "actions": [self._serialize_action(a) for a in strategy.actions],
        }

    @staticmethod
    def _serialize_action(action: Action) -> dict:
        """Serialize a single action within a strategy."""
        return {
            "obligation_id": action.obligation_id,
            "vendor": action.vendor,
            "amount": action.amount,
            "paid_amount": action.paid_amount,
            "paid_fraction": action.paid_fraction,
            "action_label": action.action_label,
            "due_date": action.due_date,
            "reasoning": action.reasoning,
        }

    def _build_obligation_summary(self) -> dict:
        """Build the obligation_summary section (PRD 10.4).

        Reflects Strategy 1 (Penalty Minimizer) action distribution.
        """
        obligations = self._data.get("obligations", [])
        total_count = len(obligations)
        total_amount = sum(float(o["amount"]) for o in obligations)
        critical_count = sum(1 for o in obligations if o.get("is_critical", False))

        from datetime import date
        overdue_count = sum(
            1 for o in obligations
            if o["due_date"] < date.today().isoformat()
        )

        # Action distribution from first strategy
        by_label: dict[str, dict] = {}
        if self._strategies:
            for action in self._strategies[0].actions:
                label = action.action_label
                if label not in by_label:
                    by_label[label] = {"count": 0, "amount": 0.0}
                by_label[label]["count"] += 1
                by_label[label]["amount"] = round(
                    by_label[label]["amount"] + action.paid_amount, 2
                )

        return {
            "total_count": total_count,
            "total_amount": round(total_amount, 2),
            "critical_count": critical_count,
            "overdue_count": overdue_count,
            "by_action_label": by_label,
        }

    def _build_metadata(self) -> dict:
        """Build the metadata section (PRD 10.5)."""
        meta = self._data.get("metadata", {})
        return {
            "master_json_last_updated": meta.get("last_updated", ""),
            "transaction_count": len(self._data.get("transactions", [])),
            "obligation_count": len(self._data.get("obligations", [])),
            "receivable_count": len(self._data.get("receivables", [])),
            "monte_carlo_runs": MC_RUNS,
            "beam_width": BEAM_WIDTH,
            "engine_version": ENGINE_VERSION,
        }
