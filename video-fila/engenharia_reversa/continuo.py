# -*- coding: utf-8 -*-
r"""continuo.py — engenharia reversa CONTÍNUA (dona 29/10): "deixar funcionando continuamente para gerar aprendizado;
rodar no vídeo base que vai ser feito e nos canais parceiros, em prioridade os que eu listar no painel (vídeo ou canal
inteiro); assim aprendemos muito com os outros canais".

Cada passada (tarefa ERContinuo, a cada 2 h; tudo sem IA, só ffmpeg/yt-dlp pela vez única; nunca abre janela):
  1. PRIORIDADES do painel (config\er_prioridades.json): canal → lista do canal (anime_discover.discover_canal, cache/
     proxy) → baixa os N mais vistos e os N menos vistos (480p, pausa, para no bloqueio) em
     D:\hipercool-materiais\engenharia_reversa\amostras\prioridade_<nome>\<id>\ ; vídeo → baixa só ele. Depois mede
     (medir.py) e escreve o achado (top × baixo do MESMO canal) em RESULTADOS_CONTINUO.md; marca feito.
  2. VÍDEO BASE: todo source.mp4 novo do Cortes (workspace\anime\<id>\) ganha fonte_medidas.json (duração, cortes/s,
     1º corte, silêncio inicial, volume do começo; desde 30/10 só dos 2 primeiros minutos, campo janela_s) — o
     pipeline/júri/brief passam a saber como é a fonte ANTES de cortar.
  3. Sem prioridade pendente: amostra de fundo dos parceiros que mais viram Shorts nossos (amostra.py --n 2 --max 4).
  4. medir.py (amostras novas) + medir_nossos.py (os nossos com views) → medidas.jsonl / medidas_nossos.jsonl.
  5. Resumo curto no Telegram (portão, rotina) e a cauda em RESULTADOS_CONTINUO.md (o melhorador central lê).
Regras: disco D ≥ 5 GB para baixar; 1 download por vez pela ytdlp_vez; proxy/pausa do IP respeitados pelo discover.

    python continuo.py [--simular] [--max 6]
Painel: aba "Engenharia reversa" (adicionar canal/vídeo prioritário, ver resultados).
"""
import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401
sys.path.insert(0, str(AQUI))
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import amostra  # noqa: E402  (baixar, listas, SAIDA, log)
import medir  # noqa: E402

CONFIG = Path(r"D:\video-fila\config\er_prioridades.json")
RESULTADOS = AQUI / "RESULTADOS_CONTINUO.md"
FONTES = AQUI / "medidas_fontes.jsonl"
WORK_CORTES = Path(r"D:\recapd-ambientes\producao\workspace\anime")
MIN_LIVRE_GB = 5
JANELA_FONTE_S = 120  # mede só os 2 primeiros minutos da fonte (AV1 longo não cabe no tempo; ver medir.medir)
PY = sys.executable
CAMPOS = ("dur", "cortes_s", "cortes_2s", "primeiro_corte", "maior_plano_s", "vol_2s", "vol_dif", "silencio_ini_s")


def log(m):
    amostra.log("[continuo] " + m)


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _anotar(texto):
    RESULTADOS.parent.mkdir(parents=True, exist_ok=True)
    if not RESULTADOS.exists():
        RESULTADOS.write_text("# Resultados da engenharia reversa contínua (o mais novo no fim)\n\n", encoding="utf-8")
    with RESULTADOS.open("a", encoding="utf-8") as f:
        f.write(texto.rstrip() + "\n\n")


def livre_gb():
    return shutil.disk_usage("D:\\").free / 1e9


# ───────── prioridades (painel) ─────────
def prioridades():
    d = _ler(CONFIG, {"itens": []})
    d.setdefault("itens", [])
    return d


def _salvar_prioridades(d):
    """30/10: grava por cima do que está NO ARQUIVO, item a item (id). A passada segura `d` por minutos (downloads +
    90 s entre eles) e o painel pode ter acrescentado prioridade nesse meio-tempo: gravar `d` inteiro apagava a nova."""
    atual = prioridades()
    meus = {i.get("id"): i for i in d["itens"]}
    atual["itens"] = [meus.get(i.get("id"), i) for i in atual["itens"]]
    _gravar(CONFIG, atual)


def adicionar(alvo, tipo=None, quem="painel"):
    """Entrada do painel: URL/@ de canal ou URL de vídeo."""
    alvo = alvo.strip()
    if not tipo:
        tipo = "video" if re.search(r"/shorts/|watch\?v=|youtu\.be/", alvo) else "canal"
    if tipo == "canal" and alvo.startswith("@"):
        alvo = "https://www.youtube.com/" + alvo + "/shorts"
    if tipo == "canal" and "youtube.com/@" in alvo and "/shorts" not in alvo:
        alvo = alvo.rstrip("/") + "/shorts"
    d = prioridades()
    if any(i["alvo"] == alvo and i.get("estado") in ("aberto", "medindo") for i in d["itens"]):
        return d
    novo_id = f"{datetime.now():%Y%m%d%H%M%S}"
    ids = {i.get("id") for i in d["itens"]}
    k = 2
    while novo_id in ids:  # dois pedidos no mesmo segundo
        novo_id = f"{datetime.now():%Y%m%d%H%M%S}_{k}"
        k += 1
    d["itens"].append({"id": novo_id, "tipo": tipo, "alvo": alvo, "quem": quem,
                       "em": datetime.now().isoformat(timespec="seconds"), "estado": "aberto"})
    _gravar(CONFIG, d)
    return d


def _nome(url):
    return amostra.nome_parceiro(url) if "/@" in url or "/channel/" in url else re.sub(r"\W+", "_", url.split("/")[-1])[:40]


def _baixar_item(item, pasta, grupo, nome, simular):
    vid = item.get("id") or re.sub(r"\W+", "", (item.get("url") or "").split("/")[-1])[:20]
    destino = pasta / vid
    if (destino / "video.mp4").exists():
        return "já"
    if simular:
        log(f"  [simular] baixaria {grupo} {item.get('url')} ({item.get('views')} views)")
        return "simulado"
    if livre_gb() < MIN_LIVRE_GB:
        log(f"  disco D com {livre_gb():.1f} GB: não baixo")
        return "sem_disco"
    falta = amostra.ytdlp_vez.pausado()  # 30/10: antes baixava mesmo com o IP do PC em pausa
    if falta:
        log(f"  IP pausado por mais {falta / 60:.0f} min: não baixo")
        return "bloqueio"
    r = amostra.baixar(item, destino)
    if r.returncode != 0 or not (destino / "video.mp4").exists():
        log(f"  download falhou {item.get('url')}: {(r.stderr or '').strip()[-200:]}")
        # stderr inteiro (o aviso de robô vem antes do texto de cookies) e pausa o PC como a amostra.py faz
        if amostra.ytdlp_vez.bloqueio(r.stderr):
            amostra.registrar_bloqueio(r.stderr, f"prioridade {nome}")
            return "bloqueio"
        return "erro"
    (destino / "lista.json").write_text(json.dumps({"parceiro_nome": nome, "grupo": grupo, "id": vid,
                                                   "views": item.get("views"), "url": item.get("url"),
                                                   "titulo": item.get("title") or item.get("titulo")}, ensure_ascii=False),
                                       encoding="utf-8")
    return "ok"


def atender_prioridades(n, max_down, simular):
    d = prioridades()
    baixados = 0
    parar = False
    for it in [x for x in d["itens"] if x.get("estado") == "aberto"]:
        if baixados >= max_down or parar:
            break
        nome = "prioridade_" + _nome(it["alvo"])
        pasta = amostra.SAIDA / nome
        log(f"prioridade {it['tipo']}: {it['alvo']}")
        try:
            if it["tipo"] == "video":
                r = _baixar_item({"url": it["alvo"], "views": None}, pasta, "video", nome, simular)
                baixados += r == "ok"
                parar = r in ("bloqueio", "sem_disco")  # IP barrado ou disco cheio vale para os próximos itens também
                it["estado"] = "medindo" if r in ("ok", "já") else ("aberto" if r in ("bloqueio", "sem_disco", "simulado") else "erro")
                it["obs"] = r
            else:
                import anime_discover
                itens = [x for x in anime_discover.discover_canal(it["alvo"]) if x.get("views") and x.get("url")]
                if not itens:
                    if amostra.ytdlp_vez.pausado():  # lista vazia por causa da pausa do IP: tenta na próxima passada
                        it["obs"], parar = "lista vazia com o IP em pausa — tento de novo", True
                    else:
                        it["estado"], it["obs"] = "erro", "canal sem lista (discover vazio: URL errada ou canal sem Shorts)"
                    continue
                itens.sort(key=lambda x: -(x.get("views") or 0))
                k = min(n, len(itens) // 2)  # canal com menos de 2N Shorts: o mesmo vídeo não entra em top E baixo
                escolhidos = [(x, "top") for x in itens[:k]] + [(x, "baixo") for x in itens[len(itens) - k:]]
                if not escolhidos:
                    it["estado"], it["obs"] = "erro", f"canal com {len(itens)} Short(s) com views: pouco para top × baixo"
                    continue
                it["n_lista"] = len(itens)
                parou = False
                for x, grupo in escolhidos:
                    r = _baixar_item(x, pasta, grupo, nome, simular)
                    baixados += r == "ok"
                    if r == "bloqueio" or r == "sem_disco":
                        parou = parar = True
                        break
                    if r == "ok":
                        time.sleep(90)
                tem = sum(1 for x, g in escolhidos if (pasta / (x.get('id') or '-') / 'video.mp4').exists())
                # 30/10: sem nenhum vídeo baixado (todos deram erro) ia para "medindo" e ficava preso para sempre
                it["estado"] = "aberto" if (parou or simular) else "medindo" if tem else "erro"
                it["obs"] = f"{tem}/{len(escolhidos)} baixados"
        except Exception as e:  # noqa: BLE001
            it["estado"], it["obs"] = "erro", f"{type(e).__name__}: {str(e)[:120]}"
            log(f"  prioridade falhou: {it['obs']}")
        finally:  # a cada item (inclusive nos `continue`): passada morta no meio não perde o que já andou
            if not simular:
                _salvar_prioridades(d)
    return baixados


def concluir_prioridades():
    """Depois do medir.py: compara top × baixo do canal prioritário e anota; marca feito."""
    d = prioridades()
    concluidas = []
    medidas = {}
    if medir.MEDIDAS.exists():
        for ln in medir.MEDIDAS.read_text(encoding="utf-8").splitlines():
            try:
                m = json.loads(ln)
                medidas.setdefault(m.get("parceiro"), []).append(m)
            except ValueError:
                pass
    for it in [x for x in d["itens"] if x.get("estado") == "medindo"]:
        nome = "prioridade_" + _nome(it["alvo"])
        ms = [m for m in medidas.get(nome, []) if not m.get("erro")]
        if not ms:
            continue
        linhas = [f"## {datetime.now():%d/%m %H:%M} — prioridade {it['tipo']}: {it['alvo']} ({len(ms)} vídeo(s) medido(s))"]
        if it["tipo"] == "canal":
            top = [m for m in ms if m.get("grupo") == "top"]
            bx = [m for m in ms if m.get("grupo") == "baixo"]
            linhas.append("| medida | top (mais vistos) | baixo (menos vistos) | diferença |")
            linhas.append("|---|---|---|---|")
            for k in CAMPOS:
                a = [m[k] for m in top if m.get(k) is not None]
                b = [m[k] for m in bx if m.get(k) is not None]
                if a and b:
                    ma, mb = statistics.median(a), statistics.median(b)
                    linhas.append(f"| {k} | {ma:.2f} | {mb:.2f} | {ma - mb:+.2f} |")
            vt = [m.get("views_lista") or 0 for m in top]
            vb = [m.get("views_lista") or 0 for m in bx]
            linhas.append(f"\nviews: top {statistics.median(vt) if vt else 0:.0f} × baixo {statistics.median(vb) if vb else 0:.0f}. "
                          "Regra D1: o que separa é assistir inteiro (duração curta, 1º corte cedo, sem silêncio inicial).")
        else:
            m = ms[0]
            linhas.append("| " + " | ".join(CAMPOS) + " |")
            linhas.append("|" + "---|" * len(CAMPOS))
            linhas.append("| " + " | ".join(f"{m.get(k)}" for k in CAMPOS) + " |")
        _anotar("\n".join(linhas))
        it["estado"] = "feito"
        it["feito_em"] = datetime.now().isoformat(timespec="seconds")
        log(f"prioridade concluída: {it['alvo']}")
        concluidas.append(it)
    _salvar_prioridades(d)
    return concluidas


# ───────── vídeo base (fonte do Cortes) ─────────
def medir_fontes(max_n=4, simular=False):  # 4 × ~5 min com a CPU cheia: a passada de 2 h não engole a seguinte
    """source.mp4 novos do Cortes ganham fonte_medidas.json; 1 linha em medidas_fontes.jsonl."""
    ultima = {}  # pasta -> última linha (a nova tentativa vem depois da que deu erro)
    if FONTES.exists():
        for ln in FONTES.read_text(encoding="utf-8").splitlines():
            try:
                x = json.loads(ln)
                ultima[x["pasta"]] = x
            except (ValueError, KeyError):
                pass

    def refazer(x):
        # 30/10: as que estouraram o tempo medindo a fonte INTEIRA ganham 1 nova chance com a janela
        return "TimeoutExpired" in str(x.get("erro") or "") and not x.get("tentativa_janela")

    n = 0
    lim = time.time() - 48 * 3600
    for src in sorted(WORK_CORTES.glob("*/source.mp4"), key=lambda p: -p.stat().st_mtime):
        pasta = src.parent
        ant = ultima.get(str(pasta))
        if (ant and not refazer(ant)) or src.stat().st_mtime < lim:
            continue
        if not ant and (pasta / "fonte_medidas.json").exists():
            continue
        if n >= max_n:
            break
        if simular:
            log(f"  [simular] mediria fonte {pasta.name}{' (de novo, com janela)' if ant else ''}")
            n += 1
            continue
        base = {"pasta": str(pasta), "id": pasta.name, "em": datetime.now().isoformat(timespec="seconds"),
                "tentativa_janela": True}
        try:
            m = {**base, **medir.medir(src, janela=JANELA_FONTE_S)}
        except Exception as e:  # noqa: BLE001
            m = {**base, "erro": f"{type(e).__name__}: {e}"}
        (pasta / "fonte_medidas.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        with FONTES.open("a", encoding="utf-8") as f:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
        n += 1
    log(f"fontes medidas nesta passada: {n}")
    return n


def _rodar(script, *args, timeout=3600):
    try:
        r = subprocess.run([PY, "-X", "utf8", str(AQUI / script), *args], cwd=str(AQUI), capture_output=True, text=True,
                           errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:  # 30/10: antes derrubava a passada inteira (sem concluir prioridades nem aviso)
        log(f"{script} passou de {timeout // 60} min — interrompido; a passada segue")
        return -1
    cauda = (r.stdout or "").strip().splitlines()[-3:]
    if r.returncode:  # com erro, o que explica está no stderr (traceback), que antes nunca ia para o log
        cauda += (r.stderr or "").strip().splitlines()[-2:]
    log(f"{script} rc={r.returncode} | " + " | ".join(x[:100] for x in cauda))
    return r.returncode


def main(a):
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true")
    ap.add_argument("--max", type=int, default=6, help="downloads de prioridade nesta passada")
    ap.add_argument("--n", type=int, default=3, help="top N e baixo N por canal prioritário")
    args = ap.parse_args(a)
    log(f"passada {'(simular) ' if args.simular else ''}| D livre {livre_gb():.1f} GB | prioridades abertas "
        f"{sum(1 for i in prioridades()['itens'] if i.get('estado') == 'aberto')}")
    # 30/10 (D41): esta passada levou a checagem de robô do YouTube 2× na madrugada (07:40 e 09:13) e cada uma pausou o
    # yt-dlp do PC INTEIRO por 120 min — os Shorts (PC1/PC2) ficaram sem fonte. Bloqueio causado pela ER há menos de
    # 12 h = esta passada não baixa nada (mede e conclui o que já tem); a produção fica com o IP.
    # 30/10: amostra.bloqueio_recente também lê a marca própria (bloqueio_er.json): a pausa global é sobrescrita pelo
    # próximo projeto bloqueado, e a amostra antes pausava sem "engenharia reversa" no motivo — o D41 nunca a via.
    if amostra.bloqueio_recente():
        log(f"não baixa nesta passada: a ER causou bloqueio do YouTube há menos de {amostra.HORAS_SEM_BAIXAR} h (D41) — só mede")
        args.max = 0
        sem_download = True
    else:
        sem_download = False
    baixados = atender_prioridades(args.n, args.max, args.simular) if not sem_download else 0
    fontes = medir_fontes(simular=args.simular)
    if args.simular:
        return
    if not sem_download and baixados == 0 and not any(i.get("estado") == "aberto" for i in prioridades()["itens"]) \
            and livre_gb() >= MIN_LIVRE_GB:
        _rodar("amostra.py", "--n", "2", "--max", "4", "--pausa", "120")  # fundo: parceiros que mais viram Shorts nossos
    _rodar("medir.py")
    feitos = concluir_prioridades()
    _rodar("medir_nossos.py", timeout=5400)
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        # 30/10: só as concluídas NESTA passada (antes repetia no Telegram, a cada 2 h, todas as concluídas do dia)
        if baixados or fontes or feitos:
            avisos.enviar(f"🔬 Engenharia reversa: {baixados} amostra(s) baixada(s), {fontes} fonte(s) do Cortes medida(s)"
                          + (f", prioridades concluídas: {', '.join(i['alvo'][-40:] for i in feitos)}" if feitos else ""),
                          origem="engenharia_reversa")
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
