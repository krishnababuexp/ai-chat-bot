FROM python:3.11-slim

# Prevent interactive Playwright prompt
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ./app/requirements.txt /app/requirements.txt

# Upgrade pip first (important)
RUN pip install --upgrade pip setuptools wheel

# Install Python deps with retry + timeout
RUN pip install --default-timeout=200 --retries=20 --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only)
RUN playwright install chromium

# Copy app
COPY ./app /app/app

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
