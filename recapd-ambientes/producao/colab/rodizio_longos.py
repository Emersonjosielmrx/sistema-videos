r"""rodizio_longos.py — dá uma 2ª/3ª chance aos LONGOS que vão mal: troca capa e título (dona 15/11: "sim, principalmente
nos que estão indo mal; regras: até 3x, quantidade mínima de dias etc.").

Regras (todas com chave):
  - longo postado há >= RODIZIO_DIAS_MIN (3) dias, views < mediana dos longos do MESMO canal (views_longos.json);
  - no máximo RODIZIO_MAX (3) trocas por vídeo, com >= RODIZIO_INTERVALO_DIAS (3) entre elas;
  - nunca a série da dona (título "PARTE n" de playlist de saga) nem vídeo acima da mediana;
  - 1 vídeo por rodada (capa nova = ~40 min de Flow); o pior (views/dia) primeiro.
Troca: capa = próxima variante (capa_b, capa_c do teste A/B, geradas por capa_ia_anime.capas_ab se faltarem);
título = novo pelo LLM (gemini_llm) a partir do roteiro, sem nome da obra; o antigo fica em rodizio_longos.json pra
comparar views antes/depois. Aplica pelo youtube_studio_extras (Chrome do cofre do canal, YT_MAQUINA=desktop).
RODIZIO_LONGOS=0 desliga.   python rodizio_longos.py [--ver]
"""
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BIN = AQUI.parent / "bin"
EST = AQUI / "rodizio_longos.json"
LOG = AQUI / "rodizio_longos.log"
STUDIO = Path(r"D:\postador-de-videos\bin\youtube_studio_extras.py")
DIAS_MIN = int(os.environ.get("RODIZIO_DIAS_MIN", "3"))
MAX = int(os.environ.get("RODIZIO_MAX", "3"))
INTERVALO = int(os.environ.get("RODIZIO_INTERVALO_DIAS", "3"))


def log(t):
    linha = f"[{datetime.now():%d/%m %H:%M}] {t}"
    print(linha, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _j(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def candidatos():
    views = _j(AQUI / "views_longos.json", {})
    postados = {(x.get("url") or "").rsplit("/", 1)[-1]: x for x in _j(AQUI / "longos_postados.json", {}).get("postados", [])}
    capas = {i.get("vid"): i for i in _j(AQUI / "capas_depois.json", []) if isinstance(i, dict)}
    est = _j(EST, {})
    por_canal = {}
    for x in views.values():
        por_canal.setdefault(x.get("canal"), []).append(x.get("views") or 0)
    med = {c: statistics.median(v) for c, v in por_canal.items()}
    agora = datetime.now()
    out = []
    for vid, x in views.items():
        try:
            dias = (agora - datetime.fromisoformat(str(x.get("postado", ""))[:16])).total_seconds() / 86400
        except ValueError:
            continue
        p, h = postados.get(vid) or {}, est.get(vid) or {}
        vw = x.get("views") or 0
        if dias < DIAS_MIN or vw >= med.get(x.get("canal"), 0) or vid not in capas:
            continue
        if re.match(r"\s*PARTE\s+\d+", p.get("titulo") or "") or re.match(r"^[\w-]{11}_\d{1,2}_+[A-Za-z]",
                                                                             p.get("nome") or ""):
            continue  # série da dona (Medieval, vilão/maid...): capa e título próprios, nunca rodízio
        trocas = h.get("trocas", [])
        if len(trocas) >= MAX:
            continue
        if trocas and (agora - datetime.fromisoformat(trocas[-1]["em"])).total_seconds() < INTERVALO * 86400:
            continue
        out.append((vw / dias, vid, x, p, capas[vid], med[x.get("canal")]))
    return sorted(out, key=lambda t: t[0])


def _capa_nova(item, ja_usadas):
    sys.path.insert(0, str(BIN))
    os.chdir(BIN)
    import capa_ia_anime
    pasta, prm = Path(item["pasta"]), item.get("params") or {}
    cands = [pasta / f"capa_{l}.jpg" for l in "bcd"]
    livres = [c for c in cands if c.exists() and c.name not in ja_usadas]
    if livres:
        return livres[0]
    if prm.get("source_url"):
        try:
            extras = capa_ia_anime.capas_ab(prm["source_url"], str(pasta / "capa.jpg"), prm.get("texto", ""),
                                            prm.get("cena", ""), prm.get("generos")) or []
            livres = [Path(x) for x in extras if Path(x).exists() and Path(x).name not in ja_usadas]
        except Exception as e:  # noqa: BLE001
            log(f"  capas_ab falhou: {type(e).__name__}: {str(e)[:120]}")
    return livres[0] if livres else None


def _titulo_novo(p, antigo):
    sys.path.insert(0, str(BIN))
    try:
        import gemini_llm
    except ImportError:
        return None
    pasta = Path(r"D:\hipercool-materiais\animes recap\videos laterais") / (p.get("nome") or "")
    resumo = ""
    for nome in ("roteiro.txt", "roteiro_longo.txt"):
        if (pasta / nome).exists():
            resumo = "\n".join((pasta / nome).read_text(encoding="utf-8", errors="replace").splitlines()[:20])
            break
    prompt = (f"Título atual de um vídeo longo de recap de manhwa/anime no YouTube (vai mal de views): \"{antigo}\".\n"
              f"Resumo do começo da história:\n{resumo[:1500]}\n\n"
              "Escreva UM título NOVO em português do Brasil, bem diferente do atual: provocação + palavras que as pessoas "
              "buscam, CAIXA ALTA nas palavras-chave, até 95 caracteres, SEM o nome da obra e SEM nome próprio de "
              "personagem, sem emoji no começo. Responda só o título.")
    try:
        linhas = [x.strip().strip('"') for x in (gemini_llm.generate_text(prompt, max_tokens=200, temperature=0.9) or "")
                  .splitlines() if x.strip()]
        t = linhas[0] if linhas else ""
    except Exception as e:  # noqa: BLE001
        log(f"  título pelo LLM falhou: {type(e).__name__}")
        return None
    return t[:100] if len(t) > 15 and t.lower() != antigo.lower() else None


_MAQ = None


def _maquina():
    """25/11: o rodízio ia SEMPRE pelo desktop (o MacBook, sendo formatado/offline) e falhava. Desktop sem ssh em 8 s =
    STI (o mais rápido logado nos canais). RODIZIO_MAQUINA força uma máquina."""
    global _MAQ
    if os.environ.get("RODIZIO_MAQUINA"):
        return os.environ["RODIZIO_MAQUINA"]
    if _MAQ is None:
        try:
            r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "desktop", "echo ok"],
                               capture_output=True, text=True, timeout=15)
            _MAQ = "desktop" if "ok" in r.stdout else "sti"
        except Exception:  # noqa: BLE001
            _MAQ = "sti"
    return _MAQ


def _studio(canal, *args):
    env = {**os.environ, "YT_MAQUINA": _maquina()}
    try:
        r = subprocess.run([sys.executable, str(STUDIO), "--canal", canal, *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900, env=env)
    except subprocess.TimeoutExpired:  # 15/11 (ForjaReact RDz52e9a_p0): Studio > 15 min derrubava a rodada sem registro
        return "aviso: Studio passou de 15 min"
    m = re.search(r"^RESULTADO: (\{.*\})\s*$", r.stdout or "", re.M)
    return m.group(1) if m else (r.stderr or r.stdout or "")[-200:]


def main(ver):
    if os.environ.get("RODIZIO_LONGOS", "1") == "0":
        return
    cands = candidatos()
    log(f"{len(cands)} longo(s) fracos elegíveis (>= {DIAS_MIN} dias, abaixo da mediana do canal, < {MAX} trocas)")
    if ver:
        for vd, vid, x, p, _, med in cands:
            log(f"  {vid} {x.get('canal')}: {x.get('views')} views ({vd:.1f}/dia; mediana do canal {med:.0f}) — {(p.get('titulo') or '')[:60]}")
        return
    if not cands:
        return
    _, vid, x, p, item, med = cands[0]
    est = _j(EST, {})
    h = est.setdefault(vid, {"trocas": [], "views_inicio": x.get("views")})
    usadas = {t.get("capa") for t in h["trocas"]} | {"capa.jpg"}
    capa = _capa_nova(item, usadas)
    antigo = p.get("titulo") or ""
    titulo = _titulo_novo(p, antigo)
    if not capa and not titulo:
        log(f"{vid}: sem capa nova nem título novo — fica pra próxima")
        return
    res_c = _studio(item["canal"], "--video", vid, "--capa", str(capa)) if capa else "sem capa nova"
    if capa and "Studio passou" in res_c:  # capa pronta e o Studio lento: não conta troca, a próxima rodada reaproveita
        log(f"{vid}: {res_c} — capa {capa.name} pronta, tenta de novo na próxima rodada")
        return
    res_t = "sem título novo"
    if titulo:
        arq = Path(tempfile.gettempdir()) / f"rodizio_{vid}.json"
        arq.write_text(json.dumps([{"video": vid, "titulo": titulo, "descricao": None, "tags": None}], ensure_ascii=False),
                       encoding="utf-8")
        res_t = _studio(item["canal"], "--metadados", str(arq))
    h["trocas"].append({"em": datetime.now().isoformat(timespec="minutes"), "views_antes": x.get("views"),
                        "capa": capa.name if capa else None, "titulo_antigo": antigo, "titulo_novo": titulo,
                        "res_capa": res_c[:160], "res_titulo": res_t[:160]})
    EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"{vid} ({x.get('canal')}, {x.get('views')} views, mediana {med:.0f}): troca {len(h['trocas'])}/{MAX} — "
        f"capa {capa.name if capa else '-'}: {res_c[:80]} | título \"{titulo}\": {res_t[:80]}")


if __name__ == "__main__":
    main("--ver" in sys.argv)
