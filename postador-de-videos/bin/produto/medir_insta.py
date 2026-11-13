"""Views dos Reels de produto PELO NAVEGADOR (28/10).

Todo vídeo de produto é postado pelo Chrome (media_id "navegador") e os tokens da API venceram (24/10) -> o placar das
variações (variacoes.medir) nunca recebeu um vídeo e o agente escolhia o formato às cegas. Aqui: UMA sessão de
Instagram já logada (maquina_remota.tentativas: notebooks -> PC2 -> desktop -> PC1 por último) lê, pela API interna
do site (a mesma que a página usa), os reels de cada conta de produto com o play_count. Os perfis são públicos:
qualquer conta logada serve. Só leitura, 1 pedido por conta, com pausa.

    D:\\veo\\venv\\Scripts\\python.exe -m produto.medir_insta --teste      (lista o que leu, não grava)
"""
import argparse
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))

LEITORA = "inovarecom.ia"  # conta cuja sessão lê (ativada no x200ma/acer)
APP_ID = "936619743392459"  # o X-IG-App-ID da página web do Instagram
JS = """async (u) => {
  const h = {headers: {'X-IG-App-ID': '%s'}, credentials: 'include'};
  const p = await fetch('/api/v1/users/web_profile_info/?username=' + u, h);
  if (!p.ok) return {erro: p.status};
  const id = ((await p.json()).data || {}).user?.id;
  if (!id) return {erro: 'sem id'};
  const r = await fetch('/api/v1/feed/user/' + id + '/?count=33', h);
  if (!r.ok) return {erro: r.status};
  const j = await r.json();
  return {itens: (j.items || []).map(i => ({code: i.code, taken_at: i.taken_at,
    views: i.play_count ?? i.ig_play_count ?? i.view_count ?? null,
    legenda: ((i.caption || {}).text || '').slice(0, 80)}))};
}""" % APP_ID


def _log(m):
    print(f"[{datetime.now():%H:%M:%S}] [medir_insta] {m}", flush=True)


def ler(contas, log=_log):
    """{conta: [{code, taken_at, views, legenda}]} lidos numa sessão só. {} se nenhuma máquina abriu."""
    import catalogo
    import maquina_remota
    from playwright.sync_api import sync_playwright
    r = (catalogo._ler(catalogo.REUSO, {}).get("instagram") or {}).get("contas", {}).get(LEITORA) or {}
    if not r.get("maquina"):
        log(f"{LEITORA} sem máquina ativada — não meço")
        return {}
    ordem = maquina_remota.tentativas(r["maquina"], r.get("perfil_remoto"), url="https://www.instagram.com/",
                                      log_fn=log)
    try:
        for rem in ordem:
            if rem is None:  # PC1: não abro Chrome aqui só para medir (dona: PC1 por último; espera a próxima)
                break
            try:
                saida = {}
                with sync_playwright() as p:
                    nav = p.chromium.connect_over_cdp(f"http://127.0.0.1:{rem.porta_local}", timeout=60000)
                    ctx = nav.contexts[0] if nav.contexts else nav.new_context()
                    pg = ctx.new_page()
                    try:
                        pg.goto("https://www.instagram.com/", timeout=90000, wait_until="domcontentloaded")
                        for c in contas:
                            res = pg.evaluate(JS, c)
                            if res.get("erro"):
                                log(f"  {c}: HTTP {res['erro']}")
                                if res["erro"] in (401, 403, 429):
                                    break  # sessão barrada/limite: para tudo (sem insistir)
                            else:
                                saida[c] = res["itens"]
                                log(f"  {c}: {len(res['itens'])} posts lidos no {rem.nome}")
                            time.sleep(random.uniform(4, 9))
                    finally:
                        pg.close()
                if saida:
                    return saida
            except Exception as e:  # noqa: BLE001
                log(f"  {rem.nome}: falhou ({type(e).__name__}: {str(e)[:160]}) — próxima máquina")
    finally:
        if hasattr(ordem, "close"):
            ordem.close()
    return {}


def casar(post, itens, folga_min=45):
    """O item do Instagram do nosso post (catálogo: account + timestamp local): taken_at mais perto, até 45 min."""
    try:
        t = datetime.fromisoformat(str(post["timestamp"])[:19]).astimezone(timezone.utc).timestamp()
    except Exception:  # noqa: BLE001
        return None
    melhor = min(itens, key=lambda i: abs((i.get("taken_at") or 0) - t), default=None)
    if melhor and abs((melhor.get("taken_at") or 0) - t) <= folga_min * 60 and melhor.get("views") is not None:
        return melhor
    return None


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--teste", action="store_true")
    ap.add_argument("--contas", nargs="*", default=["inovarecom.ia", "futebolcom.ia2"])
    a = ap.parse_args()
    lido = ler(a.contas)
    for c, its in lido.items():
        for i in its[:6]:
            print(c, datetime.fromtimestamp(i["taken_at"]).isoformat(timespec="minutes"), i["code"], i["views"],
                  i["legenda"][:50].replace("\n", " "))
