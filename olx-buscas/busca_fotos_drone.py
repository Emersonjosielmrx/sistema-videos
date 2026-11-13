# -*- coding: utf-8 -*-
"""Procura as fotos do kit do drone DJI Agras T30 no Google Fotos das contas do cofre (pedido da dona em 05/11/2026:
"siga a busca em todas as contas").

Cuidados, porque a regra da casa é nunca usar várias contas pelo mesmo IP:
  - uma conta por vez, com INTERVALO_MIN entre elas, nunca em rajada;
  - só leitura: abre a busca do Google Fotos, sem login e sem mudar nada;
  - ordem: contas pessoais primeiro, contas de canal do YouTube por último;
  - conta já aberta por outro projeto = pula agora e tenta no fim (não mexe no Chrome dos outros);
  - para quando achar fotos suficientes do drone e avisa no Telegram;
  - miniaturas que não são do kit são apagadas na hora.
Progresso: estado/busca_fotos.json; log: estado/busca_fotos.log; fotos achadas: anuncios/fotos_<conta>/
"""
import base64, json, re, sys, time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre
import olx_buscas as o
from curl_cffi import requests as cr
from playwright.sync_api import sync_playwright

INTERVALO_MIN = 10
TERMOS = ["drone", "dji", "pulverizador", "carretinha", "agras", "gerador"]
PARA_COM = 4  # fotos do drone com qualidade >= 5 para parar
EST = o.BASE / "estado" / "busca_fotos.json"
LOG = o.BASE / "estado" / "busca_fotos.log"
TMP = o.BASE / "estado" / "tmp_fotos"
PRIMEIRO = ["emersonjosiel1995", "emersonjosielmrx1995", "emersongenc", "emersongencshin", "mundosolar1995",
            "solarmundo195", "msenergypara", "e4487017", "en1653964", "emersonjosiel649", "emersonjosiel2028"]
JS = r"""() => Array.from(document.querySelectorAll('a[href*="/photo/"]')).slice(0, 40).map(a => {
  const d = a.querySelector('[style*="background-image"]') || a.querySelector('img');
  let src = null; if (d) src = d.src || (d.style.backgroundImage || '').slice(5, -2);
  return {href: a.getAttribute('href'), label: a.getAttribute('aria-label'), src};
})"""
CLASS = """Classifique cada imagem (índice 0..{n}). Procuro fotos de um kit de DRONE AGRÍCOLA DJI Agras T30 para anunciar:
o drone (grande, 6 braços, tanque), carretinha de transporte com placa solar, gerador, misturador de calda, tanque de
1000 L, baterias grandes do drone, controle do drone.
Responda SÓ um JSON: {{"itens": [{{"i": índice, "cat": "drone"|"carretinha"|"gerador"|"misturador"|"tanque"|"bateria"|
"controle"|"kit_varios"|"outro", "o_que": "curto", "qualidade_anuncio": 0-10}}]}}"""


def log(m):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%d/%m %H:%M:%S')} {m}\n")
    print(m, flush=True)


def ordem():
    reg = cofre._ler()["contas"]
    contas = [(e, v) for e, v in reg.items() if "@" in e and v.get("google") == "vivo"
              and e.split("@")[0] not in ("emersonjosielmrx", "contapessoal")
              and (v.get("apelido") or "") != "contapessoal"]
    def chave(ev):
        e, v = ev
        ap = e.split("@")[0]
        if ap in PRIMEIRO:
            return (0, PRIMEIRO.index(ap))
        if not v.get("usos"):
            return (1, ap)
        return (2, ap)  # canais por último
    return [e for e, _ in sorted(contas, key=chave)]


def classificar(arquivos):
    j = o.ler(o.OMNI, {})
    out = []
    for i in range(0, len(arquivos), 4):
        grupo = arquivos[i:i + 4]
        cont = [{"type": "text", "text": CLASS.format(n=len(grupo) - 1)}]
        for a in grupo:
            cont.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(a.read_bytes()).decode()}})
        for _ in range(3):
            try:
                r = cr.post(j["base_url"].rstrip("/") + "/v1/chat/completions", timeout=120,
                            headers={"Authorization": "Bearer " + j["api_key"]},
                            json={"model": "gemini-fila", "temperature": 0.1, "max_tokens": 1500,
                                  "messages": [{"role": "user", "content": cont}]})
                its = json.loads(re.search(r"\{.*\}", r.json()["choices"][0]["message"]["content"], re.S).group(0))["itens"]
                out += [(grupo[x["i"]], x) for x in its if 0 <= x["i"] < len(grupo)]
                break
            except Exception:
                time.sleep(5)
    return out


def uma_conta(email, est):
    ap = email.split("@")[0]
    porta, proc = cofre.abrir(email, url="about:blank", visivel=False)
    if proc is None:
        return "ocupada"
    achados = []
    TMP.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=60000)
            ctx = b.contexts[0]
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            fotos = {}
            try:
                for t in TERMOS:
                    pg.goto("https://photos.google.com/search/" + t, wait_until="commit", timeout=45000)
                    pg.wait_for_timeout(6000)
                    if "accounts.google" in pg.url:
                        return "deslogada"
                    for x in pg.evaluate(JS):
                        if x["src"]:
                            fotos.setdefault(x["href"].split("/photo/")[-1], x)
                arqs = {}
                for fid, x in fotos.items():
                    try:
                        body = ctx.request.get(re.sub(r"=w\d+-h\d+(-no)?", "=w480-h480", x["src"]), timeout=30000).body()
                        if body[:3] == b"\xff\xd8\xff":
                            a = TMP / f"{ap}_{fid[:16]}.jpg"; a.write_bytes(body); arqs[a] = (fid, x)
                    except Exception:
                        pass
                log(f"{ap}: {len(fotos)} fotos nas buscas, {len(arqs)} baixadas")
                for a, c in classificar(list(arqs)):
                    if c.get("cat") not in ("outro", None):
                        fid, x = arqs[a]
                        pasta = o.BASE / "anuncios" / f"fotos_{ap}"
                        pasta.mkdir(parents=True, exist_ok=True)
                        try:  # versão grande para o anúncio
                            big = ctx.request.get(re.sub(r"=w\d+-h\d+(-no)?", "=w2048-h2048", x["src"]), timeout=60000).body()
                            (pasta / f"{c['cat']}_{c.get('qualidade_anuncio', 0)}_{fid[:12]}.jpg").write_bytes(big)
                        except Exception:
                            pass
                        achados.append({"cat": c["cat"], "q": c.get("qualidade_anuncio"), "o_que": c.get("o_que"),
                                        "data": x.get("label")})
            finally:
                for a in TMP.glob(f"{ap}_*.jpg"):
                    a.unlink()  # miniaturas pessoais não ficam no disco
                cofre.fechar(proc, b, email)
    except Exception as e:
        try:
            cofre.fechar(proc, None, email)
        except Exception:
            pass
        return f"erro: {str(e)[:80]}"
    est["achados"][ap] = achados
    return achados


def main():
    est = o.ler(EST, {"feitas": {}, "achados": {}, "ocupadas": []})
    fila = [e for e in ordem() if e not in est["feitas"]] + [e for e in est["ocupadas"]]
    log(f"início: {len(fila)} contas na fila (intervalo {INTERVALO_MIN} min)")
    for n, email in enumerate(fila):
        r = uma_conta(email, est)
        ap = email.split("@")[0]
        if r == "ocupada":
            if email not in est["ocupadas"]:
                est["ocupadas"].append(email)
            log(f"{ap}: aberta por outro projeto, fica para o fim")
            o.gravar(EST, est)
            continue
        if email in est["ocupadas"]:
            est["ocupadas"].remove(email)
        est["feitas"][email] = r if isinstance(r, str) else f"{len(r)} fotos do kit"
        o.gravar(EST, est)
        if isinstance(r, list) and r:
            resumo = ", ".join(f"{x['cat']}({x['q']})" for x in r)
            log(f"{ap}: ACHOU {resumo}")
            o.mandar(f"📷 Fotos do drone: achei {len(r)} na conta <b>{ap}</b>: {resumo}. "
                     f"Salvas em D:\\olx-buscas\\anuncios\\fotos_{ap}")
        else:
            log(f"{ap}: {r if isinstance(r, str) else 'nada do kit'}")
        boas = sum(1 for v in est["achados"].values() for x in v if x["cat"] == "drone" and (x["q"] or 0) >= 5)
        if boas >= PARA_COM:
            log(f"parei: {boas} fotos boas do drone")
            o.mandar(f"✅ Achei {boas} fotos boas do drone. Parei a busca nas contas.")
            return
        if n < len(fila) - 1:
            time.sleep(INTERVALO_MIN * 60)
    log("fim da fila")
    o.mandar("Terminei de procurar as fotos do drone em todas as contas do cofre. Veja D:\\olx-buscas\\estado\\busca_fotos.log")


if __name__ == "__main__":
    main()
