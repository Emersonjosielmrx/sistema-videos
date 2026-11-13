# -*- coding: utf-8 -*-
r"""services/instagram/postar.py — postar no Instagram por HTTP com a sessão do Chrome do cofre (sem abrir janela).

Mesmos cookies e o MESMO User-Agent do Chrome do perfil ig_<conta> (core\cofre_cookies.py), conexão imitando o
Chrome (curl_cffi): para o Instagram é o mesmo navegador de sempre, no mesmo PC/IP. Regra do dono (25/10): conta nova
logada em aparelho novo foi suspensa — testar só em conta antiga, uma por vez.

Fluxo do próprio site:
  1. foto  -> POST /rupload_igphoto/fb_uploader_<upload_id>   (bytes da imagem; parâmetros no X-Instagram-Rupload-Params)
  2. story -> POST /api/v1/media/configure_to_story/           (upload_id)
     feed  -> POST /api/v1/media/configure/                    (upload_id + legenda)
     carrossel -> várias fotos + POST /api/v1/media/configure_sidecar/ (children_metadata)

    python -m services.instagram.postar story <conta> imagem.jpg
    python -m services.instagram.postar carrossel <conta> "legenda" img1.jpg img2.jpg ...
    python -m services.instagram.postar perfil <conta> [--bio "..."] [--link https://...]
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from services.instagram.web import APP_ID, InstagramWeb  # noqa: E402

LOG = ROOT / "logs" / "instagram_postagens.jsonl"


class InstagramPostar(InstagramWeb):
    def _hd(self, extra=None):
        h = {"X-IG-App-ID": APP_ID, "X-CSRFToken": self.s.cookies.get("csrftoken") or "", "X-ASBD-ID": "359341",
             "X-Requested-With": "XMLHttpRequest", "X-Instagram-AJAX": getattr(self, "rev", "1") or "1",
             "Origin": "https://www.instagram.com", "Referer": "https://www.instagram.com/", "X-IG-D": "www"}
        # 13/11 (captura do navegador 12/11, capturas\passivo_instagram_20261112.jsonl): o site manda também o LSD e o
        # claim (X-IG-WWW-Claim, devolvido pelo próprio Instagram em respostas anteriores — "0" quando ainda não tem)
        if getattr(self, "lsd", ""):
            h["X-FB-LSD"] = self.lsd
        h["X-IG-WWW-Claim"] = getattr(self, "claim", "") or "0"
        h.update(extra or {})
        return h

    def subir_foto(self, caminho):
        """Envia a imagem (JPEG) e devolve o upload_id."""
        from PIL import Image
        import io
        im = Image.open(caminho).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=92)
        dados = buf.getvalue()
        upload_id = str(int(time.time() * 1000))
        nome = f"fb_uploader_{upload_id}"
        params = {"media_type": 1, "upload_id": upload_id, "upload_media_height": im.height,
                  "upload_media_width": im.width}
        r = self.s.post(f"https://www.instagram.com/rupload_igphoto/{nome}", data=dados, timeout=120,
                        headers=self._hd({"X-Entity-Name": nome, "X-Entity-Length": str(len(dados)),
                                          "X-Entity-Type": "image/jpeg", "Offset": "0", "Content-Type": "image/jpeg",
                                          "X-Instagram-Rupload-Params": json.dumps(params)}))
        if r.status_code != 200 or '"ok"' not in r.text:
            raise RuntimeError(f"upload da foto falhou: {r.status_code} {r.text[:200]}")
        return upload_id, im.size

    def _registrar(self, tipo, resp, extra):
        LOG.parent.mkdir(exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "conta": self.conta, "tipo": tipo,
                                "ok": resp.get("status") == "ok", "media": (resp.get("media") or {}).get("code")
                                or (resp.get("media") or {}).get("pk"), **extra}, ensure_ascii=False) + "\n")

    @staticmethod
    def _story_9x16(imagem):
        """09/11 (dona: "os stories estão saindo com imagens cortadas, na Globo principalmente"): a capa do carrossel é
        4:5 (1080x1350) e o story é 9:16 — o Instagram dava zoom e cortava as bordas (texto e logo). Agora monta
        1080x1920 com a imagem INTEIRA no centro sobre o fundo desfocado dela. Desligar: STORY_9X16=0."""
        import os
        from pathlib import Path as _P
        if os.environ.get("STORY_9X16", "1") == "0":
            return imagem
        from PIL import Image, ImageFilter
        im = Image.open(imagem).convert("RGB")
        if abs(im.width / im.height - 9 / 16) < 0.01:
            return imagem  # já é 9:16
        W, H = 1080, 1920
        fundo = im.resize((W, int(im.height * W / im.width)) if im.width / im.height < W / H else
                          (int(im.width * H / im.height), H), Image.LANCZOS)
        fundo = fundo.crop(((fundo.width - W) // 2, (fundo.height - H) // 2,
                            (fundo.width - W) // 2 + W, (fundo.height - H) // 2 + H))
        fundo = fundo.filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.55))
        esc = min(W / im.width, H / im.height)
        frente = im.resize((int(im.width * esc), int(im.height * esc)), Image.LANCZOS)
        fundo.paste(frente, ((W - frente.width) // 2, (H - frente.height) // 2))
        saida = _P(imagem).with_name(_P(imagem).stem + "_story9x16.jpg")
        fundo.save(saida, quality=95)
        return str(saida)

    def story(self, imagem):
        imagem = self._story_9x16(imagem)
        upload_id, _ = self.subir_foto(imagem)
        r = self.s.post("https://www.instagram.com/api/v1/media/configure_to_story/", timeout=60, headers=self._hd(),
                        data={"upload_id": upload_id, "caption": "", "configure_mode": "1",
                              "share_to_facebook": "", "share_to_fb_destination_id": "",
                              "share_to_fb_destination_type": "USER", "source_type": "library"})
        d = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text[:300]}
        self._registrar("story", d, {"arquivo": str(imagem), "http": r.status_code})
        if d.get("status") != "ok":
            raise RuntimeError(f"story recusado: {r.status_code} {str(d)[:300]}")
        return (d.get("media") or {}).get("pk")

    def carrossel(self, imagens, legenda):
        """Post de 2 a 10 imagens no feed (carrossel nativo)."""
        if not 2 <= len(imagens) <= 10:  # assert some com python -O
            raise ValueError(f"carrossel precisa de 2 a 10 imagens (veio {len(imagens)})")
        filhos = []
        for img in imagens:
            uid, (w, h) = self.subir_foto(img)
            filhos.append({"upload_id": uid, "source_type": "library", "edits": {"crop_original_size": [w, h]}})
            time.sleep(2)
        corpo = {"caption": legenda, "client_sidecar_id": str(int(time.time() * 1000)), "children_metadata": filhos,
                 "disable_comments": "0", "like_and_view_counts_disabled": False, "source_type": "library"}
        r = self.s.post("https://www.instagram.com/api/v1/media/configure_sidecar/", timeout=120,
                        headers=self._hd({"Content-Type": "application/json"}), data=json.dumps(corpo))
        d = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text[:300]}
        self._registrar("carrossel", d, {"n": len(imagens), "http": r.status_code})
        if d.get("status") != "ok":
            raise RuntimeError(f"carrossel recusado: {r.status_code} {str(d)[:300]}")
        return (d.get("media") or {}).get("code")


    def reel(self, video, legenda):
        """Reel (vai também para o feed). Capturado 29/10 (capturas/ig_reel.jsonl): rupload_igvideo em i.instagram.com
        -> rupload_igphoto (capa, mesmo upload_id) -> configure_to_clips (202 enquanto processa). Devolve o código."""
        import subprocess
        import tempfile
        if not (legenda or "").strip():
            raise RuntimeError("Reel sem legenda: não posto (regra 'Video' nunca mais)")
        p = Path(video)
        import shutil
        lado = Path(str(p) + ".meta.json")  # 29/10 (D23): máquina sem ffmpeg (Acer) recebe medidas+capa do PC1
        if lado.exists() and not shutil.which("ffprobe"):
            m_ = json.loads(lado.read_text("utf-8"))
            w, h, dur = m_["w"], m_["h"], float(m_["dur"])
        else:
            pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
                                 "-select_streams", "v:0", "-of", "json", str(p)], capture_output=True,
                                text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                info = json.loads(pr.stdout)
                w, h = info["streams"][0]["width"], info["streams"][0]["height"]
                dur = float(info["format"]["duration"])
            except (ValueError, KeyError, IndexError):
                raise RuntimeError(f"ffprobe não leu o vídeo {p.name}: {pr.stderr.strip()[:200]}") from None
        uid = str(int(time.time() * 1000))
        nome = f"fb_uploader_{uid}"
        dados = p.read_bytes()
        params = {"client-passthrough": "1", "is_clips_video": "1", "for_album": False, "is_sidecar": "0",
                  "media_type": 2, "upload_id": uid, "upload_media_duration_ms": int(dur * 1000),
                  "upload_media_height": h, "upload_media_width": w, "video_format": "", "video_transform": None,
                  "provenance_metadata": json.dumps({"origin": ["EXTERNAL"]})}
        r = self.s.post(f"https://i.instagram.com/rupload_igvideo/{nome}", data=dados, timeout=600,
                        headers=self._hd({"X-Entity-Name": nome, "X-Entity-Length": str(len(dados)), "Offset": "0",
                                          "X-Instagram-Rupload-Params": json.dumps(params)}))
        if '"ok"' not in r.text:
            raise RuntimeError(f"envio do vídeo falhou: {r.status_code} {r.text[:200]}")
        capa_pronta = Path(str(p) + ".capa.jpg")
        if capa_pronta.exists():
            capa = capa_pronta
        else:
            capa = Path(tempfile.gettempdir()) / f"{nome}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(p), "-frames:v", "1", "-q:v", "3", str(capa)],
                           check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            cb = capa.read_bytes()
            r = self.s.post(f"https://i.instagram.com/rupload_igphoto/{nome}", data=cb, timeout=120,
                            headers=self._hd({"X-Entity-Name": nome, "X-Entity-Length": str(len(cb)), "Offset": "0",
                                              "X-Entity-Type": "image/jpeg", "Content-Type": "image/jpeg",
                                              "X-Instagram-Rupload-Params": json.dumps(
                                                  {"media_type": 2, "upload_id": uid, "upload_media_height": h,
                                                   "upload_media_width": w,
                                                   "provenance_metadata": json.dumps({"origin": ["EXTERNAL"]})})}))
        finally:
            capa.unlink(missing_ok=True)  # some mesmo com erro (antes a temporária ficava no TEMP)
        if '"ok"' not in r.text:
            raise RuntimeError(f"envio da capa falhou: {r.status_code} {r.text[:200]}")
        campos = {"archive_only": False, "caption": legenda, "clips_share_preview_to_feed": "1",
                  "disable_comments": "0", "disable_oa_reuse": False, "like_and_view_counts_disabled": "0",
                  "media_share_flow": "creation_flow", "source_type": "library", "upload_id": uid,
                  "video_subtitles_enabled": "0"}
        corpo = {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in campos.items()}
        corpo["signed_body"] = "SIGNATURE." + json.dumps(campos, ensure_ascii=False, separators=(",", ":"))
        corpo["fb_dtsg"] = self.dtsg
        # 13/11: campos do site que o navegador manda junto (captura 12/11) — sem eles, 1357001 desde 06/11
        csrf = self.s.cookies.get("csrftoken") or ""
        corpo.update({"lsd": getattr(self, "lsd", ""), "jazoest": "2" + str(sum(ord(c) for c in self.dtsg)),
                      "__a": "1", "__d": "www", "__user": "0", "__comet_req": "7",
                      "__rev": getattr(self, "rev", "") or "", "dpr": "1"})
        if not csrf:
            print("aviso: sem csrftoken no cookie — o configure tende a pedir login", file=sys.stderr)
        ultimo = "sem resposta"
        for _ in range(30):  # 202 = ainda processando o vídeo
            try:
                r = self.s.post("https://www.instagram.com/api/v1/media/configure_to_clips/", data=corpo, timeout=120,
                                headers=self._hd({"Content-Type": "application/x-www-form-urlencoded"}))
            except Exception as ex:  # noqa: BLE001 — 30/10: queda de rede aqui fazia o postador cair no Chrome e
                ultimo = f"{type(ex).__name__}: {str(ex)[:120]}"  # postar o Reel 2x; o mesmo upload_id é repetível
                time.sleep(8)
                continue
            codigo = self._codigo_reel(r)
            if codigo:
                self._registrar("reel", {"status": "ok", "media": {"code": codigo}},
                                {"arquivo": str(video), "legenda": legenda[:80]})
                return codigo
            ultimo = f"{r.status_code} {r.text[:300]}"
            if not self._reel_processando(r):  # recusa de verdade (spam, login, legenda): repetir só piora a conta
                break
            time.sleep(8)
        raise RuntimeError(f"Reel não confirmou: {ultimo}")

    @staticmethod
    def _json_ig(texto):
        """Resposta do site: JSON puro ou `for (;;);{"__ar":1,"payload":{...}}` (capturas/ig_reel.jsonl). Devolve o
        miolo (payload quando houver) ou None."""
        t = (texto or "").lstrip()
        if t.startswith("for (;;);"):
            t = t[9:]
        try:
            d = json.loads(t)
        except ValueError:
            return None
        if isinstance(d, dict) and isinstance(d.get("payload"), dict):
            return d["payload"]
        return d if isinstance(d, dict) else None

    @classmethod
    def _codigo_reel(cls, r):
        """Código do Reel só quando a resposta traz a mídia criada (media.code), não um "code" qualquer do texto."""
        d = cls._json_ig(r.text)
        if d is not None:
            md = d.get("media")
            return md.get("code") if isinstance(md, dict) and md.get("code") else None
        m = re.search(r'"media":\{.*?"code":"([^"]+)"', r.text, re.S)  # JSON cortado: mesmo critério de antes
        return m.group(1) if m else None

    @classmethod
    def _reel_processando(cls, r):
        """Ainda processando (statusCode 202 no corpo ou no HTTP, 5xx, transcode) = esperar; outra recusa = parar.
        Na dúvida (resposta que não se entende) continua esperando, como antes — parar cedo manda pro Chrome e
        pode virar Reel em dobro."""
        if r.status_code == 202 or r.status_code >= 500:
            return True
        d = cls._json_ig(r.text)
        if d is None:
            return True
        if d.get("statusCode") == 202:
            return True
        t = r.text.lower()
        if any(x in t for x in ("transcode", "not finished", "processing", "try again")):
            return True
        recusa = ("feedback_required", "login_required", "checkpoint", "spam", "challenge_required")
        return not (d.get("status") == "fail" or any(x in t for x in recusa))

    def criar_destaque(self, titulo, stories):
        """Destaque do perfil com Stories (pk) já arquivados — a conta precisa de "Salvar story no arquivo" ligado
        (/accounts/settings/v2/archiving_and_downloading/). POST /api/v1/highlights/create_reel/
        (capturas/ig_destaque.jsonl). Devolve o id do destaque."""
        csrf = self.s.cookies.get("csrftoken") or ""
        r = self.s.post("https://www.instagram.com/api/v1/highlights/create_reel/", timeout=60,
                        headers=self._hd({"Content-Type": "application/x-www-form-urlencoded"}),
                        data={"cover": json.dumps({"media_id": str(stories[0])}),
                              "media_ids": json.dumps([f"{s}_{self.uid}" for s in stories]), "source": "self_profile",
                              "title": titulo, "jazoest": "2" + str(sum(ord(c) for c in csrf)), "fb_dtsg": self.dtsg})
        rid = re.search(r'"id":"(highlight:\d+)"', r.text)
        self._registrar("destaque", {"status": "ok" if rid else "fail", "media": {"pk": rid.group(1) if rid else None}},
                        {"titulo": titulo, "http": r.status_code})
        if not rid:
            raise RuntimeError(f"destaque recusado: {r.status_code} {r.text[:200]}")
        return rid.group(1)

    def editar_legenda(self, media_pk, texto):
        """Troca a legenda de um post/Reel: POST /api/v1/media/<pk>/edit_media/ com JSON (capturas/
        ig_editar_legenda.jsonl; o campo da legenda é caption_text)."""
        csrf = self.s.cookies.get("csrftoken") or ""
        vazio = json.dumps({"added": [], "in": [], "removed": []})
        r = self.s.post(f"https://www.instagram.com/api/v1/media/{media_pk}/edit_media/", timeout=60,
                        data=json.dumps({"caption_text": texto, "coauthor_invites": vazio, "usertags": vazio,
                                         "jazoest": "2" + str(sum(ord(c) for c in csrf)), "fb_dtsg": self.dtsg},
                                        ensure_ascii=False).encode(),
                        headers=self._hd({"Content-Type": "application/json"}))
        if '"caption"' not in r.text:
            raise RuntimeError(f"editar legenda recusado: {r.status_code} {r.text[:200]}")

    def comentarios(self, codigo):
        """Comentários do post (1ª página, como a página do post já traz embutido no HTML — consulta
        PolarisPostCommentsContainerQuery, capturas/ig_comentarios_ler.jsonl). Devolve (media_id, [comentários])."""
        h = self.s.get(f"https://www.instagram.com/p/{codigo}/", timeout=30).text
        mid = re.search(r'"queryID":"\d+","variables":\{"media_id":"(\d+)"', h)
        i = h.find('"xdt_api__v1__media__media_id__comments__connection":')
        out = []
        if i >= 0:
            conn, _ = json.JSONDecoder().raw_decode(h, i + len('"xdt_api__v1__media__media_id__comments__connection":'))
            for e in conn.get("edges", []):
                n = e["node"]
                out.append({"id": n["pk"], "texto": n.get("text", ""), "usuario": (n.get("user") or {}).get("username"),
                            "usuario_id": (n.get("user") or {}).get("pk"), "quando": n.get("created_at"),
                            "respostas": n.get("child_comment_count", 0)})
        return (mid.group(1) if mid else None), out

    def comentar(self, media_id, texto, responder_a=None):
        """Comenta no post (PolarisPostCommentInputRevampedMutation, capturas/ig_comentar.jsonl). responder_a =
        comentário {id, usuario} (capturas/ig_responder.jsonl: o site põe "@usuario " na frente e manda
        replied_to_comment_id como número). Devolve o id do comentário novo."""
        dados = {"comment_text": texto, "media_id": str(media_id)}
        if responder_a:
            dados["comment_text"] = f"@{responder_a['usuario']} {texto}"
            dados["replied_to_comment_id"] = int(responder_a["id"])
            conexao = ('client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__parent_comment_id__'
                       f'child_comments__connection_connection(media_id:"{media_id}",parent_comment_id:"{responder_a["id"]}")')
        else:
            conexao = ('client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection'
                       f'(data:{{}},media_id:"{media_id}",sort_order:"popular")')
        d = self.graphql("PolarisPostCommentInputRevampedMutation", {"connections": [conexao], "data": dados})
        c = ((d.get("xig_comment_create") or {}).get("comment_dict") or {})
        self._registrar("comentario", {"status": "ok" if c.get("pk") else "fail", "media": {"pk": c.get("pk")}},
                        {"media_id": media_id, "texto": texto[:80]})
        if not c.get("pk"):
            raise RuntimeError(f"comentário recusado: {str(d)[:300]}")
        return c["pk"]

    def mandar_dm(self, usuario_id, texto):
        """DM para um usuário (capturas/ig_dm.jsonl): POST /api/v1/direct_v2/create_group_thread/ (abre ou devolve a
        conversa) + mutação IGDirectTextSendMutation no thread_v2_id. Devolve o id da mensagem."""
        import random
        csrf = self.s.cookies.get("csrftoken") or ""
        r = self.s.post("https://www.instagram.com/api/v1/direct_v2/create_group_thread/", timeout=60,
                        headers=self._hd({"Content-Type": "application/x-www-form-urlencoded"}),
                        data={"recipient_users": json.dumps([str(usuario_id)]), "fb_dtsg": self.dtsg,
                              "jazoest": "2" + str(sum(ord(c) for c in csrf))})
        conversa = r.json().get("thread_v2_id")
        if not conversa:
            raise RuntimeError(f"conversa não abriu: {r.status_code} {r.text[:200]}")
        d = self.graphql("IGDirectTextSendMutation", {
            "ig_thread_igid": conversa, "offline_threading_id": str(random.randint(7 * 10 ** 18, 75 * 10 ** 17)),
            "recipient_igids": None, "replied_to_client_context": None, "replied_to_item_id": None,
            "reply_to_message_id": None, "sampled": None, "text": {"sensitive_string_value": texto},
            "mentions": [], "mentioned_user_ids": [], "commands": None, "forwarded_from_thread_id": None,
            "is_forwarded_from_own_message": None, "send_attribution": "igd_web_chat_tab:in_thread"})
        m = (d.get("xig_direct_text_send_with_slide_messaging_response") or {}).get("message_id")
        self._registrar("dm", {"status": "ok" if m else "fail", "media": {"pk": m}},
                        {"para": str(usuario_id), "texto": texto[:80]})
        if not m:
            raise RuntimeError(f"DM recusada: {str(d)[:300]}")
        return m

    def editar_perfil(self, bio=None, link=None):
        """Bio e link da bio (campanha da semana). Capturado 29/10 (capturas/ig_edit_salvar.jsonl): o site lê
        GET /api/v1/accounts/edit/web_form_data/ e salva POST /api/v1/web/accounts/edit/ com o formulário inteiro.
        jazoest = "2" + soma dos códigos do csrftoken. O Instagram recusa ✅ na bio ("marcas de verificação")."""
        fd = self.s.get("https://www.instagram.com/api/v1/accounts/edit/web_form_data/", timeout=30,
                        headers=self._hd()).json()["form_data"]
        csrf = self.s.cookies.get("csrftoken") or ""
        corpo = {"biography": fd["biography"] if bio is None else bio,
                 "chaining_enabled": "on" if fd.get("chaining_enabled") else "",
                 "external_url": (fd.get("external_url") or "") if link is None else link,
                 "first_name": fd.get("first_name") or "", "username": fd["username"],
                 "jazoest": "2" + str(sum(ord(c) for c in csrf)), "fb_dtsg": self.dtsg}
        r = self.s.post("https://www.instagram.com/api/v1/web/accounts/edit/", data=corpo, timeout=60,
                        headers=self._hd({"Referer": "https://www.instagram.com/accounts/edit/"}))
        d = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text[:300]}
        self._registrar("perfil", d, {"bio": corpo["biography"][:80], "link": corpo["external_url"], "http": r.status_code})
        if d.get("status") != "ok":
            raise RuntimeError(f"editar perfil recusado: {r.status_code} {str(d)[:300]}")
        return {"bio": corpo["biography"], "link": corpo["external_url"]}


METRICAS = ROOT / "logs" / "instagram_metricas.jsonl"


def _medir_conta(ig, conta):
    """10/11 dona ("não tem métricas dos instas; estão ganhando seguidores, curtidas?"): depois de postar, na MESMA
    sessão da conta (mesma saída/IP, sem acesso extra a outra conta), grava seguidores e views/curtidas dos últimos
    reels em logs/instagram_metricas.jsonl. Falhar aqui nunca afeta a postagem. Desligar: IG_MEDIR=0."""
    import os
    if os.environ.get("IG_MEDIR", "1") == "0":
        return
    try:
        p = ig.perfil_info()
        rs = ig.reels(quantos=12)
        rec = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "conta": conta, "seguidores": p.get("seguidores"),
               "posts": p.get("posts"),
               "views_12": sum(r.get("views") or 0 for r in rs), "curtidas_12": sum(r.get("curtidas") or 0 for r in rs),
               "comentarios_12": sum(r.get("comentarios") or 0 for r in rs),
               "reels": [{k: r.get(k) for k in ("codigo", "views", "curtidas", "quando")} for r in rs]}
        METRICAS.parent.mkdir(exist_ok=True)
        with METRICAS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"métricas {conta}: {rec['seguidores']} seguidores | 12 reels: {rec['views_12']} views, "
              f"{rec['curtidas_12']} curtidas", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"métricas {conta}: não li ({type(e).__name__})", flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 3 or sys.argv[1] not in ("story", "reel", "carrossel", "perfil"):
        raise SystemExit(__doc__.split("\n\n")[-1].strip() + "\n    python -m services.instagram.postar reel <conta> "
                         "video.mp4 \"legenda\"|@legenda.txt")
    acao, conta = sys.argv[1], sys.argv[2]
    # 29/10 (D31): sem cookie da conta neste PC e com cookie numa máquina -> roda LÁ (core/maquinas.py); os arquivos
    # (vídeo, fotos, @legenda) vão por ssh. `--local` força aqui, `--maquina x200ma` força lá.
    from core.maquinas import ou_remoto
    def _e_arquivo(a):  # legenda longa (> 255 bytes) estoura ENAMETOOLONG no Path.is_file() do Linux (visto 18:29 no x200ma)
        try:
            return len(a) < 250 and Path(a).is_file()
        except (OSError, ValueError):
            return False
    arqs = [a[1:] if a.startswith("@") else a for a in sys.argv[3:] if _e_arquivo(a[1:] if a.startswith("@") else a)]
    if ou_remoto(f"ig_{conta}", "services.instagram.postar", enviar=arqs, timeout=1200) is not None:
        return
    ig = InstagramPostar(conta)
    if acao == "story":
        print("story ok, id", ig.story(sys.argv[3]))
    elif acao == "reel":  # reel <conta> <video.mp4> "legenda"  (29/10 Fable, D21: é o que o postar_insta_auto chama)
        leg = sys.argv[4]
        if leg.startswith("@") and Path(leg[1:]).is_file():  # @arquivo: legenda em UTF-8 (o cmd do Windows estraga acento/emoji)
            leg = Path(leg[1:]).read_text("utf-8")
        print("reel ok:", f"https://www.instagram.com/reel/{ig.reel(sys.argv[3], leg)}/")
        _medir_conta(ig, conta)
    elif acao == "carrossel":
        print("carrossel ok:", f"https://www.instagram.com/p/{ig.carrossel(sys.argv[4:], sys.argv[3])}/")
    elif acao == "perfil":  # perfil <conta> [--bio "..."] [--link URL]
        a = sys.argv
        print(ig.editar_perfil(bio=a[a.index("--bio") + 1] if "--bio" in a else None,
                               link=a[a.index("--link") + 1] if "--link" in a else None))


if __name__ == "__main__":
    main()
