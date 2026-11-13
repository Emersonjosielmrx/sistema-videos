"""faxina.py — libera disco nos PCs SEM PERDER NADA (dono, 22/10/2026).

Pedido do dono: "limpezas periódicas que desocupem espaço; se na hora do vídeo estiver cheio, adianta a limpeza;
NUNCA limpar logins/cookies do Chrome; códigos mortos e testes vão se acumulando; NA DÚVIDA, MOVER PRO DRIVE em vez
de apagar; cuidado: o Kiro/vigia já apagou coisa sem conferir que foi pro Drive e perdemos muito".

Por isso aqui NÃO há agente nem LLM — só regras fixas, e cada arquivo segue UMA destas saídas:
  - DRIVE (o padrão): copia pro Drive, CONFERE no Drive (tamanho + md5 lidos de lá) e SÓ ENTÃO apaga do PC.
    Qualquer divergência = o arquivo FICA no PC. Destino: manhwa-drive:faxina/<pc>/<caminho original>.
  - APAGAR: só o que é regenerável com certeza — vídeo-FONTE baixado do YouTube (cópia de vídeo público) de job JÁ
    ENCERRADO, intermediário de render e download pela metade. Fica registrado (id do YouTube) no log.
Trava dura: caminho com logins-google / chrome / cofre / perfis / secrets / cookies / Login Data / .git / venv /
models / amostras_voz é IGNORADO por qualquer regra (nem lista).

    python faxina.py                 # rodada normal (o vigia geral chama a cada 6 h)
    python faxina.py --simular       # só mostra o que faria
    python faxina.py --urgente       # disco apertado: idades menores + backup dos postados na hora
Registro de tudo: D:\\video-fila\\logs\\faxina.jsonl (recuperar do Drive: rclone copyto <drive> <local>).
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG = BASE / "logs" / "faxina.jsonl"
RCLONE = r"D:\tools\rclone.exe"
REMOTO = "manhwa-drive:faxina/pc1"
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DIA = 86400
MIN_LIVRE_GB = {"D:\\": 15, "C:\\": 8}  # abaixo disso a rodada vira --urgente sozinha

PROIBIDO = ("logins-google", "chrome", "cofre", "perfis", "secrets", "cookies", "login data", "\\.git",
            "\\venv", "\\.venv", "\\models\\", "amostras_voz", "\\python\\venv")

ANIME = Path(r"D:\hipercool-materiais\anime")
FONTE_NOMES = ("source.mp4", "source.webm", "source.mkv", "source_reed.mp4")
INTERMEDIARIOS = ("_semlegenda", "_subs_batch", ".temp.", ".part", ".f39", ".f40", ".ytdl")
TESTES = [Path(r"D:\tmp")]
CODIGO = [Path(r"D:\recapd-ambientes\producao\bin"), Path(r"D:\hipercool-videos\bin"),
          Path(r"D:\postador-de-videos\bin"), Path(r"D:\manhwa-react\mr"), Path(r"D:\video-fila"),
          Path(r"D:\historias-em-frames\bin"), Path(r"D:\veo\beta"), Path(r"D:\veo\beta\pos_producao")]
BACKUP_PADRAO = (".bkp_", ".bak_", ".bak-", ".antes_", ".orig_")


def log(msg):
    print(f"[faxina {time.strftime('%d/%m %H:%M')}] {msg}", flush=True)


def _registrar(**kw):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"em": time.strftime("%Y-%m-%dT%H:%M:%S"), **kw}, ensure_ascii=False) + "\n")


def _proibido(p):
    s = str(p).lower()
    return any(x in s for x in PROIBIDO)


def _livre_gb(raiz):
    try:
        return shutil.disk_usage(raiz).free / 1e9
    except OSError:
        return 999.0


def _em_uso(f):
    """Arquivo aberto por outro processo (render/upload em andamento)? No Windows não dá pra renomear arquivo aberto."""
    tmp = f.with_name(f.name + ".faxina_teste")
    try:
        os.rename(f, tmp)
        os.rename(tmp, f)
        return False
    except OSError:
        return True


def _md5(f):
    h = hashlib.md5()
    with open(f, "rb") as fh:
        for bloco in iter(lambda: fh.read(4 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _rclone(*args, timeout=3600):
    r = subprocess.run([RCLONE, *args], capture_output=True, text=True, timeout=timeout, encoding="utf-8",
                       errors="replace", creationflags=SEM_JANELA)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _pro_drive(f, simular, motivo):
    """Copia -> confere NO DRIVE (tamanho + md5 lidos do remoto) -> só então apaga do PC. True se saiu do PC."""
    if _proibido(f) or not f.is_file():
        return False
    rel = str(f.resolve()).replace(":", "").replace("\\", "/")
    alvo = f"{REMOTO}/{rel}"
    tam = f.stat().st_size
    if simular:
        log(f"  [simular] DRIVE {f} ({tam / 1e6:.0f} MB) — {motivo}")
        return False
    if _em_uso(f):
        log(f"  em uso, fica: {f.name}")
        return False
    md5 = _md5(f)
    rc, msg = _rclone("copyto", str(f), alvo, timeout=600 + int(tam / 50e3))
    if rc:
        log(f"  [!] cópia falhou, fica no PC: {f.name} ({msg[-150:]})")
        return False
    rc, saida = _rclone("lsjson", "--hash", alvo, timeout=300)
    try:
        info = json.loads(saida)[0]
        ok = int(info.get("Size", -1)) == tam and (info.get("Hashes") or {}).get("md5", "").lower() == md5
    except (ValueError, IndexError, TypeError):
        ok = False
    if not ok:
        log(f"  [!] conferência no Drive FALHOU, fica no PC: {f.name}")
        _registrar(acao="mantido", arquivo=str(f), motivo="conferência falhou")
        return False
    f.unlink()
    _registrar(acao="drive", arquivo=str(f), drive=alvo, bytes=tam, md5=md5, motivo=motivo)
    return True


LOTE_MAX_BYTES = 20e6  # 23/10: arquivo pequeno vai em lote (antes: ~1 min por arquivo, 71 backups de código = 1 h+)


def _pro_drive_lote(arquivos, simular, motivo):
    """Mesma garantia do _pro_drive (copia, confere tamanho + md5 NO DRIVE e só então apaga), mas com UMA cópia e UMA
    conferência do rclone pra todos os arquivos pequenos do D:. Devolve os bytes que saíram do PC."""
    import tempfile
    lista, liberado = {}, 0
    for f in arquivos:
        if _proibido(f) or not f.is_file():
            continue
        r = f.resolve()
        if r.drive.upper() != "D:":  # fora do D: (junção pra outro disco): vai sozinho, do jeito antigo
            tam = f.stat().st_size
            liberado += tam if _pro_drive(f, simular, motivo) else 0
            continue
        if _em_uso(f):
            log(f"  em uso, fica: {f.name}")
            continue
        lista[r.relative_to("D:\\").as_posix()] = (f, f.stat().st_size)
    if not lista:
        return liberado
    if simular:
        for f, tam in lista.values():
            log(f"  [simular] DRIVE {f} ({tam / 1e6:.0f} MB) — {motivo} (lote)")
        return liberado
    with tempfile.TemporaryDirectory() as tmp:
        arq, comb = Path(tmp) / "lista.txt", Path(tmp) / "conferencia.txt"
        arq.write_text("\n".join(lista), encoding="utf-8")
        rc, msg = _rclone("copy", "D:\\", f"{REMOTO}/D", "--files-from", str(arq), "--no-traverse")
        if rc:
            log(f"  [!] cópia do lote falhou, tudo fica no PC ({msg[-150:]})")
            return liberado
        _rclone("check", "D:\\", f"{REMOTO}/D", "--files-from", str(arq), "--one-way", "--combined", str(comb))
        iguais = {l[2:].strip() for l in (comb.read_text(encoding="utf-8", errors="replace").splitlines()
                                          if comb.exists() else []) if l.startswith("= ")}
    for rel, (f, tam) in lista.items():
        if rel in iguais and f.is_file() and f.stat().st_size == tam:
            f.unlink()
            liberado += tam
            _registrar(acao="drive", arquivo=str(f), drive=f"{REMOTO}/D/{rel}", bytes=tam, motivo=f"{motivo} (lote)")
        else:
            log(f"  [!] conferência no Drive FALHOU, fica no PC: {f.name}")
            _registrar(acao="mantido", arquivo=str(f), motivo="conferência do lote falhou")
    return liberado


def _apagar(f, simular, motivo):
    if _proibido(f) or not f.is_file():
        return False
    tam = f.stat().st_size
    if simular:
        log(f"  [simular] APAGA {f} ({tam / 1e6:.0f} MB) — {motivo}")
        return False
    if _em_uso(f):
        return False
    f.unlink()
    _registrar(acao="apagado", arquivo=str(f), bytes=tam, motivo=motivo)
    return True


def _encerrados():
    ids = set()
    for nome in ("_feitos_short.txt", "_feitos_short_attempted.txt", "_feitos_deitado.txt",
                 "_feitos_deitado_attempted.txt"):
        try:
            ids |= {l.strip()[:11] for l in (ANIME / nome).read_text(encoding="utf-8", errors="replace").splitlines()
                    if l.strip() and not l.startswith("#")}
        except OSError:
            pass
    return ids


def regra_anime(simular, urgente):
    """Pastas de job do anime/parceiro: fonte (cópia de vídeo público) e intermediários de job ENCERRADO saem; o
    Short pronto do layout antigo (final_anime_short.mp4, produto nosso) vai pro DRIVE."""
    enc, agora = _encerrados(), time.time()
    idade_fonte = 2 * 3600 if urgente else DIA
    idade_final = DIA if urgente else 3 * DIA
    liberado = 0
    for pasta in ANIME.iterdir() if ANIME.exists() else []:
        if not pasta.is_dir() or pasta.name[:11] not in enc:
            continue
        for f in pasta.iterdir():
            if not f.is_file():
                continue
            try:
                idade, tam = agora - f.stat().st_mtime, f.stat().st_size
            except OSError:
                continue
            nome = f.name.lower()
            if (nome in FONTE_NOMES or any(x in nome for x in INTERMEDIARIOS)) and idade > idade_fonte:
                if _apagar(f, simular, f"fonte/intermediário de job encerrado {pasta.name[:11]} (cópia do YouTube)"):
                    liberado += tam
            elif nome == "final_anime_short.mp4" and idade > idade_final and not _RAPIDA:
                if _pro_drive(f, simular, "Short pronto do layout antigo (produto nosso)"):
                    liberado += tam
    return liberado


def regra_testes(simular, urgente):
    """D:\\tmp: testes soltos. Tudo que passou da idade vai pro DRIVE (nunca apagado)."""
    idade_min, agora, liberado, pequenos = (2 if urgente else 7) * DIA, time.time(), 0, []
    for raiz in TESTES:
        for f in raiz.rglob("*") if raiz.exists() else []:
            try:
                if f.is_file() and agora - f.stat().st_mtime > idade_min and f.stat().st_size > 50e3:
                    tam = f.stat().st_size
                    if tam <= LOTE_MAX_BYTES:
                        pequenos.append(f)
                    elif _pro_drive(f, simular, "teste/arquivo solto em D:\\tmp"):
                        liberado += tam
            except OSError:
                continue
    return liberado + _pro_drive_lote(pequenos, simular, "teste/arquivo solto em D:\\tmp")


def regra_codigo_morto(simular, urgente):
    """Backups de código (.bkp_/.bak_/.antes_) com mais de 10 dias e pastas bin_bkp_*: DRIVE."""
    idade_min, agora, liberado, pequenos = (5 if urgente else 10) * DIA, time.time(), 0, []
    for raiz in CODIGO:
        if not raiz.exists():
            continue
        for f in list(raiz.glob("*")) + list(raiz.glob("*_bkp_*/**/*")):
            try:
                if not f.is_file():
                    continue
                # a cópia herda a data do ORIGINAL (Copy-Item/copy2): um backup feito hoje parecia velho. A idade
                # vem da data no NOME (bkp_20261022...) quando existe — o backup recente fica perto pra desfazer.
                import re as _re
                m = _re.search(r"(20\d{6})", f.name) or _re.search(r"(20\d{6})", str(f.parent.name))
                try:
                    criado = time.mktime(time.strptime(m.group(1), "%Y%m%d")) if m else f.stat().st_mtime
                except ValueError:
                    criado = f.stat().st_mtime
                if agora - criado < idade_min:
                    continue
                if not (any(x in f.name for x in BACKUP_PADRAO) or "_bkp_" in str(f.parent)):
                    continue
                tam = f.stat().st_size
                if tam <= LOTE_MAX_BYTES:
                    pequenos.append(f)
                elif _pro_drive(f, simular, "backup de código antigo"):
                    liberado += tam
            except OSError:
                continue
    return liberado + _pro_drive_lote(pequenos, simular, "backup de código antigo")


_PS_PC2 = r"""
$antes = (Get-PSDrive C).Free; $agora = Get-Date; $lib = 0
Get-ChildItem "$env:TEMP" -Directory -Filter 'anime_worker_*' -Force -ErrorAction SilentlyContinue | ForEach-Object {
  $arqs = @(Get-ChildItem $_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue)
  $ult = ($arqs | Measure-Object LastWriteTime -Maximum).Maximum; if (-not $ult) { $ult = $_.LastWriteTime }
  $h = ($agora - $ult).TotalHours
  if ($h -lt 6) { return }
  $finais = @($arqs | Where-Object { $_.Name -like 'final_anime_*' })
  # 27/10 (dona: "coloque no Drive os vídeos feitos lá"): final parado há 6 h+ = o PC1 desistiu de buscar (reenvio
  # do longo a cada ~2 h, 3 cópias de 4-5 GB) -> vai pro Drive (rclone só apaga depois de conferir) e a pasta sai
  $rc = 'C:\hipercool-materiais\tools\rclone.exe'
  if ($finais.Count -gt 0 -and (Test-Path $rc)) {
    foreach ($f in $finais) {
      $dest = 'manhwa-drive:videos-backup/recap-longos-pc2/' + $f.LastWriteTime.ToString('yyyy-MM-dd_HHmm') + '_' + $_.Name + '_' + $f.Name
      if ('__SIM__' -ne '1') { & $rc --config 'C:\hipercool-materiais\tools\rclone.conf' moveto $f.FullName $dest --checksum 2>$null }
      if (-not (Test-Path $f.FullName)) { $lib += $f.Length; 'DRIVE ' + $dest }
    }
    $finais = @($finais | Where-Object { Test-Path $_.FullName })
  }
  if ($finais.Count -gt 0 -and $h -lt 72) {
    $arqs | Where-Object { $_.Name -notlike 'final_anime_*' -and $_.Name -ne 'roteiro.txt' } | ForEach-Object { $lib += $_.Length; if ('__SIM__' -ne '1') { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue } }
  } else { $lib += ($arqs | Measure-Object Length -Sum).Sum; if ('__SIM__' -ne '1') { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue } }
}
'{0}|{1:N1}|{2:N1}' -f $lib, ($antes/1GB), ((Get-PSDrive C).Free/1GB)
"""


def regra_pc2(simular, urgente):
    """PC2 (ssh pc2): pastas de trabalho do worker de anime (TEMP\\anime_worker_*) que ficaram de job que FALHOU —
    juntou 16,8 GB em 22/10. Sem escrita há 6 h = intermediários saem; vídeo final fica até 3 dias pro PC1 buscar.
    (O worker também varre sozinho a cada tarefa nova, depois que reinicia com o código de 22/10.)"""
    import base64
    ps = _PS_PC2.replace("__SIM__", "1" if simular else "0")
    enc = base64.b64encode(ps.encode("utf-16-le")).decode()
    ssh = r"C:\Program Files\Git\usr\bin\ssh.exe" if Path(r"C:\Program Files\Git\usr\bin\ssh.exe").exists() else "ssh"
    try:
        r = subprocess.run([ssh, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "pc2",
                            f"powershell -NoProfile -EncodedCommand {enc}"], capture_output=True, timeout=1200,
                           creationflags=SEM_JANELA)
        saida = (r.stdout or b"").decode("utf-8", "replace").splitlines()
        for l in saida:
            if l.startswith("DRIVE "):
                log(f"  PC2: vídeo pronto -> {l[6:]}")
                _registrar(acao="drive", arquivo="pc2:" + l[6:].rsplit("/", 1)[-1], drive=l[6:], motivo="final do PC2 parado 6 h+")
        linha = [l for l in saida if l.count("|") == 2][-1]
        lib, antes, depois = linha.split("|")
        log(f"  PC2: {'[simular] ' if simular else ''}{float(lib) / 1e9:.2f} GB de pastas paradas do worker | livre C: "
            f"{antes} -> {depois} GB")
        if not simular and float(lib) > 0:
            _registrar(acao="pc2_worker_temp", bytes=float(lib), motivo="pastas anime_worker_* paradas há 6 h+")
        return 0 if simular else float(lib)
    except Exception as e:  # noqa: BLE001 — PC2 desligado/sem rede: segue
        log(f"  PC2: não deu pra varrer ({type(e).__name__})")
        return 0


CCV = Path(r"D:\claude-code-video")


def regra_claude_code_video(simular, urgente):
    """29/10 (dona: "não está colocando os vídeos no Drive? estamos quase sem espaço"): Claude Code Video. Trabalho
    ENCERRADO (pronto/falhou/voz_proibida) vai inteiro pro DRIVE menos o estado.json (gerar.py lê os títulos feitos e o
    rodízio de vozes dele); vídeo pronto de saida\\ vai pro DRIVE depois da idade (o último fica em ULTIMO_VIDEO)."""
    agora, liberado, pequenos = time.time(), 0, []
    idade_trab = 2 * 3600 if urgente else DIA
    idade_saida = DIA if urgente else 3 * DIA

    def _mandar(f, motivo):
        nonlocal liberado
        tam = f.stat().st_size
        if tam <= LOTE_MAX_BYTES:
            pequenos.append(f)
        elif _pro_drive(f, simular, motivo):
            liberado += tam

    for est in (CCV / "trabalhos").glob("*/estado.json"):
        try:
            status = json.loads(est.read_text("utf-8")).get("status")
        except (OSError, ValueError):
            continue
        if status not in ("pronto", "falhou", "voz_proibida") or agora - est.stat().st_mtime < idade_trab:
            continue
        for f in est.parent.rglob("*"):
            if not f.is_file() or f == est:
                continue
            partes = f.relative_to(est.parent).parts
            # quadros do júri, cópias da pasta pública, áudio do clone e quadros de cada rodada: regeneráveis (29/10:
            # eram 115 de 162 MB por trabalho) -> apaga; o resto (vídeo, imagens, vozes, melhor.mp4) vai pro Drive
            if partes[0] in ("quadros", "public", "clone") or (partes[0] == "lapidar" and len(partes) > 2):
                tam = f.stat().st_size
                if _apagar(f, simular, f"claude-code-video: intermediário de trabalho encerrado {est.parent.name}"):
                    liberado += tam
            else:
                _mandar(f, f"claude-code-video: trabalho encerrado ({status}) {est.parent.name}")
    for f in (CCV / "saida").rglob("*"):
        if f.is_file() and agora - f.stat().st_mtime > idade_saida:
            _mandar(f, "claude-code-video: vídeo pronto (saida)")
    return liberado + _pro_drive_lote(pequenos, simular, "claude-code-video")


def regra_postados_ja(simular):
    """Urgente: o backup dos POSTADOS (manhwa-react\\scripts\\backup_drive.py, que já confere tamanho+md5) roda na hora."""
    if simular:
        log("  [simular] rodaria o backup_drive.py (postados -> Drive)")
        return 0
    antes = _livre_gb("D:\\")
    try:
        subprocess.run([r"D:\manhwa-react\.venv\Scripts\python.exe", r"D:\manhwa-react\scripts\backup_drive.py"],
                       capture_output=True, timeout=3 * 3600, creationflags=SEM_JANELA,
                       env=dict(os.environ, PYTHONUTF8="1"))
    except Exception as e:  # noqa: BLE001
        log(f"  backup_drive falhou ({type(e).__name__})")
    return max(0.0, (_livre_gb("D:\\") - antes) * 1e9)


TRAVA = BASE / "estado" / "faxina.lock"


def rodar(simular=False, urgente=False, rapida=False):
    """rapida = só o que é instantâneo (apagar fonte/intermediário regenerável) — a produção chama assim quando o
    disco aperta na hora do vídeo: não espera upload pro Drive. A rodada completa fica com o vigia (6 h)."""
    if not simular:
        try:
            TRAVA.parent.mkdir(parents=True, exist_ok=True)
            if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < 6 * 3600:
                log("outra faxina está rodando — saio")
                return 0
            TRAVA.write_text(str(os.getpid()), encoding="utf-8")
        except OSError:
            pass
    try:
        return _rodar(simular, urgente, rapida)
    finally:
        if not simular:
            TRAVA.unlink(missing_ok=True)


_RAPIDA = False


def _rodar(simular, urgente, rapida):
    global _RAPIDA
    _RAPIDA = rapida
    if not urgente and any(_livre_gb(r) < g for r, g in MIN_LIVRE_GB.items()):
        urgente = True
        log("disco abaixo do mínimo — rodada URGENTE")
    log(f"início ({'simulação' if simular else 'real'}{', urgente' if urgente else ''}{', rápida' if rapida else ''})"
        f" | livre D: {_livre_gb('D:/'):.1f} GB, C: {_livre_gb('C:/'):.1f} GB")
    total = 0
    regras = (("anime (fontes/finais)", regra_anime),) if rapida else (
        ("anime (fontes/finais)", regra_anime), ("testes D:\\tmp", regra_testes), ("código morto", regra_codigo_morto),
        ("claude-code-video", regra_claude_code_video), ("PC2 (worker)", regra_pc2))
    for nome, fn in regras:
        try:
            b = fn(simular, urgente)
            total += b
            log(f"{nome}: {b / 1e9:.2f} GB liberados")
        except Exception as e:  # noqa: BLE001 — uma regra com defeito não para as outras
            log(f"{nome}: falhou ({type(e).__name__}: {e})")
    if urgente and not rapida:
        total += regra_postados_ja(simular)
    log(f"fim: {total / 1e9:.2f} GB liberados | livre D: {_livre_gb('D:/'):.1f} GB, C: {_livre_gb('C:/'):.1f} GB")
    return total


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rodar(simular="--simular" in sys.argv, urgente="--urgente" in sys.argv, rapida="--rapida" in sys.argv)
