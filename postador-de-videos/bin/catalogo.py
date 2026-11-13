"""Catalogo central dos videos de todos os projetos: onde cada um esta (PC e/ou Google Drive) e onde ja foi postado.

Remontado a cada uso a partir dos registros que os postadores ja gravam (sincronizar), sem mudar nenhum postador.
Reuso: disponiveis("tiktok"|"instagram") = ja saiu em outra rede e ainda nao nesta, com a conta de destino de
config/reuso_plataformas.json; baixar() traz do Drive o que ja nao esta no PC. O que passou pelo YouTube nao volta ao YouTube.
O backup que tira do PC o que ja foi postado e D:\\manhwa-react\\scripts\\backup_drive.py (le este catalogo).

Uso: python catalogo.py [resumo | disponiveis tiktok|instagram | baixar <caminho original>]
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import politica  # noqa: E402

CONFIG = BIN.parent / "config"
LOGS = BIN.parent / "logs"
CATALOGO = CONFIG / "catalogo_videos.json"
# nome que se repete em toda pasta de item (parceiro, rede): bloquear por ele travava os 182 Shorts do parceiro (20/10)
NOMES_GENERICOS = {"video.mp4", "final.mp4", "short.mp4", "saida.mp4", "output.mp4"}
REUSO = CONFIG / "reuso_plataformas.json"
CACHE = BIN.parent / "cache_reuso"  # copia baixada do Drive so para postar; liberar() apaga
RCLONE = r"D:\tools\rclone.exe"
RCLONE_REMOTO = "manhwa-drive:"
MANIFESTO = Path(r"D:\manhwa-react\logs\backup_drive.jsonl")  # o que o backup tirou do PC e onde ficou no Drive
LIMPOS = Path(r"D:\hipercool-materiais\veo\limpos")  # Veo sem marca/propaganda (bin/limpar_veo.py)
POSTADOS = Path(r"D:\hipercool-materiais\_postados")
TIKTOK_AUTO = LOGS / "tiktok_auto_posted.json"
TIKTOK_CDP = Path(r"D:\hipercool-producao\logs\tiktok_posted.json")
INSTA_MULTI = LOGS / "multiplataforma_log.json"
INSTA_AUTO = LOGS / "instagram_auto_posted.json"
LOGS_PROPRIOS = [(Path(r"D:\historias-em-frames\logs\videos_postados.json"), "historias-em-frames"),
                 (Path(r"D:\recapd-ambientes\producao\logs\videos_postados.json"), "recapd")]
CDP_CONTAS = {"cdp_9222": "canalalucinaai", "cdp_9251": "3dfabricadeautomacoesia", "cdp_9261": "inovaremanhwaverseita",
              "cdp_9271": "jornalcomia"}
VIDEO = {".mp4", ".mov", ".mkv", ".webm"}

# (pasta no PC, projeto, pasta no Drive dentro de videos-backup/, aceita casar postagem so pelo nome do arquivo).
# Filas de postagem (shorts/cortes/grandes do manhwa-react, topo do veo\pos_final, animes recap) ficam de fora.
PASTAS = [
    (r"D:\hipercool-materiais\_postados\react", "manhwa-react", "manhwa-react/postados/react", True),
    (r"D:\hipercool-materiais\_postados\historias", "historias-em-frames", "manhwa-react/postados/historias", True),
    (r"D:\manhwa-react\work\rede_marca", "manhwa-react", "manhwa-react/rede_marca", True),
    (r"D:\hipercool-materiais\_postados\vo3", "veo", "veo/postados_vo3", True),
    (r"D:\hipercool-materiais\_postados\recaps", "recapd", "recapd/postados_recaps", True),
    (r"D:\hipercool-materiais\_usados", "veo", "veo/usados", True),
    (r"D:\hipercool-materiais\veo\ja_agendados", "veo", "veo/ja_agendados", True),
    (r"D:\hipercool-materiais\veo\pos_final\completo", "veo", "veo/pos_final_completo", True),
    (r"D:\hipercool-materiais\veo\veo_videos_iniciais", "veo", "veo/brutos_veo_videos_iniciais", False),
    (r"D:\veo\beta\videos", "veo", "veo/beta_videos", False),
    (r"D:\hipercool-materiais\videos", "hipercool", "hipercool/videos", False),
    (r"D:\hipercool-videos\workspace\shorts", "hipercool", "hipercool/shorts", False),  # = junção p/ hipercool-materiais\shorts_hipercool
    (r"D:\historias-em-frames\workspace\videos", "historias-em-frames", "historias-em-frames/videos", False),
    (r"D:\ms-energy\videos\_postados", "ms-energy", "ms-energy/postados", True),
]
# Catálogo POR FICHA (18/10, unificação): pasta de itens com postar.json (1 vídeo final por ficha, campo "arquivo"). Só o
# vídeo da ficha entra (a pasta tem intermediários); a postagem do YouTube vem da própria ficha (posted_url,
# agendado_para, canal_postado). Assim os Shorts de parceiro entram no reuso TikTok/Instagram e no backup.
FICHAS = [(r"D:\hipercool-materiais\animes recap\shorts", "parceiro", "parceiro/shorts", False),
          # 02/11: Shorts de comentários do Comédia Noturna (D:\videos-comentarios) no reuso TikTok/Insta
          (r"D:\hipercool-materiais\videos-comentarios", "comentarios", "comentarios/fichas", False)]
MS_ENERGY_LOG = Path(r"D:\ms-energy\videos\postagem_log.json")  # postador proprio do ms-energy (insta/fb/stories)
BRUTOS = Path(r"D:\hipercool-materiais\veo\veo_videos_iniciais")  # geracoes brutas do Veo: reaproveitaveis em videos novos
SUSPENSOS = Path(r"D:\hipercool-materiais\veo\pos_final\completo")  # VO3 antigo: muitos passaram pelos canais suspensos


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001  (registro ausente ou quebrado = vazio)
        return padrao


def _iso(t):
    return t.isoformat(timespec="seconds") if t else None


def pasta_de(caminho):
    """(pasta, projeto, pasta no Drive, por_nome) da pasta conhecida que contem o caminho, ou None."""
    s = str(caminho).casefold()
    for p in PASTAS + FICHAS:
        if s.startswith(p[0].casefold() + "\\"):
            return p
    return None


def _fichas():
    """[(postar.json, vídeo da ficha, dados)] das pastas de FICHAS."""
    out = []
    for raiz, *_ in FICHAS:
        for pj in Path(raiz).glob("*/postar.json") if os.path.isdir(raiz) else []:
            d = _ler(pj, {})
            f = pj.parent / (d.get("arquivo") or "video.mp4")
            if f.is_file():
                out.append((pj, f, d))
    return out


def _varrer():
    arqs = {}
    for raiz, *_ in PASTAS:
        if os.path.isdir(raiz):
            for f in Path(raiz).rglob("*"):
                if f.suffix.lower() in VIDEO and f.is_file():
                    arqs[str(f).casefold()] = f
    for _pj, f, _d in _fichas():
        arqs[str(f).casefold()] = f
    return arqs


def _no_drive():
    """caminho original (casefold) -> registro do manifesto, so do que saiu mesmo do PC."""
    out = {}
    if MANIFESTO.exists():
        for linha in MANIFESTO.read_text(encoding="utf-8").splitlines():
            r = json.loads(linha)
            if r.get("drive") and Path(r["local"]).suffix.lower() in VIDEO and not Path(r["local"]).exists():
                out[r["local"].casefold()] = r
    return out


def _postagens(caminhos):
    """[(plataforma, conta, id, quando, caminho|None, nome)] de todos os registros conhecidos."""
    out = []
    aprov_nome = defaultdict(set)  # aprovacoes.json guarda o caminho completo do que foi aprovado para subir
    for d in politica.ler_json(politica.APROV_FILE, {}).values():
        if d.get("arquivo"):
            aprov_nome[Path(d["arquivo"]).name].add(d["arquivo"])
    for r in politica._ler_ledger():
        if r.get("video_id") and r.get("arquivo"):
            cam = aprov_nome.get(r["arquivo"], set())
            # ledger com caminho (desde 18/10): liga direto ao arquivo, mesmo quando o nome é só "video.mp4"
            out.append(("youtube", r.get("canal"), r["video_id"], politica._dt(r.get("publish_at")) or politica._dt(r.get("ts")),
                        r.get("caminho") or (next(iter(cam)) if len(cam) == 1 else None), r["arquivo"]))
    for _pj, f, d in _fichas():  # ficha postada (parceiro): a postagem está nela
        if d.get("posted_url"):
            out.append(("youtube", d.get("canal_postado"), str(d["posted_url"]).rsplit("/", 1)[-1],
                        politica._dt(d.get("agendado_para")) or politica._dt(d.get("posted_at")), str(f), f.name))
    for pj in POSTADOS.glob("react/*/*.postar.json"):  # a rede arquiva cada video postado com o registro do upload
        p = _ler(pj, {}).get("postado") or {}
        if p.get("video_id"):
            stem = pj.name[:-len(".postar.json")]
            out.append(("youtube", p.get("canal"), p["video_id"], politica._dt(p.get("publish_at")) or politica._dt(p.get("postado_em")),
                        str(pj.with_name(stem + ".mp4")), stem + ".mp4"))
    for pj in POSTADOS.glob("historias/*/*/postar.json"):
        p = _ler(pj, {}).get("postado") or {}
        if p.get("video_id"):
            pasta = str(pj.parent).casefold() + "\\"
            for c in caminhos:
                if c.startswith(pasta):
                    out.append(("youtube", p.get("canal"), p["video_id"], politica._dt(p.get("publish_at")) or politica._dt(p.get("postado_em")),
                                c, Path(c).name))
    for e in _ler(TIKTOK_AUTO, []):
        out.append(("tiktok", e.get("account"), None, politica._dt(e.get("timestamp")), e.get("path"), e.get("file")))
    for e in _ler(TIKTOK_CDP, []):
        out.append(("tiktok", CDP_CONTAS.get(e.get("account"), e.get("account")), None, politica._dt(e.get("timestamp")), None, e.get("file")))
    for stem, e in _ler(INSTA_MULTI, {}).items():
        if e.get("ig"):
            out.append(("instagram", e.get("ig_conta"), None, politica._dt(e["ig"]), None, stem + ".mp4"))
        if e.get("tk"):
            out.append(("tiktok", None, None, politica._dt(e["tk"]), None, stem + ".mp4"))
    for e in _ler(INSTA_AUTO, []):
        out.append(("instagram", e.get("account"), e.get("media_id"), politica._dt(e.get("timestamp")), e.get("path"), e.get("file")))
    for stem, e in _ler(MS_ENERGY_LOG, {}).items():
        for k, plat in (("insta", "instagram"), ("fb", "facebook"), ("stories", "stories")):
            if e.get(k):
                try:
                    quando = politica._dt(e[k])
                except ValueError:  # o log as vezes so diz "ok": postado, sem data
                    quando = None
                out.append((plat, "ms-energy", None, quando, None, stem + ".mp4"))
    for log, conta in LOGS_PROPRIOS:  # postadores proprios gravam so o caminho
        quando = datetime.fromtimestamp(log.stat().st_mtime).astimezone() if log.exists() else None
        for p in _ler(log, []):
            out.append(("youtube", conta, None, quando, p, Path(p).name))
    pasta = str(SUSPENSOS).casefold() + "\\"
    for c in caminhos:
        if c.startswith(pasta):
            out.append(("youtube", "canais suspensos (VO3 antigo)", None, None, c, Path(c).name))
    return out


def sincronizar(salvar=True):
    arqs, drive = _varrer(), _no_drive()
    todos = arqs.keys() | drive.keys()
    por_nome = defaultdict(list)  # so pastas de arquivo ja postado: nas filas o nome nao basta
    for k in todos:
        p = pasta_de(k)
        if p and p[3]:
            por_nome[Path(k).name.casefold()].append(k)
    videos = {}

    def video(k):
        if k not in videos:
            f, r = arqs.get(k), drive.get(k)
            if f and not f.exists():  # 05/11 16:38: apagado entre a listagem e aqui -> rodada inteira quebrava
                f = None
                if not r:
                    videos[k] = None
                    return None
            cam = str(f) if f else r["local"]
            p = pasta_de(cam)
            projeto = p[1] if p else r["drive"].split("videos-backup/")[-1].split("/")[0]  # ex.: rejeitado saido da fila
            partes = Path(cam).relative_to(p[0]).parts if p else ()
            videos[k] = {"caminho": cam, "nome": Path(cam).name, "bytes": f.stat().st_size if f else r["bytes"],
                         "projeto": projeto, "origem": partes[0] if len(partes) > 1 else "",  # react: canal de origem
                         "no_pc": bool(f), "drive": r["drive"] if r else None,
                         "tipo": "bruto" if BRUTOS in Path(cam).parents else "copia" if "__" in Path(cam).stem else "final",
                         "postagens": []}
        return videos[k]

    so_nome = defaultdict(set)  # postagem que nao deu para ligar a um arquivo: o nome fica bloqueado nessa rede
    for plat, conta, vid, quando, cam, nome in _postagens(todos):
        if cam and str(cam).startswith(RCLONE_REMOTO):  # video so do Drive (outro PC): vem do _registro (_etapas)
            continue
        alvos =[str(cam).casefold()] if cam and str(cam).casefold() in todos else []
        if not alvos and nome and len(por_nome.get(nome.casefold(), [])) == 1:
            alvos = list(por_nome[nome.casefold()])
        if nome and "__" in Path(nome).stem:  # copia com o @ do canal (rede): a postagem vale para o original
            orig = (Path(nome).stem.split("__")[0] + Path(nome).suffix).casefold()
            if len(por_nome.get(orig, [])) == 1:
                alvos += por_nome[orig]
        if not alvos and nome and nome.casefold() not in NOMES_GENERICOS:
            so_nome[plat].add(nome.casefold())
        for k in alvos:
            p = {"plataforma": plat, "conta": conta, "id": vid, "quando": _iso(quando)}
            v = video(k)
            if v and p not in v["postagens"]:
                v["postagens"].append(p)
    for k in todos:  # tudo que esta no Drive e os brutos do Veo entram mesmo sem postagem
        if k in drive or BRUTOS in Path(k).parents:
            video(k)
    videos = {k: v for k, v in videos.items() if v}
    _etapas(videos)
    cat ={"atualizado": _iso(politica.agora()), "videos": sorted(videos.values(), key=lambda v: v["caminho"]),
           "so_nome": {p: sorted(s) for p, s in so_nome.items()}}
    if salvar:
        # 07/11 05:08: TikTok, Instagram e backup gravam o catálogo ao mesmo tempo com o MESMO .tmp -> WinError 32 e a
        # RODADA INTEIRA do Instagram quebrava. .tmp por processo + tenta de novo; se ainda travado, segue com o da
        # memória (o próximo grava).
        tmp = CATALOGO.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
        for tentativa in range(6):
            try:
                os.replace(tmp, CATALOGO)
                break
            except PermissionError:
                if tentativa == 5:
                    tmp.unlink(missing_ok=True)
                    break
                import time
                time.sleep(2)
    return cat


def _etapas(videos):
    """Junta o Drive organizado por etapas (bin/etapas.py): video numa pasta de etapa que nenhum registro deste PC conhece
    (veio do outro PC) vira item so do Drive, e as postagens anotadas por todos os PCs entram nos videos."""
    import etapas
    try:
        no_drive, regs = etapas.listar(), etapas.ler_registros()
    except Exception as e:  # noqa: BLE001  (sem Drive: fica so o que este PC sabe)
        print(f"catalogo: etapas do Drive fora ({str(e)[:150]})", file=sys.stderr)
        return
    conhecidos = {v["drive"].casefold() for v in videos.values() if v["drive"]}
    fora = 0
    for f in no_drive:
        if f["drive"].casefold() in conhecidos:
            continue
        pt = etapas.partes(f["drive"])
        if not pt:  # 21/10 12:40: arquivo fora do formato das etapas no Drive derrubava o catálogo e o backup inteiro
            # 10/11: eram ~16 mil linhas/dia no log do TikTok (anime/1_youtube_pendente e cortes_longo, que têm caminho
            # próprio: postar_longos) — agora 1 linha com o total; CATALOGO_FORA_DETALHE=1 volta a listar
            fora += 1
            if os.environ.get("CATALOGO_FORA_DETALHE") == "1":
                print(f"catalogo: fora do formato das etapas, ignorado: {f['drive']}", file=sys.stderr)
            continue
        proj, et, origem, resto = pt
        videos[f["drive"].casefold()] = {
            "caminho": f["drive"], "nome": resto.rsplit("/", 1)[-1], "bytes": f["bytes"], "projeto": proj,
            "origem": "" if origem == "_" else origem, "no_pc": False, "drive": f["drive"], "tipo": "final",
            "postagens": [{"plataforma": etapas.rede_da_etapa(et), "conta": None, "id": None, "quando": None}]}
    if fora and os.environ.get("CATALOGO_FORA_DETALHE") != "1":
        print(f"catalogo: {fora} arquivo(s) fora do formato das etapas ignorados (longos/cortes têm caminho próprio)",
              file=sys.stderr)
    por_chave ={etapas.chave(v["drive"]): v for v in videos.values() if v["drive"] and etapas.chave(v["drive"])}
    for r in regs:  # chave (projeto, origem, resto) nao muda quando o video troca de etapa
        v = por_chave.get(etapas.chave(r.get("drive")))
        if not v or not r.get("plataforma"):
            continue
        p = {"plataforma": r["plataforma"], "conta": r.get("conta"), "id": r.get("id"), "quando": r.get("quando")}
        igual = next((x for x in v["postagens"] if x["plataforma"] == p["plataforma"] and x["conta"] in (None, p["conta"])), None)
        if not igual:
            v["postagens"].append(p)
        elif igual["conta"] is None:
            igual.update(p)


def _conta(v, regras):
    """1a conta cujo tema (comeco do nome do arquivo), canal de origem ou canal do YouTube onde saiu ('postados_em')
    bate; senao a 1a que aceita o projeto."""
    for conta, r in regras.items():
        if any(v["nome"].startswith(t) for t in r.get("temas", [])) or (v["origem"] and v["origem"] in r.get("canais", [])):
            return conta
        if any(p["plataforma"] == "youtube" and p["conta"] in r.get("postados_em", []) for p in v["postagens"]):
            return conta
        # 'parceiro_de' (18/10, dono liberou parceiro no TikTok/Insta): só os Shorts de PARCEIRO que saíram nesse canal
        # do YouTube — o react/Veo do mesmo canal não vai junto
        if v["projeto"] == "parceiro" and any(p["plataforma"] == "youtube" and p["conta"] in r.get("parceiro_de", [])
                                              for p in v["postagens"]):
            return conta
    # 29/10 (Fable; dona: "nenhum canal pode ficar sem postar"): o 'projetos' é a reserva de várias contas; antes a
    # PRIMEIRA conta da lista levava todos os vídeos do projeto e as outras ficavam "vazias" (fabricadeautomacoes0).
    # Agora o vídeo vai, de forma fixa (md5 do nome), para uma das contas que aceitam o projeto — espalha o estoque.
    reserva = [conta for conta, r in regras.items() if v["projeto"] in r.get("projetos", [])]
    if reserva:
        return reserva[int(hashlib.md5(v["nome"].encode("utf-8")).hexdigest(), 16) % len(reserva)]
    return None


def disponiveis(plataforma, cat=None):
    """Videos finais ja postados em outra rede e ainda nao nesta, com a conta de destino; os postados mais recentes primeiro."""
    cat = cat or sincronizar()
    cfg = _ler(REUSO, {}).get(plataforma) or {}
    bloq = (set(cat["so_nome"].get(plataforma, [])) - NOMES_GENERICOS) | \
        {k.casefold() for k in _ler(CONFIG / "reuso_pulados.json", {}).get(plataforma, {})}
    out = []
    # historias-em-frames guarda 2 versoes da mesma historia na pasta (v1_FINAL e v1_FINAL_ULTIMO): 1 por pasta
    historia = lambda v: str(Path(v["caminho"]).parent).casefold() if v["projeto"] == "historias-em-frames" else None  # noqa: E731
    pastas = {historia(v) for v in cat["videos"] if historia(v) and any(p["plataforma"] == plataforma for p in v["postagens"])}
    contas_cfg = cfg.get("contas", {})

    def ja_na_rede(v):
        """Já saiu nesta rede. Exceção (dona 24/10): conta com "repostar_de" reposta o que saiu SÓ nessas contas
        (ex.: msenergysolar.pa reposta a msenergycap)."""
        aqui = [p for p in v["postagens"] if p["plataforma"] == plataforma]
        if not aqui:
            return False
        destino = _conta(v, contas_cfg)
        de = set((contas_cfg.get(destino) or {}).get("repostar_de") or [])
        return not de or any(p["conta"] not in de for p in aqui) or \
            any(p["plataforma"] == plataforma and p["conta"] == destino for p in v["postagens"])

    for v in cat["videos"]:
        if (v["tipo"] != "final" or not v["postagens"] or not (v["no_pc"] or v["drive"]) or v["bytes"] > cfg.get("bytes_max", 200e6)
                or v["nome"].casefold() in bloq or v["caminho"].casefold() in bloq
                or ja_na_rede(v) or historia(v) in pastas - {None}):
            continue
        if historia(v):
            pastas.add(historia(v))
        conta = _conta(v, cfg.get("contas", {}))
        if not conta:
            continue
        # 23/10 (dona: "os veo têm um processo diferente de colocar propaganda"): o COMPLETO tem o slide com o WhatsApp
        # fixo; nunca sai como está, mesmo com veo_so_limpo desligado — o comercial do reuso é montado do LIMPO
        # (comercial_veo.py). Vale também pra COMPLETO que apareça com outro projeto depois da junção das pastas.
        completo = re.search(r"_COMPLETO$", Path(v["nome"]).stem) or "pos_final_completo" in v["caminho"].replace("\\", "/")
        if (cfg.get("veo_so_limpo") and v["projeto"] == "veo") or completo:
            limpo = versao_limpa(v)  # o COMPLETO tem o slide de propaganda/WhatsApp: so sai a versao limpa
            if not limpo:
                continue
            out.append(dict(v, conta_reuso=conta, limpo=str(limpo)))
        else:
            out.append(dict(v, conta_reuso=conta))
    # primeiro o que esta neste PC, depois o deste PC que ja foi pro Drive, por ultimo o que so o outro PC postou (dono,
    # 16/10); dentro de cada um o mais recente primeiro; empate (ex.: VO3 antigo sem data) em ordem embaralhada fixa para
    # nao sair um tema em sequencia
    out.sort(key=lambda v: (v["no_pc"], v["caminho"] != v["drive"], max(p["quando"] or "" for p in v["postagens"]),
                            hashlib.md5(v["nome"].encode()).hexdigest()), reverse=True)
    return out


def pular(plataforma, v, motivo):
    """Nao oferecer mais este video nesta rede (ex.: longo demais)."""
    p = CONFIG / "reuso_pulados.json"
    d = _ler(p, {})
    d.setdefault(plataforma, {})[v["caminho"]] = motivo
    # 22/10 (P05): troca atômica — truncado aqui o reuso ofereceria de novo o que já foi pulado
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def versao_limpa(v):
    """Veo COMPLETO -> a versao limpa de mesmo nome em veo/limpos (tema_AAAAMMDD_HHMMSS[_COMPLETO].mp4), so se o
    limpar_veo.py a aprovou (json sem 'revisar'). None se nao houver."""
    base = re.sub(r"_COMPLETO$", "", Path(v["nome"]).stem)
    mp4 = LIMPOS / f"{base}.mp4"
    meta = _ler(mp4.with_suffix(".json"), None)
    # 29/10: limpo que foi para o Drive (json com 'no_drive') continua valendo; o baixar() traz só o escolhido
    return mp4 if meta and (not meta.get("revisar") or so_marca_ia(meta)) and (mp4.exists() or meta.get("no_drive")) \
        else None


def so_marca_ia(meta):
    """Dono 19/10: Veo barrado SO pela marca d'agua Grok/Veo/Sora no canto pode sair no TikTok/Instagram (nunca no
    YouTube), se o resto da checagem do limpar_veo passou: corte da propaganda achado, tela cheia, decodifica, sem logo
    do TikTok. Marca do TikTok, nao conferida ou de outra ferramenta continua barrada."""
    from limpar_veo import LIMIAR_TIKTOK
    marca = str(meta.get("marca_ia") or "")
    return (str(meta.get("revisar") or "").startswith("marca d'agua ")
            and re.fullmatch(r"(?i)(grok|veo|sora)( (grok|veo|sora))*", marca.strip()) is not None
            and meta.get("corte_detectado") is True and meta.get("layout") == "cru" and meta.get("decodifica") is True
            and float(meta.get("nota_tiktok") or 0) < LIMIAR_TIKTOK and not meta.get("posted_url"))


# Legenda do reuso (item AB-04 de D:\veo\docs\PLANO_MELHORIAS_VEO.md, 16/10): antes TikTok sorteava 8 frases
# "#viral #fyp" e o Instagram punha "<tema> 🤯 #viral" - hashtag generica e o padrao de spam que derrubou os canais.
LEGENDA_GENERICA = {"video", "vídeo", "final", "short", "shorts", "output", "saida", "saída", "render", "clip"}
HASH_RUIM = re.compile(r"\s*#(fyp|foryou\w*|viral\w*|paravoce|pravoce|xyzbca|trending|shorts|reels|explore)\b", re.I)
PUBLICADOS_REDE = Path(r"D:\hipercool-materiais\_postados\react\publicados.json")


def legenda_reuso(v):
    """Legenda do video no TikTok/Instagram: Veo -> a FALA do limpo + "feito com IA"; react/historias -> o titulo que o
    agente da rede escreveu para o YouTube (publicados.json, pelo id); sem nada -> o tema do nome. Sem #fyp/#viral."""
    import ast
    texto, ia = "", v.get("projeto") in ("veo", "historias-em-frames")
    if v.get("limpo"):
        meta = _ler(Path(v["limpo"]).with_suffix(".json"), {}) or {}
        texto = (meta.get("fala") or "").strip()
    if not texto:
        ps = v.get("postagens") or []
        if isinstance(ps, str):
            try:
                ps = ast.literal_eval(ps)
            except (ValueError, SyntaxError):
                ps = []
        ids = {p.get("id") for p in ps if p.get("plataforma") == "youtube" and p.get("id")}
        if ids:
            reg = _ler(PUBLICADOS_REDE, {}) or {}
            texto = next((r.get("titulo") or "" for r in reg.values() if isinstance(r, dict) and r.get("video_id") in ids), "")
    if not texto and v.get("caminho"):  # 28/10: Shorts de parceiro = pasta/video.mp4 com o título ao lado
        pasta = Path(v["caminho"]).parent
        for nome in ("metadata.json", "postar.json"):
            meta = _ler(pasta / nome, {}) or {}
            if isinstance(meta, dict) and (meta.get("titulo") or "").strip():
                tags = " ".join(dict.fromkeys(re.findall(r"#\w+", meta.get("descricao") or "")))
                texto = f"{meta['titulo'].strip()} {tags}".strip()
                break
    if not texto:
        texto = re.sub(r"_(\d{8}_\d{6}|\d{4}(_\d{2}){5}).*$", "", Path(v["nome"]).stem).replace("_", " ").strip().capitalize()
    texto = HASH_RUIM.sub("", texto).strip()
    # 28/10 (dono: "isso não pode acontecer nunca"): nome genérico de arquivo não é legenda -> "" e o postador pula
    miolo = re.sub(r"#\w+", "", texto).strip()  # tamanho em letras: tailandês/japonês não têm espaço entre palavras
    if len(miolo) < 12 or miolo.lower() in LEGENDA_GENERICA:
        return ""
    return texto + ("\n\nVídeo feito com IA." if ia else "")


def baixar(v):
    """Caminho local do video: a versao limpa (veo_so_limpo); o proprio, se ainda esta no PC; senao copia do Drive em
    cache_reuso/ (conferida pelo tamanho)."""
    if v.get("limpo"):
        limpo = Path(v["limpo"])
        drive = (_ler(limpo.with_suffix(".json"), {}) or {}).get("no_drive")
        if not limpo.exists() and drive:  # 29/10 (disco cheio): o limpo foi para o Drive; volta só o que vai sair
            r = subprocess.run([RCLONE, "copyto", drive, str(limpo), "--retries", "3"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=900)
            if not limpo.exists():
                raise RuntimeError(f"nao baixou do Drive {drive}: {(r.stderr or r.stdout).strip()[-300:]}")
        return limpo
    if v["no_pc"] and Path(v["caminho"]).exists():
        return Path(v["caminho"])
    CACHE.mkdir(parents=True, exist_ok=True)
    dst = CACHE / f"{hashlib.md5(v['caminho'].casefold().encode()).hexdigest()[:8]}_{v['nome']}"
    r = subprocess.run([RCLONE, "copyto", v["drive"], str(dst), "--retries", "2", "--timeout", "45s", "--contimeout", "20s"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if r.returncode or not dst.exists() or dst.stat().st_size != v["bytes"]:
        dst.unlink(missing_ok=True)
        raise RuntimeError(f"nao baixou do Drive {v['drive']}: {(r.stderr or r.stdout).strip()[-300:]}")
    return dst


def liberar(caminho):
    """Apaga a copia baixada para postar (nunca o original)."""
    p = Path(caminho)
    if CACHE in p.parents:
        try:
            p.unlink(missing_ok=True)
        except PermissionError:  # 06/11 14:45: arquivo ainda aberto (envio em outra máquina) derrubava a RODADA inteira
            pass  # fica no cache_reuso; a próxima liberar/limpeza apaga


def resumo(cat):
    por = defaultdict(lambda: Counter())
    for v in cat["videos"]:
        c = por[v["projeto"]]
        c["videos"] += 1
        c["GB no PC"] += v["bytes"] / 1e9 if v["no_pc"] else 0
        c["GB no Drive"] += v["bytes"] / 1e9 if v["drive"] else 0
        for plat in {p["plataforma"] for p in v["postagens"]}:
            c[plat] += 1
    print(f"catalogo {cat['atualizado']}: {len(cat['videos'])} video(s)")
    for proj, c in sorted(por.items()):
        print(f"  {proj:20} {c['videos']:5} videos | PC {c['GB no PC']:6.2f} GB | Drive {c['GB no Drive']:6.2f} GB | "
              f"youtube {c['youtube']} tiktok {c['tiktok']} instagram {c['instagram']}")
    for plat in ("tiktok", "instagram"):
        d = Counter(v["conta_reuso"] for v in disponiveis(plat, cat))
        print(f"  disponivel para {plat}: {sum(d.values())} -> " + ", ".join(f"{k} {n}" for k, n in d.most_common()))


def main():
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "resumo"
    cat = sincronizar()
    if cmd == "resumo":
        resumo(cat)
    elif cmd == "disponiveis":
        for v in disponiveis(sys.argv[2], cat)[:40]:
            print(f"{v['conta_reuso']:26} {'PC   ' if v['no_pc'] else 'Drive'} {v['bytes'] / 1e6:6.1f} MB  {v['caminho']}")
    elif cmd == "baixar":
        v = next(v for v in cat["videos"] if v["caminho"].casefold() == sys.argv[2].casefold())
        print(baixar(v))


if __name__ == "__main__":
    main()
