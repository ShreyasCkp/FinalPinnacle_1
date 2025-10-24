#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Install system packages required by xhtml2pdf / Cairo
apt-get update
apt-get install -y libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# Activate the virtual environment
source antenv/bin/activate

# (Optional) Collect static files and run migrations
# python manage.py collectstatic --noinput
# python manage.py migrate --noinput

# Start Gunicorn
gunicorn student_alerts_app.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --log-file -
