r"""arsenal_memes.py — arsenal de falas REAIS curtas de séries famosas pros vídeos (dona 28/10: "baixe todas as possíveis,
corte e estipule quantos segundos dá pra usar com segurança; são cortes de 2-3 palavras, tipo 'cara, ela tá na sua'").

Pra cada meme do MEMES: busca no YouTube (proxy, ytdlp_vez), baixa só o ÁUDIO de vídeos curtos, acha a frase com o
Whisper (tempo por palavra) e corta justo (folga 0,15 s antes / 0,4 s depois, teto TETO_S). Grava em
D:\hipercool-materiais\assets\memes_series\<nome>.wav + memes_series.json {nome: arquivo, frase, gatilhos, serie,
dur, fonte}. Quem usa: bin\anime_segments (frase da narração casa um gatilho -> o meme toca no respiro).

    python arsenal_memes.py            # baixa o que falta
    python arsenal_memes.py so=greg    # só esses
Segurança (decisão 28/10): corte de 1–4 s, teto 6 s (a dona ouviu que até 10 s é uso justo; ficamos bem abaixo),
no máximo 1 meme a cada ~2 min de vídeo e nunca o mesmo 2x no vídeo (quem aplica controla).
"""
import difflib
import json
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
import ytdlp_vez  # noqa: E402

SAIDA = Path(r"D:\hipercool-materiais\assets\memes_series")
CATALOGO = SAIDA / "memes_series.json"
MODELOS = Path(r"D:\hipercool-materiais\models\whisper")
TETO_S = 10.0
PAUSA_S = 0.45  # silêncio entre palavras que encerra a fala
MAX_DOWNLOADS = 3

# nome: (série, busca no YouTube, frase a achar no áudio, gatilhos na narração)
MEMES = {
    "pega_ladrao": ("Chaves", "chaves pega ladrão", "pega ladrão", ["ladrão", "roubou", "roubar", "furtou"]),
    "sem_querer_querendo": ("Chaves", "chaves foi sem querer querendo", "foi sem querer querendo",
                            ["sem querer", "acidente", "por acaso"]),
    "isso_isso_isso": ("Chaves", "chaves isso isso isso", "isso isso isso", ["conseguiu", "isso mesmo", "acertou em cheio"]),
    "nao_se_irrite": ("Chaves", "chaves tá bom mas não se irrite", "não se irrite", ["irritad", "nervos", "furioso"]),
    "ninguem_tem_paciencia": ("Chaves", "chaves ninguém tem paciência comigo", "ninguém tem paciência comigo",
                              ["paciência", "ninguém liga", "ignorad", "desprezad"]),
    "disco_voador": ("Chaves", "chaves já se foi o disco voador", "já se foi o disco voador",
                     ["foi embora", "partiu", "sumiu", "desapareceu", "saiu correndo"]),
    "tinha_que_ser_o_chaves": ("Chaves", "seu madruga tinha que ser o chaves de novo", "tinha que ser o chaves",
                               ["de novo", "outra vez", "tinha que ser"]),
    "madruga_olhinhos": ("Chaves", "seu madruga quero ver outra vez seus olhinhos de noite serena",
                         "quero ver outra vez seus olhinhos", ["violão", "cantou", "cantar", "serenata", "música"]),
    "pague_o_aluguel": ("Chaves", "seu barriga pague o aluguel seu madruga", "aluguel",
                        ["dívida", "devendo", "pagar", "cobrar", "cobrança"]),
    "gentalha": ("Chaves", "dona florinda não se misture com essa gentalha", "não se misture com essa gentalha",
                 ["pobre", "plebeu", "despreza", "nojo", "humilh"]),
    "astucia": ("Chapolin", "chapolin não contavam com minha astúcia", "não contavam com minha astúcia",
                ["plano", "astúcia", "truque", "armadilha", "enganou"]),
    "sigam_me": ("Chapolin", "chapolin sigam-me os bons", "sigam-me os bons", ["sigam", "atrás de mim", "vamos lá"]),
    "suspeitei": ("Chapolin", "chapolin suspeitei desde o princípio", "suspeitei desde o princípio",
                  ["suspeit", "desconfi", "eu sabia", "já sabia"]),
    "julius_centavos": ("Todo Mundo Odeia o Chris", "julius isso custa centavos todo mundo odeia o chris",
                        "centavos", ["comprar", "preço", "caro", "barato", "loja", "gastar", "pagou"]),
    "julius_nao_comprar": ("Todo Mundo Odeia o Chris", "julius se não comprar é mais barato",
                           "mais barato", ["comprar", "economiz", "gastar", "dinheiro"]),
    "rochelle_emprego": ("Todo Mundo Odeia o Chris", "rochelle meu marido tem dois empregos",
                         "meu marido tem dois empregos", ["não preciso", "emprego", "trabalh"]),
    "greg_ta_na_sua": ("Todo Mundo Odeia o Chris", "greg cara ela tá na sua todo mundo odeia o chris",
                       "cara ela tá tão na sua", ["gostou dele", "apaixon", "corou", "interessad", "romance", "olhou pra ele"]),
    "faustao_o_loco": ("Faustão", "faustão ô loco meu", "ô loco meu", ["incrível", "absurdo", "inacreditável", "surreal"]),
    "faustao_errou": ("Faustão", "faustão errou", "errou", ["errou", "falhou", "errado", "fracass"]),
    "bob_tô_pronto": ("Bob Esponja", "bob esponja eu tô pronto", "eu tô pronto", ["pronto", "preparado", "treinou"]),
    # 29/10 dona: "faltam falas originais dos personagens, como do Buzz Lightyear 'ao infinito e além', da Moana 'eu
    # sou Moana'" — os bordões REAIS dos personagens que também temos como voz clonada
    "buzz_infinito": ("Toy Story", "buzz lightyear ao infinito e além dublado", "ao infinito e além",
                      ["voou", "decolou", "subiu", "infinito", "lançou", "pulou do alto"]),
    "moana_sou_moana": ("Moana", "moana eu sou moana dublado", "eu sou moana",
                        ["sou eu", "eu sou", "apresentou", "se revelou", "quem eu sou"]),
    "vegeta_8000": ("Dragon Ball", "vegeta é mais de oito mil dublado", "mais de oito mil",
                    ["poder", "nível de poder", "força absurda", "monstruoso", "aura"]),
    "naruto_dattebayo": ("Naruto", "naruto nunca volto atrás na minha palavra dublado", "nunca volto atrás",
                         ["promessa", "prometeu", "jurou", "não desistir", "palavra"]),
    "seu_madruga_que_que_foi": ("Chaves", "seu madruga o que que foi o que que houve", "o que que foi",
                                ["o que houve", "o que aconteceu", "estranhou"]),
    "galvao_e_tetra": ("Galvão Bueno", "galvão bueno é tetra", "é tetra", ["venceu", "campeão", "vitória", "conquistou"]),
}


def _norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in s if not unicodedata.combining(c))).split()


def _yt(args, rotulo):
    if ytdlp_vez.pausado():
        raise SystemExit(f"yt-dlp em pausa ({ytdlp_vez.pausado() / 60:.0f} min) — rode de novo depois")
    with ytdlp_vez.vez(rotulo):
        r = subprocess.run([sys.executable, "-m", "yt_dlp", *args], capture_output=True, text=True,
                           encoding="utf-8", errors="ignore", timeout=600)
    if ytdlp_vez.bloqueio(r.stdout + r.stderr):
        ytdlp_vez.pausar("arsenal_memes: " + (r.stderr or "")[-150:])
        raise SystemExit("YouTube barrou o IP — pausei o yt-dlp e parei")
    return r


def _whisper():
    from faster_whisper import WhisperModel
    return WhisperModel("medium", device="cpu", compute_type="int8", download_root=str(MODELOS))


def _achar(modelo, wav, frase):
    """(início, fim) da fala que contém a frase, ou None. Dona 01/11 ("o Greg só fala 'ela tá na sua' e fica de fora o
    'cara'"): o corte era só a frase de busca; agora estende pros dois lados até o fim da frase (pontuação do Whisper)
    ou uma pausa (PAUSA_S)."""
    segs, _ = modelo.transcribe(str(wav), language="pt", word_timestamps=True, vad_filter=True)
    palavras = [(w.start, w.end, _norm(w.word), w.word.strip()) for s in segs for w in (s.words or [])]
    palavras = [(a, b, t[0], bruto) for a, b, t, bruto in palavras if t]
    alvo = _norm(frase)
    n = len(alvo)
    melhor = (0.0, None)
    for i in range(len(palavras) - n + 1):
        jan = [p[2] for p in palavras[i:i + n]]
        r = difflib.SequenceMatcher(None, " ".join(jan), " ".join(alvo)).ratio()
        if r > melhor[0]:
            melhor = (r, (i, i + n - 1))
    if melhor[0] < 0.72:
        return None
    i, j = melhor[1]
    fim_frase = lambda k: palavras[k][3][-1:] in ".!?…"  # noqa: E731
    while i > 0 and not fim_frase(i - 1) and palavras[i][0] - palavras[i - 1][1] < PAUSA_S \
            and palavras[j][1] - palavras[i - 1][0] < TETO_S:
        i -= 1
    while j + 1 < len(palavras) and not fim_frase(j) and palavras[j + 1][0] - palavras[j][1] < PAUSA_S \
            and palavras[j + 1][1] - palavras[i][0] < TETO_S:
        j += 1
    return palavras[i][0], palavras[j][1]


def main():
    so = next((a[3:].split(",") for a in sys.argv[1:] if a.startswith("so=")), None)
    refazer = "refazer" in sys.argv[1:]  # recorta de novo os já catalogados, do mesmo vídeo-fonte (sem busca)
    SAIDA.mkdir(parents=True, exist_ok=True)
    cat = json.loads(CATALOGO.read_text(encoding="utf-8")) if CATALOGO.exists() else {}
    modelo = None
    for nome, (serie, busca, frase, gatilhos) in MEMES.items():
        if (so and not any(nome.startswith(s) for s in so)) or (nome in cat and not refazer):
            continue
        if nome in cat and cat[nome].get("fonte"):
            achados = [{"url": cat[nome]["fonte"], "title": cat[nome].get("titulo_fonte")}]
        else:
            r = _yt(["--flat-playlist", "--dump-json", "--match-filter", "duration < 400", f"ytsearch8:{busca}"],
                    f"busca meme {nome}")
            achados = [json.loads(l) for l in r.stdout.splitlines() if l.strip().startswith("{")]
            achados = [a for a in achados if (a.get("duration") or 0) and a["duration"] < 400][:MAX_DOWNLOADS]
        feito = False
        for a in achados:
            url = a.get("url") or f"https://www.youtube.com/watch?v={a['id']}"
            with tempfile.TemporaryDirectory() as tmp:
                _yt(["-f", "bestaudio[ext=m4a]/bestaudio", "-o", f"{tmp}/a.%(ext)s", "--no-playlist", url],
                    f"download meme {nome}")
                arq = next(Path(tmp).glob("a.*"), None)
                if not arq:
                    continue
                wav = Path(tmp) / "a.wav"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(arq), "-ac", "1", "-ar", "16000", str(wav)],
                               check=True)
                modelo = modelo or _whisper()
                try:  # 28/10: mkl_malloc sem RAM (render rodando junto) derrubava o arsenal inteiro
                    pos = _achar(modelo, wav, frase)
                except (RuntimeError, MemoryError) as e:
                    print(f"{nome}: Whisper sem memória ({str(e)[:60]}) — pulo este vídeo", flush=True)
                    continue
                if not pos:
                    print(f"{nome}: frase não achada em {a.get('title', '')[:50]}", flush=True)
                    continue
                ini = max(0.0, pos[0] - 0.15)
                dur = min(TETO_S, pos[1] + 0.4 - ini)
                out = SAIDA / f"{nome}.wav"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ini:.2f}", "-t", f"{dur:.2f}", "-i", str(arq),
                                "-af", "afade=t=in:d=0.03,areverse,afade=t=in:d=0.08,areverse,loudnorm=I=-16",
                                "-ac", "2", "-ar", "44100", str(out)], check=True)
                cat[nome] = {"arquivo": out.name, "serie": serie, "frase": frase, "gatilhos": gatilhos,
                             "dur": round(dur, 2), "fonte": url, "titulo_fonte": a.get("title"),
                             "trecho": [round(ini, 2), round(ini + dur, 2)], "em": time.strftime("%Y-%m-%d %H:%M")}
                CATALOGO.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"{nome}: OK {dur:.1f} s de '{a.get('title', '')[:50]}'", flush=True)
                feito = True
                break
        if not feito:
            print(f"{nome}: NÃO saiu ({len(achados)} vídeos tentados)", flush=True)
    print(f"arsenal: {len(cat)} memes em {SAIDA}")


if __name__ == "__main__":
    main()
