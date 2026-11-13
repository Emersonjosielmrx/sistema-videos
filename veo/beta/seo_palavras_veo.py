#!/usr/bin/env python3
"""seo_palavras_veo.py - o que o publico DIGITA na busca do YouTube, por tema do Veo (item DS-03, 16/10).

Antes nenhum titulo do veo usava palavra buscada. Copia a ideia do banco do hipercool (seo_palavras.json: "como o
publico busca"), mas montado pelo autocompletar PUBLICO do YouTube (suggestqueries, client=firefox, ds=yt; sem chave
de API). A rede (mr/rede.py adaptar) manda as do tema do clipe ao agente de metadados, que usa as que combinarem.

Grava logs/seo_palavras_veo.json {tema_do_arquivo: [palavras]}. Rodar 1x por semana (as buscas mudam devagar):
    python seo_palavras_veo.py
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

SAIDA = Path(__file__).resolve().parent / "logs" / "seo_palavras_veo.json"
# prefixo do arquivo do limpo (tema_AAAAMMDD_HHMMSS) -> sementes de busca
SEMENTES = {
    "segredos_do_oce": ["fundo do mar", "oceano profundo", "criaturas marinhas"],
    "robos_desastrad": ["robô", "robô humanoide", "robô engraçado"],
    "robos": ["robô", "robô humanoide"],
    "tech_news": ["notícias de tecnologia", "inteligência artificial"],
    "noticias_de_ia": ["notícias inteligência artificial", "ia nova"],
    "super_slow_ia": ["câmera lenta", "slow motion"],
    "slowmo": ["câmera lenta", "slow motion"],
    "danca_e_musica_": ["dança", "música ia"],
    "stand-up_ia": ["stand up comedy", "piada"],
    "stand-up": ["stand up comedy", "piada"],
    "alienigenas": ["alienígena", "ets", "ovni"],
    "vendas_com_ia": ["vender no whatsapp", "inteligência artificial vendas"],
    "transformacao": ["transformação", "antes e depois"],
    "surreal": ["vídeo surreal", "ia vídeo"],
    "motivacao_ia": ["motivação", "frases motivacionais"],
    "recenas_ia": ["cenas famosas", "filme"],
    "recordes_mundia": ["recorde mundial", "maior do mundo"],
    "mitos_vs_verdad": ["mito ou verdade", "verdade ou mentira"],
    "dicas_financeir": ["dinheiro", "educação financeira"],
    "corpo_humano": ["corpo humano", "curiosidades corpo humano"],
    "fatos_bizarros": ["fatos bizarros", "curiosidades"],
    "fofos_e_absurdo": ["animais fofos", "fofo"],
    "humor_de_ia": ["humor", "vídeo engraçado"],
}
# o autocompletar mistura musica com o tema ("camera lenta funk/phonk/slowed"): fora
MUSICA = re.compile(r"\b(funk|phonk|slowed|remix|letra|lyrics|1 hour|hariel|henry freitas|mc |música|musica|clipe "
                    r"oficial|tiktok|instrumental|karaok)", re.I)


def sugestoes(q):
    url = ("https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=pt-BR&gl=BR&q="
           + urllib.parse.quote(q))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace"))[1]


def main():
    banco = {}
    for tema, sementes in SEMENTES.items():
        achadas = []
        for s in sementes:
            try:
                achadas += [x for x in sugestoes(s) if not MUSICA.search(x)]
            except Exception as ex:  # noqa: BLE001
                print(f"  {s}: {ex}")
            time.sleep(0.4)
        banco[tema] = list(dict.fromkeys(achadas))[:15]
        print(f"{tema}: {', '.join(banco[tema][:6])}")
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps({"_leia": "autocompletar publico do YouTube por tema do Veo (seo_palavras_veo.py)",
                                 "temas": banco}, ensure_ascii=False, indent=1), "utf-8")
    print(f"gravado: {SAIDA}")


if __name__ == "__main__":
    main()
