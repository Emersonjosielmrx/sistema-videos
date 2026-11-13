> ## ⛔ NÃO SEGUIR ESTE ROTEIRO (revisado em 03/10/2026)
>
> Revisão feita a pedido da dona. O código foi refeito (`cmd/server/proxy_pool.go`) e este roteiro
> ficou **obsoleto e perigoso**:
> - manda instalar Squid e abrir a porta 3128 na **produção** (VPS compartilhada com Atlas/Lucrativa)
>   e usar a **VPS 209, que foi invadida**, como saída da IA;
> - põe proxy na **IA da ligação** (soma 0,1–0,5 s em toda fala) — a dona quer medir antes;
> - publica com `docker-compose`/`git pull` e SSH por **senha** (a produção roda via systemd e só se
>   publica com `bash ops/publicar.sh`; SSH só por chave — ver `CLAUDE.md`).
>
> Como ficou: proxies Webshare cadastrados no **cofre do painel** (provedor "Proxy Webshare"), usados só
> nos pedidos de IA sem pressa; ligação direta; Gemini de fora. Senhas removidas deste arquivo.

# 📋 CHECKLIST DE DEPLOY - Sistema de Proxy + Key Rotation

**Data de Implementação:** 03/10/2026  
**Desenvolvedor:** Claude (Kiro)  
**Revisor:** [A PREENCHER]  
**Status:** ⏳ Aguardando Revisão e Deploy

---

## 📦 O QUE FOI IMPLEMENTADO

### Resumo Executivo
Sistema **duplo de proxies** para otimizar chamadas LLM:
1. **VPS Proxy** (interno, Groq) - 4x mais rápido que Webshare
2. **Webshare Proxy** (externo, OpenRouter) - evita rate limit por IP
3. **Rotação de 13 chaves** (4 OpenRouter + 9 Groq)

### Problema Resolvido
- ❌ Groq via Webshare: ~1.5s+ (muito lento)
- ❌ Rate limits frequentes (poucas chaves)
- ✅ Groq via VPS: ~0.3-0.4s (4x mais rápido)
- ✅ 13 chaves + 40 proxies (alta disponibilidade)

---

## 📁 ARQUIVOS MODIFICADOS/CRIADOS

### Backend Go (D:\hermes-call\cmd\server\)

#### 1. ✅ vps_proxy_pool.go [NOVO]
**Localização:** `D:\hermes-call\cmd\server\vps_proxy_pool.go`

**O que faz:**
- Detecta VPS atual por IP
- Configura proxies internos baseado em matriz de latência
- VPS 53: usa VPS 22 como proxy (50/50)
- VPS 22: usa VPS 53 como proxy (50/50) - melhora latência!
- VPS 241: usa VPS 53 e VPS 22 (33/33/33)

**Funções principais:**
- `initVPSProxyPool()` - Inicializa pool baseado no IP da VPS
- `detectCurrentVPSIP()` - Detecta IP via HERMES_VPS_IP ou ipify.org
- `getVPSProxyHTTPClient()` - Retorna client com proxy apropriado
- `isGroqProvider()` - Detecta se é requisição Groq

**Variáveis de ambiente necessárias:**
```bash
HERMES_VPS_IP=209.145.60.53  # IP da VPS atual
```

---

#### 2. ✅ proxy_pool.go [NOVO]
**Localização:** `D:\hermes-call\cmd\server\proxy_pool.go`

**O que faz:**
- Gerencia 40 proxies Webshare rotativos
- Cooldown inteligente (429: 2min, 402: 10min, 401/403: 30min)
- Round-robin entre proxies

**Funções principais:**
- `initGlobalProxyPool()` - Inicializa com lista de proxies
- `pick()` - Seleciona próximo proxy não descansando
- `rest()` - Coloca proxy em cooldown
- `newHTTPClientWithProxy()` - Cria HTTP client com proxy

**Proxies configurados:** 40 URLs Webshare

---

#### 3. ✅ llm_key_pool.go [MODIFICADO]
**Localização:** `D:\hermes-call\cmd\server\llm_key_pool.go`

**Mudanças:**
- Função `postLLM()` modificada (linhas 188-267)
- Detecta provider (Groq vs OpenRouter)
- Groq → usa VPS proxy
- OpenRouter → usa Webshare proxy
- Outros → sem proxy

**Lógica de roteamento:**
```go
isGroq := isGroqProvider(a.provider, a.apiBaseURL)

if isGroq {
    client = getVPSProxyHTTPClient(timeout, true)  // VPS interno
} else if globalProxyPool != nil {
    client = newHTTPClientWithProxy(proxy.URL, timeout)  // Webshare
}
```

---

#### 4. ✅ server.go [MODIFICADO]
**Localização:** `D:\hermes-call\cmd\server\server.go`

**Mudanças:**
- Import adicionado: `"strings"` (linha 7)
- Inicialização VPS proxy (linhas ~495-520)
- Inicialização Webshare proxy

**Código adicionado:**
```go
// VPS proxy pool (Groq)
initVPSProxyPool()
if vpsProxySettings != nil {
    log.Info("VPS proxy pool initialized for Groq", ...)
}

// Webshare proxy pool (OpenRouter/outros)
if us := settings.LoadUserSettings(...); us.Proxy.Enabled {
    initGlobalProxyPool(us.Proxy.ProxyURLs)
    log.Info("Webshare proxy pool initialized for OpenRouter", ...)
}
```

---

### Settings (D:\hermes-call\internal\settings\)

#### 5. ✅ store.go [MODIFICADO]
**Localização:** `D:\hermes-call\internal\settings\store.go`

**Mudanças:**
- Struct `ProxySettings` adicionado (linhas ~280-285)
- Campo `Proxy ProxySettings` em `UserSettings` (linha ~305)
- `ss.loadUserKey(ctx, userID, "proxy", &us.Proxy)` (linha ~502)

**Estrutura:**
```go
type ProxySettings struct {
    Enabled   bool     `json:"enabled"`
    ProxyURLs []string `json:"proxy_urls"`
}
```

---

### Scripts de Deploy (D:\hermes-call\deploy\)

#### 6. ✅ setup-vps-proxy.sh [NOVO]
**Localização:** `D:\hermes-call\deploy\setup-vps-proxy.sh`

**O que faz:**
- Instala Squid proxy (porta 3128)
- Configura ACLs (permite apenas 3 VPS)
- Configura firewall (ufw)
- Testa o proxy

**Como executar:**
```bash
bash deploy/setup-vps-proxy.sh
```

**Deve ser executado em TODAS as 3 VPS.**

---

#### 7. ✅ add_openrouter_keys.py [MODIFICADO]
**Localização:** `D:\hermes-call\deploy\add_openrouter_keys.py`

**Mudanças:**
- Array `GROQ_KEYS` adicionado (9 chaves)
- Função `add_groq_keys()` adicionada
- Array `PROXY_URLS` atualizado (40 proxies)
- Flag `--skip-groq` adicionada

**Como executar:**
```bash
export HERMES_TOKEN="<SEGREDO_REMOVIDO>"
python3 deploy/add_openrouter_keys.py
```

**Adiciona:**
- 4 chaves OpenRouter
- 9 chaves Groq
- 40 proxies Webshare

---

#### 8. ✅ add-openrouter-keys.sh [MODIFICADO]
**Localização:** `D:\hermes-call\deploy\add-openrouter-keys.sh`

**Mudanças:**
- Array `GROQ_KEYS` adicionado
- Loop para processar Groq keys
- Array `PROXY_URLS` atualizado (40 proxies)

**Alternativa em Bash ao script Python.**

---

### Documentação (D:\hermes-call\deploy\)

#### 9. ✅ VPS_PROXY_README.md [NOVO]
Guia completo do sistema VPS proxy (Groq)

#### 10. ✅ PROXY_POOL_README.md [MODIFICADO]
Guia do sistema Webshare + chaves (atualizado com Groq)

#### 11. ✅ IMPLEMENTACAO_COMPLETA.md [NOVO]
Resumo executivo de tudo que foi feito

---

## 🔍 PONTOS CRÍTICOS PARA REVISAR

### ⚠️ 1. Compilação Go
**Verificar:**
- [ ] `vps_proxy_pool.go` compila sem erros
- [ ] `proxy_pool.go` compila sem erros
- [ ] Imports estão corretos em `server.go`
- [ ] Funções exportadas estão acessíveis

**Como testar:**
```bash
cd D:\hermes-call
go build ./cmd/server
```

---

### ⚠️ 2. Variável de Ambiente HERMES_VPS_IP
**Verificar:**
- [ ] Está definida em cada VPS
- [ ] Valor correto (IP público da VPS)
- [ ] Definida no lugar certo (docker-compose.yml ou systemd)

**Valores esperados:**
```
VPS 53:  HERMES_VPS_IP=209.145.60.53
VPS 22:  HERMES_VPS_IP=157.173.207.22
VPS 241: HERMES_VPS_IP=62.171.128.241
```

---

### ⚠️ 3. Squid Instalado em TODAS as VPS
**Verificar antes do deploy Hermes:**
- [ ] VPS 53: Squid rodando na porta 3128
- [ ] VPS 22: Squid rodando na porta 3128
- [ ] VPS 241: Squid rodando na porta 3128

**Como verificar:**
```bash
# Em cada VPS
systemctl status squid
curl -x http://127.0.0.1:3128 https://api.groq.com/openai/v1/models
```

---

### ⚠️ 4. Firewall
**Verificar:**
- [ ] Porta 3128 aberta entre VPS
- [ ] ACLs do Squid permitem as 3 VPS

**Como verificar:**
```bash
# De VPS 53 para VPS 22
curl -x http://157.173.207.22:3128 https://api.groq.com/openai/v1/models

# De VPS 22 para VPS 53
curl -x http://209.145.60.53:3128 https://api.groq.com/openai/v1/models
```

---

### ⚠️ 5. Chaves e Proxies no Banco
**Verificar após add_openrouter_keys.py:**
- [ ] 4 chaves OpenRouter no banco
- [ ] 9 chaves Groq no banco
- [ ] 40 proxies Webshare no settings

**Como verificar:**
```bash
# Conectar no banco
docker exec -it hermes-call-db psql -U postgres -d wacalls_main

# Ver credenciais
SELECT name, provider FROM credentials ORDER BY created_at DESC LIMIT 15;

# Ver proxies
SELECT value->'proxy'->'proxy_urls' FROM settings WHERE key='proxy';
```

---

## 📝 CHECKLIST DE DEPLOY

### Fase 1: Preparação das VPS

#### VPS 53 (209.145.60.53)
```bash
ssh root@209.145.60.53  # senha: <removido — ver cofre>

# 1. Atualizar código
cd /root/hermes-call
git pull origin main  # ou branch apropriado

# 2. Instalar Squid
bash deploy/setup-vps-proxy.sh

# 3. Verificar Squid
systemctl status squid
curl -x http://127.0.0.1:3128 https://api.groq.com/openai/v1/models

# 4. Verificar conectividade com outras VPS
curl -x http://157.173.207.22:3128 https://api.groq.com/openai/v1/models
curl -x http://62.171.128.241:3128 https://api.groq.com/openai/v1/models
```

**Checklist:**
- [ ] Git pull executado
- [ ] Squid instalado e rodando
- [ ] Teste local funcionando
- [ ] Conectividade com VPS 22 OK
- [ ] Conectividade com VPS 241 OK

---

#### VPS 22 (157.173.207.22)
```bash
ssh root@157.173.207.22  # senha: <removido — ver cofre>

# 1. Atualizar código
cd /root/hermes-call
git pull origin main

# 2. Instalar Squid
bash deploy/setup-vps-proxy.sh

# 3. Verificar Squid
systemctl status squid
curl -x http://127.0.0.1:3128 https://api.groq.com/openai/v1/models

# 4. Verificar conectividade com outras VPS
curl -x http://209.145.60.53:3128 https://api.groq.com/openai/v1/models
curl -x http://62.171.128.241:3128 https://api.groq.com/openai/v1/models
```

**Checklist:**
- [ ] Git pull executado
- [ ] Squid instalado e rodando
- [ ] Teste local funcionando
- [ ] Conectividade com VPS 53 OK
- [ ] Conectividade com VPS 241 OK

---

#### VPS 241 (62.171.128.241)
```bash
ssh root@62.171.128.241  # senha: <removido — ver cofre>

# 1. Atualizar código
cd /root/hermes-call
git pull origin main

# 2. Instalar Squid
bash deploy/setup-vps-proxy.sh

# 3. Verificar Squid
systemctl status squid
curl -x http://127.0.0.1:3128 https://api.groq.com/openai/v1/models

# 4. Verificar conectividade com outras VPS
curl -x http://209.145.60.53:3128 https://api.groq.com/openai/v1/models
curl -x http://157.173.207.22:3128 https://api.groq.com/openai/v1/models
```

**Checklist:**
- [ ] Git pull executado
- [ ] Squid instalado e rodando
- [ ] Teste local funcionando
- [ ] Conectividade com VPS 53 OK
- [ ] Conectividade com VPS 22 OK

---

### Fase 2: Adicionar Chaves e Proxies

**Executar em UMA VPS apenas (recomendado: VPS 53)**

```bash
ssh root@209.145.60.53
cd /root/hermes-call

# 1. Instalar dependências Python
pip3 install requests

# 2. Obter JWT token
# Acessar painel → DevTools → localStorage.getItem('token')
# OU: Fazer login via API e capturar token

# 3. Adicionar chaves
export HERMES_TOKEN="<SEGREDO_REMOVIDO>"
python3 deploy/add_openrouter_keys.py

# Deve mostrar:
# ✅ 4 chaves OpenRouter adicionadas
# ✅ 9 chaves Groq adicionadas
# ✅ 40 proxies configurados
```

**Checklist:**
- [ ] Script executado sem erros
- [ ] 4 chaves OpenRouter adicionadas
- [ ] 9 chaves Groq adicionadas
- [ ] 40 proxies Webshare configurados

---

### Fase 3: Configurar Variável de Ambiente

**Em CADA VPS:**

#### Docker Compose (se usar)
```yaml
# docker-compose.yml
services:
  hermes-call:
    environment:
      - HERMES_VPS_IP=209.145.60.53  # Mudar por VPS
```

#### Systemd (se usar)
```ini
# /etc/systemd/system/hermes-call.service
[Service]
Environment="HERMES_VPS_IP=209.145.60.53"  # Mudar por VPS
```

**Checklist:**
- [ ] VPS 53: HERMES_VPS_IP=209.145.60.53
- [ ] VPS 22: HERMES_VPS_IP=157.173.207.22
- [ ] VPS 241: HERMES_VPS_IP=62.171.128.241

---

### Fase 4: Deploy Hermes Call

**Em CADA VPS, na ordem:**

#### 1. VPS 241 (teste primeiro)
```bash
ssh root@62.171.128.241
cd /root/hermes-call

# Build
docker-compose down
docker-compose build

# Start
docker-compose up -d

# Verificar logs
docker-compose logs -f | grep -E "VPS proxy|Webshare proxy|error"
```

**Logs esperados:**
```
VPS proxy pool initialized for Groq vps=241 proxies=2 direct_ratio=0.33
Webshare proxy pool initialized for OpenRouter count=40
```

**Checklist VPS 241:**
- [ ] Build sem erros
- [ ] Serviço subiu
- [ ] Log "VPS proxy pool initialized" apareceu
- [ ] Log "Webshare proxy pool initialized" apareceu
- [ ] Nenhum erro crítico

---

#### 2. VPS 53 (produção)
```bash
ssh root@209.145.60.53
cd /root/hermes-call

docker-compose down
docker-compose build
docker-compose up -d
docker-compose logs -f | grep -E "VPS proxy|Webshare proxy|error"
```

**Logs esperados:**
```
VPS proxy pool initialized for Groq vps=53 proxies=1 direct_ratio=0.5
Webshare proxy pool initialized for OpenRouter count=40
```

**Checklist VPS 53:**
- [ ] Build sem erros
- [ ] Serviço subiu
- [ ] Log VPS proxy correto (vps=53, proxies=1)
- [ ] Nenhum erro crítico

---

#### 3. VPS 22 (produção)
```bash
ssh root@157.173.207.22
cd /root/hermes-call

docker-compose down
docker-compose build
docker-compose up -d
docker-compose logs -f | grep -E "VPS proxy|Webshare proxy|error"
```

**Logs esperados:**
```
VPS proxy pool initialized for Groq vps=22 proxies=1 direct_ratio=0.5
Webshare proxy pool initialized for OpenRouter count=40
```

**Checklist VPS 22:**
- [ ] Build sem erros
- [ ] Serviço subiu
- [ ] Log VPS proxy correto (vps=22, proxies=1)
- [ ] Nenhum erro crítico

---

### Fase 5: Testes Funcionais

#### Teste 1: Groq com VPS Proxy
```
1. Acessar painel Hermes Call
2. Configurações → IA
3. Selecionar credencial Groq
4. Testar modelo
5. Verificar logs
```

**Log esperado:**
```
# NÃO deve aparecer "Webshare" para Groq
# Latência esperada: 0.3-0.5s
```

**Checklist:**
- [ ] Teste Groq funcionou
- [ ] Latência < 0.5s
- [ ] Sem menção a Webshare nos logs

---

#### Teste 2: OpenRouter com Webshare
```
1. Painel → Configurações → IA
2. Selecionar credencial OpenRouter
3. Testar modelo
4. Verificar logs
```

**Log esperado:**
```
# DEVE aparecer "proxy pool" ou fingerprint de proxy
```

**Checklist:**
- [ ] Teste OpenRouter funcionou
- [ ] Logs mencionam proxy pool
- [ ] Sem erros de conexão

---

#### Teste 3: Rotação de Chaves
```
1. Fazer múltiplas chamadas rápidas (forçar rate limit)
2. Verificar logs
```

**Log esperado:**
```
pool de chaves: chave recusada, tentando a próxima status=429 chave=<fingerprint>
```

**Checklist:**
- [ ] Sistema rotaciona automaticamente
- [ ] Nenhuma chamada falha por falta de chave
- [ ] Cooldown funcionando

---

#### Teste 4: Monitorar Squid
```bash
# Em cada VPS
tail -f /var/log/squid/access.log | grep groq
```

**O que observar:**
- [ ] Requisições Groq aparecem nos logs
- [ ] IPs das outras VPS aparecem como origem
- [ ] Sem erros 403/500

---

### Fase 6: Monitoramento (primeiras 24h)

#### Métricas a observar:
```bash
# Logs Hermes
docker-compose logs -f | grep -E "groq|openrouter|proxy|chave recusada"

# Logs Squid
tail -f /var/log/squid/access.log

# Performance
# Comparar latência antes/depois
```

**Checklist 24h:**
- [ ] Sem erros críticos
- [ ] Latência Groq estável (< 0.5s)
- [ ] Rotação de chaves funcionando
- [ ] Squid estável em todas VPS

---

## 🚨 ROLLBACK (se necessário)

### Se algo der errado:

```bash
# Em cada VPS
cd /root/hermes-call
git log  # ver commit anterior
git checkout <commit-anterior>
docker-compose down
docker-compose build
docker-compose up -d
```

**OU remover apenas variável:**
```bash
# Remover HERMES_VPS_IP do docker-compose.yml
# Sistema vai funcionar sem VPS proxy (usa Webshare para tudo)
docker-compose restart
```

---

## 📊 MATRIZ DE DECISÃO

| Situação | Ação |
|----------|------|
| Build falha | Verificar erros Go, revisar imports |
| Squid não sobe | Verificar porta 3128 livre, logs Squid |
| VPS não detectada | Definir HERMES_VPS_IP manualmente |
| Groq lento | Verificar se está usando VPS proxy (logs) |
| Rate limit contínuo | Verificar se chaves foram adicionadas |
| Proxy timeout | Testar conectividade entre VPS (curl) |

---

## 📞 CONTATOS E REFERÊNCIAS

### Documentação
- [VPS_PROXY_README.md](D:/hermes-call/deploy/VPS_PROXY_README.md)
- [PROXY_POOL_README.md](D:/hermes-call/deploy/PROXY_POOL_README.md)
- [IMPLEMENTACAO_COMPLETA.md](D:/hermes-call/deploy/IMPLEMENTACAO_COMPLETA.md)

### VPS
- VPS 53: 209.145.60.53 (root / <removido>)
- VPS 22: 157.173.207.22 (root / <removido>)
- VPS 241: 62.171.128.241 (root / <removido>)

### Arquivos Críticos
- `cmd/server/vps_proxy_pool.go` - Proxy VPS
- `cmd/server/proxy_pool.go` - Proxy Webshare
- `cmd/server/llm_key_pool.go` - Integração
- `cmd/server/server.go` - Inicialização

---

## ✅ ASSINATURA DE REVISÃO

**Revisor:** ___________________________  
**Data:** ___/___/______  
**Status:** [ ] Aprovado [ ] Aprovado com ressalvas [ ] Rejeitado

**Comentários:**
```
[Espaço para comentários do revisor]
```

---

**IMPORTANTE:** Este documento deve ser seguido na ordem apresentada. Não pule etapas.
