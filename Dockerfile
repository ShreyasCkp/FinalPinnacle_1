# Use official Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for packages like pycairo/weasyprint
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    pkg-config \
    libcairo2 \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libpng-dev \
    libfontconfig1-dev \
    fontconfig \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project code
COPY . .

# Collect static files & migrate database
RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput

# Expose port 8000 for gunicorn
EXPOSE 8000

# Start the application
CMD ["gunicorn", "student_alerts_app.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "600"]
