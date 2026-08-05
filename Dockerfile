FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg (requires libpq)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Add /app to PYTHONPATH
ENV PYTHONPATH=/app

# The command will be overridden in docker-compose.yml depending on the service
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8668"]
