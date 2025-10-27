#!/bin/bash
set -e

echo "🚀 Starting Django app at $(date)"

# 1. (Optional) Activate virtual environment if exists
if [ -f "/home/site/wwwroot/antenv/bin/activate" ]; then
  source /home/site/wwwroot/antenv/bin/activate
fi

# 2. Install Python dependencies
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -r /home/site/wwwroot/requirements.txt

# 3. Apply database migrations
python3 /home/site/wwwroot/manage.py migrate --noinput || echo "⚠️ Migrations failed"

# 4. Collect static files
python3 /home/site/wwwroot/manage.py collectstatic --noinput || echo "⚠️ Collectstatic failed"

# 5. Start Gunicorn with logs
exec gunicorn student_alerts_app.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --timeout 600 \
    --access-logfile /home/LogFiles/gunicorn-access.log \
    --error-logfile /home/LogFiles/gunicorn-error.log
