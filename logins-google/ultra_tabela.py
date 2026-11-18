"""Tabela da oferta AI Ultra (17/11). Lê o LOG (só acrescenta — os 2 verificadores gravavam o json um por cima do
outro) + o json, e classifica pelo TEXTO da página (pt/en)."""
import ast
import json
import re

ARQ = r"D:\logins-google\ultra_resultado_1711.json"
LOG = r"D:\logins-google\ultra_1711.log"

r = {}
try:
    r.update(json.load(open(ARQ, encoding="utf-8")))
except Exception:
    pass
for linha in open(LOG, encoding="utf-8"):
    m = re.search(r"\] (?:\[casa\] )?([\w.+-]+@gmail\.com): (\{.*\})\s*$", linha)
    if m:
        try:
            r[m.group(1)] = ast.literal_eval(m.group(2))
        except Exception:
            pass


def classe(v):
    t = " ".join(str(v.get(k) or "") for k in ("detalhe", "cartao", "erro"))
    tl = t.lower()
    if "12-month free trial" in t or "teste gratuito de 12 meses" in tl:
        m = re.search(r"(Mastercard|Visa|Elo|American Express|Amex)[-\s]?\d{4}", t)
        return "TEM A OFERTA (cartão já salvo: " + (m.group(0) if m else "ver na tela") + ")"
    if "não está disponível" in tl and "separadamente" in tl:
        return "TEM SÓ O AI ULTRA (YouTube Premium indisponível — assina só o Ultra)"
    if v.get("oferta") is True:
        c = v.get("cartao") or "?"
        return "TEM A OFERTA (falta cadastrar cartão)" if c == "sem cartão salvo" else "TEM A OFERTA (cartão já salvo: " + c + ")"
    if "forma de pagamento" in tl or "payment method" in tl:
        return "TEM A OFERTA (falta cadastrar cartão)"
    if "já tem uma assinatura" in tl or "already have" in tl:
        return "JÁ ASSINADA (Ultra já ativo)"
    if "erro no nosso sistema" in tl or "something went wrong" in tl:
        return "erro do Google — testar de novo"
    if "login" in tl:
        return "não logada"
    if "em uso" in tl or "aberta pela dona" in tl:
        return "aberta/em uso — conferir"
    if v.get("erro"):
        return "falhou: " + v["erro"][:60]
    return "sem oferta: " + t[:80]


if __name__ == "__main__":
    for k in sorted(r):
        print(f"{k.split('@')[0]:30} | {classe(r[k])}")
