#!/bin/bash
# batch_meek_cat.sh — Gera um capítulo inteiro do The Meek Cat com dual pipeline.
#
# Uso:
#   ./bin/batch_meek_cat.sh <numero_capitulo>
#
# Exemplo:
#   ./bin/batch_meek_cat.sh 3   # Gera capítulo 3: scrape → split → dual pipeline
#
# O dual pipeline gera 4 vídeos:
#   1. Normal
#   2. Normal Censurado
#   3. HyperFrames
#   4. HyperFrames Censurado
#
# Diretório do projeto
set -e
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

if [ -z "$1" ]; then
    echo "Uso: $0 <numero_capitulo>"
    echo "Exemplo: $0 3"
    exit 1
fi

CAP_NUM="$1"
CAP_NUM_PAD="$(printf "%02d" "$CAP_NUM")"
SLUG="the-meek-cat-cap${CAP_NUM_PAD}"
URL="https://tiamanhwa.com/manhwa/the-meek-cat/capitulo-${CAP_NUM}/"
TITULO="The Meek Cat — Capítulo ${CAP_NUM}"
PANELS_DIR="workspace/panels/${SLUG}"

echo "╔════════════════════════════════════════════════════╗"
echo "║  THE MEEK CAT — Capítulo ${CAP_NUM}"
echo "║  URL: ${URL}"
echo "║  Saída: ${PANELS_DIR}"
echo "╚════════════════════════════════════════════════════╝"

# Passo 1: Scrape
echo ""
echo "▶ Passo 1: Scrape — ${URL}"
./venv/bin/python bin/tia-fetcher.py \
    --url "$URL" \
    --slug "$SLUG" \
    --max-panels 50

if [ $? -ne 0 ]; then
    echo "✗ Scrape falhou para capítulo ${CAP_NUM}"
    exit 1
fi
echo "✓ Scrape concluído"

# Passo 2: Split
echo ""
echo "▶ Passo 2: Split — cortando painéis"
./venv/bin/python bin/panel-splitter.py \
    --split \
    --input "workspace/cache/${SLUG}/" \
    --out "$PANELS_DIR" \
    --no-open

if [ $? -ne 0 ]; then
    echo "✗ Split falhou para capítulo ${CAP_NUM}"
    exit 1
fi
echo "✓ Split concluído"

# Passo 3: Dual Pipeline (Normal + HyperFrames + Censurados)
echo ""
echo "▶ Passo 3: Dual Pipeline — gera 4 vídeos"
./venv/bin/python bin/dual-pipeline.py \
    --panels-dir "$PANELS_DIR" \
    --titulo "$TITULO" \
    --max-panels 120

if [ $? -eq 0 ]; then
    echo "✓ Capítulo ${CAP_NUM} — todos os 4 vídeos gerados com sucesso!"
else
    echo "✗ Dual pipeline falhou para capítulo ${CAP_NUM}"
    exit 1
fi

# Listar resultado
echo ""
echo "📁 Vídeos gerados para Capítulo ${CAP_NUM}:"
ls -lh "workspace/videos/" | grep "the-meek-cat-cap${CAP_NUM_PAD}\|meek-cat-cap${CAP_NUM_PAD}" 2>/dev/null || true
