# -*- coding: utf-8 -*-
"""Trava de qualidade do MS Energy: clipe ou short que falhar aqui NAO entra na fila de postagem.

Por que (analise 22/10, docs\\ANALISE_CAMPANHA.md): o video saia da foto em ~1 s, com faixa preta, sem o cartao da
marca, com outra pessoa no meio — e o pipeline dizia "sucesso". Medidas: parecido com a foto (quadro 0 e ao longo
do clipe), faixa preta (cropdetect), duracao/audio, juiz por visao (mesma cena? texto? deformacao?) e a fala ouvida
pelo Whisper comparada com o roteiro (as palavras com tempo tambem viram a legenda).
"""
import base64
import io
import json
import re
import subprocess
import unicodedata
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FP = r"D:\hipercool-materiais\bin\ffprobe.exe"
GATEWAY = Path(r"D:\veo\beta\secrets\gateway.json")
WHISPER_DIR = r"D:\hipercool-materiais\models\whisper"

_whisper = None

# 04/11: as solares (clientes reais = prioridade da dona) rodavam ABAIXO do normal (padrão do Agendador, prio 7) e
# perdiam a CPU pro VS Code/Chrome/lotes: whisper > 600 s e ffmpeg/ffprobe estourando o tempo DEPOIS do clipe do Veo
# aprovado (Advance 21:53, Globo 22:15 em 03/11). Todo pipeline solar importa este módulo: sobe para ACIMA do normal.
if __import__("os").name == "nt" and not __import__("os").environ.get("QA_WHISPER_THREADS"):  # filho do whisper fica baixo
    try:
        import ctypes as _ct
        _k = _ct.windll.kernel32
        _k.GetCurrentProcess.restype = _ct.c_void_p
        _k.SetPriorityClass(_ct.c_void_p(_k.GetCurrentProcess()), 0x00008000)  # ABOVE_NORMAL_PRIORITY_CLASS
    except Exception:  # noqa: BLE001
        pass


def probe(v):
    r = subprocess.run([FP, "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
                        "-of", "json", str(v)], capture_output=True, text=True, timeout=120)
    d = json.loads(r.stdout)
    vs = [s for s in d["streams"] if s["codec_type"] == "video"][0]
    return (float(d["format"]["duration"]), int(vs["width"]), int(vs["height"]),
            any(s["codec_type"] == "audio" for s in d["streams"]))


def quadro(v, t):
    r = subprocess.run([FF, "-v", "error", "-ss", f"{max(t, 0):.2f}", "-i", str(v), "-frames:v", "1",
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, timeout=300)
    return Image.open(io.BytesIO(r.stdout)).convert("RGB") if r.stdout else None


def parecido(a, b):
    """0..1 — correlacao dos tons de cinza 64x114 (1 = igual)."""
    if a is None or b is None:
        return None
    a = np.asarray(ImageOps.fit(a, (64, 114)).convert("L"), dtype=float).ravel()
    b = np.asarray(ImageOps.fit(b, (64, 114)).convert("L"), dtype=float).ravel()
    a -= a.mean()
    b -= b.mean()
    d = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return round(float(a @ b / d), 2)


def faixa_preta(v, dur, w, h):
    """True se o video tem faixa preta (encaixotado) em algum dos 3 trechos."""
    # o ultimo trecho conferido termina ~0,4 s antes do fim: a montagem corta os 0,3 s finais (o Veo as vezes
    # estraga o ultimo quadro, ex.: faixa preta lateral aos 7,8 s no teste de 22/10)
    for t in (min(1.0, dur / 4), dur / 2, max(dur - 1.5, 0), max(dur - 0.9, 0)):
        cmd = [FF, "-v", "info", "-ss", f"{t:.2f}", "-i", str(v), "-frames:v", "12",
               "-vf", "cropdetect=limit=0.09:round=2:reset=0", "-f", "null", "-"]
        # 01/11: com a RAM do PC1 no fim, 12 quadros passaram de 60 s e o TimeoutExpired derrubou o reel depois do
        # Veo já pago — agora tenta 1x com folga e, se ainda travar, pula este trecho
        r = None
        for tmo in (60, 180):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=tmo, encoding="utf-8",
                                   errors="replace")
                break
            except subprocess.TimeoutExpired:
                continue
        if r is None:
            continue
        achados = re.findall(r"crop=(\d+):(\d+):", r.stderr)
        if achados:
            cw, ch = map(int, achados[-1])
            if cw < 0.94 * w or ch < 0.94 * h:
                return True
    return False


def _norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


WHISPER_TRAVA = Path(r"D:\ms-energy\cache\whisper_vez.lock")
WHISPER_PRAZO_S = 600


def _transcrever_agora(v):
    global _whisper
    from faster_whisper import WhisperModel
    if _whisper is None:
        try:
            import os as _os
            _whisper = WhisperModel("medium", device="cpu", compute_type="int8",
                                    cpu_threads=int(_os.environ.get("QA_WHISPER_THREADS", "4")), download_root=WHISPER_DIR)
        except RuntimeError as e:  # memoria apertada (Chrome do Flow aberto): igual ao manhwa-react, 1 thread
            if "mkl_malloc" not in str(e):
                raise
            import os
            import time
            time.sleep(5)
            os.environ["MKL_NUM_THREADS"] = "1"
            _whisper = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=1, download_root=WHISPER_DIR)
    segs, _ = _whisper.transcribe(str(v), language="pt", word_timestamps=True, vad_filter=True, beam_size=5,
                                  condition_on_previous_text=False)
    return [(w.word.strip(), round(w.start, 2), round(w.end, 2)) for s in segs for w in (s.words or [])]


def transcrever(v):
    """Palavras ouvidas [(palavra, inicio, fim)] pelo Whisper medium local (mesmo modelo do hipercool).
    03/11: as 3 solares (MS, Advance, Globo) carregavam um medium CADA uma e guardavam até o fim — o PC1 ficou sem
    memória virtual ("mkl_malloc: failed to allocate memory", 14:44) e a MS travou 2,5 h no whisper. Agora: 1 whisper
    por vez no PC (trava de arquivo, espera até o prazo), o modelo sai da memória depois do uso e passou de
    WHISPER_PRAZO_S = erro (quem chama segue sem conferir a fala)."""
    global _whisper
    import gc
    import msvcrt
    import threading
    import time
    WHISPER_TRAVA.parent.mkdir(parents=True, exist_ok=True)
    fim = time.time() + WHISPER_PRAZO_S
    with open(WHISPER_TRAVA, "a+") as trava:
        while True:
            try:
                msvcrt.locking(trava.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.time() > fim:
                    raise RuntimeError("whisper: outra solar ocupou a vez por mais que o prazo")
                time.sleep(3)
        t = None
        try:
            # 24/11 (dona: "esse PC não é tão ruim pra uns navegadores deixarem ele inusável"): na thread, o whisper
            # que passava do prazo CONTINUAVA rodando escondido (4 núcleos + o modelo medium) até o programa acabar —
            # o reel_advance chegou a 5,2 GB reservados e o PC1 ficou sem memória. Agora roda num PROCESSO à parte,
            # em prioridade baixa: estourou o prazo = processo morto e a memória volta na hora. QA_WHISPER_THREAD=1
            # volta ao jeito antigo.
            import os
            if os.environ.get("QA_WHISPER_THREAD") != "1":
                return _transcrever_processo(v, max(30, fim - time.time()))
            res = {}

            def _rodar():
                try:
                    res["p"] = _transcrever_agora(v)
                except Exception as e:  # noqa: BLE001
                    res["e"] = e

            t = threading.Thread(target=_rodar, daemon=True)
            t.start()
            t.join(max(30, fim - time.time()))
            if t.is_alive():
                raise RuntimeError(f"whisper passou de {WHISPER_PRAZO_S} s")
            if "e" in res:
                raise res["e"]
            return res["p"]
        finally:
            if t is None or not t.is_alive():  # travado no prazo: o modelo fica com a thread presa
                _whisper = None  # solta o modelo: a próxima solar carrega o dela
                gc.collect()
            try:
                trava.seek(0)
                msvcrt.locking(trava.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass


_REMOTO_PY = ("import json,sys\n"
              "from faster_whisper import WhisperModel\n"
              "m=WhisperModel('medium',device='cpu',compute_type='int8',cpu_threads=4,"
              "download_root=sys.argv[3])\n"
              "segs,_=m.transcribe(sys.argv[1],language='pt',word_timestamps=True,vad_filter=True,beam_size=5,"
              "condition_on_previous_text=False)\n"
              "json.dump([(w.word.strip(),round(w.start,2),round(w.end,2)) for s in segs for w in (s.words or [])],"
              "open(sys.argv[2],'w',encoding='utf-8'))\n")


def _transcrever_fora(v, prazo):
    """25/11 (PC1 com 4,6 GB num whisper medium do QA às 07:55 — regra: PC1 só supervisor): transcreve no STI (16 GB,
    faster_whisper no venv do chatterbox, modelo medium em ~/modelos/whisper). Manda só o vídeo, devolve as palavras.
    None = não deu (máquina ocupada/fora) -> quem chamou roda aqui como antes. QA_WHISPER_FORA=0 desliga."""
    import os
    import uuid
    if os.environ.get("QA_WHISPER_FORA", "1") == "0":
        return None
    host, py = "sti", "~/chatterbox/venv/bin/python"
    pasta = f"/tmp/qa_whisper_{uuid.uuid4().hex[:8]}"
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
    try:
        if subprocess.run(ssh + [f"mkdir -p {pasta}"], capture_output=True, timeout=30).returncode != 0:
            return None
        ext = Path(v).suffix or ".mp4"
        if subprocess.run(["scp", "-q", "-o", "BatchMode=yes", str(v), f"{host}:{pasta}/v{ext}"],
                          capture_output=True, timeout=300).returncode != 0:
            return None
        r = subprocess.run(ssh + [f"cd {pasta} && nice -n 10 {py} - {pasta}/v{ext} {pasta}/p.json ~/modelos/whisper "
                                  f"&& cat {pasta}/p.json"],
                           input=_REMOTO_PY, capture_output=True, text=True, timeout=max(60, prazo))
        if r.returncode != 0 or not r.stdout.strip().startswith("["):
            return None
        return [tuple(x) for x in json.loads(r.stdout)]
    except Exception:  # noqa: BLE001
        return None
    finally:
        try:
            subprocess.run(ssh + [f"rm -rf {pasta}"], capture_output=True, timeout=30)
        except Exception:  # noqa: BLE001
            pass


def _transcrever_processo(v, prazo):
    """Whisper num processo filho (mesmo Python), prioridade abaixo do normal e 2 threads. Passou do prazo = mata.
    25/11: tenta primeiro FORA do PC1 (_transcrever_fora)."""
    import os
    import sys
    import tempfile
    fora = _transcrever_fora(v, prazo)
    if fora is not None:
        return fora
    cod = ("import json,sys; sys.path.insert(0, sys.argv[3]); import qa_ms; "
           "json.dump(qa_ms._transcrever_agora(sys.argv[1]), open(sys.argv[2], 'w', encoding='utf-8'))")
    fd, saida = tempfile.mkstemp(suffix=".json", prefix="whisper_")
    os.close(fd)
    amb = dict(os.environ, QA_WHISPER_THREADS="2", PYTHONUTF8="1")
    flags = 0x00004000 | 0x08000000 if os.name == "nt" else 0  # BELOW_NORMAL + sem janela
    p = subprocess.Popen([sys.executable, "-c", cod, str(v), saida, str(Path(__file__).resolve().parent)],
                         env=amb, creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        _, err = p.communicate(timeout=prazo)
    except subprocess.TimeoutExpired:
        p.kill()
        try:
            p.communicate(timeout=10)
        except Exception:  # noqa: BLE001
            pass
        Path(saida).unlink(missing_ok=True)
        raise RuntimeError(f"whisper passou de {int(prazo)} s (processo encerrado, memória liberada)")
    try:
        if p.returncode != 0:
            raise RuntimeError(f"whisper falhou: {(err or b'').decode('utf-8', 'replace')[-200:]}")
        return [tuple(x) for x in json.loads(Path(saida).read_text("utf-8"))]
    finally:
        Path(saida).unlink(missing_ok=True)


def fala_confere(esperada, palavras):
    return round(SequenceMatcher(None, _norm(esperada), _norm(" ".join(p[0] for p in palavras))).ratio(), 2)


def _grade(imgs, rotulos):
    cw, ch = 240, 427
    g = Image.new("RGB", (cw * 3, (ch + 24) * 2), "white")
    fonte = ImageFont.load_default()
    for i, (im, rot) in enumerate(zip(imgs, rotulos)):
        x, y = (i % 3) * cw, (i // 3) * (ch + 24)
        if im is not None:
            g.paste(ImageOps.fit(im, (cw, ch)), (x, y + 24))
        ImageDraw.Draw(g).text((x + 4, y + 6), rot, fill="black", font=fonte)
    buf = io.BytesIO()
    g.save(buf, "JPEG", quality=85)
    return buf.getvalue()


def julgar(imgs, rotulos, tipo):
    """Juiz por visao (gateway, gemini-3-flash). Devolve dict ou None se o gateway falhar."""
    if tipo == "foto_real":
        contexto = ("O quadro FOTO e a foto original de uma instalacao; os outros sao quadros do video que deveria so "
                    "animar essa foto (movimento de camera e movimentos naturais).")
        extra = ' "pessoas_falando": true se alguma pessoa aparece falando ou mexendo a boca,\n'
    else:
        contexto = "Os quadros sao de um video de um(a) consultor(a) falando para a camera."
        extra = ' "pessoa_trocou": true se a pessoa muda de rosto/roupa/genero ao longo dos quadros,\n'
    pergunta = (f"Quadros de um video curto de propaganda de uma empresa de energia solar. {contexto} Responda SO JSON:\n"
                '{"mesma_cena": true se TODOS os quadros mostram o mesmo lugar e o mesmo plano continuo, false se em '
                'algum momento vira outra cena, outro lugar ou outra pessoa,\n'
                ' "texto_na_tela": true se aparecem letras, legendas, logotipos ou marcas d\'agua no video,\n'
                ' "deformacao": true se ha rosto, maos, corpo ou objetos derretendo, tortos ou fundidos, ou placas '
                'solares que surgem/somem/mudam de quantidade; mudanca de perspectiva so por movimento de camera NAO conta,\n'
                f'{extra}'
                ' "nota_profissional": 1 a 10 (parece propaganda seria e bem feita de uma empresa real?),\n'
                ' "problemas": ["..."]}')
    return visao_json(_grade(imgs, rotulos), pergunta)


def visao_json(jpeg, pergunta):
    """Pergunta ao modelo de visao do gateway (gemini-3-flash) sobre uma imagem JPEG; devolve o JSON da resposta ou
    {"_erro": ...}. Tambem usado pelo carrossel_ms (conferir ilustracao)."""
    erro = None
    # 18/11: AI Studio (gemini/gemini-3.5-flash) acertava 7% (403 sem free tier / 429 por minuto); 3-flash do
    # Antigravity acerta 99% e leu certo as fotos reais no teste. AI Studio fica de 2a tentativa.
    for modelo in ("antigravity/gemini-3-flash", "gemini/gemini-3.5-flash"):
        try:
            gw = json.loads(GATEWAY.read_text(encoding="utf-8"))
            corpo = {"model": modelo, "max_tokens": 500, "temperature": 0.1,
                     "messages": [{"role": "user", "content": [
                         {"type": "text", "text": pergunta},
                         {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,"
                                                             + base64.b64encode(jpeg).decode()}}]}]}
            url = gw.get("gateway_url", "http://157.173.207.22:20128").rstrip("/") + "/v1/chat/completions"
            req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers={
                "Authorization": "Bearer " + gw["gateway_key"], "Content-Type": "application/json"})
            txt = json.loads(urllib.request.urlopen(req, timeout=90).read())["choices"][0]["message"]["content"]
            return json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
        except Exception as e:  # noqa: BLE001
            erro = f"{type(e).__name__}: {str(e)[:100]}"
    return {"_erro": erro}


def checar_clipe(clip, roteiro, log=print):
    """Confere o clipe cru do Veo. {'ok', 'motivos', 'medidas', 'palavras'}."""
    motivos, med = [], {}
    dur, w, h, audio = probe(clip)
    med.update(dur=round(dur, 2), res=f"{w}x{h}", audio=audio)
    if not 6.5 <= dur <= 9.5:
        motivos.append(f"duracao {dur:.1f}s")
    if not audio:
        motivos.append("sem audio")
    if faixa_preta(clip, dur, w, h):
        motivos.append("faixa preta")
    tipo = roteiro["tipo"]
    if tipo == "foto_real":
        foto = Image.open(roteiro["quadro"]).convert("RGB")
        tempos = [0.0, 2.0, 4.0, 6.0, dur - 0.4]
        imgs = [quadro(clip, t) for t in tempos]
        sims = [parecido(foto, q) for q in imgs]
        med["parecido_foto"] = dict(zip([f"{t:.1f}" for t in tempos], sims))
        # numero so no inicio (0 e 2 s): camera andando derruba a correlacao depois mesmo na mesma cena (teste
        # 22/10); a "transformacao" dos videos antigos dava 0,01-0,27 aos 2 s. Do meio para o fim vale o juiz.
        if sims[0] is None or sims[0] < 0.80:
            motivos.append(f"nao comecou na foto (parecido {sims[0]})")
        elif sims[1] is None or sims[1] < 0.40:
            motivos.append(f"saiu da foto logo no inicio (parecido aos 2 s: {sims[1]})")
        imgs, rotulos = [foto] + imgs, ["FOTO"] + [f"{t:.1f}s" for t in tempos]
    else:
        tempos = [0.0, 1.5, 3.0, 4.5, 6.0, dur - 0.4]
        imgs, rotulos = [quadro(clip, t) for t in tempos], [f"{t:.1f}s" for t in tempos]
    if roteiro.get("clone_bases"):  # 25/10: clone da empresa — o rosto do vídeo tem que ser o das fotos_base
        try:
            import sys
            if r"D:\veo\beta" not in sys.path:
                sys.path.append(r"D:\veo\beta")
            import foto_na_hora
            foto_na_hora.usar_bases(roteiro["clone_bases"])
            ok_r, notas_r, motivo_r = foto_na_hora.revisar_video(str(clip))
            med["rosto_clone"] = notas_r
            if not ok_r:
                motivos.append(f"clone: {motivo_r}")
        except Exception as e:  # noqa: BLE001
            log(f"  [QA] revisor de rosto do clone falhou ({type(e).__name__}) — segue sem ele")
    # 2 votos: o juiz deu nota 8 e depois 3 ao MESMO clipe (22/10). Cena/deformacao/pessoa so reprovam se os 2
    # votos concordam; nota = media; texto na tela reprova com 1 voto (esse ele ve de forma estavel).
    # 03/11: 2 rodadas morreram aos 150 min logo após o clipe sair, sem uma linha no log — cada passo agora avisa
    import time as _t
    _t0 = _t.time()
    log("  [QA] juiz de visão (2 votos)...")
    votos = [v for v in (julgar(imgs, rotulos, tipo), julgar(imgs, rotulos, tipo)) if v and "_erro" not in v]
    log(f"  [QA] juiz ok ({_t.time() - _t0:.0f} s) — whisper...")
    med["visao"] = votos
    if votos:
        def todos(chave, valor=True):
            return all(v.get(chave) is valor for v in votos)
        if todos("mesma_cena", False):
            motivos.append("visao: virou outra cena")
        if any(v.get("texto_na_tela") for v in votos):
            motivos.append("visao: texto/logo na tela")
        if todos("deformacao"):
            motivos.append("visao: deformacao")
        if todos("pessoas_falando"):
            motivos.append("visao: pessoa da foto falando")
        if todos("pessoa_trocou"):
            motivos.append("visao: pessoa trocou")
        nota = sum(int(v.get("nota_profissional") or 10) for v in votos) / len(votos)
        med["nota_media"] = nota
        if nota < 5:
            motivos.append(f"visao: nota {nota:.1f}")
    else:
        log("  [QA] visao indisponivel — seguindo so com as medidas")
    palavras = []
    if not audio:  # 03/11: clipe sem áudio já está reprovado — o whisper no PC1 lotado gastava 10+ min à toa
        ok = False
        log(f"  [QA] clipe REPROVADO: {'; '.join(motivos)} (sem áudio: pulo o whisper) | "
            f"{json.dumps(med, ensure_ascii=False)[:300]}")
        return {"ok": ok, "motivos": motivos, "medidas": med, "palavras": palavras}
    try:
        _t0 = _t.time()
        palavras = transcrever(clip)
        log(f"  [QA] whisper ok ({_t.time() - _t0:.0f} s)")
        med["fala_ouvida"] = " ".join(p[0] for p in palavras)
        med["fala_confere"] = fala_confere(roteiro["fala_final"], palavras)
        if not palavras:
            motivos.append("sem fala")
        elif med["fala_confere"] < 0.5:
            motivos.append(f"fala diferente do roteiro ({med['fala_confere']})")
    except Exception as e:  # noqa: BLE001
        log(f"  [QA] whisper falhou ({type(e).__name__}: {str(e)[:80]}) — sem conferir a fala")
    ok = not motivos
    log(f"  [QA] clipe {'APROVADO' if ok else 'REPROVADO: ' + '; '.join(motivos)} | {json.dumps(med, ensure_ascii=False)[:400]}")
    return {"ok": ok, "motivos": motivos, "medidas": med, "palavras": palavras}


def checar_final(mp4, log=print):
    """Confere o short montado: duracao com cartao, audio, resolucao da montagem e cartao no fim (nao preto)."""
    from montagem_ms import H as ALTURA, W as LARGURA
    motivos = []
    dur, w, h, audio = probe(mp4)
    if dur < 10.0:
        motivos.append(f"curto demais ({dur:.1f}s): cartao faltando")
    if not audio:
        motivos.append("sem audio")
    if (w, h) != (LARGURA, ALTURA):
        motivos.append(f"resolucao {w}x{h}")
    fim = quadro(mp4, dur - 0.5)
    if fim is None or np.asarray(fim.convert("L")).mean() < 15:
        motivos.append("fim preto (cartao nao apareceu)")
    ok = not motivos
    log(f"  [QA] final {'APROVADO' if ok else 'REPROVADO: ' + '; '.join(motivos)} ({dur:.1f}s {w}x{h})")
    return {"ok": ok, "motivos": motivos, "dur": round(dur, 2)}
