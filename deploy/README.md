# Guia de Deploy

Este diretório contém os arquivos de configuração para deploy em produção na DigitalOcean.

## Estrutura de Arquivos

```
/srv/scraper-app/          # No servidor (Droplet)
├── docker-compose.prod.yml
├── .env.prod
├── deploy/
│   └── nginx.conf
└── credentials.json       # Arquivo de credenciais Google OAuth
```

## Pré-requisitos

1. **Droplet na DigitalOcean** com Docker e Docker Compose instalados
2. **GitHub Actions** configurado com secrets:
   - `SSH_HOST`: IP ou domínio do Droplet
   - `SSH_USER`: Usuário SSH (geralmente `root`)
   - `SSH_KEY`: Chave privada SSH para acesso ao servidor
   - `SSH_PORT`: Porta SSH (opcional, padrão 22)

## Configuração Inicial no Servidor

1. **Conectar ao Droplet via SSH**

2. **Criar diretório da aplicação:**
   ```bash
   mkdir -p /srv/scraper-app/deploy
   cd /srv/scraper-app
   ```

3. **Copiar arquivos de configuração:**
   ```bash
   # Copiar docker-compose.prod.yml
   # Copiar deploy/nginx.conf
   # Criar .env.prod baseado em .env.prod.example
   ```

4. **Configurar variáveis de ambiente:**
   ```bash
   cp .env.prod.example .env.prod
   nano .env.prod  # Editar com valores reais
   ```

5. **Adicionar credenciais Google OAuth:**
   ```bash
   # Copiar credentials.json para /srv/scraper-app/
   ```

6. **Ajustar permissões:**
   ```bash
   chmod 600 .env.prod
   chmod 600 credentials.json
   ```

## Configuração do GitHub Actions

1. **Acessar Settings > Secrets and variables > Actions** no repositório GitHub

2. **Adicionar os seguintes secrets:**
   - `SSH_HOST`: IP ou domínio do servidor
   - `SSH_USER`: Usuário SSH
   - `SSH_KEY`: Chave privada SSH completa
   - `SSH_PORT`: Porta SSH (opcional)

## Deploy Automatizado

O deploy é executado automaticamente quando há push para a branch `main`.

### Deploy Manual

Você também pode executar o workflow manualmente:
1. Acessar a aba "Actions" no GitHub
2. Selecionar "Deploy to DigitalOcean"
3. Clicar em "Run workflow"

## Verificação Pós-Deploy

Após o deploy, verificar:

1. **Status dos containers:**
   ```bash
   cd /srv/scraper-app
   docker compose -f docker-compose.prod.yml ps
   ```

2. **Logs dos serviços:**
   ```bash
   docker compose -f docker-compose.prod.yml logs -f web
   docker compose -f docker-compose.prod.yml logs -f worker
   docker compose -f docker-compose.prod.yml logs -f nginx
   ```

3. **Testar aplicação:**
   - Acessar http://seu-ip-ou-dominio
   - Verificar se a API responde
   - Testar WebSocket em /ws/notifications/

## Rollback

Para voltar a uma versão anterior:

```bash
cd /srv/scraper-app
docker compose -f docker-compose.prod.yml pull ghcr.io/seu-usuario/lua-web-scrapper-web:COMMIT_SHA_ANTERIOR
docker compose -f docker-compose.prod.yml up -d web worker
```

## Manutenção

### Atualizar variáveis de ambiente

1. Editar `.env.prod` no servidor
2. Reiniciar serviços:
   ```bash
   docker compose -f docker-compose.prod.yml restart web worker
   ```

### Backup do banco de dados

```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U scraper scraper > backup_$(date +%Y%m%d).sql
```

### Limpeza de volumes antigos

```bash
docker system prune -a --volumes
```

## Troubleshooting

### Container não inicia
- Verificar logs: `docker compose -f docker-compose.prod.yml logs web`
- Verificar variáveis de ambiente: `docker compose -f docker-compose.prod.yml config`

### Erro de conexão com banco
- Verificar se o container `db` está rodando
- Verificar variáveis `POSTGRES_*` no `.env.prod`

### WebSocket não funciona
- Verificar configuração do Nginx (upgrade headers)
- Verificar se o serviço `web` está usando Daphne (ASGI)

### Arquivos estáticos não aparecem
- Executar: `docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput`
- Verificar volume `static_data` no docker-compose



