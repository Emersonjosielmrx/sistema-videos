# -*- coding: utf-8 -*-
"""idiomas.py — versões do hipercool em outras línguas (canais inovare hindi/ind/ita/ru/thai).

Reaproveita tudo do capítulo em português (painéis, censura, recortes, efeitos) e troca só:
  - o ROTEIRO: tradução das falas + título + tags + editorial (Claude/Gemini via proxy, 1 chamada por
    capítulo, cache em narration_cache/<chave>_<lang>.json);
  - a VOZ: edge-tts (grátis, sem cota), voz feminina/masculina do idioma com tom/velocidade por personagem;
  - os TEXTOS FIXOS da tela (selo, CTA, Shorts) e a fonte da legenda (devanágari/tailandês).
"""
import asyncio
import hashlib
import json
import subprocess
from pathlib import Path

from hp_common import PROJECT_DIR, log

IDIOMAS = {
    "hi": {"nome": "hindi", "edge": {"F": "hi-IN-SwaraNeural", "M": "hi-IN-MadhurNeural"},
           "fonte_ass": "Nirmala UI", "fonte_png": r"C:\Windows\Fonts\NirmalaB.ttf"},
    "id": {"nome": "indonésio", "edge": {"F": "id-ID-GadisNeural", "M": "id-ID-ArdiNeural"}},
    "it": {"nome": "italiano", "edge": {"F": "it-IT-ElsaNeural", "M": "it-IT-DiegoNeural"}},
    "fr": {"nome": "francês", "edge": {"F": "fr-FR-DeniseNeural", "M": "fr-FR-HenriNeural"}},
    "en": {"nome": "inglês", "edge": {"F": "en-US-JennyNeural", "M": "en-US-GuyNeural"}},
    "ru": {"nome": "russo", "edge": {"F": "ru-RU-SvetlanaNeural", "M": "ru-RU-DmitryNeural"},
           "fonte_ass_hook": "Montserrat ExtraBold"},
    "th": {"nome": "tailandês", "edge": {"F": "th-TH-PremwadeeNeural", "M": "th-TH-NiwatNeural"},
           "fonte_ass": "Leelawadee UI", "fonte_png": r"C:\Windows\Fonts\LeelaUIb.ttf"},
    # vietnamita: latino com muitos acentos empilhados — a Luckiest Guy não tem, a Montserrat tem
    "vi": {"nome": "vietnamita", "edge": {"F": "vi-VN-HoaiMyNeural", "M": "vi-VN-NamMinhNeural"},
           "fonte_ass_hook": "Montserrat ExtraBold",
           "fonte_png": r"D:\hipercool-materiais\assets\fonts\Montserrat-ExtraBold.ttf"},
}

# textos fixos que aparecem na tela / na descrição
TEXTOS = {
    "pt": {"segue": "SEGUE PRO CAP. {n}!", "mais": "SEGUE PRA MAIS!", "cap": "CAP. {n}", "parte": "PARTE {x} DE {y}",
           "continua": "CONTINUA NO PRÓXIMO VÍDEO! ➡️", "inscreva": "INSCREVA-SE 🔔", "fim": "✅ FIM DO CAPÍTULO!",
           "recap": "Recap completo", "capitulo": "Capítulo", "assine": "📌 INSCREVA-SE e ative o 🔔 para não perder nenhum capítulo!",
           "continua_parte": "🔥 CONTINUA NA PARTE {n}!"},
    "hi": {"segue": "अध्याय {n} देखें!", "mais": "और देखें!", "cap": "अध्याय {n}", "parte": "भाग {x} / {y}",
           "continua": "अगले वीडियो में जारी! ➡️", "inscreva": "सब्सक्राइब करें 🔔", "fim": "✅ अध्याय समाप्त!",
           "recap": "पूरा रीकैप", "capitulo": "अध्याय", "assine": "📌 सब्सक्राइब करें और 🔔 दबाएँ ताकि कोई अध्याय न छूटे!",
           "continua_parte": "🔥 भाग {n} में जारी!"},
    "id": {"segue": "LANJUT KE BAB {n}!", "mais": "LANJUT LAGI!", "cap": "BAB {n}", "parte": "BAGIAN {x} DARI {y}",
           "continua": "BERSAMBUNG DI VIDEO BERIKUTNYA! ➡️", "inscreva": "SUBSCRIBE 🔔", "fim": "✅ BAB SELESAI!",
           "recap": "Rekap lengkap", "capitulo": "Bab", "assine": "📌 SUBSCRIBE dan aktifkan 🔔 agar tidak ketinggalan bab berikutnya!",
           "continua_parte": "🔥 BERSAMBUNG KE BAGIAN {n}!"},
    "fr": {"segue": "SUITE AU CHAP. {n} !", "mais": "À SUIVRE !", "cap": "CHAP. {n}", "parte": "PARTIE {x} SUR {y}",
           "continua": "SUITE DANS LA PROCHAINE VIDÉO ! ➡️", "inscreva": "ABONNE-TOI 🔔", "fim": "✅ FIN DU CHAPITRE !",
           "recap": "Résumé complet", "capitulo": "Chapitre", "assine": "📌 ABONNE-TOI et active la 🔔 pour ne rater aucun chapitre !",
           "continua_parte": "🔥 SUITE DANS LA PARTIE {n} !"},
    "en": {"segue": "CONTINUES IN CH. {n}!", "mais": "TO BE CONTINUED!", "cap": "CH. {n}", "parte": "PART {x} OF {y}",
           "continua": "CONTINUES IN THE NEXT VIDEO! ➡️", "inscreva": "SUBSCRIBE 🔔", "fim": "✅ END OF CHAPTER!",
           "recap": "Full recap", "capitulo": "Chapter", "assine": "📌 SUBSCRIBE and turn on 🔔 so you never miss a chapter!",
           "continua_parte": "🔥 CONTINUES IN PART {n}!"},
    "it": {"segue": "CONTINUA NEL CAP. {n}!", "mais": "CONTINUA!", "cap": "CAP. {n}", "parte": "PARTE {x} DI {y}",
           "continua": "CONTINUA NEL PROSSIMO VIDEO! ➡️", "inscreva": "ISCRIVITI 🔔", "fim": "✅ FINE DEL CAPITOLO!",
           "recap": "Riassunto completo", "capitulo": "Capitolo", "assine": "📌 ISCRIVITI e attiva la 🔔 per non perdere nessun capitolo!",
           "continua_parte": "🔥 CONTINUA NELLA PARTE {n}!"},
    "ru": {"segue": "ДАЛЬШЕ — ГЛАВА {n}!", "mais": "ПРОДОЛЖЕНИЕ СЛЕДУЕТ!", "cap": "ГЛ. {n}", "parte": "ЧАСТЬ {x} ИЗ {y}",
           "continua": "ПРОДОЛЖЕНИЕ В СЛЕДУЮЩЕМ ВИДЕО! ➡️", "inscreva": "ПОДПИШИСЬ 🔔", "fim": "✅ КОНЕЦ ГЛАВЫ!",
           "recap": "Полный пересказ", "capitulo": "Глава", "assine": "📌 ПОДПИШИСЬ и нажми 🔔, чтобы не пропустить новые главы!",
           "continua_parte": "🔥 ПРОДОЛЖЕНИЕ В ЧАСТИ {n}!"},
    "vi": {"segue": "XEM TIẾP CHƯƠNG {n}!", "mais": "XEM TIẾP NHÉ!", "cap": "CHƯƠNG {n}", "parte": "PHẦN {x}/{y}",
           "continua": "CÒN TIẾP Ở VIDEO SAU! ➡️", "inscreva": "ĐĂNG KÝ KÊNH 🔔", "fim": "✅ HẾT CHƯƠNG!",
           "recap": "Tóm tắt đầy đủ", "capitulo": "Chương", "assine": "📌 ĐĂNG KÝ và bật 🔔 để không bỏ lỡ chương mới!",
           "continua_parte": "🔥 CÒN TIẾP Ở PHẦN {n}!"},
    "th": {"segue": "ไปต่อบทที่ {n}!", "mais": "ติดตามต่อ!", "cap": "บทที่ {n}", "parte": "ตอนที่ {x} จาก {y}",
           "continua": "ติดตามต่อในคลิปถัดไป! ➡️", "inscreva": "กดติดตาม 🔔", "fim": "✅ จบบท!",
           "recap": "สรุปเต็ม", "capitulo": "บทที่", "assine": "📌 กดติดตามและกด 🔔 เพื่อไม่พลาดบทต่อไป!",
           "continua_parte": "🔥 ติดตามต่อในตอนที่ {n}!"},
}


def texto(lang, chave, **kw):
    return TEXTOS.get(lang or "pt", TEXTOS["pt"]).get(chave, TEXTOS["pt"][chave]).format(**kw)


# ─── tradução do roteiro ─────────────────────────────────────────────────────
def traduzir_recap(recap, lang, cache_file):
    """recap (pt) -> recap no idioma. Mantém personas/gêneros/posições; 1 chamada; cache por capítulo."""
    destino = Path(cache_file).with_name(Path(cache_file).stem + f"_{lang}.json")
    if destino.exists():
        return json.loads(destino.read_text(encoding="utf-8"))
    import claude_client
    locs = recap.get("locucoes", [])
    ed = recap.get("_editorial") or {}
    pacote = {"titulo_video": recap.get("titulo_video", ""), "tags": recap.get("tags", []),
              "gancho": ed.get("gancho", ""), "pergunta": ed.get("pergunta", ""),
              "falas": [l.get("text", "") for l in locs],
              "impactos": [{"fala": i["fala"], "palavra_pt": i["palavra"]} for i in ed.get("impactos", [])]}
    prompt = (
        f"Traduza do português para o {IDIOMAS[lang]['nome']} este roteiro de vídeo de recap de manhwa no YouTube. "
        "Tom de narrador de recap: natural, envolvente, frases curtas, como um nativo falaria. Mantenha nomes "
        "próprios. Devolva SÓ JSON com as MESMAS chaves; 'falas' com EXATAMENTE o mesmo número de itens e na mesma "
        "ordem (fala vazia continua vazia); 'gancho' curto e em MAIÚSCULAS se o alfabeto tiver; em cada impacto, "
        "troque 'palavra_pt' por 'palavra' = a palavra correspondente EXATAMENTE como aparece na fala traduzida.\n\n"
        + json.dumps(pacote, ensure_ascii=False))
    def _gemini_direto():  # reserva quando o proxy do Claude Code cai (503 em todos os modelos)
        try:
            import gemini_llm
            return gemini_llm.generate_text(prompt, max_tokens=16000, temperature=0.4)
        except Exception as e:  # noqa: BLE001
            log(f"  [!] tradução: Gemini direto falhou ({str(e)[:100]})")
            return None

    out = None
    for _ in range(3):
        r = claude_client._extract_json(claude_client.perguntar(prompt, max_tokens=16000, temperature=0.4)
                                        or claude_client.gemini(prompt, max_tokens=16000, temperature=0.4)
                                        or _gemini_direto())
        if isinstance(r, dict) and len(r.get("falas", [])) == len(locs):
            out = r
            break
        log(f"  [!] tradução {lang} veio incompleta, tentando de novo")
    if not out:
        raise RuntimeError(f"tradução para {lang} falhou")
    novo = dict(recap)
    novo["locucoes"] = [dict(l, text=t) for l, t in zip(locs, out["falas"])]
    novo["titulo_video"] = out.get("titulo_video") or recap.get("titulo_video")
    novo["tags"] = out.get("tags") or recap.get("tags", [])
    import fx_acabamento
    novo["_editorial"] = dict(ed, gancho=out.get("gancho") or ed.get("gancho", ""),
                              pergunta=out.get("pergunta") or ed.get("pergunta", ""),
                              impactos=[dict(i, palavra=fx_acabamento._norm(t.get("palavra", "")))
                                        for i, t in zip(ed.get("impactos", []), out.get("impactos", []))],
                              fonte="llm")
    novo["idioma"] = lang
    destino.write_text(json.dumps(novo, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"  [OK] roteiro traduzido para {IDIOMAS[lang]['nome']} ({len(locs)} falas) -> {destino.name}")
    return novo


# ─── voz (edge-tts) ──────────────────────────────────────────────────────────
TTS_CACHE = PROJECT_DIR / "workspace" / "tts_cache"


def _perfil(persona, gender, lang):
    """Voz do idioma pelo gênero + tom/velocidade fixos por personagem (personagens soam diferentes)."""
    narrador = (persona or "").lower() in ("narrador", "narradora", "narrator", "")
    g = "F" if narrador else ("F" if str(gender or "M").upper().startswith("F") else "M")
    voz = IDIOMAS[lang]["edge"][g]
    if narrador:
        return voz, "+5%", "+0Hz"
    h = int(hashlib.md5((persona or "").encode()).hexdigest(), 16)
    return voz, f"{(h % 4) * 5 - 5:+d}%", f"{(h // 4 % 5) * 3 - 6:+d}Hz"


def falar(texto_fala, wav_path, persona, gender, lang):
    """Gera wav (24 kHz mono) da fala no idioma; cache por voz+texto. True/False."""
    import edge_tts
    voz, rate, pitch = _perfil(persona, gender, lang)
    chave = hashlib.sha256(f"edge:{voz}:{rate}:{pitch}:{texto_fala.strip()}".encode()).hexdigest()[:16]
    cache = TTS_CACHE / f"{chave}.wav"
    if not cache.exists():
        mp3 = cache.with_suffix(".mp3")
        try:
            asyncio.run(edge_tts.Communicate(texto_fala, voz, rate=rate, pitch=pitch).save(str(mp3)))
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ar", "24000", "-ac", "1", str(cache)],
                           check=True, timeout=60)
        except Exception as e:  # noqa: BLE001
            log(f"  [!] edge-tts {voz} falhou: {str(e)[:100]}")
            return False
        finally:
            mp3.unlink(missing_ok=True)
        log(f"  TTS[{lang}]: {persona} ({voz} {rate} {pitch}) — {texto_fala[:50]}...")
    else:
        log(f"  TTS[{lang}]: {persona} ({voz}) — [CACHE] {texto_fala[:50]}...")
    import shutil
    shutil.copy2(cache, wav_path)
    return True
