"""Narração de um vídeo INTEIRO no Fish Audio (online) — chamado pelo anime_tts._narrar_online nos Shorts.
Dona 18/11: "quando for Shorts, priorizar gerar o áudio online e aí monta; controle de créditos de cada conta usando
uma por vez; se não houver créditos usa o mesmo p3 com técnicas".

A geração em si é do fish_http.gerar_frases (outro chat, 18/11): HTTP, 3 falas em paralelo, cache (texto repetido
não paga de novo), troca de conta quando o crédito acaba e Chrome quente da fabrica_fish (porta 9397) só para o token
do reCAPTCHA. Cada conta sai pelo IP fixo dela (fish_proxy). Roda no python da produção (não precisa do D:\\veo\\venv).

Este arquivo faz o que é da PRODUÇÃO:
- trava: uma narração por vez neste PC (_em_uso.lock; o fish_http de linha de comando usa a mesma);
- MP3 -> WAV mono 44,1 kHz (o que a montagem lê, igual às outras bases);
- <wav>.words.json com o tempo REAL de cada palavra do roteiro (legenda cinética no tempo da fala);
- nunca levanta: falhou = {} e o anime_tts segue no p3.

    import fish_lote
    feitos = fish_lote.gerar([(i, texto, "D:/.../audio_i.wav"), ...], log=print)   # -> {i: wav}
    fish_lote.preaquecer()   # opcional, no começo do vídeo: o Chrome abre enquanto o resto é montado
FISH_ONLINE=0 desliga tudo.
"""
import json, os, re, subprocess, sys, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))
if r"D:\logins-google" not in sys.path:
    sys.path.insert(0, r"D:\logins-google")
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
MAX_CHARS = 480
TRAVA = AQUI / "_em_uso.lock"


def _travar(prazo=600):
    for _ in range(prazo):
        try:
            fd = os.open(str(TRAVA), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:
                if time.time() - TRAVA.stat().st_mtime > 1800:  # trava velha (processo morto)
                    TRAVA.unlink()
                    continue
            except OSError:
                pass
            time.sleep(1)
    return False


def _soltar():
    try:
        TRAVA.unlink()
    except OSError:
        pass


def preaquecer():
    """Chame no começo do vídeo: a conta escolhida já vai abrindo o Chrome quente em segundo plano. Nunca levanta."""
    if not disponivel():
        return None
    try:
        import fish_http
        return fish_http.preaquecer()
    except Exception:  # noqa: BLE001
        return None


def _palavras(feitos, textos, log):
    """Sidecar <wav>.words.json [[ini, fim, palavra]] (formato do edge_tts_engine). Whisper 'small' na CPU (~1 s por
    frase curta); as palavras são as do ROTEIRO, casadas por ordem com os tempos. Contagem diferente = sem sidecar
    (a legenda estima pelo tamanho, como faz com o Kokoro sem tempos)."""
    m = None
    for tentativa in (1, 2):  # 19/11: RuntimeError de memória momentânea no PC1 — 1 nova tentativa, com menos threads
        try:
            import numpy as np, wave
            from faster_whisper import WhisperModel
            m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2 if tentativa == 2 else 4)
            break
        except Exception as e:  # noqa: BLE001
            if tentativa == 2:
                log(f"[fish] sem Whisper pros tempos das palavras ({type(e).__name__}) — legenda estimada")
                return
            time.sleep(10)
    ok = 0
    for i, wav in feitos.items():
        try:
            with wave.open(str(wav), "rb") as w:
                sr = w.getframerate()
                a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
            if sr != 16000:
                idx = np.linspace(0, len(a) - 1, int(len(a) * 16000 / sr)).astype(np.int64)
                a = a[idx]
            segs = list(m.transcribe(a, language="pt", word_timestamps=True)[0])
            tempos = [(float(x.start), float(max(x.end, x.start + 0.05))) for s in segs for x in (s.words or [])]
            palavras = re.findall(r"\S+", textos[i])
            if len(tempos) != len(palavras) or not tempos:
                continue
            Path(str(wav) + ".words.json").write_text(json.dumps(
                [[round(t0, 3), round(t1, 3), p] for (t0, t1), p in zip(tempos, palavras)], ensure_ascii=False),
                encoding="utf-8")
            ok += 1
        except Exception as e:  # noqa: BLE001
            log(f"[fish] tempos da frase {i}: {type(e).__name__}")
    log(f"[fish] tempos por palavra: {ok}/{len(feitos)} frases")


def disponivel():
    """Só no PC que tem o cofre das contas e o registro de créditos (o PC1): as contas do pool saem pelas pontes
    daqui. Outra máquina (PC2, desktop, Kaggle) nunca tenta — cai no p3 dela."""
    return (os.environ.get("FISH_ONLINE", "1") != "0" and Path(r"D:\logins-google\cofre\contas.json").exists()
            and (AQUI / "creditos.json").exists())


def voz_do_nicho(nicho=None):
    """19/11 dona: Neymar só em esporte; Iberê nas curiosidades; o resto o narrador do Chris (voz_por_nicho.json)."""
    try:
        m = json.loads((AQUI / "voz_por_nicho.json").read_text(encoding="utf-8"))
        return m.get((nicho or "").strip().lower()) or m.get("padrao")
    except (OSError, ValueError):
        return None


def gerar(frases, log=print, voz=None):
    """frases = [(i, texto, destino_wav)]. Devolve {i: destino_wav} das que saíram no Fish. Nunca levanta.
    voz = id da voz no site; sem voz = a do nicho do vídeo (NICHO_CLONE/PARCEIRO_TIPO) ou o narrador do Chris."""
    if not disponivel():
        return {}
    if not voz:
        voz = voz_do_nicho(os.environ.get("NICHO_CLONE") or os.environ.get("PARCEIRO_TIPO"))
    frases = [(i, t.strip(), str(d)) for i, t, d in frases if t and t.strip() and len(t.strip()) <= MAX_CHARS]
    if not frases:
        return {}
    if not _travar():
        log("[fish] outra narração ocupando há 10 min — sigo no p3")
        return {}
    t0 = time.time()
    try:
        import fish_http
        pedidos = [(i, t, str(Path(d).with_suffix(".fish.mp3"))) for i, t, d in frases]
        mp3s = fish_http.gerar_frases(pedidos, voz=voz, log=log)
        feitos = {}
        destino = {i: d for i, _, d in frases}
        for i, mp3 in mp3s.items():
            wav = destino[i]
            r = subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", wav],
                               capture_output=True, creationflags=0x08000000 if os.name == "nt" else 0)
            Path(mp3).unlink(missing_ok=True)
            if r.returncode == 0 and Path(wav).exists():
                feitos[i] = wav
        if feitos:
            _palavras(feitos, {i: t for i, t, _ in frases}, log)
        log(f"[fish] {len(feitos)}/{len(frases)} frases online em {time.time() - t0:.0f}s")
        return feitos
    except Exception as e:  # noqa: BLE001
        log(f"[fish] falhou ({type(e).__name__}: {str(e)[:150]}) — sigo no p3")
        return {}
    finally:
        _soltar()


if __name__ == "__main__":  # teste: python fish_lote.py "frase 1" "frase 2"
    out = Path(r"D:\tmp\fish_lote_teste")
    out.mkdir(parents=True, exist_ok=True)
    print(gerar([(k, t, str(out / f"audio_{k}.wav")) for k, t in enumerate(sys.argv[1:])]))
