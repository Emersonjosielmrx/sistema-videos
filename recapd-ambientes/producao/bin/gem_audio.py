#!/usr/bin/env python3
"""Manda arquivos de audio pro Gemini ouvir e dizer se sao protegidos por copyright.

Uso: python gem_audio.py <arq1.mp3> <arq2.mp3> ...
"""
import sys, base64, os
sys.path.insert(0, "bin")
import gemini_llm

PROMPT = (
    "Ouca este trecho de musica e identifique se e uma obra PROTEGIDA por direitos "
    "autorais (OST de anime/jogo/filme, musica comercial de artista) ou se e trilha "
    "livre/royalty-free. Se reconhecer a obra, diga nome e origem. Responda SO JSON: "
    '{"protegida":"sim|nao|incerto","nome":"","origem":"","motivo":"",'
    '"confianca":"baixa|media|alta"}'
)


def main():
    for path in sys.argv[1:]:
        name = os.path.basename(path)
        try:
            b64 = base64.b64encode(open(path, "rb").read()).decode()
            parts = [
                {"text": PROMPT},
                {"inline_data": {"mime_type": "audio/mp3", "data": b64}},
            ]
            r = gemini_llm._call(parts, temperature=0.2, max_tokens=400)
            print(f"### {name}\n{(r or '(sem resposta)').strip()}\n")
        except Exception as e:
            print(f"### {name}\nERRO: {e}\n")


if __name__ == "__main__":
    main()
