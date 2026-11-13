"""enviar_script_remoto.py — manda UM script .ps1 pra uma máquina Windows e roda lá numa tarefa da tela, numa conexão
ssh só (dona 26/10: "mandando o script de uma vez fica muito mais rápido, isso deve ser padrão"). O OpenSSH 10.4 do
desktop castiga rajada de conexões (PerSourcePenalties) e stdin por pipe derruba o sshd: o arquivo vai compactado
dentro do -EncodedCommand.

    python bin\\netbooks\\enviar_script_remoto.py <maquina> <script.ps1> <nome_da_tarefa> [--antes "<ps>"]
"""
import base64
import gzip
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import maquina_remota as mr  # noqa: E402


PEDACO = 1800  # o sshd do Windows corta a linha de comando longa (14 mil chars chegou pela metade): vai em partes
B64 = "C:/postador-worker/_envio.b64"


def _rodar(host, ps):
    enc = base64.b64encode(ps.encode("utf-16-le")).decode()
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", host,
                        f"powershell -NoProfile -EncodedCommand {enc}"], capture_output=True, timeout=180)
    return (r.stdout + r.stderr).decode("utf-8", "replace")


def enviar(maquina, script, tarefa, antes=""):
    import time
    host = mr.MAQUINAS[maquina]["ssh"]
    dados = base64.b64encode(gzip.compress(Path(script).read_bytes())).decode()
    destino = f"C:/postador-worker/{Path(script).name}"
    partes = [dados[i:i + PEDACO] for i in range(0, len(dados), PEDACO)]
    for n, parte in enumerate(partes[:-1]):  # uma conexão por parte, 65 s entre elas (castigo de rajada do sshd)
        ps = ("New-Item -ItemType Directory -Force C:/postador-worker | Out-Null;"
              + (f"Set-Content -NoNewline -Path '{B64}' -Value '{parte}';" if n == 0 else
                 f"Add-Content -NoNewline -Path '{B64}' -Value '{parte}';") + f"'PARTE {n}'")
        for tentativa in range(4):  # o sshd do desktop derruba conexão de vez em quando: espera 5 min e repete a parte
            saida = _rodar(host, ps)
            if f"PARTE {n}" in saida:
                break
            time.sleep(300)
        else:
            return False, f"parte {n}: {saida[-200:]}"
        time.sleep(120)
    ultima = (f"Set-Content -NoNewline -Path '{B64}' -Value '{partes[-1]}';" if len(partes) == 1 else
              f"Add-Content -NoNewline -Path '{B64}' -Value '{partes[-1]}';")
    ps = (f"{antes};" if antes else "") + ultima + (
        f"$b = [Convert]::FromBase64String((Get-Content -Raw '{B64}'));"
        "$ms = New-Object IO.MemoryStream(,$b);"
        "$gz = New-Object IO.Compression.GZipStream($ms, [IO.Compression.CompressionMode]::Decompress);"
        "$out = New-Object IO.MemoryStream; $gz.CopyTo($out);"
        f"[IO.File]::WriteAllBytes('{destino}', $out.ToArray());"
        f"schtasks /create /tn {tarefa} /tr \"powershell -NoProfile -ExecutionPolicy Bypass -File {destino}\" "
        "/sc once /st 00:00 /it /f | Out-Null;"
        f"schtasks /run /tn {tarefa} | Out-Null;"
        f"Remove-Item '{B64}';"
        f"'ENVIADO ' + (Get-Item '{destino}').Length"
    )
    for tentativa in range(4):
        saida = _rodar(host, ps)
        if "ENVIADO" in saida:
            return True, saida
        time.sleep(300)
    return False, saida


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    antes = a[a.index("--antes") + 1] if "--antes" in a else ""
    ok, saida = enviar(a[0], a[1], a[2], antes)
    print("OK" if ok else "FALHOU", saida.strip().splitlines()[-1][:300] if saida.strip() else "")
