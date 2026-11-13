"""Transforma fotos de documentos em "escaneados": recorta a folha, endireita a
perspectiva, tira sombra/fundo e deixa o papel branco e o texto escuro.

Uso: python -I escanear_documentos.py <pasta_fotos> <pasta_saida>
Os cantos aproximados de cada folha ficam em PAGINAS (refinados sozinhos pela borda).
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

DPI = 200
LARGURA_MM = 210

# arquivo -> (nome de saída, cantos aproximados TL, TR, BR, BL em pixels da foto,
#             lados a refinar pela borda real: t, r, b, l)
# Canto fora da foto pode ter coordenada negativa; o que cair fora vira papel branco.
PAGINAS = {
    "WhatsApp Image 2026-10-19 at 08.48.45.jpeg": (
        "01_contrato_compra_e_venda",
        [(36, 87), (812, 86), (879, 1255), (-3, 1226)], "trb",
        [[(20, 60), (89, 60), (87, 135), (20, 134)]]),  # canto de cima dobrado
    "WhatsApp Image 2026-10-19 at 08.48.45 (1).jpeg": (
        "02_declaracao_quitacao_divida",
        [(-3, 149), (770, 177), (806, 1329), (-3, 1298)], "trb",
        [[(-10, 120), (46, 120), (46, 199), (-10, 196)],  # canto de cima dobrado
         [(-10, 1223), (57, 1225), (57, 1340), (-10, 1340)]]),  # sombra no pé da folha
    "WhatsApp Image 2026-10-19 at 08.48.45 (2).jpeg": (
        "03_certidao_positiva_efeito_negativa",
        [(60, 42), (800, 88), (806, 1271), (-48, 1215)], "trb",
        # canto de cima à direita envergado: depois da curva aparecem outros papéis
        [[(802, 60), (900, 60), (900, 340), (840, 340), (838, 300), (833, 250), (822, 200),
          (812, 150), (802, 95)]]),
    "WhatsApp Image 2026-10-19 at 08.48.45 (3).jpeg": (
        "04_iptu_documento_arrecadacao",
        [(0, 262), (795, 228), (897, 1080), (0, 1125)], "rb",
        [
            # comprovante da lotérica caído por cima do canto (não é deste documento),
            # com a sombra dele e o resto do brasão que ficou por baixo (só mancha preta)
            [(-5, 150), (310, 150), (310, 366), (190, 392), (190, 420), (140, 424),
             (80, 428), (30, 436), (-5, 450)],
            # canto de cima à direita enrolado (aparece o lençol por trás)
            [(770, 190), (840, 190), (840, 300), (812, 300), (798, 250), (785, 222)],
        ]),
    "WhatsApp Image 2026-10-19 at 08.48.45 (4).jpeg": (
        "05_boletim_cadastro_imobiliario",
        [(41, 90), (853, 88), (895, 1305), (15, 1270)], "trb",
        [
            # sombra de algo em cima da folha, no canto (fora do quadro do cabeçalho)
            [(46, 80), (99, 80), (99, 122), (80, 128), (46, 128)],
            # canto de baixo à esquerda arredondado (aparece o lençol)
            [(-5, 1165), (95, 1168), (100, 1268), (150, 1276), (160, 1340), (-5, 1340)],
        ]),
}


def mascara_papel(img):
    """1 onde é papel (claro), 0 no lençol. Limiar de Otsu sobre a foto borrada."""
    cinza = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (0, 0), 2.5)
    limiar, _ = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = (cinza > limiar).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return m, limiar


def refinar_lado(mask, p0, p1, centro, raio=45):
    """Acha a transição lençol->papel perto da reta p0-p1 e ajusta uma reta nela."""
    p0, p1 = np.float64(p0), np.float64(p1)
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    n = np.array([-d[1], d[0]])
    if np.dot(centro - (p0 + p1) / 2, n) < 0:
        n = -n  # normal apontando para dentro da folha
    h, w = mask.shape
    achados = []
    s = np.arange(-raio, raio + 1)
    for t in np.linspace(0.06, 0.94, 80):
        p = p0 + t * (p1 - p0)
        pts = np.round(p[None, :] + s[:, None] * n[None, :]).astype(int)
        ok = (pts[:, 0] >= 0) & (pts[:, 0] < w) & (pts[:, 1] >= 0) & (pts[:, 1] < h)
        if not ok.all():
            continue
        v = mask[pts[:, 1], pts[:, 0]]
        # transições fora(0) -> dentro(1) com papel firme por 12 px adiante
        cand = [i for i in range(1, len(s) - 12) if v[i - 1] == 0 and v[i:i + 12].all()]
        if cand:
            i = min(cand, key=lambda i: abs(s[i]))
            achados.append(pts[i] - 0.5 * n)
    if len(achados) < 15:
        return None, len(achados), achados
    a = np.float32(achados)
    for corte in (6, 3):  # ajusta, descarta quem fugiu da reta (canto dobrado, outro papel)
        vx, vy, x0, y0 = cv2.fitLine(a, cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
        dist = np.abs((a[:, 0] - x0) * vy - (a[:, 1] - y0) * vx)
        if (dist < corte).sum() < 12:
            return None, len(achados), achados
        a = a[dist < corte]
    vx, vy, x0, y0 = cv2.fitLine(a, cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
    return (np.array([x0, y0]), np.array([vx, vy])), len(a), achados


def cruzar(l1, l2):
    (p, d), (q, e) = l1, l2
    m = np.array([[d[0], -e[0]], [d[1], -e[1]]])
    t = np.linalg.solve(m, q - p)
    return p + t[0] * d


def cantos_refinados(mask, aprox, lados):
    c = np.float64(aprox)
    centro = c.mean(axis=0)
    retas, log, pontos = [], [], []
    for k, nome in enumerate("trbl"):
        p0, p1 = c[k], c[(k + 1) % 4]
        manual = (p0, (p1 - p0) / np.linalg.norm(p1 - p0))
        if nome in lados:
            reta, n, achados = refinar_lado(mask, p0, p1, centro)
            pontos += achados
            log.append(f"{nome}:{n}{'' if reta is not None else '(manual)'}")
            retas.append(reta if reta is not None else manual)
        else:
            log.append(f"{nome}:manual")
            retas.append(manual)
    # retas: topo, direita, baixo, esquerda -> cantos TL, TR, BR, BL
    novos = [cruzar(retas[3], retas[0]), cruzar(retas[0], retas[1]),
             cruzar(retas[1], retas[2]), cruzar(retas[2], retas[3])]
    return np.float64(novos), " ".join(log), pontos


def proporcao_real(cantos, w, h):
    """Altura/largura real da folha (Zhang & He, quadro branco), com foco estimado."""
    u0, v0 = w / 2, h / 2
    tl, tr, br, bl = [np.array([x, y, 1.0]) for x, y in cantos]
    m1, m2, m3, m4 = tl, tr, bl, br
    k2 = np.dot(np.cross(m1, m4), m3) / np.dot(np.cross(m2, m4), m3)
    k3 = np.dot(np.cross(m1, m4), m2) / np.dot(np.cross(m3, m4), m2)
    n2 = k2 * m2 - m1
    n3 = k3 * m3 - m1
    f_padrao = 0.6 * np.hypot(w, h)  # celular ~26 mm equivalente
    f = f_padrao
    if abs(n2[2] * n3[2]) > 1e-9:
        f2 = -((n2[0] * n3[0] - (n2[0] * n3[2] + n2[2] * n3[0]) * u0 + n2[2] * n3[2] * u0 ** 2)
               + (n2[1] * n3[1] - (n2[1] * n3[2] + n2[2] * n3[1]) * v0 + n2[2] * n3[2] * v0 ** 2)) / (n2[2] * n3[2])
        if f2 > 0 and 0.5 * f_padrao < np.sqrt(f2) < 2 * f_padrao:
            f = np.sqrt(f2)
    a = np.array([[f, 0, u0], [0, f, v0], [0, 0, 1]])
    ai = np.linalg.inv(a)
    wh = np.sqrt((n2 @ ai.T @ ai @ n2) / (n3 @ ai.T @ ai @ n3))
    return 1 / wh, f


def fundo_branco(img):
    """Divide cada canal pela iluminação do papel (tira sombra e amarelado)."""
    h, w = img.shape[:2]
    escala = 4
    peq = cv2.resize(img, (w // escala, h // escala), interpolation=cv2.INTER_AREA)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (41, 41))
    papel = cv2.dilate(peq, k)  # máximo local = papel sem a tinta
    papel = cv2.medianBlur(papel, 21)
    papel = cv2.GaussianBlur(papel, (0, 0), 8)
    papel = cv2.resize(papel, (w, h), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    out = img.astype(np.float32) / np.maximum(papel, 1) * 255
    return np.clip(out, 0, 255)


def niveis(img, preto=55, branco=228, gama=1.25):
    x = np.clip((img - preto) / (branco - preto), 0, 1)
    return x ** gama * 255


def realcar_cor(img_u8, ganho=1.35):
    hsv = cv2.cvtColor(img_u8, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * ganho, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def lencol_na_borda(papel, faixa):
    """Pedaços não-papel encostados na borda da folha (lençol, canto dobrado),
    limitados a uma faixa junto da borda pra nunca apagar texto do meio."""
    nao_papel = (papel == 0).astype(np.uint8)
    n, rot = cv2.connectedComponents(nao_papel, connectivity=4)
    borda = np.unique(np.concatenate([rot[0], rot[-1], rot[:, 0], rot[:, -1]]))
    fundo = np.isin(rot, borda[borda > 0])
    h, w = papel.shape
    perto = np.zeros((h, w), bool)
    perto[:faixa], perto[-faixa:], perto[:, :faixa], perto[:, -faixa:] = True, True, True, True
    fundo &= perto
    # engorda um pouco pra levar junto a sombra da beirada
    return cv2.dilate(fundo.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0


def sujeira_na_borda(x, faixa):
    """Manchas escuras encostadas na beirada que cabem inteiras na faixa da borda
    (sombra do vão, pontinhos do lençol, beirada de outra folha). Texto e linhas
    do formulário não encostam na beirada ou passam da faixa, então ficam."""
    cinza = cv2.cvtColor(x, cv2.COLOR_BGR2GRAY)
    escuro = (cinza < 215).astype(np.uint8)
    n, rot, st, _ = cv2.connectedComponentsWithStats(escuro, connectivity=8)
    h, w = cinza.shape
    sujo = np.zeros(n, bool)
    for i in range(1, n):
        x0, y0, bw, bh = st[i, :4]
        x1, y1 = x0 + bw - 1, y0 + bh - 1
        sujo[i] = ((x0 <= 2 and x1 < faixa) or (x1 >= w - 3 and x0 >= w - faixa)
                   or (y0 <= 2 and y1 < faixa) or (y1 >= h - 3 and y0 >= h - faixa))
    return cv2.dilate(sujo[rot].astype(np.uint8), np.ones((5, 5), np.uint8)) > 0


def escanear(img, cantos, mask, tampar=None):
    h_img, w_img = img.shape[:2]
    razao, f = proporcao_real(cantos, w_img, h_img)
    larg = round(LARGURA_MM / 25.4 * DPI)
    alt = round(larg * razao)
    destino = np.float32([[0, 0], [larg - 1, 0], [larg - 1, alt - 1], [0, alt - 1]])
    m = cv2.getPerspectiveTransform(np.float32(cantos), destino)
    limpa = cv2.fastNlMeansDenoisingColored(img, None, 3, 3, 5, 15)
    folha = cv2.warpPerspective(limpa, m, (larg, alt), flags=cv2.INTER_LANCZOS4,
                                borderMode=cv2.BORDER_REPLICATE)
    dentro_foto = cv2.warpPerspective(np.full(img.shape[:2], 255, np.uint8), m, (larg, alt),
                                      flags=cv2.INTER_NEAREST, borderValue=0)
    # fora da foto conta como papel (vai ficar branco de qualquer jeito)
    papel = cv2.warpPerspective(mask, m, (larg, alt), flags=cv2.INTER_NEAREST, borderValue=1)
    x = fundo_branco(folha)
    x = niveis(x)
    x = x.astype(np.uint8)
    x = realcar_cor(x)
    borrado = cv2.GaussianBlur(x, (0, 0), 1.6)
    x = cv2.addWeighted(x, 1.5, borrado, -0.5, 0)
    x[dentro_foto == 0] = 255  # parte da folha fora da foto vira papel branco
    x[lencol_na_borda(papel, round(0.035 * larg))] = 255
    x[sujeira_na_borda(x, round(0.035 * larg))] = 255
    for poligono in tampar or []:
        pts = cv2.perspectiveTransform(np.float32([poligono]), m)[0]
        cv2.fillPoly(x, [np.int32(np.round(pts))], (255, 255, 255))
    return x, razao, f


def main():
    origem, saida = Path(sys.argv[1]), Path(sys.argv[2])
    saida.mkdir(parents=True, exist_ok=True)
    debug = saida / "_conferencia"
    debug.mkdir(exist_ok=True)
    paginas_pdf = []
    for arq, (nome, aprox, lados, *tampar) in PAGINAS.items():
        img = cv2.imdecode(np.fromfile(str(origem / arq), np.uint8), cv2.IMREAD_COLOR)
        mask, limiar = mascara_papel(img)
        cantos, log, pontos = cantos_refinados(mask, aprox, lados)
        resultado, razao, f = escanear(img, cantos, mask, tampar[0] if tampar else None)
        print(f"{nome}: {log} | limiar {limiar:.0f} | razao {razao:.3f} f {f:.0f} | "
              f"{resultado.shape[1]}x{resultado.shape[0]} | cantos {np.round(cantos).astype(int).tolist()}")
        pad = 60
        marcada = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(40, 40, 40))
        cv2.polylines(marcada, [np.int32(np.float64(aprox) + pad)], True, (0, 0, 255), 1)
        for p in pontos:
            cv2.circle(marcada, tuple(np.int32(np.round(p + pad))), 2, (255, 0, 255), -1)
        cv2.polylines(marcada, [np.int32(np.round(cantos + pad))], True, (0, 220, 0), 1)
        cv2.imencode(".jpg", marcada)[1].tofile(str(debug / f"{nome}_cantos.jpg"))
        rgb = Image.fromarray(cv2.cvtColor(resultado, cv2.COLOR_BGR2RGB))
        rgb.save(saida / f"{nome}.png", dpi=(DPI, DPI), optimize=True)
        rgb.save(saida / f"{nome}.jpg", dpi=(DPI, DPI), quality=95, subsampling=0)
        paginas_pdf.append(rgb)
    pdf = saida / "documentos_da_casa_escaneados.pdf"
    paginas_pdf[0].save(pdf, save_all=True, append_images=paginas_pdf[1:],
                        resolution=DPI, quality=92, subsampling=0)
    print("PDF:", pdf)


if __name__ == "__main__":
    main()
