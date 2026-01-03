# bizmitra/services/alerts_engine.py

def generate_alerts(features):
    alerts = []

    bills = features["bills_count"]
    unpaid_ratio = features["unpaid_ratio"]
    sales_trend = features["sales_trend"]

    if bills == 0:
        alerts.append({
            "level": "neutral",
            "title": "No billing activity",
            "message": "Create bills to activate business monitoring.",
        })
        return alerts

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
            "message": f"{int(unpaid_ratio*100)}% bills unpaid."
        })

    elif unpaid_ratio > 0.2:
        alerts.append({
            "level": "warning",
            "title": "Moderate unpaid exposure",
            "message": f"{int(unpaid_ratio*100)}% bills unpaid."
        })

    if sales_trend == "down":
        alerts.append({
            "level": "warning",
            "title": "Sales declining",
            "message": "Sales in the last 30 days are lower than the previous period.",
        })

    
    if not alerts:
        alerts.append({
            "level": "success",
            "title": "Business operating normally",
            "message": "No critical conditions detected at this time.",
        })

    return alerts
chat_engine.py

def respond(query, features):
    q = query.lower()

    if "risk" in q:
        return (
            f"Your current unpaid ratio is "
            f"{int(features['unpaid_ratio']*100)}%. "
            "This directly increases predicted risk."
        )

    if "increase sales" in q:
        return (
            "Based on billing patterns, increasing average bill value "
            "has the strongest impact on growth."
        )

    if "why" in q:
        return (
            "BizMitra analyzes unpaid behavior, bill frequency, "
            "and sales trends using ML patterns."
        )

    return (
        "I can help with risk, growth, unpaid bills, "
        "or forecasting questions."
    )
feature_builder.py
from billing.models import Bill
from django.db.models import Avg, Sum
from bizmitra.services.risk_api_client import get_risk

def build_business_features(business):
    bills = Bill.objects.filter(business=business, is_deleted=False)

    total_bills = bills.count()
    unpaid_bills = bills.filter(payment_status__iexact="UNPAID").count()

    total_sales = bills.filter(payment_status__iexact="PAID").aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    avg_bill = bills.filter(payment_status__iexact="PAID").aggregate(
        avg=Avg("total_amount")
    )["avg"] or 0

    unpaid_ratio = unpaid_bills / total_bills if total_bills else 0

    # Default sales trend
    sales_trend = "stable"
    if total_bills >= 2:
        latest = bills.order_by("-created_at").first()
        oldest = bills.order_by("created_at").first()
        if latest and oldest:
            if latest.total_amount > oldest.total_amount:
                sales_trend = "upward"
            elif latest.total_amount < oldest.total_amount:
                sales_trend = "downward"

    # ✅ Use ML model for risk prediction
    features = {
        "bills_count": total_bills,
        "unpaid_ratio": unpaid_ratio,
        "total_sales": float(total_sales),
        "avg_bill_value": float(avg_bill),
        "sales_trend": sales_trend,
    }

    features["risk_score"] = get_risk(features)

    return features
guided_chat.py
def get_guided_response(features, query):
    query = query.lower()

    unpaid_ratio = features["unpaid_ratio"]
    avg_bill = features["avg_bill_value"]
    total_sales = features["total_sales"]
    trend = features["sales_trend"]

    if "unpaid" in query or "risk" in query:
        if unpaid_ratio == 0:
            return (
                "All your bills are paid. "
                "There is currently no cash-flow risk."
            )
        return (
            f"{int(unpaid_ratio * 100)}% of bills are unpaid. "
            "This can impact liquidity."
        )

    if "cash" in query:
        return (
            "Cash flow is under pressure due to unpaid bills."
            if unpaid_ratio > 0.3
            else "Cash flow appears stable."
        )

    if "growth" in query:
        return (
            "Upselling and bundles can increase revenue."
            if avg_bill < 3000
            else "Your order values are already healthy."
        )

    if "trend" in query or "pattern" in query:
        return f"Sales trend is currently {trend}."

    if "this week" in query:
        return (
            "This week, focus on collecting unpaid bills "
            "and sustaining current sales momentum."
        )

    if "what if" in query:
        return (
            "If unpaid exposure continues, future liquidity risk will rise. "
            "Reducing unpaid bills stabilizes growth."
        )

    return (
        "I can help with unpaid bills, cash-flow, growth, "
        "patterns, and what-if analysis."
    )
insight_engine.py
from bizmitra.services.risk_api_client import get_risk
def generate_insights(features):
    insights = []

    risk_score = float(get_risk(features))
    unpaid_ratio = features["unpaid_ratio"]
    avg_bill = features["avg_bill_value"]

    # ML risk insight (ALWAYS shown)
    insights.append({
        "level": "risk" if risk_score > 0.6 else "success",
        "title": "ML Cash-Flow Risk Forecast",
        "risk_score": risk_score,
        "message": f"Predicted cash-flow risk is {int(risk_score * 100)}%.",
        "recommendation": (
            "Reduce unpaid exposure immediately."
            if risk_score > 0.6
            else "Risk levels are stable."
        ),
    })

    # Unpaid exposure (ONLY if real)
    if unpaid_ratio > 0.3:
        insights.append({
            "level": "warning",
            "title": "Unpaid Exposure Pattern",
            "unpaid_ratio": unpaid_ratio,
            "message": f"{int(unpaid_ratio * 100)}% of bills are unpaid.",
            "recommendation": "Enable reminders or advance payments.",
        })

    # Average bill value
    if avg_bill < 1000:
        insights.append({
            "level": "warning",
            "title": "Low Order Value",
            "avg_bill_value": avg_bill,
            "message": f"Average bill value is ₹{int(avg_bill)}.",
            "recommendation": "Bundle products or upsell.",
        })

    return insights
risk_api_client.py
import requests

BIZMITRA_RISK_API = "https://bizmitraapi-production.up.railway.app/predict-risk"

def get_risk(unpaid_ratio, avg_bill_value, bills_count):
    payload = {
        "unpaid_ratio": unpaid_ratio,
        "avg_bill_value": avg_bill_value,
        "bills_count": bills_count,
    }

    try:
        response = requests.post(BIZMITRA_RISK_API, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        # Fail safe – never break dashboard
        return {
            "risk_score": 0.0,
            "risk_label": 0,
            "error": str(e)
        }
