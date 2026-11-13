"""Guarda os 2 vídeos reais de exemplo da V5 no Redis do n8n6 (redis2, DB 4, sem validade), em base64.
O vídeo passa por -movflags +faststart (sem recodificar) para a prévia tocar no navegador sem pedir pedaços.
Uso: python sobe_exemplos.py"""
import base64, subprocess, sys, tempfile
from pathlib import Path

PRONTOS = Path(__file__).parent.parent / "videos_prontos"
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
VIDEOS = {"exemplo-advance.mp4": PRONTOS / "EDITOR_Advance_Solar_video_real" / "1_ORIGINAL.mp4",
          "exemplo-globo.mp4": PRONTOS / "EDITOR_Globo_Solar_depoimento_real" / "1_ORIGINAL.mp4"}
CRUS = PRONTOS / "crus"   # V6+: vídeos crus (AG Jornalismo, CC BY), já em 720p com faststart (ex_*.mp4)
VIDEOS.update({f"exemplo-{n}.mp4": CRUS / f"ex_{n}.mp4" for n in ("teste", "caue", "alderon", "luciana")})
SEM_JANELA = 0x08000000
PREFIXOS = sys.argv[1:] or ["ed5:", "ed6:"]   # uma chave por versão (cada versão lê só as dela)
with tempfile.TemporaryDirectory(dir=r"D:\hipercool-materiais\fluxo-anuncio-api\editor_v2\local") as tmp:
    for nome, orig in VIDEOS.items():
        saida = Path(tmp) / nome
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(orig), "-c", "copy", "-movflags", "+faststart", str(saida)],
                       check=True, creationflags=SEM_JANELA)
        b64 = base64.b64encode(saida.read_bytes())
        for pre in PREFIXOS:
            cmd = ('R=$(docker ps --format "{{.Names}}" | grep redis2 | head -1); '
                   f'docker exec -i $R redis-cli -n 4 -x SET {pre}arq:{nome} >/dev/null && '
                   f'docker exec $R redis-cli -n 4 STRLEN {pre}arq:{nome}')
            r = subprocess.run(["ssh", "hermes-bloqueio", cmd], input=b64, capture_output=True, creationflags=SEM_JANELA)
            print(pre, nome, saida.stat().st_size, "bytes -> base64", len(b64), "| no Redis:", r.stdout.decode().strip(), r.stderr.decode().strip()[:200])
