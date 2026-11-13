#!/usr/bin/env python3
"""comercial_veo.py - 1 a cada N videos do Veo no TikTok/Instagram vai COM propaganda, montada SEGURA na hora
(decisao do dono 16/10: "sim, mas com cuidado, foi ai que deu problema"; itens VO-04/VO-05 de
D:\\veo\\docs\\PLANO_MELHORIAS_VEO.md). YouTube NUNCA: so o reuso (TikTok/Instagram) chama isto.

Por que montar na hora: os COMPLETO antigos (veo\\pos_final) tem o numero de WhatsApp na tela e nunca podem ser usados.
Aqui o comercial sai do LIMPO aprovado + montar_final (card v6: nome do produto + beneficio + "LINK NO PERFIL"; a voz
diz o beneficio e "o link esta no perfil" - conferido em 16/10 por transcricao e quadros).

Regras (config/reuso_plataformas.json -> <rede>.veo_comercial = {"ligado": true, "a_cada": 3}):
  - vez: as ultimas a_cada-1 postagens do Veo NESTA conta foram limpas -> esta e comercial (1 em 3);
  - produto: nunca o mesmo do ultimo comercial da conta;
  - SEGURANCA: 3 quadros do fim vao a um modelo de visao ("tem telefone, URL, @ ou QR code?"). Qualquer "sim" ou
    falha do gateway -> nao usa (posta o limpo). Melhor perder a propaganda do que repetir o banimento.
Uso pelos postadores: c = comercial_veo.preparar(v, "tiktok", conta) -> None ou {"arquivo", "produto"}.
"""
import base64
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import catalogo  # noqa: E402

VEO_PY = r"D:\veo\venv\Scripts\python.exe"
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
PRODUTOS = Path(r"D:\veo\beta\pos_producao\assets\produtos.json")
GATEWAY = Path(r"D:\veo\beta\secrets\gateway.json")
LOGS = {"tiktok": catalogo.TIKTOK_AUTO, "instagram": catalogo.INSTA_AUTO}
PERGUNTA = ("Esta imagem e um quadro de um video curto. Existe escrito nela algum NUMERO DE TELEFONE, endereco de site "
            "ou URL, @ de perfil de rede social, ou QR code? (O nome de um produto, a palavra WhatsApp como nome de "
            "funcao e o texto 'LINK NO PERFIL' NAO contam.) Responda SO com JSON: "
            '{"contato": "sim" ou "nao", "o_que": "<o que achou ou vazio>"}')


def _cfg(plataforma):
    return ((catalogo._ler(catalogo.REUSO, {}) or {}).get(plataforma) or {}).get("veo_comercial") or {}


def _historico(plataforma, conta):
    """Postagens do Veo desta conta, da mais antiga para a mais nova (as que tem 'tipo')."""
    regs = catalogo._ler(LOGS[plataforma], []) or []
    return [r for r in regs if r.get("account") == conta and r.get("tipo") == "veo"]


def vez(plataforma, conta):
    cfg = _cfg(plataforma)
    if not cfg.get("ligado"):
        return False
    n = max(2, int(cfg.get("a_cada", 3)))
    try:  # 24/10 (dono: "cada insta um produto"): conta de produto = 1 a cada 2 com propaganda do produto dela
        if (json.loads((Path(__file__).resolve().parent.parent / "config" / "marcas_instagram.json")
                       .read_text(encoding="utf-8"))["contas"].get(conta) or {}).get("produto"):
            n = 2
    except Exception:  # noqa: BLE001
        pass
    ultimos = _historico(plataforma, conta)[-(n - 1):]
    return len(ultimos) == n - 1 and all(r.get("formato", "limpo") != "comercial" for r in ultimos)


def _produto(stem, plataforma, conta):
    """Produto do catalogo (peso), por md5 do video+conta, nunca o do ultimo comercial desta conta."""
    cat = json.loads(PRODUTOS.read_text(encoding="utf-8"))
    # 24/10 (dono: "cada insta um produto"): conta de produto (config\marcas_instagram.json) anuncia SO o seu
    try:
        marca = (json.loads((Path(__file__).resolve().parent.parent / "config" / "marcas_instagram.json")
                            .read_text(encoding="utf-8"))["contas"].get(conta) or {})
        fixo = next((p for p in cat.get("produtos", []) if p.get("id") == marca.get("produto")), None)
        if fixo:
            return fixo
    except Exception:  # noqa: BLE001
        pass
    ultimo = next((r.get("produto") for r in reversed(_historico(plataforma, conta)) if r.get("formato") == "comercial"),
                  None)
    pool = [p for p in cat.get("produtos", []) for _ in range(int(p.get("peso", 1))) if p.get("id") != ultimo]
    if not pool:
        return None
    return pool[int(hashlib.md5(f"{stem}|{conta}".encode()).hexdigest(), 16) % len(pool)]


def _montar(limpo, saida, tema, fala, produto):
    codigo = ("import sys, json; sys.path.insert(0, r'D:\\veo\\beta'); sys.path.insert(0, r'D:\\veo\\beta\\pos_producao')\n"
              "from montar_final import montar\n"
              "a = json.loads(sys.argv[1])\n"
              "r = montar(a['limpo'], a['saida'], a['tema'], a['tema'], a['fala'], voz='auto', formato_cta='slide', "
              "com_vo3_propaganda=False, produto=a['produto'])\n"
              "print('MONTAR: ' + json.dumps(r if isinstance(r, dict) else {'ok': bool(r)}, default=str))\n")
    arg = json.dumps({"limpo": str(limpo), "saida": str(saida), "tema": tema, "fala": fala, "produto": produto})
    try:
        r = subprocess.run([VEO_PY, "-c", codigo, arg], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900, env={**__import__("os").environ, "PYTHONUTF8": "1"})
    except subprocess.TimeoutExpired:  # 19/10: escapava e derrubava a rodada inteira do TikTok depois de 10 posts
        Path(saida).unlink(missing_ok=True)
        return False, {"ok": False, "erro": "montagem passou de 900 s"}
    m = re.search(r"^MONTAR: (\{.*\})\s*$", r.stdout or "", re.M)
    res = json.loads(m.group(1)) if m else {"ok": False, "erro": (r.stderr or r.stdout or "")[-300:]}
    return bool(res.get("ok")) and Path(saida).exists(), res


def seguro(mp4):
    """(True, '') se nenhum de 3 quadros do fim tem telefone/URL/@/QR; senao (False, motivo). Falha = nao seguro."""
    try:
        gw = json.loads(GATEWAY.read_text(encoding="utf-8"))
        dur = float(subprocess.run([FFMPEG.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries",
                                    "format=duration", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True)
                    .stdout.strip() or 0)
        url = gw.get("gateway_url", "").rstrip("/") + "/v1/chat/completions"
        for f in (0.6, 0.8, 0.95):
            img = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{dur * f:.2f}", "-i", str(mp4), "-frames:v", "1",
                                  "-vf", "scale=540:-2", "-f", "image2", "-vcodec", "mjpeg", "-"], capture_output=True).stdout
            corpo = {"model": "antigravity/gemini-3-flash", "max_tokens": 80, "messages": [{"role": "user", "content": [
                {"type": "text", "text": PERGUNTA},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(img).decode()}}]}]}
            req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers={
                "Authorization": "Bearer " + gw["gateway_key"], "Content-Type": "application/json"})
            txt = json.loads(urllib.request.urlopen(req, timeout=90).read())["choices"][0]["message"]["content"]
            m = re.search(r'"contato"\s*:\s*"(\w+)"', txt)
            if not m or m.group(1).lower() != "nao":
                return False, f"quadro {int(f * 100)}%: {txt.strip()[:120]}"
        return True, ""
    except Exception as ex:  # noqa: BLE001
        return False, f"checagem falhou: {type(ex).__name__}: {str(ex)[:100]}"


def preparar(v, plataforma, conta, log=print):
    """Se for a vez desta conta e der para montar um comercial seguro: {"arquivo", "produto"}; senao None (limpo)."""
    if v.get("projeto") != "veo" or not v.get("limpo") or not vez(plataforma, conta):
        return None
    limpo = Path(v["limpo"])
    meta = catalogo._ler(limpo.with_suffix(".json"), {}) or {}
    produto = _produto(limpo.stem, plataforma, conta)
    if produto and not limpo.exists():  # 29/10: o limpo pode estar só no Drive (json 'no_drive')
        try:
            limpo = catalogo.baixar(v)
        except RuntimeError as e:
            log(f"  comercial: {str(e)[:160]}")
            return None
    if not produto:
        return None
    catalogo.CACHE.mkdir(parents=True, exist_ok=True)
    saida = catalogo.CACHE / f"comercial_{limpo.stem}__{produto['id']}.mp4"
    ok, res = _montar(limpo, saida, meta.get("tema") or "", meta.get("fala") or "", produto)
    if not ok:
        log(f"  comercial: nao montou ({str(res.get('erro') or res)[:160]}) - vai o limpo")
        return None
    bom, motivo = seguro(saida)
    if not bom:
        log(f"  comercial DESCARTADO pela checagem de contato ({motivo}) - vai o limpo")
        saida.unlink(missing_ok=True)
        return None
    log(f"  comercial: {produto['id']} (1 a cada {_cfg(plataforma).get('a_cada', 3)} nesta conta), checagem ok")
    return {"arquivo": saida, "produto": produto["id"]}
