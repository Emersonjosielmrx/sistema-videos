"""test_omniroute_voices.py — Testa TODAS as variacoes possiveis de voz via OmniRoute GPT Audio.

Muda o prompt pra conseguir vozes diferentes:
- Masculinas: grave, jovem, agressivo, calmo, misterioso, narrador epico
- Femininas: suave, energetica, madura, sussurro, dramatica
- Estilos: anime villain, heroi, comedia, terror, romance
"""
import json
import base64
import time
import subprocess
import http.client
import urllib.parse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "_voice_tests" / "04_omniroute_variacoes"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
from _segredos import omniroute_auth  # noqa: E402  (chave em secrets/omniroute_key.txt)
OMNIROUTE_KEY = omniroute_auth()

MODEL = "openrouter/openai/gpt-audio-mini"

TEXTO = (
    "Ele nunca imaginou que aquele seria seu ultimo dia. "
    "O sangue escorria pelo chao enquanto a escuridao tomava conta de tudo. "
    "Mas no fundo do seu coracao, uma chama ainda ardia."
)

VARIACOES = [
    # MASCULINAS
    {
        "nome": "01_masc_grave_epico",
        "desc": "Masculina grave epica",
        "prompt": "Voce e um narrador com voz GRAVE e PROFUNDA, estilo epico de anime. Leia com tom dramatico e imponente, pausas longas, como se estivesse narrando uma batalha final:",
    },
    {
        "nome": "02_masc_jovem_energetico",
        "desc": "Masculina jovem energetica",
        "prompt": "Voce e um narrador JOVEM e ENERGETICO, cheio de empolgacao. Leia rapido e com entusiasmo, como um youtuber animado narrando um recap de manhwa:",
    },
    {
        "nome": "03_masc_villain_sinistro",
        "desc": "Masculina villain sinistro",
        "prompt": "Voce e um VILAO de anime, voz sinistra e ameacadora. Leia com tom frio, calculista e levemente sarcastico, como se estivesse revelando seu plano maligno:",
    },
    {
        "nome": "04_masc_calmo_sabio",
        "desc": "Masculina calma sabia",
        "prompt": "Voce e um MESTRE SABIO, voz calma e serena. Leia devagar com sabedoria e serenidade, como um sensei ensinando uma licao importante:",
    },
    {
        "nome": "05_masc_misterioso_sussurro",
        "desc": "Masculina misteriosa sussurro",
        "prompt": "Voce e um narrador MISTERIOSO. Leia em tom baixo, quase sussurrando, como se estivesse contando um segredo sombrio, estilo terror psicologico:",
    },
    {
        "nome": "06_masc_heroi_determinado",
        "desc": "Masculina heroi determinado",
        "prompt": "Voce e um HEROI DETERMINADO, voz firme e corajosa. Leia com conviccao e forca, como o protagonista que nao desiste nunca, estilo shounen:",
    },
    {
        "nome": "07_masc_comedia_divertido",
        "desc": "Masculina comedia divertido",
        "prompt": "Voce e um narrador de COMEDIA, voz leve e divertida. Leia com humor, algumas pausas comicas, como se estivesse narrando uma cena absurda de anime slice-of-life:",
    },
    {
        "nome": "08_masc_reporter_noticiarista",
        "desc": "Masculina reporter/jornal",
        "prompt": "Voce e um REPORTER DE TV, voz profissional e clara. Leia como se fosse uma noticia urgente de ultima hora, tom serio mas acessivel:",
    },
    # FEMININAS
    {
        "nome": "09_fem_suave_doce",
        "desc": "Feminina suave doce",
        "prompt": "Voce e uma narradora com voz FEMININA, SUAVE e DOCE. Leia delicadamente, com carinho e ternura, como se estivesse contando uma historia de amor:",
    },
    {
        "nome": "10_fem_energetica_animada",
        "desc": "Feminina energetica",
        "prompt": "Voce e uma narradora FEMININA ENERGETICA e ANIMADA. Leia com muita empolgacao e energia, como uma youtuber animada fazendo recap de manhwa:",
    },
    {
        "nome": "11_fem_madura_elegante",
        "desc": "Feminina madura elegante",
        "prompt": "Voce e uma narradora FEMININA com voz MADURA e ELEGANTE. Leia com sofisticacao e classe, tom grave e refinado, como uma apresentadora de documentario:",
    },
    {
        "nome": "12_fem_dramatica_intensa",
        "desc": "Feminina dramatica intensa",
        "prompt": "Voce e uma narradora FEMININA DRAMATICA e INTENSA. Leia com muita emocao, quase ao ponto de lagrimas, como se estivesse narrando a morte de um personagem querido:",
    },
    {
        "nome": "13_fem_villain_sedutora",
        "desc": "Feminina villain sedutora",
        "prompt": "Voce e uma VILA de anime FEMININA, voz sedutora e perigosa. Leia com tom provocativo e calculista, como uma antagonista manipuladora:",
    },
    {
        "nome": "14_fem_terror_assustadora",
        "desc": "Feminina terror",
        "prompt": "Voce e uma narradora FEMININA de TERROR. Leia em tom assustador, voz baixa e tensa, com pausas que criam suspense, como narracao de creepypasta:",
    },
    # ESTILOS ESPECIAIS
    {
        "nome": "15_narrador_audiobook",
        "desc": "Estilo audiobook profissional",
        "prompt": "Voce e um narrador profissional de AUDIOBOOK. Leia com clareza perfeita, ritmo controlado, tom neutro mas envolvente, como um audiobook best-seller:",
    },
    {
        "nome": "16_narrador_podcast",
        "desc": "Estilo podcast conversacional",
        "prompt": "Voce e um host de PODCAST. Leia de forma CONVERSACIONAL e natural, como se estivesse falando com um amigo, tom casual e proximo:",
    },
    {
        "nome": "17_narrador_trailer",
        "desc": "Estilo trailer de filme",
        "prompt": "Voce e o narrador de um TRAILER DE FILME EPICO. Voz grave, dramatica, com pausas cinematograficas. Cada frase e uma revelacao. Tom tipo 'In a world where...':",
    },
    {
        "nome": "18_narrador_esportivo",
        "desc": "Estilo narrador esportivo",
        "prompt": "Voce e um NARRADOR ESPORTIVO empolgado. Leia como se fosse um gol decisivo, com crescentes de emocao e explosoes de entusiasmo:",
    },
]


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def gen_omniroute(prompt_prefix, out_path):
    try:
        full_prompt = prompt_prefix + "\n\n" + TEXTO
        body = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": full_prompt}],
            "modalities": ["audio"],
            "stream": True,
        }).encode()

        parsed = urllib.parse.urlparse(OMNIROUTE_URL)
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=120)
        conn.request("POST", parsed.path, body=body, headers={
            "Content-Type": "application/json",
            "Authorization": OMNIROUTE_KEY,
        })
        resp = conn.getresponse()

        if resp.status != 200:
            err = resp.read().decode(errors="replace")
            log(f"    HTTP {resp.status}: {err[:150]}")
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
            log("    Sem audio na resposta")
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
    log("=== OMNIROUTE GPT AUDIO — 18 VARIACOES DE VOZ ===")
    log(f"Texto: {TEXTO[:60]}...")
    log(f"Saida: {OUT_DIR}")
    log("")

    ok_count = 0
    for v in VARIACOES:
        log(f"[{v['nome']}] {v['desc']}...")
        out = OUT_DIR / f"{v['nome']}.wav"
        ok = gen_omniroute(v["prompt"], out)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"  OK ({kb} KB)")
            ok_count += 1
        else:
            log(f"  FALHOU")
        time.sleep(2)

    log("")
    log(f"=== {ok_count}/{len(VARIACOES)} geradas com sucesso ===")
    log(f"Pasta: {OUT_DIR}")
    log("Escuta cada uma e compara os estilos!")


if __name__ == "__main__":
    main()
