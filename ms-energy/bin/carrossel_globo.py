# -*- coding: utf-8 -*-
"""Carrossel da GLOBO SOLAR | ENERGIA GLOBAL (@globosolarenergiag, Concórdia do Pará) — dona 31/10/2026: "comece as
postagens da Globo Solar como fizemos com as do Advance, usando o conteúdo que temos geral e o que captamos do próprio
Instagram".

Mesmo visual e mesmas travas do carrossel_advance (capa com foto real, 4 slides, CTA; 90 min entre posts; pausa de
18 h se o Instagram limitar), com a marca da Globo: ardósia #1A222D + laranja-avermelhado #EA3A21 (medidos no avatar e
nos Reels dela). Fotos: as aprovadas da biblioteca geral (revisar_instalacao). Sem preço/promoção das artes antigas.
Posta por HTTP com a sessão do cofre ig_globosolarenergiag. Rodar com D:\\veo\\venv\\Scripts\\python.exe.
    python carrossel_globo.py              # posta o já gerado e não postado; senão gera e posta
    python carrossel_globo.py --so-gerar
    python carrossel_globo.py --postar <pasta>
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, r"D:\ms-energy\bin")
sys.path.insert(0, r"D:\veo\beta")
import carrossel_advance as ca  # noqa: E402
import carrossel_ms as cm  # noqa: E402
import roteiro_ms  # noqa: E402

CONTA = "globosolarenergiag"
LOCAL = "Concórdia do Pará e região"
ARDOSIA = (26, 34, 45)
ARDOSIA_ESC = (10, 13, 18)
LARANJA = (234, 58, 33)
EMPRESA = ("Globo Solar | Energia Global, empresa de energia solar de Concórdia do Pará, no Pará, Brasil (Av. Deodoro "
           "da Fonseca, bairro Pinheiro). Projeto e instalação de energia solar para casas, comércios e fazendas; "
           "financia e parcela. Orçamento pelo WhatsApp do perfil do Instagram @globosolarenergiag.")
OUTRA_MARCA = re.compile(r"ms ?energy|msenergy|advance|castanhal|santa maria", re.I)
PAUTAS = [p for p in ca.PAUTAS]
PAUTAS.insert(0, ("financia", "casa", "Dá para financiar e parcelar o sistema de energia solar; muita gente troca a "
                                      "conta de luz pela parcela. Orçamento sem compromisso."))

# tudo da Globo em arquivos próprios (o histórico, a pausa e o intervalo NÃO se misturam com os da Advance)
ca.DIR = Path(r"D:\ms-energy\videos\carrosseis_globo")
ca.HIST = Path(r"D:\ms-energy\cache\historico_carrosseis_globo.json")
ca.REELS = Path(r"D:\ms-energy\videos\reels_globo")
ca.PAUSA = Path(r"D:\ms-energy\cache\globo_pausa.json")
ca.PAUTAS = PAUTAS
ca.EMPRESA = EMPRESA


def logo_texto(largura, cor=None):
    """Logo em texto (GLOBO branco / SOLAR laranja, como o logo 3D do avatar), fundo transparente."""
    f1 = ImageFont.truetype(ca.ANTON, 200)
    f2 = ImageFont.truetype(ca.ANTON, 120)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w1, w2 = d.textlength("GLOBO", font=f1), d.textlength("SOLAR", font=f2)
    im = Image.new("RGBA", (int(max(w1, w2)) + 20, 360), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.text(((im.width - w1) / 2, 0), "GLOBO", font=f1, fill="white")
    dd.text(((im.width - w2) / 2, 215), "SOLAR", font=f2, fill=LARANJA)
    return im.resize((largura, int(im.height * largura / im.width)), Image.LANCZOS)


ca.usar_marca(ARDOSIA, ARDOSIA_ESC, LARANJA, CONTA, LOCAL, logo_texto)


def textos(pauta):
    roteiro_ms.EMPRESA = EMPRESA
    capas = [h.get("capa", "") for h in ca._hist()]
    correcao = ""
    for tentativa in range(4):
        try:
            t = cm._pedir_textos(pauta, capas, correcao)
        except Exception as e:  # noqa: BLE001
            ca.log(f"LLM falhou ({type(e).__name__}: {str(e)[:80]})")
            continue
        erros = cm._validar(t)
        if OUTRA_MARCA.search(json.dumps(t, ensure_ascii=False)):
            erros.append("cite só a Globo Solar de Concórdia do Pará (nenhuma outra empresa ou cidade)")
        if not erros:
            ok, problema = roteiro_ms._revisar(" ".join(s["texto"] for s in t["slides"]), pauta[2], tipo="carrossel")
            if not ok:
                erros = [f"revisor: {problema[:150]}"]
        if not erros:
            return t
        ca.log(f"textos reprovados ({tentativa + 1}): {'; '.join(erros)[:200]}")
        correcao = "CORRIJA a resposta anterior: " + "; ".join(erros)
    return None


def legenda(t, pauta_id):
    tags = ["#energiasolar", "#concordiadopara", "#energiasolarpara", "#painelsolar", "#globosolar"]
    if pauta_id == "rural":
        tags.append("#agro")
    return (f"{t['legenda'].strip()}\n\n"
            "☀️ Quer saber quanto dá para economizar? Comente SOL ou chame no WhatsApp do perfil: (91) 99394-9409.\n"
            f"📍 {LOCAL}\n\n" + " ".join(tags))


ca.textos = textos
ca.legenda = legenda


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-gerar", action="store_true")
    ap.add_argument("--postar")
    a = ap.parse_args()
    ca.DIR.mkdir(parents=True, exist_ok=True)
    try:
        if a.postar:
            if ca.espaco_ok():
                ca.postar(a.postar)
            return
        if a.so_gerar:
            ca.gerar()
            return
        ca.insistir(lambda: ca._pendente() or ca.gerar(), ca.postar)
    except Exception as e:  # noqa: BLE001
        ca.log(f"ERRO: {type(e).__name__}: {e}")
        if any(s in str(e).lower() for s in ca.LIMITE):
            ca.pausar(str(e))
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar(f"Globo Solar: carrossel falhou ({type(e).__name__}: {str(e)[:150]})",
                          "globo-carrossel", importante=False)
        except Exception:  # noqa: BLE001
            pass
        raise


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"[{datetime.now():%H:%M:%S}] Globo Solar")
    main()
