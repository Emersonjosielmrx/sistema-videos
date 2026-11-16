r"""teste_chegada.py — prova se o e-mail CHEGA em cada provedor temporário (o Kaggle recusa todos os domínios
descartáveis no campo, então não serve de remetente). Remetente: caixa descartável do Guerrilla Mail (API send_email),
sem conta nenhuma. Tudo pelo proxy grátis rotativo do Webshare (testar_provedores.sessao), nunca pela casa.

    python teste_chegada.py                # cria caixa em cada provedor, manda 1 e-mail, espera até 4 min
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))
import testar_provedores as tp  # noqa: E402

G = "https://api.guerrillamail.com/ajax.php"
ALVOS = ["mailtm", "tempmaillol", "tempmailplus", "tempmailio", "maildrop", "mailnesia", "inboxkitten", "harakiri",
         "guerrilla", "mailinator", "mailgw", "dropmail", "developermail", "1secmail"]


def remetente():
    s = tp.sessao()
    r = s.get(G, params={"f": "get_email_address", "lang": "en"}, timeout=25).json()
    return s, r["sid_token"], r["email_addr"]


def enviar(s, sid, para, assunto):
    r = s.post(G, params={"f": "send_email"}, data={"sid_token": sid, "to": para, "subject": assunto,
                                                       "body": f"codigo de teste {assunto}"}, timeout=30)
    return r.text[:200]


def main():
    alvos = sys.argv[1:] or ALVOS
    gs, sid, de = remetente()
    print("remetente", de, flush=True)
    caixas = {}
    for p in alvos:
        try:
            s = tp.sessao()
            st = tp.PROVEDORES[p][0](s)
            marca = f"TST{int(time.time()) % 100000}{p[:4]}"
            caixas[p] = {"st": st, "marca": marca, "enviado": enviar(gs, sid, st["email"], marca), "t0": time.time()}
            print(f"{p:14} {st['email']:40} envio: {caixas[p]['enviado'][:80]}", flush=True)
        except Exception as e:  # noqa: BLE001
            caixas[p] = {"erro": f"{type(e).__name__}: {str(e)[:150]}"}
            print(f"{p:14} sem caixa: {caixas[p]['erro']}", flush=True)
        time.sleep(3)  # sem rajada no remetente
    fim = time.time() + 240
    pend = {p for p, c in caixas.items() if "st" in c}
    while pend and time.time() < fim:
        time.sleep(20)
        for p in list(pend):
            c = caixas[p]
            try:
                msgs = tp.PROVEDORES[p][1](tp.sessao(), c["st"])
                if any(c["marca"] in str(m) or "guerrilla" in str(m.get("de", "")).lower() or "sharklasers" in
                       str(m.get("de", "")).lower() for m in msgs) or (msgs and p != "guerrilla"):
                    c["chegou_em_s"] = round(time.time() - c["t0"])
                    c["msgs"] = msgs[:2]
                    pend.discard(p)
                    print(f"CHEGOU {p} em {c['chegou_em_s']} s: {msgs[:1]}", flush=True)
            except Exception as e:  # noqa: BLE001
                c["erro_ler"] = f"{type(e).__name__}: {str(e)[:120]}"
    res = {p: {"email": c.get("st", {}).get("email"), "chegou": "chegou_em_s" in c, "seg": c.get("chegou_em_s"),
               "erro": c.get("erro") or (None if "chegou_em_s" in c else c.get("erro_ler")), "envio": c.get("enviado")}
           for p, c in caixas.items()}
    (DIR / "resultado_chegada.json").write_text(json.dumps({"em": datetime.now().isoformat(timespec="seconds"),
                                                            "remetente": de, "resultado": res}, ensure_ascii=False,
                                                           indent=1), encoding="utf-8")
    for p, r in res.items():
        print(f"{p:14} {'CHEGOU em ' + str(r['seg']) + ' s' if r['chegou'] else 'NAO chegou'}  {r['erro'] or ''}")


if __name__ == "__main__":
    main()
