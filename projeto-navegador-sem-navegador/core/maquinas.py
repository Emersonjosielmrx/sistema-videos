# -*- coding: utf-8 -*-
r"""core/maquinas.py — "rode onde o cookie está" (29/10, D31; dona: "tudo isso tem que rodar em todos os notebooks e
PCs"). Cada máquina (x200ma, acer, pc2, desktop) tem o nsn_worker com os cookies DELA (D23, nunca copiados). Qualquer
comando do nsn (postar, quero, fotos_http, web...) pode rodar no PC1 com os cookies daqui OU numa máquina que tenha o
cookie do perfil, pelo ssh do postador (maquina_remota.Remoto.nsn_run). Este módulo decide e despacha.

    from core.maquinas import ou_remoto
    def main():
        if ou_remoto("ig_" + conta, "services.instagram.postar", enviar=[video]) is not None: return   # rodou lá
        ...                                                                                            # roda aqui

Regra: cookie aqui no PC1 -> roda aqui (None). Sem cookie aqui e alguma máquina tem -> roda LÁ, imprime a saída de lá
e devolve (rc, saída). `--maquina <nome>` na linha de comando força a máquina; `--local` força aqui. Dentro do worker
(nas máquinas) o postador não existe: devolve None sempre (roda local lá).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTADOR = r"D:\postador-de-videos\bin"


def _mr():
    try:
        if POSTADOR not in sys.path:
            sys.path.append(POSTADOR)
        import maquina_remota
        return maquina_remota
    except Exception:  # noqa: BLE001 — nas máquinas (worker) não há postador: tudo é local
        return None


def local_tem(perfil, google=False):
    try:
        d = json.loads((ROOT / "cookies" / f"cofre_{perfil}.json").read_text("utf-8"))
    except (OSError, ValueError):
        return False
    nomes = ("SID", "__Secure-1PSID") if google else ("sessionid",)
    return any(c.get("name") in nomes for c in d.get("cookies", []))


def onde_tem(perfil, google=False, maquinas=None):
    """Máquinas (na ordem do postador) que já colheram o cookie desse perfil."""
    mr = _mr()
    if not mr:
        return []
    out = []
    for nome in (maquinas or sorted(mr.MAQUINAS, key=lambda m: mr.ORDEM_NAVEGADOR.get(m, 9))):
        r = mr.Remoto(nome)
        try:
            if not r.vivo():
                continue
            if (r.nsn_tem_google(perfil) if google else r.nsn_tem_cookie(perfil)):
                out.append(nome)
        except Exception:  # noqa: BLE001
            continue
    return out


def ou_remoto(perfil, modulo, argv=None, google=False, enviar=(), receber=(), timeout=900):
    """None = rode aqui. (rc, saida) = rodou numa máquina (a saída de lá já foi impressa)."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--local" in argv:
        return None
    forcada = None
    if "--maquina" in argv:
        i = argv.index("--maquina")
        if i + 1 >= len(argv) or argv[i + 1].startswith("-"):
            raise SystemExit("--maquina precisa do nome da máquina (ex.: --maquina x200ma)")
        forcada = argv[i + 1]
    argv = [a for i, a in enumerate(argv) if a not in ("--maquina", "--local") and (i == 0 or argv[i - 1] != "--maquina")]
    if not forcada and local_tem(perfil, google):
        return None
    mr = _mr()
    if not mr:
        return None
    maqs = [forcada] if forcada else onde_tem(perfil, google)
    if not maqs:
        return None
    r = mr.Remoto(maqs[0])
    print(f"[nsn] {perfil}: sem cookie neste PC — rodando no {maqs[0]} com os cookies de lá", flush=True)
    rc, saida = r.nsn_run(modulo, argv, enviar=enviar, receber=receber, timeout=timeout)
    print(saida.rstrip(), flush=True)
    return rc, saida
