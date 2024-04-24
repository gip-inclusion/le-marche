#!/usr/bin/env bash
set -e
echo ""
echo "================================================"
echo "= Le marché de l'inclusion Dev docker-compose  ="
echo "================================================"
echo ""

while ! pg_isready -h $POSTGRESQL_ADDON_HOST -p $POSTGRESQL_ADDON_PORT; do
    >&2 echo "Postgres is unavailable - sleeping"
    sleep 1
done

./manage.py migrate

./manage.py runserver 0.0.0.0:8880
