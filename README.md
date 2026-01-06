# Lua Web Scraper

Sistema de automação web com scripts Lua e Splash, incluindo editor online com execução em tempo real via WebSockets.

## Funcionalidades

- **Editor Lua Online**: Interface web para escrever e executar scripts Lua
- **Execução Assíncrona**: Scripts executados em background com feedback em tempo real
- **WebSockets**: Atualizações ao vivo do progresso de execução
- **Comentários como Passos**: Use comentários especiais (`-- 1. Descrição`) para definir passos executáveis
- **Gerenciamento de Scripts**: Salve, organize e version seus scripts Lua com histórico de execuções
- **Auto-salvamento**: Scripts são salvos automaticamente enquanto você edita
- **Autenticação Google**: Login seguro com contas Google
- **Sidebar Interativa**: Navegue facilmente entre seus scripts e exemplos pré-definidos
- **Scraping Python**: Suporte a scraping com Scrapy (integração futura)
- **Screenshot e HTML**: Captura automática de screenshots e HTML das páginas

## Tecnologias

- **Backend**: Django + Django Channels + Redis
- **Frontend**: Nuxt 3 + Vue 3 + TypeScript
- **Web Scraping**: Splash + Scrapy
- **Fila de Jobs**: RQ (Redis Queue)
- **Banco**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **WebSockets**: Django Channels com Redis como channel layer

## Instalação e Configuração

### Desenvolvimento

1. **Clonar o repositório**
   ```bash
   git clone <repository-url>
   cd lua-web-scrapper
   ```

2. **Instalar dependências Python**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Instalar dependências Node.js**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configurar autenticação Google** (obrigatório)
   - Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/)
   - Ative a Google+ API
   - Crie credenciais OAuth 2.0 do tipo "Web application"
   - Baixe o arquivo JSON de credenciais
   - **Coloque o arquivo na raiz do projeto como `credentials.json`**
   - Ou especifique um caminho personalizado:
     ```bash
     export GOOGLE_CREDENTIALS_FILE="caminho/para/seu-arquivo.json"
     ```

     **Estrutura esperada do arquivo JSON:**
     ```json
     {
       "web": {
         "client_id": "seu-client-id.apps.googleusercontent.com",
         "client_secret": "seu-client-secret"
       }
     }
     ```

     > ⚠️ **Importante**: Nunca commite arquivos de credenciais no Git. O arquivo `credentials.json` já está no `.gitignore`.

   - **Arquivo .env** (opcional):
     ```bash
     # Copie este conteúdo para um arquivo .env na raiz do projeto
     DEBUG=True
     SECRET_KEY=django-insecure-change-this-in-production
     GOOGLE_CREDENTIALS_FILE=credentials.json
     REDIS_URL=redis://127.0.0.1:6379/1
     ```

5. **Iniciar serviços**
   ```bash
   # Opção 1: Aplicação completa com monitoramento (recomendado)
   make start
   # ou
   ./start.sh

   # Opção 2: Desenvolvimento com WebSockets (ASGI)
   make dev-async

   # Opção 3: Desenvolvimento simples (WSGI, sem WebSockets)
   make dev
   ```

5. **Acessar aplicação**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Admin: http://localhost:8000/admin

### Comandos Make Disponíveis

```bash
make install      # Instalar todas as dependências
make docker-up    # Iniciar Redis e Splash via Docker
make docker-down  # Parar serviços Docker
make migrate      # Executar migrações Django

# Modos de desenvolvimento:
make dev          # Desenvolvimento WSGI (sem WebSockets)
make dev-async    # Desenvolvimento ASGI (com WebSockets)

# Produção/Completo:
make start        # Aplicação completa com monitoramento
make stop         # Parar todos os serviços
```

### Testes

Execute o script de teste WebSocket:

```bash
python test_websocket.py
```

#### Testando Autenticação Google

Para testar se as credenciais Google estão configuradas corretamente:

1. **Script de teste automatizado:**
   ```bash
   python test_google_auth.py
   ```

2. **Testar URLs de autenticação:**
   - Acesse http://localhost:8000/accounts/google/login/
   - Deve redirecionar para o login do Google se as credenciais estiverem corretas

## Produção

### Infra como Código (AWS + Terraform)
- **Recursos**: EC2 Ubuntu 22.04 com EIP e SG liberando 22/80/443; Docker + Compose instalados via `user_data`.
- **State**: Terraform Cloud (ajuste `organization/workspace` em `terraform/versions.tf`).
- **Variáveis principais** (`terraform/variables.tf`):
  - `aws_region` (padrão `sa-east-1`)
  - `instance_type` (padrão `t3.micro`)
  - `key_name` (obrigatório, Key Pair existente)
- **Execução local**:
  ```bash
  export TF_API_TOKEN=...
  export AWS_ACCESS_KEY_ID=...
  export AWS_SECRET_ACCESS_KEY=...

  terraform -chdir=terraform init
  terraform -chdir=terraform plan -var="key_name=seu-keypair"
  terraform -chdir=terraform apply -auto-approve -var="key_name=seu-keypair"
  ```
- **Arquivos sensíveis**: não commitar `*.tfvars`, `.terraform/`, `*.tfstate`.
- **Bootstrap**: o `user_data` cria `/srv/scraper-app` e instala Docker/Compose; o workflow envia `docker-compose.prod.yml`, `deploy/nginx.conf`, `.env.prod` e `credentials.json`.

### Pipeline (GitHub Actions)
- Job `provision-infra`: roda Terraform, gera `public_ip` (output).
- Job `build-and-deploy`: usa o IP dinâmico, publica no GHCR e faz deploy via SSH.
- Secrets necessários:
  - Infra: `TF_API_TOKEN`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_KEY_PAIR_NAME` (nome do Key Pair).
  - Deploy: `SSH_USER`, `SSH_KEY`, `SSH_PORT` (o host vem do Terraform).
  - App: `ENV_PROD` (conteúdo completo do `.env.prod`) e `GOOGLE_CREDENTIALS_JSON` (conteúdo do `credentials.json`).

### Configuração ASGI

O sistema usa Django Channels para WebSockets. Em produção, use um servidor ASGI:

**Daphne (recomendado):**
```bash
daphne lua_web_scrapper.asgi:application --bind 0.0.0.0 --port 8000
```

**Uvicorn:**
```bash
uvicorn lua_web_scrapper.asgi:application --host 0.0.0.0 --port 8000
```

### Nginx Reverse Proxy

Exemplo de configuração Nginx com suporte a WebSockets:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend Nuxt (SSR)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API Django
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSockets
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Arquivos estáticos
    location /_nuxt/ {
        proxy_pass http://localhost:3000;
    }

    location /media/ {
        alias /path/to/your/project/media/;
    }

    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }
}
```

### Docker Compose Produção

Para produção, use uma configuração mais robusta:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  splash:
    image: scrapinghub/splash:3.5
    environment:
      - SPLASH_ARGS=--max-timeout 300 --disable-private-mode --disable-xvfb
    volumes:
      - /tmp/splash-cache:/tmp/splash-cache
    restart: unless-stopped

  django:
    build: .
    command: daphne lua_web_scrapper.asgi:application --bind 0.0.0.0 --port 8000
    volumes:
      - .:/app
      - staticfiles:/app/staticfiles
      - media:/app/media
    environment:
      - DJANGO_SETTINGS_MODULE=lua_web_scrapper.settings
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - redis
      - splash
    restart: unless-stopped

  nuxt:
    build: ./frontend
    command: npm run build && npm run start
    volumes:
      - ./frontend:/app
    environment:
      - NODE_ENV=production
    restart: unless-stopped

volumes:
  redis_data:
  staticfiles:
  media:
```

## Uso

### Editor Lua

1. Acesse http://localhost:3000/lua-editor
2. Escreva seu script Lua usando comentários especiais para definir passos:
   ```lua
   function main(splash, args)
     -- 1. Acessar página inicial
     splash:go("https://example.com")
     splash:wait(2)

     -- 2. Extrair informações
     local title = splash:select('title'):text()

     -- 3. Retornar dados
     return {
       title = title,
       url = splash:url()
     }
   end
   ```
3. Clique em "Executar Script" para execução assíncrona com feedback em tempo real
4. Use "Execução Síncrona" como fallback

### API Endpoints

#### Autenticação
- `GET /api/auth/user/` - Informações do usuário autenticado (requer autenticação)
- `GET /accounts/google/login/` - Iniciar login com Google
- `POST /accounts/logout/` - Logout do usuário

#### Scripts Lua
- `GET /api/scripts/` - Lista scripts do usuário autenticado
- `POST /api/scripts/` - Criar novo script
- `GET /api/scripts/{id}/` - Detalhes de um script específico
- `PUT/PATCH /api/scripts/{id}/` - Atualizar script
- `DELETE /api/scripts/{id}/` - Deletar script
- `GET /api/scripts/{id}/executions/` - Lista execuções do script
- `GET /api/scripts/{id}/executions/latest/` - Última execução do script

#### Execução de Scripts
- `POST /api/lua/execute/` - Execução síncrona (aceita `script_id` opcional)
- `POST /api/lua/execute/async/` - Execução assíncrona com WebSocket (aceita `script_id` opcional)

#### WebSockets
- `WS /ws/notifications/` - WebSocket para notificações em tempo real

**Nota**: Todos os endpoints de scripts requerem autenticação via sessão Django.

## Gerenciamento de Scripts

### Autenticação e Login

O sistema utiliza autenticação com Google para proteger seus scripts. Para fazer login:

1. Clique em "Entrar com Google" no cabeçalho
2. Autorize o acesso à sua conta Google
3. Você será redirecionado de volta ao editor

### Sidebar de Scripts

A sidebar esquerda permite gerenciar seus scripts Lua:

#### Exemplos Pré-definidos
- **Screenshot do meu site**: Script que acessa https://www.mrleonardobrito.com/, tira screenshot e exibe
- **Wikipedia aleatória**: Script que acessa links aleatórios na Wikipedia e tira screenshots

#### Scripts Salvos
- Visualize todos os seus scripts salvos
- Veja o status da última execução (Sucesso/Erro/Nunca executado)
- Clique em um script para carregá-lo no editor

### Auto-salvamento

Seus scripts são salvos automaticamente enquanto você edita:
- O salvamento ocorre 1.5 segundos após parar de digitar
- Um indicador visual mostra o status: "Salvando...", "Salvo" ou "Erro ao salvar"
- Scripts são salvos apenas quando você está autenticado

### Criando e Editando Scripts

1. **Novo script**: Clique no botão "+" na sidebar para criar um script
2. **Carregar exemplo**: Clique em um exemplo na seção "Exemplos" para começar
3. **Editar**: Modifique o código e configurações - será salvo automaticamente
4. **Executar**: Use "Executar Script" (assíncrono) ou "Execução Síncrona"
5. **Histórico**: Cada execução é registrada com status, logs e screenshots

## Desenvolvimento

### Estrutura do Projeto

```
lua-web-scrapper/
├── lua_web_scrapper/          # Config Django
├── scraper/                   # App principal
│   ├── consumers.py           # WebSocket consumers
│   ├── services/              # Lógica de negócio
│   ├── utils/                 # Utilitários
│   └── views/                 # API endpoints
├── frontend/                  # Nuxt.js
│   ├── composables/           # Vue composables
│   ├── components/            # Componentes Vue
│   ├── pages/                 # Páginas Nuxt
│   └── public/                # Assets estáticos
├── staticfiles/               # Arquivos estáticos coletados
├── media/                     # Uploads
└── requirements.txt           # Dependências Python
```

### Scripts e Comandos Disponíveis

**Scripts:**
- `./start.sh` - Inicia aplicação completa (Django ASGI, Nuxt, Redis, Splash)
- `python test_websocket.py` - Testes WebSocket

**Comandos Make:**
- `make install` - Instalar dependências
- `make start` - Iniciar aplicação completa
- `make dev` - Desenvolvimento WSGI
- `make dev-async` - Desenvolvimento ASGI (WebSockets)
- `make stop` - Parar aplicação

**Django direto:**
- `./manage.py runserver` - Django WSGI (sem WebSocket)
- `daphne lua_web_scrapper.asgi:application` - Django ASGI (com WebSocket)

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto é open source sob a licença MIT.
