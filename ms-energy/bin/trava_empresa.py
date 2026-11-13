"""trava_empresa.py — ÚLTIMA conferência antes de publicar um Reel de cliente (04/11/2026).

Dona 04/11: "foi postado no Insta da Globo conteúdo da Advance — isso não pode acontecer nunca mais." (Reel DfTKW4-s-CD,
03/11 21:21: clipe gerado pela Advance reaproveitado pela Globo; a trava de rosto conferiu contra as fotos da ADVANCE
porque o roteiro reaproveitado era da Advance — passou.) Duas travas independentes, as duas precisam passar:

1. DONO DO VÍDEO: o sidecar (.json) do Reel tem "_empresa" (gravado na aprovação pelo gerar_short_veo). Diferente da
   empresa que vai postar = recusa. Vídeo antigo sem "_empresa" só passa se a trava 2 passar.
2. ROSTO: Reel de apresentador (clone do dono/responsável) é conferido contra as fotos-base DA EMPRESA QUE VAI POSTAR
   (assets\\<empresa>\\clone_bases), nunca as do roteiro. Rosto de outra pessoa = recusa.
Recusou = o vídeo vai pra videos\\_revisar, aviso importante no Telegram e RuntimeError (o insistir pega o próximo
reel pronto ou gera outro: o horário não fica sem post).

    from trava_empresa import conferir
    conferir(mp4, "Globo Solar @globosolarenergiag", Path(r"D:\\ms-energy\\assets\\globo\\clone_bases"), log)
"""
import json
import shutil
import sys
from pathlib import Path

REVISAR = Path(r"D:\ms-energy\videos\_revisar")
IMG = (".jpg", ".jpeg", ".png", ".webp")


def _recusar(mp4, motivo, log):
    REVISAR.mkdir(parents=True, exist_ok=True)
    for ext in (".mp4", ".json"):
        p = Path(mp4).with_suffix(ext)
        if p.exists():
            shutil.move(str(p), str(REVISAR / p.name))
    log(f"  [TRAVA EMPRESA] RECUSADO {Path(mp4).name}: {motivo} → _revisar (não posta)")
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(f"🚫 Reel de cliente RECUSADO antes de postar: {Path(mp4).name} — {motivo}. Foi pra "
                      "ms-energy\\videos\\_revisar; o horário segue com outro reel.", "solares", importante=True)
    except Exception:  # noqa: BLE001
        pass
    raise RuntimeError(f"trava da empresa: {motivo}")


def conferir(mp4, empresa, bases_dir=None, log=print):
    """empresa = o mesmo texto do gerar_short_veo._empresa_atual() ("Nome @conta"). bases_dir = fotos-base do
    responsável dessa empresa (None = empresa sem clone, ex.: MS). Passou = None; recusou = RuntimeError."""
    mp4 = Path(mp4)
    try:
        side = json.loads(mp4.with_suffix(".json").read_text("utf-8"))
    except (OSError, ValueError):
        return _recusar(mp4, "sem o arquivo de dados do vídeo (.json) — não sei de quem é", log)
    dono = side.get("_empresa")
    # 04/11 13:30: o Reel Remotion da Globo (ccv_globosolarenergiag_*, pipeline claude_code_video) foi recusado por não
    # ter "_empresa" e o horário atrasou 40 min. O claude-code-video gera POR CONTA (origem saida\<conta>\..., nome
    # ccv_<conta>_*): a conta do arquivo é a marca. Só vale se bater com o @ desta empresa.
    if not dono and side.get("pipeline") == "claude_code_video" and "@" in (empresa or ""):
        arroba = empresa.rsplit("@", 1)[1].strip().lower()
        conta_origem = Path(str(side.get("origem", ""))).parent.name.lower()
        conta_nome = mp4.name.lower().removeprefix("ccv_").rsplit("_", 2)[0]
        if conta_origem and conta_origem == conta_nome:
            if conta_origem != arroba:
                return _recusar(mp4, f"o vídeo Remotion é da conta @{conta_origem} e ia sair em '{empresa}'", log)
            dono = empresa
    if dono and dono != empresa:
        return _recusar(mp4, f"o vídeo é de '{dono}' e ia sair em '{empresa}'", log)
    usa_clone = side.get("tipo_video") == "apresentador" and "clone" in json.dumps(side, ensure_ascii=False)
    if usa_clone and bases_dir:
        bases = [str(p) for p in sorted(Path(bases_dir).glob("*")) if p.suffix.lower() in IMG]
        if not bases:
            return _recusar(mp4, f"sem fotos-base do responsável em {bases_dir} pra conferir o rosto", log)
        try:
            if r"D:\veo\beta" not in sys.path:
                sys.path.append(r"D:\veo\beta")
            import foto_na_hora
            foto_na_hora.usar_bases(str(bases_dir))  # a PASTA das fotos-base (não a lista)
            ok, notas, motivo = foto_na_hora.revisar_video(str(mp4))
        except Exception as e:  # noqa: BLE001 — não conseguiu conferir = não posta às cegas
            return _recusar(mp4, f"não consegui conferir o rosto ({type(e).__name__}: {str(e)[:80]})", log)
        # o revisar_video devolve ok=True quando ELE falha ("indisponível — não trava"): aqui sem nota real não passa
        if not notas or not any(n > 0 for n in notas):
            return _recusar(mp4, f"conferência de rosto sem resultado ({motivo}) — não posto às cegas", log)
        if not ok:
            return _recusar(mp4, f"rosto não é o responsável da empresa ({motivo}; notas {notas})", log)
        log(f"  [TRAVA EMPRESA] ok: {mp4.name} é de {empresa} (rosto confere: {notas})")
    elif not dono:
        return _recusar(mp4, "vídeo antigo sem marca de empresa e sem rosto pra conferir", log)
    else:
        log(f"  [TRAVA EMPRESA] ok: {mp4.name} é de {empresa}")
    return None
