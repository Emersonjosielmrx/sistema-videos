"""Trecho de colab/postar_longos.py (postagem dos longos). Várias rodadas podem rodar ao mesmo tempo (tarefa do
Windows a cada hora + execução manual); cada uma lê o estado no começo, trabalha horas e grava no fim."""
import copy
import json
import os
import sys
import tempfile
import threading
import time
import weakref
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

BASE = Path(__file__).parent
ESTADO = BASE / "longos_postados.json"
FICHAS = BASE / "fichas"  # uma pasta por longo (ficha); o bipar_palavrao.py cria FICHAS/<nome>/SEM_PALAVRAO.txt
_TRAVA_EST = threading.RLock()
_TRAVA_ORIG = threading.Lock()
_ORIG_PRESOS = weakref.WeakKeyDictionary()
_LOCK_DEPTH = 0


class _EstadoDict(dict):
    pass


def _eh_titulo_real(titulo):
    return isinstance(titulo, str) and bool(titulo.strip()) and not titulo.lstrip().startswith("(")


def _esta_liberado(nome):
    return isinstance(nome, str) and bool(nome) and nome not in (".", "..") and (FICHAS / nome / "SEM_PALAVRAO.txt").exists()


def _adquirir_trava_arquivo(lock_path, timeout=30.0):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_path, "a+b")
    try:
        if sys.platform == "win32":
            f.seek(0, os.SEEK_END)
            if f.tell() == 0:
                f.write(b"\0")
                f.flush()
            deadline = time.monotonic() + timeout
            while True:
                f.seek(0)
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Timeout aguardando trava de {lock_path}")
                    time.sleep(0.01)
        else:
            deadline = time.monotonic() + timeout
            while True:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Timeout aguardando trava de {lock_path}")
                    time.sleep(0.01)
        return f
    except BaseException:
        f.close()
        raise


def _liberar_trava_arquivo(f):
    try:
        if sys.platform == "win32":
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    finally:
        f.close()


def _escrever_json_atomico(destino, dados):
    destino.parent.mkdir(parents=True, exist_ok=True)
    conteudo = json.dumps(dados, ensure_ascii=False, indent=1)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(destino.parent),
        prefix=f".{destino.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(conteudo)
            f.flush()
        for tentativa in range(10):
            try:
                os.replace(tmp_name, destino)
                break
            except PermissionError:
                if tentativa == 9:
                    raise
                time.sleep(0.01)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def _estado():
    for tentativa in range(3):
        try:
            data = json.loads(ESTADO.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {"postados": [], "reprovados": []}
            res = _EstadoDict(data)
            presos = data.get("presos")
            if isinstance(presos, dict):
                with _TRAVA_ORIG:
                    _ORIG_PRESOS[res] = copy.deepcopy(presos)
            return res
        except PermissionError:
            if tentativa < 2:
                time.sleep(0.005)
                continue
            return _EstadoDict({"postados": [], "reprovados": []})
        except (OSError, ValueError):
            return _EstadoDict({"postados": [], "reprovados": []})


def _gravar_estado(est):
    """03/11: grava JUNTANDO com o que está no arquivo. Em 02/11 duas rodadas rodaram juntas e a que terminou depois
    gravou a lista que tinha lido de manhã por cima: o post do yKfgs no Fio da Meada sumiu e ele voltou pra fila (quase
    saiu em 3 canais — regra: vídeo único por canal). Postado/reprovado/corte que existir no arquivo nunca se perde."""
    global _LOCK_DEPTH
    with _TRAVA_EST:
        lock_file = None
        if _LOCK_DEPTH == 0:
            lock_file = _adquirir_trava_arquivo(ESTADO.with_name(ESTADO.name + ".lock"))
        _LOCK_DEPTH += 1
        try:
            _gravar_estado_trancado(est)
        finally:
            _LOCK_DEPTH -= 1
            if lock_file is not None:
                _liberar_trava_arquivo(lock_file)


def _gravar_estado_trancado(est):
    disco = _estado()

    # Incidente 3: título que começa com "(" é nota provisória e perde para título real do arquivo para o mesmo url.
    titulos_reais_disco = {}
    for p in disco.get("postados") or []:
        url = p.get("url")
        titulo = p.get("titulo")
        if url and _eh_titulo_real(titulo):
            titulos_reais_disco[url] = titulo

    vistos = set()
    postados = []
    for p in est.get("postados") or []:
        chave = (p.get("nome"), p.get("url"))
        if chave in vistos:
            continue
        vistos.add(chave)
        url = p.get("url")
        if not _eh_titulo_real(p.get("titulo")) and url in titulos_reais_disco:
            p = {**p, "titulo": titulos_reais_disco[url]}
        postados.append(p)
    for p in disco.get("postados") or []:
        chave = (p.get("nome"), p.get("url"))
        if chave in vistos:
            continue
        vistos.add(chave)
        postados.append(p)
    est["postados"] = postados

    # Incidente 1: ficha com SEM_PALAVRAO.txt está liberada e nunca pode ficar em "reprovados".
    reprovados_uniao = set(est.get("reprovados") or []) | set(disco.get("reprovados") or [])
    est["reprovados"] = sorted(n for n in reprovados_uniao if not _esta_liberado(n))

    est["cortes_postados"] = sorted(set(est.get("cortes_postados") or []) | set(disco.get("cortes_postados") or []))

    # Incidente 2 e 4: preservar presos de qualquer rodada e aplicar presos_soltar apenas quando status == "enviando".
    orig_presos = None
    if isinstance(est, _EstadoDict):
        with _TRAVA_ORIG:
            orig_presos = _ORIG_PRESOS.get(est)

    disco_presos = disco.get("presos")
    if not isinstance(disco_presos, dict):
        disco_presos = {}
    est_presos = est.get("presos")
    if not isinstance(est_presos, dict):
        est_presos = {}

    presos = {nome: copy.deepcopy(info) for nome, info in disco_presos.items()}
    for nome, info in est_presos.items():
        if nome in presos:
            if (
                isinstance(presos[nome], dict)
                and presos[nome].get("status") == "erro"
                and isinstance(info, dict)
                and info.get("status") != "erro"
            ):
                continue
            presos[nome] = copy.deepcopy(info)
        else:
            if orig_presos is not None and nome in orig_presos and orig_presos[nome] == info:
                continue
            presos[nome] = copy.deepcopy(info)

    soltar = set(est.get("presos_soltar") or []) | set(disco.get("presos_soltar") or [])
    for nome in soltar:
        if nome in presos and isinstance(presos[nome], dict) and presos[nome].get("status") == "enviando":
            del presos[nome]

    est["presos"] = presos
    est.pop("presos_soltar", None)

    if isinstance(est, _EstadoDict):
        with _TRAVA_ORIG:
            _ORIG_PRESOS[est] = copy.deepcopy(presos)

    _escrever_json_atomico(ESTADO, est)
