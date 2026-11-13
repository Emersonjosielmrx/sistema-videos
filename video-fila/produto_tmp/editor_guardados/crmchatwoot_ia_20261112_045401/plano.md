# Plano de Edição — CRM Chatwoot IA (`crmchatwoot_ia_20261112_045401`)

## Identidade e Diretrizes
- **Produto:** CRM Chatwoot IA
- **Duração total:** 30.18s (906 frames a 30 fps)
- **Cores principais:**
  - Azul Marca/Destaque: `#1F93FF`
  - Fundo Escuro / Apoio: `#111827`
  - Branco Texto: `#FFFFFF`
  - Glassmorphism translúcido: `rgba(17, 24, 39, 0.85)`
- **Tipografia:** Montserrat (via `@remotion/google-fonts/Montserrat`), pesos 600, 700, 900. Textos rigorosamente ≥ 32px (títulos ≥ 48px).
- **Safe Zone:** y entre 150 e 1580; x entre 60 e 1020 (margem lateral mínima de 60px).
- **Karaokê:** Componente padrão `Karaoke` (`src/lib/karaoke.tsx`), base 360 (y ≤ 1560), sem legenda no cartão final.
- **Movimento contínuo:** Nenhum elemento estático > 1.5s; zooms contínuos em fundos (1.0 -> 1.08), microinterações, brilhos e transições com mola.

---

## Cena 0 — Gancho / Pergunta (0.00s a 5.39s | Frames 0 a 162)
- **Tipo:** `pergunta`
- **Fala:** "Cansado de CRM engessado que sua equipe não consegue usar?"
- **Composição:** Tipo a) Texto GIGANTE tela cheia com destaque visual sobre foto escurecida com zoom lento (1.0 -> 1.07).
- **Fundo:** `img_0.jpg` com push-in suave e vinheta lateral protegendo a pessoa (mulher trabalhando ao fundo/direita).
- **Elementos gráficos:**
  - Topo (y=180): Badge animado com glow: `ALERTA DE PRODUTIVIDADE`.
  - Centro (y=450 a 900): Container glassmorphic escuro de alto contraste:
    - Linha 1 (0.3s na palavra "Cansado"): "CANSADO DE" (font-size 52px, branco).
    - Linha 2 (0.95s na palavra "CRM" e 1.6s "engessado"): "CRM ENGESSADO" com pílula de marca-texto azul `#1F93FF` em escala com mola (spring).
    - Linha 3 (2.5s na palavra "equipe" / "não consegue usar"): "QUE SUA EQUIPE NÃO CONSEGUE USAR?" (font-size 44px, cor `#E2E8F0`).
  - Grafismo de suporte: Ícone de alerta animado com pulsação suave.
- **Transição de saída:** Wipe vertical suave com desfoque de movimento para a Cena 1.

---

## Cena 1 — O Problema (5.04s a 12.29s | Frames 151 a 369)
- **Tipo:** `imagem`
- **Fala:** "Sistemas prontos costumam complicar o trabalho diário com telas difíceis que ninguém na empresa preenche."
- **Composição:** Tipo e) Pilha de cards de impacto entrando escalonados sobre foto com pan sutil e motion design de telas difíceis.
- **Fundo:** `img_1.jpg` com leve pan horizontal e scale lento (1.02 -> 1.08).
- **Elementos gráficos:**
  - Topo (y=180): Rótulo badge `O PROBLEMA` em cápsula escura com borda vermelha/âmbar sutil.
  - Título de impacto (y=270): "SISTEMAS PRONTOS COMPLICAM" (font-size 46px).
  - Cards empilhados (y=440 a 1100):
    - **Card 1** (entra aos 6.0s na palavra "prontos"): "Sistemas engessados e genéricos" + ícone de trava / bloqueio.
    - **Card 2** (entra aos 8.6s na palavra "telas difíceis"): "Telas complexas e confusas" + barra com campos vazios ilustrando atrito.
    - **Card 3** (entra aos 10.0s na palavra "ninguém preenche"): "Baixa adesão da equipe" + indicador de preenchimento 0%.
- **Transição de saída:** Slide diagonal com zoom coordenado para a Cena 2.

---

## Cena 2 — Como Funciona (11.94s a 19.99s | Frames 358 a 600)
- **Tipo:** `conversa`
- **Fala:** "Nós criamos uma solução sob medida com inteligência artificial, unindo helpdesk e atendimento na mesma tela."
- **Composição:** Tipo b) Celular moderno em perspectiva 3D (rotateY ~14deg) com interface realista de atendimento integrado Chatwoot IA.
- **Fundo:** `img_2.jpg` com zoom cinematográfico e overlay escuro gradiente.
- **Elementos gráficos:**
  - Topo (y=180): Rótulo badge `COMO FUNCIONA` em azul `#1F93FF`.
  - Header do Celular (y=300): Barra de app com logo "CRM Chatwoot IA", status "Atendimento com IA Ativo", badge "Simulação" discreto.
  - Balões de conversa sincronizados (font-size 32px para legibilidade perfeita):
    - Mensagem 1 (12.8s): Cliente: "Preciso de ajuda com a entrega do meu pedido anterior."
    - Indicador (14.7s na fala "inteligência artificial"): "IA buscando histórico e tickets..." (três pontos pulsantes).
    - Mensagem 2 (16.3s na fala "unindo helpdesk"): Empresa: "Localizei o chamado aberto aqui. Já estou transferindo para o responsável."
    - Mensagem 3 (18.2s na fala "mesma tela"): Cliente: "Perfeito, muito obrigado pelo retorno rápido!"
  - Badge lateral flutuante (17.2s): "Helpdesk + CRM Integrados ✓".
- **Transição de saída:** Zoom-through suave na tela do smartphone em direção à solução.

---

## Cena 3 — O Resultado (19.64s a 26.59s | Frames 589 a 798)
- **Tipo:** `imagem`
- **Fala:** "Sua rotina fica mais leve com processos adaptados exatamente ao jeito que você já trabalha."
- **Composição:** Tipo g) Grade/Checklist dinâmico de 3 pilares de produtividade adaptados com checkmarks animados e barras de fluidez sobre foto em movimento.
- **Fundo:** `img_3.jpg` com movimento suave de câmera (push-in 1.0 -> 1.07).
- **Elementos gráficos:**
  - Topo (y=180): Rótulo badge `O RESULTADO` em azul marca `#1F93FF`.
  - Título focal (y=270): "SUA ROTINA MAIS LEVE" (font-size 50px, peso 900).
  - Tópicos sequenciais revelados com mola (spring) à medida que a narração avança:
    - Item 1 (entra aos 20.4s na fala "rotina mais leve"): "Processos adaptados ao seu fluxo" (ícone de engrenagem sincronizada).
    - Item 2 (entra aos 22.0s na fala "processos adaptados"): "Histórico e tickets unificados" (ícone de pasta inteligente).
    - Item 3 (entra aos 23.5s na fala "jeito que você já trabalha"): "Produtividade real para o time" (ícone de raio/velocidade).
- **Transição de saída:** Crossfade dinâmico com blur para o cartão de encerramento.

---

## Cena 4 — Cartão Final / CTA (26.24s a 30.18s | Frames 787 a 906)
- **Tipo:** `cartao`
- **Fala:** "Chame a gente no direct."
- **Composição:** Cartão final profissional de agência, vivo, com microinterações constantes.
- **Fundo:** `img_4.jpg` desfocada (blur 16px) com véu escuro gradiente azul marinho (`rgba(17, 24, 39, 0.88)`), glow dinâmico de fundo.
- **Elementos gráficos:**
  - Logo/Marca principal (y=420): "CRM CHATWOOT IA" em letras imponentes (64px, bold 900) com brilho gradiente azul/branco e ícone tecnológico integrado.
  - Frase de valor (y=620): "Atendimento, tickets e histórico em um só lugar." (font-size 36px, cor `#CBD5E1`, textWrap balance).
  - Botão CTA pulsante com shimmer animado (y=920, altura 110px, largura 780px):
    - Texto (42px, peso 900): "CHAME NO DIRECT" (alinhado rigorosamente à locução "Chame a gente no direct").
    - Efeito de pulso de escala (1.0 -> 1.04 em loop sinusoidal).
  - Handle / Conta oficial (y=1120): `@crmchatwoot.ia` (font-size 36px, peso 700, cor `#94A3B8`).
  - Sem karaokê nesta cena final.
