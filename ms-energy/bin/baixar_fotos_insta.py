# -*- coding: utf-8 -*-
"""Fotos reais da MS Energy para os videos: baixa do Instagram @msenergycap (Graph API) e classifica por visao.

Dono 22/10/2026: "fotos tem no proprio insta". So entra conteudo de antes de 07/2025 (dali em diante sao memes/IA).
Rodar de novo pega posts novos e so classifica o que falta (retomavel: cada resposta vai pro indice na hora).

    python baixar_fotos_insta.py            # baixa + classifica
    python baixar_fotos_insta.py --so-baixar
"""
import argparse
import base64
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

DIR = Path(r"D:\ms-energy\assets\fotos_instagram")
INDICE = DIR / "indice.json"
LOGO = Path(r"D:\ms-energy\assets\logo\perfil_instagram.jpg")
CREDS = Path(r"D:\credenciais-canais\instagram_contas.json")
GATEWAY = Path(r"D:\veo\beta\secrets\gateway.json")
BASE = "https://graph.instagram.com/v21.0"
ATE = "2025-07-01"  # depois disso o perfil so tem meme/IA

PERGUNTA = (
    "Esta imagem e um post antigo do Instagram ou uma foto da galeria de uma empresa de energia solar no Para (Brasil). "
    "Responda SO um JSON:\n"
    '{"foto_real": true se for FOTOGRAFIA real (nao arte, flyer, montagem, desenho ou print),\n'
    ' "texto_sobreposto": "nenhum" | "pouco" | "muito" (letras desenhadas por cima da foto),\n'
    ' "telefone_ou_link": true se aparece telefone, @, site ou QR,\n'
    ' "mostra": "placas_no_telhado" | "usina_no_solo" | "equipe_instalando" | "cliente_com_placas" | "casa" | '
    '"equipamento" | "conta_de_luz" | "outro",\n'
    ' "rostos": numero de rostos visiveis,\n'
    ' "qualidade": 1 a 10 (nitidez, luz, enquadramento),\n'
    ' "foco_x": 0.0 a 1.0 (posicao horizontal do assunto principal, para recortar vertical 9:16),\n'
    ' "boa_para_video": true se e foto real, nitida, SEM texto/telefone por cima e mostra energia solar/instalacao,\n'
    ' "descricao_en": "uma frase objetiva em ingles: o que aparece, onde, luz, angulo da camera"}'
)


def _get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def _api(path, **params):
    return json.loads(_get(f"{BASE}/{path}?{urllib.parse.urlencode(params)}").decode())


def _token():
    contas = json.load(open(CREDS, encoding="utf-8"))
    return next(c for c in contas if "msenergycap" in c["name"].lower())["data"]["accessToken"]


def _carregar():
    return json.loads(INDICE.read_text("utf-8")) if INDICE.exists() else {}


def _salvar(ind):
    INDICE.write_text(json.dumps(ind, ensure_ascii=False, indent=1), "utf-8")


def baixar():
    DIR.mkdir(parents=True, exist_ok=True)
    LOGO.parent.mkdir(parents=True, exist_ok=True)
    tok = _token()
    perfil = _api("me", fields="username,profile_picture_url", access_token=tok)
    if perfil.get("profile_picture_url"):
        LOGO.write_bytes(_get(perfil["profile_picture_url"]))
        print("logo:", LOGO)
    ind = _carregar()
    campos = ("id,media_type,media_url,thumbnail_url,permalink,timestamp,caption,"
              "children{id,media_type,media_url,thumbnail_url}")
    res = _api("me/media", fields=campos, limit=50, access_token=tok)
    novos = 0
    while True:
        for m in res.get("data", []):
            if m["timestamp"][:10] >= ATE:
                continue
            filhos = m.get("children", {}).get("data") or [m]
            for f in filhos:
                url = f.get("thumbnail_url") if f.get("media_type") == "VIDEO" else f.get("media_url")
                if not url:
                    continue
                nome = f"{m['timestamp'][:10]}_{m['id']}" + (f"_{f['id']}" if f is not m else "") + ".jpg"
                if nome in ind:
                    continue
                try:
                    Image.open(io.BytesIO(_get(url))).convert("RGB").save(DIR / nome, quality=95)
                except Exception as e:  # noqa: BLE001
                    print("falhou", nome, e)
                    continue
                ind[nome] = {"media_id": m["id"], "data": m["timestamp"][:10], "permalink": m.get("permalink"),
                             "tipo": "frame_de_video" if f.get("media_type") == "VIDEO" else "foto",
                             "legenda": (m.get("caption") or "")[:200]}
                novos += 1
        _salvar(ind)
        nxt = res.get("paging", {}).get("next")
        if not nxt:
            break
        res = json.loads(_get(nxt).decode())
    print(f"baixadas agora: {novos} | no indice: {len(ind)}")


def _visao(img_path, gw):
    im = Image.open(img_path).convert("RGB")
    im.thumbnail((1024, 1024))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    corpo = {"model": "gemini/gemini-3.5-flash", "max_tokens": 400, "messages": [{"role": "user", "content": [
        {"type": "text", "text": PERGUNTA},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}}]}]}
    url = gw.get("gateway_url", "http://157.173.207.22:20128").rstrip("/") + "/v1/chat/completions"
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers={
        "Authorization": "Bearer " + gw["gateway_key"], "Content-Type": "application/json"})
    txt = json.loads(urllib.request.urlopen(req, timeout=90).read())["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0))


def classificar(workers=4):
    """25/10: 4 perguntas de visão ao mesmo tempo e o índice gravado a cada 25 (antes: 1 por vez e o índice inteiro
    regravado a cada foto — 4.600 fotos levaram ~2h40 na madrugada de 25/10)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    gw = json.loads(GATEWAY.read_text(encoding="utf-8"))
    ind = _carregar()
    faltam = [nome for nome, item in sorted(ind.items()) if "visao" not in item]
    feitos = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futuros = {ex.submit(_visao, DIR / nome, gw): nome for nome in faltam}
        for i, fut in enumerate(as_completed(futuros), 1):
            nome = futuros[fut]
            try:
                v = fut.result()
            except Exception as e:  # noqa: BLE001
                print(f"[{i}/{len(faltam)}] {nome}: erro {str(e)[:100]}")
                continue
            ind[nome]["visao"] = v
            feitos += 1
            if feitos % 25 == 0:
                _salvar(ind)
            print(f"[{i}/{len(faltam)}] {nome}: boa={v.get('boa_para_video')} mostra={v.get('mostra')} "
                  f"q={v.get('qualidade')}", flush=True)
    _salvar(ind)
    boas = [n for n, it in ind.items() if (it.get("visao") or {}).get("boa_para_video")]
    print(f"classificadas: {sum(1 for it in ind.values() if 'visao' in it)}/{len(ind)} | boas para video: {len(boas)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-baixar", action="store_true")
    a = ap.parse_args()
    baixar()
    if not a.so_baixar:
        classificar()
