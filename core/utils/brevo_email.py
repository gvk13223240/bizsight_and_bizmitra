import os
import requests

BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

def send_email(subject, html_content, to_email):
    url = "https://api.brevo.com/v3/smtp/email"

    payload = {
        "sender": {
            "email": DEFAULT_FROM_EMAIL,
            "name": "BizSight"
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
