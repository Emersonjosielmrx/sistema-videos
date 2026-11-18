"""Trecho da legenda cinética MIX dos Shorts (recapd bin/legenda_mix.py).
alinhadas = [(palavra, ini_s, fim_s)] vindas do Whisper, em ordem de tempo."""
import re

CURTAS = {"a", "o", "e", "é", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "um", "uma", "que",
          "com", "pra", "para", "por", "se", "seu", "sua", "te", "eu", "ao", "à", "os", "as", "ou", "mas", "não",
          "já", "tem", "vai", "só", "isso", "essa", "esse", "ela", "ele", "me", "mais", "muito", "quem", "como"}


def _limpa(w):
    return re.sub(r"^[^\wÀ-ÿ]+|[^\wÀ-ÿ!?%]+$", "", w)


def blocos(alinhadas):
    """[(curtas_em_cima, forte, ini, fim)] — curtas se juntam à próxima forte; cada bloco fica até o próximo."""
    bl, pre = [], []
    for w, s, e in alinhadas:
        if _limpa(w).lower() in CURTAS and len(pre) < 3:
            pre.append((w, s, e))
            continue
        bl.append(([x[0] for x in pre], w, pre[0][1] if pre else s, e))
        pre = []
    if pre:
        bl.append(([x[0] for x in pre[:-1]], pre[-1][0], pre[0][1], pre[-1][2]))
    res = []
    for i, (cima, forte, s, e) in enumerate(bl):
        prox = bl[i + 1][2] if i + 1 < len(bl) else e + 0.5
        res.append((cima, forte, s, max(min(prox, e + 0.5), s + 0.3)))
    return res
