#!/bin/bash
set -e

echo "Updating package sources and installing Cairo system dependencies..."

# Fix deprecated Debian repositories for Azure App Service base images
sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list
sed -i 's|security.debian.org|archive.debian.org|g' /etc/apt/sources.list
apt-get -o Acquire::Check-Valid-Until=false update -y

# Install required system packages for xhtml2pdf, reportlab, and Cairo
apt-get install -y \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpango1.0-dev \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info

apt-get clean
rm -rf /var/lib/apt/lists/*

echo "Applying database migrations..."
python manage.py migrate --noinput || echo "⚠️ Migrations failed (check DB config), continuing startup..."

echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️ Collectstatic failed, continuing startup..."

echo "Starting Gunicorn server..."
exec gunicorn student_alerts_app.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --timeout 180 \
    --log-level info \
    --log-file -
