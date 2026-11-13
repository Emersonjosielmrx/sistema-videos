"""V6 (03/11): cards em SVG (cantos redondos, degradê, brilho, sombra) que o ffmpeg da nuvem lê (librsvg).
O 🧩 Monta a edição devolve `cards` (base64 de uma lista de SVGs); aqui o fluxo ganha:
- 💾 Guarda os cards (1 dia): Redis <pre>arq:cards-<job> logo depois de guardar o .ass;
- 📖 Lê o arquivo: cards-<job>-<n>.svg lê a chave cards-<job>;
- 🧩 Vira arquivo: entrega o SVG número <n> (image/svg+xml) para o ffmpeg na nuvem.
Usado por gera_versoes.py: aplica(w, nivel)."""
import uuid


def aplica(w, nivel):
    pre = f"ed{nivel}:"
    nos = {n["name"]: n for n in w["nodes"]}
    gt = nos["💾 Guarda os textos (1 dia)"]
    novo = {"parameters": {"operation": "set", "key": f"={pre}arq:cards-{{{{ $('🧩 Pega o vídeo').first().json.job }}}}",
                           "value": "={{ $('🧩 Monta a edição').first().json.cards || '' }}", "keyType": "string", "expire": True, "ttl": 86400},
            "name": "💾 Guarda os cards (1 dia)", "type": "n8n-nodes-base.redis", "typeVersion": gt["typeVersion"],
            "position": [gt["position"][0] + 150, gt["position"][1] + 160], "credentials": gt["credentials"],
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"editor-v{nivel}|💾 Guarda os cards (1 dia)"))}
    w["nodes"].append(novo)
    w["connections"][novo["name"]] = w["connections"]["💾 Guarda os textos (1 dia)"]
    w["connections"]["💾 Guarda os textos (1 dia)"] = {"main": [[{"node": novo["name"], "type": "main", "index": 0}]]}

    la = nos["📖 Lê o arquivo"]["parameters"]
    antes = "String($json.query.id || '').replace(/[^a-z0-9.-]/g, '')"
    assert antes in la["key"]
    la["key"] = la["key"].replace(antes, antes + ".replace(/^(cards-[a-z0-9]+)-[0-9]+\\.svg$/, '$1')")

    c = nos["🧩 Vira arquivo"]["parameters"]
    antes = "const b64 =String($input.first().json.arquivo || '');\n"
    assert c["jsCode"].count(antes) == 1
    c["jsCode"] = c["jsCode"].replace(antes, antes +
        "const cd = /^cards-[a-z0-9]{6,40}-([0-9]{1,2})\\.svg$/.exec(id);   // V6: os cards em SVG de cada edição\n"
        "if (cd) {\n"
        "  let lista = [];\n"
        "  try { lista = JSON.parse(Buffer.from(b64, 'base64').toString('utf8')); } catch (e) {}\n"
        "  const svg = lista[Number(cd[1])];\n"
        "  if (!svg) return [{ json: { existe: false } }];\n"
        "  return [{ json: { existe: true }, binary: { data: await this.helpers.prepareBinaryData(Buffer.from(svg, 'utf8'), id, 'image/svg+xml') } }];\n"
        "}\n")
    return w
