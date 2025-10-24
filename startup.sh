#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "Installing system dependencies for Cairo..."
# Install Cairo and related libraries
apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn student_alerts_app.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --timeout 180 \
    --log-level info \
    --log-file -
