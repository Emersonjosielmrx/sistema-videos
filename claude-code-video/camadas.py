"""Prepara cada foto de cena para os efeitos VIVOS do Remotion (28/10, incorporado do historias-em-frames).

Por foto (img_N.jpg na pasta pública) gera, quando dá:
  img_N_prof.png    profundidade 0..255 (perto = claro). Depth-Anything-V2-Small ONNX int8 (27 MB, CPU, ~2 s),
                    o mesmo do hipercool (fx_parallax). Serve ao <Profundidade> (2.5D de verdade, por pixel).
  img_N_meio.png    camadas para o <Camadas25D>: a foto inteira fica embaixo (sem buraco quando as camadas andam) e
  img_N_perto.png   por cima o que está no meio e o que está perto, com borda suave (ideia do parallax_engine).
  img_N_recorte.png o assunto principal sem fundo (rembg isnet, como as fotos do dono), só se ocupa 10–80% da tela
                    (senão não é um personagem/objeto: é paisagem ou detalhe).
  img_N_limpo.jpg   o fundo SEM o assunto (inpainting Telea + desfoque, porte do _fundo_limpo): sem isso o recorte
                    anda por cima da foto original e aparecem DOIS rostos (lição do historias-em-frames, 02/10).
Falhou uma parte = só ela falta (o editor usa o que existe; a cena segue com FotoViva).
"""
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

MODELO = Path(r"D:\hipercool-materiais\models\depth-anything-v2-small\model_int8.onnx")
_sess = None


def _ram_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / 2**30
    except Exception:  # noqa: BLE001
        return 9.0


def profundidade(im):
    """0..1 float32 do tamanho da foto, perto = 1."""
    global _sess
    if _sess is None:
        import onnxruntime as ort
        op = ort.SessionOptions()
        op.intra_op_num_threads = 2  # não toma a CPU da produção
        _sess = ort.InferenceSession(str(MODELO), op, providers=["CPUExecutionProvider"])
    inp = np.asarray(im.convert("RGB").resize((518, 518)), np.float32).transpose(2, 0, 1)[None] / 255.0
    out = _sess.run(None, {_sess.get_inputs()[0].name: inp})[0][0]
    out = out[0] if out.ndim == 3 else out
    out = (out - out.min()) / max(1e-6, float(out.max() - out.min()))
    return np.asarray(Image.fromarray((out * 255).astype(np.uint8)).resize(im.size, Image.BILINEAR), np.float32) / 255


def _puxa_empurra(img, valido):
    """Preenche o buraco com a média ponderada da vizinhança em pirâmide (fica um fundo desfocado natural).
    O inpainting Telea do historias-em-frames deixava RISCOS radiais num buraco do tamanho de uma pessoa."""
    import cv2
    imgs, pesos = [img * valido[..., None]], [valido]
    while min(imgs[-1].shape[:2]) > 6:
        imgs.append(cv2.pyrDown(imgs[-1]))
        pesos.append(cv2.pyrDown(pesos[-1]))
    fill = imgs[-1] / np.maximum(pesos[-1], 1e-4)[..., None]
    for c, p in zip(reversed(imgs[:-1]), reversed(pesos[:-1])):
        up = cv2.pyrUp(fill, dstsize=(c.shape[1], c.shape[0]))
        a = np.clip(p * 3, 0, 1)[..., None]
        fill = c / np.maximum(p, 1e-4)[..., None] * a + up * (1 - a)
    return fill


def fundo_limpo(im, mascara):
    """Foto sem o assunto: tira a região (dilatada) e preenche pela vizinhança em 512 px, desfocado."""
    import cv2
    img = cv2.cvtColor(np.asarray(im.convert("RGB")), cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]
    m = (np.asarray(mascara.resize((w, h))) > 30).astype(np.uint8) * 255
    k = max(5, int(min(h, w) * 0.025)) | 1
    m = cv2.dilate(m, np.ones((k, k), np.uint8), iterations=2)
    s = 512.0 / max(h, w)
    sw, sh = max(8, int(w * s)), max(8, int(h * s))
    pequeno = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA).astype(np.float32)
    valido = (cv2.resize(m, (sw, sh), interpolation=cv2.INTER_NEAREST) < 128).astype(np.float32)
    fill = np.clip(_puxa_empurra(pequeno, valido), 0, 255).astype(np.uint8)
    fill = cv2.resize(cv2.GaussianBlur(fill, (0, 0), 3), (w, h), interpolation=cv2.INTER_CUBIC)
    a = (cv2.GaussianBlur(m, (0, 0), k / 2.0).astype(np.float32) / 255.0)[..., None]
    res = (img.astype(np.float32) * (1 - a) + fill.astype(np.float32) * a).astype(np.uint8)
    return Image.fromarray(cv2.cvtColor(res, cv2.COLOR_BGR2RGB))


def _camada(im, d, de):
    m = Image.fromarray(((d >= de) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
    c = im.convert("RGBA")
    c.putalpha(m)
    return c


def preparar(img_path, pub, n, recorte=None, log=print, prazo=150):
    """Gera os arquivos da cena n em `pub`. recorte = função(PIL) -> (máscara L | None, cobertura)."""
    t0 = time.time()
    out = {}
    if _ram_gb() < 1.2:
        log(f"  [vivo] cena {n}: RAM baixa, sem camadas")
        return out
    im = Image.open(img_path).convert("RGB")
    try:
        if MODELO.exists():
            d = profundidade(im)
            Image.fromarray((d * 255).astype(np.uint8)).save(pub / f"img_{n}_prof.png")
            _camada(im, d, 0.42).save(pub / f"img_{n}_meio.png")
            _camada(im, d, 0.70).save(pub / f"img_{n}_perto.png")
            out.update(profundidade=f"img_{n}_prof.png", camadas=["img_%d.jpg" % n, f"img_{n}_meio.png",
                                                                  f"img_{n}_perto.png"])
    except Exception as e:  # noqa: BLE001
        log(f"  [vivo] cena {n}: profundidade falhou ({type(e).__name__}: {str(e)[:80]})")
    if recorte and time.time() - t0 < prazo:
        try:
            m, cob = recorte(im)
            if m is not None and 0.10 <= cob <= 0.80:
                r = im.convert("RGBA")
                r.putalpha(m)
                r.save(pub / f"img_{n}_recorte.png")  # do tamanho da tela: encaixa por cima do limpo sem conta
                fundo_limpo(im, m).save(pub / f"img_{n}_limpo.jpg", quality=90)
                box = m.point(lambda v: 255 if v > 128 else 0).getbbox()
                out.update(recorte=f"img_{n}_recorte.png", fundo_limpo=f"img_{n}_limpo.jpg",
                           assunto_caixa=list(box) if box else None, assunto_cobre=round(cob, 2))
        except Exception as e:  # noqa: BLE001
            log(f"  [vivo] cena {n}: recorte falhou ({type(e).__name__}: {str(e)[:80]})")
    return out
