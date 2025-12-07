#!/bin/sh

set -e

echo "Waiting for MySQL..."
while ! mysqladmin ping -h"$DB_HOST" --silent; do
  sleep 1
done
echo "MySQL is ready."

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application with Gunicorn..."
# Allow docker-compose command to run (Gunicorn)
exec "$@"
