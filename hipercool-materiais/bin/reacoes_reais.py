"""reacoes_reais.py — REAÇÕES REAIS de cada narrador parceiro (22/10; item 3 da lista "FAZER IMEDIATAMENTE" do
D:\\video-fila\\CONTINUAR_MELHORIAS_2026-10-22.md; dono 22/10 13:05: "dá pra perceber que é IA").

Recorta do material REAL do narrador (amostras_voz\\dataset_narradores\\<voz>\\voz.wav, a voz limpa do treino do
clone) as interjeições curtas e soltas ("caraca", "nossa", "meu deus", "eita", "vixe"...) e grava em
models\\rvc\\vozes\\<voz>\\humano\\reacao_NN.wav + humano\\reacoes.json (arquivo próprio: o clone2.py humano reescreve
o humano.json inteiro). O narracao_curva.humanizar encaixa até 2 por vídeo logo depois de uma frase de impacto, SÓ com
a chave ligada (narracao_curva.reacoes_ligadas), que começa DESLIGADA até o dono ouvir a amostra.

Transcrição com tempo por palavra: Whisper large-v3 do Groq (hipercool bin\\groq_api.py, sempre pelo proxy Webshare),
guardada em D:\\tmp\\reacoes\\<voz>.json (não pede de novo). Não pesa a CPU da produção (só ffmpeg pra cortar).
Palavrão fica de fora (monetização). "cara", "mano", "gente" só valem bem isolados (são palavras comuns também).

    python reacoes_reais.py <voz|todos> [--previa]
      --previa: emenda as reações achadas em amostras_voz\\clone2\\humano\\<voz>_reacoes.wav pra ouvir
"""
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais")
VOZES = RAIZ / "models" / "rvc" / "vozes"
DATASET = RAIZ / "amostras_voz" / "dataset_narradores"
PREVIA = RAIZ / "amostras_voz" / "clone2" / "humano"
FFMPEG = str(RAIZ / "bin" / "ffmpeg.exe")
TMP = Path(r"D:\tmp\reacoes")
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
MAX_REACOES = 6
POR_ROTULO = 2
# (palavras normalizadas, isolamento mínimo antes, depois): as comuns ("cara", "mano") só bem soltas
# 22/10: o material é narração corrida (kkvirjao: 66-119 pausas em 8 min); a reação real vem no meio da fala com
# pausa curta (0,1-0,15 s). As fortes valem com pausa curta; as comuns só bem soltas.
PADROES = [(("caraca",), .1, .08), (("caramba",), .1, .08), (("nossa",), .1, .08), (("eita",), .1, .08),
           (("vixe",), .1, .08), (("vish",), .1, .08), (("putz",), .1, .08), (("uau",), .1, .08),
           (("uou",), .1, .08), (("meu", "deus"), .1, .08), (("misericordia",), .1, .08), (("socorro",), .15, .1),
           (("olha", "so"), .15, .1), (("serio",), .25, .2), (("cara",), .35, .3), (("mano",), .35, .3),
           (("gente",), .35, .3), (("oxe",), .1, .08), (("ue",), .25, .2)]
RISADA = re.compile(r"^(?:(?:ha){2,}h?|(?:kk)+k?|(?:he){2,}h?|(?:hah)+a?)$")
PALAVRAO = re.compile(r"porra|caralh|merda|puta|foda|cacete|bucet|pqp|viad|arromb", re.I)


def _norm(w):
    w = unicodedata.normalize("NFKD", str(w or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", w)


def _transcricao(voz, src):
    TMP.mkdir(parents=True, exist_ok=True)
    cache = TMP / f"{voz}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    mp3 = TMP / f"{voz}.mp3"  # 8 min de wav = 84 MB; o Groq aceita até 25 MB -> mp3 mono 16 kHz ~3 MB
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "16000", "-b:a", "48k", str(mp3)],
                   check=True, timeout=300, creationflags=SEM_JANELA)
    sys.path.append(r"D:\hipercool-videos\bin")
    import groq_api
    j = groq_api.transcrever(str(mp3), "pt", palavras=True, timeout=300)
    if not j or not j.get("words"):
        raise RuntimeError("Groq não devolveu as palavras (sem chave/proxy livre?)")
    cache.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    return j


def _silencios(src, limiar_db):
    """[(ini, fim)] dos silêncios do áudio REAL (o Groq devolve as palavras coladas: a pausa só aparece no som)."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(src), "-af",
                        f"silencedetect=noise={limiar_db:.0f}dB:d=0.1", "-f", "null", "-"],
                       capture_output=True, timeout=300, creationflags=SEM_JANELA)
    txt = (r.stderr or b"").decode("utf-8", "replace")
    ini = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", txt)]
    fim = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", txt)]
    return list(zip(ini, fim))


def _candidatas(palavras, silencios, tolera=0.25):
    """[(corte_ini, corte_fim, texto, rótulo, isolamento_s)] das interjeições com pausa REAL antes e depois (no
    áudio), sem palavrão por perto. O corte cai nas bordas das pausas (mais limpo que o tempo da palavra)."""
    out = []
    n = len(palavras)
    for i in range(n):
        for padrao, antes_min, depois_min in [(("risada",), .2, .15)] + PADROES:
            k = len(padrao)
            if i + k > n:
                continue
            if padrao == ("risada",):
                if not RISADA.match(_norm(palavras[i]["word"])):
                    continue
            elif tuple(_norm(palavras[i + x]["word"]) for x in range(k)) != padrao:
                continue
            ini, fim = float(palavras[i]["start"]), float(palavras[i + k - 1]["end"])
            antes = [s for s in silencios if abs(s[1] - ini) <= tolera and s[1] - s[0] >= antes_min]
            depois = [s for s in silencios if abs(s[0] - fim) <= tolera and s[1] - s[0] >= depois_min]
            if not antes or not depois:
                continue
            s_a = max(antes, key=lambda s: s[1])
            s_d = min(depois, key=lambda s: s[0])
            # folga pra dentro da pausa sem encostar na palavra vizinha (pausa curta = folga curta)
            a = s_a[1] - min(0.04, 0.5 * (s_a[1] - s_a[0]))
            b = s_d[0] + min(0.08, 0.6 * (s_d[1] - s_d[0]))
            if not 0.18 <= b - a <= 1.4:
                continue
            vizinhas = " ".join(palavras[x]["word"] for x in range(max(0, i - 3), min(n, i + k + 3)))
            if PALAVRAO.search(vizinhas):
                continue
            iso = min(max(s[1] - s[0] for s in antes), max(s[1] - s[0] for s in depois))
            out.append((a, b, " ".join(palavras[i + x]["word"].strip() for x in range(k)), "_".join(padrao),
                        round(iso, 2)))
    return out


def _cortar(src, ini, fim, ganho_db, dst):
    a, b = max(0.0, ini), fim  # já com a folga dentro das pausas reais (_candidatas)
    d = b - a
    subprocess.run([FFMPEG, "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", str(src),
                    "-af", f"volume={ganho_db:.1f}dB,afade=t=in:d=0.015,afade=t=out:st={max(0.0, d - 0.06):.3f}:d=0.06",
                    "-ac", "1", "-ar", "44100", str(dst)], check=True, timeout=60, creationflags=SEM_JANELA)
    vd = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(dst), "-af", "volumedetect", "-f", "null", "-"],
                        capture_output=True, timeout=60, creationflags=SEM_JANELA)
    pico = re.search(rb"max_volume: (-?[\d.]+) dB", vd.stderr or b"")
    media = re.search(rb"mean_volume: (-?[\d.]+) dB", vd.stderr or b"")
    pico, media = (float(pico.group(1)) if pico else 0.0), (float(media.group(1)) if media else -99.0)
    if pico > -1.0:  # estourou com o ganho: baixa só o que passou
        tmp = dst.with_suffix(".tmp.wav")
        subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(dst), "-af", f"volume={-1.0 - pico:.1f}dB", str(tmp)],
                       check=True, timeout=60, creationflags=SEM_JANELA)
        tmp.replace(dst)
    return round(d, 3), media


def reacoes(voz, previa=False):
    src = DATASET / voz / "voz.wav"
    pasta = VOZES / voz / "humano"
    if not src.exists() or not pasta.exists():
        print(f"{voz}: sem material (voz.wav do dataset ou pasta humano) — pulado", flush=True)
        return None
    try:
        hum = json.loads((pasta / "humano.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        hum = {}
    ganho = float(hum.get("ganho_db") or 0.0)
    # limiar do silêncio entre o fundo e a fala DESSE narrador (medidos pelo clone2 humano no mesmo voz.wav)
    piso, fala = float(hum.get("piso_db") or -60), float(hum.get("fala_db") or -30)
    j = _transcricao(voz, src)
    palavras = [w for w in j["words"] if str(w.get("word") or "").strip()]
    cand = _candidatas(palavras, _silencios(src, piso + 0.6 * (fala - piso)))
    cand.sort(key=lambda c: -c[4])  # mais solta primeiro = corte mais limpo
    escolhidas, por_rot = [], {}
    for c in cand:
        if por_rot.get(c[3], 0) >= POR_ROTULO or any(abs(c[0] - e[0]) < 2 for e in escolhidas):
            continue
        escolhidas.append(c)
        por_rot[c[3]] = por_rot.get(c[3], 0) + 1
        if len(escolhidas) >= MAX_REACOES:
            break
    for velho in pasta.glob("reacao_*.wav"):
        velho.unlink()
    lista = []
    for k, (ini, fim, texto, rot, iso) in enumerate(sorted(escolhidas)):
        dst = pasta / f"reacao_{k:02d}.wav"
        dur, media = _cortar(src, ini, fim, ganho, dst)
        if media < -40:  # quase muda: não serve
            dst.unlink(missing_ok=True)
            continue
        lista.append({"arq": dst.name, "dur": dur, "texto": texto, "rotulo": rot, "t": round(ini, 2),
                      "isolamento_s": iso, "media_db": round(media, 1)})
    info = {"gerado": f"{datetime.now():%d/%m %H:%M}", "fonte": str(src), "candidatas": len(cand), "reacoes": lista}
    tmp = pasta / "reacoes.json.tmp"
    tmp.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(pasta / "reacoes.json")
    if previa and lista:
        PREVIA.mkdir(parents=True, exist_ok=True)
        entradas, fc = [], []
        for i, r in enumerate(lista):
            entradas += ["-i", str(pasta / r["arq"])]
            fc.append(f"[{i}:a]aformat=sample_rates=44100:channel_layouts=mono,apad=pad_dur=0.7[a{i}]")
        fc.append("".join(f"[a{i}]" for i in range(len(lista))) + f"concat=n={len(lista)}:v=0:a=1[o]")
        subprocess.run([FFMPEG, "-y", "-v", "error", *entradas, "-filter_complex", ";".join(fc), "-map", "[o]",
                        str(PREVIA / f"{voz}_reacoes.wav")], check=True, timeout=120, creationflags=SEM_JANELA)
    print(f"{voz}: {len(lista)} reação(ões) de {len(cand)} candidata(s): "
          + ", ".join(f"'{r['texto']}' {r['dur']}s" for r in lista), flush=True)
    return info


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    alvo = sys.argv[1]
    vozes = sorted(p.parent.name for p in DATASET.glob("*/voz.wav")) if alvo == "todos" else [alvo]
    for v in vozes:
        try:
            reacoes(v, previa="--previa" in sys.argv)
        except Exception as e:  # noqa: BLE001  (uma voz não para as outras)
            print(f"{v}: FALHOU {type(e).__name__}: {str(e)[:160]}", flush=True)
