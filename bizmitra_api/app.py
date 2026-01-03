from fastapi import FastAPI
from pydantic import BaseModel
import tensorflow as tf
import joblib
import numpy as np

app = FastAPI(title="BizMitra Risk API")

# Load once at startup
model = tf.keras.models.load_model("risk_model.h5")
scaler = joblib.load("scaler.pkl")


class RiskInput(BaseModel):
    unpaid_ratio: float
    avg_bill_value: float
    bills_count: int


@app.post("/predict-risk")
def predict_risk(data: RiskInput):
    X = np.array([[
        data.unpaid_ratio,
        data.avg_bill_value,
        data.bills_count
    ]])

    X_scaled = scaler.transform(X)
    risk_score = model.predict(X_scaled)[0][0]

    return {
        "risk_score": float(risk_score),
        "risk_label": int(risk_score >= 0.5)
    }
