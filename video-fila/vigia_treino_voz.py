# -*- coding: utf-8 -*-
"""vigia_treino_voz.py — 10/11 dona: "treino de voz precisa de alguns Kaggle de prioridade antes de continuar a
produção, mas acompanhe pra não ficar muito parado (26 min em 10 contas)". De hora em hora: lê a fila_treino no Drive
(só leitura, sem falar com o Kaggle) e avisa no Telegram: pedidos novos, em andamento há quanto tempo, prontos e
PARADOS (em andamento > 90 min, ou pendente > 60 min sem ninguém pegar). Tarefa: VigiaTreinoVoz."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RCLONE = r"D:\tools\rclone.exe"
FILA = "manhwa-drive:colab_recap/fila_treino"
ESTADO = Path(r"D:\video-fila\estado\vigia_treino_voz.json")


def lsjson():
    r = subprocess.run([RCLONE, "lsjson", "-R", "--files-only", "--max-depth", "2", FILA], capture_output=True,
                       text=True, timeout=300, creationflags=0x08000000)
    return json.loads(r.stdout or "[]")


def mt(i):
    s = i["ModTime"].replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s[:19] + s[-6:]).astimezone(timezone.utc)
    except ValueError:
        return None


def main():
    agora = datetime.now(timezone.utc)
    pastas = {}
    for i in lsjson():
        if "/" in i["Path"]:
            p, n = i["Path"].split("/", 1)
            pastas.setdefault(p, {})[n] = mt(i)
    try:
        antes = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        antes = {}
    linhas, parados, novos_prontos = [], [], []
    for pid, arqs in sorted(pastas.items()):
        if "pedido.json" not in arqs:
            continue
        if "pronto.json" in arqs or "erro.json" in arqs:
            st = "pronto" if "pronto.json" in arqs else "erro"
            if antes.get(pid) not in ("pronto", "erro"):
                novos_prontos.append(f"{'✅' if st == 'pronto' else '🔴'} {pid}: {st}")
            antes[pid] = st
            continue
        em = [(n, t) for n, t in arqs.items() if n.startswith("em_andamento_")]
        if em:
            quem, t = em[0]
            minutos = int((agora - t).total_seconds() / 60) if t else 0
            linhas.append(f"⏳ {pid}: treinando há {minutos} min ({quem[13:-5]})")
            if minutos > 90:
                parados.append(f"⚠️ {pid}: em andamento há {minutos} min (passou de 90)")
            antes[pid] = "andamento"
        else:
            t = arqs.get("pedido.json")
            minutos = int((agora - t).total_seconds() / 60) if t else 0
            linhas.append(f"🕓 {pid}: esperando conta há {minutos} min")
            if minutos > 60:
                parados.append(f"⚠️ {pid}: ninguém pegou há {minutos} min")
            antes[pid] = "pendente"
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(antes, ensure_ascii=False), encoding="utf-8")
    print("\n".join(linhas + parados + novos_prontos) or "fila_treino vazia", flush=True)
    if parados or novos_prontos:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar("🎙️ Treino de voz no Kaggle\n" + "\n".join(novos_prontos + parados + linhas[:10]),
                      origem="treino de voz", importante=bool(parados), html_ok=False,
                      chave="<SEGREDO_REMOVIDO>" + ",".join(sorted(p.split(":")[0] for p in parados + novos_prontos)))


if __name__ == "__main__":
    main()
