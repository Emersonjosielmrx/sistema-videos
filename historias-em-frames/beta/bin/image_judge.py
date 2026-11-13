# -*- coding: utf-8 -*-
"""image_judge.py — Multi-agente Gemini Vision pra selecionar melhores imagens.

Compara variações de uma cena e escolhe a melhor baseado em:
- Coerência com o prompt original
- Qualidade artística
- Consistência visual com imagens anteriores da mesma história
"""
import json
import base64
import time
import urllib.request
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import log

import gateway_cfg  # noqa: E402
OMNIROUTE_URL = gateway_cfg.url("/v1/chat/completions")
OMNIROUTE_KEY = gateway_cfg.bearer()  # secrets/omniroute.json
MODEL = "antigravity/gemini-2.5-flash-lite"


def _encode_image(path):
    """Converte imagem pra base64 data URL."""
    data = Path(path).read_bytes()
    return f"data:image/png;base64,{base64.b64encode(data).decode()}"


def judge_variations(variations, prompt, previous_finals=None):
    """Compara variações e retorna índice da melhor.

    Args:
        variations: list de Paths de imagens (variações da mesma cena)
        prompt: o prompt original usado pra gerar
        previous_finals: list de Paths de imagens já aprovadas (pra coerência)

    Returns:
        dict com {best_idx, scores, reasoning} ou None se falhar
    """
    valid = [(i, v) for i, v in enumerate(variations) if v and Path(v).exists() and Path(v).stat().st_size > 1000]

    if len(valid) == 0:
        return None
    if len(valid) == 1:
        return {"best_idx": valid[0][0], "scores": [100], "reasoning": "única variação disponível"}

    # Montar mensagem com imagens
    content_parts = []
    content_parts.append({
        "type": "text",
        "text": (
            f"Você é um diretor de arte avaliando imagens geradas por IA para um vídeo.\n\n"
            f"PROMPT ORIGINAL: {prompt}\n\n"
            f"Compare as {len(valid)} variações abaixo e escolha a MELHOR.\n"
            f"Critérios (em ordem de importância):\n"
            f"1. Coerência com o prompt (retrata o que foi pedido?)\n"
            f"2. Qualidade artística (composição, iluminação, detalhes)\n"
            f"3. Impacto visual (chamaria atenção num vídeo?)\n"
            f"4. Ausência de artefatos (mãos estranhas, texto ilegível, etc)\n\n"
            f"Responda APENAS em JSON:\n"
            f'{{"best_idx": N, "scores": [score1, score2, ...], "reasoning": "explicação curta"}}\n'
            f"Onde scores são 0-100 pra cada variação."
        ),
    })

    for i, (orig_idx, vpath) in enumerate(valid):
        content_parts.append({"type": "text", "text": f"\n--- Variação {i} (idx={orig_idx}) ---"})
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": _encode_image(vpath)},
        })

    # Se tem imagens anteriores, incluir pra coerência
    if previous_finals and len(previous_finals) > 0:
        last_final = previous_finals[-1]
        if last_final and Path(last_final).exists():
            content_parts.append({"type": "text", "text": "\n--- Referência (cena anterior aprovada, manter estilo similar) ---"})
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": _encode_image(last_final)},
            })

    try:
        body = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": content_parts}],
            "temperature": 0.3,
            "max_tokens": 512,
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            OMNIROUTE_URL, data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": OMNIROUTE_KEY,
            },
        )

        log(f"  image_judge: comparando {len(valid)} variações...")
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())

        content = data["choices"][0]["message"]["content"]
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        result = json.loads(content.strip())
        best = result.get("best_idx", valid[0][0])
        log(f"  image_judge: melhor = variação {best} (scores: {result.get('scores', [])})")
        return result

    except Exception as e:
        log(f"  image_judge: erro — {e}, usando primeira variação")
        return {"best_idx": valid[0][0], "scores": [], "reasoning": f"fallback (erro: {e})"}


def select_best_for_story(story_cache_dir, n_scenes, n_variations=3, prompts=None):
    """Percorre todas as cenas e seleciona a melhor variação de cada uma.

    Args:
        story_cache_dir: Path do diretório de cache da história
        n_scenes: número de cenas
        n_variations: variações por cena
        prompts: lista de prompts originais (1 por cena)

    Returns:
        list de Paths dos finais selecionados
    """
    import shutil
    finals = []

    for i in range(n_scenes):
        final_path = story_cache_dir / f"scene_{i:02d}_final.png"

        if final_path.exists() and final_path.stat().st_size > 1000:
            finals.append(final_path)
            continue

        # Coletar variações existentes
        variations = []
        for v in range(n_variations):
            vpath = story_cache_dir / f"scene_{i:02d}_v{v}.png"
            variations.append(vpath if vpath.exists() and vpath.stat().st_size > 1000 else None)

        valid_count = sum(1 for v in variations if v)
        if valid_count == 0:
            finals.append(None)
            continue

        if valid_count == 1:
            # Só uma — usa direto
            best_path = next(v for v in variations if v)
            shutil.copy2(best_path, final_path)
            finals.append(final_path)
            continue

        # Multi-agente: comparar
        prompt = prompts[i] if prompts and i < len(prompts) else ""
        result = judge_variations(variations, prompt, previous_finals=finals)

        if result:
            best_idx = result["best_idx"]
            best_path = story_cache_dir / f"scene_{i:02d}_v{best_idx}.png"
            if best_path.exists():
                shutil.copy2(best_path, final_path)
            else:
                best_path = next((v for v in variations if v), None)
                if best_path:
                    shutil.copy2(best_path, final_path)
        else:
            best_path = next((v for v in variations if v), None)
            if best_path:
                shutil.copy2(best_path, final_path)

        finals.append(final_path if final_path.exists() else None)

    ok = sum(1 for f in finals if f)
    log(f"  image_judge: {ok}/{n_scenes} cenas com imagem final selecionada")
    return finals
