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
