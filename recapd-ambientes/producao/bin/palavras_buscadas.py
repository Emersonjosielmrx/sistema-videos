r"""palavras_buscadas.py — o que o público DIGITA na busca do YouTube, por nicho (16/11/2026).

Por quê: o banco config/seo_palavras.json foi escrito à mão em 30/10, nunca mais mudou e só tem palavras de ANIME
(isekai, sistema, "ele foi traído pelo clã"). O seo_generator punha essa lista no pedido do título de TODO nicho — um
Short de pesca ou de futebol recebia "anime recap, resumo anime" como "palavras buscadas". Os nichos que mais rendem
hoje (esportes, fatos, pesca) não tinham palavra nenhuma.

Como: o autocompletar público da busca do YouTube (suggestqueries, o mesmo que a caixa de busca usa; sem conta, sem
cookie, sem chave — não age como nenhuma conta nossa). Ideia vinda da caixa do pesquisador (youtube-autocomplete-miner
/ youtube-suggest-scraper), refeita em ~100 linhas só com requests. Poucas consultas, espaçadas, 1x por dia.

    python palavras_buscadas.py            # atualiza config/seo_palavras_nicho.json (tarefa PalavrasBuscadas, 1x/dia)
    python palavras_buscadas.py --ver      # só mostra o que tem

Saída: {"em": iso, "nichos": {nicho: {"palavras": [...], "padroes": [...]}}}. O seo_generator._palavras(b, midia) usa
o nicho do vídeo quando existe aqui; sem arquivo ou sem o nicho = o banco de sempre. SEO_PALAVRAS_NICHO=0 desliga.
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

PROD = Path(__file__).resolve().parent.parent
SAIDA = PROD / "config" / "seo_palavras_nicho.json"
URL = "https://suggestqueries.google.com/complete/search"
ESPACO_S = 1.5  # entre consultas: nunca em rajada

# sementes por nicho (as chaves são as "midia" do parceiro.json / seo_generator._MIDIAS). Semente curta = "palavras";
# semente em forma de pergunta/frase = "padroes" (como o público formula a busca)
SEMENTES = {
    "esportes": (["futebol curiosidades", "curiosidades do futebol", "jogador de futebol", "história do futebol"],
                 ["por que os jogadores de futebol ", "o jogador que ", "o que aconteceu com o jogador "]),
    "pesca": (["pescaria ", "pesca de ", "isca para ", "dicas de pescaria"],
              ["como pescar ", "qual a melhor isca para ", "pescaria de "]),
    "fatos": (["curiosidades sobre ", "fatos curiosos ", "você sabia ", "curiosidades do mundo"],
              ["por que o ", "o que acontece se ", "como funciona ", "a história por trás "]),
    "curiosidades": (["curiosidades sobre ", "fatos curiosos ", "você sabia "],
                     ["por que o ", "o que acontece se ", "como funciona "]),
    "natureza": (["animais curiosidades", "animais selvagens ", "curiosidades sobre animais"],
                 ["por que os animais ", "o animal mais ", "como os animais "]),
    "dorama": (["dorama resumo", "dorama recap", "dorama ", "kdrama resumo"],
               ["dorama em que ", "ela descobriu que ", "ceo se apaixona "]),
    "filme_sem_voz": (["filme resumo", "resumo de filme", "filme recap", "filme completo resumido"],
                      ["filme em que ", "um homem descobre ", "resumo do filme "]),
    "manhwa": (["manhwa recap", "manhwa resumo", "manhwa ", "recap manhwa"],
               ["ele foi humilhado mas ", "ele renasceu como ", "ele voltou no tempo "]),
    "anime": (["anime recap", "resumo anime", "anime ", "anime completo"],
              ["ele foi humilhado mas ", "ele renasceu como ", "ele foi traído "]),
    "jogos": (["jogos curiosidades", "curiosidades de jogos", "gta curiosidades", "minecraft curiosidades"],
              ["o jogo em que ", "por que o jogo ", "o segredo do jogo "]),
    "financas": (["como investir ", "renda extra ", "educação financeira ", "fundos imobiliários "],
                 ["como ganhar dinheiro ", "vale a pena investir em ", "quanto rende "]),
    "negocios": (["como vender mais ", "marketing para ", "automação para ", "atendimento whatsapp "],
                 ["como conseguir clientes ", "como aumentar as vendas ", "como automatizar "]),
    "saude": (["clínica marketing", "como atrair pacientes", "gestão de clínica "],
              ["como lotar a agenda ", "como atrair pacientes para "]),
    "imobiliario": (["corretor de imóveis ", "como vender imóveis", "mercado imobiliário "],
                    ["como captar imóveis ", "como vender imóvel ", "vale a pena comprar imóvel "]),
}


def sugerir(q, sessao, hl="pt", gl="BR"):
    r = sessao.get(URL, params={"client": "firefox", "ds": "yt", "q": q, "hl": hl, "gl": gl}, timeout=15)
    r.raise_for_status()
    r.encoding = "utf-8"
    d = json.loads(r.text)
    return [s.strip() for s in (d[1] if isinstance(d, list) and len(d) > 1 else []) if isinstance(s, str) and s.strip()]


# ruído do autocompletar que não pode virar título: nome de pessoa/canal/obra/jogo/app/time, outra língua, público
# infantil. O que sobra é o jeito genérico de buscar. (1ª coleta, 16/11: "michael jackson", "orochinho", "gino e geno",
# "roube um ovo", "blox fruits", "o diabo veste prada", "nubank", "flamengo", "english", "para crianças"...)
_RUIDO = re.compile(
    r"\b(michael|jackson|orochinho|nilce|robson|gino|geno|bolsonaro|lula|neymar|messi|cristiano|ronaldo|flamengo|"
    r"corinthians|palmeiras|roube um ovo|blox|roblox|minecraft|free fire|fortnite|pokemon|batman|backrooms|prada|"
    r"vorazes|mortais|nubank|inter|mercado pago|mercado livre|shopee|ifood|99 food|tiktok|instagram|facebook|youtube|"
    r"google|asmr|english|ingles|inglês|sus|bl|freitas|edu|ai|hospital|crian[cç]as?|infantil|dormir|canal|"
    r"quando o telefone toca|a li[cç][aã]o|empresses|palace|namoradas|destrui[cç][aã]o final|dia d|obsess[aã]o)\b", re.I)


def _limpas(lista, teto):
    """Sem repetição, sem hashtag/@/link, sem número, sem frase gigante e sem o ruído acima; mantém a ordem (a 1ª é a
    mais buscada)."""
    out = []
    for s in lista:
        s = " ".join(s.split())
        if not (3 <= len(s) <= 60) or any(c in s for c in "#@/") or s.lower() in (x.lower() for x in out):
            continue
        if _RUIDO.search(s) or re.search(r"\d", s):
            continue
        out.append(s)
        if len(out) >= teto:
            break
    return out


def coletar(log=print):
    try:
        velho = json.loads(SAIDA.read_text(encoding="utf-8")).get("nichos") or {}
    except (OSError, ValueError):
        velho = {}
    sessao = requests.Session()
    sessao.headers["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0")
    nichos, falhas = {}, 0
    for nicho, (curtas, frases) in SEMENTES.items():
        pal, pad = [], []
        for grupo, destino in ((curtas, pal), (frases, pad)):
            for q in grupo:
                try:
                    destino += sugerir(q, sessao)
                    falhas = 0
                except Exception as e:  # noqa: BLE001
                    falhas += 1
                    log(f"[palavras] {nicho} '{q}': {type(e).__name__} {str(e)[:80]}")
                    if falhas >= 4:  # o serviço está recusando: para e fica com o que já tinha
                        log("[palavras] 4 falhas seguidas — paro aqui e mantenho o arquivo anterior nos nichos que faltam")
                        for n2, v2 in velho.items():
                            nichos.setdefault(n2, v2)
                        return nichos
                time.sleep(ESPACO_S)
        pal, pad = _limpas(pal, 18), _limpas(pad, 10)
        if len(pal) >= 4:
            nichos[nicho] = {"palavras": pal, "padroes": pad}
        elif nicho in velho:  # veio vazio hoje: não apaga o que já se sabia
            nichos[nicho] = velho[nicho]
        log(f"[palavras] {nicho}: {len(pal)} palavras, {len(pad)} padrões")
    return nichos


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--ver" in sys.argv:
        try:
            d = json.loads(SAIDA.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return print("sem arquivo ainda:", SAIDA)
        print("coletado em", d.get("em"))
        for n, v in d.get("nichos", {}).items():
            print(f"\n{n}: {', '.join(v['palavras'][:10])}\n   como buscam: {' | '.join(v['padroes'][:5])}")
        return None
    nichos = coletar()
    if not nichos:
        return print("[palavras] nada coletado — arquivo não mexido")
    tmp = SAIDA.with_suffix(".tmp")
    tmp.write_text(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "nichos": nichos},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(SAIDA)
    print(f"[palavras] gravado {SAIDA} ({len(nichos)} nichos)")
    return None


if __name__ == "__main__":
    main()
