FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (important for Pillow, reportlab, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static safely
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    gunicorn core.wsgi:application --bind 0.0.0.0:8000

