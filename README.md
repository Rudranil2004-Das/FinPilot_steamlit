# FinPilot — Personal Finance Workspace

A redesigned, offline-first recreation of the JEV AI Financial Advisor project. It keeps the original goals—transaction categorization, spending review, and bill prioritization—but adds a cleaner dashboard, persistent SQLite storage, CSV import/export, filters, a monthly trend, and a bill ledger.

## Run on Windows

1. Install Python 3.10 or newer from https://www.python.org/downloads/ (enable **Add Python to PATH**).
2. Extract the ZIP to a normal folder (not inside another ZIP or a protected system folder).
3. Double-click `run_windows.bat`. On first run it creates `.venv`, installs dependencies, and launches Streamlit.
4. If the browser does not open, visit http://localhost:8501.

### Run manually

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Features

- Dashboard: recorded income/expenses, net flow, review queue, category chart, latest activity.
- Transactions: add, search/filter, delete, and persist transactions locally.
- Smart review: keyword-based category suggestion and explainable budget-aware review score.
- Bill planner: due-date urgency, available-funds shortfall, saved bill list.
- Insights & export: monthly expense trend, category statistics, CSV downloads and CSV import.

## Important design note

The original repository required an external TypeSafe API for its core analysis, so the frontend could fail when credentials, network access, or SDK setup were missing. This version removes that runtime dependency: core calculations work locally without API keys. The review score is a transparent heuristic, **not a trained machine-learning model**, not a bank connection, and not proof of fraud. All initial demo transactions are fictional. Records are stored in `finpilot.db` on the machine running the app; deleting that file resets local storage.

## CSV import format

Required headers: `description`, `amount`. Optional headers: `tx_date`, `category`, `tx_type` (`Expense` or `Income`), `budget`.

Example:

```csv
tx_date,description,amount,category,tx_type,budget
2026-10-29,Weekly groceries,1250,Groceries,Expense,2500
2026-10-28,Part-time salary,8000,Income,Income,0
```

## Project structure

- `app.py` — Streamlit frontend and local SQLite workflows
- `finance_service.py` — offline categorization and financial review logic
- `requirements.txt` — minimal runtime dependencies
- `run_windows.bat` — Windows setup launcher
