# bizmitra/views/alerts.py

from django.shortcuts import render, redirect
from accounts.utils import get_current_business
from bizmitra.services.feature_builder import build_business_features
from bizmitra.services.alerts_engine import generate_alerts


def alerts_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("/accounts/login/")
    bills = business.bills.all()
    features = build_business_features(bills)
    alerts = generate_alerts(features)

    return render(request, "bizmitra/alerts.html", {
        "business": business,
        "alerts": alerts,
    })
