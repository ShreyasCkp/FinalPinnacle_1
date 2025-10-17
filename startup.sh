#!/bin/bash

# Install dependencies (if not done by Oryx)
pip install -r requirements.txt

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
gunicorn student_alerts_app.wsgi:application --bind=0.0.0.0 --timeout 600
