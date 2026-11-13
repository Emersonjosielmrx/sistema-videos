# -*- coding: utf-8 -*-
"""image_generator.py — Geração de imagens em lotes via OmniRoute.

Gera N variações por cena, opera em lotes de 10, cache por hash do prompt.
Integra com character_bank pra coerência visual.
"""
import json
import hashlib
import time
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, IMAGES_DIR, log
import omniroute_image
import character_bank

BATCH_SIZE = 10
DELAY_WITHIN_BATCH_S = 8           # delay entre imagens do mesmo lote (era 5)
PAUSE_BETWEEN_BATCHES_S = 60       # pausa entre lotes (era 30)
QUOTA_BACKOFF_SEQUENCE = [20, 60, 180, 360, 600]  # backoff progressivo em segundos
QUOTA_COOLDOWN_FILE = PROJECT_DIR / "workspace" / ".quota_cooldown.txt"
QUOTA_COOLDOWN_SEC = 3600  # 1h antes de tentar de novo após esgotar


def _cooldown_ate():
    """Instante (unix) em que a cota volta, lido de .quota_cooldown.txt, ou 0.
    O arquivo guarda a HORA DE VOLTA (e o que o auto_producer le). Antes guardava a hora
    em que a cota ACABOU: o auto_producer lia como hora de volta (ja no passado) e nunca
    esperava. Valor antigo (no passado) = formato velho -> +QUOTA_COOLDOWN_SEC."""
    try:
        v = float(QUOTA_COOLDOWN_FILE.read_text().strip())
    except (OSError, ValueError):
        return 0
    return v if v > time.time() else v + QUOTA_COOLDOWN_SEC


def _grava_cooldown(segundos):
    QUOTA_COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUOTA_COOLDOWN_FILE.write_text(str(time.time() + segundos))


class ApiQuotaExhaustedError(Exception):
    """Quota do Gemini image-gen esgotada. Aguardar 1h antes de tentar de novo."""
    pass


def _image_cache_dir(story_id):
    d = IMAGES_DIR / story_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _variation_path(cache_dir, scene_idx, variation_idx):
    return cache_dir / f"scene_{scene_idx:02d}_v{variation_idx}.png"


def _final_path(cache_dir, scene_idx):
    return cache_dir / f"scene_{scene_idx:02d}_final.png"


def garantir_vertical(img_path, alvo=9 / 16):
    """Versao 9:16 da imagem (scene_XX_final_916.png) se ela nao for vertical.

    As imagens vinham 1024x1024 e os efeitos de painel fazem scale=2160:3840 (9:16):
    tudo saia ESTICADO 78% na vertical (rosto alongado). Quadrada/retrato largo ->
    recorte 9:16 centrado no maior rosto (Haar do OpenCV; sem rosto, no centro).
    Paisagem (muito larga) -> imagem inteira sobre fundo desfocado. Ja vertical: igual."""
    p = Path(img_path)
    try:
        from PIL import Image, ImageFilter
        im = Image.open(p).convert("RGB")
    except Exception:
        return p
    w, h = im.size
    if abs(w / h - alvo) < 0.04:
        return p
    out = p.with_name(p.stem + "_916.png")
    if out.exists() and out.stat().st_size > 1000:
        return out
    try:
        if w / h <= 1.2:
            cw = int(round(h * alvo))
            cx = w // 2
            try:
                import cv2
                import numpy as np
                g = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2GRAY)
                casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
                faces = casc.detectMultiScale(g, 1.1, 5, minSize=(w // 12, w // 12))
                if len(faces):
                    fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                    cx = fx + fw // 2
            except Exception:
                pass
            x0 = max(0, min(w - cw, cx - cw // 2))
            novo = im.crop((x0, 0, x0 + cw, h))
        else:
            H2 = int(round(w / alvo))
            fundo = im.resize((int(H2 * w / h), H2), Image.LANCZOS)
            fx0 = (fundo.width - w) // 2
            fundo = fundo.crop((fx0, 0, fx0 + w, H2)).filter(ImageFilter.GaussianBlur(28))
            fundo.paste(im, (0, (H2 - h) // 2))
            novo = fundo
        if novo.height < 1280:   # garante no minimo 720x1280
            esc = 1280 / novo.height
            novo = novo.resize((int(novo.width * esc), 1280), Image.LANCZOS)
        novo.save(out)
        return out
    except Exception:
        return p


MOOD_FRAMING = {
    "sad_emotional": "extreme close-up on face showing raw emotion, tears visible, shallow depth of field",
    "tense_dramatic": "low angle dramatic shot, strong perspective lines, character looming",
    "action": "dynamic wide angle, motion blur hints, explosive energy, tilted frame",
    "calm_chill": "wide establishing shot, serene landscape, character small in frame, breathing room",
    "romantic_sexy": "medium intimate shot, soft focus background, warm backlight, two-shot framing",
    "funny_lighthearted": "slightly tilted medium shot, exaggerated expressive pose, bright open composition",
    "neutral_chill": "balanced medium shot, natural eye-level perspective, clean background",
}


def _enrich_prompt(base_prompt, genero, scene_text="", mood=None, persona=None, texto_na_imagem=None):
    """Adiciona estilo do gênero, enquadramento por mood e instruções de qualidade."""
    import os
    style = character_bank.get_style_for_genre(genero)
    negative = character_bank.get_negative_prompt(genero)

    framing = ""
    if mood and mood in MOOD_FRAMING:
        framing = f"Camera framing: {MOOD_FRAMING[mood]}. "

    consistency = ""
    if os.environ.get("CHARACTER_CONSISTENCY", "1") == "1" and persona:
        consistency = character_bank.build_consistency_block(genero, [persona])

    text_overlay = ""
    # O roteiro as vezes manda dict/lista ({'conteudo': 'ENTREGA REALIZADA'}) e o str()
    # disso ia literal pro prompt: a imagem saia com "{'conteúdo': ...}" escrito.
    if isinstance(texto_na_imagem, dict):
        texto_na_imagem = " ".join(str(v) for v in texto_na_imagem.values() if v)
    elif isinstance(texto_na_imagem, (list, tuple)):
        texto_na_imagem = " ".join(str(v) for v in texto_na_imagem if v)
    texto_na_imagem = str(texto_na_imagem or "").strip(" {}[]'\"")
    # texto longo o modelo de imagem escreve errado e o zoom dos efeitos corta a borda
    # ("EXPOSICAO INTERNACIONAL" saiu pela metade): so placas curtas, no centro
    if texto_na_imagem and len(texto_na_imagem) <= 20 and not any(c in texto_na_imagem for c in "{}:"):
        text_overlay = (f"Image contains visible text overlay reading exactly: \"{texto_na_imagem}\" "
                        f"(spelled exactly like this), centered in the middle of the image, fully "
                        f"inside the frame with wide margins from every edge. ")
    else:
        text_overlay = "No text, letters or captions anywhere in the image. "
        # o roteiro tambem escreve o pedido de texto dentro do proprio image_prompt
        import re as _re
        base_prompt = _re.sub(r"[,.;]?\s*(the )?image contains visible text[^.]*\.?", ".", base_prompt or "",
                              flags=_re.I).strip()

    parts = [base_prompt]
    if text_overlay:
        parts.append(text_overlay)
    if consistency:
        parts.append(consistency)
    if framing:
        parts.append(framing)
    parts.append(f"Art style: {style}.")
    parts.append("High quality, detailed, cinematic composition, professional lighting.")
    parts.append("Vertical 1080x1920 format.")
    if negative:
        parts.append(f"Avoid: {negative}.")

    return " ".join(parts)


# Condicao fisica do protagonista: se aparece na maioria das cenas, vale pra TODAS.
# Cada imagem e gerada sozinha — no 1o video da prod a cena final nao dizia "wheelchair"
# e o protagonista paraplegico apareceu EM PE.
_TRACOS = [
    (r"wheelchair|cadeira de rodas", "is sitting in a wheelchair"),
    (r"crutch|muleta", "is using crutches"),
    (r"prosthetic|pr[oó]tese", "has a prosthetic limb"),
    (r"\bblind\b|white cane|\bceg[oa]\b", "is blind and uses a white cane"),
    (r"eye ?patch|tapa-olho", "wears an eye patch"),
]


def _com_tracos_fixos(cenas):
    """Copia das cenas com a condicao fisica fixa do protagonista acrescentada nos
    image_prompt que a omitem (so nas cenas em que o protagonista aparece)."""
    import re
    prompts = [c.get("image_prompt", "") for c in cenas]
    fixos = [(rx, frase) for rx, frase in _TRACOS
             if sum(1 for p in prompts if re.search(rx, p, re.I)) >= max(2, len(prompts) // 3)]
    if not fixos:
        return cenas
    # so a partir da 1a cena que mostra a condicao (antes dela pode ser o "antes" da
    # historia: acidente, hospital)
    inicio = {rx: next(i for i, p in enumerate(prompts) if re.search(rx, p, re.I)) for rx, _ in fixos}
    out = []
    for i, c in enumerate(cenas):
        p = c.get("image_prompt", "")
        protag = re.search(r"protagonista|protagonist", p, re.I) or c.get("persona") == "Protagonista"
        add = [frase for rx, frase in fixos
               if protag and i > inicio[rx] and not re.search(rx, p, re.I)]
        if add:
            c = dict(c, image_prompt=p + " The protagonist " + " and ".join(add)
                     + ", exactly as in the other scenes of this story.")
            log(f"  image_gen: traco fixo acrescentado na cena: {', '.join(add)}")
        out.append(c)
    return out


def generate_images_for_story(story, n_variations=3, story_id=None):
    """Gera imagens pra todas as cenas de uma história.

    Args:
        story: dict com 'cenas' (do story_writer)
        n_variations: quantas variações gerar por cena (default 3)
        story_id: identificador pra cache (auto-gerado se None)

    Returns:
        list de Paths das imagens finais (1 por cena), ou None nas falhas
    """
    if not story_id:
        h = hashlib.md5(json.dumps(story.get("cenas", [])[:3]).encode()).hexdigest()[:10]
        story_id = f"{story.get('genero', 'misc')}_{h}"

    cache_dir = _image_cache_dir(story_id)
    genero = story.get("genero", "superacao")
    cenas = _com_tracos_fixos(story.get("cenas", []))

    log(f"  image_gen: {len(cenas)} cenas, {n_variations} variações cada = {len(cenas)*n_variations} imgs")
    log(f"  image_gen: cache em {cache_dir}")

    # Coletar todos os jobs
    jobs = []
    for i, cena in enumerate(cenas):
        final = _final_path(cache_dir, i)
        if final.exists() and final.stat().st_size > 1000:
            continue  # já tem final escolhido

        for v in range(n_variations):
            vpath = _variation_path(cache_dir, i, v)
            if vpath.exists() and vpath.stat().st_size > 1000:
                continue  # variação já existe

            prompt = _enrich_prompt(
                cena.get("image_prompt", ""), genero,
                cena.get("texto", ""), cena.get("mood"), cena.get("persona"),
                cena.get("texto_na_imagem"))
            jobs.append({"scene": i, "variation": v, "prompt": prompt, "out": vpath})

    if not jobs:
        log("  image_gen: todas as imagens já em cache!")
        return [_final_path(cache_dir, i) for i in range(len(cenas))]

    log(f"  image_gen: {len(jobs)} imagens a gerar ({len(jobs)//BATCH_SIZE + 1} lotes)")

    # Gerar em lotes
    ok_count = 0
    fail_count = 0
    consecutive_fails = 0
    backoff_idx = 0

    # Cooldown persistente: se a cota ainda nao voltou, aborta limpo (nada e gasto)
    if QUOTA_COOLDOWN_FILE.exists():
        volta = _cooldown_ate()
        try:  # 22/10: com o Flow no PC (omniroute_image cai nele quando o gateway nao tem cota) o video nao para
            sys.path.insert(0, r"D:\flow-imagens")
            import cliente as _flow
            flow_ok = _flow.disponivel()
        except Exception:  # noqa: BLE001
            flow_ok = False
        if volta > time.time() and flow_ok:
            log("  image_gen: cota do gateway em espera — seguindo pelo Flow (Nano Banana)")
        elif volta > time.time():
            wait_min = int((volta - time.time()) // 60) + 1
            log(f"  image_gen: cota de imagem em espera — volta em {wait_min}min")
            raise ApiQuotaExhaustedError(
                f"QUOTA_COOLDOWN: aguarde {wait_min}min antes de tentar de novo")
        else:
            log("  image_gen: cooldown expirado, retomando...")
            QUOTA_COOLDOWN_FILE.unlink(missing_ok=True)

    for batch_start in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        log(f"  image_gen: lote {batch_num}...")

        for job in batch:
            # Reset exhausted flag entre cenas (omniroute_image pode setar)
            omniroute_image._exhausted = False
            success = omniroute_image._generate(job["prompt"], job["out"])
            if success:
                ok_count += 1
                consecutive_fails = 0
                backoff_idx = 0
                time.sleep(DELAY_WITHIN_BATCH_S)
            else:
                fail_count += 1
                consecutive_fails += 1

                # O gateway disse quando a cota volta: PARA o video ja (as imagens prontas
                # ficam no cache) e agenda a retomada pra essa hora. Antes seguia falhando
                # imagem por imagem e o video inteiro era descartado.
                volta_s = getattr(omniroute_image, "ULTIMO_RESET_S", 0)
                if volta_s > getattr(omniroute_image, "ESPERA_CURTA_MAX_S", 90):
                    _grava_cooldown(volta_s + 60)
                    log(f"  image_gen: cota de imagem esgotada — {ok_count} imagens em cache, "
                        f"retomar em {volta_s // 60 + 1}min")
                    raise ApiQuotaExhaustedError(
                        f"API_QUOTA_EXHAUSTED: cota de imagem volta em {volta_s // 60 + 1}min")

                if consecutive_fails >= 5:
                    # Marca cooldown persistente (não tenta de novo por 1h)
                    _grava_cooldown(QUOTA_COOLDOWN_SEC)
                    log(f"  image_gen: 5 falhas seguidas — quota esgotada, cooldown 1h gravado")
                    log(f"  image_gen: geradas: {ok_count}/{len(jobs)}, falhas: {fail_count}")
                    raise ApiQuotaExhaustedError(
                        "API_QUOTA_EXHAUSTED: 5 falhas seguidas — aguardando 1h")

                # Backoff exponencial: 20s → 60s → 180s → 360s → 600s
                wait_s = QUOTA_BACKOFF_SEQUENCE[min(backoff_idx, len(QUOTA_BACKOFF_SEQUENCE)-1)]
                backoff_idx += 1
                log(f"  image_gen: falha {consecutive_fails}/5, backoff {wait_s}s...")
                time.sleep(wait_s)

        if consecutive_fails >= 5:
            break

        # Pausa entre lotes (só se ainda há jobs e geramos algo)
        if batch_start + BATCH_SIZE < len(jobs) and ok_count > 0:
            log(f"  image_gen: pausa entre lotes {PAUSE_BETWEEN_BATCHES_S}s...")
            time.sleep(PAUSE_BETWEEN_BATCHES_S)

    log(f"  image_gen: concluído — {ok_count} ok, {fail_count} falhas")

    # Retornar lista de imagens finais (a melhor variação, ou a primeira disponível)
    results = []
    for i in range(len(cenas)):
        final = _final_path(cache_dir, i)
        if final.exists() and final.stat().st_size > 1000:
            results.append(final)
            continue

        # Pegar primeira variação disponível como "final" provisório
        best = None
        for v in range(n_variations):
            vpath = _variation_path(cache_dir, i, v)
            if vpath.exists() and vpath.stat().st_size > 1000:
                best = vpath
                break

        if best:
            try:
                shutil.copy2(best, final)
            except PermissionError:
                time.sleep(1)
                try:
                    shutil.copy2(best, final)
                except PermissionError:
                    log(f"  Aviso: não conseguiu copiar {best.name} para {final.name} (arquivo em uso).")
                    if not final.exists():
                        log("  Erro: O arquivo final não existe e a cópia falhou!")
            results.append(final)
        else:
            results.append(None)

    return results


def get_story_id(story):
    """Gera ID estável pra uma história (pra cache)."""
    h = hashlib.md5(json.dumps(story.get("cenas", [])[:3]).encode()).hexdigest()[:10]
    return f"{story.get('genero', 'misc')}_{h}"
