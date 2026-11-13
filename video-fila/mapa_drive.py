"""mapa_drive.py — MAPA do que está no Google Drive (videos-backup e a cópia das vozes/fontes), pra achar e trazer de volta
à mão (dona 23/10/2026: "como já temos muita coisa no Drive, tem que ter um mapa; se um dia eu precisar, posso pegar
manualmente"). Uma listagem só (rclone lsjson -R) e a soma é feita aqui. Gera D:\\video-fila\\MAPA_DRIVE.md.

    python mapa_drive.py      # refaz o mapa (a faxina diária também chama)
"""
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RCLONE = r"D:\tools\rclone.exe"
RAIZ = "manhwa-drive:videos-backup"
SAIDA = Path(__file__).resolve().parent / "MAPA_DRIVE.md"

# o que cada pasta guarda (quem manda pra lá) — atualizar quando surgir pasta nova
O_QUE = {
    "hipercool/videos": "capítulos do hipercool já postados e o estoque longe da vez (manhwa-react\\scripts\\backup_drive: "
                        "hipercool_postados/hipercool_estoque). Mesmo caminho de D:\\hipercool-materiais\\videos.",
    "hipercool/videos/longo": "16:9 (capNN.mp4) e compilados do hipercool; o compilado traz de volta sozinho (fila._do_drive).",
    "hipercool/shorts": "Shorts do hipercool já postados (D:\\hipercool-materiais\\shorts_hipercool).",
    "hipercool-materiais/models/rvc/vozes": "o .index das vozes RVC paradas (o .pth fica no PC). Volta sozinho: "
                                           "hipercool-materiais\\bin\\vozes_drive.py garantir <voz>.",
    "hipercool-materiais/anime": "vídeos-fonte do anime já usados (source.*) e vídeos de trabalho de pastas paradas. "
                                 "Volta sozinho quando o recap pede: fontes_drive.trazer.",
    "hipercool-materiais/amostras_voz": "sobras de treino/teste de voz já encerrados (pesos do Kaggle, dataset v3, "
                                        "fidelidade, referências). Volta: hipercool-materiais\\bin\\amostras_drive.py "
                                        "trazer <caminho>. Lista arquivo a arquivo: _NO_DRIVE.md em cada pasta.",
    "parceiro": "Shorts do recap de parceiros (postar.json fica no PC; sai 3 dias depois de público no YouTube).",
    "veo": "vídeos do Veo por etapa (1_youtube/2_tiktok/3_instagram), brutos e o espelho antigo pos_final_completo "
           "(COMPLETO = com o slide de propaganda; nunca reaproveitar sem a versão limpa).",
    "manhwa-react": "rede de canais react (postados, rede_marca, nao-usados).",
    "historias-em-frames": "vídeos do Histórias em Frames.",
    "recapd": "recaps postados (postados_recaps).",
    "ms-energy": "MS Energy (cliente): postados.",
    "anime": "pendentes antigos do anime (fora do formato das etapas).",
}


def main():
    r = subprocess.run([RCLONE, "lsjson", "-R", "--files-only", "--no-mimetype", "--fast-list", RAIZ],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600,
                       creationflags=0x08000000)
    if r.returncode:
        print("rclone falhou:", (r.stderr or "")[-300:])
        return 1
    itens = json.loads(r.stdout or "[]")
    n, b, ult = defaultdict(int), defaultdict(int), defaultdict(str)
    for it in itens:
        partes = it["Path"].split("/")
        for k in range(1, min(4, len(partes))):  # pastas até o 3º nível
            p = "/".join(partes[:k])
            n[p] += 1
            b[p] += it.get("Size") or 0
            ult[p] = max(ult[p], (it.get("ModTime") or "")[:10])
    total = sum(it.get("Size") or 0 for it in itens)
    ln = ["# Mapa do Google Drive (mapa_drive.py)", "",
          f"Atualizado {datetime.now():%d/%m/%Y %H:%M}. Remoto `{RAIZ}`: {len(itens)} arquivos, {total / 1e9:.1f} GB.", "",
          "## Como pegar algo de volta à mão", "",
          "- **Pelo navegador:** drive.google.com, pasta **videos-backup** (conta do rclone `manhwa-drive`), mesmo caminho da tabela.",
          "- **Pelo rclone** (no PC1):",
          "  - um arquivo: `D:\\tools\\rclone.exe copyto \"manhwa-drive:videos-backup/<caminho>/<arquivo>\" \"D:\\destino\\<arquivo>\"`",
          "  - uma pasta: `D:\\tools\\rclone.exe copy \"manhwa-drive:videos-backup/<pasta>\" \"D:\\destino\"`",
          "  - procurar pelo nome: `D:\\tools\\rclone.exe lsf -R --include \"*parte_do_nome*\" manhwa-drive:videos-backup`",
          "- **Voltam sozinhos** (não precisa fazer nada): vozes (`vozes_drive.py garantir <voz>`), fontes do anime "
          "(quando o recap pede), 16:9 do compilado do hipercool e os capítulos do estoque quando chega a vez.", "",
          "## Pastas", "", "| pasta | arquivos | GB | último envio | o que é |", "|---|---:|---:|---|---|"]
    for p in sorted(n, key=lambda x: x.lower()):
        if p.count("/") > 2:
            continue
        desc = next((O_QUE[k] for k in sorted(O_QUE, key=len, reverse=True) if p == k or p.startswith(k + "/")), "")
        etapa = {"1_youtube": "etapa: já saiu no YouTube (falta TikTok/Instagram)", "2_tiktok": "etapa: já saiu no "
                 "YouTube e no TikTok", "3_instagram": "etapa: já saiu em todas as redes"}.get(p.split("/")[1] if "/" in p else "")
        if etapa and p.count("/") == 1:
            desc = etapa + " (catálogo/etapas do postador)"
        if p.count("/") == 2 and not any(p == k for k in O_QUE):
            desc = ""  # 3º nível: só número (a descrição fica na pasta de cima)
        ln.append(f"| `{p}` | {n[p]} | {b[p] / 1e9:.2f} | {ult[p]} | {desc} |")
    SAIDA.write_text("\n".join(ln) + "\n", encoding="utf-8")
    print(SAIDA, f"{len(itens)} arquivos, {total / 1e9:.1f} GB")
    return 0


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
