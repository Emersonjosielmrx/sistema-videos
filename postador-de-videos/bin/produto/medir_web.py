"""produto/medir_web.py — views/curtidas/comentários dos Reels de produto SEM a API do Instagram (tokens venceram) e
sem abrir Chrome a cada vez: leitura GraphQL pelo cofre (projeto-navegador-sem-navegador, InstagramWeb.reels), 1 chamada
por conta. Fable 29/10 (PRODUTOS item 1 — ver FABLE_DECISOES.md D9).

Liga cada Reel ao `.json` em D:\\video-fila\\produto_fila\\<conta>\\_postados\\ pela legenda (60 primeiros caracteres)
e pela hora (|taken_at − postado_em| < 36 h). Grava:
  - no placar das variações (config\\produto_variacoes.json, chave "ig:<codigo>", campo views = o que o contagem usa);
  - no próprio .json do vídeo: "medidas": {instagram: {views, curtidas, comentarios, codigo, medido}}.
Só mede vídeo com ≥ 48 h de postado; remede a cada 24 h até 14 dias. Para no 1º erro HTTP 4xx (429 = pausa 24 h).

    python -m produto.medir_web            # todas as contas com _postados
    python -m produto.medir_web <conta>    # só uma
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — regra da dona: nenhum processo filho abre janela na tela
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

BIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
from produto import variacoes  # noqa: E402

NSN = Path(r"D:\projeto-navegador-sem-navegador")
PAUSA = variacoes.RAIZ / "config" / "produto_medir_web_pausa.txt"
ESPERA_ENTRE_CONTAS_S = 25  # dona: nada de rajada; 7 contas = ~3 min


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return padrao


def _pausado():
    try:
        return time.time() < float(PAUSA.read_text().strip() or 0)
    except (OSError, ValueError):
        return False


def _pendentes(conta, placar):
    """[.json de vídeos postados ≥ 48 h] que nunca foram medidos ou cuja medida tem > 24 h (até 14 dias de idade)."""
    out = []
    for arq in sorted((variacoes.FILA / conta / "_postados").glob("*.json")):
        side = _ler(arq, {})
        try:
            quando = datetime.fromisoformat(side.get("postado_em") or "")
        except ValueError:
            continue
        idade = datetime.now() - quando
        if idade < timedelta(hours=48) or idade > timedelta(days=14):
            continue
        m = (side.get("medidas") or {}).get("instagram") or {}
        try:
            fresco = datetime.now() - datetime.fromisoformat(m.get("medido") or "") < timedelta(hours=24)
        except ValueError:
            fresco = False
        if not fresco:
            out.append((arq, side, quando))
    return out


def _casa(side, quando, reels):
    """O Reel do vídeo: o feed não traz legenda, e a conta posta vários Reels por noite (29/10: 3 em 15 min), então
    vale a HORA — o postador grava postado_em no instante do envio e o Reel aparece 1–3 min depois (medido: 18:23:06 →
    18:24; 20:32:57 → 20:35). Pega o mais próximo publicado entre 0 e 20 min depois; legenda igual, se vier, confirma."""
    t = (side.get("legenda") or side.get("titulo") or "").lower()[:40]
    cands = []
    for r in reels:
        if not r.get("quando"):
            continue
        dt = (datetime.fromtimestamp(int(r["quando"])) - quando).total_seconds()
        if -120 <= dt <= 20 * 60:
            cands.append((0 if t and t in (r.get("legenda") or "").lower() else 1, abs(dt), r))
    return min(cands, key=lambda c: c[:2])[2] if cands else None


VEO_PY = Path(r"D:\veo\venv\Scripts\python.exe")  # tem curl_cffi (TLS igual ao Chrome, que o Instagram exige)


def _reels_views(ig, paginas=4):
    """{codigo: {views, curtidas, comentarios}} da aba Reels, PAGINANDO: o servidor fixa 12 por página (page_size=50 é
    ignorado, medido 29/10) e dá end_cursor/has_next_page; contas de produto postam ~5 Reels por noite, então 12 não
    cobrem 48 h. Para quando repete ou acaba."""
    m = ig.modelos["PolarisProfileReelsTabContentQuery"]
    out, cursor = {}, None
    for _ in range(paginas):
        v = ig._variaveis(m, target_user_id=ig.uid, user_id=ig.uid)
        if cursor:
            v["after"] = cursor
            if isinstance(v.get("data"), dict):
                v["data"]["after"] = cursor
        d = ig.graphql("PolarisProfileReelsTabContentQuery", v)
        conn = next((x.get("clips_connection") for x in d.values() if isinstance(x, dict) and "clips_connection" in x),
                    None) or next((x for x in d.values() if isinstance(x, dict) and "edges" in x), {})
        antes = len(out)
        for e in conn.get("edges", []):
            md = e.get("node", {}).get("media", {})
            if md.get("code"):
                out[md["code"]] = {"views": md.get("play_count") if md.get("play_count") is not None else md.get("view_count"),
                                   "curtidas": md.get("like_count"), "comentarios": md.get("comment_count")}
        pi = conn.get("page_info") or {}
        if len(out) == antes or not pi.get("has_next_page") or not pi.get("end_cursor"):
            break
        cursor = pi["end_cursor"]
        time.sleep(3)
    return out


def medir(placar=None, log=print, so=None):
    if _pausado():
        log("[medir_web] em pausa (erro HTTP recente); pulo")
        return placar
    try:
        import curl_cffi  # noqa: F401
    except ImportError:
        # o Python de quem chamou (postador/sistema) não tem o curl_cffi: roda por fora no venv do Veo, que tem
        import os
        import subprocess
        if os.environ.get("MEDIR_WEB_FILHO") == "1" or not VEO_PY.exists():
            log("[medir_web] sem curl_cffi neste Python e sem o venv do Veo: pulo")
            return placar
        log(f"[medir_web] sem curl_cffi aqui: rodando por {VEO_PY}")
        r = subprocess.run([str(VEO_PY), "-m", "produto.medir_web", *([so] if so else [])], cwd=str(BIN),
                           capture_output=True, text=True, errors="replace", timeout=1800,
                           env={**os.environ, "MEDIR_WEB_FILHO": "1", "PYTHONUTF8": "1"}, creationflags=0x08000000)
        for ln in (r.stdout + r.stderr).strip().splitlines()[-12:]:
            log(ln)
        return _ler(variacoes.PLACAR, placar if placar is not None else {"videos": {}})
    if str(NSN) not in sys.path:
        sys.path.insert(0, str(NSN))
    from services.instagram.web import InstagramWeb
    placar = placar if placar is not None else _ler(variacoes.PLACAR, {"videos": {}})
    placar.setdefault("videos", {})
    contas = [so] if so else sorted(p.name for p in variacoes.FILA.iterdir() if (p / "_postados").is_dir())
    novos, primeira = 0, True
    for conta in contas:
        pend = _pendentes(conta, placar)
        if not pend:
            continue
        if not primeira:
            time.sleep(ESPERA_ENTRE_CONTAS_S)
        primeira = False
        try:
            ig = InstagramWeb(conta, perfil_cofre=f"ig_{conta}")
            # a aba Reels dá views por código mas sem data/legenda; o feed dá data/legenda/curtidas sem views: junta
            views = _reels_views(ig)
            time.sleep(3)
            reels = []
            for p in ig.posts(quantos=24):
                v = views.get(p.get("codigo"))
                if v is not None or p.get("tipo") == "reel":
                    reels.append({**p, "views": (v or {}).get("views"),
                                  "curtidas": p.get("curtidas") if p.get("curtidas") is not None else (v or {}).get("curtidas")})
        except Exception as e:  # noqa: BLE001
            msg = f"{type(e).__name__}: {str(e)[:140]}"
            log(f"[medir_web] {conta}: falhou ({msg})")
            if "429" in msg or "403" in msg or "401" in msg:
                try:
                    PAUSA.write_text(str(time.time() + 24 * 3600))
                except OSError:
                    pass
                log("[medir_web] erro HTTP do Instagram: pausa de 24 h (não arriscar a conta)")
                break
            continue
        for arq, side, quando in pend:
            r = _casa(side, quando, reels)
            if not r or r.get("views") is None:
                log(f"[medir_web] {conta}: {arq.name} sem Reel correspondente nos 24 últimos")
                continue
            agora = datetime.now().isoformat(timespec="minutes")
            chave = f"ig:{r.get('codigo') or r.get('id')}"
            placar["videos"][chave] = {"conta": conta, "arquivo": arq.with_suffix(".mp4").name,
                                       "variante": variacoes.variante_real(side), "views": int(r["views"]),
                                       "curtidas": r.get("curtidas"), "comentarios": r.get("comentarios"),
                                       "plataforma": "instagram", "medido": agora}
            side.setdefault("medidas", {})["instagram"] = {"views": int(r["views"]), "curtidas": r.get("curtidas"),
                                                           "comentarios": r.get("comentarios"), "codigo": r.get("codigo"),
                                                           "medido": agora}
            try:
                arq.write_text(json.dumps(side, ensure_ascii=False, indent=1), "utf-8")
            except OSError:
                pass
            novos += 1
            log(f"[medir_web] {conta}: {arq.name} -> {r['views']} views, {r.get('curtidas')} curtidas "
                f"({side.get('variante')} / real {variacoes.variante_real(side)})")
    variacoes.PLACAR.write_text(json.dumps(placar, ensure_ascii=False, indent=1), "utf-8")
    log(f"[medir_web] {novos} medida(s) nova(s) | no placar: {len(placar['videos'])}")
    return placar


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    medir(so=sys.argv[1] if len(sys.argv) > 1 else None)
