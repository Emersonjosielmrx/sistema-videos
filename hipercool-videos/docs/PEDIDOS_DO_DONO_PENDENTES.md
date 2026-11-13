# Pedidos do dono — o que falta fazer (passagem de bastão, 15/10/2026 ~8h50)

Para o próximo modelo/agente que pegar o hipercool. Antes de mexer, leia:
1. `CLAUDE.md` (deste projeto);
2. `docs/MELHORIAS_PARA_TODOS_OS_PROJETOS.md` (regras de título, capa, Studio, estrutura);
3. `docs/revisao_tecnica_melhorias.md` (o que já foi feito e conferido);
4. `docs/seo_titulos.md`.

Confira cada item na produção real (log, print, arquivo), não só lendo código. O dono escreve em português informal,
com erros de digitação, e quer resultado pronto e resposta direta.

## Regras que não mudam

- Nunca mostrar chave/token nem o conteúdo de `secrets/`. Commit/push só com confirmação do dono.
- Um render pesado por vez na máquina. Português sempre primeiro.
- Google/YouTube **só pelo navegador** (Chrome do cofre, `youtube_web_poster.py`). Nunca criar nem pedir chave de API
  no Google Cloud. O autocompletar público (`suggestqueries`) pode.
- O postador (`D:\postador-de-videos`) é usado por todos os projetos. Mudança tem que ser compatível com o que já
  existe; prefira módulo novo (foi o que se fez com `youtube_studio_extras.py`).
- Código mudou e roda no PC2 (línguas)? Copie: `scp bin/<arquivo> pc2:C:/hipercool-videos/bin/`.
- **Recusado, não fazer mesmo se o dono insistir** (responder curto, sem sermão):
  - capa com marcador de cena de sexo: olho revirado/ahegao, baba, fluido, camisinha, mão no seio, recorte de
    painel de sexo, "sofrimento" sexual; nudez, mosaico na capa, cara de menor;
- **Voz de outros canais na abertura**: LIBERADO só para os canais que autorizaram o dono em 15/10/2026 (lista em
  `config/intros_voz.json` → `autorizados`; o dono está pedindo de mais canais). Canal fora da lista: não usar. Nunca
  o nome do canal/criador na fala. Ver item 5.

---

## Pendentes, em ordem de prioridade

### 0. Ordem de postagem por dia (dona, 23/10/2026) ✅ FEITO no código (23/10 noite) — ver CLAUDE.md, "Postagem"
- Pedido: "um vídeo do capítulo feito em retrato, um do capítulo feito em paisagem, um compilado do cap 1 até o atual
  do dia que foi postado [...] só [depois] shorts cortados dos capítulos e os de resumo. [...] todo dia."
- Feito: `fila._longos_do_dia` / `compilados_do_dia` / `_postar_longo_da_vez`, `postar_hipercool --longo-caps A-B` e o
  Short de resumo entrando por último (`postar_hipercool.short_resumo_postavel`, só pt). Backups `*.bak_20261023_ordem`.
- 23/10 (2ª leva): `longo_pt_desde` tirada por decisão da dona; compilado pt só com 16:9 refeitos; teto do dia = o
  real do canal (Manhwa Noturno 3, línguas 4). Falta (postador, não mexido): `catalogo.PASTAS` não tem
  `D:\hipercool-materiais\shorts_hipercool` (destino real da junção `workspace\shorts`), então 4 Shorts postados
  (0,33 GB) não vão pro Drive.

### 1. Capas novas do cap 7 (depois caps 2–5 e compilado) — esperando a cota de imagem
- **Pedido**: capas com o catálogo novo de poses e roupa só sensual (lingerie/biquíni/camisola/babydoll).
  - Ver a memória `feedback_capas` e `docs/MELHORIAS...` §2.
  - O dono aprovou do cap07_sheet: harém na cama e ela ajoelhada por cima dele no chão.
  - Reprovou:
    - língua de boca fechada (tem que ser BOCA BEM ABERTA, língua pra fora);
    - perna por cima (tem que ser EM VOLTA DO PESCOÇO);
    - colo com 1 mulher só;
    - poses já testadas (ela sozinha em cima, sentada de frente).
- **Estado**:
  - As capas atuais do cap 7 (`workspace/videos/the-inheritor/cap07/pt/censurado/...capa*.jpg`) são do plano
    ANTIGO.
  - O plano antigo foi arquivado em `workspace/cache/capa_ia/plano_the-inheritor_cap07.v1-antigo.json`.
  - O plano de texto agora passa no LLM (testado). Imagem: a cota do `antigravity/gemini-3.1-flash-image` acabou
    às 06:57 e voltaria por volta das 11:12.
  - 15/10 11:15: tentado. A 1ª imagem foi reprovada pelo verificador (`ato_sexual`) e o gateway ficou sem cota de
    novo: 0 de 3 capas, nada foi sobrescrito. Cópia das capas antigas em `workspace/tmp/capas_cap07_plano_antigo/`.
    Tentar de novo quando a cota voltar.
- **Fazer**:
  ```
  cd /d/hipercool-videos
  PYTHONUTF8=1 venv/Scripts/python.exe bin/capa_ia.py --obra the-inheritor --selo "CAP. 7" --chave cap07 \
    --saida workspace/videos/the-inheritor/cap07/pt/censurado/hipercool_the-inheritor-cap-tulo-7_20261015_0730_NORMAL_CENSURADO_ULTIMO.capa.jpg \
    --narracao workspace/narration_cache/the-inheritor-cap07_sk1_sf1_111panels.json
  ```
  - Montar uma folha (contact sheet) com as 3 capas e MOSTRAR ao dono antes de seguir.
  - Depois: caps 2–5 (mesmo comando, `--chave capNN` e a capa de cada um) e o compilado
    (`hiper-longo._capa_compilacao`, chave `caps01-05`).
- **Atenção**: o cap 7 está "pronto" e ainda não foi postado em pt. Se a fila postar antes, ele sobe com a capa
  antiga; depois troque a capa no Studio.

### 2. Capas verticais dos Shorts — 1º teste de verdade
- **Pedido**: "tem que fazer para os shorts também".
- **Estado**:
  - Código pronto: `capa_ia.capas_short` (720x1280, 2 imagens 9:16 por capítulo, selo "CAP. N • i/total") e
    `postar_hipercool.capas_short` (põe a capa em cada Short no upload).
  - Nunca rodou com imagem, por falta de cota.
- **Fazer**:
  - Depois da cota, gerar para o cap 2 (cortes já feitos em `workspace/shorts/the-inheritor-cap2/`) e mostrar
    ao dono.
  - No 1º Short postado, conferir no log do `youtube_web_poster` a linha "capa: enviada" (o upload de Short pode
    não ter campo de miniatura).
  - Se não tiver, colocar a capa depois do upload pela página de edição (lá tem "Enviar arquivo": visto em 15/10).

### 0. ADVERTÊNCIA no canal pt (16/10) e análise do vídeo pronto — LER PRIMEIRO
- O canal pt antigo (InovareManhwaVerse) levou **advertência das diretrizes ("Nudez e conteúdo sexual")** pelo
  compilado caps 1-11 (`8ln3ExxYEcc`, removido pelo YouTube): painéis sem censura e mosaico no lugar errado.
  Envio bloqueado até ~23/10; a advertência vale até ~14/01/2027; mais 2 em 90 dias apagam o canal.
- Feito (16/10): os 13 vídeos do The Inheritor do canal antigo ficaram PRIVADOS (`youtube_studio_extras.py
  --visibilidade private`, função nova); o cred `novo_inovaremanhwaverse` foi para `suspensos` no
  `D:\postador-de-videos\config\canais_status.json`; o compilado caps 1-3 (`GzVaXWTzJ00`) também tinha mamilos à
  mostra aos ~15:10 e está privado.
- Feito (16/10): **`bin/revisao_video.py`** — análise do vídeo censurado pronto, quadro a quadro (Gemini), que trava a
  postagem e refaz o capítulo sozinha; reforços na `censura_visual` (painel de score baixo, conferência do mosaico,
  lista de fosco forçado, parser de várias caixas). Detalhes no `CLAUDE.md` ("Análise do vídeo pronto").
- O dono criou o canal pt novo **Manhwa Noturno** (@manhwanoturno, cred `novo_manhwanoturno`; outra sessão mudou
  `config/fila.json` e a marca d'água). Atenção: postar em outro canal durante a semana de envio bloqueado pode ser
  tratado pelo YouTube como burlar a restrição. Caps 1 e 2 são renders antigos: só sobem se a análise aprovar.
- Decisão do dono pendente: cena de sexo mosaicada (1/3 do vídeo, auditoria `seguranca-06`) a análise costuma
  reprovar quando o mosaico é só na boca/fluido — o resultado é mais fosco nessas cenas.
- **Regra do dono (16/10 10:15)**: barra preta em volta do painel (e defeito visual parecido) é aceitável e pode
  postar — não parar render nem segurar postagem por isso; só censura trava.
- **Regra do dono (16/10)**: mosaico sempre primeiro, fosco só se não tiver jeito. Versão normal do vídeo só
  precisa ser produzida uma vez — re-renders fazem apenas a censurada (flag `so_cens_pt` em `hiper-pipeline.py`).
  Canais de outros idiomas (hi/id/it/ru/th/vi) NÃO receberam strike; continuam postando normalmente.
- **Re-render de tudo (16/10 08:50, rodando)**: `bin/refazer_caps.py 1-11` (processo destacado; log
  `logs/refazer_caps.log`), em ordem, via `fila.renderizar`: roteiro/censura/2.5D do cache, vozes do elenco novo
  (dono: caps 1 e 2 só vão pro canal novo com as vozes novas — nada do que saiu no canal antigo é reaproveitado;
  caps 1-7 tinham as vozes antigas do Gemini), marca @manhwanoturno e análise do vídeo pronto no fim de cada um.
  ~1 h por capítulo. Ele espera se houver outro hiper-pipeline rodando — não lance outro lote por cima.
- **Lançamento do Manhwa Noturno (16/10, rodando)**: o dono pediu, nesta ordem, cap 1 completo em retrato → cap 1
  em 16:9 → Shorts do cap 1, respeitando o tempo entre postagens. `bin/refazer_caps.py 1-11 --longo 1 --assumir`
  faz o 16:9 do cap 1 logo depois do retrato; `bin/lancamento_pt.py` (log `logs/lancamento_pt.log`) posta um por
  vez pela política `postagem_pt` (canal parado sai já; depois 2 h e só no pico 18h-23h), só o cap 1 NOVO com análise
  "ok". O 16:9 do pt passou a usar o elenco novo (até hoje usava as vozes do Gemini: `hiper-longo._momentos`).
- **PC2** (16/10 ~09:45): os 18 arquivos de `bin/` + `marca_scan.py` foram copiados (md5 conferido às 10:00: tudo
  igual ao PC1, menos `fx_clips.py`, que mudou aqui depois da cópia — conserto da barra preta em andamento por outra
  sessão às 09:57). Ao terminar o conserto, copiar de novo `fx_clips.py` e `elenco.py`. O cap 3 RU que roda lá desde
  09:35 começou com o código antigo.
  PC2 ficou desligado de ~10:05 a ~10:17; às 10:10 recebeu o `fx_clips.py`/`elenco.py` consertados (md5 conferido)
  e foi religado.

### 0b. Achados de 16/10 à tarde (análise feita direto, sem subagentes — o workflow caiu inteiro em 429)
1. **Mapa do meta atrasado (causa raiz: `fx_clips._igualar_audio`) — FEITO 16/10 12:12 (ok do dono): `-af apad`
   junto do `-shortest`; testado nos clipes reais do cap 1 (55 refeitos, perda total 0,18 s contra 3,55 s; os curtos
   ficam com 1,5 s); copiado pro PC2 (md5 conferido). Vale do próximo render em diante.** O
   `_igualar_audio` refaz com `-shortest` os clipes cujo áudio é de outro formato (24 kHz no meio de 48 kHz: 61 de
   ~107 no cap 1). Clipe curto tem vídeo de 1,5 s (mínimo de propósito) e fala de 0,8-1,1 s: a cópia sai com
   0,83-1,15 s. Perda de 3,55 s no cap 1 (`workspace/tmp/session_1792159021`, conferido clipe a clipe); o
   `fx_acabamento.finalizar` mede os clipes ORIGINAIS, então `acabamento.fronteiras` fica até 2,3-3,5 s adiantado no
   fim (vídeo 433,5 s x meta 436,8 s; cortes reais medidos). Efeitos: painel curto pisca (<1 s), aviso "CENSURADO PRO
   YOUTUBE" em cima do painel errado no fim (visto aos 421 s, no casaco), corte dos Shorts fora da fronteira perto do
   fim (provável causa do "corte no meio da fala" da auditoria), revisor apontando painel errado (já contornado no
   revisor). Conserto de 1 linha: `-af apad` junto do `-shortest` no `_igualar_audio` (o áudio ganha silêncio e o clipe
   fica com a duração do vídeo). Conferir depois: meta x `ffprobe` do vídeo final batendo.
2. **Backup dos caches: roteiro/censura/groq sem cópia desde 14/10.** Em 15 e 16/10 a tarefa morreu no limite de 2 h
   com as vozes primeiro (16/10: 640 MB a 77 KB/s, 2h23; código 267014 = encerrada pelo agendador) e o
   `backup_caches.log` não tem linha desde 14/10 06:44. O código das 06:39 (vozes por último + limite de 100 min) já
   resolve a partir de amanhã. Conferir a rodada de 17/10 06:10. Rodado de novo à mão em 16/10 ~12:10 (ok do dono):
   ver o fim do `logs/backup_caches.log`.
3. **Login do canal descoberto na hora de postar.** O completo do cap 1 falhou às 11:30 com "Confirme que é você"
   (conta inovaremanhwaverse2, print `D:\postador-de-videos\logs\yt_web\20261016_113053_falha_manhwanoturno.png`),
   embora o cofre marcasse google=vivo às 07:29. Ideia: rodar `youtube_web_poster.py --checar` dos canais do
   hipercool (pt + línguas) 1x/dia antes do pico e avisar no Telegram quem precisa logar.
4. **Renders antigos do cap 1 pt com nudez sem censura — APAGADOS** (16/10 ~12:10, ok do dono): os 8 arquivos de
   `...20261013_1515...` e `...20261015_0407...` (669 MB). Os registros de postagem do canal antigo ficaram; o
   catálogo do postador ainda os lista como "no PC" até o próximo `catalogo.sincronizar()` (o `backup_drive.py` pula
   arquivo que sumiu).
5. **Revisor: rigor e oscilação — decisão do dono.** O dono olhou o cap 1 das 10:15 e aprovou; a análise reprova 5-6
   quadros desse mesmo vídeo (cenas de lingerie/corpo com mosaico) e o modelo oscila entre rodadas (0:55 reprovou na
   1ª e passou na 2ª; 420 s e 430 s o contrário). Opções: (a) manter "1 sim em 3 opiniões" (mais seguro, mais
   refeitos); (b) "2 sins em 3"; (c) no 1º reprovado REFORÇAR o mosaico (bloco maior, folga maior) em vez de fosco, e
   fosco só no 2º — combina com "mosaico primeiro".
6. **Corrigido nesta sessão (16/10):** revisor 3,7x mais rápido e com o painel certo (`revisao_video.py`, ver
   CLAUDE.md); `--liberar` chamava a liberação 3 vezes e apagava o registro do que a análise achou; o
   `lancamento_pt.py` não gravava `pt_completo_em`/`pt_shorts_ok` (a fila postaria o cap 1 de novo); painéis 007/102/103
   tirados da lista de fosco forçado (entraram pelo mapa errado).
7. **Cap 1 do Manhwa Noturno**: o dono aprovou a versão das 10:15 (`--liberar`, 11:29); o estado do cap 1 aponta pra
   ela (pronto, análise ok liberada pelo dono). Falta só o dono logar a conta (janela aberta pelo `cofre.py logar
   inovaremanhwaverse2`); depois: `pythonw bin/lancamento_pt.py` (completo -> 16:9 -> Shorts; ele grava
   `pt_completo_em`/`pt_shorts_ok`). NÃO religar o robô antes do login: ele abriria o mesmo Chrome da conta no meio do
   login. O refeito das 11:25 (`...20261016_1125...mp4`, sem meta, fosco nos painéis inocentes) ficou órfão: não usar.
   **Lote**: o `refazer_caps` das 10:01 parou sozinho entre 11:41 e 12:07 (depois do passe final do refeito, sem log
   de fim). Religado às 12:15 via WMI, fora de qualquer sessão: `refazer_caps.py 2-11 --so-longo 1` (16:9 do cap 1,
   depois caps 2-11; log `logs/refazer_caps.log`).
8. **TERCEIRO CANAL, só +18 (pedido do dono, 16/10) — A FAZER.** Em vez de marcar +18 nos canais atuais (corta o
   alcance deles), um canal novo dedicado, com TODO vídeo subindo com restrição de idade (+18) marcada pelo próprio
   canal. Atenção: +18 não libera nudez no YouTube (a regra de nudez/conteúdo sexual vale igual); serve pra cena
   sugestiva (lingerie, insinuação, mosaico) que hoje reprova na análise ou corre risco nos canais abertos. Falta:
   (a) o dono criar o canal e logar a conta no cofre (`D:\logins-google\cofre.py logar <conta>`); (b) o
   `youtube_web_poster.py` marcar "Restrição de idade (avançado) → Sim, maiores de 18" no upload (hoje não marca em
   lugar nenhum; só "não é para crianças" e "conteúdo alterado (IA)"); (c) `config/fila.json`: canal, handle e marca
   d'água do canal novo; (d) decidir com o dono o que vai pra lá (ex.: os capítulos/cenas que a análise reprova por
   mosaico fraco) e se a análise usa um critério próprio pra ele.
9. **Retomada da análise total (16/10).** Feitas: revisor (lento e painel errado), mapa do meta (causa raiz no
   `fx_clips`), backup, disco (vídeos do hipercool = 15,7 GB; o aperto do D: vem de fora), login dos canais, opções
   do upload (+18/IA/crianças), renders antigos, disputa de máquina (o `anime_night_shift.py` do recapd está parado
   desde 08:03 com 0 de CPU — outro projeto, monitor dele falhando), robô de lançamento e estado. FALTAM: (a) arquivos
   de estado com vários processos — o `fila.gravar_estado` já mescla, conferir os outros JSON (`_forcar_fosco.json`
   grava sem trava nem troca atômica, `limitador.json`, `model_health.json`, `intros_voz_stats.json`, postagens);
   (b) dados de crescimento sem o Studio (views/likes públicos via yt-dlp por canal, língua, tipo e horário);
   (c) falhas por cota/429 nos logs (`gemini-tts.log`, análise "incompleto") e quanto tempo custam; (d) histórico do
   dono (conversas em `C:\Users\Haylla\.claude-vscode\projects\d--\*.jsonl`: pedidos repetidos e reclamações).
   Cada frente: anotar o achado AQUI assim que confirmado, antes de passar pra próxima.
10. **Lista da outra sessão assumida por claude-be (dono, 16/10 ~12:30: "faça 9").** Ordem (o que roda na hora de
    postar primeiro; o que mexe no render só depois que o lote terminar, ~meia-noite). Status — atualizar a cada passo:
    - [ ] Shorts (`split-shorts.py`, achados shorts-02/03/10/11 em `workspace/tmp/auditoria_15out/grupos/g4_shorts.json`) — **CORRIGIDO 16:07, EM TESTE**:
      - [x] um encode por parte (era 3: part_raw + cta_clip + concat final);
      - [x] sem cartão final mudo/estático: overlay PNG transparente com a música continuando, fade-in + escurecimento;
      - [x] "FIM DO CAP. N" na última parte (antes era "CONTINUA" em todas);
      - [x] quadro limpo na abertura: `escolher_frame_limpo` busca visualmente (scene cut) nos primeiros 4 s (deriva do mapa: shorts-10);
      - [x] carimbo "CAP. N | PARTE i" no vídeo (drawtext no canto superior esquerdo, 32px branco borda preta).
      Teste: `workspace/tmp/teste_shorts_16out` (cap 1, 5 partes esperadas, rodando em background task bi3txpptf).
      Se passar: copiar para PC2 antes das 18h (o `lancamento_pt` vai cortar os Shorts do cap 1 às 18-23h).
      **16/10 15h20 — os Shorts do cap 1 NÃO dependem mais deste teste.** O dono mandou postar os 5 de
      `Área de trabalho\Hipercool\SHORTS NOVOS (ver como ficaram)` (cortados às 11:15 do completo das 10:15): **2 hoje
      e 3 amanhã ao longo do dia** (~10h, ~15h, ~20h). Eles estão em `workspace/shorts/the-inheritor-cap1/` com um
      `meta_shorts.json` cujo `_fonte` é o completo das 10:15 (o `cortar_shorts` reaproveita e não corta de novo); o que
      havia lá foi para `_antes_16out_15h/`. Quem posta: `bin/shorts_a_cada_2h.py` (tarefa `HipercoolShorts2h`, a cada
      20 min; log `logs/shorts_2h.log`; desliga sozinha no fim). O `lancamento_pt` agora termina no 16:9 (não posta
      mais Shorts) e roda numa cópia só (havia duas). **Não cortar de novo nem trocar os arquivos dessa pasta até os
      5 subirem (17/10 à noite)** — o split-shorts em teste deu parte 5 com 433 s e erro de `UnicodeEncodeError` às
      15:01. O `postar_shorts_agendado.py` + `HIPERCOOL_POSTAR_SHORT_CRON.txt` de outro agente nunca rodaram (cron não
      existe no Windows) e subiriam todos de uma vez: ficaram desativados.
      Achado no caminho: `D:\postador-de-videos\logs\yt_web.lock` (a `Trava` do `youtube_web_poster`) estava órfã desde
      13:30 (dono do lock morreu sem soltar). Todo upload pelo navegador esperava 20 min e falhava até ela fazer 3 h
      (16:30). Apagada às 15:25 (ninguém estava com ela aberta). Ideia: a `Trava` gravar o PID e soltar se ele morreu.
    - [ ] SEO por língua (shorts-08 em `g7_seo.json`): tags/palavras de busca no idioma do canal.
    - [ ] Efeitos 2.5D (`fx_parallax.py`, `g3_parallax.json`: balão cortado no zoom, rosto grande descartado, espelho
      invertendo texto) — SÓ DEPOIS DO LOTE.
    - [ ] Estudo dos narradores (piadas/jargões dos 15 canais; ferramentas em `D:\hipercool-materiais\referencias_narradores\`).
    - [x] Short de RESUMO (gerado desde 16/10; POSTADO por último desde 23/10, ordem da dona, só pt). Falta: voz local de reserva no PC2; narrador por obra; vozes proibidas no historias-em-frames;
      compilado com narração extra (caps 1-5).

### 3-ATUALIZAÇÃO (15/10 20h): extras BLOQUEADOS PELA CONTA DO YOUTUBE — só o dono resolve (NÃO está feito)

(16/10: o "✅ FEITO" que estava aqui era engano — isto é bloqueio da conta, só o dono resolve. A remoção do nome da obra
é o item 5b.)

- Canal pt (InovareManhwaVerse): a verificação que estava "em análise" foi NEGADA. Ao fixar comentário aparece
  "Os recursos avançados não estão disponíveis — Acreditamos que você violou as políticas do YouTube antes…
  pedir acesso novamente em 14 de novembro de 2026; contestação até 14 de dezembro de 2026" (print em
  `D:\postador-de-videos\logs\yt_web\20261015_164956_comentario_fixado.png`). Bloqueia: comentário fixado, vídeo
  relacionado, teste A/B. O DONO decide se contesta (botão "Contestar" no Studio) — o agente não contesta.
- Canais de língua: pra ligar Short ao vídeo pedem a "verificação única" (telefone) — o dono faz em Studio →
  Configurações → Canal → Qualificação de recursos.
- Código: `youtube_studio_extras._bloqueio_conta` reconhece as duas telas e devolve "bloqueado: …"; o
  `postar_hipercool._extra_pendente` só tenta de novo depois da data ("até 2026-11-14") e nunca no caso da
  verificação única (depois que o dono verificar: apagar o "status" desses extras nos `workspace/postagens/*.json`).
  Os 35 extras já tentados foram marcados assim (a postagem parou de abrir o navegador por eles).

### 3. Extras do Studio que dependem da verificação do canal
- **Pedido**: teste A/B de capa, tela final/playlist, comentário "SEM CENSURA" fixado, vídeo relacionado e
  apagar rascunhos — também nos Shorts.
  - "Pode ir usando nos canais que já estão liberados."
- **Estado**:
  - Funcionando e conferido: tela final (cap 1 pt), limpeza de rascunhos (10 apagados) e postar comentário.
  - Pendentes porque o canal pt está em "A verificação por vídeo está em análise" (~24 h a partir de 15/10 de
    manhã): fixar o comentário, vídeo relacionado e teste A/B.
  - Roda sozinho: `fila.postagem` → `postar_hipercool.rodar_extras` (3 vídeos por rodada, repete pendente a cada 3 h).
    - Plano por vídeo em `workspace/postagens/*.json` → `extras`.
    - Já preenchido para o que subiu em pt e nas línguas.
- **Fazer** quando o canal liberar:
  - As telas do teste A/B e do "Vídeo relacionado" NUNCA foram vistas além do aviso de verificação. O código
    tenta de forma genérica e tira prints (`D:\postador-de-videos\logs\yt_web\*ab_dialogo*`,
    `*relacionado_dialogo*`).
  - Abrir os prints da 1ª tentativa e acertar os seletores em `youtube_studio_extras.py` (`teste_ab`,
    `relacionado`).
  - Conferir no vídeo que ficou "Fixado por @InovareManhwaVerse".
- Manual: `PYTHONUTF8=1 venv/Scripts/python.exe bin/postar_hipercool.py --extras`.
- Canais de língua: os extras já foram planejados (tela final + relacionado). Ver se rodam lá e se alguns já são
  verificados.

### 4-ATUALIZAÇÃO (15/10 20h): `bin/metricas.py` (novo) — leitura no Studio pelo navegador — PARCIAL, não validado

**16/10 (revisado)**: só **visualizações** e **duração média** foram lidas de verdade (2 de 3 vídeos; o 3º deu "Ops!
Algo deu errado"). **Impressões, CTR e retenção aos 30 s — que são o que decide título e abertura — nunca foram lidos**
(os vídeos tinham 3 views) e `workspace/metricas.json` continua vazio. Só dá pra dizer que funciona quando um vídeo com
100+ impressões tiver CTR e retenção lidos e conferidos com o Studio. Os vídeos do canal pt antigo agora estão
privados; medir no canal novo. PC2: os arquivos estão iguais aos do PC1 (md5 conferido 16/10).

- Lê impressões, CTR, views, duração média e retenção aos 30 s dos vídeos LONGOS (completo e compilado) postados há
  2-21 dias (6 por rodada, 1 rodada por dia, chamado no fim da `fila.postagem`); guarda em `workspace/metricas.json`.
- Decide com 7+ dias e 3+ vídeos medidos: retenção 30 s acima da mediana dos compilados = vitória da fala de voz
  humana (`intros_voz.registrar_resultado`); CTR acima da mediana dos completos do canal (100+ impressões) = vitória
  do estilo de título (`seo.registrar_resultado`). Teste A/B: bloqueado (ver 3-ATUALIZAÇÃO).
- A leitura das telas é `youtube_studio_extras --metricas` (testado 16/10: b3837hIphag views=3, dur_media=107s; h-0gDOsA7OY views=3, dur_media=6s; zuBKb2CXSro retornou erro genérico "Ops! Algo deu errado").

### 4. Medir o que rende (capas e títulos)
- **Pedido**: "vamos testar todas e medir qual tem as melhores respostas"; títulos "temos que fazer um estudo
  disso também".
- **Estado**: os pesos existem mas ninguém alimenta.
  - Capas: `capa_ia.registrar_teste` (chamado quando o teste A/B começa) e `registrar_vencedora` (NÃO chamado).
  - Títulos: `seo.registrar_resultado` (NÃO chamado); o estilo usado fica em `completo.estilo_titulo`.
- **Fazer**:
  - Leitor do Studio pelo navegador: resultado do teste A/B (capa vencedora) e CTR/visualizações por vídeo em
    48 h.
  - Ligar em `registrar_vencedora(capa_json, idx)` e `seo.registrar_resultado(estilo, venceu)`.
  - Critério sugerido: CTR acima da mediana do canal.
  - Também é o antigo "item 1" (analytics do próprio canal pelo Studio).

### 5. Voz humana no começo do vídeo longo (compilado 16:9) ✅ FEITO
- **Pedido**: o feed toca o começo no hover e o público usa isso pra ver se é voz de IA. Quer uma voz humana
  logo no início: "se inscreva, deixe seu like", "a nossa história começa com…", avisos.
  - 15/10: 15 canais autorizaram o uso da voz deles (Porão, Mangáticos, Mattz, Sr. Guugou, Momo, Mike, Drezin,
    O Melhor Manhwa, KkVirjão, Doinsuka, iJax, Solem_8037, Jubertim, Iki, solem_sun).
  - "Analise essas aberturas, quais podemos usar, mixar pra não ficar estranho, sem o nome deles (ou corta o nome);
    cada compilado com uma abertura diferente pra testar qual fica melhor."
- **Feito (15/10)**: `bin/intros_voz.py` + `config/intros_voz.json` + ligado no `hiper-longo.compilar()` e no
  `postar_hipercool.postar_longo` (ver CLAUDE.md, "Abertura com voz humana no compilado").
  - Colheita: começo (150 s) e fim (75 s) de 4 vídeos longos por canal, transcritos no Groq.
  - Abertura montada só com fala genérica de UM criador: voz separada da música dele, corte no silêncio, nossa trilha.
  - Vídeo da abertura testado: mesmo formato do cap 1, emenda sem re-encode decodifica sem erro.
- **Feito (15/10 à noite, pedido do dono depois de ouvir)**: "ficaram boas", mas (a) "o começo fica estático a
  imagem" → a tela agora tem MEMES ANIMADOS (gif/mp4 do catálogo do fx_memes) SEM som trocando junto com a fala,
  sobre a capa desfocada (a capa nítida só no 1º meio segundo, pra prévia do feed continuar a miniatura); (b)
  "algumas ficavam melhor no meio, já que tem esse momento de like" → campo `lugar` ("abertura" | "meio") em cada fala
  de `config/intros_voz.json`: 4 falas de "meio" (mike_r1, drezin_2, mattz_2, mattz_r1) entram numa troca de
  capítulo perto de 1/3 do compilado (nunca antes de 4 min), de outro criador que não o da abertura;
  `meta["intro_meio"]`. Porão (3 falas) montado e ativo (dono: "é humana, posso confirmar ouvindo"). Testado num
  compilado de verdade (caps 1-5 numa pasta temporária): emendas conferidas, capítulos deslocados certo.
  Prévias: área de trabalho `Hipercool\ABERTURAS COM VOZ HUMANA (ouvir)` (COMEÇO/MEIO no nome do arquivo).
- **Falta**:
  - Medir: leitor da retenção aos 30 s no Studio → `intros_voz.registrar_resultado(id, venceu)` (junto do item 4).
  - Completo vertical por capítulo (também é vídeo longo no feed): hoje sem abertura. Se o dono quiser, prefixar
    na hora de postar (o arquivo do completo também gera os Shorts, então não dá pra mexer nele).
  - Canais novos que o dono conseguir: pôr em `autorizados` com os nomes, `colher`, escolher, `montar`.

### 5b. Nome da obra em LUGAR NENHUM (dono, 15/10 à noite) — ✅ FEITO (16/10)

**16/10 (revisado)**: títulos sem o nome da obra no ar (`_sem_nome_da_obra/RESULTADO_FINAL.txt`: 34 + 3 correções).
O agente anterior tinha posto **título em português** no completo hindi `BGjF_MKZGsw` e no tailandês `G-DpRVvi5RM`
("problema de encoding" — era só o terminal); voltaram pros títulos em hindi/tailandês já planejados (conferido no
YouTube em UTF-8). O Short indonésio `_Pn7LzkP9rE` tinha título e descrição em português desde o upload: trocados
por indonésio. Os Shorts de hindi/indonésio/vietnamita terminavam com "(Parte N)" em português: trocado por
भाग/Bagian/Phần em 12 Shorts, e o `seo.pacote(... "shorts")` agora corrige isso sozinho (o exemplo do prompt era copiado).

Pedido: "as playlists não podem ter o nome da obra, lembra que nenhum lugar pode ter o nome da obra, pode trocar
para o novo padrão (títulos com reencarnado etc.)"; "não precisa renderizar nada de novo pra tirar o nome, o que
está feito está, é só o que der pra renomear"; "pode fazer essas mudanças no YouTube Studio depois".
- **Feito**:
  - Playlists renomeadas no Studio e conferidas (8): pt "The Inheritor — Recap" e "— Maratona" + id/it/ru/th/vi
    "— Recap". Nomes novos (padrão de título, gerados por `seo.nome_playlist`) GRAVADOS em `config/fila.json` →
    `obras[].playlists[língua][recap|maratona]`; `postar_hipercool._nome_playlist` lê de lá (nunca mais f"{obra} —").
    A "The Inheritor — Recap" duplicada e VAZIA do pt virou "Playlist vazia (pode apagar)" — apagar só com ok do dono.
  - Planos de tela final (`workspace/postagens/*.json` → `extras.tela_final.playlist`) trocados pros nomes novos.
  - Código (vale do próximo render em diante; o que já está renderizado NÃO vai ser refeito, ordem do dono):
    selo do vertical agora é só "CAP. N" (`fx_acabamento.montar_ass`); cartão do longo só "CAPÍTULO N"
    (`hiper-longo._titulo_capitulo`); `nomes_proibidos` com o nome traduzido (O Herdeiro, Наследник, उत्तराधिकारी,
    L'Erede, Pewaris, Người Thừa Kế, ทายาท, L'Héritier). O cap 10 (render começou 19:00) ainda sai com o selo antigo.
  - **Vídeos já postados (16/10)**: atualizados via navegador (ver a revisão de 16/10 logo acima — os títulos em
    português do hindi/tailandês/indonésio foram corrigidos).
  Os textos novos JÁ ESTÃO PRONTOS e conferidos (sem o nome, nem traduzido): um arquivo por canal em
  `workspace/postagens/_sem_nome_da_obra/<canal>.json` ([{video, titulo|null, descricao, tags}]). Os textos antigos
  (pra desfazer) estão em `workspace/postagens/_backup_metadados_antes_sem_nome_15-10.json`.
  Rodar UM canal por vez (cada um abre o Chrome daquela conta; o navegador tem trava, espera a postagem):
  ```
  cd /d/postador-de-videos
  PYTHONUTF8=1 /d/hipercool-videos/venv/Scripts/python.exe bin/youtube_studio_extras.py \
      --canal <CANAL> --metadados /d/hipercool-videos/workspace/postagens/_sem_nome_da_obra/<CANAL>.json
  ```
  `<CANAL>` = nome do arquivo sem .json: inovaremanhwaverse (8), inovaremanhwabr (3, canal pt antigo),
  GtuH5ezUK8eBaC60 (hindi, 8), nYsAKUb3DbR1QOEm (indonésio), 7zpNZNll2jlBnQ0J (italiano), TkfzifstYEoG4jKg (russo),
  q3mik36FjtTgFkNC (tailandês), 8ROQmZVjbpwiwMoX (vietnamita) — 3 cada. A última linha é
  `RESULTADO: {"metadados": {"<id>": "ok" | "aviso: ..."}}`; "ok" = salvo e conferido no Studio. Aviso → print em
  `D:\postador-de-videos\logs\yt_web\`. Teste com `--ensaio` primeiro se quiser (não mexe em nada).
  Conferir depois pelo público: `yt-dlp --skip-download -j https://youtu.be/<id>` (título/descrição/tags sem o nome).
  Ao terminar um canal, apague o arquivo dele da pasta `_sem_nome_da_obra` (o que sobra = o que falta).

### 6. Playlists com o nome da obra — RESOLVIDO em 15/10 (ver 5b)
- As playlists "The Inheritor — Recap" e "The Inheritor — Maratona" são públicas e levam o nome da obra (o dono
  proibiu o nome no título por direitos autorais).
  - Perguntado em 15/10: renomear pra algo como "Ele Herdou uma Garota — Recap"? Sem resposta.
- Há uma "The Inheritor — Recap" duplicada e vazia no canal pt. Apagar só com ok do dono.
- Se renomear: o nome está em `postar_hipercool.py` (`playlist = f"{obra} — Recap"`, `— Maratona`) e nos planos
  `extras.tela_final.playlist` já gravados em `workspace/postagens/*.json`.

### 7. Capas de fantasia (obras de fantasia/ação que vierem na fila)
- **Pedido**: nos testes A/B, além das poses sensuais, "poses de fantasia": batalha, golpe de espada, luta
  contra alguém/monstro, cobrindo os subgêneros da obra — alternativa pra outro público, sem largar as sensuais.
- **Estado**:
  - Pronto em `capa_ia.POSES_GENERO`. Entra 1 variante de batalha quando a obra tem um gênero de ação em
    `config/fila.json` → `obras[].generos` (fantasia, acao, murim, apocalipse, sistema, regressao,
    reencarnacao, realeza…).
  - The Inheritor não tem esse gênero. Nunca testado com imagem.
- **Fazer**:
  - Ao cadastrar obra nova, preencher `generos` (as mesmas chaves de `config/seo_palavras.json`) e
    `nomes_proibidos`.
  - Na 1ª obra de fantasia, conferir a capa de batalha e mostrar ao dono.

### 8. Títulos/descrição/tags — acompanhar
- **Feito em 15/10**:
  - sem o nome da obra (`seo._sem_obra` + modelo fixo);
  - banco de palavras do autocompletar real;
  - 3 estilos de título em rodízio.
  - Conferido no ensaio do cap 2 (nenhum título com o nome).
- **Fazer**:
  - Refazer a pesquisa de palavras para cada gênero novo (`docs/seo_titulos.md`).
  - Conferir nos primeiros posts reais (título, descrição sem #TheInheritor, chamada SEM CENSURA no 2º
    parágrafo da descrição em pt).
  - Vídeos já postados com o nome da obra no título (cap 1 pt e as línguas): perguntar ao dono se troca o título
    no Studio.

### 9. Levar as melhorias para os outros projetos
- **Pedido**: tudo isso documentado como leitura obrigatória no react manhwa, no histórias em frames e nos outros,
  pra quando o dono mexer neles o agente aplicar (ou copiar daqui).
- **Estado**:
  - Feito: `LEIA_MELHORIAS_HIPERCOOL.md` + aviso no `CLAUDE.md` de `D:\manhwa-react`, `D:\historias-em-frames`
    e `D:\recapd-ambientes`.
- **Fazer**: ao mudar regra aqui, atualizar `docs/MELHORIAS_PARA_TODOS_OS_PROJETOS.md` e recopiar para os 3.

### 9a. Marca do scan (BLACKOUTCOMICS.COM) nos caps 1-6 (15/10 20h) ✅ FEITO
- O 16:9 do cap 2 saiu com o carimbo "BLACKOUTCOMICS.COM — aqui você lê…" no último painel: os caps 1-6 foram feitos
  antes do `bin/marca_scan.py` existir (a fila só limpa antes de renderizar, desde o cap 7).
- Feito: `marca_scan.limpar_pasta` nos caps 1-6 (108 painéis; originais em `<pasta>/_originais/`). NADA foi
  renderizado de novo (ordem do dono); vale pro que ainda for feito desses capítulos (16:9 do cap 6, capas).

### 9b. Groq com as chaves novas e pelo proxy Webshare ✅ FEITO (manhwa-react pendente)
- **Pedido**: "adicione essas [6 chaves novas] e use com proxy webshare".
- **Feito**: chaves 4–9 em `D:\postador-de-videos\secrets\groq_keys.json`; a chave 1 dá 401 e foi marcada
  `"invalida"`; 2–9 respondem 200 pelo proxy. `bin/groq_api.py` (rodízio + proxy obrigatório) usado pelo
  `fx_acabamento` (tempo por palavra, agora em FLAC) e pelo `intros_voz`.
- **Falta (baixa prioridade)**:
  - o manhwa-react (`mr/transcribe.py`) usa as mesmas chaves e ainda chama direto — atualizar quando mexer no manhwa-react;
  - o PC2 não tem chave do Groq: lá o tempo por palavra é proporcional. Ligar só depois de testar as línguas
    (tailandês não tem espaço entre palavras e o alinhamento pode errar).

### 10. Outros que ficaram
- **Compilado 16:9 com mais narração**: caps 1–5 só ganham as frases extras se refizer
  (`hiper-longo.py --refazer`, ~60 vozes Gemini). Fazer quando a cota de TTS permitir.
- **Pergunta antiga ao dono ("item 9")**: a estratégia de cota do Gemini (roteiro estendido pro 16:9 custa
  LLM + TTS por capítulo) continua sem resposta.
- **Hindi**: as `part_03..07` estão num estado sem o "completo" (ele ficou no arquivo antigo, sem sufixo), então
  ficaram sem "vídeo relacionado". Dá pra apontar à mão pro completo `BGjF_MKZGsw` se o dono quiser.

---

## Feito em 15/10 (não refazer)
- `D:\postador-de-videos\bin\youtube_studio_extras.py` (novo) + `rodar_extras`/`_extras_de` no
  `postar_hipercool.py` + chamada no `fila.postagem`.
- `capa_ia.py`:
  - plano de texto sem descrição de pose/lingerie (era recusado pelo Gemini e pelo Claude);
  - roupa sorteada no código;
  - `capas_short` 9:16;
  - `POSES_GENERO`;
  - `_reprovada(chk, pose)`.
- `seo.py` v2: regras novas, `_palavras`, `_sem_obra`, 3 estilos, `escolher_estilo`/`registrar_resultado`.
  `config/seo_palavras.json` (novo). `config/fila.json`: `generos` e `nomes_proibidos` do The Inheritor.
- Docs: `MELHORIAS_PARA_TODOS_OS_PROJETOS.md`, `seo_titulos.md`, este arquivo; `CLAUDE.md` atualizado.
- PC2 recebeu `capa_ia.py` e `seo.py`.

### 11. Vozes: ordem de fallback, vozes locais, narradores variados (dono, 15/10 ~9h30)
Amostras ouvidas pelo dono: `Área de trabalho\Hipercool\AMOSTRAS DE VOZ`. Gostou da **edge AndrewMultilingual** em pt.
A edge **Antonio NUNCA mais** (voz masculina ruim).
- **Feito (15/10)**:
  - `edge_tts_engine.py`: Antonio -> en-US-AndrewMultilingualNeural.
  - `gemini_tts.TTS_MODELS`: 3.1 -> 3.8 -> 3.8-lite -> 3.1-lite -> 2.5.
  - PC2 atualizado.
- **Ordem desejada**: Gemini 3.1 (todas as chaves) -> Gemini 3.8 (todas as chaves) -> edge nova (AndrewMultilingual /
  multilíngues) ou local. Só que essa cadeia de tentativas pode demorar mais que gerar local direto. Medir o tempo
  de cada degrau e decidir.
- **Personagem não pode trocar de voz** no meio do capítulo/série quando cair no fallback: fixar o motor por
  personagem e por capítulo. Se cair, o capítulo inteiro vai pro degrau seguinte.
- **Local SÓ como reserva** (o dono não quer que atrase a produção): quando todos os limites do Gemini baterem, ou
  para algumas vozes. Rodar no PC2 em paralelo (dividir o trabalho), não no PC1.
  - Teste no PC1, CPU, com render rodando junto: Supertonic-3 ~1,5x tempo real (pt, hi, id, it, ru, vi; sem th);
    Kokoro (pt, hi, it); VieNeu (só vi) 0,5x.
  - Venv de teste em `D:\tools\tts-teste`, script `D:\tools\testar_vozes.py`.
- **Falta**:
  - Ranking completo (qualidade x velocidade) e estimativa de quanto tempo o local acrescentaria por capítulo.
  - Pesquisar mais modelos: OmniVoice, VoxCPM2, MOSS-TTS-Nano, Qwen3-TTS, Chatterbox. OmniVoice e VoxCPM2 precisam
    de GPU NVIDIA; ver se o outro PC (desktop-su00b7v) tem.
- **Narrador variado por obra** (pra não ficar igual em tudo) e vozes diferentes nos compilados.
- **Abertura com voz humana**: feita com vozes de canais que autorizaram (item 5).

#### 11b. Atualização 15/10 ~10h30 (decisões do dono depois de ouvir as amostras)
- **Feito**:
  - `bin/elenco.py`: elenco fixo por obra + motor do pt; `config/fila.json` `tts_motor: "edge"` (próximo vídeo pt
    só com edge, a partir do cap 9).
  - Elenco do The Inheritor em `config/elenco/the-inheritor.json`: narradora Thalita +5%, Joo Inhyuk = Andrew,
    Noh Yeseul = Ava, Professora = Seraphina. Os nomes Gemini antigos ficaram guardados.
  - Normalização do "Rapaz"/"Jovem" que é o protagonista.
  - Proibidas Antonio/Francisca/Isabella.
  - `bin/sem_janela.py` (sem janelas de cmd/python na tela) no `fila.py` e no `backup_caches.py`.
  - PC2 atualizado. Docs copiados para manhwa-react, historias-em-frames e recapd-ambientes.
  - Demo do elenco: `Área de trabalho\Hipercool\AMOSTRAS DE VOZ\0 - ELENCO THE INHERITOR (teste edge, trecho do cap 8).mp3`.
- **Conferir no cap 9 (1º vídeo só edge)**:
  - log `TTS[edge]`;
  - tempo da etapa de voz (esperado ~10 min);
  - mostrar ao dono e perguntar se fica.
  - Se ficar: decidir a narradora de cada obra nova (variar) e os compilados com voz diferente.
- **15/10 ~12h**: o render do cap 8 com o Gemini (09:40) FALHOU às 10:30 (o log foi sobrescrito pela nova
  tentativa; motivo perdido). A fila refez o cap 8 às 10:40 já com o motor edge: o cap 8 é o 1º vídeo só edge (voz
  inteira em ~16 min). Conferir o resultado e mostrar ao dono.
- **15/10 14h**: o passe final do cap 8 travava sempre aos 19 s (ffmpeg 8 + emojis como `-loop 1` imagem). Corrigido
  em `fx_acabamento._clipe_parado` (copiado pro PC2); a fila refaz o cap 8 com a correção.
- **Falta**:
  - local (Supertonic-3) como reserva no PC2;
  - aplicar o elenco fixo também nas outras línguas (hoje `idiomas._perfil`, md5 por nome, sem normalizar
    apelido);
  - trocar as vozes proibidas no código do historias-em-frames (bin/, beta/, prod/, teste/) quando o dono for
    mexer lá.
