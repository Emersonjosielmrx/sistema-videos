# Plano de Edição — Agenda IA (sintetizerisada_20261127_072410)

Duração total: 33.44 s (1004 frames a 30 fps)
Produto: Agenda IA
Paleta: Laranja (#FFA94D), Grafite Escuro (#1F2937 / #111827), Branco (#FFFFFF), Verde destaque (#10B981)

---

## Cena 0 (0.00s a 5.07s — Frames 0 a 152) — "A Pergunta / O Gancho"
- **Tipo:** pergunta
- **Fala:** "Dois clientes pedem o mesmo horário e você perde um deles?"
- **Composição escolhida:** (a) Texto GIGANTE tela cheia com palavras-chave em destaque + cards de colisão de horário sobre foto de salão em push-in constante.
- **Posicionamento dos elementos:**
  - Barra de progresso contínua no topo (y=150, h=6px).
  - Badge no topo (y=170): "AGENDA IA • CONFLITO DE HORÁRIO".
  - Título cinético (y=260 a 520): "DOIS CLIENTES PEDEM O MESMO HORÁRIO?" com "MESMO HORÁRIO" em pílula laranja.
  - Centro (y=620 a 1100): Demonstração visual do conflito: dois cards de agendamento mobile às 15:00 colidindo. Aos 2.60s ("você perde um deles?"), o segundo card ganha X vermelho "HORÁRIO PERDIDO" e alerta pulsante "⚠️ PERDA DE FATURAMENTO".
  - Fundo: `img_0.jpg` com zoom contínuo de 1.05 a 1.18 + vinheta protetora escura.
  - Legenda Karaokê na base (y=1320 a 1580).
- **Entrada por palavra:**
  - 0.32s ("Dois"): Pop do badge e entrada das palavras com mola.
  - 1.53s ("mesmo horário"): Acende box laranja no título e colisão dos cards 15:00.
  - 2.60s ("perde um deles"): X vermelho e alerta dramático com tremor sutil.
- **Transição para Cena 1:** Corte rápido com push-in de câmera (0.3s antes do fim).

---

## Cena 1 (4.72s a 12.91s — Frames 142 a 387) — "O Problema Real (Depoimento do Dono)"
- **Tipo:** dono
- **Fala:** "Eu vivia com dois clientes pedindo o mesmo horário no WhatsApp, e sempre um deles saía chateado comigo."
- **Composição escolhida:** (h) Vídeo cheio do apresentador real com câmera em push-in sutil (1.00 a 1.06) e texto estritamente no alto (y: 160 a 330), mantendo rosto 100% livre (y: 350 a 1100 desobstruído).
- **Posicionamento dos elementos:**
  - Vídeo de fundo: `dono_1.mp4` via `OffthreadVideo` em tela cheia, muted.
  - Topo (y=165): Badge "RELATO REAL • O PROBLEMA".
  - Headline superior (y=230 a 320): Card dinâmico sincronizado:
    - 5.38s a 8.50s: "DOIS CLIENTES NO WHATSAPP"
    - 8.64s a 12.0s: "CLIENTE CHATEADO COM A EMPRESA ❌" com tag de dor.
  - Legenda Karaokê na base (y=1320 a 1580).
- **Entrada por palavra:**
  - 5.38s ("Eu vivia"): Entrada do badge de contexto.
  - 7.36s ("pedindo o mesmo horário"): Card superior destaca o problema.
  - 10.84s ("saía chateado"): Badge fica vermelha/alerta de atrito.
- **Transição para Cena 2:** Slide lateral suave com desfoque de movimento.

---

## Cena 2 (12.56s a 21.18s — Frames 377 a 635) — "Como Funciona (A Solução Inteligente)"
- **Tipo:** conversa
- **Fala:** "A IA vê a agenda em tempo real, oferece só o horário livre e bloqueia a vaga para o primeiro que escolher."
- **Composição escolhida:** (b) Mockup de smartphone inclinado em 3D sutil (rotateY de 15deg a 0deg) com fluxo de mensagens do WhatsApp aparecendo uma a uma conforme a narração + selo "Simulação".
- **Posicionamento dos elementos:**
  - Fundo: `img_2.jpg` com desfoque elegante + overlay dark da marca (#111827 a 85%).
  - Topo (y=165): Badge "COMO FUNCIONA • IA NO WHATSAPP".
  - Indicador de status IA (y=230): Pílula pulsante "⚡ Verificação em tempo real" que muda para "🔒 Vaga bloqueada automaticamente".
  - Smartphone (y=340 a 1280, w=840px): Interface do WhatsApp com tipografia >= 34px:
    - 13.05s: Cliente pergunta: "Oi! Tem horário amanhã às 15h?"
    - 15.00s ("A IA vê a agenda"): IA responde: "Tenho sim! Às 15h está livre. Posso reservar para você?"
    - 17.30s: Cliente responde: "Pode reservar, por favor."
    - 18.20s ("bloqueia a vaga"): IA confirma: "Pronto, horário confirmado. Vou te lembrar antes." + Tag verde "VAGA BLOQUEADA NO SISTEMA".
    - 19.40s: Cliente: "Perfeito, obrigada!"
  - Selo discreto "Simulação" no canto inferior do mockup.
  - Legenda Karaokê na base (y=1320 a 1580).
- **Entrada por palavra:** Sincronização estrita de cada balão no momento em que a locução aborda a ação.
- **Transição para Cena 3:** Zoom-through penetrando na tela com desfoque radial.

---

## Cena 3 (20.83s a 29.80s — Frames 625 a 894) — "O Resultado & Comparativo de Custo"
- **Tipo:** veo
- **Fala:** "Sem conflito e sem duplo agendamento, a agenda fica organizada dia e noite, por uma fração do custo de uma recepção humana."
- **Composição escolhida:** (c) Comparativo dinâmico de valor e benefícios com cards de impacto sobre o vídeo comercial do salão (`video_3.mp4`).
- **Posicionamento dos elementos:**
  - Vídeo de fundo: `video_3.mp4` via `OffthreadVideo` muted com leve gradiente para contraste perfeito.
  - Topo (y=165): Badge "O RESULTADO • EFICIÊNCIA MÁXIMA".
  - Bloco de Benefícios (y=250 a 480):
    - 21.32s ("Sem conflito"): Check verde "✓ ZERO CONFLITO DE HORÁRIO".
    - 22.83s ("sem duplo agendamento"): Check verde "✓ ZERO DUPLO AGENDAMENTO".
    - 25.05s ("dia e noite"): Tag luminosa "🌙 ATENDIMENTO 24H AUTOMÁTICO".
  - Comparativo de Custo (y=530 a 1150) — estritamente baseado nos fatos do briefing:
    - 26.33s ("fração do custo"): Entrada do card comparativo:
      - Recepção humana: "R$ 2.500 /mês" (tachado em vermelho suave)
      - Agenda IA 24h: "A partir de R$ 199" (em destaque dourado/laranja com brilho)
      - Economia superior a 90% sem folgas nem atrasos.
  - Legenda Karaokê na base (y=1320 a 1580).
- **Entrada por palavra:** Cada linha do comparativo e benefício entra com spring sincronizado à fala.
- **Transição para Cena 4:** Wipe dinâmico com flare laranja para o cartão final.

---

## Cena 4 (29.45s a 33.44s — Frames 883 a 1004) — "Cartão Final de Alta Conversão"
- **Tipo:** cartao
- **Fala:** "Chame a gente no direct."
- **Composição:** Cartão final profissional de agência, sem legenda karaokê, altamente pulsante e dinâmico.
- **Posicionamento dos elementos:**
  - Fundo: `img_4.jpg` com desfoque cinematográfico (blur 16px) e véu azul-escuro/grafite (#111827).
  - Topo (y=300): Logotipo & Nome "AGENDA IA" (fonte 64px, negrito 900, com ícone de calendário reluzente).
  - Subtítulo explicativo (y=430): "Agendamentos automáticos 24h direto no WhatsApp" (fonte 36px, legível e direto).
  - Pilar de diferenciais (y=560 a 780): Três badges em cápsula:
    - "✓ 24 horas por dia"
    - "✓ Sem duplo agendamento"
    - "✓ A partir de R$ 199"
  - Botão CTA Principal (y=920 a 1100, w=820px, h=130px):
    - Background laranja pulsante (#FFA94D) com escala contínua de 1.00 a 1.07.
    - Shimmer de luz passando pelo botão a cada 1.5s.
    - Texto CTA: "CHAME NO DIRECT" (fonte 46px, peso 900, cor #1F2937).
  - Identificador social (y=1220):
    - Box escuro protetor (opacidade 90%): "@sintetizerisada" (fonte 42px).
- **Movimento contínuo:** Zoom-in no fundo (1.05 a 1.15), pulso harmônico do botão, rotação suave do ícone da marca.
