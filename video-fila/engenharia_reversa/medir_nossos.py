"""Mede os NOSSOS Shorts já medidos em views (29/10): o mp4 do ledger + as mesmas medidas do medir.py. Grava
medidas_nossos.jsonl (já medido = pula) e compara quem passou de 500 com quem ficou em <= 10, no geral e no MESMO
canal. Sem yt-dlp, sem IA."""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import medir  # noqa: E402  (traz sem_janela)
from dados_nossos import L, led, ms  # noqa: E402
SAIDA = AQUI / "medidas_nossos.jsonl"
CAMPOS = ("dur", "cortes_s", "cortes_2s", "primeiro_corte", "maior_plano_s", "vol_2s", "vol_dif", "silencio_ini_s")


TMP = Path(r"D:\hipercool-materiais\engenharia_reversa\tmp")
RCLONE = r"D:\tools\rclone.exe"
PAUSA_DRIVE = 45  # s entre um vídeo e outro do Drive
MAX_POR_RODADA = 40  # a tarefa roda de hora em hora: ~40/h deixa folga para o backup da produção


class LimiteDrive(Exception):
    pass


def do_drive(mp4):
    """O Short já foi pro backup: acha o caminho no _NO_DRIVE.md da pasta e traz UM para TMP (quem chama apaga
    depois de medir). None se não achou ou se o D: está com menos de 1 GB."""
    import re
    import shutil
    import subprocess
    import time
    if shutil.disk_usage("D:\\").free < 1e9:
        return None
    try:
        texto = (mp4.parent / "_NO_DRIVE.md").read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"\| " + re.escape(mp4.name) + r" \|[^`]{0,40}`(manhwa-drive:[^`]+)`", texto)
    if not m:
        return None
    if do_drive.buscas >= MAX_POR_RODADA:
        return None
    do_drive.buscas += 1
    TMP.mkdir(parents=True, exist_ok=True)
    destino = TMP / f"{mp4.parent.name[:60]}.mp4"
    time.sleep(PAUSA_DRIVE)  # devagar: o Drive é o mesmo do backup da produção
    for _ in range(3):
        try:
            r = subprocess.run([RCLONE, "copyto", m.group(1), str(destino), "--retries", "1", "--low-level-retries",
                                "2", "--timeout", "60s"], capture_output=True, text=True, errors="replace", timeout=300)
        except subprocess.TimeoutExpired:
            print(f"Drive lento demais ({mp4.parent.name}) — paro a rodada", flush=True)
            raise LimiteDrive()
        # limite POR MINUTO do client_id público do rclone (dividido com o mundo): passa sozinho em ~1 min
        if r.returncode and "per minute" in (r.stderr or "").lower():
            print(f"Drive: limite por minuto em {mp4.parent.name} — espero 90 s", flush=True)
            time.sleep(90)
            continue
        break
    if r.returncode:
        if re.search(r"rateLimitExceeded|userRateLimit|quota|403", r.stderr or "", re.I):
            # 29/10 04:15: o limite do Drive estourou (a produção usa a mesma conta): nunca insistir
            print(f"Drive no limite ({(r.stderr or '').strip()[-120:]}) — paro a rodada", flush=True)
            raise LimiteDrive()
        print(f"Drive falhou em {mp4.parent.name}: {(r.stderr or '').strip()[-150:]}", flush=True)
    return destino if destino.exists() else None


do_drive.buscas = 0  # só busca de verdade conta no limite (sem registro no Drive não gasta a cota da rodada)


def carregar():
    d = {}
    if SAIDA.exists():
        for ln in SAIDA.read_text(encoding="utf-8").splitlines():
            try:
                x = json.loads(ln)
                d[x["vid"]] = x
            except (ValueError, KeyError):
                pass
    return d


def _trava():
    """Uma cópia por vez (tarefa de hora em hora + rodada manual). Solta sozinha se o processo morrer."""
    import msvcrt
    f = open(AQUI / "medir_nossos.lock", "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print("outra cópia já está medindo — saio")
        sys.exit(0)
    return f


def main():
    trava = _trava()  # noqa: F841 (segura até o fim)
    for sobra in TMP.glob("*.mp4"):  # rodada interrompida no meio deixa o vídeo trazido do Drive
        sobra.unlink(missing_ok=True)
    feitos = carregar()
    for x in L:
        if x["vid"] in feitos or not x["projeto"].startswith(("parceiro", "hipercool", "manhwa")):
            continue
        mp4 = Path(led[x["vid"]]["caminho"])
        temporario = False
        if not mp4.exists():
            try:
                mp4 = do_drive(mp4)
            except LimiteDrive:
                break
            if not mp4:
                continue
            temporario = True
        linha = {"vid": x["vid"], "views": x["v"], "canal": x["canal"], "projeto": x["projeto"], "hora": x["hora"]}
        try:
            linha.update(medir.medir(mp4))
        except Exception as e:  # noqa: BLE001
            linha["erro"] = f"{type(e).__name__}: {e}"
        finally:
            if temporario:
                mp4.unlink(missing_ok=True)
        with open(SAIDA, "a", encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
        feitos[x["vid"]] = linha
        print(f"medido {x['vid']} {x['v']:.0f} views dur {linha.get('dur')} cortes/s {linha.get('cortes_s')}", flush=True)
    comparar(list(feitos.values()))


def elegivel(x):
    """True = o feed deu o lote de teste; False = nem mostrou (Fable ER_01: continuaram 100% com < 10 views no
    período); None = sem dado. Sem tabela do Studio, cai nas views de 48 h (>= 100 sim, <= 10 não)."""
    m = ms.get(x["vid"])
    r = (m.get("ret_lista") or {}) if isinstance(m, dict) else {}
    vp, co = r.get("views_periodo"), r.get("continuaram")
    if vp is not None:
        if vp >= 20:
            return True
        if co == 100 and vp < 10:
            return False
    return True if x["views"] >= 100 else False if x["views"] <= 10 else None


def _studio(x):
    m = ms.get(x["vid"]) if isinstance(ms.get(x["vid"]), dict) else {}
    r = m.get("ret_lista") or {}
    return {"pct_media": r.get("pct_media") or m.get("pct_media"), "continuaram": r.get("continuaram")}


def _tabela(out, titulo, a, b, na, nb):
    out += [f"### {titulo}", "", f"| medida | {na} (n {len(a)}) | {nb} (n {len(b)}) |", "|---|---|---|"]
    for c in CAMPOS + ("pct_media",):
        va = [x[c] for x in a if x.get(c) is not None]
        vb = [x[c] for x in b if x.get(c) is not None]
        if va and vb:
            out.append(f"| {c} | {statistics.median(va):.2f} | {statistics.median(vb):.2f} |")
    out.append("")


def _mesmo_canal(out, titulo, xs, eh_a, eh_b):
    g = defaultdict(lambda: ([], []))
    for x in xs:
        if eh_a(x):
            g[x["canal"]][0].append(x)
        elif eh_b(x):
            g[x["canal"]][1].append(x)
    pares = [v for v in g.values() if v[0] and v[1]]
    out += [f"### {titulo} — no MESMO canal ({len(pares)} canais)", "",
            "| medida | mediana da diferença (A − B) | canais A maior / A menor |", "|---|---|---|"]
    for c in CAMPOS + ("pct_media",):
        difs = []
        for a, b in pares:
            va = [x[c] for x in a if x.get(c) is not None]
            vb = [x[c] for x in b if x.get(c) is not None]
            if va and vb:
                difs.append(statistics.median(va) - statistics.median(vb))
        if difs:
            out.append(f"| {c} | {statistics.median(difs):+.2f} | {sum(d > 0 for d in difs)} / {sum(d < 0 for d in difs)} |")
    out.append("")


def comparar(xs):
    """Grava comparacao_nossos.md: (1) elegível x não elegível — o que no VÍDEO acompanha o feed mostrar ou não;
    (2) entre os elegíveis, 2º lote (>= 2.000 views ou % assistido >= 65) x 1º lote só."""
    from datetime import datetime
    xs = [{**x, **_studio(x)} for x in xs if "erro" not in x and x.get("dur")]
    for x in xs:
        x["eleg"] = elegivel(x)
    sim = [x for x in xs if x["eleg"] is True]
    nao = [x for x in xs if x["eleg"] is False]
    lote2 = [x for x in sim if x["views"] >= 2000 or (x.get("pct_media") or 0) >= 65]
    lote1 = [x for x in sim if x not in lote2]
    out = [f"# Os nossos Shorts medidos — {datetime.now():%d/%m %H:%M}", "",
           f"Gerado por `medir_nossos.py` (sem IA). Medidos {len(xs)}: elegíveis {len(sim)}, não elegíveis {len(nao)}, "
           f"sem dado {len(xs) - len(sim) - len(nao)}. Elegível = o feed deu o lote de teste (Fable ER_01).", "",
           "## 1. O feed mostrou x não mostrou", ""]
    _tabela(out, "Geral", sim, nao, "elegível", "não elegível")
    _mesmo_canal(out, "Elegível (A) x não elegível (B)", xs, lambda x: x["eleg"] is True, lambda x: x["eleg"] is False)
    out += ["## 2. Entre os elegíveis: 2º lote x só o 1º", ""]
    _tabela(out, "Geral", lote2, lote1, "2º lote", "1º lote")
    _mesmo_canal(out, "2º lote (A) x 1º lote (B)", sim, lambda x: x in lote2, lambda x: x in lote1)
    # duração em faixas: taxa de elegível e de % assistido >= 65
    out += ["## 3. Duração", "", "| duração | n | % elegível | mediana % assistido (elegíveis) |", "|---|---|---|---|"]
    for a_, b_ in ((0, 20), (20, 30), (30, 45), (45, 60), (60, 90), (90, 999)):
        f = [x for x in xs if a_ <= x["dur"] < b_]
        fe = [x for x in f if x["eleg"] is not None]
        pm = [x["pct_media"] for x in f if x["eleg"] and x.get("pct_media") is not None]
        if f:
            out.append(f"| {a_}–{b_} s | {len(f)} | {sum(x['eleg'] for x in fe) / len(fe) if fe else 0:.0%} | "
                       f"{statistics.median(pm) if pm else '-'} |")
    out.append("")
    texto = "\n".join(out)
    (AQUI / "comparacao_nossos.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
