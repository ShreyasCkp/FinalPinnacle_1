#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "🚀 Starting custom startup script..."

# --- Install missing system dependencies for PDF rendering (Cairo, WeasyPrint, ReportLab, xhtml2pdf) ---
apt-get update -y && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    fonts-freefont-ttf

echo "✅ System dependencies installed."

# --- Activate Azure virtual environment (antenv/env/venv) ---
if [ -d "antenv" ]; then
  echo "🟢 Activating 'antenv' virtual environment..."
  source antenv/bin/activate
elif [ -d "env" ]; then
  echo "🟢 Activating 'env' virtual environment..."
  source env/bin/activate
elif [ -d "venv" ]; then
  echo "🟢 Activating 'venv' virtual environment..."
  source venv/bin/activate
else
  echo "⚠️ No virtual environment found — continuing without activation."
fi

# --- Ensure dependencies are installed ---
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# --- Run Django setup tasks ---
echo "⚙️ Running collectstatic and migrate..."
python manage.py collectstatic --noinput || true
python manage.py migrate --noinput || true

# --- Start Gunicorn server ---
echo "🔥 Starting Gunicorn..."
exec gunicorn student_alerts_app.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 3 \
  --timeout 120 \
  --log-file -
