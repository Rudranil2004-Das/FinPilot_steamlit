"""Offline-first finance analysis helpers. No API key or paid AI service required."""
from datetime import date, datetime
import re

CATEGORY_KEYWORDS = {
    "Groceries": ["grocery", "groceries", "supermarket", "vegetable", "food", "milk", "bakery"],
    "Utilities": ["electricity", "water bill", "gas bill", "internet", "wifi", "mobile recharge", "phone bill"],
    "Transport": ["uber", "ola", "metro", "bus", "train", "fuel", "petrol", "diesel", "taxi", "transport"],
    "Shopping": ["shopping", "amazon", "flipkart", "clothes", "electronics", "headphone", "phone", "laptop"],
    "Healthcare": ["doctor", "hospital", "medicine", "medical", "pharmacy", "clinic"],
    "Subscriptions": ["subscription", "netflix", "spotify", "prime video", "membership"],
    "Rent & Housing": ["rent", "hostel", "accommodation", "maintenance"],
    "Education": ["college", "tuition", "course", "book", "education", "exam fee"],
    "Income": ["salary", "income", "freelance payment", "refund", "received"],
    "Transfer": ["transfer", "sent to", "upi transfer", "bank transfer"],
}

def categorize_transaction(description: str) -> tuple[str, float]:
    text = description.lower()
    scores = {category: sum(1 for word in words if word in text) for category, words in CATEGORY_KEYWORDS.items()}
    if not scores or max(scores.values()) == 0:
        return "Other", 0.45
    best = max(scores, key=scores.get)
    return best, min(0.98, 0.62 + 0.12 * scores[best])

def analyze_transaction(description: str, amount: float, usual_budget: float, monthly_spend: float = 0) -> dict:
    if not description.strip(): raise ValueError("Please enter a transaction description.")
    if amount <= 0 or usual_budget <= 0: raise ValueError("Amount and usual budget must be greater than zero.")
    category, confidence = categorize_transaction(description)
    ratio = amount / usual_budget
    # Transparent rules, not a fraud model or bank-integrated AI.
    risk = 0.08 + max(0, ratio - 1) * 0.22
    if ratio >= 2: risk += 0.18
    if ratio >= 4: risk += 0.20
    if amount >= 25000: risk += 0.12
    if any(x in description.lower() for x in ["unknown", "unrecognized", "not mine", "unauthorised", "unauthorized"]): risk += 0.35
    risk = max(0.02, min(0.97, risk))
    severity = 1 if risk < .25 else 2 if risk < .5 else 3
    return {"description": description.strip(), "amount": float(amount), "usual_budget": float(usual_budget), "budget_ratio": ratio,
            "category": category, "category_confidence": confidence, "review_probability": risk,
            "severity_score": severity, "budget_exceeded": amount > usual_budget,
            "recommendation": "Review this transaction" if risk >= .5 or ratio >= 2 else "No immediate review flag",
            "analysis_method": "Local rule-based analysis"}

def analyze_bill(bill_name: str, amount: float, due_date_text: str, available_money: float, consequence: str = "") -> dict:
    if not bill_name.strip(): raise ValueError("Bill name is required.")
    if amount <= 0 or available_money < 0: raise ValueError("Bill amount must be positive and available funds cannot be negative.")
    try: due = datetime.strptime(due_date_text, "%Y-%m-%d").date()
    except (ValueError, TypeError): raise ValueError("Due date must be a valid date.")
    days = (due - date.today()).days
    shortfall = max(0, amount - available_money)
    urgency = 0.5 if days < 0 else 0.45 if days == 0 else 0.3 if days <= 3 else 0.18 if days <= 7 else 0.05
    if shortfall > 0: urgency += 0.35
    if any(w in consequence.lower() for w in ["disconnection", "eviction", "penalty", "late fee", "essential"]): urgency += 0.12
    urgency = min(.99, urgency)
    priority = "Critical" if urgency >= .75 else "High" if urgency >= .5 else "Moderate" if urgency >= .28 else "Low"
    return {"bill_name": bill_name.strip(), "amount": float(amount), "due_date": due.isoformat(), "days_remaining": days,
            "priority": priority, "priority_score": round(urgency * 3, 2), "shortfall_probability": 0.9 if shortfall else 0.05,
            "shortfall": round(shortfall, 2), "funds_sufficient": shortfall == 0, "consequence": consequence.strip()}
