"""test_omniroute_all.py — Testa TUDO do OmniRoute:
- GPT Audio Mini (18 variacoes de voz)
- GPT Audio Premium (18 variacoes de voz)
- Lyria Pro (5 estilos de musica longa)
- Lyria Clip (5 estilos de musica curta)
"""
import json
import base64
import time
import subprocess
import http.client
import urllib.parse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "_voice_tests"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
from _segredos import omniroute_auth  # noqa: E402  (chave em secrets/omniroute_key.txt)
OMNIROUTE_KEY = omniroute_auth()

TEXTO = (
    "Ele nunca imaginou que aquele seria seu ultimo dia. "
    "O sangue escorria pelo chao enquanto a escuridao tomava conta de tudo. "
    "Mas no fundo do seu coracao, uma chama ainda ardia."
)

VOZ_VARIACOES = [
    ("01_masc_grave_epico",       "Masculina grave epica",
     "Voce e um narrador com voz GRAVE e PROFUNDA, estilo epico de anime. Leia com tom dramatico e imponente, pausas longas, como se estivesse narrando uma batalha final:"),
    ("02_masc_jovem_energetico",  "Masculina jovem energetica",
     "Voce e um narrador JOVEM e ENERGETICO, cheio de empolgacao. Leia rapido e com entusiasmo, como um youtuber animado narrando um recap de manhwa:"),
    ("03_masc_villain_sinistro",  "Masculina villain sinistro",
     "Voce e um VILAO de anime, voz sinistra e ameacadora. Leia com tom frio, calculista e levemente sarcastico, como se estivesse revelando seu plano maligno:"),
    ("04_masc_calmo_sabio",       "Masculina calma sabia",
     "Voce e um MESTRE SABIO, voz calma e serena. Leia devagar com sabedoria e serenidade, como um sensei ensinando uma licao importante:"),
    ("05_masc_misterioso",        "Masculina misteriosa",
     "Voce e um narrador MISTERIOSO. Leia em tom baixo, quase sussurrando, como se estivesse contando um segredo sombrio, estilo terror psicologico:"),
    ("06_masc_heroi",             "Masculina heroi determinado",
     "Voce e um HEROI DETERMINADO, voz firme e corajosa. Leia com conviccao e forca, como o protagonista que nao desiste nunca, estilo shounen:"),
    ("07_masc_comedia",           "Masculina comedia",
     "Voce e um narrador de COMEDIA, voz leve e divertida. Leia com humor, pausas comicas, como se estivesse narrando uma cena absurda de anime slice-of-life:"),
    ("08_masc_reporter",          "Masculina reporter",
     "Voce e um REPORTER DE TV, voz profissional e clara. Leia como se fosse uma noticia urgente de ultima hora, tom serio mas acessivel:"),
    ("09_fem_suave",              "Feminina suave doce",
     "Voce e uma narradora com voz FEMININA, SUAVE e DOCE. Leia delicadamente, com carinho e ternura, como se estivesse contando uma historia de amor:"),
    ("10_fem_energetica",         "Feminina energetica",
     "Voce e uma narradora FEMININA ENERGETICA e ANIMADA. Leia com muita empolgacao e energia, como uma youtuber animada fazendo recap:"),
    ("11_fem_madura",             "Feminina madura elegante",
     "Voce e uma narradora FEMININA com voz MADURA e ELEGANTE. Leia com sofisticacao e classe, tom grave e refinado, como uma apresentadora de documentario:"),
    ("12_fem_dramatica",          "Feminina dramatica",
     "Voce e uma narradora FEMININA DRAMATICA e INTENSA. Leia com muita emocao, como se estivesse narrando a morte de um personagem querido:"),
    ("13_fem_villain",            "Feminina villain sedutora",
     "Voce e uma VILA de anime FEMININA, voz sedutora e perigosa. Leia com tom provocativo e calculista, como uma antagonista manipuladora:"),
    ("14_fem_terror",             "Feminina terror",
     "Voce e uma narradora FEMININA de TERROR. Leia em tom assustador, voz baixa e tensa, com pausas que criam suspense:"),
    ("15_audiobook",              "Audiobook profissional",
     "Voce e um narrador profissional de AUDIOBOOK. Leia com clareza perfeita, ritmo controlado, tom neutro mas envolvente:"),
    ("16_podcast",                "Podcast conversacional",
     "Voce e um host de PODCAST. Leia de forma CONVERSACIONAL e natural, como se estivesse falando com um amigo, tom casual:"),
    ("17_trailer",                "Trailer de filme",
     "Voce e o narrador de um TRAILER DE FILME EPICO. Voz grave, dramatica, com pausas cinematograficas. Tipo 'In a world where...':"),
    ("18_esportivo",              "Narrador esportivo",
     "Voce e um NARRADOR ESPORTIVO empolgado. Leia como se fosse um gol decisivo, com crescentes de emocao e explosoes de entusiasmo:"),
]

MUSICA_ESTILOS = [
    ("01_epic_battle",    "Epica de batalha",
     "Compose an epic anime battle soundtrack with Japanese taiko drums, dramatic orchestral strings, and rising intensity. 30 seconds."),
    ("02_sad_emotional",  "Triste emocional",
     "Compose a melancholic emotional piano piece with soft strings, bittersweet and moving, like a sad anime scene. 30 seconds."),
    ("03_dark_tension",   "Dark suspense",
     "Compose dark suspenseful music with ominous low strings, eerie atmosphere, building dread, psychological thriller style. 30 seconds."),
    ("04_comedy_fun",     "Comedia leve",
     "Compose light playful music for a comedic anime scene, quirky instruments, bouncy rhythm, slice-of-life style. 30 seconds."),
    ("05_romantic",       "Romantica",
     "Compose romantic atmospheric music with gentle piano and warm strings, intimate and tender mood. 30 seconds."),
]


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def call_omniroute(prompt, model, out_path, ext="wav", timeout=120):
    try:
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["audio"],
            "stream": True,
        }).encode()

        parsed = urllib.parse.urlparse(OMNIROUTE_URL)
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=timeout)
        conn.request("POST", parsed.path, body=body, headers={
            "Content-Type": "application/json",
            "Authorization": OMNIROUTE_KEY,
        })
        resp = conn.getresponse()

        if resp.status != 200:
            err = resp.read().decode(errors="replace")
            log(f"    HTTP {resp.status}: {err[:200]}")
            conn.close()
            return False

        raw = resp.read().decode(errors="replace")
        conn.close()

        audio_chunks = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            try:
                chunk = json.loads(payload)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                audio_data = delta.get("audio", {})
                if isinstance(audio_data, dict) and audio_data.get("data"):
                    audio_chunks.append(audio_data["data"])
            except json.JSONDecodeError:
                pass

        if not audio_chunks:
            try:
                data = json.loads(raw)
                b64 = data.get("choices", [{}])[0].get("message", {}).get("audio", {}).get("data")
                if b64:
                    audio_chunks = [b64]
            except:
                pass

        if not audio_chunks:
            log(f"    Sem audio (resp: {raw[:150]})")
            return False

        full_b64 = "".join(audio_chunks)
        audio_bytes = base64.b64decode(full_b64)

        if len(audio_bytes) < 500:
            log(f"    Audio muito pequeno ({len(audio_bytes)} bytes)")
            return False

        tmp = out_path.with_suffix(".tmp")
        tmp.write_bytes(audio_bytes)

        if ext == "mp3":
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "2", "-b:a", "192k", str(out_path)],
                check=True, capture_output=True, timeout=30,
            )
        else:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "2", str(out_path)],
                check=True, capture_output=True, timeout=30,
            )
        tmp.unlink(missing_ok=True)

        if out_path.exists() and out_path.stat().st_size > 1000:
            return True
    except Exception as e:
        log(f"    Erro: {e}")
    return False


def main():
    log("=" * 60)
    log("OMNIROUTE — TESTE COMPLETO (2 APIs voz + 2 APIs musica)")
    log("=" * 60)

    # ─── GPT Audio Mini (18 variacoes) ───
    log("")
    log(">>> GPT AUDIO MINI (voz leve, paga)")
    mini_dir = OUT_DIR / "04_gpt_audio_mini"
    mini_dir.mkdir(parents=True, exist_ok=True)
    mini_ok = 0
    for nome, desc, prompt in VOZ_VARIACOES:
        log(f"  [{nome}] {desc}")
        out = mini_dir / f"{nome}.wav"
        full_prompt = prompt + "\n\n" + TEXTO
        ok = call_omniroute(full_prompt, "openrouter/openai/gpt-audio-mini", out)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"    OK ({kb} KB)")
            mini_ok += 1
        else:
            log(f"    FALHOU")
        time.sleep(2)
    log(f"  GPT Audio Mini: {mini_ok}/{len(VOZ_VARIACOES)}")

    # ─── GPT Audio Premium (18 variacoes) ───
    log("")
    log(">>> GPT AUDIO PREMIUM (voz premium, paga)")
    premium_dir = OUT_DIR / "05_gpt_audio_premium"
    premium_dir.mkdir(parents=True, exist_ok=True)
    premium_ok = 0
    for nome, desc, prompt in VOZ_VARIACOES:
        log(f"  [{nome}] {desc}")
        out = premium_dir / f"{nome}.wav"
        full_prompt = prompt + "\n\n" + TEXTO
        ok = call_omniroute(full_prompt, "openrouter/openai/gpt-audio", out)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"    OK ({kb} KB)")
            premium_ok += 1
        else:
            log(f"    FALHOU")
        time.sleep(2)
    log(f"  GPT Audio Premium: {premium_ok}/{len(VOZ_VARIACOES)}")

    # ─── Lyria Pro (musica longa) ───
    log("")
    log(">>> LYRIA PRO (musica longa, GRATIS)")
    lyria_pro_dir = OUT_DIR / "06_lyria_pro"
    lyria_pro_dir.mkdir(parents=True, exist_ok=True)
    lyria_pro_ok = 0
    for nome, desc, prompt in MUSICA_ESTILOS:
        log(f"  [{nome}] {desc}")
        out = lyria_pro_dir / f"{nome}.mp3"
        ok = call_omniroute(prompt, "openrouter/google/lyria-3-pro-preview", out, ext="mp3", timeout=180)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"    OK ({kb} KB)")
            lyria_pro_ok += 1
        else:
            log(f"    FALHOU")
        time.sleep(3)
    log(f"  Lyria Pro: {lyria_pro_ok}/{len(MUSICA_ESTILOS)}")

    # ─── Lyria Clip (musica curta) ───
    log("")
    log(">>> LYRIA CLIP (musica curta, GRATIS)")
    lyria_clip_dir = OUT_DIR / "07_lyria_clip"
    lyria_clip_dir.mkdir(parents=True, exist_ok=True)
    lyria_clip_ok = 0
    for nome, desc, prompt in MUSICA_ESTILOS:
        log(f"  [{nome}] {desc}")
        out = lyria_clip_dir / f"{nome}.mp3"
        ok = call_omniroute(prompt, "openrouter/google/lyria-3-clip-preview", out, ext="mp3", timeout=180)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"    OK ({kb} KB)")
            lyria_clip_ok += 1
        else:
            log(f"    FALHOU")
        time.sleep(3)
    log(f"  Lyria Clip: {lyria_clip_ok}/{len(MUSICA_ESTILOS)}")

    # ─── Resumo final ───
    log("")
    log("=" * 60)
    log("RESUMO FINAL")
    log("=" * 60)
    log(f"  GPT Audio Mini:    {mini_ok}/{len(VOZ_VARIACOES)} vozes")
    log(f"  GPT Audio Premium: {premium_ok}/{len(VOZ_VARIACOES)} vozes")
    log(f"  Lyria Pro:         {lyria_pro_ok}/{len(MUSICA_ESTILOS)} musicas")
    log(f"  Lyria Clip:        {lyria_clip_ok}/{len(MUSICA_ESTILOS)} musicas")
    total_ok = mini_ok + premium_ok + lyria_pro_ok + lyria_clip_ok
    total = len(VOZ_VARIACOES)*2 + len(MUSICA_ESTILOS)*2
    log(f"  TOTAL:             {total_ok}/{total}")
    log("")
    log("Pastas:")
    log(f"  {OUT_DIR / '04_gpt_audio_mini'}     — 18 vozes (mini)")
    log(f"  {OUT_DIR / '05_gpt_audio_premium'}  — 18 vozes (premium)")
    log(f"  {OUT_DIR / '06_lyria_pro'}           — 5 musicas longas")
    log(f"  {OUT_DIR / '07_lyria_clip'}          — 5 musicas curtas")


if __name__ == "__main__":
    main()
