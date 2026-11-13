# -*- coding: utf-8 -*-
"""tests/test_offline.py — testes SEM rede, sem Chrome e sem cookies reais (30/10). Rodam em segundos:

    python -m unittest tests.test_offline -v        (na raiz do projeto; python do D:\\veo\\venv)

Cobrem as partes puras: gravação atômica, trava/merge dos cookies do cofre, argv do --maquina, empacotador do worker e
as travas de segurança do upload do YouTube (nunca público fora de hora, nunca 2º vídeo por erro na etapa final).
"""
import itertools
import json
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


class TestArquivo(unittest.TestCase):
    def test_gravar_json_atomico_e_sem_sobras(self):
        from core.arquivo import gravar_json
        with tempfile.TemporaryDirectory() as d:
            alvo = Path(d) / "x.json"
            gravar_json(alvo, {"a": "ç"})
            gravar_json(alvo, {"a": 2})
            self.assertEqual(json.loads(alvo.read_text("utf-8")), {"a": 2})
            self.assertEqual([p.name for p in Path(d).iterdir()], ["x.json"])  # nenhum .tmp esquecido

    def test_gravacoes_concorrentes_nunca_deixam_json_quebrado(self):
        from core.arquivo import gravar_json
        with tempfile.TemporaryDirectory() as d:
            alvo = Path(d) / "c.json"
            gravar_json(alvo, {"n": 0})
            erros, parar = [], threading.Event()

            def leitor():
                while not parar.is_set():
                    try:
                        json.loads(alvo.read_text("utf-8"))
                    except PermissionError:
                        pass  # Windows: leitura no instante do replace — o ler() do cofre repete
                    except ValueError as ex:
                        erros.append(ex)
            t = threading.Thread(target=leitor)
            t.start()
            for i in range(200):
                gravar_json(alvo, {"n": i, "lixo": "x" * 5000})
            parar.set()
            t.join()
            self.assertEqual(erros, [])


class TestCofreCookies(unittest.TestCase):
    def setUp(self):
        import core.cofre_cookies as cc
        self.cc = cc
        self.tmp = tempfile.TemporaryDirectory()
        self.dir_orig = cc.DIR
        cc.DIR = Path(self.tmp.name)

    def tearDown(self):
        self.cc.DIR = self.dir_orig
        self.tmp.cleanup()

    def _semear(self, cookies):
        self.cc._gravar("p", {"perfil": "p", "ua": "UA-teste", "cookies": cookies})

    def test_salvar_so_grava_o_que_o_servidor_mudou(self):
        cc = self.cc
        self._semear([{"name": "A", "value": "1", "domain": ".x.com", "path": "/"},
                      {"name": "B", "value": "1", "domain": ".x.com", "path": "/"}])
        s = cc.sessao("p", ["x.com"])
        # outro processo girou o B enquanto esta sessão rodava
        d = cc.ler("p")
        d["cookies"][1]["value"] = "girado-por-outro"
        cc._gravar("p", d)
        s.cookies.set("A", "novo-do-servidor", domain=".x.com", path="/")  # Set-Cookie nesta sessão
        cc.salvar(s)
        val = {c["name"]: c["value"] for c in cc.ler("p")["cookies"]}
        self.assertEqual(val, {"A": "novo-do-servidor", "B": "girado-por-outro"})

    def test_salvar_cookie_novo_entra(self):
        cc = self.cc
        self._semear([{"name": "A", "value": "1", "domain": ".x.com", "path": "/"}])
        s = cc.sessao("p", ["x.com"])
        s.cookies.set("N", "v", domain=".x.com", path="/")
        cc.salvar(s)
        self.assertIn("N", {c["name"] for c in cc.ler("p")["cookies"]})

    def test_salvar_sem_arquivo_nao_inventa(self):
        cc = self.cc
        self._semear([{"name": "A", "value": "1", "domain": ".x.com", "path": "/"}])
        s = cc.sessao("p", ["x.com"])
        cc._arq("p").unlink()
        s.cookies.set("A", "2", domain=".x.com", path="/")
        cc.salvar(s)
        self.assertFalse(cc._arq("p").exists())

    def test_trava_velha_e_tomada(self):
        cc = self.cc
        lk = cc.DIR / "cofre_p.lock"
        lk.write_text("")
        import os
        velho = time.time() - 120
        os.utime(lk, (velho, velho))
        t0 = time.time()
        with cc._trava("p"):
            pass
        self.assertLess(time.time() - t0, 2)
        self.assertFalse(lk.exists())


class TestMaquinasArgv(unittest.TestCase):
    def test_local_forcado(self):
        from core.maquinas import ou_remoto
        self.assertIsNone(ou_remoto("ig_x", "m", argv=["reel", "--local"]))

    def test_maquina_sem_nome(self):
        from core.maquinas import ou_remoto
        with self.assertRaises(SystemExit):
            ou_remoto("ig_x", "m", argv=["reel", "--maquina"])
        with self.assertRaises(SystemExit):
            ou_remoto("ig_x", "m", argv=["reel", "--maquina", "--local2"])


class TestEmpacotador(unittest.TestCase):
    def test_pacote_completo(self):
        import empacotar_worker as e
        self.assertEqual(e.imports_faltando(), [])

    def test_detecta_import_faltando(self):
        import empacotar_worker as e
        with mock.patch.object(e, "ARQUIVOS", [a for a in e.ARQUIVOS if a != "core/arquivo.py"]):
            self.assertTrue(any("core/arquivo.py" in x for x in e.imports_faltando()))


def _enviador_falso(videos_lidos, falhar_final=False):
    """Enviador com a rede trocada por respostas prontas."""
    sys.modules.setdefault("youtube_http", types.SimpleNamespace(
        sincronizar=lambda s: None, Studio=object, COOKIES_DIR=Path(tempfile.gettempdir()),
        STUDIO="https://studio.youtube.com", _email=lambda s: s))
    from services.youtube import upload_http as up
    e = up.Enviador.__new__(up.Enviador)
    e.slug, e.token = "teste", "tok"
    chamadas = []
    leituras = iter(videos_lidos)

    def _metadados(vid, **campos):
        chamadas.append(campos)
        if falhar_final and "scheduledPublishing" in campos:
            raise RuntimeError("video_manager/metadata_update: HTTP 503")
    e._metadados = _metadados
    e.st = types.SimpleNamespace(videos=lambda n: [next(leituras)])
    return up, e, chamadas


class TestUploadSeguranca(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch("time.sleep")
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_sem_horario_recusa_antes_de_enviar(self):
        up, e, _ = _enviador_falso([])
        with self.assertRaises(RuntimeError):
            e.enviar("nao_existe.mp4", "t")  # nem tenta abrir o arquivo

    def test_horario_passado_recusa_antes_de_enviar(self):
        up, e, _ = _enviador_falso([])
        with self.assertRaisesRegex(RuntimeError, "já passou"):
            e.enviar("nao_existe.mp4", "t", agendar=int(time.time()) + 60)

    def test_agendado_confere_e_devolve(self):
        alvo = int(time.time()) + 3600
        up, e, ch = _enviador_falso([{"id": "V", "privacidade": "private", "agendado_para": alvo}])
        self.assertEqual(e._completar("V", "", [], alvo, False, None, None, None), "V")
        self.assertEqual(ch[-1]["scheduledPublishing"]["set"]["timeSec"], str(alvo))

    def test_erro_na_etapa_final_mas_servidor_gravou_nao_duplica(self):
        alvo = int(time.time()) + 3600
        ok = {"id": "V", "privacidade": "private", "agendado_para": alvo}
        up, e, _ = _enviador_falso([ok, ok], falhar_final=True)
        self.assertEqual(e._completar("V", "", [], alvo, False, None, None, None), "V")

    def test_erro_na_etapa_final_e_servidor_nao_gravou_falha(self):
        alvo = int(time.time()) + 3600
        up, e, _ = _enviador_falso([{"id": "V", "privacidade": "private", "agendado_para": None}], falhar_final=True)
        with self.assertRaises(RuntimeError):
            e._completar("V", "", [], alvo, False, None, None, None)

    def test_publico_sem_agenda_volta_para_privado(self):
        alvo = int(time.time()) + 3600
        pub = {"id": "V", "privacidade": "public", "agendado_para": None}
        up, e, ch = _enviador_falso([pub, pub, pub])
        with self.assertRaisesRegex(RuntimeError, "PÚBLICO"):
            e._completar("V", "", [], alvo, False, None, None, None)
        self.assertEqual(ch[-1].get("privacyState"), {"newPrivacy": "PRIVATE"})

    def test_agenda_aparece_na_2a_leitura(self):
        alvo = int(time.time()) + 3600
        up, e, _ = _enviador_falso([{"id": "V", "privacidade": "private", "agendado_para": None},
                                    {"id": "V", "privacidade": "private", "agendado_para": alvo}])
        self.assertEqual(e._completar("V", "", [], alvo, False, None, None, None), "V")

    def test_sem_conseguir_reler_confia_no_update(self):
        alvo = int(time.time()) + 3600
        up, e, _ = _enviador_falso([])
        e.st = types.SimpleNamespace(videos=mock.Mock(side_effect=RuntimeError("rede")))
        self.assertEqual(e._completar("V", "", [], alvo, False, None, None, None), "V")

    def test_rascunho_aparece_no_log_cortado(self):
        """30/10 forjareact/cenareact: 403 indentado do metadata_update depois do createvideo; o postador corta a
        mensagem em 300 caracteres e o id do rascunho que ficou no canal precisa sobrar nesse pedaço."""
        up, e, _ = _enviador_falso([])
        del e._metadados  # usa o _metadados de verdade (ele chama o _yt com a sessão falsa)
        erro_403 = json.dumps({"error": {"code": 403, "message": "The caller does not have permission",
                                         "errors": [{"message": "The caller does not have permission",
                                                     "domain": "global", "reason": "forbidden"}],
                                         "status": "PERMISSION_DENIED"}}, indent=2)

        def post(url, **kw):
            if "upload.youtube.com" in url:
                return types.SimpleNamespace(headers={"X-Goog-Upload-URL": "U"}, status_code=200, text="")
            if url == "U":
                return types.SimpleNamespace(json=lambda: {"scottyResourceId": "S"}, status_code=200, text="")
            if "createvideo" in url:
                return types.SimpleNamespace(json=lambda: {"videoId": "RASC1"}, status_code=200, text="")
            return types.SimpleNamespace(status_code=403, text=erro_403)
        e.st = types.SimpleNamespace(s=types.SimpleNamespace(post=post, cookies={"SAPISID": "x"}),
                                     channel_id="C", versao="1")
        with tempfile.TemporaryDirectory() as d:
            v = Path(d) / "v.mp4"
            v.write_bytes(b"0" * 10)
            with self.assertRaises(RuntimeError) as cm:
                e.enviar(str(v), "t", agendar=int(time.time()) + 3600)
        cortado = str(cm.exception)[:300]  # o mesmo corte do youtube_web_poster._subir_http
        self.assertIn("rascunho privado RASC1 ficou no canal", cortado)
        self.assertIn("HTTP 403", cortado)
        self.assertNotIn("\n", str(cm.exception))


class TestInstagramReelResposta(unittest.TestCase):
    """Formatos reais de configure_to_clips (capturas/ig_reel.jsonl, 29/10)."""
    def _r(self, texto, status=200):
        return types.SimpleNamespace(text=texto, status_code=status)

    def setUp(self):
        from services.instagram.postar import InstagramPostar
        self.P = InstagramPostar

    def test_processando_202_no_corpo(self):
        r = self._r('for (;;);{"__ar":1,"rid":"x","payload":{"statusCode":202},"lid":"1"}')
        self.assertIsNone(self.P._codigo_reel(r))
        self.assertTrue(self.P._reel_processando(r))

    def test_sucesso_embrulhado(self):
        r = self._r('for (;;);{"__ar":1,"payload":{"media":{"pk":"4018","code":"DfE3C7QzC5a","media_type":2}}}')
        self.assertEqual(self.P._codigo_reel(r), "DfE3C7QzC5a")

    def test_sucesso_json_puro(self):
        self.assertEqual(self.P._codigo_reel(self._r('{"media":{"code":"ABC"},"status":"ok"}')), "ABC")

    def test_recusa_para_de_repetir(self):
        r = self._r('{"message":"feedback_required","spam":true,"status":"fail"}', 400)
        self.assertIsNone(self.P._codigo_reel(r))
        self.assertFalse(self.P._reel_processando(r))

    def test_code_de_erro_nao_conta_como_postado(self):
        r = self._r('{"status":"fail","error":{"code":"IG_ERR"}}', 400)
        self.assertIsNone(self.P._codigo_reel(r))

    def test_resposta_estranha_continua_esperando(self):
        self.assertTrue(self.P._reel_processando(self._r("<html>oops</html>")))


class TestQuero(unittest.TestCase):
    def test_dm_uma_vez_por_dia(self):
        import quero
        hoje = time.strftime("%Y-%m-%d %H:%M")
        feitos = {"1": {"usuario": "ana", "dm": "mid.x", "quando": hoje},
                  "2": {"usuario": "bia", "dm_erro": "convite", "quando": hoje},
                  "3": {"usuario": "cris", "dm": "mid.y", "quando": "2026-01-01 10:00"}}
        self.assertTrue(quero._dm_hoje(feitos, "ana"))
        self.assertFalse(quero._dm_hoje(feitos, "bia"))   # DM falhou: pode tentar de novo
        self.assertFalse(quero._dm_hoje(feitos, "cris"))  # foi em outro dia

    def test_bloqueio(self):
        import quero
        self.assertTrue(quero._bloqueado("comentário recusado: {'message': 'feedback_required', 'spam': True}"))
        self.assertFalse(quero._bloqueado("DM recusada: convite pendente"))


class TestTikTokVideos(unittest.TestCase):
    def test_has_more_sem_itens_nao_trava(self):
        from services.tiktok import studio
        t = studio.TikTokStudio.__new__(studio.TikTokStudio)
        t.csrf, t.arroba = "", "x"
        resp = types.SimpleNamespace(status_code=200, text="", json=lambda: {"item_list": [], "has_more": True, "cursor": 0})
        t.s = types.SimpleNamespace(post=mock.Mock(return_value=resp))
        self.assertEqual(t.videos(200), [])
        self.assertEqual(t.s.post.call_count, 1)

    def test_pagina(self):
        from services.tiktok import studio
        t = studio.TikTokStudio.__new__(studio.TikTokStudio)
        t.csrf, t.arroba = "", "x"
        paginas = iter([{"item_list": [{"item_id": "1"}], "has_more": True, "cursor": 50},
                        {"item_list": [{"item_id": "2"}], "has_more": False}])
        t.s = types.SimpleNamespace(post=lambda *a, **k: types.SimpleNamespace(
            status_code=200, text="", json=lambda d=next(paginas): d))
        self.assertEqual([v["id"] for v in t.videos(200)], ["1", "2"])


class TestSeguirBloqueio(unittest.TestCase):
    def _r(self, status, corpo):
        txt = corpo if isinstance(corpo, str) else json.dumps(corpo)

        def _json():
            return json.loads(txt)
        return types.SimpleNamespace(status_code=status, text=txt, json=_json)

    def test_usuario_com_spam_no_nome_nao_pausa(self):
        from services.instagram.seguir import Seguidor
        r = self._r(200, {"users": [{"username": "spam_challenge_br"}], "status": "ok"})
        self.assertEqual(Seguidor._checar(None, r)["users"][0]["username"], "spam_challenge_br")

    def test_feedback_required_pausa(self):
        from services.instagram.seguir import Bloqueio, Seguidor
        with self.assertRaises(Bloqueio):
            Seguidor._checar(None, self._r(400, {"message": "feedback_required", "status": "fail"}))

    def test_html_nao_e_bloqueio(self):
        from services.instagram.seguir import Bloqueio, Seguidor
        with self.assertRaises(RuntimeError) as cm:
            Seguidor._checar(None, self._r(200, "<html>login</html>"))
        self.assertNotIsInstance(cm.exception, Bloqueio)


class TestCdpAba(unittest.TestCase):
    """A aba fica minutos em silêncio (Flow gerando por HTTP): o timeout do recv não pode matar a leitura."""
    def _aba(self, recebidos):
        import queue
        import websocket
        from core.cdp_aba import Aba
        fila, enviados = queue.Queue(), []
        for x in recebidos:
            fila.put(x)

        class WS:
            def send(self, m):
                enviados.append(json.loads(m))
                fila.put(json.dumps({"id": enviados[-1]["id"], "result": {"ok": True}}))

            def recv(self):
                x = fila.get()
                if x == "TIMEOUT":
                    raise websocket.WebSocketTimeoutException("timed out")
                if x == "FIM":
                    raise ConnectionError("fechou")
                return x

            def close(self):
                pass
        a = Aba.__new__(Aba)
        a.ws, a._id, a._resp, a._ouvintes = WS(), itertools.count(1), {}, {}
        a._cond, a._envio = threading.Condition(), threading.Lock()
        threading.Thread(target=a._ler, daemon=True).start()
        return a, fila

    def test_silencio_nao_mata_a_leitura(self):
        a, _ = self._aba(["TIMEOUT", "TIMEOUT", "TIMEOUT"])
        time.sleep(0.2)
        self.assertEqual(a.chamar("Runtime.evaluate", timeout=5), {"ok": True})

    def test_aba_fechada_avisa(self):
        a, fila = self._aba([])
        fila.put("FIM")
        time.sleep(0.2)
        with self.assertRaisesRegex(TimeoutError, "fechou"):
            a.chamar("X", timeout=2)


class TestFlowFluxo(unittest.TestCase):
    def test_linha_cortada_nao_perde_a_midia(self):
        from services.veo_flow.flow_gerar import ler_fluxo
        ferr = [["generate_image", "generate_image",
                 [[["status", [None, None, "success"]], ["media_id", [None, None, "11d3c05c-bcba-45c1-b7bb-d6a605880cc5"]]]]]]
        boa = json.dumps([["wrb.fr", None, json.dumps(ferr)]])
        txt = boa + "\n" + '[["wrb.fr",null,"[[\\"cortad'  # stream cortado no fim
        r = ler_fluxo(txt)
        self.assertEqual(r["ferramentas"][0]["media_id"], "11d3c05c-bcba-45c1-b7bb-d6a605880cc5")
        self.assertIsNone(r["recusa"])

    def test_recusa(self):
        from services.veo_flow.flow_gerar import ler_fluxo
        txt = json.dumps([["wrb.fr", None, None, None, None, [8, None, "PUBLIC_ERROR_UNUSUAL_ACTIVITY"]]])
        self.assertIn("UNUSUAL", ler_fluxo(txt)["recusa"])


VENV = Path(r"D:\veo\venv\Scripts\python.exe")


def _python_certo():
    """O projeto roda no python do D:\\veo\\venv (curl_cffi, websocket-client, Pillow). Rodado com outro python sem
    essas bibliotecas (ex.: o `python` padrão do PC), relança com o do venv em vez de dar ModuleNotFoundError."""
    try:
        import websocket  # noqa: F401
        import requests  # noqa: F401
        return True
    except ImportError:
        return False


class TestCapturaTokenCanalCerto(unittest.TestCase):
    """capturar_passivo: o token vai pro yt_sessao do canal do documentURL do PEDIDO, não da aba (que atrasa ~2 s).
    01/11: a mesma aba do Studio troca de canal e o token novo chegava antes de self.alvo['url'] atualizar."""
    def test_token_usa_documenturl_do_pedido(self):
        import capturar_passivo as cp
        corpo = json.dumps({"context": {"request": {"sessionInfo": {"token": "TOK_B"}}}})
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "cookies").mkdir()
            with mock.patch.object(cp, "ROOT", Path(d)), \
                 mock.patch.object(cp, "CANAIS", {"UCaaaaaaaaaaaaaaaaaaaaaa": "canal_a",
                                                  "UCbbbbbbbbbbbbbbbbbbbbbb": "canal_b"}):
                o = cp.Ouvinte.__new__(cp.Ouvinte)
                o.alvo = {"url": "https://studio.youtube.com/channel/UCaaaaaaaaaaaaaaaaaaaaaa/videos"}  # aba defasada (A)
                # o pedido real veio do frame do canal B:
                o._token_sessao(corpo, "https://studio.youtube.com/channel/UCbbbbbbbbbbbbbbbbbbbbbb/videos/upload")
                b = Path(d) / "cookies" / "yt_sessao_canal_b.json"
                a = Path(d) / "cookies" / "yt_sessao_canal_a.json"
                self.assertTrue(b.exists(), "token devia ir pro canal do documentURL (B)")
                self.assertFalse(a.exists(), "não pode gravar no canal da aba defasada (A)")
                self.assertEqual(json.loads(b.read_text("utf-8"))["token"], "TOK_B")


if __name__ == "__main__":
    if not _python_certo() and VENV.exists() and Path(sys.executable).resolve() != VENV.resolve():
        import subprocess
        print(f"(este python não tem as bibliotecas do projeto; rodando com {VENV})", flush=True)
        sys.exit(subprocess.call([str(VENV), "-X", "utf8", __file__, *sys.argv[1:]], cwd=str(ROOT)))
    unittest.main()
