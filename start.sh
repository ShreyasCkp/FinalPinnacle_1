#!/bin/bash
set -e
echo "---- Installing system dependencies ----"
apt-get update -y
apt-get install -y libcairo2 libcairo2-dev libpango1.0-0 libpangocairo-1.0-0 \
                   libgdk-pixbuf2.0-0 libffi-dev libjpeg-dev zlib1g-dev

echo "---- Running Django setup ----"
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "---- Starting Gunicorn ----"
exec gunicorn student_alerts_app.wsgi:application --bind=0.0.0.0 --timeout 600
