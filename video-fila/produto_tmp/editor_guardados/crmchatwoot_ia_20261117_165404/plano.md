# Plano de Edição — crmchatwoot_ia_20261117_165404

## Briefing & Regras
- **Marca / Produto**: CRM Chatwoot IA (`#1F93FF`, apoio/fundo `#111827`, texto `#FFFFFF`)
- **Fatos permitidos**:
  1. CRM personalizado a partir do Chatwoot, integração CRM e helpdesk/tickets
  2. CRM personalizado com IA
  3. Um CRM feito para o seu negócio a partir do Chatwoot, com atendimento, tickets e histórico de cada cliente em um só lugar.
- **Duração**: 29.12s (874 frames a 30 fps)
- **Safe Zone estrita**: x entre 60 e 1020, y entre 150 e 1580 em todos os quadros.
- **Fontes mínimas**: Todo texto, badge, rótulo e card com fonte >= 34px (títulos 48px a 72px).
- **Karaokê**: Componente oficial `<Karaoke>`, base=360 (y=1560), apenas nas cenas 0 a 3 (sem legenda no cartão final).
- **Variedade visual**: 5 composições distintas e sem repetição de templates idênticos.

---

## Cenas e Composições de Agência

### Cena 0 (0.00s – 5.00s) — `pergunta`
- **Fala**: "Perdendo controle dos atendimentos com ferramentas básicas?"
- **Composição**: **(b) Mockup 3D Isométrico Vivo de Fila Caótica + Tipografia Cinética de Impacto**
- **Movimento e Sincronia**:
  - Fundo com malha tech dinâmica, drift contínuo e orbs luminosos em `#1F93FF`.
  - 0.0s–0.3s: Banner de alerta vermelho vibrante no topo: **"PERDENDO CONTROLE"** (pop 0.31s).
  - 1.35s: Complemento **"dos atendimentos"** entra com translação e scale.
  - 2.10s: Conclusão **"com ferramentas básicas?"** com destaque ciano.
  - 1.80s: Selo fixo do gancho de tela: **"Chatwoot comum ou com IA?"**.
  - Centro (y=570–1270): Celular/painel isométrico 3D (`rotateY(-15deg) rotateX(6deg)`) flutuando com `Math.sin`.
  - Itens desorganizados entram escalonados (0.45s, 1.35s, 2.25s) com selos de alerta "Sem histórico", "Sem ticket", "Sem contexto".
- **Transição**: Wipe suave / scale-out (4.65s–5.00s).

### Cena 1 (4.65s – 11.83s) — `dono` (Rótulo: "O problema")
- **Fala**: "Uma ferramenta padrão de mensagens não entende a rotina específica da sua empresa."
- **Composição**: **(h) Vídeo do apresentador com push-in + Comparador Dinâmico Asimétrico no Topo**
- **Proteção do rosto**: Rosto livre entre y=460 e 1100. HUD concentrado no topo (y=165 a 420).
- **Movimento e Sincronia**:
  - Vídeo `dono_1.mp4` com zoom suave contínuo (1.0 -> 1.06).
  - 4.8s: Badge compacto superior esquerdo **"01 · O PROBLEMA"**.
  - 5.63s ("Uma ferramenta padrão de mensagens"): Card esquerdo surge — **"Ferramenta Padrão"** (Só mensagens soltas).
  - 8.05s ("não entende"): Carimbo central vermelho pulsa — **"✕ NÃO ENTENDE"**.
  - 9.35s ("a rotina específica da sua empresa"): Card direito em azul neon entra — **"Sua Empresa"** (Rotina & fluxo próprio).
- **Transição**: Desmonte em 11.48s e transição luminosa.

### Cena 2 (11.48s – 18.39s) — `dono` (Rótulo: "Como funciona")
- **Fala**: "Nós adaptamos o sistema com inteligência artificial para o fluxo do seu negócio."
- **Composição**: **(f) Pipeline de Arquitetura Conectada (Nodes SVG interativos) no Topo + Vídeo do Apresentador**
- **Diferenciação visual radical**: Layout não repete caixas de Cena 1 nem Cena 3; usa nódulos de arquitetura de software conectados por feixes luminosos.
- **Movimento e Sincronia**:
  - Vídeo `dono_2.mp4` com zoom progressivo (1.01 -> 1.07).
  - Topo (y=165 a 420): Badge central **"02 · COMO FUNCIONA"** + 3 nós de fluxo conectados:
    - 12.23s ("Nós adaptamos o sistema"): Nó 1 acende em azul — **Chatwoot Base**.
    - 14.43s ("com inteligência artificial"): Linha de pulso conecta ao Nó 2 em esmeralda/ciano com brilho — **Motor de IA**.
    - 16.49s ("para o fluxo do seu negócio"): Linha conecta ao Nó 3 em azul vivo — **Fluxo da Sua Empresa**.
  - Barra de status inferior no card indica a sincronização inteligente.
- **Transição**: Corte suave com feixe azul (18.04s–18.39s).

### Cena 3 (18.04s – 25.52s) — `dono` (Rótulo: "O resultado")
- **Fala**: "Sua equipe trabalha com muito mais clareza tendo tudo reunido no dia a dia."
- **Composição**: **(g) Vitrine Unificada All-in-One no Topo Direito + Vídeo do Apresentador**
- **Proteção do rosto**: Apresentador 100% livre. HUD no topo (y=165 a 430).
- **Movimento e Sincronia**:
  - Vídeo `dono_3.mp4` com zoom suave (1.02 -> 1.08).
  - 18.2s: Badge alinhado à direita **"03 · O RESULTADO"**.
  - 19.02s ("clareza"): Card de impacto **"✨ Mais clareza para a equipe"**.
  - 21.30s e 23.08s ("tendo tudo reunido no dia a dia"): 3 pilares essenciais confirmados do briefing entram conectados:
    1. **Atendimento centralizado**
    2. **Helpdesk & Tickets**
    3. **Histórico de cada cliente**
  - Banner inferior une os 3 em **"Tudo reunido em um só lugar"**.
- **Transição**: Zoom-through cinematográfico para o cartão final (25.17s–25.52s).

### Cena 4 (25.17s – 29.12s) — `cartao`
- **Fala**: "Chame a gente no direct."
- **Composição**: **(a/d) Cartão Final de Alta Conversão de Agência (sem espaços vazios)**
- **Distribuição vertical perfeita (y=180 a y=1540, x=60 a 1020)**:
  - Fundo com blur suave de `img_4.jpg` + gradiente orbital dinâmico com orbs de luz em movimento contínuo.
  - Topo (y=190–430):
    - Badge: `FEITO PARA O SEU NEGÓCIO`
    - Título da marca: **CRM Chatwoot IA** (72px, bold, relevo)
    - Resumo dos fatos: `Um CRM feito para o seu negócio a partir do Chatwoot.`
  - Centro (y=470–1040): 3 cards premium dos pilares permitidos com ícones em destaque e badges de validação:
    1. `Atendimento e histórico de cada cliente`
    2. `Integração CRM e helpdesk / tickets`
    3. `Personalizado com IA a partir do Chatwoot`
  - CTA Principal (y=1120–1270):
    - Botão vibrante em gradiente azul (`#1F93FF` a `#0284C7`), com pulso contínuo (`scale(1.0 a 1.05)`), reflexo de luz diagonal animado a cada 1.5s.
    - Texto exato: **"CHAME NO DIRECT"** (48px, bold 900).
  - Base (y=1330–1410):
    - Pill do Instagram: **`@crmchatwoot.ia`** (38px, bold 800).
- **Karaokê**: Desativado no cartão final (conforme especificação oficial).
