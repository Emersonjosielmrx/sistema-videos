r"""resumo_rodada.py — resumo da RODADA horária no formato que a dona pediu (10/11):
pendentes | postados e feitos DESDE A ÚLTIMA RODADA | balanço (reserva, Kaggle, contas) | melhorador | pesquisador.

    python D:\video-fila\resumo_rodada.py          # imprime e grava a marca da rodada (estado\resumo_rodada.json)
    python D:\video-fila\resumo_rodada.py --ver    # imprime sem mexer na marca

Só leitura de logs/pastas locais e arquivos de estado (nenhuma conta é consultada). Contagem certa de post
(ACOMPANHAMENTO_HORARIO.md): TikTok "OK #N", Instagram soma de "RESUMO Instagram: postados N", solares "PUBLICADO:",
YouTube = uploads_ledger.jsonl.
"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
MARCA = BASE / "estado" / "resumo_rodada.json"
POST = Path(r"D:\postador-de-videos")
MAT = Path(r"D:\hipercool-materiais")
PESQ = MAT / "pesquisador_melhorias"


def _ler(p, padrao=None):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except (OSError, ValueError):
        return padrao


def _linhas_desde(arq, desde):
    """Linhas '[HH:MM:SS] ...' de um log diário depois de `desde` (mesmo dia do arquivo)."""
    try:
        txt = Path(arq).read_text("utf-8", errors="replace").splitlines()
    except OSError:
        return []
    dia = datetime.fromtimestamp(Path(arq).stat().st_mtime).date()
    m_dia = re.search(r"(\d{8})", Path(arq).name)
    if m_dia:
        dia = datetime.strptime(m_dia.group(1), "%Y%m%d").date()
    out = []
    for l in txt:
        m = re.match(r"\[(\d\d:\d\d:\d\d)\]", l)
        if m:
            t = datetime.combine(dia, datetime.strptime(m.group(1), "%H:%M:%S").time())
            if t >= desde:
                out.append(l)
    return out


def _dias(desde):
    d, fim = desde.date(), datetime.now().date()
    while d <= fim:
        yield d
        d += timedelta(days=1)


def postados(desde):
    out = {}
    tk = ig = 0
    for d in _dias(desde):
        tk += sum(1 for l in _linhas_desde(POST / "logs" / f"tiktok_{d:%Y%m%d}.log", desde) if re.search(r"OK #\d+", l))
        for l in _linhas_desde(POST / "logs" / f"instagram_{d:%Y%m%d}.log", desde):
            m = re.search(r"RESUMO Instagram: postados (\d+)", l)
            ig += int(m.group(1)) if m else 0
    out["TikTok"], out["Instagram"] = tk, ig
    # solares: os logs do ms-energy não têm data por linha; o registro HTTP do Instagram tem (sem contar story)
    sol = 0
    try:
        for l in Path(r"D:\projeto-navegador-sem-navegador\logs\instagram_postagens.jsonl").read_text(
                "utf-8", errors="replace").splitlines()[-2000:]:
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if (r.get("ok") and r.get("tipo") != "story" and r.get("quando", "") >= f"{desde:%Y-%m-%d %H:%M:%S}"
                    and re.search(r"advance|globo|msenergy", r.get("conta", ""))):
                sol += 1
    except OSError:
        pass
    out["Solares (reel/carrossel)"] = sol
    yt = 0
    try:
        for l in (POST / "logs" / "uploads_ledger.jsonl").read_text("utf-8", errors="replace").splitlines()[-3000:]:
            try:
                r = json.loads(l)
            except ValueError:
                continue
            t = str(r.get("ts") or r.get("em") or r.get("quando") or "")
            try:
                tt = datetime.fromtimestamp(float(t)) if re.fullmatch(r"[\d.]+", t) else datetime.fromisoformat(t[:19])
            except ValueError:
                continue
            if tt >= desde:
                yt += 1
    except OSError:
        pass
    out["YouTube (subidos/agendados)"] = yt
    return out


def _novos(padrao, desde, pasta=False):
    n = 0
    for p in glob.glob(padrao):
        try:
            # criação (Windows: getctime), não modificação — o postar.json é regravado quando o vídeo é postado
            if os.path.getctime(p) >= desde.timestamp():
                n += 1
        except OSError:
            pass
    return n


def feitos(desde):
    return {
        # pasta <obra>_capN_AAAAMMDD: só as do(s) dia(s) do período (ctime de pasta antiga muda ao mexer)
        "Cortes/Shorts parceiro": sum(_novos(str(MAT / "animes recap" / "shorts" / f"*_{d:%Y%m%d}*" / "postar.json"),
                                             desde) for d in _dias(desde)),
        "Comédia Noturna": _novos(str(MAT / "videos-comentarios" / "*" / "postar.json"), desde),
        "Veo limpos": _novos(str(MAT / "veo" / "limpos" / "*.mp4"), desde),
        "Reels solares": sum(_novos(rf"D:\ms-energy\videos\{p}\*.mp4", desde)
                             for p in ("reels_advance", "reels_globo", "shorts_veo", "shorts")),
        "Longos": _novos(str(MAT / "_longos_postar" / "*" / "*.mp4"), desde),
    }


def balanco():
    b = _ler(BASE / "estado" / "balanco_kaggle.json", {}) or {}
    g, r = b.get("gpus") or {}, b.get("reserva") or {}
    canais = sorted(b.get("canais") or [], key=lambda c: c.get("dias", 99))[:3]
    linhas = [f"Reserva: {r.get('na_meta', '?')}/{r.get('total', '?')} canais com 7 dias; mais vazios: "
              + ", ".join(f"{c['canal']} {c['dias']}d" for c in canais),
              f"Kaggle: curto {g.get('curto_ativas', '?')}/{g.get('curto_total', '?')} | longo "
              f"{g.get('longo_ativas', '?')}/{g.get('longo_total', '?')} (balanço de {str(b.get('em', ''))[11:16]})"]
    pz = _ler(POST / "config" / "instagram_pausas.json", {}) or {}
    ig = ((_ler(POST / "config" / "reuso_plataformas.json", {}) or {}).get("instagram") or {}).get("contas") or {}
    linhas.append(f"Instagram: {len([c for c in ig if c not in pz])} contas ativas, {len(pz)} em pausa/suspensas")
    fila = _ler(POST / "config" / "instagram_criar_fila.json", {}) or {}
    ult = max((v.get("t", 0) for v in fila.values() if v.get("logado")), default=0)
    if ult:
        linhas.append(f"Contas IG novas: última criada {datetime.fromtimestamp(ult):%d/%m}")
    return linhas


def melhorador():
    e = _ler(BASE / "estado" / "central" / "estado.json", {}) or {}
    modo = _ler(r"D:\vps157\modo_tokens.json", {}) or {}
    volta = e.get("ultima_volta", "")
    rod = e.get("rodadas") or {}
    ult = sorted(((v.get("em", ""), k) for k, v in rod.items() if isinstance(v, dict)), reverse=True)[:2]
    parado = ""
    try:
        if volta and datetime.now() - datetime.fromisoformat(volta[:19]) > timedelta(hours=3):
            parado = " — PARADO"
    except ValueError:
        pass
    return [f"Melhorador central: última volta {volta[5:16].replace('T', ' ')}{parado}; modo tokens "
            f"{modo.get('modo', '?')}; últimas aplicações: " + (", ".join(f"{k} {em[5:16]}" for em, k in ult) or "nenhuma")]


def pesquisador(desde):
    regs = []
    try:
        for l in (PESQ / "motor_registro.jsonl").read_text("utf-8", errors="replace").splitlines()[-400:]:
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if r.get("inicio", "")[:19] >= desde.isoformat(timespec="seconds"):
                regs.append(r)
    except OSError:
        pass
    ok = [r for r in regs if r.get("status") == "ok"]
    pend = {}
    for arq in glob.glob(str(PESQ / "ENTREGAS" / "*.md")):
        pend[Path(arq).stem] = Path(arq).read_text("utf-8", errors="replace").count("[ ] PENDENTE")
    impl = _ler(PESQ / "implantados.json", []) or []
    repr_ = _ler(PESQ / "reprovados.json", []) or []
    impl_novos = [i for i in impl if str(i.get("data", "")) >= desde.strftime("%Y-%m-%d")]
    return [f"Pesquisador: {len(regs)} pesquisas desde a última rodada ({len(ok)} ok); pendentes de avaliar: "
            + ", ".join(f"{k} {v}" for k, v in pend.items()),
            f"Implantados {len(impl)} no total ({len(impl_novos)} hoje) | reprovados {len(repr_)}"]


PENDENTES = BASE / "PENDENTES_DONA.md"


def maquinas():
    """Ocupação de cada PC (última rodada do controlador) e dos celulares (celulares_medida.json)."""
    out = []
    try:
        ls = (BASE / "logs" / f"controlador_{datetime.now():%Y%m%d}.log").read_text("utf-8", errors="replace").splitlines()
        ult = next((l for l in reversed(ls) if re.search(r"\] pc1: .*\| pc2: ", l)), "")
        corpo = re.sub(r"^\[[^]]*\]\s*", "", ult)
        for m in re.finditer(r"(?:^| \| )([\w-]+): (.*?)(?= \| [\w-]+: (?:ocupado|LIVRE|livre|parado|fora)|$)", corpo):
            out.append(f"{m.group(1)}: {m.group(2)[:80]}")
    except OSError:
        pass
    nomes = {l.split(":")[0] for l in out}
    cel = _ler(BASE / "estado" / "celulares_medida.json", {}) or {}
    for k, v in cel.items():
        if k not in nomes:
            out.append(f"{k}: {'LIVRE' if v.get('ocioso') else 'PARADO'} — {str(v.get('motivo', ''))[:60]}")
    livres = [l.split(":")[0] for l in out if re.match(r"[\w-]+: (LIVRE|PARADO)", l)]
    return out, livres


def erros_painel():
    try:
        sys.path.insert(0, str(BASE))
        import painel_controlador as pc
        r = pc.api_problemas({})
        lst = r.get("problemas", r) if isinstance(r, dict) else r
        return [f"[{x.get('nivel')}] {x.get('titulo')}" for x in (lst or [])][:8]
    except Exception as e:  # noqa: BLE001
        return [f"painel não respondeu ({type(e).__name__})"]


def telegram(desde):
    out = []
    try:
        for l in (BASE / "estado" / "avisos.jsonl").read_text("utf-8", errors="replace").splitlines()[-500:]:
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if r.get("em", "") >= desde.isoformat(timespec="seconds") and r.get("situacao") == "enviado":
                out.append(f"{r.get('origem')}: {' '.join(str(r.get('texto', '')).split())[:110]}")
    except OSError:
        pass
    return out


def aprendizado():
    pi = BASE / "aprendizado" / "PARA_IMPLEMENTAR.md"
    try:
        txt = pi.read_text("utf-8", errors="replace")
        return [f"Aprendizado: {txt.count('- [ ]')} itens para implementar, {txt.count('- [x]')} feitos (PARA_IMPLEMENTAR.md)"]
    except OSError:
        return []


def pendentes():
    """Lista curta mantida à mão em PENDENTES_DONA.md (uma linha '- ' por pendência; apagar quando resolver)."""
    try:
        return [l[2:].strip() for l in PENDENTES.read_text("utf-8").splitlines() if l.startswith("- ")]
    except OSError:
        return []


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    m = _ler(MARCA, {}) or {}
    agora = datetime.now()
    try:
        desde = datetime.fromisoformat(m["ultima"])
    except (KeyError, ValueError):
        desde = agora - timedelta(hours=1)
    if agora - desde > timedelta(hours=26):
        desde = agora - timedelta(hours=24)
    print(f"RODADA {agora:%d/%m %H:%M} (desde {desde:%d/%m %H:%M})")
    meia_noite = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    p, f = postados(desde), feitos(desde)
    pd, fd = postados(meia_noite), feitos(meia_noite)
    print(f"POSTADOS desde a última rodada {sum(p.values())} | hoje {sum(pd.values())}: "
          + " | ".join(f"{k} {v}/{pd[k]}" for k, v in p.items()))
    print(f"FEITOS desde a última rodada {sum(f.values())} | hoje {sum(fd.values())}: "
          + " | ".join(f"{k} {v}/{fd[k]}" for k, v in f.items()))
    print("  (número/número = desde a última rodada / total do dia)")
    print("BALANÇO:")
    for l in balanco() + melhorador() + pesquisador(desde) + aprendizado():
        print(f"  - {l}")
    maq, livres = maquinas()
    print("MÁQUINAS" + (f" (LIVRES/PARADAS: {', '.join(livres)})" if livres else " (todas ocupadas)") + ":")
    for l in maq:
        print(f"  - {l}")
    print("ERROS DO PAINEL (corrigir):")
    for l in erros_painel() or ["nenhum"]:
        print(f"  - {l}")
    tg = telegram(desde)
    print(f"TELEGRAM desde a última rodada ({len(tg)}):")
    for l in tg[-8:]:
        print(f"  - {l}")
    pend = pendentes()
    print("PENDENTE:" + ("" if pend else " nada aberto no log"))
    for l in pend:
        print(f"  - {l}")
    if "--ver" not in sys.argv:
        MARCA.parent.mkdir(parents=True, exist_ok=True)
        MARCA.write_text(json.dumps({"ultima": agora.isoformat(timespec="seconds")}), encoding="utf-8")


if __name__ == "__main__":
    main()
