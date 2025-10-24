FROM python:3.9-slim

WORKDIR /app

# Install system dependencies required by xhtml2pdf / Cairo
RUN apt-get update && apt-get install -y \
    libcairo2 libcairo2-dev \
    libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev libjpeg-dev zlib1g-dev \
    fonts-dejavu-core build-essential git wget pkg-config python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure startup.sh is executable
RUN chmod +x startup.sh

EXPOSE 8000

# Start the app
CMD ["bash", "startup.sh"]
