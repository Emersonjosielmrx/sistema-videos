import sys, json, requests, re
sys.path.insert(0, r"D:\gemini-argo")
import gemini_http as gh

arq = gh._arq_cookies("canalanimescomia")
cookies = json.loads(arq.read_text(encoding="utf-8"))
s = requests.Session()
s.cookies.update(cookies)
s.headers.update({"User-Agent": gh.UA})
r = s.get("https://gemini.google.com/app", timeout=30)
html = r.text

print("Status:", r.status_code)
print("WIZ_global_data presente?", "WIZ_global_data" in html)

m = re.search(r"WIZ_global_data\s*=\s*({.*?});", html, re.DOTALL)
if m:
    try:
        data = json.loads(m.group(1))
        print("Chaves WIZ:", list(data.keys()))
        for k in ["SNlM0e", "cfb2h", "FdrFJe"]:
            print(f"Chave {k}:", data.get(k))
    except Exception as e:
        print("Erro parse WIZ:", e)
        print("Trecho WIZ:", m.group(1)[:300])
else:
    print("Nao achou WIZ_global_data")
    # Vamos verificar se a pagina esta redirecionando para login ou se eh a pagina de deslogado
    if "accounts.google.com" in html or "Sign in" in html or "Fazer login" in html:
        print("A PAGINA TEM FAZER LOGIN!")
    else:
        print("Pagina nao tem Fazer Login aparente")
