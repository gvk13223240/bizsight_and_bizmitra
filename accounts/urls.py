from django.urls import path
from .views import (
    login_view,
    logout_view,
    business_profile_view,
    business_dashboard,
    onboarding_view,
    signup_view,
    # activate_view,
)

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    # path("activate/<uidb64>/<token>/", activate_view, name="activate"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("business/profile/", business_profile_view, name="business_profile"),
    path("business/", business_dashboard, name="business_dashboard"),
    path("onboarding/", onboarding_view, name="onboarding"),

]
