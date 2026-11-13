#!/usr/bin/env python3
"""youtube_poster.py — posta vídeo no YouTube DIRETO (sem n8n).

Usa as credenciais OAuth extraídas do n8n (D:\\credenciais-canais\\youtube_canais.json):
cada canal tem clientId + clientSecret + refresh_token. Fluxo:
  1. refresh_token -> access_token (POST oauth2.googleapis.com/token)
  2. upload resumable do mp4 (POST/PUT googleapis.com/upload/youtube/v3/videos)

Rodízio entre contas BR pra driblar o limite diário de upload do YouTube.

Uso:
    python bin/youtube_poster.py --video X.mp4 --titulo "..." --descricao "..." \
        --tags "tag1,tag2" --canal "inovare recap manga" [--privacy unlisted] [--short]
    python bin/youtube_poster.py --listar-canais
"""
import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CREDS_FILE = Path(os.environ.get(
    "YT_CREDS_FILE", r"D:\credenciais-canais\youtube_canais.json"))
TOKEN_URL = "<SEGREDO_REMOVIDO>"
UPLOAD_URL = ("https://www.googleapis.com/upload/youtube/v3/videos"
              "?uploadType=resumable&part=snippet,status")


def _load_canais():
    return json.loads(CREDS_FILE.read_text(encoding="utf-8"))


def _find_canal(canais, nome_ou_id):
    for c in canais:
        if c["id"] == nome_ou_id or c["nome"].strip().lower() == nome_ou_id.strip().lower():
            return c
    # match parcial pelo nome
    for c in canais:
        if nome_ou_id.strip().lower() in c["nome"].strip().lower():
            return c
    return None


def refresh_access_token(canal):
    """Troca o refresh_token por um access_token novo."""
    data = urllib.parse.urlencode({
        "client_id": canal["clientId"],
        "client_secret": canal["clientSecret"],
        "refresh_token": canal["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def upload(video_path, titulo, descricao, tags, canal, privacy="public",
           categoria="24", made_for_kids=False, publish_at=None):
    """Upload resumable. Retorna o videoId, ou levanta exceção.

    publish_at: string RFC 3339 ex. '2026-07-01T15:00:00.000Z'. Força privacy=private.

    BLOQUEADO (18/10, unificação): esta cópia local subia DIRETO pela API, sem passar pelo postador (reserva de canal,
    teto, agendamento, parada geral) — e upload por API está proibido desde 16/10. Todo upload vai por
    D:\\postador-de-videos\\bin\\politica.py postar_youtube(..., projeto=...) -> youtube_web_poster.py (navegador).
    """
    raise RuntimeError("upload por API proibido (16/10): use politica.postar_youtube do D:\\postador-de-videos\\bin "
                       "(navegador, com reserva/teto/agendamento); esta cópia local não posta mais")
    video_path = Path(video_path)
    size = video_path.stat().st_size
    token = refresh_access_token(canal)
    status_obj = {
        "privacyStatus": "private" if publish_at else privacy,
        "selfDeclaredMadeForKids": made_for_kids,
    }
    if publish_at:
        status_obj["publishAt"] = publish_at
    meta = {
        "snippet": {
            "title": titulo[:100],
            "description": descricao[:5000],
            "tags": tags if isinstance(tags, list) else [t.strip() for t in tags.split(",") if t.strip()],
            "categoryId": categoria,
        },
        "status": status_obj,
    }
    # 1. inicia sessão resumable
    init = urllib.request.Request(
        UPLOAD_URL, data=json.dumps(meta).encode(), method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": mimetypes.guess_type(str(video_path))[0] or "video/mp4",
            "X-Upload-Content-Length": str(size),
        })
    with urllib.request.urlopen(init, timeout=60) as r:
        session_url = r.headers["Location"]
    # 2. envia o arquivo inteiro (PUT único; suficiente p/ vídeos de poucas dezenas de MB)
    with open(video_path, "rb") as f:
        body = f.read()
    put = urllib.request.Request(
        session_url, data=body, method="PUT",
        headers={"Content-Type": "video/*", "Content-Length": str(size)})
    with urllib.request.urlopen(put, timeout=600) as r:
        res = json.loads(r.read().decode())
    return res.get("id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video")
    ap.add_argument("--titulo")
    ap.add_argument("--descricao", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--canal", help="nome ou id do canal (youtube_canais.json)")
    ap.add_argument("--privacy", default="public",
                    choices=["public", "unlisted", "private"])
    ap.add_argument("--publish-at", default=None,
                    help="Agendar publicação: RFC 3339 ex. 2026-07-01T15:00:00.000Z (força private)")
    ap.add_argument("--listar-canais", action="store_true")
    ap.add_argument("--test-token", action="store_true",
                    help="só testa renovar o access_token do canal (não posta)")
    args = ap.parse_args()

    canais = _load_canais()
    if args.listar_canais:
        for c in canais:
            up = "up" if c.get("tem_upload") else "noup"
            print(f"  [{up}] {c['nome']}  (id {c['id']})")
        return

    canal = _find_canal(canais, args.canal or "")
    if not canal:
        print(f"canal não encontrado: {args.canal}", file=sys.stderr)
        sys.exit(1)

    if args.test_token:
        tok = refresh_access_token(canal)
        print(f"OK: access_token renovado p/ '{canal['nome']}' (len {len(tok)})")
        return

    if not args.video or not args.titulo:
        print("--video e --titulo obrigatórios pra postar", file=sys.stderr)
        sys.exit(1)
    try:
        vid = upload(args.video, args.titulo, args.descricao, args.tags, canal,
                     privacy=args.privacy, publish_at=args.publish_at)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        motivo = ""
        try:
            motivo = json.loads(body)["error"]["errors"][0]["reason"]
        except Exception:
            pass
        # uploadLimitExceeded = bateu no limite DIÁRIO de uploads da conta (não é
        # cota da API). Espere o dia virar e rode de novo (a fila é idempotente).
        print(f"ERRO {e.code} [{motivo}]: {body[:300]}", file=sys.stderr)
        sys.exit(2)
    if args.publish_at:
        print(f"AGENDADO: https://youtu.be/{vid}  (canal: {canal['nome']}) → publica {args.publish_at}")
    else:
        print(f"POSTADO: https://youtu.be/{vid}  (canal: {canal['nome']})")


if __name__ == "__main__":
    main()
