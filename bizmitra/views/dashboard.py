from django.shortcuts import render, redirect
from accounts.utils import get_current_business
from bizmitra.services.feature_builder import build_business_features
from bizmitra.services.insight_engine import generate_insights
import json

def dashboard_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("/accounts/login/")

    features = build_business_features(business)
    insights = generate_insights(features)

    return render(request, "bizmitra/dashboard.html", {
        "business": business,
        "features": features,
        "insights": insights,
        "features_json": json.dumps(features),
        "insights_json": json.dumps(insights),
    })
