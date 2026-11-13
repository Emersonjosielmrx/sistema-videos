r"""disparar_sti.py — o notebook STI (Linux Mint) monta Shorts de parceiro INTEIROS (13/11/2026).

Dona 12-13/11: "por que o PC1 tem que montar? temos que rearranjar pra não ter gargalo no PC1"; "o STI no Linux Mint é
mais leve e vai gerar mais vídeos"; "manter os dispositivos totalmente ocupados". Até aqui o STI só recebia o xfade
de 3 clipes de cada Short do PC1. O 1º Short completo saiu dele em 13/11 08:53 (1080x1920, 60 fps, voz clonada,
legenda, ficha igual à do PC1).

Mesmo desenho do PC3 (ocioso.disparar_parceiro_pc3 / disparar_pc3.py), fora da rodada do controlador:
  1. buscar(): se o Short anterior terminou, traz a ficha (postar.json + video.mp4 + capa) pra pasta de postagem do
     PC1, confere 1080x1920 e áudio, apaga lá e dispara a postagem.
  2. disparar(): escolhe canal/fonte AQUI com a MESMA regra do PC2 (ocioso._escolher_pc2: prioridade por rendimento,
     fonte reservada), baixa a fonte AQUI (vez do yt-dlp do PC1), manda pro STI e dispara ~/recapd-sti/sti_short.sh.
O STI nunca fala com o YouTube (SEM_YTDLP=1) nem posta: só monta.

Não dispara quando: o STI está com a vez do TikTok/Veo/login (maquina_remota: reserva não-manual segue valendo, o
Short roda com nice), 3 falhas seguidas (estado\sti_short_falhou.json), ou controle "sti producao" desligado.
Trava própria: nunca 2 ao mesmo tempo. Log: logs\disparar_sti.log.

    python disparar_sti.py            # busca o pronto e, se livre, dispara o próximo
    python disparar_sti.py buscar     # só busca
    python disparar_sti.py status
Desligar: python controle.py desligar sti producao   (ou env STI_SHORTS=0)
"""
import json
import msvcrt
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
PROD = Path(r"D:\recapd-ambientes\producao")
SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")
FEITOS = Path(r"D:\hipercool-materiais\anime")
LOG = BASE / "logs" / "disparar_sti.log"
TRAVA = BASE / "estado" / "disparar_sti.lock"
EST = BASE / "estado" / "sti_short.json"
FALHOU = BASE / "estado" / "sti_short_falhou.json"
ALVO = "sti"  # alias do ~/.ssh/config
R_BASE = "recapd-sti"
R_SHORTS = "D/hipercool-materiais/animes recap/shorts"
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
MORTO_MIN = 100  # log parado há mais que isso sem .fim = morreu


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    if sys.stdout:
        try:
            print(linha, flush=True)
        except (OSError, ValueError):
            pass


def _ssh(cmd, timeout=120):
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", ALVO, cmd], capture_output=True,
                       timeout=timeout, creationflags=_SEM_JANELA)
    return r.returncode, (r.stdout or b"").decode("utf-8", "replace")


def _scp(*args, timeout=900):
    return subprocess.run(["scp", "-q", "-r", "-o", "BatchMode=yes", *args], capture_output=True, timeout=timeout,
                          creationflags=_SEM_JANELA)


def _falhas():
    try:
        return int(json.loads(FALHOU.read_text(encoding="utf-8")).get("seguidas", 0))
    except (OSError, ValueError):
        return 0


def _falhou(vid, motivo):
    n = _falhas() + 1
    FALHOU.write_text(json.dumps({"seguidas": n, "id": vid, "motivo": motivo,
                                  "quando": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False),
                      encoding="utf-8")
    log(f"[!] STI: Short {vid} falhou ({motivo}) — {n}ª falha seguida")
    if n == 3:
        try:
            import avisos
            avisos.enviar(f"STI pausado pros Shorts: 3 seguidos falharam (último {vid}: {motivo}). "
                          f"Log: ~/recapd-sti/logs/sti_short_{vid}.log", "sti shorts", importante=True)
        except Exception:  # noqa: BLE001
            pass


def _video_ok(mp4):
    """(ok, texto). 1080x1920 no mínimo (regra da dona) e áudio com som."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height:format=duration", "-of", "json", str(mp4)], capture_output=True,
                           text=True, timeout=60, creationflags=_SEM_JANELA)
        j = json.loads(r.stdout)
        w, h = j["streams"][0]["width"], j["streams"][0]["height"]
        dur = float(j["format"]["duration"])
        v = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-af", "volumedetect", "-vn", "-f",
                            "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=120, creationflags=_SEM_JANELA)
        import re
        m = re.search(r"mean_volume:\s*(-?[\d.]+)", v.stderr or "")
        vol = float(m.group(1)) if m else -99.0
    except Exception as e:  # noqa: BLE001
        return False, f"não medi o vídeo ({type(e).__name__})"
    if min(w, h) < 1080:
        return False, f"{w}x{h} — abaixo de 1080p"
    if dur < 8:
        return False, f"só {dur:.0f} s"
    if vol < -45:
        return False, f"áudio mudo (volume médio {vol:.0f} dB)"
    return True, f"{w}x{h}, {dur:.0f} s, {vol:.0f} dB"


def _devolver(vid):
    """Tira o vídeo do "já tentado" pra outra máquina poder fazer (o Short não chegou a existir)."""
    arq = FEITOS / "_feitos_short_attempted.txt"
    try:
        linhas = [l for l in arq.read_text(encoding="utf-8").splitlines() if l.strip() and l.strip() != vid]
        arq.write_text("".join(l + chr(10) for l in linhas), encoding="utf-8")
    except OSError:
        pass


def _trazer_pasta(p):
    """Traz 1 pasta de Short pronta do STI pra postagem do PC1. True = entrou na postagem."""
    dst = SHORTS / p
    if dst.exists():  # nome já usado aqui (raro): não sobrescreve
        log(f"[!] {p} já existe no PC1 — fica no STI")
        return False
    tmp = Path(tempfile.mkdtemp(prefix="sti_short_", dir=str(SHORTS.parent)))
    # 13/11: o scp do Windows fala SFTP e quer o caminho CRU — com "\ " ele procurava "animes\" e falhava
    # ("No such file"): 2 Shorts prontos ficaram presos no STI. Tenta cru; o jeito antigo fica de reserva.
    # (testado 13/11 15:36: cru e com "\ " falham; entre ASPAS SIMPLES funciona — o scp daqui manda o caminho pro
    # shell do STI, que separa no espaço)
    r = _scp(f"{ALVO}:'{R_SHORTS}/{p}'", str(tmp))
    veio = tmp / p
    if r.returncode != 0 or not (veio / "postar.json").exists():
        shutil.rmtree(veio, ignore_errors=True)
        r = _scp(f"{ALVO}:{R_SHORTS}/{p}".replace(" ", "\\ "), str(tmp))
    if r.returncode != 0 or not (veio / "postar.json").exists() or not (veio / "video.mp4").exists():
        log(f"[!] falhou trazer {p} do STI (fica lá): {(r.stderr or b'').decode('utf-8', 'replace')[:160]}")
        shutil.rmtree(tmp, ignore_errors=True)
        return False
    ok, como = _video_ok(veio / "video.mp4")
    if not ok:
        log(f"[!] {p} do STI REPROVADO na chegada ({como}) — não entra na postagem; cópia fica no STI")
        shutil.rmtree(tmp, ignore_errors=True)
        _ssh(f"mv ~/{shlex.quote(R_SHORTS)}/{shlex.quote(p)} ~/{R_BASE}/reprovados_$(date +%s)_{shlex.quote(p)}", 60)
        return False
    try:  # marca de onde veio (pro painel e pra medir o STI depois)
        pj = veio / "postar.json"
        d = json.loads(pj.read_text(encoding="utf-8"))
        d["feito_em"] = "sti"
        pj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, ValueError):
        pass
    shutil.move(str(veio), str(dst))
    shutil.rmtree(tmp, ignore_errors=True)
    _ssh(f"rm -rf ~/{shlex.quote(R_SHORTS)}/{shlex.quote(p)}", 120)
    log(f"STI -> PC1: {p} trazido pra postagem ({como})")
    return True
    return False

def _trazer_presos():
    """13/11: Short que ficou pronto no STI e não veio (cópia falhou, registro apagado). Só quando nada roda lá.
    Devolve False (não segura o disparo do próximo)."""
    try:
        rc, txt = _ssh(f"pgrep -fc '[a]nime_auto[.]py --modo' || true; echo ---; ls -1 ~/{shlex.quote(R_SHORTS)} "
                       "2>/dev/null", timeout=40)
    except subprocess.TimeoutExpired:
        return False
    if rc != 0 or "---" not in txt:
        return False
    rodando, pastas = txt.split("---", 1)
    if rodando.strip() not in ("0", ""):
        return False
    trouxe = 0
    for p in [x.strip() for x in pastas.splitlines() if x.strip()]:
        trouxe += 1 if _trazer_pasta(p) else 0
    if trouxe:
        log(f"STI: {trouxe} Short(s) preso(s) lá trazido(s) pra postagem")
        FALHOU.unlink(missing_ok=True)
        try:
            sys.path.insert(0, str(PROD / "bin"))
            import parceiro_diario
            parceiro_diario.disparar_postagem()
        except Exception as e:  # noqa: BLE001
            log(f"[!] postagem não disparada ({type(e).__name__}) — a tarefa de 30 min pega")
    return False


def buscar():
    """Short que o STI terminou -> pasta de postagem do PC1. True = ainda está fazendo (não dispara outro)."""
    try:
        est = json.loads(EST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _trazer_presos()
    vid = est["id"]
    rc, txt = _ssh(f"cat ~/{R_BASE}/logs/sti_short_{shlex.quote(vid)}.fim 2>/dev/null || echo ANDANDO; "
                   f"echo ---; echo $(( ($(date +%s) - $(stat -c %Y ~/{R_BASE}/logs/sti_short_{shlex.quote(vid)}.log "
                   f"2>/dev/null || echo 0)) / 60 )); echo ---; ls -1 ~/{shlex.quote(R_SHORTS)} 2>/dev/null", timeout=60)
    if rc != 0 or "---" not in txt:
        log(f"STI não respondeu (rc {rc}) — tento na próxima")
        return True
    fim, parado, pastas = (p.strip() for p in (txt.split("---") + ["", ""])[:3])
    if fim == "ANDANDO":
        mins = int(parado) if parado.lstrip("-").isdigit() else 0
        # 13/11: o STI reiniciou sozinho 3x no dia (12:51, 17:38, 17:41) e o Short que rodava morria; o PC1 esperava
        # 100 min de log parado pra perceber. Sem processo do anime_auto lá e log parado há > 6 min = caiu: libera
        # agora, devolve o vídeo pra fila (sai do "attempted") e NÃO conta como falha do Short.
        if mins > 6:
            try:
                rc3, vivo = _ssh("pgrep -fc '[a]nime_auto[.]py --modo' || true; uptime -s", timeout=40)
            except subprocess.TimeoutExpired:
                rc3, vivo = 1, ""
            if rc3 == 0 and vivo.split()[:1] == ["0"]:
                log(f"[!] STI: o Short {vid} morreu no meio (sem processo lá; ligado desde "
                    f"{' '.join(vivo.split()[1:3])}) — máquina reiniciou; libero o próximo")
                _devolver(vid)
                EST.unlink(missing_ok=True)
                return False
        if mins <= MORTO_MIN:
            log(f"STI ainda fazendo o Short {vid} ({est.get('destino')}; log parado há {mins} min)")
            return True
        _falhou(vid, f"morreu sem terminar (log parado há {mins} min)")
        EST.unlink(missing_ok=True)
        return False
    trouxe = False
    for p in [x.strip() for x in pastas.splitlines() if x.strip()]:
        trouxe = _trazer_pasta(p) or trouxe
    if trouxe:
        with open(FEITOS / "_feitos_short.txt", "a", encoding="utf-8") as f:
            f.write(vid + "\n")
        FALHOU.unlink(missing_ok=True)
        try:
            sys.path.insert(0, str(PROD / "bin"))
            import parceiro_diario
            parceiro_diario.disparar_postagem()
        except Exception as e:  # noqa: BLE001
            log(f"[!] postagem não disparada ({type(e).__name__}) — a tarefa de 30 min pega")
    else:
        rc2, cauda = _ssh(f"tail -c 600 ~/{R_BASE}/logs/sti_short_{shlex.quote(vid)}.log", 60)
        _falhou(vid, f"terminou (rc {fim}) sem ficha: {' '.join(cauda.split())[-220:]}")
    _ssh(f"rm -rf ~/{R_BASE}/workspace/anime/{shlex.quote(vid)}_* ; "
         f"find ~/{R_BASE}/logs -name 'sti_short_*' -mtime +3 -delete", 120)
    EST.unlink(missing_ok=True)
    return False


def _sti_livre():
    """(livre, motivo). Não disputa a máquina com render pesado dela mesma."""
    # "[a]nime_auto" = o padrão não casa com a própria linha do ssh/bash que carrega este comando (contava 1 sempre)
    try:
        rc, txt = _ssh("nproc; cut -d' ' -f1 /proc/loadavg; free -m | awk 'NR==2{print $7}'; "
                       "pgrep -fc '[a]nime_auto[.]py --modo' || true", timeout=60)
    except subprocess.TimeoutExpired:
        return False, "STI não respondeu em 60 s"
    v = txt.split()
    if rc != 0 or len(v) < 4:
        return False, "STI não respondeu"
    nucleos, carga, ram, rodando = int(v[0]), float(v[1]), int(v[2]), int(v[3])
    if rodando:
        return False, "já tem um anime_auto rodando lá"
    if ram < 3500:
        return False, f"só {ram} MB de RAM livre"
    if carga > nucleos * 1.2:
        return False, f"carga {carga} em {nucleos} núcleos"
    return True, f"carga {carga}, {ram} MB livres"


def _instalar():
    """Manda o sti_short.sh e o código que mudou no PC1 pra cópia do STI (~/recapd-sti/bin). O sitecustomize.py e os
    2 arquivos adaptados pro Linux (ytdlp_vez.py, chaves_gemini.py) NUNCA são sobrescritos."""
    r = _scp(str(BASE / "sti_short.sh"), f"{ALVO}:{R_BASE}/sti_short.sh", timeout=60)
    if r.returncode != 0:
        return False
    proteger = {"sitecustomize.py", "msvcrt_linux.py", "ytdlp_vez.py", "chaves_gemini.py"}
    tmp = Path(tempfile.mkdtemp(prefix="sti_bin_"))
    try:
        rc, txt = _ssh(f"cd ~/{R_BASE}/bin && md5sum *.py 2>/dev/null", timeout=60)
        la = {l.split()[1].lstrip("*"): l.split()[0] for l in txt.splitlines() if len(l.split()) == 2}
        import hashlib
        mudou = []
        for p in sorted((PROD / "bin").glob("*.py")):
            if p.name in proteger:
                continue
            # compara sem o CRLF do Windows (a cópia de lá pode estar com LF)
            dados = p.read_bytes()
            if la.get(p.name) not in (hashlib.md5(dados).hexdigest(), hashlib.md5(dados.replace(b"\r\n", b"\n")).hexdigest()):
                shutil.copy2(p, tmp / p.name)
                mudou.append(p.name)
        for nome in ("parceiro.json", "narradores_nichos.json", "narradores_ajustado.json"):
            if (PROD / "config" / nome).exists():
                shutil.copy2(PROD / "config" / nome, tmp / ("_cfg_" + nome))
        if mudou or True:
            r = _scp(*[str(x) for x in tmp.iterdir()], f"{ALVO}:{R_BASE}/_chegando/", timeout=300)
            if r.returncode != 0:
                _ssh(f"mkdir -p ~/{R_BASE}/_chegando", 30)
                r = _scp(*[str(x) for x in tmp.iterdir()], f"{ALVO}:{R_BASE}/_chegando/", timeout=300)
            _ssh(f"cd ~/{R_BASE}/_chegando && for f in _cfg_*; do [ -f \"$f\" ] && mv -f \"$f\" ../config/\"${{f#_cfg_}}\"; "
                 f"done; mv -f *.py ../bin/ 2>/dev/null; chmod +x ../sti_short.sh; true", 60)
        if mudou:
            log(f"STI: {len(mudou)} arquivo(s) do bin atualizado(s) ({', '.join(mudou[:6])}{'...' if len(mudou) > 6 else ''})")
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def disparar():
    """Escolhe, baixa, manda e dispara 1 Short no STI. Devolve o rótulo; RuntimeError com o motivo quando não dá."""
    if os.environ.get("STI_SHORTS") == "0":
        raise RuntimeError("STI_SHORTS=0")
    try:
        import controle
        ok, motivo = controle.ligado("sti", "producao")
        if not ok:
            raise RuntimeError(f"desligado: {motivo}")
    except ImportError:
        pass
    if _falhas() >= 3:
        raise RuntimeError(f"STI pausado: 3 Shorts seguidos falharam lá ({FALHOU.name})")
    livre, motivo = _sti_livre()
    if not livre:
        raise RuntimeError(f"STI ocupado ({motivo})")
    import ocioso
    ocioso.log = log
    sys.path.insert(0, str(PROD / "bin"))
    import anime_discover
    import anime_fetch
    import parceiro_diario as pdi
    c = pdi.cfg()
    # 13/11: pilha única (ocioso.pegar_pronto) — Short já escolhido e baixado pelo PC1 = dispara em segundos. O STI
    # ficava parado enquanto o PC1 escolhia e baixava (até 50 min numa rodada). Pilha vazia = caminho antigo.
    pronto = ocioso.pegar_pronto("sti") if ocioso.PILHA_ALVO > 1 else None
    if pronto:
        tmp, meta = pronto
        cand, alvo = meta["cand"], meta["alvo"]
        escolha = (meta["fonte"], meta["tipo"], meta["rodizio"]) if meta.get("rodizio") else (meta["fonte"], meta["tipo"])
        log(f"STI pega da pilha: {cand['id']} pra {alvo['nome']}")
    else:
        esc = ocioso._escolher_pc2(pdi, anime_discover, c)
        if not esc:
            raise RuntimeError("nenhum canal que falta tem vídeo novo (ou filas cheias)")
        alvo, escolha, cand = esc
        tmp = None
    fonte, tipo = escolha[0], escolha[1]
    if not _instalar():
        if pronto:
            ocioso.devolver_pronto(tmp)
        raise RuntimeError("não consegui mandar o sti_short.sh pro STI")
    if tmp is None:
        tmp = Path(tempfile.mkdtemp(prefix="prebaixar_sti_"))
    enviado = False
    try:
        if pronto:
            video = next(iter(sorted(tmp.glob("*.mp4"))), None)
        else:
            video = anime_fetch.download_video(cand["url"], tmp)  # baixa AQUI (vez do yt-dlp do PC1)
        if not video:
            raise RuntimeError(f"a fonte {cand['id']} não baixou aqui — o STI não baixa, não dispara")
        fonte_mp4 = tmp / "source.mp4"
        if Path(video) != fonte_mp4:
            shutil.move(str(video), str(fonte_mp4))
        extras = (sorted(tmp.glob("cap*.vtt")) + [tmp / "cand.json"]) if pronto else ocioso._extras_pc1(cand, tmp, anime_fetch)
        extras = [x for x in extras if Path(x).exists()]
        r_dir = f"{R_BASE}/workspace/anime/{cand['id']}_{ocioso._slug(cand['title'])}"
        _ssh(f"mkdir -p ~/{shlex.quote(r_dir)}", 30)
        cp = _scp(str(fonte_mp4), *[str(p) for p in extras], f"{ALVO}:{r_dir}/", timeout=900)
        if cp.returncode != 0:
            raise RuntimeError(f"scp pro STI falhou: {(cp.stderr or b'').decode('utf-8', 'replace')[:200]}")
        enviado = True
    finally:
        if pronto and not enviado:
            ocioso.devolver_pronto(tmp)  # não chegou lá: o download volta pra pilha
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    if not pronto:  # o preparado já entrou nos tentados quando foi preparado
        with open(FEITOS / "_feitos_short_attempted.txt", "a", encoding="utf-8") as f:
            f.write(cand["id"] + "\n")
    args = " ".join(shlex.quote(str(a)) for a in (cand["id"], fonte, alvo["handle"], alvo["canal"], tipo))
    rc, saida = _ssh(f"nohup ~/{R_BASE}/sti_short.sh {args} > /dev/null 2>&1 < /dev/null & echo disparado", 40)
    if "disparado" not in saida:
        raise RuntimeError(f"o STI não aceitou o disparo: {saida.strip()[:160]}")
    if len(escolha) == 3:
        pdi._rodizio_registrar(escolha[2])
    EST.write_text(json.dumps({"id": cand["id"], "destino": alvo["nome"], "titulo": cand["title"],
                               "inicio": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False),
                   encoding="utf-8")
    log(f"STI faz o Short {cand['id']} [{tipo}] pra {alvo['nome']}")
    return f"Cortes: Short {cand['id']} pra {alvo['nome']} no STI"


def main():
    if sys.stdout is None:  # pythonw
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    f = open(TRAVA, "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        return 0
    try:
        acao = sys.argv[1] if len(sys.argv) > 1 else ""
        if acao == "status":
            print("em andamento:", EST.read_text(encoding="utf-8") if EST.exists() else "nada",
                  "| falhas seguidas:", _falhas(), "| STI:", _sti_livre())
            return 0
        if buscar():
            return 0
        if acao == "buscar":
            return 0
        try:
            log("OK: " + disparar())
            return 0
        except RuntimeError as e:
            log(f"STI: {e}")
            return 1
        except Exception as e:  # noqa: BLE001
            log(f"[!] disparo do STI falhou: {type(e).__name__}: {e}")
            return 1
    finally:
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        f.close()


if __name__ == "__main__":
    sys.exit(main())
