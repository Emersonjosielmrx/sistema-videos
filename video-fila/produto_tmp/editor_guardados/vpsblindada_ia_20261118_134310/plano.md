# Plano de Edição — vpsblindada_ia_20261118_134310
Produto: VPS Blindada | Duração: 31.04s (932 frames a 30 fps) | Dimensões: 1080x1920

## Diretrizes Rígidas
- Safe Zone: x: 60..1020, y: 150..1580.
- Proteção do apresentador (Cenas 1, 2, 3): Rosto situado entre y=320 e y=1150. Todos os grafismos superiores ficam estritamente entre y=160 e y=300 (respiro >= 40px da cabeça). Karaokê ancorado na base em y=1560 (base=360px), bem abaixo do peito/queixo.
- Piso de tipografia: NENHUM texto menor que 34px (título >= 52px).
- Movimento contínuo de 0 a 100% da duração: push-in, pan, pulsos e transições fluidas.
- Fatos estritamente fiéis ao briefing (Docker, Portainer, Traefik, n8n self-hosted, backup automático, Bot Sentinela).

---

## Cena 0 (0.00s a 4.93s) — Pergunta: "Medo de colocar seu sistema online e sofrer invasões?"
- **Composição**: a + f (Texto Cinético de Alto Impacto + HUD de Alerta Cibernético sobre fundo dinâmico).
- **Fundo**: `img_0.jpg` com push-in constante (scale 1.06 -> 1.15), grid cibernético sutil e partículas de luz.
- **Barra de Progresso**: Linha fina no topo (y=150) preenchendo suavemente ao longo do vídeo.
- **Elementos Visuais**:
  - y=170: Badge de categoria `⚠️ ALERTA DE SEGURANÇA` entrando em spring aos 0.25s.
  - y=270..520: Título cinético escalonado:
    - 0.32s ("Medo"): "MEDO DE COLOCAR" (Branco bold 64px)
    - 1.41s ("sistema online"): "SEU SISTEMA ONLINE" (Azul neon #0EA5E9 68px)
    - 2.40s ("sofrer invasões"): "E SOFRER INVASÕES?" (Vermelho alerta #EF4444 com leve pulso de impacto)
  - y=620..1100: HUD Central de Proteção Digital:
    - Escudo tecnológico com anel de escaneamento em rotação contínua e status `[ SERVIDOR DESPROTEGIDO ]` -> simulando o risco das conexões expostas.
  - y=1320..1560: Karaokê sincronizado na base.
- **Transição**: Desmonte suave com fade/scale aos 4.6s dando lugar à entrada do dono.

---

## Cena 1 (4.58s a 11.78s) — Dono: "Eu tinha receio de expor meu sistema na internet sem proteção adequada nas conexões."
- **Composição**: h (Vídeo real do dono em tela cheia com câmera em push-in sutil 1.00 -> 1.06).
- **Mídia**: `dono_1.mp4` via `<OffthreadVideo>` muted.
- **Topo (y=160..290)**:
  - y=165: Selo `O PROBLEMA` (Pill grafite translúcido com ponto pulsante vermelho).
  - y=225: Card minimalista de impacto: `RISCO NAS CONEXÕES • SISTEMA EXPOSTO` (entra aos 6.0s na palavra "receio", com ícone de alerta de rede).
- **Centro (y=320..1300)**: Rosto e gestos do apresentador 100% desobstruídos.
- **Base (y=1320..1560)**: Karaokê no ritmo exato da locução (5.24s a 10.98s).
- **Transição**: Desmonte do card do topo aos 11.2s e cross-fade suave para a cena 2.

---

## Cena 2 (11.43s a 19.61s) — Dono: "A estrutura configurada com Traefik gerencia o tráfego e protege as conexões de forma segura."
- **Composição**: h (Vídeo real do dono em tela cheia, variação de enquadramento com pan/zoom sutil 1.01 -> 1.06).
- **Mídia**: `dono_2.mp4` via `<OffthreadVideo>` muted.
- **Topo (y=160..290)**:
  - y=165: Selo `COMO FUNCIONA` (Pill grafite com ponto azul ciano #0EA5E9).
  - y=225: Card de arquitetura segura: `TRAEFIK: GERÊNCIA E ROTEAMENTO SEGURO` (entra aos 14.3s na palavra "Traefik", com ícone de escudo SSL ativo).
- **Centro (y=320..1300)**: Rosto do apresentador totalmente preservado.
- **Base (y=1320..1560)**: Karaokê sincronizado (12.21s a 18.61s).
- **Transição**: Fade out dos cards aos 19.0s e transição suave para a cena 3.

---

## Cena 3 (19.26s a 27.45s) — Dono: "Hoje meu sistema roda online com tranquilidade, tráfego protegido e servidor seguro para o negócio."
- **Composição**: h (Vídeo real do dono em tela cheia com push-in 1.02 -> 1.07).
- **Mídia**: `dono_3.mp4` via `<OffthreadVideo>` muted.
- **Topo (y=160..290)**:
  - y=165: Selo `O RESULTADO` (Pill esmeralda/ciano com ícone de check).
  - y=225: Card de confirmação de segurança: `SISTEMA ONLINE COM TRANQUILIDADE` (entra aos 20.9s na palavra "roda online", com indicador pulsante de status `PROTEGIDO`).
- **Centro (y=320..1300)**: Rosto do apresentador 100% desobstruído.
- **Base (y=1320..1560)**: Karaokê sincronizado (19.56s a 27.22s).
- **Transição**: Zoom sutil de impacto aos 27.0s transferindo para o cartão final.

---

## Cena 4 (27.10s a 31.04s) — Cartão Final: "Chame a gente no direct."
- **Composição**: Cartão de Conversão Premium de Alta Performance.
- **Fundo**: `img_4.jpg` com blur 14px + véu escuro gradiente da marca (#0B132B / #111827) + partículas e anéis de luz tecnológica.
- **Elementos**:
  - y=280: Ícone central do Escudo Cibernético com pulso neon azul.
  - y=460: Nome da marca em destaque: `VPS BLINDADA` (64px, branco puro + glow azul ciano).
  - y=570: Frase síntese do produto: `Sua VPS pronta, segura e com backup` (38px, cor #E2E8F0).
  - y=680..920: Pilares tecnológicos em cards modernos:
    - Card 1: `DOCKER & TRAEFIK CONFIGURADOS`
    - Card 2: `BACKUP AUTOMÁTICO & SENTINELA`
  - y=1100..1240: Botão de Ação CTA:
    - Texto idêntico à voz: `CHAME NO DIRECT` (50px, peso 900)
    - Animação: Pulso contínuo (scale 1.00 a 1.07 em loop suave) + efeito de luz metálica varrendo.
  - y=1380: Perfil oficial `@vpsblindada.ia` (40px, cor #38BDF8) ativo desde o frame 0 do cartão!
  - Sem karaokê neste cartão final.
