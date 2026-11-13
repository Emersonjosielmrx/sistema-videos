"""Pesquisador de melhorias dos vídeos — gera os pedidos dos ajudantes, confere links e cresce a cada rodada.

Uso (ver LEIA_PRIMEIRO.md):
  python pesquisador.py rodada [--modo area|projeto|cruzado|tudo] [--areas a,b] [--projetos x,y]
  python pesquisador.py conferir <arquivo.md>      # confere repos do GitHub citados (API pública, só leitura)
  python pesquisador.py importar <arquivo.md>      # repos citados -> ja_conhecidos.txt (exclusão nas próximas)
  python pesquisador.py areas_novas <arquivo.md>   # seção AREAS_NOVAS: -> novas áreas no config.json
  python pesquisador.py comparar <pasta da rodada> # argon x gemini: COMPARACAO.md, JUNTO.md, placar.json
  python pesquisador.py marcar <ids>               # registra que a área/projeto foi pesquisada hoje
  python pesquisador.py status
Rodada é DUPLA por padrão (o mesmo pedido para argon-pesquisa e gemini-pro-pesquisa); --simples alterna.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, "config.json")
CONHECIDOS = os.path.join(BASE, "ja_conhecidos.txt")
CACHE = os.path.join(BASE, "conferidos.json")
HISTORICO = os.path.join(BASE, "historico.json")
HIST_AREAS = os.path.join(BASE, "historico_areas.json")  # por pedido: rodadas + repos já trazidos
RODADAS = os.path.join(BASE, "rodadas")

RE_REPO = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
IGNORAR_DONOS = {"orgs", "topics", "search", "features", "settings", "marketplace", "sponsors", "collections"}


def _ler_json(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _gravar_json(caminho, dados):
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    os.replace(tmp, caminho)


def _repos_do_texto(texto):
    vistos = []
    for dono, repo in RE_REPO.findall(texto):
        repo = re.sub(r"\.git$", "", repo).rstrip(".")
        if dono.lower() in IGNORAR_DONOS or not repo:
            continue
        chave = f"{dono}/{repo}"
        if chave.lower() not in {v.lower() for v in vistos}:
            vistos.append(chave)
    return vistos


def _conhecidos():
    try:
        with open(CONHECIDOS, encoding="utf-8") as f:
            return [l.split("#")[0].strip() for l in f if l.split("#")[0].strip()]
    except OSError:
        return []


# ---------------------------------------------------------------- rodada (gera os pedidos)

def _anteriores(chave):
    """O que as rodadas passadas já trouxeram para esta área/projeto (para não repetir)."""
    h = _ler_json(HIST_AREAS, {}).get(chave)
    if not h:
        return ""
    return (f"RODADAS ANTERIORES deste tema ({', '.join(h['rodadas'][-5:])}) já trouxeram: "
            f"{', '.join(h['repos'][-80:])}. NÃO devolva de novo; vá além (outros subtemas, projetos mais novos, "
            f"técnicas sem repositório).\n\n")


def _pedido(cfg, titulo, foco, subtemas, extra="", chave=""):
    conhecidos = _conhecidos()
    return (
        f"PESQUISA DE MELHORIAS — {titulo}\n\n"
        f"Contexto: {cfg['contexto_global']}\n\n"
        f"{extra}{_anteriores(chave)}"
        f"Pesquise na WEB e no GitHub (dados do ano atual, abra os links de verdade) tudo o que melhore: {foco}.\n"
        f"Subtemas para começar (são só exemplos — procure também o que NÃO está na lista e seja específico):\n"
        + "".join(f"- {s}\n" for s in subtemas)
        + f"\nJÁ CONHECEMOS (não repetir; só cite se houver versão nova relevante): {', '.join(conhecidos) or '(nada)'}\n\n"
        f"Devolva 10 a 15 itens. {cfg['formato_resposta']}\n"
    )


def cmd_rodada(args):
    cfg = _ler_json(CONFIG, None)
    modo = _opt(args, "--modo", "tudo")
    so_areas = set(filter(None, _opt(args, "--areas", "").split(",")))
    so_proj = set(filter(None, _opt(args, "--projetos", "").split(",")))
    areas = {a["id"]: a for a in cfg["areas"]}
    hist = _ler_json(HISTORICO, {})
    agentes = cfg["agentes_pesquisa"]

    pasta = os.path.join(RODADAS, datetime.now().strftime("%Y-%m-%d_%H%M"))
    os.makedirs(os.path.join(pasta, "pedidos"), exist_ok=True)
    pedidos = []

    if modo in ("area", "tudo"):
        # áreas pesquisadas há mais tempo (ou nunca) vão primeiro
        ordem = sorted(areas.values(), key=lambda a: hist.get(f"area:{a['id']}", ""))
        for a in ordem:
            if so_areas and a["id"] not in so_areas:
                continue
            pedidos.append((f"area_{a['id']}", a["nome"],
                            _pedido(cfg, f"área {a['nome']}", a["nome"], a["subtemas"], chave=f"area_{a['id']}")))

    if modo in ("projeto", "cruzado", "tudo"):
        for p in cfg["projetos"]:
            if so_proj and p["id"] not in so_proj:
                continue
            docs = "".join(f"- {d}\n" for d in p.get("docs", []))
            extra = (f"PROJETO: {p['nome']} — pasta {p['pasta']}. Antes de pesquisar, LEIA (Read/Glob) o CLAUDE.md "
                     f"ou README da pasta e estes docs para entender o pipeline e o que já foi feito:\n{docs or '- (achar na pasta)'}\n")
            if modo in ("projeto", "tudo"):
                subt = [f"{areas[i]['nome']}: " + "; ".join(areas[i]["subtemas"][:3])
                        for i in p["areas_chave"] if i in areas]
                pedidos.append((f"projeto_{p['id']}", p["nome"],
                                _pedido(cfg, f"projeto {p['nome']}", f"o projeto {p['nome']} especificamente",
                                        subt + ["gargalos e defeitos que você notar no pipeline lido"], extra,
                                        chave=f"projeto_{p['id']}")))
            if modo == "cruzado":
                for i in p["areas_chave"]:
                    if i in areas and (not so_areas or i in so_areas):
                        a = areas[i]
                        pedidos.append((f"{p['id']}__{i}", f"{p['nome']} × {a['nome']}",
                                        _pedido(cfg, f"{a['nome']} no projeto {p['nome']}",
                                                f"{a['nome']} aplicado ao projeto {p['nome']}", a["subtemas"], extra,
                                                chave=f"{p['id']}__{i}")))

    # duplo (padrão, pedido da dona 03/11): o MESMO pedido vai para os dois pesquisadores -> comparar e juntar
    duplo = "--simples" not in args
    lista = []
    for n, (nome, titulo, texto) in enumerate(pedidos):
        arq = os.path.join(pasta, "pedidos", f"{nome}.md")
        with open(arq, "w", encoding="utf-8") as f:
            f.write(texto)
        for ag in (agentes if duplo else [agentes[n % len(agentes)]]):
            curto = ag.split("-")[0]
            lista.append({"id": nome, "titulo": titulo, "agente": ag, "pedido": arq,
                          "resposta": os.path.join(pasta, "respostas", f"{nome}__{curto}.md")})
    os.makedirs(os.path.join(pasta, "respostas"), exist_ok=True)
    _gravar_json(os.path.join(pasta, "rodada.json"), lista)
    print(json.dumps({"pasta": pasta, "total": len(lista), "pedidos": lista}, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- conferir links (API pública do GitHub)

def _api(repo):
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "pesquisador-melhorias"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
        lic = (d.get("license") or {}).get("spdx_id") or "SEM LICENÇA"
        return {"ok": True, "nome": d.get("full_name"), "estrelas": d.get("stargazers_count"),
                "push": (d.get("pushed_at") or "")[:10], "licenca": lic, "arquivado": d.get("archived"),
                "descricao": (d.get("description") or "")[:140]}
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            try:
                req2 = urllib.request.Request(f"https://github.com/{repo}", headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=20) as r2:
                    html = r2.read(1500000).decode("utf-8", "ignore")
                m_desc = re.search(r'<meta name="description" content="([^"]+)"', html)
                desc = (m_desc.group(1) if m_desc else "").replace(f" - {repo}", "")[:140]
                m_st = (re.search(r'aria-label="([0-9,]+) users? starred this repository"', html)
                        or re.search(r'id="repo-stars-counter-star"[^>]*title="([0-9,]+)"', html)
                        or re.search(r'title="([0-9,]+)"[^>]*id="repo-stars-counter-star"', html))
                est = int(m_st.group(1).replace(",", "")) if m_st else None
                m_dono = re.search(r'<meta property="og:url" content="https://github.com/([^"]+)"', html)
                return {"ok": True, "nome": (m_dono.group(1) if m_dono else repo), "estrelas": est,
                        "push": "?", "licenca": "ver repo (fallback HTML)",
                        "arquivado": "This repository has been archived" in html,
                        "descricao": desc}
            except urllib.error.HTTPError as e2:
                if e2.code == 404:
                    return {"ok": False, "erro": "HTTP 404"}
            except Exception:
                pass
            return {"ok": None, "erro": "limite da API (60/h sem GITHUB_TOKEN) — rode de novo depois"}
        return {"ok": False, "erro": f"HTTP {e.code}"}
    except Exception as e:  # rede caiu etc.
        return {"ok": None, "erro": str(e)[:80]}


def cmd_conferir(args):
    with open(args[0], encoding="utf-8") as f:
        repos = _repos_do_texto(f.read())
    cache = _ler_json(CACHE, {})
    linhas = ["| repo | existe | ★ | último push | licença | obs |", "|---|---|---|---|---|---|"]
    for repo in repos:
        r = cache.get(repo.lower())
        if not r or r.get("ok") is None or r.get("data") != str(date.today()):
            r = _api(repo)
            r["data"] = str(date.today())
            if r.get("ok") is not None:
                cache[repo.lower()] = r
                _gravar_json(CACHE, cache)
            time.sleep(1.2)
        if r.get("ok"):
            obs = "ARQUIVADO" if r["arquivado"] else ""
            if r["licenca"] in ("SEM LICENÇA", "NOASSERTION", "NOASSERTION".lower()):
                obs += " ler LICENSE (comercial?)"
            if r["push"] and r["push"] < str(date.today().year - 1):
                obs += " parado"
            linhas.append(f"| {r['nome']} | sim | {r['estrelas']} | {r['push']} | {r['licenca']} | {obs.strip()} |")
        else:
            linhas.append(f"| {repo} | {'NÃO' if r.get('ok') is False else '?'} | | | | {r.get('erro', '')} |")
    saida = os.path.splitext(args[0])[0] + "_CONFERIDO.md"
    with open(saida, "w", encoding="utf-8") as f:
        f.write(f"# Conferência dos repositórios — {date.today()}\n\nFonte: api.github.com (só leitura).\n\n"
                + "\n".join(linhas) + "\n")
    print("\n".join(linhas))
    print(f"\n-> {saida}")


# ---------------------------------------------------------------- crescer a cada rodada

def cmd_importar(args):
    atuais = {c.lower() for c in _conhecidos()}
    novos = []
    for arq in args:
        with open(arq, encoding="utf-8") as f:
            texto = f.read()
        achados = _repos_do_texto(texto)
        if os.path.basename(arq).upper().startswith("JUNTO"):
            # JUNTO.md lista "- dono/repo — ..." sem github.com/; só os que existem (pula NÃO EXISTE)
            achados = [m for m in re.findall(r"^- ([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+) — (?!NÃO EXISTE)", texto, re.M)]
        if True:
            for r in achados:
                if r.lower() not in atuais:
                    atuais.add(r.lower())
                    novos.append(f"{r}  # {os.path.basename(arq)} {date.today()}")
    if novos:
        with open(CONHECIDOS, "a", encoding="utf-8") as f:
            f.write("\n".join(novos) + "\n")
    print(f"{len(novos)} repositórios novos em ja_conhecidos.txt (total {len(atuais)})")


def cmd_areas_novas(args):
    cfg = _ler_json(CONFIG, None)
    ids = {a["id"] for a in cfg["areas"]}
    add = []
    for arq in args:
        with open(arq, encoding="utf-8") as f:
            texto = f.read()
        m = re.search(r"AREAS_NOVAS:\s*\n(.*?)(?:\n#|\Z)", texto, re.S)
        if not m:
            continue
        for linha in m.group(1).splitlines():
            partes = [p.strip(" -*`") for p in linha.split("|")]
            if len(partes) < 3 or not partes[0]:
                continue
            aid = re.sub(r"[^a-z0-9_]", "_", partes[0].lower())[:40]
            if aid in ids:
                continue
            ids.add(aid)
            add.append({"id": aid, "nome": partes[1], "subtemas": [partes[2]],
                        "origem": f"{os.path.basename(arq)} {date.today()}"})
    cfg["areas"].extend(add)
    _gravar_json(CONFIG, cfg)
    print(f"{len(add)} áreas novas no config.json: " + ", ".join(a["id"] for a in add))


def cmd_comparar(args):
    """comparar <pasta da rodada>: argon x gemini no mesmo pedido -> COMPARACAO.md, JUNTO.md e placar.json."""
    pasta = args[0]
    resp = os.path.join(pasta, "respostas")
    por_id = {}
    for arq in sorted(os.listdir(resp)):
        m = re.match(r"(.+)__([a-z0-9]+)\.md$", arq)
        if m:
            por_id.setdefault(m.group(1), {})[m.group(2)] = os.path.join(resp, arq)
    cache = _ler_json(CACHE, {})
    placar = _ler_json(os.path.join(BASE, "placar.json"), {})
    conhecidos = {c.lower() for c in _conhecidos()}
    linhas = ["| pedido | agente | web | repos | existem | novos (fora do já conhecido) | só ele achou |",
              "|---|---|---|---|---|---|---|"]
    junto = [f"# Resultado juntado — {os.path.basename(pasta)}\n"]
    for pid, ags in sorted(por_id.items()):
        repos = {}
        textos = {}
        for ag, arq in ags.items():
            with open(arq, encoding="utf-8") as f:
                textos[ag] = f.read()
            repos[ag] = {r.lower(): r for r in _repos_do_texto(textos[ag])}
        todos = {}
        for ag in repos:
            for k, r in repos[ag].items():
                todos.setdefault(k, (r, set()))[1].add(ag)
        # confere existência (usa cache; consulta o que falta)
        for k, (r, _) in todos.items():
            if k not in cache or cache[k].get("ok") is None:
                c = _api(r)
                c["data"] = str(date.today())
                if c.get("ok") is not None:
                    cache[k] = c
                time.sleep(1.2)
        _gravar_json(CACHE, cache)
        for ag in repos:
            web = "SIM" if re.search(r"WEB:\s*SIM", textos[ag][:300], re.I) else "NAO"
            existe = [k for k in repos[ag] if cache.get(k, {}).get("ok")]
            novos = [k for k in existe if k not in conhecidos]
            so = [k for k in existe if todos[k][1] == {ag}]
            linhas.append(f"| {pid} | {ag} | {web} | {len(repos[ag])} | {len(existe)} | {len(novos)} | {len(so)} |")
            p = placar.setdefault(ag, {"pedidos": 0, "web_sim": 0, "repos": 0, "existem": 0, "novos": 0, "exclusivos": 0})
            p["pedidos"] += 1
            p["web_sim"] += web == "SIM"
            p["repos"] += len(repos[ag])
            p["existem"] += len(existe)
            p["novos"] += len(novos)
            p["exclusivos"] += len(so)
        # histórico por tema: a próxima rodada recebe estes repos como "já trazidos"
        ha = _ler_json(HIST_AREAS, {})
        h = ha.setdefault(pid, {"rodadas": [], "repos": []})
        if os.path.basename(pasta) not in h["rodadas"]:
            h["rodadas"].append(os.path.basename(pasta))
        for k in todos:
            nome = cache.get(k, {}).get("nome")
            if nome and nome not in h["repos"]:
                h["repos"].append(nome)
        _gravar_json(HIST_AREAS, ha)
        junto.append(f"\n## {pid}\n")
        for k, (r, quem) in sorted(todos.items(), key=lambda x: -(cache.get(x[0], {}).get("estrelas") or 0)):
            c = cache.get(k, {})
            if c.get("ok"):
                junto.append(f"- {c['nome']} — ★{c['estrelas']}, push {c['push']}, {c['licenca']}"
                             f"{' ARQUIVADO' if c.get('arquivado') else ''} — achado por: {', '.join(sorted(quem))}"
                             f"{'' if k not in conhecidos else ' (já conhecido)'} — {c.get('descricao', '')}")
            else:
                junto.append(f"- {r} — NÃO EXISTE/erro ({c.get('erro', '?')}) — citado por: {', '.join(sorted(quem))}")
    _gravar_json(os.path.join(BASE, "placar.json"), placar)
    tab = ["| agente | pedidos | respondeu c/ web | repos citados | existem | % existem | novos | só ele achou |",
           "|---|---|---|---|---|---|---|---|"]
    for ag, p in placar.items():
        pct = round(100 * p["existem"] / p["repos"]) if p["repos"] else 0
        tab.append(f"| {ag} | {p['pedidos']} | {p['web_sim']} | {p['repos']} | {p['existem']} | {pct}% | {p['novos']} | {p['exclusivos']} |")
    with open(os.path.join(pasta, "COMPARACAO.md"), "w", encoding="utf-8") as f:
        f.write(f"# Argon x Gemini Pro — {os.path.basename(pasta)}\n\n## Esta rodada\n" + "\n".join(linhas)
                + "\n\n## Placar acumulado (todas as rodadas)\n" + "\n".join(tab) + "\n")
    with open(os.path.join(pasta, "JUNTO.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(junto) + "\n")
    print("\n".join(linhas + [""] + tab))
    print(f"\n-> {pasta}\\COMPARACAO.md e JUNTO.md")


def cmd_marcar(args):
    """marcar <id ...>: registra que a área/projeto foi pesquisada hoje (ordem da próxima rodada)."""
    hist = _ler_json(HISTORICO, {})
    for i in args:
        chave = i if ":" in i else (f"projeto:{i[8:]}" if i.startswith("projeto_") else f"area:{i.replace('area_', '')}")
        hist[chave] = str(date.today())
    _gravar_json(HISTORICO, hist)
    print(f"{len(args)} marcados")


def cmd_status(_args):
    cfg = _ler_json(CONFIG, None)
    hist = _ler_json(HISTORICO, {})
    print(f"Áreas: {len(cfg['areas'])} | Projetos: {len(cfg['projetos'])} | Repos conhecidos: {len(_conhecidos())}")
    for a in cfg["areas"]:
        print(f"  area {a['id']:<26} última: {hist.get('area:' + a['id'], 'nunca')}")
    for p in cfg["projetos"]:
        print(f"  proj {p['id']:<26} última: {hist.get('projeto:' + p['id'], 'nunca')}")


def _opt(args, nome, padrao):
    return args[args.index(nome) + 1] if nome in args and args.index(nome) + 1 < len(args) else padrao


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = {"rodada": cmd_rodada, "conferir": cmd_conferir, "importar": cmd_importar,
           "areas_novas": cmd_areas_novas, "marcar": cmd_marcar, "status": cmd_status,
           "comparar": cmd_comparar}.get(sys.argv[1])
    if not cmd:
        print(__doc__)
        sys.exit(1)
    cmd(sys.argv[2:])
