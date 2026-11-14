"""postar_longos.py — posta os recaps LONGOS que estão no manhwa-drive (videos-backup/anime/1_youtube_pendente) nos
canais de manhwa em português, pra comparar qual dá resultado (dona 26/10: "todos os longos vão pros canais de manhwa,
ver qual se sai melhor"; "ponha nos outros" = fora o InovareManhwaVerse, que tem advertência de nudez até 14/01/2027).

Por rodada, no máximo 1 longo por canal por dia (CANAIS). Cada longo:
  1. baixa do Drive (+ roteiro e capítulos da ficha) numa pasta temporária do hipercool-materiais;
  2. anime_publish --formato deitado: título SEO sem nome da obra, capa, capítulos na descrição e a REVISÃO de nudez;
  3. revisão "reprovado" = NÃO sobe (fica marcado na ficha); senão aprova e sobe pelo postador (politica.postar_youtube):
     público SEMPRE agendado pelo youtube_web_poster (25 min + duração), projeto "parceiro" = no Manhwa Noturno pega só
     a vaga que SOBRA no dia (o canal é do hipercool), no inovare manhwa br entra como alimentador livre;
  4. anota em longos_postados.json (vídeo, canal, link) pra comparar as views; apaga a cópia local (original no Drive).

    python postar_longos.py            # 1 rodada (tarefa RecapPostarLongos)
    python postar_longos.py --ver      # só mostra o que faria
"""
import json
import os
import re
import shutil
import subprocess
import threading
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
import sys as _sys
if _sys.platform == "win32":  # dona 26/10: rclone/ssh/scp/python filhos SEM janela na tela (PC1 e PC2)
    for _p in (r"D:\hipercool-materiais\comum", r"C:\hipercool-materiais\comum"):
        if Path(_p, "sem_janela.py").exists():
            _sys.path.append(_p)
            import sem_janela  # noqa: F401,E402
            break

AQUI = Path(__file__).resolve().parent
RCLONE = r"D:\tools\rclone.exe"
PY = r"D:\recapd-ambientes\producao\venv\Scripts\python.exe"
PUBLISH = AQUI.parent / "bin" / "anime_publish.py"
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
TMP = Path(r"D:\hipercool-materiais\_longos_postar")
ESTADO = AQUI / "longos_postados.json"
LOG = AQUI / "postar_longos.log"
# 30/10 (dona viu o iIBHQv-ahlY — feito 27/10, postado 30/10 — "por que não tem a mascote nem o resumo no começo?"):
# só sobem longos feitos DEPOIS das correções que ela pediu (resumo, mascote andando, sem roxo/Patrick/jaqueta: o Pastor
# começou 29/10 19:46). Os antigos ficam no Drive. Antes: "2026-10-25 14:00".
DESDE = "2026-10-29 19:00"
CANAIS = [
    # 30/10 dona: "o Forja já está autorizado, poste vídeos longos lá também" — ele nunca recebeu longo: vai primeiro
    ("novo_forjareact", "ForjaReact"),
    # dona 28/10: "liberei vários canais (emersonjosiel2033,32,31,0,29,27,26, gabrielly, maite) pra vídeo longo; posta um
    # em cada dos muitos que fizemos pra ver como se saem" — os que ainda não receberam longo vêm PRIMEIRO
    ("novo_assistiainvestimentos", "Assist-IA Investimentos"), ("novo_codigo_inteligente_n7j", "Fio da Meada"),
    ("novo_universo_ia_d6s", "CenaReact"), ("novo_historias_em_frames", "HistoriasEmFrames"),
    ("novo_curiosidadesnoturnas", "Curiosidades Noturnas"), ("novo_doramanoturno", "Dorama Noturno"),
    # 29/10 dona: a penalidade do InovareManhwaVerse saiu — "pode postar longos e curtos nele"
    ("novo_inovaremanhwaverse", "InovareManhwaVerse"),
    ("novo_manhwanoturno", "Manhwa Noturno"), ("hNQrW5ouNe0Ni5Me", "inovare manhwa br"),
    # 27/10 (dona: "muito conteúdo e pouco canal"): canais pt da rede manhwa-react com o parceiro como
    # alimentador "livre" (canais.json) e nicho/nome de manhwa
    ("novo_manhwareact_ia", "ManhwaReact"),
    # dona 27/10: "um grande por canal, por ordem dos mais associados a manhwa, e ver qual performa melhor"
    ("KOpyXE9rBy1YirlZ", "Animescomia"), ("novo_cartuchoreact", "CartuchoReact"),
    ("novo_ia_agora_h3n", "InventoReact")]
sys.path.append(r"D:\postador-de-videos\bin")


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"postados": [], "reprovados": []}


_TRAVA_DISCO = threading.Lock()  # 07/11: reserva de espaço dos downloads em paralelo
_RESERVADO = {}
_TRAVA_FILA = threading.RLock()  # 04/11: postagem em paralelo — quem pega/devolve longo da fila
_TRAVA_EST = threading.RLock()  # 04/11: 2 envios terminando juntos não podem gravar o estado ao mesmo tempo


def _vivo(fn, *a):
    """Roda 1 canal na thread; erro de um canal vira log e não derruba os outros."""
    try:
        return fn(*a)
    except Exception as e:  # noqa: BLE001
        log(f"{a[1] if len(a) > 1 else '?'}: falhou na postagem em paralelo ({type(e).__name__}: {str(e)[:200]})")
        return None


def _gravar_estado(est):
    """03/11: grava JUNTANDO com o que está no arquivo. Em 02/11 duas rodadas rodaram juntas e a que terminou depois
    gravou a lista que tinha lido de manhã por cima: o post do yKfgs no Fio da Meada sumiu e ele voltou pra fila (quase
    saiu em 3 canais — regra: vídeo único por canal). Postado/reprovado/corte que existir no arquivo nunca se perde."""
    with _TRAVA_EST:
        _gravar_estado_trancado(est)


def _gravar_estado_trancado(est):
    disco = _estado()
    vistos = {(p.get("nome"), p.get("url")) for p in est.get("postados", [])}
    est["postados"] = est.get("postados", []) + [p for p in disco.get("postados", [])
                                                 if (p.get("nome"), p.get("url")) not in vistos]
    est["reprovados"] = sorted(set(est.get("reprovados", [])) | set(disco.get("reprovados", [])))
    # 13/11 20h45 (Medieval 4): bipar_palavrao tirou dos reprovados, mas a rodada que já estava rodando gravou a cópia
    # antiga por cima (a união nunca tira) e a parte 4 voltou a reprovada. Ficha com SEM_PALAVRAO.txt = liberada.
    est["reprovados"] = [n for n in est["reprovados"] if not (FICHAS / n / "SEM_PALAVRAO.txt").exists()]
    est["cortes_postados"] = sorted(set(est.get("cortes_postados", [])) | set(disco.get("cortes_postados", [])))
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


def _modelo_novo(ficha):
    """Dona 26/10 (o XNKC ia pro ar com a Thalita e a tarja borrada antiga): só sobe longo feito com a voz clonada dos
    Cortes de verdade — render.json (gravado pelo alimentador) com voz_clonada e o Applio funcionando."""
    try:
        r = json.loads((ficha / "render.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(r.get("voz_clonada") and r.get("applio_ok"))


REVEZ_LIMPO_DESDE = "2026-10-27T01:20:00+00:00"  # 26/10 22:20: sem nome na legenda e parceiro sem nome na troca


def _variantes(ficha):
    """30/10: o que este longo testou ({"ab": {fator: A/B}, "narradores_modo", "experimento", "variante"}) — vai pro
    longos_postados.json pra o melhorador comparar as variantes pelas views."""
    try:
        r = json.loads((ficha / "render.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: r.get(k) for k in ("ab", "narradores_modo", "experimento", "variante") if r.get(k)}


def _revezamento_limpo(ficha):
    """Dona 26/10 ("o nome na legenda estraga o vídeo pra postagem"): revezamento renderizado DEPOIS do conserto pode
    ir pro canal; os de antes têm nome na legenda e o nome do parceiro falado na troca."""
    try:
        from datetime import timedelta
        r = json.loads((ficha / "render.json").read_text(encoding="utf-8"))
        inicio = datetime.fromisoformat(r["fim"]) - timedelta(seconds=int(r.get("segundos") or 0))
        # 30/10: vídeo SOLO (1 narrador, modo "solo") não tem vozes_lista — vale a voz clonada
        return bool(r.get("vozes_lista") or r.get("voz_clonada")) and inicio >= datetime.fromisoformat(REVEZ_LIMPO_DESDE)
    except (OSError, ValueError, KeyError):
        return False


_PALAVRAO = re.compile(r"\b(caralh\w*|porras?|put[ao]s?|puta\w*|merda\w*|fod[aeiô]\w*|cacete|bucet\w*|arrombad\w*|"
                       r"viad[oa]s?|desgraçad\w*|fdp|cuz[aã]o)\b", re.I)


def _tem_palavrao(ficha):
    """27/10: o KwdN (Dragon) foi ao ar com "caralho" falado numa passagem do revezamento. O que a voz falou nas trocas
    fica no pipeline.log — achou palavrão = não sobe (vira reprovado)."""
    if (ficha / "SEM_PALAVRAO.txt").exists():  # 13/11: bipar_palavrao.py já tirou o palavrão do áudio
        return False
    try:
        txt = (ficha / "pipeline.log").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    linhas = [l for l in txt.splitlines() if "[revezamento]" in l or "text='" in l]
    achou = sorted({m.group(0).lower() for l in linhas for m in _PALAVRAO.finditer(l)})
    if achou:
        log(f"  {ficha.name}: palavrão na narração ({', '.join(achou)}) — não sobe")
    return bool(achou)


FIO_CRED = "novo_codigo_inteligente_n7j"  # Fio da Meada


def _serie(nome):
    """'6rPpPzEFaYM_3_He_got_into_the_Medieval_Age___began' -> 'he_got_into_the_medieval_age' (None = não é série)."""
    m = re.match(r"^[\w-]{11}_(\d{1,2})_*([A-Za-z].+)$", nome or "")
    if not m:
        return None
    return "_".join(re.sub(r"_+", "_", m.group(2)).lower().split("_")[:6])


def _parte(nome):
    """Número da parte ('n_NwO2_X_5Q_10__He_got...' -> 10); sem número = 999."""
    m = re.match(r"^[\w-]{11}_(\d{1,2})_*[A-Za-z]", nome or "")
    return int(m.group(1)) if m else 999


def _dono_serie(nome, est):
    """09/11 dona (Fio da Meada não pode ficar 1 dia sem; parte 3 do 'Medieval Age' = nd67, o melhor longo dela, e as
    outras partes espalharam em Forja/ManhwaReact/inovare): canal que recebe as partes da série. Se alguma parte já
    está na Fio da Meada, a série é dela; senão a do canal da última parte. None = não é série / nunca saiu."""
    if os.environ.get("SERIE_MESMO_CANAL", "1") == "0":
        return None
    s = _serie(nome)
    if not s:
        return None
    canais = [p["canal"] for p in est.get("postados", []) if _serie(p.get("nome", "")) == s]
    if not canais:
        return None
    return FIO_CRED if FIO_CRED in canais else canais[-1]


# 11/11 pesquisador (area_serie_playlist: tirar o atrito pro próximo episódio aumenta a sessão) + dona (a série Medieval
# Age é obra que ela acompanha): longo de SÉRIE vai pra playlist DAQUELA série, em ordem; o resto na playlist geral.
# Nome sem o nome da obra (regra dos títulos). LONGO_PLAYLIST_SERIE=0 = só a geral; LONGO_PLAYLIST="" = nenhuma.
PLAYLIST_SERIES = {"he_got_into_the_medieval_age": "O ENGENHEIRO na ERA MEDIEVAL 🔥 saga completa em ordem"}


VIEWS_LONGO = AQUI / "views_ultimo_longo.json"


def _longo_decolando(cred, est):
    """11/11 (Fio da Meada travada 18 h por um SHORT dela com +2415 views/6 h, e a série Medieval inteira presa na fila):
    pro LONGO só conta se o ÚLTIMO LONGO do canal está decolando (>= LONGO_VIRAL_MIN views nas últimas ~6 h, página
    pública). Short decolando não divide views com longo novo. Motivo (texto) ou None. LONGO_VIRAL_SO_LONGO=0 = antigo."""
    import re as _re
    import urllib.request as _ur
    ult = [p for p in est.get("postados", []) if p.get("canal") == cred and p.get("url")]
    if not ult:
        return None
    ult = ult[-1]
    vid = ult["url"].rstrip("/").split("/")[-1].split("?")[0]
    try:
        h = _ur.urlopen(_ur.Request(f"https://www.youtube.com/watch?v={vid}", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130"}), timeout=30).read().decode(
            "utf-8", "ignore")
        views = int(_re.search(r'"viewCount":"(\d+)"', h).group(1))
    except Exception:  # noqa: BLE001 — sem leitura = não segura
        return None
    try:
        hist = json.loads(VIEWS_LONGO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        hist = {}
    pts = [x for x in hist.get(vid, []) if time.time() - x[0] < 30 * 3600] + [[time.time(), views]]
    hist[vid] = pts
    VIEWS_LONGO.write_text(json.dumps(hist), encoding="utf-8")
    antes = min(pts, key=lambda x: abs(x[0] - (time.time() - 6 * 3600)))
    ganho = views - antes[1]
    if time.time() - antes[0] > 4 * 3600 and ganho >= int(os.environ.get("LONGO_VIRAL_MIN", "300")):
        return f"último longo ({vid}) decolando (+{ganho} views em ~6 h)"
    return None


def _serie_publicar_ja_pronta():
    """13/11: há parte da série da dona (publicar_ja.json) com ficha pronta e ainda não postada?"""
    try:
        ja = set(json.loads((AQUI / "publicar_ja.json").read_text(encoding="utf-8")))
        post = {x.get("nome", "")[:11] for x in json.loads((AQUI / "longos_postados.json").read_text(
            encoding="utf-8")).get("postados", [])}
        fichas = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
        return any(d.name[:11] in ja and d.name[:11] not in post and (d / "nuvem.json").exists()
                   for d in fichas.iterdir())
    except (OSError, ValueError):
        return False


def _segura_longo(cred, canal, est):
    if os.environ.get("LONGO_VIRAL_SO_LONGO", "1") == "0":
        return politica.segurando_viral(canal) if canal else None
    return _longo_decolando(cred, est)


def _playlist_do_longo(nome):
    geral = os.environ.get("LONGO_PLAYLIST", "Histórias COMPLETAS 🔥 (recap)") or None
    if geral is None or os.environ.get("LONGO_PLAYLIST_SERIE", "1") == "0":
        return geral
    s = _serie(nome)
    return PLAYLIST_SERIES.get(s, geral) if s else geral


def _fila(est):
    """Fichas de longo ainda não postadas nem reprovadas, do mais antigo pro mais novo."""
    feitos = {p["nome"] for p in est["postados"]} | set(est["reprovados"])
    out = []
    for nj in FICHAS.glob("*/nuvem.json"):
        d = json.loads(nj.read_text(encoding="utf-8"))
        if (d.get("formato") == "deitado" and d.get("feito_em", "") >= DESDE and nj.parent.name not in feitos
                and (not (nj.parent / "TESTE_NARRADORES.txt").exists() or _revezamento_limpo(nj.parent))
                and _modelo_novo(nj.parent)):
            out.append((d["feito_em"], nj.parent, d))
    return sorted(out, key=lambda x: x[0])


def _avisar_qa(ficha):
    """04/11 (QA dos longos, igual aos Shorts): qa.json do Kaggle com preto/congelado/mudo/volume fora = avisa e POSTA
    (regra da dona: só censura trava). Uma vez por longo."""
    q = ficha / "qa.json"
    if not q.exists() or (ficha / "qa_avisado.txt").exists():
        return
    try:
        j = json.loads(q.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if j.get("ok") is not False and not j.get("problemas"):
        return
    log(f"  QA: {ficha.name[:40]}: {'; '.join(j.get('problemas') or [])[:200]} — posta assim mesmo (só censura trava)")
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(f"🔎 QA do longo {ficha.name[:40]}: {'; '.join(j.get('problemas') or [])[:400]}\n"
                      f"(preto {len(j.get('pretos') or [])}, congelado {len(j.get('congelados') or [])}, mudo "
                      f"{len(j.get('mudos') or [])}, volume {j.get('loudness_lufs')} LUFS) — postado assim mesmo",
                      "recap-longo", importante=True)
        (ficha / "qa_avisado.txt").write_text("1", encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _legenda_sem_tempo(ficha):
    """03/11 dona (KbLv rtQ6e-xzXuI): legenda dessincronizada desde o 1º meme — o render não mediu o início de cada
    clipe ("legenda cai na estimativa por duração") e os memes ficaram fora da conta. Esse vídeo NÃO sobe: reprova e
    avisa (refazer o render)."""
    log_ = ficha / "pipeline.log"
    try:
        txt = log_.read_text(encoding="utf-8", errors="replace") if log_.exists() else ""
    except OSError:
        return False
    if "legenda cai na estimativa" not in txt:
        return False
    log(f"  {ficha.name}: legenda sem o tempo medido dos clipes (vai dessincronizar nos memes) — NÃO sobe, refazer")
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(f"⚠️ Longo {ficha.name[:40]} NÃO postado: legenda ia sair dessincronizada (render sem os tempos "
                      "medidos). Precisa refazer no Kaggle.", "recap-longo", importante=True)
    except Exception:  # noqa: BLE001
        pass
    return True


def _curto(ficha, d):
    """Render quebrado (26/10: KkJZ 9 min pra 1069 frases): menos de 1 s por frase do roteiro não vai pro canal."""
    rot = ficha / "roteiro.txt"
    frases = sum(1 for l in rot.read_text(encoding="utf-8").splitlines() if l.strip()) if rot.exists() else 0
    if frases < 40:
        return False
    r = subprocess.run([RCLONE, "lsjson", d["drive"]], capture_output=True, text=True)
    try:
        mb = json.loads(r.stdout)[0]["Size"] / 1e6
    except (ValueError, IndexError, KeyError):
        return False
    # ~0,24 MB por segundo de vídeo nos longos bons (uNNUW: 551 MB / 2278 s); abaixo de 1 s/frase = quebrado
    if mb / 0.24 < 1.0 * frases:
        log(f"  {ficha.name}: {mb:.0f} MB pra {frases} frases — render quebrado, não sobe")
        return True
    return False


def _subir_1080(video, drive):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0:s=x", str(video)], capture_output=True, text=True, timeout=300)
    w, h = (int(x) for x in r.stdout.strip().split("x")[:2])
    if min(w, h) >= 1080:
        return
    # 04/11: no PC (100% de CPU com a produção) o upscale de um longo de 80 min levou 4 h+ e travou a fila. A VPS
    # hermes-staging (8 núcleos livres, só Drive, nenhuma conta) faz em ~1h30 e devolve ao Drive em 1080p: manda pra lá
    # e este vídeo fica pra uma próxima rodada (que já baixa em 1080p). VPS fora do ar = converte aqui como antes.
    pasta_drive = drive.rsplit("/", 2)[-2]
    try:
        r = subprocess.run(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", "hermes-staging",
                            f"pgrep -f '[u]p1080.sh {pasta_drive}' >/dev/null && echo JA || (cd /opt && nohup ./up1080.sh "
                            f"'{pasta_drive}' > /opt/up1080_{pasta_drive[:11]}.log 2>&1 </dev/null & echo MANDEI)"],
                           capture_output=True, text=True, timeout=60)
        if "JA" in r.stdout or "MANDEI" in r.stdout:
            raise RuntimeError(f"{w}x{h}: convertendo pra 1080p na VPS ({'já estava' if 'JA' in r.stdout else 'mandei agora'})"
                               " — fica pra próxima rodada")
    except (subprocess.SubprocessError, OSError):
        pass
    log(f"  vídeo em {w}x{h} — subindo pra 1080p antes de preparar")
    tmp = video.with_name("up1080.mp4")
    escala = "scale=-2:1080:flags=spline,unsharp=5:5:0.6" if w >= h else "scale=1080:-2:flags=spline,unsharp=5:5:0.6"
    for cod in (["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "20", "-b:v", "0"],
                ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]):
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", escala, *cod, "-pix_fmt", "yuv420p",
                            "-c:a", "copy", "-movflags", "+faststart", str(tmp)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode == 0 and tmp.exists():
            break
        log(f"  upscale {cod[1]} falhou: {(r.stderr or '').strip()[-200:]}")
        tmp.unlink(missing_ok=True)
    else:
        raise RuntimeError("upscale falhou nos 2 codificadores")
    tmp.replace(video)
    r = subprocess.run([RCLONE, "copyto", str(video), drive], capture_output=True, text=True)
    log(f"  1080p ok{' e o Drive ficou em 1080p' if r.returncode == 0 else ' (Drive não atualizou: ' + r.stderr.strip()[-120:] + ')'}")


def _publicar(ficha, d):
    """Baixa e roda o anime_publish. Devolve o caminho do postar.json ou None."""
    pasta = TMP / ficha.name
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True)
    video = pasta / "final_anime_deitado.mp4"
    # 05/11 06:20 (claude-dc, acompanhamento): o D ZEROU 2x de madrugada com este download (4,8 GB) e derrubou o reel
    # da Globo e o carrossel do açaí (clientes). Só baixa se, depois do vídeo, sobrarem 6 GB livres no disco.
    try:
        ls = subprocess.run([RCLONE, "lsjson", d["drive"]], capture_output=True, text=True, timeout=120)
        tam = sum(x.get("Size", 0) for x in json.loads(ls.stdout or "[]"))
    except Exception:  # noqa: BLE001
        tam = 6e9
    # 07/11 00:36 (dona viajando): com 2 canais em paralelo os dois viam o MESMO espaço livre e baixavam juntos
    # (8 + 11,3 GB) — o D caiu a 3,2 GB. Agora a reserva é sob trava: desconta o que os downloads em curso ainda vão
    # ocupar (_RESERVADO) antes de liberar este.
    with _TRAVA_DISCO:
        livre = shutil.disk_usage(str(pasta)).free - sum(_RESERVADO.values())
        # 13/11 dona ("use os 10 GB até acabar; produza até o último MB"): folga 6 -> 1,5 GB (LONGO_FOLGA_GB)
        _folga = float(os.environ.get("LONGO_FOLGA_GB", "1.5")) * 1e9
        if livre - tam < _folga:
            log(f"  sem espaço: {livre / 1e9:.1f} GB livres (já descontados os downloads em curso) e o vídeo tem "
                f"{tam / 1e9:.1f} GB (folga {_folga / 1e9:.1f} GB) — fica pra próxima rodada")
            return None, pasta
        _RESERVADO[str(video)] = tam
    try:
        # 13/11 18h40: a parte 16 travou em 1,99 de 2,00 GB e o rclone ficou parado 10+ min sem errar (sem timeout a
        # rodada inteira esperava pra sempre). Agora: --timeout 2m de conexão parada + 5 tentativas, e o processo
        # todo tem teto de LONGO_DOWNLOAD_MAX_MIN (90). LONGO_DOWNLOAD_TIMEOUT=0 volta o comando antigo.
        _cmd = [RCLONE, "copyto", d["drive"], str(video)]
        if os.environ.get("LONGO_DOWNLOAD_TIMEOUT", "1") != "0":
            _cmd += ["--timeout", "2m", "--contimeout", "60s", "--retries", "5", "--low-level-retries", "20"]
        try:
            r = subprocess.run(_cmd, capture_output=True, text=True,
                               timeout=float(os.environ.get("LONGO_DOWNLOAD_MAX_MIN", "90")) * 60)
        except subprocess.TimeoutExpired:
            log("  download do Drive passou do teto — tenta na próxima rodada")
            return None, pasta
    finally:
        with _TRAVA_DISCO:
            _RESERVADO.pop(str(video), None)
    if r.returncode != 0 or not video.exists():
        log(f"  não baixou do Drive ({r.stderr.strip()[-150:]})")
        return None, pasta
    # 03/11: longos feitos antes da regra (01/11, ex. bXe7) estão em 1280x720 no Drive. O upscale ficava pro poster,
    # no fim, em libx264 com a CPU cheia, e falhou 2x hoje (19:40) — nada subiu o dia todo. Agora sobe pra 1080p
    # LOGO depois de baixar (NVENC da placa; sem placa = libx264) e devolve ao Drive em 1080p: a próxima vez já vem certo.
    try:
        _subir_1080(video, d["drive"])
    except Exception as e:  # noqa: BLE001
        if "próxima rodada" in str(e):
            log(f"  {e}")
            shutil.rmtree(pasta, ignore_errors=True)
            return None, pasta
        log(f"  1080p falhou ({type(e).__name__}: {str(e)[:200]}) — o poster tenta de novo")
    for extra in ("capitulos.json", "roteiro.txt"):
        if (ficha / extra).exists():
            shutil.copy2(ficha / extra, pasta / extra)
    anota = pasta / "_postar_path.txt"
    cmd = [PY, "-X", "utf8", str(PUBLISH), "--video", str(video), "--anime", d.get("anime") or ficha.name[:40],
           "--cap", "1", "--formato", "deitado", "--midia", "manhwa", "--source-url", d.get("source_url", ""),
           "--titulo-original", d.get("titulo_original", ""), "--anota-postar", str(anota), "--sem-qa"]
    if (pasta / "roteiro.txt").exists():
        cmd += ["--roteiro", str(pasta / "roteiro.txt")]
    # 30/10: variante A/B do TÍTULO (render.json "ab".titulo_triade, sorteada no envio): A = título como antes,
    # B = tríade humilhação -> virada -> vingança (seo_generator lê ANIME_TITULO_TRIADE). Sem "ab" = B (era o padrão).
    try:
        ab = json.loads((ficha / "render.json").read_text(encoding="utf-8")).get("ab") or {}
    except (OSError, ValueError):
        ab = {}
    env = dict(os.environ, ANIME_TITULO_TRIADE="0" if ab.get("titulo_triade") == "A" else "1")
    # 05/11 dona ("resolva o gargalo de postagem"): a capa (Flow, 1 h+) não segura mais o envio — capas_depois.py
    if os.environ.get("CAPA_DEPOIS", "1") == "1":
        env["ANIME_CAPA_DEPOIS"] = "1"
    # 02/11 variante RECAP DE ANIME (docs\VARIANTE_ANIME_RECAP.md): título/tags/sufixo próprios no seo_generator
    try:
        if json.loads((ficha / "render.json").read_text(encoding="utf-8")).get("tipo") == "anime_recap" \
                or (ficha / "VARIANTE_ANIME_RECAP.txt").exists():
            env["ANIME_VARIANTE"] = "anime_recap"
    except (OSError, ValueError):
        pass
    # 02/11 dona ("versionamento dos títulos/tags; o de antes, com palavras que as pessoas buscam, era melhor"): a
    # versão ativa de config\seo_versoes.json manda no título (a tríade dela vence o A/B acima)
    try:
        env["ANIME_SEO_VERSAO"] = json.loads((PUBLISH.parent.parent / "config" / "seo_versoes.json")
                                             .read_text(encoding="utf-8"))["ativa_longo"]
    except (OSError, ValueError, KeyError):
        pass
    r = subprocess.run(cmd, cwd=str(PUBLISH.parent), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=3 * 3600, env=env)
    if not anota.exists():
        log(f"  anime_publish falhou rc={r.returncode}: {(r.stdout + r.stderr).strip()[-300:]}")
        return None, pasta
    return Path(anota.read_text(encoding="utf-8").strip()), pasta


def _projeto(cred):
    # 02/11 dona: "pode liberar o InovareManhwaVerse e o Manhwa Noturno pra vídeo longo" — canais do hipercool; o
    # longo entra como projeto longo_recap (alimentador "livre" só deles, postador-de-videos\bin\canais.py DECISOES)
    return "longo_recap" if cred in ("novo_inovaremanhwaverse", "novo_manhwanoturno") else "parceiro"


def rodada(ver=False):
    import politica
    est = _estado()
    hoje = datetime.now().strftime("%Y-%m-%d")
    fila = _fila(est)
    # 29/10 dona: "o do Pastor tem que postar de imediato, automático" — --primeiro <id> passa ele na frente
    if "--primeiro" in sys.argv:
        alvo = sys.argv[sys.argv.index("--primeiro") + 1]
        fila.sort(key=lambda x: not x[1].name.startswith(alvo))
    # 04/11: --pular id1,id2 = esses ficam pra próxima rodada (ex.: ainda convertendo pra 1080p na VPS — o PC a 100%
    # levaria 4 h por longo e travava a fila inteira atrás dele)
    if "--pular" in sys.argv:
        fora = [x for x in sys.argv[sys.argv.index("--pular") + 1].split(",") if x]
        fila = [x for x in fila if not any(x[1].name.startswith(p) for p in fora)]
    log(f"rodada: {len(fila)} longo(s) esperando")
    # 02/11 dona: "cada canal recebe um longo pra ver qual se sai melhor" — a ordem fixa dava 3 longos pro Forja e
    # nenhum pros últimos da lista. Agora quem tem MENOS longos vai primeiro (empate = ordem de CANAIS)
    qtd = {}
    for p in est["postados"]:
        qtd[p["canal"]] = qtd.get(p["canal"], 0) + 1
    # 02/11 dona (depois): "proporção de vídeos postados por views ganhas — todos recebem, os que dão mais recebem
    # mais". 1º quem tem 0 longo (testar todo público); depois a nota = views por longo do canal (colab\views_longos.py,
    # página pública, releitura a cada 6 h) ÷ (longos já recebidos + 1): canal que rende mais e ainda recebeu pouco
    # vai na frente. Sem views lidas = nota 0 (cai pra ordem por quantidade de antes).
    try:
        import views_longos
        vpl = {cred: c["views_por_longo"] for cred, c in views_longos.por_canal(views_longos.atualizar()).items()}
    except Exception as e:  # noqa: BLE001
        log(f"views dos longos indisponíveis ({type(e).__name__}) — ordem só pela quantidade")
        vpl = {}

    # 03/11 dona: "focar no manhwa br que está com boas visualizações, na frente da fila de hoje, depois HistoriasEmFrames
    # — isso depois que todos tiverem pelo menos um longo". Lista em config/longo.json "prioridade_canais" (nomes).
    try:
        prio = list((json.loads((AQUI.parent / "config" / "longo.json").read_text(encoding="utf-8"))
                     .get("prioridade_canais") or []))
    except (OSError, ValueError):
        prio = []

    hoje_qtd = {}
    for p in est["postados"]:
        if p["em"].startswith(hoje):
            hoje_qtd[p["canal"]] = hoje_qtd.get(p["canal"], 0) + 1

    # 06/11 dona ("invista mais nas 4 principais, elas devem receber o dobro — passar 2x na fila"): as 4 primeiras de
    # prioridade_canais (config/longo.json) contam metade dos longos do dia — o 2º longo delas entra junto com o 1º
    # dos outros canais. DOBRO_TOP=0 desliga.
    top = set(prio[:int(os.environ.get("DOBRO_TOP", "4") or 0)])
    # 07/11 dona ("invista mais na Fio da Meada, dobre os que vão bem, o melhor triplique; fila pra todos mas
    # proporcional às visualizações"): pesos_canais do config/longo.json (calculado pelo ranking real de views por
    # longo). A vez é de quem tem menos (longos de hoje ÷ peso): peso 3 recebe 3 longos pra cada 1 de um peso 1.
    # Todo canal com peso > 0 continua recebendo. Sem pesos_canais = regra antiga (dobro do top 4).
    try:
        pesos = {k: float(v) for k, v in (json.loads((AQUI.parent / "config" / "longo.json").read_text(
            encoding="utf-8")).get("pesos_canais") or {}).items() if not k.startswith("_")}
    except (OSError, ValueError):
        pesos = {}

    def _ordem(c):
        n = qtd.get(c[0], 0)
        if pesos:
            w = pesos.get(c[1], 1.0)
            if w <= 0:
                return (9, 0, 0, 0)
            return (hoje_qtd.get(c[0], 0) / w, -w, n)
        if hoje_qtd.get(c[0], 0):  # 04/11: o 2º longo do dia só depois de todos os canais terem o 1º
            peso = hoje_qtd[c[0]] / (2 if c[1] in top else 1)
            if peso < 1:  # top com 1 longo hoje: ainda está na 1ª volta (passa 2x)
                p = prio.index(c[1]) if c[1] in prio else len(prio)
                return (0.5, p, 0, 0)
            return (2, peso, 0, 0)
        p = prio.index(c[1]) if c[1] in prio else len(prio)
        return (n > 0, p, -(vpl.get(c[0], 0.0) / (n + 1)), n)
    ordem = sorted(CANAIS, key=_ordem)
    # 09/11 dona: "mais do que 3x à Fio da Meada, priorizar como uma fila separada, postando sempre o máximo mas sem
    # atrapalhar o algoritmo — longo novo na frente do que está veiculando divide as views". Fila VIP: o longo pronto vai
    # PRIMEIRO pra ela, desde que o último longo dela tenha >= FIO_VIP_INTERVALO_H (24) e nenhum vídeo dela esteja
    # decolando (aí ela fica de fora desta rodada, em vez de postar programado por cima). FIO_VIP=0 desliga.
    if os.environ.get("FIO_VIP", "1") != "0":
        vip = [c for c in ordem if c[1] == "Fio da Meada"]
        if vip:
            cred_vip = vip[0][0]
            ult = max((p["em"] for p in est["postados"] if p["canal"] == cred_vip), default="")
            h_desde = ((datetime.now() - datetime.strptime(ult[:16], "%Y-%m-%dT%H:%M")).total_seconds() / 3600
                       if ult else 999)
            segura = None
            try:
                cv, _ = politica.achar_canal(cred_vip)
                segura = _segura_longo(cred_vip, cv, est)
            except Exception:  # noqa: BLE001
                pass
            ordem = [c for c in ordem if c[0] != cred_vip]
            if segura:
                log(f"Fio da Meada (VIP): {segura} — não recebe longo por cima do que está decolando")
            # 13/11: a parte 15 do Medieval (série da dona, publicar_ja) ficou presa 1 h aqui ("último longo há 2 h").
            # Parte da série pronta passa por cima do intervalo e do "decolando". SERIE_FURA_INTERVALO=0 desliga.
            elif h_desde < float(os.environ.get("FIO_VIP_INTERVALO_H", "24")) and not (
                    os.environ.get("SERIE_FURA_INTERVALO", "1") != "0" and _serie_publicar_ja_pronta()):
                log(f"Fio da Meada (VIP): último longo há {h_desde:.0f} h — espera completar o intervalo")
            else:
                ordem = vip + ordem
                log(f"Fio da Meada (VIP): primeira da fila (último longo há {h_desde:.0f} h)")
    # 06/11 dona ("ver se compensa voltar aos outros que não estão dando nada"): canais_minimo do config/longo.json
    # (ranking das views públicas) recebem no máximo 1 longo a cada 3 dias — o resto vai pros que respondem.
    try:
        minimo = set(json.loads((AQUI.parent / "config" / "longo.json").read_text(encoding="utf-8"))
                     .get("canais_minimo") or [])
    except (OSError, ValueError):
        minimo = set()
    if minimo:
        limite = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        recente = {p["canal"] for p in est["postados"] if p.get("em", "") >= limite}
        fora = [nm for cr, nm in ordem if nm in minimo and cr in recente]
        ordem = [c for c in ordem if not (c[1] in minimo and c[0] in recente)]
        if fora:
            log(f"canais no mínimo (1 longo/3 dias, já receberam): {', '.join(fora)}")
    log("ordem dos canais: " + ", ".join(f"{nm} ({qtd.get(cr, 0)} longos, {vpl.get(cr, 0)} v/longo)"
                                        for cr, nm in ordem[:6]))
    # 04/11 dona ("resolva o gargalo de postagem": 19 longos feitos no dia e 5 postados, 41 na fila): os canais
    # sobem em PARALELO (POSTAR_PARALELO, 3) — cada canal envia pelo Chrome de uma máquina (notebooks/PC2/desktop/PC1,
    # cada uma com a sua vez e o PC1 com a trava própria), então 3 envios correm juntos sem um esperar o outro.
    # A fila sai com trava (_TRAVA_FILA): 2 canais nunca pegam o mesmo longo.
    # 05/11 08h: com 3-4 juntos, os canais caíam no PC1 (notebooks ocupados com Veo/logins), esperavam 40 min a
    # trava e desistiam — 0 longo das 02:37 às 08:00. 2 juntos + espera de até 4 h pela vez do PC1.
    os.environ.setdefault("YT_TRAVA_ESPERA_MIN", "240")
    try:
        bloqueados_cfg = set(json.loads((AQUI.parent / "config" / "longo.json").read_text(encoding="utf-8"))
                             .get("canais_bloqueados") or [])
    except (OSError, ValueError):
        bloqueados_cfg = set()
    n_par = 1 if ver else max(1, int(os.environ.get("POSTAR_PARALELO", "2")))  # 05/11: 4 = PC1, PC2, x200, acer
    # 11/11 dona (Medieval Age = prioridade máxima): a parte 9 ficou sem disco porque o OUTRO canal baixou o dele
    # antes (5,4 GB cada). Fio da Meada VIP na frente e disco < 20 GB = 1 envio por vez (ela pega o disco primeiro).
    try:
        if (n_par > 1 and ordem and ordem[0][1] == "Fio da Meada"
                and shutil.disk_usage(str(TMP)).free < float(os.environ.get("VIP_SOZINHA_GB", "20")) * 1e9):
            n_par = 1
            log("Fio da Meada (VIP) na frente e disco apertado — 1 envio por vez nesta rodada")
    except OSError:
        pass

    def _um_canal(cred, nome_canal):
        # 05/11: canal sem os recursos avançados (aviso do YouTube) não recebe longo — config/longo.json canais_bloqueados
        if cred in bloqueados_cfg:
            log(f"{nome_canal}: BLOQUEADO pra longo (config/longo.json canais_bloqueados) — pula")
            return
        # 04/11 dona: "dá pra postar mais de um por dia em cada canal; os longos têm espaço de prioridade todo dia" —
        # até LONGOS_POR_DIA (2) por canal; a ordem abaixo já põe na frente quem recebeu menos hoje
        # 13/11: a parte 15 do Medieval parou aqui (Fio da Meada já tinha 8, 13 e 14 no dia). Parte da série da dona
        # pronta não conta o limite por dia — só o limite do YouTube segura. SERIE_FURA_INTERVALO=0 desliga.
        serie_vez = os.environ.get("SERIE_FURA_INTERVALO", "1") != "0" and _serie_publicar_ja_pronta()
        if not serie_vez and sum(1 for p in est["postados"] if p["canal"] == cred and p["em"].startswith(hoje)) >= \
                int(os.environ.get("LONGOS_POR_DIA", "2")):
            log(f"{nome_canal}: já recebeu os longos de hoje")
            return
        # 29/10: o limite/cota só aparecia DEPOIS de baixar e preparar o longo (~5 min e ~1 GB de disco por canal);
        # na rodada de 28/10 isso se repetiu em 6 canais e encheu o D:. Agora confere antes.
        canal, _ = politica.achar_canal(cred)
        programar = None
        if canal:
            ate = politica.em_limite_diario(canal)
            if ate:
                log(f"{nome_canal}: limite diário do YouTube até {ate:%d/%m %H:%M} — pula")
                return
            # 04/11: a "cota do dia" é a dos Shorts (mesmo projeto parceiro) — o longo tem faixa própria
            # (politica.horario_longo / _checar_longo), então não pula mais por ela
            viral = _segura_longo(cred, canal, est)  # 30/10 / 11/11: só o LONGO do canal decolando segura
            # 04/11 dona: "se estão com vídeos decolando, poste programado" — não pula mais: sobe agora e abre daqui a
            # PROGRAMAR_VIRAL_H (6 h = a janela em que o decolando é medido), sem abrir na hora pelo publicar_ja
            programar = None
            if viral:
                from datetime import timedelta, timezone
                h = float(os.environ.get("PROGRAMAR_VIRAL_H", "6"))
                programar = (datetime.now(timezone.utc) + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
                log(f"{nome_canal}: {viral} — posta PROGRAMADO pra daqui a {h:.0f} h ({programar})")
        while True:
            with _TRAVA_FILA:
                # 09/11: parte de SÉRIE ("(9) He got into the Medieval Age...") só sai no canal dono da série
                # (_dono_serie); longo de série de outro canal fica na fila pra ele. SERIE_MESMO_CANAL=0 desliga.
                # 12/11: longo traduzido (nuvem.json com "canal") só sai no canal da língua dele
                cand = [i for i, (_, f, _d) in enumerate(fila) if _dono_serie(f.name, est) in (None, cred)
                        and (not _d.get("canal") or _d["canal"] == cred)]
                if not cand:
                    break
                # 11/11 dona (Medieval Age: completar em ordem): entre partes da MESMA série, sai a de menor número
                # (6 antes de 9 antes de 10). Fora de série, a ordem da fila como antes.
                i_ok = cand[0]
                s0 = _serie(fila[i_ok][1].name)
                # 11/11 dona ("quero a parte 11 online o mais rápido possível"): --primeiro <id> passa por cima da
                # ordem da série (a escolha manual vale)
                manual = "--primeiro" in sys.argv and fila[i_ok][1].name.startswith(
                    sys.argv[sys.argv.index("--primeiro") + 1])
                if s0 and not manual:
                    mesma = [i for i in cand if _serie(fila[i][1].name) == s0]
                    i_ok = min(mesma, key=lambda i: _parte(fila[i][1].name))
                _, ficha, d = fila.pop(i_ok)
            if ver:
                log(f"{nome_canal}: postaria {ficha.name}")
                break
            if _curto(ficha, d) or _tem_palavrao(ficha) or _legenda_sem_tempo(ficha):
                est["reprovados"].append(ficha.name)
                _gravar_estado(est)
                continue
            log(f"{nome_canal}: preparando {ficha.name}")
            _avisar_qa(ficha)
            pj, pasta = _publicar(ficha, d)
            if not pj:
                continue
            p = json.loads(pj.read_text(encoding="utf-8"))
            if str(p.get("revisao", "")).startswith("reprovado"):
                log(f"  REPROVADO na revisão ({p['revisao'][:120]}) — não sobe")
                est["reprovados"].append(ficha.name)
                _gravar_estado(est)
                shutil.rmtree(pj.parent, ignore_errors=True)
                shutil.rmtree(pasta, ignore_errors=True)
                continue
            video = pj.parent / p["arquivo"]
            # categoria própria: o postar_tudo_hoje (categoria "animes") não pega este de novo
            p.update(privacy="public", canais=[cred], categoria="longo_recap")
            pj.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
            politica.marcar_aprovacao(video, "aprovado", f"postar_longos: revisão {str(p.get('revisao'))[:60]}")
            thumb = pj.parent / p["thumb"] if p.get("thumb") else None
            log(f"  subindo: {p['titulo'][:80]}")
            # 04/11 dona ("lá ele pode fazer com prioridade — é um caso de testar se tem diferença"): teste_envio.json
            # {"maquina": "desktop", "restam": N} manda os próximos N envios de canal logado lá por aquela máquina
            teste_env = AQUI / "teste_envio.json"
            t_env = time.time()
            try:
                te = json.loads(teste_env.read_text(encoding="utf-8")) if teste_env.exists() else {}
            except (OSError, ValueError):
                te = {}
            usar_maq = None
            if te.get("restam", 0) > 0 and te.get("maquina") and n_par == 1:
                try:
                    nav = json.loads(Path(r"D:\postador-de-videos\config\youtube_navegador.json").read_text(
                        encoding="utf-8"))["canais"]
                    logins = json.loads(Path(r"D:\postador-de-videos\config\netbooks_logins.json").read_text(
                        encoding="utf-8"))
                    em = next((v.get("email") for v in nav.values() if cred in str(v.get("creds"))), "") or ""
                    if ((logins.get(em.split("@")[0].lower()) or {}).get(te["maquina"]) or {}).get("youtube"):
                        usar_maq = te["maquina"]
                except (OSError, ValueError, KeyError):
                    pass
            if usar_maq:
                os.environ["YT_MAQUINA"] = usar_maq
                log(f"  TESTE: este envio sai pelo {usar_maq}")
            # 11/11 dona (Medieval 9/11 sem views: "pode ser que esqueceu de colocar algo"): as partes saíam com título
            # solto — quem viu a parte 3 (308 views) não reconhecia a continuação. Parte de SÉRIE = "PARTE N |" no
            # título + 1ª linha da descrição apontando a saga. LONGO_TITULO_PARTE=0 desliga.
            n_parte = _parte(ficha.name)
            if (os.environ.get("LONGO_TITULO_PARTE", "1") != "0" and _serie(ficha.name) and n_parte < 999
                    and not re.match(r"(?i)\s*parte\s*\d", p["titulo"])):
                p["titulo"] = f"PARTE {n_parte} | {p['titulo']}"[:100]
                saga = PLAYLIST_SERIES.get(_serie(ficha.name)) or ""
                p["descricao"] = (f"Parte {n_parte} da saga" + (f" \"{saga}\"" if saga else "")
                                  + " — assista em ordem na playlist do canal.\n\n" + (p.get("descricao") or ""))
                log(f"  título de série: {p['titulo']}")
            # 11/11 pesquisador (area_metadata_spam, política de spam do YouTube: "título que promete o que o vídeo não
            # entrega", ex. oficial 'partida completa'): recap cobre PARTE da obra -> tira "(COMPLETO)", "Capítulo 1
            # COMPLETO", "FINAL" do título. LONGO_TITULO_SEM_PROMESSA=0 desliga.
            if os.environ.get("LONGO_TITULO_SEM_PROMESSA", "1") != "0":
                t0 = p["titulo"]
                t1 = re.sub(r"(?i)\s*[\(\[]\s*(completo|completa|final|todos os cap[ií]tulos)\s*[\)\]]", "", t0)
                t1 = re.sub(r"(?i)\s*\b(cap[ií]tulo\s*\d+\s+)?completo\b", "", t1)
                t1 = re.sub(r"\s{2,}", " ", t1).strip(" -|")
                if t1 and t1 != t0:
                    p["titulo"] = t1
                    log(f"  título sem promessa enganosa: {t0} -> {t1}")
            status, info = politica.postar_youtube(cred, video, p["titulo"], p["descricao"], p.get("tags") or [],
                                                   privacy="public", projeto=_projeto(cred), tipo="completo",
                                                   thumbnail=thumb if thumb and thumb.exists() else None,
                                                   publish_at=programar,
                                                   # 05/11 (longos com 13 impressões/semana): playlist dos completos —
                                                   # recurso padrão (não precisa de recursos avançados), sem nome de obra;
                                                   # a playlist entra na página do canal e nas sugestões do fim do vídeo.
                                                   # Falhou = o vídeo sobe assim mesmo. LONGO_PLAYLIST="" desliga.
                                                   playlist=_playlist_do_longo(ficha.name))
            os.environ.pop("YT_MAQUINA", None)
            try:
                mb = round(video.stat().st_size / 1e6)
            except OSError:
                mb = None
            log(f"  envio: {mb} MB em {(time.time() - t_env) / 60:.0f} min ({usar_maq or 'normal'})")
            if usar_maq:
                te["restam"] = te.get("restam", 1) - 1
                te.setdefault("feitos", []).append({"canal": nome_canal, "mb": mb, "min": round((time.time() - t_env) / 60),
                                                    "status": status, "em": datetime.now().isoformat("T", "minutes")})
                teste_env.write_text(json.dumps(te, ensure_ascii=False, indent=1), encoding="utf-8")
            log(f"  {status}: {info}")
            if status == "ok":
                # 29/10 noite (Fable): a duração vai junto — o melhorador_longo calcula o % assistido com ela (antes
                # saía "None%" em todos os postados: a duração só existia nos vídeos que ele mesmo analisou)
                try:
                    dur_s = round(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                                        "-of", "csv=p=0", str(video)], capture_output=True, text=True,
                                                       timeout=60).stdout.strip()))
                except Exception:  # noqa: BLE001
                    dur_s = None
                # 30/10: o id do YouTube tem 11 caracteres e pode ter "_" (RRrhPp_qeCA virava "RRrhPp")
                est["postados"].append({"nome": ficha.name, "vid": ficha.name[:11], "canal": cred,
                                        "canal_nome": nome_canal, "url": info, "titulo": p["titulo"],
                                        "em": datetime.now().isoformat(timespec="minutes"), "duracao_s": dur_s,
                                        **_variantes(ficha), "seo_versao": p.get("seo_versao"),
                                        "estilo_titulo": p.get("estilo_titulo"), "tags": p.get("tags") or []})
                # 29/10 dona: os melhores cortes do longo vão como Shorts pro MESMO canal que recebeu o longo
                est.setdefault("cortes_pendentes", []).append({"nome": ficha.name, "canal": cred,
                                                               "canal_nome": nome_canal, "drive": d["drive"],
                                                               "url_longo": info})
                _gravar_estado(est)
                # 10/11 dona: "quero ser notificada com ênfase assim que ele postar" — série Medieval Age (obra que ela
                # acompanha). Aviso IMPORTANTE (sai na hora, fora do resumo). AVISO_SERIE="" desliga.
                serie = os.environ.get("AVISO_SERIE", "medieval_age")
                if serie and serie.replace("_", "") in ficha.name.lower().replace("_", ""):
                    try:
                        sys.path.insert(0, r"D:\video-fila")
                        import avisos
                        avisos.enviar(f"🔥🔥 SAIU A SÉRIE QUE VOCÊ ACOMPANHA — He got into the Medieval Age\n"
                                      f"{p['titulo']}\nCanal: {nome_canal}\n{info}", "recap-longo", importante=True)
                    except Exception as e:  # noqa: BLE001
                        log(f"  aviso da série falhou: {e}")
                # 02/11 dona ("os que saem 8-9h você tem que postar já públicos, tem minha autorização"): ids em
                # colab\publicar_ja.json abrem na hora — o upload sai agendado (o poster força) e logo depois o Studio
                # troca pra público. Lista vazia/sem arquivo = agendado como sempre.
                try:
                    ja = json.loads((AQUI / "publicar_ja.json").read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    ja = []
                if p.get("capa_depois"):  # 05/11: capa gerada depois; o capas_depois.py abre quando aplicar
                    try:
                        import capas_depois
                        vid_cd = str(info).rstrip("/").split("/")[-1].split("=")[-1]
                        capas_depois.registrar(cred, vid_cd, pj.parent, p["capa_depois"],
                                               publicar=ficha.name[:11] in ja and not programar)
                        log(f"  capa: vai depois (capas_depois.json) — {vid_cd}")
                        # 12/11 dona ("Medieval 13 tem que postar já público e me avisar assim que postar"): vídeo do
                        # publicar_ja NÃO espera a capa própria (horas no Flow): abre JÁ com a capa reserva da série
                        # (capas_depois._capa_reserva) e avisa no Telegram; a capa própria troca depois.
                        # PUBLICAR_JA_SEM_ESPERAR_CAPA=0 = espera a capa como antes.
                        if (ficha.name[:11] in ja and not programar
                                and os.environ.get("PUBLICAR_JA_SEM_ESPERAR_CAPA", "1") != "0"):
                            st_ = r"D:\postador-de-videos\bin\youtube_studio_extras.py"
                            item_ = next((x for x in capas_depois.ler() if x["vid"] == vid_cd), None)
                            res_ = capas_depois._capa_reserva(item_, set()) if item_ else None
                            if res_:
                                capas_depois._studio(cred, vid_cd, "--capa", str(res_))
                                log(f"  capa reserva da série no ar: {res_.parent.name}/{res_.name}")
                            # 13/11 19:33 (parte 16): "a página de edição não abriu" logo após o envio (vídeo ainda
                            # processando); na mão 5 min depois foi "ok". Tenta até PUBLICO_TENTATIVAS (3) com 3 min.
                            for _tent in range(int(os.environ.get("PUBLICO_TENTATIVAS", "3"))):
                                rv = subprocess.run([r"D:\manhwa-react\.venv\Scripts\python.exe", st_, "--canal", cred,
                                                     f"--video={vid_cd}", "--visibilidade", "public"],
                                                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                                                    timeout=1800, cwd=r"D:\postador-de-videos\bin")
                                res = [l for l in (rv.stdout + rv.stderr).splitlines() if "RESULTADO" in l]
                                if res and "não abriu" not in res[-1]:
                                    break
                                log("  página de edição não abriu (vídeo processando?) — tenta de novo em 3 min")
                                time.sleep(180)
                            log(f"  público JÁ (sem esperar a capa própria): {res[-1] if res else 'sem resposta'}")
                            try:
                                sys.path.insert(0, r"D:\video-fila")
                                import avisos
                                avisos.enviar(f"🔥🔥 SAIU A SÉRIE QUE VOCÊ ACOMPANHA — NO AR E PÚBLICO AGORA\n"
                                              f"{p['titulo']}\nCanal: {nome_canal}\n{info}", "recap-longo",
                                              importante=True, chave=f"serie_publica:{vid_cd}")
                            except Exception:  # noqa: BLE001
                                pass
                    except Exception as e:  # noqa: BLE001
                        log(f"  capa depois não registrou ({type(e).__name__}: {e})")
                elif ficha.name[:11] in ja and not programar:
                    vid_yt = str(info).rstrip("/").split("/")[-1].split("=")[-1]
                    try:
                        rv = subprocess.run([r"D:\manhwa-react\.venv\Scripts\python.exe",
                                             r"D:\postador-de-videos\bin\youtube_studio_extras.py", "--canal", cred,
                                             f"--video={vid_yt}", "--visibilidade", "public"], capture_output=True,
                                            text=True, encoding="utf-8", errors="replace", timeout=1800,
                                            cwd=r"D:\postador-de-videos\bin")
                        res = [l for l in (rv.stdout + rv.stderr).splitlines() if "RESULTADO" in l]
                        log(f"  público já (autorização da dona): {res[-1] if res else 'sem resposta'}")
                    except Exception as e:  # noqa: BLE001
                        log(f"  público já falhou ({type(e).__name__}) — fica agendado")
                try:  # 01/11 (dona): o longo postado aparece destacado no bot de postagem, com tempo e melhorias
                    if r"D:\video-fila\linhas\LONGOS" not in sys.path:
                        sys.path.append(r"D:\video-fila\linhas\LONGOS")
                    if r"D:\video-fila" not in sys.path:
                        sys.path.append(r"D:\video-fila")
                    import avisos
                    import ficha_longo
                    avisos.enviar(ficha_longo.texto(ficha).replace("VÍDEO LONGO PRONTO", "VÍDEO LONGO AGENDADO"),
                                  "no ar longo", importante=True, html_ok=True, chave="<SEGREDO_REMOVIDO>" + ficha.name)
                except Exception as e:  # noqa: BLE001 — aviso nunca derruba a postagem
                    log(f"aviso do longo não saiu: {e}")
                # só o vídeo sai (o original segue no manhwa-drive): o postar.json e as capas ficam pro extras_ledger
                # montar o teste A/B quando o vídeo abrir e pro placar ler a pose de cada capa (30/10: rmtree da
                # pasta inteira = teste A/B nunca acontecia nos longos)
                for mp4 in pj.parent.glob("*.mp4"):
                    mp4.unlink(missing_ok=True)
                shutil.rmtree(pasta, ignore_errors=True)
            else:
                with _TRAVA_FILA:
                    fila.insert(0, (d.get("feito_em"), ficha, d))  # não perde a vez; tenta noutra rodada
                if status != "timeout":  # timeout pode ter subido: deixa a pasta pra conferir no Studio
                    shutil.rmtree(pj.parent, ignore_errors=True)
                shutil.rmtree(pasta, ignore_errors=True)
            break


    # 12/11 dona (longos nas outras línguas): canal estrangeiro com longo traduzido pronto entra na rodada.
    # LONGO_IDIOMAS=0 desliga.
    if os.environ.get("LONGO_IDIOMAS", "1") != "0":
        nomes_lang = {"8ROQmZVjbpwiwMoX": "inovare viet", "UYjkdFO3V3kjmKU5": "inovare eng",
                      "nYsAKUb3DbR1QOEm": "inovare ind", "q3mik36FjtTgFkNC": "inovare thai",
                      "GG97QQt8lmyv0dDG": "inovare french", "GtuH5ezUK8eBaC60": "inovare hindi"}
        ja = {c[0] for c in ordem}
        for _f, _fi, _d in list(fila):
            c = _d.get("canal")
            if c and c in nomes_lang and c not in ja:
                ordem.append((c, nomes_lang[c]))
                ja.add(c)
    if n_par == 1:
        for cred, nome_canal in ordem:
            _um_canal(cred, nome_canal)
    else:
        from concurrent.futures import ThreadPoolExecutor
        log(f"postando {n_par} canais ao mesmo tempo")
        with ThreadPoolExecutor(max_workers=n_par) as ex:
            for r in ex.map(lambda c: _vivo(_um_canal, *c), ordem):
                pass


CORTES_POR_RODADA = 2  # por canal: 3 rodadas/dia → até 6 Shorts de corte/dia no canal, dentro da escada
# 30/10: teto por DIA também (est["cortes_dia"]) — assim a rodada pode rodar mais vezes (pegar a vaga do longo quando o
# limite diário do YouTube solta) sem passar de 6 cortes por canal no dia
CORTES_POR_DIA = 6


def postar_cortes(ver=False):
    """Shorts dos melhores trechos (bin/melhores_cortes.py, pasta cortes_longo ao lado do video.mp4 no Drive) no canal
    que recebeu o longo, com a descrição apontando pro vídeo completo. Agendado como tudo (politica.postar_youtube)."""
    import politica
    est = _estado()
    pend = est.get("cortes_pendentes") or []
    feitos = set(est.setdefault("cortes_postados", []))
    hoje = datetime.now().strftime("%Y-%m-%d")
    dia = {k: v for k, v in (est.get("cortes_dia") or {}).items() if k.startswith(hoje)}
    est["cortes_dia"] = dia
    for item in list(pend):
        pasta_drive = item["drive"].rsplit("/", 1)[0] + "/cortes_longo"
        r = subprocess.run([RCLONE, "cat", f"{pasta_drive}/cortes.json"], capture_output=True, text=True,
                           encoding="utf-8")
        try:
            cortes = json.loads(r.stdout) if r.returncode == 0 else []
        except ValueError:
            cortes = []
        if not cortes:
            log(f"cortes: {item['nome']} sem cortes no Drive — sai da lista")
            pend.remove(item)
            continue
        canal, _ = politica.achar_canal(item["canal"])
        if canal and (politica.em_limite_diario(canal) or politica.cota_restante(canal, "parceiro") <= 0):
            log(f"cortes: {item['canal_nome']} sem vaga hoje — {item['nome']} espera")
            continue
        # 13/11 (Medieval 13/14 presas: os cortes do longo subiram no Fio da Meada às 04:53 gastando o mesmo limite
        # diário de envios): canal com parte da série da dona pronta e não postada = corte espera. SERIE_RESERVA_ENVIO=0
        try:
            sys.path.insert(1, str(AQUI.parent / "bin"))
            import parceiro_diario as _pd
            if os.environ.get("SERIE_RESERVA_ENVIO", "1") != "0" and _pd._serie_esperando(item["canal"]):
                log(f"cortes: {item['canal_nome']} — parte da série da dona esperando; {item['nome']} espera")
                continue
        except Exception:  # noqa: BLE001
            pass
        n = 0
        for c in sorted(cortes, key=lambda x: -float(x.get("nota") or 0)):
            chave = f"{item['nome']}/{c['arquivo']}"
            if chave in feitos:
                continue
            if n >= CORTES_POR_RODADA or dia.get(f"{hoje}|{item['canal']}", 0) >= CORTES_POR_DIA:
                break
            if ver:
                log(f"cortes: postaria {chave} em {item['canal_nome']} ({c.get('titulo')})")
                n += 1
                continue
            local = TMP / "_cortes" / item["nome"] / c["arquivo"]
            local.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([RCLONE, "copyto", f"{pasta_drive}/{c['arquivo']}", str(local)], capture_output=True)
            if not local.exists():
                continue
            titulo = (c.get("titulo") or c.get("gancho") or "Você não vai acreditar no que ele fez")[:95]
            desc = (f"{c.get('gancho', '')}\n\n▶ Vídeo COMPLETO no canal: {item.get('url_longo', '')}\n\n"
                    "#shorts #manhwa #recap #anime")
            politica.marcar_aprovacao(local, "aprovado", "corte do longo já aprovado na revisão do longo")
            status, info = politica.postar_youtube(item["canal"], local, titulo, desc, ["shorts", "manhwa", "recap"],
                                                   privacy="public", projeto="parceiro", tipo="short")
            log(f"cortes: {item['canal_nome']} {c['arquivo']} — {status}: {info}")
            local.unlink(missing_ok=True)
            if status != "ok":
                break
            # 04/11 dona ("tem algo que faça o YouTube mostrar?"): o Short do corte liga ao longo pelo VÍDEO
            # RELACIONADO do Studio (o link clicável em cima do título do Short) — a ponte mais forte de Short pra longo
            # num canal pequeno. Antes era só o link na descrição. Falhou = o Short fica como está.
            # 05/11 (dona: "longos com 0 views"): ligar NA HORA falhava sempre — o longo ainda estava agendado e não
            # aparecia na lista do Studio. Agora vai pra fila de pontes (ligar_pontes), que só liga com o longo PÚBLICO.
            vs = str(info).rstrip("/").split("/")[-1].split("=")[-1]
            vl = str(item.get("url_longo", "")).rstrip("/").split("/")[-1].split("=")[-1]
            if vs and vl:
                est.setdefault("pontes", []).append({"canal": item["canal"], "short": vs, "longo": vl,
                                                     "titulo_longo": item.get("titulo", ""), "tentativas": 0,
                                                     "estado": "pendente"})
            feitos.add(chave)
            est["cortes_postados"] = sorted(feitos)
            dia[f"{hoje}|{item['canal']}"] = dia.get(f"{hoje}|{item['canal']}", 0) + 1
            n += 1
        if all(f"{item['nome']}/{c['arquivo']}" in feitos for c in cortes):
            pend.remove(item)
    est["cortes_pendentes"] = pend
    if not ver:
        _gravar_estado(est)


PONTE_MAX_TENTATIVAS = 6
PONTES_POR_RODADA = 6


def _publico(vid):
    import urllib.request
    try:
        urllib.request.urlopen(f"https://www.youtube.com/oembed?url=https://youtu.be/{vid}&format=json", timeout=15)
        return True
    except Exception:  # noqa: BLE001
        return False


def ligar_pontes(ver=False):
    """05/11 (dona: "longos com 0 views — faça todas as possíveis"): no Studio, o longo de 7 dias teve 13-14 impressões
    (CTR 7-14 %, 12 min de média). Os Shorts dos mesmos canais fazem milhares: a ponte Short -> longo (vídeo
    relacionado, o link em cima do título do Short) é o caminho do público. Liga cada corte ao seu longo só quando o
    longo está PÚBLICO; 'aviso' tenta de novo na rodada seguinte (até PONTE_MAX_TENTATIVAS); 'bloqueado' (canal sem
    recursos avançados / sem verificação por telefone) para — trava_conta/recursos_negados não deixa nem abrir."""
    est = _estado()
    pontes = est.get("pontes") or []
    feitas = 0
    for p in pontes:
        if p["estado"] != "pendente" or feitas >= PONTES_POR_RODADA:
            continue
        if not _publico(p["longo"]):
            continue
        if ver:
            log(f"pontes: ligaria {p['short']} -> {p['longo']}")
            continue
        feitas += 1
        try:
            args = ["--canal", p["canal"], f"--video={p['short']}", "--relacionado", p["longo"]]
            if p.get("titulo_longo"):
                args += ["--titulo-relacionado", p["titulo_longo"]]
            rr = subprocess.run([r"D:\manhwa-react\.venv\Scripts\python.exe",
                                 r"D:\postador-de-videos\bin\youtube_studio_extras.py", *args], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=1800,
                                cwd=r"D:\postador-de-videos\bin", creationflags=0x08000000)
            res = ([l for l in (rr.stdout + rr.stderr).splitlines() if "RESULTADO" in l] or ["sem resposta"])[-1]
        except Exception as e:  # noqa: BLE001
            res = f"erro {type(e).__name__}"
        p["tentativas"] += 1
        p["ultimo"] = res[:200]
        if re.search(r'"relacionado": "(ok|ja)', res):
            p["estado"] = "ligada"
        elif "bloqueado" in res or "TRAVADO" in res or p["tentativas"] >= PONTE_MAX_TENTATIVAS:
            p["estado"] = "desistiu"
        log(f"pontes: {p['short']} -> {p['longo']} [{p['estado']}, {p['tentativas']}ª]: {res[:150]}")
        est2 = _estado()  # grava já (rodada longa; outra parte do estado pode ter mudado)
        est2["pontes"] = pontes
        _gravar_estado(est2)


if __name__ == "__main__":
    # 29/10: postar_quando_pronto.py também chama a rodada — 2 ao mesmo tempo postariam o mesmo longo 2x
    import msvcrt
    # 11/11 dona ("quero a parte 11 online o mais rápido possível"): --so <id> = posta SÓ esse longo agora, sem esperar
    # a rodada em curso (que já tirou os longos dela da fila e só está nos cortes). Não roda cortes/pontes.
    if "--so" in sys.argv:
        alvo = sys.argv[sys.argv.index("--so") + 1]
        sys.argv += ["--primeiro", alvo]
        _fila_orig = _fila
        _fila = lambda est: [x for x in _fila_orig(est) if x[1].name.startswith(alvo)]  # noqa: E731
        os.environ["FIO_VIP_INTERVALO_H"] = "0"
        rodada()
        sys.exit(0)
    _trava = open(AQUI / "postar_longos.lock", "w")
    try:
        msvcrt.locking(_trava.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        log("outra rodada já está rodando — esta sai")
        sys.exit(0)
    try:
        rodada(ver="--ver" in sys.argv)
        postar_cortes(ver="--ver" in sys.argv)
        try:
            ligar_pontes(ver="--ver" in sys.argv)
        except Exception as e:  # noqa: BLE001 — ponte nunca derruba a postagem
            log(f"pontes: falhou ({type(e).__name__}: {str(e)[:150]})")
        if "--ver" not in sys.argv:  # 30/10 dona: sempre 1 longo recente no PC pra conferir (troca quando posta)
            try:
                import longo_para_conferir
                longo_para_conferir.atualizar()
            except Exception as e:  # noqa: BLE001 — conferência nunca derruba a postagem
                log(f"longo pra conferir não atualizou ({type(e).__name__}: {e})")
    except BaseException:  # 29/10: a tarefa roda por pythonw (sem console) — o erro sumia e a rodada morria calada
        import traceback
        log("RODADA MORREU:\n" + traceback.format_exc())
        raise
