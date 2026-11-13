# Design Técnico — Shorts como Subproduto do Deitado

> Detalhamento de implementação da seção 6 do `PLANO_ANIME_DEITADO_V2.md`.
> Ideia-chave da dona: short NASCE do trabalho do deitado, em vez de ser garimpado.

---

## 1. Por que isso é forte
- Dor atual: algoritmo não acha bons trechos curtos, e "cortar N pedaços e juntar" fica artificial.
- Inversão: o short **já nasce** do pipeline de deitado.
- Dois subprodutos gratuitos, ambos com narração+legenda já prontas:
  - **Cold-open** (abertura empolgante) — vira short/trailer direto.
  - **Beats dramáticos marcados** — viram shorts dos melhores momentos.

---

## 2. Subproduto A — Cold-open → short (TRIVIAL)

O cold-open da seção 4.4 do plano mestre ("hoje você vai ver um homem que superou tudo...") tem 100% das qualidades de um bom short:
- Gancho no 1º segundo.
- Auto-contido (não precisa de contexto prévio).
- Duração curta (a definir — alinhar com gosto da dona; ~15-30s é o sweet spot pra Shorts/TikTok).
- Funciona como trailer que leva pro vídeo longo.

### Implementação
1. Durante a pós-produção do deitado, exportar o cold-open em DOIS arquivos: `cold_open_landscape.mp4` (16:9, vai no início do longo) e `cold_open_short.mp4` (9:16, vai pro canal de shorts).
2. Reenquadrar 9:16: como o cold-open já tem composição pensada (fundo + texto + talvez personagem), o reframe pode ser simples (`crop=ih:iw*9/16`) ou crop no personagem via cutout (Tier 3).
3. Postar nos canais via pipeline de shorts existente (`anime_discover.discover_shorts` adaptado OU bypass — esse short NÃO é descoberto, é decidido).
4. Custo extra: zero. Só mais um export no pós.

---

## 3. Subproduto B — Melhores trechos → shorts (junto do Tier 1)

### Como
- O motor de graus (seção 2 do plano) já marca os **beats dramáticos** via Motion Director em camadas (regex de palavra-gatilho: `morre|revela|ataca|grita|desperta|destrói|surge`). Esses beats são os pontos de cutout/freeze — e são **exatamente** os melhores pontos de short.
- Pra cada beat, o `fx_planner.py` gera:
  - `beat_window`: range de frases/frases próximas (ex: 5 antes + 5 depois).
  - `short_meta`: início (timestamp source), duração total (~30-60s), texto condensado pra título.
- O pipeline então extrai o intervalo do vídeo final (`final_anime_deitado.mp4`), reenquadra 9:16, e gera um short.

### Reframe: o ponto delicado
Regra geral no recap (memória `feedback-shorts-fonte-vertical`): **shorts 9:16 DEVEM vir de fonte vertical, não 16:9 reenquadrado**. Mas aqui temos uma exceção honesta: a fonte do reframe é o **NOSSO recap já produzido**, não o anime cru. Vale testar:
- **Opção 1:** reframe simples `crop=ih:iw*9/16` (perde laterais).
- **Opção 2:** blur de fundo nas laterais (preenche 9:16 sem cortar o conteúdo).
- **Opção 3:** crop inteligente no personagem via cutout (Tier 3, mais caro).

Testar em 1-2 shorts reais antes de automatizar.

### Decisão pendente da dona
- **Automático**: top 3-5 beats sozinhos viram shorts (100% autônomo, escala).
- **Curadoria**: pipeline lista os candidatos (com thumbnail+preview+score), dona aprova quais viram short.

Recomendo começar **curadoria** (menor risco, aprende o que funciona) e evoluir pra automático quando o gosto estiver calibrado.

### Implementação
1. Após render do deitado, `short_candidates.py` lê `plano.json` e gera lista de candidatos com metadata (início, fim, duração, texto do beat, mood, # de frases).
2. Modo automático: pega top N por score (combinação de dramaticidade + duração ideal).
3. Modo curadoria: gera previews 720p + manda pra dona aprovar via lista.
4. Aprovado → corta + reenquadra + exporta como short.

---

## 4. Ganhos práticos
- **Resolve a dor dos shorts** (sem descobrir candidatos novos).
- **Volume**: cada deitado pode render ~3-5 shorts (top beats) + 1 cold-open = até 6 saídas por vídeo longo.
- **Reaproveita TTS, legenda, música**: tudo já foi feito no deitado.
- **Calendário**: longos e curtos saem juntos, posting escalonado fica natural.

---

## 5. Riscos / cuidados
- **Reframe ficar ruim** mata o short. Mitigar com 3 opções testadas + curadoria inicial.
- **Beats ruins** (falso positivo na regex): Motion Director usa camada IA pra filtrar; começar com limiar alto (só keywords muito fortes).
- **Direitos**: o recap já é descaracterizado (re-narrado). O short também é. Não muda nada em termos de copyright.
- **Performance**: extrair short do vídeo final é rápido (ffmpeg trim), mas se houver muitos shorts por vídeo, vale gerar na fase de pós em lote.

---

## 6. Ordem sugerida
1. **Implementar Subproduto A primeiro** (trivial, baixo risco, alto ganho).
2. **Implementar Subproduto B** junto com Tier 1 (quando as marcações de beat já existirem).
3. **Curadoria antes de automático** — calibrar o gosto.