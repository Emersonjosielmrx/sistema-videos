"""resumo_notebooks.py — RESUMO DO DIA do trabalho dos notebooks (X200MA e Acer) no Telegram (dona, 23/10/2026).

Só LÊ logs e configs (nada de ssh, nada muda): de 00h até agora (horário de Brasília), por notebook, quantas vezes
abriu o Chrome de uma conta e pra quê (postar, Flow, login), quantas vezes o trabalho ficou no PC1 e por quê, os likes
do telão, as quedas/voltas do vigia mútuo e o que falta de login (Google e TikTok) com a próxima conta da fila.

    python resumo_notebooks.py             # monta e manda pelo portão (avisos.py)
    python resumo_notebooks.py --simular   # só mostra o texto, não manda nada
O vigia geral chama 1x por dia, a partir das 21 h (SUBVIGIAS "resumo_notebooks").
"""
import ast
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
POSTADOR = Path(r"D:\postador-de-videos")
LOG_MAQ = POSTADOR / "logs" / "maquina_remota.log"
VITRINE_LOG = BASE / "logs" / "vitrine.log"
FILA = POSTADOR / "config" / "netbooks_fila.json"
LOGINS = POSTADOR / "config" / "netbooks_logins.json"
TIKTOK = POSTADOR / "config" / "tiktok_notebooks.json"
LOGAR_LISTA = POSTADOR / "bin" / "netbooks" / "logar_lista.py"
PASTAS_LOG = [POSTADOR / "logs", Path(r"D:\recapd-ambientes\producao\logs"), Path(r"D:\manhwa-react\logs"),
              Path(r"D:\veo\logs"), Path(r"D:\veo\beta\logs")]
MAQUINAS = {"x200ma": "X200MA", "acer": "Acer", "sti": "STI"}
BRT = timezone(timedelta(hours=-3))
LIKE = {"sem_botao": "botão de like não apareceu", "video_ja_fechou": "vídeo já tinha fechado",
        "erro": "falha de conexão com o telão"}
TT = {"codigo": "esperando o código do e-mail", "nao_logou": "não entrou", "sem_conta": "sem conta no TikTok"}


def hoje():
    return datetime.now(BRT)


def _hora(s):
    h, m, *seg = (int(x) for x in s.split(":"))
    return h * 3600 + m * 60 + (seg[0] if seg else 0)


def linhas_de_hoje(caminho):
    """Linhas do arquivo escritas hoje. Aceita '[23/10 HH:MM:SS]' e '[HH:MM:SS]' (este último: lendo de trás pra
    frente, a hora 'pular pra cima' = passou da meia-noite pra ontem)."""
    agora = hoje()
    try:
        if datetime.fromtimestamp(caminho.stat().st_mtime, BRT).date() != agora.date():
            return []
        with open(caminho, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 3_000_000))
            texto = f.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    dia, out, ult = agora.strftime("%d/%m"), [], None
    for ln in reversed(texto.splitlines()):
        m = re.match(r"\[(\d\d/\d\d) (\d\d:\d\d(?::\d\d)?)\]", ln) or re.match(r"\[()(\d\d:\d\d:\d\d)\]", ln)
        if m:
            if m.group(1) and m.group(1) != dia:
                break
            t = _hora(m.group(2))
            if ult is not None and t > ult + 3600:
                break
            ult = t
        out.append(ln)
    return out[::-1]


def logs_dos_postadores():
    """{arquivo: linhas de hoje} dos logs que podem falar dos notebooks."""
    out = {}
    for pasta in PASTAS_LOG:
        if not pasta.is_dir():
            continue
        for arq in pasta.rglob("*.log"):
            if arq == LOG_MAQ:
                continue
            ls = linhas_de_hoje(arq)
            if any("pelo Chrome do" in x or "notebook livre" in x or "tento na próxima máquina" in x for x in ls):
                out[arq] = ls
    return out


def _plataforma(arq, linha):
    if "[flow]" in linha:
        return "Flow"
    if "enviando pelo Chrome do" in linha:
        return "YouTube"
    nome = arq.name.lower()
    return "TikTok" if "tiktok" in nome else "Instagram" if "insta" in nome else "postagem"


def uso_dos_postadores(logs):
    """Trabalhos feitos em cada notebook, falhas lá, e as vezes que ficou no PC1 (com o motivo)."""
    feito = {m: Counter() for m in MAQUINAS}
    falhou = Counter()
    no_pc, motivos = 0, Counter()
    for arq, ls in logs.items():
        for i, ln in enumerate(ls):
            m = re.search(r"pelo Chrome do (\w+)", ln)
            if m and m.group(1).lower() in feito:
                feito[m.group(1).lower()][_plataforma(arq, ln)] += 1
            m = re.search(r"falhou no (\w+)", ln)
            if m and "próxima máquina" in ln and m.group(1).lower() in MAQUINAS:
                falhou[m.group(1).lower()] += 1
            if "nenhum notebook livre" in ln:
                no_pc += 1
                porque = set()
                for ant in ls[max(0, i - 4):i]:
                    if "OCUPADO" in ant:
                        porque.add("notebooks ocupados com outra conta")
                    elif "não respondeu" in ant:
                        porque.add("notebook não respondeu")
                    elif re.search(r"\b(x200ma|acer)\b", ant, re.I) and "Chrome do" not in ant:
                        porque.add("erro ao abrir o Chrome")
                motivos.update(porque or {"motivo não anotado"})
    return feito, falhou, no_pc, motivos


def chrome_aberto():
    """{maquina: (vezes, contas distintas, tentativas TikTok)} pelo maquina_remota.log."""
    vezes, contas, tt = Counter(), {m: set() for m in MAQUINAS}, Counter()
    for ln in linhas_de_hoje(LOG_MAQ):
        m = re.search(r"\] (\w+): Chrome de (\S+) pronto", ln)
        if m and m.group(1) in contas:
            vezes[m.group(1)] += 1
            contas[m.group(1)].add(m.group(2))
        m = re.search(r"tiktok \S+ no (\w+):", ln)
        if m and m.group(1) in contas:
            tt[m.group(1)] += 1
    return {m: (vezes[m], len(contas[m]), tt[m]) for m in MAQUINAS}


def conferidas_hoje():
    """Contas do Google conferidas hoje em cada notebook (netbooks_logins.json, campo 'em')."""
    dia, c = hoje().strftime("%Y-%m-%d"), Counter()
    for perfil, maqs in _json(LOGINS).items():
        if perfil.startswith("_") or not isinstance(maqs, dict):
            continue
        for m, v in maqs.items():
            if m in MAQUINAS and isinstance(v, dict) and str(v.get("em", "")).startswith(dia):
                c[m] += 1
    return c


def telao_e_vigia():
    likes, quedas, voltas = Counter(), Counter(), Counter()
    for ln in linhas_de_hoje(VITRINE_LOG):
        m = re.search(r"telão curtir \S+: (\w+)", ln)
        if m:
            likes[m.group(1)] += 1
        m = re.search(r"vigia mútuo: .*?(\w+) (SEM SINAL|VOLTOU)", ln)
        if m:
            (quedas if m.group(2) == "SEM SINAL" else voltas)[m.group(1).lower()] += 1
    return likes, quedas, voltas


def _json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def contas_da_lista():
    """A ordem da dona (CONTAS do logar_lista.py), lida sem executar o arquivo."""
    try:
        for no in ast.parse(LOGAR_LISTA.read_text(encoding="utf-8")).body:
            if isinstance(no, ast.Assign) and any(getattr(t, "id", "") == "CONTAS" for t in no.targets):
                return [e.split("@")[0].lower() for e in ast.literal_eval(no.value)]
    except (OSError, SyntaxError, ValueError):
        pass
    return []


def login_google():
    fila, contas = _json(FILA), contas_da_lista()
    feitas, puladas, atual = set(fila.get("feitas", [])), set(fila.get("puladas", [])), fila.get("atual")
    prox = next((c for c in contas if c not in feitas and c not in puladas and c != atual), None)
    txt = f"Login Google: {len(feitas & set(contas)) if contas else len(feitas)} de {len(contas) or '?'} contas feitas"
    if atual:
        txt += f"; na vez agora: {atual}"
    txt += f"; próxima: {prox}" if prox else "; fila terminada"
    return txt + (f" ({len(puladas)} pulada(s))" if puladas else "")


def fila_tiktok():
    """Próximas (conta, notebook) do TikTok automático; usa a regra do próprio tiktok_notebooks.py se der."""
    try:
        sys.path.insert(0, str(POSTADOR / "bin" / "netbooks"))
        sys.path.insert(0, str(POSTADOR / "bin"))
        import tiktok_notebooks
        return tiktok_notebooks.fila()
    except Exception:  # noqa: BLE001 — sem o módulo: aproxima pelo arquivo de conferências
        return [(p, m) for p, maqs in _json(LOGINS).items() if not p.startswith("_") and isinstance(maqs, dict)
                for m, v in maqs.items() if m in MAQUINAS and isinstance(v, dict) and v.get("youtube")
                and not v.get("tiktok")]


def login_tiktok():
    logados = sum(1 for p, maqs in _json(LOGINS).items() if not p.startswith("_") and isinstance(maqs, dict)
                  for m, v in maqs.items() if m in MAQUINAS and isinstance(v, dict) and v.get("tiktok"))
    inicio = hoje().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    hoje_tt = [(p, m, v.get("resultado")) for p, maqs in _json(TIKTOK).items() if isinstance(maqs, dict)
               for m, v in maqs.items() if isinstance(v, dict) and v.get("t", 0) >= inicio]
    fila = fila_tiktok()
    txt = f"TikTok: {logados} login(s) feito(s) nos notebooks, faltam {len(fila)}"
    if fila:
        txt += f"; próxima: {fila[0][0]} ({MAQUINAS.get(fila[0][1], fila[0][1])})"
    linhas = [txt]
    codigo = [f"{p} ({MAQUINAS.get(m, m)})" for p, m, r in hoje_tt if r == "codigo"]
    if codigo:
        linhas.append("  esperando você digitar o código: " + ", ".join(codigo))
    outros = Counter(TT.get(r, r) for p, m, r in hoje_tt if r not in ("codigo", "ok", "logou"))
    if outros:
        linhas.append("  tentativas de hoje que não deram: " + ", ".join(f"{k} {v}" for k, v in outros.items()))
    return linhas


METRICAS = POSTADOR / "_analise" / "metricas_studio.json"
RET_MIN_VIEWS = 200  # com menos views o "continuaram" oscila demais (3 views = 100%)


def retencao():
    """Retenção lida em lote (metricas_rede, campo ret_lista) nos últimos 3 dias: quem mais desliza / mais segura e a
    média de "continuaram assistindo" por canal. Só Shorts com RET_MIN_VIEWS ou mais."""
    limite = (hoje() - timedelta(days=3)).isoformat(timespec="minutes")
    vs = []
    for vid, d in _json(METRICAS).items():
        r = d.get("ret_lista") if isinstance(d, dict) else None
        if not r or r.get("continuaram") is None or (r.get("views_periodo") or 0) < RET_MIN_VIEWS \
                or str(r.get("em", "")) < limite:
            continue
        titulo = d.get("titulo") or ""
        if titulo.endswith(".mp4"):  # alguns registros guardam o nome do arquivo no lugar do título
            titulo = ""
        vs.append((r["continuaram"], d.get("canal_slug") or "?", (titulo or vid)[:45], r))
    if not vs:
        return []
    vs.sort(key=lambda x: x[0])
    ln = [f"Retenção (últimos 3 dias, {len(vs)} Shorts com {RET_MIN_VIEWS}+ views; % que continuou assistindo):"]
    fmt = lambda x: f"  {x[0]:.0f}% · {x[1]} · {x[2]} ({x[3].get('dur_media') or 0:.0f} s, {x[3]['views_periodo']:.0f} views)"
    ln.append(" mais deslizados:")
    ln.extend(fmt(x) for x in vs[:3])
    if len(vs) > 3:
        ln.append(" mais assistidos:")
        ln.extend(fmt(x) for x in vs[::-1][:min(3, len(vs) - 3)])
    por_canal = {}
    for c, slug, _t, _r in vs:
        por_canal.setdefault(slug, []).append(c)
    media = sorted(((sum(v) / len(v), k, len(v)) for k, v in por_canal.items()), reverse=True)
    ln.append(" por canal: " + ", ".join(f"{k} {m:.0f}% ({n})" for m, k, n in media))
    return ln


def _lista(c):
    return ", ".join(f"{k} {v}" for k, v in c.most_common()) if c else ""


def montar():
    agora = hoje()
    abertos, conf = chrome_aberto(), conferidas_hoje()
    feito, falhou, no_pc, motivos = uso_dos_postadores(logs_dos_postadores())
    likes, quedas, voltas = telao_e_vigia()
    ln = [f"Resumo dos notebooks — {agora:%d/%m} (00h até {agora:%H:%M})"]
    for m, nome in MAQUINAS.items():
        vezes, contas, tt = abertos[m]
        ln.append(f"{nome}: abriu o Chrome {vezes} vez(es), de {contas} conta(s)")
        partes = []
        if feito[m]:
            partes.append("trabalhou: " + _lista(feito[m]))
        if conf[m] or tt:
            partes.append(f"login: {conf[m]} conta(s) conferida(s), {tt} tentativa(s) de TikTok")
        if falhou[m]:
            partes.append(f"deu erro {falhou[m]}x e passou pra outra máquina")
        if quedas[m] or voltas[m]:
            partes.append(f"saiu do ar {quedas[m]}x, voltou {voltas[m]}x")
        ln.append("  " + (" · ".join(partes) if partes else "sem trabalho registrado fora isso"))
    if no_pc:
        ln.append(f"Ficou no PC1: {no_pc} vez(es)" + (f" ({_lista(motivos)})" if motivos else ""))
    else:
        ln.append("Ficou no PC1: nenhuma vez")
    ok = likes.pop("ok", 0)
    ruins = Counter()
    for k, v in likes.items():
        ruins[LIKE.get(k, k)] += v
    ln.append(f"Likes no telão: {ok} certo(s), {sum(ruins.values())} falha(s)"
              + (f" ({_lista(ruins)})" if ruins else ""))
    ln.append(login_google())
    ln.extend(login_tiktok())
    ln.extend(retencao())
    return "\n".join(ln)


def main(args):
    texto = montar()
    print(texto)
    if "--simular" in args:
        print("\n(simulação: nada foi enviado)")
        return
    sys.path.insert(0, r"D:\video-fila")
    import avisos
    mid = avisos.enviar(texto, "resumo dos notebooks", importante=True, html_ok=False,
                        chave=f"resumo-notebooks-{hoje():%Y-%m-%d}")
    print(f"[{time.strftime('%d/%m %H:%M:%S')}] enviado: {bool(mid)}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
