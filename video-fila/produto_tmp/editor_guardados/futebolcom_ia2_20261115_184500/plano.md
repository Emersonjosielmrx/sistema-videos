# Plano de Edição — futebolcom_ia2_20261115_184500
**Produto:** Cardápio Digital (Cardápio Digital com pedido no WhatsApp e atendimento com IA)
**Duração:** 32.28 s (969 frames @ 30 fps)
**Cores:** Marca `#E11D48`, Apoio `#FACC15`, Fundo Escuro `#31060F`, Destaque `#E11D48`, Texto sobre marca `#FFFFFF`
**Fonte:** Montserrat (pesos 600, 700, 800, 900) — Tipografia mobile encorpada, todos os textos ≥ 32 px.
**Safe Zone:** y entre 150 e 1580; x entre 60 e 1020.

---

## Cena 0: Pergunta / Gancho
- **Tempo:** 0.00s a 4.76s (frames 0 a 143)
- **Tipo:** `pergunta`
- **Fala:** "Perdendo vendas porque o cliente tem dúvida sobre o prato?"
- **Composição:** (a) Texto cinético gigante em tela cheia com marcação de palavras-chave sobre fundo de marca escurecido (`img_0.jpg`).
- **Layout & Elementos:**
  - Barra de progresso no topo: y=152, altura 6 px, x=60 a 1020.
  - Tag fixa no topo (y=175): Pílula de apoio `DÚVIDAS SOBRE OS PRATOS?` com ícone de interrogação/cardápio.
  - Centro (y=440 a 980):
    - 0.0s - 0.3s: Zoom suave no fundo (scale 1.0 -> 1.06).
    - 0.316s ("Perdendo"): Surge card de alto impacto com texto "PERDENDO VENDAS?" (tamanho 68 px, 900 bold, caixa alta), com "PERDENDO" em destaque carmesim `#E11D48`.
    - 1.497s ("o cliente tem dúvida"): Transição/expansão dinâmica adicionando o bloco inferior "PORQUE O CLIENTE TEM DÚVIDA SOBRE O PRATO?" (52 px, com "DÚVIDA" em destaque amarelo `#FACC15`).
    - 2.8s ("sobre o prato"): Card visual com ilustração/ícone de cardápio digital pulsando sutilmente.
  - Base (y=1460 a 1560): Karaokê sincronizado palabra a palavra (`base=360`).
- **Movimento de Câmera:** Fundo com push-in contínuo (scale 1.0 -> 1.07), micro-pulso nas pílulas de texto.
- **Transição para Cena 1:** Fade cruzado suave com wipe direcional (frames 132 a 143).

---

## Cena 1: O Problema (Porta-voz / Dono)
- **Tempo:** 4.41s a 12.43s (frames 132 a 373)
- **Tipo:** `dono`
- **Fala:** "No horário de pico do delivery, eu não conseguia parar tudo para detalhar os acompanhamentos de cada prato."
- **Vídeo:** `dono_1.mp4` em tela cheia (`OffthreadVideo` muted, loop={false}), dono real na loja/restaurante.
- **Composição:** (h) Vídeo cheio com câmera em movimento e elementos de texto informativos estritamente no topo (y 160 a 420), mantendo o rosto do dono (y ~420 a 1200) 100% livre.
- **Layout & Elementos:**
  - Topo (y=175): Pílula de contexto "O PROBLEMA" com fundo translúcido escuro e borda fina `#E11D48`.
  - Topo Informativo (y=235 a 390):
    - 4.41s ("No horário de pico do delivery"): Entra card animado: "HORÁRIO DE PICO DO DELIVERY" (42 px, bold) com badge de alerta.
    - 6.59s ("eu não conseguia parar tudo"): Card transiciona para: "DIFICULDADE EM DETALHAR ACOMPANHAMENTOS" (38 px, alto contraste).
    - 10.51s ("acompanhamentos de cada prato"): Pulso em "ACOMPANHAMENTOS" com realce em amarelo `#FACC15`.
  - Base (y=1460 a 1560): Karaokê ativo sobre a fala do dono.
- **Movimento de Câmera:** Vídeo com zoom lento contínuo (scale 1.0 -> 1.05) para manter dinamismo cinematográfico.
- **Transição para Cena 2:** Slide sutil lateral com desfoque de movimento (frames 362 a 373).

---

## Cena 2: Como Funciona (WhatsApp & IA)
- **Tempo:** 12.08s a 21.11s (frames 362 a 633)
- **Tipo:** `conversa`
- **Fala:** "Se surge alguma pergunta sobre a refeição, o atendimento com IA explica na hora enquanto o cliente escolhe pelo celular."
- **Foto de fundo:** `img_2.jpg` com iluminação dinâmica e blur sutil.
- **Composição:** (b) Mockup de smartphone mobile imersivo em ângulo 3D sutil (rotateY -5° a 5°, perspective 1200px) com balões de WhatsApp entrando um a um, integrado à cena viva.
- **Layout & Elementos:**
  - Topo (y=165): Pílula de identificação "COMO FUNCIONA" + título "ATENDIMENTO COM IA NO WHATSAPP" (40 px, bold).
  - Mockup Celular (y=340 a 1430, x=80 a 1000):
    - Top bar do WhatsApp com avatar, "Cardápio Digital • IA" e selo "Simulação" discreto no canto.
    - 12.3s: Balão 1 (Cliente): "Boa noite! Estou olhando as fotos aqui no cardápio digital. Esse prato executivo vem com salada separada?" (34 px).
    - 15.0s ("o atendimento com IA explica na hora"): Indicador "IA digitando..." com 3 bolinhas pulsando.
    - 15.9s: Balão 2 (Empresa / IA): "Boa noite! Vem sim, a salada vai em uma embalagem separada do prato quente." (34 px, fundo verde WhatsApp `#005C4B`, texto branco).
    - 18.4s ("enquanto o cliente escolhe pelo celular"): Balão 3 (Cliente): "Perfeito, era essa a minha dúvida. Vou enviar o pedido por aqui mesmo." (34 px).
    - 19.8s: Balão 4 (Empresa / IA): "Combinado! Assim que escolher, pode mandar o pedido direto por aqui." (34 px).
  - Base (y=1460 a 1560): Karaokê perfeitamente posicionado abaixo do celular, sem nenhuma colisão (respiro > 40 px).
- **Movimento de Câmera:** Celular flutua suavemente em 3D (translateY seno leve, scale 1.0 -> 1.04), scroll natural dos balões subindo à medida que novos chegam.
- **Transição para Cena 3:** Zoom-in dinâmico mergulhando de volta para o dono (frames 623 a 633).

---

## Cena 3: O Resultado (Porta-voz / Dono)
- **Tempo:** 20.76s a 28.78s (frames 623 a 863)
- **Tipo:** `dono`
- **Fala:** "Agora eu recebo o pedido direto no WhatsApp com o cliente seguro da escolha que fez no cardápio."
- **Vídeo:** `dono_3.mp4` em tela cheia (`OffthreadVideo` muted), dono comemorando o resultado real.
- **Composição:** (h) Vídeo em tela cheia com grafismos dinâmicos posicionados exclusivamente no topo (y 160 a 420), preservando a expressão e rosto do dono.
- **Layout & Elementos:**
  - Topo (y=175): Pílula de destaque "O RESULTADO" em amarelo `#FACC15` com texto escuro.
  - Topo Informativo (y=235 a 390):
    - 20.76s ("Agora eu recebo o pedido direto no WhatsApp"): Card moderno entra com mola: "PEDIDOS DIRETOS NO WHATSAPP" (42 px, bold) com ícone de pedido confirmado.
    - 24.88s ("com o cliente seguro da escolha que fez no cardápio"): O card transiciona fluidamente para: "CLIENTE SEGURO DA ESCOLHA NO CARDÁPIO" (38 px, bold) com checkmark verde animado.
  - Base (y=1460 a 1560): Karaokê sincronizado com a fala final do dono.
- **Movimento de Câmera:** Scale contínuo 1.0 -> 1.05 no vídeo do dono.
- **Transição para Cena 4:** Efeito de fechamento com escala suave e desfoque luminoso para o cartão final (frames 853 a 863).

---

## Cena 4: Cartão Final (CTA Minimalista e Vivo)
- **Tempo:** 28.43s a 32.28s (frames 853 a 969)
- **Tipo:** `cartao`
- **Fala:** "Chame a gente no direct."
- **Convite:** "Chame no direct"
- **Composição:** Encerramento premium de alta conversão, vivo e minimalista (sem Karaokê).
- **Layout & Elementos:**
  - Fundo: `img_4.jpg` em movimento constante (zoom 1.0 -> 1.08) com vinheta escura suave.
  - Topo (y=380): Ícone de cardápio digital estilizado em gradiente carmesim e dourado com leve flutuação senoidal.
  - Centro 1 (y=560 a 700): Marca "CARDÁPIO DIGITAL" (tamanho 64 px, peso 900, branco puro com sombra sutil) + subtítulo "Atendimento com IA e pedido no WhatsApp" (36 px, cor clara `#E2E8F0`).
  - Centro 2 / Botão Principal (y=960 a 1120): Botão proeminente com a ação exata da locução:
    - Texto: "CHAME NO DIRECT" (tamanho 48 px, peso 900, cor `#FFFFFF`).
    - Fundo: Gradiente marca `#E11D48` a `#BE123C`, cantos arredondados (28 px), sombra de brilho pulsante.
    - Efeito: Pulso contínuo (scale 1.0 a 1.05 rítmico) + brilho (shimmer) que varre o botão a cada 1.5s.
  - Linha de Apoio (y=1220): "Tire suas dúvidas e modernize seu atendimento" (34 px, peso 600, cor `#FACC15`).
  - Base (y=1380): Identificador da conta `@futebolcom.ia2` (tamanho 40 px, peso 800, cor branca com pílula translúcida escura).
  - Movimento contínuo: Nada estático; partículas/brilhos suaves no fundo, botão pulsando até o último frame (969).
