# ===============================
# Stage 1: Build stage
# ===============================
FROM python:3.11.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies + runtime libraries for MySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    libmariadb3 \
    libssl-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# ===============================
# Stage 2: Production image
# ===============================
FROM python:3.11.13-slim

WORKDIR /app

# Install runtime library for MySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local /usr/local

# Copy project files
COPY --from=builder /app /app

# Expose ports
EXPOSE 8000

# Gunicorn CMD
CMD ["gunicorn", "reflectionsBE.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
