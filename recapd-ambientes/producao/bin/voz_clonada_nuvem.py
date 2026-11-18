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


PIPER = Path(os.environ.get("RAIZ_WIN", "/kaggle/working/raiz")) / "D/hipercool-materiais/models/piper"
_PIPERS = {}


def _base_piper(texto, saida, velocidade, nome="cadu"):
    """18/11 (dona: modo p3 = Kokoro/Francisca/Piper): a 3ª base, igual ao _base_tts('piper:...') do PC. O modelo
    abre 1x por processo; length_scale é o inverso da velocidade."""
    import wave
    from piper import PiperVoice, SynthesisConfig
    if nome not in _PIPERS:
        _PIPERS[nome] = PiperVoice.load(str(PIPER / f"pt_BR-{nome}-medium.onnx"))
    cfg = SynthesisConfig(length_scale=round(1.0 / max(0.6, min(1.6, velocidade)), 3))
    with wave.open(str(saida), "wb") as w:
        _PIPERS[nome].synthesize_wav(texto, w, syn_config=cfg)


KITTEN_VENV = Path(os.environ.get("KITTEN_VENV", "/tmp/venvs_voz/kitten2"))
_KITTEN_SCRIPT = r'''
import json, sys, time
import numpy as np, soundfile as sf
from kittenml import KittenTTS
M = KittenTTS("KittenML/kitten-tts-2", backend="torch")
for saida, texto in json.load(open(sys.argv[1], encoding="utf-8")):
    t0 = time.time()
    try:
        a = M.generate(texto, voice="Portuguese", normalize=False)
        a = a.cpu().numpy() if hasattr(a, "cpu") else np.asarray(a)
        sf.write(saida, a.squeeze(), M.sample_rate)
        print("OK", saida, round(time.time() - t0, 1), flush=True)
    except Exception as e:
        print("ERRO", saida, type(e).__name__, str(e)[:200], flush=True)
'''


def kitten_pronto():
    """O venv do Kitten 2 existe e importa (o kaggle_trabalhador cria em /tmp/venvs_voz/kitten2 quando há GPU)."""
    py = KITTEN_VENV / "bin" / "python"
    if not py.exists():
        return False
    return subprocess.run([str(py), "-c", "import kittenml"], capture_output=True, timeout=120).returncode == 0


def _bases_kitten(itens, lista_dir):
    """18/11 dona ("vamos começar com o padrão" — modo kitten_tudo): gera de UMA vez, num processo só (o modelo abre
    1x: ~35 s; cada fala ~5 s na GPU), a base de todo item com motor "kitten", com a voz pronta "Portuguese" do Kitten 2
    (sem copiar o jeito de ninguém: o timbre do narrador vem do RVC). Item que falhar fica sem 'entrada' e cai pro
    Kokoro no laço do lote — o vídeo nunca sai sem voz."""
    ped = []
    for i, it in enumerate(itens, 1):
        if it.get("motor") == "kitten" and not it.get("entrada"):
            ped.append([str(lista_dir / f"_kitten_{i}.wav"), it["texto"], i])
    if not ped:
        return
    py = KITTEN_VENV / "bin" / "python"
    scr = lista_dir / "_kitten_gerar.py"
    scr.write_text(_KITTEN_SCRIPT, encoding="utf-8")
    pj = lista_dir / "_kitten_ped.json"
    pj.write_text(json.dumps([[s, t] for s, t, _i in ped], ensure_ascii=False), encoding="utf-8")
    t0 = time.time()
    r = subprocess.run([str(py), str(scr), str(pj)], capture_output=True, text=True, timeout=3 * 3600)
    ok = 0
    for saida, _t, i in ped:
        if Path(saida).exists() and Path(saida).stat().st_size > 1000:
            itens[i - 1]["entrada"] = saida
            ok += 1
        else:
            itens[i - 1].pop("motor", None)  # sem a frase do Kitten: o lote gera Kokoro no lugar
            itens[i - 1]["tom_base"] = "1_kokoro"
    print(f"[kitten] {ok}/{len(ped)} frases em {time.time() - t0:.0f} s"
          + ("" if r.returncode == 0 else f" (saiu {r.returncode}: {(r.stderr or '')[-300:]})"), flush=True)


def lote(voz, lista):
    """26/10 (dona: "as vozes clonadas dos Cortes"): base Kokoro também — item sem 'entrada' gera o Kokoro aqui,
    com o tom da base certa (tom_1_kokoro / tom_2_edge_francisca), igual ao lote do PC."""
    voz = Path(voz).name  # 03/11: se vier caminho completo em VOZ_CLONADA, modelo / f"{voz}.pth" perdia a subpasta
    itens = json.loads(Path(lista).read_text(encoding="utf-8"))
    modelo = VOZES / voz
    tons = {p.stem[4:]: int(p.read_text().strip()) for p in modelo.glob("tom_*.txt")}
    f_on, f_q, f_t = _formante(voz)
    lista_dir = Path(lista).resolve().parent
    if any(it.get("motor") == "kitten" for it in itens):  # 18/11: modo kitten_tudo — todas as bases do Kitten antes
        _bases_kitten(itens, lista_dir)
    os.chdir(APPLIO)  # o Applio acha contentvec/rmvpe/fcpe por caminho relativo
    sys.path.insert(0, str(APPLIO))
    from core import run_infer_script
    for i, it in enumerate(itens, 1):
        t0 = time.time()
        origem = it.get("entrada")
        if not origem and it.get("motor") == "piper":  # 18/11: 3ª base do p3
            origem = str(lista_dir / f"_piper_{i}.wav")
            _base_piper(it["texto"], origem, it.get("velocidade", 1.0))
        elif not origem:
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
