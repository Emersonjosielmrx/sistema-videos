# Bot Veo/Flow — gerador automático de vídeos 9:16

Gera vídeos curtos (9:16, com áudio) no **Google Flow / Veo 3.1** de forma
automática, controlando o Chrome via Playwright (CDP). Roda em rodízio entre
várias contas Google, detecta quando uma conta fica sem crédito e pula pra
próxima sozinho.

> **Regra de ouro:** pra mexer em **contas**, edite **só `contas.py`**.
> Depois de qualquer mudança, rode `python validate.py`.

---

## TL;DR — ligar / parar / ver

Sempre com `PYTHONUTF8=1` (o console Windows quebra em acento sem isso).
O Python é o do venv do veo: `D:/veo/venv/Scripts/python.exe` (corrigido em 16/10; o de
`D:/hipercool-videos` não é este). Antes de mexer: `D:\veo\CLAUDE.md`, `D:\veo\docs\CONTINUAR_DAQUI.md` e
depois de mexer `python validate.py` (imports, contas e comportamentos).

**LIGAR** (produção, loop infinito de 3 contas):
```
run_cron_loop_3contas.bat
```
Ele fica rodando ciclo após ciclo. O rodízio de conta é automático (no código).

**PARAR:** feche a janela do `.bat` (ou Ctrl+C nela). Isso para só o loop —
não mata nada mais.

**VER O QUE ESTÁ RODANDO** (status de cada conta: ativa / em cooldown /
sem crédito):
```
python cron_gerar_video_llm.py sessoes
```

**CHECAR SE ESTÁ TUDO SÃO** (sem gastar crédito/Chrome):
```
python validate.py
```

**VER AS CONTAS CONFIGURADAS:**
```
python contas.py
```

---

## Onde ficam as coisas

| O quê | Caminho |
|---|---|
| Vídeos gerados | `videos/cron_shorts/` |
| Log principal | `logs/cron_gerar_llm.log` |
| Estado das contas (cooldown / EXHAUSTED) | `logs/sessoes_status.json` |
| Evidência de crédito esgotado (print + txt) | `logs/creditos_esgotados_*.png/.txt` |
| Perfis Chrome (login de cada conta) | `chrome_gen_<conta>/` |

---

## Arquivos que importam

Veja **ARQUITETURA.md** pro fluxo completo. Resumo:

| Arquivo | Pra quê |
|---|---|
| `contas.py` | **FONTE ÚNICA das contas.** Edite aqui. |
| `creditos.py` | Detecta "acabou o crédito" na página do Flow. |
| `cron_gerar_video_llm.py` | Orquestrador: escolhe conta, dispara worker, failover. |
| `loop_cron.py` | Loop infinito que chama o orquestrador. |
| `gera_auto.py` | Worker: abre o Flow, escreve prompt, baixa o mp4. |
| `flow_bot.py` | Camada baixa de Playwright (cliques, seletores). |
| `agents.py` + `llm_client.py` | Pipeline de LLM (ideia, roteiro, crítica). |
| `validate.py` | Smoke test (rode após mexer em contas/imports). |

Ferramentas avulsas de linha de comando ficam em **`tools/`**
(`upload_client.py`, `tts_client.py`, `trends_client.py`) — não fazem parte
do loop de produção.

Scripts antigos de diagnóstico/teste foram movidos pra **`_LIXO_2026-07-26/`**.
Se algo quebrou e você suspeita de um deles, estão lá (nada é apagado de cara).

---

## Guias passo a passo

- **TUTORIAL_AGENTE.md** — "não está gerando vídeo, e agora?", como ver
  crédito, como limpar estado travado.
- **TUTORIAL_NOVA_CONTA.md** — adicionar uma conta Google nova.
