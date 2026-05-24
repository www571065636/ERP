#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating superuser..."
ADMIN_USERNAME="${DJANGO_ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${DJANGO_ADMIN_PASSWORD}"
ADMIN_REALNAME="${DJANGO_ADMIN_REALNAME:-管理员}"
if [ -z "$ADMIN_PASSWORD" ]; then
    ADMIN_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(16))")
    echo ">>> DJANGO_ADMIN_PASSWORD not set. Generated random password: $ADMIN_PASSWORD <<<"
fi
python manage.py shell -c "
from system.models import User
if not User.objects.filter(username='$ADMIN_USERNAME').exists():
    User.objects.create_superuser(username='$ADMIN_USERNAME', password='$ADMIN_PASSWORD', real_name='$ADMIN_REALNAME')
    print('Superuser created: $ADMIN_USERNAME')
else:
    print('Superuser already exists')
"

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
