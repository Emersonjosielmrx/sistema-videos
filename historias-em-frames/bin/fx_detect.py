# -*- coding: utf-8 -*-
"""fx_detect.py — 'QUE CENA É ESTE PAINEL?' + escolha de SFX/foley + mood/overlay.
is_impact/tension/sensual_panel, pick_sfx*, pick_sfx_for_text (VRAA/REPROV/FOLEY/MEME maps),
get_transition_and_sfx, overlay_for_mood, detect_mood_from_text. SFX_DIR e pastas moram aqui.

Parte do motor de efeitos — mapa completo na fachada effects_engine.py.
Split mecânico verbatim do _PRE_SPLIT_effects_engine.py.bak (2026-07-04).
"""
import random
import subprocess
import os
import re
from pathlib import Path




# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4B: DETECÇÃO DE IMPACTO (pra decidir shake/sfx)
# ══════════════════════════════════════════════════════════════════════════

IMPACT_KEYWORDS = [
    "soco", "punch", "chute", "kick", "explosão", "explosion", "impacto",
    "impact", "quebr", "smash", "crash", "bate", "hit", "golpe", "strike",
    "pow", "bang", "slam", "ataque", "attack", "destr", "sangue", "blood",
    "grito", "scream", "tiro", "shot", "cai", "fall", "queda", "drop",
    "esmaga", "crush", "rasga", "rip", "corta", "cut", "faca", "knife",
    "espada", "sword", "luta", "fight", "morre", "kill", "rage", "fúria",
    "voando", "arremess", "jogou", "empurr", "choque", "colidiu", "batida",
    "pancada", "murro", "porrada", "nocaute", "ko", "desmaiou", "capotou",
]


def is_impact_panel(description: str) -> bool:
    """Detecta se o painel tem contexto de ação/impacto. Haiku primeiro, keyword fallback."""
    if not description:
        return False
    try:
        import haiku_helpers
        c = haiku_helpers.classify_action(description)
        if c is not None:
            return c == "impact"
    except Exception:
        pass
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in IMPACT_KEYWORDS)


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4C: SFX BANK (efeitos sonoros pra transições)
# ══════════════════════════════════════════════════════════════════════════

SFX_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx"
SFX_MEMES_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx_memes"
SFX_FOLEY_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx_foley"
# Pasta de SFX PRIORITÁRIOS (genéricos/atmosféricos — riser, drone, ambiência).
# Igual às trilhas prioritárias: o usuário arrasta pra cá os efeitos que quer ouvir
# mais. SFX ESPECÍFICOS (soco, porta, espada) NÃO entram aqui — eles são acionados
# direto por palavra-chave no FOLEY_DIRECT_MAP, sem sorteio.
SFX_PRIORIDADE_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx_prioridade"
# sfx_extras: 748 sons baixados, ficam na subpasta sonoros/. Antes NÃO eram usados.
SFX_EXTRAS_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx_extras" / "sonoros"
ALL_SFX_DIRS = [SFX_DIR, SFX_MEMES_DIR, SFX_FOLEY_DIR, SFX_EXTRAS_DIR]

# Duração de SFX em segundos, com cache (ffprobe é caro p/ chamar por clip).
_sfx_dur_cache = {}
def sfx_duration(path):
    """Retorna a duração (s) de um arquivo de áudio. Cacheada. 0.0 se falhar."""
    if not path:
        return 0.0
    key = str(path)
    if key in _sfx_dur_cache:
        return _sfx_dur_cache[key]
    dur = 0.0
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", key],
            capture_output=True, text=True, timeout=15)
        dur = float(out.stdout.strip() or 0.0)
    except Exception:
        dur = 0.0
    _sfx_dur_cache[key] = dur
    return dur

# ── Banco de SFX por MOOD (lê os *_categorized.json) ─────────────────────────
# Os JSONs mapeiam cada arquivo a uma categoria de clima (impacto/comedia/triste/
# suspense/romance/ambiente/transicao/sistema/neutro). Antes esse trabalho de
# categorização ficava IGNORADO — agora o pick_sfx_by_mood() usa pra escolher um
# som que combine com a cena em vez de sortear no escuro.
_SFX_MOOD_BANK = None  # cache: {categoria: [Path, ...]}

# tradução mood do vídeo (detect_mood_from_text) → categoria dos JSONs de SFX
MOOD_TO_SFX_CAT = {
    "tense_dramatic": "suspense", "sad_emotional": "tristeza",
    "romantic_sexy": "romance", "funny_lighthearted": "comedia",
    "calm_chill": "ambiente", "neutral_chill": "neutro", "action": "impacto",
}


def _load_sfx_mood_bank():
    """Lê os *_categorized.json e indexa os arquivos por categoria de clima.
    Resolve o caminho real de cada som (sfx_extras/sonoros, sfx_memes). Cacheado."""
    global _SFX_MOOD_BANK
    if _SFX_MOOD_BANK is not None:
        return _SFX_MOOD_BANK
    import json as _json
    bank = {}
    sources = [
        (SFX_DIR.parent / "sfx_extras_categorized.json", SFX_EXTRAS_DIR),
        (SFX_DIR.parent / "sfx_memes_categorized.json", SFX_MEMES_DIR),
    ]
    for json_path, base_dir in sources:
        if not json_path.exists():
            continue
        try:
            data = _json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for fname, cat in (data.get("files") or {}).items():
            f = base_dir / fname
            if f.exists():
                bank.setdefault(cat, []).append(f)
    _SFX_MOOD_BANK = bank
    return bank


def pick_sfx_by_mood(mood):
    """Sorteia um SFX cuja categoria combina com o mood do vídeo (via JSONs).
    Aplica anti-repetição. Retorna Path (str) ou None se não houver candidato."""
    global _last_sfx_used
    bank = _load_sfx_mood_bank()
    cat = MOOD_TO_SFX_CAT.get(mood)
    pool = bank.get(cat, []) if cat else []
    candidates = [f for f in pool if str(f) != _last_sfx_used] or pool
    if not candidates:
        return None
    chosen = random.choice(candidates)
    _last_sfx_used = str(chosen)
    return str(chosen)

# Categorias de SFX por contexto
SFX_IMPACT = [
    "impact.wav", "bass_hit.wav", "snap.wav",
    "new_impact_1.wav", "new_impact_2.wav",
    "whoosh_heavy.wav", "punch.wav", "thud.wav",
    "reverse_impact.wav", "deep_boom.wav",
]
SFX_TRANSITION = [
    "woosh.wav", "page_turn.wav", "riser.wav",
    "new_transition_1.wav", "new_transition_2.wav",
    "slide.wav", "swoosh_light.wav", "magic_sparkle.wav",
    "cinema_whoosh.wav", "paper_slide.wav", "subtle_click.wav",
    "dramatic_riser.wav", "tension_string.wav",
] + [f"whoosh_cinematic_{i:02d}.wav" for i in range(1, 26)]  # pack 25 (curadoria aprovada)
SFX_PAGE_TEAR = [
    "page_tear_1.wav", "page_tear_2.wav",
]

_last_sfx_used = None  # Anti-repetição: nunca repetir o mesmo SFX consecutivo

# TAREFA 18 (curadoria aprovada 2026-07-01): SFX disparados por CONTEXTO da narração.
# vraa = grito de transformação/virada épica; reprovação = erro/fracasso/"deu ruim".
# 7 e 5 variações → anti-repetição alterna (regra fixa #9). Ficam em SFX_DIR.
VRAA_POOL = [f"vraa_grito_{i:02d}.wav" for i in range(1, 8)]
VRAA_KEYWORDS = ["transform", "se transformou", "evoluiu", "despertou o poder",
                 "aura cresceu", "ficou mais forte", "virou outr", "subiu de nível",
                 "subiu de nivel", "level up", "vraa", "vrááá", "poder explod",
                 "liberou o poder", "modo besta", "se revelou"]
REPROV_POOL = [f"reprovacao_{i:02d}.wav" for i in range(1, 6)]
REPROV_KEYWORDS = ["deu ruim", "deu errado", "errou", "errado", "fracassou", "fracasso",
                   "reprovado", "reprovou", "não deu certo", "nao deu certo", "falhou",
                   "vacilou", "se ferrou", "deu merda", "foi mal", "que vergonha"]


def _pick_from_pool(pool_names, base_dir):
    """Escolhe um arquivo do pool (por nome), com anti-repetição consecutiva global.
    Reusa _last_sfx_used (mesma trava do pick_sfx). Retorna Path str válido ou None."""
    global _last_sfx_used
    cands = [base_dir / n for n in pool_names]
    cands = [p for p in cands if _valid_audio(p)]
    if not cands:
        return None
    filtered = [p for p in cands if str(p) != _last_sfx_used] or cands
    chosen = random.choice(filtered)
    _last_sfx_used = str(chosen)
    return str(chosen)


def pick_sfx(sfx_category=None):
    """Escolhe um SFX aleatório de uma categoria específica (IMPACT, TRANSITION, PAGE_TEAR).
    Garante que nunca repete o mesmo SFX consecutivamente."""
    global _last_sfx_used
    pool = SFX_TRANSITION # Default
    if sfx_category == "impact":
        pool = SFX_IMPACT
    elif sfx_category == "page_tear":
        pool = SFX_PAGE_TEAR

    # Tenta escolher um SFX do pool específico (diferente do último usado)
    sfx_file = None
    if pool:
        candidates = [SFX_DIR / f for f in pool if (SFX_DIR / f).exists()]
        # Filtrar o último usado pra não repetir
        if _last_sfx_used and len(candidates) > 1:
            candidates = [c for c in candidates if str(c) != _last_sfx_used] or candidates
        if candidates:
            sfx_file = random.choice(candidates)

    # Fallback: qualquer SFX disponível de TODAS as pastas.
    # SFX dentro de sfx_prioridade/ entram com PESO 3 (3× mais chance) — é o
    # controle manual do usuário: arrastar um efeito atmosférico pra essa pasta
    # faz ele tocar mais. Efeitos específicos (soco/porta) não passam por aqui.
    if not sfx_file:
        available = []
        for sfx_dir in ALL_SFX_DIRS:
            if sfx_dir.exists():
                available.extend([f for f in sfx_dir.glob("*.wav") if str(f) != _last_sfx_used])
                available.extend([f for f in sfx_dir.glob("*.mp3") if str(f) != _last_sfx_used])
        # Prioritários entram 3× (peso) se a pasta existir.
        if SFX_PRIORIDADE_DIR.exists():
            prio = [f for f in SFX_PRIORIDADE_DIR.glob("*.wav") if str(f) != _last_sfx_used]
            prio += [f for f in SFX_PRIORIDADE_DIR.glob("*.mp3") if str(f) != _last_sfx_used]
            available.extend(prio * 3)
        if not available:
            for sfx_dir in ALL_SFX_DIRS:
                if sfx_dir.exists():
                    available.extend(sfx_dir.glob("*.wav"))
                    available.extend(sfx_dir.glob("*.mp3"))
        if available:
            sfx_file = random.choice(available)

    if sfx_file:
        _last_sfx_used = str(sfx_file)

    return str(sfx_file) if sfx_file else None


# SFX contextual por keyword na narração (portado do n8n SOUND_EFFECTS_MAP)
SFX_CONTEXTUAL_MAP = {
    # AÇÃO E COMBATE
    "soco": {"category": "impact", "volume": 0.6, "keywords": ["soco", "murro", "pancada", "socou", "esmurrou"]},
    "tapa": {"category": "impact", "volume": 0.6, "keywords": ["tapa", "tapão", "esbofeteou", "estapeou"]},
    "explosão": {"category": "impact", "volume": 0.8, "keywords": ["explosão", "explodiu", "bomba", "detonou", "explode"]},
    "chute": {"category": "impact", "volume": 0.6, "keywords": ["chute", "chutou", "pontapé"]},
    "espada": {"category": "impact", "volume": 0.7, "keywords": ["espada", "lâmina", "cortou", "fatiou", "katana"]},
    # IMPACTO E QUEDAS
    "queda": {"category": "impact", "volume": 0.6, "keywords": ["caiu", "cair", "queda", "tropeçou", "desabou", "escorregou"]},
    "quebrou": {"category": "impact", "volume": 0.6, "keywords": ["quebrou", "vidro", "estilhaçou", "partiu", "rachou"]},
    "bateu": {"category": "impact", "volume": 0.6, "keywords": ["bateu", "colidiu", "impacto", "trombou"]},
    # EMOÇÕES E REAÇÕES
    "grito": {"category": "impact", "volume": 0.6, "keywords": ["grito", "gritou", "berrou", "urrou", "berro"]},
    "surpresa": {"category": "transition", "volume": 0.5, "keywords": ["surpresa", "surpreso", "chocado", "não acredito", "impossível"]},
    "risada": {"category": "transition", "volume": 0.5, "keywords": ["risada", "riso", "riu", "gargalhada", "haha"]},
    # SUSPENSE E DRAMA
    "suspense": {"category": "transition", "volume": 0.5, "keywords": ["suspense", "tensão", "perigo", "ameaça", "sombrio"]},
    "revelação": {"category": "transition", "volume": 0.6, "keywords": ["revelação", "segredo", "descobriu", "verdade", "revelou"]},
    "morte": {"category": "impact", "volume": 0.7, "keywords": ["morte", "morreu", "matar", "matou", "assassin"]},
    # MOVIMENTO
    "correr": {"category": "transition", "volume": 0.4, "keywords": ["correr", "correndo", "fugir", "escapar", "rápido", "velocidade"]},
    "pular": {"category": "transition", "volume": 0.5, "keywords": ["pular", "pulou", "salto", "saltou", "voou"]},
    # AMBIENTE
    "porta": {"category": "transition", "volume": 0.4, "keywords": ["porta", "bateu a porta", "abriu a porta", "fechou", "portão"]},
    "coração": {"category": "transition", "volume": 0.4, "keywords": ["coração", "batendo", "palpitou", "acelerou", "coração disparou"]},
    "trovão": {"category": "impact", "volume": 0.7, "keywords": ["trovão", "raio", "relâmpago", "tempestade"]},
    "água": {"category": "transition", "volume": 0.4, "keywords": ["água", "chuva", "mergulho", "afogando", "rio"]},
    "vento": {"category": "transition", "volume": 0.3, "keywords": ["vento", "ventania", "tempestade", "soprou"]},
    # === T8: GATILHOS NOVOS (categorias do n8n que faltavam → SÓ pools que temos) ===
    # MAGIA / SOBRENATURAL (→ magic_sparkle/sparkle vivem em SFX_TRANSITION)
    "magia": {"category": "transition", "volume": 0.5, "keywords": ["magia", "mágic", "feitiço", "feitic", "encanto", "conjur", "poder mágico", "sobrenatural", "místic", "mistic"]},
    "teleporte": {"category": "transition", "volume": 0.5, "keywords": ["teleport", "desapareceu", "sumiu", "surgiu do nada", "materializ", "portal abriu"]},
    "transformação": {"category": "transition", "volume": 0.6, "keywords": ["transform", "se transformou", "metamorf", "evoluiu", "virou outr"]},
    # GAME / POWER (→ impact pra força, transition pra brilho)
    "powerup": {"category": "transition", "volume": 0.6, "keywords": ["upou", "subiu de nível", "subiu de nivel", "level up", "power up", "powerup", "ficou mais forte", "despertou o poder", "aura cresceu"]},
    "derrota": {"category": "impact", "volume": 0.6, "keywords": ["foi derrotado", "perdeu a luta", "caiu derrotado", "game over", "wasted", "fim de jogo"]},
    "vitória": {"category": "transition", "volume": 0.6, "keywords": ["venceu", "vitória", "vitoria", "ganhou", "triunf", "conquistou", "campeão", "campeao"]},
    # NOTIFICAÇÃO / DISPOSITIVO (→ subtle_click/snap em transition)
    "notificação": {"category": "transition", "volume": 0.4, "keywords": ["notificação", "notificac", "mensagem chegou", "celular tocou", "alerta", "ping", "tocou o telefone"]},
}

# Mapa direto keyword → foley específico (prioridade sobre SFX genérico)
FOLEY_DIRECT_MAP = {
    "porta": "door_close.wav", "abriu a porta": "door_close.wav", "fechou a porta": "door_close.wav",
    "passos": "footsteps.wav", "andando": "footsteps.wav", "caminh": "footsteps.wav",
    "beijo": "kiss_smooch.wav", "beijou": "kiss_smooch.wav", "beijar": "kiss_smooch.wav",
    "coração": "heartbeat.wav", "batendo forte": "heartbeat.wav", "palpitou": "heartbeat.wav",
    "chuva": "rain_loop.wav", "chov": "rain_loop.wav",
    "trovão": "thunder.wav", "raio": "thunder.wav", "relâmpago": "thunder.wav",
    "vento": "wind_blow.wav", "ventania": "wind_blow.wav",
    "espada": "sword_slash.wav", "katana": "sword_slash.wav", "lâmina": "sword_hit.wav",
    "tiro": "gunshot.wav", "atirou": "gunshot.wav", "pistola": "gunshot_echo.wav",
    "vidro": "glass_break.wav", "estilhaçou": "glass_break.wav",
    "caiu": "body_fall.wav", "desabou": "body_fall.wav", "corpo caiu": "body_fall.wav",
    "explosão": "explosion_big.wav", "explodiu": "explosion_big.wav",
    "comendo": "eating_crunch.wav", "mordeu": "eating_crunch.wav", "mastig": "eating_crunch.wav",
    "bebendo": "drinking_gulp.wav", "engoliu": "drinking_gulp.wav", "gole": "drinking_gulp.wav",
    "telefone": "phone_ring.wav", "celular": "phone_ring.wav", "ligou": "phone_ring.wav",
    "corrente": "chain_rattle.wav", "pres": "chain_rattle.wav",
    "metal": "metal_clang.wav", "ferro": "metal_clang.wav",
    "mar": "ocean_waves.wav", "praia": "ocean_waves.wav", "ondas": "ocean_waves.wav",
    "pássaro": "birds_morning.wav", "manhã": "birds_morning.wav",
    "aplausos": "crowd_cheer.wav", "plateia": "crowd_cheer.wav", "torcida": "crowd_cheer.wav",
    "espanto": "crowd_gasp.wav", "todos ficaram": "crowd_gasp.wav",
    "sinistro": "creepy_ambience.wav", "arrepio": "creepy_ambience.wav",
    "escrevendo": "pen_writing.wav", "anotou": "pen_writing.wav",
    "tensão": "tension_drone.wav",
    # Foley extras
    "soco": "punch_hit.wav", "socou": "punch_hit.wav", "murro": "punch_hit.wav",
    "notificação": "notification.wav", "mensagem": "notification.wav", "alerta": "notification.wav",
    # Foley adicionais (arquivos confirmados em sfx_foley/)
    "explosão pequena": "explosion_small.wav", "estouro": "explosion_small.wav",
    "rápido": "fast_whoosh.wav", "disparou": "fast_whoosh.wav", "veloz": "fast_whoosh.wav",
    "devagar": "slow_whoosh.wav", "lentamente": "slow_whoosh.wav",
    "espada cortou": "sword_hit.wav", "golpe de espada": "sword_hit.wav",
    "comeu": "eating_crunch.wav", "mordida": "eating_crunch.wav",
}


# Efeitos da pasta sfx_memes acionados DIRETO por palavra-chave (estilo "humor
# brasileiro"). keyword (na narração) → nome EXATO do arquivo em sfx_memes/.
# Diferente do FOLEY_DIRECT_MAP (sons realistas), estes são cômicos/expressivos.
# Só mapeei os de nome claro; os 600+ restantes seguem disponíveis pelo sorteio
# por mood/categoria (pick_sfx). Adicione mais pares aqui conforme quiser.
MEME_SFX_DIRECT_MAP = {
    "chicote": "37- Chicote.mp3", "chibatada": "37- Chicote.mp3",
    "buzina": "30- Buzina.mp3", "buzinou": "30- Buzina.mp3",
    "tapa": "Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3",
    "bofetada": "Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3",
    "beijo": "Som de Beijo - Efeitos Sonoros Nerzinho.mp3",
    "moeda": "Efeitos Sonoros - Moeda caindo.mp3", "moedas": "Efeitos Sonoros - Moeda caindo.mp3",
    "dinheiro": "26- Dinheiro 2.mp3", "grana": "26- Dinheiro 2.mp3",
    "freio": "SE EU LARGAR O FREIO.mp3", "freada": "SE EU LARGAR O FREIO.mp3",
    "errou": "25- Errou.mp3", "errado": "25- Errou.mp3",
    "suspense": "9- Suspense 2.mp3",
    "risada": "Bixo Piruleta Risada - Efeitos sonoros Nerzinho.mp3", "gargalhada": "Bixo Piruleta Risada - Efeitos sonoros Nerzinho.mp3",
    "grito": "Grito - Efeitos sonoros Nerzinho.mp3", "gritou": "Grito - Efeitos sonoros Nerzinho.mp3",
    "campainha": "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3", "ding dong": "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3",
    "ding-dong": "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3", "interfone": "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3",
    "campainha toca": "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3",
    # Fallbacks pra foleys QUEBRADOS (door_open/footsteps/punch_hit = XML 111B):
    "passos": "Minecraft som de passos - Efeitos sonoros Nerzinho.mp3",
    "step step": "Minecraft som de passos - Efeitos sonoros Nerzinho.mp3",
    "passo a passo": "Minecraft som de passos - Efeitos sonoros Nerzinho.mp3",
    "abriu a porta": "Minecraft Porta abrindo - Efeitos sonoros Nerzinho.mp3",
    "porta se abre": "Minecraft Porta abrindo - Efeitos sonoros Nerzinho.mp3",
    "porta abrindo": "Minecraft Porta abrindo - Efeitos sonoros Nerzinho.mp3",
    "bate na porta": "Batendo na Porta - Efeitos sonoros Nerzinho.mp3",
    "batida na porta": "Batendo na Porta - Efeitos sonoros Nerzinho.mp3",
    "batem na porta": "Batendo na Porta - Efeitos sonoros Nerzinho.mp3",
    "soco": "Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3",
    "murro": "Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3",
    "socou": "Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3",
    "carro": "Carro Buzinando - Efeitos sonoros Nerzinho.mp3",
    "teclado": "Digitando teclado - Efeitos sonoros Nerzinho.mp3", "digitando": "Digitando teclado - Efeitos sonoros Nerzinho.mp3", "digitou": "Digitando teclado - Efeitos sonoros Nerzinho.mp3",
    "trovão": "Trovão - Efeitos Sonoros Nerzinho.mp3", "trovao": "Trovão - Efeitos Sonoros Nerzinho.mp3",
    "vidro": "Vidro Quebrando -  Efeito Sonoro.mp3", "vidro quebrou": "Vidro Quebrando -  Efeito Sonoro.mp3", "quebrou o vidro": "Vidro Quebrando -  Efeito Sonoro.mp3",
    "tiro": "Tiro - Efeitos Sonoros Nerzinho.mp3", "atirou": "Tiro - Efeitos Sonoros Nerzinho.mp3", "disparo": "Tiro - Efeitos Sonoros Nerzinho.mp3",
    "máquina de escrever": "Maquina de Escrever - Efeitos sonoros Nerzinho.mp3", "datilograf": "Maquina de Escrever - Efeitos sonoros Nerzinho.mp3",
    "whatsapp": "Assobio do whatsapp _ zap zap_ toque whatsapp_ whistle (donwload) ----(MP3_320K).mp3", "zap": "Assobio do whatsapp _ zap zap_ toque whatsapp_ whistle (donwload) ----(MP3_320K).mp3",
}


def _valid_audio(path):
    """True se o arquivo de áudio é válido (não um XML de erro de ~111B).
    Vários foleys baixados falharam e ficaram como '<?xml...' disfarçado de wav."""
    try:
        p = Path(path)
        if not p.exists() or p.stat().st_size < 1000:
            return False
        with open(p, "rb") as fh:
            head = fh.read(4)
        # wav=RIFF, mp3=ID3 ou 0xFFFx, ogg=OggS. XML de erro começa com '<'
        return head[:1] != b"<"
    except Exception:
        return False



def _kw_match(blob, kw):
    """Casa keyword com limite de palavra (evita 'mar' casar 'marcam',
    'rápido' casar dentro de outra). Keywords multi-palavra ou com pontuação
    usam substring; tokens simples usam fronteira de palavra."""
    if " " in kw or "-" in kw:
        return kw in blob
    return re.search(r'(?<![0-9a-zà-ú])' + re.escape(kw) + r'(?![0-9a-zà-ú])', blob) is not None


# Onomatopeias das DESCRIÇÕES → SFX (prioridade MÁXIMA: é o som literal do que
# acontece na cena). Ex.: "DING DONG" sempre vence "rápido"/"acaba" genéricos.
ONOMATOPEIA_SFX = [
    (["ding dong", "ding-dong"], ("memes", "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3", 0.55)),
    (["step step", "step"], ("memes", "Minecraft som de passos - Efeitos sonoros Nerzinho.mp3", 0.45)),
    (["clack", "clack clack"], ("foley", "door_close.wav", 0.5)),
    (["smooch", "chu~", "chu "], ("foley", "kiss_smooch.wav", 0.5)),
    (["knock", "toc toc", "tum tum"], ("memes", "Batendo na Porta - Efeitos sonoros Nerzinho.mp3", 0.5)),
    (["crash", "smash", "estilha"], ("memes", "Vidro Quebrando -  Efeito Sonoro.mp3", 0.55)),
    (["bang", "pow"], ("memes", "Tiro - Efeitos Sonoros Nerzinho.mp3", 0.5)),
]


def _sfx_fits_scene(desc, sfx_path):
    """Veta (via gateway/Haiku) um SFX que a keyword casou mas não combina com a cena.
    Retorna True se cabe OU se não há como decidir (gateway off/desc vazia) — só veta
    quando o modelo diz explicitamente que NÃO cabe. Nunca quebra o fluxo."""
    if not desc or not sfx_path:
        return True
    try:
        import haiku_helpers
        verdict = haiku_helpers.sfx_fits(desc, Path(sfx_path).name)
        return verdict is not False  # None (indeciso) ou True → mantém
    except Exception:
        return True


def pick_sfx_for_text(text, desc=""):
    """Escolhe SFX baseado no conteúdo do texto da narração + descrição.
    Prioridade: onomatopeia > foley direto > MEME direto > keyword contextual.
    Retorna (sfx_path, volume) ou (None, None) se não encontrar match.

    Se `desc` for fornecida e o gateway estiver ativo, um SFX casado por keyword é
    VETADO quando claramente não cabe na cena (reduz 'salada' de efeitos)."""
    if not text:
        return None, None
    text_lower = text.lower()

    # 0. Onomatopeia literal da descrição (prioridade máxima)
    for kws, (kind, fname, vol) in ONOMATOPEIA_SFX:
        if any(_kw_match(text_lower, k) for k in kws):
            base = SFX_MEMES_DIR if kind == "memes" else SFX_FOLEY_DIR
            p = base / fname
            if _valid_audio(p):
                return str(p), vol
            break

    # 1. Foley direto (alta prioridade — sons específicos e realistas)
    for keyword, foley_file in FOLEY_DIRECT_MAP.items():
        if _kw_match(text_lower, keyword):
            foley_path = SFX_FOLEY_DIR / foley_file
            if _valid_audio(foley_path) and _sfx_fits_scene(desc, foley_path):
                return str(foley_path), 0.6
            # arquivo quebrado/ausente/vetado → tenta próximas camadas
            break

    # 1b. MEME direto (efeitos da pasta sfx_memes acionados por palavra-chave).
    #     São os 600+ efeitos "engraçados/brasileiros" (chicote, buzina, tapa,
    #     risada...). Volume um pouco mais baixo (0.5) por serem mais chamativos.
    for keyword, meme_file in MEME_SFX_DIRECT_MAP.items():
        if _kw_match(text_lower, keyword):
            meme_path = SFX_MEMES_DIR / meme_file
            if _valid_audio(meme_path) and _sfx_fits_scene(desc, meme_path):
                return str(meme_path), 0.5
            break

    # 1c. TAREFA 18: vraa (transformação/virada) e reprovação (erro/fracasso) por CONTEXTO.
    #     Disparo por keyword (não sorteio genérico). Depois do foley/meme direto, antes do
    #     contextual — são sons de DESTAQUE, ganham do genérico quando o contexto casa.
    for kw in VRAA_KEYWORDS:
        if _kw_match(text_lower, kw):
            p = _pick_from_pool(VRAA_POOL, SFX_DIR)
            if p:
                return p, 0.7
            break
    for kw in REPROV_KEYWORDS:
        if _kw_match(text_lower, kw):
            p = _pick_from_pool(REPROV_POOL, SFX_DIR)
            if p:
                return p, 0.6
            break

    # 2. Keyword contextual (SFX genérico por categoria)
    for key, config in SFX_CONTEXTUAL_MAP.items():
        for keyword in config["keywords"]:
            if _kw_match(text_lower, keyword):
                sfx = pick_sfx(config["category"])
                return sfx, config["volume"]

    # 3. SEM fallback por mood. Decisão do usuário (28/jun): efeito sonoro só
    #    entra quando a narração tem CONTEXTO pra ele (keyword) — tiro só quando
    #    "atirou", tapa só quando "tapa", etc. Sem keyword, NÃO sobrepõe efeito:
    #    o clip mantém o som de transição LIMPO (whoosh/riser) do
    #    get_transition_and_sfx. Isso evita a "salada" de memes-fala e SFX
    #    especiais (Wilhelm Scream, "11 - Arma 2", falas) tocando aleatoriamente
    #    como fundo. (Antes: pick_sfx_by_mood sorteava da categoria 'neutro' que
    #    é 336 memes-fala não-curados → atropelava as vozes.)
    return None, None

# Tensão keywords (shake + glitch em momentos tensos, não só impacto)
TENSION_KEYWORDS = [
    "tensão", "tenso", "nervos", "medo", "assust", "choque", "revela",
    "segredo", "surpres", "descobre", "traição", "mentir", "ameaça",
    "confronto", "encurralad", "perigo", "desespero", "pânico", "furioso",
    "raiva", "ciúme", "obsess", "stalker", "persegu", "escuro", "sombr",
    "suspeito", "olhar frio", "silêncio pesado", "calafrio", "arrepio",
    "tremendo", "lágrima", "choqu", "apavorad", "terror", "sinistro",
    "ameaçador", "intimidar", "pressionad", "acuad", "encosta na parede",
]


def is_tension_panel(description: str) -> bool:
    """Detecta se o painel tem tensão dramática. Haiku primeiro, keyword fallback."""
    if not description:
        return False
    try:
        import haiku_helpers
        c = haiku_helpers.classify_action(description)
        if c is not None:
            return c == "tension"
    except Exception:
        pass
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in TENSION_KEYWORDS)


# Sensual/+18 keywords. "cena intensa"/"intensa" é o marcador deixado pela
# sanitização da visão quando o painel tinha conteúdo adulto explícito.
SENSUAL_KEYWORDS = [
    "cena intensa", "intensa", "beijo", "beij", "abraç", "carícia", "caric",
    "toque", "toca", "sedut", "seduz", "sensual", "provocan", "provoca",
    "desejo", "tesão", "paixão", "íntim", "intim", "corpo", "pele",
    "quente", "ofegant", "suspiro", "gemid", "cama", "lençol", "nu ",
    "deitad", "abraçad", "colo", "peito", "coxa", "cintura", "vermelh",
    "nervos", "tímid", "noona", "amante", "romance", "romântic",
]


def is_sensual_panel(description: str = "", text: str = "") -> bool:
    """Detecta momentos sensuais/+18 (pra aplicar voz sensual no TTS).

    Olha tanto a descrição visual (sanitizada → 'cena intensa') quanto o texto
    da narração, que costuma ter as pistas românticas/provocantes.
    """
    blob = f"{description} {text}".lower()
    if not blob.strip():
        return False
    return any(kw in blob for kw in SENSUAL_KEYWORDS)


def get_transition_and_sfx(panel_idx, descriptions):
    """Determina o tipo de transição e o SFX para um painel específico.

    Transições FREQUENTES e VARIADAS (estilo Shorts) — quase todo corte tem efeito:
    - impacto → flash vermelho / branco / zoom punch / whip + SFX de impacto
    - tensão  → glitch / blur-in / fade preto / rasgar página / rebobinar + SFX de transição
    - normal  → variedade (fade/blur/pixel/whip/flash) + uns cortes secos + SFX de transição
    """
    if panel_idx == 0:
        return None, None

    desc = descriptions[panel_idx] if panel_idx < len(descriptions) else ""
    impact = is_impact_panel(desc)
    tension = is_tension_panel(desc)

    transition_type = None
    sfx_category = "transition" # default
    sfx_file = None

    if impact:
        transition_type = random.choice(["flashred", "flash", "flashgold", "zoomin", "whip", "glitch", "punch", "snap", "speedblur", "zoomout"])
        sfx_category = "impact"
    elif tension:
        r_val = random.random()
        if r_val < 0.20:
            transition_type = "pagetear"
            sfx_category = "page_tear"
        elif r_val < 0.40:
            transition_type = "rewind"
            _rz = "rezero_respawn.wav" if (SFX_DIR / "rezero_respawn.wav").exists() and random.random() < 0.5 else "rezero_rewind.wav"
            sfx_file = str(SFX_DIR / _rz)
        elif r_val < 0.55:
            transition_type = "speedblur"
            sfx_category = "impact"
        else:
            transition_type = random.choice(["glitch", "blurin", "fade", "flashblue", "zoomin", "snap"])
            sfx_category = "transition"
    else:
        # variedade pros cortes normais; ~1/10 ficam corte seco pra dar respiro
        if random.random() < 0.10: # 10% de chance de corte seco
            transition_type = None # Corte seco
            sfx_category = None # Sem SFX para corte seco
        else:
            transition_type = random.choice([
                "fade", "dissolve", "wipeleft", "wiperight", "wipeup", "wipedown",
                "slideleft", "slideright", "slideup", "slidedown",
                "smoothleft", "smoothright", "smoothup", "smoothdown",
                "pixelize", "zoomin", "squeezeh", "squeezev",
                "circleopen", "circleclose", "circlecrop",
                "diagtl", "diagtr", "diagbl", "diagbr",
                "fadefast", "fadeslow", "snap", "distance",
                "horzopen", "horzclose", "vertopen", "vertclose",
                "radial",
            ])
            sfx_category = "transition"

    if sfx_file is None:
        sfx_file = pick_sfx(sfx_category)

    return transition_type, sfx_file


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4F: OVERLAYS ATMOSFÉRICOS (chuva/neve/faíscas/pétalas) por mood
# ══════════════════════════════════════════════════════════════════════════

OVERLAYS_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "overlays"

# mood → overlay (partícula atmosférica que combina com o clima da cena).
# Igual à trilha, o overlay é escolhido pelo MOOD detectado — não há "prioridade"
# entre eles, mas cada clima tem a partícula que faz sentido:
#   rain (chuva)      → tristeza / drama melancólico
#   petals (pétalas)  → romance / fofura
#   sparks (faíscas)  → tensão / suspense
#   snow (neve)       → calmo / contemplativo
#   speedlines        → AÇÃO / IMPACTO (linhas de velocidade estilo mangá)
# Vários moods podem apontar pro mesmo arquivo (ex.: ação e impacto → speedlines).
MOOD_OVERLAY = {
    "sad_emotional": "rain",
    "romantic_sexy": "petals",
    "tense_dramatic": "sparks",
    "calm_chill": "snow",
    "neutral_chill": "snow",
    # ação / impacto → linhas de velocidade
    "action": "speedlines",
    "impact": "speedlines",
    "funny_lighthearted": "petals",
}


# Overlay pelo que a CENA descreve (texto PT + image_prompt EN). Pelo humor sozinho saia
# neve caindo numa sala ensolarada (calm_chill -> snow) e chuva dentro de casa (sad -> rain).
_OVERLAY_TEXTO = [
    ("snow", r"\bnev|inverno|nevasca|floco|\bsnow|winter|blizzard"),
    ("rain", r"\bchuv|\bchov|tempestade|garoa|temporal|\brain|storm|drizzle"),
    ("sparks", r"\bfogo\b|fa[ií]sc|fogueira|inc[eê]ndio|brasa|forja|explos|\bfire\b|spark|ember|blaze"),
    ("petals", r"p[eé]tala|\bflor(es)?\b|cerejeira|sakura|primavera|petal|blossom|cherry tree"),
]


def overlay_para_cena(texto, mood, chance=0.6):
    """Overlay atmosferico que COMBINA com a cena (ver _OVERLAY_TEXTO), ou None.
    Sem elemento citado: so speedlines em acao/impacto e petalas em romance (30%)."""
    t = (texto or "").lower()
    for nome, rx in _OVERLAY_TEXTO:
        if re.search(rx, t):
            f = OVERLAYS_DIR / f"{nome}.mp4"
            return str(f) if f.exists() and random.random() < chance else None
    extra = {"action": "speedlines", "impact": "speedlines", "romantic_sexy": "petals"}.get(mood)
    if extra and random.random() < 0.3:
        f = OVERLAYS_DIR / f"{extra}.mp4"
        return str(f) if f.exists() else None
    return None


def overlay_for_mood(mood, chance=0.3):
    """Escolhe um overlay atmosférico pelo mood (com `chance` de NÃO aplicar nenhum).

    - Retorna o caminho do .mp4 do overlay que combina com o clima, ou None.
    - `chance` = probabilidade de aplicar (0.3 = 30% dos clips ganham overlay).
      Mantido baixo de propósito: overlay em todo clip cansa a vista.
    - Se o mood não tiver overlay mapeado (ou o arquivo não existir), retorna None.
    """
    if mood not in MOOD_OVERLAY:
        return None
    if random.random() > chance:
        return None
    overlay_name = MOOD_OVERLAY[mood]
    overlay_file = OVERLAYS_DIR / f"{overlay_name}.mp4"
    return str(overlay_file) if overlay_file.exists() else None


def detect_mood_from_text(text):
    """Detecta mood dominante de um texto. Tenta Haiku primeiro (entende contexto/
    ironia); se indisponível/falhar, cai no scoring por keywords (300+ palavras)."""
    try:
        import haiku_helpers
        m = haiku_helpers.detect_mood(text)
        if m:
            # 'action' do Haiku mapeia pro mood mais próximo do pipeline
            return "tense_dramatic" if m == "action" else m
    except Exception:
        pass
    text_lower = text.lower()
    scores = {"tense_dramatic": 0, "sad_emotional": 0, "romantic_sexy": 0,
              "funny_lighthearted": 0, "calm_chill": 0, "neutral_chill": 0}
    keywords = {
        "tense_dramatic": [
            "luta","batalha","medo","terror","perigo","tensão","morte","sangue","raiva",
            "ódio","fúria","matar","ameaça","violência","soco","golpe","destruir","arma",
            "tiro","guerra","vingança","traição","assassin","inimigo","demônio","monstro",
            "ataque","defesa","poder","explosão","grito","confronto","desafio","rival",
            "espada","faca","veneno","armadilha","emboscada","sequestro","refém","ameaçar",
            "fugi","perseguição","caçar","prender","capturar","invasão","destruição",
            "apocalipse","inferno","pesadelo","agonia","desesper","pavor","horror",
            "amaldiçoar","maldição","sombr","escuridão","trevas","caos","cruel",
            "tortura","ferido","machucado","cicatriz","queimad","envenenad","sufocad",
        ],
        "sad_emotional": [
            "chora","lágrima","triste","dor","sofr","morreu","saudade","solidão",
            "abandonad","separação","perdeu","luto","despedida","adeus","nunca mais",
            "sozinho","vazio","depressão","angústia","melancol","nostalgia","arrependimento",
            "culpa","perdão","desculpa","sinto muito","coitad","injusto","cruel destino",
            "sacrifício","partida","funeral","túmulo","memória","lembrança","chorand",
            "desabou","quebrou por dentro","coração partido","não aguento","demais pra mim",
        ],
        "romantic_sexy": [
            "amor","beijo","abraço","coração","paixão","seduz","carinho","te amo",
            "namorad","crush","romântic","lindo","linda","bonit","olhos","sorriso",
            "toque","mão","sussurro","intimidade","desejo","quero você","atraente",
            "encantad","apaixonad","ciúme","declaração","anel","casamento","encontro",
            "jantar","vinho","rosa","flor","perfume","corpo","pele","lábios","cabelo",
            "dançar","noite","lua","estrela","juntos","nós dois","sempre","pra sempre",
        ],
        "funny_lighthearted": [
            "rir","risada","engraçad","piada","haha","kkkk","zueira","brincadeir",
            "idiota","meme","eita","oxe","caramba","uai","mano","nossa","vergonha",
            "constrang","trapalhada","confusão","ridícul","bizarro","absurd","maluco",
            "doido","palhaçada","zoar","trollar","pegadinha","gafe","bobagem","besteira",
            "ué","hein","wtf","loucura","surreal","impossível","inacreditável","sério isso",
            "tô rindo","morri","não tanko","perdi tudo","genial","mitou","lendário",
            "lacrou","arrasar","poderosa","empoderad","rainha","diva","slayou",
            "mandou bem","arrasou","top","incrível","magnífico","show","brilhou",
        ],
        "calm_chill": [
            "calmo","paz","tranquil","sereno","silêncio","café","escola","casa","normal",
            "rotina","trabalho","escritório","mesa","cadeira","livro","estudo","aula",
            "professor","aluno","biblioteca","conversa","papo","bate-papo","diálogo",
            "explicar","entender","pensar","refletir","meditar","plano","estratégia",
            "preparar","treinar","praticar","cozinhar","comida","almoço","jantar",
            "amigo","colega","companheiro","parceiro","equipe","sorrindo","satisfeito",
            "aliviado","bonito dia","sol","céu","nuvem","brisa","natureza","árvore",
            "rio","lago","montanha","jardim","parque","caminhada","passeio","relaxar",
        ],
    }
    import re as _re
    for mood, words in keywords.items():
        for w in words:
            if len(w) <= 4:
                if _re.search(r'\b' + _re.escape(w), text_lower):
                    scores[mood] += 1
            else:
                if w in text_lower:
                    scores[mood] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "neutral_chill"
