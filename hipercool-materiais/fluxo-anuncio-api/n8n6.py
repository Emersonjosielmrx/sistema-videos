"""Chamadas à API do n8n6. Uso:
  python n8n6.py credencial                  -> cria (uma vez) a credencial Header Auth da JSON2Video e mostra o id
  python n8n6.py importa <fluxo.json>        -> cria o fluxo (ou atualiza, se já existe um com o mesmo nome) e ativa
  python n8n6.py get <id>                    -> baixa o fluxo para <id>.json"""
import json, sys, urllib.request, urllib.error
from pathlib import Path

AQUI = Path(__file__).parent
BASE = "https://n8n6.inovareinteligenciaartificial.com/api/v1"
CHAVE = (AQUI / "n8n6_chave.txt").read_text().strip()


def api(metodo, caminho, corpo=None):
    req = urllib.request.Request(BASE + caminho, method=metodo, data=json.dumps(corpo).encode() if corpo is not None else None,
                                 headers={"X-N8N-API-KEY": CHAVE, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            t = r.read()
            return r.status, json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        t = e.read()
        try:
            return e.code, json.loads(t)
        except Exception:  # noqa: BLE001
            return e.code, {"raw": t[:500].decode(errors="ignore")}


acao = sys.argv[1]
if acao == "credencial":
    # python n8n6.py credencial [nome arquivo_da_chave linha]   (padrão: JSON2Video)
    nome = sys.argv[2] if len(sys.argv) > 2 else "JSON2Video (x-api-key)"
    arq = sys.argv[3] if len(sys.argv) > 3 else "j2v_chave.txt"
    linha = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    valor = (AQUI / arq).read_text().split()[linha]
    st, r = api("POST", "/credentials", {"name": nome, "type": "httpHeaderAuth", "data": {"name": "x-api-key", "value": valor}})
    print(st, {k: r.get(k) for k in ("id", "name", "type", "message")})
elif acao == "importa":
    w = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    corpo = {k: w[k] for k in ("name", "nodes", "connections", "settings") if k in w}
    corpo["settings"] = {k: v for k, v in corpo.get("settings", {}).items() if k in ("executionOrder", "saveManualExecutions", "executionTimeout", "saveDataErrorExecution", "saveDataSuccessExecution", "saveExecutionProgress", "timezone", "callerPolicy")}
    st, lista = api("GET", "/workflows?limit=250&name=" + urllib.request.quote(w["name"]))
    existe = next((x for x in lista.get("data", []) if x["name"] == w["name"]), None)
    if existe:
        api("POST", f"/workflows/{existe['id']}/deactivate")
        st, r = api("PUT", f"/workflows/{existe['id']}", corpo)
        wid = existe["id"]
        if st >= 300 and existe.get("active"):  # 30/10: PUT recusado deixava o fluxo do ar desligado
            api("POST", f"/workflows/{wid}/activate")
    else:
        st, r = api("POST", "/workflows", corpo)
        wid = r.get("id")
    print("salvar:", st, wid, r.get("message", ""))
    if wid and st < 300:
        st, r = api("POST", f"/workflows/{wid}/activate")
        print("ativar:", st, r.get("active"), r.get("message", ""))
elif acao == "get":
    st, r = api("GET", f"/workflows/{sys.argv[2]}")
    (AQUI / f"{sys.argv[2]}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(st, r.get("name"), r.get("active"))
