"""Foto do dono feita NA HORA, no cenario do video (24/10/2026, pedido do dono).

Problema: a foto sorteada de D:\\veo\\fotos nao combinava com o cenario do prompt (ex.: foto de praia + "neon cyber
club"), e o Veo saia incoerente. Agora o Flow (Nano Banana, D:\\flow-imagens) cria a foto ja no cenario, usando como
referencia as fotos-base de fundo branco do dono.

PRIORIDADE DO DONO: NUNCA MUDAR O ROSTO. Toda foto gerada passa pelo revisor (OpenCV YuNet + SFace) contra as bases;
reprovou = tenta de novo; nenhuma passou = foto do ESTOQUE (aprovada antes, cenario parecido) ou None e o cron usa a
foto antiga (escolher_foto, que tambem ja tira as antigas com rosto reprovado). Nunca entra foto com rosto diferente.

Revisoes da foto (24/10, noite): rosto (obrigatorio) + visao (gateway, gemini-3-flash): texto legivel, marca d'agua/
logo e deformacao. A visao fora do ar NAO trava (o rosto e a prioridade); so o "sim" dela reprova.

  python foto_na_hora.py teste "cenario" "prompt"   -> gera e revisa uma foto (gasta 0 credito no 2.1)
  python foto_na_hora.py revisar foto.jpg ...       -> revisor de rosto + visao (nota e veredito)
  python foto_na_hora.py calibrar                   -> nota das bases entre si (o limiar tem que ficar abaixo)
  python foto_na_hora.py antigas                    -> revisor nas fotos antigas de D:\\veo\\fotos (grava a lista)
  python foto_na_hora.py video arquivo.mp4          -> rosto em 3 quadros do video pronto

VEO_FOTO_NA_HORA=0 desliga. Bases: VEO_BASES_ROSTO. Limiar: VEO_ROSTO_LIMIAR. VEO_FOTO_VISAO=0 tira a visao.
"""
import base64
import glob
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

import cv2
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
BASES_DIR = os.environ.get("VEO_BASES_ROSTO", r"D:\fotos para videos\fotos\fotos base so suar se for criar uma foto nova\sem fundo retrato")
# A pasta irma "imagem base inovare frente" tem telefone/WhatsApp (o que derrubou os canais): nunca usar.
MODELOS = r"D:\hipercool-materiais\models\rosto"
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
SAIDA_DIR = os.path.join(os.path.dirname(AQUI), "fotos_na_hora")
REPROVADAS_DIR = os.path.join(SAIDA_DIR, "_reprovadas")
CACHE_BASES = os.path.join(AQUI, "logs", "rosto_bases.npz")
REGISTRO = os.path.join(AQUI, "logs", "foto_na_hora.jsonl")
ANTIGAS_REPROVADAS = os.path.join(AQUI, "logs", "fotos_rosto_reprovado.json")
GATEWAY = os.path.join(AQUI, "secrets", "gateway.json")
if r"D:\flow-imagens" not in sys.path:
    sys.path.append(r"D:\flow-imagens")  # gera_imagem; no FIM do sys.path (memoria 23/10: outro projeto nunca na frente)

# SFace: cosseno >= 0.363 ja e "mesma pessoa" pelo OpenCV. O dono quer zero risco: exigimos bem mais.
# 25/10 (dono, vendo a foto de nota 0,553: "esse cara não é meu rosto"): 0,50 -> 0,57. As que ele aprovou tiraram
# 0,578-0,700 contra as 30 bases; sósias 0,27-0,33.
LIMIAR = float(os.environ.get("VEO_ROSTO_LIMIAR", "0.57"))
# no VIDEO o rosto vem em movimento/angulo: mediana dos 3 quadros contra um limiar um pouco menor (calibrado 24/10:
# o 1o video real deu 0,54/0,56/0,60; fotos antigas de outra "versao" do dono deram 0,34-0,44)
LIMIAR_VIDEO = float(os.environ.get("VEO_ROSTO_LIMIAR_VIDEO", "0.50"))  # 25/10: 0,45 -> 0,50 (junto com a foto)
TENTATIVAS = int(os.environ.get("VEO_FOTO_TENTATIVAS", "3"))
ESTOQUE_MAX_USOS = 2  # foto do estoque sai no maximo 2 vezes (video repetido e o que o YouTube pune)


def _log(msg):
    print(f"[foto_na_hora] {msg}", flush=True)


_det = _rec = None


def _modelos():
    global _det, _rec
    if _det is None:
        _det = cv2.FaceDetectorYN.create(os.path.join(MODELOS, "yunet.onnx"), "", (320, 320), 0.8, 0.3, 5000)
        _rec = cv2.FaceRecognizerSF.create(os.path.join(MODELOS, "sface.onnx"), "")
    return _det, _rec


def _ler(caminho):
    img = cv2.imdecode(np.fromfile(caminho, dtype=np.uint8), cv2.IMREAD_COLOR)  # aceita acento/espaco no caminho
    if img is None:
        raise ValueError(f"nao abriu {caminho}")
    return img


def rostos(caminho_ou_img):
    """Lista de (embedding, area, caixa, giro) de cada rosto, maior primeiro. giro: 0 = de frente, ~1 = perfil."""
    det, rec = _modelos()
    img = _ler(caminho_ou_img) if isinstance(caminho_ou_img, str) else caminho_ou_img
    h, w = img.shape[:2]
    if max(h, w) > 1600:
        f = 1600 / max(h, w)
        img = cv2.resize(img, (int(w * f), int(h * f)))
        h, w = img.shape[:2]
    det.setInputSize((w, h))
    _, achados = det.detect(img)
    out = []
    for r in (achados if achados is not None else []):
        emb = rec.feature(rec.alignCrop(img, r)).flatten()
        olho_d, olho_e, nariz = r[4:6], r[6:8], r[8:10]
        dist = max(1.0, float(np.linalg.norm(olho_e - olho_d)))
        giro = min(1.0, abs(float(nariz[0] - (olho_d[0] + olho_e[0]) / 2)) / dist * 2)
        out.append((emb / np.linalg.norm(emb), float(r[2] * r[3]), [int(x) for x in r[:4]], giro))
    return sorted(out, key=lambda x: -x[1])


def usar_bases(pasta):
    """25/10 (dono: "todo cliente tem uma subpasta no Drive com as fotos base do seu clone"): troca as fotos-base (e o
    cache dos rostos) pra outra pessoa — ex.: o apresentador da empresa (postador cache\\fotos_base\\<conta>). Vale pro
    processo inteiro (gerar, revisar, revisar_video). Volta ao dono com usar_bases(None)."""
    global BASES_DIR, CACHE_BASES
    import hashlib
    padrao = os.environ.get("VEO_BASES_ROSTO", r"D:\fotos para videos\fotos\fotos base so suar se for criar uma foto nova\sem fundo retrato")
    BASES_DIR = str(pasta) if pasta else padrao
    CACHE_BASES = os.path.join(AQUI, "logs", "rosto_bases.npz" if not pasta else
                               f"rosto_bases_{hashlib.md5(str(pasta).lower().encode()).hexdigest()[:10]}.npz")


def bases_com_rosto(pasta):
    """Quantas fotos da pasta têm rosto (0 se vazia/inexistente). Não muda as bases em uso."""
    global BASES_DIR, CACHE_BASES
    antes = (BASES_DIR, CACHE_BASES)
    try:
        usar_bases(pasta)
        return len(embeddings_bases()[1])
    except Exception:  # noqa: BLE001
        return 0
    finally:
        BASES_DIR, CACHE_BASES = antes


def bases():
    arqs = sorted(glob.glob(os.path.join(BASES_DIR, "*.jpg")) + glob.glob(os.path.join(BASES_DIR, "*.png")))
    if not arqs:
        raise RuntimeError(f"nenhuma foto-base em {BASES_DIR}")
    return arqs


def embeddings_bases():
    """(embs, arqs, giros) das bases com rosto (cache por nome+tamanho)."""
    arqs = bases()
    chave = "v2|" + "|".join(f"{os.path.basename(a)}:{os.path.getsize(a)}" for a in arqs)
    try:
        c = np.load(CACHE_BASES, allow_pickle=False)
        if str(c["chave"]) == chave:
            return c["embs"], [str(x) for x in c["arqs"]], [float(x) for x in c["giros"]]
    except Exception:
        pass
    embs, ok, giros = [], [], []
    for a in arqs:
        r = rostos(a)
        if r:
            embs.append(r[0][0]); ok.append(a); giros.append(r[0][3])
        else:
            _log(f"base sem rosto detectado (ignorada): {os.path.basename(a)}")
    embs = np.array(embs)
    os.makedirs(os.path.dirname(CACHE_BASES), exist_ok=True)
    np.savez(CACHE_BASES, embs=embs, arqs=np.array(ok), chave=np.array(chave), giros=np.array(giros))
    return embs, ok, giros


def nota_rosto(emb):
    """Media dos 5 cossenos mais altos contra as bases (1 base parecida nao basta)."""
    embs = embeddings_bases()[0]
    return float(np.mean(np.sort(embs @ emb)[-5:]))


def revisar_rosto(caminho):
    """(aprovada, nota, motivo) so do rosto."""
    r = rostos(caminho)
    if not r:
        return False, 0.0, "nenhum rosto na foto"
    principal = r[0]
    # outro rosto grande na cena (>40% do principal) poderia virar o "personagem" do Veo
    if len(r) > 1 and r[1][1] > 0.4 * principal[1]:
        return False, 0.0, f"{len(r)} rostos grandes na foto"
    nota = nota_rosto(principal[0])
    if nota < LIMIAR:
        return False, nota, f"rosto diferente do dono (nota {nota:.2f} < {LIMIAR:.2f})"
    return True, nota, "mesmo rosto"


PERGUNTA_VISAO = (
    "Esta foto vai virar o 1o quadro de um video curto. Responda SO com JSON, sem mais nada: "
    '{"texto": "sim" ou "nao", "marca": "sim" ou "nao", "deformacao": "sim" ou "nao", "o_que": "<curto>"}. '
    "texto = existe alguma palavra, letra ou numero LEGIVEL na imagem (letreiro, placa, camiseta, tela)? "
    "marca = existe marca d'agua, logo de app/IA (Grok, Gemini, Veo, Sora, TikTok, Meta) ou assinatura num canto? "
    "deformacao = maos/dedos/rosto/oculos claramente deformados ou duplicados?")


def revisar_visao(caminho):
    """(ok, motivo). Gateway fora/sem resposta = ok (nao trava); so o 'sim' reprova."""
    if os.environ.get("VEO_FOTO_VISAO", "1") == "0":
        return True, "visao desligada"
    try:
        gw = json.load(open(GATEWAY, encoding="utf-8"))
        img = _ler(caminho)
        h, w = img.shape[:2]
        img = cv2.resize(img, (540, int(h * 540 / w)))
        jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()
        corpo = {"model": "antigravity/gemini-3-flash", "max_tokens": 120, "messages": [{"role": "user", "content": [
            {"type": "text", "text": PERGUNTA_VISAO},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(jpg).decode()}}]}]}
        req = urllib.request.Request(gw["gateway_url"].rstrip("/") + "/v1/chat/completions",
                                     data=json.dumps(corpo).encode(),
                                     headers={"Authorization": "Bearer " + gw["gateway_key"],
                                              "Content-Type": "application/json"})
        txt = json.loads(urllib.request.urlopen(req, timeout=90).read())["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", txt, re.S)
        d = json.loads(m.group(0)) if m else {}
    except Exception as e:  # noqa: BLE001
        return True, f"visao indisponivel ({type(e).__name__})"
    ruins = [k for k in ("texto", "marca", "deformacao") if str(d.get(k, "")).lower().startswith("s")]
    if ruins:
        return False, f"visao: {', '.join(ruins)} ({str(d.get('o_que', ''))[:80]})"
    return True, "visao ok"


def revisar(caminho):
    """(aprovada, nota, motivo): rosto primeiro (obrigatorio); passou, a visao confere texto/marca/deformacao."""
    ok, nota, motivo = revisar_rosto(caminho)
    if not ok:
        return ok, nota, motivo
    ok_v, motivo_v = revisar_visao(caminho)
    # o registro guarda as duas partes (antes "mesmo rosto" escondia se a visao rodou ou estava fora)
    return ok_v, nota, (f"{motivo}; {motivo_v}" if ok_v else motivo_v)


# ---- escolha das bases (item 3): pose pelo prompt + base que mais aprova ------------------------------------------
_DE_FRENTE = re.compile(r"camera|câmera|talking|speaks|falando|selfie|direct|olha|looking at", re.I)


def _taxa_bases():
    """{base: (usos, aprovadas)} pelo registro."""
    t = {}
    for reg in _registros():
        if reg.get("refs") and "aprovada" in reg:
            for b in reg["refs"]:
                u, a = t.get(b, (0, 0))
                t[b] = (u + 1, a + (1 if reg["aprovada"] else 0))
    return t


def escolher_bases(prompt_video, n=3):  # 25/10: 3 referências (frente + 2 ângulos) copiam o rosto com mais fidelidade
    """1a base: de frente (giro < 0.35) se a cena e falando pra camera, sorteada por Thompson das aprovacoes;
    2a: outro angulo, pra o Nano Banana ver o rosto em 3D."""
    _, arqs, giros = embeddings_bases()
    taxa = _taxa_bases()

    def amostra(a):
        u, ap = taxa.get(os.path.basename(a), (0, 0))
        return random.betavariate(ap + 1, u - ap + 1)
    frente = [a for a, g in zip(arqs, giros) if g < 0.35] or arqs
    lado = [a for a, g in zip(arqs, giros) if g >= 0.35] or arqs
    pool1 = frente if _DE_FRENTE.search(prompt_video or "") else arqs
    b1 = max(pool1, key=amostra)
    resto = [a for a in (lado if b1 in frente else frente) if a != b1] or [a for a in arqs if a != b1]
    return [b1] + random.sample(resto, min(n - 1, len(resto)))


# ---- estoque (item 5): foto aprovada antes, cenario parecido --------------------------------------------------------
def _registros():
    try:
        with open(REGISTRO, encoding="utf-8") as f:
            return [json.loads(ln) for ln in f if ln.strip()]
    except (OSError, ValueError):
        return []


# palavras que TODO prompt do Veo tem: sem tirar, "neon club" e "praia" ficavam ~40% parecidos so pelo molde do texto
_COMUNS = {"person", "frame", "camera", "talking", "talks", "directly", "speaking", "speaks", "vertical", "portrait",
           "lighting", "light", "punchy", "tiktok", "brazilian", "portuguese", "engaging", "viral", "shot", "scene",
           "video", "with", "from", "that", "this", "into", "while", "their", "they", "them", "then", "there", "were",
           "have", "will", "your", "about", "says", "said", "looks", "looking", "eyes", "face", "man", "woman"}


def _palavras(t):
    return {p for p in re.findall(r"[a-z]{4,}", (t or "").lower()) if p not in _COMUNS}


def _tag_do_arquivo(caminho):
    """<tag>_<AAAAMMDD>_<HHMMSS>_<n>.png -> tag (registros de antes do campo 'tag')."""
    m = re.match(r"(.+?)_\d{8}_\d{6}_\d+\.png$", os.path.basename(str(caminho)))
    return m.group(1) if m else None


def do_estoque(cenario, tag=None):
    """Foto aprovada antes, do MESMO tema (tag; registro antigo sem o campo: tag pelo nome do arquivo), cujo cenario
    divide >= 50% das palavras de conteudo, usada menos de ESTOQUE_MAX_USOS vezes; ou None."""
    regs = _registros()
    usos = {}
    for r in regs:
        if r.get("estoque_usada"):
            usos[r["estoque_usada"]] = usos.get(r["estoque_usada"], 0) + 1
    alvo, melhor = _palavras(cenario), None
    if not alvo:
        return None
    for r in regs:
        a = r.get("arquivo")
        if not r.get("aprovada") or not a or not os.path.exists(a) or usos.get(a, 0) >= ESTOQUE_MAX_USOS:
            continue
        if tag and (r.get("tag") or _tag_do_arquivo(a)) != tag:
            continue
        p = _palavras(r.get("cenario"))
        sim = len(alvo & p) / max(1, len(alvo | p))
        if sim >= 0.5 and (melhor is None or sim > melhor[0]):
            melhor = (sim, a)
    if melhor:
        _registrar({"estoque_usada": melhor[1], "cenario": cenario, "tag": tag, "semelhanca": round(melhor[0], 2)})
        return melhor[1]
    return None


def _pedido(cenario, prompt_video):
    return (
        "Photorealistic vertical 9:16 photo of THE SAME MAN from the reference photos. "
        "ABSOLUTE PRIORITY: keep his face 100% identical to the references - same face shape, eyes, nose, mouth, "
        "beard, hairline, haircut, skin tone, and his thin-frame glasses worn ON HIS EYES (never on the head, never sunglasses). Do not "
        "beautify, age, slim or change his face in any way. "
        f"Only change the background, clothes and lighting to fit this scene: {cenario}. "
        f"He is in the moment that starts this video: {prompt_video[:350]}. "
        "Medium shot from chest up, face clearly visible, looking at the camera, natural skin texture. "
        "Absolutely NO readable text anywhere: no signs with words, no letters on clothes or screens, no logos, "
        "no watermark, no other people's faces in focus."
    )


PRAZO_S = float(os.environ.get("VEO_FOTO_PRAZO_MIN", "15")) * 60  # etapa inteira da foto; passou = foto de reserva
CONTAS_POR_TENTATIVA = 2  # sem isso o gera_imagem tentava TODAS as contas do PC1 (ate 5 min cada falha)


def gerar(cenario, prompt_video, tag="veo", maquinas=None, pedido=None):
    """Caminho da foto aprovada no cenario (nova ou do estoque do mesmo tema), ou None (o cron cai na foto antiga).
    maquinas: as que a cadeia do Veo liberou (24/10: sem isso o Flow abria Chrome no PC1 em pausa de carga ou no desktop
    com o dono em chamada); None = sem restricao (teste manual)."""
    if os.environ.get("VEO_FOTO_NA_HORA", "1") == "0":
        return None
    try:
        from gera_imagem import gerar_imagem
        embeddings_bases()
    except Exception as e:
        _log(f"indisponivel ({str(e)[:120]}) - tenta o estoque")
        return do_estoque(cenario, tag)
    os.makedirs(SAIDA_DIR, exist_ok=True)
    os.makedirs(REPROVADAS_DIR, exist_ok=True)
    texto = pedido or _pedido(cenario or "", prompt_video or "")  # pedido: outra pessoa (clone de empresa)
    inicio = time.time()
    sem_rosto = 0
    for t in range(1, TENTATIVAS + 1):
        if time.time() - inicio > PRAZO_S:
            _log(f"prazo de {PRAZO_S / 60:.0f} min da foto acabou - segue sem tentar de novo")
            break
        refs = escolher_bases(prompt_video)
        motivo = ""
        saida = os.path.join(SAIDA_DIR, f"{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{t}.png")
        t0 = time.time()
        try:
            arqs = gerar_imagem(texto, saida, refs=refs, formato="9:16", max_contas=CONTAS_POR_TENTATIVA,
                                maquinas=maquinas)
        except Exception as e:
            _log(f"tentativa {t}: Flow falhou ({str(e)[:150]})")
            _registrar({"tentativa": t, "erro": str(e)[:600], "cenario": cenario, "tag": tag,  # 600: D35 motivo por maquina
                        "maquinas": maquinas, "s": round(time.time() - t0)})
            if "polic" in str(e).lower():
                break
            if str(e).rstrip().endswith("imagem:"):  # nenhuma conta nem foi tentada (maquinas da lista ocupadas)
                break
            continue
        for arq in map(str, arqs):  # gerar_imagem devolve Path
            ok, nota, motivo = revisar(arq)
            _registrar({"tentativa": t, "arquivo": arq, "refs": [os.path.basename(r) for r in refs], "aprovada": ok,
                        "nota": round(nota, 3), "motivo": motivo, "cenario": cenario, "tag": tag,
                        "s": round(time.time() - t0)})
            if ok:
                _log(f"APROVADA {os.path.basename(arq)} (nota {nota:.2f})")
                return arq
            _log(f"REPROVADA {os.path.basename(arq)}: {motivo}")
            try:
                os.replace(arq, os.path.join(REPROVADAS_DIR, os.path.basename(arq)))
            except OSError:
                pass
        sem_rosto = sem_rosto + 1 if "nenhum rosto" in motivo else 0
        if sem_rosto >= 2:  # 25/10: tema "Transformação" (objetos) deu 2x sem rosto e 7,5 min perdidos: o cenário não tem pessoa
            _log("2 fotos seguidas sem rosto: o cenário não favorece pessoa - segue com a foto de reserva")
            break
        if t < TENTATIVAS and "nenhum rosto" not in motivo and "rosto diferente" not in motivo:
            texto += " Reminder: the previous attempt was rejected for: " + motivo[:120] + "."
    est = do_estoque(cenario, tag)
    if est:
        _log(f"nenhuma nova passou - usando do estoque {os.path.basename(est)}")
        return est
    _log("nenhuma foto passou no revisor - usa foto antiga (rosto nunca muda)")
    return None


# ---- fotos antigas (item 6) e video pronto (item 7) -----------------------------------------------------------------
def _gravar_antigas(d):
    d["_leia"] = ("fotos de D:\\veo\\fotos conferidas pelo revisor de rosto (foto_na_hora.py antigas / rosto_ok): "
                  "reprovadas saem do sorteio do cron; aprovadas nao sao conferidas de novo")
    d["limiar"] = LIMIAR
    tmp = ANTIGAS_REPROVADAS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, ANTIGAS_REPROVADAS)


def revisar_antigas(pasta=r"D:\veo\fotos"):
    """Confere TODAS as antigas e grava {caminho_rel: ...} de aprovadas e reprovadas (o cron tira as reprovadas)."""
    ruins, boas, total = {}, {}, 0
    for a in glob.glob(os.path.join(pasta, "**", "*.*"), recursive=True):
        if not a.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) or os.sep + "_" in a[len(pasta):]:
            continue
        total += 1
        try:
            ok, nota, motivo = revisar_rosto(a)
        except Exception as e:  # noqa: BLE001
            ok, nota, motivo = False, 0.0, f"erro {e}"
        rel = os.path.relpath(a, pasta).replace(os.sep, "/")
        if ok:
            boas[rel] = round(nota, 3)
        else:
            ruins[rel] = {"nota": round(nota, 3), "motivo": motivo}
    _gravar_antigas({"total": total, "reprovadas": ruins, "aprovadas": boas})
    return total, len(ruins)


def rosto_ok(caminho, pasta=r"D:\veo\fotos"):
    """A foto antiga e do dono? Usa o que ja foi conferido (aprovadas/reprovadas); foto que ninguem conferiu ainda
    (nova na pasta, ou de fora dela) e conferida AGORA (~0,2 s) e o resultado fica gravado. Erro = False (rosto nunca
    muda: na duvida a foto nao entra)."""
    try:
        rel = os.path.relpath(caminho, pasta).replace(os.sep, "/")
    except ValueError:  # outro disco
        rel = os.path.abspath(caminho)
    try:
        d = json.load(open(ANTIGAS_REPROVADAS, encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    if rel in d.get("reprovadas", {}):
        return False
    if rel in d.get("aprovadas", {}):
        return True
    try:
        ok, nota, motivo = revisar_rosto(caminho)
    except Exception:  # noqa: BLE001
        return False
    if ok:
        d.setdefault("aprovadas", {})[rel] = round(nota, 3)
    else:
        d.setdefault("reprovadas", {})[rel] = {"nota": round(nota, 3), "motivo": motivo}
    d["total"] = len(d.get("aprovadas", {})) + len(d.get("reprovadas", {}))
    try:
        _gravar_antigas(d)
    except OSError:
        pass
    return ok


def fotos_antigas_reprovadas(pasta=r"D:\veo\fotos"):
    try:
        d = json.load(open(ANTIGAS_REPROVADAS, encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {os.path.normcase(os.path.join(pasta, *k.split("/"))) for k in d.get("reprovadas", {})}


def revisar_video(mp4, posicoes=None):
    """(ok, notas, motivo): rosto principal em vários quadros; mediana >= LIMIAR_VIDEO. Sem rosto num quadro conta 0.

    11/11: no vídeo FINAL dos reels o quadro de 90% é o CARTÃO da marca (sem rosto, nota 0,0 em TODOS os aprovados) —
    a mediana de 3 virava o MENOR dos 2 rostos e 1 careta (boca aberta, 0,485) reprovava vídeo certo: a Globo ficou 3
    horários sem reel (21:20, 23:20, 01:20) com o próprio responsável no vídeo (folha conferida). Agora: 5 quadros só nos
    85% iniciais (antes do cartão), quadros SEM rosto não entram na mediana, e precisa de 2+ quadros com rosto.
    Rosto de outra pessoa continua reprovado (fica abaixo do limiar na maioria dos quadros). VEO_ROSTO_3QUADROS=1 volta."""
    antigo = os.environ.get("VEO_ROSTO_3QUADROS") == "1"
    if posicoes is None:
        posicoes = (0.1, 0.5, 0.9) if antigo else (0.08, 0.25, 0.42, 0.6, 0.78)
    try:
        dur = float(subprocess.run([FFMPEG.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries",
                                    "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True)
                    .stdout.strip() or 0)
        notas = []
        for p in posicoes:
            png = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{dur * p:.2f}", "-i", mp4, "-frames:v", "1",
                                  "-f", "image2", "-vcodec", "png", "-"], capture_output=True).stdout
            img = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
            r = rostos(img) if img is not None else []
            notas.append(round(nota_rosto(r[0][0]), 3) if r else 0.0)
    except Exception as e:  # noqa: BLE001
        return True, [], f"revisor de video indisponivel ({type(e).__name__}) - nao trava"
    if antigo:
        med = sorted(notas)[len(notas) // 2]
    else:
        com_rosto = sorted(n for n in notas if n > 0)
        if len(com_rosto) < 2:
            return False, notas, f"rosto do dono em só {len(com_rosto)} de {len(notas)} quadros"
        meio = len(com_rosto) // 2
        med = com_rosto[meio] if len(com_rosto) % 2 else (com_rosto[meio - 1] + com_rosto[meio]) / 2
    if med < LIMIAR_VIDEO:
        return False, notas, f"rosto do video diferente do dono (mediana {med:.2f} < {LIMIAR_VIDEO:.2f})"
    return True, notas, "mesmo rosto no video"


def _registrar(reg):
    reg["em"] = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(REGISTRO, "a", encoding="utf-8") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "revisar":
        for a in sys.argv[2:]:
            print(os.path.basename(a), revisar(a))
    elif cmd == "calibrar":
        embs, arqs, giros = embeddings_bases()
        print(f"{len(arqs)} bases com rosto de {len(bases())}")
        for i, a in enumerate(arqs):
            outros = np.delete(embs, i, axis=0) @ embs[i]
            print(f"{np.mean(np.sort(outros)[-5:]):.3f}  giro {giros[i]:.2f}  {os.path.basename(a)}")
    elif cmd == "antigas":
        print("total, reprovadas:", revisar_antigas())
    elif cmd == "video":
        for a in sys.argv[2:]:
            print(os.path.basename(a), revisar_video(a))
    elif cmd == "teste":
        print(gerar(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "", tag="teste"))
    else:
        print(__doc__)
