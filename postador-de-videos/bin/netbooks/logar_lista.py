"""logar_lista.py — a fila de contas que a dona loga nos notebooks, uma por vez (23/10/2026: "começa com essas, as que
tiverem canais já no PC1"). Um comando por conta:

    python bin\\netbooks\\logar_lista.py seguinte     # confere+ativa a conta aberta e abre a PRÓXIMA com o e-mail digitado
    python bin\\netbooks\\logar_lista.py abrir        # só (re)abre a conta da vez, com o e-mail digitado
    python bin\\netbooks\\logar_lista.py pular        # deixa a conta da vez pra depois e abre a próxima
    python bin\\netbooks\\logar_lista.py estado       # onde está a fila

A dona faz o resto na tela (verificação "não sou um robô", senha, código). Senha nunca passa por aqui.
Fora da lista (sem cadastro no PC1, 23/10): inovaremanhwaverse3, inovaremanhwaverse4, msenergypara, revolutionemerson7;
canalalucinaai posta pelo perfil antigo (porta 9222) e precisa ser cadastrado no cofre antes.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import maquina_remota as mr  # noqa: E402

FILA = Path(__file__).resolve().parent.parent.parent / "config" / "netbooks_fila.json"
CONTAS = [  # ordem da dona (23/10)
    "Inovaremanhwaversethai@gmail.com", "Inovaremanhwaverseviet@gmail.com", "Inovaremanhwaversehindi@gmail.com",
    "Inovaremanhwaverserussian@gmail.com", "Inovaremanhwaversefrench@gmail.com", "Inovaremanhwaverseita@gmail.com",
    "inovaremanhwaverseesp@gmail.com", "inovaremanhwaverseind@gmail.com", "inovaremanhwaverseing@gmail.com",
    "inovaremanhwaverse@gmail.com", "inovaremanhwabr@gmail.com", "mentoriaiapro@gmail.com", "filmescomia00@gmail.com",
    "jogoscomia@gmail.com", "entrevistacomia@gmail.com", "jornalcomia@gmail.com", "canalhistoriacomia@gmail.com",
    "aulacomia@gmail.com", "comoseriasecomia@gmail.com", "revolutionemerson1@gmail.com", "revolutionemerson2@gmail.com",
    "revolutionemerson3@gmail.com", "rezaulkarimul355@gmail.com", "emersonjosiel2026@gmail.com",
    "emersonjosiel2027@gmail.com", "emersonjosiel2029@gmail.com", "emersonjosiel2030@gmail.com",
    "emersonjosiel2031@gmail.com", "emersonjosiel2032@gmail.com",
    "emersonjosiel2035@gmail.com",  # dona 12/11: conta nova, ainda sem canal na config
]


def _perfil(email):
    return email.split("@")[0].lower()


def _ler():
    try:
        return json.loads(FILA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"atual": None, "feitas": [], "puladas": []}


def _gravar(est):
    FILA.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")


def _proxima(est):
    for e in CONTAS:
        p = _perfil(e)
        if p not in est["feitas"] and p not in est["puladas"] and p != est.get("atual"):
            return e
    return None


def _abrir(email):
    import email_login
    for m in ("x200ma", "acer"):
        try:
            email_login.um(m, _perfil(email), email)
        except Exception as ex:  # noqa: BLE001
            print(f"{m}: não abriu ({type(ex).__name__}: {str(ex)[:120]}) — rode de novo: logar_lista.py abrir")


def desktop(est):
    """Fila do DESKTOP (dona 23/10: "coloca as contas lá também"): anda sozinha, atrás dos notebooks. Confere a da vez
    (Studio abre logado?) e abre a próxima com o e-mail digitado."""
    import desktop_login
    feitas = est.setdefault("desktop_feitas", [])
    atual = est.get("desktop_atual")
    if atual:
        if not desktop_login.conferir(atual):
            print(f"desktop: {atual} NÃO ficou logado. Termine na tela e rode 'desktop' de novo.")
            return
        feitas.append(atual)
        est["desktop_atual"] = None
    email = next((e for e in CONTAS if _perfil(e) not in feitas and _perfil(e) not in est["puladas"]), None)
    if not email:
        _gravar(est)
        print("desktop: fila terminada.")
        return
    est["desktop_atual"] = _perfil(email)
    _gravar(est)
    print(f"\n== desktop: abrindo {email}")
    desktop_login.abrir(_perfil(email), email)
    print("Na tela do desktop: verificação, senha, código. Depois: python bin\\netbooks\\logar_lista.py desktop")


def main(cmd):
    est = _ler()
    est.setdefault("feitas", [])
    est.setdefault("puladas", [])
    if cmd == "desktop":
        return desktop(est)
    if cmd == "estado":
        print(f"feitas {len(est['feitas'])}/{len(CONTAS)}: {', '.join(est['feitas']) or '-'}")
        print(f"da vez: {est.get('atual') or '-'} | puladas: {', '.join(est['puladas']) or '-'}")
        print(f"próxima: {_proxima(est) or 'nenhuma'}")
        return
    if cmd == "seguinte" and est.get("atual"):
        ok = mr.ativar(est["atual"]) == 0
        if not ok:
            print(f"\n{est['atual']} NÃO ficou logado. Termine o login nos notebooks e rode 'seguinte' de novo "
                  f"(ou 'abrir' pra reabrir a janela com o e-mail).")
            return
        est["feitas"].append(est["atual"])
        est["atual"] = None
    elif cmd == "pular" and est.get("atual"):
        est["puladas"].append(est["atual"])
        est["atual"] = None
    if cmd == "abrir" and est.get("atual"):
        email = next(e for e in CONTAS if _perfil(e) == est["atual"])
    else:
        email = _proxima(est)
        if not email:
            _gravar(est)
            print("Fila terminada.")
            return
        est["atual"] = _perfil(email)
    _gravar(est)
    print(f"\n== abrindo {email} nos 2 notebooks")
    _abrir(email)
    print(f"\nNa tela: verificação (se pedir), senha, código. Depois: python bin\\netbooks\\logar_lista.py seguinte")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1] if len(sys.argv) > 1 else "estado")
