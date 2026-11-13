"""conferir_pedidos.py — confere, num longo PRONTO, se os pedidos da dona saíram no vídeo (30/10, Fable; dona: "trabalhe
junto com o melhorador pra melhorar a cada vídeo que sair"). Lê o pipeline.log e o render.json da ficha (que o
alimentador copia do Kaggle) e grava CONFERENCIA.md na ficha + uma linha em linhas\\LONGOS\\conferencias.jsonl (o
melhorador central/longo lê). Sem IA, só o que o próprio render registrou.

    python conferir_pedidos.py <pasta da ficha | id do vídeo>    # um
    python conferir_pedidos.py --novos                             # todas as fichas com pipeline.log ainda não conferidas
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))  # ficha_longo.py
REGISTRO = AQUI / "conferencias.jsonl"
NARR = Path(r"D:\recapd-ambientes\producao\colab\teste_narradores.json")


def _n(rx, txt):
    m = re.search(rx, txt)
    return int(m.group(1)) if m else 0


def conferir(ficha):
    ficha = Path(ficha)
    log = (ficha / "pipeline.log").read_text(encoding="utf-8", errors="replace")
    try:
        render = json.loads((ficha / "render.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        render = {}
    try:
        g = json.loads(NARR.read_text(encoding="utf-8"))
        ruins, grupos = set(g.get("ruins") or []), g.get("grupos") or {}
    except (OSError, ValueError):
        ruins, grupos = set(), {}
    vozes = [v for v in str(render.get("vozes_lista") or "").split(",") if v]
    primeira_ok = bool(vozes) and vozes[0] in (grupos.get("resumo") or [])
    itens = []

    def item(pedido, ok, detalhe):
        itens.append({"pedido": pedido, "ok": ok, "detalhe": detalhe})

    m = re.search(r"\[longo\] resumo de abertura: (\d+) frases", log)
    item("Resumo de abertura", bool(m), f"{m.group(1)} frases" if m else
         ("FALTOU (IA fora — ver faltou.json)" if "resumo" in log and "faltou" in log.lower() else "não saiu"))
    item("Narradores por grupo, 1º = voz do resumo", primeira_ok and not (set(vozes) & ruins),
         f"{', '.join(vozes) or '(sem revezamento)'}" + (f" | RUINS: {', '.join(set(vozes) & ruins)}" if set(vozes) & ruins else ""))
    fp = _n(r"\[longo\] (\d+) falas de personagem", log)
    fv = re.search(r"\[personagem\] (\d+) falas com voz de personagem \(([^)]*)\)", log)
    item("Falas de personagem com outra voz", fp > 0 and bool(fv),
         f"{fp} falas marcadas" + (f"; vozes: {fv.group(2)}" if fv else "; NENHUMA saiu com voz própria"))
    pz = _n(r"\[mascote\] (\d+) CTAs viram pausa", log)
    item("Mascote: pausa com a voz dela (só gravações andando)", pz > 0,
         f"{pz} pausas" + ("; JAQUETA na pausa!" if re.search(r"\[mascote\] pausa \d+: (inscreva|comenta)_0\d", log) else ""))
    rea = _n(r"\[longo\] mascote reagindo em (\d+)", log)
    item("Mascote reagindo à história", rea > 0, f"{rea} reações")
    mv = _n(r"\[longo\] (\d+) meme\(s\) visual", log)
    fig = len(re.findall(r"\[meme\] figurinha no trecho", log))
    item("Memes visuais (tela cheia + figurinhas)", mv + fig > 0, f"{mv} em tela cheia, {fig} figurinhas")
    se = _n(r"\[longo\] (\d+) fala\(s\) de série", log)
    item("Falas reais de séries (bordões)", se > 0, f"{se}")
    dv = len(re.findall(r"\[divisoria\] trecho", log))
    item("Transição divisória (estilo manhwa-react)", dv > 0, f"{dv} transições")
    part = len(re.findall(r"\+ (particula|transicao) ", log))
    item("SEM partículas/transições de elemento (roxo)", part == 0, f"{part} encontradas")
    perfil = re.search(r"\[longo\] fonte tipo \w+; perfil: (\{.*?\})", log)
    tremida = "ANIME_FX_TREMIDA_TODOS': '1'" in (perfil.group(1) if perfil else "")
    item("Tremida só em impacto (não no vídeo todo)", not tremida, "tremida geral LIGADA" if tremida else "ok")
    lufs = re.search(r"master: (-?[\d.]+) LUFS", log)
    item("Som final masterizado", bool(lufs), f"mix {lufs.group(1)} LUFS -> -14" if lufs else "sem master")
    cap = _n(r"\[longo\] (\d+) capítulos", log)
    item("Capítulos", cap > 0, f"{cap}" + (" (com Comente PARTE 2)" if 'PARTE 2' in log else ""))
    gh = _n(r"\[longo\] (\d+) mini-ganchos", log)  # 30/10: engenharia reversa (Porão) — gancho a cada 15 min
    item("Mini-ganchos a cada 15 min", gh > 0, f"{gh}")
    falhas = sorted(set(re.findall(r"\[(longo|mascote|personagem)\][^\n]*(?:falhou|indisponível|não entrou)[^\n]*", log)))
    ok = sum(1 for i in itens if i["ok"])
    md = [f"# Conferência dos pedidos — {ficha.name}", f"{datetime.now():%d/%m %H:%M} · {ok} de {len(itens)} ok", "",
          "| pedido | ok | detalhe |", "|---|---|---|"]
    md += [f"| {i['pedido']} | {'✅' if i['ok'] else '❌'} | {i['detalhe']} |" for i in itens]
    linhas_falha = [l for l in log.splitlines() if re.search(r"\[(longo|mascote|personagem)\].*(falhou|indisponível|não entrou)", l)]
    if linhas_falha:
        md += ["", "Falhas registradas no render:", *[f"- `{l[-200:]}`" for l in linhas_falha[:15]]]
    (ficha / "CONFERENCIA.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    with REGISTRO.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "ficha": ficha.name, "ok": ok,
                            "total": len(itens), "faltando": [i["pedido"] for i in itens if not i["ok"]]},
                           ensure_ascii=False) + "\n")
    print("\n".join(md))
    return itens


def _ja_conferidas():
    try:
        return {json.loads(l)["ficha"] for l in REGISTRO.read_text(encoding="utf-8").splitlines() if l.strip()}
    except OSError:
        return set()


if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else "--novos"
    if alvo == "--novos":
        feitas = _ja_conferidas()
        enviados = 0
        MAX_AVISOS = 3  # 01/11: 9 fichas antigas conferidas de uma vez mandaram 9 avisos na hora; o resto vai no resumo
        for p in sorted(FICHAS.glob("*/pipeline.log"), key=lambda x: x.stat().st_mtime):
            if p.parent.name not in feitas and p.stat().st_mtime > datetime(2026, 10, 29, 19).timestamp():
                itens = conferir(p.parent)
                try:
                    sys.path.insert(0, r"D:\video-fila")
                    import avisos
                    falta = [i for i in itens if not i["ok"]]
                    try:  # 01/11 (dona): tempo, onde vai postar, atualizações que entraram e as do próximo
                        import ficha_longo
                        cab = ficha_longo.texto(p.parent) + "\n\n"
                    except Exception as e:  # noqa: BLE001 — sem a ficha o aviso sai como antes
                        print(f"ficha_longo falhou: {e}")
                        cab = f"🔎 Longo pronto conferido: {p.parent.name[:60]}\n"
                    avisos.enviar(cab + f"✅ {len(itens) - len(falta)} de {len(itens)} pedidos seus saíram no vídeo."
                                  + ("\nFaltou: " + "; ".join(f"{i['pedido']} ({i['detalhe'][:60]})" for i in falta)
                                     if falta else ""), "longo", importante=enviados < MAX_AVISOS,
                                  chave="<SEGREDO_REMOVIDO>" + p.parent.name)
                    enviados += 1
                except Exception as e:  # noqa: BLE001
                    print(f"aviso falhou: {e}")
    else:
        pasta = Path(alvo) if Path(alvo).exists() else next(FICHAS.glob(f"{alvo}*"))
        conferir(pasta)
