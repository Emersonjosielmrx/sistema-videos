"""fila_render.py — vez de render pesado entre os projetos de vídeo deste PC (dono, 17/10/2026: "fazer uma filinha
pros projetos não se atrapalharem entre si"). Em 17/10 às 7h o PC estava com 1,1 GB de RAM livre: hipercool,
anime longo, postagem e Shorts do parceiro renderizando juntos, cada um sem saber dos outros.

Uso (no ponto onde o projeto começa UM render pesado):
    sys.path.insert(0, r"D:\\video-fila"); import fila_render
    with fila_render.vez("parceiro", "Short kaijinre X"):
        ...render...

- `fila.json` aqui: quantos renders ao mesmo tempo (slots) e a prioridade de cada projeto (menor = antes).
- Quem espera grava um arquivo em estado/esperando; a vez vai pro de MAIOR prioridade (empate: quem chegou antes).
- Vez de processo que morreu ou passou de max_h é liberada sozinha. TTS e postagem NÃO entram (são leves).
- Falhou a fila (pasta sumiu, erro) = o render segue sem esperar: a fila nunca pode parar a produção.
- `python fila_render.py` mostra quem está renderizando e quem espera.
"""
import contextlib
import json
import os
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
EST = BASE / "estado"
CFG = BASE / "fila.json"
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _cfg():
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"slots": 1, "max_h": 6, "prioridade": {}}


def _vivo(pid):
    try:
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", creationflags=_SEM_JANELA, timeout=30)
        return str(pid) in (r.stdout or "")
    except Exception:  # noqa: BLE001
        return True


def _ler(pasta, max_h):
    out = []
    for p in (EST / pasta).glob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if time.time() - d.get("desde", 0) > max_h * 3600 or not _vivo(d.get("pid", 0)):
            p.unlink(missing_ok=True)  # morto ou esquecido: libera
            continue
        out.append((p, d))
    return out


def _pastas(maquina):
    """PC1 usa rodando/esperando (como sempre); outra máquina (pc2, desktop) tem a fila dela, mesma prioridade."""
    return ("rodando", "esperando") if maquina == "pc1" else (f"rodando_{maquina}", f"esperando_{maquina}")


@contextlib.contextmanager
def vez(projeto, rotulo="", espera_max_h=None, maquina="pc1"):
    """Bloqueia até ter vez; libera ao sair do `with`. maquina="pc2"/"desktop" (18/10): o despacho pra outra máquina
    (hipercool fila.py pc2, anime ocioso.py) segura a vez dela enquanto confere e dispara, e os dois não disparam juntos."""
    meu = None
    try:
        c = _cfg()
        prio = int(c.get("prioridade", {}).get(projeto, 9))
        p_rod, p_esp = _pastas(maquina)
        for sub in (p_rod, p_esp):
            (EST / sub).mkdir(parents=True, exist_ok=True)
        nome = f"{projeto}_{os.getpid()}_{int(time.time() * 1000)}.json"
        info = {"projeto": projeto, "rotulo": rotulo[:120], "pid": os.getpid(), "prio": prio, "desde": time.time()}
        esp = EST / p_esp / nome
        esp.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
        limite = time.time() + (espera_max_h or c.get("espera_max_h", 8)) * 3600
        avisou = False
        while True:
            c = _cfg()
            rod = _ler(p_rod, c.get("max_h", 6))
            fila = sorted(_ler(p_esp, 24), key=lambda x: (x[1]["prio"], x[1]["desde"]))
            slots = c.get("slots", 1) if maquina == "pc1" else (c.get("slots_maquina") or {}).get(maquina, 1)
            livres = int(slots) - len(rod)
            posicao = next((i for i, x in enumerate(fila) if x[0].name == nome), 0)
            if livres > posicao or time.time() > limite:
                meu = EST / p_rod / nome
                info["desde"] = time.time()
                meu.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
                esp.unlink(missing_ok=True)
                break
            if not avisou:
                ocup = ", ".join(f"{d['projeto']} ({d['rotulo'][:40]})" for _, d in rod) or "-"
                print(f"[fila_render] {projeto}: esperando a vez (rodando: {ocup}; {posicao} na frente)", flush=True)
                avisou = True
            time.sleep(20)
    except Exception as e:  # noqa: BLE001
        print(f"[fila_render] fila indisponível ({type(e).__name__}: {e}) — segue sem esperar", flush=True)
    try:
        yield
    finally:
        if meu:
            meu.unlink(missing_ok=True)


def marcar(projeto, rotulo, pid, maquina):
    """Registra um processo que já está rodando (pid) como ocupando a máquina até ele morrer — pro despacho que
    dispara um filho longo (anime_auto do modo ocioso usa o PC2 por horas, mas só aparece lá minutos depois)."""
    try:
        p_rod, _ = _pastas(maquina)
        (EST / p_rod).mkdir(parents=True, exist_ok=True)
        info = {"projeto": projeto, "rotulo": rotulo[:120], "pid": int(pid),
                "prio": int(_cfg().get("prioridade", {}).get(projeto, 9)), "desde": time.time()}
        (EST / p_rod / f"{projeto}_{pid}_{int(time.time() * 1000)}.json").write_text(
            json.dumps(info, ensure_ascii=False), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"[fila_render] não marcou {projeto} em {maquina} ({e})", flush=True)


def ocupando(maquina, fora_pid=None):
    """[(projeto, rótulo)] de quem tem a vez (ou foi marcado) nesta máquina, sem contar o próprio processo."""
    p_rod, _ = _pastas(maquina)
    return [(d["projeto"], d.get("rotulo", "")) for _p, d in _ler(p_rod, _cfg().get("max_h", 6))
            if d.get("pid") != (fora_pid or os.getpid())]


def status():
    c = _cfg()
    rod, fila = _ler("rodando", c.get("max_h", 6)), _ler("esperando", 24)
    print(f"slots: {c.get('slots', 1)} | prioridade: {c.get('prioridade')}")
    for tit, lst in (("RODANDO", rod), ("ESPERANDO", sorted(fila, key=lambda x: (x[1]["prio"], x[1]["desde"])))):
        print(tit)
        for _, d in lst:
            print(f"  {d['projeto']:10} pid {d['pid']:6} há {(time.time() - d['desde']) / 60:5.0f} min  {d['rotulo']}")


if __name__ == "__main__":
    status()
