#!/bin/bash
echo "=== Starting migrations ==="
python manage.py migrate --noinput
echo "=== Migrations done ==="
echo "=== Creating admin user ==="
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@parlons.com', 'qazwsx')
    print('Admin created')
else:
    print('Admin already exists')
"
echo "=== Loading data ==="
python manage.py loaddata data.json || echo "=== Loaddata failed or already loaded ==="
echo "=== Starting collectstatic ==="
python manage.py collectstatic --noinput || echo "=== Collectstatic failed but continuing ==="
echo "=== Starting gunicorn ==="
exec gunicorn parle_francais.wsgi --bind 0.0.0.0:${PORT:-8000}