# BizSight & BizMitra

<p align="center">
  <img src="static/bizsight_logo.png" alt="BizSight Logo" width="200"/>
</p>

<p align="center">
  <img src="static/bizmitra_logo.png" alt="BizMitra Logo" width="200"/>
</p>

**BizSight** is a Django-based business intelligence and billing platform designed for small and medium businesses.  
**BizMitra** is the AI-powered companion layer that adds insights, alerts, and risk intelligence on top of BizSight’s data.

Together, they help business owners **manage billing, analyze sales, and understand business risks** from a single system.

---

## Why BizSight?

Many small businesses still rely on:
- Manual billing
- Basic spreadsheets
- No real analytics
- No visibility into risks or trends

BizSight was built to solve this gap with a **simple, practical, and extensible system** that focuses on:
- Day-to-day billing
- Clear sales analytics
- Easy data imports
- Actionable insights

_No heavy ERP. No unnecessary complexity._

---

## What is BizMitra?

BizMitra is the **intelligence layer** of BizSight.

It works as a digital business companion that:
- Analyzes billing and sales data
- Generates smart insights
- Raises alerts for risky patterns
- Uses a trained ML model for risk scoring
- Provides a guided, chat-style experience

BizMitra does not replace business owners — it **assists decision-making**.

---

## Core Features

### Billing
- Create bills with multiple items  
- Track paid, unpaid, and pay-later bills  
- Automatic bill numbering  
- Soft delete support  
- PDF invoice generation  
- Optional email delivery of invoices  

### UPI Payments
- Business can add its own UPI ID  
- QR code generated per bill  
- Prompts configuration if UPI is missing  
- Supports walk-in and registered customers  

### Analytics Dashboard
- Daily and monthly sales trends  
- Total sales, bill count, paid/unpaid metrics  
- Top-selling items  
- Charts using real business data  
- Date-range filtering  

### Data Import
- Import bills from:
  - Google Sheets (public CSV export)
  - CSV file uploads
- Preview data before import  
- Handles missing emails and walk-in customers  
- Ready-to-use CSV template  

### Exports
- Download data as:
  - CSV
  - Excel
  - PDF reports  
- Date-filtered exports supported  

### BizMitra Intelligence
- Smart insights based on sales behavior  
- Alerts for unusual or risky patterns  
- Risk prediction using TensorFlow model  
- Modular AI services  

---

## Tech Stack

- **Backend**: Django  
- **Database**: SQLite (development)  
- **Frontend**: Django Templates + CSS  
- **Analytics**: Custom aggregation services  
- **AI / ML**:
  - TensorFlow (pre-trained model)
  - Scikit-learn (scaler)
- **Charts**: Chart.js  
- **Imports**: Google Sheets CSV + file uploads  

---

## Project Structure

```
core/
accounts/
billing/
analytics_engine/
bizmitra/
insights/
static/
```

---

## ML & Risk Model

- `risk_model.h5` → Pre-trained TensorFlow model  
- `scaler.pkl` → Feature scaler  
- Models loaded at runtime  
- Training code excluded from production  
- Inference behavior remains unchanged  

---

## Setup Instructions

```bash
git clone https://github.com/gvk13223140/bizsight.git
cd bizsight

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Open: http://127.0.0.1:8000

