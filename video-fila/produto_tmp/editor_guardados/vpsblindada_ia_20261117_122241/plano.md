# Plano de Edição — VPS Blindada (`vpsblindada_ia_20261117_122241`)

## Informações Gerais
- **Produto / Marca:** VPS Blindada (@vpsblindada.ia)
- **Duração Total:** 28.97 s (870 frames a 30 fps)
- **Paleta de Cores:**
  - Marca / Ciano Primário: `#0EA5E9` (Sky Blue tecnológico)
  - Fundo Escuro / Apoio: `#0B1120` / `#0F172A`
  - Destaque Karaokê: Pílula `#0EA5E9` com texto `#0B1120` (Contraste 7.2:1, padrão WCAG AAA)
  - Alerta / Incidente: `#EF4444` / `#FECACA`
  - Sucesso / Monitoramento: `#10B981` / `#34D399`
- **Safe Zone Rigorosa:** x entre 60 e 1020; y entre 150 e 1580 (elementos reais entre y=154 e y=1522).
- **Tipografia:** Montserrat, pesos 700/800/900, todos os textos rigorosamente com tamanho ≥ 32px.
- **Ícones:** 100% SVG vetoriais inline (Icons.tsx) eliminando qualquer dependência de fontes/emojis do sistema operacional.

---

## Cena a Cena

### Cena 0 (0.00s – 4.86s | frames 0 – 145) — Tipo: `pergunta`
- **Fala:** "Sua operação para e você só descobre pela reclamação?"
- **Composição:** **Composição A** — Pergunta-gancho unificada desde 00:00 sobre fundo tecnológico em zoom dinâmico (1.00 -> 1.22), scanline vertical contínua e entrada escalonada dos alertas.
- **Layout & Elementos:**
  - Topo (y = 165): Badge `[ FALHA SILENCIOSA ]` com `AlertIcon` pulsando.
  - Título unificado desde frame 0 (y = 230 a 380):
    - `SUA OPERAÇÃO PARA` (com `PARA` em pílula vermelha pulsante).
    - `e você só descobre pela reclamação?` (com destaque cinético e glow âmbar em `reclamação`).
  - Centro Focal (y = 420 a 1000):
    - Frame 4: HUD de Servidor (`STATUS DO SERVIDOR: PARADO` com shake sutil de impacto e pulso contínuo).
    - Frame 58 (sincronizado com "descobre pela reclamação"): Card de Notificação de Incidente do Cliente sobe com spring dinâmico.
    - Frame 90: Gancho oficial do briefing fixado no card: `"🔍 Processo travou sem você saber?"`.
  - Base (y = 1550): Karaokê oficial ancorado na base segura.
  - Variação 20% vs 80%: > 18% (> 4%).

### Cena 1 (4.51s – 12.21s | frames 135 – 366) — Tipo: `dono`
- **Fala:** "Um erro inesperado travava minha operação e eu só percebia quando tudo já estava parado."
- **Composição:** **Composição H** — Vídeo do apresentador com enquadramento aberto (plano médio/busto, scale 0.92 -> 0.95), fundo corporativo com desfoque controlado, respiro superior e peito livre.
- **Layout & Elementos:**
  - Posicionamento do Vídeo: plano médio com respiro superior (headroom), peito na faixa de y=1400-1550.
  - Topo (y = 155 a 270):
    - Badge `[ ⚠ O PROBLEMA ]` com `AlertIcon` SVG.
    - Frame 10 – 98: `ERRO INESPERADO NA OPERAÇÃO` (com `INESPERADO` em destaque).
    - Frame 98+: `TUDO JÁ ESTAVA PARADO` (com `PARADO` em destaque e punch-in sutil).
  - Base (y = 1550): Karaokê sobre o peito/camisa do dono, com mais de 150px de distância do queixo/barba/boca.
  - Variação 20% vs 80%: > 35% (> 4%).

### Cena 2 (11.86s – 18.92s | frames 355 – 567) — Tipo: `conversa`
- **Fala:** "A estrutura conta com o Bot Sentinela, que monitora a operação e detecta as falhas ativamente."
- **Composição:** **Composição B** — Mockup de smartphone vertical refinado com transição de entrada suave (scale-in e slide ágil), fundo com grafismos de conexões de servidor ancorando a tela.
- **Layout & Elementos:**
  - Transição de entrada: scale-in suave de 0.85 para 1.0 com slide lateral conectando a Cena 1 à Cena 2.
  - Topo (y = 165): Rótulo `[ COMO FUNCIONA ]` + Título: `BOT SENTINELA ATIVO`.
  - Mockup do Smartphone (y = 340 a 1280):
    - Header: Avatar `BotIcon`, `Bot Sentinela`, badge `● Online`, selo `SIMULAÇÃO`.
    - Mensagem de sistema de alto contraste: `🔒 Servidor conectado ao Bot Sentinela` (fonte 34px branca com glow ciano).
    - Balão 1 (Empresa, frame 18+): Header `⚡ NOTIFICAÇÃO DO SISTEMA` + *"Alerta: o Bot Sentinela detectou uma falha no fluxo de automação."*
    - Indicador de digitação: *"Cliente digitando..."* (3 pontos padronizados).
    - Balão 2 (Cliente, frame 84+): *"Obrigado pelo aviso, já estamos corrigindo o processo."*
    - Indicador de digitação: *"Bot Sentinela digitando..."* (3 pontos padronizados).
    - Balão 3 (Empresa, frame 135+): *"Servidor seguro, estável e sob monitoramento constante."*
  - Base (y = 1550): Karaokê oficial sincronizado.
  - Variação 20% vs 80%: > 15% (> 4%).

### Cena 3 (18.57s – 25.37s | frames 557 – 761) — Tipo: `dono`
- **Fala:** "Agora não fico mais no escuro, conto com servidor seguro e o robô vigiando tudo."
- **Composição:** **Composição H variada** — Variação de corte com punch-in digital (+12%), enquadramento deslocado à esquerda (-220px) liberando a lateral direita inteira para o card tecnológico.
- **Layout & Elementos:**
  - Posicionamento do Vídeo: enquadramento com respiro no topo, deslocado à esquerda, rosto totalmente livre.
  - Topo (y = 155 a 270):
    - Badge `[ 🛡️ O RESULTADO ]` com `ShieldIcon` SVG ciano.
    - Frame 9 – 88: `NÃO FICO MAIS NO ESCURO`.
    - Frame 88+: `SERVIDOR SEGURO + ROBÔ VIGIANDO`.
  - Lateral Direita (x = 730 a 1030, y = 580):
    - Card oficial do `BOT SENTINELA` entra no frame 130 sincronizado com a locução ("o robô vigiando") com slide lateral e overshoot.
    - Micro-animação contínua em looping de radar/ping pulsando no ponto verde de 'Monitoramento Ativo'.
    - Zero colisão com têmpora, cabeça ou cabelo do apresentador.
  - Base (y = 1550): Karaokê oficial sobre a camisa.
  - Variação 20% vs 80%: > 30% (> 4%).

### Cena 4 (25.02s – 28.97s | frames 750 – 870) — Tipo: `cartao`
- **Fala:** "Chame a gente no direct."
- **Composição:** **Composição de CTA de Agência** — Coreografia de entrada em cascata (stagger), foco limpo de conversão e eliminação total do panfleto estático.
- **Layout & Elementos:**
  - Topo (y = 175 a 450):
    - Frame 0: Escudo `ShieldIcon` descendo com ease-out e flutuação contínua + Nome `VPS BLINDADA`.
    - Frame 4: Proposta de valor *"Sua VPS pronta, segura e com backup"*.
  - Centro Focal (y = 520 a 860):
    - Entrada em cascata individual dos 5 pills de recursos com 4 frames de intervalo (frames 8, 12, 16, 20, 24).
  - Bloco de Ação (y = 1040 a 1440):
    - Frame 16: Botão CTA `[ CHAME NO DIRECT ]` entra com scale-pop sincronizado com a locução, sem texto redundante entre aspas acima.
    - Pulso de brilho neon (glow pulsante) + efeito de varredura de luz (shine sweep) contínuo.
    - Frame 26: Arroba oficial `@vpsblindada.ia` com `InstagramIcon` SVG.
  - Karaokê: Desligado no cartão final.
  - Variação 20% vs 80%: > 15% (> 4%).
