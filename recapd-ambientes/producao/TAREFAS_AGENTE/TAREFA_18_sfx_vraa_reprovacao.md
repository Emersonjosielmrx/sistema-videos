# TAREFA 18 — Integrar SFX novos da curadoria: "vraa" + sons de reprovação

> **[FEITO 2026-07-01]** 12 wavs copiados p/ workspace/assets/sfx/; disparo por keyword
> integrado no pick_sfx_for_text (effects_engine.py) entre o MEME direto e o contextual.
> Helper _pick_from_pool com anti-repetição (reusa _last_sfx_used). Self-test OK: vraa e
> reprovação alternam entre variações; texto neutro não dispara.
> Origem: sessão de curadoria. Regra de ouro respeitada (sons isolados via demucs de
> shorts de outros criadores usados só como PISTA; SFX curtos não têm "original limpo").
> Catálogo curadoria: vraa=`d706ddb8`, reprovação=`dff11dc0`.
> Doc-espelho na curadoria: `D:\hipercool-materiais\_curadoria\_aprovados\sfx\LEIA_INTEGRAR_vraa_prioridade.md`

## Onde estão os arquivos (12 wavs, mono 48kHz, loudnorm -16 LUFS)
`D:\hipercool-materiais\_curadoria\_aprovados\sfx\`
- **vraa** (grito de transformação/impacto): `vraa_grito_01.wav` … `vraa_grito_07.wav` (7 variações, ~1s)
- **reprovação** (erro / "deu ruim" / buzzer): `reprovacao_01.wav` … `reprovacao_05.wav` (5 variações, ~1.3–1.6s)

Ter várias variações é de propósito: a anti-repetição consecutiva do `pick_sfx`/`pick_sfx_for_text`
alterna entre elas e evita soar sempre igual (regra fixa #9 do projeto: SFX não repete consecutivo).

## PASSO 1 — copiar os arquivos
```bash
# workspace/ é junction compartilhada, então vale pras cópias que a usam
cp "D:/hipercool-materiais/_curadoria/_aprovados/sfx/vraa_grito_0"*.wav      workspace/assets/sfx/
cp "D:/hipercool-materiais/_curadoria/_aprovados/sfx/reprovacao_0"*.wav      workspace/assets/sfx/
```
> Decisão de PASTA (importante):
> - Se quiser que toquem MAIS que os outros SFX genéricos (a usuária pediu "vraa como
>   **prioridade**"), copiar TAMBÉM pra `workspace/assets/sfx_prioridade/` — a pasta dá
>   **peso 3×** no fallback do `pick_sfx()` (ver effects_engine.py ~L468). É controle manual
>   por pasta, não mexe em JSON.
> - Mas o disparo ideal desses dois sons é **por palavra-chave** (contexto da narração),
>   não sorteio genérico. Ver PASSO 2.

## PASSO 2 — disparar por PALAVRA-CHAVE (é o ponto principal desta tarefa)
O pipeline já tem `pick_sfx_for_text(text)` em `bin/effects_engine.py` (~L683) que casa o
texto da narração contra mapas de keyword. **Adicionar os dois sons novos lá.** Em que
palavras usar cada um:

### 🔊 VRAA — grito de transformação / power-up / impacto de virada
Bate com momentos de **transformação, despertar de poder, golpe forte, virada épica**.
Já existem as chaves certas no `SFX_CONTEXTUAL_MAP` (~L487) — só apontar pro vraa:
- `"transformação"` → keywords: transform, se transformou, metamorf, evoluiu, virou outr
- `"powerup"` → keywords: upou, subiu de nível, level up, ficou mais forte, despertou o poder, aura cresceu
- `"grito"` → keywords: grito, gritou, berrou, urrou, berro

**Como fazer:** criar um pool próprio do vraa e retorná-lo nessas categorias. Sugestão de
implementação (padrão do arquivo — pool de arquivos + escolha anti-repetição):
```python
# junto dos outros pools de SFX
VRAA_POOL = [f"vraa_grito_{i:02d}.wav" for i in range(1, 8)]   # em workspace/assets/sfx/
# dentro de pick_sfx_for_text, ANTES do bloco "2. Keyword contextual", adicionar:
VRAA_KEYWORDS = ["transform", "se transformou", "evoluiu", "despertou o poder",
                 "aura cresceu", "ficou mais forte", "virou outr", "subiu de nível",
                 "level up", "vraa", "vrááá"]
for kw in VRAA_KEYWORDS:
    if _kw_match(text_lower, kw):
        p = _pick_from_pool(VRAA_POOL, SFX_DIR)   # reusar lógica anti-repetição do pick_sfx
        if p: return str(p), 0.7
```
> Palavra literal "vraa"/"vrááá" na descrição também dispara (onomatopeia). Volume 0.7
> (é chamativo, mas é o destaque do momento). Ajustar se ficar alto no mix.

### 🔊 REPROVAÇÃO — erro / fracasso / "deu ruim" / buzzer
Bate com momentos de **erro, fracasso, deu errado, reprovado, game over cômico**.
Já existe `"errou"/"errado"` no `MEME_SFX_DIRECT_MAP` (~L571, hoje aponta pra `25- Errou.mp3`)
e `"derrota"` no contextual. Adicionar os novos como pool alternativo:
```python
REPROV_POOL = [f"reprovacao_{i:02d}.wav" for i in range(1, 6)]
REPROV_KEYWORDS = ["deu ruim", "deu errado", "errou", "errado", "fracassou", "fracasso",
                   "reprovado", "reprovou", "não deu certo", "nao deu certo", "falhou",
                   "vacilou", "se ferrou", "deu merda", "foi mal"]
for kw in REPROV_KEYWORDS:
    if _kw_match(text_lower, kw):
        p = _pick_from_pool(REPROV_POOL, SFX_DIR)
        if p: return str(p), 0.6
```
> Colocar esse bloco DEPOIS do foley direto e ANTES/junto do MEME direto. Volume 0.6.
> Se quiser manter o `25- Errou.mp3` antigo no sorteio, é só incluí-lo no `REPROV_POOL`.

## PASSO 3 — validar (NÃO rodar 2 renders juntos — regra do _LEIA_PRIMEIRO)
1. Self-test isolado: chamar `pick_sfx_for_text("ele se transformou e a aura cresceu")` →
   deve devolver um `vraa_grito_0X.wav`. E `pick_sfx_for_text("apostou tudo e deu ruim")` →
   um `reprovacao_0X.wav`. Rodar N vezes e conferir que ALTERNA (anti-repetição).
2. Conferir que os arquivos existem e são áudio válido (`_valid_audio`).
3. Só depois, se a máquina estiver ociosa, 1 vídeo de teste curto e validar com ffprobe
   (duração/áudio) que os sons entram no momento certo e não estouram o mix.

## PASSO 4 — encerrar
- Colar resultado do self-test na seção "RESULTADO" abaixo.
- Marcar `[FEITO AAAA-MM-DD]` no topo e no `_LEIA_PRIMEIRO.md`.
- Registrar em `logs/night-shift.md`.
- Mover os 12 wavs + os docs `LEIA_INTEGRAR_*` de `_aprovados/sfx/` da curadoria pra
  `D:\hipercool-materiais\_curadoria\_ja_implementados\sfx\` (pra outro agente não reimplementar).

## Cuidados
- **NÃO** re-separar/re-normalizar: os 12 arquivos já estão limpos e em -16 LUFS.
- **NÃO** jogar vraa/reprovação no `SFX_TRANSITION` inteiro (tocaria em TODA transição = poluição).
  O certo é disparo por keyword (contexto) + opcionalmente peso 3 via pasta prioridade.
- `_kw_match` e a lógica anti-repetição já existem no arquivo — reusar, não reinventar.
- Se `_pick_from_pool` não existir com esse nome, extrair a lógica de escolha do `pick_sfx`
  (candidatos existentes − último usado → random.choice) numa helper.

## RESULTADO
(preencher ao implementar)
