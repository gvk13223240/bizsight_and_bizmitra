from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
# from django.contrib.auth.tokens import default_token_generator
# from django.core.mail import send_mail
from django.shortcuts import render, redirect
# from django.urls import reverse
# from django.utils.encoding import force_bytes
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .forms import BusinessForm
from .models import Business
from .utils import get_current_business


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                business = user.business
            except Business.DoesNotExist:
                return redirect("onboarding")

            login(request, user)
            request.session["business_id"] = business.id
            return redirect("business_dashboard")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html", {})


def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("login")


@login_required
def business_dashboard(request):
    business = get_current_business(request)
    if not business:
        return redirect("onboarding")

    return render(request, "accounts/business.html", {"business": business})


@login_required
def business_profile_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("onboarding")

    if request.method == "POST":
        if request.FILES.get("logo"):
            business.logo = request.FILES["logo"]

        business.name = request.POST.get("name")
        business.email = request.POST.get("email")
        business.phone = request.POST.get("phone")
        business.address = request.POST.get("address")
        business.upi_id = request.POST.get("upi_id")
        business.save()

        messages.success(request, "Business profile updated successfully")
        return redirect("dashboard")

    return render(
        request,
        "accounts/business_profile.html",
        {"business": business},
    )


@login_required
def dashboard_view(request):
    return render(request, "accounts/dashboard.html")


@login_required
def onboarding_view(request):
    if hasattr(request.user, "business"):
        request.session["business_id"] = request.user.business.id
        return redirect("business_dashboard")

    if request.method == "POST":
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save(commit=False)
            business.user = request.user
            business.save()

            request.session["business_id"] = business.id
            return redirect("business_dashboard")
    else:
        form = BusinessForm()

    return render(
        request,
        "accounts/onboarding.html",
        {"form": form},
    )


# def signup_view(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         email = request.POST.get("email")
#         password = request.POST.get("password")

#         if User.objects.filter(username=username).exists():
#             messages.error(request, "Username is already taken.")
#             return render(request, "accounts/signup.html")

#         if User.objects.filter(email=email).exists():
#             messages.error(request, "Email is already registered.")
#             return render(request, "accounts/signup.html")

#         user = User.objects.create_user(
#             username=username,
#             email=email,
#             password=password,
#         )
#         user.is_active = True
#         user.save()

#         uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
#         token = default_token_generator.make_token(user)
#         activate_path = reverse(
#             "activate",
#             kwargs={"uidb64": uidb64, "token": token},
#         )
#         activation_link = request.build_absolute_uri(activate_path)

#         subject = "Verify your BizSight account"
#         message = (
#             f"Hi {user.username},\n\n"
#             "Thanks for signing up for BizSight.\n"
#             "Please verify your email by clicking the link below:\n\n"
#             f"{activation_link}\n\n"
#             "If you didn't create this account, you can ignore this email."
#         )

#         try:
#             send_mail(
#                 subject,
#                 message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [user.email],
#                 fail_silently=False,
#             )
#             messages.success(
#                 request,
#                 "Account created successfully. Please log in.",
#             )
#             return redirect("login")
#         except Exception as e:
#             messages.error(
#                 request,
#                 f"Could not send verification email. Please try again later. ({e})",
#             )
#             return render(request, "accounts/signup.html")

#     return render(request, "accounts/signup.html")

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, "accounts/signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, "accounts/signup.html")

        # Create user and activate immediately
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        user.is_active = True
        user.save()

        # Log the user in directly after signup
        login(request, user)
        messages.success(request, "Account created successfully. Welcome to BizSight!")

        # Redirect to onboarding (to set up business profile)
        return redirect("onboarding")

    return render(request, "accounts/signup.html")

# def activate_view(request, uidb64, token):
#     try:
#         uid = urlsafe_base64_decode(uidb64).decode()
#         user = User.objects.get(pk=uid)
#     except (User.DoesNotExist, ValueError, TypeError, OverflowError):
#         user = None

#     if user and default_token_generator.check_token(user, token):
#         user.is_active = True
#         user.save()

#         login(request, user)
#         messages.success(
#             request,
#             "Your email has been verified. Let's set up your business profile.",
#         )
#         return redirect("onboarding")

#     messages.error(request, "Invalid or expired verification link.")
#     return redirect("signup")
