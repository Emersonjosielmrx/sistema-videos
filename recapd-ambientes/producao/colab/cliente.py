r"""
PC1 ↔ Colab (recap longo). Plano: producao/COLAB_RECAP_LONGO.md.

  enviar(work, video, roteiro, titulo) -> id      sobe source.mp4 + roteiro.txt + json pequenos pra manhwa-drive:colab_recap/fila/<id>
  esperar(id, destino_mp4, horas=6) -> bool       espera pronto.json/erro.json, baixa o mp4, apaga a pasta do Drive
  python cliente.py teste <pasta_work> <url> "<titulo>"   legenda + roteiro aqui, envia e espera (1º teste)
  python cliente.py vivo                                   quando a Colab deu sinal de vida pela última vez
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys as _sys
if _sys.platform == "win32":  # dona 26/10: rclone/ssh/scp/python filhos SEM janela na tela (PC1 e PC2)
    for _p in (r"D:\hipercool-materiais\comum", r"C:\hipercool-materiais\comum"):
        if Path(_p, "sem_janela.py").exists():
            _sys.path.append(_p)
            import sem_janela  # noqa: F401,E402
            break

RCLONE = r"D:\tools\rclone.exe"
FILA = "manhwa-drive:colab_recap/fila"
FILA_SRC = "manhwa-drive:colab_recap/fila_src"
os.environ["RCLONE_DRIVE_USE_TRASH"] = "false"  # apagado na lixeira ainda conta na cota do Drive
VIVO = "manhwa-drive:colab_recap/vivo.json"
BIN = Path(__file__).resolve().parent.parent / "bin"


_TRANSITORIO = ("quota", "rate limit", "ratelimit", "userratelimit", "403", "429", "500", "502", "503", "504",
                "timeout", "timed out", "connection reset", "connection refused", "unexpected eof", "tls handshake",
                "no such host", "temporary", "try again", "internal error", "backend error")


def _rc(*args, saida=False, tentativas=7):
    """rclone com nova tentativa (25/10: o Google devolve 403 de cota na chave pública do rclone a qualquer hora).
    Cota/5xx/rede: espera 20 s, 40 s ... até 10 min. 'Não existe' (rc 3/4) sobe na hora — quem chama decide."""
    for i in range(tentativas):
        try:
            # 01/11: sem encoding o Windows lia em cp1252 — pedido.json com acento matava o alimentador (rc=1)
            r = subprocess.run([RCLONE, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=7200)
        except subprocess.TimeoutExpired:
            r = subprocess.CompletedProcess(args, 5, "", "timeout")
        if r.returncode == 0:
            return r.stdout if saida else None
        err = (r.stderr or "")[-800:]
        transitorio = r.returncode in (5, 6, 8) or (r.returncode not in (1, 3, 4)
                                                    and any(t in err.lower() for t in _TRANSITORIO))
        if not transitorio or i == tentativas - 1:
            raise RuntimeError(f"rclone {args[0]} falhou (rc={r.returncode}): {err[-400:]}")
        espera = min(600, 20 * 2 ** i) + random.uniform(0, 15)
        print(f"{datetime.now():%H:%M} rclone {args[0]} falhou (temporário) — de novo em {espera:.0f} s", flush=True)
        time.sleep(espera)


def _ler_json(remoto):
    try:
        return json.loads(_rc("cat", remoto, saida=True))
    except (RuntimeError, ValueError):
        return None


def vivo():
    d = _ler_json(VIVO)
    if not d:
        return None
    return (datetime.now(timezone.utc) - datetime.fromisoformat(d["em"])).total_seconds()


def gravar_token():
    """Token de 1 h do manhwa-drive (escopo drive.file) pra Colab baixar código/assets (baixar_drive.py)."""
    subprocess.run([RCLONE, "about", "manhwa-drive:"], capture_output=True, check=True)  # renova se venceu
    conf = json.loads(_rc("config", "dump", saida=True))
    token = json.loads(conf["manhwa-drive"]["token"])["access_token"]
    _rc("mkdir", FILA_SRC)
    itens = json.loads(_rc("lsjson", "manhwa-drive:colab_recap", "--dirs-only", saida=True))
    ids = {i["Name"]: i["ID"] for i in itens}
    tmp = Path(__file__).with_name(f"_token_manhwa_{os.getpid()}.json")  # token_loop e alimentador gravam juntos
    tmp.write_text(json.dumps({"access_token": token, "raiz_id": ids["raiz"], "src_id": ids["fila_src"]}),
                   encoding="utf-8")
    try:
        _rc("copyto", str(tmp), "manhwa-drive:colab_recap/token_manhwa.json")
    finally:
        tmp.unlink()


VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")


def _voz_do_longo(tipo):
    """Voz clonada do longo pelo mesmo rodízio dos Cortes (anime_voz_clonada.proxima pelo nicho): (pasta da voz, base
    francisca|kokoro|misto) — 26/10 a base dos Cortes vale também (o Kaggle tem Kokoro). None = longo sem clone."""
    try:
        sys.path.insert(0, str(BIN))
        import anime_voz_clonada
        voz, base = anime_voz_clonada.proxima(tipo or "manhwa")
        d = VOZES / voz
        if all((d / n).exists() for n in (f"{voz}.pth", f"{voz}.index", "tom_2_edge_francisca.txt")):
            if base in ("kokoro", "misto") and not (d / "tom_1_kokoro.txt").exists():
                base = "francisca"
            return d, base
        print(f"voz {voz} incompleta pra nuvem — longo sem clone", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"escolha da voz falhou ({type(e).__name__}: {e}) — longo sem clone", flush=True)
    return None, None


VPS = "hermes-prod"
VPS_ENTRADA = "/opt/recap_central/entrada"
SCP = r"C:\Program Files\Git\usr\bin\scp.exe"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"


TESTE_NARRADORES = Path(__file__).with_name("teste_narradores.json")


def _teste_narradores():
    """(dados, lista de vozes) do próximo longo com revezamento de narradores (teste_narradores.json, modo contínuo),
    ou (None, None). Só vozes que já estão no Drive (subir_vozes.py -> vozes_no_drive.json), na ordem, a partir do
    cursor; começa quando há pelo menos 'minimo' delas lá."""
    try:
        t = json.loads(TESTE_NARRADORES.read_text(encoding="utf-8"))
        no_drive = set(json.loads(Path(__file__).with_name("vozes_no_drive.json").read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return None, None
    if not t.get("continuo"):
        return None, None
    ruins = set(t.get("ruins") or [])  # 28/10 dona: "narradores ruins pra te treinar: Patrick Estrela"
    pool = [v for v in t.get("ordem", []) if v in no_drive and v not in ruins and (VOZES / v / f"{v}.pth").exists()]
    if len(pool) < int(t.get("minimo", 6)):
        return None, None
    if t.get("grupos"):
        return t, _narradores_por_grupo(t, set(pool) | {v for v in no_drive if (VOZES / v / f"{v}.pth").exists()} - ruins)
    n = min(int(t.get("por_video", 10)), len(pool))
    c = int(t.get("cursor", 0)) % len(pool)
    vozes = (pool[c:] + pool[:c])[:n]
    # 28/10 dona: "as vozes iniciais têm que ser sempre as mais atrativas, principalmente a primeira" — abre com uma
    # das 'atrativas' (rodízio entre elas) e as outras atrativas sorteadas vão logo depois
    atr = [v for v in t.get("atrativas") or [] if v in pool]
    if atr:
        primeira = atr[int(t.get("cursor", 0)) // max(1, n) % len(atr)]
        resto = [v for v in vozes if v != primeira]
        vozes = [primeira] + sorted(resto, key=lambda v: v not in atr)
        vozes = vozes[:n]
    return t, vozes


def _narradores_por_grupo(t, disponiveis):
    """Dona 29/10: 1º narrador (resumo + começo) dos 'resumo'; 2º dos 'secundarios'; do 3º em diante 'terciarios'
    (mulheres e engraçados). Tipo do vídeo sorteado por 'modos' (normalmente só primários). Dentro de cada grupo vai
    primeiro quem foi MENOS usado nos últimos 7 dias (garante 1 vídeo de cada primário/secundário por semana)."""
    g = t["grupos"]
    limite = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    uso = {}
    for v in t.get("videos") or []:
        if str(v.get("pid", ""))[:8] >= limite:
            for voz in v.get("vozes") or []:
                uso[voz] = uso.get(voz, 0) + 1

    def ordem(grupo, fora=()):
        cand = [v for v in g.get(grupo, []) if v in disponiveis and v not in fora]
        random.shuffle(cand)
        return sorted(cand, key=lambda v: uso.get(v, 0))

    modos = g.get("modos") or {"so_primarios": 1}
    modo = random.choices(list(modos), weights=list(modos.values()))[0]
    # o 1º é um primário (homens: Momo, Mike...); os outros da lista "resumo" (Fatos Desconhecidos) abrem 1 em 5
    extras = [v for v in ordem("resumo") if v not in g.get("primarios", [])]
    escolhidas = extras[:1] if extras and random.random() < 0.2 and modo != "solo" else ordem("primarios")[:1]
    t["_modo"] = modo  # 30/10: vai pro pedido.json (narradores_modo) pra comparar os modos pelas views
    # 30/10 (dona: "tem que ter vídeos SOLO de narradores, e misturas com mais e com menos narradores, outros só com os
    # da fila 1: Mike, Momo etc."): solo = 1 primário o vídeo inteiro; dupla = 2 primários; mistura_grande = 6-7 vozes
    if modo == "solo":
        pass
    elif modo == "dupla":
        escolhidas += ordem("primarios", escolhidas)[:1]
    elif modo == "mistura_grande":
        escolhidas += (ordem("primarios", escolhidas)[:2] + ordem("secundarios")[:2] + ordem("terciarios")[:2])
    elif modo == "so_primarios":
        escolhidas += ordem("primarios", escolhidas)[:3]
    elif modo == "primarios_secundarios":
        sec, pri = ordem("secundarios"), ordem("primarios", escolhidas)
        escolhidas += [x for par in zip(sec[:2], pri[:2]) for x in par]
    else:
        escolhidas += ordem("secundarios")[:1] + ordem("terciarios")[:3]
    # 31/10 dona: no máx. 5 narradores (trocas ~4-6); Galvão/Chaves só como participação especial curta
    # (anime_tts.revezar põe 3 frases deles no meio de um bloco) — em 1 de cada 3 vídeos com mais de 1 narrador
    escolhidas = escolhidas[:5]
    esp = ordem("participacao_especial", escolhidas)
    if modo != "solo" and esp and (modo in ("com_terciarios", "mistura_grande") or random.random() < 0.33):
        escolhidas.append(esp[0])
    print(f"narradores ({modo}): {', '.join(escolhidas)}", flush=True)
    return escolhidas


def _voz_pro_cache(ssh, voz):
    """26/10: a voz (≈190 MB: .index + .pth) subia em TODO pedido pela internet de casa (~9 min cada). Agora fica num
    cache da VPS (/opt/recap_central/vozes/<voz>) e só sobe o arquivo que falta ou mudou de tamanho."""
    cache = f"/opt/recap_central/vozes/{voz.name}"
    r = subprocess.run(ssh + [f"mkdir -p {cache} && cd {cache} && stat -c '%n %s' * 2>/dev/null"],
                       capture_output=True, text=True, timeout=120)
    la = dict(l.rsplit(" ", 1) for l in r.stdout.splitlines() if " " in l)
    for f in voz.iterdir():
        if f.suffix in (".pth", ".index", ".txt", ".json") and la.get(f.name) != str(f.stat().st_size):
            subprocess.run([SCP, "-q", "-o", "BatchMode=yes", str(f), f"{VPS}:{cache}/{f.name}"], check=True,
                           capture_output=True, timeout=3600)


INTROS_CFG = Path(r"D:\hipercool-videos\config\intros_voz.json")
INTROS_DIR = Path(r"D:\hipercool-materiais\assets\intros_voz")
INTROS_USO = Path(__file__).with_name("intros_uso.json")
_INTRO_CTA = re.compile(r"like|inscrev|inscriç|sininho|notifica|hyp|coment|curtid", re.I)
# canal autorizado (intros_voz.json) -> voz clonada dele
INTRO_VOZ = {"@momomanhwa": "momo", "@mikemanhwa": "mike", "@mattzmanhwa": "mattz", "@drezinnimes": "drezin",
             "@ijaxmanhwa": "ijax", "@oporaodacidadela": "porao"}


def _intro_do_longo(vozes):
    """01/11 dona: as falas de abertura REAIS (Momo, Mike, Porão...; cortadas dos vídeos deles pelo hipercool
    intros_voz.py) nunca tinham entrado no longo. Escolhe uma: do 1º narrador já sorteado, se ele tiver; senão
    qualquer uma (e o dono dela vira o 1º narrador). Rodízio pelo menos usado (intros_uso.json). None = sem."""
    try:
        intros = json.loads(INTROS_CFG.read_text(encoding="utf-8")).get("intros") or []
    except (OSError, ValueError):
        return None
    cands = []
    for i in intros:
        # L-F5 (LONGOS_MELHORIAS.md) 01/11 (LONGOS\referencias\PADROES_COMUNS.md, falha 1): pedir like/inscrição nos primeiros segundos derruba a
        # retenção — só as aberturas SEM pedido (17 de 20 pedem). INTRO_COM_CTA=1 libera as outras.
        if os.environ.get("INTRO_COM_CTA") != "1" and _INTRO_CTA.search(str(i.get("texto", ""))):
            continue
        v = INTRO_VOZ.get(str(i.get("canal", "")).lower())
        wav = INTROS_DIR / str(i.get("arquivo", ""))
        if v and wav.exists() and (VOZES / v / f"{v}.pth").exists() and i.get("palavras"):
            cands.append({**i, "voz": v, "wav": wav})
    if not cands:
        return None
    try:
        usos = json.loads(INTROS_USO.read_text(encoding="utf-8")) if INTROS_USO.exists() else {}
    except (OSError, ValueError):
        usos = {}
    mesma = [c for c in cands if vozes and c["voz"] == vozes[0]]
    pool = mesma or cands
    random.shuffle(pool)
    esc = min(pool, key=lambda c: usos.get(c["id"], 0))
    usos[esc["id"]] = usos.get(esc["id"], 0) + 1
    try:
        INTROS_USO.write_text(json.dumps(usos, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    return esc


EXPERIMENTO = Path(r"D:\video-fila\linhas\LONGOS\experimento.json")


def _variante_do_experimento():
    """{"experimento", "variante", "longo_override"} do teste A/B ativo ou None. O melhorador_longo escreve o
    experimento.json ({"nome", "ativo", "A": {...}, "B": {...}, "enviados": {"A": n, "B": n}}); aqui vai a variante
    com MENOS vídeos enviados (empate = A) e conta. Falhou = pedido normal."""
    try:
        e = json.loads(EXPERIMENTO.read_text(encoding="utf-8"))
        if not e.get("ativo"):
            return None
        env = e.setdefault("enviados", {"A": 0, "B": 0})
        v = "A" if env.get("A", 0) <= env.get("B", 0) else "B"
        env[v] = env.get(v, 0) + 1
        EXPERIMENTO.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
        return {"experimento": e.get("nome"), "variante": v, "longo_override": e.get(v) or {}}
    except (OSError, ValueError, AttributeError):
        return None


def enviar(work, video, roteiro, titulo, extra=None, pid=None):
    """Dona 25/10: o PC prepara, mas não fala com o Kaggle — o pedido vai pra VPS (hermes-prod, vps_central.py), que
    põe na fila do Kaggle e acompanha. Original já no Drive (manhwa-drive:...) vai só como endereço.
    pid (29/10, fila_dona.py): o trabalhador pega o 1º livre por NOME — um pid baixo fura a fila na ordem escolhida."""
    work = Path(work)
    pid = pid or f"{datetime.now():%Y%m%d_%H%M%S}_{work.name[:11]}"
    remoto = f"{VPS_ENTRADA}/{pid}"
    ssh = [SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", VPS]
    subprocess.run(ssh + [f"mkdir -p {remoto}"], check=True, capture_output=True, timeout=120)
    pedido = {"titulo": titulo, "enviado": datetime.now().isoformat(timespec="seconds"), **(extra or {})}
    if not pedido.get("tipo") and (work / "tipo_fonte.txt").exists():  # 30/10: preparar() achou manhwa na fonte
        pedido["tipo"] = (work / "tipo_fonte.txt").read_text(encoding="utf-8").strip()
    arquivos = [p for p in work.glob("*.json") if p.stat().st_size < 5_000_000 and p.name != "_pedido_colab.json"]
    if Path(roteiro).exists():  # sem roteiro (sem legenda do YouTube): o trabalhador transcreve e roteiriza (25/10)
        arquivos.append(Path(roteiro))
    if str(video).startswith("manhwa-drive:"):
        pedido["origem_drive"] = str(video)
    else:
        arquivos.append(Path(video))
    try:  # 28/10: vozes de personagem (falas do jeito do Mike) — o Kaggle baixa do cache de vozes do Drive
        _p = json.loads((Path(__file__).resolve().parent.parent / "config" / "longo.json").read_text(encoding="utf-8"))
        _p = _p.get("personagens") or {}
        _m = json.loads((Path(__file__).resolve().parent.parent / "config" / "longo.json").read_text(encoding="utf-8"))
        _m = [(_m.get("mascote") or {}).get("voz_clone")]  # 28/10: voz clonada da mascote (edge puro nunca)
        if _p.get("ligado") or any(_m):
            pedido["vozes_extra"] = list(dict.fromkeys([v for v in (_p.get("vozes_m") or []) + (_p.get("vozes_f") or [])
                                                        + (_p.get("vozes_monstro") or []) + (_p.get("vozes_vilao") or [])
                                                        + (_p.get("vozes_crianca") or []) + _m if v]))
    except (OSError, ValueError):
        pass
    exp = _variante_do_experimento()
    if exp:  # 28/10: teste A/B do melhorador_longo (linhas\LONGOS\experimento.json) — A e B se alternam por pedido
        pedido.update(exp)
    # 30/10 (dona: "tudo que for subjetivo, se é bom ou não, não deve substituir o antigo e sim virar uma variante pra
    # teste A/B"): config/longo.json "ab_fatores" = {fator: {"A": {chave: valor}, "B": {...}}}; cada pedido sorteia A/B
    # POR FATOR (md5 do pid + fator: independente e fixo) e as chaves entram no longo_override. pedido["ab"] registra.
    try:
        fat = json.loads((BIN.parent / "config" / "longo.json").read_text(encoding="utf-8")).get("ab_fatores") or {}
        import hashlib
        ab, ovr = {}, dict(pedido.get("longo_override") or {})
        for nome, f in fat.items():
            if nome.startswith("_") or not isinstance(f, dict):
                continue
            # 30/10 (dona: "não precisa ser só A/B, pode ter C, D, E, F"): quantas variantes o fator tiver (A, B, C...)
            vs = sorted(k for k in f if not k.startswith("_"))
            if not vs:
                continue
            v = vs[int(hashlib.md5(f"{pid}|{nome}".encode()).hexdigest(), 16) % len(vs)]
            ab[nome] = v
            ovr.update(f.get(v) or {})
        if ab:
            pedido["ab"], pedido["longo_override"] = ab, ovr
    except (OSError, ValueError) as e:
        print(f"ab_fatores ilegível ({e}) — pedido sem variantes", flush=True)
    voz, base_voz = _voz_do_longo(pedido.get("tipo"))  # voz clonada dos Cortes (voz + base), no Kaggle com GPU
    teste, vozes_rev = _teste_narradores()
    if teste:  # 26/10: longo com revezamento de narradores (teste_narradores.json, contínuo)
        voz, base_voz = VOZES / vozes_rev[0], teste.get("base") or "misto"
        pedido["vozes_lista"] = vozes_rev  # já estão no Drive (subir_vozes.py): nada sobe aqui
        pedido["teste_narradores"] = f"vídeo {len(teste.get('videos', [])) + 1} do revezamento"
        pedido["narradores_modo"] = teste.get("_modo")  # 30/10: solo/dupla/so_primarios/.../mistura_grande
    # 12/11: longo em OUTRA LÍNGUA nunca abre com a fala real do narrador (é em português). LONGO_IDIOMA_SEM_INTRO=0 volta.
    sem_intro = pedido.get("idioma") and os.environ.get("LONGO_IDIOMA_SEM_INTRO", "1") != "0"
    intro = None if sem_intro else _intro_do_longo(vozes_rev if teste else [voz.name] if voz else [])
    if intro:  # 01/11 dona: abre com a fala REAL do narrador (cortada dos vídeos dele) e ele mesmo narra o resumo
        if teste:
            vozes_rev = [intro["voz"]] + [v for v in vozes_rev if v != intro["voz"]]
            pedido["vozes_lista"] = vozes_rev
        voz = VOZES / intro["voz"]
        shutil.copy2(intro["wav"], work / "intro_voz.wav")
        (work / "intro_voz.json").write_text(json.dumps({k: intro[k] for k in ("id", "voz", "texto", "palavras")},
                                                        ensure_ascii=False), encoding="utf-8")
        arquivos += [work / "intro_voz.wav", work / "intro_voz.json"]
        pedido["intro_voz"] = intro["id"]
        print(f"abertura com voz real: {intro['id']} ({intro['voz']} narra o resumo)", flush=True)
    if voz:
        pedido["voz_clonada_base"] = base_voz
        pedido["voz_clonada"] = voz.name
        if not teste:
            _voz_pro_cache(ssh, voz)
    for arq in arquivos:  # source.mp4 grande: scp direto (sobe uma vez só, igual antes pro Drive)
        nome = "source.mp4" if arq == Path(video) else arq.name
        subprocess.run([SCP, "-q", "-o", "BatchMode=yes", str(arq), f"{VPS}:{remoto}/{nome}"], check=True,
                       capture_output=True, timeout=7200)
    tmp = work / "_pedido_colab.json"
    tmp.write_text(json.dumps(pedido, ensure_ascii=False), encoding="utf-8")
    subprocess.run([SCP, "-q", "-o", "BatchMode=yes", str(tmp), f"{VPS}:{remoto}/pedido.json"], check=True,
                   capture_output=True, timeout=300)
    tmp.unlink()
    subprocess.run(ssh + [f"touch {remoto}/enviado.ok"], check=True, capture_output=True, timeout=120)
    if teste:  # só depois de chegar inteiro: falhou no meio = o próximo pedido usa as mesmas vozes
        teste["cursor"] = int(teste.get("cursor", 0)) + len(vozes_rev)
        teste.setdefault("videos", []).append({"pid": pid, "vozes": vozes_rev})
        TESTE_NARRADORES.write_text(json.dumps(teste, ensure_ascii=False, indent=1), encoding="utf-8")
    return pid


def _enviar_direto_antigo(work, video, roteiro, titulo, extra=None):
    """Envio de antes (PC direto pra fila do Drive). Fica só como reserva manual."""
    gravar_token()
    work = Path(work)
    pid = f"{datetime.now():%Y%m%d_%H%M%S}_{work.name[:11]}"
    destino = f"{FILA}/{pid}"
    # o Drive da 649 tem ~3 GB: o original (grande) fica no manhwa-drive; na fila só os arquivos pequenos.
    # Original guardado de uma tentativa que falhou (manhwa-drive:...): move dentro do Drive, sem baixar do YouTube.
    _rc("moveto" if str(video).startswith("manhwa-drive:") else "copyto", str(video), f"{FILA_SRC}/{pid}/source.mp4")
    if Path(roteiro).exists():  # sem roteiro (sem legenda do YouTube): o trabalhador transcreve e roteiriza (25/10)
        _rc("copyto", str(roteiro), f"{destino}/roteiro.txt")
    for js in work.glob("*.json"):
        if js.stat().st_size < 5_000_000 and js.name != "_pedido_colab.json":
            _rc("copyto", str(js), f"{destino}/{js.name}")
    tmp = work / "_pedido_colab.json"
    tmp.write_text(json.dumps({"titulo": titulo, "enviado": datetime.now().isoformat(timespec="seconds"),
                               **(extra or {})}, ensure_ascii=False), encoding="utf-8")
    _rc("copyto", str(tmp), f"{destino}/pedido.json")  # por último: a Colab só pega quando o pedido existe
    tmp.unlink()
    return pid


def baixar_final(pid, destino_mp4):
    """Kaggle/VPS deixam o vídeo no manhwa-drive (FILA_SRC); a Colab, no Drive da 649 (FILA)."""
    for lugar in (FILA_SRC, FILA):
        try:
            _rc("copyto", f"{lugar}/{pid}/final_anime_deitado.mp4", str(destino_mp4))
            if Path(destino_mp4).exists():
                return
        except RuntimeError:
            continue
    raise RuntimeError(f"vídeo pronto de {pid} não achado")


def guardar_cortes(pid, nome):
    """29/10: os melhores trechos do longo (bin/melhores_cortes.py → fila_src/<pid>/cortes_longo) vão pra pasta do longo
    no Drive (ao lado do video.mp4) ANTES do limpar() apagar a fila. postar_longos os posta no canal do longo."""
    anime_auto = _projeto()
    try:
        if "cortes.json" in _rc("lsf", f"{FILA_SRC}/{pid}/cortes_longo", saida=True):
            _rc("copy", f"{FILA_SRC}/{pid}/cortes_longo", f"{anime_auto.DRIVE_ANIME}/{nome}/cortes_longo")
            print(f"cortes do longo guardados: {anime_auto.DRIVE_ANIME}/{nome}/cortes_longo", flush=True)
    except RuntimeError as e:
        print(f"cortes do longo não guardados ({e})", flush=True)


def limpar(pid):
    for lugar in (FILA, FILA_SRC):
        try:
            _rc("purge", f"{lugar}/{pid}")
        except RuntimeError:
            pass


def esperar(pid, destino_mp4, horas=6):
    pasta = f"{FILA}/{pid}"
    fim = time.time() + horas * 3600
    while time.time() < fim:
        if _ler_json(f"{pasta}/pronto.json"):
            baixar_final(pid, destino_mp4)
            try:
                _rc("copyto", f"{pasta}/pipeline.log", str(Path(destino_mp4).with_name("pipeline_colab.log")))
            except RuntimeError:
                pass
            limpar(pid)
            return True
        erro = _ler_json(f"{pasta}/erro.json")
        if erro:
            Path(destino_mp4).with_name("erro_colab.json").write_text(json.dumps(erro, ensure_ascii=False, indent=1),
                                                                      encoding="utf-8")
            limpar(pid)
            return False
        time.sleep(60)
    return False


def teste(work, url, titulo):
    sys.path.insert(0, str(BIN))
    import anime_fetch
    import anime_probe
    import anime_script
    work = Path(work)
    video = work / "source.mp4"
    txt, lang = anime_fetch.fetch_captions(url, work)
    if not txt:
        txt, lang = anime_fetch.transcribe_whisper(video)
    if not txt:
        raise SystemExit("sem transcrição")
    dur = anime_probe.video_duration(str(video))
    alvo = max(40, min(600, max(120, int(dur * 0.55 / 3.0))))
    roteiro = work / "roteiro.txt"
    n = anime_script.rewrite_to_file(txt, roteiro, target_lines=alvo)
    print(f"roteiro: {n} frases (alvo {alvo}, original {dur:.0f} s)", flush=True)
    if not n:
        raise SystemExit("roteiro falhou")
    pid = enviar(work, video, roteiro, titulo)
    print("enviado:", pid, flush=True)
    ok = esperar(pid, work / "final_anime_deitado.mp4")
    print("PRONTO" if ok else "FALHOU", work / ("final_anime_deitado.mp4" if ok else "erro_colab.json"), flush=True)


def _projeto():
    sys.path.insert(0, str(BIN))
    import anime_auto
    return anime_auto


def _cortar_intro(work, video, url):
    """Dona 29/10 ("não esquece de cortar a introdução dele pra deixar só o vídeo mesmo"): acha onde termina a
    apresentação do canal do parceiro (saudação, inscreva-se, 'hoje vamos ver...') e começa a história, e corta o
    original ali — o nosso resumo de abertura entra no lugar. Desloca a legenda com tempo pro roteiro bater. Feito 1x
    (intro_cortada.json). Falhou/sem intro = original inteiro."""
    marca = work / "intro_cortada.json"
    if marca.exists():
        return
    import anime_fetch
    cues = []
    anime_fetch.fetch_captions(url, work, langs=("pt",))
    cues_arq = work / "legenda_tempos.json"
    if cues_arq.exists():
        cues = json.loads(cues_arq.read_text(encoding="utf-8"))
    if not cues:
        try:
            os.environ.setdefault("HF_HOME", r"D:\hipercool-materiais\modelos\hf")
            from faster_whisper import WhisperModel
            # 29/10: transcrever o vídeo direto carregava o áudio INTEIRO (2h07) na memória e dava MemoryError;
            # só os 4 primeiros minutos num wav pequeno
            wav = work / "_intro_4min.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", "240", "-i", str(video), "-vn", "-ac", "1", "-ar",
                            "16000", str(wav)], check=True, capture_output=True, timeout=300)
            segs, _ = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4).transcribe(
                str(wav), language="pt", vad_filter=True)
            cues = [[round(s.start, 1), s.text.strip()] for s in segs]
            wav.unlink(missing_ok=True)
        except Exception as e:  # noqa: BLE001
            print(f"intro: sem transcrição do começo ({type(e).__name__}) — original inteiro", flush=True)
            return
    inicio = "\n".join(f"{s:.0f}s {t}" for s, t in cues if s < 240)
    if not inicio:
        return
    import claude_client
    pergunta = ("Começo de um vídeo de recap narrado de outro canal (segundo + fala). Em que SEGUNDO termina a introdução "
                "do canal (saudação, pedido de inscrição/like/comentário, apresentação do canal, propaganda) e começa a "
                "HISTÓRIA de fato? Se começa direto na história, responda 0. Responda SÓ o número.\n\n" + inicio[:6000])
    resp = ""
    # 29/10: a gemini-fila deu tempo esgotado e a resposta vazia virou "nada a cortar" — o longo ia com a intro
    # 29/10 23h: a G1_iPga6nLg morreu aqui com a OmniRoute fora uns minutos (logo depois os 3 respondiam em 1-4 s) —
    # 4 rodadas da cadeia com 3 min entre elas antes de desistir
    for rodada in range(4):
        if rodada:
            time.sleep(180)
        for modelo in ("gemini-fila", "antigravity/gemini-3-flash", "antigravity/gemini-3.8-flash-tiered"):
            # 30/10 (Fable): max_tokens 20 -> 600 — modelo que "pensa" antes de responder volta vazio com teto curto
            # (lição do hipercool 28/10: "Argon + pedido curto = lixo"); a resposta continua lida pelo 1º número
            resp = claude_client.generate_text(pergunta, max_tokens=600, temperature=0, timeout=120, model=modelo) or ""
            if re.search(r"\d", resp):
                break
        if re.search(r"\d", resp):
            break
    if not re.search(r"\d", resp):
        # 30/10 (ronda da noite): G1_iPga6nLg falhou 3x aqui com a OmniRoute no ar — o começo fala de "dar prazer a
        # elas" e o filtro de segurança do Gemini devolve vazio. Reserva sem IA: o fim da intro é a frase de chamada
        # do canal ("deixe um like… bora pra história") — corta no começo da fala seguinte. Nem isso = vai inteiro.
        chamada = re.compile(r"\b(like|inscrev\w*|comente|coment[aá]rio|sininho|bora pra hist[oó]ria|sem mais "
                             r"enrola\w*|vamos (l[aá]|come[cç]ar)|antes de come[cç]ar)\b", re.I)
        marcas = [i for i, (s, t) in enumerate(cues) if s < 240 and chamada.search(t)]
        resp = str(cues[marcas[-1] + 1][0]) if marcas and marcas[-1] + 1 < len(cues) else "0"
        print(f"intro: IA sem resposta — pela frase de chamada do canal: {resp} s", flush=True)
    m = re.search(r"\d+(\.\d+)?", resp)
    corte = float(m.group(0)) if m else 0.0
    if not 3 <= corte <= 240:
        marca.write_text(json.dumps({"corte_s": 0, "resposta": resp[:80]}), encoding="utf-8")
        print(f"intro: nada a cortar ({resp.strip()[:30]!r})", flush=True)
        return
    tmp = work / "source_sem_intro.mp4"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{corte:.2f}", "-i", str(video), "-c", "copy",
                        "-avoid_negative_ts", "make_zero", str(tmp)], capture_output=True)
    if r.returncode != 0 or not tmp.exists():
        print("intro: corte falhou — original inteiro", flush=True)
        return
    tmp.replace(video)
    if cues_arq.exists():
        cues_arq.write_text(json.dumps([[round(s - corte, 2), t] for s, t in cues if s >= corte], ensure_ascii=False),
                            encoding="utf-8")
    marca.write_text(json.dumps({"corte_s": corte, "fala_cortada": inicio[:1500]}, ensure_ascii=False), encoding="utf-8")
    print(f"intro do parceiro cortada: primeiros {corte:.0f} s", flush=True)


def preparar(url, info=None):
    """Baixa, legenda e faz o roteiro LONGO (~99% da duração, igual ao worker do PC2). -> dict do pedido."""
    anime_auto = _projeto()
    import anime_fetch
    import anime_probe
    import anime_script
    import yt_dlp
    import ytdlp_vez
    if not info:
        with ytdlp_vez.vez("info"):
            info = yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}).extract_info(url, download=False)
    vid, titulo = info["id"], info["title"]
    nome = f"{vid}_{anime_auto._slug(titulo)}"
    work = anime_auto.BASE / nome
    work.mkdir(parents=True, exist_ok=True)
    # 30/10: o Pastor (LAeiXj2Qmlg, recap de manhwa em PT sem "manhwa" no título) saiu ESPELHADO, com o texto dos
    # painéis invertido. O tipo também sai da descrição/tags/canal da fonte; o enviar() põe no pedido.json.
    meta = " ".join([titulo, info.get("description") or "", " ".join(info.get("tags") or []),
                     info.get("channel") or "", info.get("uploader") or ""]).lower()
    if re.search(r"manhwa|manhua|webtoon", meta):
        (work / "tipo_fonte.txt").write_text("manhwa", encoding="utf-8")
    video = next(iter(work.glob("source.mp4")), None)
    # 25/10: um original quebrado (download interrompido) foi pra fila e o Kaggle narrou 2 h sem conseguir cortar nada.
    # Só sobe original que o ffprobe lê inteiro; quebrado = apaga e baixa de novo. 29/10: menos a intro já cortada.
    try:
        cortado = float(json.loads((work / "intro_cortada.json").read_text(encoding="utf-8")).get("corte_s") or 0)
    except (OSError, ValueError):
        cortado = 0.0
    if video and anime_probe.video_duration(str(video)) < max(30, 0.9 * (info.get("duration") or 0) - cortado):
        print(f"original quebrado ou incompleto ({video.stat().st_size // 2**20} MB) — baixando de novo", flush=True)
        video.unlink()
        video = None
    video = video or anime_fetch.download_video(url, work)
    if not video:
        raise RuntimeError("download falhou")
    if anime_probe.video_duration(str(video)) < max(30, 0.9 * (info.get("duration") or 0)):
        Path(video).unlink(missing_ok=True)
        raise RuntimeError("original baixado não abre inteiro (ffprobe) — não vai pra fila")
    roteiro = work / "roteiro.txt"
    if not roteiro.exists():
        _cortar_intro(work, video, url)
    if not roteiro.exists():
        dur = anime_probe.video_duration(str(video))
        txt, _ = anime_fetch.fetch_captions(url, work)
        if not txt:
            # 25/10: sem legenda do YouTube, quem transcreve é o TRABALHADOR (Whisper do vídeo inteiro + roteiro com tempo,
            # bin/anime_preparo_longo.py, chamado pelo anime-pipeline). Aqui era o Whisper do PC1: parava nos 25 min (o
            # 76SY de 2h18 virou roteiro só do começo) e, com o PC1 a 100%, 6 min de áudio passavam de 10 min.
            print("sem legenda do YouTube — transcrição e roteiro vão ser feitos no trabalhador", flush=True)
            return {"vid": vid, "titulo": titulo, "nome": nome, "url": url, "work": work, "video": video,
                    "roteiro": roteiro}
        alvo = max(40, round(dur * 0.99 / 6.6))  # anime_worker_daemon: ~6,6 s de narração por frase
        frases, tempos = [], []
        cues_arq = work / "legenda_tempos.json"
        if cues_arq.exists():  # dona 25/10: o longo também narra o que está na tela (igual ao Short dos Cortes)
            try:
                frases, tempos = anime_script.rewrite_longo_com_tempo(
                    json.loads(cues_arq.read_text(encoding="utf-8")), alvo, dur)
            except Exception as e:  # noqa: BLE001
                print(f"roteiro com tempo falhou ({type(e).__name__}: {e}) — roteiro normal", flush=True)
                frases, tempos = [], []
        if frases:
            roteiro.write_text("\n".join(frases) + "\n", encoding="utf-8")
            (work / "roteiro_tempos.json").write_text(json.dumps(tempos), encoding="utf-8")
            n = len(frases)
        else:
            n = anime_script.rewrite_to_file(txt, roteiro, target_lines=alvo)
        print(f"roteiro: {n} frases {'com tempo' if frases else 'sem tempo'} (alvo {alvo}, original {dur / 60:.0f} min)",
              flush=True)
        if not n:
            raise RuntimeError("roteiro falhou")
    return {"vid": vid, "titulo": titulo, "nome": nome, "url": url, "work": work, "video": video, "roteiro": roteiro}


def publicar_drive(p, final, feito_por):
    """Vídeo pronto -> Drive no formato do modo ocioso (nuvem.json) e sai do disco. `final` local (Colab) ou remoto
    no manhwa-drive (Kaggle/VPS: move dentro do Drive, sem passar pela internet de casa)."""
    anime_auto = _projeto()
    destino = f"{anime_auto.DRIVE_ANIME}/{p['nome']}/video.mp4"
    _rc("moveto" if str(final).startswith("manhwa-drive:") else "copyto", str(final), destino)
    if "video.mp4" not in _rc("lsl", destino, saida=True):
        raise RuntimeError("subida pro Drive não conferiu — vídeo fica no disco: " + str(final))
    ficha = anime_auto.ANIMES_FICHAS / p["nome"]
    ficha.mkdir(parents=True, exist_ok=True)
    if Path(p["roteiro"]).exists():
        shutil.copy2(p["roteiro"], ficha / "roteiro.txt")
    if (Path(p["work"]) / "resumo_fim.json").exists():  # 12/11: compilado da série
        shutil.copy2(Path(p["work"]) / "resumo_fim.json", ficha / "resumo_fim.json")
    if (Path(p["work"]) / "capitulos.json").exists():  # 25/10: o anime_publish põe os capítulos na descrição
        shutil.copy2(Path(p["work"]) / "capitulos.json", ficha / "capitulos.json")
    (ficha / "nuvem.json").write_text(json.dumps(
        {"drive": destino, "titulo_original": p["titulo"], "source_url": p["url"], "formato": "deitado",
         "anime": anime_auto._extrair_nome_anime(p["titulo"]), "feito_em": time.strftime("%Y-%m-%d %H:%M"),
         "feito_por": feito_por, "postar": "baixar do Drive, rodar anime_publish e postar",
         # 12/11: longo traduzido (longo_idiomas.py) -> o postar_longos manda SÓ pro canal da língua
         **({"idioma": p["idioma"].get("codigo"), "canal": p.get("canal")} if isinstance(p.get("idioma"), dict) else {}),
         # 12/11 dona ("procure obras parecidas e põe lá pra replicar o resultado"): parecido com um campeão
         # (garimpar_parecidos.py) só sai no canal onde o campeão deu certo. CANAL_DESTINO_PARECIDO=0 desliga.
         **({"canal": p["canal_destino"], "tema": p.get("tema")}
            if p.get("canal_destino") and os.environ.get("CANAL_DESTINO_PARECIDO", "1") != "0" else {})},
        ensure_ascii=False, indent=2), encoding="utf-8")
    anime_auto._marca_feito(p["vid"], "deitado")
    shutil.rmtree(p["work"], ignore_errors=True)
    print("NO DRIVE:", destino, flush=True)


def produzir(url):
    p = preparar(url)
    pid = enviar(p["work"], p["video"], p["roteiro"], p["titulo"])
    print("enviado:", pid, flush=True)
    final = p["work"] / "final_anime_deitado.mp4"
    if not esperar(pid, final, horas=14):
        raise SystemExit(f"render falhou: {p['work'] / 'erro_colab.json'}")
    publicar_drive(p, final, "fila")


def _tipo_do_canal(canal):
    """manhwa/anime do canal-fonte (config/longo.json "canais"): o pipeline tira o espelho do manhwa (dona 25/10)."""
    try:
        cfg = json.loads((BIN.parent / "config" / "longo.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    c = (canal or "").lower()
    return next((t for chave, t in (cfg.get("canais") or {}).items() if chave.lower() in c), None)


ALIMENTAR_LOG = Path(__file__).with_name("alimentar_estado.json")
# 10/11: 210 min (07/11) estava ERRADO — a nota dizia "roteiro ~1050 frases qualquer duração", mas o roteiro tem 1 frase
# a cada 6,6 s do original (alvo = dur/6,6): HZRT de 206 min virou 1952 frases ≈ 13 h a 24 s/frase > 11,5 h da sessão
# Kaggle — refeito 3x desde 08/11 sem nunca terminar. 170 min ≈ 1550 frases ≈ 10,3 h: cabe. LONGO_MAX_MIN muda.
MAX_DUR_S = float(os.environ.get("LONGO_MAX_MIN", "170")) * 60


def _pedidos():
    """{pid: {arquivos}} da fila. 27/10: 1 lsf -R só (antes 1 por pedido; com a cota do Drive estourada cada chamada
    levava até 10 min e uma volta do alimentar passava de 2 h)."""
    out = {}
    for linha in _rc("lsf", FILA, "-R", saida=True).split("\n"):
        linha = linha.strip()
        if not linha:
            continue
        pid, _, arq = linha.partition("/")
        out.setdefault(pid, set())
        if arq and not arq.endswith("/"):
            out[pid].add(arq)
    return out


_PEDIDO_CACHE = {}


def _pedido_json(pid):
    """pedido.json não muda depois de enviado: lê 1 vez só (27/10, cota do Drive)."""
    if pid not in _PEDIDO_CACHE:
        d = _ler_json(f"{FILA}/{pid}/pedido.json")
        if d is None:
            return None
        _PEDIDO_CACHE[pid] = d
    return _PEDIDO_CACHE[pid]


PASTA_VER = Path(r"D:\hipercool-materiais\recap-longos-prontos")


def _o_que_testar(pedido, marcas, alvo):
    """01/11 dona ("faço muitos pedidos, quando o teste chega eu já não lembro o que pedi"): junto de cada prévia, a
    lista do que ela pediu que está NESTA prévia + o minuto exato onde cada novidade aparece. Vira um .txt do lado do
    vídeo e vai no Telegram."""
    def mmss(t):
        return f"{int(t // 60)}:{int(t % 60):02d}"
    linhas = ["O QUE TESTAR NESTA PRÉVIA", ""]
    for i, p in enumerate(pedido.get("o_que_testar") or [], 1):
        linhas.append(f"{i}. {p}")
    if marcas:
        linhas += ["", "ONDE APARECE (minuto no vídeo):"]
        ult = {}
        # 02/11: a PREVIA5 saiu com a lista só até 0:24 — o pronto.json leva só as 1ªs marcas; e a legenda criativa
        # (centenas) enchia. Agora em ordem de tempo, legenda criativa/efeito repetido no máx. 1 a cada 20 s por tipo
        nomes = {"fx_troca": "FLASH BRANCO na troca de cena", "fx_revela": "NEGATIVO (revelação)",
                 "fx_micro": "zoom leve (palavra forte)", "fx_impacto": "COMBO de impacto (golpe)",
                 "fx_tensao": "BARRAS DE CINEMA (tensão)", "fx_poder": "DESPERTAR: brilho + zoom que dispara",
                 "fx_brasa": "BRASAS subindo", "fx_sistema": "GLITCH (janela de sistema)",
                 "fx_memoria": "FANTASMA da cena (lembrança)"}
        for t, tipo, rot in sorted(marcas, key=lambda m: float(m[0])):
            if (tipo.startswith(("legenda_criativa", "fx_")) or tipo == "legenda_mix_modo") \
                    and float(t) - ult.get(tipo, -99) < 20:
                continue
            ult[tipo] = float(t)
            linhas.append(f"{mmss(float(t))}  {nomes.get(tipo) or tipo.replace('_', ' ') + ': ' + str(rot)}")
    txt = "\n".join(linhas)
    try:
        if alvo:
            Path(str(alvo)).with_name(Path(str(alvo)).stem + "_O_QUE_TESTAR.txt").write_text(txt, encoding="utf-8")
    except OSError:
        pass
    return txt


def _abrir_na_pasta(final_drive, nome):
    """Cópia do vídeo pra pasta de acompanhamento + abre o Explorer nela (dona 26/10: "abra a pasta com o aviso")."""
    try:
        PASTA_VER.mkdir(parents=True, exist_ok=True)
        alvo = PASTA_VER / f"{datetime.now():%Y-%m-%d_%Hh%M}_{nome[:60]}.mp4"
        # 04/11 dona: "só manter sempre a última" — 4 cópias de teste de narradores (5–9 GB cada, 26 GB) se acumularam
        # aqui. O vídeo mora no Drive; no PC fica só a cópia mais nova de cada tipo (TESTE_NARRADORES, PREVIA...).
        tipo = nome.split("_")[0] + "_"
        for velho in PASTA_VER.glob(f"*_{tipo}*.mp4"):
            try:
                velho.unlink()
            except OSError:
                pass  # aberto no player: fica pra próxima
        # 06/11 (dona viajando; disco a 5,9 GB): a cópia de 3 GB de um TESTE de narradores segurou a postagem de um
        # longo ("sem espaço"). Só baixa a cópia de conferência com folga de 12 GB depois dela; senão fica só no Drive.
        try:
            tam = sum(x.get("Size", 0) for x in json.loads(_rc("lsjson", final_drive, saida=True) or "[]"))
        except (RuntimeError, ValueError):
            tam = 6e9
        if shutil.disk_usage(str(PASTA_VER)).free - tam < 12e9:
            print(f"cópia de conferência {nome[:40]} pulada: disco sem folga (o vídeo está no Drive: {final_drive})",
                  flush=True)
            return None
        _rc("copyto", final_drive, str(alvo))
        subprocess.Popen(["explorer", "/select,", str(alvo)])
        return alvo
    except Exception as e:  # noqa: BLE001
        print(f"abrir na pasta falhou: {e}", flush=True)
        return None


def _avisar_teste(pid, pedido, ficha, arqs, final_drive):
    """Longo de TESTE de narradores pronto: não vai pra canal (marca na ficha), abre a pasta e avisa no Telegram."""
    (ficha / "TESTE_NARRADORES.txt").write_text(f"{pedido.get('teste_narradores')}: "
                                                f"{', '.join(pedido.get('vozes_lista') or [])}\n", encoding="utf-8")
    alvo = _abrir_na_pasta(final_drive, f"TESTE_NARRADORES_{pedido.get('nome', pid)}")
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        r = _ler_json(f"{FILA}/{pid}/pronto.json") or {}
        avisos.enviar(f"🎙️ Teste de narradores pronto ({pedido.get('teste_narradores')}): "
                      f"{len(pedido.get('vozes_lista') or [])} vozes se revezando (legenda sem nome de narrador).\n"
                      f"Revezamento no Kaggle: {'sim' if r.get('vozes_lista') else 'NÃO (saiu com 1 voz só)'}\n"
                      f"Abri a pasta no PC: {alvo or PASTA_VER}", "recap-longo", importante=True)
    except Exception as e:  # noqa: BLE001
        print(f"aviso do teste falhou: {e}", flush=True)


def _avisar_narracao_nova(est, pid, pedido, ficha, arqs):
    """Dona 26/10: "assim que tiver um vídeo com a nova narração, me mande" — 1º longo feito com a voz dos Cortes
    COMPLETA (base do rodízio, Kokoro funcionando no Kaggle): Telegram (importante) com o título e 40 s de amostra."""
    if est.get("avisou_narracao_nova"):
        return False
    r = _ler_json(f"{FILA}/{pid}/pronto.json") or {}
    if not (r.get("voz_clonada") and r.get("applio_ok") and r.get("kokoro_nuvem")):
        return False
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        texto = (f"🎙️ Recap longo com a NARRAÇÃO NOVA pronto: {pedido.get('titulo', '')[:90]}\n"
                 f"Voz {r['voz_clonada']} · base {r.get('voz_base')} (igual aos Cortes, com Kokoro).\n"
                 f"Vídeo inteiro em D:\\hipercool-materiais\\recap-longos-prontos (último feito).")
        if "amostra.mp3" in arqs:
            _rc("copyto", f"{FILA}/{pid}/amostra.mp3", str(ficha / "amostra.mp3"))
            if avisos.enviar_arquivo(str(ficha / "amostra.mp3"), texto, "recap-longo") is None:
                avisos.enviar(texto, "recap-longo", importante=True)
        else:
            avisos.enviar(texto, "recap-longo", importante=True)
        est["avisou_narracao_nova"] = pid
        return True
    except Exception as e:  # noqa: BLE001 — aviso nunca derruba o alimentador
        print(f"aviso da narração nova falhou: {e}", flush=True)
    return False


def alimentar(canal, folga=6):  # 07/11: com 10 contas de longo, folga 2 deixava 8 sem pedido (saíam ociosas)
    """Loop: recolhe prontos (-> Drive) e mantém (trabalhadores vivos + folga) pedidos esperando na fila, com os
    vídeos do canal do mais visto pro menos. Pedidos sem 'nome' no pedido.json são de outro processo (produzir)."""
    import yt_dlp
    anime_auto = _projeto()
    import ytdlp_vez
    est = json.loads(ALIMENTAR_LOG.read_text(encoding="utf-8-sig")) if ALIMENTAR_LOG.exists() else {"falhas": {}}
    # batida logo ao começar: o vigia mede o travamento pela data deste arquivo (sem isto ele matava o recém-religado)
    ALIMENTAR_LOG.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    # 03/11: o YouTube barrou a lista ("Sign in to confirm you're not a bot") e o alimentar morria AQUI, antes de
    # recolher — 4 animes prontos (q5Sv, asv0, yqCT, g-JG) ficaram parados no Drive o dia todo. Lista falhou ou yt-dlp
    # pausado = segue só recolhendo (lista vazia, não pede vídeo novo).
    lista = []
    if not ytdlp_vez.pausado():
        try:
            with ytdlp_vez.vez("lista do canal"):
                try:
                    lista = yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}).extract_info(
                        canal, download=False)["entries"] or []
                except Exception as e_px:  # noqa: BLE001
                    # 09/11: o Webshare grátis da vez respondia "402 Payment Required" (banda acabou) e a volta
                    # inteira ficava sem lista — alimentador sem pedido desde 08/11 23:34. Proxy falhou = tira ele
                    # da roda e lista DIRETO (consulta pequena, 1 por volta, como era antes de 22/10).
                    if "proxy" not in str(e_px).lower():
                        raise
                    ytdlp_vez.proxy_ruim(os.environ.get("https_proxy"), str(e_px))
                    lista = yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True, "proxy": ""}).extract_info(
                        canal, download=False)["entries"] or []
        except Exception as e:  # noqa: BLE001
            print(f"lista do canal falhou ({str(e)[:120]}) — esta volta só recolhe os prontos", flush=True)
    else:
        print("yt-dlp pausado — esta volta só recolhe os prontos", flush=True)
    lista = [e for e in lista if e.get("id")]
    # 29/10 dona: "evite fazer esses escolares de briga; de preferência os de apocalipse, medievais etc." — título de
    # escola sai; apocalipse/medieval/dungeon... vêm antes (dentro de cada grupo, do mais visto pro menos)
    escola = re.compile(r"\b(school|academy|class(mate|room)?s?|bull(y|ies|ied)|student|teacher|high ?school|"
                        r"escola|academia|colegial|valent)", re.I)
    prefere = re.compile(r"\b(apocalyp\w*|zombie|medieval|kingdom|knight|dungeon|tower|dragon|demon|monster|war|"
                         r"emperor|king|sword|murim|martial|cultivat\w*|survival|system|regress\w*|reincarnat\w*|"
                         r"apocalipse|reino|cavaleiro|masmorra|dragão|demônio|guerra|imperador)", re.I)
    # 12/11 dona ("por que bloquear o tema se deu muito bom? não seria usar mais ele?"): escola com original de
    # ESCOLA_MIN_VIEWS (1 mi) ou mais NÃO sai mais; só o escolar fraco fica de fora. ESCOLA_MIN_VIEWS=0 barra todos.
    _esc_min = int(os.environ.get("ESCOLA_MIN_VIEWS", "1000000"))
    fora = [e for e in lista if escola.search(e.get("title") or "")
            and not (_esc_min and (e.get("view_count") or 0) >= _esc_min)]
    # 09/11 dona: "vamos dar prioridade a esses vídeos que dão mais visualizações, independente do canal" — ordem só
    # pelas views do original (o tema preferido só desempata). ORDEM_POR_TEMA=1 volta a ordem antiga (tema primeiro).
    if os.environ.get("ORDEM_POR_TEMA", "0") == "1":
        lista = sorted((e for e in lista if e not in fora),
                       key=lambda e: (not prefere.search(e.get("title") or ""), -(e.get("view_count") or 0)))
    else:
        lista = sorted((e for e in lista if e not in fora),
                       key=lambda e: (-(e.get("view_count") or 0), not prefere.search(e.get("title") or "")))
    print(f"canal: {len(lista)} vídeos ({len(fora)} de escola fora)", flush=True)
    while True:
        os.utime(ALIMENTAR_LOG)  # batida no começo de cada volta também (vigia mede pela data)
        feitos = anime_auto._ja_feitos("deitado")
        ped = _pedidos()
        # 1) recolher
        for pid, arqs in ped.items():
            if "pronto.json" not in arqs and "erro.json" not in arqs:
                continue
            if "pedido.json" not in arqs:
                # 25/10: 2 trabalhadores no mesmo pedido — o 2º terminou depois da pasta ser recolhida e recriou ela só
                # com pronto/erro (vídeo repetido sobrando no Drive). Não tem pedido: só limpar.
                print(f"{datetime.now():%H:%M} pasta órfã {pid} ({', '.join(sorted(arqs))}) — limpa", flush=True)
                limpar(pid)
                continue
            pedido = _pedido_json(pid) or {}
            if "nome" not in pedido:
                # 01/11: pedido refeito/da dona (sem "nome") ficava órfão quando o script que esperava por ele morria —
                # 10 longos prontos parados no Drive desde 30/10. Pronto sem dono = o alimentador recolhe também.
                if "pronto.json" not in arqs or not pedido.get("titulo"):
                    continue
                vid = pid.split("_", 2)[-1]
                pedido = {**pedido, "vid": vid, "nome": f"{vid}_{anime_auto._slug(pedido['titulo'])}",
                          "url": f"https://www.youtube.com/watch?v={vid}"}
            if pedido.get("previa") and "pronto.json" in arqs:
                # 01/11 dona (modo melhorias): prévia curta pra conferir as mudanças — NUNCA vira ficha nem é postada
                if "recolhendo_pc.txt" in arqs:  # 02/11: outro script do PC já está baixando esta (não baixa 2x)
                    continue
                remoto = f"{FILA_SRC}/{pid}/final_anime_deitado.mp4"
                try:
                    alvo = _abrir_na_pasta(remoto, f"PREVIA_{pedido.get('nome', pid)}")
                    if not alvo or not Path(str(alvo)).exists():
                        # 02/11: cópia falhou = NÃO limpa (antes apagava a prévia do Drive sem ter baixado)
                        print(f"prévia {pid}: cópia falhou — fica no Drive pra próxima", flush=True)
                        continue
                    sys.path.insert(0, r"D:\video-fila")
                    import avisos
                    r = _ler_json(f"{FILA}/{pid}/pronto.json") or {}
                    testar = _o_que_testar(pedido, r.get("marcas") or  # 03/11: era "lista" (apagava a do canal)
                                           _ler_json(f"{FILA_SRC}/{pid}/cortes_longo/marcas_visuais.json"), alvo)
                    avisos.enviar(f"🧪 PRÉVIA pronta (não vai pra canal): {pedido.get('titulo', '')[:80]}\n"
                                  f"Versão: {(r.get('versao') or {}).get('versao', '?')}\nAbri no PC: {alvo}\n\n"
                                  + testar[:3000], "recap-longo", importante=True)
                except Exception as e:  # noqa: BLE001
                    print(f"prévia {pid}: aviso/cópia falhou ({e})", flush=True)
                limpar(pid)
                continue
            p = {**pedido, "work": anime_auto.BASE / pedido["nome"], "roteiro": anime_auto.BASE / pedido["nome"] / "roteiro.txt"}
            if "pronto.json" in arqs:
                quem = (_ler_json(f"{FILA}/{pid}/pronto.json") or {}).get("por", "colab")
                remoto = f"{FILA_SRC}/{pid}/final_anime_deitado.mp4"
                try:
                    no_backup = "final_anime_deitado.mp4" in _rc("lsf", f"{FILA_SRC}/{pid}", saida=True)
                except RuntimeError:
                    no_backup = False
                if no_backup:
                    final = remoto
                else:
                    final = p["work"] / "final_anime_deitado.mp4"
                    p["work"].mkdir(parents=True, exist_ok=True)
                    try:
                        baixar_final(pid, final)
                    except RuntimeError as e:
                        # 03/11: waaQ já recolhido por outra rotina (ficha na_nuvem existe, vídeo saiu do Drive) e a
                        # pasta ficou na fila — o alimentar morria aqui e q5Sv/asv0/yqCT/g-JG nunca desciam
                        vid = str(pedido.get("vid") or pid.split("_", 2)[-1])
                        nuvem = _projeto().ANIMES_FICHAS.parent / "na_nuvem"
                        if any((d / "nuvem.json").exists() for d in nuvem.glob(f"{vid[:8]}*")):
                            print(f"{pid}: já recolhido antes (ficha na_nuvem) — limpa a fila", flush=True)
                            limpar(pid)
                        else:
                            print(f"{pid}: {e} — fica pra próxima volta", flush=True)
                        continue
                if not Path(p["roteiro"]).exists() and "roteiro.txt" in arqs:  # roteiro feito no trabalhador (25/10)
                    try:
                        p["work"].mkdir(parents=True, exist_ok=True)
                        _rc("copyto", f"{FILA}/{pid}/roteiro.txt", str(p["roteiro"]))
                    except RuntimeError:
                        pass
                if "resumo_fim.json" in arqs:  # 12/11: onde termina o resumo de abertura (compilar_serie.py)
                    try:
                        p["work"].mkdir(parents=True, exist_ok=True)
                        _rc("copyto", f"{FILA}/{pid}/resumo_fim.json", str(p["work"] / "resumo_fim.json"))
                    except RuntimeError:
                        pass
                if "capitulos.json" in arqs:  # capítulos do longo (25/10) vão pra ficha, pra descrição do YouTube
                    try:
                        p["work"].mkdir(parents=True, exist_ok=True)
                        _rc("copyto", f"{FILA}/{pid}/capitulos.json", str(p["work"] / "capitulos.json"))
                    except RuntimeError:
                        pass
                guardar_cortes(pid, pedido["nome"])
                publicar_drive(p, final, f"{quem} (emersonjosiel649)")
                if "qa.json" in arqs:  # 04/11: QA do longo feito no Kaggle (preto/congelado/mudo/volume) vai pra ficha
                    try:
                        _rc("copyto", f"{FILA}/{pid}/qa.json", str(_projeto().ANIMES_FICHAS / pedido["nome"] / "qa.json"))
                    except RuntimeError:
                        pass
                # 26/10: o que o trabalhador registrou (voz clonada, marca do site) + log do render ficam na ficha —
                # antes o limpar() apagava tudo e não dava pra conferir se a voz clonada entrou
                ficha = _projeto().ANIMES_FICHAS / pedido["nome"]
                try:
                    (ficha / "render.json").write_text(json.dumps(_ler_json(f"{FILA}/{pid}/pronto.json") or {},
                                                                  ensure_ascii=False, indent=1), encoding="utf-8")
                    if "pipeline.log" in arqs:
                        _rc("copyto", f"{FILA}/{pid}/pipeline.log", str(ficha / "pipeline.log"))
                except (OSError, RuntimeError):
                    pass
                if pedido.get("teste_narradores"):
                    _avisar_teste(pid, pedido, ficha, arqs, f"{anime_auto.DRIVE_ANIME}/{pedido['nome']}/video.mp4")
                elif _avisar_narracao_nova(est, pid, pedido, ficha, arqs):
                    _abrir_na_pasta(f"{anime_auto.DRIVE_ANIME}/{pedido['nome']}/video.mp4", pedido["nome"])
            else:
                erro = _ler_json(f"{FILA}/{pid}/erro.json") or {}
                est["falhas"][pedido["vid"]] = est["falhas"].get(pedido["vid"], 0) + 1
                print(f"ERRO {pid}: {str(erro.get('log', erro))[-300:]}", flush=True)
                # 26/10: pythonw não tem saída e o limpar() apaga a fila — sem isto o motivo do erro sumia (w0who)
                pasta_erros = Path(__file__).with_name("erros")
                pasta_erros.mkdir(exist_ok=True)
                (pasta_erros / f"{pid}.json").write_text(json.dumps(erro, ensure_ascii=False, indent=1), encoding="utf-8")
                try:
                    if "pipeline.log" in arqs:
                        _rc("copyto", f"{FILA}/{pid}/pipeline.log", str(pasta_erros / f"{pid}.log"))
                except RuntimeError:
                    pass
            limpar(pid)
        # 2) abastecer
        # 27/10: relê os feitos DEPOIS de recolher — antes usava a lista do começo da volta e o pedido recolhido já
        # tinha sido apagado do Drive, então o vídeo que acabou de chegar voltava pra fila (RA4H e PFbu feitos 2x)
        feitos = anime_auto._ja_feitos("deitado")
        ped = {pid: a for pid, a in ped.items() if not a & {"pronto.json", "erro.json"}}
        esperando =sum(1 for a in ped.values() if "pedido.json" in a and not a & {"pronto.json", "erro.json"}
                        and not any(x.startswith("em_andamento") for x in a))
        vivos = 0
        # 08/11: com 22 contas, ler 1 vivo_*.json por vez no Drive (cota da chave pública do rclone = 40-60 s cada)
        # levava a volta inteira e o alimentador quase não mandava pedido. A central já publica as GPUs com conta no
        # status.json (abaixo); os vivo*.json só valem se o status não responder.
        try:
            with urllib.request.urlopen("https://produtos.opus-sem-limites.com.br/recap-5a857ed863/status.json",
                                        timeout=20) as r:
                vivos = sum(1 for g in json.loads(r.read().decode("utf-8")).get("gpus", []) if g.get("conta"))
        except Exception:  # noqa: BLE001
            vivos = 0
        for arq in ([] if vivos else
                    _rc("lsf", "manhwa-drive:colab_recap", "--files-only", "--include", "vivo*.json", saida=True).split()):
            d = _ler_json(f"manhwa-drive:colab_recap/{arq}")
            if d and (datetime.now(timezone.utc) - datetime.fromisoformat(d["em"])).total_seconds() < 1800:
                vivos += 1
        # 26/10: as GPUs do Kaggle podem gravar o mesmo vivo_kaggle.json (nome igual) e contavam como 1 — a fila ficava
        # com 1-2 pedidos e 3 GPUs paradas. Vale o nº de GPUs com conta que a central da VPS publica.
        try:
            with urllib.request.urlopen("https://produtos.opus-sem-limites.com.br/recap-5a857ed863/status.json",
                                        timeout=20) as r:
                vivos = max(vivos, sum(1 for g in json.loads(r.read().decode("utf-8")).get("gpus", []) if g.get("conta")))
        except Exception:  # noqa: BLE001 — sem status da VPS, fica a contagem pelos vivo*.json
            pass
        em_fila = {(_pedido_json(pid) or {}).get("vid") for pid in ped}
        # 26/10: o pedido passa pela entrada da VPS (até 5 min) antes de aparecer na fila; sem isto o mesmo vídeo era
        # reenviado a cada volta (uNNUWNkro0I foi 3x) e virava 3 GPUs no mesmo vídeo. Enviado há < 6 h = já está indo.
        agora_ts = time.time()
        enviados = {v: t for v, t in est.setdefault("enviados", {}).items() if agora_ts - t < 24 * 3600}  # 07/11: 6 h < tempo do longo no Kaggle (2-8 h) + repasse da VPS: reenviava (4JTC 4x, VgQU 3x)
        est["enviados"] = enviados
        a_caminho = set(enviados) - em_fila
        esperando += len(a_caminho)
        em_fila |= a_caminho
        import ytdlp_vez
        if ytdlp_vez.pausado():  # YouTube barrando o IP de casa: nada de yt-dlp (regra: sem rajada)
            pass
        elif esperando < max(1, vivos) + folga - 1:
            # 09/11 dona ("esses que tem que fazer"): config/fontes_prioridade.json vai na FRENTE do canal normal
            # (vídeos de milhões de views dos canais novos). FONTES_PRIORIDADE=0 desliga.
            prio_lista = []
            if os.environ.get("FONTES_PRIORIDADE", "1") != "0":
                try:
                    prio_lista = [dict(v, duration=v.get("min", 0) * 60, prio=True) for v in json.loads(
                        (BIN.parent / "config" / "fontes_prioridade.json").read_text(encoding="utf-8"))["videos"]]
                except (OSError, ValueError, KeyError):
                    prio_lista = []
            for e in prio_lista + lista:
                if (e["id"] in feitos or e["id"] in em_fila or e["id"] in est.get("ignorar", [])
                        or est["falhas"].get(e["id"], 0) >= 2):
                    continue
                # Kaggle/Colab cortam a sessão em 12 h; render ~5x o tempo do vídeo → acima disso fica pra VPS
                # 12/11 dona (parte 13 do Medieval, ~190 min): as partes 11/12 (191 min) já renderizaram dentro das
                # 11,5 h do Kaggle; série que a dona acompanha passa com "forcar_longo" na fontes_prioridade (até 200 min)
                if (e.get("duration") or 0) > MAX_DUR_S and not (e.get("forcar_longo") and e["duration"] <= 200 * 60):
                    if e["id"] not in est.setdefault("longos_demais", []):
                        est["longos_demais"].append(e["id"])
                    continue
                try:
                    p = preparar(f"https://www.youtube.com/watch?v={e['id']}")
                    pid = enviar(p["work"], p["video"], p["roteiro"], p["titulo"],
                                 {**{k: p[k] for k in ("vid", "titulo", "nome", "url")},
                                  "canal": e.get("canal") if e.get("prio") else canal,
                                  **({k: e[k] for k in ("canal_destino", "tema") if e.get(k)} if e.get("prio") else {}),
                                  "tipo": e.get("tipo") if e.get("prio") else _tipo_do_canal(canal)})
                    est["enviados"][e["id"]] = time.time()
                    # grava JÁ: reinício no meio da volta perdia isto e o vídeo saía 2x (w0who 26/10)
                    ALIMENTAR_LOG.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
                    print(f"{datetime.now():%H:%M} enviado {pid} ({esperando + 1} esperando, {vivos} trabalhadores)",
                          flush=True)
                    (p["work"] / "source.mp4").unlink(missing_ok=True)  # já está no Drive da fila
                except Exception as ex:  # noqa: BLE001
                    if ytdlp_vez.bloqueio(str(ex)):  # bloqueio do IP não é culpa do vídeo
                        ytdlp_vez.pausar(f"alimentar recap longo: {ex}")
                        print(f"YouTube barrou o IP ({e['id']}): yt-dlp em pausa", flush=True)
                    else:
                        est["falhas"][e["id"]] = est["falhas"].get(e["id"], 0) + 1
                        print(f"falhou preparar {e['id']}: {ex}", flush=True)
                break
        ALIMENTAR_LOG.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(120)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "teste":
        teste(a[1], a[2], a[3])
    elif a and a[0] == "produzir":
        produzir(a[1])
    elif a and a[0] == "alimentar":  # python cliente.py alimentar https://www.youtube.com/@Manhwa_Fresh/videos
        alimentar(a[1])
    elif a and a[0] == "token_loop":  # mantém o token da Colab válido (vence em 1 h)
        while True:
            try:
                gravar_token()
                print(datetime.now().strftime("%H:%M"), "token renovado", flush=True)
            except Exception as e:  # noqa: BLE001
                print("token falhou:", e, flush=True)
            time.sleep(600)  # o rclone só renova perto de vencer: o token gravado pode ter poucos minutos
    elif a and a[0] == "vivo":
        s = vivo()
        print("nunca" if s is None else f"há {s:.0f} s")
    else:
        print(__doc__)
