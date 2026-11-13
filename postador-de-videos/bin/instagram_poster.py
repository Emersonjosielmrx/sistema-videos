#!/usr/bin/env python3
"""
instagram_poster.py — Posta vídeos no Instagram via Graph API (Reels).
Usa as credenciais extraídas do n8n (D:\\credenciais-canais\\instagram_contas.json).

Suporta 2 tipos de token:
  - Token FB (começa com EAA...) → usa graph.facebook.com + instagramBusinessAccountId
  - Token IG (começa com IGAA...) → usa graph.instagram.com + igUserId (campo 'me')

Fluxo da API Graph para Reels:
  1. POST /{ig-user-id}/media (media_type=REELS, video_url=URL_PUBLICA)
  2. Aguarda processamento (GET /{container-id}?fields=status_code)
  3. POST /{ig-user-id}/media_publish (creation_id=container_id)

Upload de vídeo via litterbox.catbox.moe (URL direta, 24h).
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

CREDS_FILE = Path(os.environ.get(
    "INSTA_CREDS_FILE", r"D:\credenciais-canais\instagram_contas.json"))
GRAPH_FB_URL = "https://graph.facebook.com/v21.0"
GRAPH_IG_URL = "https://graph.instagram.com/v21.0"


def carregar_contas():
    with open(CREDS_FILE, "r", encoding="utf-8") as f:
        contas = json.load(f)
    return contas


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


def upload_video_publico(video_path):
    """Sobe o vídeo pra URL pública direta. Tenta litterbox → uguu.se → tmpfiles."""
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    video_path = type(video_path)(_g1080(video_path)) if not isinstance(video_path, str) else str(_g1080(video_path))
    # 02/11: tmpfiles fora (o link dele é página HTML, o Instagram recusava o reel); 2 voltas nos que servem o mp4
    from postar_ms_energy import _e_video
    for volta in (1, 2):
        for name, fn in [("litterbox", _upload_litterbox), ("uguu.se", _upload_uguu)]:
            try:
                url = fn(video_path)
                if url and _e_video(url):
                    return url
                print(f"  {name} falhou{' (link não é vídeo)' if url else ''}, tentando proximo...")
            except Exception as e:
                print(f"  {name} erro: {e}, tentando proximo...")
        if volta == 1:
            time.sleep(20)
    return None


def _base_url(token):
    """Retorna a base URL certa conforme o tipo de token."""
    if token.startswith("IGAA"):
        return GRAPH_IG_URL
    return GRAPH_FB_URL


def graph_post(path, params, method="POST"):
    """Faz requisição à Graph API (detecta IG vs FB pelo token)."""
    base = _base_url(params.get("access_token", ""))
    url = f"{base}/{path}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": json.loads(body) if body.startswith("{") else body, "status": e.code}


def graph_get(path, params):
    """GET na Graph API (detecta IG vs FB pelo token)."""
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


def postar_reel(conta, video_url, caption="", share_to_feed=True, thumb_offset=None, publicar=True):
    """Posta um Reel no Instagram. Retorna (sucesso, msg).
    25/10: share_to_feed=true EXPLICITO (o Reel tambem vai pro feed de quem segue; no @msenergycap os Reels chegavam a
    2-8 contas com 2 mil seguidores) e thumb_offset (ms do quadro da capa; o 1o quadro as vezes e escuro).
    publicar=False: cria e espera o container ficar pronto, sem publicar (teste de parametros; expira em 24 h)."""
    token = conta["data"]["accessToken"]

    if token.startswith("IGAA"):
        me = graph_get("me", {"fields": "user_id", "access_token": token})
        ig_id = me.get("user_id") or me.get("id")
        if not ig_id:
            return False, f"nao consegui pegar ig user_id: {me}"
    else:
        ig_id = conta["data"]["instagramBusinessAccountId"]

    # Passo 1: Criar container
    params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true" if share_to_feed else "false",
        "access_token": token,
    }
    if thumb_offset is not None:
        params["thumb_offset"] = str(int(thumb_offset))
    resp = graph_post(f"{ig_id}/media", params)
    if "error" in resp:
        err = resp["error"]
        if isinstance(err, dict):
            msg = err.get("error", {}).get("message", str(err))
            code = err.get("error", {}).get("code", 0)
        else:
            msg = str(err)
            code = resp.get("status", 0)
        return False, f"container falhou: [{code}] {msg}"

    container_id = resp.get("id")
    if not container_id:
        return False, f"sem container_id: {resp}"

    # Passo 2: Aguardar processamento (até 150s)
    for _ in range(30):
        time.sleep(5)
        status_resp = graph_get(container_id, {
            "fields": "status_code",
            "access_token": token
        })
        status = status_resp.get("status_code", "")
        if status == "FINISHED":
            break
        if status == "ERROR":
            return False, f"processamento deu erro: {status_resp}"
    else:
        return False, f"timeout processamento (status={status})"
    if not publicar:
        return True, f"container pronto, NAO publicado (teste): {container_id}"

    # Passo 3: Publicar
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
        return False, f"publish falhou: {msg}"

    media_id = pub_resp.get("id", "?")
    return True, f"publicado! media_id={media_id}"


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--caption", default="")
    parser.add_argument("--conta", help="Nome da conta (parcial)")
    parser.add_argument("--listar", action="store_true")
    parser.add_argument("--capa-ms", type=int, help="quadro da capa em milissegundos (thumb_offset)")
    parser.add_argument("--so-reels", action="store_true", help="NAO mandar pro feed (share_to_feed=false)")
    parser.add_argument("--teste-container", action="store_true",
                        help="cria o container e confere os parametros, SEM publicar")
    args = parser.parse_args()

    contas = carregar_contas()

    if args.listar:
        for i, c in enumerate(contas):
            print(f"  [{i}] {c['name']}")
        return

    if args.conta:
        filtradas = [c for c in contas if args.conta.lower() in c["name"].lower()]
        if not filtradas:
            print(f"Conta '{args.conta}' nao encontrada!")
            return
        contas = filtradas

    # Upload do vídeo pra URL pública
    video = Path(args.video)
    if not video.exists():
        print(f"Video nao encontrado: {video}")
        return

    print(f"Subindo video pra litterbox ({video.stat().st_size/1024/1024:.1f} MB)...")
    url = upload_video_publico(str(video))
    if not url:
        print("FALHA no upload pra litterbox!")
        return
    print(f"URL: {url}")

    for conta in contas:
        nome = conta["name"]
        print(f"\n[{nome}] Postando reel...")
        ok, msg = postar_reel(conta, url, caption=args.caption, share_to_feed=not args.so_reels,
                              thumb_offset=args.capa_ms, publicar=not args.teste_container)
        if ok:
            print(f"  OK: {msg}")
        else:
            print(f"  FALHA: {msg}")


if __name__ == "__main__":
    main()
