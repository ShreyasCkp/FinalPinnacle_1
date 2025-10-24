#!/bin/bash
set -e  # Exit on error

# Install missing system dependencies for Cairo, WeasyPrint, xhtml2pdf
apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info

# Activate the correct virtual environment (Azure automatically creates one called "antenv" or "env")
if [ -d "antenv" ]; then
  source antenv/bin/activate
elif [ -d "env" ]; then
  source env/bin/activate
elif [ -d "venv" ]; then
  source venv/bin/activate
else
  echo "⚠️ No virtual environment found — continuing without activation"
fi

# Optional: collect static and migrate if needed
python manage.py collectstatic --noinput || true
python manage.py migrate --noinput || true

# Start Gunicorn
exec gunicorn student_alerts_app.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --log-file -
