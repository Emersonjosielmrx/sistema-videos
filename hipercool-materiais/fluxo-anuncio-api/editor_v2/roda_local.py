r"""Testa o montador no PC, sem a nuvem: pega os dados de uma execução real do editor no n8n6 (transcrição, quadro,
pedido), roda o monta_edicao.js no node e o comando no ffmpeg local.
    python roda_local.py <id_execucao> <ia.json> <nivel> <video_original.mp4> <saida.mp4>"""
import json, shlex, subprocess, sys, urllib.request
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\fluxos-n8n\ferramentas")
import n8n_servidor as s  # noqa: E402

AQUI = Path(__file__).parent
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
exe, ia_arq, nivel, video, saida = sys.argv[1:6]
TRAB = AQUI / "local"
(TRAB / "inputs").mkdir(parents=True, exist_ok=True)
(TRAB / "outputs").mkdir(exist_ok=True)

cache = TRAB / f"exec_{exe}.json"
if not cache.exists():
    st, r = s.api("GET", f"/executions/{exe}?includeData=true")
    rd = r["data"]["resultData"]["runData"]
    dados = {n: rd[n][0]["data"]["main"][0][0]["json"] for n in ("🧩 Pega o vídeo", "🎧 Deepgram: transcreve", "🧩 Lê a extração")}
    cache.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
dados = json.loads(cache.read_text(encoding="utf-8-sig"))
dados["🧩 Lê a direção"] = json.loads(Path(ia_arq).read_text(encoding="utf-8-sig"))

codigo = (AQUI / "monta_edicao.js").read_text(encoding="utf-8").replace("__NIVEL__", nivel)
js = ("const D = " + json.dumps(dados, ensure_ascii=False) + ";\nconst $ = n => ({ first: () => ({ json: D[n] }) });\n"
      "(async () => { const r = await (async () => {\n" + codigo + "\n})(); console.log(JSON.stringify(r[0].json)); })()"
      ".catch(e => { console.error('ERRO', e.message); process.exit(1); });\n")
(TRAB / "roda.js").write_text(js, encoding="utf-8")
p = subprocess.run(["node", str(TRAB / "roda.js")], capture_output=True, text=True, encoding="utf-8")
if p.returncode:
    raise SystemExit(p.stderr)
res = json.loads(p.stdout)
corpo = json.loads(res["corpo"])
print({k: v for k, v in res.items() if k not in ("corpo", "textos", "fala")})
(TRAB / "inputs" / "in_textos.ass").write_bytes(__import__("base64").b64decode(res["textos"]))
for nome, url in corpo["input_files"].items():
    alvo = TRAB / "inputs" / nome
    if nome == "in_video.mp4":
        alvo.write_bytes(Path(video).read_bytes())
    elif nome != "in_textos.ass" and not nome.endswith(".svg") and (not alvo.exists() or nome == "in_fundo.jpg" or nome.startswith("in_trilha")):
        alvo.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read())
cmd = corpo["ffmpeg_commands"][0]
if res.get("qtd_cards"):   # V6: o ffmpeg do PC não lê SVG (o da nuvem lê): vira PNG num Chrome sem janela e troca no comando
    from playwright.sync_api import sync_playwright
    svgs = json.loads(__import__("base64").b64decode(res["cards"]).decode("utf-8"))
    with sync_playwright() as pw:
        nav = pw.chromium.launch(headless=True)
        pg = nav.new_page()
        for i, sv in enumerate(svgs):
            pg.set_content(f'<html><body style="margin:0;background:transparent">{sv}</body></html>')
            pg.locator("svg").screenshot(path=str(TRAB / "inputs" / f"in_c{i}.png"), omit_background=True)
        nav.close()
    cmd = cmd.replace(".svg ", ".png ")
(TRAB / "comando.txt").write_text(cmd, encoding="utf-8")
r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *shlex.split(cmd)], cwd=TRAB, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", creationflags=0x08000000)
print("ffmpeg:", r.returncode, r.stderr[-1500:])
feito = next((TRAB / "outputs").glob("editado-*.mp4"), None)
if feito:
    Path(saida).write_bytes(feito.read_bytes())
    feito.unlink()
    print("salvo em", saida)
