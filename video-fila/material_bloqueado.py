# -*- coding: utf-8 -*-
"""material_bloqueado.py — o que causou bloqueio no YouTube sai de uso SOZINHO (dono 21/10).

Dono: "inteligência anti-bloqueio: identificar quando teve um bloqueio e parar de usar aquilo que causou, sem esperar
os avisos". O bloqueio que queremos é o do vídeo PROGRAMADO (aparece "Bloqueado" na lista de Shorts do Studio e não
abre — não compromete o canal); o avisos_studio acha esses e registra aqui. Material:
- fonte (canal do parceiro de onde veio o vídeo): FONTE_LIMITE bloqueios em JANELA_DIAS -> sai do rodízio do
  parceiro (parceiro_diario._escolher_fonte); 1 bloqueio já pesa (peso menor);
- trilha: causa = música (página de direitos do Studio) OU a mesma trilha em TRILHA_LIMITE vídeos bloqueados -> sai
  do sorteio (blocklist) e, se for das prioritarias/, é MOVIDA pra prioritarias/_bloqueadas/ (nada é apagado).
Estado: D:\\video-fila\\estado\\material_bloqueado.json.
"""
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

ESTADO = Path(r"D:\video-fila\estado\material_bloqueado.json")
BLOCKLIST = Path(r"D:\hipercool-materiais\_curadoria\copyright_blocklist.json")
PRIORITARIAS = Path(r"D:\hipercool-materiais\assets\trilhas\prioritarias")
JANELA_DIAS = 14
FONTE_LIMITE = 2
TRILHA_LIMITE = 2


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(p).with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def estado():
    d = _ler(ESTADO, {})
    d.setdefault("fontes", {})
    d.setdefault("trilhas", {})
    return d


def registrar(video, fonte=None, trilhas=(), causa=None):
    """Um vídeo bloqueado. causa = {"tipo": "musica"|"video"|"?", "conteudo": "..."} (página de direitos) ou None.
    Devolve a lista do que saiu de uso agora ([(tipo, nome, motivo)])."""
    d = estado()
    agora = datetime.now().isoformat(timespec="seconds")
    tipo = (causa or {}).get("tipo")  # "musica" | "video" | "ambos" | None (não deu pra ler a causa)
    # relendo o mesmo vídeo (agora com a causa): refaz a conta dele do zero
    for f in d["fontes"].values():
        f["bloqueios"] = [b for b in f["bloqueios"] if b["video"] != video]
    for x in d["trilhas"].values():
        if not x.get("fora"):
            x["videos"] = [v for v in x["videos"] if v != video]
    # fonte do parceiro só leva a culpa se a IMAGEM foi reivindicada (ou se a causa é desconhecida)
    if fonte and tipo in (None, "video", "ambos"):
        d["fontes"].setdefault(fonte, {"bloqueios": []})["bloqueios"].append(
            {"video": video, "em": agora, "causa": tipo})
    conteudos = [f"{r.get('conteudo', '')} {r.get('autor', '')}" for r in (causa or {}).get("reivindicacoes", [])
                 if any(k in str(r.get("tipo", "")).lower() for k in ("udio", "elodia", "letra", "música", "musica",
                                                                       "composi", "melody", "lyric", "music",
                                                                       "audiovisual"))]
    for t in trilhas:
        x = d["trilhas"].setdefault(t, {"videos": [], "confirmada": False})
        if tipo in ("musica", "ambos"):
            # causa conhecida: só a faixa reivindicada leva a culpa (21/10: "deep space … FREE FOR PROFIT" foi
            # reivindicada — nome "livre" não protege nada)
            if not any(_casa(t, c) for c in conteudos):
                continue
            x["confirmada"] = True
        elif tipo == "video":
            continue
        if video not in x["videos"]:
            x["videos"].append(video)
    # música reivindicada que não estava entre as trilhas conhecidas do vídeo (Short sem log, outro projeto): procura
    # pelo nome na biblioteca inteira (21/10: "Infraction Music - Halloween Night" num Short do Filme Noturno)
    if tipo in ("musica", "ambos") and conteudos:
        conhecidas = [t for t in trilhas if any(_casa(t, c) for c in conteudos)]
        if not conhecidas:
            for arq in _biblioteca():
                if any(_casa(arq.name, c) for c in conteudos):
                    x = d["trilhas"].setdefault(arq.name, {"videos": [], "confirmada": False})
                    x["confirmada"] = True
                    if video not in x["videos"]:
                        x["videos"].append(video)
    _gravar(ESTADO, d)
    return aplicar(d)


def _biblioteca():
    """Arquivos de trilha da pasta comum (top + prioritarias)."""
    raiz = PRIORITARIAS.parent
    return [f for f in list(raiz.glob("*")) + list(PRIORITARIAS.glob("*"))
            if f.is_file() and f.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg", ".opus")]


CATALOGO = Path(r"D:\hipercool-materiais\_curadoria\catalogo.json")
_nomes_catalogo = None


def _nome_catalogo(arquivo):
    """Nome/artista/título de origem que a curadoria gravou pra trilha. O arquivo muitas vezes não tem o nome da
    música: 21/10 "inaudio - Infraction- Backslider" era phonk_drift_atmospheric_infraction_LHae9zvUfug.mp3."""
    global _nomes_catalogo
    if _nomes_catalogo is None:
        _nomes_catalogo = {}
        cat = _ler(CATALOGO, [])
        for x in cat if isinstance(cat, list) else []:
            if not isinstance(x, dict) or x.get("tipo") != "trilha":
                continue
            ident = x.get("identificacao") or {}
            texto = f"{ident.get('nome', '')} {ident.get('artista', '')} {x.get('origem_titulo', '')}"
            for c in (x.get("caminho_aprovado"), x.get("arquivo_limpo")):
                if c:
                    _nomes_catalogo[Path(c).name.lower()] = texto
    return _nomes_catalogo.get(Path(arquivo).name.lower(), "")


def _casa(arquivo, conteudo):
    """O conteúdo reivindicado ("Cornfield Chase - Hans Zimmer") bate com o nome do arquivo da trilha (ou com o nome
    que a curadoria registrou pra ele)?"""
    import re
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower())  # noqa: E731
    # palavra INTEIRA e sem as genéricas: "music"/"night" dentro de "Midnight Club … Loading Music" casava com
    # "Infraction Music - Halloween Night" (21/10)
    genericas = {"music", "musica", "song", "beat", "beats", "sound", "official", "remix", "version", "copyright",
                 "free", "theme", "soundtrack", "audio", "video", "kbps", "prod", "instrumental", "original"}
    a = {w for w in norm(f"{Path(arquivo).stem} {_nome_catalogo(arquivo)}").split() if len(w) >= 4}
    c = {w for w in norm(conteudo).split() if len(w) >= 4} - genericas
    return bool(c) and len(a & c) >= min(2, len(c))


def aplicar(d=None):
    """Tira de uso as trilhas que passaram do limite (blocklist + move das prioritarias). Devolve o que tirou agora."""
    d = d or estado()
    feito = []
    bl = _ler(BLOCKLIST, {})
    ja = {(x.get("arquivo") if isinstance(x, dict) else x).lower() for x in bl.get("blocklist", [])}
    mudou = False
    for t, x in d["trilhas"].items():
        if x.get("fora"):
            continue
        if not (x.get("confirmada") or len(x["videos"]) >= TRILHA_LIMITE):
            continue
        motivo = ("música reivindicada no Studio" if x.get("confirmada")
                  else f"em {len(x['videos'])} vídeos bloqueados")
        if t.lower() not in ja:
            bl.setdefault("blocklist", []).append({"arquivo": t, "bloquear": True, "adicionado": datetime.now().strftime(
                "%Y-%m-%d"), "motivo": f"anti-bloqueio automático: {motivo} ({', '.join(x['videos'][:5])})"})
            ja.add(t.lower())
            mudou = True
        p = PRIORITARIAS / t
        if p.is_file():  # curada pelo dono, mas causou bloqueio: sai do sorteio sem apagar
            (PRIORITARIAS / "_bloqueadas").mkdir(exist_ok=True)
            shutil.move(str(p), str(PRIORITARIAS / "_bloqueadas" / t))
        x["fora"] = datetime.now().isoformat(timespec="seconds")
        x["motivo"] = motivo
        feito.append(("trilha", t, motivo))
    if mudou:
        _gravar(BLOCKLIST, bl)
    _gravar(ESTADO, d)
    return feito


def bloqueios_da_fonte(nome, dias=JANELA_DIAS):
    corte = (datetime.now() - timedelta(days=dias)).isoformat()
    return sum(1 for b in estado()["fontes"].get(nome, {}).get("bloqueios", []) if b.get("em", "") >= corte)


def fontes_fora(dias=JANELA_DIAS):
    """Nomes de fonte com FONTE_LIMITE+ bloqueios na janela — o parceiro não usa."""
    return {n for n in estado()["fontes"] if bloqueios_da_fonte(n, dias) >= FONTE_LIMITE}
