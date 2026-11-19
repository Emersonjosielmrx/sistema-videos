"""alarme_vendas.py — ALARME DE VENDA E DE MENSAGEM DE CLIENTE (dona 18/11: "me avisar de compra feita ou mensagem
recebida, qualquer coisa assim, pergunta, pelo Telegram com máxima prioridade até ser respondido; e melhore a do
99Freelas porque pode até mandar mais, se mandar eu nunca vi; aviso sonoro no PC bem característico das duas coisas").

Por quê: a resposta de cliente do 99Freelas ia só para o bot "Interessados no produto", sem som de madrugada e marcada
como "ℹ️ AVISO" no meio de outros — a dona nunca viu. Aqui cada alerta:
  • sai por avisos.prioridade (TODOS os bots, com som, até de madrugada);
  • REPETE a cada REPETIR_MIN até a dona confirmar ("ok", "visto", "vi", "respondi", "já vi" no @plantao_emerson_bot,
    ou "ok 12" para um alerta só) — o plantao.py chama confirmar();
  • toca no PC um som próprio: 💰 VENDA = moedas subindo (alegre); 💬 MENSAGEM = dois toques de campainha. Repete junto.

Uso pelos robôs:   import alarme_vendas; alarme_vendas.alertar("venda"|"mensagem", titulo, texto, link, chave)
Tarefa AlarmeVendas (1/1 min, oculta):  python alarme_vendas.py         -> repete os pendentes e toca o som
Teste:  python alarme_vendas.py --som venda|mensagem    |   python alarme_vendas.py --lista
Desligar: ALARME_VENDAS=0 (variável) ou apague a tarefa AlarmeVendas.
"""
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
EST = BASE / "estado" / "alarme_vendas.json"
LOG = BASE / "estado" / "alarme_vendas.log"
# 19/11 dona: "respondi a mensagem ontem e ele mandou CENTENAS de mensagens mesmo eu tendo respondido" — 56 lembretes x
# 10 bots (~560). Agora: o 1º aviso vai a todos os bots; os LEMBRETES só no bot Plantão, no máximo MAX_LEMBRETES, com
# intervalo dobrando (10, 20, 40, 60, 60, 60 min); e o alarme FECHA SOZINHO quando a dona responde na plataforma
# (resolvido(chave), chamado pelo robô do 99Freelas e pelo vigia do GGMax).
REPETIR_MIN = 10          # 1º lembrete 10 min depois; depois dobra até TETO_MIN
TETO_MIN = 60
MAX_LEMBRETES = 6
SOM_A_CADA_MIN = 5        # PC: toca de novo a cada 5 min enquanto houver pendente (e só nas 2 primeiras horas)
SOM_ATE_H = 2
DESISTIR_H = 12           # depois de 12 h sem resposta para de insistir (fica no registro)
CONFIRMA = re.compile(r"^\W*(ok|okay|visto|vi|j[aá]\s*vi|respondi|j[aá]\s*respondi|entendi|recebi|beleza|blz|certo)"
                      r"\W*(\d+)?\W*$", re.I)


def log(m):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%d/%m %H:%M:%S}] {m}\n")
    except OSError:
        pass


def _ler():
    try:
        return json.loads(EST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"seq": 0, "alertas": {}}


def _gravar(d):
    EST.parent.mkdir(parents=True, exist_ok=True)
    tmp = EST.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(EST)


# ───────────── som ─────────────
SONS = {"venda": [(988, .09), (1319, .09), (1568, .09), (1976, .09), (2637, .12), (0, .12)] * 3 + [(2637, .45)],
        "mensagem": [(1046, .35), (784, .55), (0, .4)] * 2}


def _wav(tipo):
    """Gera (uma vez) o WAV do som: o Beep do Windows falha sem alto-falante interno (18/11), o WAV sai nas caixas."""
    import math
    import struct
    import wave
    arq = BASE / "estado" / f"som_{tipo}.wav"
    if arq.exists():
        return arq
    taxa, quadros = 22050, bytearray()
    for freq, dur in SONS[tipo]:
        n = int(taxa * dur)
        for i in range(n):
            env = min(1.0, i / 400, (n - i) / 400)  # sem estalo no começo/fim de cada nota
            v = 0 if not freq else 0.55 * env * (math.sin(2 * math.pi * freq * i / taxa)
                                                 + 0.3 * math.sin(4 * math.pi * freq * i / taxa))
            quadros += struct.pack("<h", int(max(-1, min(1, v)) * 32000))
    arq.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(arq), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(bytes(quadros))
    return arq


def tocar(tipo):
    """Som característico: 💰 venda = moedas subindo 3x; 💬 mensagem = ding-dong 2x (WAV pelas caixas de som)."""
    tipo = "venda" if tipo == "venda" else "mensagem"
    try:
        import winsound
        winsound.PlaySound(str(_wav(tipo)), winsound.SND_FILENAME)
    except Exception as e:  # noqa: BLE001
        log(f"som falhou: {e}")


def _telegram(a, n, repeticao):
    sys.path.insert(0, str(BASE))
    rot = "💰💰💰 VENDA FEITA" if a["tipo"] == "venda" else "💬💬 CLIENTE MANDOU MENSAGEM"
    if repeticao:  # lembrete: curto e SÓ no bot Plantão (não nos 10 bots)
        import plantao
        txt = (f"🔔 Lembrete {repeticao}/{MAX_LEMBRETES} — {rot} #{n}\n{a['origem']}: {a['titulo']}\n👉 {a['link']}\n"
               f"(para sozinho quando você responder lá; ou mande \"ok\")")
        return 1 if plantao.enviar(txt) else 0
    import avisos
    texto = (f"{rot} — #{n}\n{a['origem']}: {a['titulo']}\n\n{a['texto'][:1500]}\n\n👉 {a['link']}\n\n"
             f"O alarme para sozinho quando você responder ao cliente lá (ou mande \"ok\" no bot Plantão).")
    return avisos.prioridade(texto, origem=f"alarme-{a['tipo']}")


def resolvido(chave, motivo="a dona respondeu na plataforma"):
    """Fecha o alarme daquela chave (a dona já respondeu/atendeu). Devolve True se fechou algum."""
    d = _ler()
    fechou = False
    for n, a in d["alertas"].items():
        if a["chave"] == chave and not a.get("confirmado"):
            a["confirmado"] = datetime.now().isoformat(timespec="seconds")
            a["motivo_fim"] = motivo
            fechou = True
            log(f"#{n} fechado sozinho: {motivo}")
    if fechou:
        _gravar(d)
    return fechou


def abertos(prefixo=""):
    """Chaves dos alarmes ainda abertos (para o vigia conferir se já foram atendidos)."""
    return [a["chave"] for a in _ler()["alertas"].values()
            if not a.get("confirmado") and not a.get("desistiu") and a["chave"].startswith(prefixo)]


def alertar(tipo, origem, titulo, texto, link="", chave=None):
    """Registra um alerta novo (venda|mensagem) e já avisa + toca. Mesma chave = não duplica. Devolve o número."""
    if os.environ.get("ALARME_VENDAS", "1") == "0":
        return None
    d = _ler()
    chave = chave or f"{origem}:{titulo}:{texto[:80]}"
    for n, a in d["alertas"].items():
        if a["chave"] == chave:
            return int(n)
    d["seq"] += 1
    n = d["seq"]
    a = {"tipo": tipo, "origem": origem, "titulo": titulo, "texto": texto, "link": link, "chave": chave,
         "criado": time.time(), "ultimo_tg": time.time(), "ultimo_som": time.time(), "vezes": 1, "confirmado": None}
    d["alertas"][str(n)] = a
    _gravar(d)
    ok = _telegram(a, n, 0)
    log(f"NOVO #{n} {tipo} {origem}: {titulo[:80]} (telegram em {ok} bots)")
    tocar(tipo)
    return n


def confirmar(texto):
    """Chamado pelo plantao.py com a mensagem da dona. Se for confirmação, fecha o(s) alerta(s) e devolve a resposta."""
    m = CONFIRMA.match(texto or "")
    if not m:
        return None
    d = _ler()
    abertos = {n: a for n, a in d["alertas"].items() if not a.get("confirmado")}
    if not abertos:
        return None  # "ok" solto sem alarme aberto: segue o fluxo normal do plantão
    alvo = [m.group(2)] if m.group(2) and m.group(2) in abertos else list(abertos)
    for n in alvo:
        d["alertas"][n]["confirmado"] = datetime.now().isoformat(timespec="seconds")
    _gravar(d)
    log(f"dona confirmou {alvo}")
    resto = len(abertos) - len(alvo)
    return (f"🔕 Alarme parado: {', '.join('#' + n for n in alvo)}."
            + (f" Ainda {resto} aberto(s)." if resto else ""))


def rodada():
    if os.environ.get("ALARME_VENDAS", "1") == "0":
        return
    d = _ler()
    agora = time.time()
    tocar_tipo = None
    mudou = False
    for n, a in d["alertas"].items():
        if a.get("confirmado") or a.get("desistiu"):
            continue
        if agora - a["criado"] > DESISTIR_H * 3600:
            a["desistiu"] = True; mudou = True
            log(f"#{n} sem confirmação em {DESISTIR_H}h — parei de insistir")
            continue
        feitos = a["vezes"] - 1
        espera = min(TETO_MIN, REPETIR_MIN * 2 ** feitos) * 60
        if feitos < MAX_LEMBRETES and agora - a["ultimo_tg"] >= espera:
            a["vezes"] += 1; a["ultimo_tg"] = agora; mudou = True
            _telegram(a, n, a["vezes"] - 1)
            log(f"#{n} lembrete {a['vezes'] - 1}")
        if agora - a["criado"] < SOM_ATE_H * 3600 and agora - a["ultimo_som"] >= SOM_A_CADA_MIN * 60:
            a["ultimo_som"] = agora; mudou = True
            tocar_tipo = "venda" if a["tipo"] == "venda" or tocar_tipo == "venda" else "mensagem"
    if mudou:
        _gravar(d)
    if tocar_tipo:
        tocar(tocar_tipo)


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.argv[1:2] == ["--som"]:
        tocar(sys.argv[2] if len(sys.argv) > 2 else "venda")
    elif sys.argv[1:2] == ["--lista"]:
        for n, a in _ler()["alertas"].items():
            print(n, a["tipo"], a["origem"], a["titulo"][:60], "CONFIRMADO" if a.get("confirmado") else "ABERTO")
    else:
        rodada()
