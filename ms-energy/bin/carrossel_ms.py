# -*- coding: utf-8 -*-
"""Carrossel educativo do MS Energy no Instagram (dono 22/10/2026: "faça a postagem de imagens e carrosséis").

6 imagens 1080x1350 (4:5): capa (pergunta sobre foto REAL de instalação da empresa — Instagram antigo ou Google Fotos),
4 slides (uma ideia cada, com ilustração Nano Banana 2.1 pelo Google Flow desde 22/10; reserva Cloudflare FLUX.2 klein —
só ilustração, nunca "instalação da empresa" — conferida por visão; falhou = foto real) e CTA (orçamento
grátis/WhatsApp). Texto com as regras do roteiro_ms (sem zerar, número, concessionária, "garantir"; acento; revisor).
Publica pela API do Instagram como carrossel. Rodar com D:\\veo\\venv (o gerador do Flow usa playwright/filelock de lá).
    python carrossel_ms.py               # posta o já produzido e não postado (até 4 dias); senão gera e posta
    python carrossel_ms.py --so-gerar    # produz em videos\\carrosseis\\<data> sem postar (a tarefa posta depois)
    python carrossel_ms.py --postar <pasta>
Tarefa MSEnergy_Carrossel (terça, quinta e sábado 12:37, sem janela).
"""
import argparse
import io
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, r"D:\ms-energy\bin")
sys.path.insert(0, r"D:\veo\beta")
import roteiro_ms  # noqa: E402
from montagem_ms import FONTE_BLACK, FONTE_XBOLD, VERMELHO, _f, _logo_rgba, _quebrar  # noqa: E402

W, H = 1080, 1350
DIR = Path(r"D:\ms-energy\videos\carrosseis")
HIST = Path(r"D:\ms-energy\cache\historico_carrosseis.json")
CREDS = Path(r"D:\credenciais-canais\instagram_contas.json")
GRAPH = "https://graph.instagram.com/v21.0"
MODELO_IMG = "@cf/black-forest-labs/flux-2-klein-4b"
ESCURO = (17, 17, 20)


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def _hist():
    try:
        return json.loads(HIST.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return []


# ───────────────────────────── texto ─────────────────────────────

def _pedir_textos(pauta, capas_usadas, correcao):
    from llm_client import _call_gemini_native
    system = ("Você escreve carrosséis educativos de Instagram para uma empresa REAL de energia solar. Objetivo: ensinar "
              "e gerar pedidos de orçamento, com confiança e clareza. Português do Brasil com acentuação correta. "
              "Responda SÓ JSON válido.")
    user = f"""Empresa: {roteiro_ms.EMPRESA}
Assunto deste carrossel (só a ideia; NÃO copie estas palavras): {pauta[2]}

Regras obrigatórias:
- NÃO prometer conta zerada, "zerar", R$ 0 ou "de graça". NÃO usar números, porcentagens, preços, prazos ou anos.
- NÃO citar distribuidora/concessionária. Nada de "segredo" ou "ninguém te conta".
- PROIBIDA qualquer forma da palavra garantir: "garante", "garantir", "garantem", "garantido", "garantindo" (a trava
  reprova). Use "ajuda a", "evita", "deixa", "mantém" no lugar. Só "garantia de fábrica" é permitido.
- "capa": pergunta ou frase forte de 3 a 8 palavras.
- "slides": exatamente 4 itens, cada um com "titulo" (2 a 6 palavras) e "texto" (12 a 28 palavras, uma ideia só,
  linguagem simples, útil e honesta). Do primeiro ao último, eles respondem a capa.
- "imagens": exatamente 4 descrições em INGLÊS de uma FOTO ilustrativa realista para cada slide (sem pessoas, sem
  texto, sem logotipos; casas, telhados, sol, chuva, campo ou comércio do norte do Brasil quando couber).
- "legenda": 2 ou 3 linhas curtas para o Instagram, sem convite no final e sem hashtags.
- "titulo": até 60 caracteres.
Capas já usadas (não repita): {capas_usadas[-20:]}
{correcao}
Responda SÓ: {{"capa": "...", "slides": [{{"titulo": "...", "texto": "..."}}], "imagens": ["..."], "legenda": "...", "titulo": "..."}}"""
    txt = _call_gemini_native(system, user, max_tokens=1600, temperatura=0.8)
    return json.loads(re.search(r"\{.*\}", txt, re.S).group(0))


def _validar(t):
    erros = []
    slides = t.get("slides") or []
    if len(slides) != 4 or len(t.get("imagens") or []) != 4:
        return ["precisa de exatamente 4 slides e 4 imagens"]
    if not 2 <= len((t.get("capa") or "").split()) <= 9:
        erros.append("capa precisa de 3 a 8 palavras")
    for i, s in enumerate(slides, 1):
        if not 1 <= len((s.get("titulo") or "").split()) <= 7:
            erros.append(f"slide {i}: título com 2 a 6 palavras")
        if not 8 <= len((s.get("texto") or "").split()) <= 32:
            erros.append(f"slide {i}: texto com 12 a 28 palavras")
    campos = [t.get("capa", ""), t.get("legenda", ""), t.get("titulo", "")] + \
             [s.get("titulo", "") + " " + s.get("texto", "") for s in slides]
    for c in campos:
        erros += roteiro_ms.problemas_texto(c)
        sem = sorted(set(re.findall(roteiro_ms._SEM_ACENTO, c.lower())))
        if sem:
            erros.append(f"sem acento ({', '.join(sem)})")
    return sorted(set(erros))


def gerar_textos(pauta):
    capas = [h.get("capa", "") for h in _hist()]
    correcao = ""
    for tentativa in range(3):
        try:
            t = _pedir_textos(pauta, capas, correcao)
        except Exception as e:  # noqa: BLE001
            log(f"LLM falhou ({type(e).__name__}: {str(e)[:80]})")
            continue
        erros = _validar(t)
        if not erros:
            ok, problema = roteiro_ms._revisar(" ".join(s["texto"] for s in t["slides"]), pauta[2], tipo="carrossel")
            if not ok:
                erros = [f"revisor: {problema[:150]}"]
        if not erros:
            return t
        log(f"textos reprovados (tentativa {tentativa + 1}): {'; '.join(erros)[:200]}")
        correcao = "CORRIJA a resposta anterior: " + "; ".join(erros)
    return None


# ───────────────────────────── imagens ─────────────────────────────

_PERG_IMG = ('Esta imagem vai ilustrar um post de uma empresa de energia solar. Responda SO JSON: {"texto_ou_letras": '
             'true se aparece qualquer letra, numero, palavra ou logotipo, "pessoas": true se aparece pessoa ou parte '
             'do corpo, "deformado": true se ha objeto torto, derretido ou impossivel, "parece_foto": true se parece '
             'fotografia real, "nota": 1 a 10 (bonita e profissional?)}')


def _flow(pr, destino):
    """Nano Banana 2.1 pelo Google Flow (D:\\flow-imagens, contas do Veo, 0 crédito no teste de 22/10). 16:9 = a faixa
    de imagem do slide (1080x680). None se nenhuma conta entregou."""
    sys.path.insert(0, r"D:\flow-imagens")
    from gera_imagem import gerar_imagem
    import threading
    res = {}

    def _rodar():
        try:
            res["im"] = Image.open(gerar_imagem(pr, destino, formato="16:9", log=lambda m: None)[0]).convert("RGB")
        except Exception as e:  # noqa: BLE001
            res["erro"] = e

    # 01/11: o Flow ocupado (rajada de capas) prendeu o carrossel 1 h sem chegar à reserva — no máx. 6 min aqui
    t = threading.Thread(target=_rodar, daemon=True)
    t.start()
    t.join(360)
    if t.is_alive():
        log("Flow passou de 6 min — sigo para a reserva")
        return None
    if "erro" in res:
        log(f"Flow falhou: {str(res['erro'])[:160]}")
        return None
    return res.get("im")


def _cloudflare(pr):
    sys.path.insert(0, r"D:\hipercool-videos\bin")
    import imagem_reserva
    try:
        return Image.open(io.BytesIO(imagem_reserva.gerar_com(MODELO_IMG, pr, "9:16"))).convert("RGB")
    except Exception as e:  # noqa: BLE001
        log(f"Cloudflare falhou: {str(e)[:120]}")
        return None


def ilustracao(prompt_en, destino):
    """(imagem, origem). Dono 22/10 ("sim troque"): 1º Nano Banana pelo Flow (bem melhor), reserva FLUX.2 klein na
    Cloudflare (60 contas do hipercool, sempre pelo proxy). Toda imagem é conferida por visão."""
    import qa_ms
    pr = (prompt_en.strip().rstrip(".") + ". Setting: small town or countryside in Pará, northern Brazil (ceramic tile "
          "or fiber-cement roofs, tropical vegetation; never snow, chimneys or asphalt shingles). Realistic photograph, "
          "natural light. No people, no text, no letters, no logos, no watermark.")
    for origem, fazer in (("flow nano banana", lambda: _flow(pr, destino)), ("cloudflare", lambda: _cloudflare(pr)),
                          ("cloudflare", lambda: _cloudflare(pr))):
        im = fazer()
        if im is None:
            continue
        buf = io.BytesIO()
        im.copy().resize((im.width // 2, im.height // 2)).save(buf, "JPEG", quality=85)
        v = qa_ms.visao_json(buf.getvalue(), _PERG_IMG)
        if "_erro" in v:
            log(f"visão indisponível ({v['_erro']}) — imagem não conferida, uso foto real")
            return None, "sem visão"
        if not (v.get("texto_ou_letras") or v.get("pessoas") or v.get("deformado")) and int(v.get("nota") or 0) >= 6:
            return im, origem
        log(f"ilustração reprovada ({origem}): {v}")
    return None, "reprovada"


def foto_real(evitar=()):
    boas = [b for b in roteiro_ms.fotos_boas() if b[0] not in evitar]
    if not boas:
        return None, None
    nome, _ = random.choice(boas)
    return roteiro_ms._aparar_bordas(Image.open(roteiro_ms.FOTOS_DIR / nome).convert("RGB")), nome


# ───────────────────────────── desenho ─────────────────────────────

def _caber(d, texto, fonte, tam, largura, max_linhas, minimo=26):
    while True:
        f = _f(fonte, tam)
        linhas = _quebrar(d, texto, f, largura)
        if len(linhas) <= max_linhas or tam <= minimo:
            return f, linhas
        tam -= 2


def _degrade(im, de_y, ate_y, alfa_max, de_baixo=True):
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for y in range(de_y, ate_y):
        f = (y - de_y) / max(ate_y - de_y, 1)
        gd.line([(0, y), (im.width, y)], fill=ESCURO + (int(alfa_max * (f if de_baixo else 1 - f)),))
    return Image.alpha_composite(im, g)


def capa(foto, texto, destino):
    im = ImageOps.fit(foto, (W, H)).convert("RGBA")
    im = _degrade(im, int(H * 0.35), H, 235)
    im = _degrade(im, 0, 220, 150, de_baixo=False)
    lg = _logo_rgba(300)
    im.alpha_composite(lg, (50, 30))
    d = ImageDraw.Draw(im)
    f, linhas = _caber(d, texto, FONTE_BLACK, 100, W - 120, 4)
    alt = len(linhas) * int(f.size * 1.15)
    y = H - 210 - alt
    d.rectangle((60, y - 34, 220, y - 22), fill=VERMELHO)
    for ln in linhas:
        d.text((60, y), ln, font=f, fill="white")
        y += int(f.size * 1.15)
    d.text((60, H - 120), "Arraste para o lado  →", font=_f(FONTE_XBOLD, 36), fill=(225, 225, 225))
    im.convert("RGB").save(destino, quality=92)


def slide(img, n, total, titulo, texto, destino):
    im = Image.new("RGBA", (W, H), ESCURO + (255,))
    alto_img = 680  # imagem em cima; titulo + texto (ate 5 linhas) cabem antes do rodape (logo em y ~1170)
    im.paste(ImageOps.fit(img, (W, alto_img)).convert("RGBA"), (0, 0))
    im = _degrade(im, alto_img - 220, alto_img, 255)
    d = ImageDraw.Draw(im)
    pilula = f"{n}/{total}"
    fp = _f(FONTE_BLACK, 40)
    lw = d.textlength(pilula, font=fp)
    d.rounded_rectangle((W - lw - 110, 40, W - 40, 110), radius=35, fill=VERMELHO)
    d.text((W - lw - 75, 50), pilula, font=fp, fill="white")
    y = alto_img - 30
    ft, lt = _caber(d, titulo, FONTE_BLACK, 70, W - 160, 2)
    d.rectangle((60, y + 8, 72, y + 8 + len(lt) * int(ft.size * 1.12) - 14), fill=VERMELHO)
    for ln in lt:
        d.text((95, y), ln, font=ft, fill="white")
        y += int(ft.size * 1.12)
    y += 24
    fx, lx = _caber(d, texto, FONTE_XBOLD, 46, W - 150, 5, minimo=34)
    for ln in lx:
        d.text((95, y), ln, font=fx, fill=(232, 232, 232))
        y += int(fx.size * 1.3)
    lg = _logo_rgba(150)
    im.alpha_composite(lg, (60, H - lg.height - 30))
    fa = _f(FONTE_XBOLD, 32)
    d.text((W - 60 - d.textlength("@msenergycap", font=fa), H - 75), "@msenergycap", font=fa, fill=(200, 200, 200))
    im.convert("RGB").save(destino, quality=92)


def cta(foto, destino):
    im = ImageOps.fit(foto, (W, H)).filter(ImageFilter.GaussianBlur(4))
    im = Image.blend(im, Image.new("RGB", (W, H), ESCURO), 0.72).convert("RGBA")
    lg = _logo_rgba(480)
    im.alpha_composite(lg, ((W - lg.width) // 2, 110))
    d = ImageDraw.Draw(im)

    def centro(t, f, y, cor="white"):
        d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=cor)

    y = 110 + lg.height + 50
    centro("Orçamento grátis", _caber(d, "Orçamento grátis", FONTE_BLACK, 110, W - 100, 1)[0], y)
    y += 150
    for ln in _quebrar(d, "Energia solar para casa, comércio e campo", _f(FONTE_XBOLD, 50), W - 140):
        centro(ln, _f(FONTE_XBOLD, 50), y)
        y += 66
    y += 40
    fb = _f(FONTE_BLACK, 62)
    t = "Chame no WhatsApp"
    lw = d.textlength(t, font=fb)
    d.rounded_rectangle(((W - lw) / 2 - 60, y - 24, (W + lw) / 2 + 60, y + 96), radius=60, fill=VERMELHO)
    centro(t, fb, y)
    y += 170
    centro("Link na bio  •  @msenergycap", _f(FONTE_XBOLD, 46), y)
    y += 70
    centro("Paragominas e região – PA", _f(FONTE_XBOLD, 40), y, (210, 210, 210))
    im.convert("RGB").save(destino, quality=92)


def _estilo_ms():
    """30/10 (dona): mesmo visual dos carrosséis da Advance (título grosso em itálico, foto com cantos, pílula, botão)
    nas cores da MS Energy: preto + vermelho do logo. Devolve (capa, slide, cta) desse estilo."""
    import carrossel_advance as ca
    ca.usar_marca((34, 22, 26), (10, 10, 12), VERMELHO, "msenergycap", "Paragominas e região – PA",
                  lambda largura, cor=None: _logo_rgba(largura))
    return ca.capa, ca.slide, ca.cta


def gerar():
    """Gera um carrossel em videos\\carrosseis\\<data>; devolve a pasta ou None."""
    capa, slide, cta = _estilo_ms()  # noqa: F811  (estilo novo; as funções antigas ficam para quem importa)
    # 25/10: mesmas 5 pautas mais frias do rodízio, escolhidas pelo placar do carrossel (funil_insta, Thompson)
    pauta = roteiro_ms.escolher_pauta(formato="carrossel", hist=_hist())
    log(f"pauta: {pauta[0]}")
    t = gerar_textos(pauta)
    if not t:
        log("STOP: textos não passaram nas regras em 3 tentativas")
        return None
    pasta = DIR / datetime.now().strftime("%Y%m%d_%H%M")
    pasta.mkdir(parents=True, exist_ok=True)
    fotos_usadas = []
    foto_capa, nome = foto_real()
    if foto_capa is None:
        log("STOP: sem foto real para a capa")
        return None
    fotos_usadas.append(nome)
    capa(foto_capa, t["capa"], pasta / "slide_1.jpg")
    origens = []
    for i, (s, pr) in enumerate(zip(t["slides"], t["imagens"]), 2):
        img, origem = ilustracao(pr, pasta / f"ilustracao_{i}.png")
        if img is None:
            img, nome = foto_real(evitar=fotos_usadas)
            if img is None:
                img, nome = foto_capa, fotos_usadas[0]
            fotos_usadas.append(nome)
            origem = f"foto real {nome}"
        origens.append(origem)
        slide(img, i, 6, s["titulo"], s["texto"], pasta / f"slide_{i}.jpg")
    foto_cta, nome = foto_real(evitar=fotos_usadas)
    cta(foto_cta or foto_capa, pasta / "slide_6.jpg")
    insta, _, tags = roteiro_ms.legendas_finais(t["legenda"], pauta[0])
    meta = {"pauta": pauta[0], "capa": t["capa"], "slides": t["slides"], "imagens_prompt": t["imagens"],
            "origem_imagens": origens, "foto_capa": fotos_usadas[0], "titulo": t.get("titulo"),
            "legenda_insta": insta, "hashtags": tags, "gerado_em": datetime.now().isoformat(timespec="seconds")}
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    log(f"gerado: {pasta} | capa '{t['capa']}' | imagens: {origens}")
    return pasta


# ───────────────────────────── postagem ─────────────────────────────

def _graph(caminho, dados=None, **params):
    url = f"{GRAPH}/{caminho}"
    if dados is None:
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params))
    else:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(dados).encode(), method="POST")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=90).read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None


def _story_da_capa(ig, tok, pasta, upload):
    """25/10: o carrossel (o formato que mais rende: mediana 25 views x 5 dos Reels novos) não ia pro Story; os Reels
    já iam (postar_ms_energy). A capa vai pro Story logo depois de publicar — quem segue vê de novo. Falha aqui nunca
    derruba o carrossel (que já está publicado): devolve o motivo."""
    try:
        capa = str(Path(pasta) / "slide_1.jpg")
        try:  # 09/11: capa 4:5 -> 9:16 sem corte (mesma regra do postar.story das outras solares)
            import sys as _s
            _s.path.insert(0, r"D:\projeto-navegador-sem-navegador\services\instagram")
            import postar as _p
            classe = next(v for v in vars(_p).values() if isinstance(v, type) and hasattr(v, "_story_9x16"))
            capa = classe._story_9x16(capa)
        except Exception as e:  # noqa: BLE001
            log(f"story 9:16 não montou ({type(e).__name__}) — vai a capa original")
        url = upload(capa)
        if not url:
            return "upload falhou"
        cid = _graph(f"{ig}/media", {"media_type": "STORIES", "image_url": url, "access_token": tok})["id"]
        for _ in range(12):
            if _graph(cid, fields="status_code", access_token=tok).get("status_code") == "FINISHED":
                break
            time.sleep(5)
        sid = _graph(f"{ig}/media_publish", {"creation_id": cid, "access_token": tok})["id"]
        log(f"story da capa publicado: {sid}")
        return sid
    except Exception as e:  # noqa: BLE001
        log(f"story da capa falhou ({type(e).__name__}: {str(e)[:120]})")
        return f"falhou: {str(e)[:120]}"


def _textos_alternativos(meta):
    """Texto alternativo de cada slide (capa, 4 slides, CTA): o que está escrito + 'energia solar no Pará'. A busca do
    Instagram e quem usa leitor de tela leem isto; antes ia vazio."""
    fim = "Energia solar no Pará — MS Energy, Paragominas e região."
    alts = [f"{meta.get('capa', '').strip()} — {fim}"]
    for s in meta.get("slides") or []:
        alts.append(f"{s.get('titulo', '').strip()}: {s.get('texto', '').strip()} {fim}")
    alts.append("Orçamento grátis de energia solar para casa, comércio e propriedade rural com a MS Energy: chame no "
                "WhatsApp pelo link do perfil @msenergycap. Paragominas e região, Pará.")
    return alts


def postar(pasta):
    pasta = Path(pasta)
    meta = json.loads((pasta / "meta.json").read_text("utf-8"))
    if meta.get("postado"):
        log(f"já postado: {meta['postado'].get('permalink')}")
        return meta["postado"]
    tok = next(c for c in json.loads(CREDS.read_text("utf-8")) if "msenergycap" in c["name"].lower())["data"]["accessToken"]
    ig = _graph("me", fields="user_id", access_token=tok)["user_id"]
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    from postar_ms_energy import upload_video_publico  # litterbox -> uguu -> tmpfiles (serve pra imagem também)
    try:  # 25/10: carrossel gerado antes da legenda nova (frase morna + rodapé fixo) é refeito: pergunta + Comente SOL
        import legenda_empresa
        if legenda_empresa.relegendar(meta, "msenergycap"):
            log("legenda refeita no formato novo (pergunta + Comente SOL)")
    except Exception as e:  # noqa: BLE001
        log(f"legenda nova falhou ({type(e).__name__}: {e}) - fica a antiga")
    alts = _textos_alternativos(meta)
    filhos = []
    for i, img in enumerate(sorted(pasta.glob("slide_*.jpg"))):
        url = upload_video_publico(str(img))
        if not url:
            raise RuntimeError(f"upload público falhou: {img.name}")
        item = {"image_url": url, "is_carousel_item": "true", "access_token": tok}
        if i < len(alts) and alts[i]:
            item["alt_text"] = alts[i][:1000]  # 25/10: busca/acessibilidade lêem isto (testado: a API aceita)
        filhos.append(_graph(f"{ig}/media", item)["id"])
    car = _graph(f"{ig}/media", {"media_type": "CAROUSEL", "children": ",".join(filhos),
                                 "caption": meta["legenda_insta"], "access_token": tok})["id"]
    for _ in range(24):
        st = _graph(car, fields="status_code", access_token=tok).get("status_code")
        if st == "FINISHED":
            break
        if st == "ERROR":
            raise RuntimeError("Instagram recusou o carrossel (status ERROR)")
        time.sleep(5)
    for tent in range(6):  # 05/11 14:41: FINISHED e mesmo assim 2207027 "mídia não está pronta" -> carrossel do dia perdido
        try:
            mid = _graph(f"{ig}/media_publish", {"creation_id": car, "access_token": tok})["id"]
            break
        except RuntimeError as e:
            if "2207027" not in str(e) or tent == 5:
                raise
            time.sleep(20)
    link =_graph(mid, fields="permalink", access_token=tok).get("permalink")
    meta["postado"] = {"media_id": mid, "permalink": link, "em": datetime.now().isoformat(timespec="seconds")}
    meta["postado"]["story"] = _story_da_capa(ig, tok, pasta, upload_video_publico)
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    h = _hist()
    h.append({"data": meta["postado"]["em"], "pauta": meta["pauta"], "capa": meta["capa"], "pasta": str(pasta),
              "permalink": link})
    HIST.parent.mkdir(parents=True, exist_ok=True)
    HIST.write_text(json.dumps(h[-200:], ensure_ascii=False, indent=1), "utf-8")
    log(f"PUBLICADO: {link}")
    return meta["postado"]


def _pendente(dias=4):
    """Carrossel já produzido (--so-gerar) e ainda não postado, dos últimos dias: a tarefa posta ele em vez de gerar."""
    limite = time.time() - dias * 86400
    for p in sorted(DIR.glob("*/meta.json"), reverse=True):
        try:
            m = json.loads(p.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not m.get("postado") and p.stat().st_mtime > limite and len(list(p.parent.glob("slide_*.jpg"))) == 6:
            return p.parent
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-gerar", action="store_true")
    ap.add_argument("--postar")
    a = ap.parse_args()
    try:
        if a.postar:
            postar(a.postar)
            return
        pronto = None if a.so_gerar else _pendente()
        if pronto:
            log(f"carrossel já produzido e não postado: {pronto}")
        pasta = pronto or gerar()
        if pasta and not a.so_gerar:
            postar(pasta)
    except Exception as e:  # noqa: BLE001
        log(f"ERRO: {type(e).__name__}: {e}")
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar(f"MS Energy: carrossel do Instagram falhou ({type(e).__name__}: {str(e)[:150]})",
                          "msenergy-carrossel", importante=False)
        except Exception:  # noqa: BLE001
            pass
        raise


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
