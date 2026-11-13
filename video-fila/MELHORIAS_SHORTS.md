# Melhorias nos Shorts do Cortes (dono 21/10 ~09:10)

> OUTRO AGENTE VAI CONTINUAR? Leia primeiro a seção "PASSAGEM DE BASTÃO (22/10)" no fim deste arquivo: estado atual,
> o que foi feito e testado, o que está pela metade e a lista do que falta, em ordem.

Pedido: "atualize o código no outro PC pra rodar clone de voz também; os últimos segundos de cada vídeo ficam com a
imagem parada enquanto o áudio rola (não em todos); está re-narrando mas muito dessincronizado da imagem (o narrador
fala de um quadro específico que está na tela); às vezes o vídeo parece cortado abruptamente, não usa o mesmo tamanho
do original, e termina sem gancho de retorno (o final encaixa no começo: 'x coisa acontece com o animal... e é por isso
que' liga ao começo). No geral aceitável, mas melhorar nos próximos."

Regra: não quebrar a produção (testar num Short de verdade antes de soltar; backup de cada arquivo).

## Frentes
- [~] 1 Voz clonada no PC2 — BLOQUEADO por disco (ver abaixo); Shorts só no PC1 (C:\recapd-e-animes; nada nas pastas do hipercool)
- [x] 2 Imagem parada no fim — conferido 11:59 (freezedetect: nenhum congelamento) (áudio maior que o vídeo)
- [x] 3 Narração sincronizada — conferido 11:45 (cortes pelos tempos 0 8 15 22... 62 s) com o quadro que ela descreve
- [x] 4 Duração perto do original — 62 s de Short pra 69 s de original, cobrindo tudo / fim abrupto
- [x] 5 Gancho de retorno — no log de todo Short novo (no lugar do CTA) (fim emenda no começo, loop)

## Achados
- 1 (BLOQUEADO por disco): o clone completo no PC2 precisa ~13 GB (venv_vozes 1,4 + kokoro 0,65 + 71 narradores
  .pth 4,0 + .index 6,4); o C: do PC2 tem 11,9 GB e precisa de 3-5 GB pras línguas do hipercool. C:\hipercool-materiais
  lá é do hipercool (não usar). Hoje: Short de parceiro só no PC1 (todos com clone); PC2 = anime longo + hipercool.
  Pra liberar: dono libera espaço no PC2 (Downloads dele 4,8 GB) ou HD externo; aí instalar em C:\recapd-e-animes\vozes.
- 2/3/4 FEITO no código (backups *.bak_20261021_sincronia): causa = anime_segments cortava em sequência a partir do 0
  (cut_at = soma das falas): frase fora do quadro, Short só com o começo do original, última frase passando do fim
  (imagem parada). Agora (só vertical): legenda guarda os tempos (anime_fetch legenda_tempos.json), roteiro curto marca
  [Ns] de cada frase (anime_script.rewrite_curto_com_tempo -> roteiro_tempos.json), cada frase começa no segundo que
  narra; sem tempos as frases se espalham pelo original inteiro; corte nunca passa do fim. Longo (deitado) igual.
- 5 FEITO no código: anime_script.fechar_loop reescreve a última frase emendando na primeira (no lugar do CTA; CTA só
  se o gancho falhar). PARCEIRO_LOOP=0 desliga.
- FALTA: conferir num Short real (log: "roteiro com tempo", "gancho de retorno", "cortes pelos tempos"; fim sem imagem
  parada com freezedetect).

## Tarefas novas (dono 21/10 ~11:20) — cron 12:01 "continue"
- [~] 6 v2 aprovadas — os 10 da pasta já eram v2; 57 vozes sem perfil_v2: gerando ESTIMADO (D:	mp\perfil_personagens.py) (amostras_voz\clone2\comparar_v1_v2): conferir que TODOS os narradores rodam no estilo v2
- [x] 7 instalar as vozes — Cintilante (She-Ra) e Hanako-San (Yo-Kai Watch) no rodízio (73), com linguagem_v2 de amostras_voz\amostras_audio\novas3\aprovados (2 vozes)
- [x] 8 narrador pelo tipo de vídeo — config
arradores_nichos.json (73 vozes, nota 0-3) + anime_voz_clonada.proxima(nicho) + _historico.jsonl; FALTA ver o 1º Short (não só por vez): encaixe voz x nicho, balanceado pra todos terem chance, gravar
      os dados (narrador, nicho, views) pra decidir os melhores. Caso: "o cara do LoL" (akali) caiu em curiosidades.
- [x] (já feito 11:10) bug do roteiro com tempo: `import json` local no fazer_short (trocado por pass)

## Tarefas do dono 21/10 ~13:15 (com prints do painel) — ordem de execução
- [x] A Backup no Drive — FEITO 14:03: catalogo._etapas quebrava com 1 arquivo fora do formato das etapas no Drive (anime/1_youtube_pendente/.../video.mp4); agora ignora e avisa; backup rodou ok (backup catalogo.py.bak_20261021_partes)
- [ ] B Buzz Lightyear: o trecho original só fala "ao infinito" — falta "e além"
- [ ] C Capitão Nascimento = narrador de AÇÃO e AGRESSIVO: pesquisar, frases feitas dele (bordões), refazer jeito + encaixe
- [x] D Esporte Noturno sem foto de perfil e banner — resolvido em V (imagens geradas para os 3 canais Noturno)
- [x] E Painel IA: 1 clique abre JANELA com a conversa da resolução; tudo documentado do que fez (pra outra IA continuar);
      botão "corrigir todos"; base de conhecimento dos problemas resolvidos (o vigia aprende; RAG leve, graph RAG se precisar)
      FEITO 22/10 08:20 e testado no navegador (computador e celular): detalhes em D:\video-fila\MELHORIAS_PAINEL.md,
      seção "Frente E". Peças: janela dlg-ia, consertos_ia\<id>.md + INDICE.md, POST /api/ia_corrigir_todos,
      base_consertos.py (prompt da IA do painel e do vigia geral).
- [x] F Liga/desliga mostra tudo ligado mas só 2 projetos estão ligados de verdade: api_producao agora lê o estado do
      controlador (disparos_hoje, necessidades) e expõe "ativo" (tem necessidade ou despacho hoje) e "disparos_hoje"
      por projeto; no painel cada card mostra badge "N hoje" (verde) ou "sem necessidade" (cinza)
- [x] G Filtro de dias: botão "Ontem" adicionado (calcula de/até com a data de ontem); links dos avisos clicáveis
      (linkify converte URLs no texto escapado em <a> tags)
- [ ] H Saúde: TUDO que pode dar problema ou acabar — limites de chaves, proxies, IAs, cotas, créditos, Drive, etc.
- [ ] I Voz clonada no painel: mais filtros, mais organizado, links clicáveis (histórico com nicho/canal/views)
- [x] J PC3 (desktop) no painel/controlador: maquinas.py já media, agora controlador.py grava medidas.desktop no estado,
      painel_controlador.py expõe em /api/medir e /api/geral, painel_web/index.html mostra 3 cards (PC1/PC2/DESKTOP),
      saúde inclui "Desktop / PC3 (ssh)". Regra OBS+código mantida. FALTA: botão no desktop pra desligar o uso dele.
- [ ] K Mais 2 PCs fracos como TELA: ao gerar o vídeo, abre lá sozinho; deixar tudo pronto pra adicionar
- [ ] L Responder no fim: 2 tablets Android servem pra quê?
- [ ] M (cron) conferir o Short de animais com narrador por nicho; marcar 6/8 acima
- [ ] N Chapolin narrou SEM nenhuma frase típica (dono 14:05): conferir por que o jeito do personagem não entrou no roteiro
      + baixar os trechos originais dele (há muitos no YouTube) — e o mesmo pros outros personagens

## Pedidos do dono 21/10 ~15h (depois do reinício da sessão)
- [x] B Buzz: trecho refeito "ao infinito e além" (2,3 s; corte pelas palavras tira a pausa dramática)
- [x] N Chapolin: roteiro era escrito ANTES de escolher o narrador (nenhum Short saiu no jeito do personagem desde 20/10);
      agora a voz é escolhida antes e o VOZ_CLONADA vale durante o roteiro; trecho original "Não contavam com minha astúcia"
- [~] O 4 canais sem post hoje: a maioria dos 27 "sem post" tem agendamentos para hoje à tarde/noite (publish_at
      futuro). Realmente sem nada: fiodameada, forjareact, inovaremanhwaverse (controlador produzindo pra eles;
      34 disparos PC1 + 20 PC2 hoje). Inovare-eng/french com advertência, correto parados.
- [x] P Narração sempre "como manhwa" em curiosidades: _system() agora muda conforme NICHO_CLONE/PARCEIRO_TIPO; nichos sem protagonista não usam "prota"/"garoto"; _jeito_do_nicho() adapta o repertório; prompt v4 invalida cache antigo
- [x] Q Gancho de retorno só repete a frase inicial: prompt reformulado — agora pede PERGUNTA ou frase INCOMPLETA que a primeira frase responde (não copiar/repetir)
- [x] R Lula leu "GTA V" como letra: _seguro() no anime_tts converte II-XX em número (regex com lookbehind, não pega V sozinho no início)
- [x] S Plankton não ficou bom: todos os scores zerados em narradores_nichos.json (nunca será sorteado)
- [x] C Capitão Nascimento = narrador de AÇÃO e AGRESSIVO: linguagem_v2.json reforçada (tom agressivo/intimidador,
      resumo "líder implacável", bordões sem duplicatas + "Tropa de Elite osso duro de roer"), notas em
      narradores_nichos.json subidas (anime/manhwa/filme/esportes → 3), 2 trechos reais baixados
      (pede_pra_sair 1.1s nota 1.0, missão_dada 2.3s nota 1.0) em trechos_icones/capitao_nascimento/.
      Bug "narrou sem frase típica" já corrigido em N (voz agora é escolhida ANTES do roteiro).
- [ ] T Trechos originais dos outros personagens (baixar_trechos2.py; respeitar a pausa do yt-dlp da outra sessão)
- [x] Jubetim narração muito lenta: perfil_v2.json ajustado (rate -9→-3, velocidade 0.85→0.92, curva_rate 0.91→1.0)

## Pedidos do dono 21/10 ~19h-20h
- [x] W Seu Madruga com 2 bordões no começo (trecho real "A vingança nunca é plena" + abertura escrita): anime_script v5 —
      com trecho real a 1ª frase vai direto ao assunto, no máximo 1 bordão escrito depois; rótulo do trecho "plana"->"plena"
- [x] X Short "curto, sem contexto": prova nos roteiros (Marcelo/Ivete: 5 frases, 1ª = só apresentação, última trocada
      por cópia da 1ª -> 3 de conteúdo, o Marcelo nem aparecia; Nintendo/Seu Madruga igual). Consertado: gancho mantém o
      desfecho + trava no código (_gancho_ruim: recusa cópia da 1ª/abertura/bordão e gancho que perde o fato; 2 tentativas);
      1ª frase = fato com o chamado do narrador (_tirar_abertura_vazia tira abertura copiada); nichos sem protagonista com o
      nome certo (esportes/jogos/pesca; antes "esporte"/"game" e o Short de esporte saía com texto de "conteúdo animado");
      sem "apelido de protagonista" em vídeo informativo. Testado com LLM nos 2 roteiros + 2 legendas reais. Backup
      anime_script.py.bak_20261021_gancho2. FALTA: conferir o 1º Short de produção com o código novo (log "[script]").
- [x] U Veo 3 nos canais ManhwaReact/InventoReact: é configuração explícita do dono (16/10) em D:\manhwa-react\mr\rede.py
      linha 43: canais_veo_limpo = ["inventoreact", "manhwareact"]; 11 vídeos entregues (6 Invento, 5 Manhwa) 19-21/10
- [x] V Game/Esporte/Bicho Noturno sem foto/banner: 6 imagens geradas via Cloudflare flux-2-klein-4b (proxy Webshare)
      em D:\tmp\imagens_canais\ (3 perfis 9:16 + 3 banners 16:9). APLICAR MANUALMENTE pelo YouTube Studio (não há
      automação para upload de perfil/banner). Contas OK: os 60 tokens Cloudflare funcionam via proxy Webshare
      (o erro 401 da sessão anterior era do ip_fixo com padrão não reconhecido)
- [x] Z Vídeos duplicados em videos_voz_clonada ("por que não abre só o vídeo feito em vez de copiar"): eram 55 cópias
      (1,2 GB, 34 só de 21/10) + o vigia abria 2 janelas (cópia e fila). Agora anime_voz_clonada.registrar só grava o .txt
      (campo "video" = o da fila), vigia só avisa (o laço dos Shorts novos abre o da fila), painel conta pelo _rodizio.json
      e o "ver" toca o da fila (testado com print: semcopia_desk_voz_ver.png). _rodizio.json migrado (52 entradas;
      backup _rodizio.antes_sem_copia_20261021.json). Backups *.bak_20261021_semcopia. FALTA: dono confirmar apagar as
      55 cópias antigas (todas com original na fila); se aparecer entrada com "copia" (Short que já estava rodando com o
      código velho), rodar a migração de novo.
- [x] Y Janelas piscando: CREATE_NO_WINDOW adicionado em TODOS os subprocess.run de:
      - D:\manhwa-react\scripts\backup_drive.py (rclone; backup .bak_20261021_janela)
      - D:\postador-de-videos\bin\etapas.py (rclone; backup .bak_20261021_janela)
      - D:\postador-de-videos\bin\limpar_veo.py (ffmpeg+ffprobe+rclone, ~15 chamadas; backup .bak_20261021_janela)
      Padrão: _SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0) + creationflags=_SEM_JANELA
      py_compile OK nos 3 arquivos. Próximo: verificar se há outros arquivos com subprocess.run sem a flag

## Revisão 00:10 (22/10, cron do dono) — Opus 5.5 conferindo o trabalho do modelo anterior (Opus 4.6)
Feita direto com Grep/Read/Bash (memória: no Opus nada de subagente/Workflow).

Produção às 00:16: SAUDÁVEL. Controlador a cada 10 min (última 00:12), PC1 com Cortes (pid 14752), PC2 com anime longo;
4 disparos desde 00:00 (123 em 21/10). Ledger real (D:\postador-de-videos\logs\uploads_ledger.jsonl): 73 registrados
em 21/10; 35 vídeos publicam em 22/10 e 29 em 23/10. Vigia ok (avisos que se repetem: legenda do YouTube 429, que passa
sozinho; capa IA recusada pelo filtro do Cloudflare, "reserva também não gerou"). Tudo compila; JSONs válidos.

Conferido e OK:
- Y: backup_drive rodou 22:40 e 23:40 depois da edição (22:00) sem erro; limpar_veo não roda desde 19/10 (só compila);
  relatório do agente confere (entradas pythonw com _SEM_JANELA ou sem_janela.py; filhos de .bat oculto herdam o console
  invisível). D:\tmp\relatorio_y_sem_janela.txt
- C Capitão: JSON válido; trechos 1,06 s e 2,30 s com áudio de verdade (média -22 dB).
- U: confere (rede.py canais_veo_limpo = inventoreact, manhwareact).
- v5 do roteiro: em 21/10, 26 "roteiro com tempo", 28 "gancho de retorno" e 24 "cortes pelos tempos" em 61 Shorts.
- 6: 73/73 vozes com linguagem_v2 e perfil_v2.
- M: narrador por nicho funciona em 8 nichos; "animais" ainda não teve Short depois do conserto N (o único foi 03:55 de
  21/10, antes). Conferir no próximo Bicho Noturno.

Defeitos achados no trabalho do modelo anterior:
1. H saúde: "Tarefas agendadas" esperava "StatusVideos" (não existe) = alarme falso pra sempre; "Cofre de cookies" lia o
   playwright_state.json do hipercool (morto há 86 dias) = alarme falso pra sempre; TikTok olhava a pasta antiga do
   hipercool (o login real é pelo cofre/postador); Telegram só procurava a palavra TOKEN no código. Item com ok=false
   vira "problema" no painel (_problemas), então isso sujava a lista. E o principal do pedido (limites, cotas, créditos)
   não era medido: só contava chaves. H NÃO estava pronto.
2. J desktop: o botão chamava atualizar(), que não existe (erro depois do clique); usava emoji; desligar só valia pro
   controlador (o /api/medir do painel, o ociosidade.py do hipercool e o vigia do Telegram continuavam usando o desktop);
   o "desktop" ia aparecer em Liga/desliga com uma chave de "postagem" sem sentido.
3. V imagens: as 6 são JPEG com nome .png; banners 1344x768 (o YouTube exige no mínimo 2048x1152 e recusaria); perfis
   768x1344 (não são quadrados).
4. A conta "uploads agendados hoje: 0" do começo da noite estava errada (caminho errado do ledger). O real está acima.
5. O servidor do painel (PainelVideos) ainda roda o código antigo: F e H só aparecem depois de reiniciar.
6. O (canais sem post): às 00:20, 10 canais do YouTube sem nada pra 22/10 nem pra 23/10: Assist-IA Investimentos,
   Bicho Noturno, Dicas financeiras da ia, Fio da Meada, ForjaReact, Inovare Manga ind, Inovaremanhwaverseviet,
   ManhwaReact, Mundo Que Nao Existe, inovare manhwa br. Mais 3 sem nada amanhã: @CodigoInteligente-n7j,
   DicasFinanceirasDaIA, Manhwa Noturno. Falta ver quem alimenta cada um.
7. T: 49 personagens sem trecho original + 16 vozes de parceiro sem bordão buscável
   (D:\tmp\relatorio_t_trechos_faltantes.txt). O yt-dlp está levando 429 agora: baixar devagar, 1 personagem por vez.

Ordem dos consertos: 1, 2, 3, reiniciar o painel + prints, 6, H completo (cotas), T, depois I/E/K/L/aprendizado/docs.

## PASSAGEM DE BASTÃO (22/10 ~00:55) — estado atual e o que falta, em ordem
Regras que valem pra tudo (memória do dono): nunca parar a produção; backup .bak_AAAAMMDD_motivo antes de editar;
py_compile + teste real; documentar aqui; no Opus nada de subagente/Workflow; yt-dlp sem rajada; PC2 é do hipercool
(nunca taskkill pythonw lá); agendamento sempre com publishAt; Google só pelo navegador.

### Feito nesta rodada (Opus 5.5, depois da revisão 00:10) e testado
- J desktop: a chave mora em D:\video-fila\maquinas.py (_desktop_desligado + começo de medir()): desktop desligado =
  medir("desktop") devolve ocupado sem ssh, pra controlador, painel, ociosidade.py do hipercool e vigia do Telegram.
  controlador.py voltou exatamente ao original. controle.py: projeto "desktop" (só etapa producao, nome "desktop (PC3)").
  Painel: interruptor "Usar este PC" no card do desktop (tela Geral) e card próprio em Liga/desliga (sem emoji, sem
  atualizar() inexistente). Testado: ramo desligado (0,00 s, sem ssh), controle.painel(), node --check do JS.
- Painel, cache depois do clique: _refletir_controle() em painel_controlador.py atualiza o cache de /api/geral e
  /api/producao na hora (antes a chave voltava pra posição antiga por até 30 s e o dono podia desfazer sem querer).
- Painel, Liga/desliga: badge por projeto = "rodando agora" (processo vivo: em_execucao), "N disparo(s) hoje",
  "esperando vaga" ou "nada rodando agora" (antes manhwa-react/postador apareciam "sem necessidade" mesmo rodando).
- Painel, agenda (frente O): 8 dos 10 "SEM POST HOJE" eram nome diferente entre catálogo e canais.json
  ("MundoQueNaoExiste", "ManhwaReact-ia", "YouTube inovaremanhwaverseind", "@CodigoInteligente-n7j"...). Agora compara
  nome/@handle/slug normalizados e a linha de reserva usa as datas reais do ledger (_canais devolve handle, publica_dia,
  no_ar_hoje). Testado direto (D:\tmp\teste_agenda.py): sobram só os 2 reais, Bicho Noturno e ForjaReact.
- Postador do YouTube (D:\postador-de-videos\bin\youtube_web_poster.py, backup .bak_20261022_hashtag): nova
  _fechar_sugestoes() no lugar do clique no título. Causa provada com os prints de logs\yt_web\*_falha_forjareact.png: em
  contas com "Hashtags sugeridas" a lista de hashtags abre por cima do título, o clique esperava 30 s e falhava DEPOIS do
  arquivo enviado; cada tentativa deixou um vídeo privado a mais (ForjaReact: 126 tentativas do mesmo vídeo de 18 a
  22/10), o que esgotou o limite diário da conta. Testado em navegador real com página que imita os 3 casos
  (D:\tmp\teste_hashtag\teste_fechar_sugestoes.py): sem lista igual a antes (0,1 s); lista que fecha com clique fora;
  lista que só fecha com Escape (o Escape não fecha o diálogo). FALTA ver o 1º envio real do ForjaReact (23/10, depois
  da pausa de limite) e do Dicas financeiras da ia: no log tem que aparecer AGENDADO, e "hashtag_por_cima" nos prints.

### Concluído depois da passagem (22/10 00:45-02:00) e testado
- V imagens: PRONTAS em D:\tmp\imagens_canais\final: {gamenoturno,esportenoturno,bichonoturno}_perfil_800x800.png e
  _banner_2560x1440.jpg (209-759 KB), mais _previa_celular_*.jpg (faixa central que aparece no celular; conferidas
  olhando). O banner do Game foi gerado de novo sem texto (novo\gamenoturno_banner_v2.jpg, controle no centro, combina
  com o perfil). O imagem_reserva central (hipercool-materiais\comum) não acha as chaves: usar a cópia de
  D:\hipercool-videos\bin. FALTA SÓ O DONO aplicar no Studio de cada canal.
- H saúde: bloco refeito em painel_controlador.py (backup .bak_20261022_saude). Itens novos, todos medida real: discos,
  Gemini livres agora (gemini_estado "ate"), proxies Webshare (2 sorteados abrindo google generate_204), contas do
  YouTube no limite diário (.limite_diario.json do parceiro_diario), capas por IA hoje (com x sem capa no log do dia),
  Google Drive (rclone about manhwa-drive:, 1x por hora) e tarefas agendadas (14 da produção/postagem: faltando,
  desabilitada ou sem rodar há 26 h). Saíram os alarmes falsos e os emojis. Teste real (67 s): só 1 problema, o real
  (novo_filmenoturno e novo_forjareact no limite diário). AINDA FALTA no H: cota do OmniRoute/Opus e Kiro, crédito do
  Flow/Veo (exit 6), contas TikTok banidas.
- Painel reiniciado 00:53 (Stop/Start da tarefa PainelVideos; processos 6636/23392). Prints em
  D:\video-fila\logs\prints_painel\rev22_*.png (computador e celular: Geral, Liga/desliga, Agenda, Saúde) e clique de
  verdade no interruptor do desktop: desligou, ficou desligado depois de a tela redesenhar, religou; controle.json
  terminou com desktop ligado; nenhum erro de JavaScript (script D:\tmp\teste_painel_prints.py).
- Línguas do hipercool no PC2 travadas (problema vermelho no painel): o pc2-trazer passava 30-60 min preso trazendo
  cap09/th/censurado do PC2 e segurava workspace\pc2.lock, então o "fila.py pc2" do controlador só achava "outro pc2
  rodando". Causa provada: o D:\hipercool-videos\bin\pc2.py chamava "ssh" do PATH = C:\Windows\System32\OpenSSH\ssh.exe,
  que entrega o vídeo de 262 MB até faltar 55 KB e para (log fila_pc2-trazer.log mudo desde 21/10 18:38). Com o ssh do
  Git o mesmo vídeo veio inteiro em 27 s. Conserto: constante SSH = ssh do Git nos 3 pontos do pc2.py (backup
  .bak_20261022_ssh_git); teste com a função _baixar de verdade: 262.234.027 bytes em 24 s, igual ao PC2. A rodada
  presa (pid 8276, código antigo) estoura sozinha ~02:09; a próxima já usa o conserto. CONFERIR depois das 02:30:
  fila_pc2-trazer.log com "pc2: ... th pronto" e o problema sumindo do painel.
- Postador, conferido na produção real (02:20): depois da 1ª correção, 14 envios AGENDADOS em vários canais (2 do
  Dicas, que falhava em série) e 2 prints "hashtag_por_cima" (01:19 Dicas e 01:37 Game Noturno) = a lista estava por
  cima do título e o envio seguiu. Sobrou 1 falha (Dicas 01:26, print falha_dicasfinanceirasdaia): o limite diário
  estourou no meio do 3º envio e a lista do "#shorts" do título estava aberta AO LADO da descrição; o clique no título
  passava e a lista ficava. 2º ajuste (backup .bak_20261022_hashtag2): o 1º clique agora é sempre no cabeçalho do
  diálogo (fecha a lista do título e a da descrição), depois o clique no título; e erro genérico com "limite diário" na
  tela vira Falha("limite") (antes "erro"), pra conta entrar na pausa de limite e não ser tentada de novo no dia.
  Teste em navegador, 4 casos (sem lista 0,8 s; lista por cima 0,8 s; só com Escape 6,5 s; lista ao lado 0,7 s) + aviso
  de limite lido no diálogo: todos OK. A falha do ForjaReact 01:59 veio de fora do postador de parceiros (provável rede
  manhwa-react, dona do canal), que não lê a pausa de limite do parceiro_diario: ver se a rede respeita o limite.
- Pergunta do dono "por que não usa o Webshare?": teste sem cookie com o IP de casa barrado: proxies fixos 2 de 2
  barrados; o rotativo passou na consulta mas o download travou (o IP muda a cada pedido). E o anime_fetch usa
  --cookies de conta logada, que não pode sair por IP de datacenter. Webshare segue nos lugares obrigatórios (Groq, Edge
  TTS, Gemini TTS, capas). Memória feedback_ytdlp_sem_rajada atualizada.

- I voz clonada no painel (FEITO 02:00): /api/voz junta _historico.jsonl (nicho, canal, encaixe; existe desde 21/10),
  postar.json (link e canal postado) e métricas do Studio (views) por vídeo; narrador ganhou "nichos narrados" e views
  somadas. Tabela de vídeos com colunas nicho/canal/encaixe/views/YouTube (link "abrir") e filtro em cada uma. Teste:
  57 vídeos, 23 com nicho, 44 com link; filtro nicho=manhwa 57 -> 3 no navegador; prints rev22_desk_voz_*.png e
  rev22_cel_voz.png sem erro de JS. Views ainda vazias: a leitura do Studio (metricas_studio.json) não passou por
  esses vídeos novos; aparece "sem leitura" até ler. Canal sem postar.json aparece pelo nome do cadastro (canais.json).
- M (FEITO 01:54): o Short do Bicho Noturno (nicho animais) pegou dino_da_silva_sauro_familia_dinossauro pelo nicho
  (encaixe 3, nunca usado no nicho, 15 candidatos), base francisca, config 2. Roteiro com tempo (10 frases, 0-60 s do
  original), 1º gancho recusado por perder o fato e o 2º aceito, com o jeito do personagem ("Não é a mamãe", "meu caro
  pançudo"). DEFEITO NOVO ACHADO: a FONTE do Short não é de animais: "The five richest pastors in Brazil" do parceiro
  @papodebixo (lista "papodebixo" no discover). O narrador por nicho está certo; a escolha do vídeo do parceiro não
  confere o assunto. Não barrei (o Bicho Noturno está com fila 0 e ficaria sem postagem). FAZER: no parceiro_diario /
  anime_discover, conferir que o título/legenda do candidato é do nicho do canal destino antes de baixar (ou tirar o
  @papodebixo do Bicho Noturno).

L (resposta pro dono) — 2 tablets Android servem pra:
1. Tela fixa do painel (http://<PC1 na Tailscale>:8790 com a chave do celular), navegador em tela cheia: produção,
   problemas e saúde à vista o tempo todo, sem abrir o PC.
2. Tela de revisão de vídeo (o mesmo da K): cada Short/longo que fica pronto abre sozinho; o dono assiste e aprova ou
   reprova (alimenta o aprendizado). Funciona igual num tablet e num PC fraco.
3. Conferência das contas pelos apps oficiais (YouTube Studio, TikTok, Instagram): ver alcance, advertência e
   comentário pelo app, que mostra coisas que o navegador não mostra. NÃO usar pra postar em massa nem logar dezenas
   de contas no mesmo aparelho (liga as contas entre si; regra da F5).
Não servem pra render (fracos) nem pra rodar o yt-dlp (mesmo IP de casa).

K FEITO (02:05): rota /api/tela (painel_controlador._tela: vídeos das últimas 48 h na fila do Cortes, hipercool e MS
Energy; arquivo mexido há menos de 90 s fica de fora) + página D:\video-fila\painel_web\tela.html (toca cada vídeo
novo assim que aparece, mais antigo primeiro; sem novidade repete os 8 mais recentes; botão Pular; tenta com som e, se
o aparelho bloquear, toca mudo com botão "Tocar com som"; 1ª vez num aparelho só os 3 últimos contam como novos). O
vídeo sai pela /midia que já existia (Range, só pastas de produção, pede a chave). Teste no Chrome de verdade: tocou,
Pular passou pro próximo, sem erro de JS (print rev22_tela_tocando.png). Defeito achado e corrigido no teste: o aviso
"Esperando..." ficava por cima do vídeo ([hidden] perdia pro display:flex).
COMO PÔR UMA TELA NOVA (PC fraco ou tablet na Tailscale): abrir 1 vez o link do painel com ?chave= (o mesmo do
celular; a chave está em D:\video-fila\estado\painel_chave.txt) pra gravar o cookie; depois abrir
http://revision-pc-1:8790/tela.html. No PC fraco, atalho: chrome.exe --kiosk --autoplay-policy=no-user-gesture-required
"http://revision-pc-1:8790/tela.html". No Android: Chrome > Adicionar à tela inicial; tocar 1 vez pra liberar o som.
Achado de quebra: transferência travada do PC2 deixa vídeo incompleto na pasta (cap09 th, 55 KB a menos); a tela pula
(erro ao tocar), e o conserto do ssh do PC2 evita novos.

K (desenho original) — 2 PCs fracos como TELA:
- Nada instalado neles além de navegador + Tailscale. O painel ganha a página /tela (lista os vídeos que acabaram de
  ficar prontos e toca um atrás do outro em tela cheia) e uma rota que serve o mp4 com suporte a Range, só das pastas
  de PODE_ABRIR (shorts da fila, hipercool, MS Energy). Chrome no PC fraco: --kiosk --autoplay-policy=no-user-gesture-required
  "http://<PC1>:8790/tela?chave=...". "Novo vídeo" = o mesmo laço que hoje abre o Short novo no PC1 (voz_clonada vigia).
- Adicionar uma tela nova = abrir o atalho no aparelho (nada no servidor). Botões aprovar/reprovar opcionais.

Problemas antigos que o painel mostrou (não vieram desta rodada; fazer depois):
- Tarefa "Limpeza source.mp4 anime" (CONFERIDO 02:03): o script EXISTE e roda (o 0x80070002 de 21/10 04:00 foi
  passageiro; próxima 22/10 04:00). Mas quase não libera nada: dry-run achou 59 source.mp4 (7,3 GB; 29 com mais de 2
  dias = 3,8 GB) e só 1 passa (12,5 MB), porque a regra espera final_anime_short.mp4 na mesma pasta e hoje o Short
  pronto vai pra fila (animes recap\shorts). PROPOSTA (precisa do OK do dono, regra de limpeza do D:): considerar
  pronto quando o Short da pasta já foi postado (postar.json com posted_url) e o source tem mais de 2 dias.
- Tarefa ParceiroKaijinre-Postagem "encerrada à força" 00:45 (CONFERIDO): caso isolado; limite da tarefa 3 h, rodadas
  de 3 s a 38 min, a de 01:45 terminou com código 0. Nada a fazer.

### Pela metade (continuar daqui) — ATUALIZADO: itens 1, 2 e 3 abaixo já foram feitos (ver "Concluído depois")
1. V imagens dos 3 canais Noturno (D:\tmp\imagens_canais): as atuais são JPEG com nome .png; banner 1344x768 (YouTube
   exige 2048x1152) e perfil 768x1344. Plano: perfil = recorte quadrado centrado em y=690 -> 800x800 PNG (os 3 têm o
   assunto no centro, conferido); banner = ampliar pra 2560 de largura e cortar pra 2560x1440, salvar .jpg q92 (<6 MB).
   O banner do Game Noturno tem TEXTO QUEBRADO da IA ("G'AANENAB GEMMING"): gerar de novo com imagem_reserva.gerar(prompt
   sem texto, "16:9") (D:\hipercool-materiais\comum\imagem_reserva.py devolve (bytes, modelo)). Esporte e Bicho: bons.
   Depois o dono aplica no Studio (não há automação de perfil/banner).
2. H saúde: o bloco novo em _saude() (painel_controlador.py) tem alarmes falsos e precisa ser refeito ANTES de reiniciar o
   painel: tirar "StatusVideos" das tarefas esperadas (não existe; as reais: ControladorVideos, PainelVideos,
   VigiaVideos, PostadorDeVideos, BackupDriveVideos, ParceiroKaijinre-Postagem, HipercoolPostagem, HipercoolPC2,
   MSEnergy_PostarInsta, MSEnergy_PostarTikTok, TikTokRodadaExtra, ManhwaReact-Rede, ManhwaReact-Lote, VozClonadaVigia)
   e conferir LastTaskResult/LastRunTime; tirar o cofre (lia playwright_state.json morto do hipercool), a pasta antiga
   de TikTok e o "Telegram" que só procurava a palavra TOKEN; tirar os emojis. E medir o que o dono pediu (o que pode
   ACABAR): estado das chaves/cotas em D:\hipercool-videos\secrets (proxies_estado.json, proxy_health.json,
   gemini_estado.json), Pollinations 402 = saldo do dia, Cloudflare 429 por conta, Groq 401, cota do OmniRoute/Opus
   (monitor que lê a cota), Kiro (kiro_renovacao.py), crédito do Flow/Veo (exit 6), espaço do Drive (rclone about
   manhwa-drive:), contas com "limite diário de envios" (parceiro_diario cooldown), contas TikTok banidas.
   Item com ok=false vira "problema" no painel: só pôr o que for real.
3. Reiniciar o painel (tarefa PainelVideos; processos 13452/4200 rodam o código de 21/10 20:46) e tirar prints desktop e
   celular (memória: verificar telas com print real e testar o clique no interruptor do desktop).

### Novo pedido do dono 22/10 ~00:50 — Manhwa Noturno (PRIORIDADE)
Palavras do dono: no Manhwa Noturno pararam de postar os vídeos longos: os Shorts do capítulo completo, os compilados e o
completo em formato paisagem. Os 3 deveriam sair todo dia e o que sobrar do limite vai pros Shorts. E estão usando
Shorts comuns dos canais parceiros nele e no "inovare manhwa br"; um dos dois é pra ser EXCLUSIVO do hipercool.
O que já se sabe: canais.json diz manhwanoturno dono=hipercool, alimentadores {"parceiro": "sobra"}, libera_as 23:00,
max_dia 3; inovaremanhwabr dono=manhwa-react, parceiro livre. A memória diz "pt = Manhwa Noturno desde 16/10" (canal pt
do hipercool). O parceiro.json (D:\recapd-ambientes\producao\config) tem Manhwa Noturno na lista "pt" com fila_alvo 6, e
o postador de parceiros agendou Short de parceiro lá (log 22/10 00:08 "POR QUE ELA VOLTOU após o DIVÓRCIO").
canais.json NÃO se edita à mão: decisão do dono vai em DECISOES de D:\postador-de-videos\bin\canais.py.
Investigação e conserto: ver seção "Manhwa Noturno" abaixo.

### Manhwa Noturno — o que achei (22/10 ~00:40) e o plano
FATOS (com prova):
- Ledger: 4 postagens/dia do hipercool em 16, 17 e 18/10; desde 19/10 só "parceiro/short" (1-2 por dia).
- Motivo: D:\hipercool-videos\config\fila.json postar_pt=false + postar_pt_volta_em="2026-10-24" (+ _postar_pt_motivo):
  "19/10 (dono disse sim): The Inheritor fora do Manhwa Noturno até o fim do congelamento de envio do
  InovareManhwaVerse (advertência de 16/10)". O Manhwa Noturno começou a subir a MESMA série e os MESMOS cortes no dia
  da advertência = evasão (support.google.com/youtube/answer/2802032; punição pode encerrar TODOS os canais).
  Análise completa: D:\postador-de-videos\ANALISE_CRESCER_SEM_BAN_2026-10-18.md, F5. O log
  D:\hipercool-videos\logs\fila_postagem.log mostra "postagem em pt SEGURADA" a cada 20 min. Volta sozinho em 24/10
  (fila._pt_ligado compara a data).
- Os Shorts de parceiro lá fazem parte da mesma decisão (o canal não podia ficar vazio: regra "nunca sem postagem").
- O canal EXCLUSIVO do hipercool é o Manhwa Noturno: D:\postador-de-videos\bin\canais.py DECISOES (18/10): "Manhwa
  Noturno fica com o hipercool (até 3/dia, regra BR), parceiro só a vaga que sobrar" (alimentadores parceiro=sobra,
  libera_as 23:00). O "inovare manhwa br" é da rede manhwa-react (parceiro livre): pode ter Short de parceiro.
- O Cortes ainda tem o Manhwa Noturno na lista "pt" do D:\recapd-ambientes\producao\config\parceiro.json (fila_alvo
  6): gasta produção do PC1 com Short pra ele. Já há 1 Short de parceiro agendado lá pra 25/10 12:20
  (https://youtu.be/00ZM261VhQ0).
- O que a fila do hipercool posta em pt por dia hoje (fila.postagem, quando o pt está ligado): no máximo 1 compilado
  16:9 + 1 completo (9:16) + Shorts do capítulo até a cota (3/dia, regra BR). O compilado NÃO é diário: só quando há
  longo_primeiro (2) capítulos e depois a cada longo_a_cada (3) capítulos novos (fila.postar_longos). O capítulo
  sozinho em 16:9 (paisagem) NÃO é postado: hoje ele só serve de peça do compilado.

PEDIDO DO DONO (22/10): todo dia os 3 formatos longos (Shorts/completo do capítulo, compilado e completo em paisagem)
e o que sobrar do limite com Shorts; Manhwa Noturno só com conteúdo do hipercool.

RISCO DE 24/10 — TRAVADO (22/10 ~00:47): conferido no estado: "_longo_postado" the-inheritor|pt = 0, pt_completo vazio
em todos os 16 capítulos e o único compilado pt pronto é the-inheritor_caps01-02.mp4. Teste sem postar
(D:\tmp\teste_compilado_pt.py, simula 24/10 e troca a função de postar por uma falsa): SEM trava a fila postaria
caps01-02 no Manhwa Noturno na 1ª rodada de 24/10. Trava feita: config\fila.json "longo_pt_desde": 12 (+ obs) e
bin\fila.py postar_longos pula compilado pt com capítulo menor que esse número (backups *.bak_20261022_compilado_pt).
Com a trava: pt não posta compilado nenhum, línguas iguais a antes. Tirar a chave = comportamento antigo.
Ainda falta (dono decide): os COMPLETOS dos caps 3-11. Os caps 1-2 já estão no Manhwa Noturno (16-18/10) e o
"retoma" por canal não sobe de novo; a partir de 24/10 o completo do dia começaria no cap 3. Os caps 3-11 só estavam
no canal advertido dentro do compilado caps 1-11: leitura literal da F5 ("não repostar os vídeos que estavam lá") deixa
postar; leitura cautelosa manda começar no 12. Perguntar ao dono antes de 24/10.

PLANO (fazer em 22-23/10, pronto pra quando o pt voltar em 24/10):
1. NÃO antecipar a volta (evasão). Manter os Shorts de parceiro no Manhwa Noturno até 23/10 (senão o canal fica vazio
   22-23/10). Em 24/10: tirar "parceiro: sobra" do DECISOES (canais.py) e tirar o Manhwa Noturno da lista "pt" do
   parceiro.json (o Cortes passa a produzir pros canais com fila vazia). Isso deixa o canal exclusivo do hipercool.
2. Cadência pedida = 3 longos/dia + Shorts no que sobrar. Com o teto atual de 3/dia (regra BR do DECISOES) não sobra
   vaga pra Short. PERGUNTAR AO DONO o teto do Manhwa Noturno (ex.: 5/dia = 3 longos + 2 Shorts). Lembrar que a conta
   do canal pode não ser verificada (o Studio corta o envio diário, como no ForjaReact) e que canal novo com muito
   envio por dia pesa contra (ANALISE_CRESCER_SEM_BAN).
3. fila.py: compilado pt diário (hoje é a cada 3 capítulos) e postar o capítulo sozinho em 16:9 todo dia (hoje não
   posta). O compilado pt tem que começar no cap 12 (por causa da trava acima): mudar quem monta o compilado
   (fila.tempo_livre / bin\hiper-longo.py) pra fazer compilado pt a partir de longo_pt_desde. Os vídeos 16:9 de cada capítulo já são feitos no tempo livre (fila.tempo_livre); falta a etapa de postar
   (postar_hipercool com --longo aceita o arquivo). Respeitar a análise do vídeo pronto (veredito "ok") e o risco acima.
4. Avisar o dono no resumo: o que voltou em 24/10, o que entrou no lugar dos Shorts de parceiro.

### Fidelidade da voz clonada (dono 22/10 ~02:50) — plano próprio
D:\hipercool-materiais\amostras_voz\clone2\MELHORIAS_FIDELIDADE_2026-10-22.md (estado atual no fim do arquivo).
A/B prontos pra ouvir (clone2\fidelidade\LEIA_PRA_OUVIR.txt); retreino-piloto do porao andando sozinho pela tarefa
VozFidelidadePiloto (dataset 20 min + de-reverb, Kaggle com Ov2Super, amostra de cada checkpoint).
INCIDENTE 05:31: a separação do piloto no PC1 coincidiu com o 1º travamento da voz clonada da produção (rc 0xC0000005, falta de memória): piloto parado e tarefa desabilitada 05:40; o pesado vai pro Kaggle.
CONFIRMADO no log: 2 Shorts falharam por falta de memória enquanto a separação rodava (05:31 rc 0xC0000005 e 05:36
"DefaultCPUAllocator: not enough memory", clone.log de MfAQkNeypDQ e zapc2YyZp0Y). Desde 05:44 o piloto só faz coisa
leve no PC1 (baixar, cortar, mp3); separação, treino e amostras rodam no Kaggle.

### Lista da sessão do Hermes (D:\video-fila\CONTINUAR_MELHORIAS_2026-10-22.md, 51 propostas, nenhuma verificada)
Análise em 22/10 ~02:45 (o que vale; detalhes nos journals citados lá). Andamento:
- HC-08 FEITO 05:35: D:\hipercool-videos\bin\pc2.py _bin_local não manda mais backup pro PC2 (".bkp_", ".antes_",
  qualquer "x.py.<algo>"; backup .bak_20261022_filtro_bkp). Teste: 89 arquivos iriam, nenhum backup, fila.py/pc2.py fora.
- M8/MR-08/HC-09 (views dos Shorts de parceiro) — PLANO, NÃO FEITO: o postador\bin\metricas_rede.py abre 1 página do
  Studio por vídeo (até 12 por rodada, 4 por canal) e trata os de fora da rede (parceiro) como "só 1ª leitura" de 48 a
  96 h com 1 vaga garantida: só 10 Shorts de parceiro no metricas_studio.json; dos 44 Shorts com voz clonada e link,
  0 com views. Fazer: ler as views EM LOTE na lista Conteúdo do Studio (1 página por canal = dezenas de vídeos,
  coluna Visualizações), usando o youtube_studio_extras.sessao e a Trava do postador (não brigar com upload), gravar
  views por video_id no mesmo metricas_studio.json. Com isso o anime_voz_clonada ("bonus_views") e o painel (aba Voz)
  passam a ter dado. Fazer de dia, com print de cada passo.
- M10 (capa de reserva quando a IA recusa): valor baixo pra Short (o YouTube já escolhe um quadro sozinho). Pular.
- HC-07 (checar login dos canais antes do pico, com aviso) e CM-01 (edge COMUM ainda troca Francisca por Thalita fora
  do clone, contra a regra de 16/10): próximos baratos. MR-05 (git local) = commit precisa de OK do dono.

### IDEIA DO DONO 22/10 ~05:20: GPU do Kaggle na PRODUÇÃO (principalmente vídeo longo) — análise e plano
- Onde ganha mais (medido aqui): a CONVERSÃO da voz clonada. Na CPU do PC1 (i5-8365U, sem GPU; o PC2 também não
  tem) leva 2-4x a duração do áudio com o PC livre e ~19x com o PC ocupado: 1 h de narração = 2 a 19 h, por isso
  vídeo longo com voz clonada é "inviável aqui" (memória da voz clonada). No T4 o RVC converte dezenas de vezes mais
  rápido que o tempo real: 1 h de narração em poucos minutos de GPU. É o que libera voz clonada no compilado do
  hipercool e no anime longo.
- Onde ganha pouco ou nada: transcrição (já vai pelo Whisper do Groq, grátis); render de vídeo inteiro no Kaggle
  (teria que subir painéis, cache 2.5D e modelos a cada lote: pesado e frágil). Fica pra depois, só a parte de ML
  (profundidade 2.5D, checagem de nudez) se valer a pena medir.
- Como fazer (mesmo caminho do treino, que já funciona pelo navegador): notebook "conversor" (Applio no mesmo commit
  + o NOSSO patch do rvc\infer\pipeline.py, APPLIO_F0_ESCALA/APPLIO_F0_FINAL_ST, senão o som muda) recebe um pacote
  (as narrações .wav + lista.json no formato do voz_clonada.lote + o .pth/.index do narrador), converte e devolve um
  zip; um invólucro tipo kaggle_piloto.py (clone2\fidelidade) manda e baixa. Cada lote leva ~15-25 min de ida e volta
  (fila do Kaggle + instalar o Applio): serve pra vídeo longo, não pra Short (Short converte em 1-3 min aqui).
  Na produção: narração clonada acima de N minutos vai pro Kaggle; se o Kaggle falhar, sai com a voz sem clone
  (nunca segurar a postagem).
- Cota: 30 h/semana de GPU na conta verificada (emersonjosiel649). O treino usa ~1 h por voz; a conversão de 1 h de
  narração usa minutos. Dá pra dezenas de vídeos longos por semana.
- ATENÇÃO, regra do Kaggle: UMA conta por pessoa. Criar contas do Kaggle nas outras contas Google (pelo RPA) pra
  multiplicar a GPU é proibido e pode banir todas (mesma lógica da F5: ligação entre contas pune tudo). Usar a conta
  verificada que já existe; se faltar GPU, opção paga por hora (decisão do dono).
- MEDIDO 22/10 06:00 (pra decidir Short x longo): Short do Cortes leva mediana 11 min no PC1 (3 a 21 min, 28 Shorts
  com clone em 21/10); a conversão da voz é ~metade disso (1 clone.log com tempos: 6,3 min pra 8 frases; A/B de
  hoje: 30-45 s por frase com o PC ocupado). VÍDEO LONGO: vale muito (horas de CPU viram minutos; a demora de
  15-25 min do Kaggle não importa). SHORT: só em LOTE (as narrações de 10-20 Shorts juntas, poucas vezes por dia):
  libera ~metade do PC1 pra fazer mais Shorts, mas exige partir o Cortes em 2 metades (antes e depois da voz;
  arquivos da sessão do clone) e gasta cota (cada ida ao Kaggle ~15-25 min de sessão; 1 por hora estouraria as
  30 h da semana em ~4 dias). Se o Kaggle falhar, a voz converte aqui como hoje (nunca segurar).
- Ordem sugerida: depois do piloto do porao terminar (a mesma automação do Kaggle), fazer o notebook conversor e
  testar 1 vídeo longo do hipercool com voz clonada antes de ligar na produção.

### Marca d'água na frente da tarja branca (dono 22/10 ~06:20) — FEITO 06:33 e testado
- Defeito: nos Shorts de parceiro do @kaijinre com título na tarja branca, a NOSSA @ (ex.: @manhwanoturno), que anda pela
  tela no lugar da marca móvel deles (84% -> 11% -> 84% da altura), passava por cima da tarja e o borrão que esconde a
  marca deles embaçava as letras do título. Prova: D:\video-fila\logs\prints_marca\antes_RD2C5.png (t=28 s).
- Causa: D:\recapd-ambientes\producao\bin\parceiro_marca.py cobrir() colava a tarja PRIMEIRO e a marca depois.
- Conserto (backup parceiro_marca.py.bak_20261022_marca_tarja): a tarja é colada por ÚLTIMO; ao cruzar a faixa, a nossa
  @ passa POR TRÁS da tarja (que já esconde a marca deles) e o título fica limpo. Nos canais novos (cobrir_canal, @ fixa
  em 0.30): se a @ cair na altura da tarja, vai pra logo acima dela (abaixo, se em cima ficar a menos de 11% do topo).
- Teste com vídeo real (clipe de 12 s do RD2C5FXSIYk, módulo testado numa cópia e trocado de uma vez com os.replace,
  pra não pegar o Cortes que estava rodando no meio): D:\video-fila\logs\prints_marca\depois_RD2C5.png (t=28 s tarja
  limpa; t=25,8 s a @ entrando atrás; canal novo com a @ acima da tarja). Script: prints_marca\teste\testar.py.
- Vale pros Shorts novos. Os que já estavam prontos na fila saem como estão (regra: defeito visual não trava). O PC2
  recebe o arquivo novo na próxima sincronização do bin (pc2_recapd.sincronizar_bin, automática no disparo).

### Rodada 22/10 08:36 em diante (Opus 5.5, sessão nova; crons "continue" 10:10, 12:37, 13:38)
- H saúde COMPLETO (08:50; backups painel_controlador.py e painel_web\index.html .bak_20261022_saude2): 4 itens novos,
  todos medida real, teste direto D:\tmp\teste_saude2.py (20 itens em 32 s):
  - "IA dos agentes: Opus 4.6 (Antigravity)": lê D:\opus_monitor.json do MonitorOpus (sem ssh); sem crédito = amarelo
    com a hora que volta (hoje 17:20); monitor parado há mais de 40 min = vermelho.
  - "Kiro (IA do vigia e do aprendizado)": ssh hermes-bloqueio kiro_renovacao.py --simular (só leitura, 1x por hora)
    + ritmo pelo kiro_renovacao.log. AGORA: 9 contas com crédito, 82 sem; gastando ~10/dia = acaba em ~1 dia, e só
    renova dia 1 (10 dias). Amarelo "acaba antes do dia 1"; 0 contas = vermelho.
  - "Veo (Google Flow): contas com crédito hoje": D:\veo\beta\logs\sessoes_status.json (EXHAUSTED até 00:05) x
    D:\veo\beta\contas.py. AGORA 8 de 13. 0 = vermelho (MS Energy sem Veo novo).
  - "TikTok: contas paradas ou deslogadas": o postador NÃO detecta ban; medida = DESLOGADO no log de ontem/hoje +
    conta sem post há 48 h (tiktok_auto_posted.json) enquanto as outras postam. AGORA 58 de 59 postaram em 26 h; só
    3dfabricadeautomacoesia (deslogada, já conhecida).
  - Novo estado "alerta" (ok=True + alerta): badge amarelo, NÃO vira problema; ok=False continua virando problema.
  Painel reiniciado 08:52 (processos 22592/19048); prints logs\prints_painel\saude2_desk.png, saude2_cel.png e
  saude2_card_*.png (D:\tmp\teste_saude_prints.py): amarelo no Opus e no Kiro, vermelho no TikTok e no limite do
  YouTube, sem erro de JS. H FECHADO.
- RISCO ACHADO PELO H: Kiro zera em ~1 dia e só renova dia 1. Quem usa o Kiro (claude_proxy.json, modelo
  kr/claude-sonnet-4.5): vigia_geral (agente de conserto), painel_ia (IA do painel, "corrigir todos"), aprendizado,
  hipercool claude_client (cai pro Opus 4.6 e depois devolve None: "quem chama sempre tem caminho sem Claude"),
  capas por IA (hipercool, histórias, Cortes). O roteiro do Cortes NÃO usa Kiro (antigravity/gemini-3-flash).
  Vigia e painel IA não tinham reserva.
- RESERVA DO KIRO FEITA (09:08): D:\video-fila\ia_reserva.py (comum): modelos(principal) = principal + reservas,
  tirando quem foi recusado na última hora (estado\ia_reserva.json); falhou_sem_trabalhar = "API Error" sem STATUS e
  sem nenhum passo; marcar(modelo) = fora 1 h pra todos. Reservas grátis testadas com claude.exe -p + ferramenta
  (D:\tmp\kiro_reserva\teste_cli.py): antigravity/gemini-3-flash 11 s, agy/gemini-3.8-flash-high 48 s
  (gemini-3.8-flash-tiered 239 s = fora; cc/ = contas do Claude Code do dono, fora). Na reserva, o vigia e o "aplicar"
  do painel recebem AVISO_RESERVA (só conserto óbvio de 1-3 linhas com backup; na dúvida REVISAR com diagnóstico).
  vigia_geral.chamar_agente e painel_ia._rodar (job["modelo"], job["modelos_recusados"]) usam isso; backups
  *.bak_20261022_reserva. Teste real D:\tmp\kiro_reserva\teste_troca.py (principal falso "kr/nao-existe...", nada
  gravado na produção): vigia recusado -> reserva -> OK; painel IA direto na reserva -> resposta certa; painel IA
  recusado no meio -> repete sozinho -> resposta certa. Junto: regex do STATUS do vigia não pula mais de linha (o
  detalhe saía "[stderr]"). O aprendizado não precisa (já segue com o Gemini se o Claude cair). Vigia do hipercool
  (hipercool-videos\bin\vigia_agente.py, sem edição desde 18/10) com a mesma reserva + mesmo conserto do regex
  (backup .bak_20261022_reserva; sem D:\video-fila, no PC2, cai no jeito antigo); teste
  D:\tmp\kiro_reserva\teste_troca_hipercool.py: recusado -> gemini-3-flash -> OK. Conferir no vigia_geral.log quando
  o Kiro zerar: "recusado pelo gateway ... vai o próximo" e "chamando agente (antigravity/gemini-3-flash)".
- M8 FEITO (10:15) — views em LOTE na lista de Conteúdo do Studio. Causa da falta de views: o metricas_rede roda de
  hora em hora (rede_hora_em_hora.bat) com --max 3 = 3 vídeos/hora (3 páginas do Analytics por vídeo); havia 88 de
  fora da rede sem views em 20 canais. Novo: youtube_studio_extras.views_lista(pg, channel_id, alvos) lê a coluna
  .tablecell-views/.tablecell-visibility (conferido no print D:\tmp\m8_views\lista_cartuchoreact.png), 30 por página,
  passa de página até achar os alvos (até 4), recarrega 1x se a lista não aparecer em 45 s (+ print
  views_lista_<aba>_sem_linhas). metricas_rede.coletar_lote(max_canais, so=None): canais com mais "sem views"
  primeiro, cada canal no máximo 1x a cada 6 h (_analise\metricas_lote.json), só PREENCHE quem é Público, 48 h a 21
  dias e não tem views (fonte_leitura="lista", so_primeira, lido_em, idade_h: a 1ª leitura de 48-96 h do Telegram
  passa a contar esses também); quem já tem views do Analytics fica igual e ganha views_lista. --lote 4 é o PADRÃO
  (o .bat não mudou; --lote 0 desliga). Backups *.bak_20261022_lote. PROVA NA PRODUÇÃO (rodada das 09:30 do .bat, com
  o código novo): hindi 13/14, ru 9/10, ita 7/8, inovaremanhwabr 7/8 em ~4 min (Chrome 6-13 s + lista 34-70 s por
  canal); testes na mão: cartuchoreact 4/4 (456 views = print), manhwanoturno 7/7. Sem views: 88 -> 47.
  Os 48 Shorts com voz clonada e link ainda têm MENOS de 48 h (41 agendados pro futuro, 7 no ar): as views deles
  entram sozinhas quando passarem de 48 h (D:\tmp\m8_views\por_que_sem_views.py e conferir_voz.py pra conferir).
  Erro meu no teste: editei metricas_lote.json pelo PowerShell (UTF-8 com BOM, o Python não leu) e o registro do
  cartuchoreact sumiu; só antecipa a releitura dele. JSON = só pelo Python.
- QUEM GASTA O KIRO (medido 10:25, banco do gateway, só leitura): tudo numa chave só ("opus-vscode-claudecode", a
  mesma do VS Code e da produção); 2.311 pedidos ok em 48 h, 123 de 138 mi de tokens em pedidos de 40-120 mil tokens
  (= sessão de agente do Claude Code); scripts pequenos (< 8 mil) só 1,2 mi. Agentes automáticos em 48 h: vigia geral
  63 chamadas (até 60 voltas cada), vigia do hipercool 13, IA do painel 11 pedidos (51 voltas). Das 63 do vigia geral,
  42 deram "OK, nada a fazer"; 35 eram coisa conhecida: yt-dlp em pausa/"not a bot" (15 OK + 1 REVISAR), capa IA
  recusada pelo filtro (14 OK + 6 REVISAR), legenda YT 429 (6 OK + 2). (D:\tmp\kiro_reserva\motivos_vigia.py)
- CONSERTO (10:30, backup vigia_geral.py.bak_20261022_ruido): RUIDO do vigia geral ganhou só esses 3 padrões justos
  ("capa IA: reserva também não gerou|todas as tentativas reprovadas", "legenda YT (xx) falhou: ...429/Too Many
  Requests/not a bot", "yt-dlp em pausa") e, com a pausa no mesmo trecho de log, "[auto] download falhou" também não
  conta. Replay dos logs reais de 21-22/10 em blocos de 20 min (D:\tmp\kiro_reserva\teste_ruido.py): rodadas que
  chamariam o agente 48 -> 11; continuam aparecendo pipeline/subprocesso falhou, Traceback, roteiro com tempo,
  "sem transcrição", e o download que falhou SEM pausa (21/10 13:16, o incidente real). Cuidado que vi no caminho:
  "burn_subtitles falhou ... rc=4294967284" tem "429" no número; o padrão novo não pega isso (é falha real). Pra não
  sumir de vista: a Saúde mostra a taxa de capas (já mostrava) e o item "yt-dlp (vez única)" agora fica AMARELO "IP
  barrado" com os minutos da pausa (teste com pausa simulada: D:\tmp\teste_saude_pausa.py). Painel reiniciado 10:30.
  Efeito esperado: bem menos crédito do Kiro gasto e menos REVISAR no Telegram. CONFERIR amanhã: contar "chamando
  agente" no vigia_geral.log de 22/10 x 23/10.
- ForjaReact 01:59 (pendência da passagem) FECHADO: NÃO foi a rede do manhwa-react (ela não teve vídeo pro
  forjareact o dia todo: "SEM VIDEO BOM"). O print yt_web\20261022_015939_falha_forjareact.png mostra o arquivo
  "video" (Short de parceiro) batendo em "O limite diário de envios foi alcançado" = o postador de parceiros ANTES do
  2º conserto (02:20). Depois dele: parceiro_postar_auto.log 06:55, 09:52, 10:06, 10:40 "ForjaReact / Dicas: esperando
  passar o limite de uploads da conta — pulando". Nenhuma falha nova desde 02:21.
- O (10:40, /api/agenda): os 25 canais do YouTube têm post HOJE (no ar ou agendado mais tarde). Sem nada pra AMANHÃ
  ainda: ForjaReact (limite diário), Bicho Noturno, @CodigoInteligente-n7j (Fio da Meada), Manhwa Noturno (parceiro
  "sobra" entra depois das 23:00). Reconferir às 13h e às 21h.
- Vigia na produção depois do filtro: 10:15 (código antigo) chamou o agente pela capa IA = OK (3 min de Kiro); 10:35
  (código novo) "outros projetos: ok" sem agente; o detalhe do STATUS saiu limpo.
- Aba Voz (10:35, backups *.bak_20261022_voz_quando): a coluna views não diz mais só "sem leitura": "ainda não
  postado" / "publica 28/10, 12:30" / "lê a partir de <publicação + 48 h>" / "na fila de leitura" (agendado_para do
  postar.json, campo novo publica_em no /api/voz). Print logs\prints_painel\voz_quando_desk.png e _cel.png, 0 erro de
  JS; hoje: 25 não postados, 41 agendados, 7 esperando as 48 h. OUTRA SESSÃO mexe no painel ao mesmo tempo ("ranking
  api", backup dela 10:27): minhas edições entraram por cima das dela sem conflito (conferido por grep dos dois lados).
- Saúde, falso alarme corrigido (10:20): "Tarefas agendadas: não conferiu (TimeoutExpired)" virou problema com o PC
  ocupado (o PowerShell das 14 tarefas passou de 60 s). Agora 150 s e, se estourar, fica amarelo "sem medida" (não
  vira problema). Painel reiniciado 10:20 (processos 18988/9864).
- Problemas do painel às 10:20: só os reais (disco do PC2 4,3 GB; ForjaReact no limite; TikTok 3dfabricadeautomacoesia
  deslogada) + "4 Shorts falharam hoje" = os 4 de 05:23-05:36 (incidente de memória do piloto, já parado). Buraco sem
  Short pronto de 06:55 a 09:51 = IP barrado (pausa do yt-dlp 07:12 -> ~09:26); voltou 09:51.
- Aprendizado (pergunta pro dono, NÃO mexi): 70 mensagens "enviado" em 48 h (até 3 por vídeo, 1 vídeo a cada 30 min =
  ~35/dia) e nenhuma resposta SIM/NÃO desde 20/10 (255 pendentes). As mensagens chegam; o volume é que não dá pra
  responder. Proposta: 1 resumo por dia com os 5 melhores achados, resposta pelo número.
- Docs (10:25): TAREFAS_PARCEIROS.md ganhou nota no topo: quem dispara a produção é o ControladorVideos;
  ParceiroKaijinre-Producao DESLIGADA desde 20/10 05:05 (conferido no agendador); painel, controle.json e este arquivo.
- E (o que faltava, 10:20): o vigia do hipercool (hipercool-videos\bin\vigia_agente.py, modo "vigia") também leva no
  prompt os casos parecidos da base_consertos (o modo "consulta" não); teste com subprocess falso
  (D:\tmp\kiro_reserva\teste_base_hipercool.py): 21 casos na base (16 do vigia do hipercool), 3 no prompt.
- T AUTOMÁTICO DE MADRUGADA (10:20): D:\video-fila\trechos_noite.py + tarefa TrechosNoite (diária 03:20, pythonw do
  venv do recapd, limite 4 h). 1 personagem por vez pelo baixar_trechos2.py, 15 min entre eles, para no 1º bloqueio do
  IP (ytdlp_vez.pausado) e às 06:30; pula quem já tem trechos.json/trechos_revisar.json (quando a lista acaba a tarefa
  não faz nada). Ordem: woody, homem_de_ferro_tony_stark, patolino, lula, naruto, patrick_estrela,
  seu_sirigueijo_peter_griffin, harry_potter, dinho_mamonas_assassinas, thomas_shelby_peaky_blinders (walter_white já
  tinha). TRAVA DE QUALIDADE: o anime_tts abre o Short com qualquer trecho do trechos.json, sem ninguém ouvir, e a
  nota do baixador só mede se as palavras batem; personagem com algum trecho de nota < 0,85 vai pra
  trechos_revisar.json (fora dos Shorts) até alguém ouvir e renomear. Resultado no resumo do Telegram (avisos, não
  importante) e em logs\trechos_noite_AAAAMMDD.log. Teste sem yt-dlp (D:\tmp\trechos_noite_teste\teste.py): pula quem
  tem, bom entra, fraco vai pra revisar, vazio avisa. CONFERIR 23/10 de manhã: o log e se algum Short abriu com trecho
  novo ("abre com trecho original de woody" no _parceiro_AAAAMMDD.log).

### Aprendizado sem resposta do dono (dono 22/10 ~13h: "não sabia que tinha que responder; o sistema decide e deixa
### documentado; quem for mexer é obrigado a ler, já que o vigia e a IA são fracos") — FEITO 13:15
- aprendizado.py (backup .bak_20261022_candidato; acervo.jsonl.bak_20261022_candidato): pendente sem resposta em 24 h
  com nota >= 7 vira "candidato" (promover(), a cada rodada do VigiaVideos e no comando aprovados). Documento
  D:\video-fila\aprendizado\PARA_IMPLEMENTAR.md refeito a cada rodada: A = aprovados pelo dono, B = candidatos em
  grupos (parecidos juntos; mais vídeos primeiro, depois nota), top 40, com como aplicar, link+segundo, trecho e ids.
  marcar aceita vários ids (vírgula) e --motivo; aplicado/reprovado vai pro ja_temos.json (não volta). Mensagem do
  Telegram agora diz "se quiser responda; sem resposta em 24 h o sistema decide". Hoje: 114 grupos de candidatos.
- OBRIGATÓRIO pra quem for mexer na produção (memória feedback_aprendizado_parceiros atualizada): rodar
  `python D:\video-fila\aprendizado.py aprovados`, LER o PARA_IMPLEMENTAR.md, aplicar (teste real + backup) ou
  reprovar com motivo. O vigia e a IA do painel NÃO decidem isso.
- Lista de prioridades do Cortes/recap (40 tarefas): D:\video-fila\MELHORIAS_RECAP_PRIORIDADES_2026-10-22.md.

### Lista da outra sessão (CONTINUAR_MELHORIAS_2026-10-22.md, "FAZER IMEDIATAMENTE") — andamento claude-8a 13:35
- Item 1 (VPS baixadora): testado, NÃO serve sem cookies (7 clientes do yt-dlp barrados na hermes-staging e na 157).
  Saídas = decisão do dono: conta só pra baixar com cookies na VPS / proxy residencial pago só no bloqueio / estoque
  de fontes baixado devagar em casa. Medir antes o efeito do proxy das consultas pequenas (manhã de 23/10).
- Item 4 (horários vencedores): FEITO — parceiro_diario._ordem_horarios (Thompson no placar de horários; detalhes
  e números no Registro 13:35 do CONTINUAR).
- Item 3 (reações reais do narrador): SEM MATERIAL — reacoes_reais.py pronto, mas os 8 min de treino de cada parceiro
  quase não têm reação (0 aproveitáveis nos 13); nada ligado na voz. Próximo passo (gasta IP) = decisão do dono.
- P04 (checagem diária de login, 04-08 h): FEITO — checar_canais_diario.py + subvigia + item na Saúde. 1ª rodada
  completa 23/10 de madrugada: conferir logs\checar_canais.log do postador.

### Ordens do dono 22/10 ~20:15 (respostas à lista) — FAZER NESTA ORDEM (crons continue 00:17 e 01:19)
- [x] R1 limpar_source.py: a regra nova JÁ estava feita (02:24, outra sessão); dry-run 20:20: sobram só 9 sources
      (anime longo, saem sozinhos pela "tentativa encerrada" em 3 dias). Nada a mudar.
- [x] R2 FEITO 20:30 — notificar_telegram._placar_titulos registra "nicho_canal" (grupo = canal_id do ledger, item =
      midia da ficha, vitória = acima da mediana do canal; backup .bak_20261022_nicho_canal); parceiro_diario
      _nicho_do_canal (backup .bak_20261022_nicho_canal): principal = nicho do cadastro até outro ter 5+ medidas no
      canal e média (+1/+2) 0,1 maior; 20% testa outro nicho (Thompson); log "nicho: <canal> testa/agora é ...".
      Backfill com as medições de 48 h: 47 (D:\tmp\alcance\backfill_nicho_canal.py). Simulação 1000x por canal
      (D:\tmp\alcance\teste_nicho.py): ~80% o nicho do cadastro, 20% espalhado; Dicas já testa dorama mais (2/2).
- [ ] (texto original do R2) NICHO POR CANAL PELO FUNIL (dono: "os nichos devem ser decididos mais pelo algoritmo do que dá certo no canal
      do que pelo nome; vídeo de mangá pode dar mais certo no canal que fizemos pra dorama; o funil vai definindo o que
      é de cada canal e separando"): placar por (canal, nicho) no medir_48h + escolha do nicho por Thompson no
      parceiro_diario._escolher_fonte (o nicho do cadastro começa na frente, os outros vão sendo testados).
- [x] R3 ForjaReact: inventário SÓ LEITURA no Studio 20:40 (D:\tmp\forja\inventario.py, print lista_short.png):
      "1–8 de 8", todos PÚBLICOS, nenhum rascunho/privado — os duplicados já não existem. Nada apagado.
- [x] R4 FEITO 21:05 — gerador = D:\flow-imagens\gera_imagem.py (dono indicou; Nano Banana 2.1, contas do Veo, 0
      crédito). D:\tmp\imagens_canais\flow\gerar_noturnos.py: arte SEM texto (16:9 e 1:1) no estilo do Manhwa Noturno
      + título por cima (Luckiest Guy amarela, Montserrat) na área segura 1546x423 -> <n>noturno_banner_2560x1440.jpg
      e <n>noturno_perfil_800x800.png (conferidos no olho). aplicar_studio.py: Personalização > Branding, "Enviar"
      escolhido pelo título do bloco (o 1º ensaio mandou o perfil pro banner e o Studio recusou; nada publicado),
      recorte "Pronto", "Publicar". PUBLICADO em Game, Esporte e Bicho Noturno (prints studio_<n>_3_publicado.png).
- (histórico) R4 BLOQUEADO 20:50: não achei no PC nenhum gerador de IMAGEM pelo Flow (grep labs.google em todos os bin/comum:
      só o Veo de VÍDEO no controlador/gera_auto; a pasta "como cirar imagens de canais" usa o capa_ia.py do hipercool,
      Pollinations, que está sem saldo — HC-06). Perguntei ao dono onde está o gerador. Texto original:
      Imagens dos 3 Noturno (Game/Esporte/Bicho): refazer com o gerador NOVO que usa o Flow no navegador (dono: "é o
      melhor") e APLICAR no Studio (perfil + banner).
- [ ] R5 (PRÓXIMO; achado: demucs instalado em D:\hipercool-materiais\python\venv pra separar a voz da trilha; baixar
      os 4 s pelo PROXY, que é pequeno, e não pelo IP de casa) Reações reais: baixar UMA vez e reusar (banco por narrador; nunca baixar de novo a cada vídeo): legendas dos
      vídeos dos parceiros pelo proxy -> achar reações -> baixar só 4 s de madrugada -> reacoes_reais -> inserção com
      chave desligada + amostra A/B pro dono.
- [~] R5 COLHEITA AUTOMÁTICA 23:45: 1º teste (mike) — lista de 15 vídeos pelo proxy OK, 1ª legenda lida (0 reações),
      2ª legenda: proxy barrado ("not a bot") e a rodada parou; agora tenta até 3 proxies por pedido. Cada pedido espera
      a vez única do yt-dlp com a produção (13 min no teste) -> roda de MADRUGADA: tarefa ReacoesColheita 01:30
      (reacoes_colheita.bat, 40 pedidos/noite, limite 3 h, log amostras_voz\reacoes_colheita.log). CONFERIR 23/10:
      o log e humano\reacoes.json; com reações no banco, gerar a amostra A/B (NARRACAO_REACOES=1) pro dono ouvir.
      Reação é rara na legenda automática: o banco enche devagar (algumas noites).
      23/10 05:22 CONFERIDO: a rodada de 01:30 NÃO fez nada (bug: o "40" do --max-pedidos virava filtro de voz) ->
      consertado (backup .bak_20261023_argv). Teste real depois: lista OK, legenda pelo proxy = "not a bot" nos 3
      proxies (mesmo bloqueio da legenda da produção) -> o banco só enche quando os proxies voltarem a passar.
- (histórico) R5 EM TESTE 23:10 — D:\hipercool-materiais\bin\reacoes_colheita.py (tudo pelo PROXY: lista do canal, legenda
      pt com tempo por palavra, só ~4 s de áudio com --download-sections; demucs separa a voz; corta nas pausas;
      grava humano\reacao_NN.wav + reacoes.json; para com 4 por voz = reuso pra sempre; estado
      amostras_voz\reacoes_colheita.json). 1º teste: mike, 8 pedidos. FALTA depois: tarefa de madrugada + inserção no
      narracao_curva.humanizar com chave desligada + amostra A/B pro dono.
- [x] R7 JÁ FEITO por outra sessão às 22:06-22:14 (prompt v7 do anime_script: personagem narra o vídeo inteiro como
      ele, manias/bordões reais/referências/"soaria falso" do persona v2 de 62 vozes; monitor_bordoes.py ligado no
      anime_segments tira o bordão que a voz fala estranho 2x). Conferido: ainda sem Short com personagem desde 22:08.
- (texto original) R7 (dono 22/10 21h, PRIORIDADE) PERSONAGEM NARRA COMO ELE MESMO: "parar de ser alguém falando com a voz da
      Chiquinha narrando um vídeo, pra ser a própria Chiquinha narrando do jeito dela" (ex.: "pois é, pois é, pois é",
      muito a cara dela). Inserir no roteiro coisas que o personagem falaria (bordões, jeito, reações, como ele chama o
      público) e MONITORAR quais falas icônicas ficam estranhas (pra trocar/tirar).
- [x] (23:00) ESTOQUE NA PAUSA: anime_auto agora usa o estoque de fontes quando o IP está pausado (antes parava antes
      de chegar nele). Detalhes no Registro 23:00 do CONTINUAR.
- [x] R6 FEITO 23:18 — hipercool bin\vigia_agente.checar ignora log de capítulo que terminou ("Vídeo pronto" no fim)
      e olha o mais recente ainda em andamento (backup .bak_20261022_cap_pronto); checagem real: sem o alarme do cap14.
- [x] R5 (parte 2) 23:15 — narracao_curva.humanizar: reação real do narrador logo DEPOIS de frase de impacto, máx 2 por
      vídeo, no lugar da respiração; chave reacoes_ligadas() DESLIGADA (NARRACAO_REACOES=1 ou comum\reacoes.json
      {"ligado": true}); com ela desligada nada muda (o sorteio extra nem roda). Teste com voz falsa
      (D:\tmp\reacoes_teste\teste_insercao.py): ligado 2,00->2,50 s + words.json deslocado; desligado sem reação.
      Propagado: recursos.py subir narracao_curva.py --de recapd (comum + hipercool + historias + recapd).
- (texto original) R6 (alarme falso do cap14 no vigia do hipercool: combinar com a sessão do hipercool).
- Manhwa Noturno (teto/caps 3-11): está com a claude-c2; não mexer.

### PENDE DO DONO (só ele pode; o resto segue sozinho)
1. Studio: "verificação única" (telefone) nas contas do ForjaReact (emersonjosiel0), Filme Noturno e Dicas financeiras da
   ia: o próprio Studio diz que isso libera mais envios por dia.
2. Studio do ForjaReact: apagar os vídeos privados duplicados "TRAÍDA E ROUBADA! O Sistema de Vingança Mais Forte!".
3. Aplicar as 6 imagens de D:\tmp\imagens_canais\final (perfil 800x800 + banner 2560x1440) no Game/Esporte/Bicho Noturno.
4. Manhwa Noturno: qual teto por dia (3 longos + Shorts não cabem em 3/dia) e se os completos dos caps 3-11 podem sair lá
   depois de 24/10 (leitura literal x cautelosa da F5).
5. OK pra mudar a regra do limpar_source.py (libera ~3,8 GB do D:, hoje com 11% livre).
6. Bicho Noturno: tirar o parceiro @papodebixo (posta fora do nicho) ou aceitar a checagem de assunto no discover.
7. Se este histórico for compartilhado: trocar a senha de 1 proxy Webshare (apareceu num log de ferramenta no teste de 01:50).
8. (22/10 tarde) 5 pares de Short com a MESMA fonte de parceiro já no ar em 2 canais (lista no Registro 15:30 do
   CONTINUAR): deixar ou tirar 1 de cada. A trava nova impede novos.
9. Mix de nichos (diagnóstico de alcance): mais filme/dorama/fatos, menos kaijinre/manhwa nos canais de qualquer nicho?
10. yt-dlp barrado: a VPS não serve sem cookies. Conta só pra baixar na VPS / proxy residencial pago só no bloqueio /
    estoque de fontes baixado devagar? (antes medir a manhã de 23/10 com o proxy das consultas + o download em 1 passo)
11. Reações reais do narrador: buscar o material nos vídeos dos parceiros (gasta o IP de casa de madrugada)?
12. Só pra saber: o Kiro acaba em ~1 dia (renova dia 1); vigia e IA do painel já trocam sozinhos pra reserva grátis.

### Fila do que falta depois (em ordem)
- PC2 CONFERIDO NA PRODUÇÃO (02:18): fila_pc2.log "[02:14:10] pc2: the-inheritor-cap09 th pronto" e "PC2 terminou a
  versão th de the-inheritor-cap09" (disparo do controlador 02:12:31, já com o ssh do Git). O vídeo preso desde 21/10
  chegou e as línguas voltaram a andar. Falta só o problema vermelho sumir do painel (ele olha as 3 últimas linhas do
  fila_pc2.log; some nas próximas rodadas).
- 23/10: 1º envio do ForjaReact e do Dicas depois da pausa de limite (AGENDADO no parceiro_postar_auto.log; se aparecer
  print "hashtag_por_cima" em logs\yt_web, a lista estava por cima e o conserto agiu).
- Antes de 24/10: Manhwa Noturno (plano acima) depois da resposta do dono.
- O: Bicho Noturno com fila 0 (havia Short sendo feito 00:08); conferir às ~13h que todo canal teve post no dia.
- AVISAR O DONO (só ele pode): fazer a "verificação única" (telefone) no Studio das contas do ForjaReact
  (emersonjosiel0), Filme Noturno e Dicas financeiras da ia (a mensagem do Studio diz que libera mais envios por dia), e
  apagar os vídeos privados duplicados "TRAÍDA E ROUBADA! O Sistema de Vingança..." no ForjaReact.
- T PREPARADO (02:12), NÃO RODADO: o IP de casa está sendo barrado de novo (01:04 e 01:41; pausa automática ligada) e
  cada pedido durante o bloqueio alonga o bloqueio e para os Shorts. O baixador estava só em D:\tmp; cópia permanente
  em D:\video-fila\baixar_trechos2.py, agora com a regra do ytdlp_vez: não baixa se pausado() > 0 e, se levar "not a
  bot"/429, liga a pausa pra todos (pausar) e para a rodada inteira (teste sem YouTube: parou antes de chamar o
  yt-dlp). Rodar 1 personagem por vez, de madrugada sem bloqueio:
  D:\recapd-ambientes\producao\venv\Scripts\python.exe D:\video-fila\baixar_trechos2.py woody   (e assim por diante)
- T: 49 personagens sem trecho original (D:\tmp\relatorio_t_trechos_faltantes.txt). Baixar 1 por vez com intervalo,
  pela vez do yt-dlp (ytdlp_vez), só quando não houver 429; começar pelos bordões REAIS e famosos (Woody, Homem de Ferro,
  Lula, Patolino, Seu Sirigueijo, Naruto, Thomas Shelby...). Muitos bordões da lista foram inventados pela IA: não têm
  trecho no YouTube.
- M: conferir o próximo Short do Bicho Noturno (nicho animais) com narrador por nicho.
- I: voz clonada no painel com nicho/canal/views por vídeo (o histórico de narrador x nicho NÃO está em
  config\_historico.jsonl: achar onde o anime_voz_clonada grava).
- E: FEITO 22/10 08:20 (janela da conversa, documento por pedido, "corrigir todos", base de consertos no prompt da IA
  e do vigia geral). Falta só o vigia do hipercool consultar a base (projeto dele) e o dono usar o "corrigir todos".
- K: 2 PCs fracos como tela que abre o vídeo pronto sozinho. L: responder pra que servem os 2 tablets Android.
- Sistema de aprendizado com vídeos dos parceiros: EXISTE e roda (D:\video-fila\aprendizado.py, VigiaVideos a cada
  30 min; acervo 312 achados em 22/10 07:15). MAS o laço não fecha: 0 aprovados e 0 reprovados (255 pendentes, 57
  descartados; placar claude-sonnet 151 x gemini 104 pendentes). Ver com o dono se as mensagens chegam e se ele quer
  responder "sim/não" ou outro jeito (ex.: 1 resumo por dia com os 5 melhores). "aprovados" vazio = nada a aplicar.
- Docs: D:\hipercool-videos\docs\ANALISE_UNIFICACAO_PROJETOS.md e D:\video-fila\TAREFAS_PARCEIROS.md. ATENÇÃO: os dois
  foram alterados por OUTRA sessão às 01:44-01:47 de 22/10 (11 sessões abertas na máquina, 1 ocupada): combinar antes de
  editar. O TAREFAS_PARCEIROS ainda não cita o controlador.
- FEITO 22/10 05:25 (dono mandou): as 55 cópias de videos_voz_clonada apagadas (cada uma idêntica por md5 ao
  video.mp4 da fila; 1,24 GB; lista em videos_voz_clonada\_copias_apagadas_20261022.txt). Nenhuma cópia nova desde o
  conserto de 21/10. E o vigia abria a pasta Documentos em vez da do vídeo (aspas do explorer /select com espaço no
  caminho): consertado em bin\voz_clonada.py (_mostrar).
- Bloqueado: voz clonada no PC2 (falta disco).
