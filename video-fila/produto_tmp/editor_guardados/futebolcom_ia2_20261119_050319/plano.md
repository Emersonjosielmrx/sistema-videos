# Plano de Edição — Cardápio Digital (futebolcom_ia2_20261119_050319)

- **ID:** futebolcom_ia2_20261119_050319
- **Produto:** Cardápio Digital
- **Duração Total:** 30.96s (929 frames a 30 fps)
- **Paleta de Cores:**
  - Marca / Primária: `#E11D48` (Vinho / Rosa framboesa vibrante)
  - Apoio: `#FACC15` (Amarelo ouro)
  - Fundo escuro: `#31060F` (Bordô escuro premium)
  - Destaque: `#E11D48`
  - Sucesso: `#10B981` (Verde esmeralda para resultado positivo)
  - Texto: `#FFFFFF`
- **Safe Zone:** Topo informativo (y=150 a 480), Centro focal (y=500 a 1280), Base do Karaokê (y=1320 a 1580), Margens x=60 a 1020.
- **Rostos livres:** Em todas as cenas com o apresentador (cenas 1, 2 e 3), a cabeça e o rosto ficam estritamente livres (elementos apenas no topo y=150 a 420 e karaokê na base y=1560).

---

## Cena 0 — Pergunta (0.00s a 4.81s | Frames 0 a 144)
- **Tipo:** `pergunta`
- **Fala:** "Seu cliente desiste de pedir porque demora para responder?"
- **Composição:** **b / a** — Tipografia cinética forte no topo + Celular moderno no centro focal simulando o cliente esperando resposta e desistindo.
- **Elementos e Posições:**
  - Fundo: `img_0.jpg` com push-in suave (scale 1.05 -> 1.15) e gradiente com luz radial sutil da marca.
  - Topo (y=170 a 420):
    - Selo de gancho: "ATENDIMENTO AO CLIENTE" (entra aos 0.2s)
    - Pergunta cinética:
      - 0.3s ("Seu cliente"): entra com mola
      - 0.97s ("desiste de pedir"): marca-texto vermelho `#E11D48`
      - 2.22s ("porque demora para responder?"): badge de alerta pulsando
  - Centro Focal (y=520 a 1260):
    - Mockup de celular realista vertical (largura 780px, cantos arredondados, borda premium).
    - Selo discreto "Simulação" no topo do mockup.
    - 0.5s: Balão de mensagem do cliente entra: "Boa noite, tem cardápio aí?" (19:42)
    - 2.0s: Indicador de relógio / espera animada: "Aguardando resposta... 25 min"
    - 2.8s: Segundo balão do cliente desistindo: "Deixa, demorou muito, pedi no outro." (com tag de alerta vermelho)
  - Base (y=1560): Karaokê sincronizado via `<Karaoke />`.
- **Transição:** Wipe / Flash suave para Cena 1 aos 4.46s (frame 134).

---

## Cena 1 — O Problema (4.46s a 12.64s | Frames 134 a 379)
- **Tipo:** `dono`
- **Fala:** "Quando eu demorava a responder o cardápio, o cliente cansava de esperar e pedia no concorrente."
- **Rótulo:** "O problema"
- **Composição:** **h** — Vídeo real `dono_1.mp4` em tela cheia com push-in sutil (scale 1.00 -> 1.05), apresentador centralizado e elementos 100% livres de cabeça/rosto.
- **Elementos e Posições:**
  - Vídeo: `dono_1.mp4` (OffthreadVideo mudo).
  - Topo Informativo (y=160 a 410):
    - Tag ordinal: "ETAPA 1/3 • O PROBLEMA" (pílula bordo com borda `#E11D48` e texto branco).
    - Bloco textual cinético sincronizado:
      - 5.37s ("Quando eu demorava a responder o cardápio"): Título "Demora no atendimento"
      - 8.43s ("o cliente cansava de esperar"): Card de dor entra com slide-down "Tempo de espera elevado"
      - 10.81s ("e pedia no concorrente"): Badge de alerta com pulso sutil "⚠️ Pedidos perdidos para a concorrência"
  - Base (y=1560): Karaokê oficial sincronizado.
- **Transição:** Desmonte elegante dos cards superiores aos 12.0s antes da troca fluida para Cena 2.

---

## Cena 2 — Como Funciona (12.29s a 20.17s | Frames 369 a 605)
- **Tipo:** `dono`
- **Fala:** "Com o cardápio digital, o cliente olha as fotos e tira dúvida com a IA sem esperar."
- **Rótulo:** "Como funciona"
- **Composição:** **g / h** — Vídeo real `dono_2.mp4` em tela cheia + painel de recursos com checklist tecnológico no topo informativo.
- **Elementos e Posições:**
  - Vídeo: `dono_2.mp4` (OffthreadVideo mudo com micro-pan e push-in sutil scale 1.02 -> 1.06).
  - Topo Informativo (y=160 a 420):
    - Tag ordinal: "ETAPA 2/3 • COMO FUNCIONA" (pílula dourada `#FACC15` com texto escuro).
    - Chips/Pílulas dinâmicas escalonadas no topo (sem cobrir o dono):
      - 13.6s ("cardápio digital"): "📱 Cardápio Digital no celular"
      - 15.6s ("olha as fotos"): "📸 Fotos reais dos pratos"
      - 18.1s ("tira dúvida com a IA sem esperar"): "🤖 Atendimento com IA na hora" (com glow suave da marca)
  - Base (y=1560): Karaokê oficial sincronizado.
- **Transição:** Transição fluida com saída em fade-up dos chips aos 19.5s para introduzir o resultado na Cena 3.

---

## Cena 3 — O Resultado (19.82s a 27.46s | Frames 595 a 824)
- **Tipo:** `dono`
- **Fala:** "Hoje o pedido sai do cardápio direto para o WhatsApp e eu deixo de perder venda pela demora."
- **Rótulo:** "O resultado"
- **Composição:** **e / h** — Vídeo real `dono_3.mp4` em tela cheia (dono com camisa vermelha) + cards de conversão e resultado no topo.
- **Elementos e Posições:**
  - Vídeo: `dono_3.mp4` (OffthreadVideo mudo com zoom sutil 1.00 -> 1.05).
  - Topo Informativo (y=160 a 415):
    - Tag ordinal: "ETAPA 3/3 • O RESULTADO" (pílula esmeralda `#10B981` com texto branco).
    - Cards de resultado entrando em sincronia:
      - 20.9s ("o pedido sai do cardápio direto para o WhatsApp"): Card flutuante moderno "✓ Pedido direto no WhatsApp"
      - 24.4s ("eu deixo de perder venda pela demora"): Selo de sucesso em destaque "✨ Zero vendas perdidas por demora"
  - Base (y=1560): Karaokê oficial sincronizado.
- **Transição:** Desmonte antes do corte para o Cartão Final aos 26.8s.

---

## Cena 4 — Cartão Final / CTA (27.11s a 30.96s | Frames 813 a 929)
- **Tipo:** `cartao`
- **Fala:** "Chame a gente no direct."
- **Composição:** Encerramento Institucional de Alta Conversão.
- **Elementos e Posições:**
  - Fundo: `img_4.jpg` com véu escuro translúcido da marca e zoom contínuo (scale 1.05 -> 1.15).
  - Animação de entrada fluida (0.0s do cartão):
    - Selo de categoria: "SOLUÇÃO PARA DELIVERY E RESTAURANTES"
    - Logo / Marca grande: "CARDÁPIO DIGITAL" (branco + detalhes `#FACC15`)
    - Frase de valor: "Cardápio no celular com fotos e pedido direto no WhatsApp"
    - Botão de CTA de conversão em destaque:
      - Texto: "CHAME NO DIRECT" (mesma ação falada em `convite_voz`)
      - Efeito de pulso contínuo (scale 1.0 a 1.07 com spring/sin) até o frame final.
      - Feixe de luz / shimmer percorrendo o botão.
    - Perfil oficial visível desde o frame inicial da cena: `@futebolcom.ia2` (em pílula elegante).
- **Sem Karaokê nesta cena**, garantindo foco 100% no CTA e na marca!
