"""Vídeo PROFISSIONAL de produto (dono 25/10): Reel de 20–30 s que vende com confiança.

Estrutura (roteiro de agentes.py):
  abertura   — cartão "pergunta de cliente" sobre a imagem do 1º bloco (aprendizado c9627e2c)
  bloco 1..3 — imagem do Flow com movimento de câmera | conversa de WhatsApp animada (chat_ui) | cena do Veo
  cartão     — marca, o que o produto faz, "Link no perfil", @conta
Camada de efeitos desenhada quadro a quadro (uma faixa .mov com transparência, sobreposta no fim):
  frase fixa no topo na cor da marca (9a1f9f1f/8d5ffe30), tópico numerado "1 · O problema" (82b76de6), legenda
  KARAOKÊ com a palavra falada acesa na cor da marca (ffb4c8fe/62c7ec8c/e4fbdf10), barrinha de progresso no topo.
Áudio: narradora edge-tts gravada por trecho (o tempo de cada palavra vem do próprio edge = legenda exata), trilha
de licença livre baixinha, −14 LUFS.

    python -m produto.video --conta futebolcom.ia2 [--veo] [--saida D:\\...]
"""
import argparse
import asyncio
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

BIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
from produto import agentes, ajustes, chat_ui  # noqa: E402
from produto import kit as kit_mod  # noqa: E402

try:  # COMUM (dona 02/11): cor igualada entre cenas de vídeo; sem a lib segue como antes
    import realce_visual  # noqa: E402
except Exception:  # noqa: BLE001
    realce_visual = None

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
W, H, FPS = 1080, 1920, 30
FILA = Path(r"D:\video-fila\produto_fila")
TMP_RAIZ = Path(r"D:\video-fila\produto_tmp")
TRILHAS = [r"D:\hipercool-materiais\assets\trilhas\calm_chill.mp3",            # Serene View (Mixkit), licença livre
           r"D:\hipercool-materiais\assets\trilhas\Beyond - Patrick Patrikios.mp3"]
VOL_TRILHA = 0.13
XF = 0.35            # duração das transições
FOLGA = 0.28         # respiro depois de cada fala
# áreas (Reels cobre ~250 px no topo e ~380 px embaixo com a interface: nada importante fora delas)
TOPO = (60, 150, 1020, 290)        # frase fixa
# o tópico numerado fica logo ABAIXO da frase (altura calculada; 25/10: em y fixo encostava na frase de 2 linhas e a
# trava final viu "caixa preta cortada")
AREA_CHAT = (70, 490, 1010, 1290)
LEGENDA_Y = 1280                   # faixa da legenda 1280..1580: acima da legenda/botões do Reels


def log_padrao(m):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def _dur(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, timeout=60)
    return float(r.stdout.strip() or 0)


VITRINE = Path(r"D:\hipercool-materiais\produtos_ultimo_video")  # dono 26/10: pasta aberta com o último vídeo
OPINIOES = VITRINE / "OPINIOES.txt"


def vitrine(mp4, side, status):
    """Cópia do vídeo que acabou de sair (aprovado, reprovado ou teste) na pasta que fica aberta pro dono ver.
    Mantém os 6 mais novos; o mais novo começa com '0_ULTIMO'. OPINIOES.txt é dele (nunca sobrescrito)."""
    try:
        VITRINE.mkdir(parents=True, exist_ok=True)
        for velho in VITRINE.glob("0_ULTIMO_*"):
            velho.rename(velho.with_name(velho.name.replace("0_ULTIMO_", "", 1)))
        destino = VITRINE / f"0_ULTIMO_{Path(mp4).name}"
        shutil.copy2(mp4, destino)
        lap = side.get("lapidar") or {}
        destino.with_suffix(".txt").write_text(
            f"{status} — {side.get('marca')} ({side.get('conta')}) — {datetime.now():%d/%m %H:%M}\n"
            f"Título: {side.get('titulo')}\nFormato: {side.get('variante')} | dono nas cenas {side.get('cenas_dono_feitas')}"
            f" | Veo comercial {side.get('veo_broll_feitos')} | voz {side.get('voz')}\n"
            f"Nota do júri: {lap.get('nota')} {lap.get('notas') or ''}\n"
            f"Trava: {(side.get('trava_final') or {}).get('motivos') or 'ok'}\n"
            f"Original: {mp4}\n\nOpinião? Escreva no OPINIOES.txt desta pasta (o nome do vídeo + o que achou).\n",
            "utf-8")
        if not OPINIOES.exists():
            OPINIOES.write_text("Escreva aqui o que achou de cada vídeo (nome do vídeo: opinião). "
                                "A sessão da linha PRODUTOS lê a cada vídeo novo.\n\n", "utf-8")
        mp4s = sorted((p for p in VITRINE.glob("*.mp4")), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in mp4s[6:]:
            p.unlink(missing_ok=True)
            p.with_suffix(".txt").unlink(missing_ok=True)
    except Exception as e:  # noqa: BLE001
        log_padrao(f"  [vitrine] não copiei: {type(e).__name__}: {str(e)[:100]}")


_SEM_MEMORIA = ("Cannot allocate memory", "get_buffer() failed", "Out of memory", "out of memory")


def _ff(args, timeout=900):
    # 26/10 15:16: "Cannot allocate memory" com o PC1 sem RAM derrubou o VPS depois de 3 cenas do dono prontas ->
    # falta de memória espera e tenta de novo (até ~6 min) em vez de jogar o vídeo fora
    for tentativa in range(4):
        r = subprocess.run([FF, "-y", "-v", "error", *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        if not r.returncode:
            return
        if tentativa < 3 and any(s in r.stderr for s in _SEM_MEMORIA):
            log_padrao(f"  [ffmpeg] sem memória — espero {60 * (tentativa + 1)} s e tento de novo")
            time.sleep(60 * (tentativa + 1))
            continue
        raise RuntimeError(f"ffmpeg: {r.stderr[-600:]}")


# ───────────────────────────── narração ─────────────────────────────

async def _edge(texto, mp3, voz, ritmo):
    import edge_tts
    palavras = []
    with open(mp3, "wb") as f:
        async for ch in edge_tts.Communicate(texto, voz, rate=ritmo, boundary="WordBoundary").stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                ini = ch["offset"] / 1e7
                palavras.append((ch["text"], round(ini, 3), round(ini + ch["duration"] / 1e7, 3)))
    return palavras


VOZ_RESERVA = "pt-BR-FranciscaNeural"  # 26/10: a Thalita (multilíngue) falhou ao acaso em várias frases; a Francisca não


def narrar(texto, mp3, kit, log=log_padrao, esperas=(15, 30, 60, 120, 0)):
    """(mp3, palavras [(palavra, ini, fim)], duração). O edge às vezes devolve vazio (NoAudioReceived); 26/10
    06:15–06:27 ficou fora ~15 min e as 3 tentativas em 6 s derrubaram 3 vídeos -> 5 tentativas, espera crescente."""
    for tentativa, espera in enumerate(esperas):
        try:
            palavras = asyncio.run(_edge(texto, str(mp3), kit["voz"], kit["ritmo"]))
            if palavras and Path(mp3).stat().st_size > 3000:
                return mp3, palavras, _dur(mp3)
        except Exception as e:  # noqa: BLE001
            log(f"  [voz] edge falhou ({kit['voz'][6:14]}, {type(e).__name__}) — tentativa {tentativa + 1}/{len(esperas)}")
        time.sleep(espera)
    raise RuntimeError(f"narração (edge-tts) falhou {len(esperas)}x")


# ───────────────────────────── imagens ─────────────────────────────

VOZES_CFG = Path(__file__).resolve().parents[2] / "config" / "produto_vozes.json"
PY_VOZES = r"D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe"
VOZ_CLONADA = r"D:\hipercool-materiais\bin\voz_clonada.py"


def clonar_vozes(audio, nomes, pasta, log=log_padrao):
    """28/10 (dona: "Francisca é voz ruim; temos vozes clonadas muito melhores... cuidado com o público"): os trechos
    da narradora passam pelo RVC (voz_clonada.py lote, 1 processo) com uma voz sorteada de config\\produto_vozes.json.
    O RVC mantém a duração -> os tempos das palavras do edge continuam valendo. Qualquer falha ou duração diferente =
    devolve None e o vídeo inteiro fica na voz base (nunca 2 vozes de narradora no mesmo vídeo)."""
    try:
        cfg = json.loads(VOZES_CFG.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return None
    if not cfg.get("vozes") or not nomes:  # 28/10 (dona): sem "ligado" — voz edge pura nunca vai pro vídeo
        return None
    voz = random.choice(cfg["vozes"])
    lista, novos = [], {}
    for nome in nomes:
        wav_in = pasta / f"base_{nome}.wav"
        _ff(["-i", str(audio[nome][0]), "-ar", "32000", "-ac", "1", str(wav_in)])
        novos[nome] = pasta / f"voz_{voz}_{nome}.wav"
        lista.append({"saida": str(novos[nome]), "tom_base": "2_edge_francisca", "entrada": str(wav_in)})
    arq = pasta / "vozes_lote.json"
    arq.write_text(json.dumps(lista), "utf-8")
    t0 = time.time()
    onde = "PC2" if cfg.get("pc2", True) and _clonar_pc2(voz, nomes, pasta, novos, int(cfg.get("prazo_s", 1800)), log) \
        else "PC1"
    if onde == "PC1":
        try:
            subprocess.run([PY_VOZES, VOZ_CLONADA, "lote", voz, str(arq)], capture_output=True,
                           timeout=int(cfg.get("prazo_s", 1800)), creationflags=0x08000000 | 0x00004000)
        except subprocess.TimeoutExpired:
            log(f"  [voz] {voz}: o clone passou de {cfg.get('prazo_s', 1800)} s — fica a voz base")
            return None
    for nome in nomes:
        if not novos[nome].exists() or abs(_dur(novos[nome]) - audio[nome][2]) > 0.2:
            log(f"  [voz] {voz}: trecho {nome} não saiu certo — fica a voz base no vídeo todo")
            return None
    for nome in nomes:
        audio[nome] = (novos[nome], audio[nome][1], audio[nome][2])
    log(f"  [voz] narração com a voz clonada {voz} ({len(nomes)} trechos, {(time.time() - t0) / 60:.1f} min no {onde})")
    return voz


def _clonar_pc2(voz, nomes, pasta, novos, prazo, log):
    """28/10: no PC1 carregado o clone levou 10,9 min para 5 s de fala -> roda no PC2 (o hipercool já tem lá o Applio,
    o venv_vozes e os modelos em C:\\hipercool-materiais; o `subst D: C:\\` faz os caminhos D:\\ valerem). 3 conexões:
    tar dos wavs base -> lote lá -> tar das vozes de volta. False = o PC1 faz."""
    from produto.editor import TAR, _ssh_pc2
    tid = pasta.name
    remoto = f"C:\\produto-pc2\\vozes\\{tid}"
    pacote = pasta / "vozes_ida.tar"
    try:
        lista = [{"saida": f"{remoto}\\{novos[n].name}", "tom_base": "2_edge_francisca",
                  "entrada": f"{remoto}\\base_{n}.wav"} for n in nomes]
        (pasta / "vozes_lote_pc2.json").write_text(json.dumps(lista), "utf-8")
        r = subprocess.run([TAR, "-cf", str(pacote), "-C", str(pasta), "vozes_lote_pc2.json",
                            *[f"base_{n}.wav" for n in nomes]], capture_output=True, timeout=120)
        if r.returncode:
            raise RuntimeError(f"tar: {r.stderr[-150:]!r}")
        r = subprocess.run(["scp", "-q", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", str(pacote),
                            "pc2:C:/produto-pc2/pacotes/"], capture_output=True, input=b"", timeout=300)
        if r.returncode:
            raise RuntimeError(f"scp ida: {r.stderr[-150:]!r}")
        ps = f"""$ErrorActionPreference='Continue'
cmd /c "subst D: C:\\ >nul 2>&1"
$m=[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)
if ($m -lt 2) {{ "SEM_RAM $m GB"; exit 4 }}
Get-ChildItem C:\\produto-pc2\\vozes -Directory -EA SilentlyContinue | Where-Object {{ $_.LastWriteTime -lt (Get-Date).AddHours(-6) }} | Remove-Item -Recurse -Force -EA SilentlyContinue
New-Item -ItemType Directory -Force {remoto} | Out-Null
Set-Location {remoto}
& {TAR} -xf C:\\produto-pc2\\pacotes\\{pacote.name}
Remove-Item C:\\produto-pc2\\pacotes\\{pacote.name} -Force
& C:\\hipercool-materiais\\python\\venv_vozes\\Scripts\\python.exe C:\\hipercool-materiais\\bin\\voz_clonada.py lote {voz} vozes_lote_pc2.json 2>&1 | Select-Object -Last 3
& {TAR} -cf volta.tar {' '.join(novos[n].name for n in nomes)}
if ($LASTEXITCODE -eq 0) {{ 'VOZES_OK' }}"""
        rc, txt = _ssh_pc2(ps, prazo)
        if "VOZES_OK" not in txt:
            raise RuntimeError(txt.strip()[-250:] or f"ssh rc={rc}")
        volta = pasta / "vozes_volta.tar"
        r = subprocess.run(["scp", "-q", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
                            f"pc2:C:/produto-pc2/vozes/{tid}/volta.tar", str(volta)], capture_output=True,
                           input=b"", timeout=300)
        if r.returncode:
            raise RuntimeError(f"scp volta: {r.stderr[-150:]!r}")
        subprocess.run([TAR, "-xf", str(volta), "-C", str(pasta)], capture_output=True, timeout=120)
        volta.unlink(missing_ok=True)
        return all(novos[n].exists() for n in nomes)
    except Exception as e:  # noqa: BLE001
        log(f"  [voz] PC2 não clonou ({type(e).__name__}: {str(e)[-180:]}) — faço aqui")
        return False
    finally:
        pacote.unlink(missing_ok=True)


def _f(caminho, tam):
    return ImageFont.truetype(caminho, tam)


def _quebrar(d, texto, f, largura):
    linhas, atual = [], ""
    for p in texto.split():
        t = (atual + " " + p).strip()
        if d.textlength(t, font=f) <= largura or not atual:
            atual = t
        else:
            linhas.append(atual)
            atual = p
    return linhas + ([atual] if atual else [])


def fundo_marca(kit):
    """Sem imagem boa: degradê da marca com brilho suave (nunca tela lisa morta)."""
    im = Image.new("RGB", (W, H), kit["escuro"])
    d = ImageDraw.Draw(im)
    cor = kit["cor"]
    for y in range(H):
        a = (y / H) ** 1.6 * 0.5
        d.line([(0, y), (W, y)], fill=tuple(int(kit["escuro"][i] * (1 - a) + cor[i] * a) for i in range(3)))
    brilho = Image.new("L", (W, H), 0)
    ImageDraw.Draw(brilho).ellipse((-300, -200, 900, 900), fill=90)
    brilho = brilho.filter(ImageFilter.GaussianBlur(160))
    return Image.composite(Image.new("RGB", (W, H), tuple(min(255, c + 60) for c in cor)), im, brilho)


BANCO = Path(r"D:\video-fila\produto_banco")   # imagens aprovadas por marca (reserva quando o Flow falha)
_PERG_IMG = ('Esta imagem vai ilustrar um anúncio profissional em vídeo. Responda SÓ JSON: {"texto_em_destaque": true '
             'se há letras/palavras GRANDES ou legíveis em destaque (placa, cardápio, tela, logotipo, embalagem) — letras '
             'pequenas e desfocadas no fundo NÃO contam; "deformado": true se há pessoa, mão, rosto ou objeto torto, '
             'derretido ou impossível; "improprio": true se há nudez, violência ou algo ofensivo; "nota": 1 a 10 '
             '(bonita, profissional, parece foto real?)}')


def imagem(kit, prompt_en, destino, log=log_padrao):
    """Imagem do Flow (Nano Banana, 0 crédito) conferida por visão; None se não saiu boa. 25/10: a checagem do
    carrossel (qualquer letra = reprova) recusou 2 de 3 cenas de restaurante por placa/cardápio no fundo -> no vídeo
    só reprova texto EM DESTAQUE, e o pedido já pede cena sem placas."""
    sys.path.insert(0, r"D:\flow-imagens")
    pr = (prompt_en.strip().rstrip(".") + ". Clean composition without signs, menu boards, labels, packaging text or "
          "readable screens. Professional commercial photography, natural light, realistic. No text, no letters, no "
          "logos, no watermark.")
    for tentativa in range(2):
        try:
            from gera_imagem import gerar_imagem
            arq = gerar_imagem(pr, destino, formato="9:16", log=lambda m: None)[0]
            im = Image.open(arq).convert("RGB")
        except Exception as e:  # noqa: BLE001
            log(f"  [imagem] Flow falhou: {str(e)[:140]}")
            return None
        buf = __import__("io").BytesIO()
        im.copy().resize((im.width // 2, im.height // 2)).save(buf, "JPEG", quality=85)
        try:
            v = _visao(buf.getvalue(), _PERG_IMG)
        except Exception as e:  # noqa: BLE001
            log(f"  [imagem] visão indisponível ({type(e).__name__}) — não uso imagem sem conferir")
            return None
        if not (v.get("texto_em_destaque") or v.get("deformado") or v.get("improprio")) and int(v.get("nota") or 0) >= 6:
            im = ImageOps.fit(im, (W, H), method=Image.LANCZOS)
            pasta = BANCO / kit["conta"]
            pasta.mkdir(parents=True, exist_ok=True)
            im.save(pasta / f"{datetime.now():%Y%m%d_%H%M%S}_{random.randint(100, 999)}.jpg", quality=92)
            (pasta / "_prompts.jsonl").open("a", encoding="utf-8").write(
                json.dumps({"prompt": prompt_en, "quando": datetime.now().isoformat(timespec="seconds")},
                           ensure_ascii=False) + "\n")
            return im
        log(f"  [imagem] reprovada (tentativa {tentativa + 1}): {v}")
    return None


def do_banco(kit, evitar=()):
    """Uma imagem já aprovada desta marca (a menos usada recentemente), para quando o Flow não entrega."""
    pasta = BANCO / kit["conta"]
    fotos = [p for p in pasta.glob("*.jpg") if p.name not in evitar] if pasta.exists() else []
    if not fotos:
        return None, None
    p = random.choice(fotos)
    return ImageOps.fit(Image.open(p).convert("RGB"), (W, H)), p.name


CHIP_Y = (960, 1105)  # destaques empilhados logo acima da legenda (1280..1580)


def _chip(kit, texto):
    """Destaque da fala: cartão branco com ✓ na cor da marca (entra quando a narradora diz o trecho)."""
    f = _f(kit_mod.FONTE_XBOLD, 54)
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lw = int(d.textlength(texto, font=f))
    larg, alt = min(lw + 170, W - 140), 112
    im = Image.new("RGBA", (larg + 20, alt + 24), (0, 0, 0, 0))
    sombra = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((8, 14, larg + 8, alt + 14), radius=30, fill=(0, 0, 0, 120))
    im = Image.alpha_composite(im, sombra.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, larg, alt), radius=30, fill=(255, 255, 255, 248))
    d.ellipse((22, 22, 90, 90), fill=kit["cor"])
    d.line((40, 57, 52, 70, 73, 42), fill=kit["texto"], width=9, joint="curve")
    d.text((112, (alt - 62) // 2), texto, font=f, fill=(22, 22, 26))
    return im


def seg_imagem(img, dur, saida, direcao=0, kit=None, chips=()):
    """Imagem parada vira cena: zoom lento + deslize (Ken Burns) com interpolação suave (escala 2x antes).
    chips = [(texto, t_local)]: 28/10 (júri: "foto parada", "slide", tela desligada da fala, mesmo com a medida de
    movimento 5–15%: zoom na foto inteira não conta como movimento) -> destaques entram deslizando quando ditos e
    sobem devagar até o fim da cena (elemento em movimento a cena toda)."""
    src = saida.with_suffix(".png")
    img.save(src)
    n = int(math.ceil(dur * FPS))
    # zoompan sobre a imagem 2x maior: sem o "tremido" do zoompan em resolução final
    # 26/10 (verificadores, "movimento" 4 em todos): 10% em 8 s parecia foto parada -> 16% e deslize maior
    zz, pan = 1 + ajustes.valor("kenburns_zoom"), ajustes.valor("kenburns_pan")  # botões do melhorador
    z0, z1 = (1.0, zz) if direcao % 2 == 0 else (zz, 1.0)
    zexpr = f"{z0}+({z1 - z0})*on/{n}"
    xexpr = "iw/2-(iw/zoom/2)" + (f"+on*{pan}" if direcao % 3 == 1 else f"-on*{pan}" if direcao % 3 == 2 else "")
    kb = f"scale={W * 2}:{H * 2},zoompan=z='{zexpr}':x='{xexpr}':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},setsar=1"
    chips = [(t, max(0.15, min(tl, dur - 0.9))) for t, tl in chips if t][:len(CHIP_Y)] if kit and \
        ajustes.valor("destaques_tela") else []
    ent, fc, ultimo, pngs = ["-loop", "1", "-i", str(src)], [f"[0:v]{kb}[b0]"], "b0", []
    for i, (texto, t0) in enumerate(chips):
        png = saida.with_suffix(f".chip{i}.png")
        _chip(kit, texto).save(png)
        pngs.append(png)
        ent += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(png)]
        fc.append(f"[{i + 1}:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.3:alpha=1[c{i}]")
        x = f"70-160*pow(max(0\\,1-(t-{t0:.2f})/0.35)\\,3)"  # desliza da esquerda (0,35 s, freia no fim)
        y = f"{CHIP_Y[i]}-26*max(0\\,t-{t0:.2f})/{max(dur - t0, 0.5):.2f}"  # e sobe 26 px até o fim da cena
        fc.append(f"[{ultimo}][c{i}]overlay=x='{x}':y='{y}':eval=frame[b{i + 1}]")
        ultimo = f"b{i + 1}"
    fc.append(f"[{ultimo}]format=yuv420p[v]")
    try:
        _ff([*ent, "-filter_complex", ";".join(fc), "-map", "[v]", "-frames:v", str(n), "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "18", str(saida)])
    finally:
        src.unlink(missing_ok=True)
        for p in pngs:
            p.unlink(missing_ok=True)
    return saida


def tempos_destaques(destaques, palavras, ofs_local):
    """[(texto, t_local)]: cada destaque entra 0,1 s antes da 1ª palavra dele na voz (palavras = [(w, ini, fim)] do
    trecho; ofs_local = onde o trecho começa dentro da cena)."""
    from produto.agentes import _norm
    ws = [_norm(w) for w, _, _ in palavras]
    out, de = [], 0
    for d in destaques or []:
        ps = _norm(d).split()
        i = next((j for j in range(de, len(ws) - len(ps) + 1) if ws[j:j + len(ps)] == ps), None)
        if i is None:  # o edge separou diferente: acha só a 1ª palavra
            i = next((j for j in range(de, len(ws)) if ps and ws[j] == ps[0]), None)
        if i is not None:
            out.append((d, ofs_local + palavras[i][1] - 0.1))
            de = i + 1
    return out


def _rosto_caixa(img):
    """(x, y, l, a) do maior rosto da imagem PIL (YuNet, o mesmo da foto na hora) ou None."""
    try:
        import cv2
        import numpy as np
        det = cv2.FaceDetectorYN.create(r"D:\hipercool-materiais\models\rosto\yunet.onnx", "", (320, 320), 0.7, 0.3,
                                        5000)
        f = 0.5
        bgr = cv2.cvtColor(np.array(img.convert("RGB").resize((int(img.width * f), int(img.height * f)))),
                           cv2.COLOR_RGB2BGR)
        det.setInputSize((bgr.shape[1], bgr.shape[0]))
        _, achados = det.detect(bgr)
        if achados is None or not len(achados):
            return None
        r = max(achados, key=lambda a: a[2] * a[3])
        return tuple(float(v) / f for v in r[:4])
    except Exception:  # noqa: BLE001 - sem cv2/modelo: fica como antes
        return None


def _livrar_cabeca(foto, y_fim_cartao):
    """28/10 (júri: "cartão da pergunta cobre a testa/topo da cabeça do apresentador" na Follow-up e na Fábrica):
    se a cabeça (rosto + 45% de folga pro cabelo) sobe acima do fim do cartão, a foto DESCE o necessário (até 380 px)
    e o alto vira a própria foto borrada."""
    caixa = _rosto_caixa(foto)
    if not caixa:
        return foto
    _, y, _, a = caixa
    topo_cabeca = y - 0.45 * a
    desce = int(min(max(y_fim_cartao + 40 - topo_cabeca, 0), 380))
    if desce <= 0:
        return foto
    fundo = foto.resize((W, H)).filter(ImageFilter.GaussianBlur(28))
    fundo.paste(foto, (0, desce))
    # costura suave entre o borrado e a foto
    faixa = Image.linear_gradient("L").rotate(180).resize((W, 60))
    fundo.paste(foto.crop((0, 0, W, 60)).filter(ImageFilter.GaussianBlur(6)), (0, desce), faixa)
    return fundo


def card_pergunta(kit, pergunta, fundo, com_rosto=False):
    """Abertura: pergunta de cliente num cartão estilo comentário/mensagem sobre o fundo desfocado.
    com_rosto (26/10, diretor: "slide de Canva, sem rosto humano"): fundo = foto do dono, pouco desfocada, e o cartão
    sobe para o alto e o rosto (meio da foto) fica à mostra.
    fundo=None: só o cartão sobre transparente (vai por cima de um clipe do Veo: seg_veo_com_cartao)."""
    if fundo is None:
        base = Image.new("RGBA", (W, H), kit["escuro"] + (90,))
    elif com_rosto:
        fundo = ImageOps.fit(fundo, (W, H), centering=(0.5, 0.35))
        d0 = ImageDraw.Draw(fundo.copy())
        fundo = _livrar_cabeca(fundo, 170 + len(_quebrar(d0, pergunta, _f(chat_ui.UI_SB, 58), W - 260)) * 74 + 190)
        base = Image.blend(fundo.filter(ImageFilter.GaussianBlur(3)), Image.new("RGB", (W, H), kit["escuro"]), 0.3)
    else:
        base = Image.blend(fundo.filter(ImageFilter.GaussianBlur(14)), Image.new("RGB", (W, H), kit["escuro"]), 0.5)
    im = base.convert("RGBA")
    d = ImageDraw.Draw(im)
    f_txt, f_rot = _f(chat_ui.UI_SB, 58), _f(chat_ui.UI_SB, 34)
    linhas = _quebrar(d, pergunta, f_txt, W - 260)
    alt = len(linhas) * 74 + 190
    x0, y0 = 90, (170 if com_rosto else (H - alt) // 2 - 80)  # com o dono: cartão no alto, rosto livre no meio
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((x0 + 10, y0 + 22, W - x0 + 10, y0 + alt + 22), radius=48,
                                             fill=(0, 0, 0, 160))
    im = Image.alpha_composite(im, sombra.filter(ImageFilter.GaussianBlur(24)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0, y0, W - x0, y0 + alt), radius=48, fill=(255, 255, 255, 250))
    d.ellipse((x0 + 40, y0 + 40, x0 + 112, y0 + 112), fill=(205, 205, 210))
    d.ellipse((x0 + 62, y0 + 52, x0 + 90, y0 + 80), fill=(245, 245, 247))
    d.pieslice((x0 + 50, y0 + 80, x0 + 102, y0 + 132), 180, 360, fill=(245, 245, 247))
    d.text((x0 + 134, y0 + 56), "Pergunta frequente", font=f_rot, fill=(110, 110, 118))
    y = y0 + 140
    for ln in linhas:
        d.text((x0 + 48, y), ln, font=f_txt, fill=(22, 22, 26))
        y += 74
    d.rounded_rectangle((x0, y0 + alt - 14, x0 + 220, y0 + alt), radius=7, fill=kit["cor"])
    return im if fundo is None else im.convert("RGB")


def card_final(kit, fundo, partes=False):
    """Cartão da marca: nome grande na cor da marca, o que o produto faz, pílula 'Link no perfil', @conta.
    fundo=None: véu escuro semitransparente (vai por cima de um clipe do Veo)."""
    if fundo is None:
        base = Image.new("RGBA", (W, H), kit["escuro"] + (175,))
    else:
        base = Image.blend(fundo.filter(ImageFilter.GaussianBlur(10)), Image.new("RGB", (W, H), kit["escuro"]), 0.78)
    im = base.convert("RGBA")
    d = ImageDraw.Draw(im)

    def centro(t, f, y, c):
        d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=c)

    cor = kit["cor"]
    nome = kit["nome_produto"]
    tam = 132
    while d.textlength(nome, font=_f(kit_mod.FONTE_BLACK, tam)) > W - 120 and tam > 60:
        tam -= 4
    y = 560
    d.rounded_rectangle((W / 2 - 70, y - 70, W / 2 + 70, y - 58), radius=6, fill=cor)
    # 26/10 (verificadores): vermelho da marca sobre o fundo escuro da marca ficava ilegível -> cor só se é clara
    luz = 0.2126 * cor[0] + 0.7152 * cor[1] + 0.0722 * cor[2]
    centro(nome, _f(kit_mod.FONTE_BLACK, tam), y, cor if luz > 140 else (255, 255, 255))
    y += int(tam * 1.25)
    sub = ((kit["produto"] or {}).get("cta_curto") or kit.get("tema") or "").strip()
    for ln in _quebrar(d, sub, _f(kit_mod.FONTE_XBOLD, 56), W - 160):
        centro(ln, _f(kit_mod.FONTE_XBOLD, 56), y, (240, 240, 240))
        y += 72
    y += 70
    fb = _f(kit_mod.FONTE_BLACK, 64)
    t = kit["convite"]
    lw = d.textlength(t, font=fb)
    caixa = (int((W - lw) / 2 - 64), int(y - 26), int((W + lw) / 2 + 64), int(y + 100))
    botao = Image.new("RGBA", (caixa[2] - caixa[0], caixa[3] - caixa[1]), (0, 0, 0, 0))
    db = ImageDraw.Draw(botao)
    db.rounded_rectangle((0, 0, botao.width - 1, botao.height - 1), radius=63, fill=cor)
    db.text(((botao.width - lw) / 2, 26), t, font=fb, fill=kit["texto"])
    if not partes:  # partes=True: o botão vem separado para pulsar (seg_cartao_vivo)
        im.alpha_composite(botao, (caixa[0], caixa[1]))
    y += 190
    centro(kit["arroba"], _f(kit_mod.FONTE_XBOLD, 50), y, (225, 225, 225))
    y += 80
    centro("Link no perfil" if kit["convite"] != "Link no perfil" else "Fale com a gente no direct",
           _f(kit_mod.FONTE_XBOLD, 40), y, (190, 190, 195))
    if partes:
        return im, botao, caixa
    return im if fundo is None else im.convert("RGB")


def seg_cartao_vivo(kit, fundo, dur, saida, clip=None):
    """27/10 (júri: "cartão final parado"; ideia do melhorador): cartão final VIVO — botão pulsando (1,00–1,06, ~1 s)
    e fundo com zoom lento (foto) ou o clipe do Veo correndo atrás. Quadro a quadro (PIL) direto pro ffmpeg."""
    base, botao, caixa = card_final(kit, fundo if clip is None else None, partes=True)
    n = int(math.ceil(dur * FPS))
    cx, cy = (caixa[0] + caixa[2]) / 2, (caixa[1] + caixa[3]) / 2
    if clip is not None:
        cmd_in = ["-i", str(clip), "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        d = _dur(clip)
        fator = max(1.0, dur / max(d - 0.3, 0.5))
        filtro = (f"[0:v]setpts={fator:.4f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"fps={FPS},setsar=1[f];[f][1:v]overlay=0:0:shortest=1,format=yuv420p[v]")
        cmd = [FF, "-y", "-v", "error", *cmd_in, "-filter_complex", filtro, "-map", "[v]", "-t", f"{dur:.3f}"]
    else:
        cmd = [FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
               "-i", "-", "-vf", "format=yuv420p"]
    proc = subprocess.Popen([*cmd, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-frames:v", str(n),
                             str(saida)], stdin=subprocess.PIPE)
    try:
        for q in range(n):
            t = q / FPS
            if clip is None:  # zoom lento no cartão inteiro (sem o botão), como o Ken Burns
                z = 1 + ajustes.valor("kenburns_zoom") * 0.5 * q / max(n - 1, 1)
                fr = base.resize((int(W * z), int(H * z)))
                fr = fr.crop(((fr.width - W) // 2, (fr.height - H) // 2, (fr.width - W) // 2 + W,
                              (fr.height - H) // 2 + H))
            else:
                fr = base.copy()
            # 28/10 (júri Follow-up/Fábrica: q13–q15 "rigorosamente idênticos"): o pulso de 1,1 s caía na mesma fase nos
            # quadros do júri (~1,2 s entre eles) -> período 0,83 s, o botão ENTRA crescendo (0,25–0,6 s) e um brilho
            # atravessa o botão a cada 1,5 s (posição diferente em todo quadro)
            entra = min(max((t - 0.25) / 0.35, 0), 1)
            entra = 1 - (1 - entra) ** 3
            s = (0.6 + 0.4 * entra) * (1 + ajustes.valor("pulso_botao") * (0.5 - 0.5 * math.cos(2 * math.pi * t / 0.83)))
            bt = botao
            if ajustes.valor("brilho_botao"):
                bt = botao.copy()
                faixa = Image.new("RGBA", bt.size, (0, 0, 0, 0))
                xb = -160 + (bt.width + 320) * ((t % 1.5) / 1.0)
                ImageDraw.Draw(faixa).polygon([(xb, 0), (xb + 70, 0), (xb + 20, bt.height), (xb - 50, bt.height)],
                                              fill=(255, 255, 255, 110))
                faixa.putalpha(Image.composite(faixa.getchannel("A"), Image.new("L", bt.size, 0),
                                               bt.getchannel("A").point(lambda v: 255 if v > 200 else 0)))
                bt = Image.alpha_composite(bt, faixa.filter(ImageFilter.GaussianBlur(6)))
            if entra <= 0:
                proc.stdin.write(fr.convert("RGBA").tobytes())
                continue
            b = bt.resize((int(bt.width * s), int(bt.height * s)), Image.LANCZOS)
            if entra < 1:
                b.putalpha(b.getchannel("A").point(lambda v, q=entra: int(v * q)))
            fr.alpha_composite(b, (int(cx - b.width / 2), int(cy - b.height / 2)))
            proc.stdin.write(fr.convert("RGBA").tobytes())
    finally:
        proc.stdin.close()
        proc.wait(timeout=600)
    if proc.returncode:
        raise RuntimeError("ffmpeg do cartão vivo falhou")
    return saida


def seg_veo_com_cartao(clip, cartao, dur, saida):
    """Cartão (RGBA) por cima de um clipe do Veo em movimento (26/10, dono: "3 Veo em diante" -> a abertura e o
    cartão final ganham Veo de fundo em vez de foto parada)."""
    png = Path(saida).with_suffix(".cartao.png")
    cartao.save(png)
    d = _dur(clip)
    fator = max(1.0, dur / max(d - 0.3, 0.5))
    _ff(["-i", str(clip), "-loop", "1", "-i", str(png), "-filter_complex",
         f"[0:v]setpts={fator:.4f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
         f"setsar=1[f];[f][1:v]overlay=0:0:shortest=1,format=yuv420p[v]", "-map", "[v]", "-an", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(saida)])
    png.unlink(missing_ok=True)
    return saida


# ───────────────────────────── Veo (cena comercial sem fala) ─────────────────────────────

def prompt_veo(prompt_en):
    return (f"{prompt_en.strip().rstrip('.')}. Professional commercial cinematography for a small-business software "
            "ad, shot on a cinema camera, shallow depth of field, soft natural light, smooth slow dolly movement. "
            "People only seen from the side or from behind, doing natural everyday actions; nobody looks at the "
            "camera and nobody speaks. Ambient sound only, no music, no dialogue, no voice-over. No text, no "
            "captions, no logos, no phone or computer screens with readable text, no watermarks. One continuous "
            "shot. 9:16 vertical portrait.")


def prompt_apresentador(cenario_en, fala):
    """O DONO (1º quadro = foto dele no cenário, feita pelo foto_na_hora) falando para a câmera. Mesma forma de pedido
    que funcionou no MS Energy (22/10: fala no formato simples 'says ...: "..."'; sem "smartphone framing")."""
    return (f"The man from the first frame, {cenario_en.strip().rstrip('.')}. Keep his face exactly as in the first "
            "frame. Medium close-up, vertical 9:16 framing, shot on a professional cinema camera, realistic, natural "
            "light, true-to-life colors, full-frame image with no interface elements. He has a calm, confident and "
            f'friendly manner and looks straight into the camera. He says in Brazilian Portuguese: "{fala}" Only this '
            "line is spoken. Natural hand gestures. One single continuous shot: no cuts. Soft ambient sound, no music. "
            "No subtitles, no captions, no on-screen text, no logos, no watermarks. 9:16 vertical portrait.")


def apresentador(conta, b, saida, log=log_padrao):
    """Bloco do DONO (25/10: "todos os produtos têm que usar EU como personagem nos vídeos do Veo 3"):
    foto dele no cenário (foto_na_hora: rosto conferido contra as fotos-base) -> Veo com essa foto no 1º quadro ->
    rosto conferido de novo no vídeo -> (clipe, wav, palavras com tempo). None = bloco vira imagem + narradora."""
    try:
        sys.path.insert(0, r"D:\veo\beta")
        sys.path.insert(0, r"D:\ms-energy\bin")
        import foto_na_hora as fnh
        import qa_ms
    except Exception as e:  # noqa: BLE001
        log(f"  [dono] indisponível ({type(e).__name__}: {str(e)[:100]})")
        return None
    cen = b.get("cenario_en") or "in a bright modern small-business office"
    foto = b.get("foto_fixa")
    for rodada in range(0 if foto else 3):  # 25/10 17:50: notebooks ocupados -> as 3 tentativas caíram em 30 s
        # 26/10 16:35: travou 20 min sem saída no Chrome remoto (túnel caído; o Playwright não tem prazo ali) ->
        # a foto roda numa thread com prazo; estourou = segue com a foto já aprovada (abaixo)
        import threading
        res = {}

        def _foto():
            res["foto"] = fnh.gerar(cen, f"he talks to the camera about {kit_mod.kit(conta)['nome_produto']}",
                                    tag=f"produto_{conta}")
        th = threading.Thread(target=_foto, daemon=True)  # daemon: travada não segura o fim do processo
        th.start()
        th.join(1200)
        if th.is_alive():
            log("  [dono] a foto passou de 20 min (Chrome remoto travado) — sigo sem esperar")
        foto = res.get("foto")
        if foto or rodada == 2:
            break
        # 25/10 18:05: sem máquina livre -> a última foto dele JÁ APROVADA (rosto conferido) desta mesma conta
        aprovadas = [rg.get("arquivo") for rg in fnh._registros()
                     if rg.get("aprovada") and rg.get("tag") == f"produto_{conta}" and rg.get("arquivo")
                     and Path(rg["arquivo"]).exists()]
        if aprovadas:
            foto = aprovadas[-1]
            log(f"  [dono] Flow sem máquina livre — uso a foto dele já aprovada desta conta ({Path(foto).name})")
            break
        log("  [dono] Flow sem máquina livre agora — espero 4 min e tento de novo")
        time.sleep(240)
    if not foto:
        log("  [dono] nenhuma foto dele passou no revisor de rosto — bloco sem o dono")
        return None
    log(f"  [dono] foto no cenário: {foto}")
    b["foto_dono"] = str(foto)  # a capa do carrossel do mesmo roteiro usa esta foto (dono 25/10: "carrosséis também")
    clip = clipe_veo(None, saida, log, foto=foto, pedido=prompt_apresentador(cen, b["fala"]))
    if not clip:
        return None
    ok, notas, motivo = fnh.revisar_video(str(clip))
    if not ok:
        log(f"  [dono] rosto mudou no vídeo ({motivo}) — descartado")
        return None
    wav = Path(saida).with_suffix(".wav")
    _ff(["-i", str(clip), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    palavras = []
    for tentativa in range(2):  # 25/10 18:25: falhou com o PC1 sem memória; no teste das 22h o mesmo áudio funcionou
        try:
            palavras = qa_ms.transcrever(wav)
            break
        except Exception as e:  # noqa: BLE001
            log(f"  [dono] Whisper falhou ({type(e).__name__}: {str(e)[:80]})"
                + (" — espero 60 s e tento de novo" if tentativa == 0 else " — legenda pelo texto do roteiro"))
            if tentativa == 0:
                time.sleep(60)
    from montagem_ms import alinhar
    d = _dur(clip)
    alinhadas = alinhar(b["fala"], palavras, d)  # texto CERTO do roteiro com os tempos que o Whisper ouviu
    log(f"  [dono] vídeo aprovado (rosto {notas}); {len(alinhadas)} palavras na legenda")
    return clip, wav, alinhadas, d


def clipe_veo(prompt_en, saida, log=log_padrao, foto=None, pedido=None):
    """Clipe de 8 s pelo Veo com a mesma escada de contas do MS Energy (gerar_short_veo). None se não saiu.
    Precisa do python do Veo (D:\\veo\\venv): é o que a tarefa diária usa. foto = 1º quadro (dono)."""
    try:
        sys.path.insert(0, r"D:\ms-energy\bin")
        sys.path.insert(0, r"D:\veo\beta")
        import gerar_short_veo as gsv
    except Exception as e:  # noqa: BLE001
        log(f"  [veo] indisponível neste python ({type(e).__name__}: {str(e)[:100]})")
        return None
    pedido = pedido or prompt_veo(prompt_en)
    # 26/10 04h: máquina ocupada / PC1 pausado não é falha — antes gastava as 3 tentativas e o vídeo saía sem o dono
    tentativa, prazo = 0, time.time() + 3600
    while tentativa < 3 and time.time() < prazo:
        sessao = gsv.escolher_sessao()
        if sessao is None:
            # 26/10 04:50: PC1 pausado + notebooks postando = nenhuma conta agora; o dono é obrigatório -> espera
            if time.time() + 120 < prazo:
                log("  [veo] sem conta livre agora — espero 2 min")
                time.sleep(120)
                os.environ.pop("VEO_SO_NOTEBOOK", None)  # o PC1 pode ter saído da pausa nesse tempo
                continue
            log("  [veo] sem conta livre")
            return None
        gsv.aplicar_sessao(sessao)
        log(f"  [veo] conta {sessao['session']} (tentativa {tentativa + 1})")
        ok = gsv.gerar_video_robusto(pedido, foto, str(saida), log=log)
        if ok == "MAQUINA_OCUPADA":
            time.sleep(60)
            continue
        if ok == "PAUSED" and os.environ.get("VEO_SO_NOTEBOOK") == "1":
            log("  [veo] PC1 pausado e notebooks ocupados — espero 2 min")
            time.sleep(120)
            continue
        tentativa += 1
        if ok is True:
            gsv.registrar_sucesso_sessao(sessao["session"])
            return saida
        if isinstance(ok, tuple) and ok[0] == "NO_CREDITS":
            gsv.marcar_creditos_esgotados(sessao["session"], padrao_texto=ok[1] if len(ok) > 1 else "")
        elif ok == "SESSAO":
            gsv.marcar_conta_fora(sessao["session"], "login caiu ou conta bloqueada no Flow", horas=6)
        elif ok == "TRAVOU":
            gsv.marcar_conta_fora(sessao["session"], "Flow travado (nada gerou no prazo)", horas=1)
        elif ok == "COPYRIGHT_BLOCKED":
            log("  [veo] pedido recusado por política — sem Veo neste vídeo")
            return None
        elif ok == "PAUSED":
            # 25/10 17:31: PC1 sem memória (pausa por carga) -> só as contas dos notebooks geram (o Chrome abre lá)
            tentativa -= 1
            log("  [veo] PC1 pausado por carga — tento pelas contas dos notebooks")
            os.environ["VEO_SO_NOTEBOOK"] = "1"
        else:
            gsv.registrar_falha_sessao(sessao["session"], "produto profissional: veo falhou")
    return None


def seg_veo(clip, dur, saida):
    """Clipe do Veo em 1080x1920 com a duração do bloco (se faltar tempo, desacelera de leve; sem som)."""
    d = _dur(clip)
    fator = max(1.0, dur / max(d - 0.3, 0.5))
    # 27/10 (júri: "plano do apresentador parado 5 s"; ideia do melhorador): aproximação lenta ao longo da cena —
    # escala recalculada a cada quadro + corte no centro (mais suave que o zoompan, que treme o rosto)
    p = ajustes.valor("punchin_video")
    _ff(["-i", str(clip), "-vf",
         f"setpts={fator:.4f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
         f"scale=w='trunc({W}*(1+{p}*t/{dur:.3f})/2)*2':h=-2:eval=frame,crop={W}:{H},"
         f"setsar=1,format=yuv420p", "-an", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "18", str(saida)])
    return saida


# ───────────────────────────── material REAL do cliente (MS Energy) ─────────────────────────────

MS_CLIPES = Path(r"D:\ms-energy\assets\videos_reais\clipes.json")
MS_VIDEOS = Path(r"D:\ms-energy\assets\fotos_instagram\google_fotos\videos")
USO_REAIS = BIN.parent / "config" / "produto_reais_uso.json"
FOTO_POR_TEMA = {"placas_no_telhado": {"placas_no_telhado", "cliente_com_placas"}, "usina_no_solo": {"usina_no_solo"},
                 "equipe_instalando": {"equipe_instalando"}, "estrutura": {"equipe_instalando", "placas_no_telhado"},
                 "inversor": {"equipamento"}, "drone": {"placas_no_telhado", "usina_no_solo"}}


def _uso_reais():
    try:
        return json.loads(USO_REAIS.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def seg_real(tema, dur, saida, evitar, log=log_padrao):
    """Instalação REAL (25/10 22h, dono: "uma parte Veo e outra com imagens de instalações e a IA falando"):
    1º um trecho de vídeo real do tema (clipes.json, o usado há mais tempo), senão uma foto aprovada do tema com
    movimento de câmera. Devolve o id usado (para não repetir no mesmo vídeo) ou None."""
    uso = _uso_reais()
    try:
        clipes = [c for c in json.loads(MS_CLIPES.read_text("utf-8"))["clipes"]
                  if (MS_VIDEOS / c["arquivo"]).exists() and c["id"] not in evitar]
    except Exception:  # noqa: BLE001
        clipes = []
    do_tema = [c for c in clipes if c.get("categoria") == tema or tema in (c.get("mostra") or "")]
    cand = sorted(do_tema or clipes, key=lambda c: uso.get(c["id"], ""))
    if cand:
        c = cand[0]
        n = c["fim"] - c["inicio"]
        fator = max(1.0, dur / max(n - 0.2, 0.5))  # trecho curto: desacelera de leve para cobrir a fala
        _ff(["-ss", f"{c['inicio']:.2f}", "-t", f"{n:.2f}", "-i", str(MS_VIDEOS / c["arquivo"]), "-vf",
             f"setpts={fator:.4f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
             f"setsar=1,format=yuv420p", "-an", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "18", str(saida)])
        uso[c["id"]] = datetime.now().isoformat(timespec="seconds")
        USO_REAIS.write_text(json.dumps(uso, ensure_ascii=False, indent=1), "utf-8")
        log(f"  [real] trecho {c['id']} ({c.get('mostra', '')[:60]})")
        return c["id"]
    try:
        sys.path.insert(0, r"D:\ms-energy\bin")
        import roteiro_ms
        fotos = [(n_, it) for n_, it in roteiro_ms.fotos_boas() if n_ not in evitar
                 and (it.get("visao") or {}).get("mostra") in FOTO_POR_TEMA.get(tema, {tema})]
        fotos = sorted(fotos or roteiro_ms.fotos_boas(), key=lambda f: uso.get(f[0], ""))
        if fotos:
            nome = fotos[0][0]
            seg_imagem(ImageOps.fit(Image.open(roteiro_ms.FOTOS_DIR / nome).convert("RGB"), (W, H)), dur, saida,
                       direcao=random.randint(0, 2))
            uso[nome] = datetime.now().isoformat(timespec="seconds")
            USO_REAIS.write_text(json.dumps(uso, ensure_ascii=False, indent=1), "utf-8")
            log(f"  [real] foto {nome}")
            return nome
    except Exception as e:  # noqa: BLE001
        log(f"  [real] fotos indisponíveis ({type(e).__name__}: {str(e)[:100]})")
    return None


def foto_real_fundo():
    """Foto real aprovada (fundo do cartão de pergunta e do cartão final do cliente)."""
    try:
        sys.path.insert(0, r"D:\ms-energy\bin")
        import roteiro_ms
        boas = roteiro_ms.fotos_boas()
        if boas:
            return ImageOps.fit(Image.open(roteiro_ms.FOTOS_DIR / random.choice(boas)[0]).convert("RGB"), (W, H))
    except Exception:  # noqa: BLE001
        pass
    return None


# ───────────────────────────── camada de efeitos ─────────────────────────────

def _blocos_legenda(palavras, max_pal=3, max_chars=20):
    """[[(palavra, ini, fim)...], ...]: pedaços de até 3 palavras, quebrando na pontuação."""
    grupos, cur = [], []
    for w, s, e in palavras:
        cur.append((w, s, e))
        if len(cur) >= max_pal or len(" ".join(x[0] for x in cur)) >= max_chars or w.endswith((".", "!", "?", ",", ":")):
            grupos.append(cur)
            cur = []
    if cur:
        grupos.append(cur)
    return grupos


class Camada:
    """Desenha a faixa de cima (frase fixa, tópico, progresso) e a faixa da legenda, quadro a quadro, com cache."""
    TOPO_H = 480
    LEG_H = 300

    def __init__(self, kit, gancho, rotulos, grupos, tempos, total):
        self.k, self.total = kit, total
        self.t_gancho, self.t_card = tempos["gancho"], tempos["card"]
        self.rotulos = rotulos            # [(numero, texto, ini, fim)]
        self.grupos = grupos              # [[(palavra, ini, fim)], ...] com tempo absoluto
        self.f_leg = _f(kit_mod.FONTE_XBOLD, ajustes.valor("legenda_fonte"))
        self.f_rot = _f(kit_mod.FONTE_XBOLD, 40)
        self.f_num = _f(kit_mod.FONTE_BLACK, 40)
        self.img_gancho = self._gancho(gancho)
        self.rot_y = min(TOPO[1] + self.img_gancho.height + 10, self.TOPO_H - 92)
        self.img_rot = {n: self._rotulo(n, t) for n, t, _, _ in rotulos}
        self.cache_leg = {}

    def _gancho(self, texto):
        k = self.k
        im = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        tam = 60
        while tam > 34:
            f = _f(kit_mod.FONTE_BLACK, tam)
            linhas = _quebrar(d, texto.upper(), f, W - 200)
            if len(linhas) <= 2:
                break
            tam -= 4
        alt = len(linhas) * int(tam * 1.18) + 44
        larg = max(d.textlength(ln, font=f) for ln in linhas) + 80
        x0 = (W - larg) / 2
        d.rounded_rectangle((x0 + 6, 10, x0 + larg + 6, alt + 10), radius=28, fill=(0, 0, 0, 90))
        d.rounded_rectangle((x0, 0, x0 + larg, alt), radius=28, fill=k["cor"] + (245,))
        y = 22
        for ln in linhas:
            d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=k["texto"])
            y += int(tam * 1.18)
        return im.crop((0, 0, W, alt + 14))

    def _rotulo(self, n, texto):
        k = self.k
        im = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        lw = d.textlength(texto, font=self.f_rot)
        d.rounded_rectangle((60, 6, 60 + lw + 130, 82), radius=38, fill=(12, 12, 16, 200))
        d.ellipse((66, 12, 130, 76), fill=k["cor"])
        num = str(n)
        d.text((98 - d.textlength(num, font=self.f_num) / 2, 18), num, font=self.f_num, fill=k["texto"])
        d.text((150, 18), texto, font=self.f_rot, fill=(255, 255, 255))
        return im

    def _legenda(self, gi, ativa):
        chave = (gi, ativa)
        if chave in self.cache_leg:
            return self.cache_leg[chave]
        palavras = [w for w, _, _ in self.grupos[gi]]
        im = Image.new("RGBA", (W, self.LEG_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        f = self.f_leg
        esp = d.textlength(" ", font=f)
        larg = [d.textlength(p, font=f) for p in palavras]
        total = sum(larg) + esp * (len(palavras) - 1)
        tam_f = f
        # 28/10 (júri Hermes Call: "legenda invade a margem lateral, < 60 px"): 70 px de cada lado (antes 50)
        if total > W - 140:  # pedaço comprido: letra menor
            tam_f = _f(kit_mod.FONTE_XBOLD, int(ajustes.valor("legenda_fonte") * (W - 140) / total))
            larg = [d.textlength(p, font=tam_f) for p in palavras]
            esp = d.textlength(" ", font=tam_f)
            total = sum(larg) + esp * (len(palavras) - 1)
        x = (W - total) / 2
        y = (self.LEG_H - tam_f.size) / 2 - 10
        for i, p in enumerate(palavras):
            cor = self.k["destaque"] if i == ativa else (255, 255, 255)
            if i == ativa:  # fundo suave atrás da palavra falada
                d.rounded_rectangle((x - 12, y - 4, x + larg[i] + 12, y + tam_f.size + 18), radius=16,
                                    fill=(0, 0, 0, 120))
            d.text((x, y), p, font=tam_f, fill=cor, stroke_width=7, stroke_fill=(0, 0, 0))
            x += larg[i] + esp
        self.cache_leg[chave] = im
        return im

    def quadro_topo(self, t):
        im = Image.new("RGBA", (W, self.TOPO_H), (0, 0, 0, 0))
        if t < self.t_card:
            # barrinha de progresso (do início até o cartão)
            ImageDraw.Draw(im).rectangle((0, 0, int(W * min(t / self.t_card, 1)), 9), fill=self.k["cor"] + (255,))
            if t >= self.t_gancho:
                p = min((t - self.t_gancho) / 0.35, 1)
                p = 1 - (1 - p) ** 3
                g = self.img_gancho
                if p < 1:
                    g = g.copy()
                    g.putalpha(g.getchannel("A").point(lambda v, q=p: int(v * q)))
                im.alpha_composite(g, (0, int(TOPO[1] - 20 * (1 - p))))
            for n, _, ini, fim in self.rotulos:
                if ini <= t < fim:
                    p = 1 - (1 - min((t - ini) / 0.3, 1)) ** 3
                    r = self.img_rot[n]
                    if p < 1:
                        r = r.copy()
                        r.putalpha(r.getchannel("A").point(lambda v, q=p: int(v * q)))
                    # entra deslizando da direita até o lugar (deslocamento sempre >= 0: nada sai pela borda)
                    desl = int(40 * (1 - p))
                    if desl:
                        r = r.crop((0, 0, r.width - desl, r.height))
                    im.alpha_composite(r, (desl, self.rot_y))
        return im

    def quadro_legenda(self, t):
        im = Image.new("RGBA", (W, self.LEG_H), (0, 0, 0, 0))
        for gi, g in enumerate(self.grupos):
            ini = g[0][1]
            fim = self.grupos[gi + 1][0][1] if gi + 1 < len(self.grupos) else g[-1][2] + 0.5
            fim = min(fim, g[-1][2] + 0.6)
            if ini <= t < fim:
                ativa = max((i for i, (_, s, _) in enumerate(g) if s <= t), default=0)
                leg = self._legenda(gi, ativa)
                p = min((t - ini) / 0.12, 1)
                if p < 1:  # entrada com leve crescimento
                    s = 0.9 + 0.1 * p
                    leg2 = leg.resize((int(W * s), int(self.LEG_H * s)))
                    leg2.putalpha(leg2.getchannel("A").point(lambda v, q=p: int(v * q)))
                    im.alpha_composite(leg2, (int((W - leg2.width) / 2), int((self.LEG_H - leg2.height) / 2)))
                else:
                    im.alpha_composite(leg)
                break
        return im

    def gravar(self, saida_topo, saida_leg):
        """Duas faixas .mov com transparência (qtrle): a de cima e a da legenda."""
        n = int(math.ceil(self.total * FPS))
        procs = []
        for arq, alt in ((saida_topo, self.TOPO_H), (saida_leg, self.LEG_H)):
            procs.append(subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s",
                                           f"{W}x{alt}", "-r", str(FPS), "-i", "-", "-c:v", "qtrle", "-pix_fmt",
                                           "argb", str(arq)], stdin=subprocess.PIPE))
        try:
            for q in range(n):
                t = q / FPS
                procs[0].stdin.write(self.quadro_topo(t).tobytes())
                procs[1].stdin.write(self.quadro_legenda(t).tobytes())
        finally:
            for p in procs:
                p.stdin.close()
                p.wait(timeout=600)
        if any(p.returncode for p in procs):
            raise RuntimeError("ffmpeg da camada de efeitos falhou")


# ───────────────────────────── montagem ─────────────────────────────

TRANSICOES = ["smoothleft", "fade", "smoothup", "fade"]


def emendar(segs, durs, saida):
    """Segmentos com transições (xfade). Devolve o início de cada segmento no vídeo final."""
    ent, fc, inicios = [], [], [0.0]
    for i, s in enumerate(segs):
        ent += ["-i", str(s)]
        fc.append(f"[{i}:v]fps={FPS},settb=AVTB,setsar=1,format=yuv420p,setpts=PTS-STARTPTS[s{i}]")
    atual, t = "s0", durs[0]
    for i in range(1, len(segs)):
        off = t - XF
        inicios.append(off)
        fc.append(f"[{atual}][s{i}]xfade=transition={TRANSICOES[(i - 1) % len(TRANSICOES)]}:duration={XF}:"
                  f"offset={off:.3f}[x{i}]")
        atual, t = f"x{i}", off + durs[i]
    _ff([*ent, "-filter_complex", ";".join(fc), "-map", f"[{atual}]", "-c:v", "libx264", "-preset", "medium",
         "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), str(saida)], timeout=1200)
    return inicios, t


def _visao(jpeg, pergunta):
    import base64
    import re
    import urllib.request
    gw = json.loads(agentes.GATEWAY.read_text("utf-8"))
    # 28/10: 3 timeouts num vídeo só com o gemini-3-flash -> a imagem nova (nota 9 depois, conferida) foi trocada por
    # foto do banco sem nada a ver com a fala. Tenta os outros Gemini antes de desistir (testados: 5 s / 5 s / 29 s).
    erro = None
    for modelo in ("antigravity/gemini-3-flash", "gemini/gemini-3.5-flash", "agy/gemini-3.8-flash-high"):
        corpo = {"model": modelo, "max_tokens": 300, "temperature": 0.1, "messages": [
            {"role": "user", "content": [{"type": "text", "text": pergunta}, {"type": "image_url", "image_url": {
                "url": "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()}}]}]}
        req = urllib.request.Request(gw["gateway_url"].rstrip("/") + "/v1/chat/completions",
                                     data=json.dumps(corpo).encode(),
                                     headers={"Authorization": "Bearer " + gw["gateway_key"],
                                              "Content-Type": "application/json"})
        try:
            txt = json.loads(urllib.request.urlopen(req, timeout=90).read())["choices"][0]["message"]["content"]
            return json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
        except Exception as e:  # noqa: BLE001
            erro = e
    raise erro


_PERG_FINAL = ('Este é um quadro de um anúncio profissional em vídeo (Reels). FAZEM PARTE DO DESENHO e NÃO são defeito: '
               'a faixa colorida com o título no topo, a etiqueta numerada (ex.: "2 Como funciona"), a LEGENDA grande '
               'com uma palavra destacada no meio/baixo da tela (é karaokê: mostra só 2 ou 3 palavras da frase por vez, '
               'então pedaço de frase como "confere fotos dos" é NORMAL, não é texto cortado), os cartões com ✓ e '
               'trecho da fala, a conversa de celular com o selo "Simulação", o cartão '
               'de pergunta e o cartão final da marca. Responda SÓ JSON: {"defeito": true SÓ se há texto cortado pela '
               'borda da tela, letras embaralhadas/sem sentido NA IMAGEM DE FUNDO (não na legenda), marca d\'água de '
               'outra empresa, imagem deformada (mãos/rostos/objetos tortos), tela preta, elementos sobrepostos de forma '
               'quebrada, ou algo impróprio; "motivo": "descreva exatamente o que e onde"}')


def trava_final(mp4, total, log=log_padrao):
    """(ok, motivos): duração, áudio e 3 quadros conferidos por visão (falha da visão = aprova com aviso)."""
    motivos = []
    d = _dur(mp4)
    if not 12 <= d <= 45:
        motivos.append(f"duração {d:.1f}s fora de 12–45 s")
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
                        str(mp4)], capture_output=True, text=True)
    if not r.stdout.strip():
        motivos.append("sem áudio")
    for f in (0.22, 0.55, 0.8):
        jpeg = subprocess.run([FF, "-v", "error", "-ss", f"{d * f:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf",
                               "scale=540:-2", "-f", "image2", "-vcodec", "mjpeg", "-"], capture_output=True).stdout
        try:
            v = _visao(jpeg, _PERG_FINAL)
            if v.get("defeito"):
                # 25/10: a legenda grande sobre o balcão foi lida como "marca d'água borrada" (quadro estava limpo) ->
                # quadro acusado é conferido de novo; só reprova se a 2ª olhada confirmar
                v2 = _visao(jpeg, _PERG_FINAL + ' Confira com cuidado: só confirme o defeito se tiver certeza.')
                if v2.get("defeito"):
                    motivos.append(f"quadro {int(f * 100)}%: {v.get('motivo', '')[:120]}")
                else:
                    log(f"  [trava] quadro {int(f * 100)}%: 1ª olhada viu '{v.get('motivo', '')[:80]}', 2ª não confirmou")
        except Exception as e:  # noqa: BLE001
            log(f"  [trava] visão indisponível no quadro {int(f * 100)}% ({type(e).__name__})")
    return not motivos, motivos


def nivelar(mp4, log=log_padrao):
    """−14 LUFS / pico −1,5 dB pelo master_loudness COMUM (mesmo padrão dos outros projetos)."""
    try:
        sys.path.insert(0, r"D:\hipercool-materiais\comum")
        import master_loudness as ml
        m = ml.measure_pass(str(mp4), -14, -1.5)
        tmp = Path(mp4).with_name(Path(mp4).stem + "_nivel.mp4")
        ml.apply_pass(str(mp4), str(tmp), -14, -1.5, m)
        if tmp.exists() and tmp.stat().st_size > 10_000:
            tmp.replace(mp4)
    except Exception as e:  # noqa: BLE001
        log(f"  [áudio] nivelamento falhou ({type(e).__name__}: {str(e)[:100]}) — segue como saiu")


def gerar(conta, com_veo=False, saida_dir=None, log=log_padrao, variante=None):
    """Gera 1 Reel profissional para a conta. Devolve o mp4 aprovado (com .json ao lado) ou None.
    variante (produto\\variacoes.py): quais blocos o dono apresenta e se repete a foto (o agente aprende qual rende)."""
    from produto import variacoes
    var = variacoes.VARIANTES.get(variante) if variante else None
    if var is not None:
        com_veo = var["com_veo"]
    cenas = tuple(var["cenas"]) if var and var.get("cenas") else (1,)
    mesma_foto = bool(var and var.get("mesma_foto"))
    k = kit_mod.kit(conta)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp = TMP_RAIZ / f"{conta}_{ts}"
    tmp.mkdir(parents=True, exist_ok=True)
    saida_dir = Path(saida_dir) if saida_dir else FILA / conta
    saida_dir.mkdir(parents=True, exist_ok=True)
    log(f"=== {k['nome_produto']} ({k['arroba']}) — vídeo profissional{' com Veo' if com_veo else ''} ===")
    broll = tuple(var.get("veo_broll") or ()) if var and not kit_mod.kit(conta).get("cliente") else ()
    r = agentes.roteiro(k, com_veo=com_veo, log=log, cenas=cenas, broll=broll)
    if not r:
        log("  [STOP] roteiro não passou nas regras/revisor")
        return None

    # 0) o DONO apresenta o bloco 1 (avatar Veo das fotos dele); não saiu = bloco vira imagem + narradora
    donos = {}  # bloco (1..3) -> (clipe, wav, palavras, duração); 25/10 18:40: ele abre E fecha
    foto_fixa = None
    for i, b in enumerate(r["blocos"], 1):
        if b.get("visual") == "apresentador":
            # 27/10: foto nova por cena = óculos/roupa/cenário diferentes -> júri reprovou a Agenda (5,33, "quebra severa
            # de continuidade do apresentador") e derrubou o VPS -> TODA cena do dono parte da foto da 1ª
            if foto_fixa:
                b["foto_fixa"] = foto_fixa
            d_ = apresentador(conta, b, tmp / f"dono_{i}.mp4", log)
            foto_fixa = foto_fixa or b.get("foto_dono")
            if d_:
                donos[i] = d_
            else:
                b["visual"] = "imagem"
                b["prompt_en"] = b.get("prompt_en") or (b.get("cenario_en", "") + ", no people in focus")
    # 28/10 (júri Fábrica/Disparo: "legenda some e ele continua"; conferido no vídeo: a fala acaba em 5,7 s e a cena
    # usava o clipe de 8 s inteiro = 2 s de dono mudo): a cena do dono acaba folga_dono depois da última palavra;
    # a voz dele é cortada junto (senão o ambiente do clipe vaza na cena seguinte)
    for i, (clip_d, wav_d, pal_d, dur_d) in list(donos.items()):
        if not pal_d:
            continue
        corte = round(min(dur_d, max(3.5, pal_d[-1][2] + ajustes.valor("folga_dono") + 0.25)), 2)
        if corte < dur_d - 0.3:
            wav_c = Path(wav_d).with_name(Path(wav_d).stem + "_corte.wav")
            _ff(["-i", str(wav_d), "-t", f"{corte:.2f}", "-af", f"afade=t=out:st={corte - 0.15:.2f}:d=0.15",
                 str(wav_c)])
            donos[i] = (clip_d, wav_c, pal_d, corte)
            log(f"  [dono] bloco {i}: fala acaba em {pal_d[-1][2]:.1f}s — cena {dur_d:.1f}s -> {corte:.1f}s")
    dono = donos.get(1)  # compatibilidade com o resto (bloco 1)
    # 29/10: o Whisper medium (~2 GB) só serve para as cenas do dono e ficava carregado até o fim do vídeo (processo
    # do vídeo a 4,8 GB com a RAM do PC a 2,6 GB livres) -> solta aqui
    qa = sys.modules.get("qa_ms")
    if qa is not None and getattr(qa, "_whisper", None) is not None:
        qa._whisper = None
        import gc
        gc.collect()

    # 1) narração por trecho (o bloco do dono usa a voz do próprio vídeo)
    pecas = [("pergunta", r["pergunta_cliente"])] + [(f"b{i}", b["fala"]) for i, b in enumerate(r["blocos"], 1)] + \
            [("cta", k["convite_voz"])]
    audio = {}
    for rodada_voz in range(2):  # falhou com a voz da marca = o vídeo TODO com a reserva (nunca 2 vozes no mesmo)
        try:
            for nome, texto in pecas:
                if nome[0] == "b" and int(nome[1]) in donos:
                    dd = donos[int(nome[1])]
                    audio[nome] = (dd[1], dd[2], dd[3])
                    continue
                audio[nome] = narrar(texto, tmp / f"voz_{nome}.mp3", k, log,
                                     esperas=(10, 20, 0) if k["voz"] != VOZ_RESERVA else (15, 30, 60, 120, 0))
            break
        except RuntimeError:
            if rodada_voz or k["voz"] == VOZ_RESERVA:
                raise
            log(f"  [voz] {k['voz']} instável — narro o vídeo todo com {VOZ_RESERVA}")
            k = {**k, "voz": VOZ_RESERVA}
    narradas = [n for n, _ in pecas if not (n[0] == "b" and int(n[1]) in donos)]
    voz_clonada = clonar_vozes(audio, narradas, tmp, log)
    if narradas and not voz_clonada:
        # 28/10 (dona): "as vozes edge puras (Thalita, Antonio...) nunca devem ser usadas; as dos clones, mesmo as
        # ruins, são melhores; edge só com clone em cima" -> clone falhou no PC2 e no PC1 = o vídeo não sai
        raise RuntimeError("clone de voz falhou (PC2 e PC1): não faço vídeo com voz edge pura")
    LEAD = 0.22
    FOLGA = ajustes.valor("folga_fala")  # botão do melhorador
    durs = [max(2.7, LEAD + audio["pergunta"][2] + FOLGA + XF)]
    durs += [LEAD + audio[f"b{i}"][2] + FOLGA + XF for i in (1, 2, 3)]
    for i, dd in donos.items():
        durs[i] = dd[3] - 0.25 + XF
    durs.append(max(3.2, LEAD + audio["cta"][2] + 1.3))

    # 2) visuais de cada bloco (falhou o Flow: imagem já aprovada do banco da marca; outra deste vídeo espelhada;
    #    por último o degradê da marca — 25/10: o bloco 1 saiu liso e fraco)
    imgs = []
    for i, b in enumerate(r["blocos"], 1):
        im = None
        if b.get("visual") in ("imagem", "veo") and b.get("prompt_en"):
            im = imagem(k, b["prompt_en"], tmp / f"img_{i}.png", log)
        imgs.append(im)
    usadas_banco = []
    for i, b in enumerate(r["blocos"]):
        if imgs[i] is None and b.get("visual") == "imagem":
            im, nome = do_banco(k, usadas_banco)
            if im is None:
                outra = next((x for x in imgs if x is not None), None)
                im = ImageOps.mirror(outra) if outra is not None else None
            else:
                usadas_banco.append(nome)
                log(f"  [imagem] bloco {i + 1}: do banco da marca ({nome})")
            imgs[i] = im
    fundo_padrao = next((x for x in imgs if x is not None), None) or \
        (foto_real_fundo() if k.get("cliente") else None) or fundo_marca(k)
    reais_usados = []
    segs = [tmp / "s0_pergunta.mp4"]
    # 26/10 (dono: "ficou bom com 2 Veo, podemos fazer com 3 em diante"): Veo também ATRÁS do cartão da pergunta e
    # do cartão final (variações com veo_abertura/veo_cartao) — o que o Veo do bloco já pediu serve de cena
    veo_extra = []
    cena_extra = next((b.get("prompt_en") for b in r["blocos"] if b.get("visual") == "veo" and b.get("prompt_en")),
                      None) or (r["blocos"][0].get("cenario_en") or "a modern small Brazilian business") + \
        ", wide establishing shot, no person in the foreground, slow cinematic camera move"
    foto_abre = next((b.get("foto_dono") for b in r["blocos"] if b.get("foto_dono") and Path(b["foto_dono"]).exists()),
                     None)
    clip_abre = clipe_veo(cena_extra, tmp / "veo_abertura.mp4", log) if (var or {}).get("veo_abertura") and com_veo \
        else None
    if clip_abre:
        seg_veo_com_cartao(clip_abre, card_pergunta(k, r["pergunta_cliente"], None), durs[0], segs[0])
        veo_extra.append("abertura")
    else:
        seg_imagem(card_pergunta(k, r["pergunta_cliente"],
                                 Image.open(foto_abre).convert("RGB") if foto_abre else fundo_padrao,
                                 com_rosto=bool(foto_abre)), durs[0], segs[0], direcao=0)
    usou_veo = None
    tipos = ["pergunta"]  # o que cada cena REALMENTE virou (o editor Remotion recebe isto)
    for i, b in enumerate(r["blocos"], 1):
        s = tmp / f"s{i}_{b.get('visual')}.mp4"
        feito = False
        if i in donos:
            seg_veo(donos[i][0], durs[i], s)
            usou_veo, feito = str(donos[i][0]), "dono"
        if b.get("visual") == "veo" and com_veo and not feito:
            clip = clipe_veo(b["prompt_en"], tmp / f"veo_{i}.mp4", log)
            if clip:
                seg_veo(clip, durs[i], s)
                usou_veo, feito = str(clip), "veo"
        if not feito and b.get("visual") == "real":
            usado = seg_real(b.get("real_tema") or "placas_no_telhado", durs[i], s, reais_usados, log)
            if usado:
                reais_usados.append(usado)
                feito = "real"
        # 28/10 (diretor Hermes: "explica o produto e mostra foto de banco"; o Veo do bloco 2 falhou e virou foto):
        # Veo que falhou no bloco 2 -> a conversa de reserva do roteiro (o produto funcionando)
        if not feito and (b.get("visual") == "conversa" or (i == 2 and b.get("conversa"))):
            if b.get("visual") != "conversa":
                log(f"  [cena] bloco {i}: {b.get('visual')} não saiu — uso a conversa de reserva")
            chat_ui.render(k, b["conversa"], durs[i], s, area=AREA_CHAT, fundo=imgs[i - 1] or fundo_padrao, log=log)
            feito = "conversa"
        if not feito:
            # a voz do bloco começa LEAD + meia transição depois do início da cena (mesma conta do ofs da legenda)
            chips = tempos_destaques(b.get("destaques"), audio[f"b{i}"][1], LEAD + XF * 0.5)
            seg_imagem(imgs[i - 1] or fundo_marca(k), durs[i], s, direcao=i, kit=k, chips=chips)
            feito = "imagem"
            if chips:
                log(f"  [destaques] bloco {i}: {', '.join(f'{t} ({tl:.1f}s)' for t, tl in chips)}")
        tipos.append(feito)
        segs.append(s)
    tipos.append("cartao")
    segs.append(tmp / "s4_cartao.mp4")
    clip_fim = clipe_veo(cena_extra + ", golden hour", tmp / "veo_cartao.mp4", log) \
        if (var or {}).get("veo_cartao") and com_veo else None
    seg_cartao_vivo(k, fundo_padrao, durs[-1], segs[-1], clip=clip_fim)  # botão pulsando (27/10)
    if clip_fim:
        veo_extra.append("cartao")

    # 3) emenda com transições. Antes: duas cenas de VÍDEO seguidas (Veo/dono/real) ficam com a cor do começo da
    # 2ª puxada para a do fim da 1ª, soltando em 1,5 s (dona 02/11; REALCE_COR=0 desliga) — sem o "pisca" de cor.
    if realce_visual and realce_visual.disponivel("cor"):
        for i in range(1, len(segs) - 1):
            if tipos[i] in ("veo", "dono", "real") and tipos[i - 1] in ("veo", "dono", "real") \
                    and realce_visual.igualar_cor(segs[i], segs[i - 1]):
                log(f"  [cor] cena {i} puxada para a cor da cena {i - 1}")
    base = tmp / "base.mp4"
    inicios, total = emendar(segs, durs, base)
    log(f"  [montagem] {len(segs)} cenas emendadas ({total:.1f}s)")

    # 4) camada de efeitos (topo + legenda karaokê)
    grupos, ofs = [], {}
    for idx, (nome, _) in enumerate(pecas):
        # o áudio do dono já vem colado no vídeo dele: começa junto com a cena
        do_dono = nome[0] == "b" and nome[1:].isdigit() and int(nome[1:]) in donos
        ofs[nome] = inicios[idx] if do_dono else inicios[idx] + LEAD + (XF * 0.5 if idx else 0)
        # 26/10 (verificadores): agrupar POR FALA — o edge não manda pontuação e a legenda emendava o fim de uma
        # fala com o começo da outra ("monta tudo A"); o cartão final já escreve o convite, sem legenda por cima
        if nome != "cta":
            grupos += _blocos_legenda([(w, s + ofs[nome], e + ofs[nome]) for w, s, e in audio[nome][1]])
    rotulos = [(i, b["rotulo"].strip().capitalize(), inicios[i] + 0.1, inicios[i] + durs[i] - XF)
               for i, b in enumerate(r["blocos"], 1)]
    camada = Camada(k, r["gancho_tela"], rotulos, grupos, {"gancho": inicios[1], "card": inicios[-1] + 0.1}, total)
    topo, leg = tmp / "topo.mov", tmp / "legenda.mov"
    camada.gravar(topo, leg)

    # 5) áudio: narração por trecho + trilha que abaixa sozinha quando a narradora fala (sidechain)
    trilha = random.choice([t for t in TRILHAS if Path(t).exists()])
    # 28/10 (dona: "os efeitos de choque e fogo do manhwa-react... pra transicionar a tela, quando dá o choque aparece
    # a próxima"): faixa elétrica/fogo/glitch atravessando a tela em cada troca de cena (produto\efeitos.py)
    efeito = None
    if ajustes.valor("efeitos_transicao"):
        try:
            from produto import efeitos
            efeito = random.choice(efeitos.ESTILOS)
            efeitos.camada([inicios[i] for i in range(1, len(segs))], total, tmp / "efeitos.mov", k["cor"], efeito)
        except Exception as e:  # noqa: BLE001
            log(f"  [efeitos] sem transição de impacto ({type(e).__name__}: {str(e)[:100]})")
            efeito = None
    ent = ["-i", str(base), "-i", str(topo), "-i", str(leg)]
    if efeito:
        ent += ["-i", str(tmp / "efeitos.mov")]
        fc = ["[0:v][3:v]overlay=0:0[v0]", "[v0][1:v]overlay=0:0[v1]", f"[v1][2:v]overlay=0:{LEGENDA_Y}[v]"]
        log(f"  [efeitos] transições de impacto: {efeito} ({len(segs) - 1} trocas)")
    else:
        fc = [f"[0:v][1:v]overlay=0:0[v1]", f"[v1][2:v]overlay=0:{LEGENDA_Y}[v]"]
    a0 = len(ent) // 2  # 1ª entrada de áudio
    rotas = []
    for idx, (nome, _) in enumerate(pecas):
        ent += ["-i", str(audio[nome][0])]
        ms_ = int(ofs[nome] * 1000)
        fc.append(f"[{a0 + idx}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms_}|{ms_}[n{idx}]")
        rotas.append(f"[n{idx}]")
    ni = a0 + len(pecas)
    ent += ["-stream_loop", "-1", "-i", trilha]
    fc.append(f"{''.join(rotas)}amix=inputs={len(rotas)}:duration=longest:normalize=0,apad,atrim=0:{total:.3f}[voz]")
    fc.append("[voz]asplit=2[voz1][voz2]")
    fc.append(f"[{ni}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
              f"volume={ajustes.valor("vol_trilha") * 2:.3f},afade=t=in:d=0.8,afade=t=out:st={max(total - 1.5, 0):.2f}:d=1.5[mu]")
    fc.append("[mu][voz1]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=400[mud]")
    fc.append("[voz2][mud]amix=inputs=2:duration=first:normalize=0[a]")
    stem = f"{conta.replace('.', '_')}_{ts}"
    out = saida_dir / f"{stem}.mp4"
    _ff([*ent, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264",
         "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(out)], timeout=3600)  # 26/10: "medium" estourou 30 min com o PC carregado
    nivelar(out, log)
    ok, motivos = trava_final(out, total, log)
    side = {"conta": conta, "produto": k["produto_id"], "marca": k["marca"], "titulo": r["titulo"],
            "legenda": agentes.legenda_final(k, r), "roteiro": r, "voz": k["voz"], "voz_clonada": voz_clonada,
            "efeito_transicao": efeito,
            "trilha": Path(trilha).name,
            "veo": usou_veo, "duracao_s": round(total, 2), "trava_final": {"ok": ok, "motivos": motivos},
            "formato": "explicativo" + ("+veo" if usou_veo else ""), "gerado_em": datetime.now().isoformat(timespec="seconds"),
            # o que REALMENTE saiu (o agente de variações aprende com isto, não com o que foi pedido)
            "variante": variante, "cenas_dono_feitas": sorted(donos), "mesma_foto": mesma_foto,
            "veo_broll_feitos": [i for i in range(1, len(tipos) - 1) if tipos[i] == "veo"],
            "veo_extra_feitos": veo_extra,
            "veo_total": len(donos) + sum(1 for t in tipos if t == "veo") + len(veo_extra),
            "cenas": [{"n": i, "ini": round(inicios[i], 2), "fim": round(inicios[i] + durs[i] - (XF if i < len(durs) - 1 else 0), 2),
                       "fala": pecas[i][1],
                       "tipo": tipos[i]}
                      for i in range(len(durs))]}
    trava_ok = ok
    if ok:
        try:  # 26/10 (dono): 4 verificadores Gemini a cada vídeo; problemas viram melhoria no código
            from produto import lapidar
            lap = lapidar.verificar(out, side, k, log)
            if lap:
                side["lapidar"] = {x: lap[x] for x in ("nota", "notas", "graves", "reprovar", "motivo")}
                if lap["reprovar"]:
                    ok, motivos = False, [f"verificadores: {lap['motivo']}"]
                    side["trava_final"] = {"ok": ok, "motivos": motivos}
        except Exception as e:  # noqa: BLE001
            log(f"  [lapidar] não rodou: {type(e).__name__}: {str(e)[:140]}")
    if trava_ok:
        # 26/10 (dono: "o outro agente melhorou muito, atualize a sua"): o MESMO material vai ao editor Gemini em
        # Remotion + corretor (produto\editor.py); fica a versão de maior nota
        try:
            from produto import editor
            ctx = {"total": total, "trilha": trilha, "titulo": r["titulo"], "gancho": r["gancho_tela"],
                   "vozes": [(audio[nome][0], ofs[nome]) for nome, _ in pecas],
                   "palavras": [{"p": w, "ini": round(s + ofs[nome], 3), "fim": round(e + ofs[nome], 3), "cena": idx}
                                for idx, (nome, _) in enumerate(pecas) for w, s, e in audio[nome][1]],
                   "cenas": [{"n": i, "ini": round(inicios[i], 2), "fim": round(inicios[i] + durs[i], 2),
                              "tipo": tipos[i], "fala": pecas[i][1],
                              "rotulo": r["blocos"][i - 1]["rotulo"] if 0 < i < len(durs) - 1 else None,
                              "conversa": r["blocos"][i - 1].get("conversa") if tipos[i] == "conversa" else None,
                              "img": (imgs[i - 1] if 0 < i < len(durs) - 1 and imgs[i - 1] is not None
                                      else fundo_padrao) if tipos[i] not in ("dono", "real", "veo") else None,
                              "seg": segs[i] if tipos[i] in ("dono", "real", "veo") else None}
                             for i in range(len(durs))]}
            melhor = editor.melhorar(conta, k, ctx, side, out, log)
            if melhor:
                guarda = FILA / "_molde"  # o molde fica guardado (reserva se a versão do editor for barrada depois)
                guarda.mkdir(parents=True, exist_ok=True)
                shutil.copy2(out, guarda / out.name)
                shutil.copy2(melhor[0], out)
                side["lapidar"] = {x: melhor[1][x] for x in ("nota", "notas", "graves", "reprovar", "motivo")}
                side["formato"] += "+editor"
                side["editor"] = True
                ok, motivos = True, []
                side["trava_final"] = {"ok": True, "motivos": [], "obs": "versão do editor (nota dos verificadores)"}
                log(f"  [editor] fica a versão do editor (nota {melhor[1]['nota']})")
            editor.limpar(out.stem)
        except Exception as e:  # noqa: BLE001
            log(f"  [editor] não rodou: {type(e).__name__}: {str(e)[:160]}")
    if not ok:
        rev = FILA / "_revisar"
        rev.mkdir(parents=True, exist_ok=True)
        destino = rev / out.name
        shutil.move(str(out), str(destino))
        destino.with_suffix(".json").write_text(json.dumps(side, ensure_ascii=False, indent=1), "utf-8")
        vitrine(destino, side, "REPROVADO (não vai pra fila)")
        log(f"  [STOP] reprovado na trava final: {'; '.join(motivos)} → {destino}")
        return None
    out.with_suffix(".json").write_text(json.dumps(side, ensure_ascii=False, indent=1), "utf-8")
    agentes.registrar(conta, r, out, side["formato"])
    try:  # o mesmo roteiro aprovado vira carrossel (a tarefa Marcas_Carrossel posta)
        from produto import carrossel
        carrossel.do_roteiro(conta, r, imgs, log, base=None if saida_dir == FILA / conta else saida_dir)
    except Exception as e:  # noqa: BLE001
        log(f"  [carrossel] não saiu: {type(e).__name__}: {str(e)[:140]}")
    shutil.rmtree(tmp, ignore_errors=True)
    vitrine(out, side, "NA FILA (vai ser postado)" if saida_dir == FILA / conta else "TESTE (não vai pra fila)")
    log(f"  [OK] {out} ({total:.1f}s)")
    return out


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--conta", required=True)
    ap.add_argument("--veo", action="store_true")
    ap.add_argument("--saida")
    a = ap.parse_args()
    gerar(a.conta, com_veo=a.veo, saida_dir=a.saida)
