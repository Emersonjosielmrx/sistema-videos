# HeyGen Video Pipeline

Pipeline automatizado para gerar vídeos no HeyGen via Chrome DevTools Protocol (CDP), colando texto via Ctrl+V (Windows clipboard) e monitorando o render ate gerar o MP4.

## Estrutura

```
D:/roteador-heygen-api/
├── pipeline/
│   ├── run_one.py          # Pipeline COMPLETO: colar + render + download
│   ├── watch_download.py   # So monitora Scene rendered e baixa MP4
│   └── tts_fixes.py        # Dicionario de correcoes foneticas PT-BR
├── chrome_profile_heygen/  # Perfil do Chrome (login HeyGen)
├── videos/api_jobs/        # MP4s gerados
├── logs_watch_*.log        # Logs de cada render
└── *.md                    # Documentacao adicional
```

## Pre-requisitos

- Chrome com `--remote-debugging-port=9225` ja aberto (perfil em `chrome_profile_heygen/`)
- Logado em https://app.heygen.com
- Python 3.13 + `websockets`, `urllib.request` (ja inclusos no venv em `D:\hipercool-videos\venv\`)
- Windows (SendKeys Ctrl+V usa PowerShell nativo)

## Uso basico

### Gerar UM video

```cmd
cd D:\roteador-heygen-api
PYTHONUTF8=1 python pipeline\run_one.py 10000
```

Argumentos: numero de caracteres (3000 = 3min audio, 10000 = 11min, 20000 = 22min).

O `run_one.py` faz:
1. Le avatar atual - se nao comeca com `emerson`, troca via galeria "Choose Avatar"
2. Garante Motion Engine = Avatar III (evita limite de quota)
3. Constroi texto BASE com `tts_fixes.apply_fixes()`
4. Cola texto via `Set-Clipboard` + `SendKeys ^v`
5. Clica Render Scene com VERIFICACAO (ate 5 tentativas ate ver "Rendering")
6. Espera "Scene rendered" (max 50min)
7. Baixa MP4 via `urllib.request`

### Monitorar render existente (se voce ja clicou Render manualmente)

```cmd
set TAG=meu_video
set MAX_WAIT=3000
python pipeline\watch_download.py
```

## tts_fixes - correcoes foneticas PT-BR

Vozes tipo Chill Chase / Alex Nekrasov do HeyGen pronunciam mal varias palavras:

| Original | Aplica correcao |
|---|---|
| `voce` | -> `você` (com virgula antes) |
| `codigo` | -> `có-di-go` (hifenizacao forca silabas) |
| `implementar` | -> `implemen-tar` |
| `padrao` | -> `pad-rão` |
| `IA` | -> `I A` |
| `OAuth` | -> `O-Auth` |
| `n8n` | -> `n oito n` |

Adicionar novas regras:
```python
from tts_fixes import add_rule
add_rule('palavra_errada', 'pronuncia_correta')  # simples
add_rule(r'regex_pattern', 'substituicao', regex=True)  # regex
```

## Resultados observados (2026-07-27)

| Tam texto | Audio | Render | Arquivo | Tamanho |
|---|---|---|---|---|
| 3k chars | 03:44 | ~3min | emerson_3min_224s_7d54.mp4 | 54.7 MB |
| 5k chars | 06:00 | ~7min | emerson_5k_f4e64.mp4 | 84.1 MB |
| 10k chars | 11:39 | 40min | emerson_10k_699s_2682.mp4 | 165.9 MB |

**Escala**: ~14 MB / min audio, ~3.5 min render / min audio.

## LIMITACOES CONHECIDAS

### Limite diario de quota

Apos renderizar ~21min de audio no mesmo dia (3k+5k+10k), o proximo render (20k) travou em "Rendering" sem gerar MP4. **Limite diario da conta HeyGen**.

**Workaround**: renderizar 1 video grande por dia.

Sinais de limite:
- Render fica "Rendering" >30min sem "Scene rendered"
- "Scene rendered" aparece mas URL do video nao tem MP4

### Talking Photo deletado

Se o avatar do draft for Talking Photo deletado no servidor (ex: `emerson2`), Render Scene dah erro 400 silencioso e trava 45min ate timeout. **Sempre verificar avatar antes** (`current_avatar()`).

Avatars validos (2026-07-27): `emerson`, `emerson2` (talvez deletado), `emerson3`, `emerson5`, `marg*a`, `Eva`, etc.

## Arquitetura tecnica

### Por que paste via clipboard (Ctrl+V)?

O campo de script do HeyGen usa ProseMirror (editor rich text). Tentar inserir texto via CDP `Input.insertText` ou `Input.dispatchKeyEvent` (typing) dah perda de caracteres em textos >1k. O **unico** caminho confiavel para texto grande eh o clipboard do SO + Ctrl+V (SendKeys + SetForegroundWindow).

### Por que Avatar III?

`Avatar IV` e `Avatar V` contam contra quota (mais bonitos mas limitados). `Avatar III` eh "ilimitado" no plano da Haylla - pode renderizar varios videos sem bater quota rapido.

### Por que Chrome via CDP?

O HeyGen nao tem API publica de geracao. A unica forma de automatizar eh controlar o navegador. CDP da controle total (cliques, typing, leitura de DOM, fetch) sem dependencia de API key.

## Troubleshooting

| Sintoma | Causa provavel | Solucao |
|---|---|---|
| paste incompleto (< 50%) | Race clipboard/set_clipboard | Rodar de novo; usar `_recola_20k.py` (timing mais conservador) |
| Render nao inicia | Avatar Talking Photo deletado | Trocar avatar via galeria "Choose Avatar" |
| Editor sem botao Render | Estado stale do draft anterior | Navegar pra `https://app.heygen.com/create-v4/draft?vt=l` |
| Conexao CDP cai | Chrome reiniciou | Religar Chrome (perfil em chrome_profile_heygen/) |

## Documentos relacionados

- `HANDOFF_HEYGEN_API.md` - historico da exploracao da API
- `PROCESSO_FUNCIONAL_2026-07-27.md` - passo-a-passo do que funciona
- `PROCESSO_PREVIEW_AVATAR3.md` - detalhes do setup do Avatar III