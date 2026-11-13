import json, shutil, time, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path
f = Path(r"D:\recapd-ambientes\producao\config\parceiro.json")
# 09/11 dona: autorização recebida de todos os canais de CANAIS_DARK_PARA_CONTATO.md (seções A e B)
NOVOS = [
 ("fatosdesconhecidos", "fatos"), ("tinocandotv", "fatos"), ("Tio_San", "anime"), ("spotniks", "financas"),
 ("Batimaanimes", "anime"), ("NodeHatVencendoFilmes", "filme_sem_voz"), ("DerrotandoFilmes", "filme_sem_voz"),
 ("OssosPerdidos", "fatos"), ("FocanaHistória", "fatos"), ("Clark69", "anime"), ("GuilhermeAnalisa", "fatos"),
 ("UniversoNarrado", "fatos"), ("SOLUCIONANDOFILMES", "filme_sem_voz"), ("DrakeZando", "filme_sem_voz"),
 ("passoapassoempreendedoroficial", "financas"), ("ChapéusdePalha", "anime"), ("skyroxalex", "fatos"),
 ("HoradaHistóriaConversaToon", "anime"), ("ManhwaDoKawa", "manhwa"), ("filmesnostalgicos", "filme_sem_voz"),
 ("liandracarla26", "fatos"), ("curiosomercado", "financas"), ("Animenokokoro", "anime"),
 ("buyandholdbrasil", "financas"), ("Historiadosgrandes", "financas"), ("SubsoloGeek", "anime"),
 ("Orff_", "dorama"), ("desvendandofilme", "filme_sem_voz"), ("RubyRomances", "manhwa"),
 ("resumodetela", "filme_sem_voz"), ("AbreviandoDoramas", "dorama"), ("rebobinarecap", "anime"),
 ("RecapandoManhwa", "manhwa"), ("DIÁRIODOSPESADELOS", "fatos"),
 ("zackdfilms", "fatos"), ("dailydoseofinternet", "fatos"), ("beamazed", "fatos"), ("chills", "fatos"),
 ("coldfusion", "financas"), ("nukestop5", "fatos"), ("slappedham", "fatos"), ("kpophmkshorts", "dorama"),
 ("top5s", "fatos"), ("score90", "esportes"), ("magnatesmedia", "financas"), ("howmoneyworks", "financas"),
 ("storyrecapped", "filme_sem_voz"), ("bingecentral", "filme_sem_voz"), ("footballshortsrk67", "esportes"),
 ("danielccmovie", "filme_sem_voz"), ("gtashorttv", "jogos"), ("BTNDocumentaries", "fatos"),
]
DUVIDA = {"Orff_", "DIÁRIODOSPESADELOS", "footballshortsrk67", "FocanaHistória", "ChapéusdePalha",
          "HoradaHistóriaConversaToon", "top5s"}


def existe(h):  # 1 GET por handle duvidoso, espaçado (sem rajada)
    url = "https://www.youtube.com/@" + urllib.parse.quote(h)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "pt-BR"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


shutil.copy2(f, f.with_name(f"parceiro.json.bkp_{datetime.now():%Y%m%d_%H%M}_dark"))
j = json.loads(f.read_text(encoding="utf-8"))
tem = {x.get("nome", "").lower() for x in j["fontes"]} | {x.get("url", "").lower() for x in j["fontes"]}
add, pulou = [], []
for h, tipo in NOVOS:
    url = f"https://www.youtube.com/@{h}/shorts"
    if h.lower() in tem or url.lower() in tem:
        pulou.append(h + " (já tinha)"); continue
    if h in DUVIDA:
        ok = existe(h); time.sleep(4)
        if not ok:
            pulou.append(h + " (handle não existe)"); continue
    j["fontes"].append({"url": url, "tipo": tipo, "nome": h, "cobertura": "auto",
                        "_obs": "09/11 dona: autorizado (CANAIS_DARK_PARA_CONTATO.md)"})
    add.append(h)
f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
json.loads(f.read_text(encoding="utf-8"))
print("adicionados", len(add), "| total fontes", len(j["fontes"]))
print("pulados:", pulou)
