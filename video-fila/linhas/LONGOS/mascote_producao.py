r"""Produção contínua da mascote (dona 28/10: "mantenha a produção lá constante como se fosse um dos projetos de
vídeo"). Tarefa MascoteProducao (oculta) roda isto; cada rodada:
  1. imagens que faltam (bench\gerar_waifu2.py: série biquíni, cosplays, amigas);
  2. VIDEOS_POR_RODADA falas novas no Veo 3 — roupa menos usada x fala menos usada (dona: "cada vídeo com uma roupa
     diferente"); a amiga entra em ~1 de cada 4 (elas "aparecem menos");
  3. confere que o vídeo é ELA (fundo branco no quadro; o Veo já baixou vídeo de outro robô da mesma conta) e recorta
     (bench\mascote_recorte.py) -> assets\mascote_viva\<tema>_<roupa>_NN.webm, que o longo usa (mascote_overlay).
Registro: assets\mascote_viva\producao.json.   python mascote_producao.py [--videos N]
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PY = r"D:\veo\venv\Scripts\python.exe"
BENCH = Path(__file__).resolve().parent / "bench"
FOTOS = Path(r"D:\hipercool-materiais\mascote_waifu_v2")
VIVA = Path(r"D:\hipercool-materiais\assets\mascote_viva")
REG = VIVA / "producao.json"
LOG = FOTOS / "producao.log"
VIDEOS_POR_RODADA = int(sys.argv[sys.argv.index("--videos") + 1]) if "--videos" in sys.argv else 1

# (id, tema, fala, movimento). Tema = começo do nome do arquivo, que o mascote_overlay.gravacao_viva escolhe pela frase.
FALAS = [
    ("insc1", "inscreva", "Ei, gostou da história? Então se inscreve no canal e ativa o sininho, que amanhã tem mais!",
     "She waves at the camera, smiles, then points at the viewer and winks"),
    ("insc2", "inscreva", "Se você chegou até aqui, já é de casa! Se inscreve aí pra não perder o próximo.",
     "She leans toward the camera with a warm smile and makes a heart with her hands"),
    ("insc3", "inscreva", "Deixa o seu like, que isso me ajuda demais a trazer mais histórias pra você!",
     "She gives a thumbs up, bounces happily and blows a kiss"),
    ("insc4", "inscreva", "Psiu! Ainda não é inscrito? Corre lá, que é rapidinho e de graça!",
     "She whispers with a hand beside her mouth, then laughs and points at the viewer"),
    ("com1", "comenta", "Deixa aqui nos comentários: você faria a mesma coisa que ele? Eu quero saber!",
     "She leans forward curiously, hand on her chin, then points down toward the bottom of the screen"),
    ("com2", "comenta", "E aí, quem você acha que vai vencer essa? Me conta aqui nos comentários!",
     "She crosses her arms with a teasing smile, then points at the viewer"),
    ("com3", "comenta", "Comenta aqui embaixo qual foi a sua parte favorita até agora!",
     "She claps excitedly and points down with both hands"),
    # 30/10 dona: "o nome vai ser Maria" — ela se apresenta (tema inscreva: entra nos pedidos de inscrição)
    ("maria1", "inscreva", "Oi, eu sou a Maria! Se você curte essas histórias, se inscreve no canal que tem mais!",
     "She waves cheerfully, puts a hand on her chest introducing herself, then points at the viewer and winks"),
    ("tchau1", "tchau", "Valeu por assistir até aqui! Te vejo no próximo, beijo!",
     "She smiles warmly, blows a kiss to the camera and waves goodbye"),
    ("tchau2", "tchau", "Por hoje é só, gente! Amanhã tem mais, não some, hein!",
     "She waves goodbye with both hands, then winks"),
    ("susto", "reacao_susto", "Oxe! Gente, eu não esperava por essa não!",
     "She jumps back surprised with both hands on her cheeks, eyes wide, then laughs"),
    ("riso", "reacao_riso", "Hahaha, não acredito que ele fez isso!",
     "She bursts out laughing, holding her belly, wiping a tear"),
    ("raiva", "reacao_raiva", "Ai, que raiva desse cara! Alguém segura ele!",
     "She puffs her cheeks angrily, stomps her foot and shakes her fist playfully"),
    ("choque", "reacao_choque", "Gente, que reviravolta! Eu tô passada!",
     "She covers her mouth in shock, then fans herself with her hand"),
    # 02/11 dona ("as reações da mascote é só uma mesma fala... tem que ter variedade, algumas curtas"): até 01/11 só
    # existiam 4 falas de reação e TODAS as roupas/amigas gravavam a mesma — no vídeo ela repetia "Oxe! Gente, eu não
    # esperava por essa não!". Agora várias por emoção, CURTAS (1-2 s), e o mascote_overlay nunca repete a fala no vídeo.
    ("susto2", "reacao_susto", "Eita!", "She jumps with wide eyes and both hands up, then giggles"),
    ("susto3", "reacao_susto", "Nossa, que susto!", "She flinches back with a hand on her chest, then laughs nervously"),
    ("susto4", "reacao_susto", "Socorro, gente!", "She hides her face behind her hands and peeks through her fingers"),
    ("riso2", "reacao_riso", "Kkkkk, eu não aguento!", "She laughs hard, bending forward and slapping her knee"),
    ("riso3", "reacao_riso", "Ele não presta, gente!", "She laughs and shakes her head in disbelief"),
    ("riso4", "reacao_riso", "Que vergonha alheia!", "She covers half of her face with a hand, cringing and laughing"),
    ("raiva2", "reacao_raiva", "Que ódio!", "She crosses her arms, puffs her cheeks and turns her face away"),
    ("raiva3", "reacao_raiva", "Bem feito pra ele!", "She smirks, nods with satisfaction and dusts off her hands"),
    ("raiva4", "reacao_raiva", "Não acredito nisso!", "She throws her hands up in frustration and stomps once"),
    ("choque2", "reacao_choque", "Mentira!", "She gasps with both hands on her cheeks, mouth open"),
    ("choque3", "reacao_choque", "Para tudo!", "She raises a hand like a stop sign, eyes wide, frozen in shock"),
    ("choque4", "reacao_choque", "Tá de brincadeira!", "She leans in toward the camera squinting, then steps back stunned"),
]

# 02/11 dona ("a amiga foi feita pra interagirem uma com a outra, comentando, e não aparecer falando a mesma coisa"):
# conversas de 2 falas — a amiga RESPONDE à Maria (tema "dupla_<n>_a" = Maria, "dupla_<n>_b" = amiga). O
# mascote_overlay junta o par (Maria fala, a amiga responde) na mesma cena. (id, emoção, fala da Maria, fala da amiga)
DUPLAS = [
    ("dupla1", "choque", "Amiga, você viu isso?!", "Vi! Tô sem palavras!"),
    ("dupla2", "raiva", "Esse cara não tem jeito!", "Né? Alguém dá um jeito nele!"),
    ("dupla3", "riso", "Ele achou que ia dar certo!", "Coitado, kkkk!"),
    ("dupla4", "susto", "Eu não esperava essa!", "Nem eu, amiga!"),
    ("dupla5", "choque", "Quem diria, hein?", "Eu já sabia, amiga!"),
    ("dupla6", "riso", "Amiga, olha a cara dele!", "Eu tô chorando de rir!"),
]


# 30/10 dona: cenas MUDAS por cima do vídeo andando (sem parar a história) — (id, tema, texto da faixa, extra).
# tema "cena_<tipo>" = nome do arquivo que o mascote_overlay.cena_viva escolhe; aviao = faixa com o texto.
CENAS = [
    ("passeio", "cena_passeio", "", ""),
    ("aponta", "cena_aponta", "", ""),
    ("pendurada", "cena_pendurada", "", ""),
    ("aviao_like", "cena_aviao", "DEIXA SEU LIKE!", ""),
    ("aviao_comenta", "cena_aviao", "COMENTA AÍ!", ""),
    ("aviao_inscreve", "cena_aviao", "SE INSCREVE!", ""),
]
GERA_IMG = r"D:\flow-imagens\gera_imagem.py"


def _quadro_aviao(roupa, img, texto):
    """1º quadro da cena do avião (ela pilotando + faixa com o texto), pelo gerador de imagem (escreve texto bem)."""
    pasta = FOTOS / "cenas"
    pasta.mkdir(exist_ok=True)
    base = pasta / f"aviao_{roupa}_{re.sub(r'[^A-Z]', '', texto.upper())}.png"
    feitos = sorted(pasta.glob(base.stem + "*.png"))
    if feitos:
        return feitos[0]
    prompt = (f"The SAME anime girl as in the reference image (same face, hair and outfit), flying a small cute red "
              f"cartoon propeller airplane seen from the side, on the left part of the image, smiling and waving, "
              f"towing a long white cloth banner behind the plane with big bold black capital letters that read exactly "
              f"\"{texto}\". Plain pure white background, nothing else, 16:9 wide shot, clean anime cel-shaded style, "
              f"the whole plane and the whole banner visible. No other text, no logo, no watermark.")
    subprocess.run([PY, GERA_IMG, prompt, str(base), "--ref", str(img), "--formato", "16:9", "--quantidade", "1",
                    "--maquinas", "pc1,desktop,x200ma,acer", "--max-contas", "3"], capture_output=True, timeout=1800,
                   creationflags=0x08000000)
    feitos = sorted(pasta.glob(base.stem + "*.png"))
    return feitos[0] if feitos else None


def _subir_drive(nome):
    """Gravação nova -> Drive (o Kaggle copia a mascote_viva de lá a cada pedido)."""
    destino = "manhwa-drive:colab_recap/raiz/D/hipercool-materiais/assets/mascote_viva"
    for ext in (".webm", ".json"):
        if (VIVA / f"{nome}{ext}").exists():
            subprocess.run([r"D:\tools\rclone.exe", "copyto", str(VIVA / f"{nome}{ext}"), f"{destino}/{nome}{ext}"],
                           capture_output=True, timeout=600, creationflags=0x08000000)


def _vez_da_cena(reg):
    cenas = sum(1 for f in reg["feitos"] if f["tema"].startswith("cena_"))
    return cenas < len(reg["feitos"]) - cenas


def uma_cena(reg):
    todas = {k: v for k, v in roupas().items() if not k.startswith("amiga_")}
    feitos = reg["feitos"]
    uso_c = {c[0]: sum(1 for f in feitos if f["fala"] == c[0]) for c in CENAS}
    ruins = {c[0] for c in CENAS if sum(1 for f in reg["falhas"] if f["fala"] == c[0]) >= 4}
    fid, tema, texto, extra = min([c for c in CENAS if c[0] not in ruins] or CENAS, key=lambda c: (uso_c[c[0]], c[0]))
    uso_r = {k: sum(1 for f in feitos if f["roupa"] == k) for k in todas}
    roupa = min(todas, key=lambda k: (uso_r[k], k))
    img = todas[roupa]
    tipo = tema.split("_", 1)[1]
    if tipo == "aviao":
        img = _quadro_aviao(roupa, img, texto)
        if not img:
            log(f"  cena aviao: gerador de imagem não entregou o quadro ({roupa}, {texto}) — fica pra próxima")
            return
    n = sum(1 for f in feitos if f["tema"] == tema) + 1
    nome = f"{tema}_{roupa}_{n:02d}"
    log(f"Veo: {nome} (cena muda {tipo}{' — ' + texto if texto else ''})")
    mp4 = VIVA / f"{nome}.mp4"
    r = subprocess.run([PY, "-u", str(BENCH / "veo_mascote.py"), str(img), nome, texto, extra, "--cena", tipo],
                       cwd=r"D:\veo\beta", capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=3600, creationflags=0x08000000)
    with open(FOTOS / "veo.log", "a", encoding="utf-8") as fh:
        fh.write(f"\n===== {nome} =====\n{r.stdout}{r.stderr}")
    motivo = next((l.strip() for l in reversed((r.stdout + r.stderr).splitlines()) if l.strip()), "?")[:200]
    if not mp4.exists():
        if not any(x in motivo for x in FALHA_DA_CONTA):
            reg["falhas"].append({"fala": fid, "roupa": roupa, "em": datetime.now().isoformat(timespec="seconds"),
                                  "motivo": motivo})
        log(f"  falhou: {nome}: {motivo}")
        return
    if not _e_ela(mp4):
        errado = FOTOS / "_errados_veo"
        errado.mkdir(exist_ok=True)
        mp4.replace(errado / mp4.name)
        reg["falhas"].append({"fala": fid, "roupa": roupa, "em": datetime.now().isoformat(timespec="seconds"),
                              "motivo": "vídeo sem fundo branco"})
        log(f"  descartado: {nome} sem fundo branco")
        return
    subprocess.run([PY, str(BENCH / "mascote_recorte.py"), str(mp4)], capture_output=True, timeout=900,
                   creationflags=0x08000000)
    (VIVA / f"{nome}.json").write_text(json.dumps({"cena": tipo, "texto": texto, "tema": tema, "roupa": roupa},
                                                  ensure_ascii=False), encoding="utf-8")
    reg["feitos"].append({"fala": fid, "tema": tema, "roupa": roupa, "arquivo": f"{nome}.webm",
                          "em": datetime.now().isoformat(timespec="seconds")})
    _subir_drive(nome)
    log(f"  ok: {nome}.webm")


# falha da conta/automação do Flow (não da roupa): tenta outra conta e não conta contra a roupa
FALHA_DA_CONTA = ("SO_NOTEBOOK", "nenhuma conta", "travada", "SessaoExpirada", "texto nao entrou", "caixa de prompt",
                  "Recaptcha", "CreditosEsgotados", "sem video novo baixavel")


def log(msg):
    linha = f"[{datetime.now():%Y-%m-%d %H:%M}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(linha + "\n")


def _reg():
    try:
        return json.loads(REG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # as 3 primeiras (28/10, roupa de jaqueta) já estão no arsenal
        antigos = [("insc1", "inscreva", "inscreva_01"), ("com1", "comenta", "comenta_01"),
                   ("susto", "reacao_susto", "reacao_susto_01")]
        return {"feitos": [{"fala": f, "tema": t, "roupa": "jaqueta", "arquivo": a + ".webm", "em": "2026-10-28"}
                           for f, t, a in antigos if (VIVA / f"{a}.webm").exists()], "falhas": []}


def _borda_branca(png, minimo=0.9):
    """Fração da borda da imagem que é branco de estúdio (o recorte só tira branco)."""
    from PIL import Image
    im = Image.open(png).convert("L").resize((120, 200))
    w, h = im.size
    px = [im.getpixel((x, y)) for x in range(w) for y in (0, h - 1)] + [im.getpixel((x, y)) for y in range(h) for x in (0, w - 1)]
    return sum(1 for v in px if v >= 235) / len(px) >= minimo


# 30/10 dona: "não fazer mais da mascote com roupa normal, a original" — o biquíni verde-amarelo comum dela
ORIGINAIS = {"biquini_brasil", "biquini_praia"}


def roupas():
    """{roupa: imagem} — a principal (todas as fantasias) e as amigas (prefixo amiga_)."""
    # 28/10 dona: só ela EM PÉ andando (pasta andando/, bench\gerar_waifu2.py andando) — sentada/deitada não serve
    r = {}
    for p in sorted(FOTOS.glob("andando/*_1.png")):
        if not _borda_branca(p):  # 29/10: 07_biquini_praia tinha praia no fundo e o Veo gravou o retângulo da praia
            continue
        base = p.stem[:-2]
        if base.split("_", 1)[-1] in ORIGINAIS:
            continue
        r[base if base.startswith("amiga_") else base.split("_", 1)[1]] = p
    return r


def escolher(reg):
    feitos = reg["feitos"]
    todas = roupas()
    amiga = sum(1 for f in feitos if f["roupa"].startswith("amiga_"))
    vez_amiga = any(k.startswith("amiga_") for k in todas) and amiga < (len(feitos) + 1) // 4
    # roupa que o Veo recusou 3x (biquíni pode bater na política) sai da roda
    ruins = {k for k in todas if sum(1 for f in reg["falhas"] if f["roupa"] == k) >= 3}
    cand = {k: v for k, v in todas.items() if k.startswith("amiga_") == vez_amiga and k not in ruins} or \
        {k: v for k, v in todas.items() if k not in ruins}
    uso_r = {k: sum(1 for f in feitos if f["roupa"] == k) for k in cand}
    # 30/10 dona: "falta variedade de roupa" — sem preferência por biquíni: sempre a fantasia menos usada
    roupa = min(cand, key=lambda k: (uso_r[k], k))
    ja = {(f["fala"], f["roupa"]) for f in feitos}
    uso_f = {f[0]: sum(1 for x in feitos if x["fala"] == f[0]) for f in FALAS}
    # 30/10 dona: "o máximo possível de reações com roupas diferentes" — na roupa da vez, reação primeiro
    fala = min([f for f in FALAS if (f[0], roupa) not in ja] or FALAS,
               key=lambda f: (not f[1].startswith("reacao_"), uso_f[f[0]], f[0]))
    return roupa, cand[roupa], fala


def _e_ela(mp4):
    """Quadro com bastante branco puro = fundo de estúdio dela (o vídeo errado era um homem num telhado)."""
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-ss", "1", "-i", str(mp4), "-frames:v", "1", "-vf", "scale=90:160",
                            "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    return bool(bruto) and sum(1 for b in bruto if b >= 235) / len(bruto) >= 0.25


def _vez_da_dupla(reg):
    """02/11: 1 a cada 3 gravações é uma conversa Maria x amiga (até cada dupla ter as 2 partes gravadas)."""
    feitos = reg["feitos"]
    return any(not _dupla_completa(reg, d[0]) for d in DUPLAS) and len(feitos) % 3 == 2


def _dupla_completa(reg, did):
    temas = {f["tema"] for f in reg["feitos"]}
    return f"{did}_a" in temas and f"{did}_b" in temas


def uma_dupla(reg):
    """Grava a parte que falta da próxima conversa: _a = Maria (roupa dela menos usada), _b = amiga respondendo."""
    did, emo, fala_a, fala_b = next(d for d in DUPLAS if not _dupla_completa(reg, d[0]))
    temas = {f["tema"] for f in reg["feitos"]}
    parte = "a" if f"{did}_a" not in temas else "b"
    todas = roupas()
    cand = {k: v for k, v in todas.items() if k.startswith("amiga_") == (parte == "b")}
    if not cand:
        log(f"  dupla {did}: sem foto de {'amiga' if parte == 'b' else 'Maria'}")
        return
    uso = {k: sum(1 for f in reg["feitos"] if f["roupa"] == k) for k in cand}
    roupa = min(cand, key=lambda k: (uso[k], k))
    fala = fala_a if parte == "a" else fala_b
    # a amiga RESPONDE: olha pro lado (onde a Maria está) antes de falar; a Maria fala olhando pra amiga e pro público
    mov = ("She turns to her friend beside her, points at the screen and talks excitedly" if parte == "a" else
           "She turns to her friend beside her, nods and answers with an expressive face, then looks at the camera")
    nome = (f"dupla_{did[5:]}_a_andando_{roupa}_01" if parte == "a" else f"{roupa}_andando_dupla_{did[5:]}_b_01")
    lado = "esquerda" if parte == "a" else "direita"
    log(f"Veo: {nome} ({'Maria' if parte == 'a' else 'amiga'}: {fala})")
    mp4 = VIVA / f"{nome}.mp4"
    r = subprocess.run([PY, "-u", str(BENCH / "veo_mascote.py"), str(cand[roupa]), nome, fala, mov, "--entra", lado],
                       cwd=r"D:\veo\beta", capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=3600, creationflags=0x08000000)
    with open(FOTOS / "veo.log", "a", encoding="utf-8") as fh:
        fh.write(f"\n===== {nome} =====\n{r.stdout}{r.stderr}")
    if not mp4.exists() or not _e_ela(mp4):
        motivo = next((l.strip() for l in reversed((r.stdout + r.stderr).splitlines()) if l.strip()), "?")[:200]
        log(f"  dupla falhou: {nome}: {motivo}")
        return
    subprocess.run([PY, str(BENCH / "mascote_recorte.py"), str(mp4)], capture_output=True, timeout=900,
                   creationflags=0x08000000)
    (VIVA / f"{nome}.json").write_text(json.dumps({"fala": fala, "tema": f"{did}_{parte}", "roupa": roupa,
                                                   "lado": lado, "dupla": did, "parte": parte, "emocao": emo},
                                                  ensure_ascii=False), encoding="utf-8")
    reg["feitos"].append({"fala": f"{did}_{parte}", "tema": f"{did}_{parte}", "roupa": roupa,
                          "arquivo": f"{nome}.webm", "em": datetime.now().isoformat(timespec="seconds")})
    _subir_drive(nome)
    log(f"  ok: {nome}.webm")


def um_video(reg):
    roupa, img, (fid, tema, fala, mov) = escolher(reg)
    n = sum(1 for f in reg["feitos"] if f["tema"] == tema) + 1
    # "_andando_" = paisagem 16:9 com ela entrando por um lado (o mascote_overlay põe em tela cheia, ela anda no vídeo)
    nome = f"{tema}_andando_{roupa}_{n:02d}" if not roupa.startswith("amiga_") else f"{roupa}_andando_{tema}_{n:02d}"
    lado = "esquerda" if len(reg["feitos"]) % 2 == 0 else "direita"
    log(f"Veo: {nome} entrando pela {lado} ({fala})")
    mp4 = VIVA / f"{nome}.mp4"
    for _ in range(3):  # conta só-notebook com os notebooks ocupados = outra conta na próxima tentativa
        r = subprocess.run([PY, "-u", str(BENCH / "veo_mascote.py"), str(img), nome, fala, mov, "--entra", lado],
                           cwd=r"D:\veo\beta",
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600,
                           creationflags=0x08000000)
        with open(FOTOS / "veo.log", "a", encoding="utf-8") as fh:
            fh.write(f"\n===== {nome} =====\n{r.stdout}{r.stderr}")
        motivo = next((l.strip() for l in reversed((r.stdout + r.stderr).splitlines()) if l.strip()), "?")[:200]
        if mp4.exists() or not any(x in motivo for x in FALHA_DA_CONTA):
            break
        log(f"  conta/Flow com problema ({motivo[:80]}) — outra tentativa")
    if not mp4.exists():
        if any(x in motivo for x in FALHA_DA_CONTA):
            log(f"  sem conta Veo livre agora — {nome} fica pra próxima rodada")
            return
        reg["falhas"].append({"fala": fid, "roupa": roupa, "em": datetime.now().isoformat(timespec="seconds"),
                              "motivo": motivo})
        log(f"  falhou: {nome}: {motivo}")
        return
    if not _e_ela(mp4):
        errado = FOTOS / "_errados_veo"
        errado.mkdir(exist_ok=True)
        mp4.replace(errado / mp4.name)
        reg["falhas"].append({"fala": fid, "roupa": roupa, "em": datetime.now().isoformat(timespec="seconds"),
                              "motivo": "vídeo não é ela (sem fundo branco)"})
        log(f"  descartado: {nome} não é ela")
        return
    subprocess.run([PY, str(BENCH / "mascote_recorte.py"), str(mp4)], capture_output=True, timeout=900,
                   creationflags=0x08000000)
    # 29/10: o longo usa o texto (legenda) e o lado (variação de posição) na pausa dela (mascote_overlay.pausa_viva)
    (VIVA / f"{nome}.json").write_text(json.dumps({"fala": fala, "tema": tema, "roupa": roupa, "lado": lado},
                                                  ensure_ascii=False), encoding="utf-8")
    reg["feitos"].append({"fala": fid, "tema": tema, "roupa": roupa, "arquivo": f"{nome}.webm",
                          "em": datetime.now().isoformat(timespec="seconds")})
    log(f"  ok: {nome}.webm")


def main():
    # 30/10: só as fotos em pé andando (as sentadas/deitadas de biquini/cosplay não servem desde 28/10) e as amigas
    for etapa in ("amigas", "andando"):
        subprocess.run([PY, "-u", str(BENCH / "gerar_waifu2.py"), etapa], capture_output=True, timeout=4 * 3600,
                       creationflags=0x08000000)
    reg = _reg()
    for _ in range(VIDEOS_POR_RODADA):
        try:
            if "--dupla" in sys.argv or _vez_da_dupla(reg):
                uma_dupla(reg)
            elif "--cena" in sys.argv or _vez_da_cena(reg):
                uma_cena(reg)
            else:
                um_video(reg)
        except Exception as e:  # noqa: BLE001
            log(f"  erro: {type(e).__name__}: {e}")
        REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
