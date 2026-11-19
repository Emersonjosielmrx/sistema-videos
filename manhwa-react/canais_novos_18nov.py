# -*- coding: utf-8 -*-
"""18/11 dona: "tem canais novos nos celulares... gerando capas e fotos de perfil para o outro agente colocar os que
faltam, inclusive ha outros canais novos tb sem capa e banner e perfil".
Conferido na página pública (sem login) quais canais vivos estão com avatar padrão e/ou sem banner.
Canais SEM rosto (nicho faceless e canais do teste do celular não podem se ligar à família) -> perfil = emblema por IA,
banner = arte IA + nome (mr.channels.make_banner sem foto). Saída: canais\\<slug>\\ (perfil, banner, marca, textos).
    python canais_novos_18nov.py [slug ...]
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from PIL import Image  # noqa: E402
from mr import channels as C  # noqa: E402
from mr.imagem import gerar  # noqa: E402

cfg = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
RAIZ = BASE / "canais"

EMB = ("Bold modern YouTube channel profile icon, single centered emblem filling the frame, flat vector + soft 3D, "
       "high contrast, clean dark background, ")

CANAIS = [
    # --- controle PC / outros agentes (avatar padrão + sem banner) ---
    dict(slug="clinicalucrativaia", name="Clínica Lucrativa IA", handle="@clinicalucrativaia", color="#00B894",
         tagline="Gestão, marketing e IA para clínicas", via="PC",
         niche="gestão e marketing de clínicas e consultórios com inteligência artificial",
         description="Como encher a agenda e lucrar mais com a sua clínica usando inteligência artificial: marketing, "
                     "atendimento, gestão e automação para médicos, dentistas, psicólogos e estética. Vídeos novos toda semana.",
         keywords=["clínica", "consultório", "marketing médico", "gestão de clínica", "inteligência artificial",
                   "dentista", "estética", "agenda cheia", "automação", "IA para saúde"],
         arte={"perfil": EMB + "a medical cross merged with a rising profit arrow and a small AI chip, teal and white",
               "banner": "Wide modern bright medical clinic reception with soft teal light, holographic charts and AI "
                         "interface floating, clean futuristic look, no people"}),
    dict(slug="empresariointeligenteia", name="Empresário Inteligente IA", handle="@empresariointeligenteia",
         color="#3D7BFF", tagline="Negócios e lucro com inteligência artificial", via="PC",
         niche="negócios, empreendedorismo e IA aplicada a empresas",
         description="Estratégias reais para empresários usarem inteligência artificial e crescer: vendas, gestão, "
                     "produtividade e automação. Sem enrolação, direto ao ponto.",
         keywords=["empreendedorismo", "negócios", "inteligência artificial", "empresário", "gestão", "produtividade",
                   "automação", "IA para empresas", "lucro", "pequenas empresas"],
         arte={"perfil": EMB + "a stylized brain made of circuit lines inside a golden briefcase shape, blue and gold",
               "banner": "Wide cinematic modern office at night with city skyline, glowing blue AI network lines and "
                         "growth charts over the desk, premium business mood, no people"}),
    dict(slug="imovelemfoco", name="Imóvel em Foco", handle="@imovelemfoco", color="#FF8A00",
         tagline="Tudo sobre comprar, vender e investir em imóveis", via="PC",
         niche="mercado imobiliário, compra, venda e investimento em imóveis",
         description="Dicas práticas para comprar, vender, alugar e investir em imóveis: financiamento, documentação, "
                     "valorização e oportunidades do mercado imobiliário.",
         keywords=["imóveis", "mercado imobiliário", "financiamento", "comprar casa", "investir em imóveis", "aluguel",
                   "apartamento", "corretor", "valorização", "casa própria"],
         arte={"perfil": EMB + "a modern house silhouette inside a camera focus frame / magnifying lens, orange and white",
               "banner": "Wide cinematic modern houses and apartment buildings at golden hour, warm orange sky, "
                         "clean architecture, no people"}),
    dict(slug="leielucro", name="Lei e Lucro", handle="@leielucroia", color="#C9A227",
         tagline="Direito, dinheiro e seus direitos explicados", via="PC",
         niche="direito do dia a dia, direitos do consumidor e do trabalhador, finanças",
         description="Seus direitos explicados de um jeito simples: consumidor, trabalho, empresas, impostos e dinheiro. "
                     "Conhecimento jurídico que vira proteção e lucro.",
         keywords=["direito", "direitos do consumidor", "direito trabalhista", "advogado", "lei", "impostos",
                   "finanças", "seus direitos", "jurídico", "dinheiro"],
         arte={"perfil": EMB + "golden scales of justice with a coin on one side, gold on deep navy blue",
               "banner": "Wide cinematic law library with a golden scale of justice, stacks of gold coins and soft "
                         "warm light, navy and gold palette, no people"}),
    dict(slug="pordentro", name="Por Dentro", handle="@pordentrobr-d4w", color="#00C2FF",
         tagline="Como as coisas funcionam por dentro", via="PC",
         niche="como as coisas funcionam por dentro: motores, aviões, eletrônicos, máquinas e engenharia",
         description="Abrimos tudo para você ver por dentro: motores, aviões, eletrônicos, máquinas e invenções do dia a "
                     "dia. Engenharia explicada em poucos segundos.",
         keywords=["como funciona", "por dentro", "engenharia", "motor", "avião", "eletrônicos", "máquinas",
                   "curiosidades", "ciência", "shorts"],
         arte={"perfil": EMB + "a cutaway x-ray view of a mechanical gear engine, glowing cyan blueprint lines",
               "banner": "Wide cinematic exploded-view cutaway of a jet engine and a car engine in glowing cyan "
                         "blueprint style on a dark background, no people"}),
    dict(slug="vendasqueescalam", name="Vendas que Escalam", handle="@vendasqueescalam", color="#E63946",
         tagline="Vender mais todo mês, com método", via="PC",
         niche="vendas, marketing digital e crescimento de negócios",
         description="Técnicas de vendas, marketing digital e tráfego para vender mais todo mês: funil, copy, "
                     "atendimento e automação com IA.",
         keywords=["vendas", "marketing digital", "como vender mais", "funil de vendas", "copywriting", "tráfego pago",
                   "negócios", "empreendedorismo", "escala", "IA"],
         arte={"perfil": EMB + "a bold red rising staircase bar chart with an upward arrow, red and white",
               "banner": "Wide cinematic glowing red and white rising bar charts and arrows climbing like a staircase "
                         "over a dark city, energetic, no people"}),
    # --- celulares (teste 3 contas): subir SÓ pelo app do YouTube no próprio aparelho ---
    dict(slug="curiosodemais", name="Curioso Demais", handle="@CuriosoDemais-l6p", color="#7B2CFF",
         tagline="Curiosidades que você não sabia", via="CELULAR A2 (2042)",
         niche="curiosidades: animais, natureza, ciência e o mundo",
         description="Curiosidades rápidas que vão te deixar de boca aberta: animais, natureza, ciência e segredos do "
                     "mundo. Um Short novo todo dia!",
         keywords=["curiosidades", "você sabia", "animais", "natureza", "ciência", "fatos", "shorts", "incrível"],
         arte={"perfil": EMB + "a cute curious owl with huge glowing eyes peeking through a magnifying glass, purple",
               "banner": "Wide magical nature scene at twilight: exotic birds, a chameleon, glowing mushrooms and a "
                         "giant magnifying glass, purple and teal light, no people"}),
    dict(slug="fatosocultos", name="Fatos Ocultos", handle="@FatosOcultos-x8j", color="#14B37D",
         tagline="O que ninguém te contou", via="CELULAR A3 (2054)",
         niche="fatos ocultos e curiosidades: história, ciência, mistérios",
         description="Os fatos que ficam escondidos: história, ciência, natureza e mistérios que quase ninguém conhece. "
                     "Shorts novos todo dia.",
         keywords=["fatos", "curiosidades", "mistérios", "história", "ciência", "você sabia", "segredos", "shorts"],
         arte={"perfil": EMB + "a half-open eye inside a keyhole with green light leaking out, emerald on black",
               "banner": "Wide cinematic ancient hidden chamber with a door slightly open and emerald green light "
                         "pouring out, old maps and artifacts, mysterious mood, no people"}),
    dict(slug="segredosrevelados", name="Segredos Revelados", handle="@SegredosRevelados-q8h", color="#FFB703",
         tagline="Segredos do mundo revelados em segundos", via="CELULAR S20 Ultra (2052)",
         niche="segredos e curiosidades: como as coisas são feitas, natureza, ciência",
         description="Segredos revelados em poucos segundos: como as coisas são feitas, truques da natureza e da "
                     "ciência que ninguém explica. Shorts todo dia.",
         keywords=["segredos", "curiosidades", "revelado", "ciência", "natureza", "como é feito", "fatos", "shorts"],
         arte={"perfil": EMB + "a glowing golden padlock bursting open with light rays, amber on dark",
               "banner": "Wide cinematic old treasure chest opening with golden light bursting out, floating ancient "
                         "scrolls and gears, warm amber mood, no people"}),
]


def perfil(ch, out):
    p = gerar(cfg, ch["arte"]["perfil"], aspect="1:1")
    if not p:
        raise RuntimeError("imagem do perfil não saiu")
    C._cover(Image.open(p).convert("RGB"), 800, 800).save(out, quality=95)


def um(ch):
    pasta = RAIZ / ch["slug"]
    pasta.mkdir(parents=True, exist_ok=True)
    try:
        perfil(ch, pasta / "perfil.png")
        C.make_banner(cfg, ch, pasta / "banner.png", None)
        C.make_watermark(cfg, ch, pasta / "marca_dagua.png")
        C.write_docs(cfg, {**ch, "nota": f"Aplicar por: {ch['via']}"}, pasta)
        return ch["slug"], "OK"
    except Exception as e:  # noqa: BLE001
        return ch["slug"], f"ERRO {e}"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    so = set(sys.argv[1:])
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(um, [c for c in CANAIS if not so or c["slug"] in so]):
            print("RESULTADO", *r, flush=True)
