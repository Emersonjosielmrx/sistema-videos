# Ajudante (24/10): roda um PowerShell (lido de arquivo ou do argumento) em outra máquina por ssh, codificado.
#   python _ps_em.py <host> <arquivo.ps1 | -c "script">
import sys

sys.path.insert(0, r"D:\video-fila")
import transferencias  # noqa: E402

host = sys.argv[1]
script = sys.argv[3] if sys.argv[2] == "-c" else open(sys.argv[2], encoding="utf-8").read()
rc, txt = transferencias._ps_remoto(host, script, timeout=1800)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print(txt)
print(f"[rc={rc}]")
