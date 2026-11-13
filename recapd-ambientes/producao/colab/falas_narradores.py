"""falas_narradores.py — BANCO DE FALAS E SONS ORIGINAIS de cada narrador (04/11/2026, roda na hermes-staging).

Dona 04/11: "inserir o máximo de falas originais dos narradores que sejam genéricas — podemos ter um banco disso — e
principalmente das coisas que não são falas, como risadas etc." Fonte: o vídeo COMPLETO do narrador (baixado pelo
baixador do Kaggle, manhwa-drive:narradores_originais/<voz>/source.mp4). Só Drive: nenhuma conta, nenhum YouTube.

Por narrador:
  1. voz separada da trilha no áudio inteiro (audio-separator, UVR MDX, CPU)
  2. transcrição com tempo por palavra (faster-whisper small, pt)
  3. FALAS genéricas por padrão (saudação, inscrição/like, reação, despedida, risada escrita) — cortadas no limite da
     fala (silero-vad) com 80 ms de folga
  4. SONS que não são fala (EfficientAT, AudioSet): risada, risadinha, gargalhada, suspiro, respiração, ofego
  5. banco/<voz>/{falas,sons}/*.wav + banco.json; prévia previa_falas.wav / previa_sons.wav; sobe pro Drive
     (manhwa-drive:narradores_originais/<voz>/banco/). NADA entra em vídeo antes da dona ouvir.

    venv/bin/python falas_narradores.py <voz> [<voz> ...]
"""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DADOS = AQUI / "dados"
RC = ["rclone", "--config", "/opt/recap_central/rclone.conf"]
DRIVE = "manhwa-drive:narradores_originais"

PADROES = {  # categoria -> regex (texto do trecho em minúsculas)
    "saudacao": r"\b(salve|fala (galera|rapaziada|pessoal|meu povo)|e a[ií],? (galera|rapaziada|pessoal)|bem[- ]vindos?|"
                r"seja(m)? bem[- ]vindos?|tudo bem com vocês|beleza,? galera)\b",
    "inscricao": r"\b(inscrev\w*|deixa (o|aquele|seu) like|deixe (o|seu) like|ativa(r)? o sininho|comenta(r|m)? a[ií]|"
                 r"compartilh\w*|segue o canal|apoia(r)? o canal|membro do canal)\b",
    "reacao": r"^\W*(caraca|caramba|vixe|vish|eita|nossa|meu deus|que isso|rapaz|mano|uau|olha (só|isso)|sério|"
              r"não acredito|como assim|pera(í| a[ií])|calma a[ií]|misericórdia|socorro|gente)\b",
    "despedida": r"\b(é isso,? (galera|rapaziada|pessoal)|até a próxima|até o próximo|valeu,? (galera|rapaziada|pessoal)|"
                 r"tchau|fui|beijo(s)? (pra|para) (vocês|todos)|nos vemos)\b",
    "risada": r"\b(k{3,}|(ha){2,}|(he){2,}|(rs){2,})\b",
    # 12/11 dona ("o banco de falas deve ser ampliado pra usar principalmente piadas e coisas de mulheres, como de muito
    # RES-peito etc., trocadilhos, risadas"): o vídeo pede "piada" e "bordao" (anime_segments._FalasReais.CATS) e o
    # banco nunca teve essas categorias — só entrava saudação/inscrição/reação/despedida/risada escrita.
    "beleza": r"\b(res[- ]?peito|respeito|que (mulher|gata|deusa|beldade)|olha (essa|a) (mulher|moça|gata)|"
              r"(muito|que) (gostosa|linda|bonita|maravilhosa)|(a|essa) moça|delícia|que corpo|que (peitão|bundão)|"
              r"comissão de frente|par de|airbag|melões|faróis|pernão|cinturinha|ela (é|tá) (muito|demais))\b",
    "piada": r"\b(é (brincadeira|piada)|tô brincando|zueira|zoeira|não me julg\w*|que vergonha|passando vergonha|"
             r"o cara é (muito )?(burro|lerdo|liso|doido|maluco)|tá de (sacanagem|brincadeira)|só (faltou|falta)|"
             r"sacou|entendeu a (piada|referência)|trocadilho|ba dum|tum dum|piadinha|deu ruim|"
             r"(e|aí) (ele|ela) (fala|falou|disse|virou)|sem condição|que isso,? (mano|rapaz|meu))\b",
    "bordao": r"\b(meu deus do céu|ai ai|aí sim|é isso aí|olha o nível|que absurdo|que viagem|pode isso|"
              r"(ele|ela) é (o|a) (brabo|braba|cara|mina)|simplesmente|sinceramente|incrível|insano|surreal|"
              r"respeita|(se )?liga (só|nessa)|presta atenção)\b",
}
SONS = {"Laughter": "risada", "Giggle": "risadinha", "Snicker": "risadinha", "Belly laugh": "gargalhada",
        "Chuckle, chortle": "risadinha", "Sigh": "suspiro", "Breathing": "respiracao", "Gasp": "ofego",
        "Whistling": "assobio", "Clapping": "palmas"}


def sh(cmd, **k):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **k)


def audio_cheio(src, pasta):
    """04/11 16:25: separar a voz das 2h23 do Porão de uma vez levou 2h10 a 6,4 núcleos e 16 GB de RAM sem terminar.
    Agora: transcrição e sons no áudio ORIGINAL (o Whisper e o detector aguentam a trilha) e a voz é separada só de
    cada trecho escolhido (segundos) — ver cortar()."""
    bruto = pasta / "audio44.wav"
    if not bruto.exists():
        sh(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-ac", "2", "-ar", "44100", str(bruto)])
    return bruto


_SEP = {}


def _so_voz(trecho, pasta):
    """Separa a voz da trilha só deste trecho curto; falhou = o trecho como está (nunca derruba o narrador).
    04/11 19:25: chamar o audio-separator por trecho recarregava o modelo grande a cada corte (> 10 min num trecho de
    3 s com a CPU dividida) — agora o modelo leve Kim_Vocal_2 (MDX, ONNX) carrega 1x por narrador."""
    sep = pasta / "_sep_trecho"
    try:
        from audio_separator.separator import Separator
        if _SEP.get("pasta") != str(sep):
            sep.mkdir(parents=True, exist_ok=True)
            s = Separator(output_dir=str(sep), output_single_stem="Vocals", output_format="WAV")
            s.load_model(model_filename="Kim_Vocal_2.onnx")
            _SEP.update(s=s, pasta=str(sep))
        for f in sep.glob("*.wav"):
            f.unlink()
        saidas = _SEP["s"].separate(str(trecho))
        achou = next((sep / Path(x).name for x in saidas if "ocal" in Path(x).name), None)
        return achou if achou and achou.exists() else trecho
    except Exception as e:  # noqa: BLE001
        print(f"  separação do trecho falhou ({type(e).__name__}) — vai o áudio original", flush=True)
        return trecho


PARTES = 6  # 04/11 18:30: 1 processo usava só 1,6 dos 8 núcleos (2h+ no Porão de 2h23) — 6 partes ao mesmo tempo


def _transcrever_parte(args):
    wav, offset = args
    from faster_whisper import WhisperModel
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=1)
    segs, _ = m.transcribe(str(wav), language="pt", word_timestamps=True, vad_filter=True)
    return [{"ini": round(s.start + offset, 2), "fim": round(s.end + offset, 2), "texto": s.text.strip(),
             "palavras": [[round(w.start + offset, 2), round(w.end + offset, 2), w.word.strip()] for w in (s.words or [])]}
            for s in segs if s.text.strip()]


def transcrever(voz16, pasta):
    arq = pasta / "transcricao.json"
    if arq.exists():
        return json.loads(arq.read_text(encoding="utf-8"))
    from concurrent.futures import ProcessPoolExecutor
    dur = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(voz16)]).stdout)
    passo = dur / PARTES
    partes = []
    for k in range(PARTES):
        p = pasta / f"_parte{k}.wav"
        sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{k * passo:.2f}", "-t", f"{passo:.2f}", "-i", str(voz16), str(p)])
        partes.append((p, k * passo))
    with ProcessPoolExecutor(max_workers=PARTES) as ex:
        out = [s for lst in ex.map(_transcrever_parte, partes) for s in lst]
    for p, _ in partes:
        p.unlink(missing_ok=True)
    arq.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def falas(trans):
    """[(cat, ini, fim, texto)]: a FRASE curta que bate no padrão (até 6 s); frase longa = só as palavras do trecho."""
    achados = []
    for s in trans:
        t = s["texto"].lower()
        for cat, rx in PADROES.items():
            m = re.search(rx, t)
            if not m:
                continue
            # 12/11 dona ("as falas reais às vezes acabam bruscamente no meio de uma palavra; mesmo assim são muito
            # boas, ampliar"): frase inteira até FALA_MAX_S (10 s, era 6). Frase maior: o trecho do padrão vai até a
            # PRÓXIMA PAUSA de verdade (vírgula/ponto ou buraco >= 0,25 s entre palavras), nunca num nº fixo de
            # palavras — antes cortava "±2 palavras" e a fala parava no meio. FALA_CORTE_PAUSA=0 volta o jeito antigo.
            import os
            fala_max = float(os.environ.get("FALA_MAX_S", "10"))
            if s["fim"] - s["ini"] <= fala_max:
                achados.append((cat, s["ini"], s["fim"], s["texto"]))
            else:
                ws = s["palavras"]
                idx = [i for i, w in enumerate(ws) if re.search(rx, " ".join(x[2] for x in ws[max(0, i - 2):i + 3]).lower())]
                if not idx:
                    break
                if os.environ.get("FALA_CORTE_PAUSA", "1") == "0":
                    a, b = max(0, idx[0] - 2), min(len(ws) - 1, idx[0] + 3)
                else:
                    def pausa(k):  # depois da palavra k há fim de frase ou silêncio
                        return (ws[k][2].endswith((".", "!", "?", ",", ";", ":"))
                                or (k + 1 < len(ws) and ws[k + 1][0] - ws[k][1] >= 0.25))
                    # palavras EXATAS do padrão (início e fim do match), não a janela ±2 — senão o trecho parava
                    # antes da própria fala ("...ele nem," sem o "salve galera")
                    pos, ini_w = 0, []
                    for w in ws:
                        ini_w.append(pos)
                        pos += len(w[2]) + 1
                    junto = " ".join(x[2] for x in ws).lower()
                    mm = re.search(rx, junto)
                    if not mm:
                        break
                    a0 = max(k for k, p in enumerate(ini_w) if p <= mm.start())
                    b0 = max(k for k, p in enumerate(ini_w) if p <= max(mm.start(), mm.end() - 1))
                    a = a0
                    while a > 0 and not pausa(a - 1) and ws[a0][0] - ws[a - 1][0] < fala_max / 2:
                        a -= 1
                    b = b0
                    while b < len(ws) - 1 and not pausa(b) and ws[b + 1][1] - ws[a][0] <= fala_max:
                        b += 1
                achados.append((cat, ws[a][0], ws[b][1], " ".join(x[2] for x in ws[a:b + 1])))
            break
    return achados


def sons(voz16):
    """[(nome, ini, fim, score)] — EfficientAT mn10_as, janelas de 1 s (passo 0,5 s), vizinhas viram 1 trecho."""
    import os
    os.chdir(AQUI / "EfficientAT")  # o EfficientAT lê metadata/ e resources/ por caminho relativo
    try:
        sys.path.insert(0, str(AQUI / "EfficientAT"))
        import csv
        import numpy as np
        import soundfile as sf
        import torch
        import librosa
        from models.mn.model import get_model as get_mn
        from models.preprocess import AugmentMelSTFT
        modelo = get_mn(pretrained_name="mn10_as").eval()
        mel = AugmentMelSTFT(n_mels=128, sr=32000, win_length=800, hopsize=320).eval()
        lab_csv = next((AQUI / "EfficientAT").rglob("class_labels_indices.csv"), None)
        labels = [r[2] for r in csv.reader(open(lab_csv, encoding="utf-8"))][1:] if lab_csv else []
        alvo = {i: SONS[n] for i, n in enumerate(labels) if n in SONS}
        x, sr = librosa.load(str(voz16), sr=32000, mono=True)
    except Exception as e:  # noqa: BLE001
        print(f"  sons: EfficientAT indisponível ({type(e).__name__}: {e})", flush=True)
        return []
    jan, passo, hits = 32000, 16000, []
    with torch.no_grad():
        for i in range(0, max(1, len(x) - jan), passo):
            w = torch.from_numpy(x[i:i + jan]).unsqueeze(0)
            p = torch.sigmoid(modelo(mel(w).unsqueeze(1))[0]).squeeze(0).numpy()
            melhor = max(alvo, key=lambda k: p[k]) if alvo else None
            if melhor is not None and p[melhor] >= 0.35:
                hits.append((alvo[melhor], i / 32000, float(p[melhor])))
    trechos = []
    for nome, t, s in hits:
        if trechos and trechos[-1][0] == nome and t <= trechos[-1][2] + 0.1:
            trechos[-1] = (nome, trechos[-1][1], t + 1.0, max(trechos[-1][3], s))
        else:
            trechos.append((nome, t, t + 1.0, s))
    return [x for x in trechos if 0.4 <= x[2] - x[1] <= 5.0]


def ajustar_vad(voz16, ini, fim):
    """Estende/encolhe [ini, fim] até o limite da fala pelo silero-vad (folga 80 ms)."""
    try:
        from silero_vad import get_speech_timestamps, load_silero_vad, read_audio
        if "m" not in ajustar_vad.__dict__:
            ajustar_vad.m = load_silero_vad()
            ajustar_vad.a = read_audio(str(voz16), sampling_rate=16000)
        a = ajustar_vad.a[int(max(0, ini - 1.0) * 16000):int((fim + 1.0) * 16000)]
        ts = get_speech_timestamps(a, ajustar_vad.m, sampling_rate=16000, return_seconds=True)
        base = max(0, ini - 1.0)
        dentro = [(base + t["start"], base + t["end"]) for t in ts if base + t["end"] > ini and base + t["start"] < fim]
        if dentro:
            ini, fim = min(d[0] for d in dentro), max(d[1] for d in dentro)
    except Exception:  # noqa: BLE001
        pass
    # 12/11 dona ("acabam bruscamente no meio de uma palavra"): 80 ms no fim comia a última sílaba (o Whisper marca o
    # fim da palavra cedo); fim com 0,30 s de folga e o fade de saída mais longo no cortar(). FALA_FOLGA_FIM=0.08 volta.
    import os
    return max(0, ini - 0.08), fim + float(os.environ.get("FALA_FOLGA_FIM", "0.30"))


def cortar(audio, ini, fim, saida):
    """Corta [ini, fim] (+0,5 s de margem pro separador), separa a voz, tira a margem e finaliza."""
    pasta = Path(saida).parent.parent.parent  # dados/<voz>
    m = 0.5
    bruto = pasta / "_trecho.wav"
    sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0, ini - m):.2f}", "-t", f"{fim - ini + 2 * m:.2f}", "-i",
        str(audio), "-ac", "2", "-ar", "44100", str(bruto)])
    so = _so_voz(bruto, pasta)
    off = m if ini >= m else ini
    sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{off:.2f}", "-t", f"{fim - ini:.2f}", "-i", str(so), "-af",
        "afade=t=in:d=0.03,areverse,afade=t=in:d=0.18,areverse,loudnorm=I=-20:TP=-2", "-ac", "1", "-ar", "44100",
        str(saida)])


def previa(arquivos, saida, sil):
    if not arquivos:
        return
    lst = saida.with_suffix(".txt")
    lst.write_text("".join(f"file '{a}'\nfile '{sil}'\n" for a in arquivos), encoding="utf-8")
    sh(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), str(saida)])
    lst.unlink()


def fazer(voz):
    t0 = time.time()
    pasta = DADOS / voz
    pasta.mkdir(parents=True, exist_ok=True)
    src = pasta / "source.mp4"
    if not src.exists():
        sh(RC + ["copyto", f"{DRIVE}/{voz}/source.mp4", str(src)], timeout=3600)
    vozw = audio_cheio(src, pasta)
    voz16 = pasta / "voz16.wav"
    if not voz16.exists():
        sh(["ffmpeg", "-y", "-v", "error", "-i", str(vozw), "-ac", "1", "-ar", "16000", str(voz16)])
    print(f"{voz}: áudio pronto ({time.time() - t0:.0f} s)", flush=True)
    trans = transcrever(voz16, pasta)
    print(f"{voz}: {len(trans)} trechos transcritos ({time.time() - t0:.0f} s)", flush=True)
    banco = pasta / "banco"
    for sub in ("falas", "sons"):
        (banco / sub).mkdir(parents=True, exist_ok=True)
        for f in (banco / sub).glob("*.wav"):
            f.unlink()
    itens, vistos = [], set()
    lista = falas(trans)
    gen = pasta / "genericos.json"  # 04/11: escolha da IA (falas_ia.py no PC) — bordões, piadas, reações que servem pra todos
    if gen.exists():
        lista += [(x["cat"], x["ini"], x["fim"], x["texto"]) for x in json.loads(gen.read_text(encoding="utf-8"))
                  if x["fim"] - x["ini"] <= 8]
    for n, (cat, a, b, txt) in enumerate(lista, 1):
        chave = re.sub(r"\W+", " ", txt.lower()).strip()
        if chave in vistos:
            continue
        vistos.add(chave)
        a, b = ajustar_vad(voz16, a, b)
        arq = banco / "falas" / f"{cat}_{n:03d}.wav"
        cortar(vozw, a, b, arq)
        itens.append({"tipo": "fala", "categoria": cat, "texto": txt, "ini": round(a, 2), "dur": round(b - a, 2),
                      "arquivo": f"falas/{arq.name}"})
    for n, (nome, a, b, s) in enumerate(sons(voz16), 1):
        arq = banco / "sons" / f"{nome}_{n:03d}.wav"
        cortar(vozw, max(0, a - 0.1), b + 0.15, arq)
        itens.append({"tipo": "som", "categoria": nome, "score": round(s, 2), "ini": round(a, 2),
                      "dur": round(b - a + 0.25, 2), "arquivo": f"sons/{arq.name}"})
    (banco / "banco.json").write_text(json.dumps({"voz": voz, "gerado": time.strftime("%d/%m %H:%M"),
                                                  "aprovado": False, "itens": itens}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    sil = pasta / "_sil.wav"
    sh(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "0.7", str(sil)])
    previa([str(banco / i["arquivo"]) for i in itens if i["tipo"] == "fala"], banco / "previa_falas.wav", sil)
    previa([str(banco / i["arquivo"]) for i in itens if i["tipo"] == "som"], banco / "previa_sons.wav", sil)
    sh(RC + ["copy", str(banco), f"{DRIVE}/{voz}/banco"], timeout=3600)
    cats = {}
    for i in itens:
        cats[i["categoria"]] = cats.get(i["categoria"], 0) + 1
    print(f"{voz}: PRONTO em {(time.time() - t0) / 60:.0f} min — {cats}", flush=True)


if __name__ == "__main__":
    for v in sys.argv[1:]:
        try:
            fazer(v)
        except Exception as e:  # noqa: BLE001
            print(f"{v}: ERRO {type(e).__name__}: {e}", flush=True)
