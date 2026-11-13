"""rampa_canais.py — teto de uploads POR CANAL que sobe com dados (dono, 22/10).

Pedido do dono: "meta de 3 vídeos por dia, mas tem canais com o limite da conta já desbloqueado que podem
postar mais — verificar e deixar os que vão muito bem postarem 4, 5 ou mais, aumentando conforme fizer
sentido pro algoritmo do YouTube".

Como funciona:
- O teto da política continua o de sempre (4/canal/dia). Cada canal pode ter DEGRAUS EXTRAS aqui
  (`config\\rampa_canais.json`), que o `politica.teto_canal`/`cota_restante` somam ao teto.
- SOBE +1 degrau (até +4 → teto 8) quando, por 3+ dias desde a última mudança: (a) o canal ENCHEU o teto
  atual em pelo menos 2 dos últimos 3 dias (tem demanda e a conta aguentou); (b) não pegou "limite diário"
  (não está em config\\limite_diario.json); (c) RENDE: mediana de views em 48 h >= mediana geral dos canais
  medidos, ou pct_1000 >= 10 (aprendizado_global). Um degrau por vez = crescimento gradual, bom pro algoritmo.
- DESCE -1 na hora se o canal pegar "limite diário de envios" (politica.marcar_limite_diario chama descer()).
- Canal que o dono JÁ SABE que está desbloqueado: python bin/rampa_canais.py --subir <canal> [degraus]
  (seed manual; a subida automática continua a partir dali). --status mostra tudo; --rodar avalia agora.

Quem roda: notificar_telegram chama rodar() 1x/dia (guardado por data). Nada aqui posta nem abre navegador.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import politica  # noqa: E402

ESTADO = politica.CONFIG_DIR / "rampa_canais.json"
APREND = Path(r"D:\postador-de-videos\_analise\aprendizado_global.json")
MAX_EXTRA = 4          # teto efetivo máximo = política (4) + 4 = 8/dia
DIAS_ENTRE_DEGRAUS = 3  # sobe no máximo 1 degrau a cada 3 dias
DIAS_CHEIOS = 2         # precisa ter enchido o teto atual em >= 2 dos últimos 3 dias
# 29/10 dona: "verifiquei no YouTube quase todos os canais pra colocar mais vídeos e maiores — documente como
# liberados pra postar à vontade; só basta subirem na escada, cada dia postando mais, pra não encher de uma vez".
# Canal LIBERADO (--liberar): sobe 1 degrau POR DIA (sem exigir rendimento), até +8 (teto 12/dia); desce igual.
MAX_EXTRA_LIBERADO = 8
# 29/10 dona: "quando o último vídeo parou de crescer, porque o YouTube parou de veicular, aí pode postar mais" —
# +1 vaga HOJE se o canal ganhou nas últimas 6 h menos de 25% do que costuma ganhar em 6 h (média das 24 h antes),
# com média de pelo menos 30 views/6 h (canal parado de vez não é sinal). Fonte: painel\historico.jsonl (3 em 3 h).
HISTORICO = Path(r"D:\postador-de-videos\painel\historico.jsonl")
LOG_ESTAGNACAO = politica.CONFIG_DIR.parent / "logs" / "rampa_estagnacao.log"


def teto_extra(c):
    return MAX_EXTRA_LIBERADO if c.get("liberado") else MAX_EXTRA


def _ganhos_6h(slug):
    """(ganho das últimas ~6 h, média de ganho por 6 h nas 24 h anteriores) do canal, ou None sem dados."""
    pontos = []
    try:
        for linha in HISTORICO.read_text(encoding="utf-8").splitlines()[-4000:]:
            if f'"slug": "{slug}"' in linha:
                r = json.loads(linha)
                t = politica._dt(r.get("ts") or "")
                if t:
                    pontos.append((t, int(r.get("views") or 0)))
    except (OSError, ValueError):
        return None
    if len(pontos) < 4:
        return None
    pontos.sort()
    fim_t, fim_v = pontos[-1]
    if (politica.agora() - fim_t).total_seconds() > 8 * 3600:
        return None  # coleta parada: sem sinal
    def _em(h):
        alvo = fim_t.timestamp() - h * 3600
        return min(pontos, key=lambda p: abs(p[0].timestamp() - alvo))
    t6, v6 = _em(6)
    t30, v30 = _em(30)
    if (fim_t - t6).total_seconds() < 4 * 3600 or (t6 - t30).total_seconds() < 18 * 3600:
        return None
    janela = (t6 - t30).total_seconds() / (6 * 3600)
    return fim_v - v6, (v6 - v30) / janela


def bonus_estagnacao(canal_id):
    """1 se o canal (cred) estagnou hoje (vaga extra), 0 senão. Decisão gravada 1x por dia e por canal (vigilância)."""
    d = _ler()
    c = d["canais"].get(canal_id) or {}
    hoje = politica.agora().date().isoformat()
    if c.get("bonus_dia") == hoje:
        return 1
    if c.get("bonus_negado") == politica.agora().strftime("%Y-%m-%dT%H"):
        return 0  # já avaliado nesta hora
    cad = (politica.ler_json(politica.CONFIG_DIR / "canais.json", {}).get("canais") or {})
    slug = next((k for k, x in cad.items() if isinstance(x, dict) and canal_id in (x.get("creds") or [])), None)
    g = _ganhos_6h(slug) if slug else None
    c = d["canais"].setdefault(canal_id, {"extra": 0})
    if g and g[1] >= 30 and g[0] < 0.25 * g[1]:
        c["bonus_dia"] = hoje
        msg = f"{slug}: últimas 6 h +{g[0]} views x média {g[1]:.0f}/6 h -> o YouTube parou de entregar: +1 vaga hoje"
        _gravar(d)
        try:
            LOG_ESTAGNACAO.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_ESTAGNACAO, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now():%d/%m %H:%M}] {msg}\n")
        except OSError:
            pass
        return 1
    c["bonus_negado"] = politica.agora().strftime("%Y-%m-%dT%H")
    _gravar(d)
    return 0


# 30/10 dona: "se um vídeo ainda está sendo viralizado e postamos outro, aquele primeiro para" — o contrário do bônus de
# estagnação: canal que ganhou nas últimas 6 h pelo menos VIRAL_X vezes o que costuma ganhar (e no mínimo VIRAL_MIN
# views) segura novos envios até esfriar, por no máximo VIRAL_MAX_H horas desde que começou a segurar.
VIRAL_X = 2.0
VIRAL_MIN = 300
VIRAL_MAX_H = 18


def segurar_viral(canal_id):
    """Motivo (texto) se o canal deve segurar novos envios porque um vídeo dele está decolando agora; None senão."""
    cad = (politica.ler_json(politica.CONFIG_DIR / "canais.json", {}).get("canais") or {})
    slug = next((k for k, x in cad.items() if isinstance(x, dict) and canal_id in (x.get("creds") or [])), None)
    g = _ganhos_6h(slug) if slug else None
    d = _ler()
    c = d["canais"].get(canal_id) or {}
    agora = politica.agora()
    desde = politica._dt(c.get("viral_desde") or "")
    if not g or g[0] < max(VIRAL_MIN, VIRAL_X * g[1]):
        if desde:  # esfriou: solta
            c.pop("viral_desde", None)
            d["canais"][canal_id] = c
            _gravar(d)
        return None
    if desde and (agora - desde).total_seconds() > VIRAL_MAX_H * 3600:
        return None  # segurou o máximo; volta a postar mesmo crescendo
    if not desde:
        c["viral_desde"] = agora.isoformat(timespec="seconds")
        d["canais"][canal_id] = c
        _gravar(d)
        try:
            LOG_ESTAGNACAO.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_ESTAGNACAO, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now():%d/%m %H:%M}] {slug}: +{g[0]} views em 6 h x média {g[1]:.0f}/6 h -> "
                        f"vídeo decolando: segura novos envios (até {VIRAL_MAX_H} h)\n")
        except OSError:
            pass
    return f"vídeo do canal decolando (+{g[0]} views em 6 h, média {g[1]:.0f}) — novo envio espera esfriar"


def _ler():
    d = politica.ler_json(ESTADO, {})
    d.setdefault("canais", {})
    return d


def _gravar(d):
    d["_leia"] = ("Degraus EXTRAS de upload por canal (bin/rampa_canais.py; soma ao teto da política em "
                  "teto_canal/cota_restante). Sobe com dados, desce na hora se pegar 'limite diário'. Não editar "
                  "à mão: use python bin/rampa_canais.py --subir/--zerar.")
    politica.gravar_json(ESTADO, d)


def extra(canal_id):
    """Degraus extras deste cred (0 se não tem)."""
    c = _ler()["canais"].get(canal_id) or {}
    return max(0, min(teto_extra(c), int(c.get("extra", 0))))


def descer(canal_id, motivo="pegou 'limite diário' do YouTube"):
    """-1 degrau na hora (chamado pelo politica.marcar_limite_diario)."""
    d = _ler()
    c = d["canais"].get(canal_id)
    if not c or int(c.get("extra", 0)) <= 0:
        return False
    c["extra"] = int(c["extra"]) - 1
    c["ultima_mudanca"] = datetime.now().astimezone().isoformat(timespec="seconds")
    c["motivo"] = f"desceu: {motivo}"
    _gravar(d)
    return True


def _mudar(d, cid, delta, motivo):
    c = d["canais"].setdefault(cid, {"extra": 0})
    teto = MAX_EXTRA_LIBERADO if "forte" in motivo or "LIBERADO" in motivo else teto_extra(c)  # 12/11: forte = até 12/dia
    c["extra"] = max(0, min(max(teto, int(c.get("extra", 0))), int(c.get("extra", 0)) + delta))
    c["ultima_mudanca"] = datetime.now().astimezone().isoformat(timespec="seconds")
    c["motivo"] = motivo


def rodar(simular=False):
    """Avalia cada canal do cadastro e sobe quem merece. Devolve as mudanças [(canal, de, para, motivo)]."""
    import statistics
    d = _ler()
    cad = politica.ler_json(politica.CONFIG_DIR / "canais.json", {})
    cad = cad.get("canais") or {}
    apr = politica.ler_json(APREND, {}).get("por_canal") or {}
    medianas = [v.get("mediana", 0) for v in apr.values() if isinstance(v, dict) and v.get("n", 0) >= 4]
    med_geral = statistics.median(medianas) if medianas else 0
    limite = politica.ler_json(politica.LIMITE_DIARIO_FILE, {})
    regs = politica._ler_ledger()
    agora = politica.agora()
    base = politica.politica()["max_uploads_por_canal_dia"]
    # uploads por dia (ts) dos últimos 3 dias, por cred
    por_dia = {}
    for r in regs[-2000:]:
        q = politica._dt(r.get("ts") or "")
        if q and (agora - q).days <= 3 and r.get("canal_id"):
            por_dia.setdefault(r["canal_id"], {}).setdefault(q.date().isoformat(), 0)
            por_dia[r["canal_id"]][q.date().isoformat()] += 1
    mudancas = []
    for chave, x in cad.items():
        if not isinstance(x, dict) or not x.get("creds"):
            continue
        cid = x["creds"][0]
        c = d["canais"].get(cid) or {}
        lib = bool(c.get("liberado"))
        extra_atual = int(c.get("extra", 0))
        m = apr.get(chave) or {}
        # 12/11 dona ("os maiores sempre no máximo; os mais baixos ficam com as sobras"): a escada segue o RENDIMENTO.
        # Forte (mediana 48 h >= 300) sobe como liberado (1/dia até +8 = 12/dia). Fraco (< 50 com >= 4 vídeos medidos)
        # não sobe e DESCE 1 degrau por dia até o teto base (4/dia — o mínimo dele). RAMPA_POR_RENDIMENTO=0 desliga.
        por_rend = os.environ.get("RAMPA_POR_RENDIMENTO", "1") != "0" and m.get("n", 0) >= 4
        forte = por_rend and m.get("mediana", 0) >= 300
        fraco = por_rend and m.get("mediana", 0) < 50
        if fraco:
            ult = c.get("ultima_mudanca")
            recente = False
            try:
                recente = bool(ult) and (agora - datetime.fromisoformat(ult)).total_seconds() < 20 * 3600
            except ValueError:
                pass
            if extra_atual > 0 and not recente:
                motivo = f"desceu: rende pouco (mediana {m.get('mediana')} em 48 h) — vagas vão pros canais fortes"
                mudancas.append((chave, base + extra_atual, base + extra_atual - 1, motivo))
                if not simular:
                    for cr in x["creds"]:
                        _mudar(d, cr, -1, motivo)
            continue
        if forte:
            lib = True
        if extra_atual >= (MAX_EXTRA_LIBERADO if forte else teto_extra(c)):
            continue
        ult = c.get("ultima_mudanca")
        if ult:
            try:
                # liberado: 1 degrau por dia (20 h de folga pra não depender da hora exata da rodada)
                if (agora - datetime.fromisoformat(ult)).total_seconds() < (
                        20 * 3600 if lib else DIAS_ENTRE_DEGRAUS * 86400):
                    continue
            except ValueError:
                pass
        # recusado há pouco: nem pensar em subir (29/10: só o limite ainda ATIVO — o arquivo guarda os vencidos também
        # e travava a escada pra sempre)
        if any(politica._dt((limite.get(cr) or {}).get("ate") or "") and
               politica._dt(limite[cr]["ate"]) > agora for cr in x["creds"]):
            continue
        teto_atual = base + extra_atual
        dias = {}
        for cr in x["creds"]:
            for dia, n in (por_dia.get(cr) or {}).items():
                dias[dia] = dias.get(dia, 0) + n
        cheios = sum(1 for n in dias.values() if n >= teto_atual)
        if cheios < (1 if lib else DIAS_CHEIOS):
            continue
        m = apr.get(chave) or {}
        rende = (m.get("n", 0) >= 4 and (m.get("mediana", 0) >= med_geral or m.get("pct_1000", 0) >= 10))
        if not (rende or lib):
            continue
        motivo = (f"subiu (canal forte, mediana {m.get('mediana')} em 48 h, 1 degrau/dia): encheu o teto {teto_atual}"
                  if forte else f"subiu (LIBERADO pelo YouTube, 1 degrau/dia): encheu o teto {teto_atual}" if lib else
                  f"subiu: encheu o teto {teto_atual} em {cheios} dos últimos 3 dias, sem 'limite diário', "
                  f"mediana {m.get('mediana')} (geral {med_geral}) / pct1000 {m.get('pct_1000')}%")
        mudancas.append((chave, teto_atual, teto_atual + 1, motivo))
        if not simular:
            for cr in x["creds"]:
                _mudar(d, cr, +1, motivo)
    if mudancas and not simular:
        _gravar(d)
        try:
            if r"D:\video-fila" not in sys.path:
                sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar("Rampa de uploads: " + "; ".join(f"{c}: {de}->{para}/dia" for c, de, para, _m in mudancas),
                          "rampa de canais", importante=True)
        except Exception:  # noqa: BLE001
            pass
    return mudancas


def main():
    args = sys.argv[1:]
    if "--liberar" in args:  # 29/10 dona: canal verificado no YouTube = liberado pra postar à vontade (escada diária)
        d = _ler()
        for nome in args[args.index("--liberar") + 1:]:
            canal, err = politica.achar_canal(nome)
            if not canal:
                print(f"{nome}: {err}")
                continue
            c = d["canais"].setdefault(canal["id"], {"extra": 0})
            c["liberado"] = datetime.now().astimezone().isoformat(timespec="seconds")
            c["liberado_nota"] = "dona 29/10: verificado no YouTube, longos + mais Shorts; sobe 1 degrau/dia até 12/dia"
            print(f"{nome} ({canal['id']}): LIBERADO (extra {c.get('extra', 0)}, teto da escada "
                  f"{politica.politica()['max_uploads_por_canal_dia'] + MAX_EXTRA_LIBERADO}/dia)")
        _gravar(d)
    elif "--subir" in args:  # seed manual do dono: canal com limite da conta já desbloqueado
        i = args.index("--subir")
        nome, n = args[i + 1], int(args[i + 2]) if len(args) > i + 2 and args[i + 2].isdigit() else 1
        canal, err = politica.achar_canal(nome)
        if not canal:
            print(f"canal não achado: {err}")
            return
        d = _ler()
        for _ in range(n):
            _mudar(d, canal["id"], +1, f"seed manual do dono ({datetime.now():%d/%m})")
        _gravar(d)
        print(f"{nome} ({canal['id']}): extra = {extra(canal['id'])} (teto efetivo "
              f"{politica.politica()['max_uploads_por_canal_dia'] + extra(canal['id'])}/dia)")
    elif "--zerar" in args:
        i = args.index("--zerar")
        canal, err = politica.achar_canal(args[i + 1])
        if not canal:
            print(f"canal não achado: {err}")
            return
        d = _ler()
        d["canais"].pop(canal["id"], None)
        _gravar(d)
        print(f"{args[i + 1]}: rampa zerada (teto volta ao da política)")
    elif "--rodar" in args:
        for c, de, para, m in rodar(simular="--simular" in args):
            print(f"{c}: {de} -> {para}/dia ({m})")
    else:
        d = _ler()
        base = politica.politica()["max_uploads_por_canal_dia"]
        if not d["canais"]:
            print(f"nenhum canal com degrau extra (teto de todos = {base}/dia). "
                  "--subir <canal> [n], --rodar [--simular], --zerar <canal>")
        for cid, c in sorted(d["canais"].items()):
            print(f"{cid:28} teto {base + int(c.get('extra', 0))}/dia (extra {c.get('extra')}) "
                  f"desde {c.get('ultima_mudanca', '?')[:16]} — {c.get('motivo', '')}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
