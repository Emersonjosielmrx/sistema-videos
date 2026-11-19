"""Relatório da manhã (dona 19/11: "amanhã quero ver muitos vídeos já prontos de produção real"): quais vídeos saíram
com o Fish (marca _voz_online.json na pasta do áudio), por motor, e o estado das contas/créditos/referências.
    python relatorio_fish.py            # imprime e grava RELATORIO_MANHA.md
"""
import json, os, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
WS = Path(r"D:\recapd-ambientes\producao\workspace\anime")
R = r"D:\tools\rclone.exe"
desde = datetime.now() - timedelta(hours=12)
L = [f"# Fish na produção — {datetime.now():%d/%m %H:%M}", "",
     "> ⚠️ **LICENÇA (achado 19/11 de madrugada — decisão da dona):** as duas opções do Fish têm restrição de uso",
     "> COMERCIAL. Site, plano GRÁTIS: 'Uso comercial' aparece riscado (só o Plus/Pro libera). Kaggle, Fish Speech 1.5:",
     "> os PESOS são **CC-BY-NC-SA 4.0** (não comercial; o código é Apache, mas quem gera a voz são os pesos).",
     "> Canal monetizado publicando voz do Fish = risco de violar a licença. Opções: assinar o Plus (libera comercial",
     "> no site), ou manter o Fish só em vídeos de teste/canais sem monetização até decidir. A produção NÃO foi parada.",
     ""]

# 1) Shorts do PC1 (online)
shorts = []
for marca in WS.glob("*/**/_voz_online.json"):
    try:
        if datetime.fromtimestamp(marca.stat().st_mtime) < desde:
            continue
        d = json.loads(marca.read_text(encoding="utf-8"))
        pasta = marca.parent.parent if marca.parent.name in ("audio_cache",) else marca.parent
        final = next(pasta.glob("final_anime_short.mp4"), None)
        shorts.append((pasta.name[:60], d.get("motor"), f"{len(d.get('frases', []))}/{d.get('total')}",
                       "pronto" if final else "montando"))
    except (OSError, ValueError):
        pass
L += [f"## Shorts com Fish online no PC1 (últimas 12 h): {len(shorts)}", "", "| Vídeo | Motor | Frases Fish | Estado |",
      "|---|---|---|---|"] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in shorts] + [""]

# 2) Kaggle (longos e Shorts) — pela marca que o anime_tts grava no Drive não dá; usa o vivo + fila
L += ["## Kaggle", ""]
try:
    vivos = subprocess.run([R, "lsf", "manhwa-drive:colab_recap", "--include", "vivo_*.json"], capture_output=True,
                           text=True, timeout=120, encoding="utf-8", errors="replace").stdout.split()
    com_fish = 0
    for v in vivos:
        c = subprocess.run([R, "cat", f"manhwa-drive:colab_recap/{v}"], capture_output=True, text=True,
                           timeout=60, encoding="utf-8", errors="replace").stdout
        if '"fish": true' in c.replace(" ", "").replace('"fish":true', '"fish": true'):
            com_fish += 1
    L.append(f"- Kernels que já mostraram o Fish Speech instalado: {com_fish} de {len(vivos)} sinais de vida.")
except Exception as e:  # noqa: BLE001
    L.append(f"- (não li o Kaggle: {type(e).__name__})")

# 2b) longos do Kaggle prontos desde ontem à noite (o 1º longo com Fish: 20261115_231005_Jjd71vw8hXQ)
try:
    alvo = "20261115_231005_Jjd71vw8hXQ"
    l = subprocess.run([R, "lsf", f"manhwa-drive:colab_recap/fila/{alvo}"], capture_output=True, text=True,
                       timeout=120, encoding="utf-8", errors="replace").stdout
    est = "PRONTO" if "pronto.json" in l else "ERRO" if "erro.json" in l else "renderizado, subindo"
    L.append(f"- 1º longo com Fish (I Was Reborn To Give My Cheating Wife..., ~40 min 1080p): **{est}**")
    L.append("  - Fish Speech no Kaggle narrou: **porao 128/128, iki 56/56, mangaticos 54/54 frases** (log do "
             "pipeline 19/11). thomas_shelby/moana e personagens ficaram no clone antigo (sem referência na hora).")
except Exception as e:  # noqa: BLE001
    L.append(f"- (longo: {type(e).__name__})")

# 3) contas e créditos
try:
    import sys
    sys.path.insert(0, str(AQUI))
    import creditos
    d = creditos.carregar()
    logadas = [e for e, r in d.items() if r.get("logado")]
    tot = sum((creditos.estimado(r) or 0) for r in d.values())
    L += ["", f"## Contas do Fish: {len(logadas)} logadas — ~{tot} créditos (~{tot // 450} Shorts de 30 s)"]
    L += [f"- {e}: ~{creditos.estimado(d[e])}" for e in logadas]
except Exception as e:  # noqa: BLE001
    L.append(f"(créditos: {type(e).__name__})")

# 4) referências no Drive
try:
    ls = subprocess.run([R, "lsf", "-R", "manhwa-drive:colab_recap/vozes", "--include", "**/referencia_fish.wav",
                         "--files-only"], capture_output=True, text=True, timeout=300, encoding="utf-8",
                        errors="replace").stdout.split()
    L += ["", f"## Referências do Fish no Drive: {len(ls)} vozes"]
except Exception:  # noqa: BLE001
    pass
txt = "\n".join(L)
(AQUI / "RELATORIO_MANHA.md").write_text(txt, encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8", errors="replace") if hasattr(sys.stdout, "reconfigure") else None
print(txt)
