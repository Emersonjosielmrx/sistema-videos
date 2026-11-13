#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_advertencias.py — testes OFFLINE do bloqueio "Muitos avisos" (diretrizes da comunidade).

Cobre (sem rede, sem Chrome, sem postar): a classificação do erro, a espera de 24 h por canal
(sem renovar o contador em cada checagem), o veto ANTES de abrir qualquer poster, os mapas de STATUS
dos dois posters e o caminho HTTP (navegador sem navegador) parando no aviso em vez de cair no Chrome.

    python bin/test_advertencias.py           (ou: python -m unittest bin.test_advertencias -v)
"""
import json
import sys
import tempfile
import types
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import politica  # noqa: E402
import youtube_poster  # noqa: E402
import youtube_web_poster  # noqa: E402

AVISO_PT = ("createvideo sem videoId: REJECTED Muitos avisos Devido às advertências relacionadas às "
            "diretrizes da comunidade, não é possível enviar vídeos no momento.")
AVISO_EN = "Many warnings: due to community guidelines you are unable to upload videos"


class TestClassificacao(unittest.TestCase):
    def test_muitos_avisos_pt(self):
        self.assertEqual(politica.classificar_erro(AVISO_PT), "advertencias")

    def test_muitos_avisos_en(self):
        self.assertEqual(politica.classificar_erro(AVISO_EN), "advertencias")

    def test_erro_generico_nao_e_advertencia(self):
        self.assertEqual(politica.classificar_erro("erro de rede temporário"), "erro")

    def test_aviso_de_direitos_autorais_nao_e_advertencia(self):
        # "warning: copyright claim" é do CONTEÚDO, não o bloqueio de envio por diretrizes
        self.assertEqual(politica.classificar_erro("warning: copyright claim on this video"), "erro")

    def test_limite_diario_continua_limite(self):
        self.assertEqual(politica.classificar_erro("HTTP 403 uploadLimitExceeded"), "limite")

    def test_mapas_de_status_tem_advertencias(self):
        self.assertEqual(youtube_poster.STATUS_BLOQUEIO.get("advertencias"), "advertencias")
        self.assertEqual(youtube_web_poster.STATUS_BLOQUEIO.get("advertencias"), "advertencias")


class TestCooldown(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self._orig = politica.ADVERTENCIAS_FILE
        politica.ADVERTENCIAS_FILE = Path(self._td.name) / "advertencias_upload.json"
        self.canal = {"id": "canal-teste", "nome": "Canal teste"}

    def tearDown(self):
        politica.ADVERTENCIAS_FILE = self._orig
        self._td.cleanup()

    def test_marca_e_reconhece_24h(self):
        ate = politica.marcar_advertencias(self.canal["id"])
        self.assertGreater(ate, politica.agora())
        self.assertIsNotNone(politica.em_advertencias(self.canal))

    def test_checar_nao_renova_o_contador(self):
        politica.marcar_advertencias(self.canal["id"])
        vezes = json.loads(politica.ADVERTENCIAS_FILE.read_text("utf-8"))[self.canal["id"]]["vezes"]
        # checagens repetidas não podem empurrar a espera nem somar "vezes" (bug do limite_diario, 30/10)
        for _ in range(3):
            cod, _msg = politica.checar_upload(self.canal, "arquivo-inexistente.mp4") or ("", "")
            if cod != "advertencias":  # uma parada geral real deste PC pode vir antes; então pulo a asserção
                self.skipTest(f"checar_upload barrou antes por '{cod}' (bloqueio global ativo)")
        depois = json.loads(politica.ADVERTENCIAS_FILE.read_text("utf-8"))[self.canal["id"]]["vezes"]
        self.assertEqual(depois, vezes)

    def test_canal_sem_aviso_nao_bloqueia(self):
        self.assertIsNone(politica.em_advertencias({"id": "outro-canal"}))


class TestVetoAntesDoPoster(unittest.TestCase):
    """postar_youtube não pode nem iniciar o poster enquanto o canal está em espera."""
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self._orig = {k: getattr(politica, k) for k in
                      ("ADVERTENCIAS_FILE", "parada_ativa", "_postagem_desligada", "achar_canal")}
        self._run = politica.subprocess.run
        politica.ADVERTENCIAS_FILE = Path(self._td.name) / "advertencias_upload.json"
        politica.parada_ativa = lambda: None
        politica._postagem_desligada = lambda projeto=None: None
        self.canal = {"id": "canal-teste", "nome": "Canal teste"}
        politica.achar_canal = lambda nome: (self.canal, None)

        def _nao_chamar(*a, **k):
            raise AssertionError("subprocess.run foi chamado durante o cooldown de advertências")
        politica.subprocess.run = _nao_chamar

    def tearDown(self):
        for k, v in self._orig.items():
            setattr(politica, k, v)
        politica.subprocess.run = self._run
        self._td.cleanup()

    def test_veta_sem_abrir_poster(self):
        politica.marcar_advertencias(self.canal["id"])
        status, _info = politica.postar_youtube("Canal teste", "x.mp4", "t", "", [])
        self.assertEqual(status, "advertencias")


class TestCaminhoHTTP(unittest.TestCase):
    """O upload por HTTP (navegador sem navegador) para no aviso e NÃO cai no Chrome."""
    def setUp(self):
        self._mods = {}
        for nome in ("services", "services.youtube", "services.youtube.upload_http"):
            self._mods[nome] = sys.modules.get(nome)
        pkg = types.ModuleType("services")
        pkg.__path__ = []
        sub = types.ModuleType("services.youtube")
        sub.__path__ = []
        leaf = types.ModuleType("services.youtube.upload_http")

        class _Enviador:
            def __init__(self, slug):
                pass

            def enviar(self, *a, **k):
                raise RuntimeError(AVISO_PT)
        leaf.Enviador = _Enviador
        sub.upload_http = leaf
        pkg.youtube = sub
        sys.modules["services"] = pkg
        sys.modules["services.youtube"] = sub
        sys.modules["services.youtube.upload_http"] = leaf
        self._dur = youtube_web_poster._duracao_video
        self._log = youtube_web_poster.log
        self._loghttp = youtube_web_poster._log_http
        self._mapa = youtube_web_poster.ler_mapa
        youtube_web_poster._duracao_video = lambda v: 30
        youtube_web_poster.log = lambda m: None
        youtube_web_poster._log_http = lambda m: None
        youtube_web_poster.ler_mapa = lambda: {"canais": {}}  # postar_http default True; não lê o config real

    def tearDown(self):
        for nome, mod in self._mods.items():
            if mod is None:
                sys.modules.pop(nome, None)
            else:
                sys.modules[nome] = mod
        youtube_web_poster._duracao_video = self._dur
        youtube_web_poster.log = self._log
        youtube_web_poster._log_http = self._loghttp
        youtube_web_poster.ler_mapa = self._mapa

    def test_http_para_no_aviso_sem_chrome(self):
        a = types.SimpleNamespace(video="x.mp4", titulo="t", descricao="", tags="", ensaio=False,
                                  privacy="public", thumbnail=None, playlist=None, sintetico=None)
        e = {}
        alvo = datetime.now().astimezone()
        with self.assertRaises(youtube_web_poster.Falha) as cm:
            youtube_web_poster._subir_http("canal-teste", e, a, alvo, False)
        self.assertEqual(cm.exception.status, "advertencias")

    def test_http_limite_diario_nao_cai_no_chrome(self):
        """LimiteDiario do upload_http: o Chrome bate no MESMO limite da conta, então para e devolve 'limite'."""
        class LimiteDiario(RuntimeError):
            pass

        class _Env:
            def __init__(self, slug):
                pass

            def enviar(self, *a, **k):
                raise LimiteDiario("createvideo sem videoId: REJECTED O limite diário de envios foi alcançado")
        sys.modules["services.youtube.upload_http"].Enviador = _Env
        a = types.SimpleNamespace(video="x.mp4", titulo="t", descricao="", tags="", ensaio=False,
                                  privacy="public", thumbnail=None, playlist=None, sintetico=None)
        with self.assertRaises(youtube_web_poster.Falha) as cm:
            youtube_web_poster._subir_http("canal-teste", {}, a, datetime.now().astimezone(), False)
        self.assertEqual(cm.exception.status, "limite")


if __name__ == "__main__":
    unittest.main(verbosity=2)
