#!/bin/sh

set -e

echo "Waiting for MySQL..."
while ! nc -z mysql 3306; do
  sleep 1
done
echo "MySQL is up."

echo "Applying Django migrations (FAKE)..."
python manage.py migrate --fake

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Check if initial data is already loaded
echo "Checking if database is empty..."
ROWCOUNT=$(echo "SELECT COUNT(*) FROM zone;" | mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -h mysql -D "$MYSQL_DATABASE" | tail -n 1)

if [ "$ROWCOUNT" = "0" ]; then
  echo "Loading initial data..."
  python manage.py loaddata zones.json
else
  echo "Initial data already present. Skipping loaddata."
fi

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000
