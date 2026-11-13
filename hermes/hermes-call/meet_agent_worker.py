#!/usr/bin/env python3
"""
Worker do Agente de Reunião (Google Meet) — Hermes Call v3.

DIVISÃO DE RESPONSABILIDADE (importante):
- O CÉREBRO (quando responder + o que responder + voz) mora no SERVIDOR Go, no
  endpoint POST /api/meet/turn. Ele aplica o gate wake-word/auto (ver meet_agent.go),
  transcreve o áudio (STT compartilhado) e devolve {should_respond, reply,
  audio_ogg_b64}. Isso é testável por API.
- Este worker é só a PLUMBING de áudio: entra na reunião (Playwright/Chrome), capta
  o áudio dos participantes em blocos, manda pro servidor (que transcreve + pensa) e
  injeta a resposta em áudio num microfone virtual.

ONDE RODAR (configurável — a dona pediu os 2):
- LOCAL (recomendado p/ não pesar no VPS): PC com Chrome + microfone virtual
  (VB-Audio Cable no Windows / módulo null-sink do PulseAudio no Linux). Menos frágil.
- VPS: precisa Xvfb + PulseAudio (null sink) dentro do container. Mais pesado/frágil.
  Use MEET_AUDIO_BACKEND=pulse e rode num serviço com esses pacotes.

MODOS:
  --dry-run   : NÃO abre navegador. Lê frases de teste (--transcript ou stdin),
                chama o servidor e imprime a decisão do gate. Valida a lógica de
                wake-word/memória sem hardware de áudio.
  --self-test : valida dependências (ffmpeg, playwright, mic virtual) e sai. Não
                entra em reunião. Use pra conferir o ambiente ANTES do modo real.
  (padrão)    : abre o Meet e opera de verdade (requer áudio configurado).

CONFIG (env ou flags):
  MEET_SERVER      base do Hermes (ex.: https://hermescall.opus-sem-limites.com.br)
  MEET_TOKEN       JWT do dono (login em /api/auth/login) ou API key
  MEET_PROFILE     id/nome do perfil de agente (traz wake-word, modo, voz, prompt)
  MEET_URL         link da reunião (modo real)
  MEET_BOT_NAME    nome que o bot usa ao entrar (default "Assistente IA")
  MEET_AUDIO_BACKEND  'vbcable' (win) | 'pulse' (linux/vps) | 'none'
  MEET_CAPTURE_DEVICE nome/índice do dispositivo de captura (fala dos participantes)
  MEET_OUTPUT_DEVICE  nome/índice do mic virtual onde injetar a resposta
  MEET_CHUNK_SEC   tamanho do bloco de captura em segundos (default 6)
  MEET_HEADLESS    "1" p/ headless (VPS) | "0" p/ ver o navegador (default 0)

DEPENDÊNCIAS:
  pip install playwright && playwright install chromium
  ffmpeg no PATH (captura/conversão de áudio)
  Windows: VB-Audio Virtual Cable  |  Linux: pulseaudio + `pactl load-module module-null-sink`
"""
import argparse
import base64
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request


# ---------------------------------------------------------------------------
# Comunicação com o servidor (o "cérebro")
# ---------------------------------------------------------------------------
def call_turn(server, token, profile, transcript="", audio_ogg_b64="",
              meeting="", voice_reply=False, timeout=90):
    """Manda uma fala (texto OU áudio) pro servidor e devolve a decisão + resposta.

    Se transcript vier vazio e audio_ogg_b64 preenchido, o SERVIDOR transcreve
    (reusa o STT já configurado). Assim o worker não precisa de chave de STT.
    """
    url = server.rstrip("/") + "/api/meet/turn"
    body = json.dumps({
        "profile": profile,
        "transcript": transcript,
        "audio_ogg_b64": audio_ogg_b64,
        "meeting": meeting,
        "voice_reply": voice_reply,
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token,
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def save_reply_audio(res, path=None):
    """Salva o OGG da resposta (se veio) e devolve o caminho, pra injetar no mic."""
    b64 = res.get("audio_ogg_b64")
    if not b64:
        return None
    data = base64.b64decode(b64)
    path = path or os.path.join(tempfile.gettempdir(), "meet_reply.ogg")
    with open(path, "wb") as f:
        f.write(data)
    return path


# ---------------------------------------------------------------------------
# Áudio — captura (participantes) e reprodução (mic virtual)
# Toda a parte específica de SO fica isolada AQUI, pra facilitar debug.
# ---------------------------------------------------------------------------
def _have(cmd):
    return shutil.which(cmd) is not None


def ffmpeg_capture_chunk(backend, device, seconds, out_ogg):
    """Grava `seconds` de áudio do dispositivo de captura num OGG (opus).

    - vbcable (Windows): dshow -> `-f dshow -i audio="<device>"`
    - pulse (Linux/VPS): pulse -> `-f pulse -i <device>`
    Retorna True se gerou arquivo com conteúdo.
    """
    if not _have("ffmpeg"):
        raise RuntimeError("ffmpeg não encontrado no PATH")
    if backend == "vbcable":
        infmt, indev = "dshow", f"audio={device}"
    elif backend == "pulse":
        infmt, indev = "pulse", device
    else:
        raise RuntimeError(f"backend de captura não suportado: {backend}")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", infmt, "-i", indev, "-t", str(seconds),
           "-ac", "1", "-ar", "16000", "-c:a", "libopus", out_ogg]
    subprocess.run(cmd, check=True, timeout=seconds + 15)
    return os.path.exists(out_ogg) and os.path.getsize(out_ogg) > 200


def audio_rms_ok(ogg_path):
    """Heurística barata: só manda pro servidor se o bloco tem som (evita STT à toa).

    Usa ffmpeg volumedetect. Retorna True se o pico não for silêncio absoluto.
    """
    if not _have("ffmpeg"):
        return True  # sem ffmpeg pra medir, deixa passar
    try:
        p = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", ogg_path, "-af", "volumedetect",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=20)
        err = p.stderr or ""
        for line in err.splitlines():
            if "mean_volume:" in line:
                # ex.: "mean_volume: -91.0 dB" (silêncio ~ -90dB)
                db = float(line.split("mean_volume:")[1].replace("dB", "").strip())
                return db > -80.0
        return True
    except Exception:
        return True


def play_to_mic(backend, device, ogg_path):
    """Toca o OGG da resposta NO microfone virtual, pra os participantes ouvirem.

    - vbcable (Windows): manda pro "CABLE Input" via dshow output.
    - pulse (Linux/VPS): paplay no sink virtual.
    """
    if backend == "pulse":
        if _have("paplay"):
            subprocess.run(["paplay", "--device=" + device, ogg_path], check=False, timeout=120)
            return True
        # fallback: ffmpeg -> pulse sink
        if _have("ffmpeg"):
            subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                            "-i", ogg_path, "-f", "pulse", device], check=False, timeout=120)
            return True
    elif backend == "vbcable":
        # No Windows a injeção no CABLE Input é feita tocando o áudio no dispositivo
        # de saída "CABLE Input". ffplay é o caminho mais simples se disponível.
        if _have("ffplay"):
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "error",
                            "-audio_device_index", device, ogg_path], check=False, timeout=120)
            return True
    print(f"[audio] AVISO: não consegui tocar no mic virtual (backend={backend}). "
          f"Confira MEET_OUTPUT_DEVICE e as ferramentas (paplay/ffplay).")
    return False


# ---------------------------------------------------------------------------
# Playwright — entrar na reunião
# ---------------------------------------------------------------------------
def join_meet(page, meet_url, bot_name):
    """Entra na sala do Meet: seta o nome, muta câmera/mic, clica em participar.

    Os seletores do Meet mudam com frequência — deixei fallbacks e um modo tolerante
    (se um passo falhar, segue). O objetivo é entrar SÓ com áudio de saída.
    """
    page.goto(meet_url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(4)
    # Preenche o nome (tela de "pré-join" pra convidados).
    for sel in ['input[aria-label="Seu nome"]', 'input[placeholder="Seu nome"]',
                'input[type="text"]']:
        try:
            el = page.query_selector(sel)
            if el:
                el.fill(bot_name)
                break
        except Exception:
            pass
    # Muta câmera e microfone reais (o bot fala pelo mic VIRTUAL, não pelo do SO).
    for label in ["Desativar microfone", "Turn off microphone",
                  "Desativar câmera", "Turn off camera"]:
        try:
            btn = page.query_selector(f'[aria-label*="{label}"]')
            if btn:
                btn.click()
                time.sleep(0.4)
        except Exception:
            pass
    # Clica em participar / pedir para entrar.
    for txt in ["Participar agora", "Pedir para participar", "Join now", "Ask to join"]:
        try:
            btn = page.get_by_text(txt, exact=False)
            if btn and btn.count() > 0:
                btn.first.click()
                print(f"[meet] cliquei em '{txt}'")
                return True
        except Exception:
            pass
    print("[meet] AVISO: não achei o botão de entrar — o Meet pode ter mudado o layout. "
          "Entre manualmente na janela aberta; o loop de áudio continua.")
    return False


# ---------------------------------------------------------------------------
# Loops
# ---------------------------------------------------------------------------
def dry_run(args):
    """Valida a lógica (gate + memória) sem navegador/áudio."""
    lines = [args.transcript] if args.transcript else \
        [l.strip() for l in sys.stdin if l.strip()]
    if not lines:
        print("Digite frases de teste (Ctrl-D encerra). Ex.: 'Francisca, que horas são?'")
        lines = [l.strip() for l in sys.stdin if l.strip()]
    for t in lines:
        res = call_turn(args.server, args.token, args.profile, transcript=t,
                        meeting=args.meeting, voice_reply=args.voice)
        mark = "🗣️ RESPONDE" if res.get("should_respond") else "🤐 ignora"
        print(f"\n[{mark}] ({res.get('reason')})  <- {t!r}")
        if res.get("should_respond"):
            print("   reply:", (res.get("reply") or "")[:300])
            ap = save_reply_audio(res)
            if ap:
                print("   áudio salvo em:", ap)
    return 0


def self_test(args):
    """Confere o ambiente: ferramentas de áudio, playwright, backend alcançável."""
    print("=== SELF-TEST do worker Meet ===")
    ok = True
    for tool in ["ffmpeg", "ffplay", "paplay"]:
        have = _have(tool)
        print(f"  {'✓' if have else '·'} {tool}: {'ok' if have else 'ausente'}")
    try:
        import playwright  # noqa
        print("  ✓ playwright: instalado")
    except Exception:
        print("  ✗ playwright: FALTA (pip install playwright && playwright install chromium)")
        ok = False
    # Testa o cérebro com uma frase.
    try:
        res = call_turn(args.server, args.token, args.profile,
                        transcript="teste de conexão", meeting="selftest", timeout=30)
        print(f"  ✓ servidor respondeu: should_respond={res.get('should_respond')} reason={res.get('reason')}")
    except Exception as e:
        print(f"  ✗ servidor inacessível: {e}")
        ok = False
    print("=== " + ("TUDO OK" if ok else "FALTAM DEPENDÊNCIAS") + " ===")
    return 0 if ok else 2


def run_real(args):
    """Modo real: abre o Meet, capta áudio em blocos, pensa no servidor, injeta a voz."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print("Playwright indisponível:", e)
        return 2

    backend = os.getenv("MEET_AUDIO_BACKEND", "none")
    cap_dev = os.getenv("MEET_CAPTURE_DEVICE", "")
    out_dev = os.getenv("MEET_OUTPUT_DEVICE", "")
    chunk = int(os.getenv("MEET_CHUNK_SEC", str(args.chunk)))
    headless = os.getenv("MEET_HEADLESS", "0") == "1"

    if backend == "none" or not cap_dev:
        print("[meet] AVISO: MEET_AUDIO_BACKEND/MEET_CAPTURE_DEVICE não configurados. "
              "Vou entrar na reunião, mas SEM captura de áudio. Rode --self-test "
              "e configure o mic virtual pra operar de verdade.")

    # Fila desacopla captura (produtor) do processamento (consumidor), pra a captura
    # não parar enquanto o servidor pensa/fala.
    q = queue.Queue(maxsize=4)
    stop = threading.Event()

    def capture_loop():
        i = 0
        while not stop.is_set():
            out = os.path.join(tempfile.gettempdir(), f"meet_cap_{i%3}.ogg")
            try:
                if ffmpeg_capture_chunk(backend, cap_dev, chunk, out) and audio_rms_ok(out):
                    with open(out, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    try:
                        q.put(b64, timeout=1)
                    except queue.Full:
                        pass  # servidor lento; descarta bloco pra não acumular atraso
            except Exception as e:
                print("[capture] erro:", e)
                time.sleep(1)
            i += 1

    def process_loop():
        while not stop.is_set():
            try:
                b64 = q.get(timeout=1)
            except queue.Empty:
                continue
            try:
                res = call_turn(args.server, args.token, args.profile,
                                audio_ogg_b64=b64, meeting=args.meeting, voice_reply=True)
            except Exception as e:
                print("[process] servidor:", e)
                continue
            if not res.get("should_respond"):
                continue
            txt = (res.get("transcript") or "").strip()
            reply = (res.get("reply") or "").strip()
            print(f"[meet] 👤 {txt!r}\n[meet] 🤖 {reply[:200]}")
            ap = save_reply_audio(res)
            if ap and backend != "none" and out_dev:
                play_to_mic(backend, out_dev, ap)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless, args=[
            "--use-fake-ui-for-media-stream",  # auto-permite mic/cam sem popup
            "--disable-blink-features=AutomationControlled",
        ])
        ctx = browser.new_context(permissions=["microphone", "camera"])
        page = ctx.new_page()
        bot_name = os.getenv("MEET_BOT_NAME", "Assistente IA")
        join_meet(page, args.meet_url, bot_name)

        cap_t = threading.Thread(target=capture_loop, daemon=True)
        proc_t = threading.Thread(target=process_loop, daemon=True)
        if backend != "none" and cap_dev:
            cap_t.start()
        proc_t.start()
        print("[meet] operando. Ctrl-C pra sair.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[meet] encerrando...")
        finally:
            stop.set()
            time.sleep(1)
            browser.close()
    return 0


def main():
    ap = argparse.ArgumentParser(description="Worker do Agente de Reunião (Meet)")
    ap.add_argument("--server", default=os.getenv("MEET_SERVER", "https://hermescall.opus-sem-limites.com.br"))
    ap.add_argument("--token", default=os.getenv("MEET_TOKEN", ""))
    ap.add_argument("--profile", default=os.getenv("MEET_PROFILE", ""))
    ap.add_argument("--meet-url", default=os.getenv("MEET_URL", ""))
    ap.add_argument("--meeting", default=os.getenv("MEET_ID", "teste"))
    ap.add_argument("--transcript", default="", help="frase única pra testar (dry-run)")
    ap.add_argument("--chunk", type=int, default=6, help="segundos por bloco de captura")
    ap.add_argument("--voice", action="store_true", help="pedir áudio TTS de volta")
    ap.add_argument("--dry-run", action="store_true", help="testa gate/memória sem navegador")
    ap.add_argument("--self-test", action="store_true", help="checa dependências e conexão, sem entrar")
    args = ap.parse_args()

    if not args.token:
        print("Erro: informe --token (JWT do dono) ou MEET_TOKEN.")
        return 1
    if args.self_test:
        return self_test(args)
    if args.dry_run or not args.meet_url:
        return dry_run(args)
    return run_real(args)


if __name__ == "__main__":
    sys.exit(main())
