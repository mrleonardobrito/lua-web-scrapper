
import json
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from ..utils.error_responses import validation_error, not_found_error, internal_server_error
from ..services.lua_executor import run_lua_script_job
from ..models import Script, ScriptExecution

import django_rq
import logging

logger = logging.getLogger(__name__)


class ExecuteLuaScriptAsyncView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['script-executions'],
        summary='Executar script Lua de forma assíncrona',
        description="""
Inicia execução assíncrona de script Lua via RQ worker. 

**Importante:** O resultado e progresso da execução são enviados via WebSocket.
Para receber as notificações, conecte-se ao WebSocket em `/ws/notifications/` e 
inscreva-se na sessão retornada.

**Fluxo:**
1. Chame este endpoint para iniciar a execução
2. Receba `session_id` na resposta
3. Conecte-se ao WebSocket `/ws/notifications/`
4. Envie mensagem de subscribe com o `session_id`:
   ```json
   {
     "action": "subscribe",
     "session_id": "session-id-retornado"
   }
   ```
5. Receba notificações de progresso e resultado via WebSocket

**Tipos de mensagens WebSocket recebidas:**
- `lua_execution_progress`: Progresso de cada passo da execução
- `lua_execution_completed`: Execução finalizada com sucesso
- `lua_execution_error`: Erro durante a execução
""",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'script': {
                        'type': 'string',
                        'description': 'Script Lua a ser executado',
                        'example': 'function main(splash, args)\n  splash:go(args.url)\n  return {html=splash:html()}\nend'
                    },
                    'args': {
                        'type': 'object',
                        'description': 'Argumentos para o script',
                        'properties': {
                            'url': {'type': 'string', 'example': 'https://example.com'},
                            'wait': {'type': 'number', 'example': 3},
                            'html': {'type': 'boolean', 'example': True},
                            'png': {'type': 'boolean', 'example': True}
                        }
                    },
                    'steps': {
                        'type': 'array',
                        'description': 'Passos extraídos dos comentários (opcional)',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'index': {'type': 'integer'},
                                'title': {'type': 'string'},
                                'commentLine': {'type': 'integer'}
                            }
                        }
                    },
                    'script_id': {
                        'type': 'integer',
                        'description': 'ID do script salvo (opcional, para usuários autenticados)'
                    }
                },
                'required': ['script', 'args']
            }
        },
        responses={
            200: {
                'description': 'Script enfileirado com sucesso. Use o session_id para se inscrever no WebSocket.',
                'content': {
                    'application/json': {
                        'example': {
                            'session_id': '550e8400-e29b-41d4-a716-446655440000',
                            'job_id': 'abc123',
                            'status': 'enqueued',
                            'message': 'Script Lua enfileirado para execução',
                            'websocket_url': 'ws://localhost:8000/ws/notifications/',
                            'note': 'Conecte-se ao WebSocket e inscreva-se usando o session_id para receber atualizações'
                        }
                    }
                }
            },
            400: {
                'description': 'Erro de validação',
                'content': {
                    'application/json': {
                        'example': {
                            'error': 'Script Lua é obrigatório',
                            'code': 'validation_error',
                            'status': 400
                        }
                    }
                }
            },
            404: {
                'description': 'Script não encontrado',
                'content': {
                    'application/json': {
                        'example': {
                            'error': 'Script não encontrado ou não pertence ao usuário',
                            'code': 'not_found',
                            'status': 404
                        }
                    }
                }
            },
            500: {
                'description': 'Erro interno do servidor',
                'content': {
                    'application/json': {
                        'example': {
                            'error': 'Erro interno: ...',
                            'code': 'internal_server_error',
                            'status': 500
                        }
                    }
                }
            }
        }
    )
    def post(self, request):
        try:
            data = request.data
            lua_script = data.get('script', '').strip()
            args = data.get('args', {})
            steps = data.get('steps', [])
            script_id = data.get('script_id')
            session_id = data.get('session_id', '').strip(
            ) if data.get('session_id') else None

            # Log para debug
            logger.info(f'Session ID recebido: {session_id}')

            if not lua_script:
                return validation_error('Script Lua é obrigatório')

            if len(lua_script) > 10000:
                return validation_error('Script Lua muito longo (máx. 10KB)')

            if not isinstance(args, dict):
                return validation_error('args deve ser um objeto JSON')

            dangerous_patterns = [
                'os.execute', 'io.popen', 'loadfile', 'dofile',
                'require.*os', 'require.*io', 'package.loadlib'
            ]

            import re
            for pattern in dangerous_patterns:
                if re.search(pattern, lua_script, re.IGNORECASE):
                    return validation_error(f'Comando perigoso detectado: {pattern}')

            if 'function main' not in lua_script:
                return validation_error('Script deve conter uma função main(splash, args)')

            script = None
            if script_id:
                # Se script_id for fornecido, o usuário deve estar autenticado
                if not request.user.is_authenticated:
                    return validation_error('script_id requer autenticação')
                try:
                    script = Script.objects.get(
                        id=script_id, user=request.user)
                except Script.DoesNotExist:
                    return not_found_error('Script não encontrado ou não pertence ao usuário')

            execution = None
            if request.user.is_authenticated and script:
                execution = ScriptExecution.objects.create(
                    script=script,
                    status='pending',
                    request_args=args
                )

            # Gerar session_id apenas se não foi fornecido pelo frontend
            if not session_id:
                session_id = str(uuid.uuid4())
                logger.info(f'Gerando novo session_id: {session_id}')
            else:
                logger.info(f'Usando session_id fornecido: {session_id}')

            queue = django_rq.get_queue('lua_execution', default_timeout=300)
            job = queue.enqueue(
                run_lua_script_job,
                session_id,
                lua_script,
                args,
                steps,
                execution.id if execution else None
            )

            logger.info(
                f'Job Lua enfileirado: {job.id} para sessão {session_id}')

            return Response({
                'session_id': session_id,
                'job_id': job.id,
                'status': 'enqueued',
                'message': 'Script Lua enfileirado para execução'
            }, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            return validation_error('JSON inválido no body da requisição')
        except Exception as e:
            logger.error(
                f'Erro ao iniciar execução Lua assíncrona: {str(e)}', exc_info=True)
            return internal_server_error(f'Erro interno: {str(e)}')
