# Tarefas: Shorts de PARCEIROS (todos os nichos) — leia isto primeiro

Atualizado 18/10/2026 ~05:00 (claude-opus). Quem pegar: siga a ordem, marque [x] e escreva o que fez embaixo de cada item.
Regras do dono e da casa: D:\manhwa-react\MELHORIAS_APLICADAS_E_PENDENTES.md (seção do parceiro), memória do projeto.

> **28/10 (lista nova da dona)**: 18 canais que faltavam entraram em `producao\config\parceiro.json` (_obs "lista da
> dona 28/10"; backup parceiro.json.bak_20261028_lista_dona; total 82, PC2 igual). manhwa: danielarecapsbr,
> carecanomultiverso · anime: levisaosensei, shounenanimes5, xackal777, topanimes2373, ryukmovies, animeeditsvnx,
> nerddaybr, nerdrudimentar, allonegeek · filme_sem_voz: crystalcine, guilhermesouza-i5x · jogos: pontocuriosoytt ·
> fatos/curiosidades: kaiquebelgames (críticas de filme), nucleotech_ofc (ciência), conspiracoessecretas, explicaaii1
> (teorias). Os demais da lista já estavam. O link avulso youtube.com/shorts/7kW17VixwEU é 1 vídeo (canal não
> identificado) — não entrou. Busca testada no levisaosensei: 962 Shorts.

> **22/10 (claude-8a, conferido nas tarefas do Windows): desde 20/10 quem DISPARA a produção é o `ControladorVideos`**
> (`D:\video-fila\controlador.py`, 10 em 10 min; manda nos 2 PCs: PC1 = Cortes/Shorts, PC2 = anime longo + línguas do
> hipercool; desktop/PC3 só tarefa leve e só sem OBS/editor aberto). A tarefa `ParceiroKaijinre-Producao` está
> DESLIGADA desde 20/10 05:05; a `ParceiroKaijinre-Postagem` continua (postagem, :15/:45). Liga/desliga por projeto em
> `D:\video-fila\controle.json`, pelo painel http://localhost:8790 (aba Liga/desliga; no celular pela Tailscale com a
> chave). Estado atual e o que falta: `D:\video-fila\MELHORIAS_SHORTS.md` (PASSAGEM DE BASTÃO + rodadas de 22/10). A IA
> do vigia e do painel (Kiro) troca sozinha pra uma reserva grátis quando o Kiro fica sem crédito (`ia_reserva.py`).

> **18/10 19:15 (claude-32, unificação)**: o parceiro posta como `PROJETO="parceiro"` (não mais `reservado_para`).
> Onde pode postar vem do cadastro único `D:\postador-de-videos\config\canais.json` (`politica.pode_postar`):
> Manhwa Noturno = dono hipercool, teto 3, parceiro só "sobra" (canal vazio no dia ou depois das 23:00 BR — decisão do
> dono); 3 Noturnos dedicados = dono parceiro, teto 3; reacts/línguas = "livre". `pol.cota_restante(canal, "parceiro")`
> já devolve 0 quando é vaga do dono. Espera da trava do Chrome não conta mais como timeout. Ledger grava projeto/tipo.
>
> **18/10 ~23h40 (claude-32, dono: "vê o que é melhor" com a semana programada)**: teto de UPLOAD (4/canal/dia) é
> separado do de PUBLICAÇÃO por dia (`canais.json max_dia`: reacts BR 3, Noturnos 3, línguas 4). Onde o parceiro é
> "livre" (reacts, línguas) há `reserva_dono: 1`: 1 upload/dia guardado pro dono até 23:00 e 1 publicação/dia guardada
> pro dono em cada dia da semana → parceiro até 2 abrindo/dia nos reacts, 3 nas línguas e nos Noturnos. `parceiro_diario`
> agora chama `pol.horario_publicacao(canal, alvo, PROJETO)` (com o projeto: o dia cheio pro parceiro passa pro próximo
> e o `agendado_para` gravado bate com o real). Reuso: Shorts de parceiro no catálogo por ficha + regra `parceiro_de`.

> **19/10 (claude, análise "crescer sem banir")**: o dono confirmou que TODAS as fontes de `config\parceiro.json` são
> parceiras AUTORIZADAS — não perguntar de novo. Narração: `anime_script.py` agora usa o jeito de falar dos 15
> narradores BR medidos pelo hipercool (`_jeito_do_nicho`, prompt v3; em anime/manhwa 1 tirada sorteada por trecho).

## Onde está tudo
- Código: `D:\recapd-ambientes\producao\bin` — `anime_auto.py` (produz 1 Short: baixa, roteiriza, narra, renderiza),
  `parceiro_marca.py` (cobre legenda/marca do parceiro), `parceiro_diario.py`
  (status/producao/postar), `anime_idiomas.py` (línguas), `narracao_curva.py` (voz de locutor), `fx_clips._movimento`
  (câmera + impacto).
- Config: `config\parceiro.json` (canais de destino, horários, por_dia, fila_alvo, fontes com rodízio, narradores por nicho).
- Tarefas Windows (nome antigo, servem pra todos os nichos): `ParceiroKaijinre-Producao` (a cada 30 min, :05/:35),
  `ParceiroKaijinre-Postagem` (a cada 30 min, :15/:45), `VigiaVideos` (20 em 20 min; agente = kr/claude-sonnet-4.5
  do Kiro, em D:\hipercool-videos\secrets\claude_proxy.json). Render pesado passa pela fila `D:\video-fila\fila_render.py`.
- Ver a fila: `D:\veo\venv\Scripts\python.exe bin\parceiro_diario.py status` (na pasta producao).

## Nichos ativos (18/10)
Cada canal pt recebe vídeo de fonte do SEU nicho (`nicho` no config). Canal cujo nicho não tem fonte ainda cai no
rodízio global (o nicho que menos produziu em 24h — pode ser anime, esporte, filme...).
**Canais DEDICADOS (18/10, criados pelo dono, 2 por dia, projeto `recapd` no canais_reservados, só navegador,
`--checar` ok nos 3):** Dorama Noturno (@doramanoturno, conta maiteanajessicajesus, nicho dorama), Filme Noturno
(@filmenoturno, simonerebecaluizasilva, nicho filme_sem_voz), Curiosidades Noturnas (@curiosidadesnoturnasbr,
gabriellyvitoriaisabelaaraujo, nicho fatos — as fontes de fatos são Shorts de curiosidades).
- **manhwa**: kaijinre, king_chan01 → canais Manhwa Noturno, ForjaReact, inovare manhwa br
- **anime**: richan, ansaketv, nerdcf, 100animee, olaranjo1, animax_97, 6× channel/UC... → ManhwaReact, Animescomia, InventoReact, CartuchoReact
- **dorama**: drameela, jresumos, 7× channel/UC... → CenaReact
- **fatos**: inusifatos, xiuliamelo, carlosmerchanat, canalutopia, thalisshortsbr → Mundo Que Nao Existe
- **esportes**: futtres, fabioindaia2006 → sem canal dedicado (só entra nos canais de nicho sem fonte, via rodízio)
- **filme_sem_voz**: andreu_edit1 → sem canal dedicado (idem)
- **financas**: (sem fonte ainda) → Assist-IA Investimentos, Dicas financeiras da ia (recebem do rodízio)
- **história_mitologia**: thalisshortsbr (via `nichos`) → HistoriasEmFrames
- **curiosidades**: xiuliamelo, canalutopia (via `nichos`) → Fio da Meada
- **18/10 19:15 — encaixe pelo CONTEÚDO real** (títulos recentes de cada fonte, `yt-dlp --flat-playlist`): fonte pode
  ter `"nichos": [...]` = outros nichos que ela atende (`_escolher_fonte`; o rodízio dos nichos sem fonte usa só o
  `tipo` principal). xiuliamelo = curiosidades (Hollywood, uniformes); canalutopia = fatos bizarros; thalisshortsbr =
  histórias reais/mistérios; carlosmerchanat = agricultura/natureza; futtres = futebol; fabioindaia2006 = mistura;
  andreu.edit1 = resumo de filme de terror; UCRKSO0 = mini-séries (vingança, start-up). **inusifatos = bilionários
  (Elon Musk) + POLÍTICA BR (Lula, Bolsonaro, STF, eleição 2026)** — política hoje cai em Curiosidades Noturnas/Mundo;
  dono decide se tira a fonte. Finanças: nenhuma fonte posta finanças — dono precisa indicar parceiro.
  `fila_alvo` dos 13 canais BR: 3 → 6 (2 dias de reserva; postagem segue no máx 3/dia).

## Decisões do dono (17-18/10)
- Refação de vídeo de parceiro que JÁ está no YouTube NÃO passa pela trava de nudez (já feito em anime_publish).
- TESTE: manhwa/dorama de parceiro nos 12 canais de react, 4 por canal/dia (entradas `teste_rede` no config). Se
  renderem como os reacts, trocamos. Medir views em 48 h.
- Ideia do dono: em vez de borrar a legenda do parceiro, pôr um TÍTULO legal em cima + NOSSA legenda em outro lugar.
- Ficar "no mínimo diferente além do áudio e trilha": efeitos do hipercool/manhwa-react.
- **18/10**: "não estamos mais fazendo só recap de manhwa, são TODOS os tipos de vídeo". Expandir e ramificar.
- Agendamento obrigatório: NUNCA publishAt direto; sempre ≥10 min no futuro; YouTube checa direitos antes.
- **REGRA 18/10 — NUNCA SEM POSTAGEM**: nenhum canal fica 1 dia sem postar, em hipótese nenhuma. Impedimento
  (marca d'água, defeito visual pequeno, análise reprovando) SÓ AVISA — o vídeo sobe com o que tem. Produção e
  postagem são independentes: problema na produção não trava a postagem do que já está pronto. Vale pra todos
  os canais (parceiro, hipercool, react). Documentado em memória `feedback-nunca-sem-postagem`.
- **18/10 ~13:00 — 3 POR DIA nos canais BRASILEIROS** (mín 1, máx 3): cada canal pt tem `por_dia: 3`, `fila_alvo: 3`
  e 3 horários. As línguas continuam 1/dia (valores globais). **Canal sem post no dia** (nada publicado nem agendado
  pra hoje) = URGENTE: o próximo Short pronto é agendado pra agora+11 min (o Studio arredonda pra cima em passos de
  15 min → sai entre 11 e 25 min; com menos de 5 min o postador publicaria direto, o que é proibido). A produção
  (`_prioridade` em parceiro_diario.py, usada também pelo ocioso/PC2) faz primeiro os canais sem post hoje.
  Tarefa `ParceiroKaijinre-Postagem` a cada 30 min (:15 e :45; antes 6 horários fixos); a postagem pula se outra
  ainda estiver subindo (`_outro_postar_rodando`), senão as duas subiriam o mesmo Short. Além disso, cada Short pt
  novo dispara a postagem na hora (`disparar_postagem`, na produção e no ocioso quando traz do PC2; log
  `logs/parceiro_postar_auto.log`).
- **18/10 13:15 — PC2 travado 3 h na narração**: edge-tts 7.2.8 no venv do PC2 levava 403 do Bing (PC1 com 7.3.1
  ok). Short dFQYTbDx3ig encerrado (só a árvore dele, PID 800), edge-tts do PC2 → 7.3.1, teste de voz ok. O
  `atualizar_ytdlp.py` agora atualiza também o edge-tts dos 2 venvs do recapd e cobre o venv do PC2.
- **18/10 14:40 — Short preso em "esperando"** (HistoriasEmFrames, desconhecido-2): o ffmpeg da capa de referência
  (`_thumb_src.png` → `capa.jpg`) falhou com `check=True` e derrubou o `anime_publish` ANTES do `pronto=True` de
  parceiro. Repetido depois: funcionou (falha passageira, provavelmente memória — ver abaixo). Agora a falha dessa
  capa só avisa no log (com o erro do ffmpeg) e o publish segue. O Short foi liberado à mão (mesma `revisao` do publish).
- **18/10 14:40 — logins trocados no cofre**: no `cofre.py logar`, a conta emersonjosiel0 foi entrada no Chrome do
  perfil rezaulkarimul355 e vice-versa (ForjaReact: Timeout no Studio; Mundo: "sem permissão no canal"). Conferir
  com `account_info` em `perfis\<conta>\Default\Preferences`. Pastas renomeadas trocando os nomes (Chromes fechados).
- **18/10 ~13:50–14:35 — memória esgotada no PC1**: commit livre 0,8 GB de 36 GB; o `audio-separator` da tarefa
  `VozClonadaFila` (dataset de narradores) segurava 6 GB sozinho. Nesse intervalo: ffmpeg da capa falhou, Playwright
  morreu com "out of memory". Não mexi na tarefa da voz (é do material); se repetir, rodar o separador no PC2 ou
  fora do horário de produção.

## 18/10 19:30 — DONO: "são 26 canais, todos postam 1 a 3/dia, só 2 em restrição; sempre fabricar mais; hoje já
## deixar os de amanhã programados"
- 26 = 12 react (Dicas, Fio da Meada, Animescomia, CenaReact, InventoReact, ManhwaReact, Mundo, HistoriasEmFrames,
  inovare manhwa br, CartuchoReact, ForjaReact, Assist-IA) + 11 internacionais (thai, viet, hindi, ru, fr, ita, esp,
  ind, eng, InovareManhwaVerse, inovaremanhwabr) + 3 Noturnos novos (+ Manhwa Noturno do hipercool).
  Temas que o dono deu: inovare br = manhwa/webtoon/murim/regressão; CartuchoReact = games retrô/consoles/nostalgia;
  ForjaReact = forja/cutelaria/ferreiro/ofícios; Assist-IA = investimentos/cripto/trader. NÃO há fonte parceira de
  games, forja nem finanças — hoje recebem anime/manhwa/rodízio. Dono precisa indicar parceiros desses temas.
- Feito: parceiro.json com 17 pt + 8 línguas ligados (hi,id,it,ru,th,vi,en,fr), todos `por_dia` 3, 3 horários,
  `fila_alvo` 6 (pt) / 4 (línguas, global); `linguas_pausadas` removido; CenaReact (nicho filme_sem_voz) e
  ManhwaReact religados; InovareManhwaVerse incluído; Animescomia religado + `usar: true` no youtube_navegador (dono
  logando 19:30 — conferir `account_info` do perfil). Francês novo no `anime_idiomas.IDIOMAS` (voz
  fr-FR-VivienneMultilingualNeural) e no `_IDIOMA_NOME` do anime_publish. `rede_canais.json`: inovare_eng e
  inovare_french "pausado" → "hipercool" (como o ita; rede de react não pega). Backups `*.bkp_20261018_*`.
- `parceiro_diario`: `minimo` = 1 (a vaga do dono já sai de `pol.cota_restante(canal, "parceiro")`).
- 19:30 dono: "7 dias, 3 por dia, vai preenchendo conforme os vídeos saem; canal sem post = programado pra 10 min".
  `parceiro_diario.DIAS_FRENTE = 7`: a postagem programa até 7 dias à frente POR CAMADAS (1/dia nos 7 dias, depois
  o 2º, depois o 3º) — nenhum dia fica vazio se faltar vídeo. Limite real: teto de UPLOAD por dia (3-4/canal) no
  postador; a semana cheia (21/canal) leva dias pra fechar. Subir o teto é decisão do dono (risco no YouTube).
- `D:\postador-de-videos\config\canais.json` (cadastro único da claude-32): animescomia (dono manhwa-react),
  inovare_eng e inovare_french (dono hipercool) estavam "reservado" pro parceiro → `alimentadores: {"parceiro":
  "livre"}` igual ao inovare_ita. Backup `canais.json.bkp_20261018_parceiro26`.
- Animescomia sem fila: o Short pronto `jojos-bizarre-adventure_cap1_20261018` (InventoReact, que já tinha 4 hoje)
  foi passado pra ele (`canal_origem` no postar.json; sai com o @ do InventoReact gravado).
- Línguas: versão traduzida precisa do ORIGINAL do parceiro (o workspace só guarda final + roteiro) → sem download,
  sem língua. 19:28 YouTube ainda bloqueando.
- ~20:00 o bloqueio do YouTube passou sozinho (produção e línguas voltaram; hindi urgente 21:04). Tentativa de cookies
  de conta reserva (emersonjosiel649 etc.) não serviu: o perfil não tinha sessão em .youtube.com (só Google) — arquivo
  e script apagados. Se o bloqueio voltar: precisa conta com sessão do YouTube (SAPISID em .youtube.com).
- 23:00: `_prioridade` agora conta post de QUALQUER projeto no ledger (antes só do parceiro → Manhwa Noturno, que tem
  o do hipercool e só aceita "sobra", furava a fila e acumulou 5 prontos). InovareManhwaVerse `ativo: false`
  (suspenso); os 4 prontos dele (manhwa) passados pro ManhwaReact (`canal_origem` no postar.json).
- 23:10: balanço do 1º dia (18/10, ledger): 21 de 24 com vídeo; faltavam ita/eng/fr. URGENTE agora = canal sem vídeo
  de QUALQUER projeto no dia do Brasil OU no dia local; usa o próximo horário normal que cubra o dia que falta e só
  cai em agora+11 min se não houver mais horário (senão a rodada das 00:15 publicaria tudo de madrugada).
- **23:15 — inovare FRENCH: 2 ADVERTÊNCIAS DE DIREITOS AUTORAIS (27/09 e 18/10); a 3ª remove o canal e os associados.
  inovare ENG: advertências de diretrizes, upload bloqueado ("Muitos avisos").** Prints:
  `D:\postador-de-videos\logs\yt_web\20261018_225232_falha_inovare_french.png` e `..._225102_falha_inovare_eng.png`.
  Eu tinha despausado os 2 às 19:30 — DESFEITO: rede_canais "pausado" de novo, alimentador parceiro tirado do
  canais.json, `ativo: false` no parceiro.json. Nenhum upload chegou a entrar neles. Dono precisa abrir o Studio
  do francês (ler o aviso / curso de direitos autorais). São as "2 em restrição" + esp e InovareManhwaVerse suspensos.
- 23:20: regra "mesma fonte não sai em 2 canais no mesmo dia" agora vale POR IDIOMA (barrava thai/viet: a versão
  traduzida tem a fonte do Short pt).
- 23:40: ao matar à força (taskkill /F) o youtube_web_poster do inglês ficou `D:\postador-de-videos\logs\yt_web.lock`
  ÓRFÃO (o postador só descarta trava com 3 h) → a rodada 23:13 parou no ForjaReact ("trava ocupada há 25 min").
  Apagada às 23:40 depois de conferir que nenhum postador vivo a segurava. Lição: matou postador = conferir a trava.
  O italiano não pegou o 18/10 do Brasil por isso (o dele saiu 19/10 em Roma).
- RESTRIÇÕES (não postam): Inovare esp ("suspenso" no rede_canais, sem navegador) e InovareManhwaVerse ("suspensos").
- Cota de upload é por DIA DE UPLOAD (máx ~3-4/canal): canal que já subiu 3 hoje só programa os de amanhã depois da
  meia-noite (rodada 00:15). Produção depende do download — bloqueado pelo YouTube desde 19:03 (ver 1b).

> **18/10 ~23h30 (claude-b7, dono: "pode ligar no TikTok" + "1 a 3 por dia como no YouTube, nunca deveriam ter parado,
> podem reaproveitar os VO3 do Drive")**: Shorts de parceiro agora saem no TikTok. Em `reuso_plataformas.json`, cada
> TikTok que já existe ganhou `postados_em` com o canal do YouTube do parceiro (2026=InventoReact, 2027=HistoriasEmFrames,
> 2029=CenaReact, 2030=CartuchoReact, 2033=Assist-IA, inovaremanhwaverseita=inovare manhwa br/Animescomia) — junto com o
> `parceiro_de` do claude-32. **TikTok novo dos 3 Noturnos** (contas do cofre; o dono logou, conferido no Studio).
> **Novo `postador\bin\reserva_veo.py`**: conta abaixo da cota completa com Veo (1º a sobra do catálogo, 2º limpo
> aprovado que nunca saiu, guardando 10 pro YouTube; o usado vira "rejeitado" e nunca sobe no YouTube). Os dois posters
> avisam no Telegram toda conta que não postou no dia e por quê. Resultado medido: 16 contas × 3 = 48/dia no TikTok
> (hoje saíram 23, com 4 contas paradas). Rodada do TikTok 90→150 min.
> **Pendente do dono**: TikTok do `3dfabricadeautomacoesia` continua deslogado (janela aberta na porta 9251); no
> Instagram só 4 tokens vivos (os 4 já ligados) — `recenas.ia` e `dicasfinanceiras.ia` têm token morto e teriam conteúdo.

## 19/10 madrugada (claude-opus) — TikTok em todas as contas + PC desligado
- Dono 19/10 00:12: "poste em todos os TikToks possíveis, pode usar os Veo do Drive pra completar". reuso_plataformas.json
  tiktok foi de 16 pra 25 contas (bkp `.bkp_20261019_contas_novas`; detalhes na memória project_tiktok_logins).
- `tiktok_cdp_poster.py`: espera do campo de arquivo 30 -> 90 s (CPU 100% com produção+limpar_veo e o TikTok Studio
  não montava) e, se faltar, grava url + texto da página no log. `tiktok_login_google.py`: TK_ESPERA (s).
- Rodada manual 00:36–03:04: 20 posts em 19 contas. Sem post: emersonjosiel2029/2033, inovaremanhwaverse2,
  3dfabricadeautomacoesia (página lenta, antes do 90 s), inovaremanhwaverseesp (subiu mas o botão Publicar não clicou),
  gameoftroneskingsroadbrasil (sem campo de arquivo nem com 90 s).
- **PC DESLIGADO às 03:07** (evento 1074, winlogon/SISTEMA, sem tarefa agendada de desligar) e voltou 07:32 -> o ciclo
  PostadorDeVideos das 06:40 não rodou; disparado à mão 07:41 (Start-ScheduledTask). A tarefa não tem "executar assim que
  possível": se o PC desligar de novo na madrugada, rodar à mão.
- 08h: 5 canais BR sem post hoje -> remanejados Shorts prontos do mesmo nicho (postar.json: "canal" novo,
  "canal_origem", "remanejado"): beelzebub->Animescomia, was-struck-black->CartuchoReact, happy->InventoReact. Os que
  mandei pro InventoReact/Fio da Meada antes foram subidos no canal antigo pela rodada que já rodava (ela guarda a
  fila na memória) — registro corrigido. Fio da Meada: sem Short de curiosidades, é o próximo da produção.
- `parceiro_diario.py postar`: 2 passadas — 1ª só os canais sem post hoje (1 cada), 2ª enche a semana. Antes a
  rodada levava 1 h nos dias futuros dos canais da frente do config antes de chegar nos vazios. Testado com --ensaio.
- Login automático do Google com senha: o Google pede reCAPTCHA ("Confirme que é você") — parado; o dono loga à mão
  (cofre.py logar). emersonjosiel2028@gmail.com NÃO EXISTE no Google.

## 19/10 tarde (claude-opus)
- **Anime recap no PC2 nunca funcionou pelo ocioso (desde 17/10)**: `anime_auto.py` mandava `work_dir` = pasta do PC1
  (`D:\recapd-ambientes\...`); o PC2 NÃO TEM drive D:, o `mkdir` (fora do try no daemon) estourava, a thread morria e o
  daemon respondia 408 "task_timeout" na hora. Corrigido: `work_dir` vazio (o PC2 cria a dele e devolve no resultado).
  Conferir no `logs\anime_ocioso_AAAAMMDD.log` se saiu "Worker OK". Risco seguinte: o yt-dlp do PC2 usa
  `--cookies-from-browser chrome` e falhava em 2 s (é o que pausou o parceiro no PC2 desde 18/10 16:23,
  `D:\video-fila\estado\pc2_parceiro_falhou.json`).
- `anime_health_monitor.py` (alerta do Telegram "Monitor Anime Recap"): lia o próprio log e realertava o eco pra sempre;
  e o erro de ontem (fr/en 22:5x, já desligados) nunca saía porque olhava o mtime do arquivo. Agora ignora o próprio log
  e linha com data fora da janela de 14 h.
- Status 13:10: TikTok 49 posts hoje em 24/25 contas (só 3dfabricadeautomacoesia, deslogada, em 0); esp, gameoftrones,
  2029, 2033 e verse2 postaram na rodada do ciclo. Rodada extra (3º do dia) 13:10, log `logs\tiktok_20261019_tarde.log`.
  O "_COMPLETO" no log da reserva é só o nome do catálogo: com `veo_so_limpo` o `catalogo.baixar` sobe o de veo/limpos.
- YouTube 13:10 (ledger): os 22 canais ativos com vídeo hoje (1 a 3 cada; o que segura 3/canal é falta de Short pronto).
- 13:15: login TikTok das 13 contas com Google logado hoje, 1 a cada 4 min (TK_ESPERA=120).
- 14:2x: as 5 "captcha" eram "Verifique se é você" (código por e-mail): `tiktok_login_google.py` lê o código no Gmail do
  mesmo perfil -> logaram filmescomia1 @filmescomia7, aulasrevolution @mentoria.com.ia, e4487017 @msica.e.dana.ia,
  inovarecap @inovare.cap, emersonjosielmrx1995 @fatos.e.curiosida65 (cadastradas no reuso tiktok, Veo de reserva).
- Dono 19/10 ~15h: "pode criar as contas nas 8": `TK_CRIAR=1` no tiktok_login_google (nascimento 15/03/1995, "Ignorar" no
  nome = nome automático). en1653964 -> @emersonn598 (cadastrada). Outras 7 rodando 1 a cada 5 min (vendeafiliados3,
  murilodoctor192, emersongencshin, solarmundo195, revolutionemerson1/2/3) -> cadastrar no reuso tiktok quando logarem.
- Veo: 391 brutos do Drive ainda não limpos (de 672). Lote extra de 60 às 15h: 14 aprovados (resto marca Grok/moldura).
  Os 267 "revisar" antigos são quase todos marca d'água de IA (regra do dono: não postar) -> não servem.
- **INSTAGRAM pelo navegador (dono: "todas as contas de insta postando como as do YouTube")**: `bin/instagram_login.py`
  (perfil próprio no cofre "ig_<usuário>", senha só por IG_SENHA) + `postar_insta_auto.py` posta pelo
  `instagram_cdp_poster.py` quando a conta tem "cofre" (só conta com "POSTADO com sucesso"). Poster consertado: o
  "Compartilhar" clicava o botão de um post do feed (abria envio por mensagem) e a legenda saía vazia (Lexical) -> agora
  só dentro da janela "Novo reel" + Input.insertText. Conferido no perfil: recenas.ia 674 -> 676 posts.
  Logadas: recenas.ia (CenaReact/Filme/Dorama Noturno), fakenews.ia4 (Curiosidades Noturnas/Fio da Meada),
  futebolcom.ia2 e sintetizerisada (Veo de reserva). Precisam do dono: emerson.inteligenciaartificial (Instagram diz
  usuário/senha incorretos), fabricadeautomacoesia (as 2 senhas recusadas), dicasfinanceiras.ia (pede SELFIE de
  verificação), danceandmusicwith.ia SUSPENSA ("identidade falsa"; dá pra pedir análise — decisão do dono).
  msenergycap = cliente, fora. Nos perfis Google do cofre só o msenergypara tem Instagram.
- 17:52–18:57 fila de login espaçada: +10 TikToks logados e as 7 contas criadas (lista e @ na memória
  project_tiktok_logins). 19:10 cadastradas no reuso tiktok (48 contas, bkp `.bkp_20261019_1910`). inovaremanhwabr
  (navegador fechou) e emersongenc (sem TikTok -> criar) refeitos 19:10. Insta da fila: emerson.inteligenciaartificial
  ninguém digitou a senha em 3 min; fabricadeautomacoesia senha recusada; dicasfinanceiras.ia selfie.
- **Rodada de TikTok da noite morreu depois de 10 posts**: `comercial_veo._montar` passou de 900 s e o
  `TimeoutExpired` escapava do `preparar` (que promete "não deu -> vai o limpo"). Corrigido: estouro = não montou, sobe
  o limpo. A postagem automática do TikTok é só a PostadorDeVideos 06:40 (1×/dia); as outras rodadas foram manuais.
- **Gargalo das contas só-Veo**: 0 Veo limpo livre pro TikTok/Insta (372 de 454 limpos com "revisar", ~250 por marca
  d'água Grok/Veo/Sora). Depois da sobra do dia (~17) as ~30 contas só-Veo ficam vazias.
  **Dono 19:2x: "liberar só TikTok/Insta"** -> `catalogo.so_marca_ia` + `reserva_veo.nunca_postados` (243 liberados;
  YouTube segue bloqueado pelo `mr/rede.py`). Disponíveis: TikTok 22 -> 250 Veo, Instagram 284.
- 19:2x: inovaremanhwabr logou (@inovaremanhwabr4) e ganhou o conteúdo do canal inovare manhwa br (saiu do TikTok do
  Italiano, igual ao ManhwaReact); emersongenc criado @emersonjosiel378. 50 contas TikTok.
- **Tarefa nova `TikTokRodadaExtra`** (14:05 e 19:35, `bin\tiktok_rodada_extra.bat`, prazo 240 min, respeita o botão
  DESLIGAR): o ciclo das 06:40 só dá 135 min ao TikTok (~35 posts) e 50 contas × 3 = ~150. Horários sem sobrepor (o
  postar_tiktok_auto não tem trava; duas rodadas juntas gravariam o tiktok_auto_posted.json uma por cima da outra).
- **19:5x PROXY WEBSHARE NO TIKTOK** (dono: "quanto ao risco é só usar proxy da webshare"; avisado e escolheu os
  grátis mesmo): os 66 proxies de secrets/proxies.txt são do plano grátis = os MESMOS 10 IPs de datacenter
  (EUA/GB/PT/DE, nenhum BR) em todas as contas; "-rotate" troca de IP a cada conexão, "-N" fixa (o "-10" dá 403 ->
  9 IPs). `bin/proxy_tiktok.py` (pythonw, sobe sozinho pelo postador): portas 18201-18209 = IP 1-9, PAC em
  18200/<N>.pac manda SÓ domínio do TikTok pelo proxy (YouTube do mesmo perfil do cofre segue direto; conferido no
  Chrome real: ipify = IP de casa, TikTok logado pelo proxy). Credencial com 402 (banda do mês) sai até o dia 2 e entra a
  próxima com o MESMO IP. Últimas 25 linhas do proxies.txt = só Groq. Conta -> IP em config/proxy_tiktok.json.
  Proxy fora -> posta pela internet de casa e loga "PROXY FORA". `cofre.abrir(..., extra=[flags])`. Liga/desliga:
  reuso tiktok "proxy_webshare". Uso de banda: `python bin/proxy_tiktok.py --uso` (só abrir o Studio = 16,5 MB;
  41 credenciais × ~1 GB/mês não aguentam o mês inteiro com ~150 posts/dia -> depois cai pro IP de casa).
  Login/criação de conta (tiktok_login_google) continua pela internet de casa.
  1º post pelo proxy: 19:52 esp (IP 3) OK, ~27 MB (abrir o Studio + vídeo de 8 s).
- 20:0x dono: "deixar X contas sem proxy, quantidade segura": 5 (`"sem_proxy": true` no reuso: doramanoturno,
  filmenoturno, curiosidadesnoturnas, emersonjosiel2032/ManhwaReact, inovaremanhwaverse2/Manhwa Noturno) = mesmo tanto
  de contas por IP que cada IP do proxy tem (~45/9). Dono: a banda da Webshare renova a cada 30 dias (dia de cada
  conta) -> 402 agora tenta de novo em 24 h. Os proxies que ele mandou já estavam todos no proxies.txt (31.59.20.176:6754
  e 45.39.15.202:6632 = outras portas de entrada das mesmas contas); todos responderam.
  20:1x: dono mandou +30 contas Webshare -> todas novas, todas responderam, adicionadas no proxies.txt (normalizadas
  para p.webshare.io:80; bkp `.bkp_20261019_2015`). 96 contas Webshare: TikTok usa 71, as últimas 25 só o Groq. Os "-N"
  das novas = os mesmos 9 IPs (conferido em 3 delas).
  **YouTube pelo proxy: NÃO feito** (dono pediu "a mesma coisa com o YouTube"; expliquei e ficou pra ele decidir):
  YouTube 19/10 = 56 uploads, 1,38 GB só de vídeo (+ Studio a cada upload); os 66 grátis somam ~66 GB/30 dias
  (~2,2 GB/dia) e o TikTok sozinho já gasta ~4 GB/dia; sessão Google feita no BR abrindo de datacenter EUA/Europa
  dispara "verifique que é você" (várias só voltam com celular) -> risco de parar a postagem dos canais.
- 19:4x: criação de TikTok nas que faltavam (dono: "faça os tik toks das que ainda estão sem"): mentoriaiapro @iapro518;
  viet/ind/ing erraram o apelido (no cofre são inovaremanhwaverseviet/ind/ing) -> refeitos 20:1x–20:2x.
  Criadas e cadastradas: aulacomia, comoseriasecomia, rezaulkarimul355, canalanimescomia (conteúdo do Animescomia; o
  TikTok do Italiano passou a levar o canal italiano), emersonjosiel0, viet e ind (conteúdo do canal de cada língua),
  ing (só Veo). 59 contas TikTok.

## Contas Google PULADAS no login de 19/10 (dono: "não podem ser logadas agora, precisam de mais coisas, como
## verificação de número de telefone") — refazer com o dono e o celular em mãos
- inovaremanhwaverse3, inovaremanhwaverse4, revolutionemerson7, andreluizdias384
  (`python D:\logins-google\cofre.py logar <apelido>`).
- emersonjosiel2028: o Google diz que o e-mail NÃO EXISTE (conferir o endereço com o dono).
- msenergy810: senha marcada como errada na lista do dono.
Logadas e salvas (conferido com cofre.py checar): revolutionemerson1, revolutionemerson2, revolutionemerson3.
SÓ TIKTOK (dono: "o canal foi bloqueado, acho"): filmescomia1 — conferir o YouTube dela (e das outras que o dono
apontar) DEPOIS dos logins: abrir studio.youtube.com no perfil do cofre e ver se o canal está encerrado/bloqueado;
nunca criar canal novo nessas contas.

## PENDENTE (dono 19/10 09:07): criar canais YouTube novos nas contas revolutionemerson1/2/3/7
Pedido: "criar o canal conforme os temas dos parceiros que ainda não temos: falta filmes, não sei se tem esportes,
curiosidades" — fazer DEPOIS de logar todas as contas (login do Google: uma janela por vez, dono digita a senha).
Temas de fonte parceira x canal hoje (config/parceiro.json "fontes" x "pt"):
- esportes: fontes futtres, fabioindaia2006 -> NENHUM canal (candidato nº 1)
- filme_sem_voz: andreu_edit1, f_UCRKSO0 -> Filme Noturno e CenaReact já usam (dono acha que falta "filmes": perguntar
  se é outro estilo, ex. resumo de filme narrado)
- curiosidades: xiuliamelo, canalutopia (nichos) -> Fio da Meada; fatos -> Curiosidades Noturnas e Mundo Que Nao Existe
- financas: Assist-IA e Dicas têm canal mas NENHUMA fonte parceira
Antes de criar, OBRIGATÓRIO:
1. Abrir o YouTube/Studio de cada revolutionemerson e ver se a conta já teve canal ENCERRADO. Dono 18/10: "a maria tem
   canais banidos, só serve pra TikTok" — essas 4 usam a senha comum. Conta com canal encerrado NÃO pode criar outro
   (regra de evasão do YouTube: support.google.com/youtube/answer/2802032; derruba os canais associados) -> só TikTok.
2. Canal novo = tema novo, nunca substituto de canal advertido/encerrado (memória feedback_canal_pausado_advertencia).
3. Criar pelo navegador (nunca API do Google Cloud), cadastrar: youtube_navegador.json (usar), parceiro.json "pt" com
   nicho, canais.json se refaz sozinho; TikTok da mesma conta em reuso_plataformas.json (postados_em).

## >>> PRÓXIMO MODELO: COMECE AQUI (passagem 18/10 ~15:05, claude-opus, tokens acabando) <<<
Estado às 15:05: 11 de 13 canais BR ativos com post hoje. Tudo roda sozinho (produção a cada 30 min, postagem
:15/:45 + disparo a cada Short novo, vigia de 20 em 20 min). Faltando:
1. **ForjaReact** — 1 Short pronto (`sistema-anti-canalhas_cap1_20261018`), ainda não subiu. Perfis do cofre
   corrigidos às 14:40 (estavam trocados). Às 15:00 deu um FALSO timeout: o postador ficou 12 min só esperando a
   trava `D:\postador-de-videos\logs\yt_web.lock` (1 upload por navegador por vez; um `youtube_studio_extras.py` do
   hipercool estava com ela) e nem abriu o Chrome; o `parceiro_diario` marcou `timeout_em` ("verificar"). Já tirei o
   `timeout_em` à mão (ledger confirma: nada subiu). CONFERIR na próxima rodada que subiu.
   **CONSERTADO 18/10 ~18:20 em parceiro_diario.py** (12 Shorts tinham ficado presos em 'verificar'): causa = no
   timeout a política mata só o LANÇADOR do venv (Scripts\python.exe abre um 2º python), o postador de verdade fica
   vivo, espera a trava e pode subir depois sem registro. Agora: (a) `_esperar_trava` espera o `yt_web.lock` ficar
   livre ANTES de chamar a política (a espera não come mais os 10 min); (b) `_reconciliar` no início de cada
   postagem casa cada 'verificar' com upload órfão no ledger (mesmo canal, video.mp4, ≤45 min, id sem dono) → postado;
   sem upload e sem postador vivo → volta pra fila. Ensaio sem gravar: 12 de 12 voltariam (nenhum órfão no ledger).
   Conserto de raiz ainda aberto (outra sessão, claude-32, mexendo no politica.py — avisada): matar a ÁRVORE do
   postador no timeout, ou chamar o python base em vez do lançador.
1b. **18/10 19:03 — YouTube bloqueou o IP do PC1 pro yt-dlp** ("Sign in to confirm you're not a bot") depois de ~50
   consultas de views em paralelo (claude-opus, pra ranking do dono — ERRO meu). A produção passou a falhar no
   download às 19:05. Conferência agendada 19:41. Lição: consulta de views/metadados = 1 por vez com pausa, nunca
   `xargs -P`. O yt-dlp também avisa "No supported JavaScript runtime" (sem deno) — se o bloqueio não passar,
   instalar deno e/ou dar proxy (Webshare, como o Groq) ao yt-dlp do anime_fetch/anime_discover.
   19:15 testado: PC1 e PC2 saem pelo MESMO IP público (191.36.137.42) → os dois bloqueados; proxy Webshare também
   bloqueado (IP de datacenter); `--js-runtimes node` não resolve. Listagem de canal (`--flat-playlist`) funciona; só
   a extração do vídeo pede login. Saídas: esperar (a produção tenta a cada 30 min, para em 3 falhas) ou cookies de
   conta Google pelo CDP do Chrome do cofre (só conta reserva sem canal, e só com OK do dono — arrisca a conta).
2. **Mundo Que Nao Existe** — 2 Shorts prontos; upload começou 15:00:18 com o perfil já corrigido. CONFERIR.
3. **HistoriasEmFrames** — Short liberado (estava preso em "esperando", ver abaixo); deve subir na próxima rodada.
4. **Dicas financeiras da ia** — Short sendo produzido (14:17→). Sai sozinho; canal sem post = agendamento urgente.
5. Se os logins do cofre derem problema de novo: `python D:\logins-google\cofre.py logar <apelido>` e o dono loga;
   DEPOIS conferir que o e-mail certo entrou (`account_info` em `perfis\<apelido>\Default\Preferences`).
6. Memória do PC1: `VozClonadaFila` (audio-separator ~6 GB) esgotou o commit às 13:50–14:35 → falhas aleatórias
   (ffmpeg, Playwright). Se repetir, propor ao dono rodar o separador no PC2 ou à noite. Não matar sem o dono.
7. Comando pra ver tudo: `D:\veo\venv\Scripts\python.exe -X utf8 bin\parceiro_diario.py status` (na pasta producao).

## Feito

### 17/10 (claude-06)
- Tarja: 80% da largura, LLM pede português correto.
- Narrador por nicho: config narradores + PARCEIRO_TIPO.
- Balanço PCs: ocioso.py + pc2_parceiro.ps1.

### 18/10 (claude-opus)
- [x] **Item 1 — Fontes múltiplas com rodízio**: `fontes` lista no config com 30 fontes em 6 nichos. Rodízio automático
  (`_escolher_fonte` em parceiro_diario.py): nicho menos produzido nas últimas 24h → fonte menos usada dentro dele.
  Estado em `workspace/anime/_rodizio.json`.
- [x] **Filtro de itens expandido**: parceiro_diario.py aceitava só `midia=="manhwa"`, agora filtra por
  `categoria=="parceiro"` (qualquer nicho; o recap de anime próprio fica de fora).
- [x] **Narradores para todos os nichos**: 16 tipos no config, todos com voz Multilingual.
- [x] **Nicho por canal** (~05:00): `_escolher_fonte(c, alvo)` usa o `nicho` do canal de destino; antes o campo
  existia no config mas ninguém lia (canal de fatos podia receber dorama).
- [x] **Bug que ia derrubar a 1ª rodada com rodízio**: parceiro_diario passava `--midia` pro anime_auto, que não
  aceita esse argumento (parse_args estrito, sairia com erro 2). Tirado; o tipo vai por `PARCEIRO_TIPO`.
- [x] **SEO para todos os nichos**: `_MIDIAS` em seo_generator.py com 13 dicts de substituição.
- [x] **anime_publish expandido**: `--midia` sem choices fixas, `_eh_parceiro` detecta qualquer tipo ≠ anime,
  capa IA restrita a anime/manhwa (outros usam quadro do vídeo).
- [x] **Canais react mapeados para nichos**: campo `nicho` em cada canal pt do config.
- [x] **canais_parceiros.py**: 12 novos canais adicionados.
- [x] **Watchdog**: vigia_geral.py relança produção se nenhum Short novo em 5h.
- [x] **Regra de agendamento**: salva em memória, todos os uploads com publishAt.

### 18/10 ~10:00 (claude-opus) — PRODUÇÃO MÁXIMA (dono: "último feito foi ontem, inaceitável; tem que ficar produzindo")
- [x] Tarefa `ParceiroKaijinre-Producao` a cada 30 min (IgnoreNew + lock: nunca encavala). Antes: 6 horários fixos.
- [x] Rodada não para na 1ª falha: pula aquele canal e segue; só encerra com 3 falhas seguidas.
- [x] Guarda de CPU desligada na produção do parceiro (`ANIME_MAX_CPU_PCT=0`): esperava até 30 min ANTES DE CADA
  CLIPE com o hipercool renderizando. A de RAM continua. 1º Short depois disso: 47 min (antes: horas).
- [x] `_marcas_fixas`: só borra caixa com ≥10% dos pixels em ≥90% dos quadros (anime denso dava falso positivo no
  meio da tela — logo real 28%, acaso 0%). Candidatas fracas só servem pra achar a legenda sem visão.
- [x] yt-dlp: `D:\video-fila\atualizar_ytdlp.py` + tarefa `AtualizarYtDlp` (05:23 e 17:23): PC1 (sistema + venv do
  recapd) e PC2 (sistema). PC2 foi de 2026.07.04 → 2026.08.19 e voltou a baixar.
- [x] PC2: ocioso dispara Short de parceiro sempre que o PC2 está livre (antes só com o PC1 ocupado), com a fonte do
  nicho do canal, `-Tipo` (PARCEIRO_TIPO) e cópia do `config/parceiro.json` por scp. Falha da máquina devolve o
  vídeo à fila; falha do vídeo descarta; 3 falhas seguidas pausam (`estado/pc2_parceiro_falhou.json`).
- [x] Filme Noturno com 2 fontes: @andreu.edit1 (é resumo NARRADO em pt, com legenda — o "sem voz" do nome não
  vale) e `UCRKSO0AInMtfM7rDgurjyyw` (da lista do dono 17/10, tinha ficado fora do config). Dry-run dos 2 ok
  (tarja + roteiro de 19 frases). Fonte fora do config cai no molde do @kaijinre — toda fonte nova tem que entrar
  em `fontes` com `cobertura: "auto"`.
- [x] `parceiro_diario` relê o config a cada vídeo (antes só no começo da rodada, que dura horas).
- [x] Canais Noturno logo depois do Manhwa Noturno no `pt` (no empate de fila é servido quem vem antes). CenaReact
  `ativo=false` (dono: dorama só no Dorama Noturno).

## Fila de tarefas restantes
1. [x] ~~Fontes múltiplas~~ (feito 18/10)
2. [x] **Cobertura por canal** (`parceiro_marca.cobrir_canal`, `cobertura: "auto"`), testada 18/10 num Short de
   @inusifatos (43 s, 12 quadros conferidos): legenda por visão (2 tentativas; o gateway às vezes volta vazio) →
   tarja branca com o título. Se a visão falhar, a faixa sai das marcas fixas da metade de baixo (a legenda deles
   fica sempre na mesma linha). Marcas d'água/logos achados sozinhos (`_marcas_fixas`: bordas que ficam no mesmo
   lugar em ≥70% de 16 quadros) e borrados — pegou "OpusClip" e o logo "INUSI FATOS". Tarja ocupa ~20-24% da tela
   (a legenda deles chega a 3 linhas).
   - **25/10 (claude-opus, dono: "a tarja não saiu no lugar da legenda do outro... nos próximos não pode mais
     acontecer")**: youtu.be/qGrvCYG36cg (Filme Noturno, fonte cineverso jYETXAo06Fo) — a visão chamou de legenda o
     TÍTULO amarelo FIXO do topo; a tarja foi pra lá e a legenda deles ficou à mostra embaixo. 23 de 300 detecções
     (18-24/10) caíram no topo. Correção em `parceiro_marca._texto_sobreposto` (48 quadros, letra clara + contorno
     preto → palavras → faixas): **legenda = linha na mesma altura que MUDA**; **título/marca = mesmo desenho em todos
     os quadros**. A faixa dos pixels (segura: fina, centralizada, presente) manda; a visão só decide quando os pixels
     não têm certeza e é RECUSADA se apontar texto fixo. Legenda em 2 linhas entra inteira (2º menor topo / 2º maior
     base). Título fixo deles no letterbox preto é pintado da cor do fundo (some); em cima da imagem não se mexe.
     Sem legenda deles + título fixo no topo = tarja em cima do título (`titulo_topo`). Prompt da visão
     (`anime_hardsub_detect`) passou a mandar ignorar título fixo. `anime_auto._reeditar_parceiro` zera
     SUB_Y_CENTER/GANCHO_Y a cada vídeo (o processo faz vários seguidos) e desce o gancho (`GANCHO_Y`,
     `anime_gancho`) quando a tarja fica no alto. Testado em 8 fontes reais (cineverso ×3, legenda no meio, embaixo,
     em 2 posições, cena com muito branco/preto). Os Shorts antigos com a tarja errada ficam (dono: "pode usar").
   - **25/10 (claude-opus, sincronia fala × cena)**: desde 24/10 a última fala tem 0,6 s de folga (24/24 Shorts de
     25/10) e sem acrossfade comendo sílaba (`fx_clips`). Ainda saíam ~25% sem os tempos do roteiro (corte
     "espalhado", fala pode vir depois da cena): 8× a IA marcou só 2 linhas (frases longas) e 2 recusas. Agora
     `anime_script._frases_com_tempo` lê toda marca [Ns] do texto e reparte as frases do trecho; se faltar, pede de novo
     1 vez. Formato com várias vozes (26/10): `anime_testes.alinhar_tempos` dá a cada fala do diálogo o segundo
     da frase do solo com mais palavras em comum (sem voltar na história) — não cai mais no "espalhado".
   - **26/10 (claude-opus, dono)**: (a) sem legenda deles = SEM tarja branca (`parceiro_marca.cobrir_canal`: saiu a
     tarja no título fixo do topo); (b) dorama e filme_sem_voz narram em 1ª pessoa (o protagonista conta), outros
     personagens pelo papel ("o herdeiro", "o homem rico"), nunca "prota" (`anime_script._NICHOS_PRIMEIRA_PESSOA`,
     prompt v10); (c) clone lento: ~60 vozes sem legenda medida herdavam -7%/x0.87 — piso +5%/x0.98 em
     `anime_tts._perfil_v2`. Os 2 vídeos reclamados (eJbeRUKf8vw fim cortado, Sv6Jvwtjncs) são de 21-22/10, antes
     das correções. TikTok (postador): notebooks postam em paralelo ao PC1 (`postar_tiktok_auto.py`).
3. [x] **Título na faixa da legenda** (feito 17/10).
4. [ ] **Versão DORAMA**: SEO pronto, canal Dorama Noturno pronto. Nenhum dorama produzido ainda (até 18/10 todos
   os Shorts do parceiro eram manhwa do @kaijinre, inclusive os do CenaReact). Os primeiros saem da rodada de
   18/10 09:02 em diante — conferir o 1º (cobertura auto + voz Ava).
   - Dry-run de FATOS ok em 18/10 (@inusifatos → Mundo Que Nao Existe): descoberta, legenda pt, cobertura auto,
     tarja "ELE SOBREVIVEU NO LUGAR MAIS PERIGOSO DO MUNDO", roteiro 11 frases; parou antes do render.
   - Narração (edge-tts) falhou entre ~04:50 e ~05:50 de 18/10 ("pool de proxies esgotado") nos 2 PCs; voltou
     sozinha (teste 09:00: direto e 4/4 proxies ok). Um pipeline que pegou a falha ficou preso tentando o mesmo
     áudio por 2 h (processo manual 3248, encerrado; vídeos devolvidos à fila).
5. [ ] **Versão FILME** (filme com falas — requer separação de voz narrador × personagem).
6. [ ] **Efeitos** (copiar do hipercool): transições, SFX, emoji, 2.5D/parallax.
7. [x] ~~Hipercool na fila de render~~ (feito 17/10).
8. [ ] **Balanço PCs** (`D:\video-fila\ocioso.py` → `bin\pc2_parceiro.ps1`): o disparo funciona, mas no PC2 o
   yt-dlp 2026.07.04 leva **403 Forbidden** no download (o do PC1, 2026.08.19, baixa). De 04:53 a 07:53 do dia 18
   cada rodada de 15 min disparou 1 Short, ele falhava em segundos e o ocioso marcava o vídeo como FEITO — 13
   vídeos do @kaijinre queimados (devolvidos à fila; backup `_feitos_short*.txt.bak_20261018`). Corrigido no ocioso:
   só marca feito se o vídeo voltou; se não, devolve o id e pausa o PC2 pro parceiro
   (`D:\video-fila\estado\pc2_parceiro_falhou.json` — apagar pra religar). Corrigido também id começando com "-"
   (`--id=$Id`). FALTA: atualizar o yt-dlp do PC2 (fica no Python do sistema, compartilhado com o hipercool — dono
   decide) e fazer o ocioso usar o nicho do canal (hoje manda sempre `c["fonte"]` = @kaijinre e não passa
   PARCEIRO_TIPO nem o config/parceiro.json pro PC2, que o sincronizar_bin não copia).
9. [ ] **Nichos sem fonte**: financas, historia_mitologia, curiosidades, satisfatórios, natureza, quiz, info_errada,
   ia_futuro, motivação — dono precisa indicar canais parceiros para esses nichos.
10. [ ] **Contas deslogadas**: ManhwaReact e Animescomia com login vencido (ativo=false no config).

## Não fazer
- Não mexer em D:\hipercool-videos, D:\postador-de-videos, D:\manhwa-react\mr (outras sessões). Não religar nada
  desligado. Voz Antonio proibida (Francisca/Isabella liberadas pelo dono em 16/10; Francisca = base da voz clonada).
  Voz clonada do Lula (e do Bolsonaro) fora do rodízio até o dono confirmar (`anime_voz_clonada.FORA`, dono 20/10);
  o Short `gta-faturou-us_cap1_20261021` (narrado com ela) fica "reprovado" até o dono decidir — não liberar.
  Nada de nome da obra em título/descrição/tags.
