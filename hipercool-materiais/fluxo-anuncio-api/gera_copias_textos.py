"""Gera as CÓPIAS "textos novos" das 3 versões (V1b, V2b, V3b) a partir dos fluxos já prontos (fluxo_v1/v2/v3.json),
sem mexer neles: troca só o código do nó que monta o filme, os caminhos dos webhooks, as chaves do Redis e o nome.
Uso: python gera_copias_textos.py"""
import json, re, uuid
from pathlib import Path

AQUI = Path(__file__).parent
COPIAS = [
    # (pasta original, pasta da cópia, nó que monta o filme, arquivo .js da cópia, sufixo do webhook, prefixo Redis, caminho da página, nome)
    ("v1", "v1b", "🧩 Monta o filme (JSON2Video)", "monta_filme.js", "j2v", "j2vb", "anvj2v", "anvj2vb", "anuncio-j2v", "anuncio-j2vb", "anuncio-video", "anuncio-video-b",
     "Vídeo de Anúncio com IA · JSON2Video · textos novos - V1b"),
    ("v2", "v2b", "🧩 Monta o filme (Shotstack)", "monta_filme.js", "ss", "ssb", "anvss", "anvssb", "anuncio-ss", "anuncio-ssb", "anuncio-shotstack", "anuncio-shotstack-b",
     "Vídeo de Anúncio com IA · Shotstack · textos novos - V2b"),
    ("v3", "v3b", "🧩 Monta o filme (Very Good FFmpeg)", "monta_ffmpeg.js", "ff", "ffb", "anvff", "anvffb", "anuncio-ff", "anuncio-ffb", "anuncio-ffmpeg", "anuncio-ffmpeg-b",
     "Vídeo de Anúncio com IA · ffmpeg na nuvem · textos novos - V3b"),
]
for orig, copia, no_filme, arq_js, suf, suf_b, red, red_b, pag, pag_b, cam, cam_b, nome in COPIAS:
    t = (AQUI / orig / f"fluxo_{orig}.json").read_text(encoding="utf-8")
    t = t.replace(f"anuncio-video-{suf}", f"anuncio-video-{suf_b}")
    t = t.replace(f"{red}:", f"{red_b}:")
    t = re.sub(rf"{pag}/(\$\{{[a-z]+\}}|C[ÓO]DIGO)/{cam}\b", rf"{pag_b}/\1/{cam_b}", t)
    t = t.replace(f'":id/{cam}"', f'":id/{cam_b}"').replace(f"`:id/{cam}`", f"`:id/{cam_b}`")
    t = t.replace(f'"webhookId": "{pag}"', f'"webhookId": "{pag_b}"')
    w = json.loads(t)
    w["id"] = (orig.upper() + "b" + uuid.uuid4().hex)[:16]
    w["name"] = nome
    for n in w["nodes"]:
        n["id"] = str(uuid.uuid4())
        if "webhookId" in n and n["webhookId"] != pag_b:
            n["webhookId"] = str(uuid.uuid4())
    alvo = next(n for n in w["nodes"] if n["name"] == no_filme)
    alvo["parameters"]["jsCode"] = (AQUI / copia / arq_js).read_text(encoding="utf-8").strip() + "\n"
    tudo = json.dumps(w, ensure_ascii=False)
    assert f"anuncio-video-{suf}\"" not in tudo and f"anuncio-video-{suf}-" not in tudo, "sobrou webhook da versão original"
    assert f"{red}:" not in tudo, "sobrou chave do Redis da versão original"
    caminhos = re.findall(r'"path": "([^"]+)"', tudo)
    (AQUI / copia / f"fluxo_{copia}.json").write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
    print(copia, "ok:", len(w["nodes"]), "nós |", caminhos)
