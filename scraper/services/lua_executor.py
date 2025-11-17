"""
Serviço para execução de scripts Lua via Splash.
Responsável por comunicação com Splash, processamento de resultados e salvamento de screenshots.
"""

import os
import time
import base64
import requests
from typing import Optional
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


def wrap_lua_script(lua_script: str) -> str:
    wrapper_lines = [
        "--[[ Script do usuário ]]--",
        lua_script,
        "",
        "local __esmeralda_user_main = main",
        "main = nil",
        "if type(__esmeralda_user_main) ~= 'function' then",
        "    error('Script deve definir function main(splash, args)')",
        "end",
        "",
        "local function __esmeralda_normalize_args(args)",
        "    local normalized = args or {}",
        "    if normalized.args then",
        "        for k, v in pairs(normalized.args) do",
        "            normalized[k] = v",
        "        end",
        "        normalized.args = nil",
        "    end",
        "    return normalized",
        "end",
        "",
        "function main(splash, args)",
        "    local normalized = __esmeralda_normalize_args(args)",
        "    return __esmeralda_user_main(splash, normalized)",
        "end",
    ]

    return "\n".join(wrapper_lines)


def execute_lua_script(lua_script: str, args: dict) -> dict:
    try:
        logger.info(f'Executando script Lua com args: {args}')

        splash_url = 'http://localhost:8050/execute'
        wrapped_script = wrap_lua_script(lua_script)

        splash_payload = {
            'lua_source': wrapped_script,
            'url': args.get('url', 'https://httpbin.org/html'),
            'wait': args.get('wait', 3),
            'html': args.get('html', 1),
            'png': args.get('png', 1),
        }

        for key, value in args.items():
            if key not in ['url', 'wait', 'html', 'png']:
                splash_payload[key] = value

        splash_payload['args'] = args

        logger.debug(f'Enviando payload para Splash: {splash_payload}')

        response = requests.post(splash_url, json=splash_payload, timeout=30)

        if response.status_code == 200:
            splash_result = response.json()

            if splash_result.get('error') or (splash_result.get('errors') and len(splash_result.get('errors', [])) > 0):
                error_msg = splash_result.get(
                    'error', 'Erro desconhecido no Splash')
                logger.error(f'Erro no script Lua: {error_msg}')

                return {
                    'script_executed': False,
                    'error': error_msg,
                    'details': splash_result.get('description', ''),
                    'splash_response': splash_result,
                    'timestamp': time.time()
                }

            logger.info('Script Lua executado com sucesso')

            result = {
                'script_executed': True,
                'timestamp': time.time(),
                'args_provided': args,
                'splash_response': splash_result
            }

            if splash_result.get('png'):
                try:
                    screenshot_url = _save_screenshot(splash_result['png'])
                    if screenshot_url:
                        result['screenshot_url'] = screenshot_url
                        logger.info(f'Screenshot salva: {screenshot_url}')
                    else:
                        result['screenshot_error'] = 'Erro ao salvar screenshot'
                except Exception as e:
                    logger.error(f'Erro ao processar screenshot: {str(e)}')
                    result['screenshot_error'] = str(e)

            return result

        else:
            error_msg = f'Erro no Splash: HTTP {response.status_code}'
            logger.error(f'{error_msg} - {response.text[:500]}')

            return {
                'script_executed': False,
                'error': error_msg,
                'details': response.text[:500],
                'timestamp': time.time()
            }

    except requests.RequestException as e:
        error_msg = f'Erro de conexão com Splash: {str(e)}'
        logger.error(error_msg)

        return {
            'script_executed': False,
            'error': error_msg,
            'timestamp': time.time()
        }

    except Exception as e:
        error_msg = f'Erro interno na execução Lua: {str(e)}'
        logger.error(error_msg)

        return {
            'script_executed': False,
            'error': error_msg,
            'timestamp': time.time()
        }


def _save_screenshot(png_data: str) -> Optional[str]:
    try:
        if isinstance(png_data, str) and png_data.startswith('data:image/png;base64,'):
            png_data = png_data.split(',')[1]

        png_bytes = base64.b64decode(png_data)

        screenshot_dir = os.path.join(
            settings.MEDIA_ROOT, 'screenshots', 'lua_editor')
        os.makedirs(screenshot_dir, exist_ok=True)

        timestamp = int(time.time())
        screenshot_filename = f"lua_script_{timestamp}.png"
        screenshot_path = os.path.join(screenshot_dir, screenshot_filename)

        with open(screenshot_path, 'wb') as f:
            f.write(png_bytes)

        return f"/media/screenshots/lua_editor/{screenshot_filename}"

    except Exception as e:
        logger.error(f'Erro ao salvar screenshot: {str(e)}')
        return None


def run_lua_script_job(session_id: str, lua_script: str, args: dict, steps: list = None, execution_id: int = None):
    from django.apps import apps
    ScriptExecution = apps.get_model('scraper', 'ScriptExecution')
    channel_layer = get_channel_layer()
    steps = steps or []

    def send_progress_event(event_type: str, **kwargs):
        event_data = {
            "type": event_type,
            "session_id": session_id,
            "timestamp": time.time(),
            **kwargs
        }

        async_to_sync(channel_layer.group_send)(
            f"notifications_session_{session_id}",
            event_data
        )

        async_to_sync(channel_layer.group_send)(
            "notifications_lua",
            event_data
        )

    try:
        logger.info(f'Iniciando job Lua para sessão {session_id}')

        # Pequeno delay para dar tempo do cliente se inscrever no WebSocket
        # (Necessário quando o cliente se inscreve após receber o session_id)
        time.sleep(1.0)

        execution = None
        if execution_id:
            try:
                execution = ScriptExecution.objects.get(id=execution_id)
                execution.status = 'running'
                execution.save()
            except ScriptExecution.DoesNotExist:
                logger.warning(
                    f'Execution {execution_id} não encontrada para sessão {session_id}')

        send_progress_event("lua_execution_progress", step_index=0,
                            step_title="Iniciando execução", status="running")

        for step in steps:
            send_progress_event(
                "lua_execution_progress",
                step_index=step.get("index"),
                step_title=step.get("title"),
                status="pending"
            )

        send_progress_event("lua_execution_progress", step_index=0,
                            step_title="Preparando script", status="running")

        result = execute_lua_script(lua_script, args)

        if result.get('script_executed'):
            logger.info(
                f'Script Lua executado com sucesso para sessão {session_id}')

            if execution:
                from django.utils import timezone
                execution.status = 'success'
                execution.finished_at = timezone.now()
                execution.response_data = result
                if result.get('screenshot_url'):
                    execution.screenshot_url = result.get('screenshot_url')
                execution.save()

                execution.script.last_executed_at = timezone.now()
                execution.script.save()

            for step in steps:
                send_progress_event(
                    "lua_execution_progress",
                    step_index=step.get("index"),
                    step_title=step.get("title"),
                    status="success"
                )

            send_progress_event(
                "lua_execution_completed",
                success=True,
                result=result
            )

        else:
            error_msg = result.get('error', 'Erro desconhecido')
            logger.error(
                f'Erro na execução Lua para sessão {session_id}: {error_msg}')

            if execution:
                from django.utils import timezone
                execution.status = 'error'
                execution.finished_at = timezone.now()
                execution.response_data = result
                execution.logs = error_msg
                execution.save()

            for step in steps:
                send_progress_event(
                    "lua_execution_progress",
                    step_index=step.get("index"),
                    step_title=step.get("title"),
                    status="error",
                    log=error_msg
                )

            send_progress_event(
                "lua_execution_error",
                error=error_msg,
                details=result.get('details')
            )

    except Exception as e:
        error_msg = f'Erro interno no job Lua: {str(e)}'
        logger.error(f'{error_msg} para sessão {session_id}')

        if execution:
            from django.utils import timezone
            execution.status = 'error'
            execution.finished_at = timezone.now()
            execution.logs = error_msg
            execution.save()

        send_progress_event(
            "lua_execution_error",
            error=error_msg
        )
