# 01 — MoneyPrinterTurbo (⭐94k) → WordBoundary do edge-tts

Clone: `D:\outros projetos para extrair melhorias\MoneyPrinterTurbo`
Veredito: 🟢 **ALTO VALOR.** Resolve a queixa #2 ("legenda só aparece no começo / dessincroniza")
na RAIZ, de graça, reusando o edge-tts que já usamos.

## O PROBLEMA no nosso código (medido, não suposto)
- `bin/edge_tts_engine.py:202` — geramos áudio com `await communicate.save(out_path)`.
  O `.save()` **descarta** os eventos de timing que o edge-tts emite. Saímos só com o .mp3.
- Consequência: em `bin/effects_engine.py:2544` (`render_subtitles_short`), como NÃO temos o
  tempo real de cada palavra, **estimamos**: fatiamos a duração do clip proporcional ao
  TAMANHO de cada palavra (linha ~2572, `weights = [max(2, len(w)) for w in words]`).
  Essa estimativa erra e ACUMULA → a legenda "anda" e some/atrasa nas falas seguintes.

## O QUE O MoneyPrinterTurbo FAZ (a peça a copiar)
Arquivo: `app/services/voice.py`, função `azure_tts_v1` (linhas ~721-759).
Em vez de `.save()`, ele consome o STREAM e captura os eventos de boundary:

```python
communicate = edge_tts.Communicate(text, voice, rate=rate_str)  # +boundary="WordBoundary" no 7.x
sub_maker = edge_tts.SubMaker()
with open(voice_file, "wb") as file:
    def _handle_chunk(chunk):
        if chunk["type"] == "audio":
            file.write(chunk["data"])
        elif chunk["type"] in ["WordBoundary", "SentenceBoundary"]:
            sub_maker.feed(chunk)   # <-- guarda offset+duração de CADA palavra
    # consome communicate.stream() chamando _handle_chunk em cada chunk
```
Cada chunk WordBoundary traz `offset` e `duration` em unidades de 100ns (dividir por 1e7 = segundos).
Isso é o TIMING REAL da palavra, dito pela própria voz — não estimativa.

Detalhes úteis no mesmo arquivo:
- `mktimestamp()` (linha ~45): converte 100ns → timestamp. Já temos lógica equivalente, mas serve de ref.
- Compatibilidade edge_tts 7.x: no 7.x passa-se `boundary="WordBoundary"` no Communicate e usa
  `stream_sync()`; no antigo, `stream()` async já emite os boundaries. Ver `create_edge_tts_communicate`
  e `stream_edge_tts_chunks` (linhas ~580-718). COPIAR esse cuidado de versão.

## PLANO DE IMPLEMENTAÇÃO (passo-a-passo)
**Não começar sem antes conferir md5 de `edge_tts_engine.py` e `effects_engine.py`.**

1. Em `bin/edge_tts_engine.py`, criar variante de `_generate_edge_tts` que NÃO usa `.save()`:
   - consome `communicate.stream()`, escreve os chunks `audio` no .mp3
   - acumula os `WordBoundary` numa lista `[(start_s, end_s, word), ...]`
   - retorna essa lista junto (ou grava um sidecar `.words.json` ao lado do .wav).
2. `speak()` passa a devolver/persistir os word-timings. Manter a assinatura atual funcionando
   (fallback: se a lista vier vazia, cai no comportamento de hoje — não quebrar nada).
3. Persistir os timings no cache de TTS (`tts_cache.py`) junto com o áudio — assim não recalcula.
4. Em `effects_engine.render_subtitles_short`, se houver word-timings reais para a entry,
   USAR eles em vez de `word_durs` estimado (linha ~2572-2588). Sem timings → estimativa atual.
5. Os tempos do edge-tts são RELATIVOS ao clip; somar o offset absoluto do clip
   (`_CLIP_ABS_STARTS[i]`) — o MESMO relógio que já usamos hoje. Cuidado: o áudio passa por
   apad/atrim no concat (sync fix), então validar que o offset de palavra bate pós-concat.
6. VALIDAR: gerar um cap de teste e conferir no vídeo que cada palavra acende no tempo certo
   até o FIM (não só no começo). ffprobe pra duração/sync.

## ⚠️ ARMADILHAS
- edge-tts com `rate`/`pitch` != 0 muda a duração real → bom, porque o WordBoundary já reflete isso
  (outra razão pra usar o real e não estimar).
- Pitch/rate por persona (nosso `_get_voice_profile`) continua válido — o boundary vem do áudio final.
- Proxy Webshare: o nosso fluxo de proxy/fallback (linhas 367-424) precisa ser preservado na
  variante de stream. NÃO perder o retry direto→proxy ao trocar `.save()` por `.stream()`.

## O que NÃO copiar do MoneyPrinterTurbo
- Toda a camada FastAPI/Redis/MVC (`app/controllers`, `app/router.py`) — não é nosso caso.
- `subtitle.py` usa faster_whisper pra TRANSCREVER áudio e achar timing. NÓS NÃO PRECISAMOS
  transcrever: já temos o texto (a narração é nossa) e o edge-tts nos dá o timing direto.
  Whisper seria reprocessar à toa. Ignorar o caminho whisper deles.
- `correct()`/`similarity()` (Levenshtein) servem pra casar transcrição com script — desnecessário pra nós.
