"""etapas.py — videos de todos os projetos e PCs no Google Drive, por projeto e por ETAPA (rede onde ja sairam).

<remoto>/<projeto>/<N>_<rede>/<origem>/<resto>: a pasta e a ULTIMA rede por onde o video ja passou, na ordem do
projeto em config/etapas.json (padrao youtube -> tiktok -> instagram; rede nova = acrescentar na lista). <origem> e o
canal de origem (react), a obra ou o genero; <resto> mantem as subpastas do PC (historia, capitulo), entao nomes
repetidos nao se chocam. Fora das etapas: <projeto>/brutos (Veo cru), <projeto>/_sem_postagem e
manhwa-react/_copias_rede (copias com o @ do canal).

Cada PC anota as postagens SO no seu <remoto>/_registro/<pc>.jsonl; o catalogo (catalogo.py) le os de todos e lista
as pastas de etapa, entao o video que o outro PC postou no YouTube entra no reuso do TikTok/Instagram deste. Mudar de
etapa e moveto no proprio Drive (nada desce). O backup (D:/manhwa-react/scripts/backup_drive.py) poe nas etapas o que
ja foi postado; o TikTok/Instagram chamam registrar() depois de postar.

Uso: python etapas.py [registros | migrar [--simular]]
"""
import argparse
import json
import os
import re
import socket
import subprocess

_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
CONFIG = BIN.parent / "config"
LOGS = BIN.parent / "logs"
RCLONE = r"D:\tools\rclone.exe"
PC = socket.gethostname().lower()
REGISTRO = LOGS / f"registro_etapas_{PC}.jsonl"  # copia local do <remoto>/_registro/<pc>.jsonl deste PC
MANIFESTO = Path(r"D:\manhwa-react\logs\backup_drive.jsonl")  # local -> Drive: o catalogo acha o arquivo por ele
MIGRACAO = LOGS / "migracao_etapas.jsonl"  # de -> para de cada arquivo movido na migracao (para desfazer)
VIDEO = {".mp4", ".mov", ".mkv", ".webm"}
ETAPA = re.compile(r"\d+_[a-z0-9]+")
_cache = {}
_pastas_ok, _trava = set(), threading.Lock()


def cfg():
    return json.loads((CONFIG / "etapas.json").read_text(encoding="utf-8"))


def remoto():
    return cfg()["remoto"]


def ordem(projeto):
    return (cfg()["projetos"].get(projeto) or {}).get("etapas") or cfg()["padrao"]


def so_no_fim(projeto):
    return bool((cfg()["projetos"].get(projeto) or {}).get("so_no_fim"))


def etapa(projeto, redes):
    """Pasta da etapa ("2_tiktok") = a rede mais adiantada da ordem do projeto entre as que o video ja saiu; None se nenhuma."""
    o = ordem(projeto)
    idx = [o.index(r) for r in redes if r in o]
    return f"{max(idx) + 1}_{o[max(idx)]}" if idx else None


def ultima(projeto):
    o = ordem(projeto)
    return f"{len(o)}_{o[-1]}"


def partes(caminho):
    """(projeto, etapa, origem, resto) de um caminho no formato das etapas; None se nao for."""
    pre = remoto() + "/"
    if not str(caminho).startswith(pre):
        return None
    p = str(caminho)[len(pre):].split("/")
    return (p[0], p[1], p[2], "/".join(p[3:])) if len(p) >= 4 and ETAPA.fullmatch(p[1]) else None


def nivel(caminho):
    """Numero da etapa de um caminho no Drive (0 = fora das etapas): o video nunca volta de etapa."""
    p = partes(caminho or "")
    return int(p[1].split("_")[0]) if p else 0


def rede_da_etapa(nome):
    return nome.split("_", 1)[1]


def chave(caminho):
    """O que nao muda quando o video troca de etapa: (projeto, origem, resto); None fora do formato."""
    p = partes(caminho or "")
    return (p[0], p[2], p[3].casefold()) if p else None


def _resto(v):
    """Caminho abaixo da origem: as subpastas do PC (pasta da historia, capitulo) evitam choque de nomes repetidos."""
    pd = partes(v.get("drive") or "")
    if pd and v["caminho"] == v.get("drive"):  # so existe no Drive (veio de outro PC): ja esta no formato
        return pd[3]
    import catalogo
    p = catalogo.pasta_de(v["caminho"])
    if not p:
        return v["nome"]
    rel = Path(v["caminho"]).relative_to(p[0]).parts
    if v.get("origem") and len(rel) > 1 and rel[0].casefold() == v["origem"].casefold():
        rel = rel[1:]
    return "/".join(rel)


def destino(v, redes=()):
    """Caminho no Drive conforme as redes onde o video ja saiu (+ redes): etapa, brutos, copias ou _sem_postagem."""
    base = f"{remoto()}/{v['projeto']}"
    if v["tipo"] == "bruto":
        return f"{base}/brutos/{_resto(v)}"
    if v["tipo"] == "copia" and v["projeto"] == "manhwa-react":
        return f"{base}/_copias_rede/{_resto(v)}"
    et = etapa(v["projeto"], set(redes) | {p["plataforma"] for p in v["postagens"]})
    return f"{base}/{et}/{v.get('origem') or '_'}/{_resto(v)}" if et else f"{base}/_sem_postagem/{_resto(v)}"


def _rclone(*args, timeout=300, log=False):
    """(codigo, saida): stdout se deu certo, stderr se nao; log=True: stdout + stderr (o -v do rclone sai no stderr)."""
    try:
        # 02/11: o manhwa-drive usa o cliente público do rclone (sem chave própria: regra da dona) e o Google
        # devolvia RATE_LIMIT_EXCEEDED -> 300 "não subiu" e rodadas presas horas. --tpslimit segura o ritmo de chamadas.
        r = subprocess.run([RCLONE, *args, "--retries", "3", "--low-level-retries", "10", "--timeout", "60s",
                            "--contimeout", "30s", "--tpslimit", "8", "--tpslimit-burst", "8"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, creationflags=_SEM_JANELA)
    except subprocess.TimeoutExpired:
        return -1, f"passou de {timeout}s"
    if log:
        return r.returncode, (r.stdout + r.stderr).strip()
    return r.returncode, (r.stdout if r.returncode == 0 else (r.stderr or r.stdout)).strip()


# 23/10 (dona: "o Drive recusando por excesso de pedidos"): cada processo (backup de hora em hora, TikTok, Instagram,
# rede, métricas) listava o Drive INTEIRO de novo — a lembrança era só de 2 min e dentro do próprio processo. Agora a
# lista fica num arquivo compartilhado por 20 min; recusa do Google (limite) = usa a última lista boa (até 12 h).
CACHE_LISTA = Path(__file__).resolve().parent.parent / "logs" / "etapas_lista_cache.json"
CACHE_VALE_S, CACHE_RESERVA_S = 20 * 60, 12 * 3600


def _cache_disco():
    try:
        return json.loads(CACHE_LISTA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def invalidar_lista():
    """Este PC mexeu no Drive (moveu/copiou): a próxima listagem busca de novo."""
    _cache.clear()
    try:
        CACHE_LISTA.unlink()
    except OSError:
        pass


def listar():
    """Videos nas pastas de etapa de todos os projetos e PCs: [{'drive', 'bytes'}] (guardado por 20 min, entre processos)."""
    if _cache.get("t", 0) > time.time() - 120:
        return _cache["lista"]
    disco = _cache_disco()
    if disco.get("t", 0) > time.time() - CACHE_VALE_S and disco.get("remoto") == remoto():
        _cache.update(t=time.time(), lista=disco["lista"])
        return disco["lista"]
    # 02/11: --fast-list = listagem em lote (poucas chamadas) em vez de 1 chamada por pasta (milhares por rodada)
    rc, out = _rclone("lsjson", "-R", "--fast-list", "--files-only", "--include", "/*/[0-9]*_*/**", remoto(),
                      timeout=900)
    if rc:
        if disco.get("lista") is not None and disco.get("t", 0) > time.time() - CACHE_RESERVA_S:
            return disco["lista"]  # Google recusou (limite/rede): a lista de antes serve
        raise RuntimeError(f"rclone lsjson {rc}: {out[-300:]}")
    lista = [{"drive": f"{remoto()}/{f['Path']}", "bytes": f["Size"]} for f in json.loads(out or "[]")
             if Path(f["Path"]).suffix.lower() in VIDEO]
    _cache.update(t=time.time(), lista=lista)
    try:
        tmp = CACHE_LISTA.with_suffix(".tmp")
        tmp.write_text(json.dumps({"t": time.time(), "remoto": remoto(), "lista": lista}), encoding="utf-8")
        tmp.replace(CACHE_LISTA)
    except OSError:
        pass
    return lista


def ler_registros():
    """Postagens anotadas por todos os PCs (<remoto>/_registro/*.jsonl); a deste PC vem da copia local (vale mesmo se a
    ultima nao subiu)."""
    rc, out = _rclone("cat", f"{remoto()}/_registro", "--filter", f"- /{PC}.jsonl", "--filter", "+ *.jsonl",
                      "--filter", "- *")
    if rc == 3:  # a pasta ainda nao existe: nenhum PC anotou nada
        out = ""
    elif rc:
        raise RuntimeError(f"rclone cat {rc}: {out[-300:]}")
    if REGISTRO.exists():
        out += "\n" + REGISTRO.read_text(encoding="utf-8")
    regs = []
    for linha in out.splitlines():
        try:
            regs.append(json.loads(linha))
        except ValueError:
            continue
    return regs


def anotar(v, drive, postagens):
    """Acrescenta postagens do video ao registro deste PC (local; publicar_registro() sobe pro Drive)."""
    LOGS.mkdir(parents=True, exist_ok=True)
    em = datetime.now().astimezone().isoformat(timespec="seconds")
    with open(REGISTRO, "a", encoding="utf-8") as f:
        for p in postagens:
            f.write(json.dumps({"em": em, "pc": PC, "projeto": v["projeto"], "origem": v.get("origem") or "",
                                "nome": v["nome"], "drive": drive, "plataforma": p["plataforma"], "conta": p.get("conta"),
                                "id": p.get("id"), "quando": p.get("quando")}, ensure_ascii=False) + "\n")


def publicar_registro():
    if REGISTRO.exists():
        rc, msg = _rclone("copyto", str(REGISTRO), f"{remoto()}/_registro/{PC}.jsonl")
        if rc:
            print(f"etapas: o registro nao subiu pro Drive ({msg[-200:]}); sobe na proxima postagem")


def _manifesto(local, drive, nome, tam):
    MANIFESTO.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFESTO, "a", encoding="utf-8") as m:
        m.write(json.dumps({"em": datetime.now().astimezone().isoformat(timespec="seconds"), "local": local,
                            "drive": drive, "nome": nome, "bytes": tam}, ensure_ascii=False) + "\n")


def _remanifestar(movidos):
    """O catalogo acha no Drive o video deste PC pelo manifesto (vale a ultima linha): linha nova para cada um movido."""
    if not movidos or not MANIFESTO.exists():
        return
    ultimo = {}
    for linha in MANIFESTO.read_text(encoding="utf-8").splitlines():
        r = json.loads(linha)
        if r.get("drive") and r.get("local"):
            ultimo[r["local"]] = r
    for r in ultimo.values():
        if r["drive"] in movidos:
            _manifesto(r["local"], movidos[r["drive"]], r["nome"], r["bytes"])


def garantir(pasta):
    """Cria a pasta no Drive (e as de cima) um rclone de cada vez neste PC: dois criando a mesma pasta juntos = duas
    pastas com o mesmo nome, e o rclone so enxerga uma (16/10 havia 2 'veo' e 2 'rede_marca', do backup em paralelo)."""
    if pasta in _pastas_ok:
        return
    import msvcrt
    with _trava:
        if pasta in _pastas_ok:
            return
        LOGS.mkdir(parents=True, exist_ok=True)
        with open(LOGS / "etapas_mkdir.lock", "a+b") as f:  # trava entre processos (backup x TikTok x Instagram)
            while True:
                try:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.5)
            try:
                rc, msg = _rclone("mkdir", pasta)
            finally:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        if rc:
            raise RuntimeError(f"rclone mkdir {pasta}: {msg[-200:]}")
        _pastas_ok.add(pasta)


def _mover(de, para):
    """Move no proprio Drive o video e o que e dele na mesma pasta (capa, textos); numa pasta de historia (tem
    postar.json) a pasta inteira, para as 2 versoes, o postar.json e as capas nao se separarem.
    Devolve ({caminho antigo: novo} dos videos movidos, erros)."""
    dir_de, nome = de.rsplit("/", 1)
    dir_para = para.rsplit("/", 1)[0]
    invalidar_lista()  # o Drive vai mudar: a lista guardada deixa de valer
    rc, out = _rclone("lsjson", "--files-only", dir_de)
    nomes = [f["Name"] for f in json.loads(out or "[]")] if rc == 0 else [nome]
    try:
        garantir(dir_para)
    except RuntimeError as e:
        return {}, [str(e)]
    if "postar.json" in nomes:
        rc, msg = _rclone("move", dir_de, dir_para, "--delete-empty-src-dirs", timeout=1800)
        if rc:
            return {}, [f"{dir_de}: {msg[-200:]}"]
        return {f"{dir_de}/{n}": f"{dir_para}/{n}" for n in nomes if Path(n).suffix.lower() in VIDEO}, []
    stem = Path(nome).stem
    juntos = [n for n in nomes if n == nome or (n.startswith((stem + ".", stem + "_")) and Path(n).suffix.lower() not in VIDEO)]
    movidos, erros = {}, []
    for n in juntos:
        rc, msg = _rclone("moveto", f"{dir_de}/{n}", f"{dir_para}/{n}", timeout=600)
        if rc:
            erros.append(f"{n}: {msg[-200:]}")
        elif n == nome:
            movidos[de] = para
    return movidos, erros


def registrar(v, rede, conta, vid=None):
    """Depois de postar v (item do catalogo) em `rede`: anota no registro deste PC e, se o arquivo ja esta no Drive, muda de
    etapa. Devolve o caminho novo no Drive (None se nao mudou)."""
    novo = None
    if v.get("drive") and not v.get("no_pc"):
        alvo = destino(v, {rede})
        if nivel(alvo) > nivel(v["drive"]):
            movidos, erros = _mover(v["drive"], alvo)
            if erros:
                print(f"etapas: {v['nome']} nao mudou de etapa ({erros[0]})")
            _remanifestar(movidos)
            novo = movidos.get(v["drive"])
    anotar(v, novo or v.get("drive"), [{"plataforma": rede, "conta": conta, "id": vid,
                                        "quando": datetime.now().astimezone().isoformat(timespec="seconds")}])
    publicar_registro()
    return novo


def migrar(simular):
    """Uma vez (16/10): do espelho antigo do PC no Drive para as etapas, conforme as postagens do catalogo."""
    import catalogo
    # antes de tudo junta as pastas repetidas (o rclone so enxerga uma: os arquivos da outra sumiriam do plano)
    rc, msg = _rclone("dedupe", "--dedupe-mode", "skip", "-v", *(["--dry-run"] if simular else []), remoto(), timeout=1800,
                     log=True)
    juntas = [l.split(": ", 1)[-1] for l in msg.splitlines() if "duplicate directories" in l] if rc == 0 else [msg[-200:]]
    print(f"pastas repetidas no Drive {'a juntar' if simular else 'juntadas'}: {len(juntas)}")
    for l in juntas:
        print(f"  {l}")
    cat = catalogo.sincronizar()
    plano = [(v, destino(v)) for v in cat["videos"]
             if v.get("drive") and v["caminho"] != v["drive"] and not partes(v["drive"])]
    plano = [(v, alvo) for v, alvo in plano if alvo != v["drive"]]
    # historia: a pasta inteira (v1_FINAL, v1_FINAL_ULTIMO, postar.json, capas) vai junto, na etapa do video mais adiantado
    historias, tarefas = defaultdict(list), []
    for v, alvo in plano:
        if v["projeto"] == "historias-em-frames":
            historias[v["drive"].rsplit("/", 1)[0]].append((v, alvo))
        else:
            tarefas.append([(v, alvo)])
    for grupo in historias.values():
        dir_para = max(grupo, key=lambda x: nivel(x[1]))[1].rsplit("/", 1)[0]
        tarefas.append([(v, f"{dir_para}/{a.rsplit('/', 1)[1]}") for v, a in grupo])
    por_pasta = Counter()
    for itens in tarefas:
        for v, alvo in itens:
            por_pasta["/".join(alvo[len(remoto()) + 1:].split("/")[:2])] += 1
    print(f"migracao: {len(plano)} video(s) do espelho antigo para as etapas")
    for k, n in sorted(por_pasta.items()):
        print(f"  {k:45} {n:5}")
    if simular:
        lista = LOGS / "migracao_etapas_simulacao.txt"
        lista.write_text("\n".join(f"{v['drive']}  ->  {a}" for itens in tarefas for v, a in itens), encoding="utf-8")
        print(f"lista completa (de -> para): {lista}")
        return
    pastas = sorted({a.rsplit("/", 1)[0] for itens in tarefas for _, a in itens})
    print(f"criando {len(pastas)} pasta(s), uma de cada vez")
    for d in pastas:
        garantir(d)

    def uma(itens):
        movidos, erros = {}, []
        for v, alvo in itens:
            if v["drive"] not in movidos:  # historia com postar.json: o 1o ja leva a pasta toda
                m, e = _mover(v["drive"], alvo)
                movidos.update(m)
                erros += e
        return itens, movidos, erros

    feitos = falhas = 0
    pendentes = {}
    with ThreadPoolExecutor(3) as ex:  # 3 ao mesmo tempo, como o backup
        for i, (itens, movidos, erros) in enumerate(ex.map(uma, tarefas), 1):
            pendentes.update(movidos)
            for v, _ in itens:
                novo = movidos.get(v["drive"])
                if not novo:
                    falhas += 1
                    print(f"  NAO MOVEU {v['drive']}: {(erros or ['nao achou no Drive'])[0]}")
                    continue
                with open(MIGRACAO, "a", encoding="utf-8") as m:
                    m.write(json.dumps({"de": v["drive"], "para": novo}, ensure_ascii=False) + "\n")
                if v["postagens"]:
                    anotar(v, novo, v["postagens"])
                feitos += 1
            if i % 50 == 0 or i == len(tarefas):
                _remanifestar(pendentes)
                pendentes = {}
                print(f"  {i}/{len(tarefas)}")
    publicar_registro()
    print(f"migracao: {feitos} video(s) movidos, {falhas} com erro (ficam onde estavam; rodar de novo repete so eles)")
    for raiz in sorted({"/".join(v["drive"][len(remoto()) + 1:].split("/")[:2]) for v, _ in plano}):
        _rclone("rmdirs", f"{remoto()}/{raiz}", timeout=900)  # so as pastas que ficaram vazias
        rc, out = _rclone("lsf", "-R", "--files-only", f"{remoto()}/{raiz}")
        sobra = out.splitlines() if rc == 0 else []
        if sobra:
            print(f"  ficou em {raiz}: {len(sobra)} arquivo(s) sem video do catalogo (ex.: {sobra[0]})")


def main():
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="registros", choices=["registros", "migrar"])
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()
    if a.cmd == "migrar":
        migrar(a.simular)
    else:
        c = Counter((r.get("pc"), r.get("plataforma")) for r in ler_registros())
        for (pc, plat), n in sorted(c.items()):
            print(f"  {pc:20} {plat:12} {n}")


if __name__ == "__main__":
    main()
