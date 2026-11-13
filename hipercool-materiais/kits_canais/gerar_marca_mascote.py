# 03/11 dona: "temos que trocar as capas dos canais em si e as fotos de perfil também pela da mascote, como as do
# Manhwa Noturno, que já são boas". Gera, por canal, perfil (800x800) e banner (2560x1440) com a MARIA (mascote) no
# estilo do kit do Manhwa Noturno (como cirar imagens de canais\canal_manhwa_noturno): noite, neon roxo, arte manhwa,
# nome do canal em amarelo grosso + subtítulo na área segura do banner (1546x423 no meio).
#   python gerar_marca_mascote.py ["Canal" ...]   -> kits_canais\mascote_<canal>\perfil.png banner.png
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import capa_ia_anime as c  # noqa: E402

AQUI = Path(__file__).parent
REF_NOTURNO = Path(r"D:\hipercool-materiais\como cirar imagens de canais\canal_manhwa_noturno")
FONTE = r"C:\Windows\Fonts\impact.ttf"
CANAIS = {  # canal: subtítulo do banner
    "ForjaReact": "RESUMOS COMPLETOS DE MANHWA",
    "Dorama Noturno": "HISTÓRIAS COMPLETAS TODA NOITE",
    "CenaReact": "RESUMOS COMPLETOS DE MANHWA",
    "Fio da Meada": "HISTÓRIAS COMPLETAS DO COMEÇO AO FIM",
    "HistoriasEmFrames": "HISTÓRIAS COMPLETAS EM MANHWA",
    "Curiosidades Noturnas": "RESUMOS COMPLETOS TODA NOITE",
    "InventoReact": "RESUMOS COMPLETOS DE MANHWA",
    "inovare manhwa br": "RESUMOS COMPLETOS DE MANHWA",
    "Animescomia": "ANIMES RESUMIDOS DO COMEÇO AO FIM",
}
MARIA = ("MARIA the mascot girl from the SECOND reference (long wavy dark-brown hair to her waist, golden-brown eyes, "
         "tanned caramel skin, beauty mark under her left eye) - same face and hair exactly")
PERFIL = (f"A square YouTube channel profile picture in the SAME style as the FIRST reference (night city neon bokeh "
          f"background in purple, pink and blue, glossy manhwa art, close-up portrait): {MARIA}, winking with one "
          "finger on her lips, a playful smile, blushing, wearing a black spaghetti-strap top and a choker. Her face "
          "centered and big (it will be cut in a circle). No text, no logo.")
BANNER = (f"A wide 16:9 YouTube channel banner art in the SAME style and mood as the FIRST reference (dark luxury room "
          f"at night, big window with a purple neon city, glossy manhwa art): {MARIA}, in a black silk nightdress, "
          "leaning playfully over a handsome blushing dark-haired man who sits on the floor, on the RIGHT half of the "
          "image. The LEFT and CENTER are calm dark room space (text will be written there later). No text, no logo.")


def _texto(banner, nome, sub, out):
    im = Image.open(banner).convert("RGB").resize((2560, 1440), Image.LANCZOS)
    esc = Image.new("L", im.size, 0)
    ImageDraw.Draw(esc).rectangle((0, 0, 1500, 1440), fill=150)
    im = Image.composite(Image.new("RGB", im.size, (12, 6, 24)), im, esc.filter(ImageFilter.GaussianBlur(220)))
    # 03/11: na 1ª leva o texto caiu em cima das personagens -> painel escuro translúcido atrás do texto (área segura)
    painel = Image.new("L", im.size, 0)
    ImageDraw.Draw(painel).rounded_rectangle((520, 560, 1560, 900), radius=40, fill=190)
    im = Image.composite(Image.new("RGB", im.size, (10, 4, 22)), im, painel.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(im)
    f1, f2 = ImageFont.truetype(FONTE, 118), ImageFont.truetype(FONTE, 56)
    x, y = 560, 590  # área segura: x 507-2053, y 508-931
    d.text((x, y), nome.upper(), font=f1, fill=(255, 214, 0), stroke_width=7, stroke_fill=(0, 0, 0))
    d.text((x + 4, y + 150), sub, font=f2, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((x + 4, y + 225), "Vídeos novos toda semana", font=f2, fill=(205, 160, 255), stroke_width=3,
           stroke_fill=(0, 0, 0))
    im.save(out, optimize=True)


def um(nome):
    d = AQUI / f"mascote_{nome.replace(' ', '_').lower()}"
    d.mkdir(exist_ok=True)
    maria = c._maria(nome)
    if not (d / "perfil.png").exists():
        img = c._gerar_com_ref(PERFIL, str(REF_NOTURNO / "perfil_800.jpg"), "16:9", [str(maria)])
        if img:
            im = Image.open(img).convert("RGB")
            w, h = im.size
            s = min(w, h)
            im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((800, 800)).save(d / "perfil.png")
    if not (d / "banner.png").exists():
        img = c._gerar_com_ref(BANNER, str(REF_NOTURNO / "banner_2560x1440.jpg"), "16:9", [str(maria)])
        if img:
            Image.open(img).convert("RGB").save(d / "arte_banner.png")  # arte crua: refaz o texto sem gastar Flow
            _texto(img, nome, CANAIS.get(nome, "RESUMOS COMPLETOS"), d / "banner.png")
    elif (d / "arte_banner.png").exists() and "--texto" in sys.argv:
        _texto(d / "arte_banner.png", nome, CANAIS.get(nome, "RESUMOS COMPLETOS"), d / "banner.png")
    print(nome, [p.name for p in d.glob("*.png")], flush=True)


if __name__ == "__main__":
    for n in [a for a in sys.argv[1:] if not a.startswith("--")] or CANAIS:
        try:
            um(n)
        except Exception as e:  # noqa: BLE001
            print(n, "erro", type(e).__name__, e, flush=True)
