# CLAUDE.md — Veo (Shorts gerados no Google Flow / Veo 3.1)

> **OBRIGATÓRIO ANTES DE MELHORAR QUALQUER VÍDEO (dona, 01/11):** rode `python D:\video-fila\aprendizado.py aprovados`,
> leia `D:\video-fila\aprendizado\PARA_IMPLEMENTAR.md` (todos os aprovados + os candidatos do tipo que você vai mexer) e
> marque cada um aplicado/reprovado. Ninguém mais implanta isso — se você pular, fica parado. Passo a passo:
> `D:\video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md`. Mexeu em LONGO? Mesma obrigação em
> `D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md` (A FAZER / JÁ FEITO / DESCARTADO — não refazer o que já está lá).

> **LEIA PRIMEIRO.** Guia de qualquer agente que abra `D:\veo`. Criado em 15/10/2026 durante a auditoria de melhorias.
> Mantenha atualizado quando o procedimento mudar.

## Leia nesta ordem

0. **`docs\CONTINUAR_DAQUI.md` — onde paramos e o que falta.** Em 16/10/2026 foram feitas as Ondas 0 e 1
   (9 das 50 melhorias, commits `a1cee7e` e `8ad167a`); a lista das pendentes, com arquivo e como fazer, está lá.
   **Cuidado: outra sessão edita `D:\manhwa-react\mr\rede.py` — veja a seção "Armadilhas" antes de abrir esse arquivo.**
1. `docs\PLANO_MELHORIAS_VEO.md` — plano de melhorias, regras antibanimento e ordem de execução (15/10/2026).
2. `docs\LEVANTAMENTO_2026-10-15.md` — como o projeto funciona hoje, estado e achados confirmados no código.
3. `beta\README.md`, `beta\ARQUITETURA.md`, `beta\LEIA_PERFIS_E_COFRE.md` (perfis do Chrome moram no cofre),
   `beta\pos_producao\GUIA_PROPAGANDA_PORTAVEL.md` e `beta\pos_producao\VO3_PROPAGANDA_ROTACAO.md`.
4. Postagem: `D:\postador-de-videos\LEIA.txt` e `D:\manhwa-react\HANDOFF_REDE.md` — a rede do manhwa-react é o
   único caminho do veo até o YouTube.
5. Regras que valem para todo projeto de vídeo da dona: `D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md`.

## O que é

Gera Shorts 9:16 de 8 s no Google Flow (modelo "Veo 3.1 - Fast") controlando um Chrome real por Playwright/CDP, em
rodízio de contas Google (`beta\contas.py`), a partir de uma foto da dona (image-to-video) e de um prompt montado por
agentes de LLM. A pós-produção (`beta\pos_producao`) acrescenta efeitos, um clipe de comercial dos produtos da dona
feito no Veo (VO3) e um card CTA de imagem. A postagem não é daqui: é do `D:\postador-de-videos` e da rede do
`D:\manhwa-react`.

## Onde está cada coisa

| Caminho | O que é |
|---|---|
| `beta\` | **a versão que roda** ("LIVE"). Git só aqui (remoto `fabricadeautomacoesia/veo-beta`). Em 16/10 entraram no `main` a Onda 0 (`a1cee7e`) e a Onda 1 (`8ad167a`), **nenhuma enviada ao GitHub**; o resto do código de ago-out continua sem commit (item BX-01 do plano) |
| `beta\validar_video.py` | o vídeo presta? (9:16, duração, áudio, decodifica, sem preto/congelado). Usado pelo porteiro do cron |
| `beta\conferir_fala.py` | o Veo falou o que foi pedido, em português? (transcrição + semelhança e cobertura) |
| `experimental\` | cópia antiga, **desativada em 12/10** (usa as mesmas portas da beta: ligar abriria Chromes vazios). Não mexer |
| `prod\` | não existe ainda (`ambientes.json`: ativar só ao promover uma versão provada) |
| `supervisor.py`, `ambientes.json` | controle dos ambientes por prioridade e recurso da máquina |
| `fotos\` | fotos antigas do dono — desde 24/10 só RESERVA: 290 de 638 com rosto reprovado saem do sorteio (`beta\logs\fotos_rosto_reprovado.json`) |
| `beta\foto_na_hora.py` | (24/10) foto do dono criada NA HORA no Flow, no cenário do vídeo, a partir das bases de fundo branco (`D:\fotos para videos\fotos\fotos base so suar se for criar uma foto nova\sem fundo retrato`; nunca a pasta "imagem base inovare frente", que tem telefone) + revisor de rosto (YuNet+SFace, `D:\hipercool-materiais\models\rosto`) + visão (texto/marca). Saída em `D:\veo\fotos_na_hora`. Desliga: `VEO_FOTO_NA_HORA=0`; rosto no porteiro: `VEO_CONFERIR_ROSTO=0`; visão: `VEO_FOTO_VISAO=0`; prazo: `VEO_FOTO_PRAZO_MIN` (15). Tudo em `docs\FOTO_NA_HORA.md` |
| Flow por HTTP nas máquinas (29/10, D30 em `D:\hipercool-materiais\tarefas complexas para fable 5.1\FABLE_DECISOES.md`) | `beta\cadeia_veo.http_remoto` (chamado em `gera_auto._gerar_nos_notebooks` antes do Playwright): nos notebooks/PC2 o vídeo é pedido ao Flow por HTTP pelo nsn_worker de lá (`D:\projeto-navegador-sem-navegador\services\veo_flow\flow_gerar.py` modo worker); o Chrome de lá só fabrica o token do reCAPTCHA e fecha em ~40-50 s (antes ~33 min). Falhou antes de pedir = Chrome como antes. Desliga: `FLOW_HTTP_REMOTO=0` (`config.py`); por conta: `contas.SEM_HTTP`. Saúde por máquina na aba "Sem navegador (HTTP)" do painel (`maquina_remota.py saude-flow`) |
| funil do Veo (24/10) | tema por Thompson no placar de 48 h (`postador\bin\notificar_telegram._placar_veo` → `_analise\placar_veo_*.json`), réplica de viral (`VEO_VIRAL_MIN` 1000 views, máx 3), bônus viral e teto da rampa na rede (`mr\rede.py`, `veo_peso_viral`) |
| `beta\cron_gerar_video_llm.py`, `agents.py`, `inteligencia.py`, `gera_auto.py`, `flow_bot.py` | geração do vídeo criativo |
| `beta\pos_producao\` | pós-produção: `montar_final.py` (orquestra), `cta_card.py`/`cta_builder.py` (card), `vo3_propaganda_rotator.py` + `comercial_agents.py` (comercial Veo), `worker_noite.py`, `plugins\` |
| `beta\videos\cron_shorts\` | brutos gerados |
| `beta\videos_pos\cron_shorts\` | saída da pós (com sidecar `.json`) |
| `beta\logs\` | `sessoes_status.json` (contas), `video_cache.json` (fórmulas/métricas), `PAUSE_SYSTEM` (pausa), `cron_gerar_llm.log` |
| `D:\hipercool-materiais\veo\` | `veo_videos_iniciais` (brutos), `limpos` (versão sem marca e sem slide, a que vai para o YouTube), `pos_final\completo` (com propaganda: **não vai para o YouTube**), `propagandas_vo3` |
| `D:\logins-google\cofre\perfis\<conta>` | perfis do Chrome das contas. As pastas `chrome_gen_*` da beta são **junções** para lá: apagar só com `rmdir`, nunca `rm -rf` |

## Ambiente

- Python: `D:\veo\venv\Scripts\python.exe` com `PYTHONUTF8=1` (os `.bat` usam este venv; o `beta\README.md` ainda
  cita o venv do hipercool, está desatualizado). ffmpeg/ffprobe: `D:\hipercool-materiais\bin\`.
- Sem gastar crédito nem abrir Chrome: `python validate.py` (sanidade), `python cron_gerar_video_llm.py sessoes`
  (estado das contas), `python contas.py` (contas). Contas: edite **só** `contas.py`.
- Um render pesado por vez na máquina.

## Ligar / pausar

- Geração (em `beta\`): `Veo_LIGAR_visivel.bat` / `Veo_LIGAR_invisivel.bat` apagam `logs\PAUSE_SYSTEM` e chamam
  `run_cron_loop_3contas.bat`; `Veo_DESLIGAR.bat` (`desligar.py`) cria `PAUSE_SYSTEM`, mata os Chromes do bot e encerra
  o loop. Na raiz: `Veo_PAINEL.bat` (supervisor) e `Veo_PAINEL_DESLIGAR.bat` (para tudo).
- Pós-produção: `Veo_POS_TUDO.bat on|off` (flags `cron_video`, `pos_video`, `cron_pos_retro`, `voz_whatsapp`),
  `Veo_POS_FLAG.bat <flag> on|off|list`, `Veo_POS_RODAR.bat [incremental|retroativo] [limite]`.
- **Estado em 22/10/2026 (substitui o de 16/10):** `beta\logs\PAUSE_SYSTEM` **não existe mais** (sumiu em 16/10)
  e o loop antigo morreu em 15/10 16:58. Quem governa gerar/limpar hoje é o **controlador geral**
  (`D:\video-fila\controlador.py`, tarefa `ControladorVideos`, a cada 10 min): Veo é prioridade 6, limpa brutos do
  Drive quando a reserva de limpos cai abaixo de 400 e SÓ gera vídeo novo com o Drive zerado e reserva < 100
  (teto 40/dia) — com 500+ limpos de reserva ele fica em repouso de propósito, mesmo "ligado". O caminho antigo
  (`AgendadorVO3`/etapas 1-2 do `postar_tudo_auto.bat`) foi desarmado em 16/10 à noite. **Atenção:** o MS Energy
  gera pelas MESMAS contas do Flow de madrugada e costuma esgotar o crédito (~02:00); o botão `Veo_DESLIGAR.bat`
  (PAUSE_SYSTEM) segura só o cron do veo — o controlador não o conhece (pendência VEO-06 de 22/10).

## Regras (da dona; não negociáveis)

- **Nunca postar vídeo do veo direto no YouTube.** Só pela rede do manhwa-react (`manhwareact.py rede`), na versão
  LIMPA (`D:\postador-de-videos\bin\limpar_veo.py`), com aprovação e 1 vídeo por canal por dia. Não religar
  `postar_tudo_hoje.py`, `agendar_vo3.py` nem `beta\roteamento.py` para o veo (apontam para canais suspensos).
- **Nada de número de WhatsApp, slide de produto nem cartão "Siga @…" no corte que vai ao YouTube**: foi o que
  derrubou os canais antigos em 04/09/2026. COMPLETO nunca como limpo. Nunca repostar os 730 de `pos_final`.
- Nunca o mesmo vídeo em 2 canais. Metadados únicos por vídeo (sem "#shorts #ia #viral" por template, sem telefone na
  descrição). Declarar "conteúdo alterado ou sintético" no upload (a pessoa que fala é gerada): o postador já tem
  `--sintetico`; quem chama precisa pedir.
- Nunca engajamento falso (likes/comentários por bot). Google/YouTube só pelo navegador; nunca criar nem pedir chave
  de API no Google Cloud.
- Voz edge **proibida**: `pt-BR-AntonioNeural` (Francisca e Isabella liberadas pelo dono em 16/10; Francisca = base da voz clonada).
  (22/10: o Antonio JÁ está em PROIBIDAS no `beta\pos_producao\edge_tts_veo.py` — corrigido; a lista de lá ainda
  proíbe Francisca/Isabella da regra velha, atualizar quando mexer no arquivo.)
  Voz fixa por produto/personagem, sorteada por md5, nunca por `hash()`.
- Tarefa agendada não pode abrir janela de console (`sem_janela.py` do hipercool/manhwa-react).
- Segredos (cofre, `beta\secrets`, `beta\sessions`, chaves) nunca no git, no chat ou em documento.
- Commit/push e qualquer postagem real só com confirmação da dona.
- Teste a seco (`beta\teste_cadeia_a_seco.py`) roda o `cron.run()` de verdade: sempre com `VEO_FOTO_NA_HORA=0` e
  `VEO_CONFERIR_ROSTO=0` (já estão no arquivo), senão abre o Flow pra gerar foto.
- Validar de verdade antes de dizer "pronto": ffprobe (bom = h264 720x1280 8 s + aac; `mjpeg 512x512` sem áudio =
  Nano Banana, jogar fora), quadros extraídos e vistos, log. ffprobe não ouve o idioma: a fala em pt-BR se confere
  com transcrição ou de ouvido.
- Não mexer no PC2 nem nos projetos Atlas, Lucrativa e MS Energy.
- Desktop (desktop-su00b7v, 100.73.7.19): Windows SEM SENHA desde 24/10/2026; acesso só por chave
  (`ssh -o BatchMode=yes desktop`), nunca usar/pedir senha; chave recusada = avisar o dono. Ocupado com OBS ou chamada.
- A dona escreve em português com erros de digitação e quer resposta direta, em português do Brasil.

## Registro do progresso

Terminou um item do plano? Marque no `docs\PLANO_MELHORIAS_VEO.md` (seção "Registro") com data e o que foi validado.
Mudou procedimento, caminho ou botão? Atualize este arquivo.
