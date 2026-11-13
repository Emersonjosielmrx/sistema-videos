"""anime_auto.py — modo AUTÔNOMO: acha, baixa, roteiriza e renderiza sozinho.

No V2, separa os fluxos em '--modo deitado' e '--modo short', já que buscam fontes
diferentes: recaps longos vs shorts nativos do YouTube.
"""
import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import shutil
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import anime_discover
import anime_fetch
import anime_script
import anime_probe
import anime_metrics
import anime_worker_client
import anime_voz_clonada
import anime_testes
import claude_fallback as claude_client  # usa gemini quando OMNIROUTE_BYPASS=1

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE = Path(__file__).resolve().parent.parent / "workspace" / "anime"
PIPELINE = Path(__file__).resolve().parent / "anime-pipeline.py"


def _feitos_path(prefix=""):
    """Arquivo de feitos, separado por modalidade (prefixo)."""
    if prefix:
        return BASE / f"_feitos_{prefix}.txt"
    return BASE / "_feitos.txt"


def _ja_feitos(prefix=""):
    """Retorna o set de IDs já processados."""
    fpath = _feitos_path(prefix)
    if fpath.exists():
        return set(fpath.read_text(encoding="utf-8").split())
    return set()


def _marca_feito(vid, prefix=""):
    """Registra um ID de vídeo como já feito."""
    fpath = _feitos_path(prefix)
    fpath.parent.mkdir(parents=True, exist_ok=True)
    with open(fpath, "a", encoding="utf-8") as f:
        f.write(vid + "\n")


def _cands_do_estoque(fonte_url, ja):
    """Candidatos do ESTOQUE de fontes já baixadas (workspace\\anime\\_estoque\\<id>\\meta.json), no formato do
    discover_canal: 1º os da MESMA fonte do parceiro pedida, depois os do mesmo TIPO de conteúdo (manhwa = anime,
    como no rodízio do parceiro_diario) — a narração (PARCEIRO_TIPO) tem que combinar com o vídeo."""
    try:
        cfg = json.loads((BASE.parent.parent / "config" / "parceiro.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    fontes = {f["nome"]: f for f in cfg.get("fontes") or [] if f.get("nome") and f.get("url")}
    pedida = next((f for f in fontes.values() if f["url"].rstrip("/") == str(fonte_url).rstrip("/")), None)
    grupo = {"manhwa": "anime"}
    tipo = grupo.get((pedida or {}).get("tipo"), (pedida or {}).get("tipo"))
    out = []
    for meta in sorted((BASE / "_estoque").glob("*/meta.json")):
        try:
            m = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        f = fontes.get(m.get("fonte"))
        if not f or m.get("id") in ja or not list(meta.parent.glob("source.*")):
            continue
        mesma = bool(pedida) and f["nome"] == pedida["nome"]
        if not mesma and grupo.get(f.get("tipo"), f.get("tipo")) != tipo:
            continue
        out.append({"id": m["id"], "title": m.get("title") or m["id"], "url": m.get("url"),
                    "views": m.get("views") or 0, "duration": m.get("duration") or 0, "parte": 0,
                    "parceiro": f["url"], "estoque": True, "fonte_estoque": f["nome"], "_mesma": mesma})
    out.sort(key=lambda c: (not c["_mesma"], -c["views"]))
    return out


def _slug(s):
    """Transforma um título em nome de pasta seguro."""
    return "".join(c if c.isalnum() else "_" for c in s)[:40].strip("_")


import re as _re

_NOME_CACHE = {}


def _nome_neutro(titulo_yt):
    """Título sem obra (curiosidade, futebol...): nome neutro e único, nunca palavra do título/assunto — o SEO derruba
    título/tag que contenha o nome da obra (seo_generator._sem_obra; 21/10 "Dorama" deixou o Short com 1 tag só)."""
    return "sem-obra-" + hashlib.md5(titulo_yt.encode("utf-8")).hexdigest()[:6]


def _extrair_nome_anime(titulo_yt):
    """Extrai só o nome curto do anime de um título longo do YouTube.
    Ex: 'The ENTIRE Story of Berserk in 110 Minutes' -> 'Berserk'
    Usa LLM com fallback heurístico."""
    if titulo_yt in _NOME_CACHE:
        return _NOME_CACHE[titulo_yt]

    # Tenta via LLM (rápido, eco)
    if claude_client.is_available():
        try:
            resp = claude_client.generate_text(
                f"Extraia APENAS o nome do anime/manhwa/dorama/filme/série citado neste título de YouTube. "
                f"Retorne SÓ o nome (1-4 palavras, sem explicação). Se o título não citar obra nenhuma, "
                f"responda só: NENHUM\n"
                f"Título: {titulo_yt}",
                max_tokens=30, temperature=0.0)
            # 21/10: veio "/workspace\nMy granddaughter..." (caminho antes da resposta) e virou a obra inteira
            linhas = [l.strip().strip('"').strip("'") for l in (resp or "").splitlines()]
            linhas = [l for l in linhas if l and not _re.match(r"[/\\]|[A-Za-z]:[/\\]", l)]
            if linhas and 2 <= len(linhas[0]) <= 60:
                nome = linhas[0]
                low = nome.lower()
                if (_re.search(r"\b(nenhum\w*|n[ãa]o|none|unknown|desconhecid\w*|sorry|desculpe|no (anime|manhwa))\b"
                               r"|n/a|encontrad|not found", low)
                        or _re.fullmatch(r"anime|manhwa|mang[aá]|webtoon|k-?drama|doramas?|drama|filmes?|film|movie"
                                         r"|s[ée]ries?", low)):
                    nome = _nome_neutro(titulo_yt)
                _NOME_CACHE[titulo_yt] = nome
                logging.info(f"[auto] nome extraído via LLM: '{titulo_yt[:50]}' -> '{nome}'")
                return nome
        except Exception as e:
            logging.warning(f"[auto] LLM extração falhou: {e}")

    # Fallback heurístico: remove padrões comuns de títulos recap
    t = titulo_yt
    # Remove prefixos/sufixos comuns
    for pat in [r"(?i)\bthe\s+entire\s+story\s+of\s+", r"(?i)\bcomplete\s+story\s+of\s+",
                r"(?i)\bfull\s+story\s+of\s+", r"(?i)\banime\s+recap\s*",
                r"(?i)\brecap\s+completo\s*", r"(?i)\bresumo\s+completo\s*",
                r"(?i)\bin\s+\d+\s+minutes?\s*$", r"(?i)\|\s*anime\s+recap.*$",
                r"(?i)\|\s*all\s+details.*$", r"(?i)\|\s*todos\s+os\s+detalhes.*$",
                r"(?i)\[AMV\].*$", r"(?i)\(AMV\).*$",
                r"(?i)\bep(isode)?\s*\d+.*$", r"(?i)\bcap[ií]tulo\s*\d+.*$",
                r"(?i)\bseason\s*\d+.*$", r"(?i)\btemporada\s*\d+.*$",
                r"\s*[|\-–—]\s*$", r"^\s*[|\-–—]\s*"]:
        t = _re.sub(pat, "", t).strip()
    # Se sobrou algo razoável (2-40 chars), usa
    if 2 <= len(t) <= 40:
        _NOME_CACHE[titulo_yt] = t
        logging.info(f"[auto] nome extraído heurístico: '{titulo_yt[:50]}' -> '{t}'")
        return t
    # Último recurso: título longo sem padrão de recap não é nome de obra (as 3 primeiras palavras viravam nome
    # proibido no SEO: 'marca que MAIS', 'This job will')
    nome = _nome_neutro(titulo_yt)
    _NOME_CACHE[titulo_yt] = nome
    logging.info(f"[auto] nome extraído fallback: '{titulo_yt[:50]}' -> '{nome}'")
    return nome


def _cleanup_workspace(work_dir, manter=()):
    """Apaga os arquivos intermediários, deixando só o vídeo final e o roteiro (+ `manter`)."""
    keep_files = ["final_anime_deitado.mp4", "final_anime_deitado_ads.mp4",
                  "final_anime_short.mp4", "roteiro.txt", "_testes_usados.json", *manter]
    logging.info(f"[auto|cleanup] Limpando arquivos temporários em {work_dir}...")

    for item in work_dir.iterdir():
        if item.name in keep_files:
            continue

        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as e:
            logging.warning(f"[auto|cleanup] Erro ao apagar {item.name}: {e}")

    logging.info("[auto|cleanup] Limpeza concluída.")


# 23/10: DISJUNTOR da legenda do YouTube. Desde 22/10 ~13:00 toda legenda pelo proxy volta "not a bot"/429 (0 de 10 em
# 23/10; 64 em 20/10): cada Short esperava a vez do yt-dlp pra 2 pedidos à toa (mediana ~4 min até desistir) e cada
# "not a bot" tirava um proxy da roda por 1 h (os mesmos do download de emergência). LEGENDA_FALHAS_ABRE falhas seguidas
# = direto pro Whisper (que também dá roteiro com tempo); 1 teste a cada LEGENDA_TESTE_H pra perceber quando voltar.
LEGENDA_DISJUNTOR = Path(__file__).resolve().parent.parent / "logs" / "legenda_disjuntor.json"
LEGENDA_FALHAS_ABRE = 6
LEGENDA_TESTE_H = 2


def _legenda_yt(cand, work):
    try:
        est = json.loads(LEGENDA_DISJUNTOR.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {}
    agora = time.time()
    ja_baixada = any(Path(work).glob("cap*.vtt"))  # rodada anterior: o fetch_captions só relê, sem pedido novo
    if not ja_baixada and est.get("falhas", 0) >= LEGENDA_FALHAS_ABRE \
            and agora - est.get("ultimo_teste", 0) < LEGENDA_TESTE_H * 3600:
        logging.info(f"[auto] legenda do YouTube pulada ({est['falhas']} falhas seguidas; testa de novo a cada "
                     f"{LEGENDA_TESTE_H} h) — vai pro Whisper")
        return None, None
    txt, lang = anime_fetch.fetch_captions(cand["url"], work)
    if not ja_baixada:
        try:
            novo = {"falhas": 0 if txt else est.get("falhas", 0) + 1, "ultimo_teste": agora,
                    "ultimo_ok": agora if txt else est.get("ultimo_ok"),
                    "quando": time.strftime("%Y-%m-%d %H:%M")}
            LEGENDA_DISJUNTOR.parent.mkdir(parents=True, exist_ok=True)
            tmp = LEGENDA_DISJUNTOR.with_name(LEGENDA_DISJUNTOR.name + ".tmp")
            tmp.write_text(json.dumps(novo, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, LEGENDA_DISJUNTOR)
            if txt and est.get("falhas", 0) >= LEGENDA_FALHAS_ABRE:
                logging.info("[auto] legenda do YouTube VOLTOU — disjuntor fechado")
        except OSError:
            pass
    return txt, lang


def _prepara_candidato(cand, sem_whisper=False):
    """Baixa o vídeo e tenta extrair transcrição (YT legenda ou Whisper). sem_whisper=True: sem legenda do YT devolve
    txt="" (quem transcreve é o PC2)."""
    vid = cand["id"]
    work = BASE / f"{vid}_{_slug(cand['title'])}"
    work.mkdir(parents=True, exist_ok=True)
    logging.info(f"===== {cand['title'][:60]} ({cand['views']:,} views) =====")

    # 1. transcrição preliminar
    txt, lang = _legenda_yt(cand, work)
    # 03/11: Shorts EXTRAS do Kaggle (abastecedor_kaggle) morriam no Whisper do PC1 lotado (600 s, 5x em 1 h) depois
    # de gastar 1 download do IP de casa. Sem legenda do YouTube = pula ANTES de baixar.
    # 04/11 dona ("os PCs fazem um atrás do outro e as GPUs pegam também, ninguém espera"): com a legenda do YT barrada
    # pelo IP de casa (429) TODO extra era pulado e o Kaggle ficou parado o dia todo. Fonte CURTA (<= 120 s) segue:
    # o Whisper tiny leva 20-60 s (medido 04/11; o estouro de 03/11 era a CPU em 100% do banco_mulheres, já contido).
    try:
        _dur_fonte = float(cand.get("duration") or 0)
    except (TypeError, ValueError):
        _dur_fonte = 0.0
    # 19:20: os extras chegam SEM duração (0) — Short de parceiro (página /shorts, marca "parceiro") é curto por definição
    _curta = 0 < _dur_fonte <= 120 or (not _dur_fonte and (cand.get("parceiro") or "/shorts" in str(cand.get("url"))))
    if not txt and os.environ.get("SHORTS_SEM_WHISPER") == "1" and not _curta:
        logging.info("[auto] sem legenda do YT e SHORTS_SEM_WHISPER=1 — pulo (sem whisper no PC1, sem download)")
        # 03/11: o pulo não pode queimar a fonte — 11 vídeos ficaram "tentados" e os PCs (com whisper) nunca mais os pegavam
        try:
            p = _feitos_path("short_attempted")
            linhas = p.read_text(encoding="utf-8").split("\n")
            p.write_text("\n".join(x for x in linhas if x.strip() != vid), encoding="utf-8")
        except OSError:
            pass
        return None, None, None

    # 2. baixar vídeo (reutiliza se já existe — PC1 pode enviar antes de disparar no PC2)
    # 30/10: "source.*" pegava o pedaço parcial do yt-dlp (source.f396.mp4, só vídeo, sem áudio) = 4 falhas repetidas.
    # Só vale o arquivo final; os pedaços de um download interrompido são apagados (o yt-dlp baixa de novo).
    for parcial in work.glob("source.f*"):
        parcial.unlink(missing_ok=True)
    existente = next((f for f in work.glob("source.*") if f.stem == "source"
                      and f.suffix.lower() in (".mp4", ".mkv", ".webm")), None)
    if existente:
        logging.info(f"[auto] vídeo-fonte já existe: {existente.name}")
        video = existente
    else:
        logging.info("[auto] baixando vídeo-fonte...")
        video = anime_fetch.download_video(cand["url"], work)
        if not video:
            logging.error("[auto] download falhou")
            return None, None, None

    cand["_lang"] = lang  # o payload do worker manda o idioma (antes usava um "lang" que não existia lá: NameError)
    if not txt and sem_whisper:
        # 26/10: o Whisper do longo no PC1 estourava 47 min (PC1 sobrecarregado) e o anime nem chegava ao PC2
        logging.info("[auto] sem legenda do YT — o Whisper fica pro PC2 (worker)")
        return work, video, ""
    # Fallback se não veio legenda do YT
    if not txt:
        # 25/10: sem max_seconds o Whisper parava nos 25 min — o recap LONGO saía feito só com o começo do original
        txt, lang = anime_fetch.transcribe_whisper(video, max_seconds=int(anime_probe.video_duration(str(video)) or 1440) + 60)
        # 23/10: o _whisper_sub grava os tempos ao lado do wav; viram o legenda_tempos.json (roteiro com tempo = a fala
        # cai no quadro que ela descreve). Em 22/10 os 11 Shorts feitos pelo Whisper saíram SEM tempo.
        lado = Path(str(Path(video).with_suffix(".whisper.wav")) + ".tempos.json")
        try:
            if txt and lado.exists() and not (work / "legenda_tempos.json").exists():
                if len(json.loads(lado.read_text(encoding="utf-8"))) >= 3:
                    lado.replace(work / "legenda_tempos.json")
                    logging.info("[fetch] tempos do Whisper viraram legenda_tempos.json (roteiro com tempo)")
        except (OSError, ValueError) as e:
            logging.warning(f"[fetch] tempos do Whisper não serviram ({e})")
    if not txt:
        logging.error("[auto] sem transcrição disponível")
        return None, None, None
    cand["_lang"] = lang
    return work, video, txt


DRIVE_ANIME = "manhwa-drive:videos-backup/anime/1_youtube_pendente"
R_RCLONE = r"C:\recapd-e-animes\tools\rclone.exe --config C:\recapd-e-animes\secrets\rclone.conf"


def _deitado_pro_drive(cand, work, remoto, remote_wd, host, port, orig_dur, n):
    """PC2 -> Drive (rclone lá), confere, apaga no PC2 e grava a ficha aqui. True/False."""
    import json as _json
    nome = f"{cand['id']}_{_slug(cand['title'])}"
    destino = f"{DRIVE_ANIME}/{nome}/video.mp4"
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "pc2", f'{R_RCLONE} copyto "{remoto}" "{destino}"'],
                       capture_output=True, text=True, timeout=4 * 3600)
    chk = subprocess.run(["ssh", "-o", "BatchMode=yes", "pc2", f'{R_RCLONE} lsl "{destino}"'],
                         capture_output=True, text=True, timeout=300)
    if r.returncode != 0 or "video.mp4" not in (chk.stdout or ""):
        logging.error(f"[auto|deitado] FALHA ao subir do PC2 pro Drive — NÃO apago lá: {(r.stderr or '')[-300:]}")
        anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA", "upload Drive falhou",
                                 orig_dur=orig_dur, lines=n)
        return False
    logging.info(f"[auto|deitado] no Drive: {destino} | cleanup PC2: "
                 f"{anime_worker_client.limpar(host, port, remote_wd)}")
    ficha = ANIMES_FICHAS / nome
    ficha.mkdir(parents=True, exist_ok=True)
    rot = work / "roteiro.txt"
    if rot.exists():
        shutil.copy2(rot, ficha / "roteiro.txt")
    (ficha / "nuvem.json").write_text(_json.dumps(
        {"drive": destino, "titulo_original": cand.get("title"), "source_url": cand.get("url"), "formato": "deitado",
         "anime": _extrair_nome_anime(cand["title"]), "feito_em": time.strftime("%Y-%m-%d %H:%M"),
         "postar": "sem canal ainda (dono vai criar o de anime): baixar do Drive, rodar anime_publish e postar"},
        ensure_ascii=False, indent=2), encoding="utf-8")
    _marca_feito(cand["id"], "deitado")
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    anime_metrics.record_job(cand["id"], cand["title"], "deitado", "SUCESSO", orig_dur=orig_dur, lines=n)
    return True


ANIMES_FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")


def fazer_deitado(cand, target_lines, dry_run, use_worker=False,
                  worker_host="100.125.7.77", worker_port=8772):
    """Fluxo para recap longo (deitado 16:9)."""
    _marca_feito(cand["id"], "deitado_attempted")

    work, video, txt = _prepara_candidato(cand, sem_whisper=use_worker and not dry_run)
    if not work:
        if work and work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA", "Baixar ou Transcrição falhou")
        return False
    pc2_transcreve = use_worker and not txt  # 26/10: sem legenda do YT, o PC2 faz Whisper + roteiro (tira peso do PC1)

    orig_dur = anime_probe.video_duration(str(video))

    # target_lines dinâmico: cada linha ≈ 3s de narração TTS. Pra o recap deitado
    # sair proporcional ao original (nem curto demais, nem infinito), miramos ~55%
    # da duração do original em narração. Ex.: original 30min -> ~16min de recap ->
    # ~330 linhas. Piso de 120 (nunca menos que ~6min) e teto de 600 (~30min) pra
    # não estourar custo de LLM/TTS/render. O --target-lines vira só um piso mínimo.
    if orig_dur and orig_dur > 0:
        dyn = int((orig_dur * 0.55) / 3.0)
        target_lines = max(target_lines, min(600, max(120, dyn)))
        logging.info(f"[auto|deitado] original {orig_dur:.0f}s -> target_lines={target_lines} (dinâmico)")

    roteiro = work / "roteiro.txt"
    n = 0
    (work / "roteiro_tempos.json").unlink(missing_ok=True)
    if (work / "legenda_tempos.json").exists():  # dona 25/10: o longo também narra o que está na tela (igual ao Short)
        try:
            frases, tempos = anime_script.rewrite_longo_com_tempo(
                json.loads((work / "legenda_tempos.json").read_text(encoding="utf-8")), target_lines, orig_dur)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[auto|deitado] roteiro com tempo falhou ({type(e).__name__}: {e}) — roteiro normal")
            frases, tempos = [], []
        if frases:
            roteiro.write_text("\n".join(frases) + "\n", encoding="utf-8")
            (work / "roteiro_tempos.json").write_text(json.dumps(tempos), encoding="utf-8")
            n = len(frases)
    if n == 0 and not pc2_transcreve:
        n = anime_script.rewrite_to_file(txt, roteiro, target_lines=target_lines)
    if n == 0 and not pc2_transcreve:
        if work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA", "Roteirização falhou/Recusa IA", orig_dur=orig_dur)
        return False
    logging.info(f"[auto|deitado] roteiro longo: {n} frases"
                 f"{' com tempo' if (work / 'roteiro_tempos.json').exists() else ''}"
                 + (" — transcrição e roteiro ficam pro PC2" if pc2_transcreve else ""))

    if dry_run:
        logging.info("[auto] DRY-RUN — parou antes de renderizar")
        return True

    if use_worker:
        logging.info(f"[auto|deitado] DESPACHANDO pro worker {worker_host}:{worker_port}...")
        # 26/10: o PC2 baixava a fonte de novo pelo IP da casa, fora da vez do yt-dlp (o autoloop dele bloqueou o IP):
        # a fonte que o PC1 já baixou vai junto e o daemon pula o download (source.mp4 na pasta dele)
        r_wd = ""
        if video and Path(video).exists():
            r_dir = f"C:/recapd-e-animes/workspace/anime/{cand['id']}"
            try:
                subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "pc2", f'mkdir "{r_dir}"'],
                               capture_output=True, timeout=60)
                cp = subprocess.run(["scp", "-q", "-o", "BatchMode=yes", str(video), f"pc2:{r_dir}/source.mp4"],
                                    capture_output=True, timeout=1800)
                if cp.returncode == 0:
                    r_wd = r_dir
                    logging.info(f"[auto|deitado] fonte enviada pro PC2 ({Path(video).stat().st_size // 1048576} MB)")
                else:
                    logging.warning(f"[auto|deitado] envio da fonte falhou ({(cp.stderr or b'')[:150]!r}) — o PC2 baixa")
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[auto|deitado] envio da fonte falhou ({type(e).__name__}: {e}) — o PC2 baixa")
        payload = {
            "video_url": cand["url"],
            "titulo": cand["title"],
            "modo": "deitado",
            # 19/10: o caminho do PC1 (D:\...) não existe lá; vazio = o PC2 cria a pasta dele
            "work_dir": r_wd,
            "target_lines": target_lines,
            # 25/10: PC1 envia transcrição/roteiro pro PC2 (PC2 não tem Whisper funcionando)
            "transcript_txt": txt if txt else "",
            "transcript_lang": cand.get("_lang") or "en",
            "roteiro_txt": roteiro.read_text(encoding="utf-8") if roteiro.exists() else "",
        }
        # Se tiver legenda_tempos.json, envia também (roteiro com tempo)
        legenda_tempos_path = work / "legenda_tempos.json"
        if legenda_tempos_path.exists():
            payload["legenda_tempos_json"] = legenda_tempos_path.read_text(encoding="utf-8")
        result = anime_worker_client.run_anime(worker_host, worker_port, payload, timeout=14400)
        if not result or not result.get("ok"):
            err = result.get("error", "desconhecido") if result else "sem resposta"
            logging.error(f"[auto|deitado] Worker falhou: {err}")
            anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA",
                                   f"Worker error: {err}", orig_dur=orig_dur, lines=n)
            if work.exists(): shutil.rmtree(work)
            return False
        logging.info(f"[auto|deitado] Worker OK: {result.get('video_path', '')}")
        # PC2 e SO worker: TRANSFERE o video pro PC1 e depois APAGA do PC2.
        # (antes: usava o path do PC2 direto -> vf.exists()=False no PC1 e o
        #  arquivo ficava guardado la ate o disco zerar. Fix da causa raiz.)
        remoto = result.get("video_path", "")
        remote_wd = result.get("work_dir", str(work))
        vf = work / "final_anime_deitado.mp4"
        if os.environ.get("ANIME_DESTINO") == "drive":
            # modo ocioso (dono 17/10): o PC2 sobe o vídeo pronto DIRETO pro Google Drive e apaga o dele; aqui fica só
            # a ficha (nuvem.json). Nada de vídeo grande no disco deste PC. Postar = baixar do Drive na hora.
            return _deitado_pro_drive(cand, work, remoto, remote_wd, worker_host, worker_port, orig_dur, n)
        if anime_worker_client.baixar(worker_host, worker_port, remoto, vf):
            logging.info(f"[auto|deitado] baixado pro PC1: {vf}")
            r_clean = anime_worker_client.limpar(worker_host, worker_port, remote_wd)
            logging.info(f"[auto|deitado] cleanup PC2: {r_clean}")
        else:
            logging.error("[auto|deitado] FALHA ao baixar do PC2 — NAO apago "
                          "de la (pra nao perder o video). Verifique espaco/rede.")
            anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA",
                                     "download do worker falhou", orig_dur=orig_dur, lines=n)
            return False
    else:
        cmd = [sys.executable, str(PIPELINE),
               "--video-source", str(video), "--script", str(roteiro),
               "--titulo", cand["title"], "--formato", "deitado"]
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        r = subprocess.run(cmd, env=env)
        if r.returncode != 0:
            logging.error(f"[auto|deitado] pipeline falhou (rc={r.returncode})")
            anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA",
                                   f"Pipeline rc={r.returncode}", orig_dur=orig_dur, lines=n)
            return False
        vf = work / "final_anime_deitado.mp4"

    _marca_feito(cand["id"], "deitado")

    # PROPAGANDA MID-ROLL: insere blocos (clipe Veo + card) em varios momentos
    # do recap. Codigo em d:\hipercool-videos\propaganda_lateral (nao edita
    # veo/beta; reusa contas). Tolerante a falha: se der erro, mantem o video.
    if vf.exists() and os.environ.get("ANIME_MIDROLL", "1") == "1":
        try:
            sys.path.insert(0, r"D:\hipercool-videos\propaganda_lateral")
            import inserir_midroll
            interval = float(os.environ.get("ANIME_MIDROLL_MIN", "20"))
            com_ads = work / "final_anime_deitado_ads.mp4"
            if inserir_midroll.inserir(str(vf), str(com_ads), intervalo_min=interval):
                vf = com_ads
                logging.info(f"[auto|deitado] mid-roll inserido: {vf}")
        except Exception as e:
            logging.warning(f"[auto|deitado] mid-roll pulado: {str(e)[:120]}")

    # Coleta metricas finais de SUCESSO antes de limpar
    af_dur, vf_dur = 0.0, 0.0
    if vf.exists():
        vf_dur = anime_probe.video_duration(str(vf))
        try:
           import json
           out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "json", str(vf)], capture_output=True, text=True).stdout
           d = json.loads(out)
           for s in d.get("streams",[]):
               if s.get("codec_type") == "audio": af_dur = float(s.get("duration", 0))
        except: pass

    _cleanup_workspace(work)

    # Gera postar.json + metadata viral automaticamente
    if vf.exists():
        try:
            pub_cmd = [sys.executable, str(PIPELINE.parent / "anime_publish.py"),
                       "--video", str(vf),
                       "--anime", _extrair_nome_anime(cand["title"]),
                       "--cap", "1",
                       "--formato", "deitado",
                       "--source-url", cand.get("url", ""),
                       "--titulo-original", cand.get("title", ""),
                       "--roteiro", str(work / "roteiro.txt")]
            if not use_worker:  # no PC2 a voz é escolhida lá
                import anime_tts
                pub_cmd += ["--narrador", os.environ.get("ANIME_TTS_VOICE") or anime_tts.NARRATOR_VOICE]
            env_pub = dict(os.environ, PYTHONUTF8="1")
            # 900 s: SEO pelo LLM + capa IA com checagem por visão (até 3 imagens) — 120 s matava no meio
            rp = subprocess.run(pub_cmd, env=env_pub, timeout=4800)  # 4800: inclui a análise do vídeo pronto (anime_revisao, 16/10)
            if rp.returncode == 0:
                logging.info("[auto|deitado] publish OK — postar.json gerado")
            else:
                logging.warning(f"[auto|deitado] publish falhou (rc={rp.returncode}) — vídeo mantido sem metadata")
        except Exception as e:
            logging.warning(f"[auto|deitado] publish erro: {e}")

    # Deriva short 9:16 do deitado (primeiro segmento de ~55s)
    short_out = work / "final_anime_short.mp4"
    if vf.exists() and not short_out.exists() and os.environ.get("ANIME_AUTO_SHORT", "1") == "1":
        try:
            short_cmd = [sys.executable, str(PIPELINE.parent / "shorts_from_deitado.py"),
                         "--video", str(vf), "--first-only"]
            env_s = dict(os.environ, PYTHONUTF8="1")
            rs = subprocess.run(short_cmd, env=env_s, timeout=600)
            if rs.returncode == 0 and short_out.exists():
                logging.info(f"[auto|deitado] short derivado OK: {short_out}")
                # Publish do short também
                try:
                    pub_s = [sys.executable, str(PIPELINE.parent / "anime_publish.py"),
                             "--video", str(short_out),
                             "--anime", _extrair_nome_anime(cand["title"]),
                             "--cap", "1",
                             "--formato", "short",
                             "--source-url", cand.get("url", ""),
                             "--titulo-original", cand.get("title", ""),
                       "--roteiro", str(work / "roteiro.txt")]
                    subprocess.run(pub_s, env=env_s, timeout=4800)
                except Exception:
                    pass
            else:
                logging.warning(f"[auto|deitado] short derivado falhou (rc={rs.returncode})")
        except Exception as e:
            logging.warning(f"[auto|deitado] short derivado erro: {e}")

    logging.info(f"[auto|deitado] PRONTO: {work}")
    anime_metrics.record_job(cand["id"], cand["title"], "deitado", "SUCESSO", orig_dur=orig_dur, lines=n, final_v=vf_dur, final_a=af_dur)
    return True


HANDLE_PARCEIRO = os.environ.get("PARCEIRO_HANDLE", "@manhwanoturno")  # pt sai no Manhwa Noturno até o canal novo


def _fonte_cfg(url):
    """Entrada de config/parceiro.json "fontes" desta URL de canal ({} se não achar)."""
    try:
        import json as _j
        c = _j.loads((Path(__file__).resolve().parent.parent / "config" / "parceiro.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    alvo = (url or "").rstrip("/").lower()
    return next((f for f in c.get("fontes") or [] if f.get("url", "").rstrip("/").lower() == alvo), {})


def _reeditar_parceiro(video, handle=None, titulo_original="", narracao="", fonte_url=""):
    """Short de canal PARCEIRO (16/10, @kaijinre). Dono: "tem que ser só em cima da marca e colocar a nossa em cima"
    (a 1ª versão borrava 20% do meio da tela). Agora (parceiro_marca): a legenda amarela deles é coberta SÓ onde tem
    palavra e a NOSSA legenda entra exatamente em cima (SUB_Y_CENTER); a marca "@kaijinre", que anda pela tela, é
    trocada pela nossa @ no mesmo lugar e estilo. Sem espelho (ANIME_DESCARACT_FLIP=0: inverteria o texto dos painéis);
    o crop/cor do fx_clips continua. Devolve o vídeo coberto (ou o original se falhar)."""
    os.environ["ANIME_DESCARACT_FLIP"] = "0"
    # a legenda deles já foi coberta aqui: a detecção de legenda queimada do anime-pipeline achava a NOSSA tarja e
    # borrava o título (17/10, REUNION). No parceiro ela não roda.
    os.environ["ANIME_HARDSUB_DETECT"] = "0"
    # narrador por nicho (dono 17/10): config/parceiro.json "narradores" + "tipo_fonte" (ou PARCEIRO_TIPO)
    try:
        import json as _j
        _c = _j.loads((Path(__file__).resolve().parent.parent / "config" / "parceiro.json").read_text(encoding="utf-8"))
        _voz = (_c.get("narradores") or {}).get(os.environ.get("PARCEIRO_TIPO") or _c.get("tipo_fonte", "manhwa"))
        if _voz and not os.environ.get("ANIME_TTS_VOICE"):
            os.environ["ANIME_TTS_VOICE"] = _voz
    except (OSError, ValueError):
        pass
    os.environ.setdefault("ANIME_FX_MOV", "1")  # câmera por trecho + impacto (dono 17/10: "ficar no mínimo diferente")
    # 25/10: um processo faz vários Shorts seguidos — sem isto, o vídeo sem tarja herdava a altura do anterior
    os.environ.pop("SUB_Y_CENTER", None)
    os.environ.pop("GANCHO_Y", None)
    os.environ.pop("CORTES_COBERTURA_USADA", None)  # 27/10: teste T2 (tarja x delogo) — vai pro postar.json
    try:
        import parceiro_marca
        out = Path(video).with_name(Path(video).stem + "_reed.mp4")
        tarja = ""
        if os.environ.get("PARCEIRO_ESTILO", "titulo") == "titulo" and titulo_original:
            import anime_gancho  # dono 17/10: tarja branca com título chamativo em cima da legenda deles
            tarja = anime_gancho.gerar_titulo_tarja(titulo_original, narracao)
        cob = _fonte_cfg(fonte_url).get("cobertura", "kaijinre")
        if cob != "kaijinre":  # canais novos (18/10): cobertura pela config do canal ou "auto" (visão)
            r = parceiro_marca.cobrir_canal(video, out, handle or HANDLE_PARCEIRO,
                                            {"legenda": "auto", "apagar": "auto"} if cob == "auto" else cob,
                                            titulo=tarja or None)
            if not r:
                raise RuntimeError("cobrir_canal falhou")
            H = r["H"]
            centro = None
            if r["tarja"]:  # nossa legenda logo abaixo da tarja; se a tarja estiver no pé da tela, acima dela
                baixo = parceiro_marca.centro_saida(r["tarja"][1], H)
                centro = round(baixo + 0.05, 4) if baixo < 0.83 else round(parceiro_marca.centro_saida(r["tarja"][0], H) - 0.05, 4)
            elif r["placa"]:  # sem título: nossa legenda em cima da placa que cobriu a deles
                centro = parceiro_marca.centro_saida((r["placa"][0] + r["placa"][1]) / 2, H)
            if centro:
                os.environ["SUB_Y_CENTER"] = str(centro)
            # 25/10: o gancho dos 3 s iniciais fica no topo (11%-36%); tarja lá em cima = gancho desce pra baixo da
            # nossa legenda, senão escreve em cima do título da tarja
            if r["tarja"] and parceiro_marca.centro_saida(r["tarja"][0], H) < 0.40:
                os.environ["GANCHO_Y"] = str(round(min(0.62, (centro or 0.5) + 0.06), 4))
            elif r.get("topo_fixo") and parceiro_marca.centro_saida(r["topo_fixo"][1], H) > 0.09:
                # 27/10 (8a49d5): título fixo deles no alto ficou na tela — o gancho vai logo abaixo dele, não por cima
                os.environ["GANCHO_Y"] = str(round(min(0.62, parceiro_marca.centro_saida(r["topo_fixo"][1], H) + 0.02), 4))
            elif centro and centro < 0.40:
                # 30/10: legenda deles no alto (placa/delogo) = nossa legenda em 0,12-0,21; o gancho (topo, 0,11-0,31)
                # escrevia em cima dela nos 3 s iniciais. Gancho desce pra logo abaixo da nossa legenda.
                os.environ["GANCHO_Y"] = str(round(min(0.62, centro + 0.09), 4))
            os.environ["CORTES_COBERTURA_USADA"] = r.get("cobertura") or ""
            logging.info(f"[auto|parceiro] canal novo ({cob}): tarja={tarja or '-'} | {r} | nossa legenda em {centro}"
                         + (f" | gancho em {os.environ['GANCHO_Y']}" if os.environ.get("GANCHO_Y") else ""))
            return out
        det = parceiro_marca.detectar(video)
        if parceiro_marca.modo_cobertura(video) == "delogo":
            tarja = ""  # 28/10: delogo apaga a legenda deles; a nossa entra em cima, sem tarja branca
        if not parceiro_marca.cobrir(video, out, handle or HANDLE_PARCEIRO, det, titulo=tarja or None):
            raise RuntimeError("cobrir falhou")
        # 30/10: gravado só DEPOIS de cobrir (antes, o T2 registrava cobertura que não aconteceu quando cobrir falhava)
        os.environ["CORTES_COBERTURA_USADA"] = "tarja" if tarja else ("delogo" if det.get("faixa") else "nada")
        # com tarja, a nossa legenda vai ABAIXO dela (dono 17/10: "uma nova legenda mais embaixo")
        centro = 0.885 if tarja else parceiro_marca.centro_legenda_saida(det)
        logging.info(f"[auto|parceiro] tarja: {tarja or '(sem — borrão antigo)'}")
        if centro:
            os.environ["SUB_Y_CENTER"] = str(centro)
        logging.info(f"[auto|parceiro] legenda/marca deles cobertas só onde estavam, marca -> "
                     f"{handle or HANDLE_PARCEIRO}; nossa legenda em {centro}: {out.name}")
        return out
    except Exception as e:  # noqa: BLE001
        # 30/10: antes seguia com o original = Short no NOSSO canal com a @ e a legenda do parceiro (6x nos logs, quase
        # sempre MemoryError/WinError 1455). Agora devolve None: o fazer_short espera RAM, tenta 1x e, se falhar, não sai.
        for k in ("CORTES_COBERTURA_USADA", "SUB_Y_CENTER", "GANCHO_Y"):
            os.environ.pop(k, None)
        logging.error(f"[auto|parceiro] cobertura falhou ({type(e).__name__}: {e}) — sem cobertura o Short não sai")
        return None


def _tirar_faixa_preta(video):
    """03/11 (rodada): Short de parceiro vertical (720x1280) com faixas pretas EMBUTIDAS em cima/embaixo saía igual
    (modo native = escala + pad) — 40% da tela preta (J_0l755RUfU). Mede o quadro útil (cropdetect em 4 pontos); se
    a faixa passar de 8% da altura, recorta pra source_sem_faixa.mp4 (a fonte vira deitada -> reframe com fundo).
    Falhou = segue com o original."""
    import re
    video = Path(video)
    flags = 0x08000000 if os.name == "nt" else 0
    try:
        dur = anime_probe.video_duration(str(video)) or 0
        w, h = anime_probe.video_dimensions(str(video))
        if not (dur > 3 and w and h):
            return video
        caixas = []
        for f in (0.2, 0.4, 0.6, 0.8):
            r = subprocess.run(["ffmpeg", "-v", "info", "-ss", f"{dur * f:.2f}", "-i", str(video), "-frames:v", "8",
                                "-vf", "cropdetect=limit=24:round=2:reset=0", "-f", "null", "-"],
                               capture_output=True, text=True, timeout=120, creationflags=flags,
                               encoding="utf-8", errors="replace")
            m = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", r.stderr)
            if m:
                caixas.append(tuple(map(int, m[-1])))
        if len(caixas) < 3:
            return video
        # a maior caixa entre os pontos (cena escura num ponto não pode cortar conteúdo)
        cw, ch = max(c[0] for c in caixas), max(c[1] for c in caixas)
        cx, cy = min(c[2] for c in caixas), min(c[3] for c in caixas)
        if ch >= h * 0.84 and cw >= w * 0.92:
            return video
        ch, cw = min(ch, h - cy) // 2 * 2, min(cw, w - cx) // 2 * 2
        saida = video.with_name("source_sem_faixa.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", f"crop={cw}:{ch}:{cx}:{cy}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-c:a", "copy", str(saida)],
                       check=True, capture_output=True, timeout=900, creationflags=flags)
        logging.info(f"[auto|short] faixa preta embutida na fonte ({w}x{h} -> útil {cw}x{ch}): recortada")
        return saida
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[auto|short] medir faixa preta falhou ({type(e).__name__}: {str(e)[:100]}) — original")
        return video


def fazer_short(cand, target_lines, dry_run, use_worker=False,
                worker_host="100.125.7.77", worker_port=8772):
    """Fluxo para formato curto (9:16)."""
    _marca_feito(cand["id"], "short_attempted")
    # 27/10 teste T3 (TESTES.md): palavra de impacto no centro x inclinada de lado; fixo por vídeo -> postar.json
    try:
        _aj = json.loads((Path(__file__).resolve().parent / "cortes_ajustes.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _aj = {}
    # 27/10 (dona): texto do vídeo (roteiro/título/gancho) no Argon; reserva automática = Gemini (claude_client)
    os.environ["TEXTO_VIDEO_MODELO"] = _aj.get("texto_video_modelo", "")
    os.environ["TEXTO_VIDEO_RESERVA"] = _aj.get("texto_video_reserva", "")
    os.environ["TEXTO_VIDEO_TIMEOUT"] = str(_aj.get("texto_video_timeout_s", 120))
    # 30/10 (dona: "toda coisa subjetiva vira variante A B C D E"): os sorteios T3-T9 (um bloco por teste até 30/10,
    # ver .bak_20261030_variantes) passaram para bin\variantes.py — mesmo md5(prefixo+id) e mesma divisão com 2 braços
    # (conferido em 629 ids reais), agora com N braços ("abc", lista) e os testes novos T10 saudacao / T11
    # ninguem_esperava. Cada braço vai na env de sempre (CORTES_LEGENDA_ESTILO, _GANCHO_MEIO, _GANCHO_REMOTION,
    # _FX_CHOQUE, _MASCOTE, _CURTO [T8, Fable D3], _FALA_RAPIDA [T9, D16], _SAUDACAO, _NINGUEM_ESPERAVA) -> postar.json.
    # ANTES DE MUDAR um teste: FABLE_DECISOES.md (D1/D3/D16) e o placar (bin\placar_variantes.py).
    import variantes
    variantes.aplicar(cand["id"], _aj)
    _fr = os.environ.get("CORTES_FALA_RAPIDA")  # T9: B = fala +fala_delta pontos % (anime_tts._frase_v2)
    os.environ["CORTES_FALA_DELTA"] = str(_aj.get("fala_delta", 15)) if _fr == "B" else "0"

    work, video, txt = _prepara_candidato(cand)
    if work:
        (work / "_testes_usados.json").unlink(missing_ok=True)  # T5/T6: o render deste vídeo grava o que usou
    if not work:
        if work and work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA", "Baixar ou Transcrição falhou")
        return False
    video = _tirar_faixa_preta(video)
    original = Path(video)
    if cand.get("parceiro"):
        try:
            _narr = Path(txt).read_text(encoding="utf-8", errors="replace") if txt and Path(str(txt)).is_file() else str(txt or "")
        except OSError:
            _narr = ""
        video = _reeditar_parceiro(original, titulo_original=cand.get("title", ""), narracao=_narr,
                                   fonte_url=cand.get("parceiro", ""))
        if video is None:  # 30/10: quase sempre falta de RAM — espera a janela abrir e tenta 1x
            import gc
            gc.collect()
            try:
                import fx_clips
                fx_clips._wait_for_ram(min_mb=1500, max_wait_s=600)
            except Exception:  # noqa: BLE001
                time.sleep(60)
            video = _reeditar_parceiro(original, titulo_original=cand.get("title", ""), narracao=_narr,
                                       fonte_url=cand.get("parceiro", ""))
        if video is None:
            anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA", "cobertura do parceiro falhou")
            if work.exists():
                shutil.rmtree(work)
            return False
        use_worker = False  # o worker baixa o ORIGINAL de novo pela URL: perderia a reedição e o roteiro maior

    orig_dur = anime_probe.video_duration(str(video))
    # Teto de 10 linhas: source curta (50s) → 10 linhas → ~30s de narração (bom short)
    # Linha curta no TTS edge-tts = ~3s. Target = 30s → 10 linhas máximo.
    target_lines = min(10, max(5, int(orig_dur / 4.5))) if orig_dur else 8
    if cand.get("parceiro"):  # resumo do parceiro (~85 s) conta a história inteira: não espremer em 10 frases
        # 21/10: medido ~5,4 s por frase (não 4,5) — fonte de 34 s com 8 frases dava ~43 s de narração e o fim
        # (história e o CTA) era cortado; mínimo 5 em vez de 8 pra fonte curta
        # 30/10: teto 18 -> 10 (~55 s). 26 Shorts saíram com 90-220 s (fonte de 88-180 s); medido 18-27/10 entre os
        # elegíveis: 60 s+ chegam a 1.500 views em 0 de 34 e passam de 65% assistido em 2 de 34 (< 30 s: 4 e 8 de 12).
        # Continua bem mais longo que o braço B do T8 (4-5 frases), então o teste segue comparando curto x longo.
        target_lines = min(10, max(5, int(orig_dur / 5.5))) if orig_dur else 10
        if orig_dur and orig_dur < 30:  # 23/10 (dono): fonte curta com 5 frases = narração 1,4-2x o original e a última
            target_lines = 3        # cena repetia imagem (4 casos em 20-23/10: fontes de 16-22 s, frase real ~7,5 s)
        elif os.environ.get("CORTES_CURTO") == "B":  # 29/10 teste T8: versão curta (~5,4 s por frase -> 22-27 s)
            target_lines = 5 if orig_dur and orig_dur >= 60 else 4
    logging.info(f"[auto|short] Duração do original: {orig_dur:.1f}s -> Alvo: {target_lines} linhas"
                 f" (T8 curto={os.environ.get('CORTES_CURTO', '-')}).")

    # voz clonada (dono 19/10; todos os nichos desde 21/10): o narrador é escolhido pelo encaixe com o nicho do vídeo e
    # ANTES do roteiro — 21/10: era escolhido depois e o anime_script nunca via o VOZ_CLONADA, então nenhum Short saiu
    # no jeito do personagem (o Chapolin narrou sem nenhum bordão)
    clone = None
    nicho_clone = None
    if cand.get("parceiro") and not use_worker and (getattr(anime_voz_clonada, "TODOS_OS_NICHOS", False)
                                                     or os.environ.get("PARCEIRO_TIPO", "manhwa") in anime_voz_clonada.NICHOS):
        try:
            nicho_clone = anime_voz_clonada.nicho_do_video(os.environ.get("PARCEIRO_TIPO"), os.environ.get("PARCEIRO_CANAL"))
            clone = anime_voz_clonada.proxima(nicho_clone)
            if clone:
                logging.info(f"[auto|short] narrador escolhido pelo nicho: {clone[0]} — {anime_voz_clonada.ULTIMA_ESCOLHA}")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[auto|short] rodízio da voz clonada falhou ({e}) — voz normal")
    # 28/10 (dona: "Thalita, Antonio e as outras do Edge PURAS nunca; as clonadas, até as ruins, são melhores; Edge só
    # como base com clone em cima"): Short de parceiro sem narrador clonado NÃO sai (antes seguia com a Edge pura).
    if cand.get("parceiro") and not clone and os.environ.get("PERMITIR_EDGE_PURO") != "1":
        logging.error("[auto|short] sem narrador clonado — Short não sai (voz Edge pura proibida, dona 28/10)")
        anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA", "sem voz clonada (Edge pura proibida)",
                                 orig_dur=orig_dur, lines=0, ar=None)
        return False
    # dona 23/10 ("testando nos vídeos reais devagar; quem se sair bem aparece mais"): uma parte dos Shorts com clone
    # vira TESTE (anime_testes): formato com várias vozes ou voz nova sozinha. Os outros são o controle "solo".
    teste = None
    if clone:
        try:
            teste = anime_testes.sortear(nicho_clone, os.environ.get("PARCEIRO_CANAL"), dur=orig_dur)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[auto|short] sorteio do teste falhou ({type(e).__name__}: {e}) — Short normal")
        if teste and teste.get("voz"):  # o _historico guarda a escolha da voz que narrou, não a do clone trocado
            for k in ("usos_no_nicho", "usos", "bonus_views"):
                anime_voz_clonada.ULTIMA_ESCOLHA.pop(k, None)
            anime_voz_clonada.ULTIMA_ESCOLHA.update(teste=teste["item"], estado_teste=teste["estado"], encaixe=1,
                                                    trocado_de=clone[0])
            clone = (teste["voz"], teste["base"])
        if teste:
            logging.info(f"[auto|short] TESTE {teste['item']} ({teste['estado']})")
    formato = teste.get("formato") if teste else None

    roteiro = work / "roteiro.txt"
    # CTA no fim como frase À PARTE (novidade e73ac5 do hipercool, 21/10): a história pede 1 frase a menos pra
    # duração não crescer; só Short de parceiro (as línguas traduzem depois, junto); PARCEIRO_CTA=0 desliga
    # formato em teste: sem CTA (as regras do formato proíbem pedir like e 1 linha a mais desalinharia fala x voz)
    cta = cand.get("parceiro") and os.environ.get("PARCEIRO_CTA", "1") != "0" and not formato
    # dono 21/10: o fim emenda no começo (loop) em vez do CTA — o CTA só volta se o gancho falhar
    loop = cand.get("parceiro") and os.environ.get("PARCEIRO_LOOP", "1") != "0"
    n = 0
    tempos_arq = work / "legenda_tempos.json"
    # + restos de um formato de outra rodada na mesma pasta (dry-run/--id): o anime_segments usaria o diálogo velho
    for velho in ("roteiro_tempos.json", "roteiro_falas.json", "roteiro_narrador.txt", "roteiro_tempos_solo.json"):
        (work / velho).unlink(missing_ok=True)
    env_antes = {k: os.environ.get(k) for k in ("VOZ_CLONADA", "VOZ_CLONADA_VERSAO", "NICHO_CLONE")}
    if clone and not formato:  # só durante o roteiro: as versões nas outras línguas (anime_idiomas) seguem sem o clone
        os.environ.update(VOZ_CLONADA=clone[0], VOZ_CLONADA_VERSAO="2")  # formato: história neutra, a IA do formato reescreve
    if nicho_clone:
        os.environ["NICHO_CLONE"] = nicho_clone
    anime_script.TRANSCRICAO_LIXO = False
    try:
        if tempos_arq.exists():  # dono 21/10: cada frase com o segundo do original que ela narra (sincronia com o quadro)
            try:
                frases, tempos = anime_script.rewrite_curto_com_tempo(json.loads(tempos_arq.read_text(encoding="utf-8")),
                                                                      target_lines - (1 if cta else 0), orig_dur)
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[auto|short] roteiro com tempo falhou ({e}) — roteiro normal")
                frases, tempos = [], []
            if frases:
                roteiro.write_text("\n".join(frases) + "\n", encoding="utf-8")
                (work / "roteiro_tempos.json").write_text(json.dumps(tempos), encoding="utf-8")
                n = len(frases)
        if n == 0 and not anime_script.TRANSCRICAO_LIXO:  # 27/10: lixo = não tenta o roteiro normal (outro modelo inventava)
            n = anime_script.rewrite_to_file(txt, roteiro, target_lines=target_lines - (1 if cta else 0))
        if n == 0:
            if work.exists(): shutil.rmtree(work)
            anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA",
                                     "Transcrição lixo (IA recusou)" if anime_script.TRANSCRICAO_LIXO
                                     else "Roteirização falhou/Recusa IA", orig_dur=orig_dur)
            return False
        if loop:
            frases = [l for l in roteiro.read_text(encoding="utf-8").splitlines() if l.strip()]
            nova = anime_script.fechar_loop(frases)
            if nova:
                logging.info(f"[auto|short] gancho de retorno: «{frases[-1]}» -> «{nova}»")
                frases[-1] = nova
                roteiro.write_text("\n".join(frases) + "\n", encoding="utf-8")
                cta = False
    finally:
        for k, v in env_antes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    # 01/11 dona ("dorama narrado pro homem em 1ª pessoa mesmo quando a protagonista é mulher — se for mulher a
    # narradora tem que ser mulher"): a voz é escolhida antes do roteiro; com o roteiro pronto, confere a concordância
    if clone and anime_script.primeira_pessoa() and roteiro.exists():
        try:
            fem = anime_script.narradora_feminina(roteiro.read_text(encoding="utf-8"))
            gen_voz = anime_voz_clonada.genero_da_voz(clone[0])
            if fem and gen_voz != "f":
                nova_voz = anime_voz_clonada.proxima(nicho_clone, genero="f")
                if nova_voz:
                    logging.info(f"[auto|short] 1ª pessoa de MULHER: narrador {clone[0]} -> narradora {nova_voz[0]}")
                    anime_voz_clonada.ULTIMA_ESCOLHA.update(trocado_de=clone[0], motivo="protagonista mulher em 1ª pessoa")
                    clone = nova_voz
            elif not fem and gen_voz == "f" and anime_script.narradora_feminina(roteiro.read_text(encoding="utf-8")) \
                    is False and _re.search(r"\b(obrigado|sozinho|eu mesmo)\b", roteiro.read_text(encoding="utf-8"), _re.I):
                nova_voz = anime_voz_clonada.proxima(nicho_clone, genero="m")
                if nova_voz:
                    logging.info(f"[auto|short] 1ª pessoa de HOMEM: narradora {clone[0]} -> narrador {nova_voz[0]}")
                    clone = nova_voz
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[auto|short] conferência do gênero da narração falhou ({type(e).__name__}: {e})")
    if cta:
        frase = anime_script.cta_fim(cand.get("id") or cand.get("title", ""))
        with open(roteiro, "a", encoding="utf-8") as fh:
            fh.write(frase + "\n")
        n += 1
        arq_t = work / "roteiro_tempos.json"
        if arq_t.exists():  # o CTA também ganha um tempo (o fim do original), senão a sincronia cai no modo espalhado
            t = json.loads(arq_t.read_text(encoding="utf-8"))
            arq_t.write_text(json.dumps(t + [max(t[-1] if t else 0, (orig_dur or 0) * 0.9)]), encoding="utf-8")
        logging.info(f"[auto|short] CTA no fim: {frase}")
    clone_solo, refeito_solo = clone, False  # formato: o clone fica de reserva (volta pro solo se falhar ou soar mal)
    if formato:
        if anime_testes.aplicar_formato(work, formato):
            clone = None  # os "if clone" abaixo (env do pipeline, registrar, --narrador) não valem pro formato
            n = len([l for l in roteiro.read_text(encoding="utf-8").splitlines() if l.strip()])
        else:
            anime_testes.registrar(teste, falhou="a IA não devolveu o diálogo")
            anime_testes.contar_falha(teste["item"], "a IA não devolveu o diálogo")
            teste = formato = None
            refeito_solo = True  # roteiro escrito sem o jeito do narrador: não entra no controle "solo"
    logging.info(f"[auto|short] roteiro curto: {n} frases")

    w, h = anime_probe.video_dimensions(str(video))
    ar = w / float(h) if h else 0.0
    if anime_probe.is_vertical(str(video)):
        logging.info(f"[auto|short] fonte VERTICAL ({w}x{h}) — native.")
        short_kind = "native"
    else:
        logging.warning(f"[auto|short] fonte HORIZONTAL ({w}x{h}) — reframe.")
        short_kind = "reframe"

    if dry_run:
        logging.info("[auto] DRY-RUN — parou antes de renderizar")
        return True

    config_clone, resumo_clone = "1", work / "clone_resumo.json"

    if use_worker:
        logging.info(f"[auto|short] DESPACHANDO pro worker {worker_host}:{worker_port}...")
        payload = {
            "video_url": cand["url"],
            "titulo": cand["title"],
            "modo": "short",
            "work_dir": "",  # pasta do PC2 (ver deitado)
            # 25/10: PC1 envia transcrição/roteiro pro PC2 (PC2 não tem Whisper funcionando)
            "transcript_txt": txt if txt else "",
            "transcript_lang": cand.get("_lang") or "en",
            "roteiro_txt": roteiro.read_text(encoding="utf-8") if roteiro.exists() else "",
        }
        # Se tiver legenda_tempos.json ou roteiro_tempos.json, envia também
        legenda_tempos_path = work / "legenda_tempos.json"
        if legenda_tempos_path.exists():
            payload["legenda_tempos_json"] = legenda_tempos_path.read_text(encoding="utf-8")
        result = anime_worker_client.run_anime(worker_host, worker_port, payload, timeout=14400)
        if not result or not result.get("ok"):
            err = result.get("error", "desconhecido") if result else "sem resposta"
            logging.error(f"[auto|short] Worker falhou: {err}")
            anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA",
                                   f"Worker error: {err}", orig_dur=orig_dur, lines=n, ar=ar)
            if work.exists(): shutil.rmtree(work)
            return False
        logging.info(f"[auto|short] Worker OK: {result.get('video_path', '')}")
        # PC2 e SO worker: TRANSFERE o video pro PC1 e depois APAGA do PC2.
        remoto = result.get("video_path", "")
        remote_wd = result.get("work_dir", str(work))
        vf = work / "final_anime_short.mp4"
        if anime_worker_client.baixar(worker_host, worker_port, remoto, vf):
            logging.info(f"[auto|short] baixado pro PC1: {vf}")
            r_clean = anime_worker_client.limpar(worker_host, worker_port, remote_wd)
            logging.info(f"[auto|short] cleanup PC2: {r_clean}")
        else:
            logging.error("[auto|short] FALHA ao baixar do PC2 — NAO apago de la "
                          "(pra nao perder o video). Verifique espaco/rede.")
            anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA",
                                     "download do worker falhou", orig_dur=orig_dur, lines=n, ar=ar)
            return False
    else:
        cmd = [sys.executable, str(PIPELINE),
               "--video-source", str(video), "--script", str(roteiro),
               "--titulo", cand["title"], "--formato", "short",
               "--short-source-kind", short_kind]
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        if clone:  # só no pt: as versões nas outras línguas (anime_idiomas) usam o os.environ, sem o clone
            config_clone = anime_voz_clonada.config_da_vez()
            env.update(VOZ_CLONADA=clone[0], VOZ_CLONADA_BASE=clone[1], VOZ_CLONADA_VERSAO="2",
                       VOZ_CLONADA_CONFIG=config_clone, VOZ_CLONADA_RESUMO=str(resumo_clone))
            logging.info(f"[auto|short] voz clonada: {clone[0]} ({clone[1]}, config {config_clone})")
        vf = work / "final_anime_short.mp4"
        # 02/11 dona ("usar o Kaggle pra produzir em lotes os Shorts de corte — liberar RAM e CPU daqui pros Veo 3"):
        # com SHORTS_NO_KAGGLE=1 a RENDERIZAÇÃO (o que come CPU/RAM: TTS + clone + clipes + legenda) vai pra fila do
        # Kaggle (fila_shorts, linha paralela do kaggle_trabalhador); download, reedição, roteiro e escolha da voz
        # ficam aqui (rápidos). Volta o vídeo e segue igual (publish, testes, métricas). Falhou/demorou = renderiza aqui.
        r = None
        if os.environ.get("SHORTS_NO_KAGGLE") == "1":
            try:
                import lote_shorts_kaggle
                ok_k = lote_shorts_kaggle.renderizar(work, video, roteiro, cand, short_kind, env, vf)
                if ok_k:
                    r = subprocess.CompletedProcess(cmd, 0)
                    logging.info("[auto|short] renderizado no KAGGLE (lote)")
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[auto|short] Kaggle falhou ({type(e).__name__}: {e}) — renderiza aqui")
        # 03/11 (dona: "continuar usando os PCs normal no máximo; o Kaggle é pra ajudar a encher o estoque"): os Shorts
        # EXTRAS do abastecedor_kaggle (SHORTS_SO_KAGGLE=1) nunca renderizam no PC1 — Kaggle falhou = desiste
        if r is None and os.environ.get("SHORTS_SO_KAGGLE") == "1":
            logging.warning("[auto|short] extra do Kaggle sem vídeo do Kaggle — não renderiza no PC (SHORTS_SO_KAGGLE)")
            return False
        if r is None:
            r = subprocess.run(cmd, env=env)
            if r.returncode != 0 and os.environ.get("SHORTS_NO_KAGGLE") == "1":
                # 02/11: o render do PC logo depois do Kaggle saiu rc=1 em 6 min sem traceback no log (ZtABfk1NGxA) —
                # 1 nova tentativa antes de perder o Short (o estado do workspace mexido pelo lote pode ter atrapalhado)
                logging.warning("[auto|short] render no PC falhou depois do Kaggle — 1 nova tentativa")
                r = subprocess.run(cmd, env=env)
        if teste:  # teste gradual: o que se ouve no Short pronto confere com o roteiro? (anime_testes.conferir)
            q = anime_testes.conferir(work, vf) if r.returncode == 0 and vf.exists() else \
                {"ok": None, "motivo": f"pipeline rc={r.returncode}"}
            logging.info(f"[auto|short] TESTE {teste['item']}: áudio ok={q.get('ok')} sem={q.get('sem')} {q.get('motivo') or ''}")
            anime_testes.contar_qualidade(teste["item"], q)
            teste["qualidade"] = q
            if r.returncode != 0 and not formato:  # voz em teste quebrou o pipeline
                anime_testes.contar_falha(teste["item"], f"pipeline rc={r.returncode}")
            if formato and (r.returncode != 0 or q.get("ok") is False):  # formato falhou/soou mal: refaz no SOLO, 1 vez
                item_formato, rc_formato = teste["item"], r.returncode
                anime_testes.registrar(teste, qualidade=q, refeito_solo=True,
                                       falhou=q.get("motivo") if r.returncode != 0 else None)
                anime_testes.desfazer_formato(work)
                teste = formato = None
                refeito_solo = True
                clone = clone_solo
                env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
                if clone:
                    config_clone = anime_voz_clonada.config_da_vez()
                    env.update(VOZ_CLONADA=clone[0], VOZ_CLONADA_BASE=clone[1], VOZ_CLONADA_VERSAO="2",
                               VOZ_CLONADA_CONFIG=config_clone, VOZ_CLONADA_RESUMO=str(resumo_clone))
                logging.warning(f"[auto|short] formato refeito no SOLO ({clone[0] if clone else 'voz normal'})")
                r = subprocess.run(cmd, env=env)
                if rc_formato != 0 and r.returncode == 0:  # o solo saiu: a culpa era do formato, não da fonte/máquina
                    anime_testes.contar_falha(item_formato, f"pipeline rc={rc_formato}")
        if r.returncode != 0:
            if clone:
                anime_voz_clonada.registrar(*clone, nicho=nicho_clone, canal=os.environ.get("PARCEIRO_CANAL"))
            if teste:
                anime_testes.registrar(teste, qualidade=teste.get("qualidade"), falhou=f"pipeline rc={r.returncode}")
            logging.error(f"[auto|short] pipeline falhou (rc={r.returncode})")
            anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA", f"Pipeline rc={r.returncode}", orig_dur=orig_dur, lines=n, ar=ar)
            return False

    _marca_feito(cand["id"], "short")

    # Coleta metricas finais de SUCESSO antes de limpar
    af_dur, vf_dur = 0.0, 0.0
    if vf.exists():
        vf_dur = anime_probe.video_duration(str(vf))
        try:
           pass  # json vem do topo (21/10: este import local quebrava o roteiro com tempo)
           out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "json", str(vf)], capture_output=True, text=True).stdout
           d = json.loads(out)
           for s in d.get("streams",[]):
               if s.get("codec_type") == "audio": af_dur = float(s.get("duration", 0))
        except: pass

    # parceiro: o original e a detecção ficam pras versões nas outras línguas (anime_idiomas), apagados no fim
    # (_impactos.json: as línguas usam as mesmas frases de impacto da curva de narração)
    # 23/10: + clone_resumo.json (era apagado aqui, antes do registrar lá embaixo: o .txt do narrador saía sem as
    # frases) e o roteiro do teste/formato (o anime_testes copia pra pasta do Short depois do publish)
    _cleanup_workspace(work, manter=[original.name, original.with_suffix(".parceiro.json").name, "_impactos.json",
                                     "clone_resumo.json", "roteiro_falas.json", "roteiro_narrador.txt"]
                       if cand.get("parceiro") else [])

    # Gera postar.json + metadata viral automaticamente
    if vf.exists():
        try:
            nome = _extrair_nome_anime(cand["title"])  # 1x só: a versão pt e as línguas usam o MESMO nome
            anota = work / "_postar_pt.txt"            # caminho do postar.json pt (as línguas herdam a análise dele)
            pub_cmd = [sys.executable, str(PIPELINE.parent / "anime_publish.py"),
                       "--video", str(vf),
                       "--anime", nome,
                       "--cap", "1",
                       "--formato", "short",
                       "--source-url", cand.get("url", ""),
                       "--titulo-original", cand.get("title", ""),
                       "--roteiro", str(work / "roteiro.txt"),
                       "--anota-postar", str(anota)]
            if cand.get("parceiro"):  # categoria "parceiro" (quem posta é o parceiro_diario) em qualquer nicho
                pub_cmd += ["--midia", os.environ.get("PARCEIRO_TIPO", "manhwa"),
                            "--parceiro", _fonte_cfg(cand["parceiro"]).get("nome") or cand["parceiro"].rstrip("/").split("/")[-2]]
            if cand.get("parceiro") and os.environ.get("PARCEIRO_CANAL"):  # parceiro_diario escolhe o canal
                pub_cmd += ["--canal", os.environ["PARCEIRO_CANAL"]]
            if clone:  # a frase sai da voz base e o RVC troca o timbre: quem se ouve é o narrador clonado
                pub_cmd += ["--narrador", clone[0], "--voz-base", clone[1]]
            elif formato:  # várias vozes: quem fala vai no --elenco (narrador = voz edge daria crédito errado no placar)
                pass
            elif not use_worker:  # no PC2 a voz é escolhida lá
                import anime_tts
                pub_cmd += ["--narrador", os.environ.get("ANIME_TTS_VOICE") or anime_tts.NARRATOR_VOICE]
            ct = anime_testes.campos(teste, clone)  # teste gradual: "solo" = controle; refeito no solo fica à parte
            if ct:
                pub_cmd += ["--teste-voz", "solo_refeito" if refeito_solo else ct["teste_voz"],
                            "--elenco", ",".join(ct["elenco"])] + (["--sintetico"] if ct["sintetico"] else [])
            segurado = teste and (teste.get("qualidade") or {}).get("ok") is False  # voz em teste que soou mal
            if segurado:  # já nasce segurado (nunca fica pronto=True nem por um instante)
                pub_cmd += ["--segurar", teste["qualidade"].get("motivo") or "áudio ruim"]
            env_pub = dict(os.environ, PYTHONUTF8="1")
            rp = subprocess.run(pub_cmd, env=env_pub, timeout=4800)  # 4800: inclui a análise do vídeo pronto (anime_revisao, 16/10)
            if teste:  # roteiro na pasta do Short (o vigia reconfere) + registro
                pj_t = Path(anota.read_text(encoding="utf-8").strip()) if rp.returncode == 0 and anota.exists() else None
                if pj_t:
                    anime_testes.guardar_roteiro(work, pj_t.parent)
                    anime_testes.marcar_conferido(pj_t.parent, teste.get("qualidade"))
                anime_testes.registrar(teste, pasta=pj_t.parent if pj_t else None, qualidade=teste.get("qualidade"),
                                       falhou=None if pj_t else f"publish rc={rp.returncode}")
            if clone:  # cópia na pasta do narrador (Área de Trabalho); sem postar.json = conta como falha
                pj = Path(anota.read_text(encoding="utf-8").strip()) if rp.returncode == 0 and anota.exists() else None
                if segurado:  # não vai subir: conta como falha da voz+base (a trava de 24 h do rodízio vale pra ela)
                    pj = None
                anime_voz_clonada.registrar(*clone, video=pj.parent / "video.mp4" if pj else None, config=config_clone,
                                            resumo=resumo_clone if resumo_clone.exists() else None,
                                            nicho=nicho_clone, canal=os.environ.get("PARCEIRO_CANAL"))
            if rp.returncode == 0:
                logging.info("[auto|short] publish OK — postar.json gerado")
                if cand.get("parceiro") and original.exists():
                    import anime_idiomas  # versões nos canais estrangeiros (dono, 16/10)
                    pt_postar = anota.read_text(encoding="utf-8").strip() if anota.exists() else None
                    # formato: as línguas (uma voz só) traduzem a história do narrador, não o diálogo
                    rot_l = work / "roteiro_narrador.txt" if formato and (work / "roteiro_narrador.txt").exists() \
                        else work / "roteiro.txt"
                    if formato and (work / "_impactos.json").exists():  # impactos eram das falas do diálogo, não da história
                        (work / "_impactos.json").replace(work / "_impactos_formato.json")
                    anime_idiomas.gerar(work, original, rot_l, cand, nome, pt_postar=pt_postar)
            else:
                logging.warning(f"[auto|short] publish falhou (rc={rp.returncode}) — vídeo mantido sem metadata")
        except Exception as e:
            logging.warning(f"[auto|short] publish erro: {e}")

    if cand.get("parceiro"):
        _cleanup_workspace(work)  # agora sim: original, detecção e pastas das línguas
    logging.info(f"[auto|short] PRONTO: {work}")
    anime_metrics.record_job(cand["id"], cand["title"], "short", "SUCESSO", orig_dur=orig_dur, lines=n, final_v=vf_dur, final_a=af_dur, ar=ar)
    return True


def main():
    p = argparse.ArgumentParser(
        description="Recap de anime — modo autônomo. 3 modos de engine:\n"
                    "  local   = tudo aqui (gasta CPU本地)\n"
                    "  worker  = discovery+fetch+script aqui, render no PC2 (max worker)\n"
                    "  both    = short no PC2, deitado aqui (50/50 automático)")
    p.add_argument("--fonte", default=None,
                   help="canal PARCEIRO no lugar da busca (ex.: https://www.youtube.com/@kaijinre/shorts): "
                        "resumos sem 'Part N' primeiro; reedita (cobre legenda/marca deles)")
    p.add_argument("--id", default=None, help="só este vídeo da fonte (o PC1 escolhe e manda o PC2 fazer)")
    p.add_argument("--modo", choices=["deitado", "short", "ambos"], default="ambos",
                   help="Formato do vídeo")
    p.add_argument("--engine", choices=["local", "worker", "both"], default="both",
                   help="local=tudo aqui | worker=render no PC2 | both=short no PC2, deitado aqui")
    p.add_argument("--top", type=int, default=30, help="Considera os N mais vistos")
    p.add_argument("--target-lines", type=int, default=40, help="Frases no roteiro (deitado)")
    p.add_argument("--dry-run", action="store_true", help="Só descobre e roteiriza, não renderiza")
    p.add_argument("--limit", type=int, default=1, help="Máximo vídeos por modo (0=infinito)")
    p.add_argument("--worker-host", default=os.environ.get("ANIME_WORKER_HOST", "100.125.7.77"))
    p.add_argument("--worker-port", type=int,
                   default=int(os.environ.get("ANIME_WORKER_PORT", "8772")))
    args = p.parse_args()

    # ── Checar worker ────────────────────────────────────────────────
    use_worker = args.engine in ("worker", "both")
    worker_online = False
    if use_worker:
        if anime_worker_client.is_online(args.worker_host, args.worker_port):
            h = anime_worker_client.health(args.worker_host, args.worker_port)
            logging.info(f"[auto] Worker PC2 online: cores={h['cores']}, "
                        f"ram={h['ram_gb']}GB, ffmpeg={h['ffmpeg']}")
            worker_online = True
        else:
            logging.warning(f"[auto] Worker PC2 offline — caindo pra LOCAL")
            use_worker = False

    # ── Modo SHORT ──────────────────────────────────────────────────
    if args.modo in ("short", "ambos"):
        logging.info(">>> SHORT — discover...")
        feitos = _ja_feitos("short")
        tentados = _ja_feitos("short_attempted")
        try:  # 22/10: fonte já POSTADA (registro durável do parceiro_diario) também conta como feita — em 20/10 o disco
            #       cheio não gravou o _feitos_short e 6 fontes foram produzidas e postadas de novo em outro canal
            for _por_canal in json.loads((BASE / "_fontes_postadas.json").read_text(encoding="utf-8")).values():
                feitos |= set(_por_canal)
        except (OSError, ValueError, AttributeError):
            pass
        # filtra os feitos ANTES de cortar no top (16/10: discover(top=2) devolvia só os 2 melhores, já feitos,
        # e a rodada morria em "nenhum candidato" com centenas de candidatos novos na lista)
        cand_pc1 = None
        if args.id and os.environ.get("SEM_YTDLP") == "1":
            # 26/10: PC2/PC3 não listam o canal (yt-dlp = mesmo IP da casa): o PC1 manda o vídeo escolhido em cand.json
            for f in sorted(BASE.glob(f"{args.id}_*/cand.json")):
                cand_pc1 = json.loads(f.read_text(encoding="utf-8"))
            logging.info(f"[auto] SEM_YTDLP=1: candidato do PC1 {'achado' if cand_pc1 else 'NÃO achado'} ({args.id})")
        fonte = ([cand_pc1] if cand_pc1 else [] if os.environ.get("SEM_YTDLP") == "1" and args.id
                 else anime_discover.discover_canal(args.fonte) if args.fonte
                 else anime_discover.discover_shorts(top=max(args.top * 25, 50)))
        try:  # 03/11: fontes reservadas por quem já escolheu (PC2, PC3, abastecedor do Kaggle) — D:\video-fila\ocioso
            _rv = json.loads(Path(r"D:\video-fila\estado\fontes_reservadas.json").read_text(encoding="utf-8"))
            reservados = {k for k, t in _rv.items() if time.time() - t < 8 * 3600}
        except (OSError, ValueError):
            reservados = set()
        if args.id:
            reservados.discard(args.id)  # quem reservou foi quem mandou fazer este
        novos = [c for c in fonte if c["id"] not in feitos and c["id"] not in tentados and c["id"] not in reservados]
        # 30/10 (321 Shorts de 18-27/10): fonte com < 100 mil views chega a 500 views em 11% contra 30% (p 0,002) — entra
        # no lote igual e perde lá. Fontes acima do piso primeiro; abaixo só se a fonte não tiver nenhuma acima.
        # PISO_VIEWS_FONTE=0 desliga.
        piso = int(os.environ.get("PISO_VIEWS_FONTE", "100000") or 0)
        fortes = [c for c in novos if (c.get("views") or 0) >= piso]
        if piso and fortes and len(fortes) < len(novos):
            logging.info(f"[auto] piso de {piso:,} views na fonte: {len(fortes)} de {len(novos)} candidatos passam")
            novos = fortes + [c for c in novos if (c.get("views") or 0) < piso]
        cands = novos[:args.top]
        if args.id:  # balanço entre PCs (17/10): o PC1 escolhe o vídeo e manda o PC2 fazer ESSE, sem repetir
            cands = [c for c in fonte if c["id"] == args.id][:1]
        import ytdlp_vez
        # 23/10 (dono): também no "espaçando downloads" (5-15 min de espera depois de bloqueios) — o estoque sai na hora
        espera = getattr(ytdlp_vez, "espera_download_s", lambda: 0)()
        if (ytdlp_vez.pausado() or espera > 120) and args.fonte and not args.id:
            # 22/10: com o IP em pausa a rodada parava ANTES do download — o estoque (estoque_fontes, consumido no
            # anime_fetch.download_video) nunca era usado justo quando serve. Agora: fonte já baixada do estoque.
            est = _cands_do_estoque(args.fonte, feitos | tentados)
            if est:
                motivo = "IP em pausa" if ytdlp_vez.pausado() else f"download esperaria {espera / 60:.0f} min"
                logging.info(f"[auto] {motivo} — uso o ESTOQUE: {est[0]['id']} ({est[0]['fonte_estoque']}, "
                             f"{est[0]['title'][:60]})")
                cands = est[:1]
        if not cands:
            logging.warning("[auto] Nenhum candidato short disponível.")
        else:
            logging.info(f"[auto] {len(cands)} candidatos short novos. Engine={args.engine}")

        # Split: worker→short faz tudo no PC2, local→short faz tudo aqui,
        #        both→short vai pro worker (short = vertical = mais leve pro PC2)
        short_engine = "worker" if (args.engine == "both") else args.engine
        short_local = (short_engine == "local")

        for c in cands:
            # YouTube barrando o IP: cada candidato tentado agora ficava "tentado" pra sempre (21/10: ~216 dos
            # melhores queimados em 4 h de pausa). Do estoque não baixa nada: segue.
            if ytdlp_vez.pausado() and not c.get("estoque"):
                # 23/10 (dona: produção do recap no máximo): com proxy e banda de emergência, segue — o
                # anime_fetch.download_video baixa pelo proxy; se falhar, o candidato volta pra fila (abaixo)
                import anime_fetch
                try:  # 30/10 (dona, D43): o Kaggle (outro IP) baixa — a rodada não para por falta de IP
                    import kaggle_baixar
                    kaggle_vivo = os.environ.get("KAGGLE_BAIXAR", "1") != "0" and kaggle_baixar.vivo(5)
                except Exception:  # noqa: BLE001
                    kaggle_vivo = False
                if kaggle_vivo:
                    logging.info(f"[auto] IP em pausa — {c['id']} vai pelo baixador do KAGGLE")
                elif not (ytdlp_vez.proxy_url() and anime_fetch._banda_proxy_livre() > 25):
                    logging.warning("[auto] yt-dlp em pausa (YouTube barrando o IP) e sem banda de emergência no "
                                    "proxy — rodada encerrada sem gastar candidatos")
                    break
                else:
                    logging.warning(f"[auto] IP em pausa — {c['id']} vai pelo download de EMERGÊNCIA do proxy")
            if short_local:
                ok = fazer_short(c, target_lines=None, dry_run=args.dry_run,
                                use_worker=False)
            else:
                ok = fazer_short(c, target_lines=None, dry_run=args.dry_run,
                                use_worker=True,
                                worker_host=args.worker_host,
                                worker_port=args.worker_port)
            if not ok and ytdlp_vez.pausado():  # falha da máquina (IP barrado no meio): volta pra fila, como no ocioso
                tent = _feitos_path("short_attempted")
                tent.write_text("".join(l + "\n" for l in tent.read_text(encoding="utf-8").split() if l != c["id"]),
                                encoding="utf-8")
            elif not ok:
                _marca_feito(c["id"], "short_attempted")
            elif args.limit > 0:
                args.limit -= 1
                if args.limit <= 0:
                    break

    # ── Modo DEITADO ────────────────────────────────────────────────
    if args.modo in ("deitado", "ambos"):
        logging.info(">>> DEITADO — discover...")
        feitos = _ja_feitos("deitado")
        tentados = _ja_feitos("deitado_attempted")
        # 26/10: top=125 cortava ANTES de tirar os 735 feitos/tentados (os mais vistos) -> "nenhum candidato" com 819 na
        # busca; agora filtra a lista inteira (já vem ordenada por views)
        cands = [c for c in anime_discover.discover(top=100000)
                  if c["id"] not in feitos and c["id"] not in tentados][:args.top]
        if not cands:
            logging.warning("[auto] Nenhum candidato deitado disponível.")
        else:
            logging.info(f"[auto] {len(cands)} candidatos deitado novos. Engine={args.engine}")

        # both→deitado fica aqui (deitado = longo = mais seguro local)
        deitado_engine = "local" if (args.engine == "both") else args.engine
        deitado_local = (deitado_engine == "local")

        import ytdlp_vez
        for c in cands:
            if ytdlp_vez.pausado():  # IP barrado: não gastar candidato (ficaria em deitado_attempted pra sempre)
                logging.warning("[auto] yt-dlp em pausa (YouTube barrando o IP) — rodada encerrada sem gastar candidatos")
                break
            if deitado_local:
                ok = fazer_deitado(c, args.target_lines, args.dry_run,
                                  use_worker=False)
            else:
                ok = fazer_deitado(c, args.target_lines, args.dry_run,
                                  use_worker=True,
                                  worker_host=args.worker_host,
                                  worker_port=args.worker_port)
            if ok and args.limit > 0:
                args.limit -= 1
                if args.limit <= 0:
                    break

if __name__ == "__main__":
    main()
