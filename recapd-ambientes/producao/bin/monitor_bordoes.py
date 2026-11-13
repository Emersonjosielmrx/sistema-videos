"""monitor_bordoes.py — descobre quais bordões/manias a VOZ CLONADA fala estranho e tira do roteiro (dono, 22/10/2026).

Pedido do dono: "já colocamos nos personagens falas icônicas, mas temos que monitorar quais delas ficam estranhas". Ex.:
"pipipipipi" virar "a-a-a-a", bordão comido pelo clone, palavra soletrada.

Depois que a narração de um vídeo sai, cada frase que contém um bordão/mania do guia do narrador é TRANSCRITA (Groq
Whisper, pelo proxy — só essas frases, poucos KB) e o trecho do bordão é comparado com o que saiu. Placar por voz em
D:\\hipercool-materiais\\amostras_voz\\monitor_bordoes.json; bordão que sai estranho 2+ vezes (e em metade ou mais das
vezes) entra em `bordoes_estranhos` no linguagem_v2.json da voz — o roteiro (anime_script._jeito_do_narrador) para de
pedir ele. Nunca derruba a produção: qualquer falha aqui só é logada.
"""
import difflib
import json
import logging
import re
import sys
import time
import unicodedata
from pathlib import Path

VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
PLACAR = Path(r"D:\hipercool-materiais\amostras_voz\monitor_bordoes.json")
LOG = Path(r"D:\hipercool-materiais\amostras_voz\monitor_bordoes.jsonl")
LIMIAR = 0.62      # semelhança mínima do trecho do bordão (0..1) pra contar como "saiu certo"
MIN_FALHAS = 2


def _norm(t):
    t = unicodedata.normalize("NFKD", str(t or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z ]+", " ", re.sub(r"\s+", " ", t)).strip()


def _semelhanca(esperado, ouvido):
    """Melhor semelhança do bordão contra qualquer janela do texto ouvido do mesmo tamanho."""
    e, o = _norm(esperado), _norm(ouvido).split()
    if not e or not o:
        return 0.0
    n = max(1, len(e.split()))
    melhor = 0.0
    for i in range(max(1, len(o) - n + 1)):
        for k in (n - 1, n, n + 1):
            jan = " ".join(o[i:i + max(1, k)])
            melhor = max(melhor, difflib.SequenceMatcher(None, e, jan).ratio())
    return melhor


def _transcrever(wav):
    # 23/10: era sys.path.insert(0, bin do hipercool) e FICAVA — os imports seguintes do mesmo processo (fx_foley,
    # fx_music...) passavam a vir do hipercool, que tem outra versão: 3 Shorts morreram (ImportError
    # enhance_narration_audio / add_dynamic_music sem no_copyright). Agora entra no FIM (o hp_common é o daqui) e sai.
    h = r"D:\hipercool-videos\bin"
    sys.path.append(h)
    try:
        import groq_api
    finally:
        while h in sys.path:
            sys.path.remove(h)
    r = groq_api.transcrever(str(wav), idioma="pt", palavras=False, timeout=120)
    return " ".join(s.get("text", "") for s in (r or {}).get("segments", []))


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def conferir(voz, frases_wavs):
    """frases_wavs: [(texto da frase, caminho do wav narrado)]. Confere só as frases com bordão/mania do guia."""
    if not voz:
        return
    guia_p = VOZES / voz / "linguagem_v2.json"
    guia = _ler(guia_p, {})
    alvos = [b for b in (guia.get("bordoes_iconicos") or []) + (guia.get("maneirismos") or []) if b]
    if not alvos:
        return
    placar = _ler(PLACAR, {})
    pv = placar.setdefault(voz, {})
    novos_estranhos = []
    for texto, wav in frases_wavs:
        presentes = [b for b in alvos if _norm(b) and _norm(b) in _norm(texto)]
        if not presentes or not Path(wav).exists():
            continue
        try:
            ouvido = _transcrever(wav)
        except Exception as e:  # noqa: BLE001
            logging.info(f"[monitor_bordoes] transcrição falhou ({type(e).__name__}) — pulo")
            return
        for b in presentes:
            s = _semelhanca(b, ouvido)
            d = pv.setdefault(b, {"testes": 0, "falhas": 0})
            d["testes"] += 1
            if s < LIMIAR:
                d["falhas"] += 1
            d["ultima"] = {"sem": round(s, 2), "ouvido": ouvido[:160], "em": time.strftime("%Y-%m-%d %H:%M")}
            try:
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"voz": voz, "bordao": b, "sem": round(s, 2), "ouvido": ouvido[:200],
                                        "wav": str(wav), "em": time.strftime("%Y-%m-%dT%H:%M:%S")},
                                       ensure_ascii=False) + "\n")
            except OSError:
                pass
            logging.info(f"[monitor_bordoes] {voz}: \"{b}\" -> semelhança {s:.2f}{' (ESTRANHO)' if s < LIMIAR else ''}")
            if d["falhas"] >= MIN_FALHAS and d["falhas"] / d["testes"] >= 0.5 \
                    and b not in (guia.get("bordoes_estranhos") or []):
                novos_estranhos.append(b)
    if novos_estranhos:
        guia.setdefault("bordoes_estranhos", []).extend(novos_estranhos)
        guia_p.write_text(json.dumps(guia, ensure_ascii=False, indent=1), encoding="utf-8")
        logging.warning(f"[monitor_bordoes] {voz}: fora do roteiro (soam estranhos): {novos_estranhos}")
    PLACAR.parent.mkdir(parents=True, exist_ok=True)
    tmp = PLACAR.with_name(PLACAR.name + ".tmp")
    tmp.write_text(json.dumps(placar, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(PLACAR)


if __name__ == "__main__":  # relatório: python monitor_bordoes.py
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for v, bs in sorted(_ler(PLACAR, {}).items()):
        for b, d in sorted(bs.items(), key=lambda kv: -kv[1]["falhas"]):
            print(f"{v:18} {d['falhas']}/{d['testes']} estranho  \"{b}\"  (última: {d.get('ultima', {}).get('sem')})")
