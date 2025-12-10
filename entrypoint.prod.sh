#!/bin/sh

set -e

echo "Waiting for MySQL..."
while ! nc -z db 3306; do
  sleep 1
done
echo "MySQL is up."

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application with Gunicorn..."
# Allow docker-compose command to run (Gunicorn)
exec "$@"
