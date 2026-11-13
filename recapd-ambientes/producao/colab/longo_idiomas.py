r"""longo_idiomas.py — longo JÁ FEITO em português -> versão em outra língua nos canais estrangeiros (12/11/2026).

Dona 12/11: "os longos em outras línguas já deveriam existir; faça do jeito mais eficiente". O jeito mais barato:
  - o ROTEIRO pt pronto (na_nuvem/<ficha>/roteiro.txt) é traduzido em blocos de 120 frases (mesma ordem/quantidade:
    imagem e cortes saem iguais, só muda a fala) — sem refazer a análise do vídeo;
  - a fonte é baixada de novo pelo mesmo preparar() do alimentador e o pedido vai pra MESMA fila do Kaggle com
    "idioma" (kaggle_trabalhador troca voz-base, fonte da legenda e marca "outra língua", igual aos Shorts);
  - o pronto volta pela fila normal; o postar_longos posta no canal da língua (canal do pedido).
Prioridade: vietnamita e inglês (os que rendem). Língua com canal punido (russo, italiano) não entra.

    python longo_idiomas.py vi V4msWWPktbU            # mostra o plano
    python longo_idiomas.py vi V4msWWPktbU --fazer    # traduz e manda pra fila
"""
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BIN = AQUI.parent / "bin"
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
sys.path[:0] = [str(AQUI), str(BIN)]

# canal estrangeiro de cada língua (cred do postador) — só os que podem receber (sem trava)
CANAL = {"vi": "8ROQmZVjbpwiwMoX", "en": "UYjkdFO3V3kjmKU5", "id": "nYsAKUb3DbR1QOEm", "th": "q3mik36FjtTgFkNC",
         "fr": "GG97QQt8lmyv0dDG", "hi": "GtuH5ezUK8eBaC60"}
BLOCO = 120


def traduzir(linhas, lang):
    import anime_idiomas
    out = []
    for i in range(0, len(linhas), BLOCO):
        parte = linhas[i:i + BLOCO]
        t = anime_idiomas.traduzir(parte, lang)
        if not t or len(t) != len(parte):
            raise RuntimeError(f"tradução do bloco {i // BLOCO + 1} falhou ({len(t or [])}/{len(parte)} frases)")
        out += t
        print(f"  bloco {i // BLOCO + 1}/{-(-len(linhas) // BLOCO)} ok", flush=True)
    return out


def main(lang, vid, fazer):
    import anime_idiomas
    if lang not in anime_idiomas.IDIOMAS or lang not in CANAL:
        sys.exit(f"língua {lang} sem canal liberado: {sorted(CANAL)}")
    ficha = next((d for d in FICHAS.iterdir() if d.name.startswith(vid)), None)
    if not ficha or not (ficha / "roteiro.txt").exists():
        sys.exit(f"ficha/roteiro de {vid} não achado em {FICHAS}")
    linhas = [l.strip() for l in (ficha / "roteiro.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    li = anime_idiomas.IDIOMAS[lang]
    print(f"{ficha.name}: {len(linhas)} frases -> {li['nome']} ({-(-len(linhas) // BLOCO)} blocos), canal {CANAL[lang]}")
    if not fazer:
        return
    trad = traduzir(linhas, lang)
    import cliente
    p = cliente.preparar(f"https://www.youtube.com/watch?v={vid}")
    # 12/11: o Kaggle só lê "roteiro.txt" — com outro nome ele refazia o roteiro EM PORTUGUÊS. Pasta própria da língua.
    (Path(p["work"]) / f"idioma_{lang}").mkdir(exist_ok=True)
    rot = Path(p["work"]) / f"idioma_{lang}" / "roteiro.txt"
    rot.write_text("\n".join(trad) + "\n", encoding="utf-8")
    titulo = f"[{lang.upper()}] {p['titulo']}"
    # nome próprio (sufixo da língua): a ficha/Drive do longo pt não é sobrescrita
    extra = {**{k: p[k] for k in ("vid", "titulo", "url")}, "nome": f"{p['nome']}_{lang}", "canal": CANAL[lang],
             "tipo": "manhwa",
             # 12/11 dona: "cuidado com memes e falas dos originais, que estão em português" — tudo que tem voz em pt
             # sai; ficam os memes de IMAGEM (sem fala) e os efeitos. As falas de personagem são as do roteiro já
             # traduzido (mesma voz clonada, outra língua), então ficam.
             "longo_override": {"memes_series.ligado": False, "resumo.memes": 0, "mascote.ligado": False,
                                "mascote.fala": False, "mascote.reacoes": False, "cta.ligado": False,
                                "memes_visuais.imagem_cada": 15, "memes_visuais.so_imagem": True},
             "idioma": {"codigo": lang, "nome": li["nome"], "voz": li["voz"], **{k: li[k] for k in
                                                                               ("fonte_png", "fonte_ass", "engine")
                                                                               if li.get(k)}}}
    pid = cliente.enviar(p["work"], p["video"], rot, titulo, extra)
    print(f"enviado {pid} ({li['nome']}, {len(trad)} frases)")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) < 2:
        print(__doc__)
        sys.exit(1)
    main(a[0], a[1], "--fazer" in sys.argv)
