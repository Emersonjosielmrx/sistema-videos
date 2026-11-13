# -*- coding: utf-8 -*-
r"""camada_opus.py — 3ª camada das melhorias contínuas: o JUIZ Opus (24/10).

O Opus não edita e não usa claude -p. Este processo, separado do motor, faz UMA chamada direta à API (stream, sem
ferramentas) com o dossiê que o motor (melhoria_continua.py) já montou, grava o texto ao vivo e o resultado. Para cada
aplicação o Opus devolve um bloco <<<AUDITORIA {json} AUDITORIA>>>; quem age (desfazer, refazer, avisar) é o motor.
Nunca roda dentro do passo() do motor: ele dispara "pythonw camada_opus.py lote <id>" destacado e só lê os arquivos.

    python camada_opus.py lote <id> [--modelo M] [--base URL] [--sem-checar-modelo]   (overrides: teste grátis)
    python camada_opus.py ligar | desligar | status                                    (o botão da dona)

Arquivos em estado\opus:
  <id>_pedido.json  o motor escreve: id, modelo, base_url, system, dossie (caminho do <id>_dossie.md), max_tokens,
                    primeiro_byte_s, tempo_max_min, jobs, exigir_modelo ("" = não confere), respeitar_botao
  <id>.txt          só o texto da resposta, gravado ao vivo (se o processo morrer, o motor reprocessa este arquivo)
  <id>.json         resultado: status terminou|caiu|travou|desligado|recusado_HTTP_<n>|modelo_errado|erro, vereditos...
  camada.lock       {"pid","id","inicio"}: um lote por vez
Botão: estado\opus_camada_DESLIGADA existe = desligada. O lote rodando vê no pedaço seguinte do stream, fecha a conexão
e sai com "desligado" (nada é morto); os blocos já fechados valem.
Travas de tempo: socket com timeout = primeiro_byte_s (vale entre um pedaço e outro), teto total conferido a cada pedaço
e um relógio de segurança (teto + 60 s) que grava o parcial como "travou" e sai sozinho (os._exit).
A chave vem do claude_proxy.json, fica só em memória e é limpa de qualquer texto de erro.
"""
import http.client
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent                          # D:\video-fila
PASTA = BASE / "estado" / "opus"
DESLIGADA = BASE / "estado" / "opus_camada_DESLIGADA"           # arquivo-flag do botão (existe = desligada)
LOCK = PASTA / "camada.lock"                                    # {"pid","id","inicio"}
PROXY = Path(r"D:\hipercool-videos\secrets\claude_proxy.json")  # campo auth_token (lido só em memória)
SEM_JANELA = 0x08000000
FOLGA_TIMER_S = 60      # relógio de segurança: teto + isto -> grava "travou" e sai sozinho
LOCK_VELHO_H = 3        # lock mais velho que isto é sobra (o Windows reaproveita PID; o lote sai no teto + 60 s)
PADRAO = {"max_tokens": 12000, "primeiro_byte_s": 150, "tempo_max_min": 12}
_ABRIDOR = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # direto, sem proxy do ambiente
_SEGREDOS = set()       # a chave em memória, só pra limpar de texto de erro
_BLOCO = re.compile(r"<<<\s*AUDITORIA\b((?:(?!<<<\s*AUDITORIA\b).)*?)\bAUDITORIA\s*>>>", re.S)


# ─── utilidades ──────────────────────────────────────────────────────────────
def _dizer(msg):
    """print que não quebra no pythonw (stdout None)."""
    try:
        if sys.stdout is not None:
            print(msg, flush=True)
    except Exception:  # noqa: BLE001
        pass


def _agora():
    return datetime.now().isoformat(timespec="seconds")


def _ler_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _gravar_json(p, obj):
    """Gravação atômica (.tmp + os.replace). Se o motor estiver lendo no instante, tenta de novo."""
    p = Path(p)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    for _ in range(20):
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            time.sleep(0.1)
    os.replace(tmp, p)


def _limpar(txt, n=600):
    """Texto de erro sem chave nenhuma (a do proxy, Bearer, x-api-key, sk-..., tokens compridos) e curto."""
    s = str(txt or "")
    for seg in _SEGREDOS:
        if seg:
            s = s.replace(seg, "<chave>")
    s = re.sub(r"(?i)(bearer\s+)[^\s\"',;]+", r"\1<chave>", s)
    s = re.sub(r"(?i)(x-api-key[\"']?\s*[:=]\s*[\"']?)[^\s\"',;]+", r"\1<chave>", s)
    s = re.sub(r"\b(?:sk|pk|rk)-[A-Za-z0-9_\-]{8,}", "<chave>", s)
    s = re.sub(r"[A-Za-z0-9_\-+=]{32,}", "<...>", s)
    s = " ".join(s.split())
    return s[:n]


def _num(v, padrao):
    try:
        v = float(v)
        return v if v > 0 else float(padrao)
    except (TypeError, ValueError):
        return float(padrao)


def _dur(seg):
    return f"{seg / 60:g} min" if seg >= 120 else f"{seg:.0f} s"


def _milhar(n):
    return f"{int(n or 0):,}".replace(",", ".")


def _url(base):
    b = str(base).strip().rstrip("/")
    return b + "/messages" if b.endswith("/v1") else b + "/v1/messages"


def _chave():
    d = _ler_json(PROXY)
    k = str((d or {}).get("auth_token") or "").strip() if isinstance(d, dict) else ""
    if not k:
        raise RuntimeError("sem auth_token no claude_proxy.json")
    _SEGREDOS.add(k)
    return k


# ─── botão e lock ────────────────────────────────────────────────────────────
def _vivo(pid):
    """Mesmo jeito do painel_ia._vivo (tasklist), conferindo o PID como número inteiro."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    try:
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"], capture_output=True, text=True,
                           timeout=15, creationflags=SEM_JANELA)
        return f'"{pid}"' in (r.stdout or "")
    except Exception:  # noqa: BLE001
        return False


def desligada():
    """A dona apertou DESLIGAR (o arquivo-flag existe)."""
    try:
        return DESLIGADA.exists()
    except OSError:
        return False


def lote_vivo():
    """O lote rodando agora ({"pid","id","inicio"}) ou None. Lock de processo morto (ou velho demais) não conta."""
    d = _ler_json(LOCK)
    if not isinstance(d, dict) or not _vivo(d.get("pid")):
        return None
    try:
        if (datetime.now() - datetime.fromisoformat(str(d.get("inicio")))).total_seconds() > LOCK_VELHO_H * 3600:
            return None
    except (TypeError, ValueError):
        pass
    return d


def _pegar_lock(lid):
    """(True, None) se pegou; (False, quem) se outro lote vivo segura. Lock de morto é trocado."""
    PASTA.mkdir(parents=True, exist_ok=True)
    for _ in range(3):
        try:
            fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            quem = lote_vivo()
            if quem:
                return False, quem
            try:
                LOCK.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                time.sleep(0.2)
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "id": lid, "inicio": _agora()}, f)
        return True, None
    return False, (lote_vivo() or {"id": "?", "pid": None})


def _soltar_lock():
    """Apaga o lock só se for deste processo."""
    d = _ler_json(LOCK)
    if isinstance(d, dict) and str(d.get("pid")) == str(os.getpid()):
        try:
            LOCK.unlink()
        except OSError:
            pass


# ─── vereditos ───────────────────────────────────────────────────────────────
def _json_tolerante(corpo):
    """dict/list do bloco, ou None. Tolera cerca de código, texto em volta e vírgula sobrando."""
    s = re.sub(r"(?m)^\s*```[\w-]*\s*$", "", corpo).strip()
    dec = json.JSONDecoder(strict=False)
    for cand in (s, re.sub(r",\s*([}\]])", r"\1", s)):
        try:
            return json.loads(cand, strict=False)
        except ValueError:
            pass
        ini = min((i for i in (cand.find("{"), cand.find("[")) if i >= 0), default=-1)
        if ini >= 0:
            try:
                return dec.raw_decode(cand[ini:])[0]
            except ValueError:
                pass
    return None


def extrair_vereditos(texto):
    """Blocos <<<AUDITORIA {json} AUDITORIA>>> já fechados -> lista de dicts. Bloco quebrado (ou aberto) é pulado."""
    saida = []
    for m in _BLOCO.finditer(str(texto or "")):
        obj = _json_tolerante(m.group(1))
        if isinstance(obj, dict):
            saida.append(obj)
        elif isinstance(obj, list):
            saida.extend(o for o in obj if isinstance(o, dict))
    return saida


# ─── o lote (uma chamada) ────────────────────────────────────────────────────
class _Lote:
    def __init__(self, lid):
        self.lid = str(lid)
        self.t0 = time.monotonic()
        self.trava = threading.Lock()
        self.gravado = self.acabou = self.refez = False
        self.texto, self.txt, self.ultimo = [], None, None
        self.exigir, self.respeitar, self.corpo, self.chave = "", True, {}, ""
        self.pb = float(PADRAO["primeiro_byte_s"])
        self.teto_s = float(PADRAO["tempo_max_min"]) * 60
        self.url = ""
        self.r = {"id": self.lid, "status": "erro", "vereditos": [], "tokens_in": 0, "tokens_out": 0,
                  "primeiro_byte_s": None, "segundos": 0, "modelo_resposta": "", "erro": None, "inicio": _agora(),
                  "fim": None, "pid": os.getpid(),
                  # a mais (24/10): pra calibrar opus_primeiro_byte_s e documentar
                  "modelo_pedido": "", "jobs": [], "stop_reason": None, "primeiro_conteudo_s": None,
                  "maior_silencio_s": 0.0, "sem_stream": False}

    # preparo: lê o pedido, o dossiê e a chave. Devolve (status, erro) se não dá pra chamar.
    def preparar(self, modelo=None, base=None, checar_modelo=True):
        p = _ler_json(PASTA / f"{self.lid}_pedido.json")
        if not isinstance(p, dict):
            return "erro", f"pedido {self.lid}_pedido.json não achado ou quebrado"
        modelo = str(modelo or p.get("modelo") or "").strip()
        base = str(base or p.get("base_url") or "").strip()
        if not modelo or not base:
            return "erro", "pedido sem modelo ou sem base_url"
        self.url = _url(base)
        self.exigir = str(p.get("exigir_modelo") or "").strip().lower() if checar_modelo else ""
        self.pb = _num(p.get("primeiro_byte_s"), PADRAO["primeiro_byte_s"])
        self.teto_s = _num(p.get("tempo_max_min"), PADRAO["tempo_max_min"]) * 60
        self.respeitar = p.get("respeitar_botao", True) is not False
        self.r.update(modelo_pedido=modelo, jobs=list(p.get("jobs") or []))
        if self.respeitar and desligada():
            return "desligado", "a camada já estava desligada (botão) antes de começar"
        dos = Path(str(p.get("dossie") or ""))
        if not str(p.get("dossie") or "").strip():
            return "erro", "pedido sem dossiê"
        if not dos.is_absolute():
            dos = PASTA / dos
        try:
            dossie = dos.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return "erro", f"não li o dossiê {dos.name}: {e}"
        if not dossie.strip():
            return "erro", "dossiê vazio"
        try:
            self.chave = _chave()
        except Exception as e:  # noqa: BLE001
            return "erro", str(e)
        self.corpo = {"model": modelo, "max_tokens": int(_num(p.get("max_tokens"), PADRAO["max_tokens"])),
                      "messages": [{"role": "user", "content": dossie}]}
        if str(p.get("system") or "").strip():
            self.corpo["system"] = str(p["system"])
        self.txt = open(PASTA / f"{self.lid}.txt", "w", encoding="utf-8", newline="")
        return None

    def _cabecalhos(self, stream):
        return {"content-type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": self.chave,
                "authorization": f"Bearer {self.chave}", "user-agent": "camada-opus/1",
                "accept": "text/event-stream" if stream else "application/json"}

    def _texto(self, t):
        if not t:
            return
        self.texto.append(t)
        if self.txt:
            self.txt.write(t)
            self.txt.flush()

    def _usage(self, u):
        if not isinstance(u, dict):
            return
        ent = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                                 "cache_read_input_tokens"))
        if ent:
            self.r["tokens_in"] = max(self.r["tokens_in"], ent)
        if u.get("output_tokens"):
            self.r["tokens_out"] = max(self.r["tokens_out"], int(u["output_tokens"]))

    def _modelo_ok(self):
        return not self.exigir or self.exigir in str(self.r["modelo_resposta"]).lower()

    def _fechar(self, status, erro=None, espera=-1):
        """Grava o <id>.json uma vez só (o relógio de segurança e o fluxo normal podem chegar juntos)."""
        if not self.trava.acquire(timeout=espera):
            return True
        try:
            if self.gravado:
                return True
            texto = "".join(self.texto)
            if not self._modelo_ok() and (status == "terminou" or (texto and status in ("travou", "caiu",
                                                                                         "desligado", "erro"))):
                erro = (f"modelo errado: pedi algo com '{self.exigir}', respondeu '{self.r['modelo_resposta'] or '?'}'"
                        + (f" ({erro})" if erro else ""))
                status = "modelo_errado"
            ver = [] if status == "modelo_errado" or status.startswith("recusado") else extrair_vereditos(texto)
            self.r.update(status=status, vereditos=ver, erro=_limpar(erro) if erro else None, fim=_agora(),
                          segundos=round(time.monotonic() - self.t0, 1))
            _gravar_json(PASTA / f"{self.lid}.json", self.r)
            self.gravado = True
            return True
        finally:
            self.trava.release()

    def estourou(self):
        """Relógio de segurança (teto + 60 s): grava o parcial como travou e sai sozinho. Ninguém mata o processo."""
        if self.acabou:
            return
        try:
            if self.txt:
                try:
                    self.txt.flush()
                except Exception:  # noqa: BLE001
                    pass
            self._fechar("travou", f"passou do teto de {_dur(self.teto_s)} + {FOLGA_TIMER_S} s (relógio de "
                                   "segurança)", espera=10)
            _soltar_lock()
        finally:
            if not self.acabou:
                os._exit(4)

    def chamar(self, stream=True):
        corpo = dict(self.corpo, stream=stream)
        req = urllib.request.Request(self.url, data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
                                     headers=self._cabecalhos(stream), method="POST")
        restante = max(5.0, self.teto_s - (time.monotonic() - self.t0))
        t_envio = time.monotonic()
        try:
            resp = _ABRIDOR.open(req, timeout=self.pb if stream else restante)
        except urllib.error.HTTPError as e:
            try:
                corpo_erro = e.read(2000).decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                corpo_erro = ""
            if e.code == 400 and stream and not self.refez:  # gateway que não aceita stream: 1 vez sem stream
                self.refez = True
                self.r["sem_stream"] = True
                try:  # o botão DESLIGAR lê do lock que este lote está sem stream (achado 20)
                    trava = _ler_json(LOCK)
                    if isinstance(trava, dict) and str(trava.get("id")) == self.lid:
                        _gravar_json(LOCK, dict(trava, sem_stream=True))
                except Exception:  # noqa: BLE001
                    pass
                if self.respeitar and desligada():
                    return self._fechar("desligado", "a dona desligou a camada (botão)")
                return self.chamar(False)
            return self._fechar(f"recusado_HTTP_{e.code}", f"HTTP {e.code}: {_limpar(corpo_erro, 400)}")
        except (TimeoutError, socket.timeout):
            return self._fechar("travou", f"nada chegou em {_dur(self.pb if stream else restante)} (nem o 1º byte)")
        except urllib.error.URLError as e:
            if isinstance(e.reason, (TimeoutError, socket.timeout)):
                return self._fechar("travou", f"não conectou em {_dur(self.pb)}")
            return self._fechar("erro", f"sem conexão com {self.url}: {e.reason}")
        except (http.client.HTTPException, OSError) as e:
            return self._fechar("caiu", f"conexão caiu antes da resposta: {type(e).__name__}: {e}")
        with resp:
            if resp.status != 200:
                return self._fechar(f"recusado_HTTP_{resp.status}", f"HTTP {resp.status}")
            tipo = str(resp.headers.get("content-type") or "").lower()
            if stream and not ("json" in tipo and "event-stream" not in tipo):
                return self._ler_stream(resp, t_envio)
            return self._ler_inteiro(resp, t_envio)

    def _ler_stream(self, resp, t_envio):
        evento, dados = "", []
        while True:
            try:
                linha = resp.readline()
            except (TimeoutError, socket.timeout):
                self.r["maior_silencio_s"] = round(max(self.r["maior_silencio_s"],
                                                       time.monotonic() - (self.ultimo or t_envio)), 1)
                onde = "nem o 1º byte" if self.r["primeiro_byte_s"] is None else "no meio da resposta"
                return self._fechar("travou", f"{_dur(self.pb)} sem nada do servidor ({onde})")
            except (http.client.HTTPException, OSError) as e:
                return self._fechar("caiu", f"conexão caiu no meio: {type(e).__name__}: {e}")
            agora = time.monotonic()
            if not linha:
                break
            if self.r["primeiro_byte_s"] is None:
                self.r["primeiro_byte_s"] = round(agora - t_envio, 1)
            if self.ultimo is not None:
                self.r["maior_silencio_s"] = round(max(self.r["maior_silencio_s"], agora - self.ultimo), 1)
            self.ultimo = agora
            # a cada pedaço: teto total e botão
            if agora - self.t0 > self.teto_s:
                return self._fechar("travou", f"passou do teto de {_dur(self.teto_s)}")
            if self.respeitar and desligada():
                return self._fechar("desligado", "a dona desligou a camada (botão); os blocos já fechados valem")
            s = linha.decode("utf-8", "replace").rstrip("\r\n")
            if not s:
                if dados and self._evento(evento, "\n".join(dados)):
                    return True
                evento, dados = "", []
                continue
            if s.startswith(":"):
                continue
            campo, _, valor = s.partition(":")
            valor = valor[1:] if valor.startswith(" ") else valor
            if campo == "event":
                evento = valor
            elif campo == "data":
                dados.append(valor)
        if dados and self._evento(evento, "\n".join(dados)):
            return True
        if self.r["stop_reason"]:  # gateway que não manda message_stop, mas mandou o fim
            return self._fechar("terminou")
        return self._fechar("caiu", "a resposta acabou no meio (sem message_stop)")

    def _evento(self, tipo_sse, dados):
        """Trata um evento SSE. True = já gravou o status final (para de ler)."""
        if dados.strip() == "[DONE]":
            return False
        try:
            obj = json.loads(dados)
        except ValueError:
            return False
        if not isinstance(obj, dict):
            return False
        tipo = obj.get("type") or tipo_sse
        if tipo == "message_start":
            msg = obj.get("message") or {}
            self.r["modelo_resposta"] = str(msg.get("model") or "")
            self._usage(msg.get("usage"))
            if not self._modelo_ok():
                return self._fechar("modelo_errado", f"pedi algo com '{self.exigir}', respondeu "
                                                     f"'{self.r['modelo_resposta'] or '?'}'")
        elif tipo == "content_block_delta":
            d = obj.get("delta") or {}
            if d.get("type") in ("text_delta", "thinking_delta") and self.r["primeiro_conteudo_s"] is None:
                self.r["primeiro_conteudo_s"] = round(time.monotonic() - self.t0, 1)
            if d.get("type") == "text_delta":  # thinking_delta só conta como atividade
                self._texto(d.get("text") or "")
        elif tipo == "message_delta":
            self._usage(obj.get("usage"))
            sr = (obj.get("delta") or {}).get("stop_reason")
            if sr:
                self.r["stop_reason"] = sr
        elif tipo == "message_stop":
            return self._fechar("terminou")
        elif tipo == "error":
            err = obj.get("error") or {}
            msg = f"{err.get('type')}: {err.get('message')}" if isinstance(err, dict) else str(err)
            return self._fechar("caiu", f"erro no stream: {msg}")
        return False

    def _ler_inteiro(self, resp, t_envio):
        """Resposta sem stream (o refazer do HTTP 400, ou gateway que respondeu JSON)."""
        try:
            bruto = resp.read()
        except (TimeoutError, socket.timeout):
            return self._fechar("travou", "a resposta sem stream não chegou dentro do teto")
        except (http.client.HTTPException, OSError) as e:
            return self._fechar("caiu", f"conexão caiu: {type(e).__name__}: {e}")
        self.r["primeiro_byte_s"] = round(time.monotonic() - t_envio, 1)
        if self.respeitar and desligada():  # 24/10 (achado 20): o botão vale também sem stream
            return self._fechar("desligado", "a dona desligou durante a resposta sem stream")
        try:
            obj = json.loads(bruto.decode("utf-8", "replace"))
        except ValueError:
            return self._fechar("caiu", f"resposta não é JSON: {bruto[:300].decode('utf-8', 'replace')}")
        if not isinstance(obj, dict):
            return self._fechar("caiu", "resposta JSON sem objeto")
        if obj.get("type") == "error" or obj.get("error"):
            err = obj.get("error") or {}
            msg = f"{err.get('type')}: {err.get('message')}" if isinstance(err, dict) else str(err)
            return self._fechar("caiu", f"erro na resposta: {msg}")
        self.r["modelo_resposta"] = str(obj.get("model") or "")
        self._usage(obj.get("usage"))
        self.r["stop_reason"] = obj.get("stop_reason")
        for b in obj.get("content") or []:
            if isinstance(b, dict) and b.get("type") == "text":
                self._texto(b.get("text") or "")
        return self._fechar("terminou")

    def fechar_txt(self):
        if self.txt:
            try:
                self.txt.close()
            except Exception:  # noqa: BLE001
                pass


def lote(lid, modelo=None, base=None, checar_modelo=True):
    """Julga um lote (o motor dispara com pythonw, destacado). Devolve o resultado (o mesmo do <id>.json)."""
    PASTA.mkdir(parents=True, exist_ok=True)
    j = _Lote(lid)
    ok, quem = _pegar_lock(j.lid)
    if not ok:
        j.r.update(fim=_agora(), erro=f"recusado: já tem lote rodando ({quem.get('id')}, pid {quem.get('pid')})")
        if str(quem.get("id")) != j.lid:  # não pisa no resultado do lote vivo de mesmo id
            _gravar_json(PASTA / f"{j.lid}.json", j.r)
        return j.r
    timer = None
    try:
        falha = j.preparar(modelo, base, checar_modelo)
        if falha:
            j._fechar(*falha)
        else:
            timer = threading.Timer(j.teto_s + FOLGA_TIMER_S, j.estourou)
            timer.daemon = True
            timer.start()
            j.chamar(True)
        if not j.gravado:
            j._fechar("erro", "acabou sem status (defeito do camada_opus)")
    except Exception as e:  # noqa: BLE001
        j._fechar("erro", f"{type(e).__name__}: {e} | {traceback.format_exc(limit=3)}")
    finally:
        j.acabou = True
        if timer:
            timer.cancel()
        j.fechar_txt()
        _soltar_lock()
    return j.r


# ─── botão da dona ───────────────────────────────────────────────────────────
def _contar(lid):
    """(itens do lote, já decididos no .txt, pedido) do lote vivo."""
    p = _ler_json(PASTA / f"{lid}_pedido.json")
    p = p if isinstance(p, dict) else {}
    try:
        feitos = len(extrair_vereditos((PASTA / f"{lid}.txt").read_text(encoding="utf-8", errors="replace")))
    except OSError:
        feitos = 0
    return len(p.get("jobs") or []), feitos, p


def ligar():
    """Apaga o arquivo do botão. Não força nada: o gatilho do motor continua valendo."""
    estava = desligada()
    try:
        DESLIGADA.unlink()
    except FileNotFoundError:
        pass
    except OSError as e:
        return f"Não consegui ligar a camada Opus ({e}). Tente de novo."
    if not estava:
        return "A camada Opus já estava ligada. Nada mudou."
    return ("Camada Opus LIGADA. Ela volta a julgar sozinha quando o Opus tiver crédito, você não estiver usando "
            "e houver fila. Não força nada agora.")


def desligar():
    """Cria o arquivo do botão. O lote rodando para no próximo pedaço; os já decididos valem; nada é morto."""
    ja = desligada()
    if not ja:
        try:
            DESLIGADA.parent.mkdir(parents=True, exist_ok=True)
            DESLIGADA.write_text(f"{_agora()} botão\n", encoding="utf-8")
        except OSError as e:
            return f"Não consegui desligar a camada Opus ({e}). Tente de novo."
    cab = "A camada Opus já estava desligada." if ja else "Camada Opus DESLIGADA: não começa julgamento novo."
    viv = lote_vivo()
    if not viv:
        return f"{cab} Nada estava sendo julgado agora. Pode usar o Opus à vontade. Para voltar, use o botão LIGAR."
    n, feitos, ped = _contar(viv.get("id"))
    dec = f" ({feitos} já decidido{'s' if feitos != 1 else ''})" if feitos else ""
    if ped.get("respeitar_botao") is False:
        teto = _num(ped.get("tempo_max_min"), PADRAO["tempo_max_min"])
        return (f"{cab} Estava julgando {n}{dec}; esse lote não para pelo botão e termina sozinho em até "
                f"{teto:g} min. Depois disso, não começa outro.")
    if viv.get("sem_stream"):  # achado 20: sem stream só para quando a resposta chegar
        teto = _num(ped.get("tempo_max_min"), PADRAO["tempo_max_min"])
        return (f"{cab} Estava julgando {n}{dec} numa resposta sem stream: ela não para no meio e pode levar até "
                f"{teto:g} min; o resultado é descartado. Espere antes de usar o Opus. Para voltar, use o botão LIGAR.")
    return (f"{cab} Estava julgando {n}{dec}; para no próximo pedaço; os já decididos valem. "
            f"Pode usar o Opus. Para voltar, use o botão LIGAR.")


def _quando(iso):
    try:
        return datetime.fromisoformat(str(iso)).strftime("%d/%m %H:%M")
    except (TypeError, ValueError):
        return "?"


def status_txt():
    """Uma linha por assunto: ligada/desligada, lote rodando, último lote."""
    linhas = []
    if desligada():
        try:
            desde = _quando(DESLIGADA.read_text(encoding="utf-8").split()[0])
        except (OSError, IndexError):
            desde = "?"
        linhas.append(f"Camada Opus (3ª camada, juiz): DESLIGADA pelo botão desde {desde}.")
    else:
        linhas.append("Camada Opus (3ª camada, juiz): LIGADA.")
    viv = lote_vivo()
    if viv:
        n, feitos, _ = _contar(viv.get("id"))
        try:
            ha = int((datetime.now() - datetime.fromisoformat(str(viv.get("inicio")))).total_seconds() // 60)
        except (TypeError, ValueError):
            ha = "?"
        linhas.append(f"Julgando agora: lote {viv.get('id')} ({n} itens, {feitos} já decididos, há {ha} min).")
    else:
        linhas.append("Nenhum lote rodando agora.")
    try:
        res = sorted((p for p in PASTA.glob("*.json") if not p.name.endswith("_pedido.json")),
                     key=lambda p: p.stat().st_mtime)
    except OSError:
        res = []
    ult = _ler_json(res[-1]) if res else None
    if isinstance(ult, dict):
        linhas.append(f"Último lote: {ult.get('id')} — {ult.get('status')}, {len(ult.get('vereditos') or [])} "
                      f"vereditos, {_milhar(ult.get('tokens_in'))} tokens de entrada e {_milhar(ult.get('tokens_out'))}"
                      f" de saída, {ult.get('segundos')} s, em {_quando(ult.get('fim'))}"
                      + (f" ({ult.get('erro')})" if ult.get("erro") else "") + ".")
    else:
        linhas.append("Nenhum lote julgado ainda.")
    return "\n".join(linhas)


# ─── linha de comando ────────────────────────────────────────────────────────
USO = ("uso: camada_opus.py lote <id> [--modelo M] [--base URL] [--sem-checar-modelo] | ligar | desligar | status")


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        try:
            if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    cmd = a[0].lower() if a else "status"
    if cmd == "ligar":
        _dizer(ligar())
        return 0
    if cmd == "desligar":
        _dizer(desligar())
        return 0
    if cmd == "status":
        _dizer(status_txt())
        return 0
    if cmd != "lote" or len(a) < 2 or not re.fullmatch(r"[\w.\-]{1,100}", a[1]):
        _dizer(USO)
        return 2
    lid, modelo, base, checar = a[1], None, None, True
    i = 2
    while i < len(a):
        op = a[i]
        if op.startswith("--modelo=") or op.startswith("--base="):
            nome, _, val = op.partition("=")
            modelo, base = (val, base) if nome == "--modelo" else (modelo, val)
        elif op in ("--modelo", "--base") and i + 1 < len(a):
            i += 1
            modelo, base = (a[i], base) if op == "--modelo" else (modelo, a[i])
        elif op == "--sem-checar-modelo":
            checar = False
        else:
            _dizer(USO)
            return 2
        i += 1
    r = lote(lid, modelo=modelo, base=base, checar_modelo=checar)
    _dizer(f"{lid}: {r['status']} | {len(r['vereditos'])} vereditos | {r['segundos']} s | 1º byte "
           f"{r['primeiro_byte_s']} s | tokens {r['tokens_in']}+{r['tokens_out']} | modelo {r['modelo_resposta']}"
           + (f" | {r['erro']}" if r["erro"] else ""))
    if str(r.get("erro") or "").startswith("recusado: já tem lote"):
        return 3
    return 0 if r["status"] == "terminou" else 1


if __name__ == "__main__":
    sys.exit(main())
