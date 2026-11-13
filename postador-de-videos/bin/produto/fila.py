"""Fila dos vídeos PROFISSIONAIS de produto (D:\\video-fila\\produto_fila\\<conta>\\*.mp4 + .json) e a entrega ao
postar_insta_auto (mesmo formato dos itens do catálogo). Postado -> _postados\\ (nunca apaga).

Ordem nas contas de produto (dono 25/10: "focados nos produtos, não no entretenimento"):
  1. pasta da empresa (material real, pastas_empresas) — até metade das vagas
  2. vídeo profissional de produto (esta fila)
  3. Veo de reserva (entretenimento) só se ainda sobrar vaga
"""
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

FILA = Path(r"D:\video-fila\produto_fila")


def pendentes(conta):
    pasta = FILA / conta
    if not pasta.exists():
        return []
    return sorted((p for p in pasta.glob("*.mp4") if p.with_suffix(".json").exists()), key=lambda p: p.stat().st_mtime)


CCV = Path(r"D:\claude-code-video")
CCV_POSTADOS = FILA / "_ccv_postados.json"  # o projeto de lá é independente: não movemos os arquivos dele


def _ccv_postados():
    try:
        return set(json.loads(CCV_POSTADOS.read_text("utf-8")))
    except Exception:  # noqa: BLE001
        return set()


def _ccv_ficha(conta, stem, postado_em, legenda):
    """29/10: o post do claude-code-video não deixava .json em _postados\\, então o medir_web nunca media e o
    melhorador central não via a linha. Ficha só .json (sem mp4: o produto.melhorador ignora), marcada ccv."""
    dest = FILA / conta / "_postados"
    dest.mkdir(parents=True, exist_ok=True)
    j = dest / f"{stem}.json"
    if not j.exists():
        j.write_text(json.dumps({"ccv": True, "projeto": "ccv", "postado_em": postado_em, "legenda": legenda,
                                 "arquivo": str(CCV / "saida" / conta / f"{stem}.mp4")}, ensure_ascii=False, indent=1),
                     "utf-8")


def itens_ccv(conta, vagas, log=print):
    """26/10 (dono: "o claude code video com Gemini, limpo, já fez alguns — poste"): vídeos prontos do
    D:\\claude-code-video\\saida\\<conta> que passam na trava de texto da tela (editor.problemas_texto: sem número,
    porcentagem, prazo ou preço inventado). Reprovado fica de fora e é avisado no log."""
    from produto import editor, kit as kit_mod
    pasta, out, feitos = CCV / "saida" / conta, [], _ccv_postados()
    if vagas <= 0 or not pasta.exists():
        return out
    for mp4 in sorted(pasta.glob(f"{conta.replace('.', '_')}_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
        if mp4.stem in feitos or "ANTES" in mp4.stem or not mp4.with_suffix(".json").exists():
            continue
        src = next((p for p in (CCV / "remotion" / "src" / "videos" / mp4.stem,
                                CCV / "estado" / "videos_guardados" / mp4.stem) if p.exists()), None)
        if src is None:
            continue
        side = json.loads(mp4.with_suffix(".json").read_text("utf-8"))
        try:
            k = dict(kit_mod.kit(conta))
        except Exception:  # noqa: BLE001  (conta de entretenimento não tem produto)
            k = {"fatos": []}
        # 29/10: entretenimento (Fato ou Fake, Recenas) era barrado sempre — "20 MIL EMUS", "1932" são fatos que a
        # NARRAÇÃO conta; o que a fala diz também vale como fato (número que ninguém falou continua barrado)
        falas = [c.get("fala", "") for c in ((side.get("roteiro") or {}).get("cenas") or [])]
        k["fatos"] = list(k.get("fatos") or []) + falas
        fala = re.sub(r"[^a-zà-ú0-9 ]", "", " ".join(falas).lower())
        erros = [e for e in editor.problemas_texto(src, k)
                 if not (falas and (m := re.match(r'"([^"]+)"', e))
                         and re.sub(r"[^a-zà-ú0-9 ]", "", m.group(1).lower()).strip() in fala)]
        if erros:
            log(f"  [{conta}] claude-code-video {mp4.name} BARRADO (texto da tela): {' | '.join(erros)[:200]}")
            continue
        out.append({"caminho": str(mp4), "nome": mp4.name, "bytes": mp4.stat().st_size, "projeto": "produto",
                    "ccv": True, "origem": "", "no_pc": True, "drive": None, "tipo": "final", "postagens": [],
                    "reserva": None, "conta_reuso": conta, "legenda": side.get("legenda") or side.get("titulo") or ""})
        log(f"  [{conta}] vídeo do claude-code-video: {mp4.name}")
        if len(out) >= vagas:
            break
    return out


def itens(conta, vagas, log=print):
    try:
        out = itens_ccv(conta, vagas, log)
    except Exception as e:  # noqa: BLE001
        log(f"  [{conta}] claude-code-video: {type(e).__name__}: {str(e)[:120]}")
        out = []
    vagas -= len(out)
    for mp4 in pendentes(conta)[:max(0, vagas)]:
        try:
            side = json.loads(mp4.with_suffix(".json").read_text("utf-8"))
        except Exception:  # noqa: BLE001
            continue
        out.append({"caminho": str(mp4), "nome": mp4.name, "bytes": mp4.stat().st_size, "projeto": "produto",
                    "origem": "", "no_pc": True, "drive": None, "tipo": "final", "postagens": [], "reserva": None,
                    "conta_reuso": conta, "legenda": side.get("legenda") or side.get("titulo") or ""})
        log(f"  [{conta}] vídeo profissional de produto: {mp4.name} ({side.get('formato')})")
    return out


def usado(v, log=print):
    if v.get("ccv"):
        feitos = _ccv_postados() | {Path(v["caminho"]).stem}
        CCV_POSTADOS.write_text(json.dumps(sorted(feitos), ensure_ascii=False, indent=1), "utf-8")
        _ccv_ficha(v["conta_reuso"], Path(v["caminho"]).stem, datetime.now().isoformat(timespec="seconds"),
                   v.get("legenda") or "")
        return
    mp4 = Path(v["caminho"])
    dest = mp4.parent / "_postados"
    dest.mkdir(parents=True, exist_ok=True)
    for p in (mp4, mp4.with_suffix(".json")):
        if p.exists():
            shutil.move(str(p), str(dest / p.name))
    try:
        j = dest / mp4.with_suffix(".json").name
        side = json.loads(j.read_text("utf-8"))
        side["postado_em"] = datetime.now().isoformat(timespec="seconds")
        j.write_text(json.dumps(side, ensure_ascii=False, indent=1), "utf-8")
    except Exception:  # noqa: BLE001
        pass
