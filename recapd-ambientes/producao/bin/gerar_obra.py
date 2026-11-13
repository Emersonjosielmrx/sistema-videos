# -*- coding: utf-8 -*-
"""gerar_obra.py — Orquestrador do fluxo 3 fases (edge → gemini voz masc → censurada).

Implementa o fluxo exato desenhado com a usuária pra economizar quota e tempo:
- FASE 1: edge (prévia 720p). Tudo keyless, offline, veloz. Gera o normal/v1.mp4.
- FASE 2: gemini MALE_ONLY (final 1080p). Usa TTS_ENGINE=gemini + GEMINI_MALE_ONLY=1.
          Narrador (Francisca) e Mulheres reusam o cache da Fase 1 (0 quota).
          Só personagens masculinos chamam o Gemini (trocam a voz do Antonio).
- FASE 3: censurada. Pega do cache da Fase 2 e queima o mosaico/upscale 1080p.

MODOS DE USO:
  --alta-producao     # Pula Fase 1. Vai direto pra Fase 2 + Fase 3.
  --previa            # Roda só Fase 1. Você assiste e depois aprova.
  --aprovar           # Roda Fase 2 + Fase 3 nos caps pré-aprovados.

Exemplos:
  python bin/gerar_obra.py --obra regressed-warriors --caps 4-47 --alta-producao
  python bin/gerar_obra.py --obra the-meek-cat --caps 8 --previa
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PY = Path("D:/recapd-ambientes/producao/venv/Scripts/python.exe")

TITULOS = {
    "regressed-warriors": "O Guerreiro Regressou — Capitulo {cap}",
    "the-meek-cat": "The Meek Cat — Capitulo {cap}",
    "perverts-daily-life": "A Perverts Daily Life — Capitulo {cap}",
    "wonderful-new-world": "Wonderful New World — Capitulo {cap}",
}

def log(msg):
    print(f"\n{'='*60}\n[GERAR_OBRA] {msg}\n{'='*60}", flush=True)

def run_pipeline(obra, cap_num, is_fase23=False, dry_run=False):
    slug = f"{obra}-cap{cap_num:02d}"
    panels = PROJECT / "workspace" / "panels" / slug
    if not panels.is_dir() and not dry_run:
        log(f"PULANDO {slug} — painéis não encontrados")
        return False

    titulo = TITULOS.get(obra, f"{obra} — Capitulo {{cap}}").format(cap=cap_num)
    bas_cmd = [
        str(PY), "bin/hiper-pipeline.py",
        "--panels-dir", str(panels), "--titulo", titulo,
        "--narrator-gender", "M", "--max-panels", "120",
        "--subtitles", "--karaoke", "--skip-notify"
    ]

    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["GEMINI_TTS_PROXY_ENABLED"] = "1"

    if not is_fase23:
        # FASE 1: Prévia Edge (720p, rápido)
        log(f"FASE 1: Prévia (Edge TTS) — {slug}")
        env["TTS_ENGINE"] = "edge"
        cmd = bas_cmd + ["--preset", "teste"]
        
        if dry_run:
            print(f"CMD: {' '.join(cmd)}")
            print(f"ENV_VARS: TTS_ENGINE={env.get('TTS_ENGINE')} GEMINI_MALE_ONLY={env.get('GEMINI_MALE_ONLY')}")
            return True
            
        r = subprocess.run(cmd, cwd=str(PROJECT), env=env)
        return r.returncode == 0
    else:
        # FASE 2 + 3: Gemini Male-Only (1080p, principal + censurada)
        log(f"FASE 2+3: Gemini (troca voz masculina) + Censurada — {slug}")
        env["TTS_ENGINE"] = "gemini"
        env["GEMINI_MALE_ONLY"] = "1"
        env["CENSURA_BRANCO_VAR"] = "B2"
        cmd = bas_cmd + ["--preset", "final", "--censura"]
        
        if dry_run:
            print(f"CMD: {' '.join(cmd)}")
            print(f"ENV_VARS: TTS_ENGINE={env.get('TTS_ENGINE')} GEMINI_MALE_ONLY={env.get('GEMINI_MALE_ONLY')} CENSURA_BRANCO_VAR={env.get('CENSURA_BRANCO_VAR')}")
            return True

        r = subprocess.run(cmd, cwd=str(PROJECT), env=env)
        return r.returncode == 0

def prse_caps(caps_str):
    if "-" in caps_str:
        start, end = map(int, caps_str.split("-"))
        return list(range(start, end + 1))
    return [int(c) for c in caps_str.split(",")]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--obra", required=True, help="Slug da obra (ex: regressed-warriors)")
    p.add_argument("--caps", required=True, help="Capítulos: ex 4 ou 4-47 ou 4,5,6")
    p.add_argument("--dry-run", action="store_true", help="Apenas mostra os comandos")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--alta-producao", action="store_true", help="Direto Fase 2+3 (alta prod)")
    g.add_argument("--previa", action="store_true", help="Só Fase 1 (edge 720p p/ assistir)")
    g.add_argument("--aprovar", action="store_true", help="Gera Fase 2+3 do cap já visto")
    args = p.parse_args()

    caps = prse_caps(args.caps)
    log(f"INICIANDO lote: {args.obra} caps {args.caps}")

    for c in caps:
        if args.previa:
            run_pipeline(args.obra, c, is_fase23=False, dry_run=args.dry_run)
        elif args.aprovar or args.alta_producao:
            run_pipeline(args.obra, c, is_fase23=True, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
