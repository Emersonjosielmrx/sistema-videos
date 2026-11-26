# D:\sistema\catalogo\trocar_python.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/trocar_python.py)
# OBRA sistema unico - PYTHON UNICO. Troca o interpretador das tarefas agendadas "PRONTA para trocar" (unificacao.json,
# feito pelo analisar_uso.py a partir do USO REAL) para D:\veo\venv (python.exe ou pythonw.exe, mantendo o tipo).
# Seguranca: guarda as acoes originais de cada tarefa em D:\sistema\mapa\python_troca\troca.json e o XML em backup\.
#   python trocar_python.py --aplicar [--max N] [--so TAREFA]   troca as prontas (padrao: todas)
#   python trocar_python.py --verificar     (tarefa TrocaPythonVerificar, 10 min) depois da 1a rodada com o Python novo:
#        resultado 0 (ou igual ao de antes) = CONFIRMADA; piorou = VOLTA SOZINHA para o Python antigo e avisa no Telegram.
#   python trocar_python.py --voltar TAREFA | --voltar-todas      volta manual
#   python trocar_python.py --status
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path(r"D:\sistema\mapa\python_troca")
EST = BASE / "troca.json"
UNI = Path(r"D:\sistema\mapa\unificacao.json")
NOVO = {"python.exe": r"D:\veo\venv\Scripts\python.exe", "pythonw.exe": r"D:\veo\venv\Scripts\pythonw.exe"}
RE_PY = re.compile(r'[A-Za-z]:\\(?:(?![A-Za-z]:\\)[^"])*?\\(python[w]?\.exe)', re.I)  # 26/11: nunca atravessa outro caminho (engolia rodar_oculto.vbs)
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
OK_CODIGOS = {0, 267009, 267011, 2147946720, -2147020576}  # 0 | rodando | nunca rodou | ja estava rodando
# 26/11: 0x41306 = tarefa INTERROMPIDA (limite de tempo / MatarTravados) - nao diz nada sobre o Python; espera a proxima
INCONCLUSIVO = {267014}


def ps(cmd, timeout=90):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", "[Console]::OutputEncoding=[Text.Encoding]::UTF8;" + cmd],
                       capture_output=True, timeout=timeout, creationflags=SEM_JANELA, env={**os.environ, "SISTEMA_USO": "0"})
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def info(nome):
    rc, out, err = ps(f"$t=Get-ScheduledTask -TaskName '{nome}'; $i=$t|Get-ScheduledTaskInfo; "
                      "[pscustomobject]@{acoes=@($t.Actions|%{[pscustomobject]@{e=$_.Execute;a=$_.Arguments;d=$_.WorkingDirectory}});"
                      "ultima=$i.LastRunTime.ToString('s');res=$i.LastTaskResult;caminho=$t.TaskPath}|ConvertTo-Json -Depth 4")
    if rc != 0 or not out.strip():
        raise RuntimeError(err.strip()[:300] or "tarefa nao encontrada")
    j = json.loads(out)
    j["acoes"] = j["acoes"] if isinstance(j["acoes"], list) else [j["acoes"]]
    return j


def gravar_acoes(nome, acoes):
    partes = []
    for a in acoes:
        arg = f"-Argument '{(a.get('a') or '').replace(chr(39), chr(39)*2)}'" if a.get("a") else ""
        wd = f"-WorkingDirectory '{a['d']}'" if a.get("d") else ""
        partes.append(f"(New-ScheduledTaskAction -Execute '{a['e'].replace(chr(39), chr(39)*2)}' {arg} {wd})")
    rc, out, err = ps(f"Set-ScheduledTask -TaskName '{nome}' -Action @({','.join(partes)}) | Out-Null; 'ok'")
    if rc != 0 or "ok" not in out:
        raise RuntimeError(err.strip()[:300])


TRAVA = BASE / "troca.lock"


def travar():
    """26/11: verificador e --aplicar rodando juntos perderam 4 registros (um salvou por cima do outro). Agora um espera o outro."""
    BASE.mkdir(parents=True, exist_ok=True)
    for _ in range(240):
        try:
            fd = os.open(str(TRAVA), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:
                if time.time() - TRAVA.stat().st_mtime > 900:  # trava esquecida (processo morreu)
                    TRAVA.unlink()
                    continue
            except OSError:
                pass
            time.sleep(1)
    return False


def destravar():
    try:
        TRAVA.unlink()
    except OSError:
        pass


def _corrigir_engolidos(d):
    """26/11: a 1a versao da RE_PY atravessava espacos e trocava 'D:\\rodar_oculto.vbs C:\\...\\python.exe' inteiro pelo
    Python novo (sumia o rodar_oculto.vbs). Refaz a acao a partir da original com a regex nova."""
    for nome, r in d.items():
        if r.get("tipo") == "bat" or r.get("estado") not in ("trocada", "confirmada"):
            continue
        perdeu = any("rodar_oculto" in (a.get("a") or "").lower() and "rodar_oculto" not in (b.get("a") or "").lower()
                     for a, b in zip(r.get("acoes_antes", []), r.get("acoes_depois", [])))
        if not perdeu:
            continue
        novas = [{"e": RE_PY.sub(lambda m: NOVO[m.group(1).lower()], a["e"] or ""),
                  "a": RE_PY.sub(lambda m: NOVO[m.group(1).lower()], a.get("a") or ""), "d": a.get("d")} for a in r["acoes_antes"]]
        gravar_acoes(nome, novas)
        r["acoes_depois"] = novas
        r["obs"] = "26/11 corrigida: rodar_oculto.vbs tinha sumido da acao"
        print(f"{nome}: acao corrigida -> {novas[0]['e']} {novas[0]['a'][:90]}")


def ler():
    return json.loads(EST.read_text(encoding="utf-8")) if EST.exists() else {}


def salvar(d):
    BASE.mkdir(parents=True, exist_ok=True)
    EST.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def avisar(txt):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(txt, "python-unico", importante=True)
    except Exception:  # noqa: BLE001
        pass


def aplicar(maximo, so):
    d = ler()
    prontas = [t["tarefa"] for t in json.loads(UNI.read_text(encoding="utf-8"))["tarefas"] if t["situacao"] == "PRONTA para trocar"]
    if "--sem-postagem" in sys.argv:  # 26/11: no horario nobre so troca o que nao posta
        cat = json.loads(Path(r"D:\sistema\catalogo\sistema.json").read_text(encoding="utf-8-sig"))
        sem_postagem = {t for pid, p in cat["projetos"].items() if p["categoria"] != "B-postagem" and pid != "empresas"
                        for t in p.get("tarefas", [])}
        prontas = [t for t in prontas if t in sem_postagem]
    if so:
        prontas = [t for t in prontas if t == so]
    feitas = 0
    for nome in prontas:
        if feitas >= maximo:
            break
        if nome in d and d[nome]["estado"] in ("trocada", "confirmada", "voltou"):
            continue  # 26/11: "voltou" = falhou no Python novo; so volta a tentar a mao (apagar o registro)
        try:
            i = info(nome)
            novas, mudou = [], False
            for a in i["acoes"]:
                e, arg = a["e"] or "", a.get("a") or ""
                def sub(m):
                    return NOVO[m.group(1).lower()]
                e2, arg2 = RE_PY.sub(sub, e), RE_PY.sub(sub, arg)
                mudou |= (e2 != e or arg2 != arg)
                novas.append({"e": e2, "a": arg2, "d": a.get("d")})
            if not mudou:
                print(f"{nome}: interpretador nao esta na acao da tarefa (dentro de .bat?) - pulada")
                d[nome] = {"estado": "pulada", "motivo": "python dentro de .bat/.ps1", "em": time.strftime("%Y-%m-%dT%H:%M:%S")}
                continue
            BASE.joinpath("backup").mkdir(parents=True, exist_ok=True)
            subprocess.run(["schtasks", "/query", "/tn", i["caminho"] + nome, "/xml"],
                           stdout=open(BASE / "backup" / f"{re.sub(r'[^\w-]', '_', nome)}.xml", "wb"), creationflags=SEM_JANELA)
            gravar_acoes(nome, novas)
            d[nome] = {"estado": "trocada", "em": time.strftime("%Y-%m-%dT%H:%M:%S"), "acoes_antes": i["acoes"],
                       "acoes_depois": novas, "res_antes": i["res"], "ultima_antes": i["ultima"]}
            feitas += 1
            print(f"{nome}: TROCADA -> D:\\veo\\venv")
        except Exception as e:  # noqa: BLE001
            print(f"{nome}: ERRO {e}")
            d[nome] = {"estado": "erro", "motivo": str(e)[:300], "em": time.strftime("%Y-%m-%dT%H:%M:%S")}
        salvar(d)
    salvar(d)
    print(f"{feitas} trocada(s)")


def _uso_por_main():
    """main.py (minusculo) -> pacotes externos usados de verdade (registrador sistema_uso)."""
    out = {}
    for f in sorted(Path(r"D:\sistema\mapa\uso").glob("uso_*.jsonl"))[-7:]:
        for l in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                j = json.loads(l)
            except ValueError:
                continue
            m = (j.get("main") or "").lower()
            if m.endswith(".py"):
                out.setdefault(m, set()).update(e for e in j.get("externos", []) if not e.endswith("__mypyc") and not e.startswith("_"))
    return out


def _principal_tem(pacotes):
    if not pacotes:
        return {}
    prog = ("import importlib.util,json,sys\n"
            "def ok(m):\n    try:\n        return importlib.util.find_spec(m) is not None\n    except Exception:\n        return False\n"
            "print(json.dumps({m: ok(m) for m in json.loads(sys.argv[1])}))")
    r = subprocess.run([NOVO["python.exe"], "-c", prog, json.dumps(sorted(pacotes))], capture_output=True, text=True,
                       timeout=300, creationflags=SEM_JANELA, env={**os.environ, "SISTEMA_USO": "0"})
    return json.loads(r.stdout.strip().splitlines()[-1])


MANUAL = {"playwright", "selenium", "undetected_chromedriver", "uiautomator2", "patchright", "nodriver", "pyautogui"}


def aplicar_bats(maximo):
    """26/11: tarefa que chama um .bat com Python antigo DENTRO -> troca o Python no .bat (copia .bak_obra_python), se
    todos os .py chamados nele tiverem uso real registrado e o principal tiver os pacotes. Mesma verificacao/volta."""
    d = ler()
    cat = json.loads(Path(r"D:\sistema\catalogo\sistema.json").read_text(encoding="utf-8-sig"))
    uso = _uso_por_main()
    cands = []
    for p in cat["projetos"].values():
        for nome, det in p.get("tarefas_detalhe", {}).items():
            m = re.search(r"([A-Za-z]:\\[^\"]+?\.bat)", det.get("cmd", ""), re.I)
            if det.get("ligada") and m and nome not in d:
                cands.append((nome, m.group(1)))
    feitas = 0
    for nome, bat in cands:
        if feitas >= maximo:
            break
        try:
            txt = Path(bat).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        velhos = [x for x in RE_PY.finditer(txt) if not x.group(0).lower().startswith(r"d:\veo\venv")]
        if not velhos:
            continue
        scripts = [s.lower() for s in re.findall(r"([A-Za-z]:\\[^\"\r\n]+?\.py)", txt)]
        if not scripts or any(s not in uso for s in scripts):
            print(f"{nome}: .bat sem uso registrado de todos os .py - espera"); continue
        pac = set().union(*(uso[s] for s in scripts))
        if pac & MANUAL:
            print(f"{nome}: usa navegador ({', '.join(pac & MANUAL)}) - so manual"); continue
        tem = _principal_tem(pac)
        faltam = [k for k in pac if not tem.get(k)]
        if faltam:
            print(f"{nome}: falta no principal {faltam}"); continue
        bak = Path(bat + ".bak_obra_python")
        if not bak.exists():
            bak.write_text(txt, encoding="utf-8", errors="replace")
        novo = RE_PY.sub(lambda mm: NOVO[mm.group(1).lower()], txt)
        Path(bat).write_text(novo, encoding="utf-8", errors="replace")
        i = info(nome)
        d[nome] = {"estado": "trocada", "tipo": "bat", "bat": bat, "bat_antes": txt, "em": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "res_antes": i["res"], "ultima_antes": i["ultima"]}
        salvar(d)
        feitas += 1
        print(f"{nome}: .bat TROCADO -> D:\\veo\\venv ({bat})")
    print(f"{feitas} .bat trocado(s)")


def voltar(nome, d, motivo):
    if d[nome].get("tipo") == "bat":
        Path(d[nome]["bat"]).write_text(d[nome]["bat_antes"], encoding="utf-8", errors="replace")
        d[nome].update(estado="voltou", voltou_em=time.strftime("%Y-%m-%dT%H:%M:%S"), motivo=motivo)
        return
    gravar_acoes(nome, d[nome]["acoes_antes"])
    d[nome].update(estado="voltou", voltou_em=time.strftime("%Y-%m-%dT%H:%M:%S"), motivo=motivo)


def verificar():
    d = ler()
    for nome, r in d.items():
        if r.get("estado") != "trocada":
            continue
        try:
            i = info(nome)
        except Exception as e:  # noqa: BLE001
            r["ultimo_erro"] = str(e)[:200]
            continue
        if i["ultima"] <= r["em"]:
            continue  # ainda nao rodou com o Python novo
        if i["res"] in INCONCLUSIVO:
            r["obs"] = f"rodada {i['ultima']} interrompida (0x41306) - espera a proxima"
            continue
        antes_ok = r["res_antes"] in OK_CODIGOS
        agora_ok = i["res"] in OK_CODIGOS
        if agora_ok or (not antes_ok and i["res"] == r["res_antes"]):
            r.update(estado="confirmada", confirmada_em=time.strftime("%Y-%m-%dT%H:%M:%S"), res_depois=i["res"])
        else:
            voltar(nome, d, f"resultado piorou: antes 0x{r['res_antes'] & 0xFFFFFFFF:X}, com Python novo 0x{i['res'] & 0xFFFFFFFF:X}")
            avisar(f"Python unico: a tarefa {nome} falhou no Python novo e VOLTOU sozinha para o antigo ({r['motivo']}).")
    salvar(d)


def status():
    d = ler()
    cont = {}
    for nome, r in sorted(d.items()):
        cont[r["estado"]] = cont.get(r["estado"], 0) + 1
        print(f"{nome:28} {r['estado']:11} {r.get('motivo', '')[:90]}")
    print("TOTAL:", ", ".join(f"{k} {v}" for k, v in sorted(cont.items())))


a = sys.argv[1:]
if any(x in a for x in ("--aplicar", "--bats", "--corrigir", "--verificar", "--voltar", "--voltar-todas", "--recuperar")) and not travar():
    print("outra execucao segurando a trava ha 4 min - saindo")
    sys.exit(0)
import atexit
atexit.register(destravar)
if "--recuperar" in a:
    # tarefa ja no D:\veo\venv sem registro (perdido): reconstroi acoes_antes trocando o veo pelo python original
    # que o uso real registrou (unificacao.json) -> volta automatica passa a valer para ela de novo
    dd = ler()
    uni = {t["tarefa"]: t for t in json.loads(UNI.read_text(encoding="utf-8"))["tarefas"]}
    for nome in a[a.index("--recuperar") + 1:]:
        if nome in dd:
            continue
        i = info(nome)
        velhos = [x for x in uni.get(nome, {}).get("py", []) if not x.startswith(r"d:\veo\venv")]
        if not velhos:
            print(nome, ": nao sei o python antigo"); continue
        antigo = velhos[0]
        antes = []
        for ac in i["acoes"]:
            f = lambda t: re.sub(r"D:\\veo\\venv\\Scripts\\python(w?)\.exe",
                                 lambda m: re.sub(r"python[w]?\.exe$", "python" + m.group(1) + ".exe", antigo, flags=re.I), t or "", flags=re.I)
            antes.append({"e": f(ac["e"]), "a": f(ac.get("a")), "d": ac.get("d")})
        dd[nome] = {"estado": "trocada", "em": "2026-11-26T12:38:00", "acoes_antes": antes, "acoes_depois": i["acoes"],
                    "res_antes": 0, "ultima_antes": "", "obs": "registro recuperado 26/11 (perdido na corrida)"}
        print(nome, ": registro recuperado, antigo =", antigo)
    salvar(dd)
elif "--bats" in a:
    aplicar_bats(int(a[a.index("--max") + 1]) if "--max" in a else 999)
elif "--aplicar" in a:
    aplicar(int(a[a.index("--max") + 1]) if "--max" in a else 999, a[a.index("--so") + 1] if "--so" in a else None)
elif "--verificar" in a:
    verificar()
elif "--voltar-todas" in a:
    dd = ler()
    for n in [n for n, r in dd.items() if r.get("estado") in ("trocada", "confirmada")]:
        voltar(n, dd, "volta manual (todas)")
    salvar(dd)
elif "--voltar" in a:
    dd = ler()
    voltar(a[a.index("--voltar") + 1], dd, "volta manual")
    salvar(dd)
else:
    status()
