import requests
from django.conf import settings


def send_email(subject, html_content, to_email):
    url = "https://api.brevo.com/v3/smtp/email"

    payload = {
        "sender": {
            "email": settings.DEFAULT_FROM_EMAIL,
            "name": "BizSight"
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    headers = {
        "api-key": settings.BREVO_API_KEY,
        "accept": "application/json",
        "content-type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
