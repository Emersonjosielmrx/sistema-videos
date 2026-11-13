"""test_vozes_fala_pura.py — Gera vozes de FALA PURA (narração tipo anime) SEM música.

DIFERENTE das pastas 04/05 que têm trilha misturada na fala.
Aqui é SÓ voz, sem música, sem SFX, sem fundo — como narração de audiobook/anime.
"""
import json
import base64
import time
import subprocess
import http.client
import urllib.parse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "_voice_tests" / "11_vozes_fala_pura"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
from _segredos import omniroute_auth  # noqa: E402  (chave em secrets/omniroute_key.txt)
OMNIROUTE_KEY = omniroute_auth()

TEXTO_NARR = (
    "Ele nunca imaginou que aquele seria seu ultimo dia. "
    "O sangue escorria pelo chao enquanto a escuridao tomava conta de tudo. "
    "Mas no fundo do seu coracao, uma chama ainda ardia. "
    "E foi naquele momento que ele decidiu: nao importa o que aconteca, "
    "eu vou lutar ate o fim."
)

INSTRUCAO_PURA = (
    "IMPORTANT: Generate ONLY speech. No music. No sound effects. "
    "No background audio. No soundtrack. No instruments. "
    "Pure voice only, like a professional audiobook narration. "
    "Clear, clean voice with no background of any kind."
)

# 8 via GPT Audio Mini (grátis combo) + 6 via GPT Audio Premium (pago)
VOZES = [
    # --- GPT Audio Mini (combo grátis) ---
    ("01_mini_masc_epico", "openrouter/openai/gpt-audio-mini",
     f"{INSTRUCAO_PURA}\n\nYou are a MALE narrator with an epic, dramatic voice. "
     f"Read this text in Brazilian Portuguese with intensity and gravitas, "
     f"like a professional anime narrator. Pure speech only:\n\n{TEXTO_NARR}"),

    ("02_mini_masc_calmo", "openrouter/openai/gpt-audio-mini",
     f"{INSTRUCAO_PURA}\n\nYou are a calm, deep-voiced MALE narrator. "
     f"Read this text in Brazilian Portuguese with a soothing, steady tone, "
     f"like a wise storyteller. Pure speech only:\n\n{TEXTO_NARR}"),

    ("03_mini_fem_narradora", "openrouter/openai/gpt-audio-mini",
     f"{INSTRUCAO_PURA}\n\nYou are a FEMALE narrator with a clear, professional voice. "
     f"Read this text in Brazilian Portuguese like an anime narrator, "
     f"expressive but natural. Pure speech only:\n\n{TEXTO_NARR}"),

    ("04_mini_fem_terror", "openrouter/openai/gpt-audio-mini",
     f"{INSTRUCAO_PURA}\n\nYou are a FEMALE narrator of horror stories. "
     f"Read this text in Brazilian Portuguese with a low, tense voice, "
     f"creating suspense with pauses. Pure speech only:\n\n{TEXTO_NARR}"),

    ("05_mini_masc_jovem", "openrouter/openai/gpt-audio-mini",
     f"{INSTRUCAO_PURA}\n\nYou are a young MALE narrator with an energetic voice. "
     f"Read this text in Brazilian Portuguese with excitement and youthful energy, "
     f"like a shounen anime narrator. Pure speech only:\n\n{TEXTO_NARR}"),

    ("06_mini_masc_grave", "openrouter/openai/gpt-audio-mini",
     f"{INSTRUCAO_PURA}\n\nYou are a MALE narrator with an extremely deep, bass voice. "
     f"Read this text in Brazilian Portuguese with a rumbling, authoritative tone, "
     f"like a movie trailer narrator. Pure speech only:\n\n{TEXTO_NARR}"),

    ("07_mini_fem_doce", "openrouter/openai/gpt-audio-mini",
     f"{INSTRUCAO_PURA}\n\nYou are a FEMALE narrator with a sweet, gentle voice. "
     f"Read this text in Brazilian Portuguese softly and warmly, "
     f"like telling a bedtime story. Pure speech only:\n\n{TEXTO_NARR}"),

    ("08_mini_neutro_audiobook", "openrouter/openai/gpt-audio-mini",
     f"{INSTRUCAO_PURA}\n\nYou are a professional audiobook narrator, gender neutral. "
     f"Read this text in Brazilian Portuguese with perfect clarity, "
     f"controlled rhythm, engaging but neutral. Pure speech only:\n\n{TEXTO_NARR}"),

    # --- GPT Audio Premium (pago, qualidade superior) ---
    ("09_premium_masc_epico", "openrouter/openai/gpt-audio",
     f"{INSTRUCAO_PURA}\n\nYou are a MALE narrator with a powerful, epic voice. "
     f"Read this text in Brazilian Portuguese with dramatic intensity, "
     f"like narrating an anime battle scene. Pure speech only:\n\n{TEXTO_NARR}"),

    ("10_premium_fem_misterio", "openrouter/openai/gpt-audio",
     f"{INSTRUCAO_PURA}\n\nYou are a FEMALE narrator of mystery stories. "
     f"Read this text in Brazilian Portuguese with an intriguing, mysterious tone, "
     f"building curiosity. Pure speech only:\n\n{TEXTO_NARR}"),

    ("11_premium_masc_vilao", "openrouter/openai/gpt-audio",
     f"{INSTRUCAO_PURA}\n\nYou are a MALE villain narrator with a menacing voice. "
     f"Read this text in Brazilian Portuguese with a dark, threatening tone, "
     f"like an anime antagonist monologuing. Pure speech only:\n\n{TEXTO_NARR}"),

    ("12_premium_fem_heroina", "openrouter/openai/gpt-audio",
     f"{INSTRUCAO_PURA}\n\nYou are a FEMALE heroine narrator with a brave, determined voice. "
     f"Read this text in Brazilian Portuguese with strength and conviction, "
     f"like a warrior telling her story. Pure speech only:\n\n{TEXTO_NARR}"),

    ("13_premium_masc_sensei", "openrouter/openai/gpt-audio",
     f"{INSTRUCAO_PURA}\n\nYou are a wise old MALE sensei narrator. "
     f"Read this text in Brazilian Portuguese with wisdom and gravitas, "
     f"slow and deliberate, like a master teaching his student. Pure speech only:\n\n{TEXTO_NARR}"),

    ("14_premium_masc_esportivo", "openrouter/openai/gpt-audio",
     f"{INSTRUCAO_PURA}\n\nYou are a sports commentator narrator, MALE voice. "
     f"Read this text in Brazilian Portuguese with growing excitement, "
     f"building energy like narrating a decisive goal. Pure speech only:\n\n{TEXTO_NARR}"),
]


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def call_omniroute(prompt, model, out_path, timeout=120):
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
            except Exception:
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
    log("VOZES DE FALA PURA — SEM MUSICA, SEM SFX")
    log("=" * 60)
    log(f"14 vozes (8 Mini + 6 Premium), destino: {OUT_DIR}")
    log("")

    ok_count = 0
    fail_503 = 0

    for nome, model, prompt in VOZES:
        tag = "MINI" if "mini" in model else "PREMIUM"
        out = OUT_DIR / f"{nome}.wav"

        if out.exists() and out.stat().st_size > 1000:
            log(f"  [{nome}] ({tag}) ja existe, pulando")
            ok_count += 1
            continue

        log(f"  [{nome}] ({tag}) gerando...")
        ok = call_omniroute(prompt, model, out)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"    OK ({kb} KB)")
            ok_count += 1
        else:
            log(f"    FALHOU")
            fail_503 += 1
            if fail_503 >= 3:
                log("  3+ falhas consecutivas, proxy provavelmente fora. Parando.")
                break
        time.sleep(2)

    log("")
    log("=" * 60)
    log(f"=== {ok_count}/{len(VOZES)} geradas ===")
    log(f"Pasta: {OUT_DIR}")
    if fail_503 > 0:
        log(f"({fail_503} falharam — proxy pode estar fora, tente de novo depois)")


if __name__ == "__main__":
    main()
