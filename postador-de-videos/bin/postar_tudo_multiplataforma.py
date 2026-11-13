#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""postar_tudo_multiplataforma.py — YouTube + Instagram + TikTok.

Estende postar_tudo_hoje.py: cada video postado no YouTube eh replicado
automaticamente no Instagram (Graph API, conta mapeada por nicho) e
TikTok (CDP, round-robin entre portas disponiveis).

Uso:
  python postar_tudo_multiplataforma.py --preview
  python postar_tudo_multiplataforma.py                      # posta tudo
  python postar_tudo_multiplataforma.py --so vo3             # so uma categoria
  python postar_tudo_multiplataforma.py --skip-insta         # pula Instagram
  python postar_tudo_multiplataforma.py --skip-tiktok        # pula TikTok
  python postar_tudo_multiplataforma.py --skip-youtube       # so insta+tiktok
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# ── Paths ──
PY_EXE = Path(r"D:\veo\venv\Scripts\python.exe")
PY_EXE_ALT = Path(r"D:\hipercool-videos\venv\Scripts\python.exe")
YT_POSTER = Path(r"D:\postador-de-videos\bin\youtube_poster.py")
IG_POSTER = Path(r"D:\postador-de-videos\bin\instagram_poster.py")
TK_POSTER = Path(r"D:\postador-de-videos\bin\tiktok_cdp_poster.py")
YT_CREDS = Path(r"D:\credenciais-canais\youtube_canais.json")
IG_CREDS = Path(r"D:\credenciais-canais\instagram_contas.json")
VEO_CACHE = Path(r"D:\veo\beta\logs\video_cache.json")
MATERIAIS = Path(r"D:\hipercool-materiais")
POSTADOS = MATERIAIS / "_postados"
LOG_FILE = Path(r"D:\postador-de-videos\logs\multiplataforma_log.json")

DEAD = {
    "fabio com ia", "enpresainovare (financeiro",
    "emersonjosiel1995( motivação", "emersonjosiel1995nov(motivação",
    "nova conta de manga br",
}

# ── Mapeamento YouTube canal → Instagram conta (por nicho) ──
# Nomes parciais (lowercase) do canal YT → nome da conta IG
YT_TO_IG = {
    "fake news":               "fakenews.ia4",
    "sintetize risada":        "sintetizerisada",
    "dança e música":          "danceandmusicwith.ia",
    "danca e musica":          "danceandmusicwith.ia",
    "vídeos cassetadas":       "videocassetadascom.ia",
    "videos cassetadas":       "videocassetadascom.ia",
    "re cenas":                "recenas.ia",
    "ia pro":                  "iapro.mentoria",
    "mentoria":                "iapro.mentoria",
    "energia solar":           "msenergycap",
    "inovare com ia":          "inovarecom.ia",
    "emerson ai":              "emerson.inteligenciaartificial",
    "emerson":                 "emerson.inteligenciaartificial",
    "fabrica de automacoes":   "fabricadeautomacoesia",
    "fabricadeautomacoes":     "fabricadeautomacoesn8n",
    "dicas financeiras":       "dicasfinanceiras.ia",
    "futebol":                 "futebolcom.ia2",
    "game of thrones":         "futebolcom.ia2",
    "lucro com ia":            "_lucrocomia_",
    "lucro":                   "_lucrocomia_",
}
IG_FALLBACK_IA = "inovarecom.ia"
IG_FALLBACK_MANGA = "inovaremanhwaverseesp"

# TikTok CDP ports
TIKTOK_PORTS = [9222, 9251, 9261]


def _is_manga(nome):
    n = nome.lower()
    return "manga" in n or "manhwa" in n or "anime" in n


def carregar_pools_yt():
    cred = json.loads(YT_CREDS.read_text(encoding="utf-8"))
    vivos = [c for c in cred if c["nome"] not in DEAD and c.get("tem_upload")]
    manga = [c["nome"] for c in vivos if _is_manga(c["nome"])]
    ia = [c["nome"] for c in vivos if not _is_manga(c["nome"])]
    return ia, manga


def carregar_contas_ig():
    return json.loads(IG_CREDS.read_text(encoding="utf-8"))


def mapear_canal_para_ig(canal_yt):
    """Dado um canal YT, retorna o nome da conta IG correspondente."""
    low = canal_yt.lower()
    for chave, conta in YT_TO_IG.items():
        if chave in low:
            return conta
    if _is_manga(canal_yt):
        return IG_FALLBACK_MANGA
    return IG_FALLBACK_IA


def carregar_log():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    return {}


def salvar_log(log):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Coleta (reuso do postar_tudo_hoje) ──
def _parse_json(txt):
    import re
    if not txt:
        return {}
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


def rota_vo3(persona, tema, fala, canais_ia):
    import gemini_llm
    canais_txt = "\n".join(f"- {c}" for c in canais_ia)
    prompt = (
        "Voce roteia um Short de IA (VO3) pro canal certo do YouTube e escreve os metadados.\n"
        f"Persona/tema do video: {persona} / {tema}\n"
        f"Fala do video (o que a pessoa diz): {fala[:400]}\n\n"
        f"Canais disponiveis (escolha o mais alinhado ao tema):\n{canais_txt}\n\n"
        "Responda SO um JSON: {\"canal\": \"<nome EXATO de um canal da lista>\", "
        "\"titulo\": \"<titulo viral PT-BR ate 90 chars, pode 1 emoji, com #shorts>\", "
        "\"descricao\": \"<2-3 linhas chamativas + 4-6 hashtags>\", "
        "\"tags\": [\"6-10 tags PT-BR\"]}"
    )
    resp = gemini_llm.generate_text(prompt, max_tokens=500)
    d = _parse_json(resp)
    canal = d.get("canal", "")
    if canal not in canais_ia:
        canal = None
    tit = (d.get("titulo") or persona)[:100]
    desc = d.get("descricao") or f"{persona}\n\n#shorts #ia #viral"
    tags = d.get("tags") or ["shorts", "ia", "viral", "brasil"]
    return canal, tit, desc, tags


def coletar_vo3(canais_ia, limite=None, canal_fixo=None, skip_gemini=False):
    if not VEO_CACHE.is_file():
        return []
    cache = json.loads(VEO_CACHE.read_text(encoding="utf-8"))
    pend = [x for x in cache
            if not (x.get("metrics") or {}).get("posted_url")
            and os.path.isfile(x.get("video_path") or "")]
    vistos, uniq = set(), []
    for x in reversed(pend):
        vp = x["video_path"]
        if vp in vistos:
            continue
        vistos.add(vp)
        uniq.append(x)
    if limite:
        uniq = uniq[:limite]
    itens = []
    if canal_fixo:
        print(f"[vo3] {len(uniq)} pendentes — canal fixo '{canal_fixo}'")
    elif skip_gemini:
        print(f"[vo3] {len(uniq)} pendentes — round-robin SEM Gemini")
    else:
        print(f"[vo3] {len(uniq)} pendentes — roteando com Gemini...")
    for i, x in enumerate(uniq, 1):
        persona = x.get("canal", "")
        tema = x.get("tema", "")
        fala = x.get("fala", "") or ""
        if canal_fixo:
            canal = canal_fixo
            tit = f"{persona} - {tema[:50]} #shorts"
            desc = fala[:200] + "\n\n#shorts #ia #viral"
            tags = ["shorts", "ia", "viral"]
        elif skip_gemini:
            canal = canais_ia[(i - 1) % len(canais_ia)]
            tit = f"{persona} - {tema[:50]} #shorts"
            desc = fala[:200] + "\n\n#shorts #ia #viral"
            tags = ["shorts", "ia", "viral"]
        else:
            try:
                canal, tit, desc, tags = rota_vo3(persona, tema, fala, canais_ia)
            except Exception as e:
                canal, tit, desc, tags = None, f"{persona} #shorts", "#shorts #ia #viral", ["shorts", "ia", "viral"]
                print(f"  ! rota falhou ({type(e).__name__}) — canal auto")
        itens.append({
            "categoria": "vo3", "arquivo": x["video_path"],
            "canal_pref": canal, "canal_pool": canais_ia,
            "titulo": tit, "descricao": desc, "tags": tags,
            "cache_id": x.get("id"), "privacy": "public",
        })
        if i % 10 == 0:
            print(f"  ...{i}/{len(uniq)} roteados")
    return itens


def coletar_materiais(categoria, canais_pool, canais_ia=None):
    import glob as _glob
    itens = []
    for pj in _glob.glob(str(MATERIAIS / "**" / "postar.json"), recursive=True):
        try:
            d = json.loads(Path(pj).read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("categoria") != categoria or d.get("pronto") is False:
            continue
        arq = d.get("arquivo", "")
        full = Path(pj).parent / arq
        if not arq or not full.is_file():
            continue
        canais_item = d.get("canais") or None
        itens.append({
            "categoria": categoria, "arquivo": str(full),
            "canal_pref": (canais_item[0] if canais_item else None),
            "canal_pool": canais_item or canais_pool,
            "titulo": d.get("titulo") or full.stem,
            "descricao": d.get("descricao") or "",
            "tags": d.get("tags") or [],
            "cache_id": None,
            "privacy": d.get("privacy", "public"),
            "postar_json": pj,
        })
    return itens


# ── Postagem YouTube ──
def postar_youtube(canal_nome, item, privacy):
    tags = item["tags"]
    tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)
    cmd = [
        str(PY_EXE), str(YT_POSTER),
        "--video", item["arquivo"],
        "--titulo", item["titulo"],
        "--descricao", item["descricao"],
        "--tags", tags_str,
        "--canal", canal_nome,
        "--privacy", privacy,
    ]
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True,
                           timeout=600, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return "timeout", None
    out = (r.stdout or "") + (r.stderr or "")
    if "POSTADO:" in out or "AGENDADO:" in out:
        url = None
        for tok in out.split():
            if "youtu.be/" in tok:
                url = tok.strip()
                break
        return "ok", url
    low = out.lower()
    if "uploadlimitexceeded" in low or "quotaexceeded" in low or "ratelimitexceeded" in low:
        return "limit", None
    if "invalid_grant" in low or "suspended" in low or "invalid_client" in low:
        return "dead", None
    return "error", out.strip()[-200:]


# ── Postagem Instagram ──
def postar_instagram(video_path, caption, conta_nome):
    """Posta Reel no Instagram. Retorna (ok, msg)."""
    cmd = [
        str(PY_EXE_ALT), str(IG_POSTER),
        "--video", str(video_path),
        "--caption", caption,
        "--conta", conta_nome,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                           env={**os.environ, "PYTHONUTF8": "1"})
    except subprocess.TimeoutExpired:
        return False, "timeout"
    output = r.stdout + r.stderr
    if r.returncode == 0 and "publicado" in output.lower():
        return True, output.strip().split("\n")[-1][:100]
    # Detectar limites
    low = output.lower()
    if "rate limit" in low or "too many" in low or "limit" in low:
        return False, "RATE_LIMIT"
    return False, output.strip()[-150:] if output else f"exit={r.returncode}"


# ── Postagem TikTok ──
def verificar_portas_tiktok(ports):
    import urllib.request
    disponiveis = []
    for p in ports:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{p}/json/version", timeout=3)
            disponiveis.append(p)
        except Exception:
            pass
    return disponiveis


def postar_tiktok(video_path, caption, port):
    """Posta via TikTok CDP. Retorna (ok, msg)."""
    cmd = [
        str(PY_EXE_ALT), str(TK_POSTER),
        "--video", str(video_path),
        "--max", "1",
        "--port", str(port),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180,
                           env={**os.environ, "PYTHONUTF8": "1"})
    except subprocess.TimeoutExpired:
        return False, "timeout"
    output = r.stdout + r.stderr
    if "Post clicked" in output:
        return True, "ok"
    return False, output.strip()[-100:] if output else f"exit={r.returncode}"


# ── Gravar URLs ──
def gravar_posted_url_veo(cache_id, url):
    if not cache_id or not url:
        return
    try:
        cache = json.loads(VEO_CACHE.read_text(encoding="utf-8"))
        for x in cache:
            if x.get("id") == cache_id:
                x.setdefault("metrics", {})["posted_url"] = url
                break
        VEO_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"  ! falha gravando posted_url veo: {e}")


def gravar_posted_url_materiais(item, url):
    pj = item.get("postar_json")
    if not pj or not url:
        return
    try:
        p = Path(pj)
        doc = json.loads(p.read_text(encoding="utf-8"))
        doc["posted_url"] = url
        doc["posted_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"  ! falha gravando posted_url materiais: {e}")


def mover_postado(item):
    dst_dir = POSTADOS / item["categoria"]
    dst_dir.mkdir(parents=True, exist_ok=True)
    src = Path(item["arquivo"])
    if not src.exists():
        return
    dst = dst_dir / src.name
    if dst.exists():
        dst = dst_dir / f"{src.stem}_{int(time.time())}{src.suffix}"
    try:
        shutil.move(str(src), str(dst))
        pj = item.get("postar_json")
        if pj and Path(pj).is_file():
            shutil.move(pj, str(dst_dir / f"{dst.stem}.postar.json"))
    except Exception as e:
        print(f"  ! falha movendo: {e}")


def escolher_canal(item, bloqueados):
    pref = item.get("canal_pref")
    if pref and pref not in bloqueados:
        return pref
    for c in item["canal_pool"]:
        if c not in bloqueados:
            return c
    return None


def main():
    ap = argparse.ArgumentParser(description="Postador multiplataforma: YouTube + Instagram + TikTok")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--so", choices=["vo3", "recap", "animes", "historias"], default=None)
    ap.add_argument("--limite-canal", type=int, default=None)
    ap.add_argument("--vo3-max", type=int, default=None)
    ap.add_argument("--canal-fixo", type=str, default=None)
    ap.add_argument("--skip-gemini", action="store_true")
    ap.add_argument("--skip-youtube", action="store_true", help="Pula YouTube (so insta+tiktok)")
    ap.add_argument("--skip-insta", action="store_true", help="Pula Instagram")
    ap.add_argument("--skip-tiktok", action="store_true", help="Pula TikTok")
    ap.add_argument("--intervalo", type=int, default=30, help="Segundos entre posts (default 30)")
    ap.add_argument("--tiktok-ports", default="9222,9251,9261")
    args = ap.parse_args()

    fazer_yt = not args.skip_youtube
    fazer_ig = not args.skip_insta
    fazer_tk = not args.skip_tiktok

    canais_ia, canais_manga = carregar_pools_yt()
    contas_ig = carregar_contas_ig() if fazer_ig else []
    contas_ig_map = {c["name"].lower().replace("instagram ", ""): c for c in contas_ig}

    tk_ports = [int(p) for p in args.tiktok_ports.split(",")]
    tk_disponiveis = verificar_portas_tiktok(tk_ports) if fazer_tk else []

    print(f"{'='*60}")
    print(f"POSTADOR MULTIPLATAFORMA")
    print(f"{'='*60}")
    print(f"  YouTube:   {'SIM' if fazer_yt else 'NAO'} ({len(canais_ia)} IA + {len(canais_manga)} manga)")
    print(f"  Instagram: {'SIM' if fazer_ig else 'NAO'} ({len(contas_ig)} contas)")
    print(f"  TikTok:    {'SIM' if fazer_tk else 'NAO'} (portas {tk_disponiveis or 'nenhuma'})")
    print()

    # Coletar itens
    cats = [args.so] if args.so else ["recap", "animes", "historias", "vo3"]
    itens = []
    if "recap" in cats:
        itens += coletar_materiais("recap", canais_manga)
    if "animes" in cats:
        itens += coletar_materiais("animes", canais_manga)
    if "historias" in cats:
        itens += coletar_materiais("historias", canais_ia)
    if "vo3" in cats:
        itens += coletar_vo3(canais_ia, limite=args.vo3_max, canal_fixo=args.canal_fixo,
                             skip_gemini=args.skip_gemini)

    print(f"\n=== INVENTARIO ===")
    for cat, n in Counter(it["categoria"] for it in itens).most_common():
        print(f"  {cat:10} {n}")
    print(f"  TOTAL      {len(itens)}")

    if args.preview:
        print(f"\n{'='*60}")
        print("PREVIEW — mapeamento YT → IG:")
        for it in itens[:20]:
            canal = it.get("canal_pref") or "(auto)"
            ig_conta = mapear_canal_para_ig(canal)
            print(f"  [{it['categoria']:8}] YT:{canal[:25]:25} → IG:{ig_conta}")
        print(f"\n>>> NADA POSTADO.")
        return

    # Postagem round-robin
    log = carregar_log()
    bloqueados_yt = set()
    postados = Counter()
    por_canal = Counter()
    ig_bloqueadas = set()
    tk_idx = [0]
    restantes = list(itens)

    rodada = 0
    while restantes:
        rodada += 1
        avancou = False
        ainda = []

        for it in restantes:
            arquivo = it["arquivo"]
            arquivo_key = Path(arquivo).stem

            # ── YouTube ──
            yt_url = None
            canal_yt = None
            if fazer_yt:
                canal_yt = escolher_canal(it, bloqueados_yt)
                if not canal_yt:
                    ainda.append(it)
                    continue
                if args.limite_canal and por_canal[canal_yt] >= args.limite_canal:
                    bloqueados_yt.add(canal_yt)
                    ainda.append(it)
                    continue

                print(f"\n[r{rodada}] {it['categoria']:8} → YT [{canal_yt}] {it['titulo'][:45]}", end=" ", flush=True)
                status, info = postar_youtube(canal_yt, it, it["privacy"])
                if status == "ok":
                    print(f"OK {info or ''}")
                    yt_url = info
                    postados["yt"] += 1
                    por_canal[canal_yt] += 1
                    avancou = True
                    gravar_posted_url_veo(it.get("cache_id"), info)
                    gravar_posted_url_materiais(it, info)
                elif status in ("limit", "limite"):
                    print("LIMITE REAL")
                    bloqueados_yt.add(canal_yt)
                    ainda.append(it)
                    continue
                elif status == "advertencias":
                    print("MUITOS AVISOS — canal em espera")
                    bloqueados_yt.add(canal_yt)
                    ainda.append(it)
                    continue
                elif status == "dead":
                    print("CANAL MORTO")
                    bloqueados_yt.add(canal_yt)
                    ainda.append(it)
                    continue
                elif status == "timeout":
                    print("TIMEOUT")
                    ainda.append(it)
                    continue
                else:
                    print(f"ERRO: {info}")
                    # descarta o item com erro
            else:
                canal_yt = it.get("canal_pref") or it["canal_pool"][0] if it["canal_pool"] else "desconhecido"
                avancou = True

            # ── Instagram ──
            if fazer_ig:
                ig_conta_nome = mapear_canal_para_ig(canal_yt or "")
                if ig_conta_nome not in ig_bloqueadas:
                    caption = it["descricao"] or it["titulo"]
                    if not caption.strip():
                        caption = it["titulo"]
                    print(f"  → IG [{ig_conta_nome}]...", end=" ", flush=True)
                    ok, msg = postar_instagram(it["arquivo"], caption, ig_conta_nome)
                    if ok:
                        print(f"OK")
                        postados["ig"] += 1
                        if arquivo_key not in log:
                            log[arquivo_key] = {}
                        log[arquivo_key]["ig"] = datetime.now().isoformat()
                        log[arquivo_key]["ig_conta"] = ig_conta_nome
                        salvar_log(log)
                    else:
                        if msg == "RATE_LIMIT":
                            print(f"RATE LIMIT — bloqueando {ig_conta_nome}")
                            ig_bloqueadas.add(ig_conta_nome)
                        else:
                            print(f"ERRO: {msg[:80]}")
                    time.sleep(5)

            # ── TikTok ──
            if fazer_tk and tk_disponiveis:
                port = tk_disponiveis[tk_idx[0] % len(tk_disponiveis)]
                tk_idx[0] += 1
                caption_tk = it["titulo"][:100] + " #shorts #viral #fyp #brasil"
                print(f"  → TK [porta {port}]...", end=" ", flush=True)
                ok, msg = postar_tiktok(it["arquivo"], caption_tk, port)
                if ok:
                    print("OK")
                    postados["tk"] += 1
                    if arquivo_key not in log:
                        log[arquivo_key] = {}
                    log[arquivo_key]["tk"] = datetime.now().isoformat()
                    salvar_log(log)
                else:
                    print(f"ERRO: {msg[:80]}")
                time.sleep(3)

            # Mover postado (se YouTube OK ou YouTube desabilitado)
            if fazer_yt and yt_url:
                mover_postado(it)
            elif not fazer_yt:
                pass  # sem YouTube, nao move (video pode ser postado no YT depois)

            if args.intervalo > 0:
                time.sleep(args.intervalo)

        restantes = ainda

        # Checar se ainda tem canais livres
        if fazer_yt:
            pools_ativos = set()
            for it in restantes:
                pools_ativos.update(it["canal_pool"])
            if not (pools_ativos - bloqueados_yt):
                print(f"\n*** Todos os canais YT bateram no limite. ***")
                break
        if not avancou:
            print(f"\n*** Nenhum avanco — encerrando. ***")
            break

    # Resumo
    print(f"\n{'='*60}")
    print(f"RESUMO")
    print(f"{'='*60}")
    if fazer_yt:
        print(f"  YouTube:   {postados.get('yt', 0)} postados")
    if fazer_ig:
        print(f"  Instagram: {postados.get('ig', 0)} postados")
    if fazer_tk:
        print(f"  TikTok:    {postados.get('tk', 0)} postados")
    print(f"  Restantes: {len(restantes)}")
    if fazer_yt:
        print(f"\n  Por canal YT:")
        for c, n in por_canal.most_common():
            blk = " [LIMITE]" if c in bloqueados_yt else ""
            print(f"    {c[:40]:40} {n}{blk}")


if __name__ == "__main__":
    main()
