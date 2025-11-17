import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from drf_spectacular_websocket.decorators import extend_ws_schema
from .serializers import (
    SubscribeInputSerializer,
    SubscribedOutputSerializer,
    ErrorOutputSerializer,
    LuaExecutionProgressOutputSerializer,
    LuaExecutionCompletedOutputSerializer,
    LuaExecutionErrorOutputSerializer,
)

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        logger.info(f"WebSocket connection established: {self.channel_name}")
        await self.accept()

        await self.channel_layer.group_add(
            "notifications",
            self.channel_name
        )

    async def disconnect(self, close_code):
        logger.info(
            f"WebSocket connection closed: {self.channel_name}, code: {close_code}")

        for group in getattr(self, 'groups', []):
            await self.channel_layer.group_discard(group, self.channel_name)

    @extend_ws_schema(
        type='receive',
        summary='Receber mensagens do WebSocket',
        description='Recebe mensagens JSON do cliente. Ação suportada: "subscribe"',
        request=SubscribeInputSerializer,
        responses={
            200: SubscribedOutputSerializer,
            400: ErrorOutputSerializer,
        },
    )
    async def receive_json(self, content, **kwargs):
        try:
            serializer = SubscribeInputSerializer(data=content)
            if not serializer.is_valid():
                await self.send_error(f"Erro de validação: {serializer.errors}")
                return

            action = serializer.validated_data.get('action')
            session_id = serializer.validated_data.get('session_id')

            if action == 'subscribe':
                await self.handle_subscribe(session_id)
            else:
                logger.warning(f"Unknown action received: {action}")
                await self.send_error(f"Ação desconhecida: {action}")

        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            await self.send_error("Erro ao processar mensagem")

    @extend_ws_schema(
        type='send',
        summary='Enviar erro',
        description='Envia mensagem de erro para o cliente',
        request=None,
        responses=ErrorOutputSerializer,
    )
    async def send_error(self, message):
        await self.send_json({
            "type": "error",
            "message": message
        })

    @extend_ws_schema(
        type='send',
        summary='Confirmar inscrição',
        description='Confirma que a inscrição foi realizada com sucesso',
        request=None,
        responses=SubscribedOutputSerializer,
    )
    async def handle_subscribe(self, session_id):
        if not hasattr(self, 'groups'):
            self.groups = []

        group_name = "notifications_lua"
        await self.channel_layer.group_add(group_name, self.channel_name)
        self.groups.append(group_name)
        logger.debug(f"Subscribed {self.channel_name}")

        if session_id:
            group_name = f"notifications_session_{session_id}"
            await self.channel_layer.group_add(group_name, self.channel_name)
            self.groups.append(group_name)
            logger.debug(
                f"Subscribed {self.channel_name} to session: {session_id}")

        await self.send_json({
            "type": "subscribed",
            "session_id": session_id,
            "message": "Inscrição realizada com sucesso"
        })

    @extend_ws_schema(
        type='send',
        summary='Progresso da execução Lua',
        description='Notifica sobre o progresso de cada passo da execução do script Lua',
        request=None,
        responses=LuaExecutionProgressOutputSerializer,
    )
    async def lua_execution_progress(self, event):
        await self.send_json({
            "type": "lua_execution_progress",
            "session_id": event["session_id"],
            "step_index": event.get("step_index"),
            "step_title": event.get("step_title"),
            "status": event.get("status", "running"),
            "log": event.get("log"),
            "timestamp": event.get("timestamp"),
        })

    @extend_ws_schema(
        type='send',
        summary='Execução Lua concluída',
        description='Notifica que a execução do script Lua foi concluída com sucesso',
        request=None,
        responses=LuaExecutionCompletedOutputSerializer,
    )
    async def lua_execution_completed(self, event):
        await self.send_json({
            "type": "lua_execution_completed",
            "session_id": event["session_id"],
            "success": event.get("success", False),
            "result": event.get("result"),
            "error": event.get("error"),
            "timestamp": event.get("timestamp"),
        })

    @extend_ws_schema(
        type='send',
        summary='Erro na execução Lua',
        description='Notifica sobre erros ocorridos durante a execução do script Lua',
        request=None,
        responses=LuaExecutionErrorOutputSerializer,
    )
    async def lua_execution_error(self, event):
        await self.send_json({
            "type": "lua_execution_error",
            "session_id": event["session_id"],
            "error": event.get("error"),
            "details": event.get("details"),
            "timestamp": event.get("timestamp"),
        })
