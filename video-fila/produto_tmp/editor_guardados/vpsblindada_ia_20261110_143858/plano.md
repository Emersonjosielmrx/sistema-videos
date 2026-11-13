# Plano de Edição — vpsblindada_ia_20261110_143858 (VPS Blindada)

## Visão Geral
- **Produto:** VPS Blindada (`#0EA5E9` / `#111827` / `#FFFFFF`)
- **Duração:** 29.14 s (875 frames a 30 fps)
- **Regras de Ouro:**
  - Safe zone rigorosa: `x` entre `60` e `1020`, `y` entre `150` e `1580`.
  - Fonte mínima `>= 32px` em 100% dos textos (títulos `>= 48px`).
  - Movimento contínuo `> 10%` entre 20% e 80% de cada cena (zoom/pan no fundo, entradas sincronizadas à fala, flutuação contínua, barras/indicadores vivos).
  - `Karaoke` nativo (`src/lib/karaoke`) nas cenas 0 a 3, oculto na cena 4 (CTA).
  - Rostos nas cenas `dono` (`dono_1.mp4` e `dono_3.mp4`) 100% livres no centro (elementos gráficos só na faixa `y: 165–420`).

---

## Cena 0 — Pergunta (0.00s a 4.81s)
- **Composição:** (a) Texto GIGANTE cinético + Visualização de Container que trava vs Servidor Blindado.
- **Fala:** "Um aplicativo que trava pode derrubar todo o meu negócio?"
- **Elementos e Sincronia:**
  - **Fundo:** `img_0.jpg` com push-in dinâmico (scale `1.0` -> `1.14`, pan suave) + grade isométrica cibernética em movimento contínuo.
  - **0.0s (Gancho imediato):** Selo superior `SISTEMAS ISOLADOS NO SERVIDOR` (34px) + Pergunta principal com palavras que acendem/entram com spring sincronizadas à voz:
    - `Um aplicativo` (0.31s)
    - `que TRAVA` (1.20s — destaque vermelho alerta `#EF4444`)
    - `pode DERRUBAR` (1.78s — marca-texto/pílula)
    - `todo o meu NEGÓCIO?` (2.60s — destaque ciano `#0EA5E9`)
  - **Centro nobre (y: 700–1220):** Diagrama interativo vivo mostrando 3 blocos de serviços no servidor:
    - Aos `1.20s` ("trava"), o App 01 entra em alerta vermelho (`TRAVADO`), enviando ondas de choque.
    - Aos `2.30s` ("todo o meu negócio"), uma barreira de blindagem ciano (`ISOLAMENTO ATIVO`) se fecha ao redor do App 01, mantendo App 02 (`Sistema Web`) e App 03 (`Automação n8n`) operando com pulso verde estável.
- **Transição:** Wipe diagonal tecnológico para a Cena 1.

---

## Cena 1 — Dono / O Problema (4.46s a 10.86s)
- **Composição:** (h) Vídeo cheio do dono (`dono_1.mp4`) com câmera em push-in suave (`1.0` -> `1.07`) + HUD superior compacto (`y: 165–415`) sem cobrir o rosto.
- **Fala:** "Eu temia que uma falha em um aplicativo travasse o resto dos meus serviços."
- **Elementos e Sincronia (apenas no topo y: 165–415):**
  - **4.46s:** Pílula `O PROBLEMA` (32px, fundo vermelho escuro/borda alerta) + card escuro translúcido de alto contraste.
  - **5.78s ("falha em um aplicativo"):** Entra o indicador esquerdo `1 App com falha` com ícone de alerta pulsando.
  - **7.60s ("travasse o resto"):** Seta animada conectando ao bloco direito `Resto dos serviços em risco`, que acende aos `9.46s` ("serviços").
- **Transição:** Slide + Scale 3D para a Cena 2.

---

## Cena 2 — Conversa / Como Funciona (10.51s a 17.86s)
- **Composição:** (b) Celular inclinado em 3D + Painel de Containers Docker/Portainer sincronizado à fala.
- **Fala:** "A estrutura entrega Docker e Portainer configurados para separar cada aplicação de forma independente."
- **Elementos e Sincronia:**
  - **Fundo:** `img_2.jpg` com pan/zoom contínuo + feixes de luz em movimento.
  - **Topo (y: 165–290):** Pílula `COMO FUNCIONA` + Título `Docker + Portainer Configurados` (48px) com selo `Simulação` (32px).
  - **Centro (y: 310–1280):** Mockup de smartphone grande (largura 920px, inclinação 3D que evolui de `-10deg` a `6deg` ao longo da cena) exibindo a conversa de WhatsApp com todas as fontes `>= 32px`:
    - **10.6s:** Balão 1 (cliente, direita): *"Como ficam organizados meus sistemas na VPS?"*
    - **11.4s–12.0s:** Indicador *"digitando..."* animado.
    - **12.0s ("Docker e Portainer"):** Balão 2 (empresa, esquerda): *"Com Docker e Portainer configurados, cada aplicação roda em seu próprio ambiente isolado."*
    - **14.3s ("separar cada aplicação"):** Três pílulas visuais de containers independentes (`Container 01 • Sistema`, `Container 02 • Automação`, `Container 03 • Banco`) acendem em sequência dentro do painel.
    - **15.7s ("independente"):** Balão 3 (cliente, direita): *"Entendi, fica muito mais organizado para gerenciar."*
- **Transição:** Cortina luminosa vertical para a Cena 3.

---

## Cena 3 — Dono / O Resultado (17.51s a 25.54s)
- **Composição:** (h) + (g) Vídeo cheio do dono (`dono_3.mp4`) com zoom contínuo (`1.0` -> `1.08`) + Checklist horizontal/compacto no topo (`y: 165–425`) com ✓ animado na palavra falada.
- **Fala:** "Agora tenho minha VPS pronta e segura, com Docker, Portainer e backup automático funcionando."
- **Elementos e Sincronia (topo y: 165–425, rosto 100% livre):**
  - **17.8s:** Pílula `O RESULTADO` + Título `Sua VPS pronta e segura` (46px).
  - **Checklist vivo em 3 pílulas grandes (`>= 32px`) que acendem na palavra exata:**
    - **19.8s ("pronta e segura"):** Item 1 `✓ VPS Pronta e Segura`
    - **21.8s ("Docker, Portainer"):** Item 2 `✓ Docker + Portainer`
    - **23.3s ("backup automático"):** Item 3 `✓ Backup Automático`
- **Transição:** Zoom-through com blur para o Cartão Final.

---

## Cena 4 — Cartão Final / CTA (25.19s a 29.14s)
- **Composição:** Cartão final de agência vivo, sem legenda Karaokê.
- **Fala:** "Chame a gente no direct."
- **Elementos e Sincronia (dentro de y: 160–1520):**
  - **Fundo:** `img_4.jpg` com zoom contínuo (`1.0` -> `1.12`) + partículas/anéis orbitais em movimento constante até o último frame.
  - **Topo/Centro (y: 210–860):** Escudo 3D animado da marca + Nome `VPS BLINDADA` (72px, branco com brilho ciano) + Subtítulo `Sua VPS pronta, segura e com backup` (38px) + 3 badges de fatos (`Docker + Portainer + Traefik`, `n8n próprio`, `Bot Sentinela`).
  - **Base de Ação (y: 920–1450):**
    - Botão pulsante grande `CHAME NO DIRECT` (50px) com feixe de luz (shimmer) atravessando continuamente.
    - Arroba `@vpsblindada.ia` (40px) em pílula escura com ícone.
