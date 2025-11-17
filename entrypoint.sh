#!/usr/bin/env bash
set -e

cd /application

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput || true

echo "Aplicando migrations..."
python manage.py migrate --noinput

echo "Iniciando Gunicorn..."
exec gunicorn project.wsgi:application --bind 0.0.0.0:8000 --workers 3
