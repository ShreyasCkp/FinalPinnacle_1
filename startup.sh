#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Apply migrations
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
