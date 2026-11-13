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
   de volta no orquestrador: thumbnail_client + metrics_client + cache
```

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
