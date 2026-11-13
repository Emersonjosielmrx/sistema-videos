#!/usr/bin/env python3
"""youtube_poster.py — posta vídeo no YouTube DIRETO (sem n8n).

Usa as credenciais OAuth extraídas do n8n (D:\\credenciais-canais\\youtube_canais.json):
cada canal tem clientId + clientSecret + refresh_token. Fluxo:
  1. checa a política (bin/politica.py): parada geral, canal bloqueado, cota do
     dia, aprovação humana do vídeo, intervalo mínimo entre vídeos do canal
  2. refresh_token -> access_token (POST oauth2.googleapis.com/token)
  3. upload resumable do mp4 em pedaços de 16 MB, retomando de onde parou se a
     conexão cair (não carrega o arquivo inteiro na memória)

Uso:
    python bin/youtube_poster.py --video X.mp4 --titulo "..." --descricao "..." \
        --tags "tag1,tag2" --canal "Inovare Manhwa esp" [--privacy unlisted]
    python bin/youtube_poster.py --listar-canais

Saída: POSTADO:/AGENDADO: em caso de sucesso, e SEMPRE uma última linha
"STATUS: <ok|limite|cota|morto|suspenso|parado|nao_aprovado|erro> <info>" que os
scripts de fila usam (ver politica.postar_youtube).
"""
import argparse
import json
import mimetypes
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import politica  # noqa: E402

CREDS_FILE = politica.CREDS_FILE
TOKEN_URL = "<SEGREDO_REMOVIDO>"
UPLOAD_URL = ("https://www.googleapis.com/upload/youtube/v3/videos"
              "?uploadType=resumable&part=snippet,status")
CHUNK = 16 * 1024 * 1024  # múltiplo de 256 KiB, exigido pela API
TENTATIVAS = 6
RETRY_HTTP = (500, 502, 503, 504)

# Códigos de saída do CLI
EXIT_OK, EXIT_USO, EXIT_HTTP, EXIT_BLOQUEADO = 0, 1, 2, 5
# STATUS por código de bloqueio da política
STATUS_BLOQUEIO = {"parado": "parado", "canal_bloqueado": "morto",
                   "cota_diaria": "cota", "nao_aprovado": "nao_aprovado",
                   "reservado": "reservado", "advertencias": "advertencias"}


class _SemRedirect(urllib.request.HTTPRedirectHandler):
    """O protocolo resumable responde 308 'Resume Incomplete' — não é redirect."""
    def redirect_request(self, *a, **k):
        return None


_opener = urllib.request.build_opener(_SemRedirect)


def _load_canais():
    return json.loads(CREDS_FILE.read_text(encoding="utf-8"))


def _find_canal(canais, nome_ou_id):
    canal, _ = politica.achar_canal(nome_ou_id, canais)
    return canal


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


def _offset_confirmado(session_url, size):
    """Pergunta ao YouTube quantos bytes já chegaram. Retorna (offset, resposta_final|None)."""
    req = urllib.request.Request(session_url, data=b"", method="PUT", headers={
        "Content-Length": "0", "Content-Range": f"bytes */{size}"})
    try:
        with _opener.open(req, timeout=60) as r:
            return size, json.loads(r.read().decode())  # já tinha terminado
    except urllib.error.HTTPError as e:
        if e.code != 308:
            raise
        rng = e.headers.get("Range")
        return (int(rng.rsplit("-", 1)[1]) + 1 if rng else 0), None


def _enviar(session_url, video_path, size):
    """Envia o arquivo em pedaços; retoma do último byte confirmado em falhas de rede/5xx."""
    offset, falhas = 0, 0
    with open(video_path, "rb") as f:
        while True:
            f.seek(offset)
            chunk = f.read(CHUNK)
            fim = offset + len(chunk) - 1
            req = urllib.request.Request(session_url, data=chunk, method="PUT", headers={
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {offset}-{fim}/{size}"})
            try:
                with _opener.open(req, timeout=300) as r:
                    return json.loads(r.read().decode())  # 200/201: terminou
            except urllib.error.HTTPError as e:
                if e.code == 308:
                    rng = e.headers.get("Range")
                    offset = int(rng.rsplit("-", 1)[1]) + 1 if rng else 0
                    falhas = 0
                    continue
                if e.code not in RETRY_HTTP or falhas >= TENTATIVAS:
                    raise
                motivo = f"HTTP {e.code}"
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
                if falhas >= TENTATIVAS:
                    raise
                motivo = type(e).__name__
            falhas += 1
            espera = min(2 ** falhas, 60)
            print(f"  ... falha no envio ({motivo}), retomando em {espera}s "
                  f"[{falhas}/{TENTATIVAS}]", file=sys.stderr)
            time.sleep(espera)
            offset, final = _offset_confirmado(session_url, size)
            if final is not None:
                return final


def upload(video_path, titulo, descricao, tags, canal, privacy="public",
           categoria="24", made_for_kids=False, publish_at=None, idioma=None, sintetico=None):
    """Upload resumable. Retorna o videoId, ou levanta exceção.

    publish_at: string RFC 3339 ex. '2026-07-01T15:00:00.000Z'. Força privacy=private.
    idioma: ex. 'pt-BR' -> defaultLanguage + defaultAudioLanguage (ajuda o YouTube a achar o público certo).
    sintetico: True marca 'conteúdo alterado ou sintético' (obrigatório em vídeo realista feito com IA).
    Não aplica a política — quem chama upload() direto (em vez do CLI) é responsável.
    """
    video_path = Path(video_path)
    size = video_path.stat().st_size
    # Dono 21/10: nem emergência abre na hora. A checagem de direitos leva ~10 min DEPOIS do upload; só agendado o
    # bloqueio vira "não publicou" em vez de advertência. Mínimo +25 min (Short) / +25 min + duração (longo).
    if privacy == "public" or publish_at:
        minimo = politica.agenda_minima(video_path)
        pedido = politica._dt(publish_at) if publish_at else None
        if not pedido or pedido < minimo:
            publish_at = politica.rfc3339(minimo)
            print(f"[agenda] publishAt empurrado p/ {publish_at} (margem da checagem de direitos)")
    token = refresh_access_token(canal)
    status_obj = {
        "privacyStatus": "private" if publish_at else privacy,
        "selfDeclaredMadeForKids": made_for_kids,
    }
    if publish_at:
        status_obj["publishAt"] = publish_at
    if sintetico is not None:
        status_obj["containsSyntheticMedia"] = bool(sintetico)
    meta = {
        "snippet": {
            "title": titulo[:100],
            "description": descricao[:5000],
            "tags": tags if isinstance(tags, list) else [t.strip() for t in tags.split(",") if t.strip()],
            "categoryId": categoria,
        },
        "status": status_obj,
    }
    if idioma:
        meta["snippet"]["defaultLanguage"] = idioma
        meta["snippet"]["defaultAudioLanguage"] = idioma
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
    # 2. envia em pedaços
    return _enviar(session_url, video_path, size).get("id")


def _fim(status, info="", code=EXIT_OK):
    print(f"STATUS: {status} {info}".rstrip())
    sys.exit(code)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--video")
    ap.add_argument("--titulo")
    ap.add_argument("--descricao", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--canal", help="nome exato ou id do canal (youtube_canais.json)")
    ap.add_argument("--privacy", default="public",
                    choices=["public", "unlisted", "private"])
    ap.add_argument("--publish-at", default=None,
                    help="Agendar publicação: RFC 3339 ex. 2026-07-01T15:00:00.000Z (força private)")
    ap.add_argument("--categoria", default="24", help="categoryId (24 entretenimento, 20 games, 1 filmes/animacao, 27 educacao, 28 ciencia/tec)")
    ap.add_argument("--idioma", default=None, help="ex. pt-BR (defaultLanguage + defaultAudioLanguage)")
    ap.add_argument("--sintetico", action="store_true", help="marca conteudo sintetico/feito com IA")
    ap.add_argument("--projeto", default=None,
                    help="projeto que está postando (canais reservados: dono ou alimentador do cadastro canais.json)")
    ap.add_argument("--tipo", default=None, help="short/completo/compilado/react/veo... (só pro ledger)")
    ap.add_argument("--listar-canais", action="store_true")
    ap.add_argument("--test-token", action="store_true",
                    help="só testa renovar o access_token do canal (não posta)")
    args = ap.parse_args()

    canais = _load_canais()
    if args.listar_canais:
        for c in canais:
            up = "up" if c.get("tem_upload") else "noup"
            bloq = politica.motivo_bloqueio(c)
            dono = politica.reservado_para(c)
            print(f"  [{up}] {c['nome'].strip()}  (id {c['id']})"
                  + (f"  RESERVADO: {dono}" if dono else "")
                  + (f"  BLOQUEADO: {bloq}" if bloq else ""))
        return

    canal, err = politica.achar_canal(args.canal or "", canais)
    if not canal:
        print(err, file=sys.stderr)
        _fim("erro", err, EXIT_USO)

    if args.test_token:
        tok = refresh_access_token(canal)
        print(f"OK: access_token renovado p/ '{canal['nome'].strip()}' (len {len(tok)})")
        return

    if not args.video or not args.titulo:
        print("--video e --titulo obrigatórios pra postar", file=sys.stderr)
        _fim("erro", "faltou --video/--titulo", EXIT_USO)
    if not Path(args.video).is_file():
        print(f"vídeo não existe: {args.video}", file=sys.stderr)
        _fim("erro", "arquivo não existe", EXIT_USO)
    try:  # 31/10 REGRA da dona: nada sobe com menos de 1080p
        args.video = str(politica.garantir_1080(args.video))
    except Exception as e1080:  # noqa: BLE001
        _fim("erro", f"vídeo abaixo de 1080p e o upscale falhou ({str(e1080)[:150]}) — não sobe", EXIT_USO)

    bloqueio = politica.checar_upload(canal, args.video, args.projeto, args.tipo)
    if bloqueio:
        codigo, msg = bloqueio
        print(f"BLOQUEADO [{codigo}]: {msg}", file=sys.stderr)
        _fim(STATUS_BLOQUEIO[codigo], msg, EXIT_BLOQUEADO)

    # Intervalo mínimo entre vídeos do mesmo canal: agenda a publicação em vez de
    # publicar colado no anterior. Só para vídeos públicos (ou já agendados).
    publish_at = args.publish_at
    if publish_at or args.privacy == "public":
        publish_at = politica.rfc3339(politica.horario_obrigatorio(canal, publish_at, args.projeto, args.tipo))  # nunca público direto
        minimo = politica.agenda_minima(args.video)  # mesma margem que o upload() aplica; o ledger grava o horário real
        if politica._dt(publish_at) < minimo:
            publish_at = politica.rfc3339(minimo)

    try:
        vid = upload(args.video, args.titulo, args.descricao, args.tags, canal,
                     privacy=args.privacy, publish_at=publish_at, categoria=args.categoria,
                     idioma=args.idioma, sintetico=True if args.sintetico else None)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        motivo = ""
        try:
            motivo = json.loads(body)["error"]["errors"][0]["reason"]
        except Exception:
            pass
        # uploadLimitExceeded = bateu no limite DIÁRIO de uploads da conta (não é
        # cota da API). Não insista: a política já limita o volume por canal.
        print(f"ERRO {e.code} [{motivo}]: {body[:300]}", file=sys.stderr)
        classe = politica.classificar_erro(f"{motivo} {body}")
        politica.tratar_erro(canal, classe, f"{e.code} {motivo} {body[:150]}")
        _fim(classe, f"{e.code} {motivo}".strip(), EXIT_HTTP)
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
        print(f"ERRO REDE: {e}", file=sys.stderr)
        _fim("erro", f"rede: {e}", EXIT_HTTP)

    politica.registrar_upload(canal, vid, args.video, publish_at, projeto=args.projeto, tipo=args.tipo)
    url = f"https://youtu.be/{vid}"
    if publish_at:
        print(f"AGENDADO: {url}  (canal: {canal['nome'].strip()}) → publica {publish_at}")
    else:
        print(f"POSTADO: {url}  (canal: {canal['nome'].strip()})")
    _fim("ok", url)


if __name__ == "__main__":
    main()
