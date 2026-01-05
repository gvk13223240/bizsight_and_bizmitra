from django.shortcuts import render, redirect
from accounts.utils import get_current_business
from bizmitra.services.feature_builder import build_business_features
from bizmitra.services.guided_chat import get_guided_response

def guided_chat_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("/accounts/login/")

    bills = business.bills.all()
    features = build_business_features(bills)

    response = None
    user_query = None

    if request.method == "POST":
        user_query = request.POST.get("query", "")
        response = get_guided_response(features, user_query)

    return render(request, "bizmitra/chat.html", {
        "business": business,
        "user_query": user_query,
        "response": response,
    })
