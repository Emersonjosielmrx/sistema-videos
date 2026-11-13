# Melhorias entre projetos — recapd-ambientes, historias-em-frames, manhwa-react

**Origem**: D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md
**Pedido**: "pegar o melhor de cada um com as coisas que o outro ja tem assim podemos economizar muitos tokens em vez de construir do 0"
**Última revisão**: 16/10/2026 ~07:00 — revisão do trabalho de 16/10 madrugada, conferida com teste real (gateway, imagens, logs).

---

## Como cada vídeo chega no YouTube (conferido em 16/10 — o mapeamento de antes estava errado)

| Projeto | Quem gera o postar.json | Quem posta | Observação |
|---|---|---|---|
| recap de anime (recapd-ambientes) | `bin/anime_auto.py` → `bin/anime_publish.py` → `D:\hipercool-materiais\animes recap\...\postar.json` | `D:\postador-de-videos\bin\postar_tudo_hoje.py` (tarefa PostadorDeVideos) | `postar_animes.py` é legado, NÃO está agendado |
| historias-em-frames | `bin/story_pipeline.py` (`_write_postar_json`) → `D:\hipercool-materiais\historias-em-frames\...` | rede do manhwa-react (`manhwareact.py rede`, `mr/rede.py`) — o agente de cada canal reescreve título/comentário em cima do postar.json | `postar_historias.py` é legado, NÃO está agendado |

---

## ✅ Corrigido na revisão de 16/10 (o que o outro agente tinha feito errado)

1. **Quebrava os dois pipelines**: `claude_client.py` e `gemini_llm.py` do hipercool foram copiados POR CIMA dos do recapd e
   do historias — sumiram `generate_text`, `read_balloons`, `audit_with_truth`, `strong_model`... (roteiro do anime,
   publicação, narração das histórias). **Restaurados do git** nos dois projetos.
2. **Gateway velho**: no recapd a chave padrão do `claude_client` foi desativada (403) e o modelo
   `antigravity/gemini-2.5-flash` saiu do catálogo (historias também). `secrets/omniroute.json` dos dois →
   `antigravity/gemini-3-flash` + chave do gateway (backup `.bak_16out`). Testado: responde.
3. **historias `gemini_llm`**: 1º modelo do gateway (`gemini-3.1-pro-high`) saiu do catálogo → cada chamada perdia tempo;
   trocado por `antigravity/gemini-3-flash` (visão 6 s; antes ~4 min no total).
4. **SEO ligado no lugar errado**: estava em `postar_animes.py`/`postar_historias.py` (legados, não rodam). Agora:
   - anime: `anime_publish.py` usa `seo_generator.gerar_seo_anime` (fallback: prompt antigo, com o nome da obra apagado);
   - histórias: `story_pipeline._write_postar_json` usa `seo_generator.gerar_seo_historia` (fallback: crew/viralizador).
5. **SEO das histórias não recebia a história** (só "terror"/"superacao" + caminho do arquivo → título genérico que
   promete o que não acontece). Agora recebe gênero, tema, título e narração. Banco `config/seo_palavras.json` ganhou
   drama/romance/comédia/religioso pelo autocompletar real do YouTube.
6. **Nome da obra no anime**: o filtro apagava o título INTEIRO do vídeo-fonte (inútil). Agora o LLM devolve
   `nomes_da_obra` (inglês, português, original, apelidos) e título com qualquer um deles é descartado (pegou
   "O HERÓI DO ESCUDO" no teste). Títulos cortados no meio ("…e o que SUBIU") e tags cortadas ("…se torno") corrigidos.
7. **`postar_historias.py` quebrado**: passava `--thumbnail` pro `youtube_poster.py`, que não aceita → todo upload com
   capa falharia. Revertido pro original (git).
8. **Capas**:
   - histórias são Shorts **9:16** (720x1280) — a capa era 16:9; e a pose era sorteada sem olhar a história
     (12 poses × 5 roupas + cache = capas repetidas). Agora: cena da própria história + clima do gênero + frase do SEO;
   - anime: `capas_anime.json` só tinha 7 animes (o resto caía num herói genérico) e a capa saiu com o símbolo da Folha
     na bandana. Agora o protagonista vem do SEO (`protagonista_visual`), sem emblemas; 9:16 no Short;
   - as duas: **checagem por visão** copiada do hipercool (letra/logo, sangue, cara de menor, tela dividida → tenta
     outra pose, até 3), **frase grande** (LuckiestGuy, contorno preto), JPEG < 2 MB;
   - removido "school uniform" das roupas (proibido) e "clothes torn" de uma pose; pronome HE/SHE corrigido.
9. **Capa não chegava no YouTube**: `postar_tudo_hoje.py` agora manda o `"thumb"` do postar.json; `mr/rede.py` aceita a
   capa das histórias (antes só react).
10. **`studio_extras_anime.py`** criava playlist "One Piece Recap"/"Naruto Recap" (nome da obra) → removido.

## ✅ Faltava e foi feito em 16/10

- **Anime parado desde agosto** (347 falhas seguidas): `workspace\anime` aponta pra `D:\hipercool-materiais\anime`, que
  tinha sumido → `mkdir` quebrava no 1º candidato. Pasta recriada e `_feitos_*.txt` **reconstruídos** do histórico
  (pipeline_metrics, postados) pra não refazer vídeo já postado. E o `discover(top=2)` cortava antes de filtrar os
  feitos ("nenhum candidato" com 841 na lista) — agora filtra antes.
- `anime_auto` passa título-fonte + roteiro pro `anime_publish` e o tempo dele subiu de 120 s pra 900 s; o postar.json
  é gravado ANTES da capa (se a capa demorar, o vídeo não fica sem metadata).
- **§4b vozes no recapd**: narração era Francisca → Thalita Multilingual (nota: Francisca liberada novamente pelo dono em 16/10, é a base da voz clonada; só Antonio continua proibida); Antonio → Andrew/Brian/William;
  `hash()` → md5 (mesma troca já feita no historias).
- **edge-tts 7.2.8 dava 403** em todas as vozes (recapd e historias) → atualizado pra 7.3.1 (a do hipercool).

## ✅ Trilha do hipercool → react e historias (Onda 2.2, claude-20, 16/10 tarde)

- **react `mr/music.py`**: nos 30 vídeos dos últimos 10 dias saíram "Undertale Sound Effect - Taking Damage", Funk das
  Winx 4×, Pokémon/Mario Kart/Zelda/Minecraft. Agora: filtro de lixo + faixa ≥ 1 min, `prefer_priority` (estava no config
  e o código ignorava) = ~85% prioritárias com clima do `climas.json`, sem repetir as últimas 16. Simulação 200×/clima:
  lixo 14→0 no neutro, engraçado 1→4 faixas, repetição seguida ~0. Remix real (work/2026_10_07_15_50_45 parte 2):
  -14,2 LUFS com e sem trilha, música -33 dB nas pausas, voz +0,3 dB. Mix não mudou.
- **historias**: o `story_pipeline` NÃO usava o `fx_music` — mixava na mão (sorteio cru sem blocklist, volume fixo 0.12
  sem ducking, `amix` que derruba a narração 6 dB, corte seco entre faixas). Agora chama `fx_music.add_dynamic_music`
  com a seleção do hipercool (lixo, ≥ 1 min, recentes, trechos seguidos do mesmo clima = 1 faixa, ≤ 100 s), mais
  `normalize=0` nos `amix` (o do riser dividia a trilha pelo nº de trocas), `cp`→`shutil` e `moods.json` lido em UTF-8.
  Teste com voz real 75 s (tenso/triste/tenso): 3 faixas com crossfade, voz igual (-23,6→-23,4 dB), música -27 dB nas
  pausas. Backups `bin/*.bkp_20261016_trilha`. Produção das histórias parada desde 08/10 — só vale quando voltar.
- **hipercool `bin/fx_music.py:_escolher`** (dono autorizou): usava `min(..., recentes.index)` quando todas as faixas do
  clima já tocaram → pegava a tocada POR ÚLTIMO e repetia; agora `max`. Teste com 4 faixas: rodízio sem repetir.
  Commit `ada5ce9` (só esse arquivo). No react a mesma linha repetia a faixa 193 de 200 vezes antes da correção.
- **"Rajada" do hipercool no pt (Onda 2.4) — não é problema público**: o ledger tem as partes 1–8 do cap 1 enviadas
  ao InovareManhwaVerse em 15/10 05:27–06:09, mas as 10 de 15/10 estão PRIVADAS (oEmbed 403; público = 200). O dono
  confirma que só 1 short foi publicado. Nada a fazer no `postar_hipercool.py` por isso.

## Histórias "prontas pra religar" (claude-20, 16/10 tarde — dono parou em 08/10 por falta de views)

Teste de ponta a ponta com os parâmetros da produção (terror, 8 cenas, high) em `workspace\_teste_religar` (a rede
não lê): saiu inteiro em 13,6 min — 59 s, -14 LUFS, SEO, capa 9:16 boa, trilha nova. Quadros vistos:
- **1º segundo preto/escuro**: intro "estilo Re:Zero" (0,15 s preto + painel borrado a 40% + fade 1 s, sem fala, 1,8 s).
  → agora o Short começa DIRETO na cena 1 com a narração e o título como gancho grande no topo por 3 s
  (`fx_legendas_ass` estilo Hook, padrão do react). Intro antiga: `HIST_INTRO=1`.
- **mascote "EITA! 👀" cobria a legenda** → `MASCOTE_OVERLAY` padrão 0.
- **`shakeglitch` parece vídeo corrompido** → `diretor_cena.FORA`.
- **fogo numa cena de "névoa densa"**: o anti-repetição das transições elementais trocava pelo PRÓXIMO da lista →
  agora pula o corte (só o `ELEMENTAL_FORCE` de teste ainda troca).
- **card de propaganda com wa.me/<número> em verde WhatsApp em 80% dos vídeos** (`promo_mode: rotate`) — o mesmo
  tipo de slide que derrubou os canais do Veo → `config\settings.json` `promo_mode: "off"` (backup
  `settings.json.bkp_20261016_promo`). Religar só com o dono.
- Marca @InovareStories: no caminho ASS fica no canto sup. direito = faixa que a rede desfoca e troca pelo @ do canal. OK.
- Fica como está: card final "INSCREVA-SE" (2,4 s).
Backups: `bin/*.bkp_20261016_religar`.
**2º teste com as correções** (`workspace\_teste_religar2`, 7,4 min com cache): 57 s, -14 LUFS; quadro 0 s = cena 1 +
gancho "O ANDAR QUE NÃO DEVERIA EXISTIR" no topo + legenda; sem mascote; cena 6 `perspectivetilt` (sem glitch); névoa
sem fogo. Pronto pra religar (produção/postagem = decisão do dono).

## Recap de anime x hipercool — o que ainda falta (claude-20, 16/10 ~17:20; dono: anime volta com canal próprio)

Tem: SEO novo, capa IA (1 por vídeo), vozes aprovadas, legenda palavra a palavra (fx_subtitles/ASS), Shorts.
Falta (copiar do hipercool/historias):
- **Trilha quebrada**: `anime-pipeline.py` passa `{"texto": ...}` e o `fx_music.add_dynamic_music` lê `"text"` → clima
  nunca detectado (trilha não acompanha a história). E o `fx_music` do recapd é o fork antigo: sem `normalize=0`
  (narração -6 dB), sem blocklist de copyright, sem filtro de lixo/recentes, `cp` no Windows → mesma correção das historias.
- **Master -14 LUFS**: só com `MASTER_LOUDNORM=1` (não ligado) → vídeo sai baixo e o YouTube não aumenta.
- **Abertura com gancho na tela** (o "gancho" só vai pros metadados) e **barra de progresso**: não tem.
- **Análise do vídeo pronto** (`revisao_video.py`, trava de nudez): não tem — anime com fan service corre o risco do pt.
- **Extras do Studio**: `studio_extras_anime` existe e não está ligado. **Capa A/B**: 1 capa só.
- Nenhum recap de anime gerado desde set/2026 (nada no disco) → testar de ponta a ponta como nas historias.
- Postagem: `postar_tudo_hoje` é o caminho de rajada/round-robin da auditoria — canal novo do anime deveria ir pela
  rede (espaçada) — claude-40.

**Feito 16/10 ~17:30–18:00 (dono: "faça todas"), backups `*.bkp_20261016_anime`:**
- `fx_music.py` = a versão corrigida das historias (seleção do hipercool, normalize=0, blocklist, UTF-8, `shutil`);
  `anime-pipeline.py` passa `{"text": ...}`.
- Master -14 LUFS / -1 dBTP no fim do `anime-pipeline` (`master_loudness.measure_pass/apply_pass`, vídeo copiado).
- `anime_gancho.py` (novo): gancho de 3–6 palavras pelo LLM (sem nome da obra) no topo nos 1os 3,2 s + barra de
  progresso; vídeo longo = mesma passada da legenda ASS (`fx_subtitles.burn_subtitles_ass(extra=...)`), Short = passada
  curta à parte. `ANIME_GANCHO=0` desliga. Testado nos dois formatos (quadros vistos).
- `anime_revisao.py` (novo): trava do vídeo pronto = `revisao_video.py` do hipercool em PROCESSO SEPARADO (importar
  traria o bin do hipercool pra frente do sys.path), passo 0,5 s no Short / 3 s no longo. `anime_publish` grava
  `pronto: false` + `revisao: pendente` e só libera com "ok"; `python bin/anime_revisao.py --pendentes` refaz.
  Teste: Short de 57 s, 48 quadros, ok em 2 min 16 s. `anime_auto`: timeout do publish 900 → 4800 s.
- O anime renderiza no PC2 (worker 100.125.7.77 = revision-pc-2, cópia em `C:\recapd-e-animes\bin`). **Dono autorizou
  (16/10 ~19:30) atualizar só essa pasta**: copiados fx_music, anime-pipeline, anime_captions, anime_gancho,
  fx_subtitles (backup lá `*.bkp_20261016_anime`, hashes conferidos, compila e importa no venv de lá). O daemon roda o
  anime-pipeline como subprocesso → vale no próximo job, sem reiniciar. `claude_client` do PC2 já tinha `timeout` (não
  mexido). A trava (anime_publish) roda aqui.
- Capa A/B: não feito (canal novo não terá "Testar e comparar"). Extras do Studio + postagem espaçada: pedidos à claude-40.
- **Teste de ponta a ponta (19:10) achou o anime QUEBRADO antes de tudo isso**: `anime_script` chama
  `claude_client.generate_text(..., timeout=300)` e o `claude_client` restaurado do git em 16/10 não aceitava `timeout` →
  todo roteiro falhava ("bloco 0 falhou: unexpected keyword argument 'timeout'"), nenhum recap saía. Corrigido:
  `generate_text(..., timeout=90)` repassa pro `_post` (mesma assinatura do `claude_fallback`). Backup
  `claude_client.py.bkp_20261016_anime`. Vale também pro PC2 (a cópia de lá precisa do mesmo).
- **2º teste (19:18–19:34) passou de ponta a ponta** (local): Short do Horimiya, gancho "O SEGREDINHO DELES FOI
  REVELADO" no topo + barra + legenda (quadros vistos), master -23,5 → -14 LUFS, capa IA, revisão ok (17 quadros),
  postar.json `pronto` só depois do ok. Marcado `pronto: false` + `"teste"` à mão: capa errada e marca d'água (abaixo).
  - **Capa de batalha num romance** (pose `confronto_boss`, cavaleiro gigante): o SEO não mandou `generos` → padrão
    ação. Corrigido: 6 poses fora da batalha em `config/POSES_ANIME.py` (romance/escolar/comédia/drama/mistério/
    esporte, `REGRAS_GERAIS`: adultos vestidos, sem beijo), gênero deduzido do título/cena (`_generos_do_texto`),
    nada casou = pose neutra (nunca batalha). Refeita: "segredo_revelado" — combina. Backups `*.bkp_20261016_anime`.
  - **Marca d'água do canal de origem** ("WM520 DX", espelhada) aparece no vídeo: o Short usa clipe de outro canal.
    `marca_scan` do hipercool não serve (molde de scan em imagem parada). Recurso novo — decidir com o dono.
  - Short de só 14 s (fonte curta).
- Achados no mesmo teste (não mexidos): o discover pega candidato estranho (clipe oficial em japonês, "ONEE-CHAN 7w7",
  "wtf..."); yt-dlp falha em parte dos downloads; Whisper `tiny` transcreveu Steins;Gate como hindi.

## 🚧 Shorts do parceiro @kaijinre reeditados com nossas vozes (claude-20, pedido do dono 16/10 ~19:50)

Dono: usar os Shorts de resumo do @kaijinre (parceiro, liberou TODOS), reeditar como o manhwa-react, vozes de IA nossas,
repostar. Longos e Shorts vão pro canal NOVO em pt (dono vai criar); até lá o pt sai no canal pt do hipercool; também
nos canais de língua estrangeira que já existem (hindi/ind/ita/ru/thai/vi). Fonte (conferido): 219 Shorts, manhwa,
narração pt, 720x1280 ~85 s, legenda amarela queimada ~66% da altura + marca "KAIJINRE" ~71%.
Dado do hipercool (`short_resumo.py`): Short SEM "Parte N" fez 513 mil; a "Parte 2" da mesma obra 2,4 mil → ordem:
resumos sem parte (mais vistos primeiro), partes por último.
Plano (base = Short do recapd: baixa, transcreve, reescreve, TTS, legenda, gancho, trilha, master, revisão):
1. [x] fonte = canal (`anime_discover.discover_canal`, `anime_auto --fonte <url>`): 219 Shorts, 82 resumos sem parte
       (1º: 2,6 mi), partes por último em ordem; feitos/tentados não se repetem.
2. [x] `anime_auto._reeditar_parceiro`: desfoca a faixa 58–78% (legenda amarela + KAIJINRE ficam ilegíveis — quadro
       visto) + zoom 8% deslocado + cor; sem espelho. Só quando a fonte é parceiro.
3. [x] roteiro do parceiro: até 18 frases (Short de anime segue com 10).
   Teste de ponta a ponta rodando (19:58) — `python bin/anime_auto.py --modo short --engine local --limit 1
   --fonte https://www.youtube.com/@kaijinre/shorts`. Backups `*.bkp_20261016_kaijin`.
4. [x] SEO de MANHWA: `seo_generator.gerar_seo_anime(midia="manhwa")` troca os termos/hashtags (#manhwa #webtoon
       #resumomanhwa; cache separado); `anime_publish --midia manhwa` (o `anime_auto` passa sozinho quando a fonte é
       parceiro) e grava `"midia"` no postar.json pra postagem rotear. Testado com título real. Capa: pose pelo gênero
       (já corrigido acima).
   **Teste do parceiro (20:07–20:48)**: resumo de 2,6 mi ("The Nerd Only Needed to TAKE OFF her Hoodie") → Short pt de
   43,7 s, faixa deles coberta, nossa voz + legenda + gancho + master -14 (de -22,9). **Revisão REPROVOU** (2 quadros, 18 s
   e 29 s) — olhando a folha: close de rosto suado e garota vestida = alarme falso; ficou `pronto: false` (certo: erra
   pro lado seguro). Novo: `python bin/anime_revisao.py --aprovar <postar.json> <quem>` libera depois de olhar a folha.
   Achados: (a) o @kaijinre tem 2ª marca "@kaijinre" semitransparente/espelhada solta no meio dos painéis — a faixa não
   cobre; (b) gancho cortado "ELE NÃO SABIA O QUE VINHA A" → corrigido (longo demais = sem gancho; PC2 sincronizado);
   (c) capa IA deu timeout no gateway → capa de quadro; (d) Short de parceiro renderiza LOCAL (o worker baixaria o
   original sem a reedição).
   **Dono viu o vídeo (16/10 ~22h): "está muito borrado no meio, tem que ser só em cima da marca e colocar a nossa
   em cima"** + liberou remover a 2ª marca. Refeito (`bin/parceiro_marca.py`, novo):
   - marca "@kaijinre" = branca semitransparente, CENTRALIZADA, tamanho fixo, que desce/sobe devagar o vídeo todo
     (84%→11%→84% em 70 s). Achada pelo "quanto clareou rumo ao branco" ((I−fundo)/(255−fundo), mediana 9x9) + molde
     só na faixa central, 4 q/s, trilha suavizada (11 de 282 pontos descartados). Molde em
     `config/parceiro_marcas/kaijinre_alfa.png`. Trocada por **@manhwanoturno** no mesmo lugar/estilo (Times Bold).
     (Tentativas que NÃO serviram: top-hat + molde na tela toda — nota 0,5–0,6 em tudo; top-hat só no centro — errou 2 de 4.)
   - legenda deles: linha medida por vídeo (y 923–972); coberta SÓ na largura das palavras (união ±0,23 s — as letras
     entram animadas), placa escurecida; a NOSSA legenda vai centralizada nela (`SUB_Y_CENTER`, 0,767 no final).
     Bug achado e corrigido: `crop` do ffmpeg com altura ímpar arredonda sem avisar → leitura desalinhava (26 quadros
     aos 41 s); agora par + `exact=1`; conferência em 30 instantes: 0 legenda fora da placa.
   - `fx_clips`: `ANIME_DESCARACT_FLIP=0` tira só o espelho (o anime espelhava tudo: "FANGIRL NUMBERS HERE" ao contrário);
     `fx_subtitles`: `SUB_Y_CENTER`. `anime_auto._reeditar_parceiro` liga tudo isso (sem o zoom extra de antes).
   - O Short de teste antigo (`nerd-only-needed_cap1_20261016`) foi com a faixa grande → descartar.
5. [~] línguas (`bin/anime_idiomas.py`, novo; 7 canais ativos do `hipercool/config/fila.json`: hi id it ru th vi en —
       fr está desligado). Por língua, a partir do ORIGINAL: cobre com o @ daquele canal, traduz o roteiro (1 chamada),
       voz de narrador do canal (a mesma do hipercool), legenda/gancho com fonte do alfabeto — hi/th pelo libass
       (`ANIME_SUB_ENGINE=ass` + Nirmala/Leelawadee: o Pillow daqui NÃO tem raqm), vi com Montserrat —, SEO na língua
       (`seo_generator(idioma_nome=)`), capa sem texto em hi/th/ru/vi, pasta `<slug>_cap1_<data>_<lang>`, `"idioma"` no
       postar.json; análise de nudez HERDADA da pt (`anime_revisao.herdar`; liberar a pt à mão libera as línguas).
       Ligado no fim do Short de parceiro (`anime_auto`; `ANIME_IDIOMAS` escolhe as línguas). Envs novos (padrão = antes):
       `ANIME_TTS_VOICE`, `ANIME_SUB_FONT_PNG/ASS`, `ANIME_LANG_NOME`; ASS também respeita `SUB_Y_CENTER`.
   **Testes (16/10 ~22h–23h)**: hindi (quadros vistos: devanágari certo, @inovaremanhwaversehindi, sem espelho) — mas o
   título saiu em PORTUGUÊS → `seo_generator`: instrução de língua no FIM do prompt + checagem do alfabeto + cache também
   validado (re-teste hindi/italiano/tailandês ok). pt "Part 8. He Spent YEARS Seeing Girls as ROCKS" (1,1 mi): legenda
   nossa centralizada na placa, gancho, @manhwanoturno; **revisão reprovou 23/44/49 s = alarme falso** (professora de
   saia, quadro de transição com close de rosto corado, aluna de uniforme) → `pronto: false` até alguém liberar.
   Os 2 testes velhos marcados `"teste"` + `pronto: false` (hindi saiu com `pronto: true` → corrigido na hora).
   **Corrigido depois dos testes (23:30)** — backups `*.bkp_20261016_lote`:
   - fila: o título do @kaijinre começa com EMOJI ("🎮 Part 2. ...") e o `re.match` não achava a "Part N" → a Part 8
     entrou como resumo e foi a 1ª. Agora `re.search` + `yt-dlp --encoding utf-8` (sem ele sai cp1252). Conferido: 137
     partes, 82 resumos; fila = 2,6 mi, 1,0 mi, 961 mil...
   - o "Nerd" de 2,6 mi tinha ficado marcado FEITO com a versão do borrão grande (que o dono reprovou) → desmarcado
     (`_feitos_short*.txt.bkp_20261016_nerd`), volta a ser o 1º com a cobertura nova.
   - pasta de saída: `<obra>_cap1_<data>` com `exist_ok` → as "Part N" da mesma obra (a "Seeing Girls as ROCKS" tem 33+)
     SOBRESCREVIAM o vídeo da fila no mesmo dia. `anime_publish._pasta_saida`: outra fonte → `-2`, `-3`...; a mesma fonte
     reaproveita (refazer).
   - herança da análise: o nome da obra era pedido 2x ao LLM e a versão hindi não achava a pt ("Lookism" ≠ slug da pt).
     Agora o `anime_auto` calcula o nome 1x e o `anime_publish --anota-postar` devolve o caminho exato do postar.json pt
     pro `anime_idiomas.gerar(pt_postar=)`; `anime_revisao._herdeiros` compara caminho resolvido.
   Rodada completa (pt + 7 línguas) disparada 23:31, prioridade baixa: log `workspace/anime/_parceiro_20261016.err.log`.
6. [x] **EM PRODUÇÃO (16/10 ~23:50)** — dono viu a Part 8: "pode melhorar muita coisa mas está bem postável, pode
       colocar em produção, ponha pra postar no manhwaverse br e no novo [Manhwa Noturno], 1 por dia".
       `bin/parceiro_diario.py` (status/producao/postar --ensaio) + `config/parceiro.json` + `cron_parceiro.bat`;
       tarefas **ParceiroKaijinre-Producao 02:20** e **ParceiroKaijinre-Postagem 23:20/23:50** (sobe depois da janela do hipercool: a cota de 4/canal/dia conta pela hora do upload — apontado pela claude-5c) (rodar_oculto.vbs).
       - "manhwaverse br" = **inovare manhwa br** (@inovaremanhwabr, da rede); o InovareManhwaVerse está com envio
         bloqueado (advertência 16/10). Cada canal pt recebe vídeo DIFERENTE: a produção escolhe o canal de fila menor
         e grava o @ dele (`PARCEIRO_HANDLE`/`PARCEIRO_CANAL` → `anime_publish --canal`).
       - postar.json do parceiro: `"categoria": "parceiro"` (o postar_tudo_hoje ignora), `"canal"`, `"fonte"`.
       - 1 por canal por dia, agendado (privacy private + publish_at, `projeto=reservado_para(canal)` como hipercool/
         rede), aprovação marcada com nota; a mesma fonte não sai em 2 canais no mesmo dia. Horários fora das janelas
         dos donos: Manhwa Noturno 12:20 (hipercool 18–23h), inovare manhwa br 16:40 (rede 13:00/19:20/22:00), línguas
         16–17h de lá (hipercool 17–22h). en/fr pausados no postador → fora.
       - produção: fila alvo 2 por canal, até 2 pt por rodada, línguas só as de fila curta (máx 3 por fonte), disco
         ≥ 8 GB, prioridade baixa, não roda se já houver anime_auto do parceiro rodando.
       - Part 8 liberada à mão pelo DONO (assistiu) → 1º agendamento: Manhwa Noturno 18/10 12:20 (upload 17/10 23:20; a cota de 4 de 16/10
         do canal já foi usada pelo hipercool).
       - Bug achado no 1º teste do .bat: a saída do PowerShell vem em cp850, a leitura utf-8 quebrava e a checagem
         "já tem produção rodando" dava falso → subiu uma 2ª produção junto (deixada rodando: inovare manhwa br estava
         com fila 0). Corrigido (errors=replace; sem resposta = não roda).
       - Avisado à claude-5c (postador). Achado pra ela: `politica.py` tem 0 canais ativos na rotação → os recaps de
         ANIME (categoria animes) não têm canal no postar_tudo_hoje hoje. Ela confirmou: os Shorts do parceiro ficam
         FORA do catalogo.py (sem TikTok/Insta — só YouTube foi liberado; decisão do dono) e a rede manda 1 react/dia
         no inovare manhwa br (cabe). Antes das 23h a postagem só sobe com cota_restante ≥ 2 (vaga do dono do canal).
       - Logs: `logs\parceiro_producao.log`, `logs\parceiro_postar.log` (um por ação: o cmd prende o arquivo do `>>`
         enquanto a produção roda e a postagem nem começaria); render: `workspace\anime\_parceiro_AAAAMMDD.log`.
   **Decisão do dono pendente**: quem libera alarme falso da trava (só o dono, ou claude-20 olhando cada quadro marcado
   e registrando `--aprovar ... claude-20`). Quase todo Short do parceiro é de escola/romance → a trava (1 "sim" em 3
   opiniões já reprova) deve marcar muitos. 17/10 00:05: o "Nerd" refeito (2,6 mi) reprovou aos 31 s — quadros 28,5–
   33,5 s vistos: nerd de moletom olhando por cima do ombro + rapaz de camiseta = alarme falso; parado com as línguas.

## ✅ Narração com curva de locutor (hipercool → recapd, claude-05, 17/10 ~00:05)

Dono: "tem métodos de narração que parecem mais reais, tipo um narrador de futebol aumentando a velocidade, diminuindo
e variando volume, que o hipercool fez (docs/VOZ_E_NARRACAO_PENDENTE.md) — implementa na sua criação também".
`bin/narracao_curva.py` (cópia adaptada de hipercool `elenco.curva_climax/prosodia/_pos_processar`), ligado no
`anime_segments` → `anime_tts.narrate(indice, impactos, total)` → `edge_tts_engine.speak(rate=, pitch=)`. Vale pro recap
de anime (Short e deitado) e pro parceiro, pt e línguas. Backups `*.bkp_20261017_curva`.
- impactos (os "gols") escolhidos 1x por vídeo pelo LLM (1 por ≤6 frases, 2 no Short, ~1 a cada 12 no longo; reserva:
  heurística de exclamação/virada/posição), guardados em `_impactos.json` ao lado da fonte; as línguas recebem os da pt
  (`ANIME_IMPACTOS`). Rampa quadrática de 4 frases no Short (7 no longo) até +18% de velocidade e +4 dB; respiro de 2
  (3) frases a -12%, -4 Hz, -3 dB; tom quase parado (+1 Hz: o dono reprovou a voz "fina" no hipercool).
- adaptações pro Short (impactos perto): impacto é sempre pico (no hipercool o 2º de 2 impactos colados saía MAIS
  LENTO) e a frase logo antes de um impacto embala mesmo dentro do respiro do anterior.
- pontuação (grito +10%/+3 dB, reticência -8%), variação fixa por frase ±3%/±1 dB, cada frase nivelada a -20 LUFS + a
  curva, cauda de silêncio do edge cortada (0,25 s; 0,6 s depois do impacto).
- Medido na Part 8 (mesma voz e frases): volume entre frases variava 2,1 dB → 7,9 dB; frase de impacto 3,42 → 3,96
  palavras/s, respiro 2,5–2,7; áudio 57,0 → 54,9 s. Amostra pro dono:
  `workspace/anime/_amostra_curva/ANTES_e_DEPOIS_narracao.mp3` (aberta na tela). `ANIME_PROSODIA=0` desliga.
- **historias-em-frames** também (pronto pra religar): mesma cópia `bin/narracao_curva.py`; `story_pipeline` aplica por
  cena (impactos 1x por história, curva sobre o perfil da voz) e a curva entra na chave do cache de narração (o cache
  é por texto e vale pra todas as histórias); `edge_tts_engine.speak(rate=, pitch=)`. `NARRACAO_CURVA=0` desliga.
  Testado no venv DELE (`historias-em-frames\venv`, edge-tts 7.3.1): respiro -13%/-14% e ~-3 dB, base -19,8 LUFS.
  Backups `*.bkp_20261017_curva`. (Atenção: o python do sistema tem edge-tts 7.2.8 e a Microsoft devolve 403 pra ele;
  no mesmo teste 4 proxies Webshare deram **402 Payment Required** — parte do pool está sem crédito.)
- Falta: PC2 (C:\recapd-e-animes\bin) ainda sem a curva — só importa quando o Short de anime voltar a renderizar lá.
  Não feito do doc do hipercool (lá também está "a fazer"): alongar vogal tônica, micro-variação DENTRO da frase,
  respiração audível.

## ⚠️ Achado 16/10 tarde (claude-20) — recaps do hipercool nos canais de língua com 0 views REAIS

`_analise/aprendizado_global.json` (30 dias): "recap hipercool" n=24, mediana 0, todos 0. Conferido na página pública
(13–14/10, ru/thai/hindi/vi): oEmbed 200 (público), `playabilityStatus OK`, `isFamilySafe true`, não listado = false,
**viewCount 0** após 2 dias. Ou seja: publicado, sem restrição de idade, e o YouTube não entrega a ninguém. Causa mais
provável: o mesmo recap em 7–8 canais (13/10) = conteúdo repetido. Não mexido — decidir com o dono (estratégia de
postagem do hipercool). Referência: react/rede mediana 28, p75 ~1.200 (quase tudo para no teste inicial de ~1.200).

## Teste real (16/10)

- SEO anime (Shield Hero / Berserk): sem nome da obra nem traduzido; títulos inteiros; ~4 s.
- SEO histórias (ralo / Alzheimer): títulos da história, 15-23 tags, #shorts; ~20 s com capa.
- Capas: Shield Hero 16:9 (protagonista parecido, sem logo), ralo 9:16, drama 9:16 — vistas uma a uma.
- `anime_publish` de ponta a ponta numa pasta de teste: postar.json + capa + `thumb`.

---

## 📋 PENDENTE

1. **Postagem do anime**: o `postar_tudo_hoje` está com 0 canais ativos ("Pools: 0 IA | 0 manga") — nada de anime sobe
   até o dono ligar canais pra categoria animes.
2. **Extras do Studio (§3) no anime**: o upload sobe PRIVADO e comentário só fixa em vídeo público → precisa de rodada
   periódica (`studio_extras_anime.rodar_extras`) ligada no postador. Histórias: a rede já posta o 1º comentário.
   `studio_extras_historias.py` ficou sem uso.
3. **Teste A/B de capa** (3 capas por vídeo + Thompson em `capas_poses.json`): hoje é 1 capa por vídeo; o `.capa.json`
   ao lado guarda pose/texto pra medir quando houver dados.
4. **Capas sensuais no anime** (o CLAUDE.md do recapd pede rodízio sensual + batalha): só batalha por enquanto.
5. **Medir**: `estilo_titulo` e `capa_pose` vão no postar.json; falta ler CTR no Studio e chamar
   `seo_generator.registrar_resultado`.

## ✅ Feito em 18/10/2026 (revisão completa hipercool → manhwa-react)

- **§4d ffmpeg 8 `-loop 1`** corrigido em `mr/render.py`: máscara de emenda (passo A) e emoji/overlay PNG (passo B)
  agora usam `_clipe_parado` (clipe .mov com `loop=`, como o hipercool). Cache em `%TEMP%/mr_clipes`.
- **Banco de palavras buscadas** (`seo_palavras.json` do hipercool) integrado na rede para vídeos do react:
  `_palavras_buscadas_react` em `mr/rede.py` cruza os gêneros do editorial com o banco e manda as palavras ao agente
  do canal no prompt. Antes só o Veo recebia palavras buscadas.
- **Extras do Studio** (comentário fixado pelo navegador): `_extras_studio` em `mr/rede.py` roda
  `youtube_studio_extras.py --comentario` para cada vídeo da rede que já abriu. Chamado no fim de `_comentarios`.
  Marca `extras_studio` no registro para não repetir.
- **Thompson de título**: já existia na rede (`ESTRATEGIAS["titulo"]` com 5 braços + `ordem_bracos` + exploração 25%).
  A estratégia vai no registro da postagem e o painel mede em 48 h. Não precisou de adaptação — faltava só o dado de
  SEO (palavras buscadas), que agora entra.

## ✅ NÃO SE APLICA

- §4c Groq: recapd e historias usam faster-whisper local. (manhwa-react: feito em 15-16/10, ver `CORRECAO_GROQ_PROXY.md`.)
- §6 Censura/revisão do vídeo pronto (`revisao_video.py`, detecção de nudez, mosaico por painel): EXCLUSIVO DO
  HIPERCOOL. O react usa painéis do vídeo original do criador, que já passou pela moderação do YouTube. A detecção
  de nudez e o mosaico localizado dependem do pipeline de painéis soltos (Sightengine/NudeNet/Gemini por painel) que
  só existe no hipercool. A trava `revisao_video.py` é do hipercool e do recap de anime (que usa painéis de manhwa);
  manhwa-react, historias-em-frames e Veo limpo NÃO precisam dela. (Decisão do dono, 18/10/2026.)
- §4b Vozes proibidas (Antonio/Francisca/Isabella): não se aplica ao manhwa-react — o react usa a voz do próprio
  criador, sem TTS. Vale para recapd, historias e hipercool.

## ✅ Feito em 18/10/2026 — 6 funcionalidades dos outros projetos adicionadas ao manhwa-react

Pedido: "faltou alguma coisa boa que tem nos outros projetos de vídeo que esse não tem? → adicione todas".

### 1. Anti-ban no título/descrição (hipercool `ANTI_BAN`)
- `mr/rede.py`: dicionário `ANTI_BAN` (palavra→troca segura), regex ordenada por comprimento, função `anuncio_seguro()`.
  Aplicado em `_validar_meta()` (titulo, descricao, tags, comentario) e no upload de completos (~linha 1073).
- `mr/publish.py`: título, descrição e tags passam por `anuncio_seguro()` antes do upload.
- Verificado: teste unitário com frases reais; a regex preserva maiúsculas/minúsculas.

### 2. Retry do YouTube Studio "Algo deu errado" (hipercool `metricas`)
- `D:\postador-de-videos\bin\youtube_studio_extras.py`: `metricas()` agora tenta 2× cada aba do Analytics quando
  detecta "Algo deu errado" / "Something went wrong" (recarrega a página e reentra na aba).
- Backup `.bkp_20261018`. O cron horário já roda — a correção vale na próxima execução.
- Não verificado em produção: depende do próximo "Algo deu errado" real. 2 contas do cofre estão deslogadas
  (dono precisa rodar `cofre.py logar`).

### 3. Notificação na tela + Telegram (hipercool `notificar`)
- `mr/notificar.py` (novo): `tela()` (balloon do Windows via PowerShell NotifyIcon), `telegram()` (bot via
  `D:\postador-de-videos\config\telegram.json`), `aviso()` (os dois juntos).
- `manhwareact.py`: `_run_batch()` dispara `aviso()` ao final do lote com contagem prontos/erros.
- `mr/rede.py` e `mr/publish.py`: disparam `aviso(nivel="erro")` quando um canal é suspenso.
- Verificado: balloon apareceu na tela (2º teste, 8 s de espera para o PowerShell carregar Forms).

### 4. Limitador inteligente de rate-limit (hipercool `limitador`)
- `mr/limitador.py` (novo): backoff exponencial por serviço (LIMIAR=3 falhas → pausa 5 min, dobra a cada rodada,
  máx 2 h; metade no sucesso). Estado em `work/limitador.json`.
- Integrado em `mr/llm.py` (proxy LLM), `mr/capa.py` (visão), `mr/transcribe.py` (Groq).
  Cada chamada checa `restante()` antes e registra `falhou()`/`ok()` depois.
- Verificado: importa e roda sem erro; lógica idêntica ao hipercool (adaptada para `mr.common`).

### 5. Foley contextual por keyword (hipercool `foley`)
- `mr/foley.py` (novo): `FOLEY_MAP` com 24 situações (soco, espada, explosão, porta, etc.),
  `plan_foley()` retorna eventos sfx com campo `dur`.
- `mr/pipeline.py`: integração gateada por `config.json > overlays > foley` (default `true`).
  Filtra só palavras de conteúdo narrado (speaker == "content").
- `mr/render.py`: `render_audio()` aplica `atrim+afade` nos eventos com `dur` para cortar o foley.
- Keywords refinados com narração real de 48 min (3tMxBPYp6WE): "bateu" sozinho → removido de soco
  (conflitava com "bateu na porta"), "espada" → frases completas ("empunha a espada", "saca a espada"),
  "comemora" → removido de aplauso, "rajada" → "rajada de vento" (não "de relâmpagos"),
  "tapa" → "dá/deu um tapa" (não "tapa os ouvidos"). Zero falsos positivos no teste final.
- Verificado: teste com narração real, sem falsos positivos após refinamento.

### 6. Templates de capa por gênero com A/B/C (hipercool capa A/B + Thompson)
- `mr/capa.py`: `GENRE_COLORS` (10 gêneros), `genero_de(*textos)` (detecção automática por palavras-chave),
  `caminhos_ab(out)` (gera paths B/C a partir do A), `_tratamento(canvas, variante, genero)`:
  A = controle (branco/amarelo), B = gradiente vertical na cor do gênero (alfa 0.45),
  C = escurecimento esquerda→direita na cor do gênero.
- `mr/grande.py`: chama `genero_de()` e passa `genero` a `capa_grande()`; salva `thumbs_ab` no postar.json.
- `mr/rede.py`: registra `thumbs_ab` no publicados.json (usando `posted_dir`, depois do `_arquivar`).
- `D:\postador-de-videos\bin\extras_rede.py`: `planejar()` inclui `teste_ab` para completos com 2+ capas;
  main loop passa `ab=capas` ao `youtube_studio_extras.rodar()`.
- Thompson sampling: já existia em `mr/rede.py` (`ordem_bracos`). O loop de métricas alimenta automaticamente.
- Verificado: geradas capas A/B/C para gêneros "drama" e "fantasia" em vídeo real — imagens vistas e aprovadas.
  Backup `.bkp_20261018` nos arquivos do postador.

### 7. Tela final "1 vídeo + playlist" nos completos (18/10, depois)
- `mr/rede.py`: `PLAYLIST_COMPLETOS` (nome fixo, sem obra); o upload do completo manda `playlist=` (o web poster cria a
  playlist se não existir; falha não trava o upload) e grava `"playlist"` no publicados.json.
- `extras_rede.py`: `planejar()` põe `tela_final` em todo completo público com `playlist` no registro → `rodar(tela_final=)`.
- Não verificado no Studio: vale a partir do próximo completo (nenhum completo tem `playlist` ainda; ensaio = 0
  pendentes). Canal sem verificação → Studio devolve "pendente" e tenta de novo.

### 8. Rascunhos presos (18/10, depois)
- `extras_rede.py`: no fim da rodada, 1x por dia por canal tocado, `rodar(limpar_rascunhos=True)` só LISTA (sem
  `--apagar-mesmo`) e escreve no log o comando de apagar. Estado `config/extras_rede_rascunhos.json`.

## Vigia de melhorias entre projetos (18/10)

`D:\postador-de-videos\bin\vigia_melhorias.py`, tarefa **VigiaMelhorias** (pythonw, 09:07, sem janela). Todo dia avisa
(Telegram + tela) as linhas de Novidades que cada projeto ainda não tratou e o projeto que mudou código sem linha nova
em Novidades. Marcar: `--marcar manhwa-react <id> feito|nao --motivo "..."`; ver: `--listar`. Regra escrita em "Como
manter" do doc central. As 3 melhorias acima que servem aos outros (tela final/rascunhos, capa A/B/C, foley) já estão
em Novidades.
- Marcado: `8e1dce` (fix `ab=`/`teste_ab` do studio_extras_historias) = não se aplica, o `extras_rede.py` já usa os
  nomes certos.
- Pendentes pro manhwa-react (1º aviso, 18/10): nenhum canal sem postagem; limite do postador dividido; ordem de
  postagem do hipercool; ffmpeg `-ss` perto do fim; print com emoji sem UTF-8.
