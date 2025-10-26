#!/bin/bash

# 1. Install system libraries needed by your apps
apt-get -o Acquire::Check-Valid-Until=false update -y
apt-get install -y libcairo2 libpango-1.0-0 libffi-dev libssl-dev libjpeg-dev \
                   libfreetype6-dev libpq-dev build-essential
apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Upgrade pip and install Python dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r /home/site/wwwroot/requirements.txt

# 3. Apply Django database migrations
python3 /home/site/wwwroot/manage.py migrate --noinput || echo "⚠️ Migrations failed"

# 4. Collect static files
python3 /home/site/wwwroot/manage.py collectstatic --noinput || echo "⚠️ Collectstatic failed"

# 5. Start Gunicorn
exec gunicorn student_alerts_app.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 180
