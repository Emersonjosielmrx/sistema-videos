# Plano de Edição — Cardápio Digital (futebolcom_ia2_20261110_045334)

## Metadados e Paleta
- Duração: 30.45s (914 frames @ 30fps)
- Marca: Cardápio Digital
- Cores:
  - Primária/Marca: #E11D48 (Carmim / Rose vibrante)
  - Apoio: #FACC15 (Amarelo / Dourado)
  - Fundo escuro: #31060F (Bordô escuro premium)
  - Destaque: #E11D48
  - Texto sobre marca: #FFFFFF
- Tipografia: Montserrat (pesos 700, 800, 900)
- Safe Zone: x ∈ [60, 1020], y ∈ [150, 1580]
- Regra de ouro: fonte mínima ≥ 32px em todos os textos (incluindo badges e balões de WhatsApp); títulos ≥ 48px; no máximo 2 camadas de leitura; movimento contínuo (>10%) do início ao fim; zero karaokê no cartão final.

---

## Cena 0 (0.0s – 4.43s | Frames 0 – 133)
- **Tipo:** Pergunta
- **Fala:** "Vou continuar recebendo os pedidos no meu WhatsApp?"
- **Composição:** a) Texto GIGANTE tela cheia cinético sobre foto com zoom contínuo e vinheta dramática.
- **Fundo:** `img_0.jpg` (pizzaria artesanal, forno a lenha) com push-in suave (scale 1.05 -> 1.15) e gradiente escuro na vertical para contraste ideal (relação > 4.5:1).
- **Elementos Visuais:**
  - y=200..260: Pill animada no topo: `[ ❓ DÚVIDA DE QUEM ATENDE ]` (entra no frame 6 com spring).
  - y=450..850: Texto cinético escalonado em 3 linhas gigantescas:
    - Linha 1: "VOU CONTINUAR" (entra aos 0.3s com mola)
    - Linha 2: "RECEBENDO OS PEDIDOS" (entra aos 1.0s com mola e destaque de palavra)
    - Linha 3: "NO MEU WHATSAPP?" (entra aos 2.1s com destaque em pílula verde #25D366 / #E11D48 e ícone pulsando)
  - y=900..1020: Selo animado `[ 📲 Pedidos direto no seu WhatsApp ]` que entra aos 2.8s reforçando a resposta imediata.
- **Transição:** Wipe rápido / slide para a esquerda com desfoque de movimento aos 4.1s.

---

## Cena 1 (4.08s – 12.11s | Frames 122 – 363)
- **Tipo:** Dono
- **Fala:** "Eu achava que usar um cardápio digital ia tirar os meus clientes do atendimento no WhatsApp."
- **Composição:** h) Vídeo cheio do apresentador com câmera em push-in sutil (1.0 -> 1.06) e elementos gráficos EXCLUSIVAMENTE no topo (y=160 a y=420) para blindar 100% o rosto do dono (rosto em y=500..1100).
- **Fundo:** `dono_1.mp4` em tela cheia via `<OffthreadVideo muted />`.
- **Elementos Visuais (Apenas topo):**
  - y=170..230: Badge de categoria: `[ ⚠️ O PROBLEMA ]` (fundo vinho escuro translúcido com borda suave).
  - y=250..400: Card horizontal compacto com texto sincronizado dinâmico:
    - 5.0s – 8.5s: "“ACHAVA QUE IA TIRAR MEUS CLIENTES...”" (com ícone de incerteza)
    - 8.6s – 11.8s: "DO ATENDIMENTO NO WHATSAPP?" (com highlight na palavra WHATSAPP)
  - Movimento contínuo: barra de progresso do pensamento do dono preenchendo suavemente, mantendo dinamismo constante.
- **Transição:** Transição de zoom-in / slide lateral aos 11.7s.

---

## Cena 2 (11.76s – 19.97s | Frames 353 – 599)
- **Tipo:** Conversa
- **Fala:** "Mas a conversa continua lá dentro: a IA tira dúvidas sobre a pizza enquanto o cliente escolhe pela foto."
- **Composição:** b) Celular 3D inclinado (rotateY: -12deg, rotateX: 6deg, perspective: 1200px) com interface de WhatsApp hiper-realista, mensagens entrando uma a uma, badge obrigatório "SIMULAÇÃO" (≥34px), e miniatura do cardápio com foto viva da pizza.
- **Fundo:** `img_2.jpg` com blur suave (12px) e véu escuro (#31060F com opacidade 0.75) para destacar o mockup do smartphone.
- **Elementos Visuais no Smartphone (largura 880px, fontes ≥ 34px):**
  - Header WhatsApp com nome "Pizzaria Bella • IA Atendente" e status "Online".
  - Selo obrigatório no topo do celular: `[ ✦ SIMULAÇÃO ]` (34px, alto contraste).
  - Balões de conversa sincronizados com a narração e o áudio:
    - 12.2s (frame 366): Cliente: "Boa noite! Tem pizza meio a meio?"
    - 13.5s (frame 405): Empresa/IA: "Boa noite! Temos sim. Veja as fotos no cardápio:" + Card com foto e botão "Abrir Cardápio".
    - 15.5s (frame 465): Cliente: "A de frango vem com catupiry?"
    - 16.8s (frame 504): Empresa/IA: "Sim, vai com catupiry! Qual a outra metade?"
    - 18.0s (frame 540): Cliente: "Quero metade frango e metade calabresa."
  - Indicador sutil de "IA respondendo instantaneamente" pulsando.
- **Transição:** Zoom mergulhando suavemente na transição para a cena 3 (aos 19.6s).

---

## Cena 3 (19.62s – 26.95s | Frames 589 – 808)
- **Tipo:** Veo / Demonstração
- **Fala:** "Você mantém o canal que seu cliente já conhece, mas recebe o pedido organizado direto na tela do celular."
- **Composição:** e) / d) Vídeo de b-roll do pizzaiolo (`video_3.mp4`) com push-in dinâmico + Card flutuante sofisticado de "PEDIDO ORGANIZADO" (comanda digital automática) entrando em cascata lateral.
- **Fundo:** `video_3.mp4` (chef espalhando molho com concha) com slow zoom e gradiente para leitura.
- **Elementos Visuais:**
  - y=170..230: Badge superior: `[ 🚀 O RESULTADO ]`
  - y=270..400: Título dinâmico:
    - 20.0s – 22.5s: "CANAL QUE O CLIENTE JÁ CONHECE" (com ícone WhatsApp oficial estilizado)
    - 22.8s – 26.5s: "PEDIDO 100% ORGANIZADO NA TELA"
  - y=450..1200: Painel de Comanda Inteligente (Mobile Order Ticket):
    - Cabeçalho: "NOVO PEDIDO RECEBIDO #1042" (com badge verde pulsante "CONFIRMADO")
    - Item 1: "1x Pizza Grande Meio a Meio" (R$ 68,00)
    - Subitens com checks: "✓ 1/2 Frango c/ Catupiry" e "✓ 1/2 Calabresa Especial"
    - Observação: "Pedido fechado automaticamente pela IA via WhatsApp"
    - Animação: O ticket entra deslizando com spring, e cada item é checado com animação verde na fala "pedido organizado".
- **Transição:** Cross-dissolve elegante com escala aos 26.6s.

---

## Cena 4 (26.6s – 30.45s | Frames 798 – 914)
- **Tipo:** Cartão Final (CTA)
- **Fala:** "Chame a gente no direct."
- **Composição:** Encerramento exclusivo, luminoso e de alto impacto de agência: zero karaokê, foco total no CTA.
- **Fundo:** `img_4.jpg` com desfoque profundo (24px), zoom contínuo lento (1.0 -> 1.08) e overlay escuro premium (#31060F com 0.85 de opacidade).
- **Elementos Visuais (y=200 a y=1480, perfeitamente equilibrados):**
  - y=280..420: Logo / Marca em destaque: "CARDÁPIO DIGITAL" (fonte 68px, branco + pílula carmim #E11D48, flutuação suave floating spring).
  - y=460..540: Subtítulo de valor (36px): "Pedidos direto no seu WhatsApp com IA"
  - y=620..920: Visual central elegante: Ícone flutuante 3D de Mensagem / Direct com brilho radial.
  - y=1000..1160: Botão de Ação CTA Gigante (altura 120px, largura 800px):
    - Texto: "CHAME NO DIRECT" (52px, bold 900)
    - Efeito: pulsação contínua (scale 1.0 -> 1.05) + feixe de brilho (shimmer) varrendo da esquerda para a direita a cada 1.5s.
  - y=1240..1320: Handle oficial: "@futebolcom.ia2" (40px, cor #FACC15 de apoio com ícone do Instagram).
- **Final:** Animação viva até o último frame (914).
