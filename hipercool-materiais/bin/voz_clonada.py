"""Voz clonada para todos os projetos: TTS base (Kokoro ou edge) -> RVC (Applio) com o timbre de um narrador.

Tudo em D:\\hipercool-materiais (nada no C:):
  python\\venv_vozes\\Scripts\\python.exe     roda este script (Python 3.11: o venv principal 3.13 nao instala RVC)
  tools\\applio                              RVC sem fairseq (rvc\\models e junction para models\\rvc)
  models\\kokoro                             kokoro-v1.0.onnx + voices-v1.0.bin
  models\\rvc\\treinos\\<voz>.log              log do treino (a pasta do treino e apagada quando o modelo fica pronto)
  models\\rvc\\vozes\\<voz>\\<voz>.pth/.index  modelo pronto (+ f0.txt = tom medio do narrador)
  amostras_voz\\dataset_narradores\\<voz>\\    material de treino p/ QUALQUER modelo (ver LEIA.txt da pasta)
  amostras_voz\\2026-10-18_vozes_clonadas\\    amostras p/ ouvir + STATUS.txt + fila.log

Uso:
  voz_clonada.py fila [--so-material]   material de treino dos parceiros, depois treino + amostras um por um
                           (prioridade baixa). Retomavel: pula o que ja esta pronto. Roda pela tarefa agendada
                           VozClonadaFila. --so-material: nao treina aqui (CPU leva dias); so gera as amostras de
                           quem ja tem modelo em models\\rvc\\vozes (treinado no Kaggle: amostras_voz\\kaggle_treino_rvc.ipynb,
                           bin\\empacotar_kaggle.py e bin\\importar_kaggle.py).
  voz_clonada.py vigiar    tarefa VozClonadaVigia (10 min): abre a pasta de cada voz assim que fica pronta (material e
                           amostras) e avisa no Telegram, idem nos marcos; relanca a
                           fila se morrer; FALHOU novo/travada -> agente kr/claude-sonnet-4.5 (diario VIGIA_DIARIO.txt);
                           chama bin\\kaggle_rpa.py auto (manda o lote de treino pro Kaggle e baixa/importa quando termina)
  voz_clonada.py falar <voz> "<texto>" <saida.wav> [--base kokoro:pm_alex | edge:<voz edge>] [--tom N]
                           [--velocidade 1.0 (so kokoro)] [--tom-base 1_kokoro|2_edge_francisca|3_edge_andrew]
  voz_clonada.py converter <voz> <narracao.wav|mp3> <saida.wav> [--tom N | --tom-base <base>]
                           PARA OS PROJETOS: a narracao que o projeto ja fez (ritmo de locutor) sai com a voz do
                           parceiro; tom automatico. CPU (sem GPU no PC1): ~2-4x a duracao do audio (~19x com o PC a 100%).
  voz_clonada.py lote <voz> <lista.json>   varias frases num processo so (ver lote()); usado pelo recap de anime
  --tom-base: tom FIXO medido na amostra daquela base (narracao frase a frase: o tom automatico por frase pula 1
  semitom de uma pra outra). Cache em models\\rvc\\vozes\\<voz>\\tom_<base>.txt.

QUAL VOZ BASE (dono ouviu as amostras, 19/10/2026):
  edge Francisca + clone = pronuncia PERFEITA
  edge Andrew + clone    = sotaque de gringo aprendendo portugues: NAO usar em pt
  Kokoro + clone         = bom pra emocao e fala acelerada, parece narracao de jogo
  Misto (recap de anime): Francisca nas frases normais, Kokoro na abertura e chegando nos impactos — mesma pessoa,
  ritmo que muda como narrador humano. Velocidade medida: edge+clone ~1/3 mais rapido que kokoro+clone.
"""
import argparse
import asyncio
import datetime
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.append(r"D:\hipercool-materiais\comum")
from ytdlp_vez import vez as _ytdlp_vez  # noqa: E402  (1 yt-dlp por vez no PC, todos os projetos)

RAIZ = Path(r"D:\hipercool-materiais")
APPLIO = RAIZ / "tools" / "applio"
PY = RAIZ / "python" / "venv_vozes" / "Scripts" / "python.exe"
TREINOS = RAIZ / "models" / "rvc" / "treinos"
VOZES = RAIZ / "models" / "rvc" / "vozes"
DATASET = RAIZ / "amostras_voz" / "dataset_narradores"
AMOSTRAS = RAIZ / "amostras_voz" / "2026-10-18_vozes_clonadas"
KOKORO = RAIZ / "models" / "kokoro"
TMP = RAIZ / "python" / "tmp"
FFMPEG = str(RAIZ / "bin" / "ffmpeg.exe")
SEPARADOR = Path(r"D:\tools\separador\Scripts\audio-separator.exe")  # o mesmo do intros_voz do hipercool
YTDLP = r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\Scripts\yt-dlp.exe"
GROQ = Path(r"D:\hipercool-videos\bin")  # groq_api.py: Whisper large-v3 sempre pelo proxy
SR = "32000"
EPOCAS = 40
DISCO_MIN_GB = 3
SEM_JANELA = 0x08000000 | 0x00004000  # CREATE_NO_WINDOW | BELOW_NORMAL: nao pisca janela nem atrasa o render

# 15 canais que autorizaram a voz em 15/10 (hipercool config\intros_voz.json); os 6 primeiros ja tem voz humana
# conferida nas aberturas, os outros 9 nao foram ouvidos (canal com voz de IA nao serve)
PARCEIROS = [("porao", "@oporaodacidadela"), ("drezin", "@DrezinNimes"), ("mike", "@mikemanhwa"),
             ("mattz", "@MattzManhwa"), ("ijax", "@iJaxManhwa"), ("momo", "@MomoManhwa"),
             ("pie", "@PieRecaps"),  # 19/10: pedido do dono, logo depois do momo
             ("mangaticos", "@mangaticos"), ("guugou", "@SR.GUUGOU"), ("omelhormanhwa", "@omelhormanhwa"),
             ("kkvirjao", "@KkVirjao"), ("doinsuka", "@Doinsuka"), ("solem8037", "@Solem_8037"),
             ("jubertim", "@Jubertim"), ("iki", "@IkiManhwa"), ("solemsun", "@solem_sun")]
BASES = [("1_kokoro", "kokoro:pm_alex"), ("2_edge_francisca", "edge:pt-BR-FranciscaNeural"),
         ("3_edge_andrew", "edge:en-US-AndrewMultilingualNeural")]
TEXTO_TESTE = ("Durante anos, ele foi chamado de lixo pela própria família. Ninguém acreditava nele. "
               "Mas naquela noite, quando abriu os olhos, uma janela azul apareceu bem na frente dele. "
               "Sistema ativado. E foi exatamente ali... que tudo começou a mudar.")

os.environ.update({
    "APPLIO_CONFIG_DIR": str(APPLIO / "config_local"),  # senao o Applio grava em %APPDATA% (C:)
    "APPLIO_LOGS_DIR": str(TREINOS),
    "HF_HOME": str(RAIZ / "models" / "huggingface"),
    "TORCH_HOME": str(RAIZ / "models" / "torch"),
    "TEMP": str(TMP),
    "TMP": str(TMP),
})


class DiscoCheio(Exception):
    pass


def _mostrar(arquivo):
    """Explorer com o arquivo selecionado. 22/10: com a lista ["explorer", f"/select,{x}"] o Python põe aspas em volta
    do argumento inteiro quando o caminho tem espaço ("animes recap\\shorts") e o Explorer abria a pasta Documentos."""
    subprocess.Popen(f'explorer /select,"{arquivo}"')


def _rodar(cmd, timeout=None):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, creationflags=SEM_JANELA)
    if r.returncode:
        raise RuntimeError(f"{Path(str(cmd[0])).name} saiu com {r.returncode}: {(r.stderr or r.stdout)[-300:]}")
    return r


def _checar_disco():
    livre = shutil.disk_usage("D:\\").free / 1024 ** 3
    if livre < DISCO_MIN_GB:
        raise DiscoCheio(f"disco D com {livre:.1f} GB livres (minimo {DISCO_MIN_GB})")


def _mp3(origem, destino, dur=None):
    _rodar([FFMPEG, "-v", "error", "-y", "-i", origem, *(["-t", str(dur)] if dur else []), "-ac", "1",
            "-codec:a", "libmp3lame", "-b:a", "192k", destino])


def tom_medio(wav, seg=90):
    """Mediana do F0 (Hz) de ate `seg` s do meio do arquivo."""
    import librosa
    import numpy as np
    dur = librosa.get_duration(path=str(wav))
    y, sr = librosa.load(str(wav), sr=16000, mono=True, offset=max(0.0, dur / 2 - seg / 2), duration=seg)
    f0, voz, _ = librosa.pyin(y, fmin=60, fmax=400, sr=sr)
    return float(np.nanmedian(f0[voz]))


# ─── material de treino ──────────────────────────────────────────────────────
def _parece_pt(titulo):
    t = f" {titulo.lower()} "
    return bool(re.search(r"[ãõçáéíóúâêô]", t)) or any(
        w in t for w in (" ele ", " ela ", " de ", " que ", " com ", " para ", " um ", " uma ", " seu ", " sua "))


def coletar(voz, canal):
    """13 min de voz limpa (1:00 a 14:00) de um video longo recente do canal -> dataset\\<voz>\\voz.wav."""
    pasta = DATASET / voz
    tmp = pasta / "_baixando"
    shutil.rmtree(tmp, ignore_errors=True)  # sobra de tentativa interrompida
    tmp.mkdir(parents=True)
    with _ytdlp_vez(f"voz clonada: lista {canal}"):
        r = _rodar([YTDLP, "--no-warnings", "--flat-playlist", "-j", "--playlist-end", "15",
                    f"https://www.youtube.com/{canal}/videos"], 180)
    videos = [json.loads(linha) for linha in r.stdout.splitlines() if linha.startswith("{")]
    longos = [v for v in videos if (v.get("duration") or 0) >= 900]
    if not longos:
        raise RuntimeError("nenhum video de 15 min ou mais entre os 15 mais novos")
    # titulo em ingles costuma ser a versao dublada (outra voz); ate 2 h baixa mais rapido
    longos.sort(key=lambda v: (not _parece_pt(v.get("title", "")), v["duration"] > 7200, v["duration"]))
    for v in longos[:5]:
        url = f"https://www.youtube.com/watch?v={v['id']}"
        try:  # baixa inteiro: --download-sections travava (18/10, ffmpeg recebia 0 bytes)
            with _ytdlp_vez(f"voz clonada: audio {canal}"):
                _rodar([YTDLP, "--no-warnings", "--no-playlist", "-q", "-f", "ba[language^=pt]/ba", "-o",
                        tmp / "bruto.%(ext)s", url], 1800)
            break
        except RuntimeError as e:  # 403 do YouTube costuma ser passageiro (pie, 19/10): espera e tenta o proximo video
            if not re.search(r"members|join this channel|private|unavailable|premiere|live event|403|forbidden",
                             str(e), re.I):
                raise
            time.sleep(30)
    else:
        raise RuntimeError("os 5 videos candidatos sao de membros/privados/indisponiveis")
    bruto = next(p for p in tmp.glob("bruto.*") if p.suffix not in (".part", ".wav"))
    cortado = tmp / "cortado.wav"
    _rodar([FFMPEG, "-v", "error", "-y", "-ss", "60", "-t", "480", "-i", bruto, "-ac", "1", "-ar", "44100", cortado])
    bruto.unlink()
    _rodar([SEPARADOR, cortado, "-m", "UVR-MDX-NET-Voc_FT.onnx", "--model_file_dir", SEPARADOR.parents[1] / "modelos",
            "--output_dir", tmp, "--output_format", "WAV", "--single_stem", "Vocals"], 7200)
    next(tmp.glob("*Vocals*.wav")).replace(pasta / "voz.wav")
    (pasta / "fonte.txt").write_text(f"{canal} {url} (de 1:00 a 14:00)\n{v.get('title', '')}\n", encoding="utf-8")
    shutil.rmtree(tmp)


def preparar(voz):
    """Trechos de 3 a 12 s com o texto (segmentos do Whisper juntados), no formato LJSpeech e no do GPT-SoVITS."""
    import soundfile as sf
    sys.path.insert(0, str(GROQ))
    import groq_api
    pasta = DATASET / voz
    TMP.mkdir(parents=True, exist_ok=True)
    mp3 = TMP / f"{voz}_whisper.mp3"
    _rodar([FFMPEG, "-v", "error", "-y", "-i", pasta / "voz.wav", "-ac", "1", "-ar", "16000", "-b:a", "64k", mp3])
    j = groq_api.transcrever(str(mp3), palavras=False)
    mp3.unlink()
    if not j:
        raise RuntimeError("transcricao do Groq falhou (sem proxy/chave?)")
    grupos, cur = [], None
    for s in j["segments"]:
        texto = " ".join(s["text"].split())
        if s.get("no_speech_prob", 0) > 0.5 or s.get("avg_logprob", 0) < -1.0 or not texto:
            cur = None
            continue
        if cur and s["start"] - cur["fim"] < 0.4 and s["end"] - cur["ini"] <= 12:
            cur["fim"], cur["texto"] = s["end"], f"{cur['texto']} {texto}"
            cur["lp"] = min(cur["lp"], s.get("avg_logprob", 0))
        else:
            cur = {"ini": s["start"], "fim": s["end"], "texto": texto, "lp": s.get("avg_logprob", 0)}
            grupos.append(cur)
    grupos = [g for g in grupos if 3 <= g["fim"] - g["ini"] <= 12]
    if not grupos:
        raise RuntimeError("nenhum trecho de 3 a 12 s na transcricao")
    audio, sr = sf.read(str(pasta / "voz.wav"), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    wavs = pasta / "wavs"
    wavs.mkdir(exist_ok=True)
    linhas_lj, linhas_sovits = [], []
    for n, g in enumerate(grupos, 1):
        id_ = f"{voz}_{n:04d}"
        a, b = int(max(0.0, g["ini"] - 0.05) * sr), int((g["fim"] + 0.1) * sr)
        sf.write(str(wavs / f"{id_}.wav"), audio[a:b], sr, subtype="PCM_16")
        linhas_lj.append(f"{id_}|{g['texto']}|{g['texto']}")
        linhas_sovits.append(f"wavs/{id_}.wav|{voz}|pt|{g['texto']}")
    ref = max((g for g in grupos if 8 <= g["fim"] - g["ini"] <= 12), key=lambda g: g["lp"], default=grupos[0])
    a, b = int(max(0.0, ref["ini"] - 0.05) * sr), int((ref["fim"] + 0.1) * sr)
    sf.write(str(pasta / "referencia.wav"), audio[a:b], sr, subtype="PCM_16")
    (pasta / "referencia.txt").write_text(ref["texto"] + "\n", encoding="utf-8")
    (pasta / f"{voz}.list").write_text("\n".join(linhas_sovits) + "\n", encoding="utf-8")
    (pasta / "metadata.csv").write_text("\n".join(linhas_lj) + "\n", encoding="utf-8")  # por ultimo: marca "pronto"
    return len(grupos), sum(g["fim"] - g["ini"] for g in grupos) / 60


# ─── treino RVC ──────────────────────────────────────────────────────────────
def _applio(voz, log, *args):
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n> core.py {' '.join(args)}\n")
        f.flush()
        p = subprocess.Popen([str(PY), "core.py", *args], cwd=APPLIO, stdout=f, stderr=subprocess.STDOUT,
                             creationflags=SEM_JANELA)
        while p.poll() is None:
            time.sleep(60)
            if args[0] == "train":
                cauda = Path(log).read_text(encoding="utf-8", errors="replace")[-6000:]
                ep = re.findall(r"epoch=(\d+)", cauda)
                vel = re.findall(r"training_speed=(\S+)", cauda)
                if ep:
                    _estado(voz, f"treinando: epoca {ep[-1]}/{EPOCAS}"
                                 + (f" (cada epoca leva {vel[-1]})" if vel else ""))
    fim = Path(log).read_text(encoding="utf-8", errors="replace")[-400:]
    if p.returncode or "failed" in fim.lower():
        raise RuntimeError(f"core.py {args[0]} falhou, ver {log}")


def treinar(voz, epocas):
    origem = DATASET / voz / "voz.wav"
    pasta = DATASET / voz / "_treino"  # so a voz limpa: o Applio le todo audio da pasta
    pasta.mkdir(exist_ok=True)
    if not (pasta / "voz.wav").exists():
        os.link(origem, pasta / "voz.wav")
    TREINOS.mkdir(parents=True, exist_ok=True)
    log = TREINOS / f"{voz}.log"
    _estado(voz, "treino: fatiando o audio")
    _applio(voz, log, "preprocess", "--model-name", voz, "--dataset-path", str(pasta), "--sample-rate", SR,
            "--cpu-cores", "2", "--normalization-mode", "post")
    _estado(voz, "treino: extraindo tom e timbre")
    _applio(voz, log, "extract", "--model-name", voz, "--f0-method", "rmvpe", "--cpu-cores", "2", "--gpu", "-",
            "--sample-rate", SR, "--embedder-model", "contentvec")
    for tentativa in range(1, 4):  # falta de RAM derruba o treino; o Applio retoma do ultimo checkpoint
        _estado(voz, "treino: comecando" if tentativa == 1 else f"treino: tentativa {tentativa}/3")
        try:
            _applio(voz, log, "train", "--model-name", voz, "--save-every-epoch", "5", "--save-only-latest",
                    "--total-epoch", str(epocas), "--sample-rate", SR, "--batch-size", "4", "--gpu", "-")
            break
        except RuntimeError:
            if tentativa == 3:
                raise
            time.sleep(600)
    pesos = sorted((TREINOS / voz).glob(f"{voz}_*e_*s.pth"),
                   key=lambda p: int(re.search(r"_(\d+)e_", p.name).group(1)))
    destino = VOZES / voz
    destino.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TREINOS / voz / f"{voz}.index", destino / f"{voz}.index")
    (destino / "f0.txt").write_text(f"{tom_medio(origem):.1f}\n", encoding="utf-8")
    shutil.copyfile(pesos[-1], destino / f"{voz}.pth")  # por ultimo: marca "pronto"
    shutil.rmtree(TREINOS / voz)  # ~1,5 GB por voz (fatias, features, checkpoints); o material fica no dataset
    shutil.rmtree(pasta)


# ─── fala ────────────────────────────────────────────────────────────────────
_KOKOROS = {}
_PONTUACAO = set(';:,.!?¡¿—…"«»“”()')


def _kokoro(modelo):
    if modelo not in _KOKOROS:
        from kokoro_onnx import Kokoro
        _KOKOROS[modelo] = Kokoro(str(KOKORO / modelo), str(KOKORO / "voices-v1.0.bin"))
    return _KOKOROS[modelo]


def _palavras_kokoro(texto, tempos):
    """[[ini, fim, palavra]] como o words.json do edge: fonemas agrupados pelos espaços. Contagem diferente da do texto
    (número lido por extenso etc.) = None (fica sem tempo por palavra, como antes)."""
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


# dono 23/10: o Kokoro lê "Ô"/"Ê" SOZINHOS como nome da letra ("ô circunflexo"): "Ô Ratinho!", "Ô loco, meu!".
# "Oh"/"Eh" saem com o mesmo som (ˈo / ˈe). Só a palavra sozinha; "você", "vovô" ficam como estão.
_CIRCUNFLEXO_SOLTO = re.compile(r"(?<!\w)([ÔôÊê])(?!\w)")


def _sem_circunflexo_solto(texto):
    return _CIRCUNFLEXO_SOLTO.sub(lambda m: {"Ô": "Oh", "ô": "oh", "Ê": "Eh", "ê": "eh"}[m.group(1)], texto)


def _base_tts(base, texto, saida, velocidade=1.0, palavras=None):
    """palavras = caminho do words.json (só Kokoro): usa a cópia do modelo que diz a duração de cada fonema
    (models\\kokoro\\kokoro-v1.0-dur.onnx, áudio idêntico) e grava o tempo de cada palavra."""
    motor, nome = base.split(":", 1)
    if motor == "kokoro":
        import soundfile as sf
        falado = _sem_circunflexo_solto(texto)  # a legenda (words.json) segue com o texto original
        if palavras and (KOKORO / "kokoro-v1.0-dur.onnx").exists():
            audio, sr, tempos = _kokoro("kokoro-v1.0-dur.onnx").create_timed(
                falado, voice=nome, speed=velocidade, lang="pt-br", sentence_pause=0.0, clause_pause=0.0)
            pal = _palavras_kokoro(texto, tempos)
            if pal:
                Path(palavras).write_text(json.dumps(pal, ensure_ascii=False), encoding="utf-8")
        else:
            audio, sr = _kokoro("kokoro-v1.0.onnx").create(falado, voice=nome, speed=velocidade, lang="pt-br")
        sf.write(str(saida), audio, sr)
    elif motor == "edge":
        import edge_tts
        mp3 = Path(saida).with_suffix(".mp3")
        asyncio.run(edge_tts.Communicate(texto, nome).save(str(mp3)))
        _rodar([FFMPEG, "-v", "error", "-y", "-i", mp3, saida])
        mp3.unlink()
    else:
        raise ValueError(f"base desconhecida: {base}")


def tom_fixo(voz, base_nome):
    """Semitons da voz base (amostra em _bases\\<base_nome>.wav) ate o tom medio do narrador, medido 1x e guardado."""
    cache = VOZES / voz / f"tom_{base_nome}.txt"
    if cache.exists():
        return int(cache.read_text().strip())
    alvo = float((VOZES / voz / "f0.txt").read_text().strip())
    tom = max(-24, min(24, round(12 * math.log2(alvo / tom_medio(AMOSTRAS / "_bases" / f"{base_nome}.wav")))))
    cache.write_text(str(tom))
    return tom


def converter(voz, entrada, saida, tom=None, dividir=False, index_rate=0.5, protect=0.33, volume_envelope=1.0,
              formant_shifting=False, formant_qfrency=1.0, formant_timbre=1.0):
    """Troca o timbre de `entrada` (wav) pelo do narrador; tom automatico = leva a mediana do F0 ate a dele.
    dividir=True: o Applio corta nos silencios e converte por partes (narracao longa, menos memoria)."""
    modelo = VOZES / voz
    if not (modelo / f"{voz}.pth").exists():
        raise SystemExit(f"voz '{voz}' sem modelo; prontas: {', '.join(sorted(v.name for v in VOZES.iterdir() if (v / f'{v.name}.pth').exists()))}")
    try:  # 23/10 (dona): o .index de voz parada fica no Drive; volta aqui, sem IA (bin\vozes_drive.py)
        import vozes_drive
        vozes_drive.garantir(voz)
    except Exception as e:  # noqa: BLE001
        print(f"vozes_drive: {e}", flush=True)
    if tom is None:
        alvo = float((modelo / "f0.txt").read_text().strip())
        tom = max(-24, min(24, round(12 * math.log2(alvo / tom_medio(entrada)))))
    os.chdir(APPLIO)  # o Applio acha contentvec/rmvpe por caminho relativo
    if str(APPLIO) not in sys.path:
        sys.path.insert(0, str(APPLIO))
    from core import run_infer_script
    # fcpe: ~10% mais rapido que o rmvpe com o mesmo som (teste 21/10, 12 vozes); "[error with torchfcpe...]" no log e so aviso
    run_infer_script(pitch=tom, index_rate=index_rate, volume_envelope=volume_envelope, protect=protect,
                     f0_method="fcpe", input_path=str(entrada), output_path=str(saida),
                     pth_path=str(modelo / f"{voz}.pth"), index_path=str(modelo / f"{voz}.index"),
                     split_audio=dividir, f0_autotune=False, f0_autotune_strength=1.0,
                     proposed_pitch=False, proposed_pitch_threshold=155.0, export_format="WAV",
                     embedder_model="contentvec", formant_shifting=formant_shifting,
                     formant_qfrency=formant_qfrency, formant_timbre=formant_timbre)
    return tom


def converter_audio(voz, entrada, saida, tom=None):
    """Para os projetos: narracao pronta (wav/mp3, com o ritmo de locutor de cada projeto) -> mesma fala com a voz
    do parceiro. Prioridade baixa (nao trava o render); acima de 1 min converte por partes."""
    import psutil
    import soundfile as sf
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    entrada, saida = Path(entrada).resolve(), Path(saida).resolve()
    saida.parent.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    wav = entrada
    if entrada.suffix.lower() != ".wav":
        wav = TMP / f"conv_{voz}_{os.getpid()}.wav"
        _rodar([FFMPEG, "-v", "error", "-y", "-i", entrada, "-ac", "1", wav])
    try:
        t0 = time.time()
        tom = converter(voz, wav, saida, tom, dividir=sf.info(str(wav)).duration > 60)
    finally:
        if wav != entrada:
            wav.unlink(missing_ok=True)
    print(f"{saida} (tom {tom:+d}, {time.time() - t0:.0f} s)", flush=True)


def falar(voz, texto, saida, base, tom, velocidade=1.0):
    import psutil
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    saida = Path(saida).resolve()
    saida.parent.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    bruto = TMP / f"base_{voz}_{os.getpid()}.wav"
    _base_tts(base, texto, bruto, velocidade)
    tom = converter(voz, bruto, saida, tom)
    bruto.unlink()
    print(f"{saida} (tom {tom:+d})", flush=True)


def _carregar_formant(voz):
    perfil = VOZES / voz / "perfil_v2.json"
    if perfil.exists():
        dados = json.loads(perfil.read_text(encoding="utf-8")).get("aplicar", {}).get("formant")
        if dados:
            return {"on": True, "q": dados.get("qfrency", 1.0), "t": dados.get("timbre", 1.0)}
    return {"on": False, "q": 1.0, "t": 1.0}


_KOKORO_VOZES_PT = ["pm_alex", "pm_santa"]


def lote(voz, lista):
    """Varias frases num processo so (o Applio carrega 1x; frase a frase eram ~1 min cada so de carga).
    lista.json: [{"saida", "tom_base", "entrada": wav} | {"saida", "tom_base", "texto", "velocidade"} (Kokoro)]
    + opcionais do clone 2.0 (perfil do narrador, bin\\clone2.py): "tom_extra" (semitons so desta frase),
    "f0_escala" (faixa de entonacao; patch nosso no Applio, env APPLIO_F0_ESCALA), "final_st" (fim de frase: semitons
    no ultimo quarto, env APPLIO_F0_FINAL_ST), "eq" ([[Hz, dB], ...] do microfone), "index_rate" (0-1, mistura do
    timbre do narrador), "protect" (0-0.5, preserva consoantes), "volume_envelope" (0-1, copia dinâmica da base).
    Kokoro grava <saida>.words.json (tempo de cada palavra) quando da pra casar com o texto."""
    import psutil
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    TMP.mkdir(parents=True, exist_ok=True)
    itens = json.loads(Path(lista).read_text(encoding="utf-8"))
    formant = _carregar_formant(voz)
    for i, it in enumerate(itens, 1):
        t0 = time.time()
        origem = it.get("entrada")
        if not origem:
            origem = TMP / f"lote_{voz}_{os.getpid()}.wav"
            kokoro_voz = _KOKORO_VOZES_PT[i % len(_KOKORO_VOZES_PT)]
            _base_tts(f"kokoro:{kokoro_voz}", it["texto"], origem, it.get("velocidade", 1.0),
                      palavras=it["saida"] + ".words.json")
        os.environ["APPLIO_F0_ESCALA"] = str(it.get("f0_escala", 1))
        os.environ["APPLIO_F0_FINAL_ST"] = str(it.get("final_st", 0))
        tom = converter(voz, origem, it["saida"], tom_fixo(voz, it["tom_base"]) + int(it.get("tom_extra", 0)),
                        index_rate=float(it.get("index_rate", 0.5)),
                        protect=float(it.get("protect", 0.33)),
                        volume_envelope=float(it.get("volume_envelope", 1.0)),
                        formant_shifting=formant["on"], formant_qfrency=formant["q"], formant_timbre=formant["t"])
        if it.get("eq"):
            eq = TMP / f"lote_eq_{os.getpid()}.wav"
            pontos = ";".join(f"entry({f},{g})" for f, g in it["eq"])
            _rodar([FFMPEG, "-v", "error", "-y", "-i", it["saida"], "-af", f"firequalizer=gain_entry='{pontos}'", eq])
            shutil.move(str(eq), it["saida"])
        if not it.get("entrada"):
            Path(origem).unlink(missing_ok=True)
        print(f"[{i}/{len(itens)}] {it['saida']} (tom {tom:+d}, ir={it.get('index_rate', 0.5)}, {time.time() - t0:.0f} s)", flush=True)
    os.environ.pop("APPLIO_F0_ESCALA", None)
    os.environ.pop("APPLIO_F0_FINAL_ST", None)


def amostras(voz):
    bases = AMOSTRAS / "_bases"
    bases.mkdir(parents=True, exist_ok=True)
    for nome, base in BASES:
        wav = bases / f"{nome}.wav"
        if not wav.exists():
            _base_tts(base, TEXTO_TESTE, wav)
            _mp3(wav, AMOSTRAS / f"base_{nome}_sem_clone.mp3")
    ref = DATASET / voz / "referencia.wav"
    _mp3(ref if ref.exists() else DATASET / voz / "voz.wav", AMOSTRAS / f"{voz}_0_original.mp3", dur=15)
    for nome, _b in BASES:
        out = TMP / f"{voz}_{nome}.wav"
        converter(voz, bases / f"{nome}.wav", out)
        _mp3(out, AMOSTRAS / f"{voz}_{nome}.mp3")
        out.unlink()


# ─── fila ────────────────────────────────────────────────────────────────────
_status, _marcos = {}, []


def _gravar_status():
    linhas = [f"Fila da voz clonada - atualizado {datetime.datetime.now():%d/%m %H:%M}",
              f"Amostras para ouvir: {AMOSTRAS}", f"Material de treino: {DATASET}", ""]
    linhas += [f"{v}: {_status.get(v, 'na fila')}" for v, _c in PARCEIROS] + [""] + _marcos
    (AMOSTRAS / "STATUS.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def _estado(voz, texto):
    _status[voz] = " ".join(str(texto).split())[:220]
    print(f"{datetime.datetime.now():%d/%m %H:%M} {voz}: {_status[voz]}", flush=True)
    _gravar_status()


def _marco(texto):
    _marcos.append(texto)
    print(f"{datetime.datetime.now():%d/%m %H:%M} {texto}", flush=True)
    _gravar_status()


def _pronta(voz):
    return (AMOSTRAS / f"{voz}_{BASES[-1][0]}.mp3").exists()


def fila(com_treino):
    import psutil
    if PAUSA_TESTES.exists():  # dono 21/10: produção primeiro — nem a tarefa nem o vigia rodam a fila com a pausa
        sys.exit(f"testes de voz pausados pelo dono ({PAUSA_TESTES})")
    AMOSTRAS.mkdir(parents=True, exist_ok=True)
    trava = AMOSTRAS / "fila.pid"
    if trava.exists() and psutil.pid_exists(int(trava.read_text() or 0)):
        sys.exit("a fila ja esta rodando")
    trava.write_text(str(os.getpid()))
    sys.stdout = sys.stderr = open(AMOSTRAS / "fila.log", "a", encoding="utf-8", buffering=1)
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    for voz, _c in PARCEIROS:
        if _pronta(voz):
            _status[voz] = "PRONTO - amostras na pasta"
        elif (DATASET / voz / "metadata.csv").exists():
            _status[voz] = "material pronto, esperando o treino"
    _marco(f"fila iniciada (pid {os.getpid()})")
    try:
        for voz, _c in PARCEIROS:  # 0) quem ja tem modelo (veio do Kaggle) ganha as amostras antes do material dos
            if _pronta(voz) or not (VOZES / voz / f"{voz}.pth").exists():  # outros, que leva ~35 min por canal
                continue
            ref = DATASET / voz / "referencia.wav"
            if not ref.exists() and not (DATASET / voz / "voz.wav").exists():  # material foi apagado (pos-Kaggle)
                continue
            _checar_disco()
            try:
                _estado(voz, "gerando as amostras")
                amostras(voz)
                _estado(voz, "PRONTO - amostras na pasta")
            except Exception as e:
                _estado(voz, f"FALHOU: {e}")
        for voz, canal in PARCEIROS:  # 1) material de treino de todos (serve p/ outros modelos tambem)
            if (DATASET / voz / "metadata.csv").exists():
                continue
            _checar_disco()
            try:
                if not (DATASET / voz / "voz.wav").exists():
                    _estado(voz, "baixando e separando a voz da musica")
                    coletar(voz, canal)
                _estado(voz, "transcrevendo e cortando os trechos")
                n, minutos = preparar(voz)
                _estado(voz, f"material pronto ({n} trechos, {minutos:.1f} min com texto), esperando o treino")
            except Exception as e:  # canal/rede/proxy: registra e segue pro proximo
                _estado(voz, f"FALHOU no material: {e}")
        _marco(f"MATERIAL PRONTO: {DATASET}")
        sem_modelo = []
        for voz, _c in PARCEIROS:  # 2) amostras, uma voz por vez (treino aqui so sem --so-material)
            if _pronta(voz) or not (DATASET / voz / "voz.wav").exists():
                continue
            if not com_treino and not (VOZES / voz / f"{voz}.pth").exists():
                sem_modelo.append(voz)
                continue
            _checar_disco()
            try:
                if not (VOZES / voz / f"{voz}.pth").exists():
                    treinar(voz, EPOCAS)
                _estado(voz, "gerando as amostras")
                amostras(voz)
                _estado(voz, "PRONTO - amostras na pasta")
            except Exception as e:
                _estado(voz, f"FALHOU: {e}")
        if sem_modelo:
            _marco(f"FILA PARADA: sem modelo ainda (treino no Kaggle): {', '.join(sem_modelo)}")
        else:
            _marco(f"TUDO PRONTO: {AMOSTRAS}")
    except DiscoCheio as e:
        _marco(f"PAROU: {e}")
    finally:
        trava.unlink(missing_ok=True)


# ─── vigia (tarefa VozClonadaVigia, a cada 10 min) ───────────────────────────
CLAUDE = Path(r"D:\hipercool-videos\tools\claude\claude.exe")
PROXY = Path(r"D:\hipercool-videos\secrets\claude_proxy.json")  # kr/claude-sonnet-4.5: o mesmo do vigia do Telegram
PARADO_H = 4
FINAIS = ("FILA PARADA", "TUDO PRONTO", "PAROU")
PROMPT_VIGIA = """Você é o VIGIA da fila de voz clonada, rodando sozinho, sem ninguém olhando. Outro agente mais forte
vai revisar tudo o que você fizer.

MOTIVO DESTA CHAMADA:
{motivo}

PRIMEIRO leia: D:\\hipercool-materiais\\amostras_voz\\2026-10-18_vozes_clonadas\\STATUS.txt, o fim do fila.log da mesma
pasta, o VIGIA_DIARIO.txt (o que vigias anteriores já fizeram) e D:\\hipercool-materiais\\bin\\voz_clonada.py (o
docstring e a função da etapa que falhou). Log de treino: D:\\hipercool-materiais\\models\\rvc\\treinos\\<voz>.log.

Se o motivo for o KAGGLE (treino na GPU grátis, pelo navegador): leia D:\\hipercool-materiais\\amostras_voz\\kaggle\\
LEIA.txt, STATUS.txt, estado.json (historico[-1].resumo = o RESUMO.txt do notebook, com o erro de CADA voz) e os
erro_*.png mais novos. Código: bin\\kaggle_rpa.py (navegador), bin\\importar_kaggle.py e o notebook
amostras_voz\\kaggle_treino_rvc.ipynb (o próximo lote sobe a versão do disco). Pode consertar esses arquivos (com
backup) e rodar `python\\venv\\Scripts\\python.exe bin\\kaggle_rpa.py baixar` para conferir de novo um lote que já
terminou. NUNCA rode `kaggle_rpa.py treinar` nem mexa no estado.json: duplica lote e gasta a cota de GPU (30 h/semana).
Erro de código no notebook = conserte o .ipynb para o próximo lote e peça REVISAR descrevendo o erro.

Se o motivo for um SHORT COM VOZ CLONADA (recap de anime, dono 19/10): leia
D:\\hipercool-materiais\\videos_voz_clonada\\LEIA.txt e _rodizio.json. Quem produz é o parceiro_diario (recapd) chamando
D:\\recapd-ambientes\\producao\\bin\\anime_auto.py; procure "voz clonada" e "[clone]" no
D:\\recapd-ambientes\\producao\\workspace\\anime\\_parceiro_<AAAAMMDD>.log e o clone.log em <pasta do vídeo>\\audio_cache\\
_base_clone\\. Só nestes arquivos você pode consertar (com backup): recapd bin\\anime_tts.py (preparar_clone),
bin\\anime_voz_clonada.py e a função lote() do bin\\voz_clonada.py; depois do conserto pode zerar a falha DAQUELA
combinação em "falhas" do _rodizio.json (com backup) pra ela tentar de novo. NUNCA rode anime_auto/parceiro_diario na
mão nem poste nada: a produção normal pega o próximo sozinha. "Nenhum Short novo há 24 h" pode ser só fila de postagem
cheia (a produção espera): confira no D:\\recapd-ambientes\\producao\\logs\\parceiro_producao.log antes de mexer.
EDGE "No audio was received" direto E em todos os proxies = PARÂMETRO que o edge grátis recusa (20/10: o contour no
SSML), NÃO bloqueio da Microsoft (20/10 um vigia concluiu "Microsoft bloqueou Francisca/Thalita/Andrew" e trocou a voz:
estava errado). Antes de concluir, teste a mesma voz com texto simples e sem rate/pitch/contour. NUNCA troque a voz base
do clone (Francisca, aprovada pelo dono) e NUNCA edite o edge_tts_engine.py (é código comum de todos os projetos).
CLONE 2.0 (comparações v1 × v2): leia D:\\hipercool-materiais\\amostras_voz\\clone2\\PROGRESSO.md, comparar.log/.err;
código bin\\clone2.py (pode consertar com backup; rodar de novo com o venv do recapd: `D:\\recapd-ambientes\\producao\\
venv\\Scripts\\python.exe bin\\clone2.py comparar` pula o que já está pronto). Não mexa no v1 da produção.

TESTES PAUSADOS PELO DONO (21/10): se existir D:\\hipercool-materiais\\amostras_voz\\TESTES_PAUSADOS.json, NUNCA relance a
fila, o clone2 nem o Kaggle e não apague esse arquivo — a produção de vídeos tem a vez.
SEU TRABALHO: entender o motivo. Se o conserto for pequeno e claro, conserte em bin\\voz_clonada.py. A fila pula o que
já está pronto e tenta de novo o que falhou quando roda outra vez; o vigia relança ela sozinho quando terminar, então
NÃO pare a fila que está rodando. Fila travada (log parado há horas e processo sem CPU): pode matar só os processos
DELA (linha de comando com voz_clonada, dataset_narradores, separador ou applio) e rodar
`powershell -Command Start-ScheduledTask VozClonadaFila`. Se não tiver certeza, NÃO mexa: descreva e peça revisão.
Se a tarefa não subir, o ÚNICO jeito manual é: `D:\\hipercool-materiais\\python\\venv_vozes\\Scripts\\pythonw.exe
D:\\hipercool-materiais\\bin\\voz_clonada.py fila --so-material` (venv_vozes E --so-material SEMPRE: sem ele a fila
TREINA NA CPU, leva dias e trava o PC — 19/10 13:30 um vigia rodou "fila" sem ele e às 15:21 começou a treinar o momo).
SEPARADOR LENTO NÃO É TRAVADO (19/10 um vigia matou 2 separações no meio achando que travaram): com o PC a 100% o
audio-separator faz 25–30 s por passo (~177 passos = mais de 1 h por canal). Só está travado se o tempo de CPU do
processo (Get-Process <pid> | % CPU) NÃO sobe em 10 minutos. Subindo = trabalhando: deixe terminar.

REGRAS DURAS (quebrar qualquer uma é pior do que deixar parado):
- Antes de editar QUALQUER arquivo, copie o original para
  D:\\hipercool-materiais\\amostras_voz\\2026-10-18_vozes_clonadas\\vigia_backups\\{hora}\\ (mesmo nome).
- NUNCA apague nada em amostras_voz, models, tools nem python. Nada de limpeza de disco.
- NUNCA use o disco C: (cache, temporário, instalação): tudo fica em D:\\hipercool-materiais.
- NUNCA instale ou atualize pacotes, nem mexa no Applio (tools\\applio), nos venvs ou no separador (D:\\tools).
- NUNCA mexa em outras tarefas agendadas nem na produção (hipercool, recapd, manhwa-react, postador) — fora os 3
  arquivos do Short com voz clonada citados acima; não mate
  processos que não sejam da fila de vozes; NUNCA mate pythonw em outra máquina.
- Canais: só os da lista PARCEIROS (quem adiciona é o dono). Não adicione, troque nem tire canal.
- Groq só pelo groq_api.py do hipercool (proxy obrigatório). Não poste nada em lugar nenhum.

RASTRO OBRIGATÓRIO: ACRESCENTE (não reescreva) ao fim de
D:\\hipercool-materiais\\amostras_voz\\2026-10-18_vozes_clonadas\\VIGIA_DIARIO.txt:
== {hora} — <resumo em 1 linha>
- Motivo / o que achei (com trecho de log) / o que fiz (arquivos e backup) / como desfazer
- Estado: RESOLVIDO | PRECISA REVISÃO | NADA A FAZER

ÚLTIMA LINHA da sua resposta, exatamente uma destas:
STATUS: OK
STATUS: CONSERTEI - <o que, em 1 linha>
STATUS: REVISAR - <por que, em 1 linha>
"""


def _avisar(titulo, texto, nivel="ok"):
    sys.path.insert(0, str(GROQ))
    try:
        import notificar  # mesmo bot do Telegram do postador
        tela, telegram = notificar.aviso(f"Voz clonada: {titulo}", texto, nivel=nivel)
        print(f"aviso '{titulo}': tela={tela} telegram={telegram}", flush=True)
    except Exception as e:  # avisar nunca derruba o vigia
        print(f"aviso falhou: {e}", flush=True)


def _chamar_agente(motivo):
    cfg = json.loads(PROXY.read_text(encoding="utf-8"))
    hora = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    env = dict(os.environ, ANTHROPIC_BASE_URL=cfg["base_url"], ANTHROPIC_AUTH_TOKEN=cfg["auth_token"], PYTHONUTF8="1")
    env.pop("ANTHROPIC_API_KEY", None)
    try:  # 23/10 (dona: Kiro esgotou): mesma reserva do vigia geral (D:\video-fila\ia_reserva.py, Gemini 3.8 etc.)
        if r"D:\video-fila" not in sys.path:
            sys.path.append(r"D:\video-fila")
        import ia_reserva
        ordem = ia_reserva.modelos(cfg["modelo"])
    except ImportError:
        ia_reserva, ordem = None, [cfg["modelo"]]
    texto = ""
    for modelo in ordem:
        print(f"{hora} chamando {modelo}: {motivo[:200]}", flush=True)
        extra = ia_reserva.AVISO_RESERVA if ia_reserva and ia_reserva.eh_reserva(modelo) else ""
        try:
            r = subprocess.run([str(CLAUDE), "-p", PROMPT_VIGIA.format(motivo=motivo, hora=hora) + extra,
                                "--model", modelo, "--output-format", "text", "--max-turns", "40",
                                "--dangerously-skip-permissions"],
                               cwd=str(RAIZ), env=env, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=1800, creationflags=SEM_JANELA)
            texto = (r.stdout or "") + (f"\n[stderr]\n{r.stderr}" if r.stderr else "")
        except subprocess.TimeoutExpired:
            texto = "[vigia] agente passou de 30 min e foi interrompido"
            break
        if not (ia_reserva and ia_reserva.falhou_sem_trabalhar(texto)):
            break
        ia_reserva.marcar(modelo)
        print(f"modelo {modelo} recusado pelo gateway: fica fora 1 h, vai o próximo", flush=True)
    (AMOSTRAS / f"vigia_agente_{hora}.log").write_text(texto, encoding="utf-8")
    m = re.findall(r"STATUS:?\**\s*\**\s*(OK|CONSERTEI|REVISAR)\**\s*[-—:]?\s*(.*)", texto, re.I)
    status, detalhe = (m[-1][0].upper(), m[-1][1].strip()) if m else ("REVISAR", "agente não devolveu STATUS")
    print(f"agente: {status} {detalhe[:200]}", flush=True)
    return status, detalhe, f"vigia_agente_{hora}.log"


VIDEOS = RAIZ / "videos_voz_clonada"  # Shorts com a voz clonada (recapd bin\anime_voz_clonada.py, dono 19/10)
VIDEO_PARADO_H = 24


def _producao_rodando():
    """Render de vídeo rodando no PC1 (Cortes/hipercool): a fila de vozes só volta com ele parado (produção tem a vez)."""
    # 23/10: wmic substitui Get-CimInstance (timeout 90s -> 10s); wmic traz a linha de comando completa
    try:
        r = subprocess.run(["wmic", "process", "where", "name like 'python%'", "get", "commandline"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", creationflags=SEM_JANELA, timeout=10)
    except (subprocess.TimeoutExpired, OSError):
        return True
    return any(m in (r.stdout or "") for m in ("anime-pipeline.py", "parceiro_diario.py producao", "hiper-pipeline", "fila.py ciclo"))


def _vigiar_videos(est, avisados, agora):
    """Cada Short novo com a voz clonada: abre a pasta com o vídeo selecionado + aviso (dono: "assim que tiver os
    primeiros vídeos, abra pra mim"). Falha nova ou rodízio parado há 24 h = motivo pro agente (est["video_motivo"])."""
    arq = VIDEOS / "_rodizio.json"
    r = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {"feitos": {}, "falhas": {}}
    for k, info in r.get("feitos", {}).items():
        # dono 21/10: o vídeo não é mais copiado pra cá; quem abre na tela é o laço dos Shorts novos (abaixo). Aqui só
        # o aviso com o narrador. Chave com o nome da antiga cópia (= .txt com .mp4): os já avisados não repetem.
        if not info.get("video") or not info.get("txt"):
            continue
        video = Path(info["video"])
        chave = f"video:{k}:{Path(info['txt']).with_suffix('.mp4').name}"
        if chave in avisados:
            continue
        if f"video:{k}" in avisados and video.exists() and video.stat().st_mtime < 1792542600:  # anteriores a 20/10 21:30
            avisados.append(chave)
            continue
        if not video.exists():
            continue
        _avisar(f"Short com a voz clonada: {k}", f"{video.parent.name}\nPostagem normal pela fila do canal.\n"
                f"Narração: {info['txt']}", "info")
        avisados.append(chave)
    # dono 21/10: "só um abriu a pasta sozinho" — abre TODO Short novo pronto (qualquer voz), não só os com clone
    shorts = RAIZ / "animes recap" / "shorts"
    desde_todos = est.setdefault("todos_desde", agora)
    for mp4 in sorted(shorts.glob("*/video.mp4"), key=lambda p: p.stat().st_mtime) if shorts.exists() else []:
        chave = f"short:{mp4.parent.name}"
        if mp4.stat().st_mtime < desde_todos or chave in avisados or agora - mp4.stat().st_mtime < 60:
            continue
        # 23/10 (dona: "a janela de vídeo pronto continua abrindo pra mim; só tem que abrir no NOTEBOOK, já no YouTube,
        # quando postar"): não abre mais o Explorer no PC1 — quem mostra é o telão do Acer (D:\video-fila\vitrine.py)
        avisados.append(chave)
    vistas = est.setdefault("video_falhas", {})
    for k, n in r.get("falhas", {}).items():
        if n > vistas.get(k, 0):
            est["video_motivo"] = (est.get("video_motivo", "") + f"\n- Short com voz clonada FALHOU: {k} ({n}ª vez; "
                                   "na 2ª o rodízio pula essa combinação)").strip()
    est["video_falhas"] = dict(r.get("falhas", {}))
    pendentes = [f"{v}:{b}" for v, _c in PARCEIROS if (VOZES / v / f"{v}.pth").exists()
                 for b in ("francisca", "kokoro", "misto")
                 if f"{v}:{b}" not in r.get("feitos", {}) and r.get("falhas", {}).get(f"{v}:{b}", 0) < 2]
    desde = max(arq.stat().st_mtime if arq.exists() else 0, est.setdefault("videos_desde", agora),
                est.get("video_parado_aviso", 0))
    if pendentes and (agora - desde) / 3600 > VIDEO_PARADO_H:
        est["video_parado_aviso"] = agora
        est["video_motivo"] = (est.get("video_motivo", "") + f"\n- Nenhum Short com voz clonada novo há {VIDEO_PARADO_H} h "
                               f"e faltam {len(pendentes)} (próximo: {pendentes[0]}).").strip()


COMPARAR = RAIZ / "amostras_voz" / "clone2" / "comparar_v1_v2"  # clone 2.0: original × v1 × v2 (bin\clone2.py)
# Dono 21/10: "os testes de clone de voz continuam voltando sozinhos, agora preciso priorizar a produção". Com este
# arquivo: a fila de material/amostras não roda, o vigia não relança nada (fila, clone2 comparar) e não roda o Kaggle.
# Continua: abrir na tela cada Short novo com voz clonada (produção). Apagar o arquivo = testes voltam.
PAUSA_TESTES = RAIZ / "amostras_voz" / "TESTES_PAUSADOS.json"


def _vigiar_clone2(est, avisados, agora):
    """Dono 19/10: "deixe o vigia pra abrir" as comparações v1 × v2: cada narrador novo abre selecionado + aviso;
    clone2.py comparar morreu antes de acabar = relança (3x em 6 h); FALHOU no log = motivo pro agente."""
    import psutil
    if not COMPARAR.parent.exists():
        return
    for mp3 in sorted(COMPARAR.glob("*_2_v2.mp3")):
        voz = mp3.name[:-len("_2_v2.mp3")]
        if f"clone2:{voz}" in avisados:
            continue
        _mostrar(mp3)
        _avisar(f"clone 2.0 do {voz} pronto", f"Comparar: {voz}_0_original (voz real), {voz}_1_v1, {voz}_2_v2 "
                f"(+ {voz}_2_v2_texto.txt).\nPasta aberta no PC: {COMPARAR}", "info")
        avisados.append(f"clone2:{voz}")
    faltam = [v for v, _c in PARCEIROS if (VOZES / v / f"{v}.pth").exists() and not (COMPARAR / f"{v}_2_v2.mp3").exists()]
    rodando = any("clone2.py" in " ".join(p.info["cmdline"] or []) for p in psutil.process_iter(["cmdline"]))
    if faltam and not rodando:
        tent = [t for t in est.get("clone2_relances", []) if agora - t < 6 * 3600]
        if len(tent) < 3:
            log = COMPARAR.parent / "comparar.log"
            with open(log, "a", encoding="utf-8") as fh, open(COMPARAR.parent / "comparar.err", "a") as fe:
                subprocess.Popen([r"D:\recapd-ambientes\producao\venv\Scripts\python.exe", "-u",
                                  str(RAIZ / "bin" / "clone2.py"), "comparar"], cwd=str(RAIZ), stdout=fh, stderr=fe,
                                 env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"), creationflags=SEM_JANELA)
            est["clone2_relances"] = tent + [agora]
            print(f"clone2 comparar relançado (faltam {len(faltam)})", flush=True)
        elif not est.get("clone2_motivo_dado"):
            est["clone2_motivo_dado"] = True
            est["video_motivo"] = (est.get("video_motivo", "") + "\n- clone 2.0: bin\\clone2.py comparar morreu 3x em "
                                   f"6 h (faltam {', '.join(faltam)}); ver amostras_voz\\clone2\\comparar.log/.err e "
                                   "PROGRESSO.md").strip()


def vigiar():
    import psutil
    arq_est = AMOSTRAS / "vigia_estado.json"
    est = json.loads(arq_est.read_text(encoding="utf-8")) if arq_est.exists() else {}
    sys.stdout = sys.stderr = open(AMOSTRAS / "vigia.log", "a", encoding="utf-8", buffering=1)
    arq_st = AMOSTRAS / "STATUS.txt"
    st = arq_st.read_text(encoding="utf-8") if arq_st.exists() else ""
    pid = AMOSTRAS / "fila.pid"
    rodando = pid.exists() and psutil.pid_exists(int(pid.read_text() or 0))
    falhas = [linha for linha in st.splitlines() if "FALHOU" in linha]
    agora = time.time()
    motivos = []

    avisados = est.setdefault("avisados", [])
    for marco, pasta in (("MATERIAL PRONTO", DATASET), ("TUDO PRONTO", AMOSTRAS)):
        if marco in st and marco not in avisados:
            subprocess.Popen(["explorer", str(pasta)])
            _avisar(marco.capitalize(), f"Pasta aberta no PC: {pasta}"
                    + (f"\nFalharam ({len(falhas)}):\n" + "\n".join(falhas) if falhas else "\nNenhuma falha."))
            avisados.append(marco)
    for linha in st.splitlines():  # cada voz abre assim que fica pronta (pedido do dono)
        m = re.match(r"^(\w+): (material pronto|PRONTO - amostras)", linha)
        if not m:
            continue
        voz, material = m.group(1), m.group(2).startswith("material")
        chave = f"{'material' if material else 'amostras'}:{voz}"
        if chave in avisados:
            continue
        if material:
            subprocess.Popen(["explorer", str(DATASET / voz)])
            _avisar(f"material de treino do {voz} pronto",
                    f"{linha.split(': ', 1)[1]}\nÉ a voz REAL dele (ainda não é a clonada).\n"
                    f"Pasta aberta no PC: {DATASET / voz}")
        else:
            _mostrar(AMOSTRAS / f"{voz}_{BASES[0][0]}.mp3")
            _avisar(f"amostras do {voz} prontas",
                    f"Pasta aberta no PC: {AMOSTRAS}\n{voz}_0_original.mp3 = a voz real, para comparar")
        avisados.append(chave)
    if "PAROU" in st and "PAROU" not in avisados:
        _avisar("fila parou", next(linha for linha in st.splitlines() if "PAROU" in linha), "erro")
        avisados.append("PAROU")

    terminou = any(f in st for f in FINAIS)
    # 21/10: a fila (separador) tomava a RAM e a produção ficou 4 h parada -> só relança sem render rodando
    pausado = PAUSA_TESTES.exists()
    livre = (rodando or not _producao_rodando()) and not pausado
    if livre and not rodando and not terminou:  # morreu no meio (PC reiniciou, erro): relanca, mas sem ficar em loop
        relances = [t for t in est.get("relances", []) if agora - t < 6 * 3600]
        if len(relances) < 3:
            subprocess.run(["powershell", "-NoProfile", "-Command", "Start-ScheduledTask VozClonadaFila"],
                           creationflags=SEM_JANELA)
            est["relances"] = relances + [agora]
            _avisar("fila relançada", "A fila tinha parado sem terminar (PC reiniciou?); relancei. Continua de onde parou.",
                    "aviso")
        else:
            motivos.append("- A fila morreu 3 vezes em 6 h logo depois de relançada (ver fila.log).")
    elif rodando and arq_st.exists() and (agora - arq_st.stat().st_mtime) / 3600 > PARADO_H:
        motivos.append(f"- A fila está rodando mas o STATUS.txt não muda há mais de {PARADO_H} h (travada?).")

    novas = [f for f in falhas if f not in est.get("falhas_vistas", [])]
    if novas:
        motivos.append("- Falhas novas:\n" + "\n".join(f"  {f}" for f in novas))

    if livre and terminou and not rodando and est.pop("relancar_ao_terminar", False):  # conserto do agente vale pra proxima
        subprocess.run(["powershell", "-NoProfile", "-Command", "Start-ScheduledTask VozClonadaFila"],
                       creationflags=SEM_JANELA)
        avisados[:] = [a for a in avisados if a not in ("MATERIAL PRONTO", "TUDO PRONTO")]
        _avisar("fila relançada", "Relancei a fila para tentar de novo o que o vigia consertou.", "info")

    sem_amostra = [v for v, _c in PARCEIROS if (VOZES / v / f"{v}.pth").exists() and not _pronta(v)]
    if livre and terminou and not rodando and sem_amostra and est.get("relance_modelos") != sem_amostra:  # modelo veio do Kaggle
        subprocess.run(["powershell", "-NoProfile", "-Command", "Start-ScheduledTask VozClonadaFila"],
                       creationflags=SEM_JANELA)
        est["relance_modelos"] = sem_amostra  # uma vez por conjunto: se as amostras falharem, quem cuida e o agente
        _avisar("fila relançada", f"Modelo pronto sem amostra ({', '.join(sem_amostra)}): relancei a fila para "
                "gerar as amostras.", "info")

    _vigiar_videos(est, avisados, agora)
    if est.get("video_motivo"):
        motivos.append(est["video_motivo"])
    if pausado:  # testes pausados pelo dono: só os vídeos da produção seguem abrindo
        print(f"{datetime.datetime.now():%d/%m %H:%M} testes pausados ({PAUSA_TESTES.name}): sem fila, clone2 e Kaggle",
              flush=True)
        arq_est.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
        return
    try:
        _vigiar_clone2(est, avisados, agora)
    except Exception as e:  # noqa: BLE001 — o resto do vigia não pode parar por isso
        print(f"clone2: {e}", flush=True)

    try:  # treino na GPU do Kaggle pelo navegador: manda o que espera treino e baixa/importa o lote que terminou
        r = subprocess.run([str(RAIZ / "python" / "venv" / "Scripts" / "python.exe"), str(RAIZ / "bin" / "kaggle_rpa.py"),
                            "auto"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800,
                           creationflags=SEM_JANELA)  # a tarefa do vigia morre em 1 h; o agente pode levar mais 30 min
        saida = (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        saida = "KAGGLE: FALHOU kaggle_rpa.py passou de 30 min"
    print(saida.strip()[-1500:], flush=True)
    fim = re.findall(r"^KAGGLE: (\w+) (.*)$", saida, re.M)
    evento, info = fim[-1] if fim else ("FALHOU", "kaggle_rpa.py terminou sem a linha KAGGLE (ver vigia.log)")
    if evento in ("ENVIADO", "IMPORTADO"):
        _avisar(f"Kaggle: lote {evento.lower()}", info, "info")
    elif evento == "FALHOU" and est.get("kaggle_falha") != info:  # mesma falha repetida avisa uma vez so
        _avisar("Kaggle falhou", f"{info}\nPrints: {RAIZ}\\amostras_voz\\kaggle", "erro")
    if evento == "FALHOU" and est.get("kaggle_falha") != info:  # o agente olha; fica pendente ate ele ser chamado
        est["kaggle_motivo"] = f"- Kaggle falhou: {info}"
    elif evento == "IMPORTADO" and "sem modelo" in info:
        est["kaggle_motivo"] = f"- Kaggle: lote voltou com voz sem modelo: {info}"
    if est.get("kaggle_motivo"):
        motivos.append(est["kaggle_motivo"])
    est["kaggle_falha"] = info if evento == "FALHOU" else None

    if not motivos:
        est["falhas_vistas"] = falhas
    elif agora - est.get("ultima_chamada", 0) > 3600:  # no limite de 1/h as falhas novas esperam a proxima rodada
        est["ultima_chamada"] = agora
        est["falhas_vistas"] = falhas
        est.pop("kaggle_motivo", None)
        est.pop("video_motivo", None)
        arq_est.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
        status, detalhe, log = _chamar_agente("\n".join(motivos))
        if status == "CONSERTEI":
            est["relancar_ao_terminar"] = True
        if status != "OK":
            _avisar(f"vigia {status}", f"{detalhe[:300]}\nRastro: {AMOSTRAS}\\VIGIA_DIARIO.txt e {log}",
                    "aviso" if status == "CONSERTEI" else "erro")
    print(f"{datetime.datetime.now():%d/%m %H:%M} rodando={rodando} terminou={terminou} falhas={len(falhas)} "
          f"motivos={len(motivos)}", flush=True)
    arq_est.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fila").add_argument("--so-material", action="store_true")
    sub.add_parser("vigiar")
    f = sub.add_parser("falar")
    f.add_argument("voz")
    f.add_argument("texto")
    f.add_argument("saida")
    f.add_argument("--base", default="kokoro:pm_alex")
    f.add_argument("--tom", type=int, default=None)
    f.add_argument("--velocidade", type=float, default=1.0)
    f.add_argument("--tom-base", choices=[n for n, _b in BASES])
    c = sub.add_parser("converter")
    c.add_argument("voz")
    c.add_argument("entrada")
    c.add_argument("saida")
    c.add_argument("--tom", type=int, default=None)
    c.add_argument("--tom-base", choices=[n for n, _b in BASES])
    lo = sub.add_parser("lote")
    lo.add_argument("voz")
    lo.add_argument("lista")
    a = ap.parse_args()
    if getattr(a, "tom_base", None) and a.tom is None:
        a.tom = tom_fixo(a.voz, a.tom_base)
    if a.cmd == "fila":
        fila(not a.so_material)
    elif a.cmd == "vigiar":
        vigiar()
    elif a.cmd == "converter":
        converter_audio(a.voz, a.entrada, a.saida, a.tom)
    elif a.cmd == "lote":
        lote(a.voz, a.lista)
    else:
        falar(a.voz, a.texto, a.saida, a.base, a.tom, a.velocidade)
