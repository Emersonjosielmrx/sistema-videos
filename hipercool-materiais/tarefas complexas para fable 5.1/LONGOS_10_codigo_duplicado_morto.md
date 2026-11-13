# 10 — Código duplicado/divergente e código morto
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Fatos:** `D:\recapd-ambientes\producao\bin\parallax25d.py` tinha erro de sintaxe e nunca rodou (corrigido 28/10);
o glitch de cor do longo entrava nos trechos errados (corrigido 28/10); há `fx_clips.py`, `hiper-pipeline.py`,
`landscape-compiler.py`, `parallax_engine.py`, `panel_fx_auto.py` em VÁRIOS projetos e dezenas de `_SNAPSHOT*`,
`_BACKUP*`, `.bak*` dentro de `bin\` (o pacote do Kaggle exclui, mas grep/IA se perdem neles).

**Onde olhar:** `D:\hipercool-materiais\comum\` + `recursos.py` (código comum, cópia "# COMUM"), `D:\recapd-ambientes\
producao\bin`, `D:\hipercool-videos\bin`, memória "Código comum (recursos.py)".

**O que falta:** mapa do que é chamado de verdade (rotas reais desde as tarefas agendadas do Windows), o que nunca
roda, e onde a cópia de um projeto divergiu da outra com bug. Cuidado: limpeza do D: já derrubou a produção uma vez
(memória "Limpeza do D: com segurança") — mover, não apagar, e só depois de provar que nada usa.

## Fable — resultado
**29/10 (Fable) — dois levantamentos feitos, nada apagado nem movido.**
1. **Sintaxe (py_compile em todos os `*.py` de 16 pastas de produção):** resultado em
   `D:\video-fila\engenharia_reversa\sintaxe_29-10.txt`. **4 arquivos que NUNCA rodaram:** no `recapd\bin`
   `duracao_protegidos.py`, `gerar_blocklist.py`, `listar_protegidos.py` (SyntaxError; os 3 têm cópia divergente no
   postador que compila → a do recapd é a morta) e **`historias-em-frames\bin\parallax25d.py`** ("`_DEPTH_PIPE` is
   used prior to global declaration" — o MESMO bug corrigido em 28/10 só na cópia do recapd; prova viva do item 2).
   Todo o resto (16 pastas) compila. Repetir a varredura é 1 comando (está no histórico; vale uma tarefa semanal no
   `semanal.bat` da engenharia reversa).
2. **Duplicados entre projetos (md5, sem _SNAPSHOT/_BACKUP/.bak):** 108 nomes de arquivo repetidos em 2+ projetos;
   36 IDÊNTICOS (os do `hipercool-materiais\comum`, como manda o `recursos.py`) e **~72 DIVERGENTES**. Os que
   importam, por serem o coração de cada pipeline e terem 3–4 versões diferentes: `claude_client.py` (4: hipercool 4k,
   recapd 27k, postador 16k, histórias 17k — a cadeia de modelos D7 só existe na do recapd), `gemini_llm.py` (4),
   `fx_clips.py` (3: 43k/100k/70k), `fx_subtitles.py` (3), `hiper-pipeline.py` (3), `censura_visual.py` (3: 39k/21k/15k),
   `seo_generator.py` (2: 26k × 9k), `narration.py` (89k × 28k), `parallax25d.py` (3 — a corrigida em 28/10 foi só a do
   recapd; postador e histórias têm outras versões), `elemental_transitions.py`, `mascote_overlay.py`,
   `panel_effects.py`, `queue-runner.py`. Comando do mapa: no histórico desta sessão (md5 por nome em 12 pastas).
3. **O que fazer, na ordem segura:** (a) promover para `comum` só o que já é IGUAL (0 risco); (b) para cada divergente
   do núcleo, decidir qual é a "fonte" (a maior/mais nova em uso) e pôr nas outras um cabeçalho "# DIVERGE de
   <projeto>/<arquivo> — ler antes de corrigir aqui" (corrigir bug em uma cópia e esquecer as outras é o padrão do
   `parallax25d`); (c) rotas reais: as tarefas agendadas apontam para poucos pontos de entrada (`anime_auto`,
   `parceiro_diario`, `fila.py`, `postar_tudo_hoje`, `notificar_telegram`, `vitrine`, `controlador`…) — um
   `python -X importtime`/`sys.modules` dump no fim de cada entrada por 1 dia lista o que é importado de verdade; o
   resto é candidato a `_morto\` (mover, não apagar, conferindo no Drive). Não fiz o dump: exige rodar a produção com
   instrumentação e a regra é não tocar nela de madrugada sem a dona.

**29/10 tarde (sessão LONGOS):** `historias-em-frames\bin\parallax25d.py` corrigido (mesmo `global _DEPTH_PIPE` duplicado; compila). Os 3 scripts mortos do recapd e os ~72 divergentes: não mexidos.
