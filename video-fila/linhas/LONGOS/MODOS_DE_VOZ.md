# Modos de voz — Shorts e longos (dona, 18/11/2026)

Decidido pela dona depois do teste de ouvido P0..P6 (`amostras_voz\estudo_motores_kaggle_1711\final\TESTE_DE_OUVIDO`,
gabarito em `GABARITO.txt`): "o P0 não faz mais sentido; temos centenas de vídeos prontos, então podemos usar o
modelo melhor". A ordem quando a produção apertar está no fim.

## Os modos (chave `VOZ_MODO`, lida por `anime_tts._voz_modo()`)

| Modo | O que é | Onde | Estado |
|---|---|---|---|
| **kitten_tudo** (padrão com GPU) | Kitten 2 com a voz pronta "Portuguese" em todas as frases + RVC do narrador por cima + todas as técnicas de produção | Kaggle com GPU (longos e Shorts de lá) | **ATIVO** a partir da próxima sessão (18/11); teste de ponta a ponta no código de produção OK (Barba Branca, 10/10 falas em 133 s) |
| **p3** (padrão) | revezamento Kokoro / Francisca / Piper + técnicas. Kokoro no gancho, nas subidas e nos impactos; Francisca e Piper revezam o resto com teto de 50 s seguidos. Onde há GPU, entra o Kitten 2 no gancho, nas perguntas e no clímax | PCs (sem GPU) hoje; Kaggle depois | **ATIVO** no PC1, desktop e PC2 (18/11) |
| **p1** | Kokoro no gancho e nas subidas, Francisca no resto + técnicas | reserva | ativo como queda automática |
| p0 | base única por vídeo, sem mistura | aposentado | só com `VOZ_MODO=p0` ou `ANIME_MISTURA=0` |

"Técnicas de produção" = tudo que já existia: clone 2.0 (perfil medido do narrador), climas por trecho (tensão, épico,
vilão, triste, ação... — mudam tom, ritmo, pausa e fim de frase), curva de clímax, humanizar (pausas, ênfase, ritmo,
vibrato, fundo de sala, respiração real quando o narrador tem), variação de frase para frase na força do clone.
No p3 o clima NÃO troca mais a base (antes tensão/épico forçavam Francisca e ação forçava Kokoro).

## Queda automática (nunca estraga o vídeo)
- `p3` sem o Piper instalado na máquina, ou sem voz clonada → cai para `p1`.
- Fora do Windows (STI, Kaggle) o Piper ainda não é gerado → `p1`.
- Frase com base "piper" e Piper indisponível → sai na Francisca.

## Arquivos
- `recapd-ambientes\producao\bin\anime_tts.py`: `_voz_modo`, `_piper_pronto`, `_base_p3`, `base_da_frase`;
  `preparar_clone` (item do lote com `motor: "piper"`, `tom_base: "3_piper"`); `_frase_v2` (Piper usa o perfil do Kokoro).
- `hipercool-materiais\bin\voz_clonada.py`: `_piper()` (modelo aberto 1x por processo), `_base_tts("piper:cadu")`, lote.
- Modelo: `hipercool-materiais\models\piper\pt_BR-cadu-medium.onnx` (rhasspy/piper-voices, MIT).
- Amostra-padrão do tom: `amostras_voz\2026-10-18_vozes_clonadas\_bases\3_piper.wav` → `tom_fixo(voz, "3_piper")`
  calcula sozinho o tom do clone de cada narrador (fica em `models\rvc\vozes\<voz>\tom_3_piper.txt`).
- Pacote `piper-tts==1.8.0` no `venv_vozes` (instalado com `--no-deps`; usa o onnxruntime que já estava; torch intacto).

## Onde está implantado (18/11)
| Máquina | Modo efetivo | Observação |
|---|---|---|
| PC1 | p3 | |
| Desktop (PC3) | p3 | teste de ponta a ponta: `versao_P6_p3_producao_real.mp4` |
| PC2 | p3 | conferido com o `subst D: C:\` da produção |
| STI | p3 | teste de ponta a ponta pelo `voz_clonada_nuvem` (Linux). O STI nunca tinha usado Kokoro: instalado `kokoro-onnx==0.6.1` e ligado `KOKORO_NUVEM=1` no `sti_short.sh` |
| Kaggle (longos e Shorts na GPU) | p3 a partir da próxima sessão | Piper instalado pelo `kaggle_trabalhador._preparar_applio` (central na hermes-prod); modelo do Piper no pacote (`montar_pacote.assets`); `tom_3_piper.txt` de 107 vozes no cache `colab_recap/vozes` |

O que a sincronização automática NÃO leva (feito à mão em 18/11; máquina nova precisa repetir):
- pacote `piper-tts==1.8.0` (`--no-deps`) no `venv_vozes`; no STI também `kokoro-onnx==0.6.1`;
- `models\piper\pt_BR-cadu-medium.onnx` (+ `.json`) e `amostras_voz\2026-10-18_vozes_clonadas\_bases\3_piper.wav`;
- `tom_3_piper.txt` em cada `models\rvc\vozes\<voz>` (o `tom_fixo` cria sozinho no Windows se a amostra existir).
vcozes\<voz>` (o `tom_fixo` cria sozinho no Windows se a amostra existir).
Voz nova no Drive: rodar `voz_clonada.tom_fixo(voz, "3_piper")` e subir o `tom_3_piper.txt` junto.
Backups: `anime_tts.py.bak_20261118_*`, `voz_clonada.py.bak_*`, `voz_clonada_nuvem.py.bak_*`, `sti_short.sh.bak_*`;
central: `kaggle_trabalhador.py.bak_20261118_0931_antes_piper`.

## kitten_tudo — como funciona (18/11)
- Dona escolheu a voz PADRÃO do Kitten (sem copiar o jeito de áudio real): "o que me preocupa são os personagens famosos".
  Teste das 3 referências (real / clone / padrão) em `TESTE_DE_OUVIDO\versao_K_ref_*.mp4`: mesmo tempo (±3%); o padrão
  não precisa de preparo nenhum por voz.
- `anime_tts._voz_modo()`: sem `VOZ_MODO`, usa `kitten_tudo` se `_kitten_pronto()` (não-Windows, `KITTEN_NUVEM=1` e
  `tom_4_kitten.txt` do narrador); senão `p3`; senão `p1`. Nos PCs nunca liga (forçar também cai pro p3).
- `kaggle_trabalhador.preparar_applio()` (central e PC1): só com GPU, cria `/tmp/venvs_voz/kitten2`
  (`--system-site-packages`, `kittenml` + `soundfile`) e liga `KITTEN_NUVEM=1`. `KITTEN=0` desliga.
- `voz_clonada_nuvem._bases_kitten()`: gera todas as frases de um vídeo num processo só (modelo abre 1x, ~35 s; ~5 s
  por fala); falhou uma frase = ela sai no Kokoro.
- Tom do clone: amostra `_bases\4_kitten.wav` (10 falas reais do Kitten padrão, 42 s, mediana 137 Hz) ->
  `tom_4_kitten.txt` em 107 vozes, no PC1 e no cache `colab_recap/vozes`. Voz nova: `voz_clonada.tom_fixo(voz, "4_kitten")`.
- 18/11: 18 vozes do cache do Kaggle estavam SEM `tom_1_kokoro`/`tom_2_edge_francisca` (falha antiga: subiam sem o tom
  e o clone usava tom 0 na Francisca). Completadas.
- Memória da GPU com Kitten + clone + render: NÃO medida. Se apertar: `VOZ_MODO=p3` na sessão (ordem abaixo).

## Custo de tempo (voz, medido/estimado)
- p3 sem Kitten nos PCs: ~igual ao de hoje. O Piper abre em ~20–45 s uma vez por processo e gera cada frase em ~0,6 s.
- p3 com Kitten (GPU): +~30% na voz do Short (Kitten aberto entre os Shorts); +13–28% no longo (Kitten com teto).
- kitten_tudo (GPU): +~75% na voz do Short; +140–170% na voz do longo. Memória da GPU estimada 3–5 GB (NÃO medida).
- Sem GPU o Kitten leva ~30 min por frase: nunca nos PCs.

## SE A PRODUÇÃO APERTAR (dona: "deixa documentado")
1. GPU com fila → trocar `kitten_tudo` por **p3 com Kitten** (`VOZ_MODO=p3` no Kaggle).
2. Ainda apertado → **p2/p3 sem Kitten** (o padrão dos PCs).
3. Último recurso → **p1** (`VOZ_MODO=p1`).
Nunca voltar ao p0.
