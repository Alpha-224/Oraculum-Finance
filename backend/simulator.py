"""
simulator.py — Deterministic 30-day cash position timeline.

Produces a CashTimeline by combining opening balance, scheduled inflows
(from receivables), and outflows (from obligations) day-by-day.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from .config import HORIZON_DAYS, logger


@dataclass
class CashTimeline:
    """30-day cash position timeline output object."""

    opening_balance: float          # C(0)
    daily_balances: list[float]     # 30 entries, index 0 = today
    daily_dates: list[str]          # 30 YYYY-MM-DD strings
    minimum_cash: float             # lowest point in the 30-day window
    first_breach_day: Optional[int] # day index where cash < 0, or None
    total_inflows: float            # sum of all inflows over horizon
    total_outflows: float           # sum of all scheduled payments over horizon
    net_position: float             # total_inflows - total_outflows


class CashSimulator:
    """Deterministic cash-flow simulator.

    Args:
        data: The full master JSON dict (transactions, obligations, receivables).
        horizon_days: Number of days to simulate. Defaults to HORIZON_DAYS.
    """

    def __init__(self, data: dict, horizon_days: int = HORIZON_DAYS) -> None:
        self._data = data
        self._horizon = horizon_days

    def run(self) -> CashTimeline:
        """Run the deterministic simulation and return a CashTimeline."""
        opening_balance = self._compute_opening_balance()
        today = date.today()

        inflows_by_day = self._build_inflow_schedule(today)
        outflows_by_day = self._build_outflow_schedule(today)

        daily_balances, daily_dates = self._simulate_days(
            opening_balance, today, inflows_by_day, outflows_by_day
        )

        total_inflows = sum(inflows_by_day.get(t, 0.0) for t in range(self._horizon))
        total_outflows = sum(outflows_by_day.get(t, 0.0) for t in range(self._horizon))
        minimum_cash = min(daily_balances)
        first_breach = self._find_first_breach(daily_balances)

        return CashTimeline(
            opening_balance=opening_balance,
            daily_balances=daily_balances,
            daily_dates=daily_dates,
            minimum_cash=minimum_cash,
            first_breach_day=first_breach,
            total_inflows=total_inflows,
            total_outflows=total_outflows,
            net_position=total_inflows - total_outflows,
        )

    # ─── Private Helpers ────────────────────────────────────────────────

    def _compute_opening_balance(self) -> float:
        """Extract C(0) from the last sorted transaction's running_balance."""
        transactions = self._data.get("transactions", [])
        if not transactions:
            logger.warning("Empty transactions[] — using C(0) = 0.0")
            return 0.0

        sorted_txns = sorted(transactions, key=lambda t: t["date"])
        return float(sorted_txns[-1]["running_balance"])

    def _build_inflow_schedule(self, today: date) -> dict[int, float]:
        """Build day-indexed dict of inflows from receivables.

        Fixed inflows (probability >= 0.95): full amount.
        Uncertain inflows (0.5 <= probability < 0.95): weighted by probability.
        Overdue receivables (is_overdue=True): treated as $0.
        """
        inflows: dict[int, float] = {}
        receivables = self._data.get("receivables", [])

        for rec in receivables:
            if rec.get("is_overdue", False):
                continue

            probability = float(rec.get("probability", 0.9))
            if probability < 0.5:
                continue

            expected = date.fromisoformat(rec["expected_date"])
            day_index = (expected - today).days

            if day_index < 0 or day_index >= self._horizon:
                continue

            amount = float(rec["amount"])
            if probability >= 0.95:
                weighted = amount
            else:
                weighted = amount * probability

            inflows[day_index] = inflows.get(day_index, 0.0) + weighted

        return inflows

    def _build_outflow_schedule(self, today: date) -> dict[int, float]:
        """Build day-indexed dict of outflows from obligations.

        Handles recurring obligations by expanding them within the horizon.
        """
        outflows: dict[int, float] = {}
        obligations = self._data.get("obligations", [])

        for obl in obligations:
            self._add_obligation_to_schedule(obl, today, outflows)

        return outflows

    def _add_obligation_to_schedule(
        self, obl: dict, today: date, outflows: dict[int, float]
    ) -> None:
        """Add a single obligation (and its recurrences) to the outflow schedule."""
        due = date.fromisoformat(obl["due_date"])
        amount = float(obl["amount"])
        is_recurring = obl.get("recurring_payment", False)
        periodicity = obl.get("periodicity")

        # Add the base obligation
        day_index = (due - today).days
        if 0 <= day_index < self._horizon:
            outflows[day_index] = outflows.get(day_index, 0.0) + amount

        # Expand recurring obligations
        if is_recurring and periodicity:
            delta = self._periodicity_to_delta(periodicity)
            if delta:
                next_due = due + delta
                while True:
                    idx = (next_due - today).days
                    if idx >= self._horizon:
                        break
                    if idx >= 0:
                        outflows[idx] = outflows.get(idx, 0.0) + amount
                    next_due += delta

    @staticmethod
    def _periodicity_to_delta(periodicity: str) -> Optional[timedelta]:
        """Convert periodicity string to timedelta."""
        mapping = {
            "daily": timedelta(days=1),
            "weekly": timedelta(days=7),
            "monthly": timedelta(days=30),
        }
        return mapping.get(periodicity)

    def _simulate_days(
        self,
        opening: float,
        today: date,
        inflows: dict[int, float],
        outflows: dict[int, float],
    ) -> tuple[list[float], list[str]]:
        """Iterate over horizon days computing daily cash balances."""
        balances: list[float] = []
        dates: list[str] = []
        cash = opening

        for t in range(self._horizon):
            if t == 0:
                # Day 0 = today, start with opening balance then apply flows
                cash = opening + inflows.get(t, 0.0) - outflows.get(t, 0.0)
            else:
                cash = cash + inflows.get(t, 0.0) - outflows.get(t, 0.0)

            balances.append(round(cash, 2))
            dates.append((today + timedelta(days=t)).isoformat())

        return balances, dates

    @staticmethod
    def _find_first_breach(balances: list[float]) -> Optional[int]:
        """Find the first day index where cash drops below zero."""
        for i, bal in enumerate(balances):
            if bal < 0:
                return i
        return None
