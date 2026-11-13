"""trava_conta.py — trava central de canal do YouTube por TELA de punição (05/11/2026).

Dona 05/11 ("corrija pra isso não acontecer nunca mais, assim não vamos perder os outros canais"): os robôs só
conheciam as telas da época em que foram feitos. Tela nova do YouTube virava "falha" e eles tentavam de novo a cada
rodada, sem fim — o que o próprio YouTube chama de "tentar burlar" ("poderemos encerrar sua conta"):
    inovare_ita    REMOVIDO por nudez           -> 54 entradas depois de removido
    inovare_hindi  "Muitos avisos" (diretrizes) -> 117 tentativas de envio
    mundoquenaoexiste strike de direitos 01/11  -> 85 tentativas
    Assist-IA / inovare br / CenaReact recursos avançados negados -> ~70 tentativas de fixar/A-B/relacionado

Agora TODO print de falha dos robôs do YouTube (youtube_web_poster._shot, usado também pelo youtube_studio_extras,
collabs, capas_depois, postar_longos...) passa por `ver_tela`: se a página mostra uma dessas telas, o canal é gravado
em config/contas_travadas.json (1 aviso no Telegram, uma vez só) e `checar` (chamado no _canal_e_mapa, porta de
entrada de todos) recusa qualquer automação nesse canal até a data — ou até a dona apagar a linha.

    tipo        o que trava                        até
    removido    tudo                               a dona apagar (contestação aceita)
    strike      tudo (3 strikes = canal E os ligados a ele removidos)   a dona apagar (depois de ver o strike no Studio)
    avisos      envio de vídeo                     +7 dias (o bloqueio do YouTube dura até os avisos vencerem)
    negado      só recursos avançados (fixar comentário, teste A/B, vídeo relacionado) — ver youtube_studio_extras

Desligar (não recomendado): YT_TRAVA_CONTA=0. Ver: python trava_conta.py
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "config"
ARQ = CONFIG / "contas_travadas.json"
NEGADOS = CONFIG / "recursos_negados.json"
TELAS = CONFIG.parent / "logs" / "telas_falha.jsonl"

REMOVIDO = re.compile(r"foi removido do YouTube|canal .{0,60}foi (removido|encerrado)|conta .{0,30}foi encerrada|"
                      r"channel .{0,60}(has been|was) (removed|terminated)|account (has been )?terminated", re.I)
STRIKE = re.compile(r"removido devido a uma solicitação de remoção por direitos autorais|advertência por violação de "
                    r"direitos autorais|removed due to a copyright|copyright strike|Strike \d\s", re.I)
AVISOS = re.compile(r"muitos avisos|too many warnings|many warnings", re.I)
NEGADO = re.compile(r"recursos avançados não estão disponíveis|perdeu o acesso aos recursos avançados|"
                    r"advanced features (are )?(not|un)available|lost access to advanced features|"
                    r"contestação relacionada aos recursos avançados foi negada|acesso aos recursos avançados está bloqueado|"
                    r"appeal (related to|for) advanced features (was|has been) (denied|rejected)", re.I)
MESES = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6, "jul": 7, "ago": 8, "set": 9, "out": 10,
         "nov": 11, "dez": 12}


def _ligado():
    return os.environ.get("YT_TRAVA_CONTA", "1") != "0"


def _ler(arq):
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar(arq, d):
    arq.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _avisar(msg):
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(msg, "youtube-trava", importante=True, html_ok=False)
    except Exception:  # noqa: BLE001
        pass


def classificar(txt):
    """'removido' | 'strike' | 'avisos' | 'negado' | None, pelo texto da página."""
    if not txt:
        return None
    if REMOVIDO.search(txt):
        return "removido"
    if STRIKE.search(txt):
        return "strike"
    if AVISOS.search(txt):
        return "avisos"
    if NEGADO.search(txt):
        return "negado"
    return None


def marcar(slug, nome, tipo, txt="", print_=None):
    """Grava a trava (1 aviso por canal+tipo). Devolve a entrada."""
    if tipo == "negado":
        m = re.search(r"novamente (?:em|a partir de) (\d{1,2}) de (\w{3})\w* de (\d{4})", txt or "", re.I)
        ate = f"{m.group(3)}-{MESES.get(m.group(2).lower()[:3], 1):02d}-{int(m.group(1)):02d}" if m else ""
        d = _ler(NEGADOS)
        novo = slug not in d
        d[slug] = {"ate": ate, "em": datetime.now().isoformat("T", "minutes"), **({"obs": d[slug].get("obs")}
                                                                                   if not novo and d[slug].get("obs") else {})}
        _gravar(NEGADOS, d)
        if novo:
            _avisar(f"⚠️ YouTube: {nome} está SEM recursos avançados até {ate or '?'} — o robô parou de tentar "
                    f"fixar comentário / teste A/B / vídeo relacionado nele (contestar no Studio).")
        return d[slug]
    d = _ler(ARQ)
    ant = d.get(slug) or {}
    ate = (datetime.now() + timedelta(days=7)).date().isoformat() if tipo == "avisos" else ""
    d[slug] = {"nome": nome, "tipo": tipo, "ate": ate, "desde": ant.get("desde") or datetime.now().isoformat("T", "minutes"),
               "print": str(print_ or ""), "trecho": re.sub(r"\s+", " ", txt or "")[:300]}
    _gravar(ARQ, d)
    if ant.get("tipo") != tipo:
        o_que = {"removido": "foi REMOVIDO pelo YouTube", "strike": "levou STRIKE de direitos autorais",
                 "avisos": "está com 'Muitos avisos' (envio bloqueado)"}[tipo]
        _avisar(f"🛑 YouTube: {nome} {o_que}. Parei TODA automação nesse canal "
                f"{'por 7 dias' if ate else 'até você liberar'} pra não parecer tentativa de burlar "
                f"(isso pode levar os canais ligados). Print: {print_}. Liberar: apagar a linha em "
                f"config\\contas_travadas.json")
    return d[slug]


def checar(slug, para="tudo"):
    """Motivo da trava (str) ou None. para='envio' também barra 'avisos'; 'tudo' barra removido/strike/avisos."""
    if not _ligado() or not slug:
        return None
    x = _ler(ARQ).get(slug)
    if not x:
        return None
    if x.get("ate") and datetime.now().date().isoformat() >= x["ate"]:
        return None
    return f"{x['tipo']} desde {x.get('desde', '?')[:10]}" + (f" até {x['ate']}" if x.get("ate") else
                                                              " (a dona libera apagando a linha em contas_travadas.json)")


def ver_tela(pg, slug, nome, print_=None):
    """Lê a página e trava o canal se for tela de punição. Nunca levanta exceção."""
    if not _ligado() or not slug:
        return None
    try:
        txt = pg.inner_text("body", timeout=3000)
    except Exception:  # noqa: BLE001
        return None
    tipo = classificar(txt)
    try:  # registro de TODA tela de falha: tela nova do YouTube aparece no resumo (python trava_conta.py telas)
        try:
            dlg = " | ".join(pg.locator("tp-yt-paper-dialog:visible, ytcp-dialog:visible, [role=dialog]:visible, "
                                        "ytcp-uploads-dialog:visible").all_inner_texts())[:400]
        except Exception:  # noqa: BLE001
            dlg = ""
        with open(TELAS, "a", encoding="utf-8") as f:
            f.write(json.dumps({"em": datetime.now().isoformat("T", "seconds"), "canal": slug, "tipo": tipo,
                                "print": str(print_ or ""), "dialogo": re.sub(r"\s+", " ", dlg),
                                "pagina": re.sub(r"\s+", " ", txt)[:300]}, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass
    if tipo:
        try:
            marcar(slug, nome, tipo, txt, print_)
        except Exception:  # noqa: BLE001
            pass
    return tipo


def resumo_telas(dias=3):
    """Agrupa as telas de falha dos últimos dias pelo texto do diálogo: o que se repete = tela nova a tratar."""
    from collections import Counter
    lim = (datetime.now() - timedelta(days=dias)).isoformat()
    cont, exemplo = Counter(), {}
    try:
        linhas = TELAS.read_text(encoding="utf-8").splitlines()
    except OSError:
        linhas = []
    for l in linhas:
        try:
            x = json.loads(l)
        except ValueError:
            continue
        if x["em"] < lim:
            continue
        chave = re.sub(r"\d+", "#", (x.get("dialogo") or x.get("pagina") or "")[:90])
        cont[chave] += 1
        exemplo[chave] = x
    for chave, n in cont.most_common(25):
        x = exemplo[chave]
        print(f"{n:4}x  [{x.get('tipo') or '-'}] {chave}\n       ex.: {x['canal']} {x['print']}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["telas"]:
        resumo_telas(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
        sys.exit()
    for s, x in _ler(ARQ).items():
        print(f"{s:28} {x['tipo']:9} desde {x.get('desde', '')[:16]} até {x.get('ate') or 'a dona liberar'}")
    for s, x in _ler(NEGADOS).items():
        print(f"{s:28} negado    até {x.get('ate') or '?'} (só recursos avançados)")
