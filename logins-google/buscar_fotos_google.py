# -*- coding: utf-8 -*-
"""Busca no Google Fotos pelo NAVEGADOR (contas ja logadas do cofre) e baixa o que achar. Serve a qualquer projeto.

Dono 22/10/2026: "material real podemos implementar uma busca no Google Fotos via navegador mesmo, tem varias contas
logadas que tem fotos". Sem API (regra: Google so pelo navegador). A busca do Google Fotos entende o conteudo
("painel solar", "telhado"...), igual a caixa de busca do site.

Cada item baixado vai para <destino>/<conta>_<data>_<id>.jpg (video: <destino>/videos/...mp4) e para <destino>/indice_google.json (retomavel: o que
ja esta no indice nao baixa de novo; foto repetida em 2 contas e pulada pelo "hash" da imagem).

    python buscar_fotos_google.py --destino D:\\pasta --buscas "painel solar" "energia solar" [--contas a b] [--videos]
"""
import argparse
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cofre  # noqa: E402

CONTAS = ["fabricadeautomacoesia", "emersongenc", "emersonjosiel649", "emersonjosielmrx1995"]
MESES = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6, "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11,
         "dez": 12}


def _data(aria):
    """'Foto - Retrato - 28 de jun. de 2023, 12:10:02' -> '2023-06-28'"""
    m = re.search(r"(\d{1,2}) de (\w{3})\w*\.? de (\d{4})", aria or "")
    return f"{m.group(3)}-{MESES.get(m.group(2).lower(), 0):02d}-{int(m.group(1)):02d}" if m else "sem-data"


def _hash(dados):
    """dHash 8x8 (64 bits): a mesma foto em 2 contas, ou em tamanhos diferentes, da o mesmo numero."""
    from PIL import Image
    im = Image.open(io.BytesIO(dados)).convert("L").resize((9, 8))
    px = im.tobytes()
    return "%016x" % sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] > px[(i // 8) * 9 + i % 8 + 1])


def _coletar(pg, busca, maximo):
    pg.goto("https://photos.google.com/search/" + quote(busca), wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(8000)
    achados, parado = {}, 0
    while len(achados) < maximo and parado < 4:
        antes = len(achados)
        for it in pg.evaluate("""() => [...document.querySelectorAll('a[href*="/photo/"]')].map(a => {
                const e = a.querySelector('[style*="background-image"]');
                const m = e && e.style.backgroundImage.match(/url\\("?([^")]+)/);
                return {href: a.getAttribute('href'), aria: a.getAttribute('aria-label') || '', img: m ? m[1] : null}; })"""):
            pid = (it["href"] or "").rstrip("/").split("/")[-1]
            if pid and it["img"] and pid not in achados:
                achados[pid] = it
        parado = parado + 1 if len(achados) == antes else 0
        pg.mouse.wheel(0, 2500)
        pg.wait_for_timeout(1800)
    return list(achados.items())[:maximo]


SEM_FOTOS = Path(__file__).resolve().parent / "fotos_contas_vazias.json"  # dono 24/10: conta vazia nao e mais buscada
DIAS_REBUSCA = 14              # 25/10: conta+termo buscado ha menos que isso e pulado (rodar de novo = so o que falta)
VIDEO_MAX_BYTES = 150 * 2**20  # 24/10: video grande travou a busca 2x e estourou a memoria do Chrome ("RangeError")
QUASE_IGUAL_BITS = 6           # 25/10: fotos em rajada (mesma cena) contam como uma so


def _quase_igual(h, ints):
    """dHash a <= 6 bits de alguma ja guardada = mesma cena (rajada, outra resolucao, leve recorte)."""
    x = int(h, 16)
    return any((x ^ y).bit_count() <= QUASE_IGUAL_BITS for y in ints)


def _tamanho(pg, url):
    """Content-Length pelo HEAD (None se o Google nao disser)."""
    try:
        r = pg.request.head(url, timeout=30000)
        return int(r.headers.get("content-length") or 0) or None
    except Exception:  # noqa: BLE001
        return None


def _vazias():
    return json.loads(SEM_FOTOS.read_text("utf-8")) if SEM_FOTOS.exists() else {}


def _biblioteca_vazia(pg):
    """Pagina inicial do Fotos sem nenhuma foto/video = conta vazia."""
    pg.goto("https://photos.google.com/", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(8000)
    if "accounts.google.com" in pg.url:
        return None  # deslogada: nao da pra saber
    return pg.locator('a[href*="/photo/"]').count() == 0


def buscar(destino, buscas, contas=CONTAS, por_busca=150, videos=False, log=print, forcar=False):
    """videos=True baixa tambem os videos (ate VIDEO_MAX_BYTES) para <destino>/videos. forcar=True ignora o
    progresso (busca de novo o que foi buscado ha menos de DIAS_REBUSCA dias)."""
    from datetime import timedelta
    from playwright.sync_api import sync_playwright
    vazias = _vazias()
    pulo = [c for c in contas if c in vazias]
    if pulo:
        log(f"puladas (Google Fotos vazio, {SEM_FOTOS.name}): {', '.join(pulo)}")
    contas = [c for c in contas if c not in vazias]
    destino = Path(destino)
    (destino / "videos").mkdir(parents=True, exist_ok=True)
    arq = destino / "indice_google.json"
    arq_prog = destino / "progresso_busca.json"
    prog = json.loads(arq_prog.read_text("utf-8")) if arq_prog.exists() else {}
    limite = (datetime.now() - timedelta(days=DIAS_REBUSCA)).isoformat()
    ind = json.loads(arq.read_text("utf-8")) if arq.exists() else {}
    vistos = {v.get("id") for v in ind.values()}
    hashes = {v.get("hash") for v in ind.values() if v.get("hash")}
    hash_ints = [int(h, 16) for h in hashes]
    novos = pendentes_gravar = grandes = 0
    for conta in contas:
        if not forcar and all(prog.get(conta, {}).get(b, "") >= limite for b in buscas):
            log(f"{conta}: todos os termos buscados ha menos de {DIAS_REBUSCA} dias — nem abro o Chrome")
            continue
        try:
            porta, proc = cofre.abrir(conta)
        except Exception as e:  # noqa: BLE001
            log(f"{conta}: nao abriu ({e})")
            continue
        br = None
        try:
            with sync_playwright() as p:
                br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
                pg = br.contexts[0].new_page()
                pg.set_viewport_size({"width": 1400, "height": 900})
                pg.set_default_timeout(90000)  # 24/10: travou 2x sem erro na mesma busca (sem limite = espera pra sempre)
                try:
                    vazia = _biblioteca_vazia(pg)
                except Exception as e:  # noqa: BLE001  (24/10: net::ERR_FAILED derrubou a busca inteira)
                    log(f"{conta}: Fotos nao carregou ({type(e).__name__}) — pula esta vez")
                    vazia = "erro"
                if vazia == "erro":
                    buscas_conta = []
                elif vazia is None:
                    log(f"{conta}: pediu login -> python cofre.py logar {conta}")
                    buscas_conta = []
                else:
                    # 24/10: so a pagina inicial marcou aulasrevolution (que tem fotos) como vazia -> confirma com a
                    # 1a busca: so vira "vazia" se ela tambem voltar com 0
                    feitas = prog.get(conta, {})
                    buscas_conta = [b for b in buscas if forcar or feitas.get(b, "") < limite]
                    if len(buscas_conta) < len(buscas):
                        log(f"{conta}: {len(buscas) - len(buscas_conta)} termo(s) buscados ha menos de "
                            f"{DIAS_REBUSCA} dias — pulados")
                for n_busca, busca in enumerate(buscas_conta):
                    try:
                        itens = _coletar(pg, busca, por_busca)
                    except Exception as e:  # noqa: BLE001
                        log(f"{conta} '{busca}': busca falhou ({type(e).__name__})")
                        continue
                    if "accounts.google.com" in pg.url:
                        log(f"{conta}: pediu login -> python cofre.py logar {conta}")
                        break
                    if n_busca == 0 and vazia is True and not itens:
                        vazias[conta] = datetime.now().isoformat(timespec="minutes")
                        SEM_FOTOS.write_text(json.dumps(vazias, indent=1), "utf-8")
                        log(f"{conta}: Google Fotos VAZIO — fica fora das proximas buscas")
                        break
                    baixados = 0
                    for pid, it in itens:
                        if pid in vistos:
                            continue
                        video = it["aria"].lower().startswith("v")  # "Vídeo - ..."
                        if video and not videos:
                            continue
                        base = it["img"].split("=")[0]
                        url = base + ("=dv" if video else "=w2048-h2048-no")
                        if video:
                            tam = _tamanho(pg, url)
                            if tam and tam > VIDEO_MAX_BYTES:
                                grandes += 1
                                vistos.add(pid)
                                continue
                        try:
                            r = pg.request.get(url, timeout=180000)
                            dados = r.body() if r.ok else None
                        except Exception:  # noqa: BLE001
                            dados = None
                        if not dados:
                            continue
                        h = None
                        if not video:
                            try:
                                h = _hash(dados)
                            except Exception:  # noqa: BLE001
                                continue
                            if h in hashes or _quase_igual(h, hash_ints):
                                vistos.add(pid)
                                continue
                            hashes.add(h)
                            hash_ints.append(int(h, 16))
                        nome = ("videos/" if video else "") + f"{conta}_{_data(it['aria'])}_{pid[-12:]}." + (
                            "mp4" if video else "jpg")
                        (destino / nome).write_bytes(dados)
                        ind[nome] = {"id": pid, "conta": conta, "busca": busca, "data": _data(it["aria"]),
                                     "tipo": "video" if video else "foto", "aria": it["aria"], "hash": h,
                                     "baixado": datetime.now().isoformat(timespec="minutes")}
                        vistos.add(pid)
                        novos += 1
                        baixados += 1
                        pendentes_gravar += 1
                        if pendentes_gravar >= 10:  # 25/10: gravar o indice inteiro a cada foto deixava tudo lento
                            arq.write_text(json.dumps(ind, ensure_ascii=False, indent=1), "utf-8")
                            pendentes_gravar = 0
                    arq.write_text(json.dumps(ind, ensure_ascii=False, indent=1), "utf-8")
                    pendentes_gravar = 0
                    prog.setdefault(conta, {})[busca] = datetime.now().isoformat(timespec="minutes")
                    arq_prog.write_text(json.dumps(prog, ensure_ascii=False, indent=1), "utf-8")
                    log(f"{conta} '{busca}': {len(itens)} resultados, {baixados} novos")
                try:
                    pg.close()
                except Exception:  # noqa: BLE001  (24/10: Chrome caiu sem memoria -> derrubava a busca inteira)
                    pass
        finally:
            cofre.fechar(proc, br, conta)
    arq.write_text(json.dumps(ind, ensure_ascii=False, indent=1), "utf-8")
    log(f"total novos: {novos} | no indice: {len(ind)}" + (f" | videos acima de {VIDEO_MAX_BYTES >> 20} MB pulados: "
                                                           f"{grandes}" if grandes else ""))
    return ind


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", required=True)
    ap.add_argument("--buscas", nargs="+", required=True)
    ap.add_argument("--contas", nargs="+", default=CONTAS)
    ap.add_argument("--por-busca", type=int, default=150)
    ap.add_argument("--videos", action="store_true")
    ap.add_argument("--forcar", action="store_true", help="busca de novo termos feitos ha menos de DIAS_REBUSCA dias")
    a = ap.parse_args()
    buscar(a.destino, a.buscas, a.contas, a.por_busca, a.videos, forcar=a.forcar)
