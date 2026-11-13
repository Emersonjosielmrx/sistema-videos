"""reserva_veo.py — Veo limpo como reserva do TikTok/Instagram: conta sem video proprio no dia nao para.

Dono 18/10: "1 a 3 por dia como no YouTube; podem reaproveitar os VO3 do Drive; nunca deveriam ter parado".
completar() da Veo a cada conta que ficou abaixo da cota do dia, uma de cada vez (todas chegam a 1 antes de alguma ir a 2):
  1o Veo do catalogo que ja saiu no YouTube e sobra em outra conta (mais do que ela posta hoje);
  2o limpo aprovado (bin/limpar_veo.py) que ainda nao saiu em lugar nenhum, do mais antigo para o mais novo, deixando os
     'deixar_pro_youtube' mais novos para a rede do YouTube (que pega os mais novos primeiro).
usado() tira do YouTube o limpo que saiu primeiro no TikTok/Instagram (o que passou por eles nunca sobe no YouTube).
Fala repetida (o Veo gerou o mesmo roteiro mais de uma vez) nao sai duas vezes na mesma rede.
Config: "reserva_veo" em config/reuso_plataformas.json.
"""
import json
import re
from datetime import datetime
from pathlib import Path

import catalogo
import politica

POSTADOS = {"tiktok": catalogo.TIKTOK_AUTO, "instagram": catalogo.INSTA_AUTO}


def config():
    return (catalogo._ler(catalogo.REUSO, {}) or {}).get("reserva_veo") or {}


def _base(nome):
    return re.sub(r"_COMPLETO$", "", Path(str(nome or "")).stem)


def _fala_do_limpo(mp4):
    meta = catalogo._ler(Path(mp4).with_suffix(".json"), {}) or {}
    return " ".join((meta.get("fala") or "").lower().split())


def _fala(v):
    return _fala_do_limpo(v["limpo"]) if v.get("limpo") else ""


def _item(mp4):
    return {"caminho": str(mp4), "nome": mp4.name, "bytes": mp4.stat().st_size if mp4.exists() else 0,
            "projeto": "veo", "origem": "", "no_pc": mp4.exists(), "drive": None, "tipo": "final", "postagens": [],
            "limpo": str(mp4), "reserva": "limpo"}


def _no_pc(v, log=print):
    """29/10 (dona: disco cheio, "mova e deixe fácil de aproveitarmos"): o limpo que foi para o Drive (json com
    'no_drive') volta para veo/limpos só quando é escolhido. Devolve False se não deu para baixar (pula para o próximo)."""
    if v.get("reserva") != "limpo" or Path(v["limpo"]).exists():
        return True
    origem = (catalogo._ler(Path(v["limpo"]).with_suffix(".json"), {}) or {}).get("no_drive")
    if not origem:
        return False
    import subprocess
    subprocess.run([r"D:\tools\rclone.exe", "copyto", origem, v["limpo"], "--retries", "3"], capture_output=True,
                   timeout=900, creationflags=0x08000000)
    ok = Path(v["limpo"]).exists()
    log(f"Reserva Veo: {'baixei do Drive' if ok else 'NÃO baixou do Drive'} {Path(v['limpo']).name}")
    return ok


def nunca_postados(plataforma, cat, deixar):
    """Limpos que podem sair nesta rede sem ter passado pelo YouTube: primeiro os que ja sairam na outra rede de reuso
    (ja tirados do YouTube), depois os aprovados livres; do mais antigo para o mais novo."""
    no_catalogo = {_base(v["nome"]) for v in cat["videos"] if v["projeto"] == "veo" and v["postagens"]}
    na_rede = {_base(p.get("file")) for p in catalogo._ler(POSTADOS[plataforma], []) or []}
    aprov = politica.ler_json(politica.APROV_FILE, {})
    reusados, livres, com_marca = [], [], []
    for jp in catalogo.LIMPOS.glob("*.json"):
        meta, mp4 = catalogo._ler(jp, None), jp.with_suffix(".mp4")
        if not isinstance(meta, dict) or meta.get("posted_url") or not (mp4.exists() or meta.get("no_drive")) \
                or jp.stem in no_catalogo or jp.stem in na_rede:
            continue
        marca = bool(meta.get("revisar")) and catalogo.so_marca_ia(meta)
        if meta.get("revisar") and not marca:
            continue
        redes = {r.get("plataforma") for r in meta.get("reuso") or []}
        if plataforma in redes:
            continue
        if redes:
            reusados.append((meta.get("criado") or "", mp4))
        elif marca:  # dono 19/10: so TikTok/Instagram, depois dos sem marca (nunca serviu ao YouTube: fora do deixar)
            com_marca.append((meta.get("criado") or "", mp4))
        elif politica.status_aprovacao(mp4, aprov) == "aprovado":
            livres.append((meta.get("criado") or "", mp4))
    reusados.sort()
    livres.sort()
    com_marca.sort()
    livres = livres[:max(0, len(livres) - int(deixar))]
    return [_item(mp4) for _, mp4 in reusados + livres + com_marca]


def completar(plataforma, plano, disponiveis, cat, log=print):
    """plano: conta -> (resta, candidatos da propria conta), so contas que podem postar hoje; completa as listas no
    lugar. Veo da propria conta alem do que ela posta hoje vira sobra para as outras. Devolve {conta: quantos ganhou}."""
    cfg = config()
    if not cfg.get("ligado"):
        return {}
    sobra = []
    for resta, cand in plano.values():
        cabeca, cauda = cand[:resta], cand[resta:]
        sobra += [v for v in cauda if v["projeto"] == "veo"]
        cand[:] = cabeca + [v for v in cauda if v["projeto"] != "veo"]  # o resto fica de reserva se um falhar
    sobra += [v for v in disponiveis if v["projeto"] == "veo" and v["conta_reuso"] not in plano]

    ja = {_fala_do_limpo(catalogo.LIMPOS / f"{_base(p.get('file'))}.mp4")
          for p in catalogo._ler(POSTADOS[plataforma], []) or []}
    ja |= {_fala(v) for _, cand in plano.values() for v in cand}
    ja.discard("")

    def fila():
        yield from sobra
        yield from nunca_postados(plataforma, cat, cfg.get("deixar_pro_youtube", 10))  # so calcula se a sobra acabar

    def sem_repetir(itens):
        for v in itens:
            f = _fala(v)
            if f and f in ja:
                continue
            ja.add(f)
            yield v

    fonte = sem_repetir(fila())
    ganhou = {}
    sem_veo = {c for c, r in ((catalogo._ler(catalogo.REUSO, {}).get(plataforma) or {}).get("contas") or {}).items()
               if (r or {}).get("sem_veo")}
    # 01/11: a reserva acaba em 2-9 contas por rodada e ia sempre para as primeiras do json — 22 contas do TikTok
    # ficaram 6 dias sem post. Agora vai primeiro para quem está há mais tempo sem postar (rodízio)
    ultimo = {}
    for p in catalogo._ler(POSTADOS[plataforma], []) or []:
        if isinstance(p, dict):
            c, t = p.get("account") or p.get("conta"), str(p.get("timestamp") or p.get("em") or "")
            if c and t > ultimo.get(c, ""):
                ultimo[c] = t
    ordem = sorted(plano.items(), key=lambda kv: ultimo.get(kv[0], ""))
    for rodada in range(max((r for r, _ in plano.values()), default=0)):
        for conta, (resta, cand) in ordem:
            if conta in sem_veo or rodada >= resta or len(cand) > rodada:
                continue
            v = next(fonte, None)
            while v is not None and not _no_pc(v, log):
                v = next(fonte, None)
            if v is None:
                break
            cand.append(dict(v, conta_reuso=conta, reserva=v.get("reserva") or "sobra"))
            ganhou[conta] = ganhou.get(conta, 0) + 1
    if ganhou:
        log("Reserva Veo: " + ", ".join(f"{c} +{n}" for c, n in ganhou.items()))
    return ganhou


def usado(v, plataforma, conta):
    """Depois de postado: limpo que nunca tinha saido vai para 'reuso' no json e e rejeitado para o YouTube."""
    if v.get("reserva") != "limpo":
        return
    mp4 = Path(v["limpo"])
    jp = mp4.with_suffix(".json")
    meta = catalogo._ler(jp, {}) or {}
    meta.setdefault("reuso", []).append({"plataforma": plataforma, "conta": conta,
                                         "quando": datetime.now().isoformat(timespec="seconds")})
    jp.write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    politica.marcar_aprovacao(mp4, "rejeitado", f"saiu primeiro no {plataforma} ({conta}): nunca sobe no YouTube "
                                                "(reserva_veo, dono 18/10)")
