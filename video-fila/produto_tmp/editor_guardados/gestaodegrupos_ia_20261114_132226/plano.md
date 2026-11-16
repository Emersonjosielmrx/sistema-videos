# Plano de Edição — Gestão de Grupos IA (`gestaodegrupos_ia_20261114_132226`)

## Dados Gerais
- **Produto**: Gestão de Grupos IA
- **Duração**: 31.44 s (944 frames a 30 fps)
- **Cores**: Marca/Destaque `#14B8A6` (Teal), Apoio/Fundo `#111827` (Dark Slate), Texto `#FFFFFF`
- **Tipografia**: Montserrat (todas as fontes ≥ 32 px, títulos ≥ 44 px, `textWrap: 'balance'`)
- **Safe Zone**: y: 150 a 1580, x: 60 a 1020
- **Áudio**: `narracao.mp3` contínua (0 a 944), `trilha.mp3` com ducking (volume 0.09 com fala, 0.18/0.22 nas pausas)
- **Karaokê**: componente oficial `src/lib/karaoke.tsx` com `base={390}` (base em y=1530, estritamente acima de y=1540), quebras por frase para evitar linhas órfãs, destaque ciano contínuo sem lacunas.

---

## Cena 0 (0.00s a 5.12s | Frames 0 a 153)
- **Tipo**: `pergunta`
- **Fala**: "Preciso ler todas as mensagens para saber o que rolou no grupo?"
- **Composição**: **a) + e)** — Abertura de alto impacto com gancho de urgência + push-in contínuo + notificações WhatsApp em cascata (SEM números inventados)
- **Fundo**: `img_0.jpg` com push-in contínuo (scale 1.02 → 1.25) e pan Y (0 → -45px) de 0 a 153 frames garantindo movimento > 4.0%
- **Elementos Visuais**:
  - y=175: Badge de urgência "⚠️ SEUS GRUPOS ESTÃO FORA DE CONTROLE?" (entra no frame 2)
  - y=255 a 480: Pergunta cinética sincronizada: "Preciso ler" (frame 4), "TODAS AS MENSAGENS" (frame 14), "para saber o que rolou no grupo?" (frame 38)
  - y=550 a 1180: Cards de WhatsApp entrando escalonados:
    - Frame 12: "Grupo Diretoria & Sócios" / "Mensagens não lidas acumuladas" (selo "NÃO LIDAS")
    - Frame 48: "Equipe Comercial & Vendas" / "Discussões em andamento" (selo "ACUMULADAS")
    - Frame 82: "Suporte & Projetos Ativos" / "Conversas acumuladas nos grupos" (selo "ALERTA")
    - Frame 105: Banner gancho "⚠️ CENTENAS DE MENSAGENS ACUMULADAS?" com 100% de opacidade e contraste sobre vermelho sólido
- **Transição**: Crossfade/wipe suave aos 4.77s (frame 143)

---

## Cena 1 (4.77s a 12.17s | Frames 143 a 365)
- **Tipo**: `dono`
- **Fala**: "Eu perdia muito tempo lendo centenas de mensagens acumuladas para entender o que acontecia nos grupos."
- **Composição**: **h)** — Vídeo cheio com câmera viva, punch-in digital jump cut em "centenas de mensagens acumuladas" e microanimações flutuantes laterais
- **Mídia**: `<OffthreadVideo src={staticFile('dono_1.mp4')} muted />` com plano médio inicial e corte dinâmico de zoom (1.16x → 1.22x) no frame 76
- **Proteção da figura humana**: Rosto totalmente livre entre y=320 e 1100
- **Elementos Visuais**:
  - y=165: Pill badge "O PROBLEMA"
  - y=230: Card escuro padronizado com borda e glow na ênfase: "CENTENAS DE MENSAGENS ACUMULADAS NOS GRUPOS"
  - y=420 e y=480: Microanimações flutuantes nas laterais (balões "💬 Centenas de mensagens" e "⚠️ Grupos acumulados")
- **Transição**: Slide suave aos 11.82s (frame 354)

---

## Cena 2 (11.82s a 20.02s | Frames 354 a 600)
- **Tipo**: `veo` (Como funciona)
- **Fala**: "O recurso de atas gera um resumo direto no grupo, organizando os principais pontos da conversa de forma prática."
- **Composição**: **b) + g)** — Motion design limpo com fundo abstrato da marca e smartphone central frontal com geração da ata do WhatsApp
- **Fundo**: Motion design abstrato com gradiente radial teal (#14B8A6/#111827), orbes pulsantes e linhas de rede (elimina conflito com crypto b-roll)
- **Elementos Visuais**:
  - y=165: Badge "⚡ COMO FUNCIONA • ATAS AUTOMÁTICAS"
  - y=235: Título em box escuro padronizado com borda teal: "RESUMO DIRETO NO GRUPO"
  - y=355 a 1150: Smartphone frontal com alta legibilidade:
    - Cabeçalho: "Grupo da Empresa", "Gestão de Grupos IA ativo" (28px, #5EEAD4), tag "Simulação" (24px, #FFFFFF)
    - Pergunta do usuário no grupo: "Quem pode resumir o que foi alinhado hoje?"
    - Card da ATA gerada automaticamente com checklist sincronizado com a voz (frame 36, 105, 156)
- **Transição**: Desfoque / corte suave aos 19.67s (frame 590)

---

## Cena 3 (19.67s a 27.85s | Frames 590 a 835)
- **Tipo**: `dono`
- **Fala**: "Hoje fico informado rapidamente sobre as conversas e mantenho meus grupos de WhatsApp no automático."
- **Composição**: **h) + b)** — Close-up mais fechado do apresentador (scale 1.32x → 1.42x) para romper monotonia + card dinâmico de automação na lateral em "no automático"
- **Mídia**: `<OffthreadVideo src={staticFile('dono_3.mp4')} muted />` com enquadramento close-up distinto da Cena 1
- **Proteção da figura humana**: Rosto totalmente livre
- **Elementos Visuais**:
  - y=165: Pill badge "✓ O RESULTADO"
  - y=230: Card com título padronizado: "GRUPOS DE WHATSAPP NO AUTOMÁTICO"
  - y=420 (lateral direita): Card dinâmico de automação surgindo aos ~24s (frame 130) ("WhatsApp no Automático" com moderação e resumos)
- **Transição**: Dissolve suave para o cartão final aos 27.5s (frame 825)

---

## Cena 4 (27.50s a 31.44s | Frames 825 a 944)
- **Tipo**: `cartao`
- **Fala**: "Chame a gente no direct."
- **Composição**: **Cartão Final de Alta Conversão Dinâmico**
- **Fundo**: `img_4.jpg` com blur intenso e push-in contínuo (scale 1.05 → 1.20)
- **Elementos Visuais**:
  - Avatar da marca com zoom contínuo lento (1.0 → 1.10) e levitação suave
  - Anel ambiental com pulso contínuo
  - Botão CTA "CHAME NO DIRECT" com pulso contínuo (1.0 → 1.04) e feixe de luz (sheen pass) contínuo
  - Perfil oficial "@gestaodegrupos.ia"
- **Sem Karaokê**: Foco total na chamada de ação.
