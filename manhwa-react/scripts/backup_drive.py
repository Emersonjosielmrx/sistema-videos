"""Backup no Google Drive (rclone, remoto manhwa-drive, pasta videos-backup) do que ja foi POSTADO ou NAO vai mais ser usado,
em todos os projetos (manhwa-react, hipercool, veo, historias-em-frames, recapd).

Quem foi postado onde vem do catalogo central (D:\\postador-de-videos\\bin\\catalogo.py), que tambem diz ao TikTok/Instagram
o que reaproveitar e baixa do Drive na hora de postar. So some do PC o que o rclone conferiu no Drive (tamanho + md5).
Midia vai; .json/.txt/.md sao copiados e ficam (registro, painel e comentarios leem). No Drive cada video vai para a ETAPA
do projeto (D:\\postador-de-videos\\bin\\etapas.py, 16/10): videos-backup/<projeto>/<N>_<rede>/<origem>/..., a ultima rede por
onde ja passou (youtube -> tiktok -> instagram); o TikTok/Instagram mudam de etapa quando postam. Os 2 PCs usam o mesmo Drive.
- postado: postagem mais recente ha mais de ESPERA_POSTADO (sem data = antiga), numa pasta do catalogo (filas ficam de fora)
- bruto do Veo (veo_videos_iniciais) que ja virou final, parado ha ESPERA_BRUTO: reaproveitavel, fica documentado no Drive
- nao usado: shorts/cortes/grandes do manhwa-react rejeitado na aprovacao ha ESPERA
Depois apaga cache regeneravel do work/ (wav, temas/*.mp4) de gravacao sem nada na fila e copias em output/ ja no Drive.

Uso: python scripts/backup_drive.py [--simular]     (agendado: tarefa BackupDriveVideos, scripts/backup_drive.bat)
"""
import argparse
import json
import os
import re
import shutil
import subprocess

_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, r"D:\postador-de-videos\bin")
from mr.common import load_config, load_json, log  # noqa: E402
import politica  # noqa: E402
import catalogo  # noqa: E402
import etapas  # noqa: E402
sys.path.append(r"D:\hipercool-materiais\bin")
import registro_drive  # noqa: E402  (25/10: o que sai fica anotado no _NO_DRIVE.md da própria pasta)

RCLONE = r"D:\tools\rclone.exe"
REMOTO = "manhwa-drive:"
DRIVE = REMOTO + "videos-backup"
ESPERA_POSTADO = timedelta(hours=2)  # 20/10 dono: postado vai logo pro Drive; 2 h = YouTube termina a checagem de direitos
ESPERA = timedelta(days=3)  # rejeitado na aprovacao e cache do work/
ESPERA_BRUTO = timedelta(days=14)
MIDIA = {".mp4", ".mkv", ".mov", ".webm", ".jpg", ".jpeg", ".png"}
TEXTO = {".json", ".txt", ".md"}
CACHE_WORK = {"raw.wav", "clean.wav", "final.wav", "grande_audio.wav"}
MANIFESTO = catalogo.MANIFESTO
RCLONE_LOG = RAIZ / "logs" / "backup_rclone.log"


def _ler(p):
    try:
        return load_json(p)
    except Exception:  # noqa: BLE001  (ausente ou quebrado = sem dado)
        return {}


def _item(f):
    """2026_x_p1_thumb.jpg -> 2026_x_p1 ; 2026_x__inovare_ru.mp4 -> 2026_x"""
    return re.sub(r"_thumb$", "", f.stem).split("__")[0]


def _reabertos(postados):
    """Stems da rede que vao ser repostados no canal certo (e ainda nao foram): ficam no PC."""
    reg = _ler(postados / "react" / "publicados.json")
    return {s for s, e in _ler(postados / "react" / "reabertos.json").items()
            if (reg.get(s) or {}).get("video_id") in (None, e.get("video_antigo"))}


def _imagens(f):
    """Capa/thumb e selo do mesmo item (X_thumb.jpg, X.png; thumb_v1.jpg na pasta de uma historia)."""
    historia = (f.parent / "postar.json").exists()
    return [m for m in f.parent.iterdir() if m.is_file() and m.suffix.lower() in MIDIA - catalogo.VIDEO
            and (m.stem.startswith(f.stem) or (historia and m.stem.startswith("thumb")))]


HIPER_ESTADO = Path(r"D:\hipercool-videos\workspace\fila_estado.json")
HIPER_VIDEOS = Path(r"D:\hipercool-videos\workspace\videos")


def _hipercool_em_uso():
    """Pastas <obra>\\<capNN>\\<língua> do hipercool cuja postagem ainda não acabou (pt sem pt_shorts_ok, língua sem
    'postado'): o completo sobe e os Shorts são cortados DELE depois, 1 por rodada no pico. 19/10: o backup levou o
    cap 1 de 5 línguas 3 dias depois do completo e os Shorts pararam com 'vídeo não encontrado'."""
    try:
        est = json.loads(HIPER_ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    out = set()
    for chave, e in est.items():
        m = re.match(r"^(.+)-(cap\d+)$", str(chave))
        if not m or not isinstance(e, dict) or not e.get("video"):
            continue
        pend = [] if e.get("pt_shorts_ok") else ["pt"]
        pend += [l for l, li in (e.get("idiomas") or {}).items() if isinstance(li, dict) and li.get("video")
                 and not li.get("postado")]
        for lang in pend:
            out.add(str((HIPER_VIDEOS / m.group(1) / m.group(2) / lang).resolve()).casefold() + "\\")
    return out


HIPER_MATERIAIS = Path(r"D:\hipercool-materiais")
HIPER_DIAS = 3  # 16:9 (longo/): o compilado do dia cola todos os capNN.mp4; sair logo = baixar de volta todo dia
HIPER_DIAS_VERTICAL = 2 / 24  # 29/10 (dona: "estamos guardando conteúdo postado?"): vertical e Shorts postados, 2 h


def hipercool_postados(agora):
    """23/10 (dona: "todos os vídeos do hipercool que postaram vão pro Drive; ocupam muito espaço; até os grandes que o
    compilado precisa podem subir e ser pegos de volta"). O catálogo só reconhecia 28 deles (23 GB ficavam no PC).
    Pelo fila_estado do hipercool: capítulo/Shorts de uma língua JÁ postados (pt: pt_completo_em + pt_shorts_ok; língua:
    postado) e o 16:9 (longo/: capNN.mp4 e compilados) de capítulo já postado. Só arquivo parado há HIPER_DIAS dias
    (16:9) ou HIPER_DIAS_VERTICAL (vertical e Shorts).
    Vai para videos-backup/hipercool/{videos,shorts}/<mesmo caminho>; o compilado baixa de volta (fila._do_drive)."""
    try:
        est = json.loads(HIPER_ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    em_uso = _hipercool_em_uso()
    postado = {}  # (obra, capNN, lang) -> True
    for chave, e in est.items():
        m = re.match(r"^(.+)-cap(\d+)$", str(chave))
        if not m or not isinstance(e, dict):
            continue
        cap = f"cap{int(m.group(2)):02d}"
        postado[(m.group(1), cap, "pt")] = bool(e.get("pt_completo_em") and e.get("pt_shorts_ok"))
        for lang, li in (e.get("idiomas") or {}).items():
            postado[(m.group(1), cap, lang)] = isinstance(li, dict) and bool(li.get("postado"))
    limite = agora.timestamp() - HIPER_DIAS * 86400
    limite_vert = agora.timestamp() - HIPER_DIAS_VERTICAL * 86400
    itens = []
    base = HIPER_MATERIAIS / "videos"
    for f in base.rglob("*.mp4"):
        rel = f.relative_to(base).parts
        if (f.stat().st_mtime > (limite if rel[0] == "longo" else limite_vert)
                or any(str(f.resolve()).casefold().startswith(p) for p in em_uso)):
            continue
        if rel[0] == "longo":  # longo/<obra>/[lang/]capNN.mp4 ou <obra>_capsAA-BB.mp4
            obra = rel[1]
            lang = rel[2] if len(rel) == 4 else "pt"
            m = re.match(r"cap(\d+)\.mp4$", f.name)
            ok = (not m) or postado.get((obra, f"cap{int(m.group(1)):02d}", lang), False)
        elif len(rel) >= 4:  # <obra>/capNN/<lang>/...
            ok = postado.get((rel[0], rel[1], rel[2]), False)
        else:
            ok = False
        if ok:
            itens.append((f, f"{DRIVE}/hipercool/videos/{'/'.join(rel)}"))
    sh = HIPER_MATERIAIS / "shorts_hipercool"
    for f in sh.rglob("*.mp4"):  # <obra>-capN[-lang]/...
        m = re.match(r"^(.+)-cap(\d+)(?:-(\w+))?$", f.relative_to(sh).parts[0])
        if m and f.stat().st_mtime <= limite_vert and postado.get((m.group(1), f"cap{int(m.group(2)):02d}", m.group(3) or "pt")):
            itens.append((f, f"{DRIVE}/hipercool/shorts/{f.relative_to(sh).as_posix()}"))
    return itens


HIPER_JANELA = Path(r"D:\hipercool-videos\workspace\janela_local.json")


def hipercool_estoque(agora, simular):
    """23/10 (dona: "capítulos que ainda vão demorar a ser postados vão pro Drive, deixando só os mais necessários").
    Capítulo pronto e AINDA NÃO postado, fora da janela (os N próximos de cada língua, gravados pelo fila._janela_local
    a cada rodada), sobe inteiro (<obra>/capNN/<lang>/**) e deixa o aviso _NO_DRIVE.txt na pasta: quando ele entra na
    janela, o fila traz de volta. Só sobe com segurança: janela gravada há menos de 2 h; completo ainda não subido no
    canal (o que já subiu corta Shorts dele); pt "pronto"/"compilado" (não "revisar": a dona revê) e já analisado
    (revisar_pendentes analisa 1 por rodada e travaria num mp4 ausente); parado há 1 dia.
    29/10 (dona: "o 16 não precisa, nem o 8 foi postado"): caíram as exigências de 16:9 feito e de línguas com vídeo
    — o hiper-longo e as línguas usam caches/painéis, não o mp4 vertical; só a postagem usa, e a janela traz antes."""
    try:
        jan = json.loads(HIPER_JANELA.read_text(encoding="utf-8"))
        est = json.loads(HIPER_ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    em = politica._dt(jan.get("em"))
    if not em or (agora - em).total_seconds() > 2 * 3600:
        log("backup: janela do hipercool velha ou ausente - estoque fica no PC")
        return []
    manter = {tuple(x) for x in jan.get("manter") or []}
    limite = agora.timestamp() - 86400
    itens = []
    for chave, e in est.items():
        m = re.match(r"^(.+)-cap(\d+)$", str(chave))
        if not m or not isinstance(e, dict):
            continue
        obra, cap = m.group(1), f"cap{int(m.group(2)):02d}"
        candidatos = []
        idi = e.get("idiomas") or {}
        if (e.get("situacao") in ("pronto", "compilado") and e.get("video") and not e.get("pt_completo_em")
                and e.get("revisao")):
            candidatos.append("pt")
        for lang, li in idi.items():
            if isinstance(li, dict) and li.get("video") and not li.get("postado") and not li.get("completo_em"):
                candidatos.append(lang)
        for lang in candidatos:
            if (obra, cap, lang) in manter:
                continue
            pasta = HIPER_VIDEOS / obra / cap / lang
            # só os .mp4 (o peso): json/capas/revisão ficam no PC (a fila lê)
            arqs = [f for f in pasta.rglob("*.mp4") if f.is_file()] if pasta.is_dir() else []
            if not arqs or max(f.stat().st_mtime for f in arqs) > limite:
                continue
            if not simular:
                (pasta / "_NO_DRIVE.txt").write_text(
                    "Estoque do hipercool no Drive (backup_drive.hipercool_estoque, 23/10): o fila.py traz de volta "
                    "quando este capítulo entrar nos próximos a sair.\n", encoding="utf-8")
            itens += [(f, f"{DRIVE}/hipercool/videos/{f.relative_to(HIPER_VIDEOS).as_posix()}") for f in arqs]
    return itens


def do_catalogo(cat, limite, limite_bruto, reab):
    """[(arquivo, caminho no Drive)] do que ja pode sair do PC, segundo o catalogo: o video na etapa do projeto conforme
    as redes onde ja saiu (etapas.destino), capa e selo na mesma pasta. As 2 versoes de uma historia ficam juntas, na
    etapa da mais adiantada; projeto so_no_fim (ms-energy) so sai depois da ultima rede (o postador dele usa o arquivo)."""
    finais = {v["nome"].casefold() for v in cat["videos"] if v["tipo"] == "final"}
    redes_pasta = {}
    for v in cat["videos"]:
        if v["projeto"] == "historias-em-frames" and v["no_pc"]:
            redes_pasta.setdefault(Path(v["caminho"]).parent, set()).update(p["plataforma"] for p in v["postagens"])
    itens = []
    em_uso = _hipercool_em_uso()
    for v in cat["videos"]:
        f = Path(v["caminho"])
        if not v["no_pc"] or not f.is_file() or _item(f) in reab:
            continue
        if em_uso and any(str(f.resolve()).casefold().startswith(p) for p in em_uso):
            continue  # hipercool ainda posta Shorts deste capítulo/língua
        redes = {p["plataforma"] for p in v["postagens"]} | redes_pasta.get(f.parent, set())
        if v["tipo"] == "bruto":
            ok = f"{f.stem}_COMPLETO{f.suffix}".casefold() in finais and f.stat().st_mtime < limite_bruto
        else:
            datas = [politica._dt(p["quando"]) for p in v["postagens"]]
            ok = bool(datas) and all(d is None or d < limite for d in datas)
            if ok and etapas.so_no_fim(v["projeto"]):
                # 23/10 (parceiro): também sai quando todas as postagens têm mais de sai_apos_dias dias — senão o que
                # nunca vai pro Instagram ficava no PC pra sempre; TikTok/Instagram baixam do Drive (catalogo.baixar)
                dias = (etapas.cfg()["projetos"].get(v["projeto"]) or {}).get("sai_apos_dias")
                velho = bool(dias) and all(d is not None and d < limite - timedelta(days=dias) for d in datas)
                ok = etapas.etapa(v["projeto"], redes) == etapas.ultima(v["projeto"]) or velho
        if ok:
            alvo = etapas.destino(v, redes)
            pasta = alvo.rsplit("/", 1)[0]
            itens += [(f, alvo)] + [(m, f"{pasta}/{m.name}") for m in _imagens(f)]
    return itens


def rejeitados(cfg, aprov, limite):
    for k in ("ready", "ready_cortes", "ready_grandes"):
        for mp4 in sorted(Path(cfg["paths"][k]).glob("*/*.mp4")):
            d = aprov.get(politica._chave(mp4)) or {}
            if politica.status_aprovacao(mp4, aprov) == "rejeitado" and (politica._dt(d.get("em")) or limite) < limite:
                yield mp4
                yield from (mp4.with_name(mp4.stem + s) for s in ("_thumb.jpg", ".postar.json", "_meta.txt")
                            if mp4.with_name(mp4.stem + s).exists())


PARCEIRO_SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")


def parceiro_reprovados(limite):
    """29/10 (dona: "sim" pros reprovados irem pro Drive): Short de parceiro reprovado (revisao "reprovado...", nunca
    postado) e parado há mais de ESPERA ficava no PC pra sempre. Sobe o vídeo e a capa; o postar.json fica (se a dona
    liberar depois, o vídeo está em videos-backup/parceiro/nao-usados/<pasta>)."""
    for pj in PARCEIRO_SHORTS.glob("*/postar.json"):
        try:
            d = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if d.get("categoria") != "parceiro" or d.get("posted_url") or "reprovado" not in str(d.get("revisao") or ""):
            continue
        if pj.stat().st_mtime > limite:
            continue
        for f in [pj.parent / d.get("arquivo", "video.mp4")] + list(pj.parent.glob("capa*.jpg")):
            if f.is_file():
                yield f, f"{DRIVE}/parceiro/nao-usados/{pj.parent.name}/{f.name}"


def _textos(f):
    item = _item(f)
    return [t for t in f.parent.iterdir() if t.is_file() and t.suffix.lower() in TEXTO
            and (t.name.startswith((item + ".", item + "_")) or t.name == "postar.json")]


def _rclone(*args, timeout=None):
    # 1 arquivo por chamada e prazo por arquivo: em lote (move --files-from) um envio que engasgava no fim recomecava
    # sozinho para sempre sem erro no log (13/10: 3 h para 1 GB); sozinho o mesmo arquivo subia em 17 s
    try:
        r = subprocess.run([RCLONE, *args, "--retries", "3", "--low-level-retries", "10", "--timeout", "60s", "--contimeout", "30s",
                            "--drive-stop-on-upload-limit", "--log-file", str(RCLONE_LOG), "--log-level", "NOTICE"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=_SEM_JANELA)
    except subprocess.TimeoutExpired:
        return -1, f"passou de {timeout:.0f}s"
    return r.returncode, (r.stderr or r.stdout).strip() or f"detalhes em {RCLONE_LOG}"


def _lista(raiz, arquivos):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
        tmp.write("\n".join(f.relative_to(raiz).as_posix() for f in arquivos))
    return tmp.name


REGISTRO_PASTA = "_MOVIDOS_PARA_DRIVE.txt"  # nao usar _NO_DRIVE.txt: o fila do hipercool traz de volta quem tem esse aviso


def registrar_na_pasta(feitos, em):
    """Deixa em cada pasta de origem a lista legivel do que saiu dela e para onde foi no Drive."""
    por_pasta = {}
    for f, b, alvo in feitos:
        por_pasta.setdefault(f.parent, []).append(f"{em}  {f.name}  ({b / 1e6:.0f} MB)  ->  {alvo}\n")
    for pasta, linhas in por_pasta.items():
        with open(pasta / REGISTRO_PASTA, "a", encoding="utf-8") as r:
            r.writelines(linhas)


def enviar(itens, simular):
    """rclone moveto de cada arquivo para o seu caminho no Drive (so apaga do PC depois de conferir tamanho + md5); os
    textos do item (.json/.txt/.md) so copiados para a mesma pasta. Devolve [(arquivo, bytes, caminho no Drive)] enviados."""
    itens = list(dict(itens).items())  # a capa de uma historia vem 1 vez por versao
    if not itens:
        return []
    tam = {f: f.stat().st_size for f, _ in itens}
    itens.sort(key=lambda it: -tam[it[0]])  # 29/10 (dona: "ir liberando espaço"): os maiores primeiro
    log(f"backup: {len(itens)} arquivo(s), {sum(tam.values()) / 1e6:.0f} MB -> {DRIVE}")
    if simular:
        for f, alvo in itens:
            log(f"   {f.name}  ->  {alvo[len(DRIVE) + 1:]}")
        return [(f, tam[f], alvo) for f, alvo in itens]
    MANIFESTO.parent.mkdir(parents=True, exist_ok=True)
    em = politica.agora().isoformat(timespec="seconds")
    with open(MANIFESTO, "a", encoding="utf-8") as m:  # antes de mover: se cair no meio, registrado e fora do PC = no Drive
        for f, alvo in itens:
            m.write(json.dumps({"em": em, "local": str(f), "drive": alvo, "nome": f.name, "bytes": tam[f]},
                               ensure_ascii=False) + "\n")
    copiar = {}
    for f, alvo in itens:
        for t in _textos(f):
            if t not in tam:
                copiar.setdefault((t.parent, alvo.rsplit("/", 1)[0]), set()).add(t)

    def um(item):  # moveto: confere tamanho + md5 no Drive e so entao apaga do PC
        f, alvo = item
        # 29/10: a pasta é criada na hora de cada arquivo (garantir já faz uma de cada vez, com trava). Antes criava
        # TODAS antes do 1º envio: ~190 pastas x 1 rclone lento = 20+ min sem liberar nada
        try:
            etapas.garantir(alvo.rsplit("/", 1)[0])
        except RuntimeError as e:
            return f, (1, str(e))
        return f, _rclone("moveto", str(f), alvo, timeout=180 + tam[f] / 80e3)  # 17/10: a 300 KB/s ~8 por rodada estouravam o prazo

    enviados = 0
    with ThreadPoolExecutor(3) as ex:  # 3 ao mesmo tempo: o custo fixo de cada chamada (~3 s) nao vira gargalo
        for i, (f, (rc, msg)) in enumerate(ex.map(um, itens), 1):
            if rc:
                log(f"backup:   {f.name}: nao subiu ({msg[-200:]}) - fica no PC, tenta de novo amanha")
            else:
                enviados += tam[f]
            if i % 25 == 0:
                log(f"backup:   {i}/{len(itens)} arquivo(s), {enviados / 1e6:.0f} MB")
    # 29/10: textos DEPOIS dos vídeos — antes vinham primeiro (1 rclone por pasta, ~117 chamadas) e as rodadas de
    # 02:48 e 04:40 morreram nessa fase (memória) sem subir nenhum vídeo: o que libera disco tem de ir primeiro
    for (raiz, pasta), textos in copiar.items():
        arq = _lista(raiz, textos)
        rc, msg = _rclone("copy", str(raiz), pasta, "--files-from-raw", arq, "--no-traverse", timeout=900)
        Path(arq).unlink()
        if rc:
            log(f"backup: copia dos textos para {pasta} com erro {rc}: {msg[-300:]}")
    feitos =[(f, tam[f], alvo) for f, alvo in itens if not f.exists()]
    registrar_na_pasta(feitos, em)
    if len(feitos) < len(itens):
        log(f"backup: {len(itens) - len(feitos)} arquivo(s) nao confirmados no Drive - continuam no PC, tenta de novo amanha")
    return feitos


def limpar_cache(cfg, limite_ts, no_drive, simular):
    """Apaga o que da para refazer: wav/temas do work/ sem nada na fila e parados ha ESPERA; mp4 de output/ ja no Drive."""
    fila = {re.sub(r"_p\d+$", "", f.stem) for k in ("ready", "ready_cortes", "ready_grandes")
            for f in Path(cfg["paths"][k]).glob("*/*.mp4")}
    lixo = []
    for d in sorted(Path(cfg["paths"]["work"]).iterdir()):
        if not d.is_dir() or d.name.startswith(("_", "rede_")) or any(b == d.name or b.startswith(d.name + "_tema") for b in fila):
            continue
        arquivos = [f for f in d.rglob("*") if f.is_file()]
        if arquivos and max(f.stat().st_mtime for f in arquivos) < limite_ts:
            lixo += [f for f in arquivos if f.name in CACHE_WORK or (f.parent.name == "temas" and f.suffix == ".mp4")]
    lixo += [f for f in Path(cfg["paths"]["output"]).glob("*/*.mp4") if (f.name, f.stat().st_size) in no_drive]
    total = sum(f.stat().st_size for f in lixo)
    log(f"backup: cache {len(lixo)} arquivo(s), {total / 1e6:.0f} MB (work/ e output/)")
    if not simular:
        em = politica.agora().isoformat(timespec="seconds")
        with open(MANIFESTO, "a", encoding="utf-8") as m:
            for f in lixo:
                m.write(json.dumps({"em": em, "apagado": str(f), "bytes": f.stat().st_size, "motivo": "cache"}, ensure_ascii=False) + "\n")
                f.unlink()
    return total


TRAVA = RAIZ / "logs" / "backup_drive.lock"


def _vivo(pid):
    # 29/10: pid morto = "INFORMAÇÕES: nenhuma tarefa..." em cp850; lido como utf-8 quebrava (stdout None, TypeError)
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                       encoding="cp850", errors="replace", creationflags=_SEM_JANELA)
    return str(pid) in (r.stdout or "")


def main():
    ap = argparse.ArgumentParser(description="manda para o Google Drive o que ja foi postado ou nao vai mais ser usado")
    ap.add_argument("--simular", action="store_true", help="so mostra o que faria")
    args = ap.parse_args()
    if not args.simular:
        # 29/10: com a internet lenta uma rodada passa de 1 h e a tarefa horária empilhava 2-3 subindo os mesmos arquivos
        try:
            pid = int(TRAVA.read_text().strip())
        except (OSError, ValueError):
            pid = 0
        if pid and pid != os.getpid() and _vivo(pid):
            log(f"backup: rodada anterior (pid {pid}) ainda subindo - esta não começa")
            return
        TRAVA.write_text(str(os.getpid()))
    cfg = load_config()
    if not args.simular:
        rc, msg = _rclone("lsd", REMOTO)
        if rc:
            log(f"backup: sem acesso ao Google Drive (rclone {rc}): {msg[-300:]}")
            log(f"backup: refazer a autorizacao: {RCLONE} config reconnect manhwa-drive:")
            sys.exit(1)
    livre = shutil.disk_usage("D:\\").free
    agora = politica.agora()
    limite = agora - ESPERA
    aprov = politica.ler_json(politica.APROV_FILE, {})
    cat = catalogo.sincronizar()
    itens = do_catalogo(cat, agora - ESPERA_POSTADO, (agora - ESPERA_BRUTO).timestamp(), _reabertos(Path(cfg["publish"]["posted_dir"]).parent))
    fila = Path(cfg["paths"]["ready"]).parent  # rejeitado na aprovacao: fora das etapas, como estava
    itens += [(f, f"{DRIVE}/manhwa-react/nao-usados/{f.relative_to(fila).as_posix()}") for f in rejeitados(cfg, aprov, limite)]
    ja = {f for f, _ in itens}
    itens += [(f, a) for f, a in hipercool_postados(agora) if f not in ja]  # 23/10: hipercool postado sai do PC
    ja = {f for f, _ in itens}
    itens += [(f, a) for f, a in hipercool_estoque(agora, args.simular) if f not in ja]  # 23/10: estoque longe da vez
    ja = {f for f, _ in itens}
    itens += [(f, a) for f, a in parceiro_reprovados(limite.timestamp()) if f not in ja]  # 29/10: reprovado do parceiro
    feitos = enviar(itens, args.simular)
    if feitos and not args.simular:
        for f, b, alvo in feitos:  # 25/10 (dona): documentado na pasta de onde saiu
            registro_drive.anotar(f, alvo, b, "backup_drive.py")
        etapas.invalidar_lista()  # 23/10: a lista do Drive guardada (20 min) deixou de valer
    if feitos and not args.simular:
        por_arquivo = {Path(v["caminho"]): v for v in cat["videos"]}
        for f, _, alvo in feitos:  # o outro PC (TikTok/Instagram) fica sabendo onde e em que canal cada video ja saiu
            v = por_arquivo.get(f)
            if v and v["postagens"]:
                etapas.anotar(v, alvo, v["postagens"])
        etapas.publicar_registro()
        catalogo.sincronizar()  # o catalogo passa a apontar para o Drive
    no_drive = {(f.name, b) for f, b, _ in feitos}
    if MANIFESTO.exists():
        for linha in MANIFESTO.read_text(encoding="utf-8").splitlines():
            r = json.loads(linha)
            if r.get("drive") and not Path(r["local"]).exists():
                no_drive.add((r["nome"], r["bytes"]))
    cache = limpar_cache(cfg, limite.timestamp(), no_drive, args.simular)
    total = sum(b for _, b, _ in feitos) + cache
    if args.simular:
        log(f"backup [SIMULACAO]: liberaria {total / 1e9:.2f} GB ({len(feitos)} para o Drive)")
    else:
        depois = shutil.disk_usage("D:\\").free
        log(f"backup: {len(feitos)} arquivo(s) no Drive; D: livre {livre / 1e9:.1f} -> {depois / 1e9:.1f} GB")


if __name__ == "__main__":
    main()
