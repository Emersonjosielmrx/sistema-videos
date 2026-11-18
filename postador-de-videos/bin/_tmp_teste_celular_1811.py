"""18/11 dona: 1 canal por celular (o menor visível no app), posta 1 Short pronto em cada, só pelo celular."""
import json, os, glob, subprocess, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
import politica as pol
sys.stdout.reconfigure(encoding="utf-8")
cj = json.load(open(r"D:\postador-de-videos\config\canais.json", encoding="utf-8"))
L = cj if isinstance(cj, list) else cj.get("canais", cj)
L = list(L.values()) if isinstance(L, dict) else L
cred = {x.get("slug"): (x.get("creds") or [None])[0] for x in L if isinstance(x, dict)}
usados = set()
for l in open(r"D:\postador-de-videos\logs\uploads_ledger.jsonl", encoding="utf-8"):
    try:
        usados.add(os.path.normcase(json.loads(l).get("caminho", "")))
    except ValueError:
        pass
for slug in (sys.argv[1:] or ["inovare_viet", "fiodameada"]):
    cands = []
    for p in glob.glob(r"D:\hipercool-materiais\animes recap\*\*\postar.json"):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        v = os.path.join(os.path.dirname(p), d.get("arquivo", "video.mp4"))
        if d.get("canal") == cred[slug] and d.get("tipo") == "short" and not d.get("posted_url") \
                and d.get("pronto") and os.path.exists(v) and os.path.normcase(v) not in usados:
            cands.append((os.path.getmtime(v), p, v, d))
    if not cands:
        print(f"== {slug}: nenhum Short pronto"); continue
    _, pj, mp4, d = sorted(cands)[0]
    pol.marcar_aprovacao(mp4, "aprovado", "teste celular 18/11 (dona: 1 canal por celular, o menor)")
    cmd = [r"D:\veo\venv\Scripts\python.exe", "youtube_web_poster.py", "--video", mp4, "--titulo", d["titulo"],
           "--descricao", d.get("descricao", ""), "--tags", ",".join(d.get("tags") or []), "--canal", d["canal"],
           "--privacy", "public", "--projeto", "parceiro", "--tipo", "short"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1500,
                       cwd=os.path.dirname(__file__))
    out = (r.stdout + r.stderr).strip()
    print(f"== {slug} ({os.path.basename(os.path.dirname(pj))}) código {r.returncode}")
    print("\n".join(out.splitlines()[-3:]))
    if r.returncode == 0 and "AGENDADO:" in out:
        linha = [l for l in out.splitlines() if l.startswith("AGENDADO:")][-1]
        d.update(posted_url=linha.split()[1], posted_at=datetime.now().astimezone().isoformat(timespec="seconds"),
                 canal_postado=d["canal"], teste_celular=linha)
        open(pj, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))
    try:
        u = open(r"D:\projeto celular sub controle\postagens_celular.jsonl", encoding="utf-8").read().splitlines()[-1]
        x = json.loads(u); print("   celular:", x.get("serial"), x.get("resultado"), x.get("motivo", ""))
    except Exception:
        pass
