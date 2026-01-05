def get_guided_response(features, query):
    query = query.lower()

    # ✅ SAFE extraction (NO KeyErrors)
    unpaid_ratio = features.get("unpaid_ratio", 0)
    avg_bill = features.get("avg_bill_value", 0)
    total_sales = features.get("total_sales", 0)
    trend = features.get("sales_trend", "stable")

    # -------------------------
    # Unpaid / Risk
    # -------------------------
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

    # -------------------------
    # Cash flow
    # -------------------------
    if "cash" in query:
        return (
            "Cash flow is under pressure due to unpaid bills."
            if unpaid_ratio > 0.3
            else "Cash flow appears stable."
        )

    # -------------------------
    # Growth
    # -------------------------
    if "growth" in query:
        if avg_bill == 0:
            return "Not enough billing data yet to assess growth."
        return (
            "Upselling and bundles can increase revenue."
            if avg_bill < 3000
            else "Your order values are already healthy."
        )

    # -------------------------
    # Trends
    # -------------------------
    if "trend" in query or "pattern" in query:
        return f"Sales trend is currently {trend}."

    # -------------------------
    # Weekly advice
    # -------------------------
    if "this week" in query:
        return (
            "This week, focus on collecting unpaid bills "
            "and sustaining current sales momentum."
        )

    # -------------------------
    # What-if analysis
    # -------------------------
    if "what if" in query:
        return (
            "If unpaid exposure continues, future liquidity risk will rise. "
            "Reducing unpaid bills stabilizes growth."
        )

    # -------------------------
    # Fallback
    # -------------------------
    return (
        "I can help with unpaid bills, cash-flow, growth, "
        "patterns, and what-if analysis."
    )
