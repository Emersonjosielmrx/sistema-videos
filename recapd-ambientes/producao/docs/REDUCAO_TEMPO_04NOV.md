# Redução do tempo de geração dos longos — 04/11

Medido no waaQ (anime, 87 min de vídeo final): 318 min no Kaggle.
Legenda 97 min (30%) · junção dos clipes 63 (20%) · narração + clone 41 (13%) · montagem dos clipes 30 (9%) ·
música 26 (8%) · preparo 24 (8%) · master 13 (4%) · cortes 3 (1%).

## Decisões da dona (04/11)
- Roteiro: SEM trava de tamanho (nem mínima nem máxima) — narração a melhor possível.
- 2 (60 fps falso), 3 (música/master), 5 (esteira narração), 7 (Argon), 8 (Whisper GPU): fazer.
- 4 (legenda mais leve) e 6 (transição só na troca de cena): SÓ com vídeo de teste lado a lado pra ela ver.
  A legenda MIX é diferencial nosso.

## Feito (código no Drive colab_recap/raiz/.../bin — vale nos longos que começarem depois)
| Item | Onde | Ganho esperado |
|---|---|---|
| Roteiro sem trava (sem "NO MÍNIMO", sem refazer < 80%, max_tokens 5000) | anime_script.py | depende da obra |
| 2 — 60 fps falso | JÁ EXISTIA desde 01/11 (clipes a 30 fps, fps=60 só depois da legenda, fx_subtitles) | 0 (estimativa de 25% estava errada) |
| 3 — master -14 LUFS na junção das fatias da legenda | fx_subtitles._queima_em_fatias + anime-pipeline (ANIME_MASTER_NA_JUNCAO, _MasterFeito) | ~13 min (4%) |
| 5 — Edge em paralelo (4) no preparar_clone | anime_tts.py (_EDGE_POOL, ANIME_EDGE_PARALELO) | ~30 min (9%); teste PC: 8 frases 18 s -> 9,5 s, mesma duração |
| 7 — Argon com teto real de 90 s | anime_tts._criativo (ARGON_TETO_S) | ~5-9 min (2-3%) |
| 8 — Whisper na GPU (carrega libcublas/cudnn; instala se faltar) | anime_preparo_longo._carregar_cuda_libs | ~7 min quando não há roteiro |

Teste do 3 no PC: áudio -47,9 LUFS entrou, saiu -14,06; vídeo copiado, 2 fatias ok.

## Decisões da dona (04/11 ~02:30)
- Legenda: LEVE ligada nos longos (config\longo.json efeitos ANIME_LEGENDA_LEVE=1) — a COMPLETA é melhor, voltar
  quando der. Teste: hipercool-materiais\testes_legenda_04nov (A x B: 269 s x 201 s).
- Transições e efeitos: NÃO mudar (teste C/D/E: 40% gl 196 s, 10% 124 s, 0% 72 s — ela escolheu manter).

## 2 longos por sessão (CPU de um + GPU do outro) — subido 04/11 08:20
- colab\kaggle_trabalhador.py md5 952ab100 nas 4 centrais (junto com o baixador do chat dos curtos, 16a1ee88):
  loop_duplo, linha_uso (BASE/uso.log a cada 60 s; vai pra fila/<pid>/uso.log), _marcar com temporário por thread,
  fazer(pid, gpu). Só nas contas DOIS_LONGOS_TESTE = {emerso, emersonia}; TRAB_DOIS_LONGOS=1 liga em todas, =0 desliga.
- bin\anime_segments._vez_da_cpu (Drive): trava de arquivo TRAB_CPU_LOCK antes dos clipes; marca _fase_cpu.
- Simulação no PC (4 longos de mentira): GPUs 0/1 alternando, CPU nunca dupla, sessão sai sozinha; 45 s x 60 s.
- MEDIR: comparar horas/longo das 2 contas de teste (pronto.json "segundos" + uso.log) com as outras 7. Esperado
  ~25-30% mais longos por sessão (a parte de antes da CPU = 27% no waaQ). Se ok, ligar em todas.

## Falta
- Vídeo de TESTE (prévia no Kaggle, trecho ~3 min, mesmo trecho em 4 versões):
  A) legenda atual + transições como hoje (ANIME_GL_TRANS_CHANCE 0.4)
  B) legenda leve + transições como hoje
  C) legenda atual + transição só na troca de cena
  D) legenda leve + transição só na troca de cena
  "Legenda leve" ainda não existe: precisa de um modo com menos cartões animados por frase (hoje ~16/frase).
- Conferir no 1º longo com o código novo: log "[preparo] libs CUDA", "Whisper small (GPU)", "master ... (na junção
  da legenda)", tempo do bloco clone e o total.
