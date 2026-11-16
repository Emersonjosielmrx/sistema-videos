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
