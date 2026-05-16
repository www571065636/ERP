#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating superuser..."
python manage.py shell -c "
from system.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(username='admin', password='admin123', real_name='管理员')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
"

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
