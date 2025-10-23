# Use official Python slim image
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcairo2 libcairo2-dev libpango1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev libjpeg-dev zlib1g-dev fonts-dejavu-core \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Make startup script executable
RUN chmod +x start.sh

EXPOSE 8000

# Start the application
CMD ["./start.sh"]
