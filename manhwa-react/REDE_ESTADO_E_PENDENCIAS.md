# Rede de canais - estado e pendencias (2026-10-04/05)

Leia junto com CANAIS_E_DISTRIBUICAO.md (parte dele esta DESATUALIZADA - ver secao 4).

## 1. O que foi feito
- **Contencao**: os 13 videos do `distribuir_videos.py` foram arquivados em `hipercool-materiais/_postados/react/` e registrados
  em `publicados.json` (nao repostam). `distribuir_videos.py` -> `.DESATIVADO` (pulava a politica e postava fora do nicho).
- **Inovare Manhwa esp esta SUSPENSO** (a API disse; nao era API desabilitada). Marcado em canais_status.json.
- **Mapa unico da rede**: `D:/postador-de-videos/config/rede_canais.json` (12 canais ativos com nicho, persona, regras,
  categoria, horarios; Inovare internacionais = `pausado` ate o dono checar o esp; `a_verificar`: n7h e h4b).
- **ManhwaReact (i5r) e ManhwaReact-ia sao o MESMO canal** (UC5Za1hPxak0iufFcJ4UsK9w): politica.py agora soma aliases.
- politica.py: aliases, status pausado/suspenso do mapa, canais da rede reservados (VO3/recaps nao postam neles).
- youtube_poster.py: `--categoria`, `--idioma pt-BR`, `--sintetico` (marca conteudo de IA).
- manhwa-react: `config.json` puxa os canais do mapa (handles reais: @manhwareact-ia, @cenareact-f3j...); editorial
  distribui entre os 12 canais e considera a fila de cada um; bug do meme `.avif` corrigido.
- **`mr/rede.py` + `manhwareact.py rede`**: inventario (react + historias-em-frames) -> notas do "diretor da rede" (LLM)
  -> 1 video/canal/dia, cada video em UM canal -> troca do @ no canto se mudou de canal -> agente do canal reescreve
  titulo/descricao/tags/comentario -> horario que aprende (explora 3x cada, depois o melhor) -> upload agendado via politica.
- Ciclo 06:40 (`postar_tudo_auto.bat`, etapa 2b) agora chama `manhwareact.py rede` (antes `publicar`).
- Tarefas novas: `ManhwaReact-Comentarios` (30 em 30 min, 1o comentario do canal quando o video abre) e
  `ManhwaReact-Lote` (02:00, processa 1-COLOQUE-AQUI).
- Limpeza (`scripts/limpeza_rede_2026-10-04.py`, idempotente, log em `logs/limpeza_2026-10-04.json`): priva ~144 videos
  (canal errado, duplicados, lote generico de IA de 08/2026; nos canais Animescomia/inovaremanhwabr so copias e spam ET)
  e devolve 11 Shorts a fila do canal certo (`reabertos.json`). Mantidos com metadado a ajustar: Oshi no Ko (ManhwaReact),
  anime trader (AssistIA), Vegeta (HistoriasEmFrames), cama-quarto (MundoQueNaoExiste).

## 2. Em andamento / conferir
- Limpeza relancada em 05/10 (pode parar por cota da API: rode de novo, continua de onde parou).
- Lote das gravacoes de 04/10: relancado 05/10 00:24 e MORREU por falta de memoria (OpenBLAS; pagefile fixo 4 GB, ver HANDOFF). A tarefa ManhwaReact-Lote (02:00) tenta de novo; aumentar o pagefile resolve.
- **`manhwareact.py rede --simular` NUNCA foi rodado** (interrompido): rodar antes de confiar no 06:40. Erros esperaveis
  ficam no log `D:/postador-de-videos/logs/manhwa_react_AAAAMMDD.log`.

## 3. Pendencias (em ordem)
1. Rodar `python manhwareact.py rede --simular` e corrigir o que quebrar.
2. **Aprovacao humana continua ligada**: so sobe o aprovado. Botao `scripts/BOTAO_REDE_APROVAR.bat` (react + 10 historias).
   Para desligar: `exigir_aprovacao_humana: false` em `postador-de-videos/config/politica.json` (decisao do dono).
3. Limite total 12/dia em politica.json = exatamente os 12 canais; subir se entrar canal novo.
4. Ajustar metadados dos 4 videos mantidos + videos publicos recentes: `rede.adaptar()` + `rede.editar_meta()` (falta script).
5. **Painel HTML** (inscritos, views, likes, comentarios por canal/video + comentarios para responder + gravar
   `_analise/rede_horarios.json` com views de 48 h por horario, que o agendador usa para aprender). NAO FEITO.
6. Habilitar YouTube Analytics API no projeto Google 1006898207642 (link no erro 403) para o painel ter retencao/dia.
7. Conferir n7h/h4b (`a_verificar`) quando a cota renovar: provavelmente o mesmo canal do HistoriasEmFrames/CartuchoReact.
8. Dono: verificar cada canal por telefone (youtube.com/verify) - sem isso a thumbnail personalizada da 403.
9. Dono: checar no Studio por que o esp foi suspenso antes de reativar os Inovare internacionais (status no mapa).
10. Atualizar descricao/palavras-chave/pais dos canais (channels.update) - varios estao sem descricao e com nome minusculo.
11. Fio da Meada ainda tem handle @codigointeligente-n7j (trocar no Studio e depois no mapa).

## 4. Desatualizado em CANAIS_E_DISTRIBUICAO.md
- "esp/eng 403 = API desabilitada": errado (esp suspenso). Lista de "15 livres" e `distribuir_videos.py`: substituidos pela rede.

## 5. Decisao: SEM gerador de likes/comentarios
`D:/projetos-navegador` (MEGA ENGAGE, multi-conta headless) e engajamento falso pela regra do YouTube; rodou em 06/08 com
contas da rede e 22 canais cairam em 04/09. Nao ligar. Tarefa MegaEngageMonitor fica desabilitada.

## 6. Atualizacao 05/10 (madrugada) - FEITO
- Limpeza concluida: 147 privados (inclui 4 copias do Rei Demonio no inovaremanhwabr), 11 devolvidos a fila, 0 erros.
- `rede --simular` testado: funciona (10 videos planejados para 05-06/10, troca de @ ok). Sem video para forja/historias/financas
  ate o dono aprovar as 10 historias e as gravacoes novas (`scripts/BOTAO_REDE_APROVAR.bat`).
- Metadados de 21 videos publicos desde 01/10 reescritos pelo agente do canal (`scripts/ajustar_metadados_rede.py`, log
  `logs/metadados_ajustados.json`). Videos PROPRIOS do AssistIA/Dicas ficam de fora (o agente distorceu um: nunca reescrever).
- Painel: `D:/postador-de-videos/bin/painel_canais.py` -> `painel/index.html`; tarefa PainelCanais (3 em 3 h); atalho
  "PAINEL DOS CANAIS" na area de trabalho; grava `_analise/rede_horarios.json` (aprendizado de horario).
- Perfil dos 12 canais: descricao (onde faltava), palavras-chave, pais BR, idioma pt.

## 7. Ainda pendente
- Lote das gravacoes: falha por MEMORIA (pagefile fixo 4 GB). Dono: Sistema > Avancado > Desempenho > Memoria virtual >
  "gerenciado pelo sistema" e reiniciar. Tarefa ManhwaReact-Lote (02:00) tenta todo dia.
- Aprovar os 27 pendentes. Itens 6-9 e 11 da secao 3 sao do dono (Analytics API, verificar telefone, esp, handle Fio da Meada).
- Conferir o log do 1o ciclo real: `D:/postador-de-videos/logs/manhwa_react_20261005.log`.

## 8. Atualizacao 05/10 01h - 19 canais + estrategias por canal
- Os 7 Inovare internacionais voltaram (pedido do dono) para react NACIONAL (pt-BR), 1/dia, cada um com um ANGULO proprio
  (rede_canais.json): french=romance/fofo, hindi=luta/hype, ind=isekai/ranking de poder, eng=vilao/plot twist,
  ita=comedia/memes, ru=sombrio/seinen, thai=donghua/cultivo. politica.json: max_uploads_total_dia 20.
- n7h = HistoriasEmFrames e h4b = CartuchoReact (aliases, confirmado pelo dono). As 49 credenciais estao todas explicadas.
- **Estrategias por canal** (mr/rede.py): cada upload escolhe 1 braco por dimensao - titulo (pergunta/choque/curiosidade/
  opiniao/nome_obra), gancho da descricao (pergunta_direta/contexto/spoiler_parcial), 1o comentario (opiniao/a_ou_b/previsao)
  e horario. Exploracao: cada braco 2x no canal, depois o melhor (media do canal puxada pela media da rede) com 25% de teste.
- **Aprendizado**: o painel mede cada video da rede 40-60 h depois de abrir: nota = views/mediana do canal x (1+engajamento)
  -> `_analise/rede_aprendizado.json` (por braco) + historico; o agente do canal recebe a MEMORIA (titulos que mais/menos
  renderam). Painel mostra "Estrategias em teste" e "Falta video bom para".
- **Revisor**: barra titulo com palavra que derruba anuncio, 'o criador', e (canais com regras: AssistIA/Dicas) robo/bot/
  garantido/fique rico/preve o mercado; pede correcao 1x; se insistir, o video NAO sobe naquele canal.
- **Fome**: canal com pouco video nos ultimos 3 dias ganha bonus na distribuicao (evita french/hindi com 2 e eng/ita com 0).
- **Sem rajada**: tarefa `ManhwaReact-Rede` de hora em hora (min 17) so sobe o que publica nas proximas 3 h
  (`--janela`; `--sem-janela` sobe tudo agora - evite). Trava `work/rede.lock` impede 2 rodadas ao mesmo tempo.
- Comentarios agora saem pela credencial principal do canal (a alias i5r estava sem cota).
- 05/10: a rodada antiga (antes da janela) ja subiu 20 videos (05 e 06/10) e encheu a cota de hoje: eng/ita/ru/thai/forja
  comecam 06/10.

## 9. Limites conhecidos
- Falta conteudo de forja, games, donghua, financas e "impossivel" (ver painel). Nao reaproveitar os 730 videos de
  veo/pos_final: muitos ja foram postados nos canais suspensos (repostar = reupload de canal encerrado).
- Analytics API desligada no projeto -> o aprendizado usa views/likes/comentarios publicos (nao retencao).

## 10. Retomada 05/10 10h40 (cron das 07:28 + pedido de handoff)
- Itens da retomada ja estavam feitos nesta sessao: limpeza (147 privados, 11 reabertos), `rede --simular` ok, metadados (21),
  painel + tarefa, perfil dos 12 canais. Lote das 02:00 funcionou: todas as gravacoes de 04/10 processadas.
- Tarefas conferidas rodando: ManhwaReact-Rede (de hora em hora), Comentarios, PainelCanais, PostadorDeVideos 06:40. Sem PARADO.
- 2 videos novos (InventoReact: 13_27_42 moto-taxi, 08_23_52 golpe da mala) conferidos por quadros e aprovados pelo agente
  (o dono delegou a aprovacao em 05/10).
- PC ainda NAO reiniciou (boot 27/09): memoria virtual nova so vale depois do reinicio.
- **HANDOFF completo para outro agente: `HANDOFF_REDE.md`** + conversa salva em `historico_conversas/2026-10-04_05_rede/`.
