#!/bin/bash
# add-openrouter-keys.sh — Adiciona chaves OpenRouter e proxies Webshare ao Hermes Call
# Execução: bash add-openrouter-keys.sh

set -e

echo "=========================================="
echo "Adicionando chaves OpenRouter ao Hermes Call"
echo "=========================================="

# Chaves OpenRouter
OPENROUTER_KEYS=(
    "<SEGREDO_REMOVIDO>|-1"
    "<SEGREDO_REMOVIDO>|alicina ai"
    "<SEGREDO_REMOVIDO>|andre"
    "<SEGREDO_REMOVIDO>|emerson paga"
)

# Chaves Groq
GROQ_KEYS=(
    "<SEGREDO_REMOVIDO>|groq-1"
    "<SEGREDO_REMOVIDO>|groq-2"
    "<SEGREDO_REMOVIDO>|groq-3"
    "<SEGREDO_REMOVIDO>|groq-4"
    "<SEGREDO_REMOVIDO>|groq-5"
    "<SEGREDO_REMOVIDO>|groq-6"
    "<SEGREDO_REMOVIDO>|groq-7"
    "<SEGREDO_REMOVIDO>|groq-8"
    "<SEGREDO_REMOVIDO>|groq-9"
)

# Proxies Webshare
PROXY_URLS=(
    # Host: 45.39.15.202:6632
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@45.39.15.202:6632/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"

    # Host: 31.59.20.176:6754
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/"

    # Host: p.webshare.io:80
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/"
)

# URL da API do Hermes Call
API_URL="${HERMES_API_URL:-http://localhost:8080}"
TOKEN="<SEGREDO_REMOVIDO>"

if [ -z "$TOKEN" ]; then
    echo "❌ Erro: HERMES_TOKEN não definido"
    echo "Uso: HERMES_TOKEN=seu-jwt-token bash add-openrouter-keys.sh"
    exit 1
fi

echo ""
echo "🔑 Adicionando ${#OPENROUTER_KEYS[@]} chaves OpenRouter..."
echo ""

for key_data in "${OPENROUTER_KEYS[@]}"; do
    IFS='|' read -r key name <<< "$key_data"

    echo "Adicionando: $name"

    response=$(curl -s -w "\n%{http_code}" -X POST \
        "$API_URL/api/credentials" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{
            \"name\": \"OpenRouter - $name\",
            \"type\": \"llm\",
            \"provider\": \"openrouter\",
            \"api_key\": \"$key\",
            \"base_url\": \"https://openrouter.ai/api\"
        }")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo "  ✅ Adicionada com sucesso"
    else
        echo "  ❌ Erro: HTTP $http_code"
        echo "  Resposta: $body"
    fi

    sleep 0.5
done

echo ""
echo "🚀 Adicionando ${#GROQ_KEYS[@]} chaves Groq..."
echo ""

for key_data in "${GROQ_KEYS[@]}"; do
    IFS='|' read -r key name <<< "$key_data"

    echo "Adicionando: $name"

    response=$(curl -s -w "\n%{http_code}" -X POST \
        "$API_URL/api/credentials" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{
            \"name\": \"Groq - $name\",
            \"type\": \"llm\",
            \"provider\": \"groq\",
            \"api_key\": \"$key\",
            \"base_url\": \"https://api.groq.com/openai\"
        }")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo "  ✅ Adicionada com sucesso"
    else
        echo "  ❌ Erro: HTTP $http_code"
        echo "  Resposta: $body"
    fi

    sleep 0.5
done

echo ""
echo "🌐 Configurando ${#PROXY_URLS[@]} proxies Webshare..."
echo ""

# Junta todos os proxies em uma string separada por vírgulas
PROXY_LIST=$(IFS=,; echo "${PROXY_URLS[*]}")

# Atualiza as configurações de proxy
response=$(curl -s -w "\n%{http_code}" -X POST \
    "$API_URL/api/settings" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{
        \"proxy\": {
            \"enabled\": true,
            \"proxy_urls\": $(printf '%s\n' "${PROXY_URLS[@]}" | jq -R . | jq -s .)
        }
    }")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
    echo "✅ Proxies configurados com sucesso"
else
    echo "❌ Erro ao configurar proxies: HTTP $http_code"
    echo "Resposta: $body"
fi

echo ""
echo "=========================================="
echo "✅ Concluído!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "1. Reinicie o serviço Hermes Call para ativar o proxy pool"
echo "2. Verifique os logs: journalctl -u hermes-call -f"
echo "3. Confirme que vê: 'proxy pool initialized'"
echo ""
