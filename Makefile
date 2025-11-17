.PHONY: install start dev stop migrate docker-up docker-down kill-ports

# Variáveis
PWD := $(shell pwd)
VENV = venv
PYTHON = $(PWD)/$(VENV)/bin/python
PIP = $(PWD)/$(VENV)/bin/pip
DAPHNE = $(PWD)/$(VENV)/bin/daphne
MANAGE = $(PYTHON) manage.py
FRONTEND_DIR = frontend
CONCURRENTLY = $(FRONTEND_DIR)/node_modules/.bin/concurrently

install:
	@echo "🚀 Instalando dependências do projeto..."
	@echo "📦 Criando ambiente virtual Python..."
	@python -m venv $(VENV)
	@echo "📥 Instalando dependências Python..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "📦 Instalando dependências do frontend..."
	@cd $(FRONTEND_DIR) && npm install
	@echo "✅ Instalação concluída!"
	@echo "⚠️ Ative o ambiente virtual com: source ./$(VENV)/bin/activate"

docker-up:
	@echo "🐳 Iniciando Docker Compose (Redis e Splash)..."
	@docker compose up -d
	@echo "⏳ Aguardando serviços Docker iniciarem..."
	@sleep 3

docker-down:
	@echo "🛑 Parando Docker Compose..."
	@docker compose down 

kill-ports:
	@echo "🔍 Verificando portas em uso..."
	@if command -v lsof >/dev/null 2>&1; then \
		for port in 8000 24678 3000; do \
			PID=$$(lsof -ti :$$port 2>/dev/null); \
			if [ ! -z "$$PID" ]; then \
				echo "🛑 Encerrando processo na porta $$port (PID: $$PID)..."; \
				kill -9 $$PID 2>/dev/null || true; \
			fi; \
		done; \
		echo "✅ Portas liberadas!"; \
	else \
		echo "⚠️  lsof não encontrado. Pulando verificação de portas."; \
	fi

migrate:
	@echo "🔄 Executando migrações do Django..."
	@$(MANAGE) migrate

collectstatic:
	@echo "📦 Coletando arquivos estáticos..."
	@$(MANAGE) collectstatic --noinput

dev: kill-ports docker-up migrate collectstatic
	@echo "🚀 Iniciando aplicação em modo desenvolvimento (ASGI com WebSockets)..."
	@echo "📝 Django ASGI: http://localhost:8000"
	@echo "📝 Frontend: http://localhost:3000"
	@echo "📝 Admin: http://localhost:8000/admin"
	@echo ""
	@if [ ! -f "$(DAPHNE)" ]; then \
		echo "❌ Erro: daphne não encontrado em $(DAPHNE)"; \
		echo "💡 Execute: source $(VENV)/bin/activate && pip install daphne"; \
		exit 1; \
	fi
	@$(CONCURRENTLY) \
		--names "Django-ASGI,Nuxt" \
		--prefix-colors "magenta,green" \
		--kill-others \
		--kill-others-on-fail \
		"$(DAPHNE) lua_web_scrapper.asgi:application --bind localhost --port 8000" \
		"cd $(FRONTEND_DIR) && npm run dev"

stop: kill-ports docker-down
	@echo "✅ Aplicação parada!"

