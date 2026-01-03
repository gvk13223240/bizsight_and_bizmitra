import requests

BIZMITRA_RISK_API = "https://bizmitraapi-production.up.railway.app/predict-risk"

def get_risk(unpaid_ratio, avg_bill_value, bills_count):
    payload = {
        "unpaid_ratio": unpaid_ratio,
        "avg_bill_value": avg_bill_value,
        "bills_count": bills_count,
    }

    try:
        response = requests.post(BIZMITRA_RISK_API, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        # Fail safe – never break dashboard
        return {
            "risk_score": 0.0,
            "risk_label": 0,
            "error": str(e)
        }

