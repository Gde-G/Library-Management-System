#!/bin/ash

echo "Apply DB migrations"
python3 manage.py migrate

exec "$@"

