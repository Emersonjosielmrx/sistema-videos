# 🔌 MELHORIAS EXTERNAS — índice mestre (LEIA ANTES DE IMPLEMENTAR)

> **Agente: este diretório é OBRIGATÓRIO.** Antes de "melhorar legenda/transição/TTS/áudio"
> do hipercool, ABRA o doc da área aqui. Cada doc já comparou LINHA A LINHA o nosso código
> com um projeto open-source maduro e diz exatamente: o que copiar, o que NÃO copiar, e por quê.
> Não reinvente o que já foi analisado. Se for implementar, siga o passo-a-passo do doc.

> ⚠️ **NÃO confie só nestes resumos — LEIA O CÓDIGO-FONTE dos clones na hora de implementar.**
> Cada doc aponta o arquivo:linha exato no clone (`D:\outros projetos para extrair melhorias\...`).
> ABRA esse arquivo e leia em volta da função citada: (1) confirma que o resumo está correto e
> nada mudou, (2) pega detalhes de borda que o resumo condensou (tratamento de versão, edge cases,
> imports), (3) pode revelar OUTRAS peças úteis que não entraram no doc. Estes docs são um MAPA,
> não substituem ler o código real antes de copiar qualquer linha.

Analisado em 2026-06-30. Os 8 projetos estão clonados em
`D:\outros projetos para extrair melhorias\` (shallow clone, só pra estudo — NÃO são deps).

## Regra de ouro antes de mexer
1. `md5sum bin/*.py` e comparar com `_VERSAO_CORRENTE_LEIA.md`. Não bateu = outro agente mexeu → PARE.
2. Trabalhar LOCAL (sem commit/push sem confirmação). NUNCA rodar 2 capítulos juntos.
3. Congelar snapshot datado depois de mudança estável (ver convenção no handoff).
4. Validar com ffprobe (duração/áudio) antes de dizer "pronto".

## Os 8 projetos e o que cada um nos oferece

| # | Projeto | ⭐ | Doc | Veredito |
|---|---|---|---|---|
| 1 | **MoneyPrinterTurbo** | 94k | [01_moneyprinterturbo.md](01_moneyprinterturbo.md) | 🟢 ALTO — WordBoundary do edge-tts resolve legenda na raiz |
| 2 | **captacity** | 138 | [02_captacity.md](02_captacity.md) | 🟢 ALTO — agrupamento word-level que cabe na tela |
| 3 | **ShortGPT** | 7.5k | [03_shortgpt.md](03_shortgpt.md) | 🟡 MÉDIO — getCaptionsWithTime + arquitetura de engine |
| 4 | **xfade-easing** | 117 | [04_xfade_easing.md](04_xfade_easing.md) | 🟡 MÉDIO — easing nas transições xfade (sem easing hoje) |
| 5 | **auto-editor** | 4.5k | [05_auto_editor.md](05_auto_editor.md) | 🟢 ALTO — cortar silêncio da narração TTS |
| 6 | **moviepy** | 14.7k | [06_moviepy.md](06_moviepy.md) | ⚪ BAIXO — referência de efeitos; não adotar como dep |
| 7 | **auto-subtitle** | 2.2k | [07_auto_subtitle.md](07_auto_subtitle.md) | ⚪ BAIXO — só linha inteira; nada novo p/ nós |
| 8 | **AI-Youtube-Shorts** | 155 | [08_ai_youtube_shorts.md](08_ai_youtube_shorts.md) | ⚪ BAIXO — pipeline mais simples que o nosso |

## Ordem recomendada de ataque (maior retorno / menor risco primeiro)
1. **WordBoundary do edge-tts** (doc 01) — mata a queixa "legenda some/dessincroniza" na RAIZ,
   sem nova dependência, reusando o edge-tts que já temos. **Começar por aqui.**
2. **Agrupamento word-level** (doc 02/03) — melhora como as palavras viram cards de legenda.
3. **Cortar silêncio TTS** (doc 05) — narração mais "apertada", menos pausa morta.
4. **Easing nas transições** (doc 04) — transições mais suaves/profissionais.

## O que o nosso pipeline JÁ faz melhor que todos eles (NÃO regredir)
- Split de painéis de manhwa + leitura de balões por visão.
- Ensemble multi-modelo de narração com auditor + auto-tuning ([narration_ensemble.py]).
- ~50 transições elementais por keyword PT/EN ([elemental_transitions.py]).
- Timing de legenda por offsets reais pós-xfade (`_CLIP_ABS_STARTS`).
- Cache de TTS/visão, gap híbrido, concat em lotes anti-OOM.
> Nenhum dos 8 projetos faz isso. NÃO trocar nosso pipeline por nenhum deles — só extrair peças.
