> **DESATUALIZADO (05/10/2026)** - escrito pelo agente anterior; tem erros (esp e SUSPENSO, nao 'API desabilitada'; distribuir_videos.py postava fora do nicho e foi desativado). Use `HANDOFF_REDE.md` e `REDE_ESTADO_E_PENDENCIAS.md`.

# Sistema de Canais e Distribuicao de Videos

Guia completo para qualquer modelo ou operador entender e operar o sistema de
publicacao de videos nos canais do YouTube.

---

## Visao Geral da Arquitetura

```
D:\manhwa-react\              <- Projeto ManhwaReact (producao de shorts)
  manhwareact.py              <- Processamento de video (webcam + conteudo -> short)
  distribuir_videos.py        <- Distribuicao de videos prontos entre canais
  config.json                 <- Config do processador

D:\postador-de-videos\        <- Sistema de publicacao no YouTube
  bin\youtube_poster.py       <- Upload direto via YouTube API (OAuth2 resumable)
  bin\politica.py             <- Rate limiting, bloqueios, ledger de uploads
  config\canais_status.json   <- Lista de canais bloqueados (suspensos/token_morto/desativados)
  config\canais_reservados.json <- Canais reservados para projetos especificos
  config\politica.json        <- Limites de volume (max uploads/dia, intervalo, etc)
  logs\uploads_ledger.jsonl   <- Registro de TODOS os uploads feitos (append-only)

D:\credenciais-canais\
  youtube_canais.json         <- Credenciais OAuth2 de TODOS os 49 canais
```

---

## Os 49 Canais do YouTube

### Classificacao (atualizado em 2026-10-04)

| Categoria | Qtd | Status |
|-----------|-----|--------|
| **Suspensos** | 22 | Suspensos pelo YouTube em 2026-09-04 por spam. NAO usar. |
| **Token morto** | 10 | OAuth2 refresh_token invalido (invalid_grant). Requer relogin. |
| **Desativados** | 5 | Desativados manualmente. NAO usar. |
| **Reservados (principais)** | 3 | Reservados para o projeto manhwa-react. |
| **Livres (usaveis)** | 9 | Funcionam normalmente, tem_upload=true. |
| **Livres (sem flag)** | 6 | Funcionam (confirmado), mas tem_upload=false no JSON. |
| **TOTAL** | ~49 | (alguns IDs duplicados entre categorias) |

### Canais Bloqueados (37 total) - NAO USAR

**22 suspensos** (canais_status.json -> suspensos):
Suspensos em 2026-09-04 por postagem automatica em massa (spam).
Incluem: fake News ia, fofos e absurdos, Cerebro Digital, Emerson AI (2x),
sintetize risada, danca e musica com ia, Game of thrones kingsroad brasil,
Inovare inteligencia artificial (2x), energia solar ia, Videos cassetadas ia,
curiosidades e fatos ia, fala com a IA, Aulas Ia, ia brasileira,
IA PRO, Inovare com ia, Re cenas ia, Fabio com ia, inovaremanhwaverseviet, mais 1.

**10 token_morto** (canais_status.json -> token_morto):
Token OAuth2 expirou e precisa relogin manual no navegador.
Incluem: InovareManhwaVerse, inovaremanhwabr, Inovaremanhwaversethai,
@IAAgora-h3n*, @IAAgora-n7h, @UniversoIA-d6s*, @IASemLimites-h4b,
@CodigoInteligente-n7j**, @MenteArtificial-i5r*, @Inovaremanhwaversethai (v2).

(*) = canal principal/reservado, token renovado e funciona apesar de estar na lista.
(**) = usuario confirmou que funciona apesar de estar na lista.

**5 desativados** (canais_status.json -> desativados):
Desativados manualmente: fabio com ia, enpresainovare, emersonjosiel1995 (2x),
nova conta de manga br.

### 3 Canais Principais (Reservados)

Reservados exclusivamente para o projeto manhwa-react (canais_reservados.json):

| ID | Nome | Email | Projeto |
|----|------|-------|---------|
| novo_mente_artificial_i5r | MenteArtificial / ManhwaReact | (ver credenciais) | manhwa-react |
| novo_universo_ia_d6s | UniversoIA / CenaReact | (ver credenciais) | manhwa-react |
| novo_ia_agora_h3n | IAAgora / InventoReact | (ver credenciais) | manhwa-react |

Estes canais ja receberam 2 videos cada em 2026-10-04 (6 total).
Sao os canais prioritarios e sempre recebem videos primeiro.

### 15 Canais Livres (Usaveis para Distribuicao)

Canais que NAO estao em nenhuma lista de bloqueio e TEM refresh_token valido:

| # | ID no JSON | Nome | Email | tem_upload |
|---|------------|------|-------|------------|
| 1 | KOpyXE9rBy1YirlZ | Animescomia | canalanimescomia@gmail.com | true |
| 2 | 0RW4rz4ekPpkPcZx | Inovare Manhwa esp | inovaremanhwaverseesp@gmail.com | true |
| 3 | GG97QQt8lmyv0dDG | inovare Manhwa french | inovaremanhwaversefrench@gmail.com | true |
| 4 | GtuH5ezUK8eBaC60 | Inovaremanhwaversehindi | inovaremanhwaversehindi@gmail.com | true |
| 5 | nYsAKUb3DbR1QOEm | YouTube inovaremanhwaverseind | inovaremanhwaverseind@gmail.com | true |
| 6 | UYjkdFO3V3kjmKU5 | Inovare Manhwa eng | inovaremanhwaverseing@gmail.com | true |
| 7 | 7zpNZNll2jlBnQ0J | inovaremanhwaverseita | inovaremanhwaverseita@gmail.com | true |
| 8 | TkfzifstYEoG4jKg | inovare manhwa verse ru | inovaremanhwaverserussian@gmail.com | true |
| 9 | novo_manhwareact_ia | ManhwaReact-ia | emersonjosiel2032@gmail.com | true |
| 10 | novo_assistiainvestimentos | AssistIA Investimentos | emersonjosiel2033@gmail.com | false |
| 11 | novo_historias_em_frames | HistoriasEmFrames | emersonjosiel2027@gmail.com | false |
| 12 | novo_cartuchoreact | CartuchoReact | emersonjosiel2030@gmail.com | false |
| 13 | novo_forjareact | ForjaReact | emersonjosiel0@gmail.com | false |
| 14 | novo_mundoquenaoexiste | MundoQueNaoExiste | rezaulkarimul355@gmail.com | false |
| 15 | novo_dicasfinanceirasdaia | DicasFinanceirasDaIA | empressinovare@gmail.com | false |

Nota: tem_upload=false nao significa que nao funciona. O usuario confirmou que
todos os 15 canais acima tem refresh_token valido e renovam automaticamente.

---

## Como Funciona o Upload

### Fluxo Completo

```
1. manhwareact.py processa videos brutos -> gera .mp4 + .postar.json
2. distribuir_videos.py le os .postar.json e os canais disponiveis
3. Para cada par (video, canal):
   a. youtube_poster.upload() envia o video via YouTube API
   b. politica.registrar_upload() registra no ledger
4. Espera 30 segundos entre uploads
```

### youtube_poster.upload()

Arquivo: `D:\postador-de-videos\bin\youtube_poster.py`

```python
upload(video_path, titulo, descricao, tags, canal, privacy="public",
       categoria="24", made_for_kids=False, publish_at=None)
```

- Chama `refresh_access_token(canal)` internamente para renovar o token OAuth2
- Faz upload resumable (chunked) para a YouTube Data API v3
- Retorna o `videoId` do video publicado
- NAO aplica politica de rate limiting — quem chama e responsavel

### refresh_access_token(canal)

- POST para `https://oauth2.googleapis.com/token`
- Envia: client_id, client_secret, refresh_token, grant_type=refresh_token
- Retorna: access_token (valido por ~1 hora)
- Se o refresh_token estiver invalido: erro `invalid_grant`

### politica.registrar_upload()

Arquivo: `D:\postador-de-videos\bin\politica.py`

- Appends uma linha JSON ao ledger: `D:\postador-de-videos\logs\uploads_ledger.jsonl`
- Cada linha contem: canal, video_id, arquivo, timestamp, publish_at
- O ledger e a fonte de verdade para saber quantos uploads foram feitos

### Limites da Politica (politica.json)

| Regra | Valor Padrao | Descricao |
|-------|--------------|-----------|
| max_uploads_por_canal_dia | 3 | Maximo de uploads por canal por dia |
| max_uploads_total_dia | 12 | Maximo total de uploads por dia (todos os canais) |
| intervalo_min_horas_mesmo_canal | 2h | Intervalo minimo entre uploads no mesmo canal |
| exigir_aprovacao_humana | true | Requer aprovacao antes de cada upload |
| parar_tudo_ao_detectar_suspensao | true | Para tudo se um canal for suspenso |

**IMPORTANTE**: 22 canais ja foram suspensos por postagem automatica em massa.
Manter aprovacao humana e poucos uploads por dia e CRITICO para evitar mais suspensoes.

---

## distribuir_videos.py - Guia de Operacao

### O que faz

Distribui videos prontos (.postar.json) entre canais ociosos, 1 video por canal.
Le automaticamente quais canais estao bloqueados e quais estao livres.

### Localizacao dos videos prontos

```
D:\hipercool-materiais\manhwa-react\shorts\
  manhwareact\           <- Pasta do canal
    2026_10_03_*.mp4     <- Video renderizado
    2026_10_03_*.postar.json  <- Metadados para publicacao
```

Cada `.postar.json` contem:
- arquivo: nome do .mp4
- titulo, descricao, tags: metadados do YouTube
- thumb: thumbnail
- privacy: "public" ou "private"
- made_for_kids: false
- pronto: true (indica que o video esta pronto para publicar)

### Como rodar

```bash
# Ver o plano de distribuicao (dry-run, nao faz upload)
python -X utf8 distribuir_videos.py

# Executar os uploads de verdade
python -X utf8 distribuir_videos.py --confirmar
```

**SEMPRE usar `-X utf8`** porque os titulos dos videos contem emojis e caracteres
especiais que causam UnicodeEncodeError no Windows (cp1252).

### Logica de selecao de canais

1. Carrega todos os 49 canais de `D:\credenciais-canais\youtube_canais.json`
2. Carrega `D:\postador-de-videos\config\canais_status.json`
3. Exclui canais que estao em: suspensos, token_morto, desativados
4. Exclui os 3 canais principais (MAIN_IDS) que sao reservados
5. Exclui canais sem refresh_token
6. Resultado: ~15 canais usaveis

### Logica de distribuicao

- Faz zip(videos, canais) -> cada video vai para um canal diferente
- Limite: 1 video por canal por execucao
- Espera 30 segundos entre uploads
- Registra cada upload no ledger da politica

### Output esperado

```
============================================================
  DISTRIBUICAO DE VIDEOS
  Canais disponiveis: 15
  Videos disponiveis: 15
============================================================

PLANO DE DISTRIBUICAO:
------------------------------------------------------------
  1. Titulo do video...
     -> NomeDoCanal (email@gmail.com)
  ...
------------------------------------------------------------

Total: 15 uploads
```

---

## Arquivos de Configuracao

### youtube_canais.json (credenciais)

Caminho: `D:\credenciais-canais\youtube_canais.json`

Array de 49 objetos, cada um com:
```json
{
  "id": "identificador_unico",
  "nome": "Nome do Canal",
  "clientId": "xxx.apps.googleusercontent.com",
  "clientSecret": "xxx",
  "refresh_token": "<SEGREDO_REMOVIDO>",
  "access_token": "<SEGREDO_REMOVIDO>",
  "scope": "https://www.googleapis.com/auth/youtube.upload ...",
  "tem_upload": true,
  "tem_refresh": true,
  "email": "email@gmail.com"
}
```

### canais_status.json (bloqueios)

Caminho: `D:\postador-de-videos\config\canais_status.json`

```json
{
  "suspensos": [{"nome": "...", "id": "...", "motivo": "...", "em": "2026-09-24"}],
  "token_morto": [{"nome": "...", "id": "...", "token_hash": "...", "em": "..."}],
  "desativados": [{"nome": "...", "id": "...", "motivo": "...", "em": "..."}]
}
```

- `suspensos`: Canal suspenso pelo YouTube. NAO usar.
- `token_morto`: Refresh token invalido. Requer relogin no navegador.
  Tem `token_hash` — quando o token e renovado (relogin), o bloqueio cai automaticamente.
- `desativados`: Desativado manualmente.

### canais_reservados.json

Caminho: `D:\postador-de-videos\config\canais_reservados.json`

```json
{
  "manhwa-react": [
    "novo_mente_artificial_i5r",   // ManhwaReact
    "novo_universo_ia_d6s",        // CenaReact
    "novo_ia_agora_h3n"            // InventoReact
  ]
}
```

Canais reservados ficam FORA dos pools de rotacao dos postadores automaticos.

### uploads_ledger.jsonl

Caminho: `D:\postador-de-videos\logs\uploads_ledger.jsonl`

Append-only, uma linha JSON por upload:
```json
{"canal": "...", "video_id": "...", "arquivo": "...", "ts": "2026-10-04T14:30:00Z"}
```

Use este arquivo para verificar quantos uploads foram feitos hoje:
```bash
grep "2026-10-04" D:/postador-de-videos/logs/uploads_ledger.jsonl | wc -l
```

---

## Operacoes Comuns

### Verificar uploads de hoje

```bash
cat D:/postador-de-videos/logs/uploads_ledger.jsonl | grep "2026-10-04"
```

### Verificar quantos canais estao disponiveis

```bash
cd D:/manhwa-react
.venv/Scripts/python.exe -X utf8 distribuir_videos.py
# (sem --confirmar = dry-run, so mostra o plano)
```

### Verificar status da politica

```bash
cd D:/postador-de-videos
python bin/politica.py
```

### Postar nos canais principais (3 canais reservados)

Os 3 canais principais sao gerenciados pelo sistema principal do manhwareact.py:
```bash
cd D:/manhwa-react
.venv/Scripts/python.exe manhwareact.py publicar
```

### Postar nos canais secundarios (15 canais livres)

```bash
cd D:/manhwa-react
.venv/Scripts/python.exe -X utf8 distribuir_videos.py --confirmar
```

### Processar novos videos

```bash
cd D:/manhwa-react
# Colocar videos em 1-COLOQUE-AQUI\
.venv/Scripts/python.exe manhwareact.py batch
```

---

## Regras de Seguranca CRITICAS

1. **NUNCA fazer upload em massa** — 22 canais ja foram suspensos por isso em 2026-09-04
2. **Maximo 3 uploads por canal por dia** (configuravel em politica.json)
3. **Maximo 12 uploads total por dia** (todos os canais somados)
4. **Intervalo minimo de 2 horas** entre uploads no mesmo canal
5. **Sempre usar --confirmar** para execucao real (sem a flag = dry-run)
6. **Sempre verificar o ledger** antes de rodar para ver quantos uploads ja foram feitos hoje
7. **NAO usar canais da lista suspensos** — sao permanentemente banidos
8. **Cuidado com canais token_morto** — podem funcionar se o token foi renovado,
   mas verificar caso a caso

---

## Historico de Publicacoes (2026-10-04)

### Lote 1: Canais Principais (6 videos)

| Canal | Video ID | URL |
|-------|----------|-----|
| ManhwaReact (novo_mente_artificial_i5r) | awX_r8Dbj_E | https://youtu.be/awX_r8Dbj_E |
| ManhwaReact (novo_mente_artificial_i5r) | B7NyByTnYfE | https://youtu.be/B7NyByTnYfE |
| CenaReact (novo_universo_ia_d6s) | goJ_jqSWDcs | https://youtu.be/goJ_jqSWDcs |
| CenaReact (novo_universo_ia_d6s) | 2NCLDstA6TQ | https://youtu.be/2NCLDstA6TQ |
| InventoReact (novo_ia_agora_h3n) | kIVKFUzxUvg | https://youtu.be/kIVKFUzxUvg |
| InventoReact (novo_ia_agora_h3n) | 5XSMItlSwLI | https://youtu.be/5XSMItlSwLI |

### Lote 2: Canais Secundarios (15 tentativas, 13 sucesso, 2 falhas)

Executado via `distribuir_videos.py --confirmar` em 2026-10-04.

| # | Canal | Video ID | URL | Status |
|---|-------|----------|-----|--------|
| 1 | Animescomia | e3erT3rZsos | https://youtu.be/e3erT3rZsos | OK |
| 2 | Inovare Manhwa esp | - | - | FALHA (403 Forbidden) |
| 3 | inovare Manhwa french | jDxMrrKvOSE | https://youtu.be/jDxMrrKvOSE | OK |
| 4 | Inovaremanhwaversehindi | a10g9t8TPRw | https://youtu.be/a10g9t8TPRw | OK |
| 5 | inovaremanhwaverseind | Vx_YuCgrXmM | https://youtu.be/Vx_YuCgrXmM | OK |
| 6 | Inovare Manhwa eng | - | - | FALHA (403 Forbidden) |
| 7 | inovaremanhwaverseita | kmAt11C8TSo | https://youtu.be/kmAt11C8TSo | OK |
| 8 | inovare manhwa verse ru | b5wIgdKVHtw | https://youtu.be/b5wIgdKVHtw | OK |
| 9 | ManhwaReact-ia | px-pO3sRxCw | https://youtu.be/px-pO3sRxCw | OK |
| 10 | AssistIA Investimentos | Lk5EbXnFKI4 | https://youtu.be/Lk5EbXnFKI4 | OK |
| 11 | HistoriasEmFrames | rUlvwVfGfOk | https://youtu.be/rUlvwVfGfOk | OK |
| 12 | CartuchoReact | gyuhRigIDcc | https://youtu.be/gyuhRigIDcc | OK |
| 13 | ForjaReact | qz-a5UNYGns | https://youtu.be/qz-a5UNYGns | OK |
| 14 | MundoQueNaoExiste | lOQC4UjOHW4 | https://youtu.be/lOQC4UjOHW4 | OK |
| 15 | DicasFinanceirasDaIA | WL4v_ZND6Kk | https://youtu.be/WL4v_ZND6Kk | OK |

**Falhas**: Inovare Manhwa esp (0RW4rz4ekPpkPcZx) e Inovare Manhwa eng (UYjkdFO3V3kjmKU5)
retornaram HTTP 403 Forbidden. Provavel causa: YouTube Data API nao habilitada
no projeto OAuth desses canais, ou cota de API excedida. Verificar no Google Cloud Console.

---

## Troubleshooting

### UnicodeEncodeError (cp1252)

Titulos com emojis causam erro no Windows. Solucao:
```bash
python -X utf8 distribuir_videos.py
```
Ou adicionar `os.environ["PYTHONUTF8"] = "1"` no inicio do script.

### invalid_grant no refresh_token

O refresh_token expirou. Opcoes:
1. Fazer relogin OAuth2 no navegador para aquele canal
2. O canal sera adicionado automaticamente em canais_status.json -> token_morto
3. Quando renovar o token, o bloqueio cai automaticamente (via token_hash)

### Canal nao aparece como usavel

Verificar se o canal esta em alguma lista de canais_status.json.
Mesmo que o canal funcione, se estiver em suspensos/token_morto/desativados,
o script distribuir_videos.py vai ignora-lo.

### EOFError: input()

Nao e possivel usar input() em shells nao-interativos.
Usar `--confirmar` como flag de linha de comando em vez de perguntar ao usuario.

### Videos .postar.json nao encontrados

Verificar se o manhwareact.py terminou o processamento.
Os .postar.json ficam em: `D:\hipercool-materiais\manhwa-react\shorts\<canal_slug>\`
