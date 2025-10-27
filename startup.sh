#!/bin/bash
set -e

LOG_DIR=/home/LogFiles
mkdir -p $LOG_DIR

echo "🚀 Starting Django app at $(date)" | tee -a $LOG_DIR/startup.log

# Optional: activate venv
if [ -f "/home/site/wwwroot/antenv/bin/activate" ]; then
  source /home/site/wwwroot/antenv/bin/activate
fi

# Upgrade pip and install dependencies
python3 -m pip install --no-cache-dir --upgrade pip | tee -a $LOG_DIR/startup.log
python3 -m pip install --no-cache-dir -r /home/site/wwwroot/requirements.txt | tee -a $LOG_DIR/startup.log

# Apply database migrations
python3 /home/site/wwwroot/manage.py migrate --noinput | tee -a $LOG_DIR/startup.log || echo "⚠️ Migrations failed" | tee -a $LOG_DIR/startup.log

# Collect static files
python3 /home/site/wwwroot/manage.py collectstatic --noinput | tee -a $LOG_DIR/startup.log || echo "⚠️ Collectstatic failed" | tee -a $LOG_DIR/startup.log

# Start Gunicorn
exec gunicorn student_alerts_app.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 3 \
  --timeout 600 \
  --access-logfile $LOG_DIR/gunicorn-access.log \
  --error-logfile $LOG_DIR/gunicorn-error.log
