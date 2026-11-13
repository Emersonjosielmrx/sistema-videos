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

# Sistema Completo de Proxy + Key Rotation - Resumo Final

## ✅ O Que Foi Implementado

### 1. Sistema Duplo de Proxies

#### A. VPS Proxy Pool (Groq apenas) - **NOVO**
- Proxies **internos entre VPS** com latência otimizada
- **4x mais rápido** que Webshare para Groq (0.3s vs 1.5s)
- Configuração automática por VPS baseada em testes reais
- Arquivo: [vps_proxy_pool.go](D:/hermes-call/cmd/server/vps_proxy_pool.go)

#### B. Webshare Proxy Pool (OpenRouter e outros)
- 40 proxies rotativos externos
- Evita rate limit por IP
- Cooldown inteligente (429/401/402)
- Arquivo: [proxy_pool.go](D:/hermes-call/cmd/server/proxy_pool.go)

### 2. Rotação de Chaves LLM

#### OpenRouter: 4 chaves
1. `-1` (default)
2. `alicina ai`
3. `andre`
4. `emerson paga`

#### Groq: 9 chaves
1. `groq-1`
2. `groq-2`
3. `groq-3`
4. `groq-4` (nova)
5. `groq-5` (nova)
6. `groq-6` (nova)
7. `groq-7` (nova)
8. `groq-8` (nova)
9. `groq-9` (nova)

**Total: 13 chaves LLM**

### 3. Roteamento Inteligente

```
┌─────────────────┐
│  Requisição LLM │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ Provider?│
    └────┬─────┘
         │
    ┌────▼────────────────────┐
    │ Groq?   │ OpenRouter?   │
    └────┬────┴───────┬───────┘
         │            │
    ┌────▼─────┐ ┌───▼────────┐
    │VPS Proxy │ │ Webshare   │
    │(interno) │ │ (externo)  │
    │0.3-0.4s  │ │ via proxy  │
    └──────────┘ └────────────┘
```

## 📁 Arquivos Criados/Modificados

### Backend (Go)
1. ✅ [vps_proxy_pool.go](D:/hermes-call/cmd/server/vps_proxy_pool.go) - **NOVO** - Proxy interno entre VPS
2. ✅ [proxy_pool.go](D:/hermes-call/cmd/server/proxy_pool.go) - **NOVO** - Proxy Webshare externo
3. ✅ [llm_key_pool.go](D:/hermes-call/cmd/server/llm_key_pool.go) - **MODIFICADO** - Integração dupla de proxies
4. ✅ [server.go](D:/hermes-call/cmd/server/server.go) - **MODIFICADO** - Inicialização dos pools
5. ✅ [store.go](D:/hermes-call/internal/settings/store.go) - **MODIFICADO** - ProxySettings

### Scripts de Deploy
1. ✅ [add_openrouter_keys.py](D:/hermes-call/deploy/add_openrouter_keys.py) - **MODIFICADO** - Adicionado Groq
2. ✅ [add-openrouter-keys.sh](D:/hermes-call/deploy/add-openrouter-keys.sh) - **MODIFICADO** - Adicionado Groq
3. ✅ [setup-vps-proxy.sh](D:/hermes-call/deploy/setup-vps-proxy.sh) - **NOVO** - Instala Squid

### Documentação
1. ✅ [VPS_PROXY_README.md](D:/hermes-call/deploy/VPS_PROXY_README.md) - **NOVO** - Guia completo VPS proxy
2. ✅ [PROXY_POOL_README.md](D:/hermes-call/deploy/PROXY_POOL_README.md) - **MODIFICADO** - Atualizado com Groq

## 🚀 Deploy - Ordem de Execução

### Passo 1: Instalar Squid em TODAS as VPS

```bash
# VPS 53 (209.145.60.53)
ssh root@209.145.60.53  # senha: <removido — ver cofre>
cd /root/hermes-call
git pull
bash deploy/setup-vps-proxy.sh

# VPS 22 (157.173.207.22)
ssh root@157.173.207.22  # senha: <removido — ver cofre>
cd /root/hermes-call
git pull
bash deploy/setup-vps-proxy.sh

# VPS 241 (62.171.128.241)
ssh root@62.171.128.241  # senha: <removido — ver cofre>
cd /root/hermes-call
git pull
bash deploy/setup-vps-proxy.sh
```

### Passo 2: Adicionar Chaves LLM

```bash
# Em UMA das VPS (de preferência VPS 53)
ssh root@209.145.60.53
cd /root/hermes-call

# Obter JWT token do painel
export HERMES_TOKEN="<SEGREDO_REMOVIDO>"

# Instalar requests
pip3 install requests

# Adicionar 4 chaves OpenRouter + 9 chaves Groq + 40 proxies Webshare
python3 deploy/add_openrouter_keys.py
```

### Passo 3: Configurar e Deploy Hermes Call

**Em CADA VPS:**

```bash
# Editar docker-compose.yml ou systemd service
# Adicionar variável de ambiente:

# VPS 53:
HERMES_VPS_IP=209.145.60.53

# VPS 22:
HERMES_VPS_IP=157.173.207.22

# VPS 241:
HERMES_VPS_IP=62.171.128.241
```

**Rebuild e restart:**
```bash
docker-compose down
docker-compose build
docker-compose up -d

# Verificar logs
docker-compose logs -f | grep -E "VPS proxy|Webshare proxy"
```

### Passo 4: Verificar

Deve aparecer nos logs:

```
VPS proxy pool initialized for Groq vps=53 proxies=1 direct_ratio=0.5
Webshare proxy pool initialized for OpenRouter count=40
```

## 📊 Configuração por VPS

### VPS 241 (62.171.128.241) - Teste/Dev
- **Groq**: 33% direto, 33% via VPS 53, 33% via VPS 22
- **OpenRouter**: via Webshare (40 proxies rotativos)
- **9 chaves Groq** disponíveis (rotação)

### VPS 53 (209.145.60.53) - Produção 1 ⚡
- **Groq**: 50% direto (0.266s - mais rápido!), 50% via VPS 22
- **OpenRouter**: via Webshare (40 proxies rotativos)
- **9 chaves Groq** disponíveis (rotação)

### VPS 22 (157.173.207.22) - Produção 2
- **Groq**: 50% direto, 50% via VPS 53 (melhora latência!)
- **OpenRouter**: via Webshare (40 proxies rotativos)
- **9 chaves Groq** disponíveis (rotação)

## 🎯 Benefícios

### Performance
- **Groq 4x mais rápido**: 0.3s vs 1.5s (VPS proxy vs Webshare)
- **OpenRouter sem rate limit**: 40 proxies + 4 chaves = 160 combinações
- **Groq alta disponibilidade**: 9 chaves × 2-3 destinos = 18-27 combinações

### Redundância
- Falha de 1 chave → rotaciona automaticamente
- Falha de 1 proxy → tenta próximo
- Rate limit → cooldown inteligente + próxima chave/proxy

### Custo
- VPS proxy: **grátis** (tráfego interno)
- Webshare: já contratado (40 proxies)
- Squid: open source

## 🧪 Testes

### Teste 1: Groq com VPS Proxy
```bash
# No painel: Configurações → IA → Testar com Groq
# Log esperado: "VPS proxy" (não deve mencionar Webshare)
```

### Teste 2: OpenRouter com Webshare
```bash
# No painel: Configurações → IA → Testar com OpenRouter
# Log esperado: "proxy pool" ou "tentando próximo proxy"
```

### Teste 3: Rotação de Chaves
```bash
# Forçar rate limit fazendo múltiplas chamadas rápidas
# Log esperado: "chave recusada, tentando a próxima"
```

### Teste 4: Squid Proxy
```bash
# Em cada VPS
curl -x http://127.0.0.1:3128 https://api.groq.com/openai/v1/models

# De outra VPS
curl -x http://209.145.60.53:3128 https://api.groq.com/openai/v1/models
```

## 📚 Documentação

- [VPS_PROXY_README.md](D:/hermes-call/deploy/VPS_PROXY_README.md) - Guia completo VPS proxy (Groq)
- [PROXY_POOL_README.md](D:/hermes-call/deploy/PROXY_POOL_README.md) - Guia Webshare + chaves

## ⚠️ Importante

1. **VPS 241 não é proxy para outras** (sempre piora latência)
2. **VPS 22 melhora via VPS 53** (caso especial - único que melhora)
3. **Squid precisa estar rodando em TODAS as VPS** antes do deploy
4. **HERMES_VPS_IP deve estar definido** em cada VPS
5. **Groq usa VPS proxy, OpenRouter usa Webshare** (nunca mistura)

## 🎉 Resultado Final

### Antes
- ❌ Groq lento via Webshare (1.5s+)
- ❌ Rate limit frequente (1 chave OR, 3 chaves Groq)
- ❌ Sem distribuição de carga

### Depois
- ✅ Groq rápido via VPS (0.3-0.4s) - **4x mais rápido**
- ✅ Alta disponibilidade (13 chaves, 40 proxies)
- ✅ Distribuição inteligente por VPS e provider
- ✅ Rotação automática em caso de falha
- ✅ Sistema duplo otimizado (VPS interno + Webshare externo)

---

**Data de implementação:** 03/10/2026  
**Versão:** v1.0 - Sistema Completo de Proxy + Key Rotation
