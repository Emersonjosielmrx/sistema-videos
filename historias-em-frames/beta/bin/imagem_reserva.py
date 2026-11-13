# -*- coding: utf-8 -*-
# COMUM — fonte única: D:\hipercool-materiais\comum\imagem_reserva.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir imagem_reserva.py --de <projeto>
"""imagem_reserva.py — gerador de imagem de RESERVA das capas IA (hipercool capa_ia, recapd capa_ia_anime, historias
capa_ia_historias), chamado quando o modelo de imagem do gateway OmniRoute não gera (19/10: 403 "Verify your
account" e 429 de cota). GATEWAY liga/desliga o gateway nos três capa_ia: o dono tirou por hora em 20/10; True = ele
volta a ser o 1º (é o das capas boas) e a reserva só entra quando ele falha.

Cloudflare Workers AI (conta grátis: 10 mil neurons/dia, zera 00:00 UTC; passou = HTTP 429, sem cobrança) e
SiliconFlow (internacional, só com saldo: o crédito de boas-vindas acabou no teste de 19/10). Chaves em
secrets/cloudflare.json ("contas": lista; cota acabou numa = usa a próxima) e secrets/siliconflow.json (pasta
central; no PC2, a secrets/ dele).
Custo 1344x768 no Cloudflare: flux-2-klein-4b ~105 neurons (~95 capas/dia); flux-2-dev ~3.750, lucid-origin ~2.850,
phoenix ~2.400 (2-4/dia: fora). SDXL-lightning erra a pose e o filtro dele devolve imagem preta: fora.

Pollinations (gen.pollinations.ai, secrets/pollinations.json), depois do Cloudflare (dono 20/10: fallback, nunca o
1º): só modelo com paid_only=false gasta o saldo grátis. flux.2-klein-4b = o mesmo modelo do Cloudflare SEM o filtro
de saída (faz as poses de RECUSA); z-image-turbo é permissivo (o _checar do capa_ia pega o que passa do ponto). Lá o
tamanho vai em "size" (width/height no /v1 são ignorados: sai 1024x1024). gpt-image, mai-image e flux-1.1-pro de lá
recusam pose sensual. Teste 20/10: hipercool workspace/capas_reserva_teste/alternativas_20out/COMPARATIVO_*.jpg.

Sempre pelo proxy Webshare de secrets/proxies.txt, nunca direto (dono 19/10). As contas grátis do Webshare dividem
os mesmos 10 IPs: usuário "-N" = IP fixo nº N em qualquer conta. Cada conta do Cloudflare sai SEMPRE pelo IP dela
(conta 1 -> IP 1...); se a banda de uma conta do Webshare acabar, tenta o mesmo IP por outra.

Google Flow / Nano Banana 2.1 (D:\\flow-imagens, contas do Veo, 0 crédito) é o 1º desde 22/10 (dono: "nos lugares dos
geradores de imagem coloque esse sistema"): o melhor dos testes. Só existe no PC1 — no PC2 (ou com FLOW_IMAGEM=0, ou
logo depois de uma falha: pausa de 30 min) o cliente devolve None na hora e segue a lista de antes. ~1-2 min por imagem.

RECUSA = pose do hipercool -> modelos onde ela nunca saiu aprovada no teste de 19/10 (3 tentativas nas sensuais, 2 nas
outras; hipercool workspace/capas_reserva_teste/resultado*.json): não gasta cota com elas. No klein-4b o filtro do
Cloudflare barra a imagem pronta ~metade das vezes até nas que passam (montada_peito, harem_disputa, batalha_espada,
magia, duelo, despertar). Lucid/Phoenix recusam o pedido sensual já na entrada.
"""
import base64
import json
import random
from pathlib import Path

import requests

SECRETS = Path(__file__).resolve().parent.parent / "secrets"
GATEWAY = False  # dono 20/10: Gemini do gateway fora por hora (403 "Verify your account"/429 desde 19/10)
FLOW = "flow/nano-banana-2.1"
MODELOS = [FLOW, "@cf/black-forest-labs/flux-2-klein-4b", "pollinations/black-forest-labs/flux.2-klein-4b",
           "pollinations/tongyi-mai/z-image-turbo", "Qwen/Qwen-Image"]
POLLINATIONS_IP = 5  # IP fixo do Webshare; as contas do Cloudflare saem pelo 1-4
TAMANHO = {"16:9": (1344, 768), "9:16": (768, 1344)}
TAMANHO_SF = {"16:9": "1664x928", "9:16": "928x1664"}
PROXY_TENTATIVAS = 4
RECUSA = {p: {"@cf/black-forest-labs/flux-2-klein-4b"} for p in (
    "pernas_pescoco_chao", "pernas_pescoco_deitada", "pernas_pescoco_lado", "montada_costas", "colo_harem",
    "harem_cama", "harem_um_em_cima", "rosto", "contra_monstro", "dupla_batalha")}


def _chave(nome):
    try:
        return json.loads((SECRETS / nome).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _proxies(ip_fixo):
    """Proxies Webshare em ordem aleatória de conta: ip_fixo=N -> usuário '-N' (mesmo IP em todas); None = rotativo."""
    try:
        linhas = [x.strip() for x in (SECRETS / "proxies.txt").read_text(encoding="utf-8").splitlines()
                  if x.strip() and not x.startswith("#")]
    except OSError:
        return []
    random.shuffle(linhas)
    urls = [x if x.startswith("http") else "http://" + x for x in linhas]
    return [u.replace("-rotate:", f"-{ip_fixo}:") for u in urls if "-rotate:" in u] if ip_fixo else urls


def _post(url, ip_fixo=None, **kw):
    """(bytes, content-type) pelo proxy; RuntimeError 'HTTP <código> ...' se o serviço respondeu erro, ou se nenhum
    proxy conectou (não vai direto)."""
    erro = "sem secrets/proxies.txt"
    for p in _proxies(ip_fixo)[:PROXY_TENTATIVAS]:
        try:
            r = requests.post(url, proxies={"http": p, "https": p}, timeout=(20, 180), **kw)
        except requests.RequestException as e:  # proxy fora/sem banda: mesmo IP por outra conta do Webshare
            erro = f"proxy: {type(e).__name__}"
            continue
        if r.status_code == 407:
            erro = "proxy: 407"
            continue
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code} {r.text[:200]}")
        return r.content, r.headers.get("Content-Type", "")
    raise RuntimeError(f"nenhum proxy conectou ({erro})")


def _cloudflare(modelo, prompt, formato):
    c = _chave("cloudflare.json") or {}
    contas = c.get("contas") or ([c] if c.get("account_id") else [])
    if not contas:
        raise RuntimeError("sem secrets/cloudflare.json")
    w, h = TAMANHO[formato]
    for i, conta in enumerate(contas):
        url = f"https://api.cloudflare.com/client/v4/accounts/{conta['account_id']}/ai/run/{modelo}"
        cab = {"Authorization": "Bearer " + conta["api_token"]}
        if "flux-2" in modelo:  # FLUX.2 no Workers AI só aceita multipart
            kw = {"files": {"prompt": (None, prompt), "width": (None, str(w)), "height": (None, str(h))}}
        else:
            kw = {"json": {"prompt": prompt, "width": w, "height": h}}
        try:
            dados, tipo = _post(url, ip_fixo=i % 10 + 1, headers=cab, **kw)
            break
        except RuntimeError as e:  # 429 = cota do dia da conta acabou: vai pra próxima; filtro/erro vale pra todas
            if not str(e).startswith("HTTP 429") or i == len(contas) - 1:
                raise
    if not tipo.startswith("application/json"):
        return dados  # SDXL/Leonardo devolvem a imagem crua
    d = json.loads(dados)
    img = (d.get("result") or {}).get("image")
    if not img:
        raise RuntimeError(str(d.get("errors"))[:200])
    return base64.b64decode(img)


def _siliconflow(modelo, prompt, formato):
    c = _chave("siliconflow.json")
    if not c:
        raise RuntimeError("sem secrets/siliconflow.json")
    dados, _ = _post(c.get("base_url", "https://api.siliconflow.com/v1") + "/images/generations",
                     headers={"Authorization": "Bearer " + c["api_key"]},
                     json={"model": modelo, "prompt": prompt, "image_size": TAMANHO_SF[formato]})
    url = json.loads(dados)["images"][0]["url"]  # link temporário: baixa na hora
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return r.content


def _pollinations(modelo, prompt, formato):
    c = _chave("pollinations.json")
    if not c:
        raise RuntimeError("sem secrets/pollinations.json")
    w, h = TAMANHO[formato]
    dados, _ = _post("https://gen.pollinations.ai/v1/images/generations", ip_fixo=POLLINATIONS_IP,
                     headers={"Authorization": "Bearer " + c["api_key"]},
                     json={"model": modelo, "prompt": prompt, "size": f"{w}x{h}", "n": 1,
                           "response_format": "b64_json"})
    img = ((json.loads(dados).get("data") or [{}])[0]).get("b64_json")
    if not img:
        raise RuntimeError(f"pollinations sem imagem: {dados[:200]!r}")
    return base64.b64decode(img)


def _flow(prompt, formato):
    import sys
    import tempfile
    sys.path.insert(0, r"D:\flow-imagens")
    try:
        import cliente
    except ImportError:
        raise RuntimeError("Flow não existe neste PC") from None
    with tempfile.TemporaryDirectory() as d:
        p = cliente.gerar(prompt, Path(d) / "flow.png", formato=formato)
        if not p:
            raise RuntimeError("Flow não entregou (ou em pausa)")
        return p.read_bytes()


def gerar_com(modelo, prompt, formato="16:9"):
    """Bytes da imagem desse modelo; RuntimeError com o motivo se não gerar."""
    if modelo.startswith("flow/"):
        return _flow(prompt, formato)
    if modelo.startswith("@cf/"):
        return _cloudflare(modelo, prompt, formato)
    if modelo.startswith("pollinations/"):
        return _pollinations(modelo.split("/", 1)[1], prompt, formato)
    return _siliconflow(modelo, prompt, formato)


def gerar(prompt, formato="16:9", pose=None):
    """(bytes, modelo) do 1º modelo que gerar, pulando os que recusam a pose; (None, motivos) se nenhum."""
    motivos = []
    for m in MODELOS:
        if pose and m in RECUSA.get(pose, ()):
            continue
        try:
            return gerar_com(m, prompt, formato), m
        except Exception as e:  # noqa: BLE001  (filtro, cota, rede: tenta o próximo)
            motivos.append(f"{m.split('/')[-1]}: {str(e)[:120]}")
    return None, "; ".join(motivos) or "pose recusada por todos"
