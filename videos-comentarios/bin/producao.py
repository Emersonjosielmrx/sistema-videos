# -*- coding: utf-8 -*-
"""producao.py — produção e postagem automáticas dos Shorts de comentários (canal Comédia Noturna).

Fonte: Shorts do parceiro @risohit (mais vistos primeiro). Para cada um: baixa em 1080p, a IA lê nos quadros a cena e
os comentários dos prints, cada comentário vai para um personagem de comédia (rodízio de vozes clonadas), renderiza com
comentarios_video.montar e grava video.mp4 + postar.json em D:\\hipercool-materiais\\videos-comentarios\\<data>_<id>\\.
Postagem: politica.postar_youtube (agenda central, sempre agendado, teto 3/dia do canal).

    python bin/producao.py ciclo        # tarefa ComentariosProducao: lista (12 h), produz 1 se o estoque é baixo, posta 1
    python bin/producao.py listar | produzir [id] | postar | status
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJETO / "bin"))
sys.path.append(r"D:\hipercool-materiais\comum")
sys.path.append(r"D:\postador-de-videos\bin")
sys.path.append(r"D:\video-fila")
import comentarios_video as cv  # noqa: E402

FONTE = "https://www.youtube.com/@risohit/shorts"
CANAL = "novo_comedianoturna"
NOME_PROJETO = "comentarios"
ESTADO = PROJETO / "estado" / "fila.json"
SAIDA = Path(r"D:\hipercool-materiais\videos-comentarios")
DOWNLOADS = PROJETO / "downloads"
LOG = PROJETO / "logs" / "producao.log"
ESTOQUE_MAX = 4          # vídeos prontos ainda não postados
POSTAR_ATE_H = 36        # só sobe se a vaga de publicação for nas próximas 36 h (o resto fica no estoque)
RAM_MIN_GB = 3.0
YTDLP = shutil.which("yt-dlp") or r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\Scripts\yt-dlp.exe"

ELENCO = ["chaves_chapolin", "quico", "chiquinha", "seu_madruga", "professor_girafales", "faustao", "silvio_santos",
          "chapolin_colorado", "galvao_bueno", "cid_moreira", "bob_esponja", "lula_molusco", "seu_sirigueijo_peter_griffin",
          "burro_shrek", "shrek_bussunda", "pica_pau", "patolino", "pernalonga", "pato_donald", "salsicha", "joao_grilo",
          "gru_hassum", "mestre_kame", "dinho_mamonas_assassinas", "ronaldo_fenomeno", "deadpool_reginaldo",
          "apostolo_valdemiro_santiago", "luiz_carlos_persy", "ivete_sangalo", "ludmilla"]
FORA = {"lula", "bolsonaro"}
TRILHAS = ["A Fool_s Theme - Brian Bolger.mp3", "Bella Bella Beat - Nana Kwabena.mp3",
           "AUTOMOTIVO SUPER MARIO WORLD 2 (INSTRUMENTAL) (128 kbps).mp3",
           "( Lofi Sem Direitos Autorais ) Cheel - Anywhen You Say (128 kbps).mp3"]
DIR_TRILHAS = Path(r"D:\hipercool-materiais\assets\trilhas")


def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    if sys.stdout:
        print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def ler():
    if ESTADO.exists():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {"fontes": {}, "uso_vozes": {}, "listado_em": None}


def gravar(est):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ESTADO)


def rodar(cmd, timeout=None):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, creationflags=cv.SEM_JANELA,
                          timeout=timeout, encoding="utf-8", errors="replace")


# ───────── fonte ─────────
def listar(est, forcar=False):
    if not forcar and est.get("listado_em") and \
            datetime.now() - datetime.fromisoformat(est["listado_em"]) < timedelta(hours=12):
        return
    import ytdlp_vez
    if getattr(ytdlp_vez, "pausado", lambda: None)():
        log("listar: yt-dlp em pausa (bloqueio do YouTube) — fica pra depois")
        return
    with ytdlp_vez.vez("comentarios: lista do @risohit"):
        r = rodar([YTDLP, "--flat-playlist", "-J", "--playlist-end", "300", FONTE], timeout=600)
    if r.returncode != 0:
        log(f"listar: yt-dlp falhou: {r.stderr[-300:]}")
        return
    novos = 0
    for e in json.loads(r.stdout).get("entries") or []:
        f = est["fontes"].setdefault(e["id"], {"estado": "novo"})
        novos += f.get("titulo") is None
        f.update(titulo=e.get("title"), views=e.get("view_count") or 0)
    est["listado_em"] = datetime.now().isoformat(timespec="seconds")
    gravar(est)
    log(f"listar: {len(est['fontes'])} Shorts na fonte ({novos} novos)")


def baixar(vid):
    import ytdlp_vez
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    mp4 = DOWNLOADS / f"risohit_{vid}.mp4"
    if mp4.exists():
        return mp4
    with ytdlp_vez.vez(f"comentarios: baixar {vid}"):
        r = rodar([YTDLP, "--ffmpeg-location", r"D:\hipercool-materiais\bin", "-f","137+140/bv*[height>=1080]+ba/b", "--merge-output-format", "mp4", "--no-playlist",
                   "-o", str(mp4), f"https://www.youtube.com/shorts/{vid}"], timeout=900)
    if r.returncode != 0 or not mp4.exists():
        raise RuntimeError(f"download falhou: {r.stderr[-300:]}")
    return mp4


# ───────── IA: ler os comentários, montar elenco, metadados ─────────
def ler_quadros(mp4, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    for q in pasta.glob("q_*.jpg"):
        q.unlink()
    dur = cv.duracao(mp4)
    tempos = [dur * (i + 0.5) / 16 for i in range(16)]  # 16 quadros espalhados pelo vídeo inteiro
    for i, t in enumerate(tempos, 1):
        rodar([cv.FFMPEG, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", mp4, "-frames:v", "1", "-vf", "scale=540:-1",
               pasta / f"q_{i:02d}.jpg"])
    arqs = sorted(pasta.glob("q_*.jpg"))
    imagens = [q.read_bytes() for q in arqs]
    prompt = ("Estes são 16 quadros, em ordem (Painel 1 = início), de um Short brasileiro de humor: um vídeo viral com "
              "prints de comentários de redes sociais (Instagram/TikTok) aparecendo por cima. Extraia:\n"
              "- titulo_tela: o texto fixo no topo do vídeo, se houver (senão \"\");\n"
              "- cena: 1 frase dizendo o que acontece no vídeo viral;\n"
              "- comentarios: cada comentário que aparece nos prints, com o TEXTO EXATO como está escrito (sem "
              "@usuario, sem tempo, sem curtidas, sem 'Responder', sem emojis) e o número do 1º Painel em que ele "
              "aparece; sem repetir; na ordem em que aparecem.\n"
              "- prints_regiao: em que parte da tela os prints de comentário aparecem na maior parte do tempo: \"topo\", "
              "\"meio\" ou \"baixo\".\n"
              'Responda SÓ JSON: {"titulo_tela": "...", "cena": "...", "prints_regiao": "baixo", '
              '"comentarios": [{"texto": "...", "painel": 1}]}')
    txt = cv.ia(prompt, imagens)
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        raise RuntimeError(f"IA não devolveu JSON: {txt[:200]}")
    dados = json.loads(m.group(0))
    vistos, coms = set(), []
    for c in dados.get("comentarios") or []:
        texto, painel = (c.get("texto"), c.get("painel")) if isinstance(c, dict) else (c, None)
        texto = re.sub(r"\s+", " ", str(texto or "")).strip(" \"'")
        if len(texto) < 4 or cv._norm(texto) in vistos:
            continue
        vistos.add(cv._norm(texto))
        try:
            t_src = round(tempos[max(1, min(16, int(painel))) - 1] - dur / 32, 2)
        except (TypeError, ValueError):
            t_src = None
        coms.append({"texto": texto, "t_src": t_src})
    coms.sort(key=lambda x: x["t_src"] if x["t_src"] is not None else 999)
    dados["comentarios"] = coms
    return dados


def vozes_disponiveis():
    ok = []
    for v in ELENCO:
        d = cv.VOZES / v
        if v not in FORA and (d / f"{v}.pth").exists() and (d / "personagem.json").exists() and \
                (d / "linguagem_v2.json").exists():
            ok.append(v)
    return ok


def montar_elenco(est, n):
    uso = est.setdefault("uso_vozes", {})
    vozes = vozes_disponiveis()
    random.shuffle(vozes)
    vozes.sort(key=lambda v: uso.get(v, 0))
    escolhidas = vozes[:n]
    for v in escolhidas:
        uso[v] = uso.get(v, 0) + 1
    return escolhidas


def nome_personagem(voz):
    nome = json.loads((cv.VOZES / voz / "personagem.json").read_text(encoding="utf-8")).get("nome", voz)
    return re.sub(r"\s*\(.*?\)", "", nome).strip() or voz


def metadados(dados, falas):
    prompt = ("Short de humor do canal Comédia Noturna: personagens famosos (" +
              ", ".join(f["nome"] for f in falas) + ") zoam os comentários de um vídeo viral.\n"
              f"Cena: {dados.get('cena')}\nTexto do vídeo: {dados.get('titulo_tela')}\n"
              "Comentários: " + " | ".join(f["comentario"] for f in falas) + "\n\n"
              "Crie: titulo (até 60 caracteres, curto, provocativo, estilo meme brasileiro, sem aspas, com no máximo 1 "
              "emoji), descricao (2 frases + 4 hashtags incluindo #shorts e #comentarios) e tags (8 palavras-chave).\n"
              'Responda SÓ JSON: {"titulo": "...", "descricao": "...", "tags": ["..."]}')
    meta = {}
    for tentativa in range(2):
        try:
            txt = cv.ia(prompt)
            m = re.search(r"\{.*\}", txt if isinstance(txt, str) else json.dumps(txt), re.S)
            meta = json.loads(m.group(0))
            break
        except Exception as e:  # noqa: BLE001
            log(f"metadados: IA falhou ({e}){'; tentando de novo' if tentativa == 0 else '; usando o texto do vídeo'}")
    titulo = (meta.get("titulo") or dados.get("titulo_tela") or "A internet não perdoa").strip()[:95]
    desc = meta.get("descricao") or "Os comentários mais engraçados da internet, zoados pelos personagens. #shorts #comentarios"
    tags = meta.get("tags") or ["comentários engraçados", "humor", "meme", "chaves", "zueira"]
    return titulo, desc, tags


# ───────── produção ─────────
def ram_livre_gb():
    r = rodar(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"])
    try:
        return int(r.stdout.strip()) / 1024 / 1024
    except ValueError:
        return 99.0


def pendentes():
    return sorted(p for p in SAIDA.glob("*/postar.json")
                  if not json.loads(p.read_text(encoding="utf-8")).get("postado"))


# ───────── nuvem (Kaggle): dona 01/11 "produzir em lotes no Kaggle" pra liberar RAM/CPU do PC1 pro Veo ─────────
MODO = os.environ.get("COMENTARIOS_MODO", "local")  # nuvem | local — 03/11: sem Kaggle pros curtos, volta pro PC


def _kaggle_curto_vivo():
    """07/11 (dona viajando: Comédia Noturna era o canal mais vazio, 3,0 dias): o 'local' segura o estoque em 4
    (ESTOQUE_MAX) e nunca chega aos 7 dias. Com conta de Shorts verificada no pool (a central atende a
    fila_comentarios no loop_curto), vai pra NUVEM, que enche a reserva de 7 dias. Env COMENTARIOS_MODO manda."""
    try:
        p = json.loads(Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json").read_text(encoding="utf-8"))
        return any(c.get("verificada") and not c.get("pausada") and not c.get("banida") and c.get("papel") == "curto"
                   for c in p.get("contas") or [])
    except (OSError, ValueError):
        return False


if "COMENTARIOS_MODO" not in os.environ and _kaggle_curto_vivo():
    MODO = "nuvem"
COLAB = "manhwa-drive:colab_recap"
FILA_COM = f"{COLAB}/fila_comentarios"
RAIZ_DRIVE = f"{COLAB}/raiz"
# 02/11 dona: "sempre reservas no Drive, em lotes, deixando vídeos pra uma semana guardados caso paremos de gerar por
# uma semana" -> estoque = 7 dias x 3/dia (+ folga). Os que não postam hoje ficam no Drive (arquivar) e voltam na hora.
RESERVA_DIAS = 7
POR_DIA = 3
LOTE = 6                 # pedidos preparados por ciclo (2 em 2 h) até encher a reserva
ESTOQUE_NUVEM = RESERVA_DIAS * POR_DIA + 3  # prontos não postados + pedidos na nuvem
_CODIGO_SUBIDO = False


def rcl(*args, timeout=1800):
    """02/11: o Drive (cota compartilhada) deixava um lsf 5 min parado e o TimeoutExpired derrubava o pedido inteiro.
    3 tentativas com espera crescente; não deu = returncode 124 (quem chama decide: pular a rodada)."""
    for tentativa in range(3):
        try:
            r = rodar([RCLONE, *args, "--retries", "2", "--low-level-retries", "5"], timeout=timeout)
            if r.returncode == 0 or args[0] in ("cat",):
                return r
        except subprocess.TimeoutExpired:
            r = subprocess.CompletedProcess(args, 124, "", "timeout")
        time.sleep(20 * (tentativa + 1))
    log(f"drive: rclone {args[0]} falhou 3x ({(r.stderr or '')[-150:]})")
    return r


def subir_codigo():
    """Código e o que o render usa e o pacote do recap não leva (cortados, montagem_ms, fonte do coração)."""
    global _CODIGO_SUBIDO
    if _CODIGO_SUBIDO:
        return
    rcl("sync", str(PROJETO / "bin"), f"{RAIZ_DRIVE}/D/videos-comentarios/bin", "--exclude", "__pycache__/**")
    rcl("copyto", r"D:\ms-energy\bin\montagem_ms.py", f"{RAIZ_DRIVE}/D/ms-energy/bin/montagem_ms.py")
    rcl("sync", str(cv.SFX_TRANSICAO), f"{RAIZ_DRIVE}/D/tmp_logs/sons_novos/cortados")
    rcl("copyto", r"C:\Windows\Fonts\seguisym.ttf", f"{RAIZ_DRIVE}/C/Windows/Fonts/seguisym.ttf")
    _CODIGO_SUBIDO = True


def garantir_voz(voz):
    """A voz no cache único do Drive (colab_recap/vozes/<voz>) que o trabalhador do Kaggle baixa."""
    r = rcl("lsf", f"{COLAB}/vozes/{voz}", timeout=300)
    if r.returncode == 0 and f"{voz}.pth" in r.stdout.split():
        return
    # lsf falhou ou falta a voz: copy só manda o que não está lá
    r = rcl("copy", str(cv.VOZES / voz), f"{COLAB}/vozes/{voz}", "--max-depth", "1",
            "--include", "*.pth", "--include", "*.index", "--include", "*.txt", "--include", "*.json")
    if r.returncode != 0:
        raise RuntimeError(f"voz {voz} não subiu pro Drive (Drive lento) — tenta na próxima rodada")
    log(f"nuvem: voz {voz} subiu pro cache do Drive")


def enviar_nuvem(vid, mp4, cfg, meta, tmp):
    subir_codigo()
    for voz in {f["voz"] for f in cfg["falas"]}:
        garantir_voz(voz)
    ped = tmp / "pedido"
    shutil.rmtree(ped, ignore_errors=True)
    ped.mkdir(parents=True)
    shutil.copy(mp4, ped / "source.mp4")
    for nome in ("roteiro.json", "efeitos.json"):
        shutil.copy(tmp / nome, ped / nome)
    (ped / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    r = rcl("copy", str(ped), f"{FILA_COM}/{vid}")
    if r.returncode != 0:
        raise RuntimeError(f"envio pro Drive falhou: {r.stderr[-200:]}")
    (ped / "pedido.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    rcl("copyto", str(ped / "pedido.json"), f"{FILA_COM}/{vid}/pedido.json")  # por último: só aí o Kaggle pega


def recolher(est):
    """Pedidos prontos no Kaggle -> pasta de postagem (video.mp4 + postar.json); erro -> volta pra fila da fonte."""
    r = rcl("lsf", FILA_COM, "--dirs-only", timeout=300)
    if r.returncode != 0:
        log("recolher: Drive sem resposta — fica pra próxima rodada")
        return
    for vid in (p.rstrip("/") for p in r.stdout.split()):
        nomes = set(rcl("lsf", f"{FILA_COM}/{vid}", timeout=300).stdout.split())
        f = est["fontes"].setdefault(vid, {})
        ja = [p for p in SAIDA.glob(f"*_{vid}/postar.json")]
        if "pronto.json" in nomes and ja:  # já tem versão na fila de postagem: não duplica no canal (fica de teste)
            teste = PROJETO / "tmp" / f"kaggle_teste_{vid}"
            rcl("copy", f"{FILA_COM}/{vid}", str(teste), "--include", "video.mp4", "--include", "falas_final.json")
            rcl("purge", f"{FILA_COM}/{vid}")
            f.update(estado="feito", pasta=str(ja[0].parent))
            log(f"recolher: {vid} saiu do Kaggle mas já existe {ja[0].parent.name} — guardado só como teste em {teste}")
            continue
        if "pronto.json" in nomes:
            pasta = SAIDA / f"{datetime.now():%Y-%m-%d}_{vid}"
            pasta.mkdir(parents=True, exist_ok=True)
            rcl("copy", f"{FILA_COM}/{vid}", str(pasta), "--include", "video.mp4", "--include", "meta.json",
                "--include", "falas_final.json")
            if not (pasta / "video.mp4").exists():
                log(f"recolher: {vid} pronto mas o vídeo não baixou — tento na próxima")
                continue
            d = json.loads((pasta / "meta.json").read_text(encoding="utf-8"))
            if (pasta / "falas_final.json").exists():
                fl = json.loads((pasta / "falas_final.json").read_text(encoding="utf-8"))
                d["falas"] = [{k: x.get(k) for k in ("nome", "comentario", "texto", "desc")} for x in fl]
            d.update(duracao=round(cv.duracao(pasta / "video.mp4"), 1), feito_na="kaggle")
            (pasta / "postar.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            for x in ("meta.json", "falas_final.json"):
                (pasta / x).unlink(missing_ok=True)
            rcl("purge", f"{FILA_COM}/{vid}")
            f.update(estado="feito", pasta=str(pasta))
            log(f"recolher: {vid} pronto no Kaggle -> {pasta.name} ({d['duracao']:.0f}s) {d['titulo']!r}")
        elif "erro.json" in nomes:
            try:
                err = json.loads(rcl("cat", f"{FILA_COM}/{vid}/erro.json").stdout)
            except ValueError:
                err = {}
            rcl("purge", f"{FILA_COM}/{vid}")
            f.update(estado="falhou", erro=f"kaggle: {str(err.get('error'))} {str(err.get('log', ''))[-300:]}")
            log(f"recolher: {vid} ERRO no Kaggle: {f['erro'][:300]}")
    gravar(est)


def na_nuvem(est):
    return sum(1 for f in est["fontes"].values() if f.get("estado") == "na_nuvem")


def produzir(est, vid=None, nuvem=False):
    if vid is None:
        cand = [(f.get("views", 0), k) for k, f in est["fontes"].items()
                if f.get("estado") == "novo" or (f.get("estado") == "falhou" and f.get("tentativas", 0) < 2)]
        if not cand:
            log("produzir: nenhum Short novo na fonte")
            return None
        vid = max(cand)[1]
    f = est["fontes"].setdefault(vid, {"estado": "novo"})
    f["tentativas"] = f.get("tentativas", 0) + 1
    gravar(est)
    log(f"produzir: {vid} ({f.get('views', 0)} views) {f.get('titulo')!r}")
    try:
        mp4 = baixar(vid)
        dados = ler_quadros(mp4, PROJETO / "tmp" / vid / "quadros")
        coms = dados["comentarios"][:6]
        if len(coms) < 3:
            raise RuntimeError(f"só {len(coms)} comentário(s) legível(is) nos prints")
        vozes = montar_elenco(est, len(coms))
        falas = [{"voz": v, "nome": nome_personagem(v), "comentario": c["texto"], "t_src": c["t_src"],
                  "cena": dados.get("cena", "")}
                 for v, c in zip(vozes, coms)]
        titulo, desc, tags = metadados(dados, falas)
        trilhas = [DIR_TRILHAS / t for t in TRILHAS if (DIR_TRILHAS / t).exists()]
        pasta = SAIDA / f"{datetime.now():%Y-%m-%d}_{vid}"
        cfg = {"video_base": str(mp4), "titulo": dados.get("titulo_tela") or titulo, "falas": falas,
               "trilha": str(random.choice(trilhas)) if trilhas else "", "trilha_volume": 0.25,
               "cache": vid, "output": str(pasta / "video.mp4"),
               "prints_regiao": str(dados.get("prints_regiao") or "").strip().lower()}
        if nuvem:  # tudo que é IA aqui; voz clonada + render no Kaggle
            tmp = PROJETO / "tmp" / vid
            cv.roteirizar(falas, tmp / "roteiro.json")
            cv.escolher_efeitos_ia(falas, tmp / "efeitos.json")
            cfg["legenda_mix"] = cv.ms.escolher_mix()
            meta = {"titulo": titulo, "descricao": desc, "tags": tags, "tipo": "short", "sintetico": True,
                    "fonte": f"https://www.youtube.com/shorts/{vid}", "elenco": [x["nome"] for x in falas],
                    "criado": datetime.now().isoformat(timespec="seconds")}
            enviar_nuvem(vid, mp4, cfg, meta, tmp)
            f.update(estado="na_nuvem", enviado=datetime.now().isoformat(timespec="seconds"))
            log(f"produzir: {vid} enviado pro Kaggle (lote) {titulo!r}")
            mp4.unlink(missing_ok=True)
            shutil.rmtree(tmp, ignore_errors=True)
            return "nuvem"
        import fila_render
        with fila_render.vez(NOME_PROJETO, f"Short de comentários {vid}"):
            # 01/11: a voz clonada (RVC) estourou o arquivo de paginação com o render do parceiro rodando junto
            for _ in range(40):
                if ram_livre_gb() >= RAM_MIN_GB:
                    break
                time.sleep(30)
            cv.montar(cfg)
        dur = cv.duracao(pasta / "video.mp4")
        postar = {"titulo": titulo, "descricao": desc, "tags": tags, "tipo": "short", "sintetico": True,
                  "fonte": f"https://www.youtube.com/shorts/{vid}", "elenco": [x["nome"] for x in falas],
                  "falas": [{k: x.get(k) for k in ("nome", "comentario", "texto", "desc")} for x in falas],
                  "duracao": round(dur, 1), "criado": datetime.now().isoformat(timespec="seconds")}
        (pasta / "postar.json").write_text(json.dumps(postar, ensure_ascii=False, indent=1), encoding="utf-8")
        f.update(estado="feito", pasta=str(pasta))
        log(f"produzir: OK {pasta} ({dur:.0f}s) {titulo!r}")
        mp4.unlink(missing_ok=True)  # a fonte baixa de novo se precisar; o cache das vozes/quadros não serve mais
        shutil.rmtree(PROJETO / "tmp" / vid, ignore_errors=True)
        return pasta
    except BaseException as e:  # noqa: BLE001
        f.update(estado="falhou", erro=str(e)[:300])
        if re.search(r"pagina[çc][ãa]o|memory|MemoryError|not enough|Drive lento|timed out|envio pro Drive", str(e), re.I):
            f["tentativas"] = max(0, f["tentativas"] - 1)  # falta de RAM é passageira: não gasta tentativa
        log(f"produzir: FALHOU {vid}: {str(e)[:300]}")
        if isinstance(e, KeyboardInterrupt):
            raise
        return None
    finally:
        gravar(est)


# ───────── postagem ─────────
NOTA_APROVACAO = "comentarios: conferência automática ok (1080p, volume, áudio ouvido); dona liberou a produção em 01/11"
CONFERIR_AUDIO = r"D:\recapd-ambientes\producao\bin\conferir_audio.py"


def conferir(pasta):
    """'' = pode subir; senão o motivo. 1080x1920, volume audível e o áudio ouvido pelo conferir_audio do recapd
    (fala vazia/erro da IA/inglês segura; sem como ouvir = não segura)."""
    mp4 = pasta / "video.mp4"
    r = rodar([cv.FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of",
               "csv=p=0", mp4])
    try:
        w, h = (int(x) for x in r.stdout.strip().split(",")[:2])
    except ValueError:
        return "não consegui ler o vídeo"
    if w < 1080 or h < 1920:
        return f"resolução {w}x{h} abaixo de 1080x1920"
    r = rodar([cv.FFMPEG, "-hide_banner", "-i", mp4, "-af", "ebur128=framelog=quiet", "-f", "null", "-"], timeout=300)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    if m and float(m[-1]) < -20:
        return f"volume baixo ({m[-1]} LUFS)"
    r = rodar([sys.executable.replace("pythonw.exe", "python.exe"), CONFERIR_AUDIO, pasta], timeout=600)
    try:
        v = json.loads(r.stdout[r.stdout.index("{"):])
    except ValueError:
        log(f"conferir: conferir_audio não respondeu ({r.stderr[-200:]}) — segue")
        return ""
    if v.get("ok") is False:
        return f"áudio: {v.get('motivo')}"
    log(f"conferir: áudio ok ({v.get('motivo') or 'ouvido'})")
    return ""


RCLONE = r"D:\tools\rclone.exe"
DRIVE = "manhwa-drive:videos-backup/comentarios"
NO_PC_HOJE = 3  # teto do canal: só os da vez de hoje ficam no PC


def _para_drive(pj, d, motivo):
    """Sobe video.mp4 pro Drive, confere (rclone check) e só então apaga do PC. postar.json fica com 'drive'."""
    mp4 = pj.parent / "video.mp4"
    destino = f"{DRIVE}/{pj.parent.name}"
    r = rodar([RCLONE, "copy", mp4, destino], timeout=1800)
    if r.returncode != 0:
        log(f"drive: falhou subir {pj.parent.name}: {r.stderr[-200:]}")
        return
    r = rodar([RCLONE, "check", pj.parent, destino, "--one-way", "--include", "video.mp4"], timeout=900)
    if r.returncode != 0:
        log(f"drive: rclone check NÃO bateu em {pj.parent.name} — fica no PC")
        return
    d["drive"] = f"{destino}/video.mp4"
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    mp4.unlink()
    log(f"drive: {pj.parent.name} -> Drive ({motivo}); saiu do PC")


def do_drive(pasta):
    """Traz o video.mp4 de volta do Drive na hora de postar. True = está no PC."""
    mp4 = pasta / "video.mp4"
    if mp4.exists():
        return True
    d = json.loads((pasta / "postar.json").read_text(encoding="utf-8"))
    if not d.get("drive"):
        return False
    r = rodar([RCLONE, "copy", d["drive"].rsplit("/", 1)[0], pasta, "--include", "video.mp4"], timeout=1800)
    ok = r.returncode == 0 and mp4.exists()
    log(f"drive: {pasta.name} baixado do Drive pra postar" if ok else f"drive: falhou baixar {pasta.name}: {r.stderr[-200:]}")
    return ok


def arquivar():
    """Postado há 2 h+ (já foi ao ar ou está agendado no YouTube) e pendente que não é da vez de hoje -> Drive."""
    hoje = datetime.now().date()
    postados_hoje = 0
    fichas = []
    for pj in sorted(SAIDA.glob("*/postar.json")):
        d = json.loads(pj.read_text(encoding="utf-8"))
        fichas.append((pj, d))
        p = d.get("postado")
        if p and p != "segurado" and datetime.fromisoformat(p).date() == hoje:
            postados_hoje += 1
    vagas_hoje = max(0, NO_PC_HOJE - postados_hoje)
    pend = 0
    for pj, d in fichas:
        if not (pj.parent / "video.mp4").exists():
            continue
        p = d.get("postado")
        if p and p != "segurado":
            # 48 h no PC: o reuso do TikTok/Insta (catalogo, ficha) pega o vídeo daqui antes de ir pro Drive
            if datetime.now() - datetime.fromisoformat(p) > timedelta(hours=48):
                _para_drive(pj, d, "já postado")
        elif not p:
            pend += 1
            if pend > vagas_hoje:
                _para_drive(pj, d, "não posta hoje")


TRAVA_POSTAR = PROJETO / "estado" / "postar.lock"


def postar():
    """Uma postagem por vez (a tarefa de postagem de 30 em 30 min e o ciclo de 2 em 2 h nunca sobem o mesmo vídeo)."""
    try:
        fd = os.open(TRAVA_POSTAR, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        if time.time() - TRAVA_POSTAR.stat().st_mtime < 3 * 3600:
            log("postar: outra postagem nossa em andamento")
            return
        TRAVA_POSTAR.unlink(missing_ok=True)
        fd = os.open(TRAVA_POSTAR, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    try:
        _postar()
    finally:
        TRAVA_POSTAR.unlink(missing_ok=True)


def _postar():
    import politica as pol
    fila = pendentes()
    if not fila:
        log("postar: nada pendente")
        return
    canal, err = pol.achar_canal(CANAL)
    if not canal:
        log(f"postar: canal {CANAL} não achado: {err}")
        return
    pj = fila[0]
    d = json.loads(pj.read_text(encoding="utf-8"))
    quando = pol.horario_obrigatorio(canal, None, NOME_PROJETO)
    if quando - pol.agora() > timedelta(hours=POSTAR_ATE_H):
        log(f"postar: próxima vaga só em {quando:%d/%m %H:%M} — estoque fica guardado")
        return
    mp4 = pj.parent / "video.mp4"
    if not do_drive(pj.parent):
        log(f"postar: {pj.parent.name} sem vídeo no PC nem no Drive — pulado")
        return
    problema = conferir(pj.parent)
    if problema:
        d.update(postado="segurado", revisao=problema)
        pj.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"postar: SEGURADO {pj.parent.name}: {problema}")
        try:
            import avisos
            avisos.enviar(f"Comédia Noturna: Short segurado antes de subir ({pj.parent.name}): {problema}",
                          "comentarios", importante=True)
        except Exception:  # noqa: BLE001
            pass
        return
    pol.marcar_aprovacao(str(mp4), "aprovado", NOTA_APROVACAO)
    status, info = pol.postar_youtube(CANAL, str(pj.parent / "video.mp4"), d["titulo"], d["descricao"], d["tags"],
                                      privacy="public", publish_at=pol.rfc3339(quando), projeto=NOME_PROJETO,
                                      tipo="short", sintetico=bool(d.get("sintetico")))
    log(f"postar: {pj.parent.name} -> {status} {info} (publica {quando:%d/%m %H:%M})")
    if status == "ok":
        # posted_url/canal_postado/agendado_para = o que o catalogo.py lê da ficha (reuso TikTok/Insta, 02/11)
        d.update(postado=datetime.now().isoformat(timespec="seconds"), url=info, publish_at=quando.isoformat(),
                 posted_url=info, canal_postado="Comédia Noturna", agendado_para=quando.isoformat())
        pj.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def ciclo():
    est = ler()
    listar(est)
    if MODO == "nuvem":
        recolher(est)
        for _ in range(LOTE):
            n = len(pendentes()) + na_nuvem(est)
            if n >= ESTOQUE_NUVEM:
                log(f"ciclo: estoque cheio ({n} prontos/na nuvem) — não prepara")
                break
            if produzir(est, nuvem=True) is None and not any(
                    f.get("estado") == "novo" for f in est["fontes"].values()):
                break
        postar()
        arquivar()
        dias = len(pendentes()) / POR_DIA
        log(f"ciclo: reserva {len(pendentes())} prontos = {dias:.1f} dias (meta {RESERVA_DIAS}), {na_nuvem(est)} na nuvem")
        if dias < 1 and na_nuvem(est) == 0:
            try:
                import avisos
                avisos.enviar(f"Comédia Noturna: reserva com {dias:.1f} dia(s) de vídeo e nada no Kaggle — produção "
                              "parada? (log D:\\videos-comentarios\\logs\\producao.log)", "comentarios", importante=True)
            except Exception:  # noqa: BLE001
                pass
        return
    n = len(pendentes())
    if n >= ESTOQUE_MAX:
        log(f"ciclo: estoque cheio ({n} prontos) — não produz")
    elif ram_livre_gb() < RAM_MIN_GB:
        log(f"ciclo: RAM livre {ram_livre_gb():.1f} GB < {RAM_MIN_GB} — não produz agora")
    else:
        produzir(est)
    postar()
    arquivar()


def status():
    est = ler()
    cont = {}
    for f in est["fontes"].values():
        cont[f.get("estado")] = cont.get(f.get("estado"), 0) + 1
    print("fonte:", cont, f"| reserva: {len(pendentes())} prontos = {len(pendentes()) / POR_DIA:.1f} dias "
          f"(meta {RESERVA_DIAS}) | na nuvem: {na_nuvem(est)}")
    for p in sorted(SAIDA.glob("*/postar.json"))[-8:]:
        d = json.loads(p.read_text(encoding="utf-8"))
        print(f"  {p.parent.name}: {d['titulo'][:50]!r} postado={d.get('postado', '-')} publica={d.get('publish_at', '-')}")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ciclo"
    if cmd in ("ciclo", "produzir"):
        # 02/11: o ciclo da tarefa e uma produção manual ao mesmo tempo gravaram o estado por cima um do outro
        # (oyIlXAs1REE perdeu o "feito" e foi produzido 2x). Um processo de produção por vez.
        import msvcrt
        _trava = open(PROJETO / "estado" / "producao.lock", "w")
        try:
            msvcrt.locking(_trava.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            log(f"{cmd}: outra produção em andamento — saio")
            raise SystemExit(0)
    if cmd == "ciclo":
        try:
            ciclo()
        except Exception:  # noqa: BLE001
            import traceback
            log("ciclo: ERRO\n" + traceback.format_exc())
            raise
    elif cmd == "listar":
        listar(ler(), forcar=True)
    elif cmd == "produzir":
        produzir(ler(), sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "postar":
        postar()
    elif cmd == "status":
        status()
    else:
        raise SystemExit(__doc__)
