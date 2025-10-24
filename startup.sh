#!/bin/bash
# Activate virtual environment
source antenv/bin/activate

# Apply migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
exec gunicorn student_alerts_app.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --log-file -
