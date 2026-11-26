"""/tmp/central_edit/teste_logica.py — testa SÓ a lógica nova do vps_central (401 repetido e fila 1,5 h), sem rede,
sem conta de verdade: carrega as funções do arquivo novo e troca tudo que falaria com o Kaggle por falsos."""
import json, sys, types
from datetime import datetime, timedelta, timezone
from pathlib import Path

src = Path("/tmp/central_edit/sandbox/vps_central_novo.py").read_text(encoding="utf-8")
# carrega o módulo sem rodar o main e sem ler config de verdade
mod = types.ModuleType("vc")
mod.__file__ = "/tmp/central_edit/sandbox/vps_central_novo.py"
codigo = src.split('\nif __name__ == "__main__":')[0]
try:
    exec(compile(codigo, "vc", "exec"), mod.__dict__)
except Exception as e:  # noqa: BLE001
    print("carregar falhou:", repr(e)[:300]); sys.exit(1)

avisos = []
mod.tg = lambda t: avisos.append(t)
mod._medir_uma = lambda est, conta: None
mod._garantir_dataset = lambda conta, est: True
mod.CFG = {"kaggle": {}, "telegram": {}}

# ---- 401: 1ª vez = descanso 12 h; 2ª vez = para + 1 aviso; 3ª vez = não avisa de novo
est = {"cotas": {"contateste": {"erro": "401 unauthorized"}}}
conta = {"username": "contateste"}
for i in range(3):
    mod._lancar_conta(conta, est)
r = est["ruins"]["contateste"]["motivo"]
ok1 = est["n401"]["contateste"] == 3 and "sem internet" in r and len(avisos) == 1
print("401 repetido:", "OK" if ok1 else "FALHOU", "| n401 =", est["n401"]["contateste"], "| avisos =", len(avisos), "|", r[:60])
agora = datetime.now(timezone.utc)
print("conta 401 fica parada (sem internet):", "OK" if mod._esta_ruim(est, "contateste", agora + timedelta(hours=30)) else "FALHOU")

# ---- 401 só 1 vez e depois a cota mede bem = zera
est2 = {"cotas": {"c2": {"erro": "401 unauthorized"}}}
mod._lancar_conta({"username": "c2"}, est2)
est2["cotas"]["c2"] = {"livre_h": 20}
try:
    mod._lancar_conta({"username": "c2"}, est2)
except Exception:  # noqa: BLE001 — pode quebrar mais adiante (push falso); só importa o contador
    pass
print("401 1x e depois cota ok = zera:", "OK" if "c2" not in est2.get("n401", {}) else "FALHOU")

# ---- liberar zera o contador
mod.EST = Path("/tmp/central_edit/_est_teste.json")
mod.EST.write_text(json.dumps(est))
mod.liberar(["contateste"])
e3 = json.loads(mod.EST.read_text())
print("liberar zera n401:", "OK" if "contateste" not in e3.get("n401", {}) and "contateste" not in e3.get("ruins", {}) else "FALHOU")
mod.EST.unlink()
print("limite da fila (padrão):", float(mod.CFG["kaggle"].get("queued_max_h", 1.5)), "h")

# ---- fila: vaga lançada há 2 h com status "queued" -> solta a vaga, conta NÃO vai pro descanso
agora = datetime.now(timezone.utc)
for horas, esperado in ((2.0, "solta"), (1.0, "mantém")):
    est4 = {"gpus": [{"conta": "fila1", "lancado_em": (agora - timedelta(hours=horas)).isoformat(timespec="seconds")}]}
    mod.NUM_GPUS = 1
    mod._conta_por_user = lambda u: {"username": u}
    mod.kg = lambda conta, *a: 'fila1/recap-trabalho has status "kernelworkerstatus.queued"'
    mod._escolher = lambda *a, **k: None
    try:
        mod.manter_slots(est4)
    except Exception as e:  # noqa: BLE001 — 2ª passada pode precisar de mais coisa; só importa a 1ª
        pass
    vaga = est4["gpus"][0]["conta"]
    obt = "solta" if vaga is None else "mantém"
    descanso = "fila1" in est4.get("ruins", {})
    print(f"fila {horas} h: esperado={esperado} obtido={obt} descanso={descanso}",
          "OK" if obt == esperado and not descanso else "FALHOU")

# ---- conta que soltou a fila não é escolhida de novo por 6 h
mod.CONTAS = [{"username": "fila1"}, {"username": "outra"}]
mod._saida_queimada = lambda c: False
mod._ip_da_conta = lambda c: c["username"]
mod._livre_h = lambda est, u, ag: None
mod._papel = lambda c: "longo"
est5 = {"fila_kaggle": {"fila1": (agora - timedelta(hours=2)).isoformat(timespec="seconds")}}
nomes = [c["username"] for c in mod._candidatas(est5, set(), agora)]
print("fila1 fora por 6 h:", "OK" if nomes == ["outra"] else f"FALHOU {nomes}")
est5["fila_kaggle"]["fila1"] = (agora - timedelta(hours=7)).isoformat(timespec="seconds")
nomes = [c["username"] for c in mod._candidatas(est5, set(), agora)]
print("fila1 volta depois de 6 h:", "OK" if "fila1" in nomes else f"FALHOU {nomes}")
