# -*- coding: utf-8 -*-
r"""placar_estilos.py — o que rende em cada Instagram (dona 31/10/2026: "ter todos os tipos e formatos e ir usando os
que têm mais resultado").

1x por dia lê as visualizações dos Reels de cada conta (1 consulta por conta, pela sessão do cofre: as contas
pessoais não têm API) e compara cada Reel com >= 48 h com a MEDIANA da conta: acima = vitória (1), na mediana = 0,5,
abaixo = 0 (mesma regra do funil_insta). Conta no placar comum (postador\bin\placar_titulos.py):
  insta_estilos  grupo <conta>          item = estilo do roteiro (pergunta, criativo, dica, mito, chamada)
  insta_estilos  grupo <conta>:cenas    item = nº de cenas (1, 2, 3)
  insta_estilos  grupo <conta>:formato  item = tipo_video (apresentador, foto_real, video_real, obra_real)
roteiro_ms.escolher_estilo usa o 1º (Thompson). Chamado pelo vigia_pasta_empresas (tarefa de 30 min), 1x por dia.
    D:\veo\venv\Scripts\python.exe placar_estilos.py [--agora]
"""
import json
import statistics as st
import sys
import time
from datetime import datetime
from pathlib import Path

CONTAS = {
    "advance_novoestrela": [Path(r"D:\ms-energy\videos\reels_advance")],
    "globosolarenergiag": [Path(r"D:\ms-energy\videos\reels_globo")],
    "msenergycap": [Path(r"D:\ms-energy\videos\_postados"), Path(r"D:\ms-energy\videos\shorts_veo")],
}
ESTADO = Path(r"D:\ms-energy\cache\placar_estilos.json")
MIN_BASE = 4


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except (OSError, ValueError):
        return padrao


def _sidecars(pastas):
    """{texto do json: dados} dos Reels gerados (para achar o código do Reel no permalink ou em qualquer campo)."""
    out = []
    for pasta in pastas:
        for j in pasta.rglob("*.json") if pasta.exists() else []:
            try:
                txt = j.read_text("utf-8")
                out.append((txt, json.loads(txt)))
            except (OSError, ValueError):
                pass
    return out


def pontuar(conta, pastas, est, log=print):
    sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
    if r"D:\postador-de-videos\bin" not in sys.path:
        sys.path.append(r"D:\postador-de-videos\bin")
    import placar_titulos
    from services.instagram.web import InstagramWeb
    ig = InstagramWeb(conta)
    reels = ig.reels(quantos=30)
    time.sleep(3)
    datas = {p["codigo"]: p["quando"] for p in ig.posts(30) if p.get("quando")}  # a aba Reels não traz a data
    for r in reels:
        r["quando"] = r.get("quando") or datas.get(r.get("codigo"))
    agora = time.time()
    maduros = [r for r in reels if r.get("views") is not None and r.get("quando") and agora - r["quando"] >= 48 * 3600]
    if len(maduros) < MIN_BASE:
        log(f"[placar] {conta}: {len(maduros)} Reel(s) com 48 h (mín. {MIN_BASE}) — espera")
        return 0
    med = st.median(r["views"] for r in maduros)
    med_c = st.median(r.get("curtidas") or 0 for r in maduros)
    med_k = st.median(r.get("comentarios") or 0 for r in maduros)
    sides = _sidecars(pastas)
    feitos = est.setdefault("pontuados", {})
    n = 0
    for r in maduros:
        if not r.get("codigo") or r["codigo"] in feitos:
            continue
        side = next((d for txt, d in sides if r["codigo"] in txt), None)
        if not side:
            continue
        # 31/10 (dona: "visualizações, curtidas etc"): views pesam 2, curtidas e comentários 1 cada, sempre contra a
        # mediana da própria conta (a MS tem ~6 views, a Globo ~400: comparar entre contas seria injusto)
        nota = (2 * (r["views"] > med) + ((r.get("curtidas") or 0) > med_c)
                + ((r.get("comentarios") or 0) > med_k))
        v = 1.0 if nota >= 3 else 0.5 if nota == 2 else 0.0
        chave = f"est:{conta}:{r['codigo']}"
        if side.get("estilo"):
            placar_titulos.registrar_item("insta_estilos", conta, side["estilo"], v, chave)
        placar_titulos.registrar_item("insta_estilos", f"{conta}:cenas", str(side.get("cenas") or 1), v, chave + ":c")
        placar_titulos.registrar_item("insta_estilos", f"{conta}:formato", str(side.get("tipo_video")), v, chave + ":f")
        if side.get("legenda_estilo"):  # 01/11: karaokê x cinética
            placar_titulos.registrar_item("insta_estilos", f"{conta}:legenda", side["legenda_estilo"], v, chave + ":l")
        if side.get("legenda_mix"):  # 01/11: mix de adesivos por palavra — inteligente x livre
            placar_titulos.registrar_item("insta_estilos", f"{conta}:legenda_mix", side["legenda_mix"], v,
                                          chave + ":m")
        if side.get("layout"):  # 01/11: normal x aula (faixa + etapas)
            placar_titulos.registrar_item("insta_estilos", f"{conta}:layout", side["layout"], v, chave + ":y")
        feitos[r["codigo"]] = {"conta": conta, "views": r["views"], "mediana": med, "vitoria": v,
                               "curtidas": r.get("curtidas"), "comentarios": r.get("comentarios"),
                               "estilo": side.get("estilo"), "cenas": side.get("cenas"), "tipo": side.get("tipo_video")}
        n += 1
    log(f"[placar] {conta}: mediana {med} views | {n} Reel(s) novos no placar")
    return n


def relatorio():
    """Texto curto (Telegram) com o que rende em cada empresa solar: estilos com taxa de vitória e nº de testes."""
    if r"D:\postador-de-videos\bin" not in sys.path:
        sys.path.append(r"D:\postador-de-videos\bin")
    import placar_titulos
    linhas = ["☀️ <b>Empresas solares — o que está rendendo</b> (Reels acima da média da própria conta: views, "
              "curtidas e comentários)"]
    for conta in CONTAS:
        for grupo, nome in ((conta, "estilo"), (f"{conta}:cenas", "cenas"), (f"{conta}:formato", "formato"),
                            (f"{conta}:legenda", "legenda"), (f"{conta}:legenda_mix", "mix da legenda"),
                            (f"{conta}:layout", "layout")):
            tx = placar_titulos.taxas("insta_estilos", grupo)
            if not tx:
                continue
            itens = sorted(tx.items(), key=lambda kv: -(kv[1][1] / kv[1][0] if kv[1][0] else 0))
            linhas.append(f"@{conta} {nome}: " + ", ".join(f"{k} {100 * v // t if t else 0}% ({t})"
                                                           for k, (t, v) in itens))
    return "\n".join(linhas) if len(linhas) > 1 else ""


def rodar(agora=False, log=print):
    est = _ler(ESTADO, {})
    hoje = datetime.now().strftime("%Y-%m-%d")
    if est.get("dia") == hoje and not agora:
        return
    for conta, pastas in CONTAS.items():
        try:
            pontuar(conta, pastas, est, log)
        except Exception as e:  # noqa: BLE001  (uma conta fora não para as outras)
            log(f"[placar] {conta}: {type(e).__name__}: {str(e)[:150]}")
        time.sleep(5)
    est["dia"] = hoje
    if datetime.now().weekday() == 0 and est.get("relatorio") != hoje:  # segunda-feira: resumo no Telegram
        txt = relatorio()
        if txt:
            try:
                sys.path.insert(0, r"D:\video-fila")
                import avisos
                avisos.enviar(txt, "empresas-solares-placar", importante=False)
                est["relatorio"] = hoje
            except Exception as e:  # noqa: BLE001
                log(f"[placar] relatório não foi: {e}")
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rodar(agora="--agora" in sys.argv)
