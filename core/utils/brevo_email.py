import os
import base64
import requests

BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

def send_email(subject, html_content, to_email, attachments=None):
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

    if attachments:
        payload["attachment"] = []
        for file_path in attachments:
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                payload["attachment"].append({
                    "content": encoded,
                    "name": os.path.basename(file_path),
                })

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    # Hard fail only in dev
    response.raise_for_status()
