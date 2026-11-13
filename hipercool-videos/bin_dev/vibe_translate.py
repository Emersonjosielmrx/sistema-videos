#!/usr/bin/env python
"""vibe_translate.py - Traduz um texto curto pro portugues do Brasil via Gemini.

Uso:  python vibe_translate.py "texto em ingles"
Saida: a traducao em pt-BR no stdout (so o texto).
Usado pra narrar perguntas de multipla escolha do Claude Code que vem em ingles.
"""
import sys
import os

BIN = r"D:\hipercool-videos\bin"
if BIN not in sys.path:
    sys.path.insert(0, BIN)
os.chdir(r"D:\hipercool-videos")

def main():
    if len(sys.argv) < 2:
        print("", end=""); return 1
    txt = sys.argv[1].strip()
    if not txt:
        print("", end=""); return 0
    try:
        import gemini_llm
        prompt = ("Traduza para portugues do Brasil, de forma natural e curta. "
                  "Responda SOMENTE com a traducao, sem aspas, sem comentarios. "
                  f"Texto: {txt}")
        out = gemini_llm.generate_text(prompt, max_tokens=512, temperature=0.3)
    except Exception as e:
        sys.stderr.write(f"erro: {e}\n")
        print("", end=""); return 1
    if out:
        sys.stdout.write(out.strip().strip('"').strip())
    return 0

if __name__ == "__main__":
    sys.exit(main())
