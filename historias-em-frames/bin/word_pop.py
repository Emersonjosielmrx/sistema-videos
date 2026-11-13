# -*- coding: utf-8 -*-
"""
Word Pop - Efeitos visuais para palavras-chave
Gera efeitos de popup para palavras fortes usando drawtext e overlay de progresso.
"""
import os
import sys
import re
from pathlib import Path

# Add bin/ to path to import hp_common
bin_dir = Path(__file__).resolve().parent
if str(bin_dir) not in sys.path:
    sys.path.insert(0, str(bin_dir))

import hp_common

# Configurações com fallback
WORD_POP_ENABLED = os.environ.get("WORD_POP", "1") == "1"
PROGRESS_BAR_ENABLED = os.environ.get("PROGRESS_BAR", "1") == "1"

# Fonte explícita pro drawtext. SEM isto o ffmpeg tenta o fontconfig, que está
# quebrado no build do Windows ("Cannot load default config file") e CRASHA
# (access violation) → o clip cai no fallback a 25fps e dessincroniza o concat.
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/impact.ttf",
    "C:/Windows/Fonts/ariblk.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _font_path():
    """Retorna o 1º .ttf existente (path escapado pro drawtext do ffmpeg)."""
    p = next((f for f in _FONT_CANDIDATES if Path(f).exists()), None)
    if not p:
        return None
    # ffmpeg drawtext no Windows precisa de : escapado no fontfile (C\:/...)
    return p.replace(":", "\\:")


_FONT = _font_path()
_FONTFILE = f"fontfile='{_FONT}':" if _FONT else ""

# Palavras de poder para destacar
POWER_WORDS = [
    "MORREU", "NUNCA", "SEGREDO", "MENTIRA", "TRAIU", 
    "DESTRUIU", "IMPOSSÍVEL", "PERIGO", "VERDADE", "SANGUE", 
    "MORTE", "CHOCANTE", "REVELOU", "JAMAIS", "NINGUÉM"
]

def detect_power_words(texto):
    """
    Detecta palavras de poder no texto.
    Retorna uma lista de tuplas com (palavra_encontrada, posicao_no_texto) ou apenas palavras.
    """
    if not texto:
        return []
        
    texto_upper = texto.upper()
    found_words = []
    
    # Busca por palavras inteiras para evitar falsos positivos
    for word in POWER_WORDS:
        # Regex para palavras inteiras (boundary)
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, texto_upper):
            found_words.append(word)
            
    return found_words

def build_word_pop_filter(word, start_time, duration=0.5):
    """
    Gera string do filtro drawtext para um popup de palavra.
    Efeito de scale-up e fade.
    """
    end_time = start_time + duration
    
    # Animação de tamanho usando a variável t (tempo)
    # fontsize cresce de 80 a 120 durante a duração
    # alpha faz fade in e in fade out
    
    # Math para o tamanho baseado no tempo: 
    # (t-start_time)/duration vai de 0 a 1
    # max(80, min(120, 80 + 40*((t-start_time)/duration)))
    fontsize_expr = f"80+40*(t-{start_time})/{duration}"
    
    # Math para alpha: peak no meio da duração
    # fade in nos primeiros 10%, fully visible 80%, fade out últimos 10%
    alpha_expr = f"if(lt(t,{start_time+duration*0.1}), (t-{start_time})/({duration*0.1}), if(gt(t,{end_time-duration*0.1}), ({end_time}-t)/({duration*0.1}), 1))"
    
    # drawtext parameters em um formato robusto
    # Usando fonte padrão e texto branco com borda preta grossa
    filter_string = (
        f"drawtext=text='{word}':"
        f"{_FONTFILE}"
        f"fontcolor=white:bordercolor=black:borderw=4:"
        f"fontsize='{fontsize_expr}':"
        f"alpha='{alpha_expr}':"
        f"x='(w-text_w)/2':y='(h-text_h)/2':" # Center on screen
        f"enable='between(t,{start_time},{end_time})'"
    )
    
    return filter_string

def build_progress_bar_filter(current_scene, total_scenes, start_time, end_time):
    """
    Gera string do filtro drawtext para mostrar progresso da cena atual.
    """
    text = f"{current_scene}/{total_scenes}"
    
    filter_string = (
        f"drawtext=text='{text}':"
        f"{_FONTFILE}"
        f"fontcolor=white:"
        f"fontsize=40:"
        f"box=1:boxcolor=black@0.5:boxborderw=10:" # Semi-transparent box
        f"x='w-text_w-30':y='30':" # Top right with margin
        f"enable='between(t,{start_time},{end_time})'"
    )
    
    return filter_string

def get_word_pop_filters(cenas, timestamps):
    """
    Recebe listas de cenas (texto) e seus tempos de início.
    Gera o filtro composto para adicionar os overlays.
    """
    if not cenas or not timestamps or len(cenas) != len(timestamps):
        hp_common.log("word_pop: listas inválidas ou de tamanhos diferentes.", level="warning")
        return ""
        
    filters = []
    total_scenes = len(cenas)
    
    # Calculamos end_times baseado no início da próxima (e damos 5s pra última)
    end_times = []
    for i in range(len(timestamps) - 1):
        end_times.append(timestamps[i+1])
    # Damos 5s pra última cena (uma estimativa)
    if timestamps:
        end_times.append(timestamps[-1] + 5.0)
        
    for i, (cena_texto, t_start, t_end) in enumerate(zip(cenas, timestamps, end_times)):
        current_scene = i + 1
        
        # 1. Adicionar Progress Bar se ativado
        if PROGRESS_BAR_ENABLED:
            prog_filter = build_progress_bar_filter(current_scene, total_scenes, t_start, t_end)
            filters.append(prog_filter)
            
        # 2. Adicionar Word Pops se ativado
        if WORD_POP_ENABLED and cena_texto:
            words = detect_power_words(cena_texto)
            
            # Espalhar na primeira metade da duração da cena pra não poluir
            # Se a cena dura 2s, e tem 2 palavras, eles aparecem nos primeiros 1s
            scene_duration = t_end - t_start
            
            for j, word in enumerate(words):
                # Calcular delay sequencial: primeira palavra no inicio, segunda um pouco depois
                pop_start = t_start + (j * 0.7) 
                
                # Só bota se couber na cena
                if pop_start < (t_end - 0.5):
                    pop_filter = build_word_pop_filter(word, pop_start)
                    filters.append(pop_filter)
                    
    # Join todos os drawtext filters com virgula (para mesma stream na chain do ffmpeg)
    if filters:
        hp_common.log(f"word_pop: Gerados {len(filters)} overlays de drawtext (incl. progresso e palavras mágicas)")
        return ",".join(filters)
        
    return ""
