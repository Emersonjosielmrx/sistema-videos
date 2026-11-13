"""anime_fetch.py — baixa o vídeo-fonte e sua transcrição.

Módulo isolado. Duas responsabilidades, ambas via yt-dlp:
  1. baixar o mp4 do vídeo.
  2. obter a transcrição — estratégia dupla:
       (a) legenda do YouTube (auto-caption, rápida; YT ainda traduz pra pt);
       (b) fallback Whisper (transcreve o áudio) — só se (a) falhar.

Retorna caminhos locais. NÃO reescreve o roteiro (isso é o anime_script).
O texto da legenda vem CRU (pode estar em qualquer língua) — traduzir/reescrever
é trabalho do anime_script via IA.
"""
import logging
import os
import sys
import re
import subprocess
from pathlib import Path

# O venv do recapd-e-animes é vazio (só pip+psutil).
# faster-whisper foi instalado no Python do SISTEMA (C:/Python313).
# Adiciona o site-packages do sistema no path pra poder importar.
if "faster_whisper" not in sys.modules:
    import site
    sys.path.append(r"C:\Users\Emerson-IA\AppData\Local\Programs\Python\Python313\Lib\site-packages")
    sys.path.extend(site.getsitepackages())

# MKL/OMP (backend do ctranslate2/faster-whisper) lê estas vars UMA VEZ, no load da
# lib. Precisam existir ANTES do 'from faster_whisper import ...' (que é lazy, dentro
# da função) — por isso ficam aqui no topo do módulo. Sem isso, o MKL abre arenas
# grandes por thread e estoura 'mkl_malloc: failed to allocate memory' mesmo com RAM
# sobrando (fragmentação de arena, não falta física).
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_DYNAMIC", "FALSE")
os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")
os.environ.setdefault("HF_HOME", r"D:\hipercool-materiais\models\huggingface")  # pasta COMUM de modelos (dono 17/10)


def download_video(url, out_dir, max_height=720):
    """Baixa o vídeo como mp4. Retorna Path do arquivo ou None.

    22/10: UM download só, no formato certo: em pé até 720 de largura (720x1280) se existir; senão o melhor até 720p
    de altura (fonte deitada). Antes baixava por largura e, se a fonte era deitada (25 de 55 fontes em 5 dias), o
    arquivo inteiro ia pro lixo e baixava de novo por altura — 2 downloads grandes pelo IP de casa (97bBeHddKJI:
    376 MB jogados fora + 918 MB), e volume de download é o que faz o YouTube barrar o IP.
    """
    import ytdlp_vez  # COMUM: 1 yt-dlp por vez no PC (rajada bloqueou o IP da casa)
    # 22/10 (dono: "não parar por nada"): fonte já baixada no ESTOQUE (bin\estoque_fontes.py) é usada direto —
    # a produção segue mesmo com o yt-dlp em pausa, sem tocar na rede.
    try:
        import estoque_fontes
        pronto = estoque_fontes.consumir_para(url, out_dir)
        if pronto:
            logging.info(f"[fetch] fonte veio do ESTOQUE (zero download): {pronto.name}")
            return pronto
    except Exception as e:  # noqa: BLE001 — estoque é atalho, nunca derruba o caminho normal
        logging.warning(f"[fetch] estoque indisponível ({type(e).__name__}: {e}) — baixando normal")
    # 23/10 (dona): fonte já usada vai pro Drive (hipercool-materiais\bin\fontes_drive.py); se a pasta pede de novo,
    # volta de lá (rápido, sem gastar o IP de casa) antes de ir ao YouTube
    try:
        if r"D:\hipercool-materiais\bin" not in sys.path:
            sys.path.append(r"D:\hipercool-materiais\bin")
        import fontes_drive
        do_drive = fontes_drive.trazer(out_dir)
        if do_drive:
            logging.info(f"[fetch] fonte voltou do DRIVE (zero download do YouTube): {do_drive.name}")
            return do_drive
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[fetch] Drive indisponível ({type(e).__name__}: {e}) — baixando normal")
    if os.environ.get("SEM_YTDLP") == "1":
        # 24/10: PC3 (desktop) — mesmo IP da casa e a vez do yt-dlp (ytdlp_vez) só existe no PC1: lá a fonte vem
        # baixada pelo PC1 (ocioso._prebaixar_remoto); sem ela, o Short não sai (nunca baixa no PC3)
        logging.error("[fetch] SEM_YTDLP=1 (PC3): fonte não veio do PC1 — não baixa aqui")
        return None
    falta = ytdlp_vez.pausado()
    espera = getattr(ytdlp_vez, "espera_download_s", lambda: 0)()
    # 03/11 (dona: "baixar no próprio Kaggle usando o IP dele"): o IP de casa levou 26 bloqueios/estouros hoje SEM entrar
    # em pausa ("Sign in to confirm you're not a bot", TimeoutExpired) — o Kaggle só era chamado com a pausa. Agora o
    # baixador do Kaggle vai PRIMEIRO sempre que está vivo; a casa é a reserva. KAGGLE_BAIXAR=pausa = só na pausa (antigo).
    # 03/11 20:55 teste real (J_0l755RUfU): o IP da sessão do Kaggle TAMBÉM levou "Sign in to confirm" — Kaggle primeiro
    # só atrasava. Padrão voltou a "pausa"; KAGGLE_BAIXAR=1 liga o Kaggle-primeiro quando o IP de lá estiver bom.
    # 04/11: o baixador roda em TODAS as sessões do Kaggle (linha_baixador do kaggle_trabalhador) e só sessão NÃO barrada
    # renova o vivo.json — vivo = algum IP do Kaggle baixando. Volta o Kaggle primeiro.
    _kb = os.environ.get("KAGGLE_BAIXAR", "1")
    if _kb != "0" and (_kb != "pausa" or falta or espera > 300):
        # 30/10 (dona, D43: "pode usar os IPs do Kaggle, assim não paramos mais por falta de IP"): IP de casa barrado
        # ou o espaçamento ia dormir > 5 min (30/10: ~4 h paradas) -> o baixador do Kaggle (outro IP, grátis) baixa
        # no mesmo formato e traz pelo Drive. Falhou/fora do ar = segue o caminho de sempre (proxy/espera).
        try:
            import re as _re
            import kaggle_baixar
            m = _re.search(r"(?:v=|shorts/|youtu\.be/)([\w-]{11})", str(url))
            if m and kaggle_baixar.vivo(5):
                logging.info(f"[fetch] IP {'em pausa' if falta else (f'esperaria {espera / 60:.0f} min' if espera > 300 else 'de casa poupado')}"
                             " — baixando pelo KAGGLE (outro IP)")
                v, _legs = kaggle_baixar.baixar(url, m.group(1), out_dir, log=logging.info)
                if v and v.exists():
                    alvo = Path(out_dir) / ("source" + v.suffix.lower())
                    if v != alvo:
                        v.replace(alvo)
                    return alvo
                logging.warning("[fetch] Kaggle não trouxe o vídeo — caminho de sempre")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[fetch] Kaggle indisponível ({type(e).__name__}: {e}) — caminho de sempre")
    px = None
    if falta:
        # 22/10 (dono: "se é IP, usa proxy"): IP de casa pausado -> download de EMERGÊNCIA pelo proxy rotativo,
        # com TETO de banda diário (a voz/TTS depende da mesma banda da Webshare). Sem proxy/banda = espera.
        px = ytdlp_vez.proxy_url()
        livre = _banda_proxy_livre()
        if not px or livre <= 0:
            logging.error(f"[fetch] yt-dlp em pausa (YouTube barrando o IP) por mais {falta / 60:.0f} min — "
                          f"não baixa agora ({'sem proxy' if not px else 'banda de proxy do dia esgotada'})")
            return None
        logging.warning(f"[fetch] IP em pausa ({falta / 60:.0f} min) — download de EMERGÊNCIA pelo proxy "
                        f"({livre:.0f} MB de banda livre hoje)")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_tmpl = str(out_dir / "source.%(ext)s")

    def _do_download(fmt_spec, proxy=None):
        # Cookies para evitar bloqueio anti-bot do YouTube (18/10/2026)
        cookies_path = Path(__file__).parent.parent / "cookies.txt"
        # 28/10 (dona aprovou): mesma resolução, mas H.264 em vez de AV1 — AV1 custa +46% de CPU na montagem
        cmd = ["yt-dlp", url, "-f", fmt_spec, "-S", "res,vcodec:h264",
               "--merge-output-format", "mp4", "-o", out_tmpl,
               "--no-warnings", "--no-playlist"]
        if cookies_path.exists():
            cmd.extend(["--cookies", str(cookies_path)])
        if proxy:
            cmd.extend(["--proxy", proxy])
        env = os.environ.copy()
        with ytdlp_vez.vez("anime: download"):
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800, env=env)
        for f in out_dir.glob("source.*"):
            if f.stem == "source" and f.suffix.lower() in (".mp4", ".mkv", ".webm"):  # 30/10: nunca o pedaço source.f396
                _banda_proxy_gastar(sum(x.stat().st_size for x in out_dir.glob("source.*")) / 1e6 if proxy else 0)
                return f
        return None

    # 1. Formato único (conferido 22/10 por consulta pelo proxy): aspect_ratio<0.9 = em pé (a régua do antigo
    #    _is_vertical); Short em pé -> 398+251 720x1280 (igual ao de antes); deitado -> 398+251 1280x720 direto.
    #    bv*+ba: o YT não tem mais mp4 combinado em 720p; --merge-output-format mp4 junta.
    fmt = (f"bv*[aspect_ratio<0.9][width<={max_height}]+ba/bv*[height<={max_height}]+ba/"
           f"b[height<={max_height}]/b")
    for rodada in (1, 2):  # com proxy: bloqueio troca o proxy e tenta 1x de novo (nunca alonga a pausa do IP)
        try:
            fpath = _do_download(fmt, px)
            if fpath:
                return fpath
            break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            motivo = _motivo_ytdlp(e)
            logging.warning(f"[fetch] download (formato único{' via proxy' if px else ''}) falhou: {motivo}")
            if ytdlp_vez.bloqueio(motivo):
                if px:
                    ytdlp_vez.proxy_ruim(px, motivo)
                    px = ytdlp_vez.proxy_url()
                    if rodada == 1 and px:
                        continue
                    return None
                ytdlp_vez.pausar(motivo)
                return None
            break

    # 2. Rede de segurança: o filtro por altura de antes (mais compatível)
    fmt_h = (
        f"bestvideo[height<={max_height}]+bestaudio/"
        f"best[height<={max_height}][ext=mp4]/"
        f"best[height<={max_height}]/worst[height>0]"
    )
    try:
        return _do_download(fmt_h, px)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        motivo = _motivo_ytdlp(e)
        logging.error(f"[fetch] download falhou: {motivo}")
        if ytdlp_vez.bloqueio(motivo):
            if px:
                ytdlp_vez.proxy_ruim(px, motivo)
            else:
                ytdlp_vez.pausar(motivo)
        return None


BANDA_PROXY = Path(r"D:\video-fila\ytdlp_proxy_banda.json")
PROXY_MB_DIA = float(os.environ.get("PROXY_DOWNLOAD_MB_DIA", "200"))


def _banda_proxy_livre():
    """MB que o download de emergência ainda pode gastar HOJE pelos proxies (a voz usa a mesma banda da Webshare)."""
    import json as _json
    import time as _time
    try:
        d = _json.loads(BANDA_PROXY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    if d.get("dia") != _time.strftime("%Y-%m-%d"):
        return PROXY_MB_DIA
    return max(0.0, PROXY_MB_DIA - float(d.get("mb", 0)))


def _banda_proxy_gastar(mb):
    if not mb or mb <= 0:
        return
    import json as _json
    import time as _time
    try:
        d = _json.loads(BANDA_PROXY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    hoje = _time.strftime("%Y-%m-%d")
    if d.get("dia") != hoje:
        d = {"dia": hoje, "mb": 0.0}
    d["mb"] = float(d.get("mb", 0)) + mb
    d["_leia"] = f"banda dos downloads de EMERGÊNCIA pelo proxy (teto {PROXY_MB_DIA:.0f} MB/dia; anime_fetch, 22/10)"
    try:
        BANDA_PROXY.write_text(_json.dumps(d), encoding="utf-8")
    except OSError:
        pass


def _motivo_ytdlp(e):
    """O porquê de verdade (fim do stderr do yt-dlp); o str() do erro só mostrava o comando."""
    err = getattr(e, "stderr", None) or getattr(e, "output", None) or ""
    if isinstance(err, bytes):
        err = err.decode("utf-8", "replace")
    linhas = [l.strip() for l in str(err).splitlines() if l.strip()]
    return " | ".join(linhas[-3:])[-400:] or f"{type(e).__name__} (sem stderr)"


def _parse_vtt(vtt_path):
    """Extrai só o texto de um .vtt (descarta timestamps, tags, duplicatas)."""
    lines = []
    seen_last = None
    for raw in Path(vtt_path).read_text(encoding="utf-8", errors="ignore").splitlines():
        s = raw.strip()
        if not s or s == "WEBVTT" or "-->" in s or s.isdigit():
            continue
        if s.startswith(("Kind:", "Language:", "NOTE")):
            continue
        s = re.sub(r"<[^>]+>", "", s)          # tags <c>, <00:00:00>
        s = re.sub(r"\[[^\]]*\]", "", s).strip()  # [Music], [Applause]
        if s and s != seen_last:               # auto-caption repete muito
            lines.append(s)
            seen_last = s
    return " ".join(lines).strip()


def _parse_vtt_tempos(vtt_path):
    """[[início_s, texto], ...] do .vtt, sem as repetições da legenda automática (que rola linha a linha). Dono 21/10:
    o narrador fala de um quadro específico — o roteiro curto usa esses tempos pra cada frase cair no momento certo."""
    def seg(t):
        h, m, s = (["0"] + t.split(":"))[-3:]
        return int(h) * 3600 + int(m) * 60 + float(s.replace(",", "."))
    cues, ini, vistos = [], None, set()
    for raw in Path(vtt_path).read_text(encoding="utf-8", errors="ignore").splitlines():
        s = raw.strip()
        if "-->" in s:
            try:
                ini = seg(s.split("-->")[0].strip())
            except ValueError:
                ini = None
            continue
        if not s or ini is None or s == "WEBVTT" or s.isdigit() or s.startswith(("Kind:", "Language:", "NOTE")):
            continue
        s = re.sub(r"\[[^\]]*\]", "", re.sub(r"<[^>]+>", "", s)).strip()
        if s and s not in vistos:
            vistos.add(s)
            cues.append([round(ini, 2), s])
    return cues


def fetch_captions(url, out_dir, langs=("pt", "es")):
    """Baixa auto-caption do YouTube (já traduzida pra langs, em ordem de preferência).

    Retorna (texto, lang) do primeiro idioma disponível, ou (None, None).
    21/10: eram 5 idiomas (pt, en, es, ko, ja), 1 pedido cada. Em 9 dias de log só pt (103) e es (7) deram legenda,
    e os 50 vídeos sem legenda gastavam 5 pedidos cada — o YouTube barra o IP da casa por volume de pedidos.
    Pedir pt e es juntos gerou 429 na legenda es (teste 21/10) → um idioma por vez, es só se o pt não vier.
    """
    import ytdlp_vez  # COMUM: 1 yt-dlp por vez no PC
    out_dir = Path(out_dir)

    def _achar():
        for lang in langs:
            for vtt in sorted(out_dir.glob(f"cap*.{lang}*.vtt")):  # cap.pt.vtt (agora) e cap_pt.pt.vtt (antes)
                txt = _parse_vtt(vtt)
                if len(txt) > 100:  # legenda utilizável (mín 100 chars; < 100 vai pro Whisper)
                    return txt, lang, vtt
        return None

    achado = _achar()  # já baixada numa rodada anterior (ou mandada pelo PC1): não pede de novo
    if not achado and os.environ.get("SEM_YTDLP") == "1":
        # 26/10: PC2/PC3 = mesmo IP da casa; a legenda vem do PC1 junto com a fonte, senão Whisper
        logging.info("[fetch] SEM_YTDLP=1: sem legenda do PC1 — vai pro Whisper")
        return None, None
    for lang in ([] if achado else langs):
        # 22/10 (dono: "falei pra usar o webshare"): a LEGENDA é pequena (KB) e sai por proxy rotativo — não
        # gasta o IP da casa. Bloqueio COM proxy = proxy ruim (troca e tenta 1x de novo), sem pausar o PC.
        proxy = ytdlp_vez.proxy_url()
        if not proxy:
            falta = ytdlp_vez.pausado()
            if falta:
                logging.warning(f"[fetch] yt-dlp em pausa (YouTube barrando o IP) por mais {falta / 60:.0f} min — sem legenda")
                return None, None
        for tentativa in (1, 2):
            cmd = [
                "yt-dlp", url, "--skip-download",
                "--write-auto-subs", "--sub-langs", lang,
                "--sub-format", "vtt", "-o", str(out_dir / "cap"),
                "--no-warnings", "--no-playlist",
            ] + (["--proxy", proxy] if proxy else [])
            try:
                with ytdlp_vez.vez("anime: legenda"):
                    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
                break
            except Exception as e:  # noqa: BLE001 — sem legenda do YT o Whisper transcreve
                motivo = _motivo_ytdlp(e)
                logging.warning(f"[fetch] legenda YT ({lang}) falhou: {motivo}")
                if ytdlp_vez.bloqueio(motivo) or "429" in motivo or "Too Many Requests" in motivo:
                    if proxy:
                        ytdlp_vez.proxy_ruim(proxy, motivo)
                        proxy = ytdlp_vez.proxy_url()
                        if tentativa == 1 and proxy:
                            continue
                    else:
                        ytdlp_vez.pausar(motivo)
                break
        achado = _achar()
        if achado:
            break
    if achado:
        txt, lang, vtt = achado
        logging.info(f"[fetch] legenda YT obtida (lang={lang}, {len(txt)} chars)")
        try:
            import json as _json
            cues = _parse_vtt_tempos(vtt)
            if cues:
                (out_dir / "legenda_tempos.json").write_text(_json.dumps(cues, ensure_ascii=False), encoding="utf-8")
        except Exception as e:  # noqa: BLE001 — sem tempos o Short espalha as frases pelo original
            logging.warning(f"[fetch] tempos da legenda falharam: {e}")
        return txt, lang
    logging.warning("[fetch] sem legenda YT utilizável")
    return None, None


def transcribe_whisper(video_path, model_size="tiny", max_seconds=1500):
    """Fallback: transcreve o áudio com faster-whisper via SUBPROCESS ISOLADO.

    Rodar em subprocesso separado evita o erro "mkl_malloc: failed to allocate memory"
    que ocorre quando o whisper carrega num processo já com memória fragmentada por
    outras libs (anime_script, etc.). Cada subprocesso é uma página em branco pro MKL.

    Retorna (texto, lang) ou (None, None).
    """
    # Qual Python do venv usar no subprocess.
    PY = sys.executable  # o mesmo python que roda anime_auto.py
    if not Path(PY).exists():
        for _py in (
            r"D:\recapd-ambientes\producao\venv\Scripts\python.exe",
            r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe",
            r"C:\Users\Emerson-IA\AppData\Local\Programs\Python\Python313\python.exe",
        ):
            if Path(_py).exists():
                PY = _py
                break

    wav = Path(video_path).with_suffix(".whisper.wav")

    # Verifica se o vídeo tem stream de áudio antes de tentar extrair
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_type", "-of", "default=noprint_wrappers=1:nokey=1",
             str(video_path)],
            capture_output=True, text=True, timeout=30,
        )
        if not probe.stdout.strip():
            logging.warning(f"[fetch] vídeo sem faixa de áudio: {Path(video_path).name} — Whisper pulado")
            return None, None
    except Exception as e:
        logging.warning(f"[fetch] ffprobe falhou ao verificar áudio: {e}")
        # Continua tentando extrair mesmo assim (pode ser erro transitório)

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-t", str(max_seconds), "-i", str(video_path),
             "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", str(wav)],
            check=True, capture_output=True, timeout=600,
        )
    except Exception as e:
        logging.error(f"[fetch] extração de áudio p/ Whisper falhou: {e}")
        return None, None

    whisper_script = Path(__file__).parent / "_whisper_sub.py"
    # Timeout dinâmico progressivo (11/11: vídeos de 2-3min davam timeout em 600s quando CPU carregada levava 1500s+)
    # Vídeos curtos (até 10 min): 5x a duração, mínimo 900s (15 min)
    # Vídeos médios (10-25 min): 2.5x a duração
    # Vídeos longos (>25 min): 1.5x a duração, máximo 7200s (2h)
    if max_seconds <= 600:
        whisper_timeout = max(900, int(max_seconds * 5))
    elif max_seconds <= 1500:
        whisper_timeout = int(max_seconds * 2.5)
    else:
        whisper_timeout = min(7200, int(max_seconds * 1.5))
    # Tenta apenas "tiny" para minimizar risco de MemoryError
    for msize in ("tiny",):
        try:
            env = dict(os.environ,
                MKL_NUM_THREADS="1", OMP_NUM_THREADS="1",
                PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
            )
            result = subprocess.run(
                [PY, str(whisper_script), str(wav), msize],
                capture_output=True, text=True, timeout=whisper_timeout,
                encoding="utf-8", errors="replace",
                env=env,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().splitlines()
                if len(lines) >= 2:
                    txt = lines[0].strip()
                    lang = lines[1].strip()
                    if len(txt) > 50:
                        logging.info(f"[fetch] Whisper transcreveu (model={msize}, lang={lang}, {len(txt)} chars)")
                        _cleanup_wav(wav, video_path)
                        return txt, lang
                    logging.warning(f"[fetch] Whisper (model={msize}) texto curto demais ({len(txt)} chars)")
                else:
                    logging.warning(f"[fetch] Whisper (model={msize}) output inesperado: {result.stdout[:100]!r}")
            else:
                logging.error(f"[fetch] Whisper (model={msize}) rc={result.returncode}: {(result.stderr or '')[-800:]}")  # 30/10: o fim tem o erro real (o começo era só aviso)
        except Exception as e:
            logging.error(f"[fetch] Whisper (model={msize}) exception: {e}")

    _cleanup_wav(wav, video_path)
    return None, None


def _cleanup_wav(wav, video_path):
    try:
        if Path(wav) != Path(video_path):
            Path(wav).unlink(missing_ok=True)
    except Exception:
        pass


def get_transcript(url, video_path, out_dir):
    """Transcrição com estratégia dupla: legenda YT primeiro, Whisper como fallback.

    Retorna (texto, lang) — texto CRU (língua original/traduzida), pra reescrita depois.
    """
    txt, lang = fetch_captions(url, out_dir)
    if txt:
        return txt, lang
    logging.info("[fetch] tentando fallback Whisper...")
    return transcribe_whisper(video_path)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    url = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("_fetch_test")
    txt, lang = fetch_captions(url, out)
    print(f"lang={lang} chars={len(txt or '')}")
    if txt:
        print(txt[:500])
