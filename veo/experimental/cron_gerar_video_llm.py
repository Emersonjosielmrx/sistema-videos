# -*- coding: utf-8 -*-
"""Cron autonoma INTELIGENTE: gera 1 video Veo por execucao usando LLM.

Diferencas vs cron_gerar_video.py:
- Usa llm_client (Gemini Flash Lite ou OpenAI-compat) para gerar falas virais
- Tambem usa LLM para descrever cenario em ingles (otimizado para Veo)
- Mantem fallback automatico para lista estatica se LLM falhar
- Log indica fonte: 'llm' ou 'fallback'

Uso:
  # com LLM (Gemini):
  set GOOGLE_API_KEY=AIza...
  python cron_gerar_video_llm.py

  # com OpenAI-compat:
  set LLM_BASE_URL=http://localhost:1234/v1
  set LLM_API_KEY=lm-studio
  set LLM_MODEL=qwen2.5-7b-instruct
  python cron_gerar_video_llm.py

  # sem LLM (so fallback - mesmo comportamento do antigo):
  set LLM_DISABLED=1
  python cron_gerar_video_llm.py
"""
import os, sys, random, subprocess, glob, datetime, json

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# Independente: fotos em <raiz>/fotos (raiz = pai do ambiente). Override VEO_FOTOS.
# SEM fallback pra hipercool — o projeto roda mesmo se outra pasta for apagada.
_RAIZ = os.path.dirname(BASE)  # D:\veo
FOTOS_DIR = os.environ.get("VEO_FOTOS", os.path.join(_RAIZ, "fotos"))
VIDEOS_DIR = os.path.join(BASE, "videos", "cron_shorts")
LOG_FILE = os.path.join(BASE, "logs", "cron_gerar_llm.log")
HIST_FILE = os.path.join(BASE, "logs", "cron_gerar_video_llm.hist.json")
CACHE_FILE = os.path.join(BASE, "logs", "video_cache.json")  # formula de cada video
SESSOES_FILE = os.path.join(BASE, "logs", "sessoes_status.json")  # controle de failover

# Defaults Flow (podem ser sobrescritos pela bat ou env)
os.environ.setdefault("FLOW_SESSION", "seebotsia")
os.environ.setdefault("FLOW_PROJ", "https://labs.google/fx/pt/tools/flow")
os.environ.setdefault("FLOW_ASPECT", "9:16")
os.environ.setdefault("FLOW_MODEL", "Veo 3.1 - Fast")
os.environ.setdefault("FLOW_DURATION", "8S")
os.environ.setdefault("FLOW_PORT", "9250")
os.environ.setdefault("FLOW_PROFILE", "chrome_gen_seebotsia")

# Pool de sessoes (failover automatico).
# FONTE UNICA: contas.py. Nao redefina a lista aqui — edite contas.py.
from contas import SESSOES
import recursos  # sensor de RAM/CPU pra timeout dinamico e pool adaptativo
try:
    from notifica import avisar_desktop  # pop-up no canto da tela
except Exception:
    def avisar_desktop(t, m):  # fallback: no-op se o modulo faltar
        pass

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

CANAIS = [
    {"nome": "ReCenas IA", "tema": "Releitura de Cenas Famosas"},
    {"nome": "Aulas IA", "tema": "Micro-aulas e Tutoriais"},
    {"nome": "Cassetadas IA", "tema": "Erros da IA (AI Fails)"},
    {"nome": "AlucinaAI", "tema": "Visuais Psicodelicos"},
    {"nome": "Cerebro Digital", "tema": "Trocadilhos Visuais Literais"},
    {"nome": "Fofos e Absurdos", "tema": "Fofura em Situacoes Bizarras"},
    {"nome": "Motivacao IA", "tema": "Citacoes Motivacionais"},
    {"nome": "Curiosidades IA", "tema": "Fatos Rapidos Chocantes"},
    {"nome": "Danca e Musica IA", "tema": "Visualizacao de Musica"},
    {"nome": "Dicas Financeiras", "tema": "Educacao Financeira"},
    {"nome": "Mitos vs Verdades", "tema": "Desmentindo Mitos"},
    {"nome": "Fatos Bizarros", "tema": "Curiosidades Estranhas"},
    {"nome": "Corpo Humano", "tema": "Fatos Medicos e Biologicos"},
    {"nome": "Segredos do Oceano", "tema": "Talassofobia e Vida Marinha"},
    {"nome": "Dicas Fitness", "tema": "Exercicios e Nutricao"},
    {"nome": "Noticias de IA", "tema": "Noticias sobre Inteligencia Artificial"},
    {"nome": "Recordes Mundiais", "tema": "Visualizacao de Recordes"},
    {"nome": "Stand-up IA", "tema": "Piadas contadas por IA"},
    {"nome": "E Se...", "tema": "Cenarios Hipoteticos"},
    {"nome": "Humor de IA", "tema": "Humor Nonsense e Surreal"},
    {"nome": "Ilusoes de Otica", "tema": "Ilusoes e Puzzles Visuais"},
    {"nome": "Transformacao", "tema": "Morphing Satisfatorio"},
    {"nome": "Super Slow IA", "tema": "Camera Lenta Extrema"},
    {"nome": "Alienigenas", "tema": "ETs em Situacoes Engracadas"},
    {"nome": "Robos Desastrados", "tema": "Robos Tentando Ser Humanos"},
]

FALAS_FALLBACK = {
    "Releitura de Cenas Famosas": ["Eu sou inevitavel... ou nao?", "Ate a vista, baby!", "Voce nao vai acreditar no que eu vi"],
    "Micro-aulas e Tutoriais": ["Sabia que o cerebro processa imagens em milissegundos?", "Deixa eu te mostrar um truque incrivel"],
    "Erros da IA (AI Fails)": ["A inteligencia artificial tentou e falhou bonito", "Olha o que a IA fez dessa vez"],
    "Visuais Psicodelicos": ["Fecha os olhos e imagina cores que nao existem", "Bem-vindo a dimensao das cores"],
    "Trocadilhos Visuais Literais": ["Isso e literalmente o que acontece", "Quando a piada vira realidade"],
    "Fofura em Situacoes Bizarras": ["Isso e fofo demais pra ser real", "A fofura nao tem limites"],
    "Citacoes Motivacionais": ["Voce e mais forte do que imagina", "Hoje e o dia de mudar tudo"],
    "Fatos Rapidos Chocantes": ["Voce nao vai acreditar nisso!", "Isso e real e vai te chocar"],
    "Visualizacao de Musica": ["Sente essa batida?", "Quando o som vira imagem"],
    "Educacao Financeira": ["Esse truque simples muda suas financas", "O segredo que os ricos nao contam"],
    "Desmentindo Mitos": ["Isso que te contaram e mentira", "Mito desmentido em 3, 2, 1"],
    "Curiosidades Estranhas": ["O mundo e mais estranho do que parece", "Isso existe de verdade!"],
    "Fatos Medicos e Biologicos": ["Seu corpo faz isso sem voce saber", "Olha o acontece dentro de voce"],
    "Talassofobia e Vida Marinha": ["O oceano esconde segredos terriveis", "Isso vive la embaixo no escuro"],
    "Exercicios e Nutricao": ["Esse exercicio muda tudo em 30 dias", "O segredo e mais simples do que parece"],
    "Noticias sobre Inteligencia Artificial": ["A IA acabou de fazer algo inacreditavel", "O futuro chegou mais cedo"],
    "Visualizacao de Recordes": ["Ninguem jamais conseguiu isso antes!", "Olha o nivel dessa conquista"],
    "Piadas contadas por IA": ["Sabe qual e a do robo no bar?", "Preparado? Tres, dois, um..."],
    "Cenarios Hipoteticos": ["E se a gravidade parasse agora?", "E se o tempo voltasse uma hora?"],
    "Humor Nonsense e Surreal": ["Isso nao faz sentido nenhum e ta tudo bem", "Bem-vindo ao mundo do absurdo"],
    "Ilusoes e Puzzles Visuais": ["Seus olhos estao te enganando agora", "Concentra no centro e veja a magica"],
    "Morphing Satisfatorio": ["Olha essa transformacao suave", "Satisfacao visual garantida"],
    "Camera Lenta Extrema": ["Em camera lenta tudo fica epico", "O detalhe que passa despercebido"],
    "ETs em Situacoes Engracadas": ["Os aliens vieram e ficaram confusos", "Primeiro contato... muito estranho"],
    "Robos Tentando Ser Humanos": ["Iniciando protocolo humano... erro!", "Robo tentando viver... nao deu certo"],
}

PROMPTS_TPL_FALLBACK = {
    "Releitura de Cenas Famosas": "The person reenacts a famous movie scene dramatically. They speak to camera in Brazilian Portuguese: '{fala}'. Cinematic lighting.",
    "Micro-aulas e Tutoriais": "Close-up of person explaining something fascinating to camera. They speak clearly in Brazilian Portuguese: '{fala}'.",
    "Erros da IA (AI Fails)": "Person reacting surprised to camera about an AI fail. They speak in Brazilian Portuguese: '{fala}'. Comedic timing.",
    "Visuais Psicodelicos": "Person surrounded by psychedelic swirling colors. They speak in Brazilian Portuguese: '{fala}'. Trippy neon visuals.",
    "Trocadilhos Visuais Literais": "Person making a visual pun come to life. They speak in Brazilian Portuguese: '{fala}'.",
    "Fofura em Situacoes Bizarras": "Person in an absurdly cute situation speaking to camera in Brazilian Portuguese: '{fala}'. Soft pastel.",
    "Citacoes Motivacionais": "Person delivering a motivational quote into camera. They speak in Brazilian Portuguese: '{fala}'. Golden hour.",
    "Fatos Rapidos Chocantes": "Person sharing a shocking fact with wide eyes. They speak in Brazilian Portuguese: '{fala}'. Dynamic zoom.",
    "Visualizacao de Musica": "Person vibing to music with sound waves. They speak in Brazilian Portuguese: '{fala}'.",
    "Educacao Financeira": "Person explaining a money tip confidently. They speak in Brazilian Portuguese: '{fala}'.",
    "Desmentindo Mitos": "Person debunking a myth with confident expression. They speak in Brazilian Portuguese: '{fala}'.",
    "Curiosidades Estranhas": "Person sharing a bizarre fact amazed. They speak in Brazilian Portuguese: '{fala}'.",
    "Fatos Medicos e Biologicos": "Person explaining a body fact with hand gestures. They speak in Brazilian Portuguese: '{fala}'.",
    "Talassofobia e Vida Marinha": "Person speaking about ocean mysteries, deep blue background. They speak in Brazilian Portuguese: '{fala}'.",
    "Exercicios e Nutricao": "Person giving fitness advice energetically. They speak in Brazilian Portuguese: '{fala}'.",
    "Noticias sobre Inteligencia Artificial": "Person reporting AI news with futuristic effects. They speak in Brazilian Portuguese: '{fala}'.",
    "Visualizacao de Recordes": "Person amazed by a world record. They speak in Brazilian Portuguese: '{fala}'.",
    "Piadas contadas por IA": "Person telling a joke with comedic timing. They speak in Brazilian Portuguese: '{fala}'.",
    "Cenarios Hipoteticos": "Person pondering a wild what-if scenario. They speak in Brazilian Portuguese: '{fala}'.",
    "Humor Nonsense e Surreal": "Person in surreal absurd situation. They speak in Brazilian Portuguese: '{fala}'.",
    "Ilusoes e Puzzles Visuais": "Person presenting an optical illusion. They speak in Brazilian Portuguese: '{fala}'.",
    "Morphing Satisfatorio": "Person transforming smoothly with morph effect. They speak in Brazilian Portuguese: '{fala}'.",
    "Camera Lenta Extrema": "Person in extreme slow motion dramatic effect. They speak in Brazilian Portuguese: '{fala}'.",
    "ETs em Situacoes Engracadas": "Person encountering aliens in funny situation. They speak in Brazilian Portuguese: '{fala}'.",
    "Robos Tentando Ser Humanos": "Person acting like malfunctioning robot. They speak in Brazilian Portuguese: '{fala}'.",
}

# Historico persistido (para nao repetir entre sessoes)
HIST_FALAS = {c["tema"]: [] for c in CANAIS}
HIST_CENARIOS = {c["tema"]: [] for c in CANAIS}


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode("ascii"), flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        try:
            f.write(line + "\n")
        except Exception:
            pass


# Forca utf-8 no stdout (Windows cp1252 quebra acentos)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


# ---------------------------------------------------------------------------
# Detector de bloqueio (Fase 14)
# ---------------------------------------------------------------------------
def detectar_bloqueio_global():
    """Analisa o log/sessoes_status para detectar bloqueio global.

    Criterios:
    - >= 3 sessoes em cooldown simultaneamente = bloqueio do sistema
    - >= 5 falhas em 10min por todas sessoes = provavel rate limit
    Retorna (bloqueado: bool, motivo: str)
    """
    from datetime import timedelta
    status = load_sessoes_status()
    em_cooldown = sum(1 for s, info in status.items() if sessao_em_cooldown(s))
    agora = datetime.datetime.now()
    falhas_recentes = 0
    for s, info in status.items():
        for f in info.get("failures_log", []):
            try:
                ts = datetime.datetime.fromisoformat(f["ts"])
                if (agora - ts).total_seconds() < 600:
                    falhas_recentes += 1
            except Exception:
                continue
    if em_cooldown >= 3:
        return True, f"{em_cooldown} sessoes em cooldown"
    if falhas_recentes >= 5:
        return True, f"{falhas_recentes} falhas em 10min"
    return False, ""


def pausar_sistema(duracao_min=60, motivo="bloqueio detectado", ate_recurso=False):
    """Pausa o sistema. Cria arquivo de pausa e MATA os Chromes/workers em
    andamento (pausa que pausa de verdade).

    ate_recurso=True cria pausa SEM prazo (until=None): so o monitor_recursos.py
    religa quando RAM/CPU/disco voltarem (ou de madrugada). Usado p/ carga critica.
    """
    pause_file = os.path.join(BASE, "logs", "PAUSE_SYSTEM")
    payload = {"motivo": motivo, "tipo": "carga" if ate_recurso else "bloqueio"}
    if ate_recurso:
        payload["until"] = None
        log(f"[pause] SISTEMA PAUSADO ate recurso voltar - {motivo}")
    else:
        until = datetime.datetime.now() + datetime.timedelta(minutes=duracao_min)
        payload["until"] = until.isoformat(timespec="seconds")
        log(f"[pause] SISTEMA PAUSADO ate {until} - {motivo}")
    with open(pause_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    matar_chromes_do_bot()  # encerra o que estiver rodando (nao deixa Chrome zumbi)


def sistema_pausado():
    """Verifica se o sistema esta pausado. Pausa sem 'until' = ativa ate
    o monitor religar (nao expira sozinha)."""
    pause_file = os.path.join(BASE, "logs", "PAUSE_SYSTEM")
    if not os.path.exists(pause_file):
        return False
    try:
        with open(pause_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        until = data.get("until")
        if until is None:
            return True  # pausa sem prazo (carga critica) — so o monitor remove
        if datetime.datetime.now() >= datetime.datetime.fromisoformat(until):
            os.remove(pause_file)
            return False
        return True
    except Exception:
        return False


def matar_chromes_do_bot():
    """Mata os Chromes nas portas das contas (via netstat+taskkill).
    Usado ao pausar, pra nao deixar Chrome consumindo RAM à toa."""
    import subprocess as _sp
    portas = [c.get("port") for c in SESSOES if c.get("port")]
    for p in portas:
        try:
            out = _sp.run(["netstat", "-ano"], capture_output=True, text=True, timeout=15).stdout
            for linha in out.splitlines():
                if f":{p} " in linha and "LISTENING" in linha:
                    pid = linha.split()[-1].strip()
                    if pid.isdigit():
                        _sp.run(["taskkill", "/PID", pid, "/T", "/F"],
                                capture_output=True, text=True, timeout=10)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Cache foto-cenario matching (Fase 15)
# ---------------------------------------------------------------------------
# Foto ideal por tema: nota da combinacao (foto, cenario) baseado em views
FOTO_CENARIO_FILE = os.path.join(BASE, "logs", "foto_cenario_match.json")


def load_foto_cenario():
    if not os.path.exists(FOTO_CENARIO_FILE):
        return {}
    try:
        with open(FOTO_CENARIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_foto_cenario(data):
    try:
        with open(FOTO_CENARIO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"[match] save falhou: {e}")


def registrar_match(foto, cenario, score, views=0):
    """Registra pontuacao de um par (foto, cenario)."""
    data = load_foto_cenario()
    # Hash do cenario (primeiras palavras-chave)
    import re
    palavras = re.findall(r'\w+', cenario.lower())[:5]
    cenario_key = "_".join(palavras)
    foto_key = foto or "none"
    key = f"{foto_key}|||{cenario_key}"
    if key not in data:
        data[key] = {"foto": foto_key, "cenario_key": cenario_key,
                     "scores": [], "views": [], "count": 0}
    data[key]["scores"].append(float(score))
    data[key]["views"].append(int(views))
    data[key]["count"] += 1
    # Mantem ultimos 20
    data[key]["scores"] = data[key]["scores"][-20:]
    data[key]["views"] = data[key]["views"][-20:]
    save_foto_cenario(data)


def melhores_fotos_para_cenario(cenario, top_n=3):
    """Retorna top N fotos que funcionam bem para este cenario."""
    data = load_foto_cenario()
    import re
    palavras = re.findall(r'\w+', cenario.lower())[:5]
    cenario_key = "_".join(palavras)
    # Filtra matches com este cenario
    matches = [v for v in data.values() if v["cenario_key"] == cenario_key]
    if not matches:
        return []
    matches.sort(key=lambda x: sum(x["views"]) / max(len(x["views"]), 1), reverse=True)
    return [m["foto"] for m in matches[:top_n]]


def escolher_foto_inteligente(foto_padrao, cenario):
    """50% das vezes, escolhe foto recomendada para o cenario."""
    if random.random() < 0.5:
        melhores = melhores_fotos_para_cenario(cenario, top_n=3)
        if melhores:
            abs_paths = []
            for f in melhores:
                if f and f != "none":
                    abs_paths.append(os.path.join(FOTOS_DIR, f))
            if abs_paths:
                escolhas = [p for p in abs_paths if os.path.exists(p)]
                if escolhas:
                    return random.choice(escolhas)
    return foto_padrao


# ---------------------------------------------------------------------------
# Detector de saturacao (Fase 18) - evita shadowban
# ---------------------------------------------------------------------------
def contar_videos_recentes_por_tema(tema, horas=24):
    """Conta videos gerados de um tema nas ultimas X horas."""
    cache = load_cache()
    agora = datetime.datetime.now()
    count = 0
    for item in cache:
        if item.get("tema") != tema:
            continue
        try:
            ts = datetime.datetime.fromisoformat(item.get("ts", ""))
            if (agora - ts).total_seconds() < horas * 3600:
                count += 1
        except Exception:
            continue
    return count


def detectar_saturacao(tema, max_por_dia=5):
    """Se tema ja tem max_por_dia videos em 24h, retorna True."""
    count = contar_videos_recentes_por_tema(tema, horas=24)
    if count >= max_por_dia:
        log(f"[saturacao] tema '{tema}' ja tem {count} videos em 24h (max {max_por_dia})")
        return True
    return False


def temas_disponiveis(temas_possiveis, max_por_dia=5):
    """Filtra temas que nao estao saturados."""
    return [t for t in temas_possiveis if not detectar_saturacao(t, max_por_dia)]


def escolher_canal_inteligente(canais, max_por_dia=5):
    """Escolhe canal aleatorio, mas pula canais saturados."""
    disponiveis = temas_disponiveis([c["tema"] for c in canais], max_por_dia)
    if not disponiveis:
        log("[saturacao] TODOS canais saturados, usando qualquer um")
        return random.choice(canais)
    cand = [c for c in canais if c["tema"] in disponiveis]
    return random.choice(cand)


def load_hist():
    global HIST_FALAS, HIST_CENARIOS
    if os.path.exists(HIST_FILE):
        try:
            with open(HIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                HIST_FALAS.update(data.get("falas", {}))
                HIST_CENARIOS.update(data.get("cenarios", {}))
        except Exception as e:
            log(f"[hist] erro ao carregar: {e}")


def save_hist():
    try:
        with open(HIST_FILE, "w", encoding="utf-8") as f:
            json.dump({"falas": HIST_FALAS, "cenarios": HIST_CENARIOS}, f,
                      ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"[hist] erro ao salvar: {e}")


# ---------------------------------------------------------------------------
# Cache de formulas de videos (replicacao e analise de viralizacao)
# ---------------------------------------------------------------------------
def load_cache():
    """Carrega cache de formulas. Cada item: {id, ts, canal, tema, fala, cenario,
    prompt_final, foto, video_path, score, iteracoes, fonte, metrics (preenchido depois)}.
    """
    if not os.path.exists(CACHE_FILE):
        return []
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"[cache] erro ao carregar: {e}")
        return []


def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"[cache] erro ao salvar: {e}")


def registrar_formula(canal_nome, tema, fala, cenario, prompt_final, foto,
                     video_path, score, iteracoes, fonte):
    """Registra a formula completa de um video no cache. Retorna id."""
    import uuid
    cache = load_cache()
    item = {
        "id": str(uuid.uuid4())[:8],
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "canal": canal_nome,
        "tema": tema,
        "fala": fala,
        "cenario": cenario,
        "prompt_final": prompt_final,
        "foto": os.path.basename(foto) if foto else None,
        "video_path": video_path,
        "score": score,
        "iteracoes": iteracoes,
        "fonte": fonte,
        "metrics": {},  # preenchido depois com views/likes se vier
    }
    cache.append(item)
    # Mantem so os ultimos 500
    cache = cache[-500:]
    save_cache(cache)
    log(f"[cache] formula registrada: id={item['id']} score={score}/10")
    return item["id"]


def update_metrics(video_id, metrics):
    """Atualiza metricas de um video (views, likes, etc)."""
    cache = load_cache()
    for item in cache:
        if item["id"] == video_id:
            item["metrics"].update(metrics)
            item["metrics_updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
            save_cache(cache)
            log(f"[cache] metricas atualizadas: {video_id} {metrics}")
            return True
    return False


def top_formulas(min_score=8, top_n=10):
    """Retorna as formulas com maior score, para replicar."""
    cache = load_cache()
    ranked = [c for c in cache if c.get("score", 0) >= min_score]
    ranked.sort(key=lambda c: c.get("score", 0), reverse=True)
    return ranked[:top_n]


def buscar_formula(video_id):
    """Busca formula por id."""
    cache = load_cache()
    for item in cache:
        if item["id"] == video_id:
            return item
    return None


def formula_to_canal_dict(item):
    """Converte item do cache em dict similar ao CANAIS para reutilizar."""
    return {"nome": item["canal"], "tema": item["tema"]}


def score_formula(item):
    """Score composto: critic score + bonus de metrics.

    Sem metrics: usa so o score do critic.
    Com metrics: score + bonus views (log) + bonus likes.
    """
    base = item.get("score", 0)
    metrics = item.get("metrics", {})
    if not metrics:
        return base
    views = metrics.get("views", 0)
    likes = metrics.get("likes", 0)
    # Bonus: log(views) escala de 0-2, log(likes) de 0-1.5
    import math
    bonus_views = math.log10(max(views, 1)) * 0.5
    bonus_likes = math.log10(max(likes, 1)) * 0.3
    return base + bonus_views + bonus_likes


def analisar_padroes_viralizacao():
    """Analisa o cache para identificar padroes dos videos que viralizaram.

    Retorna insights por canal: avg_score, avg_views, top_falas, top_keywords.
    """
    cache = load_cache()
    com_metrics = [c for c in cache if c.get("metrics", {}).get("views")]
    if len(com_metrics) < 3:
        return {"msg": f"precesia mais dados: {len(com_metrics)}/3 videos com metrics"}

    # Agrupa por canal
    from collections import defaultdict
    por_canal = defaultdict(list)
    for c in com_metrics:
        por_canal[c["canal"]].append(c)

    insights = {}
    for canal, items in por_canal.items():
        views = [c["metrics"]["views"] for c in items]
        fala_len = [len(c.get("fala","")) for c in items]
        insights[canal] = {
            "n_videos": len(items),
            "avg_views": sum(views) / len(views),
            "max_views": max(views),
            "avg_critic_score": sum(c.get("score", 0) for c in items) / len(items),
            "avg_fala_len": sum(fala_len) / len(fala_len) if fala_len else 0,
            "top_fala": max(items, key=lambda c: c["metrics"]["views"]).get("fala", ""),
        }

    # Identifica palavras-chave em falas virais (top 25% views)
    ordenadas = sorted(com_metrics, key=lambda c: c["metrics"]["views"], reverse=True)
    top_quartil = ordenadas[:max(1, len(ordenadas) // 4)]
    todas_falas = " ".join(c.get("fala", "") for c in top_quartil).lower()
    # Stopwords basicas
    stopwords = {"que", "para", "com", "uma", "você", "voce", "esse", "essa", "isso", "aqui", "agora", "sua", "seu", "mais", "como", "pelo", "pela", "todo", "toda", "sem", "tem", "foi", "vai", "vão", "sao", "ser", "ter", "dar", "ver", "ficar", "deixar"}
    palavras = [w for w in re.findall(r'\w+', todas_falas) if len(w) > 3 and w not in stopwords]
    from collections import Counter
    kw_count = Counter(palavras).most_common(10)
    insights["__keywords__"] = kw_count

    # Salva tambem em arquivo
    out_file = os.path.join(BASE, "logs", "padroes_viralizacao.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    log(f"[padroes] analise salva em {out_file}")
    return insights


def ajustar_score_com_historico(score_base, canal):
    """Bônus baseado em historico do canal.

    Se canal tem historico de videos com views > X, da bonus.
    """
    cache = load_cache()
    do_canal = [c for c in cache if c.get("canal") == canal and c.get("metrics", {}).get("views")]
    if not do_canal:
        return score_base
    avg_views = sum(c["metrics"]["views"] for c in do_canal) / len(do_canal)
    # >10k views = +1.0 no score, >50k = +2.0
    if avg_views >= 50000:
        return score_base + 2.0
    if avg_views >= 10000:
        return score_base + 1.0
    if avg_views >= 1000:
        return score_base + 0.5
    return score_base


def escolher_formula_para_replicar(min_score=8, replica_prob=0.3):
    """Escolhe formula para replicar (30% chance). Score composto >= min_score."""
    cache = load_cache()
    validas = [c for c in cache if c.get("video_path") and score_formula(c) >= min_score]
    if not validas:
        return None
    if random.random() > replica_prob:
        return None
    # 60% replica a top, 40% replica aleatoria (variedade)
    if random.random() < 0.6:
        validas.sort(key=lambda c: score_formula(c), reverse=True)
        return validas[0]
    return random.choice(validas)


def gerar_prompts_replicacao(item):
    """Gera variacoes de fala/cenario a partir de uma formula vencedora.

    Usa LLM para criar 2-3 variacoes mantendo o estilo.
    """
    fala_orig = item.get("fala", "")
    cenario_orig = item.get("cenario", "")
    canal = item.get("canal", "")
    tema = item.get("tema", "")
    try:
        from llm_client import LLMClient
        client = LLMClient()
        prompt = f"""Replique esta formula viral mantendo o ESTILO mas variando conteudo:

Canal: {canal}
Tema: {tema}
Fala original: {fala_orig}
Cenario original: {cenario_orig}

Responda em JSON:
{{"fala": "<nova fala no mesmo estilo, mesmo idioma, maximo 100 chars>", "cenario": "<novo cenario variando elementos especificos, mesmo estilo visual, maximo 200 chars>"}}

Apenas o JSON, sem explicacao."""
        resp = client.send(prompt, max_tokens=400)
        import json
        m = __import__('re').search(r'\{.*\}', resp, __import__('re').DOTALL)
        if m:
            data = json.loads(m.group(0))
            return data.get("fala"), data.get("cenario")
    except Exception as e:
        log(f"[replica] LLM variacao falhou: {e}")
    # Fallback: retorna original (replica exata)
    return fala_orig, cenario_orig


# ---------------------------------------------------------------------------
# Controle de sessoes (failover automatico)
# ---------------------------------------------------------------------------
def load_sessoes_status():
    """Carrega status: {sessao: {failures, last_failure, last_success, cooldown_until}}.

    Sessao com >= 3 falhas em <30min vai pra cooldown de 30min.
    """
    if not os.path.exists(SESSOES_FILE):
        return {}
    try:
        with open(SESSOES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_sessoes_status(status):
    try:
        with open(SESSOES_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"[sessao] erro ao salvar: {e}")


def registrar_falha_sessao(session_name, motivo):
    status = load_sessoes_status()
    info = status.get(session_name, {"failures": 0, "failures_log": []})
    info["failures"] = info.get("failures", 0) + 1
    info["last_failure"] = datetime.datetime.now().isoformat(timespec="seconds")
    info["last_motivo"] = motivo
    log_fails = info.get("failures_log", [])
    log_fails.append({"ts": info["last_failure"], "motivo": motivo})
    info["failures_log"] = log_fails[-20:]
    # Se >= 3 falhas, cooldown 30min
    if len(log_fails) >= 3:
        ate = datetime.datetime.now() + datetime.timedelta(minutes=30)
        info["cooldown_until"] = ate.isoformat(timespec="seconds")
        log(f"[sessao] {session_name} em cooldown ate {ate}")
    status[session_name] = info
    save_sessoes_status(status)


def marcar_creditos_esgotados(session_name, padrao_texto=""):
    """Marca a sessao como EXHAUSTED — sem creditos — e aplica cooldown longo
    ate o reset diario (proxima meia-noite).

    Este e o lado ORQUESTRADOR do fluxo de creditos. O lado WORKER (detectar
    na pagina do Flow) fica em creditos.py; ele avisa este cron via exit code 2
    + marcador stdout "CREDITOS_ESGOTADOS padrao='...'".

    O bot NAO vai mais tentar essa sessao durante o resto do dia. Quando a meia-
    noite passar, o cooldown expira e o bot volta a usar a conta (assume que
    creditos foram renovados).

    Args:
        session_name: nome da sessao (ex.: "seebotsia")
        padrao_texto: trecho do texto que o Flow mostrou (pra diagnostico)
    """
    status = load_sessoes_status()
    info = status.get(session_name, {})
    agora = datetime.datetime.now()

    # Proxima meia-noite (00:00 do dia seguinte)
    amanha = (agora + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0)
    # Margem de seguranca: 5min depois da meia-noite (caso o Flow demore)
    ate = amanha + datetime.timedelta(minutes=5)

    info["status"] = "EXHAUSTED"
    info["cooldown_until"] = ate.isoformat(timespec="seconds")
    info["last_motivo"] = "creditos_esgotados"
    info["padrao_creditos"] = padrao_texto
    info["marked_exhausted_at"] = agora.isoformat(timespec="seconds")
    info["creditos_renova_em"] = ate.isoformat(timespec="seconds")
    status[session_name] = info
    save_sessoes_status(status)
    log(f"[sessao] {session_name} MARCADA COMO EXHAUSTED ate {ate} "
        f"(padrao='{padrao_texto}')")


def registrar_sucesso_sessao(session_name):
    status = load_sessoes_status()
    info = status.get(session_name, {"failures": 0})
    info["failures"] = 0
    info["failures_log"] = []
    info.pop("cooldown_until", None)
    info["last_success"] = datetime.datetime.now().isoformat(timespec="seconds")
    status[session_name] = info
    save_sessoes_status(status)


def sessao_em_cooldown(session_name):
    status = load_sessoes_status()
    info = status.get(session_name, {})
    cd = info.get("cooldown_until")
    if not cd:
        return False
    try:
        ate = datetime.datetime.fromisoformat(cd)
        if datetime.datetime.now() >= ate:
            return False
        return True
    except Exception:
        return False


def escolher_sessao():
    """Escolhe melhor sessao disponivel. Tenta em ordem do pool, pula as em cooldown.

    Logga quais sessoes estao bloqueadas e por que (incluindo EXHAUSTED).
    Retorna None se TODAS estao bloqueadas — NAO martela SESSOES[0] (bug 2026-07-26:
    ficava horas tentando gerar em contas ja sem credito, timeout de 24min cada).
    """
    status = load_sessoes_status()
    bloqueadas = []
    for s in SESSOES:
        info = status.get(s["session"], {})
        if info.get("status") == "EXHAUSTED":
            bloqueadas.append(f"{s['session']}=EXHAUSTED (renova {info.get('creditos_renova_em','?')})")
            continue
        if sessao_em_cooldown(s["session"]):
            bloqueadas.append(f"{s['session']}=COOLDOWN (ate {info.get('cooldown_until','?')})")
            continue
        return s
    if bloqueadas:
        log(f"[pool] todas sessoes bloqueadas: {'; '.join(bloqueadas)}")
    # Todas esgotadas/cooldown: NAO gerar (antes retornava SESSOES[0] e martelava).
    return None


def todas_sessoes_esgotadas():
    """True se TODAS as sessoes estao EXHAUSTED (sem credito ate o reset diario).

    Usado pra pular o ciclo inteiro sem gastar LLM montando prompt (bug 2026-07-26).
    Retorna (True, quando_renova) ou (False, None).
    """
    status = load_sessoes_status()
    if not SESSOES:
        return True, None
    renovacoes = []
    for s in SESSOES:
        info = status.get(s["session"], {})
        if info.get("status") != "EXHAUSTED":
            return False, None
        renovacoes.append(info.get("creditos_renova_em", "?"))
    # todas EXHAUSTED — a mais cedo a renovar
    validas = [r for r in renovacoes if r and r != "?"]
    return True, (min(validas) if validas else None)


def aplicar_sessao(s):
    """Aplica env vars da sessao."""
    os.environ["FLOW_SESSION"] = s["session"]
    os.environ["FLOW_PORT"] = s["port"]
    os.environ["FLOW_PROFILE"] = s["profile"]
    log(f"[sessao] usando {s['session']} na porta {s['port']}")


def escolher_foto():
    fotos = glob.glob(os.path.join(FOTOS_DIR, "*.jpg"))
    fotos += glob.glob(os.path.join(FOTOS_DIR, "*.jpeg"))
    fotos += glob.glob(os.path.join(FOTOS_DIR, "*.png"))
    if not fotos:
        return None
    return random.choice(fotos)


def montar_prompt(canal):
    """Tenta LLM multi-agent; fallback para LLM simples; fallback para lista estatica.

    Retorna: dict com prompt_final, fala, cenario, fonte, score, iteracoes
    """
    tema = canal["tema"]
    canal_nome = canal["nome"]
    default_tpl = "Person speaking to camera in Brazilian Portuguese: '{fala}'. Engaging and viral."
    tpl = PROMPTS_TPL_FALLBACK.get(tema, default_tpl)

    fala = None
    cenario = None
    fonte = "fallback"
    score = 0
    iteracoes = 0

    # CAMADA 0: Tenta replicar formula vencedora (score composto >= 8, prob 30%)
    try:
        replica = escolher_formula_para_replicar(min_score=8, replica_prob=0.3)
        if replica:
            log(f"[replica] replicando formula {replica['id']} (score_composto={score_formula(replica):.1f})")
            nova_fala, novo_cenario = gerar_prompts_replicacao(replica)
            if nova_fala and novo_cenario:
                fala = nova_fala
                cenario = novo_cenario
                HIST_FALAS.setdefault(tema, []).append(fala)
                HIST_CENARIOS.setdefault(tema, []).append(cenario)
                score = replica.get("score", 8)  # herda score base
                iteracoes = 0
                fonte = "replica"
                log(f"[replica] variacao gerada: {fala!r}")
    except Exception as e:
        log(f"[replica] erro: {e}")

    # CAMADA 1: Tenta multi-agent (Trend Scout + Hook + Scenario + Critic)
    multi_fala = random.random() < 0.30  # 30% dos videos usam multi-fala
    try:
        from agents import run_pipeline
        # Enriquece exemplos com falas vencedoras (Fase 13)
        from vencedoras import get_exemplos_falas, get_exemplos_cenarios
        ex_falas = HIST_FALAS.get(tema, []) + get_exemplos_falas(tema, top_n=5)
        ex_cenarios = HIST_CENARIOS.get(tema, []) + get_exemplos_cenarios(tema, top_n=5)
        log(f"[agent] pipeline multi-agent para '{canal_nome}' (multi_fala={multi_fala}, ex_falas={len(ex_falas)})...")
        result = run_pipeline(
            canal_nome, tema,
            exemplos_falas=ex_falas,
            exemplos_cenarios=ex_cenarios,
            multi_fala=multi_fala,
        )
        fala = result.get("fala")
        cenario = result.get("cenario")
        if fala:
            HIST_FALAS.setdefault(tema, []).append(fala)
        if cenario:
            HIST_CENARIOS.setdefault(tema, []).append(cenario)
        score = result.get("score", 0)
        iteracoes = result.get("iteracoes", 0)
        log(f"[agent] multi-agent OK (score={score}/10, iteracoes={iteracoes})")
        fonte = "agent"
    except Exception as e:
        log(f"[agent] multi-agent falhou ({type(e).__name__}: {e})")

    # CAMADA 2: Fallback - LLM simples (Gemini Flash Lite direto)
    if not fala:
        try:
            from llm_client import gerar_fala_viral, gerar_prompt_viral
            log(f"[llm] gerando fala para '{canal_nome}'...")
            fala = gerar_fala_viral(canal_nome, tema, exemplos=HIST_FALAS.get(tema, []))
            if fala:
                HIST_FALAS.setdefault(tema, []).append(fala)
                log(f"[llm] fala OK: {fala!r}")
                log(f"[llm] gerando cenario...")
                cenario = gerar_prompt_viral(canal_nome, tema, fala, exemplos_cenarios=HIST_CENARIOS.get(tema, []))
                if cenario:
                    HIST_CENARIOS.setdefault(tema, []).append(cenario)
                    log(f"[llm] cenario OK: {cenario!r}")
                fonte = "llm"
                score = 5  # score medio - sem critic
        except Exception as e:
            log(f"[llm] erro: {type(e).__name__}: {e}")

    # CAMADA 3: Fallback - lista estatica
    if not fala:
        falas_lista = FALAS_FALLBACK.get(tema, ["Isso vai te surpreender!", "Voce precisa ver isso"])
        fala = random.choice(falas_lista)
        HIST_FALAS.setdefault(tema, []).append(fala)
        log(f"[fallback] fala escolhida: {fala!r}")
        score = 3

    if cenario:
        if "{fala}" in cenario:
            prompt = cenario.replace("{fala}", fala)
        else:
            prompt = f"{cenario} They speak in Brazilian Portuguese: '{fala}'. 9:16 vertical portrait."
    else:
        prompt = tpl.replace("{fala}", fala)

    if len(HIST_FALAS.get(tema, [])) > 50:
        HIST_FALAS[tema] = HIST_FALAS[tema][-50:]
    if len(HIST_CENARIOS.get(tema, [])) > 30:
        HIST_CENARIOS[tema] = HIST_CENARIOS[tema][-30:]

    return {
        "prompt": prompt,
        "fala": fala,
        "cenario": cenario,
        "fonte": fonte,
        "score": score,
        "iteracoes": iteracoes,
    }


def gerar_fila_safe(canal_nome, tema, exemplos):
    from llm_client import gerar_fala_viral
    return gerar_fala_viral(canal_nome, tema, exemplos=exemplos).strip().strip('"').strip("'")


def gerar_cenario_safe(canal_nome, tema, fala, exemplos_cenarios):
    from llm_client import gerar_prompt_viral
    return gerar_prompt_viral(canal_nome, tema, fala, exemplos_cenarios=exemplos_cenarios).strip().strip('"').strip("'")


def gerar_video(prompt, foto, out_path):
    """Executa gera_auto.py e retorna:
       - True: video gerado com sucesso
       - False: falha normal (sessao em cooldown curto)
       - "NO_CREDITS": creditos esgotados (sessao deve marcar cooldown longo)

    A deteccao e feita por marcador especial no stderr/stdout de gera_auto.py.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [
        sys.executable,  # mesmo venv que rodou o cron (D:\veo\venv) — sem hardcode
        os.path.join(BASE, "gera_auto.py"),
        prompt,
        out_path,
        foto,
    ]
    # Timeout DINAMICO: base 12min, esticado quando a maquina esta apertada
    # (CPU/RAM sob carga fazem o Veo renderizar mais devagar). Antes era 8min
    # fixo, que estourava sob carga sem gerar (desperdicava a sessao).
    try:
        tmo = recursos.timeout_dinamico(720)
    except Exception:
        tmo = 720
    log(f"CMD: python gera_auto.py ... (timeout={tmo}s, {recursos.nivel_carga() if hasattr(recursos,'nivel_carga') else '?'})")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=tmo,
                                encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        log(f"[gerar] TIMEOUT {tmo}s - marcando falha de sessao")
        return False
    # exit code 5 = worker detectou pausa e abortou ANTES de abrir Chrome.
    # Nao e falha de sessao — nao penaliza a conta.
    if result.returncode == 5:
        log("[gerar] worker abortou: sistema pausado")
        return "PAUSED"
    # Detecta creditos esgotados via exit code 2 OU marcador no stdout
    if result.returncode == 2:
        output = (result.stdout or "") + (result.stderr or "")
        log("[gerar] exit code 2 = CREDITOS ESGOTADOS")
        import re as _re
        m = _re.search(r"padrao='([^']*)'", output)
        padrao = m.group(1) if m else "no_credits"
        return ("NO_CREDITS", padrao)
    output = (result.stdout or "") + (result.stderr or "")
    if "CREDITOS_ESGOTADOS" in output:
        log("[gerar] detectado marcador CREDITOS_ESGOTADOS no output")
        import re as _re
        m = _re.search(r"padrao='([^']*)'", output)
        padrao = m.group(1) if m else ""
        return ("NO_CREDITS", padrao)
    if result.returncode != 0:
        log(f"ERRO gera_auto exit={result.returncode}: {result.stderr[-300:]}")
        return False
    return os.path.exists(out_path) and os.path.getsize(out_path) > 100_000


def validar_video(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30)
        dims = r.stdout.strip()
        r2 = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_name", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30)
        audio = r2.stdout.strip()
        return dims, audio
    except Exception as e:
        return None, str(e)


def run():
    # FASE 14: Verifica se sistema esta pausado
    if sistema_pausado():
        log("[pause] sistema pausado, abortando")
        return False

    # GUARDA DE CREDITO (bug 2026-07-26): se TODAS as contas estao sem credito,
    # nao adianta montar prompt (gasta LLM) nem abrir Chrome (timeout de 24min).
    # Pula o ciclo inteiro ate o reset diario (meia-noite BR). O loop .bat espera
    # 30s e chama de novo; ate renovar, cada ciclo custa ~0 (so este cheque).
    esgotadas, renova = todas_sessoes_esgotadas()
    if esgotadas:
        log(f"[creditos] TODAS as contas sem credito — pulando ciclo (renova {renova or 'meia-noite'})")
        return "NO_ACCOUNTS"

    # GUARDA DE CARGA (bug 2026-07-26): se a maquina esta afogada, NAO abre
    # Chrome (ele crasha sob carga). Em vez de queimar timeout, pausa ate o
    # recurso voltar — o monitor_recursos.py religa quando aliviar/de madrugada.
    try:
        import recursos
        if not recursos.disco_ok():
            log(f"[carga] disco baixo ({recursos.disco_livre_gb():.0f}GB) - pausando ate liberar")
            pausar_sistema(motivo="disco_baixo", ate_recurso=True)
            return False
        if recursos.slots_por_recurso() < 1:
            log(f"[carga] {recursos.resumo()} - sem RAM p/ 1 Chrome, pausando ate aliviar")
            pausar_sistema(motivo="carga_critica", ate_recurso=True)
            return False
        log(f"[carga] {recursos.resumo()}")
    except Exception as e:
        log(f"[carga] checagem falhou (seguindo): {str(e)[:80]}")

    # FILA (buffer): tenta reaproveitar um prompt pronto ANTES de chamar o Gemini.
    # Assim nao desperdicamos o trabalho do LLM quando um video falhou antes.
    item_fila = None
    try:
        import fila
        item_fila = fila.desenfileirar()
    except Exception as e:
        log(f"[fila] leitura falhou (seguindo): {str(e)[:80]}")

    if item_fila:
        formula = item_fila["formula"]
        canal = item_fila["canal"]
        foto = item_fila["foto"]
        log(f"[fila] reaproveitando prompt pronto (restam {fila.tamanho()} na fila)")
    else:
        formula = montar_prompt(canal_escolhido := escolher_canal_inteligente(CANAIS))
        canal = canal_escolhido
        foto = escolher_foto()
        if not foto:
            log("ERRO: nenhuma foto editada encontrada")
            return False
        # FASE 15: Foto inteligente (considera matches historicos)
        if formula.get("cenario"):
            foto_inteligente = escolher_foto_inteligente(foto, formula["cenario"])
            if foto_inteligente != foto:
                log(f"[match] usando foto inteligente: {os.path.basename(foto_inteligente)}")
                foto = foto_inteligente

    prompt = formula["prompt"]
    fala = formula["fala"]
    fonte = formula["fonte"]
    score = formula["score"]
    iteracoes = formula["iteracoes"]

    # FAILOVER com teto por SCORE: video bom merece insistir (3 sessoes);
    # video fraco (score baixo) nao vale queimar 3x o timeout — tenta 1x so.
    # Evita o caso real de um score 5 desperdicar 24min em 3 timeouts.
    try:
        _score_num = float(score)
    except (TypeError, ValueError):
        _score_num = 7.0
    max_tentativas = 3 if _score_num >= 7 else (2 if _score_num >= 5.5 else 1)
    tentativas = []
    for tentativa_n in range(max_tentativas):
        sessao = escolher_sessao()
        if sessao is None:
            # Todas as contas esgotaram (talvez durante as tentativas). Preserva o
            # prompt na fila pra usar quando renovar, e sai sem martelar.
            log("[creditos] sem conta disponivel no meio das tentativas — preservando prompt na fila")
            try:
                import fila
                _it = item_fila if item_fila else {"formula": formula, "foto": foto, "canal": canal, "tentativas": 0}
                fila.enfileirar(_it["formula"], _it["foto"], _it["canal"], prioridade=True)
            except Exception:
                pass
            return "NO_ACCOUNTS"
        tentativas.append(sessao["session"])
        aplicar_sessao(sessao)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = canal["nome"].replace(" ", "_").lower()[:15]
        out_name = f"{slug}_{ts}.mp4"
        out_path = os.path.join(VIDEOS_DIR, out_name)

        log(f"=== GERANDO === Canal: {canal['nome']} | Tema: {canal['tema']} | Fonte: {fonte} | Score={score}/10 | Sessao={sessao['session']} (tentativa {tentativa_n+1})")
        log(f"Foto: {os.path.basename(foto)}")
        log(f"Fala: {fala}")
        log(f"Prompt: {prompt[:150]}...")

        ok = gerar_video(prompt, foto, out_path)
        # Caso 0: sistema pausou no meio → devolve o prompt pra fila e sai limpo
        if ok == "PAUSED":
            try:
                import fila
                _it = item_fila if item_fila else {"formula": formula, "foto": foto, "canal": canal, "tentativas": 0}
                fila.enfileirar(_it["formula"], _it["foto"], _it["canal"], prioridade=True)
            except Exception:
                pass
            log("[pause] abortando ciclo (prompt preservado na fila)")
            return False
        # Caso 1: creditos esgotados → marca EXHAUSTED + tenta proxima sessao
        if isinstance(ok, tuple) and ok[0] == "NO_CREDITS":
            padrao_achou = ok[1] if len(ok) > 1 else ""
            log(f"[CREDITOS] {sessao['session']} SEM CREDITOS! padrao='{padrao_achou}'")
            marcar_creditos_esgotados(sessao["session"], padrao_texto=padrao_achou)
            continue  # tenta proxima sessao (pula sem cooldown de 5min, vai ate meia-noite)
        if ok:
            registrar_sucesso_sessao(sessao["session"])
            # ...resto do codigo
            save_hist()
            video_id = registrar_formula(
                canal["nome"], canal["tema"], fala, formula["cenario"],
                prompt, foto, out_path, score, iteracoes, fonte
            )
            log(f"[cache] id={video_id} salvo para analise de viralizacao")

            # FASE 10: Gera 3 thumbnails A/B test
            try:
                from thumbnail_client import gen_3_variants
                thumbs = gen_3_variants(foto, fala, canal["nome"])
                # Atualiza cache com paths das thumbnails
                cache = load_cache()
                for item in cache:
                    if item["id"] == video_id:
                        item["thumbnails"] = thumbs
                        save_cache(cache)
                        log(f"[thumb] 3 variantes A/B salvas: {thumbs}")
                        break
            except Exception as e:
                log(f"[thumb] falhou: {e}")

            dims, audio = validar_video(out_path)
            log(f"VALIDACAO: dims={dims} audio={audio}")
            if not audio:
                log("AVISO: video sem audio!")
            size_kb = os.path.getsize(out_path) // 1024
            log(f"SUCESSO: {out_name} ({size_kb}KB)")
            avisar_desktop("Veo: video pronto", f"{canal['nome']} - {out_name}")
            return True
        else:
            # Falha: registra e tenta proxima
            motivo = "gerar_video falhou"
            log(f"[sessao] {sessao['session']} falhou - tentando proxima...")
            registrar_falha_sessao(sessao["session"], motivo)
            # Marca sessao atual como em cooldown para nao tentar de novo
            status = load_sessoes_status()
            info = status.get(sessao["session"], {})
            info["cooldown_until"] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat(timespec="seconds")
            status[sessao["session"]] = info
            save_sessoes_status(status)
            continue

    # Todas tentativas falharam
    save_hist()
    registrar_formula(
        canal["nome"], canal["tema"], fala, formula["cenario"],
        prompt, foto, None, score, iteracoes, fonte
    )
    log(f"FALHA TOTAL: tentei {tentativas} - video nao gerado")

    # REAPROVEITA o trabalho do Gemini: em vez de descartar o prompt, devolve
    # pra fila (prioridade). No proximo ciclo tenta de novo, com sessao nova,
    # sem pagar o LLM outra vez. (Descarta so depois de N retentativas.)
    try:
        import fila
        _it = item_fila if item_fila else {"formula": formula, "foto": foto, "canal": canal, "tentativas": 0}
        if fila.reenfileirar_no_erro(_it):
            log(f"[fila] prompt devolvido pra fila p/ nova tentativa (fila={fila.tamanho()})")
        else:
            log("[fila] prompt descartado (excedeu retentativas)")
    except Exception as e:
        log(f"[fila] reenfileirar falhou: {str(e)[:80]}")

    # FASE 14: Detecta bloqueio global apos N falhas
    bloqueado, motivo = detectar_bloqueio_global()
    if bloqueado:
        # Se a causa provavel e carga da maquina, pausa ate recurso voltar
        # (monitor religa). Senao, pausa fixa de 60min (rate limit/bloqueio).
        try:
            import recursos
            if recursos.nivel_carga() in ("apertado", "critico"):
                pausar_sistema(motivo=f"{motivo} + carga alta", ate_recurso=True)
            else:
                pausar_sistema(duracao_min=60, motivo=motivo)
        except Exception:
            pausar_sistema(duracao_min=60, motivo=motivo)
        log(f"[pause] BLOQUEIO DETECTADO: {motivo}")
    return False


if __name__ == "__main__":
    import sys
    load_hist()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        r = run()
        # exit code 6 = nenhuma conta com credito. O loop .bat espera MAIS
        # (15min) em vez de martelar de 30 em 30s ate a meia-noite (bug 2026-07-26).
        if r == "NO_ACCOUNTS":
            sys.exit(6)
    elif cmd == "encher_fila":
        # Enche o buffer de prompts prontos (so fase LLM, sem Chrome).
        # Barato — roda mesmo sob carga. Chamado pelo monitor quando ha folga.
        import fila
        faltam = fila.quanto_encher()
        if faltam <= 0:
            print(f"fila ja cheia ({fila.tamanho()})")
        else:
            print(f"enchendo fila: gerando {faltam} prompt(s)...")
            feitos = 0
            for _ in range(faltam):
                try:
                    canal = escolher_canal_inteligente(CANAIS)
                    formula = montar_prompt(canal)
                    foto = escolher_foto()
                    if not foto:
                        print("  sem foto — parando"); break
                    if formula.get("cenario"):
                        foto = escolher_foto_inteligente(foto, formula["cenario"])
                    if fila.enfileirar(formula, foto, canal):
                        feitos += 1
                        print(f"  +1 ({canal['nome']}, score={formula.get('score')})")
                except Exception as e:
                    print(f"  erro: {str(e)[:80]}")
            print(f"pronto: +{feitos} prompt(s), fila={fila.tamanho()}")
    elif cmd == "fila":
        import fila
        print(f"fila: {fila.tamanho()} prompt(s) pronto(s) | min={fila.FILA_MIN} alvo={fila.FILA_ALVO}")
    elif cmd == "top":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        min_score = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        print(f"=== TOP {n} formulas (score >= {min_score}/10) ===")
        for f in top_formulas(min_score=min_score, top_n=n):
            print(f"[{f['id']}] {f['canal']} score={f['score']} fala={f['fala']!r}")
    elif cmd == "show":
        vid = sys.argv[2]
        f = buscar_formula(vid)
        if f:
            print(json.dumps(f, ensure_ascii=False, indent=2))
        else:
            print(f"nao achei id={vid}")
    elif cmd == "metrics":
        vid = sys.argv[2]
        views = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        likes = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        if update_metrics(vid, {"views": views, "likes": likes}):
            print(f"metricas salvas: id={vid} views={views} likes={likes}")
        else:
            print(f"id nao encontrado: {vid}")
    elif cmd == "post":
        # post VIDEO_ID URL
        vid = sys.argv[2]
        url = sys.argv[3]
        if update_metrics(vid, {"posted_url": url, "posted_at": datetime.datetime.now().isoformat(timespec="seconds")}):
            print(f"url postada: id={vid} url={url}")
        else:
            print(f"id nao encontrado: {vid}")
    elif cmd == "fetch":
        # fetch metrics (usa metrics_client)
        try:
            from metrics_client import auto_update_all
            auto_update_all()
        except Exception as e:
            print(f"metrics fetch falhou: {e}")
    elif cmd == "padroes":
        # analisa padroes de viralizacao
        try:
            ins = analisar_padroes_viralizacao()
            print(json.dumps(ins, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"padroes falhou: {e}")
    elif cmd == "sessoes":
        # Lista status de creditos de cada sessao (incluindo EXHAUSTED)
        status = load_sessoes_status()
        agora = datetime.datetime.now()
        print(f"{'SESSAO':<20} {'STATUS':<12} {'COOLDOWN':<20} {'ULTIMO':<22} {'MOTIVO'}")
        print("-" * 100)
        for s in SESSOES:
            info = status.get(s["session"], {})
            st = info.get("status", "ATIVA")
            cd = info.get("cooldown_until", "-")
            ult = info.get("last_success") or info.get("last_failure") or "-"
            motivo = info.get("last_motivo", "-")
            if st == "EXHAUSTED":
                cd = info.get("creditos_renova_em", "-")
            print(f"{s['session']:<20} {st:<12} {cd:<20} {ult:<22} {motivo}")
        # Sessoes nao declaradas
        declared = {s["session"] for s in SESSOES}
        for k in status:
            if k not in declared:
                print(f"{k:<20} (nao declarada, mas tem status)")
    elif cmd == "clear_exhausted":
        # Limpa status EXHAUSTED de todas sessoes (forcar reset manual)
        # Util apos upgrade do plano ou pra forcar re-teste
        status = load_sessoes_status()
        cleared = []
        for k, v in status.items():
            if v.get("status") == "EXHAUSTED":
                v.pop("status", None)
                v.pop("cooldown_until", None)
                v.pop("creditos_renova_em", None)
                v.pop("padrao_creditos", None)
                cleared.append(k)
        save_sessoes_status(status)
        print(f"Sessoes liberadas de EXHAUSTED: {cleared or '(nenhuma)'}")
    elif cmd == "thumb":
        # cron_gerar_video_llm.py thumb VIDEO_ID
        vid = sys.argv[2]
        cache = load_cache()
        item = next((c for c in cache if c["id"] == vid), None)
        if not item:
            print(f"video nao encontrado: {vid}")
        else:
            foto = os.path.join(FOTOS_DIR, item.get("foto", "")) if item.get("foto") else None
            try:
                from thumbnail_client import gen_3_variants
                thumbs = gen_3_variants(foto, item.get("fala", ""), item.get("canal", ""))
                # Atualiza cache
                for it in cache:
                    if it["id"] == vid:
                        it["thumbnails"] = thumbs
                        save_cache(cache)
                        break
                print(json.dumps(thumbs, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"thumb falhou: {e}")
    elif cmd == "dashboard":
        # roda dashboard em background (nao bloqueante)
        import subprocess
        log(f"[dashboard] iniciando em http://localhost:5000")
        subprocess.Popen(
            [sys.executable, os.path.join(BASE, "dashboard.py")],
            creationflags=0x00000008 | 0x00000200,  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        )
        log(f"[dashboard] rodando em background, abra http://localhost:5000")