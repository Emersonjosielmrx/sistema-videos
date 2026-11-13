# TAREFA 4 — Sistema de Memória / Continuidade visual (MemorySystem)

STATUS: [~] MÓDULO PRONTO 2026-06-30 (effects_memory.py + self-test); INTEGRAÇÃO no pipeline pendente (coexistir c/ prefer_speed do T7 + instância por vídeo — validar em render)

> Leia antes: `_LEIA_PRIMEIRO.md` + `ANALISE_fluxo3_efeitos.md`. Não mexer em censura. Não rodar 2 pipelines.

## PROBLEMA QUE RESOLVE
Hoje cada painel sorteia filtro/movimento de forma ISOLADA → o vídeo "pula" de um grading
quente pra um frio, de pan pra baixo pra pan pra cima, sem coesão. O n8n resolve com um
histórico das últimas N páginas que puxa a escolha seguinte pra perto da anterior.

## PASSO 0 — OBRIGATÓRIO: analisar o JS original
Extraia o nó `aplica efeitos` de `D:\downloads\fabrica de animes-3-cria video pequeno copy.json`
(é `nodes[0].parameters.jsCode`, 5333 linhas) e leia:
- `class MemorySystem` (linhas ~910-1006): `record/getTrend/getAverage/shouldMaintainContinuity/suggestBasedOnHistory`.
- bloco `GLOBAL_CONFIG.memory` (~179-194): `smoothingWindow:3` e os `weights`
  (previousPage 0.5 / averageLast3 0.3 / contextual 0.2).
```python
import json
js = json.load(open(r"D:\downloads\fabrica de animes-3-cria video pequeno copy.json", encoding="utf-8"))["nodes"][0]["parameters"]["jsCode"]
print("\n".join(js.split("\n")[909:1006]))   # rode com PYTHONUTF8=1 → arquivo
```

## O QUE FAZER
- Criar `bin/effects_memory.py` com uma classe `EffectsMemory` (porte do MemorySystem):
  histórico em memória das últimas 3 escolhas por categoria (`color_grading`, `movement_dir`,
  `pacing`, `atmosphere`), com `record()` e `suggest(options)` que prefere a opção mais
  parecida com a tendência recente (peso da config).
- Integrar em `bin/effects_engine.py` no ponto onde o filtro/movimento é sorteado por painel
  (procure onde escolhe de `EFFECTS_LIST`/zoompan; ver `build_clip*` e `get_transition_and_sfx`).
  Em vez de `random.choice`, passar pelas sugestões da memória quando houver tendência.
- Flag `EFFECTS_MEMORY=1` (default OFF na 1ª versão, pra validar lado a lado).

## CUIDADO
- A memória é POR VÍDEO (resetar no início de cada `run_pipeline`). Não pode vazar entre capítulos.
- Não engessar: continuidade é PESO, não trava. Manter variação (não repetir exatamente o mesmo).
- effects_engine tem state global cuidadoso (`_CLIP_ABS_STARTS`); não colidir com isso.

## VALIDAR (sem render pesado)
- Self-test do módulo: simula 6 escolhas, mostra que a 2ª-6ª tendem à anterior mas variam.
- Se for gerar vídeo: checar render rodando antes (ver _LEIA_PRIMEIRO), usar TEST_MODE=2 e
  comparar 2 clipes (com/sem flag) — relatar se ficou mais coeso sem ficar repetitivo.

## RESULTADO (preencher)
- [ ] effects_memory.py + self-test
- [ ] integrado atrás de EFFECTS_MEMORY=1
- Observações:
