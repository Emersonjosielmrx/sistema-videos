"""Pool de contas do Fish Audio — cada conta sai por um IP Webshare FIXO e EXCLUSIVO (regra do IP único, igual ao
Kaggle: dona 18/11 'as contas já têm um IP designado e é só sair pelo mesmo'). Os IPs rnprmtfo-N vão de 1 a 100 (mesma
conta Webshare rnprmtfo-rotate); os que o Kaggle usa NUNCA são reusados aqui.

    python pool_fish.py status                 # mostra o pool e os IPs livres
    python pool_fish.py montar [N]             # atribui IP livre às próximas N contas não-Kaggle sem IP (padrão 20)
    python pool_fish.py ip <email>             # mostra/garante o IP de uma conta

Guarda a atribuição no cofre (campo fish_proxy = 'rnprmtfo-N') e nunca dá o mesmo N a duas contas.
"""
import io, contextlib, re, sys
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\recapd-ambientes\producao\colab")
import cofre  # noqa: E402

POOL_KAGGLE = Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json")
CRIADOR = Path(r"D:\criador-contas-kaggle")  # reservas de IP do criador de contas do Kaggle (outro chat)
N_MIN, N_MAX = 1, 100  # a conta Webshare rnprmtfo tem 100 IPs


def eh_kaggle(email):
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            return bool(cofre.saida_kaggle(email))
        except Exception:  # noqa: BLE001
            return True  # ponte fora / erro = trata como Kaggle (não arrisca)


def ns_usados():
    """IPs rnprmtfo-N já comprometidos: usados pelo pool do Kaggle, por kaggle_proxy no cofre, ou por fish_proxy."""
    usados = set()
    try:
        usados |= {int(m) for m in re.findall(r"rnprmtfo-(\d+)", POOL_KAGGLE.read_text(encoding="utf-8"))}
    except OSError:
        pass
    # 19/11 (corrida do p100 com o criador do Kaggle): o criador RESERVA o N em saidas_usadas.json / contas_criadas.json
    # (chaves "pN" ou textos rnprmtfo-N) antes de a conta aparecer no kaggle_pool. Sem ler isso, o Fish pegou o 100 que o
    # criador já tinha reservado 6 min antes.
    for arq in (CRIADOR / "saidas_usadas.json", CRIADOR / "contas_criadas.json", CRIADOR / "n_liberados.json"):
        try:
            t = arq.read_text(encoding="utf-8")
        except OSError:
            continue
        usados |= {int(m) for m in re.findall(r"rnprmtfo-(\d+)", t)}
        usados |= {int(m) for m in re.findall(r'"p(\d+)"', t)}
    reg = cofre._ler().get("contas", {})
    for e in reg.values():
        # kaggle_proxy_antigo = IP de conta já BANIDA no Kaggle (19/11): queimado, nunca reusar (2º banimento 09/11)
        # fish_proxy_conflito = IP que o Fish teve que largar porque era do Kaggle (19/11 p100)
        for campo in ("kaggle_proxy", "kaggle_proxy_antigo", "fish_proxy", "fish_proxy_conflito"):
            m = re.match(r"rnprmtfo-(\d+)", str(e.get(campo) or ""))
            if m:
                usados.add(int(m.group(1)))
    return usados


def livres():
    u = ns_usados()
    return [n for n in range(N_MIN, N_MAX + 1) if n not in u]


def pool_atual():
    reg = cofre._ler().get("contas", {})
    return {e_mail: e["fish_proxy"] for e_mail, e in reg.items() if e.get("fish_proxy")}


def _eh_nova(e):
    """Conta ainda no período de conta nova (regra 19/11, ver memória feedback_conta_nova_canal_poucos_lugares)."""
    from datetime import datetime
    ate = str(e.get("nova_ate") or "")
    if ate:
        return ate >= datetime.now().strftime("%Y-%m-%d")
    usos = " ".join(str(v) for v in (e.get("usos") or {}).values()).lower()
    return "canal novo" in usos or "conta nova" in str(e.get("_obs") or "").lower()


def candidatas():
    """Contas não-Kaggle, com Google vivo, ainda sem fish_proxy — as de menos uso em outros serviços primeiro."""
    reg = cofre._ler().get("contas", {})
    out = []
    for email, e in reg.items():
        if "@" not in email or e.get("fish_proxy"):
            continue
        if str(e.get("google")) == "morto":
            continue
        # 20/11 dona: conta tirada do Fish (ex.: msenergypara = cliente MS Energy, fala só pela casa) nunca volta sozinha
        if e.get("fish_removida") or e.get("so_casa"):
            continue
        if eh_kaggle(email):
            continue
        # 19/11 dona (Por Dentro perdido: conta nova do canal foi pro pool do Fish com outro IP no mesmo dia ->
        # "Confirme que é você" e não voltou): conta NOVA fica só no aparelho onde nasceu. Fora do pool: (a) nova_ate
        # no futuro (cofre.marcar_nova), (b) qualquer uso "canal novo" no YouTube, (c) _obs de conta nova sem nova_ate.
        # POOL_FISH_ACEITA_NOVA=1 desliga.
        if __import__("os").environ.get("POOL_FISH_ACEITA_NOVA") != "1" and _eh_nova(e):
            continue
        peso = len(e.get("usos") or {})  # menos serviços = mais seguro = primeiro
        out.append((peso, email))
    out.sort()
    return [e for _, e in out]


def montar(n=20):
    disp = livres()
    cands = candidatas()
    if not disp:
        print("sem IP rnprmtfo livre")
        return
    feitas = []
    for email in cands[:n]:
        if not disp:
            print("acabaram os IPs livres")
            break
        ip = disp.pop(0)
        cofre._marcar(email, fish_proxy=f"rnprmtfo-{ip}")
        feitas.append((email, ip))
        print(f"  {email} -> rnprmtfo-{ip}")
    print(f"pool do Fish: +{len(feitas)} contas | total {len(pool_atual())} | IPs livres restantes {len(disp)}")


def status():
    p = pool_atual()
    print(f"pool do Fish Audio: {len(p)} contas")
    for e_mail, ip in sorted(p.items(), key=lambda kv: int(kv[1].split('-')[1])):
        print(f"  {ip:14s} {e_mail}")
    print(f"IPs rnprmtfo livres: {len(livres())}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "montar":
        montar(int(sys.argv[2]) if len(sys.argv) > 2 else 20)
    elif cmd == "ip":
        email = sys.argv[2]
        reg = cofre._ler().get("contas", {})
        print(reg.get(email.lower(), {}).get("fish_proxy") or "(sem IP; rode: pool_fish.py montar)")
    else:
        status()
