# -*- coding: utf-8 -*-
"""pc2.py — o PC2 (Revision-PC, ssh "pc2" via Tailscale) renderiza as versões nas LÍNGUAS; o PC1 fica com o pt.

Chamado pelo fila.py do PC1 (comando "pc2", tarefa HipercoolPC2): manda pro PC2 o que falta (roteiro do capítulo,
cache 2.5D novo, painéis), dispara bin/pc2_rodar.ps1 lá e, quando o log mostra "[OK] Vídeo final", traz os
arquivos do vídeo e a tradução do roteiro (o SEO da língua lê) pro PC1. Tudo por tar dentro do ssh.
"""
import base64
import os
import re
import subprocess
import tempfile
from pathlib import Path

from hp_common import log

HOST = "pc2"
# 22/10: o ssh do Windows (System32\OpenSSH) não entrega os últimos KB do tar que vem do PC2: o vídeo de 262 MB
# parava a 55 KB do fim e a rodada esperava até o timeout segurando a trava das línguas, toda vez. O ssh do Git trouxe
# o mesmo vídeo inteiro em 27 s (mesmo motivo do D:\video-fila\maquinas.py).
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe" if Path(r"C:\Program Files\Git\usr\bin\ssh.exe").exists() else "ssh"
MAT = Path(r"D:\hipercool-materiais")
CACHE = Path(r"D:\hipercool-videos\workspace\cache")
BIN = Path(r"D:\hipercool-videos\bin")
R_MAT = "C:/hipercool-materiais"
R_CACHE = "C:/hipercool-videos/workspace/cache"
VIDEOS = Path(r"D:\hipercool-videos\workspace\videos")
R_VIDEOS = "C:/hipercool-videos/workspace/videos"
R_BIN = "C:/hipercool-videos/bin"
CACHES = ("clips_2p5d", "profundidade", "mascaras")
# Só rodam no PC1 e não têm o que fazer no PC2 (que só renderiza língua): a fila é quem coordena os dois,
# o pc2.py é o lado de cá dessa conversa e o refazer_caps/lancamento_pt são o lote e o lançamento em pt.
# O resto do bin/ vai inteiro, porque o hiper-pipeline de lá importa quase tudo.
BIN_SO_PC1 = ("fila.py", "pc2.py", "refazer_caps.py", "lancamento_pt.py")


def _ssh(cmd, timeout=120):
    return subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST, cmd],
                          capture_output=True, timeout=timeout)


def _txt(r):
    return (r.stdout or b"").decode("utf-8", "replace")


def no_ar():
    try:
        return _ssh("echo ok", timeout=30).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def _remotos(pasta):
    r = _ssh(f'dir /b "{pasta}"')
    return set(_txt(r).split()) if r.returncode == 0 else set()


def _lista_tmp(nomes):
    """Grava os nomes num arquivo, um por linha, pro 'tar -T' (devolve o caminho).

    16/10: os nomes iam SOLTOS na linha de comando do tar e o Windows corta em 32767 caracteres —
    só a pasta 'mascaras' tem 2944 arquivos (~156 mil caracteres), e as três somadas dão ~220 mil.
    Resultado: FileNotFoundError [WinError 206] em TODA rodada da tarefa HipercoolPC2 desde 14/10
    (62 vezes no logs/fila_pc2.log), o PC2 nunca recebeu o cache 2.5D e nenhuma língua foi
    renderizada lá — só o cap 1 existe nos outros idiomas.
    Com '-T' não há limite: o tar lê a lista do arquivo. Testado no GNU tar 1.35 (o que o Python
    acha no PATH daqui) e no bsdtar 3.3.2 do System32 (o que o PC2 tem), inclusive com espaço no
    nome — no arquivo de lista cada linha é um nome inteiro, sem aspas.
    """
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8", newline="\n")
    f.write("".join(n + "\n" for n in nomes))
    f.close()
    return f.name


def _apagar(caminho):
    try:
        os.unlink(caminho)
    except OSError:
        pass


def _enviar(base, nomes, destino):
    """Arquivos/pastas (relativos a base) -> destino no PC2."""
    if not nomes:
        return True
    lista = _lista_tmp(nomes)
    try:
        tar = subprocess.Popen(["tar", "-cf", "-", "-C", str(base), "-T", lista], stdout=subprocess.PIPE)
        r = subprocess.run([SSH, "-o", "BatchMode=yes", HOST, f"tar -xf - -C {destino}"], stdin=tar.stdout,
                           capture_output=True, timeout=3600)
        tar.stdout.close()
        return tar.wait() == 0 and r.returncode == 0
    finally:
        _apagar(lista)


def _baixar(origem, nomes, destino):
    """Arquivos de origem (pasta no PC2) -> destino no PC1."""
    if not nomes:
        return True
    # Lista longa vai pelo STDIN do ssh ('-T -'): no PC2 quem interpreta o comando é o cmd.exe, que
    # corta em 8191 caracteres — menos ainda que o limite daqui. Arquivo em vez de pipe direto
    # pra não travar se a lista passar do buffer do pipe.
    # 21/10: pelo stdin o tar do PC2 às vezes não recebe o fim da lista (OpenSSH do Windows) e fica parado sem mandar
    # nada até o timeout de 1 h (32 vezes no fila_pc2-trazer.log; línguas "não vieram em 24 h" e a trava do PC2
    # segurava as línguas a noite toda). Lista curta (o vídeo de uma língua) vai na linha de comando; o ssh derruba
    # conexão morta em ~1 min; estouro de tempo = falhou (tenta na próxima rodada), não derruba a tarefa.
    soltos = " ".join(f'"{n}"' for n in nomes)
    lista = None if len(soltos) < 7000 else _lista_tmp(nomes)
    ssh_cmd = [SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15",
               "-o", "ServerAliveCountMax=4", HOST]
    ssh = None
    try:
        if lista is None:
            ssh = subprocess.Popen(ssh_cmd + [f"tar -cf - -C {origem} {soltos}"], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE)
        else:
            with open(lista, "rb") as f:
                ssh = subprocess.Popen(ssh_cmd + [f"tar -cf - -C {origem} -T -"], stdin=f, stdout=subprocess.PIPE)
        r = subprocess.run(["tar", "-xf", "-", "-C", str(destino)], stdin=ssh.stdout, capture_output=True,
                           timeout=1800)
        ssh.stdout.close()
        return ssh.wait(timeout=120) == 0 and r.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"pc2: trazer {origem} passou do tempo (tenta de novo na próxima rodada)", flush=True)
        return False
    finally:
        if ssh is not None and ssh.poll() is None:
            ssh.kill()
        if lista:
            _apagar(lista)


def _bin_local():
    """{nome: (tamanho, data)} do bin/ daqui, já sem o que não vai pro PC2."""
    itens = {}
    for p in BIN.iterdir():
        n = p.name
        # "_" = rascunho/teste solto do dono, ".bak"/".bak-16out" = cópia de segurança, pasta = __pycache__.
        # 22/10: ".bkp_..."/".antes_..." e qualquer "x.py.<algo>" também são cópia (o PC2 está sem disco)
        if (n.startswith("_") or re.search(r"\.(bak|bkp|antes|orig|old)|\.py\.", n) or n in BIN_SO_PC1
                or not p.is_file()):
            continue
        st = p.stat()
        itens[n] = (st.st_size, int(st.st_mtime))
    return itens


def _bin_remoto():
    """{nome: (tamanho, data)} do bin/ do PC2, ou None se não deu pra listar.

    Vai por PowerShell -EncodedCommand (e não pelo 'dir' que o _remotos usa) por dois motivos: o 'dir'
    do cmd não dá tamanho nem data em coluna estável — depende do idioma e do formato de data do
    Windows de lá —, e as aspas do script seriam comidas pelo cmd.exe que recebe a linha do ssh.
    """
    ps = ("Get-ChildItem -LiteralPath 'C:\\hipercool-videos\\bin' -File | ForEach-Object "
          "{ $_.Name + '|' + $_.Length + '|' + "
          "[int64]($_.LastWriteTimeUtc - [datetime]'1970-01-01').TotalSeconds }")
    r = _ssh("powershell -NoProfile -EncodedCommand " + base64.b64encode(ps.encode("utf-16-le")).decode())
    if r.returncode != 0:
        return None
    itens = {}
    for linha in _txt(r).splitlines():
        partes = linha.strip().split("|")
        if len(partes) == 3 and partes[1].isdigit():
            itens[partes[0]] = (int(partes[1]), int(partes[2]))
    return itens


def sincronizar_bin():
    """Manda pro PC2 o que mudou no bin/. Devolve (ok, recado pro log).

    16/10 (pedido do dono): o código só chegava lá por 'scp' na mão e o PC2 acumulou 18 arquivos
    atrasados — passou dias renderizando língua com o pipeline velho sem ninguém perceber.
    Tamanho diferente = mudou; mais novo aqui = mudou mesmo com o mesmo tamanho. O tar preserva a
    data, então depois da cópia os dois ficam iguais e a rodada seguinte não copia nada.
    Nunca entra config/ nem secrets/ nem workspace/: o PC2 tem os dele.
    """
    local = _bin_local()
    remoto = _bin_remoto()
    if remoto is None:
        return False, "pc2: não consegui listar o bin/ do PC2"
    mudou = sorted(n for n, (tam, data) in local.items()
                   if n not in remoto or remoto[n][0] != tam or data > remoto[n][1] + 2)
    if not mudou:
        return True, f"pc2: bin/ já igual ({len(local)} arquivos conferidos, 0 copiados)"
    if not _enviar(BIN, mudou, R_BIN):
        return False, f"pc2: FALHOU copiar o bin/ ({len(mudou)} arquivos)"
    return True, f"pc2: {len(mudou)} arquivos atualizados ({', '.join(mudou[:8])})"


def sincronizar(slug_cap):
    """Código do bin/ + cache 2.5D que o PC2 ainda não tem + roteiros do capítulo + painéis (se faltarem)."""
    ok_bin, recado = sincronizar_bin()
    log(recado)
    if not ok_bin:
        # Sem o código novo lá o vídeo sai com o pipeline velho — melhor não renderizar; a tarefa
        # HipercoolPC2 roda de novo em 20 min e o fila.py já loga "falhou a cópia pro PC2".
        return False
    ok = True
    for c in CACHES:
        loc = CACHE / c
        if loc.exists():
            tem = _remotos(f"{R_CACHE}/{c}".replace("/", "\\"))
            ok &= _enviar(CACHE, [f"{c}/{p.name}" for p in loc.iterdir() if p.name not in tem], R_CACHE)
    ok &= _enviar(MAT, [f"narration_cache/{p.name}" for p in (MAT / "narration_cache").glob(f"{slug_cap}_*")], R_MAT)
    # Painéis SEMPRE, não só "se faltarem" (16/10): a limpeza da marca do scan reescreve os painéis no PC1 e o PC2
    # seguia com a versão velha — outro md5, outra resposta da censura (o cap 3 panel_054 original saía com os
    # mamilos à mostra). E a lista de fosco forçado pela análise do vídeo pronto, que é por md5 do painel.
    ok &= _enviar(MAT, [f"panels/{slug_cap}"], R_MAT)
    forcados = CACHE.parent / "censura_cache" / "_forcar_fosco.json"
    if forcados.exists():
        ok &= _enviar(CACHE.parent, ["censura_cache/_forcar_fosco.json"], R_CACHE.rsplit("/", 1)[0])
    return ok


def rodando():
    """Algum hiper-pipeline vivo no PC2 (o daemon de workers de lá não conta)."""
    r = _ssh("wmic process where \"name='python.exe'\" get commandline")
    return "hiper-pipeline" in _txt(r)


def disparar(chave, lang, titulo, slug_cap, fim=0, inicio=0):
    t64 = base64.b64encode(titulo.encode("utf-8")).decode()
    r = _ssh("powershell -NoProfile -ExecutionPolicy Bypass -File C:\\hipercool-videos\\bin\\pc2_rodar.ps1 "
             f"-Chave {chave} -Lang {lang} -TituloB64 {t64} -Pasta D:\\hipercool-materiais\\panels\\{slug_cap} "
             f"-Fim {int(fim)} -Inicio {int(inicio)}")
    return r.returncode == 0 and "rc 0" in _txt(r)


def log_render(chave, lang):
    return _txt(_ssh(f"type C:\\hipercool-videos\\logs\\pc2_{chave}_{lang}.log"))


def trazer(video, slug_cap, lang):
    """Arquivos do vídeo (mesmo prefixo até _<LÍNGUA>) + tradução do roteiro -> PC1. `video` é o caminho do log:
    só o nome (hipercool-materiais/videos, antigo) ou <obra>/capNN/<língua>/<versão>/nome (workspace/videos; 20/10:
    só olhava o antigo e 24 línguas prontas ficaram presas no PC2 desde 16-17/10)."""
    rel = Path(video.replace("\\", "/"))
    if rel.parent == Path("."):
        r_dir, l_dir, w_dir = f"{R_MAT}/videos", MAT / "videos", r"C:\hipercool-materiais\videos"
    else:
        r_dir, l_dir = f"{R_VIDEOS}/{rel.parent.as_posix()}", VIDEOS / rel.parent
        w_dir = R_VIDEOS.replace("/", "\\") + "\\" + str(rel.parent).replace("/", "\\")
    prefixo = rel.name.split(f"_{lang.upper()}_")[0] + f"_{lang.upper()}_"
    nomes = [n for n in _remotos(w_dir) if n.startswith(prefixo)]
    l_dir.mkdir(parents=True, exist_ok=True)
    if rel.name not in nomes or not _baixar(r_dir, nomes, l_dir):
        return False
    trad = [n for n in _remotos(r"C:\hipercool-materiais\narration_cache")
            if n.startswith(slug_cap + "_") and n.endswith(f"_{lang}.json")]
    _baixar(f"{R_MAT}/narration_cache", trad, MAT / "narration_cache")
    if not all((l_dir / n).exists() for n in nomes):
        return False
    _ssh(f'del /q "{w_dir}\\{prefixo}*"')  # o PC2 tem pouco disco; a cópia está no PC1
    return True


def video_final(texto_log):
    """Caminho do vídeo final como o hiper-pipeline escreveu no log (relativo a workspace/videos, ou só o nome)."""
    m = re.findall(r"\[OK\] Vídeo final: (\S+\.mp4)", texto_log)
    return m[-1] if m else None
