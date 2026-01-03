#!/bin/bash
set -e

LOG_DIR=/home/LogFiles
mkdir -p $LOG_DIR

echo "Starting Django app at $(date)" | tee -a $LOG_DIR/startup.log

# Install system deps needed for pycairo (used by xhtml2pdf/svglib)
if command -v apt-get >/dev/null 2>&1; then
  if ! command -v pkg-config >/dev/null 2>&1; then
    echo "Installing system packages for cairo..." | tee -a $LOG_DIR/startup.log
    export DEBIAN_FRONTEND=noninteractive
    apt-get update | tee -a $LOG_DIR/startup.log
    apt-get install -y --no-install-recommends pkg-config libcairo2-dev | tee -a $LOG_DIR/startup.log
  fi
fi

# Prefer the app virtual environment if available
PYTHON_BIN="/home/site/wwwroot/antenv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3)"
fi

# Upgrade pip and install dependencies
$PYTHON_BIN -m pip install --no-cache-dir --upgrade pip | tee -a $LOG_DIR/startup.log
$PYTHON_BIN -m pip install --no-cache-dir --prefer-binary -r /home/site/wwwroot/requirements.txt | tee -a $LOG_DIR/startup.log

# Fallback: install missing runtime-only deps if requirements didn't include them
if ! $PYTHON_BIN - <<'PY' >/dev/null 2>&1
import num2words
PY
then
  echo "Installing missing dependency: num2words" | tee -a $LOG_DIR/startup.log
  $PYTHON_BIN -m pip install --no-cache-dir num2words==0.5.13 | tee -a $LOG_DIR/startup.log
fi

# Apply database migrations
$PYTHON_BIN /home/site/wwwroot/manage.py migrate --noinput | tee -a $LOG_DIR/startup.log || echo "Migrations failed" | tee -a $LOG_DIR/startup.log

# Collect static files
$PYTHON_BIN /home/site/wwwroot/manage.py collectstatic --noinput | tee -a $LOG_DIR/startup.log || echo "Collectstatic failed" | tee -a $LOG_DIR/startup.log

# Start Gunicorn
exec $PYTHON_BIN -m gunicorn student_alerts_app.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 3 \
  --timeout 600 \
  --access-logfile $LOG_DIR/gunicorn-access.log \
  --error-logfile $LOG_DIR/gunicorn-error.log