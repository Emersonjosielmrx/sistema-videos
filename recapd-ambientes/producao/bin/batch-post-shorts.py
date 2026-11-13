#!/usr/bin/env python3
"""batch-post-shorts.py — Corta vídeo censurado em Shorts e agenda no YouTube.

Fluxo:
  1. Corta com split-shorts.py (ou reutiliza --shorts-dir existente)
  2. Gera títulos/descrições/tags virais com anti-ban
  3. Posta cada Short como privado com publishAt agendado pro mesmo dia

Uso:
    python bin/batch-post-shorts.py \\
        --video "D:/hipercool-materiais/videos/VIDEO_CENSURADO.mp4" \\
        --obra "The Meek Cat" --capitulo 1 \\
        --canal "inovare recap manga" \\
        --hora-inicio 14:00 \\
        [--intervalo 30] [--shorts-dir workspace/shorts/the-meek-cat-cap1] \\
        [--dry-run]

Canais disponíveis:
    "inovare recap manga"   → @InovareManhwaVerse
    "nova conta de manga br"→ @inovaremanhwabr
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "bin"))

BRT = timezone(timedelta(hours=-3))

_HOOKS = [
    "ELE FEZ O QUÊ?! 😱",
    "ISSO É INSANO 🔥",
    "NÃO ACREDITO NO QUE ACONTECEU 😭",
    "TODO MUNDO ESTÁ FALANDO DESSE MANHWA 👀",
    "POR QUE NINGUÉM ME CONTOU SOBRE ISSO 🤯",
    "O FINAL DESSE CAP VAI TE CHOCAR 💀",
    "ESSE MANHWA É VICIANTE 🫀",
    "EU PRECISEI PAUSAR AQUI 😤",
    "A CENA MAIS INSANA DO MANHWA 🔥",
    "NÃO ERA PRA GOSTAR TANTO ASSIM 😭",
]

_TAGS_BASE = [
    "manhwa", "manhwabr", "recap manhwa", "manhwa recap", "webtoon",
    "romance coreano", "drama coreano", "shorts", "manhwa shorts",
    "anime br", "mangá recap", "manhwa brasil", "manhwa portugues",
    "webtoon br", "coreia", "manhwa em português",
]

_ANTI_BAN_TITULO = [
    (r"18\s*\+", "conteúdo maduro"),
    (r"hentai|ecchi|porn[oô]", "anime de cultura"),
    (r"nudes|nudez|\bpelad[oa]\b|\bnua\b", "sem roupa"),
    (r"\bsexo\b|coito", "o momento"),
    (r"mamilos|tetas|peitos", "comissão"),
    (r"bunda|raba|nádegas", "traseiro"),
    (r"\bpinto\b|\bpau\b|\brola\b|p[eê]nis|piroca", "instrumento"),
    (r"buceta|vagina|xereca|ppk|xana", "flor"),
    (r"orgasmo", "clímax"),
    (r"assassin\w+|\bmatar\b|\bmorte\b|\bmorreu\b", "desviver"),
    (r"sangue", "suco de tomate"),
    (r"suicídio|se matar", "ir de base"),
]
_ANTI_BAN_C = [(re.compile(p, re.IGNORECASE), s) for p, s in _ANTI_BAN_TITULO]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def anti_ban(texto):
    for rgx, sub in _ANTI_BAN_C:
        texto = rgx.sub(sub, texto)
    return texto


def gerar_titulo(obra, capitulo, part, total):
    if part == 1:
        hook = _HOOKS[(capitulo - 1) % len(_HOOKS)]
        t = f"{hook} | {obra.upper()} Cap.{capitulo} Pt.{part}/{total} #shorts"
    elif part == total:
        t = f"COMO TERMINA ESSE CAPÍTULO?! 🤯 | {obra.upper()} Cap.{capitulo} Pt.{part}/{total} #shorts"
    else:
        hook = _HOOKS[(part - 1) % len(_HOOKS)]
        t = f"{hook} | {obra.upper()} Cap.{capitulo} Pt.{part}/{total} #shorts"
    return anti_ban(t[:100])


def gerar_descricao(obra, capitulo, part, total):
    if part < total:
        continua = f"➡️ PARTE {part + 1} NO MEU PERFIL! Segue pra não perder!"
    else:
        continua = "✅ FIM DO CAPÍTULO! Próximo cap em breve no perfil."
    slug_tag = re.sub(r"[^a-zA-Z0-9]", "", obra)
    desc = (
        f"📖 {obra} — Capítulo {capitulo}, Parte {part} de {total}\n"
        f"{continua}\n\n"
        f"🔥 Segue o perfil pra não perder nenhuma parte!\n"
        f"💬 Comenta o que achou dessa cena!\n"
        f"❤️ Deixa o like se ficou viciado!\n\n"
        f"#{slug_tag} #manhwa #manhwabr #recap #webtoon #shorts #animebrasil #romancecoreano"
    )
    return anti_ban(desc[:5000])


def gerar_tags(obra, capitulo):
    slug = re.sub(r"[^a-zA-Z0-9]", "", obra)
    tags = list(_TAGS_BASE) + [
        obra,
        f"{obra} cap {capitulo}",
        f"{obra} capitulo {capitulo}",
        slug,
        f"cap {capitulo}",
        f"capitulo {capitulo}",
    ]
    return list(dict.fromkeys(tags))[:30]


def calcular_publish_at(hora_inicio_str, parte_idx, intervalo_min):
    """Retorna ISO 8601 UTC para o YouTube (parte_idx 0-based)."""
    h, m = map(int, hora_inicio_str.split(":"))
    agora = datetime.now(BRT)
    base = agora.replace(hour=h, minute=m, second=0, microsecond=0)
    publicar = base + timedelta(minutes=parte_idx * intervalo_min)
    return publicar.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def main():
    ap = argparse.ArgumentParser(description="Corta e agenda Shorts no YouTube")
    ap.add_argument("--video", required=True, help="Vídeo censurado fonte (.mp4)")
    ap.add_argument("--obra", required=True, help="Nome da obra ex. 'The Meek Cat'")
    ap.add_argument("--capitulo", type=int, required=True)
    ap.add_argument("--canal", required=True,
                    help="Nome do canal: 'inovare recap manga' ou 'nova conta de manga br'")
    ap.add_argument("--hora-inicio", required=True,
                    help="HH:MM (horário BRT) da 1ª parte. Ex: 14:00")
    ap.add_argument("--intervalo", type=int, default=30,
                    help="Minutos entre partes (default 30)")
    ap.add_argument("--shorts-dir",
                    help="Dir com Shorts já cortados (pula o split-shorts.py)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Simula sem postar. Mostra títulos e horários.")
    args = ap.parse_args()

    video = Path(args.video)
    if not video.exists():
        print(f"ERRO: vídeo não encontrado: {video}", file=sys.stderr)
        sys.exit(1)

    # 1. Cortar shorts (ou reutilizar dir existente)
    slug = re.sub(r"[^a-z0-9]+", "-", args.obra.lower()).strip("-")
    shorts_dir = (Path(args.shorts_dir) if args.shorts_dir
                  else PROJECT / "workspace" / "shorts" / f"{slug}-cap{args.capitulo}")
    meta_path = shorts_dir / "meta_shorts.json"

    if not meta_path.exists():
        log(f"Cortando Shorts de: {video.name}")
        cmd = [
            sys.executable,
            str(PROJECT / "bin" / "split-shorts.py"),
            "--video", str(video),
            "--obra", args.obra,
            "--capitulo", str(args.capitulo),
            "--out-dir", str(shorts_dir),
        ]
        subprocess.run(cmd, check=True)
        if not meta_path.exists():
            print("ERRO: split-shorts.py não gerou meta_shorts.json", file=sys.stderr)
            sys.exit(1)
    else:
        log(f"Reutilizando Shorts em: {shorts_dir}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    parts = sorted(meta.items())
    total = len(parts)
    log(f"{total} partes encontradas")

    # 2. Postar cada parte
    poster = str(PROJECT / "bin" / "youtube_poster.py")
    resultados = []

    for idx, (part_key, _) in enumerate(parts):
        part_num = idx + 1
        part_files = sorted(shorts_dir.glob(f"*_parte{part_num:02d}.mp4"))
        if not part_files:
            log(f"  AVISO: parte {part_num} não encontrada, pulando")
            continue
        part_file = part_files[0]

        titulo = gerar_titulo(args.obra, args.capitulo, part_num, total)
        descricao = gerar_descricao(args.obra, args.capitulo, part_num, total)
        tags = gerar_tags(args.obra, args.capitulo)
        publish_at = calcular_publish_at(args.hora_inicio, idx, args.intervalo)

        log(f"  Parte {part_num}/{total}: {part_file.name}")
        log(f"    Título : {titulo}")
        log(f"    Tags   : {', '.join(tags[:6])}...")
        log(f"    Agenda : {publish_at} UTC")

        if args.dry_run:
            resultados.append({
                "parte": part_num, "arquivo": str(part_file),
                "titulo": titulo, "publish_at": publish_at, "status": "DRY_RUN",
            })
            continue

        cmd = [
            sys.executable, poster,
            "--video", str(part_file),
            "--titulo", titulo,
            "--descricao", descricao,
            "--tags", ",".join(tags),
            "--canal", args.canal,
            "--privacy", "private",
            "--publish-at", publish_at,
        ]
        try:
            r = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
            linha = r.stdout.strip()
            log(f"    ✓ {linha}")
            resultados.append({
                "parte": part_num, "titulo": titulo,
                "publish_at": publish_at, "resultado": linha, "status": "OK",
            })
        except subprocess.CalledProcessError as e:
            erro = (e.stderr or e.stdout or "").strip()
            log(f"    ✗ ERRO: {erro}")
            resultados.append({
                "parte": part_num, "titulo": titulo,
                "publish_at": publish_at, "status": "ERRO", "erro": erro,
            })

    # 3. Salvar resumo
    resumo_path = shorts_dir / "post_resumo.json"
    resumo_path.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for r in resultados if r["status"] == "OK")
    dr = sum(1 for r in resultados if r["status"] == "DRY_RUN")
    log(f"\n{'=' * 60}")
    if args.dry_run:
        log(f"DRY RUN — {dr}/{total} partes simuladas. Nada foi postado.")
    else:
        log(f"{'✅' if ok == total else '⚠️'} {ok}/{total} partes agendadas. Resumo: {resumo_path}")
    for r in resultados:
        brt_dt = (datetime.fromisoformat(r["publish_at"].replace("Z", "+00:00"))
                  .astimezone(BRT).strftime("%d/%m %H:%M BRT"))
        log(f"  Pt.{r['parte']:02d}: [{r['status']}] {r['titulo'][:60]}")
        log(f"         publica: {brt_dt}")


if __name__ == "__main__":
    main()
