# Crescer sem banir os canais — análise de 18/10/2026

Pedido do dono: "veja tudo que podemos melhorar dentro da barreira de não banir os canais".
Arquivo de controle: cada achado entra aqui na hora. Ao retomar, seguir só as frentes que não estão "feita".

Base: suspensão de 22 canais em 04/09 por "spam, práticas enganosas e golpes" = padrão de rede coordenada
(ver SPAM_BANIMENTO_2026-09-04.md). 18 das 44 contas do bot de engajamento (D:\projetos-navegador) eram desses canais.

## Frentes

| # | Frente | Status |
|---|---|---|
| F1 | Engajamento automático ainda ligado (comentários/likes entre os próprios canais) | feita |
| F2 | Volume e padrão de postagem (ledger, tetos, horários) | feita |
| F3 | Mesmo conteúdo em vários canais (rede manhwa-react, parceiros, catálogo) | feita |
| F4 | Direitos autorais (advertências atuais, bloqueio de obras) | feita |
| F5 | Ligação entre contas (IP, navegador, OAuth) | feita |
| F6 | Metadados repetidos (título, descrição, tags, comentário fixado) | feita |
| F7 | Alavancas legítimas de crescimento (o que já existe, o que falta) | feita |
| F8 | Medição (o que usamos pra decidir) | feita |

## Feito depois da resposta do dono (19/10 00:20)
- Item 1 (dono: "sim"): pt do hipercool segurado — `hipercool config/fila.json` `postar_pt: false` +
  `postar_pt_volta_em: 2026-10-24` (volta sozinho, `fila._pt_ligado`). Parado o upload que estava em curso
  (compilado `the-inheritor_caps01-02.mp4` no Manhwa Noturno; a análise tinha reprovado um capítulo dele às 00:11 e
  ele subia mesmo assim). Log confirma "postagem em pt SEGURADA" às 00:22. Nota "substitui..." trocada em
  `youtube_navegador.json`. Pode ter ficado um rascunho no Studio do Manhwa Noturno.
- Item 3 (dono: "sim, se tiver os suficientes"): nudez achada segura o vídeo — `postar_hipercool._revisao_ok` devolve
  `nudez` só com veredito "reprovado" do mesmo arquivo (sem reanalisar a cada rodada); `fila._nudez` tira o
  capítulo da vez no pt e nas línguas e a fila passa pro próximo; compilado e Shorts cobertos (compilado confere cada
  capNN.mp4; Short confere o completo de onde saiu). Testado na fila real: 13 de 16 capítulos pt reprovados (cap 3 já
  está PÚBLICO no Manhwa Noturno), cap 2 reprovado em hi/id/it/ru/th/vi. Canal sem vídeo liberado recebe Short de
  parceiro, então nenhum fica vazio.

## Resumo por prioridade (19/10)

Tudo abaixo era proposta quando foi escrito (antes da resposta do dono).

**Urgente (risco de perder todos os canais):**
1. Manhwa Noturno repostando The Inheritor durante o congelamento do InovareManhwaVerse = evasão de advertência
   (F5). Parar The Inheritor ali até ~23/10 e não repostar o que já estava no canal advertido.
2. ~~30 das 31 fontes de Short de parceiro sem autorização registrada (F3)~~ — dono confirmou em 19/10: todas
   autorizadas.
3. Análise de nudez não segura a postagem (F4). Travar só quando o veredito for "exposto".

**Importante (reduz risco e custa pouco):**
4. Hipercool nas línguas: 27 de 32 recaps com 0 view em 48 h (F8) — conferir restrição no Studio e parar onde dá 0.
5. Brecha do nome da obra em hashtag no revisor da rede (F6) — comparar sem espaço/pontuação.
6. Exemplos literais no prompt ("ninguém reparou…") e mesmo tema repetido no canal (F6).
7. Comentário fixado "Comenta SEM CENSURA" (F7) — trocar por pergunta sobre a história.
8. Aviso no Telegram quando a rede passar de X uploads/dia (F2) — só aviso.
9. Mover `run_mega_engage.bat` e `run_painel_e_mega_engage.bat` para `_legado` (F1).

**Crescer:**
10. Coração e resposta nos comentários de quem assiste, pelo próprio canal (F7).
11. Concentrar volume nos formatos que passam de 1.000 views (react de filme/série, drama, luta de anime) e cortar
    nos canais com mediana perto de 0 (F7).
12. Verificar por telefone os canais que faltam: libera vídeo relacionado, fixar comentário e A/B (F7).
13. Medição: título real do hipercool no placar, CTR do Studio, e medir os Shorts de parceiro antes de manter 60/dia (F8).

**Só o dono faz no Studio:** ler de quem veio a 2ª advertência do french (18/10); ver "Restrições" dos recaps com
0 view; dizer quais parceiros autorizaram.

## Achados

Ponto de partida: a auditoria de 15/10 (`D:\veo\docs\auditoria_2026-10-15\ler_postagem_banimento.json`, 12 problemas
e 13 oportunidades). Aqui só confiro o que dela continua aberto e acrescento o que ela não olhou (crescimento, medição).

### F1 — engajamento automático (18/10 23:40)
- Bot de likes/comentários (`D:\projetos-navegador`): parado desde 21/08, `paused: true` desde 18/10, tarefa
  MegaEngageMonitor desabilitada. OK.
- Sobrou atalho manual que liga o bot: `D:\hipercool-videos\run_mega_engage.bat` e `run_painel_e_mega_engage.bat`
  (não agendados). Proposta: mover para `_legado` para ninguém rodar por engano.
- Único engajamento automático ligado: tarefa ManhwaReact-Comentarios (a cada 30 min) — o PRÓPRIO canal posta o 1º
  comentário no PRÓPRIO vídeo (`mr/rede.py:1432-1479` passa `--canal <dono> --video <id>`). Isso é permitido.
  Ainda falha em alguns canais: `403 insufficient permissions` no ManhwaReact em 18/10 19:54
  (`D:\manhwa-react\logs\rede_comentarios.log`).

### F2 — volume e padrão (ledger 12/10 a 18/10, 178 uploads)
Resolvido desde 15/10 (conferido no código e no ledger):
- piso no código: 4 por canal/dia e 1 h entre vídeos do mesmo canal (`politica.py:106`), json só aperta;
- upload por API proibido: 0 uploads por `youtube_poster.py` depois de 16/10 22h (antes: 20);
- público direto virou agendado (`politica.horario_obrigatorio`, usado nos dois posters): último público direto em
  18/10 13:26; nenhum depois;
- caminho antigo do VO3 saiu do `postar_tudo_auto.bat`, AgendadorVO3 desabilitado;
- nenhum canal com mais de 4 por dia de publicação depois de 17/10.

Aberto:
- **Volume da rede triplicou num dia**: 22–24 uploads/dia de 14 a 17/10, **60 em 18/10** (shorts de parceiro em
  todos os canais). O dono decidiu em 16/10 que o limite é por canal, não coletivo. Mas os 22 canais caíram juntos
  justamente por serem lidos como uma rede (mesmo PC/IP, mesma família de contas). Sugestão: aviso no Telegram se a
  rede passar de X por dia (só aviso, sem travar), para o dono ver a curva.
- Horários de publicação estão espalhados (01h–23h, pico 12–13h). OK.

### F3 — mesmo conteúdo em vários canais
- Rede do manhwa-react: continua com 1 canal por vídeo (`mr/rede.py:12, 380-400`). OK.
- **Hipercool**: o mesmo capítulo do The Inheritor saiu em até 9 canais (13–15/10) e ainda sai em 5 em 18/10
  (Manhwa Noturno + ru/thai/hindi/viet), dublado em cada língua. Dublar para canal de outra língua é prática aceita;
  o risco é outro: **uma reclamação de direitos sobre a obra vira advertência em todos esses canais de uma vez**. O
  francês já tem 2 advertências e a 3ª derruba o canal e os associados. Recap hipercool tinha mediana de 1 view
  (aprendizado_global, n=6) — o espalhamento não está trazendo retorno que compense.
- **Shorts de parceiro — maior risco aberto hoje.** `recapd-ambientes\producao\config\parceiro.json` tem **31 fontes**;
  só a @kaijinre tem a parceria anotada (memória de 16/10). As outras 30 (entraram em 17–18/10: @king_chan01,
  @richan-anime, @ansaketv, @nerdcf.animes, @100ANIMEE, @drameela, @olaranjo1, @jresumos, @inusifatos,
  @canalutopia, @thalisshortsbr, @futtres e mais 18 por ID de canal) **não têm registro de autorização** nem no
  config nem no `TAREFAS_PARCEIROS.md`. O pipeline baixa o Short, troca a marca deles pela nossa e põe a nossa voz;
  cada Short vai pro pt + até 3 línguas (`linguas_por_fonte: 3`), nos canais inovare sobreviventes.
  Se alguma fonte não autorizou, isso é reupload de terceiro com a marca trocada: reclamação de direitos,
  "conteúdo reutilizado" e "práticas enganosas" — o mesmo motivo da suspensão de 04/09.
  Proposta: campo por fonte `autorizado: {quem, data, prova}` e o `parceiro_diario.py` só usar fonte com esse campo;
  guardar print da conversa de cada parceiro (já sugerido para as vozes em `project_intros_voz`).
  **Respondido 19/10: o dono confirmou que TODAS as fontes do `parceiro.json` são parceiras autorizadas.** Não é
  risco aberto. Fica só a sugestão de guardar o print de cada autorização, caso venha reclamação.
- Detalhe menor: um Short de 18/10 ficou com pasta/obra "não-especificado-no-título" (o extrator não achou o nome);
  o título publicado saiu normal.

### F4 — direitos autorais e advertências (19/10)
Quadro atual (`config/canais_status.json`, `rede_canais.json`, `youtube_navegador.json`):
- **InovareManhwaVerse**: advertência de diretrizes por **nudez** em 16/10 (compilado caps 1-11 do hipercool), envio
  bloqueado até ~23/10, vale até 14/01/2027; e advertência de direitos autorais desde 08/10.
- **inovare french**: **2 advertências de direitos autorais** (27/09 e 18/10). A 3ª encerra o canal — e encerramento
  pode levar junto os canais ligados à mesma conta/dono. Pausado desde 18/10 23:15.
- **inovare english**: envio bloqueado por advertências de diretrizes ("Muitos avisos"). Pausado.

O que já protege:
- trava de música (lista de faixas bloqueadas) e o revisor da rede que barra o nome da obra no metadado;
- o poster para quando o Studio mostra a página de advertência (`youtube_web_poster.py:300`);
- tudo agendado (`politica.horario_obrigatorio`).

Aberto:
- **A análise de nudez não segura mais a postagem.** `postar_hipercool.py:449-451`: se `revisao_video` não dá "ok",
  só escreve no log e sobe mesmo assim (regra do dono de 18/10, "canal nunca fica sem postagem"). Foi exatamente
  esse tipo de vídeo que deu a advertência de 16/10. Mais 2 advertências de diretrizes em 90 dias apagam o canal,
  e o hipercool hoje sobe em 5 canais (Manhwa Noturno + ru/thai/hindi/viet). Proposta que respeita as duas regras:
  travar **só** quando o veredito for "exposto" (nudez vista) e seguir subindo quando o motivo for outro (sem
  veredito, análise velha); o canal posta o próximo vídeo liberado da fila, então não fica vazio.
  **Pergunta ao dono.**
- **Agendamento = proteção (regra do dono, reforçada em 19/10 — eu tinha escrito errado aqui).** Todo vídeo sobe
  agendado, nem que seja pra 10 min depois: quando há problema de direitos, o aviso vem ANTES de publicar e o YouTube
  não deixa ir ao ar; como não vai ao ar, o canal não leva advertência. Já está no código
  (`politica.horario_obrigatorio`, público sem data vira agora+11 min) e não pode sair.
- **O poster confirma "publicar mesmo assim" com a verificação ainda rodando** (`youtube_web_poster.py:708-710`).
  Ideia já anotada na auditoria (item A1) e não feita: depois do agendamento, uma passada que abre o vídeo no
  Studio quando a verificação termina e, se houver reivindicação/restrição, volta para privado e avisa no Telegram.
- **Mesma obra em vários canais** (ver F3): uma reclamação manual do dono da obra pode acertar vários canais no
  mesmo dia. Proposta: não pôr a mesma obra do hipercool num canal que já tem advertência ativa de direitos.
- Ação manual que só o dono faz: no Studio do french e do InovareManhwaVerse, ler de qual obra e de quem veio cada
  advertência de direitos (a 2ª do french é de 18/10). Saídas para advertência de direitos: esperar os 90 dias,
  pedir retratação a quem reclamou, ou contranotificação (só se o uso for legítimo). Essa obra/fonte sai da fila.

### F5 — ligação entre contas (19/10)
Como é hoje: cada conta tem o próprio perfil do Chrome (`youtube_web_poster.py:175`, `--user-data-dir` + CDP), todas
saem do IP de casa (PC1 e PC2). Upload por API está proibido; o único uso de API que sobrou é o caminho antigo de
comentário (`mr/publish.py:144`) — o comentário da rede já sai pelo Studio (`logs/rede_comentarios.log`, "extras
studio"). O projeto OAuth compartilhado deixou de importar para upload.

Não vale a pena "esconder" a ligação (proxy por conta, navegador falso etc.): o YouTube trata isso como evasão e
derruba tudo. Ter vários canais do mesmo dono no mesmo IP é normal; o que pune é o comportamento (F1–F3).

**Achado mais grave da análise — evasão de advertência no Manhwa Noturno:**
- InovareManhwaVerse levou advertência de diretrizes em 16/10 (01:52 subiu `the-inheritor_caps01-11.mp4`), com
  envio congelado até ~23/10.
- No mesmo dia, 16/10 12:48, o **Manhwa Noturno** (conta `inovaremanhwaverse2@gmail.com`, nota em
  `youtube_navegador.json:294`: "substitui o InovareManhwaVerse até a advertência vencer") começou a subir **a mesma
  série e os mesmos cortes**: `cap1_parte01..04`, `cap-tulo-1`, `cap-tulo-2` — que já tinham saído no
  InovareManhwaVerse em 15–16/10. De 16 a 18/10: 12 uploads no ledger, 11 deles The Inheritor.
- Regra oficial (support.google.com/youtube/answer/2802032): "You're prohibited from using, creating, or acquiring
  another channel to get around these restrictions" — e a punição "may result in termination of all your existing
  YouTube channels". Isto é, o risco não é só o Manhwa Noturno: são **todos** os canais do dono.
- Proposta: parar The Inheritor no Manhwa Noturno pelo menos até o fim do congelamento (~23/10), e não repostar ali
  os vídeos que já estavam no canal advertido; tirar do `youtube_navegador.json` a nota "substitui...". Depois do
  congelamento, o Manhwa Noturno pode seguir com conteúdo próprio (vídeo novo, não cópia do canal advertido).
  **Decisão do dono** (bate com a regra "nunca sem postagem": o canal pode continuar com shorts de outro tipo).
- Mesma lógica para o english ("Muitos avisos", envio bloqueado): não mover o conteúdo dele para outro canal.

### F6 — metadados repetidos (19/10)
Fonte: `_analise/metricas_studio.json` (103 vídeos) + títulos dos logs `manhwa-react/logs/rede_2026101[678].log` +
oEmbed público de 2 vídeos do hipercool.
- Formato único em toda a rede: 94 de 103 títulos terminam em `#shorts #<1 tag>` e quase todos têm 😱/🔥. Vem da
  regra do agente (`mr/rede.py:431-451`). Sozinho não derruba, mas é a "impressão digital" de rede.
- **Frase-molde copiada do exemplo do prompt**: a estratégia "curiosidade" traz o exemplo literal
  `('ninguem reparou nesse detalhe...')` e "opiniao" traz `('essa e a cena mais triste de...')` (`rede.py:453-454`).
  Resultado: "Ninguém reparou…" abre 9 dos 103 títulos medidos, em 7 canais (manhwareact, dicasfinanceiras ×2,
  mundoquenaoexiste ×2, inovare_ita, inovare_hindi, inovaremanhwabr, inovare_ind). Proposta:
  tirar os exemplos literais e o revisor recusar título que comece com as mesmas 3 palavras de um título da rede
  nos últimos 7 dias.
- **Brecha no revisor do nome da obra** (`rede.py:653-656`): compara com espaço (`"garota exemplar" in txt`), então a
  obra em hashtag passa: `#garotaexemplar`, `#mushokutensei`, `#dragonball`, `#blackclover`, `#rezero`, `#tensura`,
  `#maougakuin` estão em títulos medidos (a maioria de antes da regra de 15/10, mas a brecha continua no código).
  Conserto: comparar só letras/números (tirar espaço e pontuação dos dois lados).
- **Mesmo tema repetido no mesmo canal**: InventoReact publicou "IA que vende no WhatsApp" 4 vezes em 3 dias
  (16/10 20:25, 16/10 22:25, 17/10 10:00, 18/10 09:15 — todos "vaga do Veo"). Tema de produto do dono repetido é
  o que o YouTube chama de spam/conteúdo repetitivo — foi o perfil dos 22 canais de IA suspensos. Proposta: no
  máximo 1 vídeo do mesmo tema por canal por semana (o revisor compara com os títulos recentes do canal).
- **Vídeo fora do nicho com hashtag do nicho**: ManhwaReact recebeu vídeos do Veo de robô/IA/ET marcados `#anime`
  ("Esse robô quis imitar humano e deu MUITO errado 🤖😂 #shorts #anime", "AVANÇO GIGANTE na IA está chegando").
  Hashtag que não corresponde ao vídeo é "metadado enganoso" nas regras de spam. A conferir assistindo; se o vídeo
  não for anime, a vaga do Veo não deveria cair num canal de manhwa (e a mediana do ManhwaReact é 2 views).
- Hipercool: títulos publicados estão certos (oEmbed: "O SEGREDO DA HERANÇA 🔥 Cap. 1 | Parte 2/5 #manhwa #recap");
  o nome de arquivo que aparece no `metricas_studio.json` é falha da medição (ver F8).

### F7 — alavancas legítimas de crescimento (19/10)
Já existe (tudo pelo próprio canal, sem risco):
- comentário do próprio canal no próprio vídeo, fixado (`youtube_studio_extras.comentar_fixar`, rede e hipercool);
- "vídeo relacionado" do Short apontando para o completo (`extras_rede.py:81`, `postar_hipercool.py:499`);
- tela final "1 vídeo + 1 playlist" no completo e playlist fixa dos completos (`rede.py:583`, 18/10);
- teste A/B de capas no completo/longo (`youtube_studio_extras.teste_ab`);
- estratégia de título/gancho/comentário escolhida pelos números (`metricas_rede.py:230`);
- compilado longo no hipercool (o formato que estoura no Porão Manhwa).

Travado por ação do dono: "vídeo relacionado", fixar comentário e A/B exigem o canal **verificado por telefone**
(`extras_rede.json`: "fixar libera depois da verificação" no inovare_ind e no IA Agora). Verificar os canais que
faltam libera essas três coisas de uma vez. (O YouTube limita quantos canais um mesmo número verifica por ano.)

Falta:
1. **Responder e dar coração nos comentários de quem assiste** — não existe em nenhum projeto. É o sinal de
   engajamento verdadeiro (gente de fora) e o canal respondendo no próprio vídeo é permitido. Sugestão segura:
   coração em todo comentário novo e resposta curta em poucos por dia, pelo Studio do próprio canal; nunca em vídeo
   de outro canal da rede.
2. **Concentrar em vez de espalhar.** Nos 103 vídeos medidos, quem passa de 1.000 views é pouca coisa e sempre o
   mesmo tipo: react de filme/série (CenaReact "Garota Exemplar" 1.226 e 1.353), drama animado (HistoriasEmFrames
   1.202), luta de anime (inovare_hindi 1.278), opinião sobre manhwa (inovaremanhwabr 1.211). ManhwaReact tem
   mediana 2 views em 16 vídeos; Manhwa Noturno 1–2. Menos uploads nos canais mortos e mais no formato que funciona
   = mais views e menos "volume de rede" (F2).
3. **Postagens na aba Comunidade/Posts** (enquete "qual parte vocês querem?") — não existe. Só se o canal tiver a aba.
4. **Comentário "Comenta SEM CENSURA"** (`postar_hipercool.py:61`, fixado nos vídeos com censura do pt): pede
   comentário em troca de conteúdo e anuncia versão explícita — num canal que já levou advertência por nudez, chama
   atenção para o lado sexual. Proposta: trocar por pergunta sobre a história (como a rede faz).

### F8 — medição (19/10)
Fontes: placar `_analise/aprendizado_global.json` (views na API em 48 h, `notificar_telegram.medir_48h`),
`config/telegram_estado.json` (`medidas_48h`, 102 vídeos) e `_analise/metricas_studio.json` (Studio, 103 vídeos).
- **40 dos 102 vídeos medidos tinham 0 view com 48 h de público. 27 deles são recap do hipercool nos canais de
  outra língua**: inovare_hindi 8/10, inovare_ita 5/6, inovare_ind 4/6, inovare_thai 4/4, inovare_ru 4/6. Short
  público sem nenhuma view em 2 dias quer dizer que o YouTube não está mostrando — o mais provável é restrição de
  idade (conteúdo adulto não entra no feed de Shorts) ou canal limitado. **Conferir no Studio** a coluna
  "Restrições" desses vídeos. Se for isso, espalhar o hipercool nessas línguas dá zero retorno e só soma risco
  (F3/F4/F5). Proposta: parar o hipercool nas línguas que deram 0 até ver o motivo; a regra "nunca sem postagem"
  continua valendo com outro conteúdo.
- Os ~1.200 views que se repetem em vários canais (1.204, 1.211, 1.217…) são reais (API) — é o lote de teste que o
  YouTube dá a um Short; quem não segura a retenção para aí. Não é erro de leitura.
- **Studio**: 45 de 103 leituras deram erro ("nenhuma métrica achada"); CTR e impressões nunca foram lidos (0/103);
  "continuaram" só em 13. Com isso o aprendizado de gancho tem pouca amostra e o de título só vale para vídeo
  longo (`metricas_rede.py:225`), que quase não há.
- **Hipercool medido sem título nem estratégia**: `metricas_rede.py:126` usa o nome do arquivo como título para
  quem não está no registro da rede (é o `the-inheritor_cap1_parte02.mp4` da F6). Não dá para aprender qual título
  do hipercool funciona. O título real está no estado do `postar_hipercool`.
- 41 dos 102 vídeos estão como origem "sem registro" (ledger de antes de 18/10 sem projeto/tipo). Desde 18/10 o
  ledger grava projeto/tipo, então isso some sozinho em 30 dias.
- **Shorts de parceiro ainda não têm medida** (começaram 17–18/10; a 1ª leitura de 48 h sai a partir de 19–20/10).
  Antes de manter 60 uploads/dia, olhar esse número.

