# -*- coding: utf-8 -*-
"""story_writer.py — Gera roteiros estruturados por gênero via Gemini.

Output: JSON com título viral, tags, e lista de cenas (texto, image_prompt, persona, mood).
Usa character_bank pra manter coerência visual entre cenas.
Cache por hash do tema pra não regerar.
"""
import json
import hashlib
import os
import time
import urllib.request
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, STORIES_DIR, log
import character_bank

import gateway_cfg  # noqa: E402
OMNIROUTE_URL = gateway_cfg.url("/v1/chat/completions")
OMNIROUTE_KEY = gateway_cfg.bearer()  # secrets/omniroute.json
# Roteiro = 1 chamada por video e e a base de tudo: modelo forte primeiro, os leves
# de reserva (o flash-lite sozinho escrevia texto_na_imagem com erro, ex. "CHEFF").
# Override: STORY_MODEL=modelo (vai na frente da lista).
# (gemini-3.5-flash-high saiu: o gateway responde "no longer available")
MODELOS = ["antigravity/gemini-3.1-pro-high", "antigravity/gemini-2.5-flash",
           "antigravity/gemini-2.5-flash-lite"]
if os.environ.get("STORY_MODEL"):
    MODELOS.insert(0, os.environ["STORY_MODEL"])
MODEL = MODELOS[0]


def _find_bash():
    """Acha o bash.exe (Git Bash). Necessário porque quando o daemon roda via
    Tarefa Agendada do Windows, o PATH NÃO tem o Git — então 'bash' cru dá
    WinError 2 e mascara toda a produção. Procura caminhos conhecidos."""
    import shutil, os
    b = shutil.which("bash")
    if b:
        return b
    for c in (
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Git\bin\bash.exe"),
    ):
        if os.path.exists(c):
            return c
    return "bash"  # último recurso: deixa o subprocess falhar com msg clara

GENRE_PROMPTS = {
    "superacao": {
        "tom": "inspirador, emocionante, jornada do herói brasileiro",
        "estrutura": "início humilde → desafios → quase desistir → virada → conquista",
        "exemplo_titulo": "Ele dormia no chão e hoje opera corações",
    },
    "terror": {
        "tom": "tenso, atmosférico, suspense crescente, final impactante",
        "estrutura": "normalidade → primeiro sinal → tensão crescente → revelação → horror",
        "exemplo_titulo": "Nunca abra a porta do porão depois das 3",
    },
    "misterio": {
        "tom": "intrigante, cerebral, pistas sutis, revelação surpreendente",
        "estrutura": "crime/enigma → investigação → pistas falsas → insight → solução",
        "exemplo_titulo": "O caso que a polícia nunca resolveu",
    },
    "motivacional": {
        "tom": "poderoso, direto, frases de impacto, transformador",
        "estrutura": "situação comum → reflexão profunda → lição → chamada à ação",
        "exemplo_titulo": "As 5 verdades que ninguém te conta sobre sucesso",
    },
    "curiosidades": {
        "tom": "surpreendente, factual, ritmo rápido, wow-factor",
        "estrutura": "gancho → fato surpreendente → contexto → mais fatos → conclusão mind-blowing",
        "exemplo_titulo": "Seu cérebro faz isso toda noite e você não sabe",
    },
    "religioso": {
        "tom": "solene, esperançoso, narrativa bíblica adaptada, mensagem universal",
        "estrutura": "contexto histórico → personagem → provação → fé → recompensa divina",
        "exemplo_titulo": "O jovem que enfrentou um gigante com uma pedra",
    },
    "romance": {
        "tom": "envolvente, íntimo, química entre personagens, final emocional",
        "estrutura": "encontro → atração → obstáculo → separação → reencontro/resolução",
        "exemplo_titulo": "Ela jurou que nunca mais ia amar",
    },
    "comedia": {
        "tom": "leve, engraçado, timing cômico, situações absurdas",
        "estrutura": "normalidade → incidente cômico → escalada → caos → desfecho surpreendente",
        "exemplo_titulo": "O dia que ele confundiu a sogra com a uber",
    },
    "drama": {
        "tom": "profundo, reflexivo, conflitos humanos reais, catarse",
        "estrutura": "vida normal → ruptura → conflito interno → escolha difícil → consequência",
        "exemplo_titulo": "Ele perdeu tudo pra descobrir o que importa",
    },
    "fantasia": {
        "tom": "épico, mágico, mundo diferente, jornada heróica",
        "estrutura": "mundo fantástico → chamado → aliados → provação → batalha final",
        "exemplo_titulo": "O garoto que acordou com magia nas mãos",
    },
}


def _cache_path(genero, tema, n_cenas):
    h = hashlib.md5(f"{genero}:{tema}:{n_cenas}".encode()).hexdigest()[:12]
    d = STORIES_DIR / genero
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{h}.json"


def _build_system_prompt(genero, n_cenas, characters):
    """Monta o system prompt pro Gemini com contexto do gênero e personagens."""
    genre_info = GENRE_PROMPTS.get(genero, GENRE_PROMPTS["superacao"])

    char_block = ""
    if characters:
        char_block = "\n\nPERSONAGENS DISPONÍVEIS (use estes nos prompts de imagem para coerência visual):\n"
        for c in characters:
            char_block += f"- {c['id']} ({c['nome']}): {c['aparencia']}\n"

    return f"""Você é um roteirista de vídeos virais para YouTube Shorts/Reels em português brasileiro.

GÊNERO: {genero}
TOM: {genre_info['tom']}
ESTRUTURA NARRATIVA: {genre_info['estrutura']}
EXEMPLO DE TÍTULO VIRAL: {genre_info['exemplo_titulo']}
{char_block}
REGRAS:
1. Título VIRAL (máx 60 chars) — gatilho emocional, sem clickbait falso
2. Exatamente {n_cenas} cenas
3. Cada cena DEVE TER 1 persona clara e 1 texto.
4. INTERCALE: Narrador explica a situação, Personagens têm falas intensas em primeira pessoa (ex: "Não vou desistir!").
5. Prompts de imagem devem ser ESPECÍFICOS e CONSISTENTES (mesmos personagens/cenário entre cenas).
   Em TODO image_prompt em que o protagonista aparece, REPITA os traços físicos FIXOS dele
   (idade, cabelo, roupa e QUALQUER condição física: cadeira de rodas, muletas, prótese,
   cegueira, cicatriz). Cada imagem é gerada sozinha: se a cena final não disser "in his
   wheelchair", o personagem paraplégico aparece em pé.
6. Moods possíveis: tense_dramatic, sad_emotional, romantic_sexy, funny_lighthearted, calm_chill, neutral_chill
7. Personas disponíveis (use até 6):
   - "Narrador" — voz feminina suave, narra em terceira pessoa
   - "Protagonista" — personagem principal (M ou F conforme a história)
   - "Antagonista" — vilão/oponente
   - "Mentor" — guia/sábio/conselheiro
   - "Aliado" — amigo/parceiro do protagonista
   - "Coadjuvante" — personagem secundário
   NÃO invente nomes de persona — use apenas estes rótulos.
8. Campo OPCIONAL 'arquetipo_vocal' por cena — define TOM de voz:
   mentor, vilao, misterioso, jovem_heroi, jovem_heroina, comico, crianca, idoso, idosa, autoritario, sedutor, assustado, narrador_grave, narrador_empolgado
   Se omitido, a voz é escolhida pelo gênero automaticamente.
9. Campo OPCIONAL 'texto_na_imagem' — texto que APARECE NA IMAGEM (não narrado):
   Use APENAS quando narrativamente relevante. Tipos:
   - time_skip: "3 ANOS DEPOIS", "Na manhã seguinte"
   - mensagem: texto de celular/carta
   - placa: letreiro, aviso, manchete de jornal
   Máximo 3 palavras curtas (o gerador de imagem erra/corta texto longo); escreva com a
   ortografia correta. Quando presente, inclua no image_prompt: "image contains visible text
   reading: [o texto], centered, fully inside the frame"

RESPONDA APENAS em JSON válido com esta estrutura:
{{
  "titulo": "título viral aqui",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "cenas": [
    {{
      "texto": "texto falado em PT-BR (só a fala, sem aspas, sem nome do personagem antes)",
      "image_prompt": "detailed image prompt in English, include character description, setting, lighting, camera angle",
      "persona": "Narrador",
      "mood": "tense_dramatic",
      "arquetipo_vocal": "narrador_empolgado",
      "texto_na_imagem": null,
      "sfx_hint": "optional sound effect hint like 'thunder' or 'heartbeat'"
    }}
  ]
}}"""


def generate_story(genero="superacao", tema=None, n_cenas=10):
    """Gera roteiro completo. Retorna dict ou None se falhar."""
    cached = _cache_path(genero, tema or "random", n_cenas)
    if cached.exists():
        log(f"  story_writer: cache hit {cached.name}")
        return json.loads(cached.read_text(encoding="utf-8"))

    characters = character_bank.get_characters(genero)
    system_prompt = _build_system_prompt(genero, n_cenas, characters)

    user_msg = f"Crie uma história de {genero}"
    if tema:
        user_msg += f" sobre: {tema}"
    else:
        user_msg += " com tema original e criativo (invente algo único)"

    _ultimo_erro = None
    for _modelo in MODELOS:
        try:
            body = json.dumps({
                "model": _modelo,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.9,
                "max_tokens": 4096,
                "stream": False,
            }).encode()

            req = urllib.request.Request(
                OMNIROUTE_URL, data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": OMNIROUTE_KEY,
                },
            )

            log(f"  story_writer: gerando roteiro ({genero}, {n_cenas} cenas)...")
            # OMNIROUTE proxy bug: stdin via @- retorna 0 bytes.
            # curl 8.x do Git Bash com --data-raw inline funciona.
            # IMPORTANT: subprocess.run com lista usa curl.exe do Windows (antigo, bugado).
            # Solução: bash -c com --data-raw inline.
            import subprocess
            _body = json.dumps({
                "model": _modelo,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.9,
                "max_tokens": 4096,
            })
            # Sem espaços extras no JSON.
            _body_compact = json.dumps(json.loads(_body), separators=(",", ":"))
            # json.dumps NAO escapa aspa simples: um tema com apostrofo ("olho d'agua")
            # fecharia a string do shell. ' e JSON valido e nao quebra o bash.
            _body_compact = _body_compact.replace("'", "\\u0027")
            # Envolver em aspas simples para o shell.
            _cmd = (
                "curl -s -X POST " + OMNIROUTE_URL +
                ' -H \'Authorization: ' + OMNIROUTE_KEY + '\'' +
                ' -H \'Content-Type: application/json\'' +
                " --data-raw '" + _body_compact + "'" +
                ' --max-time 120'
            )
            # Nao logar o _cmd: ele carrega o header Authorization com a chave.
            log(f"  story_writer: POST {OMNIROUTE_URL} model={_modelo} body={len(_body_compact)}B")
            _proc = subprocess.run(
                [_find_bash(), "-c", _cmd],
                capture_output=True, text=True
            )
            raw = _proc.stdout
            log(f"  story_writer: curl len={len(raw)} rc={_proc.returncode} stderr={_proc.stderr[:200]}")
            if raw.startswith("data:"):
                content = ""
                for line in raw.splitlines():
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content += delta.get("content", "")
                    except Exception:
                        continue
                data = {"choices": [{"message": {"content": content}}]}
            else:
                data = json.loads(raw) if raw else {}

            content = data["choices"][0]["message"]["content"]
            # Limpar markdown code block se vier
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            story = json.loads(content.strip())

            if "cenas" not in story or len(story["cenas"]) < 2:
                log(f"  story_writer: roteiro incompleto (poucas cenas) com {_modelo} — tentando o proximo")
                continue

            story["genero"] = genero
            story["tema"] = tema
            story["_modelo"] = _modelo
            story["_generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

            cached.write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding="utf-8")
            log(f"  story_writer: OK — '{story['titulo']}' ({len(story['cenas'])} cenas)")
            return story

        except Exception as e:
            _ultimo_erro = e
            log(f"  story_writer: {_modelo} falhou ({str(e)[:120]}) — tentando o proximo")
            continue
    log(f"  story_writer: ERRO — todos os modelos falharam ({_ultimo_erro})")
    return None


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Gerador de roteiros por gênero")
    p.add_argument("--genero", default="superacao", choices=list(GENRE_PROMPTS.keys()))
    p.add_argument("--tema", default=None, help="Tema opcional (Gemini inventa se omitido)")
    p.add_argument("--n-cenas", type=int, default=10)
    args = p.parse_args()

    story = generate_story(args.genero, args.tema, args.n_cenas)
    if story:
        print(json.dumps(story, indent=2, ensure_ascii=False))
    else:
        print("FALHOU", file=sys.stderr)
        sys.exit(1)
