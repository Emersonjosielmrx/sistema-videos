"""melhores_cortes.py — acha os MELHORES TRECHOS de um recap longo pros canais de cortes (dona 28/10: "faça também uma
sub função pra identificar os melhores cortes pra colocar nos canais de cortes").

A IA lê o roteiro numerado (com o tempo de cada frase no vídeo final) e escolhe trechos que se sustentam sozinhos:
começam com gancho (frase que prende sem precisar do antes), têm virada/ação no meio e terminam em fecho ou suspense.
Cada trecho vira um Short 9:16 cortado do longo FINAL (narração, legenda, trilha e efeitos já prontos), com o mesmo
enquadramento dos Shorts derivados (shorts_from_deitado.make_vertical_short).
Saída: <workspace>/cortes_longo/corte_NN.mp4 + cortes.json [{arquivo, ini, fim, dur, gancho, titulo, motivo, nota}].
config/longo.json "cortes": {ligado, max, min_s, max_s}. Falhou = longo segue sem cortes.
"""
import json
import logging
import os
import re
import shutil
from pathlib import Path

# 29/10 (Fable, LONGOS_05/ER_01): 35–90 s param no platô de ~1.200 views (44% assistido); os Shorts que passaram do
# 1º lote têm 13–24 s e são vistos inteiros — 1 acontecimento só
PADRAO = {"ligado": True, "max": 5, "min_s": 15, "max_s": 25}


def _cfg():
    try:
        c = json.loads((Path(__file__).resolve().parent.parent / "config" / "longo.json").read_text(encoding="utf-8"))
        return {**PADRAO, **(c.get("cortes") or {})}
    except (OSError, ValueError):
        return dict(PADRAO)


def escolher(frases, inicios, dur_total, cfg, pular=0, proibidas=()):
    """[(i_ini, i_fim, gancho, titulo, motivo, nota)] — índices de frase (fim incluso)."""
    import claude_client
    proib = set(proibidas)
    k = max(1, -(-sum(len(f) for f in frases) // 70000))  # roteiro muito grande: amostra a cada k frases
    linhas = "\n".join(f"{i} [{int(inicios[i]) // 60}:{int(inicios[i]) % 60:02d}] {frases[i][:170]}"
                       for i in range(pular, len(frases), k) if i not in proib)
    prompt = (
        f"Roteiro de um recap narrado em PT-BR (número da frase, [minuto:segundo no vídeo], frase). Escolha os {cfg['max']} "
        f"MELHORES trechos pra virar Shorts de cortes (cada um com {cfg['min_s']} a {cfg['max_s']} segundos). Regras: o "
        "trecho é UM acontecimento só (curto: 2 a 4 frases) e se entende SOZINHO; a 1ª frase já prende (conflito, "
        "humilhação, poder, revelação, briga — nunca começa no meio de uma explicação); termina na frase de impacto, "
        "de um jeito que emende de volta no começo (o Short repete em loop). Prefira os momentos mais virais: vingança, reviravolta, o "
        "fraco mostrando poder, romance/ciúme, humor. Trechos não se sobrepõem. Dê nota 0-10 de potencial viral, um "
        "GANCHO curto pra escrever na tela (até 7 palavras, MAIÚSCULAS nas palavras fortes, sem nome da obra) e um "
        "TÍTULO de Short (até 70 letras, provocação + palavras buscadas como reencarnou, sistema, rei, poder; sem nome "
        "da obra).\nResponda SÓ um JSON: [{\"ini\": 120, \"fim\": 131, \"nota\": 9, \"gancho\": \"...\", "
        "\"titulo\": \"...\", \"motivo\": \"...\"}]\n\nROTEIRO:\n" + linhas)
    resp = claude_client.generate_text(prompt, max_tokens=3000, temperature=0.4, timeout=300,
                                       model=os.environ.get("CORTES_LONGO_MODELO", "gemini-fila")) or ""
    m = re.search(r"\[.*\]", resp, re.S)
    out = []
    for x in json.loads(m.group(0)) if m else []:
        try:
            a, b = int(x["ini"]), int(x["fim"])
        except (KeyError, TypeError, ValueError):
            continue
        if pular <= a <= b < len(frases):
            out.append((a, b, str(x.get("gancho") or "")[:60], str(x.get("titulo") or "")[:90],
                        str(x.get("motivo") or "")[:200], float(x.get("nota") or 0)))
    return out


def _ajustar(a, b, inicios, dur_total, cfg):
    """Tempo (ini, fim) do trecho: começa na frase a, termina no começo da frase seguinte a b; encolhe/estica por
    frase inteira até caber em [min_s, max_s]."""
    fim_de = lambda j: inicios[j + 1] if j + 1 < len(inicios) else dur_total  # noqa: E731
    while b > a and fim_de(b) - inicios[a] > cfg["max_s"]:
        b -= 1
    while b + 1 < len(inicios) and fim_de(b) - inicios[a] < cfg["min_s"]:
        b += 1
    ini, fim = max(0.0, inicios[a] - 0.15), fim_de(b) + 0.2
    return (ini, min(fim, dur_total)) if cfg["min_s"] - 5 <= fim - ini <= cfg["max_s"] + 5 else None


def _legendar_corte(sem_leg, ini, fim, frases, inicios, word_times, saida):
    """02/11: corte em pé com a legenda do formato em pé (MIX, cartões, efeitos, mascote muda no CURTIR): recorta as
    frases do trecho com o tempo relativo ao corte e queima pelo mesmo fx_subtitles do Short. True/False."""
    import fx_subtitles
    ents, offs, wts = [], [], []
    for k, (txt, t0) in enumerate(zip(frases, inicios)):
        t1 = inicios[k + 1] if k + 1 < len(inicios) else fim
        if t1 <= ini or t0 >= fim:
            continue
        ents.append((txt, max(0.4, min(t1, fim) - max(t0, ini))))
        offs.append(max(0.0, t0 - ini))
        wt = word_times[k] if word_times and k < len(word_times) else None
        wts.append([[a - max(0.0, ini - t0), b - max(0.0, ini - t0), *r] for a, b, *r in wt
                    if b > ini - t0] if wt else None)
    if not ents:
        return False
    return fx_subtitles.burn_subtitles_ass(str(sem_leg), ents, str(saida), word_times=wts, offsets=offs)


def _volume(arq):
    """02/11 (revisão dos cortes do DshSnbY3y8s: -17,3 e -18,9 LUFS): o corte sai do vídeo ANTES do master do longo
    (que leva a -14), então ficava ~4 dB mais baixo que os outros Shorts. Só o áudio vai a -14 LUFS; vídeo copiado.
    Falhou = fica como estava."""
    import subprocess
    tmp = arq.with_name(arq.stem + "_vol.mp4")
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(arq), "-map", "0", "-c:v", "copy",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-movflags", "+faststart", str(tmp)], check=True, capture_output=True, timeout=300)
        if tmp.stat().st_size > 100_000:
            tmp.replace(arq)
    except Exception as e:  # noqa: BLE001 — volume é ajuste; nunca derruba o corte
        logging.warning(f"[cortes] volume não ajustado ({type(e).__name__}: {str(e)[:120]})")
        tmp.unlink(missing_ok=True)


def gerar(final_mp4, frases, inicios, workspace, pular=0, proibidas=(), word_times=None):
    """final_mp4 = vídeo SEM legenda quando word_times vem (02/11: o corte ganha legenda própria em pé); senão o final
    legendado (modo antigo: 16:9 encolhido no meio)."""
    cfg = _cfg()
    if not cfg.get("ligado") or not inicios or len(inicios) != len(frases):
        return []
    try:
        import subprocess
        dur_total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                          "csv=p=0", str(final_mp4)], capture_output=True, text=True,
                                         timeout=30).stdout.strip())
        trechos = sorted(escolher(frases, inicios, dur_total, cfg, pular, proibidas), key=lambda t: -t[5])
        from shorts_from_deitado import make_vertical_short
        pasta = Path(workspace) / "cortes_longo"
        pasta.mkdir(exist_ok=True)
        feitos, usados = [], []
        for a, b, gancho, titulo, motivo, nota in trechos:
            tempo = _ajustar(a, b, inicios, dur_total, cfg)
            if not tempo or any(tempo[0] < f and u < tempo[1] for u, f in usados):
                continue
            arq = pasta / f"corte_{len(feitos) + 1:02d}.mp4"
            ok = False
            if word_times is not None:  # 02/11: em pé SEM legenda -> legenda própria do formato em pé
                cru = pasta / f"_cru_{len(feitos) + 1:02d}.mp4"
                if make_vertical_short(final_mp4, tempo[0], tempo[1] - tempo[0], cru, cheio=True):
                    ok = _legendar_corte(cru, tempo[0], tempo[1], frases, inicios, word_times, arq)
                    cru.unlink(missing_ok=True)
                    # o corte grava marcas_visuais.json em cortes_longo/ e ao lado dele: não pode sobrescrever as do
                    # longo (que a prévia usa) — tira as do corte
                    for lixo in (arq.with_name("marcas_visuais.json"), arq.with_name(arq.stem + ".ass"),
                                 pasta / "cortes_longo"):
                        if lixo.is_dir():
                            shutil.rmtree(lixo, ignore_errors=True)
                        else:
                            lixo.unlink(missing_ok=True)
            else:
                ok = make_vertical_short(final_mp4, tempo[0], tempo[1] - tempo[0], arq)
            if ok:
                _volume(arq)
                usados.append(tempo)
                feitos.append({"arquivo": arq.name, "ini": round(tempo[0], 2), "fim": round(tempo[1], 2),
                               "dur": round(tempo[1] - tempo[0], 1), "frases": [a, b], "gancho": gancho,
                               "titulo": titulo, "motivo": motivo, "nota": nota})
            if len(feitos) >= cfg["max"]:
                break
        (pasta / "cortes.json").write_text(json.dumps(feitos, ensure_ascii=False, indent=1), encoding="utf-8")
        logging.info(f"[cortes] {len(feitos)} cortes pros canais de cortes: "
                     + " | ".join(f"{c['dur']:.0f}s nota {c['nota']:.0f} {c['gancho']}" for c in feitos))
        return feitos
    except Exception as e:  # noqa: BLE001 — corte é extra; nunca derruba o longo
        logging.warning(f"[cortes] não saíram ({type(e).__name__}: {e})")
        return []
