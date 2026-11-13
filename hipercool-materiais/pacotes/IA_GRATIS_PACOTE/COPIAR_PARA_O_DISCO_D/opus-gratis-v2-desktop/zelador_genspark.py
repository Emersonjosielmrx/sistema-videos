"""Zelador do pool do Genspark (molde: D:\\sonnet web\\zelador_sonnet.py). Roda 1x/dia (tarefa ZeladorGenspark).
- conta logada sem teste de Opus: manda "responda so: ok" (3 créditos) — sem Opus no grátis vira opus=False e sai da fila
  de vez; respondeu = opus=True.
- conta já testada: confere login + saldo pelo menu (sem gastar crédito); deslogou = sai da fila.
No fim lista quem precisa de login à mão (python login_fila.py 3 --todas).
    python zelador_genspark.py [--so-opus]"""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import genspark as g  # noqa: E402

so_opus = "--so-opus" in sys.argv
contas = [c for c in g._ler()["contas"] if c.get("logado")]
print(f"{len(contas)} conta(s) logada(s)")
for c in contas:
    a = c["apelido"]
    t0 = time.time()
    try:
        if c.get("opus") is None:
            r = g.perguntar("responda so: ok", conta=a, tentativas=1)
            dep = g._conta(g._ler(), a) or {}
            if r:
                g.marcar_opus(a, True)
                st = "opus OK"
            else:
                st = "SEM OPUS" if dep.get("opus") is False else ("DESLOGADA" if not dep.get("logado") else "erro")
        elif not so_opus:
            g.checar(a)
            continue
        else:
            continue
    except Exception as e:  # noqa: BLE001
        st = f"erro {str(e)[:60]}"
    finally:
        g._fechar_todos_quentes()  # um Chrome por vez (RAM)
    print(f"  {a:32} {st}  ({time.time() - t0:.0f}s)", flush=True)

dados = g._ler()["contas"]
boas = [c["apelido"] for c in dados if c.get("logado") and c.get("opus") is not False]
sem = [c["apelido"] for c in dados if c.get("opus") is False]
fora = [c["apelido"] for c in dados if not c.get("logado")]
print(f"\nCom Opus e logadas: {len(boas)} · sem Opus: {len(sem)} {sem}\nPrecisam de login à mão: {len(fora)} {fora}")
