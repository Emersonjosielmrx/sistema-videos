"""Abre o Chrome do cofre da conta pela saída fixa dela (IP rnprmtfo-N), no facebook.com, para a dona logar.
    python fb_abrir_login.py <email_cofre>"""
import sys, time
sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
import requests
import fish_audio

email = sys.argv[1]
cofre, n = fish_audio.checar_conta(email)  # recusa conta do Kaggle; exige IP próprio
porta_px = fish_audio._subir_ponte(n)
px = f"http://127.0.0.1:{porta_px}"
ip = requests.get("https://api.ipify.org", proxies={"http": px, "https": px}, timeout=20).text
print(f"saida: {ip} (rnprmtfo-{n})", flush=True)
porta, proc = cofre.abrir(email, extra=(f"--proxy-server=127.0.0.1:{porta_px}", "https://www.facebook.com/"))
print(f"Chrome aberto na porta CDP {porta} — faça o login do Facebook nele", flush=True)
