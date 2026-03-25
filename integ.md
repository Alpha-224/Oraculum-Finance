# Oraculum / CashFlow Guardian

## Master Prompt PRD for Claude Opus

### Role

You are Claude Opus acting as a senior Flutter integration engineer and product implementer.

### Mission

Inspect the entire repo, understand the current Flutter frontend structure, and complete the remaining integration work for the app’s main flow, dashboard/simulation/account screens, and backend connectivity using the provided backend contract.

The app is a finance product called **ORACULUM**. The frontend already has the visual direction and core navigation theme. Your job is to turn the existing project into a fully working, well-structured Flutter app that consumes the backend response schema below and uses it to power the dashboard, simulation, and account experience.

Do not redesign the whole app from scratch unless necessary. Preserve the existing look and feel where possible. Prefer surgical, architecture-clean edits over broad rewrites.

---

## Product Summary

ORACULUM is a cash-flow decision app with a polished emerald/teal visual theme and an animated atmospheric background. The app flow is:

**login → main app with bottom navigation → dashboard / data submission / simulation / account**

The app should feel premium, readable, and finance-oriented.

### Visual direction

* Dark emerald/teal background theme
* White and green-tinted text colors that remain legible
* Title text should be **ORACULUM** in all caps and bold where used
* Keep the interface clean, modern, and calm rather than alarming
* Dashboard should present “days to zero” in a softer, impressionist style, not a panic style

---

## What Already Exists

Assume the repository already contains most of the Flutter frontend scaffold and some screens.

Likely existing pieces include:

* Login screen
* Main app shell
* Bottom navigation / page switching
* Global animated background
* Data submission page concept
* Early dashboard layout ideas

You must inspect the repo structure and adapt to what is actually present.

---

## Backend Contract

The frontend must integrate with this backend.

**API base URL:** `http://localhost:5001`

### Endpoints

1. `GET /api/health`
2. `POST /api/decision`

### Response contract summary

The backend returns a `DecisionResponse` object with:

* `generated_at`
* `horizon_days`
* `opening_balance`
* `timeline`
* `survival_probability`
* `risk_label`
* `strategies` (always exactly 3)
* `obligation_summary`
* `metadata`

### Important guarantees

You may rely on these guarantees without defensive workarounds:

* `timeline.dates` always has 30 items
* `timeline.balances` always has 30 items
* `strategies` always has exactly 3 items in this order:

  1. Penalty Minimizer
  2. Operation Protector
  3. Relationship Preserver
* Each strategy has the same number of actions
* `action_label` is always one of: `PAY_NOW`, `PAY_SCHEDULED`, `PARTIAL`, `DELAY`, `NEGOTIATE`
* `risk_label` is always one of: `LOW_RISK`, `MODERATE_RISK`, `HIGH_RISK`, `CRITICAL_RISK`
* `action.reasoning` is always non-empty
* `action.paid_amount <= action.amount`
* `action.paid_fraction` is always a 0.1 increment between 0 and 1
* `survival_probability` is always between 0 and 1
* `timeline.first_breach_day` may be null but is never omitted

---

## Business Goal

The frontend should transform the backend response into a usable finance UI that helps a user:

* understand current cash position
* see projected cash decline over 30 days
* compare three decision strategies
* inspect payment actions by obligation
* understand risk and survival probability
* review totals, urgency, and summaries

The core value proposition is clarity, trust, and immediate decision support.

---

## Required Work Scope

### 1. Repo inspection and cleanup

You must first inspect the repo and identify:

* current Flutter app structure
* actual screen names and file paths
* current navigation flow
* any existing services, models, widgets, theme files, or utilities
* any broken imports or architecture issues
* any duplicated or dead code that should be removed or consolidated

Then make a minimal but coherent integration plan based on the actual repo, not assumptions.

### 2. App shell and routing

Ensure the app has a stable shell with:

* login screen as the entry point
* authenticated main app screen
* bottom navigation with four tabs
* swipe support if already present or easy to preserve
* clean route transitions

### 3. Dashboard integration

Create or update the dashboard so it uses backend data and displays:

* opening balance
* survival probability
* risk label
* a 30-day cash forecast chart using `timeline.dates` and `timeline.balances`
* the minimum projected cash value
* first breach day if present
* obligation summary cards / buckets
* a clear cash pressure warning banner when needed

The dashboard must feel calm and readable. Do not make the top section look like an emergency alert unless the backend indicates severe risk.

### 4. Simulation page integration

Build the simulation page as the core strategy comparison screen.
It should show:

* three strategy tabs or cards
* strategy name and description
* total payments, deferred amount, late fees
* strategy survival probability and risk label
* risk metrics where useful
* the list of obligations for the selected strategy
* each obligation’s vendor, due date, amount, paid amount, paid fraction, action label, and reasoning

The selected strategy should be easy to switch between.

### 5. Account page integration

The account page should summarize the user’s financial profile and the backend-derived view of obligations/flow. It should include at minimum:

* current income and expenditure context where relevant
* totals derived from backend data
* breakdown cards or sections for contributing items
* a clean summary view of monthly or period-based balances if the backend response supports it

If the backend does not directly supply something, use the existing app logic carefully and transparently rather than inventing unsupported values.

### 6. Data submission page integration

Preserve or improve the existing split data submission experience:

* top half: manual entry
* bottom half: document upload

Manual entry should navigate to a form with:

* income / expenditure choice
* amount
* one-time / recurring choice
* date picker using a calendar popup
* to/from field
* category field

Document upload should present a visible tap-anywhere upload experience with the background remaining clearly visible in the green theme.

If file-picker integration is needed, wire it properly and make it work on supported targets.

### 7. Backend service layer

Create a clean API layer for the backend:

* health check call
* decision call
* JSON parsing into Dart models
* basic error handling
* loading states and retry-friendly UX

The integration should not scatter HTTP calls throughout widgets.

### 8. Models and serialization

Create or update Dart models for the backend contract, including at minimum:

* DecisionResponse
* Timeline
* Strategy
* Action
* RiskMetrics
* ObligationSummary
* ActionBucket
* Metadata

Use a predictable model layer with `fromJson` constructors. Keep naming clean and consistent.

### 9. Theming and UI consistency

Ensure the whole app matches the existing visual direction:

* emerald/teal global background
* translucent or softly elevated panels where appropriate
* white / muted-white text
* consistent color mapping for risk labels and action labels
* bold all-caps ORACULUM title where used

Update text colors and card backgrounds so content remains readable on the dark background.

### 10. Error handling and fallback states

The app should gracefully handle:

* backend offline
* backend health check failure
* malformed or unexpected responses
* loading states
* empty strategy/action states if needed

Use helpful user-facing messages, not raw technical errors, unless the app is in a debug/error state.

---

## Implementation Priorities

Work in this order:

1. inspect repo and map current architecture
2. fix or stabilize any structural issues that block integration
3. create/update models and backend service layer
4. wire dashboard to backend data
5. wire simulation page to backend data
6. wire account page to backend summaries
7. polish navigation, theme, and reusable widgets
8. clean up imports, dead code, and build errors

---

## Expected Files / Areas to Review

You must inspect the actual repo, but likely areas include:

* `lib/main.dart`
* `lib/screens/`
* `lib/widgets/`
* `lib/services/`
* `lib/models/`
* `lib/theme/`
* `pubspec.yaml`
* any assets used for icons or background visuals

If these folders do not exist, create a clean equivalent structure.

---

## Suggested Flutter Architecture

Use a modular structure like this if the repo does not already have a better one:

```text
lib/
  main.dart
  app.dart
  models/
    decision_response.dart
    timeline.dart
    strategy.dart
    action.dart
    risk_metrics.dart
    obligation_summary.dart
    metadata.dart
  services/
    api_service.dart
    auth_service.dart
  screens/
    login_page.dart
    home_page.dart
    dashboard_page.dart
    data_page.dart
    manual_entry_page.dart
    document_upload_page.dart
    simulation_page.dart
    account_page.dart
  widgets/
    global_background.dart
    bottom_nav.dart
    summary_card.dart
    strategy_card.dart
    obligation_tile.dart
    status_badge.dart
  theme/
    app_theme.dart
```

You do not need to use this exact structure, but the final code should be similarly clean and maintainable.

---

## UI Requirements by Screen

### Dashboard screen

* Top section: “days to zero” styled softly and impressionistically
* Middle section: current balance in a simple, clean format
* Lower section: urgent payments with due date and individual payment amount
* Bottom: total amount due within a week

### Simulation screen

* Show three backend strategies
* Show details for selected strategy
* Display each obligation/action clearly
* Include reasoning text
* Make it easy to compare strategies visually

### Account screen

* Show financial summary and breakdowns
* Use readable cards and sections
* Keep layout calm and organized

### Data submission screen

* Split into manual entry and document upload halves
* Manual entry navigates to a structured form
* Document upload is tap-anywhere with visible upload affordance

### Login screen

* Keep it simple and on-theme
* ORACULUM title should be all caps and bold where used

---

## Color / Label Mapping

Use these mappings consistently:

### Risk labels

* `LOW_RISK` → green
* `MODERATE_RISK` → amber
* `HIGH_RISK` → orange
* `CRITICAL_RISK` → red

### Action labels

* `PAY_NOW` → red
* `PAY_SCHEDULED` → green
* `PARTIAL` → orange
* `DELAY` → amber
* `NEGOTIATE` → amber

---

## Technical Constraints

* Do not break the existing login or navigation flow
* Do not hardcode backend data except for temporary placeholders during development
* Prefer readable, production-like Flutter code
* Keep widgets small and reusable where possible
* Avoid unnecessary dependencies unless they clearly improve the integration
* Preserve mobile compatibility first
* If web compatibility is affected by a package, note it clearly

---

## Acceptance Criteria

The task is complete only when all of the following are true:

* App builds successfully
* Login still works
* Main app shell loads correctly
* Dashboard displays backend-driven data
* Simulation page displays all 3 strategies and the actions for the selected one
* Account page shows backend-informed summaries
* Data submission flow works for manual and document upload paths
* Backend API calls are centralized and clean
* UI uses the correct emerald/teal theme and readable text colors
* ORACULUM title appears in all caps and bold where used
* No broken imports, unresolved references, or obvious architecture regressions remain

---

## Output Requirements

When finishing, provide:

1. a concise summary of what changed
2. the exact files created or modified
3. any assumptions made
4. any remaining TODOs or limitations
5. run/build issues encountered, if any

Do not produce vague progress notes. Make concrete repo-level changes.

---

## Final Instruction

Treat the backend contract as the source of truth. Build the Flutter frontend so that the dashboard, simulation, and account pages are real consumers of the backend response, not mock-only UI.

Work carefully. Keep the codebase coherent. Preserve the app’s visual identity. Make the integration production-grade enough that the backend team can plug in without revisiting the frontend architecture.