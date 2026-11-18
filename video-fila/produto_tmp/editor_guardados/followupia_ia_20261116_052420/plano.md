# Plano de Edição (Corrigido v3) — followupia_ia_20261116_052420

- **Produto:** Follow-up IA (`@followupia.ia`)
- **Duração:** 31.34s (941 frames a 30fps)
- **Cores:** Marca `#4ECDC4`, Apoio/Fundo `#111827`, Texto sobre marca `#121216`
- **Zonas seguras:** `y` entre `150` e `1580`, `x` entre `60` e `1020`. Fontes >= 32px (todas >= 32px). Karaokê com base em y=1470 (base=450), 100% livre de palavras órfãs com quebras simétricas.
- **Estrutura modular:** `Video.tsx` compondo `Cena0.tsx`, `Cena1.tsx`, `Cena2.tsx`, `Cena3.tsx`, `Cena4.tsx`.

## Cena 0 (0.00s – 5.12s | `pergunta` | `dono_1.mp4`)
- **Composição:** Conexão humana imediata: Dono nítido e bem iluminado em primeiro plano falando direto para a câmera + Pop-up flutuante compacto e dinâmico na lateral esquerda com simulação do WhatsApp (balão cliente, resposta empresa aos 1.35s e alerta de vácuo aos 2.6s com tag "Sem resposta há semanas" em branco sobre fundo vermelho de alto contraste).
- **Fala:** "Dá para resgatar quem pediu preço no mês passado e não comprou?"
- **Elementos:**
  - `<OffthreadVideo src={staticFile('dono_1.mp4')} muted />` nítido e vivo (sem borrão ou escurecimento agressivo), enquadramento lateral com o apresentador falando diretamente para a câmera.
  - Título unificado no topo seguro (y: 175) com destaques cinéticos neon em ciano (`pediu preço`, `no mês passado`, `e não comprou?`).
  - Pop-up compacto flutuante de WhatsApp na lateral esquerda (x: 55, w: 480, y: 450) com tags de dor em alto contraste.
  - Transição contínua com zoom-through conectando à Cena 1.

## Cena 1 (4.77s – 12.08s | `dono` | `dono_1.mp4`)
- **Composição:** Vídeo cheio do dono em plano médio, rebaixado em 95px no enquadramento (headroom > 100px) + Top HUD posicionado em y: 175 (livre de sliver superior cortado sobre a barra de progresso em y: 150) + Punch-in dinâmico de escala (corte para 1.08x com spring ágil) aos 7.36s na fala da dor ("esfriaram semanas atrás").
- **Fala:** "Muitos contatos interessados esfriaram semanas atrás porque não tivemos braço para insistir."
- **Elementos:**
  - Punch-in para 1.08x aos 7.36s.
  - Top HUD em y: 175: "O PROBLEMA" + rótulo "Funil de Vendas" / "Capacidade esgotada" em branco de alta luminosidade (#FFFFFF/#FECACA). Card 1 entra aos 5.46s e esfria aos 7.36s. Card 2 ("Sem braço para insistir") entra aos 9.40s.
  - Transição suave de saída com slide direcional para conectar à demonstração da IA na Cena 2.

## Cena 2 (11.73s – 19.92s | `dono` | `dono_2.mp4`)
- **Composição:** Presença humana preservada com autoridade: fundador em cena em plano lateral médio falando para a câmera + overlay flutuante de WhatsApp demonstrando a automação da IA ao lado dele + Barra de etapas no topo (y: 175) com ativação mutuamente exclusiva e sincronizada com o áudio.
- **Fala:** "A IA envia mensagens no WhatsApp para trazer esse público de volta e nunca desiste."
- **Elementos:**
  - `<OffthreadVideo src={staticFile('dono_2.mp4')} muted />` mantido em cena.
  - Stepper 1-2-3 no topo (y: 175):
    - 12.67s – 15.15s: Aba 1 ativa em ciano ("1. Envia no WhatsApp"), abas 2 e 3 inativas.
    - 15.15s – 17.15s: Ao falar 'trazer esse público de volta', desativa aba 1 e ativa aba 2 com realce ciano ("2. Traz de volta").
    - 17.15s – 19.92s: Ao falar 'nunca desiste', passa o destaque exclusivamente para a aba 3 em esmeralda ("3. Nunca desiste").
  - Overlay de WhatsApp flutuante: etiqueta "Lead inativo há semanas" em texto branco puro (#FFFFFF) de alto contraste; balão 1 de disparo IA aos 12.67s; balão 2 de resposta do lead aos 15.15s; confirmação heroica aos 17.15s.

## Cena 3 (19.57s – 27.75s | `dono` | `dono_3.mp4`)
- **Composição:** Corte com punch-in de close-up (1.20x a 1.26x) quebrando a monotonia + transição animada 3D suave (flip out/in) entre o card de resultados e a tabela comparativa + animação de traçado (stroke-dashoffset via SVG) riscando o valor do SDR (R$ 2.500) aos 24.8s.
- **Fala:** "Eu recupero vendas de semanas atrás direto no WhatsApp, a partir de cento e noventa e nove reais."
- **Elementos:**
  - Dono em close-up 1.20x rebaixado com headroom garantido.
  - 19.57s – 24.61s: "O RESULTADO" + "Recupera vendas de semanas atrás" + "✓ Converte leads inativos no WhatsApp".
  - 24.61s – 27.75s: Flip 3D suave para o Comparativo:
    - SDR Humano: R$ 2.500 riscado por traço animado em SVG neon red + "Custa mais e desiste".
    - Follow-up IA: A partir de R$ 199 + "✓ Nunca desiste".
  - Transição suave direcional conectando com o encerramento.

## Cena 4 (27.40s – 31.34s | `cartao` | `img_4.jpg`)
- **Composição:** Cartão final premium de agência, limpo e desobstruído: 100% posicionado acima de y: 1580 (termina em y: 1210, margem segura de 370px contra interface do Reels), sem poluição de cards intermediários ou checklists redundantes.
- **Fala:** "Chame a gente no direct."
- **Elementos:**
  - Entrada escalonada (stagger com spring) para marca, proposta e CTA.
  - Dinamismo contínuo: botão CTA com pulso de scale contínuo (1.0 para 1.04) e reflexo metálico/shimmer deslizando em loop ininterrupto até o último frame.
  - Marca "Follow-up IA" em evidência heroica (98px).
  - Proposta de valor em 1 linha única: "Follow-ups com IA que recuperam vendas no WhatsApp".
  - Botão CTA luminoso "CHAME NO DIRECT" e arroba obrigatório "@followupia.ia".
  - Slogan "Pare de perder venda por esquecimento" em branco puro (#FFFFFF) de alta luminosidade, seguro na zona nobre do Reels.
