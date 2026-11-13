# -*- coding: utf-8 -*-
"""capa_ia.py — capa 16:9 REDESENHADA no estilo das capas que mais clicam no nicho (O Porão da Cidadela / "Manhwa
Recap": arte limpa e colorida, ELA EM CIMA DELE ou harém em volta dele, roupa muito sensual mas cobrindo, balões).

Poses em RODÍZIO (catálogo POSES, pedido do dono em 15/10): cada capítulo sai com n variantes de poses diferentes,
escolhidas por amostragem de Thompson sobre as vitórias no teste A/B do Studio (workspace/capas_poses.json) — pose
que ganha aparece mais, as outras continuam sendo testadas. Sentada no colo e abraço só com 2+ mulheres.

Dois layouts: "texto" (frase grande à esquerda + balão branco com a fala dela) e "baloes" (fala dela + reação dele em
amarelo, apontando pro rosto de cada um — como as referências). Rostos localizados pela visão do Gemini, que também
reprova a imagem com nudez, mosaico, ato sexual ou cara de menor (o limite: perto da linha, sem cruzar).

O PLANO (poses + cenas) fica salvo por capítulo: as outras línguas reaproveitam as mesmas imagens (cache por prompt) e
só traduzem as falas. Ao lado da capa vai <nome>.capa.json com a pose/layout de cada variante (pro teste A/B).

Gera pelo gateway OmniRoute (antigravity/gemini-3.1-flash-image: só texto -> imagem; aparência dos personagens em
config/capas.json). Desligado por hora (dono 20/10, imagem_reserva.GATEWAY): vai direto pra reserva.

  python bin/capa_ia.py --obra the-inheritor --selo "CAP. 7" --saida X.capa.jpg --narracao cache.json [--n 3]
"""
import argparse
import base64
import hashlib
import json
import random
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log  # noqa: E402
import visao_capa  # noqa: E402  (COMUM: defeitos de corpo/pose + visão com reserva)

CFG = PROJECT_DIR / "config" / "capas.json"
CACHE = PROJECT_DIR / "workspace" / "cache" / "capa_ia"
CHK_DIR = CACHE / "checagem"
STATS = PROJECT_DIR / "workspace" / "capas_poses.json"
MODELO = "antigravity/gemini-3.1-flash-image"
W, H = 1280, 720

# catálogo (dono, 15/10 — referências em config/capas_referencia/): "min" = mínimo de mulheres na cena. Aprovadas na
# 1ª rodada: harem_cama e montada_peito. Fora (já testadas nas capas antigas): ela sozinha em cima/de quatro/no colo.
POSES = {
    "pernas_pescoco_chao": (1, "he sits on the floor; she sits on the edge of the bed behind him and wraps her long "
                               "legs around his NECK from behind, thighs on both sides of his head, ankles crossed on "
                               "his chest, leaning forward over his head with a teasing grin; he panics and blushes, "
                               "face toward the viewer (comedic); exactly one man"),
    "pernas_pescoco_deitada": (1, "she lies on her back on the bed and locks her raised legs around his NECK in a "
                                  "playful leg-lock, he kneels at the edge of the bed trapped between her thighs, "
                                  "his head turned to the viewer, panicking and red-faced (comedic wrestling hold); "
                                  "she laughs teasingly; exactly one man"),
    "pernas_pescoco_lado": (1, "both lie on the floor; she lies on her side and squeezes his NECK between her thighs "
                               "in a comedic leg scissor hold, he taps the floor in panic, blushing; she smirks "
                               "confidently at the viewer; exactly one man"),
    "montada_peito": (1, "he lies on his back on the floor, she kneels over him straddling his chest, hands on his "
                         "chest, leaning down over his face with a dominant teasing grin; he is shocked and sweating"),
    "montada_costas": (1, "he lies face-down on the floor, she sits on his back with her legs spread over his "
                          "shoulders, elbows on her knees, smug playful smile at the viewer; he looks up panicking"),
    "colo_harem": (2, "she sits facing him on his lap with her arms around his neck, while another woman hugs him from "
                      "behind pressing against his back and a third clings to his arm; he is overwhelmed and blushing"),
    "harem_cama": (3, "three women surround him on a big bed: one lies on top of his chest, one hugs his arm, one leans "
                      "on his shoulder from behind, all with seductive smiles; he sits in the middle sweating"),
    "harem_um_em_cima": (3, "he lies on his back on a big bed, she lies on top of him chin on his chest smiling, while "
                            "two other women lie on each side of him hugging his arms and smiling seductively; he "
                            "sweats, overwhelmed"),
    "harem_disputa": (3, "two women pull him by the arms in opposite directions, pressing against him and glaring at "
                         "each other jealously, while she sits on his lap smiling; he is panicking (comedic)"),
    "rosto": (1, "extreme close-up of HER face and bare shoulders filling most of the frame, mouth wide OPEN with her "
                 "tongue sticking far out, flushed red cheeks, sweat drops, eyes looking straight at the viewer, one "
                 "hand pulling her strap down off her shoulder; HIM small in the background, shocked"),
}
# "poses de fantasia" (dono, 15/10): obra de fantasia/ação ganha 1 variante de batalha no teste A/B — alternativa pra
# atrair outro público, sem largar as sensuais. (gêneros que liberam, descrição). Gêneros da obra: config/fila.json
# obras[].generos (as mesmas chaves de config/seo_palavras.json).
POSES_GENERO = {
    "batalha_espada": ({"fantasia", "acao", "murim", "apocalipse", "realeza", "regressao", "reencarnacao"},
                       "HE swings a glowing sword in a dynamic mid-air action pose, a huge energy slash trail cutting "
                       "across the frame, debris and sparks flying, fierce determined expression; epic battle"),
    "contra_monstro": ({"fantasia", "acao", "apocalipse", "sistema"},
                       "HE stands small in the foreground ready to strike while a gigantic monster towers over him, "
                       "dramatic scale contrast, glowing eyes in the dark, wind and dust; epic battle"),
    "magia": ({"fantasia", "reencarnacao", "realeza"},
              "HE casts an enormous glowing magic spell, swirling runes and light around his raised hand, his hair "
              "and coat blown by the energy, confident smirk"),
    "duelo": ({"murim", "acao", "fantasia", "realeza", "regressao"},
              "HE and a rival clash blades in mid-air, sparks exploding between the swords, intense eye contact, "
              "speed lines"),
    "despertar": ({"sistema", "acao", "apocalipse", "regressao", "selado", "genio"},
                  "HE awakens a massive power aura, glowing eyes, cracks in the ground, blank glowing game-like "
                  "window panels (no text) floating around him"),
    "dupla_batalha": ({"fantasia", "acao", "apocalipse", "murim"},
                      "SHE and HE fight back to back surrounded by enemies, she in revealing fantasy battle armor "
                      "with bare shoulders and a short skirt, both with weapons drawn, confident grins"),
}
ROUPAS_BATALHA = ["revealing fantasy battle armor with bare shoulders and a short skirt",
                  "tight black combat bodysuit with a belt of daggers", "flowing mage robe with a deep neckline"]
REGRAS_BATALHA = ("All characters are grown-up adults in their twenties. Action-packed, cinematic, no gore, no blood. "
                  "No text, no letters, no speech bubble, no logo, no watermark.")
# dono (15/10): SÓ roupa muito sensual — lingerie, biquíni, camisola, babydoll (blusa/saia/vestido = "muita roupa")
ROUPAS = ["black lace two-piece lingerie set under an open sheer robe", "tiny red string bikini",
          "white lace two-piece lingerie set", "short black silk nightgown with thin straps and a plunging neckline",
          "red lace babydoll with thigh-high stockings", "micro white bikini", "black lace bodysuit lingerie",
          "pink satin camisole and tiny shorts sleepwear"]
ROUPAS_EPOCA = ["revealing off-shoulder silk period gown with a deep neckline and a high slit",
                "thin loose traditional robe slipping off her shoulders, tied loosely at the waist",
                "ornate noble corset dress with a very low neckline and bare shoulders"]
REGRAS = ("All women are grown-up adults in their late twenties with mature curvy bodies, every woman in lingerie, "
          "bikini or nightgown (no casual clothes, no office clothes, no skirts) that still covers everything private. "
          "No text, no letters, no speech bubble, no logo, no watermark.")
ESTILO = "Korean manhwa art style, clean lineart, bright high-saturation colors, soft cinematic lighting, eye-catching " \
         "16:9 YouTube thumbnail, dynamic composition, characters large in frame, one continuous image, no border, " \
         "no split, no panels."
ENQUADRE = {"texto": "The characters fill the RIGHT two thirds; the LEFT third is an uncluttered empty part of the "
                     "same scene to hold text.",
            "baloes": "The characters fill the center of the frame; leave some empty background at the top corners.",
            "etiqueta": "The characters fill the RIGHT two thirds; leave space at the upper left for a bold archetype badge.",
            "rotulos": "The characters fill the center; leave some clear background above their heads for speech labels and arrows.",
            "vertical": "Tall vertical frame: the characters fill the middle and lower part, faces large; leave some "
                        "empty background at the top."}
ESTILO_VERTICAL = ESTILO.replace("16:9 YouTube thumbnail", "9:16 vertical YouTube Shorts cover")
VW, VH = 720, 1280  # capa dos Shorts
AMARELO, PRETO, BRANCO = (255, 212, 0), (0, 0, 0), (255, 255, 255)


def _cfg_obra(obra):
    try:
        return json.loads(CFG.read_text(encoding="utf-8")).get(obra)
    except (OSError, ValueError):
        return None


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _gateway():
    c = json.loads((PROJECT_DIR / "secrets" / "claude_proxy.json").read_text(encoding="utf-8"))
    return c["base_url"].rstrip("/"), c["auth_token"]


def _gerar(prompt, formato="16:9", pose=None):
    """Imagem (Path) pro prompt — do cache, do gateway (se imagem_reserva.GATEWAY) ou da reserva (imagem_reserva:
    Cloudflare/Pollinations, sem os modelos que recusam a pose). None se nada gerou."""
    import imagem_reserva
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{hashlib.md5(prompt.encode()).hexdigest()[:16]}.png"
    if out.exists() and out.stat().st_size > 5000:
        return out
    b64 = None
    if imagem_reserva.GATEWAY:
        base, tok = _gateway()
        corpo = json.dumps({"model": MODELO, "prompt": prompt, "n": 1, "response_format": "b64_json",
                            "size": "1024x1792" if formato == "9:16" else "1792x1024",
                            "aspect_ratio": formato}).encode()
        req = urllib.request.Request(base + "/v1/images/generations", data=corpo,
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
            b64 = ((d.get("data") or [{}])[0]).get("b64_json")
        except urllib.error.HTTPError as e:
            log(f"  capa IA: gateway HTTP {e.code} {e.read().decode('utf-8', 'replace')[:120]}")
        except Exception as e:  # noqa: BLE001
            log(f"  capa IA: gateway falhou ({type(e).__name__}: {str(e)[:100]})")
    if b64:
        out.write_bytes(base64.b64decode(b64))
        return out
    img, quem = imagem_reserva.gerar(prompt, formato, pose)
    if not img:
        log(f"  capa IA: reserva também não gerou ({quem[:300]})")
        return None
    log(f"  capa IA: imagem pela reserva ({quem})")
    out.write_bytes(img)
    return out


# palavras neutras de propósito: termo sexual + "criança" no mesmo pedido faz o Google recusar a pergunta inteira
_PERGUNTA = (
    'Quality check of a drawn YouTube thumbnail. Answer ONLY JSON: {"descoberto": true/false (some private body part '
    'is left uncovered by clothing), "borrado": true/false (mosaic or blur patch), "intimo": true/false (shows an '
    'intimate act instead of just a teasing pose; a hug or lap pose is fine), "adultos": true/false (every character '
    'clearly looks like a grown-up adult), "letras": true/false (letters or speech bubbles drawn in the image), '
    '"ousadia": 0-10 (how daring the outfits and pose are), "roupa_ousada": true/false (EVERY woman wears only '
    'lingerie, bikini, nightgown or babydoll — false if any wears casual/office clothes, a skirt or a sweater), '
    '"dividida": true/false (the picture looks split into two panels/scenes or has a visible seam or border), '
    + visao_capa.DEFEITOS + ', '
    '"homens": number of men in the picture, '
    '"mulheres": number of women in the picture, '
    '"ela": [ymin, xmin, ymax, xmax] face box of the main woman (0-1000) or null, "ele": [ymin, xmin, ymax, xmax] face '
    'box of the man (0-1000) or null}')
VISAO_RESERVA = visao_capa.VISAO_RESERVA  # pelo gateway, quando o Gemini dá 429/recusa


def _checar(img, pose=None):
    """Checagem da imagem gerada pela VISÃO (Gemini; reserva Claude pelo gateway) + caixas dos rostos. Com a pose, a
    visão também confere se a cena bate com ela (dono 20/10: ela sentada no lugar dele passou). Cache por md5+pose.
    None se as duas falharem."""
    b = Path(img).read_bytes()
    # v3 (20/10): + parte do corpo duplicada, figurantes e pose certa
    f = CHK_DIR / f"{hashlib.md5(b).hexdigest()}_v3_{pose or 'sem_pose'}.json"
    d = _ler(f, None)
    if d:
        return d
    pergunta = _PERGUNTA + (visao_capa.pergunta_pose(_pose(pose)[1]) if pose else "")
    try:
        gw = _gateway()
    except (OSError, ValueError, KeyError):
        gw = None
    r = visao_capa.perguntar(b, pergunta, gateway=gw)
    if r is None:
        return None

    def caixa(v):
        try:
            y0, x0, y1, x1 = [float(n) / 1000 for n in v]
            return [x0, y0, x1, y1] if x1 > x0 and y1 > y0 else None
        except (TypeError, ValueError):
            return None
    def num(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None
    d = {"exposto": bool(r.get("descoberto")), "censura": bool(r.get("borrado")), "ato_sexual": bool(r.get("intimo")),
         "menor": r.get("adultos") is False, "texto": bool(r.get("letras")), "sensual": float(r.get("ousadia") or 0),
         "roupa_ousada": r.get("roupa_ousada") is not False, "dividida": bool(r.get("dividida")),
         "anatomia": bool(r.get("anatomia")), "figurantes": bool(r.get("figurantes")),
         "pose_certa": None if not pose else r.get("pose_certa") is not False, "pose_erro": r.get("pose_erro") or "",
         "homens": num(r.get("homens")), "mulheres": num(r.get("mulheres")),
         "ela": caixa(r.get("ela")), "ele": caixa(r.get("ele"))}
    _gravar(f, d)
    return d


def _llm_json(pedido, max_tokens=1400, temperature=0.9):
    """JSON (dict) do Gemini; se ele recusar, der cota ou devolver JSON quebrado, do Claude pelo gateway. {} se os
    dois falharem."""
    import gemini_llm

    def claude(modelo):
        base, tok = _gateway()
        corpo = {"model": modelo, "max_tokens": max_tokens, "temperature": temperature,
                 "messages": [{"role": "user", "content": pedido}]}
        req = urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(corpo).encode(),
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok})
        with urllib.request.urlopen(req, timeout=120) as r:
            c = json.loads(r.read())["choices"][0]["message"]["content"]
        return c if isinstance(c, str) else "".join(p.get("text", "") for p in c)
    # 23/10 (dona: Kiro esgotou): depois do Claude, os Gemini do Antigravity no mesmo gateway
    reservas = [lambda m=m: claude(m) for m in dict.fromkeys([VISAO_RESERVA] + visao_capa.RESERVAS_GATEWAY)]
    for pedir in [lambda: gemini_llm.generate_text(pedido, max_tokens=max_tokens, temperature=temperature,
                                                   max_attempts=2)] + reservas:
        try:
            return json.loads(re.search(r"\{.*\}", pedir() or "", re.S).group(0))
        except Exception as e:  # noqa: BLE001
            ultimo = e
    log(f"  capa IA: LLM falhou ({str(ultimo)[:100]})")
    return {}


def _reprovada(chk, pose=None):
    """Nudez, mosaico, ato íntimo, cara de menor, imagem dividida em painéis ou roupa comum (o dono quer só
    lingerie/biquíni/camisola; pose de batalha não precisa) -> fora. Dono 19/10: corpo malformado (braço a mais,
    corpo partido) e, nas poses sensuais (todas com 1 homem), homem repetido ou ela repetida na pose de 1 mulher.
    Dono 20/10: parte do corpo duplicada (duas bundas), gente sobrando no fundo e pose diferente da pedida."""
    if not chk or chk["exposto"] or chk["censura"] or chk["ato_sexual"] or chk["menor"] or chk.get("dividida") or \
            chk.get("anatomia") or chk.get("figurantes") or chk.get("pose_certa") is False or \
            (pose not in POSES_GENERO and not chk.get("roupa_ousada", True)):
        return True
    return pose in POSES and ((chk.get("homens") or 0) > 1
                              or (POSES[pose][0] == 1 and (chk.get("mulheres") or 0) > 1))


# ---------- rodízio de poses (teste A/B) ----------

def _stats():
    return _ler(STATS, {})


def _escolher_poses(n, rng=random):
    """n poses diferentes por amostragem de Thompson (Beta(vitórias+1, derrotas+1)): a que mais ganha no teste A/B
    sai mais, as pouco testadas ainda aparecem."""
    s = _stats()
    nota = {p: rng.betavariate(s.get(p, {}).get("vitorias", 0) + 1,
                               s.get(p, {}).get("testes", 0) - s.get(p, {}).get("vitorias", 0) + 1) for p in POSES}
    return sorted(POSES, key=nota.get, reverse=True)[:n]


def _generos(obra):
    try:
        cfg = json.loads((PROJECT_DIR / "config" / "fila.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return set(next((o.get("generos") or [] for o in cfg.get("obras", []) if o.get("slug") == obra), []))


def _pose_genero(obra, usadas, rng=random):
    """Uma pose de batalha que combine com os gêneros da obra (Thompson como as outras); None se a obra não é de
    fantasia/ação ou o plano já tem uma."""
    cands = [p for p, (gs, _d) in POSES_GENERO.items() if gs & _generos(obra)]
    if not cands or usadas & set(POSES_GENERO):
        return None
    s = _stats()
    return max(cands, key=lambda p: rng.betavariate(s.get(p, {}).get("vitorias", 0) + 1,
                                                   s.get(p, {}).get("testes", 0) - s.get(p, {}).get("vitorias", 0) + 1))


def _pose(p):
    """(mín. de mulheres, descrição) da pose — catálogo sensual ou de batalha."""
    return POSES[p] if p in POSES else (1 if "SHE" in POSES_GENERO[p][1] else 0, POSES_GENERO[p][1])


def registrar_teste(capa_json):
    """Chamado pelo postador quando as variantes entram num teste A/B do Studio."""
    d = _ler(capa_json, {})
    s = _stats()
    for v in d.get("variantes", []):
        for k in (v.get("pose"), f"layout:{v.get('layout')}"):
            if k:
                s.setdefault(k, {"testes": 0, "vitorias": 0})["testes"] += 1
    _gravar(STATS, s)


def registrar_vencedora(capa_json, idx):
    """Chamado quando o Studio aponta a capa vencedora (idx na lista de variantes)."""
    vs = _ler(capa_json, {}).get("variantes", [])
    if not 0 <= idx < len(vs):
        return
    s = _stats()
    for k in (vs[idx].get("pose"), f"layout:{vs[idx].get('layout')}"):
        if k:
            s.setdefault(k, {"testes": 1, "vitorias": 0})["vitorias"] += 1
    _gravar(STATS, s)


# ---------- plano por capítulo ----------

def _personagens(c, n_mulheres, roupa, roupas):
    """Personagens pro prompt com a ROUPA colada em cada mulher (roupa no fim do prompt o gerador ignora e veste
    suéter): ELA, as outras mulheres da obra (harém) + genéricas, ELE. n_mulheres=0 (batalha só dele): só ELE."""
    if n_mulheres == 0:
        return f"HIM = {c['ele']}."
    t = f"HER (the main woman) = {c['ela']}, wearing {roupa}."
    if n_mulheres > 1:
        outras = [o["desc"] for o in c.get("outras", [])][:n_mulheres - 1]
        while len(outras) < n_mulheres - 1:
            outras.append("another beautiful adult woman with a different hair color and style")
        resto = [r for r in roupas if r != roupa]
        random.shuffle(resto)
        t += " OTHER WOMEN: " + "; ".join(f"{o}, wearing {resto[i % len(resto)]}" for i, o in enumerate(outras)) + "."
    return t + f" HIM = {c['ele']}."


def _plano(obra, c, chave, roteiro, n, texto_pt="", fala=None):
    """{"variantes": [{pose, layout, roupa, prompt}], "textos": {"pt": {...}}} do capítulo — salvo em
    CACHE/plano_<obra>_<chave>.json (as outras línguas e as re-renderizações usam o mesmo)."""
    arq = CACHE / f"plano_{obra}_{chave}.json"
    pl = _ler(arq, None)
    if pl and len([v for v in pl["variantes"] if not v.get("reprovada")]) >= n:
        return pl, arq
    usadas = {v["pose"] for v in (pl or {}).get("variantes", [])}
    poses = [p for p in _escolher_poses(len(POSES)) if p not in usadas][:n + 1]
    batalha = _pose_genero(obra, usadas)
    if batalha:  # obra de fantasia/ação: 1 das variantes vira pose de batalha (alternativa no teste A/B)
        poses = poses[:max(1, n - 1)] + [batalha] + poses[max(1, n - 1):]
    roupas = ROUPAS_EPOCA if c.get("epoca") else ROUPAS
    sorteio = random.sample(roupas, k=min(len(roupas), len(poses)))
    # o LLM só escreve cenário/falas/título: pose e roupa vão direto pro prompt da imagem. Com a descrição das poses
    # e da lingerie no pedido, Gemini (PROHIBITED_CONTENT) e Claude recusam o plano inteiro (15/10)
    lista = "\n".join(f'{i + 1}. "{p}": ' + (
        "epic battle moment of the chapter (fala_dela = his battle cry, reacao_dele = the enemy's shocked line)"
        if p in POSES_GENERO else "several women tease him at once" if POSES[p][0] >= 2
        else "she teases him up close") for i, p in enumerate(poses))
    # só as linhas sem palavra sexual: o roteiro inteiro de um manhwa adulto o Gemini bloqueia (PROHIBITED_CONTENT)
    limpo = "\n".join(ln for ln in (roteiro or "").splitlines() if not _SEXUAL.search(ln))
    pedido = (
        f"Romantic comedy manhwa chapter script (Portuguese):\n{limpo[:3500]}\n\nFor a comedic YouTube thumbnail of "
        f"this chapter, plan each variant below (same characters, a setting from the chapter):\n{lista}\n\n"
        f"For each variant give: \"cenario\" (setting + lighting, English, max 20 words), \"fala_dela\" (what "
        f"she says, Brazilian Portuguese, 1-4 words, teasing/provocative, like \"MESTRE?!\", \"PARE DE FRESCURA!\", "
        f"\"AGORA EU SOU SUA!\"{f', or her real line {chr(34)}{fala}{chr(34)} if it fits' if fala else ''}), "
        f"\"reacao_dele\" (his flustered reaction, 1-3 words, like \"NUNCA!\", \"TÁ BOM...\", \"SOCORRO...\"). "
        f"No sexual or explicit words in the lines. Also \"texto\": a thumbnail title, Brazilian Portuguese, 2-4 words, "
        f"curious and provocative (like \"ELA É SUA HERANÇA?!\"). Answer ONLY JSON: "
        f'{{"poses": [{{"pose": "<variant id>", "cenario": "...", "fala_dela": "...", "reacao_dele": "..."}}],'
        f' "texto": "..."}}')
    r = _llm_json(pedido)
    por_pose = {str(x.get("pose")): x for x in r.get("poses", []) if isinstance(x, dict)}
    if not por_pose:  # sem falas a capa sai pela metade: quem chamou usa a capa de painel
        return None, arq
    pl = pl or {"variantes": [], "textos": {"pt": {"texto": "", "falas": {}}}}
    if r.get("texto") and not pl["textos"]["pt"].get("texto"):
        pl["textos"]["pt"]["texto"] = str(r["texto"]).strip().upper()
    base = len(pl["variantes"])
    for i, p in enumerate(poses):
        x = por_pose.get(p) or {}
        luta = p in POSES_GENERO
        roupa = random.choice(ROUPAS_BATALHA) if luta else sorteio[i % len(sorteio)]
        cena = _pose(p)[1] + (f"; setting: {x['cenario']}" if x.get("cenario") else
                              "; setting: a ruined battlefield at dusk" if luta else "; setting: a cozy bedroom at night")
        layouts_disponiveis = ["texto", "baloes", "etiqueta", "rotulos"]
        layout = "texto" if luta else layouts_disponiveis[(base + i) % len(layouts_disponiveis)]
        prompt = (f"Scene: {cena}. {_personagens(c, _pose(p)[0], roupa, ROUPAS_BATALHA if luta else roupas)} {ESTILO} "
                  f"{ENQUADRE.get(layout, ENQUADRE['texto'])} {REGRAS_BATALHA if luta else REGRAS}")
        pl["variantes"].append({"pose": p, "layout": layout, "roupa": roupa, "prompt": prompt})
        pl["textos"]["pt"]["falas"][p] = [str(x.get("fala_dela") or "").strip().upper(),
                                         str(x.get("reacao_dele") or "").strip().upper()]
    if texto_pt and len(texto_pt.split()) <= 6:
        pl["textos"]["pt"]["texto"] = texto_pt.upper()
    _gravar(arq, pl)
    return pl, arq


def _textos(pl, arq, idioma):
    """Textos da capa na língua do vídeo (traduz os do pt uma vez e guarda no plano)."""
    pt = pl["textos"]["pt"]
    feito = pl["textos"].get(idioma)
    if feito and set(pt["falas"]) <= set(feito.get("falas", {})):
        return feito
    import idiomas
    nome = idiomas.IDIOMAS.get(idioma, {}).get("nome", idioma)
    try:
        t = _llm_json(f"Translate these YouTube thumbnail lines from Brazilian Portuguese to {nome}, keeping them "
                      f"SHORT, punchy and in UPPERCASE where the script has case. Same JSON keys. Answer ONLY JSON:\n"
                      f"{json.dumps(pt, ensure_ascii=False)}", max_tokens=800, temperature=0.3)
        t = {"texto": str(t.get("texto") or ""), "falas": {k: [str(a or ""), str(b or "")]
                                                         for k, (a, b) in (t.get("falas") or {}).items()}}
    except Exception:  # noqa: BLE001
        return {"texto": "", "falas": {}}
    pl["textos"][idioma] = t
    _gravar(arq, pl)
    return t


# ---------- composição ----------

def _inter(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def _posicionar(tam, rosto, obstaculos, quadro=(W, H)):
    """Canto sup-esq (x, y) de uma caixa tam=(w, h) perto do rosto (caixa em px), sem cobrir rostos/obstáculos."""
    w, h = tam
    W, H = quadro
    fx0, fy0, fx1, fy1 = rosto
    melhor = None
    for y in range(16, max(17, H - h - 15), 20):  # busca em grade: a 1ª versão (6 posições fixas) empilhava os balões
        for x in range(16, max(17, W - w - 15), 20):
            caixa = (x, y, x + w, y + h)
            dx, dy = max(fx0 - (x + w), x - fx1, 0), max(fy0 - (y + h), y - fy1, 0)
            nota = sum(_inter(caixa, o) for o in obstaculos) * 3 + abs((dx * dx + dy * dy) ** 0.5 - 40) + \
                (0 if y + h <= fy1 else 40)  # acima/ao lado do rosto antes de embaixo
            if melhor is None or nota < melhor[0]:
                melhor = (nota, x, y)
    return melhor[1], melhor[2]


def _ponta(d, caixa, rosto, cor):
    """Ponta (triângulo) saindo da caixa do texto em direção ao rosto, no máx. 130 px."""
    x0, y0, x1, y1 = caixa
    fx, fy = (rosto[0] + rosto[2]) / 2, (rosto[1] + rosto[3]) / 2
    px, py = min(max(fx, x0 + 30), x1 - 30), min(max(fy, y0 + 20), y1 - 20)
    dx, dy = fx - px, fy - py
    dist = (dx * dx + dy * dy) ** 0.5 or 1
    alvo = max(0.0, dist - 0.5 * max(rosto[2] - rosto[0], rosto[3] - rosto[1]))
    comp = min(130.0, alvo)
    if comp < 25:
        return
    tx, ty = px + dx / dist * (comp + 20), py + dy / dist * (comp + 20)
    nx, ny = -dy / dist * 18, dx / dist * 18
    tri = [(px + nx, py + ny), (px - nx, py - ny), (tx, ty)]
    d.polygon(tri, fill=cor, outline=PRETO, width=5)


def _quebrar(d, texto, f, larg):
    linhas, cur = [], ""
    for w in texto.split():
        tst = (cur + " " + w).strip()
        if cur and d.textlength(tst, font=f) > larg:
            linhas.append(cur)
            cur = w
        else:
            cur = tst
    return linhas + ([cur] if cur else [])


def _fala(d, texto, rosto, obstaculos, fonte, estilo, quadro=(W, H)):
    """Fala perto do rosto com ponta pra ele. estilo "balao" = caixa branca com texto preto; "amarelo" = letra
    amarela com contorno preto (como as referências). Devolve a caixa ocupada."""
    import fx_acabamento as fa
    W, H = quadro
    tam = 58 if estilo == "amarelo" else 50
    while True:
        f = fa._fonte(fonte, tam)
        linhas = _quebrar(d, texto, f, (0.30 if W > H else 0.55) * W)
        if len(linhas) <= 2 or tam <= 30:
            break
        tam -= 4
    lh = int(f.size * 1.08)
    tw = max(d.textlength(ln, font=f) for ln in linhas)
    pad = 26 if estilo == "balao" else 8
    w, h = int(tw + 2 * pad), int(lh * len(linhas) + 2 * pad)
    if rosto:
        x, y = _posicionar((w, h), rosto, obstaculos, quadro)
    else:
        x, y = int(0.55 * W), 30
    caixa = (x, y, x + w, y + h)
    if rosto:
        _ponta(d, caixa, rosto, BRANCO)
    if estilo == "balao":
        d.rounded_rectangle(caixa, radius=26, fill=BRANCO, outline=PRETO, width=6)
    for i, ln in enumerate(linhas):
        lx = x + pad + (tw - d.textlength(ln, font=f)) / 2
        if estilo == "balao":
            d.text((lx, y + pad + i * lh - 4), ln, font=f, fill=(15, 15, 15))
        else:
            d.text((lx, y + pad + i * lh), ln, font=f, fill=AMARELO, stroke_width=9, stroke_fill=PRETO)
    return caixa


# 01/11 dona: a mascote antiga (chibi roxa) sai de tudo — a figurinha agora é a Maria recortada (PNG com alfa).
# Fora: estudante (uniforme escolar é proibido na capa) e recortes de meio corpo.
MASCOTE_DIR = Path(r"D:\hipercool-materiais\mascote_waifu_v2\cosplay_recorte")


def _colar_mascote(capa, semente="", lado="direita", alto=0.46):
    """Cola a mascote (contorno branco de figurinha + sombra) no canto de baixo. Devolve a pose usada ou None."""
    import os
    from PIL import Image, ImageFilter
    if os.environ.get("CAPA_MASCOTE", "1") == "0":
        return None
    fotos = sorted(p for p in MASCOTE_DIR.glob("*.png") if "estudante" not in p.name) if MASCOTE_DIR.exists() else []
    fotos = [p for p in fotos if Image.open(p).height >= 900]
    if not fotos:
        return None
    foto = fotos[int(hashlib.md5(str(semente).encode()).hexdigest(), 16) % len(fotos)]
    pose = foto.stem
    m = Image.open(foto).convert("RGBA")
    m = m.crop(m.getbbox() or (0, 0, m.width, m.height))
    W, H = capa.size
    h = int(H * alto)
    m = m.resize((max(1, int(m.width * h / m.height)), h), Image.LANCZOS)
    borda = max(4, h // 60)
    a = m.getchannel("A").filter(ImageFilter.MaxFilter(borda * 2 + 1))
    fig = Image.new("RGBA", (m.width + 2 * borda, m.height + 2 * borda), (0, 0, 0, 0))
    branco = Image.new("RGBA", fig.size, (255, 255, 255, 255))
    alfa = Image.new("L", fig.size, 0)
    alfa.paste(a, (borda, borda))
    fig.paste(branco, (0, 0), alfa)
    fig.alpha_composite(m, (borda, borda))
    sombra = Image.new("RGBA", fig.size, (0, 0, 0, 0))
    sombra.putalpha(alfa.point(lambda v: v * 0.55).filter(ImageFilter.GaussianBlur(borda * 2)))
    x = W - fig.width - int(W * 0.015) if lado == "direita" else int(W * 0.015)
    y = H - fig.height + int(fig.height * 0.06)
    base = capa.convert("RGBA")
    base.alpha_composite(sombra, (max(0, x + borda), max(0, min(H - 1, y + borda))))
    base.alpha_composite(fig, (max(0, x), max(0, y)))
    capa.paste(base.convert("RGB"))
    return pose


_ETIQUETAS = [
    ("YANDERE", r"yandere|obcecad|obsess|possessiv"), ("HARÉM", r"har[eé]m|esposas|noivas"),
    ("RANK S", r"rank[- ]?s\b|classe s|s-rank"), ("ISEKAI", r"isekai|outro mundo|transportad|invocad"),
    ("REGRESSÃO", r"regress|voltou no tempo|segunda chance"), ("REENCARNOU", r"renasc|reencarn"),
    ("VILÃ", r"\bvil[ãa]\b"),
    ("DEMÔNIA", r"dem[ôo]ni[ao]|s[uú]cubo"), ("ELFA", r"\belf[ao]s?\b"), ("RAINHA", r"rainha|imperatriz|princesa"),
    ("DEUSA", r"\bdeusa"), ("ASSASSINA", r"assassin"), ("NERD", r"\bnerd\b"), ("O MAIS FRACO", r"mais frac|fracot"),
    ("APAIXONADA", r"apaixon|se apaixonou|amor"),
]

_PAPEIS = [("RANK S", r"rank[- ]?s\b|classe s|s-rank|mais forte|invenc"), ("O MAIS FRACO", r"mais frac|fracot|n[ií]vel 1|level 1"),
           ("REGRESSOR", r"regress|voltou no tempo|segunda chance"), ("REENCARNADO", r"renasc|reencarn"),
           ("NERD", r"\bnerd\b"), ("VILÃO", r"\bvil[ãa]o\b"), ("GÊNIO", r"g[eê]nio"), ("REI", r"\brei\b|imperador")]


def _papel(texto="", cena=""):
    t = f"{cena} {texto}".lower()
    return next((p for p, rx in _PAPEIS if re.search(rx, t)), "PROTA")


def _etiqueta(texto="", cena=""):
    t = f"{cena} {texto}".lower()
    for palavra, rx in _ETIQUETAS:
        if re.search(rx, t):
            return palavra
    pal = re.sub(r"[^\wÀ-ú ]", " ", texto or "").split()
    return " ".join(pal[:2]).upper() if pal else ""


def _lua(d, p0, p2, bojo, esp, contorno):
    import math
    mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2
    vx, vy = p2[0] - p0[0], p2[1] - p0[1]
    n = math.hypot(vx, vy) or 1
    p1 = (mx - vy / n * n * 0.35 * bojo, my + vx / n * n * 0.35 * bojo)
    pts = []
    for i in range(41):
        t = i / 40
        bx = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        by = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
        dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
        k = math.hypot(dx, dy) or 1
        w = esp * math.sin(math.pi * t) + 2
        pts.append(((bx - dy / k * w, by + dx / k * w), (bx + dy / k * w, by - dx / k * w)))
    lua = [a for a, _ in pts] + [b for _, b in reversed(pts)]
    d.line(lua + [lua[0]], fill=PRETO, width=contorno, joint="curve")
    d.polygon(lua, fill=AMARELO)


def _caber_fonte(d, texto, larg_max, tam, fonte="LuckiestGuy-Regular.ttf"):
    import fx_acabamento as fa
    while tam > 30:
        f = fa._fonte(fonte, tam)
        if d.textlength(texto, font=f) <= larg_max:
            return f, tam
        tam -= 6
    return fa._fonte(fonte, tam), tam


def _desenhar_etiqueta(capa, palavra, rosto=None, fonte="LuckiestGuy-Regular.ttf"):
    from PIL import ImageDraw
    W, H = capa.size
    d = ImageDraw.Draw(capa)
    vertical = H > W
    f, tam = _caber_fonte(d, palavra, W * (0.86 if vertical else 0.62), int(H * (0.11 if vertical else 0.2)), fonte)
    larg = d.textlength(palavra, font=f)
    x = (W - larg) / 2
    y = int(H * (0.62 if vertical else 0.66))
    p0 = (x + larg * 0.86, y + tam * 0.12)
    if rosto and rosto[3] < y:
        p2 = (min(max(rosto[0], 20), W - 20) if (rosto[0] + rosto[2]) / 2 > p0[0] else rosto[2], rosto[3] + tam * 0.1)
    else:
        p2 = (x + larg * 0.70, y - tam * 1.25)
    _lua(d, p0, p2, -1 if p2[0] < p0[0] else 1, tam * 0.16, max(6, tam // 14))
    d.text((x, y), palavra, font=f, fill=AMARELO, stroke_width=max(8, tam // 11), stroke_fill=PRETO)


def _seta(d, ini, fim, esp, contorno):
    import math
    vx, vy = fim[0] - ini[0], fim[1] - ini[1]
    n = math.hypot(vx, vy) or 1
    ux, uy = vx / n, vy / n
    cab = min(esp * 2.6, n * 0.45)
    base = (fim[0] - ux * cab, fim[1] - uy * cab)
    ctrl = ((ini[0] + base[0]) / 2 - uy * n * 0.12, (ini[1] + base[1]) / 2 + ux * n * 0.12)
    lados_a, lados_b = [], []
    for i in range(25):
        t = i / 24
        bx = (1 - t) ** 2 * ini[0] + 2 * (1 - t) * t * ctrl[0] + t * t * base[0]
        by = (1 - t) ** 2 * ini[1] + 2 * (1 - t) * t * ctrl[1] + t * t * base[1]
        dx = 2 * (1 - t) * (ctrl[0] - ini[0]) + 2 * t * (base[0] - ctrl[0])
        dy = 2 * (1 - t) * (ctrl[1] - ini[1]) + 2 * t * (base[1] - ctrl[1])
        k = math.hypot(dx, dy) or 1
        w = esp * (0.55 + 0.45 * t) / 2
        lados_a.append((bx - dy / k * w, by + dx / k * w))
        lados_b.append((bx + dy / k * w, by - dx / k * w))
    dx, dy = (base[0] - ctrl[0]), (base[1] - ctrl[1])
    k = math.hypot(dx, dy) or 1
    px_, py_ = -dy / k, dx / k
    ponta = [(base[0] + px_ * esp * 1.25, base[1] + py_ * esp * 1.25), fim,
             (base[0] - px_ * esp * 1.25, base[1] - py_ * esp * 1.25)]
    corpo = lados_a + list(reversed(lados_b))
    for forma in (corpo, ponta):
        d.line(forma + [forma[0]], fill=PRETO, width=contorno, joint="curve")
    d.polygon(corpo, fill=AMARELO)
    d.polygon(ponta, fill=AMARELO)


def _rotulos(capa, rotulos, fonte="LuckiestGuy-Regular.ttf"):
    from PIL import ImageDraw
    W, H = capa.size
    d = ImageDraw.Draw(capa)

    def dentro(c):
        if not c:
            return None
        x0, y0, x1, y1 = max(0, c[0]), max(0, c[1]), min(W, c[2]), min(H, c[3])
        return c if x1 > x0 and y1 > y0 and (x1 - x0) * (y1 - y0) >= 0.5 * (c[2] - c[0]) * (c[3] - c[1]) else None

    rotulos = [(t if dentro(c) else "", dentro(c)) for t, c in rotulos]
    bloqueio = [c for _, c in rotulos if c] + [(W * (0.62 if H > W else 0.85), H * 0.62, W, H)]

    def livre(r):
        return (r[0] >= W * 0.02 and r[2] <= W * 0.98 and r[1] >= H * 0.02 and r[3] <= H * 0.98
                and not any(r[0] < b[2] and b[0] < r[2] and r[1] < b[3] and b[1] < r[3] for b in bloqueio))

    for i, (txt, cx) in enumerate(rotulos):
        if not txt:
            continue
        f, tam = _caber_fonte(d, txt, W * (0.8 if H > W else 0.36), int(min(W, H) * 0.13), fonte)
        larg, alt = d.textlength(txt, font=f), tam * 1.05
        alvo = ((cx[0] + cx[2]) / 2, (cx[1] + cx[3]) / 2) if cx else (W * (0.25 + 0.5 * (i % 2)), H * 0.1)
        pos = None
        if cx:
            gap = tam * 1.3
            cmx = alvo[0] - larg / 2
            fora = cx[0] - larg - gap, cx[2] + gap
            acima = cx[1] - alt - gap
            lados = [(x, acima) for x in (cmx, cx[2] - larg, cx[0])]
            lados += [(x, alvo[1] - alt / 2) for x in (fora if alvo[0] < W / 2 else fora[::-1])]
            lados += [(x, cx[3] + gap) for x in (cmx, cx[2] - larg, cx[0])]
            pos = next(((x, y) for x, y in lados if livre((x, y, x + larg, y + alt))), None)
        if not pos:
            def longe(c):
                if not cx:
                    return True
                dx = max(cx[0] - (c[0] + larg), c[0] - cx[2], 0)
                dy = max(cx[1] - (c[1] + alt), c[1] - cx[3], 0)
                return (dx * dx + dy * dy) ** 0.5 >= tam * 0.8
            cands = [(W * fx - larg / 2, H * fy) for fy in (0.03, 0.12, 0.22, 0.34, 0.46, 0.58, 0.7, 0.8)
                     for fx in (0.22, 0.35, 0.5, 0.65, 0.78)]
            cands = [c for c in cands if livre((c[0], c[1], c[0] + larg, c[1] + alt)) and longe(c)]
            pos = min(cands, key=lambda c: (c[0] + larg / 2 - alvo[0]) ** 2 + (c[1] + alt / 2 - alvo[1]) ** 2) \
                if cands else (W * 0.04, H * 0.04 + i * alt * 1.2)
        x, y = pos
        if cx:
            ini = (min(max(alvo[0], x + larg * 0.15), x + larg * 0.85),
                   y + alt if y + alt <= cx[1] else y if y >= cx[3] else y + alt / 2)
            if y + alt > cx[1] and y < cx[3]:
                ini = (x + larg if x + larg <= cx[0] else x, y + alt / 2)
            fx = min(max(ini[0], cx[0] + (cx[2] - cx[0]) * 0.2), cx[2] - (cx[2] - cx[0]) * 0.2)
            fy = min(max(ini[1], cx[1] + (cx[3] - cx[1]) * 0.25), cx[3] - (cx[3] - cx[1]) * 0.25)
            fim = (cx[0] - tam * 0.1 if ini[0] < cx[0] else cx[2] + tam * 0.1 if ini[0] > cx[2] else fx,
                   cx[1] - tam * 0.1 if ini[1] < cx[1] else cx[3] + tam * 0.1 if ini[1] > cx[3] else fy)
            _seta(d, ini, fim, tam * 0.3, max(5, tam // 14))
        bloqueio.append((x, y, x + larg, y + alt))
        d.text((x, y), txt, font=f, fill=AMARELO, stroke_width=max(6, tam // 10), stroke_fill=PRETO)


def _compor(img_path, layout, texto, selo, falas, rostos, out_jpg, fonte="LuckiestGuy-Regular.ttf", quadro=(W, H)):
    """quadro (1280x720; Shorts 720x1280): layout "texto" = frase grande à esquerda (branco/amarelo) + balão branco
    com a fala dela; "baloes" = fala dela e reação dele em amarelo apontando pros rostos. Selo vermelho no canto."""
    from PIL import Image, ImageDraw
    import fx_acabamento as fa
    W, H = quadro
    img = Image.open(img_path).convert("RGB")
    sc = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * sc) + 1, int(img.height * sc) + 1), Image.LANCZOS)
    ox, oy = (img.width - W) // 2, (img.height - H) // 2
    capa = img.crop((ox, oy, ox + W, oy + H))
    d = ImageDraw.Draw(capa)

    def px(b):  # caixa 0-1 da imagem original -> px da capa recortada
        if not b:
            return None
        return (b[0] * img.width - ox, b[1] * img.height - oy, b[2] * img.width - ox, b[3] * img.height - oy)
    ela, ele = px(rostos.get("ela")), px(rostos.get("ele"))
    obst = [b for b in (ela, ele) if b]
    if selo:
        fs = fa._fonte("Montserrat-ExtraBold.ttf", 44)
        lw = int(d.textlength(selo, font=fs))
        d.rounded_rectangle([30, 26, 30 + lw + 44, 26 + 70], radius=12, fill=(215, 30, 45), outline=PRETO, width=4)
        d.text((52, 34), selo, font=fs, fill=BRANCO)
        obst.append((20, 16, 30 + lw + 60, 110))
    dela, dele = (falas + ["", ""])[:2]
    obst += [b for b in (ela, ele) if b]  # rosto pesa em dobro: balão nunca em cima de rosto
    # 31/10: rótulo sem rosto achado = capa sem texto nenhum; etiqueta sem palavra idem -> volta pra frase grande
    if (layout == "rotulos" and not (ele or ela)) or (layout == "etiqueta" and not _etiqueta(texto)):
        layout = "texto"
    if layout == "etiqueta":
        palavra = _etiqueta(texto)
        _desenhar_etiqueta(capa, palavra, rosto=ela, fonte=fonte)
    elif layout == "rotulos":
        papel = _papel(texto)
        rot = []
        if ele:
            rot.append((papel, ele))
        if ela:
            rot.append((dela or "SÓ MEU!", ela))
        _rotulos(capa, rot, fonte=fonte)
    elif layout == "texto" and texto:
        area, tam = int(0.40 * W), 118
        while tam > 54:
            f = fa._fonte(fonte, tam)
            linhas = _quebrar(d, texto.upper(), f, area)
            if len(linhas) <= 3:
                break
            tam -= 8
        y = (H - len(linhas) * int(tam * 1.1)) // 2 + 30
        obst.append((30, y - 10, 44 + area, y + len(linhas) * int(tam * 1.1)))
        for i, ln in enumerate(linhas):
            d.text((44, y), ln, font=f, fill=AMARELO if i % 2 else BRANCO, stroke_width=10, stroke_fill=PRETO)
            y += int(tam * 1.1)
        if dela:
            _fala(d, dela, ela, obst, fonte, "balao", quadro)
    else:
        if dela:
            obst.append(_fala(d, dela, ela, obst, fonte, "amarelo", quadro))
        if dele and ele:
            _fala(d, dele, ele, obst, fonte, "amarelo", quadro)
    _colar_mascote(capa, semente=img_path)
    capa.save(out_jpg, quality=92)
    return out_jpg


def capas(obra, texto, selo, out_jpg, n=3, fonte="LuckiestGuy-Regular.ttf", roteiro=None, fala=None, idioma="pt",
          chave=None):
    """Até n capas checadas: out_jpg = a 1ª; as outras <nome>_v2.jpg, _v3.jpg... + <nome>.json com pose/layout de
    cada uma. `chave` identifica o capítulo (ex. "cap07") pra todas as línguas usarem as mesmas imagens; `fala` =
    fala real dela no capítulo (vai no balão do layout "texto"). [] se a obra não estiver em config/capas.json ou o
    gateway não gerar nada (aí quem chamou usa a capa de painel)."""
    c = _cfg_obra(obra)
    if not c or not c.get("ele") or not c.get("ela"):
        return []
    chave = chave or hashlib.md5(f"{roteiro or ''}|{texto or ''}".encode()).hexdigest()[:12]
    texto_pt = texto if idioma == "pt" else ""
    feitas, meta, sem_cota = [], [], False
    for _rodada in range(3):  # pose reprovada -> o plano ganha poses novas
        pl, arq = _plano(obra, c, chave, roteiro, n, texto_pt, fala)
        if not pl:
            break
        tx = _textos(pl, arq, idioma)
        titulo = texto if texto and len(texto.split()) <= 6 else (tx.get("texto") or texto)
        mudou = False
        for v in pl["variantes"]:
            if len(feitas) >= n:
                break
            if v.get("reprovada") or any(m["pose"] == v["pose"] for m in meta):
                continue
            img = _gerar(v["prompt"], pose=v["pose"])
            if not img:  # gateway fora e a reserva sem cota ou recusa ESTA pose: tenta a próxima, sem reprovar
                sem_cota = True
                continue
            chk = _checar(img, v["pose"])
            if _reprovada(chk, v["pose"]):
                log(f"  capa IA: pose {v['pose']} reprovada ({chk})")
                v["reprovada"], mudou = True, True
                continue
            falas = list(tx.get("falas", {}).get(v["pose"]) or ["", ""])
            layout = v["layout"] if titulo else "baloes"
            alvo = Path(out_jpg) if not feitas else Path(out_jpg).with_name(
                Path(out_jpg).name.replace(".jpg", f"_v{len(feitas) + 1}.jpg"))
            feitas.append(_compor(img, layout, titulo, selo, falas, chk, alvo, fonte))
            meta.append({"arquivo": alvo.name, "pose": v["pose"], "layout": layout, "falas": falas})
        if mudou:
            _gravar(arq, pl)
        if len(feitas) >= n or not mudou or sem_cota:
            break
    if sem_cota:
        log(f"  capa IA: gateway e reserva não geraram todas — {len(feitas)} de {n} capa(s)")
    if feitas:
        _gravar(Path(out_jpg).with_suffix(".json"), {"obra": obra, "chave": chave, "idioma": idioma,
                                                    "variantes": meta})
        log(f"  capa IA: {len(feitas)} capa(s) — {', '.join(m['pose'] + '/' + m['layout'] for m in meta)}")
    return feitas


def capas_short(obra, selos, out_base, chave, fonte="LuckiestGuy-Regular.ttf", idioma="pt", roteiro=None, fala=None,
                n_img=2):
    """Capas 9:16 dos Shorts (720x1280): n_img imagens verticais com as poses/falas do plano do capítulo (o mesmo das
    capas 16:9; a imagem é outra) e UMA capa por Short com o selo dele (ex. "CAP. 7 • 3/8"), alternando as imagens.
    Saída <out_base>_p01.jpg, _p02.jpg... na ordem de `selos`. [] se não der (aí o Short sobe sem capa)."""
    c = _cfg_obra(obra)
    if not c or not c.get("ele") or not c.get("ela") or not selos:
        return []
    pl, arq = _plano(obra, c, chave, roteiro, n_img, "", fala)
    if not pl:
        return []
    tx = _textos(pl, arq, idioma)
    imgs = []
    for v in pl["variantes"]:
        if len(imgs) >= n_img:
            break
        if v.get("reprovada") or v.get("reprovada_vertical"):
            continue
        prompt = v["prompt"].replace(ENQUADRE.get(v["layout"], ENQUADRE["texto"]), ENQUADRE["vertical"])
        prompt = prompt.replace(ESTILO, ESTILO_VERTICAL) if ESTILO in prompt else prompt + " " + ESTILO_VERTICAL
        img = _gerar(prompt, "9:16", v["pose"])
        if not img:
            log(f"  capa IA (Short): sem imagem da pose {v['pose']} (gateway e reserva)")
            continue
        chk = _checar(img, v["pose"])
        if _reprovada(chk, v["pose"]):
            log(f"  capa IA (Short): pose {v['pose']} reprovada ({chk})")
            v["reprovada_vertical"] = True
            _gravar(arq, pl)
            continue
        imgs.append((img, chk, list(tx.get("falas", {}).get(v["pose"]) or ["", ""])))
    if not imgs:
        return []
    saidas = []
    for i, selo in enumerate(selos):
        img, chk, falas = imgs[i % len(imgs)]
        saidas.append(_compor(img, "baloes", "", selo, falas, chk, Path(f"{out_base}_p{i + 1:02d}.jpg"), fonte,
                              quadro=(VW, VH)))
    log(f"  capa IA (Short): {len(saidas)} capa(s) com {len(imgs)} imagem(ns)")
    return saidas


_SEXUAL = re.compile(r"sex|masturb|transa|goz|tes[aã]o|\bnua\b|\bnu\b|pelad|peito|seio|bunda|\bpau\b|pênis|buceta|"
                     r"porra|caralho|fod", re.I)


def fala_da_capa(falas, n_max=22):
    """A fala mais 'de capa' (curta, com ?/!) SEM palavra sexual — texto da miniatura também conta pra regra do
    YouTube. None se nenhuma servir."""
    import fx_acabamento as fa
    from narration import _so_som
    boas = [f for f in falas if f and not _SEXUAL.search(f) and not _so_som(f)
            and any(len(w) >= 4 for w in re.findall(r"[a-zà-ÿ]+", f.lower()))]  # gemido/"?! M-" não vira balão
    return fa._fala_curta(boas, n_max)


def obra_do_painel(painel):
    """'D:/.../panels/the-inheritor-cap05/panel_001.jpg' -> 'the-inheritor'."""
    return re.sub(r"-cap\d+$", "", Path(painel).parent.name)


def chave_do_painel(painel):
    """'D:/.../panels/the-inheritor-cap05/panel_001.jpg' -> 'cap05' (None se não tiver capítulo)."""
    m = re.search(r"-(cap\d+)$", Path(painel).parent.name)
    return m.group(1) if m else None


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--obra", required=True)
    ap.add_argument("--texto", default="")
    ap.add_argument("--selo", default="")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--chave", help="capítulo (ex. cap07): as línguas reaproveitam as imagens do mesmo plano")
    ap.add_argument("--narracao", help="roteiro do capítulo (workspace/narration_cache/...json): cenas e balão vêm dele")
    a = ap.parse_args()
    roteiro = fala = None
    if a.narracao:
        locs = json.loads(Path(a.narracao).read_text(encoding="utf-8")).get("locucoes", [])
        roteiro = "\n".join(f"{l.get('persona')}: {l.get('text')}" for l in locs)
        fala = fala_da_capa([l.get("text") for l in locs if l.get("gender") == "F"
                             and (l.get("persona") or "").lower() not in ("narrador", "narradora")])
    for p in capas(a.obra, a.texto, a.selo, a.saida, a.n, roteiro=roteiro, fala=fala, idioma=a.idioma, chave=a.chave):
        print(p)
