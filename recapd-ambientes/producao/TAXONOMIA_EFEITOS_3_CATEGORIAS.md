# 🎬 TAXONOMIA DE EFEITOS — 3 categorias (separação pedida pela usuária 2026-06-30)

> A usuária notou (com razão) que eu estava misturando coisas de naturezas diferentes sob
> "transições". Separando em 3 categorias claras pra organizar o sistema e guiar o que criar.
> Base: análise de 1688 falas + 1633 descrições dos narration_cache.

---

## 📐 As 3 categorias

### CAT 1 — TRANSIÇÃO REAL (no CORTE, entre painel A→B)
Acontece NO BOUNDARY entre dois painéis. Cobre/varre/revela a tela — só faz sentido na troca.
É a "transição de fato". Hoje aplicada via `elemental_transitions.apply()` centrada no corte.

### CAT 2 — OVERLAY ATMOSFÉRICO (EM CIMA do painel, enquanto ele aparece)
Roda SOBRE o painel durante a exibição dele (não no corte). Dá clima/ambiente: partículas,
clima, luz. É decorativo e contínuo. Precisa de um gancho DIFERENTE (durante o clip, não no boundary).

### CAT 3 — ANIMAÇÃO INTERATIVA / ENGAJAMENTO (em cima do painel, elemento de UI/reação)
Sobreposições estilo TikTok/YouTube: botão de like que pulsa, "inscreva-se", setinha, emojis
reativos, enquete. Servem a 2 propósitos: (a) reação emocional do personagem (anime), (b) CTA
de engajamento do canal. A usuária citou o exemplo do "deixe seu like".

---

## 🗂️ Classificação dos 39 efeitos atuais

### CAT 1 — Transição real (no corte) — 18
tear, tvoff, glitch, swipelight, inkblot, blinds, cinebars, radialzoom, speedlines,
fire, water, ice, disintegrate, portal, exclaim, impact, shockwave, flashback

### CAT 2 — Overlay atmosférico (em cima do painel) — 16
snow, rain, smoke, leaves, petals, bokeh, wind, bubbles, sparkle, starburst,
fireworks, divine, shadow, lightning, blood, quake

### CAT 3 — Animação reativa/emoção (em cima do painel) — 5
hearts, blush, anger, sweatdrop, question
> Estes hoje são tratados como "transição" mas são REAÇÕES — ficam melhor SOBRE o painel
> da fala correspondente, não no corte. De engajamento puro (like/subscribe) = NENHUM ainda.

### Efeitos que servem em MAIS DE UMA categoria (versáteis)
- **fire / water**: varredura serve de transição (CAT1) E chama/respingo pode ficar de overlay (CAT2)
- **lightning / shockwave**: como impacto no corte (CAT1) ou flash atmosférico sobre o painel (CAT2)
- **sparkle / starburst**: brilho de transição (CAT1) ou over o painel num momento mágico (CAT2)
- **hearts**: reação (CAT3) ou transição romântica fofa no corte (CAT1)
- **portal**: abertura no corte (CAT1) ou vórtice girando sobre o painel (CAT2)

---

## 💡 O QUE FALTA / IDEIAS por categoria (da reanálise dos textos)

### CAT 1 (transição) — bem coberta, poucas faltas
- **pageturn** (virar página de mangá) — clássico do gênero, falta
- **shatter-glass** (vidro estilhaça e revela próximo) — temos disintegrate mas não vidro
- **brushstroke** (pincelada de tinta varre, estilo sumi-e) — combina com obra oriental

### CAT 2 (overlay atmosférico) — brechas reais achadas no texto:
- **noite/estrelas** (41× "noite/escuro/lua") — céu noturno/vagalumes sobre cena noturna
- **sol/raios quentes** (73× "sol/dia/manhã") — god-rays suaves de dia
- **multidão/festa** (93×!) — confete/luzes de balada sobre cena de festa
- **cidade/neon** (47× "cidade/rua") — luzes de cidade/neon piscando
- **calor/verão** (22×) — ondas de calor/cigarras visuais
- **chuva já temos** (rain) ✓

### CAT 3 (engajamento/UI) — categoria NOVA, quase vazia. Gatilhos no texto:
- **cliffhanger (138×!)** — "continua", "será que", "não perca" → seta "inscreva-se p/ ver o resto"
- **pergunta ao público (97×)** — "o que você acha" → balão de enquete/comentário
- Ideias de UI moderna (independente do texto, padrão TikTok/YT Shorts):
  - **like-burst**: coração/joinha que sobe e estoura (a que a usuária viu)
  - **subscribe-pop**: botão "INSCREVA-SE" desliza, pulsa, brilha
  - **follow-arrow**: setinha animada apontando
  - **comment-bubble**: balão de comentário aparece
  - **emoji-rain**: chuva de emojis reativos (😱😍🔥) no momento certo

---

## ⚙️ Implicação técnica (importante)
Hoje TUDO entra pelo mesmo gancho (`elemental_transitions.apply`, overlay centrado NO CORTE).
- CAT 1 funciona certo assim (é no boundary).
- CAT 2 e CAT 3 idealmente deveriam rodar DURANTE o painel (janela = início→fim do clip daquele
  painel), não no corte. Hoje, quando caem via detecção, entram no corte — funciona mas não é o ideal.
- PRÓXIMO PASSO TÉCNICO (quando for editar código, com a janela livre): criar um 2º modo de
  aplicação "overlay durante o painel i" usando `_CLIP_ABS_STARTS[i]`→`[i+1]`, separado do modo
  "transição no corte". Marcar cada efeito com sua categoria no ASSET_FILE (ex: dict com {file, cat}).

## Status
- Classificação: FEITA (acima).
- Criação de novos: AGUARDANDO escolha da usuária de quais ideias seguir (CAT 2 atmosféricos / CAT 3 engajamento).
- Exemplo concreto CAT 3: vou criar o **like-burst** como amostra (a usuária citou o "like").
