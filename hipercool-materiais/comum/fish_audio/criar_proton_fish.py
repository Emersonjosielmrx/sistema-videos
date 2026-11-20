r"""criar_proton_fish.py — cria UMA caixa Proton NOVA só pro Fish, pelo IP rnprmtfo-N do Fish (nunca tocou o Kaggle),
usando a receita do criador do Kaggle (criar_proton.py: apita e espera a DONA resolver o captcha do Proton).

Dona 19/11: "crie da mesma forma que faz pra conta Kaggle, com aviso pra eu resolver o captcha". O Fish recusa e-mail
descartável ("Não é possível usar endereços de e-mail descartáveis") e os Proton que existem são das contas VIVAS do
Kaggle (proibido: ligaria a viva à casa). Então: caixa Proton nova, por um IP do Fish.

Depois de criar, a caixa sai de caixas_email.json do criador (lá ela marcaria "pN" e o pool_fish acharia que o IP é do
Kaggle) e vai para caixas_fish.json aqui.

    python criar_proton_fish.py <N>
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CRIADOR = Path(r"D:\criador-contas-kaggle")
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(CRIADOR))
sys.path.insert(0, r"D:\logins-google")

import criar_fish_mao as cfm  # noqa: E402  (checar_ip: IP do Fish, nunca Kaggle, máx 2)

CAIXAS_CRIADOR = CRIADOR / "caixas_email.json"
CAIXAS_FISH = AQUI / "caixas_fish.json"


def mover_para_fish(n):
    """Tira do caixas_email.json do criador as caixas com saida pN (feitas agora pro Fish) e grava em caixas_fish.json."""
    todas = json.loads(CAIXAS_CRIADOR.read_text(encoding="utf-8"))
    minhas = [c for c in todas if c.get("saida") == f"p{n}"]
    resto = [c for c in todas if c.get("saida") != f"p{n}"]
    CAIXAS_CRIADOR.write_text(json.dumps(resto, ensure_ascii=False, indent=1), encoding="utf-8")
    fish = json.loads(CAIXAS_FISH.read_text(encoding="utf-8")) if CAIXAS_FISH.exists() else []
    for c in minhas:
        c["fish_proxy"] = f"rnprmtfo-{n}"
        c["uso"] = "Fish Audio (dona 19/11) — NUNCA usar no Kaggle"
        fish = [x for x in fish if x.get("email") != c["email"]] + [c]
    CAIXAS_FISH.write_text(json.dumps(fish, ensure_ascii=False, indent=1), encoding="utf-8")
    return minhas


def main(n):
    cfm.checar_ip(n)
    import criar_proton
    try:
        criar_proton.main(n)
    finally:
        feitas = mover_para_fish(n)
        for c in feitas:
            print(f"CAIXA: {c['email']} | senha {c['senha']} | resultado {c.get('resultado') or c.get('erro', '')[:80]}",
                  flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]))
