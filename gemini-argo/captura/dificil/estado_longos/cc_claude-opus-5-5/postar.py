"""Trecho de colab/postar_longos.py (postagem dos longos). Várias rodadas podem rodar ao mesmo tempo (tarefa do
Windows a cada hora + execução manual); cada uma lê o estado no começo, trabalha horas e grava no fim."""
import copy
import json
import os
import shutil
import threading
import time
from pathlib import Path

BASE = Path(__file__).parent
ESTADO = BASE / "longos_postados.json"
FICHAS = BASE / "fichas"  # uma pasta por longo (ficha); o bipar_palavrao.py cria FICHAS/<nome>/SEM_PALAVRAO.txt
_TRAVA_EST = threading.RLock()


class _Estado(dict):
    """O estado é um dict comum (vai pro json igual), mas lembra o que a rodada LEU do arquivo (`_lido`). Assim, ao
    gravar, dá para saber o que a rodada mudou de propósito e o que é só cópia velha do que leu de manhã."""
    _lido = None


def _ler_disco():
    """Lê o arquivo. Devolve (dados, ok). ok=False quando não existe ou não deu para ler: aí nada pode ser tratado
    como "alguém tirou do arquivo"."""
    for tentativa in range(5):
        try:
            return json.loads(ESTADO.read_text(encoding="utf-8")), True
        except FileNotFoundError:
            return {}, False
        except (OSError, ValueError):
            time.sleep(0.05 * (tentativa + 1))  # pode estar sendo escrito à mão / por outro programa
    return {}, False


def _estado():
    dados, _ = _ler_disco()
    if not isinstance(dados, dict):
        dados = {}
    dados.setdefault("postados", [])
    dados.setdefault("reprovados", [])
    est = _Estado(dados)
    est._lido = copy.deepcopy(dict(dados))
    return est


def _gravar_estado(est):
    """03/11: grava JUNTANDO com o que está no arquivo. Em 02/11 duas rodadas rodaram juntas e a que terminou depois
    gravou a lista que tinha lido de manhã por cima: o post do yKfgs no Fio da Meada sumiu e ele voltou pra fila (quase
    saiu em 3 canais — regra: vídeo único por canal). Postado/reprovado/corte que existir no arquivo nunca se perde.

    17/11 (INCIDENTES.md): ficha com SEM_PALAVRAO.txt nunca fica em "reprovados"; "presos" de outra rodada não somem;
    título-nota "(...)" perde para título de verdade do mesmo url; "presos_soltar" solta só preso "enviando" e não fica
    gravado. A trava vale também entre processos (arquivo .lock) e a gravação é atômica (tmp + replace)."""
    with _TRAVA_EST, _TravaArquivo(ESTADO.with_name(ESTADO.name + ".lock")):
        _gravar_estado_trancado(est)


class _TravaArquivo:
    """Trava entre processos (as rodadas são processos separados; o RLock só vale dentro de um)."""

    def __init__(self, caminho, espera=600):
        self.caminho, self.espera, self.fd = caminho, espera, None

    def __enter__(self):
        self.fd = os.open(str(self.caminho), os.O_RDWR | os.O_CREAT, 0o666)
        limite = time.monotonic() + self.espera
        while True:
            try:
                _travar(self.fd)
                return self
            except OSError:
                if time.monotonic() > limite:
                    os.close(self.fd)
                    raise TimeoutError(f"trava de {self.caminho} presa há mais de {self.espera}s")
                time.sleep(0.02)

    def __exit__(self, *exc):
        try:
            _destravar(self.fd)
        finally:
            os.close(self.fd)


if os.name == "nt":
    import msvcrt

    def _travar(fd):
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)

    def _destravar(fd):
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _travar(fd):
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _destravar(fd):
        fcntl.flock(fd, fcntl.LOCK_UN)


def _e_nota(titulo):
    return isinstance(titulo, str) and titulo.strip().startswith("(")


def _liberada(nome):
    try:
        return (FICHAS / str(nome) / "SEM_PALAVRAO.txt").is_file()
    except (OSError, ValueError):
        return False


def _status(preso):
    return preso.get("status") if isinstance(preso, dict) else None


def _juntar_postados(meus, disco, lidos):
    lido_tit = {(p.get("nome"), p.get("url")): p.get("titulo") for p in lidos} if lidos is not None else {}
    disco_por_chave = {}
    real_por_url = {}
    for p in disco:
        disco_por_chave.setdefault((p.get("nome"), p.get("url")), p)
        if p.get("url") and p.get("titulo") and not _e_nota(p.get("titulo")):
            real_por_url.setdefault(p.get("url"), p.get("titulo"))

    saida, vistos = [], set()
    for p in list(meus) + [p for p in disco]:
        chave = (p.get("nome"), p.get("url"))
        if chave in vistos:
            continue
        vistos.add(chave)
        p = dict(p)
        d = disco_por_chave.get(chave)
        tit = p.get("titulo")
        if _e_nota(tit) or not tit:
            # incidente 3: nota provisória perde para título de verdade do arquivo (mesmo url)
            real = d.get("titulo") if d and d.get("titulo") and not _e_nota(d.get("titulo")) else None
            real = real or real_por_url.get(p.get("url"))
            if real:
                p["titulo"] = real
        elif d and d.get("titulo") and not _e_nota(d.get("titulo")) and d.get("titulo") != tit \
                and chave in lido_tit and lido_tit[chave] == tit:
            # a rodada não mexeu no título (é o que leu); o arquivo foi corrigido depois -> vale o arquivo
            p["titulo"] = d["titulo"]
        saida.append(p)
    # título de verdade que só a rodada tem também tira a nota de outra entrada do mesmo url
    for p in saida:
        if p.get("url") and p.get("titulo") and not _e_nota(p["titulo"]):
            real_por_url.setdefault(p["url"], p["titulo"])
    for p in saida:
        if _e_nota(p.get("titulo")) and real_por_url.get(p.get("url")):
            p["titulo"] = real_por_url[p["url"]]
    return saida


def _juntar_presos(meus, disco, lidos, disco_ok):
    saida = {}
    for nome in list(disco) + [n for n in meus if n not in disco]:
        d, e = disco.get(nome), meus.get(nome)
        intocado = lidos is not None and nome in lidos and lidos[nome] == e
        if e is None:
            saida[nome] = d  # incidente 2: preso marcado por outra rodada não some
        elif d is None:
            if intocado and disco_ok:
                continue  # a rodada só tinha a cópia do que leu; alguém soltou depois (presos_soltar)
            saida[nome] = e
        elif intocado:
            saida[nome] = d  # a rodada não mexeu: o do arquivo é igual ou mais novo
        elif lidos is not None:
            saida[nome] = e  # a rodada mudou de propósito
        else:  # sem saber o que a rodada leu: "erro" do arquivo não é rebaixado para "enviando"
            saida[nome] = d if (_status(d) == "erro" and _status(e) != "erro") else e
    return saida


def _gravar_estado_trancado(est):
    disco, disco_ok = _ler_disco()
    if not isinstance(disco, dict):
        disco, disco_ok = {}, False
    if not disco_ok and ESTADO.exists():
        try:  # arquivo existe mas está ilegível: guarda cópia antes de sobrescrever
            shutil.copy2(ESTADO, ESTADO.with_name(ESTADO.name + f".ilegivel-{int(time.time())}"))
        except OSError:
            pass
    lido = getattr(est, "_lido", None)
    lido = lido if isinstance(lido, dict) else None

    est["postados"] = _juntar_postados(est.get("postados") or [], disco.get("postados") or [],
                                       (lido.get("postados") or []) if lido is not None else None)

    # incidente 1: ficha liberada (SEM_PALAVRAO.txt) nunca fica em "reprovados"
    reprov = set(est.get("reprovados") or []) | set(disco.get("reprovados") or [])
    est["reprovados"] = sorted(n for n in reprov if not _liberada(n))
    est["cortes_postados"] = sorted(set(est.get("cortes_postados") or []) | set(disco.get("cortes_postados") or []))

    presos = _juntar_presos(est.get("presos") or {}, disco.get("presos") or {},
                            (lido.get("presos") or {}) if lido is not None else None, disco_ok)
    # incidente 4: solta só quem está "enviando"; presos_soltar não fica gravado
    for nome in set(est.get("presos_soltar") or []) | set(disco.get("presos_soltar") or []):
        if nome in presos and _status(presos[nome]) == "enviando":
            del presos[nome]
    est["presos"] = presos
    est.pop("presos_soltar", None)

    for chave, valor in disco.items():  # campo que outro programa pôs no arquivo e a rodada não conhece
        if chave not in est and chave != "presos_soltar":
            est[chave] = valor

    _escrever_atomico(json.dumps(est, ensure_ascii=False, indent=1))
    if isinstance(est, _Estado):
        est._lido = copy.deepcopy(dict(est))  # a próxima gravação da rodada compara com o que acabou de gravar


def _escrever_atomico(texto):
    tmp = ESTADO.with_name(f"{ESTADO.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(texto, encoding="utf-8")
    for tentativa in range(50):
        try:
            os.replace(tmp, ESTADO)  # quem lê nunca vê arquivo pela metade
            return
        except PermissionError:  # Windows: alguém está com o arquivo aberto
            time.sleep(0.05 + 0.01 * tentativa)
    try:
        os.replace(tmp, ESTADO)
    finally:
        if tmp.exists():
            tmp.unlink()
