# Use a full Debian-based Python image
FROM python:3.9-bullseye
 
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
 
# Set working directory
WORKDIR /app
 
# Install system dependencies for pycairo and PDF libs
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    git \
&& rm -rf /var/lib/apt/lists/*
 
# Upgrade pip to the latest version
RUN pip install --upgrade pip
 
# Copy requirements first (for caching)
COPY requirements.txt .
 
# Clear pip cache to avoid stale build artifacts
RUN pip cache purge
 
# Install pycairo separately to isolate potential issues
RUN pip install --no-cache-dir pycairo || { echo "pycairo installation failed"; exit 1; }
 
# Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements.txt || { echo "requirements.txt installation failed"; exit 1; }
 
# Copy the Django project
COPY . .
 
# Expose port
EXPOSE 8000
 
# Run gunicorn
CMD ["gunicorn", "student_alerts_app.wsgi:application", "--bind", "0.0.0.0:8000"]