# -*- coding: utf-8 -*-
"""revisar_memes.py — tela para a dona tirar memes ANTIGOS do sorteio dos longos (21/11).

Abre no navegador uma galeria com os memes antigos (vídeos de memes_img/memes e imagens do PACK) e os 20 novos (só
para comparar, marcados NOVO). Clicar em "Remover" grava o nome em config/memes_removidos.json; "Voltar" desfaz.
Nada é apagado do disco: fx_detect.meme_proibido lê a lista e o meme some de todo sorteio (meio do vídeo, resumo,
memes de imagem). Uso: python bin/revisar_memes.py  (Ctrl+C fecha)."""
import html
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

RAIZ = Path(__file__).resolve().parent.parent
MEMES_IMG = RAIZ / "workspace" / "assets" / "memes_img"
LISTA = RAIZ / "config" / "memes_removidos.json"
PORTA = 8794
PASTAS = [("Vídeos antigos", MEMES_IMG / "memes"), ("Imagens antigas", MEMES_IMG / "PACK de imagens e memes"),
          ("Novos (prioridade)", MEMES_IMG / "memes_novos")]
EXT_VIDEO = {".mp4", ".webm"}
EXT_IMG = {".jpg", ".jpeg", ".png", ".gif"}
_trava = threading.Lock()


def _ler():
    try:
        return set(json.loads(LISTA.read_text(encoding="utf-8")).get("removidos", []))
    except (OSError, ValueError, AttributeError):
        return set()


def _gravar(nomes):
    LISTA.write_text(json.dumps({"_leia": "21/11 dona: memes tirados do sorteio dos longos (bin/revisar_memes.py). "
                                          "Tirar o nome daqui = o meme volta. Os arquivos não foram apagados.",
                                 "removidos": sorted(nomes)}, ensure_ascii=False, indent=1), encoding="utf-8")


def _descricoes():
    try:
        cat = json.loads((RAIZ / "config" / "memes_catalogo.json").read_text(encoding="utf-8"))
        return {Path(m["file"].replace("\\", "/")).name: m.get("desc", "") for m in cat.values()}
    except (OSError, ValueError):
        return {}


def _pagina():
    rem, desc = _ler(), _descricoes()
    blocos = []
    for titulo, pasta in PASTAS:
        arqs = sorted(p for p in pasta.glob("*") if p.suffix.lower() in EXT_VIDEO | EXT_IMG) if pasta.exists() else []
        novo = pasta.name == "memes_novos"
        cards = []
        for p in arqs:
            src = "/arq/" + quote(f"{pasta.name}/{p.name}")
            midia = (f'<video src="{src}" preload="none" controls playsinline></video>' if p.suffix.lower() in EXT_VIDEO
                     else f'<img src="{src}" loading="lazy" alt="">')
            fora = p.name in rem
            botao = "" if novo else (f'<button data-n="{html.escape(p.name)}">'
                                     f'{"Voltar" if fora else "Remover"}</button>')
            cards.append(f'<div class="c{" fora" if fora else ""}">{midia}<p>{html.escape(desc.get(p.name) or p.stem)}'
                         f'</p>{botao}</div>')
        blocos.append(f"<h2>{titulo} <small>({len(arqs)})</small></h2><div class=g>{''.join(cards)}</div>")
    return f"""<!doctype html><html lang=pt-br><meta charset=utf-8><meta name=viewport content="width=device-width">
<title>Revisar memes</title><style>
:root{{--bg:#16161a;--fg:#eee;--card:#24242a;--ac:#e05050}}
body{{background:var(--bg);color:var(--fg);font:14px system-ui;margin:0;padding:16px}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}}
.c{{background:var(--card);border-radius:8px;padding:8px}} .c.fora{{opacity:.35}}
video,img{{width:100%;height:160px;object-fit:contain;background:#000;border-radius:4px}}
p{{margin:6px 0;font-size:12px;min-height:30px}} button{{width:100%;padding:8px;border:0;border-radius:6px;
background:var(--ac);color:#fff;font-weight:600;cursor:pointer}} .fora button{{background:#4a8}}
#top{{position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:2}}</style>
<div id=top><b>Memes dos longos</b>: clique em <b>Remover</b> para tirar o meme do sorteio (nada é apagado).
Removidos: <b id=n>{len(rem)}</b></div>{''.join(blocos)}
<script>document.addEventListener('click',async e=>{{const b=e.target.closest('button');if(!b)return;
const r=await fetch('/alternar?n='+encodeURIComponent(b.dataset.n),{{method:'POST'}});const j=await r.json();
const c=b.closest('.c');c.classList.toggle('fora',j.fora);b.textContent=j.fora?'Voltar':'Remover';
document.getElementById('n').textContent=j.total;}});</script></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _resp(self, corpo, tipo, cod=200):
        self.send_response(cod)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            return self._resp(_pagina().encode("utf-8"), "text/html; charset=utf-8")
        if u.path.startswith("/arq/"):
            pasta, _, nome = unquote(u.path[5:]).partition("/")
            base = {p.name: p for _t, p in PASTAS}.get(pasta)
            arq = (base / nome) if base else None
            if arq and arq.is_file() and arq.parent == base:
                tipo = {".mp4": "video/mp4", ".webm": "video/webm", ".gif": "image/gif", ".png": "image/png"}.get(
                    arq.suffix.lower(), "image/jpeg")
                return self._resp(arq.read_bytes(), tipo)
        self._resp(b"nao achei", "text/plain", 404)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path != "/alternar":
            return self._resp(b"", "text/plain", 404)
        nome = unquote(u.query.partition("n=")[2])
        with _trava:
            rem = _ler()
            fora = nome not in rem
            (rem.add if fora else rem.discard)(nome)
            _gravar(rem)
        self._resp(json.dumps({"fora": fora, "total": len(rem)}).encode(), "application/json")


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORTA), H)
    url = f"http://127.0.0.1:{PORTA}/"
    print(f"Revisão de memes em {url} (Ctrl+C fecha)")
    if "--sem-navegador" not in sys.argv:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
