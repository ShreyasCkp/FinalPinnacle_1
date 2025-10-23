#!/bin/bash
set -e  # Exit immediately if any command fails
 
echo "---- Installing system dependencies ----"
apt-get update -y
apt-get install -y libcairo2 libcairo2-dev libpango-1.0-0 libpangocairo-1.0-0 \
                   libgdk-pixbuf2.0-0 libffi-dev libjpeg-dev zlib1g-dev
 
echo "---- Installing Python dependencies ----"
pip install -r requirements.txt
 
echo "---- Running Django setup ----"
python manage.py migrate --noinput
python manage.py collectstatic --noinput
 
echo "---- Starting Gunicorn ----"
exec gunicorn student_alerts_app.wsgi:application --bind=0.0.0.0 --timeout 600