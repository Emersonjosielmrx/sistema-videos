# Vídeos e fotos PROFISSIONAIS de produto + melhorias na busca/gestão de fotos (25/10)

Pedido do dono (25/10, 07:00): "faça todas as melhorias possíveis no nosso sistema de busca de fotos e gerenciamento
disso pra postagem; ele tem que criar vídeos e fotos desse material usando projetos como cortes e Veo para produzir
vídeos, narrações etc., focados não no entretenimento e sim nos PRODUTOS, de maneira profissional, passando confiança.
O foco é diferente do entretenimento do YouTube; os agentes têm que ser diferentes, aproveitando o máximo de efeitos."

Regras que valem aqui:
- Opus = sem Agent/Workflow (memória project_trocador_subagentes: 4 falhas, a última com o dono chamando o skill).
- Base = pipeline do MS Energy (D:\ms-energy\bin: roteiro_ms, video_real_ms, montagem_ms, qa_ms, gerar_short_veo):
  propaganda honesta (sem número/preço/prazo inventado, sem "garantir", sem "zerar", sem concessionária/concorrente),
  acentuação certa, revisor, trava final; NÃO usar agents.py/montar_final do Veo de memes.
- Aprendizado (feedback_aprendizado_parceiros): aplicados aqui, para marcar no fim:
  karaokê na cor da marca (ffb4c8fe, 62c7ec8c, e4fbdf10) · frase fixa no topo (9a1f9f1f, 8d5ffe30) ·
  tópicos numerados (82b76de6) · cartão de pergunta do cliente como gancho (c9627e2c) ·
  "recorte de interface" = conversa de WhatsApp animada mostrando o produto (8ebdb5ea) ·
  fundo desfocado do próprio vídeo (f8637eae, já em pastas_empresas 24/10).
- Contas de produto: inovarecom.ia = Hermes Call, futebolcom.ia2 = Cardápio Digital, sintetizerisada = Agenda IA
  (config\marcas_instagram.json). MS Energy segue no pipeline próprio (só ganha os clipes automáticos e a busca melhor).

## Arquitetura (D:\postador-de-videos\bin\produto\)
- `kit.py` — kit da marca: cores, nome, fatos permitidos do produto (produtos.json), narrador, hashtags, regras.
- `agentes.py` — agentes PROFISSIONAIS (diferentes dos de entretenimento): estrategista (banco de pautas por produto:
  dor, objeção, como funciona, caso de uso, pergunta frequente), roteirista (gancho + 3 blocos + chamada), diretor de
  arte (plano visual: imagem do Flow / conversa animada / Veo / material real), revisor de conformidade.
- `chat_ui.py` — conversa de WhatsApp animada (balões, "digitando…", horário, selo "simulação") na cor da marca.
- `video.py` — montagem: Ken Burns/parallax nas imagens, conversa animada, clipe do Veo (cena comercial sem fala),
  narração (edge-tts com tempo de cada palavra), legenda karaokê na cor da marca, frase fixa no topo, tópicos
  numerados, transições suaves, trilha livre baixinha, cartão final da marca, −14 LUFS, trava final por visão.
- `fila.py` — fila por conta (D:\video-fila\produto_fila\<conta>\) + entrega ao postar_insta_auto.
- `biblioteca.py` — material real por marca (Google Fotos, pasta da empresa, Instagram): índice único, uso/rodízio,
  CORTES automáticos dos vídeos (cenas → quadro checado por visão → trechos aprovados) → clipes do video_real.

## Frentes
1. [x] kit.py + agentes.py — roteiros aprovados p/ Cardápio e Agenda IA (revisor barrou "500ml", "até 3 adicionais";
       horário de exemplo na conversa liberado; "Perfeito!" liberado; revisor tenta 3x antes de desistir)
2. [x] chat_ui.py — print ok (tiques desenhados; balão antigo some sob o cabeçalho em vez de cobrir a resposta)
3. [~] video.py — 2 testes completos (Cardápio 25 s, Agenda IA 29 s). Correções: tópico abaixo da frase do topo,
       imagem só reprova texto EM DESTAQUE, banco de imagens por marca (produto_banco), trava final sabe o que é do
       desenho e confere 2x o quadro acusado. FALTA: 1 vídeo aprovado de ponta a ponta com o código novo.
3b. [x] 25/10 11:14 Hermes Call aprovado de ponta a ponta (28,5 s) + carrossel do mesmo roteiro; vídeo na fila
       produto_fila\inovarecom.ia. Aprendizado marcado aplicado (9 ids).
4. [ ] Veo no vídeo de produto: no teste o roteirista não escolheu "veo" (era opcional) -> agora obrigatório em 1
       bloco quando com_veo. FALTA ver 1 vídeo com a cena do Veo (Produto_Videos alterna dias com Veo).
5. [x] fila (produto\fila.py) + postar_insta_auto (empresa → produto → Veo) + tarefa Produto_Videos 04:41/13:41
6. [~] cortes_ms.py rodando nos 212 vídeos (triagem descarta animação/anúncio; 3 quadros por trecho). Backup do
       clipes.json em clipes.json.bak_20261025_antes_cortes
7. [x] busca: 1 processo por conta com prazo de 45 min + mata o Chrome da conta; espera memória; retomada por
       conta+termo (progresso_busca.json, 14 dias; semeado do log de 24/10); quase-duplicadas (dHash ≤ 6 bits); vídeo
       > 150 MB pulado; índice gravado a cada 10; classificação 4 em paralelo (4.600 fotos: 2h40 → minutos); Drive
       por último. Teste 25/10: só fez os 3 termos que faltavam (+141 fotos).
8. [x] carrossel do MESMO roteiro do vídeo (produto\carrossel.py) + gancho no carrossel_marca.gerar (posta o de
       produto primeiro). Corrigido: log do carrossel_marca derrubava a tarefa (PermissionError) — rodada de hoje
       refeita às 08:06.
9. [x] aprendizado: os 9 ids estão "aplicado" no acervo (conferido 26/10); memória atualizada 26/10

## Dono como personagem (25/10 17h)
Dono: "todos os produtos têm que usar EU como personagem nos vídeos do Veo 3; avatar Veo3 com base nas minhas fotos;
carrosséis também"; vale para produto E MS Energy (troca a regra de 22/10). Fotos-base: D:\fotos para videos\fotos\
fotos base...\sem fundo retrato (a pasta "imagem base inovare frente" tem telefone: nunca). Ferramenta já existente:
D:\veo\beta\foto_na_hora.py (foto dele no cenário pelo Flow + revisor de rosto SFace; revisar_video no vídeo pronto).
1. [x] agentes: com Veo, bloco 1 = "apresentador" (fala 10–18 palavras + cenario_en)
2. [x] video.py: apresentador() = foto_na_hora.gerar -> Veo (1º quadro) -> revisar_video -> voz do próprio vídeo +
       Whisper alinhado ao texto (legenda karaokê); falhou = bloco vira imagem + narradora
3. [x] teste real (futebolcom.ia2 --veo) — ver item 7 (teste7, dono aprovou)
4. [~] capa do carrossel com o dono: carrossel.do_roteiro usa b["foto_dono"] do bloco 1; conferir no carrossel do
       teste misto. 26/10: teste com saida_dir fora da fila põe o carrossel na MESMA pasta de teste.
5. [x] MS Energy: apresentador = dono (roteiro_ms._clone cai no dono; formato misto no produto\video.py, item 8)
6. [x] Produto_Videos: todo vídeo com o dono
7. [x] 25/10 18:24 PRIMEIRO vídeo com o dono (Cardápio, teste7): foto no cenário aprovada, Veo 8 s com áudio, rosto no
       vídeo 0,60/0,53/0,62. Dono: "agora sim". (Whisper falhou -> legenda pelo texto; ver por quê)
8. [ ] dono 25/10: "complementar: uma parte Veo (ele) e outra como o vídeo anterior, com imagens de INSTALAÇÕES e a
       IA falando" -> formato no MS Energy: bloco 1 = dono no Veo (clone/foto_na_hora), blocos 2-3 = clipes reais
       (clipes.json) / fotos aprovadas + narradora Thalita + karaokê, cartão MS Energy. Fazer como visual "real" no
       produto\video.py (kit msenergysolar.pa) ou no video_real_ms (prefixo do dono).
       -> 25/10 22h FEITO no produto\video.py: kit msenergysolar.pa (cliente: fatos do roteiro_ms, "orçamento grátis"
          permitido, concessionária barrada, @msenergycap, Thalita), visual "real" (seg_real: trecho do clipes.json do
          tema, rodízio em config\produto_reais_uso.json; senão foto aprovada). Roteiro de teste aprovado (dono + usina
          + drone). Teste completo em D:\ms-energy\_diag\teste_misto (NÃO entra na fila até o dono aprovar).
9. [x] variações + agente (produto\variacoes.py, Thompson pelas views; mede antes de cada produção)
10. [x] correções 25/10 noite: gera_imagem passa FLOW_PROFILE da conta (abria Chrome com a pasta de outra);
        gerar_short_veo trata "SO_NOTEBOOK" como máquina ocupada (troca de conta sem castigo); _clone do MS Energy e
        apresentador() esperam conta livre (3x 4 min) e reusam foto já aprovada; Whisper tenta 2x.
11. [ ] dono aprovar o 1º vídeo misto do MS Energy -> aí incluir msenergysolar.pa na produção diária

## Melhoria contínua + verificadores Gemini (26/10 05h, dono)
Dono: "a cada vídeo você analisa o que pode melhorar e vai fazendo; integre o sistema do D:\claude-code-video (multi
agentes Gemini) que edita e melhora os vídeos; não são só testes, já faça vídeos reais que vamos usar".
- `produto\motor.py` = cópia do motor de lá (claude.exe -p pelo OmniRoute, modelo agy/gemini-3.8-flash-high, só Read);
  config `config\produto_lapidar.json` (ligado, modelo, reprovar_abaixo 4,5).
- `produto\lapidar.py` = os 4 verificadores de lá (legibilidade, movimento, roteiro_marca, diretor) em paralelo,
  3 quadros por cena + folha; sabem o que é do nosso desenho (topo, tópico, karaokê, "Simulação", @, dono).
  Lá o corretor edita o código Remotion do vídeo; aqui a montagem é Python/ffmpeg, então: nota < 4,5 ou grave de
  roteiro_marca -> _revisar; o resto vai pra fila (vídeo REAL) e os problemas ficam em logs\produto_lapidar.jsonl.
  `python -m produto.lapidar` = resumo dos problemas que se repetem -> a cada rodada (crons 5h–12h) consertar no código.
- video.py grava `cenas` (ini/fim/fala/tipo) no .json e chama lapidar.verificar depois da trava final.
- Veo do dono: "sem conta livre" também espera (2 min, prazo 1 h) e solta o VEO_SO_NOTEBOOK para tentar o PC1.

### EDITOR Gemini em Remotion (26/10 08:40, dono: "o outro agente atualizou a dele e melhorou muito, atualize a sua")
Lá (D:\claude-code-video): o Gemini ESCREVE a edição em Remotion, olha os quadros, e o corretor refaz até 6 rodadas
(Cardápio 5,62 -> 7,62; roteiro/marca 7 -> 10). Trazido para cá:
- `remotion\` (package.json/config copiados; node_modules = junção para o de lá) + `remotion\EDITOR.md` = regras de
  lá ("Aprendido dos verificadores": gancho 0–2 s, nada parado > 1,5 s, variar layout, rosto livre, letra ≥ 32 px,
  karaokê pela base, botão = ação da fala, cartão com foto, 2 camadas de leitura, selos só com fatos) + o nosso
  material: cena `dono` (vídeo dele mudo, voz já na narração, rosto nunca coberto), `real` (instalação real do
  MS Energy como prova), `conversa` (mensagens prontas), `veo`; tempo das cenas FIXO.
- `produto\editor.py`: depois do molde + nota, monta a pasta pública (narracao.mp3 com TODA a voz no tempo, trilha,
  fotos, vídeos das cenas, briefing.json), editor Gemini (90 turnos, aceita limite), render, 4 verificadores, corretor
  (fatos + "não estrague" + graves da rodada anterior), até 4 rodadas, para se 2 não superam; fica a de MAIOR nota
  (editor x molde). Config `produto_lapidar.json` -> editor (por_rodada 2: cada um ~1–3 h). motor.py com EDITOR e
  aceitar_limite (como o de lá). Diário: trava velha 3 h -> 10 h.
- Voz: a Thalita (multilíngue) falhou AO ACASO em várias frases (teste 08:40: mesmas frases X/ok); Francisca 8/8 ok.
  Agora: falhou com a voz da marca -> o vídeo TODO é narrado de novo com a Francisca (nunca 2 vozes).
- 1º vídeo real com o editor: disparoemmassa.ia (logs\produto_editor_teste.log), vai pra fila.

### Rodadas de melhoria (nota dos verificadores por vídeo -> o que mudou no código)
| quando | vídeo | nota | problema que se repete | conserto |
|---|---|---|---|---|
| 26/10 05:15 | futebolcom_ia2_20261025_180528 (Cardápio c/ dono, já na fila; cenas divididas por tempo só no teste) | 4,67 (leg 6, mov 4, rot 4; diretor caiu "None None") | legenda emendava falas ("monta tudo A", "lanchonete Chame a") e aparecia sobre o cartão final; nome da marca vermelho sobre fundo vinho ilegível; conversa com 2 balões juntos e >2 s parada | legenda agrupada POR FALA e sem legenda no cartão; nome do cartão branco se a cor é escura (print ok); verificador tenta 2x; "grave" de roteiro_marca só segura se for inventado/português (resto vira melhoria). ritmo da conversa: 05:20 chat_ui espalha as mensagens até ~1,6 s do fim (antes só comprimia; com folga acabava cedo) — print 1 quadro/s ok |
| 26/10 10:10 | disparoemmassa_ia (molde 5,75; editor r1 6,0) | mov 4 nos dois; diretor 5–6 | foto parada ("banco de imagem", >4 s sem mudar); botão "Link no perfil" x voz "chame no direct"; gancho = pergunta técnica ("Como eu configuro..."); contas novas sem hashtag/público | Ken Burns 10%->16% e deslize 2x; convite dos produtos = "Chame no direct" (linha de baixo "Link no perfil"; legenda do post sem repetir) — print ok; roteirista: pergunta de abertura = DOR/desejo, nunca "como configuro"; kit: público + 5 hashtags p/ disparo, follow-up, VPS, fábrica |
| 26/10 14:00 | followupia (molde 5,75: leg 7, mov 5 (era 4), rot 7, dir 4) | diretor 4 | abertura = card sobre fundo escuro vazio ("slide de Canva, sem rosto"); botão branco sobre turquesa (~1,5:1); conversa pequena com 60% vazio; troca de camisa entre as 2 cenas do dono (variação abre_fecha — o Thompson decide) | abertura com a FOTO DO DONO (pouco desfocada) e a pergunta no alto (print 3 fotos ok); kit: texto escuro quando a cor da marca é clara (print ok); chat_ui letras 42->52 e cabeçalho maior (print ok) |
| 26/10 11:15 | disparoemmassa (editor, ficou 6,0) | — | corretor r3 caiu: "exceeded 32000 output tokens" (reescreve o Video.tsx inteiro); a versão escolhida tinha "Envio 100% Automático em Minutos" e "100% Livre" (verificadores deram só "média") -> vídeo TIRADO da fila (_revisar), carrossel (do roteiro) ok | motor: CLAUDE_CODE_MAX_OUTPUT_TOKENS 64000; EDITOR.md: corrigir com Edit, cenas em arquivos; editor.problemas_texto(): lê os textos da tela no .tsx (porcentagem, preço, prazo, número, garantia, grátis, concorrente...) -> versão com texto proibido não é escolhida e vira "grave" pro corretor (testado no .tsx real: pegou os 2, sem alarme falso); molde guardado em produto_fila\_molde antes de trocar |
| 26/10 11:05 | disparoemmassa (EDITOR r1 6,0 · r2 6,0) | mov 4–5, diretor 5 | editor escreveu na tela frase ≠ da fala (abertura); 3 passos anunciados e pulou do 1 pro 3; tudo entra nos primeiros 40% e depois congela; mesmo layout em todas; "em minutos" inventado; palavra órfã | EDITOR.md "Aprendido aqui": tela = fala do momento (pergunta = fala), passos acendem 1 a 1 na fala, movimento a cena inteira, layout por tipo de cena, textWrap balance, escala sem número, nada de prazo, cartão sempre vivo (vale da r3 em diante) |

## Diário
- 26/10 03:05 — teste misto (teste2) gerou o clipe do dono no Veo (emersonjosiel0, 8 s com áudio) mas caiu no log do
  gerar_short_veo: ffprobe devolveu None (RAM baixa) e `{dur:.1f}` estourou. Corrigido (duração "?" no log). Teste
  refeito do zero (teste3.log; roteiro novo, então o clipe antigo não serve). x200ma: Tailscale SSH em modo "check"
  pede confirmação no navegador — depende do dono (link ou ACL "accept"). [CORREÇÃO 03:20: o sistema usa a 2222
  (sshd), que funciona; o "nada visível" é porque o Chrome da conta só abre na tela durante cada tarefa.]
- 26/10 03:11 foto nova do dono aprovada (nota 0,71). Veo: tentativa 1 (inovaremultiatendimento, notebook) falhou no
  Flow ("texto não entrou na caixa"), 2 = notebooks ocupados, 3 = PC1 pausado -> acabaram as 3 sem falha real e o
  bloco do dono virou imagem. CORRIGIDO no clipe_veo: ocupado/pausado espera (60 s / 2 min) e NÃO conta tentativa nem
  castiga a conta (antes MAQUINA_OCUPADA caía no registrar_falha_sessao); prazo total 1 h. teste3 segue sem o dono
  (serve para conferir instalações reais + karaokê + carrossel); refazer o misto depois do Produto_Videos das 04:41.
- 26/10 08h — PRODUÇÃO 04:41 (código antigo, sem verificadores): 4 vídeos REAIS na fila + 4 carrosséis.
  Hermes Call (dono_uma_cena) e Cardápio (dono_uma_cena): foto do dono ok mas Veo sem conta (PC1 pausado + notebooks
  ocupados) -> sem o dono no vídeo (capa do carrossel COM o dono); Agenda IA = sem_dono; Fábrica de Conteúdo =
  dono_mesma_foto com o dono nas cenas 1 e 3 (rosto 0,61–0,68), print ok. Disparo, Follow-up e VPS: edge-tts
  "NoAudioReceived" 06:15–06:27 (3 tentativas em 6 s) -> CORRIGIDO: 5 tentativas com espera 15/30/60/120 s.
  teste3 do MS Energy: encode final "medium" estourou 30 min com o PC cheio -> arquivo quebrado; CORRIGIDO: preset
  "fast" crf 18, prazo 1 h. Teste refeito (teste4.log, python -u).
- 26/10 08h — nome sem acento no cartão/voz ("Fabrica de Conteudo"): produtos.json do Veo é compartilhado ->
  corrigido só no kit.py (ACENTO: Fábrica de Conteúdo, Recuperação de Carrinho, Comunicação, Gestão).
- 26/10 08h — carrossel 07:13: inovarecom.ia e videocassetadascom.ia falharam (token da API venceu 24/10). Os perfis
  ig_<conta> do cofre estão logados (instagram_local 03h) -> postar_insta_auto.cofre_logado(): token vencido +
  perfil logado = posta pelo navegador (vídeo e carrossel). Os 2 carrosséis publicados às 08:15/08:17.
- 26/10 09h — Disparo em Massa (1º real com editor): foto do dono ok (0,74), mas o Veo falhou 3x DE VERDADE:
  inovaremultiatendimento (acer, Atom) "texto não entrou na caixa" pela 2ª vez hoje -> CORRIGIDO no
  D:\veo\beta\gera_auto.py: confere a caixa por até 20 s (a digitação no Atom demora); emersonjosiel2026 e
  inovaremanhwaverse DESLOGADAS do Flow (exit 3, fora do rodízio até 15h) -> dono precisa logar de novo.
  Thalita falhou de novo -> vídeo todo com a Francisca (funcionou). Molde nota 5,75 (4 verificadores ok); editor
  começou 09:23.
- 26/10 10:20 — dono: "pode ir fazendo e postando já nos novos instagrams". Os 4 novos (disparoemmassa, followupia,
  vpsblindada, fabricademarketing) estão logados no Chrome do PC1 (cofre ig_*). Postado agora: fabricademarketing
  (vídeo com o dono, 10:21, navegador). Disparo entra na fila quando o editor terminar; depois disso um processo
  separado faz Follow-up e VPS (logs\produto_contas_novas.log). As rodadas do Instagram 14:05/19:35 postam a fila
  de produto (empresa → produto → Veo).
- 26/10 13h — os "esperadores" em PowerShell (-Command) morreram sem rodar (aspas); trocado por
  D:\video-fila\produto_tmp\fila_contas_novas.ps1: Follow-up -> VPS -> teste misto do MS Energy (teste5.log).
  Follow-up começou 13:04. Crons: de hora em hora (:17) por 48 h + um às 28/10 12:25 que apaga o de hora em hora.
  O Produto_Videos das 13:41 sai sozinho se a trava (.rodando) estiver ocupada — normal.
- 26/10 13:30 — dono: "formatos diferentes, com 2 Veo3, 3 Veo3 e assim por diante": variacoes.VARIANTES agora tem
  0/1/2/3 Veo — dono_uma_cena (1), dono_abre_fecha e dono_mesma_foto (2), dono_e_cena_veo (dono no 1 + cena
  comercial do Veo no 3), dono_tres (dono nos 3 blocos), dono_abre_fecha_veo_meio (dono 1 e 3 + Veo no 2), sem_dono.
  agentes aceita `broll` (blocos "veo" sem o dono; "conversa" só é exigida se sobra bloco livre); video.py grava
  veo_broll_feitos; variante_real reconhece todas. O Thompson experimenta todas e puxa a que dá mais views.
- 26/10 13:30 — dono: "o claude code video com Gemini, limpo, já fez alguns — confira e poste nos novos":
  produto\fila.itens_ccv() põe na fila de postagem os vídeos de D:\claude-code-video\saida\<conta> que PASSAM na
  trava de texto (editor.problemas_texto no código Remotion deles); postado = _ccv_postados.json (não mexe nos
  arquivos de lá). Hoje: Disparo (ccv, nota 6,55) BARRADO ("Entrega: 99.4%", "Faltam mais 998 contatos"),
  Cardápio 005145 barrado ("24 min sem resposta", "100% com IA", "#142"); passam Cardápio 013422 e Hermes 230205
  (entram na rodada 14:05). Contas novas (4 de 25/10; hoje o criador falhou 2x no CRM Chatwoot): nenhum vídeo
  limpo do ccv ainda. FALTA: a trava de texto não existe no D:\claude-code-video (o outro agente deveria pôr).
- 26/10 14:15 — Follow-up: molde 5,75 com o dono (rosto 0,60–0,63); editor caiu aos 20 min com
  "[claude-code:unrecognized_model] agy/gemini-3.8-flash-high" (passageiro: às 14:10 os 3 modelos respondiam) ->
  ficou o molde; POSTADO 14:13 (navegador). editor.py agora tenta o modelo_reserva (agy/gemini-3.8-flash-tiered)
  continuando o Video.tsx. VPS começou 14:09 (gancho novo: "Seu sistema travou sem avisar?").
- 26/10 15:10 — VPS: dono aprovado 14:38 (0,66–0,68). Padrão do dia: o ACER (Atom, "lento") falha na tela do Flow
  (painel de ajustes, envio da imagem, "texto não entrou" mesmo com a espera de 20 s) — já é o último da fila das
  máquinas; contas só dele custam tentativas. PENDENTE: medir sucesso/falha por máquina antes de mexer nos tempos do
  gera_auto (compartilhado com o Veo). O Produto_Videos das 13:41 saiu por causa da trava (esperado).
- 26/10 16:25 — VPS (variação dono_tres = 3 Veo) fez as 3 cenas do dono (rosto ok) e caiu às 15:16 no ffmpeg
  "Cannot allocate memory" (PC1 sem RAM) -> as 3 cenas perdidas. CORRIGIDO: video._ff espera 60/120/180 s e tenta
  de novo quando é falta de memória. VPS refeito depois do teste do MS Energy (fila_vps_de_novo.ps1). Teste misto do
  MS Energy (teste5.log) rodando desde 15:17.
- 26/10 17:00 — teste misto do MS Energy (teste5): roteiro levou 38 min (LLM lento); a foto travou 20 min sem saída
  depois de "[img] arquivo enviado" no Chrome remoto (item.count() sem prazo com o túnel caído). Encerrado (processo
  meu). CORRIGIDO no apresentador(): a foto roda numa thread daemon com prazo de 20 min; estourou = foto já
  aprovada. Fila agora: VPS (começou 16:56) -> teste do MS Energy (fila_ms_teste.ps1, teste6.log).
- 26/10 08h — capa do carrossel com o dono: o texto cobria boca/queixo -> foto sobe (centering 0,8) e pergunta em até
  4 linhas (print com 3 fotos ok).
