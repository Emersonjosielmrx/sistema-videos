#!/usr/bin/env python3
"""Amostras A/B de voz humana pro dono ouvir (17/10/2026).

O MESMO trecho do cap 5 (falas 106-116: o corredor, a mulher misteriosa, o "Professora?!" que é
impacto, e o respiro) gravado uma vez por técnica + a versão atual + tudo junto. Só áudio (voz), sem
trilha, pra dar pra comparar a voz. Saída em D:/hipercool-materiais/amostras_voz/<data>/ com LEIA.txt.

    python bin/amostras_voz.py
    python bin/amostras_voz.py --so 0_atual,4_pausa_variavel
"""
import argparse
import copy
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log  # noqa: E402

OBRA = "the-inheritor"
ROTEIRO = PROJECT_DIR / "workspace" / "narration_cache" / "the-inheritor-cap05_sk1_sf1_v3_118panels.json"
JANELA = range(106, 117)
SAIDA = Path(r"D:/hipercool-materiais/amostras_voz") / date.today().isoformat()
MIN_CLIP = 1.5  # fx_clips.build_clip: painel nunca dura menos que isso
# Figurante sem entrada no elenco: a voz que o cap 5 usou de verdade (log de 16/10 23:45). Sem isto o
# elenco.voz CRIAVA o figurante no config da obra (17/10: criou "mulher desconhecida|F" com uma Isabella
# que o edge recusa — removido).
VOZ_FIXA = {"Mulher desconhecida": {"voice": "pt-BR-FranciscaNeural", "rate": "-12%", "pitch": "-14Hz"}}

VERSOES = {
    "0_atual": ({}, "Como sai HOJE na produção (já com a curva do clímax corrigida em 17/10)."),
    "1_sem_camera": ({"texto": "sem_camera"}, "Ideia 7: o narrador para de descrever o desenho ('alguém fora do "
                     "quadro grita...') e conta a história. Muda só o TEXTO das falas pegas."),
    "2_muletas": ({"texto": "muletas"}, "Ideia 3: muletas reais dos narradores de referência ('mano', 'tipo', "
                  "'cara', 'olha só'...) e fala com quem assiste, na medida que eles usam. Muda só o TEXTO."),
    "3_respiracao": ({"respirar": True}, "Ideia 13: respiração humana real antes de algumas falas do narrador "
                     "(depois do impacto e antes de fala longa)."),
    "4_pausa_variavel": ({"pausa": True}, "Ideia 14: a pausa entre falas segue a curva — curta chegando no "
                         "clímax, silêncio de suspense logo antes do 'Professora?!', mais longa depois."),
    "5_ritmo_por_pedaco": ({"pedaco": True}, "Ideia 8: cada fala do narrador gravada em pedaços com velocidades "
                           "diferentes (começa calmo, acelera no meio, segura no fim)."),
    "6_gemini_nos_picos": ({"gemini": True}, "Ideia 11: as falas que chegam no clímax vão pro Gemini com instrução "
                           "de estilo ('empolgado, contando pra um amigo'); o resto fica no edge."),
    "7_tudo_junto": ({"texto": "sem_camera+muletas", "respirar": True, "pausa": True, "pedaco": True, "gemini": True,
                      "rate": 9}, "Tudo junto (inclusive o ritmo do 8)."),
    "8_ritmo_das_referencias": ({"rate": 9, "pausa": True}, "Medido em 17/10: o nosso narrador fala 171 palavras/min "
                                "e os humanos ~200 (11 canais), e nós temos 5,8 pausas longas por minuto contra "
                                "0,2-1,4 deles. Aqui: narrador +9% mais rápido e pausas curtas (só segura antes do impacto)."),
}
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _ff(args, timeout=300):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, args)], check=True, timeout=timeout,
                   capture_output=True, creationflags=_SEM_JANELA)


def textos(recap, modo):
    """Falas da janela com o texto da versão. Cache em disco: o LLM roda uma vez por modo."""
    cache = SAIDA / f"_textos_{modo.replace('+', '_')}.json"
    if cache.exists():
        return {int(k): v for k, v in json.loads(cache.read_text(encoding="utf-8")).items()}
    import narration
    locs = copy.deepcopy(recap["locucoes"])
    desc = recap.get("descriptions") or []
    real = narration.voz_humana
    narration.voz_humana = lambda chave: True  # liga as chaves só aqui dentro
    try:
        if "sem_camera" in modo:
            narration._reescrever_narrador_fraco(locs, desc, "narradora", "F")
        if "muletas" in modo:
            narration.temperar_muletas(locs, list(JANELA), "narradora")
    finally:
        narration.voz_humana = real
    out = {i: locs[i]["text"] for i in JANELA}
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def gravar_versao(nome, op, recap, impactos):
    import elenco
    import voz_humana as vh
    pasta = SAIDA / "_falas" / nome
    pasta.mkdir(parents=True, exist_ok=True)
    txt = textos(recap, op["texto"]) if op.get("texto") else {i: recap["locucoes"][i]["text"] for i in JANELA}
    wavs, notas = [], []
    for i in JANELA:
        loc = recap["locucoes"][i]
        persona = loc.get("persona") or "Narrador"
        genero = None if vh._eh_narrador(persona) else loc.get("gender")
        texto = txt[i]
        wav = pasta / f"{i}.wav"
        feito, como = False, "edge"
        if op.get("gemini") and vh._eh_narrador(persona) and vh.eh_pico(i, impactos):
            feito = vh.falar_gemini_estilo(OBRA, texto, wav, persona, genero)
            como = "gemini+estilo" if feito else "edge (gemini falhou)"
        if not feito and op.get("pedaco") and vh._eh_narrador(persona):
            feito = vh.falar_em_pedacos(OBRA, texto, wav, persona, genero, indice=i, impactos=impactos,
                                        extra_rate=op.get("rate", 0))
            como = "edge em pedaços" if feito else "edge"
        if not feito and op.get("rate") and vh._eh_narrador(persona):
            v, _g = elenco.voz(OBRA, persona, genero)
            feito = elenco.falar_edge(texto, wav, vh._deslocar_rate(v, op["rate"]), persona, obra=OBRA,
                                      indice=i, impactos=impactos)
            como = f"edge {op['rate']:+d}%"
        if not feito and persona in VOZ_FIXA:
            feito = elenco.falar_edge(texto, wav, VOZ_FIXA[persona], persona, obra=OBRA, indice=i, impactos=impactos)
        if not feito:
            feito = elenco.falar(OBRA, texto, wav, persona, genero, indice=i, impactos=impactos)
        if not feito:
            log(f"  [!] {nome}: fala {i} sem voz")
            continue
        extra = vh.vestir(wav, i, impactos, texto, persona, pausa=bool(op.get("pausa")),
                          respirar=bool(op.get("respirar")))
        # o painel dura no mínimo MIN_CLIP: a sobra vira silêncio, como no vídeo
        d = vh.duracao(wav)
        if d < MIN_CLIP:
            tmp = wav.with_suffix(".pad.wav")
            _ff(["-i", wav, "-af", f"apad=whole_dur={MIN_CLIP}", tmp])
            tmp.replace(wav)
        wavs.append(wav)
        notas.append(f"  {i} [{persona}] ({como}{', ' + json.dumps(extra, ensure_ascii=False) if extra else ''}) {texto}")
    lista = pasta / "_lista.txt"
    lista.write_text("".join(f"file '{w.name}'\n" for w in wavs), encoding="utf-8")
    bruto = pasta / "_junto.wav"
    _ff(["-f", "concat", "-safe", "0", "-i", lista, "-c:a", "pcm_s16le", bruto])
    mp3 = SAIDA / f"{nome}.mp3"
    _ff(["-i", bruto, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-b:a", "192k", mp3])
    log(f"  [OK] {mp3.name} ({vh.duracao(mp3):.1f}s)")
    return notas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so", default="")
    a = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)
    recap = json.loads(ROTEIRO.read_text(encoding="utf-8"))
    impactos = [i["fala"] for i in (recap.get("_editorial") or {}).get("impactos", []) if isinstance(i.get("fala"), int)]
    escolha = [v for v in a.so.split(",") if v] or list(VERSOES)
    leia = [f"AMOSTRAS DE VOZ — {date.today():%d/%m/%Y}",
            "Mesmo trecho do cap 5 do The Inheritor (falas 106-116, ~40 s), só a voz, sem trilha.",
            "Ouça o 0_atual primeiro e depois compare cada um com ele. Diga quais ficam (pode ser mais de um).",
            "Nada disso está ligado na produção: cada um tem uma chave em config/fila.json -> voz_humana.", ""]
    for nome in escolha:
        op, descr = VERSOES[nome]
        log(f"versão {nome}")
        try:
            notas = gravar_versao(nome, op, recap, impactos)
        except Exception as e:  # noqa: BLE001 — uma versão quebrada não derruba as outras
            log(f"  [X] {nome} falhou: {str(e)[:200]}")
            notas = [f"  (falhou: {str(e)[:150]})"]
        leia += [f"{nome}.mp3 — {descr}", *notas, ""]
    (SAIDA / ("LEIA.txt" if not a.so else f"LEIA_{a.so.replace(',', '_')}.txt")).write_text(
        "\n".join(leia), encoding="utf-8")
    log(f"pronto: {SAIDA}")


if __name__ == "__main__":
    main()
