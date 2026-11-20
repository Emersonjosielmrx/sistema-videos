# Plano de Edição — vitrineia_inovare_20261120_010728

Produto: Vitrine IA
Duração total: 30.58 s (918 frames @ 30 fps)
Cores: Marca `#A78BFA`, Fundo Escuro `#111827`, Destaque `#A78BFA`, Texto sobre Marca `#121216`
Padrão de Qualidade: Motion design profissional de agência para Reels/TikTok (9:16 vertical).

---

## Barra Global e Áudio
- Barra de progresso contínua no topo em `y = 150` (altura 6 px, cor `#A78BFA` com brilho sutil).
- Áudio da narração contínuo (`narracao.mp3`).
- Trilha sonora contínua (`trilha.mp3`), com volume dinâmico: 0.10 durante falas, 0.20 em pausas e fade out suave nos últimos 1.5s.
- Legenda Karaokê (`../../lib/karaoke`) ancorada em `base = 360` (base em `y = 1560`), com quebra forçada por cena e desligada no cartão final.

---

## Cena 0 (0.00s – 4.83s, frames 0 – 145) — Tipo: `pergunta`
- **Composição:** (a) Texto GIGANTE tela cheia cinético com destaque marca-texto sobre foto ambientada.
- **Fundo:** `img_0.jpg` com push-in de câmera (scale 1.00 -> 1.12) e leve pan vertical, escurecimento com overlay gradiente protetor (contraste > 4.5:1).
- **Elementos e Sincronização:**
  - 0.0s – 0.3s: Badge superior com corte diagonalchanfrado "DÚVIDA FREQUENTE" em `y = 190`.
  - 0.3s ("Vou parar de"): Título principal entra com scale spring em `y = 480`: "VOU PARAR DE" (branco, 62px, peso 900).
  - 1.0s ("perder cliente"): Linha de alto impacto surge em `y = 570`: "PERDER CLIENTE" em destaque na caixa `#A78BFA` com texto `#121216` (68px).
  - 2.0s ("por demora"): Surge caixa vermelha/laranja de alerta "POR DEMORA" (60px) em `y = 670`.
  - 2.5s ("no atendimento?"): Complementa "NO ATENDIMENTO?" (58px) em `y = 760`.
  - 3.2s: Selo fixo do gancho surge suavemente: "Cliente some por demora?" com ícone de relógio pulsante.
- **Transição para Cena 1 (4.5s):** Zoom-through com fade rápido dos elementos de texto.

---

## Cena 1 (4.48s – 12.67s, frames 134 – 380) — Tipo: `dono`
- **Composição:** (h) Vídeo cheio (`dono_1.mp4`) com câmera viva e overlays informativos estritamente no topo (`y = 170 – 430`), preservando 100% o rosto do apresentador (rosto entre `y = 580 – 1100`).
- **Vídeo:** `<OffthreadVideo src={staticFile('dono_1.mp4')} muted />` em tela cheia com leve zoom contínuo (1.00 -> 1.05).
- **Elementos e Sincronização:**
  - 4.5s – 5.2s: Badge translúcido com corte diagonal (item aprovado 28a1924f) em `y = 180`: "O PROBLEMA · RELATO REAL".
  - 5.3s – 8.6s ("Eu perdia venda toda vez que demorava a responder"): Card flutuante compacto no topo (`y = 260 – 410`, largura 960px) com glassmorphism:
    - Ícone de tempo em alerta + frase: "DEMORA NA RESPOSTA = CLIENTE PERDIDO" (fonte 40px bold).
  - 9.6s – 12.6s ("O cliente esperava pouco e ia comprar em outra loja"): Transição suave do card superior para:
    - "SEM RESPOSTA RÁPIDA, O CLIENTE COMPRA NO CONCORRENTE" com tag visual de aviso.
  - Karaokê na base (`y = 1560`), posicionado sobre o peito/camisa escura, sem encostar no rosto.
- **Transição para Cena 2 (12.3s):** Desfoque e slide suave para entrada do mockup mobile.

---

## Cena 2 (12.32s – 20.56s, frames 370 – 617) — Tipo: `conversa`
- **Composição:** (b) Mockup de Celular 3D (perspectiva com `rotateY(10deg)` e `rotateX(4deg)`) com balões de conversa reais do WhatsApp entrando sincronizados com a fala.
- **Fundo:** `img_2.jpg` com blur suave (12px), véu escuro e push-in constante (scale 1.05 -> 1.15).
- **Elementos e Sincronização:**
  - 12.3s: Badge no topo em `y = 175`: "COMO FUNCIONA · ATENDIMENTO INTELIGENTE".
  - 12.5s: Celular surge com spring suave ocupando o centro da tela (`y = 270 – 1260`, altura ~940px, largura ~620px), com moldura realista, dynamic island e selo discreto "Simulação" no topo.
  - 12.8s ("O cliente pergunta por uma sandália"): Balão 1 do cliente entra pelo lado esquerdo: "Oi! Vocês têm sandália confortável para o dia a dia?" (fonte 34px).
  - 14.5s: Indicador animado "digitando..." do bot.
  - 14.8s ("e o bot, que conhece os produtos da loja"): Balão 2 da Vitrine IA entra pelo lado direito em tom roxo translúcido: "Temos sim! Conheço todos os modelos da loja. Prefere salto baixo ou rasteira?" (fonte 34px).
  - 17.0s ("responde na hora"): Badge de status "⚡ Resposta imediata" pulsa no celular.
  - 18.1s ("e já indica o modelo"): Balão 3 (cliente: "Rasteira, de preferência") e Balão 4 (bot: "Então recomendo a rasteira de couro. Quer que eu separe o seu tamanho?") entram com rolagem natural.
- **Transição para Cena 3 (20.2s):** Wipe com máscara angular e desintegração suave do celular.

---

## Cena 3 (20.21s – 26.99s, frames 606 – 810) — Tipo: `imagem`
- **Composição:** (e/g) Vitrine de Resultados: Cards dinâmicos escalonados com benefícios concretos e dados do briefing entrando no ritmo da voz.
- **Fundo:** `img_3.jpg` com pan horizontal e zoom suave (scale 1.02 -> 1.14), iluminação com vinheta radial elegante.
- **Elementos e Sincronização:**
  - 20.2s: Tarja chanfrada no topo em `y = 180`: "O RESULTADO NA PRÁTICA".
  - 20.7s ("Hoje o bot atende na hora"): Card 1 desliza com spring da esquerda em `y = 380`:
    - "✓ ATENDIMENTO NA HORA" com subtítulo "Zero fila de espera no WhatsApp e Direct" (fonte 36px).
  - 22.4s ("e eu deixo de perder cliente"): Card 2 desliza da direita em `y = 600`:
    - "✓ RETENÇÃO DE CLIENTES" com subtítulo "Quem tem pressa compra da sua loja" (fonte 36px).
  - 24.2s ("que só queria uma resposta rápida"): Card 3 surge com escala central em `y = 820`:
    - "✓ CONHECIMENTO COMPLETO DA LOJA" com subtítulo "Atende, recomenda e fecha a venda" (fonte 36px).
  - Efeito de brilho (shimmer) contínuo percorrendo os cards até o corte.
- **Transição para Cena 4 (26.6s):** Zoom-in acelerado com flash suave para a tela de ação.

---

## Cena 4 (26.64s – 30.58s, frames 799 – 918) — Tipo: `cartao` (CTA)
- **Composição:** Cartão final dinâmico, vivo e profissional.
- **Fundo:** `img_4.jpg` com desfoque artístico (20px), véu escuro na paleta da marca (`rgba(17, 24, 39, 0.88)`), partículas e luz ambiente pulsante.
- **Elementos:**
  - Topo (`y = 440`): Logo/marca em destaque "VITRINE IA" (tamanho 80px, peso 900, `#A78BFA` com glow suave).
  - Centro (`y = 660 – 820`): Proposta de valor oficial do briefing:
    - "Bot com todo o conhecimento da sua loja."
    - "Atende, recomenda e vende." (fonte 44px, branco, alto contraste).
  - CTA Principal (`y = 1060 – 1220`):
    - Botão magnético com animação contínua de pulso (`scale 1.00 -> 1.06` em loop senoidal):
    - Texto exato da fala do convite: "CHAME NO DIRECT" (fonte 50px bold, cor `#121216` sobre fundo `#A78BFA`).
    - Shimmer/brilho diagonal passando pelo botão.
  - Perfil oficial (`y = 1340`):
    - Badge estilizado com `@vitrineia_inovare` (fonte 40px, com ícone de direct/mensagem).
  - Sem karaokê nesta cena (foco 100% no CTA).
