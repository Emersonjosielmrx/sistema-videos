# Proxy Pool e OpenRouter - Guia de Deploy

Sistema de rotação de chaves OpenRouter + proxies Webshare para distribuir carga e evitar rate limits.

## Arquivos Criados

### Backend (Go)
- `cmd/server/proxy_pool.go` - Sistema de rotação de proxies HTTP
- `cmd/server/llm_key_pool.go` - Integração proxy + key rotation (MODIFICADO)
- `cmd/server/server.go` - Inicialização do proxy pool (MODIFICADO)
- `internal/settings/store.go` - ProxySettings (MODIFICADO)

### Deploy
- `deploy/add_openrouter_keys.py` - Script Python para adicionar chaves via API
- `deploy/add-openrouter-keys.sh` - Script Bash alternativo

## Como Funciona

### Rotação Dupla (Chaves + Proxies)

O sistema rotaciona **duas** camadas simultaneamente:

1. **Key Pool** - Rotaciona entre múltiplas chaves OpenRouter do mesmo usuário
2. **Proxy Pool** - Rotaciona entre múltiplos proxies Webshare

Quando uma requisição falha:
- **429 (rate limit)**: descansa proxy (2min) + chave (30s), tenta próximos
- **401/403 (auth)**: descansa chave (30min), tenta próxima
- **502/503 (rede)**: descansa proxy (30s), tenta próximo

### Proxies Rotativos (-rotate)

Os proxies têm `-rotate` no username, então **cada requisição usa um IP diferente automaticamente**. O pool gerencia apenas **qual proxy** usar, não qual IP (isso é feito pelo Webshare).

## Deploy nas VPS

### VPS 1: 62.171.128.241 (nproxy)
```bash
ssh root@62.171.128.241
# Senha: <removido — ver cofre>

cd /root/hermes-call
git pull

# Instalar dependências do Python
apt-get update && apt-get install -y python3-pip
pip3 install requests

# Obter token JWT (faça login no painel e pegue do localStorage ou cookie)
export HERMES_TOKEN="<SEGREDO_REMOVIDO>"

# Adicionar chaves e proxies
python3 deploy/add_openrouter_keys.py --url http://localhost:8080

# OU via variável de ambiente
export HERMES_API_URL="http://localhost:8080"
python3 deploy/add_openrouter_keys.py

# Rebuild e restart
docker-compose down
docker-compose build
docker-compose up -d

# Verificar logs
docker-compose logs -f | grep "proxy pool"
```

### VPS 2: 209.145.60.53 (root)
```bash
ssh root@209.145.60.53
# Senha: <removido — ver cofre>

# Mesmos passos acima
```

## Configuração Alternativa via ENV

Se preferir configurar via variáveis de ambiente em vez do banco:

```bash
# No docker-compose.yml ou systemd service
HERMES_PROXY_URLS="http://<USUARIO>:<SEGREDO_REMOVIDO>@host1:port1,http://<USUARIO>:<SEGREDO_REMOVIDO>@host2:port2,..."
```

O sistema carrega proxies nesta ordem de prioridade:
1. Settings do banco (tabela `settings`, chave `proxy`)
2. Variável de ambiente `HERMES_PROXY_URLS`

## Testando

### 1. Verificar logs de inicialização
```bash
# Docker
docker-compose logs -f | grep -i proxy

# Systemd
journalctl -u hermes-call -f | grep -i proxy

# Deve aparecer:
# proxy pool initialized count=39
```

### 2. Testar requisição LLM
No painel do Hermes Call:
1. Vá em Configurações → IA
2. Selecione uma credencial OpenRouter
3. Teste o modelo
4. Verifique os logs - deve ver rotação de proxies em caso de rate limit

### 3. Monitorar rate limits
```bash
# Ver avisos de rotação
docker-compose logs -f | grep "pool de chaves\|proxy pool"

# Saída esperada em caso de 429:
# proxy pool: tentando próximo proxy status=429 proxy=a3f2c1e8
# pool de chaves: chave recusada, tentando a próxima status=429 chave=7f3a9bc2
```

## Chaves Adicionadas

### OpenRouter
Total: **4 chaves OpenRouter**

1. `-1` (default)
2. `alicina ai`
3. `andre`
4. `emerson paga`

### Groq
Total: **9 chaves Groq**

1. `groq-1`
2. `groq-2`
3. `groq-3`
4. `groq-4` (nova)
5. `groq-5` (nova)
6. `groq-6` (nova)
7. `groq-7` (nova)
8. `groq-8` (nova)
9. `groq-9` (nova)

**Total: 13 chaves LLM** (4 OpenRouter + 9 Groq)

## Proxies Configurados

Total: **39 proxies Webshare** (rotativos)

Distribuídos entre:
- `45.39.15.202:6632` (1 proxy)
- `31.59.20.176:6754` (8 proxies)
- `p.webshare.io:80` (30 proxies)

## Troubleshooting

### Proxies não inicializados
```bash
# Verificar se ProxySettings existe no banco
docker exec -it hermes-call-db psql -U postgres -d wacalls_main -c "SELECT key, value FROM settings WHERE key='proxy';"

# Se não existir, rodar script novamente
python3 deploy/add_openrouter_keys.py --skip-keys
```

### Chaves não rotacionando
```bash
# Verificar credenciais no banco
docker exec -it hermes-call-db psql -U postgres -d wacalls_main -c "SELECT id, name, provider, base_url FROM credentials WHERE provider='openrouter';"

# Adicionar manualmente via API
curl -X POST http://localhost:8080/api/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenRouter - teste",
    "type": "llm",
    "provider": "openrouter",
    "api_key": "<SEGREDO_REMOVIDO>",
    "base_url": "https://openrouter.ai/api"
  }'
```

### Rate limits persistindo
Se mesmo com 4 chaves + 39 proxies ainda bater rate limit:
1. Verifique se os proxies estão realmente rotativos (`-rotate` no username)
2. Aumente o cooldown em `proxy_pool.go` (linha `proxyRestFor`)
3. Adicione mais chaves OpenRouter via painel ou script

## Estrutura do Sistema

```
┌─────────────────┐
│   AIAgent       │
│  (aiagent.go)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  postLLM()      │─────▶│  Key Pool        │
│ (llm_key_pool)  │      │  - 4 chaves OR   │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│ HTTP Client     │─────▶│  Proxy Pool      │
│ (proxy_pool)    │      │  - 39 proxies WS │
└─────────────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐
│  OpenRouter API │
│  (rate limited) │
└─────────────────┘
```

## Próximos Passos

1. ✅ Código implementado
2. ✅ Scripts de deploy criados
3. ⏳ Deploy na VPS 1
4. ⏳ Deploy na VPS 2
5. ⏳ Testar rotação em produção
6. ⏳ Monitorar rate limits por 24h

## Notas de Segurança

- ⚠️ As chaves estão em **texto plano** no banco (tabela `credentials`)
- ⚠️ Os proxies têm credenciais nos URLs (armazenados em `settings.proxy`)
- ✅ As chaves são **mascaradas** antes de ir pro frontend
- ✅ Os logs usam **fingerprints** (8 chars SHA256), nunca a chave/senha completa
