# CORTES — ESTADO (linha dos Shorts de parceiro; sessão dona desde 26/10/2026 19h)

Prompt: D:\video-fila\linhas\PROMPT_LINHAS.md (cartão CORTES). claude-code-video: lendo v1.1 (aplicada: nada ainda).
Objetivo do dono (26/10): MÁXIMO de viralização/views. Vídeo pronto pra ele ver (27/10 mudou de lugar, ele não
achava): D:\hipercool-materiais\CORTES_ULTIMO_VIDEO\ (atalho "CORTES - ultimo video" na Área de Trabalho):
ultimo/anterior_1/anterior_2.mp4 + testes\ (TODO teste da sessão vai pra lá também) + OPINIOES.txt — LER todo ciclo.

## Frentes (ordem = impacto/risco; [x] = feito com prova; marcar hora)
!! [x 18:20] PC2 C: cheio (0 bytes 15:30) -> 21 GB livres. Causa: LONGOS reenvia o mesmo longo a cada ~2 h (MURAL).
   Pronto foi pro Drive (videos-backup/recap-longos-pc2); faxina.regra_pc2 manda final parado 6 h+ pro Drive; rclone
   no PC2 (C:\hipercool-materiais\tools). anime_script/anime_auto sincronizados. fx_music.py (trilha) = outro chat.
M2. [x 21:00] MÁQUINAS NO MÁXIMO (DECISOES 21:00): PC2 até 3 Shorts juntos; desktop automático se livre.
   CONFERIR amanhã: Shorts/dia do PC2 (hoje 4) e do desktop (hoje 0) + MAQUINAS_24H.md da PRODUTOS (08:05).
   Postagem TikTok: 52/59 contas logadas no PC2, ordem já é notebooks -> PC2 -> PC1, mas só 2 posts juntos (1 navegador
   por máquina no agente do postador) — PC2 com vários Chrome juntos = mudança no maquina_remota (linha do postador).
G. [x 20:20] AGENTE substituto construído (DECISOES 20:20) — NÃO LIGAR até a dona mandar. Falta: ela passar o
   modelo de código (agente.json "modelo"); depois ligar = ligado=true + Enable-ScheduledTask Cortes_Agente.
A. [x 21:55] ARGON NO TEXTO DO VÍDEO (dona mandou; DECISOES 12:45). MEDIDO e TABELADO em COMPARACAO_MODELOS.md:
   30 roteiros Argon OK (meta era 6). 85 chamadas Argon no dia: 78 ok (92%), 7 falhas (timeout/502) → fallback Gemini.
   Mediana Argon 20 s vs Gemini 7 s (+13 s por chamada, ~5% do pipeline — desprezível). Gemini 0 falhas.
   Falta: júri Argon vs Gemini (nota/história/retenção) quando houver >= 6 Shorts julgados; views 48 h.
P. [x 27/10 04:30] PAINEL "só 3 postagens ontem": o Instagram pelo navegador grava id "navegador" e o _postagens
   deduplicava por (plataforma, id) -> 36 posts viravam 1-3. Corrigido (painel_controlador.py) + erro de recálculo
   do cache agora vai pra logs\painel_erros.log (antes era engolido). Painel reiniciado; 26/10 = YT 44, IG 36, TT 71.
L. [~ 27/10 08:40] LEGENDA (dono 27/10): a barra preta só pra coisas muito específicas; quer palavras maiores, algumas MUITO
   maiores e até de lado na tela (efeito de impacto), fontes diferentes e cor por personagem.
   ACHADO 07:40: ênfase (palavra 1,3x) e impacto (palavra enorme ~1 s no centro, máx 2/vídeo a cada 8 s) JÁ existem
   em fx_subtitles, mas só ligam com "falantes" = formato de 2+ vozes (anime_formatos.falantes_legenda) — o Short
   SOLO (a maioria) não tem nenhum.
   [x 08:40] PASSO 1: anime_formatos.enfase_solo (cor amarela, sem nome) + anime_segments chama no vertical solo.
     Testado: 5 frases, ênfase e impacto selecionados corretamente. PC2 sync.
     [x 10:30] PRODUÇÃO REAL: sem-obra-cb6037 (09:23) = impacto "APROVEITOU" enorme no centro ~51 s + ênfase
     "aproveitou" maior na legenda (testes\cb6037_impacto.png). Só 1 impacto em 80 s (máx 2/8 s) — ok.
   [x 12:10] PASSO 2 = T3 ligado (TESTES.md): metade dos Shorts com impacto inclinado de lado (Bangers/LuckiestGuy).
   CONFERIR quadros do 1º Short "lateral" + medir views. FALTA: cor por personagem (só formatos 2+ vozes).
   PLANO T3 (original): (2) impacto LATERAL: \frz -8..-12 e posição esquerda/direita alternando, fonte de impacto
   (Bangers/LuckiestGuy no ASS) — variante B; (3) cor por personagem: só onde há falantes (formatos) por enquanto.
   A/B por sorteio fixo, gravar "legenda_estilo" no postar.json. Barra preta do produto -> trocar pelo estilo normal.
T. [~] TARJA/APAGADO EXATO (dono 27/10): tarja e delogo cobrindo SÓ a área da legenda (o delogo dos longos é tão
   sutil que quase não se vê) + nossa legenda em cima. [x 06:20] caixa justa + margens mínimas; T2 ligado (TESTES).
   [x 11:40] 1º Shorts reais com delogo: f4be19 limpo; de73a8 deixava a 2ª linha deles -> caixa cresce pra baixo e
   pros lados (DECISOES 11:40). Medir views T2 quando houver >= 6 por versão.
   [x 11:50] gancho em cima do título fixo da fonte -> topo_fixo + GANCHO_Y (DECISOES). INSCREVA-SE = da fonte.
   CONFERIR no 1º Short de fonte com título fixo no alto (Grana Nerd/assistiainvestimentos).
M. [ ] MELHORADOR DOS CORTES (dono 26/10 23:50): cópia do sistema de melhorias contínuas (melhoria_continua.py,
   hoje PARADO) só pros Shorts, com o objetivo de fazer o que esta sessão faz: ver o vídeo feito -> escolher 1
   melhoria -> testar -> documentar -> próximo melhor/mais viral. CONSTRUIR AGORA mas NÃO LIGAR (só no sinal do dono,
   "num botão"). Modelos: Kiro NÃO (sem crédito); Gemini 3.8 flash com MUITO cuidado (histórico de quebrar o
   sistema); modelo novo "Gemini Argo" (achar no OmniRoute). Ir treinando os prompts com as experiências desta
   sessão (o que deu certo/errado vira regra). Decidir com os outros chats (MURAL) se compartilha ou é independente.
   - [x 00:20] Argon = "agy/gemini-4-argon-disabled": NÃO responde (timeout 120 s) em 27/10 00:15; 3.8 flash high ok.
   - [x 00:25] bin\cortes_ajustes.json (sync PC2) lido por anime_script (regras_roteiro, só PARCEIRO_CANAL),
     seo_generator (regras_titulo, só Short pt) e parceiro_marca (tarja_largura_max 0,50-0,80, tarja_letra 0,38-0,62).
   - [x 06:40] bin\cortes_melhorador.py + cortes_melhorador.json (molde do colab\melhorador_longo): vigia/desfaz,
     decide por lote (4 júris, >= 6 h), alavancas do cortes_ajustes.json com tipo/faixa (testado: recusa fora da faixa),
     código -> PROPOSTAS.md, modo SOMBRA (decide e grava SOMBRA.md, não aplica), uso por modelo em melhorador_estado.json.
     Camadas: Opus 5.5 > Opus 4.6 > Kiro (>= 01/11) > Gemini 3.8; hoje so_gemini_hoje; Argon só com argon_liberado.
     DESLIGADO: controle.json melhorador_cortes=false + tarefa Cortes_Melhorador desabilitada; LIGAR/DESLIGAR_MELHORADOR.bat.
     PROMPT_MELHORADOR.md v1.1 e LICOES.md treinados com esta sessão.
   - [x 07:10] 1ª volta em sombra (Gemini 3.8 high, ~6 min): 2 certas, 1 meia, 1 errada (repetiu o "fim cortado" das
     lições). Útil como ACHADOR; não aplica sozinho. Rodar em sombra a cada lote e somar o placar no SOMBRA.md.
0. Crons "continue": 1 por hora (dono 26/10 21h: "têm que ser de uma em uma hora") + extras pedidas. Recriar SEMPRE
   antes de acabarem (CronList); só vivem nesta sessão.
1. [x 20:10] TARJA (dono 26/10: "todos vêm com tarja mesmo sem legenda; e mesmo com legenda, menor e menos larga")
   - feito 19:00: visão (anime_hardsub_detect) só vale com texto LIDO e que MUDA entre quadros; folga 0,03->0,015;
     pixels preferem faixa da metade de baixo (GTA pegou o topo e deixou a legenda real à mostra); tarja 72% (era 80%),
     largura = legenda deles + 6% quando medida; letra 50% da altura (era 62%).
   - teste em 5 fontes reais: 7gIwyy (legenda c/ brilho) e JKR5 (chinês) = tarja ok; DXw e DzhR = sem tarja
     -> NA FOLHA tinham legenda intermitente: visão agora com 6 quadros (detecta DzhR/DXw/7gIwyy); controle
     negativo (2 Veo limpos) = 0/6 = sem tarja. PC2 sincronizado.
   - [x 23:10] PRODUÇÃO REAL: 21:44 fonte sem legenda = 0/6 lidos = SEM tarja (sem-obra-5f43a1, quadro limpo);
     22:00/22:32 com legenda = tarja menor/mais estreita (sem-obra-6d5bef). Júri: versões _xx (língua) só movimento.
   - do júri (MURAL 19:20): tarja FIXA 64 s, letra miúda, gênero errado ("ELE" na Merida), spoiler no 1º quadro.
     -> gerar_titulo_tarja: sem spoiler do final, gênero certo; avaliar tarja que muda/some (GOSTO -> teste).
2. [x 21:05] Título quebrado: "ELE DESCOBRIU ovos BICHOS..." — seo_generator descarta título com palavra minúscula
   colada entre MAIÚSCULAS (testado em 6 títulos: só o quebrado sai). PC2 sincronizado.
3a. Achados do 1º júri (sem-obra-05d212, 4,38) a atacar: (i) legenda "a marmita"/"taca um" — a legenda é o TEXTO do
   roteiro (só o tempo vem da voz): conferir com Whisper se é gíria do roteiro ou leitura errada do júri; (ii) a troca
   de imagem atrasa o anúncio do item ("No quarto" com a imagem anterior) em vídeo de RANKING; (iii) 1º lugar
   prometido no gancho sem destaque (payoff); (iv) fim em gancho "quer saber..." lido como corte (é o loop — medir
   retenção antes de mexer: GOSTO); (v) texto de gancho do topo perto da borda (conferir posição real em 1080x1920).
3. [x 21:25] bin\cortes_juri.py (veio de claude-code-video v1.1): movimento em TODO short, júri 4 focos em 1/4,
   aprendiz -> APRENDIDO.md (+ OPINIOES do dono com prioridade). Teste real: sem-obra-05d212 = 4,38, 20 regras.
   Tarefa Cortes_Juri (30 min) criada; MURAL respondido; DECISOES. claude-code-video: v1.1 APLICADA.
   Sistema claude-code-video v1.1 (ATUALIZACAO_PARA_LINHAS.md): (a) executar() nos subprocess com filhos;
   (b) movimento medido + trava de texto em TODO short (barato); (c) júri Gemini entretenimento em 1 a cada 3-5;
   (d) aprendiz por lote -> regras do pipeline; nota da 1ª versão no evolucao.jsonl. Responder no MURAL.
4. [ ] Trechos quase pretos (5,4% movimento) -> pular trecho escuro no corte (CERTEZA).
5. [x 07:30] @handle por cima de rostos: parceiro_marca._y_marca escolhe entre 0,30/0,24/0,36/0,18/0,64 a altura
   com MENOS bordas (rosto/olho/ação = muita borda) fora da tarja/legenda; empate fica 0,30. Em 2 Shorts reais
   escolheu 0,18 (acima do rosto). CONFERIR no 1º Short novo (quadros).
6. [x 00:00 no ar, MEDIR] T1 ligado (TESTES.md): cortes_produto.py + postar_tiktok_auto.produto_meio; testado em
   Short real + dry-run. VOZ CLONADA na postagem: TRAVOU >10 min carregando o Applio no PC1 (26/10 23:55) ->
   desligada (CORTES_PRODUTO_CLONE=1 liga); anime_tts.preparar_clone(abertura=False) pronto. CERTO: gerar
   audio_produto.wav NA PRODUÇÃO (anime_auto, clone já carregado) e o cortes_produto usar. Piada ligada à cena,
   medir views (medir_tiktok) quando houver >= 6 B por conta. DESENHO: trecho 2-3 s do Veo LIMPO do produto num corte de cena a 55-65% do Short (nunca
   começo/fim) + 1 frase positiva do narrador ligando a história ao produto (só o NOME; nada de telefone/URL/@/QR) +
   checagem de visão de contato (PERGUNTA do comercial_veo; qualquer "sim"/falha = posta sem). SÓ nas cópias TikTok/
   Insta (montado na hora, como comercial_veo; regra antiga "YouTube NUNCA" — banimento de 16/10 foi número na tela);
   YouTube só depois de medir. A/B 1 em 3 cópias; views48h/mediana da conta (medir_tiktok). Código: recapd bin\
   cortes_produto.py (a fazer) + chamada no reuso de parceiro no postar_tiktok_auto (linha PRODUTOS/postador:
   avisar no MURAL antes). PRODUTOS no meio do Short (dono 26/10): trechos curtos dos comerciais Veo nossos (já feitos), em ponto
   estratégico (nunca início/fim), narrador faz piada positiva; GOSTO -> teste A/B medindo retenção/views (poucos
   segundos podem derrubar). Cuidado: já tivemos banimento — sem promessa enganosa, marcado como nosso.
7. [ ] Ganchos de expectativa ("pontos de expectativa pra prender até a próxima parte") — com cuidado (banimento
   por isso antes): nada de "parte 2" falsa; GOSTO -> teste.
8. [ ] Instalar Cortes no PC3 (dono: "pode assumir"): InstalarPC3 automático; assets caem (ssh reset) — ver.
9. [ ] Imagens (Flow) pelo PC2: testar quando o dono não estiver usando o PC2.
10. [ ] Ideia do dono: ampliar os curtos para longos (compilados? ver referência Porão: compilados 1-4 h estouram)
    — linha LONGOS é de outro agente: propor pelo MURAL, não fazer aqui.
11. [x 28/10 09:40] aprovado 5a106596: v11 só tinha a 1ª pessoa -> anime_script v12 (+ tom de desabafo informal),
    marcado "aplicado". FALTA: 541 grupos de candidatos (avaliar os 10 mais fortes por ciclo).
13. [x 28/10 10:10] GANCHO LIXO ("[EMPTY RESPONSE]"/inglês) em 13 de 49 Shorts -> validação + 600 tokens + trava
    do júri; 13 segurados (DECISOES 10:10). CONFERIR folha do topo dos próximos Shorts (D:\tmp\folha_topo.py).
    PRÓXIMO NO PRINCIPAL: história nota 2 no júri (5119c9, 918e98, 6852df) — ver o porquê nas fichas.
12. [x 28/10 09:30] PC2 preso em 1 Short por vez (CPU 100% = render do próprio Short) -> CPU só barra com 0 ou 2+;
    disparo que falha devolve o vídeo pra fila (DECISOES 09:30). CONFERIR Shorts/hora do PC2.

14. [ ] Voz nova narrador_chris (recado de outro chat 28/10: D:\hipercool-materiais\models\rvc\vozes\narrador_chris\,
    `voz_clonada.py converter narrador_chris in.wav out.wav`). Cortes usa elenco fixo -> só como TESTE A/B num nicho
    (ouvir 1 amostra antes; views 48 h). Não ligar sem ouvir.

15. [x 28/10 13:40] Hypit 1 (legenda por sentido) e 2 (corte na troca de cena); L, 4 e 7 feitos (DECISOES 13:40).
16. [x 28/10 17:50 — REFERENCIA_NERDCF.md escrito; ideias de teste lá, nenhuma ligada] Hypit 3 engenharia reversa: claude-code-video\referencia.py no Short de anime que mais estourou entre os
    parceiros (L_mSR_s39-s, @nerdcf.animes, 13 mi) -> ANALISE/LINHA_DO_TEMPO em claude-code-video\referencias\
    cortes_nerdcf_anya_13mi\ + comparação com o nosso em linhas\CORTES\REFERENCIA_NERDCF.md. Só documentar.
19. [x 28/10 18:50] MASCOTE (T7, TESTES.md): cortes_mascote.py; conferido no T-Rex (D:\tmp\t7_folha.png: foto no
    canto de cima aos 15,5 s, gravação viva aos 47 s, sem cobrir a cena). PC2 com recortes + reacao_susto_01.webm.
    T6+T7 juntos no mesmo Short: ok (trex_choque_fogo_mascote.mp4); legenda sobreposta conferida resolvida.
18. [x 28/10 17:40] CHOQUE/FOGO (T6, TESTES.md): quadros em hipercool-materiais\assets\cortes_fx (PC1 e PC2 C:),
    sobrepostos nos impactos e em 2 trocas de cena; conferido no T-Rex (D:\tmp\t6_folha.png). Glitch fora (render
    travou). Junto: legenda anterior ficava ~0,3 s embaixo da nova -> fx_subtitles corta o cartão no início do próximo.
    REMOTION: os nossos ficam em claude-code-video\remotion\src\_cortes\ (src\videos é limpa pela outra linha e
    apagava o gancho = "No entry point specified"). Recriar efeitos: D:\tmp\gerar_fx.ps1 (combos no topo).
17. [x 28/10 17:00 T5 ligado "ab"] REMOTION + FFMPEG (dona 28/10: "mixar ou juntar"): o corte continua no ffmpeg (leve, ~volume); o Remotion
    entra só como CAMADA CURTA por cima, onde o ffmpeg é ruim: gancho animado dos 0-3 s, palavra de impacto 3D/mola,
    telinha de WhatsApp/print, recorte vivo do personagem (camadas.py/vivo.tsx do claude-code-video). Render só dos
    poucos segundos da camada, com fundo transparente (ProRes 4444/webm alpha) -> overlay no ffmpeg. Custo medido lá:
    ~1 GB de RAM (Chrome), 4-7 min por 30 s -> 3 s de camada ~30-60 s. Fazer como teste A/B em 1 de cada 4 Shorts,
    só com RAM livre >= 3 GB, executar() que mata a árvore (lição do travamento de 26/10). PRÓXIMO.

## PENDENTES (dona pediu a lista 28/10) — quem destrava
- L cor por personagem: FEITO (nomes no solo; voz nos 2+).   - T conferir 1º Short com título fixo no alto: esperar sair.
- M melhorador / G agente: PRONTOS, desligados — só ligam no sinal da dona (G falta ela dizer o modelo de código).
- 4 trechos quase pretos: FEITO.   - 7 ganchos de expectativa: FEITO como teste T4.
- 8 PC3: desktop sem ssh -> dona precisa religar o sshd lá (Restart-Service sshd) ou instalar à mão.
- 9 Flow pelo PC2: só quando a dona não estiver usando o PC2.   - 10 curtos->longos: é da linha LONGOS (propor no MURAL).

## Já feito hoje (26/10) — ver DECISOES.md
PC2 com Cortes (voz clonada) e SEM yt-dlp; controlador manda Short pro PC2; dorama/filme 1ª pessoa v11;
narrador clone piso +5%; TikTok paralelo; sync de tempos no formato várias vozes.
