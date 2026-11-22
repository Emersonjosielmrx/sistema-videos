# Plano de Edição — Agente Pessoal IA (Agentes de IA)
ID: agentesdeia_ia_20261121_222123
Duração: 31.14 s (935 frames a 30 fps)
Formato: Vertical 1080x1920 (Reels / TikTok)

## Paleta de Cores & Design System
- Marca / Destaque: #10B981 (Verde Esmeralda Vibrante)
- Fundo Escuro / Apoio: #111827 (Dark Slate / Grafite Profundo)
- Cards e Superfícies: rgba(17, 24, 39, 0.94) com bordas em rgba(255, 255, 255, 0.12) e glow esmeralda
- Texto: #FFFFFF (Principal), #94A3B8 (Secundário), #10B981 (Acentos e badges)
- Safe Zone: y = 150 a y = 1580, laterais x = 60 a 1020. Tipografia mínima >= 32px.

---

## Cenas e Composições

### Cena 0 (0.00s a 5.43s | frames 0 a 163) — Pergunta
- **Tipo**: pergunta
- **Fala**: "Posso transferir essas pequenas tarefas chatas do dia a dia para ele?"
- **Composição**: a) Texto GIGANTE cinético em tela cheia sobre foto escura com marca-texto dinâmico e cards de microtarefas entrando.
- **Layout & Posicionamento**:
  - y = 150: Barra de progresso superior
  - y = 220: Badge superior animado com mola "PERGUNTA FREQUENTE"
  - y = 340 a 780: Pergunta em texto cinético grande (fonte 56px, textWrap balance): "Posso transferir essas pequenas tarefas chatas do dia a dia para ele?"
    - 0.3s ("Posso transferir"): entrada em mola scale(0.9 -> 1.0)
    - 1.4s ("pequenas tarefas chatas"): caixa destacada verde esmeralda com texto contrastante
  - y = 840 a 1300: Pilha de 3 cards representativos das microtarefas ("Pesquisa de concorrentes", "Agendamento de reuniões", "Follow-up de contatos") entrando escalonados aos 1.8s, 2.4s, 3.0s com selo "Delegável".
  - y = 1560: Karaoke centralizado na base segura.
- **Movimento**: Zoom no fundo (1.05 -> 1.15), partículas de luz flutuando, entrada progressiva com spring.
- **Transição**: Slide suave com desfoque direcional para a cena 1.

### Cena 1 (5.08s a 13.10s | frames 152 a 393) — Dono / O Problema
- **Tipo**: dono
- **Fala**: "Minhas prioridades ficavam sempre para trás porque as microtarefas acumuladas tomavam todo o meu expediente."
- **Composição**: h) Vídeo do dono em tela cheia (dono_1.mp4) com push-in constante e elementos SOMENTE no topo (y 150 a 420), preservando 100% o rosto (y 450 a 1350 intocado).
- **Layout & Posicionamento**:
  - y = 150: Barra de progresso
  - y = 190: Tag / Badge "O PROBLEMA" com glow vermelho/esmeralda suave
  - y = 260 a 400: Card dinâmico superior:
    - 5.38s a 8.5s: "PRIORIDADES FICAVAM PARA TRÁS" com indicador de alerta
    - 8.66s a 12.8s: transmuta para "MICROTAREFAS ACUMULADAS TOMAVAM O EXPEDIENTE" com medidor animado de sobrecarga
  - y = 1560: Karaoke na base segura.
- **Movimento**: Câmera push-in (scale 1.00 -> 1.06) no vídeo do dono, microanimações no card superior.
- **Transição**: Zoom-through sutil para a interface mobile da cena 2.

### Cena 2 (12.75s a 19.87s | frames 382 a 596) — Conversa / Como Funciona
- **Tipo**: conversa
- **Fala**: "Você transfere essa rotina para o agente de inteligência artificial, e ele faz as tarefas por você."
- **Composição**: b) Celular 3D inclinado (rotateY -12°, perspective 1200px) com mockup mobile premium (largura 860px), chat WhatsApp com mensagens reais e selo "Simulação".
- **Layout & Posicionamento**:
  - y = 150: Barra de progresso
  - y = 190: Badge "COMO FUNCIONA • DELEGAÇÃO EM AÇÃO"
  - y = 280 a 1400: Mockup de celular 3D estilizado:
    - Top bar com avatar de IA, nome "Agente Pessoal IA" e selo "Simulação" (obrigatório)
    - 13.24s: Mensagem 1 (Cliente, direita): "Pode fazer o agendamento da reunião e a pesquisa de mercado?" (fonte 34px)
    - 14.89s: Indicador "digitando..." animado com 3 pontos sincronizados
    - 16.07s: Mensagem 2 (Empresa/IA, esquerda): "Claro! Tarefas assumidas. Já estou iniciando a pesquisa e organizando o agendamento." (fonte 34px)
    - 17.50s: Mensagem 3 (Empresa/IA, esquerda): "Tudo pronto por aqui. Pesquisa concluída e reunião agendada na sua pauta." com check duplo azul
  - y = 1560: Karaoke na base segura.
- **Movimento**: Rotação suave do celular 3D (-14° a -8°), escala suave (1.02 -> 1.07), balões de chat surgindo com mola amortecida.
- **Transição**: Wipe de luz esmeralda rápida para a cena 3.

### Cena 3 (19.52s a 27.55s | frames 585 a 826) — Dono / O Resultado
- **Tipo**: dono
- **Fala**: "Eu consigo terminar o dia com foco total no negócio, delegando qualquer coisa chata da rotina."
- **Composição**: h) Vídeo do dono em tela cheia (dono_3.mp4) com push-in constante e elementos SOMENTE no topo (y 150 a 420), mantendo a cabeça/rosto 100% livres.
- **Layout & Posicionamento**:
  - y = 150: Barra de progresso
  - y = 190: Tag / Badge "O RESULTADO" em verde esmeralda com brilho
  - y = 260 a 400: Card dinâmico superior:
    - 19.81s a 23.5s: "FOCO TOTAL NO NEGÓCIO" com ícone de meta e produtividade
    - 23.76s a 27.2s: "ROTINA CHATA DELEGADA" com selo de eficiência
  - y = 1560: Karaoke na base segura.
- **Movimento**: Push-in contínuo (scale 1.00 -> 1.06), partículas ascendentes de sucesso/foco.
- **Transição**: Desfoque radial com fade para o cartão final.

### Cena 4 (27.20s a 31.14s | frames 816 a 935) — Cartão Final
- **Tipo**: cartao
- **Fala**: "Chame a gente no direct."
- **Composição**: Cartão final dinâmico, moderno e de alta conversão.
- **Layout & Posicionamento (Safe Zone 150 a 1580)**:
  - Fundo: img_4 com desfoque cinematográfico + gradiente escuro de marca + orbs pulsantes
  - y = 150: Barra de progresso completa
  - y = 280 a 380: Marca em destaque "Agentes de IA" (fonte 64px, bold 900) + Tag "AGENTE PESSOAL IA"
  - y = 460 a 640: Card de proposta de valor: "Delegue tarefas reais a um agente IA. Pesquisa, agendamento, follow-up, qualquer coisa." (fonte 36px)
  - y = 740 a 920: Botão de ação pulsando (scale 1.00 a 1.07 com ciclo de mola contínuo):
    - Fundo verde #10B981, texto branco 46px: "CHAME NO DIRECT" + ícone de direct + brilho passando (shimmer)
  - y = 1020 a 1120: Perfil oficial "@agentesdeia.ia" em destaque com badge de verificação
  - Sem legenda karaokê nesta cena.
- **Movimento**: Fundo com push lento (1.08 -> 1.18), pulsação contínua no CTA, feixes de luz cruzando a tela.
