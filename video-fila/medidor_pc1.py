"""medidor_pc1.py — o mesmo medidor do telao_win.py (PC2/desktop), aqui no PC1 (dona 29/10/2026: "PC2, PC1 e desktop
... medidor de porcentagem de CPU e RAM ... monitor 24 h 7 dias ... análise a cada 24 h").

1 linha por minuto em estado\\saude_pc1.csv, mesmas colunas do C:\\vitrine\\saude.csv (o analise_maquinas.py lê os 3).
Tarefa MedidorPC1 (pythonw, ao entrar no Windows e a cada 10 min): se já tem um rodando, sai na hora (trava).
Só biblioteca padrão.
"""
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "vitrine"))
CSV = BASE / "estado" / "saude_pc1.csv"
TRAVA = BASE / "estado" / "medidor_pc1.lock"


def _travar():
    """True se este processo ficou com a trava (arquivo aberto em modo exclusivo enquanto vive)."""
    import msvcrt
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    f = open(TRAVA, "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        f.close()
        return None
    return f


def main():
    trava = _travar()
    if not trava:
        return  # já tem um medidor rodando
    import telao_win as tw  # só as funções de medida (_tempos, _ram, _contar); o telão não abre aqui
    oc0, to0 = tw._tempos()
    while True:
        time.sleep(60)
        try:
            oc1, to1 = tw._tempos()
            cpu = round(100 * (1 - (oc1 - oc0) / max(to1 - to0, 1)))
            oc0, to0 = oc1, to1
            ram, livre = tw._ram()
            try:
                n = tw._contar()
            except Exception:  # noqa: BLE001 — PC1 sem RAM: o tasklist passa de 60 s; -1 = não deu pra contar
                n = {"ffmpeg": -1, "python": -1, "pythonw": -1, "chrome": -1}
            novo = not CSV.exists()
            with open(CSV, "a", encoding="utf-8") as f:
                if novo:
                    f.write("quando,cpu,ram_pct,ram_livre_gb,ffmpeg,python,pythonw,chrome,camera,telao\n")
                f.write(f"{time.strftime('%Y-%m-%d %H:%M')},{cpu},{ram},{livre},{n['ffmpeg']},{n['python']},"
                        f"{n['pythonw']},{n['chrome']},0,0\n")
            if CSV.stat().st_size > 5_000_000:  # ~35 dias: guarda o fim
                CSV.write_text(CSV.read_text("utf-8")[-2_500_000:].split("\n", 1)[1], "utf-8")
        except Exception as e:  # noqa: BLE001 — o medidor nunca para (o erro fica anotado)
            try:
                with open(BASE / "logs" / "medidor_pc1.log", "a", encoding="utf-8") as f:
                    f.write(f"{time.strftime('%d/%m %H:%M:%S')} {type(e).__name__}: {e}\n")
            except OSError:
                pass


if __name__ == "__main__":
    if os.name == "nt":
        main()
