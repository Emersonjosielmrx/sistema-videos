# Plano de Edição — sintetizerisada_20261110_061444 (Agenda IA)

## Análise de Ativos Visuais
- `img_0.jpg`, `img_1.jpg`, `img_2.jpg`, `img_4.jpg`: Recepção de clínica moderna iluminada, recepcionista de perfil à esquerda/centro (x: 200..620, y: 650..1350). Para garantir diversidade visual total e evitar repetição (Regra 16 do APRENDIDO.md), cada cena usará enquadramentos, recortes geométricos, máscaras e composições de fundo completamente distintos.
- `dono_3.mp4`: Apresentador no centro (rosto em y: 450..880, tronco até y: 1450). Zona livre para gráficos: topo (y: 150..420) e legenda na base (y <= 1560).

## Cenas e Composições (4+ composições distintas, sem repetição seguida)

### Cena 0 (0.00s – 5.70s) | Tipo: `pergunta` | Composição: (a) Texto Cinético Gigante + Card de Agenda Esburacada
- **Fala:** "Como evitar buracos na agenda quando o cliente desmarca em cima da hora?"
- **Visual & Câmera:** `img_0.jpg` com push-in dinâmico (scale 1.0 -> 1.12) e pan lateral, filtro escuro nos 42% superiores para leitura perfeita, mantendo a recepção visível e clara abaixo.
- **Elementos Sincronizados:**
  - 0.1s: Pílula de alerta no topo (y=165) com o `gancho_tela`: "Agenda vazia por cancelamento repentino?".
  - 0.3s: Título cinético grande (54px, balanceado) palavra por palavra sincronizado com `palavras` da cena 0, destacando "BURACOS NA AGENDA" e "DESMARCA" na cor `#FFA94D`.
  - 1.5s ('agenda') a 3.3s ('desmarca'): Card visual flutuante no lado direito superior/médio (livre da recepcionista) mostrando 3 horários do dia (09:00, 14:00, 16:00) onde o horário das 14:00 sofre um efeito de cancelamento/vago em tempo real quando a voz diz "desmarca em cima da hora" (2.78s).
- **Transição:** Wipe diagonal energético na cor da marca (`#FFA94D` + `#1F2937`) em 5.35s–5.70s.

### Cena 1 (5.35s – 13.97s) | Tipo: `imagem` (O problema) | Composição: (c) Tela Dividida Antes x Depois Horizontal + Comparativo de Custo
- **Fala:** "Eu ficava com horários vagos por cancelamento repentino. Hoje a IA confirma tudo com antecedência."
- **Visual & Câmera:** Divisão Antes x Depois com movimento contínuo (>10% de variação entre 20% e 80% da cena).
- **Elementos Sincronizados:**
  - 5.4s: Rótulo "O PROBLEMA" -> "A VIRADA" no topo (y=165).
  - 5.8s ('Eu ficava com horários vagos...'): Metade Esquerda (ANTES) acende com card escuro/avermelhado mostrando "Horários Vagos", "Cancelamento repentino" e "Recepção humana: R$ 2.500/mês".
  - 9.18s ('Hoje a IA confirma tudo com antecedência'): Linha divisória luminosa varre e destaca a Metade Direita (HOJE COM AGENDA IA) em `#FFA94D` e `#1F2937`, mostrando checkmarks animados: "Confirma com antecedência", "Trabalha 24h no WhatsApp" e "A partir de R$ 199/mês".
- **Transição:** Zoom-through 3D mergulhando no painel do WhatsApp em 13.62s–13.97s.

### Cena 2 (13.62s – 22.39s) | Tipo: `conversa` (Como funciona) | Composição: (b) Celular Inclinado 3D + Badges Laterais Sincronizados
- **Fala:** "A Agenda IA confirma e reagenda sozinha direto no WhatsApp, vinte e quatro horas, sem conflito."
- **Visual & Câmera:** Fundo escuro tecnológico `#1F2937` com recorte circular suave de ambiente e grade dinâmica + Celular grande (altura 980px, y=340..1320) com leve rotação 3D e flutuação contínua.
- **Elementos Sincronizados:**
  - Topo (y=160..310): Rótulo "COMO FUNCIONA" + 3 pílulas de benefícios que acendem no tempo exato da fala: `15.92s` ("Confirma e reagenda"), `19.09s` ("Atendimento 24h"), `20.24s` ("Sem conflito").
  - Dentro do Celular (Selo "Simulação" >= 32px, todas as fontes >= 32px): As 5 mensagens do briefing entram uma a uma (14.0s, 15.3s, 16.8s, 18.4s, 19.8s) com indicador "digitando..." antes das respostas da empresa e scroll suave.
- **Transição:** Slide vertical suave revelando o vídeo do dono em 22.04s–22.39s.

### Cena 3 (22.04s – 30.07s) | Tipo: `dono` (O resultado) | Composição: (h) Vídeo Real em Tela Cheia + HUD Superior Sincronizado
- **Fala:** "Meus agendamentos automáticos funcionam dia e noite, sem duplo agendamento e com a agenda organizada."
- **Visual & Câmera:** `<OffthreadVideo src={staticFile('dono_3.mp4')} muted />` com zoom lento contínuo (1.0 -> 1.07). Rosto do apresentador (y=450..900) 100% livre.
- **Elementos Sincronizados (Apenas na faixa y=155..410):**
  - 22.1s: Rótulo "O RESULTADO" + Card HUD horizontal no topo.
  - Os 3 pilares acendem um por um no exato instante da voz:
    1. `22.52s` ("agendamentos automáticos / dia e noite") -> Badge "01 • Dia e Noite (24h)"
    2. `26.24s` ("sem duplo agendamento") -> Badge "02 • Sem Duplo Agendamento"
    3. `28.20s` ("agenda organizada") -> Badge "03 • Agenda Organizada"

### Cena 4 (29.72s – 33.72s) | Tipo: `cartao` (CTA Final) | Composição: (f) Cartão Final de Agência com Recorte Geométrico e Botão Pulsante
- **Fala:** "Chame a gente no direct."
- **Visual & Câmera:** Fundo em `#1F2937` com luzes em movimento + `img_4.jpg` em recorte arqueado/desfocado com zoom contínuo (1.0 -> 1.12). Sem legenda Karaokê.
- **Elementos Sincronizados (y=200..1450):**
  - Marca "AGENDA IA" gigante em destaque + subtítulo "Agendamentos automáticos 24h no WhatsApp".
  - Card de destaque com os fatos: "Confirma e reagenda sozinha • A partir de R$ 199".
  - Botão CTA grande pulsando continuamente: "CHAME A GENTE NO DIRECT" (alinhado com `convite_voz` e `convite`) + brilho passando.
  - Arroba `@sintetizerisada` em pílula de alto contraste (y=1320).
