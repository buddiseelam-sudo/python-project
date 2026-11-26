"""Core business logic and validation for Trip Budget Calculator."""
from datetime import date

CATEGORIES = ("transport", "stay", "food", "activities")
REQUIRED_FIELDS = ("trip_name", "destination", "start_date", "end_date", "travelers",
                   "transport", "stay", "food", "activities")

def validate_record(record):
    """Return a list of human-readable validation errors."""
    errors = []
    for field in ("trip_name", "destination"):
        if not str(record.get(field, "")).strip():
            errors.append(f"{field.replace('_', ' ').title()} cannot be blank.")
    try:
        start = date.fromisoformat(str(record.get("start_date", "")))
        end = date.fromisoformat(str(record.get("end_date", "")))
        if end < start:
            errors.append("End date cannot be earlier than start date.")
    except (TypeError, ValueError):
        errors.append("Enter valid start and end dates.")
    try:
        travelers = int(record.get("travelers", 0))
        if travelers < 1:
            errors.append("Number of travelers must be at least 1.")
    except (TypeError, ValueError):
        errors.append("Number of travelers must be a whole number.")
    for field in CATEGORIES + ("budget_limit",):
        try:
            value = float(record.get(field, 0))
            if value < 0:
                errors.append(f"{field.title()} cannot be negative.")
        except (TypeError, ValueError):
            errors.append(f"{field.title()} must be a valid number.")
    return errors

def calculate_total(record):
    return round(sum(float(record.get(k, 0) or 0) for k in CATEGORIES), 2)

def enrich_record(record):
    result = dict(record)
    result["total_cost"] = calculate_total(result)
    result["budget_status"] = (
        "Over Budget" if float(result.get("budget_limit", 0) or 0) > 0
        and result["total_cost"] > float(result.get("budget_limit", 0) or 0)
        else "Within Budget"
    )
    return result

def summarize(records):
    totals = [calculate_total(r) for r in records]
    total = round(sum(totals), 2)
    budgets = [float(r.get("budget_limit", 0) or 0) for r in records]
    exceeded = sum(1 for r, t in zip(records, totals)
                   if float(r.get("budget_limit", 0) or 0) > 0 and t > float(r.get("budget_limit", 0) or 0))
    return {
        "trip_count": len(records),
        "total_spend": total,
        "average_spend": round(total / len(records), 2) if records else 0,
        "highest_spend": max(totals, default=0),
        "lowest_spend": min(totals, default=0),
        "over_budget": exceeded,
        "total_budget": round(sum(budgets), 2),
    }

def category_totals(records):
    return {k: round(sum(float(r.get(k, 0) or 0) for r in records), 2) for k in CATEGORIES}
