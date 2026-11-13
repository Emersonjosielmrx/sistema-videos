# Plano de Edição — followupia_ia_20261110_100550 (Follow-up IA)

## Visão Geral
- **Produto:** Follow-up IA (`@followupia.ia`)
- **Público:** Vendedores e empresas que perdem clientes que somem depois do orçamento.
- **Duração:** 29.61s (889 frames a 30fps)
- **Paleta:** Marca `#4ECDC4`, Apoio `#111827`, Fundo Escuro `#111827`, Destaque `#4ECDC4`, Texto Sobre Marca `#121216`
- **Safe Zone:** `y: 150..1580`, `x: 60..1020`, todas as fontes `>= 32px`.
- **Observação de Ativos:** `img_0.jpg` e `img_4.jpg` possuem os mesmos bytes (447748 bytes). Portanto, na Cena 0 (`img_0.jpg`) usamos recorte/enquadramento e estética escura ciano/grafite na parte superior com foco na pergunta, e no Cartão Final (Cena 4) usamos um fundo generativo dinâmico escuro `#111827` com malha luminosa `#4ECDC4` + recorte em arco de `img_3.jpg`/`img_4.jpg` altamente diferenciado para evitar qualquer repetição visual.

## Cenas e Composições

### Cena 0 — Pergunta (0.00s a 5.07s | Frames 0–152)
- **Composição:** **(a) Texto GIGANTE tela cheia + (e) Notificações de cliente sumido sobre foto escurecida (`img_0.jpg`)**
- **Movimento de Câmera:** Push-in contínuo em `img_0.jpg` (scale `1.02 -> 1.12`, pan leve) sob véu gradiente `#111827`.
- **Sincronia com a fala:**
  - `0.0s`: Pílula de topo `DÚVIDA DO VENDEDOR` + pergunta principal aparecendo palavra a palavra / bloco cinético: *"Como vender para quem parou de falar comigo sem perder tempo?"*
  - `1.38s` ("parou"): Card de chat simulado no centro-baixo (acima da legenda) mostrando orçamento enviado e status *"Visualizado — Cliente parou de responder?"* (`gancho_tela`).
  - `2.80s` ("perder tempo"): Selo de destaque em `#4ECDC4` acende.
- **Transição:** Wipe diagonal ciano/escuro (0.35s).

### Cena 1 — O Problema / Dono (4.72s a 11.76s | Frames 141–353)
- **Composição:** **(h) Vídeo cheio (`dono_1.mp4`) com câmera em movimento (zoom 1.0 -> 1.07) e elementos APENAS no topo (y=155..430) para proteger o rosto central do apresentador**
- **Sincronia com a fala:**
  - `4.72s`: Rótulo `01 • O PROBLEMA` no topo esquerdo (`y=165`).
  - `5.04s` ("gastava horas"): Card compacto no topo (`y=230..410`) lado esquerdo: `Esforço manual` — *"Gastava horas correndo atrás de quem sumiu"*.
  - `9.36s` ("venda sempre escapava"): Card compacto no topo lado direito acende em vermelho/alerta: `Resultado` — *"A venda sempre escapava"* + comparativo real do briefing (*"SDR humano: R$ 2.500 e desiste"*).
- **Transição:** Slide/cross-fade suave (0.35s).

### Cena 2 — Como Funciona / Veo + WhatsApp 3D (11.41s a 19.20s | Frames 342–576)
- **Composição:** **(b) Celular inclinado em 3D (lado direito, `x=430..1015`) + Etapas numeradas à esquerda (`x=60..410`) sobre o vídeo `video_2.mp4` deslocado para a esquerda (mostrando a pessoa trabalhando no notebook à esquerda)**
- **Sincronia com a fala:**
  - `11.90s` ("A IA"): Rótulo `02 • COMO FUNCIONA` e título `Follow-up IA no WhatsApp`.
  - `13.53s` ("follow-up automático"): Passo `01` acende à esquerda + 1ª mensagem automática da IA entra no WhatsApp 3D.
  - `15.94s` ("reativar o contato"): Passo `02` (`Reativa o contato`) acende + resposta do cliente no WhatsApp.
  - `17.17s` ("conduzir a negociação"): Passo `03` (`Conduz a negociação`) acende + mensagem de fechamento da IA + selo `Simulação` (>=32px).
- **Transição:** Zoom-through / corte com deslize (0.35s).

### Cena 3 — O Resultado (18.85s a 26.01s | Frames 565–780)
- **Composição:** **(g) Grade/Checklist de 3 benefícios com ✓ animado + Comparativo de Fatos sobre `img_3.jpg` (escritório amplo com push-in e pan contínuo)**
- **Sincronia com a fala:**
  - `19.34s` ("Hoje eu recupero"): Rótulo `03 • O RESULTADO` + Card 01 com ✓ animado: `Recupera leads inativos`.
  - `21.27s` ("fecho negócios pelo WhatsApp"): Card 02 com ✓ animado: `Fecha negócios no WhatsApp`.
  - `23.17s` ("sem depender de esforço manual"): Card 03 com ✓ animado: `Sem esforço manual — ela nunca desiste` + Pílula de fato oficial: `A partir de R$ 199 (SDR humano custa R$ 2.500)`.
- **Transição:** Cross-fade com expansão luminosa para o CTA (0.35s).

### Cena 4 — Cartão Final / CTA (25.66s a 29.61s | Frames 770–889)
- **Composição:** **Cartão Final de Agência com movimento contínuo (>10% até o último frame), sem legenda Karaokê**
- **Elementos (todos entre y=160 e y=1480, x=60..1020):**
  - Fundo escuro `#111827` com recorte dinâmico de `img_4.jpg` em zoom contínuo + ondas luminosas `#4ECDC4`.
  - Marca grande `Follow-up IA` + subtítulo `Follow-ups com IA que recuperam vendas no WhatsApp`.
  - Destaque do fato: `A partir de R$ 199 • Ela nunca desiste`.
  - Botão pulsante com brilho passando: `CHAME NO DIRECT` (alinhado com `convite_voz`: *"Chame a gente no direct."*).
  - Handle `@followupia.ia` em pílula de alto contraste (`y=1360`).
