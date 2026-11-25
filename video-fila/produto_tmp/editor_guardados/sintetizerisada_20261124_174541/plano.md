# Plano de Edição — Agenda IA (sintetizerisada_20261124_174541)

## Diretrizes Gerais
- Resolução: 1080x1920 @ 30 fps
- Duração: 32.54s (977 frames)
- Cores: Primária `#FFA94D` (Laranja da marca), Fundo `#1F2937` (Cinza escuro ardósia), Apoio `#0F172A` / `#0B0D13`, Texto `#FFFFFF`
- Tipografia: Montserrat (Bold / Black), todos os textos com tamanho >= 34 px (títulos >= 48 px), caixas de proteção com opacidade >= 90% para contraste >= 4.5:1
- Safe Zone: x entre 60 e 1020, y entre 150 e 1580.
- Movimento contínuo: câmera dinâmica (zoom/pan) e microdinâmica ativa >= 4% em todos os momentos.
- Legenda Karaokê: componente pronto `src/lib/karaoke.tsx`, ancorado em y <= 1580 (base: 360), quebra por cena, ausente na cena final (cartão).

---

## Cena 0 (0.0s – 5.29s, frames 0 – 159)
- **Tipo:** `pergunta`
- **Fala:** "Seu cliente desiste de marcar horário por causa de aplicativo?"
- **Composição:** Tipo a (Texto cinético GIGANTE com palavra-chave destacada sobre fundo vivo escurecido + card de dor com ícone de rejeição de app)
- **Câmera:** Zoom lento e constante no fundo (1.00 -> 1.08) com pan suave vertical (-20px) e partículas de luz ambiente.
- **Elementos Visuais:**
  - y = 150: Barra de progresso do vídeo (topo seguro).
  - y = 190: Badge de dor / gancho: "❌ BARREIRA DE ENTRADA" (pop com mola aos 0.3s).
  - y = 300 - 680: Título cinético em Montserrat 900 (tamanho 64px, textWrap: balance):
    - "SEU CLIENTE" (0.3s)
    - "DESISTE DE MARCAR" (1.0s, palavra "DESISTE" em pílula vermelha/laranja destacada)
    - "POR CAUSA DE APLICATIVO?" (2.4s - 3.8s)
  - y = 780 - 1180: Card visual de simulação do problema mobile (entra aos 1.2s com spring):
    - Notificação simulada de alerta: "Memória cheia • Baixar aplicativo (180 MB)" com ícone de erro e botão "CANCELAR" pulsando.
  - y = 1240: Selo gancho fixo: "CLIENTE NÃO PRECISA BAIXAR NADA" (surge aos 3.8s após o término da pergunta com destaque na marca).
  - y = 1560 (base 360): Legenda Karaokê ativa.
- **Transição para Cena 1:** Dissolve suave cruzada (0.35s).

---

## Cena 1 (4.94s – 12.97s, frames 148 – 389)
- **Tipo:** `dono`
- **Fala:** "Eu perdia cliente porque ninguém queria instalar mais um aplicativo só para marcar um horário comigo."
- **Composição:** Tipo h (Vídeo real do dono em tela cheia com movimento suave de câmera 1.00 -> 1.06 e textos exclusivos no topo y: 160-320, respeitando o rosto).
- **Rosto do Apresentador:** Olhado no still `dono_1_still.jpg`: cabeça em y ~350-1050. Zona superior y: 160-310 totalmente livre para títulos; zona inferior com legenda karaokê sobre o peito.
- **Elementos Visuais:**
  - y = 160: Badge de contexto com rótulo do briefing: "🔴 O PROBLEMA" (pílula escura com borda laranja).
  - y = 220: Título de impacto no topo (Montserrat Bold 48px, box protetor 90% opaco):
    - De 4.94s a 8.5s: "CLIENTES PERDIDOS POR APLICATIVO"
    - De 8.5s a 12.97s: "NINGUÉM QUER INSTALAR MAIS UM APP" (entra escalonado aos 8.5s sincronizado com "ninguém queria instalar...").
  - Fundo do vídeo: `<OffthreadVideo src={staticFile('dono_1.mp4')} muted />` com leve zoom progressivo.
  - y = 1560 (base 360): Legenda Karaokê sincronizada.
- **Transição para Cena 2:** Slide lateral suave / wipe com aceleração.

---

## Cena 2 (12.62s – 21.22s, frames 379 – 637)
- **Tipo:** `conversa`
- **Fala:** "O cliente chama no WhatsApp que já usa todo dia, e a IA agenda, confirma e reagenda sozinha."
- **Composição:** Tipo b (Interface mobile de WhatsApp em mockup grande 860px com balões escalonados sincronizados com a fala + painel de etapas 1-2-3 acendendo no topo).
- **Câmera:** Leve inclinação 3D dinâmica (rotateY de -4° a +3°) com zoom contínuo (1.02 -> 1.10).
- **Elementos Visuais:**
  - y = 160: Badge "⚡ COMO FUNCIONA" + Selo discreto "Simulação".
  - y = 230: Barra de etapas 1-2-3:
    - [1. AGENDA] acende em verde/laranja aos 17.6s (palavra "agenda")
    - [2. CONFIRMA] acende aos 18.1s (palavra "confirma")
    - [3. REAGENDA] acende aos 18.8s (palavra "reagenda")
  - y = 320 - 1280: Mockup de Celular (largura 860px):
    - Topo de WhatsApp ("Agenda IA • Online").
    - Mensagens entram sincronizadas (font size 36px, legível e em alto contraste):
      - 13.2s: Cliente: "Oi! Queria marcar um horário para quinta."
      - 15.0s: Indicador "Digitando..." animado.
      - 16.3s - 17.6s: Agenda IA: "Olá! Tenho quinta às 15h ou 17h. Agendado para quinta às 15h!"
      - 18.1s: Agenda IA: "✓ Agendamento confirmado com lembrete na véspera."
      - 18.8s - 19.5s: Cliente: "Preciso remarcar para sexta." -> IA: "Sem problema! Reagendado para sexta às 15h."
  - y = 1560 (base 360): Legenda Karaokê.
- **Transição para Cena 3:** Transição de zoom-out dinâmico.

---

## Cena 3 (20.87s – 28.90s, frames 626 – 867)
- **Tipo:** `dono`
- **Fala:** "Hoje meu cliente marca direto na conversa, sem instalar nada, e minha agenda fica organizada o dia todo."
- **Composição:** Tipo h (Vídeo real do dono em tela cheia com evolução do negócio, rótulo no topo e micro-card de status).
- **Rosto do Apresentador:** Respiro de > 40px preservado.
- **Elementos Visuais:**
  - y = 160: Badge "🟢 O RESULTADO" (pílula verde com borda).
  - y = 220: Título de impacto no topo (Montserrat Bold 48px):
    - De 20.87s a 24.5s: "DIRETO NA CONVERSA • SEM INSTALAR NADA"
    - De 24.5s a 28.9s: "AGENDA ORGANIZADA O DIA TODO"
  - y = 300: Micro-card dinâmico com checkmark: "✓ 100% no WhatsApp • Sem duplicidade" (entra aos 24.5s).
  - Fundo do vídeo: `<OffthreadVideo src={staticFile('dono_3.mp4')} muted />` com zoom contínuo (1.00 -> 1.06).
  - y = 1560 (base 360): Legenda Karaokê.
- **Transição para Cena 4:** Zoom-through luminoso com vinheta da marca.

---

## Cena 4 (28.55s – 32.54s, frames 857 – 977)
- **Tipo:** `cartao` (Encerramento de Alta Conversão)
- **Fala:** "Chame a gente no direct."
- **Composição:** Tipo f (Cartão final sofisticado com fundo desfocado da marca, logotipo animado com glow, benefício e botão CTA de alta pulsação).
- **SEM LEGENDA KARAOKÊ:** conforme regra expressa dos manuais.
- **Elementos Visuais:**
  - y = 200: Logo / Ícone dinâmico estilizado de calendário com IA e brilho contínuo.
  - y = 380: Marca em destaque: "AGENDA IA" (Montserrat 900, 80px, cor `#FFFFFF` com contorno/glow laranja `#FFA94D`).
  - y = 490: Subtítulo de posicionamento oficial do briefing (Montserrat Medium 38px):
    "Agendamentos automáticos com IA direto no WhatsApp"
  - y = 620 - 920: Card de diferenciais permitidos:
    - "✓ Atendimento e agendamento 24h"
    - "✓ Confirmação e reagendamento automáticos"
    - "✓ Sem conflito e sem duplo agendamento"
  - y = 1040 - 1200: Botão CTA pulsante (scale 1.00 a 1.07 em ciclos de 1.2s):
    - Texto exato da locução: "CHAME NO DIRECT" (Montserrat 900, 48px, fundo gradiente `#FFA94D` -> `#FF922B`).
    - Shimmer / feixe de luz passando continuamente pelo botão.
  - y = 1260: Perfil oficial: "@sintetizerisada" (Montserrat Bold 36px, visível até o final).
  - Câmera: Push-in no fundo desfocado (1.05 -> 1.15) mantendo a tela 100% viva.
