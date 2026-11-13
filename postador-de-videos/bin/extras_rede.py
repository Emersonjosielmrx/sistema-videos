#!/usr/bin/env python3
"""extras_rede.py - acabamento no YouTube Studio dos videos da REDE do manhwa-react (Onda 2.3 / DS-05, 16/10).

Copiado do padrao do hipercool (postar_hipercool._extras_de / rodar_extras / _extra_pendente), pelo navegador
(youtube_studio_extras.py: mesmo Chrome/perfil/trava do web poster, sem Data API):
  - "video relacionado" nos Shorts de REACT ja publicos -> o completo (react deitado) publico mais recente do MESMO
    canal: quem ve o Short cai no video longo do dono. Veo e historias ficam de fora (outro assunto).
  - o comentario a rede ja faz (rede_comentarios).
  - teste A/B de capa (18/10) no completo ja publico que tem "thumbs_ab" no registro (capas A/B/C do mr/capa.py).
  - tela final "1 video + 1 playlist" (18/10) no completo ja publico que tem "playlist" no registro.
  - rascunhos presos (18/10): so LISTA no log, 1x por dia por canal (apagar continua manual, --apagar-mesmo).
Exige canal verificado: sem isso o Studio devolve "pendente" e tenta de novo depois (como no hipercool).

Roda na tarefa ManhwaReact-Rede, DEPOIS da rede (mesmo Chrome, sem disputa), no maximo --max videos por rodada.
Estado: config/extras_rede.json.   Uso: python bin/extras_rede.py [--max 2] [--ensaio]
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
PUBLICADOS = Path(r"D:\hipercool-materiais\_postados\react\publicados.json")
ESTADO = BIN.parent / "config" / "extras_rede.json"
RASCUNHOS = BIN.parent / "config" / "extras_rede_rascunhos.json"
LOG = BIN.parent / "logs" / "extras_rede.log"
INTERVALO_H = 3      # pendente/aviso: tenta de novo depois disso
MAX_AVISOS = 5       # aviso repetido: desiste
JANELA_DIAS = 30     # Short mais velho que isso nao ganha extra


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _dt(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.astimezone()
    except (TypeError, ValueError):
        return None


def _pendente(p, agora):
    """Igual ao postar_hipercool._extra_pendente."""
    st = p.get("status") or ""
    if st in ("ok", "ja") or (st.startswith("aviso") and p.get("tentativas", 0) >= MAX_AVISOS):
        return False
    if "comentário postado" in st:  # 16/10: postado; fixar so com o canal verificado (dono) - nao reabre o Chrome por isso
        return False
    if st.startswith("bloqueado"):
        m = re.search(r"até (\d{4}-\d{2}-\d{2})", st)
        return bool(m) and agora.date().isoformat() >= m.group(1)
    em = p.get("em")
    return not em or (agora - datetime.fromisoformat(em)).total_seconds() >= INTERVALO_H * 3600


def no_ar(vid):
    """O video esta publico de verdade? oEmbed: 200 publico, 401/403 privado, 404 removido (16/10: o completo
    wKiGkUQ6bBc do InventoReact foi removido por ser longo demais e seguia como alvo)."""
    import urllib.error
    import urllib.request
    try:
        urllib.request.urlopen(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json",
                               timeout=20)
        return True
    except urllib.error.HTTPError:
        return False
    except Exception:  # noqa: BLE001  (sem rede: nao decide agora)
        return None


def planejar(reg, estado, agora_utc):
    """Acrescenta ao estado o 'relacionado' de cada Short de react publico cujo canal tem completo publico."""
    publico = lambda v: (_dt(v.get("publish_at")) or _dt(v.get("postado_em")) or agora_utc) <= agora_utc
    completos = {}
    for v in reg.values():
        if isinstance(v, dict) and v.get("fonte") == "completo" and v.get("video_id") and publico(v) \
                and no_ar(v["video_id"]):
            s = v.get("canal_slug")
            if s not in completos or (_dt(v.get("publish_at")) or agora_utc) > (_dt(completos[s].get("publish_at")) or agora_utc):
                completos[s] = v
    for v in reg.values():
        if not isinstance(v, dict) or v.get("fonte") not in ("react", None) or not v.get("video_id"):
            continue  # None = registro antigo (antes do campo fonte), todos react
        quando = _dt(v.get("publish_at")) or _dt(v.get("postado_em"))
        comp = completos.get(v.get("canal_slug"))
        if not comp or not quando or quando > agora_utc or (agora_utc - quando).days > JANELA_DIAS:
            continue
        e = estado.setdefault(v["video_id"], {"canal": v.get("canal_id") or v.get("canal"), "titulo": v.get("titulo", ""),
                                             "publish_at": v.get("publish_at"), "extras": {}})
        rel = e["extras"].setdefault("relacionado", {"video": comp["video_id"], "titulo": comp.get("titulo", "")})
        if rel.get("video") != comp["video_id"] and rel.get("status") not in ("ok", "ja"):
            rel.update(video=comp["video_id"], titulo=comp.get("titulo", ""))  # o alvo antigo saiu do ar
    # comentario que a API nao pode fazer (403 de permissao: mr/publish.py marca "navegador") -> pelo Studio, FIXADO
    for v in reg.values():
        if not isinstance(v, dict) or not v.get("video_id") or not v.get("comentario_texto"):
            continue
        c = str(v.get("comentario") or "")
        if c != "navegador" and not (c.startswith("erro: 403") and "insufficie" in c.lower()):
            continue
        quando = _dt(v.get("publish_at")) or _dt(v.get("postado_em"))
        if not quando or quando > agora_utc:
            continue  # comentar_fixar so em video ja publico
        e = estado.setdefault(v["video_id"], {"canal": v.get("canal_id") or v.get("canal"), "titulo": v.get("titulo", ""),
                                             "publish_at": v.get("publish_at"), "extras": {}})
        e["extras"].setdefault("comentario", {"texto": v["comentario_texto"]})
    for v in reg.values():
        if not isinstance(v, dict) or v.get("fonte") != "completo" or not v.get("video_id") \
                or len([c for c in v.get("thumbs_ab") or [] if Path(c).is_file()]) < 2 or not publico(v):
            continue
        e = estado.setdefault(v["video_id"], {"canal": v.get("canal_id") or v.get("canal"), "titulo": v.get("titulo", ""),
                                             "publish_at": v.get("publish_at"), "extras": {}})
        e["extras"].setdefault("teste_ab", {"capas": [c for c in v["thumbs_ab"] if Path(c).is_file()]})
    # tela final "1 video + 1 playlist" (18/10) no completo ja publico que subiu numa playlist (mr/rede.py PLAYLIST_COMPLETOS)
    for v in reg.values():
        if isinstance(v, dict) and v.get("fonte") == "completo" and v.get("video_id") and v.get("playlist") and publico(v):
            e = estado.setdefault(v["video_id"], {"canal": v.get("canal_id") or v.get("canal"), "titulo": v.get("titulo", ""),
                                                 "publish_at": v.get("publish_at"), "extras": {}})
            e["extras"].setdefault("tela_final", {"playlist": v["playlist"]})
    # curtir: DESLIGADO aqui em 23/10 (dona: "só em UMA conta, a minha pessoal, no Acer quando ele já abre o vídeo pra
    # eu ver"). Isto curtia com o próprio canal em TODOS os canais da rede. O like agora é do telão do Acer
    # (D:\video-fila\vitrine.py curtir_no_telao), com a conta pessoal da dona, 1 vez por vídeo.
    for e in estado.values():
        c = e.get("extras", {}).get("curtir")
        if c is not None and c.get("status") not in ("ok", "ja"):
            e["extras"].pop("curtir")
    # sem alvo no ar: tira o relacionado ainda nao feito (nao abre o Chrome a toa)
    for vid, e in estado.items():
        rel = e.get("extras", {}).get("relacionado")
        if rel and rel.get("status") not in ("ok", "ja") and not any(
                c["video_id"] == rel.get("video") for c in completos.values()):
            e["extras"].pop("relacionado")
    return estado


def canais_bloqueados(estado):
    """{(canal, acao)} em que o Studio ja disse 'bloqueado' (ex.: relacionado sem a verificacao por telefone) - nao
    tenta essa ACAO nos outros videos do canal: um aviso basta, o resto e o dono resolver. Por acao: o canal bloqueado
    para 'relacionado' continua recebendo o 'comentario'."""
    return {(e.get("canal"), k) for e in estado.values() for k, p in e.get("extras", {}).items()
            if str(p.get("status") or "").startswith("bloqueado")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=2)
    ap.add_argument("--ensaio", action="store_true", help="so mostra o que faria")
    a = ap.parse_args()
    agora, agora_utc = datetime.now(), datetime.now(timezone.utc)
    reg = json.loads(PUBLICADOS.read_text(encoding="utf-8")) if PUBLICADOS.exists() else {}
    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    planejar(reg, estado, agora_utc)
    bloq = canais_bloqueados(estado)
    if bloq:
        log(f"extras da rede: bloqueado no Studio (dono resolve): {', '.join(sorted(f'{c} {k}' for c, k in bloq))}")

    def fazer_de(e):
        return {k: p for k, p in e.get("extras", {}).items() if (e.get("canal"), k) not in bloq and _pendente(p, agora)}
    fila = sorted(((vid, e) for vid, e in estado.items() if fazer_de(e)),
                  key=lambda x: x[1].get("publish_at") or "", reverse=True)
    log(f"extras da rede: {len(fila)} video(s) com acabamento pendente; nesta rodada ate {a.max}")
    if a.ensaio:
        for vid, e in fila[:a.max]:
            log(f"  [ensaio] {vid} ({e['canal']}): {', '.join(fazer_de(e))} | {e['titulo'][:50]}")
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
        return
    import youtube_studio_extras as yx
    for vid, e in fila[:a.max]:
        fazer = fazer_de(e)
        kw = {}
        if "relacionado" in fazer:
            kw.update(relacionado=fazer["relacionado"]["video"], titulo_relacionado=fazer["relacionado"]["titulo"])
        if "comentario" in fazer:
            kw["comentario"] = fazer["comentario"]["texto"]
        if "teste_ab" in fazer:
            kw["ab"] = fazer["teste_ab"]["capas"]
        if "tela_final" in fazer:
            kw["tela_final"] = fazer["tela_final"]["playlist"]
        if "curtir" in fazer:
            kw["curtir"] = True
        res = yx.rodar(e["canal"], vid, **kw)
        for k, p in fazer.items():
            p["status"] = res.get(k) or "aviso: " + str(res.get("erro") or "sem resposta")[:150]
            p["em"], p["tentativas"] = agora.isoformat(timespec="seconds"), p.get("tentativas", 0) + 1
        log(f"  {vid} ({e['canal']}): " + ", ".join(f"{k}={p['status']}" for k, p in fazer.items()))
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    # rascunhos presos (uploads que travaram no meio): so LISTA (sem --apagar-mesmo), 1x por dia por canal tocado
    vistos = json.loads(RASCUNHOS.read_text(encoding="utf-8")) if RASCUNHOS.exists() else {}
    hoje = agora.date().isoformat()
    for canal_id in sorted({e["canal"] for _, e in fila[:a.max] if e.get("canal")} - {c for c, d in vistos.items() if d == hoje}):
        st = str(yx.rodar(canal_id, limpar_rascunhos=True).get("rascunhos") or "")
        vistos[canal_id] = hoje
        if st and not st.startswith("ensaio: 0 "):
            log(f"  rascunhos presos {canal_id}: {st} (apagar: youtube_studio_extras.py --canal {canal_id} --limpar-rascunhos --apagar-mesmo)")
    RASCUNHOS.write_text(json.dumps(vistos, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
