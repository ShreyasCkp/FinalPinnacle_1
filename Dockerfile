# Use official Python image
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config libcairo2-dev libfreetype6-dev libpng-dev libfontconfig1-dev \
    libpango1.0-dev libgdk-pixbuf2.0-dev libffi-dev libjpeg-dev zlib1g-dev \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Collect static files & migrate DB on container start (optional: can be in startup script)
# Commenting here if you want to run via entrypoint script
# RUN python manage.py migrate --noinput
# RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Use entrypoint script for DB migrations + static files + Gunicorn
CMD ["bash", "start.sh"]
