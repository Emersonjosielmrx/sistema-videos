#!/usr/bin/env python3
"""pastas_empresas.py — Pasta publica no Drive de cada Instagram + cor da marca nos posts (dono 24/10).

"cada um deve ter sua pasta de conteudos no Drive [...] a pasta deve ser publica, assim as empresas que vao entrar
podem colocar seus conteudos na pasta e o sistema vai se virar de normalizar e postar fotos e videos a partir daquele
conteudo, colocando numa subpasta como usados pra reaproveitar se nao tiver, assim com balance com conteudos Veo".

- Marca/cor/produto de cada conta: config\\marcas_instagram.json (docs\\PASTAS_EMPRESAS.md).
- Drive: manhwa-drive:empresas/<conta>/entrada (a empresa coloca) e .../usados (o que ja saiu). Link de EDICAO aberto
  (decisao do dono 24/10); por isso TUDO passa pela checagem por visao antes de postar (nudez/violencia/contato).
- Video -> 1080x1920 com fundo e faixa na cor da marca, ate 90 s. Fotos -> Reel de ate 4 fotos (3,5 s cada) com
  moldura e faixa na cor da marca + trilha de licenca livre.
- postar_insta_auto.py pede itens() antes do Veo de reserva (no maximo metade das vagas do dia); postou -> usado()
  move os originais para usados/. Sem nada novo -> reaproveita 1 dos usados (o mais antigo, 1 vez a cada 7 dias).

    python pastas_empresas.py criar          # cria as pastas, libera o link e grava no json
    python pastas_empresas.py listar         # o que tem em cada entrada
    python pastas_empresas.py testar <conta> # prepara (sem postar) e mostra o arquivo gerado
"""
import base64
import json
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MARCAS = RAIZ / "config" / "marcas_instagram.json"
ESTADO = RAIZ / "config" / "pastas_empresas_estado.json"
CACHE = Path(r"D:\video-fila\empresas_cache")
RCLONE = r"D:\tools\rclone.exe"
REMOTO = "manhwa-drive:empresas"
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
GATEWAY = Path(r"D:\veo\beta\secrets\gateway.json")  # mesmo do comercial_veo
FONTE = r"D:\hipercool-materiais\assets\fonts\Montserrat-Black.ttf"
TRILHAS = [r"D:\hipercool-materiais\assets\trilhas\calm_chill.mp3",            # Serene View (Mixkit), licenca livre
           r"D:\hipercool-materiais\assets\trilhas\Beyond - Patrick Patrikios.mp3"]
FOTO = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
VIDEO = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}
W, H = 1080, 1920
REUSO_DIAS = 7


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return padrao


def _gravar(p, d):
    tmp = Path(str(p) + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(p)


def marcas():
    return _ler(MARCAS, {}).get("contas", {})


def _rc(*args, timeout=600):
    r = subprocess.run([RCLONE, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    if r.returncode:
        raise RuntimeError(f"rclone {args[0]}: {(r.stderr or r.stdout).strip()[-300:]}")
    return r.stdout


# 30/10: o manhwa-drive é escopo drive.file -> só enxerga o que o PRÓPRIO rclone subiu; o que a empresa coloca pelo
# link (navegador) fica invisível (a entrada da Advance tinha 14 arquivos e o rclone via 0). Ler/baixar/mover pelo
# colab649 (escopo drive inteiro), entrando pela pasta da conta (pasta_id do marcas_instagram.json).
LEITOR = "colab649"


def _loc(conta, caminho):
    """Args do rclone para <conta>/<caminho> vendo os arquivos de qualquer dono (cai no REMOTO sem pasta_id)."""
    pid = (marcas().get(conta) or {}).get("pasta_id")
    if pid:
        return [f"{LEITOR}:{caminho}", "--drive-root-folder-id", pid]
    return [f"{REMOTO}/{conta}/{caminho}"]


def _rgb(hexa):
    h = hexa.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ───────────────────────────── Drive ─────────────────────────────

def _token():
    _rc("about", "manhwa-drive:", timeout=120)  # renova o token no rclone.conf
    cfg = json.loads(_rc("config", "dump", timeout=60))["manhwa-drive"]
    return json.loads(cfg["token"])["access_token"]


def _liberar_edicao(pasta_id, tok):
    """Qualquer pessoa com o link pode colocar arquivos (escopo drive.file: vale pras pastas que o rclone criou)."""
    req = urllib.request.Request(
        f"https://www.googleapis.com/drive/v3/files/{pasta_id}/permissions?sendNotificationEmail=false",
        data=json.dumps({"role": "writer", "type": "anyone", "allowFileDiscovery": False}).encode(),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def criar():
    """Cria empresas/<conta>/{entrada,usados} pra toda conta do json, libera o link de edicao e grava o link."""
    dados = _ler(MARCAS, {})
    for conta in dados["contas"]:
        _rc("mkdir", f"{REMOTO}/{conta}/entrada")
        _rc("mkdir", f"{REMOTO}/{conta}/usados")
        _rc("mkdir", f"{REMOTO}/{conta}/fotos_base")  # 25/10: fotos do rosto do "clone" (apresentador) da empresa
    ids = {d["Name"]: d["ID"] for d in json.loads(_rc("lsjson", REMOTO, "--dirs-only"))}
    tok = _token()
    for conta, m in dados["contas"].items():
        if not ids.get(conta):
            print(f"{conta}: pasta sem ID")
            continue
        if m.get("pasta_id") != ids[conta] or not m.get("link"):
            for espera in (0, 20, 60, 120):  # 24/10: 403 na 6a seguida (limite de compartilhamento do Google)
                time.sleep(espera)
                try:
                    _liberar_edicao(ids[conta], tok)
                    break
                except urllib.error.HTTPError as e:
                    print(f"{conta}: {e.code} {e.read().decode('utf-8', 'replace')[:160]}")
            else:
                continue
            m["pasta_id"] = ids[conta]
            m["link"] = f"https://drive.google.com/drive/folders/{ids[conta]}"
            _gravar(MARCAS, dados)
            time.sleep(3)
        print(f"{conta:24} {m['link']}")


FOTOS_BASE_LOCAL = Path(r"D:\postador-de-videos\cache\fotos_base")


def fotos_base(conta, log=print):
    """25/10 (dono: "todo cliente tem que ter uma subpasta na pasta do Drive pra colocar suas fotos base para seus
    clones"): copia empresas/<conta>/fotos_base do Drive pra cache\\fotos_base\\<conta> (só imagens; o que sumiu do
    Drive sai daqui também). Devolve a pasta local (pode estar vazia)."""
    destino = FOTOS_BASE_LOCAL / conta
    destino.mkdir(parents=True, exist_ok=True)
    try:
        _rc("sync", *_loc(conta, "fotos_base"), str(destino), "--include", "*.{jpg,jpeg,png,webp,JPG,JPEG,PNG,WEBP}",
            timeout=900)
    except Exception as e:  # noqa: BLE001  (Drive fora: usa o que já estava aqui)
        log(f"[fotos_base] {conta}: Drive não respondeu ({str(e)[:120]}) - uso a cópia local")
    return destino


def eh_cliente(conta):
    """Empresa CLIENTE (marcas_instagram.json "cliente": true, ex.: MS Energy): o clone nunca é o dono."""
    return bool((marcas().get(conta) or {}).get("cliente"))


def clone_bases(conta, log=print):
    """De quem é o rosto do clone da conta (25/10, dono: "uma subpasta só pras fotos dos clones dentro da pasta do
    material; hoje seria a minha para todos, mas vão entrar mais 2 clientes que colocam as fotos deles"):
      (pasta, "empresa") — empresas/<conta>/fotos_base no Drive tem >= 3 fotos (quem chama confere o rosto)
      (None,  "dono")    — conta da casa (produto/tema) sem fotos: as fotos-base do dono (padrão do foto_na_hora;
                           elas NÃO vão pro Drive: a pasta tem link aberto de edição)
      (False, "cliente sem fotos") — cliente sem fotos: sem clone (nunca o rosto do dono num cliente)"""
    pasta = fotos_base(conta, log)
    fotos = [x for x in pasta.iterdir() if x.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    if len(fotos) >= 3:
        return pasta, "empresa"
    if eh_cliente(conta):
        return False, "cliente sem fotos"
    return None, "dono"


_DRIVE_FALHAS = [0]


def _arquivos(conta, sub):
    # 03/11: com a cota do Drive estourada (403 do cliente público do rclone) cada conta esperava até 2 x 240 s — a
    # rodada do Instagram das 10:22 acabou no prazo de 150 min sem 1 post e a das 13:02 ficou 1h45 parada aqui.
    # 2 falhas na rodada = o resto dela não consulta o Drive (posta com o que está no PC).
    if _DRIVE_FALHAS[0] >= 2:
        return []
    try:
        itens = json.loads(_rc("lsjson", *_loc(conta, sub), "--files-only", timeout=240))
    except (RuntimeError, subprocess.TimeoutExpired):  # 30/10: Drive no limite de requisições estourava o tempo
        _DRIVE_FALHAS[0] += 1
        if _DRIVE_FALHAS[0] == 2:
            print("  [Drive] 2 consultas das pastas das empresas falharam — o resto da rodada sem o Drive", flush=True)
        return []
    return sorted((i for i in itens if Path(i["Name"]).suffix.lower() in FOTO | VIDEO), key=lambda i: i["ModTime"])


# ───────────────────────────── checagem ─────────────────────────────

PERGUNTA = ("Esta imagem vai ser postada no Instagram de uma empresa. Responda SO com JSON: "
            '{"ok": true|false, "motivo": "..."} — ok=false se tiver nudez, conteudo sexual, violencia, sangue, '
            "armas, drogas, simbolo de odio, documento pessoal, ou se for so um print de conversa/tela. "
            "Telefone, @ ou site da PROPRIA empresa na imagem e permitido.")


def checar(jpg_bytes):
    """(ok, motivo) pela visao do gateway (mesmo do comercial_veo). Falha na checagem = NAO posta."""
    try:
        gw = json.loads(GATEWAY.read_text("utf-8"))
        corpo = {"model": "antigravity/gemini-3-flash", "max_tokens": 120, "messages": [{"role": "user", "content": [
            {"type": "text", "text": PERGUNTA},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(jpg_bytes).decode()}}]}]}
        req = urllib.request.Request(gw["gateway_url"].rstrip("/") + "/v1/chat/completions", data=json.dumps(corpo).encode(),
                                     headers={"Authorization": "Bearer " + gw["gateway_key"],
                                              "Content-Type": "application/json"})
        txt = json.loads(urllib.request.urlopen(req, timeout=90).read())["choices"][0]["message"]["content"]
        m = re.search(r'"ok"\s*:\s*(true|false)', txt, re.I)
        mot = re.search(r'"motivo"\s*:\s*"([^"]*)', txt)
        return (bool(m) and m.group(1).lower() == "true"), (mot.group(1) if mot else txt.strip()[:120])
    except Exception as e:  # noqa: BLE001
        return False, f"checagem falhou: {type(e).__name__}: {str(e)[:100]}"


def _quadro(arq, t=None):
    """JPEG pequeno (foto ou um quadro do video) para a checagem."""
    args = [FFMPEG, "-v", "error"] + (["-ss", f"{t:.2f}"] if t is not None else []) + [
        "-i", str(arq), "-frames:v", "1", "-vf", "scale=640:-2", "-f", "image2", "-vcodec", "mjpeg", "-"]
    return subprocess.run(args, capture_output=True, timeout=120).stdout


def _duracao(arq):
    r = subprocess.run([FFMPEG.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(arq)], capture_output=True, text=True, timeout=60)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _tem_audio(arq):
    r = subprocess.run([FFMPEG.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=index", "-of", "csv=p=0", str(arq)], capture_output=True, text=True,
                       timeout=60)
    return bool(r.stdout.strip())


# ───────────────────────────── cor da marca ─────────────────────────────

def faixa_png(marca, destino):
    """Faixa de baixo na cor da marca com o nome (sobreposta em todo Reel da conta)."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cor, texto = _rgb(marca["cor"]), _rgb(marca.get("texto", "#FFFFFF"))
    d.rectangle((0, H - 170, W, H), fill=cor + (255,))
    d.rectangle((0, H - 178, W, H - 170), fill=_rgb(marca.get("apoio", "#000000")) + (255,))
    f = ImageFont.truetype(FONTE, 64)
    nome = marca.get("marca", "")
    d.text(((W - d.textlength(nome, font=f)) / 2, H - 125), nome, font=f, fill=texto)
    im.save(destino)
    return destino


def _video(orig, saida, marca, faixa):
    """Video da empresa -> 1080x1920, conteudo inteiro (sem cortar) sobre a cor de apoio + faixa da marca, <= 90 s."""
    dur = min(_duracao(orig), 90)
    apoio, cor = marca.get("apoio", "#000000").lstrip("#"), marca["cor"].lstrip("#")
    # fundo = o proprio video desfocado e escurecido na cor de apoio; na frente o video inteiro com moldura da marca
    filtro = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,"
              f"drawbox=x=0:y=0:w=iw:h=ih:color=0x{apoio}@0.55:t=fill[fundo];"
              f"[b]scale={W - 120}:{H - 420}:force_original_aspect_ratio=decrease,"
              f"pad=iw+24:ih+24:12:12:color=0x{cor}[frente];"
              f"[fundo][frente]overlay=(W-w)/2:(H-180-h)/2,setsar=1[base];[base][1:v]overlay=0:0[v]")
    ent = ["-i", str(orig), "-i", str(faixa)]
    if _tem_audio(orig):
        mapa = ["-map", "[v]", "-map", "0:a"]
    else:
        ent += ["-stream_loop", "-1", "-i", random.choice([t for t in TRILHAS if Path(t).exists()])]
        filtro += ";[2:a]volume=0.35[a]"
        mapa = ["-map", "[v]", "-map", "[a]"]
    subprocess.run([FFMPEG, "-y", "-v", "error", *ent, "-filter_complex", filtro, *mapa, "-t", f"{dur:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", str(saida)], check=True, timeout=900)


def _fotos(fotos, saida, marca, faixa, seg=3.5):
    """Ate 4 fotos -> Reel: cada foto inteira com moldura na cor da marca, zoom leve, faixa da marca, trilha."""
    from PIL import Image, ImageFilter, ImageOps
    apoio, cor = _rgb(marca.get("apoio", "#000000")), _rgb(marca["cor"])
    quadros = []
    for i, f in enumerate(fotos):
        im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        # fundo = a propria foto desfocada e escurecida na cor de apoio (foto deitada nao deixa tela vazia)
        tela = Image.blend(ImageOps.fit(im, (W, H)).filter(ImageFilter.GaussianBlur(40)),
                           Image.new("RGB", (W, H), apoio), 0.55)
        im.thumbnail((W - 120, H - 420))
        x, y = (W - im.width) // 2, (H - 180 - im.height) // 2
        tela.paste(Image.new("RGB", (im.width + 24, im.height + 24), cor), (x - 12, y - 12))
        tela.paste(im, (x, y))
        q = saida.with_name(f"{saida.stem}_q{i}.png")
        tela.save(q)
        quadros.append(q)
    ent, partes = [], []
    for i, q in enumerate(quadros):
        ent += ["-loop", "1", "-t", f"{seg}", "-i", str(q)]
        partes.append(f"[{i}:v]scale={W}:{H},zoompan=z='min(zoom+0.0008,1.06)':d={int(seg * 30)}:s={W}x{H}:fps=30,"
                      f"setsar=1[f{i}]")
    n = len(quadros)
    ent += ["-i", str(faixa), "-stream_loop", "-1", "-i", random.choice([t for t in TRILHAS if Path(t).exists()])]
    filtro = ";".join(partes) + ";" + "".join(f"[f{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[c];" \
        f"[c][{n}:v]overlay=0:0[v];[{n + 1}:a]volume=0.4,afade=t=out:st={n * seg - 1:.1f}:d=1[a]"
    try:
        subprocess.run([FFMPEG, "-y", "-v", "error", *ent, "-filter_complex", filtro, "-map", "[v]", "-map", "[a]",
                        "-t", f"{n * seg:.1f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", str(saida)], check=True, timeout=900)
    finally:
        for q in quadros:
            q.unlink(missing_ok=True)


# ───────────────────────────── para o postador ─────────────────────────────

def _baixar(conta, sub, nome):
    d = CACHE / conta / "orig"
    d.mkdir(parents=True, exist_ok=True)
    dst = d / nome
    if not dst.exists():
        _rc("copyto", *_loc(conta, f"{sub}/{nome}"), str(dst), timeout=900)
    return dst


def _legenda(marca):
    if marca.get("produto"):
        return f"{marca['marca']} — fale com a gente no direct e veja como funciona na sua empresa."
    return f"{marca['marca']} · {marca.get('tema', '')}".strip(" ·")


def itens(conta, vagas, log=print):
    """Ate <vagas> Reels prontos (mp4 no PC) feitos do que a empresa colocou na pasta. Formato dos itens do
    catalogo (postar_insta_auto) + 'empresa': {conta, sub, arquivos} para usado()."""
    m = marcas().get(conta)
    if not m or vagas <= 0:
        return []
    velho = time.time() - 86400  # montagens que nao sairam (simulacao, erro de postagem) e originais baixados
    for p in (CACHE / conta).rglob("*") if (CACHE / conta).exists() else []:
        if p.is_file() and p.stat().st_mtime < velho:
            p.unlink(missing_ok=True)
    est = _ler(ESTADO, {})
    recusados = set(est.get("recusados", {}).get(conta, []))
    novos = [i for i in _arquivos(conta, "entrada") if i["Name"] not in recusados]
    sub = "entrada"
    if not novos:  # reaproveita 1 dos usados (o mais antigo que nao saiu nos ultimos REUSO_DIAS)
        usos = est.get("reuso", {}).get(conta, {})
        limite = (datetime.now() - timedelta(days=REUSO_DIAS)).isoformat()
        velhos = [i for i in _arquivos(conta, "usados") if usos.get(i["Name"], "") < limite]
        novos, sub, vagas = velhos, "usados", min(vagas, 1)
    if not novos:
        return []
    CACHE.mkdir(parents=True, exist_ok=True)
    faixa = faixa_png(m, CACHE / f"faixa_{conta}.png")
    saida_itens, fotos = [], []

    def recusar(nome, motivo):
        log(f"  [{conta}] RECUSADO {nome}: {motivo}")
        est.setdefault("recusados", {}).setdefault(conta, []).append(nome)
        _gravar(ESTADO, est)

    def fechar_fotos():
        if not fotos:
            return
        mp4 = CACHE / conta / f"fotos_{datetime.now():%Y%m%d_%H%M%S}_{len(saida_itens)}.mp4"
        _fotos([f for _, f in fotos], mp4, m, faixa)
        saida_itens.append(_item(conta, sub, mp4, [n for n, _ in fotos], m))
        fotos.clear()

    for i in novos:
        if len(saida_itens) >= vagas:
            break
        nome, ext = i["Name"], Path(i["Name"]).suffix.lower()
        try:
            orig = _baixar(conta, sub, nome)
        except Exception as e:  # noqa: BLE001
            log(f"  [{conta}] {nome}: nao baixou ({e})")
            continue
        if ext in FOTO:
            ok, mot = checar(_quadro(orig))
            if not ok:
                recusar(nome, mot)
                continue
            fotos.append((nome, orig))
            if len(fotos) == 4:
                fechar_fotos()
            continue
        dur = _duracao(orig)
        if dur < 2:
            recusar(nome, "video vazio ou corrompido")
            continue
        quadros = [_quadro(orig, dur * f) for f in (0.15, 0.5, 0.85)]
        ruim = next((mot for ok, mot in map(checar, quadros) if not ok), None)
        if ruim:
            recusar(nome, ruim)
            continue
        mp4 = CACHE / conta / f"video_{Path(nome).stem[:40]}_{datetime.now():%H%M%S}.mp4"
        try:
            _video(orig, mp4, m, faixa)
        except Exception as e:  # noqa: BLE001
            log(f"  [{conta}] {nome}: nao normalizou ({e})")
            continue
        saida_itens.append(_item(conta, sub, mp4, [nome], m))
    if len(saida_itens) < vagas:
        fechar_fotos()
    for it in saida_itens:
        log(f"  [{conta}] pasta da empresa: {it['nome']} ({len(it['empresa']['arquivos'])} arquivo(s) de {sub})")
    return saida_itens


def _item(conta, sub, mp4, arquivos, marca):
    return {"caminho": str(mp4), "nome": mp4.name, "bytes": mp4.stat().st_size, "projeto": "empresa", "origem": "",
            "no_pc": True, "drive": None, "tipo": "final", "postagens": [], "reserva": None, "conta_reuso": conta,
            "legenda": _legenda(marca), "empresa": {"conta": conta, "sub": sub, "arquivos": arquivos}}


def usado(v, log=print):
    """Depois de postado: originais de entrada/ vao para usados/; reaproveitado ganha a data no estado."""
    e = v.get("empresa") or {}
    conta = e.get("conta")
    est = _ler(ESTADO, {})
    for nome in e.get("arquivos", []):
        if e.get("sub") == "entrada":
            ori = _loc(conta, f"entrada/{nome}")
            try:
                _rc("moveto", ori[0], _loc(conta, f"usados/{nome}")[0], *ori[1:], timeout=300)
            except Exception as ex:  # noqa: BLE001
                # 06/11: arquivo que o CLIENTE subiu pelo link é dele — o Drive não deixa outra conta mover
                # (403 cannotAddParent, 3 tentativas a cada post). Copia pra usados/ e tira da entrada (apagar o próprio
                # atalho da pasta compartilhada é permitido); se nem isso, o estado "reuso" abaixo já marca como usado.
                if "cannotAddParent" in str(ex) or "insufficientFilePerm" in str(ex):  # 07/11: as 2 formas do 403
                    try:
                        _rc("copyto", ori[0], _loc(conta, f"usados/{nome}")[0], *ori[1:], timeout=300)
                        _rc("deletefile", ori[0], *ori[1:], timeout=120)
                        log(f"  [{conta}] {nome}: copiado pra usados (era do cliente, não dava pra mover)")
                    except Exception as ex2:  # noqa: BLE001
                        log(f"  [{conta}] {nome}: fica na entrada (arquivo do cliente) — marcado como usado ({str(ex2)[:80]})")
                else:
                    log(f"  [{conta}] nao movi {nome} para usados: {ex}")
        est.setdefault("reuso", {}).setdefault(conta, {})[nome] = datetime.now().isoformat(timespec="seconds")
    _gravar(ESTADO, est)
    Path(v["caminho"]).unlink(missing_ok=True)


def listar():
    for conta, m in marcas().items():
        print(f"{conta:24} entrada={len(_arquivos(conta, 'entrada')):3}  usados={len(_arquivos(conta, 'usados')):3}  "
              f"{m.get('link', '(sem pasta)')}")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "listar"
    if cmd == "criar":
        criar()
    elif cmd == "listar":
        listar()
    elif cmd == "fotos_base":  # fotos_base [conta]: baixa as fotos do clone (todas as contas sem argumento)
        for c in ([sys.argv[2]] if len(sys.argv) > 2 else list(marcas())):
            p = fotos_base(c)
            print(f"{c:24} {len([x for x in p.iterdir() if x.is_file()])} foto(s) em {p}")
    elif cmd == "testar" and len(sys.argv) > 2:
        for it in itens(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2):
            print(it["caminho"], it["empresa"])
    else:
        print(__doc__)
