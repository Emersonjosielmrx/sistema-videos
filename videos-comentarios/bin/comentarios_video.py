# -*- coding: utf-8 -*-
"""comentarios_video.py — Shorts de comentários engraçados falados por personagens com voz clonada.

Cada comentário vira uma fala de um personagem (Seu Madruga, Girafales, Quico...) no jeito dele (roteiro pela IA a
partir do linguagem_v2.json quando a fala não vem escrita): base edge Francisca ou Kokoro -> RVC (voz_clonada.py lote).
Visual: cartão do comentário no topo, legenda "adesivos" do montagem_ms.py (ms-energy), figurinha (meme do catálogo do
recapd) e SFX escolhidos pela IA para combinar com a fala, zoom-soco + tremida + flash a cada fala.
Áudio: falas niveladas, trilha que abaixa sob a voz, SFX na palavra da piada, loudnorm final -14 LUFS.

    python bin/comentarios_video.py --config config/video_001.json
"""
import asyncio
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import os  # noqa: E402

NUVEM = os.name != "nt"  # Kaggle (colab_traduz troca D:\ por <RAIZ_WIN>/D/ em Path/open; strings em sys.path/subprocess não)
sys.path.append(str(Path(r"D:\ms-energy\bin")))
sys.path.append(str(Path(r"D:\hipercool-videos\bin")))
import montagem_ms as ms  # noqa: E402

# COMUM (dona 02/11): transições gl-transitions na troca de comentário. O moderngl só existe no venv central: o
# site-packages dele entra no FIM do sys.path (o que este Python já tem continua vindo dele). Kaggle: segue sem.
sys.path.append(r"D:\hipercool-materiais\python\venv\Lib\site-packages")
try:
    import realce_visual  # noqa: E402  (cópia em D:\hipercool-videos\bin)
except Exception:  # noqa: BLE001
    realce_visual = None
GL_TRANS_CHANCE = float(os.environ.get("COMENT_GL_TRANS_CHANCE", "0.6"))

FFMPEG = "ffmpeg" if NUVEM else r"D:\hipercool-materiais\bin\ffmpeg.exe"
FFPROBE = "ffprobe" if NUVEM else r"D:\hipercool-materiais\bin\ffprobe.exe"
PY_VOZES = r"D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe"
VOZ_CLONADA = r"D:\hipercool-materiais\bin\voz_clonada.py"
VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
SFX_TRANSICAO = Path(r"D:\tmp_logs\sons_novos\cortados")
SFX_MEMES = Path(r"D:\recapd-ambientes\producao\workspace\assets\sfx_memes")
SFX_CATEGORIAS = SFX_MEMES.parent / "sfx_memes_categorized.json"
MEMES_CATALOGO = Path(r"D:\recapd-ambientes\producao\config\memes_catalogo.json")
FONTES = Path(r"D:\hipercool-materiais\assets\fonts")
PROJETO = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
TOPO_H = 400  # faixa do título + cartão do comentário (cobre o print que vem no vídeo de origem)
PAUSA = 0.18
SEM_JANELA = 0x08000000

ms.FORTES = {"vó", "vovó", "avó", "músculo", "personal", "socorro", "zumbi", "apocalipse", "errou", "aluguel",
             "aparelho", "academia", "morto", "vivo", "profissão", "loco", "dedicação", "errado", "querendo"}


def rodar(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                          creationflags=0 if NUVEM else SEM_JANELA, **kw)


def duracao(p):
    r = rodar([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p])
    return float(r.stdout.strip())


def _norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def _json_da_resposta(txt):
    if isinstance(txt, dict):
        txt = txt.get("text") or json.dumps(txt)
    m = re.search(r"\[.*\]", txt, re.S)
    return json.loads(m.group(0)) if m else None


GATEWAY_SECRET = Path(r"D:\hipercool-videos\secrets\claude_proxy.json")
# 07/11: agy/antigravity respondem 200 com "This version of Antigravity is no longer supported" (texto, não erro) e o
# roteiro falhava "IA não devolveu JSON" — gemini 3.5 (AI Studio pelo OmniRoute, testado com imagem) na frente
GATEWAY_MODELOS = ["gemini/gemini-3.5-flash", "agy/gemini-3.8-flash-high", "antigravity/gemini-3-flash"]


def _gateway(prompt, imagens):
    import base64
    import urllib.request
    c = json.loads(GATEWAY_SECRET.read_text(encoding="utf-8"))
    conteudo = [{"type": "text", "text": prompt}]
    for i, b in enumerate(imagens or [], 1):
        conteudo += [{"type": "text", "text": f"Painel {i}:"},
                     {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()}}]
    # 07/11: o gemini/ do OmniRoute gira entre chaves do AI Studio — umas dão 403 (sem tier grátis), outras 429
    # (esfriando ~50 s): repetir o mesmo modelo 3x com pausa pega uma chave boa
    for modelo in [m for m in GATEWAY_MODELOS for _ in range(3 if m.startswith("gemini/") else 1)]:
        corpo = {"model": modelo, "max_tokens": 4000, "temperature": 0.7,
                 "messages": [{"role": "user", "content": conteudo}]}
        req = urllib.request.Request(c["base_url"].rstrip("/") + "/v1/chat/completions", data=json.dumps(corpo).encode(),
                                     headers={"Content-Type": "application/json",
                                              "Authorization": "Bearer " + c["auth_token"]})
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                m = json.loads(r.read())["choices"][0]["message"]["content"]
            txt = m if isinstance(m, str) else "".join(p.get("text", "") for p in m)
            if "Antigravity is no longer supported" in txt[:200]:
                print(f"[ia] gateway {modelo}: versão do Antigravity fora — próximo", flush=True)
                continue
            if txt.strip():
                return txt
        except Exception as e:  # noqa: BLE001
            print(f"[ia] gateway {modelo}: {str(e)[:120]}", flush=True)
            if modelo.startswith("gemini/") and ("403" in str(e) or "429" in str(e)):
                import time
                time.sleep(25)
    return None


def ia(prompt, imagens=None):
    """Gemini direto (chaves do hipercool); vazio/429 -> gateway OmniRoute (Gemini 3.8 do Antigravity)."""
    try:
        import gemini_llm
        r = gemini_llm.generate_from_images(imagens, prompt) if imagens else \
            gemini_llm.generate_text(prompt, temperature=0.9)
        if isinstance(r, dict):
            r = r.get("text")
        if r and str(r).strip():
            return r
    except Exception as e:  # noqa: BLE001
        print(f"[ia] gemini direto: {str(e)[:120]}", flush=True)
    r = _gateway(prompt, imagens)
    if not r:
        raise RuntimeError("IA sem resposta (Gemini direto e gateway)")
    return r


# ───────── roteiro: comentário -> fala no jeito do personagem ─────────
def falavel(comentario):
    """Comentário como o personagem LÊ em voz alta: sem emoji, sem 'kkkk' (o TTS soletra), espaços limpos."""
    t = re.sub(r"[^\w\s,.!?;:()'\"%$@#&/+\-ÀÁÂÃÉÊÍÓÔÕÚÇàáâãéêíóôõúç]", " ", comentario)
    t = re.sub(r"\b[kK]{2,}\w*\b|\b(rs){2,}\b|\bha(ha)+\b", " ", t)
    return re.sub(r"\s+", " ", t).strip(" ,") or comentario


# 02/11: a IA (Gemini 3 Flash) punha o "Errou/Ô loco, meu" do Faustão na Ludmilla, o "Ma oê" do Silvio no Patolino...
# Bordão famoso -> dono (voz). Reação com bordão de outro = refeita; os bordões do linguagem_v2 de cada voz entram também.
BORDOES_DONO = {"errou": "faustao", "o loco": "faustao", "ô loco": "faustao", "oh loco": "faustao", "ma oe": "silvio_santos",
                "mah oue": "silvio_santos", "ma oee": "silvio_santos", "quem quer dinheiro": "silvio_santos",
                "hohoho": "mestre_kame", "ho ho ho": "mestre_kame", "ta ta ta": "professor_girafales",
                "sem querer querendo": "chaves_chapolin", "nao contavam com minha astucia": "chapolin_colorado",
                "gentalha": "quico", "eu gosto de dinheiro": "seu_sirigueijo_peter_griffin", "boa noite": "cid_moreira",
                "isso isso isso": "chaves_chapolin", "pi pi pi": "chiquinha", "humilde presente": "professor_girafales",
                "olha o vidro": "galvao_bueno", "e do brasil": "galvao_bueno", "haja coracao": "galvao_bueno"}


def bordao_alheio(voz, reacao):
    r = " " + _norm(reacao) + " "
    for b, dono in BORDOES_DONO.items():
        if f" {b} " in r and dono != voz and not (dono == "chaves_chapolin" and voz == "chapolin_colorado"):
            return True
    return False


def roteirizar(falas, cache):
    """01/11 (dona: "o central do projeto é LER os comentários"): o personagem lê o comentário COMO ESTÁ ESCRITO e só
    depois reage curto no jeito dele (bordão). A IA escreve só a reação; texto = comentário lido + reação."""
    faltam = [f for f in falas if not f.get("texto")]
    if not faltam:
        return
    prontos = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    precisa = [f for f in faltam if f["comentario"] not in prontos]
    if precisa:
        blocos = []
        for i, f in enumerate(precisa):
            ling = VOZES / f["voz"] / "linguagem_v2.json"
            j = json.loads(ling.read_text(encoding="utf-8")) if ling.exists() else {}
            blocos.append(f"{i}. PERSONAGEM {f['nome']} — {j.get('resumo', '')} Tom: {', '.join(j.get('tom', []))}. "
                          f"Bordões: {'; '.join(j.get('bordoes', []))}. Frases reais: "
                          f"{'; '.join(j.get('frases_reais', [])[:4])}\n   COMENTÁRIO (ele acabou de ler): {f['comentario']}")
        prompt = ("Short de humor brasileiro: cada personagem famoso LÊ em voz alta um comentário engraçado de um vídeo "
                  "viral e logo depois solta uma REAÇÃO curta. Regras da reação:\n"
                  "1. Tem que RESPONDER AO COMENTÁRIO que ele leu (concordar, zoar, completar a piada) — nada genérico.\n"
                  "2. No jeito DAQUELE personagem: use o tom e, se couber, UM bordão DA LISTA DELE. NUNCA use bordão ou "
                  "frase famosa de OUTRO personagem ou pessoa (ex.: 'Ô loco, meu' e 'Errou' só o Faustão; 'Ma oê' só o "
                  "Silvio Santos; 'Tá tá tá' só o Girafales).\n"
                  "3. De 4 a 10 palavras, português falado, sem emoji, sem aspas, sem rubrica, sem repetir o comentário.\n"
                  f"Cena do vídeo: {falas[0].get('cena', '')}\n\n" + "\n".join(blocos) +
                  '\n\nResponda SÓ JSON: [{"i": 0, "reacao": "..."}, ...]')
        for tentativa in range(2):
            for r in _json_da_resposta(ia(prompt)) or []:
                try:
                    f = precisa[int(r["i"])]
                    reacao = r["reacao"].strip()
                except (KeyError, ValueError, IndexError, AttributeError):
                    continue
                if not bordao_alheio(f["voz"], reacao):
                    prontos[f["comentario"]] = reacao
            precisa = [f for f in precisa if f["comentario"] not in prontos]
            if not precisa:
                break
            blocos = [b for b in blocos if any(f"COMENTÁRIO (ele acabou de ler): {f['comentario']}" in b for f in precisa)]
            prompt = prompt.split("\n\n")[0] + "\n\nATENÇÃO: a tentativa anterior usou bordão de OUTRO personagem.\n\n" + \
                "\n".join(f"{i}. " + b.split(". ", 1)[1] for i, b in enumerate(blocos)) + \
                '\n\nResponda SÓ JSON: [{"i": 0, "reacao": "..."}, ...]'
        for f in precisa:  # insistiu no bordão alheio: usa um bordão DELE (ou fica só a leitura)
            ling = VOZES / f["voz"] / "linguagem_v2.json"
            proprios = json.loads(ling.read_text(encoding="utf-8")).get("bordoes", []) if ling.exists() else []
            if proprios:
                prontos[f["comentario"]] = random.choice(proprios).rstrip(". ")
        cache.write_text(json.dumps(prontos, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in faltam:
        lido = falavel(f["comentario"])
        f["reacao"] = prontos.get(f["comentario"], "")
        f["n_lido"] = len(lido.split())
        f["texto"] = f"{lido.rstrip('.!?')}... {f['reacao']}" if f["reacao"] else lido


# ───────── vozes clonadas ─────────
async def _edge(texto, mp3, rate):
    import edge_tts
    proxy = None
    if NUVEM:  # o edge bloqueia o IP do Kaggle depois de ~60 frases (recapd 26/10): sempre pelo Webshare rotativo
        arq = Path(r"D:\recapd-ambientes\producao\secrets\proxies.txt")
        if arq.exists():
            linhas = [x.strip() for x in arq.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")]
            proxy = random.choice(linhas) if linhas else None
            proxy = proxy if not proxy or proxy.startswith("http") else "http://" + proxy
    com = edge_tts.Communicate(texto, "pt-BR-FranciscaNeural", rate=rate, boundary="WordBoundary", proxy=proxy)
    palavras = []
    with open(mp3, "wb") as f:
        async for c in com.stream():
            if c["type"] == "audio":
                f.write(c["data"])
            elif c["type"] == "WordBoundary":
                ini = c["offset"] / 1e7
                palavras.append([round(ini, 3), round(ini + c["duration"] / 1e7, 3), c["text"]])
    return palavras


def base_do_personagem(voz):
    info = json.loads((VOZES / voz / "personagem.json").read_text(encoding="utf-8"))
    return "francisca" if "francisca" in info.get("bases", []) else "kokoro"


def gerar_vozes(falas, tmp):
    """Cada fala na voz do personagem (cache por texto: só refaz a fala que mudou). Devolve wav + tempo das palavras."""
    por_voz = {}
    for i, f in enumerate(falas):
        chave = hashlib.md5(f"{f['voz']}|{f['texto']}".encode("utf-8")).hexdigest()[:8]
        f["wav"] = str(tmp / f"fala_{i:02d}_{f['voz']}_{chave}.wav")
        f["palavras_json"] = f["wav"] + ".palavras.json"
        if Path(f["wav"]).exists() and Path(f["palavras_json"]).exists():
            continue
        if base_do_personagem(f["voz"]) == "francisca":
            mp3 = tmp / f"base_{i:02d}.mp3"
            pal = asyncio.run(_edge(f["texto"], mp3, f.get("rate", "+6%")))
            base_wav = tmp / f"base_{i:02d}.wav"
            rodar([FFMPEG, "-v", "error", "-y", "-i", mp3, "-ac", "1", base_wav])
            Path(f["palavras_json"]).write_text(json.dumps(pal, ensure_ascii=False), encoding="utf-8")
            item = {"saida": f["wav"], "tom_base": "2_edge_francisca", "entrada": str(base_wav)}
        else:
            item = {"saida": f["wav"], "tom_base": "1_kokoro", "texto": f["texto"], "velocidade": f.get("velocidade", 1.05)}
        por_voz.setdefault(f["voz"], []).append(item)

    for voz, itens in por_voz.items():
        lista = tmp / f"lote_{voz}.json"
        lista.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
        print(f"[voz] {voz}: {len(itens)} fala(s)...", flush=True)
        if NUVEM:  # Kaggle com GPU: o mesmo lote, Applio no ambiente próprio do trabalhador
            r = rodar([os.environ.get("VOZES_PY_NUVEM", sys.executable),
                       Path(r"D:\recapd-ambientes\producao\bin\voz_clonada_nuvem.py"), "lote", voz, lista])
        else:
            r = rodar([PY_VOZES, VOZ_CLONADA, "lote", voz, lista])
        if r.returncode != 0:
            raise SystemExit(f"[ERRO] voz {voz}:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")

    for f in falas:
        if not Path(f["wav"]).exists():
            raise SystemExit(f"[ERRO] fala sem áudio: {f['wav']}")
        kokoro_words = Path(f["wav"] + ".words.json")
        if not Path(f["palavras_json"]).exists():
            if kokoro_words.exists():
                shutil.copy(kokoro_words, f["palavras_json"])
            else:  # sem tempo por palavra: divide a duração igualmente
                ws = f["texto"].split()
                d = duracao(f["wav"]) / len(ws)
                Path(f["palavras_json"]).write_text(json.dumps([[k * d, (k + 1) * d, w] for k, w in enumerate(ws)],
                                                               ensure_ascii=False), encoding="utf-8")
        f["palavras"] = json.loads(Path(f["palavras_json"]).read_text(encoding="utf-8"))
        n = f.get("n_lido") or len(f["palavras"])
        f["t_reacao"] = f["palavras"][n][0] if n < len(f["palavras"]) else f["palavras"][-1][1]
        # a próxima fala entra logo depois da última palavra (corta o silêncio do fim do arquivo)
        f["dur"] = min(duracao(f["wav"]), f["palavras"][-1][1] + 0.25)


# ───────── figurinha + SFX que combinam com a fala ─────────
def _catalogos():
    memes = []
    for m in json.loads(MEMES_CATALOGO.read_text(encoding="utf-8")).values():
        if m.get("ok") and m.get("kind") == "image" and Path(m["file"]).exists():
            memes.append(m)
    cats = json.loads(SFX_CATEGORIAS.read_text(encoding="utf-8")).get("files", {})
    sfx = sorted(n for n, c in cats.items() if c in ("comedia", "impacto") and (SFX_MEMES / n).exists()
                 and not re.search(r"music|song|m[uú]sica|background|completo|frases|reverb|eco\b|echo", n, re.I))
    return memes, sfx


def escolher_efeitos_ia(falas, cache):
    """Figurinha + SFX + palavra da piada de cada fala pela IA (só pelo texto; no PC). Grava no cache (efeitos.json),
    que vai junto no pedido do Kaggle — lá o escolher_efeitos só encaixa no tempo, sem IA nem catálogos."""
    salvo = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    falta = [i for i, f in enumerate(falas) if f["texto"] not in salvo]
    if falta:
        memes, sfx = _catalogos()
        lista_m = "\n".join(f"M{k}: {m['desc']} ({', '.join(m.get('tags', []))})" for k, m in enumerate(memes))
        lista_s = "\n".join(f"S{k}: {Path(n).stem}" for k, n in enumerate(sfx))
        lista_f = "\n".join(f"{i}. {falas[i]['nome']}: {falas[i]['texto']}" for i in falta)
        prompt = ("Short de humor: cada fala abaixo ganha UMA figurinha na tela (meme em imagem) e UM efeito sonoro "
                  "que combinem com o que está sendo dito (a piada, a emoção, a ação). Não repita figurinha nem efeito. "
                  "'palavra' = a palavra da fala onde o efeito sonoro bate (a da piada).\n\nFALAS:\n" + lista_f +
                  "\n\nFIGURINHAS:\n" + lista_m + "\n\nEFEITOS SONOROS:\n" + lista_s +
                  '\n\nResponda SÓ JSON: [{"i": 0, "figurinha": "M12", "sfx": "S40", "palavra": "..."}, ...]')
        try:
            res = _json_da_resposta(ia(prompt)) or []
        except Exception as e:  # noqa: BLE001
            print(f"[ia] escolha falhou ({e}); vai por palavras", flush=True)
            res = []
        usados_m, usados_s = set(), set()
        for r in res:
            try:
                i = int(r["i"])
                km, ks = int(str(r["figurinha"]).lstrip("Mm")), int(str(r["sfx"]).lstrip("Ss"))
                salvo[falas[i]["texto"]] = {"figurinha": memes[km]["file"], "sfx": str(SFX_MEMES / sfx[ks]),
                                            "palavra": r.get("palavra", ""), "desc": memes[km]["desc"]}
                usados_m.add(km)
                usados_s.add(ks)
            except (KeyError, ValueError, IndexError, TypeError):
                continue
        for i in falta:  # reserva: maior número de palavras em comum com a descrição/nome
            if falas[i]["texto"] in salvo:
                continue
            pal = set(_norm(falas[i]["texto"]).split())
            km = max((k for k in range(len(memes)) if k not in usados_m),
                     key=lambda k: len(pal & set(_norm(memes[k]["desc"] + " " + " ".join(memes[k].get("tags", []))).split())))
            ks = random.choice([k for k in range(len(sfx)) if k not in usados_s])
            usados_m.add(km)
            usados_s.add(ks)
            salvo[falas[i]["texto"]] = {"figurinha": memes[km]["file"], "sfx": str(SFX_MEMES / sfx[ks]), "palavra": "",
                                        "desc": memes[km]["desc"]}
        cache.write_text(json.dumps(salvo, ensure_ascii=False, indent=1), encoding="utf-8")
    return salvo


def escolher_efeitos(falas, cache):
    salvo = escolher_efeitos_ia(falas, cache)
    for f in falas:
        f.update(salvo[f["texto"]])
        alvo = _norm(f.get("palavra", ""))
        t = f["palavras"][-1][0]
        for s, e, w in f["palavras"]:
            if alvo and _norm(w) == alvo:
                t = s
        f["t_sfx"] = t
        print(f"[efeito] {f['nome']}: figurinha '{f['desc'][:50]}' | sfx {Path(f['sfx']).stem} @ '{f.get('palavra')}'",
              flush=True)


def png_figurinha(origem, destino, n, escala=1.0):
    """Meme como figurinha: recorte que cabe em 380 px, borda branca grossa, sombra e leve giro."""
    im = Image.open(origem)
    im.seek(0)
    im = im.convert("RGBA")
    lado = int(380 * escala)
    im.thumbnail((lado, lado), Image.LANCZOS)
    borda = 14
    pad = borda + 24
    w, h = im.width + 2 * pad, im.height + 2 * pad
    alfa = Image.new("L", (w, h), 0)
    alfa.paste(im.getchannel("A"), (pad, pad))
    contorno = alfa.point(lambda a: 255 if a > 40 else 0).filter(ImageFilter.MaxFilter(borda * 2 + 1))
    sombra = contorno.filter(ImageFilter.GaussianBlur(10)).point(lambda a: int(a * 0.55))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(Image.composite(Image.new("RGBA", (w, h), (0, 0, 0, 255)), out, sombra), (0, 0))
    out = Image.alpha_composite(out.transform(out.size, Image.AFFINE, (1, 0, -6, 0, 1, -8)),
                                Image.composite(Image.new("RGBA", (w, h), (255, 255, 255, 255)),
                                                Image.new("RGBA", (w, h), (0, 0, 0, 0)), contorno))
    out.alpha_composite(im, (pad, pad))
    out = out.rotate((-9, 7, -5, 10, -7, 6)[n % 6], resample=Image.BICUBIC, expand=True)
    out.save(destino)
    return out.size


# ───────── visual ─────────
def _fonte(nome, tam):
    return ImageFont.truetype(str(FONTES / nome), tam)


def _quebrar(d, texto, fonte, largura):
    linhas, cur = [], ""
    for w in texto.split():
        t = f"{cur} {w}".strip()
        if cur and d.textlength(t, font=fonte) > largura:
            linhas.append(cur)
            cur = w
        else:
            cur = t
    return linhas + ([cur] if cur else [])


CORES_AVATAR = [(255, 87, 34), (33, 150, 243), (156, 39, 176), (76, 175, 80), (255, 193, 7), (233, 30, 99),
                (0, 188, 212)]


_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍⃣]+")


def png_faixa(titulo, destino):
    """Faixa escura do topo com o título (fixa o vídeo todo; cobre o print que vem no vídeo de origem).
    Devolve o y onde o cartão do comentário começa."""
    im = Image.new("RGBA", (W, TOPO_H), (18, 18, 22, 255))
    d = ImageDraw.Draw(im)
    ft = _fonte("Montserrat-Black.ttf", 50)
    y = 24
    # 02/11 revisão: a Montserrat não tem emoji — o "💀" do título saía como □ na faixa de TODO vídeo (título do
    # YouTube continua com emoji; só a faixa desenhada perde)
    titulo = re.sub(r"\s{2,}", " ", _EMOJI.sub("", titulo)).strip()
    for ln in _quebrar(d, titulo.upper(), ft, W - 80)[:2]:
        d.text(((W - d.textlength(ln, font=ft)) / 2, y), ln, font=ft, fill=(255, 214, 10), stroke_width=3,
               stroke_fill=(0, 0, 0))
        y += 60
    im.save(destino)
    return y + 14


def png_cartao(fala, n, destino, alto):
    """Cartão do comentário (estilo Instagram) com o personagem que fala; entra animado como nos comerciais."""
    larg = W - 48
    im = Image.new("RGBA", (larg + 24, alto + 24), (0, 0, 0, 0))
    sombra = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((8, 12, larg + 8, alto + 12), radius=28, fill=(0, 0, 0, 130))
    im = Image.alpha_composite(im, sombra.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, larg, alto), radius=28, fill=(255, 255, 255, 255))
    cor = CORES_AVATAR[n % len(CORES_AVATAR)]
    d.ellipse((24, 24, 124, 124), fill=cor)
    d.text((74, 74), fala["nome"][0].upper(), font=_fonte("Montserrat-Black.ttf", 52), fill="white", anchor="mm")
    fn = _fonte("Montserrat-ExtraBold.ttf", 34)
    nome = fala["nome"].lower().replace(" ", "_")
    d.text((148, 22), nome, font=fn, fill=(20, 20, 20))
    d.text((156 + d.textlength(nome, font=fn), 24), "  agora", font=_fonte("Montserrat-ExtraBold.ttf", 28),
           fill=(140, 140, 140))
    fc = _fonte("Montserrat-ExtraBold.ttf", 33)
    yy = 70
    for ln in _quebrar(d, fala["comentario"], fc, larg - 148 - 110)[:3]:
        d.text((148, yy), ln, font=fc, fill=(35, 35, 35))
        yy += 42
    d.text((larg - 56, 50), "♥", font=ImageFont.truetype(str(Path(r"C:\Windows\Fonts\seguisym.ttf")), 44),
           fill=(237, 73, 86), anchor="mm")
    d.text((larg - 56, 96), f"{random.Random(fala['comentario']).randint(300, 9000):,}".replace(",", "."),
           font=_fonte("Montserrat-ExtraBold.ttf", 28), fill=(120, 120, 120), anchor="mm")
    im.save(destino)


def filtro_movimento(falas):
    """Zoom-soco (+7% que volta em ~0,4 s) com tremida curta a cada fala nova, sobre um empurrão lento contínuo."""
    socos = "+".join(f"0.07*exp(-7*(it-{f['ini']:.2f}))*gte(it,{f['ini']:.2f})" for f in falas)
    tremor = "+".join(f"14*sin(it*70)*exp(-12*(it-{f['ini']:.2f}))*gte(it,{f['ini']:.2f})" for f in falas)
    z = f"1.03+0.0015*it+{socos}"
    return (f"scale=1620:2880,zoompan=z='{z}':d=1:fps=30:s={W}x{H}:"
            f"x='iw/2-(iw/zoom/2)+({tremor})':y='ih/2-(ih/zoom/2)'")


FAIXAS_PRINTS = {"topo": (TOPO_H, int(H * 0.47)), "meio": (int(H * 0.30), int(H * 0.66)),
                 "baixo": (int(H * 0.60), H)}


def _abaixo_do_cartao(png):
    """Adesivo que subiu até o cartão do comentário (topo) desce o necessário."""
    im = Image.open(png).convert("RGBA")
    bb = im.getbbox()
    if bb and bb[1] < TOPO_H + 12:
        desce = TOPO_H + 12 - bb[1]
        novo = Image.new("RGBA", im.size, (0, 0, 0, 0))
        novo.alpha_composite(im.crop((0, 0, W, H - desce)), (0, desce))
        novo.save(png)


def base_sincronizada(video, falas, dur_final, tmp):
    """Enquanto o personagem lê um comentário, passa o trecho do vídeo de origem em que o print DELE aparece (t_src,
    da visão): do aparecimento até o próximo comentário, esticado até 2x ou segurando o último quadro se a fala for
    mais longa. Sem t_src em todas as falas = None (o vídeo roda em loop, como antes)."""
    if not falas or any(f.get("t_src") is None for f in falas):
        return None
    total = duracao(video)
    pedacos = []
    for i, f in enumerate(falas):
        ini_tela = 0.0 if i == 0 else f["ini"]
        fim_tela = falas[i + 1]["ini"] if i + 1 < len(falas) else dur_final
        alvo = fim_tela - ini_tela
        a = max(0.0, min(f["t_src"] - 0.3, total - 0.6))
        prox = falas[i + 1]["t_src"] - 0.3 if i + 1 < len(falas) else total
        b = prox if prox > a + 0.6 else min(a + alvo, total)
        L = max(b - a, 0.5)
        k = min(max(alvo / L, 1.0), 2.0)
        vf = f"fps=30,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,setpts={k:.4f}*PTS"
        if alvo > L * k:
            vf += f",tpad=stop_mode=clone:stop_duration={alvo - L * k + 0.2:.3f}"
        seg = tmp / f"base_{i:02d}.mp4"
        r = rodar([FFMPEG, "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{L:.3f}", "-i", video, "-vf", vf,
                   "-t", f"{alvo:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", seg])
        if r.returncode != 0:
            print(f"[base] trecho {i} falhou: {r.stderr[-200:]}", flush=True)
            return None
        pedacos.append(seg)
    # troca de comentário com transição gl (do último quadro do trecho anterior), mesma duração de cada trecho
    if realce_visual and realce_visual.disponivel("transicao"):
        rng = random.Random(str(video))
        feitas = sum(bool(realce_visual.transicao_inicio(pedacos[i], pedacos[i - 1], dur=0.4, semente=rng.random()))
                     for i in range(1, len(pedacos)) if rng.random() < GL_TRANS_CHANCE)
        print(f"[base] {feitas} transições gl", flush=True)
    lista = tmp / "base_lista.txt"
    lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in pedacos), encoding="utf-8")
    base = tmp / "base.mp4"
    r = rodar([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", base])
    if r.returncode != 0:
        print(f"[base] concat falhou: {r.stderr[-200:]}", flush=True)
        return None
    print(f"[base] vídeo sincronizado com os comentários ({len(pedacos)} trechos)", flush=True)
    return base


def montar(cfg):
    tmp = PROJETO / "tmp" / cfg.get("cache", Path(cfg["output"]).stem)
    tmp.mkdir(parents=True, exist_ok=True)
    falas = cfg["falas"]
    roteirizar(falas, tmp / "roteiro.json")
    gerar_vozes(falas, tmp)

    t = 0.4
    for f in falas:
        f["ini"] = t
        t += f["dur"] + PAUSA
    dur_final = t + 0.8
    print(f"[info] {len(falas)} falas, {dur_final:.1f}s", flush=True)
    escolher_efeitos(falas, tmp / "efeitos.json")

    # overlays: (png, x, y, ini, fim, anim) — anim: None | "cartao" (desliza da esquerda freando + aparece, como os
    # cartões dos comerciais do produto/video.py) | "sobe" (vai subindo devagar até sair, elemento sempre em movimento)
    ov = []
    faixa = tmp / "faixa.png"
    cy0 = png_faixa(cfg["titulo"], faixa)
    ov.append((faixa, 0, 0, 0, dur_final, None))
    lado = cfg.get("figurinha_lado", "alternar")
    for n, f in enumerate(falas):
        fim = falas[n + 1]["ini"] if n + 1 < len(falas) else dur_final
        pc = tmp / f"cartao_{n:02d}.png"
        png_cartao(f, n, pc, TOPO_H - 16 - cy0)
        ov.append((pc, 24, cy0, 0 if n == 0 else f["ini"] - 0.05, fim, "cartao"))
        pf, pfp = tmp / f"fig_{n:02d}.png", tmp / f"fig_{n:02d}_pop.png"
        fw, fh = png_figurinha(f["figurinha"], pf, n)
        pw, ph = png_figurinha(f["figurinha"], pfp, n, escala=1.22)
        esquerda = lado == "esquerda" or (lado == "alternar" and n % 2 == 0)
        x = 20 if esquerda else W - fw - 20
        y = TOPO_H + 30
        entra = f["ini"] + f.get("t_reacao", 0.15)  # só na reação: enquanto lê, o print do comentário fica livre
        if entra + 0.3 >= fim:
            continue
        ov.append((pfp, x - (pw - fw) // 2, y - (ph - fh) // 2, entra, entra + 0.08, None))
        ov.append((pf, x, y, entra + 0.08, fim, "sobe"))

    # legenda MIX (montagem_ms 01/11, padrão aprovado pela dona): cada palavra com desenho/cor/pop/giro/sublinhado
    # próprios e rastro da anterior; modo "inteligente" ou "livre" sorteado por vídeo (gravado no falas_final.json)
    alinhadas = []
    for f in falas:
        alinhadas += [(w, f["ini"] + s, f["ini"] + e) for s, e, w in f["palavras"]]
    blocos = ms.blocos_cineticos(alinhadas)
    mix = cfg.get("legenda_mix") or ms.escolher_mix()
    cfg["legenda_mix"] = mix
    plano = ms.plano_legenda(blocos, Path(cfg["output"]).stem, mix)
    # 02/11: a palavra caía em cima do print do comentário (touro: prints embaixo). A faixa dos prints (visão) vira a
    # área proibida da legenda, como o rosto no reel solar; prints embaixo = a legenda pode subir (até o cartão do topo)
    faixa_prints = FAIXAS_PRINTS.get(cfg.get("prints_regiao") or "", FAIXAS_PRINTS["meio"])
    topo_livre = cfg.get("prints_regiao") == "baixo"
    anterior = None
    for n, (cima, forte, s, e) in enumerate(blocos):
        pop, nor = tmp / f"leg_{n:03d}_pop.png", tmp / f"leg_{n:03d}.png"
        ms._png_cinetica(cima, forte, str(pop), n, rosto=faixa_prints, pop=True, topo_livre=topo_livre, estilo=plano[n])
        ms._png_cinetica(cima, forte, str(nor), n, rosto=faixa_prints, topo_livre=topo_livre, estilo=plano[n])
        for p in (pop, nor):
            _abaixo_do_cartao(p)
        puro = Image.open(nor).convert("RGBA")
        if plano[n]["rastro"] and anterior is not None and not ms._encostam(anterior.getbbox(), puro.getbbox()):
            ms._com_rastro(str(pop), anterior)
            ms._com_rastro(str(nor), anterior)
        anterior = puro
        meio = min(s + 0.09, e)
        ov.append((pop, 0, 0, s, meio - 0.01, None))
        if e - meio >= 0.04:
            ov.append((nor, 0, 0, meio, e - 0.02, None))
    print(f"[legenda] MIX {mix}: {len(blocos)} blocos", flush=True)

    base = base_sincronizada(cfg["video_base"], falas, dur_final, tmp)
    entradas = ["-i", str(base)] if base else ["-stream_loop", "-1", "-i", cfg["video_base"]]
    flash = ",".join(f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.35:t=fill:enable='between(t,{f['ini']:.2f},"
                     f"{f['ini'] + 0.06:.2f})'" for f in falas)
    filtros = [f"[0:v]fps=30,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
               f"{filtro_movimento(falas)},{flash}[b0]"]
    atual = "[b0]"
    for k, (p, x, y, a, b, anim) in enumerate(ov, 1):
        quando = f"enable='between(t,{a:.3f},{b:.3f})'"
        if anim == "cartao":
            entradas += ["-loop", "1", "-framerate", "30", "-t", f"{dur_final:.3f}", "-i", str(p)]
            filtros.append(f"[{k}:v]format=rgba,fade=t=in:st={max(a, 0):.2f}:d=0.25:alpha=1[c{k}]")
            xe = f"{x}-220*pow(max(0\\,1-(t-{a:.2f})/0.35)\\,3)"
            filtros.append(f"{atual}[c{k}]overlay=x='{xe}':y={y}:eval=frame:{quando}[b{k}]")
        elif anim == "sobe":
            entradas += ["-i", str(p)]
            ye = f"{y}-30*(t-{a:.2f})/{max(b - a, 0.5):.2f}"
            filtros.append(f"{atual}[{k}:v]overlay=x={x}:y='{ye}':eval=frame:{quando}[b{k}]")
        else:
            entradas += ["-i", str(p)]
            filtros.append(f"{atual}[{k}:v]overlay={x}:{y}:{quando}[b{k}]")
        atual = f"[b{k}]"
    # barrinha de progresso no topo (comerciais): enche até o fim do vídeo
    filtros.append(f"color=c=0xFFD60A:s={W}x10:r=30:d={dur_final:.3f}[barra]")
    filtros.append(f"{atual}[barra]overlay=x='-{W}+{W}*t/{dur_final:.2f}':y=0:eval=frame[vfim]")
    atual = "[vfim]"
    video = tmp / "video.mp4"
    script = tmp / "filtro_video.txt"
    script.write_text(";".join(filtros), encoding="utf-8")
    r = rodar([FFMPEG, "-y", "-v", "error", *entradas, "-filter_complex_script", script, "-map", atual,
               "-t", f"{dur_final:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
               "-an", video])
    if r.returncode != 0:
        raise SystemExit(f"[ERRO] vídeo:\n{r.stderr[-2000:]}")
    print("[video] OK", flush=True)

    # áudio: falas niveladas (-16 LUFS) + SFX da piada na palavra certa + transição (cortados) no começo de cada
    # fala + trilha que abaixa sob a voz (sidechain); amix SEM normalizar e loudnorm final em -14 LUFS.
    trans = [p for p in SFX_TRANSICAO.iterdir() if p.suffix.lower() in (".wav", ".mp3") and duracao(p) <= 2.2]
    random.Random(cfg["titulo"]).shuffle(trans)
    ent, fil, rot = [], [], []
    k = 0

    def entrada(arq, filtro, nome):
        nonlocal k
        ent.extend(["-i", str(arq)])
        fil.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,{filtro}[{nome}]")
        rot.append(f"[{nome}]")
        k += 1

    for n, f in enumerate(falas):
        ms_ini = int(f["ini"] * 1000)
        entrada(f["wav"], f"atrim=0:{f['dur'] + 0.1:.3f},loudnorm=I=-16:TP=-2,adelay={ms_ini}|{ms_ini}", f"v{n}")
        ms_sfx = int((f["ini"] + f["t_sfx"]) * 1000)
        entrada(Path(f["sfx"]), f"atrim=0:2.5,afade=t=out:st=2.1:d=0.4,loudnorm=I=-20,volume=0.8,adelay={ms_sfx}|{ms_sfx}",
                f"s{n}")
        if trans and n > 0:
            ms_tr = max(0, ms_ini - 200)
            entrada(trans[n % len(trans)], f"volume=0.35,adelay={ms_tr}|{ms_tr}", f"t{n}")
    fil.append(f"{''.join(rot)}amix=inputs={len(rot)}:normalize=0:duration=longest[voz]")
    final = "[voz]"
    if cfg.get("trilha"):
        ent += ["-stream_loop", "-1", "-i", str(Path(cfg["trilha"]))]
        fil.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,volume={cfg.get('trilha_volume', 0.25)},"
                   f"atrim=0:{dur_final:.3f}[tr0]")
        fil.append("[voz]asplit=2[voz1][voz2]")
        fil.append("[tr0][voz2]sidechaincompress=threshold=0.04:ratio=5:attack=30:release=350[tr]")
        fil.append("[voz1][tr]amix=inputs=2:normalize=0:duration=longest[mix]")
        final = "[mix]"
    fil.append(f"{final}atrim=0:{dur_final:.3f},afade=t=out:st={dur_final - 1:.3f}:d=1,"
               f"loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    audio = tmp / "audio.wav"
    script_a = tmp / "filtro_audio.txt"
    script_a.write_text(";".join(fil), encoding="utf-8")
    r = rodar([FFMPEG, "-y", "-v", "error", *ent, "-filter_complex_script", script_a, "-map", "[aout]",
               "-ar", "48000", audio])
    if r.returncode != 0:
        raise SystemExit(f"[ERRO] áudio:\n{r.stderr[-2000:]}")
    print("[audio] OK", flush=True)

    saida = Path(cfg["output"])
    saida.parent.mkdir(parents=True, exist_ok=True)
    r = rodar([FFMPEG, "-y", "-v", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
               "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", saida])
    if r.returncode != 0:
        raise SystemExit(f"[ERRO] final:\n{r.stderr[-2000:]}")
    (tmp / "falas_final.json").write_text(json.dumps(falas, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[OK] {saida}", flush=True)
    return saida


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    montar(json.loads(Path(ap.parse_args().config).read_text(encoding="utf-8")))
