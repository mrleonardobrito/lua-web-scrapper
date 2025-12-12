#!/usr/bin/env bash
set -e

cd /app

echo "Ajustando permissões dos volumes..."
mkdir -p /app/staticfiles /app/media
chown -R app:app /app/staticfiles /app/media

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput || true

echo "Aplicando migrations..."
python manage.py migrate --noinput

echo "Iniciando Gunicorn..."
exec gunicorn project.wsgi:application --bind 0.0.0.0:8000 --workers 3
