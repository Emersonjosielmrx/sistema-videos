"""T (22/10): trechos ORIGINAIS dos personagens de madrugada, sem rajada de yt-dlp (17/10 a rajada barrou o IP da casa
e parou os Shorts). 1 personagem por vez pelo baixar_trechos2.py, 15 min entre um e outro; para no 1º bloqueio do IP
(pausa do ytdlp_vez) e às 06:30 (de dia o Cortes usa o yt-dlp o tempo todo). Personagem que já tem trecho é pulado:
a tarefa diária (TrechosNoite, 03:20) termina sozinha quando a lista acaba.

Trava de qualidade: o anime_tts abre o Short com QUALQUER trecho do trechos.json, sem ninguém ouvir antes, e a nota do
baixador só diz que as palavras batem (não que é a voz do personagem). Personagem com algum trecho de nota < 0,85 fica
em trechos_revisar.json (fora dos Shorts) até alguém ouvir e renomear pra trechos.json.
Log: logs\\trechos_noite_AAAAMMDD.log; resultado no resumo do Telegram (avisos, não importante)."""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — 29/10 (dona): nenhum processo filho (yt-dlp, ssh, ffmpeg) abre janela
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
PY = r"D:\recapd-ambientes\producao\venv\Scripts\python.exe"
SAIDA = Path(r"D:\hipercool-materiais\amostras_voz\trechos_icones")
ORDEM = ["woody", "homem_de_ferro_tony_stark", "patolino", "lula", "naruto", "patrick_estrela",
         "seu_sirigueijo_peter_griffin", "harry_potter", "dinho_mamonas_assassinas", "thomas_shelby_peaky_blinders",
         # 23/10: vozes dos formatos (bordão original no Short de várias vozes) — SEMPRE pra revisar: a dona ouve antes
         "quico", "chiquinha", "chaves_chapolin", "professor_girafales", "chico_selton", "joao_grilo", "faustao",
         "silvio_santos", "galvao_bueno", "pato_donald"]
REVISAR_SEMPRE = {"quico", "chiquinha", "chaves_chapolin", "professor_girafales", "chico_selton", "joao_grilo", "faustao",
                  "silvio_santos", "galvao_bueno", "pato_donald"}
NOTA_MIN = 0.85
INTERVALO_S = 15 * 60
ESPERA_MAX_S = 30 * 60  # pausa do IP até 30 min: espera em vez de largar a noite
PARAR_AS = "06:30"
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
LOG = BASE / "logs" / f"trechos_noite_{datetime.now():%Y%m%d}.log"

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import ytdlp_vez  # noqa: E402  (COMUM: 1 yt-dlp por vez no PC + pausa quando o YouTube barra o IP)


def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%H:%M:%S}] {msg}\n")


def _estranhos():
    """23/10 (dona aprovou o áudio original do bordão: "sempre que ficar estranho podemos fazer isso"): personagem
    aprovado com bordão que a voz clonada fala estranho (monitor_bordoes -> bordoes_estranhos) entra na fila do trecho
    ORIGINAL — sempre pra revisar antes."""
    vozes = Path(r"D:\hipercool-materiais\models\rvc\vozes")
    out = []
    for g in sorted(vozes.glob("*/linguagem_v2.json")):
        try:
            d = json.loads(g.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if d.get("bordoes_estranhos") and (g.parent / "personagem.json").exists():
            out.append(g.parent.name)
    return out


def feito(voz):
    return (SAIDA / voz / "trechos.json").exists() or (SAIDA / voz / "trechos_revisar.json").exists()


def main():
    extras = [v for v in _estranhos() if v not in ORDEM]
    REVISAR_SEMPRE.update(extras)
    faltam = [v for v in ORDEM + extras if not feito(v)]
    if not faltam:
        return
    log(f"início: {len(faltam)} personagem(ns) sem trecho: {', '.join(faltam)}")
    resumo = []
    for i, voz in enumerate(faltam):
        if datetime.now().strftime("%H:%M") >= PARAR_AS:
            log(f"passou de {PARAR_AS}: o resto fica pra próxima madrugada")
            break
        falta = ytdlp_vez.pausado()
        # 23/10: a rodada das 03:20 desistiu numa pausa de "mais 1 min" e perdeu a noite: pausa curta que acaba antes
        # do PARAR_AS = espera (é o mesmo IP liberado que o Cortes vai usar; 1 personagem a cada 15 min, sem rajada)
        if falta and falta <= ESPERA_MAX_S and \
                (datetime.now() + timedelta(seconds=falta + 60)).strftime("%H:%M") < PARAR_AS:
            log(f"yt-dlp em pausa por mais {falta / 60:.0f} min: espero")
            time.sleep(falta + 60)
            falta = ytdlp_vez.pausado()
        if falta:
            log(f"yt-dlp em pausa por mais {falta / 60:.0f} min (IP barrado): paro aqui")
            break
        try:
            r = subprocess.run([PY, str(BASE / "baixar_trechos2.py"), voz], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=45 * 60, creationflags=SEM_JANELA)
            saida = (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            saida = "passou de 45 min"
        linhas = [l for l in saida.splitlines() if l.startswith(("OK ", "-- ", "FIM")) or "pausa" in l or "barrou" in l]
        log(f"{voz}: " + (" | ".join(linhas)[-600:] or saida.strip()[-300:] or "sem saída"))
        tj = SAIDA / voz / "trechos.json"
        if tj.exists():
            notas = [t.get("nota", 0) for t in json.loads(tj.read_text(encoding="utf-8"))]
            if min(notas) < NOTA_MIN or voz in REVISAR_SEMPRE:
                tj.replace(tj.with_name("trechos_revisar.json"))
                resumo.append(f"{voz}: {len(notas)} trecho(s), nota mínima {min(notas):.2f} = REVISAR antes de usar")
            else:
                resumo.append(f"{voz}: {len(notas)} trecho(s) bom(ns) (nota {min(notas):.2f}+), já entram nos Shorts")
        else:
            resumo.append(f"{voz}: nada achado")
        if "barrou o IP" in saida or "em pausa" in saida:
            log("YouTube barrou o IP no meio: paro a rodada")
            break
        if i < len(faltam) - 1:
            time.sleep(INTERVALO_S)
    log("fim: " + " || ".join(resumo))
    if resumo:
        try:
            import avisos
            avisos.enviar("Trechos originais dos personagens (madrugada):\n" + "\n".join(resumo)
                          + "\nRevisar = ouvir na pasta do personagem em D:\\hipercool-materiais\\amostras_voz\\"
                          "trechos_icones e renomear trechos_revisar.json pra trechos.json se a voz for a dele.",
                          "trechos_noite", html_ok=False)
        except Exception as e:  # noqa: BLE001
            log(f"aviso não foi: {e}")


if __name__ == "__main__":
    main()
