#!/bin/sh

set -e

echo "Waiting for MySQL..."
while ! nc -z db 3306; do
  sleep 1
done
echo "MySQL is up."

echo "Applying Django migrations (FAKE)..."
python manage.py migrate --fake

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Check if initial data is already loaded
echo "Loading initial zones data..."
python manage.py loaddata zones.json || echo "Already loaded"

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000
