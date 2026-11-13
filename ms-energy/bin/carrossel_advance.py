# -*- coding: utf-8 -*-
"""Carrossel da ADVANCE SOLAR (Castanhal-PA) no Instagram @advance_novoestrela (dona 29/10/2026: "começar hoje mesmo
as postagens de carrossel; pode usar as mesmas imagens da MS Energy, só elimine as de painel torto / instalação ruim;
fale que instalação não é tudo igual, o barato às vezes sai caro").

Mesmo formato do carrossel_ms (capa com foto real, 4 slides, CTA), marca própria (nada de MS Energy) e só fotos com
"instalacao.ok" = true (revisar_instalacao.py). Posta por HTTP com a sessão do cofre (conta pessoal, sem token da API):
D:\\projeto-navegador-sem-navegador services\\instagram\\postar.py. A capa vai também pro Story.
Rodar com D:\\veo\\venv\\Scripts\\python.exe (Flow + curl_cffi).
    python carrossel_advance.py              # posta o já gerado e não postado; senão gera e posta
    python carrossel_advance.py --so-gerar
    python carrossel_advance.py --postar <pasta>
"""
import argparse
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, r"D:\ms-energy\bin")
sys.path.insert(0, r"D:\veo\beta")
import carrossel_ms as cm  # noqa: E402
import roteiro_ms  # noqa: E402
from montagem_ms import FONTE_BLACK, FONTE_XBOLD, _f, _quebrar  # noqa: E402

CONTA = "advance_novoestrela"
MARCA = "Advance Energia Solar"
LOCAL = "Castanhal e região – PA"
# 29/10 (dona): seguir o estilo da MATRIZ @advanceengenhariasolar — roxo vivo + laranja, título grosso em itálico
ROXO = (91, 33, 234)
ROXO_ESC = (40, 10, 120)
LARANJA = (243, 102, 28)
COR = LARANJA
ESCURO = ROXO_ESC
W, H = cm.W, cm.H
DIR = Path(r"D:\ms-energy\videos\carrosseis_advance")
HIST = Path(r"D:\ms-energy\cache\historico_carrosseis_advance.json")
NSN = Path(r"D:\projeto-navegador-sem-navegador")
ILUSTRAR = False  # 29/10: ilustração de IA reprovada em todas as tentativas; empresa real usa foto real
ANTON = r"D:\ms-energy\assets\fontes\Anton-Regular.ttf"

EMPRESA = ("Advance Solar, empresa de energia solar de Castanhal, no Pará, Brasil. Projeto, instalação e manutenção de "
           "sistemas de energia solar para casas, comércios e propriedades rurais. Orçamento grátis pelo WhatsApp do "
           "perfil do Instagram @advance_novoestrela.")
# (id, cenário, assunto) — a 1ª é o pedido da dona 29/10
PAUTAS = [
    ("barato_caro", "telhado", "Instalação de energia solar não é tudo igual: o barato às vezes sai caro. Painel torto, "
                               "fiação mal feita e estrutura fraca dão prejuízo; muita gente chama a gente para refazer."),
    ("como_escolher", "casa", "Como escolher quem instala: projeto feito para a sua casa, material de qualidade, "
                              "instalação caprichada e alguém perto para a manutenção."),
    ("calor_ar", "casa", "No calor do Pará o ar-condicionado não para e a conta sobe; o mesmo sol forte gera energia."),
    ("chuva", "casa", "Chove muito no Pará: painel funciona em dia nublado? Gera menos, mas gera; o projeto considera o "
                      "ano todo."),
    ("noite", "casa", "E de noite? A energia que sobra durante o dia vira crédito na conta de luz e é usada depois."),
    ("manutencao", "telhado", "Manutenção é simples: limpeza de vez em quando e revisão para o sistema render sempre."),
    ("financiamento", "casa", "Dá para financiar o sistema; muita gente troca a conta de luz pela parcela."),
    ("rural", "campo", "Na roça e no sítio: bomba d'água, ordenha e freezer podem rodar com a energia do sol."),
    ("comercio", "comercio", "Comércio gasta energia de dia, justo quando o sol gera: freezer, ar e iluminação."),
    # 06/11 dona (referencias-instagram.zip, plano de posts M3/M5/M10/M11 dos perfis de solar que mais engajam):
    ("como_funciona", "telhado", "Como funciona em 5 passos: o sol bate na placa, a placa gera energia, o inversor "
                                 "deixa pronta pra casa, a casa usa na hora e o que sobra vira crédito na conta."),
    ("fio_b_2026", "casa", "Energia solar em 2026 ainda vale a pena? Existe o Fio B, uma taxa pelo uso da rede sobre a "
                           "energia que vai e volta, que sobe um pouco a cada ano; o que a casa usa na hora em que o "
                           "sol gera não paga. Cada casa precisa de simulação feita com a conta real."),
    ("tres_erros", "telhado", "3 erros ao contratar energia solar: não vistoriar o telhado antes, sistema mal "
                              "dimensionado para o consumo e não acompanhar a homologação com a Equatorial."),
    ("falta_luz", "casa", "Faltou luz, a casa continua ligada? Sistema sem bateria desliga quando a rede cai, por "
                          "segurança de quem trabalha na rede. Para ter luz na queda, só com bateria."),
    ("conta_zera", "casa", "A conta de luz zera? Não zera: continuam taxas como a iluminação pública e a parte do uso "
                           "da rede. O que cai é a energia que você pagava."),
    ("manda_telhado", "telhado", "Quer ver como fica a sua casa com energia solar? Manda a foto do seu telhado e da sua "
                                 "conta no WhatsApp que a gente faz a simulação."),
]
_OUTRA_MARCA = re.compile(r"ms ?energy|msenergy|paragominas|santa maria", re.I)


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def reel_ja_saiu(conta, legenda, minutos=15):
    """12/11: o HTTP dava "1357001/feedback_required" e MESMO ASSIM publicava — o fallback do navegador postava o mesmo
    vídeo de novo 5 min depois (e SEM legenda): Advance e Globo com 2 Reels por horário desde 06/11 (painel de
    clientes: xx:04 com legenda + xx:09 sem). Antes do navegador: lê os Reels do perfil (mesma sessão/IP da conta, só
    leitura) e, se saiu um Reel com esta legenda nos últimos `minutos`, devolve o código — não posta de novo.
    None = não saiu (ou não deu pra ler: aí segue o fallback, como antes)."""
    try:
        sys.path.insert(0, str(NSN))
        from services.instagram.web import InstagramWeb
        ig = InstagramWeb(conta)
        inicio = (legenda or "").strip()[:40]
        agora = time.time()
        # posts() = feed, que traz data e legenda (a aba de Reels vem sem taken_at nem caption — testado 12/11)
        for r in ig.posts(quantos=6):
            q = r.get("quando") or 0
            if (r.get("tipo") == "reel" and q and agora - float(q) <= minutos * 60 and inicio
                    and (r.get("legenda") or "").strip()[:40] == inicio):
                return r.get("codigo") or "ja_saiu"
    except Exception as e:  # noqa: BLE001 — conferir nunca derruba a postagem
        log(f"conferir se o Reel já saiu: não deu ({type(e).__name__}: {str(e)[:100]}) — segue o navegador")
    return None


def reel_pelo_navegador(conta, mp4, legenda):
    """06/11 (dona: "não é só aquele aviso de notificação?"): Advance e Globo davam 1357001 "Entre na sua conta" e a API
    feedback_required/spam pelo HTTP (curl_cffi), mas o MESMO login no Chrome do cofre posta normal (Globo 13:0x ok).
    Fallback: abre o Chrome do perfil ig_<conta> (oculto, mesmo IP) e posta como a dona postaria. Devolve True/False."""
    import subprocess
    sys.path.insert(0, r"D:\logins-google")
    import cofre
    porta, proc = cofre.abrir(f"ig_{conta}", "https://www.instagram.com/", visivel=False)
    try:
        r = subprocess.run([r"D:\veo\venv\Scripts\python.exe", "-X", "utf8", r"D:\postador-de-videos\bin\instagram_cdp_poster.py",
                            "--video", str(mp4), "--caption", legenda, "--port", str(porta)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600, creationflags=0x08000000)
        log("navegador: " + " | ".join(l.strip() for l in (r.stdout or "").splitlines()[-3:]))
        return r.returncode == 0 and "POSTADO" in (r.stdout or "")
    finally:
        if proc is not None:
            try:
                cofre.fechar(proc, None, f"ig_{conta}")
            except Exception:  # noqa: BLE001
                pass


def _hist():
    try:
        return json.loads(HIST.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return []


def _pauta():
    usadas = {h.get("pauta"): i for i, h in enumerate(_hist())}
    if "barato_caro" not in usadas:
        return PAUTAS[0]
    return random.choice(sorted(PAUTAS, key=lambda p: usadas.get(p[0], -1))[:4])


def fotos():
    """Só as fotos que a revisão de instalação APROVOU (sem torto, sem reparo, sem marca)."""
    return [n for n, it in roteiro_ms.fotos_boas() if (it.get("instalacao") or {}).get("ok") is True]


def foto(evitar=()):
    boas = [n for n in fotos() if n not in evitar]
    if not boas:
        return None, None
    n = random.choice(boas)
    return roteiro_ms._aparar_bordas(Image.open(roteiro_ms.FOTOS_DIR / n).convert("RGB")), n


# ───────────────────────────── marca ─────────────────────────────

LOGO_DIR = Path(r"D:\ms-energy\assets\advance")


def logo(largura, cor="branco"):
    r"""Logo NOVO da Advance Energia Solar (ícone hexagonal, tirado do Instagram da matriz em 29/10, fundo
    transparente): assets\advance\logo_branco.png / logo_laranja.png / logo_roxo.png."""
    lg = Image.open(LOGO_DIR / f"logo_{cor}.png").convert("RGBA")
    return lg.resize((largura, int(lg.height * largura / lg.width)), Image.LANCZOS)


def _logo_max(largura, alt_max):
    """Logo com largura E altura máximas (o da MS Energy é alto: em 30/10 cobriu o texto e empurrou o cartão)."""
    lg = logo(largura)
    bb = lg.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()  # tira a borda vazia do logo
    if bb:
        lg = lg.crop(bb)
        if lg.width < largura:
            lg = lg.resize((largura, int(lg.height * largura / lg.width)), Image.LANCZOS)
    if lg.height > alt_max:
        lg = lg.resize((int(lg.width * alt_max / lg.height), alt_max), Image.LANCZOS)
    return lg


def _fundo_roxo(alto=H):
    """Degradê roxo vivo -> roxo escuro (como os posts da matriz)."""
    g = Image.new("RGBA", (W, alto))
    d = ImageDraw.Draw(g)
    for y in range(alto):
        t = y / alto
        d.line([(0, y), (W, y)], fill=tuple(int(ROXO[i] * (1 - t) + ROXO_ESC[i] * t) for i in range(3)) + (255,))
    return g


def _titulo(im, linhas, x, y, tam, cores, inclina=0.18, sombra=True, espaco=1.05):
    """Título em Anton MAIÚSCULO e em itálico (cisalhado), uma cor por linha. Devolve o y do fim.
    espaco: altura da linha (x tam); com Ç/Á em linhas seguidas usar ~1.25 (a cedilha some sob o acento)."""
    from PIL import ImageFont
    f = ImageFont.truetype(ANTON, tam)
    alto = int(tam * espaco)
    camada = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    yy = y
    for i, ln in enumerate(linhas):
        if sombra:
            d.text((x + 6, yy + 6), ln.upper(), font=f, fill=(0, 0, 0, 110))
        d.text((x, yy), ln.upper(), font=f, fill=cores[i % len(cores)])
        yy += alto
    k = inclina
    camada = camada.transform(im.size, Image.AFFINE, (1, k, -k * yy, 0, 1, 0), Image.BICUBIC)
    im.alpha_composite(camada)
    return yy


def _caber_anton(texto, tam, largura, max_linhas):
    from PIL import ImageFont
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while True:
        f = ImageFont.truetype(ANTON, tam)
        linhas = _quebrar(d, texto.upper(), f, largura)
        larga = max(d.textlength(ln, font=f) for ln in linhas) > largura  # palavra sozinha maior que a largura
        if (len(linhas) <= max_linhas and not larga) or tam <= 50:
            return tam, linhas
        tam -= 4


def capa(img, texto, destino):
    im = ImageOps.fit(img, (W, H)).convert("RGBA")
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for y in range(int(H * 0.38), H):
        t = (y - H * 0.38) / (H * 0.62)
        gd.line([(0, y), (W, y)], fill=ROXO_ESC + (int(245 * min(1, t * 1.3)),))
    for y in range(0, 220):
        gd.line([(0, y), (W, y)], fill=ROXO_ESC + (int(170 * (1 - y / 220)),))
    im = Image.alpha_composite(im, g)
    im.alpha_composite(_logo_max(330, 150), (55, 50))
    tam, linhas = _caber_anton(texto, 150, W - 170, 4)
    y0 = H - 230 - len(linhas) * int(tam * 1.05)
    cores = ["white"] * (len(linhas) - 1) + [LARANJA]
    _titulo(im, linhas, 70, y0, tam, cores)
    d = ImageDraw.Draw(im)
    fa = _f(FONTE_BLACK, 38)
    t = "ARRASTE PARA O LADO  →"
    lw = d.textlength(t, font=fa)
    d.rounded_rectangle((60, H - 150, 60 + lw + 60, H - 80), radius=35, fill=LARANJA)
    d.text((90, H - 142), t, font=fa, fill="white")
    im.convert("RGB").save(destino, quality=92)


def slide(img, n, total, titulo, texto, destino):
    im = _fundo_roxo()
    alto_img = 640
    foto_r = ImageOps.fit(img, (W - 100, alto_img)).convert("RGBA")
    mascara = Image.new("L", foto_r.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, *foto_r.size), radius=40, fill=255)
    im.paste(foto_r, (50, 50), mascara)
    d = ImageDraw.Draw(im)
    pil = f"{n}/{total}"
    fp = _f(FONTE_BLACK, 40)
    lw = d.textlength(pil, font=fp)
    d.rounded_rectangle((W - lw - 120, 80, W - 80, 150), radius=35, fill=LARANJA)
    d.text((W - lw - 100, 90), pil, font=fp, fill="white")
    tam, lt = _caber_anton(titulo, 96, W - 170, 2)
    y = _titulo(im, lt, 70, alto_img + 90, tam, ["white", LARANJA], sombra=False)
    d = ImageDraw.Draw(im)
    y += 20
    fx, lx = cm._caber(d, texto, FONTE_XBOLD, 46, W - 140, 4, minimo=32)  # 4 linhas: não chega no logo
    for ln in lx:
        d.text((70, y), ln, font=fx, fill=(240, 236, 255))
        y += int(fx.size * 1.3)
    lg = _logo_max(250, 75)
    im.alpha_composite(lg, (60, H - lg.height - 45))
    fa = _f(FONTE_XBOLD, 32)
    d.text((W - 60 - d.textlength("@" + CONTA, font=fa), H - 85), "@" + CONTA, font=fa, fill=(220, 210, 255))
    im.convert("RGB").save(destino, quality=92)


def cta(img, destino):
    fundo = ImageOps.fit(img, (W, H)).filter(ImageFilter.GaussianBlur(5)).convert("RGBA")
    roxo = _fundo_roxo()
    roxo.putalpha(225)
    im = Image.alpha_composite(fundo, roxo)
    lg = _logo_max(620, 230)
    im.alpha_composite(lg, ((W - lg.width) // 2, 150))
    y = _titulo(im, ["Orçamento", "grátis"], 120, 150 + lg.height + 60, 150, ["white", LARANJA], espaco=1.3)
    d = ImageDraw.Draw(im)

    def centro(t, f, y, cor="white"):
        d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=cor)

    y += 30
    for ln in _quebrar(d, "Instalação caprichada para casa, comércio e campo", _f(FONTE_XBOLD, 48), W - 160):
        centro(ln, _f(FONTE_XBOLD, 48), y)
        y += 62
    y += 50
    fb = _f(FONTE_BLACK, 60)
    t = "CHAME NO WHATSAPP"
    lw = d.textlength(t, font=fb)
    d.rounded_rectangle(((W - lw) / 2 - 60, y - 26, (W + lw) / 2 + 60, y + 96), radius=60, fill=LARANJA)
    centro(t, fb, y, "white")
    y += 170
    centro("@" + CONTA, _f(FONTE_XBOLD, 46), y)
    y += 66
    centro(LOCAL, _f(FONTE_XBOLD, 40), y, (225, 215, 255))
    im.convert("RGB").save(destino, quality=92)


def usar_marca(cor_fundo, cor_fundo_esc, destaque, conta, local, logo_fn):
    """30/10 (dona: "usar tudo que aprendemos no da MS aqui e vice-versa; padronizar as cores lá também, só que lá é
    vermelho e preto"): o MESMO visual (título Anton itálico, foto com cantos, pílula, botão) com as cores/logo de
    outra marca. Troca as globais deste módulo (capa/slide/cta leem na hora). Ex.: carrossel_ms._estilo_ms()."""
    global ROXO, ROXO_ESC, LARANJA, COR, ESCURO, CONTA, LOCAL, logo
    ROXO, ROXO_ESC, LARANJA, COR, ESCURO = cor_fundo, cor_fundo_esc, destaque, destaque, cor_fundo_esc
    CONTA, LOCAL = conta, local
    logo = logo_fn


# ───────────────────────────── geração ─────────────────────────────

def textos(pauta):
    roteiro_ms.EMPRESA = EMPRESA  # o pedido do carrossel_ms lê daqui
    capas = [h.get("capa", "") for h in _hist()]
    correcao = ""
    for tentativa in range(4):
        try:
            t = cm._pedir_textos(pauta, capas, correcao)
        except Exception as e:  # noqa: BLE001
            log(f"LLM falhou ({type(e).__name__}: {str(e)[:80]})")
            continue
        erros = cm._validar(t)
        tudo = json.dumps(t, ensure_ascii=False)
        if _OUTRA_MARCA.search(tudo):
            erros.append("cite só a Advance Solar de Castanhal (tire MS Energy/Paragominas)")
        if not erros:
            ok, problema = roteiro_ms._revisar(" ".join(s["texto"] for s in t["slides"]), pauta[2], tipo="carrossel")
            if not ok:
                erros = [f"revisor: {problema[:150]}"]
        if not erros:
            return t
        log(f"textos reprovados ({tentativa + 1}): {'; '.join(erros)[:200]}")
        correcao = "CORRIJA a resposta anterior: " + "; ".join(erros)
    return None


def legenda(t, pauta_id):
    tags = ["#energiasolar", "#castanhal", "#castanhalpa", "#energiasolarpara", "#painelsolar"]
    if pauta_id == "rural":
        tags.append("#agro")
    return (f"{t['legenda'].strip()}\n\n"
            "☀️ Quer saber quanto dá para economizar? Comente SOL ou chame no WhatsApp do perfil: o orçamento é grátis.\n"
            f"📍 {LOCAL}\n\n" + " ".join(tags))


def gerar():
    pauta = _pauta()
    log(f"pauta: {pauta[0]} | fotos aprovadas: {len(fotos())}")
    if len(fotos()) < 3:
        log("STOP: menos de 3 fotos aprovadas na revisão de instalação")
        return None
    t = textos(pauta)
    if not t:
        log("STOP: textos não passaram nas regras")
        return None
    pasta = DIR / datetime.now().strftime("%Y%m%d_%H%M")
    pasta.mkdir(parents=True, exist_ok=True)
    usadas = []
    fc, n = foto()
    usadas.append(n)
    capa(fc, t["capa"], pasta / "slide_1.jpg")
    origens = []
    for i, (s, pr) in enumerate(zip(t["slides"], t["imagens"]), 2):
        img, origem = (None, "foto real") if not ILUSTRAR else cm.ilustracao(pr, pasta / f"ilustracao_{i}.png")
        if img is None:
            img, n = foto(evitar=usadas)
            img, n = (img, n) if img is not None else (fc, usadas[0])
            usadas.append(n)
            origem = f"foto real {n}"
        origens.append(origem)
        slide(img, i, 6, s["titulo"], s["texto"], pasta / f"slide_{i}.jpg")
    fcta, n = foto(evitar=usadas)
    cta(fcta or fc, pasta / "slide_6.jpg")
    meta = {"conta": CONTA, "pauta": pauta[0], "capa": t["capa"], "slides": t["slides"], "origem_imagens": origens,
            "fotos": usadas, "legenda_insta": legenda(t, pauta[0]), "gerado_em": datetime.now().isoformat(timespec="seconds")}
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    log(f"gerado: {pasta} | capa '{t['capa']}' | {origens}")
    return pasta


def postar(pasta):
    pasta = Path(pasta)
    meta = json.loads((pasta / "meta.json").read_text("utf-8"))
    if meta.get("postado"):
        log(f"já postado: {meta['postado'].get('permalink')}")
        return meta["postado"]
    sys.path.insert(0, str(NSN))
    from services.instagram.postar import InstagramPostar
    ig = InstagramPostar(CONTA)
    imgs = [str(p) for p in sorted(pasta.glob("slide_*.jpg"))]
    pelo_nav = False
    try:
        code = ig.carrossel(imgs, meta["legenda_insta"])
    except Exception as e:  # noqa: BLE001  06/11: HTTP limitado (spam/1357001) -> pelo Chrome do cofre, como o reel
        if not any(s in str(e).lower() for s in ("1357001", "entre para continuar", "feedback_required", "spam")):
            raise
        log("HTTP limitado pelo Instagram — carrossel pelo navegador do cofre")
        if not reel_pelo_navegador(CONTA, "|".join(imgs), meta["legenda_insta"]):
            raise
        code, pelo_nav = None, True
    link = f"https://www.instagram.com/p/{code}/" if code else f"https://www.instagram.com/{CONTA}/"
    meta["postado"] = {"permalink": link, "em": datetime.now().isoformat(timespec="seconds")}
    try:
        if pelo_nav:
            raise RuntimeError("story pulado: conta limitada no HTTP")
        time.sleep(20)
        meta["postado"]["story"] = ig.story(imgs[0])
    except Exception as e:  # noqa: BLE001  (story nunca derruba o carrossel já publicado)
        meta["postado"]["story"] = f"falhou: {str(e)[:120]}"
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    h = _hist()
    h.append({"data": meta["postado"]["em"], "pauta": meta["pauta"], "capa": meta["capa"], "pasta": str(pasta),
              "permalink": link})
    HIST.parent.mkdir(parents=True, exist_ok=True)
    HIST.write_text(json.dumps(h[-200:], ensure_ascii=False, indent=1), "utf-8")
    log(f"PUBLICADO: {link} | story: {meta['postado']['story']}")
    return meta["postado"]


REELS = Path(r"D:\ms-energy\videos\reels_advance")
INTERVALO_MIN = 90  # 30/10: 9 carrosséis de hora em hora (03h-11h) + Reels = rajada -> feedback_required


def ultimo_post():
    """Data do último post da conta (carrossel ou Reel), ou None."""
    datas = [h.get("data", "") for h in _hist()]
    for j in REELS.glob("*.json"):
        try:
            datas.append((json.loads(j.read_text("utf-8")).get("postado") or {}).get("em", ""))
        except Exception:  # noqa: BLE001
            pass
    datas = [d for d in datas if d]
    return datetime.fromisoformat(max(datas)) if datas else None


PAUSA = Path(r"D:\ms-energy\cache\advance_pausa.json")
LIMITE = ("feedback_required", "spam", "tente novamente", "checkpoint",
          "1357001", "entre para continuar")  # 06/11: o reel devolve "Entre na sua conta" quando a conta está limitada (spam)


def pausar(motivo, horas=6, log=log):  # 06/11: 18 h deixava cliente 1 dia sem post; 6 h e tenta de novo
    """30/10: o Instagram limitou a conta (feedback_required/spam). Insistir piora: nada posta até 'ate'."""
    from datetime import timedelta
    ate = datetime.now() + timedelta(hours=horas)
    PAUSA.parent.mkdir(parents=True, exist_ok=True)
    PAUSA.write_text(json.dumps({"ate": ate.isoformat(timespec="seconds"), "motivo": motivo[:300]},
                                ensure_ascii=False), "utf-8")
    log(f"Instagram limitou a conta: posts PAUSADOS até {ate:%d/%m %H:%M} ({PAUSA.stem})")


def espaco_ok(log=log):
    """Nunca postar em rajada nem com a conta limitada: no mínimo INTERVALO_MIN minutos depois do último post."""
    try:
        p = json.loads(PAUSA.read_text("utf-8"))
        if datetime.now() < datetime.fromisoformat(p["ate"]):
            log(f"pausado até {p['ate'][:16]} (Instagram limitou a conta: {p['motivo'][:80]})")
            return False
    except Exception:  # noqa: BLE001  (sem pausa)
        pass
    u = ultimo_post()
    if u and (datetime.now() - u).total_seconds() < INTERVALO_MIN * 60:
        log(f"espero: último post da conta foi às {u:%H:%M} (mínimo {INTERVALO_MIN} min entre posts)")
        return False
    return True


def limitada():
    """O Instagram limitou a conta (pausa ativa)? Aí nada insiste."""
    try:
        return datetime.now() < datetime.fromisoformat(json.loads(PAUSA.read_text("utf-8"))["ate"])
    except Exception:  # noqa: BLE001
        return False


def insistir(pegar, publicar, ate_min=210, log=None):
    """01/11 (dona: "as postagens das empresas solares não podem deixar de sair; deu erro, tenta até conseguir, com os
    devidos intervalos"): sem vídeo/erro = nova tentativa a cada 10 min; intervalo de INTERVALO_MIN ainda correndo =
    espera. Para só com o Instagram limitando a conta ou perto do próximo horário (ate_min), que assume dali."""
    log = log or globals()["log"]
    fim = time.time() + ate_min * 60
    while True:
        try:
            if limitada():
                espaco_ok(log)  # registra o motivo
                return False
            item = pegar()
            if item:
                while not espaco_ok(log):
                    if limitada() or time.time() + 300 > fim:
                        return False
                    time.sleep(300)
                publicar(item)
                return True
            log("nada pronto para postar — tento de novo em 10 min")
        except Exception as e:  # noqa: BLE001
            log(f"ERRO: {type(e).__name__}: {str(e)[:200]} — tento de novo em 10 min")
            if any(s in str(e).lower() for s in LIMITE):
                pausar(str(e), log=log)
                return False
        if time.time() + 600 > fim:
            log("perto do próximo horário: ele assume daqui")
            return False
        time.sleep(600)


def _pendente(dias=3):
    limite = time.time() - dias * 86400
    for p in sorted(DIR.glob("*/meta.json"), reverse=True):
        m = json.loads(p.read_text("utf-8"))
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
        if a.so_gerar:
            gerar()
            return
        insistir(lambda: _pendente() or gerar(), postar)
    except Exception as e:  # noqa: BLE001
        log(f"ERRO: {type(e).__name__}: {e}")
        if any(s in str(e).lower() for s in LIMITE):
            pausar(str(e))
            # 30/10: o Instagram limitou a conta -> desliga a rodada de hora em hora (a diária segue amanhã)
            import subprocess
            subprocess.run(["schtasks", "/Change", "/TN", "AdvanceSolar_Carrossel_Hora", "/Disable"],
                           capture_output=True, creationflags=0x08000000)
            log("Instagram limitou a conta: tarefa de hora em hora DESLIGADA")
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar(f"Advance Solar: carrossel falhou ({type(e).__name__}: {str(e)[:150]})",
                          "advance-carrossel", importante=False)
        except Exception:  # noqa: BLE001
            pass
        raise


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
