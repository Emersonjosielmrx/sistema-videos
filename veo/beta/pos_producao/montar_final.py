# -*- coding: utf-8 -*-
"""montar_final.py — orquestra a montagem FINAL do short do veo.

Junta tudo que construímos, na receita:
  INTRO (overlay abertura) → VÍDEO (punch no gancho + overlay de impacto)
  → TRANSIÇÃO elemental → PROPAGANDA (card CTA + voz) → OUTRO (overlay fim)

Módulos usados (todos CPU-only, sem crédito):
  - montagem.py       : punch_gancho, overlay_alpha, transicao
  - cta_builder.py    : montar_cta (slide/overlay) + escolher_produto
  - efeitos rotam por hash pra não repetir sempre o mesmo.

Uso:
    from montar_final import montar
    montar(video_in, out, canal, tema, fala, voz="sarah", formato_cta="slide")
"""
import subprocess
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
_TMP = _BASE / "tmp" / "_montar_final"
_TMP.mkdir(parents=True, exist_ok=True)

# rotação de efeitos por posição (pra variar entre vídeos)
_INTRO = ["chiado_tv", "glitch", "portal", "raio"]
_IMPACTO = ["raio", "shockwave", "impacto", "zoompunch", "starburst"]
_TRANS = ["fogo", "gelo", "rasgo", "agua"]


def _wh(path):
    try:
        r = subprocess.run(
            [_FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(path)],
            capture_output=True, text=True, timeout=20)
        w, h = r.stdout.strip().split("x")[:2]
        return int(w), int(h)
    except Exception:
        return 720, 1280


def _pick(lista, stem, salt=""):
    # md5 (nao hash() nativo — randomizado por processo, quebraria a
    # reprodutibilidade: mesmo video daria efeitos diferentes a cada run).
    import hashlib
    h = int(hashlib.md5(f"{stem}|{salt}".encode("utf-8")).hexdigest(), 16)
    return lista[h % len(lista)]


def montar(*args, **kwargs):
    """Um render por vez (BX-03, D:\\veo\\beta\\trava_render.py): espera ate 30 min a trava; ocupada depois disso,
    nao monta (False, como as outras falhas daqui)."""
    sys.path.insert(0, str(_BASE.parent))
    from trava_render import TravaOcupada, trava_render
    try:
        with trava_render("montar_final", esperar_s=1800):
            return _montar(*args, **kwargs)
    except TravaOcupada as ex:
        print(f"[montar_final] {ex} - nao montou")
        return False


def _montar(video_in, out_path, canal, tema, fala, voz="sarah",
            formato_cta="slide", com_intro=True, com_punch=True,
            com_transicao=True, com_propaganda=True,
            com_vo3_propaganda=False, com_pexels_broll=False,
            produto=None):
    """Monta o short final. Retorna True se gerou. Cada etapa é opcional e
    tolerante a falha (se uma falhar, segue com o que tem).

    com_vo3_propaganda (default False): se True, insere ANTES do card CTA um
    clipe de propaganda Veo do MESMO produto (rotacionado do pool vo3), formando
    VÍDEO → VO3-PROPAGANDA(clipe) → PROPAGANDA(card CTA). Só usa clipes já
    gerados no pool (pos_producao/propagandas_pool/vo3/); se o pool estiver
    vazio, ignora silenciosamente e mantém o fluxo antigo intacto.

    com_pexels_broll (default False): se True, injeta 2 clipes b-roll do Pexels
    (buscados por keyword derivada do tema/produto): um após os efeitos iniciais
    (2-3s) e outro antes da transição pro card CTA (2-3s). Forma:
    INTRO/PUNCH → BROLL1 → VÍDEO-MEIO → BROLL2 → [VO3] → CARD."""
    from montagem import punch_gancho, overlay_alpha, transicao, OVERLAYS
    stem = Path(video_in).stem
    atual = Path(video_in)

    # meta de rastreabilidade: tudo que foi de fato aplicado neste video.
    # devolvido no retorno pra virar sidecar JSON (erros/acertos replicaveis).
    meta = {
        "ok": False, "stem": stem, "canal": canal, "tema": tema, "fala": fala,
        "voz": voz, "formato_cta": formato_cta,
        "efeitos": {"punch": False, "intro": None, "impacto": None,
                    "transicao": None, "vo3_propaganda": None, "broll_count": 0},
        "propaganda": {"aplicada": False, "produto_id": None, "produto_nome": None,
                       "fonte_fundo": None},
        "avisos": [],
    }

    # 1) PUNCH no gancho
    if com_punch:
        p = _TMP / f"{stem}_punch.mp4"
        if punch_gancho(str(atual), str(p)):
            atual = p
            meta["efeitos"]["punch"] = True

    # 2) INTRO overlay (abertura) + IMPACTO no gancho
    if com_intro:
        efe_intro = _pick(_INTRO, stem, "intro")
        i = _TMP / f"{stem}_intro.mp4"
        if efe_intro in OVERLAYS and overlay_alpha(str(atual), str(i), efe_intro, inicio=0.0):
            atual = i
            meta["efeitos"]["intro"] = efe_intro
        efe_imp = _pick(_IMPACTO, stem, "imp")
        j = _TMP / f"{stem}_imp.mp4"
        if efe_imp in OVERLAYS and overlay_alpha(str(atual), str(j), efe_imp, inicio=0.4):
            atual = j
            meta["efeitos"]["impacto"] = efe_imp

    # Escolhe o produto UMA vez — card e clipe vo3 tem que ser do MESMO produto.
    if produto is None:
        try:
            from cta_builder import escolher_produto
            produto = escolher_produto(tema=tema, canal=canal, stem=stem)
        except Exception:
            produto = None

    # 3) PROPAGANDA (card CTA + voz) — vira um segmento separado
    prop_clip = None
    if com_propaganda:
        try:
            from cta_builder import montar_cta, _montar_slide, _card, _narracao_cta
            if produto:
                meta["propaganda"]["produto_id"] = produto.get("id")
                meta["propaganda"]["produto_nome"] = produto.get("nome")
                prop = _TMP / f"{stem}_prop.mp4"
                # gera o slide do CTA como clip independente (5-6s)
                w, h = _wh(atual)
                card = _card(produto, stem=stem)
                try:
                    import omniroute_image as _oi
                    meta["propaganda"]["fonte_fundo"] = getattr(_oi, "_ultima_fonte", None)
                except Exception:
                    pass
                audio = _narracao_cta(produto, voz, stem=stem)
                # registra a voz/variante de fato usadas (rastreabilidade)
                try:
                    from cta_builder import _escolher_voz
                    from cta_card import escolher_variante
                    meta["propaganda"]["voz_usada"] = (
                        voz if voz and voz != "auto" else _escolher_voz(stem=stem))
                    meta["propaganda"]["card_variante"] = escolher_variante(stem)
                except Exception:
                    pass
                from cta_builder import _slide_clip
                if _slide_clip(card, audio, prop, w, h):
                    prop_clip = prop
                    meta["propaganda"]["aplicada"] = True
                else:
                    meta["avisos"].append("slide_clip falhou (sem propaganda)")
        except Exception as e:
            print(f"[montar_final] propaganda falhou: {str(e)[:80]}", flush=True)
            meta["avisos"].append(f"propaganda erro: {str(e)[:80]}")

    # 2b) BROLL do Pexels (opcional) — injeta 2 clipes curtos (2-3s) de b-roll
    # em pontos estratégicos do vídeo: um logo após os efeitos iniciais (pra dar
    # dinamismo) e outro antes da transição pro card (pra preparar o gancho).
    if com_pexels_broll:
        try:
            from pexels_broll import buscar_broll
            # keyword pra buscar: usa o tema (ex: "IA", "Financas") + produto se tiver
            kw = tema.split()[0] if tema else "business"
            if produto:
                kw = produto.get("nome", kw).split()[0]  # 1ª palavra do produto

            # broll 1: logo após efeitos iniciais (0.8s no vídeo)
            broll1 = buscar_broll(kw + " modern", orientacao="portrait", duracao_min=3)
            if broll1:
                b1 = _TMP / f"{stem}_broll1.mp4"
                # extrai 2.5s do broll, depois concat com o vídeo atual
                w, h = _wh(atual)
                try:
                    subprocess.run([
                        _FFMPEG, "-y", "-i", str(broll1), "-i", str(atual),
                        "-filter_complex",
                        f"[0:v]trim=0:2.5,setpts=PTS-STARTPTS,scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}[b];"
                        f"[b][1:v]concat=n=2:v=1:a=0[v]",
                        "-map", "[v]", "-map", "1:a?", "-c:v", "libx264", "-preset", "veryfast",
                        "-c:a", "copy", str(b1)
                    ], capture_output=True, timeout=60, check=True)
                    if b1.exists() and b1.stat().st_size > 50_000:
                        atual = b1
                        meta["efeitos"]["broll_count"] += 1
                except Exception:
                    pass

            # broll 2: antes da transição pro card (final do vídeo criativo)
            broll2 = buscar_broll(kw + " technology", orientacao="portrait", duracao_min=3)
            if broll2:
                b2 = _TMP / f"{stem}_broll2.mp4"
                w, h = _wh(atual)
                try:
                    subprocess.run([
                        _FFMPEG, "-y", "-i", str(atual), "-i", str(broll2),
                        "-filter_complex",
                        f"[1:v]trim=0:2.5,setpts=PTS-STARTPTS,scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}[b];"
                        f"[0:v][b]concat=n=2:v=1:a=0[v]",
                        "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast",
                        "-c:a", "copy", str(b2)
                    ], capture_output=True, timeout=60, check=True)
                    if b2.exists() and b2.stat().st_size > 50_000:
                        atual = b2
                        meta["efeitos"]["broll_count"] += 1
                except Exception:
                    pass
        except Exception as e:
            print(f"[montar_final] pexels broll falhou: {str(e)[:80]}", flush=True)
            meta["avisos"].append(f"pexels broll erro: {str(e)[:80]}")

    # 3b) VO3-PROPAGANDA (clipe Veo do produto) — OPCIONAL, entre vídeo e card.
    # Só usa clipes já no pool; se vazio ou falhar, mantém o fluxo antigo.
    if com_vo3_propaganda:
        try:
            sys.path.insert(0, str(_BASE))
            from vo3_propaganda_rotator import escolher_vo3_propaganda, _clipes_do_produto
            pid = produto.get("id") if produto else None
            # so insere o clipe vo3 se houver um DO MESMO produto do card.
            # (sem fallback pra outro produto — card e clipe tem que casar)
            vo3_clip = None
            if pid and _clipes_do_produto(pid):
                vo3_clip = escolher_vo3_propaganda(produto_id=pid, stem=stem)
            if vo3_clip and Path(vo3_clip).exists():
                tipo = _pick(_TRANS, stem, "vo3trans")
                comp = _TMP / f"{stem}_vo3.mp4"
                if transicao(str(atual), str(vo3_clip), str(comp), tipo):
                    atual = comp
                    meta["efeitos"]["vo3_propaganda"] = Path(vo3_clip).name
        except Exception as e:
            print(f"[montar_final] vo3-propaganda falhou: {str(e)[:80]}", flush=True)
            meta["avisos"].append(f"vo3 erro: {str(e)[:80]}")

    # 4) TRANSIÇÃO + concatena vídeo + propaganda
    if prop_clip and com_transicao:
        tipo = _pick(_TRANS, stem, "trans")
        final = _TMP / f"{stem}_final.mp4"
        if transicao(str(atual), str(prop_clip), str(final), tipo):
            atual = final
            meta["efeitos"]["transicao"] = tipo
    elif prop_clip:
        # sem transição: concat simples
        final = _TMP / f"{stem}_final.mp4"
        if transicao(str(atual), str(prop_clip), str(final), "fogo"):
            atual = final
            meta["efeitos"]["transicao"] = "fogo"

    # copia pro destino
    try:
        import shutil
        shutil.copy(str(atual), str(out_path))
        meta["ok"] = True
        return meta
    except Exception as e:
        print(f"[montar_final] copia falhou: {e}", flush=True)
        meta["avisos"].append(f"copia falhou: {str(e)[:80]}")
        return meta


if __name__ == "__main__":
    import json
    vids = sys.argv[1:] or []
    if not vids:
        # pega 3 videos diferentes do cron_shorts
        cron = _BASE.parent / "videos" / "cron_shorts"
        vids = [str(p) for p in sorted(cron.glob("*.mp4"))[-3:]]
    # inferir canal/tema pelo nome do arquivo (slug do canal) — simplificado
    outdir = _BASE / "tmp" / "videos_teste"
    outdir.mkdir(parents=True, exist_ok=True)
    exemplos = [
        ("Alienigenas", "ETs em Situacoes Engracadas", "ETs roubam nosso wifi de madrugada e nem pagam a conta"),
        ("Dicas Financeiras", "Educacao Financeira", "O banco esconde esse erro que destroi seu salario todo mes"),
        ("Curiosidades IA", "Fatos Rapidos Chocantes", "Voce nao vai acreditar no que a IA descobriu ontem"),
    ]
    for idx, vid in enumerate(vids):
        canal, tema, fala = exemplos[idx % len(exemplos)]
        out = outdir / f"TESTE_{idx+1}_{canal.replace(' ','_')}.mp4"
        print(f"\n=== TESTE {idx+1}: {canal} | base={Path(vid).name} ===")
        meta = montar(vid, str(out), canal, tema, fala, voz="sarah")
        ok = meta.get("ok") if isinstance(meta, dict) else bool(meta)
        print(f"  {'OK' if ok else 'FALHOU'} -> {out}")
        if isinstance(meta, dict):
            print(f"     efeitos={meta['efeitos']} prop={meta['propaganda']}")
    print("\npasta:", outdir.resolve())
