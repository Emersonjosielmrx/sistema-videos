# Plano de Edição — SuperChat IA (`superchatia_ia_20261122_073012`)

## Informações Gerais
- **Produto**: SuperChat IA
- **Duração**: 31.77 s (954 frames a 30 fps)
- **Cores**: Marca `#5B6CFF`, Apoio `#111827`, Destaque `#5B6CFF`, Texto `#FFFFFF`
- **Tipografia**: Montserrat (Google Fonts), tamanhos estritamente ≥ 32px (títulos ≥ 48px)
- **Safe Zone**: 1080x1920 (y: 150 a 1580, margem x: 60 a 1020)
- **Áudio**: `narracao.mp3` integral (voz da narradora e do dono sincronizada) + `trilha.mp3` com ducking inteligente (0.10 com voz, 0.22 no final)

---

## Cena 0: Pergunta / Gancho (0.00s – 4.83s | 145 frames)
- **Tipo**: `pergunta`
- **Composição**: Composição **a** (Texto GIGANTE cinético em tela cheia com tag vermelha de alto contraste) seguida de pop-up elástico aos 1.6s do mockup de celular com simulação de multicanais.
- **Fundo**: `img_0.jpg` com push-in contínuo (scale 1.05 -> 1.24) e iluminação dinâmica.
- **Entrada dos Elementos**:
  - `t=0.0s`: Barra de progresso no topo (y=152) inicia avanço.
  - `t=0.1s`: Pill de contexto no topo (y=156): "CENTRALIZAÇÃO DE CANAIS" com badge tecnológico.
  - `t=0.318s`: Tag vermelha sólida (#DC2626) com texto branco (#FFFFFF) "PERDENDO" entra com escala e impacto (fonte 56px, bold).
  - `t=0.775s`: "CONTATO DE CLIENTE?" completa o bloco superior com animação mola (spring).
  - `t=1.60s` (f=48): Mockup gigante entra com spring elástico (pop-up) no instante em que a fala anuncia os canais.
  - `t=2.073s` (f=62): Notificação do WhatsApp Comercial entra com badge "Sem Registro" e texto secundário em cinza claro #CBD5E1.
  - `t=2.794s` (f=84): Notificação do Instagram Direct entra com badge "Lead Perdido" e texto secundário em #CBD5E1.
  - `t=3.50s` (f=105): Banner de alerta inferior "Contatos dispersos sem CRM integrado" pulsa em destaque.
  - `t=0.3s a 4.4s`: Legenda karaokê ativa na base (y=1560).
- **Transição**: Push-in contínuo conectando com o início da fala do apresentador.

---

## Cena 1: O Problema (4.48s – 12.51s | 241 frames)
- **Tipo**: `dono`
- **Composição**: Composição **h** (Vídeo em frame corporativo de alta tecnologia contextualizando o cenário real do comércio, com recorte focado eliminando ruídos visuais).
- **Vídeo**: `dono_1.mp4` em card estilizado com vinheta interna e selo "Cenário Real • Atendimento no Comércio".
- **Entrada dos Elementos**:
  - `t=4.48s`: Pill superior fixa (y=162): "O PROBLEMA" com sinalizador vermelho pulsante.
  - `t=4.48s a 9.39s`: Card no topo: "ANOTAÇÃO MANUAL DE CONTATOS" com badge "Manual".
  - `t=9.40s` ("Sempre sobrava algum contato sem registro", f=146): PUNCH-IN SECO (salto de escala para 1.12x) quebrando a monotonia do take longo. Card muda para alerta "CONTATO SEM REGISTRO".
  - Legenda karaokê perfeitamente sincronizada em y=1560.
- **Transição**: Corte contínuo aos 12.16s para a cena seguinte.

---

## Cena 2: Como Funciona (12.16s – 20.35s | 246 frames)
- **Tipo**: `dono` + Motion Design B-Roll
- **Composição**: Composição **b** na abertura e Composição **d** (zoom-through para Motion Design B-Roll demonstrando o SuperChat IA e o CRM em funcionamento).
- **Vídeo & Mockup**:
  - `t=12.16s a 15.33s` (f=0 a 94): Apresentador no escritório moderno com HUD superior espaçoso e tipografia grande.
  - `t=15.34s a 20.35s` (f=95 a 246): Transição para Motion B-Roll com Painel Central do SuperChat IA:
    - f=95 ("WhatsApp"): Mensagem WhatsApp entra com badge WA verde e notificação.
    - f=125 ("Telegram"): Mensagem Telegram entra com badge TG azul.
    - f=142 ("Instagram"): Mensagem Instagram entra com badge IG gradiente.
    - f=160 ("já alimenta o CRM com IA"): Caixa de automação do CRM ativa em tempo real com checkmarks "✓ No CRM" e brilho luminoso.
- **Transição**: Wipe direcional com blur conectando fluidamente com a Cena 3.

---

## Cena 3: O Resultado (20.00s – 28.18s | 246 frames)
- **Tipo**: `dono`
- **Composição**: Composição **g** (Checklist de benefícios com alto contraste e legibilidade impecável desde o estado inativo).
- **Vídeo**: `dono_3.mp4` com enquadramento mais fechado (escala 1.16x a 1.22x) focado na ação de acompanhamento no computador.
- **Entrada dos Elementos**:
  - `t=20.00s`: Wipe direcional suave com blur de transição.
  - `t=20.00s`: Pill superior: "O RESULTADO • CONTROLE TOTAL" (esmeralda #10B981).
  - Cards de benefícios iniciam com fundo escuro sólido (#111827), borda nítida e texto branco em 85% de opacidade:
    - `t=21.83s` ("contato fica organizado no CRM"): Card 1 acende com borda verde esmeralda (#10B981), checkmark luminoso e brilho dinâmico.
    - `t=24.65s` ("minha equipe acompanha todos"): Card 2 acende com borda azul (#5B6CFF), checkmark luminoso e brilho dinâmico.
  - Legenda karaokê em y=1560 até 27.85s.
- **Transição**: Zoom contínuo para o Cartão Final aos 27.83s.

---

## Cena 4: Cartão Final / CTA (27.83s – 31.77s | 119 frames)
- **Tipo**: `cartao`
- **Composição**: Composição **e** (Cartão final cinematográfico vivo perfeitamente centralizado verticalmente na safe zone, sem vazios na metade inferior).
- **Fundo**: `img_4.jpg` com zoom contínuo de 1.08 a 1.28 + spotlight dinâmico e anel tecnológico em rotação contínua.
- **Entrada dos Elementos**:
  - `t=27.83s`:
    - Card principal amplo e equilibrado centralizado verticalmente entre y=260 e y=1440.
    - Nome da marca grande: "SuperChat IA" (fonte 76px, bold, glow).
    - Descrição oficial com ortografia perfeita: "Multiatendimento e CRM com IA" (fonte 40px).
    - Badges de canais: "WhatsApp • Telegram • Instagram" (fonte 34px).
    - Fatos permitidos em destaque: "Centraliza conversas no mesmo painel" e "Atendimento IA 24h no WhatsApp".
    - Botão CTA com heartbeat contínuo e brilho passando a cada 36 frames: "CHAME NO DIRECT" (fonte 48px).
    - Perfil oficial visível desde o frame inicial: "@superchatia.ia" (fonte 44px).
  - Sem legenda karaokê no cartão final.
