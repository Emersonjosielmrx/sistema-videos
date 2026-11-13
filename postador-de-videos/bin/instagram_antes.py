# -*- coding: utf-8 -*-
r"""instagram_antes.py — PADRÃO (dona 05/11/2026): "torne padrão documentado para qualquer Instagram salvar o ANTES de
trabalharmos". Caso que originou: o dono do Açaí O Precioso disse que sumiram coisas dos destaques; o print das 00:28
(tirado por acaso antes de mexermos) provou que o perfil já estava sem destaques.

Rodar ANTES da 1ª ação em qualquer Instagram novo (cliente ou nosso). Pela saída da própria conta (perfil do cofre
neste PC). Só LÊ: não posta, não apaga, não arquiva.
Salva em D:\hipercool-materiais\clientes_antes\<usuario>\<AAAA-MM-DD_HHMM>\ :
  1_perfil.png (com data/hora gravada na imagem), 2_destaques.txt, 3_arquivados_stories.png (se a conta deixar ver),
  4_posts.txt (links dos posts visíveis), LEIA.txt (quando, quem, contagens).
    D:\veo\venv\Scripts\python.exe instagram_antes.py <perfil_do_cofre> <usuario>
    ex.: instagram_antes.py ig_acai_no_litro acai_oprecioso
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, r"D:\logins-google")
BASE = Path(r"D:\hipercool-materiais\clientes_antes")
FONTE = r"D:\hipercool-materiais\assets\fonts\Montserrat-ExtraBold.ttf"


def carimbar(png, texto):
    im = Image.open(png).convert("RGB")
    f = ImageFont.truetype(FONTE, max(18, im.width // 48))
    barra = int(f.size * 2.2)
    novo = Image.new("RGB", (im.width, im.height + barra), (20, 20, 20))
    novo.paste(im, (0, barra))
    ImageDraw.Draw(novo).text((16, (barra - f.size) // 2), texto, font=f, fill="white")
    novo.save(png)


def main(perfil, usuario):
    import cofre
    from playwright.sync_api import sync_playwright
    agora = datetime.now()
    pasta = BASE / usuario / agora.strftime("%Y-%m-%d_%H%M")
    pasta.mkdir(parents=True, exist_ok=True)
    porta, proc = cofre.abrir(perfil)
    info = {"quando": agora.isoformat(timespec="seconds"), "perfil_cofre": perfil, "usuario": usuario}
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = b.contexts[0].new_page()
            pg.goto(f"https://www.instagram.com/{usuario}/", timeout=60000)
            pg.wait_for_timeout(8000)
            pg.screenshot(path=str(pasta / "1_perfil.png"))
            carimbar(pasta / "1_perfil.png", f"{agora:%d/%m/%Y %H:%M} — @{usuario} ANTES de mexermos")
            try:
                info["cabecalho"] = pg.inner_text("header")[:800]
            except Exception:  # noqa: BLE001
                pass
            dest = pg.eval_on_selector_all("ul li", "e => e.map(x => x.innerText).filter(t => t && t.length < 40)")
            (pasta / "2_destaques.txt").write_text("\n".join(dest) or "(nenhum destaque)", "utf-8")
            info["destaques"] = dest
            links = []
            for _ in range(6):
                for h in pg.eval_on_selector_all('a[href*="/p/"], a[href*="/reel/"]', "e => e.map(a => a.href)"):
                    if h not in links:
                        links.append(h)
                pg.mouse.wheel(0, 3000)
                pg.wait_for_timeout(1500)
            (pasta / "4_posts.txt").write_text("\n".join(links), "utf-8")
            info["posts_visiveis"] = len(links)
            try:  # só a própria conta logada vê o arquivo
                pg.goto("https://www.instagram.com/archive/stories/", timeout=60000)
                pg.wait_for_timeout(8000)
                pg.screenshot(path=str(pasta / "3_arquivados_stories.png"), full_page=True)
                carimbar(pasta / "3_arquivados_stories.png", f"{agora:%d/%m/%Y %H:%M} — itens arquivados (stories)")
            except Exception as e:  # noqa: BLE001
                info["arquivados"] = f"não deu: {type(e).__name__}"
            pg.close()
    finally:
        cofre.fechar(proc, nome=perfil)
    (pasta / "LEIA.txt").write_text(json.dumps(info, ensure_ascii=False, indent=1), "utf-8")
    print(pasta)
    return pasta


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1], sys.argv[2].lstrip("@"))
