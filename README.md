# Oraculum Finance

**Next-Generation Cash-Flow Simulation & Advisory**

Oraculum Finance is a cash-flow decision engine and mobile application that empowers businesses to track their financial runway and make optimal payment decisions. It uses advanced simulation models to forecast 30-day survival probability and identify potential cash breaches before they happen, giving users an actionable framework to prioritize payments, negotiate terms, or delay obligations.

---

## 🚀 Key Features

### 🧠 Monte Carlo Decision Engine (Backend)
- **Automated Master Ledger**: Pulls together obligations, transactions, and expected receivables into a cohesive ledger.
- **Monte Carlo Simulations**: Runs thousands of probabilistic scenarios to accurately predict 30-day cash flow and survival chances.
- **Beam Search Planner**: Evaluates all pending obligations and generates 3 distinct payment strategies (Penalty Minimizer, Operations Protector, Relationship Preserver).
- **Actionable Outcomes**: Assigns discrete action labels (`PAY_NOW`, `SCHEDULE`, `PARTIAL`, `DELAY`, `NEGOTIATE`) to each obligation based on its risk/reward profile.

### 📱 Premium Mobile App (Frontend)
- **Glassmorphism Design**: Features a highly polished, deep emerald aesthetic with interactive glowing visuals, blurring, and floating animations.
- **Dynamic Dashboards**:
  - **Hero Dashboard**: Live 30-day forecast charts, survival probability, and quick summaries of critical tasks.
  - **Strategy Simulation**: Let users compare 3 unique strategies, drilling down into risk metrics and precise payment recommendations.
  - **Account & Metadata**: Full system diagnostics indicating transaction health, ledger size, and Monte Carlo runs metadata.

---

## 🛠 Tech Stack

- **Backend**: Python, Flask, Pandas, NumPy (for simulation and math)
- **Frontend**: Flutter (Dart), `fl_chart`, `http`
- **Landing Page**: React, Vite, Framer Motion, Tailwind (stored separately in `/src/app`)

---

## 🎮 Getting Started

### 1. Set up the Backend
Dependencies: Python 3.8+

```bash
cd backend
pip install -r requirements.txt
python api.py
```
> The API will serve requests at `http://0.0.0.0:5001`.

### 2. Set up the Frontend (Flutter)
Dependencies: Flutter SDK

```bash
cd frontend
flutter pub get
```

#### Running on Android Emulator
The app defaults to `10.0.2.2` to communicate with your localhost backend.
```bash
flutter run
```

#### Running on a Physical Device
If you are running on a physical phone, you must point the app to your desktop's local IP address. 
Update `lib/services/api_service.dart`:
```dart
static const String baseUrl = 'http://YOUR_LOCAL_IP:5001/api';
```
Then run:
```bash
flutter run
```

---

## 🎨 UI Highlight
Oraculum Finance replaces boring spreadsheets with a reactive, dark-themed experience full of smooth animations, particle background layers, and real-time interactive simulation maps built natively into Flutter using custom painters.

---

*Oraculum Finance — Because predicting the future is the best way to secure it.*
