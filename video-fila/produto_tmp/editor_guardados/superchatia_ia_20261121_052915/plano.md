# Plano de Edição — SuperChat IA (`superchatia_ia_20261121_052915`)
Duração total: 32.47 s (975 frames a 30 fps)

## Visão Geral e Identidade
- Marca: SuperChat IA
- Cores: Marca `#5B6CFF`, Fundo Escuro `#111827`, Apoio `#1F2937`, Destaque `#5B6CFF`, Texto `#FFFFFF`
- Tipografia: Montserrat (Google Fonts), pesos 500, 700, 900. Mínimo de 32 px em absolutamente todos os elementos.
- Safe Zone: Conteúdo estritamente posicionado entre y=150 e y=1580, margens laterais de 60 px (x=60 a 1020).
- Movimento Contínuo: Zoom/pan dinâmico de 1.05 a 1.15 em todas as cenas + microanimações (> 4% de variação entre 20% e 80% de cada cena).
- Karaokê: `Karaoke` oficial em `src/lib/karaoke.tsx` nas cenas 0, 1, 2 e 3. Ausente na cena 4 (cartão final).

---

## Cena 0 — "Pergunta" (0.00s a 5.63s | frames 0 a 169)
- Fala: "Consigo atender quem vem de anúncios no Instagram e no WhatsApp juntos?"
- Composição: a) Pergunta do cliente em destaque cinético com foto escurecida.
- Fundo: `img_0.jpg` com push-in contínuo (scale 1.05 -> 1.15) e leve deslocamento horizontal para garantir que o apresentador não seja sobreposto.
- Topo (y=180): Barra de progresso + Badge "DÚVIDA COMUM" com ícone.
- Área Central Superior (y=260..520):
  - Card estilizado com a fala da pergunta:
    "Consigo atender quem vem de anúncios..."
  - Sincronização de palavras:
    - 2.28s: Destaque badge "Instagram"
    - 3.04s: Destaque badge "WhatsApp"
    - 3.61s: Marca-texto e escala em "JUNTOS?"
  - 3.80s: Selo fixo do gancho "Atendimento unificado".
- Preservação de Rosto: A área de x=60..1020 e y=260..520 fica completamente acima do torso/cabeça do apresentador posicionado estrategicamente com folga > 50 px.
- Legenda Karaokê: Base em y=1560.
- Transição de Saída (5.3s): Slide suave com wipe.

---

## Cena 1 — "O problema" (5.28s a 12.34s | frames 158 a 370)
- Fala: "Eu me perdia alternando telas para responder clientes do Instagram e do WhatsApp ao mesmo tempo."
- Composição: c) Tela dividida / Comparativo dinâmico de sobrecarga ("Alternando Telas").
- Fundo: `img_1.jpg` com blur de 12 px e vinheta escura da marca.
- Topo (y=180): Badge de dor "O PROBLEMA" em vermelho alerta (#EF4444 com 90% opacidade).
- Título (y=250): "ALTERNANDO TELAS SEM PARAR" (52 px, peso 900, textWrap: balance).
- Comparativo Split (y=380..1160):
  - Card 1 (Instagram Direct) à esquerda (x=70, w=450):
    - Header rosa/gradiente Instagram + contador de "12 mensagens não lidas".
    - Balões simulando clientes esperando resposta.
    - Entra aos 6.39s ("alternando telas").
  - Card 2 (WhatsApp Web) à direita (x=560, w=450):
    - Header verde WhatsApp + alerta de "18 conversas acumuladas".
    - Entra com atraso aos 9.44s ("WhatsApp").
  - Indicador central com setas de troca contínua e badge de alerta "SOBRECARGA DE ABAS".
- Legenda Karaokê: Base em y=1560.
- Transição de Saída (12.0s): Push lateral com aceleração.

---

## Cena 2 — "Como funciona" (11.99s a 21.19s | frames 360 a 635)
- Fala: "No SuperChat IA, os contatos do Instagram, WhatsApp e Telegram chegam juntos num único painel centralizado."
- Composição: b) Mockup mobile de alta fidelidade (largura 840 px) em perspectiva frontal limpa com painel unificado.
- Fundo: `img_2.jpg` com blur 16 px e luz ambiente `#5B6CFF`.
- Topo (y=170): Badge "COMO FUNCIONA" + tag "Painel Centralizado".
- Smartphone Central (y=250..1280, largura 840 px):
  - Topbar com logo SuperChat IA e selo discreto "Simulação" (regra de transparência).
  - Indicadores dos 3 canais integrados (Instagram, WhatsApp, Telegram) acendendo conforme a voz cita cada um:
    - 15.51s: Instagram acende
    - 16.11s: WhatsApp acende
    - 16.86s: Telegram acende
  - Mensagens do briefing entrando sequencialmente (tipografia >= 34 px, fundo opaco >= 95%):
    - 13.5s: Mensagem 1 (Cliente): "Olá, vi o anúncio no Instagram e quero orçamento."
    - 16.1s: Mensagem 2 (Cliente): "Também mandei mensagem no WhatsApp."
    - 17.5s: Balão "Digitando..." animado.
    - 18.8s: Mensagem 3 (Empresa): "Recebemos os dois por aqui no painel centralizado."
- Legenda Karaokê: Base em y=1560.
- Transição de Saída (20.9s): Zoom-out rápido para o corte do dono.

---

## Cena 3 — "O resultado" (20.84s a 28.87s | frames 625 a 866)
- Fala: "Agora nossa equipe organiza todas as conversas num só lugar, com atendimento ágil para todo cliente."
- Composição: h) Vídeo cinematográfico real (`dono_3.mp4` via `<OffthreadVideo muted />`), com elementos apenas no topo (y=160..300).
- Ajuste de Câmera: Vídeo escalado em 1.14 e deslocado verticalmente para posicionar o topo da cabeça do dono em y ~ 340, deixando toda a faixa y=150..300 com respiro livre > 40 px.
- Topo (y=170): Badge "O RESULTADO" em `#5B6CFF`.
- Título Dinâmico (y=240):
  - De 21.0s a 25.5s: "ORGANIZAÇÃO EM UM SÓ LUGAR"
  - Aos 26.0s ("atendimento ágil"): transiciona com scale suave para "ATENDIMENTO ÁGIL PARA CADA CLIENTE".
- Legenda Karaokê: Base em y=1560.
- Transição de Saída (28.5s): Wipe lateral dinâmico.

---

## Cena 4 — "Cartão Final / CTA" (28.52s a 32.47s | frames 855 a 975)
- Fala: "Chame a gente no direct."
- Composição: Cartão final de alta conversão, vivo e dinâmico.
- Fundo: `img_4.jpg` com blur de 24 px + véu escuro azul marinho (`#111827`, 92% opacidade) em zoom contínuo de 1.05 a 1.15.
- Karaokê: Oculto (regra expressa de não exibir legenda no cartão final).
- Elementos:
  - Topo (y=300..520):
    - Ícone com anel pulsante e ondas de IA.
    - Marca grande: "SuperChat IA" (64 px, negrito, branco com destaque azul).
    - Frase oficial dos fatos: "Multi atendimento e CRM com IA" (36 px, cor `#D1D5DB`).
    - Pílulas de canais: "WhatsApp • Instagram • Telegram" (32 px).
  - Centro/Base (y=900..1060):
    - Botão CTA pulsante (scale senoidal 1.00 a 1.07 em ciclo de 1.2s):
      - Texto exatamente alinhado ao convite da voz: "CHAME NO DIRECT" (50 px, peso 900, branco).
      - Shimmer animado (efeito de brilho varrendo o botão).
  - Rodapé (y=1240..1360):
    - Perfil oficial visível desde o frame 0.0s do encerramento: "@superchatia.ia" (44 px, peso 700).
