# Install system libs
apt-get -o Acquire::Check-Valid-Until=false update -y
apt-get install -y libcairo2 libpango-1.0-0 libffi-dev ...
apt-get clean && rm -rf /var/lib/apt/lists/*

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r /home/site/wwwroot/requirements.txt

echo "Applying database migrations..."
python manage.py migrate --noinput || echo "⚠️ Migrations failed"

echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️ Collectstatic failed"

echo "Starting Gunicorn..."
exec gunicorn student_alerts_app.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 180
