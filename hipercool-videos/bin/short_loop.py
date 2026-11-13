#!/usr/bin/env python3
"""Fecho em LOOP do Short de resumo: uma fala nova do narrador no fim que amarra no primeiro quadro.

Pedido do dono (16/10/2026): "nos cortes é bom conectar ao começo; geralmente eles terminam com algo
como 'e é por isso que quando o vídeo começa tal coisa acontece', aí a pessoa fica vendo em loop sem
perceber que o vídeo acabou". O Short que volta sozinho pro começo soma visualização e retenção.

Como faz: ouve (Groq) os primeiros e os últimos segundos do resumo, pede ao modelo UMA frase do
narrador que fecha a história e termina pendurada, de modo que a primeira frase do vídeo complete a
ideia, grava na voz do narrador da obra e devolve o wav + a legenda. Quem cola no vídeo é o
short_resumo.montar, no mesmo encode (último quadro parado enquanto a frase é dita).

Qualquer falha devolve None e o resumo sai como antes, sem o fecho.
"""
import json
import re
import subprocess
from pathlib import Path

from hp_common import log

OUVIR_S = 12.0      # quanto do começo e do fim do resumo o modelo "ouve"
SOBRA_S = 0.15      # depois da última palavra, antes de voltar pro começo (loop seco, sem respiro)

_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _ff(args, timeout=300):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, args)], check=True, timeout=timeout,
                   capture_output=True, creationflags=_SEM_JANELA)


def _dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        str(path)], capture_output=True, text=True, timeout=30, creationflags=_SEM_JANELA)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _ouvir(video, a, b, lang, tmp):
    """Texto falado em [a, b] do vídeo (Groq). "" se não deu."""
    import groq_api
    flac = Path(tmp) / f"_loop_{int(a * 1000)}.flac"
    try:
        _ff(["-ss", f"{a:.3f}", "-t", f"{max(0.5, b - a):.3f}", "-i", video, "-vn", "-ac", "1",
             "-ar", "16000", "-c:a", "flac", flac])
        j = groq_api.transcrever(flac, lang, palavras=False) or {}
        return (j.get("text") or "").strip()
    except Exception as e:  # noqa: BLE001
        log(f"  [!] fecho em loop: não ouvi o trecho {a:.0f}-{b:.0f}s ({str(e)[:80]})")
        return ""
    finally:
        flac.unlink(missing_ok=True)


def _escrever_frase(comeco, fim, lang, gancho=""):
    import gemini_llm
    nome_lingua = "português do Brasil"
    if lang and lang != "pt":
        try:
            import idiomas
            nome_lingua = idiomas.IDIOMAS[lang]["nome"]
        except Exception:  # noqa: BLE001
            nome_lingua = lang
    pedido = (
        "Este é um Short (vídeo vertical) que resume um capítulo de manhwa, narrado. Ele vai tocar em "
        "LOOP: quando acaba, volta sozinho pro começo. Escreva UMA frase final do narrador que:\n"
        "- fecha o que acabou de acontecer no fim do vídeo;\n"
        "- termina PENDURADA, puxando pro começo: a primeira frase do vídeo tem que soar como a "
        "continuação dela, pra quem assiste não perceber que o vídeo recomeçou;\n"
        "- 8 a 18 palavras, fala de narrador de recap (próxima, provocadora), sem nome da obra;\n"
        "- termina com vírgula ou reticência, NUNCA com ponto final.\n"
        "Molde: \"...e é exatamente por isso que, naquela noite,\" -> o vídeo recomeça com a cena "
        "daquela noite.\n"
        f"Escreva em {nome_lingua}.\n\n"
        f"COMEÇO do vídeo (o que se ouve logo depois da sua frase): «{comeco}»\n"
        f"FIM do vídeo (o que se ouve logo antes da sua frase): «{fim}»\n"
        + (f"Gancho do capítulo: {gancho}\n" if gancho else "")
        + '\nDevolva SÓ JSON {"frase": "..."}.')
    try:
        txt = gemini_llm.generate_text(pedido, max_tokens=400, temperature=0.8, max_attempts=3)
        frase = str(json.loads(re.sub(r"^```json\s*|\s*```$", "", (txt or "").strip())).get("frase") or "")
    except (ValueError, TypeError, AttributeError):
        return ""
    # reticência no começo faz a voz entrar hesitando; a do fim fica (é o que deixa a frase pendurada)
    frase = re.sub(r"\s+", " ", frase).strip().lstrip(".… ")
    if frase.endswith(".") and not frase.endswith(".."):
        frase = frase[:-1] + "..."  # ponto final fecha a entonação; o loop pede a frase no ar
    frase = frase[:1].upper() + frase[1:]
    return frase if 5 <= len(frase.split()) <= 24 else ""


def _gravar_voz(frase, obra_slug, lang, wav):
    if lang and lang != "pt":
        import idiomas
        return idiomas.falar(frase, wav, "Narrador", "F", lang)
    import elenco
    return elenco.falar(obra_slug, frase, wav, "Narrador", None)


def _tempos(frase, wav, lang, dur):
    """[(palavra, ini, fim)] da frase dentro do wav: Groq com tempo por palavra, ou proporcional."""
    try:
        import groq_api
        j = groq_api.transcrever(wav, lang, palavras=True) or {}
        ws = [((w.get("word") or "").strip(), float(w["start"]), float(w["end"])) for w in j.get("words") or []]
        ws = [w for w in ws if w[0]]
        if ws:
            return ws
    except Exception:  # noqa: BLE001
        pass
    toks = frase.split()
    peso = [len(t) + 2 for t in toks]
    tot, t, out = sum(peso), 0.0, []
    for tok, p in zip(toks, peso):
        d = dur * p / tot
        out.append((tok, t, t + d))
        t += d
    return out


def _ass(caminho, palavras, t0, lang):
    """Legenda da frase no mesmo estilo da legenda do narrador (fx_acabamento: Cap), a partir de t0."""
    import fx_acabamento as fx
    fonte = "Montserrat ExtraBold"
    if lang and lang != "pt":
        try:
            import idiomas
            fonte = idiomas.IDIOMAS.get(lang, {}).get("fonte_ass") or fonte
        except Exception:  # noqa: BLE001
            pass
    hl = fx.ass_color(fx.COR)
    cab = ("[Script Info]\nScriptType: v4.00+\n"
           f"PlayResX: {fx.OW}\nPlayResY: {fx.OH}\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
           "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
           "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
           "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
           f"Style: Cap,{fonte},110,&H00FFFFFF,{hl},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,5,40,40,0,1\n\n"
           "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = []
    for k in range(0, len(palavras), 3):  # blocos de 3 palavras, a ativa em destaque
        bloco = palavras[k:k + 3]
        toks = [fx._limpa(w) for w, _a, _b in bloco]
        prox = palavras[k + 3][1] if k + 3 < len(palavras) else float("inf")
        for i, (_w, a, b) in enumerate(bloco):
            # o último do bloco não invade o bloco seguinte (sobrava o rabo do "Q" embaixo da linha nova)
            fim = bloco[i + 1][1] if i + 1 < len(bloco) else min(b + 0.2, prox)
            partes = [f"{{\\c{hl}}}{fx._esc(tok)}{{\\r}}" if j == i else fx._esc(tok)
                      for j, tok in enumerate(toks) if tok]
            ev.append(f"Dialogue: 2,{fx._ts(t0 + a)},{fx._ts(t0 + max(fim, a + 0.05))},Cap,,0,0,0,,"
                      f"{{\\an5\\pos({fx.OW // 2},{fx.CAP_Y})}}" + " ".join(partes))
    Path(caminho).write_text(cab + "\n".join(ev) + "\n", encoding="utf-8")


def preparar(video, trechos, meta, obra, out_dir):
    """{"wav", "dur", "ass", "frase"} do fecho, com a legenda já no tempo do FIM do resumo; None se não deu.

    trechos: os (ini, fim) do vídeo original que o resumo costura, na ordem."""
    if not trechos:
        return None
    lang = (meta or {}).get("idioma") or "pt"
    if lang == "pt-BR":
        lang = "pt"
    out_dir = Path(out_dir)
    total = sum(b - a for a, b in trechos)
    a0, _b0 = trechos[0]
    _a1, b1 = trechos[-1]
    comeco = _ouvir(video, a0, min(a0 + OUVIR_S, trechos[0][1] + OUVIR_S), lang, out_dir)
    fim = _ouvir(video, max(_a1, b1 - OUVIR_S), b1, lang, out_dir)
    if not comeco or not fim:
        log("  [!] fecho em loop: sem transcrição do começo/fim — resumo sai sem ele")
        return None
    gancho = (((meta or {}).get("acabamento") or {}).get("editorial") or {}).get("gancho") or ""
    frase = _escrever_frase(comeco, fim, lang, gancho if lang == "pt" else "")
    if not frase:
        log("  [!] fecho em loop: o modelo não devolveu frase que sirva — resumo sai sem ele")
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", (obra or "").lower()).strip("-")
    wav = out_dir / "_loop_fecho.wav"
    try:
        ok = _gravar_voz(frase, slug, lang, wav)
    except Exception as e:  # noqa: BLE001
        log(f"  [!] fecho em loop: voz falhou ({str(e)[:80]})")
        ok = False
    dur = _dur(wav) if ok and wav.exists() else 0.0
    if dur < 1.0:
        log("  [!] fecho em loop: sem voz — resumo sai sem ele")
        return None
    ass = out_dir / "_loop_fecho.ass"
    _ass(ass, _tempos(frase, wav, lang, dur), total, lang)
    log(f"  fecho em loop ({dur:.1f}s): {frase}")
    return {"wav": wav, "dur": dur + SOBRA_S, "ass": ass, "frase": frase, "inicio": total}
