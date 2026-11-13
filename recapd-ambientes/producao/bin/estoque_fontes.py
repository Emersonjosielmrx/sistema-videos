"""estoque_fontes.py — fontes de parceiro BAIXADAS ANTES, pra produção nunca parar (dono, 22/10 17:10:
"o sistema não pode parar por nada, só no botão").

O gargalo que parava a produção era o YouTube barrar o IP de casa no DOWNLOAD da fonte (em 22/10 nenhum Short
ficou pronto das 06:55 às 09:51). Este módulo mantém um estoque de fontes já baixadas em
`workspace\\anime\\_estoque\\<id>\\` (source.mp4 + meta.json):

  - `repor()` roda quando o IP está LIVRE (fim de cada rodada de produção + CLI pra madrugada): lista os Shorts
    novos de cada canal-fonte (consulta pequena, que já sai pelo proxy) e baixa os melhores que AINDA não foram
    feitos/postados/estocados, até o alvo.
  - `consumir_para(url, out_dir)` é chamado pelo anime_fetch.download_video ANTES de tocar na rede: fonte no
    estoque = produção segue MESMO com o yt-dlp em pausa (zero download).
  - Entrada com mais de VALIDADE_DIAS sai sozinha (fonte velha demais pra valer o disco).

    python bin/estoque_fontes.py                     # status
    python bin/estoque_fontes.py repor [--novos 3] [--alvo 8]
"""
import json
import logging
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))

PASTA = Path(r"D:\recapd-ambientes\producao\workspace\anime\_estoque")
FONTES_POSTADAS = Path(r"D:\recapd-ambientes\producao\workspace\anime\_fontes_postadas.json")
PARCEIRO_CFG = Path(r"D:\recapd-ambientes\producao\config\parceiro.json")
ALVO = 8            # fontes prontas no estoque (≈ meio dia de produção)
VALIDADE_DIAS = 7
DISCO_MIN_GB = 8.5  # não enche o estoque com o disco apertado (23/10, dono: era 10 e o D: vive em 9-10 GB -> estoque nunca repôs; 8 fontes ~0,3 GB, a produção para em 8)
_RX_ID = re.compile(r"(?:youtu\.be/|shorts/|v=)([\w-]{11})")


def _vid(url):
    m = _RX_ID.search(str(url or ""))
    return m.group(1) if m else None


def _entradas():
    out = {}
    if not PASTA.exists():
        return out
    for d in PASTA.iterdir():
        if d.is_dir() and any(d.glob("source.*")):
            out[d.name] = d
    return out


def consumir_para(url, out_dir):
    """Se a fonte da url está no estoque, MOVE o arquivo pra out_dir/source.<ext> e devolve o Path (senão None)."""
    vid = _vid(url)
    d = _entradas().get(vid or "")
    if not d:
        return None
    src = next(d.glob("source.*"))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    destino = out_dir / src.name
    shutil.move(str(src), str(destino))
    shutil.rmtree(d, ignore_errors=True)
    return destino


def _ja_feitos():
    """Ids que NÃO devem ser estocados: feitos/tentados do anime_auto + fontes já postadas + o próprio estoque."""
    ids = set(_entradas())
    try:
        import anime_auto
        ids |= anime_auto._ja_feitos("short")
        ids |= anime_auto._ja_feitos("short_attempted")
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[estoque] _ja_feitos do anime_auto indisponível ({e})")
    try:
        for por_canal in json.loads(FONTES_POSTADAS.read_text(encoding="utf-8")).values():
            ids |= set(por_canal)
    except (OSError, ValueError, AttributeError):
        pass
    return ids


def _limpar_velhos():
    agora = time.time()
    for d in list(_entradas().values()):
        try:
            if agora - d.stat().st_mtime > VALIDADE_DIAS * 86400:
                shutil.rmtree(d, ignore_errors=True)
                logging.info(f"[estoque] {d.name} venceu ({VALIDADE_DIAS} dias) — fora")
        except OSError:
            pass


def repor(max_novos=2, alvo=ALVO, emergencia=False):
    """Baixa até `max_novos` fontes novas (respeitando `alvo` no total). Devolve [ids baixados].
    Normal: só com o IP livre. `emergencia` (22/10, dono: "se é IP, usa proxy"): com o IP pausado E o estoque
    baixo, baixa pelo proxy rotativo — o teto de banda diário fica no anime_fetch (PROXY_MB_DIA)."""
    import ytdlp_vez
    _limpar_velhos()
    if ytdlp_vez.pausado():
        if not (emergencia and len(_entradas()) < max(3, alvo // 2)):
            logging.info("[estoque] yt-dlp em pausa — reponho na próxima")
            return []
        logging.info("[estoque] IP pausado + estoque baixo: EMERGÊNCIA pelo proxy (teto de banda do anime_fetch)")
    if shutil.disk_usage("D:\\").free / 1e9 < DISCO_MIN_GB:
        logging.info(f"[estoque] disco < {DISCO_MIN_GB} GB — não reponho agora")
        return []
    atual = _entradas()
    if len(atual) >= alvo:
        return []
    try:
        fontes = [f for f in json.loads(PARCEIRO_CFG.read_text(encoding="utf-8")).get("fontes", []) if f.get("url")]
    except (OSError, ValueError):
        fontes = []
    if not fontes:
        logging.warning("[estoque] sem fontes no config/parceiro.json")
        return []
    import anime_discover
    import anime_fetch
    fora = _ja_feitos()
    baixados = []
    # a fonte menos representada no estoque repõe primeiro (variedade pro rodízio de nichos)
    por_fonte = {}
    for d in atual.values():
        try:
            por_fonte[json.loads((d / "meta.json").read_text(encoding="utf-8")).get("fonte", "?")] = \
                por_fonte.get(json.loads((d / "meta.json").read_text(encoding="utf-8")).get("fonte", "?"), 0) + 1
        except (OSError, ValueError):
            continue
    for f in sorted(fontes, key=lambda x: por_fonte.get(x.get("nome", "?"), 0)):
        if len(baixados) >= max_novos or len(_entradas()) >= alvo:
            break
        try:
            cands = anime_discover.discover_canal(f["url"])  # consulta pequena: já sai pelo proxy (ytdlp_vez)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[estoque] discover de {f.get('nome')} falhou ({e})")
            continue
        for c in cands:
            if c.get("id") in fora:
                continue
            if ytdlp_vez.pausado() and not emergencia:
                logging.info("[estoque] IP pausou no meio — paro de repor")
                return baixados
            tmp = PASTA / f"_baixando_{c['id']}"
            shutil.rmtree(tmp, ignore_errors=True)
            arq = anime_fetch.download_video(c.get("url") or f"https://www.youtube.com/watch?v={c['id']}", tmp)
            if not arq:
                break  # bloqueio/falha: não insiste nesta rodada
            destino = PASTA / c["id"]
            shutil.rmtree(destino, ignore_errors=True)
            tmp.rename(destino)
            (destino / "meta.json").write_text(json.dumps(
                {**{k: c.get(k) for k in ("id", "title", "url", "duration", "views") if k in c},
                 "fonte": f.get("nome"), "tipo": f.get("tipo"),
                 "baixado_em": datetime.now().isoformat(timespec="seconds")},
                ensure_ascii=False, indent=1), encoding="utf-8")
            baixados.append(c["id"])
            logging.info(f"[estoque] + {c['id']} ({f.get('nome')}): {str(c.get('title'))[:60]}")
            break  # 1 por fonte por rodada — variedade
    if baixados:
        logging.info(f"[estoque] {len(_entradas())}/{alvo} fontes prontas")
    return baixados


def main():
    logging.basicConfig(level=logging.INFO, format="[estoque %(asctime)s] %(message)s", datefmt="%d/%m %H:%M")
    args = sys.argv[1:]
    if "repor" in args:
        novos = int(args[args.index("--novos") + 1]) if "--novos" in args else 2
        alvo = int(args[args.index("--alvo") + 1]) if "--alvo" in args else ALVO
        print("baixados:", repor(max_novos=novos, alvo=alvo, emergencia="--emergencia" in args))
    else:
        ent = _entradas()
        print(f"{len(ent)} fonte(s) no estoque (alvo {ALVO}):")
        for vid, d in sorted(ent.items()):
            try:
                m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                m = {}
            mb = sum(x.stat().st_size for x in d.glob("source.*")) / 1e6
            print(f"  {vid}  {mb:5.0f} MB  [{m.get('fonte', '?')}] {str(m.get('title'))[:60]}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
