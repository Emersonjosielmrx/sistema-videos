#!/usr/bin/env python3
"""carrossel_marca.py — Carrossel de Instagram com a COR de cada conta (dono 24/10: "padronização para cada Instagram
de cores nas postagens de carrossel e imagem até nos vídeos, cada um com sua cor"; "os carrosséis deram muitas views").

Mesmo desenho do D:\\ms-energy\\bin\\carrossel_ms.py (capa + 4 slides + chamada final), com as cores, o nome e o
assunto de config\\marcas_instagram.json. Conta de produto (Hermes Call, Cardápio Digital, Agenda IA) ensina sobre o
problema que o produto resolve; conta de tema faz um carrossel educativo do tema.
- Imagens: Nano Banana 2.1 pelo Google Flow (D:\\flow-imagens, 0 crédito), conferidas por visão; sem imagem boa = fundo
  liso na cor da marca (nunca imagem com texto/pessoa deformada).
- Postagem: conta com token -> carrossel de verdade (Graph API); conta pelo navegador -> o carrossel vira Reel de
  slides (3 s cada) pelo mesmo caminho do postar_insta_auto (o navegador só posta Reel).

    python carrossel_marca.py --conta inovarecom.ia [--so-gerar] [--postar <pasta>]
    python carrossel_marca.py --todas          # 1 por conta (tarefa diária)
"""
import argparse
import io
import json
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, r"D:\veo\beta")
sys.path.insert(0, r"D:\ms-energy\bin")
import pastas_empresas as pe  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DIR = Path(r"D:\video-fila\carrosseis_marcas")
HIST = RAIZ / "config" / "carrossel_marca_historico.json"
CREDS = Path(r"D:\credenciais-canais\instagram_contas.json")
PRODUTOS = Path(r"D:\veo\beta\pos_producao\assets\produtos.json")
GRAPH = "https://graph.instagram.com/v21.0"
FONTE_BLACK = r"D:\hipercool-materiais\assets\fonts\Montserrat-Black.ttf"
FONTE_XBOLD = r"D:\hipercool-materiais\assets\fonts\Montserrat-ExtraBold.ttf"
W, H = 1080, 1350
LOG = Path(r"D:\postador-de-videos\logs\carrossel_marca.log")


def log(msg):
    linha = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(linha, flush=True)
    try:  # 25/10 07:13: a tarefa redirecionava para este mesmo arquivo -> PermissionError derrubou a rodada inteira
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def _f(fonte, tam):
    return ImageFont.truetype(fonte, tam)


def _quebrar(d, texto, f, largura):
    linhas, atual = [], ""
    for p in texto.split():
        t = (atual + " " + p).strip()
        if d.textlength(t, font=f) <= largura:
            atual = t
        else:
            if atual:
                linhas.append(atual)
            atual = p
    return linhas + ([atual] if atual else [])


def _caber(d, texto, fonte, tam, largura, max_linhas, minimo=26):
    while True:
        f = _f(fonte, tam)
        linhas = _quebrar(d, texto, f, largura)
        if len(linhas) <= max_linhas or tam <= minimo:
            return f, linhas
        tam -= 2


def _hist():
    return pe._ler(HIST, [])


def _produto(m):
    if not m.get("produto"):
        return None
    return next((p for p in pe._ler(PRODUTOS, {}).get("produtos", []) if p.get("id") == m["produto"]), None)


# ───────────────────────────── texto ─────────────────────────────

def _assunto(m):
    p = _produto(m)
    if p:
        return (f"produto {p['nome']}: {p.get('descricao', '')}. {p.get('cta_longo', '')} Para quem: "
                f"{', '.join(p.get('tema_alvo', []))}. O carrossel ensina sobre o PROBLEMA que o produto resolve e "
                f"mostra como ele ajuda, sem exagero.")
    return f"tema da página: {m.get('tema', m['marca'])}. Carrossel educativo e curioso sobre o tema."


def gerar_textos(conta, m, log=log):
    from llm_client import _call_gemini_native
    capas = [h.get("capa", "") for h in _hist() if h.get("conta") == conta][-20:]
    system = ("Você escreve carrosséis de Instagram que geram muitas visualizações e salvamentos: capa forte, slides "
              "curtos e úteis. Português do Brasil com acentuação correta. Responda SÓ JSON válido.")
    correcao = ""
    for tentativa in range(3):
        user = f"""Página: {m['marca']} (@{conta})
Assunto: {_assunto(m)}
Regras obrigatórias:
- NÃO inventar números, porcentagens, preços, prazos, estatísticas ou nomes de empresas/pessoas reais.
- NÃO prometer resultado garantido. Nada de "segredo que ninguém te conta". Nada de política ou religião.
- "capa": pergunta ou frase forte de 3 a 8 palavras.
- "slides": exatamente 4 itens com "titulo" (2 a 6 palavras) e "texto" (12 a 28 palavras, uma ideia só).
- "imagens": exatamente 4 descrições em INGLÊS de uma imagem ilustrativa para cada slide (sem texto, sem letras,
  sem logotipos, sem rostos em close).
- "imagem_capa": 1 descrição em INGLÊS para a capa (mesmas regras).
- "legenda": 2 ou 3 linhas curtas, sem hashtags.
Capas já usadas nesta página (não repita): {capas}
{correcao}
Responda SÓ: {{"capa": "...", "slides": [{{"titulo": "...", "texto": "..."}}], "imagens": ["..."], "imagem_capa": "...", "legenda": "..."}}"""
        try:
            t = json.loads(re.search(r"\{.*\}", _call_gemini_native(system, user, max_tokens=1600, temperatura=0.8),
                                     re.S).group(0))
        except Exception as e:  # noqa: BLE001
            log(f"  LLM falhou ({type(e).__name__}: {str(e)[:80]})")
            continue
        erros = []
        if len(t.get("slides") or []) != 4 or len(t.get("imagens") or []) != 4:
            erros.append("precisa de exatamente 4 slides e 4 imagens")
        else:
            if not 2 <= len((t.get("capa") or "").split()) <= 9:
                erros.append("capa com 3 a 8 palavras")
            for i, s in enumerate(t["slides"], 1):
                if not 8 <= len((s.get("texto") or "").split()) <= 32:
                    erros.append(f"slide {i}: texto com 12 a 28 palavras")
            if re.search(r"\d", " ".join([t.get("capa", "")] + [s["titulo"] + " " + s["texto"] for s in t["slides"]])):
                erros.append("tem número (proibido)")
        if not erros:
            return t
        log(f"  textos reprovados ({tentativa + 1}): {'; '.join(erros)}")
        correcao = "CORRIJA a resposta anterior: " + "; ".join(erros)
    return None


# ───────────────────────────── imagens ─────────────────────────────

_PERG = ('Responda SO JSON: {"texto_ou_letras": true se aparece qualquer letra, numero, palavra ou logotipo, '
         '"deformado": true se ha pessoa, mao ou objeto torto/derretido/impossivel, "improprio": true se ha nudez, '
         'violencia ou algo ofensivo, "nota": 1 a 10 (bonita e profissional?)}')


def ilustracao(prompt_en, destino, formato):
    import qa_ms
    sys.path.insert(0, r"D:\flow-imagens")
    from gera_imagem import gerar_imagem
    pr = prompt_en.strip().rstrip(".") + ". High quality, natural light. No text, no letters, no logos, no watermark."
    for _ in range(2):
        try:
            im = Image.open(gerar_imagem(pr, destino, formato=formato, log=lambda x: None)[0]).convert("RGB")
        except Exception as e:  # noqa: BLE001
            log(f"  Flow falhou: {str(e)[:120]}")
            return None
        buf = io.BytesIO()
        im.copy().resize((im.width // 2, im.height // 2)).save(buf, "JPEG", quality=85)
        v = qa_ms.visao_json(buf.getvalue(), _PERG)
        if "_erro" in v:
            return None
        if not (v.get("texto_ou_letras") or v.get("deformado") or v.get("improprio")) and int(v.get("nota") or 0) >= 6:
            return im
        log(f"  ilustração reprovada: {v}")
    return None


def _liso(m):
    """Sem imagem boa: fundo na cor de apoio com um degradê da cor da marca."""
    apoio, cor = pe._rgb(m.get("apoio", "#111111")), pe._rgb(m["cor"])
    im = Image.new("RGB", (W, H), apoio)
    g = ImageDraw.Draw(im)
    for y in range(H):
        a = y / H * 0.45
        g.line([(0, y), (W, y)], fill=tuple(int(apoio[i] * (1 - a) + cor[i] * a) for i in range(3)))
    return im


# ───────────────────────────── desenho ─────────────────────────────

def _degrade(im, de_y, ate_y, alfa_max, cor, de_baixo=True):
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for y in range(de_y, ate_y):
        f = (y - de_y) / max(ate_y - de_y, 1)
        gd.line([(0, y), (im.width, y)], fill=cor + (int(alfa_max * (f if de_baixo else 1 - f)),))
    return Image.alpha_composite(im, g)


def _selo(d, m, x, y, tam=40):
    """Nome da marca numa pílula da cor da marca (no lugar do logo)."""
    f = _f(FONTE_BLACK, tam)
    lw = d.textlength(m["marca"], font=f)
    d.rounded_rectangle((x, y, x + lw + 60, y + tam + 34), radius=(tam + 34) // 2, fill=pe._rgb(m["cor"]))
    d.text((x + 30, y + 14), m["marca"], font=f, fill=pe._rgb(m.get("texto", "#FFFFFF")))


def capa(img, texto, m, destino):
    apoio, cor = pe._rgb(m.get("apoio", "#111111")), pe._rgb(m["cor"])
    im = ImageOps.fit(img, (W, H)).convert("RGBA")
    im = _degrade(im, int(H * 0.35), H, 235, apoio)
    im = _degrade(im, 0, 220, 150, apoio, de_baixo=False)
    d = ImageDraw.Draw(im)
    _selo(d, m, 50, 40)
    f, linhas = _caber(d, texto, FONTE_BLACK, 100, W - 120, 4)
    y = H - 210 - len(linhas) * int(f.size * 1.15)
    d.rectangle((60, y - 34, 220, y - 22), fill=cor)
    for ln in linhas:
        d.text((60, y), ln, font=f, fill="white")
        y += int(f.size * 1.15)
    d.text((60, H - 120), "Arraste para o lado  →", font=_f(FONTE_XBOLD, 36), fill=(225, 225, 225))
    im.convert("RGB").save(destino, quality=92)


def slide(img, n, total, titulo, texto, m, conta, destino):
    apoio, cor = pe._rgb(m.get("apoio", "#111111")), pe._rgb(m["cor"])
    escuro = tuple(int(c * 0.35) for c in apoio)
    im = Image.new("RGBA", (W, H), escuro + (255,))
    alto = 680
    im.paste(ImageOps.fit(img, (W, alto)).convert("RGBA"), (0, 0))
    im = _degrade(im, alto - 220, alto, 255, escuro)
    d = ImageDraw.Draw(im)
    fp = _f(FONTE_BLACK, 40)
    pil = f"{n}/{total}"
    lw = d.textlength(pil, font=fp)
    d.rounded_rectangle((W - lw - 110, 40, W - 40, 110), radius=35, fill=cor)
    d.text((W - lw - 75, 50), pil, font=fp, fill=pe._rgb(m.get("texto", "#FFFFFF")))
    y = alto - 30
    ft, lt = _caber(d, titulo, FONTE_BLACK, 70, W - 160, 2)
    d.rectangle((60, y + 8, 72, y + 8 + len(lt) * int(ft.size * 1.12) - 14), fill=cor)
    for ln in lt:
        d.text((95, y), ln, font=ft, fill="white")
        y += int(ft.size * 1.12)
    y += 24
    fx, lx = _caber(d, texto, FONTE_XBOLD, 46, W - 150, 5, minimo=34)
    for ln in lx:
        d.text((95, y), ln, font=fx, fill=(232, 232, 232))
        y += int(fx.size * 1.3)
    _selo(d, m, 60, H - 110, 30)
    fa = _f(FONTE_XBOLD, 32)
    d.text((W - 60 - d.textlength("@" + conta, font=fa), H - 85), "@" + conta, font=fa, fill=(200, 200, 200))
    im.convert("RGB").save(destino, quality=92)


def final(img, m, conta, destino):
    apoio, cor = pe._rgb(m.get("apoio", "#111111")), pe._rgb(m["cor"])
    escuro = tuple(int(c * 0.35) for c in apoio)  # 24/10: apoio claro (amarelo do Cardápio) apagava o texto branco
    im = Image.blend(ImageOps.fit(img, (W, H)).filter(ImageFilter.GaussianBlur(4)), Image.new("RGB", (W, H), escuro),
                     0.8).convert("RGBA")
    d = ImageDraw.Draw(im)

    def centro(t, f, y, c="white"):
        d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=c)

    p = _produto(m)
    y = 300
    fm, lm = _caber(d, m["marca"], FONTE_BLACK, 110, W - 100, 2)
    for ln in lm:
        centro(ln, fm, y, cor)
        y += int(fm.size * 1.15)
    y += 40
    sub = (p or {}).get("cta_curto") or f"Siga para mais sobre {m.get('tema', 'o tema')}"
    for ln in _quebrar(d, sub, _f(FONTE_XBOLD, 52), W - 140):
        centro(ln, _f(FONTE_XBOLD, 52), y)
        y += 68
    y += 60
    fb = _f(FONTE_BLACK, 60)
    t = "Chame no direct" if p else "Salve e compartilhe"
    lw = d.textlength(t, font=fb)
    d.rounded_rectangle(((W - lw) / 2 - 60, y - 24, (W + lw) / 2 + 60, y + 96), radius=60, fill=cor)
    centro(t, fb, y, pe._rgb(m.get("texto", "#FFFFFF")))
    y += 180
    centro("@" + conta, _f(FONTE_XBOLD, 46), y, (225, 225, 225))
    im.convert("RGB").save(destino, quality=92)


def gerar(conta):
    m = pe.marcas()[conta]
    # 25/10 (dono: conteúdo PROFISSIONAL de produto): conta de produto com carrossel pronto do roteiro do vídeo
    # (bin/produto/carrossel.py) posta esse primeiro — mesma mensagem do Reel, imagens já aprovadas
    if m.get("produto"):
        try:
            from produto import carrossel as carrossel_produto
            pronto = carrossel_produto.pendente(conta)
            if pronto:
                log(f"[{conta}] carrossel de produto pronto (do roteiro do vídeo): {pronto}")
                return pronto
        except Exception as e:  # noqa: BLE001
            log(f"[{conta}] carrossel de produto: {type(e).__name__}: {str(e)[:120]}")
    log(f"[{conta}] gerando carrossel ({m['marca']})")
    t = gerar_textos(conta, m)
    if not t:
        log(f"[{conta}] STOP: textos não passaram nas regras")
        return None
    pasta = DIR / conta / datetime.now().strftime("%Y%m%d_%H%M")
    pasta.mkdir(parents=True, exist_ok=True)
    img_capa = ilustracao(t.get("imagem_capa") or t["imagens"][0], pasta / "ilustracao_1.png", "3:4") or _liso(m)
    capa(img_capa, t["capa"], m, pasta / "slide_1.jpg")
    for i, (s, pr) in enumerate(zip(t["slides"], t["imagens"]), 2):
        img = ilustracao(pr, pasta / f"ilustracao_{i}.png", "16:9") or _liso(m)
        slide(img, i, 6, s["titulo"], s["texto"], m, conta, pasta / f"slide_{i}.jpg")
    final(img_capa, m, conta, pasta / "slide_6.jpg")
    meta = {"conta": conta, "marca": m["marca"], "capa": t["capa"], "slides": t["slides"], "legenda": t["legenda"],
            "gerado_em": datetime.now().isoformat(timespec="seconds")}
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    log(f"[{conta}] gerado: {pasta} | capa '{t['capa']}'")
    return pasta


# ───────────────────────────── postagem ─────────────────────────────

def _graph(caminho, dados=None, **params):
    url = f"{GRAPH}/{caminho}"
    req = (urllib.request.Request(url + "?" + urllib.parse.urlencode(params)) if dados is None else
           urllib.request.Request(url, data=urllib.parse.urlencode(dados).encode(), method="POST"))
    try:
        return json.loads(urllib.request.urlopen(req, timeout=90).read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None


def _token(conta):
    for c in pe._ler(CREDS, []):
        if c.get("name", "").lower().replace("instagram", "").strip() == conta:
            return (c.get("data") or {}).get("accessToken")
    return None


def _como_reel(pasta):
    """6 slides (3 s cada, zoom leve) + trilha -> mp4 1080x1920 com o slide 4:5 sobre fundo desfocado."""
    m = pe.marcas()[json.loads((pasta / "meta.json").read_text("utf-8"))["conta"]]
    saida = pasta / "carrossel_reel.mp4"
    slides = sorted(pasta.glob("slide_*.jpg"))
    quadros = []
    for i, s in enumerate(slides):
        im = Image.open(s).convert("RGB")
        tela = Image.blend(ImageOps.fit(im, (pe.W, pe.H)).filter(ImageFilter.GaussianBlur(40)),
                           Image.new("RGB", (pe.W, pe.H), pe._rgb(m.get("apoio", "#111111"))), 0.6)
        tela.paste(im, (0, (pe.H - im.height) // 2))
        q = pasta / f"_q{i}.png"
        tela.save(q)
        quadros.append(q)
    ent, partes = [], []
    for i, q in enumerate(quadros):
        ent += ["-loop", "1", "-t", "3", "-i", str(q)]
        partes.append(f"[{i}:v]scale={pe.W}:{pe.H},setsar=1[f{i}]")
    n = len(quadros)
    ent += ["-stream_loop", "-1", "-i", random.choice([t for t in pe.TRILHAS if Path(t).exists()])]
    filtro = ";".join(partes) + ";" + "".join(f"[f{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v];" \
        f"[{n}:a]volume=0.4,afade=t=out:st={n * 3 - 1}:d=1[a]"
    subprocess.run([pe.FFMPEG, "-y", "-v", "error", *ent, "-filter_complex", filtro, "-map", "[v]", "-map", "[a]",
                    "-t", str(n * 3), "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", str(saida)], check=True, timeout=600)
    for q in quadros:
        q.unlink(missing_ok=True)
    return saida


def _legenda_final(conta, meta):
    """25/10 (config\\empresas_instagram.json): conta de empresa/produto cadastrada ganha 1a linha (a capa), pergunta,
    contato e 5 hashtags; antes ia só o texto do LLM (2–3 linhas, sem hashtag nem pergunta). Conta de tema (humor,
    finanças...) sem cadastro: fica como era."""
    try:
        import legenda_empresa
        if legenda_empresa.carregar(conta):
            return legenda_empresa.montar(conta, meta["legenda"], primeira_linha=meta.get("capa"))[0]
    except Exception as e:  # noqa: BLE001
        log(f"[{conta}] legenda nova falhou ({type(e).__name__}: {e}) - vai a do LLM")
    return meta["legenda"]


def _textos_alternativos(meta):
    """O que está escrito em cada slide (capa, slides, final) — busca do Instagram e leitor de tela leem isto."""
    marca = meta.get("marca", "")
    alts = [f"{meta.get('capa', '').strip()} — {marca}"]
    for s in meta.get("slides") or []:
        alts.append(f"{s.get('titulo', '').strip()}: {s.get('texto', '').strip()} — {marca}")
    alts.append(f"{marca}: saiba mais pelo link do perfil.")
    return alts


def postar(pasta):
    pasta = Path(pasta)
    meta = json.loads((pasta / "meta.json").read_text("utf-8"))
    if meta.get("postado"):
        return meta["postado"]
    conta = meta["conta"]
    tok = _token(conta)
    cfg = (pe._ler(RAIZ / "config" / "reuso_plataformas.json", {}).get("instagram") or {}).get("contas", {})
    r = cfg.get(conta) or {}
    legenda = _legenda_final(conta, meta)
    if tok and not (r.get("cofre") or r.get("maquina")):
        try:  # 26/10: token vencido (OAuthException) e perfil do cofre logado -> pelo navegador
            _graph("me", fields="user_id", access_token=tok)
        except RuntimeError as e:
            from postar_insta_auto import cofre_logado
            if "OAuthException" in str(e) and cofre_logado(conta):
                log(f"[{conta}] token vencido — posto pelo navegador ({cofre_logado(conta)})")
                r, tok = {**r, "cofre": cofre_logado(conta)}, None
            else:
                raise
    if tok and not (r.get("cofre") or r.get("maquina")):
        ig = _graph("me", fields="user_id", access_token=tok)["user_id"]
        from postar_ms_energy import upload_video_publico  # litterbox -> uguu -> tmpfiles (serve pra imagem)
        alts = _textos_alternativos(meta)
        filhos = []
        for i, img in enumerate(sorted(pasta.glob("slide_*.jpg"))):
            url = upload_video_publico(str(img))
            if not url:
                raise RuntimeError(f"upload público falhou: {img.name}")
            item = {"image_url": url, "is_carousel_item": "true", "access_token": tok}
            if i < len(alts) and alts[i]:
                item["alt_text"] = alts[i][:1000]  # 25/10: busca e leitor de tela (a API aceita, testado)
            filhos.append(_graph(f"{ig}/media", item)["id"])
        car = _graph(f"{ig}/media", {"media_type": "CAROUSEL", "children": ",".join(filhos),
                                     "caption": legenda, "access_token": tok})["id"]
        for _ in range(24):
            st = _graph(car, fields="status_code", access_token=tok).get("status_code")
            if st == "FINISHED":
                break
            if st == "ERROR":
                raise RuntimeError("Instagram recusou o carrossel (status ERROR)")
            time.sleep(5)
        mid = _graph(f"{ig}/media_publish", {"creation_id": car, "access_token": tok})["id"]
        link = _graph(mid, fields="permalink", access_token=tok).get("permalink")
        meta["postado"] = {"como": "carrossel", "media_id": mid, "permalink": link}
    elif r.get("cofre") or r.get("maquina"):
        from postar_insta_auto import postar_navegador
        ok, msg = postar_navegador(conta, r, _como_reel(pasta), " ".join(legenda.split()))
        if not ok:
            raise RuntimeError(f"navegador: {msg}")
        meta["postado"] = {"como": "reel de slides", "msg": msg}
    else:
        raise RuntimeError("conta sem token e sem navegador configurado")
    meta["postado"]["em"] = datetime.now().isoformat(timespec="seconds")
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    h = _hist()
    h.append({"conta": conta, "data": meta["postado"]["em"], "capa": meta["capa"], "pasta": str(pasta),
              "link": meta["postado"].get("permalink")})
    pe._gravar(HIST, h[-500:])
    log(f"[{conta}] PUBLICADO ({meta['postado']['como']}): {meta['postado'].get('permalink') or meta['postado'].get('msg')}")
    return meta["postado"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conta")
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--so-gerar", action="store_true")
    ap.add_argument("--postar")
    a = ap.parse_args()
    if a.postar:
        postar(a.postar)
        return
    contas = list(pe.marcas()) if a.todas else [a.conta]
    erros = []
    for conta in contas:
        try:
            pasta = gerar(conta)
            if pasta and not a.so_gerar:
                postar(pasta)
        except Exception as e:  # noqa: BLE001
            log(f"[{conta}] ERRO: {type(e).__name__}: {str(e)[:200]}")
            erros.append(f"{conta}: {str(e)[:80]}")
    if erros and not a.so_gerar:
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar("Carrossel das marcas: " + " | ".join(erros)[:400], "carrossel-marca", importante=False)
        except Exception:  # noqa: BLE001
            pass
    if a.todas and not a.so_gerar:  # 25/10: o que já foi postado (todas as contas) vai pro Drive
        try:
            import arquivar_insta_drive
            arquivar_insta_drive.tudo(log=log)
        except Exception as e:  # noqa: BLE001
            log(f"arquivar no Drive falhou: {type(e).__name__}: {e}")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
