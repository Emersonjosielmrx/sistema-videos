#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""postar_tudo_hoje.py — Driver de postagem do dia.

Junta TODAS as fontes prontas e posta round-robin entre os canais ATIVOS,
respeitando a politica de bin/politica.py (config/politica.json): teto de
uploads por canal/dia, intervalo entre videos do mesmo canal, aprovacao humana
(bin/aprovar.py) e parada geral se o YouTube suspender algum canal.

Fontes:
  - VO3  : D:\\veo\\beta\\logs\\video_cache.json (persona/tema + video_path).
           Gemini roteia persona -> canal IA real e gera titulo/desc/tags pela FALA.
           Grava posted_url de volta no cache (fecha o loop de aprendizado do veo).
  - recap: D:\\hipercool-materiais\\**\\postar.json  categoria=recap  -> canais manga
  - animes: idem categoria=animes                                   -> canais manga
  - historias: idem categoria=historias  -> Gemini roteia entre canais IA

Uso:
  python postar_tudo_hoje.py --preview            # so planeja, nao posta
  python postar_tudo_hoje.py --so vo3             # so uma categoria
  python postar_tudo_hoje.py --limite-canal 2     # teto extra (abaixo do da politica)
  python postar_tudo_hoje.py                      # posta o que foi aprovado, ate a cota
"""
import argparse
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import politica  # noqa: E402

VEO_CACHE = Path(r"D:\veo\beta\logs\video_cache.json")
MATERIAIS = Path(r"D:\hipercool-materiais")
POSTADOS = MATERIAIS / "_postados"

# Canais suspensos / token morto / desativados ficam em config/canais_status.json.
# (Antes havia um set DEAD aqui que nao batia com os nomes do youtube_canais.json
# por causa de espacos no fim — o pool "IA" acabava sendo SO de canais suspensos.)
carregar_pools = politica.carregar_pools


# ─────────────────────────── metadados via Gemini ──────────────────────────
def rota_vo3(persona, tema, fala, canais_ia):
    """Gemini escolhe o canal IA certo pra persona/tema e escreve meta pela fala."""
    import gemini_llm
    canais_txt = "\n".join(f"- {c}" for c in canais_ia)
    prompt = (
        "Voce roteia um Short de IA (VO3) pro canal certo do YouTube e escreve os metadados.\n"
        f"Persona/tema do video: {persona} / {tema}\n"
        f"Fala do video (o que a pessoa diz): {fala[:400]}\n\n"
        f"Canais disponiveis (escolha o mais alinhado ao tema):\n{canais_txt}\n\n"
        "Responda SO um JSON: {\"canal\": \"<nome EXATO de um canal da lista>\", "
        "\"titulo\": \"<titulo viral PT-BR ate 90 chars, pode 1 emoji, com #shorts>\", "
        "\"descricao\": \"<2-3 linhas chamativas + 4-6 hashtags>\", "
        "\"tags\": [\"6-10 tags PT-BR\"]}"
    )
    resp = gemini_llm.generate_text(prompt, max_tokens=500)
    d = _parse_json(resp)
    canal = d.get("canal", "")
    if canal not in canais_ia:
        canal = None  # deixa o loop escolher
    tit = (d.get("titulo") or persona)[:100]
    desc = d.get("descricao") or f"{persona}\n\n#shorts #ia #viral"
    tags = d.get("tags") or ["shorts", "ia", "viral", "brasil"]
    return canal, tit, desc, tags


def _parse_json(txt):
    import re
    if not txt:
        return {}
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


# ─────────────────────────── coleta de itens ───────────────────────────────
_VEO_BASE = Path(r"D:\veo\beta")
_MATERIAIS_VEO = Path(r"D:\hipercool-materiais\veo")

def _resolver_video_vo3(vp):
    """Tenta localizar o MP4 real: path original, videos_pos, ja_feitos, materiais."""
    if not vp:
        return None
    p = Path(vp)
    if p.is_file():
        return str(p)
    stem = p.name
    for alt in (_VEO_BASE / "videos_pos" / "cron_shorts" / stem,
                _VEO_BASE / "pos_producao" / "ja_feitos" / stem,
                _MATERIAIS_VEO / "cron_shorts" / stem,
                _MATERIAIS_VEO / "pos_final" / stem):
        if alt.is_file():
            return str(alt)
    return None


def listar_vo3_pendentes():
    """Entradas do cache do veo ainda nao postadas e com MP4 existente (sem Gemini)."""
    if not VEO_CACHE.is_file():
        return []
    cache = json.loads(VEO_CACHE.read_text(encoding="utf-8"))
    pend = []
    for x in cache:
        if (x.get("metrics") or {}).get("posted_url"):
            continue
        resolved = _resolver_video_vo3(x.get("video_path"))
        if not resolved:
            continue
        x["_resolved_path"] = resolved
        pend.append(x)
    # dedup por arquivo, mantem o mais recente
    vistos, uniq = set(), []
    for x in reversed(pend):
        vp = x["video_path"]
        if vp in vistos:
            continue
        vistos.add(vp)
        uniq.append(x)
    return uniq


def coletar_vo3(canais_ia, limite=None, canal_fixo=None, skip_gemini=False):
    """Le o cache do veo, filtra nao-postados com arquivo, Gemini roteia+meta."""
    uniq = listar_vo3_pendentes()
    if not canais_ia and not canal_fixo:
        if uniq:
            print(f"[vo3] {len(uniq)} videos pendentes, mas nenhum canal IA ativo — pulando")
        return []
    # so gasta Gemini com o que ja foi aprovado por um humano
    aprov = politica.ler_json(politica.APROV_FILE, {})
    aguardando = [x for x in uniq if not politica.aprovado(x["_resolved_path"], aprov)]
    if aguardando:
        print(f"[vo3] {len(aguardando)} aguardando aprovacao (python bin/aprovar.py)")
        uniq = [x for x in uniq if x not in aguardando]
    if limite:
        uniq = uniq[:limite]
    itens = []
    if canal_fixo:
        print(f"[vo3] {len(uniq)} videos pendentes — usando canal fixo '{canal_fixo}' (SEM Gemini)")
    elif skip_gemini:
        print(f"[vo3] {len(uniq)} videos pendentes — round-robin SEM Gemini (--skip-gemini)")
    else:
        print(f"[vo3] {len(uniq)} videos pendentes — roteando com Gemini...")
    for i, x in enumerate(uniq, 1):
        persona = x.get("canal", "")
        tema = x.get("tema", "")
        fala = x.get("fala", "") or ""
        if canal_fixo:
            canal = canal_fixo
            tit = f"{persona} - {tema[:50]} #shorts"
            desc = fala[:200] + "\n\n#shorts #ia #viral"
            tags = ["shorts", "ia", "viral"]
        elif skip_gemini:
            canal = canais_ia[(i - 1) % len(canais_ia)]
            tit = f"{persona} - {tema[:50]} #shorts"
            desc = fala[:200] + "\n\n#shorts #ia #viral"
            tags = ["shorts", "ia", "viral"]
        else:
            try:
                canal, tit, desc, tags = rota_vo3(persona, tema, fala, canais_ia)
            except Exception as e:
                canal, tit, desc, tags = None, f"{persona} #shorts", "#shorts #ia #viral", ["shorts", "ia", "viral"]
                print(f"  ! rota falhou ({type(e).__name__}) — canal auto")
        itens.append({
            "categoria": "vo3", "arquivo": x["_resolved_path"],
            "canal_pref": canal, "canal_pool": canais_ia,
            "titulo": tit, "descricao": desc, "tags": tags,
            "cache_id": x.get("id"), "privacy": "public",
        })
        if i % 10 == 0:
            print(f"  ...{i}/{len(uniq)} roteados")
    return itens


def coletar_materiais(categoria, canais_pool, canais_ia=None, so_aprovados=True):
    """Le postar.json de materiais pra uma categoria."""
    import glob
    aprov = politica.ler_json(politica.APROV_FILE, {})
    aguardando = 0
    itens = []
    for pj in glob.glob(str(MATERIAIS / "**" / "postar.json"), recursive=True):
        try:
            d = json.loads(Path(pj).read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("categoria") != categoria or d.get("pronto") is False:
            continue
        arq = d.get("arquivo", "")
        full = Path(pj).parent / arq
        if not arq or not full.is_file():
            continue
        if so_aprovados and not politica.aprovado(full, aprov):
            aguardando += 1
            continue
        # canais fixados no postar.json: so os que continuam ativos
        canais_item = politica.filtrar_ativos(d.get("canais")) or None
        # capa propria (capa IA do recap de anime, 16/10): "thumb" relativo a pasta; ate 2 MB (limite do YouTube)
        thumb = Path(pj).parent / d["thumb"] if d.get("thumb") else None
        if thumb and not (thumb.is_file() and thumb.stat().st_size < 2_000_000):
            thumb = None
        itens.append({
            "thumb": str(thumb) if thumb else None,
            "categoria": categoria, "arquivo": str(full),
            "canal_pref": (canais_item[0] if canais_item else None),
            "canal_pool": canais_item or canais_pool,
            "titulo": d.get("titulo") or full.stem,
            "descricao": d.get("descricao") or "",
            "tags": d.get("tags") or [],
            "cache_id": None,
            "privacy": d.get("privacy", "public"),
            "postar_json": pj,
        })
    if aguardando:
        print(f"[{categoria}] {aguardando} aguardando aprovacao (python bin/aprovar.py)")
    return itens


# ─────────────────────────── postagem ──────────────────────────────────────
def postar(canal_nome, item, privacy):
    return politica.postar_youtube(canal_nome, item["arquivo"], item["titulo"],
                                   item["descricao"], item["tags"], privacy=privacy,
                                   thumbnail=item.get("thumb"), tipo=item.get("categoria"))


def gravar_posted_url(cache_id, url):
    if not cache_id or not url:
        return
    try:
        cache = json.loads(VEO_CACHE.read_text(encoding="utf-8"))
        for x in cache:
            if x.get("id") == cache_id:
                x.setdefault("metrics", {})["posted_url"] = url
                break
        politica.gravar_json(VEO_CACHE, cache, indent=None)
    except Exception as e:
        print(f"  ! falha gravando posted_url: {e}")


def gravar_posted_url_materiais(item, url):
    """Grava posted_url no postar.json de origem (recap/animes/historias) pra o
    coletor central (medir_metricas.py) fechar o loop de aprendizado."""
    pj = item.get("postar_json")
    if not pj or not url:
        return
    try:
        p = Path(pj)
        doc = json.loads(p.read_text(encoding="utf-8"))
        doc["posted_url"] = url
        doc["posted_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        politica.gravar_json(p, doc)
    except Exception as e:
        print(f"  ! falha gravando posted_url (materiais): {e}")


def mover_postado(item):
    dst_dir = POSTADOS / item["categoria"]
    dst_dir.mkdir(parents=True, exist_ok=True)
    src = Path(item["arquivo"])
    dst = dst_dir / src.name
    if dst.exists():
        dst = dst_dir / f"{src.stem}_{int(time.time())}{src.suffix}"
    try:
        shutil.move(str(src), str(dst))
        # leva junto o postar.json se houver
        pj = item.get("postar_json")
        if pj and Path(pj).is_file():
            shutil.move(pj, str(dst_dir / f"{dst.stem}.postar.json"))
    except Exception as e:
        print(f"  ! falha movendo: {e}")


def escolher_canal(item, bloqueados):
    """Canal preferido se livre; senao primeiro do pool que nao esta bloqueado."""
    pref = item.get("canal_pref")
    if pref and pref not in bloqueados:
        return pref
    for c in item["canal_pool"]:
        if c not in bloqueados:
            return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--so", choices=["vo3", "recap", "animes", "historias"], default=None)
    ap.add_argument("--limite-canal", type=int, default=None,
                    help="teto extra por canal nesta rodada (a politica ja limita por dia)")
    ap.add_argument("--vo3-max", type=int, default=None,
                    help="limita quantos VO3 rotear (economiza Gemini no teste)")
    ap.add_argument("--canal-fixo", type=str, default=None,
                    help="usa um canal fixo pra VO3 (pula roteamento Gemini)")
    ap.add_argument("--skip-gemini", action="store_true",
                    help="pula Gemini e distribui VO3 round-robin entre TODOS os canais IA")
    args = ap.parse_args()

    canais_ia, canais_manga = carregar_pools()
    print(f"Pools: {len(canais_ia)} canais IA | {len(canais_manga)} canais manga/manhwa\n")

    # 16/10 (dono; AB-01 de D:\veo\docs\PLANO_MELHORIAS_VEO.md): o caminho de verdade hoje e so o ANIME
    # (anime_publish -> aqui). Recap do hipercool tem o postador dele, historias e Veo vao pela rede do manhwa-react;
    # rodar essas categorias aqui seria postar em duplicidade, publico e em rodizio. O Veo antigo (cache vo3, que pode
    # pegar o COMPLETO com o slide de WhatsApp) so roda com config\VEO_ANTIGO_LIGADO.json.
    cats = [args.so] if args.so else ["animes"]
    if "vo3" in cats and not (Path(__file__).resolve().parent.parent / "config" / "VEO_ANTIGO_LIGADO.json").exists():
        print("vo3: caminho antigo do Veo DESARMADO (16/10) - o Veo vai ao ar limpo pela rede. "
              "Para religar de proposito: criar config\\VEO_ANTIGO_LIGADO.json")
        cats = [c for c in cats if c != "vo3"]
    itens = []
    if "recap" in cats:
        itens += coletar_materiais("recap", canais_manga)
    if "animes" in cats:
        itens += coletar_materiais("animes", canais_manga)
    if "historias" in cats:
        itens += coletar_materiais("historias", canais_ia)
    if "vo3" in cats:
        itens += coletar_vo3(canais_ia, limite=args.vo3_max, canal_fixo=args.canal_fixo,
                             skip_gemini=args.skip_gemini)

    from collections import Counter
    print("\n=== INVENTARIO ===")
    for cat, n in Counter(it["categoria"] for it in itens).most_common():
        print(f"  {cat:10} {n}")
    print(f"  TOTAL      {len(itens)}")

    if args.preview:
        print("\n>>> PREVIEW — nada postado. Amostra de roteamento VO3:")
        for it in [x for x in itens if x["categoria"] == "vo3"][:12]:
            print(f"  [{it['canal_pref'] or 'AUTO'}] {it['titulo'][:60]}")
        return

    parada = politica.parada_ativa()
    if parada:
        print(f"\n*** PARADA GERAL desde {parada['desde']}: {parada['motivo']}")
        print("*** Nada sera postado. Revise e rode: python bin/politica.py --retomar")
        return

    # round-robin por categoria, ate a cota da politica (config/politica.json)
    bloqueados = set()
    postados = Counter()
    por_canal = Counter()
    verificar = []  # timeouts: podem ter subido — NAO repetir hoje (evita duplicata)
    parar = False
    restantes = list(itens)
    rodada = 0
    while restantes and not parar:
        rodada += 1
        avancou = False
        ainda = []
        for i, it in enumerate(restantes):
            if parar:
                ainda.extend(restantes[i:])
                break
            canal = escolher_canal(it, bloqueados)
            if not canal:
                ainda.append(it)  # sem canal livre agora
                continue
            if args.limite_canal and por_canal[canal] >= args.limite_canal:
                bloqueados.add(canal)
                ainda.append(it)
                continue
            print(f"[r{rodada}] {it['categoria']:8} -> [{canal.strip()}] {it['titulo'][:50]}", end=" ")
            status, info = postar(canal, it, it["privacy"])
            if status == "ok":
                print(f"OK {info or ''}")
                postados[it["categoria"]] += 1
                por_canal[canal] += 1
                avancou = True
                gravar_posted_url(it.get("cache_id"), info)
                gravar_posted_url_materiais(it, info)
                mover_postado(it)
            elif status in ("limite", "cota"):
                print("LIMITE DO YOUTUBE" if status == "limite" else "COTA DO DIA (politica)")
                bloqueados.add(canal)
                ainda.append(it)  # tenta noutro canal
            elif status == "morto":
                print(f"CANAL BLOQUEADO/TOKEN MORTO ({info})")
                bloqueados.add(canal)
                ainda.append(it)
            elif status in ("suspenso", "parado"):
                print(f"PARADA GERAL: {info}")
                parar = True
                ainda.append(it)
            elif status == "timeout":
                print("TIMEOUT (pode ter subido — confira no Studio antes de repostar)")
                verificar.append(it)
            elif status == "nao_aprovado":
                print("NAO APROVADO — pulando")
            else:
                print(f"ERRO: {info}")
                # nao rebloqueia o canal por 1 erro de arquivo; descarta o item
        restantes = ainda
        if parar:
            print("\n*** YouTube suspendeu um canal (ou ha parada geral) — TUDO PARADO. ***")
            print("*** Veja config/PARADO.json e rode: python bin/politica.py ***")
            break
        # se todos os canais possiveis estao bloqueados, para
        pools_ativos = set()
        for it in restantes:
            pools_ativos.update(it["canal_pool"])
        if not (pools_ativos - bloqueados):
            print("\n*** Todos os canais elegiveis bateram no limite/morte. ***")
            break
        if not avancou:
            print("\n*** Nenhum avanco nesta rodada — encerrando. ***")
            break

    print(f"\n{'='*60}\nRESUMO\n{'='*60}")
    for cat, n in postados.most_common():
        print(f"  {cat:10} {n} postados")
    print(f"  TOTAL POSTADOS: {sum(postados.values())}")
    print(f"  Restantes (pra amanha): {len(restantes)}")
    if verificar:
        print(f"  TIMEOUT — conferir no YouTube Studio se subiram ({len(verificar)}):")
        for it in verificar:
            print(f"    {it['arquivo']}")
    print("\n  Por canal:")
    for c, n in por_canal.most_common():
        blk = " [LIMITE]" if c in bloqueados else ""
        print(f"    {c[:40]:40} {n}{blk}")


if __name__ == "__main__":
    main()
