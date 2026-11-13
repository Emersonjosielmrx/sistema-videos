"""analise_maquinas.py — as máquinas trabalharam MESMO as 24 h? (dona 27/10/2026: "medidor de CPU e RAM nos 2 [PC2 e
desktop], monitor 24 h 7 dias, e uma análise a cada 24 h pra verificar se trabalharam todo tempo ou se saíram do
plano; pode medir pelo ffmpeg também, pelo plano ele tem que ficar rodando praticamente 24 h por dia").

Os dados vêm do telao_win.py de cada máquina (C:\\vitrine\\saude.csv, 1 linha por minuto: cpu, ram, quantos ffmpeg/
python/chrome, câmera em uso). Regra: TRABALHANDO = CPU >= 70% ou algum ffmpeg rodando. PARADO = CPU < 30% e sem
ffmpeg. Desktop com câmera/OBS (a dona usando) não conta como parado.

    python analise_maquinas.py          # analisa as últimas 24 h, grava linhas\\MAQUINAS_24H.md e manda no resumo
    python analise_maquinas.py --so-ver # só imprime
Tarefa AnaliseMaquinas24h (todo dia 08:05).
"""
import csv
import io
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
DOC = BASE / "linhas" / "MAQUINAS_24H.md"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
LER = "powershell -NoProfile -Command Get-Content C:/vitrine/saude.csv -Tail 1600"


def _ler(maquina):
    """CSV das últimas ~26 h (1600 linhas) numa conexão; desktop pelo caminho seguro do vitrine (1 conexão, sem stdin)."""
    if maquina == "pc1":  # 29/10 (dona: "PC2, PC1 e desktop"): medidor_pc1.py, mesmo formato, aqui mesmo
        p = BASE / "estado" / "saude_pc1.csv"
        if not p.exists():
            return None, "medidor do PC1 ainda sem dados (tarefa MedidorPC1)"
        linhas = [l for l in p.read_text("utf-8").splitlines()[-1600:] if l and not l.startswith("quando")]
        cab = "quando,cpu,ram_pct,ram_livre_gb,ffmpeg,python,pythonw,chrome,camera,telao"
        return list(csv.DictReader(io.StringIO(cab + "\n" + "\n".join(linhas)))), ""
    if maquina == "desktop":
        import vitrine
        if not vitrine.TELAO_DESKTOP.exists():
            return None, "telão do desktop ainda não instalado"
        r = vitrine._ps_desktop(["Get-Content C:\\vitrine\\saude.csv -Tail 1600"], timeout=90)
    else:
        r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=15", maquina, LER],
                           capture_output=True, timeout=90, creationflags=0x08000000)
    txt = (r.stdout or b"").decode("utf-8", "replace")
    if "quando," not in txt and "," not in txt:
        return None, f"sem dados ({(r.stderr or b'').decode(errors='replace').strip()[-120:] or 'vazio'})"
    linhas = [l for l in txt.splitlines() if l and not l.startswith("quando")]
    cab = "quando,cpu,ram_pct,ram_livre_gb,ffmpeg,python,pythonw,chrome,camera,telao"
    return list(csv.DictReader(io.StringIO(cab + "\n" + "\n".join(linhas)))), ""


def analisar(maquina, linhas, desde):
    ls = [l for l in linhas if l.get("quando") and datetime.strptime(l["quando"], "%Y-%m-%d %H:%M") >= desde]
    if not ls:
        return {"maquina": maquina, "erro": "nenhuma medida nas últimas 24 h (telão/medidor parado?)"}
    cpu = [int(l["cpu"]) for l in ls]
    ff = [int(l["ffmpeg"]) for l in ls]
    cam = [int(l.get("camera") or 0) for l in ls]
    trab = sum(1 for c, f in zip(cpu, ff) if c >= 70 or f > 0)
    parado = [c < 30 and f == 0 and not k for c, f, k in zip(cpu, ff, cam)]
    # maior trecho parado seguido (minutos)
    maior, atual, ini_maior, ini = 0, 0, None, None
    for l, p in zip(ls, parado):
        if p:
            ini = ini or l["quando"]
            atual += 1
            if atual > maior:
                maior, ini_maior = atual, ini
        else:
            atual, ini = 0, None
    # horas paradas (para ver o padrão: noite? hora do almoço?)
    por_hora = {}
    for l, p in zip(ls, parado):
        h = l["quando"][11:13]
        por_hora.setdefault(h, [0, 0])
        por_hora[h][0] += p
        por_hora[h][1] += 1
    horas_paradas = [h for h, (p, n) in sorted(por_hora.items()) if n and p / n > 0.5]
    return {"maquina": maquina, "minutos_medidos": len(ls), "cobertura_pct": round(100 * len(ls) / 1440),
            "cpu_media": round(sum(cpu) / len(cpu)), "trabalhando_pct": round(100 * trab / len(ls)),
            "parado_pct": round(100 * sum(parado) / len(ls)), "com_ffmpeg_pct": round(100 * sum(1 for f in ff if f) / len(ls)),
            "ram_media": round(sum(int(l["ram_pct"]) for l in ls) / len(ls)),
            "camera_min": sum(cam), "maior_parado_min": maior, "maior_parado_desde": ini_maior,
            "horas_paradas": horas_paradas}


def texto(r):
    if r.get("erro"):
        return f"• {r['maquina'].upper()}: {r['erro']}"
    ok = "✅" if r["trabalhando_pct"] >= 85 else ("⚠️" if r["trabalhando_pct"] >= 50 else "❌")
    t = (f"{ok} {r['maquina'].upper()}: trabalhando {r['trabalhando_pct']}% do tempo (CPU média {r['cpu_media']}%, "
         f"RAM {r['ram_media']}%, ffmpeg em {r['com_ffmpeg_pct']}%), parado {r['parado_pct']}%")
    if r["maior_parado_min"] >= 30:
        t += f"; maior parada {r['maior_parado_min']} min desde {r['maior_parado_desde'][11:]}"
    if r["horas_paradas"]:
        t += f"; horas quase paradas: {', '.join(r['horas_paradas'])}h"
    if r["camera_min"]:
        t += f"; câmera/OBS em uso {r['camera_min']} min (não conta)"
    if r["cobertura_pct"] < 90:
        t += f"; medidor só cobriu {r['cobertura_pct']}% do dia"
    return t


def main(so_ver=False):
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    desde = datetime.now() - timedelta(hours=24)
    res = []
    for m in ("pc2", "pc1", "desktop"):
        try:
            linhas, erro = _ler(m)
            res.append(analisar(m, linhas, desde) if linhas else {"maquina": m, "erro": erro})
        except Exception as e:  # noqa: BLE001
            res.append({"maquina": m, "erro": f"{type(e).__name__}: {str(e)[:120]}"})
    msg = f"🖥️ Máquinas nas últimas 24 h ({datetime.now():%d/%m %H:%M}) — plano: PC2, PC1 e desktop (câmera desligada) no máximo o tempo todo\n" + \
          "\n".join(texto(r) for r in res)
    print(msg)
    if so_ver:
        return res
    DOC.parent.mkdir(parents=True, exist_ok=True)
    antes = DOC.read_text("utf-8") if DOC.exists() else "# Máquinas: trabalharam as 24 h? (mais novo em cima)\n\n"
    cab, _, resto = antes.partition("\n\n")
    DOC.write_text(cab + "\n\n" + msg + "\n\n" + resto, "utf-8")
    try:
        import avisos
        avisos.enviar(msg, "maquinas-24h")
    except Exception as e:  # noqa: BLE001
        print(f"aviso não saiu: {e}")
    return res


if __name__ == "__main__":
    main("--so-ver" in sys.argv)
