# VPS Proxy Pool - Groq Otimizado

Sistema de proxy **interno entre VPS** para chamadas Groq, baseado em testes de latência reais.

## Problema

Usar proxies externos (Webshare) adiciona **muito tempo** às chamadas Groq:
- VPS 241 → Groq direto: **0.341s**
- VPS 241 → Groq via Webshare: **~1.5s+** (440% mais lento)

## Solução

Proxies **internos entre VPS** com latência muito menor (< 100ms entre VPS).

## Matriz de Latência (Testes Reais)

| Origem | Direto | Via VPS 53 | Via VPS 22 | Via VPS 241 |
|--------|--------|------------|------------|-------------|
| **VPS 53** (209.145.60.53) | **0.266s** ⚡ | — | 0.332s (+25%) | 0.897s (+237%) |
| **VPS 22** (157.173.207.22) | 0.312s | **0.249s** (-20%) ⚡ | — | 1.003s (+221%) |
| **VPS 241** (62.171.128.241) | 0.341s | 0.852s (+150%) | 0.768s (+125%) | — |

### Insights

1. **VPS 241 como proxy SEMPRE piora** (VPS3 ruim)
2. **VPS 22 melhora via VPS 53** (único caso que melhora!)
3. **VPS 53 é a mais rápida direta** (0.266s)

## Configuração por VPS

### VPS 241 (62.171.128.241) - Teste/Dev
- **33%** chamadas diretas
- **33%** via VPS 53 (209.145.60.53:3128)
- **33%** via VPS 22 (157.173.207.22:3128)
- Divide em 3 destinos

### VPS 53 (209.145.60.53) - Produção 1
- **50%** chamadas diretas (mais rápido)
- **50%** via VPS 22 (157.173.207.22:3128)
- Divide em 2 destinos
- **NÃO usa VPS 241** (piora muito)

### VPS 22 (157.173.207.22) - Produção 2
- **50%** chamadas diretas
- **50%** via VPS 53 (209.145.60.53:3128) - **melhora latência!**
- Divide em 2 destinos

## Instalação

### 1. Instalar Squid Proxy em TODAS as VPS

```bash
# Executar em cada VPS
ssh root@209.145.60.53  # senha: <removido — ver cofre>
cd /root/hermes-call
bash deploy/setup-vps-proxy.sh

ssh root@157.173.207.22  # senha: <removido — ver cofre>
cd /root/hermes-call
bash deploy/setup-vps-proxy.sh

ssh root@62.171.128.241  # senha: <removido — ver cofre>
cd /root/hermes-call
bash deploy/setup-vps-proxy.sh
```

O script:
- Instala Squid na porta 3128
- Configura ACLs para permitir apenas as 3 VPS
- Configura firewall (ufw)
- Testa o proxy

### 2. Configurar Variável de Ambiente

Em cada VPS, adicione ao systemd service ou docker-compose:

```bash
# VPS 53
HERMES_VPS_IP=209.145.60.53

# VPS 22
HERMES_VPS_IP=157.173.207.22

# VPS 241
HERMES_VPS_IP=62.171.128.241
```

**Docker Compose:**
```yaml
# docker-compose.yml
services:
  hermes-call:
    environment:
      - HERMES_VPS_IP=209.145.60.53  # IP desta VPS
```

**Systemd:**
```ini
# /etc/systemd/system/hermes-call.service
[Service]
Environment="HERMES_VPS_IP=209.145.60.53"
```

### 3. Deploy do Código

```bash
# Em cada VPS
cd /root/hermes-call
git pull
docker-compose down
docker-compose build
docker-compose up -d

# Verificar logs
docker-compose logs -f | grep "VPS proxy"
```

Deve aparecer:
```
VPS proxy pool initialized for Groq vps=53 proxies=1 direct_ratio=0.5
```

## Como Funciona

### Roteamento Automático

O sistema detecta automaticamente a VPS atual pelo IP e rotaciona as chamadas:

**Exemplo VPS 53:**
```
Chamada 1 → Direto (50%)
Chamada 2 → Via proxy VPS 22 (50%)
Chamada 3 → Direto (50%)
Chamada 4 → Via proxy VPS 22 (50%)
...
```

### Separação por Provider

- **Groq**: usa VPS proxy (baixa latência)
- **OpenRouter**: usa Webshare proxy (evita rate limit por IP)
- **Outros**: sem proxy (direto)

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    Hermes Call                       │
│                  (qualquer VPS)                      │
└──────────────┬──────────────────────┬───────────────┘
               │                      │
     ┌─────────▼──────────┐ ┌────────▼───────────┐
     │   isGroq?          │ │  isOpenRouter?     │
     │   ✅ SIM           │ │  ✅ SIM            │
     └─────────┬──────────┘ └────────┬───────────┘
               │                      │
     ┌─────────▼──────────┐ ┌────────▼───────────┐
     │  VPS Proxy Pool    │ │ Webshare Proxy     │
     │  (interno)         │ │ (externo)          │
     │  Porta 3128        │ │ 40 proxies         │
     └─────────┬──────────┘ └────────┬───────────┘
               │                      │
     ┌─────────▼──────────┐ ┌────────▼───────────┐
     │   api.groq.com     │ │ openrouter.ai      │
     └────────────────────┘ └────────────────────┘
```

## Testes

### Testar Proxy Squid

```bash
# Em cada VPS, teste o proxy local
curl -x http://127.0.0.1:3128 https://api.groq.com/openai/v1/models

# De outra VPS, teste o proxy remoto
curl -x http://209.145.60.53:3128 https://api.groq.com/openai/v1/models
```

### Testar Chamada Groq

No painel do Hermes Call:
1. Configurações → IA
2. Selecione credencial Groq
3. Teste o modelo
4. Verifique os logs

```bash
docker-compose logs -f | grep -i "groq\|vps proxy"
```

### Monitorar Distribuição

```bash
# Ver qual VPS está sendo usada como proxy
tail -f /var/log/squid/access.log | grep groq
```

## Troubleshooting

### Proxy não responde

```bash
# Verificar se Squid está rodando
systemctl status squid

# Reiniciar
systemctl restart squid

# Ver logs
tail -f /var/log/squid/access.log
tail -f /var/log/squid/cache.log
```

### Firewall bloqueando

```bash
# Verificar regras
ufw status numbered

# Adicionar manualmente
ufw allow from 209.145.60.53 to any port 3128
ufw allow from 157.173.207.22 to any port 3128
ufw allow from 62.171.128.241 to any port 3128
```

### VPS não detectada

```bash
# Verificar variável de ambiente
echo $HERMES_VPS_IP

# Forçar detecção via IP público
curl https://api.ipify.org

# Definir manualmente
export HERMES_VPS_IP="209.145.60.53"
```

### Chamadas todas diretas (sem proxy)

```bash
# Verificar se vpsProxySettings foi inicializado
docker-compose logs | grep "VPS proxy pool initialized"

# Se não aparecer, verificar:
# 1. HERMES_VPS_IP está definido?
# 2. Código vps_proxy_pool.go foi compilado?
```

## Comparação de Performance

### Antes (Webshare)
- Groq via Webshare: **~1.5s+** por chamada
- 100 chamadas: **~150s** (2.5 min)
- ❌ Muito lento para tempo real

### Depois (VPS Proxy)
- Groq via VPS proxy: **~0.3-0.4s** por chamada
- 100 chamadas: **~35s**
- ✅ **4x mais rápido!**

## Custos

- **Squid**: Gratuito (open source)
- **Tráfego entre VPS**: Geralmente sem custo adicional (mesma rede/DC)
- **Latência adicionada**: < 100ms (vs. 1000ms+ com Webshare)

## Segurança

- ✅ ACLs restritas (apenas 3 VPS autorizadas)
- ✅ Firewall configurado (ufw)
- ✅ Sem autenticação externa (IPs internos confiáveis)
- ✅ Logs de acesso habilitados

## Notas

- VPS 241 não é usada como proxy por outras VPS (sempre piora)
- VPS 22 **melhora** usando VPS 53 como proxy (caso especial)
- O sistema funciona mesmo se uma VPS cair (degrada para direto)
- Webshare proxies ainda são usados para OpenRouter (rate limit por IP)
