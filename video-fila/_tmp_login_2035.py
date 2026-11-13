import sys, time
sys.path.insert(0, r"D:\postador-de-videos\bin"); sys.path.insert(0, r"D:\logins-google")
import cofre, youtube_web_poster as y
e = "emersonjosiel2035@gmail.com"
extra = y._proxy_da_conta_kaggle(e)          # ponte do rnprmtfo-14 — nunca pelo IP de casa
assert extra, "sem a ponte do proxy da conta — NÃO abro"
porta, proc = cofre.abrir(e, "https://accounts.google.com/ServiceLogin?Email=" + e, True, extra=extra)
print("janela aberta pelo rnprmtfo-14, porta", porta, flush=True)
