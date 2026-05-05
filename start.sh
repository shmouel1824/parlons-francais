#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn parle_francais.wsgi --bind 0.0.0.0:${PORT:-8000}