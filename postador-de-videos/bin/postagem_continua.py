"""postagem_continua.py — TikTok e Instagram postando o dia inteiro, sem depender de alguém olhando (tarefa PostagemContinua,
de hora em hora). 04/11 dona: "o objetivo acima de tudo é manter todos os vídeos sendo produzidos e postados ... eles têm
que postar sozinhos ... garanta que tudo posta, inclusive o atrasado".

Por quê: a postagem só rodava em 3 janelas (06:40 PostadorDeVideos, 14:05 e 19:35 TikTokRodadaExtra), cada uma com prazo.
Em 03/11 a da manhã foi cortada no prazo (TikTok 07:13-10:05, Instagram 10:05-12:41), a das 14:05 foi pulada (outra rodada
no ar) e a das 19:35 morreu na hora — 22 posts no TikTok e 5 no Instagram no dia.

Aqui: se nenhum postador está rodando, roda TikTok (prazo curto) e depois Instagram, um de cada vez (nunca os dois Chromes
juntos). Os limites continuam nos próprios postadores: max_por_conta_dia, intervalo entre posts da conta, pausas de
bloqueio, saída fixa de cada conta (proxy). Quem já postou o teto do dia é pulado lá dentro.
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import psutil

BIN = Path(__file__).resolve().parent
LOGS = BIN.parent / "logs"
PY = r"D:\veo\venv\Scripts\python.exe"
SEM_JANELA = 0x08000000
TIKTOK_MIN = 50   # prazo do TikTok nesta volta (a tarefa roda de hora em hora)
INSTA_MIN = 55


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    with open(LOGS / "postagem_continua.log", "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def rodando(script):
    for p in psutil.process_iter(["cmdline"]):
        try:
            if any(script in (c or "") for c in (p.info["cmdline"] or [])):
                return True
        except (psutil.Error, TypeError):
            continue
    return False


def etapa(prazo_min, log_arq, *cmd):
    return subprocess.run([PY, str(BIN / "etapa.py"), str(prazo_min), str(log_arq), "--", PY, *cmd],
                          creationflags=SEM_JANELA).returncode


def main():
    if (BIN.parent / "config" / "POSTAGEM_DESLIGADA.json").exists():
        return log("postagem desligada pelo botão — nada")
    hoje = datetime.now().strftime("%Y%m%d")
    # 05/11 12h: TikTok (50 min) e Instagram (55 min) rodavam UM ATRÁS DO OUTRO — o Instagram só tinha vez a cada ~2 h
    # (33 posts até o meio-dia x 101 em 04/11). O TikTok agora sai quase todo pelos notebooks (proxy de cada conta) e o
    # Instagram pelo PC1 (HTTP): cada rede roda na sua linha, independente; a que já estiver no ar não é repetida.
    import threading

    def tiktok():
        if rodando("postar_tiktok_auto.py"):
            return log("TikTok já no ar — pulo")
        log(f"TikTok (até {TIKTOK_MIN} min)")
        rc = etapa(TIKTOK_MIN + 10, LOGS / f"tiktok_{hoje}.log", str(BIN / "postar_tiktok_auto.py"), "--ate-min",
                   str(TIKTOK_MIN))
        log(f"TikTok fim (rc={rc})")

    def instagram():
        if rodando("postar_insta_auto.py"):
            return log("Instagram já no ar — pulo")
        log(f"Instagram (até {INSTA_MIN} min)")
        rc = etapa(INSTA_MIN, LOGS / f"instagram_{hoje}.log", str(BIN / "postar_insta_auto.py"))
        log(f"Instagram fim (rc={rc})")

    linhas = [threading.Thread(target=f) for f in (tiktok, instagram)]
    for t in linhas:
        t.start()
    for t in linhas:
        t.join()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        log(f"[!] {type(e).__name__}: {e}")
    try:  # 04/11: avisa na hora se a postagem caiu abaixo do normal ou o mesmo erro se repete
        subprocess.run([PY, "-X", "utf8", str(BIN / "vigia_postagem.py")], creationflags=SEM_JANELA, timeout=300)
    except Exception as e:  # noqa: BLE001
        log(f"[!] vigia: {type(e).__name__}: {e}")
