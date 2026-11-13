import json
from pathlib import Path

f=Path("D:/recapd-ambientes/producao/workspace/pipeline_metrics.jsonl")
if f.exists():
    for ln in f.read_text('utf-8').splitlines():
        print(ln)
else:
    print("Nenhuma metrica ainda. Elas serao geradas nas proximas execucoes.")
