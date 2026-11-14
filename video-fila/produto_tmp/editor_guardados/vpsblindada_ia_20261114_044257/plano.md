# Plano de Edição - VPS Blindada (vpsblindada_ia_20261114_044257)

## Diretrizes Gerais
- Duração total: 30.14 s (905 frames a 30 fps).
- Safe zone: Y entre 150 e 1580; X entre 60 e 1020.
- Tipografia: Títulos >= 48px, textos secundários e badges >= 32px (ideal >= 36px).
- Paleta: Marca `#0EA5E9`, Fundo `#111827`, Apoio `#0284C7`, Texto `#FFFFFF`, Alerta `#F43F5E`.
- Karaokê: `Karaoke` oficial (`../../lib/karaoke`), cor `#0EA5E9`, base=360 (y=1560), oculto no cartão final.
- Movimento: Câmera contínua (zoom/pan), animação de entrada com spring, respiração constante e micro-movimentos contínuos (delta > 4% entre 20% e 80% de cada cena).
- Respeito aos fatos: estritamente Docker, Portainer, Traefik, n8n self-hosted, backup automático, Bot Sentinela.

---

## Cena 0: Pergunta & Gancho Visual
- **Tempo:** 0.00s a 5.00s (frames 0 a 150).
- **Tipo:** `pergunta` (Composição A: Texto Cinético Gigante de Impacto + Card Central de Servidor).
- **Fala:** "Seu negócio fica desprotegido se o servidor cair hoje?"
- **Fundo:** `img_0.jpg` com push-in suave (1.00 -> 1.08) e partículas de dados cibernéticos sutis.
- **Top informative (y: 170 a 460):**
  - Badge no topo (y: 170): `ALERTA DE SEGURANÇA` com ícone de escudo pulsante (entra em 0.2s).
  - Título cinético sincronizado (y: 240 a 420):
    - Em 0.32s ("Seu negócio fica"): surge "SEU NEGÓCIO FICA" (48px, bold, branco).
    - Em 1.33s ("desprotegido"): estampa caixa de destaque vermelha/alerta "DESPROTEGIDO?" (56px, extra-bold).
    - Em 2.28s ("se o servidor cair hoje"): surge "SE O SERVIDOR CAIR HOJE" (44px, cyan #0EA5E9).
- **Centro focal (y: 540 a 1220):**
  - Card estilizado de Rack/Status de Servidor em React (largura 920px, altura 540px).
  - Mostra módulos do servidor: CPU Load, Containers, Backup Status e Rede.
  - Ao bater "desprotegido" e "cair hoje" (1.33s a 3.5s), a barra de status de backup muda para alerta piscante com glitch suave e aviso de vulnerabilidade ("SEM BACKUP DETECTADO").
  - Linha de escaneamento luminosa percorrendo o card continuamente (movimento sem parar).
- **Base (y: 1320 a 1560):**
  - Karaokê oficial sincronizado com as palavras.
- **Transição:** Flash suave e corte com sweep lateral para o porta-voz aos 4.65s.

---

## Cena 1: O Problema (Porta-voz / Dono)
- **Tempo:** 4.65s a 12.68s (frames 140 a 380).
- **Tipo:** `dono` (Composição H: Vídeo cheio com câmera push e HUD no topo informativo).
- **Fala:** "Eu operava no escuro sem ter cópia de segurança nem alertas quando algo quebrava."
- **Vídeo:** `dono_1.mp4` em tela cheia (objectFit cover, sem cortes, zoom 1.00 -> 1.06).
- **Rosto e corpo livres:** NENHUM elemento entre y=430 e y=1310. O apresentador fica 100% visível e sem sombras artificiais no rosto.
- **Top informative (y: 170 a 410):**
  - Badge (y: 175): `O PROBLEMA` (pill escuro com borda cyan, entra em 4.8s).
  - Headline dinâmica (y: 240 a 400):
    - Em 5.53s ("Eu operava no escuro"): "OPERANDO NO ESCURO" (50px, bold).
    - Em 8.49s ("cópia de segurança"): adiciona tag de alerta "SEM CÓPIA DE SEGURANÇA" (38px, fundo escuro translúcido com ponto vermelho piscante).
    - Em 9.69s ("nem alertas quando algo quebrava"): tag "FALHAS SEM AVISO" (38px).
- **Base (y: 1320 a 1560):**
  - Karaokê oficial ativo na base da tela.
- **Transição:** Dissolvência elegante com expansão de card para a cena da conversa.

---

## Cena 2: Como Funciona (WhatsApp Nativo Vivo)
- **Tempo:** 12.33s a 18.87s (frames 370 a 566).
- **Tipo:** `conversa` (Composição B/D: Celular 3D de alta fidelidade + Balões sequenciais + Selo Simulação).
- **Fala:** "A estrutura entrega cópia automática dos dados e o Bot Sentinela vigiando os erros."
- **Fundo:** `img_2.jpg` com rotação e escala sutil (1.00 -> 1.07).
- **Top informative (y: 165 a 270):**
  - Badge de contexto (y: 170): `COMO FUNCIONA` (pill cyan).
  - Título (y: 225): `ROTINA AUTOMATIZADA` (46px, bold).
- **Centro focal (y: 290 a 1270):**
  - Celular nativo em perspectiva leve (largura 920px, altura 960px).
  - Barra de topo do app: Avatar com escudo, "VPS Blindada - Suporte Técnico", status "online" e selo discreto "Simulação" (font-size 32px).
  - Balões de conversa com tipografia >= 34px:
    - 12.5s: Balão 1 (Cliente) desliza da direita: *"Como estão as cópias e a segurança das ferramentas?"*
    - 13.5s: Indicador "digitando..." aparece.
    - 13.9s (na fala "cópia automática dos dados"): Balão 2 (Empresa) entra: *"A rotina de proteção rodou perfeitamente."* com badge de verificado verde.
    - 15.2s: Indicador "digitando..." aparece novamente.
    - 15.8s (na fala "Bot Sentinela vigiando os erros"): Balão 3 (Empresa) entra: *"O Bot Sentinela segue ativo vigiando os erros."* com ícone de radar/robô.
- **Base (y: 1320 a 1560):**
  - Karaokê oficial sincronizado.
- **Transição:** Zoom-out suave com wipe direcional para o porta-voz.

---

## Cena 3: O Resultado (Porta-voz / Dono)
- **Tempo:** 18.52s a 26.55s (frames 556 a 797).
- **Tipo:** `dono` (Composição H: Vídeo cheio com câmera push e HUD no topo informativo).
- **Fala:** "Hoje trabalho com tranquilidade sabendo que meus processos contam com proteção diária e contínua."
- **Vídeo:** `dono_3.mp4` em tela cheia com compensação das bordas pretas (`scale(1.22 * zoom)`), zoom contínuo 1.00 -> 1.06.
- **Rosto e corpo livres:** Área central totalmente preservada.
- **Top informative (y: 170 a 410):**
  - Badge (y: 175): `O RESULTADO` (pill verde/cyan com glow suave).
  - Card informativo dinâmico (y: 240 a 400):
    - Em 18.6s ("Hoje trabalho com tranquilidade"): "TRANQUILIDADE TOTAL" (52px, bold, caixa alta).
    - Em 22.46s ("proteção diária e contínua"): "PROTEÇÃO DIÁRIA & CONTÍNUA" (44px) com escudo de status "ATIVO" piscando em verde.
- **Base (y: 1320 a 1560):**
  - Karaokê oficial ativo na base da tela.
- **Transição:** Glow luminoso e transição moderna para o cartão final.

---

## Cena 4: Cartão Final (CTA de Alta Conversão)
- **Tempo:** 26.20s a 30.14s (frames 786 a 905).
- **Tipo:** `cartao` (Composição de Agência: Minimalista, Vivo, Unificado).
- **Fala:** "Chame a gente no direct."
- **Fundo:** `img_4.jpg` com blur de 12px, overlay de gradiente escuro (`#111827`) e luz azul volumétrica animada.
- **Elementos (todos entre y: 220 e 1520):**
  - Logo & Marca (y: 340): Ícone de escudo cibernético 3D pulsante + texto "VPS BLINDADA" (64px, bold, com brilho ciano).
  - Proposta de valor (y: 530): *"Sua VPS pronta, segura e com backup"* (40px, semi-bold, centralizado, textWrap: balance).
  - Fatos permitidos em pills animados (y: 690 a 830):
    - Linha 1: `Docker + Portainer + Traefik` (34px)
    - Linha 2: `n8n Self-Hosted • Bot Sentinela` (34px)
    - Linha 3: `Backup Automático Diário` (34px)
  - Botão de Ação CTA (y: 1040 a 1180):
    - Fundo ciano vibrante `#0EA5E9` com texto branco em bold 50px: `"CHAME NO DIRECT"` com ícone de direct/seta.
    - Animação contínua: escala pulsando de 1.00 a 1.06 até o último frame e reflexo de brilho passando periodicamente.
  - Arroba oficial (y: 1280): `@vpsblindada.ia` (40px, bold, com badge de autenticidade).
- **Sem Karaokê:** Como manda o manual de estilo para manter foco 100% na conversão.
