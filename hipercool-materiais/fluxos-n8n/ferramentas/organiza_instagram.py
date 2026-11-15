# Renomeia os fluxos de Instagram prontos com o prefixo "📸 INSTAGRAM ·" e põe a etiqueta "instagram" (só nome e etiqueta).
import sys, json
sys.path.insert(0, r"D:\hipercool-materiais\fluxos-n8n\ferramentas")
from n8n_servidor import api
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NOVOS = {
    "1pizKCLREiCiVp0A": "📸 INSTAGRAM · Carrossel com IA, Aprovação e Agendamento",
    "Zj1EwQeAGBTwpShB": "📸 INSTAGRAM · Relatório do Perfil com IA - ok",
    "eTZ7m4360dYqNJuU": "📸 INSTAGRAM · Post Conversado com IA (chat + foto opcional) - off",
    "Cy1QZOsj5WimgWnC": "📸 INSTAGRAM · 30 Dias de Posts Prontos com IA (calendário, artes e publicação automática) - ok",
    "zyUVNOKI9UPm3Tz6": "📸 INSTAGRAM · Sorteio parte 1 (captura comentários, DM, valida seguidor) — recebe os eventos da Meta",
}
st, tags = api("GET", "/tags?limit=250")
tag = next((t for t in tags.get("data", []) if t["name"] == "instagram"), None)
if not tag:
    st, tag = api("POST", "/tags", {"name": "instagram"}); print("etiqueta criada", st)
for wid, nome in NOVOS.items():
    st, w = api("GET", f"/workflows/{wid}")
    if st >= 300:
        print("não achei", wid); continue
    antigo = w["name"]
    if antigo != nome:
        ativo = w.get("active")
        corpo = {"name": nome, "nodes": w["nodes"], "connections": w["connections"], "settings": {k: v for k, v in (w.get("settings") or {}).items() if k in ("executionOrder", "saveManualExecutions", "callerPolicy", "errorWorkflow", "timezone", "executionTimeout", "saveDataErrorExecution", "saveDataSuccessExecution", "saveExecutionProgress")}}
        st, r = api("PUT", f"/workflows/{wid}", corpo)
        print(st, antigo[:50], "->", nome[:60], r.get("message", ""))
        if ativo and not r.get("active", True):
            print("  reativando", api("POST", f"/workflows/{wid}/activate")[0])
    atuais = [{"id": t["id"]} for t in (w.get("tags") or [])]
    if not any(t["id"] == tag["id"] for t in atuais):
        st, r = api("PUT", f"/workflows/{wid}/tags", atuais + [{"id": tag["id"]}]); print("  etiqueta", st)
