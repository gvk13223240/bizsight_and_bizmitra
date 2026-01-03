import requests

RISK_API_URL = "https://bizmitraapi-production.up.railway.app/predict-risk"

def get_risk(unpaid_ratio, avg_bill_value, bills_count):
    payload = {
        "unpaid_ratio": unpaid_ratio,
        "avg_bill_value": avg_bill_value,
        "bills_count": bills_count
    }

    response = requests.post(RISK_API_URL, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()
