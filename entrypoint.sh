#!/bin/bash
set -e

# Collect static files at runtime (when env vars are available)
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Warning: collectstatic failed, continuing..."

# Use PORT from environment or default to 8000
PORT=${PORT:-8000}

# Replace PORT in the command if it's gunicorn
if [[ "$1" == "gunicorn" ]]; then
    exec gunicorn alx_project_nexus.wsgi:application --bind "0.0.0.0:${PORT}"
else
    exec "$@"
fi

