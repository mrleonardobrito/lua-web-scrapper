#!/usr/bin/env bash
set -euo pipefail

cd /app

APP_USER="${APP_USER:-app}"
APP_GROUP="${APP_GROUP:-app}"
STATIC_DIR="${STATIC_DIR:-/app/staticfiles}"
MEDIA_DIR="${MEDIA_DIR:-/app/media}"

echo "Ajustando permissões dos volumes..."
mkdir -p "$STATIC_DIR" "$MEDIA_DIR"

if [ "$(id -u)" = "0" ]; then
  if ! chown -R "${APP_USER}:${APP_GROUP}" "$STATIC_DIR" "$MEDIA_DIR" >/dev/null 2>&1; then
    echo "Aviso: Não foi possível ajustar permissões dos volumes montados (Operation not permitted)."
  fi
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  echo "Coletando arquivos estáticos..."
  python manage.py collectstatic --noinput || true
fi

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "Aplicando migrations..."
  python manage.py migrate --noinput
fi

# Se nenhum comando foi passado (ex: Dockerfile sem CMD), usamos Gunicorn como padrão.
if [ "$#" -eq 0 ]; then
  set -- gunicorn lua_web_scrapper.wsgi:application --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-3}"
fi

echo "Iniciando: $*"

if [ "$(id -u)" = "0" ]; then
  exec gosu "${APP_USER}:${APP_GROUP}" "$@"
fi

exec "$@"
