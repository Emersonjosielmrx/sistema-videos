# 12 — Controle de qualidade automático do vídeo inteiro
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Fato:** nós conferimos 3–4 quadros e um trecho de áudio. Erros no meio do longo (quadro preto, legenda fora do
tempo, mascote cobrindo a legenda, trecho sem narração, voz errada no revezamento, palavrão — 27/10 o KwdN foi ao ar
com "caralho") passam.

**Onde olhar:** `D:\recapd-ambientes\producao\colab\juri_longo.py` (folha de contato + júri de IA),
`colab\postar_longos.py` (`_curto`, `_tem_palavrao`, revisão de nudez no `anime_publish`), `bin\anime_publish.py`,
memórias "Análise do vídeo pronto", "Defeito visual não trava" (só censura trava), "Revisar na produção real".

**O que falta:** varredura do vídeo inteiro (amostra a cada N s + detecção de silêncio, quadro preto, dessincronia
legenda×fala por Whisper), com nota por trecho e bloqueio só do que a dona manda bloquear.

## Fable — resultado
**29/10 04:45 — feita a parte sem IA (`FABLE_DECISOES.md` D10).** `D:\recapd-ambientes\producao\bin\qa_video.py`:
uma passada de ffmpeg no vídeo inteiro (320 px) acha quadro preto ≥ 1 s, imagem parada ≥ 6 s, mudo ≥ 4 s, loudness
fora de −24…−10 LUFS, com os tempos; grava `qa.json` na pasta de saída e `meta["qa"]` no postar.json; avisa no
Telegram (importante só se grave). Ligado no `anime_publish` (Short e longo), só aviso — não trava. Teste: Short de
46 s em 7 s, −14,2 LUFS, sem problema. O palavrão já é pego pelo `_tem_palavrao` do postar_longos.
- Fica para depois (precisa de IA/Whisper, não medi): dessincronia legenda × fala (comparar `roteiro_tempos.json`
  com Whisper do áudio final em 3 trechos de 30 s — a cada 10 min — e marcar desvio > 1,5 s); mascote cobrindo
  legenda (comparar caixa da mascote com `SUB_Y_*` nos tempos das falas, sem IA — dá para fazer no próprio
  `qa_video` quando a mascote gravar onde ficou); voz errada no revezamento (comparar embedding Resemblyzer de cada
  trecho com a voz esperada do `roteiro_falas.json`).
