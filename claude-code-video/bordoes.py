"""Biblioteca de BORDÕES com o áudio ORIGINAL gravado (28/10, dona: "o isso isso isso pode ser pego gravado e não
clonado, pois o clone sai estranho; como são trechos curtos não tem problema").

Fica em D:\\hipercool-materiais\\assets\\bordoes\\ (todos os projetos podem usar): <nome>.mp3 + bordoes.json
(nome, texto, personagem, duracao_s, clima, publico). O roteiro do anúncio/entretenimento pode pôr `"bordao": nome`
numa cena: o gerar.py encaixa o áudio logo DEPOIS da fala daquela cena (na pausa), sem estragar o tempo do karaokê.

    python bordoes.py montar     # (re)corta tudo da lista FONTES (idempotente)
    python bordoes.py lista
Bordão novo: acrescente em FONTES (arquivo, início, fim) e rode montar.
"""
import sem_janela  # noqa: F401 — nenhum filho abre janela
import json
import subprocess
import sys
from pathlib import Path

PASTA = Path(r"D:\hipercool-materiais\assets\bordoes")
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FP = r"D:\hipercool-materiais\bin\ffprobe.exe"
MEMES = Path(r"D:\hipercool-materiais\assets\sfx_memes")
COLETANEA = MEMES / "As melhores frases da turma do Chaves.mp3"

# nome: (arquivo, ini, fim | None, texto, personagem, clima). Tempos conferidos pela transcrição (Whisper) 28/10.
FONTES = {
    "isso_isso_isso": (COLETANEA, 33.7, 38.0, "Isso, isso, isso!", "chaves", "acerto/comemoração"),
    "o_que_foi_o_que_ha": (COLETANEA, 180.0, 187.1, "O que que foi? O que que há?", "chaves", "confusão"),
    "ta_bom_nao_se_irrite": (COLETANEA, 177.0, 179.7, "Tá bom, mas não se irrite.", "chaves", "deboche"),
    "ninguem_tem_paciencia": (COLETANEA, 31.2, 33.4, "Ninguém tem paciência comigo.", "chaves", "drama/dor"),
    "prefiro_morrer": (COLETANEA, 158.5, 161.7, "Eu prefiro morrer do que perder a vida.", "chaves", "absurdo"),
    "trabalho_ruim": (COLETANEA, 20.4, 25.1, "Não tem trabalho ruim, senhora, o ruim é ter que trabalhar.", "seu_madruga",
                      "preguiça/automação"),
    "trabalhoso_viver_sem_trabalhar": (COLETANEA, 187.4, 192.6,
                                       "Não há nada mais trabalhoso do que viver sem trabalhar.", "seu_madruga",
                                       "trabalho/automação"),
    "gentalha": (COLETANEA, 71.0, 73.2, "Gentalha, gentalha!", "quico", "desprezo/concorrência"),
    "cale_se": (COLETANEA, 45.9, 50.1, "Cale-se, cale-se, cale-se, você me deixa louco!", "quico", "irritação"),
    "tomar_cafe": (COLETANEA, 102.0, 105.2, "Vamos entrar para tomar uma xícara de café.", "dona_florinda",
                   "convite/chamada"),
    "zero_pra_ele": (COLETANEA, 173.5, 176.7, "Ai que burro, dá zero pra ele!", "professor_girafales",
                     "erro/concorrente"),
    "ta_ta_ta": (PASTA / "_fonte" / "roMAwjKfHoM.mp3", 0.0, None, "Tá tá tá tá tá!", "professor_girafales",
                 "bronca/irritação"),
    "tolerancia_zero": (PASTA / "_fonte" / "vv2Y2bWr_KU.mp3", 0.0, None, "Pergunta idiota, tolerância zero!", "professor_girafales",
                        "regra/firmeza"),
    "risada_pica_pau": (PASTA / "_fonte" / "f4xgD_ocPt8.mp3", 0.0, None, "(risada do Pica-Pau)", "pica_pau",
                        "deboche/fecho"),
    "eu_nao_digo_pica_pau": (PASTA / "_fonte" / "_9Hp-GBcO30.mp3", 4.05, None, "Ai, eu não digo!", "pica_pau",
                             "deboche/surpresa"),
    "eu_nao_quero": (MEMES / "Chaves Eu não quero (meme para poops).mp3", 0.0, None, "Eu não quero!", "chaves",
                     "recusa"),
    "risada_plateia": (MEMES / "Risada de Fundo Chaves.mp3", 0.0, 3.5, "(risada da plateia)", "plateia",
                       "piada/fecho"),
    "risada_quico": (MEMES / "Risada do kiko (128 kbps).mp3", 0.0, None, "(risada do Quico)", "quico", "deboche"),
    "pancada": (MEMES / "efeito Sonoro som de pancada do Chaves.mp3", 0.0, 1.6, "(pancada)", "efeito", "impacto"),
    "ce_vai_morre": (MEMES / "cê vai morrê !! (faustão).mp3", 0.0, None, "Cê vai morrê!", "faustao", "exagero/perigo"),
    "olho_no_lance": (MEMES / "OLHO NO LANCE! Silvio luiz.mp3", 0.0, None, "Olho no lance!", "silvio_luiz",
                      "atenção/oferta"),
    "que_isso_calma": (MEMES / "que isso meu filho calma.mp3", 0.0, None, "Que isso, meu filho, calma!", "programa",
                       "calma/exagero"),
}


def _dur(p):
    r = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return round(float(r.stdout.strip() or 0), 2)


def montar():
    PASTA.mkdir(parents=True, exist_ok=True)
    cat = {}
    for nome, (src, ini, fim, texto, quem, clima) in FONTES.items():
        if not Path(src).exists():
            print(f"FALTA a fonte de {nome}: {src}")
            continue
        out = PASTA / f"{nome}.mp3"
        corte = ["-ss", f"{ini}"] + (["-to", f"{fim}"] if fim else [])
        filtro = ("silenceremove=start_periods=1:start_threshold=-42dB,areverse,"
                  "silenceremove=start_periods=1:start_threshold=-42dB,areverse,"
                  "afade=t=in:d=0.02,loudnorm=I=-16:TP=-1.5:LRA=11")
        r = subprocess.run([FF, "-v", "error", "-y", *corte, "-i", str(src), "-af", filtro, "-ar", "48000", "-ac", "2",
                            "-c:a", "libmp3lame", "-q:a", "2", str(out)], capture_output=True, text=True)
        if r.returncode or not out.exists():
            print(f"{nome}: ffmpeg falhou {r.stderr[-200:]}")
            continue
        d = _dur(out)
        if d > 8:  # bordão é curto: corta e esvanece
            subprocess.run([FF, "-v", "error", "-y", "-i", str(out), "-t", "6", "-af", "afade=t=out:st=5.4:d=0.6",
                            str(out.with_suffix(".tmp.mp3"))])
            out.with_suffix(".tmp.mp3").replace(out)
            d = _dur(out)
        cat[nome] = {"arquivo": out.name, "texto": texto, "personagem": quem, "duracao_s": d, "clima": clima,
                     "publico": "todos (Chaves é de todas as idades)" if quem not in ("faustao", "silvio_luiz",
                                                                                      "programa") else "adulto"}
        print(f"{nome:32} {d:5.2f}s  {texto}")
    (PASTA / "bordoes.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1), "utf-8")
    print(f"{len(cat)} bordões em {PASTA}")


def catalogo():
    p = PASTA / "bordoes.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else {}


if __name__ == "__main__":
    if sys.argv[1:] == ["montar"]:
        montar()
    else:
        for n, b in catalogo().items():
            print(f"{n:32} {b['duracao_s']:5.2f}s {b['personagem']:20} {b['texto']}")
