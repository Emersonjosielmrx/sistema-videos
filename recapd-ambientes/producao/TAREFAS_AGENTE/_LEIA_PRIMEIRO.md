# 📋 TAREFAS PENDENTES PARA AGENTE — LEITURA OBRIGATÓRIA

> Se você abriu um chat novo neste projeto, **LEIA ESTE ARQUIVO ANTES DE QUALQUER COISA.**
> Ele lista melhorias APROVADAS pela usuária, portadas do fluxo n8n "fábrica de animes",
> que ainda NÃO foram implementadas. Cada tarefa tem um doc próprio nesta pasta.

## ⛔ REGRAS QUE VALEM PRA TODAS AS TAREFAS DAQUI
1. **NÃO mexer em CENSURA.** Outro agente cuida disso (`bin/censura_visual.py` + docs de censura).
   Se sua tarefa esbarrar em censura, PARE e registre — não toque.
2. **NÃO rodar 2 pipelines de vídeo ao mesmo tempo** (protege as chaves e a RAM). Antes de
   gerar QUALQUER vídeo de teste, confira se há render rolando:
   ```bash
   powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.Name -match 'ffmpeg|python' } | Select-Object ProcessId,Name"
   ```
   Se listar ffmpeg/python de pipeline → NÃO gere vídeo, só faça self-test do módulo.
3. **Cópia certa:** `D:\hipercool-inferior-fix`. Teste: `grep -c render_subtitles_short bin/hiper-pipeline.py` → deve dar **>0**. Se der 0, você está na cópia errada, PARE.
4. **Python:** `D:\hipercool-videos\venv\Scripts\python.exe` (a -fix não tem venv próprio). Sempre exportar `PYTHONUTF8=1` (console Windows é cp1252 e quebra em acentos/box-drawing).
5. **Trabalho LOCAL.** Não commitar/pushar sem a usuária confirmar.
6. **Cada tarefa exige analisar o JSON ORIGINAL do n8n** (a fonte da verdade das tabelas/regras).
   Caminho: `D:\downloads\fabrica de animes-1-funcional copy 2.json` (32 nós).
   Para ler nós sem quebrar encoding, use Python com `encoding='utf-8'` e grave a saída em arquivo:
   ```python
   import json
   d = json.load(open(r"D:\downloads\fabrica de animes-1-funcional copy 2.json", encoding="utf-8"))
   nodes = {n["name"]: n for n in d["nodes"]}
   # o nó relevante de cada tarefa está indicado no doc da tarefa
   ```

## 📊 STATUS (atualizado 2026-06-30 23:50)
> 11 das 13 tarefas n8n FEITAS (self-test isolado; falta validar em render completo).
> Docs concluídos movidos pra **`_CONCLUIDAS/`** (histórico). Na raiz fica SÓ o que falta.

### ✅ CONCLUÍDAS (em `_CONCLUIDAS/`) — não precisa reabrir
- T1 viralizador · T2 tags-emoção · T3 fila-resiliente (Grupo A completo)
- T5 análise-adaptativa · T6 legenda-contexto · T7 movimento-emoção · T8 sfx-expandir · T9 perfis-qualidade (Grupo B)
- T11 merge-hierárquico · T12 robustez · T13 CTAs+capítulos (Grupo C)
- (+ T14 mascote, fora do índice original)
Cada uma: módulo + self-test + flag própria default OFF + registro em logs/night-shift.md.

### ⏳ O QUE FALTA (docs nesta pasta)
- **`TAREFA_4_memoria_continuidade.md`** — MÓDULO `effects_memory.py` pronto+testado; falta INTEGRAR
  no pipeline (coexistir com prefer_speed do T7; validar em render).
- **`TAREFA_10_paisagem_paineis.md`** — banco de fundos 16:9 FEITO (LS_FILTERS=1); falta o
  2-painéis-lado-a-lado (decisão de arquitetura A vs B + render).
- **`TAREFA_15_efeitos_mexe_no_painel.md`** — NOVA frente grande (catálogo de efeitos que
  transformam o painel: zoom/recorte/máscara). Protótipos validados; falta integrar. NÃO começada.
- **`TAREFA_18_sfx_vraa_reprovacao.md`** — integrar 12 SFX novos da curadoria (7 "vraa" +
  5 sons de reprovação/"deu ruim"), aprovados pela usuária. Disparo por KEYWORD em
  `pick_sfx_for_text`. Arquivos prontos em `_curadoria/_aprovados/sfx/`. NÃO começada.
- **`_PENDENCIAS_POS_IMPLEMENTACAO.md`** — itens que só validam em RENDER completo (máquina ocupada
  pelo render contínuo da -producao). Censura nível 3 aguarda referência da usuária.

> Validação em render: a máquina vive ocupada pelo render da versão -producao. Editar código é
> livre (cópias separadas); só NÃO rodar 2 renders pesados juntos. Por isso o que está feito é
> self-test isolado — o render completo de validação está pendente de janela ociosa.

### Grupo D — IDENTIDADE do canal (mascote). NÃO vem do n8n.
> Assets JÁ PRONTOS no projeto irmão `D:\hipercool-hyperframes` (poses + MOVs alpha animados,
> gerados 2026-06-30). A tarefa é só INTEGRAR via overlay ffmpeg, igual às transições elementais
> já feitas — zero IA, NÃO regera áudio/visão.
14. **`TAREFA_14_mascote_poses.md`** — integrar a garota propaganda (14 poses animadas) como
    overlay reagindo à narração do narrador. Flag `MASCOTE_OVERLAY=1` (default OFF). Doc-fonte:
    `D:\hipercool-hyperframes\MASCOTE_POSES_LEIA.md`.

## ✅ AO TERMINAR CADA TAREFA
- Rodar o self-test do módulo e colar o resultado no fim do doc da tarefa (seção "RESULTADO").
- Marcar a tarefa como `[FEITO AAAA-MM-DD]` no topo do doc dela e aqui na lista.
- Registrar no `logs/night-shift.md` o que foi feito.
- NÃO apagar este arquivo nem os docs — eles viram histórico.
