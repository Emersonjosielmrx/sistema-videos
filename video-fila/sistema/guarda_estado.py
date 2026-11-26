# D:\sistema\catalogo\guarda_estado.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/guarda_estado.py)
# OBRA sistema unico - GUARDIAO DOS ARQUIVOS DE ESTADO (tarefa GuardaEstado, a cada 10 min). Protege TODOS os projetos
# sem mexer em nenhum programa. Motivo: 21/11 o PC1 desligou no meio de uma gravacao, 2 JSON ficaram com 0 byte e o
# Recap ficou 5 dias travado sem ninguem saber.
#   - guarda a ultima versao BOA (JSON valido) de cada .json de controle em D:\sistema\mapa\estado_bak\<pasta>__<nome>\
#     (so quando mudou; ate 24 versoes por arquivo);
#   - se um arquivo esta com 0 byte ou JSON quebrado E continua assim depois de 15 s (nao e gravacao em andamento) E nao
#     foi mexido no ultimo minuto: restaura a ultima versao boa (o quebrado fica em ...\quebrado_<hora>.json) e avisa.
#   python guarda_estado.py            uma passada        python guarda_estado.py --status
# GUARDA_ESTADO_RESTAURAR=0 = so avisa, nao restaura.
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
BAK = Path(r"D:\sistema\mapa\estado_bak")
LOG = Path(r"D:\sistema\mapa\guarda_estado.log")
PASTAS = [r"D:\video-fila\estado", r"D:\video-fila", r"D:\recap_central_casa", r"D:\recapd-ambientes\producao\colab",
          r"D:\recapd-ambientes\producao\config", r"D:\postador-de-videos\config", r"D:\postador-de-videos\logs",
          r"D:\projeto celular sub controle\canal_pronto", r"D:\hipercool-materiais\comum", r"D:\ms-energy\config",
          r"D:\gemini-argo", r"D:\sonnet web", r"D:\opus-gratis-v2-desktop", r"D:\criador-contas-kaggle",
          r"D:\manhwa-react\config", r"D:\logins-google\cofre", r"D:\kit3d-producao", r"D:\tools\drive_central",
          r"D:\sistema\catalogo"]
MAX_VERSOES = 24
MAX_BYTES = 5_000_000


def log(msg):
    BAK.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(time.strftime("[%d/%m %H:%M:%S] ") + msg + "\n")


def avisar(txt):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(txt, "guarda-estado", importante=True)
    except Exception:  # noqa: BLE001
        pass


def valido(p):
    try:
        if os.path.getsize(p) == 0:
            return False
        with open(p, encoding="utf-8-sig") as fh:
            json.load(fh)
        return True
    except (OSError, ValueError):
        return False


def pasta_bak(p):
    return BAK / (str(p.parent).replace(":", "").replace("\\", "_").strip("_") + "__" + p.name)


def ultima_boa(p):
    d = pasta_bak(p)
    for v in sorted(d.glob("v_*.json"), reverse=True):
        if valido(v):
            return v
    return None


def guardar(p):
    d = pasta_bak(p)
    d.mkdir(parents=True, exist_ok=True)
    dado = p.read_bytes()
    h = hashlib.md5(dado).hexdigest()[:10]
    if (d / "ultimo_hash").exists() and (d / "ultimo_hash").read_text() == h:
        return
    (d / f"v_{time.strftime('%Y%m%d_%H%M%S')}.json").write_bytes(dado)
    (d / "ultimo_hash").write_text(h)
    for velho in sorted(d.glob("v_*.json"))[:-MAX_VERSOES]:
        velho.unlink()


def passada():
    agora = time.time()
    suspeitos = []
    n = 0
    for pasta in PASTAS:
        try:
            nomes = os.listdir(pasta)
        except OSError:
            continue
        for nome in nomes:
            if not nome.lower().endswith(".json"):
                continue
            p = Path(pasta) / nome
            try:
                st = p.stat()
            except OSError:
                continue
            if not p.is_file() or st.st_size > MAX_BYTES or agora - st.st_mtime > 30 * 86400:
                continue
            n += 1
            if valido(p):
                try:
                    guardar(p)
                except OSError:
                    pass
            else:
                suspeitos.append((p, st.st_mtime, st.st_size))
    restaurados = []
    if suspeitos:
        time.sleep(15)  # gravacao em andamento termina em menos que isso
    for p, mt, tam in suspeitos:
        try:
            st = p.stat()
        except OSError:
            continue
        if valido(p) or st.st_mtime != mt or time.time() - st.st_mtime < 60:
            continue  # se resolveu sozinho ou alguem ainda mexendo
        boa = ultima_boa(p)
        motivo = "0 byte" if tam == 0 else "JSON quebrado"
        if not boa:
            log(f"QUEBRADO SEM COPIA BOA: {p} ({motivo})")
            avisar(f"Arquivo de controle {motivo} e sem copia boa para restaurar: {p}")
            continue
        if os.environ.get("GUARDA_ESTADO_RESTAURAR", "1") == "0":
            log(f"QUEBRADO (so aviso): {p} ({motivo}); copia boa: {boa.name}")
            avisar(f"Arquivo de controle {motivo}: {p} (copia boa {boa.name}; restauracao desligada)")
            continue
        quebrado = pasta_bak(p) / f"quebrado_{time.strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(p, quebrado)
        tmp = str(p) + ".tmp_guarda"
        shutil.copy2(boa, tmp)
        os.replace(tmp, p)
        restaurados.append(f"{p} <- {boa.name}")
        log(f"RESTAURADO: {p} ({motivo}) <- {boa.name} (quebrado guardado em {quebrado.name})")
    if restaurados:
        avisar("Guardião de estado restaurou arquivo(s) de controle quebrado(s) (o PC desligou no meio?):\n" + "\n".join(restaurados))
    return n, len(suspeitos), restaurados


if __name__ == "__main__":
    if "--status" in sys.argv:
        print(f"copias em {BAK}: {sum(1 for _ in BAK.glob('*/v_*.json'))} versoes de {sum(1 for _ in BAK.glob('*'))} arquivos")
        if LOG.exists():
            print("\n".join(LOG.read_text(encoding="utf-8").splitlines()[-10:]))
    else:
        n, s, r = passada()
        print(f"[GUARDA ESTADO] {n} arquivos de controle conferidos | suspeitos {s} | restaurados {len(r)}")
