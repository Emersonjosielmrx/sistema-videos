# Acrescenta no "Sorteio parte 1" um nó que repassa as MENSAGENS (saída 0 do Instagram Trigger) para a Central (/webhook/insta-eventos).
# Não altera nada do que já existe: só adiciona uma ligação paralela. Backup em servidor-n8n6/_backup_sorteio_antes_14nov.json.
import sys
from pathlib import Path
sys.path.insert(0, r"D:\hipercool-materiais\fluxos-n8n\ferramentas")
from n8n_servidor import api
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WID = "zyUVNOKI9UPm3Tz6"
SEG = (Path(__file__).parent / ".segredo_eventos").read_text().strip()
NOME = "📨 Repassa para a Central do Instagram"
st, w = api("GET", f"/workflows/{WID}")
w["nodes"] = [n for n in w["nodes"] if n["name"] != NOME]
w["nodes"].append({"name": NOME, "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [-200, 900],
                   "onError": "continueRegularOutput",
                   "parameters": {"method": "POST", "url": "https://webhookn8n6.inovareinteligenciaartificial.com/webhook/insta-eventos",
                                  "sendBody": True, "specifyBody": "json",
                                  "jsonBody": "={{ JSON.stringify({ segredo: '" + SEG + "', evento: $json }) }}",
                                  "options": {"timeout": 15000, "response": {"response": {"neverError": True}}}}})
saidas = w["connections"]["Instagram Trigger"]["main"]
saidas[0] = [c for c in saidas[0] if c["node"] != NOME] + [{"node": NOME, "type": "main", "index": 0}]
corpo = {"name": w["name"], "nodes": w["nodes"], "connections": w["connections"],
         "settings": {k: v for k, v in (w.get("settings") or {}).items() if k in ("executionOrder", "saveManualExecutions", "callerPolicy", "errorWorkflow", "timezone", "executionTimeout")}}
api("POST", f"/workflows/{WID}/deactivate")
st, r = api("PUT", f"/workflows/{WID}", corpo); print("salvar", st, r.get("message", ""))
st2, r2 = api("POST", f"/workflows/{WID}/activate"); print("ativar", st2, r2.get("active"), r2.get("message", ""))
