#!/bin/bash
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput || true
exec gunicorn parle_francais.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 2