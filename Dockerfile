FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    pkg-config libcairo2-dev libfreetype6-dev libpng-dev libfontconfig1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "student_alerts_app.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "600"]
