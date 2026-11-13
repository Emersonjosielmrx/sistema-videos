# 📮 PLAYBOOK DE POSTAGEM NO YOUTUBE — completo (à prova de perder o histórico)

> Escrito 2026-07-01. Tudo que foi construído e APRENDIDO postando os recaps de
> manhwa e os tutoriais de IA. Se você é um agente novo e o histórico sumiu, este
> arquivo sozinho te ensina a postar exatamente como foi feito. PT-BR.

---

## 0) TL;DR — pra postar rápido
```bash
cd /d/hipercool-producao          # (ou /d/hipercool-inferior-fix — os scripts existem nos 2)
export PYTHONUTF8=1
PY="D:/hipercool-videos/venv/Scripts/python.exe"

# 1. cortar shorts do vídeo CENSURADO
"$PY" bin/split-shorts.py --video "CAMINHO_CENSURADO.mp4" --obra "The Meek Cat" --capitulo 2
# 2. montar a fila (edita o config antes; distribui canais/dias/horários)
"$PY" bin/montar-fila.py --config "_LEIA_POSTAR_VIDEOS/config_fila.json"
# 3. conferir sem postar
"$PY" bin/postar-fila.py --plano "_LEIA_POSTAR_VIDEOS/fila_meek_caps234.json" --dry-run
# 4. postar (privado + publishAt agendado). Idempotente.
"$PY" bin/postar-fila.py --plano "_LEIA_POSTAR_VIDEOS/fila_meek_caps234.json"
```
Postar 1 vídeo avulso:
```bash
"$PY" bin/youtube_poster.py --video X.mp4 --titulo "T" --descricao "D" --tags "a,b" \
  --canal "inovare recap manga" --privacy private --publish-at "2026-07-01T21:00:00.000Z"
```

---

## 1) REGRAS INVIOLÁVEIS
1. **Manhwa: só postar versão CENSURADA** (`..._CENSURADO_ULTIMO.mp4`). Postar não-censurado
   = risco de BAN do canal. Os shorts têm que ser cortados DO vídeo censurado.
2. **PYTHONUTF8=1 sempre.** Sem isso o console Windows (cp1252) crasha nos emojis/caixa.
3. **Nunca `nohup &`.** Use background do tool (pra receber fim real).
4. **Confirmar com a dona antes de postar de verdade** (ação pública/irreversível). Sempre `--dry-run` antes.
5. **Idempotência:** `postar-fila.py` grava status no próprio JSON; rodar de novo NÃO reposta o que já subiu.

---

## 2) LIMITES REAIS (TESTADOS EMPIRICAMENTE — não é chute de doc)

Existem **3 limites diferentes** do YouTube/API. O que te barra é o menor deles:

### a) Limite diário de upload da CONTA (erro `uploadLimitExceeded`, HTTP 400)
- É POR CANAL/conta. **VARIA muito por conta** (idade/verificação/histórico).
- Medido em 01/07: `inovare recap manga`=10, `nova conta de manga br`=10,
  `gameoftrones`=10, `inovarecap`=~9, **`manhwaverse esp`=≥21** (nem travou em 21).
- Deletar vídeo NÃO devolve a cota do dia (o contador conta o upload feito).

### b) Cota diária de UPLOADS do PROJETO de API (erro `rateLimitExceeded`/`quotaExceeded`, HTTP 429)
- Mensagem: *"Quota exceeded for quota metric 'Video Uploads' and limit 'Video Uploads per day'"*.
- É POR PROJETO Google (por `clientId`). **Vários canais compartilham 1 projeto → somam nesse teto.**
- ⚠️ **GARGALO REAL da rede:** 33 dos 37 canais usam o MESMO projeto (`clientId 43266821547-...`).
  Todos os uploads deles somam num único teto/dia (observado ~90-100/dia). Estourou em 01/07.
- Canais com projeto PRÓPRIO não sofrem: `inovare recap manga` (19117647026), `nova conta`
  (1088438334534), `manhwaverse ita` (485336095176), `manhwaverse viet` (437523744488).
- ⚠️ **Testes consomem esse teto!** Rodar `testar-canais.py`/`testar-limite.py` gasta uploads
  do projeto compartilhado — depois sobra menos pra postagem real no mesmo dia. Testar com parcimônia.

### c) Cota de UNIDADES da API (10.000/dia por projeto; upload=1.600)
- Daria só ~6 uploads/dia, MAS na prática o (b) "Video Uploads per day" aparece primeiro.

### Fatos que decorrem disso
- **Agendar `publishAt` pra frente NÃO economiza cota.** O *upload* gasta a cota no dia em
  que RODA. Pra espalhar em dias, RODE a postagem em dias diferentes (é o que o postador faz).
- Pra postar MAIS por dia: distribuir os canais em MAIS projetos Google (cada projeto = +teto).

---

## 3) ONDE ESTÁ TUDO
| Coisa | Caminho |
|---|---|
| Scripts | `D:\hipercool-producao\bin\` (cópia também em `D:\hipercool-inferior-fix\bin\`) |
| Python | `D:\hipercool-videos\venv\Scripts\python.exe` (+ `PYTHONUTF8=1`) |
| Credenciais dos 37 canais (OAuth) | `D:\credenciais-canais\youtube_canais.json` |
| Vídeos manhwa prontos (censurados) | `D:\hipercool-materiais\videos\*_CENSURADO_ULTIMO.mp4` |
| Shorts cortados | `workspace\shorts\<obra>-capN\` |
| Filas + guia + config | `D:\hipercool-producao\_LEIA_POSTAR_VIDEOS\` |
| Postador standalone (Windows) | `D:\postador-de-videos\` |
| Vídeos do OpenClaw (baixados) | `D:\openclaw-videos\` |

---

## 4) OS SCRIPTS (o que cada um faz)
- **`youtube_poster.py`** — posta 1 vídeo via OAuth (refresh_token→access_token→upload resumable).
  Flags: `--canal` (nome OU id), `--privacy`, `--publish-at` (RFC3339 UTC; força private),
  `--listar-canais`, `--test-token`. Erros da API saem legíveis (`ERRO 400 [uploadLimitExceeded]`).
- **`postagem_meta.py`** — gera TÍTULO/DESCRIÇÃO/TAGS virais + anti-ban (troca palavra de strike).
  Funções `titulo_short/descricao_short/titulo_completo/descricao_completo/tags`.
- **`split-shorts.py`** — corta vídeo longo em Shorts (~55s) com tela de CTA no fim. Corta em silêncios.
- **`montar-fila.py`** — monta fila de MANHWA a partir de um config JSON (distribui 2 canais,
  dias por cota, horários espalhados). Shorts do mesmo cap ficam no MESMO canal (CTA "parte X no perfil").
- **`montar-fila-tutoriais.py`** — monta fila dos 92 tutoriais de IA (12 canais). Tira título/desc
  do roteiro `.md`. SÓ vídeos com roteiro (exclui manhwa/fragmentos). Config no topo do arquivo.
- **`postar-fila.py`** — posta o que é do dia (ou VENCIDO: `upload_dia <= hoje` = catch-up).
  Idempotente, grava status, pausa `POSTAR_SLEEP_S` (default 4s) entre uploads p/ não estourar rate.
- **`batch-post-shorts.py`** — atalho: corta + posta shorts de 1 cap.
- **`testar-canais.py`** — testa quais canais postam (1 upload privado em cada). ⚠️ gasta cota.
- **`testar-limite.py`** — mede o limite diário real de 1 canal (empurra até `uploadLimitExceeded`).
- **`apagar-testes.py`** — apaga os vídeos de teste (lê os IDs salvos). Rode depois de testar.

---

## 5) OS CANAIS (37 total; 30 postam)
- **Manhwa (2, projeto próprio):** `inovare recap manga` (@InovareManhwaVerse) ·
  `nova conta de manga br` (@inovaremanhwabr).
- **IA/automação (12, projeto compartilhado):** inovarecap, seebotstia, raiz fabricadeautomacoes0,
  raiz 5 aulasrevolution, emersongenc cerebro digital, raiz 2 emersonjosiel649, raiz 6 emersongencshin,
  raiz 4 solarmundo195, en1653964, repost 1 inovarecap, repost 2 emersongenc, repost fabiovideoseducativos.
- **Rede ManhwaVerse (8 idiomas):** esp, french, hindi, ind, ing, ita, russian, thai.
- **NÃO postam (7):** `emersonjosiel1995`+`emersonjosiel1995nov` = SUSPENSOS. `enpresainovare`+
  `fabio com ia` = TOKEN MORTO (o `clientSecret` no JSON tem um `=` a mais no início — corrigir tirando o `=`).
  `manhwaverse viet` deu rateLimit transitório (funciona retentando).
- Ver todos: `python bin/youtube_poster.py --listar-canais`.

---

## 6) POSTADOR AUTOMÁTICO (não depende do Claude/VS Code)
Roda pelo **Agendador de Tarefas do Windows**, task **`PostadorDeVideos`**, todo dia **06:40**
(StartWhenAvailable = se o PC estava desligado, roda ao ligar). Chama `D:\postador-de-videos\postar-hoje.cmd`
→ `postar_hoje.py`, que roda TODAS as filas `fila_*.json` de `_LEIA_POSTAR_VIDEOS\` (catch-up).
- Postar à mão: 2 cliques em `D:\postador-de-videos\postar-hoje.cmd`. Logs em `D:\postador-de-videos\logs\`.
- Recriar a task:
```powershell
$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c "D:\postador-de-videos\postar-hoje.cmd"'
$t = New-ScheduledTaskTrigger -Daily -At 6:40am
$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName 'PostadorDeVideos' -Action $a -Trigger $t -Settings $s -Force
```

---

## 7) OS VÍDEOS DO OPENCLAW (no Mac)
- Mac `192.168.18.45`. Servidores HTTP: **8888** = projeto hipercool-videos; **8100** = pasta
  OpenClaw inteira (`~/Downloads/apps/openclaw/`). SSH (22) fechado.
  ⚠️ 8100 expõe `secrets/` sem senha — matar quando não usar (`lsof -ti:8100 | xargs kill` no Mac).
- Vídeos: `http://192.168.18.45:8100/workspace/videos-produzidos-v2/` (107, COM b-roll) e
  `videos-produzidos/` (107, sem). Roteiros (título/desc): `videos-long-prontos/*.md`.
- ⚠️ Pasta é MISTA: tem tutorial de IA (com roteiro) + manhwa de outras obras + fragmentos de
  sub-workflow (sem roteiro). `montar-fila-tutoriais.py` só pega os que têm roteiro.

---

## 8) GOTCHAS (erros que já custaram tempo)
- `rateLimitExceeded` (429) = não é "rápido demais", é o **teto diário de upload do PROJETO**
  compartilhado. Retentar hoje não adianta; reseta à meia-noite do **Pacífico**. O catch-up pega amanhã.
- `uploadLimitExceeded` (400) = limite diário da CONTA. Idem, reseta e o catch-up recupera.
- Anti-ban: título/descrição passam por troca de palavras de strike (ver `_ANTI_BAN` em
  `postagem_meta.py` e `viralizador.py`). Adicione lá se aparecer termo novo.
- `youtube_canais.json`: 2 entradas têm `clientSecret` começando com `=` (typo) → 401. Tirar o `=`.
- publishAt é **UTC**. Brasília = UTC−3 (ex.: 21:00 UTC = 18:00 BRT).

---

## 9) FLUXO SEGURO DE TESTE DE LIMITE (sem queimar cota nem arriscar ban)
- NÃO martele os 37 canais até o limite (risco de suspensão + gasta a cota do projeto compartilhado).
- Meça numa AMOSTRA (2-3 canais) com `testar-limite.py <id1> <id2>`; depois `apagar-testes.py`.
- Lembre: os testes gastam o teto "Video Uploads per day" do projeto → não teste no mesmo dia em
  que for postar muito conteúdo real nos canais do MESMO projeto.

---
Guia operacional curto (passo a passo) também em:
`D:\hipercool-producao\_LEIA_POSTAR_VIDEOS\LEIA_PRIMEIRO.md`
