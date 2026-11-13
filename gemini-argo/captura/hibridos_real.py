"""Banco REAL das duplas Argon + reserva: reparos e melhorias tirados do nosso código de vídeo.
A nota vem de testes escondidos montados a partir da solução de referência (a do Claude Opus 5.5, feita à parte);
a mesma máquina de rodar do hibridos_bench (pasta nova por rodada, Claude Code CLI pelo proxy da VPS).
    python hibridos_real.py [filtro]       placar em hibridos_real_placar.json
    python hibridos_real.py --ref          confere os testes contra a solução de referência e contra o código com bug"""
import shutil
import sys
from pathlib import Path

import hibridos_bench as hb

# ------------------------------------------------ R1: fila do hipercool (bug real de 22/10)
FILA = {
    "fila.py": '''"""Decide se a fila do hipercool pode subir um vídeo agora no canal de uma língua (trecho de bin/fila.py)."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

POSTAGEM_IDIOMAS = {"intervalo_h": 2, "max_dia": 3, "parado_h": 24}


def pode_postar(info, ups, agora_la=None, teto=None):
    """(pode, motivo) pra subir agora no canal da língua. Canal sem nada há mais de parado_h: sai já.
    Senão só no horário de pico do país (hora de lá), intervalo_h depois do último e até max_dia por dia.
    ups = horários de publicação (com fuso) de tudo que subiu ou está agendado no canal, em ordem.
    teto = teto real do canal no postador (quando vem, vale no lugar do max_dia)."""
    p = {**POSTAGEM_IDIOMAS, **{c: info[c] for c in ("intervalo_h", "max_dia", "parado_h") if c in info}}
    if teto is not None:
        p["max_dia"] = int(teto)
    agora_la = agora_la or datetime.now(ZoneInfo(info.get("fuso", "UTC")))
    ups = sorted(ups)
    if not ups or agora_la - ups[-1] > timedelta(hours=p["parado_h"]):
        return True, "canal parado, sai já"
    if agora_la - ups[-1] < timedelta(hours=p["intervalo_h"]):
        return False, f"último há {(agora_la - ups[-1]).total_seconds() / 3600:.1f} h"
    hoje = sum(1 for u in ups if u.astimezone(agora_la.tzinfo).date() == agora_la.date())
    if hoje >= p["max_dia"]:
        return False, f"já subiram {hoje} hoje"
    ini, fim = info.get("pico", [17, 22])
    if not ini <= agora_la.hour < fim:
        return False, f"fora do pico ({agora_la:%H:%M} lá, pico {ini}h-{fim}h)"
    return True, f"pico ({agora_la:%H:%M} lá)"
''',
    "fila_postagem.log": """2026-10-18 19:02 [en] Tower of God cap 41: último há 3.1 h -> sobe
2026-10-18 21:40 [en] não sobe: último há -142.3 h
2026-10-19 18:05 [es] não sobe: último há -118.9 h
2026-10-19 18:05 [hi] não sobe: último há -97.0 h
2026-10-20 19:10 [en] não sobe: último há -144.0 h
2026-10-21 18:30 [fr] não sobe: último há -71.5 h
2026-10-22 08:12 [id] não sobe: último há -60.2 h
""",
    "LEIA.txt": "Os horários vêm do ledger do postador, que tem tanto o que já foi publicado quanto o que está agendado "
                "(publish_at no futuro, ex.: Shorts do parceiro agendados no mesmo canal).\n",
}
FILA_PREP = '''from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fila import pode_postar
TZ = ZoneInfo("America/New_York")
AG = datetime(2026, 10, 20, 19, 0, tzinfo=TZ)
def h(horas): return AG + timedelta(hours=horas)
INFO = {"fuso": "America/New_York", "pico": [17, 22]}
def ok(ups, agora=AG, info=INFO, teto=None): return pode_postar(info, ups, agora, teto)[0]
'''
FILA_OCULTO = [
    "ok([h(-5), h(24 * 6)]) is True",                        # o bug: agendado daqui a 6 dias travava o canal
    "ok([h(24 * 3)]) is True",                               # só agendado no futuro = canal parado
    "ok([h(-30), h(48)]) is True",                           # último publicado há 30 h = parado
    "ok([h(-1), h(72)]) is False",                           # publicado há 1 h: intervalo
    "ok([h(-1)]) is False",
    "ok([h(-3)]) is True",
    "ok([h(-6), h(-3), h(2)], teto=3) is False",             # teto do dia conta o agendado de hoje (21h)
    "ok([h(-6), h(-3), h(2)], teto=4) is True",
    "ok([h(-3)], agora=h(-6)) is True",                      # às 13h o h(-3) (16h) ainda é agendado: canal parado
    "ok([h(-10)], agora=h(-6)) is False",                    # 13h, último há 4 h: fora do pico
    "'-' not in pode_postar(INFO, [h(-1), h(100)], AG)[1]",  # motivo nunca com hora negativa
]
FILA_PEDIDO = ("fica o trecho da fila do hipercool (fila.py) que decide se sobe vídeo no canal de cada língua. "
               "As 6 línguas pararam de postar de 18 a 22/10 e o fila_postagem.log só diz 'não sobe: último há -144 h'. "
               "Descubra a causa e conserte em fila.py, sem quebrar o resto das regras (canal parado sai já, intervalo "
               "entre uploads, teto do dia contando também o que está agendado pra hoje, horário de pico do país). "
               "Teste com casos seus antes de terminar.")

# ------------------------------------------------ R2: youtube_http._numero (bug real de 27/10)
YT = {
    "youtube_http.py": '''"""Métricas públicas do YouTube sem navegador (trecho)."""
import re


def _numero(txt):
    """'1,2 mil visualizações' / '3,4 mi de inscritos' / '12.345 visualizações' / '2.3M views' -> int."""
    if not txt:
        return None
    t = txt.lower().replace("\\xa0", " ")
    m = re.search(r"([\\d.,]+)\\s*(mil|mi|bi|k|m|b)?", t)
    if not m:
        return 0 if re.search(r"\\b(nenhum|sem)", t) else None
    num, mult = m.group(1), m.group(2)
    if mult:
        return int(float(num.replace(".", "").replace(",", ".")) * {"mil": 1000, "k": 1000, "mi": 10**6, "m": 10**6,
                                                                   "bi": 10**9, "b": 10**9}[mult])
    return int(re.sub(r"[.,]", "", num))


def resumo_canal(textos):
    """{'inscritos': '3,4 mi de inscritos', 'videos': '812 vídeos', 'views': '...'} -> números"""
    return {k: _numero(v) for k, v in textos.items()}
''',
}
YT_PREP = "from youtube_http import _numero as n, resumo_canal\n"
YT_OCULTO = [
    "n('3,4 mi de inscritos') == 3400000",
    "n('4,1 mi de inscritos') == 4100000",
    "n('2.3M views') == 2300000",
    "n('1.5K views') == 1500",
    "n('1,2 mil visualizações') == 1200",
    "n('10 mil visualizações') == 10000",
    "n('12.345 visualizações') == 12345",
    "n('1.234.567 views') == 1234567",
    "n('812 vídeos') == 812",
    "n('1,2 bi de visualizações') == 1200000000",
    "n('Nenhuma visualização') == 0",
    "n('Sem visualizações') == 0",
    "n('') is None",
    "n('2 meses atrás') == 2",
    "resumo_canal({'inscritos': '3,4 mi de inscritos', 'videos': '812 vídeos'}) == {'inscritos': 3400000, 'videos': 812}",
]
YT_PEDIDO = ("fica o youtube_http.py que lê os números do YouTube sem navegador. No painel o canal aparece com "
             "3.399.999 inscritos, mas no YouTube está '3,4 mi de inscritos'; e um vídeo com '2.3M views' apareceu "
             "como 23 milhões. Ache as causas e conserte o _numero (os outros formatos que ele já entende têm que "
             "continuar funcionando). Teste com casos seus antes de terminar.")

# ------------------------------------------------ R3: microcortes dos Shorts (melhoria real de 22/10)
MC = {
    "narracao.py": '''"""Pós-processamento da narração dos Shorts (trecho de comum/narracao_curva.py)."""
import json
import os
from pathlib import Path

LIMIAR_SILENCIO_DB = -40.0   # quadro de 10 ms abaixo disso (dBFS) é silêncio
GAP_MICROCORTE = 0.07        # segundos de silêncio que ficam entre as falas


def ler_palavras(wav):
    """Lista de {"word", "start", "end"} (segundos) do <wav>.words.json, ou [] se não tem."""
    p = Path(str(wav) + ".words.json")
    return json.loads(p.read_text("utf-8")) if p.exists() else []


def gravar_palavras(wav, palavras):
    Path(str(wav) + ".words.json").write_text(json.dumps(palavras, ensure_ascii=False), "utf-8")
''',
}
MC_PREP = '''import json, wave, shutil
import numpy as np
from pathlib import Path
import narracao
SR = 24000
def tom(s, ch=1):
    t = np.arange(int(s * SR)) / SR
    y = (0.3 * np.sin(2 * np.pi * 220 * t) * 32767).astype(np.float32)
    return np.repeat(y[:, None], ch, axis=1)
def sil(s, ch=1): return np.zeros((int(s * SR), ch), np.float32)
def grava(nome, partes, palavras=None, ch=1):
    y = np.concatenate(partes)
    with wave.open(nome, "wb") as f:
        f.setnchannels(ch); f.setsampwidth(2); f.setframerate(SR); f.writeframes(y.astype("<i2").tobytes())
    if palavras is not None: Path(nome + ".words.json").write_text(json.dumps(palavras), "utf-8")
    return nome
def le(nome):
    with wave.open(nome) as f:
        return f.getframerate(), f.getnchannels(), np.frombuffer(f.readframes(f.getnframes()), "<i2").reshape(-1, f.getnchannels())
def trechos(y):
    q = SR // 100; n = len(y) // q
    db = 10 * np.log10(((y[:n * q].mean(axis=1) / 32768).reshape(n, q) ** 2).mean(axis=1) + 1e-12)
    som = db > -40; out = []; i = 0
    while i < n:
        if som[i]:
            j = i
            while j < n and som[j]: j += 1
            out.append((i / 100, j / 100)); i = j
        else: i += 1
    return out
PAL = [{"word": "um", "start": 0.0, "end": 0.5}, {"word": "dois", "start": 1.1, "end": 1.5},
       {"word": "tres", "start": 1.55, "end": 1.85}]
A = grava("a.wav", [tom(0.5), sil(0.6), tom(0.4), sil(0.05), tom(0.3), sil(1.0)], PAL)
RA = narracao.microcortes(A)
SA, CA, YA = le(A)
TA = trechos(YA)
B = grava("b.wav", [tom(0.5), sil(0.6), tom(0.4)], None, ch=2)
RB = narracao.microcortes(B, gap_s=0.15)
SB, CB, YB = le(B)
C = grava("c.wav", [tom(0.5), sil(0.05), tom(0.5)])
C0 = Path(C).read_bytes()
RC = narracao.microcortes(C)
NA = json.loads(Path(A + ".words.json").read_text())
'''
MC_OCULTO = [
    "isinstance(RA, tuple) and abs(RA[0] - 2.85) < 0.02",
    "1.27 <= len(YA) / SA <= 1.45 and abs(RA[1] - len(YA) / SA) < 0.02",
    "SA == SR and CA == 1",
    "len(TA) == 3",
    "all(abs((b - a) - d) <= 0.04 for (a, b), d in zip(TA, [0.5, 0.4, 0.3]))",
    "0.04 <= TA[1][0] - TA[0][1] <= 0.10",
    "0.02 <= TA[2][0] - TA[1][1] <= 0.08",
    "abs(NA[1]['start'] - TA[1][0]) <= 0.04 and abs(NA[2]['start'] - TA[2][0]) <= 0.04",
    "abs(NA[0]['start'] - 0.0) <= 0.04 and NA[2]['end'] <= len(YA) / SA + 0.01",
    "CB == 2 and RB is not None and 0.10 <= trechos(YB)[1][0] - trechos(YB)[0][1] <= 0.19",
    "RC is None and Path(C).read_bytes() == C0",
]
MC_PEDIDO = ("fica o narracao.py da narração dos Shorts. Pedido da dona: 'o que é muito usado nos Shorts é cortar as "
             "pausas entre as falas — micro cortes em vez de acelerar a fala'. Implemente em narracao.py a função "
             "microcortes(wav, gap_s=None): mexe no .wav no lugar (16 bits, mono ou estéreo); todo silêncio maior que "
             "gap_s (padrão GAP_MICROCORTE, 0,07 s; silêncio = quadros de 10 ms abaixo de LIMIAR_SILENCIO_DB) fica com "
             "gap_s, guardando o som original das pontas e com crossfade de 6 ms na emenda; a FALA NÃO ACELERA nem "
             "muda; o <wav>.words.json (se existir) acompanha os cortes. Devolve (duração antes, duração depois) em "
             "segundos, ou None quando não há nada a cortar (arquivo intocado). Use numpy e o módulo wave. "
             "Teste com um wav gerado por você antes de terminar.")

TAREFAS = {
    "fila_agendado": (FILA, FILA_PREP, FILA_OCULTO, FILA_PEDIDO),
    "numero_yt": (YT, YT_PREP, YT_OCULTO, YT_PEDIDO),
    "microcortes": (MC, MC_PREP, MC_OCULTO, MC_PEDIDO),
}

hb.TAREFAS = TAREFAS
hb.PLACAR = Path(__file__).with_name("hibridos_real_placar.json")
hb.BASE = Path(__file__).with_name("hibridos_real")
REF = Path(__file__).with_name("hibridos_real_ref")  # soluções de referência: REF/<tarefa>/<arquivo>


def conferir_ref():
    for t, (arqs, prep, casos, _) in TAREFAS.items():
        for nome in ("bug", "ref"):
            p = Path("_val") / t / nome
            shutil.rmtree(p, ignore_errors=True)
            for n, txt in arqs.items():
                (p / n).parent.mkdir(parents=True, exist_ok=True)
                (p / n).write_text(txt, "utf-8")
            if nome == "ref":
                for f in (REF / t).glob("*.py"):
                    shutil.copy(f, p / f.name)
            r = hb.nota(p, prep, casos)
            print(f"{t:14} {nome:4} {r['ok']:>2}/{len(casos)}", r["falhas"][:3])
    shutil.rmtree("_val", ignore_errors=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--ref"]:
        conferir_ref()
    else:
        import json
        from concurrent.futures import ThreadPoolExecutor
        filtro = sys.argv[1] if len(sys.argv) > 1 else ""
        feito = json.loads(hb.PLACAR.read_text("utf-8")) if hb.PLACAR.exists() else {}
        import re
        fila = [(m, t) for m in hb.MODELOS if re.search(filtro, m) for t in TAREFAS if t not in feito.get(m, {})]
        print(len(fila), "rodadas na fila", flush=True)
        with ThreadPoolExecutor(hb.PARALELO) as ex:
            list(ex.map(lambda a: hb.rodar(*a), fila))
        hb.resumo()
