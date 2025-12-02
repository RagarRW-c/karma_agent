FROM python:3.9-slim

WORKDIR /app

# Install system dependencies + playwright dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install playwright

# Install Playwright browsers (DODAJ TO!)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

EXPOSE 8000

# Default command
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]