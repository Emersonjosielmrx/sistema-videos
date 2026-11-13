# Pedidos da dona para a linha LONGOS (o melhorador lê em toda decisão; mais novo em cima)

Acrescente aqui (ou peça a um chat) qualquer pedido novo. O melhorador cumpre o que der com ALAVANCA e o resto vira
PROPOSTA de código (PROPOSTAS.md) para uma sessão forte aplicar.

## 28/10 (3º pedido) — MASCOTE
- Personagem ÚNICA = a brasileira (05_morena_brasileira). Laranja proibida (cara da Crunchyroll). Mesma cara/pele/olhos;
  muda roupa = COSPLAY da história (ninja, cavaleira, dama, streamer, estudante...), cores do Brasil.
- Poses sensuais como as capas do hipercool, sem o homem; roupas sensuais vestida (limite do Flow, sem nudez).
- Cor de cabelo e olhos: dona ainda vai escolher (opções em hipercool-materiais\mascote_waifu_v2\cores).
- Ideia: o público achar que ela é a dona do canal (persona do canal); trocar as FOTOS DE PERFIL dos canais por ela.
- Ela tem que ter VIDA: mexer enquanto fala, pose combinando com a fala, boca mexendo. Gravar no Veo 3 com fundo
  branco, recortar e pôr na lateral; GPU onde der; guardar as gravações num ARSENAL pra reaproveitar.
- Falas reais de séries: até ~10 s é uso justo pra dona; baixar todas as possíveis (arsenal_memes.py).

## 28/10 (2º pedido)
- Vozes iniciais SEMPRE as mais atrativas, principalmente a 1ª — FEITO (teste_narradores.json "atrativas").
- 1ª troca logo no começo (pra verem a troca) e as trocas cada vez mais espaçadas — FEITO (anime_tts._inicios_blocos).
- Narradores ruins: Patrick Estrela — FEITO (teste_narradores.json "ruins").
- Resumo do começo com MEMES estampados por cima ou abrindo uma brecha no vídeo — pendente (lista).
- Falas de personagem com outra voz, como o Mike faz (ora narra, ora faz a voz do personagem) — pendente (lista).
- Máximo de efeitos sonoros (espadas em batalha, coisas quebrando, corrida, tiros) — pendente (lista).
- ARSENAL de memes de áudio de séries famosas no momento certo (Chaves "pega ladrão", Seu Madruga cantando,
  Julius "isso custa x centavos", Greg "cara, ela tá na sua"...) — pendente (lista).

## 28/10
- O trabalho principal é melhorar o sistema A CADA VÍDEO: o próximo sai melhor que o anterior, e assim por diante.
  O melhorador substitui o chat e continua melhorando mesmo com ele fechado.
- Ambientação e explicação inicial: RESUMO de abertura ("hoje você vai conhecer X... foi traído... virou um cara
  foda...", com as imagens desses momentos, e o gancho pra começar) — FEITO (resumo.*).
- Mascote aparecendo e FALANDO — FEITO com a mascote atual (mascote.fala). Mascote nova: waifu bonita estilo
  Crunchyroll, mais sexy (vestida), aguardando a dona aprovar o desenho.
- Efeitos tipo hipercool (impacto, 2.5D, overlays, transições fogo/água/raio, câmera dentro da imagem, parecer
  anime) EM CAMADAS: primeiro o que acrescenta menos tempo e dá mais impacto; medir quanto cada um acrescenta
  (% e horas) — lista em EFEITOS_LISTA_DONA.md, a dona escolhe. Vídeo de 4 h não pode virar 8 h.

## 27/10
- Máximo de views/viralidade é o objetivo de tudo.
- Revezamento de narradores contínuo, muitos narradores por vídeo; troca criativa (não só mudar a voz) e cada um no
  seu jeito. NUNCA nome de narrador na legenda. Narrador PARCEIRO nunca chamado pelo nome; só personagem.
- Sem palavrão (desmonetiza) — nem na passagem de vez. Vídeo com palavrão não vai pro canal.
- Trilha não pode ficar alta em cima da voz clonada (voz vai a -18,5 LUFS antes do mix desde 27/10; conferir).
- Nada de vídeo refeito à toa: vídeo já feito nunca volta pra fila.
- Marca d'água do scan: tirar; se não der, tarja branca com a nossa marca; delogo é o preferido pra esconder texto.
- Modelos: nada de Opus nem Kiro; Argon só em texto curto/análise com prazo curto, fallback Gemini 3.8.
- Gancho escrito não pode cobrir rosto. Karaokê com palavras separadas (2 espaços desde 27/10).
- Postar 1 longo por canal por dia nos canais pt mais ligados a manhwa (Manhwa Noturno, inovare manhwa br, ForjaReact,
  ManhwaReact, Animescomia, CartuchoReact, InventoReact) e comparar qual performa melhor. NUNCA InovareManhwaVerse.
- Inserir corte curto dos produtos de IA da dona (Veo limpo, ≤ 25 s, sem contato na tela) com MUITO cuidado — ainda
  não feito, só depois de testar 1 vídeo.
- Explorar outros longos narrados: dorama longo (canais de C/K-drama recap em inglês), recap de filme, temporada
  inteira, donghua.
