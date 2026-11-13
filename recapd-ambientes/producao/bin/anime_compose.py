"""anime_compose.py — Lógica de composição visual (layout) pra formatos derivados.

Especialmente o formato SHORT (9:16), que em vez de um zoom simples (cover/crop
que destrói a visão do anime 16:9), faz composições criativas 
(ex: fundo borrado + vídeo inteiro no meio).
"""

def get_vertical_filtergraph(in_pad, out_pad, out_w=720, out_h=1280):
    """
    Recebe o stream `in_pad` (já descaracterizado), faz split para fundo e frente,
    aplica blur pesado no fundo (cover 9:16) e coloca o vídeo inteiro no centro (16:9 escalado).
    Devolve a string de filtergraph e a stream de saída em `out_pad`.
    """
    # Ex: in_pad="[descaracterizado]", out_pad="[vout]"
    # fps=30 pra precaver que scale/gblur não dessincronizem a VFR
    
    graph = (
        f"{in_pad}split=2[bg][fg];"
        
        # O Fundo (bg) sofre scale increase (cover inteiro 9:16), crop pro meio, blur pesado
        f"[bg]scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
        f"crop={out_w}:{out_h},gblur=sigma=15,"
        f"eq=brightness=-0.1:saturation=1.2[bg_blur];"
        
        # A Frente (fg) sofre decrease (16:9, sem perder nada), padda para 9:16 transparente ou usa como overlay. 
        # Vamos padronizar em overlay: scale para out_w de lagura, height proporcional (out_w*9/16=405 se fonte 16:9)
        f"[fg]scale={out_w}:-1[fg_scaled];"
        
        # Overlay do fg sobre o bg_blur perfeitamente centralizado vertical/horizontal
        f"[bg_blur][fg_scaled]overlay=x=(W-w)/2:y=(H-h)/2{out_pad}"
    )
    return graph
