# Plano de Edição — mentoriasia_ia_20261114_110117

## Informações Gerais
- **Produto / Marca:** Treinamentos e Mentorias IA
- **Duração total:** 31.79 s (954 frames a 30 fps)
- **Cores principais:**
  - Azul Marca: `#2563EB`
  - Fundo Escuro / Apoio: `#111827`
  - Destaque: `#3B82F6` / `#60A5FA`
  - Texto Claro: `#FFFFFF` / `#F8FAFC`
- **Safe Zone:**
  - Vertical: 150px a 1580px
  - Horizontal: 60px a 1020px (largura útil: 960px)
- **Áudio:**
  - `narracao.mp3`: contínua do início ao fim (volume 1.0)
  - `trilha.mp3`: volume ~0.10 com locução, ~0.22 nos segundos finais, com fade-in e fade-out

---

## Cena 0 (0.0s – 4.74s | frames 0 – 142)
- **Tipo:** `pergunta`
- **Fala:** "Seus processos internos travam a rotina da empresa?"
- **Composição:** (a) Texto GIGANTE tela cheia cinético sobre fundo tech com partículas e diagrama de fluxo em movimento.
- **Posicionamento:**
  - Barra de progresso global: y=155.
  - Selo fixo do gancho: entra aos ~2.2s em y=220 ("Processos lentos na empresa?").
  - Bloco central tipográfico: y=480 a y=1100.
    - Linha 1 (0.3s): "SEUS PROCESSOS INTERNOS" (56px, bold, caixa com glow azul).
    - Linha 2 (1.7s): "TRAVAM A ROTINA" (68px, destaque em pill vermelho/alerta que vira azul na virada).
    - Linha 3 (2.6s): "DA EMPRESA?" (54px, branco alto contraste).
  - Karaokê: base=360 (y=1560).
- **Movimento de câmera / elementos:**
  - Push-in suave no fundo (scale 1.00 -> 1.08).
  - Ícone pulsante de fluxo de processo com pulso de radar contínuo.
  - Gancho forte em 0.3s (mola stiffness: 120, damping: 14).
- **Transição para Cena 1:** Dissolve suave de 10 frames (0.33s).

---

## Cena 1 (4.39s – 12.57s | frames 132 – 377)
- **Tipo:** `dono` (vídeo `dono_1.mp4`)
- **Fala:** "Meus fluxos eram lentos, até a consultoria de otimização mostrar onde aplicar automações com IA."
- **Composição:** (h) Vídeo do apresentador em tela cheia com movimento de push-in leve (scale 1.0 -> 1.06).
- **Proteção do Rosto:** O rosto do dono ocupa y=480 a y=1300. NENHUM elemento nesta área!
- **Posicionamento:**
  - Topo informativo (y=165 a 420):
    - Badge superior (y=175): "A SITUAÇÃO" com ícone de diagnóstico.
    - Card de topo dinâmico (y=240 a 390):
      - 4.39s a 7.5s: "FLUXOS LENTOS & ROTINA TRAVADA" (chip alerta).
      - 7.6s a 12.57s: "CONSULTORIA DE OTIMIZAÇÃO COM IA" (chip azul de destravamento de processos).
  - Rodapé (y=1380 a 1560): Karaokê da fala.
- **Movimento contínuo:**
  - Câmera em push-in constante no vídeo do dono.
  - Brilho sutil contínuo e pulso do badge.
- **Transição para Cena 2:** Wipe lateral suave com desfoque de 10 frames.

---

## Cena 2 (12.22s – 20.37s | frames 367 – 611)
- **Tipo:** `conversa` (mockup de WhatsApp)
- **Fala:** "A consultoria avalia sua rotina e entrega mapa mental, pack de prompts validados e treinamento de Vibe Coding."
- **Composição:** (b) Mockup mobile grande (largura 920px) em perspectiva/frontal 3D com diálogo nativo de WhatsApp e chips de entregáveis animados.
- **Posicionamento:**
  - Topo (y=165 a 300):
    - Badge "COMO FUNCIONA" + título "ETAPAS VALIDADAS".
  - Centro (y=320 a 1320):
    - Header do WhatsApp com nome "Mentoria IA", status "Online" e selo "Simulação".
    - Mensagem 1 (Cliente, 12.3s): "Vocês avaliam meus fluxos atuais que estão lentos?"
    - Digitando... (13.5s - 14.1s)
    - Mensagem 2 (Empresa, 14.2s): "Sim, na consultoria de otimização identificamos onde criar automações com IA."
    - Mensagem 3 (Cliente, 16.2s): "E eu mesmo consigo montar depois?"
    - Mensagem 4 (Empresa, 17.8s): "Sim, com o treinamento de Vibe Coding, mapa mental e pack de prompts validados."
    - Chips de entregáveis (Mapa Mental, Pack de Prompts, Vibe Coding) acendendo em sincronia com a voz (15.1s, 16.1s, 17.6s).
  - Rodapé: Karaokê oficial (y=1400 a 1560).
  - Tipografia: todas as mensagens do WhatsApp com fonte 34px (acima dos 32px mínimos obrigatórios).
- **Movimento contínuo:**
  - Flutuação suave do celular (rotação leve 3D e pan vertical).
  - Balões entram com mola escalonada.
- **Transição para Cena 3:** Cross-dissolve de 10 frames.

---

## Cena 3 (20.02s – 28.2s | frames 601 – 846)
- **Tipo:** `dono` (vídeo `dono_3.mp4`)
- **Fala:** "Aprendi a criar automações com IA e hoje monto minhas próprias soluções para otimizar nossos processos."
- **Composição:** (h) Vídeo do apresentador em tela cheia com push-in (scale 1.0 -> 1.06) e HUD discreto no topo.
- **Proteção do Rosto:** Rosto e mãos livres de qualquer interferência (y=450 a y=1340 desobstruído).
- **Posicionamento:**
  - Topo informativo (y=165 a 420):
    - Badge superior (y=175): "O RESULTADO" com ícone de sucesso/verificado.
    - Card de topo dinâmico (y=240 a 390):
      - 20.0s a 23.5s: "APRENDIZADO PRÁTICO EM IA" (badge autonomia).
      - 23.6s a 28.2s: "CRIE SUAS PRÓPRIAS SOLUÇÕES" (badge de produtividade).
  - Rodapé (y=1380 a 1560): Karaokê da fala.
- **Movimento contínuo:**
  - Push-in suave no vídeo do dono.
  - Micro-interações de luz e pulso suave no badge.
- **Transição para Cena 4:** Zoom-through suave com fade para o cartão final.

---

## Cena 4 (27.85s – 31.79s | frames 835 – 954)
- **Tipo:** `cartao` (CTA final)
- **Fala:** "Chame a gente no direct."
- **Composição:** Encerramento profissional de agência — unificado, elegante, com alta retenção.
- **NÃO exibir Karaokê:** O Karaokê não é renderizado nesta cena (regra obrigatória).
- **Posicionamento:**
  - Fundo: `img_4.jpg` com blur suave, véu escuro e grid sutil da marca.
  - Topo/Centro superior (y=320 a 580):
    - Selo de autoridade: "TREINAMENTOS E MENTORIAS IA".
    - Título de impacto: "Automações com IA para sua empresa".
    - Lista de pilares (34px): "Vibe Coding • Consultoria • Pack de Prompts".
  - Centro/Ação (y=980 a 1150):
    - Botão principal pulsando continuamente (scale 1.0 a 1.06):
      - Fundo: gradiente azul `#2563EB` -> `#1D4ED8` com raio de 30px e sombra iluminada.
      - Texto: "CHAME NO DIRECT" (44px, bold, branco).
      - Efeito de brilho (shimmer) varrendo o botão.
  - Inferior (y=1220 a 1340):
    - Perfil: `@mentoriasia.ia` (38px, com badge e ícone oficial).
- **Movimento contínuo:**
  - Pulso suave ininterrupto no botão até o último frame (sem congelamento).
  - Flutuação suave dos elementos e partículas de luz.
