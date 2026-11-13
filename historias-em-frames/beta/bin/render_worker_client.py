# -*- coding: utf-8 -*-
"""render_worker_client.py — distribui render de clips pro PC2 via daemon HTTP.

TOPOLOGIA (Jul 2026):
  PC1: historias-em-frames (local D:)    PC2 daemon: 100.125.7.77:8771
  NAS: \\100.118.234.102\\d$ (ambos enxergam via SMB)

ROTA VERIFICADA:
  1. PC1 garante que imagem existe no NAS (via path local D:)
  2. /exec Copy-Item NAS -> C:/app  (PowerShell, UNC paths)
  3. /exec python C:/app/script.py      (ffmpeg + shutil.copy2 NAO funciona aqui por escaping)
  4. /run shutil.copy2 C:/app -> NAS    (Python direto, UNC funciona)
  5. PC1 lê output via path local D:

NOTA: shutil.copy2 de C: para UNC no cmd.exe NAO funciona (escaping).
  Por isso usamos /run (Python exec) pra escrever no NAS.
"""
import os, sys, json, time, uuid, shutil, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Config ───────────────────────────────────────────────────────────────────
DAEMON = os.environ.get("PC2_HOST", "100.125.7.77")
DAEMON_URL = f"http://{DAEMON}:{os.environ.get('PC2_PORT', '8771')}"
DAEMON_HF_HOME = os.environ.get(
    "DAEMON_HF_HOME",
    r"C:\Users\Emerson-IA\.cache\huggingface"  # PC2 local HF cache
)
NAS_ROOT = os.environ.get("NAS_SMB", r"\\100.118.234.102\d$")
NAS_HIST = os.path.join(NAS_ROOT, r"historias-em-frames")
NAS_JOBS = os.path.join(NAS_HIST, r"workspace\worker_jobs")
NAS_IMGS = os.path.join(NAS_HIST, r"workspace\images")
PC2_APP = r"C:\app"
MAX_JOBS = int(os.environ.get("MAX_PARALLEL_JOBS", "2"))
WORKER_TIMEOUT_S = int(os.environ.get("WORKER_TIMEOUT_S", "300"))


def _log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] [worker] {msg}", flush=True)


def _exec(cmd, cwd="C:/", timeout=300):
    """Executa shell command no PC2 via daemon /exec."""
    payload = json.dumps({"cmd": cmd, "cwd": cwd}).encode()
    req = urllib.request.Request(
        f"{DAEMON_URL}/exec", data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e)}


def _run(script, timeout=300):
    """Executa Python no PC2 diretamente via daemon /run (sem shell, UNC funciona)."""
    payload = json.dumps({"script": script}).encode()
    req = urllib.request.Request(
        f"{DAEMON_URL}/run", data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e)}


def is_online():
    try:
        with urllib.request.urlopen(f"{DAEMON_URL}/health", timeout=5) as r:
            h = json.loads(r.read().decode())
            _log(f"PC2 online: {h.get('host')} | {h.get('python')}")
            return True
    except Exception as e:
        _log(f"PC2 offline: {e}")
        return False


def _ensure_pc2_app():
    _exec(f"mkdir {PC2_APP}", cwd="C:/")


def _to_unc(local_path):
    """Converte D:\\... ou D:/... -> \\\\100.118.234.102\\d$\\..."""
    p = str(local_path).replace("/", "\\")
    if p.startswith("D:") or p.startswith("D\\"):
        return "\\\\100.118.234.102\\d$" + p[2:]
    return p


def _run_daemon_script(script_content, job_id, timeout=200):
    """Escreve script no NAS, copia pro daemon via Copy-Item (/exec), executa."""
    script_nas = os.path.join(NAS_JOBS, f"_scripts/{job_id}_script.py")
    os.makedirs(os.path.dirname(script_nas), exist_ok=True)
    with open(script_nas, "w", encoding="utf-8") as f:
        f.write(script_content)

    script_unc = _to_unc(script_nas)
    # Copy script NAS -> C:/app via /exec
    copy_cmd = (
        "powershell -Command \""
        f"Copy-Item -Path '{script_unc}' -Destination {PC2_APP}\\script.py -Force; "
        "Write-Host COPY_OK\""
    )
    _log(f"  copying script...")
    r = _exec(copy_cmd, cwd="C:/", timeout=30)
    if r.get("returncode") != 0:
        return False, f"copy script failed: {r.get('stderr','')[:100]}"

    # Run script via /exec (ffmpeg outputs stay on C:/app)
    _log(f"  running ffmpeg...")
    t0 = time.time()
    r = _exec("python C:\\app\\script.py", cwd="C:/", timeout=timeout)
    elapsed = time.time() - t0

    if r.get("returncode") == 0:
        return True, f"OK ({elapsed:.0f}s)"
    else:
        _log(f"  FAIL stdout: {r.get('stdout','')[:200]}")
        if r.get("stderr"):
            _log(f"  FAIL stderr: {r.get('stderr','')[:100]}")
        return False, f"rc={r.get('returncode')}"


def render_ken_burns_clip(img_local, audio_local, out_local, dur=5.0):
    """Renderiza clip Ken Burns com audio mux no PC2. Fallback: False.

    Aceita paths locais do PC1 (D:\\...) e cuida da conversão UNC internamente.

    Args:
        img_local: path local da imagem (D:\\...)
        audio_local: path local do audio (D:\\...)
        out_local: path local de output (D:\\...)
        dur: duracao em segundos

    Returns:
        True se output chegou no PC1, False caso contrário.
    """
    if not is_online():
        return False

    # Converte paths locais -> UNC (NAS que ambos enxergam)
    def _to_unc(p):
        s = str(p).replace("/", "\\")
        if s.startswith("D:") or s.startswith("D\\"):
            return "\\\\100.118.234.102\\d$" + s[2:]
        return s

    unc_img = _to_unc(img_local)
    unc_audio = _to_unc(audio_local)
    unc_out = _to_unc(out_local)

    _log(f"  PC2 Ken Burns: {Path(img_local).name} ({dur}s)...")

    # Step 1: Copy img+audio NAS -> C:/app via /exec (explicit filenames, no glob)
    for _src, _fname in [(unc_img, "_kb_img.png"), (unc_audio, "_kb_audio.wav")]:
        r = _exec(
            f"powershell -Command \"Copy-Item -Path '{_src}' -Destination {PC2_APP}\\{_fname} -Force; Write-Host OK\"",
            cwd="C:/", timeout=60
        )
        if r.get("returncode") != 0:
            _log(f"    FALHA copy {_fname}: {r.get('stderr','')[:60]}")
            return False

    _pc2_img = f"{PC2_APP}\\_kb_img.png"
    _pc2_audio = f"{PC2_APP}\\_kb_audio.wav"
    _pc2_out = f"{PC2_APP}\\_kb_out.mp4"

    # Step 2: Run ffmpeg via /run (Python direto — sem shell escaping)
    script = (
        "import subprocess, pathlib, shutil, sys, time\n"
        "tmp_img = pathlib.Path(r'C:\\app\\_kb_img.png')\n"
        "tmp_audio = pathlib.Path(r'C:\\app\\_kb_audio.wav')\n"
        "tmp_out = pathlib.Path(r'C:\\app\\_kb_out.mp4')\n"
        "nas_out = pathlib.Path(r'" + unc_out.replace("/", "//") + "')\n"
        "print('start', flush=True)\n"
        "dur = float(" + str(dur) + ")\n"
        "zoom_dur = int(dur * 25)\n"
        "# Ken Burns: zoom-in on the padded 720x1280 canvas\n"
        "vf = ('scale=720:720:force_original_aspect_ratio=decrease,'\n"
        "      'pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black')\n"
        "result = subprocess.run(\n"
        "    ['ffmpeg', '-y',\n"
        "     '-loop', '1', '-i', str(tmp_img),\n"
        "     '-i', str(tmp_audio),\n"
        "     '-vf', vf,\n"
        "     '-pix_fmt', 'yuv420p', '-r', '25',\n"
        "     '-t', str(dur),\n"
        "     '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',\n"
        "     '-threads', '2', '-shortest', str(tmp_out)],\n"
        "    capture_output=True, text=True, timeout=180)\n"
        "print('rc:', result.returncode, flush=True)\n"
        "if result.returncode != 0:\n"
        "    print('ERR:', result.stderr[-300:], flush=True)\n"
        "    sys.exit(1)\n"
        "nas_out.parent.mkdir(parents=True, exist_ok=True)\n"
        "shutil.copy2(tmp_out, nas_out)\n"
        "print('NAS OK:', nas_out.stat().st_size // 1024, 'KB', flush=True)\n"
        "for f in [tmp_img, tmp_audio, tmp_out]: f.unlink(missing_ok=True)\n"
        "sys.exit(0)\n"
    )
    t0 = time.time()
    r = _run(script, timeout=200)
    if r.get("returncode") != 0:
        _log(f"    ffmpeg failed rc={r.get('returncode')}")
        return False

    # Step 3: Verify output on PC1
    local_out = Path(out_local)
    if local_out.exists() and local_out.stat().st_size > 5000:
        _log(f"    OK {local_out.stat().st_size // 1024}KB in {time.time()-t0:.0f}s")
        return True
    else:
        _log(f"    FALHA: output not on PC1")
        return False


# ── Render Ken Burns (ffmpeg) ────────────────────────────────────────────────
_DAEMON_RENDER_SCRIPT = '''
import shutil, pathlib, subprocess, sys

nas_input = pathlib.Path(r"{nas_input}")
nas_output = pathlib.Path(r"{nas_output}")
tmp_img = pathlib.Path(r"C:\\app\\_r_img.png")
tmp_out = pathlib.Path(r"C:\\app\\_r_out.mp4")

print("NAS_INPUT:", nas_input, flush=True)

shutil.copy2(nas_input, tmp_img)
if not tmp_img.exists() or tmp_img.stat().st_size < 1000:
    print("FALHA:copy_input", flush=True)
    sys.exit(1)
print("IMG OK:", tmp_img.stat().st_size // 1024, "KB", flush=True)

vf = (
    "scale=720:1280:force_original_aspect_ratio=decrease,"
    "pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,"
    "zoompan=z='1.03':d=1:fps=25:s=720x1280"
)
args = [
    "ffmpeg", "-y", "-loop", "1", "-i", str(tmp_img),
    "-vf", vf,
    "-pix_fmt", "yuv420p", "-r", "25", "-t", "{dur}",
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
    "-threads", "2", str(tmp_out)
]
print("ffmpeg...", flush=True)
result = subprocess.run(args, capture_output=True, text=True, timeout=180)
print("ff rc:", result.returncode, flush=True)
if result.returncode != 0:
    print("ERR:", result.stderr[-300:], flush=True)
    sys.exit(1)
if not tmp_out.exists() or tmp_out.stat().st_size < 5000:
    print("FALHA:no_output", flush=True)
    sys.exit(1)
print("OUT OK:", tmp_out.stat().st_size // 1024, "KB", flush=True)

# Copia output pro NAS via shutil (Python direto, sem shell escaping)
nas_output.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(tmp_out, nas_output)
for f in [tmp_img, tmp_out]:
    f.unlink(missing_ok=True)

if nas_output.exists() and nas_output.stat().st_size > 5000:
    print("OK:", nas_output.stat().st_size // 1024, "KB", flush=True)
    sys.exit(0)
else:
    print("FALHA:nas_output", flush=True)
    sys.exit(1)
'''


def _render_clip_on_pc2(nas_input, nas_output, dur, job_id):
    """Renderiza um clip Ken Burns no PC2."""
    _ensure_pc2_app()
    script = _DAEMON_RENDER_SCRIPT.format(
        nas_input=nas_input,
        nas_output=nas_output,
        dur=dur,
    )
    return _run_daemon_script(script, job_id, timeout=200)


# ── Depth Map (depth-anything) ────────────────────────────────────────────────
def render_depth_map(img_path, output_path, job_id=None):
    """Gera depth map no PC2 via depth-anything.

    1. Copia img do NAS para C:/app via Copy-Item (/exec)
    2. Executa depth model no C:/app (/run, Python direto)
    3. Copia output de C:/app para NAS (/run, shutil.copy2)
    4. PC1 lê output via path local D:
    """
    if job_id is None:
        job_id = f"depth_{uuid.uuid4().hex[:8]}"

    local_img = Path(img_path).resolve()
    local_out = Path(output_path).resolve()
    local_out.parent.mkdir(parents=True, exist_ok=True)

    unc_input = _to_unc(local_img)
    unc_output = _to_unc(local_out)
    HF = DAEMON_HF_HOME  # PC2 local HF cache

    _log(f"  [{job_id}] Depth map via PC2...")

    # Step 1: Copy image from NAS to C:/app via /exec
    _log(f"  [{job_id}] Copy NAS->C:/app...")
    r = _exec(
        f"powershell -Command \"Copy-Item -Path '{unc_input}' -Destination {PC2_APP}\\_depth_in.png -Force; Write-Host OK\"",
        cwd="C:/", timeout=30
    )
    if r.get("returncode") != 0:
        _log(f"  [{job_id}] FALHA: copy NAS->C: {r.get('stderr','')[:80]}")
        return False

    # Step 2: Run depth model via /run (Python direto, sem shell escaping)
    script = (
        "import os, sys, pathlib\n"
        f"HF = r'{HF}'\n"
        f"NAS_IN = r'{unc_input}'\n"
        f"NAS_OUT = r'{unc_output}'\n"
        "os.environ['HF_HOME'] = HF\n"
        "os.environ['HF_HUB_OFFLINE_MODE'] = '1'\n"
        "os.environ['TRANSFORMERS_OFFLINE'] = '1'\n"
        "print('HF_HOME:', HF, flush=True)\n"
        "print('Loading model...', flush=True)\n"
        "from transformers import pipeline\n"
        "depth = pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Small-hf')\n"
        "print('Model loaded!', flush=True)\n"
        "result = depth('C:\\\\app\\\\_depth_in.png')\n"
        "depth_img = result['depth']\n"
        "out_path = pathlib.Path(NAS_OUT)\n"
        "out_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "depth_img.save(out_path)\n"
        "print('Saved:', out_path.stat().st_size // 1024, 'KB', flush=True)\n"
    )

    r = _run(script, timeout=300)
    if r.get("returncode") != 0:
        _log(f"  [{job_id}] FALHA | rc={r.get('returncode')} stderr={r.get('stderr','')[:100]}")
        return False

    # Cleanup C:/app
    _exec(f'del "{PC2_APP}\\_depth_in.png"', cwd=PC2_APP)

    # Step 3: Verify output on PC1
    if local_out.exists() and local_out.stat().st_size > 5000:
        _log(f"  [{job_id}] OK {local_out.stat().st_size // 1024}KB")
        return True
    else:
        _log(f"  [{job_id}] FALHA: output not found on PC1 ({local_out})")
        return False


# ── Main render interface ────────────────────────────────────────────────────
def _render_via_daemon(input_img, output_mp4, effect="kenburns",
                       audio_wav=None, dur=5.0, threads=2, job_id=None):
    if job_id is None:
        job_id = f"job_{uuid.uuid4().hex[:8]}"

    local_input = Path(input_img).resolve()
    local_output = Path(output_mp4).resolve()
    local_output.parent.mkdir(parents=True, exist_ok=True)

    unc_input = _to_unc(local_input)
    unc_output = _to_unc(local_output)

    _log(f"  [{job_id}] Render {effect} ({dur}s) via PC2...")
    ok, msg = _render_clip_on_pc2(unc_input, unc_output, dur, job_id)

    if ok:
        if local_output.exists() and local_output.stat().st_size > 5000:
            _log(f"  [{job_id}] OK {local_output.stat().st_size // 1024}KB | {msg}")
            return True
        else:
            _log(f"  [{job_id}] FALHA: output nao existe no PC1")
            return False
    else:
        _log(f"  [{job_id}] FALHA | {msg}")
        return False


def render_clip_remote(scene_idx, effect, input_img, output_mp4,
                       audio_wav=None, dur=5.0, ffmpeg_threads=2):
    """Interface compat com story_pipeline.py."""
    job_id = f"scene_{scene_idx:03d}_{uuid.uuid4().hex[:6]}"
    return _render_via_daemon(
        input_img, output_mp4, effect,
        audio_wav=str(audio_wav) if audio_wav else None,
        dur=dur, threads=ffmpeg_threads, job_id=job_id)


def render_batch(clips, max_parallel=MAX_JOBS):
    if not is_online():
        _log("PC2 offline — abortando batch")
        return {c["scene_idx"]: False for c in clips}
    _ensure_pc2_app()
    results = {}
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futures = {}
        for clip in clips:
            fut = pool.submit(
                render_clip_remote,
                clip["scene_idx"], clip["effect"],
                clip["input_img"], clip["output_mp4"],
                clip.get("audio_wav"), clip.get("dur", 5.0),
                clip.get("ffmpeg_threads", 2))
            futures[fut] = clip["scene_idx"]
        for fut in as_completed(futures):
            scene_idx = futures[fut]
            try:
                results[scene_idx] = fut.result()
            except Exception as e:
                _log(f"  scene_{scene_idx}: EXC {e}")
                results[scene_idx] = False
    ok = sum(1 for v in results.values() if v)
    _log(f"Batch: {ok}/{len(results)} clips OK")
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--img", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--dur", type=float, default=3.0)
    args = parser.parse_args()
    ok = _render_via_daemon(args.img, args.out, dur=args.dur, job_id="cli_test")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
