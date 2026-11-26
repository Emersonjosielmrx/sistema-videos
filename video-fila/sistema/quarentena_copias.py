# copias MORTAS de programas duplicados (nenhum uso real, nenhuma tarefa, nao importadas por arquivo vivo) -> quarentena
# por ARQUIVO (move p/ D:\sistema\quarentena\<caminho>, sem juncao: e arquivo solto). Indice no mesmo INDICE.json.
import os, re, json, hashlib, shutil, time
from pathlib import Path
V=set()
for f in Path(r"D:\sistema\mapa\uso").glob("uso_*.jsonl"):
    for l in f.read_text(encoding="utf-8",errors="ignore").splitlines():
        try: j=json.loads(l)
        except ValueError: continue
        V|={x.lower() for x in j.get("locais",[])}; V.add((j.get("main") or "").lower())
try: V|=set(json.loads(Path(r"D:\sistema\mapa\mapa_vivo.json").read_text(encoding="utf-8"))["vivos"])
except Exception: pass
CAT=json.loads(Path(r"D:\sistema\catalogo\sistema.json").read_text(encoding="utf-8-sig"))
CMDS=" ".join(d["cmd"].lower() for p in CAT["projetos"].values() for d in p.get("tarefas_detalhe",{}).values() if d.get("ligada"))
raizes=[r"D:\postador-de-videos\bin",r"D:\recapd-ambientes\producao\bin",r"D:\hipercool-videos\bin",r"D:\video-fila",r"D:\hipercool-materiais\comum",r"D:\manhwa-react\mr",r"D:\veo\beta"]
g={}
for r in raizes:
    rr=os.path.realpath(r)
    if os.path.isdir(rr):
        for f in os.listdir(rr):
            if f.endswith(".py") and f not in ("__init__.py","sitecustomize.py"): g.setdefault(f,[]).append(os.path.join(r,f))
# texto de todo .py VIVO (para ver se algum importa/chama o nome)
txt_vivo=""
for v in list(V)[:3000]:
    if v.endswith(".py") and os.path.isfile(v):
        try: txt_vivo+=open(v,encoding="utf-8",errors="ignore").read()+"\n"
        except OSError: pass
agora=time.time(); mover=[]
for n,L in g.items():
    if len(L)<2: continue
    if len({hashlib.md5(open(x,'rb').read()).hexdigest() for x in L})<2: continue
    if any(x.lower() in V or os.path.realpath(x).lower() in V for x in L): continue   # tem copia viva -> nao mexe (manual)
    mod=n[:-3]
    if re.search(r"\b(import|from)\s+"+re.escape(mod)+r"\b", txt_vivo) or n.lower() in CMDS or mod in CMDS: continue
    for x in L:
        try:
            if agora-os.path.getmtime(x) < 14*86400: break
        except OSError: break
    else:
        mover += L
Q=Path(r"D:\sistema\quarentena"); IND=Q/"INDICE.json"; ind=json.loads(IND.read_text(encoding="utf-8")) if IND.exists() else []
n=0; mb=0
for x in mover:
    real=os.path.realpath(x)
    dest=Q/real[3:]; dest.parent.mkdir(parents=True,exist_ok=True)
    mb+=os.path.getsize(real); shutil.move(real,dest)
    ind.append({"original":real,"destino":str(dest),"em":time.strftime("%Y-%m-%dT%H:%M:%S"),"motivo":"copia morta de programa duplicado (nenhum uso real/tarefa/import vivo, 14+ dias)","mb":round(os.path.getsize(dest)/1e6,2),"tipo":"arquivo"})
    n+=1
IND.write_text(json.dumps(ind,ensure_ascii=False,indent=1),encoding="utf-8")
print(f"copias mortas movidas p/ quarentena: {n} arquivos ({mb/1e6:.1f} MB) de {len({os.path.basename(x) for x in mover})} programas")
