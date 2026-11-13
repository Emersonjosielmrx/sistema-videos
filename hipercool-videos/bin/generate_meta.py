#!/usr/bin/env python3
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gemini_llm

def main():
    prompt = (
        "Gere metadados de vídeo para o recap do Capítulo 1 do manhwa/webtoon 'Moby Dick'.\n"
        "Gere um título super chamativo e dramático (clickbait saudável de recap de manhwa/webtoon) e uma descrição resumida contendo hashtags e tags apropriadas.\n"
        "Retorne APENAS um objeto JSON em formato string (sem markdown ou blocos de código ```json) com a seguinte estrutura exata:\n"
        '{\n'
        '  "title": "<TÍTULO CHAMATIVO EM PORTUGUÊS>",\n'
        '  "description": "<DESCRIÇÃO CURTA E ENVOLVENTE EM PORTUGUÊS COM #manhwa #recap #webtoon #mobydick>",\n'
        '  "tags": ["manhwa", "recap", "Moby Dick", "webtoon", "recap manhwa", "manhwa dublado"]\n'
        '}'
    )
    
    print("Chamando Gemini para gerar metadados de Moby Dick...")
    res = gemini_llm.generate_text(prompt, system="Você é um especialista em SEO de canais de recap de manhwa no YouTube no Brasil.", max_tokens=1000)
    
    if not res:
        print("Erro: Gemini retornou vazio.")
        sys.exit(1)
        
    res_clean = res.strip()
    if res_clean.startswith("```"):
        # Remove markdown wrapper
        lines = res_clean.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        res_clean = "\n".join(lines).strip()
        
    try:
        data = json.loads(res_clean)
    except Exception as e:
        print(f"Erro ao decodificar JSON gerado: {e}\nResposta: {res}")
        sys.exit(1)
        
    output = {
        "pt": data
    }
    
    out_path = Path("/Users/emerson-ia/Downloads/apps/postagem-videos/meta_pt.json")
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Metadados salvos em {out_path}!")

if __name__ == "__main__":
    main()
