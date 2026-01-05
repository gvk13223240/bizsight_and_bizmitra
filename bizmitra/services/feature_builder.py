def build_business_features(bills):
    """
    Build features safely even if bills are empty
    """

    bills_count = bills.count()

    if bills_count == 0:
        return {
            "unpaid_ratio": 0,
            "avg_bill_value": 0,
            "bills_count": 0,
            "risk_score": 0,
        }

    total_amount = sum(b.total_amount for b in bills)
    unpaid_amount = sum(
        b.total_amount for b in bills if b.payment_status == "UNPAID"
    )

    unpaid_ratio = unpaid_amount / total_amount if total_amount else 0
    avg_bill_value = total_amount / bills_count

    risk_score = get_risk(
        unpaid_ratio,
        avg_bill_value,
        bills_count,
    )

    return {
        "unpaid_ratio": unpaid_ratio,
        "avg_bill_value": avg_bill_value,
        "bills_count": bills_count,
        "risk_score": risk_score,
    }
