#!/usr/bin/env python3
r"""Classifica as contas Google vivas do cofre pelo modelo que o Gemini serve de fato quando pedimos o Argon (HTTP):
  "4 Argon"                          -> pro (entra no rodízio)
  Flash-Lite + "Limite atingido"     -> pro_sem_cota (entra no rodízio, descansando até a cota voltar)
  Flash-Lite sem aviso               -> gratis
Substitui o descobrir_pro.py (27/10: ele marcou 'sem_argon' em contas Pro). Retomável: resultado em classificar_pro.json.
    python -X utf8 D:\gemini-argo\classificar_pro.py [--refazer]
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\gemini-argo")
import gemini_argon as ga
import gemini_http as gh
import sync_cookies
from gemini_argon import cofre

RESULTADO = Path(r"D:\gemini-argo\classificar_pro.json")
# contas que a dona disse que são Pro (27/10) vão primeiro
PRIMEIRO = ["solar", "throne", "inovaremanhwa", "aula", "revolution", "multiatendimento", "filmescomia", "msenergy",
            "empresa", "murilo", "emersonjosiel", "mentoria", "jogoscomia", "genshin", "4487", "fabrica", "inovarecap",
            "rezaalka", "comoseria"]


def _liberar_ram():
    try:
        sys.path.insert(0, r"D:\logins-google")
        import chrome_conta
        chrome_conta._liberar_ram()
    except Exception:  # noqa: BLE001
        pass


def classificar(apelido):
    if not (sync_cookies.COOKIES_DIR / f"{apelido}.json").exists():
        _liberar_ram()
        if not sync_cookies.sincronizar(apelido):
            return "deslogada"
    s = gh._abrir(apelido)
    at, bl, fsid = gh._tokens(apelido, s)
    freq = json.dumps([None, json.dumps([["Diga só: oi", 0, None, None, None, None, 0], ["pt"], None])])
    url = ("https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"
           f"?bl={bl}&f.sid={fsid}&hl=pt&_reqid={int(time.time()) % 1000000}&rt=c")
    r = s.post(url, data={"f.req": freq, "at": at}, headers={
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8", "x-same-domain": "1",
        "x-goog-ext-525001261-jspb": json.dumps([1, None, None, None, gh.MODELOS["argon"]]),
        "Origin": "https://gemini.google.com", "Referer": "https://gemini.google.com/"}, timeout=300)
    servido = gh._RE_SERVIDO.findall(r.text)
    if any("argon" in x.lower() for x in servido):
        return "pro"
    if "Limite atingido" in r.text:
        return "pro_sem_cota"
    return "gratis" if servido else f"sem resposta ({r.status_code})"


DOC = Path(r"D:\gemini-argo\CONTAS_PARA_AUTORIZAR.md")


def documentar(feitos):
    """Lista pra dona as contas que não deu pra usar e o que fazer em cada uma (gravada a cada conta classificada)."""
    grupos = {
        "deslogada": ("Gemini não abre com os cookies (conta deslogada no Gemini ou pedindo confirmação)",
                      "abrir gemini.google.com nessa conta (cofre.py logar <conta>), passar a tela que aparecer"),
        "sem resposta": ("Gemini abre mas não responde (provável verificação de idade / Gemini bloqueado na conta)",
                         "abrir gemini.google.com na conta e confirmar a idade (ou ver o aviso que aparece)"),
        "gratis": ("Conta sem o plano Pro (Gemini responde, mas sem o Argon)", "só serve se assinar/ativar o Pro"),
    }
    linhas = ["# Contas Google que não entraram no rodízio do Argon\n",
              f"Gerado por `classificar_pro.py` em {datetime.now():%d/%m %H:%M}. Depois de autorizar, rode "
              "`python -X utf8 D:\\gemini-argo\\classificar_pro.py --refazer` (ou apague a linha da conta em "
              "classificar_pro.json) que ela é testada de novo e entra sozinha se for Pro.\n"]
    for chave, (titulo, fazer) in grupos.items():
        contas = sorted(e for e, v in feitos.items()
                        if v["resultado"].startswith(chave) or (chave == "deslogada" and v["resultado"].startswith("erro")))
        if contas:
            linhas += [f"\n## {titulo} — {len(contas)}\n", f"O que fazer: {fazer}.\n"]
            linhas += [f"- {e} ({feitos[e]['resultado'][:60]})" for e in contas]
    pro = sorted(e for e, v in feitos.items() if v["resultado"].startswith("pro"))
    linhas += [f"\n## Já no rodízio (Pro) — {len(pro)}\n"] + [f"- {e}" for e in pro]
    DOC.write_text("\n".join(linhas) + "\n", "utf-8")


def main():
    feitos = {} if "--refazer" in sys.argv or not RESULTADO.exists() else json.loads(RESULTADO.read_text("utf-8"))
    reg = cofre._ler()["contas"]
    vivas = [e for e, d in reg.items() if d.get("google") == "vivo" and e.endswith("@gmail.com") and e not in feitos]
    vivas.sort(key=lambda e: next((i for i, p in enumerate(PRIMEIRO) if p in e), len(PRIMEIRO)))
    print(f"{len(vivas)} contas para classificar", flush=True)
    na_lista = {c["email"] for c in ga._ler_contas()["contas"]}
    for email in vivas:
        apelido = email.split("@")[0]
        try:
            r = classificar(apelido)
        except Exception as e:  # noqa: BLE001
            r = f"erro: {str(e)[:100]}"
        feitos[email] = {"resultado": r, "quando": datetime.now().isoformat(timespec="minutes")}
        RESULTADO.write_text(json.dumps(feitos, ensure_ascii=False, indent=1), "utf-8")
        documentar(feitos)
        if r in ("pro", "pro_sem_cota") and email not in na_lista:
            ga.adicionar_conta(email)
            na_lista.add(email)
        if r == "pro_sem_cota":
            ga.marcar_sem_cota(apelido)
        elif r == "pro":
            ga.marcar_sem_cota(apelido, None)
        print(f"{email:44} {r}", flush=True)
    pro = [e for e, v in feitos.items() if v["resultado"].startswith("pro")]
    for e in pro:  # o proxy grava o mesmo arquivo ao mesmo tempo: garante que nenhuma Pro ficou de fora
        ga.adicionar_conta(e)
    print(f"\nPro: {len(pro)} (com cota agora: {sum(v['resultado'] == 'pro' for v in feitos.values())})")


if __name__ == "__main__":
    main()
