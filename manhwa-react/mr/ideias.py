"""Vigia de formatos: analisa o VIDEO REAGIDO (frames + narracao) e registra ideias de formatos que nos mesmos poderiamos produzir.

Saida acumulada em ideias/ideias.json e ideias/IDEIAS.md (quadro de ideias, ordenado por potencial).
"""
import base64
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from .common import log

RECURSOS = ("ffmpeg; TTS em portugues (edge-tts gratis, ElevenLabs, Gemini TTS); geracao de imagem por IA (Gemini/OmniRoute, Pollinations); "
            "geracao de video por IA (Veo 3 via Google Flow); 341 trilhas de musica; 650 sons de meme + 800 SFX; overlays animados (fogo, raio, confete, "
            "legendas estilo Hormozi); 86 mil paineis de manhwa; fotos do criador; narracao com LLM; Playwright para capturar sites; "
            "pipeline de recap de anime/manhwa; webcam/react.")

PROMPT = """Voce e um estrategista de canais de Shorts no YouTube Brasil. Vai receber frames e a narracao de um VIDEO QUE O CRIADOR ESTA REAGINDO
(ignore o criador e a webcam; analise so o conteudo reagido). Objetivo: descobrir se esse FORMATO de video poderia ser produzido por nos mesmos,
sem precisar de gravacao ao vivo, com estes recursos: {recursos}

Responda SOMENTE um JSON:
{{
 "formato": "nome curto do formato (ex.: 'so trilha + fotos de objetos dos anos 90', 'leitura de comentarios com musica', 'ranking com narracao IA')",
 "descricao": "o que o video faz em 1-2 frases (estrutura, ritmo, o que prende)",
 "replicavel": true,
 "como_fazer": "passo a passo curto e concreto de como produzir isso com os recursos acima (3-6 passos)",
 "ferramentas": ["ffmpeg", "TTS", "..."],
 "fonte_de_material": "de onde tirar imagens/clipes/dados (ex.: fotos de dominio publico, Pexels, prints, geracao IA)",
 "esforco": "baixo|medio|alto",
 "potencial": 7,
 "por_que_viraliza": "1 frase sobre o gatilho de retencao/compartilhamento",
 "exemplo_roteiro": "um exemplo de 3-5 linhas de roteiro/legenda para um Short nesse formato, em portugues",
 "nicho_canal": "qual dos nossos canais encaixa (manhwareact|cenareact|inventoreact|novo canal: nome sugerido)",
 "tags": ["3-6 tags"]
}}
Regras: "replicavel"=false se depender de uma pessoa especifica, de gravacao presencial ou de direitos (filme/serie/anime inteiros). "potencial" de 1 a 10
considerando quanto o formato e barato, repetivel e viral. Seja especifico: nada de generico."""


def _frames(cfg, video, layout, n=4):
    """n frames da regiao de conteudo (jpeg 512px) como bytes."""
    cx0, cy0, cx1, cy1 = layout.get("content") or [0, 0, layout["width"], layout["height"]]
    w, h = cx1 - cx0, cy1 - cy0
    from .common import ffprobe_json
    dur = float(ffprobe_json(cfg, video)["format"]["duration"])
    out = []
    for i in range(n):
        t = dur * (0.15 + 0.7 * i / max(1, n - 1))
        tmp = Path(tempfile.gettempdir()) / f"mr_idea_{i}.jpg"
        subprocess.run([cfg["paths"]["ffmpeg"], "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                        "-vf", f"crop={w}:{h}:{cx0}:{cy0},scale=512:-2", "-q:v", "4", str(tmp)], check=False)
        if tmp.exists():
            out.append(tmp.read_bytes())
            tmp.unlink(missing_ok=True)
    return out


def _ask(cfg, frames, text, tier="sonnet"):
    from .llm import _proxy, extract_json
    px = _proxy(cfg)
    base = (px.get("base_url") or "").rstrip("/")
    key = px.get("auth_token")
    models = dict(cfg["editorial"].get("models", {}))
    models.update({k: v for k, v in (px.get("models") or {}).items() if v})
    model = models.get(tier) or models.get("opus")
    if not base or not key or not model:
        return None
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(f).decode()}} for f in frames]
    content.append({"type": "text", "text": text})
    body = {"model": model, "max_tokens": 1500, "temperature": 0.4, "system": PROMPT.format(recursos=RECURSOS), "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request(base + "/v1/messages", data=json.dumps(body).encode("utf-8"),
                                 headers={"x-api-key": key, "Authorization": f"Bearer {key}", "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=180)
        d = json.loads(r.read().decode("utf-8"))
        txt = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
        return extract_json(txt)
    except Exception as e:  # noqa: BLE001
        log(f"ideias: LLM falhou ({str(e)[:120]})")
        return None


def analyze_idea(cfg, video, layout, segments, ed=None):
    frames = _frames(cfg, video, layout)
    if not frames:
        return None
    content_lines = [f"- {s['text']}" for s in segments if s.get("speaker") == "content"]
    creator_lines = [f"- {s['text']}" for s in segments if s.get("speaker") != "content"]
    text = "NARRACAO/AUDIO DO VIDEO REAGIDO:\n" + ("\n".join(content_lines) or "(sem narracao propria; so musica/ambiente)")
    text += "\n\nCOMENTARIOS DO CRIADOR (so contexto):\n" + "\n".join(creator_lines[:12])
    if ed:
        text += f"\n\nASSUNTO: {ed.get('topic')} | OBRA: {ed.get('work')}"
    data = _ask(cfg, frames, text, tier=cfg.get("ideas", {}).get("tier", "sonnet"))
    if not data or not data.get("formato"):
        return None
    data["video"] = Path(video).name
    data["data"] = time.strftime("%Y-%m-%d")
    try:
        data["potencial"] = int(data.get("potencial", 5))
    except Exception:
        data["potencial"] = 5
    data["replicavel"] = bool(data.get("replicavel", False))
    return data


def _board_paths(cfg):
    root = Path(cfg.get("ideas", {}).get("dir") or (Path(cfg["paths"]["ready"]).parent / "ideias"))
    root.mkdir(parents=True, exist_ok=True)
    return root / "ideias.json", root / "IDEIAS.md"


def save_idea(cfg, idea):
    jp, mp = _board_paths(cfg)
    items = json.load(open(jp, encoding="utf-8")) if jp.exists() else []
    items = [i for i in items if i.get("video") != idea.get("video")]
    items.append(idea)
    json.dump(items, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_board(cfg, items, mp)
    log(f"ideias: '{idea['formato']}' (replicavel={idea['replicavel']}, potencial={idea['potencial']}) -> {mp}")
    return mp


def write_board(cfg, items, mp):
    rep = sorted([i for i in items if i.get("replicavel")], key=lambda i: -i.get("potencial", 0))
    nao = sorted([i for i in items if not i.get("replicavel")], key=lambda i: -i.get("potencial", 0))
    L = ["# Quadro de ideias - formatos que nos mesmos podemos produzir", "",
         f"Gerado automaticamente pelo vigia de formatos a partir dos videos reagidos. {len(rep)} replicaveis, {len(nao)} nao replicaveis.", "",
         "## Replicaveis (ordenado por potencial)", ""]
    for i in rep:
        L += [f"### {i['formato']}  -  potencial {i.get('potencial')}/10, esforco {i.get('esforco')}  -  canal: {i.get('nicho_canal')}", "",
              f"- **Visto em:** {i.get('video')} ({i.get('data')})", f"- **O que e:** {i.get('descricao')}", f"- **Por que viraliza:** {i.get('por_que_viraliza')}",
              f"- **Como fazer:** {i.get('como_fazer')}", f"- **Ferramentas:** {', '.join(i.get('ferramentas') or [])}",
              f"- **Material:** {i.get('fonte_de_material')}", f"- **Exemplo de roteiro:**", "", "```", str(i.get("exemplo_roteiro") or "").strip(), "```", "",
              f"- Tags: {', '.join(i.get('tags') or [])}", ""]
    L += ["## Nao replicaveis (so para referencia)", ""]
    for i in nao:
        L += [f"- **{i['formato']}** ({i.get('video')}): {i.get('descricao')}"]
    mp.write_text("\n".join(L) + "\n", encoding="utf-8")
