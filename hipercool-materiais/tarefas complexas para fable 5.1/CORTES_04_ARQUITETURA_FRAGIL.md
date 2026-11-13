# CORTES — 04 — Acoplamentos escondidos (3 defeitos só em 28/10)

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES em 28/10/2026.

## Fatos (todos corrigidos, mas o padrão continua)
1. **Variável de ambiente com dois sentidos**: `ANIME_TTS_VOICE` = "voz do nicho do parceiro" (anime_auto.py ~558)
   E "esta é a versão em outra língua" (anime_idiomas.py ~119). Uma mudança para a outra língua estragou o pt.
2. **Resultado preso no processo filho**: anime_auto -> anime-pipeline.py (subprocesso) -> anime_publish.py (outro
   subprocesso). O "o que foi usado" dos testes T5/T6 ia por `os.environ` e morria no filho; nenhum postar.json teria
   o valor. Remendo: `_testes_usados.json` na pasta do vídeo (`fx_subtitles.marcar_usado`).
3. **Pasta compartilhada sem dono**: as camadas do Remotion dos Cortes estavam em
   `D:\claude-code-video\remotion\src\videos\`, que a linha CLAUDE-CODE-VIDEO limpa a cada vídeo -> "No entry point
   specified" intermitente. Mudadas para `src\_cortes\`.
- Também: `cortes_ajustes.json` é lido em vários módulos; o config do PC2 (`C:\recapd-e-animes\config`) está igual
  ao do PC1, mas o `sincronizar_bin` (`D:\video-fila\pc2_recapd.py`) diz que nunca copia config — esta sessão não
  achou quem sincroniza.

## Para o Fable
1. Auditar o fluxo anime_auto -> pipeline -> publish (e anime_idiomas, parceiro_diario, controlador.py) atrás de
   outros acoplamentos assim: variáveis de ambiente reaproveitadas, estado que não atravessa processo, pastas
   limpas por outra linha, arquivos lidos por PC1 e PC2 com versões diferentes.
2. Propor um "contexto do vídeo" único (um json por Short com tudo que foi decidido/usado) no lugar das variáveis
   de ambiente — sem reescrever a produção de uma vez (ela não pode parar: nenhum canal fica 1 dia sem postar).

## Fable — resultado
**29/10 04:00 — auditoria (tarefa 1) feita por varredura; proposta (tarefa 2) com caminho de migração sem parar.**
1. **Inventário:** 18 variáveis de ambiente são ESCRITAS num arquivo e LIDAS em outro (processo filho ou módulo):
   `ANIME_DESCARACT_FLIP` (auto→fx_clips), `ANIME_HARDSUB_DETECT` (auto→pipeline, _relegenda_antigos),
   `ANIME_PERSONAGEM_FALAS` e `ANIME_RESUMO_N` (pipeline→anime_segments, fx_clips), `ANIME_TTS_VOICE` (auto→anime_tts;
   o caso 1 deste arquivo), `CORTES_COBERTURA_USADA`, `CORTES_CURTO`, `CORTES_GANCHO_MEIO`, `CORTES_LEGENDA_ESTILO`
   (auto→publish/script/fx_subtitles), `CORTES_FX_CHOQUE` (auto→fx_subtitles), `CORTES_GANCHO_REMOTION`, `GANCHO_Y`
   (auto→anime_gancho), `CORTES_MASCOTE` (auto→anime_captions), `NICHO_CLONE` (auto→anime_script), `SUB_Y_CENTER`
   (**escrita em dois lugares**, pipeline E auto, lida em 4 — mesmo padrão do caso 1), `TEXTO_VIDEO_MODELO/RESERVA/
   TIMEOUT` (auto→claude_client, anime_tts, publish). Comando para refazer a lista: grep de `os.environ["X"] =`
   contra `environ.get("X")` em `bin\*.py` (está no histórico desta sessão; vale pôr num `make`/script da linha).
   Tudo que o render do filho DECIDE (T5/T6/T7) só volta pelo `_testes_usados.json` — certo, é o padrão a seguir.
2. **Proposta — "contexto do vídeo" sem reescrever:** um `contexto.json` na pasta do vídeo, escrito pelo `anime_auto`
   UMA vez antes de chamar o pipeline, com tudo que foi decidido (testes, voz, nicho, cobertura, ajustes de texto);
   e um módulo de 20 linhas `cortes_contexto.py` com `get(chave, padrao)` que lê **primeiro o env (compatível), depois
   o contexto.json** (acha a pasta por `CORTES_WORK` ou pelo cwd). Migração: (a) hoje o `anime_auto` já escreve o json
   além do env — zero risco; (b) cada módulo troca `os.environ.get("CORTES_X")` por `cortes_contexto.get("X")` quando
   for mexido por outro motivo; (c) quando nenhum leitor usar env, o `anime_auto` para de exportar. O `publish` passa a
   copiar o contexto inteiro para o `postar.json` (um campo `contexto`), e o placar lê de lá — acaba o "esqueci de
   registrar o teste no postar.json" (T5/T6 de 28/10). Variável com dois sentidos (`ANIME_TTS_VOICE`, `SUB_Y_CENTER`):
   viram duas chaves no contexto (`voz_nicho` × `idioma_versao`; `sub_y_short` × `sub_y_longo`).
3. **PC1 × PC2:** `cortes_ajustes.json` precisa ir junto no `sincronizar_bin` (`D:\video-fila\pc2_recapd.py`) — hoje
   igual por sorte. Não mexi (é o PC2 do hipercool; mudança só pela dona), mas o T8 (`curto`) só vale no PC1 até lá:
   no PC2 a chave não existe e o `_aj.get("curto", "ab")` sorteia igual — então funciona, mas uma decisão `"A"/"B"`
   no PC1 não chega ao PC2. Registrar isso ao fixar o T8.
