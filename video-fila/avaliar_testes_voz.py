# -*- coding: utf-8 -*-
"""avaliar_testes_voz.py — VIGIA do teste gradual de formatos e vozes (dona 23/10/2026: "põe o vigia pra ir avaliando
conforme tal personagem for se saindo bem"). Subvigia do vigia_geral (a cada 3 h). Sem LLM, sem agente.

O teste em si é o recapd bin\\anime_testes.py (sorteio na produção, conferência do áudio, placar de 48 h). Aqui:
  1. Short em teste que saiu SEM conferência (Groq fora na hora) e ainda não subiu: transcreve agora; soou mal = segura.
  2. Junta por item: produzidos, refeitos no solo, segurados, postados, medidos em 48 h, vitórias x solo, estado.
  3. Escreve D:\\video-fila\\TESTES_VOZ_RELATORIO.md (a dona e as outras sessões leem).
  4. Avisa no Telegram (bot de produção) quando um item é PROMOVIDO (vai sair mais vezes) ou PAUSADO; 1 resumo por dia.

  python avaliar_testes_voz.py            # rodada normal
  python avaliar_testes_voz.py --sem-aviso
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
RECAPD_BIN = Path(r"D:\recapd-ambientes\producao\bin")
sys.path.append(str(RECAPD_BIN))  # no FIM: os módulos daqui (avisos) vêm primeiro
import anime_testes  # noqa: E402

RELATORIO = BASE / "TESTES_VOZ_RELATORIO.md"
ESTADO = BASE / "logs" / "testes_voz_vigia.json"
LOG = BASE / "logs" / "avaliar_testes_voz.log"
MEDIDAS = Path(r"D:\postador-de-videos\config\telegram_estado.json")
STUDIO = Path(r"D:\postador-de-videos\_analise\metricas_studio.json")  # retenção (metricas_rede, outra sessão)
MIN_VIEWS_RET = 50  # com 3 views "100% continuaram" não diz nada


def log(msg):
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(linha)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(linha + "\n")
    except OSError:
        pass


def _video_id(url):
    url = str(url or "")
    for sep in ("/shorts/", "v=", "youtu.be/"):
        if sep in url:
            return url.split(sep, 1)[1].split("&")[0].split("?")[0].strip("/")
    return None


def _registros():
    out = []
    try:
        for ln in anime_testes.REGISTRO.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except ValueError:
                pass
    except OSError:
        pass
    return out


def reconferir(regs, est):
    """Short em teste sem conferência (ok=None) e ainda não postado: confere agora; ruim = segura. O resultado fica no
    estado do vigia (o registro é só da produção: regravar ele aqui perderia linha escrita no meio-tempo)."""
    feitos = 0
    rec = est.setdefault("reconferidos", {})
    for r in regs:
        if r.get("pasta") in rec:
            r["reconferido"] = rec[r["pasta"]]
        q = r.get("qualidade") or {}
        if q.get("ok") is not None or r.get("reconferido") or not r.get("pasta"):
            continue
        pasta = Path(r["pasta"])
        pj = anime_testes._ler(pasta / "postar.json", None)
        falas = anime_testes.falas_da_pasta(pasta)
        if not pj or not falas or not (pasta / "video.mp4").exists():
            continue
        ca = pj.get("conferido_audio") or {}
        if ca.get("ok") is not None and ca.get("por") != "anime_testes":
            q = {"ok": ca["ok"], "sem": ca.get("sem"), "motivo": ca.get("motivo") or ""}  # a conferência do upload já ouviu
        elif pj.get("posted_url"):
            continue
        else:
            q = anime_testes.conferir(pasta, pasta / "video.mp4", falas)
        if q.get("ok") is None:
            continue
        r["reconferido"] = rec[r["pasta"]] = {k: q.get(k) for k in ("ok", "sem", "motivo")}
        anime_testes.contar_qualidade(r["item"], q)
        feitos += 1
        log(f"reconferi {pasta.name} ({r['item']}): {'ok' if q['ok'] else 'RUIM — ' + q['motivo']} (sem {q.get('sem')})")
        if not q["ok"]:
            anime_testes.segurar(pasta, q["motivo"])
        else:
            anime_testes.marcar_conferido(pasta, q)
    return feitos


def juntar(regs):
    """{item: {...}} com o caminho de cada Short em teste até a medida de 48 h."""
    try:
        med = json.loads(MEDIDAS.read_text(encoding="utf-8")).get("medidas_48h", {})
    except (OSError, ValueError):
        med = {}
    try:
        studio = json.loads(STUDIO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        studio = {}
    por = {}
    for r in regs:
        x = por.setdefault(r["item"], {"produzidos": 0, "refeitos_solo": 0, "falhou": 0, "segurados": 0, "postados": 0,
                                       "medidos": 0, "views": [], "ultimo": None, "ruins": [], "subiu_segurado": [], "continuaram": []})
        x["produzidos"] += 1
        x["ultimo"] = r.get("quando")
        if r.get("refeito_solo"):
            x["refeitos_solo"] += 1
        if r.get("falhou"):
            x["falhou"] += 1
        q = r.get("reconferido") or r.get("qualidade") or {}
        if q.get("ok") is False:
            x["ruins"].append(q.get("motivo"))
        if not r.get("pasta"):
            continue
        pj = anime_testes._ler(Path(r["pasta"]) / "postar.json", {})
        segurado = "segurad" in str(pj.get("revisao") or "") and "teste de voz" in str(pj.get("revisao") or "")
        if segurado:
            x["segurados"] += 1
        vid = _video_id(pj.get("posted_url"))
        if vid and segurado:  # segurado no meio de um upload que já tinha começado: está no ar com o áudio ruim
            x["subiu_segurado"].append(f"{Path(r['pasta']).name} ({pj.get('posted_url')})")
        if vid:
            x["postados"] += 1
            rl = (studio.get(vid) or {}).get("ret_lista") or {}
            if rl.get("continuaram") is not None and (rl.get("views_periodo") or 0) >= MIN_VIEWS_RET:
                x["continuaram"].append(float(rl["continuaram"]))
            if vid in med:
                x["medidos"] += 1
                x["views"].append(med[vid].get("views", 0))
    return por


def relatorio(sit, por):
    c = anime_testes.cfg()
    solo = sit.get("solo", {})
    linhas = [f"# Teste gradual de formatos e vozes — {datetime.now():%d/%m %H:%M}", "",
              "Gerado pelo vigia `D:\\video-fila\\avaliar_testes_voz.py` (a cada 3 h). Teste: recapd `bin\\anime_testes.py`, "
              f"config `config\\testes_voz.json` (ligado={c.get('ligado')}, {c['fracao']:.0%} dos Shorts com clone + "
              f"{c['fracao_promovidos']:.0%} pros promovidos).", "",
              f"**Controle (solo):** {solo.get('vitorias', 0)} de {solo.get('testes', 0)} Shorts medidos passaram da mediana "
              f"do canal (taxa {solo.get('taxa', 0.5):.2f}). Promove com >= {c['min_medidas']} medidos e taxa >= solo + "
              f"{c['margem']}; pausa com taxa <= solo - {c['margem']} ou {c['ruins_pausa']} áudios ruins.", "",
              "| Item | Estado | Produzidos | Refeitos solo | Segurados | Postados | Medidos 48 h | Vitórias | Taxa | Views (mediana) | Continuaram (mediana) | Áudio ok/ruim | Falhas |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    ordem = sorted((k for k in sit if k != "solo"), key=lambda k: (-sit[k]["testes"], k))
    for k in ordem:
        s, x = sit[k], por.get(k, {})
        vs = sorted(x.get("views") or [])
        med = vs[len(vs) // 2] if vs else "-"
        cs = sorted(x.get("continuaram") or [])
        ret = f"{cs[len(cs) // 2]:.0f}% ({len(cs)})" if cs else "-"
        linhas.append(f"| {k} | {s['estado']} | {x.get('produzidos', 0)} | {x.get('refeitos_solo', 0)} | "
                      f"{x.get('segurados', 0)} | {x.get('postados', 0)} | {x.get('medidos', 0)} | {s['vitorias']}/{s['testes']} | "
                      f"{s['taxa']:.2f} | {med} | {ret} | {s.get('ok', 0)}/{s.get('ruins', 0)} | {s.get('falhas', 0)} |")
    ruins = [(k, m) for k in ordem for m in (por.get(k, {}).get("ruins") or [])[-3:] if m]
    if ruins:
        linhas += ["", "## Áudios que soaram mal (últimos)", *[f"- {k}: {m}" for k, m in ruins]]
    subiu = [(k, m) for k in ordem for m in por.get(k, {}).get("subiu_segurado") or []]
    if subiu:
        linhas += ["", "## ATENÇÃO: segurados que subiram (o upload já tinha começado) — conferir no Studio",
                   *[f"- {k}: {m}" for k, m in subiu]]
    linhas += ["", "Legenda: *novo* = ainda não saiu; *testando* = saindo, sem medida suficiente; *promovido* = rendeu acima "
               "do solo, sai mais vezes; *pausado* = rendeu abaixo, soou mal ou a dona pausou (config `pausados`)."]
    RELATORIO.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-aviso", action="store_true")
    a = ap.parse_args()
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    regs = _registros()
    est = anime_testes._ler(ESTADO, {})
    n = reconferir(regs, est)
    itens = [f"formato:{k}" for k in anime_testes.formatos()] + [f"voz:{v}" for v in anime_testes.vozes_em_teste(None)]
    itens += [r["item"] for r in regs if r["item"] not in itens]
    sit = anime_testes.situacao(itens)
    por = juntar(regs)
    relatorio(sit, por)
    antes = est.get("estados", {})
    mudou = [(k, antes.get(k), s["estado"]) for k, s in sit.items()
             if k != "solo" and s["estado"] in ("promovido", "pausado") and antes.get(k) != s["estado"]]
    log(f"rodada: {len(regs)} Shorts em teste no registro, {n} reconferido(s), {len(mudou)} mudança(s) de estado")
    if not a.sem_aviso:
        import avisos
        for k, de, para in mudou:
            s = sit[k]
            txt = (f"Teste de voz: <b>{k}</b> foi {'PROMOVIDO — vai sair mais vezes' if para == 'promovido' else 'PAUSADO'} "
                   f"({s['vitorias']} de {s['testes']} Shorts acima da mediana do canal; solo {sit['solo']['taxa']:.2f}; "
                   f"áudio {s.get('ok', 0)} ok / {s.get('ruins', 0)} ruim). Relatório: {RELATORIO}")
            avisos.enviar(txt, "recapd", importante=True, chave=f"testes_voz:{k}:{para}")
        ja = est.setdefault("avisados_subiu", [])
        for k, x in por.items():
            for m in x.get("subiu_segurado") or []:
                if m in ja:
                    continue
                ja.append(m)
                avisos.enviar(f"Teste de voz: o Short {m} ({k}) soou mal e foi segurado, mas o upload já tinha começado e "
                              "ele SUBIU. Conferir no Studio (deixar privado se estiver ruim).", "recapd",
                              importante=True, chave=f"testes_voz:subiu:{m}")
        hoje = f"{datetime.now():%Y-%m-%d}"
        if regs and est.get("resumo_em") != hoje and datetime.now().hour >= 9:
            ativos = [k for k in sit if k != "solo" and sit[k]["testes"]]
            txt = (f"Teste de voz (resumo do dia): {sum(x['produzidos'] for x in por.values())} Shorts em teste até agora, "
                   f"{sum(x['medidos'] for x in por.values())} já medidos em 48 h, {len(ativos)} itens com medida. "
                   f"Relatório: {RELATORIO}")
            avisos.enviar(txt, "recapd", chave=f"testes_voz:resumo:{hoje}")
            est["resumo_em"] = hoje
    est["estados"] = {k: s["estado"] for k, s in sit.items()}
    est["rodada"] = datetime.now().isoformat(timespec="seconds")
    anime_testes._gravar(ESTADO, est)


if __name__ == "__main__":
    main()
