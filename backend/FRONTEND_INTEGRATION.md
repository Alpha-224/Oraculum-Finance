# CashFlow Guardian — Backend → Frontend Integration Guide

**Author:** Backend Logic Lead  
**Date:** 2026-03-26  
**Backend Engine Version:** 1.0.0  
**API Base URL:** `http://localhost:5001`

---

## 1. What the Backend Does

The Decision Engine backend consumes `data_layer/master_financial_data.json` (the single, append-only financial ledger) and produces a JSON response containing:

1. **A 30-day cash timeline** — day-by-day projected cash balances
2. **Exactly 3 payment strategies** — each optimized for a different objective
3. **Per-obligation action plans** — every obligation gets a recommended action in each strategy
4. **Survival probability** — Monte Carlo–derived probability that the business stays solvent
5. **Obligation summary** — aggregate counts and amounts by action category

The backend is **READ-ONLY** — it never writes to the ledger. All data mutations happen in `data_layer/`.

---

## 2. Architecture Overview

```
master_financial_data.json
         │
         ▼  load_master_json()
   ┌──────────────────────────────────────┐
   │   DECISION ENGINE  (/backend/)       │
   │                                      │
   │  1. CashSimulator    → 30-day cash   │
   │  2. ObligationScorer → scored obls   │
   │  3. MonteCarloEngine → survival %    │
   │  4. BeamSearchPlanner→ 3 strategies  │
   │  5. ExplanationEngine→ reasoning     │
   │  6. ResponseSerializer→ final JSON   │
   └──────────────────────────────────────┘
         │
         ▼  HTTP 200 JSON
   Flutter Frontend (you)
```

### Backend Files

| File | Purpose |
|------|---------|
| `config.py` | All tunable constants (horizon, beam width, MC runs, weights) |
| `loader.py` | Reads `master_financial_data.json` from `data_layer/` |
| `simulator.py` | Produces 30-day deterministic cash timeline |
| `scorer.py` | Scores each obligation on Urgency/Monetary/Operational/Rigidity |
| `monte_carlo.py` | 1000-run simulation to estimate survival probability |
| `planner.py` | Beam search producing 3 distinct strategies |
| `explainer.py` | Generates plain-English reasoning for every action |
| `serializer.py` | Assembles the full `DecisionResponse` JSON |
| `api.py` | Flask server exposing two REST endpoints |

---

## 3. API Endpoints

### 3.1 `GET /api/health`

**Purpose:** Verify the backend is running and the data file exists.

**Request:**
```
GET http://localhost:5001/api/health
```

**Response (200):**
```json
{
  "status": "ok",
  "master_json_exists": true,
  "last_updated": "2026-03-25T21:08:15Z",
  "record_counts": {
    "transactions": 5,
    "obligations": 3,
    "receivables": 2
  }
}
```

**Flutter usage:** Call this on app startup to verify backend connectivity before showing the dashboard.

---

### 3.2 `POST /api/decision`

**Purpose:** Run the full decision engine and return 3 strategies + timeline.

**Request:**
```
POST http://localhost:5001/api/decision
Content-Type: application/json

{
  "horizon_days": 30    // optional — defaults to 30
}
```

**Response (200):** Full `DecisionResponse` JSON (see Section 4 below).

**Error Response (500):**
```json
{
  "error": "Description of what went wrong",
  "trace": "Full Python traceback"
}
```

**Flutter usage:**
```dart
final response = await http.post(
  Uri.parse('http://localhost:5001/api/decision'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({'horizon_days': 30}),
);
final data = jsonDecode(response.body);

// data['strategies'][0] → Penalty Minimizer
// data['strategies'][1] → Operation Protector
// data['strategies'][2] → Relationship Preserver
// data['timeline']['balances'] → 30-day chart data
// data['survival_probability'] → top-level risk number
```

---

## 4. Full Response Schema — `DecisionResponse`

This is the complete JSON structure returned by `POST /api/decision`. Every field described here is **contractual** — it will always be present with the documented type.

### 4.1 Top-Level Structure

```json
{
  "generated_at":         "2026-03-26T21:18:15Z",
  "horizon_days":         30,
  "opening_balance":      3825.0,
  "timeline":             { ... },
  "survival_probability": 0.82,
  "risk_label":           "MODERATE_RISK",
  "strategies":           [ ... ],
  "obligation_summary":   { ... },
  "metadata":             { ... }
}
```

| Field | Type | Description | Display Location |
|-------|------|-------------|-----------------|
| `generated_at` | `string` (ISO 8601) | When this analysis was generated | Header / footer timestamp |
| `horizon_days` | `int` | Always 30 | Subtitle: "30-Day Cash Forecast" |
| `opening_balance` | `float` | Today's cash position | Hero card: "Current Balance" |
| `survival_probability` | `float` (0–1) | From Strategy 1 (Penalty Minimizer) | **Primary risk indicator** — display as percentage |
| `risk_label` | `string` | One of: `LOW_RISK`, `MODERATE_RISK`, `HIGH_RISK`, `CRITICAL_RISK` | Color-coded risk badge |

---

### 4.2 `timeline` Object — THE CHART DATA

**This powers the main cash-flow chart on the dashboard.**

```json
"timeline": {
  "dates":            ["2026-03-26", "2026-03-27", ..., "2026-04-24"],
  "balances":         [3825.0, 3825.0, ..., 3825.0],
  "minimum_cash":     1200.0,
  "first_breach_day": null,
  "total_inflows":    8500.0,
  "total_outflows":   10300.0,
  "net_position":     -1800.0
}
```

| Field | Type | Guarantee | Frontend Usage |
|-------|------|-----------|---------------|
| `dates` | `string[]` | **Always exactly 30 entries**, YYYY-MM-DD | X-axis labels on chart |
| `balances` | `float[]` | **Always exactly 30 entries**, rounded to 2 decimals. `balances[0]` = opening balance | Y-axis values on chart. **Draw a red line at y=0** to show danger zone |
| `minimum_cash` | `float` | Lowest point in the 30 days | Display as "Lowest projected cash" |
| `first_breach_day` | `int \| null` | `null` if cash never goes negative; integer day index (0-29) if it does. **Never omitted** | If non-null, highlight that date on the chart with a warning marker |
| `total_inflows` | `float` | Sum of expected inflows | Show in summary card: "Expected Income" |
| `total_outflows` | `float` | Sum of scheduled payments | Show in summary card: "Total Obligations" |
| `net_position` | `float` | `total_inflows - total_outflows` | Show as "Net Cash Flow" — **red if negative** |

#### Chart Recommendations
- Use a **line chart** or **area chart** with the 30 dates on X, balances on Y
- Draw a **red dashed line at y=0** (the insolvency threshold)
- If `first_breach_day` is not null, mark that point with a ⚠️ icon
- Color the area below 0 in red to visually show cash danger

---

### 4.3 `strategies` Array — THE THREE STRATEGIES

**Always exactly 3 elements, always in this order:**

| Index | Name | What It Optimizes | Suggested UI Color |
|-------|------|-------------------|-------------------|
| `[0]` | `Penalty Minimizer` | Minimize total late fees | 🟢 Green / financial |
| `[1]` | `Operation Protector` | Pay all critical vendors first | 🔵 Blue / operational |
| `[2]` | `Relationship Preserver` | Protect rigid vendor relationships | 🟡 Amber / relational |

#### Single Strategy Object

```json
{
  "name":                 "Penalty Minimizer",
  "description":          "Prioritizes full payment of high-penalty obligations to minimize total late fees.",
  "total_payments":       3130.0,
  "total_deferred":       0.0,
  "total_late_fees":      0.0,
  "objective_score":      0.0,
  "survival_probability": 1.0,
  "risk_label":           "LOW_RISK",
  "risk_metrics": {
    "mean_ending_balance": 3825.0,
    "p10_ending_balance":  3825.0,
    "p90_ending_balance":  3825.0,
    "expected_shortfall":  0.0
  },
  "actions": [ ... ]
}
```

| Field | Type | Frontend Usage |
|-------|------|---------------|
| `name` | `string` | Tab/card title |
| `description` | `string` | Strategy explanation text. May start with "WARNING:" if cash pressure is detected — display this prominently if present |
| `total_payments` | `float` | "Total to pay: ₹X" |
| `total_deferred` | `float` | "Deferred: ₹X" |
| `total_late_fees` | `float` | "Late fees incurred: ₹X" — highlight in red if > 0 |
| `objective_score` | `float` | Internal quality score (lower = better) — can show as "Plan Score" |
| `survival_probability` | `float` (0–1) | **Per-strategy survival %** — display as percentage with color coding |
| `risk_label` | `string` | Badge color: `LOW_RISK` → green, `MODERATE_RISK` → amber, `HIGH_RISK` → orange, `CRITICAL_RISK` → red |
| `risk_metrics.mean_ending_balance` | `float` | "Expected cash at day 30" |
| `risk_metrics.p10_ending_balance` | `float` | "Worst-case (10th percentile)" — show in risk details |
| `risk_metrics.p90_ending_balance` | `float` | "Best-case (90th percentile)" — show in risk details |
| `risk_metrics.expected_shortfall` | `float` | Average cash deficit when breach occurs — 0.0 = no breaches |

---

### 4.4 `actions` Array — INDIVIDUAL OBLIGATION DECISIONS

**Each strategy contains exactly one action per obligation.** The count of `actions[]` is identical across all 3 strategies.

```json
{
  "obligation_id":  "obl_20240325_a1b2c3d4",
  "vendor":         "Coffee Beans Supply Co",
  "amount":         950.0,
  "paid_amount":    950.0,
  "paid_fraction":  1.0,
  "action_label":   "PAY_NOW",
  "due_date":       "2024-03-25",
  "reasoning":      "Payment to Coffee Beans Supply Co is due in 0 day(s) — immediate action required."
}
```

| Field | Type | Frontend Usage |
|-------|------|---------------|
| `obligation_id` | `string` | Internal key — use to link across strategies |
| `vendor` | `string` | **Display prominently** — the vendor/payee name |
| `amount` | `float` | Total obligation amount |
| `paid_amount` | `float` | What this strategy recommends paying now. Always ≤ `amount` |
| `paid_fraction` | `float` (0.0–1.0) | Percentage paid — always in 10% increments (0, 0.1, 0.2, …, 1.0) |
| `action_label` | `string` | **THE PRIMARY UI ELEMENT** — see table below |
| `due_date` | `string` (YYYY-MM-DD) | When the payment is due |
| `reasoning` | `string` | **Always non-empty.** Plain-English one-liner explaining WHY this action was chosen |

#### Action Labels → UI Treatment

| `action_label` | Badge Color | Badge Text | Meaning |
|----------------|-------------|------------|---------|
| `PAY_NOW` | 🔴 Red | "Pay Now" | Must be settled immediately — due within 3 days |
| `PAY_SCHEDULED` | 🟢 Green | "Scheduled" | On track — pay on due date as normal |
| `PARTIAL` | 🟠 Orange | "Partial" | Negotiate partial payment with vendor |
| `DELAY` | 🟡 Yellow | "Defer" | Safe to defer — request extension |
| `NEGOTIATE` | 🟡 Yellow | "Negotiate" | Vendor is flexible — proactively renegotiate terms |

---

### 4.5 `obligation_summary` Object — AGGREGATE DASHBOARD VIEW

**Reflects the first strategy (Penalty Minimizer) for the top-level summary view.**

```json
"obligation_summary": {
  "total_count":    3,
  "total_amount":   3130.0,
  "critical_count": 2,
  "overdue_count":  3,
  "by_action_label": {
    "PAY_NOW": { "count": 3, "amount": 3130.0 }
  }
}
```

| Field | Type | Frontend Usage |
|-------|------|---------------|
| `total_count` | `int` | "12 obligations" |
| `total_amount` | `float` | "Total owed: ₹18,500" |
| `critical_count` | `int` | "3 critical" — red badge |
| `overdue_count` | `int` | "1 overdue" — red badge |
| `by_action_label` | `object` | Pie chart or bucket cards — one per label |

#### Obligation Bucket Cards (recommended layout)

| Bucket Label | Action Labels | Badge | Card Content |
|-------------|---------------|-------|-------------|
| **Pay Now** | `PAY_NOW` | 🔴 | Count + total ₹ |
| **Partial Payment** | `PARTIAL` | 🟠 | Count + total ₹ |
| **Delay / Negotiate** | `DELAY`, `NEGOTIATE` | 🟡 | Count + total ₹ |
| **Scheduled** | `PAY_SCHEDULED` | 🟢 | Count + total ₹ |

---

### 4.6 `metadata` Object

```json
"metadata": {
  "master_json_last_updated": "2026-03-25T21:08:15Z",
  "transaction_count":        5,
  "obligation_count":         3,
  "receivable_count":         2,
  "monte_carlo_runs":         1000,
  "beam_width":               10,
  "engine_version":           "1.0.0"
}
```

| Field | Frontend Usage |
|-------|---------------|
| `master_json_last_updated` | "Data last updated: March 25, 2026" |
| `transaction_count`, `obligation_count`, `receivable_count` | Footer: "Based on 5 transactions, 3 obligations, 2 receivables" |
| `engine_version` | Footer: "Engine v1.0.0" |

---

## 5. Recommended Flutter Screen Layout

### Screen 1: Dashboard (Main View)

```
┌─────────────────────────────────────────────┐
│  CashFlow Guardian                          │
│  ─────────────────────────────              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Opening  │ │ Survival │ │ Risk     │    │
│  │ Balance  │ │ Prob.    │ │ Label    │    │
│  │ ₹3,825   │ │ 82%     │ │ MODERATE │    │
│  └──────────┘ └──────────┘ └──────────┘    │
│                                             │
│  📊 30-Day Cash Forecast                    │
│  ┌─────────────────────────────────────┐    │
│  │  Line chart: dates[] vs balances[]  │    │
│  │  Red dashed line at y=0             │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  Obligation Summary                         │
│  ┌────────┐┌────────┐┌────────┐┌────────┐  │
│  │Pay Now ││Partial ││Defer   ││On Track│  │
│  │🔴 3    ││🟠 2    ││🟡 2    ││🟢 5    │  │
│  │₹4,200  ││₹3,800  ││₹2,400  ││₹8,100  │  │
│  └────────┘└────────┘└────────┘└────────┘  │
│                                             │
│  ⚠️ Cash pressure warning (if present)      │
└─────────────────────────────────────────────┘
```

### Screen 2: Strategy Comparison

```
┌─────────────────────────────────────────────┐
│  Payment Strategies                         │
│  ─────────────────                          │
│  [Penalty Min.] [Op. Protector] [Rel. Pres.]│
│                                             │
│  Selected: Penalty Minimizer                │
│  "Prioritizes full payment of high-penalty  │
│   obligations to minimize total late fees." │
│                                             │
│  Survival: 82%  │  Late Fees: ₹0           │
│  Total Pay: ₹7,200  │  Deferred: ₹1,100    │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │ Obligation List (sorted by action)    │  │
│  ├───────────────────────────────────────┤  │
│  │ 🔴 PAY NOW  City Electricity Board    │  │
│  │   ₹1,200 due Mar 28   Pay: ₹1,200    │  │
│  │   "Late fee of $180.00 exceeds..."    │  │
│  ├───────────────────────────────────────┤  │
│  │ 🟢 SCHEDULED  Office Rent            │  │
│  │   ₹2,000 due Apr 1    Pay: ₹2,000    │  │
│  │   "Landlord requires on-time..."      │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## 6. Important Frontend Guarantees (Backend Contract)

These are **hard guarantees** from the backend. You can rely on them without defensive checks:

| Guarantee | Detail |
|-----------|--------|
| **30 timeline entries** | `timeline.dates[]` and `timeline.balances[]` always have exactly 30 elements |
| **3 strategies** | `strategies[]` always has exactly 3 elements, always in order: Penalty Minimizer → Operation Protector → Relationship Preserver |
| **Same action count** | Every `strategy.actions[]` has the same count = number of obligations |
| **Valid action labels** | `action_label` is always one of: `PAY_NOW`, `PAY_SCHEDULED`, `PARTIAL`, `DELAY`, `NEGOTIATE` |
| **Valid risk labels** | `risk_label` is always one of: `LOW_RISK`, `MODERATE_RISK`, `HIGH_RISK`, `CRITICAL_RISK` |
| **Non-empty reasoning** | `action.reasoning` is always a non-empty string — never null, never `""` |
| **Paid ≤ Amount** | `action.paid_amount` is always ≤ `action.amount` |
| **Fraction increments** | `action.paid_fraction` is always one of: 0, 0.1, 0.2, …, 0.9, 1.0 |
| **Survival ∈ [0,1]** | `survival_probability` is always between 0.0 and 1.0 |
| **Breach day nullable** | `timeline.first_breach_day` is `null` (not omitted) when cash never goes negative |
| **Balances are floats** | All `timeline.balances[]` values are `float`, rounded to 2 decimal places |

---

## 7. Risk Label Color Mapping

```dart
Color riskColor(String riskLabel) {
  switch (riskLabel) {
    case 'LOW_RISK':       return Colors.green;
    case 'MODERATE_RISK':  return Colors.amber;
    case 'HIGH_RISK':      return Colors.orange;
    case 'CRITICAL_RISK':  return Colors.red;
    default:               return Colors.grey;
  }
}

String riskEmoji(String riskLabel) {
  switch (riskLabel) {
    case 'LOW_RISK':       return '✅';
    case 'MODERATE_RISK':  return '⚠️';
    case 'HIGH_RISK':      return '🔶';
    case 'CRITICAL_RISK':  return '🔴';
    default:               return '❓';
  }
}
```

---

## 8. Action Label Color Mapping

```dart
Color actionColor(String label) {
  switch (label) {
    case 'PAY_NOW':        return Colors.red;
    case 'PAY_SCHEDULED':  return Colors.green;
    case 'PARTIAL':        return Colors.orange;
    case 'DELAY':          return Colors.amber;
    case 'NEGOTIATE':      return Colors.amber;
    default:               return Colors.grey;
  }
}

IconData actionIcon(String label) {
  switch (label) {
    case 'PAY_NOW':        return Icons.warning;
    case 'PAY_SCHEDULED':  return Icons.check_circle;
    case 'PARTIAL':        return Icons.pie_chart;
    case 'DELAY':          return Icons.schedule;
    case 'NEGOTIATE':      return Icons.handshake;
    default:               return Icons.help;
  }
}
```

---

## 9. How to Start the Backend

```bash
# From the repo root
cd backend
pip install -r requirements.txt
cd ..
python backend/api.py
# Server starts on http://localhost:5001
```

The server uses Flask with CORS enabled — Flutter web and mobile clients can connect without proxy configuration.

---

## 10. Error Handling in Flutter

```dart
try {
  final response = await http.post(
    Uri.parse('http://localhost:5001/api/decision'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'horizon_days': 30}),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    // Check for error key just in case
    if (data.containsKey('error')) {
      showErrorDialog(data['error']);
    } else {
      displayDashboard(data);
    }
  } else {
    final error = jsonDecode(response.body);
    showErrorDialog(error['error'] ?? 'Unknown server error');
  }
} catch (e) {
  showErrorDialog('Cannot connect to backend. Is it running on port 5001?');
}
```

---

## 11. Cash Pressure Warning Detection

If any strategy's `description` starts with `"WARNING:"`, it means cash drops below 20% of opening balance. You should:

1. Display a banner/alert at the top of the dashboard
2. Use red/orange theming for the affected area
3. Highlight the minimum cash point on the chart

```dart
bool hasCashPressure(Map<String, dynamic> strategy) {
  return strategy['description'].startsWith('WARNING:');
}
```

---

## 12. Quick Data Model (Dart)

```dart
class DecisionResponse {
  final String generatedAt;
  final int horizonDays;
  final double openingBalance;
  final Timeline timeline;
  final double survivalProbability;
  final String riskLabel;
  final List<Strategy> strategies;
  final ObligationSummary obligationSummary;
  final Metadata metadata;
}

class Timeline {
  final List<String> dates;       // 30 entries
  final List<double> balances;    // 30 entries
  final double minimumCash;
  final int? firstBreachDay;      // null if no breach
  final double totalInflows;
  final double totalOutflows;
  final double netPosition;
}

class Strategy {
  final String name;
  final String description;
  final double totalPayments;
  final double totalDeferred;
  final double totalLateFees;
  final double objectiveScore;
  final double survivalProbability;
  final String riskLabel;
  final RiskMetrics riskMetrics;
  final List<Action> actions;
}

class Action {
  final String obligationId;
  final String vendor;
  final double amount;
  final double paidAmount;
  final double paidFraction;
  final String actionLabel;      // PAY_NOW | PAY_SCHEDULED | PARTIAL | DELAY | NEGOTIATE
  final String dueDate;
  final String reasoning;
}

class RiskMetrics {
  final double meanEndingBalance;
  final double p10EndingBalance;
  final double p90EndingBalance;
  final double expectedShortfall;
}

class ObligationSummary {
  final int totalCount;
  final double totalAmount;
  final int criticalCount;
  final int overdueCount;
  final Map<String, ActionBucket> byActionLabel;
}

class ActionBucket {
  final int count;
  final double amount;
}

class Metadata {
  final String masterJsonLastUpdated;
  final int transactionCount;
  final int obligationCount;
  final int receivableCount;
  final int monteCarloRuns;
  final int beamWidth;
  final String engineVersion;
}
```

---

## 13. Version Contract

Any change to the response schema requires bumping `metadata.engine_version`. Check this field if you need to handle backward compatibility:

```dart
final version = data['metadata']['engine_version'];
assert(version == '1.0.0', 'Backend version mismatch — update frontend models');
```

---

*End of Integration Guide — Decision Engine Backend v1.0.0*
