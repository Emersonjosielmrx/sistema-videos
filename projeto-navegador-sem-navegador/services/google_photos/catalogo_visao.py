# -*- coding: utf-8 -*-
r"""services/google_photos/catalogo_visao.py — catálogo do Google Fotos com etiquetas por visão (SQLite).

Busca por HTTP (fotos_http.FotosHTTP), baixa só a miniatura (=w512-h512), pergunta ao Gemini do gateway
(agy/gemini-3.8-flash-high, reserva antigravity/gemini-3-flash — regra do dono: sem Opus/Kiro em pipeline) e grava em
D:\hipercool-materiais\catalogo_fotos\catalogo.db. Retomável: foto já catalogada não é perguntada de novo.

    python -m services.google_photos.catalogo_visao <conta> "painel solar" "inversor" [--maximo 40]
    python -m services.google_photos.catalogo_visao --tag "telhado colonial"        # consulta
"""
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.append(r"D:\hipercool-materiais\comum")  # no fim do sys.path (regra 23/10)
from services.google_photos.fotos_http import FotosHTTP  # noqa: E402

DB = Path(r"D:\hipercool-materiais\catalogo_fotos\catalogo.db")
MODELOS = ["agy/gemini-3.8-flash-high", "antigravity/gemini-3-flash"]
PERGUNTA = ('Describe this photo for a stock catalog used to pick images for product videos. Answer ONLY JSON: '
            '{"tags": [5 to 12 short tags IN PORTUGUESE, lowercase, concrete things visible, e.g. "painel solar no '
            'telhado", "telhado colonial", "inversor string", "instalador", "fachada"], "descricao": "one sentence in '
            'Portuguese", "tem_pessoa": true/false, "texto_na_imagem": true/false (screenshot, document or big text), '
            '"qualidade": "boa"|"media"|"ruim" (blur, dark, bad framing = ruim)}')


def _db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS fotos (id TEXT PRIMARY KEY, conta TEXT, link TEXT, largura INT, altura INT,
                 quando_ms INT, video INT, busca TEXT, tags TEXT, descricao TEXT, tem_pessoa INT, texto INT,
                 qualidade TEXT, catalogado TEXT)""")
    return c


def _gateway():
    c = json.loads(Path(r"D:\hipercool-videos\secrets\claude_proxy.json").read_text("utf-8"))
    return c["base_url"].rstrip("/"), c["auth_token"]


def _visao(b):
    import visao_capa
    gw = _gateway()
    for m in MODELOS:
        r = visao_capa.perguntar(b, PERGUNTA, gateway=gw, modelo=m, max_tokens=400)
        if r and r.get("tags"):
            return r
    return None


def catalogar(conta, buscas, maximo=40, log=print):
    db = _db()
    f = FotosHTTP(conta)
    novos = 0
    for termo in buscas:
        fotos = [x for x in f.buscar(termo, maximo + 60) if not x["video"]][:maximo]  # a grade começa pelos vídeos
        for it in fotos:
            if db.execute("SELECT 1 FROM fotos WHERE id=?", (it["id"],)).fetchone():
                continue
            mini = f.s.get(it["link"] + "=w512-h512", timeout=60)
            if mini.status_code != 200 or not mini.headers.get("content-type", "").startswith("image"):
                log(f"  miniatura não veio ({mini.status_code}): {it['id']}")  # não manda HTML de erro para a visão
                continue
            r = _visao(mini.content)
            if not r:
                log(f"  sem resposta da visão: {it['id']}")
                continue
            db.execute("INSERT OR REPLACE INTO fotos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (it["id"], conta, it["link"], it["largura"], it["altura"], it["quando_ms"], 0, termo,
                        json.dumps(r.get("tags", []), ensure_ascii=False), r.get("descricao", ""),
                        int(bool(r.get("tem_pessoa"))), int(bool(r.get("texto_na_imagem"))), r.get("qualidade", ""),
                        time.strftime("%Y-%m-%d %H:%M")))
            db.commit()
            novos += 1
            log(f"  {it['id'][-10:]}: {', '.join(r['tags'][:6])} | {r.get('qualidade')}")
    db.close()
    return novos


def por_tag(tag, boas=True):
    """Fotos cuja etiqueta contém o texto (para o gerador de vídeo puxar). Sem prints/documentos e, por padrão, só boas."""
    q = "SELECT id, conta, link, tags, descricao, qualidade FROM fotos WHERE tags LIKE ? AND texto = 0"
    if boas:
        q += " AND qualidade = 'boa'"
    db = _db()  # 30/10: fecha — o gerador de vídeo chama isto muitas vezes no mesmo processo
    try:
        return [dict(zip(("id", "conta", "link", "tags", "descricao", "qualidade"), r))
                for r in db.execute(q, (f"%{tag.lower()}%",))]
    finally:
        db.close()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if a[0] == "--tag":
        for r in por_tag(a[1]):
            print(r["id"], r["qualidade"], r["tags"], r["link"][:60])
        return
    maximo = int(a[a.index("--maximo") + 1]) if "--maximo" in a else 40
    buscas = [x for i, x in enumerate(a[1:], 1) if not x.startswith("--") and a[i - 1] != "--maximo"]
    print("novas:", catalogar(a[0], buscas, maximo))


if __name__ == "__main__":
    main()
