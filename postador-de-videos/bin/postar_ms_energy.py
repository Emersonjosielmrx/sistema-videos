#!/usr/bin/env python3
"""Postagem automática MS Energy — Instagram Feed (Reel) + Stories + TikTok (cofre) + Facebook (Reels via CDP).

Reusa instagram_poster.py (Graph API), postar_tiktok_auto.py e facebook_cdp_poster.py (Playwright CDP).
Coleta videos de shorts_veo, usa a legenda pronta do roteiro (pipeline ms_v2) ou uma legenda honesta,
posta em cada plataforma, e move pra _postados/.

Uso:
  python postar_ms_energy.py              # posta tudo que falta
  python postar_ms_energy.py --um         # posta 1 e sai (pra cron horário)
  python postar_ms_energy.py --preview    # só mostra o que seria postado
  python postar_ms_energy.py --so insta   # só Instagram (Feed+Stories)
  python postar_ms_energy.py --so fb      # só Facebook
"""
import json
import os
import sys
import shutil
import time
import random
import argparse
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from datetime import datetime

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
VIDEOS_DIR = Path(r"D:\ms-energy\videos\shorts_veo")
POSTADOS_DIR = Path(r"D:\ms-energy\videos\_postados")
LOG_FILE = Path(r"D:\ms-energy\videos\postagem_log.json")

# Instagram
INSTA_CONTA = "msenergycap"
INSTA_POSTER = Path(r"D:\postador-de-videos\bin\instagram_poster.py")
CREDS_FILE = Path(r"D:\credenciais-canais\instagram_contas.json")

# Facebook CDP
FB_POSTER = Path(r"D:\postador-de-videos\bin\facebook_cdp_poster.py")
FB_PAGE = "https://www.facebook.com/mundosolarenergia/"
FB_PORT = 9401

PY_EXE = Path(r"D:\hipercool-videos\venv\Scripts\python.exe")

# TikTok @energia.solar.da (dono 19/10: o MS Energy posta todo dia, com o conteudo dele). Internet de casa, sem o proxy
# da Webshare: empresa local, o publico tem que ser do Brasil.
TIKTOK_COFRE = "msenergypara"

GRAPH_FB_URL = "https://graph.facebook.com/v21.0"
GRAPH_IG_URL = "https://graph.instagram.com/v21.0"

# ── Legendas ─────────────────────────────────────────────────────────────────
# 22/10 (analise D:\ms-energy\docs\ANALISE_CAMPANHA.md): os 15 ganchos fixos repetiam (8x o mesmo), citavam a CEMIG
# (a empresa e do Para), prometiam "R$0"/"zerar" e mandavam seguir @MSEnergySolar (a conta e @msenergycap). Video
# novo (pipeline ms_v2) traz a legenda pronta do roteiro; video antigo recebe uma legenda honesta sem a fala dele.

GANCHOS_SEGUROS = [
    "☀️ Energia solar para casa, comércio e campo no Pará.",
    "☀️ Gere a sua própria energia com a luz do sol.",
    "☀️ Conta de luz pesando no orçamento? Fale com quem entende de energia solar.",
    "☀️ Projeto, instalação e manutenção de energia solar no Pará.",
    "☀️ Quase 10 anos instalando energia solar no Pará.",
]
CTA_INSTA = "📲 Orçamento grátis pelo WhatsApp: link no perfil @msenergycap"
CTA_TIKTOK = "📲 Orçamento grátis: chame a MS Energy no WhatsApp (perfil do Instagram @msenergycap)"
HASHTAGS = ["#energiasolar", "#energiasolarpara", "#para", "#paragominas", "#painelsolar", "#contadeluz",
            "#energiafotovoltaica", "#msenergy"]


def _legenda_nova(meta):
    """25/10 (bin\\legenda_empresa.py): video gerado antes da legenda nova (frase morna + rodape fixo; 0 comentario em
    10 posts) e refeito na hora de postar: 1a linha com "energia solar" + Pará, pergunta, "Comente SOL", 5 hashtags."""
    try:
        import legenda_empresa
        if legenda_empresa.relegendar(meta, INSTA_CONTA):
            print("  legenda refeita no formato novo (pergunta + Comente SOL)")
    except Exception as e:  # noqa: BLE001  (legenda nunca impede o post)
        print(f"  legenda nova falhou ({type(e).__name__}: {e}) - fica a antiga")


def _legenda_reserva(meta, plataforma):
    """Video antigo sem legenda pronta: gancho honesto no formato novo (ou o antigo, se o modulo falhar)."""
    try:
        import legenda_empresa
        ins, tk, _tags = legenda_empresa.montar(INSTA_CONTA, random.choice(GANCHOS_SEGUROS), meta.get("pauta"))
        if ins:
            return ins if plataforma == "insta" else tk
    except Exception:  # noqa: BLE001
        pass
    if plataforma == "insta":
        return f"{random.choice(GANCHOS_SEGUROS)}\n\n{CTA_INSTA}\n🏠 Casas • 🏪 Comércios • 🌾 Propriedades rurais — " \
               "Pará\n\n" + " ".join(HASHTAGS)
    return f"{random.choice(GANCHOS_SEGUROS)} {CTA_TIKTOK} " + " ".join(HASHTAGS[:5])


def montar_caption_viral(meta):
    """Legenda do Instagram: a do roteiro (ms_v2, refeita no formato novo se for antiga) ou uma honesta."""
    _legenda_nova(meta)
    if meta.get("legenda_insta"):
        return meta["legenda_insta"]
    return _legenda_reserva(meta, "insta")


def montar_caption_tiktok(meta):
    _legenda_nova(meta)
    if meta.get("legenda_tiktok"):
        return meta["legenda_tiktok"]
    return _legenda_reserva(meta, "tiktok")


def _video_antigo_postavel(meta):
    """Video antigo so entra como reserva se a fala dele passar nas regras de propaganda do roteiro_ms
    (sem 'zerar', sem numero, sem concessionaria...)."""
    sys.path.insert(0, r"D:\ms-energy\bin")
    import roteiro_ms
    fala = (meta.get("prompt_agents") or {}).get("fala") or ""
    return bool(fala) and not roteiro_ms.problemas_texto(fala)


# ── Coleta de vídeos ─────────────────────────────────────────────────────────

def carregar_log():
    if LOG_FILE.exists():
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_log(log):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def coletar_videos():
    """Retorna lista de dicts {mp4, json_path, meta, nome} dos vídeos disponíveis."""
    seen = set()
    items = []
    for pasta in (VIDEOS_DIR, POSTADOS_DIR):
        if not pasta.exists():
            continue
        for mp4 in sorted(pasta.glob("*.mp4")):
            if mp4.stem in seen:
                continue
            seen.add(mp4.stem)
            json_path = mp4.with_suffix(".json")
            meta = {}
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            items.append({
                "mp4": mp4,
                "json_path": json_path,
                "meta": meta,
                "nome": mp4.stem,
            })
    return items


# ── Upload público ────────────────────────────────────────────────────────────

def _upload_litterbox(video_path):
    import subprocess
    r = subprocess.run([
        "curl.exe", "-s",
        "-F", "reqtype=fileupload",
        "-F", "time=24h",
        "-F", f"fileToUpload=@{video_path}",
        "https://litterbox.catbox.moe/resources/internals/api.php"
    ], capture_output=True, text=True, timeout=180)
    if r.returncode == 0:
        url = r.stdout.strip()
        if url.startswith("https://"):
            return url
    return None


def _upload_uguu(video_path):
    import subprocess
    r = subprocess.run([
        "curl.exe", "-s",
        "-F", f"files[]=@{video_path}",
        "https://uguu.se/upload"
    ], capture_output=True, text=True, timeout=180)
    if r.returncode == 0:
        try:
            data = json.loads(r.stdout)
            if data.get("success") and data.get("files"):
                return data["files"][0]["url"]
        except Exception:
            pass
    return None


def _upload_tmpfiles(video_path):
    import subprocess
    r = subprocess.run([
        "curl.exe", "-s",
        "-F", f"file=@{video_path}",
        "https://tmpfiles.org/api/v1/upload"
    ], capture_output=True, text=True, timeout=180)
    if r.returncode == 0:
        try:
            data = json.loads(r.stdout)
            url = data.get("data", {}).get("url", "")
            if url:
                return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        except Exception:
            pass
    return None


def _e_video(url):
    """02/11 (reel MS 20:40 saiu só no story): o link do tmpfiles redireciona pra uma PÁGINA HTML e o Instagram recusa o
    reel. Só serve link que entrega o mp4 de verdade (Content-Type video/*, sem página no meio)."""
    import subprocess
    try:
        r = subprocess.run(["curl.exe", "-s", "-I", "-L", "--max-time", "30", url], capture_output=True, text=True,
                           timeout=45)
        tipos = [l.split(":", 1)[1].strip().lower() for l in r.stdout.splitlines() if l.lower().startswith("content-type")]
        # imagem também vale: o carrossel_marca usa esta mesma função pras fotos
        return bool(tipos) and tipos[-1].startswith(("video/", "image/"))
    except Exception:  # noqa: BLE001 — não deu pra conferir: usa (é como era antes)
        return True


def upload_video_publico(video_path):
    """Sobe o vídeo pra URL pública direta. Tenta litterbox → uguu.se (2 voltas). O tmpfiles saiu da lista em 02/11: o
    link dele é página HTML, o Instagram recusa."""
    for volta in (1, 2):
        for name, fn in [("litterbox", _upload_litterbox), ("uguu.se", _upload_uguu)]:
            try:
                url = fn(video_path)
                if url and _e_video(url):
                    print(f"  Upload via {name}: {url}")
                    return url
                print(f"  {name} falhou{' (link não é vídeo)' if url else ''}, tentando proximo...")
            except Exception as e:
                print(f"  {name} erro: {e}, tentando proximo...")
        if volta == 1:
            time.sleep(20)
    return None


# ── Graph API helpers ─────────────────────────────────────────────────────────

def _base_url(token):
    if token.startswith("IGAA"):
        return GRAPH_IG_URL
    return GRAPH_FB_URL


def graph_post(path, params):
    base = _base_url(params.get("access_token", ""))
    url = f"{base}/{path}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": json.loads(body) if body.startswith("{") else body, "status": e.code}


def graph_get(path, params):
    base = _base_url(params.get("access_token", ""))
    qs = urllib.parse.urlencode(params)
    url = f"{base}/{path}?{qs}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": json.loads(body) if body.startswith("{") else body, "status": e.code}


def _get_ig_account():
    """Carrega credenciais da conta msenergycap."""
    with open(CREDS_FILE, "r", encoding="utf-8") as f:
        contas = json.load(f)
    for c in contas:
        if INSTA_CONTA.lower() in c["name"].lower():
            return c
    return None


def _get_ig_user_id(conta):
    """Retorna o IG user ID da conta."""
    token = conta["data"]["accessToken"]
    if token.startswith("IGAA"):
        me = graph_get("me", {"fields": "user_id", "access_token": token})
        return me.get("user_id") or me.get("id")
    return conta["data"]["instagramBusinessAccountId"]


# ── Postagem Instagram Feed (Reel) ───────────────────────────────────────────

def postar_instagram(video_path, caption):
    """Posta Reel no Instagram via Graph API. Retorna (ok, msg)."""
    import subprocess
    cmd = [
        str(PY_EXE), str(INSTA_POSTER),
        "--video", str(video_path),
        "--caption", caption,
        "--conta", INSTA_CONTA,
        "--capa-ms", "1000",  # 25/10: capa no 1 s = foto + frase do topo (a frase fica de 0 a 2,6 s)
    ]
    # 01/11 20:40: o envio (servidor de arquivo temporário + Graph API) passou de 300 s e o TimeoutExpired derrubou a
    # rodada inteira sem post — agora 15 min e, estourando, é falha comum (o vídeo fica para a próxima tentativa)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900,
                           env={**os.environ, "PYTHONUTF8": "1"})
    except subprocess.TimeoutExpired:
        return False, "timeout de 15 min no envio ao Instagram"
    output = r.stdout + r.stderr
    if r.returncode == 0 and "publicado" in output.lower():
        return True, output.strip().split("\n")[-1]
    return False, output.strip()[-200:] if output else f"exit={r.returncode}"


# ── Postagem Instagram Stories ────────────────────────────────────────────────

def postar_instagram_stories(video_path, video_url=None):
    """Posta Stories no Instagram via Graph API. Retorna (ok, msg).
    Stories usam media_type=STORIES e não suportam caption longo,
    mas aceitam caption curto."""
    conta = _get_ig_account()
    if not conta:
        return False, f"conta {INSTA_CONTA} não encontrada"

    token = conta["data"]["accessToken"]
    ig_id = _get_ig_user_id(conta)
    if not ig_id:
        return False, "não consegui pegar ig_user_id"

    if not video_url:
        video_url = upload_video_publico(str(video_path))
        if not video_url:
            return False, "falha upload litterbox pra stories"

    params = {
        "media_type": "STORIES",
        "video_url": video_url,
        "access_token": token,
    }
    resp = graph_post(f"{ig_id}/media", params)
    if "error" in resp:
        err = resp["error"]
        if isinstance(err, dict):
            msg = err.get("error", {}).get("message", str(err))
            code = err.get("error", {}).get("code", 0)
        else:
            msg = str(err)
            code = resp.get("status", 0)
        return False, f"stories container falhou: [{code}] {msg}"

    container_id = resp.get("id")
    if not container_id:
        return False, f"sem container_id stories: {resp}"

    # 11/11: 60 s (12x5) era pouco — 9 stories da MS morreram em "timeout (status=IN_PROGRESS)" com o Instagram ainda
    # processando o vídeo (o feed do MESMO arquivo saiu). Até 4 min; MS_STORIES_ESPERA_S muda.
    for _ in range(max(1, int(os.environ.get("MS_STORIES_ESPERA_S", "240")) // 5)):
        time.sleep(5)
        status_resp = graph_get(container_id, {
            "fields": "status_code",
            "access_token": token
        })
        status = status_resp.get("status_code", "")
        if status == "FINISHED":
            break
        if status == "ERROR":
            return False, f"stories processamento erro: {status_resp}"
    else:
        return False, f"stories timeout (status={status})"

    pub_resp = graph_post(f"{ig_id}/media_publish", {
        "creation_id": container_id,
        "access_token": token,
    })
    if "error" in pub_resp:
        err = pub_resp["error"]
        if isinstance(err, dict):
            msg = err.get("error", {}).get("message", str(err))
        else:
            msg = str(err)
        return False, f"stories publish falhou: {msg}"

    media_id = pub_resp.get("id", "?")
    return True, f"stories publicado! media_id={media_id}"


# ── Postagem Facebook ─────────────────────────────────────────────────────────

def postar_facebook(video_path, caption):
    """Posta Reel no Facebook via CDP. Retorna (ok, msg)."""
    import subprocess
    cmd = [
        str(PY_EXE), str(FB_POSTER),
        "--video", str(video_path),
        "--caption", caption,
        "--port", str(FB_PORT),
        "--page", FB_PAGE,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                       env={**os.environ, "PYTHONUTF8": "1"})
    output = r.stdout + r.stderr
    if r.returncode == 0 and "postado" in output.lower():
        return True, "ok"
    return False, output.strip()[-200:] if output else f"exit={r.returncode}"


# ── Mover postado ────────────────────────────────────────────────────────────

def postar_tiktok(video_path, caption):
    sys.path.insert(0, r"D:\logins-google")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import cofre
    import postar_tiktok_auto as tk
    porta, proc = cofre.abrir(TIKTOK_COFRE)
    try:  # numa linha so: o editor do TikTok nao guarda a quebra de linha
        return tk.post_via_cdp(video_path, porta, " ".join(caption.split()))
    finally:
        tk.fechar_conta(porta, proc, {"cofre": TIKTOK_COFRE})


def mover_postado(item, plataformas):
    """Move MP4 + JSON pra _postados/ e grava metadados de postagem."""
    POSTADOS_DIR.mkdir(parents=True, exist_ok=True)
    dest_mp4 = POSTADOS_DIR / item["mp4"].name
    dest_json = POSTADOS_DIR / item["json_path"].name

    meta = item["meta"].copy()
    meta["postado_em"] = datetime.now().isoformat()
    meta["postado_plataformas"] = plataformas

    if item["json_path"].exists():
        with open(item["json_path"], "r", encoding="utf-8") as f:
            original = json.load(f)
        original.update(meta)
        with open(dest_json, "w", encoding="utf-8") as f:
            json.dump(original, f, ensure_ascii=False, indent=2)
        item["json_path"].unlink()
    else:
        with open(dest_json, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    shutil.move(str(item["mp4"]), str(dest_mp4))
    return dest_mp4


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Postagem automática MS Energy")
    parser.add_argument("--preview", action="store_true", help="Só mostra o que seria postado")
    parser.add_argument("--um", action="store_true", help="Posta 1 vídeo e sai (pra cron)")
    parser.add_argument("--so", choices=["insta", "fb", "tiktok", "todos"], default="todos",
                        help="Postar só numa plataforma")
    parser.add_argument("--ate-hora", type=int, default=23,
                        help="Hora limite (default 23 = sem limite prático)")
    parser.add_argument("--intervalo", type=int, default=120,
                        help="Segundos entre posts (default 120)")
    args = parser.parse_args()

    log = carregar_log()
    videos = coletar_videos()

    if not videos:
        print("Nenhum vídeo encontrado em", VIDEOS_DIR)
        return

    fazer_insta = args.so in ("insta", "todos")
    fazer_fb = args.so in ("fb", "todos")
    fazer_tiktok = args.so in ("tiktok", "todos")

    # Filtrar apenas vídeos que ainda precisam de alguma plataforma
    pendentes = []
    for v in videos:
        nome = v["nome"]
        # 04/11 (dona: "nunca mais conteúdo de uma empresa no Insta da outra"): vídeo com dono e que NÃO é da MS não sai
        dono = (v.get("meta") or {}).get("_empresa")
        if dono and not str(dono).startswith("MS Energy"):
            print(f"  [TRAVA EMPRESA] {nome} é de '{dono}' — não posta na MS")
            continue
        entry = log.get(nome, {})
        precisa_insta = fazer_insta and not entry.get("insta")
        precisa_stories = fazer_insta and not entry.get("stories")
        precisa_fb = fazer_fb and not entry.get("fb")
        precisa_tiktok = fazer_tiktok and not entry.get("tiktok")
        if precisa_insta or precisa_stories or precisa_fb or precisa_tiktok:
            pendentes.append(v)
    # 22/10: video novo (ms_v2, mais recente primeiro) na frente; antigo so como reserva e se a fala dele for honesta
    # 04/11 21:35: o Reel das 20:40 saiu VAZIO ("Nenhum vídeo pendente") com 2 Reels Remotion da MS prontos na pasta
    # (ccv_msenergycap_*, pipeline claude_code_video, origem saida\msenergycap): contavam como "antigo" e nunca saíam.
    def _novo(m):
        return m.get("pipeline") == "ms_v2" or (m.get("pipeline") == "claude_code_video"
                                                and "msenergycap" in str(m.get("origem", "")).lower())
    novos = sorted((v for v in pendentes if _novo(v["meta"])), key=lambda v: v["nome"], reverse=True)
    antigos = [v for v in pendentes if not _novo(v["meta"]) and _video_antigo_postavel(v["meta"])]
    barrados = len(pendentes) - len(novos) - len(antigos)
    # 25/10: o antigo (formato meme de antes do ms_v2: abertura com glitch/neon) so cobre o DIA sem post; 24/10 19:41 ele
    # saiu num 3o horario so porque faltou video novo — com post de hoje ja feito, o horario fica vazio
    hoje = datetime.now().strftime("%Y-%m-%d")
    if fazer_insta and antigos and any(str(e.get("insta") or "").startswith(hoje) for e in log.values()):
        print(f"  {len(antigos)} antigo(s) de reserva NAO entram: o Instagram ja teve post hoje")
        antigos = []
    pendentes = novos + antigos
    # 02/11 12:40: o Reel das 08:40 (só faltava o story) ficou 1º e o --um parou depois do story — o horário saiu sem
    # Reel no feed. Quem ainda precisa do FEED vem antes; o story atrasado vai quando não houver feed pendente
    if fazer_insta:
        pendentes.sort(key=lambda v: bool(log.get(v["nome"], {}).get("insta")))

    print(f"\n{'='*60}")
    print(f"MS ENERGY — Postagem Automática VIRAL")
    print(f"{'='*60}")
    print(f"  Vídeos disponíveis: {len(videos)}")
    print(f"  Pendentes:          {len(pendentes)} ({len(novos)} novos ms_v2, {len(antigos)} antigos de reserva)")
    print(f"  Barrados:           {barrados} antigos com promessa proibida na fala (zerar, número...)")
    print(f"  Instagram Feed:     {'SIM' if fazer_insta else 'NÃO'} (conta {INSTA_CONTA})")
    print(f"  Instagram Stories:  {'SIM' if fazer_insta else 'NÃO'}")
    print(f"  Facebook:           {'SIM' if fazer_fb else 'NÃO'} (página mundosolarenergia)")
    print(f"  TikTok:             {'SIM' if fazer_tiktok else 'NÃO'} (cofre {TIKTOK_COFRE})")
    print(f"  Modo:               {'1 VÍDEO' if args.um else 'CONTÍNUO'}")
    print(f"  Intervalo:          {args.intervalo}s entre posts")
    print()

    if not pendentes:
        print("Nenhum vídeo pendente! Todos já foram postados.")
        return

    if args.preview:
        for v in pendentes[:5]:
            nome = v["nome"]
            entry = log.get(nome, {})
            caption = montar_caption_viral(v["meta"])
            print(f"  {nome}")
            print(f"    IG Feed:    {'JÁ' if entry.get('insta') else 'PENDENTE'}")
            print(f"    IG Stories: {'JÁ' if entry.get('stories') else 'PENDENTE'}")
            print(f"    FB:         {'JÁ' if entry.get('fb') else 'PENDENTE'}")
            print(f"    TikTok:     {'JÁ' if entry.get('tiktok') else 'PENDENTE'}")
            print(f"    Caption:    {caption[:100]}...")
            print()
        if len(pendentes) > 5:
            print(f"  ... e mais {len(pendentes)-5} vídeos")
        print("\n>>> PREVIEW — nada postado.")
        return

    # Postar
    total = {"insta": 0, "stories": 0, "fb": 0, "tiktok": 0, "erros": 0}
    postou_algum = False
    fazer_insta_feed_ok = True
    fazer_insta_stories_ok = True
    fazer_tiktok_ok = True

    for v in pendentes:
        hora = datetime.now().hour
        if hora >= args.ate_hora:
            print(f"\n*** Hora limite ({args.ate_hora}:00) atingida. Parando. ***")
            break

        if args.um and postou_algum:
            break

        nome = v["nome"]
        if nome not in log:
            log[nome] = {}

        caption_viral = montar_caption_viral(v["meta"])
        video_url_publica = None

        # Instagram Feed (Reel)
        if fazer_insta and fazer_insta_feed_ok and not log[nome].get("insta"):
            print(f"\n[IG Feed] {nome}...", end=" ", flush=True)
            ok, msg = postar_instagram(v["mp4"], caption_viral)
            if ok:
                print(f"OK — {msg}")
                log[nome]["insta"] = datetime.now().isoformat()
                total["insta"] += 1
                salvar_log(log)
                time.sleep(10)
            else:
                print(f"ERRO — {msg[:120]}")
                total["erros"] += 1
                if "too many actions" in msg.lower():
                    print("  ⚠ Rate limit de feed — pulando feeds restantes nesta rodada")
                    fazer_insta_feed_ok = False

        # Instagram Stories
        if fazer_insta and fazer_insta_stories_ok and not log[nome].get("stories"):
            print(f"[IG Stories] {nome}...", end=" ", flush=True)
            ok, msg = postar_instagram_stories(v["mp4"], video_url=video_url_publica)
            if ok:
                print(f"OK — {msg}")
                log[nome]["stories"] = datetime.now().isoformat()
                total["stories"] += 1
                salvar_log(log)
                time.sleep(10)
            else:
                print(f"ERRO — {msg[:120]}")
                total["erros"] += 1
                if "too many actions" in msg.lower():
                    print("  ⚠ Rate limit de stories — pulando stories restantes nesta rodada")
                    fazer_insta_stories_ok = False

        # Facebook
        if fazer_fb and not log[nome].get("fb"):
            print(f"[FB] {nome}...", end=" ", flush=True)
            ok, msg = postar_facebook(v["mp4"], caption_viral)
            if ok:
                print(f"OK — {msg}")
                log[nome]["fb"] = datetime.now().isoformat()
                total["fb"] += 1
                salvar_log(log)
            else:
                print(f"ERRO — {msg[:120]}")
                total["erros"] += 1

        # TikTok
        if fazer_tiktok and fazer_tiktok_ok and not log[nome].get("tiktok"):
            print(f"[TikTok] {nome}...", end=" ", flush=True)
            try:
                ok, msg = postar_tiktok(v["mp4"], montar_caption_tiktok(v["meta"]))
            except Exception as e:  # noqa: BLE001  (Chrome do cofre nao abriu)
                ok, msg = False, f"abrir Chrome: {e}"
            if ok:
                print("OK")
                log[nome]["tiktok"] = datetime.now().isoformat()
                total["tiktok"] += 1
                salvar_log(log)
            else:
                print(f"ERRO — {str(msg)[-160:]}")
                total["erros"] += 1
                if "not_logged_in" in str(msg):
                    print("  ⚠ TikTok deslogado — logar a conta msenergypara (cofre) no tiktok.com")
                    fazer_tiktok_ok = False

        # Mover só quando TODAS plataformas estiverem postadas
        if log[nome].get("insta") and log[nome].get("stories") and log[nome].get("fb"):
            all_plat = ["instagram_feed", "instagram_stories", "facebook"]
            if v["mp4"].exists():
                dest = mover_postado(v, all_plat)
                print(f"  → Movido pra {dest}")

        postou_algum = postou_algum or total["insta"] > 0 or total["stories"] > 0 or total["fb"] > 0 or total["tiktok"] > 0

        if not args.um:
            print(f"  Aguardando {args.intervalo}s...", flush=True)
            time.sleep(args.intervalo)

    print(f"\n{'='*60}")
    print(f"RESUMO")
    print(f"{'='*60}")
    print(f"  IG Feed:    {total['insta']} postados")
    print(f"  IG Stories: {total['stories']} postados")
    print(f"  Facebook:   {total['fb']} postados")
    print(f"  TikTok:     {total['tiktok']} postados")
    print(f"  Erros:      {total['erros']}")
    restantes = len(list(VIDEOS_DIR.glob("*.mp4")))
    print(f"  Restantes:  {restantes} vídeos em {VIDEOS_DIR}")


if __name__ == "__main__":
    main()
