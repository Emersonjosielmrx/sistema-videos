# -*- coding: utf-8 -*-
"""compilado_longo.py — COMPILADO 16:9 (1920x1080) das histórias, para o YouTube longo.

Ideia do hipercool (hiper-longo.py / referência Porão: compilado longo acumula watch time). As histórias são Shorts
de ~1 min, então aqui o compilado junta HISTÓRIAS do mesmo gênero, não capítulos.

1. Cada história pronta é convertida para 16:9 (o vertical no centro, fundo desfocado de landscape_filters.py) e
   guardada em videos/<pista>/_landscape/_cache, registrada em _landscape/indice.json com gênero e título.
   O cache sobrevive ao arquivamento (a rede move a pasta postada) e ao backup do Drive (leva o mp4 em 3 dias).
2. Quando um gênero junta "compilado_min" histórias (settings.json, padrão 12 = ~12 min, abaixo do limite de 15 min
   de canal não verificado) fora de compilado, elas viram um vídeo só (concat sem re-encode), com capítulos na
   descrição e capa 16:9 (capa_ia_historias). Nenhuma chamada de TTS/roteiro: é o vídeo pronto recomposto.

Entrega: com "compilado_canal_slug" no settings.json, o mp4, a capa e <nome>.postar.json vão para
D:\\hipercool-materiais\\manhwa-react\\grandes\\<slug>\\ (a rede agenda como vídeo completo depois da revisão dela).
Sem slug, ficam em _landscape/. NUNCA grava um arquivo chamado "postar.json": a rede sobe todo postar.json de
histórias como Short.

Quem chama: story_pipeline (etapa 12) depois de cada história.
    python bin/compilado_longo.py --status
    python bin/compilado_longo.py --genero terror --agora    # compila o que tiver do gênero (mínimo 3)
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import TMP_DIR, VIDEOS_DIR, _settings, log  # noqa: E402

W, H, FPS = 1920, 1080, 30
SAIDA = VIDEOS_DIR / "_landscape"
CACHE = SAIDA / "_cache"
INDICE = SAIDA / "indice.json"
GRANDES = Path(r"D:\hipercool-materiais\manhwa-react\grandes")
MINIMO_PADRAO = 12
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

NOME_GENERO = {"terror": "TERROR", "misterio": "MISTÉRIO", "superacao": "SUPERAÇÃO", "motivacional": "MOTIVAÇÃO",
               "drama": "DRAMA", "romance": "ROMANCE", "comedia": "COMÉDIA", "religioso": "FÉ",
               "fantasia": "FANTASIA", "curiosidades": "CURIOSIDADES"}
GANCHO = {"terror": "que vão tirar seu sono", "misterio": "que ninguém conseguiu explicar",
          "superacao": "que vão mudar sua vida", "motivacional": "pra você nunca mais desistir",
          "drama": "que vão te fazer chorar", "romance": "de amor que parecem filme",
          "comedia": "impossível não rir", "religioso": "que parecem milagre",
          "fantasia": "de mundos que você nunca imaginou", "curiosidades": "que você nunca ouviu"}


def _dur(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, timeout=30, creationflags=_SEM_JANELA)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _ler_indice():
    try:
        return json.loads(INDICE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_indice(d):
    SAIDA.mkdir(parents=True, exist_ok=True)
    tmp = INDICE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(INDICE)


def _ts(seg):
    h, r = divmod(int(seg), 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def converter_16x9(vertical_mp4, out_mp4):
    """Vertical 9:16 -> 16:9 com fundo estilizado. Parâmetros de saída fixos (inclusive áudio 48 kHz estéreo) para
    o compilado poder juntar sem re-encode."""
    try:
        import landscape_filters
        _nome, fc = landscape_filters.pick_filter(W, H)
    except ImportError:
        fc = (f"[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"boxblur=18:8[bgb];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];"
              f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2")
    tmp = Path(out_mp4).with_name(Path(out_mp4).stem + "_tmp.mp4")
    cmd = ["ffmpeg", "-y", "-i", str(vertical_mp4), "-filter_complex", fc + ",fps=30,format=yuv420p[vout]",
           "-map", "[vout]", "-map", "0:a:0", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-movflags", "+faststart", str(tmp)]
    r = subprocess.run(cmd, capture_output=True, timeout=1800, creationflags=_SEM_JANELA)
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 10000:
        log(f"  ! 16:9 falhou: {(r.stderr or b'').decode('utf-8', 'replace')[-300:]}")
        tmp.unlink(missing_ok=True)
        return False
    os.replace(str(tmp), str(out_mp4))
    return True


def converter_com_cache(vertical_mp4, genero, titulo=""):
    """Converte a história para 16:9 (uma vez) e registra no índice. Devolve o Path do cache ou None."""
    vertical_mp4 = Path(vertical_mp4)
    chave = f"{vertical_mp4.parent.name}_{vertical_mp4.stem}"
    destino = CACHE / f"{chave}.mp4"
    idx = _ler_indice()
    if not (destino.exists() and destino.stat().st_size > 10000):
        CACHE.mkdir(parents=True, exist_ok=True)
        if not converter_16x9(vertical_mp4, destino):
            return None
    if chave not in idx:
        idx[chave] = {"arquivo": destino.name, "genero": (genero or "outros").lower(),
                      "titulo": re.sub(r"\s*#\S+", "", titulo or "").strip(), "origem": str(vertical_mp4),
                      "dur": round(_dur(destino), 2), "criado": datetime.now().isoformat(timespec="seconds"),
                      "compilado": None}
        _gravar_indice(idx)
    return destino


def _pendentes(genero):
    idx = _ler_indice()
    return [(k, v) for k, v in sorted(idx.items(), key=lambda kv: kv[1].get("criado", ""))
            if v.get("genero") == genero and not v.get("compilado") and (CACHE / v["arquivo"]).exists()]


def _capa(genero, n, saida_jpg, primeiro_mp4):
    """Capa 16:9: capa IA (pose por Thompson) ou, se o gateway falhar, um quadro da primeira história."""
    try:
        import capa_ia_historias
        c = capa_ia_historias.gerar_capa(genero, saida_jpg, tema=f"compilado de {n} histórias de {genero}",
                                         titulo=f"{n} histórias de {genero}",
                                         texto=f"{n} HISTÓRIAS DE {NOME_GENERO.get(genero, genero.upper())}",
                                         formato="16:9")
        if c:
            return Path(c)
    except Exception as e:  # noqa: BLE001
        log(f"  ! capa IA do compilado falhou ({e}) — usando um quadro")
    subprocess.run(["ffmpeg", "-y", "-ss", "5", "-i", str(primeiro_mp4), "-vframes", "1", "-q:v", "2",
                    str(saida_jpg)], capture_output=True, timeout=60, creationflags=_SEM_JANELA)
    return Path(saida_jpg) if Path(saida_jpg).exists() else None


def compilar(genero, itens):
    """Junta as histórias (cache 16:9) num vídeo só e grava <nome>.postar.json. Devolve o Path do mp4 ou None."""
    slug = (_settings().get("compilado_canal_slug") or "").strip()
    pasta = GRANDES / slug if slug else SAIDA
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"compilado_{genero}_{datetime.now():%Y%m%d_%H%M}"
    saida = pasta / f"{nome}.mp4"

    lista = TMP_DIR / f"{nome}_concat.txt"
    capitulos, t = [], 0.0
    with open(lista, "w", encoding="utf-8") as f:
        for i, (_k, v) in enumerate(itens):
            f.write(f"file '{(CACHE / v['arquivo']).as_posix()}'\n")
            capitulos.append(f"{_ts(t)} {v.get('titulo') or f'História {i + 1}'}")
            t += v.get("dur") or _dur(CACHE / v["arquivo"])

    tmp = pasta / f"{nome}_tmp.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy",
                        "-movflags", "+faststart", str(tmp)],
                       capture_output=True, timeout=3600, creationflags=_SEM_JANELA)
    lista.unlink(missing_ok=True)
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 10000:
        log(f"  ! compilado falhou: {(r.stderr or b'').decode('utf-8', 'replace')[-300:]}")
        tmp.unlink(missing_ok=True)
        return None
    os.replace(str(tmp), str(saida))

    n, dur = len(itens), _dur(saida)
    dur_txt = f"{int(dur // 3600)}h{int(dur % 3600 // 60):02d}" if dur >= 3600 else f"{round(dur / 60)} min"
    nome_g = NOME_GENERO.get(genero, genero.upper())
    titulo = f"{n} histórias de {nome_g} {GANCHO.get(genero, 'pra ouvir até o fim')} | {dur_txt}"[:100]
    descricao = (f"{n} histórias de {genero} narradas, uma atrás da outra ({dur_txt}).\n"
                 "Qual delas foi a melhor? Comenta o número!\n\n" + "\n".join(capitulos) +
                 f"\n\n#historias #{genero} #compilado")
    capa = _capa(genero, n, pasta / f"{nome}_capa.jpg", CACHE / itens[0][1]["arquivo"])
    doc = {"arquivo": saida.name, "categoria": "historias", "tipo": "longo", "genero": genero,
           "titulo": titulo, "descricao": descricao[:5000],
           "tags": [f"histórias de {genero}", "compilado de histórias", "histórias narradas", genero,
                    "histórias", "compilado", "história completa"],
           "comentario_fixado": "Qual história você quer ouvir no próximo compilado? Comenta aqui!",
           "historias": [k for k, _v in itens], "privacy": "private", "made_for_kids": False, "pronto": True}
    if slug:
        doc["canal_slug"] = slug
    if capa:
        doc["thumb"] = capa.name
    # por último: a rede só enxerga o vídeo quando o .postar.json aparece
    (pasta / f"{nome}.postar.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    idx = _ler_indice()
    for k, v in itens:
        idx[k]["compilado"] = saida.name
        (CACHE / v["arquivo"]).unlink(missing_ok=True)  # já está dentro do compilado
    _gravar_indice(idx)
    log(f"  + compilado {genero}: {n} histórias, {dur_txt} -> {saida}" + ("" if slug else
        " (sem compilado_canal_slug no settings.json: fica em _landscape, a rede não posta)"))
    return saida


def talvez_compilar(genero, minimo=None):
    """Compila o gênero se já tem histórias suficientes fora de compilado. Devolve o Path do compilado ou None."""
    genero = (genero or "outros").lower()
    minimo = minimo or int(_settings().get("compilado_min") or MINIMO_PADRAO)
    pend = _pendentes(genero)
    if len(pend) < minimo:
        log(f"  compilado {genero}: {len(pend)}/{minimo} histórias em 16:9")
        return None
    return compilar(genero, pend)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Compilado 16:9 das histórias")
    ap.add_argument("--status", action="store_true", help="quantas histórias em 16:9 esperam compilado, por gênero")
    ap.add_argument("--genero", "-g")
    ap.add_argument("--agora", action="store_true", help="compila o gênero com o que tiver (mínimo 3)")
    a = ap.parse_args()
    if a.genero and a.agora:
        sys.exit(0 if talvez_compilar(a.genero, minimo=3) else 1)
    cont = {}
    for v in _ler_indice().values():
        if not v.get("compilado"):
            cont[v.get("genero")] = cont.get(v.get("genero"), 0) + 1
    minimo = int(_settings().get("compilado_min") or MINIMO_PADRAO)
    print(f"esperando compilado (mínimo {minimo}): {cont or 'nenhuma'}")
    print(f"entrega: {_settings().get('compilado_canal_slug') or '(sem slug: fica em ' + str(SAIDA) + ')'}")


if __name__ == "__main__":
    main()
