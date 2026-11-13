# -*- coding: utf-8 -*-
"""fila.py — produção automática do hipercool. Produção e postagem são processos SEPARADOS, cada um com
seu liga/desliga: a produção nunca espera postagem e a postagem nunca espera render.

  python bin/fila.py ciclo              # 1 rodada de PRODUÇÃO (tarefa HipercoolFila, a cada 20 min)
  python bin/fila.py postagem           # 1 rodada de POSTAGEM (tarefa HipercoolPostagem, a cada 20 min)
  python bin/fila.py postar             # posta agora os pendentes em PORTUGUÊS (botão manual)
  python bin/fila.py idiomas            # renderiza agora todos os pendentes nas OUTRAS LÍNGUAS
  python bin/fila.py status
  python bin/fila.py ligar | desligar                    # produção
  python bin/fila.py ligar-postagem | desligar-postagem  # postagem

Regras: 1 vídeo completo novo por dia no canal pt (o resto da cota vai pra Shorts); renderiza no máximo
`adiantado` capítulos à frente do que já foi postado; capítulo com mais de `max_censura` do tempo censurado
não é postado avulso (fica "compilado"); canais das línguas: 1 subida por vez no pico do país
(`postagem_idiomas`); erro/limite -> pausa dinâmica (limitador) em vez de insistir.
"""
import copy
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "bin"))
from hp_common import log  # noqa: E402
import limitador  # noqa: E402

CONFIG = PROJECT / "config" / "fila.json"
DESLIGADA = PROJECT / "config" / "FILA_DESLIGADA.json"
POSTAGEM_DESLIGADA = PROJECT / "config" / "POSTAGEM_DESLIGADA.json"
ESTADO = PROJECT / "workspace" / "fila_estado.json"
LOCK = PROJECT / "workspace" / "fila.lock"
LOCK_POSTAGEM = PROJECT / "workspace" / "postagem.lock"
POSTADOR_BIN = Path(r"D:\postador-de-videos\bin")
PANELS = Path(r"D:\hipercool-materiais\panels")
VIDEOS = PROJECT / "workspace" / "videos"
PY = str(PROJECT / "venv" / "Scripts" / "python.exe")
ENV = dict(os.environ, PYTHONUTF8="1", GEMINI_TTS_PROXY_ENABLED="0",
           PATH=r"D:\hipercool-materiais\bin" + os.pathsep + os.environ.get("PATH", ""))
TAREFA = "HipercoolFila"
TAREFA_POSTAGEM = "HipercoolPostagem"


def cfg():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _env_render():
    """cache_clipes (config) liga/desliga o cache do movimento 2.5D (bin/fx_parallax.py)."""
    return dict(ENV, HIPER_CACHE_2P5D="1" if cfg().get("cache_clipes", True) else "0")


_lido = {}  # o estado como estava no disco quando este processo leu (base da mescla em gravar_estado)


def _ler_disco():
    if not ESTADO.exists():
        return {}
    for tentativa in range(40):  # o outro processo pode estar trocando o arquivo neste instante
        try:
            return json.loads(ESTADO.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            if tentativa == 39:
                raise
            time.sleep(0.25)


def ler_estado():
    global _lido
    e = _ler_disco()
    _lido = copy.deepcopy(e)
    return e


def _mesclar(base, meu, disco):
    for k in set(base) | set(meu):
        if k not in meu:
            disco.pop(k, None)
        elif isinstance(meu[k], dict) and isinstance(base.get(k), dict) and isinstance(disco.get(k), dict):
            _mesclar(base[k], meu[k], disco[k])
        elif k not in base or base[k] != meu[k]:
            disco[k] = copy.deepcopy(meu[k])


def gravar_estado(e):
    """Produção e postagem são processos separados gravando este arquivo: aplica no disco só o que ESTE
    processo mudou desde que leu (o que o outro gravou fica) e troca o arquivo inteiro de uma vez."""
    global _lido
    disco = _ler_disco()
    _mesclar(_lido, e, disco)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(disco, ensure_ascii=False, indent=2), encoding="utf-8")
    for tentativa in range(40):
        try:
            os.replace(tmp, ESTADO)
            break
        except PermissionError:
            if tentativa == 39:
                raise
            time.sleep(0.25)
    _lido = copy.deepcopy(e)


def video_do_estado(rel):
    """Vídeo gravado no estado; se foi organizado em <obra>/capNN/<idioma>/..., acha pelo nome; se era o
    normal de outra língua (lá só fica a censurada), devolve a censurada do mesmo render."""
    p = VIDEOS / rel
    if p.exists():
        return p
    nome = Path(rel).name
    for n in (nome, nome.replace("_ULTIMO.mp4", "_CENSURADO_ULTIMO.mp4")):
        achado = next(VIDEOS.rglob(n), None)
        if achado:
            return achado
    return p


def avisar(msg):
    log(msg)
    try:
        import _tg_safe
        _tg_safe.send(f"🎬 hipercool: {_tg_safe.esc(msg)}")
    except Exception:  # noqa: BLE001
        pass


def capitulos():
    """[(chave, obra, n, pasta)] na ordem da fila (só os que têm painéis)."""
    out = []
    for o in cfg()["obras"]:
        for n in range(o["de"], o["ate"] + 1):
            pasta = next((p for p in (PANELS / f"{o['slug']}-cap{n:02d}", PANELS / f"{o['slug']}-cap{n}")
                          if p.is_dir()), None)
            if pasta:
                out.append((pasta.name, o, n, pasta))
    return out


# ─── propaganda/créditos do scan (início e fim do capítulo) ──────────────────
def detectar_propaganda(pasta):
    """{"inicio": n, "fim": m}: painéis de propaganda/créditos do grupo de scan nas pontas.
    Pergunta ao Claude (Sonnet do Kiro) olhando os 2 primeiros e os 3 últimos painéis."""
    import claude_client
    from PIL import Image
    from io import BytesIO
    fs = sorted(p for p in pasta.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    pontas = fs[:2] + fs[-3:]
    imgs = []
    for f in pontas:
        im = Image.open(f).convert("RGB")
        im.thumbnail((512, 512))
        b = BytesIO()
        im.save(b, "JPEG", quality=80)
        imgs.append(b.getvalue())
    r = claude_client._extract_json(claude_client.perguntar(
        f"São {len(imgs)} painéis de um capítulo de manhwa, nesta ordem. Classifique CADA um:\n"
        "- \"propaganda\": página que é SÓ anúncio/créditos do grupo de scan (texto 'lançado primeiro em', "
        "logo, site, Discord, 'continua...', ficha de tradução/equipe), sem cena da história;\n"
        "- \"historia\": qualquer painel com cena/personagem/balão da história — mesmo que tenha a marca "
        "d'água do site do scan escrita por cima da arte.\n"
        f'Responda só JSON {{"paineis": [{", ".join(chr(34) + "..." + chr(34) for _ in imgs)}]}}.',
        imgs, max_tokens=150, temperature=0))
    cls = (r or {}).get("paineis") if isinstance(r, dict) else None
    if not isinstance(cls, list) or len(cls) != len(imgs):
        return {"inicio": 0, "fim": 0, "_fonte": "padrão (Claude indisponível)"}
    eh = [str(c).lower().startswith("prop") for c in cls]
    inicio = next((i for i, p in enumerate(eh[:2]) if not p), 2)
    fim = next((i for i, p in enumerate(reversed(eh[2:])) if not p), 3)
    return {"inicio": inicio, "fim": fim, "_fonte": "claude", "_classes": cls}


# ─── render ──────────────────────────────────────────────────────────────────
def tempo_livre(est):
    """Quando não há capítulo em pt pra renderizar: 1 língua e a parte 16:9 de 1 capítulo (só render; quem
    posta é a postagem, processo separado). idiomas_auto=false desliga a produção das outras línguas."""
    if cfg().get("idiomas_auto", True):
        idiomas(est, max_renders=1)
    longo(est)


def longo(est):
    """Vídeo longo 16:9 (bin/hiper-longo.py): monta o capítulo pronto mais antigo que ainda não tem a
    parte deitada (pt primeiro, depois as línguas ativas que já têm o vertical) e refaz a compilação da obra
    (cap 1 até o último pronto). Só usa cache, sem IA nova. Um capítulo por ciclo; "longo": false desliga."""
    c = cfg()
    if not c.get("longo", True) or limitador.restante("render"):
        return
    langs = [None] + [l for l, i in c["idiomas"].items() if i.get("ativo", True)]
    for lang in langs:
        marca = "longo" if not lang else f"longo_{lang}"
        for o in c["obras"]:
            caps = [(k, n) for k, ob, n, _p in capitulos() if ob["slug"] == o["slug"]
                    and est.get(k, {}).get("situacao") == "pronto"
                    and (not lang or ((est[k].get("idiomas") or {}).get(lang) or {}).get("video"))]
            falta = [(k, n) for k, n in caps if not est[k].get(marca)]
            if not falta:
                continue
            # sempre do 1º ao último pronto: a compilação nunca encolhe (o hiper-longo pula os capNN prontos)
            ate = max(n for _k, n in caps)
            logf = PROJECT / "logs" / f"fila_longo_{o['slug']}{'_' + lang if lang else ''}.log"
            with open(logf, "a", encoding="utf-8") as fh:
                rc = subprocess.run([PY, str(PROJECT / "bin" / "hiper-longo.py"), "--obra", o["slug"],
                                     "--caps", f"{o['de']}-{ate}", "--compilar", *(["--idioma", lang] if lang else [])],
                                    cwd=PROJECT, env=ENV, stdout=fh, stderr=subprocess.STDOUT).returncode
            if rc:
                limitador.falhou("render", f"longo {o['slug']} {lang or 'pt'}")
                avisar(f"falhou o vídeo longo 16:9 de {o['titulo']} {lang or 'pt'} (ver {logf.name})")
                return
            for k, _n in caps:
                est[k][marca] = datetime.now().isoformat(timespec="seconds")
            gravar_estado(est)
            log(f"  vídeo longo 16:9 {lang or 'pt'} de {o['titulo']} atualizado até o cap {ate}")
            return


def postar_longos(est):
    """Posta a compilação 16:9 de cada canal (pt e línguas ativas): a 1ª quando tiver longo_primeiro (2)
    capítulos; depois a cada longo_a_cada (3) capítulos novos. Marca em est['_longo_postado'][lang] = n caps."""
    c = cfg()
    if not c.get("longo", True) or limitador.restante("youtube"):
        return
    feito = est.setdefault("_longo_postado", {})
    alvos = ([(None, None)] if c.get("postar_pt", True) else []) + \
        [(l, i["canal"]) for l, i in c["idiomas"].items() if i.get("ativo", True)]
    for o in c["obras"]:
        for lang, canal in alvos:
            if lang and not _pode_postar(c["idiomas"][lang])[0]:
                continue
            pasta = PROJECT / "workspace" / "videos" / "longo" / o["slug"] / (lang or "")
            comps = sorted(pasta.glob(f"{o['slug']}_caps*.mp4"), key=lambda p: p.stat().st_mtime)
            if not comps:
                continue
            caps = len(json.loads(comps[-1].with_suffix(".json").read_text(encoding="utf-8")).get("caps", []))
            chave = f"{o['slug']}|{lang or 'pt'}"
            ja = feito.get(chave, 0)
            if caps < c.get("longo_primeiro", 2) or (ja and caps - ja < c.get("longo_a_cada", 3)) or caps <= ja:
                continue
            extra = ["--longo", o["slug"]] + (["--canal", canal, "--idioma", lang] if lang else [])
            resumo, _ = _postar(comps[-1], extra)
            if "longo=ok" in resumo or "longo=ja" in resumo:
                feito[chave] = caps
                gravar_estado(est)
                avisar(f"compilação 16:9 de {o['titulo']} ({caps} caps) postada em {lang or 'pt'}")
            elif re.search(r"=(erro|timeout)", resumo):
                limitador.falhou("youtube", f"longo {lang or 'pt'}: {resumo}")
                return


def migrar_canal():
    """Troca o canal pt (config canal_pt): guarda o que já foi postado no canal antigo em pt_antigo e zera,
    pra série recomeçar do cap 1 no canal novo. Rodar DEPOIS de mudar canal_pt e antes de postar_pt=true."""
    est = ler_estado()
    novo = cfg().get("canal_pt")
    n = 0
    for k, e in est.items():
        if not isinstance(e, dict) or k.startswith("_"):
            continue
        if e.get("pt_completo_em") or e.get("pt_shorts_ok"):
            e.setdefault("pt_antigo", {})[e.get("pt_canal", "inovaremanhwabr")] = {
                "pt_completo_em": e.pop("pt_completo_em", None), "pt_shorts_ok": e.pop("pt_shorts_ok", None)}
            n += 1
        e["pt_canal"] = novo
    est.get("_longo_postado", {}).pop(next((o["slug"] for o in cfg()["obras"]), "") + "|pt", None)
    gravar_estado(est)
    print(f"canal pt -> {novo}: {n} capítulo(s) voltam a postar do zero no canal novo")


def renderizar(chave, obra, n, pasta, est):
    e = est.setdefault(chave, {})
    if "skip" not in e:
        e["skip"] = detectar_propaganda(pasta)
        gravar_estado(est)
    sk = e["skip"]
    titulo = f"{obra['titulo']} — Capítulo {n}"
    logf = PROJECT / "logs" / f"fila_{chave}.log"
    cmd = [PY, str(PROJECT / "bin" / "hiper-pipeline.py"), "--panels-dir", str(pasta), "--titulo", titulo,
           "--max-panels", "120", "--subtitles", "--karaoke", "--censura", "--skip-notify",
           "--output-suffix", "_NORMAL"]
    if sk["fim"]:
        cmd += ["--skip-final", str(sk["fim"])]
    if sk["inicio"]:
        cmd += ["--start-panel", str(sk["inicio"])]
    e.update(render="rodando", inicio_render=datetime.now().isoformat(timespec="seconds"))
    gravar_estado(est)
    avisar(f"renderizando {titulo} (pula {sk['inicio']} no início, {sk['fim']} no fim)")
    with open(logf, "w", encoding="utf-8") as fh:
        rc = subprocess.run(cmd, cwd=PROJECT, env=_env_render(), stdout=fh, stderr=subprocess.STDOUT).returncode
    texto = logf.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\[OK\] Vídeo final: (\S+\.mp4)", texto)
    if rc != 0 or not m:
        e["render"] = "falhou"
        gravar_estado(est)
        pausa = limitador.falhou("render", f"{chave} rc={rc}")
        avisar(f"FALHOU o render de {titulo} (log {logf.name}); pausa {pausa // 60} min")
        return False
    limitador.ok("render")
    e.update(video=m.group(1), render="ok", fim_render=datetime.now().isoformat(timespec="seconds"))
    e.update(avaliar_censurado(VIDEOS / m.group(1)))
    gravar_estado(est)
    avisar(f"{titulo} pronto ({e['situacao']}; censura {e.get('frac_censura', 0):.0%} do tempo)")
    return True


def avaliar_censurado(video):
    """Checagem automática no lugar da revisão manual: censurada existe, validou, e não é quase toda tarja."""
    import postar_hipercool as ph
    cens = ph.achar_censurado(video)
    meta = ph.ler_meta(cens) if cens else {}
    if not cens or "censura" not in meta:
        return {"situacao": "sem_censurado"}
    val = (meta.get("acabamento") or {}).get("validacao") or {}
    dur = float(val.get("duracao") or 1)
    frac = sum(b - a for a, b in meta["censura"].get("janelas", [])) / dur
    folha = ph.gerar_folha(cens)
    if not val.get("ok"):
        return {"situacao": "invalido", "problemas": val.get("problemas"), "folha": folha.name}
    if frac > cfg()["max_censura"]:
        return {"situacao": "compilado", "frac_censura": round(frac, 3), "folha": folha.name}
    return {"situacao": "pronto", "frac_censura": round(frac, 3), "folha": folha.name}


# ─── postagem ────────────────────────────────────────────────────────────────
def _postar(video, extra):
    r = subprocess.run([PY, str(PROJECT / "bin" / "postar_hipercool.py"), "--video", str(video), "--aprovado",
                        *extra], cwd=PROJECT, env=ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=6 * 3600)
    saida = (r.stdout or "") + (r.stderr or "")
    resumo = re.findall(r"RESUMO: (.*)", saida)
    log(f"  postar {Path(video).name} {' '.join(extra)}: {resumo[-1] if resumo else saida[-300:]}")
    return resumo[-1] if resumo else "", saida


def postar_pt(est):
    """1 completo novo por dia; o resto da cota vai pros Shorts (capítulos mais antigos primeiro)."""
    if not cfg().get("postar_pt", True):
        log(f"  postagem em pt SEGURADA (config/fila.json postar_pt=false): {cfg().get('_postar_pt_motivo', '')}")
        return
    if limitador.restante("youtube"):
        log(f"  youtube em pausa por mais {limitador.restante('youtube') // 60} min")
        return
    hoje = datetime.now().date().isoformat()
    prontos = [(k, est[k]) for k, *_ in capitulos() if est.get(k, {}).get("situacao") == "pronto"]
    if not any(e.get("pt_completo_em", "")[:10] == hoje for _, e in prontos):
        for k, e in prontos:
            if not e.get("pt_completo_em"):
                resumo, _ = _postar(video_do_estado(e["video"]), ["--no-shorts"])
                if re.search(r"completo=(ok|ja)", resumo):
                    e["pt_completo_em"] = datetime.now().isoformat(timespec="seconds")
                    gravar_estado(est)
                    avisar(f"postado o completo de {k}")
                elif re.search(r"completo=(cota|limite)", resumo):
                    return
                elif "completo=" in resumo:
                    limitador.falhou("youtube", resumo)
                    return
                break
    for k, e in prontos:
        if e.get("pt_completo_em") and not e.get("pt_shorts_ok"):
            resumo, _ = _postar(video_do_estado(e["video"]), ["--no-completo"])
            if re.search(r"=(cota|limite)", resumo):
                return
            if re.search(r"=(erro|timeout)", resumo):
                limitador.falhou("youtube", resumo)
                return
            if resumo and not re.search(r"=(ensaio|cota|limite|erro|timeout|nao_aprovado)", resumo):
                e["pt_shorts_ok"] = datetime.now().isoformat(timespec="seconds")
                gravar_estado(est)
                avisar(f"todos os Shorts de {k} postados")


def idiomas(est, max_renders=None):
    """Versões nas outras línguas dos capítulos já postados em pt (prioridade sempre é o pt; com o pt
    SEGURADO — postar_pt=false — as línguas seguem sem esperar). max_renders: quantas línguas renderizar
    neste ciclo (None = todas).

    Só renderiza — a postagem fica com postar_idiomas() que o ciclo chama a cada 20 min."""
    c = cfg()
    renders = 0
    for k, obra, n, pasta in capitulos():
        e = est.get(k, {})
        if e.get("situacao") != "pronto" or not (e.get("pt_completo_em") or not c.get("postar_pt", True)):
            continue
        for lang, info in c["idiomas"].items():
            if not info.get("ativo", True):
                continue
            li = e.setdefault("idiomas", {}).setdefault(lang, {})
            if li.get("postado") or li.get("video"):
                continue
            if limitador.restante("render") or (max_renders is not None and renders >= max_renders):
                break
            renders += 1
            titulo = f"{obra['titulo']} — Capítulo {n}"
            logf = PROJECT / "logs" / f"fila_{k}_{lang}.log"
            sk = e.get("skip", {})
            cmd = [PY, str(PROJECT / "bin" / "hiper-pipeline.py"), "--panels-dir", str(pasta), "--titulo",
                   titulo, "--max-panels", "120", "--subtitles", "--karaoke", "--censura", "--skip-notify",
                   "--output-suffix", f"_{lang.upper()}", "--idioma", lang]
            if sk.get("fim"):
                cmd += ["--skip-final", str(sk["fim"])]
            if sk.get("inicio"):
                cmd += ["--start-panel", str(sk["inicio"])]
            with open(logf, "w", encoding="utf-8") as fh:
                rc = subprocess.run(cmd, cwd=PROJECT, env=_env_render(), stdout=fh, stderr=subprocess.STDOUT).returncode
            m = re.search(r"\[OK\] Vídeo final: (\S+\.mp4)", logf.read_text(encoding="utf-8", errors="replace"))
            if rc or not m:
                limitador.falhou("render", f"{k} {lang}")
                avisar(f"falhou a versão {info['nome']} de {k}")
                continue
            li["video"] = m.group(1)
            gravar_estado(est)


def _politica():
    if str(POSTADOR_BIN) not in sys.path:
        sys.path.insert(0, str(POSTADOR_BIN))
    import politica
    return politica


def _uploads_canal(canal_id):
    """Horários de publicação (com fuso) de tudo que já subiu neste canal, de qualquer projeto: ledger do
    postador, contando as credenciais-alias do mesmo canal."""
    politica = _politica()
    ids = politica.creds_mesmo_canal(canal_id)
    return sorted(politica._dt(r.get("publish_at")) or politica._dt(r["ts"])
                  for r in politica._ler_ledger() if r.get("canal_id") in ids)


def _pode_postar(info):
    """(pode, motivo) pra subir agora no canal da língua. Canal sem nada há mais de parado_h: sai já.
    Senão só no horário de pico do país (hora de lá), intervalo_h depois do último e até max_dia por dia."""
    from datetime import timedelta
    from zoneinfo import ZoneInfo
    politica = _politica()
    canal, _err = politica.achar_canal(info["canal"])
    bloqueio = politica.motivo_bloqueio(canal) if canal else "canal não achado"
    if bloqueio:  # pausado/suspenso no postador (ex.: aviso de direitos autorais): nem tenta
        return False, f"canal bloqueado no postador ({bloqueio})"
    p = cfg().get("postagem_idiomas", {})
    agora_la = datetime.now(ZoneInfo(info.get("fuso", "UTC")))
    ups = _uploads_canal(info["canal"])
    if not ups or agora_la - ups[-1] > timedelta(hours=p.get("parado_h", 24)):
        return True, "canal parado, sai já"
    if agora_la - ups[-1] < timedelta(hours=p.get("intervalo_h", 2)):
        return False, f"último há {(agora_la - ups[-1]).total_seconds() / 3600:.1f} h"
    hoje = sum(1 for u in ups if u.astimezone(agora_la.tzinfo).date() == agora_la.date())
    if hoje >= p.get("max_dia", 3):
        return False, f"já subiram {hoje} hoje"
    ini, fim = info.get("pico", [17, 22])
    if not ini <= agora_la.hour < fim:
        return False, f"fora do pico ({agora_la:%H:%M} lá, pico {ini}h-{fim}h)"
    return True, f"pico ({agora_la:%H:%M} lá)"


def postar_idiomas(est):
    """Uma subida por canal de língua por rodada, quando _pode_postar libera. Capítulos em ordem; dentro do
    capítulo o completo e depois os Shorts (postar_hipercool --max-novos 1 retoma de onde parou)."""
    c = cfg()
    for lang, info in c["idiomas"].items():
        if not info.get("ativo", True) or limitador.restante("youtube"):
            continue
        k = next((k for k, *_ in capitulos()
                  if ((est.get(k) or {}).get("idiomas") or {}).get(lang, {}).get("video")
                  and not est[k]["idiomas"][lang].get("postado")), None)
        if not k:
            continue
        pode, motivo = _pode_postar(info)
        if not pode:
            log(f"  {info['nome']}: espera — {motivo}")
            continue
        li = est[k]["idiomas"][lang]
        log(f"  {info['nome']}: sobe 1 de {k} — {motivo}")
        resumo, _ = _postar(video_do_estado(li["video"]),
                            ["--canal", info["canal"], "--idioma", lang, "--max-novos", "1"])
        if "=morto" in resumo:  # problema só deste canal (login/pausa): não pausa a postagem dos outros
            avisar(f"canal {info['nome']} recusou o upload: {resumo[:120]}")
            continue
        if re.search(r"=(erro|timeout|suspenso|parado)", resumo):
            limitador.falhou("youtube", f"{lang}: {resumo}")
            avisar(f"falhou a postagem {info['nome']} de {k}: {resumo[:120]}")
            continue
        if resumo and "faltam=" not in resumo and not re.search(r"=(cota|limite|nao_aprovado|reservado)", resumo):
            li["postado"] = datetime.now().isoformat(timespec="seconds")
            gravar_estado(est)
            avisar(f"{k} todo postado em {info['nome']}")


# ─── ciclo / lock / ligar ────────────────────────────────────────────────────
def _vivo(pid):
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
    return str(pid) in r.stdout


def _pegar_lock(lock):
    if lock.exists():
        try:
            pid = int(lock.read_text().split()[0])
            if _vivo(pid):
                log(f"outro {lock.stem} rodando (pid {pid})")
                return False
        except (ValueError, IndexError):
            pass
    lock.write_text(f"{os.getpid()} {datetime.now().isoformat(timespec='seconds')}")
    return True


def _subindo_agora():
    """Algum postar_hipercool vivo (rodada anterior, botão manual ou ciclo interrompido)? Um upload por vez."""
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "@(Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Where-Object "
                        "{ $_.CommandLine -match 'postar_hipercool\\.py' }).Count"],
                       capture_output=True, text=True)
    return (r.stdout or "0").strip() not in ("", "0")


def postagem(manual=False, so_pt=False):
    """Postagem, separada da produção (tarefa HipercoolPostagem a cada 20 min): pt, línguas e 16:9.
    Uma desligada não para a outra: config/POSTAGEM_DESLIGADA.json só vale pra rodada automática."""
    if POSTAGEM_DESLIGADA.exists() and not manual:
        log("postagem desligada (config/POSTAGEM_DESLIGADA.json)")
        return
    if not _pegar_lock(LOCK_POSTAGEM):
        return
    try:
        if _subindo_agora():
            log("tem upload do hipercool em andamento; fica pra próxima rodada")
            return
        est = ler_estado()
        postar_pt(est)
        if not so_pt:
            postar_idiomas(est)
            postar_longos(est)
    finally:
        LOCK_POSTAGEM.unlink(missing_ok=True)


def ciclo(com_idiomas=False):
    """Produção (tarefa HipercoolFila a cada 20 min): só renderiza, nunca espera postagem."""
    if DESLIGADA.exists() and not com_idiomas:  # o botão manual das línguas funciona com a fila desligada
        log("fila desligada (config/FILA_DESLIGADA.json)")
        return
    if not _pegar_lock(LOCK):
        return
    try:
        est = ler_estado()
        if com_idiomas:
            idiomas(est)
            return
        if limitador.restante("render"):
            log(f"render em pausa por mais {limitador.restante('render') // 60} min")
            return
        caps = capitulos()
        prontos_nao_postados = sum(1 for k, *_ in caps
                                   if est.get(k, {}).get("situacao") == "pronto" and not est[k].get("pt_shorts_ok"))
        if prontos_nao_postados >= cfg()["adiantado"]:
            log(f"{prontos_nao_postados} capítulos prontos esperando postagem; não renderiza agora")
            tempo_livre(est)
            return
        for k, obra, n, pasta in caps:
            if est.get(k, {}).get("render") not in ("ok",):
                renderizar(k, obra, n, pasta, est)
                break
        else:
            log("fila de capítulos terminada — adicione a próxima obra em config/fila.json")
            tempo_livre(est)
    finally:
        LOCK.unlink(missing_ok=True)


def _estado_tarefa(nome):
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"(Get-ScheduledTask -TaskName '{nome}' -ErrorAction SilentlyContinue).State"],
                       capture_output=True, text=True)
    return (r.stdout or "").strip() or "não criada"


def status():
    est = ler_estado()
    for nome, tarefa, desl in (("Produção", TAREFA, DESLIGADA), ("Postagem", TAREFA_POSTAGEM, POSTAGEM_DESLIGADA)):
        st = _estado_tarefa(tarefa)
        ligada = not desl.exists() and st in ("Ready", "Running")
        print(f"{nome}: {'LIGADA' if ligada else 'DESLIGADA'} (tarefa {tarefa}: {st})")
    print(f"Pausas: {limitador.resumo()}")
    for lang, info in cfg()["idiomas"].items():
        if info.get("ativo", True):
            try:
                print(f"  postagem {info['nome']:11s} {_pode_postar(info)[1]}")
            except Exception as e:  # noqa: BLE001
                print(f"  postagem {info['nome']:11s} ? ({e})")
    for k, *_ in capitulos():
        e = est.get(k)
        if not e:
            continue
        idi = " ".join(f"{l}:{'ok' if v.get('postado') else ('render' if v.get('video') else '-')}"
                       for l, v in (e.get("idiomas") or {}).items())
        print(f"  {k:28s} render={e.get('render', '-'):8s} {e.get('situacao', ''):10s} "
              f"pt_completo={'sim' if e.get('pt_completo_em') else 'não'} "
              f"pt_shorts={'sim' if e.get('pt_shorts_ok') else 'não'} {idi}")
    pend = [k for k, *_ in capitulos() if k not in est]
    print(f"  ... {len(pend)} capítulos ainda não começados")


def ligar(tarefa=TAREFA, comando="ciclo", desligada=DESLIGADA, nome="Produção"):
    desligada.unlink(missing_ok=True)
    acao = (f"$a = New-ScheduledTaskAction -Execute '{PROJECT / 'venv' / 'Scripts' / 'pythonw.exe'}' "
            f"-Argument '{PROJECT / 'bin' / 'fila.py'} {comando}' -WorkingDirectory '{PROJECT}'; "
            "$t = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) "
            "-RepetitionInterval (New-TimeSpan -Minutes 20); "
            "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew "
            "-ExecutionTimeLimit (New-TimeSpan -Hours 6); "
            f"Register-ScheduledTask -TaskName '{tarefa}' -Action $a -Trigger $t -Settings $s -Force | Out-Null")
    subprocess.run(["powershell", "-NoProfile", "-Command", acao], check=True)
    print(f"{nome} LIGADA: uma rodada a cada 20 min (tarefa {tarefa}).")


def desligar(tarefa=TAREFA, desligada=DESLIGADA, nome="Produção"):
    desligada.write_text(json.dumps({"desde": datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    f"Disable-ScheduledTask -TaskName '{tarefa}' -ErrorAction SilentlyContinue | Out-Null"])
    print(f"{nome} DESLIGADA (o que estiver rodando agora termina; nada novo começa).")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if sys.stderr is None:  # tarefa agendada (pythonw, sem console): o log vai pra logs/fila_<comando>.log
        sys.stderr = open(PROJECT / "logs" / f"fila_{cmd}.log", "a", encoding="utf-8", buffering=1)
    {"ciclo": lambda: ciclo(), "idiomas": lambda: ciclo(com_idiomas=True),
     "postagem": lambda: postagem(), "postar": lambda: postagem(manual=True, so_pt=True),
     "status": status, "ligar": ligar, "desligar": desligar,
     "ligar-postagem": lambda: ligar(TAREFA_POSTAGEM, "postagem", POSTAGEM_DESLIGADA, "Postagem"),
     "desligar-postagem": lambda: desligar(TAREFA_POSTAGEM, POSTAGEM_DESLIGADA, "Postagem"),
     "migrar-canal": migrar_canal}[cmd]()
