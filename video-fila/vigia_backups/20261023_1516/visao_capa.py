# -*- coding: utf-8 -*-
# COMUM — fonte única: D:\hipercool-materiais\comum\visao_capa.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir visao_capa.py --de <projeto>
"""visao_capa.py — checagem por visão comum das capas IA (hipercool capa_ia, recapd capa_ia_anime, historias
capa_ia_historias).

Cada projeto tem a sua pergunta (o que é proibido muda por tipo de canal); aqui fica o que vale pra todos:
- DEFEITOS: corpo malformado (braço/cabeça a mais, duas bundas, corpo derretendo) e gente sobrando no fundo —
  dono 19-20/10, pego primeiro no hipercool;
- pergunta_pose(desc): a cena bate com a pose pedida (quem senta, deita, ajoelha, em cima de quem);
- perguntar(): Gemini e, se ele falhar (429/recusa/JSON quebrado), o Claude pelo gateway — antes o anime e as
  histórias aceitavam a capa SEM checar quando o Gemini dava 429;
- defeitos(r): motivos de reprovação desses campos.
"""
import base64
import json
import re
import urllib.request

VISAO_RESERVA = "kr/claude-sonnet-4.5"  # dono 20/10: Haiku recusa checar capa sensual

DEFEITOS = (
    '"anatomia": true/false (look at EACH body closely; true if any is malformed: extra or missing arms, legs, hands '
    'or heads, limbs merged together or not attached to the body, one body split into separate pieces, a duplicated '
    'body part on one person such as two butts, two pairs of hips or extra breasts, a body melting into furniture or '
    'into another person), "figurantes": true/false (extra people in the background besides the main characters)')


def pergunta_pose(desc):
    """Trecho a somar no fim da pergunta (fora do JSON dela) quando há pose pedida."""
    return (' Add to the same JSON: "pose_certa": true/false (the picture shows exactly this arrangement - '
            'check carefully who sits, lies, kneels or stands, on what or on whom, and where each person is: "'
            + desc + '"), "pose_erro": what differs, max 12 words, or "".')


def _gateway_texto(b, mime, pergunta, gateway, modelo, max_tokens):
    base, tok = gateway
    corpo = {"model": modelo, "max_tokens": max_tokens, "temperature": 0.1, "messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(b).decode()}"}},
        {"type": "text", "text": pergunta}]}]}
    req = urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=120) as r:
        c = json.loads(r.read())["choices"][0]["message"]["content"]
    return c if isinstance(c, str) else "".join(p.get("text", "") for p in c)


def mime_de(b):
    return "image/png" if b[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"  # o gateway devolve JPEG no .png


def perguntar(b, pergunta, gateway=None, modelo=VISAO_RESERVA, max_tokens=500):
    """JSON (dict) da visão sobre a imagem (bytes): Gemini, depois o gateway (base, token) se houver. None se os dois
    falharem. gemini_llm é o do projeto que chamou (cada um tem o seu no bin/)."""
    mime = mime_de(b)

    def gemini():
        import gemini_llm
        return gemini_llm.describe_image(b, pergunta, mime=mime, max_tokens=max_tokens, temperature=0.1)
    tentativas = [gemini]
    if gateway and gateway[0] and gateway[1]:
        tentativas.append(lambda: _gateway_texto(b, mime, pergunta, gateway, modelo, max_tokens))
    for perguntar_a in tentativas:
        try:
            return json.loads(re.search(r"\{.*\}", perguntar_a() or "", re.S).group(0))
        except Exception:  # noqa: BLE001  (cota, recusa, rede, JSON quebrado: próxima)
            continue
    return None


def defeitos(r, figurantes=True):
    """Motivos de reprovação por DEFEITOS/pose (lista vazia = passou). figurantes=False onde multidão faz parte da cena."""
    if not r:
        return []
    m = []
    if r.get("anatomia"):
        m.append("anatomia")
    if figurantes and r.get("figurantes"):
        m.append("figurantes")
    if r.get("pose_certa") is False:
        m.append("pose errada" + (f" ({r.get('pose_erro')})" if r.get("pose_erro") else ""))
    return m
