#!/usr/bin/env python3
"""
Ciclo autonomo de geracao + postagem de videos VO3.
- Gera videos no Flow/Veo usando fotos da dona + prompts por nicho
- Posta em todos os canais ate esgotar cota de cada um
- Move postados para pasta de postados
- Registra tudo em log
"""
import os
import sys
import json
import shutil
import subprocess
import random
import time
import urllib.request
from pathlib import Path
from datetime import datetime

# === PATHS ===
FOTOS_RETRATO = Path(r"D:\fotos para videos\fotos\Fotos minhas retrato")
FOTOS_PAISAGEM = Path(r"D:\fotos para videos\fotos\Fotos minhas paisagem")
FOTOS_NOVO = Path(r"D:\fotos para videos\fotos\fotos retrato novo para videos")
VIDEOS_GERADOS = Path(r"D:\hipercool-inferior-fix\roteador-veo-api-fake\videos\api_jobs")
VIDEOS_OPENCLAW_V2 = Path(r"D:\openclaw-videos\videos-produzidos-v2")
VIDEOS_OPENCLAW_V1 = Path(r"D:\openclaw-videos\videos-produzidos")
POSTADOS_DIR = Path(r"D:\openclaw-videos\postados")
PY_EXE = Path(r"D:\hipercool-videos\venv\Scripts\python.exe")
POSTER_SCRIPT = Path(r"D:\hipercool-producao\bin\youtube_poster.py")
GERA_AUTO = Path(r"D:\hipercool-inferior-fix\roteador-veo-api-fake\gera_auto.py")
CREDS_FILE = Path(r"D:\credenciais-canais\youtube_canais.json")
LOG_DIR = Path(r"D:\hipercool-producao\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

SKIP_CANAIS = {
    "emersonjosiel1995( motivacao",
    "emersonjosiel1995nov(motivacao",
    "enpresainovare (financeiro",
    "fabio com ia",
    "inovare recap manga",
    "nova conta de manga br",
}

PROMPTS_NICHOS = [
    "POV shot from a person waking up late for work, phone alarm screaming, jumping over a messy room. A frustrated voice says in Brazilian Portuguese: \"Nao acredito que dormi de novo.\" Fast comedic cuts, vertical 9:16.",
    "A clumsy office cat in a tiny business suit knocks a coffee mug off a desk in slow motion, then looks at the camera. Says in Brazilian Portuguese: \"Nao fui eu, juro.\" Comedic timing, vertical 9:16.",
    "Cinematic close-up of the deep ocean with bioluminescent creatures. A narrator says in Brazilian Portuguese: \"Voce sabia? O fundo do mar e menos explorado que a Lua.\" Documentary style, vertical 9:16.",
    "A breathtaking view of Earth from orbit, stars and the sun rising. A narrator says in Brazilian Portuguese: \"A Terra vista do espaco cabe no seu polegar.\" Ambient space music, vertical 9:16.",
    "An athlete running alone at sunrise on an empty road, cinematic slow motion. A narrator says in Brazilian Portuguese: \"Ninguem vai fazer por voce. Levanta.\" Inspirational, golden light, vertical 9:16.",
    "A lone wolf standing on a snowy cliff at dawn. A deep narrator says in Brazilian Portuguese: \"Enquanto voce dormia, alguem treinava pra te vencer.\" Epic orchestral music, vertical 9:16.",
    "A dark empty hallway lit by a single flickering light, camera slowly pushing toward a half-open door. A whisper says in Brazilian Portuguese: \"Tem alguem na sua casa.\" Horror short, vertical 9:16.",
    "Extreme close-up of colorful kinetic sand being sliced by a knife, crisp crunchy sound, super satisfying. No speech, only ASMR. Vertical 9:16, slow motion.",
    "A dirty old pair of sneakers being cleaned, dramatic before-and-after, foam and water, satisfying close-ups. No speech, only ASMR. Vertical 9:16, bright studio light.",
    "An optical illusion of endless stairs that loop impossibly, mind-bending Escher-style. A voice says in Brazilian Portuguese: \"Quantos degraus voce consegue contar?\" Vertical 9:16, dreamy synth.",
]

PROMPTS_COM_FOTO = [
    "A young woman confidently explaining technology on camera, warm studio lighting, gentle smile, professional vibe. She says in Brazilian Portuguese: \"Isso aqui vai mudar sua vida.\" Vertical 9:16, cinematic.",
    "A young woman reacting surprised to something on her phone screen, expressive face, cozy room background. She says in Brazilian Portuguese: \"Gente, olha isso!\" Vertical 9:16, natural lighting.",
    "A young woman walking through a futuristic city at night, neon lights reflecting, cinematic mood. She says in Brazilian Portuguese: \"O futuro ja chegou.\" Vertical 9:16, synthwave music.",
]


def log(msg):
    hoje = datetime.now().strftime("%Y-%m-%d")
    logf = LOG_DIR / f"ciclo_vo3_{hoje}.log"
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(logf, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_foto_aleatoria():
    todas = []
    for pasta in [FOTOS_RETRATO, FOTOS_PAISAGEM, FOTOS_NOVO]:
        if pasta.exists():
            todas.extend(list(pasta.glob("*.jpg")) + list(pasta.glob("*.png")))
    if not todas:
        return None
    return random.choice(todas)


def garantir_chrome():
    """Garante Chrome rodando na porta 9250 com sessao logada."""
    import urllib.request
    port = 9250
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        urllib.request.urlopen(url, timeout=3)
        return True
    except Exception:
        pass
    # Tentar abrir Chrome com perfil limpo
    profile = Path(r"D:\hipercool-inferior-fix\roteador-veo-api-fake\chrome_gen_seebotsia_clean")
    profile.mkdir(parents=True, exist_ok=True)
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome):
        log("[chrome] chrome.exe nao encontrado!")
        return False
    log(f"[chrome] abrindo Chrome na porta {port}...")
    subprocess.Popen([
        chrome,
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--disable-session-crashed-bubble",
        "--disable-gpu",
        "--disable-software-rasterizer",
        f"--user-data-dir={str(profile)}",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(15):
        time.sleep(2)
        try:
            urllib.request.urlopen(url, timeout=2)
            log("[chrome] Chrome aberto OK")
            return True
        except Exception:
            pass
    log("[chrome] FALHA ao abrir Chrome")
    return False


def gerar_video(prompt, output_path, imagem=None):
    env = dict(os.environ, PYTHONUTF8="1", FLOW_PORT="9250")
    cmd = [str(PY_EXE), "-u", str(GERA_AUTO), prompt, str(output_path)]
    if imagem:
        cmd.append(str(imagem))
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=600)
        if output_path.exists() and output_path.stat().st_size > 100000:
            return True
        log(f"  [gera] falhou: saida={r.stdout[-150:] if r.stdout else 'vazio'}")
        return False
    except subprocess.TimeoutExpired:
        log("  [gera] timeout 5min")
        return False
    except Exception as e:
        log(f"  [gera] erro: {e}")
        return False


def get_videos_disponiveis():
    videos = []
    for pasta in [VIDEOS_GERADOS, VIDEOS_OPENCLAW_V2, VIDEOS_OPENCLAW_V1]:
        if pasta.exists():
            for v in sorted(pasta.glob("*.mp4")):
                if v.stat().st_size > 50000:
                    videos.append(v)
    return videos


def carregar_canais():
    with open(CREDS_FILE, "r", encoding="utf-8") as f:
        canais = json.load(f)
    return [c for c in canais if c.get("nome", "") not in SKIP_CANAIS]


def postar_video(canal, video_path):
    nome = video_path.stem.replace("_broll", "").replace("_", " ")
    if len(nome) > 10:
        partes = nome.split(" ", 1)
        if len(partes) > 1 and len(partes[0]) > 8:
            nome = partes[1]
    titulo = f"IA Shorts - {nome.title()}"[:95]
    desc = f"{titulo}\n\n#IA #Shorts #Automacao #Tech #Viral"
    env = dict(os.environ, PYTHONUTF8="1")
    cmd = [
        str(PY_EXE), str(POSTER_SCRIPT),
        "--video", str(video_path),
        "--titulo", titulo,
        "--descricao", desc,
        "--canal", str(canal.get("id")),
        "--privacy", "private"
    ]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
        out = r.stdout + (r.stderr or "")
        if r.returncode == 0 and ("Upload Completo" in out or "https://youtu.be" in out):
            return "ok"
        if "uploadLimitExceeded" in out or "rateLimitExceeded" in out or "quotaExceeded" in out:
            return "limit"
        if "invalid_grant" in out or "authenticatedUserAccountSuspended" in out or "invalid_client" in out:
            return "dead"
        return "error"
    except subprocess.TimeoutExpired:
        return "timeout"


def postar_ate_esgotar():
    POSTADOS_DIR.mkdir(parents=True, exist_ok=True)
    canais = carregar_canais()
    videos = get_videos_disponiveis()

    if not videos:
        log("Sem videos pra postar!")
        return 0

    log(f"Postagem: {len(videos)} videos, {len(canais)} canais")
    video_idx = 0
    total_postados = 0

    for canal in canais:
        cnome = canal.get("nome", "?")
        contagem = 0

        while video_idx < len(videos):
            video_path = videos[video_idx]
            resultado = postar_video(canal, video_path)

            if resultado == "ok":
                contagem += 1
                total_postados += 1
                dest = POSTADOS_DIR / video_path.name
                if dest.exists():
                    dest = POSTADOS_DIR / f"{video_path.stem}_{contagem}{video_path.suffix}"
                try:
                    shutil.move(str(video_path), str(dest))
                except Exception:
                    pass
                video_idx += 1
            elif resultado in ("limit", "dead", "timeout"):
                break
            else:
                video_idx += 1
                if contagem == 0:
                    break

        if contagem > 0:
            log(f"  {cnome}: {contagem} postados")
        if video_idx >= len(videos):
            break

    log(f"TOTAL postados neste ciclo: {total_postados}")
    return total_postados


def gerar_lote():
    gerados = 0
    ts = datetime.now().strftime("%H%M%S")

    # Garante Chrome antes de tentar gerar
    if not garantir_chrome():
        log("Chrome nao disponivel — pulando geracao, so postagem")
        return 0

    # 2 videos com foto da dona (NUNCA da pasta 'fotos base')
    for i in range(2):
        foto = get_foto_aleatoria()
        if not foto:
            break
        prompt = random.choice(PROMPTS_COM_FOTO)
        out = VIDEOS_GERADOS / f"auto_{ts}_foto_{i}.mp4"
        log(f"Gerando com foto: {foto.name[:30]}...")
        if gerar_video(prompt, out, imagem=foto):
            gerados += 1
            log(f"  OK: {out.name}")
        else:
            # Se a primeira geracao falhou, provavelmente sessao expirou
            if i == 0 and gerados == 0:
                log("Primeira geracao falhou — sessao pode estar expirada, pulando lote")
                break

    # 3 videos sem foto (nichos variados)
    for i in range(3):
        prompt = random.choice(PROMPTS_NICHOS)
        out = VIDEOS_GERADOS / f"auto_{ts}_nicho_{i}.mp4"
        log(f"Gerando nicho #{i}...")
        if gerar_video(prompt, out):
            gerados += 1
            log(f"  OK: {out.name}")
        else:
            if i == 0 and gerados == 0:
                log("Geracao de nicho tambem falhou — abortando geracao")
                break

    log(f"Gerados neste lote: {gerados}")
    return gerados


def ciclo():
    log("=" * 50)
    log("CICLO INICIADO")
    log("=" * 50)

    # 1) Tenta gerar videos novos
    try:
        gerados = gerar_lote()
    except Exception as e:
        log(f"Erro na geracao: {e}")
        gerados = 0

    # 2) Posta tudo que tiver disponivel
    try:
        postados = postar_ate_esgotar()
    except Exception as e:
        log(f"Erro na postagem: {e}")
        postados = 0

    log(f"CICLO FINALIZADO: {gerados} gerados, {postados} postados")
    log("=" * 50)
    return gerados, postados


if __name__ == "__main__":
    ciclo()
