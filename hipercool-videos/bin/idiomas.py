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
import time
from pathlib import Path

from hp_common import PROJECT_DIR, log

# "edge" = a voz do NARRADOR (não mexer: é a que já está em todos os vídeos publicados).
# "elenco" = as vozes NATIVAS extras pros personagens (16/10). Antes havia uma voz por gênero por língua:
# a Noh Yeseul em hindi era a PRÓPRIA narradora com -5%/-6Hz, e em tailandês a "Mulher" idem. Agora o
# narrador fica na voz de sempre e cada personagem pega uma voz nativa diferente (nunca a do narrador).
IDIOMAS = {
    "hi": {"nome": "hindi", "edge": {"F": "hi-IN-SwaraNeural", "M": "hi-IN-MadhurNeural"},
           # 16/10: Ananya, Kavya, Aarav e Kunal foram tiradas — NÃO EXISTEM no catálogo do edge
           # (conferido contra edge_tts.list_voices, 322 vozes). Com elas, toda fala de personagem
           # em hindi falhava 4 vezes e virava painel mudo. Sem voz nativa sobrando, o _perfil cai
           # nas Multilingual aprovadas, que falam hindi.
           "elenco": {"F": ["hi-IN-SwaraNeural"], "M": ["hi-IN-MadhurNeural"]},
           "fonte_ass": "Nirmala UI", "fonte_png": r"C:\Windows\Fonts\NirmalaB.ttf"},
    "id": {"nome": "indonésio", "edge": {"F": "id-ID-GadisNeural", "M": "id-ID-ArdiNeural"},
           "elenco": {"F": ["id-ID-GadisNeural"], "M": ["id-ID-ArdiNeural"]}},
    "it": {"nome": "italiano", "edge": {"F": "it-IT-ElsaNeural", "M": "it-IT-DiegoNeural"},
           # it-IT-IsabellaNeural ficou fora de quando era proibida; o dono a liberou em 16/10 (pode voltar)
           "elenco": {"F": ["it-IT-ElsaNeural"],
                      "M": ["it-IT-GiuseppeMultilingualNeural", "it-IT-DiegoNeural"]}},
    "fr": {"nome": "francês", "edge": {"F": "fr-FR-DeniseNeural", "M": "fr-FR-HenriNeural"},
           "elenco": {"F": ["fr-FR-EloiseNeural", "fr-FR-VivienneMultilingualNeural", "fr-FR-DeniseNeural"],
                      "M": ["fr-FR-RemyMultilingualNeural", "fr-FR-HenriNeural"]}},
    "en": {"nome": "inglês", "edge": {"F": "en-US-JennyNeural", "M": "en-US-GuyNeural"},
           "elenco": {"F": ["en-US-AvaMultilingualNeural", "en-US-EmmaMultilingualNeural", "en-US-JennyNeural"],
                      "M": ["en-US-AndrewMultilingualNeural", "en-US-BrianMultilingualNeural", "en-US-GuyNeural"]}},
    "ru": {"nome": "russo", "edge": {"F": "ru-RU-SvetlanaNeural", "M": "ru-RU-DmitryNeural"},
           # ru-RU-DariyaNeural não existe no catálogo do edge (16/10)
           "elenco": {"F": ["ru-RU-SvetlanaNeural"], "M": ["ru-RU-DmitryNeural"]},
           "fonte_ass_hook": "Montserrat ExtraBold"},
    "th": {"nome": "tailandês", "edge": {"F": "th-TH-PremwadeeNeural", "M": "th-TH-NiwatNeural"},
           # th-TH-AcharaNeural não existe no catálogo do edge (16/10)
           "elenco": {"F": ["th-TH-PremwadeeNeural"], "M": ["th-TH-NiwatNeural"]},
           "fonte_ass": "Leelawadee UI", "fonte_png": r"C:\Windows\Fonts\LeelaUIb.ttf"},
    # vietnamita: latino com muitos acentos empilhados — a Luckiest Guy não tem, a Montserrat tem
    "vi": {"nome": "vietnamita", "edge": {"F": "vi-VN-HoaiMyNeural", "M": "vi-VN-NamMinhNeural"},
           "elenco": {"F": ["vi-VN-HoaiMyNeural"], "M": ["vi-VN-NamMinhNeural"]},
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
    voz_narrador = IDIOMAS[lang]["edge"][g]
    if narrador:
        return voz_narrador, "+5%", "+0Hz"
    h = int(hashlib.md5((persona or "").encode()).hexdigest(), 16)
    # 16/10: a tabela "elenco" existia e ninguém lia — personagem e narradora saíam na MESMA voz,
    # separadas só por -5%/-6Hz (a Noh Yeseul em hindi era a própria narradora um pouco mais lenta).
    # Agora cada personagem pega uma voz nativa da língua, fixa pelo nome, e nunca a do narrador.
    # Língua sem lista (ou lista só com a voz do narrador) cai no comportamento antigo.
    pool = [v for v in (IDIOMAS[lang].get("elenco", {}).get(g) or []) if v != voz_narrador]
    if not pool:
        # Língua com uma voz só por gênero no edge (indonésio, italiano, vietnamita): usa as
        # Multilingual aprovadas pelo dono, que falam qualquer uma dessas línguas. Assim a
        # personagem para de ser a própria narradora um pouco mais lenta.
        import elenco as _el
        pool = [v for v in (_el.EDGE_F if g == "F" else _el.EDGE_M)
                if v != voz_narrador and v not in _el.PROIBIDAS]
    voz = pool[h % len(pool)] if pool else voz_narrador
    return voz, f"{(h % 4) * 5 - 5:+d}%", f"{(h // 4 % 5) * 3 - 6:+d}Hz"


def falar(texto_fala, wav_path, persona, gender, lang, indice=None, impactos=None, obra=None):
    """Gera wav (24 kHz mono) da fala no idioma; cache por voz+texto. True/False.

    22/10 (HC-03): as línguas ganham o MESMO tratamento que o pt já tinha no elenco desde 16-17/10 —
    texto_para_voz (tira rubrica "(sorriso)"/hangul), dicionário de pronúncia, curva do clímax
    (indice/impactos: a tradução preserva os índices dos impactos) e _pos_processar (corta a cauda de
    ~1,1 s do edge e nivela a -20 LUFS). Antes o wav saía CRU (shutil.copy2) e sem curva nenhuma."""
    import edge_tts
    import elenco
    bruto = (texto_fala or "").strip()
    falado = elenco.texto_para_voz(bruto, lang)
    if not falado:
        log(f"  [som] {persona} [{lang}]: fala sem nada pra ler (onomatopeia/rubrica), sem voz: {bruto[:40]}")
        return False
    voz, rate, pitch = _perfil(persona, gender, lang)
    v, ganho = elenco.prosodia(falado, {"voice": voz, "rate": rate, "pitch": pitch}, indice, impactos)
    voz, rate, pitch = v["voice"], v["rate"], v["pitch"]
    falado = elenco.aplicar_pronuncia(falado, obra, lang, voz)
    chave = hashlib.sha256(f"edge:{voz}:{rate}:{pitch}:{falado}".encode()).hexdigest()[:16]
    cache = TTS_CACHE / f"{chave}.wav"
    if not cache.exists():
        mp3 = cache.with_suffix(".mp3")
        # 4 tentativas, como o português já faz (elenco.falar_edge). O "No audio was received" do
        # edge é comum e passageiro: com UMA tentativa a fala virava painel MUDO de 0,8 s e o vídeo
        # saía "pronto" assim mesmo — no cap 1 tailandês foram 7 painéis, no cap 2 hindi, 2.
        erro = None
        for tentativa in range(1, 5):
            try:
                asyncio.run(edge_tts.Communicate(falado, voz, rate=rate, pitch=pitch).save(str(mp3)))
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ar", "24000", "-ac", "1", str(cache)],
                               check=True, timeout=60)
                erro = None
                break
            except Exception as e:  # noqa: BLE001
                erro = e
                if tentativa < 4:
                    log(f"  [!] edge {voz} falhou ({tentativa}/4): {str(e)[:90]}")
                    time.sleep(2 * tentativa)
            finally:
                mp3.unlink(missing_ok=True)
        if erro is not None:
            log(f"  [!] edge-tts {voz} falhou: {str(erro)[:100]}")
            return False
        log(f"  TTS[{lang}]: {persona} ({voz} {rate} {pitch}) — {falado[:50]}...")
    else:
        log(f"  TTS[{lang}]: {persona} ({voz}) — [CACHE] {falado[:50]}...")
    elenco._pos_processar(cache, wav_path, ganho)
    elenco._microcortes(wav_path)  # microcortes (dono 22/10), como no pt
    return True
