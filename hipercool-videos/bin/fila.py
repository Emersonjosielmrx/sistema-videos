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
  python bin/fila.py pc2                # traz o pronto do PC2 e dispara a próxima língua (o controlador geral chama)
  python bin/fila.py pc2-trazer         # só traz o pronto do PC2 (tarefa HipercoolPC2, 20 min)
  python bin/fila.py faltantes          # só correções/línguas/compilado, sem capítulo novo (o controlador geral chama)
  python bin/fila.py ligar-pc2 | desligar-pc2

Regras: 1 vídeo completo novo por dia no canal pt (o resto da cota vai pra Shorts); renderiza no máximo
`adiantado` capítulos à frente do que já foi postado; capítulo com mais de `max_censura` do tempo censurado
não é postado avulso (fica "compilado"); canais das línguas: 1 subida por vez no pico do país
(`postagem_idiomas`); erro/limite -> pausa dinâmica (limitador) em vez de insistir.
"""
import copy
import json
import shutil
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
import sem_janela  # noqa: E402,F401  (filhos sem janela na tela: roda no pythonw)
import limitador  # noqa: E402

CONFIG = PROJECT / "config" / "fila.json"
DESLIGADA = PROJECT / "config" / "FILA_DESLIGADA.json"
POSTAGEM_DESLIGADA = PROJECT / "config" / "POSTAGEM_DESLIGADA.json"
ESTADO = PROJECT / "workspace" / "fila_estado.json"
LOCK = PROJECT / "workspace" / "fila.lock"
LOCK_POSTAGEM = PROJECT / "workspace" / "postagem.lock"
LOCK_PC2 = PROJECT / "workspace" / "pc2.lock"
PC2_DESLIGADO = PROJECT / "config" / "PC2_DESLIGADO.json"
POSTADOR_BIN = Path(r"D:\postador-de-videos\bin")
PANELS = Path(r"D:\hipercool-materiais\panels")
VIDEOS = PROJECT / "workspace" / "videos"
PY = str(PROJECT / "venv" / "Scripts" / "python.exe")
ENV = dict(os.environ, PYTHONUTF8="1", GEMINI_TTS_PROXY_ENABLED="1",
           PATH=r"D:\hipercool-materiais\bin" + os.pathsep + os.environ.get("PATH", ""))
TAREFA = "HipercoolFila"
TAREFA_POSTAGEM = "HipercoolPostagem"
TAREFA_PC2 = "HipercoolPC2"


def cfg():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _pt_ligado(c):
    """postar_pt=false segura o pt; com postar_pt_volta_em (AAAA-MM-DD) a pausa acaba sozinha nesse dia."""
    volta = c.get("postar_pt_volta_em")
    return c.get("postar_pt", True) or bool(volta and datetime.now().date().isoformat() >= volta)


def _env_render(extra=None):
    """cache_clipes (config) liga/desliga o cache do movimento 2.5D (bin/fx_parallax.py).
    extra: variáveis a mais só pra este render (ex.: a marca d'água do canal da língua)."""
    env = dict(ENV, HIPER_CACHE_2P5D="1" if cfg().get("cache_clipes", True) else "0")
    env.update(extra or {})
    return env


def _marca_do_idioma(info):
    """Marca d'água do canal da LÍNGUA. O handle é constante do projeto (hp_common), então o vídeo
    hindi/tailandês saía com o @ do canal brasileiro no canto: manda o público pro canal errado e
    liga os canais entre si (todos já com advertência). Sem "handle" na config da língua o vídeo sai
    SEM marca — melhor nenhuma do que a errada."""
    return {"HIPERCOOL_WATERMARK": (info.get("handle") or "").strip()}


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


IMPORTANTE = re.compile(r"falh|erro|não vai|nao vai|não sobe|parou|parad|bloque|suspens|advert|quebr|sem espaço|"
                        r"esgot|deslog", re.I)


def avisar(msg):
    """Problema sai na hora; o resto (pronto, postado, renderizando) vai pro resumo 3x/dia do portão único
    (D:\\video-fila\\avisos.py, dono 19/10: "manda muita mensagem")."""
    log(msg)
    try:
        import _tg_safe
        _tg_safe.send(f"🎬 hipercool: {_tg_safe.esc(msg)}", importante=bool(IMPORTANTE.search(msg)))
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
def corrigir_pendentes(est):
    """Capítulo já PRONTO cujo vídeo é mais velho que a marcação de um painel dele pra sair coberto:
    refaz, um por rodada, quando a máquina está ociosa.

    Pedido do dono em 16/10: ele liberou o cap 4 com o quadro de 3m25 pra não travar a produção
    ("pode ir para o 5, depois se der tempo cubra"), e disse que as correções deviam sair sozinhas
    "quando estiver ocioso". É isso aqui.

    Não precisa de lista escrita à mão: um painel forçado (censura_visual.forcar_fosco) guarda a
    hora em que foi marcado; se essa hora é depois do fim do render do capítulo, então o vídeo que
    está lá ainda tem o painel à mostra. Depois do render novo o fim_render passa a ser o mais
    recente e o capítulo sai da lista sozinho — refaz uma vez, não fica em laço."""
    import revisao_video
    if not cfg().get("corrigir_pendentes", True):
        return False
    censura_visual = revisao_video.modulo("censura_visual")
    marcados = {}
    for p in censura_visual._forcados().values():
        try:
            quando = datetime.strptime(p.get("em", ""), "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        chave = Path(p["painel"]).parent.name
        if quando > marcados.get(chave, datetime.min):
            marcados[chave] = quando
    for chave, obra, n, pasta in capitulos():
        e = est.get(chave) or {}
        if e.get("situacao") != "pronto" or not e.get("fim_render") or chave not in marcados:
            continue
        if e.get("pt_completo_em"):
            # 17/10, o dono: "a produção é pra continuar pra capítulos novos". Refazer o vertical de um capítulo
            # que JÁ ESTÁ NO AR em pt não muda o vídeo publicado — só tira tempo dos novos. Trocar o vídeo do ar é
            # decisão do dono (não deste robô).
            continue
        if marcados[chave] <= datetime.fromisoformat(e["fim_render"]):
            continue  # o vídeo que está lá já foi feito depois da marcação
        log(f"  correção pendente: {chave} — painel marcado em "
            f"{marcados[chave]:%d/%m %H:%M}, vídeo de {datetime.fromisoformat(e['fim_render']):%d/%m %H:%M}")
        avisar(f"tempo livre: refazendo {chave} pra cobrir o painel que ficou à mostra")
        renderizar(chave, obra, n, pasta, est)
        return True
    return False


def tempo_livre(est):
    """Quando não há capítulo em pt pra renderizar: primeiro as correções pendentes (capítulo pronto com
    painel marcado pra cobrir depois), e só então 1 língua e a parte 16:9 de 1 capítulo (só render; quem
    posta é a postagem, processo separado). idiomas_auto=false desliga a produção das outras línguas."""
    if corrigir_pendentes(est):  # primeiro o que ficou torto, depois trabalho novo
        return
    compilados_do_dia(est)  # 23/10: 16:9 avulso + compilado 1..N do capítulo do dia (só colar, minutos)
    if cfg().get("idiomas_auto", True):
        idiomas(est, max_renders=1)
    longo(est)


def _seg_velho(est, o, lang, n, estrito=False):
    """(estado do cap, vídeo vertical) se o capNN.mp4 16:9 é mais velho que o vertical atual e ainda não foi refeito
    por isso (marca longo[_lang]_refeito; estrito=True ignora a marca: o compilado nunca usa um velho); senão None.
    23/10 (dona): no pt, os capNN.mp4 de 15-16/10 têm a marca do canal antigo e as vozes velhas."""
    k = next((k for k, ob, n_, _p in capitulos() if ob["slug"] == o["slug"] and n_ == n), None)
    e = est.get(k) or {}
    rel = (((e.get("idiomas") or {}).get(lang) or {}).get("video") if lang else e.get("video"))
    seg = PROJECT / "workspace" / "videos" / "longo" / o["slug"] / (lang or "") / f"cap{n:02d}.mp4"
    vert = video_do_estado(rel) if rel else None
    marca = "longo" if not lang else f"longo_{lang}"
    if (seg.exists() and vert and vert.exists() and seg.stat().st_mtime < vert.stat().st_mtime
            and (estrito or e.get(f"{marca}_refeito") != rel)):
        return e, rel
    return None


def longo(est):
    """Vídeo longo 16:9 (bin/hiper-longo.py): renderiza a parte deitada (capNN.mp4) dos capítulos prontos ou já
    postados no canal (pt primeiro, depois as línguas ativas que já têm o vertical) e refaz o capNN.mp4 do capítulo do
    dia se for mais velho que o vertical. Só usa cache, sem IA nova; "longo": false desliga. Colar a compilação é
    do compilados_do_dia desde 23/10."""
    c = cfg()
    if not c.get("longo", True) or limitador.restante("render"):
        return
    langs = [None] + [l for l, i in c["idiomas"].items() if i.get("ativo", True)]
    for lang in langs:
        marca = "longo" if not lang else f"longo_{lang}"
        for o in c["obras"]:
            postados = set(_caps_postados(est, o, lang))  # 23/10: capítulo já no canal precisa do 16:9 mesmo "revisar"
            caps = [(k, n) for k, ob, n, _p in capitulos() if ob["slug"] == o["slug"]
                    and (est.get(k, {}).get("situacao") == "pronto" or n in postados)
                    and (not lang or ((est[k].get("idiomas") or {}).get(lang) or {}).get("video"))]
            # 23/10: capNN.mp4 mais velho que o vertical atual (vozes/censura/marca velhas): refaz, 1 por vez — o do
            # capítulo do dia primeiro, depois os de..N-1 que o compilado 1..N vai usar
            alvo = ([max(postados)] + list(range(o["de"], max(postados)))) if postados else []
            n = next((n for n in alvo if _seg_velho(est, o, lang, n)), None)
            if n is not None:
                e, rel = _seg_velho(est, o, lang, n)
                logf = PROJECT / "logs" / f"fila_longo_{o['slug']}{'_' + lang if lang else ''}.log"
                with open(logf, "a", encoding="utf-8") as fh:  # --refazer: entra na fila_render (pesado)
                    rc = subprocess.run([PY, str(PROJECT / "bin" / "hiper-longo.py"), "--obra", o["slug"], "--caps",
                                         f"{n}-{n}", "--refazer", *(["--idioma", lang] if lang else [])],
                                        cwd=PROJECT, env=ENV, stdout=fh, stderr=subprocess.STDOUT).returncode
                e[f"{marca}_refeito"] = rel  # uma vez por vertical, mesmo se falhar (não fica em laço)
                gravar_estado(est)
                if rc:
                    limitador.falhou("render", f"longo {o['slug']} cap {n} {lang or 'pt'}")
                log(f"  16:9 do cap {n} {lang or 'pt'} refeito (era mais velho que o vertical): rc={rc}")
                return
            falta = [(k, n) for k, n in caps if not est[k].get(marca)]
            if not falta:
                continue
            # só os capNN.mp4 (render pesado, entra na fila_render). Desde 23/10 a compilação NÃO sai daqui: quem
            # cola é compilados_do_dia (1..N do capítulo postado no dia; um 1..máximo apagaria o 1..N não postado)
            ate = max(n for _k, n in caps)
            logf = PROJECT / "logs" / f"fila_longo_{o['slug']}{'_' + lang if lang else ''}.log"
            with open(logf, "a", encoding="utf-8") as fh:
                rc = subprocess.run([PY, str(PROJECT / "bin" / "hiper-longo.py"), "--obra", o["slug"],
                                     "--caps", f"{o['de']}-{ate}", *(["--idioma", lang] if lang else [])],
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


def _caps_postados(est, o, lang):
    """Capítulos da obra cujo completo (retrato) já subiu no canal (pt: pt_completo_em; língua: completo_em)."""
    out = []
    for k, ob, n, _p in capitulos():
        e = est.get(k) or {}
        if ob["slug"] == o["slug"] and (e.get("pt_completo_em") if not lang
                                        else ((e.get("idiomas") or {}).get(lang) or {}).get("completo_em")):
            out.append(n)
    return out


def _longo_arq(o, lang, a, b):
    return PROJECT / "workspace" / "videos" / "longo" / o["slug"] / (lang or "") / f"{o['slug']}_caps{a:02d}-{b:02d}.mp4"


def _longos_do_dia(est, o, lang):
    """ORDEM DA DONA (23/10), por dia e por canal: (1) completo em retrato do capítulo N, (2) o MESMO capítulo em
    16:9, (3) compilado 16:9 do cap 1 ao N, (4) Shorts, (5) Shorts de resumo. N = o último capítulo cujo completo já
    subiu no canal. Devolve o que falta de (2) e (3), em ordem: [("avulso", N, N), ("compilado", de, N)].
    Antes era "compilado com 2 caps e depois a cada 3" e o 16:9 do capítulo não subia sozinho. N == de: o avulso
    já é o compilado. pt: longo_pt_desde (22/10, não repetir o que saiu no canal advertido) continua valendo."""
    c = cfg()
    postados = _caps_postados(est, o, lang)
    if not c.get("longo", True) or not postados:
        return []
    n, de, chave = max(postados), o["de"], f"{o['slug']}|{lang or 'pt'}"
    itens = []
    if est.get("_longo_cap_postado", {}).get(chave, 0) < n:
        itens.append(("avulso", n, n))
    desde = None if lang else c.get("longo_pt_desde")
    if n > de and est.get("_longo_postado", {}).get(chave, 0) < n - de + 1 and not (desde and de < desde):
        itens.append(("compilado", de, n))
    return itens


DRIVE_HIPER = "manhwa-drive:videos-backup/hipercool/videos"
RCLONE = r"D:\tools\rclone.exe"


def _do_drive(arquivos):
    """Traz do Drive os arquivos que o backup tirou do PC (dona 23/10: "os grandes que o compilado precisa podem subir
    pro Drive e ser pegos de volta na hora de fazer o compilado"). Mesmo caminho relativo a workspace/videos. Falhar
    aqui só deixa faltando (o compilado espera, como antes)."""
    base = PROJECT / "workspace" / "videos"
    for f in arquivos:
        if f.exists():
            continue
        try:
            rel = f.relative_to(base).as_posix()
            r = subprocess.run([RCLONE, "copyto", f"{DRIVE_HIPER}/{rel}", str(f), "--retries", "3"],
                               capture_output=True, text=True, timeout=3600, creationflags=0x08000000)
            log(f"  trouxe do Drive {rel}: {'ok' if f.exists() else 'não achou (rc ' + str(r.returncode) + ')'}")
        except Exception as e:  # noqa: BLE001
            log(f"  trazer do Drive {f.name} falhou: {type(e).__name__}: {e}")


JANELA_LOCAL = PROJECT / "workspace" / "janela_local.json"
JANELA_N = 3  # capítulos por língua que ficam no PC (dona 23/10: "só os mais necessários"); config "janela_local"
JANELA_APERTO_GB = 10  # D: abaixo disso: a janela cai pra 1 (medida de aperto)
NO_DRIVE = "_NO_DRIVE.txt"  # o backup_drive deixa este aviso na pasta que mandou pro Drive


def _janela_do_canal(est, lang, n):
    """[(obra, capNN)] que a postagem desse canal vai usar: os que já têm o completo no canal e ainda cortam Shorts, e
    os n próximos completos na ordem e com os pulos do postar_pt/postar_idiomas (nudez não conta na vaga).
    29/10: antes eram os n primeiros pendentes — em id o cap01 (só faltava Short) ocupava a vaga e o próximo
    completo (cap03) podia estar no Drive."""
    out = []
    for k, o, num, _p in capitulos():
        e = est.get(k) or {}
        if lang == "pt":
            rel, completo, fim = e.get("video"), e.get("pt_completo_em"), e.get("pt_completo_em") and e.get("pt_shorts_ok")
            postavel = e.get("situacao") in ("pronto", "revisar", "revisar_pendente")
        else:
            li = (e.get("idiomas") or {}).get(lang) or {}
            rel, completo, fim, postavel = li.get("video"), li.get("completo_em"), li.get("postado"), True
        if not rel or fim:
            continue
        if completo:
            out.append((o["slug"], f"cap{num:02d}"))
        elif postavel and n > 0:
            if _nudez(rel):  # a postagem pula este, então não ocupa a vaga
                if lang == "pt":  # pt guarda o caminho do normal: com a censurada no Drive o _nudez não a acha
                    out.append((o["slug"], f"cap{num:02d}"))
                continue
            out.append((o["slug"], f"cap{num:02d}"))
            n -= 1
    return out


def _janela_local(est):
    """Dona 23/10: o estoque (capítulo pronto que vai demorar a sair) fica no Drive; no PC só os JANELA_N próximos de
    cada língua. Traz do Drive a pasta <obra>/capNN/<lang> que entrou na janela (só se tem o aviso NO_DRIVE: sem
    chamada ao Drive à toa) e grava a janela em workspace/janela_local.json, que o backup_drive lê pra saber o que
    pode subir. Falhar aqui não para a rodada."""
    try:
        c = cfg()
        # dona 23/10: "se apertar, podemos diminuir pra só os do dia: em vez de deixar 3, deixar só 1". config
        # fila.json "janela_local" (padrão 3); com o D: abaixo de JANELA_APERTO_GB livres cai sozinho pra 1
        n = int(c.get("janela_local", JANELA_N))
        livre_gb = shutil.disk_usage("D:\\").free / 1e9
        if livre_gb < JANELA_APERTO_GB and n > 1:
            log(f"  janela: D: com {livre_gb:.1f} GB livres (< {JANELA_APERTO_GB}) — só o próximo capítulo de cada língua no PC")
            n = 1
        manter = []
        for lang in ["pt"] + [l for l, i in c["idiomas"].items() if i.get("ativo", True)]:
            manter += [(obra, cap, lang) for obra, cap in _janela_do_canal(est, lang, n)]
        for obra, cap, lang in manter:
            pasta = VIDEOS / obra / cap / lang
            if (pasta / NO_DRIVE).exists():
                rel = pasta.relative_to(VIDEOS).as_posix()
                r = subprocess.run([RCLONE, "copy", f"{DRIVE_HIPER}/{rel}", str(pasta), "--retries", "3"],
                                   capture_output=True, text=True, timeout=3600, creationflags=0x08000000)
                if r.returncode == 0 and any(pasta.rglob("*.mp4")):
                    (pasta / NO_DRIVE).unlink(missing_ok=True)
                    log(f"  janela: {rel} voltou do Drive (vai sair em breve)")
                elif r.returncode == 3 and any(pasta.rglob("*.mp4")):
                    # 29/10: rc 3 = a pasta não existe no Drive: o backup marcou antes de subir e o envio falhou, então
                    # nada dela saiu do PC (cap12 pt tentou a cada 20 min o dia todo)
                    (pasta / NO_DRIVE).unlink(missing_ok=True)
                    log(f"  janela: {rel} nunca chegou ao Drive e continua no PC — aviso tirado")
                else:
                    log(f"  janela: {rel} não voltou do Drive (rc {r.returncode}); tenta na próxima rodada")
        JANELA_LOCAL.write_text(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "n": n,
                                            "manter": [list(x) for x in manter]}, ensure_ascii=False), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log(f"  janela local falhou: {type(e).__name__}: {e}")


def compilados_do_dia(est, maximo=2):
    """Produção do 16:9 que a postagem do dia pede (_longos_do_dia): o avulso capsNN-NN e o compilado de..N. Com os
    capNN.mp4 prontos é só COLAR (hiper-longo --compilar sem --refazer: concat -c copy + abertura de voz e CTA de
    ~10 s; não entra na fila_render, dono 17/10) — minutos. capNN.mp4 faltando: quem renderiza é o longo()."""
    c = cfg()
    if not c.get("longo", True) or limitador.restante("render"):
        return
    feitos = 0
    for o in c["obras"]:
        for lang in [None] + [l for l, i in c["idiomas"].items() if i.get("ativo", True)]:
            for tipo, a, b in _longos_do_dia(est, o, lang):
                arq = _longo_arq(o, lang, a, b)
                segs = [arq.parent / f"cap{n:02d}.mp4" for n in range(a, b + 1)]
                _do_drive(segs)  # 23/10: capNN.mp4 já postado pode estar só no Drive (backup_drive.hipercool_postados)
                if not all(s.exists() for s in segs) or any(_seg_velho(est, o, lang, n, estrito=True)
                                                            for n in range(a, b + 1)):
                    continue  # falta capNN.mp4 (ou o do dia é velho): o longo() renderiza (pesado, pela fila_render)
                if arq.exists() and arq.stat().st_mtime >= max(s.stat().st_mtime for s in segs):
                    continue  # já colado e mais novo que os capítulos
                logf = PROJECT / "logs" / f"fila_longo_{o['slug']}{'_' + lang if lang else ''}.log"
                with open(logf, "a", encoding="utf-8") as fh:
                    rc = subprocess.run([PY, str(PROJECT / "bin" / "hiper-longo.py"), "--obra", o["slug"],
                                         "--caps", f"{a}-{b}", "--compilar", *(["--idioma", lang] if lang else [])],
                                        cwd=PROJECT, env=ENV, stdout=fh, stderr=subprocess.STDOUT).returncode
                if rc or not arq.exists():
                    limitador.falhou("render", f"16:9 {tipo} {a}-{b} {lang or 'pt'}")
                    avisar(f"falhou o 16:9 {tipo} caps {a}-{b} de {o['titulo']} {lang or 'pt'} (ver {logf.name})")
                    return
                log(f"  16:9 {tipo} {lang or 'pt'} de {o['titulo']}: {arq.name} pronto pra postar")
                feitos += 1
                if feitos >= maximo:
                    return


def _canal_longos_pt():
    """29/10 (dona): completo e 16:9 em pt vão pro canal_pt_longos; os Shorts ficam no canal_pt."""
    c = cfg().get("canal_pt_longos")
    return ["--canal", c] if c else []


def _postar_longo_da_vez(est, lang, canal):
    """Sobe o próximo 16:9 da ordem do dia no canal (avulso do cap N, depois o compilado de..N) se o arquivo já
    existe. "postou" | "nada" (não há, ou ainda não está pronto: os Shorts seguem) | "parar" (erro/cota no canal)."""
    for o in cfg()["obras"]:
        chave = f"{o['slug']}|{lang or 'pt'}"
        for tipo, a, b in _longos_do_dia(est, o, lang):
            arq = _longo_arq(o, lang, a, b)
            if not arq.exists():
                log(f"  {lang or 'pt'}: 16:9 {tipo} caps {a}-{b} ainda não existe (a produção monta); Shorts seguem")
                break  # o compilado não passa na frente do avulso
            extra = ["--longo", o["slug"], "--longo-caps", f"{a}-{b}"] + (["--canal", canal, "--idioma", lang]
                                                                          if lang else _canal_longos_pt())
            resumo, _ = _postar(arq, extra)
            m = re.search(r"longo=(\w+)", resumo)
            st = m.group(1) if m else ""
            if st in ("ok", "ja"):
                if tipo == "avulso":
                    est.setdefault("_longo_cap_postado", {})[chave] = b
                else:
                    est.setdefault("_longo_postado", {})[chave] = b - a + 1
                gravar_estado(est)
                if st == "ok":
                    avisar(f"16:9 {tipo} caps {a}-{b} de {o['titulo']} postado em {lang or 'pt'}")
                    return "postou"
                continue  # já estava no ar: vai pro próximo da ordem
            if st in ("cota", "limite", "morto", "suspenso", "parado"):
                return "parar"
            if re.search(r"=(erro|timeout)", resumo):
                limitador.falhou("youtube", f"longo {lang or 'pt'}: {resumo}")
                return "parar"
            break  # nudez (segura este vídeo), faltando ou outro: os Shorts seguem
    return "nada"


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
    if e.get("refazer"):  # roteiro novo (o vídeo antigo já foi postado em outro canal)
        cmd.append("--force-llm")
    try:  # marca do scan (BLACKOUTCOMICS.COM) fora dos painéis antes do render; originais em <pasta>/_originais
        import marca_scan
        n_marca = len(marca_scan.limpar_pasta(pasta))
        if n_marca:
            log(f"  marca do scan tirada de {n_marca} painéis de {pasta.name}")
    except Exception as ex:  # noqa: BLE001 — sem limpeza o render segue com a marca
        log(f"  [!] marca do scan não tirada ({str(ex)[:120]})")
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
    e.pop("refazer", None)
    e.update(video=m.group(1), render="ok", fim_render=datetime.now().isoformat(timespec="seconds"))
    e.update(avaliar_censurado(VIDEOS / m.group(1)))
    if e.get("situacao") in ("pronto", "compilado") and revisar_pronto(e, pasta, titulo):
        gravar_estado(est)
        return renderizar(chave, obra, n, pasta, est)  # 2ª e última vez, com o fosco forçado nos painéis
    gravar_estado(est)
    avisar(f"{titulo} pronto ({e['situacao']}; censura {e.get('frac_censura', 0):.0%} do tempo)")
    return True


def revisar_pronto(e, pasta, titulo):
    """Análise do vídeo censurado PRONTO (bin/revisao_video.py) — criada em 16/10, depois que o canal pt levou
    advertência do YouTube por nudez no compilado caps 1-11 e ninguém tinha assistido. Devolve True = renderizar
    de novo.
      ok          -> segue (situacao inalterada);
      reprovado   -> 1ª vez: fosco forçado nos painéis dos trechos (censura_visual.forcar_fosco) e True;
                     2ª vez, ou trecho sem painel (abertura/meme): situacao "revisar" + Telegram — só o dono libera
                     (python bin/revisao_video.py --liberar <video>);
      incompleto  -> Gemini sem resposta: situacao "revisar_pendente"; revisar_pendentes() tenta de novo depois.
    Postar sem veredito "ok" é impossível de qualquer jeito: o postar_hipercool confere antes de subir."""
    import postar_hipercool as ph
    import revisao_video
    censura_visual = revisao_video.modulo("censura_visual")  # o do postador tem o mesmo nome (ver modulo())
    cens = ph.achar_censurado(VIDEOS / e["video"])
    if not cens:
        return False
    v = revisao_video.revisar(cens)
    e["revisao"] = {"status": v["status"], "segundos": [p["t"] for p in v["problemas"]][:40],
                    "paineis": v["paineis"], "em": v["em"]}
    if v["status"] == "ok":
        e.pop("revisao_refeito", None)
        if e.get("situacao") in ("revisar", "revisar_pendente"):
            e["situacao"] = e.pop("situacao_antes_revisao", "pronto")
        return False
    if e.get("situacao") not in ("revisar", "revisar_pendente"):
        e["situacao_antes_revisao"] = e["situacao"]
    if v["status"] == "incompleto":
        e["situacao"] = "revisar_pendente"
        return False
    if "clip_paineis" not in ph.ler_meta(cens) and not e.get("revisao_antigo"):
        # vídeo de antes de 16/10 (sem o mapa clip->painel): a censura de hoje já corrige boa parte do que ele
        # mostra; renderiza de novo com o código novo antes de forçar fosco em qualquer painel (uma vez só)
        e["revisao_antigo"], e["situacao"] = True, "revisar"  # não posta enquanto refaz
        avisar(f"{titulo}: vídeo antigo reprovado na análise ({len(v['problemas'])} quadro(s) com nudez); "
               f"renderizando de novo com a censura nova.")
        return True
    paineis = [pasta / nome for nome in v["paineis"] if (pasta / nome).exists()]
    if paineis and not e.get("revisao_refeito"):
        for p in paineis:
            censura_visual.forcar_fosco(p, f"análise do vídeo pronto: {cens.name}")
        e["revisao_refeito"], e["situacao"] = 1, "revisar"  # não posta enquanto refaz
        avisar(f"{titulo}: a análise do vídeo pronto achou nudez em {len(v['problemas'])} quadro(s) "
               f"({', '.join(v['paineis'])}). Fosco forçado nesses painéis; renderizando de novo.")
        return True
    # 2ª reprovação: NÃO renderiza de novo (seria laço), mas MARCA os painéis mesmo assim — senão o
    # que a 2ª análise achou se perde e a próxima renderização do capítulo repete o mesmo erro.
    # Caso real (cap 3, 16/10): a 1ª análise marcou 11 painéis, a 2ª reprovou outros 4 (014, 066,
    # 086, 100) e nenhum deles entrou na lista; rodar o capítulo de novo traria os mesmos quadros.
    novos = [p for p in paineis if not censura_visual.forcado(p)]
    for p in novos:
        censura_visual.forcar_fosco(p, f"2ª análise do vídeo pronto: {cens.name}")
    e["situacao"] = "revisar"
    folha = cens.with_name(cens.stem + ".revisao.jpg")
    avisar(f"{titulo} NÃO vai ser postado: a análise do vídeo pronto ainda acha nudez aos "
           f"{', '.join(f'{t:.0f}s' for t in e['revisao']['segundos'][:10])} (quadros em {folha.name}). "
           + (f"{len(novos)} painel(is) marcado(s) pra sair em fosco na próxima renderização. "
              if novos else "")
           + f"Se for engano: python bin/revisao_video.py --liberar \"{cens}\"")
    return False


def revisar_pendentes(est):
    """Capítulos parados na análise do vídeo pronto: 'revisar_pendente' (Gemini não respondeu) tenta de novo;
    'revisar' volta a 'pronto' se o dono liberou (veredito ok gravado). Também analisa UM capítulo 'pronto' que
    foi renderizado antes da análise existir (por rodada: cada análise leva ~10 min)."""
    import revisao_video
    import postar_hipercool as ph
    antigo_feito = False
    for chave, obra, n, pasta in capitulos():
        e = est.get(chave, {})
        if not e.get("video"):
            continue
        if e.get("situacao") in ("pronto", "compilado") and not e.get("revisao") and not antigo_feito:
            antigo_feito = True
            if revisar_pronto(e, pasta, f"{obra['titulo']} — Capítulo {n}"):
                gravar_estado(est)
                renderizar(chave, obra, n, pasta, est)
            gravar_estado(est)
            continue
        if e.get("situacao") not in ("revisar", "revisar_pendente"):
            continue
        cens = ph.achar_censurado(VIDEOS / e["video"])
        if e["situacao"] == "revisar" and not (cens and revisao_video.aprovado(cens)[0]):
            continue  # esperando o dono (ou um render novo)
        titulo = f"{obra['titulo']} — Capítulo {n}"
        if revisar_pronto(e, pasta, titulo):
            gravar_estado(est)
            renderizar(chave, obra, n, pasta, est)
        gravar_estado(est)


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
def _nudez(rel):
    """A análise do vídeo pronto achou nudez neste render (veredito "reprovado" do mesmo arquivo)? Dono 19/10:
    esse vídeo não sobe e a fila passa pro próximo; volta quando o render novo passar ou o dono liberar."""
    import postar_hipercool as ph
    import revisao_video
    cens = ph.achar_censurado(video_do_estado(rel))
    # 29/10: no Drive (estoque) o motivo é "arquivo no Drive, análise: reprovado" — antes passava como sem nudez
    return bool(cens) and bool(re.search(r"análise:? reprovado", revisao_video.aprovado(cens)[1]))


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
    if not _pt_ligado(cfg()):
        log(f"  postagem em pt SEGURADA (config/fila.json postar_pt=false): {cfg().get('_postar_pt_motivo', '')}")
        return
    if limitador.restante("youtube"):
        log(f"  youtube em pausa por mais {limitador.restante('youtube') // 60} min")
        return
    hoje = datetime.now().date().isoformat()
    # regra do dono (18/10): nenhum canal fica um dia sem postagem — capítulo parado na análise ou sendo refeito
    # sobe com o vídeo que já tem, e a série não trava mais nele. Exceção (dono 19/10): nudez achada fica de fora
    prontos = [(k, est[k]) for k, *_ in capitulos()
               if est.get(k, {}).get("situacao") in ("pronto", "revisar", "revisar_pendente") and est[k].get("video")
               and not _nudez(est[k]["video"])]
    ordem = [k for k, *_ in capitulos()]
    trava = len(ordem)
    if not any(e.get("pt_completo_em", "")[:10] == hoje for _, e in prontos):
        for k, e in prontos:
            if ordem.index(k) > trava:
                break  # série em ordem: não posta o seguinte antes do capítulo que está sendo refeito
            if not e.get("pt_completo_em"):
                resumo, _ = _postar(video_do_estado(e["video"]), ["--no-shorts", *_canal_longos_pt()])
                if re.search(r"completo=(ok|ja)", resumo):
                    e["pt_completo_em"] = datetime.now().isoformat(timespec="seconds")
                    gravar_estado(est)
                    avisar(f"postado o completo de {k}")
                elif "completo=nudez" in resumo:
                    continue  # a análise achou nudez agora: tenta o próximo capítulo
                elif re.search(r"completo=(cota|limite)", resumo):
                    return
                elif "completo=" in resumo:
                    limitador.falhou("youtube", resumo)
                    return
                break
    # Shorts do pt: 1 por rodada, no horário de pico do Brasil, se config/fila.json trouxer
    # "postagem_pt". Sem ela, continua como era (despeja o que couber na cota). 16/10: as 8 partes
    # do cap 1 subiram entre 05:27 e 06:09 da madrugada, uma atrás da outra, porque só as línguas
    # tinham pico e intervalo.
    pt_cfg = cfg().get("postagem_pt")
    extra_shorts = []
    if pt_cfg:
        info_pt = {**pt_cfg, "canal": cfg().get("canal_pt", "")}
        pode, motivo = _pode_postar(info_pt)
        if not pode:
            log(f"  Shorts em pt: espera — {motivo}")
            return
        log(f"  Shorts em pt: {motivo}")
        extra_shorts = ["--max-novos", "1"]
    # 23/10 (ordem da dona): depois do completo, o 16:9 do mesmo capítulo e o compilado 1..N; Shorts com o que sobrar
    if _postar_longo_da_vez(est, None, None) != "nada":
        return
    for k, e in prontos:
        if e.get("pt_completo_em") and not e.get("pt_shorts_ok"):
            resumo, _ = _postar(video_do_estado(e["video"]), ["--no-completo", *extra_shorts])
            if re.search(r"=(cota|limite)", resumo):
                return
            if re.search(r"=(erro|timeout)", resumo):
                limitador.falhou("youtube", resumo)
                return
            if resumo and not re.search(r"=(ensaio|cota|limite|erro|timeout|nao_aprovado|nudez)|faltam=", resumo):
                e["pt_shorts_ok"] = datetime.now().isoformat(timespec="seconds")
                gravar_estado(est)
                avisar(f"todos os Shorts de {k} postados")
            if extra_shorts and "=ok" in resumo:
                return


PLACAR = Path(r"D:\postador-de-videos\_analise\aprendizado_global.json")


def _ordem_linguas(c):
    """[(língua, info)] na ordem do PLACAR COMUM (views em 48 h por idioma, notificar_telegram.medir_48h): a que dá view
    renderiza primeiro (18/10, unificação: "o que dá view ganha a vez"). Sem dados (< 3 medidas) fica no meio, pra
    continuar sendo testada; empate mantém a ordem do fila.json. Nenhuma língua é desligada por isto."""
    langs = list(c["idiomas"].items())
    try:
        p = json.loads(PLACAR.read_text(encoding="utf-8")).get("por_idioma") or {}
    except (OSError, ValueError):
        return langs

    def nota(lang):
        x = p.get(lang) or {}
        if x.get("n", 0) < 3:
            return (1, 0, 0)
        return (2 if (x.get("pct_1000") or x.get("mediana")) else 0, x.get("pct_1000", 0), x.get("mediana", 0))
    return sorted(langs, key=lambda li: nota(li[0]), reverse=True)


def idiomas(est, max_renders=None):
    """Versões nas outras línguas dos capítulos prontos em pt (15/10, dono: não esperam mais o pt ser postado).
    max_renders: quantas línguas renderizar neste ciclo (None = todas).

    Só renderiza — a postagem fica com postar_idiomas() que o ciclo chama a cada 20 min."""
    c = cfg()
    renders = 0
    for k, obra, n, pasta in capitulos():
        e = est.get(k, {})
        if e.get("situacao") != "pronto":
            continue
        for lang, info in _ordem_linguas(c):
            if not info.get("ativo", True):
                continue
            li = e.setdefault("idiomas", {}).setdefault(lang, {})
            if li.get("postado") or li.get("video") or li.get("pc2"):
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
                rc = subprocess.run(cmd, cwd=PROJECT, env=_env_render(_marca_do_idioma(info)),
                                    stdout=fh, stderr=subprocess.STDOUT).returncode
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
    # a política (intervalo, teto do dia, parado_h) vem da config da língua quando ela traz a sua;
    # senão vale a global postagem_idiomas. O pt usa isso pra ter pico e intervalo como as línguas.
    p = {**cfg().get("postagem_idiomas", {}), **{c: info[c] for c in ("intervalo_h", "max_dia", "parado_h")
                                                 if c in info}}
    try:  # 23/10 (dona): o teto do dia é o REAL do canal no postador (política + rampa, apertado pelo cadastro),
        p["max_dia"] = int(politica.teto_canal(canal))  # não o número fixo daqui (pt dizia 10, línguas 3; real 3 e 4)
    except Exception:  # noqa: BLE001 — sem o postador, vale o da config
        pass
    agora_la = datetime.now(ZoneInfo(info.get("fuso", "UTC")))
    ups = _uploads_canal(info["canal"])
    # 22/10: "último upload" é o último JÁ PUBLICADO. Um agendado pro futuro (ex.: Short do parceiro com
    # publish_at pra daqui a dias no mesmo canal) fazia "agora - ups[-1]" dar negativo, que é sempre menor
    # que o intervalo, e o canal ficava preso até a data agendada (as 6 línguas pararam de 18 a 22/10:
    # "último há -144 h" no fila_postagem.log). O teto do dia continua contando os agendados de hoje.
    passados = [u for u in ups if u <= agora_la]
    if not passados or agora_la - passados[-1] > timedelta(hours=p.get("parado_h", 24)):
        return True, "canal parado, sai já"
    if agora_la - passados[-1] < timedelta(hours=p.get("intervalo_h", 2)):
        return False, f"último há {(agora_la - passados[-1]).total_seconds() / 3600:.1f} h"
    hoje = sum(1 for u in ups if u.astimezone(agora_la.tzinfo).date() == agora_la.date())
    if hoje >= p.get("max_dia", 3):
        return False, f"já subiram {hoje} hoje"
    ini, fim = info.get("pico", [17, 22])
    if not ini <= agora_la.hour < fim:
        return False, f"fora do pico ({agora_la:%H:%M} lá, pico {ini}h-{fim}h)"
    return True, f"pico ({agora_la:%H:%M} lá)"


def postar_idiomas(est):
    """Uma subida por canal de língua por rodada, quando _pode_postar libera. Capítulos em ordem. Por dia (dia
    de lá): o completo do próximo capítulo primeiro (1 por dia); o resto da cota vai pros Shorts dos capítulos
    que já têm o completo (postar_hipercool --max-novos 1 retoma de onde parou)."""
    from zoneinfo import ZoneInfo
    c = cfg()
    for lang, info in c["idiomas"].items():
        if not info.get("ativo", True) or limitador.restante("youtube"):
            continue
        todos = [(k, est[k]["idiomas"][lang]) for k, *_ in capitulos()
                 if ((est.get(k) or {}).get("idiomas") or {}).get(lang, {}).get("video")]
        pendentes = [(k, li) for k, li in todos if not li.get("postado") and not _nudez(li["video"])]
        hoje = datetime.now(ZoneInfo(info.get("fuso", "UTC"))).date().isoformat()
        # 30/10 (ronda da noite): o cap 3 em inglês não tem versão _CENSURADO e o postar_hipercool recusa sem RESUMO —
        # a fila tentou o mesmo vídeo 38x (de 20 em 20 min) e o canal ficou sem nada. Marcado = pula pro próximo
        # capítulo até o render censurado existir (achar_censurado acha = volta sozinho).
        import postar_hipercool as ph
        sem_completo = [(k, li) for k, li in pendentes if not li.get("completo_em")
                        and not (li.get("sem_censura") and not ph.achar_censurado(video_do_estado(li["video"])))]
        com_completo = [(k, li) for k, li in pendentes if li.get("completo_em")]
        tz = ZoneInfo(info.get("fuso", "UTC"))

        def _dia_la(x):  # completo_em é hora do PC; o "hoje" é o dia de lá (23/10: hindi subia 2 completos no mesmo dia)
            try:
                return datetime.fromisoformat(x).astimezone(tz).date().isoformat()
            except (TypeError, ValueError):
                return ""
        vez_completo = bool(sem_completo) and not any(_dia_la(li.get("completo_em")) == hoje for _k, li in todos)
        longos = any(_longos_do_dia(est, o, lang) for o in c["obras"])
        if not (vez_completo or longos or com_completo):
            continue  # completo de hoje já subiu e não há 16:9 nem Short pendente
        pode, motivo = _pode_postar(info)
        if not pode:
            log(f"  {info['nome']}: espera — {motivo}")
            continue
        if vez_completo:
            (k, li), extra, oque = sem_completo[0], ["--no-shorts"], "o completo"
        else:  # 23/10 (ordem da dona): 16:9 do capítulo do dia, depois o compilado 1..N, e só então Shorts
            r = _postar_longo_da_vez(est, lang, info["canal"])
            if r != "nada" or not com_completo:
                continue
            (k, li), extra, oque = com_completo[0], ["--no-completo", "--max-novos", "1"], "1 Short"
        log(f"  {info['nome']}: sobe {oque} de {k} — {motivo}")
        resumo, saida = _postar(video_do_estado(li["video"]), ["--canal", info["canal"], "--idioma", lang, *extra])
        if "não há versão censurada" in saida:
            li["sem_censura"] = datetime.now().isoformat(timespec="seconds")
            gravar_estado(est)
            avisar(f"{info['nome']}: {k} sem versão censurada — pulado até renderizar com --censura")
            continue
        if "=morto" in resumo:  # problema só deste canal (login/pausa): não pausa a postagem dos outros
            avisar(f"canal {info['nome']} recusou o upload: {resumo[:120]}")
            continue
        if re.search(r"=(erro|timeout|suspenso|parado)", resumo):
            limitador.falhou("youtube", f"{lang}: {resumo}")
            avisar(f"falhou a postagem {info['nome']} de {k}: {resumo[:120]}")
            continue
        if "--no-shorts" in extra:
            m = re.search(r"completo=(ok|ja)", resumo)
            if m:  # "ja" (subiu antes desta regra): marca sem contar como o completo de hoje
                li["completo_em"] = datetime.now().isoformat(timespec="seconds") if m.group(1) == "ok" else "ja"
                gravar_estado(est)
        elif "RESUMO:" in saida and "faltam=" not in resumo \
                and not re.search(r"=(cota|limite|nao_aprovado|reservado|nudez)", resumo):
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


def _controle(etapa):
    """Liga/desliga único dos projetos (D:\\video-fila\\controle.py): (ligado, motivo). Sem o controle = ligado."""
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import controle
        return controle.ligado("hipercool", etapa)
    except Exception:  # noqa: BLE001
        return True, ""


def postagem(manual=False, so_pt=False):
    """Postagem (tarefa HipercoolPostagem, 20 min). ORDEM DA DONA (23/10), por dia e por canal: completo retrato do
    cap N > o mesmo cap em 16:9 > compilado 16:9 de 1 a N > Shorts (os de resumo vêm do short_resumo, que só gera).
    Cada passo respeita pico/intervalo/teto (_pode_postar) e a trava de nudez; o que não está pronto não trava os
    Shorts (_postar_longo_da_vez dentro de postar_pt/postar_idiomas)."""
    if POSTAGEM_DESLIGADA.exists() and not manual:
        log("postagem desligada (config/POSTAGEM_DESLIGADA.json)")
        return
    ok, motivo = _controle("postagem")
    if not ok and not manual:
        log(f"postagem desligada: {motivo}")
        return
    if not _pegar_lock(LOCK_POSTAGEM):
        return
    try:
        if _subindo_agora():
            log("tem upload do hipercool em andamento; fica pra próxima rodada")
            return
        est = ler_estado()
        _janela_local(est)  # 23/10: o próximo a sair pode estar no Drive (estoque)
        postar_pt(est)
        if not so_pt:
            postar_idiomas(est)
        # acabamento no Studio do que já subiu (tela final, comentário fixado, teste A/B, vídeo relacionado dos
        # Shorts); pendente (canal em verificação, vídeo agendado) repete a cada 3 h
        try:
            import postar_hipercool as ph
            ph.rodar_extras(max_videos=3)
        except Exception as e:  # noqa: BLE001
            log(f"  extras do Studio falharam: {str(e)[:150]}")
        try:  # mede o que rende (retenção/CTR no Studio) 1x por dia e alimenta os rodízios (bin/metricas.py)
            import metricas
            metricas.rodar()
        except Exception as e:  # noqa: BLE001
            log(f"  métricas do Studio falharam: {str(e)[:150]}")
    finally:
        LOCK_POSTAGEM.unlink(missing_ok=True)


def pc2_ciclo(disparar=True):
    """PC2 só renderiza LÍNGUAS: traz o vídeo pronto de lá, depois dispara a próxima língua pendente. Pega as
    línguas em ordem inversa à do idiomas() do PC1, pros dois não pegarem a mesma. 19/10: a tarefa HipercoolPC2
    (20 min) só TRAZ (pc2-trazer, disparar=False); quem decide o que o PC2 faz é o controlador geral
    (D:\\video-fila\\controlador.py), que chama `fila.py pc2` quando a vez do PC2 é das línguas."""
    if PC2_DESLIGADO.exists() or not _pegar_lock(LOCK_PC2):
        return
    try:
        import pc2
        if not pc2.no_ar():
            log("pc2: fora do ar (ssh não respondeu)")
            return
        est = ler_estado()
        caps = capitulos()
        ocupado = pc2.rodando()
        for k, obra, n, pasta in caps:
            for lang, li in (est.get(k, {}).get("idiomas") or {}).items():
                if not li.get("pc2"):
                    continue
                video = pc2.video_final(pc2.log_render(k, lang))
                if video and pc2.trazer(video, Path(pasta).name, lang):
                    li.pop("pc2")
                    li["video"] = video
                    gravar_estado(est)
                    log(f"pc2: {k} {lang} pronto -> {video}")
                    avisar(f"PC2 terminou a versão {lang} de {k}")
                elif not video and (not ocupado or _marca_pc2_velha(li["pc2"])):
                    li.pop("pc2")
                    li["pc2_falhas"] = li.get("pc2_falhas", 0) + 1
                    gravar_estado(est)
                    log(f"pc2: {k} {lang} FALHOU (sem vídeo; log logs/pc2_{k}_{lang}.log no PC2)")
        if not disparar:
            return
        if ocupado:
            log("pc2: ocupado renderizando")
            return
        no_pc1 = _hipercool_no_pc1()
        if no_pc1:
            # Regra do dono (17/10, via sessão do parceiro): um projeto NÃO usa os 2 PCs ao mesmo tempo. Com o
            # hipercool renderizando no PC1, o PC2 fica pros outros projetos (parceiro, anime); a língua espera.
            log(f"pc2: hipercool já renderizando no PC1 ({no_pc1}); PC2 fica pros outros projetos")
            return
        with _vez_pc2():  # mede e dispara com a vez do PC2: o modo ocioso (anime/parceiro) não dispara junto
            livre, motivo = _pc2_livre_comum()
            if not livre:
                log(f"pc2: {motivo} (medidor comum dos 3 PCs — anime/parceiro lá contam)")
                return
            _pc2_disparar_lingua(est, caps)
    finally:
        LOCK_PC2.unlink(missing_ok=True)


def _marca_pc2_velha(marca, horas=24):
    """Marca de língua no PC2 sem vídeo no log há mais de `horas`: o render morreu lá (o pc2.rodando() pode ficar
    verdadeiro por outro render e a marca nunca saía) — conta como falha e a língua volta pra fila."""
    try:
        return (datetime.now() - datetime.fromisoformat(marca.get("desde"))).total_seconds() > horas * 3600
    except (AttributeError, TypeError, ValueError):
        return False


def faltantes():
    """Só o que falta dos capítulos já feitos: correções, línguas e compilado 16:9 (tempo_livre), sem capítulo novo.
    Dono 19/10: o hipercool tem vídeo demais pra 1 canal; capítulo novo só pelo `ciclo`, que o controlador geral
    (D:\\video-fila\\controlador.py) chama quando o Manhwa Noturno tem menos de 5 dias de estoque."""
    ok, motivo = _controle("producao")
    if not ok:
        log(f"faltantes: {motivo}")
        return
    if not _pegar_lock(LOCK):
        return
    try:
        if limitador.restante("render"):
            log(f"faltantes: render em pausa por mais {limitador.restante('render') // 60} min")
            return
        vivos = _renders_vivos()
        if vivos:
            log(f"faltantes: já tem render rodando (pid {', '.join(map(str, vivos))})")
            return
        est = ler_estado()
        revisar_pendentes(est)
        tempo_livre(est)
    finally:
        LOCK.unlink(missing_ok=True)


def _vez_pc2():
    import contextlib
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import fila_render
        return fila_render.vez("hipercool", "disparo de língua no PC2", espera_max_h=0.25, maquina="pc2")
    except Exception:  # noqa: BLE001
        return contextlib.nullcontext()


def _pc2_livre_comum():
    """Medidor ÚNICO dos 3 PCs (D:\\video-fila\\maquinas.py): antes o hipercool só via o hiper-pipeline dele no PC2 e
    disparava língua por cima de Short de parceiro/anime longo rodando lá."""
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import maquinas
        m = maquinas.medir("pc2")
        return bool(m.get("ocioso")), m.get("motivo", "")
    except Exception:  # noqa: BLE001 — sem o medidor comum, vale a checagem do próprio hipercool
        return True, ""


def _pc2_disparar_lingua(est, caps):
    """Dispara no PC2 a próxima língua pendente (ordem inversa à do PC1, pros dois não pegarem a mesma)."""
    import pc2
    c = cfg()
    for k, obra, n, pasta in caps:
        e = est.get(k, {})
        if e.get("situacao") != "pronto":
            continue
        for lang, info in reversed(_ordem_linguas(c)):
            li = e.setdefault("idiomas", {}).setdefault(lang, {})
            if (not info.get("ativo", True) or li.get("postado") or li.get("video") or li.get("pc2")
                    or li.get("pc2_falhas", 0) >= 2):
                continue
            if not pc2.sincronizar(Path(pasta).name):
                log(f"pc2: falhou a cópia pro PC2 ({k}); tenta na próxima rodada")
                return
            sk = e.get("skip", {})
            if pc2.disparar(k, lang, f"{obra['titulo']} — Capítulo {n}", Path(pasta).name,
                            sk.get("fim", 0), sk.get("inicio", 0)):
                li["pc2"] = {"desde": datetime.now().isoformat(timespec="seconds")}
                gravar_estado(est)
                log(f"pc2: renderizando {k} em {info['nome']}")
            else:
                log(f"pc2: não conseguiu disparar {k} {lang}")
            return
    log("pc2: nenhuma língua pendente")


def ciclo(com_idiomas=False):
    """Produção (tarefa HipercoolFila a cada 20 min): só renderiza, nunca espera postagem."""
    if DESLIGADA.exists() and not com_idiomas:  # o botão manual das línguas funciona com a fila desligada
        log("fila desligada (config/FILA_DESLIGADA.json)")
        return
    ok, motivo = _controle("producao")
    if not ok and not com_idiomas:
        log(f"fila desligada: {motivo}")
        return
    if not _pegar_lock(LOCK):
        return
    try:
        est = ler_estado()
        _janela_local(est)  # 23/10: traz do Drive o que entrou na janela e diz ao backup o que pode subir
        if com_idiomas:
            idiomas(est)
            return
        if limitador.restante("render"):
            log(f"render em pausa por mais {limitador.restante('render') // 60} min")
            return
        vivos = _renders_vivos()
        if vivos:  # 15/10: a tarefa parou (notebook foi pra bateria) mas o render filho continuou: não abre outro
            log(f"já tem render rodando (pid {', '.join(map(str, vivos))}); não abre outro")
            return
        revisar_pendentes(est)  # análise do vídeo pronto que ficou pendente ou foi liberada pelo dono
        caps = capitulos()
        prontos_nao_postados = sum(1 for k, *_ in caps
                                   if est.get(k, {}).get("situacao") == "pronto" and not est[k].get("pt_shorts_ok"))
        if prontos_nao_postados >= cfg()["adiantado"]:
            log(f"{prontos_nao_postados} capítulos prontos esperando postagem; não renderiza agora")
            tempo_livre(est)
            return
        for k, obra, n, pasta in caps:
            if est.get(k, {}).get("render") not in ("ok",):
                if est.get(k, {}).get("render") == "rodando" and _registrar_orfao(k, est):
                    break  # o render que ficou órfão terminou: aproveita o vídeo em vez de renderizar de novo
                renderizar(k, obra, n, pasta, est)
                break
        else:
            log("fila de capítulos terminada — adicione a próxima obra em config/fila.json")
            tempo_livre(est)
    finally:
        LOCK.unlink(missing_ok=True)


def _registrar_orfao(chave, est):
    """Render marcado 'rodando' cuja rodada da fila morreu (o Windows parou a tarefa) mas que terminou sozinho:
    registra o vídeo que ele fez (última linha "[OK] Vídeo final" do log, arquivo mais novo que o início)."""
    e = est.get(chave, {})
    logf = PROJECT / "logs" / f"fila_{chave}.log"
    try:
        finais = re.findall(r"\[OK\] Vídeo final: (\S+\.mp4)", logf.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return False
    if not finais:
        return False
    video = finais[-1]
    arq = video_do_estado(video)
    inicio = datetime.fromisoformat(e.get("inicio_render") or "2000-01-01T00:00:00")
    if not arq.exists() or datetime.fromtimestamp(arq.stat().st_mtime) < inicio:
        return False
    e.pop("refazer", None)
    e.update(video=video, render="ok", fim_render=datetime.fromtimestamp(arq.stat().st_mtime).isoformat(timespec="seconds"))
    e.update(avaliar_censurado(VIDEOS / video))
    gravar_estado(est)
    avisar(f"{chave}: o render que ficou sem a fila terminou — vídeo aproveitado ({e.get('situacao')})")
    return True


def _renders_vivos():
    """PIDs de hiper-pipeline.py rodando nesta máquina (render pesado: um por vez). Pega também o render que ficou
    órfão quando o Windows parou a tarefa da fila (ex.: notebook foi pra bateria) — sem isso a rodada seguinte via a
    trava de um processo morto e abria um 2º render do mesmo capítulo (cap 8, 15/10)."""
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Where-Object "
                        "{ $_.CommandLine -match 'hiper-pipeline\\.py' -and $_.ParentProcessId -notin "
                        "@(Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Where-Object "
                        "{ $_.CommandLine -match 'hiper-pipeline\\.py' } | ForEach-Object { $_.ProcessId }) } | "
                        "ForEach-Object { $_.ProcessId }"],
                       capture_output=True, text=True)
    return [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]


def _hipercool_no_pc1():
    """Texto curto do render do hipercool rodando NESTE PC (o PC1), ou "" se não há nenhum.
    Conta o hiper-pipeline local e qualquer vez do hipercool na fila comum (D:\\video-fila: o 16:9 também entra)."""
    if _renders_vivos():
        return "hiper-pipeline"
    try:
        sys.path.insert(0, r"D:\video-fila")
        import fila_render
        rod = [d for _p, d in fila_render._ler("rodando", 6) if d.get("projeto") == "hipercool"]
        return rod[0].get("rotulo", "fila_render") if rod else ""
    except Exception:  # noqa: BLE001 — sem a fila comum, vale só o hiper-pipeline local
        return ""


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
        idi = " ".join(f"{l}:{'ok' if v.get('postado') else ('render' if v.get('video') else ('pc2' if v.get('pc2') else '-'))}"
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
     "pc2": pc2_ciclo, "pc2-trazer": lambda: pc2_ciclo(disparar=False), "faltantes": faltantes,
     "ligar-pc2": lambda: ligar(TAREFA_PC2, "pc2", PC2_DESLIGADO, "PC2 (línguas)"),
     "desligar-pc2": lambda: desligar(TAREFA_PC2, PC2_DESLIGADO, "PC2 (línguas)"),
     "migrar-canal": migrar_canal}[cmd]()
