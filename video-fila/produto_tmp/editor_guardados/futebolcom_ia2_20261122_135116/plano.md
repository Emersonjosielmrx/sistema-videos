# Plano de Edição — Cardápio Digital
Vídeo ID: `futebolcom_ia2_20261122_135116`
Duração: 29.05 s | 872 frames (30 fps) | 1080x1920

## Identidade Visual e Diretrizes
- Marca: Cardápio Digital
- Cores: Marca `#E11D48` (Carmim), Apoio `#FACC15` (Dourado/Amarelo), Fundo Escuro `#31060F` / `#0B0D13`, Texto `#FFFFFF`.
- Tipografia: Montserrat (Black, ExtraBold, Bold, SemiBold). Piso mínimo inegociável de 32 px (títulos >= 48 px).
- Safe Zone: Margens x=60 a 1020, y=150 a 1580.
- Movimento contínuo: >= 4.0% de variação visual entre início e fim de cada cena, microdinâmica ativa constante.

---

## Cena 0: Pergunta do Cliente (0.00s a 4.55s | frames 0 a 136)
- **Tipo**: `pergunta`
- **Fala**: "Funciona bem para o movimento do almoço no restaurante?"
- **Composição**: (a) Texto cinético tela cheia com Faixa Bicolor de Alto Contraste (aprendizado aprovado fe4432ae + c6d3ccdb).
- **Fundo**: `img_0.jpg` (buffet do restaurante) com câmera em push-in contínuo (scale 1.05 -> 1.18) + véu protetor de alto contraste.
- **Entrada dos Elementos**:
  - Frame 0 (0.0s): Barra de progresso no topo (y=152). Fundo em movimento contínuo imediato.
  - Frame 5 (0.16s): Badge superior "PERGUNTA FREQUENTE" (y=210).
  - Frame 9 (0.30s): Entrada com spring pop do bloco central bicolor de alto contraste:
    - Faixa Amarela (#FACC15) com texto preto (#000000) 56 px: "FUNCIONA NO ALMOÇO?"
    - Faixa Preta (#0B0D13) com texto amarelo (#FACC15) 52 px: "DO RESTAURANTE LOTADO?"
  - Frame 55 (1.83s, voz "almoço"): Badge de apoio pulsante com o gancho do briefing: "Almoço lotado, pedido na fila?" (y=940).
  - y=1320-1560: Legenda Karaokê com destaque `#E11D48` ativando palavra por palavra conforme narração.
- **Transição**: Zoom-through dinâmico aos 4.2s com transição de opacidade/escala para Cena 1.

---

## Cena 1: O Problema (4.20s a 10.88s | frames 126 a 326)
- **Tipo**: `imagem`
- **Fala**: "No almoço corrido, a fila de mensagens crescia e eu não conseguia atender todo mundo com calma."
- **Rótulo**: "O problema"
- **Composição**: (e) Pilha de notificações de mensagens acumulando na tela sobre foto em movimento contínuo (`img_1.jpg`, pan horizontal + scale 1.08 -> 1.18).
- **Entrada dos Elementos**:
  - Frame 132 (4.4s): Header superior com Badge "O PROBLEMA" e título forte "FILA DE MENSAGENS NO ALMOÇO" (y=180-320).
  - Frame 152 (5.07s, voz "corrido"): Card 1 entra em slide da esquerda: "Mesa 4: Cadê o cardápio de hoje?" (ícone WhatsApp).
  - Frame 174 (5.80s, voz "fila de mensagens"): Card 2 entra empilhando: "Delivery: Quero fazer um pedido!" + badge "+18 não lidas".
  - Frame 225 (7.50s, voz "não conseguia atender"): Card 3 de Alerta em vermelho pulsante: "ATENDIMENTO SOBRECARREGADO" (ícone relógio/espera).
  - Base: Legenda Karaokê ativa até 9.6s.
- **Transição**: Wipe deslizante vertical suave aos 10.53s.

---

## Cena 2: Como Funciona (10.53s a 17.71s | frames 316 a 531)
- **Tipo**: `veo`
- **Fala**: "O cliente abre o cardápio digital no celular, vê as fotos dos pratos e faz o pedido pelo WhatsApp."
- **Rótulo**: "Como funciona"
- **Composição**: (b/d) Mockup Mobile Interativo 3D (rotateY de 12° a 0°, altura 860 px) com Cardápio Digital real sobre o vídeo de b-roll `video_2.mp4` (casal no restaurante).
- **Entrada dos Elementos**:
  - Frame 320 (10.66s): Header superior "COMO FUNCIONA" + título "CARDÁPIO DIGITAL COM FOTOS" (y=170-300).
  - Frame 335 (11.16s, voz "abre o cardápio"): Smartphone surge com spring 3D centralizado.
  - Frame 405 (13.50s, voz "vê as fotos dos pratos"): Destaque animado no prato executivo com foto apetitosa e etiqueta factual.
  - Frame 445 (14.83s, voz "faz o pedido pelo WhatsApp"): Botão verde WhatsApp na tela do celular dá um spring pop com checkmark ✓ "PEDIDO ENVIADO NO WHATSAPP".
  - Base: Legenda Karaokê ativa até 16.5s.
- **Transição**: Corte fluido para a gravação real do dono aos 17.36s.

---

## Cena 3: O Resultado (17.36s a 25.55s | frames 521 a 766)
- **Tipo**: `dono`
- **Fala**: "Hoje o cliente escolhe sozinho no celular, tira dúvida com a IA e o pedido chega pelo WhatsApp."
- **Rótulo**: "O resultado"
- **Composição**: (h) Vídeo do Dono (`dono_3.mp4`) em tela cheia com push-in de câmera (scale 1.0 -> 1.06).
- **Rostos Livres**: Rosto do dono está em y=300 a 1200. Zero sobreposição! Elementos gráficos exclusivamente na faixa y=160 a 310 (respiro de 60 px acima da cabeça).
- **Entrada dos Elementos**:
  - Frame 525 (17.5s): Header compacto "O RESULTADO: PEDIDOS COM IA".
  - Frame 550 (18.3s, voz "escolhe sozinho"): Etapa 1 acende no topo: "1. Cardápio no Celular".
  - Frame 635 (21.2s, voz "tira dúvida com a IA"): Etapa 2 acende no topo: "2. Atendimento com IA".
  - Frame 710 (23.7s, voz "pedido chega pelo WhatsApp"): Etapa 3 acende no topo: "3. Pedido no WhatsApp".
  - Base: Legenda Karaokê posicionada em y=1560 sem cobrir o peito/rosto do dono.
- **Transição**: Zoom contínuo e cross-fade escuro aos 25.2s.

---

## Cena 4: Cartão Final / CTA (25.20s a 29.05s | frames 756 a 872)
- **Tipo**: `cartao`
- **Fala**: "Chame a gente no direct."
- **Composição**: Cartão final dinâmico de conversão, fundo com zoom contínuo (`img_4.jpg` desfocada + véu escuro `#31060F` a 90%).
- **Entrada dos Elementos**:
  - y=360: Logo e marca "CARDÁPIO DIGITAL" com brilho metálico.
  - y=540: Frase de valor factual: "Atendimento com IA e pedidos direto pelo WhatsApp".
  - y=720: Selos de benefícios factuais: [ Pedido no WhatsApp ] [ Atendimento com IA ] [ Fotos dos Pratos ].
  - y=980: BOTÃO CTA pulsante (scale 1.00 a 1.08 em ciclo contínuo de 1.2s) na cor da marca `#E11D48`: "CHAME NO DIRECT" (idêntico à fala da locução).
  - y=1260: Badge oficial da conta: "@futebolcom.ia2" (destaque `#FACC15`).
  - Sem legenda karaokê para foco total na conversão.
