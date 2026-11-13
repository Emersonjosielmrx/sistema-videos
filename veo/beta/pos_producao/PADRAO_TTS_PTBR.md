# Padrão de TTS PT-BR (voz natural) — pra reusar em todos os projetos

Regra de ouro: **TTS PT-BR só pronuncia certo se o texto tiver ACENTOS**.
Descoberto em 30/07/2026 nos CTAs do veo — a fonte estava sem acento
("voce", "ligacoes", "automatico") e as vozes liam errado ("voke", "codyygo").
Corrigir os acentos na FONTE resolve de raiz. Não precisa de hifenização.

---

## 1. A causa raiz (vale pra ElevenLabs, HeyGen, Gemini TTS, Edge)

Texto sem acento → pronúncia errada:

| Sem acento (ERRADO) | Com acento (CERTO) | Lê como |
|---|---|---|
| voce            | você            | "voke" vs "vo-cê" |
| ligacoes        | ligações        | "ligacôes" vs "ligações" |
| automatico      | automático      | "automatíco" vs "automático" |
| atencao         | atenção         | "atencão" vs "atenção" |
| inteligencia    | inteligência    | "inteligenssa" vs "inteligência" |
| padrao          | padrão          | "padra-o" vs "padrão" |

**Ação:** guardar SEMPRE o texto-fonte (JSON, roteiro, copy) com acentuação
correta em PT-BR. É a solução mais limpa — sem gambiarra.

---

## 2. Dois níveis de correção

### Nível 1 (preferido): acentos na fonte
Basta escrever certo. Funciona em todos os engines. É o que usamos no veo.

### Nível 2 (fallback só se o engine ainda erra): hifenização
Alguns engines (HeyGen Chill/Chase) erram MESMO com acento em palavras técnicas.
Aí aplica um dicionário de substituição grafia → sílabas hifenizadas ANTES do TTS:

```
"código"        → "có-di-go"
"implementação" → "implemen-ta-ção"
"inteligência"  → "in-te-li-gên-cia"
```

Arquivo de referência pronto (80+ entradas): `D:\roteador-heygen-api\pipeline\tts_fixes.py`
Uso: `from tts_fixes import apply_fixes; texto = apply_fixes(raw)`

**Importante:** no ElevenLabs a hifenização SOA ROBÓTICA (corta sílabas).
Só use hifenização se testar e o engine ainda errar com acento puro.

---

## 3. Cliente ElevenLabs (voz premium, reusável)

Arquivo: `D:\veo\beta\pos_producao\elevenlabs_veo.py`

- 6 chaves free rotacionadas: `D:\postador-de-videos\secrets\elevenlabs_keys.json`
  (10k chars/mês cada = 60k/mês; renovam mensalmente).
- Fallback pro Edge-TTS quando as 6 esgotam.
- `model_id`: `eleven_multilingual_v2` (fala PT-BR nativo).
- `voice_settings`: stability 0.5, similarity_boost 0.8, style 0.35, use_speaker_boost True.

Vozes premade que funcionam no free (multilingual lê PT-BR):

| chave | voice_id | perfil |
|---|---|---|
| sarah   | EXAVITQu4vr4xnSDxMaL | feminina, madura, confiante |
| bella   | hpp4J3VqNfWAUOO0d1Us | feminina, brilhante, calorosa |
| matilda | XrExE9yKIg1WjnnlVkGX | feminina, animada |
| adam    | pNInz6obpgDQGcFmaJgB | masculina, firme (vendedor) |
| eric    | cjVigY5qzO86Huf0OWal | masculina, suave, confiável |

NÃO use "library voices" (ex: Hugo) — free plan bloqueia via API (HTTP 402).

Uso:
```python
from elevenlabs_veo import speak
speak("Seu texto COM ACENTOS aqui.", out_wav="saida.wav", voz="sarah")
```

---

## 4. Regra de CACHE (economiza a cota)

Texto FIXO (CTA por produto, jingle, vinheta) → gera o áudio **uma vez** e reusa.
No veo: `cta_<produto>_<voz>.wav`. Assim gastamos ~poucas chamadas no total,
não uma por vídeo. A cota free vira irrelevante.

Só gera voz nova quando o texto muda.

---

## 5. Checklist pra portar pra outro projeto

1. Copiar `elevenlabs_veo.py` (aponta pras chaves do postador — fonte única).
2. Garantir que TODO texto-fonte tem acento PT-BR correto.
3. Se o texto é fixo (CTA, jingle) → cachear o .wav por (texto+voz).
4. Testar 1 amostra; se ainda errar palavra técnica → aplicar `tts_fixes.apply_fixes` antes.
5. Fallback pro Edge-TTS quando ElevenLabs esgotar (já embutido no cliente).
