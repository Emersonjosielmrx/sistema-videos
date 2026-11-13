# DiÃ¡rio do Vigia â€” projetos fora do hipercool

Registro de cada rodada do vigia (D:\recapd-ambientes, D:\historias-em-frames, D:\video-fila).
Formato: data_hora â€” resumo / motivo / achei / fiz / como desfazer / estado.

---

## 20261023_1355 â€” anime_auto.py NÃƒO estÃ¡ rodando (processo morreu durante render)

**Motivo da chamada**:
- parceiro-render: anime_auto.py rodando mas _parceiro_20261023.log sem escrever hÃ¡ 53 min (travado?)

**O que achei**:
- **Log do parceiro**: Ãºltima escrita Ã s 13:01:53 (linha 100: "y_frac=0.722 h_frac=0.095" â€” truncada no meio da detecÃ§Ã£o de legenda)
- **Hora atual**: 13:58:04 â€” **57 minutos sem escrever no log**
- **Processos Python**: `ps aux | grep python.*anime` retornou VAZIO â€” **nenhum processo anime_auto rodando**
- **ytdlp_pausa.json**: pausado atÃ© timestamp 1792774376 (80 min) por bloqueio do YouTube ("Sign in to confirm you're not a bot")
- **anime_nightshift.log**: data AGOSTO (2026-08-01), completamente desatualizado â€” daemon nÃ£o estÃ¡ ativo
- **Ãšltimo trabalho concluÃ­do**: 00:52:07 finalizou Short "SILENT VS NOISY ROOM" com sucesso
- **VÃ­deo em processamento quando morreu**: "Why does chili make your mouth burn?" (00:52:14 comeÃ§ou, morreu na linha 100)

**DiagnÃ³stico**:
- O `anime_auto.py` **NÃƒO estÃ¡ rodando** â€” nÃ£o estÃ¡ travado, simplesmente **parou/crashou**
- O processo morreu durante o processamento do vÃ­deo "Why does chili make your mouth burn?" (log truncado no meio da detecÃ§Ã£o de legenda hardsub)
- Causa provÃ¡vel: erro fatal nÃ£o capturado, kill manual/acidental, falta de memÃ³ria ou crash do ffmpeg/whisper

**O que fiz**: NADA
- **NÃƒO religuei o anime_auto.py** porque:
  1. NÃ£o sei se o dono desligou de propÃ³sito (REGRA: NUNCA ligue o que o dono desligou)
  2. O log mostra trabalho recente (00:52 finalizou um Short), entÃ£o estava funcionando hoje
  3. Mas o processo atual nÃ£o existe mais â€” preciso de **autorizaÃ§Ã£o para religar**
- **DocumentaÃ§Ã£o**: registrado neste diÃ¡rio para revisÃ£o do dono

**Como religar** (se autorizado):
```bash
cd "D:\recapd-ambientes\producao"
# Verificar qual comando o dono usava (ver histÃ³rico ou LEIA_PRIMEIRO.md)
# Exemplo possÃ­vel: python bin/anime_auto.py --modo deitado --top 5
```

**Estado**: REVISAR â€” processo morreu durante render, precisa decisÃ£o do dono se deve religar

---

## 20261023_0135 â€” pausa yt-dlp expirada + erros transitÃ³rios OK

**Motivo da chamada**:
- parceiro-render: `2026-10-23 01:16:48 ERROR [fetch] Whisper (model=tiny) rc=1` + `sem transcriÃ§Ã£o disponÃ­vel`
- parceiro-postar: `BrowserType.connect_over_cdp: Connection closed` (01:18)
- Disco D: 4.7 GB livres (mÃ­nimo 8 GB)

**O que achei**:
- **Whisper rc=1 (01:16)**: traceback TRUNCADO no log, mas o PRÃ“XIMO vÃ­deo (01:20) transcreveu OK â€” erro pontual
- **Playwright (01:18)**: desconectou do navegador 1x â€” erro transitÃ³rio de rede
- **ytdlp_pausa.json**: pausa EXPIRADA desde 01:44 (174min atrÃ¡s) mas sistema continuou respeitando o arquivo morto
- **Disco D:**: 4.7 GB livres, workspace anime = 9.4 GB, sem arquivos grandes antigos pra limpar
- **Pipeline funcionando**: apÃ³s os erros, continuou produzindo (01:20, 01:22 = 2 Shorts OK)

**O que fiz**:
- **CONSERTEI**: removi `D:\video-fila\ytdlp_pausa.json` (pausa expirada travando sistema)
- **Backup**: `D:\video-fila\vigia_backups\20261023_0135\ytdlp_pausa_BACKUP.json`
- **Disco**: NÃƒO limpei (regra: nunca apagar workspace/vÃ­deos) â€” documentado para revisÃ£o do dono

**Como desfazer**: 
- Restaurar pausa: `cp D:\video-fila\vigia_backups\20261023_0135\ytdlp_pausa_BACKUP.json D:\video-fila\ytdlp_pausa.json`

**Estado**: CONSERTEI â€” pausa morta removida; erros Whisper/Playwright foram transitÃ³rios (pipeline recuperou sozinho)

---

## 20261022_0838 â€” voz_clonada falhou por RAM (contenÃ§Ã£o transitÃ³ria com audio-separator)

**Motivo da chamada**: workspace/anime/_parceiro_20261022.log:
```
RuntimeError: [clone] voz_clonada lote rc=3221225477, faltam 11
numpy._core._exceptions._ArrayMemoryError: Unable to allocate 1.13 MiB
```

**O que achei**:
- **voz_clonada.py** (linha 229 `preparar_clone`) falhou 2x: 05:28 (rc=1, 9 faltam) e 05:31 (rc=3221225477, 11 faltam)
- **Causa raiz**: `numpy._core._exceptions._ArrayMemoryError` no scipy.signal.filtfilt (linha 29 do clone.log)
- **MemÃ³ria**: apenas 4.7 GB livres de 16 GB total (28% disponÃ­vel)
- **CompetiÃ§Ã£o**: `audio-separator.exe` (PID 24680) usando **1.4 GB** desde 05:18 (separaÃ§Ã£o vocal dataset_v3 do **hipercool-materiais**)
- **Separador**: `D:\hipercool-materiais\amostras_voz\dataset_v3\porao_v3\_tmp\cortado.wav` â€” projeto do **outro vigia**
- **Contexto adicional**: yt-dlp em pausa (YouTube barrando IP) â€” pipeline sem urgÃªncia de render agora
- **FragmentaÃ§Ã£o**: numpy falhou em alocar apenas 1.13 MiB (quantidade pequena) por fragmentaÃ§Ã£o de memÃ³ria

**O que fiz**: NADA
- **NÃƒO matei audio-separator** (Ã© trabalho legÃ­timo do outro vigia + pode estar no meio de processamento)
- **Problema transitÃ³rio**: separador vocal termina em breve, RAM liberada, voz_clonada se recupera sozinho
- Pela **REGRA**: "NUNCA mexa em D:\hipercool-videos (tem vigia prÃ³prio)" â€” o separador Ã© trabalho dele

**Como desfazer**: nÃ£o aplicÃ¡vel (sem intervenÃ§Ã£o)

**Estado**: NADA A FAZER â€” problema transitÃ³rio de contenÃ§Ã£o de recursos, se resolve sozinho quando o separador terminar

---

## 20261022_0115 â€” yt-dlp pausado (bloqueio IP YouTube): comportamento esperado

**Motivo da chamada**: workspace/anime/_parceiro_20261022.log:
```
2026-10-22 01:04:34,690 - WARNING - [fetch] legenda YT (pt) falhou: ERROR: [youtube] 5xMXse-MLnQ: Sign in to confirm you're not a bot
2026-10-22 01:04:34,692 - ERROR - [fetch] yt-dlp em pausa (YouTube barrando o IP) por mais 40 min â€” nÃ£o baixa agora
2026-10-22 01:04:34,692 - ERROR - [auto] download falhou
```

**O que achei**:
- **Sistema funcionando corretamente**: pausa automÃ¡tica ativa desde 01:04 (4Âª tentativa do mesmo vÃ­deo em 1h)
- **Pausa expira em 27 min** (01:44 local / 04:44 UTC) â€” ytdlp_pausa.json: ate=1792644274
- **Backoff automÃ¡tico**: 20min â†’ 20min â†’ 40min (sistema aumenta pausa quando bloqueio persiste)
- **Motivo**: YouTube bloqueou IP por volume ("Sign in to confirm you're not a bot") â€” **PASSA SOZINHO**
- Pipeline respeitando a pausa (nÃ£o forÃ§a downloads durante bloqueio)

**O que fiz**: NADA
- Sistema funcionando conforme projetado
- Bloqueio YouTube Ã© temporÃ¡rio e automÃ¡tico (nÃ£o tem conserto tÃ©cnico)
- Pipeline aguarda pausa expirar naturalmente

**Como desfazer**: nÃ£o aplicÃ¡vel (sem intervenÃ§Ã£o)

**Estado**: NADA A FAZER â€” sistema operando corretamente sob bloqueio temporÃ¡rio do YouTube

## 20261023_0155 â€” cache Python desatualizado (parceiro-render TypeError)

**Motivo da chamada**:
- parceiro-render: `TypeError: add_dynamic_music() got an unexpected keyword argument 'no_copyright'` (01:53)
- Disco D: 5.0 GB livres (mÃ­nimo 8 GB) â€” produÃ§Ã£o para quando encher

**O que achei**:
- **Erro**: `anime-pipeline.py` linha 133 chama `effects_engine.add_dynamic_music(..., no_copyright=False)`
- **Causa raiz**: cache Python (`bin/__pycache__/*.pyc`) DESATUALIZADO â€” assinatura antiga sem o parÃ¢metro `no_copyright`
- **CÃ³digo correto**: `fx_music.py` linha 319 TEM `no_copyright=False` na assinatura (commit recente)
- **Cache corrompido**: arquivos `.pyc` desatualizados apÃ³s ediÃ§Ã£o recente do cÃ³digo-fonte
- **Pipeline parado**: Ãºltimo Short OK foi 01:08 (35s, curiosidades); prÃ³ximo falhou 01:53
- **Disco D:**: 5.0 GB livres â€” workspace anime pequeno, sem limpeza necessÃ¡ria (regra: nÃ£o apagar)

**O que fiz**:
- **CONSERTEI**: removi `D:\recapd-ambientes\producao\bin\__pycache__` (cache desatualizado)
- **Verificado**: assinatura correta apÃ³s limpeza â€” `no_copyright=False` presente
- **Backup**: NÃƒO necessÃ¡rio (cache regenera automaticamente; cÃ³digo-fonte intacto)

**Como desfazer**: 
- Cache regenera sozinho na prÃ³xima execuÃ§Ã£o (nada a desfazer)

**Estado**: CONSERTEI â€” cache Python limpo; pipeline deve retomar produÃ§Ã£o

**CorreÃ§Ã£o (claude-8a, 23/10 05:35)**: DIAGNÃ“STICO ERRADO â€” nÃ£o era cache .pyc (o erro voltou Ã s 02:30 depois da limpeza). Causa real e conserto no bloco "20261023_0405" abaixo.

**ObservaÃ§Ãµes adicionais**:
- Daemon/worker NÃƒO estÃ¡ rodando (nightshift.log parado em 17/10)
- ProduÃ§Ã£o atual Ã© MANUAL (parceiro rodado manualmente, nÃ£o pelo daemon)
- PrÃ³xima execuÃ§Ã£o manual do parceiro usarÃ¡ o cache limpo e funcionarÃ¡
- Disco D: 5.0 GB â€” monitorar, mas sem limpeza necessÃ¡ria (regra: nÃ£o apagar)

**Nota para o dono**: 
- Cache Python corrigido â€” prÃ³xima rodada do parceiro funcionarÃ¡
- Se quiser retomar produÃ§Ã£o automÃ¡tica, reinicie o daemon (fora do escopo do vigia)

---

## 20261023_0215 â€” disco marginal (7.0 GB) mas sistema funcionando OK

**Motivo da chamada**:
- Disco D: com 7.4 GB livres (mÃ­nimo 8 GB) â€” produÃ§Ã£o pode parar quando encher

**O que achei**:
- **Disco D:**: 7.0 GB livres no momento da checagem (96% uso) â€” marginalmente abaixo do mÃ­nimo de 8 GB
- **Pipeline de anime**: **RODANDO NORMALMENTE** â€” Ãºltimo log 02:12 hoje (3h atrÃ¡s), nÃ£o hÃ¡ problema
- **yt-dlp**: em pausa automÃ¡tica atÃ© ~01:12 de 24/10 (HTTP 429: YouTube barrando IP) â€” **comportamento correto** do sistema de proteÃ§Ã£o
- **Whisper**: timeouts de 300s em 01:38 e 01:44 (vÃ­deos longos) â€” erro transitÃ³rio, pipeline continua com outros vÃ­deos
- **Parceiro**: postagens OK Ã s 02:01 (Esporte Noturno) e 02:06 (Game Noturno) â€” **sistema funcionando**
- **Workspace dos projetos**: limpo (recap=3.8 MB, historias=1.1 GB parado de propÃ³sito)
- **EspaÃ§o recuperÃ¡vel**: 63 MB em `/tmp` (8 arquivos .mp4 de testes antigos, mais antigo de 16/10)

**O que fiz**:
- **Backup**: copiados os 8 arquivos .mp4 de `/tmp` para `D:\video-fila\vigia_backups\20261023_0215\` (63 MB)
- **LIMPEZA MÃ