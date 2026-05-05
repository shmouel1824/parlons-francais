#!/bin/bash
echo "=== Starting migrations ==="
python manage.py migrate --noinput
echo "=== Migrations done ==="
echo "=== Starting collectstatic ==="
python manage.py collectstatic --noinput || echo "=== Collectstatic failed but continuing ==="
echo "=== Starting gunicorn ==="
exec gunicorn parle_francais.wsgi --bind 0.0.0.0:${PORT:-8000}
echo "=== Gunicorn started ==="