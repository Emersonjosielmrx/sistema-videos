"""Runner: aplica o pipeline de plugins a cada mp4 novo no diret�rio fonte.

Uso:
    from pos_producao import run_pipeline
    run_pipeline(dry_run=False)

Comportamento:
    1. Lista mp4 em VIDEO_SRC_DIR (excluindo ja processados).
    2. Para cada mp4, aplica os plugins na ordem definida em config.yaml.
    3. Saida em VIDEO_OUT_DIR com mesmo nome base + sufixo do plugin (se houver).
    4. Tudo nao-destrutivo: o mp4 original nunca eh modificado.
"""

import importlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from .config import load_config, VIDEO_SRC_DIR, VIDEO_OUT_DIR, FFMPEG


def _log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [pos_producao] {msg}", flush=True)


def listar_plugins():
    """Retorna nomes de plugins disponiveis no diretorio plugins/."""
    plugins_dir = Path(__file__).parent / "plugins"
    out = []
    for p in sorted(plugins_dir.glob("*.py")):
        if p.name.startswith("_"):
            continue
        out.append(p.stem)
    return out


def _carregar_plugin(nome):
    """Importa pos_producao.plugins.<nome>. Espera expor funcao processar().

    Aceita tanto 'ffmpeg_loudnorm' quanto 'plugins.ffmpeg_loudnorm' como entrada
    (vindos do config.yaml).
    """
    if nome.startswith("plugins."):
        nome = nome[len("plugins."):]
    full = f"pos_producao.plugins.{nome}"
    try:
        mod = importlib.import_module(full)
        if not hasattr(mod, "processar"):
            _log(f"!! plugin {nome} nao expoe processar() - pulando")
            return None
        return mod
    except Exception as e:
        _log(f"!! falha ao carregar plugin {nome}: {e}")
        return None


def _listar_videos_novos(src: Path, out: Path, skip_existing=True, recursive=False):
    """Retorna mp4s em src que ainda nao tem equivalente processado em out.

    Se recursive=True, varre src recursivamente e retorna tuplas
    (mp4_path, rel_subpath) onde rel_subpath == Path relativo a src.
    Equivalente em out eh out / rel_subpath / mp4_path.stem + ".mp4".
    """
    if not src.exists():
        return []
    ja_feitos = set()
    if out.exists():
        if recursive:
            for f in out.rglob("*.mp4"):
                try:
                    rel = f.relative_to(out).parent
                    ja_feitos.add((rel.as_posix(), f.stem.split("__")[0]))
                except Exception:
                    pass
        else:
            for f in out.glob("*.mp4"):
                ja_feitos.add(f.stem.split("__")[0])
    novos = []
    candidatos = sorted(src.rglob("*.mp4")) if recursive else sorted(src.glob("*.mp4"))
    for mp4 in candidatos:
        base = mp4.stem
        if recursive:
            try:
                rel = mp4.relative_to(src).parent
                key = (rel.as_posix(), base)
            except Exception:
                key = (".", base)
        else:
            key = base
        if skip_existing and key in ja_feitos:
            continue
        novos.append((mp4, rel if recursive else None))
    return novos


_FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"


def _ffprobe(meta_args):
    """Wrapper minimo pra ffprobe. Retorna stdout ou None."""
    try:
        r = subprocess.run(
            [_FFPROBE, "-hide_banner"] + meta_args,
            capture_output=True, text=True, timeout=30
        )
        return r.stdout.strip()
    except Exception:
        return None


def _meta_do_video(mp4_path: Path):
    """Extrai meta simples: duracao (s), tem audio, dims."""
    out = {"path": str(mp4_path), "stem": mp4_path.stem,
           "duracao_s": None, "tem_audio": False, "w": None, "h": None}
    # duracao + dimensoes via show_format+show_streams
    r = _ffprobe([
        "-v", "error",
        "-show_entries", "format=duration:stream=width,height,codec_type",
        "-of", "default=noprint_wrappers=1",
        str(mp4_path),
    ])
    if r:
        for linha in r.splitlines():
            linha = linha.strip()
            if linha.startswith("duration="):
                try:
                    out["duracao_s"] = float(linha.split("=", 1)[1])
                except Exception:
                    pass
            elif linha.startswith("width="):
                try:
                    out["w"] = int(linha.split("=", 1)[1])
                except Exception:
                    pass
            elif linha.startswith("height="):
                try:
                    out["h"] = int(linha.split("=", 1)[1])
                except Exception:
                    pass
            elif linha.startswith("codec_type=audio"):
                out["tem_audio"] = True
    return out


# cache simples: stem -> meta_extra (preenchido pelo run_one, consumido pelo _processar_um)
_META_EXTRA_KW = {}


def _processar_um(mp4: Path, out_sub: Path):
    """Roda os plugins num mp4, escreve em out_sub. Retorna True se fez."""
    meta = _meta_do_video(mp4)
    meta["stem"] = mp4.stem
    # injeta meta_extra se caller passou
    if mp4.stem in _META_EXTRA_KW:
        meta.update(_META_EXTRA_KW.pop(mp4.stem))
    out_sub.mkdir(parents=True, exist_ok=True)
    rel = mp4.name
    try:
        rel = str(mp4.relative_to(out_sub.parent))
    except Exception:
        pass
    _log(f"-- [{rel}] dur={meta['duracao_s']}s audio={meta['tem_audio']}")

    cfg = load_config()
    plugins = cfg.get("pipeline") or []
    current = mp4
    for nome in plugins:
        mod = _carregar_plugin(nome)
        if mod is None:
            continue
        sufixo = getattr(mod, "SUFFIX", nome.replace("plugins.", ""))
        saida = out_sub / f"{mp4.stem}__{sufixo}.mp4"
        try:
            t0 = time.time()
            ok = mod.processar(str(current), str(saida), meta)
            dt = time.time() - t0
            if ok and saida.exists():
                _log(f"   [{nome}] ok em {dt:.1f}s -> {saida.name}")
                current = saida
            else:
                _log(f"   [{nome}] pulou (ok={ok}) saida_existe={saida.exists()}")
        except Exception as e:
            _log(f"   [{nome}] ERRO: {e}")
    if current != mp4 and current.exists():
        final = out_sub / f"{mp4.stem}.mp4"
        try:
            # copia o resultado pra um nome temporario, limpa os intermediarios
            # e so entao renomeia pro nome final (evita apagar o proprio final).
            tmp_final = out_sub / f"{mp4.stem}__RESULT.mp4"
            shutil.copy2(current, tmp_final)
            for stale in out_sub.glob(f"{mp4.stem}__*.mp4"):
                if stale == tmp_final:
                    continue
                try:
                    stale.unlink()
                except Exception:
                    pass
            for stale in out_sub.glob(f"{mp4.stem}.*.mp4"):
                try:
                    stale.unlink()
                except Exception:
                    pass
            if final.exists():
                try:
                    final.unlink()
                except Exception:
                    pass
            tmp_final.replace(final)
            _log(f"FINAL: {final.relative_to(out_sub.parent).as_posix()}")
            return True
        except Exception as e:
            _log(f"!! falha ao copiar final: {e}")
    return False


def run_pipeline(dry_run=False, recursive=False):
    """Aplica a esteira aos videos novos. Retorna numero de videos processados.

    recursive=True varre src recursivamente e espelha a estrutura em out.
    Respeita flag pos_video (se OFF, nao roda).
    """
    try:
        from pos_producao.flags import is_on as _is_on
        if not _is_on("pos_video"):
            _log("flag pos_video OFF - nada a fazer")
            return 0
        if recursive and not _is_on("cron_pos_retro"):
            _log("flag cron_pos_retro OFF - retroativo desligado")
            return 0
    except Exception as e:
        _log(f"flags: ignorando erro ({e})")

    cfg = load_config()
    src = Path(cfg.get("video_src", VIDEO_SRC_DIR))
    out = Path(cfg.get("video_out", VIDEO_OUT_DIR))
    out.mkdir(parents=True, exist_ok=True)

    plugins = cfg.get("pipeline") or []
    if not plugins:
        _log("nenhum plugin ativo no config.yaml - nada a fazer")
        return 0
    _log(f"plugins ativos ({len(plugins)}): {plugins}")
    _log(f"ffmpeg: {cfg.get('ffmpeg') or FFMPEG}")
    _log(f"modo: {'retroativo (recursivo)' if recursive else 'incremental'}")

    novos = _listar_videos_novos(src, out,
                                 cfg.get("skip_if_output_exists", True),
                                 recursive=recursive)
    limite = int(cfg.get("max_videos_per_run", 5))
    if len(novos) > limite:
        _log(f"limitando a {limite} de {len(novos)} videos nesta run")
        novos = novos[:limite]
    _log(f"{len(novos)} video(s) novo(s) para processar")

    processados = 0
    for mp4, rel in novos:
        out_sub = out / rel if rel is not None else out
        if _processar_um(mp4, out_sub):
            processados += 1
    return processados


def run_one(mp4_path, meta_extra=None):
    """Roda o pipeline em um unico mp4. Retorna True se processado.

    Usado pelo cron principal quando gera um video novo e ja quer aplicar
    pos-producao imediatamente.

    meta_extra: dict opcional com dados do cron (fala, tema, canal_nome, cenario_en).
    Esses campos sao injetados em meta para que plugins como tts_gemini_or_edge
    e legendas saibam o que narrar.
    """
    cfg = load_config()
    src = Path(cfg.get("video_src", VIDEO_SRC_DIR))
    out = Path(cfg.get("video_out", VIDEO_OUT_DIR))
    out.mkdir(parents=True, exist_ok=True)

    mp4 = Path(mp4_path).resolve()
    # mantem a mesma politica: se src eh videos/cron_shorts, saida eh videos_pos/cron_shorts
    try:
        rel = mp4.relative_to(src.resolve()).parent
    except Exception:
        rel = Path(".")
    out_sub = out / rel
    if meta_extra:
        _META_EXTRA_KW[mp4.stem] = meta_extra
    return _processar_um(mp4, out_sub)


if __name__ == "__main__":
    run_pipeline(dry_run=False)
