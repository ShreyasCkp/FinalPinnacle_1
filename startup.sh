#!/bin/bash

# 1. Install system libraries
apt-get -o Acquire::Check-Valid-Until=false update -y
apt-get install -y libcairo2 libpango-1.0-0 libffi-dev ... 
apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Create a virtual environment inside /home/site
python3 -m venv /home/site/venv
source /home/site/venv/bin/activate

# 3. Install Python dependencies inside venv
pip install --upgrade pip
pip install -r /home/site/wwwroot/requirements.txt

# 4. Apply Django migrations inside venv
python /home/site/wwwroot/manage.py migrate --noinput || echo "⚠️ Migrations failed"

# 5. Collect static files inside venv
python /home/site/wwwroot/manage.py collectstatic --noinput || echo "⚠️ Collectstatic failed"

# 6. Start Gunicorn inside venv
exec /home/site/venv/bin/gunicorn student_alerts_app.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 180
