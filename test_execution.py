#!/usr/bin/env python3
"""
Script de teste para verificar execução de script Lua e recebimento de screenshots
"""
import json
import uuid
import requests
import websocket
import time
import threading
from typing import Optional

# Configurações
API_BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/notifications/"

# Script Lua de teste que gera screenshot
LUA_SCRIPT = """function main(splash, args)
  -- Passo 1: Navegar para a URL
  splash:go(args.url or "https://www.mrleonardobrito.com/")
  -- Passo 2: Aguardar carregamento
  splash:wait(args.wait or 3)
  -- Passo 3: Capturar screenshot
  local screenshot = splash:png()
  return {
    screenshot = screenshot,
    url = splash:url(),
    title = splash:select('title') and splash:select('title'):text() or "Sem título"
  }
end"""

ARGS = {
    "url": "https://www.mrleonardobrito.com/",
    "wait": 3,
    "png": True
}

STEPS = [
    {"index": 0, "title": "Passo 1: Navegar para a URL", "commentLine": 2},
    {"index": 1, "title": "Passo 2: Aguardar carregamento", "commentLine": 4},
    {"index": 2, "title": "Passo 3: Capturar screenshot", "commentLine": 6}
]

class WebSocketClient:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.ws = None
        self.messages = []
        self.subscribed = False
        self.completed = False
        self.screenshot_received = False
        self.error = None

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.messages.append(data)
            print(f"📨 Mensagem recebida: {data.get('type')}")

            if data.get('type') == 'subscribed':
                if data.get('session_id') == self.session_id:
                    self.subscribed = True
                    print(f"✅ Inscrito com sucesso na sessão {self.session_id}")

            elif data.get('type') == 'lua_execution_progress':
                step_title = data.get('step_title', 'N/A')
                status = data.get('status', 'N/A')
                print(f"  📊 Progresso: {step_title} - {status}")

            elif data.get('type') == 'lua_execution_completed':
                self.completed = True
                result = data.get('result', {})
                if result.get('screenshot_url'):
                    self.screenshot_received = True
                    print(f"✅ Screenshot recebido: {result.get('screenshot_url')}")
                print(f"✅ Execução concluída com sucesso!")
                print(f"   Resultado: {json.dumps(result, indent=2)}")

            elif data.get('type') == 'lua_execution_error':
                self.completed = True
                self.error = data.get('error', 'Erro desconhecido')
                print(f"❌ Erro na execução: {self.error}")

        except json.JSONDecodeError as e:
            print(f"❌ Erro ao decodificar mensagem: {e}")

    def on_error(self, ws, error):
        print(f"❌ Erro WebSocket: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"🔌 WebSocket fechado: {close_status_code} - {close_msg}")

    def on_open(self, ws):
        print(f"🔌 WebSocket conectado")
        # Inscrever-se na sessão
        subscribe_msg = {
            "action": "subscribe",
            "session_id": self.session_id
        }
        ws.send(json.dumps(subscribe_msg))
        print(f"📤 Mensagem de inscrição enviada para sessão {self.session_id}")

    def connect(self):
        self.ws = websocket.WebSocketApp(
            WS_URL,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        # Executar em thread separada
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()
        return wst

    def wait_for_subscription(self, timeout=5):
        start = time.time()
        while not self.subscribed and (time.time() - start) < timeout:
            time.sleep(0.1)
        return self.subscribed

    def wait_for_completion(self, timeout=120):
        start = time.time()
        while not self.completed and (time.time() - start) < timeout:
            time.sleep(0.5)
        return self.completed


def test_execution():
    print("=" * 60)
    print("🧪 TESTE DE EXECUÇÃO DE SCRIPT LUA COM SCREENSHOT")
    print("=" * 60)
    print()

    # 1. Conectar ao WebSocket primeiro
    print("1️⃣  Conectando ao WebSocket...")
    ws_client = WebSocketClient("placeholder")  # Será atualizado depois
    ws_thread = ws_client.connect()
    time.sleep(1)  # Aguardar conexão
    print()

    # 2. Enviar requisição de execução (backend vai gerar session_id)
    print("2️⃣  Enviando requisição de execução...")
    try:
        response = requests.post(
            f"{API_BASE}/api/lua/execute/",
            json={
                "script": LUA_SCRIPT,
                "args": ARGS,
                "steps": STEPS,
                "session_id": None  # Tentar passar None para ver se funciona
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        session_id = result.get('session_id')
        print(f"✅ Requisição enviada com sucesso")
        print(f"   Job ID: {result.get('job_id')}")
        print(f"   Session ID retornado: {session_id}")
        print()

        # Atualizar session_id do cliente WebSocket
        ws_client.session_id = session_id
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar requisição: {e}")
        return False

    # 3. Inscrever-se na sessão retornada
    print("3️⃣  Inscrevendo-se na sessão retornada...")
    subscribe_msg = {
        "action": "subscribe",
        "session_id": session_id
    }
    ws_client.ws.send(json.dumps(subscribe_msg))
    print(f"📤 Mensagem de inscrição enviada para sessão {session_id}")
    
    # Aguardar confirmação de inscrição
    if not ws_client.wait_for_subscription(timeout=5):
        print("⚠️  Timeout aguardando confirmação de inscrição, continuando mesmo assim...")
    print()

    # 4. Aguardar conclusão e screenshot
    print("4️⃣  Aguardando conclusão da execução e screenshot...")
    print("   (Isso pode levar alguns segundos...)")
    print()

    completed = ws_client.wait_for_completion(timeout=120)

    if not completed:
        print("❌ Timeout aguardando conclusão da execução")
        print(f"   Mensagens recebidas: {len(ws_client.messages)}")
        for msg in ws_client.messages:
            print(f"   - {msg.get('type')}")
        return False

    # 5. Verificar resultado
    print()
    print("5️⃣  Verificando resultado...")
    print()

    if ws_client.error:
        print(f"❌ Execução falhou: {ws_client.error}")
        return False

    if ws_client.screenshot_received:
        print("✅ SUCESSO! Screenshot foi recebido via WebSocket")
        print()
        print("📋 Resumo das mensagens recebidas:")
        for i, msg in enumerate(ws_client.messages, 1):
            msg_type = msg.get('type', 'unknown')
            if msg_type == 'lua_execution_progress':
                print(f"   {i}. {msg_type} - {msg.get('step_title')} ({msg.get('status')})")
            elif msg_type == 'lua_execution_completed':
                result = msg.get('result', {})
                screenshot_url = result.get('screenshot_url', 'N/A')
                print(f"   {i}. {msg_type} - Screenshot: {screenshot_url}")
            else:
                print(f"   {i}. {msg_type}")
        return True
    else:
        print("⚠️  Execução concluída mas screenshot não foi recebido")
        print(f"   Mensagens recebidas: {len(ws_client.messages)}")
        return False


if __name__ == "__main__":
    try:
        success = test_execution()
        print()
        print("=" * 60)
        if success:
            print("✅ TESTE PASSOU!")
        else:
            print("❌ TESTE FALHOU!")
        print("=" * 60)
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Teste interrompido pelo usuário")
        exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

