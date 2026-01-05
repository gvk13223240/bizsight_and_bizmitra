from billing.models import Bill, Business
from django.db.models import Sum

def build_business_features(business):
    if not isinstance(business, Business):
        raise ValueError("build_business_features expects a Business instance")

    bills = Bill.objects.filter(business=business, is_deleted=False)

    bills_count = bills.count()

    unpaid_bills = bills.filter(payment_status="UNPAID")
    unpaid_amount = unpaid_bills.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    total_amount = bills.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    unpaid_ratio = (
        unpaid_amount / total_amount
        if total_amount > 0
        else 0
    )

    avg_bill_value = (
        total_amount / bills_count
        if bills_count > 0
        else 0
    )

    return {
        "bills_count": bills_count,
        "unpaid_ratio": round(unpaid_ratio, 2),
        "avg_bill_value": round(avg_bill_value, 2),
        "risk": "low",
        "sales_trend": "stable",
        "total_sales": float(total_amount),
    }
