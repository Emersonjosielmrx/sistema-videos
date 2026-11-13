import asyncio
import os

import httpx


ANTHROPIC_BASE_URL = os.environ.get("FLUXIA_AI_URL", "http://157.173.207.22:20128").rstrip("/")
# 07/11: o Antigravity (agy/antigravity, e o kr/haiku-fila que cai nele) passou a devolver 200 com o texto
# "This version of Antigravity is no longer supported..." e o bot mandou isso aos clientes.
# 08/11 (dono: "tem que funcionar tudo com Gemini"): Gemini do AI Studio (gemini/, chaves próprias no OmniRoute).
# 09/11: 3.5 Flash Lite e 2.5 Flash Lite respondem em 1,5-3 s (texto, imagem e áudio); os Flash completos 3.5/3.6/3.8
# do AI Studio não respondem em 30 s (502 em cada chave e o OmniRoute rodando as 72). Antes: o 2.5 Flash Lite respondia em 2-5 s com texto, imagem e áudio; o 2.5 Flash ficou sem cota (429 billing)
# e os 3.x do AI Studio levavam 100+ s. agy/ na reserva: volta sozinho quando o Antigravity voltar.
DEFAULT_MODEL = os.environ.get("FLUXIA_MODEL", "gemini/gemini-3.5-flash-lite")
VISION_MODEL = os.environ.get("FLUXIA_VISION_MODEL", "gemini/gemini-3.5-flash-lite")
SMART_MODEL = os.environ.get("FLUXIA_SMART_MODEL", DEFAULT_MODEL)

# Texto que um provedor devolve como se fosse resposta, mas é aviso de erro: nunca vai para o cliente.
BAD_REPLY_MARKERS = ("antigravity is no longer supported", "please download and install the latest",
                     "no longer supported", "rate limit", "quota exceeded", "you have reached the limit",
                     "internal server error", "an error occurred", "api key", "unauthorized")


def is_bad_reply(text: str) -> bool:
    low = (text or "").lower()
    return any(m in low for m in BAD_REPLY_MARKERS)


async def ask_agent(
    system_prompt: str,
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    timeout: float = 60,
) -> str:
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "not-needed-for-proxy",
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": model or DEFAULT_MODEL,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{ANTHROPIC_BASE_URL}/v1/messages", headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()


FALLBACK_MODELS = [m.strip() for m in os.environ.get(
    "FLUXIA_FALLBACK_MODELS",
    # 09/11 (dono): o 3.5 Lite às vezes fica lento -> o 2.5 Flash Lite é a 1ª reserva, logo depois do principal.
    "gemini/gemini-2.5-flash-lite,gemini/gemini-3.5-flash-lite,agy/gemini-3.8-flash-high,gemini/gemini-2.5-flash,"
    "cw/claude-sonnet-5-5").split(",") if m.strip()]
RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 529}
# Prazo por modelo: o cliente não pode esperar. O Lite responde em 1-3 s (texto) e até ~10 s com imagem/áudio longo.
FIRST_TIMEOUT = float(os.environ.get("FLUXIA_FIRST_TIMEOUT", "15"))
FALLBACK_TIMEOUT = float(os.environ.get("FLUXIA_FALLBACK_TIMEOUT", "15"))


async def ask_with_fallback(system_prompt: str, messages: list[dict], model: str, max_tokens: int = 1024,
                            timeout: float = 60) -> tuple[str, str, list[str]]:
    """Tenta o modelo do fluxo e depois as reservas, com prazo curto em cada um. Devolve (texto, modelo, falhas).
    Lento ou travado = passa direto para o próximo (sem repetir); só repete o MESMO modelo em erro rápido (429/5xx)."""
    chain = [model] + [m for m in FALLBACK_MODELS if m != model]
    failures: list[str] = []
    for i, m in enumerate(chain):
        # com imagem (o engine passa 90 s) só o principal ganha +10 s; as reservas ficam curtas para não somar espera
        extra = 10 if timeout > 60 and i == 0 else 0
        limit = min(timeout, (FIRST_TIMEOUT if i == 0 else FALLBACK_TIMEOUT) + extra)
        for attempt in range(2):
            try:
                text = await ask_agent(system_prompt, messages, model=m, max_tokens=max_tokens, timeout=limit)
                if text and is_bad_reply(text):
                    failures.append(f"{m}: devolveu aviso de erro ({text[:60]})")
                    break
                if text:
                    return text, m, failures
                failures.append(f"{m}: resposta vazia")
                break
            except httpx.HTTPStatusError as e:
                failures.append(f"{m}: {e.response.status_code}")
                if e.response.status_code not in RETRY_STATUS:
                    break
            except httpx.TimeoutException:
                failures.append(f"{m}: demorou mais de {limit:.0f} s")
                break  # lento: não insiste, vai para a reserva
            except httpx.TransportError as e:
                failures.append(f"{m}: {type(e).__name__}")
            if attempt == 0:
                await asyncio.sleep(1)
    raise RuntimeError("todos os modelos falharam: " + "; ".join(failures))


def format_menu_for_prompt(categories: list[dict]) -> str:
    lines = []
    for cat in categories:
        lines.append(f"\n📋 {cat['name']}")
        for item in cat.get("items", []):
            price = f"R$ {item['price']:.2f}".replace(".", ",")
            desc = f" — {item['description']}" if item.get("description") else ""
            lines.append(f"  • {item['name']}: {price}{desc}")
    return "\n".join(lines)
