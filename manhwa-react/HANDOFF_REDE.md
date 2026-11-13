# HANDOFF - Rede de canais YouTube (sessao de 04/10 13h ate 05/10 10h40)

Para o proximo agente. Leia nesta ordem:
1. **este arquivo** (o que existe, por que, como operar);
2. `REDE_ESTADO_E_PENDENCIAS.md` (diario de cada etapa, secoes 1 a 9);
3. `HANDOFF.md` (historico do pipeline de video ManhwaReact, de 01-02/10) e `CLAUDE.md` (regras do projeto).
Conversa inteira desta sessao: `historico_conversas/2026-10-04_05_rede/` (`sessao_2cfff72e_legivel.md` = so o texto;
`.jsonl` = bruto com as ferramentas).

`CANAIS_E_DISTRIBUICAO.md` foi escrito pelo agente ANTERIOR e esta **desatualizado/errado** em varios pontos (ver secao 3).

---

## 1. Resumo em 12 linhas

- Rede de **19 canais ativos** no YouTube, todos com Shorts em **portugues**, 1 video por canal por dia.
- Mapa unico: `D:\postador-de-videos\config\rede_canais.json` (nicho/angulo, persona, regras, horarios, credenciais, status).
- Postagem: `D:\manhwa-react\manhwareact.py rede` (codigo em `mr\rede.py`), chamado de hora em hora (tarefa `ManhwaReact-Rede`)
  e no ciclo das 06:40 (`PostadorDeVideos`). Sobe so o que publica nas proximas 3 h (sem rajada), agendado (private + publishAt).
- Fontes de video: Shorts do manhwa-react (`D:\hipercool-materiais\manhwa-react\shorts|cortes\<canal>\`) + historias-em-frames
  (`D:\hipercool-materiais\historias-em-frames\videos\prod\<genero>\<id>\postar.json`).
- "Diretor da rede" (LLM) da nota de encaixe video x canal; cada video vai para UM canal so; canal com fome ganha prioridade.
- Agente por canal (LLM com persona) reescreve titulo/descricao/tags/1o comentario, testando **estrategias** (titulo, gancho,
  comentario, horario) e aprendendo com as views de 48 h (painel grava `_analise\rede_aprendizado.json`). Revisor barra
  palavra proibida. Se o video muda de canal, o @ gravado no canto e trocado (ffmpeg).
- Toda postagem passa pela politica do postador (`bin\politica.py`): parada geral, bloqueio, cota (3/canal, 20/dia), aprovacao.
- Painel HTML: `D:\postador-de-videos\painel\index.html` (atalho "PAINEL DOS CANAIS" na area de trabalho; tarefa 3/3 h).
- **Aprovacao humana continua ligada**, mas o dono DELEGOU ao agente (05/10): o agente confere quadros e aprova.
- **Nunca ligar o gerador de likes/comentarios** (`D:\projetos-navegador`, MEGA ENGAGE) - decisao firme, ver secao 9.
- PC precisa **reiniciar** para valer a memoria virtual nova (renders falham por memoria ate la).

---

## 2. Pedidos e decisoes do dono (em ordem)

04/10 (pedido original): conectar o manhwa-react ao postador; processar `D:\downloads\videos` (= as mesmas 25 gravacoes de
`1-COLOQUE-AQUI`); ao menos 1 video bom por dia em cada canal; corrigir os erros do agente anterior; tags/titulo/descricao
por canal; melhores horarios por publico; painel HTML de inscritos/comentarios/likes; ligar um gerador de likes e comentarios
para dar "forca inicial" (RECUSADO - secao 9). Os 10 canais novos com refresh_token: ManhwaReact-ia, CenaReact, InventoReact,
AssistIA Investimentos, HistoriasEmFrames, CartuchoReact, @CodigoInteligente-n7j (hoje "fiodameada"), ForjaReact,
MundoQueNaoExiste, DicasFinanceirasDaIA.

Respostas do dono as 4 perguntas (04/10 ~14h):
1. Videos no canal errado: "se for bom e nao fizer mal, deixe la e poste outros melhor direcionados; se nao, prive e refaca".
2. Videos antigos da epoca do spam + duplicados: **privar todos**.
3. Canais sem conteudo de react: "aproveite o que temos distribuindo o melhor possivel por tema; muitos agentes, um por canal,
   adaptando o conteudo para a cara de cada canal; todos tem que ter pelo menos um video bom por dia".
4. Inovare esp suspenso: nao parar os canais de react; pausar os Inovare internacionais (depois revertido no item 05/10 abaixo).

04/10 noite: "seus tokens estao acabando, deixe rodando e documente" -> "corrija e termine tudo"; pediu cron para continuar
(feito: tarefa do Claude 05/10 07:28, ja disparou).
05/10 madrugada:
- "**voce que deve aprovar** os 27 videos e aumentar a memoria virtual" -> aprovados; memoria = gerenciada pelo sistema.
- "os 2 a verificar sao o mesmo canal": @IAAgora-n7h = HistoriasEmFrames; @IASemLimites-h4b = CartuchoReact (aliases).
- "os Inovare internacionais: vamos postar Shorts nacionais de react, um por dia, comece agora" -> ativados (react pt-BR).
- "o sistema ja esta adaptado para os 19 canais com multi-agentes explorando varias estrategias?" -> era so parcial;
  implementado: angulo proprio por canal, estrategias + aprendizado, revisor, fome, upload na hora certa, trava.
05/10 10h: "salve todas as informacoes e historico para outro agente continuar" -> este arquivo.

---

## 3. O que o agente anterior deixou errado (e o que foi feito)

| Problema | Correcao |
|---|---|
| `distribuir_videos.py` postou 13 Shorts **publicos na hora**, fora da politica (sem aprovacao, 19 uploads/dia > teto 12), 12 deles no canal errado (anime em canal de financas/historias/forja; react pt-BR nos canais french/hindi/ita/ru/ind) | arquivo renomeado `distribuir_videos.py.DESATIVADO`; os 13 arquivados em `_postados\react` + `publicados.json`; 10 privados e devolvidos a fila do canal certo (a maioria ja reagendada la; o resto entra nas proximas rodadas) |
| Arquivos postados continuavam na fila de prontos (o ciclo 06:40 iria repostar nos canais principais) | `scripts\arquivar_distribuidos_2026-10-04.py` |
| "Inovare Manhwa esp/eng 403 = API desabilitada" | ERRADO: a API diz **"The YouTube account of the authenticated user is suspended"** para o esp. eng listou normal (o 403 do upload nao foi explicado) |
| ManhwaReact (`novo_mente_artificial_i5r`) e ManhwaReact-ia (`novo_manhwareact_ia`) tratados como 2 canais | sao o MESMO canal UC5Za1hPxak0iufFcJ4UsK9w; politica soma aliases |
| Handles no config errados ("@ManhwaReact", "@CenaReact") gravados nos videos | handles reais vem do mapa: @manhwareact-ia, @cenareact-f3j... |
| Duplicados entre canais (HD Xbox em 3 canais, "alcool da gasolina" 2x no InventoReact, espada no Mundo, Rei Demonio 4x no inovaremanhwabr) e dezenas de "Curiosidades IA / Cerebro Digital / ETs roubam wifi" de 08/2026 publicos nos canais novos | **147 privados** (nao apagados), log em `logs\limpeza_2026-10-04.json`; script `scripts\limpeza_rede_2026-10-04.py` (idempotente) |
| Meme `.avif` derrubava o render (`Option loop not found`) | `mr\memes.py::_como_png` converte para PNG (cache `assets\memes_png`) |

Mantidos no lugar (encaixam): Oshi no Ko (ManhwaReact), anime de trader (AssistIA), Vegeta (HistoriasEmFrames),
cama-quarto (MundoQueNaoExiste). Metadados de 21 videos publicos recentes reescritos (`scripts\ajustar_metadados_rede.py`,
log `logs\metadados_ajustados.json`). **Videos proprios do AssistIA/Dicas NAO sao reescritos** (no teste o agente transformou o
video do produto do dono em "golpe do investimento" e escreveu "aumentou meu resultado").

---

## 4. As 49 credenciais (`D:\credenciais-canais\youtube_canais.json`)

23 suspensas (22 de 04/09 + esp) | 4 desativadas | **19 canais ativos** (22 credenciais: ManhwaReact, HistoriasEmFrames e
CartuchoReact tem 2 credenciais cada). Nenhuma credencial sobra sem destino.

Projetos OAuth: quase todos os canais novos usam o projeto Google **100689820764** (cota da API compartilhada; aguentou ~30
uploads + ~300 chamadas em 04/10). A credencial i5r (projeto 65933226849) estourou a cota em 04/10 - por isso a principal do
ManhwaReact e `novo_manhwareact_ia`. YouTube Analytics API **desligada** no projeto 1006898207642 (link no erro 403).

Os 19 canais ativos + o suspenso (gerado do mapa em 05/10):

| slug | canal | handle | credenciais (1a = principal) | status | angulo/nicho (resumo) | horarios BRT | cat |
|---|---|---|---|---|---|---|---|
| manhwareact | ManhwaReact | @manhwareact-ia | novo_manhwareact_ia, novo_mente_artificial_i5r | ativo | react de anime da temporada, isekai, light novel e manhwa adaptado (Re | 12:10 18:40 20:30 | 1 |
| animescomia | Animescomia | @animescomia | KOpyXE9rBy1YirlZ | ativo | anime shonen classico e de luta: Dragon Ball, Naruto, One Piece, Bleac | 11:40 17:50 21:10 | 1 |
| inovaremanhwabr | inovare manhwa br | @inovaremanhwabr | hNQrW5ouNe0Ni5Me | ativo | manhwa, webtoon, manhua e donghua: cultivo/murim, regressao, sistema,  | 13:00 19:20 22:00 | 1 |
| cenareact | CenaReact | @cenareact-f3j | novo_universo_ia_d6s | ativo | filmes, series, novelas, sitcoms e desenhos adultos (Family Guy, Simps | 12:00 19:00 21:30 | 24 |
| inventoreact | InventoReact | @inventoreact | novo_ia_agora_h3n | ativo | inventos, gadgets, experiencias caseiras, construcao, casas e veiculos | 11:30 17:30 20:00 | 28 |
| cartuchoreact | CartuchoReact | @cartuchoreact | novo_cartuchoreact, novo_ia_sem_limites_h4b | ativo | games retro e atuais, consoles, desbloqueios, hacks, emuladores, chips | 12:30 18:10 21:40 | 20 |
| forjareact | ForjaReact | @forjareact | novo_forjareact | ativo | forja de espadas, cutelaria, ferreiro, marcenaria, restauracao, artesa | 11:00 17:10 20:10 | 26 |
| mundoquenaoexiste | Mundo Que Nao Existe | @mundoquenaoexiste | novo_mundoquenaoexiste | ativo | coisas que parecem impossiveis ou de outro mundo: videos de IA, situac | 12:20 19:40 22:10 | 24 |
| historiasemframes | HistoriasEmFrames | @historiasemframes-emerson | novo_historias_em_frames, novo_ia_agora_n7h | ativo | historias curtas narradas e ilustradas de superacao, drama familiar, f | 13:10 20:00 22:20 | 24 |
| fiodameada | Fio da Meada | @codigointeligente-n7j | novo_codigo_inteligente_n7j | ativo | historias de misterio, terror, suspense, segredos revelados, comedia e | 19:10 21:40 23:00 | 24 |
| assistiainvestimentos | Assist-IA Investimentos | @assistiainvestimentos | novo_assistiainvestimentos | ativo | investimento com IA, cripto, trader, mercado financeiro, dinheiro, his | 07:40 12:15 19:30 | 27 |
| dicasfinanceirasdaia | Dicas financeiras da ia | @dicasfinanceirasdaia | novo_dicasfinanceirasdaia | ativo | financas pessoais, economia, quanto custa, vale a pena financeiramente | 08:10 12:40 20:20 | 27 |
| inovare_french | inovare Manhwa french | @inovaremanhwafrench | GG97QQt8lmyv0dDG | ativo | romance, casais, shoujo, slice of life e momentos fofos ou emocionante | 10:40 16:50 20:50 | 1 |
| inovare_hindi | Inovaremanhwaversehindi | @inovaremanhwaversehindi | GtuH5ezUK8eBaC60 | ativo | lutas epicas, power-ups, transformacoes e cenas de hype de anime e man | 11:10 17:20 21:20 | 1 |
| inovare_ind | Inovare Manga ind | @inovaremanhwaverseind | nYsAKUb3DbR1QOEm | ativo | isekai, reencarnacao, sistema, jogos e protagonista overpower; compara | 10:20 16:30 22:30 | 1 |
| inovare_eng | Inovare Manhwa eng | @inovaremanhwaverseeng | UYjkdFO3V3kjmKU5 | ativo | viloes, traicoes, plot twists e revelacoes chocantes de anime e manhwa | 12:50 18:20 21:50 | 1 |
| inovare_ita | inovaremanhwaverseita | @inovaremanhwaverseita | 7zpNZNll2jlBnQ0J | ativo | comedia, momentos engracados, memes, parodias e animacoes caseiras de  | 11:50 17:40 20:40 | 1 |
| inovare_ru | inovare manhwa verse ru | @inovaremanhwaru | TkfzifstYEoG4jKg | ativo | anime sombrio, seinen, terror, drama pesado, cenas tristes e tragedias | 13:20 18:50 23:10 | 1 |
| inovare_thai | Inovaremanhwaversethai | @inovaremanhwaversethai | q3mik36FjtTgFkNC | ativo | donghua (animacao chinesa), manhua, cultivo, artes marciais, murim e f | 09:50 15:40 19:50 | 1 |
| inovare_esp | Inovare Manhwa esp | - | 0RW4rz4ekPpkPcZx | suspenso |  |  | 24 |

Angulos dos 7 Inovare internacionais (react em portugues, ativados em 05/10): french = romance/fofo, hindi = luta/hype,
ind = isekai/ranking de poder, eng = vilao/plot twist, ita = comedia/memes, ru = sombrio/seinen, thai = donghua/cultivo.
Regras do dono no mapa (campo `regras`) para AssistIA e Dicas: nunca "robo"/"bot" (sempre "a IA", no feminino), nunca prometer
lucro/ganho garantido nem que a IA preve o mercado.

---

## 5. Como funciona (fluxo de um video)

```
gravacao (1-COLOQUE-AQUI)  --tarefa ManhwaReact-Lote 02:00-->  manhwareact.py batch
   editorial (LLM) escolhe 1 dos 19 canais pelo tema e pela fila de cada um (mr/editorial.py::_fila_por_canal)
   render com handle/cor do canal -> hipercool-materiais/manhwa-react/shorts/<slug>/<id>.mp4 + .postar.json
aprovacao (o agente, por delegacao do dono): politica.marcar_aprovacao(...)  ou  manhwareact.py rede --aprovar [--tudo]
manhwareact.py rede  (de hora em hora :17, e 06:40)  -> mr/rede.py::agendar
   trava work/rede.lock (1 rodada por vez; mais de 90 min = abandonada)
   inventario (react + historias, aprovados, nao postados; reabertos.json libera os devolvidos)
   vagas por canal no dia (max_dia=1) + fome (pouco video nos ultimos 3 dias = bonus)
   notas do diretor (LLM, cache work/rede_notas.json, recalcula se mudar o nicho de algum canal)
   distribuicao gulosa (nota + bonus do canal original + fome; nota_min 6; serie so no canal original e em ordem)
   horario (braco 'horario' da estrategia) -> se publica em mais de 3 h: so reserva, sobe numa rodada seguinte
   estrategia (titulo/gancho/comentario) -> agente do canal (LLM, cache work/rede_meta/<id>__<slug>__<estrategia>.json)
   revisor (palavras que derrubam anuncio, 'o criador', regras do dono) -> 1 correcao; se insistir, nao sobe
   troca do @ se o video mudou de canal (work/rede_marca/*.mp4, herda a aprovacao)
   politica.postar_youtube(... private + publishAt, categoria, idioma pt-BR, sintetico p/ historias)
   registro: hipercool-materiais/_postados/react/publicados.json (estrategia, horario, comentario pendente)
   arquiva: react -> _postados/react/<slug>/ ; historia -> _postados/historias/<genero>/<id>/
comentario do canal (tarefa ManhwaReact-Comentarios 30/30 min): posta a pergunta quando o video abre (credencial principal)
painel (tarefa PainelCanais 3/3 h): coleta os 19 canais, mede cada video 40-60 h apos abrir -> nota por braco em
   postador-de-videos/_analise/rede_aprendizado.json + historico (memoria do canal p/ o agente) + rede_sem_video.json
```

Estrategias (mr/rede.py::ESTRATEGIAS): titulo = pergunta | choque | curiosidade | opiniao | nome_obra; gancho = pergunta_direta |
contexto | spoiler_parcial; comentario = opiniao | a_ou_b | previsao; horario = os 3 do canal. Cada braco e testado 2x no canal;
depois vale o melhor (media do canal puxada pela media da rede, K=2), com 25% de exploracao (campo `explorar` no mapa).
nota = views_48h / mediana do canal x (1 + min(0,5; (likes + 3 x comentarios) / views)).

---

## 6. Tarefas agendadas (Windows, schtasks)

| Tarefa | Quando | O que roda |
|---|---|---|
| PostadorDeVideos | 06:40 | `postador-de-videos\bin\postar_tudo_auto.bat` (etapa 2b agora = `manhwareact.py rede`; VO3/recaps/TikTok seguem como antes, mas nao acham canal livre: todos os vivos estao reservados a rede) |
| ManhwaReact-Rede | de hora em hora, min 17 | `manhwa-react\scripts\rede_hora_em_hora.bat` (log `logs\rede_AAAAMMDD.log`) |
| ManhwaReact-Comentarios | 30/30 min | `scripts\rede_comentarios.bat` (log `logs\rede_comentarios.log`) |
| ManhwaReact-Lote | 02:00 | `scripts\lote_noturno.bat` (batch --max 20, log `logs\lote_noturno.log`) |
| PainelCanais | 3/3 h | `postador-de-videos\bin\painel_canais.bat` |
| AgendadorVO3 | 05:00 | antigo; nao acha canal livre (ok) |
| MegaEngageMonitor | - | **DESABILITADA - manter assim** |

---

## 7. Comandos uteis

```bat
cd /d D:\manhwa-react
set PYTHONUTF8=1
.venv\Scripts\python.exe manhwareact.py rede --simular --dias 2      (plano sem subir: canal, horario, estrategia, titulo)
.venv\Scripts\python.exe manhwareact.py rede                         (rodada real, respeita a janela de 3 h)
.venv\Scripts\python.exe manhwareact.py rede --aprovar [--tudo]      (aprovar react + historias)
.venv\Scripts\python.exe manhwareact.py rede --comentarios
.venv\Scripts\python.exe manhwareact.py batch --max 20               (processar gravacoes; 1 render por vez - memoria!)
.venv\Scripts\python.exe D:\postador-de-videos\bin\politica.py       (cota do dia, bloqueios, reservas)
.venv\Scripts\python.exe D:\postador-de-videos\bin\painel_canais.py --abrir
.venv\Scripts\python.exe scripts\ajustar_metadados_rede.py [--executar]   (reescreve metadados de publicos desde 01/10)
```
Ativar/pausar um canal: campo `status` (ativo | pausado | suspenso) em `rede_canais.json` - politica e rede leem na hora.
Mudar o angulo de um canal: `nicho` / `persona` / `tags_base` no mapa (as notas do diretor se recalculam sozinhas).

---

## 8. Arquivos criados/alterados nesta sessao (com backup)

postador-de-videos:
- `config\rede_canais.json` (NOVO, fonte unica) | `config\politica.json` (max_uploads_total_dia 12 -> 20)
- `config\canais_status.json` (esp em suspensos; bkp `.bkp_20261004`)
- `bin\politica.py` (aliases via rede, status pausado/suspenso do mapa, canais da rede reservados ao projeto manhwa-react,
  repasse de categoria/idioma/sintetico; bkp `_backup_2026-10-02\politica.py.antes_rede_20261004`)
- `bin\youtube_poster.py` (`--categoria --idioma --sintetico`; bkp `.bkp_20261004`)
- `bin\postar_tudo_auto.bat` (etapa 2b -> rede; bkp `.bkp_20261004`)
- `bin\painel_canais.py` + `.bat` (NOVO; bkp da 1a versao `.bkp_20261005`), `painel\index.html`, `painel\historico.jsonl`
- `_analise\rede_aprendizado.json`, `_analise\rede_sem_video.json` (gerados)

manhwa-react:
- `mr\rede.py` (NOVO; bkp da versao sem estrategias `mr\rede.py.bkp_20261005`), `mr\common.py` (junta os canais do mapa no cfg),
  `mr\editorial.py` (fila por canal + regra de nicho), `mr\memes.py` (avif -> png), `mr\publish.py` (comentario pela credencial
  principal), `manhwareact.py` (comando `rede`; bkp `.bkp_20261004`)
- scripts: `arquivar_distribuidos_2026-10-04.py`, `limpeza_rede_2026-10-04.py`, `ajustar_metadados_rede.py`,
  `rede_hora_em_hora.bat`, `rede_comentarios.bat`, `lote_noturno.bat`, `BOTAO_REDE_APROVAR.bat`
- `distribuir_videos.py.DESATIVADO` | `HANDOFF_REDE.md` (este) | `REDE_ESTADO_E_PENDENCIAS.md` | `historico_conversas\2026-10-04_05_rede\`

hipercool-materiais: `_postados\react\publicados.json` (bkp `.bkp_20261004`), `_postados\react\reabertos.json`, `_postados\historias\`.

No YouTube (fora do disco): 147 videos privados; 21 videos com metadados novos; descricao/palavras-chave/pais BR/idioma pt nos
12 canais originais (os 7 internacionais ainda NAO tiveram o perfil atualizado - pendencia).
Area de trabalho: atalho "PAINEL DOS CANAIS.bat".

---

## 9. Decisao firme: SEM gerador de likes/comentarios

`D:\projetos-navegador` (MEGA ENGAGE): Chrome headless com varias contas Google e fingerprint variado, curtindo/comentando/
inscrevendo nos proprios videos. E engajamento falso pela politica do YouTube. Rodou em 06/08 com contas da propria rede
(inovaremanhwaverseviet, gameoftrones..., esp, ind, ita, french, hindi, russian...) e em 04/09 22 canais foram suspensos por
"spam, praticas enganosas"; o esp (que participou) apareceu suspenso em 04/10. O dono pediu para ligar; foi recusado com o motivo
e oferecido o caminho permitido (1o comentario do proprio canal na hora certa, horario por publico, pergunta no video e na
descricao, painel com os comentarios reais para responder). Nao reabrir isso.

---

## 10. Estado em 05/10 10h40

- Ultimas 24 h: 20 uploads (cota do dia cheia: 20/20). Agendados para 05/10 e 06/10. ita/ru/eng estao reservados para hoje
  a noite, mas vao bater na cota do dia e ficam para 06/10 (efeito da rodada antiga, feita antes da janela de 3 h).
- Fila: ~25 videos aprovados (react + historias); 0 esperando aprovacao (os 2 do lote das 02:00 foram aprovados pelo agente
  depois de conferir quadros).
- Comentarios: 22+ pendentes saindo conforme os videos abrem (funcionando; ex.: Dicas as 08:17).
- Gravacoes: todas as de 01-04/10 processadas (04/10: 16 feitas + 1 repetida). `1-COLOQUE-AQUI` ainda tem os arquivos
  (o batch nao reprocessa: memoria + state.json).
- Aprendizado: ainda sem medicoes (primeiras em ~07/10, 48 h depois de abrirem os videos que ja tem estrategia registrada).
- Sem parada geral (`config\PARADO.json` nao existe).

## 11. Pendencias (prioridade)

1. **Reiniciar o PC** (memoria virtual ja configurada como "gerenciada pelo sistema"; seguem 4 GB alocados ate reiniciar).
2. Falta conteudo para ForjaReact, CartuchoReact, inovare_thai (donghua), MundoQueNaoExiste e AssistIA (painel: "Falta video").
   O dono precisa gravar reacts desses temas. NAO reaproveitar `veo\pos_final` (videos ja postados nos canais suspensos).
3. Atualizar o perfil (descricao/palavras-chave/pais/idioma) dos 7 Inovare internacionais para o angulo novo
   (channels.update brandingSettings - mesmo codigo usado em 05/10 para os 12; esta no historico da conversa).
4. Dono: ler o e-mail/Studio do esp (inovaremanhwaverseesp@gmail.com) para saber o motivo da suspensao. Se for "spam/contas
   associadas", reconsiderar os 7 internacionais (mesma rede antiga de contas e mesmo projeto OAuth 43266821547).
5. Dono: verificar cada canal por telefone (youtube.com/verify) - a thumbnail personalizada da 403 sem isso.
6. Dono: ativar a YouTube Analytics API no projeto 1006898207642 (o painel ganharia retencao/inscritos por video).
7. Dono: trocar o handle do Fio da Meada (@codigointeligente-n7j) e depois o campo `handle` no mapa.
8. Depois de ~1 semana de dados: revisar `_analise\rede_aprendizado.json` e cortar bracos ruins (campo `estrategias` por canal no mapa).
9. Opcional: Test & Compare de titulo/thumbnail existe so no Studio (nao ha API).

## 12. Armadilhas

- Python: sempre `D:\manhwa-react\.venv\Scripts\python.exe` com `PYTHONUTF8=1`. Heredoc no Git Bash com barra invertida ou
  aspas dentro de codigo Python quebra - use a ferramenta Edit/Write.
- A cota diaria da politica conta pela HORA DO UPLOAD (`ts` do ledger), nao pela publicacao: subir hoje o video de amanha gasta
  a cota de hoje. Por isso existe a janela de 3 h.
- `--sem-janela` gera rajada de uploads (padrao de robo que ajudou a derrubar a rede antiga). Evitar.
- Render: 1 por vez (memoria). O lote morre com "OpenBLAS Memory allocation" quando falta memoria.
- `publicados.json` e escrito por varias rotinas: so mexer com a trava (`work\rede.lock`) livre.
- Mudar o `nicho` de um canal invalida o cache de notas (1 chamada LLM para a fila toda) - normal.
- Proxy LLM: o opus costuma dar 429/503 e cair para o sonnet (ok, so mais lento).
- `CANAIS_E_DISTRIBUICAO.md` (agente anterior) esta desatualizado - nao seguir.
- Disco D: cheio derruba o lote no meio ("No space left on device"). Em 12/10 o culpado foi `D:\hipercool-videos.rar` (23,7 GB,
  e a UNICA copia de `hipercool-videos\workspace` - nao apagar sem o dono). Cache de Chrome dos perfis fechados pode ser apagado.

## 13. Atualizacao 12/10 - botoes LIGAR/DESLIGAR e pasta no desktop

Pedido do dono: "nas horas agendadas ele abre o navegador do nada e posta; tem que ter um botao liga e outro desliga pra parar
as postagens automaticas agendadas, e quando for ligado fazer as pendentes e depois voltar a agenda". E agrupar os botoes
do projeto numa pasta so, com nomes claros.

- **Pasta "ManhwaReact e Rede de Canais"** na area de trabalho, botoes numerados (1 colocar gravacoes, 2 processar, 3 aprovar,
  4 prontos, 5 LIGAR, 6 DESLIGAR, 7 painel, 8 cortar camera, 9 pasta do projeto) + "0 - O QUE CADA BOTAO FAZ.txt"
  (`scripts/LEIA_BOTOES.txt`). Recriar: `scripts/criar_atalhos.ps1` (tambem tira os atalhos soltos antigos).
- **DESLIGAR** (`rede --desligar`, `scripts/BOTAO_POSTAGEM_DESLIGAR.bat`): cria `D:/postador-de-videos/config/POSTAGEM_DESLIGADA.json`.
  Com ele: `rede` sai sem subir (loga 1 linha por hora), `rede --comentarios` sai calado, `postar_tudo_auto.bat` (06:40) e
  `agendar_vo3_auto.bat` saem no comeco. No meio de uma rodada, para antes do proximo upload. `--simular` continua funcionando.
- **LIGAR** (`rede --ligar`, `scripts/BOTAO_POSTAGEM_LIGAR.bat`): apaga o arquivo e roda a rede com `recuperar=True, ja=True`
  (pedido do dono: "como esta pendente pode postar 1 por canal logo"): TODO canal com vaga hoje e video aprovado publica agora
  (a partir de agora + 30 min, 1 canal a cada 20 min, upload nesta rodada, sem esperar o horario do canal nem a janela). A
  pendente grava `horario: None` (nao entra no aprendizado de horario). Dias inteiros perdidos nao sao recuperados: os videos
  seguem na fila e saem nos proximos dias (1 por canal por dia, no horario do canal, como sempre).
- `youtube_web_poster.py`: com `connect_over_cdp` o Playwright TRANSFERIA o arquivo pela conexao (>50 MB recusa, 30-50 MB
  estoura 30 s) - CenaReact/eng/ita falharam. Agora `_escolher_arquivo` usa CDP `DOM.setFileInputFiles` (so o caminho).
  Testado com 60 MB e em producao (CenaReact 33 MB e ita 53 MB subiram 16:51/16:54).
- **Canais pausados em 12/10 (campo `pausa` no mapa)**: inovare_french (advertencia por DIREITOS AUTORAIS de 27/09; o Studio
  trava o upload nessa tela) e inovare_eng ("Muitos avisos": advertencias de DIRETRIZES DA COMUNIDADE, envio bloqueado).
  O dono precisa ver no Studio. 3 advertencias = canal e canais associados removidos.
- 7 cortes de `2026_10_08_12_06_26` (AssistIA, robo de trading do dono) NAO aprovados: titulos com "bot", "lucro garantido",
  "57% ao ano" e a tarja "BOT DE TRADING COM IA" ferem as regras do canal - decisao do dono.
- O botao antigo "APROVAR E POSTAR" chamava `manhwareact.py publicar` (sobe direto no canal original, sem a rede e sem a trava):
  `BOTAO_APROVAR_E_POSTAR.bat` agora faz `rede --aprovar` + `rede --simular --dias 3`.
- Corrigido `postador-de-videos/bin/painel_canais.bat` e o "PAINEL DOS CANAIS.bat" do desktop: o `\b` do caminho tinha virado
  o caractere 0x08 (heredoc), a tarefa PainelCanais falhava (resultado 2) e o aprendizado nao media nada.
- `mr/probe.py`: o corte da faixa preta embaixo/em cima do conteudo aceitava ate 30% da area; clipe deitado no meio da tela do
  celular deixa ~34% preto -> sobrava faixa preta no Short. Agora 45% (faixa preta estatica no video inteiro = borda).
- Lote de `D:\downloads\7-20261012T124003Z-1-001\7` (30 gravacoes de 04-08/10): 6 ja feitas, a de 83 min (06/10 10-47-07) e a
  mesma do parte1+parte2 (registrada na memoria como feita), 23 processadas. 15 aprovadas pelo agente (folhas de quadros:
  `testes/folhas_quadros.py`); 5 seguradas por faixa preta para re-render com o probe novo.
