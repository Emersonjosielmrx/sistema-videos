"""Protótipo (pedido do dono 20/10): a MESMA voz clonada muda o jeito conforme o clima do trecho — engraçado, tensão,
terror, vilão, luta acelerando como gol, épico, triste — como narrador humano. Não mexe na produção.

Roda com D:\\hipercool-materiais\\python\\venv_vozes\\Scripts\\python.exe (edge-tts 7.3.1, Kokoro, Applio).
Saída em teste_vozes_base\\variacoes\\:
  1_<voz>_HOJE.mp3         a história como a produção faz hoje (misto Kokoro/Francisca + curva de gol do narracao_curva)
  2_<voz>_COM_CLIMAS.mp3   a mesma história com a voz mudando por clima
  vilao_ab\\                a fala do vilão em bases diferentes, mesmo tom (o efeito vem da base ou do tom?)
  trechos\\                 cada frase solta, com o clima no nome
Retomável: base e trecho já feitos são pulados.
"""
import asyncio
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

RAIZ = Path(r"D:\hipercool-materiais")
OUT = RAIZ / "teste_vozes_base" / "variacoes"
BASES = OUT / "_bases"
TRECHOS = OUT / "trechos"
AB = OUT / "vilao_ab"
PY = RAIZ / "python" / "venv_vozes" / "Scripts" / "python.exe"
VC = RAIZ / "bin" / "voz_clonada.py"
FF = str(RAIZ / "bin" / "ffmpeg.exe")
VOZES = RAIZ / "models" / "rvc" / "vozes"
SEM_JANELA = 0x08000000 | 0x00004000
os.environ["PATH"] = str(RAIZ / "bin") + os.pathsep + os.environ.get("PATH", "")
sys.path.insert(0, str(RAIZ / "comum"))
import narracao_curva  # noqa: E402  as mesmas funções da produção (deltas, variacao, pos_processar)

# tom mediano medido com RMVPE (20/10, mesmo texto): o clone é calibrado nisso, não no nome da voz
BASE_HZ = {"francisca": 234.0, "antonio": 132.0, "andrew": 110.3, "kokoro": 130.6}
EDGE = {"francisca": "pt-BR-FranciscaNeural", "antonio": "pt-BR-AntonioNeural",
        "andrew": "en-US-AndrewMultilingualNeural"}
KOKORO_VOZ = "pm_santa"   # entonação mais larga que a pm_alex (12 × 8,5 st)
NATURAL_HZ = {"mike": 120.8, "momo": 209.9}   # RMVPE no voz.wav do dataset
PISO_MULHER_HZ = 165      # abaixo disso voz de mulher vira voz de homem (o que não combinou no teste)

# rate: % somado ao do narrador | st: semitons em relação à voz natural (homem, mulher) | f0: multiplica a faixa de
# entonação do narrador | final: fim de frase em st (None = o do narrador) | db: volume | pausa: s depois da frase |
# formante: <1 voz "maior"/escura, >1 clara/sorrindo | eq: [[Hz, dB]] somado ao do narrador | eco: None/leve/sala
CLIMAS = {
    "normal":    dict(base="francisca", rate=0, st=(0, 0), f0=1.00, final=None, db=0.0, pausa=0.30, formante=1.00,
                      eq=[], eco=None, ir=0.45, pr=0.33, ve=0.75, respira=False),
    "engracado": dict(base="francisca", rate=8, st=(0, 0), f0=1.25, final=None, db=1.0, pausa=0.20, formante=1.04,
                      eq=[[3000, 2.0]], eco=None, ir=0.50, pr=0.30, ve=0.80, respira=False),
    "tensao":    dict(base="francisca", rate=-8, st=(-1, -1), f0=0.80, final=-0.5, db=-2.0, pausa=0.50,
                      formante=0.98, eq=[[6000, -2.0]], eco=None, ir=0.42, pr=0.38, ve=0.70, respira=True),
    "terror":    dict(base="francisca", rate=-16, st=(-2, -2), f0=0.65, final=-1.0, db=-4.0, pausa=0.80,
                      formante=0.96, eq=[[180, 1.5], [5000, -3.0], [10000, -5.0]], eco="leve", ir=0.40, pr=0.45,
                      ve=0.60, respira=True),
    "vilao":     dict(base="francisca", rate=-12, st=(-8, -3), f0=0.75, final=-1.2, db=1.0, pausa=0.60,
                      formante=0.92, eq=[[140, 2.5], [3000, -1.0]], eco=None, ir=0.50, pr=0.33, ve=0.75,
                      respira=False),
    # luta: Kokoro, cada pedaço (vírgula) mais rápido e mais alto que o anterior; o último (o "gol") +1 st
    "acao":      dict(base="kokoro", vel=(1.00, 1.35), st=(0, 0), f0=1.15, final=None, db=(0.0, 4.0), pausa=0.06,
                      formante=1.00, eq=[[2500, 1.5]], eco=None, ir=0.60, pr=0.25, ve=0.85, respira=False),
    "epico":     dict(base="francisca", rate=-6, st=(-1, -1), f0=1.10, final=-0.5, db=2.0, pausa=0.70,
                      formante=0.97, eq=[[120, 1.5]], eco="sala", ir=0.50, pr=0.33, ve=0.80, respira=False),
    "triste":    dict(base="francisca", rate=-10, st=(-1, -1), f0=0.85, final=-1.5, db=-3.0, pausa=0.65,
                      formante=1.00, eq=[[8000, -2.0]], eco=None, ir=0.42, pr=0.38, ve=0.70, respira=True),
}
ECO = {"leve": "aecho=0.8:0.6:35|60:0.15|0.10", "sala": "aecho=0.8:0.7:60|110:0.18|0.12"}

HISTORIA = [
    ("normal", "Kael era o mais fraco da academia inteira."),
    ("normal", "Todo santo dia, a mesma humilhação na frente de todo mundo."),
    ("engracado", "E pra piorar, o poder que ele despertou foi fazer pão."),
    ("engracado", "Isso mesmo, pão. Enquanto os outros soltavam fogo, o nosso garoto soltava baguete quentinha."),
    ("tensao", "Mas naquela noite, um silêncio estranho tomou conta do dormitório."),
    ("tensao", "As luzes do corredor começaram a apagar, uma por uma."),
    ("terror", "Alguma coisa estava respirando do outro lado da porta."),
    ("terror", "Devagar... bem devagar."),
    ("terror", "Até que uma voz atravessou a madeira."),
    ("vilao", "Eu vim buscar o que é meu. E ninguém vai sair daqui vivo."),
    ("acao", "Kael pulou da cama, desviou do primeiro golpe, do segundo, do terceiro,"),
    ("acao", "girou o corpo, agarrou a espada de madeira e acertou bem no meio do peito do monstro!"),
    ("epico", "Naquele instante, uma janela azul surgiu diante dos olhos dele."),
    ("epico", "Sistema despertado. Rank S."),
    ("triste", "Mas quando a poeira baixou, o único amigo que ele tinha estava caído no chão."),
    ("normal", "E foi exatamente ali que tudo começou a mudar."),
]
VILAO_AB = {"mike": [("A_francisca", "francisca", -8), ("B_antonio", "antonio", -8), ("C_andrew", "andrew", -8),
                     ("D_andrew_igual_ao_teste", "andrew", -13)],
            "momo": [("A_francisca", "francisca", -3), ("B_antonio", "antonio", -3)]}
NARRADORES = ["mike", "momo"]
SO_CLIMAS = {"momo"}  # momo: só a versão com climas (a de hoje dá pra comparar pela do mike)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def edge(texto, voz, rate, wav):
    import edge_tts
    mp3 = wav.with_suffix(".mp3")
    for tent in range(4):
        try:
            asyncio.run(edge_tts.Communicate(texto, voz, rate=f"{int(round(rate)):+d}%").save(str(mp3)))
            break
        except Exception as e:  # noqa: BLE001
            log(f"  edge {voz} falhou ({type(e).__name__}: {str(e)[:80]}) — tentativa {tent + 1}/4")
            time.sleep(6 * (tent + 1))
    else:
        raise RuntimeError(f"edge {voz} falhou 4x: {texto[:50]}")
    subprocess.run([FF, "-v", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", str(wav)], check=True,
                   creationflags=SEM_JANELA)
    mp3.unlink()
    time.sleep(0.7)


_K = []


def kokoro(texto, vel, wav):
    if not _K:
        from kokoro_onnx import Kokoro
        _K.append(Kokoro(str(RAIZ / "models" / "kokoro" / "kokoro-v1.0.onnx"),
                         str(RAIZ / "models" / "kokoro" / "voices-v1.0.bin")))
    a, sr = _K[0].create(texto, voice=KOKORO_VOZ, speed=float(vel), lang="pt-br")
    sf.write(str(wav), a, sr)


def base_wav(nome, base, texto, rate=0.0, vel=1.0):
    wav = BASES / f"{nome}.wav"
    if not (wav.exists() and wav.stat().st_size > 1000):
        if base == "kokoro":
            kokoro(texto, vel, wav)
        else:
            edge(texto, EDGE[base], rate, wav)
    return wav


def natural(voz):
    return NATURAL_HZ.get(voz) or float((VOZES / voz / "f0.txt").read_text().strip())


def semitons(voz, base, st):
    """Semitons do clone pra base cair em (voz natural + st); mulher nunca desce pra faixa de homem."""
    nat = natural(voz)
    alvo = nat * 2 ** (st / 12)
    if nat >= PISO_MULHER_HZ:
        alvo = max(alvo, PISO_MULHER_HZ)
    return round(12 * math.log2(alvo / BASE_HZ[base]))


def juntar_eq(*listas):
    d = {}
    for lst in listas:
        for f, g in lst or []:
            d[float(f)] = round(d.get(float(f), 0.0) + float(g), 2)
    return [[f, g] for f, g in sorted(d.items())]


def item(voz, perfil, tom_fixo, nome, base, texto, st, c, rate=0.0, vel=1.0, st_extra=0):
    pb = perfil["kokoro" if base == "kokoro" else "francisca"]
    entrada = base_wav(f"{voz}_{nome}", base, texto, rate, vel)
    final = c["final"] if c["final"] is not None else pb.get("final_st", 0)
    return {"saida": str(TRECHOS / f"{voz}_{nome}.wav"), "tom_base": "2_edge_francisca", "entrada": str(entrada),
            "tom_extra": semitons(voz, base, st) + st_extra - tom_fixo,
            "f0_escala": round(pb["f0_escala"] * c["f0"], 3), "final_st": round(final, 2),
            "eq": juntar_eq(pb.get("eq"), c["eq"]), "index_rate": c["ir"], "protect": c["pr"],
            "volume_envelope": c["ve"]}


def versao_climas(voz, perfil, tom_fixo):
    """[(item_lote, pós)]: pós = como tratar o trecho depois do clone (volume, formante, eco, pausa, respiração)."""
    mulher = natural(voz) >= PISO_MULHER_HZ
    rate_narr = perfil["francisca"]["rate"]
    vel_narr = perfil["kokoro"]["velocidade"]
    pedacos = []
    for i, (clima, texto) in enumerate(HISTORIA):
        c = CLIMAS[clima]
        st = c["st"][1 if mulher else 0]
        ant = HISTORIA[i - 1][0] if i else None
        prox = HISTORIA[i + 1][0] if i + 1 < len(HISTORIA) else None
        respira = c["respira"] and ant != clima
        if clima == "acao":
            partes = [p.strip() for p in texto.replace(",", ",|").split("|") if p.strip()]
            pedacos.append((i, clima, c, st, partes, respira, prox))
        else:
            pedacos.append((i, clima, c, st, [texto], respira, prox))
    # a luta acelera de pedaço em pedaço ao longo do trecho todo (os dois "acao" seguidos = uma subida só)
    n_acao = sum(len(p[4]) for p in pedacos if p[1] == "acao")
    k_acao = 0
    itens = []
    for i, clima, c, st, partes, respira, prox in pedacos:
        for j, parte in enumerate(partes):
            nome = f"climas_{i:02d}_{j}_{clima}"
            pos = {"db": c["db"], "formante": c["formante"], "eco": c["eco"], "pausa": c["pausa"],
                   "respira": respira and j == 0}
            if clima == "acao":
                f = k_acao / max(1, n_acao - 1)
                f = f * f  # devagar no começo, dispara no fim (locutor de futebol)
                vel = vel_narr * (c["vel"][0] + (c["vel"][1] - c["vel"][0]) * f)
                gol = k_acao == n_acao - 1
                it = item(voz, perfil, tom_fixo, nome, "kokoro", parte, st, c, vel=round(vel, 3),
                          st_extra=1 if gol else 0)
                pos["db"] = c["db"][0] + (c["db"][1] - c["db"][0]) * f
                if gol:  # o "gol": pausa grande e respiro antes do próximo trecho
                    pos["pausa"], pos["respira_depois"] = 0.85, True
                k_acao += 1
            else:
                it = item(voz, perfil, tom_fixo, nome, c["base"], parte, st, c, rate=rate_narr + c["rate"])
                if clima == "engracado" and prox == "engracado":
                    pos["pausa"] = 0.55  # tempo de piada: segura antes da frase que fecha
            itens.append((it, pos))
    return itens


def versao_hoje(voz, perfil, tom_fixo):
    """Como a produção faz hoje (anime_tts.preparar_clone + _frase_v2, VOZ_CLONADA_BASE=misto, v2)."""
    linhas = [t for _c, t in HISTORIA]
    n = len(linhas)
    impactos = narracao_curva._heuristica(linhas, narracao_curva._quantos(n))
    chave = str(OUT / f"_hoje_{voz}")
    itens = []
    for i, texto in enumerate(linhas):
        dr, dp, dg, _cauda = narracao_curva.deltas(texto, i, impactos, n)
        base = "kokoro" if i == 0 or dr >= 8 else "francisca"
        dr2 = dr * perfil["curva_rate"]
        ruido = (int(hashlib.md5(texto.encode("utf-8")).hexdigest(), 16) % 5 - 2) / 4
        tom_extra = int(round(max(-2.0, min(2.0, (dr / narracao_curva.PICO_RATE + ruido) * perfil["tom_extra_st"]))))
        v = narracao_curva.variacao(chave, i, texto, impactos, n)
        pb = perfil[base]
        nome = f"hoje_{i:02d}_{base}"
        if base == "kokoro":
            vel = max(0.75, min(1.6, pb["velocidade"] * (1 + dr2 / 100)))
            entrada = base_wav(f"{voz}_{nome}", "kokoro", texto, vel=round(vel, 2))
        else:
            rate = int(round(max(-40, min(70, pb["rate"] + dr2))))
            entrada = base_wav(f"{voz}_{nome}", "francisca", texto, rate=rate)
        it = {"saida": str(TRECHOS / f"{voz}_{nome}.wav"), "tom_base": "2_edge_francisca", "entrada": str(entrada),
              "tom_extra": semitons(voz, base, 0) + tom_extra - tom_fixo, "f0_escala": pb["f0_escala"],
              "final_st": round(pb.get("final_st", 0) * v["final_mult"], 2), "eq": pb["eq"],
              "index_rate": v["index_rate"], "protect": v["protect"], "volume_envelope": v["volume_envelope"]}
        cauda = perfil["cauda_impacto"] if i in impactos else perfil["cauda"]
        itens.append((it, {"db": dg * perfil["curva_ganho"], "formante": 1.0, "eco": None,
                           "pausa": cauda + v["pausa_s"], "respira": False}))
    log(f"  hoje: impactos {impactos} (heurística da produção)")
    return itens


def versao_vilao(voz, perfil, tom_fixo):
    c = CLIMAS["vilao"]
    texto = dict((cl, t) for cl, t in HISTORIA)["vilao"]
    itens = []
    for rotulo, base, st in VILAO_AB[voz]:
        rate = perfil["francisca"]["rate"] + c["rate"] if base == "francisca" else -5  # Antonio/Andrew já são lentos
        it = item(voz, perfil, tom_fixo, f"vilao_{rotulo}_{st:+d}st", base, texto, st, c, rate=rate)
        itens.append((it, {"db": c["db"], "formante": c["formante"], "eco": None, "pausa": 0.0, "respira": False,
                           "ab": f"{voz}_{rotulo}_{st:+d}st"}))
    return itens


def esperar_ram(min_gb=2.5, max_min=30):
    import psutil
    t0 = time.time()
    while psutil.virtual_memory().available / 1024 ** 3 < min_gb and time.time() - t0 < max_min * 60:
        log(f"  RAM livre {psutil.virtual_memory().available / 1024 ** 3:.1f} GB < {min_gb} — esperando")
        time.sleep(30)


def clonar(voz, itens):
    falta = [it for it, _p in itens if not (Path(it["saida"]).exists() and Path(it["saida"]).stat().st_size > 1000)]
    if not falta:
        return
    lista = OUT / f"_lista_{voz}.json"
    lista.write_text(json.dumps(falta, ensure_ascii=False, indent=1), encoding="utf-8")
    esperar_ram()
    log(f"  clonando {len(falta)} trechos com a voz de {voz} (Applio carrega 1x)")
    t0 = time.time()
    with open(OUT / f"_clone_{voz}.log", "a", encoding="utf-8") as fh:
        r = subprocess.run([str(PY), str(VC), "lote", voz, str(lista)], stdout=fh, stderr=subprocess.STDOUT,
                           timeout=3 * 3600, creationflags=SEM_JANELA)
    faltam = [it["saida"] for it in falta if not Path(it["saida"]).exists()]
    if r.returncode or faltam:
        raise RuntimeError(f"lote {voz} rc={r.returncode}, faltam {len(faltam)} (ver _clone_{voz}.log)")
    log(f"  clone ok em {time.time() - t0:.0f} s")


def tratar(it, pos):
    """Trecho clonado -> formante, nível (-20 LUFS + db, igual à produção), eco. Devolve (áudio 44,1k estéreo)."""
    src = Path(it["saida"])
    pronto = src.with_name(src.stem + ".pronto.wav")
    if not pronto.exists():
        y, sr = sf.read(str(src), dtype="float64")
        if y.ndim > 1:
            y = y.mean(axis=1)
        if pos["formante"] != 1.0:
            sys.path.insert(0, str(RAIZ / "tools" / "applio"))
            from rvc.lib.tools.formant import FormantShifter
            y = FormantShifter(sr).process_file(y, quefrency=1.0, timbre=pos["formante"])
        sf.write(str(pronto), y, sr)
        narracao_curva.pos_processar(pronto, ganho_db=pos["db"], cauda_s=0.05)
        if pos.get("eco"):
            tmp = pronto.with_name(pronto.stem + ".eco.wav")
            subprocess.run([FF, "-v", "error", "-y", "-i", str(pronto), "-af", ECO[pos["eco"]], str(tmp)], check=True,
                           creationflags=SEM_JANELA)
            tmp.replace(pronto)
        if sf.info(str(pronto)).samplerate != 44100:  # pos_processar falhou e deixou como veio
            tmp = pronto.with_name(pronto.stem + ".44k.wav")
            subprocess.run([FF, "-v", "error", "-y", "-i", str(pronto), "-ar", "44100", "-ac", "2", str(tmp)],
                           check=True, creationflags=SEM_JANELA)
            tmp.replace(pronto)
    y, sr = sf.read(str(pronto), dtype="float32", always_2d=True)
    if y.shape[1] == 1:
        y = np.repeat(y, 2, axis=1)
    acima = np.flatnonzero(np.abs(y).max(axis=1) > 10 ** (-45 / 20))
    if acima.size:  # silêncio do começo (Kokoro/edge) fora: a pausa é só a do clima
        y = y[max(0, acima[0] - int(0.03 * sr)):]
    return y, sr


def respiracao(voz, seed):
    reais = sorted((VOZES / voz / "humano").glob("respiracao_*.wav"))
    if reais:
        y, sr = sf.read(str(reais[seed % len(reais)]), dtype="float32", always_2d=True)
        if sr == 44100:
            return np.repeat(y[:, :1], 2, axis=1) * 0.7
    rng = np.random.default_rng(seed)
    n = int(0.26 * 44100)
    ruido = rng.standard_normal(n)
    esp = np.fft.rfft(ruido)
    fr = np.fft.rfftfreq(n, 1 / 44100)
    esp[(fr < 300) | (fr > 2500)] = 0
    y = np.fft.irfft(esp, n) * np.hanning(n)
    y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * 10 ** (-36 / 20)
    return np.repeat(y[:, None].astype("float32"), 2, axis=1)


def montar(voz, itens, destino):
    partes = []
    for k, (it, pos) in enumerate(itens):
        y, sr = tratar(it, pos)
        if pos.get("respira"):
            partes.append(respiracao(voz, k))
            partes.append(np.zeros((int(0.08 * sr), 2), "float32"))
        fade = min(len(y) // 4, int(0.01 * sr))
        if fade > 0:
            y[:fade] *= np.linspace(0, 1, fade)[:, None]
            y[-fade:] *= np.linspace(1, 0, fade)[:, None]
        partes.append(y)
        partes.append(np.zeros((int(pos["pausa"] * sr), 2), "float32"))
        if pos.get("respira_depois"):
            partes.append(respiracao(voz, k + 7))
            partes.append(np.zeros((int(0.15 * sr), 2), "float32"))
    wav = destino.with_suffix(".wav")
    sf.write(str(wav), np.concatenate(partes), 44100)
    subprocess.run([FF, "-v", "error", "-y", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "44100", "-codec:a", "libmp3lame", "-b:a", "192k", str(destino)], check=True,
                   creationflags=SEM_JANELA)
    wav.unlink()
    log(f"  pronto: {destino.name}")


def main():
    for p in (BASES, TRECHOS, AB):
        p.mkdir(parents=True, exist_ok=True)
    import psutil
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    todos = sys.argv[1:]  # narradores pedidos = só a história com climas de cada um em variacoes\narradores\
    for voz in todos or NARRADORES:
        log(f"=== {voz} (natural {natural(voz)} Hz) ===")
        perfil = json.loads((VOZES / voz / "perfil_v2.json").read_text(encoding="utf-8"))["aplicar"]
        tom_fixo = int((VOZES / voz / "tom_2_edge_francisca.txt").read_text().strip())
        climas = versao_climas(voz, perfil, tom_fixo)
        if todos:
            try:
                clonar(voz, climas)
                (OUT / "narradores").mkdir(exist_ok=True)
                montar(voz, climas, OUT / "narradores" / f"{voz}_climas.mp3")
            except Exception as e:  # noqa: BLE001
                log(f"  {voz} FALHOU: {e}")
            continue
        hoje = [] if voz in SO_CLIMAS else versao_hoje(voz, perfil, tom_fixo)
        vilao = versao_vilao(voz, perfil, tom_fixo)
        log(f"  bases prontas ({len(climas) + len(hoje) + len(vilao)} trechos)")
        clonar(voz, climas + hoje + vilao)
        n = 1 if voz == "mike" else 3
        if hoje:
            montar(voz, hoje, OUT / f"{n}_{voz}_HOJE.mp3")
        montar(voz, climas, OUT / f"{n + 1 if hoje else n}_{voz}_COM_CLIMAS.mp3")
        for it, pos in vilao:
            y, _sr = tratar(it, pos)
            wav = AB / f"{pos['ab']}.wav"
            sf.write(str(wav), y, 44100)
            subprocess.run([FF, "-v", "error", "-y", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                            "-codec:a", "libmp3lame", "-b:a", "192k", str(wav.with_suffix(".mp3"))], check=True,
                           creationflags=SEM_JANELA)
            wav.unlink()
        log(f"  vilão A/B: {', '.join(p['ab'] for _i, p in vilao)}")
    log("TUDO PRONTO")


if __name__ == "__main__":
    main()
