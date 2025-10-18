# Use a Debian-based Python image
FROM python:3.9-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for pycairo, PDF libs, and Django
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2 \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    git \
    wget \
    python3-venv \
    fontconfig \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install pycairo first
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir pycairo==1.24.0

# Copy requirements first for caching
COPY requirements.txt .

# Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY . .

# Expose port
EXPOSE 8000

# Run Django via Gunicorn
CMD ["gunicorn", "student_alerts_app.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "600"]
