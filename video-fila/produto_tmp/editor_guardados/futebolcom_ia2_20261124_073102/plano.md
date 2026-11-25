# Plano de Edição — Cardápio Digital (ID: futebolcom_ia2_20261124_073102)

- **Produto:** Cardápio Digital
- **Duração:** 31.41 s (943 frames a 30 fps)
- **Paleta de Cores:**
  - Primária (Marca): `#E11D48` (Rose/Vermelho apetite)
  - Apoio / Destaque: `#FACC15` (Amarelo ouro)
  - Fundo Escuro / Véu: `#31060F` (Burgundy profundo)
  - Texto Claro: `#FFFFFF`
- **Tipografia:** Montserrat (`@remotion/google-fonts/Montserrat`), pesos 600, 700, 800, 900.
- **Safe Zone:** y=150 a y=1580; margens laterais x=60 a x=1020.
- **Regras:** Karaokê padrão em y=1560 (base=360), desligado na Cena 4 (cartão final). Pelo menos 4 composições distintas. Movimento contínuo ≥ 4.0% em todas as cenas. Somente fatos do briefing.

---

### Cena 0: A Pergunta (0.00s a 5.31s | Frames 0 a 159)
- **Composição:** **a) Texto GIGANTE tela cheia cinético sobre foto em push-in contínuo**
- **Áudio:** "Seu cliente desiste do pedido quando precisa instalar alguma coisa?"
- **Fundo:** `img_0.jpg` com push-in de câmera (scale 1.05 -> 1.16) e escurecimento graduado com véu da marca `#31060F`.
- **Elementos Visuais:**
  - `0.20s` (frame 6): Badge de alerta no topo (y=175) `🚨 ATENÇÃO RESTAURANTES & DELIVERY`.
  - `0.30s` (frame 9): Texto "SEU CLIENTE" (54px) entra com mola.
  - `0.97s` (frame 29, na palavra "desiste"): "DESISTE DO PEDIDO?" em destaque gigante (72px) com marca-texto `#E11D48` e texto `#FACC15`.
  - `1.80s` (frame 54): Card de atrito com ícone de download barrado ❌ e alerta pulsando: "Exigir download gera desistência imediata".
  - `2.20s` (frame 66): Subtítulo cinético "QUANDO PRECISA INSTALAR ALGO".
  - `2.60s` (frame 78): Gancho fixo superior: "Cliente precisa baixar app?".
- **Câmera / Movimento:** Push-in contínuo na foto, flutuação do card de alerta, respiração contínua dos elementos.
- **Transição para Cena 1:** Wipe horizontal dinâmico com desfoque de movimento aos 5.1s.

---

### Cena 1: O Problema (4.96s a 11.43s | Frames 149 a 343)
- **Composição:** **c) Comparativo visual de atrito / Antes vs Depois**
- **Áudio:** "Eu temia que o cliente desistisse na hora de baixar um aplicativo só para ver o meu cardápio."
- **Fundo:** `img_1.jpg` com pan horizontal suave e zoom (scale 1.06 -> 1.18).
- **Elementos Visuais:**
  - `5.10s` (frame 153): Badge no topo (y=175) `⚠️ O PROBLEMA`.
  - `5.50s` (frame 165): Título de cabeçalho "O ATRITO DE BAIXAR APP".
  - `6.54s` (frame 196, na palavra "desistisse"): Card 1 (Dor - Vermelho `#E11D48`) surge com mola:
    - "❌ OBRIGAR A INSTALAR APP"
    - "Memória cheia no celular • Espera do download • Abandono do pedido"
  - `9.59s` (frame 288, na palavra "cardápio"): Card 2 (Contraste - Alerta de Frustração):
    - "⚠️ O CLIENTE SÓ QUER VER O CARDÁPIO"
    - "Cada clique a mais reduz suas vendas"
  - Micro-animação: Barra de loading de download travando em 99% com alerta de erro sutil para dramatizar a dor.
- **Câmera / Movimento:** Pan contínuo, oscilação suave dos cards flutuantes (delta Y senoidal), zoom contínuo.
- **Transição para Cena 2:** Deslize lateral 3D revelando o smartphone da próxima cena.

---

### Cena 2: Como Funciona (11.08s a 20.50s | Frames 332 a 615)
- **Composição:** **b) Celular inclinado em 3D (rotateY 18°) com WhatsApp animado balão por balão**
- **Áudio:** "Aqui não tem instalação. O cardápio abre direto no navegador do celular, com fotos, e a IA responde dúvidas na hora."
- **Fundo:** `img_2.jpg` com zoom sutil e bokeh de iluminação.
- **Elementos Visuais:**
  - `11.20s` (frame 336): Badge no topo (y=175) `💡 COMO FUNCIONA`.
  - Celular 3D de alta fidelidade à esquerda/centro (perspective 1200px, rotateY 16deg, rotateX 4deg):
    - Top bar WhatsApp com avatar "Atendimento IA" e status "Online".
    - Selo de conformidade: "Simulação".
    - `11.57s` (frame 347, "Aqui não tem instalação"): Balão cliente "Preciso instalar algum aplicativo para ver o cardápio?".
    - `13.15s` (frame 395, "O cardápio abre direto no navegador"): Digitando... seguido do balão empresa: "Não precisa! Abre direto no navegador do celular 🍔".
    - `15.86s` (frame 476, "com fotos"): Mini-card dentro do WhatsApp mostrando lanche com foto real e preço.
    - `16.66s` (frame 500, "e a IA responde dúvidas na hora"): Balão cliente "Esse lanche vem com batata?" -> Balão IA instantâneo: "Vem sim! Quer que eu anote o pedido? 🤖✨".
  - Painel de diferenciais flutuante (lado direito/alto):
    - `12.5s`: "🌐 Sem aplicativo"
    - `15.8s`: "📸 Cardápio com fotos"
    - `17.8s`: "⚡ IA tira dúvidas na hora"
- **Câmera / Movimento:** Leve movimento de câmera orbital no celular 3D (rotateY oscilando suavemente entre 14° e 18°), balões entrando com bounce de física natural.
- **Transição para Cena 3:** Zoom-through na tela do celular (a câmera mergulha no display em direção ao vídeo da cena seguinte).

---

### Cena 3: O Resultado (20.15s a 27.91s | Frames 604 a 837)
- **Composição:** **h) Vídeo comercial real (`video_3.mp4` em tela cheia) + g) Checklist animado dos 3 passos**
- **Áudio:** "O cliente escolhe pelas fotos, faz o pedido pelo WhatsApp e a sua loja não perde venda por causa de aplicativo."
- **Vídeo de Fundo:** `<OffthreadVideo src={staticFile('video_3.mp4')} muted />` com enquadramento perfeito e zoom contínuo (scale 1.00 -> 1.08).
- **Elementos Visuais (Faixa Segura Superior y=175 a y=500):**
  - `20.30s` (frame 609): Badge no topo `🚀 O RESULTADO`.
  - `20.73s` (frame 622, na palavra "cliente"): Título de impacto: "SUA LOJA NÃO PERDE VENDAS".
  - Checklist em 3 passos com ✓ sincronizado:
    - `21.78s` (frame 653, "fotos"): Passo 1 com ✓ verde: "1. Escolhe pelas fotos no celular"
    - `23.16s` (frame 695, "WhatsApp"): Passo 2 com ✓ verde: "2. Pede direto pelo WhatsApp"
    - `24.51s` (frame 735, "não perde venda"): Passo 3 com ✓ verde: "3. Zero barreiras: venda garantida"
- **Câmera / Movimento:** Movimento vivo da filmagem original somado ao zoom contínuo, entrada escalonada dos cards de checklist com mola elástica e partículas de sucesso sutis.
- **Transição para Cena 4:** Transição de desfoque e escala cinematográfica aos 27.5s.

---

### Cena 4: Cartão Final (27.56s a 31.41s | Frames 827 a 942)
- **Composição:** **Cartão Final de Agência (Motion Design de Alta Conversão)**
- **Áudio:** "Chame a gente no direct."
- **Fundo:** `img_4.jpg` com blur de 20px, véu profundo de marca `#31060F` (88% opacidade) e zoom contínuo (scale 1.10 -> 1.22).
- **Elementos Visuais:**
  - Karaokê: **DESLIGADO** (regra mandatória para evitar poluição visual sobre o CTA).
  - Identidade Visual da Marca:
    - Selo / Ícone animado do Cardápio Digital com pulso de brilho.
    - Nome da Marca: "CARDÁPIO DIGITAL" (68px bold, branco impecável).
  - Resumo do Produto (y=540 a 660):
    - "Cardápio com fotos no celular e pedido direto no WhatsApp com IA."
    - Pills de resumo: "Sem baixar aplicativo" • "Pedido no WhatsApp" • "Atendimento com IA".
  - Botão de CTA Central (y=840 a 970):
    - Texto estritamente idêntico ao convite falado: **"CHAME NO DIRECT"** (44px extra-bold).
    - Animação de pulso contínuo (scale 1.00 a 1.07 em ciclos senoidais de 1.1s).
    - Shimmer de luz passando diagonalmente pelo botão a cada 1.5s.
  - Perfil Oficial (y=1040):
    - Badge com `@futebolcom.ia2` com ícone estilizado do direct.
- **Câmera / Movimento:** Zoom contínuo na foto de fundo, flutuação suave do logotipo, pulso ininterrupto do botão CTA.
