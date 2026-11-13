import json, re, subprocess, sys, urllib.request

sql = open(sys.argv[1], encoding="utf-8").read()
prompt = re.search(r"\$prompt\$(.*)\$prompt\$", sql, re.S).group(1)

key = subprocess.run(
    ["sudo", "-u", "postgres", "psql", "-d", "wacalls_main", "-t", "-A", "-c",
     "SELECT api_key FROM credentials WHERE user_id='4e8adf4a-6530-47e2-af4c-1c268e6e68d7' AND provider='gemini' ORDER BY created_at DESC LIMIT 1"],
    capture_output=True, text=True).stdout.strip()

URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key=" + key


def ask(history):
    body = {
        "systemInstruction": {"parts": [{"text": prompt}]},
        "contents": [{"role": "user" if r == "lead" else "model", "parts": [{"text": t}]} for r, t in history],
    }
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        d = json.load(resp)
    return d["candidates"][0]["content"]["parts"][0]["text"].strip()


CASES = [
    ["Boa tarde", "Tudo sim e vc? Quem é?", "Isso, imobiliária", "Nós mesmos, eu e minha sócia"],
    ["Opa", "Tinha uma chamada não atendida no meu telefone"],
    ["Bom dia. Quem?"],
    ["Olá, seja bem-vindo e obrigado por entrar em contato com a Paloschi Empreendimentos Imobiliários! *Não estamos disponíveis no momento, mas retornamos o contato assim que possível*"],
    ["?", "Manda msg"],
    ["Não posso falar agora", "Sobre o que seria"],
    ["Olá", "Quanto custa?"],
    ["Oi", "vc é robô?"],
]

for case in CASES:
    hist = []
    print("=" * 60)
    for msg in case:
        hist.append(("lead", msg))
        reply = ask(hist)
        hist.append(("ia", reply))
        print("LEAD:", msg)
        print("IA:  ", reply)
