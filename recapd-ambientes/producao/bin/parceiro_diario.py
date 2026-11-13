"""parceiro_diario.py — produção e postagem diárias dos Shorts de parceiros (todos os nichos).

Dono, 18/10/2026: "não estamos mais fazendo só recap de manhwa, são todos os tipos de vídeo —
curiosidades, esportes, filmes, doramas, fatos, etc. Ramificar pra cada nicho."

  python bin/parceiro_diario.py status             fila de cada canal, agendados, reprovados
  python bin/parceiro_diario.py producao           produz o que falta na fila de cada canal (pt + línguas)
  python bin/parceiro_diario.py postar [--ensaio]  1 por canal por dia, agendado no horário do canal

Rodar com o python do postador (D:\\veo\\venv: tem tzdata pros fusos); a produção chama o anime_auto com o venv daqui.
Regras (config/parceiro.json):
  - cada canal pt recebe um vídeo DIFERENTE: o @ do canal é gravado na produção (PARCEIRO_HANDLE) e o destino vai no
    postar.json ("canal"). O mesmo vídeo em 2 canais derruba a entrega — e a mesma FONTE não sai em 2 canais no mesmo dia;
  - só posta o que passou na análise do vídeo pronto (pronto=true); parceiro já chega pronto (revisão dispensada);
  - REGRA 18/10: nenhum canal fica 1 dia sem postagem — impedimento avisa, nunca segura;
  - agendamento obrigatório: tudo sobe com publishAt (min 10 min no futuro), nunca publicação imediata.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BIN = Path(__file__).resolve().parent
PROD = BIN.parent
CFG = PROD / "config" / "parceiro.json"
PY_PROD = PROD / "venv" / "Scripts" / "python.exe"
SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")
WS = PROD / "workspace" / "anime"
LOCK = WS / ".parceiro_producao.lock"
POSTADOR_BIN = Path(r"D:\postador-de-videos\bin")
DESLIGADA = POSTADOR_BIN.parent / "config" / "POSTAGEM_DESLIGADA.json"
LEDGER = POSTADOR_BIN.parent / "logs" / "uploads_ledger.jsonl"
DIAS_FRENTE = 7  # dono 18/10: uma semana de publicações programadas em cada canal
TRAVA_WEB = POSTADOR_BIN.parent / "logs" / "yt_web.lock"  # 1 upload pelo navegador por vez (youtube_web_poster.Trava)
FUSO_BR = ZoneInfo("America/Sao_Paulo")
NOTA_APROVACAO = "parceiro @kaijinre: análise do vídeo pronto ok; dono liberou a produção em 16/10"
PROJETO = "parceiro"  # quem posta de verdade (ledger); onde pode postar e a vaga do dono vêm do cadastro canais.json do postador

BELOW_NORMAL, NO_WINDOW = 0x00004000, 0x08000000  # o PC também renderiza o hipercool: o parceiro fica atrás
COOLDOWN_LIMITE = WS / ".limite_diario.json"
# "limite diário de uploads da conta" (Studio): o parceiro tentava a cada 30 min (ForjaReact 161x, Dicas 83x em 3 dias).
# Espera fixa e não "até meia-noite": o Filme Noturno subiu 3-4/dia e só depois bateu no limite — se a janela do YouTube
# for de 24 h corridas, esperar o dia virar perdia o dia seguinte inteiro
ESPERA_LIMITE_H = 3
ESPACO_UPLOAD_MIN = 45  # 23/10: mínimo entre 2 envios do mesmo canal (rajada -> "limite diário" do YouTube)


def _esperar_limite(cid):
    """O canal bateu no limite de uploads da conta: não tenta de novo por ESPERA_LIMITE_H horas. Devolve até quando."""
    try:
        data = json.loads(COOLDOWN_LIMITE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    ate = datetime.now().astimezone() + timedelta(hours=ESPERA_LIMITE_H)
    data[cid] = {"ate": ate.isoformat(timespec="seconds")}
    _json_atomico(COOLDOWN_LIMITE, data)
    return ate


def _em_cooldown_limite(cid):
    """True se o canal ainda está esperando o limite de uploads passar."""
    try:
        data = json.loads(COOLDOWN_LIMITE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    ate = _dt((data.get(cid) or {}).get("ate") or "")
    if not ate:
        return False
    if datetime.now().astimezone() >= ate:
        data.pop(cid, None)
        _json_atomico(COOLDOWN_LIMITE, data)
        return False
    return True


def cfg():
    return json.loads(CFG.read_text(encoding="utf-8"))


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def _json_atomico(path, obj):
    """Grava JSON em .tmp + os.replace (troca atômica): disco cheio ou queda no meio do write não zera o
    arquivo — em 20/10 o _rodizio.json foi zerado assim (OSError 28 no meio do write_text)."""
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _politica():
    if str(POSTADOR_BIN) not in sys.path:
        sys.path.insert(0, str(POSTADOR_BIN))
    import politica
    return politica


def _dt(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.astimezone()


# ─────────────────────────── fila ───────────────────────────────────────────
def destinos(c):
    """{id da credencial: info} dos canais ligados, pt e línguas."""
    out = {d["canal"]: {**d, "idioma": "pt"} for d in c["pt"] if d.get("ativo", True)}
    out.update({d["canal"]: {**d, "idioma": lang} for lang, d in c["idiomas"].items() if d.get("ativo", True)})
    return out


def _estado(d):
    if d.get("bloqueado_studio"):
        return "bloqueado"  # subiu mas o Studio bloqueou (avisos_studio.py, 21/10): não abre, não conta como agendado
    if d.get("posted_url"):
        return "postado"
    if d.get("timeout_em"):
        return "verificar"  # o upload estourou o tempo: pode ter subido — conferir no Studio antes de repetir
    if d.get("pronto"):
        return "pronto"
    rev = str(d.get("revisao") or "").lower()
    return "reprovado" if ("reprovado" in rev or "segurado" in rev) else "esperando"


FONTES_POSTADAS = WS / "_fontes_postadas.json"  # {idioma: {id do vídeo de origem: canal}} — durável (22/10)


def _id_fonte(fonte):
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", str(fonte or ""))
    return m.group(1) if m else None


def _fontes_postadas(its):
    """Regra do dono (nunca o mesmo vídeo em 2 canais): {idioma: {id da fonte: canal}} das fontes JÁ postadas — o
    arquivo durável (a ficha vai pro Drive 2 h depois de postar) + as fichas postadas que ainda estão na fila.
    22/10: em 20/10 o disco cheio não deixou gravar o _feitos_short e 6 fontes saíram em 2 canais no dia seguinte."""
    try:
        reg = json.loads(FONTES_POSTADAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        reg = {}
    for x in its:
        f = _id_fonte(x["fonte"])
        if x["estado"] == "postado" and f and x.get("canal"):
            reg.setdefault(x["lang"], {}).setdefault(f, x["canal"])
    return reg


def _fonte(pj, d):
    if d.get("fonte"):
        return d["fonte"]
    try:
        return json.loads((pj.parent / "metadata.json").read_text(encoding="utf-8"))["video"]["source_url"]
    except (OSError, ValueError, KeyError, TypeError):
        return str(pj.parent)


def itens(c):
    """Um item por postar.json de Short do parceiro (os de teste ficam de fora), do mais antigo pro mais novo."""
    pt_padrao = c["pt"][0]["canal"]  # os primeiros (16/10) saíram com o @manhwanoturno gravado
    por_lang = {lang: d["canal"] for lang, d in c["idiomas"].items()}
    out = []
    for pj in SHORTS.glob("*/postar.json"):
        try:
            d = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        # o recap de anime próprio grava na mesma pasta (categoria "animes"): quem posta esse é o postar_tudo_hoje
        if d.get("categoria") != "parceiro" or d.get("teste"):
            continue
        lang = d.get("idioma") or "pt"
        out.append({"pj": pj, "d": d, "lang": lang, "estado": _estado(d), "fonte": _fonte(pj, d),
                    "canal": d.get("canal") or (pt_padrao if lang == "pt" else por_lang.get(lang)),
                    "mp4": pj.parent / d.get("arquivo", "video.mp4"), "mtime": pj.stat().st_mtime})
    return sorted(out, key=lambda x: x["mtime"])


def _fila(its):
    """Vídeos esperando a vez em cada canal (prontos + os que ainda esperam a análise)."""
    return Counter(x["canal"] for x in its if x["estado"] in ("pronto", "esperando"))


# ─────────────────────────── produção ───────────────────────────────────────
def _vivo(pid):
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    return str(pid) in (r.stdout or "")


def _auto_parceiro_rodando():
    """Algum anime_auto do parceiro já rodando (inclusive disparado à mão, fora deste script)? Se não der pra
    saber, responde que sim (16/10: a saída do PowerShell vem em cp850, a leitura em utf-8 quebrava, a resposta
    ficava vazia e uma 2ª produção subiu junto com a 1ª)."""
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                            "ForEach-Object { $_.CommandLine }"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           creationflags=NO_WINDOW, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return True
    linhas = (r.stdout or "").splitlines()
    if r.returncode != 0 or not linhas:
        return True
    # 03/11: os Shorts EXTRAS do Kaggle (-X abastecedor_kaggle) não contam — a produção normal do PC1 segue no máximo
    return any("anime_auto.py" in l and "--fonte" in l and "abastecedor_kaggle" not in l for l in linhas)


def _pegar_lock():
    try:
        pid = int(LOCK.read_text().strip())
        if _vivo(pid) and datetime.now().timestamp() - LOCK.stat().st_mtime < 8 * 3600:
            return False
    except (OSError, ValueError):
        pass
    if _auto_parceiro_rodando():
        return False
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(str(os.getpid()))
    return True


def _rodar_auto(c, alvo, linguas, fonte_url=None, tipo_fonte=None, video_id=None):
    """1 Short novo (o próximo da fila do parceiro) com o @ e o destino de `alvo` + as `linguas`. Com `video_id`
    (30/10, virais_fracos.py): refaz ESTE vídeo da fonte (anime_auto --id: novo roteiro/narração/título), mesmo já feito."""
    url = fonte_url or c["fonte"]
    tipo = tipo_fonte or c.get("tipo_fonte", "manhwa")
    # ANIME_MAX_CPU_PCT=0: a guarda de CPU esperava até 30 min ANTES DE CADA CLIPE com o hipercool renderizando (CPU
    # sempre 100%) e um Short levava horas (18/10). A prioridade BELOW_NORMAL já deixa o hipercool na frente; a guarda
    # de RAM (evita o ffmpeg quebrar sem memória) continua.
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PARCEIRO_HANDLE=alvo["handle"],
               PARCEIRO_CANAL=alvo["canal"], ANIME_IDIOMAS=",".join(linguas), PARCEIRO_TIPO=tipo,
               ANIME_MAX_CPU_PCT="0")
    # 02/11 dona (lote no Kaggle pra liberar CPU/RAM pros Veo 3): a renderização vai pra fila_shorts do Kaggle quando
    # D:\recapd-ambientes\producao\config\shorts_kaggle.json tiver "ligado": true (lote_shorts_kaggle.py)
    try:
        if json.loads((BIN.parent / "config" / "shorts_kaggle.json").read_text(encoding="utf-8")).get("ligado"):
            env["SHORTS_NO_KAGGLE"] = "1"
    except (OSError, ValueError):
        pass
    logf = WS / f"_parceiro_{datetime.now():%Y%m%d}.log"
    cmd = [str(PY_PROD), "-X", "utf8", str(BIN / "anime_auto.py"), "--modo", "short", "--fonte", url,
           "--engine", "local", "--limit", "1", "--top", "5"] + (["--id", video_id] if video_id else [])
    log(f"produção: {alvo['nome']} ({alvo['handle']}) [{tipo}] fonte={url.split('/')[-2]} + línguas {linguas or '-'} | log {logf.name}")
    with open(logf, "a", encoding="utf-8") as fh:
        try:
            r = subprocess.run(cmd, cwd=str(BIN), env=env, stdout=fh, stderr=subprocess.STDOUT,
                               creationflags=BELOW_NORMAL | NO_WINDOW, timeout=6 * 3600)
            return r.returncode
        except subprocess.TimeoutExpired:
            return "timeout"


RODIZIO = WS / "_rodizio.json"


def _rodizio_estado():
    try:
        return json.loads(RODIZIO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _rodizio_gravar(estado):
    RODIZIO.parent.mkdir(parents=True, exist_ok=True)
    _json_atomico(RODIZIO, estado)


NICHO_TESTE = 0.2      # fração da produção do canal que testa OUTRO nicho (o funil precisa de amostra)
NICHO_MIN_MEDIDAS = 5  # medidas no canal pra um nicho de fora virar o principal dele
NICHO_MARGEM = 0.1     # quanto a mais de vitória (média) ele precisa ter


def _nicho_do_canal(alvo, proprio, principais):
    """Dono 22/10: "os nichos devem ser decididos mais pelo algoritmo do que dá certo no canal do que pelo nome — vídeo
    de mangá pode dar mais certo no canal que fizemos pra dorama; o funil vai definindo o que é de cada canal e
    separando". Placar "nicho_canal" (notificar_telegram.medir_48h: views em 48 h contra a mediana DESTE canal).
    Principal = o nicho do cadastro, até outro nicho ter NICHO_MIN_MEDIDAS no canal e render mais (média com +1/+2);
    NICHO_TESTE das vezes testa outro nicho (Thompson). Sem placar = o do cadastro (como antes)."""
    try:
        import random
        import placar_titulos
        placar = placar_titulos.taxas("nicho_canal", alvo["canal"])
    except Exception:  # noqa: BLE001
        return proprio

    def media(n):
        t, v = placar.get(n, (0, 0))
        return (v + 1) / (t + 2)
    melhor = max((n for n in principais if placar.get(n, (0, 0))[0] >= NICHO_MIN_MEDIDAS), key=media, default=None)
    principal = melhor if melhor and media(melhor) > media(proprio) + NICHO_MARGEM else proprio
    outros = [n for n in principais if n != principal]
    if outros and random.random() < NICHO_TESTE:
        escolhido = max(outros, key=lambda n: random.betavariate(placar.get(n, (0, 0))[1] + 1,
                                                                 placar.get(n, (0, 0))[0] - placar.get(n, (0, 0))[1] + 1))
        log(f"nicho: {alvo.get('nome')} testa '{escolhido}' (principal '{principal}', cadastro '{proprio}')")
        return escolhido
    if principal != proprio:
        log(f"nicho: {alvo.get('nome')} agora é '{principal}' pelo funil (cadastro '{proprio}'; placar {placar})")
    return principal


def _escolher_fonte(c, alvo=None, evitar=None):
    """Fonte do nicho do canal de destino (pt[i]["nicho"]); nicho sem fonte ainda: rodízio — o nicho que menos
    produziu nas últimas 24h. Dentro do nicho, a fonte menos usada."""
    fontes = c.get("fontes")
    if not fontes:
        return c["fonte"], c.get("tipo_fonte", "manhwa")
    estado = _rodizio_estado()
    agora = datetime.now().timestamp()
    corte = agora - 24 * 3600
    serve = lambda f: [f["tipo"]] + f.get("nichos", [])  # "nichos": outros nichos que o conteúdo da fonte atende
    nichos = sorted({n for f in fontes for n in serve(f)})
    nicho = (alvo or {}).get("nicho")
    # 05/11 dona ("os vídeos de certo tipo pro canal em que mais rendem, independente do nome — o nome a gente muda"):
    # "nichos_foco" = {tipo: peso} calculado pelo Studio (video-fila\analise_shorts_foco.py --aplicar: mediana de views
    # do tipo NESTE canal). Sorteia pelo peso; NICHO_TESTE das vezes segue o funil antigo (testa tipo novo).
    foco = {n: float(p) for n, p in ((alvo or {}).get("nichos_foco") or {}).items() if n in nichos and float(p) > 0}
    import random as _rnd
    if (alvo or {}).get("nicho_fixo") and nicho in nichos:
        # 12/11 (canais novos de público que compra automação — negócio/saúde/imobiliário): o teste de nicho mandava
        # dorama pro "Vendas que Escalam" e saúde pro "Imóvel em Foco". nicho_fixo=true = só o nicho do cadastro.
        pass
    elif foco and _rnd.random() >= NICHO_TESTE:
        nicho = _rnd.choices(list(foco), weights=list(foco.values()))[0]
        log(f"nicho: {alvo.get('nome')} -> '{nicho}' (foco pelo Studio {foco})")
    elif alvo and nicho in nichos:  # 22/10: o funil decide o nicho de cada canal (o do cadastro começa na frente)
        nicho = _nicho_do_canal(alvo, nicho, sorted(set(f["tipo"] for f in fontes)))
    if nicho not in nichos:
        principais = sorted(set(f["tipo"] for f in fontes))
        cont_nicho = Counter({n: 0 for n in principais})
        for nome, ts_list in estado.items():
            f = next((f for f in fontes if f["nome"] == nome), None)
            if f:
                cont_nicho[f["tipo"]] += len([t for t in ts_list if t > corte])
        nicho = min(principais, key=lambda n: cont_nicho[n])
    # dentro do nicho, a fonte menos usada
    do_nicho = [f for f in fontes if nicho in serve(f)]
    try:  # placar das fontes (views em 48 h contra a mediana do canal, notificar_telegram.medir_48h; 21/10)
        import placar_titulos
        placar = placar_titulos.taxas("fontes", "parceiro")
    except Exception:  # noqa: BLE001
        placar = {}
    try:  # anti-bloqueio (dono 21/10): fonte com bloqueios repetidos no Studio sai do rodízio; 1 bloqueio pesa
        if r"D:\video-fila" not in sys.path:
            sys.path.append(r"D:\video-fila")
        import material_bloqueado as _mb
        fora = _mb.fontes_fora()
        livres = [f for f in do_nicho if f["nome"] not in fora]
        if livres:
            do_nicho = livres
        bloqueios = {f["nome"]: _mb.bloqueios_da_fonte(f["nome"]) for f in do_nicho}
    except Exception:  # noqa: BLE001
        bloqueios = {}

    _fonte_no_canal = {}
    if alvo and os.environ.get("PARCEIRO_FONTE_POR_CANAL", "1") != "0":
        try:  # gerado todo dia pelo video-fila\analise_shorts_foco.py --aplicar (tarefa FocoShorts)
            _fonte_no_canal = json.loads((BIN.parent / "estado" / "fontes_por_canal.json").read_text(
                encoding="utf-8")).get("canais", {}).get(alvo["canal"], {})
        except (OSError, ValueError):
            _fonte_no_canal = {}

    def uso(f):
        hist = estado.get(f["nome"], [])
        n = len([t for t in hist if t > corte])
        testes, vit = placar.get(f["nome"], (0, 0))
        # 23/10 (dono: "as fontes que dão mais resultado na inteligência"): era 1x-2x e só com 3 medidas — o rodízio
        # usava fabioindaia2006 (mediana 2 views) 16x e d_UCSJ6_g (mediana 1634) 4x. Agora vale com 2 medidas e vai
        # de ~0,3x (nunca rende) a ~2,5x (vence quase sempre); sem medida = 1,2 (continua sendo testada)
        if testes >= 2:
            p = (vit + 1) / (testes + 2)
            peso = 0.25 + 4 * p * p
        else:
            peso = 1.2
        peso /= 1 + 2 * bloqueios.get(f["nome"], 0)  # 1 bloqueio = 3x menos chance (2 = fora, acima)
        # 30/10 (dona: "parceiro que não dá views, aí sim cortamos"): "peso" no config (padrão 1; 0,2 = ~5x menos vez
        # no rodízio do nicho). Reversível: apagar o campo. O motivo fica no "_peso_obs" da fonte
        peso *= max(0.05, float(f.get("peso", 1) or 0.05))
        # 12/11 dona: a fonte que rende NESTE canal (mediana dela no canal ÷ mediana do canal, 0,3–3) sai mais vezes
        peso *= _fonte_no_canal.get(f["nome"], 1.0)
        # 12/11: fonte cujo TIPO é o próprio nicho do canal vem antes da que só "também serve" (Imóvel em Foco: Professor
        # Baroni [imobiliario] antes dos de negócios, que ficam de reserva)
        if (alvo or {}).get("nicho_fixo") and f.get("tipo") != nicho:
            peso /= 3
        return (n + 1) / peso
    # 09/11: "evitar" = fontes já tentadas sem vídeo novo nesta rodada (ocioso._escolher_pc2) — pega a próxima do nicho
    # peso 0 = fora do rodízio (09/11: canal sem aba de Shorts)
    do_nicho = [f for f in do_nicho if f.get("peso", 1) != 0] or do_nicho
    resto = [f for f in do_nicho if f["url"] not in (evitar or ())] or do_nicho
    fonte = min(resto, key=uso)
    return fonte["url"], fonte["tipo"], fonte["nome"]


def _rodizio_registrar(nome_fonte):
    estado = _rodizio_estado()
    agora = datetime.now().timestamp()
    corte = agora - 48 * 3600
    hist = estado.get(nome_fonte, [])
    hist = [t for t in hist if t > corte]
    hist.append(agora)
    estado[nome_fonte] = hist
    _rodizio_gravar(estado)


def disparar_postagem():
    """Short novo pronto -> postagem já, sem esperar a tarefa de 30 min (dono 18/10: canal sem post sai em minutos).
    Se outra postagem estiver subindo, esta pula sozinha (_outro_postar_rodando)."""
    try:
        fh = open(PROD / "logs" / "parceiro_postar_auto.log", "a", encoding="utf-8")
        subprocess.Popen([r"D:\veo\venv\Scripts\python.exe", "-X", "utf8", str(BIN / "parceiro_diario.py"), "postar"],
                         cwd=str(PROD), stdout=fh, stderr=subprocess.STDOUT, creationflags=NO_WINDOW,
                         env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"))
    except OSError as e:
        log(f"[!] não consegui disparar a postagem: {e}")


GRUPO_TIPO = {"manhwa": "anime"}  # no rodízio de tipo, manhwa e anime são o mesmo conteúdo


def _uso_do_tipo(c):
    """canal -> quantos Shorts do tipo de conteúdo dele saíram nas últimas 24 h (rodízio das fontes). Dono 20/10:
    havia muito mais canal de anime e quase só saía anime; dorama, filme, fatos, esportes também têm a vez."""
    # conta pelo log da produção ("produção: <canal> (@x) [tipo] fonte=..."): o _rodizio.json foi zerado quando o
    # disco encheu (20/10) e a contagem dele dizia 2 Shorts de anime num dia de 20
    fontes = c.get("fontes") or []
    corte = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    cont = Counter({GRUPO_TIPO.get(f["tipo"], f["tipo"]): 0 for f in fontes})
    try:
        with open(PROD / "logs" / "parceiro_producao.log", "rb") as fh:
            fh.seek(0, 2)
            fh.seek(max(0, fh.tell() - 400_000))
            for linha in fh.read().decode("utf-8", "replace").splitlines():
                m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\] produção: .+? \[(\w+)\] fonte=", linha)
                if m and m.group(1) >= corte:
                    cont[GRUPO_TIPO.get(m.group(2), m.group(2))] += 1
    except OSError:
        pass
    serve = {}
    for f in fontes:
        for n in [f["tipo"]] + f.get("nichos", []):
            serve.setdefault(n, GRUPO_TIPO.get(f["tipo"], f["tipo"]))
    menor = min(cont.values()) if cont else 0
    return lambda d: cont[serve[d.get("nicho")]] if d.get("nicho") in serve else menor


def _prioridade(its, fila, alvo_fila, c=None):
    """Ordem de produção: primeiro canal sem post hoje (dono 18/10: nunca sem postagem), depois o tipo de conteúdo
    menos produzido em 24 h (com `c`; dono 20/10), depois a fila mais vazia."""
    hoje = datetime.now(FUSO_BR).date()
    com_hoje = set()
    agendados = Counter()  # 02/11: publicações FUTURAS por canal (reserva = fila + agendados)
    publicados_3d = Counter()  # 02/11: consumo real (o canal pode gastar mais que o por_dia do parceiro)
    for x in its:
        q = _dt(x["d"].get("agendado_para") or "")
        if x["estado"] == "postado" and q and q.astimezone(FUSO_BR).date() == hoje:
            com_hoje.add(x["canal"])
    # post de QUALQUER projeto conta (18/10: o Manhwa Noturno tem o do hipercool todo dia e furava a fila sempre)
    try:
        try:
            bloq = set(json.loads((LEDGER.parent.parent / "config" / "bloqueados.json").read_text(encoding="utf-8")))
        except (OSError, ValueError):
            bloq = set()
        for l in LEDGER.read_text(encoding="utf-8").splitlines():
            u = json.loads(l) if l.strip() else {}
            q = _dt(u.get("publish_at") or u.get("ts") or "")
            if q and q.astimezone(FUSO_BR).date() == hoje and u.get("video_id") not in bloq:
                com_hoje.add(u.get("canal_id"))
            if q and q > datetime.now(FUSO_BR) and u.get("video_id") not in bloq:
                agendados[u.get("canal_id")] += 1
            elif q and (datetime.now(FUSO_BR) - q).total_seconds() <= 3 * 86400:
                publicados_3d[u.get("canal_id")] += 1
    except (OSError, ValueError):
        pass
    uso = _uso_do_tipo(c) if c else (lambda d: 0)
    rend = _rendimento_canais()  # 22/10 (funil do dono): canal que RENDE mais produz primeiro (empate das regras acima)
    # 02/11 dona: RESERVA de 1 semana em todo canal -> o mais vazio (em dias: fila + agendados ÷ por_dia, faixas de 1
    # dia até 7) produz primeiro; tipo de conteúdo e rendimento viram desempate dentro da mesma faixa
    # 11/11 dona ("dar mais prioridade aos canais que estão dando mais certo, como nos longos"): o teto da reserva
    # depende do rendimento (mediana de views em 48 h): Esporte Noturno 1.258 x Manhwa Noturno 2. Quem rende pede até
    # 10 dias de estoque, o médio 7, o fraco 4 — então os bons continuam sendo produzidos depois que os fracos já têm o
    # mínimo. "Sem post hoje" segue em 1º. PARCEIRO_RESERVA_POR_RENDIMENTO=0 volta ao teto único de 7.
    por_rend = os.environ.get("PARCEIRO_RESERVA_POR_RENDIMENTO", "1") != "0"

    def teto(d):
        if not por_rend:
            return 7
        r = rend.get(d["canal"])
        return 7 if r is None else 10 if r >= 300 else 7 if r >= 50 else 4

    def reserva(d):
        gasto = max(int(d.get("por_dia") or 3), publicados_3d[d["canal"]] / 3)
        dias = (fila[d["canal"]] + agendados[d["canal"]]) / gasto
        t = teto(d)
        return min(t, int(dias)) - t  # negativo = falta pra chegar no teto dele (mais negativo produz antes)
    if os.environ.get("PARCEIRO_ALVO_RENDIMENTO", "1") != "0":
        # 12/11 dona: "o melhor canal faz o máximo, depois o segundo, e assim até os mais baixos". Depois de "sem post
        # hoje", o que mais RENDE vem primeiro (o estoque por rendimento já tira da fila quem está cheio).
        return lambda d: (d["canal"] in com_hoje, -(rend.get(d["canal"]) or 0), reserva(d), uso(d),
                          fila[d["canal"]] / d.get("fila_alvo", alvo_fila))
    return lambda d: (d["canal"] in com_hoje, reserva(d), uso(d), -rend.get(d["canal"], 0),
                      fila[d["canal"]] / d.get("fila_alvo", alvo_fila))


_CONTA_LINGUA = BIN.parent / "estado" / "parceiro_vez_lingua.json"


def _vez_da_lingua():
    """True a cada N chamadas (N = PARCEIRO_LINGUA_A_CADA, padrão 3; 1 = toda vez, como antes). Contador em disco."""
    try:
        n = max(1, int(os.environ.get("PARCEIRO_LINGUA_A_CADA", "3")))
    except ValueError:
        n = 3
    try:
        k = int(json.loads(_CONTA_LINGUA.read_text(encoding="utf-8")).get("k", 0))
    except (OSError, ValueError, AttributeError):
        k = 0
    k += 1
    vez = k >= n
    try:
        _CONTA_LINGUA.parent.mkdir(parents=True, exist_ok=True)
        _CONTA_LINGUA.write_text(json.dumps({"k": 0 if vez else k}), encoding="utf-8")
    except OSError:
        return True  # sem estado: não segura a língua (comportamento antigo)
    return vez


def _canais_travados(c):
    """{cred_id} dos canais (pt e línguas) travados pelo YouTube (postador-de-videos\\bin\\trava_conta). Falhou = vazio."""
    out = set()
    try:
        sys.path.insert(1, r"D:\postador-de-videos\bin")  # depois do bin do recapd (nunca na frente)
        import trava_conta
        import youtube_web_poster as ywp
        for d in list(c.get("pt") or []) + list((c.get("idiomas") or {}).values()):
            slug, _e = ywp.entrada_do_cred(d["canal"])
            if slug and trava_conta.checar(slug):
                out.add(d["canal"])
    except Exception:  # noqa: BLE001
        pass
    return out


def alvo_por_rendimento(d, rend, base):
    """12/11 dona ("os maiores sempre no máximo; os mais baixos ficam com as sobras, mas obrigatoriamente 1 a 3 vídeos
    por dia"): o ESTOQUE de prontos de cada canal vem do que ele rende (mediana de views em 48 h), em dias de postagem:
    forte (>= 300) 10 dias, médio (>= 50) 7, fraco 3 (mínimo 3 vídeos). Canal sem medida (novo) = alvo do config.
    Assim o fraco enche rápido e sai de "falta", e o PC fica pros fortes. PARCEIRO_ALVO_RENDIMENTO=0 volta ao antigo
    (base, x2 pra quem rende >= 300)."""
    r = rend.get(d["canal"])
    if os.environ.get("PARCEIRO_ALVO_RENDIMENTO", "1") == "0":
        return base * 2 if (r or 0) >= 300 else base
    if r is None:
        return base
    pd = max(1, int(d.get("por_dia") or 2))
    dias = 10 if r >= 300 else 7 if r >= 50 else 3
    return max(3, pd * dias)


def _rendimento_canais():
    """{cred_id: mediana de views em 48 h} do placar comum (aprendizado_global.por_canal, medido pelo
    notificar_telegram). 22/10, pedido do dono: 'priorizar canais que dão mais visualizações' — vale como
    DESEMPATE depois de 'nenhum canal fica um dia sem post' e do equilíbrio por tipo de conteúdo."""
    try:
        apr = json.loads(Path(r"D:\postador-de-videos\_analise\aprendizado_global.json").read_text(encoding="utf-8"))
        por = apr.get("por_canal") or {}
        cad = json.loads(Path(r"D:\postador-de-videos\config\canais.json").read_text(encoding="utf-8"))
        cad = cad.get("canais") or cad  # o arquivo tem raiz {"canais": {...}}
    except (OSError, ValueError):
        return {}
    out = {}
    for chave, x in cad.items():
        if not isinstance(x, dict):
            continue
        med = (por.get(chave) or {}).get("mediana")
        if med is None:
            continue
        for cid in (x.get("creds") or []):
            out[cid] = med
    return out


def _controle(etapa):
    """Liga/desliga único dos projetos (D:\\video-fila\\controle.py): (ligado, motivo). Sem o controle = ligado."""
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import controle
        return controle.ligado(PROJETO, etapa)
    except Exception:  # noqa: BLE001
        return True, ""


def producao(args):
    c = cfg()
    if not c.get("ligado", True):
        log("produção: desligada (config/parceiro.json ligado=false)")
        return
    ok, motivo = _controle("producao")
    if not ok:
        log(f"produção: {motivo}")
        return
    if not _pegar_lock():
        log("produção: a rodada anterior ainda está rodando — pulando")
        return
    try:
        livre = shutil.disk_usage("D:\\").free / 1e9
        if livre < c.get("disco_min_gb", 8):
            # 22/10 (dono: "se na hora do vídeo estiver cheio, adianta a limpeza"): faxina RÁPIDA (só regenerável de
            # job encerrado, instantânea — D:\video-fila\faxina.py) e mede de novo; só pula se ainda faltar espaço
            try:
                log(f"produção: só {livre:.0f} GB livres — adiantando a faxina rápida")
                subprocess.run([r"D:\veo\venv\Scripts\python.exe", r"D:\video-fila\faxina.py", "--rapida"],
                               capture_output=True, timeout=900, creationflags=0x08000000,
                               env=dict(os.environ, PYTHONUTF8="1"))
                livre = shutil.disk_usage("D:\\").free / 1e9
                log(f"produção: depois da faxina, {livre:.0f} GB livres")
            except Exception as e:  # noqa: BLE001
                log(f"produção: faxina rápida falhou ({type(e).__name__})")
        if livre < c.get("disco_min_gb", 8):
            log(f"produção: só {livre:.0f} GB livres no D: — pulando (a fila do disco não pode encher)")
            # 22/10 (dono: "o sistema não pode parar por nada sem eu saber"): a produção parada por disco era
            # MUDA — agora avisa na hora pelo portão (repetido segura 12 h sozinho)
            try:
                if r"D:\video-fila" not in sys.path:
                    sys.path.insert(0, r"D:\video-fila")
                import avisos
                avisos.enviar(f"PRODUÇÃO DO PARCEIRO PARADA: só {livre:.0f} GB livres no D: "
                              f"(mínimo {c.get('disco_min_gb', 8)}) — liberar espaço ou esperar o backup das 05:40",
                              "produção do parceiro", importante=True)
            except Exception:  # noqa: BLE001
                pass
            return
        # 30/10 (dona: "postar nos canais que não dão views os vídeos que viralizam nos outros"): antes da produção
        # normal, 1 versão nova de um viral pra um canal fraco (bin/virais_fracos.py; modo em parceiro.json
        # "virais_fracos": ensaio = só registra o que faria)
        try:
            import virais_fracos
            virais_fracos.rodada(c)
        except Exception as e:  # noqa: BLE001
            log(f"virais->fracos: falhou ({type(e).__name__}: {str(e)[:100]}) — segue a produção normal")
        pular, falhas = set(), 0
        for _ in range(c.get("max_por_rodada", 2)):
            c = cfg()  # relê a cada vídeo: canal novo/desligado no config vale já, sem esperar a rodada (horas) acabar
            alvo_fila = c.get("fila_alvo", 2)
            # 11/11: canal TRAVADO pelo YouTube (strike/removido/avisos — Mundo Que Não Existe desde 01/11) recebia vídeo
            # que nunca sobe (log: "não subiu ... TRAVADO"); fica fora da produção
            pts = [d for d in c["pt"] if d.get("ativo", True) and d["canal"] not in _canais_travados(c)]
            its = itens(c)
            fila = _fila(its)
            rend_pt = _rendimento_canais() if os.environ.get("PARCEIRO_RESERVA_POR_RENDIMENTO", "1") != "0" else {}

            def _alvo(d):  # 11/11 dona: quem rende (mediana 48 h >= 300) guarda o dobro de vídeos prontos
                return alvo_por_rendimento(d, rend_pt, d.get("fila_alvo", alvo_fila))
            falta = [d for d in pts if fila[d["canal"]] < _alvo(d) and d["canal"] not in pular]
            if not falta:
                log("produção: filas pt cheias (" + ", ".join(f"{d['nome']} {fila[d['canal']]}" for d in pts) + ")")
                break
            alvo = min(falta, key=_prioridade(its, fila, alvo_fila, c))
            # rodízio entre fontes/nichos
            resultado = _escolher_fonte(c, alvo)
            if len(resultado) == 3:
                fonte_url, tipo_fonte, nome_fonte = resultado
            else:
                fonte_url, tipo_fonte = resultado
                nome_fonte = None
            # línguas: as de fila mais curta, no máximo linguas_por_fonte — fontes diferentes em canais diferentes
            # fila_alvo por língua (21/10: línguas com mediana 0 view em 48 h ficam com estoque pequeno)
            ling = _linguas_para(c, fila, alvo_fila, tipo_fonte)
            if c.get("linguas_pausadas"):  # dono 17/10: prioridade = os 12 canais BRASILEIROS; línguas esperam
                ling = []
            # 12/11: a versão na outra língua roda o anime-pipeline inteiro NO PC (~22 min cada) — em 11/11 foram 14
            # versões = 5 h de PC (1/3 do dia) pra canais com mediana 0–2 views, e só 20 Shorts pt saíram. Agora no
            # máximo 1 versão de língua a cada PARCEIRO_LINGUA_A_CADA Shorts (padrão 3); o resto do PC vai pro pt.
            if ling and not _vez_da_lingua():
                log(f"línguas: {', '.join(ling)} esperam (1 versão de língua a cada "
                    f"{os.environ.get('PARCEIRO_LINGUA_A_CADA', '3')} Shorts — PC pro pt)")
                ling = []
            antes = {str(x["pj"]) for x in its}
            rc = _rodar_auto(c, alvo, ling, fonte_url, tipo_fonte)
            if nome_fonte:
                _rodizio_registrar(nome_fonte)
            novos = [x for x in itens(c) if str(x["pj"]) not in antes]
            log(f"produção: rc={rc} | novos: " + (", ".join(f"{x['pj'].parent.name} [{x['estado']}]" for x in novos)
                                                  or "nenhum"))
            if any(x["lang"] == "pt" for x in novos):
                falhas = 0
                disparar_postagem()
            else:
                # 18/10: antes uma falha encerrava a rodada e a produção ficava parada até a próxima tarefa
                pular.add(alvo["canal"])
                falhas += 1
                if falhas >= 3:
                    log("produção: 3 falhas seguidas — a próxima rodada tenta de novo")
                    break
        # 22/10 (dono: "não parar por nada"): a rodada acabou e o IP está vivo — aproveita e repõe 1 fonte no
        # ESTOQUE (bin\estoque_fontes.py). Quando o YouTube barrar o IP, a produção consome daqui e não para.
        try:
            import estoque_fontes
            novos = estoque_fontes.repor(max_novos=1)
            if novos:
                log(f"estoque: +{len(novos)} fonte(s) guardada(s) pra quando o IP travar")
            else:  # 23/10: o motivo saía só no logging (que aqui não vai pra arquivo) — o estoque ficou em 0 sem rastro
                import ytdlp_vez
                livre = shutil.disk_usage("D:\\").free / 1e9
                log(f"estoque: nada reposto ({len(estoque_fontes._entradas())}/{estoque_fontes.ALVO}; "
                    + (f"disco {livre:.1f} GB < {estoque_fontes.DISCO_MIN_GB} GB" if livre < estoque_fontes.DISCO_MIN_GB
                       else "yt-dlp em pausa" if ytdlp_vez.pausado() else "sem candidato novo ou download falhou") + ")")
        except Exception as e:  # noqa: BLE001
            log(f"estoque: repor falhou ({type(e).__name__}: {str(e)[:80]})")
    finally:
        try:
            LOCK.unlink()
        except OSError:
            pass


# ─────────────────────────── postagem ───────────────────────────────────────
def _ordem_horarios(horarios, tz):
    """Dono 22/10 ("usar os horários vencedores"): o canal preenche PRIMEIRO o horário cuja faixa de 3 h (hora de
    Brasília, a mesma do placar do notificar_telegram.medir_48h) mais rende — sorteio Thompson sobre vitórias/testes,
    que continua testando os outros. Antes era sempre o mais cedo: com pouca produção o Short do dia caía no horário
    fraco (placar de 22/10: faixa 09h = 0/5, os horários das 11h; 06h = 5/8, as manhãs dos canais de finanças).
    Sem placar (PC2, arquivo fora) = ordem do relógio, como antes."""
    try:
        import random
        import placar_titulos
        placar = placar_titulos.taxas("horarios", PROJETO)
    except Exception:  # noqa: BLE001
        placar = {}

    def _hb(h):
        hh, mm = (int(v) for v in h.split(":"))
        return datetime.now(tz).replace(hour=hh, minute=mm, second=0, microsecond=0).astimezone(FUSO_BR).hour

    # 30/10 (321 Shorts de 18-27/10, comparação dentro do canal): postado 15-21 h de Brasília chega a 500 views em 13%
    # contra 33% no resto (pior em 9 de 9 canais às 15-18 h e 8 de 8 às 19-21 h). Esses horários vão pro FIM da fila
    # (só enchem se sobrar Short no dia). HORARIO_FRACO_BR="" desliga.
    fracos = {int(x) for x in os.environ.get("HORARIO_FRACO_BR", "15,16,17,18,19,20,21").split(",") if x.strip()}
    if str(tz) != str(FUSO_BR):  # o dado é dos canais em pt; os de outras línguas (outro fuso) seguem só o placar
        fracos = set()
    # 30/10 variante T12 (dona: "coisa subjetiva vira variante"; bin\variantes.py, cortes_ajustes "horario_fraco"):
    # sorteio por CANAL — A = ordem de antes de 30/10 (sem empurrar 15-21 h), B = 15-21 h no fim. O id do canal vem do
    # `cid` de quem chama (o laço da postagem), para não mexer fora desta função; sem cid = B (como estava).
    try:
        import sys as _sys
        import variantes
        _cid = _sys._getframe(1).f_locals.get("cid")
        if fracos and _cid and variantes.braco("horario_fraco", _cid) == "A":
            fracos = set()
    except Exception:  # noqa: BLE001
        pass
    if not placar:
        return sorted(horarios, key=lambda h: (_hb(h) in fracos, h))

    def nota(h):
        hb = _hb(h)
        testes, vit = placar.get(f"{hb - hb % 3:02d}h", (0, 0))
        return random.betavariate(vit + 1, testes - vit + 1) - (1.0 if hb in fracos else 0.0)
    return sorted(horarios, key=nota, reverse=True)


def _proximo_horario(dst, agora_utc):
    """Próxima publicação no horário do canal (hora de lá), com folga pro upload."""
    tz = ZoneInfo(dst["fuso"])
    hh, mm = (int(x) for x in dst["horario"].split(":"))
    agora_la = agora_utc.astimezone(tz)
    alvo = agora_la.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if alvo < agora_la + timedelta(minutes=70):
        alvo += timedelta(days=1)
    return alvo


def _gravar(pj, **campos):
    d = json.loads(pj.read_text(encoding="utf-8"))
    d.update(campos)
    _json_atomico(pj, d)


NICHOS_SERIOS = {"negocios", "saude", "imobiliario", "juridico"}  # 12/11 dona: canais pra vender automação a quem tem dinheiro


def _nota_voz(narrador, nicho):
    """Nota 0-3 do narrador no nicho (config\\narradores_nichos.json); None = sem narrador clonado ou sem a tabela."""
    if not narrador:
        return None
    try:
        t = json.loads((BIN.parent / "config" / "narradores_nichos.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    d = t.get(narrador)
    if not isinstance(d, dict):
        return None
    try:
        return float(d.get(nicho, d.get("geral", 1)))
    except (TypeError, ValueError):
        return None


def _publish_efetivo(mp4):
    """Hora em que o vídeo abre de verdade, pelo ledger: o politica pode trocar a hora pedida (Manhwa Noturno: o
    parceiro só pega a vaga de hoje) e a ficha mostrava 25/10 com o vídeo abrindo 22/10 00:30."""
    alvo = str(mp4).lower()
    try:
        linhas = LEDGER.read_text(encoding="utf-8").splitlines()[-60:]
    except OSError:
        return None
    for l in reversed(linhas):  # roda DEPOIS do upload e antes de gravar o posted_url: erro aqui = upload em dobro
        try:
            r = json.loads(l)
            if str(r.get("caminho") or "").lower() == alvo and r.get("publish_at"):
                return _dt(r["publish_at"])
        except (ValueError, AttributeError, TypeError):
            continue
    return None


def _outro_postar_rodando():
    """Outra postagem viva = os dois pegariam o mesmo Short pronto e subiriam em dobro (tarefa a cada 30 min, 18/10)."""
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                        "ForEach-Object { \"$($_.ProcessId) $($_.CommandLine)\" }"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    eu = {str(os.getpid()), str(os.getppid())}  # o python do venv é um lançador: pai e filho têm a mesma linha
    for linha in (r.stdout or "").splitlines():
        pid, _, cmd = linha.strip().partition(" ")
        if pid not in eu and "parceiro_diario.py" in cmd and " postar" in cmd and "--ensaio" not in cmd:
            return True
    return False


def _reconciliar(its):
    """18/10: no timeout a política mata só o lançador do venv; o postador de verdade segue vivo, espera a trava e
    pode subir depois sem ninguém gravar. Cada 'verificar' casa com o upload órfão do ledger (mesmo canal, arquivo
    video.mp4, até 45 min depois do timeout, id ainda sem dono); sem upload e sem postador vivo = volta pra fila."""
    verif = sorted((x for x in its if x["estado"] == "verificar"), key=lambda x: x["d"]["timeout_em"])
    if not verif:
        return
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ForEach-Object { $_.CommandLine }"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    vivos = [l for l in (r.stdout or "").splitlines() if "youtube_web_poster" in l]
    donos = {x["d"]["posted_url"].rsplit("/", 1)[-1] for x in its if x["d"].get("posted_url")}
    ledger = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    for x in verif:
        pasta = x["pj"].parent.name
        if any(pasta in l for l in vivos):
            continue  # o postador órfão ainda está subindo este
        t0 = _dt(x["d"]["timeout_em"])
        achou = next((u for u in ledger if u.get("canal_id") == x["canal"] and u.get("arquivo") == "video.mp4"
                      and u["video_id"] not in donos and t0 <= _dt(u["ts"]) <= t0 + timedelta(minutes=45)), None)
        d = json.loads(x["pj"].read_text(encoding="utf-8"))
        d.pop("timeout_em", None)
        if achou:
            donos.add(achou["video_id"])
            d.update(posted_url=f"https://youtu.be/{achou['video_id']}", posted_at=achou["ts"],
                     agendado_para=(_dt(achou.get("publish_at") or "") or _dt(achou["ts"])).isoformat(timespec="seconds"))
            log(f"{x['canal']}: {pasta} tinha subido depois do timeout -> {d['posted_url']}")
        else:
            d.pop("canal_postado", None)
            log(f"{x['canal']}: {pasta} NÃO subiu no timeout — volta pra fila")
        x["pj"].write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _serie_esperando(cid):
    """12/11: True se há parte da série da dona (colab\\publicar_ja.json) com ficha pronta em na_nuvem e ainda não
    postada, e o canal dono da série é este (Fio da Meada). Falhou a leitura = False (não segura nada)."""
    try:
        colab = Path(r"D:\recapd-ambientes\producao\colab")
        ja = set(json.loads((colab / "publicar_ja.json").read_text(encoding="utf-8")))
        post = {x.get("nome", "")[:11] for x in json.loads((colab / "longos_postados.json").read_text(
            encoding="utf-8")).get("postados", [])}
        fichas = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
        prontas = [d for d in fichas.iterdir() if d.name[:11] in ja and d.name[:11] not in post
                   and (d / "nuvem.json").exists() and "Medieval" in d.name]
        return bool(prontas) and cid == "novo_codigo_inteligente_n7j"
    except (OSError, ValueError):
        return False


def _no_notebook(cid):
    """Canal ativado nos notebooks (postador bin/maquina_remota.py): sobe pelo Chrome de lá, sem a fila do PC1."""
    try:
        if str(POSTADOR_BIN) not in sys.path:
            sys.path.insert(0, str(POSTADOR_BIN))
        import youtube_web_poster as yw
        _, e = yw.entrada_do_cred(cid)
        return bool(e and e.get("maquina"))
    except Exception:  # noqa: BLE001
        return False


def _esperar_trava(maximo_s=1500):
    """O timeout da política conta desde a chamada; esperar a trava lá dentro comia o tempo do upload (18/10)."""
    def ocupada():
        try:
            return time.time() - TRAVA_WEB.stat().st_mtime < 3 * 3600  # a mais velha o postador apaga sozinho
        except OSError:
            return False
    fim = time.time() + maximo_s
    while ocupada() and time.time() < fim:
        time.sleep(10)
    return not ocupada()


LINGUA_SEM_NICHO = {"financas"}  # conteúdo do Brasil: não vira versão em outra língua
LINGUA_TESTE = 0.15              # chance de a língua aceitar a fonte mesmo sem ser o nicho sorteado


def _linguas_para(c, fila, alvo_fila, tipo_fonte):
    """Línguas que ganham a versão DESTA fonte. 23/10 (dono: "nas outras línguas tente outros tipos de vídeo além de
    manhwa"): até aqui toda versão era manhwa (ru 0/5, it 0/3, th 0/3 no placar; vi 2/3 e hi 4/6 vão bem). Cada canal
    de língua sorteia o nicho (Thompson no placar nicho_canal dele; nicho sem medida = aposta) e só entra quando a
    fonte é desse nicho (ou LINGUA_TESTE das vezes). Fila da língua vazia = aceita qualquer nicho (nunca sem post)."""
    import random
    try:
        import placar_titulos
    except Exception:  # noqa: BLE001
        placar_titulos = None
    tipos = sorted({f["tipo"] for f in c.get("fontes", [])} - LINGUA_SEM_NICHO) or [tipo_fonte]
    out = []
    # 10/11: ru/th/vi tinham 1 vídeo "pendente" parado há dias (análise que nunca rodou) e a língua só ganha vídeo
    # com fila 0 → 0 vídeo novo; hi/it ganhavam vídeo mas o canal está TRAVADO pelo YouTube (não sobe nunca).
    # Agora: "esperando" com mais de 24 h não conta na fila; canal travado (trava_conta) não recebe versão.
    agora, fila = time.time(), Counter(fila)
    for x in itens(c):
        if x["estado"] == "esperando" and agora - x["mtime"] > 86400 and x.get("canal") in fila:
            fila[x["canal"]] = max(0, fila[x["canal"]] - 1)
    travados = set()
    try:
        sys.path.insert(1, r"D:\postador-de-videos\bin")  # depois do bin do recapd (nunca na frente)
        import trava_conta
        import youtube_web_poster as ywp
        for lang, d in c["idiomas"].items():
            slug, _e = ywp.entrada_do_cred(d["canal"])
            if slug and trava_conta.checar(slug):
                travados.add(lang)
    except Exception as e:  # noqa: BLE001
        log(f"línguas: trava_conta indisponível ({type(e).__name__}) — sigo sem pular travados")
    for lang, d in c["idiomas"].items():
        cid = d["canal"]
        if lang in travados or not d.get("ativo", True) or fila[cid] >= d.get("fila_alvo", alvo_fila):
            continue
        if fila[cid] == 0:
            out.append(lang)
            continue
        if tipo_fonte in LINGUA_SEM_NICHO:
            continue
        try:
            pl = placar_titulos.taxas("nicho_canal", cid) if placar_titulos else {}
        except Exception:  # noqa: BLE001
            pl = {}
        sorteio = {n: random.betavariate(pl.get(n, (0, 0))[1] + 1, pl.get(n, (0, 0))[0] - pl.get(n, (0, 0))[1] + 1)
                   for n in tipos}
        if max(sorteio, key=sorteio.get) == tipo_fonte or random.random() < LINGUA_TESTE:
            out.append(lang)
    # 01/11 (dona: "cada vídeo é pra ser único"): só uma versão de cada fonte sobe. A tradução só é feita pra uma
    # língua que ficou SEM fila (nunca sem postagem; as línguas também recebem o hipercool) e ela tem a preferência
    # na postagem — a versão pt dessa fonte não sobe (veja postar)
    out = [lang for lang in out if fila[c["idiomas"][lang]["canal"]] == 0]
    out = sorted(out, key=lambda lang: fila[c["idiomas"][lang]["canal"]])[:min(1, c.get("linguas_por_fonte", 1))]
    if out:
        log(f"línguas: {', '.join(out)} recebem a versão desta fonte [{tipo_fonte}]")
    return out


def _por_dia_com_rampa(pol, canal, base):
    """23/10 (dono): a rampa do postador (rampa_canais.py: canal que rende e aguenta sobe 4 -> 5...) vale aqui também —
    cada degrau extra = +1 Short do parceiro por dia em TODOS os dias da semana (os já agendados ganham a vaga).
    Nunca passa do teto do canal no postador (que soma todos os projetos)."""
    try:
        extra = pol._extra_rampa(canal)
        return max(1, min(base + extra, pol.teto_canal(canal)))
    except Exception:  # noqa: BLE001
        return base


def _horarios_para(horarios, por_dia):
    """Horários suficientes pro por_dia: faltando (rampa subiu), a vaga nova vai no meio do maior intervalo."""
    hs = sorted(set(horarios))
    mins = [int(h[:2]) * 60 + int(h[3:5]) for h in hs]
    while len(mins) < por_dia and len(mins) >= 2:
        i = max(range(len(mins) - 1), key=lambda k: mins[k + 1] - mins[k])
        if mins[i + 1] - mins[i] < 100:  # sem 50 min de folga dos dois lados: não espreme
            break
        mins.insert(i + 1, (mins[i] + mins[i + 1]) // 2)
    return [f"{m // 60:02d}:{m % 60:02d}" for m in mins]


def postar(args):
    if not args.ensaio and _outro_postar_rodando():
        log("postagem: outra rodada ainda subindo — pulando")
        return
    c = cfg()
    if not c.get("ligado", True):
        log("postagem: desligada (config/parceiro.json ligado=false)")
        return
    if DESLIGADA.exists():
        log("postagem: DESLIGADA no postador (config/POSTAGEM_DESLIGADA.json) — nada sobe")
        return
    pol = _politica()
    parada = pol.parada_ativa()
    if parada:
        log(f"postagem: PARADA GERAL desde {parada.get('desde')}: {parada.get('motivo')} — nada sobe")
        return
    agora = datetime.now().astimezone()
    if not args.ensaio:
        _reconciliar(itens(c))
    its = itens(c)
    postadas = _fontes_postadas(its)
    if not args.ensaio:
        try:
            _json_atomico(FONTES_POSTADAS, postadas)
        except OSError:
            pass
    nomes = {cid: d["nome"] for cid, d in destinos(c).items()}
    led = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    # (dia Brasil, idioma) -> fontes que já saem nesse dia; por idioma: a versão traduzida não repete pro público dela
    usados = defaultdict(set)
    ultimo = {}                # canal -> publicação mais recente (agendada ou feita) de Short do parceiro
    for x in its:
        quando = _dt(x["d"].get("agendado_para") or x["d"].get("posted_at") or "")
        if x["estado"] == "postado" and quando:
            usados[(quando.astimezone(FUSO_BR).date(), x["d"].get("idioma", "pt"))].add(x["fonte"])
            ultimo[x["canal"]] = max(ultimo.get(x["canal"], quando), quando)
    def faltas(cid, dst):
        """(sem vídeo hoje lá, sem vídeo hoje no Brasil), contando vídeo de qualquer projeto (ledger)."""
        tz = ZoneInfo(dst["fuso"])
        pubs = [_dt(x["d"]["agendado_para"]) for x in its if x["canal"] == cid and x["d"].get("agendado_para")]
        pubs = [m for m in pubs if m] + [t for t in (_dt(u.get("publish_at") or u.get("ts") or "")
                                                     for u in led if u.get("canal_id") == cid) if t]
        return (not any(m.astimezone(tz).date() == agora.astimezone(tz).date() for m in pubs),
                not any(m.astimezone(FUSO_BR).date() == agora.astimezone(FUSO_BR).date() for m in pubs))

    # 19/10: a rodada levava 1 h agendando os próximos dias dos canais na ordem do config antes de chegar nos que
    # estavam sem post hoje; 1ª passada = só esses, 1 vídeo cada; 2ª passada = todos, enchendo a semana
    dests = list(destinos(c).items())
    fila = [(cid, dst, True) for cid, dst in dests if any(faltas(cid, dst))] + [(cid, dst, False) for cid, dst in dests]
    parar = set()  # deu timeout/erro nesta rodada: não tenta de novo na 2ª passada
    for cid, dst, so_urgente in fila:
        if cid in parar:
            continue
        nome = dst["nome"]
        if _em_cooldown_limite(cid):
            if not so_urgente:  # 1 aviso por rodada (o canal aparece nas 2 passadas)
                log(f"{nome}: esperando passar o limite de uploads da conta — pulando")
            continue
        canal, err = pol.achar_canal(cid)
        if not canal:
            log(f"{nome}: {err}")
            continue
        bloq = pol.motivo_bloqueio(canal)
        if bloq:
            log(f"{nome}: bloqueado no postador ({bloq}) — pulando")
            continue
        # a vaga do dono do canal já sai de pol.cota_restante(canal, "parceiro") (cadastro único, 18/10); reservar mais
        # uma aqui impedia deixar os de amanhã programados hoje (dono 18/10: "hoje mesmo fazer os de amanhã")
        minimo = 1
        por_dia = _por_dia_com_rampa(pol, canal, int(dst.get("por_dia", c.get("por_dia", 1))))
        horarios = _horarios_para(dst.get("horarios") or [dst["horario"]], por_dia)
        tz = ZoneInfo(dst["fuso"])
        ordem = _ordem_horarios(horarios, tz)  # 22/10: o horário que mais rende primeiro (placar), não o mais cedo
        meus = [_dt(x["d"]["agendado_para"]) for x in its if x["canal"] == cid and x["d"].get("agendado_para")]
        # dono 18/10: canal sem post hoje = urgente, agendado pros próximos minutos (regra "nunca sem postagem").
        # Hoje = no Brasil E na hora de lá, contando vídeo de qualquer projeto (ledger)
        hoje_la = agora.astimezone(tz).date()
        hoje_br = agora.astimezone(FUSO_BR).date()
        falta_la, falta_br = faltas(cid, dst)
        urgente = falta_la or falta_br
        if so_urgente and not urgente:
            continue
        for _vaga in range(1 if so_urgente else por_dia):
            if pol.cota_restante(canal, PROJETO) < (1 if urgente else minimo):
                log(f"{nome}: cota do dia {pol.cota_restante(canal, PROJETO)} — deixa a vaga pro dono do canal")
                break
            # 23/10: 5 envios no mesmo canal em ~1,5 h de madrugada (agenda da semana) e vários canais pegaram o
            # "limite diário de envios" do YouTube -> no mínimo ESPACO_UPLOAD_MIN entre 2 envios do canal (qualquer projeto)
            ult = max((pol._dt(r.get("ts")) for r in pol._ler_ledger() if pol._do_canal(r, canal) and r.get("ts")),
                      default=None)
            if ult and not urgente and datetime.now().astimezone() - ult < timedelta(minutes=ESPACO_UPLOAD_MIN):
                log(f"{nome}: último envio do canal às {ult.astimezone():%H:%M} — o próximo só depois de "
                    f"{(ult + timedelta(minutes=ESPACO_UPLOAD_MIN)).astimezone():%H:%M} (envio em rajada barra o canal)")
                break
            # próximo horário do canal (hoje ou amanhã, hora de lá) num dia com menos de por_dia agendados
            agora_la = agora.astimezone(tz)
            alvo = None
            if urgente:
                # horário normal de hoje que ainda cubra o dia que falta (de madrugada não publica às 00:30 à toa);
                # senão na hora do upload (~4 min cada): < 5 min o postador publicaria direto, e o Studio arredonda
                # pra cima em passos de 15 min -> sai entre 11 e 25 min
                for h in ordem:
                    hh, mm = (int(v) for v in h.split(":"))
                    t = agora_la.replace(hour=hh, minute=mm, second=0, microsecond=0)
                    if (t >= agora_la + timedelta(minutes=70) and (not falta_la or t.date() == hoje_la)
                            and (not falta_br or t.astimezone(FUSO_BR).date() == hoje_br)):
                        alvo = t
                        break
                alvo = alvo or datetime.now().astimezone() + timedelta(minutes=11)
            else:
                # dono 18/10: uma semana programada em cada canal. 23/10 (dono): EM ORDEM — o dia mais próximo fica
                # completo (por_dia, já com a rampa) antes de começar o seguinte; antes era 1 por dia nos 7 dias
                # antes do 2º e do 3º, e a vaga nova da rampa nunca aparecia nos dias já agendados
                for d in range(DIAS_FRENTE):
                    dia_la = (agora_la + timedelta(days=d)).date()
                    no_dia = [m for m in meus if m and m.astimezone(tz).date() == dia_la]
                    if len(no_dia) >= por_dia:
                        continue
                    for h in ordem:
                        hh, mm = (int(v) for v in h.split(":"))
                        t = agora_la.replace(year=dia_la.year, month=dia_la.month, day=dia_la.day, hour=hh,
                                             minute=mm, second=0, microsecond=0)
                        if t >= agora_la + timedelta(minutes=70) and all(abs((t - m).total_seconds()) > 3000
                                                                          for m in no_dia):
                            alvo = t
                            break
                    if alvo:
                        break
            if not alvo:
                log(f"{nome}: {por_dia} por dia já agendados nos próximos {DIAS_FRENTE} dias")
                break
            dia = alvo.astimezone(FUSO_BR).date()
            prontos = [x for x in its if x["canal"] == cid and x["estado"] == "pronto"]
            for x in [x for x in prontos if not x["mp4"].exists()]:
                # 12/11 dona ("pode mandar as reservas pro Drive"): reserva_shorts_drive.py tira o video.mp4 que passa de
                # 7 dias e deixa _NO_DRIVE.txt — na vez de postar ele volta do Drive (o próximo da fila, 1 por vez)
                no_drive = x["pj"].parent / "_NO_DRIVE.txt"
                if no_drive.exists() and os.environ.get("RESERVA_VOLTA_DO_DRIVE", "1") != "0":
                    try:
                        origem = no_drive.read_text(encoding="utf-8").strip()
                        subprocess.run([r"D:\tools\rclone.exe", "copyto", origem, str(x["mp4"]), "--retries", "3"],
                                       capture_output=True, timeout=900, creationflags=0x08000000)
                        if x["mp4"].exists():
                            log(f"{nome}: {x['pj'].parent.name} voltou do Drive pra postar")
                            no_drive.unlink(missing_ok=True)
                            continue
                    except Exception as e:  # noqa: BLE001
                        log(f"{nome}: {x['pj'].parent.name} não voltou do Drive ({type(e).__name__})")
            for x in [x for x in prontos if not x["mp4"].exists()]:  # 22/10: o marcar_aprovacao derrubava a rodada inteira
                log(f"{nome}: {x['pj'].parent.name} está pronto mas sem {x['mp4'].name} — pulado")
                x["estado"] = "sem_video"
            prontos = [x for x in prontos if x["estado"] == "pronto"]
            for x in prontos:  # 22/10: fonte já postada em OUTRO canal nunca sobe (regra do dono)
                # 01/11 (dona: "cada vídeo é pra ser único; não pode ser o mesmo vídeo indo pra mais de um canal
                # nosso"): vale em QUALQUER língua (antes só dentro da mesma: o mesmo vídeo saía em pt + 3 línguas) e
                # sem a exceção dos virais (virais_fracos desligado no parceiro.json)
                f_id = _id_fonte(x["fonte"]) or ""
                outro = next((por[f_id] for por in postadas.values() if f_id in por and por[f_id] != cid), None)
                if outro:
                    x["estado"] = "repetido"
                    log(f"{nome}: {x['pj'].parent.name} SEGURADO — o mesmo vídeo do parceiro já foi postado em "
                        f"{nomes.get(outro, outro)} (nunca o mesmo vídeo em 2 canais)")
                    if not args.ensaio:
                        _gravar(x["pj"], pronto=False, revisao=f"reprovado (segurado): fonte repetida — o mesmo vídeo "
                                f"do parceiro já foi postado em {nomes.get(outro, outro)} (dono: nunca o mesmo vídeo "
                                "em 2 canais)")
            prontos = [x for x in prontos if x["estado"] == "pronto"]
            # 12/11: canal de nicho SÉRIO (público que compra automação: negócios/saúde/imobiliário) com narrador que não
            # encaixa no nicho (nota 0 em narradores_nichos.json — Pica-Pau, Chapolin...) não sobe: o PC2/PC3 usava a
            # tabela velha e o canal novo ia estrear com voz de desenho. PARCEIRO_VOZ_NICHO_SERIO=0 desliga.
            if dst.get("nicho") in NICHOS_SERIOS and os.environ.get("PARCEIRO_VOZ_NICHO_SERIO", "1") != "0":
                for x in prontos:
                    nota = _nota_voz(x["d"].get("narrador"), dst["nicho"])
                    if nota is not None and nota < 1:
                        x["estado"] = "voz_fora"
                        log(f"{nome}: {x['pj'].parent.name} SEGURADO — voz {x['d'].get('narrador')} tem nota {nota} "
                            f"no nicho {dst['nicho']} (canal sério)")
                        if not args.ensaio:
                            _gravar(x["pj"], pronto=False, revisao=f"segurado: voz {x['d'].get('narrador')} não "
                                    f"encaixa no nicho {dst['nicho']} (nota {nota}) — refazer com voz séria")
                prontos = [x for x in prontos if x["estado"] == "pronto"]
            # 01/11: a versão pt espera quando a mesma fonte tem versão numa língua que ficou sem fila (a produção
            # só faz essa versão pra língua vazia); se a da língua for reprovada, a pt volta a valer
            # 12/11 dona ("por que as fontes repetidas acontecem? não dá pra controlar?"): o Short pt e a versão em
            # língua saíam da MESMA fonte; a língua postava antes e o pt (canal que rende) virava "fonte repetida" e ia
            # pro lixo (19 em 11-12/11). Agora o PT tem a preferência: a versão da língua é que espera o pt. PREFERE_PT=0
            # volta a regra de 01/11.
            if dst["idioma"] == "pt" and os.environ.get("PREFERE_PT", "1") == "0":
                pendentes_lang = {_id_fonte(y["fonte"]) for y in its if y["lang"] != "pt"
                                  and y["estado"] in ("pronto", "esperando") and _id_fonte(y["fonte"])}
                prontos = [x for x in prontos if _id_fonte(x["fonte"]) not in pendentes_lang]
            elif dst["idioma"] != "pt" and os.environ.get("PREFERE_PT", "1") != "0":
                pendentes_pt = {_id_fonte(y["fonte"]) for y in its if y["lang"] == "pt"
                                and y["estado"] in ("pronto", "esperando") and _id_fonte(y["fonte"])}
                prontos = [x for x in prontos if _id_fonte(x["fonte"]) not in pendentes_pt]
            livres = [x for x in prontos if x["fonte"] not in usados[(dia, dst["idioma"])]]
            livres.sort(key=lambda x: not x["d"].get("viral_de"))  # 30/10: a versão do viral sai antes do Short comum
            if not livres:
                outros = Counter(x["estado"] for x in its if x["canal"] == cid)
                log(f"{nome}: nada pronto pra {alvo:%d/%m %H:%M} ({dict(outros) or 'fila vazia'}"
                    + (f"; {len(prontos)} com a fonte já usada nesse dia" if prontos else "") + ")")
                break
            x = livres[0]
            # 1 h longe dos vídeos do canal (de qualquer projeto) + teto do dia de lá com a vaga do dono guardada
            quando = pol.horario_publicacao(canal, alvo, PROJETO) or alvo
            tit = x["d"].get("titulo") or x["pj"].parent.name
            if args.ensaio:
                log(f"[ensaio] {nome}: {x['pj'].parent.name} -> {quando.astimezone(tz):%d/%m %H:%M} lá | {tit[:70]}")
                usados[(dia, dst["idioma"])].add(x["fonte"])
                x["estado"] = "ensaio"
                x["d"]["agendado_para"] = quando.isoformat(timespec="seconds")
                meus.append(quando)
                urgente = False
                continue
            thumb = x["pj"].parent / x["d"]["thumb"] if x["d"].get("thumb") else None
            if thumb and not (thumb.is_file() and thumb.stat().st_size < 2_000_000):
                thumb = None
            # 12/11 23h (Medieval 13 pronta às 22h10 e presa: os Shorts gastaram o limite diário de envios do Fio da
            # Meada entre 00h e 02h, agendados pra daqui a 2 dias). Canal com parte da SÉRIE da dona pronta e não
            # postada = Short não sobe (a vaga do dia é da série). SERIE_RESERVA_ENVIO=0 desliga.
            if os.environ.get("SERIE_RESERVA_ENVIO", "1") != "0" and _serie_esperando(cid):
                log(f"{nome}: parte da série da dona pronta esperando este canal — Short não sobe agora")
                break
            if not _no_notebook(cid) and not _esperar_trava():
                log(f"{nome}: trava de upload do navegador ocupada há 25 min — fica pra próxima rodada")
                return
            # 23/10: o vídeo pode ter sido SEGURADO depois que esta rodada leu a lista (a espera da trava leva até 25 min)
            # — sem reler, o sem-obra-a675af (narração = erro do Gemini) subiu 8 min depois de segurado
            try:
                agora_d = json.loads(x["pj"].read_text(encoding="utf-8"))
            except (OSError, ValueError):
                agora_d = {"pronto": False, "revisao": "não consegui reler o postar.json (fica pra próxima rodada)"}
            if agora_d.get("posted_url") or agora_d.get("timeout_em"):  # outro processo já subiu/tentou neste meio-tempo
                log(f"{nome}: {x['pj'].parent.name} já foi enviado por outro processo — não sobe de novo")
                x["estado"] = "postado"
                continue
            if not agora_d.get("pronto") or re.search(r"segurad|reprovad", str(agora_d.get("revisao") or ""), re.I):
                log(f"{nome}: {x['pj'].parent.name} foi segurado depois da leitura da fila — NÃO sobe "
                    f"({str(agora_d.get('revisao') or 'pronto=False')[:80]})")
                x["estado"] = "segurado"
                continue
            # 23/10 (dona, depois do mushishi): OUVE o Short antes de subir — fala vazia, erro da IA, inglês num vídeo
            # em português ou longe do roteiro = segura e avisa. Sem como conferir (Groq fora) = sobe normal.
            try:
                import conferir_audio
                if not conferir_audio.antes_de_subir(x["pj"].parent, log=log):
                    x["estado"] = "segurado"
                    continue
            except Exception as e:  # noqa: BLE001
                log(f"{nome}: conferência do áudio não rodou ({type(e).__name__}) — sobe normal")
            pol.marcar_aprovacao(x["mp4"], "aprovado", NOTA_APROVACAO)
            status, info = pol.postar_youtube(
                cid, str(x["mp4"]), tit, x["d"].get("descricao", ""), x["d"].get("tags") or [], privacy="public",
                publish_at=pol.rfc3339(quando), projeto=PROJETO, thumbnail=thumb, tipo=x["d"].get("tipo") or "short",
                sintetico=bool(x["d"].get("sintetico")))  # 23/10: voz de pessoa real no elenco = conteúdo alterado
            if status in ("parado", "suspenso"):
                log(f"{nome}: {status} — {info}. PAROU TUDO")
                return
            x["estado"] = "postado"
            if status == "timeout":
                _gravar(x["pj"], timeout_em=agora.isoformat(timespec="seconds"), canal_postado=nome)
                log(f"{nome}: TIMEOUT no upload de {x['pj'].parent.name} — conferir no Studio (fica 'verificar')")
                parar.add(cid)
                break
            if status != "ok":
                log(f"{nome}: não subiu {x['pj'].parent.name} ({status}: {info})")
                parar.add(cid)
                if status == "limite":
                    ate = _esperar_limite(cid)
                    log(f"{nome}: limite de uploads da conta — tenta de novo às {ate:%H:%M} ({ESPERA_LIMITE_H} h)")
                break
            efetivo = _publish_efetivo(x["mp4"]) or quando
            _gravar(x["pj"], posted_url=info, posted_at=agora.isoformat(timespec="seconds"),
                    agendado_para=efetivo.isoformat(timespec="seconds"), canal_postado=nome)
            x["d"]["agendado_para"] = efetivo.isoformat(timespec="seconds")  # a 2ª passada vê o canal já com post hoje
            usados[(efetivo.astimezone(FUSO_BR).date(), dst["idioma"])].add(x["fonte"])
            if _id_fonte(x["fonte"]):  # registro durável: esta fonte nunca mais sobe em outro canal (qualquer língua)
                postadas.setdefault(dst["idioma"], {})[_id_fonte(x["fonte"])] = cid
                try:
                    _json_atomico(FONTES_POSTADAS, postadas)
                except OSError:
                    pass
            meus.append(efetivo)
            # o Studio arredonda em passos de 15 min; só anota quando o politica trocou a hora de verdade
            mudou = f" (pedido {quando.astimezone(tz):%d/%m %H:%M})" if abs((efetivo - quando).total_seconds()) > 900 else ""
            log(f"{nome}: AGENDADO{' (URGENTE: canal sem post hoje)' if urgente else ''} {info} -> "
                f"{efetivo.astimezone(tz):%d/%m %H:%M} lá{mudou} | {tit[:70]}")
            urgente = False

def status(args):
    c = cfg()
    its = itens(c)
    print(f"Shorts do parceiro: {len(its)} | ligado={c.get('ligado', True)} | postagem do postador "
          f"{'DESLIGADA' if DESLIGADA.exists() else 'ligada'}")
    for cid, dst in destinos(c).items():
        meus = [x for x in its if x["canal"] == cid]
        cont = Counter(x["estado"] for x in meus)
        prox = [x for x in meus if x["estado"] == "postado" and _dt(x["d"].get("agendado_para") or "")
                and _dt(x["d"]["agendado_para"]) > datetime.now().astimezone()]
        cd = " [LIMITE DIÁRIO]" if _em_cooldown_limite(cid) else ""
        print(f"  {dst['nome'][:26]:26} [{dst['idioma']}] {dict(cont) or '-'}{cd}"
              + (f" | agendado {_dt(prox[-1]['d']['agendado_para']):%d/%m %H:%M}" if prox else ""))
    rep = [x for x in its if x["estado"] in ("reprovado", "verificar")]
    if rep:
        print("\nPrecisam de olho humano (folha <pasta>\\video.revisao.jpg; liberar: "
              "python bin\\anime_revisao.py --aprovar <postar.json> <quem>):")
        for x in rep:
            print(f"  [{x['estado']}] {x['pj']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["status", "producao", "postar"])
    ap.add_argument("--ensaio", action="store_true", help="postar: só mostra o que subiria e quando")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    {"status": status, "producao": producao, "postar": postar}[args.acao](args)


if __name__ == "__main__":
    main()
