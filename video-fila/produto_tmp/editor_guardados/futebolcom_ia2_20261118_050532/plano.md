# Plano de Edição — futebolcom_ia2_20261118_050532
Produto: Cardápio Digital | Duração: 29.61s (889 frames @ 30 fps)

## Cores e Tipografia
- Fonte Principal: Montserrat (Google Fonts)
- Cores da Marca:
  - Primária (Destaque): #E11D48 (Carmim vibrante)
  - Apoio: #FACC15 (Dourado / Amarelo solar)
  - Fundo escuro: #31060F (Vinho escuro profundo)
  - Texto sobre marca: #FFFFFF

## Estrutura das Cenas e Composições (Mínimo 4 composições distintas)

### Cena 0 (0.0s – 4.59s | frames 0 – 138)
- Tipo: `pergunta` (Gancho de dor)
- Fala: "Mensagens acumulando e clientes desistindo do pedido?"
- Composição: **(e) Pilha de notificações de alerta e cards de dor sobre fundo de alta energia**
- Layout:
  - Topo (y: 180–380): Pergunta cinética em destaque com palavra de impacto em marca-texto ("MENSAGENS ACUMULANDO?", depois "CLIENTES DESISTINDO?").
  - Centro (y: 490–1200): Cards realistas de notificações WhatsApp empilhando dinamicamente:
    - 0.5s: Card 1 "WhatsApp • 47 novas mensagens não lidas 🔴"
    - 1.3s: Card 2 "Cliente • 'Cadê o cardápio? Vou pedir em outro lugar...' ⏳"
    - 2.1s: Badge de alerta vermelho pulsando: "VENDAS SENDO PERDIDAS ❌"
  - Base: Karaokê oficial entre y=1380 e y=1560.
- Movimento: Fundo em push contínuo (scale 1.05 -> 1.15), notificações entrando com spring e leve tremor de alerta (shake), badge pulsando.
- Transição para Cena 1: Wipe lateral / scale fadeout dinâmico.

### Cena 1 (4.24s – 12.10s | frames 127 – 363)
- Tipo: `dono` (Depoimento do dono da lanchonete/restaurante)
- Fala: "No sábado à noite acumulavam muitas mensagens ao mesmo tempo e eu não vencia responder."
- Composição: **(h) Vídeo real em tela cheia com grafismos exclusivamente na zona superior (y: 160–380)**
- Layout:
  - Fundo: `dono_1.mp4` em tela cheia (OffthreadVideo muted), com leve zoom contínuo (1.0 -> 1.06).
  - Zona do apresentador (y: 400–1480): 100% LIVRE E DESOBSTRUÍDA (respeito absoluto ao rosto e expressão).
  - Topo (y: 170–360):
    - 4.5s – 6.6s: Badge elegante "O PROBLEMA" + sub-badge "SÁBADO À NOITE 🕒"
    - 7.0s – 9.2s: Card cinético "MENSAGENS AO MESMO TEMPO ⚡"
    - 9.6s – 12.1s: Badge de dor "NÃO VENCIA RESPONDER ⏳" com glow vermelho
  - Base: Karaokê oficial ancorado em y=1560.
- Movimento: Câmera lenta do vídeo + entrada com mola e flutuação sutil dos selos de topo.
- Transição para Cena 2: Deslize dinâmico com blur direcional.

### Cena 2 (11.75s – 19.28s | frames 352 – 578)
- Tipo: `conversa` (Solução: Celular com Cardápio Digital e Atendimento com IA)
- Fala: "O cardápio digital tem fotos no celular e o atendimento com IA responde dúvidas na hora."
- Composição: **(b) Celular 3D de alta fidelidade com WhatsApp real + visualização de cardápio com foto + IA respondendo**
- Layout:
  - Topo (y: 170–320): Selo "COMO FUNCIONA" + título "CARDÁPIO COM IA NO WHATSAPP 🤖"
  - Centro (y: 360–1320): Mockup de smartphone vertical com interface de WhatsApp estilizada:
    - Selo discreto "Simulação" no topo do chat (conforme regras do EDITOR.md).
    - Balão 1 (12.2s): Cliente: "Boa noite, onde vejo os pratos?"
    - Balão 2 (13.4s): Empresa: "Olá! Aqui está o cardápio digital com fotos para você escolher." + Card do Cardápio com foto de hambúrguer artesanal e preço claro.
    - Balão 3 (15.2s): Cliente: "O hambúrguer da foto vem com queijo?"
    - Digitando... com tag "IA Respondendo..." (16.2s)
    - Balão 4 (16.8s): IA: "Sim, vai com queijo e você pode pedir direto por aqui! 🍔"
  - Base: Karaokê oficial posicionado entre y=1380 e y=1560.
- Movimento: Celular com entrada em mola 3D (rotateY de 15° até 0°), balões surgindo um a um exatamente nas palavras faladas, brilho passando no cardápio.
- Transição para Cena 3: Zoom dinâmico no celular para transição com o vídeo real.

### Cena 3 (18.93s – 26.12s | frames 568 – 784)
- Tipo: `dono` (Depoimento de resultado e alívio operacional)
- Fala: "Hoje o cliente tira dúvidas sozinho e o pedido chega pronto no meu WhatsApp."
- Composição: **(h) Vídeo real em tela cheia com badges de conquista e validação apenas no topo (y: 160–380)**
- Layout:
  - Fundo: `dono_3.mp4` em tela cheia (OffthreadVideo muted), zoom lento de 1.0 -> 1.06.
  - Zona do apresentador (y: 400–1480): 100% PRESERVADA e sem obstruções.
  - Topo (y: 170–360):
    - 19.0s – 21.0s: Badge de sucesso "O RESULTADO" + selo verde "OPERAÇÃO AUTOMATIZADA"
    - 21.2s – 23.0s: Card "DÚVIDAS RESPONDIDAS PELA IA ✨"
    - 23.3s – 26.1s: Card de vitória "PEDIDO PRONTO NO WHATSAPP 📲✅"
  - Base: Karaokê oficial ancorado em y=1560.
- Movimento: Câmera orgânica do vídeo, badges com springs rápidos e partículas sutis de celebração.
- Transição para Cena 4: Zoom-through elegante revelando o cartão de conversão.

### Cena 4 (25.77s – 29.61s | frames 773 – 889)
- Tipo: `cartao` (CTA final de alta conversão)
- Fala: "Chame a gente no direct."
- Composição: **Cartão final vivo de agência (Motion Branding)**
- Layout:
  - Fundo: Gradiente escuro da marca (`fundo_escuro` #31060F com glows de #E11D48 e malha gráfica sutil em movimento contínuo).
  - Topo/Centro (y: 420–780):
    - Logotipo/Nome da marca em destaque: "CARDÁPIO DIGITAL" (com ícone estilizado de prato/celular).
    - Proposta de valor clara (y: 720): "Cardápio com fotos e IA no WhatsApp" (fonte 40px, contraste máximo).
  - Botão de Ação CTA (y: 920–1080):
    - Botão em pílula grande: "CHAME NO DIRECT" (mesma frase dita no áudio).
    - Animação de pulso contínuo (scale 1.0 -> 1.08 em loop até o último frame) + raio de luz (shimmer) varrendo.
  - Rodapé (y: 1240–1360):
    - Selo com a conta: "@futebolcom.ia2" em card elegante com borda sutil e ícone.
  - Legenda: SEM KARAOKÊ (conforme regra expressa do EDITOR.md).
- Movimento: Fundo em rotação/zoom contínuo, botão pulsando sem parar, brilho percorrendo o CTA.

---
## Verificações de Conformidade
- [x] Respeito absoluto à Safe Zone (y: 150 a 1580, x: 60 a 1020).
- [x] Barra de progresso contínua no topo em y=155.
- [x] Tipografia com tamanho mínimo absoluto >= 32px (maioria 36px–56px).
- [x] Contraste >= 4.5:1 em todos os textos.
- [x] Karaokê com quebras por cena (`quebraApos: true`), excluído no cartão final.
- [x] Rostos dos vídeos 100% protegidos (cards só acima de y=380 ou abaixo de y=1500).
- [x] Nenhuma cena parada por mais de 0.8s.
- [x] Zero fatos inventados: apenas os termos oficiais do briefing.
