# -*- coding: utf-8 -*-
r"""teste_camada_opus.py — testes do JUIZ Opus (camada_opus.py) contra um servidor SSE falso em 127.0.0.1 (24/10).

Nada aqui chama modelo de verdade nem lê a chave real: PASTA, DESLIGADA, LOCK e PROXY vão pra uma pasta temporária
(com uma chave falsa) e o estado real (estado\opus, estado\opus_camada_DESLIGADA) não é tocado. Leva uns 30 s.

    D:\veo\venv\Scripts\python.exe D:\video-fila\testes\teste_camada_opus.py
"""
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ))
import camada_opus as co  # noqa: E402

REAIS = (co.PASTA, co.DESLIGADA, co.LOCK, co.PROXY)
CHAVE_FALSA = "<SEGREDO_REMOVIDO>"
SEM_JANELA = 0x08000000

# roda o camada_opus.main() num processo à parte, com as pastas trocadas pela temporária (env CAMADA_OPUS_TESTE)
EMBRULHO = r'''
import os, sys, time
sys.path.insert(0, {raiz!r})
import camada_opus as co
from pathlib import Path
d = Path(os.environ["CAMADA_OPUS_TESTE"])
co.PASTA = d / "opus"
co.DESLIGADA = d / "opus_camada_DESLIGADA"
co.LOCK = co.PASTA / "camada.lock"
co.PROXY = d / "claude_proxy.json"
if os.environ.get("CAMADA_OPUS_TRAVAR"):  # a chamada nunca volta: só o relógio de segurança salva
    co.FOLGA_TIMER_S = 1
    class _Parado:
        def open(self, *a, **k):
            time.sleep(60)
    co._ABRIDOR = _Parado()
if os.environ.get("CAMADA_OPUS_SEM_STDOUT"):  # igual ao pythonw
    sys.stdout = None
    sys.stderr = None
sys.exit(co.main(sys.argv[1:]))
'''


# ─── servidor SSE falso ──────────────────────────────────────────────────────
def _sse(tipo, obj):
    obj = dict(obj, type=tipo)
    return f"event: {tipo}\ndata: {json.dumps(obj, ensure_ascii=False)}\n\n".encode("utf-8")


def _inicio(modelo="claude-opus-4-6-thinking", ent=1234):
    return _sse("message_start", {"message": {"id": "msg_teste", "type": "message", "role": "assistant",
                                              "model": modelo, "content": [], "stop_reason": None,
                                              "usage": {"input_tokens": ent, "output_tokens": 1}}})


def _texto(t):
    return _sse("content_block_delta", {"index": 1, "delta": {"type": "text_delta", "text": t}})


def _pensar(t):
    return _sse("content_block_delta", {"index": 0, "delta": {"type": "thinking_delta", "thinking": t}})


def _fim(saida=321):
    return (_sse("message_delta", {"delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": saida}})
            + _sse("message_stop", {}))


PING = _sse("ping", {})


def bloco(job, veredito="MANTER"):
    d = {"job": job, "veredito": veredito, "por_que": "teste com acentuação", "prova": "log 24/10 10:00",
         "confianca": 4}
    return "\nTexto antes.\n<<<AUDITORIA " + json.dumps(d, ensure_ascii=False) + " AUDITORIA>>>\n"


class Falso(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("content-length") or 0)
        corpo = json.loads(self.rfile.read(n) or b"{}")
        cen = self.path.strip("/").split("/")[0]
        self.server.pedidos.append({"cenario": cen, "corpo": corpo, "headers": {k.lower(): v for k, v in
                                                                                 self.headers.items()}})
        try:
            getattr(self, "c_" + cen)(corpo)
        except OSError:
            pass  # o cliente fechou (é o que se espera em vários cenários)

    def _abrir(self, status=200, tipo="text/event-stream"):
        self.send_response(status)
        self.send_header("content-type", tipo)
        self.send_header("transfer-encoding", "chunked")
        self.send_header("connection", "close")
        self.end_headers()

    def _env(self, b):
        self.wfile.write(f"{len(b):X}\r\n".encode() + b + b"\r\n")
        self.wfile.flush()

    def _acabar(self):
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def _json(self, status, obj):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(b)))
        self.send_header("connection", "close")
        self.end_headers()
        self.wfile.write(b)
        self.wfile.flush()

    # cenários (o caminho da base_url escolhe)
    def c_normal(self, corpo):
        self._abrir()
        self._env(_inicio())
        self._env(PING)
        self._env(_pensar("deixa eu ver"))
        self._env(_pensar(" o diff..."))
        texto = bloco("j1") + bloco("j2", "DESFAZER") + bloco("j3", "DONA")
        for i in range(0, len(texto), 7):  # blocos picados em pedaços pequenos
            self._env(_texto(texto[i:i + 7]))
        self._env(_fim())
        self._acabar()

    def c_sembyte(self, corpo):
        time.sleep(4)

    def c_silencio(self, corpo):
        self._abrir()
        self._env(_inicio())
        self._env(_texto(bloco("j1")))
        self._env(_texto(bloco("j2")[:30]))
        time.sleep(0.6)  # o .txt tem de ter o bloco 1 já gravado (ao vivo)
        try:
            self.server.estado["txt_no_meio"] = (self.server.estado["pasta"] / "silencio.txt").read_text(
                encoding="utf-8")
        except OSError as e:
            self.server.estado["txt_no_meio"] = f"ERRO {e}"
        time.sleep(4)

    def c_pings(self, corpo):
        self._abrir()
        self._env(_inicio())
        fim = time.time() + 20
        while time.time() < fim:
            self._env(PING)
            time.sleep(0.3)

    def c_429(self, corpo):
        self._json(429, {"type": "error", "error": {"type": "rate_limit_error",
                                                    "message": f"sem cota: x-api-key={CHAVE_FALSA} Bearer "
                                                               f"{CHAVE_FALSA}"}})

    def c_400(self, corpo):
        if corpo.get("stream"):
            self._json(400, {"type": "error", "error": {"type": "invalid_request_error",
                                                        "message": "stream não suportado"}})
            return
        self._json(200, {"id": "msg_x", "type": "message", "role": "assistant", "model": "claude-opus-4-6-thinking",
                         "content": [{"type": "thinking", "thinking": "hmm"},
                                     {"type": "text", "text": bloco("a") + bloco("b", "REFAZER")}],
                         "stop_reason": "end_turn", "usage": {"input_tokens": 50, "output_tokens": 60}})

    def c_modelo(self, corpo):
        self._abrir()
        self._env(_inicio(modelo="kr/claude-sonnet-4.5"))
        self._env(_texto(bloco("j1")))
        self._env(_fim())
        self._acabar()

    def c_botao(self, corpo):
        self._abrir()
        self._env(_inicio())
        self._env(_texto(bloco("j1")))
        time.sleep(0.3)
        self.server.estado["desligada"].write_text("teste botão\n", encoding="utf-8")
        time.sleep(0.3)
        self._env(PING)
        time.sleep(0.3)
        self._env(_texto(bloco("j2")))
        self._env(_fim())
        self._acabar()

    def c_erro(self, corpo):
        self._abrir()
        self._env(_inicio())
        self._env(_texto(bloco("j1")))
        self._env(_sse("error", {"error": {"type": "overloaded_error", "message": "Overloaded"}}))
        self._acabar()

    def c_corte(self, corpo):
        self._abrir()
        self._env(_inicio())
        self._env(_texto(bloco("j1")))
        self._acabar()


class Servidor(http.server.ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False

    def handle_error(self, request, client_address):
        pass


# ─── testes ──────────────────────────────────────────────────────────────────
class TesteCamadaOpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = Servidor(("127.0.0.1", 0), Falso)
        cls.srv.pedidos, cls.srv.estado = [], {}
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="teste_camada_opus_"))
        co.PASTA = self.tmp / "opus"
        co.DESLIGADA = self.tmp / "opus_camada_DESLIGADA"
        co.LOCK = co.PASTA / "camada.lock"
        co.PROXY = self.tmp / "claude_proxy.json"
        co.PROXY.write_text(json.dumps({"auth_token": CHAVE_FALSA}), encoding="utf-8")
        co._SEGREDOS.clear()
        self.assertNotEqual(co.PASTA, REAIS[0])
        self.srv.pedidos.clear()
        self.srv.estado.clear()
        self.srv.estado.update(pasta=co.PASTA, desligada=co.DESLIGADA)

    def tearDown(self):
        co.PASTA, co.DESLIGADA, co.LOCK, co.PROXY = REAIS
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ajudantes
    def pedido(self, lid, cenario, **mais):
        co.PASTA.mkdir(parents=True, exist_ok=True)
        dos = co.PASTA / f"{lid}_dossie.md"
        dos.write_text("# Dossiê de teste\nAGORA: 24/10/2026 10:05 em Brasília (UTC-3) = 13:05 UTC\n", encoding="utf-8")
        p = {"id": lid, "modelo": "antigravity/claude-opus-4-6-thinking", "base_url": f"{self.url}/{cenario}",
             "system": "Você é o juiz final.", "dossie": str(dos), "max_tokens": 2000, "primeiro_byte_s": 2,
             "tempo_max_min": 0.5, "jobs": ["j1", "j2", "j3"], "exigir_modelo": "opus-4-6", "respeitar_botao": True}
        p.update(mais)
        co._gravar_json(co.PASTA / f"{lid}_pedido.json", p)
        return p

    def conferir_arquivos(self, lid, r):
        disco = json.loads((co.PASTA / f"{lid}.json").read_text(encoding="utf-8"))
        self.assertEqual(disco, r)
        for k in ("id", "status", "vereditos", "tokens_in", "tokens_out", "primeiro_byte_s", "segundos",
                  "modelo_resposta", "erro", "inicio", "fim", "pid"):
            self.assertIn(k, disco)
        self.assertFalse(co.LOCK.exists(), "o lock tem de sumir no fim")
        self.assertEqual(list(co.PASTA.glob("*.tmp")), [])
        for p in self.tmp.rglob("*"):
            if p.is_file() and p != co.PROXY:
                self.assertNotIn(CHAVE_FALSA, p.read_text(encoding="utf-8", errors="replace"), f"chave em {p}")

    def rodar(self, lid, cenario, **mais):
        self.pedido(lid, cenario, **mais)
        r = co.lote(lid)
        self.conferir_arquivos(lid, r)
        return r

    def jobs(self, r):
        return [v.get("job") for v in r["vereditos"]]

    def embrulho(self):
        p = self.tmp / "embrulho.py"
        p.write_text(EMBRULHO.format(raiz=str(RAIZ)), encoding="utf-8")
        return p

    # ── chamada ──
    def test_normal_3_blocos(self):
        r = self.rodar("normal", "normal")
        self.assertEqual(r["status"], "terminou", r)
        self.assertEqual(self.jobs(r), ["j1", "j2", "j3"])
        self.assertEqual([v["veredito"] for v in r["vereditos"]], ["MANTER", "DESFAZER", "DONA"])
        self.assertEqual((r["tokens_in"], r["tokens_out"]), (1234, 321))
        self.assertIn("opus-4-6", r["modelo_resposta"])
        self.assertIsNotNone(r["primeiro_byte_s"])
        self.assertIsNone(r["erro"])
        self.assertEqual(r["stop_reason"], "end_turn")
        txt = (co.PASTA / "normal.txt").read_text(encoding="utf-8")
        self.assertEqual(txt, bloco("j1") + bloco("j2", "DESFAZER") + bloco("j3", "DONA"))
        self.assertNotIn("deixa eu ver", txt)  # raciocínio não vai pro .txt
        ped = self.srv.pedidos[0]
        self.assertEqual(ped["headers"]["x-api-key"], CHAVE_FALSA)
        self.assertEqual(ped["headers"]["authorization"], f"Bearer {CHAVE_FALSA}")
        self.assertEqual(ped["headers"]["anthropic-version"], "2023-06-01")
        self.assertTrue(ped["corpo"]["stream"])
        self.assertEqual(ped["corpo"]["model"], "antigravity/claude-opus-4-6-thinking")
        self.assertEqual(ped["corpo"]["max_tokens"], 2000)
        self.assertEqual(ped["corpo"]["system"], "Você é o juiz final.")
        self.assertIn("Dossiê de teste", ped["corpo"]["messages"][0]["content"])

    def test_nada_antes_do_primeiro_byte(self):
        t = time.monotonic()
        r = self.rodar("sembyte", "sembyte")
        self.assertEqual(r["status"], "travou", r)
        self.assertIsNone(r["primeiro_byte_s"])
        self.assertEqual(r["vereditos"], [])
        self.assertIn("1º byte", r["erro"])
        self.assertLess(time.monotonic() - t, 6)

    def test_silencio_no_meio(self):
        r = self.rodar("silencio", "silencio")
        self.assertEqual(r["status"], "travou", r)
        self.assertEqual(self.jobs(r), ["j1"])  # o bloco fechado vale; o aberto não
        self.assertIn("no meio", r["erro"])
        self.assertIn("AUDITORIA>>>", self.srv.estado.get("txt_no_meio", ""), "o .txt não estava sendo gravado "
                                                                                "ao vivo")

    def test_pings_sem_fim_estoura_o_teto(self):
        r = self.rodar("pings", "pings", tempo_max_min=0.05)
        self.assertEqual(r["status"], "travou", r)
        self.assertIn("teto", r["erro"])
        self.assertTrue(2.5 < r["segundos"] < 8, r["segundos"])

    def test_http_429(self):
        r = self.rodar("r429", "429")
        self.assertEqual(r["status"], "recusado_HTTP_429", r)
        self.assertEqual(r["vereditos"], [])
        self.assertNotIn(CHAVE_FALSA, r["erro"])
        self.assertIn("<chave>", r["erro"])

    def test_400_com_stream_refaz_sem_stream(self):
        r = self.rodar("r400", "400")
        self.assertEqual(r["status"], "terminou", r)
        self.assertEqual(self.jobs(r), ["a", "b"])
        self.assertTrue(r["sem_stream"])
        self.assertEqual([p["corpo"]["stream"] for p in self.srv.pedidos], [True, False])
        self.assertEqual((r["tokens_in"], r["tokens_out"]), (50, 60))

    def test_modelo_errado_descarta(self):
        r = self.rodar("modelo", "modelo")
        self.assertEqual(r["status"], "modelo_errado", r)
        self.assertEqual(r["vereditos"], [])
        self.assertEqual(r["modelo_resposta"], "kr/claude-sonnet-4.5")

    def test_botao_no_meio(self):
        r = self.rodar("botao", "botao")
        self.assertEqual(r["status"], "desligado", r)
        self.assertEqual(self.jobs(r), ["j1"])

    def test_botao_antes_nem_chama(self):
        co.DESLIGADA.write_text("x", encoding="utf-8")
        r = self.rodar("antes", "normal")
        self.assertEqual(r["status"], "desligado", r)
        self.assertEqual(self.srv.pedidos, [])

    def test_sem_respeitar_botao_vai_ate_o_fim(self):
        r = self.rodar("botao2", "botao", respeitar_botao=False)
        self.assertEqual(r["status"], "terminou", r)
        self.assertEqual(self.jobs(r), ["j1", "j2"])

    def test_evento_error_caiu(self):
        r = self.rodar("erro", "erro")
        self.assertEqual(r["status"], "caiu", r)
        self.assertIn("Overloaded", r["erro"])
        self.assertEqual(self.jobs(r), ["j1"])

    def test_acabou_sem_message_stop_caiu(self):
        r = self.rodar("corte", "corte")
        self.assertEqual(r["status"], "caiu", r)
        self.assertEqual(self.jobs(r), ["j1"])

    def test_sem_servidor_erro(self):
        r = self.rodar("semserv", "x", base_url="http://127.0.0.1:9")
        self.assertIn(r["status"], ("erro", "travou"), r)
        self.assertEqual(r["vereditos"], [])

    def test_pedido_faltando(self):
        co.PASTA.mkdir(parents=True, exist_ok=True)
        r = co.lote("nao_existe")
        self.assertEqual(r["status"], "erro")
        self.assertIn("pedido", r["erro"])
        self.conferir_arquivos("nao_existe", r)

    # ── lock ──
    def test_lock_com_pid_vivo_recusa(self):
        self.pedido("l1", "normal")
        co.PASTA.mkdir(parents=True, exist_ok=True)
        co.LOCK.write_text(json.dumps({"pid": os.getpid(), "id": "outro", "inicio": co._agora()}), encoding="utf-8")
        self.assertEqual(co.lote_vivo()["id"], "outro")
        r = co.lote("l1")
        self.assertEqual(r["status"], "erro")
        self.assertTrue(r["erro"].startswith("recusado"), r["erro"])
        self.assertEqual(self.srv.pedidos, [])
        self.assertEqual(json.loads(co.LOCK.read_text(encoding="utf-8"))["id"], "outro")  # não mexeu no do outro
        self.assertEqual(json.loads((co.PASTA / "l1.json").read_text(encoding="utf-8"))["status"], "erro")
        self.assertEqual(co.main(["lote", "l1"]), 3)

    def test_lock_de_pid_morto_e_trocado(self):
        morto = int(subprocess.run([sys.executable, "-c", "import os;print(os.getpid())"], capture_output=True,
                                   text=True, creationflags=SEM_JANELA).stdout.strip())
        self.assertFalse(co._vivo(morto))
        co.PASTA.mkdir(parents=True, exist_ok=True)
        co.LOCK.write_text(json.dumps({"pid": morto, "id": "velho", "inicio": co._agora()}), encoding="utf-8")
        self.assertIsNone(co.lote_vivo())
        r = self.rodar("l2", "normal")
        self.assertEqual(r["status"], "terminou", r)

    def test_lock_velho_demais_nao_conta(self):
        co.PASTA.mkdir(parents=True, exist_ok=True)
        velho = (datetime.now() - timedelta(hours=co.LOCK_VELHO_H + 1)).isoformat(timespec="seconds")
        co.LOCK.write_text(json.dumps({"pid": os.getpid(), "id": "v", "inicio": velho}), encoding="utf-8")
        self.assertIsNone(co.lote_vivo())

    # ── vereditos ──
    def test_extrair_vereditos_casos_quebrados(self):
        t = ("antes\n" + bloco("a")
             + "<<<AUDITORIA\n```json\n{\"job\": \"b\", \"veredito\": \"DESFAZER\"}\n```\nAUDITORIA>>>\n"
             + "<<<AUDITORIA {\"job\": \"quebrado\", \"veredito\": } AUDITORIA>>>\n"
             + "<<<AUDITORIA {\"job\": \"c\", \"veredito\": \"DONA\",} AUDITORIA>>>\n"
             + "<<<AUDITORIA o json: {\"job\": \"d\", \"por_que\": \"linha1\nlinha2\"} fim AUDITORIA>>>\n"
             + "<<<AUDITORIA {\"job\": \"aberto\"\n"
             + "<<< AUDITORIA {\"job\": \"e\", \"veredito\": \"MANTER\"} AUDITORIA >>>\n"
             + "<<<AUDITORIA [{\"job\": \"f\"}, {\"job\": \"g\"}, 3] AUDITORIA>>>\n"
             + "<<<AUDITORIA nada de json aqui AUDITORIA>>>\n"
             + "<<<AUDITORIA {\"job\": \"cortado\", \"veredito\": \"MAN")
        self.assertEqual([v["job"] for v in co.extrair_vereditos(t)], ["a", "b", "c", "d", "e", "f", "g"])
        self.assertEqual(co.extrair_vereditos(""), [])
        self.assertEqual(co.extrair_vereditos(None), [])
        self.assertEqual(co.extrair_vereditos("Formato: <<<AUDITORIA {json} AUDITORIA>>>"), [])

    def test_limpar_tira_chave(self):
        co._SEGREDOS.add(CHAVE_FALSA)
        s = co._limpar(f"x {CHAVE_FALSA} y Bearer abc.def x-api-key: zzz <SEGREDO_REMOVIDO>")
        self.assertNotIn(CHAVE_FALSA, s)
        self.assertNotIn("abc.def", s)
        self.assertNotIn("zzz", s)
        self.assertNotIn("<SEGREDO_REMOVIDO>", s)

    # ── botão ──
    def test_ligar_desligar_status(self):
        self.assertFalse(co.desligada())
        self.assertIn("já estava ligada", co.ligar())
        m = co.desligar()
        self.assertTrue(co.desligada())
        self.assertIn("DESLIGADA", m)
        self.assertIn("Nada estava sendo julgado", m)
        self.assertIn("já estava desligada", co.desligar())
        self.assertIn("DESLIGADA pelo botão", co.status_txt())
        m = co.ligar()
        self.assertFalse(co.desligada())
        self.assertIn("LIGADA", m)
        self.assertIn("LIGADA.", co.status_txt())
        # com lote vivo: 3 itens, 1 já decidido no .txt
        self.pedido("vivo", "normal")
        (co.PASTA / "vivo.txt").write_text(bloco("j1") + "<<<AUDITORIA {\"job\": \"j2\"", encoding="utf-8")
        co.LOCK.write_text(json.dumps({"pid": os.getpid(), "id": "vivo", "inicio": co._agora()}), encoding="utf-8")
        m = co.desligar()
        self.assertIn("Estava julgando 3 (1 já decidido); para no próximo pedaço; os já decididos valem", m)
        self.assertIn("Julgando agora: lote vivo (3 itens, 1 já decididos", co.status_txt())
        co.LOCK.unlink()
        # último lote no status
        co.ligar()
        self.rodar("ultimo", "normal")
        self.assertIn("Último lote: ultimo — terminou, 3 vereditos", co.status_txt())

    def test_cli_overrides(self):
        self.pedido("cli", "nada", base_url="http://127.0.0.1:9/nada")
        cod = co.main(["lote", "cli", "--modelo", "kr/claude-sonnet-4.5", "--base", f"{self.url}/modelo",
                       "--sem-checar-modelo"])
        self.assertEqual(cod, 0)
        self.assertEqual(self.srv.pedidos[0]["corpo"]["model"], "kr/claude-sonnet-4.5")
        r = json.loads((co.PASTA / "cli.json").read_text(encoding="utf-8"))
        self.assertEqual(r["status"], "terminou", r)
        self.assertEqual(self.jobs(r), ["j1"])
        self.assertEqual(r["modelo_pedido"], "kr/claude-sonnet-4.5")

    def test_cli_uso(self):
        self.assertEqual(co.main(["lote"]), 2)
        self.assertEqual(co.main(["lote", "..\\fora"]), 2)
        self.assertEqual(co.main(["lote", "x", "--outra"]), 2)
        self.assertEqual(co.main(["nada"]), 2)

    # ── processos à parte ──
    def test_relogio_de_seguranca_grava_e_sai(self):
        self.pedido("relogio", "normal", tempo_max_min=0.03)
        env = dict(os.environ, CAMADA_OPUS_TESTE=str(self.tmp), CAMADA_OPUS_TRAVAR="1")
        t = time.monotonic()
        p = subprocess.run([sys.executable, str(self.embrulho()), "lote", "relogio"], env=env, capture_output=True,
                           timeout=40, creationflags=SEM_JANELA)
        self.assertEqual(p.returncode, 4, p.stderr)
        self.assertLess(time.monotonic() - t, 15)
        r = json.loads((co.PASTA / "relogio.json").read_text(encoding="utf-8"))
        self.assertEqual(r["status"], "travou")
        self.assertIn("relógio", r["erro"])
        self.assertFalse(co.LOCK.exists())

    def test_sem_stdout_como_pythonw(self):
        env = dict(os.environ, CAMADA_OPUS_TESTE=str(self.tmp), CAMADA_OPUS_SEM_STDOUT="1")
        emb = str(self.embrulho())
        for cmd in ("status", "desligar", "status", "ligar"):
            p = subprocess.run([sys.executable, emb, cmd], env=env, capture_output=True, timeout=30,
                               creationflags=SEM_JANELA)
            self.assertEqual(p.returncode, 0, (cmd, p.stdout, p.stderr))
            self.assertEqual(p.stdout, b"")
            if cmd == "desligar":
                self.assertTrue(co.DESLIGADA.exists())
        self.assertFalse(co.DESLIGADA.exists())

    def test_botao_ps1(self):
        ps1 = RAIZ / "camada_opus_botao.ps1"
        env = dict(os.environ, CAMADA_OPUS_TESTE=str(self.tmp))
        emb = str(self.embrulho())

        def botao(modo):
            p = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1), modo,
                                "-SemJanela", "-Script", emb], env=env, capture_output=True, timeout=60,
                               creationflags=SEM_JANELA)
            return p.returncode, p.stdout.decode("utf-8", "replace")

        cod, msg = botao("OFF")
        self.assertEqual(cod, 0, msg)
        self.assertIn("Camada Opus DESLIGADA", msg)
        self.assertTrue(co.DESLIGADA.exists())
        cod, msg = botao("ON")
        self.assertEqual(cod, 0, msg)
        self.assertIn("Camada Opus LIGADA", msg)
        self.assertFalse(co.DESLIGADA.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
