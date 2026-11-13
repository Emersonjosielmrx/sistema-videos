"""ocioso.py — MODO OCIOSO do recap de anime longo (substitui o turno da noite AnimeRecapNoturno, pausado em 17/10).

Dono 17/10/2026: "mudar de modo noturno pra modo ocioso, em que ele mede a máquina e sempre que possível começa a
produção de um"; "o noturno deve passar para o PC2 e usar o Google Drive lá pra não ocupar o disco".
Tarefa `AnimeOcioso`, a cada 15 min, sem janela:
  1. atualiza o código de anime do PC2 (pc2_recapd.sincronizar_bin — igual ao que o hipercool faz);
  2. mede o PC2 (pc2_recapd.medir: sem render do hipercool/anime, CPU < 40%, RAM >= 4 GB, disco >= 8 GB);
  3. ocioso e nenhum anime longo em andamento -> dispara 1 (anime_auto --modo deitado --engine worker): o PC1 acha o
     anime e escreve o roteiro, o PC2 renderiza, sobe o vídeo pro Drive (videos-backup/anime/1_youtube_pendente) e
     apaga o dele; aqui fica só a ficha em D:\\hipercool-materiais\\animes recap\\na_nuvem.
Desligar: criar D:\\video-fila\\OCIOSO_DESLIGADO.json.
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — 29/10 (dona): nenhum processo filho (yt-dlp, ssh, ffmpeg) abre janela
import json
import shutil
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import pc2_recapd  # noqa: E402
import maquinas  # noqa: E402

LOG = BASE / "ocioso.log"
DESLIGADO = BASE / "OCIOSO_DESLIGADO.json"
PROD = Path(r"D:\recapd-ambientes\producao")
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
# 30/10 (D39): sob pythonw (tarefa agendada) o "ssh" do PATH é o do Windows (System32), que trava depois de autenticar
# (maquinas.py, 17/10): o AlimentarPC2 via "PC2 ainda fazendo" em Shorts com .fim pronto. Sempre o do Git.
_SSH = maquinas.SSH
_SCP = _SSH.replace("ssh.exe", "scp.exe") if _SSH.lower().endswith("ssh.exe") else "scp"
_DETACHED = 0x00000008


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _deitado_rodando():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ForEach-Object { $_.CommandLine }"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=_SEM_JANELA)
    linhas = (r.stdout or "").splitlines()
    if r.returncode != 0 or not linhas:
        return True  # sem saber, não dispara
    return any("anime_auto.py" in l and "deitado" in l for l in linhas)


SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")
FEITOS = Path(r"D:\hipercool-materiais\anime")
EST_PC2 = BASE / "estado" / "pc2_parceiro.json"  # formato antigo (1 Short por vez): lido e migrado
EST_PC2_DIR = BASE / "estado" / "pc2_parceiro"  # 27/10: 1 arquivo por Short em andamento no PC2
PC2_FALHOU = BASE / "estado" / "pc2_parceiro_falhou.json"
# 27/10 (dona: "o PC2 é só worker, CPU a 100% o tempo todo, máximo de Shorts"): 1 Short por vez deixava o PC2 a 5% de
# CPU (o Short espera voz/texto pela rede) e 4 Shorts em 16 h. Medido: Short rodando = 0-14% CPU, 9,3 GB RAM livres.
# 30/10 (D39): 3 -> 4. Com 2 Shorts (00:41) a CPU média da última hora foi 19% e sobraram 6,9 GB; RAM/disco/CPU(2+)
# continuam barrando, e o AlimentarPC2 dispara no máximo 1 a cada 5 min (preparo ~160 s aqui).
PC2_SHORTS_MAX = 4
PC2_SHORT_CPU_MAX, PC2_SHORT_RAM_MIN, PC2_SHORT_DISCO_MIN = 85, 2.5, 3  # 13/11 dona: disco até o fim (era 8)


def _pc2_estados():
    """[(arquivo, dict)] dos Shorts em andamento no PC2."""
    EST_PC2_DIR.mkdir(parents=True, exist_ok=True)
    if EST_PC2.exists():
        try:
            d = json.loads(EST_PC2.read_text(encoding="utf-8"))
            (EST_PC2_DIR / f"{d['id']}.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        except (OSError, ValueError, KeyError):
            pass
        EST_PC2.unlink(missing_ok=True)
    out = []
    for f in sorted(EST_PC2_DIR.glob("*.json")):
        try:
            out.append((f, json.loads(f.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            f.unlink(missing_ok=True)
    return out


def pc2_vaga_short():
    """(True/False, motivo): cabe mais um Short no PC2? Regra só dos Shorts (outro trabalho rodando lá não barra)."""
    n = len(_pc2_estados())
    if n >= PC2_SHORTS_MAX:
        return False, f"{n} Shorts rodando no PC2 (máx. {PC2_SHORTS_MAX})"
    import maquinas
    m = maquinas.medir("pc2")
    if m.get("cpu") is None:
        return False, f"PC2 não respondeu ({m.get('motivo')})"
    # 28/10: com 1 Short rodando, a CPU a 100% é o render (ffmpeg) DELE por uns minutos — barrar ali deixava o PC2
    # sempre em 1 Short por vez (08:33 "CPU 100%"). O 2º passa quase tudo esperando voz/texto: a CPU só barra com 0 ou 2+.
    # 30/10 (D39, dona: "o PC2 foca no máximo de Shorts"): com 0 Shorts a CPU alta é a língua do hipercool (prioridade
    # 5, o Short é 3) e barrava o Short: PC2 trabalhou 20 % das 24 h. Agora a CPU só barra com 2+ Shorts.
    cpu_alta = m["cpu"] > PC2_SHORT_CPU_MAX and n >= 2
    if cpu_alta or m["ram_gb"] < PC2_SHORT_RAM_MIN or m["disco_gb"] < PC2_SHORT_DISCO_MIN:
        return False, f"PC2 sem folga (CPU {m['cpu']}%, RAM {m['ram_gb']} GB, disco {m['disco_gb']} GB; {n} Shorts)"
    return True, f"{n} Shorts rodando, CPU {m['cpu']}%, RAM {m['ram_gb']} GB, disco {m['disco_gb']} GB"


def _ssh(cmd, timeout=300):
    return subprocess.run([_SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "pc2", cmd], capture_output=True,
                          stdin=subprocess.DEVNULL, timeout=timeout, creationflags=_SEM_JANELA)


def _trazer_prontos_pc2():
    """Traz do PC2 as pastas de Short PRONTAS (com postar.json; a de um Short ainda rodando fica). {pasta: fonte}."""
    # 30/10 (D39): `dir` do cmd devolve o nome no código de página do console (cp850) e "meu-irmão-é-mais-velho" chegava
    # estragado: o tar não achava a pasta e o Short pronto ficou preso no PC2 desde 29/10 20:42. PowerShell em UTF-8.
    lst = _ssh('powershell -NoProfile -Command "[Console]::OutputEncoding=[Text.Encoding]::UTF8; '
               "Get-ChildItem 'C:\\hipercool-materiais\\animes recap\\shorts' -Recurse -Filter postar.json "
               '| ForEach-Object { $_.FullName }"')
    pastas = sorted({Path(l.strip()).parent.name for l in (lst.stdout or b"").decode("utf-8", "replace").splitlines()
                     if l.strip().lower().endswith("postar.json")})
    trazidas = {}
    for p in pastas:
        # 12/11: a cópia não tinha prazo — um ssh lento/travado segurava a rodada INTEIRA do controlador (painel:
        # "controlador parado há 29 min"). Agora 10 min por pasta; estourou = mata as 2 pontas, a pasta fica no PC2 e
        # vem na próxima rodada (o rmdir lá só acontece com o postar.json já aqui).
        tar = subprocess.Popen([_SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15",
                                "-o", "ServerAliveCountMax=4", "pc2",
                                f'tar -cf - -C "C:/hipercool-materiais/animes recap/shorts" "{p}"'],
                               stdout=subprocess.PIPE, creationflags=_SEM_JANELA)
        try:
            r = subprocess.run(["tar", "-xf", "-", "-C", str(SHORTS)], stdin=tar.stdout, capture_output=True,
                               timeout=600, creationflags=_SEM_JANELA)
        except subprocess.TimeoutExpired:
            tar.kill()
            tar.stdout.close()
            log(f"[!] trazer {p} do PC2 passou de 10 min — fica lá pra próxima rodada")
            continue
        tar.stdout.close()
        try:
            tar_ok = tar.wait(timeout=60) == 0
        except subprocess.TimeoutExpired:
            tar.kill()
            tar_ok = False
        if tar_ok and r.returncode == 0 and (SHORTS / p / "postar.json").exists():
            _ssh(f'rmdir /s /q "C:\\hipercool-materiais\\animes recap\\shorts\\{p}"')
            log(f"PC2 -> PC1: {p} trazido pra postagem")
            try:
                trazidas[p] = json.loads((SHORTS / p / "postar.json").read_text(encoding="utf-8")).get("fonte", "")
            except (OSError, ValueError):
                trazidas[p] = ""
        else:
            log(f"[!] falhou trazer {p} do PC2 (fica lá)")
    return trazidas


def _buscar_parceiro_pc2():
    """Shorts de parceiro que o PC2 terminou -> pasta de postagem daqui (tar pelo ssh), apaga lá.
    Devolve quantos ainda estão rodando lá (0 = nenhum)."""
    estados = _pc2_estados()
    if not estados:
        return 0
    rodando, terminados = 0, []
    for arq, est in estados:
        fim = _ssh(f'if exist C:\\recapd-e-animes\\logs\\pc2_parceiro_{est["id"]}.fim echo FIM')
        if b"FIM" in (fim.stdout or b""):
            terminados.append((arq, est))
        else:
            rodando += 1
            log(f"PC2 ainda fazendo o Short {est['id']} ({est.get('destino')})")
    if terminados:
        _trazer_prontos_pc2()
        for arq, est in terminados:
            _fechar_short_pc2(est, _ja_aqui(est["id"]))
            arq.unlink(missing_ok=True)
    return rodando


def _fechar_short_pc2(est, trouxe):
    """Registra o fim de um Short do PC2: feito (e chama a postagem) ou falha (máquina = volta pra fila)."""
    vid = est["id"]
    if trouxe:
        with open(FEITOS / "_feitos_short.txt", "a", encoding="utf-8") as f:
            f.write(vid + "\n")
        PC2_FALHOU.unlink(missing_ok=True)
        sys.path.insert(0, str(PROD / "bin"))
        import parceiro_diario
        parceiro_diario.disparar_postagem()  # canal sem post hoje recebe em minutos
    else:
        # 18/10: o yt-dlp do PC2 falhava em segundos, o .fim saía igual e cada rodada queimava 1 vídeo da fila.
        # Falha da máquina (download/narração): o vídeo volta pra fila. Falha do vídeo (sem fala, roteiro recusado):
        # fica nos tentados, senão o PC2 pegaria o mesmo de novo. 3 falhas seguidas pausam o PC2 pro parceiro.
        logpc2 = f"C:\\recapd-e-animes\\logs\\pc2_parceiro_{vid}.log"
        # 30/10 (D39): rede/gateway da IA fora também é máquina (01:23 "host inacessível" -> roteiro com 0 frases: o vídeo
        # era descartado à toa)
        r = _ssh(f'findstr /c:"download falhou" /c:"pool de proxies" /c:"TTS falhou" /c:"gateway timeout" '
                 f'/c:"URLError" /c:"WinError 10065" /c:"WinError 10060" "{logpc2}"')
        maquina = bool((r.stdout or b"").strip())
        if maquina:
            tent = FEITOS / "_feitos_short_attempted.txt"
            tent.write_text("".join(l + "\n" for l in tent.read_text(encoding="utf-8").split() if l != vid),
                            encoding="utf-8")
        seguidas = _pc2_falhas() + 1
        PC2_FALHOU.write_text(json.dumps({"seguidas": seguidas, "id": vid, "log": logpc2,
                                          "quando": datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")
        log(f"[!] PC2 terminou o Short {vid} SEM vídeo ({'máquina: volta pra fila' if maquina else 'vídeo descartado'}"
            f", {seguidas}ª falha seguida)" + (f" — PC2 pausado pro parceiro até apagar {PC2_FALHOU.name}"
                                               if seguidas >= 3 else ""))


def _ja_aqui(vid, horas=30):
    """True se a pasta do Short desta fonte já está na postagem daqui (pode ter vindo numa busca anterior)."""
    limite = time.time() - horas * 3600
    for pj in SHORTS.glob("*/postar.json"):
        try:
            if pj.stat().st_mtime >= limite and vid in pj.read_text(encoding="utf-8"):
                return True
        except OSError:
            continue
    return False


def _pc2_falhas():
    try:
        n = int(json.loads(PC2_FALHOU.read_text(encoding="utf-8")).get("seguidas", 3))
        # 30/10 (D39): a pausa de 3 falhas só saía apagando o arquivo à mão — uma queda do gateway de madrugada (01:23,
        # "host inacessível") parava o PC2 até a dona acordar. Vence em 2 h: tenta de novo; falhou de novo, pausa de novo.
        if n >= 3 and time.time() - PC2_FALHOU.stat().st_mtime > 2 * 3600:
            return 2
        return n
    except (OSError, ValueError):
        return 0


def _slug(s):
    return "".join(c if c.isalnum() else "_" for c in s)[:40].strip("_")


def _extras_pc1(cand, tmp, anime_fetch):
    """26/10: PC2/PC3 rodam com SEM_YTDLP=1 (mesmo IP da casa): a legenda (aqui, na vez do yt-dlp do PC1) e o
    candidato (cand.json, no lugar de listar o canal lá) vão junto com a fonte. Devolve os arquivos a mandar."""
    try:
        anime_fetch.fetch_captions(cand["url"], tmp)
    except Exception as e:  # noqa: BLE001  (sem legenda = o PC remoto usa o Whisper)
        log(f"[!] legenda pro PC remoto falhou ({type(e).__name__}: {e})")
    (tmp / "cand.json").write_text(json.dumps(cand, ensure_ascii=False), encoding="utf-8")
    return sorted(tmp.glob("cap*.vtt")) + [tmp / "cand.json"]


def _fonte_para(cand, pasta, anime_fetch):
    """Fonte + extras (legenda, cand.json) do Short do PC2 em `pasta`. (Path do vídeo ou None, [arquivos extras]).
    30/10 (D43): com o IP de casa barrado (ytdlp_vez em pausa) e o baixador do Kaggle vivo, baixa LÁ (outro IP;
    colab\\kaggle_baixador.py) — antes o PC2 ficava horas sem Short esperando a pausa acabar."""
    try:
        import ytdlp_vez
        import kaggle_baixar
        if ytdlp_vez.pausado() and kaggle_baixar.vivo():
            log(f"fonte {cand['id']} pelo Kaggle (IP de casa em pausa)")
            video, legs = kaggle_baixar.baixar(cand["url"], cand["id"], pasta, log=log)
            if video:
                (Path(pasta) / "cand.json").write_text(json.dumps(cand, ensure_ascii=False), encoding="utf-8")
                return video, legs + [Path(pasta) / "cand.json"]
            return None, []
    except Exception as e:  # noqa: BLE001 — Kaggle é atalho; o caminho normal segue
        log(f"[!] Kaggle indisponível pra {cand['id']} ({type(e).__name__}: {str(e)[:120]}) — caminho normal")
    video = anime_fetch.download_video(cand["url"], pasta)
    if not video:
        return None, []
    return video, list(_extras_pc1(cand, Path(pasta), anime_fetch))


def _prebaixar_pc2(cand):
    """PC1 baixa o vídeo fonte e envia pro workspace do PC2 via SCP. True se ok."""
    sys.path.insert(0, str(PROD / "bin"))
    import anime_fetch
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="prebaixar_"))
    os.environ["YTDLP_PRIORIDADE"] = "pc2"  # 30/10 (D39): o download do PC2 passa na frente na vez do yt-dlp
    try:
        video, extras = _fonte_para(cand, tmp, anime_fetch)
        if not video:
            log(f"[!] prebaixar: download falhou pra {cand['id']}")
            return False
        nome_pasta = f"{cand['id']}_{_slug(cand['title'])}"
        r_dir = f"C:/recapd-e-animes/workspace/anime/{nome_pasta}"
        _ssh(f'mkdir "{r_dir}"')
        arquivos = [str(video)] + [str(p) for p in extras]
        cp = subprocess.run([_SCP, "-q", "-o", "BatchMode=yes", *arquivos,
                             f"pc2:{r_dir}/"], capture_output=True, timeout=300,
                            creationflags=_SEM_JANELA)
        if cp.returncode != 0:
            log(f"[!] prebaixar: SCP falhou: {(cp.stderr or b'').decode('utf-8', 'replace')[:200]}")
            return False
        log(f"prebaixar: {video.name} ({video.stat().st_size // 1048576} MB) -> PC2:{r_dir}")
        return True
    finally:
        os.environ.pop("YTDLP_PRIORIDADE", None)
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


TRAVA_DISPARO_PC2 = BASE / "estado" / "pc2_disparo.lock"
# 30/10 (D39): Short preparado com antecedência (fonte + legenda + cand.json já baixados aqui). O preparo levava
# 438–793 s por Short (03:27–03:51) com o PC2 esperando; com 1 pronto o disparo é só enviar e rodar.
PRONTOS_PC2 = BASE / "estado" / "pc2_prontos"
PRONTO_MAX_H = 8
# 13/11 (dona: "o sistema tem de se comportar como um só; todos sempre no máximo"): a pilha era de 1 Short e só do PC2;
# o PC3 e o STI escolhiam e baixavam NA HORA do disparo (4 a 50 min com a máquina parada: em 13/11 o PC2 entregou 43
# Shorts, o PC3 10 e o STI 3). Agora é UMA pilha pra todos: o PC1 mantém PILHA_ALVO Shorts já baixados e cada máquina
# livre pega o mais antigo (pegar_pronto). PILHA_ALVO=1 volta ao antigo. Disco: cada fonte tem ~5-40 MB.
PILHA_ALVO = int(os.environ.get("PILHA_ALVO", "5"))
PILHA_DISCO_MIN_GB = float(os.environ.get("PILHA_DISCO_MIN_GB", "2"))


def _pilha_por_canal():
    """{id do canal: quantos Shorts já estão preparados pra ele} — entra na conta da fila (senão a pilha inteira ia
    pro mesmo canal do topo)."""
    out = {}
    for m in list(PRONTOS_PC2.glob("*/meta.json")) + list(PRONTOS_PC2.glob("_baixando_*/meta_parcial.json")):
        try:
            cid = json.loads(m.read_text(encoding="utf-8"))["alvo"]["canal"]
            out[cid] = out.get(cid, 0) + 1
        except (OSError, ValueError, KeyError):
            pass
    return out


def pegar_pronto(maquina):
    """Tira da pilha o Short preparado mais antigo e devolve (pasta, meta) — a pasta passa a ser de quem pegou (move
    pra estado\\pilha_em_uso\\<maquina>_<id>; apagar depois de mandar). None = pilha vazia. O rename é atômico: duas
    máquinas nunca pegam o mesmo."""
    uso = BASE / "estado" / "pilha_em_uso"
    uso.mkdir(parents=True, exist_ok=True)
    for d in uso.glob("*"):  # sobra de disparo que caiu no meio há mais de 2 h
        if d.is_dir() and time.time() - d.stat().st_mtime > 7200:
            import shutil
            shutil.rmtree(d, ignore_errors=True)
    for pasta, meta in _prontos_pc2():
        dst = uso / f"{maquina}_{pasta.name}"
        try:
            pasta.rename(dst)
        except OSError:
            continue  # outra máquina pegou este agora
        return dst, meta
    return None


def devolver_pronto(pasta):
    """O envio pra máquina falhou: o preparado volta pra pilha (não perde o download)."""
    try:
        Path(pasta).rename(PRONTOS_PC2 / Path(pasta).name.split("_", 1)[1])
    except (OSError, IndexError):
        pass


def _ler_feitos(nome):
    return set((FEITOS / nome).read_text(encoding="utf-8").split()) if (FEITOS / nome).exists() else set()


# 03/11 (dona: Kaggle "pra ajudar a encher o estoque mais rápido", PCs no máximo como antes): agora 3 escolhem fonte ao
# mesmo tempo (PC2/alimentador, PC3 e o abastecedor do Kaggle) e o "tentado" só era gravado depois do download —
# minutos em que outro podia pegar a MESMA fonte (regra: nunca a mesma fonte em 2 canais). Quem escolhe reserva na hora.
RESERVAS = BASE / "estado" / "fontes_reservadas.json"
RESERVA_H = 8


def _reservados():
    try:
        d = json.loads(RESERVAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {k for k, t in d.items() if time.time() - t < RESERVA_H * 3600}


def _reservar(vid):
    import msvcrt
    RESERVAS.parent.mkdir(parents=True, exist_ok=True)
    with open(BASE / "estado" / "fontes_reservadas.lock", "a+") as trava:
        for _ in range(50):
            try:
                msvcrt.locking(trava.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                time.sleep(0.1)
        try:
            try:
                d = json.loads(RESERVAS.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                d = {}
            d = {k: t for k, t in d.items() if time.time() - t < RESERVA_H * 3600}
            if vid in d:
                return False  # outro já reservou
            d[vid] = time.time()
            tmp = RESERVAS.with_suffix(".tmp")
            tmp.write_text(json.dumps(d), encoding="utf-8")
            tmp.replace(RESERVAS)
            return True
        finally:
            try:
                trava.seek(0)
                msvcrt.locking(trava.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass


_LINGUAS_DA_VEZ = ""  # 12/11: línguas da versão extra quando as filas pt estão cheias (_escolher_pc2)


_FONTES_VAZIAS = BASE / "estado" / "fontes_vazias.json"


def _fontes_vazias():
    """{url da fonte} que veio sem vídeo novo nos últimos FONTE_VAZIA_MIN minutos (vale pra PC2, PC3, STI e Kaggle)."""
    try:
        d = json.loads(_FONTES_VAZIAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    corte = time.time() - float(os.environ.get("FONTE_VAZIA_MIN", "90")) * 60
    return {u for u, t in d.items() if t > corte}


def _fonte_vazia_marcar(url):
    try:
        try:
            d = json.loads(_FONTES_VAZIAS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            d = {}
        d = {u: t for u, t in d.items() if time.time() - t < 86400}
        d[url] = time.time()
        _FONTES_VAZIAS.write_text(json.dumps(d), encoding="utf-8")
    except OSError:
        pass


def _escolher_pc2(pdi, anime_discover, c):
    """(alvo, escolha, cand) do próximo Short do PC2, ou None (mesma regra do parceiro_diario)."""
    fila = pdi._fila(pdi.itens(c))
    for _cid, _n in _pilha_por_canal().items():  # 13/11: o que já está na pilha conta como estoque do canal
        fila[_cid] += _n
    # 12/11 (dona: "por que PC2, STI, desktop e celulares não estão sendo usados se precisamos de mais vídeos?"): aqui
    # o alvo era o fila_alvo PURO (21) — o parceiro_diario dobra pra quem rende (>= 300 views/48 h: 42). Os canais que
    # MAIS rendem (Esporte Noturno 25/42, Plantão 25/42, HistoriasEmFrames 26/42, Fio da Meada 24/42, CenaReact 21/42)
    # pareciam cheios pro PC2/desktop -> "filas cheias", desktop parado o dia todo. Mesma regra do parceiro_diario
    # (_alvo) e sem canal travado pelo YouTube.
    try:
        rend = pdi._rendimento_canais() if os.environ.get("PARCEIRO_RESERVA_POR_RENDIMENTO", "1") != "0" else {}
    except Exception:  # noqa: BLE001
        rend = {}
    try:
        travados = pdi._canais_travados(c)
    except Exception:  # noqa: BLE001
        travados = set()

    def _alvo(d):
        return pdi.alvo_por_rendimento(d, rend, d.get("fila_alvo", c.get("fila_alvo", 2)))  # 12/11: estoque por rendimento
    pts = [d for d in c["pt"] if d.get("ativo", True) and d["canal"] not in travados]
    falta = [d for d in pts if fila[d["canal"]] < _alvo(d)]
    global _LINGUAS_DA_VEZ
    _LINGUAS_DA_VEZ = ""
    if not falta:
        # 12/11 dona ("o Short nos dispositivos não pode parar; pode fazer os internacionais, que é mais render, até
        # nos celulares"): filas pt cheias = o PC2/desktop faz o Short do canal pt de MENOR fila e junto as versões nas
        # LÍNGUAS com fila abaixo do alvo (cada uma é um anime-pipeline inteiro = render). Sem língua faltando = para
        # como antes. LINGUAS_QUANDO_CHEIO=0 desliga.
        ling = []
        # 13/11: com as regras atuais a versão de língua não posta (parceiro_diario.lingua_nasce_morta: mesma fonte do pt
        # + "nunca em 2 canais" + pt com preferência — 10 feitas e 1 agendada desde 12/11; e o mesmo vídeo rende 1.273
        # views no Esporte Noturno contra 0 no canal tailandês). A máquina livre não gasta ~23 min por versão morta.
        morta = getattr(pdi, "lingua_nasce_morta", lambda: False)()
        if os.environ.get("LINGUAS_QUANDO_CHEIO", "1") != "0" and not morta:
            ling = [lang for lang, d in (c.get("idiomas") or {}).items()
                    if d.get("ativo", True) and fila[d["canal"]] < d.get("fila_alvo", 2)]
            ling = sorted(ling, key=lambda lg: fila[c["idiomas"][lg]["canal"]])[:int(os.environ.get(
                "LINGUAS_POR_SHORT", "2"))]
        if not ling or not pts:
            log("parceiro: filas cheias — PC2 sem Short pra fazer")
            return None
        _LINGUAS_DA_VEZ = ",".join(ling)
        falta = [min(pts, key=lambda d: fila[d["canal"]] / max(1, _alvo(d)))]
        log(f"parceiro: filas pt cheias — Short pra {falta[0]['nome']} + versões em {_LINGUAS_DA_VEZ} (línguas com "
            "fila curta)")
    usados = _ler_feitos("_feitos_short.txt") | _ler_feitos("_feitos_short_attempted.txt") | _reservados()
    # 30/10 (D39): fonte sem vídeo novo (29/10 22:49 @grananerd) deixava o PC2 vazio a rodada inteira: tenta os próximos
    # canais da fila na mesma ordem de prioridade (até 3)
    # 13/11 (dona: "todos têm de estar sempre no máximo; resolver os gargalos"): olhava só os 3 canais do topo e
    # desistia — em 13/11 o PC2 teve 76 rodadas "sem vídeo novo" e o Kaggle 84, quase todas em 4 fontes do Fio da Meada
    # e no @score90, com outros 13 canais abaixo do estoque. Agora percorre TODOS os canais que faltam (na mesma ordem
    # de prioridade) e não consulta de novo, por FONTE_VAZIA_MIN (padrão 90 min), fonte que acabou de vir sem vídeo
    # novo (cada consulta gasta a vez do yt-dlp). ESCOLHER_SO_3=1 volta ao antigo.
    _max = 3 if os.environ.get("ESCOLHER_SO_3") == "1" else len(falta)
    vazias = _fontes_vazias()
    for alvo in sorted(falta, key=pdi._prioridade(pdi.itens(c), fila, c.get("fila_alvo", 2), c))[:_max]:
        # 09/11: a escolha ficava presa na fonte de maior peso (gplottwist09 pra Filme/CenaReact/Assist-IA, sem vídeo
        # novo há dias) e o canal era pulado — com 51 fontes novas autorizadas, sorteia de novo até 4 fontes distintas
        tentadas = set()
        for _ in range(8):
            escolha = pdi._escolher_fonte(c, alvo, evitar=tentadas | vazias)
            if escolha[0] in tentadas:
                break  # o nicho acabou (todas as fontes tentadas)
            tentadas.add(escolha[0])
            if escolha[0] in vazias:
                continue  # veio sem vídeo novo há pouco: não gasta outra consulta
            cand = next((x for x in anime_discover.discover_canal(escolha[0])
                         if x["id"] not in usados and _reservar(x["id"])), None)
            if cand:
                return alvo, escolha, cand
            log(f"parceiro: sem vídeo novo em {escolha[0]} ({alvo['nome']}) — tento outra fonte")
            _fonte_vazia_marcar(escolha[0])
            vazias.add(escolha[0])
            if len(tentadas) >= 4:
                break
        log(f"parceiro: {alvo['nome']}: {len(tentadas)} fonte(s) sem vídeo novo — tenta o próximo canal")
    log(f"parceiro: nenhum dos {min(_max, len(falta))} canais que faltam tem vídeo novo — sem Short pra fazer")
    return None


def _prontos_pc2():
    """[(pasta, meta)] dos Shorts preparados, mais velho primeiro. Velho (> PRONTO_MAX_H) ou já feito = apagado."""
    import shutil
    feitos = _ler_feitos("_feitos_short.txt")
    out = []
    for d in PRONTOS_PC2.glob("*"):  # preparo que caiu no meio (sem meta.json) e já passou de 1 h: lixo
        if d.is_dir() and not (d / "meta.json").exists() and time.time() - d.stat().st_mtime > 3600:
            shutil.rmtree(d, ignore_errors=True)
    for m in sorted(PRONTOS_PC2.glob("*/meta.json"), key=lambda p: p.stat().st_mtime):
        try:
            meta = json.loads(m.read_text(encoding="utf-8"))
            velho = time.time() - float(meta.get("quando", 0)) > PRONTO_MAX_H * 3600
            if velho or meta["cand"]["id"] in feitos or not any(m.parent.glob("*.mp4")):
                raise ValueError("velho/feito/sem vídeo")
            out.append((m.parent, meta))
        except (OSError, ValueError, KeyError):
            shutil.rmtree(m.parent, ignore_errors=True)
    return out


def _enviar_pronto_pc2(cand, pasta):
    """Manda pro workspace do PC2 os arquivos já preparados (o que o _prebaixar_pc2 fazia na hora). True se ok."""
    arquivos = [str(p) for p in sorted(pasta.glob("*.mp4")) + sorted(pasta.glob("cap*.vtt")) + [pasta / "cand.json"]
                if p.exists()]  # o mesmo que o _prebaixar_pc2 mandava (sem sobra do download)
    nome_pasta = f"{cand['id']}_{_slug(cand['title'])}"
    r_dir = f"C:/recapd-e-animes/workspace/anime/{nome_pasta}"
    _ssh(f'mkdir "{r_dir}"')
    cp = subprocess.run([_SCP, "-q", "-o", "BatchMode=yes", *arquivos, f"pc2:{r_dir}/"], capture_output=True,
                        timeout=300, creationflags=_SEM_JANELA)
    if cp.returncode != 0:
        log(f"[!] envio do preparado: SCP falhou: {(cp.stderr or b'').decode('utf-8', 'replace')[:200]}")
        return False
    log(f"prebaixar (preparado antes): {cand['id']} -> PC2:{r_dir}")
    return True


def encher_pilha(max_seg=600):
    """13/11: enche a pilha em PARALELO. Preparar 1 Short levava de 10 a 35 min (19:08-19:43: 2084 s) porque o PC1
    escolhia, pedia o download e ESPERAVA, um de cada vez — e a pilha de 5 nunca passava de 1. A fila de download de
    fora (manhwa-drive:baixador) é atendida por várias máquinas, cada uma com o seu IP (3 VPS + as sessões do Kaggle,
    kaggle_baixar): pedir N vídeos de uma vez = N baixando ao mesmo tempo, sem tocar no IP de casa.
    Escolhe os que faltam (mesma regra e mesma reserva de sempre), pede todos e recolhe o que chegar. Quem não chegar
    em `max_seg` volta pra fila (sai dos tentados). Sem baixador vivo = não faz nada (o preparo de 1 em 1 continua).
    PILHA_PARALELA=0 desliga. Devolve quantos entraram na pilha."""
    if os.environ.get("PILHA_PARALELA", "1") == "0" or PILHA_ALVO <= 1:
        return 0
    falta_n = PILHA_ALVO - len(_prontos_pc2())
    if falta_n <= 0 or shutil.disk_usage(str(BASE)).free / 1e9 < PILHA_DISCO_MIN_GB:
        return 0
    import concurrent.futures as cf
    import msvcrt
    sys.path.insert(0, str(PROD / "bin"))
    import anime_discover
    import kaggle_baixar
    import parceiro_diario as pdi
    c = pdi.cfg()
    if not c.get("ligado", True) or not kaggle_baixar.vivo(5):
        return 0
    # 13/11 20:07 (1º teste real): escolher os 5 SOB a trava do disparo segurou o PC2 por 10 min ("outro disparo pro
    # PC2 em andamento"). Agora a trava é pega e SOLTA a cada escolha (o disparo do PC2 entra no meio) e a escolha
    # inteira tem teto de PILHA_ESCOLHA_SEG (padrão 150 s): o que deu pra escolher nesse tempo é o que se pede.
    escolhidos = []
    limite = time.time() + float(os.environ.get("PILHA_ESCOLHA_SEG", "150"))
    for _ in range(falta_n):
        if time.time() > limite:
            break
        TRAVA_DISPARO_PC2.parent.mkdir(parents=True, exist_ok=True)
        f = open(TRAVA_DISPARO_PC2, "a+")
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            f.close()
            break  # um disparo está escolhendo agora: fica pra próxima rodada
        try:
            esc = _escolher_pc2(pdi, anime_discover, c)
            if not esc:
                break
            alvo, escolha, cand = esc
            with open(FEITOS / "_feitos_short_attempted.txt", "a", encoding="utf-8") as fa:
                fa.write(cand["id"] + chr(10))
            pasta = PRONTOS_PC2 / ("_baixando_" + cand["id"])
            shutil.rmtree(pasta, ignore_errors=True)
            pasta.mkdir(parents=True, exist_ok=True)
            # meta provisória: conta na fila do canal, pra próxima escolha desta mesma volta ir pra outro canal
            (pasta / "meta_parcial.json").write_text(json.dumps({"alvo": {"canal": alvo["canal"]}}), encoding="utf-8")
            escolhidos.append((alvo, escolha, cand, pasta))
        finally:
            try:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
            f.close()
        time.sleep(1)  # deixa o disparo do PC2 pegar a trava se estiver esperando
    if not escolhidos:
        return 0
    log(f"pilha: pedindo {len(escolhidos)} fonte(s) em paralelo aos baixadores de fora "
        f"({', '.join(x[2]['id'] for x in escolhidos)})")
    t0 = time.time()

    def _um(item):
        alvo, escolha, cand, pasta = item
        try:
            video, _legs = kaggle_baixar.baixar(cand["url"], cand["id"], pasta, timeout=max_seg, log=log)
        except Exception as e:  # noqa: BLE001
            log(f"[!] pilha: {cand['id']} falhou ({type(e).__name__}: {str(e)[:120]})")
            video = None
        return item, video

    entrou = 0
    with cf.ThreadPoolExecutor(max_workers=len(escolhidos)) as ex:
        for (alvo, escolha, cand, pasta), video in ex.map(_um, escolhidos):
            (pasta / "meta_parcial.json").unlink(missing_ok=True)
            if not video:
                tent = FEITOS / "_feitos_short_attempted.txt"
                try:
                    tent.write_text("".join(l + "\n" for l in tent.read_text(encoding="utf-8").split()
                                            if l != cand["id"]), encoding="utf-8")
                except OSError:
                    pass
                shutil.rmtree(pasta, ignore_errors=True)
                continue
            (pasta / "cand.json").write_text(json.dumps(cand, ensure_ascii=False), encoding="utf-8")
            (pasta / "meta.json").write_text(json.dumps(
                {"cand": cand, "alvo": {k: alvo[k] for k in ("nome", "handle", "canal")}, "fonte": escolha[0],
                 "tipo": escolha[1], "rodizio": escolha[2] if len(escolha) == 3 else None, "quando": time.time()},
                ensure_ascii=False), encoding="utf-8")
            try:
                pasta.rename(PRONTOS_PC2 / cand["id"])
                entrou += 1
            except OSError:
                shutil.rmtree(pasta, ignore_errors=True)
    log(f"pilha: {entrou} de {len(escolhidos)} chegaram em {round(time.time() - t0)} s "
        f"(pilha {len(_prontos_pc2())}/{PILHA_ALVO})")
    return entrou


def preparar_proximo_pc2():
    """AlimentarPC2 chama quando o PC2 está sem vaga (ou logo depois de disparar): deixa 1 Short pronto aqui. Mesma trava
    do disparo (não escolhe o mesmo vídeo que um disparo em andamento). True se preparou."""
    import msvcrt
    import shutil
    TRAVA_DISPARO_PC2.parent.mkdir(parents=True, exist_ok=True)
    f = open(TRAVA_DISPARO_PC2, "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        f.close()
        return False
    try:
        if len(_prontos_pc2()) >= max(1, PILHA_ALVO):
            return False  # pilha cheia
        if shutil.disk_usage(str(BASE)).free / 1e9 < PILHA_DISCO_MIN_GB:
            return False  # disco no fim: não empilha (quem dispara na hora ainda funciona)
        sys.path.insert(0, str(PROD / "bin"))
        import parceiro_diario as pdi
        import anime_discover
        import anime_fetch
        c = pdi.cfg()
        if not c.get("ligado", True) or _pc2_falhas() >= 3:
            return False
        esc = _escolher_pc2(pdi, anime_discover, c)
        if not esc:
            return False
        alvo, escolha, cand = esc
        with open(FEITOS / "_feitos_short_attempted.txt", "a", encoding="utf-8") as fa:
            fa.write(cand["id"] + "\n")  # reservado: ninguém escolhe o mesmo enquanto está preparado
        pasta = PRONTOS_PC2 / cand["id"]
        pasta.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        os.environ["YTDLP_PRIORIDADE"] = "pc2"  # 30/10 (D39): o download do PC2 passa na frente na vez do yt-dlp
        video, _extras = _fonte_para(cand, pasta, anime_fetch)
        if not video:
            log(f"[!] preparar: download falhou pra {cand['id']} — volta pra fila")
            tent = FEITOS / "_feitos_short_attempted.txt"
            tent.write_text("".join(l + "\n" for l in tent.read_text(encoding="utf-8").split() if l != cand["id"]),
                            encoding="utf-8")
            shutil.rmtree(pasta, ignore_errors=True)
            return False
        (pasta / "meta.json").write_text(json.dumps(
            {"cand": cand, "alvo": {k: alvo[k] for k in ("nome", "handle", "canal")}, "fonte": escolha[0],
             "tipo": escolha[1], "rodizio": escolha[2] if len(escolha) == 3 else None, "quando": time.time()},
            ensure_ascii=False), encoding="utf-8")
        log(f"preparado com antecedência: {cand['id']} pra {alvo['nome']} ({round(time.time() - t0)} s; pilha "
            f"{len(_prontos_pc2())}/{PILHA_ALVO})")
        return True
    finally:
        os.environ.pop("YTDLP_PRIORIDADE", None)
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        f.close()


def _disparar_parceiro_pc2():
    """Trava EXCLUSIVA em volta do disparo (30/10, D39): o controlador e o AlimentarPC2 dispararam o MESMO vídeo
    (mrXSE5iDdFc 01:48 e 01:50) porque a vez do fila_render deixa seguir depois de 72 s. Ocupada = não dispara agora."""
    import msvcrt
    TRAVA_DISPARO_PC2.parent.mkdir(parents=True, exist_ok=True)
    f = open(TRAVA_DISPARO_PC2, "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        f.close()
        log("parceiro: outro disparo pro PC2 em andamento — este não dispara (evita o mesmo vídeo 2x)")
        return False
    try:
        return _disparar_parceiro_pc2_travado()
    finally:
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        f.close()


def _disparar_parceiro_pc2_travado():
    """Escolhe AQUI o próximo vídeo do parceiro, o canal e a fonte do nicho dele (mesma regra do parceiro_diario) e
    manda o PC2 fazer. True se disparou."""
    sys.path.insert(0, str(PROD / "bin"))
    import parceiro_diario as pdi
    import anime_discover
    c = pdi.cfg()
    if not c.get("ligado", True):
        return False
    if _pc2_falhas() >= 3:
        log(f"parceiro: PC2 pausado (3 Shorts seguidos falharam lá — {PC2_FALHOU.name})")
        return False
    prontos = pegar_pronto("pc2")  # 13/11: pilha única — tira da pilha (PC3 e STI pegam da mesma)
    pasta_pronta = None
    if prontos:  # 30/10 (D39): preparado com antecedência pelo AlimentarPC2 = só enviar e rodar
        pasta_pronta, meta = prontos
        cand, alvo, fonte, tipo = meta["cand"], meta["alvo"], meta["fonte"], meta["tipo"]
        escolha = (fonte, tipo, meta["rodizio"]) if meta.get("rodizio") else (fonte, tipo)
    else:
        esc = _escolher_pc2(pdi, anime_discover, c)
        if not esc:
            return False
        alvo, escolha, cand = esc
        fonte, tipo = escolha[0], escolha[1]
    # o PC2 lê cobertura/narrador do config dele (o sincronizar_bin não copia config/)
    # 12/11: a tabela de vozes x nicho (narradores_nichos.json) vai junto no MESMO scp — antes só o parceiro.json ia e o
    # PC2 escolhia a voz pela tabela velha: os canais novos de negócios saíram com Pica-Pau e Chapolin
    cp = subprocess.run([_SCP, "-q", "-o", "BatchMode=yes", str(PROD / "config" / "parceiro.json"),
                         str(PROD / "config" / "narradores_nichos.json"),
                         *([str(PROD / "config" / "narradores_ajustado.json")]  # 13/11: ranking de voz ajustado
                           if (PROD / "config" / "narradores_ajustado.json").exists() else []),
                         "pc2:C:/recapd-e-animes/config/"], capture_output=True, timeout=120,
                        creationflags=_SEM_JANELA)
    if cp.returncode != 0:
        log(f"[!] não consegui copiar o parceiro.json pro PC2: {(cp.stderr or b'').decode('utf-8', 'replace')[:200]}")
        if pasta_pronta:
            devolver_pronto(pasta_pronta)
        return False
    # 30/10 (D39): falhou o envio/download = NÃO dispara. Antes seguia e o PC2 (SEM_YTDLP=1) tentava baixar sozinho,
    # falhava e somava "falha seguida" (04:22 kTRHBKY-oQI). Preparado que não foi: fica pra próxima; download que não
    # veio: o vídeo fica nos tentados (é dele, não da máquina).
    if pasta_pronta:
        if not _enviar_pronto_pc2(cand, pasta_pronta):
            log("[!] envio do Short preparado falhou — volta pra pilha")
            devolver_pronto(pasta_pronta)
            return False
    elif not _prebaixar_pc2(cand):
        log(f"[!] prebaixar falhou — {cand['id']} não vai pro PC2 (fica nos tentados)")
        with open(FEITOS / "_feitos_short_attempted.txt", "a", encoding="utf-8") as f:
            f.write(cand["id"] + "\n")
        return False
    if not pasta_pronta:  # o preparado já entrou nos tentados quando foi preparado
        with open(FEITOS / "_feitos_short_attempted.txt", "a", encoding="utf-8") as f:
            f.write(cand["id"] + "\n")  # o PC1 não pega o mesmo
    else:
        import shutil
        shutil.rmtree(pasta_pronta, ignore_errors=True)
    r = _ssh("powershell -NoProfile -ExecutionPolicy Bypass -File C:\\recapd-e-animes\\bin\\pc2_parceiro.ps1 "
             f"-Id {cand['id']} -Fonte {fonte} -Handle {alvo['handle']} -Canal {alvo['canal']} -Tipo {tipo}"
             + (f" -Idiomas {_LINGUAS_DA_VEZ}" if _LINGUAS_DA_VEZ else ""))
    saida = (r.stdout or b"").decode("utf-8", "replace").strip()
    if "rc 0" in saida:
        if len(escolha) == 3:
            pdi._rodizio_registrar(escolha[2])
        EST_PC2_DIR.mkdir(parents=True, exist_ok=True)
        (EST_PC2_DIR / f"{cand['id']}.json").write_text(json.dumps(
            {"id": cand["id"], "destino": alvo["nome"], "titulo": cand["title"],
             "inicio": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False), encoding="utf-8")
        try:
            ULTIMO_SHORT_PC2.write_text(str(time.time()), encoding="utf-8")  # longo_pc2_permitido conta daqui
        except OSError:
            pass
        log(f"PC2 livre -> PC2 faz o Short {cand['id']} [{tipo}] pra {alvo['nome']} ({saida})")
        return True
    # 28/10 09:00: ssh voltou vazio e o vídeo ficou nos tentados sem nunca rodar — volta pra fila e mostra o erro
    tent = FEITOS / "_feitos_short_attempted.txt"
    tent.write_text("".join(l + "\n" for l in tent.read_text(encoding="utf-8").split() if l != cand["id"]),
                    encoding="utf-8")
    erro = (r.stderr or b"").decode("utf-8", "replace").strip()
    log(f"[!] não consegui disparar no PC2 (rc {r.returncode}; {cand['id']} volta pra fila): {saida[:200]} {erro[:200]}")
    return False


# ─── PC3 (desktop) — 24/10 (dono: kanban, "colocar no PC3"; instalado por instalar_pc3.py) ───────────────────────
# Mesmo desenho do PC2 com voz clonada; o shell de lá é PowerShell (comandos por transferencias._ps_remoto), o Short
# pronto volta por scp (C:\pc3_shorts = junção pra "animes recap\shorts", sem espaço no caminho) e o PC3 NUNCA baixa:
# sem a fonte mandada daqui, não dispara.
EST_PC3 = BASE / "estado" / "pc3_parceiro.json"
PC3_FALHOU = BASE / "estado" / "pc3_parceiro_falhou.json"


def _pc3(script, timeout=300):
    import transferencias
    return transferencias._ps_remoto("desktop", script, timeout=timeout)


def _scp(*args, timeout=600):
    return subprocess.run([_SCP, "-q", "-r", "-o", "BatchMode=yes", *args], capture_output=True, timeout=timeout,
                          creationflags=_SEM_JANELA)


def pc3_instalado():
    # 27/10: o sshd do desktop "castiga" rajada de conexões (falhava 1 rodada sim, 1 não); "instalado" vale 12 h
    cache = BASE / "estado" / "pc3_instalado.json"
    try:
        if time.time() - float(json.loads(cache.read_text(encoding="utf-8"))["ok_em"]) < 12 * 3600:
            return True
    except (OSError, ValueError, KeyError):
        pass
    try:
        rc, txt = _pc3("Test-Path C:\\recapd-e-animes\\bin\\pc3_parceiro.ps1; "
                       "Test-Path D:\\hipercool-materiais\\python\\venv_vozes\\Scripts\\python.exe", timeout=60)
        ok = rc == 0 and txt.count("True") == 2
    except Exception:  # noqa: BLE001
        return False
    if ok:
        cache.write_text(json.dumps({"ok_em": time.time()}), encoding="utf-8")
    return ok


def _pc3_falhas():
    """12/11 (dona: "o desktop sempre para, quase não trabalha"): 3 falhas seguidas pausavam o PC3 ATÉ alguém apagar o
    arquivo — ficou parado de 09/11 05:04 a 11/11 08:25. Agora a pausa vale PC3_PAUSA_MIN (60): depois tenta de novo
    (1 Short; se falhar, mais 1 h). PC3_PAUSA_MIN=0 = como antes (só à mão)."""
    try:
        d = json.loads(PC3_FALHOU.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    pausa = float(os.environ.get("PC3_PAUSA_MIN", "60"))
    if pausa and int(d.get("seguidas", 3)) >= 3:
        try:
            desde = datetime.fromisoformat(d.get("quando"))
        except (TypeError, ValueError):
            desde = datetime.now()
        if (datetime.now() - desde).total_seconds() > pausa * 60:
            return 2  # passou a pausa: libera UMA tentativa (falhou de novo = 3 de novo e mais 1 h)
    return int(d.get("seguidas", 3))


def buscar_parceiro_pc3():
    """Short que o PC3 terminou -> pasta de postagem daqui (scp), apaga lá. True se ainda está fazendo."""
    try:
        est = json.loads(EST_PC3.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    vid = est["id"]
    logpc3 = f"C:\\recapd-e-animes\\logs\\pc3_parceiro_{vid}.log"
    # 03/11: o Short P6YLYnLzo7Y morreu lá às 20:29 sem .fim e o PC3 (a máquina mais livre) ficou 10 h "ainda fazendo".
    # Junto (1 conexão só): quantos min o log está parado. Parado > 90 min sem .fim = morreu, conta como falha.
    rc, txt = _pc3(f"Test-Path C:\\recapd-e-animes\\logs\\pc3_parceiro_{vid}.fim; "
                   f"try {{ [int]((Get-Date) - (Get-Item -LiteralPath '{logpc3}' -ErrorAction Stop).LastWriteTime)"
                   f".TotalMinutes }} catch {{ -1 }}", timeout=60)
    linhas = [x.strip() for x in txt.splitlines() if x.strip()]
    if "True" not in linhas[:1]:
        parado = int(linhas[1]) if len(linhas) > 1 and linhas[1].lstrip("-").isdigit() else -1
        if parado <= 90:
            log(f"PC3 ainda fazendo o Short {vid} ({est.get('destino')})")
            return True
        seguidas = _pc3_falhas() + 1
        PC3_FALHOU.write_text(json.dumps({"seguidas": seguidas, "id": vid, "log": logpc3, "motivo": "morreu sem .fim",
                                          "quando": datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")
        log(f"[!] PC3: o Short {vid} morreu sem terminar (log parado há {parado} min) — libero o PC3 "
            f"({seguidas}ª falha seguida; log {logpc3})")
        EST_PC3.unlink(missing_ok=True)
        return False
    rc, txt = _pc3("Get-ChildItem C:\\pc3_shorts -Directory | ForEach-Object Name", timeout=60)
    trouxe = False
    for p in [x.strip() for x in txt.splitlines() if x.strip()]:
        r = _scp(f"desktop:C:/pc3_shorts/{p}", str(SHORTS))
        if r.returncode == 0 and (SHORTS / p / "postar.json").exists():
            _pc3(f"Remove-Item -LiteralPath 'C:\\pc3_shorts\\{p}' -Recurse -Force", timeout=120)
            log(f"PC3 -> PC1: {p} trazido pra postagem")
            trouxe = True
        else:
            log(f"[!] falhou trazer {p} do PC3 (fica lá): {(r.stderr or b'').decode('utf-8', 'replace')[:200]}")
    if trouxe:
        with open(FEITOS / "_feitos_short.txt", "a", encoding="utf-8") as f:
            f.write(vid + "\n")
        PC3_FALHOU.unlink(missing_ok=True)
        sys.path.insert(0, str(PROD / "bin"))
        import parceiro_diario
        parceiro_diario.disparar_postagem()
    else:
        # 12/11: "SEM_YTDLP" aparece em TODO log do PC3 (é o modo normal: a fonte vem do PC1) — casava sempre e todo
        # vídeo era tratado como falha da máquina. Agora só o erro de verdade ("SEM_YTDLP: ... não", proxy, TTS).
        rc, txt = _pc3(f"Select-String -Path '{logpc3}' -Pattern 'pool de proxies','TTS falhou','SEM_YTDLP=1 e sem' "
                       "-SimpleMatch | Select-Object -First 1", timeout=60)
        if txt.strip():  # falha da máquina: o vídeo volta pra fila
            tent = FEITOS / "_feitos_short_attempted.txt"
            tent.write_text("".join(l + "\n" for l in tent.read_text(encoding="utf-8").split() if l != vid), encoding="utf-8")
        # 12/11 (dona: "o desktop sempre para"): vídeo SEM FALA (roteiro de 1 frase / sem transcrição) é defeito do
        # VÍDEO, não do desktop — 3 desses pausaram o PC3 por 2 dias. Não conta. PC3_FALHA_VIDEO_NAO_CONTA=0 volta.
        rc2, conteudo = _pc3(f"Select-String -Path '{logpc3}' -Pattern 'roteiro com 1 frase','roteiro com 0 frase',"
                             "'sem transcrição disponível' -SimpleMatch | Select-Object -First 1", timeout=60)
        if conteudo.strip() and os.environ.get("PC3_FALHA_VIDEO_NAO_CONTA", "1") != "0":
            log(f"PC3: o Short {vid} não saiu por causa do VÍDEO (sem fala) — não conta como falha do PC3")
            EST_PC3.unlink(missing_ok=True)
            return False
        seguidas = _pc3_falhas() + 1
        PC3_FALHOU.write_text(json.dumps({"seguidas": seguidas, "id": vid, "log": logpc3,
                                          "quando": datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")
        log(f"[!] PC3 terminou o Short {vid} SEM vídeo ({seguidas}ª falha seguida; log {logpc3})"
            + (f" — PC3 pausado pro parceiro até apagar {PC3_FALHOU.name}" if seguidas >= 3 else ""))
    EST_PC3.unlink(missing_ok=True)
    return False


def disparar_parceiro_pc3():
    """Escolhe AQUI o próximo vídeo/canal/fonte (mesma regra do PC2), baixa a fonte AQUI, manda pro PC3 e dispara o
    pc3_parceiro.ps1. Devolve o rótulo do que disparou; levanta RuntimeError com o motivo quando não dá."""
    if buscar_parceiro_pc3():
        raise RuntimeError("o PC3 ainda está fazendo o Short anterior")
    if _pc3_falhas() >= 3:
        raise RuntimeError(f"PC3 pausado pro parceiro: 3 Shorts seguidos falharam lá ({PC3_FALHOU.name})")
    sys.path.insert(0, str(PROD / "bin"))
    import parceiro_diario as pdi
    import anime_discover
    import anime_fetch
    import tempfile
    import shutil
    c = pdi.cfg()
    # 04/11: o PC3 tentava UM canal só (o 1º da prioridade) e, sem vídeo novo nele (@thalisshortsbr, a noite toda), o
    # desktop ficava parado com CPU 0%. Mesma escolha do PC2: até 3 canais na ordem de prioridade, fonte já reservada.
    pronto = pegar_pronto("pc3") if PILHA_ALVO > 1 else None  # 13/11: pilha única (já baixado = dispara em segundos)
    if pronto:
        tmp, meta = pronto
        cand, alvo = meta["cand"], meta["alvo"]
        escolha = (meta["fonte"], meta["tipo"], meta["rodizio"]) if meta.get("rodizio") else (meta["fonte"], meta["tipo"])
        log(f"PC3 pega da pilha: {cand['id']} pra {alvo['nome']}")
    else:
        esc = _escolher_pc2(pdi, anime_discover, c)
        if not esc:
            raise RuntimeError("nenhum canal que falta tem vídeo novo (ou filas cheias)")
        alvo, escolha, cand = esc
        tmp = Path(tempfile.mkdtemp(prefix="prebaixar_pc3_"))
    fonte, tipo = escolha[0], escolha[1]
    try:
        if pronto:
            video = next(iter(sorted(tmp.glob("*.mp4"))), None)
        else:
            video = anime_fetch.download_video(cand["url"], tmp)  # baixa AQUI (vez do yt-dlp do PC1)
        if not video:
            raise RuntimeError(f"a fonte {cand['id']} não baixou aqui — o PC3 não baixa, não dispara")
        r_dir = f"C:/recapd-e-animes/workspace/anime/{cand['id']}_{_slug(cand['title'])}"
        _pc3(f"New-Item -ItemType Directory -Force '{r_dir}' | Out-Null", timeout=60)
        # 27/10: 1 scp só (eram 4 conexões seguidas + as outras = castigo do sshd do desktop); o parceiro.json vai junto
        # e o disparo abaixo move ele pro config
        shutil.copy2(PROD / "config" / "parceiro.json", tmp / "parceiro.json")
        # 12/11: a tabela de vozes x nicho vai no mesmo scp (o PC3 escolhia a voz pela tabela velha — Pica-Pau em negócios)
        shutil.copy2(PROD / "config" / "narradores_nichos.json", tmp / "narradores_nichos.json")
        extras = (sorted(tmp.glob("cap*.vtt")) + [tmp / "cand.json"]) if pronto else _extras_pc1(cand, tmp, anime_fetch)
        cp = _scp(str(video), *[str(p) for p in extras if Path(p).exists()], str(tmp / "parceiro.json"),
                  str(tmp / "narradores_nichos.json"), f"desktop:{r_dir}/", timeout=900)
        if cp.returncode != 0:
            if pronto:
                for sobra in ("parceiro.json", "narradores_nichos.json"):
                    (tmp / sobra).unlink(missing_ok=True)
                devolver_pronto(tmp)
            raise RuntimeError(f"scp pro PC3 falhou: {(cp.stderr or b'').decode('utf-8', 'replace')[:200]}")
    finally:
        if not (pronto and not tmp.exists()):
            shutil.rmtree(tmp, ignore_errors=True)
    if not pronto:  # o preparado já entrou nos tentados quando foi preparado
        with open(FEITOS / "_feitos_short_attempted.txt", "a", encoding="utf-8") as f:
            f.write(cand["id"] + "\n")
    rc, saida = _pc3(f"Move-Item -Force '{r_dir}/parceiro.json' 'C:/recapd-e-animes/config/parceiro.json'; "
                     f"Move-Item -Force '{r_dir}/narradores_nichos.json' 'C:/recapd-e-animes/config/narradores_nichos.json'; "
                     # 02/11: a ExecutionPolicy do desktop está Undefined (= Restricted): "& script.ps1" era bloqueado e
                     # o disparo voltava vazio ("não aceitou"). Bypass só nesta execução, sem mexer na política da máquina.
                     "powershell -NoProfile -ExecutionPolicy Bypass -File C:\\recapd-e-animes\\bin\\pc3_parceiro.ps1 "
                     f"-Id '{cand['id']}' -Fonte '{fonte}' -Handle '{alvo['handle']}' -Canal '{alvo['canal']}' -Tipo '{tipo}'"
                     + (f" -Idiomas '{_LINGUAS_DA_VEZ}'" if _LINGUAS_DA_VEZ else ""))
    if "rc 0" not in saida:
        raise RuntimeError(f"o PC3 não aceitou o disparo: {saida.strip()[:200]}")
    if len(escolha) == 3:
        pdi._rodizio_registrar(escolha[2])
    EST_PC3.write_text(json.dumps({"id": cand["id"], "destino": alvo["nome"], "titulo": cand["title"],
                                   "inicio": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False),
                       encoding="utf-8")
    log(f"PC3 faz o Short {cand['id']} [{tipo}] pra {alvo['nome']} ({saida.strip()})")
    return f"Cortes: Short {cand['id']} pra {alvo['nome']} no PC3"


def main():
    if DESLIGADO.exists():
        log("desligado (OCIOSO_DESLIGADO.json)")
        return
    try:
        import controle  # liga/desliga único (mesma pasta)
        ok, motivo = controle.ligado("anime", "producao")
    except Exception:  # noqa: BLE001
        ok, motivo = True, ""
    if not ok:
        log(f"desligado: {motivo}")
        return
    ok, recado = pc2_recapd.sincronizar_bin()
    log(recado)
    todos = maquinas.medir_todos()  # os 3 PCs (dono 17/10); o desktop só com OBS/editor fechados
    log(" | ".join(f"{h}: {'LIVRE' if x.get('ocioso') else 'ocupado'} ({x.get('motivo')})" for h, x in todos.items()))
    # PC2 livre faz Short de parceiro mesmo com o PC1 livre (dono 18/10: "produção máxima pra alimentar esses canais";
    # antes só ia pro PC2 se o PC1 estivesse ocupado). Prioridade sobre o anime longo (sem canal ainda).
    _buscar_parceiro_pc2()
    import fila_render  # vez do PC2 (18/10): o hipercool (fila.py pc2) e este despacho não disparam juntos lá
    if pc2_vaga_short()[0]:  # 27/10: até 3 Shorts juntos no PC2
        with fila_render.vez("parceiro", "disparo de Short no PC2", espera_max_h=0.25, maquina="pc2"):
            if pc2_vaga_short()[0] and _disparar_parceiro_pc2():
                return
    if ok and todos["pc2"].get("ocioso"):  # ok = o bin do PC2 sincronizou
        disparar_anime_longo()


ULTIMO_SHORT_PC2 = BASE / "estado" / "pc2_ultimo_short.txt"  # hora do último Short disparado no PC2
LONGO_PC2_SEM_SHORT_MIN = 30


def longo_pc2_permitido():
    """(True/False, motivo). 27/10 (dona): recap longo só nas GPUs; 30/10 (dona): "na pior das hipóteses, pra não ficar
    parado, fazer os vídeos longos que iriam pra GPU". Longo no PC2 só como reserva: nenhum Short rodando nem
    preparado, nenhum Short disparado há LONGO_PC2_SEM_SHORT_MIN min e o yt-dlp sem pausa (o longo também baixa a fonte
    aqui). ANIME_LONGO_PC2=1 libera sempre (como antes)."""
    if os.environ.get("ANIME_LONGO_PC2") == "1":
        return True, "ANIME_LONGO_PC2=1"
    if _pc2_estados():
        return False, "Short rodando no PC2"
    if _prontos_pc2():
        return False, "tem Short preparado pro PC2"
    try:
        ultimo = float(ULTIMO_SHORT_PC2.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        ultimo = 0.0
    parado_min = (time.time() - ultimo) / 60
    if parado_min < LONGO_PC2_SEM_SHORT_MIN:
        return False, f"último Short no PC2 há {parado_min:.0f} min (< {LONGO_PC2_SEM_SHORT_MIN})"
    try:
        sys.path.insert(0, str(PROD / "bin"))
        import ytdlp_vez
        if ytdlp_vez.pausado():
            return False, "yt-dlp em pausa (o longo também precisa baixar a fonte)"
    except Exception:  # noqa: BLE001
        pass
    return True, f"PC2 sem Short há {parado_min:.0f} min — longo de reserva"


def disparar_anime_longo():
    """1 anime longo no PC2 (o PC1 acha o anime e escreve o roteiro, o PC2 renderiza). True se disparou.
    19/10: o controlador geral (controlador.py) chama isto quando a vez do PC2 é do anime longo."""
    import fila_render
    # 27/10 (dona): recap longo SÓ nas GPUs do Kaggle; a CPU do PC2 é pros Shorts. 30/10: reserva quando o PC2 está
    # parado sem Short (longo_pc2_permitido). Trava aqui pega todo caminho (controlador e o fim do main deste arquivo).
    ok, motivo = longo_pc2_permitido()
    if not ok:
        log(f"anime longo não roda no PC2 agora ({motivo})")
        return False
    log(f"anime longo no PC2: {motivo}")
    if _deitado_rodando():
        log("anime longo já em andamento — espera")
        return False
    with fila_render.vez("anime", "disparo de anime longo no PC2", espera_max_h=0.25, maquina="pc2"):
        m = maquinas.medir("pc2")  # de novo, já com a vez: alguém pode ter disparado enquanto este mediu
        if not m.get("ocioso"):
            log(f"PC2 deixou de estar livre ({m.get('motivo')}) — anime longo espera")
            return False
        logf = PROD / "logs" / f"anime_ocioso_{datetime.now():%Y%m%d}.log"
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", ANIME_DESTINO="drive")
        with open(logf, "a", encoding="utf-8") as fh:
            proc = subprocess.Popen([str(PROD / "venv" / "Scripts" / "python.exe"), "-X", "utf8",
                                     str(PROD / "bin" / "anime_auto.py"),
                                     "--modo", "deitado", "--engine", "worker", "--limit", "1", "--top", "5"],
                                    cwd=str(PROD / "bin"), env=env, stdout=fh, stderr=subprocess.STDOUT,
                                    creationflags=_SEM_JANELA | _DETACHED | 0x00004000)
        # o anime_auto acha o anime e escreve o roteiro AQUI antes de mandar o render pro PC2 (minutos): até ele
        # morrer, o PC2 conta como ocupado pro medidor comum
        fila_render.marcar("anime", "anime longo (modo ocioso)", proc.pid, "pc2")
    log(f"PC2 ocioso -> disparei 1 anime longo (log {logf.name})")
    return True


if __name__ == "__main__":
    main()
