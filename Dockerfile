# ✅ Use maintained Python image
FROM python:3.9-bullseye

# Prevent .pyc and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    pkg-config \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libpng-dev \
    libfontconfig1-dev \
    git \
    wget \
    fontconfig \
 && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --upgrade pip setuptools wheel

# Install pycairo
RUN pip install --no-cache-dir pycairo==1.24.0

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create static/media
RUN mkdir -p /app/static /app/media

# Collect static during build
RUN python manage.py collectstatic --noinput

# Expose Gunicorn port
EXPOSE 8000

# Start server
CMD ["gunicorn", "student_alerts_app.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "600"]
