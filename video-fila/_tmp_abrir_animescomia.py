import sys
sys.path.insert(0, r"D:\postador-de-videos\bin"); sys.path.insert(0, r"D:\logins-google")
import cofre, youtube_web_poster as y
e = "canalanimescomia@gmail.com"
extra = y._proxy_da_conta_kaggle(e)          # rnprmtfo-49 (92.112.200.33) — só ele
assert extra, "sem a ponte do proxy — NÃO abro"
porta, proc = cofre.abrir(e, "https://www.kaggle.com/settings", True, extra=extra)
print("animescomia aberta no Kaggle pelo rnprmtfo-49, porta", porta, flush=True)
