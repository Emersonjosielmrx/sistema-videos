# GUIA DE OPERAÇÃO — Hipercool Videos Pipeline

> Como baixar capítulos do tiamanhwa.com, cortar em painéis e gerar vídeos.
> Inclui TODOS os ajustes e parâmetros que funcionaram.

---

## 1. BAIXAR CAPÍTULO (tia-fetcher.py)

### Comando básico:
```bash
cd ~/Downloads/apps/hipercool\ videos
source venv/bin/activate

# Baixar capítulo específico
python bin/tia-fetcher.py \
    --url https://tiamanhwa.com/manhwa/the-meek-cat/capitulo-2/ \
    --slug the-meek-cat-cap02
```

### Parâmetros importantes:
- `--url`: URL do capítulo (sempre terminar com `/`)
- `--slug`: nome da pasta (ex: `the-meek-cat-cap02`)
- `--max-panels 50`: limite de strips (default 50, aumentar se capítulo for longo)

### O que ele faz:
1. Baixa o HTML do capítulo
2. Extrai os links das strips (imagens) do reader Madara
3. Baixa cada strip como `.webp` + converte pra `.jpg`
4. Salva em: `workspace/cache/<slug>/`
5. Gera `_meta.json` no mesmo diretório

### Problemas comuns:
- **Age gate (conteúdo adulto):** O cookie `wpmanga-adult=1` já está no código
- **Strips faltando:** Aumentar `--max-panels` se o capítulo for maior que 50 strips
- **Conexão caindo:** Tenta novamente com backoff exponencial (já implementado)

---

## 2. CORTAR EM PAINÉIS (panel-splitter.py)

### PASSO 1 — TESTAR ANTES (sempre!):
```bash
# Preview com parâmetros padrão
python bin/panel-splitter.py \
    --test \
    --input workspace/cache/the-meek-cat-cap02/

# Se o manhwa tiver fundo PRETO entre painéis (modo ESCURO):
python bin/panel-splitter.py \
    --test \
    --input workspace/cache/the-meek-cat-cap02/ \
    --dark-mode

# Ajustar sensibilidade (se estiver cortando demais/pouco):
python bin/panel-splitter.py \
    --test \
    --input workspace/cache/the-meek-cat-cap02/ \
    --thresh 240 --min-h 400 --max-h 2400 --gap-min 30
```

### PASSO 2 — AJUSTAR PARÂMETROS (se o teste não ficar bom):

Os parâmetros que mais importam:

| Parâmetro | Padrão | O que faz | Quando ajustar |
|---|---|---|---|
| `--thresh` | 230 | Sensibilidade (menor = mais cortes) | Se tá cortando pouco ou demais |
| `--min-h` | 300 | Altura mínima de um painel (px) | Painéis muito pequenos sendo ignorados |
| `--max-h` | 2500 | Altura máxima de um painel (px) | Painéis enormes não sendo cortados |
| `--gap-min` | 25 | Largura mínima do espaço entre painéis | Manhwas com gaps pequenos |
| `--dark-mode` | — | Usa fundo PRETO em vez de BRANCO | Manhwas com fundo escuro entre painéis |

### PASSO 3 — PRODUÇÃO (depois do teste aprovado):
```bash
python bin/panel-splitter.py \
    --split \
    --input workspace/cache/the-meek-cat-cap02/ \
    --out workspace/panels/the-meek-cat-cap02/ \
    --thresh 230 --min-h 300 --max-h 2500 --gap-min 25
```

### O que o splitter faz por dentro:
1. Abre cada strip vertical
2. Varre a imagem horizontalmente detectando linhas de separação (espaços BRANCOS ou PRETOS)
3. Quando encontra um gap ≥ `--gap-min` pixels, considera uma quebra de painel
4. Corta cada painel e salva como `panel_000.jpg`, `panel_001.jpg`, etc.
5. Descarta painéis com altura < `--min-h` (provavelmente são linhas decorativas)
6. Remove bordas pretas/brancas de cada painel

### Saída esperada:
```
workspace/panels/the-meek-cat-cap02/
├── panel_000.jpg   (primeiro painel)
├── panel_001.jpg   (segundo painel)
├── panel_002.jpg
├── panel_003.jpg
├── panel_004.jpg
├── panel_005.jpg
...
└── panel_106.jpg   (último — ~107 painéis por capítulo)
```

---

## 3. PIPELINE COMPLETA (uma etapa só)

### Se quiser fazer tudo de uma vez (scrape → split → pipeline):
```bash
# Com o batch script:
bash bin/batch_meek_cat.sh 3
bash bin/batch_meek_cat.sh 4
# ... etc

# Ou com o queue-runner (fila serial, recomendado):
python bin/queue-runner.py --caps 3-9 --dual
```

### O queue-runner faz, em ordem, pra cada capítulo:
1. **Scrape** (tia-fetcher) — só se não tiver cache
2. **Split** (panel-splitter) — só se não tiver painéis cortados
3. **Pipeline** (dual-pipeline) — gera os 4 vídeos

---

## 4. VALIDAÇÃO RÁPIDA

### Verificar se o download funcionou:
```bash
ls workspace/cache/the-meek-cat-cap03/ | head -10
ls workspace/cache/the-meek-cat-cap03/*.jpg | wc -l   # quantas strips
```

### Verificar se o split funcionou:
```bash
ls workspace/panels/the-meek-cat-cap03/ | head -10
ls workspace/panels/the-meek-cat-cap03/*.jpg | wc -l   # quantos painéis
```

### Verificar tamanhos (se tem arquivo de 0 bytes, deletar):
```bash
find workspace/ -name "*.jpg" -size 0 -delete
```

---

## 5. PROBLEMAS COMUNS E SOLUÇÕES

### "No such file or directory: workspace/cache/slug/"
- O cache_dir é criado automático, mas se a URL estiver errada, nada é baixado
- Verificar URL: `curl -sI "$URL" | head -5`

### Strips faltando (ex: baixou 15 de 20)
- Aumentar `--max-panels` (o regex pode ter perdido algumas)
- Tentar de novo: o fetcher pula arquivos que já existem

### Split cortando errado
- Usar `--test` primeiro — SEMPRE
- Ajustar `--thresh` (tentar 220 ou 245)
- Se o manhwa tiver gaps muito pequenos, baixar `--gap-min` pra 15
- Se tiver cortando painéis limpos, aumentar `--min-h` pra 400

### Painéis em branco depois do split
- São painéis descartáveis (créditos, páginas em branco)
- A pipeline remove os 5 primeiros automaticamente se forem em branco
- Se ainda sobrarem, pode ignorar — a pipeline pula painéis que falham na descrição

### Proxy SOCKS5 offline (erro "Proxy SOCKS5 offline, fallback para conexão direta")
- O proxy local `socks5h://localhost:1080` está caído
- O pipeline cai pra conexão direta automaticamente (funciona, só é mais lento)
- Se quiser usar proxy HTTP: as credenciais estão em `secrets/proxies.txt`

---

## 6. DICAS DOS AJUSTES QUE FIZEMOS

1. **Panel-splitter `--dark-mode`** — Essencial pra manhwas com fundo preto (muitos manhwas coreanos usam)
2. **`--thresh 230`** — Funciona bem pra maioria dos casos; 240 se o fundo for muito claro
3. **`--min-h 300`** — Painéis menores que 300px geralmente são decoração/efeito
4. **`--gap-min 25`** — A maioria dos manhwas tem gap de ~30px entre painéis
5. **Sempre testar antes** (`--test`) — O splitter gera um HTML de preview na pasta `_test_<slug>/`
