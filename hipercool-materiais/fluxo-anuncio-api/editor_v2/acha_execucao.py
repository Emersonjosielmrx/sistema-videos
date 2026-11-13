# Acha a execução do editor que fez um job. python acha_execucao.py <id_fluxo> [job]
import sys
sys.path.insert(0, r"D:\hipercool-materiais\fluxos-n8n\ferramentas")
import n8n_servidor as s  # noqa: E402

st, l = s.api("GET", f"/executions?workflowId={sys.argv[1]}&limit=60")
for e in l["data"]:
    st, r = s.api("GET", f"/executions/{e['id']}?includeData=true")
    rd = r["data"]["resultData"]["runData"]
    if "🧩 Pega o vídeo" in rd:
        job = rd["🧩 Pega o vídeo"][0]["data"]["main"][0][0]["json"].get("job")
        if len(sys.argv) < 3 or sys.argv[2] == job:
            print(e["id"], job, e.get("status"))
