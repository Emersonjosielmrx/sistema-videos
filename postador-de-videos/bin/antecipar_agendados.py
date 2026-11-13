"""antecipar_agendados.py — dona 30/10: "pra que não poste um vídeo enquanto o anterior ainda está sendo veiculado (aí
corta as visualizações do anterior e eles dividem as mesmas views); se um vídeo parar de receber views, muda o próximo
programado da fila pra público — mantendo a fila e aproveitando o máximo do algoritmo pra cada vídeo".

Para cada canal com vídeo AGENDADO (ledger com publish_at no futuro):
  - o canal ESTAGNOU (rampa_canais._ganhos_6h: últimas 6 h < 25% do ganho médio de 6 h, média >= 30 views/6 h) E
  - o último vídeo que abriu no canal abriu há >= 6 h (não briga com um vídeo que acabou de sair)
  -> o PRÓXIMO agendado do canal vira público agora (youtube_studio_extras --visibilidade public: confere recarregando).
Máx. 1 por canal a cada 12 h e MAX_POR_RODADA por rodada. Registro em config\\antecipados.json, log em
logs\\antecipar_agendados.log, Telegram (avisos). Nada de upload novo: só adianta o que já passou pela checagem do
YouTube (o agendado já foi conferido quanto a direitos).

    python bin\\antecipar_agendados.py --ensaio   # só mostra o que faria
    python bin\\antecipar_agendados.py            # faz (tarefa AnteciparAgendados, 3 em 3 h)
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import politica  # noqa: E402
import rampa_canais  # noqa: E402

ESTADO = politica.CONFIG_DIR / "antecipados.json"
LOG = BIN.parent / "logs" / "antecipar_agendados.log"
HORAS_DESDE_ULTIMO = 6
HORAS_ENTRE = 12
MAX_POR_RODADA = 4
PY = r"D:\veo\venv\Scripts\python.exe"


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M}] {m}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def _ledger():
    out = []
    try:
        for ln in politica.LEDGER_FILE.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
    except OSError:
        pass
    return out


HIST_HTTP = BIN.parent / "logs" / "historico_views_http.jsonl"


def coletar_http(slugs):
    """30/10: o painel (Data API) só acompanha 19 canais; os Noturno/Inovare de outras línguas não têm histórico.
    Soma das views dos vídeos de 28 dias pelo Studio HTTP (metricas_rede._studio_http, sem Chrome) -> 1 linha por
    canal, no máx. 1 a cada 2,5 h. Só os canais que têm agendado e não estão no histórico do painel."""
    import metricas_rede
    ultimas = {}
    try:
        for ln in HIST_HTTP.read_text(encoding="utf-8").splitlines()[-3000:]:
            r = json.loads(ln)
            ultimas[r["slug"]] = r["ts"]
    except (OSError, ValueError):
        pass
    for slug in slugs:
        t = politica._dt(ultimas.get(slug))
        if t and (politica.agora() - t).total_seconds() < 2.5 * 3600:
            continue
        v = metricas_rede._studio_http(slug)
        if not v:
            continue
        with open(HIST_HTTP, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": politica.agora().isoformat(timespec="seconds"), "slug": slug,
                                "views": sum(int(x.get("views") or 0) for x in v.values())}) + "\n")


def _ganhos(slug):
    """(ganho 6 h, média por 6 h) — histórico do painel se houver; senão o do Studio HTTP (mesma conta)."""
    g = rampa_canais._ganhos_6h(slug)
    if g is not None:
        return g
    antes = rampa_canais.HISTORICO
    try:
        rampa_canais.HISTORICO = HIST_HTTP
        return rampa_canais._ganhos_6h(slug)
    finally:
        rampa_canais.HISTORICO = antes


def _slug(cred, cad):
    return next((k for k, x in cad.items() if isinstance(x, dict) and cred in (x.get("creds") or [])), None)


def planejar():
    agora = politica.agora()
    est = politica.ler_json(ESTADO, {"antecipados": {}})
    feitos = est.get("antecipados") or {}
    cad = (politica.ler_json(politica.CONFIG_DIR / "canais.json", {}).get("canais") or {})
    por_canal = {}
    for r in _ledger():
        if r.get("video_id") and r.get("canal_id"):
            por_canal.setdefault(r["canal_id"], []).append(r)
    planos = []
    for cred, regs in por_canal.items():
        futuros = sorted((r for r in regs if politica._dt(r.get("publish_at")) and politica._dt(r["publish_at"]) >
                          agora + timedelta(minutes=30) and r["video_id"] not in feitos),
                         key=lambda r: politica._dt(r["publish_at"]))
        if not futuros:
            continue
        abertos = [politica._dt(r.get("publish_at")) or politica._dt(r.get("ts")) for r in regs]
        abertos = [t for t in abertos if t and t <= agora]
        ultimo = max(abertos) if abertos else None
        if ultimo and (agora - ultimo).total_seconds() < HORAS_DESDE_ULTIMO * 3600:
            continue
        ult_ant = max((politica._dt(x["em"]) for x in feitos.values() if x.get("canal") == cred and x.get("em")),
                      default=None)
        if ult_ant and (agora - ult_ant).total_seconds() < HORAS_ENTRE * 3600:
            continue
        slug = _slug(cred, cad)
        g = _ganhos(slug) if slug else None
        if not g or g[1] < 30 or g[0] >= 0.25 * g[1]:
            continue
        prox = futuros[0]
        planos.append({"cred": cred, "slug": slug, "video": prox["video_id"], "publish_at": prox["publish_at"],
                       "projeto": prox.get("projeto"), "motivo": f"últimas 6 h +{g[0]} views x média {g[1]:.0f}/6 h; "
                       f"último vídeo abriu {ultimo:%d/%m %H:%M}" if ultimo else f"+{g[0]} x {g[1]:.0f}/6 h"})
    return planos[:MAX_POR_RODADA]


def main(ensaio=False):
    # 1º: histórico HTTP dos canais com agendado que o painel não acompanha
    try:
        agora = politica.agora()
        cad = (politica.ler_json(politica.CONFIG_DIR / "canais.json", {}).get("canais") or {})
        com_agendado = {_slug(r["canal_id"], cad) for r in _ledger() if r.get("canal_id")
                        and politica._dt(r.get("publish_at")) and politica._dt(r["publish_at"]) > agora}
        sem_hist = [s for s in com_agendado if s and rampa_canais._ganhos_6h(s) is None]
        coletar_http(sem_hist)
        log(f"histórico HTTP: {len(sem_hist)} canal(is) com agendado e sem histórico do painel")
    except Exception as e:  # noqa: BLE001
        log(f"histórico HTTP falhou ({type(e).__name__}: {str(e)[:100]})")
    planos = planejar()
    if not planos:
        log("nenhum canal estagnado com agendado na fila — nada a adiantar")
        return
    est = politica.ler_json(ESTADO, {"antecipados": {}})
    for p in planos:
        log(f"{'ENSAIO ' if ensaio else ''}{p['slug']}: {p['motivo']} -> {p['video']} (era {p['publish_at'][:16]}) vira público")
        if ensaio:
            continue
        r = subprocess.run([PY, "-X", "utf8", str(BIN / "youtube_studio_extras.py"), "--canal", p["cred"], "--video",
                            p["video"], "--visibilidade", "public"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900, cwd=str(BIN.parent))
        ok = '"ok"' in (r.stdout or "") or "'ok'" in (r.stdout or "") or "ja" in (r.stdout or "")[-200:]
        log(f"  {p['video']}: {'ok' if ok else 'falhou: ' + (r.stdout + r.stderr).strip()[-200:]}")
        if ok:
            est.setdefault("antecipados", {})[p["video"]] = {"canal": p["cred"], "slug": p["slug"],
                                                            "em": politica.agora().isoformat(timespec="seconds"),
                                                            "era": p["publish_at"], "motivo": p["motivo"]}
            politica.gravar_json(ESTADO, est)
            try:
                sys.path.insert(0, r"D:\video-fila")
                import avisos
                avisos.enviar(f"⏩ {p['slug']}: o último vídeo parou de receber views ({p['motivo']}) — adiantei o "
                              f"agendado https://youtu.be/{p['video']} pra público agora.", "postagem", importante=False)
            except Exception:  # noqa: BLE001
                pass


if __name__ == "__main__":
    main(ensaio="--ensaio" in sys.argv)
