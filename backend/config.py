"""
config.py — All constants, tunable parameters, and shared logging for the Decision Engine.

Every tunable value lives here. No magic numbers elsewhere.
"""

import logging

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("decision_engine")

# ─── Simulation ──────────────────────────────────────────────────────────────
HORIZON_DAYS: int = 30  # Rolling simulation window in days

# ─── Monte Carlo ─────────────────────────────────────────────────────────────
MC_RUNS: int = 1000  # Number of Monte Carlo iterations

# Delay distribution parameters per client tier (Normal distribution)
DELAY_PARAMS: dict[str, dict[str, int]] = {
    "critical": {"mean": 0, "std": 2},    # reliable clients: ±2 days
    "standard": {"mean": 3, "std": 5},    # typical: ~3 days late on average
    "minor":    {"mean": 7, "std": 10},   # unreliable: often 1–2 weeks late
}

# ─── Scoring ─────────────────────────────────────────────────────────────────
URGENCY_DECAY_K: float = 0.15  # Exponential decay constant for U score

VITALITY_MAP: dict[str, int] = {
    "critical": 10,
    "standard": 5,
    "minor":    1,
}

# ─── Planner ─────────────────────────────────────────────────────────────────
BEAM_WIDTH: int = 10  # Beam search breadth
INSOLVENCY_PENALTY: float = 1000.0  # J penalty for any cash-negative plan

PARTIAL_FRACTIONS: list[float] = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

TIER_WEIGHTS: dict[str, float] = {
    "critical": 1.0,
    "standard": 0.5,
    "minor":    0.1,
}

DISTINCT_THRESHOLD: float = 0.80  # Max overlap before strategy is re-selected

# ─── Explainer ───────────────────────────────────────────────────────────────
LOW_CASH_THRESHOLD: float = 0.20  # Fraction of C(0); below = cash pressure warning

# ─── API ─────────────────────────────────────────────────────────────────────
FLASK_PORT: int = 5001

# ─── Engine Metadata ─────────────────────────────────────────────────────────
ENGINE_VERSION: str = "1.0.0"
