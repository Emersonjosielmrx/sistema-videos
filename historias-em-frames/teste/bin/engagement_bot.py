# -*- coding: utf-8 -*-
"""
Módulo de Engajamento para YouTube.
Gera textos de repostagem, cross-promo e comunidade baseados no gênero.
Obs: Não faz chamadas de API reais (evita expiração de OAuth), apenas gera o conteúdo.
"""
import os
import sys
import json
import hashlib
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hp_common import PROJECT_DIR, log
except ImportError:
    # Fallback if run standalone
    PROJECT_DIR = Path(__file__).resolve().parent.parent
    def log(msg, level="INFO"):
        print(f"[{level}] {msg}")

# Constantes e Env Vars
AUTO_REPLY = int(os.environ.get("AUTO_REPLY", "0"))
CROSS_PROMO = int(os.environ.get("CROSS_PROMO", "1"))

REPLY_TEMPLATES = {
    "superacao": ["Obrigado! Sua historia tambem e de superacao!", "Cada dia e uma chance nova", "Voce e mais forte do que pensa"],
    "terror": ["Dorme com a luz acesa hoje hein", "Parte 2 vem com mais medo...", "Nao olha atras de voce..."],
    "misterio": ["Acertou o culpado?", "Tem uma pista escondida nesse video...", "O proximo caso e ainda mais bizarro"],
    "romance": ["Quem chorou levanta a mao", "O amor e complicado ne?", "Parte 2 ta no forno!"],
    "comedia": ["KKKKK aconteceu comigo", "Ri demais editando esse", "Marca aquele amigo que faria isso"],
    "motivacional": ["Vai dar certo! Acredita!", "Anota essa frase!", "Comenta seu objetivo aqui"],
    "drama": ["Forte demais essa historia", "Voce faria diferente?", "A vida e assim mesmo..."],
    "fantasia": ["Qual poder voce escolheria?", "Esse mundo merece uma serie!", "Parte 2 confirmada!"],
    "religioso": ["Amem!", "Deus e fiel!", "Compartilha com quem precisa ouvir"],
    "curiosidades": ["Eu nao sabia disso!", "Qual fato mais te surpreendeu?", "Comenta um fato curioso"]
}

def _get_hash_index(text: str, max_val: int) -> int:
    """Retorna um índice determinístico baseado no texto."""
    if not text:
        return 0
    h = hashlib.md5(text.encode('utf-8')).hexdigest()
    return int(h, 16) % max_val

def get_reply(genero: str, comment_text: str = "") -> str:
    """Seleciona uma resposta contextual baseada no gênero e texto do comentário."""
    genero = genero.lower().strip()
    templates = REPLY_TEMPLATES.get(genero)
    
    if not templates:
        # Fallback genérico se o gênero não estiver mapeado
        templates = ["Obrigado pelo comentário!", "Valeu por assistir!", "Não esquece do like!"]
        
    idx = _get_hash_index(comment_text, len(templates))
    return templates[idx]

def generate_cross_promo(current_video_id: str, genero: str, max_links: int = 3) -> list:
    """Busca outros vídeos do mesmo gênero no workspace para cross-promotion."""
    if not CROSS_PROMO:
        return []
        
    genero = genero.lower().strip()
    videos_dir = PROJECT_DIR / "workspace" / "videos"
    
    related_videos = []
    
    if not videos_dir.exists():
        log("Diretório workspace/videos não encontrado.", "WARNING")
        return related_videos
        
    for video_folder in videos_dir.iterdir():
        if not video_folder.is_dir() or video_folder.name == current_video_id:
            continue
            
        meta_file = video_folder / "_meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    
                v_genero = meta.get("genero", "").lower().strip()
                if v_genero == genero:
                    related_videos.append({
                        "id": video_folder.name,
                        "titulo": meta.get("titulo", video_folder.name),
                        "path": str(video_folder)
                    })
            except Exception as e:
                log(f"Erro ao ler meta de {video_folder.name}: {e}", "ERROR")
                
    # Sort determinístico para as recomendações não mudarem toda hora
    related_videos.sort(key=lambda x: x["id"], reverse=True)
    return related_videos[:max_links]

def generate_description_links(videos_same_genre: list) -> str:
    """Formata a seção de links para a descrição do YouTube."""
    if not videos_same_genre:
        return ""
        
    linhas = ["\n👇 MAIS VÍDEOS QUE VOCÊ VAI GOSTAR 👇\n"]
    for v in videos_same_genre:
        # Nota: Idealmente os URLs viriam do banco se já postados,
        # como geramos pré-postagem, fica como placeholder para o n8n preencher
        linhas.append(f"📺 {v['titulo']} - (Insira o Link Aqui)")
        
    return "\n".join(linhas)

def generate_community_post(genero: str, story_title: str, cenas: list = None) -> dict:
    """Gera conteúdo para aba Comunidade do YouTube."""
    genero = genero.lower().strip()
    
    # Texto base
    textos = {
        "terror": f"Vocês teriam coragem de passar por isso? 😱 Saiu nova história de terror: '{story_title}'!",
        "romance": f"Aquele romance que mexe com o coração... ❤️ Já assistiu '{story_title}'?",
        "superacao": f"Não desista! A história '{story_title}' vai te inspirar hoje. 💪",
        "misterio": f"O final de '{story_title}' vai explodir sua cabeça! 🤯 Descobriu o segredo?",
        "comedia": f"Marque aquele amigo que é exatamente assim! 😂 Novo vídeo: '{story_title}'",
    }
    texto_teaser = textos.get(genero, f"Novo vídeo no canal! Confere lá: '{story_title}' 🎥")
    
    # Enquete
    polls = {
        "misterio": {"question": "Quem você acha que é o culpado antes do final?", "options": ["O vizinho", "A esposa", "O detetive", "Tava na cara o tempo todo!"]},
        "romance": {"question": "Você perdoaria?", "options": ["Sim, amor acima de tudo", "Depende...", "Nunca!", "Vou assistir pra decidir"]},
        "terror": {"question": "O que você faria no lugar dele?", "options": ["Corria muito!", "Lutava", "Ficava paralisado", "Trancava a porta e chorava"]},
    }
    
    poll = polls.get(genero)
    
    # Escolha de imagem da cena p/ thumbnail do post (geralmente uma do meio)
    image_hint = cenas[len(cenas)//2]['img_path'] if cenas and len(cenas) > 0 else "Escolha uma miniatura chamativa do vídeo."
    
    return {
        "text": texto_teaser,
        "poll": poll,
        "image_hint": image_hint
    }

if __name__ == "__main__":
    print(f"AUTO_REPLY: {AUTO_REPLY}")
    print(f"CROSS_PROMO: {CROSS_PROMO}")
    
    teste_gen = "terror"
    print(f"\n--- Teste ({teste_gen}) ---")
    print("Reply:", get_reply(teste_gen, "Nossa que medo"))
    print("Post:", generate_community_post(teste_gen, "O Fantasma da Meia Noite"))
