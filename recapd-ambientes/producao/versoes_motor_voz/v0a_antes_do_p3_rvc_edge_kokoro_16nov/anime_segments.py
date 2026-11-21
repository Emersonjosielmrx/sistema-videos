"""anime_segments.py — corta o vídeo-fonte em clipes sincronizados com a narração.

Módulo isolado que faz o loop principal:
  1. narra cada frase (anime_tts)
  2. mede a duração real do áudio (anime_probe)
  3. corta a fatia correspondente do vídeo-fonte, descaracterizada (fx_clips)

Retorna a lista de caminhos dos clipes gerados, na ordem.
O offset no vídeo-fonte dá loop quando a soma das falas passa do fim do vídeo.
"""
import os
import time
import json
import random
import logging
import re
import shutil
import subprocess
from pathlib import Path

from fx_clips import build_clip_from_video, sfx_gap_s
from anime_probe import audio_duration, video_duration
from fx_detect import pick_sfx_for_text, sfx_duration
from anime_tts import narrate

ULTIMOS_FALANTES = None  # 23/10: quem fala cada entry do último build_segments (formato com várias vozes)
PAUSAS = {}  # 29/10: {índice da frase: (webm da mascote, lado, k)} — CTAs que viram a pausa com a voz dela
_POOL_CLIPES = None  # 02/11: pool de clipes em paralelo (ANIME_CLIPES_PARALELO), criado no 1º build_segments


def _fala_do_short(audio_wav, out_dir, i):
    """Short (vertical), dono 22/10: MICROCORTES obrigatórios — "cortar as pausas entre as falas, em vez de acelerar
    a fala", e "bom pros CURTOS, não pros longos". O áudio é o mesmo pras duas orientações, então o corte vai numa
    CÓPIA (fala_<i>.wav + words.json). 23/10: a dona ouviu o teste no vídeo longo e aprovou ("ficou bom") — vale nas
    duas orientações (o respiro ENTRE as falas do deitado segue o CLIP_GAP_S dele). Falhou = a fala original."""
    try:
        import narracao_curva
        dst = Path(out_dir) / f"fala_{i}.wav"
        shutil.copy2(audio_wav, dst)
        wj, dj = Path(str(audio_wav) + ".words.json"), Path(str(dst) + ".words.json")
        if wj.exists():
            shutil.copy2(wj, dj)
        else:
            dj.unlink(missing_ok=True)
        narracao_curva.microcortes(dst)
        return dst
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[segments] microcortes da frase {i} falhou ({e}) — fala original")
        return audio_wav


def _voz_depois_do_sfx(audio_wav, sfx_dur, dst):
    """(wav com silêncio no começo, segundos). Falhou = (original, 0) e o SFX volta a misturar."""
    gap = sfx_gap_s(sfx_dur)
    if not gap:
        return audio_wav, 0.0
    ms = int(gap * 1000)
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(audio_wav), "-af", f"adelay={ms}:all=1",
                        str(dst)], check=True, capture_output=True, timeout=60)
        return dst, gap
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[sfx] silêncio antes da voz falhou ({type(e).__name__}) — SFX misturado")
        return audio_wav, 0.0


AVANCO_MIN = 0.6  # cada corte anda pelo menos 60% da fala anterior


def _desprender(base, narradas, n_res, src_dur):
    """01/11 dona (imagem ~1 min na tela com raio pra ela mesma): o roteiro voltava no tempo e o "nunca volta" segurava
    as frases seguintes no mesmo segundo (ssMb: 26 frases em 5368 s; VgQU 16; XNKC 9). Cada corte anda no mínimo
    AVANCO_MIN da fala anterior: o vídeo segue quase em velocidade real e alcança o roteiro depois (narração < original)."""
    presas = 0
    for k in range(1, len(base)):
        if narradas[k][0] < n_res or narradas[k - 1][0] < n_res:
            continue
        piso = min(base[k - 1] + AVANCO_MIN * narradas[k - 1][3], max(0.0, src_dur - narradas[k][3] - 0.05))
        if base[k] < piso:
            base[k] = piso
            presas += 1
    if presas:
        logging.info(f"[segments] {presas} cortes empurrados pra frente (frases presas no mesmo plano)")


def _inicios(narradas, tempos, src_dur, trocas=None):
    """Segundo do original onde começa o corte de cada frase do Short. tempos (alinhado às frases do roteiro) = o que a
    frase narra; sem tempos = frases espalhadas pelo original inteiro na proporção da narração. Sempre crescente e
    sem passar do fim (corte + fala <= duração do original: nada de imagem parada no fim)."""
    total = sum(d for *_r, d in narradas) or 1.0
    escala = src_dur / total
    ok = bool(tempos) and all(isinstance(tempos[i], (int, float)) for i, *_r in narradas if i < len(tempos)) \
        and len(tempos) > max(i for i, *_r in narradas)
    # 28/10: as ANIME_RESUMO_N primeiras frases são o resumo de abertura do longo (anime-pipeline._resumo_longo): cada uma
    # mostra um momento de qualquer ponto da história e a trava "nunca volta no tempo" não vale pra elas — a história
    # que vem depois começa do zero, senão ficaria toda presa no último momento do resumo.
    try:
        n_res = int(os.environ.get("ANIME_RESUMO_N") or 0) if ok else 0
    except ValueError:
        n_res = 0
    base, acum, ant = [], 0.0, 0.0
    for i, _line, _wav, d in narradas:
        t = float(tempos[i]) if ok else acum * escala
        if i >= n_res:
            t = max(ant, t)                          # nunca volta no tempo
            ant = t
        base.append(min(t, max(0.0, src_dur - d - 0.05)))  # o corte inteiro cabe dentro do original
        acum += d
    _desprender(base, narradas, n_res, src_dur)
    out, ant = [], 0.0
    for (i, _line, _wav, d), t in zip(narradas, base):
        if trocas:  # 28/10 (Hypit): começa na troca de cena mais perto (±1,5 s), dentro das mesmas travas e sempre
            # DEPOIS do corte anterior (2 frases na mesma troca = take repetido, defeito que o júri pune)
            piso = (ant + 0.5 if out else 0.0) if i >= n_res else 0.0
            t = _encostar_na_troca(t, trocas, piso, max(0.0, src_dur - d - 0.05))
        out.append(round(t, 2))
        if i >= n_res:
            ant = t
    # 30/10: o teto "cabe no original" vem DEPOIS do "nunca volta", então as últimas frases (CTA/loop com tempo perto do
    # fim) recuavam pra dentro do trecho da anterior — fim com o mesmo plano repetido ("55 54", "70 70", "56 57 58").
    # Passada de trás pra frente: cada corte termina antes do próximo começar, adiantando a imagem no máximo
    # RECUO_MAX_S (dona 25/10: a fala pode vir ANTES da cena, nunca depois). Narração maior que o original ainda
    # sobrepõe um pouco, mas nunca 2 frases no mesmo plano.
    RECUO_MAX_S = 8.0
    nxt, orig_out = src_dur, list(out)
    for j in range(len(out) - 1, -1, -1):
        if narradas[j][0] < n_res:
            break
        lim = nxt - narradas[j][3] - 0.05
        if out[j] > lim:
            out[j] = round(max(0.0, orig_out[j] - RECUO_MAX_S, lim), 2)
        nxt = out[j]
    for j in range(1, len(out)):  # e continua sempre crescente
        if narradas[j][0] >= n_res and out[j] < out[j - 1] + 0.5:
            out[j] = round(min(out[j - 1] + 0.5, max(0.0, src_dur - narradas[j][3] - 0.05)), 2)
    logging.info(f"[segments] cortes {'pelos tempos do roteiro' if ok else 'espalhados pelo original (proporção)'}: "
                 + " ".join(f"{x:.0f}" for x in out) + f" (original {src_dur:.0f}s, narração {total:.0f}s)")
    return out


# 28/10 (linha CORTES, frente 4 + regra 21 do júri): trecho quase preto da fonte (transição, cena noturna sem luz) caía
# em frase inteira do Short = tela escura narrada. Brilho médio (Y) da fonte a 2 quadros/s; janela da frase escura =
# corte desliza até ESCURO_BUSCA_S pro trecho claro mais perto (sem voltar antes do corte anterior). Falhou = como antes.
ESCURO_Y = 24          # brilho RGB 0-255 (preto de vídeo ~0-16 depois da conversão)
ESCURO_FRACAO = 0.6    # >= 60% da janela escura = frase "no escuro"
ESCURO_BUSCA_S = 4.0


# 28/10 (Hypit, packages/media-local files.ts visualBoundaries): 1 leitura da fonte a 12 quadros/s em 32x32 RGB dá as
# TROCAS DE CENA (diferença média absoluta entre quadros vizinhos / 255 >= 0,1) e o BRILHO por meio segundo. Cache
# _analise_fonte.json ao lado do vídeo (as duas orientações e as outras línguas reusam).
TROCA_FPS, TROCA_LIMIAR, TROCA_ENCOSTA_S = 12, 0.1, 1.5
_LADO = 32 * 32 * 3


def _analise_fonte(video_path):
    cache = Path(video_path).parent / "_analise_fonte.json"
    try:
        d = json.loads(cache.read_text(encoding="utf-8"))
        if d.get("v") == 1 and d.get("tam") == Path(video_path).stat().st_size:
            return d
    except (OSError, ValueError):
        pass
    try:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-skip_loop_filter", "all", "-i", str(video_path), "-an", "-vf",
                              f"fps={TROCA_FPS},scale=32:32,format=rgb24", "-f", "rawvideo", "-"],
                             capture_output=True, timeout=300).stdout
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[segments] análise da fonte indisponível ({type(e).__name__}) — cortes como antes")
        return {"trocas": [], "brilho": []}
    try:
        import numpy as np
        q = np.frombuffer(raw[:len(raw) // _LADO * _LADO], dtype=np.uint8).reshape(-1, 32 * 32, 3).astype(np.int16)
        dif = (np.abs(q[1:] - q[:-1]).mean(axis=(1, 2)) / 255.0) if len(q) > 1 else np.array([])
        luma = (q[..., 0] * 0.299 + q[..., 1] * 0.587 + q[..., 2] * 0.114).mean(axis=1)
        trocas = [round(float(k + 1) / TROCA_FPS, 2) for k in np.nonzero(dif >= TROCA_LIMIAR)[0]]
        meio = TROCA_FPS // 2
        brilho = [round(float(luma[k:k + meio].mean()), 1) for k in range(0, len(luma), meio)]
    except ImportError:
        frames = [raw[k:k + _LADO] for k in range(0, len(raw) - _LADO + 1, _LADO)]
        trocas = [round(k / TROCA_FPS, 2) for k in range(1, len(frames))
                  if sum(abs(a - b) for a, b in zip(frames[k], frames[k - 1])) / _LADO / 255 >= TROCA_LIMIAR]
        lum = [sum(f[0::3]) * 0.299 / 1024 + sum(f[1::3]) * 0.587 / 1024 + sum(f[2::3]) * 0.114 / 1024 for f in frames]
        brilho = [round(sum(lum[k:k + 6]) / len(lum[k:k + 6]), 1) for k in range(0, len(lum), 6)]
    d = {"v": 1, "tam": Path(video_path).stat().st_size, "trocas": trocas, "brilho": brilho}
    try:
        cache.write_text(json.dumps(d), encoding="utf-8")
    except OSError:
        pass
    return d


def _brilho_por_meio_segundo(video_path):
    return _analise_fonte(video_path).get("brilho") or []


def _encostar_na_troca(t, trocas, piso, teto):
    """Início do corte -> troca de cena mais perto dentro de ±TROCA_ENCOSTA_S, sem sair de [piso, teto]."""
    perto = [x for x in trocas if abs(x - t) <= TROCA_ENCOSTA_S and piso <= x <= teto]
    return min(perto, key=lambda x: abs(x - t)) if perto else t


def _fracao_escura(ys, ini, d):
    a, b = int(ini * 2), max(int(ini * 2) + 1, int((ini + d) * 2))
    jan = ys[a:b]
    return sum(y < ESCURO_Y for y in jan) / len(jan) if jan else 0.0


def _fugir_do_escuro(video_path, plano, src_dur):
    ys = _brilho_por_meio_segundo(video_path)
    if not ys or sum(y < ESCURO_Y for y in ys) == 0:
        return plano
    out, ant, mudou = [], 0.0, []
    for i, line, wav, d, ini in plano:
        if _fracao_escura(ys, ini, d) >= ESCURO_FRACAO:
            melhor = None
            for k in range(1, int(ESCURO_BUSCA_S * 2) + 1):
                for t in (ini + k / 2, ini - k / 2):
                    if ant <= t <= max(0.0, src_dur - d - 0.05) and _fracao_escura(ys, t, d) < 0.25:
                        melhor = t
                        break
                if melhor is not None:
                    break
            if melhor is not None:
                mudou.append(f"{ini:.1f}->{melhor:.1f}")
                ini = round(melhor, 2)
        out.append((i, line, wav, d, ini))
        ant = ini
    if mudou:
        logging.info(f"[segments] fugiu do escuro em {len(mudou)} frase(s): {' '.join(mudou)}")
    return out


def _falas_mascote(lines, originais, audio_dir):
    """Dona 28/10 ("não há mascote aparecendo ou falando; dar voz à mascote"): as frases ANIME_MASCOTE_FALAS (índices,
    o anime-pipeline marca os CTAs do longo) saem com a voz DELA (ANIME_MASCOTE_VOZ, edge; tom/velocidade em
    ANIME_MASCOTE_TOM) e com o texto original (o revezamento reescreveria no jeito do narrador). O áudio fica pronto
    antes do clone, que pula o que já existe. Falhou = a frase fica com o narrador, como antes."""
    try:
        idx = {int(x) for x in os.environ.get("ANIME_MASCOTE_FALAS", "").split(",") if x.strip()}
    except ValueError:
        idx = set()
    voz = os.environ.get("ANIME_MASCOTE_VOZ", "")
    if not idx or not voz or audio_dir is None:
        return lines
    # 29/10 dona ("não ouvi a voz dela; o vídeo atrás fica em loop borrado na hora dela falar"): com gravação viva de
    # texto conhecido, a frase vira a PAUSA DELA — o texto e a voz do próprio vídeo (o áudio fica pronto aqui e o TTS
    # pula), montada no laço por mascote_overlay.montar_pausa. Sem gravação = a fala clonada de antes.
    if os.environ.get("ANIME_MASCOTE_PAUSA", "1") == "1":
        import mascote_overlay
        lines = list(lines)
        ordem = sorted(idx)
        # 01/11 dona: "a mascote quase sempre está com a mesma roupa de ninja no começo" — k começava em 0 em todo vídeo
        # e a 1ª gravação (ordem alfabética) era sempre a ninja; o deslocamento por vídeo varia a roupa
        import hashlib
        desl = int(hashlib.md5(str(Path(audio_dir).resolve()).encode()).hexdigest(), 16) % 997
        for k, i in enumerate(ordem):
            if i >= len(lines) or (Path(audio_dir) / f"audio_{i}.wav").exists():
                continue
            # 30/10: a fala tem que caber no ponto do vídeo (o CTA do fim é a última frase) e não repetir gravação
            pos = "fim" if i == len(lines) - 1 else ("inicio" if k == 0 and len(ordem) > 1 else "meio")
            esc = mascote_overlay.pausa_viva(originais[i] if i < len(originais) else lines[i], k + desl, posicao=pos,
                                             usados={w for w, _l, _k in PAUSAS.values()})
            if not esc:
                continue
            webm, fala, lado = esc
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", webm, "-vn", "-ac", "2", "-ar", "44100",
                                "-c:a", "pcm_s16le", str(Path(audio_dir) / f"audio_{i}.wav")], capture_output=True)
            if r.returncode == 0:
                lines[i] = fala
                PAUSAS[i] = (webm, lado, k)
        if PAUSAS:
            logging.info(f"[mascote] {len(PAUSAS)} CTAs viram pausa com a voz dela: "
                         + ", ".join(f"{i}={Path(w).stem}" for i, (w, _l, _k) in sorted(PAUSAS.items())))
        idx -= set(PAUSAS)
        if not idx:
            return lines
    # 28/10 dona: "vozes do edge PURAS (Thalita, Antonio, Francisca) nunca — só com o clone por cima". A mascote sai
    # com a voz clonada ANIME_MASCOTE_CLONE (config mascote.voz_clone); sem clone nesta máquina = fica com o narrador.
    import anime_tts
    clone = os.environ.get("ANIME_MASCOTE_CLONE", "")
    if not clone or not anime_tts.clone_ligado() or not (anime_tts.VOZES_DIR / clone / f"{clone}.pth").exists():
        logging.info("[mascote] sem voz clonada da mascote nesta máquina — as falas dela ficam com o narrador")
        return lines
    lines = list(lines)
    for i in idx:
        if i < len(lines) and i < len(originais):
            lines[i] = originais[i]
    antes = os.environ.get("VOZ_CLONADA")
    try:
        os.environ["VOZ_CLONADA"] = clone
        anime_tts.preparar_clone(lines, audio_dir, [], so={i for i in idx if i < len(lines)}, abertura=False)
        logging.info(f"[mascote] {len(idx)} falas com a voz clonada {clone}")
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[mascote] clone {clone} falhou ({type(e).__name__}: {e}) — falas com o narrador")
    finally:
        if antes is not None:
            os.environ["VOZ_CLONADA"] = antes
    return lines



def _falas_personagem(lines, originais, audio_dir, impactos):
    """Dona 28/10 (como o Mike: o narrador faz a voz do personagem): ANIME_PERSONAGEM_FALAS = JSON {índice: voz
    clonada} (anime-pipeline._falas_personagem). Cada fala sai com a voz do personagem (Applio, como o revezamento)
    e o texto original (o revezamento reescreveria). Voz que não chegou nesta máquina / sem clone = a frase fica com
    o narrador."""
    import anime_tts
    try:
        marc = {int(k): v for k, v in json.loads(os.environ.get("ANIME_PERSONAGEM_FALAS") or "{}").items()}
    except (ValueError, AttributeError):
        marc = {}
    if not marc or audio_dir is None or not anime_tts.clone_ligado():
        return lines
    lines = list(lines)
    for i in marc:
        if i < len(lines) and i < len(originais):
            lines[i] = originais[i]
    antes = os.environ.get("VOZ_CLONADA")
    try:
        for voz in dict.fromkeys(marc.values()):
            if not (anime_tts.VOZES_DIR / voz / f"{voz}.pth").exists():
                logging.warning(f"[personagem] voz {voz} não está nesta máquina — falas ficam com o narrador")
                continue
            os.environ["VOZ_CLONADA"] = voz
            try:
                anime_tts.preparar_clone(lines, audio_dir, impactos, so={i for i, v in marc.items() if v == voz},
                                         abertura=False)
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[personagem] voz {voz} falhou ({type(e).__name__}: {e}) — ficam com o narrador")
    finally:
        if antes is not None:
            os.environ["VOZ_CLONADA"] = antes
    logging.info(f"[personagem] {len(marc)} falas com voz de personagem ({', '.join(dict.fromkeys(marc.values()))})")
    return lines


_DUR_SUSPEITAS = {"n": 0}


def _duracao_sa(wav, texto, out_dir, i):
    """04/11 (pesquisa, zenstory "tts-hallucination-duration-bound"; dona: "faça as ideias que valem a pena"): fala com
    duração absurda pro tamanho do texto (edge/clone deixou silêncio grande no começo/fim, ou voz arrastada) deixa o
    vídeo parado e a legenda esperando. > 2x o esperado (2,6 palavras/s) + 2 s = corta o silêncio > 0,5 s do FIM
    (o começo fica: a legenda conta dele). Só encurta; nunca troca a voz. Conta e loga (o QA do longo vê no log)."""
    try:
        palavras = max(1, len(str(texto).split()))
        d = audio_duration(wav)
        lim = 2.0 * palavras / 2.6 + 2.0
        if d <= lim:
            return wav
        _DUR_SUSPEITAS["n"] += 1
        limpo = Path(out_dir) / f"_dur_ok_{i}.wav"
        # só o FIM: o tempo de cada palavra da legenda conta a partir do começo do áudio (cortar o começo adiantaria
        # a legenda dessa frase)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af",
                        "areverse,silenceremove=start_periods=1:start_duration=0:start_threshold=-45dB,areverse,"
                        "apad=pad_dur=0.25", str(limpo)], check=True, timeout=120)
        d2 = audio_duration(str(limpo))
        logging.warning(f"[voz] frase {i}: {d:.1f} s pra {palavras} palavras (limite {lim:.1f}) — fim mudo cortado: "
                        f"{d2:.1f} s")
        return str(limpo) if 0.3 < d2 < d else wav
    except Exception as e:  # noqa: BLE001
        logging.info(f"[voz] conferência de duração pulada na frase {i} ({type(e).__name__})")
        return wav


_VEZ_CPU = {"fh": None}


def _vez_da_cpu():
    """04/11 dona ("tem horas que a CPU roda no Kaggle e a GPU fica parada, e vice-versa — se os 2 rodarem sempre a 100%
    pode ser muito mais rápido"): na sessão do Kaggle dois longos andam juntos. Tudo ANTES daqui (transcrição, roteiro,
    narradores, Edge, voz clonada na GPU) quase não usa CPU; daqui pra frente (clipes, junção, música, legenda) é CPU
    pura. Só UM longo por vez passa deste ponto: trava de arquivo (TRAB_CPU_LOCK, posta pelo kaggle_trabalhador) que o
    sistema solta sozinho quando o processo termina. Ao pegar, grava TRAB_FASE_CPU_ARQ (o trabalhador vê e começa a
    adiantar o próximo). Sem a variável (PC, VPS, Shorts) = não espera nada, como antes."""
    trava = os.environ.get("TRAB_CPU_LOCK")
    if not trava or _VEZ_CPU["fh"] is not None:
        return
    try:
        import fcntl
    except ImportError:
        return
    t0 = time.time()
    fh = open(trava, "a+")
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)  # espera o outro longo sair da parte de CPU
    _VEZ_CPU["fh"] = fh  # segura até o fim do processo
    espera = time.time() - t0
    logging.info(f"[cpu] vez da CPU {'na hora' if espera < 5 else f'depois de {espera / 60:.0f} min esperando o outro longo'}")
    marca = os.environ.get("TRAB_FASE_CPU_ARQ")
    if marca:
        try:
            Path(marca).write_text(str(time.time()), encoding="utf-8")
        except OSError:
            pass


def build_segments(video_path, lines, out_dir, audio_dir=None, orient="landscape", tempos=None):
    """Gera um clipe por frase. Retorna (clips, entries, sfx_durs, word_times).

    clips:      [caminhos_dos_clipes] na ordem.
    entries:    [(texto, duracao_s), ...] alinhado aos clipes (pra legenda).
    sfx_durs:   [duracao_sfx_s, ...] alinhado aos clipes.
    word_times: [[[start_rel,end_rel,palavra],...] | None, ...] alinhado aos
                clipes — timing REAL por palavra do edge-tts (sidecar .words.json),
                relativo ao início do áudio do clipe. None quando o sidecar falta.

    video_path: mp4 fonte (anime cru).
    lines: lista de frases do roteiro.
    out_dir: Path onde salvar os clip_N.mp4 (por orientação).
    audio_dir: Path onde ficam os audio_N.wav. Default = out_dir. Passar um
               dir COMPARTILHADO faz o áudio TTS ser gerado 1x e reusado nas
               duas orientações (não regera nem gasta proxy à toa).
    orient: "landscape" (16:9) ou "vertical" (9:16) — controla o enquadramento
            via env ANIME_ORIENT lido dentro de build_clip_from_video.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = Path(audio_dir) if audio_dir else out_dir
    audio_dir.mkdir(parents=True, exist_ok=True)

    os.environ["ANIME_ORIENT"] = orient

    src_dur = video_duration(video_path)  # pra dar loop no corte
    if src_dur <= 0:
        # 25/10: no Kaggle o original tinha sumido (outro trabalhador limpou a pasta) e o pipeline narrou as 582 frases
        # por 2 h com todos os cortes falhando. Sem original legível não há vídeo: para na hora.
        logging.error(f"[segments/{orient}] vídeo de origem ilegível ou ausente ({video_path}) — nada a fazer")
        return [], [], [], []
    global_time = 0.0
    PAUSAS.clear()
    clips = []
    entries = []
    sfx_durs = []
    word_times = []

    # curva de locutor (hipercool, 17/10): impactos escolhidos 1x por vídeo, guardados ao lado da fonte
    # (_impactos.json) — as duas orientações e as versões nas outras línguas usam os mesmos
    impactos = []
    try:
        import narracao_curva
        if narracao_curva.ligado():
            impactos = narracao_curva.escolher_impactos(lines, Path(video_path).parent / "_impactos.json")
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[segments] curva de narração indisponível ({type(e).__name__}: {e}) — voz plana")

    import anime_tts
    import anime_formatos
    falas = anime_formatos.falas_do_video(Path(video_path).parent)  # dono 23/10: Short com várias vozes (desligado sem o arquivo)
    # 26/10 (dona): revezamento de narradores no longo — VOZ_CLONADA_LISTA="voz1,voz2,...": cada voz narra um bloco
    # seguido, com uma passagem engraçada na troca e o nome dela na legenda (pra ela escolher quais servem pra manhwa)
    vozes_rev = [v.strip() for v in os.environ.get("VOZ_CLONADA_LISTA", "").split(",") if v.strip()]
    dono_rev = None
    originais = list(lines)
    if falas and len(falas) == len(lines):
        anime_formatos.preparar_formato(falas, audio_dir)
    elif anime_tts.clone_ligado() and len(vozes_rev) >= 2:
        lines, dono_rev = anime_tts.revezar(lines, vozes_rev)
        lines = _falas_mascote(lines, originais, audio_dir)
        lines = _falas_personagem(lines, originais, audio_dir, impactos)
        anime_tts.preparar_revezamento(lines, dono_rev, audio_dir, impactos)
    elif anime_tts.clone_ligado():  # voz clonada do parceiro: todas as frases de uma vez (falhou = o vídeo não sai)
        lines = _falas_mascote(lines, originais, audio_dir)
        lines = _falas_personagem(lines, originais, audio_dir, impactos)
        anime_tts.preparar_clone(lines, audio_dir, impactos)
    else:
        lines = _falas_mascote(lines, originais, audio_dir)
    # 23/10: cor/nome de quem fala na legenda (só formato com 2+ vozes); falhou = legenda normal
    global ULTIMOS_FALANTES
    ULTIMOS_FALANTES, quem = None, None
    if falas and len(falas) == len(lines):
        try:
            quem = anime_formatos.falantes_legenda(falas, impactos)  # + ênfase/impacto (23/10)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[segments] cor/nome da legenda por voz indisponível ({type(e).__name__}: {e}) — legenda normal")
    # dona 26/10: nome do narrador na legenda estraga o vídeo pra postar — revezamento usa a legenda normal
    # 27/10: ênfase/impacto também no Short solo (1 voz) — mesma seleção de palavras, só sem cor/nome de voz
    if not quem and orient == "vertical":
        try:
            quem = anime_formatos.enfase_solo(lines, impactos)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[segments] ênfase solo indisponível ({type(e).__name__}: {e})")
    falantes = [] if quem else None
    pendentes = []  # futuro do pool por clipe (None = feito em série)
    # 02/11 (pesquisa H6): no Kaggle os ~800 clipes saíam 1 por vez com a GPU parada. ANIME_CLIPES_PARALELO=N (o
    # kaggle_trabalhador põe 3) = N clipes ao mesmo tempo; 1/vazio = como antes (PC, Shorts)
    global _POOL_CLIPES
    try:
        n_par = int(os.environ.get("ANIME_CLIPES_PARALELO") or 1)
    except ValueError:
        n_par = 1
    if n_par > 1 and _POOL_CLIPES is None:
        from concurrent.futures import ThreadPoolExecutor
        _POOL_CLIPES = ThreadPoolExecutor(max_workers=n_par)

    # Short (vertical), dono 21/10: o corte era em sequência a partir do 0 — a frase não caía no quadro que ela narra, o
    # Short mostrava só o começo do original (fim abrupto) e a última frase passava do fim (imagem parada). Agora narra
    # tudo antes e cada frase começa no segundo do original que ela narra (roteiro com tempo) ou, sem tempos, as frases
    # se espalham pelo original inteiro; nenhum corte passa do fim do vídeo.
    # 22/10 (dono: "sincronia com as falas do original, não falar de imagem que já passou/vai passar"): o DEITADO
    # entra no mesmo plano — a narração dura ~55% do original e o corte sequencial fazia a 2ª metade do original
    # nunca aparecer (dessincronia que só crescia). Com tempos usa os tempos; sem, espalha na proporção.
    plano = None
    if src_dur > 0:
        narradas = []
        for i, line in enumerate(lines):
            audio_wav = narrate(line, audio_dir / f"audio_{i}.wav", indice=i, impactos=impactos, total=len(lines))
            if audio_wav is None:
                logging.error(f"[segments] pulando frase {i} (TTS falhou)")
                continue
            if i not in PAUSAS:  # a fala da mascote fica inteira (a boca no vídeo segue o áudio dela)
                audio_wav = _fala_do_short(audio_wav, out_dir, i)  # dona 23/10: microcortes também no deitado
                audio_wav = _duracao_sa(audio_wav, line, out_dir, i)
            d = audio_duration(audio_wav)
            if d <= 0:
                logging.error(f"[segments] áudio {i} sem duração — pulando")
                continue
            narradas.append((i, line, audio_wav, d))
        # 30/10: no Short, frase sem áudio = história com buraco (28/10 QjidaJbpEx4 saiu com 1 de 10 frases, 4 s, e foi
        # publicado). Vertical: nenhuma perda tolerada — devolve vazio e o anime-pipeline para ("nenhum clipe").
        if orient == "vertical" and len(narradas) < len(lines):
            logging.error(f"[segments/{orient}] {len(lines) - len(narradas)} de {len(lines)} frases sem áudio — "
                          "Short incompleto não sai")
            return [], [], [], []
        # 28/10 dona aprovou no longo também (+4%: 1 leitura da fonte inteira) — ANIME_TROCA_LONGO=1 (config/longo.json)
        trocas = (_analise_fonte(video_path).get("trocas")
                  if orient == "vertical" or os.environ.get("ANIME_TROCA_LONGO") == "1" else None)
        plano = [(i, line, wav, d, ini) for (i, line, wav, d), ini
                 in zip(narradas, _inicios(narradas, tempos, src_dur, trocas))]
        if orient == "vertical":
            plano = _fugir_do_escuro(video_path, plano, src_dur)
        # 22/10 (dono: "monitorar quais falas icônicas ficam estranhas"): só as frases com bordão/mania do narrador são
        # transcritas e comparadas; o que sai estranho 2x sai do roteiro (monitor_bordoes.py). Nunca derruba o vídeo.
        try:
            import monitor_bordoes
            if falas and len(falas) == len(lines):  # formato (23/10): cada voz confere os bordões dela
                for voz in sorted({x["voz"] for x in falas}):
                    monitor_bordoes.conferir(voz, [(line, wav) for i, line, wav, _d in narradas if falas[i]["voz"] == voz])
            else:
                monitor_bordoes.conferir(os.environ.get("VOZ_CLONADA"), [(line, wav) for _i, line, wav, _d in narradas])
        except Exception as e:  # noqa: BLE001
            logging.info(f"[segments] monitor de bordões pulado ({type(e).__name__}: {e})")

    _vez_da_cpu()
    for i, line, audio_wav, clip_dur, inicio in (plano if plano is not None else
                                                  ((i, line, None, None, None) for i, line in enumerate(lines))):
        if plano is None:
            audio_wav = narrate(line, audio_dir / f"audio_{i}.wav", indice=i, impactos=impactos, total=len(lines))
            if audio_wav is None:
                logging.error(f"[segments] pulando frase {i} (TTS falhou)")
                continue
            audio_wav = _fala_do_short(audio_wav, out_dir, i)  # dona 23/10: microcortes também no deitado

            clip_dur = audio_duration(audio_wav)
            if clip_dur <= 0:
                logging.error(f"[segments] áudio {i} sem duração — pulando")
                continue

        cut_at = inicio if inicio is not None else (global_time % src_dur if src_dur > 0 else global_time)
        clip_out = str(out_dir / f"clip_{i}.mp4")
        logging.info(f"[segments/{orient}] clipe {i}: corte@{cut_at:.1f}s dur={clip_dur:.2f}s")

        sfx_path, _sfx_vol = pick_sfx_for_text(line, "")  # retorna (path, volume)
        sfx_dur = sfx_duration(sfx_path) if sfx_path else 0.0
        gap, wav_fala = 0.0, audio_wav
        if sfx_path and i not in PAUSAS and sfx_dur > 0:
            audio_wav, gap = _voz_depois_do_sfx(audio_wav, sfx_dur, out_dir / f"voz_sfx_{i}.wav")
            clip_dur += gap
        ok = None
        if i in PAUSAS:  # 29/10: a pausa da mascote (voz dela, cena em loop borrada atrás)
            import mascote_overlay
            from fx_assets import W as _w, H as _h
            webm, lado, k = PAUSAS[i]
            amiga = mascote_overlay.amiga_viva(k // 3, so_pedido=True) if k % 3 == 1 else None  # 1 a cada 3 pausas
            ok = mascote_overlay.montar_pausa(video_path, cut_at, webm, audio_wav, clip_out, _w, _h, k, lado, amiga)
            if ok:
                sfx_dur = 0.0
                if amiga:  # 31/10: a amiga fala depois da Maria — o trecho ficou mais longo que a fala dela
                    clip_dur = max(clip_dur, video_duration(clip_out))
                logging.info(f"[mascote] pausa {i}: {Path(webm).stem} ({clip_dur:.1f} s)")
            else:
                logging.warning(f"[mascote] pausa {i} não montou — vira clipe normal com a voz dela")
        futuro = None
        if not ok:
            kw_clip = dict(video_source=video_path, audio_path=str(audio_wav), out_path=clip_out, panel_idx=i,
                           effects_mgr=None, global_start_t=cut_at, clip_duration=clip_dur, subtitles=line,
                           sfx=sfx_path, impacto=i in impactos)
            if _POOL_CLIPES is not None:
                import fx_clips as _fxc  # escolhas que dependem da ordem: aqui, em ordem
                kw_clip["decisao"] = _fxc.decidir_trecho(i, i in impactos, line)
                # 02/11 (pesquisa H6): o clipe (só ffmpeg + detecção do trecho) vai pro pool; a narração continua em
                # ordem neste loop. O resultado entra na lista na MESMA posição (ordem do vídeo não muda)
                futuro = _POOL_CLIPES.submit(build_clip_from_video, **kw_clip)
                ok = True
            else:
                ok = build_clip_from_video(**kw_clip)
        # avança o tempo mesmo se o clipe falhar, pra manter o alinhamento do corte.
        global_time += clip_dur
        if not ok:
            logging.error(f"[segments/{orient}] clipe {i} inválido — pulando (não entra no concat)")
            continue
        # Timing REAL por palavra: sidecar irmão do wav, gerado pelo edge-tts
        # (edge_tts_engine._move_words_sidecar). [[start_rel,end_rel,palavra],...]
        # relativo ao início do áudio do clipe. None quando o sidecar falta (ex:
        # TTS que não emitiu WordBoundary) — a legenda cai na estimativa por len().
        wt = None
        try:
            wj = Path(str(wav_fala) + ".words.json")
            if wj.exists():
                data = json.loads(wj.read_text(encoding="utf-8"))
                if isinstance(data, list) and data:
                    wt = [[s + gap, e + gap, *resto] for s, e, *resto in data] if gap else data
        except Exception as e:
            logging.warning(f"[segments] falha lendo words.json {i}: {e}")

        clips.append(clip_out)
        entries.append((line, clip_dur))
        sfx_durs.append(sfx_dur)
        word_times.append(wt)
        if falantes is not None:
            falantes.append(quem[i])
        pendentes.append(futuro)
        # 05/11 dona: fala REAL do narrador (reação/piada/bordão do banco dele) depois de uma frase forte
        try:
            dono_i = (dono_rev[i] if dono_rev and i < len(dono_rev) else os.environ.get("VOZ_CLONADA") or "")
            real = _falas_reais.depois(video_path, out_dir, orient, i, line, clip_dur, dono_i, i in impactos,
                                       cut_at + clip_dur)
        except Exception as e:  # noqa: BLE001
            logging.info(f"[falas reais] pulada ({type(e).__name__}: {e})")
            real = None
        if real:
            clips.append(real[0])
            entries.append(real[1])
            sfx_durs.append(0.0)
            word_times.append(real[2])
            if falantes is not None:
                falantes.append(None)
            pendentes.append(None)

    # clipes do pool: espera todos; o que falhou sai das listas (igual ao "pulando" de antes), mantendo a ordem
    if any(f is not None for f in pendentes):
        manter = []
        for k, f in enumerate(pendentes):
            try:
                ok_k = True if f is None else bool(f.result())
            except Exception as e:  # noqa: BLE001
                logging.error(f"[segments/{orient}] clipe {clips[k]} falhou no pool ({type(e).__name__}: {e})")
                ok_k = False
            if not ok_k:
                logging.error(f"[segments/{orient}] {Path(clips[k]).name} inválido — pulando (não entra no concat)")
            manter.append(ok_k)
        clips = [c for c, m in zip(clips, manter) if m]
        entries = [c for c, m in zip(entries, manter) if m]
        sfx_durs = [c for c, m in zip(sfx_durs, manter) if m]
        word_times = [c for c, m in zip(word_times, manter) if m]
        if falantes is not None:
            falantes = [c for c, m in zip(falantes, manter) if m]

    intro = _clipe_intro(video_path, out_dir, plano)
    if intro:
        clips.insert(0, intro[0])
        entries.insert(0, intro[1])
        sfx_durs.insert(0, 0.0)
        word_times.insert(0, intro[2])
        if falantes is not None:
            falantes.insert(0, None)
    ULTIMOS_FALANTES = falantes  # [(cor_rgb, nome, extra)] alinhado a entries, ou None (lido pelo anime-pipeline, 23/10)
    return clips, entries, sfx_durs, word_times


class _FalasReais:
    """05/11/2026 dona ("as falas estão aprovadas de usar, essas aí já pode começar"): banco de falas ORIGINAIS de
    cada narrador (hermes-staging falas_narradores.py -> manhwa-drive:narradores_originais/<voz>/banco; o Kaggle
    copia pra <pasta do vídeo>/falas_reais/<voz>/). No longo (16:9), no bloco do narrador X, depois de uma frase forte
    (impacto, "!" ou "?"), entra 1 fala real de X (reação, piada, bordão, risada escrita), no máximo 1 a cada
    FALAS_REAIS_A_CADA s de vídeo (padrão 150) e sem repetir no vídeo. Os SONS (risada/grito detectados) só entram
    com "sons_aprovados": true no banco.json (a dona ouve antes). FALAS_REAIS=0 desliga."""
    CATS = ("reacao", "piada", "bordao", "risada", "transicao", "beleza")  # 12/11: + beleza (RES-peito, "que mulher")
    # 12/11 dona ("principalmente piadas e coisas de mulheres, RES-peito, trocadilhos, risadas"): essas vão primeiro
    PREFERIDAS = ("beleza", "piada", "risada")

    def __init__(self):
        self.dir, self.desde, self.usados, self.bancos = None, 0.0, set(), {}

    def _banco(self, pasta, voz):
        if voz not in self.bancos:
            b = pasta / "falas_reais" / voz
            itens = []
            try:
                bj = json.loads((b / "banco.json").read_text(encoding="utf-8"))
                for it in bj.get("itens") or []:
                    # 05/11 dona: "nem todas são risadas, do Momo só uma é risada mesmo" — o detector erra; som só
                    # entra com "aprovado": true NO ITEM (a dona ouviu aquele arquivo)
                    ok_cat = it.get("categoria") in self.CATS if it.get("tipo") == "fala" else it.get("aprovado") is True
                    # 12/11: o banco novo guarda a frase inteira até 10 s (+0,3 s de folga) — 6,5 jogava fora as longas
                    if ok_cat and 0.4 <= float(it.get("dur") or 0) <= 10.5 and (b / it["arquivo"]).exists():
                        itens.append({**it, "wav": b / it["arquivo"]})
            except (OSError, ValueError):
                pass
            random.shuffle(itens)
            if os.environ.get("FALAS_PREFERIDAS", "1") != "0":
                itens.sort(key=lambda it: it.get("categoria") not in self.PREFERIDAS)  # estável: mantém o sorteio
            self.bancos[voz] = itens
        return self.bancos[voz]

    def depois(self, video_path, out_dir, orient, i, line, clip_dur, voz, impacto, inicio):
        if os.environ.get("FALAS_REAIS", "1") == "0" or orient != "landscape" or not voz:
            return None
        if self.dir != str(out_dir):  # vídeo novo
            self.__init__()
            self.dir = str(out_dir)
        self.desde += clip_dur
        forte = impacto or str(line).rstrip().endswith(("!", "?"))
        # 12/11 dona ("as falas reais são muito boas, ampliar o máximo possível"): 1 a cada 60 s (era 150)
        if not forte or self.desde < float(os.environ.get("FALAS_REAIS_A_CADA", "60")) or i < 3:
            return None
        cands = [x for x in self._banco(Path(video_path).parent, voz) if x["arquivo"] not in self.usados]
        if not cands:
            return None
        esc = cands[0]
        self.usados.add(esc["arquivo"])
        aud = Path(out_dir) / f"fala_real_{i}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(esc["wav"]), "-af",
                        "afade=t=in:d=0.05,loudnorm=I=-16:TP=-1.5,apad=pad_dur=0.3", "-ar", "44100", "-ac", "2",
                        str(aud)], check=True, capture_output=True, timeout=60)
        dur = audio_duration(aud)
        texto = str(esc.get("texto") or "")
        out = str(Path(out_dir) / f"clip_fala_real_{i}.mp4")
        ok = build_clip_from_video(video_source=video_path, audio_path=str(aud), out_path=out, panel_idx=i,
                                   effects_mgr=None, global_start_t=inicio, clip_duration=dur, subtitles=texto,
                                   sfx=None, impacto=False)
        if not ok:
            return None
        self.desde = 0.0
        logging.info(f"[falas reais] {voz} depois da frase {i}: {esc['arquivo']} ({dur:.1f} s) '{texto[:60]}'")
        return out, (texto, dur), None


_falas_reais = _FalasReais()


def _clipe_intro(video_path, out_dir, plano):
    """01/11 dona: o longo abre com a fala REAL do narrador (intro_voz.wav + intro_voz.json que o cliente manda no
    pedido, cortada dos vídeos dele pelo hipercool intros_voz.py) e ele mesmo narra o resumo em seguida. Fim natural:
    corta 0,1 s depois da última palavra, fade de 0,15 s e 0,35 s de respiro. (clip, (texto, dur), word_times) ou None."""
    pasta = Path(video_path).parent
    wav, meta = pasta / "intro_voz.wav", pasta / "intro_voz.json"
    if os.environ.get("ANIME_ORIENT") != "landscape" or not wav.exists() or not meta.exists():
        return None
    try:
        d = json.loads(meta.read_text(encoding="utf-8"))
        pal = [(str(w), float(a), float(b)) for w, a, b in d["palavras"]]
        fim = pal[-1][2]
        aud = Path(out_dir) / "intro_voz_pronta.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af",
                        f"atrim=0:{fim + 0.1:.2f},afade=t=out:st={max(0.0, fim - 0.05):.2f}:d=0.15,apad=pad_dur=0.35",
                        "-ar", "44100", "-ac", "2", str(aud)], check=True, capture_output=True, timeout=60)
        dur = audio_duration(aud)
        texto = " ".join(w for w, _a, _b in pal)
        out = str(Path(out_dir) / "clip_intro.mp4")
        ok = build_clip_from_video(video_source=video_path, audio_path=str(aud), out_path=out, panel_idx=0,
                                   effects_mgr=None, global_start_t=plano[0][4] if plano else 0.0,
                                   clip_duration=dur, subtitles=texto, sfx=None, impacto=False)
        if not ok:
            logging.warning("[intro] clipe da abertura com voz real não montou — segue sem")
            return None
        logging.info(f"[intro] abertura com voz real {d.get('id')} ({d.get('voz')}, {dur:.1f} s): {texto[:80]}")
        return out, (texto, dur), [[a, b, w] for w, a, b in pal]
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[intro] abertura com voz real falhou ({type(e).__name__}: {e}) — segue sem")
        return None
