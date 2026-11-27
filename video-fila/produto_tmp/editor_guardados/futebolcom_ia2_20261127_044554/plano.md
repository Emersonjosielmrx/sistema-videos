# Plano de Edição — futebolcom_ia2_20261127_044554

**Produto:** Cardápio Digital (Cardápio Digital)  
**Duração:** 30.85s (926 frames @ 30 fps)  
**Identidade Visual:**
- Marca: `#E11D48`
- Apoio: `#FACC15`
- Fundo Escuro: `#31060F`
- Destaque: `#E11D48`
- Texto sobre Marca: `#FFFFFF`

---

## 1. Visão Geral das Cenas e Composição

| Cena | Início (s) | Fim (s) | Tipo | Rótulo / Conteúdo | Composição Adotada |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | 0.00 | 4.26 | Pergunta | "Cliente manda um oi e some sem fazer o pedido?" | **a)** Texto cinético dramático + Mockup flutuante de chat abandonado |
| **1** | 3.91 | 11.69 | Dono | "Eu via o cliente mandar um oi, esperar a resposta..." | **h)** Vídeo dono tela cheia (push 1.00→1.05) + Card dor no topo |
| **2** | 11.34 | 19.52 | Dono | "Hoje o cliente recebe o link, vê as fotos... tira dúvidas com a IA..." | **g)** Vídeo dono (push 1.02→1.07) + Timeline de 3 etapas 1-2-3 acendendo no topo |
| **3** | 19.17 | 27.35 | Dono | "O pedido é confirmado no próprio WhatsApp... cozinha trabalha." | **e)** Vídeo dono (push 1.05→1.01) + Notificação de status e cozinha no topo |
| **4** | 27.00 | 30.85 | Cartão | "Chame a gente no direct." | **Cartão Final** Branding, benefício, botão CTA pulsante e @handle |

---

## 2. Detalhamento Cena a Cena

### Cena 0 (0.00s a 4.26s — frames 0 a 128)
- **Fala:** "Cliente manda um oi e some sem fazer o pedido?"
- **Fundo:** `img_0.jpg` com zoom cinematográfico contínuo (scale 1.00 a 1.08) e vinheta escura profunda `#31060F`.
- **Topo (y=160 a 420):**
  - y=165: Badge com borda e fundo opaco: `ATENDIMENTO NO WHATSAPP`.
  - y=240 a 400: Tipografia cinética sincronizada com a fala:
    - 0.3s a 1.3s: "CLIENTE MANDA UM OI..." (box escuro 90%, destaque em branco).
    - 1.4s a 2.8s: "...E SOME SEM FAZER O PEDIDO?" (box protetor com destaque `#E11D48`).
  - 2.8s em diante: Gancho de tela selo fixo: "Do primeiro oi ao pedido fechado".
- **Centro (y=560 a 1180):**
  - Mockup mobile estilizado em React representando a dor do delivery:
    - Balão de mensagem cliente: "Oi, boa noite! Tem cardápio?" às 19:42 com 2 tiques cinzas.
    - Indicador de espera: "Sem resposta... cliente desistiu" com ícone de alerta sutil.
    - Selo obrigatório discreto: "Simulação".
- **Movimento contínuo:** Movimento contínuo de câmera + flutuação do card de mensagem (rotate/translate) garantindo > 4% de variação entre frame 25 e frame 100.
- **Transição:** Crossfade / overlap dinâmico aos 3.91s.

### Cena 1 (3.91s a 11.69s — frames 117 a 351)
- **Fala:** "Eu via o cliente mandar um oi, esperar a resposta e desistir antes de escolher o que pedir."
- **Arquivo:** `dono_1.mp4` (vídeo mudo em tela cheia, objectFit cover).
- **Rosto livre:** Rosto do apresentador localizado em y ≈ 480 a 1150. Elementos gráficos restritos a y=160 a 420 (respiro > 60px).
- **Topo (y=160 a 420):**
  - y=165: Pill badge `O PROBLEMA` em fundo `#31060F` com borda fina `#E11D48` e micro-pulso.
  - y=240 a 390: Card opaco (90%) com texto dinâmico:
    - 4.7s a 7.5s (palavras "Eu via o cliente mandar um oi"): "CLIENTE MANDA UM OI..."
    - 7.5s a 10.9s (palavras "esperar a resposta e desistir..."): "...ESPERA RESPOSTA E DESISTE DO PEDIDO" em destaque avermelhado.
- **Base (y=1440 a 1560):** Karaokê pronto com espaçamento real e destaque ativo na cor `#E11D48`.
- **Movimento contínuo:** Push de câmera contínuo no vídeo (scale 1.00 a 1.06) + pulso sutil no card.

### Cena 2 (11.34s a 19.52s — frames 340 a 586)
- **Fala:** "Hoje o cliente recebe o link, vê as fotos dos pratos, tira dúvidas com a IA e pede."
- **Arquivo:** `dono_2.mp4` (vídeo mudo em tela cheia).
- **Rosto livre:** Apresentador centralizado com cabeça a partir de y ≈ 460. Elementos em y=155 a 415.
- **Topo (y=155 a 415):**
  - y=160: Pill badge `COMO FUNCIONA: 3 ETAPAS`.
  - y=220 a 395: Painel horizontal com 3 abas / etapas que acendem uma a uma sincronizadas com a fala:
    - Etapa 1 (acende aos 12.2s em "recebe o link"): `1. LINK DO CARDÁPIO`
    - Etapa 2 (acende aos 14.5s em "vê as fotos dos pratos"): `2. FOTOS DOS PRATOS`
    - Etapa 3 (acende aos 16.4s em "tira dúvidas com a IA e pede"): `3. IA & PEDIDO`
  - As etapas inativas ficam com fundo escuro sutil e ao serem citadas recebem destaque imediato em `#E11D48` e borda `#FACC15`.
- **Base (y=1440 a 1560):** Karaokê sincronizado.
- **Movimento contínuo:** Push de câmera contínuo (scale 1.02 a 1.07) + acendimento progressivo das etapas.

### Cena 3 (19.17s a 27.35s — frames 575 a 821)
- **Fala:** "O pedido é confirmado no próprio WhatsApp, e eu deixo de perder venda enquanto a cozinha trabalha."
- **Arquivo:** `dono_3.mp4` (vídeo mudo em tela cheia).
- **Rosto livre:** Apresentador com rosto a partir de y ≈ 480. Elementos em y=160 a 420.
- **Topo (y=160 a 420):**
  - y=165: Pill badge `O RESULTADO`.
  - y=230 a 395: Card de notificação de resultado dinâmico:
    - 19.8s a 23.0s ("O pedido é confirmado no próprio WhatsApp"): "PEDIDO CONFIRMADO NO WHATSAPP" com badge de checkmark verde animado.
    - 23.3s a 26.5s ("eu deixo de perder venda enquanto a cozinha trabalha"): Transição suave para "COZINHA PRODUZINDO SEM PERDER VENDA" com radar pulsante de atividade.
- **Base (y=1440 a 1560):** Karaokê sincronizado.
- **Movimento contínuo:** Push inverso (scale 1.05 a 1.01) + animação de pulso contínuo do status.

### Cena 4 (27.00s a 30.85s — frames 810 a 926)
- **Fala:** "Chame a gente no direct."
- **Fundo:** `img_4.jpg` escurecida com overlay degradê da marca `#31060F` (opacidade 88%) e zoom contínuo (1.00 a 1.08).
- **Sem Karaokê:** Conforme regra do manual, o karaokê cessa no cartão final para foco total no CTA.
- **Estrutura Visual:**
  - y=240 a 360: Título principal da marca: `CARDÁPIO DIGITAL` (fonte 64px, branca, negrito 900) com sub-badge `ATENDIMENTO COM IA & WHATSAPP`.
  - y=410 a 610: Card de benefícios autorizados do briefing: "O cliente vê fotos dos pratos no celular e faz o pedido direto pelo WhatsApp".
  - y=780 a 940: Botão CTA com entrada escalonada e pulso senoidal contínuo (scale 1.00 a 1.07):
    - Texto estritamente correspondente ao convite: `CHAME NO DIRECT` (fonte 48px, bold, fundo `#E11D48`, brilho animado atravessando).
  - y=1020 a 1120: Caixa de contato oficial com `@futebolcom.ia2` (fonte 38px, alto contraste).
- **Movimento contínuo:** Pulso do botão CTA + efeito shimmer/brilho no botão + zoom suave do fundo.

---

## 3. Elementos Globais
- **Barra de Progresso:** Posicionada em y = 150, altura 6px, cor gradiente `#E11D48` para `#FACC15`, avançando suavemente de 0 a 100% ao longo dos 926 frames.
- **Áudio:** `narracao.mp3` toca de 0.0s até o final. `trilha.mp3` em volume 0.10 com ducking e fade-out suave nos últimos 1.5s.
- **Tipografia:** Montserrat, com piso inegociável de 32px para todo e qualquer texto.
