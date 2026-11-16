"""anime_auto.py — modo AUTÔNOMO: acha, baixa, roteiriza e renderiza sozinho.

No V2, separa os fluxos em '--modo deitado' e '--modo short', já que buscam fontes
diferentes: recaps longos vs shorts nativos do YouTube.
"""
import argparse
import logging
import os
import subprocess
import sys
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import anime_discover
import anime_fetch
import anime_script
import anime_probe
import anime_metrics
import anime_worker_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE = Path(__file__).resolve().parent.parent / "workspace" / "anime"
PIPELINE = Path(__file__).resolve().parent / "anime-pipeline.py"


def _feitos_path(prefix=""):
    """Arquivo de feitos, separado por modalidade (prefixo)."""
    if prefix:
        return BASE / f"_feitos_{prefix}.txt"
    return BASE / "_feitos.txt"


def _ja_feitos(prefix=""):
    """Retorna o set de IDs já processados."""
    fpath = _feitos_path(prefix)
    if fpath.exists():
        return set(fpath.read_text(encoding="utf-8").split())
    return set()


def _marca_feito(vid, prefix=""):
    """Registra um ID de vídeo como já feito."""
    fpath = _feitos_path(prefix)
    fpath.parent.mkdir(parents=True, exist_ok=True)
    with open(fpath, "a", encoding="utf-8") as f:
        f.write(vid + "\n")


def _slug(s):
    """Transforma um título em nome de pasta seguro."""
    return "".join(c if c.isalnum() else "_" for c in s)[:40].strip("_")


def _cleanup_workspace(work_dir):
    """Apaga os arquivos intermediários, deixando só o vídeo final e o roteiro."""
    keep_files = ["final_anime_deitado.mp4", "final_anime_short.mp4", "roteiro.txt"]
    logging.info(f"[auto|cleanup] Limpando arquivos temporários em {work_dir}...")

    for item in work_dir.iterdir():
        if item.name in keep_files:
            continue

        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as e:
            logging.warning(f"[auto|cleanup] Erro ao apagar {item.name}: {e}")

    logging.info("[auto|cleanup] Limpeza concluída.")


def _prepara_candidato(cand):
    """Baixa o vídeo e tenta extrair transcrição (YT legenda ou Whisper)."""
    vid = cand["id"]
    work = BASE / f"{vid}_{_slug(cand['title'])}"
    work.mkdir(parents=True, exist_ok=True)
    logging.info(f"===== {cand['title'][:60]} ({cand['views']:,} views) =====")

    # 1. transcrição preliminar
    txt, lang = anime_fetch.fetch_captions(cand["url"], work)

    # 2. baixar vídeo
    logging.info("[auto] baixando vídeo-fonte...")
    video = anime_fetch.download_video(cand["url"], work)
    if not video:
        logging.error("[auto] download falhou")
        return None, None, None

    # Fallback se não veio legenda do YT
    if not txt:
        txt, lang = anime_fetch.transcribe_whisper(video)
    if not txt:
        logging.error("[auto] sem transcrição disponível")
        return None, None, None

    return work, video, txt


def fazer_deitado(cand, target_lines, dry_run, use_worker=False,
                  worker_host="100.125.7.77", worker_port=8772):
    """Fluxo para recap longo (deitado 16:9)."""
    _marca_feito(cand["id"], "deitado_attempted")

    work, video, txt = _prepara_candidato(cand)
    if not work:
        if work and work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA", "Baixar ou Transcrição falhou")
        return False

    orig_dur = anime_probe.video_duration(str(video))

    roteiro = work / "roteiro.txt"
    n = anime_script.rewrite_to_file(txt, roteiro, target_lines=target_lines)
    if n == 0:
        if work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA", "Roteirização falhou/Recusa IA", orig_dur=orig_dur)
        return False
    logging.info(f"[auto|deitado] roteiro longo: {n} frases")

    if dry_run:
        logging.info("[auto] DRY-RUN — parou antes de renderizar")
        return True

    if use_worker:
        logging.info(f"[auto|deitado] DESPACHANDO pro worker {worker_host}:{worker_port}...")
        payload = {
            "video_url": cand["url"],
            "titulo": cand["title"],
            "modo": "deitado",
            "work_dir": str(work),
        }
        result = anime_worker_client.run_anime(worker_host, worker_port, payload, timeout=4000)
        if not result or not result.get("ok"):
            err = result.get("error", "desconhecido") if result else "sem resposta"
            logging.error(f"[auto|deitado] Worker falhou: {err}")
            anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA",
                                   f"Worker error: {err}", orig_dur=orig_dur, lines=n)
            if work.exists(): shutil.rmtree(work)
            return False
        logging.info(f"[auto|deitado] Worker OK: {result.get('video_path', '')}")
        vf = Path(result.get("video_path", ""))
    else:
        cmd = [sys.executable, str(PIPELINE),
               "--video-source", str(video), "--script", str(roteiro),
               "--titulo", cand["title"], "--formato", "deitado"]
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        r = subprocess.run(cmd, env=env)
        if r.returncode != 0:
            logging.error(f"[auto|deitado] pipeline falhou (rc={r.returncode})")
            anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA",
                                   f"Pipeline rc={r.returncode}", orig_dur=orig_dur, lines=n)
            return False
        vf = work / "final_anime_deitado.mp4"

    _marca_feito(cand["id"], "deitado")

    # Coleta metricas finais de SUCESSO antes de limpar
    af_dur, vf_dur = 0.0, 0.0
    if vf.exists():
        vf_dur = anime_probe.video_duration(str(vf))
        try:
           import json
           out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "json", str(vf)], capture_output=True, text=True).stdout
           d = json.loads(out)
           for s in d.get("streams",[]):
               if s.get("codec_type") == "audio": af_dur = float(s.get("duration", 0))
        except: pass

    _cleanup_workspace(work)
    logging.info(f"[auto|deitado] PRONTO: {work}")
    anime_metrics.record_job(cand["id"], cand["title"], "deitado", "SUCESSO", orig_dur=orig_dur, lines=n, final_v=vf_dur, final_a=af_dur)
    return True


def fazer_short(cand, target_lines, dry_run, use_worker=False,
                worker_host="100.125.7.77", worker_port=8772):
    """Fluxo para formato curto (9:16)."""
    _marca_feito(cand["id"], "short_attempted")

    work, video, txt = _prepara_candidato(cand)
    if not work:
        if work and work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA", "Baixar ou Transcrição falhou")
        return False

    orig_dur = anime_probe.video_duration(str(video))
    # Teto de 10 linhas: source curta (50s) → 10 linhas → ~30s de narração (bom short)
    # Linha curta no TTS edge-tts = ~3s. Target = 30s → 10 linhas máximo.
    target_lines = min(10, max(5, int(orig_dur / 4.5))) if orig_dur else 8
    logging.info(f"[auto|short] Duração do original: {orig_dur:.1f}s -> Alvo: {target_lines} linhas.")

    roteiro = work / "roteiro.txt"
    n = anime_script.rewrite_to_file(txt, roteiro, target_lines=target_lines)
    if n == 0:
        if work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA", "Roteirização falhou/Recusa IA", orig_dur=orig_dur)
        return False
    logging.info(f"[auto|short] roteiro curto: {n} frases")

    w, h = anime_probe.video_dimensions(str(video))
    ar = w / float(h) if h else 0.0
    if anime_probe.is_vertical(str(video)):
        logging.info(f"[auto|short] fonte VERTICAL ({w}x{h}) — native.")
        short_kind = "native"
    else:
        logging.warning(f"[auto|short] fonte HORIZONTAL ({w}x{h}) — reframe.")
        short_kind = "reframe"

    if dry_run:
        logging.info("[auto] DRY-RUN — parou antes de renderizar")
        return True

    if use_worker:
        logging.info(f"[auto|short] DESPACHANDO pro worker {worker_host}:{worker_port}...")
        payload = {
            "video_url": cand["url"],
            "titulo": cand["title"],
            "modo": "short",
            "work_dir": str(work),
        }
        result = anime_worker_client.run_anime(worker_host, worker_port, payload, timeout=4000)
        if not result or not result.get("ok"):
            err = result.get("error", "desconhecido") if result else "sem resposta"
            logging.error(f"[auto|short] Worker falhou: {err}")
            anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA",
                                   f"Worker error: {err}", orig_dur=orig_dur, lines=n, ar=ar)
            if work.exists(): shutil.rmtree(work)
            return False
        logging.info(f"[auto|short] Worker OK: {result.get('video_path', '')}")
        vf = Path(result.get("video_path", ""))
    else:
        cmd = [sys.executable, str(PIPELINE),
               "--video-source", str(video), "--script", str(roteiro),
               "--titulo", cand["title"], "--formato", "short",
               "--short-source-kind", short_kind]
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        r = subprocess.run(cmd, env=env)
        if r.returncode != 0:
            logging.error(f"[auto|short] pipeline falhou (rc={r.returncode})")
            anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA", f"Pipeline rc={r.returncode}", orig_dur=orig_dur, lines=n, ar=ar)
            return False
        vf = work / "final_anime_short.mp4"

    _marca_feito(cand["id"], "short")

    # Coleta metricas finais de SUCESSO antes de limpar
    af_dur, vf_dur = 0.0, 0.0
    if vf.exists():
        vf_dur = anime_probe.video_duration(str(vf))
        try:
           import json
           out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "json", str(vf)], capture_output=True, text=True).stdout
           d = json.loads(out)
           for s in d.get("streams",[]):
               if s.get("codec_type") == "audio": af_dur = float(s.get("duration", 0))
        except: pass

    _cleanup_workspace(work)
    logging.info(f"[auto|short] PRONTO: {work}")
    anime_metrics.record_job(cand["id"], cand["title"], "short", "SUCESSO", orig_dur=orig_dur, lines=n, final_v=vf_dur, final_a=af_dur, ar=ar)
    return True


def main():
    p = argparse.ArgumentParser(
        description="Recap de anime — modo autônomo. 3 modos de engine:\n"
                    "  local   = tudo aqui (gasta CPU本地)\n"
                    "  worker  = discovery+fetch+script aqui, render no PC2 (max worker)\n"
                    "  both    = short no PC2, deitado aqui (50/50 automático)")
    p.add_argument("--modo", choices=["deitado", "short", "ambos"], default="ambos",
                   help="Formato do vídeo")
    p.add_argument("--engine", choices=["local", "worker", "both"], default="both",
                   help="local=tudo aqui | worker=render no PC2 | both=short no PC2, deitado aqui")
    p.add_argument("--top", type=int, default=5, help="Considera os N mais vistos")
    p.add_argument("--target-lines", type=int, default=40, help="Frases no roteiro (deitado)")
    p.add_argument("--dry-run", action="store_true", help="Só descobre e roteiriza, não renderiza")
    p.add_argument("--limit", type=int, default=1, help="Máximo vídeos por modo (0=infinito)")
    p.add_argument("--fonte", help="URL do canal fonte (modo short com fonte específica)")
    p.add_argument("--id", help="ID de vídeo específico da fonte")
    p.add_argument("--worker-host", default=os.environ.get("ANIME_WORKER_HOST", "100.125.7.77"))
    p.add_argument("--worker-port", type=int,
                   default=int(os.environ.get("ANIME_WORKER_PORT", "8772")))
    args = p.parse_args()

    # ── Checar worker ────────────────────────────────────────────────
    use_worker = args.engine in ("worker", "both")
    worker_online = False
    if use_worker:
        if anime_worker_client.is_online(args.worker_host, args.worker_port):
            h = anime_worker_client.health(args.worker_host, args.worker_port)
            logging.info(f"[auto] Worker PC2 online: cores={h['cores']}, "
                        f"ram={h['ram_gb']}GB, ffmpeg={h['ffmpeg']}")
            worker_online = True
        else:
            logging.warning(f"[auto] Worker PC2 offline — caindo pra LOCAL")
            use_worker = False

    # ── Modo SHORT ──────────────────────────────────────────────────
    if args.modo in ("short", "ambos"):
        logging.info(">>> SHORT — discover...")
        feitos = _ja_feitos("short")
        tentados = _ja_feitos("short_attempted")
        cands = [c for c in anime_discover.discover_shorts(top=args.top)
                  if c["id"] not in feitos and c["id"] not in tentados]
        if not cands:
            logging.warning("[auto] Nenhum candidato short disponível.")
        else:
            logging.info(f"[auto] {len(cands)} candidatos short novos. Engine={args.engine}")

        # Split: worker→short faz tudo no PC2, local→short faz tudo aqui,
        #        both→short vai pro worker (short = vertical = mais leve pro PC2)
        short_engine = "worker" if (args.engine == "both") else args.engine
        short_local = (short_engine == "local")

        for c in cands:
            if short_local:
                ok = fazer_short(c, target_lines=None, dry_run=args.dry_run,
                                use_worker=False)
            else:
                ok = fazer_short(c, target_lines=None, dry_run=args.dry_run,
                                use_worker=True,
                                worker_host=args.worker_host,
                                worker_port=args.worker_port)
            if not ok:
                _marca_feito(c["id"], "short_attempted")
            elif args.limit > 0:
                args.limit -= 1
                if args.limit <= 0:
                    break

    # ── Modo DEITADO ────────────────────────────────────────────────
    if args.modo in ("deitado", "ambos"):
        logging.info(">>> DEITADO — discover...")
        feitos = _ja_feitos("deitado")
        tentados = _ja_feitos("deitado_attempted")
        cands = [c for c in anime_discover.discover(top=args.top)
                  if c["id"] not in feitos and c["id"] not in tentados]
        if not cands:
            logging.warning("[auto] Nenhum candidato deitado disponível.")
        else:
            logging.info(f"[auto] {len(cands)} candidatos deitado novos. Engine={args.engine}")

        # both→deitado fica aqui (deitado = longo = mais seguro local)
        deitado_engine = "local" if (args.engine == "both") else args.engine
        deitado_local = (deitado_engine == "local")

        for c in cands:
            if deitado_local:
                ok = fazer_deitado(c, args.target_lines, args.dry_run,
                                  use_worker=False)
            else:
                ok = fazer_deitado(c, args.target_lines, args.dry_run,
                                  use_worker=True,
                                  worker_host=args.worker_host,
                                  worker_port=args.worker_port)
            if ok and args.limit > 0:
                args.limit -= 1
                if args.limit <= 0:
                    break

if __name__ == "__main__":
    main()
