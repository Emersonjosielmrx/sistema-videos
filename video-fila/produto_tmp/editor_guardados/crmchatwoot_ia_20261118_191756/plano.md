# Plano de Edição — crmchatwoot_ia_20261118_191756
Produto: CRM Chatwoot IA
Duração: 35.03s (1051 frames a 30 fps)
Cores: Marca (#1F93FF), Apoio/Fundo (#111827), Texto Destaque (#FFFFFF)

## Regras Visuais e Zonas Seguras
- Safe Zone: x=60..1020, y=150..1580.
- Tipografia: Montserrat (Bold / Black / ExtraBold), tamanho mínimo de texto >= 32px (títulos 48-64px).
- Karaokê: via `src/lib/karaoke.tsx`, destaque em pílula azul (#1F93FF) com texto branco (#FFFFFF), base y <= 1580. Oculto na cena 4 (CTA final).
- Apresentador (Dono): Rosto e corpo 100% protegidos em cenas 1 e 3. Textos e badges exclusivamente no topo (y=160..340).

---

## Cena 0: Pergunta (0.00s - 6.92s | frames 0 - 207)
- **Tipo**: pergunta
- **Composição**: a) Texto cinético impactante sobre foto viva com zoom contínuo e vinheta da marca.
- **Fundo**: `img_0.jpg` com push-in suave (scale 1.05 -> 1.15) e leve pan. Vinheta gradiente escura suave no topo e na base para contraste 100%.
- **Movimento e Elementos**:
  - 0.0s - 0.4s: Gancho imediato. Surge pill badge `DÚVIDA FREQUENTE` no topo (y=180).
  - 0.32s - 1.51s ("Meu negócio é pequeno"): Bloco 1 entra com escala e mola: "MEU NEGÓCIO É **PEQUENO**" (palavra 'PEQUENO' com marca-texto azul #1F93FF).
  - 1.81s - 3.79s ("um CRM com IA"): Card central expande com badge "CRM COM IA" + ícone de inteligência artificial.
  - 3.80s - 5.45s ("não vai ser complicado demais?"): Destaque da objeção principal "NÃO VAI SER **COMPLICADO DEMAIS?**" com pulso suave.
  - 5.45s - 6.70s: Desmonte fluido com fade-out e transição limpa para o corte do Dono.
- **Transição**: Wipe suave / crossfade para cena 1.

---

## Cena 1: Dono — O Problema (6.57s - 14.76s | frames 197 - 442)
- **Tipo**: dono
- **Composição**: h) Vídeo real do Dono em tela cheia com movimento leve de câmera e grafismo de topo exclusivo.
- **Vídeo**: `dono_1.mp4` via `<OffthreadVideo muted />` com escala 1.0 -> 1.05. Rosto totalmente livre de qualquer sobreposição.
- **Movimento e Elementos**:
  - Topo (y=170): Badge pill "O PROBLEMA" com acabamento dark glassmorphism.
  - 7.61s - 11.80s ("Eu achava que CRM com inteligência artificial era coisa de empresa grande"):
    Card de topo com frase cinética: "ERA SÓ PRA **EMPRESA GRANDE?**"
  - 11.97s - 14.55s ("...mas hoje meu atendimento está organizado"):
    Transição do texto do topo com flip/slide para: "HOJE: **ATENDIMENTO ORGANIZADO**" com ícone de check.
- **Transição**: Desfoque direcional / transição limpa para cena 2.

---

## Cena 2: Veo — Como Funciona (14.41s - 23.61s | frames 432 - 708)
- **Tipo**: veo
- **Composição**: g) Grade / Pilares dinâmicos de benefícios acendendo 1 a 1 na hora exata da locução, integrados com b-roll de equipe em moldura moderna.
- **Vídeo**: `video_2.mp4` em janela b-roll superior (y=280..720) com bordas arredondadas e sombra suave.
- **Movimento e Elementos**:
  - Topo (y=170): Badge "COMO FUNCIONA" + Título "CRM SOB MEDIDA".
  - 17.6s - 18.3s: Selo "A partir do Chatwoot".
  - 18.62s ("atendimento"): Card 1 acende com spring: `[💬 Atendimento]` em azul #1F93FF.
  - 19.43s ("tickets"): Card 2 acende com spring: `[🎫 Tickets Integrados]`.
  - 20.01s - 22.3s ("histórico de cada cliente em um só lugar"): Card 3 acende com spring: `[📂 Histórico Centralizado]`.
  - 22.3s - 23.4s: Os 3 cards pulsam juntos em sincronia demonstrando a solução unificada "TUDO EM UM SÓ LUGAR".
- **Transição**: Zoom dinâmico para a volta do Dono.

---

## Cena 3: Dono — O Resultado (23.26s - 31.44s | frames 698 - 943)
- **Tipo**: dono
- **Composição**: h) Vídeo do Dono em tela cheia com novo enquadramento e grafismo de topo dinâmico.
- **Vídeo**: `dono_3.mp4` via `<OffthreadVideo muted />` com leve push-in contínuo.
- **Movimento e Elementos**:
  - Topo (y=170): Badge pill "O RESULTADO" com glow sutil.
  - 23.6s - 26.6s ("O sistema se adapta ao meu jeito de trabalhar"):
    Headline no topo (y=230): "ADAPTADO AO SEU **FLUXO**".
  - 27.4s - 30.8s ("...e minha equipe atende com clareza, sem complicação"):
    Headline transiciona para: "CLAREZA E **SEM COMPLICAÇÃO**" com destaque luminoso.
- **Transição**: Fade cruzado elegante para o cartão final.

---

## Cena 4: Cartão Final — CTA (31.09s - 35.03s | frames 933 - 1051)
- **Tipo**: cartao
- **Composição**: Encerramento inédito, cinematográfico, de alta conversão.
- **Fundo**: `img_4.jpg` com blur profundo (26px) + overlay escuro da marca (#111827 / #0F172A) e malha de luz azul (#1F93FF).
- **Movimento e Elementos**:
  - Topo (y=240..380): Logomarca "CRM Chatwoot IA" grande, com ícone estilizado e micro-flutuação suave.
  - Centro (y=480..680): Proposta de valor em card translúcido:
    "Um CRM feito para o seu negócio a partir do Chatwoot, com atendimento, tickets e histórico em um só lugar."
  - Botão CTA (y=860..1020): Botão "CHAME NO DIRECT" em pulso contínuo (scale 1.0 -> 1.08) com feixe de luz passando continuamente. Ação 100% idêntica ao convite falado ("Chame a gente no direct").
  - Rodapé (y=1120): Perfil oficial `@crmchatwoot.ia` nítido e visível desde o frame 0 do cartão final.
  - Karaokê: Totalmente desligado no encerramento conforme exigido pelas regras.
