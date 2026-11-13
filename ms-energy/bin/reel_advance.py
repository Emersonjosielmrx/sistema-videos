# -*- coding: utf-8 -*-
r"""reel_advance.py — Reels da ADVANCE ENERGIA SOLAR (@advance_novoestrela, Castanhal-PA) com o CLONE do Luiz
(dona 30/10: "cadê os vídeos de avatar? só vejo os carrosséis").

Reaproveita o pipeline ms_v2 (gerar_short_veo: roteiro_ms -> Veo 3.1 -> trava qa_ms -> montagem_ms -> trava final)
trocando, só neste processo, a marca: empresa/convite/hashtags (roteiro_ms), fotos-base do clone = Luiz
(assets\advance\clone_bases, rosto conferido pelo foto_na_hora), roupa azul-marinho como na foto dele, cartão final
no estilo da matriz (roxo + laranja + logo Advance) e histórico próprio. Posta por HTTP com o cofre (postar.py reel)
e a capa no Story. Clone que não passa no revisor de rosto = NÃO posta (nunca outro rosto no lugar do dono).

    D:\veo\venv\Scripts\python.exe reel_advance.py            # gera 1 e posta
    D:\veo\venv\Scripts\python.exe reel_advance.py --so-gerar
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\ms-energy\bin")
sys.path.insert(0, r"D:\veo\beta")
import roteiro_ms  # noqa: E402
import montagem_ms  # noqa: E402
import carrossel_advance as ca  # noqa: E402

CONTA = ca.CONTA
BASES = Path(r"D:\ms-energy\assets\advance\clone_bases")
SAIDA = Path(r"D:\ms-energy\videos\reels_advance")
LOG = Path(r"D:\ms-energy\logs\reel_advance.log")


def log(msg):
    linha = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(linha, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


# ───────────────────────── troca de marca (só neste processo) ─────────────────────────

def _clone_advance(cenario, fala_final, log=print):
    """Foto do Luiz NO cenário da pauta, criada na hora pelo Flow e conferida contra as fotos dele (foto_na_hora)."""
    import foto_na_hora
    if foto_na_hora.bases_com_rosto(str(BASES)) < 3:
        log("  [CLONE] menos de 3 fotos do Luiz com rosto — sem vídeo")
        return None
    foto_na_hora.usar_bases(str(BASES))
    for rodada in range(3):
        f = foto_na_hora.gerar(roteiro_ms.CENARIOS[cenario], fala_final, tag="advance_clone",
                               pedido=roteiro_ms.PEDIDO_CLONE.format(cenario=roteiro_ms.CENARIOS[cenario]))
        if f:
            log(f"  [CLONE] Luiz no cenário '{cenario}': {Path(f).name}")
            return f, str(BASES)
        aprovadas = [r.get("arquivo") for r in foto_na_hora._registros()
                     if r.get("aprovada") and r.get("tag") == "advance_clone" and r.get("arquivo")
                     and Path(r["arquivo"]).exists() and r.get("cenario") == roteiro_ms.CENARIOS[cenario]]
        if aprovadas:
            return aprovadas[-1], str(BASES)
        if rodada < 2:
            log("  [CLONE] Flow sem conta livre — espero 4 min")
            time.sleep(240)
    return None


def _legendas_advance(legenda, pauta_id):
    tags = ["#energiasolar", "#castanhal", "#castanhalpa", "#energiasolarpara", "#painelsolar", "#advanceenergiasolar"]
    insta = (f"{legenda.strip()}\n\n"
             "☀️ Quer saber quanto dá para economizar? Comente SOL ou chame no WhatsApp do perfil: o orçamento é grátis.\n"
             f"📍 {ca.LOCAL}\n\n" + " ".join(tags))
    return insta, insta, tags


def _cartao_advance(foto_fundo, destino):
    from PIL import Image, ImageDraw, ImageFilter, ImageOps
    W, H = montagem_ms.W, montagem_ms.H
    if foto_fundo and Path(foto_fundo).exists():
        fundo = ImageOps.fit(Image.open(foto_fundo).convert("RGB"), (W, H)).filter(ImageFilter.GaussianBlur(6))
    else:
        fundo = Image.new("RGB", (W, H), ca.ROXO_ESC)
    roxo = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(roxo)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(ca.ROXO[i] * (1 - t) + ca.ROXO_ESC[i] * t) for i in range(3)) + (225,))
    im = Image.alpha_composite(fundo.convert("RGBA"), roxo)
    px = montagem_ms.px
    lg = ca.logo(px(560))
    im.alpha_composite(lg, ((W - lg.width) // 2, px(150)))
    # cabe na largura (vídeo é 1080x1920; o itálico empurra a 1ª linha ~0.18 x altura do bloco para a direita)
    from PIL import ImageFont
    tam = int(W * 0.2)
    while ImageDraw.Draw(im).textlength("ORÇAMENTO", font=ImageFont.truetype(ca.ANTON, tam)) > W * 0.68:
        tam -= 4
    y = ca._titulo(im, ["Orçamento", "grátis"], int(W * 0.06), px(150) + lg.height + px(60), tam,
                   ["white", ca.LARANJA], espaco=1.3)
    d = ImageDraw.Draw(im)
    F = montagem_ms

    def centro(t, f, y, cor="white"):
        d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=cor)

    y += px(20)
    for ln in F._quebrar(d, "Energia solar para casa, comércio e campo", F._f(F.FONTE_XBOLD, px(40)), W - px(120)):
        centro(ln, F._f(F.FONTE_XBOLD, px(40)), y)
        y += px(54)
    y += px(40)
    t = "CHAME NO WHATSAPP"
    tb = px(50)
    while d.textlength(t, font=F._f(F.FONTE_BLACK, tb)) > W * 0.72:
        tb -= 2
    fb = F._f(F.FONTE_BLACK, tb)
    lw = d.textlength(t, font=fb)
    d.rounded_rectangle(((W - lw) / 2 - px(50), y - px(22), (W + lw) / 2 + px(50), y + px(80)), radius=px(50),
                        fill=ca.LARANJA)
    centro(t, fb, y)
    y += px(130)
    centro("@" + CONTA, F._f(F.FONTE_XBOLD, px(40)), y)
    y += px(58)
    centro(ca.LOCAL, F._f(F.FONTE_XBOLD, px(34)), y, (225, 215, 255))
    im.convert("RGB").save(destino, quality=95)
    return destino


def trocar_marca():
    roteiro_ms.EMPRESA = ca.EMPRESA
    roteiro_ms.CTA_FALADO = "Orçamento grátis com a Advance."
    roteiro_ms.INSTAGRAM = "@" + CONTA
    roteiro_ms.HIST = Path(r"D:\ms-energy\cache\historico_roteiros_advance.json")
    roteiro_ms.PAUTAS = [p for p in roteiro_ms.PAUTAS if p[0] not in ("experiencia", "empresa_local", "manutencao", "barato_caro",
                                                                   "clientes")] + [
        ("manutencao", "telhado", "Manutencao e simples: limpeza de vez em quando e revisao; a Advance tambem cuida disso."),
        ("empresa_local", "comercio", "Empresa de Castanhal, no Para, que conhece o sol, a chuva e os telhados da regiao."),
        ("barato_caro", "telhado", "Instalacao nao e tudo igual: o barato pode sair caro; projeto e instalacao bem "
                                   "feitos evitam prejuizo."),
        # 30/10: fotos reais do Luiz com clientes que fecharam projeto (pasta do Drive) -> prova social
        ("clientes", "casa", "Clientes de verdade de Castanhal e regiao fechando o projeto de energia solar com a "
                             "Advance; quem fecha indica para vizinho e familia."),
    ]
    roteiro_ms.RESERVA.update({
        "manutencao": ("Painel solar dá trabalho? A manutenção é simples e a Advance cuida disso.", "Dá trabalho?"),
        "empresa_local": ("Somos de Castanhal e conhecemos o sol, a chuva e os telhados daqui.", "Empresa de Castanhal"),
        "barato_caro": ("Instalação não é tudo igual. Feita do jeito certo, evita prejuízo e dor de cabeça.",
                        "O barato sai caro?"),
        "clientes": ("Mais um cliente da região fechou com a Advance. O próximo pode ser você.", "Mais um cliente!"),
    })
    roteiro_ms.PEDIDO_CLONE = roteiro_ms.PEDIDO_CLONE.replace("plain solid red polo shirt", "plain solid navy blue shirt")
    roteiro_ms._clone = _clone_advance
    roteiro_ms.legendas_finais = _legendas_advance
    roteiro_ms.escolher_pauta = _pauta_advance
    montagem_ms.cartao = _cartao_advance
    montagem_ms.VERMELHO = ca.LARANJA


_pauta_original = roteiro_ms.escolher_pauta


def _pauta_advance(evitar=(), formato="reel", hist=None):
    import random
    usadas = {h.get("pauta"): i for i, h in enumerate(roteiro_ms._hist() if hist is None else hist)}
    cand = sorted((p for p in roteiro_ms.PAUTAS if p[0] not in evitar), key=lambda p: usadas.get(p[0], -1))[:5]
    return random.choice(cand)


# ───────────────────────── gerar e postar ─────────────────────────

def _proximo_tipo():
    """30/10 (dona: "por que só vídeo Veo? cadê as variações, imagem de obras como tinha no da MS"): rodízio dos
    formatos da MS Energy. clone do Luiz <-> foto REAL de obra animada pelo Veo (narrador do Veo). O video_real da MS
    narra com edge Thalita PURA (voz proibida sem clone): fica de fora até ganhar voz clonada."""
    feitos = [json.loads(j.read_text("utf-8")).get("tipo_video")
              for j in sorted(SAIDA.glob("*.json"), key=lambda p: p.stat().st_mtime)]
    ultimo = feitos[-1] if feitos else None
    if ultimo != "obra_real":
        # 30/10: material REAL que o Luiz põe na pasta do Drive (obra_advance) vem antes do Veo
        try:
            import obra_advance
            if obra_advance.material():
                return "obra_real"
        except Exception as e:  # noqa: BLE001  (Drive fora: segue o Veo)
            log(f"pasta do Drive não respondeu ({type(e).__name__}) — sigo o Veo")
    return "com_foto" if ultimo == "apresentador" else "criativo"


def gerar():
    trocar_marca()
    import gerar_short_veo as g
    SAIDA.mkdir(parents=True, exist_ok=True)
    tipo = _proximo_tipo()
    if tipo == "obra_real":
        import obra_advance
        log("formato deste Reel: material real da pasta do Drive")
        r = obra_advance.gerar(log)
        if r:
            return r
        tipo = "criativo"
    log(f"formato deste Reel: {'foto real de obra' if tipo == 'com_foto' else 'avatar do Luiz'}")
    r = g.gerar_short_veo(output_dir=SAIDA, tipo=tipo, log=log)
    if not r or r == "SEM_CONTA":
        log(f"sem vídeo ({r})")
        return None
    side = json.loads(Path(r).with_suffix(".json").read_text("utf-8"))
    if side.get("tipo_video") == "foto_real":
        return Path(r)
    if side.get("tipo_video") != "apresentador" or "clone" not in json.dumps(side):
        # o pipeline caiu para pessoa inventada pelo Veo: não é o Luiz -> não vai pro perfil dele
        destino = Path(r"D:\ms-energy\videos\_revisar") / Path(r).name
        destino.parent.mkdir(exist_ok=True)
        Path(r).replace(destino)
        log(f"vídeo sem o clone do Luiz -> {destino} (não posta)")
        return None
    return Path(r)


def postar(mp4):
    mp4 = Path(mp4)
    side_arq = mp4.with_suffix(".json")
    side = json.loads(side_arq.read_text("utf-8"))
    if side.get("postado"):
        return side["postado"]
    # 04/11 (dona: "nunca mais conteúdo de uma empresa no Insta da outra"): o vídeo tem que ser da Advance E o rosto o
    # do Luiz (fotos-base DESTA empresa). Recusou = _revisar + aviso; o insistir pega outro.
    trocar_marca()
    import gerar_short_veo as g
    import trava_empresa
    trava_empresa.conferir(mp4, g._empresa_atual(), BASES, log)
    sys.path.insert(0, str(ca.NSN))
    from services.instagram.postar import InstagramPostar
    ig = InstagramPostar(CONTA)
    try:
        code = ig.reel(str(mp4), side["legenda_insta"])
    except RuntimeError as e:  # 06/11: HTTP limitado (1357001/spam) mas o Chrome do cofre posta -> vai pelo navegador
        if not any(s in str(e).lower() for s in ("1357001", "entre para continuar", "feedback_required")):
            raise
        # 12/11: o HTTP "limitado" às vezes JÁ publicou — o navegador postava o mesmo vídeo de novo (sem legenda)
        code = ca.reel_ja_saiu(CONTA, side["legenda_insta"])
        if code:
            log(f"HTTP respondeu erro mas o Reel JÁ SAIU ({code}) — não posto de novo pelo navegador")
            code = None if code == "ja_saiu" else code
        else:
            log("HTTP limitado pelo Instagram — tentando pelo navegador do cofre")
            if not ca.reel_pelo_navegador(CONTA, mp4, side["legenda_insta"]):
                raise
            code = None
    side["postado"] = {"permalink": f"https://www.instagram.com/reel/{code}/" if code else f"https://www.instagram.com/{CONTA}/",
                       "em": datetime.now().isoformat(timespec="seconds")}
    side_arq.write_text(json.dumps(side, ensure_ascii=False, indent=2), "utf-8")
    log(f"PUBLICADO: {side['postado']['permalink']}")
    # dona 30/10: o mesmo vídeo vai para o status do WhatsApp do Luiz (se ele conectou o WhatsApp no Painel de
    # Clientes). Falhar aqui nunca desfaz o post do Instagram.
    try:
        sys.path.insert(0, r"D:\painel-clientes\coletor")
        import status_whatsapp
        if status_whatsapp.mandar_video("advance", mp4, side.get("legenda_insta") or "", log=log):
            side["status_whatsapp"] = datetime.now().isoformat(timespec="seconds")
            side_arq.write_text(json.dumps(side, ensure_ascii=False, indent=2), "utf-8")
    except Exception as e:  # noqa: BLE001
        log(f"status WhatsApp: {type(e).__name__}: {e}")
    return side["postado"]


def _pendente():
    """Reel pronto e não postado: material REAL da empresa (obra_real) antes do Veo; depois o mais novo."""
    prontos = []
    for j in sorted(SAIDA.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):  # nomes têm 2 prefixos
        s = json.loads(j.read_text("utf-8"))
        if not s.get("postado") and j.with_suffix(".mp4").exists():
            prontos.append((s.get("tipo_video") != "obra_real", j.with_suffix(".mp4")))
    return min(prontos, key=lambda p: p[0])[1] if prontos else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-gerar", action="store_true")
    a = ap.parse_args()
    def publicar(mp4):
        postar(mp4)
        if json.loads(Path(mp4).with_suffix(".json").read_text("utf-8")).get("tipo_video") == "obra_real":
            import obra_advance
            obra_advance.marcar_usados(mp4, log)

    try:
        if a.so_gerar:
            gerar()
            return
        ca.insistir(lambda: _pendente() or gerar(), publicar, log=log)  # 01/11: tenta até sair
    except Exception as e:  # noqa: BLE001
        log(f"ERRO: {type(e).__name__}: {e}")
        if any(s in str(e).lower() for s in ca.LIMITE):
            ca.pausar(str(e), log=log)
        raise


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
