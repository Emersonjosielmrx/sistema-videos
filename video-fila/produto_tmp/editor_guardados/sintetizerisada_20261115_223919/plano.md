# Plano de Edição — Agenda IA (sintetizerisada_20261115_223919)

## 1. Identidade e Parâmetros
- **Produto**: Agenda IA
- **Duração**: 32.04 s (962 frames a 30 fps)
- **Cores**: 
  - Marca / Destaque: `#FFA94D` (Âmbar vibrante)
  - Apoio / Fundo escuro: `#1F2937` (Cinza ardósia escuro)
  - Texto sobre marca: `#1F2937`
  - Texto principal: `#FFFFFF`
- **Safe Zone**: x: 60 a 1020 px, y: 150 a 1580 px. Tipografia rigorosamente >= 32 px.
- **Áudio**: narracao.mp3 contínua do início ao fim; trilha.mp3 de fundo com volume 0.09 (fala) e fade in/out.
- **Karaokê**: componente oficial `Karaoke` da base em y=1560 (base=360), ativo nas cenas 0, 1, 2 e 3 (desativado no cartão final).
- **Barra de Progresso**: posicionada em y=150, preenchimento contínuo 0 a 100% na cor da marca.

---

## 2. Roteiro por Cena

### Cena 0 (0.00s – 5.05s | Frames 0 – 152) — `pergunta`
- **Composição**: a) Texto GIGANTE cinético tela cheia + gancho visual forte nos primeiros 2s.
- **Fundo**: `img_0.jpg` com push-in contínuo (zoom 1.00 -> 1.08) e vinheta escura suave.
- **Elementos Visuais**:
  - Topo (y=180): Selo animado "AGENDA IA • CLÍNICAS E CONSULTÓRIOS" (entra em 0.2s com spring).
  - Centro (y=500 a 1120): Texto cinético escalonado conforme a locução:
    - 0.3s: "CLIENTE DESMARCA" (Branco 62px, Bold)
    - 1.2s: "À NOITE..." (Destaque Âmbar `#FFA94D` 66px em cápsula)
    - 2.0s: "E VOCÊ PERDE A MANHÃ" (Branco 54px)
    - 2.8s: "RESOLVENDO?" (Âmbar `#FFA94D` 72px com pulso sutil)
  - Card de contexto noturno (y=1180): Notificação simulada de alerta às 22:45 com micro-animação de flutuação.
- **Karaokê**: Ativo com destaque `#FFA94D`.
- **Transição**: Crossfade dinâmico com scale punch nos frames 141-152.

### Cena 1 (4.70s – 12.73s | Frames 141 – 382) — `dono`
- **Composição**: h) Vídeo cheio do apresentador com câmera em push (zoom 1.00 -> 1.055) e card de comparativo no topo seguro (y=160 a 410). Rosto e tronco 100% livres (y=440 a 1300).
- **Vídeo**: `dono_1.mp4` em tela cheia (`OffthreadVideo` mudo).
- **Elementos Visuais (Topo Informativo y=165 a 410)**:
  - Selo fixo: "A SITUAÇÃO" com badge ardósia/âmbar.
  - Fase 1 (4.7s a 8.8s): Card de alerta "ANTES: PEDIDOS DE TROCA" + "Mensagens acumuladas no WhatsApp" (vermelho/âmbar).
  - Fase 2 (8.9s a 12.7s): Transição no momento em que fala "Hoje tudo se resolve enquanto descanso" -> Card "HOJE: TUDO RESOLVIDO" + "Reagendamentos automáticos no descanso" (verde/âmbar).
- **Karaokê**: Ativo na base (y=1560).
- **Transição**: Crossfade suave com sobreposição nos frames 371-382.

### Cena 2 (12.38s – 20.56s | Frames 371 – 617) — `dono`
- **Composição**: h) Vídeo cheio do apresentador com movimento lento de aproximação (zoom 1.02 -> 1.07) e card dinâmico de automação no topo seguro (y=160 a 420).
- **Vídeo**: `dono_2.mp4` em tela cheia (`OffthreadVideo` mudo).
- **Elementos Visuais (Topo Informativo y=165 a 420)**:
  - Selo: "COMO FUNCIONA • IA ATIVA" com pulso sutil de radar.
  - Fase 1 (12.38s a 16.0s): "IMPREVISTO À NOITE?" + "Sem recepção humana no horário".
  - Fase 2 (16.05s a 20.56s): Ativação imediata na fala "a Agenda IA reagenda..." -> Card iluminado "AGENDA IA REAGENDA SOZINHA" + "Direto pelo WhatsApp • 24 horas" com badge de WhatsApp IA ativo.
- **Karaokê**: Ativo na base (y=1560).
- **Transição**: Crossfade nos frames 606-617.

### Cena 3 (20.21s – 28.40s | Frames 606 – 852) — `dono`
- **Composição**: h) Vídeo cheio do apresentador com push sutil (zoom 1.00 -> 1.05) e card de resultado profissional no topo seguro (y=160 a 420).
- **Vídeo**: `dono_3.mp4` em tela cheia (`OffthreadVideo` mudo).
- **Elementos Visuais (Topo Informativo y=165 a 420)**:
  - Selo: "O RESULTADO • EXPEDIENTE LIVRE" com ícone de check.
  - Fase 1 (20.21s a 25.5s): "FOCO TOTAL NO ATENDIMENTO" + "Comece o dia com a agenda pronta".
  - Fase 2 (25.56s a 28.4s): Ativação em "sem precisar tocar no celular..." -> Card "ZERO TEMPO NO CELULAR" + "Manhã livre de mensagens operacionais".
- **Karaokê**: Ativo na base (y=1560).
- **Transição**: Desmonte e transição fluida para o cartão final nos frames 842-852.

### Cena 4 (28.05s – 32.04s | Frames 842 – 962) — `cartao`
- **Composição**: Encerramento minimalista de agência, vivo e unificado.
- **Fundo**: `img_4.jpg` com push-in (1.00 -> 1.07) e gradiente escuro de prestígio (`rgba(31,41,55,0.92)` a `rgba(15,23,42,0.96)`).
- **Elementos Visuais**:
  - Topo (y=280): Badge "SOLUÇÃO INTELIGENTE DE AGENDAMENTO".
  - Marca (y=430): "AGENDA IA" (86px, ultra-bold, branco com glow âmbar).
  - Card de Benefícios Fatos (y=620 a 860): 3 pontos fiéis ao briefing:
    - "✓ Agendamentos automáticos 24h"
    - "✓ Direto no WhatsApp sem conflito de horários"
    - "✓ Sem duplo agendamento"
  - Botão CTA Pulsante (y=990 a 1130):
    - Texto: "CHAME NO DIRECT" (52px, bold, `#1F2937`)
    - Fundo: Âmbar vibrante `#FFA94D` com pulso contínuo (scale 1.00 a 1.055) e efeito shimmer percorrendo o botão.
  - Arroba (y=1230): Badge fosco com "@sintetizerisada" (44px, bold).
  - Rodapé (y=1390): "Clínicas • Consultórios • Salões • Profissionais" (32px).
- **Karaokê**: Oculto no cartão final (conforme especificação do manual).

---
## 3. Verificações de Conformidade
- [x] Safe Zone rigorosa (y=150 a 1580, x=60 a 1020)
- [x] Tipografia mínima >= 32 px (títulos 48-86px, corpo 34-44px)
- [x] Contraste >= 4.5:1 com caixas de apoio e pílulas
- [x] Movimento contínuo em todas as camadas (zero estático por > 1s)
- [x] Fatos estritos sem invenção de dados
- [x] Rosto do apresentador 100% desobstruído
