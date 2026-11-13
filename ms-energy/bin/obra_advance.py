# -*- coding: utf-8 -*-
r"""obra_advance.py — Reel da ADVANCE com o MATERIAL REAL que a empresa coloca na pasta do Drive (30/10, dona:
"usando também o material novo que foi colocado na pasta de compartilhamento dele").

Pasta: empresas/advance_novoestrela/entrada (link aberto de edição; ver postador\docs\PASTAS_EMPRESAS.md — lida pelo
remote colab649, o manhwa-drive não enxerga o que a empresa sobe pelo navegador).
Sem Veo e sem voz sintética (a Thalita pura é proibida na Advance): foto/vídeo REAL na parte de cima da tela, frase no
topo, legenda do roteiro embaixo (tempo distribuído; fala curta para dar tempo de ler), trilha livre e cartão da
Advance (montagem_ms com a troca de marca do reel_advance). Cada arquivo é classificado por visão (cliente / obra usam;
selfie, oferta, print, ruim e proibido ficam fora — oferta pode estar vencida, só com a dona); classificação guardada
no estado do pastas_empresas. Um assunto por Reel (cliente = prova social com a pauta "clientes"; obra = pauta normal)
e um mesmo cliente só uma vez. Depois de postado o original vai para usados/. No histórico do perfil, vídeo real teve
~25x mais views que IA (docs\ANALISE_CAMPANHA.md frente 4).

    D:\veo\venv\Scripts\python.exe obra_advance.py --listar
    D:\veo\venv\Scripts\python.exe obra_advance.py --so-gerar
    D:\veo\venv\Scripts\python.exe obra_advance.py            # gera e posta (respeita intervalo e pausa da conta)
"""
import argparse
import base64
import json
import random
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\ms-energy\bin")
sys.path.insert(0, r"D:\veo\beta")
sys.path.insert(0, r"D:\postador-de-videos\bin")
import pastas_empresas as pe  # noqa: E402
import reel_advance as ra  # noqa: E402

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
CONTA = ra.CONTA
SAIDA = ra.SAIDA
TMP = Path(r"D:\ms-energy\cache\tmp_obra_advance")
TRILHAS = [r"D:\hipercool-materiais\assets\trilhas\calm_chill.mp3",
           r"D:\hipercool-materiais\assets\trilhas\Beyond - Patrick Patrikios.mp3"]
VOLUME = 0.30
W, H = 1080, 1920
AREA = (int(H * 0.11), int(H * 0.60))  # foto/vídeo entre 11% e 60% da altura: a legenda (~66%) não cobre a obra
TRECHO_MIN, TRECHO_MAX = 3.0, 6.0
MAX_ITENS = 4
DUR_MIN = 8.0
FALA_MIN, FALA_MAX = 10, 22  # sem voz a fala é lida: 40 palavras (1º teste 30/10) não dava tempo
S_POR_PALAVRA = 0.42


def log(msg):
    ra.log(msg)


def _dur(p):
    return pe._duracao(p)


def material():
    """Fotos/vídeos novos da pasta entrada (fora os recusados), do mais antigo ao mais novo."""
    est = pe._ler(pe.ESTADO, {})
    recusados = set(est.get("recusados", {}).get(CONTA, []))
    # 31/10: o Drive recusa mover para usados/ (403 cannotAddParent) e o Reel das 14:12 repetiu as 4 fotos do das
    # 08:09 -> o que já foi postado sai da lista SEMPRE, mesmo que continue na entrada
    postados = {n for j in SAIDA.glob("advance_obra_*.json")
                for n in (json.loads(j.read_text("utf-8")).get("drive_arquivos") or [])
                if json.loads(j.read_text("utf-8")).get("postado")}
    postados |= set(est.get("reuso", {}).get(CONTA, {}))
    itens = [i for i in pe._arquivos(CONTA, "entrada") if i["Name"] not in postados]
    if not itens:  # Drive fora/no limite: o que já foi baixado e aprovado pela visão (ainda não postado)
        orig = pe.CACHE / CONTA / "orig"
        itens = [{"Name": n, "ModTime": "", "Size": (orig / n).stat().st_size}
                 for n, c in est.get("classificados", {}).get(CONTA, {}).items()
                 if c.get("tipo") in USAR and (orig / n).exists() and n not in postados]
    return [i for i in itens if i["Name"] not in recusados]


PERGUNTA = (
    "Esta imagem foi enviada por uma empresa de energia solar para o Instagram dela. Classifique e responda SO com JSON "
    '{"tipo": "...", "cliente_nome": "...", "motivo": "..."}. tipo: "cliente" = pessoa da empresa com cliente(s) '
    '(entrega/assinatura de projeto), pode ter moldura/arte com o nome do cliente; "obra" = instalação, placas solares, '
    'equipe trabalhando, inversor; "selfie" = só uma pessoa sozinha (selfie/retrato), sem cliente; "oferta" = arte de '
    'promoção com preço, brinde, condição de pagamento ou data; "print" = captura de tela, post/story de outra conta, '
    'notícia, interface de app — se aparecerem ícones de curtir/comentar/compartilhar, "..." ou barra de story do '
    'Instagram é "print" mesmo que a foto seja boa; "ruim" = tremida, escura, borrada ou sem assunto; "proibido" = '
    'nudez, violência, armas, documento pessoal. cliente_nome = nome do cliente escrito na imagem, ou "".')
USAR = {"cliente", "obra"}


def classificar(nome, orig):
    """(tipo, cliente_nome, motivo) pela visão do gateway; guardado no estado (a visão leva ~1 min por foto).
    Falha = 'ruim' (não posta) e não fica guardado."""
    est = pe._ler(pe.ESTADO, {})
    feito = est.get("classificados", {}).get(CONTA, {}).get(nome)
    if feito:
        return feito["tipo"], feito.get("cliente_nome", ""), feito.get("motivo", "")
    try:
        gw = json.loads(pe.GATEWAY.read_text("utf-8"))
        corpo = {"model": "gemini/gemini-3.5-flash", "max_tokens": 200, "messages": [{"role": "user", "content": [
            {"type": "text", "text": PERGUNTA},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," +
                                                base64.b64encode(pe._quadro(orig)).decode()}}]}]}
        req = urllib.request.Request(gw["gateway_url"].rstrip("/") + "/v1/chat/completions",
                                     data=json.dumps(corpo).encode(),
                                     headers={"Authorization": "Bearer " + gw["gateway_key"],
                                              "Content-Type": "application/json"})
        txt = json.loads(urllib.request.urlopen(req, timeout=90).read())["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001
        return "ruim", "", f"classificação falhou: {type(e).__name__}"
    t = re.search(r'"tipo"\s*:\s*"(\w+)"', txt)
    c = re.search(r'"cliente_nome"\s*:\s*"([^"]*)', txt)
    m = re.search(r'"motivo"\s*:\s*"([^"]*)', txt)
    r = {"tipo": t.group(1).lower() if t else "ruim", "cliente_nome": (c.group(1) if c else "").strip(),
         "motivo": m.group(1) if m else txt[:100]}
    est = pe._ler(pe.ESTADO, {})
    est.setdefault("classificados", {}).setdefault(CONTA, {})[nome] = r
    pe._gravar(pe.ESTADO, est)
    return r["tipo"], r["cliente_nome"], r["motivo"]


def _jpg(orig):
    """HEIC/PNG/WEBP -> JPG pelo ffmpeg (o Pillow daqui não abre HEIC)."""
    if Path(orig).suffix.lower() in (".jpg", ".jpeg"):
        return orig
    j = Path(orig).with_suffix(".jpg")
    if not j.exists():
        subprocess.run([FF, "-y", "-v", "error", "-i", str(orig), "-frames:v", "1", "-q:v", "2", str(j)],
                       capture_output=True, timeout=120)
    return j if j.exists() else orig


def _recusar(nome, motivo):
    log(f"  [OBRA] RECUSADO {nome}: {motivo}")
    est = pe._ler(pe.ESTADO, {})
    est.setdefault("recusados", {}).setdefault(CONTA, []).append(nome)
    pe._gravar(pe.ESTADO, est)


def _trecho(orig, ini, dur, saida):
    """Trecho de vídeo: o quadro inteiro (sem cortar a obra) na AREA, sobre ele mesmo desfocado; sem o áudio original."""
    alto = AREA[1] - AREA[0]
    fc = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,"
          f"eq=brightness=-0.12[f];[b]scale={W - 60}:{alto}:force_original_aspect_ratio=decrease[c];"
          f"[f][c]overlay=(W-w)/2:{AREA[0]}+({alto}-h)/2,fps=30,setsar=1,format=yuv420p[v]")
    r = subprocess.run([FF, "-y", "-v", "error", "-ss", f"{ini:.2f}", "-t", f"{dur:.2f}", "-i", str(orig),
                        "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "19", str(saida)], capture_output=True, text=True, timeout=600)
    return r.returncode == 0 and Path(saida).exists()


def _foto(orig, dur, saida):
    """Foto -> trecho com zoom lento: foto inteira na AREA (cantos arredondados) sobre ela mesma desfocada."""
    from PIL import Image, ImageDraw, ImageFilter, ImageOps
    im = ImageOps.exif_transpose(Image.open(orig)).convert("RGB")
    tela = ImageOps.fit(im, (W, H)).filter(ImageFilter.GaussianBlur(36))
    tela = Image.blend(tela, Image.new("RGB", (W, H), (0, 0, 0)), 0.35)
    im.thumbnail((W - 60, AREA[1] - AREA[0]))
    mascara = Image.new("L", im.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, *im.size), radius=28, fill=255)
    tela.paste(im, ((W - im.width) // 2, AREA[0] + (AREA[1] - AREA[0] - im.height) // 2), mascara)
    q = Path(saida).with_suffix(".png")
    tela.save(q)
    n = int(dur * 30)
    r = subprocess.run([FF, "-y", "-v", "error", "-loop", "1", "-t", f"{dur:.2f}", "-i", str(q), "-vf",
                        f"scale={W * 2}:{H * 2},zoompan=z='min(zoom+0.0005,1.05)':x='iw/2-(iw/zoom/2)':"
                        f"y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps=30,setsar=1,format=yuv420p",
                        "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", str(saida)],
                       capture_output=True, text=True, timeout=600)
    q.unlink(missing_ok=True)
    return r.returncode == 0 and Path(saida).exists()


def _chave_cliente(nome):
    r"""Nome do cliente comparável: 30/10 a visão devolveu "MARIA JOSÉ" numa foto e "MARIA JOS�" na outra."""
    import unicodedata
    n = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), nome or "")
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()
    n = re.sub(r"[^a-z]", "", n)
    return n if len(n) >= 4 else ""


def escolher(log=log):
    """Baixa e classifica. Devolve (fontes, assunto): fontes = [{"nome", "orig", "video": bool, "dur"}] de UM assunto
    ('cliente' ou 'obra'), sem repetir o mesmo cliente, até MAX_ITENS (vídeo conta como até 2)."""
    TMP.mkdir(parents=True, exist_ok=True)
    novos = material()
    novos.sort(key=lambda i: Path(i["Name"]).suffix.lower() not in pe.VIDEO)  # vídeo primeiro: movimento segura mais
    fontes, assunto, clientes = [], None, set()
    for item in novos:
        if sum(2 if f["video"] else 1 for f in fontes) >= MAX_ITENS:
            break
        nome = item["Name"]
        try:
            orig = pe._baixar(CONTA, "entrada", nome)
        except Exception as e:  # noqa: BLE001  (limite do Drive: fica para a próxima rodada)
            log(f"  [OBRA] {nome}: não baixou ({str(e)[:100]})")
            continue
        video = Path(nome).suffix.lower() in pe.VIDEO
        if video:
            d = _dur(orig)
            if d < 2:
                _recusar(nome, "vídeo vazio ou corrompido")
                continue
            q = TMP / f"q_{Path(nome).stem}.jpg"
            q.write_bytes(pe._quadro(orig, d * 0.5))
            tipo, cli, mot = classificar(nome, q)
            if tipo in USAR:
                ruim = next((m for ok, m in (pe.checar(pe._quadro(orig, d * f)) for f in (0.15, 0.85)) if not ok), None)
                if ruim:
                    tipo, mot = "proibido", ruim
        else:
            orig = _jpg(orig)
            d = 0.0
            tipo, cli, mot = classificar(nome, orig)
        if tipo not in USAR:
            # selfie = rosto do Luiz (vai à mão para clone_bases); oferta pode estar vencida -> só com a dona
            _recusar(nome, f"{tipo}: {mot}")
            continue
        if assunto and tipo != assunto:
            continue  # um assunto por Reel; o outro fica na entrada para a próxima rodada
        chave = _chave_cliente(cli)
        if chave and any(chave.startswith(c) or c.startswith(chave) for c in clientes):
            log(f"  [OBRA] {nome}: mesmo cliente ({cli}) já está neste Reel — fica para outro")
            continue
        if chave:
            clientes.add(chave)
        assunto = tipo
        fontes.append({"nome": nome, "orig": Path(orig), "video": video, "dur": d})
    return fontes, assunto


def renderizar(fontes, precisa):
    """Trechos com a duração que a leitura da fala pede (sem repetir foto). Devolve (trechos, foto_fundo)."""
    pedacos = []  # (fonte, inicio)
    for f in fontes:
        if f["video"] and f["dur"] >= TRECHO_MIN * 2.5:
            pedacos += [(f, f["dur"] * 0.25), (f, f["dur"] * 0.6)]
        else:
            pedacos.append((f, max(0.0, (f["dur"] - TRECHO_MAX) / 3) if f["video"] else 0.0))
    # +0,5 s de folga: foto arredonda para quadro inteiro e a base repetia o 1º trecho por décimos (30/10)
    cada = min(TRECHO_MAX, max(TRECHO_MIN, (precisa + 0.5 + 0.3 * (len(pedacos) - 1)) / len(pedacos)))
    trechos, fundo = [], None
    for i, (f, ini) in enumerate(pedacos):
        t = TMP / f"t{i}.mp4"
        dur = min(cada, f["dur"] - ini) if f["video"] else cada
        if (_trecho(f["orig"], ini, dur, t) if f["video"] else _foto(f["orig"], dur, t)):
            trechos.append(t)
        if fundo is None:
            fundo = f["orig"] if not f["video"] else None
    return trechos, fundo


def base(trechos, saida, dur_min=DUR_MIN):
    """Emenda os trechos (fade 0,3 s) e põe a trilha; só repete trecho se o material não cobrir dur_min."""
    lens = [_dur(t) for t in trechos]
    while sum(lens) - 0.3 * (len(lens) - 1) < dur_min - 0.6 and len(lens) < 12:
        trechos, lens = trechos + trechos[:1], lens + lens[:1]
    ent, fc = [], []
    for i, t in enumerate(trechos):
        ent += ["-i", str(t)]
        fc.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]")
    atual, pos = "v0", lens[0]
    for i in range(1, len(trechos)):
        fc.append(f"[{atual}][v{i}]xfade=transition=fade:duration=0.3:offset={pos - 0.3:.2f}[x{i}]")
        atual, pos = f"x{i}", pos + lens[i] - 0.3
    n = len(trechos)
    ent += ["-stream_loop", "-1", "-i", random.choice([t for t in TRILHAS if Path(t).exists()])]
    fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{pos:.2f},asetpts=PTS-STARTPTS,"
              f"volume={VOLUME},afade=t=in:d=0.5[a]")
    r = subprocess.run([FF, "-y", "-v", "error", *ent, "-filter_complex", ";".join(fc), "-map", f"[{atual}]",
                        "-map", "[a]", "-t", f"{pos:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                        "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", str(saida)],
                       capture_output=True, text=True, timeout=900, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        log(f"  [OBRA] base falhou: {r.stderr[-400:]}")
        return None
    return round(pos, 2)


def _roteiro(assunto, log=log):
    """Roteiro 'video_real' com a fala CURTA (é lida, não ouvida); cliente -> pauta 'clientes' (prova social)."""
    import roteiro_ms
    orig = roteiro_ms.escolher_pauta, roteiro_ms._max_palavras, roteiro_ms._min_palavras
    if assunto == "cliente":
        pauta = next(p for p in roteiro_ms.PAUTAS if p[0] == "clientes")
        roteiro_ms.escolher_pauta = lambda *a, **k: pauta
    roteiro_ms._max_palavras = lambda tipo: FALA_MAX
    roteiro_ms._min_palavras = lambda tipo: FALA_MIN
    try:
        r = roteiro_ms.gerar("video_real", log=log)
    finally:
        roteiro_ms.escolher_pauta, roteiro_ms._max_palavras, roteiro_ms._min_palavras = orig
    if assunto == "cliente":
        # 30/10: a legenda do LLM inventou "a maior parte dos projetos vem de indicação" -> texto fixo, sem fato novo
        r["legenda_insta"] = ra._legendas_advance(
            "Mais clientes de Castanhal e região fecharam o projeto de energia solar com a Advance. "
            "Obrigado pela confiança! 💜", r["pauta"])[0]
    return r


def gerar(log=log):
    ra.trocar_marca()
    import montagem_ms
    import qa_ms
    import roteiro_ms
    from gerar_short_veo import _nivelar_audio
    fontes, assunto = escolher(log)
    if not fontes:
        log("  [OBRA] pasta entrada sem material aprovado")
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    roteiro = _roteiro(assunto, log)
    precisa = max(DUR_MIN, len(roteiro["fala_final"].split()) * S_POR_PALAVRA + 1.2)
    trechos, fundo = renderizar(fontes, precisa)
    log(f"  [OBRA] {len(fontes)} arquivos / {len(trechos)} trechos ({assunto}) | fala: {roteiro['fala_final']}")
    if not trechos:
        return None
    b = TMP / f"base_{ts}.mp4"
    if not base(trechos, b, precisa):
        return None
    SAIDA.mkdir(parents=True, exist_ok=True)
    out = SAIDA / f"advance_obra_{ts}.mp4"
    ok, info = montagem_ms.montar(b, roteiro, [], out, foto_fundo=str(fundo) if fundo else None, log=log)
    if not ok:
        return None
    _nivelar_audio(out, log)
    final = qa_ms.checar_final(out, log=log)
    usados = [f["nome"] for f in fontes]
    import gerar_short_veo as _g  # 06/11: sem "_empresa" a trava_empresa recusava TODO Reel de obra (5 seguidos 15h–17h30)
    side = {"conta": CONTA, "_empresa": _g._empresa_atual(), "tipo_video": "obra_real", "pipeline": "obra_advance",
            "assunto": assunto,
            "pauta": roteiro["pauta"], "fala": roteiro["fala_final"], "gancho_tela": roteiro["gancho_tela"],
            "legenda_insta": roteiro["legenda_insta"], "legendas": info["legendas"], "drive_arquivos": usados,
            "qa_final": final, "gerado_em": datetime.now().isoformat(timespec="seconds")}
    if not final["ok"]:
        destino = Path(r"D:\ms-energy\videos\_revisar") / out.name
        destino.parent.mkdir(exist_ok=True)
        shutil.move(str(out), str(destino))
        destino.with_suffix(".json").write_text(json.dumps(side, ensure_ascii=False, indent=2), "utf-8")
        log(f"  [OBRA] reprovado na trava final ({'; '.join(final['motivos'])}) -> {destino}")
        return None
    out.with_suffix(".json").write_text(json.dumps(side, ensure_ascii=False, indent=2), "utf-8")
    roteiro_ms.registrar(roteiro, out.stem)
    shutil.rmtree(TMP, ignore_errors=True)
    log(f"  [OBRA] Reel aprovado: {out} ({final['dur']} s) com {usados}")
    return out


def marcar_usados(mp4, log=log):
    """Depois de postado: originais de entrada/ -> usados/ (o mesmo do postador)."""
    side = json.loads(Path(mp4).with_suffix(".json").read_text("utf-8"))
    pe.usado({"empresa": {"conta": CONTA, "sub": "entrada", "arquivos": side.get("drive_arquivos", [])},
              "caminho": str(TMP / "_nada")}, log=log)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--so-gerar", action="store_true")
    a = ap.parse_args()
    if a.listar:
        for i in material():
            print(f"{i['ModTime'][:16]}  {i['Size'] / 1e6:7.1f} MB  {i['Name']}")
        return
    mp4 = gerar()
    if mp4 and not a.so_gerar and ra.ca.espaco_ok(log):
        ra.postar(mp4)
        marcar_usados(mp4)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
