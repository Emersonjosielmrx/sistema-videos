"""/tmp/central_edit/aplicar_mudancas.py — aplica as mudanças de 26/11 (fila 1,5 h sem descanso + pausa de 6 h da conta
que soltou a fila + 401 repetido para e avisa) num vps_central.py, por TEXTO EXATO (assert de 1 ocorrência cada).
Uso: python3 aplicar_mudancas.py <entrada> <saida>"""
import sys
from pathlib import Path

ent, sai = Path(sys.argv[1]), Path(sys.argv[2])
s = ent.read_text(encoding="utf-8").replace("\r\n", "\n")


def troca(a, b, nome):
    global s
    n = s.count(a)
    assert n == 1, f"{nome}: achei {n} vezes"
    s = s.replace(a, b)
    print("ok", nome)


# 1) fila presa: 6 h -> 1,5 h, sem descanso de 12 h (só solta a vaga e anota)
troca('''        if "queued" in s and g.get("lancado_em") and \\
                (agora - datetime.fromisoformat(g["lancado_em"])).total_seconds() > \\
                float(os.environ.get("KAGGLE_QUEUED_MAX_H", "6")) * 3600:
            # 10/11: inovare/inovareee/mundosolar1995 ficaram 21 h 'queued' (o Kaggle não dá GPU pra conta nova) segurando
            # 3 das vagas. Fila > KAGGLE_QUEUED_MAX_H h: solta a vaga e descansa a conta (RUIM_TTL_H); o kernel em fila
            # fica lá — se o Kaggle der a GPU depois, o trabalhador pega pedido normalmente.
            est.setdefault("ruins", {})[user] = {"motivo": "queued > 6 h (Kaggle não dá GPU)",
                                                 "em": agora.isoformat(timespec="seconds")}
            print(f"{user}: queued há mais de 6 h — solta a vaga", flush=True)
            g["conta"], g["lancado_em"] = None, None
            g.pop("papel", None)
            continue''',
      '''        _fila_max_h = float(os.environ.get("KAGGLE_QUEUED_MAX_H") or CFG["kaggle"].get("queued_max_h", 1.5))
        if "queued" in s and g.get("lancado_em") and \\
                (agora - datetime.fromisoformat(g["lancado_em"])).total_seconds() > _fila_max_h * 3600:
            # 10/11: inovare/inovareee/mundosolar1995 ficaram 21 h 'queued' (o Kaggle não dá GPU pra conta nova) segurando
            # 3 das vagas. Fila > KAGGLE_QUEUED_MAX_H h: solta a vaga; o kernel em fila fica lá — se o Kaggle der a GPU
            # depois, o trabalhador pega pedido normalmente.
            # 26/11 dona ("o máximo possível com o mínimo de paradas"): 21-26/11 a fila do Kaggle cresceu (5 contas
            # 'queued' 3+ h). 6 h -> 1,5 h e a conta NÃO vai pro descanso de 12 h (não tem defeito; o Kaggle está sem
            # GPU): só solta a vaga e fica fora por KAGGLE_FILA_PAUSA_H (6 h; _candidatas), pra não abrir 2ª sessão por
            # cima do kernel que ainda está na fila (o Kaggle limita 2 sessões de GPU por conta).
            # config kaggle.queued_max_h / fila_pausa_h (ou as variáveis) mudam os tempos.
            est.setdefault("fila_kaggle", {})[user] = agora.isoformat(timespec="seconds")
            print(f"{user}: queued há mais de {_fila_max_h:g} h — solta a vaga (conta volta em 6 h)", flush=True)
            g["conta"], g["lancado_em"] = None, None
            g.pop("papel", None)
            continue''', "fila 1,5 h")

# 2) a conta que soltou a fila não é escolhida de novo por 6 h
troca('''    return [c for c in CONTAS if not _esta_ruim(est, c["username"], agora) and c["username"] not in em_uso''',
      '''    # 26/11: conta que soltou a vaga por fila do Kaggle ainda tem o kernel em fila lá — relançar nela abriria uma 2ª
    # sessão por cima (limite do Kaggle: 2 por conta). Fica fora por KAGGLE_FILA_PAUSA_H (6 h, a regra antiga).
    pausa_fila = float(os.environ.get("KAGGLE_FILA_PAUSA_H") or CFG["kaggle"].get("fila_pausa_h", 6))
    fila = est.get("fila_kaggle", {})

    def _na_fila(u):
        try:
            return u in fila and (agora - datetime.fromisoformat(fila[u])).total_seconds() < pausa_fila * 3600
        except (ValueError, TypeError):
            return False
    return [c for c in CONTAS if not _esta_ruim(est, c["username"], agora) and c["username"] not in em_uso
            and not _na_fila(c["username"])''', "pausa da conta na fila")

# 3) 401 repetido: na 2ª vez seguida, para de tentar e avisa a dona 1x
troca('''        if "401" in erro_cota:
            est.setdefault("ruins", {})[conta["username"]] = {
                "motivo": "401 ao medir a cota (token recusado / banida?)",
                "em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            print(f"{conta['username']}: 401 na cota — descansa {RUIM_TTL_H} h, próxima conta", flush=True)''',
      '''        if "401" in erro_cota:
            # 26/11: 11 contas da hermes-prod deram 401 a cada 12 h desde 25/11, para sempre (a central tratava como
            # cota). 401 = chave recusada (token velho/revogado) ou BANIDA (incidente 02/11 também começou com 401).
            # 2º 401 seguido: para de tentar (motivo "sem internet" = só volta com `vps_central.py liberar <user>`)
            # e avisa a dona 1x. Bater de novo em conta banida pelo mesmo IP das boas é o risco que se quer evitar.
            n401 = est.setdefault("n401", {})
            n401[conta["username"]] = n401.get(conta["username"], 0) + 1
            if n401[conta["username"]] >= 2:
                est.setdefault("ruins", {})[conta["username"]] = {
                    "motivo": "sem internet: 401 repetido (token recusado ou banida — dona confere)",
                    "em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                print(f"{conta['username']}: 401 de novo ({n401[conta['username']]}x) — PARA de tentar; "
                      f"liberar à mão: vps_central.py liberar {conta['username']}", flush=True)
                av = est.setdefault("avisados", [])
                if f"401_{conta['username']}" not in av:
                    av.append(f"401_{conta['username']}")
                    tg(f"🔑 Kaggle {conta['username']}: 401 repetido (chave recusada ou conta banida). "
                       f"Parei de tentar. Conferir e gerar token novo pela saída da conta; depois: "
                       f"vps_central.py liberar {conta['username']}")
            else:
                est.setdefault("ruins", {})[conta["username"]] = {
                    "motivo": "401 ao medir a cota (token recusado / banida?)",
                    "em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                print(f"{conta['username']}: 401 na cota — descansa {RUIM_TTL_H} h, próxima conta", flush=True)''',
      "401 repetido")

# 4) cota medida sem erro = chave aceita, zera o contador
troca('''    erro_cota = str(((est.get("cotas") or {}).get(conta["username"]) or {}).get("erro", ""))''',
      '''    erro_cota = str(((est.get("cotas") or {}).get(conta["username"]) or {}).get("erro", ""))
    if not erro_cota:
        est.get("n401", {}).pop(conta["username"], None)  # 26/11: mediu a cota sem erro = chave aceita, zera o 401''',
      "zera n401 quando a cota mede")

# 5) liberar zera o contador
troca('''    alvo = users or list(ruins)
    for u in alvo:
        ruins.pop(u, None)''', '''    alvo = users or list(ruins)
    for u in alvo:
        ruins.pop(u, None)
        est.get("n401", {}).pop(u, None)  # 26/11: contador do 401 repetido recomeça''', "liberar zera n401")

compile(s, "vps_central.py", "exec")
sai.write_text(s, encoding="utf-8", newline="\n")
print("COMPILA ->", sai, "| linhas:", s.count("\n"))
