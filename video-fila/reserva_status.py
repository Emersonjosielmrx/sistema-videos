"""reserva_status.py — dias de RESERVA por canal (dona 02/11: "1 semana de vídeos guardada em todo projeto").

Reserva = (agendados no YouTube pelo ledger do postador + prontos não subidos) ÷ o que o canal GASTA por dia (média de
publicações dos últimos 3 dias, entre 1 e o teto). Meta 7 dias.
Fora da meta (dona): hipercool e historias (parados); exceções documentadas: Veo e longos (ver MELHORIAS 02/11).

    python reserva_status.py          # tabela por canal, do mais vazio pro mais cheio
    python reserva_status.py resumo   # 1 linha: quantos canais na meta
"""
import glob
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(r"D:\postador-de-videos\bin")
import politica as pol  # noqa: E402

META_DIAS = 7
FORA = {"hipercool"}  # dono do canal fora da meta (parado)


def medir():
    agora = datetime.now(timezone.utc)
    led = pol._ler_ledger()
    subidos = {str(r.get("caminho") or "").casefold() for r in led}
    cad = json.loads(Path(r"D:\postador-de-videos\config\canais.json").read_text(encoding="utf-8"))["canais"]
    cred2slug = {c: k for k, v in cad.items() for c in v.get("creds") or []}
    agendados = defaultdict(int)
    publicados_3d = defaultdict(int)  # 02/11: consumo REAL (média de publicações/dia em 3 dias), não o teto
    for r in led:
        try:
            q = datetime.fromisoformat(str(r.get("publish_at") or r.get("ts")).replace("Z", "+00:00"))
            slug = cred2slug.get(r.get("canal_id"), r.get("canal_id"))
            if q > agora:
                agendados[slug] += 1
            elif (agora - q).total_seconds() <= 3 * 86400:
                publicados_3d[slug] += 1
        except (ValueError, TypeError):
            pass
    prontos = defaultdict(lambda: defaultdict(int))
    for pj in glob.glob(r"D:\hipercool-materiais\animes recap\shorts\*\postar.json"):
        try:
            d = json.loads(Path(pj).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not d.get("pronto") or str(d.get("revisao", "")).startswith("segurado"):
            continue
        pasta = Path(pj).parent
        vids = [pasta / x for x in (d.get("arquivo"), "video_1080p.mp4", "video.mp4") if x]
        if any(str(v).casefold() in subidos for v in vids) or not (any(v.exists() for v in vids) or d.get("drive")):
            continue
        prontos[cred2slug.get(d.get("canal"), d.get("canal"))]["parceiro"] += 1
    for pj in glob.glob(r"D:\hipercool-materiais\manhwa-react\*\*\*.postar.json"):
        mp4 = Path(pj[: -len(".postar.json")] + ".mp4")
        if mp4.exists() and str(mp4).casefold() not in subidos:
            prontos[Path(pj).parent.name]["manhwa-react"] += 1
    for pj in glob.glob(r"D:\hipercool-materiais\videos-comentarios\*\postar.json"):
        if not json.loads(Path(pj).read_text(encoding="utf-8")).get("postado"):
            prontos["comedianoturna"]["comentarios"] += 1
    linhas = []
    for slug, v in cad.items():
        if v.get("dono") in FORA:
            continue
        c, _ = pol.achar_canal((v.get("creds") or [slug])[0])
        try:
            teto = pol.teto_canal(c, pol.politica()) if c else (v.get("max_dia") or 3)
        except Exception:  # noqa: BLE001
            teto = v.get("max_dia") or 3
        teto = teto or 3
        # o que o canal gasta por dia de verdade; piso 3/dia (regra BR "3 por dia": canal novo ainda sem histórico)
        consumo = min(teto, max(3.0, publicados_3d.get(slug, 0) / 3))
        ag, pr = agendados.get(slug, 0), sum(prontos.get(slug, {}).values())
        linhas.append({"dias": round((ag + pr) / consumo, 1), "canal": slug, "dono": v.get("dono"), "teto": teto,
                       "consumo": round(consumo, 1),
                       "agendados": ag, "prontos": pr, "por_projeto": dict(prontos.get(slug, {}))})
    return sorted(linhas, key=lambda x: x["dias"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ls = medir()
    na_meta = sum(1 for l in ls if l["dias"] >= META_DIAS)
    print(f"{na_meta}/{len(ls)} canais com >= {META_DIAS} dias de reserva (hipercool fora)")
    if len(sys.argv) < 2 or sys.argv[1] != "resumo":
        for l in ls:
            print(f"{l['dias']:5.1f} dias  {l['canal']:24s} dono={str(l['dono']):13s} gasta={l['consumo']}/dia  "
                  f"agendados={l['agendados']:3d}  prontos={l['prontos']:3d} {l['por_projeto']}")
