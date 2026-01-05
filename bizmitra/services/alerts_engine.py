# bizmitra/services/alerts_engine.py

def generate_alerts(features):
    alerts = []

    # ✅ SAFE extraction (NO crashes)
    bills = features.get("bills_count", 0)
    unpaid_ratio = features.get("unpaid_ratio", 0)
    sales_trend = features.get("sales_trend", "stable")

    # -------------------------
    # No activity case
    # -------------------------
    if bills == 0:
        alerts.append({
            "level": "neutral",
            "title": "No billing activity",
            "message": "Create bills to activate business monitoring.",
        })
        return alerts

    # -------------------------
    # Unpaid exposure
    # -------------------------
    if unpaid_ratio == 0:
        alerts.append({
            "level": "success",
            "title": "No unpaid exposure",
            "message": "All bills are paid. No alerts detected."
        })

    elif unpaid_ratio > 0.4:
        alerts.append({
            "level": "risk",
            "title": "High unpaid exposure",
            "message": f"{int(unpaid_ratio * 100)}% bills unpaid."
        })

    elif unpaid_ratio > 0.2:
        alerts.append({
            "level": "warning",
            "title": "Moderate unpaid exposure",
            "message": f"{int(unpaid_ratio * 100)}% bills unpaid."
        })

    # -------------------------
    # Sales trend
    # -------------------------
    if sales_trend == "down":
        alerts.append({
            "level": "warning",
            "title": "Sales declining",
            "message": "Sales in the last 30 days are lower than the previous period.",
        })

    # -------------------------
    # Fallback
    # -------------------------
    if not alerts:
        alerts.append({
            "level": "success",
            "title": "Business operating normally",
            "message": "No critical conditions detected at this time.",
        })

    return alerts
