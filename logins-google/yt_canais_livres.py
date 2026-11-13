#!/usr/bin/env python3
"""yt_canais_livres.py — canais do YouTube que as contas do cofre têm e que AINDA NÃO usamos (dona 23/10/2026: "verificar
quais dessas contas têm canal no YouTube que ainda não usamos; as que tiverem os canais banidos não contam; queremos
pegar os canais desgarrados que ainda não estamos postando").

Para cada conta com Google vivo no cofre: youtube.com/account ("All channels" = nome | @handle | inscritos). Para
cada canal, a página pública do @ diz se ele foi encerrado/suspenso. Comparado com o cadastro de canais do postador
(D:\\postador-de-videos\\config\\canais.json + rede_canais.json): em_uso / livre / banido. Só lê.
Saídas: yt_canais_livres.json e YOUTUBE_CANAIS_LIVRES.md.

    python yt_canais_livres.py              # todas as contas com Google vivo
    python yt_canais_livres.py conta1 ...   # só essas
    python yt_canais_livres.py --relatorio
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import cofre  # noqa: E402

SAIDA = BASE / "yt_canais_livres.json"
RELATORIO = BASE / "YOUTUBE_CANAIS_LIVRES.md"
POSTADOR = Path(r"D:\postador-de-videos\config")
BANIDO = re.compile(r"encerrad|terminated|suspens|violação|violat|não está disponível|isn.t available|"
                    r"Este canal não existe|This channel doesn.t exist|removid", re.I)


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


# canais PESSOAIS da dona (23/10: "esses 3 eu não uso porque são pessoais"): nunca entram como "livre"
PESSOAIS = {"@fabricadeautomacoesia", "@emersonjosiel", "@hayllamikeyce3154"}


def norm(h):
    """@handle sem acento e minúsculo (23/10: "@CódigoInteligente-n7j" é o "@codigointeligente-n7j" do cadastro)."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", str(h)) if not unicodedata.combining(c)).lower()


def em_uso():
    """@handles (normalizados) dos canais que já usamos."""
    # @ E nome: canal do cadastro sem @ (23/10: Manhwa Noturno e InovareManhwaVerse) saía como "livre"
    out = set()
    for c in list((_ler(POSTADOR / "canais.json", {}).get("canais") or {}).values()) + \
            list(_ler(POSTADOR / "rede_canais.json", {}).get("canais") or []):
        for k in ("handle", "nome"):
            if c.get(k):
                out.add(norm(c[k]).replace(" ", ""))
    return out


def _texto(pg):
    return [x.strip() for x in pg.inner_text("body", timeout=15000).splitlines() if x.strip()]


def canais_da_conta(pg):
    """[(nome, @handle, inscritos)] da lista "All channels / Todos os canais" de youtube.com/account."""
    # entra pelo channel_switcher (redireciona pra /account) e espera a lista carregar (ela vem depois do resto)
    pg.goto("https://www.youtube.com/channel_switcher", wait_until="domcontentloaded", timeout=90000)
    ls = []
    for _ in range(12):
        pg.wait_for_timeout(2500)
        if "accounts.google.com" in pg.url:
            return None
        ls = _texto(pg)
        if any(re.fullmatch(r"All channels|Todos os canais", x, re.I) for x in ls) and any(x.startswith("@") for x in ls):
            break
        pg.mouse.wheel(0, 600)
    try:
        i = next(k for k, x in enumerate(ls) if re.fullmatch(r"All channels|Todos os canais", x, re.I))
    except StopIteration:
        return []
    out = []
    for k in range(i + 1, len(ls)):
        if ls[k].startswith("@") and k > 0:
            insc = ls[k + 1] if k + 1 < len(ls) and re.search(r"inscrit|subscriber", ls[k + 1], re.I) else ""
            out.append((ls[k - 1], ls[k], insc))
    return out


def situacao_canal(pg, handle):
    try:
        pg.goto(f"https://www.youtube.com/{handle}", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(5000)
        txt = " ".join(_texto(pg)[:80])
        return "banido" if BANIDO.search(txt) else "ativo"
    except Exception as e:  # noqa: BLE001
        return f"erro {type(e).__name__}"


def main(args):
    if "--relatorio" not in args:
        from playwright.sync_api import sync_playwright
        reg = cofre._ler()["contas"]
        alvos = [cofre.conta(a)[0] for a in args if not a.startswith("--")] or \
            [e for e, v in reg.items() if v.get("google") == "vivo" and v.get("tipo") != "instagram"]
        usados = em_uso()
        d = _ler(SAIDA, {})
        with sync_playwright() as p:
            for i, email in enumerate(alvos, 1):
                porta, proc = cofre.abrir(email)
                br = None
                res = {"em": datetime.now().isoformat(timespec="minutes"), "canais": []}
                try:
                    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
                    pg = br.contexts[0].new_page()
                    lista = canais_da_conta(pg)
                    if lista is None:
                        res["situacao"] = "pediu_login"
                    else:
                        res["situacao"] = "ok"
                        for nome, h, insc in lista:
                            st = "em_uso" if {norm(h).replace(" ", ""), norm(nome).replace(" ", "")} & usados else situacao_canal(pg, h)
                            res["canais"].append({"nome": nome, "handle": h, "inscritos": insc,
                                                  "situacao": "livre" if st == "ativo" else st})
                    pg.close()
                except Exception as e:  # noqa: BLE001
                    res["situacao"] = f"erro {type(e).__name__}: {str(e)[:100]}"
                finally:
                    try:
                        cofre.fechar(proc, br, email)
                    except Exception:  # noqa: BLE001
                        pass
                d = _ler(SAIDA, {})
                d[email] = res
                SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"[{i}/{len(alvos)}] {email}: {res['situacao']} "
                      + ", ".join(f"{c['handle']}={c['situacao']}" for c in res["canais"]), flush=True)
    d = _ler(SAIDA, {})
    usados = em_uso()  # recalcula: leituras antigas comparavam sem tirar acento
    for r in d.values():
        for c in r.get("canais", []):
            if c["situacao"] == "livre" and ({norm(c["handle"]).replace(" ", ""), norm(c.get("nome", "")).replace(" ", "")} & usados):
                c["situacao"] = "em_uso"
            if norm(c["handle"]) in PESSOAIS:
                c["situacao"] = "pessoal"
    SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    livres = [(e, c) for e, r in d.items() for c in r.get("canais", []) if c["situacao"] == "livre"]
    ln = ["# Canais do YouTube ainda não usados (yt_canais_livres.py)", "",
          f"Atualizado {datetime.now():%d/%m %H:%M}. {len(livres)} canal(is) livre(s) em {len(d)} conta(s) conferida(s).", "",
          "## Livres (ativos e fora do cadastro do postador)", "", "| conta | canal | @ | inscritos |", "|---|---|---|---|"]
    ln += [f"| {e} | {c['nome']} | {c['handle']} | {c['inscritos']} |" for e, c in livres] or ["| — | — | — | — |"]
    ln += ["", "## Banidos (não contam)", ""]
    ln += [f"- {e}: {c['handle']}" for e, r in d.items() for c in r.get("canais", []) if c["situacao"] == "banido"] or ["- nenhum"]
    ln += ["", "## Contas que pediram login / erro", ""]
    ln += [f"- {e}: {r['situacao']}" for e, r in d.items() if r.get("situacao") != "ok"] or ["- nenhuma"]
    RELATORIO.write_text("\n".join(ln) + "\n", encoding="utf-8")
    print(RELATORIO)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
