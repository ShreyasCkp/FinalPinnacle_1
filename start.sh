#!/bin/bash

# Exit on error
set -e

# Activate the virtual environment
source antenv/bin/activate

# Collect static files (optional, only first deploy if needed)
# python manage.py collectstatic --noinput

# Run migrations (optional)
# python manage.py migrate --noinput

# Start Gunicorn
gunicorn your_project_name.wsgi:application --bind 0.0.0.0:$PORT
