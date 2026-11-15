# Cria um fluxo temporário com webhook que lê o perfil e os 25 últimos posts da conta conectada (credencial do node), chama e apaga.
import json, sys, time, urllib.request, uuid
sys.path.insert(0, r"D:\hipercool-materiais\fluxos-n8n\ferramentas")
from n8n_servidor import api
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CRED = {"instagramAccessTokenApi": {"id": "LWfbyGDT9j3MOBGq", "name": "_lucrocomia_"}}
cam = "tmp-le-perfil-" + uuid.uuid4().hex[:8]
w = {"name": "🧪 TEMP lê perfil (apagar)", "settings": {"executionOrder": "v1"}, "connections": {
        "wh": {"main": [[{"node": "perfil", "type": "main", "index": 0}]]},
        "perfil": {"main": [[{"node": "posts", "type": "main", "index": 0}]]},
        "posts": {"main": [[{"node": "resp", "type": "main", "index": 0}]]}},
     "nodes": [
        {"name": "wh", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 0], "webhookId": cam,
         "parameters": {"path": cam, "responseMode": "responseNode", "options": {}}},
        {"name": "perfil", "type": "n8n-nodes-instagram-token.instagram", "typeVersion": 1, "position": [200, 0], "credentials": CRED,
         "parameters": {"resource": "user", "operation": "getMyProfile"}, "onError": "continueRegularOutput"},
        {"name": "posts", "type": "n8n-nodes-instagram-token.instagram", "typeVersion": 1, "position": [400, 0], "credentials": CRED,
         "parameters": {"resource": "media", "operation": "listMedia", "limit": 5}, "onError": "continueRegularOutput", "alwaysOutputData": True},
        {"name": "resp", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [600, 0],
         "parameters": {"respondWith": "text", "responseBody": "={{ JSON.stringify({ perfil: $('perfil').all().map(i => i.json), posts: $('posts').all().map(i => i.json) }) }}", "options": {}}}]}
st, r = api("POST", "/workflows", w); wid = r.get("id"); print("criado", st, wid, r.get("message", ""))
try:
    st, r2 = api("POST", f"/workflows/{wid}/activate"); print("ativo", st, r2.get("message", ""))
    time.sleep(2)
    out = urllib.request.urlopen(f"https://webhookn8n6.inovareinteligenciaartificial.com/webhook/{cam}", timeout=90).read().decode()
    print(out[:3500])
finally:
    api("POST", f"/workflows/{wid}/deactivate"); print("apagado", api("DELETE", f"/workflows/{wid}")[0])
