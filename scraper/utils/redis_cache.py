import json
import time
import os
import logging

logger = logging.getLogger(__name__)

# Usar caminho relativo ou variável de ambiente para evitar dependência do Django
BASE_DIR = os.environ.get('DJANGO_BASE_DIR', os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
PROGRESS_DIR = os.path.join(BASE_DIR, 'media', 'progress')

def ensure_progress_dir():
    os.makedirs(PROGRESS_DIR, exist_ok=True)


def cache_progress(session_id: str, data: dict):
    try:
        ensure_progress_dir()
        progress_file = os.path.join(PROGRESS_DIR, f"{session_id}.json")
        payload = {
            'timestamp': time.time(),
            **data
        }
        with open(progress_file, 'w') as f:
            json.dump(payload, f, indent=2)
        logger.debug(f'Progresso salvo para sessão {session_id}: {data.get("message", "")}')
    except Exception as exc:
        logger.error('Falha ao salvar progresso: %s', exc)


def get_progress(session_id: str) -> dict | None:   
    try:
        ensure_progress_dir()
        progress_file = os.path.join(PROGRESS_DIR, f"{session_id}.json")
        if not os.path.exists(progress_file):
            return None

        with open(progress_file, 'r') as f:
            return json.load(f)
    except Exception as exc:
        logger.error('Falha ao ler progresso: %s', exc)
        return None

