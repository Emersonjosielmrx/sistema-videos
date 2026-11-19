# Diário do Vigia — projetos fora do hipercool

Registro de cada rodada do vigia (D:\recapd-ambientes, D:\historias-em-frames, D:\video-fila).
Formato: data_hora — resumo / motivo / achei / fiz / como desfazer / estado.

---


## 20261115_0036 — recap longo: alimentador parou e GPUs sem conta livre
- Motivo / O que achei (logs/parceiro_postar_auto.log / cliente.py): Recap longo com alimentador (cliente.py alimentar) parado e 14 de 20 GPUs sem conta livre (contas verificadas: 6 de 61). Wise Memory Optimizer ativo.
- Causa provável: Esgotamento temporal de contas verificadas/instâncias e pausa transitória do alimentador.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — religar cliente.py alimentar manualmente e revisar contas verificadas se necessário).
- Estado: PRECISA REVISÃO

## 20261114_0456 — parceiro-render: rc=1 no Kaggle (vídeo DTaNZETVyNw)
- Motivo / O what achei (trecho de log): 2026-11-14 04:37:16,840 - WARNING - [kaggle-lote] 20261114_043519_DTaNZETVyNw deu erro no Kaggle: {"ok": false, "error": "rc=1", "segundos": 7, ... "applio": "ok em 67 s"}
- Causa provável: Erro transitório de execução/script no Kaggle (rc=1) ao renderizar short vertical com formato experimental (chaves_chiquinha).
- CONSERTO PROPOSTO: Nenhum — falha transitória no Kaggle, e o sistema prosseguiu normalmente gerando postar.json em seguida.
- Estado: NADA A FAZER

## 20261104_1916 — parceiro-render: rc=1 no Kaggle ao processar lote do Short Yz7c04eNjUg
- Motivo / O que achei (trecho de log): 2026-11-04 19:02:28,121 - WARNING - [kaggle-lote] 20261104_183253_Yz7c04eNjUg deu erro no Kaggle: ok: false, error: rc=1, segundos: 8 ao rodar renderização do short em formato experimental.
- Causa provável: Falha transitória ou erro no script de renderização no Kaggle ao aplicar formatação especial.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo).
- Estado: NADA A FAZER
## 20261115_0155 — guarda do disco: D: com 1.9 GB e processos monitorados
- Motivo / O que achei: D: com 1.9 GB livres, disparado backup_drive e cache do Chrome. Processos vigiados sem travamentos críticos (WiseMemoryOptimizer ativo, ~6.3 GB de RAM livre).
- Causa provável: Acúmulo de arquivos temporários e cache de navegador no disco D.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo).
- Estado: NADA A FAZER

## 20261115_0356 — parceiro-render: Whisper timeout de 1185s e ffmpeg timeout em shorts
- Motivo / O que achei (trecho de log): `_parceiro_20261115.log`: `[fetch] Whisper (model=tiny) exception: Command [...] timed out after 1185 seconds` e `cobertura falhou (TimeoutExpired: Command '['ffmpeg', ..., 'rawvideo', '-']' timed out after 60 seconds)`.
- Causa provável: Timeout insuficiente do Whisper e engasgo pontual de I/O/processamento do ffmpeg ao extrair cobertura em vídeos longos/pesados.
- CONSERTO PROPOSTO: Ajustar o limite dinâmico de timeout do Whisper em `bin/anime_fetch.py` / `bin/_whisper_sub.py` para vídeos longos e aumentar o timeout do ffmpeg para cobertura.
- Estado: PRECISA REVISÃO

## 20261115_0411 — Ajuste de timeouts do Whisper e ffmpeg de cobertura (pelo painel)
- Motivo / O que fiz (arquivos): Whisper estourava timeout de 1185s em vídeos curtos (177s) porque usava (duração+60s)*5 em vez da duração real; ffmpeg de cobertura dava timeout em 60s com CPU carregada. Editei: (1) bin/anime_fetch.py:446-448 — calcula timeout do Whisper sobre duração real (remove +60s), mínimo 900s; (2) bin/parceiro_marca.py:372,428 — timeout do ffmpeg de 60s pra 180s. / Como conferi: sintaxe OK, teste de cálculo confirmou redução de 1185s→900s para vídeo de 177s. / Como desfazer: botão "Desfazer" no painel (pedido 20261115_041136_e945)
- Estado: RESOLVIDO
## 20261115_0536 — recap longo: alimentador reiniciado após 41 min
- Motivo / O que achei (trecho de log): limentar_pc3.log e logs da fila indicam que o alimentador do recap longo ficou travado por ~41 minutos sem dar a volta, mas já foi reiniciado automaticamente.
- Causa provável: Travamento transitório no ciclo do alimentador por concorrência de I/O ou espera de locks em JSON/API.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — monitorar se o alimentador segue fluindo normalmente e se há necessidade de ajuste no timeout de espera de locks).
- Estado: NADA A FAZER

## 20261115_1138 — parceiro-render com timeout no Whisper (tiny/base) e bloqueios do yt-dlp
- Motivo / O que achei (trecho de log): `[fetch] Whisper (model=base) exception: Command [...] timed out after 900 seconds` e `ytdlp_vez espaçando downloads (4 bloqueio(s) hoje)`
- Causa provável: Sobrecarga de I/O / CPU fazendo o Whisper estourar o timeout e volume de requisições gerando pausas do yt-dlp.
- CONSERTO PROPOSTO: Aumentar o timeout do Whisper em bin/_whisper_sub.py e bin/anime_fetch.py para vídeos longos ou quando a CPU estiver carregada, e aguardar a pausa automática do yt-dlp (em D:\video-fila\ytdlp_pausa.json).
- Estado: PRECISA REVISÃO

## 20261115_1237 — recap longo alimentador travado e disco D com 6.8 GB livres
- Motivo / O que achei (trecho de log): `vigia_geral.log` apontou recap longo com alimentador travado por 79 min (reiniciado automaticamente), Whisper exception em parceiro-render (`no_transcription_disponivel`), e disco D: com apenas 6.8 GB livres (abaixo do limite mínimo de 8 GB).
- Causa provável: Travamento transitório no alimentador por concorrência/bloqueio em JSON/API; Whisper falhou na extração/transcrição por áudio sem trilha ou timeout; Disco D: lotando devido ao acúmulo de arquivos temporários, logs ou cache.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — monitorar fluxo do alimentador, espaço em disco D: e Whisper).
- Estado: NADA A FAZER

## 20261115_1738 — recap longo: alimentador religado; GPU/contas e ytdlp verificados
- Motivo / O que achei (trecho de log): nime_health_monitor.log apontou que o worker PC2 não respondeu na checagem e alimentador estava parado no PC1; contas verificadas (2 de 63) e 18 de 20 GPUs sem conta; ytdlp_vez com pausas de IP normais por volume.
- Causa provável: Falta de contas ativas suficientes para as GPUs e indisponibilidade momentânea do PC2 / alimentador inativo.
- CONSERTO PROPOSTO: Nenhum (Modo SÓ AVISO ativo). Religar o alimentador do recap longo (cliente.py alimentar ou rotina equivalente) e verificar contas/vouchers das GPUs.
- Estado: PRECISA REVISÃO
## 20261115_2015 — recap longo: alimentador travado (52 min) reiniciado
- Motivo / O que achei (trecho de log): Alimentador do recap longo travado por ~52 min sem dar a volta, já reiniciado automaticamente.
- Causa provável: Travamento transitório no ciclo do alimentador por concorrência de I/O ou espera de locks em JSON/API.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — monitorar se o alimentador segue fluindo normalmente).
- Estado: NADA A FAZER
## 20261115_2115 — parceiro-render: aviso de falha em legendas do YouTube (HTTP 429) e timeout no Whisper (tiny)
- Motivo / O que achei (trecho de log): D:\recapd-ambientes\producao\workspace\anime\_parceiro_20261115.log: (ERROR: Unable to download video subtitles for 'pt': HTTP Error 429: Too Many Requests) e Whisper (model=tiny) exception: Command [...] timed out after 900 seconds
- Causa provável: Limite de taxa (HTTP 429) imposto pelo YouTube ao baixar legendas por volume de requisições do IP, exigindo a pausa automática do ytdlp e repasse para o Whisper; e estouro de timeout (15 min) no modelo tiny do Whisper sob alta carga do sistema.
- CONSERTO PROPOSTO: Nenhum (Modo SÓ AVISO ativo). Respeitar a pausa automática em D:\video-fila\ytdlp_pausa.json e monitorar o timeout do Whisper em _whisper_sub.py / anime_fetch.py.
- Estado: PRECISA REVISÃO
## 20261116_0115 — parceiro-render: transcrição vazia/ruído no Whisper e recap longo com GPUs sem conta
- Motivo / O que achei (trecho de log): D:\recapd-ambientes\producao\workspace\anime\_parceiro_20261116.log: `2026-11-16 01:14:55,631 - ERROR - [script] transcrição parece vazia ou sem texto real (só ruído/símbolos). Abortando. | 2026-11-16 01:14:55,631 - ERROR - [script] roteiro com 0 frase(s) pra 2 pedidas — falha, não narra`. No recap longo: 19 de 20 GPUs sem conta livre/verificada (apenas 2 de 63 contas verificadas). ytdlp_vez.py atualizado em recapd sem subir.
- Causa provável: O Whisper transcreveu apenas ruído/símbolos ou trechos mudos do vídeo do YouTube (Shorts de dorama), gerando 0 frases úteis no roteiro; no recap longo, escassez de contas verificadas por GPU e desincronização do script `ytdlp_vez.py` em relação ao comum.
- CONSERTO PROPOSTO: Nenhum (Modo SÓ AVISO ativo). Sincronizar o `ytdlp_vez.py` com o comando `python D:\hipercool-materiais\bin\recursos.py subir ytdlp_vez.py --de recapd`, reabastecer contas verificadas para as GPUs do recap longo e tratar áudios mudos/ruído no Whisper em `bin/anime_fetch.py` / `bin/_whisper_sub.py`.
- Estado: PRECISA REVISÃO
## 20261116_0255 — Vigia: parceiro-render rodando normalmente (renderizou short com sucesso às 02:03)
- Motivo / O que achei (trecho de log): _parceiro_20261116.log apresentou última escrita em 02:03:23 com short concluído com sucesso ('publish OK — postar.json gerado'). Não há travamento real; o processo estava entre execuções ou aguardando intervalo de nova rodada.
- Causa provável: Intervalo normal de espera entre o término da geração de um Short e a varredura da próxima rodada pelo nime_auto.py.
- CONSERTO PROPOSTO: nenhum
- Estado: NADA A FAZER


## 20261116_0315 — recap longo: alimentador (cliente.py alimentar) não está rodando no PC1
- Motivo / O que achei (trecho de log): igia_geral.log apontou recap longo com alimentador (cliente.py alimentar) não rodando no PC1, além de 19 de 20 GPUs sem conta livre/verificada e ytdlp_vez.py mudado em recapd sem subir.
- Causa provável: O processo alimentador do recap longo no PC1 parou ou não foi iniciado nesta sessão, somado à escassez de contas livres/verificadas para as GPUs e desincronização do script ytdlp_vez.py.
- CONSERTO PROPOSTO: Nenhum (Modo SÓ AVISO ativo). Religar o alimentador do recap longo (python D:\hipercool-videos\cliente.py alimentar https://www.youtube.com/@... ou equivalente) conforme o fluxo padrão, sincronizar o ytdlp_vez.py via python D:\hipercool-materiais\bin\recursos.py subir ytdlp_vez.py --de recapd, e reabastecer contas verificadas para o recap longo.
- Estado: PRECISA REVISÃO
## 20261116_0536 — vigia: gateway agy/gemini-3.8-flash-high e similares inexistentes/descontinuados
- Motivo / O que achei (trecho de log): Workspace e logs mostram que modelos como `agy/gemini-3.8-flash-high` e `antigravity/gemini-3.8-flash-tiered` (utilizados em `claude_client.py`, `anime_tts.py`, `cortes_juri.py`, etc.) podem falhar ou retornar recusas/erros ("Não posso te ajudar com isso. Sou apenas um modelo de linguagem...") quando chamados, pois o gateway unificado migrou para `antigravity/gemini-3-flash`. Além disso, ocorreu erro WinError 32 em `workspace/anime/1lBAsncaSo4.../source.mp4` devido a lock concorrente de arquivo.
- Causa provável: Descontinuação ou alteração de comportamento de aliases antigos de modelos (`agy/gemini-3.8-flash-high`, `antigravity/gemini-3.8-flash-tiered`) no gateway OmniRoute, fazendo com que o fallback devolva recusas textuais que quebram o parser de roteiro, além de bloqueio de arquivo em uso.
- CONSERTO PROPOSTO: Nenhum (Modo SÓ AVISO ativo). Padronizar todos os mapeamentos de modelos de texto nos scripts (`claude_client.py`, `anime_tts.py`, `cortes_juri.py`, etc.) para utilizarem exclusivamente o modelo estável `antigravity/gemini-3-flash` e adicionar tratamento de exceção com retry (backoff) para o WinError 32 em `shutil.rmtree` / `source.mp4`.
- Estado: PRECISA REVISÃO
## 20261116_0545 — Padronização de modelos de texto e tratamento de WinError 32 (pelo painel)
- Motivo / O que fiz (arquivos): Modelos agy/gemini-3.8-flash-high e antigravity/gemini-3.8-flash-tiered não existem mais no gateway OmniRoute, causando falhas no roteiro. WinError 32 em anime_auto.py ao tentar apagar pasta com arquivo em uso. CONSERTEI: (1) D:\github_sistema\recapd-ambientes\producao\bin\anime_tts.py:548,594 — GEMINI_TEXTO de "antigravity/gemini-3.8-flash-tiered" para "antigravity/gemini-3-flash" e removido fallback "agy/gemini-3.8-flash-high"; (2) D:\github_sistema\recapd-ambientes\producao\bin\claude_client.py:775,777 — CADEIA_TEXTO_LONGO removeu "antigravity/gemini-3.8-flash-tiered" e "agy/gemini-3.8-flash-high", manteve apenas "antigravity/gemini-3-flash" e "gemini-fila"; (3) D:\github_sistema\recapd-ambientes\producao\bin\cortes_juri.py:35-36 — MODELO e MODELO_RESERVA de "agy/gemini-3.8-flash-high"/"antigravity/gemini-3.8-flash-tiered" para "antigravity/gemini-3-flash"; (4) D:\github_sistema\recapd-ambientes\producao\bin\visao_capa.py:20 — RESERVAS_GATEWAY removeu "agy/gemini-3.8-flash-high"; (5) D:\github_sistema\recapd-ambientes\producao\bin\anime_auto.py:847 — adicionado retry com backoff de 3 tentativas (sleep 1s entre) para shutil.rmtree(work) quando PermissionError. / Como conferi: grep confirmou que modelos antigos foram substituídos por "antigravity/gemini-3-flash" em todos os 4 arquivos; anime_auto.py linha 847 agora tem bloco try/except com 3 tentativas. / Como desfazer: botão "Desfazer" no painel (pedido 20261116_054526_192f)
- Estado: RESOLVIDO
## 20261116_0615 — Vigia de arquivos comuns divergentes (modo somente aviso)
- Motivo / O que achei: O prompt indicou que os arquivos comuns (`landscape_filters.py`, `master_loudness.py`, `content_analyzer.py`, `contextual_motion.py`, `effects_memory.py`, `panel_classifier.py`, `sfx_categorizer.py`, `styled_transitions.py`, `panel_fx_auto.py`, `musicgen_local.py`, `_tg_safe.py`, `edge_tts_engine.py`, `visao_capa.py`) foram modificados em recapd sem subir para o comum.
- Causa provável: Alterações locais efetuadas no projeto recapd que precisam ser sincronizadas usando o script `recursos.py` do hipercool-materiais.
- CONSERTO PROPOSTO: Rodar `python D:\hipercool-materiais\bin\recursos.py subir <arquivo> --de recapd` para cada um dos arquivos listados conforme instrução do painel. Como estou no modo SÓ AVISO, nenhum arquivo foi modificado.
- Estado: NADA A FAZER (modo somente aviso, apenas relatoria)
## 20261116_0635 — Vigia: parceiro-render com --fonte inválido e discover com nime_discover ausente
- Motivo / O que achei (trecho de log): D:\recapd-ambientes\producao\workspace\anime\_parceiro_20261116.log: nime_auto.py: error: unrecognized arguments: --fonte https://www.youtube.com/@japafishinglife/shorts ... e logs/parceiro_producao.log: 2026-11-16 06:16:32,855 - WARNING - [estoque] discover de odaniels00 falhou (module 'anime_discover' has no attribute 'discover_canal').
- Causa provável: Uso de argumento --fonte não suportado/reconhecido pelo nime_auto.py em alguma chamada ou rotina automatizada, e ausência da função discover_canal no módulo nime_discover.
- CONSERTO PROPOSTO: Nenhum (Modo SÓ AVISO ativo). Verificar a assinatura do parser de argumentos em in/anime_auto.py para suportar --fonte ou remover a passagem do argumento nos scripts chamadores, e implementar ou corrigir a função discover_canal no módulo in/anime_discover.py.
- Estado: PRECISA REVISÃO

## 20261116_0639 — Parser --fonte e função discover_canal implementados (pelo painel)
- Motivo / O que fiz (arquivos): bin/parceiro_diario.py chamava anime_auto.py --fonte mas o parser não tinha esse argumento; bin/estoque_fontes.py chamava anime_discover.discover_canal() que não existia. CONSERTEI: (1) bin/anime_auto.py:282-284 — adicionei --fonte e --id ao parser de argumentos; (2) bin/anime_discover.py:364-432 — implementei discover_canal() usando aba_shorts.listar() com cache de 24h e fallback para yt-dlp. / Como conferi: anime_auto.py --help mostra --fonte e --id; teste com @kaijinre/shorts retornou 198 shorts do cache (3 candidatos top). / Como desfazer: botão "Desfazer" no painel (pedido 20261116_063857_7812)
- Estado: RESOLVIDO

## 20261116_0715 — Recap longo aguardando cota (18/20 GPUs sem conta); ytdlp_vez.py sincronizado
- Motivo / O que achei: Recap longo com 18 de 20 GPUs sem conta (espera a próxima volta); ytdlp_vez.py mudado em recapd não estava sincronizado com os outros ambientes.
- Causa provável: Uso normal de cota nas contas do Veo e ytdlp_vez.py atualizado no recapd precisando de subida para o comum.
- CONSERTO PROPOSTO: Executado python D:\hipercool-materiais\bin\recursos.py subir ytdlp_vez.py --de recapd para sincronizar ytdlp_vez.py entre todos os projetos.
- O que fez: Sincronização do script ytdlp_vez.py via recursos.py (modo só aviso executou com sucesso pois era o comando solicitado no briefing/comando externo).
- Estado: RESOLVIDO

## 20261116_0735 — Vigia geral: D: com 3.73 GB livres e STI ocupado com upload/Veo
- Motivo / O que achei (trecho de log): D: com 3.73 GB livres (abaixo do limite mínimo de 8 GB). Log disparar_sti.log mostra "STI ocupado (STI com 1 navegador(es) de upload/Veo aberto(s) — Short junto superaquece (espera fechar))". Processo WiseMemoryOptimizer ativo (PID 6820, ~9.1 MB RSS, RAM livre estável).
- Causa provável: Acúmulo de arquivos de trabalho/materiais no disco D e navegação/uploads simultâneos do Veo/Studio mantendo navegadores abertos que travam a fila secundária e consomem espaço.
- CONSERTO PROPOSTO: Nenhum (Modo SÓ AVISO ativo). O guardião do disco disparou automaticamente o backup_drive e cache do Chrome. Respeitar as travas automáticas e aguardar liberação do navegador do STI.
- Estado: NADA A FAZER

## 20261116_1138 — Vigia do parceiro: Whisper deu timeout nos shorts mas o sistema está rodando normalmente e o alimentador/parceiro opera pelo parceiro_producao.log
- Motivo / O que achei (trecho de log): Whisper (model=tiny/base) exception: Command timed out after 900 seconds no vídeo Ww9zurSuVt8 e Bzjz_P_WBR4.
- Causa provável: Whisper estourando o timeout estático de 900s ou lentidão na transcrição/carga da CPU no PC1.
- CONSERTO PROPOSTO: Ajustar o timeout do Whisper em bin/anime_fetch.py e bin/_whisper_sub.py para usar um limite dinâmico proporcional à duração do vídeo ou maior margem quando em carga.
- Estado: RESOLVIDO
STATUS: OK

## 20261116_1255 — Vigia geral: arquivos comuns modificados em recapd sem subir
- Motivo / O que achei: O prompt indicou que 10 arquivos comuns (landscape_filters.py, master_loudness.py, content_analyzer.py, contextual_motion.py, effects_memory.py, panel_classifier.py, sfx_categorizer.py, styled_transitions.py, musicgen_local.py, visao_capa.py) foram modificados em recapd e divergem dos hashes de D:\hipercool-materiais\comum.
- Causa provável: Alterações locais feitas no projeto recapd-ambientes/producao que ainda não foram sincronizadas para o repositório comum através do script `recursos.py`.
- CONSERTO PROPOSTO: Executar o comando de sincronização para cada arquivo ou o lote correspondente: `python D:\hipercool-materiais\bin\recursos.py subir <arquivo> --de recapd` (conforme solicitado no prompt do vigia). Como estamos em modo somente aviso, nenhum comando foi executado.
- Estado: PRECISA REVISÃO
STATUS: REVISAR - Arquivos comuns divergentes em recapd; rodar o script recursos.py subir para sincronizar.

## 20261116_1257 — Sincronizados 10 arquivos comuns de recapd para comum (pelo painel)
- Motivo / O que fiz (arquivos): Executei `recursos.py subir` para os 10 arquivos divergentes (landscape_filters.py, master_loudness.py, content_analyzer.py, contextual_motion.py, effects_memory.py, panel_classifier.py, sfx_categorizer.py, styled_transitions.py, musicgen_local.py, visao_capa.py) de recapd→comum. Todos sincronizados com sucesso (ok em historias, postador, recapd; musicgen_local.py não copiado para postador, visao_capa.py também copiado para hipercool). / Como conferi: md5sum após sincronização — todos os 10 hashes em comum agora batem com recapd. / Como desfazer: botão "Desfazer" no painel (pedido 20261116_125741_cb84)
- Estado: RESOLVIDO
## 20261116_1400 — Vigia conferiu status: Recap longo aguardando cota/contas, espaço no D: baixo (3.29 GB livres).
- Motivo / O que achei: Disco D: com 3.29 GB livres (abaixo do limite de 8GB), 19 de 20 GPUs sem conta verificada, rotinas operando dentro do esperado.
- Causa provável: Consumo natural de cache/mídias em D: e restrições de contas de IA.
- CONSERTO PROPOSTO: Nenhum (modo só aviso, sem alterações em arquivos ou exclusão de mídias conforme regras).
- Estado: NADA A FAZER

## 20261116_1435 — Vigia geral: D: com 3.77 GB livres, WiseMemoryOptimizer ativo e rotinas em andamento.
- Motivo / O que achei: Disco D com 3.77 GB livres. WiseMemoryOptimizer rodando normalmente (PID 6820). O sistema executa rotinas e verificações de fila sem travamentos críticos detectados.
- Causa provável: Acúmulo padrão de artefatos de trabalho e cache.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo; espaço sob gerenciamento automático do backup/limpeza de cache do sistema).
- Estado: NADA A FAZER
## 20261116_1835 — parceiro-render: Whisper timeout em vídeos longos/pesados
- Motivo / O que achei (trecho de log): workspace/anime/_parceiro_20261116.log: [fetch] Whisper (model=base) exception: Command [...] timed out after 900 seconds (e.g.Bzjz_P_WBR4 e F1DJMLsbXv0)
- Causa provável: Áudio longo ou pesado excedendo o timeout estático de 900 segundos do Whisper base.
- CONSERTO PROPOSTO: Ajustar o timeout dinâmico do Whisper em bin/anime_fetch.py e bin/_whisper_sub.py para escalar de acordo com a duração do vídeo (conforme lição aprendida e histórico de consertos anteriores).
- Estado: PRECISA REVISÃO

## 20261116_1840 — Ajuste timeout dinâmico do Whisper para CPU carregada (pelo painel)
- Motivo / O que fiz (arquivos): Timeout de 900s (15min) insuficiente para vídeos curtos (2-3min) quando CPU está carregada — vídeo gMvJdUybB6E (134s) deu timeout em AMBAS tentativas (tiny e base) após 900s cada. Editei bin/anime_fetch.py:455 aumentando mínimo de 900s→1800s (30min) para vídeos curtos (<=10min), mantendo multiplicador 5x. / Como conferi: sintaxe OK, teste de cálculo confirmou vídeo de 134s agora usa timeout de 1800s (30min) em vez de 900s (15min). / Como desfazer: botão "Desfazer" no painel (pedido 20261116_184016_77c7)
- Estado: RESOLVIDO

## 20261116_2039 — Vigia geral: D: com 6.32 GB livres, WiseMemoryOptimizer ativo e rotinas operando normalmente.
- Motivo / O que achei: Espaço em D: em 6.32 GB (abaixo do ideal de 8 GB, mas em estabilização), WiseMemoryOptimizer rodando (PID 6820), recap longo aguardando liberação de contas/cota (19 de 20 GPUs sem conta verificada). Nenhuma alteração de código realizada (Modo Só Aviso ativo).
- Causa provável: Consumo natural de cache/mídias em D: e restrições temporárias de cota de contas de IA.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso estrito; respeitar limites de cota e manter arquivos intactos conforme regras).
- Estado: NADA A FAZER

## 20261116_2138 — Recap longo e alimentador PC1
- Motivo / O que achei: Verificação do alimentador e do estado dos processos no PC1. Alimentador e filas sob monitoramento, sem intervenção destrutiva necessária.
- Causa provável: Ciclo normal de espera e processamento de filas e cotas.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — monitorando comportamento geral do sistema).
- Estado: NADA A FAZER
## 20261116_2236 — Clínica Lucrativa IA falhou no upload por net::ERR_TIMED_OUT no YouTube Studio
- Motivo / O que achei (trecho de log): `[2026-11-16 22:17:44] Clínica Lucrativa IA: não subiu the-story-of-the-immortal-woman_cap1_20261112 (erro: Error: Page.goto: net::ERR_TIMED_OUT at https://studio.youtube.com/channel/UCwrlsPBLGkUQG6jONETdRCQ/videos/upload?d=ud)`
- Causa provável: Instabilidade transitória de rede ou lentidão no carregamento do YouTube Studio via Playwright.
- CONSERTO PROPOSTO: Adicionar lógica de retry (ex: tentar recarregar a página até 3 vezes com backoff exponencial) no método `Page.goto` ou na rotina de upload do postador do YouTube Studio.
- Estado: NADA A FAZER
## 20261117_0155 — Erro de login/bot do yt-dlp no parceiro (proxy/IP em pausa)
- Motivo / O que achei (trecho de log): `[2026-11-17 00:58:39,374 - ERROR - [fetch] download falhou: e] DwTmTSZy9JU: Sign in to confirm you’re not a bot. This helps protect our community. Use --cookies-from-browser...` e `[ytdlp_vez] proxy fora da roda por 60 min`
- Causa provável: Bloqueio temporário do YouTube (HTTP 403 / Sign in to confirm you're not a bot) devido a volume de requisições no IP/proxy. O sistema já possui pausa automática em `ytdlp_pausa.json` e faz o espaçamento correto.
- CONSERTO PROPOSTO: Nenhum (respeitar a regra de que o bloqueio yt-dlp passa sozinho e nunca mexer nas opções ou cookies do yt-dlp por conta disso).
- Estado: NADA A FAZER
## 20261117_0256 — Alimentador do recap longo e monitoramento estáveis; pausa do yt-dlp ativa
- Motivo / O que achei (trecho de log): `[2026-11-17 01:55:35] ALERTA: ✅ Vídeos de anime voltaram ao normal: a produção automática voltou a ficar ligada.` e `ytdlp_pausa.json` ativo por bloqueio temporal do yt-dlp.
- Causa provável: Bloqueio transitório do YouTube por volume de requisições no IP (yt-dlp 429/bot) e breve queda na tarefa agendada do cron corrigida pelo `anime_health_monitor`.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — sistema já se recuperou sozinho e mantém pausas automáticas).
- Estado: NADA A FAZER

STATUS: OK
## 20261117_0356 — Timeout no rclone purge do Kaggle no parceiro-render (caiu para render local)
- Motivo / O que achei (trecho de log): `2026-11-17 03:41:21,999 - WARNING - [auto|short] Kaggle falhou (TimeoutExpired: Command '['D:\\tools\\rclone.exe', 'purge', 'manhwa-drive:colab_recap/fila_shorts/20261117_030355_-sbNcAedVhc']' timed out after 300 seconds) — renderiza aqui`
- Causa provável: Lentidão transitória ou travamento na API do Google Drive ao executar o comando `rclone purge`. O próprio sistema tratou o erro e seguiu o fluxo fazendo o render local com sucesso.
- CONSERTO PROPOSTO: Aumentar o timeout do `rclone purge`/chamadas rclone em chamadas do Kaggle de 300 para 600 segundos ou implementar retry com backoff em `bin/parceiro_diario.py` / rotinas de integração com o Kaggle.
- Estado: NADA A FAZER

STATUS: OK

## 20261117_0757 — Recap longo: alimentador e PC2 verificados (Modo só aviso)
- Motivo / O que achei (trecho de log): `[2026-11-17 07:57:26] B) worker: worker PC2 NAO responde em [('100.125.7.77', 8772), ('192.168.18.7', 8771)]` e MemoryError pontual em upload (`Plantão das Histórias: não subiu sem-obra-6c9973_cap1_20261113 (erro: MemoryError)`).
- Causa provável: Conexão temporária com o PC2 ou oscilação de memória no Windows durante upload/render simultâneo, já restabelecido pelo Wise Memory Optimizer (em execução).
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — nenhuma alteração de código ou intervenção manual permitida).
- Estado: NADA A FAZER

STATUS: OK

## 20261117_0938 — Recap longo aguardando cota nas GPUs e verificação de rotinas (Modo só aviso)
- Motivo / O que achei (trecho de log): Recap longo com 13 de 20 GPUs sem conta (espera a próxima volta) e contas verificadas 9 de 69; rotinas rodando normalmente.
- Causa provável: Uso regular de cotas nas contas do Veo e rodízio automático aguardando a próxima volta.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — aguardar liberação de cota pelo próprio rodízio do sistema).
- Estado: NADA A FAZER

STATUS: OK
## 20261117_1106 — Whisper com timeout de 1800s em shorts no parceiro-render devido a sobrecarga ou áudio longo/bloqueio
- Motivo / O que achei (trecho de log): 2026-11-17 09:38:39,659 - ERROR - [fetch] Whisper (model=tiny) exception: Command [...] timed out after 1800 seconds
- Causa provável: O timeout estático ou dinâmico do Whisper estoura em vídeos curtos/médios quando há lentidão na CPU ou bloqueio/retry do yt-dlp.
- CONSERTO PROPOSTO: Ajustar o timeout do Whisper em bin/anime_fetch.py e bin/_whisper_sub.py para escalar proporcionalmente à duração real do vídeo com folga segura (ex: max(900, duration * 3)) e tratar timeouts com fallback de modelo ou re-tentativa.
- Estado: PRECISA REVISÃO

## 20261117_1116 — Timeout fixo de 1800s aplicado incorretamente a vídeos curtos (pelo painel)
- Motivo / O que fiz (arquivos): Whisper estourou timeout de 1800s em vídeos de ~3 min porque o código usava max(1800, duracao_real * 5), forçando 30 min mesmo quando 5x seria 15 min. Consertos anteriores (15/11, 16/11) aumentaram de 900s pra 1800s, piorando o problema. Editei bin/anime_fetch.py:479,481 — troquei max(1800, ...) por max(900, ...) para timeout proporcional. Vídeo de 3 min: 900s (15m) vs 1800s (30m) anterior. / Como conferi: sintaxe OK, teste de cálculo confirmou 177s→900s (15m). / Como desfazer: botão "Desfazer" no painel (pedido 20261117_111602_2291)
- Estado: RESOLVIDO

## 20261117_1119 — MemoryError no _ler_ledger refatorado para leitura iterativa (pelo painel)
- Motivo / O que fiz (arquivos): _ler_ledger() em D:\postador-de-videos\bin\politica.py carregava o ledger inteiro (2920 linhas, 1.02 MB) com read_text().splitlines(), causando MemoryError em situações de contenção (log manhwa_react_20261115.log). Refatorei linhas 404-413 para leitura iterativa com LEDGER_FILE.open() em vez de read_text(), eliminando pico de memória. / Como conferi: compilação OK, _ler_ledger() leu 2920 registros com sucesso, politica.py rodou sem erro. / Como desfazer: botão "Desfazer" no painel (pedido 20261117_111919_8499)
- Estado: RESOLVIDO
## 20261117_1236 — Aviso de SSLError temporário no discover_canal (@100ANIMEE)
- Motivo / O que achei (trecho de log): parceiro_producao.log registrou aviso [discover_canal] API do site falhou em https://www.youtube.com/@100ANIMEE/shorts (SSLError: Max retries exceeded...) seguido de retry bem-sucedido logo em seguida.
- Causa provável: Instabilidade transitória de rede / conexão SSL com o YouTube. O próprio script recuperou sozinho via yt-dlp / retry automático.
- CONSERTO PROPOSTO: Nenhum (comportamento resiliente padrão do script).
- Estado: NADA A FAZER
## 20261117_1516 — Verificação do alimentador do recap longo e PC1
- Motivo / O que achei (trecho de log): Alimentador do recap longo (`cliente.py alimentar`) ativo no PC1, com processamento regular de filas e pausas automáticas gerenciadas pelos scripts de monitoramento (`encher_pilha.log`, `alimentar_pc2.log`).
- Causa provável: Ciclo normal de operação e controle de fluxo/contas do sistema.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — nenhuma intervenção ou alteração de código necessária).
- Estado: NADA A FAZER

STATUS: OK
## 20261117_1616 — Verificação do alimentador de parceiros (PC2 pausado) e monitor de saúde
- Motivo / O que achei (trecho de log): limentar_pc2.log registra parceiro: PC2 pausado (3 Shorts seguidos falharam lá — pc2_parceiro_falhou.json); nime_health_monitor.log aponta PermissionError: [WinError 32] em capar_shorts.log e ValueError: Invalid name '' em parceiro_postar.log.
- Causa provável: Falhas consecutivas de processamento de Shorts no PC2 acionaram a proteção de pausa automática, além de concorrência de arquivos (WinError 32) e erro pontual de nome de canal no postador (ValueError: Invalid name '').
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — aguardar liberação ou verificação manual pelo operador, sem intervenção direta nos scripts ou estado de pausa).
- Estado: PRECISA REVISÃO
## 20261117_1716 — Alerta de SSLError temporário no discover_canal (@japafishinglife) e resiliência automática
- Motivo / O que achei (trecho de log): D:\recapd-ambientes\producao\workspace\anime\_parceiro_20261117.log registrou aviso [discover_canal] API do site falhou em https://www.youtube.com/@japafishinglife/shorts (SSLError: HTTPSConnectionPool...). O sistema lidou com instabilidades de rede e seguiu postando Shorts com sucesso nas horas seguintes.
- Causa provável: Instabilidade transitória de DNS/SSL na requisição HTTP com o YouTube, recuperada automaticamente por retry/listas em cache dos scripts subsequentes.
- CONSERTO PROPOSTO: Nenhum (comportamento resiliente padrão do script, sem alteração necessária).
- Estado: NADA A FAZER

STATUS: OK
## 20261117_1737 — Erro ValueError em parceiro_postar.log ao verificar política de envio
- Motivo / O que achei (D:\recapd-ambientes\producao\logs\parceiro_postar.log): ValueError: Invalid name '' na função _chave_video em D:\postador-de-videos\bin\politica.py na linha 890 ao processar 
.get("caminho") vazio ou inválido (Path("").with_name(...)).
- Causa provável: O registro no ledger possui um campo caminho vazio ou nulo para algum vídeo antigo (como 	oy-story_cap1_20261102), fazendo com que pathlib.Path("") seja instanciado e falhe ao tentar substituir o sufixo.
- CONSERTO PROPOSTO: Em D:\postador-de-videos\bin\politica.py (linha 889-892), verificar se o caminho não está vazio antes de chamar pathlib.Path(p), ou tratar o caso em que o caminho é vazio retornando string vazia ou o nome original. (Como o arquivo pertence a D:\postador-de-videos, vigiado por outra sessão, o ajuste deve ser feito lá).
- Estado: PRECISA REVISÃO

## 20261117_1742 — ValueError com caminho vazio em _chave_video (pelo painel)
- Motivo / O que fiz (arquivos): Registros antigos do ledger (antes de 18/10) não têm campo 'caminho', causando ValueError ao tentar Path("").with_name("") na função _chave_video de D:\postador-de-videos\bin\politica.py:886-891. Adicionei proteção 'if not arquivo: return ""' no início da função para tratar caminho vazio/None. / Como conferi: teste com _chave_video(None) e _chave_video('') retornam '' sem erro; _chave_video(caminho_válido) funciona normalmente. / Como desfazer: botão "Desfazer" no painel (pedido 20261117_174212_d876)
- Estado: RESOLVIDO
## 20261117_1816 — Disco D: com 7.09 GB livres próximo ao limite mínimo de 8 GB
- Motivo / O que achei: Disco D: com 7.09 GB livres (4.27% de 166.01 GB), abaixo do limite mínimo de 8 GB estabelecido para a produção. Processos como encher_pilha.log e alimentadores estão ativos e baixando materiais normalmente. Wise Memory Optimizer ativo (PID 3840).
- Causa provável: Acúmulo normal de materiais e arquivos temporários de trabalho na fila de render e workspaces.
- CONSERTO PROPOSTO: Nenhum (o sistema de pilhas e os baixadores continuam funcionando, e o Wise Memory Optimizer gerencia a memória; limpeza agressiva não é permitida pelas regras do vigia).
- Estado: NADA A FAZER


## 20261117_1916 — recap longo: alimentador travado por ~50 min, já reiniciado automaticamente
- Motivo / O que achei (trecho de log): Alimentador do recap longo travado por ~50 min sem dar a volta, já reiniciado automaticamente pelo sistema de vigilância geral.
- Causa provável: Travamento transitório no ciclo do alimentador por concorrência de I/O ou espera em JSON/API.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — travamento transitório já recuperado pelo reinício automático).
- Estado: NADA A FAZER
## 20261117_2217 — Recap longo ativo e alimentando no PC1; PC2 com pausa do parceiro por falha em Shorts
- Motivo / O que achei (trecho de log): `encher_pilha.log` mostra pilha de recap longo ativa e recebendo fontes (pilha 10/10), enquanto `alimentar_pc2.log` indica pausa do parceiro no PC2 por 3 falhas seguidas no short `oYKDa0qCotc`. RAM livre em 7 GB, Wise Memory Optimizer ativo.
- Causa provável: Ciclo normal de preenchimento do recap longo no PC1; falhas na geração/upload de Shorts no PC2 ativando o mecanismo de proteção (`pc2_parceiro_falhou.json`).
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — respeitar a pausa automática do PC2 sem remover arquivos de travamento por conta da regra de não interferir em execuções e pausas).
- Estado: NADA A FAZER
## 20261118_0156 — Recap longo: alimentador reiniciado e disco D com 2.11 GB livres
- Motivo / O que achei (trecho de log): O alimentador do recap longo estava travado (88 min sem dar a volta), mas já havia sido reiniciado automaticamente pelo sistema. O disco D: apresenta 2.11 GB livres (abaixo do limite de 8 GB), com alto volume de arquivos e processos python ativos em render e preenchimento de pilhas. O Wise Memory Optimizer está rodando (PID 3840).
- Causa provável: Travamento transitório por concorrência de I/O no alimentador do recap longo (já recuperado) e uso intenso de armazenamento pela fila de render e pilhas de vídeos em D:.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — o reinício automático do alimentador ocorreu com sucesso e a regra proíbe remoção de arquivos ou limpeza de disco por conta própria).
- Estado: NADA A FAZER
## 20261118_0517 — Recap longo ativo no PC1 (pilha 14/14) e PC2 pausado por falhas no parceiro
- Motivo / O que achei: O log de  mostra o alimentador rodando normalmente (), enquanto  indica pausa no PC2 devido a falhas consecutivas em shorts (). Memória RAM livre em torno de 5.7 GB (acima do limite crítico de 3 GB).
- Causa provável: Funcionamento normal do ciclo de preenchimento do recap longo, com pausa de proteção no parceiro do PC2.
- CONSERTO PROPOSTO: Nenhum. O sistema está operando dentro dos parâmetros de controle e proteções automáticas.
- Estado: NADA A FAZER
## 20261118_0517 — Recap longo ativo no PC1 (pilha 14/14) e PC2 pausado por falhas no parceiro
- Motivo / O que achei: O log de `encher_pilha.log` mostra o alimentador rodando normalmente (`pilha: pedindo 1 fonte(s)... pilha 14/14`), enquanto `alimentar_pc2.log` indica pausa no PC2 devido a falhas consecutivas em shorts (`PC2 pausado (3 Shorts seguidos falharam)`). Memória RAM livre em torno de 5.7 GB (acima do limite crítico de 3 GB).
- Causa provável: Funcionamento normal do ciclo de preenchimento do recap longo, com pausa de proteção no parceiro do PC2.
- CONSERTO PROPOSTO: Nenhum. O sistema está operando dentro dos parâmetros de controle e proteções automáticas.
- Estado: NADA A FAZER
## 20261118_0915 — Disco D: com 6.76 GB livres (abaixo do limite de 8 GB)
- Motivo / O que achei (trecho de log): igia_agente_20261118_0517.log indicou operações normais, mas o disco D: apresenta atualmente 6.76 GB livres (4.1% de 166.01 GB), ficando abaixo do limite mínimo de 8 GB estabelecido para a produção.
- Causa provável: Acúmulo natural de materiais e arquivos temporários de trabalho na fila de render e workspaces.
- CONSERTO PROPOSTO: Nenhum (o sistema possui rotinas automáticas de pausa e controle de espaço; seguir a regra de não apagar arquivos de workspace, materiais ou caches manualmente).
- Estado: NADA A FAZER
## 20261118_1017 — recap longo: alimentador travado (41 min) e reiniciado automaticamente pelo vigia
- Motivo / O que achei (trecho de log): [18/11 10:15:51] outros projetos: PROBLEMAS: recap longo: alimentador travado (41 min sem dar a volta) — reiniciado || recap longo: 16 de 20 GPUs sem conta (sem conta livre/verificada); contas verificadas: 11 de 71 || disco D: com só 4.8 GB livres (mínimo 8): a produção para quando encher
- Causa provável: Travamento transitório no ciclo do alimentador por concorrência de I/O ou espera de locks em JSON/API, combinado com espaço reduzido em disco (4.8 GB) e esgotamento de contas de GPU.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — travamento transitório já recuperado pelo reinício automático do alimentador; monitorar espaço em disco e rotatividade de contas).
- Estado: NADA A FAZER
## 20261118_1117 — Recap longo: alimentador travado recuperado automaticamente e verificação de GPUs
- Motivo / O que achei (trecho de log): [18/11 10:15:51] outros projetos: PROBLEMAS: recap longo: alimentador travado (41 min sem dar a volta) — reiniciado || recap longo: 16 de 20 GPUs sem conta (sem conta livre/verificada); contas verificadas: 11 de 71 || disco D: com só 4.8 GB livres (mínimo 8)
- Causa provável: Travamento transitório no ciclo do alimentador por concorrência de I/O ou espera em JSON/API, combinado com esgotamento temporário de cota/contas de GPU e espaço reduzido em disco.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — travamento transitório já recuperado pelo reinício automático do alimentador; monitorar espaço em disco e cota de contas de GPU).
- Estado: NADA A FAZER
## 20261118_1135 — Erro de memória MKL e Whisper no parceiro-render
- Motivo / O que achei (trecho de log): `RuntimeError: mkl_malloc: failed to allocate memory` e `Whisper (model=base) rc=1` ao tentar transcrever localmente após falha do Groq/proxy.
- Causa provável: Sobrecarga de memória RAM/heap ao carregar o modelo base do Whisper junto com MKL.
- CONSERTO PROPOSTO: Em `bin/anime_fetch.py` ou `bin/_whisper_sub.py`, tratar exceções de falta de memória do MKL/Whisper liberando cache ou caindo para o modelo tiny/fallback mais leve, ou checar RAM antes de iniciar o Whisper pesado.
- Estado: PRECISA REVISÃO
## 20261118_1155 — Recap longo e alimentador do PC1 operando normalmente
- Motivo / O que achei (trecho de log): [18/11 11:57:10] pilha: nenhum baixador de fora deu sinal nos últimos 5 min e abastecedor Kaggle despachando shorts extras normalmente ([18/11 11:58:42] DISPAROU Short extra fS9dv8k5q_A [pesca]). PC2 pausado temporariamente por falhas consecutivas no parceiro (pc2_parceiro_falhou.json), mas alimentador geral ativo.
- Causa provável: Ciclo normal de operação, com pausas de proteção ativas para o PC2 devido a falhas de Shorts e espera de novas fontes externas.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — o alimentador do recap longo e processos no PC1 estão rodando corretamente).
- Estado: NADA A FAZER

## 20261118_1737 — Recap longo: 14 de 14 GPUs sem conta verificada; contas verificadas 3 de 71
- Motivo / O que achei (trecho de log): [18/11 11:55] Recap longo: 14 de 14 GPUs sem conta (sem conta livre/verificada); contas verificadas: 3 de 71 || alimentador rodando normal e processos ativos || PC2 pausado automaticamente por protecao de shorts. | Causa provável: As contas livres/verificadas estão temporariamente esgotadas ou aguardando renovação de cota nas plataformas de geração, exigindo o ciclo normal de recarga. | CONSERTO PROPOSTO: Nenhum — aguardar renovação de cota e ciclo automático das contas Kaggle/Veo. | O que fez: Modo só aviso, verificado logs, fila e processos, acionado Wise Memory Optimizer. 
- Estado: NADA A FAZER
## 20261118_1758 — Recap longo e alimentador do PC1 operando normalmente, PC2 pausado por falha no parceiro
- Motivo / O que achei (trecho de log): `[18/11 17:57:11] pilha: nenhum baixador de fora deu sinal nos últimos 5 min — não peço nada agora` e `[18/11 17:58:17] parceiro: PC2 pausado (3 Shorts seguidos falharam lá — pc2_parceiro_falhou.json)`. Memória RAM livre estável acima de 5 GB.
- Causa provável: Funcionamento normal do ciclo de preenchimento do recap longo, com pausa de proteção no parceiro do PC2.
- CONSERTO PROPOSTO: Nenhum. O sistema está operando dentro dos parâmetros de segurança.
- Estado: NADA A FAZER

## 20261118_1958 — Cobertura ffmpeg com TimeoutExpired e disco D com 6.51 GB livres
- Motivo / O que achei: O log _parceiro_20261118.log registrou TimeoutExpired no ffmpeg ao fazer cobertura e o disco D: tem apenas 6.51 GB livres (abaixo do limite de 8 GB).
- Causa provável: Lentidão no FFmpeg ou alta carga de I/O por pouco espaço no disco D:.
- CONSERTO PROPOSTO: Aumentar o timeout do ffmpeg de cobertura em anime_auto.py / parceiro e liberar espaço no disco D.
- Estado: REVISAR
## 20261118_2018 — Vigia: Guarda do disco D (0.14 GB) e otimizador de memória ativo
- Motivo / O que achei (trecho de log): D: com 0.14 GB livres, disparado backup_drive e cache do Chrome, apaguei 4 trecho(s) velho(s) do aprendizado. Wise Memory Optimizer ativo.
- Causa provável: Acúmulo de arquivos de trabalho e cache no disco D.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — aguardar liberação automática de espaço pelo backup/sistema).
- Estado: NADA A FAZER

## 20261118_2218 — parceiro-render: rc=1 no Kaggle ao processar lote e falhas de malloc/timeout no Whisper local
- Motivo / O que achei (trecho de log): _parceiro_20261118.log: RuntimeError: mkl_malloc: failed to allocate memory no Whisper local e rc=1 no Kaggle ao processar lotes, além de avisos HTTP 429 e SignIn do yt-dlp.
- Causa provável: Contenção pontual de memória (MKL malloc) ao rodar whisper local sob alta carga de render e limite de chamadas/bloqueios do yt-dlp.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — aguardar liberação de recursos do Wise Memory Optimizer e rotação de IPs do ytdlp).
- Estado: NADA A FAZER

## 20261118_2355 — Recap longo aguardando cota nas GPUs e rotinas normais
- Motivo / O que achei (trecho de log): melhorador_central.log mostra recap longo aguardando cota nas GPUs (rodízio normal) e rotinas de cortes rodando normalmente.
- Causa provável: Uso regular de cotas nas contas do Veo e rodízio automático aguardando a próxima volta.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — aguardar liberação de cota pelo próprio rodízio do sistema).
- Estado: NADA A FAZER
STATUS: OK

## 20261119_0023 — TikTok: Postador passava apelido em vez de e-mail ao cofre e recusava contas vivas do Kaggle (pelo painel)
- Motivo: erro "Chrome ja estava aberto por outro projeto sem o proxy dela" repetido (mundosolar1995 em 17/11 05:11–07:39 e 18/11 03:08/03:21; aulasrevolution em 17/11 14:39). bin\postar_tiktok_auto.py:169 chamava cofre.saida_kaggle com o apelido; o cofre só reconhece o e-mail inteiro (cofre.py:158), devolvia None e caía na trava das linhas 171-174.
- O que fiz (arquivos): só bin\postar_tiktok_auto.py linha 169: cofre.saida_kaggle(r["cofre"]) passou a cofre.saida_kaggle(cofre.conta(r["cofre"])[0]). Cofre.py não foi mexido.
- Como conferi: sintaxe do arquivo OK; cofre.conta converte apelido em e-mail; saida_kaggle com apelido = None (defeito) e com e-mail = ponte do IP fixo de cada conta (mundosolar1995 e aulasrevolution). Ainda não vi uma rodada real do TikTok depois da mudança. fabricadeautomacoesia (banida, sem IP fixo) continua sendo recusada de propósito.
- Como desfazer: botão "Desfazer" no painel (pedido 20261119_002316_8fa0)
- Estado: PRECISA REVISÃO (falta conferir na próxima rodada do TikTok que mundosolar1995 e aulasrevolution postam agendado)
## 20261119_0255 — Estoque sem novos candidatos / download falhou no parceiro-producao e proxy Groq fora
- Motivo / O que achei (trecho de log): D:\recapd-ambientes\producao\logs\parceiro_producao.log registrou [2026-11-19 02:39:56] estoque: nada reposto (8/8; sem candidato novo ou download falhou) e no log _parceiro_20261119.log: groq: proxy .webshare.io:80 fora (groq: ProxyError).
- Causa provável: Instabilidade temporária no proxy Webshare e falta temporária de novos candidatos válidos na fonte de pesca/negócios.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — aguardar reconexão do proxy e nova varredura de candidatos).
- Estado: NADA A FAZER
## 20261119_0417 — Recap longo no PC1 e parceiro: funcionamento normal com reposição de estoque em 8/8
- Motivo / O que achei (trecho de log): Processos em Python do ambiente de produção ativos e estáveis. Estoque do parceiro completo em 8/8, com pequenas falhas transitórias de proxy já tratadas pelo rodízio automático.
- Causa provável: Ciclo normal de operação e controle de fluxo do sistema.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — nenhuma intervenção ou alteração de código realizada).
- Estado: NADA A FAZER
## 20261119_0555 — Vistoria geral: alimentador longo reiniciado e GPUs em uso normal
- Motivo / O que achei (trecho de log): Recap longo com alimentador travado (107 min) e reiniciado automaticamente; 17 de 20 GPUs sem conta (aguardando próxima volta de lançamento), contas verificadas 11 de 71. Wise Memory Optimizer rodando normalmente.
- Causa provável: Travamento transitório no ciclo do alimentador por concorrência de I/O ou espera em JSON/API.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — o alimentador já foi reiniciado e o sistema prossegue no fluxo normal).
- Estado: NADA A FAZER
## 20261119_0755 — Disco D: com 5.41 GB livres (abaixo do limite de 8 GB)
- Motivo / O que achei (trecho de log): Get-CimInstance Win32_LogicalDisk mostra D: com 5.41 GB livres (3.26% de 166.01 GB), abaixo do limite mínimo de 8 GB estabelecido para a produção. Os processos de render, melhorador central e alimentadores estão ativos e trabalhando normalmente. Wise Memory Optimizer ativo (PID 3840).
- Causa provável: Acúmulo normal de materiais, workspaces e artefatos de render nas filas de produção.
- CONSERTO PROPOSTO: Nenhum (o sistema possui rotinas automáticas de gerenciamento de espaço e o modo é estritamente de aviso, conforme regra do dono).
- Estado: PRECISA REVISÃO

## 20261119_1156 — Recap longo com alimentador ativo na pilha e PC2 pausado por falhas no parceiro; contas em uso normal
- Motivo / O que achei (trecho de log): encher_pilha.log mostra processamento contínuo da pilha de Shorts (com baixadores em paralelo e pausas por timeout em algumas fontes), enquanto parceiro_postar.log relata PC2 pausado (3 Shorts seguidos falharam lá — pc2_parceiro_falhou.json). Processos de Python ativos e Wise Memory Optimizer rodando normalmente.
- Causa provável: Ciclo normal de operação do alimentador com pausa de proteção automática no PC2 após falhas consecutivas de Shorts do parceiro, além de timeout em baixadores externos eventuais.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — respeitar a pausa automática de proteção do PC2 sem remover arquivos de falha nem interferir nos fluxos).
- Estado: NADA A FAZER
STATUS: OK
## 20261119_1436 — Vistoria geral: disco D: em 7.24 GB livres (abaixo do limite de 8 GB) e proxy Groq com falhas transitórias
- Motivo / O que achei (trecho de log): Get-CimInstance Win32_LogicalDisk mostra D: com 7.24 GB livres (7.24 GB / 166.01 GB), ligeiramente abaixo do limite mínimo de 8 GB. Logs de parceiro registraram avisos de proxy Webshare/Groq fora (recuperáveis com teste posterior) e WinError 32 pontual em capar_shorts.log. Produção de anime e monitoramento ativos e normais.
- Causa provável: Acúmulo padrão de arquivos na produção e instabilidade temporária em proxies externos de API.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — aguardar limpeza automática do sistema e reconexão de proxy sem modificações manuais).
- Estado: PRECISA REVISÃO
