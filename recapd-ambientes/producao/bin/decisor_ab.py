r"""decisor_ab.py — fecha sozinho os testes A/B dos Shorts (Cortes) que já têm resposta. 25/11.

Por quê (levantamento aprendizado-metricas, 24/11): o placar_variantes.py "não muda nada sozinho" e nenhuma tarefa o
chamava — placar parado desde 17/11 e testes "sem diferença" sorteando braço pra sempre (gancho_meio 346 x 322,
saudacao 299 x 310, fala_rapida 323 x 324). Regra FIXA, sem IA (o melhorador está pausado; isto não é ele):
  1. roda o placar (mesma régua do FABLE_DECISOES.md: D3 + D16, P >= 0,95);
  2. "PRONTO PARA DECIDIR" com vencedor  -> grava o braço vencedor;
     "PRONTO" só com perdedor           -> grava a referência (A), que ganhou;
  3. "dados suficientes, sem diferença"  com >= EMPATE_N medidos por braço -> EMPATE: grava a referência (o padrão)
     e libera a vaga pra outro teste.
Cada mudança entra em cortes_ajustes.json["historico"] (quem="decisor_ab", porque=números) e no log.
Nunca mexe em teste que a dona pôs fora do "ab", nem no horario_fraco (só indício).

    python decisor_ab.py            # decide e grava
    python decisor_ab.py --ver      # só mostra o que faria
Desligar: DECISOR_AB=0.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
AJUSTES = AQUI / "cortes_ajustes.json"
LOG = Path(r"D:\video-fila\linhas\CORTES\decisor_ab.log")
EMPATE_N = int(os.environ.get("DECISOR_EMPATE_N", "200"))
NUNCA = {"horario_fraco"}


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M}] {m}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def decidir(res):
    """{teste: (novo_valor, porque)} só dos que fecham agora."""
    out = {}
    for nome, r in res.items():
        if nome in NUNCA or r.get("valor_atual") != "ab":
            continue
        ref = r.get("referencia") or "A"
        estado = r.get("estado", "")
        pb = r.get("por_braco") or {}
        ns = {b: (pb.get(b) or {}).get("n_elegiveis", 0) for b in r.get("bracos_sorteados") or []}
        sug = r.get("sugestao") or ""
        if estado.startswith("PRONTO"):
            vence = None
            for b in r.get("bracos_sorteados") or []:
                if b != ref and f"'{b}'" in sug.split("melhor que")[0]:
                    vence = b
            novo = vence or ref
            out[nome] = (novo, f"placar PRONTO (D3+D16): {sug or 'referência venceu'}; n por braço {ns}")
        elif estado.startswith("dados suficientes") and ns and min(ns.values()) >= EMPATE_N:
            out[nome] = (ref, f"EMPATE: {min(ns.values())}+ medidos por braço sem diferença (P<0,95); fica o padrão "
                              f"{ref}; n por braço {ns}")
    return out


def main():
    if os.environ.get("DECISOR_AB", "1") == "0":
        print("DECISOR_AB=0 — desligado")
        return
    ver = "--ver" in sys.argv
    import placar_variantes as pv
    import variantes
    linhas = pv.carregar(48)
    res = pv.placar(linhas, variantes.ajustes())
    dec = decidir(res)
    abertos = [n for n, r in res.items() if r.get("valor_atual") == "ab"]
    log(f"placar: {len(linhas)} Shorts medidos, {len(abertos)} teste(s) aberto(s), {len(dec)} fecham agora")
    for n, r in res.items():
        if r.get("valor_atual") == "ab":
            log(f"  {n}: {r.get('estado')} {r.get('sugestao') or ''}")
    if not dec or ver:
        for n, (v, pq) in dec.items():
            log(f"  {'(ver) ' if ver else ''}{n} -> {v!r}: {pq}")
        return
    aj = json.loads(AJUSTES.read_text(encoding="utf-8"))
    bkp = AJUSTES.with_name(f"cortes_ajustes.json.bkp_decisor_{datetime.now():%Y%m%d_%H%M}")
    bkp.write_text(json.dumps(aj, ensure_ascii=False, indent=1), encoding="utf-8")
    hist = aj.setdefault("historico", [])
    for n, (v, pq) in dec.items():
        hist.append({"em": datetime.now().isoformat(timespec="minutes"), "quem": "decisor_ab", "chave": n,
                     "antes": aj.get(n, "ab"), "depois": v, "porque": pq})
        aj[n] = v
        log(f"  FECHADO {n} -> {v!r}: {pq}")
    tmp = AJUSTES.with_suffix(".tmp")
    tmp.write_text(json.dumps(aj, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, AJUSTES)
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar("🧪 Testes A/B dos Shorts fechados sozinhos: " +
                      "; ".join(f"{n} -> {v}" for n, (v, _) in dec.items()), "cortes", importante=False,
                      chave="<SEGREDO_REMOVIDO>", html_ok=False)
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main()
