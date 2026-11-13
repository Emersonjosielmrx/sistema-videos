"""voz_clonada_nuvem.py — o `lote` da voz clonada (D:\\hipercool-materiais\\bin\\voz_clonada.py) para o Kaggle com GPU.

Dona 25/10/2026: "o longo usa a voz clonada que usamos nos curtos — tudo roda no Kaggle". O voz_clonada.py do PC tem
coisas só do Windows (prioridade de processo, ffmpeg.exe, flags de janela); este faz o MESMO lote, com o mesmo Applio
(commit do PC + nosso pipeline.py) e os mesmos parâmetros: tom da voz base (tom_2_edge_francisca.txt) + tom_extra,
f0_escala/final_st (patch APPLIO_F0_*), index_rate/protect/volume_envelope, formante do perfil_v2 e EQ do microfone.
Bases Francisca (edge, vem pronta em 'entrada') e Kokoro (gerado aqui, kokoro_onnx + models/kokoro do pacote) — as
mesmas dos Cortes, inclusive o misto (26/10).

    python voz_clonada_nuvem.py lote <voz> <lista.json>
Variáveis: APPLIO_DIR (padrão /tmp/applio), VOZES_DIR (padrão <RAIZ_WIN>/D/hipercool-materiais/models/rvc/vozes).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

APPLIO = Path(os.environ.get("APPLIO_DIR", "/tmp/applio"))
VOZES = Path(os.environ.get("VOZES_DIR") or
             Path(os.environ.get("RAIZ_WIN", "/kaggle/working/raiz")) / "D/hipercool-materiais/models/rvc/vozes")


def _formante(voz):
    p = VOZES / voz / "perfil_v2.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8")).get("aplicar", {}).get("formant")
        if d:
            return True, d.get("qfrency", 1.0), d.get("timbre", 1.0)
    return False, 1.0, 1.0


KOKORO = Path(os.environ.get("RAIZ_WIN", "/kaggle/working/raiz")) / "D/hipercool-materiais/models/kokoro"
_KOKORO_VOZES_PT = ["pm_alex", "pm_santa"]  # o mesmo rodízio do voz_clonada.py do PC
_PONTUACAO = set(';:,.!?¡¿—…"«»“”()')
_CIRCUNFLEXO_SOLTO = re.compile(r"(?<!\w)([ÔôÊê])(?!\w)")
_KOKOROS = {}


def _kokoro(modelo):
    if modelo not in _KOKOROS:
        from kokoro_onnx import Kokoro
        _KOKOROS[modelo] = Kokoro(str(KOKORO / modelo), str(KOKORO / "voices-v1.0.bin"))
    return _KOKOROS[modelo]


def _palavras_kokoro(texto, tempos):
    grupos, atual = [], []
    for z in tempos:
        if z.phoneme == " ":
            grupos.append(atual)
            atual = []
        elif z.phoneme not in _PONTUACAO:
            atual.append(z)
    grupos = [g for g in grupos + [atual] if g]
    palavras = re.findall(r"\w+(?:[-']\w+)*", texto)
    if len(grupos) != len(palavras):
        return None
    return [[round(g[0].start, 3), round(g[-1].end, 3), p] for g, p in zip(grupos, palavras)]


def _base_kokoro(nome, texto, saida, velocidade, palavras):
    """Igual ao _base_tts('kokoro:...') do PC: 'Ô'/'Ê' soltos viram 'Oh'/'Eh' (senão lê o nome da letra) e, com o
    modelo de duração, grava o tempo de cada palavra (<saida>.words.json) pra legenda."""
    import soundfile as sf
    falado = _CIRCUNFLEXO_SOLTO.sub(lambda m: {"Ô": "Oh", "ô": "oh", "Ê": "Eh", "ê": "eh"}[m.group(1)], texto)
    if (KOKORO / "kokoro-v1.0-dur.onnx").exists():
        audio, sr, tempos = _kokoro("kokoro-v1.0-dur.onnx").create_timed(
            falado, voice=nome, speed=velocidade, lang="pt-br", sentence_pause=0.0, clause_pause=0.0)
        pal = _palavras_kokoro(texto, tempos)
        if pal:
            Path(palavras).write_text(json.dumps(pal, ensure_ascii=False), encoding="utf-8")
    else:
        audio, sr = _kokoro("kokoro-v1.0.onnx").create(falado, voice=nome, speed=velocidade, lang="pt-br")
    sf.write(str(saida), audio, sr)


def lote(voz, lista):
    """26/10 (dona: "as vozes clonadas dos Cortes"): base Kokoro também — item sem 'entrada' gera o Kokoro aqui,
    com o tom da base certa (tom_1_kokoro / tom_2_edge_francisca), igual ao lote do PC."""
    voz = Path(voz).name  # 03/11: se vier caminho completo em VOZ_CLONADA, modelo / f"{voz}.pth" perdia a subpasta
    itens = json.loads(Path(lista).read_text(encoding="utf-8"))
    modelo = VOZES / voz
    tons = {p.stem[4:]: int(p.read_text().strip()) for p in modelo.glob("tom_*.txt")}
    f_on, f_q, f_t = _formante(voz)
    lista_dir = Path(lista).resolve().parent
    os.chdir(APPLIO)  # o Applio acha contentvec/rmvpe/fcpe por caminho relativo
    sys.path.insert(0, str(APPLIO))
    from core import run_infer_script
    for i, it in enumerate(itens, 1):
        t0 = time.time()
        origem = it.get("entrada")
        if not origem:
            origem = str(lista_dir / f"_kokoro_{i}.wav")
            _base_kokoro(_KOKORO_VOZES_PT[i % len(_KOKORO_VOZES_PT)], it["texto"], origem,
                         it.get("velocidade", 1.0), it["saida"] + ".words.json")
        os.environ["APPLIO_F0_ESCALA"] = str(it.get("f0_escala", 1))
        os.environ["APPLIO_F0_FINAL_ST"] = str(it.get("final_st", 0))
        tom = tons.get(it.get("tom_base", "2_edge_francisca"), tons.get("2_edge_francisca", 0)) + int(it.get("tom_extra", 0))
        run_infer_script(pitch=tom, index_rate=float(it.get("index_rate", 0.5)),
                         volume_envelope=float(it.get("volume_envelope", 1.0)), protect=float(it.get("protect", 0.33)),
                         f0_method="fcpe", input_path=str(origem), output_path=str(it["saida"]),
                         pth_path=str(modelo / f"{voz}.pth"), index_path=str(modelo / f"{voz}.index"),
                         split_audio=False, f0_autotune=False, f0_autotune_strength=1.0, proposed_pitch=False,
                         proposed_pitch_threshold=155.0, export_format="WAV", embedder_model="contentvec",
                         formant_shifting=f_on, formant_qfrency=f_q, formant_timbre=f_t)
        if it.get("eq"):
            eq = Path(it["saida"]).with_suffix(".eq.wav")
            pontos = ";".join(f"entry({f},{g})" for f, g in it["eq"])
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", it["saida"], "-af",
                            f"firequalizer=gain_entry='{pontos}'", str(eq)], check=True)
            shutil.move(str(eq), it["saida"])
        if not it.get("entrada"):
            Path(origem).unlink(missing_ok=True)
        print(f"[{i}/{len(itens)}] {it['saida']} ({it.get('tom_base')}, tom {tom:+d}, {time.time() - t0:.1f} s)",
              flush=True)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "lote":
        lote(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
