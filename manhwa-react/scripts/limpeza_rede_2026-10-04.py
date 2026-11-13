"""Limpeza da rede (decisao do dono em 2026-10-04).

1. Privar (nao apagar) videos postados no canal errado / duplicados, e devolver os arquivos para a fila do canal certo
   (o agendador da rede reposta 1 por dia no melhor horario).
2. Privar os videos da epoca do spam (agosto/2026: 'Curiosidades IA - ...', 'Cerebro Digital - ...' etc.) que ainda estao
   publicos nos canais ativos da rede.
Tudo que muda fica em logs/limpeza_2026-10-04.json (para desfazer: tornar publico de novo no Studio).

Uso: python scripts/limpeza_rede_2026-10-04.py            (so lista)
     python scripts/limpeza_rede_2026-10-04.py --executar
"""
import json
import re
import unicodedata
import shutil
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, r"D:\manhwa-react")
from mr.common import load_config, load_json, save_json  # noqa: E402
from mr import publish as PB, rede as RD  # noqa: E402

EXECUTAR = "--executar" in sys.argv
cfg = load_config()
politica, yp = PB._postador(cfg)
creds = {c["id"]: c for c in politica.carregar_creds()}
POSTADOS = Path(cfg["publish"]["posted_dir"])
OUTPUT = Path(cfg["paths"]["output"])
READY = Path(cfg["paths"]["ready"])
LOG = Path(r"D:\manhwa-react\logs\limpeza_2026-10-04.json")

# (video_id, cred do canal onde esta, motivo, arquivo para devolver a fila ou None, slug da fila)
PRIVAR = [
    ("e3erT3rZsos", "KOpyXE9rBy1YirlZ", "3a copia do HD Xbox (original no CartuchoReact)", None, None),
    ("jDxMrrKvOSE", "GG97QQt8lmyv0dDG", "react em portugues no canal frances", "2026_10_03_13_30_21", "cenareact"),
    ("a10g9t8TPRw", "GtuH5ezUK8eBaC60", "react em portugues no canal hindi", "2026_10_03_13_31_46", "cenareact"),
    ("Vx_YuCgrXmM", "nYsAKUb3DbR1QOEm", "react em portugues no canal indonesio", "2026_10_01_11_23_15", "manhwareact"),
    ("kmAt11C8TSo", "7zpNZNll2jlBnQ0J", "react em portugues no canal italiano", "2026_10_01_16_49_02", "manhwareact"),
    ("b5wIgdKVHtw", "TkfzifstYEoG4jKg", "react em portugues no canal russo", "2026_10_01_17_47_36", "manhwareact"),
    ("gyuhRigIDcc", "novo_cartuchoreact", "anime no canal de games", "2026_10_03_13_19_24", "manhwareact"),
    ("qz-a5UNYGns", "novo_forjareact", "anime no canal de forja", "2026_10_03_13_21_35", "manhwareact"),
    ("lOQC4UjOHW4", "novo_mundoquenaoexiste", "Dragon Ball no canal de coisas impossiveis/IA", "2026_10_03_13_23_06", "manhwareact"),
    ("WL4v_ZND6Kk", "novo_dicasfinanceirasdaia", "anime no canal de financas", "2026_10_03_13_25_59", "manhwareact"),
    ("svHjEAvkatY", "novo_codigo_inteligente_n7j", "copia do HD Xbox (original no CartuchoReact) no canal de historias", None, None),
    ("UHDBY9N7o8w", "novo_codigo_inteligente_n7j", "piso liquido (inventos) no canal de historias", "2026_10_01_16_19_51", "inventoreact"),
    ("HXGj-a3q3v4", "novo_cartuchoreact", "curiosidade de cultura (inventos) no canal de games", "2026_10_01_17_49_09", "inventoreact"),
    ("hWB7SdCP6GI", "novo_mundoquenaoexiste", "copia da espada de mola (original no ForjaReact)", None, None),
    ("kIVKFUzxUvg", "novo_ia_agora_h3n", "2a copia do 'alcool da gasolina' no mesmo canal (fica a de 03/10)", None, None),
]


def uploads(cred, maximo=200):
    ch = RD._req(yp, cred, "https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true")["items"][0]
    pl = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    out, tok = [], ""
    while len(out) < maximo:
        d = RD._req(yp, cred, "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,status&maxResults=50"
                    f"&playlistId={pl}" + (f"&pageToken={tok}" if tok else ""))
        out += d.get("items", [])
        tok = d.get("nextPageToken")
        if not tok:
            break
    return out


def devolver(stem, slug, video_id, motivo):
    """Copia o Short de volta para shorts/<slug>/ (de _postados ou de output/) e libera para repostar."""
    dst = READY / slug
    dst.mkdir(parents=True, exist_ok=True)
    origem = next((p.parent for p in POSTADOS.glob(f"*/{stem}.mp4")), None) or (OUTPUT / stem)
    for nome in (f"{stem}.mp4", f"{stem}.postar.json", f"{stem}_meta.txt", f"{stem}_thumb.jpg"):
        src = origem / nome
        if src.exists() and not (dst / nome).exists():
            shutil.copy2(src, dst / nome)
    pj = dst / f"{stem}.postar.json"
    if pj.exists():
        d = load_json(pj)
        d.pop("postado", None)
        d["canal_slug"] = slug
        d["reaberto"] = {"video_antigo": video_id, "motivo": motivo, "em": "2026-10-04"}
        save_json(d, pj)
    mp4 = dst / f"{stem}.mp4"
    if mp4.exists():
        politica.marcar_aprovacao(mp4, "aprovado", f"ja tinha sido postado ({video_id}); reaberto para o canal certo")
    RD.reabrir(cfg, stem, video_id, motivo)
    return mp4.exists()


feito = load_json(LOG) if LOG.exists() else {"privados": {}, "devolvidos": {}, "erros": {}}
plano = [(v, c, m, s, sl) for v, c, m, s, sl in PRIVAR]

# epoca do spam (agosto/2026), ainda publicos nos canais ativos da rede:
#  - lote generico de IA (Curiosidades IA, Cerebro Digital, Cassetadas, Aulas IA, Ilusoes, Humor de IA, ETs...) -> privar
#  - Animescomia / inovaremanhwabr: os recaps de manhwa SAO o conteudo do canal -> ficam; so sai a copia repetida
#    (mesmo titulo 2+ vezes: fica a mais antiga) e o que e de outro idioma/tema
#  - demais canais: tudo de agosto era o lote generico -> privar
SPAM = re.compile(r"^(curiosidades ia|cerebro digital|cassetadas ia|aulas ia|ilusoes|humor de ia)|\bets?\b.*(roubam|tentou)|\bo et\b|book of ruth", re.I)
CONTEUDO_PROPRIO = {"animescomia", "inovaremanhwabr"}


def chave_titulo(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", "", t).strip()[:40]


for canal in RD.canais(cfg, politica):
    try:
        lista = uploads(canal["cred"])
    except urllib.error.HTTPError as e:
        print(f"!! {canal['nome']}: nao listou ({e.code})")
        continue
    vistos = set()
    for it in sorted(lista, key=lambda x: x["snippet"].get("publishedAt", "")):  # mais antigo primeiro
        sn, st = it["snippet"], it.get("status", {})
        vid = sn["resourceId"]["videoId"]
        if not sn.get("publishedAt", "").startswith("2026-08") or st.get("privacyStatus") != "public" or vid in vistos:
            continue
        vistos.add(vid)
        k = chave_titulo(sn["title"])
        repetido = k in vistos
        vistos.add(k)
        titulo_sem_acento = unicodedata.normalize("NFKD", sn["title"]).encode("ascii", "ignore").decode()
        if SPAM.search(titulo_sem_acento):
            motivo = "lote generico de IA (08/2026)"
        elif repetido:
            motivo = "copia repetida (08/2026)"
        elif canal["slug"] in CONTEUDO_PROPRIO:
            continue
        else:
            motivo = "lote generico de IA (08/2026)"
        plano.append((vid, canal["cred"]["id"], f"{motivo}: {sn['title'][:50]}", None, None))

print(f"{len(plano)} video(s) para privar ({'EXECUTANDO' if EXECUTAR else 'so listando'})\n")
for vid, cid, motivo, stem, slug in plano:
    nome = creds[cid]["nome"].strip()
    if vid in feito["privados"]:
        print(f"  ja feito  {vid} {nome}")
        continue
    print(f"  {vid} [{nome}] {motivo}" + (f"  -> volta para {slug}" if slug else ""))
    if not EXECUTAR:
        continue
    try:
        r = RD.privar(yp, creds[cid], vid)
        feito["privados"][vid] = {"canal": nome, "cred": cid, "motivo": motivo, "resultado": r}
        if stem:
            feito["devolvidos"][stem] = {"slug": slug, "video_antigo": vid, "ok": devolver(stem, slug, vid, motivo)}
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:200]
        feito["erros"][vid] = f"{e.code} {msg}"
        print(f"    ERRO {e.code}: {msg}")
        if "quota" in msg.lower():
            print("    cota da API do projeto acabou - rode de novo amanha (continua de onde parou)")
            save_json(feito, LOG)
            break
    save_json(feito, LOG)

if EXECUTAR:
    print(f"\nprivados: {len(feito['privados'])} | devolvidos a fila: {len(feito['devolvidos'])} | erros: {len(feito['erros'])}")
