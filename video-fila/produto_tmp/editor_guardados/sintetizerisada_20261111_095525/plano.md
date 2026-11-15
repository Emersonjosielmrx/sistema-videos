# Plano de Edição — Agenda IA (`sintetizerisada_20261111_095525`)

Duração: 28.5s (855 frames a 30 fps)
Cores da marca: Laranja `#FFA94D`, Escuro `#1F2937`, Texto Claro `#FFFFFF`, Destaque `#FFA94D`
Arroba: `@sintetizerisada`
CTA: "CHAME NO DIRECT" (fala: "Chame a gente no direct.")

---

## Cena 0 (0.0s – 5.17s | frames 0 – 155) — "pergunta"
- **Fala:** "Cliente desmarcou de última hora e deixou buraco na agenda?"
- **Composição:** a) Texto GIGANTE tela cheia cinético sobre foto escurecida com vinheta e câmera lenta push-in.
- **Visual & Elementos:**
  - Fundo: `img_0.jpg` com escala de 1.05 a 1.15, pan sutil, filtro escuro com vinheta e degradê da marca.
  - Alerta/Gancho (0.0s – 0.6s): Selo animado "AGENDA EM RISCO" com ícone de alerta em `#FFA94D` no topo (y=210).
  - Texto Cinético (sincronizado com as palavras):
    - 0.3s ("Cliente desmarcou"): Bloco superior grande entra com punch scale: "CLIENTE DESMARCOU" (tamanho 56px, bold, branco).
    - 1.48s ("de última hora"): Linha 2 com marca-texto laranja: "DE ÚLTIMA HORA?" (tamanho 64px, `#FFA94D`).
    - 2.66s ("e deixou buraco na agenda?"): Card de impacto entra em y=580: "BURACO NA SUA AGENDA" com relógio de horário vago e badge "HORÁRIO PERDIDO" em vermelho/laranja.
  - Movimento contínuo: Push-in de câmera (scale 1.05 -> 1.14), pulso de brilho no card, transição suave para a cena 1 aos 4.82s.
  - Safe zone: y=180 a 1450, x=70 a 1010. Letras 36px a 64px.
  - Transição de saída: Fade/slide limpo desarmando elementos aos 4.82s.

---

## Cena 1 (4.82s – 12.48s | frames 145 – 374) — "dono"
- **Fala:** "Remarcações de última hora tomavam meu tempo e deixavam vários horários vagos no meu dia."
- **Composição:** h) Vídeo cheio do apresentador falando, câmera com zoom lento (1.0 -> 1.06), elementos gráficos restritos estritamente ao topo (y=160–420). Rosto 100% desobstruído com respiro de >50px.
- **Visual & Elementos:**
  - Fundo: `<OffthreadVideo src={staticFile('dono_1.mp4')} muted />` com leve zoom suave contínuo.
  - Topo (y=180): Selo elegante "O PROBLEMA" com fundo glass escuro e borda fina `#FFA94D`.
  - Títulos Cinéticos sequenciais (desmonte rápido de 0.2s antes de cada um):
    - 4.82s – 7.18s ("Remarcações de última hora"): Card topo entra: "REMARCAÇÕES EM CIMA DA HORA"
    - 7.18s – 8.8s ("tomavam meu tempo"): Substitui limpo: "PERDA CONSTANTE DE TEMPO"
    - 8.9s – 12.0s ("deixavam vários horários vagos"): Substitui limpo: "HORÁRIOS VAGOS NA GRADE" com badge de alerta.
  - Base: Karaoke ativo ancorado em y=1560 (base 360).
  - Rosto livre: Área entre y=460 e 1050 totalmente limpa sem nenhum elemento gráfico sobre o apresentador.

---

## Cena 2 (12.13s – 19.36s | frames 364 – 581) — "conversa"
- **Fala:** "O cliente pede para remarcar e a inteligência artificial reorganiza o horário direto na conversa."
- **Composição:** b) Celular mockup grande em perspectiva 3D suave (rotateY 8°, rotateX 4°) com interface de WhatsApp animada e balões entrando em cascata no tempo exato da fala.
- **Visual & Elementos:**
  - Fundo: `img_2.jpg` com desfoque de 8px e vinheta escura, movimento de pan lateral.
  - Topo (y=170): Tag "COMO FUNCIONA" + título "REORGANIZAÇÃO AUTOMÁTICA".
  - Mockup de Smartphone (largura 840px, y=340 a 1400):
    - Topo do celular: Barra WhatsApp com avatar "Agenda IA", status "Online (IA 24h)" e selo discreto "Simulação".
    - 12.6s ("O cliente pede para remarcar"): Balão 1 (Cliente, direita): "Preciso mudar meu atendimento de hoje para amanhã." (fonte 34px).
    - 14.3s ("e a inteligência artificial"): Indicador "Digitando..." pulsa por 0.4s, depois entra Balão 2 (Empresa, esquerda, fundo escuro/laranja): "Sem problemas! Tenho amanhã às 14h ou 16h. Qual prefere?" (fonte 34px).
    - 15.7s ("reorganiza o horário"): Balão 3 (Cliente): "Pode ser às 14h." (fonte 34px).
    - 16.9s ("direto na conversa"): Balão 4 (Empresa): "Perfeito! Horário remarcado para amanhã às 14h." + Ícone animado de confirmação ✓.
  - Movimento contínuo: Rotação e escala sutil do aparelho, scroll suave das mensagens.

---

## Cena 3 (19.01s – 24.86s | frames 570 – 746) — "imagem"
- **Fala:** "Hoje minha recepção trabalha vinte e quatro horas com a agenda sempre em dia."
- **Composição:** g) Grade/Checklist de benefícios em cards flutuantes de alta fidelidade com checks animados e contadores sobre a foto dinâmica.
- **Visual & Elementos:**
  - Fundo: `img_3.jpg` com push-in de câmera, gradiente escuro e partículas de luz.
  - Topo (y=170): Selo "O RESULTADO" + Título "AGENDA SEMPRE CHEIA E EM DIA".
  - 3 Cards de Impacto (empilhamento escalonado com mola spring):
    - Card 1 (19.5s - "Hoje minha recepção"): "Atendimento IA 24 Horas" — Selo verde "Ativo 24/7" (y=440).
    - Card 2 (21.0s - "vinte e quatro horas"): "Zero Horários Vagos" — Ícone ✓ animado e "Sem conflito de agenda" (y=660).
    - Card 3 (22.3s - "agenda sempre em dia"): "Reagendamento no WhatsApp" — "100% Automático" (y=880).
  - Gráfico/Progresso visual: Barra de ocupação da agenda subindo de 60% para 100% com cor `#FFA94D`.
  - Movimento: cards flutuam com delay/spring suave, mantendo mais de 10% de dinamismo.

---

## Cena 4 (24.51s – 28.5s | frames 735 – 855) — "cartão"
- **Fala:** "Chame a gente no direct."
- **Composição:** Encerramento Vivo (CTA de Agência).
- **Visual & Elementos:**
  - Fundo: `img_4.jpg` com blur de 16px + véu escuro azul-petróleo/grafite (`#111827`) e luz âmbar pulsante.
  - Topo/Centro (y=420):
    - Logo Badge "Agenda IA" estilizado com ícone de calendário inteligente (tamanho 64px, negrito, branco e `#FFA94D`).
    - Tagline oficial (baseada no briefing): "Agendamentos automáticos com IA 24h" (fonte 36px, `#E5E7EB`).
  - Botão Principal (y=980):
    - Texto exato: "CHAME NO DIRECT" (fonte 46px, bold, fundo `#FFA94D`, texto `#1F2937`).
    - Animação de pulso contínuo (escala 1.0 -> 1.05 e brilho passando / shimmer wave).
  - Identificador (y=1120):
    - Handle `@sintetizerisada` em pílula translúcida com ícone do Instagram / Direct (fonte 38px, `#FFFFFF`).
  - Sem Karaoke (como exigido pela regra).

---

## Áudio e Trilha
- `narracao.mp3`: volume 1.0 do frame 0 ao fim.
- `trilha.mp3`: volume 0.10 durante narração, subindo para 0.22 no cartão final (24.5s a 28.5s), com fade out suave no último segundo.
