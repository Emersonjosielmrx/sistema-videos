"""anime_hardsub_detect.py — detecta a faixa da legenda QUEIMADA na fonte via visão.

Quase todo anime-fonte vem com legenda hard-sub (queimada no pixel). Pra pôr a
nossa legenda PT limpa por cima, primeiro borramos a faixa da legenda velha. Este
módulo pergunta ao Gemini (visão) EM QUE FAIXA VERTICAL da tela a legenda está,
amostrando alguns frames do vídeo-fonte numa ÚNICA chamada (modo batch: cobrança
por requisição, então agrupamos os frames).

Retorna (y_frac, h_frac) — topo e altura da faixa em fração da altura (0..1) — ou
None quando não há legenda / o modelo recusou / a rede caiu. O chamador decide o
fallback (faixa fixa via ANIME_HARDSUB_COVER).

Reusa: extract_last_frame (split-shorts), claude_client._post + _img_block (visão
via OmniRoute, mesmo gateway confiável da roteirização — o PC2 não tem chaves
Gemini diretas), _extract_json / is_refusal (parse robusto).
"""
import os
import re
import json
import logging
import tempfile
import statistics
import subprocess
from pathlib import Path


def _probe_dur(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=60)
        return float((r.stdout or "0").strip() or 0)
    except Exception:
        return 0.0


def _extract_frame(video_path, time_s, out_png):
    """1 frame no tempo dado. Seek 2 estágios (grosso antes de -i, fino depois) —
    mesmo idioma de split-shorts.extract_last_frame."""
    coarse = max(0.0, time_s - 1.0)
    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", f"{coarse:.2f}", "-i", str(video_path),
            "-ss", f"{time_s - coarse:.2f}",
            "-vframes", "1", "-q:v", "2", str(out_png)
        ], capture_output=True, timeout=60)
    except Exception:
        return False
    return Path(out_png).exists() and Path(out_png).stat().st_size > 500


_PROMPT = (
    "Cada imagem é um frame de um episódio de anime que PODE ter uma legenda "
    "QUEIMADA (hard-sub, texto sobreposto ao vídeo — geralmente no rodapé, às vezes "
    "no topo). Ignore balões de fala, placas e texto que faz parte do desenho. "
    # 25/10: em Short de parceiro o título amarelo fixo do topo era respondido como legenda (a tarja ia pra lá)
    "Ignore também TÍTULO/CABEÇALHO fixo (o MESMO texto em todas as imagens, comum no topo de Shorts) e marca/@ do "
    "canal: legenda é o texto que MUDA de uma imagem para outra. "
    "Para CADA imagem, na ordem, responda um objeto JSON com:\n"
    '  "tem_legenda": true/false (há texto de legenda sobreposto?),\n'
    '  "y_frac": número 0..1 (topo da faixa que contém a legenda, fração da altura),\n'
    '  "h_frac": número 0..1 (altura da faixa, fração da altura),\n'
    '  "texto": as palavras da legenda EXATAMENTE como estão escritas ("" se não der pra ler).\n'
    "Só marque tem_legenda=true se você consegue LER o texto. "
    "Responda APENAS um array JSON, um objeto por imagem, sem texto extra. "
    "Ex: [{\"tem_legenda\":true,\"y_frac\":0.84,\"h_frac\":0.14,\"texto\":\"e foi aí que ele\"}, ...]"
)


def _norm(t):
    return re.sub(r"\W+", "", str(t or "").lower())


# 27/10: veredito da última chamada — "com", "sem" (olhou e não há legenda legível) ou "falhou" (sem resposta). Com
# "sem", quem chama NÃO deve usar outro detector pra criar tarja (o de pixels deu falso positivo no Short dos ovos)
VEREDITO = "falhou"


def detect_hardsub_band(video_path, n_samples=6, min_agree=2):
    """Amostra n_samples frames (25/50/75% por padrão) e pergunta ao Gemini onde
    está a legenda queimada. Consolida: exige que >=min_agree frames concordem que
    HÁ legenda; devolve a mediana de (y_frac, h_frac). Senão None.
    """
    global VEREDITO
    VEREDITO = "falhou"
    dur = _probe_dur(video_path)
    if dur <= 0:
        logging.warning("[hardsub] duração da fonte = 0 — pulando detecção")
        return None

    # Frações internas (evita abertura/créditos das pontas).
    # 26/10: 6 quadros (eram 3) — legenda só aparece quando alguém fala; com 3, 2 quadros sem fala davam "sem legenda"
    # e a legenda coreana do Galaxy Express 999 (7 de 8 quadros) ficava à mostra
    fracs = [0.15, 0.3, 0.45, 0.6, 0.75, 0.9][:max(1, n_samples)]
    frames = []
    tmp = Path(tempfile.mkdtemp(prefix="hardsub_det_"))
    try:
        for k, fr in enumerate(fracs):
            png = tmp / f"f{k}.jpg"
            if _extract_frame(video_path, dur * fr, png):
                frames.append(png.read_bytes())
        if not frames:
            logging.warning("[hardsub] nenhum frame extraído — pulando detecção")
            return None

        try:
            import claude_client
            from claude_client import _img_block, _extract_json, is_refusal
        except Exception as e:
            logging.warning(f"[hardsub] imports de visão indisponíveis: {e}")
            return None

        # Visão via OmniRoute (mesmo gateway da roteirização). Uma chamada com os N
        # frames rotulados + o prompt (modo batch: cobrança por requisição).
        content = []
        for k, b in enumerate(frames):
            content.append({"type": "text", "text": f"Imagem {k+1}:"})
            content.append(_img_block(b, mime="image/jpeg"))
        content.append({"type": "text", "text": _PROMPT})
        try:
            resp = claude_client._post([{"role": "user", "content": content}],
                                       max_tokens=800, temperature=0.0)  # 26/10: agora devolve o texto lido
        except Exception as e:
            logging.warning(f"[hardsub] chamada de visão falhou: {e}")
            return None

        if not resp or is_refusal(resp):
            logging.info("[hardsub] modelo recusou/vazio — fallback faixa fixa")
            return None

        data = _parse_bands(resp, _extract_json)
        if not data:
            logging.info("[hardsub] resposta sem JSON aproveitável — fallback")
            return None

        # 26/10 (dono: "todos vêm com tarja mesmo sem legenda"): só conta quadro em que o modelo LEU o texto; e a
        # legenda MUDA — o mesmo texto em todos os quadros é título/marca fixa, não legenda
        positivos = [d for d in data if d.get("tem_legenda") and len(_norm(d.get("texto"))) >= 2]
        if len(positivos) < min_agree:
            logging.info(f"[hardsub] só {len(positivos)}/{len(data)} frames com legenda legível "
                         f"({[d.get('texto') for d in data]}) — assume SEM hard-sub")
            VEREDITO = "sem"
            return None
        if len({_norm(d.get("texto")) for d in positivos}) == 1:
            logging.info(f"[hardsub] o mesmo texto em todos os quadros ({positivos[0].get('texto')!r}) — é fixo, "
                         "não legenda")
            VEREDITO = "sem"
            return None
        VEREDITO = "com"
        logging.info(f"[hardsub] textos lidos: {[d.get('texto') for d in positivos]}")

        ys = [_clamp01(d.get("y_frac")) for d in positivos if d.get("y_frac") is not None]
        hs = [_clamp01(d.get("h_frac")) for d in positivos if d.get("h_frac") is not None]
        if not ys or not hs:
            return None
        y = statistics.median(ys)
        h = statistics.median(hs)
        # Margem de segurança: legenda costuma "vazar" da caixa detectada.
        h = min(1.0 - y, h + 0.015)  # 26/10: era +0,03 (tarja grande demais)
        if h <= 0.02:
            return None
        logging.info(f"[hardsub] legenda detectada: y_frac={y:.3f} h_frac={h:.3f}")
        return (round(y, 4), round(h, 4))
    finally:
        try:
            for p in tmp.glob("*"):
                p.unlink()
            tmp.rmdir()
        except Exception:
            pass


def _parse_bands(resp, extract_json):
    """A resposta pode ser um array JSON direto, ou prosa com o array embrulhado.
    Tenta json.loads direto; senão usa o _extract_json (pega 1 objeto) por fallback."""
    txt = resp.strip()
    for candidate in (txt,):
        try:
            import re
            c = re.sub(r"^```(?:json)?\s*", "", candidate)
            c = re.sub(r"\s*```$", "", c).strip()
            j = json.loads(c)
            if isinstance(j, list):
                return [d for d in j if isinstance(d, dict)]
            if isinstance(j, dict):
                return [j]
        except Exception:
            pass
    one = extract_json(txt)
    return [one] if isinstance(one, dict) else None


def _clamp01(v):
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("uso: python anime_hardsub_detect.py <video>")
        sys.exit(1)
    print(detect_hardsub_band(sys.argv[1]))
