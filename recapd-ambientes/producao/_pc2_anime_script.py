"""anime_script.py — transforma a transcrição crua num roteiro PT-BR próprio.

Módulo isolado. Pega o texto CRU da transcrição (qualquer língua, longo) e
produz um roteiro de narração em PT-BR:
  - REESCRITO com voz própria (não é tradução literal do recap alheio).
  - CONDENSADO (o recap nosso é bem mais curto que o original).
  - 1 frase por linha (cada linha vira um clipe/narração no pipeline).
  - PROTECAO ANTI-BAN: termos que dao strike no YouTube sao suavizados
    (viralizador.anti_ban). Gírias virais opcionais via VIRAL_SLANG=1.

Usa claude_client.generate_text (o proxy/gateway já configurado no projeto).
Processa a transcrição em BLOCOS pra não estourar o contexto do modelo.
"""
import logging
import os
import re
import sys
from pathlib import Path

# viralizador.py vive no mesmo diretório — garante que o import funcione
sys.path.insert(0, str(Path(__file__).resolve().parent))

import claude_client
import viralizador

_SYSTEM = (
    "Você é roteirista de um canal brasileiro de conteúdo animado. Recebe a "
    "transcrição CRUA (possivelmente em outra língua) de um vídeo animado já "
    "existente e reescreve com VOZ PRÓPRIA e ORIGINAL em português brasileiro — "
    "NUNCA traduz literalmente nem copia a narração alheia. Conte a história de "
    "forma envolvente, condensada e clara. Frases curtas e faladas (para narração "
    "em voz alta), uma ideia por frase. Não invente fatos que não estão na "
    "transcrição.\n\n"
    "REGRAS DE CONTEÚDO E FORMATAÇÃO (VIOLAÇÃO GERA FALHA CRÍTICA):\n"
    "1. NÃO use marcações teatrais, colchetes, parênteses ou nomes de personagens como título (Ex: não use 'Narrador:', '[Música]', '(Suspense)').\n"
    "2. NÃO faça introduções nem se despeça (NÃO DIGA 'Aqui está o roteiro', nem termine com 'Espero ter ajudado'). Vá DIRETO para a primeira frase da história.\n"
    "3. Retorne APENAS AS FRASES da história, limpas, uma por linha.\n\n"
    "ATENÇÃO MÁXIMA: Se a transcrição for apenas ruídos sem sentido, "
    "sons soltos sem palavras (ex: só música com risadas), ou texto totalment "
    "incompreensível (mais de 80% caracteres ilegíveis), "
    "você DEVE responder EXATAMENTE a palavra: [ERRO: LIXO], e abortar o roteiro."
)


def _split_blocks(text, block_chars=6000):
    """Divide o texto cru em blocos de ~block_chars, cortando em fim de frase."""
    text = re.sub(r"\s+", " ", text).strip()
    blocks, start = [], 0
    while start < len(text):
        end = min(start + block_chars, len(text))
        if end < len(text):
            dot = text.rfind(". ", start, end)
            if dot > start:
                end = dot + 1
        blocks.append(text[start:end].strip())
        start = end
    return blocks


def _clean_lines(raw):
    """Quebra a resposta do modelo em frases-linha limpas."""
    out = []
    for ln in raw.splitlines():
        s = ln.strip()
        s = re.sub(r"^[\-\*\d\.\)\s]+", "", s)      # bullets/numeração
        s = s.strip(' "\'')
        if len(s) >= 8:
            out.append(s)
    return out


def rewrite(transcript, target_lines=40):
    """Reescreve a transcrição num roteiro PT-BR (lista de frases).

    target_lines: nº aproximado de frases no roteiro final (controla a duração).
    Retorna [str]. Lista vazia se a IA não estiver disponível ou a transcrição for inválida.
    """
    if len(re.sub(r'[^a-zA-ZáéíóúãõçÁÉÍÓÚÃÕÇ]', '', transcript)) < 50:
        logging.error("[script] transcrição parece vazia ou sem texto real (só ruído/símbolos). Abortando.")
        return []

    if not claude_client.is_available():
        logging.error("[script] claude_client indisponível — sem reescrita")
        return []

    blocks = _split_blocks(transcript)
    per_block = max(3, round(target_lines / max(1, len(blocks))))
    logging.info(f"[script] {len(blocks)} blocos, ~{per_block} frases/bloco (target_lines={target_lines})")

    roteiro = []
    for i, blk in enumerate(blocks):
        prompt = (
            f"Trecho {i+1}/{len(blocks)} da transcrição de um recap de anime.\n"
            f"Reescreva com voz própria em PT-BR mantendo FIDELIDADE ao trecho — "
            f"narrando todos os fatos, diálogos e momentos relevantes. "
            f"Produza aproximadamente {per_block} frases curtas de narração (uma por linha), "
            f"sendo o mais completo possível dentro desse espaço: NÃO condense demais, "
            f"NÃO pule diálogos importantes, NÃO resuma em uma frase algo que pede mais.\n\n{blk}"
        )
        try:
            resp = claude_client.generate_text(prompt, system=_SYSTEM,
                                               max_tokens=1200, temperature=0.6)
        except Exception as e:
            logging.error(f"[script] bloco {i} falhou: {e}")
            continue
        if resp:
            # Proteção contra recusas quando o texto cru é lixo (sem voz/música apenas)
            resp_lower = resp.lower()
            if "[erro: lixo]" in resp_lower or ("transcrição" in resp_lower and ("incompleta" in resp_lower or "ruído" in resp_lower or "por favor" in resp_lower or "esqueceu" in resp_lower)):
                logging.warning(f"[script] A IA recusou o bloco {i} pois parece ruído/incompleto. Pulando...")
                continue

            # Filtro adicional de segurança: remover linhas que começam parecendo fillers
            clean_lines = _clean_lines(resp)
            final_lines = []
            for line in clean_lines:
                ll = line.lower()
                if ll.startswith("aqui está") or ll.startswith("aqui vai") or ll.startswith("espero que goste") or ll.startswith("claro"):
                    continue # Descarta fillers de conversação da IA
                if line.endswith(":") and len(line.split()) < 5:
                    continue # Descarta indicações como "Narrador:", "Cena 1:"
                final_lines.append(line)

            roteiro.extend(final_lines)

    if not roteiro:
        return []

    logging.info(f"[script] roteiro final: {len(roteiro)} frases (target_lines={target_lines})")

    # ── Protecao anti-ban (anti-strike YouTube) + viralizacao opcional ──
    roteiro = [viralizador.anti_ban(linha) for linha in roteiro]
    if os.environ.get("VIRAL_SLANG") == "1":
        roteiro = [viralizador.viralizar(linha) for linha in roteiro]
    return roteiro


def rewrite_to_file(transcript, out_txt, target_lines=40):
    """Reescreve e salva o roteiro (uma frase por linha). Retorna nº de frases."""
    linhas = rewrite(transcript, target_lines=target_lines)
    if not linhas:
        return 0
    from pathlib import Path
    Path(out_txt).write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return len(linhas)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    src = sys.argv[1]           # arquivo com a transcrição crua
    out = sys.argv[2] if len(sys.argv) > 2 else "roteiro.txt"
    from pathlib import Path
    n = rewrite_to_file(Path(src).read_text(encoding="utf-8"), out)
    print(f"{n} frases → {out}")
