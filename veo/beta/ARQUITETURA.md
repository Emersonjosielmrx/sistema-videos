# Arquitetura — bot Veo/Flow

Como as peças se encaixam. Leia junto com o README.

## Fluxo de um vídeo (do início ao mp4)

```
run_cron_loop_3contas.bat   (loop infinito; PYTHONUTF8=1)
        │
        ▼
loop_cron.py  ──chama──►  cron_gerar_video_llm.run()   [ORQUESTRADOR]
        │
        │  1. escolher_sessao()  -> pega a próxima conta VIVA
        │       (pula quem está EXHAUSTED / em cooldown; lista vem de contas.py)
        │  2. pipeline de LLM: agents.py + llm_client.py
        │       -> decide tema, roteiro/prompt, faz crítica de qualidade
        │  3. gerar_video()  -> dispara o WORKER como subprocesso:
        │
        ▼
gera_auto.py   [WORKER]  (roda como processo separado)
        │  - lê FLOW_SESSION/FLOW_PORT/FLOW_PROFILE do ambiente
        │  - garante Chrome aberto na porta CDP (perfil = profile da conta)
        │  - CHECA CRÉDITO antes de gastar tempo  ──►  creditos.py
        │       (texto na página  +  saldo no menu de conta)
        │  - escreve o prompt, submete, espera, baixa o mp4
        │       (cliques de baixo nível  ──►  flow_bot.py  ──► config.py)
        │
        ▼
   mp4 salvo em videos/cron_shorts/
        │
        ▼
   de volta no orquestrador: PORTEIRO (validar_video.py: decodifica/9:16/áudio/preto; conferir_fala.py: falou o
   pedido em pt?) -> reprovado vai para videos/cron_shorts/rejeitados/; aprovado entra no cache (video_cache.json)
        │
        ▼  (16/10) tarefa ManhwaReact-Rede, de hora em hora (D:\manhwa-react\scripts\rede_hora_em_hora.bat):
   D:\postador-de-videos\bin\limpar_veo.py --max 3  -> D:\hipercool-materiais\veo\limpos\<nome>.mp4/.json
        (decodifica, marca d'água de IA no canto, logo do TikTok, dedupe de vídeo [dedupe_video.py],
         legenda palavra a palavra pelo ÁUDIO, volume -14 LUFS; um render por vez [trava_render.py])
        │
        ▼
   D:\manhwa-react\mr\rede.py  -> YouTube (navegador) nos canais de canais_veo_limpo, vagas próprias do Veo,
        teto de uploads do dia, piso da política (4/canal/dia, 1 h); depois extras_rede.py e metricas_rede.py
        │
        ▼
   metricas_rede.py lê o Studio (navegador) e grava o número real em metrics do video_cache.json (AT-03)
```

Fotos de entrada (16/10): `escolher_foto(canal)` usa a subpasta da persona (`FOTOS_POR_PERSONA`) e NUNCA foto
com marca de IA (`logs\marcas_fotos.json`, gerado por `separar_fotos_marcadas.py`); sem foto limpa, não gera.
Prompt: `agents.prompt_com_fala` (fala entre aspas duplas, 9:16, "no on-screen text").

## O contrato de "acabou o crédito" (importante!)

O worker e o orquestrador são **processos diferentes**. Eles se falam por
código de saída + uma linha no stdout:

```
gera_auto.py detecta sem crédito
      │  (usa creditos.py: creditos_esgotados() e ler_saldo_creditos())
      ▼
  levanta CreditosEsgotadosError
      ▼
  imprime:  CREDITOS_ESGOTADOS padrao='<frase>'
  sai com:  exit code 2
      │
      ▼
cron_gerar_video_llm.gerar_video() lê exit 2 + o marcador
      ▼
  retorna a tupla  ("NO_CREDITS", padrao)
      ▼
  run() chama marcar_creditos_esgotados(conta)
      ▼
  conta vira status "EXHAUSTED" em logs/sessoes_status.json
  com cooldown até a próxima meia-noite (reset diário do Flow)
      ▼
  próximo ciclo: escolher_sessao() pula essa conta e usa outra
```

**Não mude** o exit code 2, o texto `CREDITOS_ESGOTADOS padrao='...'` nem a
tupla `("NO_CREDITS", ...)` sem mudar os dois lados juntos — é o que faz o
failover funcionar.

## Responsabilidade de cada módulo vivo

| Módulo | Camada | Responsabilidade |
|---|---|---|
| `contas.py` | config | Lista única de contas (session/port/profile) + derivados |
| `config.py` | config | Paths, URLs, timeouts |
| `loop_cron.py` | entrada | Loop infinito; chama `run()` |
| `cron_gerar_video_llm.py` | orquestrador | Escolhe conta, roda LLM, dispara worker, failover, estado |
| `gera_auto.py` | worker | Automação real do Flow (1 vídeo por execução) |
| `flow_bot.py` | worker | Playwright de baixo nível (cliques/seletores) |
| `creditos.py` | worker | Detecção de crédito esgotado |
| `agents.py` | LLM | Agentes (tema, roteiro, crítica) |
| `llm_client.py` | LLM | Chamada às APIs de LLM + rotação de chave |
| `vencedoras.py` | dados | Vídeos "vencedores" (referência de qualidade) |
| `thumbnail_client.py` | pós | Gera thumbnail |
| `metrics_client.py` | pós | Registra métricas |
| `dashboard.py` | extra | Painel (subprocesso opcional) |
| `veo_api.py` / `api_server.py` | extra | Servidores HTTP alternativos (não usados no loop) |

## Estado em disco

Tudo em `logs/`:
- `sessoes_status.json` — por conta: `status`, `cooldown_until`,
  `creditos_renova_em`, `padrao_creditos`, `last_motivo`. É daqui que sai o
  comando `sessoes`.
- `cron_gerar_llm.log` — log corrido.
- `video_cache.json` — fórmula/score de cada vídeo já feito.
- `creditos_esgotados_*.png/.txt` — evidência de quando o crédito acabou.
- (16/10) `worker_<sessao>_<ts>.log` — saída inteira do worker de cada tentativa (AT-12).
- (16/10) `marcas_fotos.json` — foto de entrada -> marca d'água de IA (None = limpa).
- (16/10) `hashes_videos.json` — dHash dos limpos (dedupe de vídeo); `seo_palavras_veo.json` — autocompletar do
  YouTube por tema; `sonda_contas_veo.log` — login das contas Google (1x/dia); `render.lock` — trava de render.
- `PAUSE_SYSTEM` — pausa (manual/bloqueio valem até no modo paralelo; carga só fora dele).
