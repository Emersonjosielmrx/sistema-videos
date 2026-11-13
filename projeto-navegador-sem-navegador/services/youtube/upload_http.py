# -*- coding: utf-8 -*-
r"""services/youtube/upload_http.py — subir vídeo no YouTube Studio por HTTP (cookies do gemini-argo, sem Chrome).

Sequência capturada de um upload real da produção (29/10 04:18, gamenoturno; capturas\passivo_youtube_20261029.jsonl,
tools\capturar_passivo.py):
  1. POST upload.youtube.com/upload/studio  (X-Goog-Upload-Command: start, resumable) corpo {"frontendUploadId"}
     -> cabeçalho X-Goog-Upload-URL
  2. POST <essa URL>  (X-Goog-Upload-Command: "upload, finalize", Offset 0) corpo = o arquivo -> scottyResourceId
  3. youtubei/v1/upload/createvideo  -> videoId (rascunho privado)
  4. youtubei/v1/video_manager/metadata_update: título, descrição, tags, não é para crianças, e por fim
     privado + tira o rascunho + scheduledPublishing (regra do dono: SEMPRE agendado, nunca público direto).
Descoberto: a escrita no Studio exige context.request.sessionInfo.token (sem ele o servidor responde 200 vazio). A
prova antirrobô (attestationResponseData) NÃO é exigida. O token vem de ars/grst na página; o ouvinte passivo guarda
o último de cada canal em cookies\yt_sessao_<slug>.json (vale pelo menos ~1 h; validade exata ainda não medida).

    python -m services.youtube.upload_http <slug> video.mp4 "título" [--descricao txt] [--tags a,b] [--agendar EPOCH] [--privado]
"""
import hashlib
import json
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# 30/10: no fim do sys.path (regra 23/10: pasta de outro projeto nunca na frente — este módulo roda DENTRO do postador)
for _p in (str(ROOT), r"D:\gemini-argo"):
    if _p not in sys.path:
        sys.path.append(_p)
import youtube_http  # noqa: E402
from core.arquivo import gravar_json  # noqa: E402

SESSOES = ROOT / "cookies"
MARGEM_AGENDA = 300  # s: horário que já passou (ou quase) não é agendado — o vídeo abriria na hora


class LimiteDiario(RuntimeError):
    """createvideo REJECTED pelo limite diário (canal sem telefone): o Chrome bate no mesmo limite."""


def token_sessao(slug):
    a = SESSOES / f"yt_sessao_{slug}.json"
    if not a.exists():
        raise RuntimeError(f"{slug}: sem sessionInfo.token (o ouvinte passivo guarda quando a produção abre o Studio)")
    try:
        return json.loads(a.read_text("utf-8"))["token"]
    except (ValueError, KeyError) as ex:  # arquivo pela metade/estragado = sem token (renova), não erro estranho
        raise RuntimeError(f"{slug}: yt_sessao ilegível ({type(ex).__name__})") from ex


def _studio(slug):
    """youtube_http.Studio SEM a ressincronização automática pelo Chrome (quem renova aqui é o colher_sessao, que
    pega token + cookies juntos). Troca o `sincronizar` só durante a construção e devolve o original."""
    orig = youtube_http.sincronizar

    def _morto(s):
        raise RuntimeError(f"{s}: cookies mortos")
    youtube_http.sincronizar = _morto
    try:
        return youtube_http.Studio(slug)
    except ValueError as ex:  # JSON dos cookies lido no meio de uma gravação de outro processo
        raise RuntimeError(f"{slug}: cookies ilegíveis ({ex})") from ex
    finally:
        youtube_http.sincronizar = orig


def colher_sessao(slug, espera=90):  # 60 s não bastou com o PC1 carregado (inovare_ita 29/10 17:52)
    """Uma visita escondida do Chrome do cofre ao Studio guarda o token (ars/grst) E os cookies da MESMA visita.
    29/10: abrir o Chrome do cofre gira o login e mata a cópia HTTP e o token antigos; colher os dois juntos no fim da
    visita deixa o par vivo (o manter_cookies gira de hora em hora depois)."""
    import urllib.request
    import websocket
    for p in (r"D:\logins-google", r"D:\postador-de-videos\bin\netbooks"):
        if p not in sys.path:
            sys.path.append(p)
    import chrome_conta
    import cofre
    from core.cdp_aba import Aba
    email = youtube_http._email(slug)
    chrome_conta._liberar_ram()
    porta, proc = cofre.abrir(email, url="about:blank", visivel=False)
    a, ids, token = None, set(), None
    try:
        for _ in range(30):
            try:
                a = Aba.da_porta(porta, nova="about:blank")
                break
            except Exception:  # noqa: BLE001
                time.sleep(1)
        if a is None:
            raise RuntimeError(f"{slug}: o Chrome do cofre (porta {porta}) não abriu aba em 30 s")
        a.em("Network.requestWillBeSent", lambda ev: "/ars/grst" in ev["request"]["url"] and ids.add(ev["requestId"]))
        a.em("Network.loadingFinished", lambda ev: ev["requestId"] in ids and ids.add(("ok", ev["requestId"])))
        a.chamar("Network.enable")
        a.chamar("Page.navigate", {"url": youtube_http.STUDIO})
        fim = time.time() + espera
        while time.time() < fim and not token:
            time.sleep(2)
            for x in [i for i in list(ids) if isinstance(i, tuple)]:  # list(): a thread do CDP mexe no set
                ids.discard(x)
                try:
                    corpo = a.chamar("Network.getResponseBody", {"requestId": x[1]}, timeout=15).get("body", "")
                    token = json.loads(corpo).get("sessionToken")
                except (RuntimeError, TimeoutError, ValueError, AttributeError):
                    continue  # corpo indisponível/não-JSON: espera o próximo ars/grst
                if token:
                    break
        if not token:
            raise RuntimeError(f"{slug}: o Studio não chamou ars/grst em {espera}s; página parou em "
                               f"{a.js('location.href')[:120]} | {a.js('document.title')[:60]}")
        time.sleep(5)  # deixa a página terminar de girar os cookies antes de copiar
        ck = {c["name"]: c["value"] for c in a.chamar("Network.getAllCookies")["cookies"]
              if c.get("domain", "").endswith("youtube.com")}
    finally:
        if a:
            a.fechar(fechar_aba=True)
        if proc:
            try:
                v = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=10).read())
                w = websocket.create_connection(v["webSocketDebuggerUrl"], timeout=10, suppress_origin=True)
                w.send(json.dumps({"id": 1, "method": "Browser.close"}))
                w.close()
            except Exception:  # noqa: BLE001
                pass
            cofre.fechar(proc, None, email)
    if "SAPISID" not in ck:
        raise RuntimeError(f"{slug}: sem SAPISID (conta deslogada no cofre?)")
    # atômico: o youtube_http da produção lê estes arquivos a qualquer hora
    gravar_json(youtube_http.COOKIES_DIR / f"{slug}.json", ck, ensure_ascii=True)
    gravar_json(SESSOES / f"yt_sessao_{slug}.json",
                {"token": token, "capturado": time.strftime("%Y-%m-%d %H:%M:%S"), "origem": "colher_sessao"},
                indent=None, ensure_ascii=True)
    return token


class Enviador:
    def __init__(self, slug):
        self.slug = slug
        try:
            self.st = _studio(slug)
            self.token = token_sessao(slug)
        except RuntimeError:  # cookies mortos ou sem token: uma visita escondida colhe os dois
            self._renovar()

    def _renovar(self):
        """Token morto (o Chrome da produção abriu o canal e girou o login): colhe cookies + token juntos de novo."""
        print(f"[upload_http] {self.slug}: renovando cookies + token (visita escondida ao Studio)", flush=True)
        colher_sessao(self.slug)
        self.st = _studio(self.slug)
        self.token = token_sessao(self.slug)

    def _ler_video(self, vid):
        """O vídeo como o Studio mostra (privacidade, agendado_para) ou None se não achou / não deu para ler."""
        try:
            return next((v for v in self.st.videos(15) if v["id"] == vid), None)
        except Exception as ex:  # noqa: BLE001 — leitura é conferência, não pode derrubar
            print(f"[upload_http] {self.slug}: não consegui reler {vid} ({type(ex).__name__}: {str(ex)[:100]})", flush=True)
            return None

    def _hd(self):
        ts = int(time.time())
        sap = self.st.s.cookies.get("SAPISID")
        return {"Authorization": f"SAPISIDHASH {ts}_{hashlib.sha1(f'{ts} {sap} {youtube_http.STUDIO}'.encode()).hexdigest()}",
                "X-Origin": youtube_http.STUDIO, "Origin": youtube_http.STUDIO, "x-goog-authuser": "0"}

    def _yt(self, rota, corpo):
        corpo["context"] = {"client": {"clientName": 62, "clientVersion": self.st.versao, "hl": "pt", "gl": "BR"},
                            "request": {"sessionInfo": {"token": self.token}}}
        r = self.st.s.post(f"{youtube_http.STUDIO}/youtubei/v1/{rota}?alt=json", json=corpo, headers=self._hd(),
                           timeout=60)
        if r.status_code != 200:
            # numa linha só: o JSON de erro vem indentado e o postador corta a mensagem em 300 caracteres
            raise RuntimeError(f"{rota}: HTTP {r.status_code} {' '.join(r.text.split())[:300]}")
        return r.json()

    def _metadados(self, vid, **campos):
        d = self._yt("video_manager/metadata_update", {"encryptedVideoId": vid, "flowType": "MDE_FLOW_TYPE_UPLOAD",
                                                       "videoReadMask": {"videoId": True}, **campos})
        if (d.get("overallResult") or {}).get("resultCode") != "UPDATE_SUCCESS":
            raise RuntimeError(f"metadata_update {list(campos)} falhou: {str(d)[:300]}")

    def _thumbnail(self, vid, imagem):
        """Capa personalizada por HTTP, capturada do Studio em 29/10 (capturas\\captura_capa10.jsonl, assistiainvestimentos):
        upload/studiothumbnail (resumable, corpo {}) -> scottyResourceId -> metadata_update videoStill
        UPLOAD_CUSTOM_THUMBNAIL. Canal sem telefone verificado (features.customThumbnails DISABLED) não aceita capa nem
        pelo Chrome: aí sobe sem capa. Falhou = sobe sem capa (nunca derruba o upload)."""
        arq = Path(imagem)
        if not arq.is_file():
            print(f"[upload_http] {self.slug}: capa {arq.name} não existe; sobe sem capa", flush=True)
            return
        if arq.stat().st_size > 2_000_000:
            print(f"[upload_http] {self.slug}: capa {arq.name} tem {arq.stat().st_size / 1e6:.1f} MB (max 2 MB); sobe sem capa", flush=True)
            return
        d = self._yt("creator/get_creator_channels", {"channelIds": [self.st.channel_id], "mask": {"features": {"all": True}}})
        if ((d.get("channels") or [{}])[0].get("features") or {}).get("customThumbnails", {}).get("status") \
                != "CREATOR_FEATURE_STATUS_ENABLED":
            print(f"[upload_http] {self.slug}: canal sem capa personalizada (telefone não verificado); sobe sem capa", flush=True)
            return
        fmt = "PNG" if arq.suffix.lower() == ".png" else "JPEG"
        dados = arq.read_bytes()
        r = self.st.s.post("https://upload.youtube.com/upload/studiothumbnail?authuser=0", data="{}",
                           headers={**self._hd(), "X-Goog-Upload-Protocol": "resumable",
                                    "X-Goog-Upload-Command": "start", "X-Goog-Upload-File-Name": arq.name,
                                    "X-Goog-Upload-Header-Content-Length": str(len(dados)),
                                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}, timeout=60)
        url = r.headers.get("X-Goog-Upload-URL")
        if not url:
            raise RuntimeError(f"studiothumbnail start sem URL: {r.status_code} {r.text[:200]}")
        r = self.st.s.post(url, data=dados, timeout=120,
                           headers={**self._hd(), "X-Goog-Upload-Command": "upload, finalize",
                                    "X-Goog-Upload-Offset": "0", "X-Goog-Upload-File-Name": arq.name,
                                    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"})
        scotty = r.json().get("scottyResourceId")
        if not scotty:
            raise RuntimeError(f"capa sem scottyResourceId: {r.status_code} {r.text[:200]}")
        self._metadados(vid, flowType="MDE_FLOW_TYPE_EDIT",
                        videoStill={"operation": "UPLOAD_CUSTOM_THUMBNAIL",
                                    "image": {"encryptedScottyResourceId": scotty,
                                              "name": "CUSTOM_THUMBNAIL_IMAGE_NAME_DEFAULT",
                                              "format": f"CUSTOM_THUMBNAIL_IMAGE_FORMAT_{fmt}"}})
        print(f"[upload_http] {self.slug}: capa enviada ({arq.name})", flush=True)

    def _playlist_id(self, nome):
        """Id da playlist do canal com este título; não existe = cria pública (o Chrome fazia igual)."""
        d = self._yt("creator/list_creator_playlists", {"channelId": self.st.channel_id, "memberVideoIds": [],
                                                        "pageSize": 500, "mask": {"playlistId": True, "title": True}})
        for p in d.get("playlists") or []:
            if (p.get("title") or "").strip().lower() == nome.strip().lower():
                return p["playlistId"]
        d = self._yt("playlist/create", {"title": nome[:150], "privacyStatus": "PUBLIC", "description": ""})
        pid = d.get("playlistId")
        if not pid:
            raise RuntimeError(f"playlist/create sem playlistId: {str(d)[:300]}")
        print(f"[upload_http] {self.slug}: playlist '{nome}' criada ({pid})", flush=True)
        return pid

    def _playlist(self, vid, nome):
        """Põe o vídeo na playlist (metadata_update addToPlaylist) e confere relendo a lista: o metadata_update responde
        UPDATE_SUCCESS até para campo que ignora."""
        pid = self._playlist_id(nome)
        self._metadados(vid, flowType="MDE_FLOW_TYPE_EDIT", addToPlaylist={"addToPlaylistIds": [pid]})
        d = self._yt("creator/list_creator_playlists", {"channelId": self.st.channel_id, "memberVideoIds": [vid],
                                                        "pageSize": 500, "mask": {"playlistId": True, "title": True}})
        if not any(m.get("playlistId") == pid and m.get("containsRequestedVideos") == "CONTAINS_REQUESTED_VIDEOS_ALL"
                   for m in d.get("playlistMemberships") or []):
            raise RuntimeError(f"vídeo não apareceu na playlist {pid}")
        print(f"[upload_http] {self.slug}: na playlist '{nome}'", flush=True)

    def enviar(self, arquivo, titulo, descricao="", tags=(), agendar=None, privado=False, short=True, capa=None,
               playlist=None, sintetico=None):
        arq = Path(arquivo)
        if not agendar and not privado:  # antes de gastar envio/cota (antes só era checado no fim)
            raise RuntimeError("sem horário: o dono proíbe público direto (use agendar= ou privado=True)")
        self._conferir_horario(agendar, privado)
        fid = f"innertube_studio:{str(uuid.uuid4()).upper()}:0"
        r = self.st.s.post("https://upload.youtube.com/upload/studio?authuser=0", data=json.dumps({"frontendUploadId": fid}),
                           headers={**self._hd(), "X-Goog-Upload-Protocol": "resumable",
                                    "X-Goog-Upload-Command": "start", "X-Goog-Upload-File-Name": arq.name,
                                    "X-Goog-Upload-Header-Content-Length": str(arq.stat().st_size),
                                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}, timeout=60)
        url = r.headers.get("X-Goog-Upload-URL")
        if not url:
            raise RuntimeError(f"upload start sem URL: {r.status_code} {r.text[:200]}")
        with arq.open("rb") as f:  # 30/10: em partes (vídeo longo de GB inteiro na RAM derrubava o PC1)
            r = self.st.s.post(url, data=f, timeout=(30, 1800),
                               headers={**self._hd(), "X-Goog-Upload-Command": "upload, finalize",
                                        "X-Goog-Upload-Offset": "0", "X-Goog-Upload-File-Name": arq.name,
                                        "Content-Length": str(arq.stat().st_size),
                                        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"})
        try:
            scotty = r.json().get("scottyResourceId")
        except ValueError:
            scotty = None
        if not scotty:
            raise RuntimeError(f"envio do arquivo sem scottyResourceId: {r.status_code} {r.text[:300]}")
        for tentativa in (1, 2):
            d = self._yt("upload/createvideo", {"channelId": self.st.channel_id,
                                                "resourceId": {"scottyResourceId": {"id": scotty}},
                                                "frontendUploadId": fid, "presumedShort": short,
                                                "initialMetadata": {"title": {"newTitle": titulo},
                                                                    "privacy": {"newPrivacy": "PRIVATE"},
                                                                    "draftState": {"isDraft": True}}})
            if d.get("videoId") or d.get("contents") or tentativa == 2:
                break
            self._renovar()  # resposta vazia = token morto; o arquivo já enviado (scotty) serve na 2ª tentativa
        vid = d.get("videoId")
        if not vid:  # ex. 29/10 gamenoturno: REJECTED "O limite diário de envios foi alcançado" (canal sem telefone)
            st = next(iter(((d.get("contents") or {}).get("uploadFeedbackItemRenderer") or {}).get("contents") or []),
                      {}).get("uploadStatus") or {}
            msg = " ".join(r.get("text", "") for k in ("message", "detailedMessage") for r in (st.get(k) or {}).get("runs", []))
            erro = LimiteDiario if "limite" in msg.lower() or "limit" in msg.lower() else RuntimeError
            raise erro(f"createvideo sem videoId: {st.get('uploadStatus')} {msg}" if st else
                       f"createvideo sem videoId: {str(d)[:300]}")
        print(f"[upload_http] {self.slug}: criado {vid} (rascunho privado)", flush=True)
        try:
            return self._completar(vid, descricao, tags, agendar, privado, capa, playlist, sintetico)
        except RuntimeError as ex:
            # o vídeo já existe: quem chama cai no Chrome e sobe outro; deixa rastro do rascunho privado que sobrou.
            # O rastro vai NA FRENTE: o postador corta a mensagem em 300 caracteres (30/10 forjareact/cenareact: o 403
            # do metadata_update ocupava tudo e o id do rascunho sumia do youtube_http.log)
            raise RuntimeError(f"[rascunho privado {vid} ficou no canal] {ex}") from ex

    def _conferir_horario(self, agendar, privado):
        if agendar and not privado and int(agendar) < time.time() + MARGEM_AGENDA:
            raise RuntimeError(f"horário de agendamento {time.strftime('%d/%m %H:%M', time.localtime(int(agendar)))} "
                               f"já passou ou falta menos de {MARGEM_AGENDA // 60} min: não agendo (abriria na hora)")

    def _completar(self, vid, descricao, tags, agendar, privado, capa, playlist, sintetico):
        if descricao:
            self._metadados(vid, description={"newDescription": descricao,
                                              "descriptionOperation": "MDE_TEXT_UPDATE_OPERATION_SET"})
        selo = {} if sintetico is None else {"alteredContent": {
            "operation": "MDE_ALTERED_CONTENT_UPDATE_OPERATION_SET",
            "newCreatorDisclosedHasAlteredContent": f"MDE_HAS_ALTERED_CONTENT_{'YES' if sintetico else 'NO'}"}}
        self._metadados(vid, tags={"newTags": list(tags)},
                        madeForKids={"operation": "MDE_MADE_FOR_KIDS_UPDATE_OPERATION_SET",
                                     "newMfk": "MDE_MADE_FOR_KIDS_TYPE_NOT_MFK"}, **selo)
        if playlist:
            try:
                self._playlist(vid, playlist)
            except Exception as ex:  # noqa: BLE001 — playlist falhou não derruba o upload (igual ao Chrome)
                print(f"[upload_http] {self.slug}: playlist falhou ({type(ex).__name__}: {str(ex)[:120]}); sobe sem playlist", flush=True)
        if capa:
            try:
                self._thumbnail(vid, capa)
            except Exception as ex:  # noqa: BLE001 — capa falhou não derruba o upload
                print(f"[upload_http] {self.slug}: capa falhou ({type(ex).__name__}: {str(ex)[:120]}); sobe sem capa", flush=True)
        final = {"privacyState": {"newPrivacy": "PRIVATE"},
                 "draftState": {"operation": "MDE_DRAFT_STATE_UPDATE_OPERATION_REMOVE_DRAFT_STATE"}}
        if agendar and not privado:
            # 30/10: o envio pode ter levado mais que a margem do postador — agendar no passado publicaria na hora
            self._conferir_horario(agendar, privado)
            final["scheduledPublishing"] = {"set": {"timeSec": str(int(agendar)), "privacy": "PUBLIC"}}
        elif not privado:
            raise RuntimeError("sem horário: o dono proíbe público direto (use agendar= ou privado=True)")
        try:
            self._metadados(vid, **final)
        except Exception:
            # 30/10: timeout/5xx DEPOIS de o servidor gravar = o Chrome subiria um 2º vídeo no mesmo horário.
            v = self._ler_video(vid)
            if not (v and self._final_ok(v, agendar, privado)):
                raise
            print(f"[upload_http] {self.slug}: etapa final deu erro mas o Studio já mostra {vid} certo", flush=True)
        return self._conferir_final(vid, agendar, privado)

    @staticmethod
    def _final_ok(v, agendar, privado):
        if v.get("privacidade") == "public":
            return False
        return privado or v.get("agendado_para") == int(agendar)

    def _conferir_final(self, vid, agendar, privado):
        """O metadata_update responde UPDATE_SUCCESS até para campo que ignora: relê e confere privacidade/agenda.
        Público fora de hora = volta para privado na hora e falha. Sem conseguir reler = confia no UPDATE_SUCCESS
        (falhar aqui faria o Chrome subir um 2º vídeo)."""
        for espera in (0, 3, 6):  # a lista do Studio pode demorar uns segundos para mostrar a agenda nova
            time.sleep(espera)
            v = self._ler_video(vid)
            if v is None or self._final_ok(v, agendar, privado):
                return vid
        if v.get("privacidade") == "public":
            try:
                self._metadados(vid, flowType="MDE_FLOW_TYPE_EDIT", privacyState={"newPrivacy": "PRIVATE"})
                volta = "voltei para privado"
            except Exception as ex:  # noqa: BLE001
                volta = f"NÃO consegui voltar para privado ({type(ex).__name__}) — conferir no Studio"
            raise RuntimeError(f"{vid} ficou PÚBLICO sem agendamento — {volta}")
        if not privado and v.get("agendado_para") != int(agendar):
            raise RuntimeError(f"{vid}: agendamento não pegou (Studio mostra {v.get('agendado_para')}, "
                               f"pedido {int(agendar)}); ficou privado")
        return vid


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    arg = lambda n, p=None: a[a.index(n) + 1] if n in a else p  # noqa: E731
    vid = Enviador(a[0]).enviar(a[1], a[2], descricao=arg("--descricao", ""),
                                tags=[t for t in arg("--tags", "").split(",") if t],
                                agendar=arg("--agendar"), privado="--privado" in a,
                                capa=arg("--capa"))
    print("videoId:", vid, f"https://studio.youtube.com/video/{vid}/edit")


if __name__ == "__main__":
    main()
