"""claude_fallback.py — Wrapper temporário pra usar Gemini quando gateway OmniRoute tá down.

Quando OMNIROUTE_BYPASS=1, usa gemini_llm.py direto ao invés do gateway.
Substitui claude_client.generate_text() de forma transparente.
"""
import os
import claude_client as _original_claude
import gemini_llm

_bypass_enabled = os.environ.get("OMNIROUTE_BYPASS") == "1"

def is_available():
    """Sempre retorna True no modo bypass (usa Gemini como fallback)."""
    if _bypass_enabled:
        return True
    return _original_claude.is_available()

def generate_text(prompt, system=None, max_tokens=2048, temperature=0.4, model=None, timeout=90):
    """Se bypass ativado, usa Gemini. Senão, tenta gateway OmniRoute normal."""
    if _bypass_enabled:
        # Usa Gemini direto via gemini_llm.py
        try:
            result = gemini_llm.generate_text(
                prompt,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return result
        except Exception as e:
            print(f"  [fallback] Gemini error: {e}")
            return None

    # Modo normal: tenta gateway OmniRoute
    return _original_claude.generate_text(
        prompt,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
        model=model,
        timeout=timeout
    )

def fast_model():
    if _bypass_enabled:
        return "gemini-2.0-flash-thinking"
    return _original_claude.fast_model()

def strong_model():
    if _bypass_enabled:
        return "gemini-2.5-flash"
    return _original_claude.strong_model()
