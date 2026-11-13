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
import os, sys, random, subprocess, glob, datetime, json, time
# 're' faltava no topo (16/10): analisar_padroes_viralizacao() usa re.findall e
# levantava NameError assim que houvesse 3 videos com metricas — o erro era
# engolido pelo try/except de _auto_fetch_metricas e ninguem via.
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sem_janela  # noqa: F401,E402  (ffmpeg/powershell filhos sem janela na tela - dono, 15/10; item BX-02)

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
from contas import SESSOES, contas_free, contas_pro
import contas as contas_mod
import creditos_contas  # 23/10 (dona): gerenciamento de creditos por conta (minimo 20, mais credito primeiro)
import recursos  # sensor de RAM/CPU pra timeout dinamico e pool adaptativo
import cadeia_veo  # 23/10: ordem de alternativas (notebooks -> desktop sem chamada -> PC2/PC1 o mais livre)
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
# Tier 1: auto-fetch de metricas (fecha o loop de aprendizado)
# ---------------------------------------------------------------------------
# Roda no maximo 1x/hora, no comeco do ciclo. E NO-OP enquanto nao ha o que
# buscar (nenhum video com posted_url e sem YOUTUBE_API_KEY) — entao nao custa
# nada ate os pre-requisitos existirem. Quando o postador passar a gravar
# posted_url no cache (ou YOUTUBE_API_KEY for setada), o loop de aprendizado
# (replica de formula, keywords, ranking de gancho) passa a usar VIEWS REAIS.
_METRICS_STAMP = os.path.join(BASE, "logs", ".last_metrics_fetch")


def _metricas_do_funil():
    """24/10: o laco antigo (replica de formula, palavras virais, bonus de canal) nunca recebeu views (0 de 14 no cache).
    Agora le as MESMAS medidas de 48 h do funil (postador config\\telegram_estado.json medidas_48h + ledger: o Veo sobe
    como veo_<tema>_<AAAAMMDD_HHMMSS>__<canal>.mp4) e grava metrics.views na formula de mesmo clipe. Varios canais/
    reenvios do mesmo clipe = o maior."""
    estado = json.load(open(r"D:\postador-de-videos\config\telegram_estado.json", encoding="utf-8"))
    med = estado.get("medidas_48h", {})
    views = {}
    with open(r"D:\postador-de-videos\logs\uploads_ledger.jsonl", encoding="utf-8") as f:
        for ln in f:
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            m = re.match(r"veo_(.+?_\d{8}_\d{6})", str(r.get("arquivo") or ""))
            if m and r.get("video_id") in med:
                views[m.group(1)] = max(views.get(m.group(1), 0), int(med[r["video_id"]]["views"]))
    if not views:
        return 0
    cache, n = load_cache(), 0
    for c in cache:
        stem = os.path.splitext(os.path.basename(str(c.get("video_path") or "")))[0]
        if stem in views and (c.get("metrics") or {}).get("views") != views[stem]:
            c.setdefault("metrics", {})["views"] = views[stem]
            c["metrics_updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
            n += 1
    if n:
        save_cache(cache)
        log(f"[metrics] {n} formula(s) com views de 48 h do funil")
    return n


def _auto_fetch_metricas(intervalo_h=1.0):
    """Atualiza metricas dos videos postados, no maximo 1x/intervalo_h."""
    try:
        agora = datetime.datetime.now()
        if os.path.exists(_METRICS_STAMP):
            idade = agora - datetime.datetime.fromtimestamp(os.path.getmtime(_METRICS_STAMP))
            if idade.total_seconds() < intervalo_h * 3600:
                return  # ainda no cooldown
        # AT-03 (16/10): os numeros reais chegam pelo D:\postador-de-videos\bin\metricas_rede.py (Studio pelo
        # navegador, sem API) direto em metrics do cache. O metrics_client dependia de YOUTUBE_API_KEY (proibida) e
        # devolvia vazio em silencio: nao e mais chamado. Aqui so re-analisa quando ha numero real.
        try:
            _metricas_do_funil()
        except Exception as e:
            log(f"[metrics] funil 48 h nao leu ({str(e)[:80]})")
        tem_dado = any((c.get("metrics") or {}).get("views") is not None for c in load_cache())
        open(_METRICS_STAMP, "w").close()
        if not tem_dado:
            return
        # re-analisa padroes com os dados novos
        try:
            analisar_padroes_viralizacao()
        except Exception:
            pass
        log("[metrics] auto-fetch concluido (views reais atualizadas)")
    except Exception as e:
        log(f"[metrics] auto-fetch pulou (seguindo): {str(e)[:80]}")


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
    em_cooldown = sum(1 for s, info in status.items()
                      if sessao_em_cooldown(s) and info.get("status") != "EXHAUSTED"
                      and info.get("motivo") != "reCAPTCHA Enterprise")
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
    if em_cooldown >= 10:
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
    if os.environ.get("SKIP_RESOURCE_CHECK") == "1":
        log(f"[pause] MODO PARALELO — ignorando pausa ({motivo})")
        return
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
    o monitor religar (nao expira sozinha).

    SKIP_RESOURCE_CHECK=1 (modo paralelo) so pula a pausa por CARGA (tipo "carga", do monitor de recursos). A pausa
    MANUAL da dona e a de bloqueio valem sempre (item BX-02, 16/10: antes o modo paralelo nem lia o arquivo)."""
    pause_file = os.path.join(BASE, "logs", "PAUSE_SYSTEM")
    if not os.path.exists(pause_file):
        return False
    try:
        with open(pause_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if os.environ.get("SKIP_RESOURCE_CHECK") == "1" and data.get("tipo") == "carga":
            return False
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
                marcadas = _fotos_com_marca()  # 16/10: nunca troca por uma foto com marca de IA
                escolhas = [p for p in abs_paths if os.path.exists(p) and os.path.normcase(p) not in marcadas]
                try:  # 24/10: nem por uma foto com rosto que nao e o do dono (a "recomendada" vem do historico antigo)
                    import foto_na_hora
                    escolhas = [p for p in escolhas if foto_na_hora.rosto_ok(p, FOTOS_DIR)]
                except Exception:
                    escolhas = []
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
    """Escolhe canal pulando saturados e PONDERANDO pelo pico do publico (Tier 3).

    Canais cujo publico esta no horario de pico agora tem mais chance de sair
    (peso 1.0 no pico, 0.3 fora). Nao bloqueia nada — so prioriza. Mantem
    aleatoriedade pra variedade.
    """
    disponiveis = temas_disponiveis([c["tema"] for c in canais], max_por_dia)
    if not disponiveis:
        log("[saturacao] TODOS canais saturados, usando qualquer um")
        cand = canais
    else:
        cand = [c for c in canais if c["tema"] in disponiveis]

    try:
        import inteligencia as _I
        pesos = [_I.bonus_horario(c["tema"]) for c in cand]
    except Exception:
        pesos = [1.0] * len(cand)
    # 24/10 (dono: "passar pelo sistema de rampa de melhorias do YouTube dando preferencia ao mais viral"): mesmo funil
    # dos outros projetos. O medidor de 48 h (postador notificar_telegram._placar_veo) marca vitoria do TEMA quando o
    # Veo passa da mediana do canal; aqui cada tema tira Beta(vitorias+1, derrotas+1) (Thompson, como
    # placar_titulos.escolher): tema que viraliza sai mais, tema sem dado ainda e testado, perdedor quase some.
    try:
        _vt = _placar_temas_veo()
        thomp = []
        for c in cand:
            t, v = _vt.get(_slug_tema(c), (0, 0))
            thomp.append(random.betavariate(v + 1, t - v + 1))
        # sorteio ponderado (nao o maximo): com o horario 1.0/0.3 o maximo deixava 3 temas com 95% dos ciclos
        escolhido = random.choices(cand, weights=[p * t + 1e-6 for p, t in zip(pesos, thomp)], k=1)[0]
        if _vt:
            t, v = _vt.get(_slug_tema(escolhido), (0, 0))
            log(f"[funil] tema {escolhido['nome']} ({v:g}/{t} vitorias em 48 h)")
        return escolhido
    except Exception as e:
        log(f"[funil] placar indisponivel ({str(e)[:80]}) - so pelo horario")
        return random.choices(cand, weights=pesos, k=1)[0]


def _linha_funil():
    """24/10: vai na MESMA linha diaria de creditos (sem mensagem a mais): melhor/pior tema do placar e fotos na hora
    de ontem (aprovadas/geradas)."""
    try:
        vt = {k: v for k, v in _placar_temas_veo().items() if v[0] >= 2}
        partes = []
        if vt:
            top = max(vt, key=lambda k: vt[k][1] / vt[k][0])
            pior = min(vt, key=lambda k: vt[k][1] / vt[k][0])
            partes.append(f"tema que rende: {top} ({vt[top][1]:g}/{vt[top][0]}), pior: {pior} ({vt[pior][1]:g}/{vt[pior][0]})")
        ontem = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        regs = []
        with open(os.path.join(BASE, "logs", "foto_na_hora.jsonl"), encoding="utf-8") as f:
            regs = [json.loads(ln) for ln in f if ontem in ln]
        tent = [r for r in regs if "aprovada" in r]
        if tent:
            partes.append(f"fotos na hora ontem: {sum(1 for r in tent if r['aprovada'])}/{len(tent)} aprovadas")
        return (" | Funil Veo: " + "; ".join(partes)) if partes else ""
    except Exception:
        return ""


def _slug_tema(canal):
    """O mesmo slug do nome do arquivo (gerar: canal['nome'] -> veo_<slug>_<ts>__<canal>.mp4 na rede)."""
    return canal["nome"].replace(" ", "_").lower()[:15]


def _placar_temas_veo():
    """{slug_tema: (testes, vitorias)} do placar comum (D:\\postador-de-videos\\_analise\\placar_veo_temas.json)."""
    try:
        with open(r"D:\postador-de-videos\_analise\placar_veo_temas.json", encoding="utf-8") as f:
            g = json.load(f).get("grupos", {}).get("veo", {})
    except (OSError, ValueError):
        return {}
    return {k: (x.get("testes", 0), x.get("vitorias", 0)) for k, x in g.items()}


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
    """Score composto: critic score + bonus de metrics REAIS.

    Sem metrics: usa so o score do critic (proxy ate views chegarem).
    Com metrics: pesa RETENCAO e ENGAJAMENTO (o que o algoritmo premia),
    nao so views totais — 100k views com 1% de engajamento vale menos que
    10k com 15%. Retencao nos primeiros segundos e o maior sinal.
    """
    import math
    base = item.get("score", 0)
    metrics = item.get("metrics", {})
    if not metrics:
        return base
    views = metrics.get("views", 0)
    likes = metrics.get("likes", 0)
    comments = metrics.get("comments", 0)
    shares = metrics.get("shares", 0)
    # retencao: % media assistida (0-100) — o sinal mais forte do algoritmo
    retention = metrics.get("retention", metrics.get("avg_view_pct", 0))

    # Alcance (log de views): escala suave 0-2
    bonus_views = math.log10(max(views, 1)) * 0.5
    # Engajamento REAL: share pesa mais (viraliza), depois comment, depois like
    if views > 0:
        eng = (likes + comments * 3 + shares * 5) / views
        bonus_eng = min(eng * 20, 3.0)  # cap 3.0; 15% eng ~= +3
    else:
        bonus_eng = 0.0
    # Retencao: 0-100% vira bonus 0-3 (dobra o peso do engajamento cru)
    bonus_ret = min(max(retention, 0) / 100.0 * 3.0, 3.0)
    return base + bonus_views + bonus_eng + bonus_ret


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


VEO_VIRAL_MIN = int(os.environ.get("VEO_VIRAL_MIN", "1000"))  # views em 48 h pra contar como viral
VEO_VIRAL_REPLICAS = 3   # cada viral gera no maximo 3 variacoes (mais que isso vira "conteudo repetido")
VEO_VIRAL_PROB = 0.5     # metade dos videos do tema com viral vivo sai como variacao dele
_REPLICAS_FILE = os.path.join(BASE, "logs", "replicas_virais.json")
LIMPOS_DIR = r"D:\hipercool-materiais\veo\limpos"


def escolher_viral_do_funil(canal):
    """24/10 (dono: "dando preferencia a coisas mais virais"): clipe do MESMO tema que passou de VEO_VIRAL_MIN views em
    48 h (medidas do funil) e ainda tem replica sobrando -> pseudo-formula (fala do limpo) pra gerar_prompts_replicacao.
    None se nao houver ou se o sorteio (VEO_VIRAL_PROB) mandou fazer conteudo novo."""
    slug = _slug_tema(canal)
    try:
        estado = json.load(open(r"D:\postador-de-videos\config\telegram_estado.json", encoding="utf-8"))
        med = estado.get("medidas_48h", {})
        feitas = json.load(open(_REPLICAS_FILE, encoding="utf-8")) if os.path.exists(_REPLICAS_FILE) else {}
    except (OSError, ValueError):
        return None
    virais = {}
    with open(r"D:\postador-de-videos\logs\uploads_ledger.jsonl", encoding="utf-8") as f:
        for ln in f:
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            m = re.match(r"veo_((.+?)_\d{8}_\d{6})", str(r.get("arquivo") or ""))
            # tema EXATO (startswith deixava "dicas" pegar o viral de "dicas_financeir")
            if m and m.group(2) == slug and r.get("video_id") in med:
                v = int(med[r["video_id"]]["views"])
                if v >= VEO_VIRAL_MIN and feitas.get(m.group(1), 0) < VEO_VIRAL_REPLICAS:
                    virais[m.group(1)] = max(v, virais.get(m.group(1), 0))
    if not virais or random.random() > VEO_VIRAL_PROB:
        return None
    stem = max(virais, key=virais.get)
    try:
        meta = json.load(open(os.path.join(LIMPOS_DIR, stem + ".json"), encoding="utf-8"))
    except (OSError, ValueError):
        meta = {}
    if not meta.get("fala"):
        return None
    feitas[stem] = feitas.get(stem, 0) + 1
    with open(_REPLICAS_FILE, "w", encoding="utf-8") as f:
        json.dump(feitas, f, ensure_ascii=False, indent=1)
    log(f"[replica] VIRAL do funil: {stem} ({virais[stem]} views em 48 h) - variacao {feitas[stem]}/{VEO_VIRAL_REPLICAS}")
    return {"id": stem, "fala": meta["fala"], "cenario": meta.get("cenario") or canal.get("tema", ""),
            "canal": canal["nome"], "tema": canal["tema"], "score": 9, "metrics": {"views": virais[stem]},
            "video_path": stem + ".mp4"}


def escolher_formula_para_replicar(min_score=8, replica_prob=0.3, canal_nome=None):
    """Escolhe formula para replicar (30% chance). Score composto >= min_score. canal_nome: so do mesmo canal."""
    cache = load_cache()
    validas = [c for c in cache if c.get("video_path") and score_formula(c) >= min_score
               and (canal_nome is None or c.get("canal") == canal_nome)]
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
        if _castigo_desmentido(session_name, info, ate):
            return False
        return True
    except Exception:
        return False


def _castigo_desmentido(session_name, info, ate):
    """01/11 (dona: "não ficar tentando contas sem crédito" + 48 contas fora com 33 mil créditos): castigo de 6 h por
    "login caiu" numa conta que o painel de saúde LEU logada e com crédito DEPOIS do castigo = o erro foi da máquina/
    tentativa, não da conta. Tira o castigo (no máximo 1x por hora por conta, para não virar laço)."""
    motivo = str(info.get("last_motivo") or info.get("motivo") or "")
    if not re.search(r"login|deslogad", motivo):
        return False
    try:
        import flow_saldo_real
        r = flow_saldo_real.conta(session_name)
        if not r or (r["creditos"] or 0) < creditos_contas.MINIMO:
            return False
        posto_em = ate - datetime.timedelta(hours=6)
        if datetime.datetime.fromisoformat(r["quando"]) <= posto_em:
            return False
        ult = info.get("liberado_saude_em")
        if ult and (datetime.datetime.now() - datetime.datetime.fromisoformat(ult)).total_seconds() < 3600:
            return False
    except Exception:
        return False
    status = load_sessoes_status()
    i = status.get(session_name, {})
    i.pop("cooldown_until", None)
    i["liberado_saude_em"] = datetime.datetime.now().isoformat(timespec="seconds")
    status[session_name] = i
    save_sessoes_status(status)
    log(f"[sessao] {session_name}: castigo '{motivo[:40]}' desmentido — painel leu logada com {r['creditos']} "
        f"créditos em {','.join(r['maquinas'])} às {r['quando'][11:16]}; volta ao rodízio")
    return True


def porta_em_uso(port):
    """True se outro processo (o loop do veo ou o do ms-energy) esta gerando nesta porta agora (trava do gera_auto)."""
    from filelock import FileLock, Timeout as _Timeout
    trava = FileLock(os.path.join(BASE, "logs", f".cdp_lock_{port}"))
    try:
        trava.acquire(timeout=0)
    except _Timeout:
        return True
    except Exception:
        return False
    trava.release()
    return False


def marcar_conta_fora(session_name, motivo, horas):
    """Tira a conta do rodizio por algumas horas SEM contar como falha (nao entra no bloqueio global).
    Uso: login caiu / Flow bloqueou a conta (exit 3 do gera_auto)."""
    status = load_sessoes_status()
    info = status.get(session_name, {})
    ate = datetime.datetime.now() + datetime.timedelta(hours=horas)
    info["cooldown_until"] = ate.isoformat(timespec="seconds")
    info["last_motivo"] = motivo
    status[session_name] = info
    save_sessoes_status(status)
    log(f"[sessao] {session_name} fora do rodizio ate {ate:%d/%m %H:%M} ({motivo})")


def _maquina_livre_para(session):
    """Alguma maquina onde a conta "so notebook" esta logada esta livre agora (cache de 60 s por maquina)?"""
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import maquina_remota
        import contas
        return any(maquina_remota.maquina_livre(m)
                   for m in maquina_remota.maquinas_flow(contas.perfil_notebook(session)))
    except Exception:
        return False


def _algum_notebook_livre():
    """Alguma maquina com conta "so notebook" livre agora? (o Chrome do Flow roda la, nao gasta RAM do PC1)"""
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import maquina_remota
        maqs = {m for s in SESSOES if s.get("notebook") for m in maquina_remota.maquinas_flow(s["session"])}
        return any(maquina_remota.maquina_livre(m) for m in maqs)
    except Exception:
        return False


RESERVA_NOTEBOOKS = r"D:\postador-de-videos\config\notebooks_reservados.json"


def _reservar_notebooks(minutos=12, maquinas=None):
    """23/10 (Veo parado desde 18:52): entre ver o notebook livre e abrir o Chrome passam ~7 min (roteiro do agente) e
    o login do TikTok (postador bin\\netbooks\\tiktok_notebooks.py, varias contas por rodada) pegava o notebook antes.
    Reserva as maquinas do Flow por `minutos`: o login do TikTok pula notebook reservado (o Veo vem antes).
    maquinas=[...]: so essas (a geracao em andamento reserva a etapa pelo tempo todo; minutos=0 = solta)."""
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import maquina_remota
        maqs = set(maquinas) if maquinas is not None else \
            {m for s in SESSOES if s.get("notebook") for m in maquina_remota.maquinas_flow(s["session"])}
        try:
            with open(RESERVA_NOTEBOOKS, "r", encoding="utf-8") as f:
                res = json.load(f)
        except Exception:
            res = {}
        ate = time.time() + minutos * 60
        for m in maqs:
            # 23/10 (dona): a vez de OUTRO (login dela, postagem) nao e apagada — antes o Veo escrevia "veo" por cima
            # da reserva do login e o notebook voltava pro Veo/telao no meio do login
            atual = res.get(m) or {}
            if atual.get("por") not in (None, "veo") and float(atual.get("ate", 0)) > time.time():
                continue
            res[m] = {"por": "veo", "ate": ate}
        tmp = RESERVA_NOTEBOOKS + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
        os.replace(tmp, RESERVA_NOTEBOOKS)
    except Exception as e:
        log(f"[pause] nao reservei os notebooks ({type(e).__name__}: {e})")


def _em_login(maq):
    """Maquina com a janela de login da dona aberta (reserva "login ..." do maquina_remota.logar)."""
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import maquina_remota
        return "login" in maquina_remota.reservado(maq).lower()
    except Exception:
        return False


def _pausa_por_carga():
    """True se o PAUSE_SYSTEM ativo e o da carga do PC1 (nao a pausa manual da dona nem a de bloqueio)."""
    try:
        with open(os.path.join(BASE, "logs", "PAUSE_SYSTEM"), "r", encoding="utf-8") as f:
            return json.load(f).get("tipo") == "carga"
    except Exception:
        return False


def _tipo_pausa(motivo=False):
    """'carga' / 'bloqueio' / 'manual' do PAUSE_SYSTEM (motivo=True devolve o texto do motivo)."""
    try:
        with open(os.path.join(BASE, "logs", "PAUSE_SYSTEM"), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d.get("motivo", "?") if motivo else (d.get("tipo") if d.get("tipo") in ("carga", "bloqueio") else "manual")
    except Exception:
        return "?" if motivo else "manual"


_MOTIVO = None  # motivo do ultimo ciclo sem video (cadeia_veo.registrar_falha); None = nao conta (pausa da dona)


def _aplicar_etapa(etapa):
    """Env do gera_auto p/ a etapa: maquinas permitidas e se pode cair pra este PC."""
    nome, maqs = etapa
    os.environ["VEO_MAQUINAS"] = ",".join(maqs)
    if maqs == ["pc1"]:
        os.environ.pop("VEO_SO_NOTEBOOK", None)
        os.environ["FLOW_NOTEBOOKS"] = "0"
    else:
        os.environ["VEO_SO_NOTEBOOK"] = "1"  # nunca abre Chrome neste PC (e a pausa de carga nao barra o worker)
        os.environ["FLOW_NOTEBOOKS"] = "1"
    log(f"[cadeia] etapa {nome}: {','.join(maqs)}")


def pausado_sem_notebook():
    """Pausa que vale pro ciclo inteiro: qualquer pausa, menos a de carga do PC1 com notebook livre (23/10)."""
    return sistema_pausado() and not (_pausa_por_carga() and _algum_notebook_livre())


def _contas_vivas_kaggle():
    """Contas Google VIVAS do pool do Kaggle (mesma regra de flow-imagens/gera_imagem._contas_do_kaggle)."""
    if os.environ.get("FLOW_SEM_CONTA_KAGGLE", "1") == "0":
        return set()
    try:
        with open(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json", encoding="utf-8") as f:
            pool = json.load(f)
    except (OSError, ValueError):
        return set()
    return {str(c.get("cofre") or "").split("@")[0].lower() for c in pool.get("contas", [])
            if c.get("cofre") and not c.get("banida") and c.get("ativa", True) is not False}


def escolher_sessao(etapa=None):
    """Escolhe melhor sessao disponivel. etapa = (nome, [maquinas]) da cadeia (cadeia_veo.cadeia), ou None. Tenta em ordem do pool, pula as em cooldown e as que o outro robo
    (veo x ms-energy) esta usando agora — antes os dois pegavam a mesma 1a conta e um esperava a trava ate 15 min.

    Logga quais sessoes estao bloqueadas e por que (incluindo EXHAUSTED).
    Retorna None se TODAS estao bloqueadas — NAO martela SESSOES[0] (bug 2026-07-26:
    ficava horas tentando gerar em contas ja sem credito, timeout de 24min cada).
    """
    status = load_sessoes_status()
    bloqueadas = []

    def _tentar(s):
        """Retorna a sessao se disponivel (ou auto-liberavel), senao None e
        adiciona motivo em bloqueadas."""
        info = status.get(s["session"], {})
        # 11/11: a trava do 2º banimento (conta VIVA do Kaggle fora do Flow, flow-imagens/gera_imagem._contas_do_kaggle)
        # só existia nas IMAGENS; o Veo (reels das solares/reserva) seguia usando seebotsia/gabrielly/simone/mundosolar
        # /aulasrevolution — as 5 que estão rodando no Kaggle — por IPs de casa. FLOW_SEM_CONTA_KAGGLE=0 desliga.
        if s["session"].lower() in _contas_vivas_kaggle():
            bloqueadas.append(f"{s['session']}=CONTA DO KAGGLE")
            return None
        if info.get("status") == "EXHAUSTED":
            # AUTO-LIBERACAO: se o credito ja renovou (creditos_renova_em passou),
            # limpa o EXHAUSTED preso e reusa a conta. Antes ficava travado ate
            # limpeza manual mesmo depois da meia-noite (bug 2026-07-28).
            # 24/10: voltou ao original (a "checagem de saldo real" de 23/10 nunca lia o saldo: caminho de perfil
            # errado). O minimo de 20 creditos e garantido pelo creditos_contas e pelo worker (exit 2).
            if _renovacao_ja_passou(info):
                log(f"[pool] {s['session']} renovou credito — liberando EXHAUSTED automaticamente")
                _liberar_exhausted(s["session"])
                return s
            bloqueadas.append(f"{s['session']}=EXHAUSTED (renova {info.get('creditos_renova_em','?')})")
            return None
        if sessao_em_cooldown(s["session"]):
            bloqueadas.append(f"{s['session']}=COOLDOWN (ate {info.get('cooldown_until','?')})")
            return None
        _cf = creditos_contas.fora(s["session"])  # 23/10 (dona): menos de 20 creditos = fora ate renovar
        if _cf:
            bloqueadas.append(f"{s['session']}=POUCO CREDITO ({_cf})")
            return None
        if porta_em_uso(s["port"]):
            bloqueadas.append(f"{s['session']}=EM USO (porta {s['port']})")
            return None
        if etapa is not None:
            return s  # a cadeia ja viu que as maquinas da etapa estao livres (cadeia_veo.cadeia)
        if s.get("notebook") and not _maquina_livre_para(s["session"]):
            # 23/10: conta "so notebook" (contas.py) com as maquinas ocupadas postando/fora: pula sem penalizar
            bloqueadas.append(f"{s['session']}=MAQUINAS OCUPADAS")
            return None
        return s

    # PRIORIDADE (pedido Haylla 2026-07-29): gastar PRIMEIRO as contas 'free'
    # (credito diario pequeno ~55, use-it-or-lose-it — se nao usar hoje, perde),
    # e SO DEPOIS as 'pro' grandes (1050, credito acumula, nao urge). Assim o
    # credito diario das free nunca e desperdicado.
    # 23/10 (cadeia de alternativas, cadeia_veo.py): com ETAPA, so contas que rodam nas maquinas dela; dentro da etapa
    # (dona: "se a conta tiver sem credito, e so trocar de conta e nao de maquina") a de MAIS credito primeiro,
    # empate = a que renova antes (creditos_contas.ordenar). Nenhuma serve = None e o run() passa pra proxima etapa.
    if etapa is not None:
        _nome_et, _maqs_et = etapa
        if _maqs_et == ["pc1"]:
            cands = [s for s in SESSOES if not s.get("notebook")]
        else:
            cands = [s for s in SESSOES
                     if set(cadeia_veo.maquinas_da_conta(contas_mod.perfil_notebook(s["session"]))) & set(_maqs_et)]
        random.shuffle(cands)
        for s in creditos_contas.ordenar(cands, maquinas=_maqs_et):  # 01/11: saldo real NAS máquinas da etapa
            r = _tentar(s)
            if r:
                return r
        log(f"[pool] etapa {_nome_et}: nenhuma conta serve — {'; '.join(bloqueadas)[:300] or 'nenhuma conta logada la'}")
        return None
    # (sem etapa: comportamento antigo, usado no modo paralelo/chamadas de fora)
    # 23/10 (dono: "use o Veo em todas as contas que temos"): as contas logadas so nas maquinas vem ANTES de tudo
    # (tiram o Chrome do Flow do PC1); sorteadas pra espalhar o credito; maquinas ocupadas = _tentar pula
    _nb = [s for s in SESSOES if s.get("notebook")]
    random.shuffle(_nb)
    _nb = creditos_contas.ordenar(_nb)  # 01/11: mais crédito REAL primeiro, revezando pelo uso do dia
    for s in _nb:
        r = _tentar(s)
        if r:
            return r
    if os.environ.get("VEO_SO_NOTEBOOK") == "1":  # PC1 sem RAM p/ Chrome: contas daqui ficam de fora
        log(f"[pool] so notebook (PC1 sem RAM): nenhuma conta das maquinas livre — {'; '.join(bloqueadas)[:300]}")
        return None
    for s in contas_free():
        if s.get("notebook"):
            continue
        r = _tentar(s)
        if r:
            return r
    for s in contas_pro():
        r = _tentar(s)
        if r:
            return r

    if bloqueadas:
        log(f"[pool] todas sessoes bloqueadas: {'; '.join(bloqueadas)}")
    # Todas esgotadas/cooldown: NAO gerar (antes retornava SESSOES[0] e martelava).
    return None


def _renovacao_ja_passou(info):
    """True se creditos_renova_em existe e ja passou (credito renovado)."""
    rv = info.get("creditos_renova_em")
    if not rv:
        return False
    try:
        return datetime.datetime.now() >= datetime.datetime.fromisoformat(rv)
    except Exception:
        return False


def _liberar_exhausted(session_name):
    """Remove o status EXHAUSTED e campos de cooldown de uma sessao."""
    status = load_sessoes_status()
    info = status.get(session_name, {})
    for k in ("status", "cooldown_until", "creditos_renova_em",
              "padrao_creditos", "marked_exhausted_at"):
        info.pop(k, None)
    status[session_name] = info
    save_sessoes_status(status)


def _liberar_exhausted_com_saldo(session_name, saldo):
    """Remove o status EXHAUSTED e registra o saldo lido."""
    status = load_sessoes_status()
    info = status.get(session_name, {})
    for k in ("status", "cooldown_until", "creditos_renova_em",
              "padrao_creditos", "marked_exhausted_at"):
        info.pop(k, None)
    info["saldo_lido"] = saldo
    info["saldo_lido_em"] = datetime.datetime.now().isoformat(timespec="seconds")
    status[session_name] = info
    save_sessoes_status(status)


def _adiar_renovacao(session_name, horas):
    """Adia a renovacao de creditos por N horas."""
    status = load_sessoes_status()
    info = status.get(session_name, {})
    agora = datetime.datetime.now()
    nova_renovacao = agora + datetime.timedelta(hours=horas)
    info["creditos_renova_em"] = nova_renovacao.isoformat(timespec="seconds")
    status[session_name] = info
    save_sessoes_status(status)


def _ja_passou_horas(timestamp_iso, horas):
    """True se o timestamp passou ha mais de N horas."""
    try:
        ts = datetime.datetime.fromisoformat(timestamp_iso)
        agora = datetime.datetime.now()
        return (agora - ts).total_seconds() > (horas * 3600)
    except Exception:
        return True  # Se nao conseguir parsear, considera que passou


def _checar_saldo_conta(session_name, port, profile):
    """Checa o saldo de creditos de uma conta abrindo o Flow.

    Retorna o saldo (int) ou None se falhar.
    NAO gasta credito — so abre a pagina e le o menu.
    """
    try:
        # Importa aqui pra evitar circular import
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
        from creditos import ler_saldo_creditos

        log(f"[saldo] checando {session_name}...")

        # Monta caminho do perfil (mesmo padrao do gera_auto.py)
        cofre = os.path.join(os.path.dirname(os.path.dirname(BASE)), "logins-google", "cofre")
        if profile.startswith("profiles/"):
            profile_path = os.path.join(cofre, profile)
        else:
            profile_path = os.path.join(cofre, "perfis", profile)

        if not os.path.exists(profile_path):
            log(f"[saldo] perfil nao existe: {profile_path}")
            return None

        # Abre Chrome CDP na porta
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
                ctx = browser.contexts[0] if browser.contexts else None
                if not ctx:
                    log(f"[saldo] sem contexto ativo na porta {port}")
                    return None

                page = ctx.pages[0] if ctx.pages else ctx.new_page()

                # Vai pro Flow
                page.goto("https://labs.google/fx/pt/tools/flow", timeout=30000, wait_until="domcontentloaded")
                time.sleep(2)

                # Le o saldo
                saldo = ler_saldo_creditos(page, log=log)
                browser.close()
                return saldo

            except PWTimeout:
                log(f"[saldo] timeout ao abrir Flow")
                return None
            except Exception as e:
                log(f"[saldo] erro: {type(e).__name__} {str(e)[:100]}")
                return None

    except Exception as e:
        log(f"[saldo] falha geral: {type(e).__name__} {str(e)[:100]}")
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
        # Se o credito ja renovou, essa conta NAO conta como esgotada — o
        # escolher_sessao vai auto-liberar. Nao pula o ciclo por causa dela.
        if _renovacao_ja_passou(info):
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


# Subpasta de fotos por persona (item AT-06, 16/10): as 333 das subpastas nunca entravam (glob so na raiz). Todas as
# personas sao o dono, com as fotos dele (dono, 16/10). Persona fora do mapa (ou sem foto limpa no tema) usa a raiz.
# Separador de 16/10: limpas = epocas 157, guerra 64, herois 50, raiz 6, comedia 0, jornal 0. Sem foto limpa no tema
# -> qualquer foto limpa do dono (raiz + todas as subpastas), senao 20 personas repetiriam as mesmas 6 da raiz.
FOTOS_POR_PERSONA = {
    "comedia": ("Cassetadas IA", "Stand-up IA", "Humor de IA", "Alienigenas", "Robos Desastrados", "Fofos e Absurdos"),
    "epocas": ("ReCenas IA", "E Se..."),
    "guerra": ("E Se...",),
    "jornal": ("Noticias de IA",),
    "herois": ("Motivacao IA", "Recordes Mundiais", "Dicas Fitness"),
}
_MARCAS_FOTOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "marcas_fotos.json")


def _fotos_com_marca():
    """Caminhos (normalizados) das fotos com marca d'agua de IA no canto (separar_fotos_marcadas.py, 16/10): 298 das 305
    da raiz tinham "Grok", que passa para o video e a rede barra. Foto que o relatorio ainda nao viu NAO entra aqui
    (foto nova limpa funciona sem rodar o separador; o limpar_veo confere o video de qualquer jeito)."""
    try:
        with open(_MARCAS_FOTOS, encoding="utf-8") as f:
            rel = json.load(f)
    except Exception:
        return set()
    return {os.path.normcase(os.path.join(FOTOS_DIR, *k.split("/"))) for k, v in rel.items() if v.get("marca")}


def escolher_foto(canal=None):
    # Ignora fotos ja bloqueadas (ja isoladas por infra), as listadas no
    # arquivo de bloqueios ativos (logs/bloqueios_direitos.json) e as com marca de IA.
    bloqueadas = {os.path.normcase(f) for f in _listar_fotos_bloqueadas()} | _fotos_com_marca()
    try:  # 24/10: antigas com rosto que nao e o do dono (foto_na_hora.py antigas; 290 de 638) saem do sorteio
        import foto_na_hora
        bloqueadas |= foto_na_hora.fotos_antigas_reprovadas(FOTOS_DIR)
    except Exception:
        pass

    def _limpas(pasta):
        return [f for pat in ("*.jpg", "*.jpeg", "*.png") for f in glob.glob(os.path.join(pasta, pat))
                if os.path.normcase(f) not in bloqueadas]

    nome = (canal or {}).get("nome")
    fotos = [f for p, nomes in FOTOS_POR_PERSONA.items() if nome in nomes for f in _limpas(os.path.join(FOTOS_DIR, p))]
    if not fotos:
        fotos = _limpas(FOTOS_DIR) + [f for p in FOTOS_POR_PERSONA for f in _limpas(os.path.join(FOTOS_DIR, p))]
    if not fotos:
        return None  # sem foto limpa: melhor nao gerar do que gastar credito num video que a rede barra
    # 24/10 (dono: "nunca mudar o rosto"): so foto com o rosto conferido. As 638 antigas ja foram conferidas (cache);
    # foto nova na pasta e conferida aqui na hora (~0,2 s). Revisor fora do ar = sorteio antigo (com aviso no log).
    try:
        import foto_na_hora
        random.shuffle(fotos)
        for f in fotos[:30]:
            if foto_na_hora.rosto_ok(f, FOTOS_DIR):
                return f
        log("[foto] nenhuma das 30 fotos sorteadas passou no revisor de rosto")
        return None
    except Exception as e:
        log(f"[foto] revisor de rosto indisponivel ({str(e)[:60]}) - sorteio sem conferir")
        return random.choice(fotos)


# ============================================================================
# FASE 23: DIREITOS AUTORAIS — escalonamento automatico
# ============================================================================
# Quando o Flow recusa um par (foto, prompt) por politica, este modulo:
# 1) Registra o bloqueio e quais sessoes o confirmaram
# 2) Se o MESMO par for confirmado em >=2 sessoes distintas => troca_prompt
# 3) Se a MESMA foto for bloqueada em >=2 prompts reformulados distintos =>
#    isola_foto (move para D:\veo\fotos_bloqueadas\ e sai)
#
# Os bloqueios "em avaliacao" sao gravados em logs/bloqueios_direitos.json
# para sobreviverem entre ciclos. As fotos ja isoladas vivem em
# D:\veo\fotos_bloqueadas\ (separadas do pool vivo).

_BLOQUEIOS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "bloqueios_direitos.json")
_FOTOS_BLOQ_DIR = os.path.join(_RAIZ, "fotos_bloqueadas")


def _prompt_key(prompt):
    """Hash estavel do prompt — 8 chars hex. Ignora capitalizacao/espacos."""
    import hashlib
    if not prompt:
        return ""
    norm = " ".join(str(prompt).lower().split())
    return hashlib.md5(norm.encode("utf-8")).hexdigest()[:12]


def _foto_key(foto):
    return os.path.basename(foto) if foto else ""


def _carregar_bloqueios():
    if not os.path.exists(_BLOQUEIOS_PATH):
        return {}
    try:
        with open(_BLOQUEIOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _salvar_bloqueios(data):
    os.makedirs(os.path.dirname(_BLOQUEIOS_PATH), exist_ok=True)
    try:
        with open(_BLOQUEIOS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"[bloqueios] falha ao salvar: {e}")


def _listar_fotos_bloqueadas():
    """Retorna set com paths absolutos das fotos ja isoladas (pasta ou arquivo)."""
    bloqueadas = set()
    if os.path.isdir(_FOTOS_BLOQ_DIR):
        for pat in ("*.jpg", "*.jpeg", "*.png"):
            bloqueadas.update(glob.glob(os.path.join(_FOTOS_BLOQ_DIR, pat)))
    # tambem lista as isoladas por nome em arquivo json (caminho completo)
    data = _carregar_bloqueios()
    for fk, info in data.items():
        abs_path = info.get("abs_path")
        if abs_path and os.path.exists(abs_path):
            bloqueadas.add(abs_path)
    return bloqueadas


def _tratar_bloqueio_direitos(foto, prompt, sessao):
    """Registra bloqueio de politica, decide se escalona.

    Retorna (escalonar: bool, acao: 'manter'|'trocar_prompt'|'isolar_foto').
    """
    data = _carregar_bloqueios()
    fk = _foto_key(foto)
    pk = _prompt_key(prompt)
    if not fk or not pk:
        return False, "manter"
    info = data.setdefault(fk, {"prompts": {}, "isolada": False, "abs_path": os.path.abspath(foto) if foto else ""})
    prompts = info.setdefault("prompts", {})
    entry = prompts.setdefault(pk, {"sessoes": []})
    if sessao not in entry["sessoes"]:
        entry["sessoes"].append(sessao)
        log(f"[bloqueios] registrado: foto={fk} prompt={pk} sessoes={entry['sessoes']}")

    # JA estava isolada? so retorna.
    if info.get("isolada"):
        _salvar_bloqueios(data)
        return True, "isolar_foto"

    # Decisao 1: mesmo par (foto, prompt) em >=2 sessoes => trocar_prompt
    if len(entry["sessoes"]) >= 2:
        log(f"[bloqueios] par (foto={fk}, prompt={pk}) confirmado em "
            f"{len(entry['sessoes'])} sessoes — escalando TROCAR_PROMPT")
        # Marca o prompt original como 'trocado' (sinaliza para proximo
        # montar_prompt() que o cenario exige variacao)
        entry["trocado_em"] = datetime.datetime.now().isoformat(timespec="seconds")
        entry["trocas"] = entry.get("trocas", 0) + 1
        _salvar_bloqueios(data)
        return True, "trocar_prompt"

    # Decisao 2: MESMA foto com >=2 prompts bloqueados => isolar
    if len(prompts) >= 2:
        log(f"[bloqueios] foto={fk} bloqueada em {len(prompts)} prompts "
            f"distintos — escalando ISOLAR_FOTO")
        info["isolada"] = True
        info["isolada_em"] = datetime.datetime.now().isoformat(timespec="seconds")
        _salvar_bloqueios(data)
        try:
            os.makedirs(_FOTOS_BLOQ_DIR, exist_ok=True)
            dest = os.path.join(_FOTOS_BLOQ_DIR, fk)
            if os.path.exists(foto) and not os.path.exists(dest):
                import shutil
                shutil.move(foto, dest)
                log(f"[bloqueios] foto MOVIDA para {dest}")
        except Exception as e:
            log(f"[bloqueios] ERRO ao mover foto: {e}")
        return True, "isolar_foto"

    # ainda em avaliacao
    _salvar_bloqueios(data)
    return False, "manter"



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
    # 24/10: 1o o VIRAL MEDIDO do mesmo tema (funil 48 h, ex.: cassetadas 10,8 mil); depois o cache, so do MESMO canal
    # (antes replicava a formula de qualquer canal no tema sorteado: fala de fitness em video de alienigena)
    try:
        replica = escolher_viral_do_funil(canal) or escolher_formula_para_replicar(
            min_score=8, replica_prob=0.3, canal_nome=canal_nome)
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
        # 23/10: o cenario chegou com uma linha "/workspace" (resto de ferramenta do modelo) e foi assim pro Flow
        _lixo = re.compile(r"^\s*(/[\w./-]*|[A-Za-z]:\\\S*)\s*$")
        fala, cenario = ("\n".join(l for l in (t or "").splitlines() if not _lixo.match(l)).strip() or None
                         for t in (result.get("fala"), result.get("cenario")))
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

    from agents import prompt_com_fala  # mesmo formato do pipeline (AT-08a: aspas duplas + sem texto na tela)
    prompt = prompt_com_fala(cenario if cenario else tpl, fala)

    if len(HIST_FALAS.get(tema, [])) > 50:
        HIST_FALAS[tema] = HIST_FALAS[tema][-50:]
    if len(HIST_CENARIOS.get(tema, [])) > 30:
        HIST_CENARIOS[tema] = HIST_CENARIOS[tema][-30:]

    # Tier 2/3: CTA coerente com a persona (vai pra legenda do post, nao pro
    # video falado — 8s e curto demais pra encaixar CTA sem comer conteudo).
    cta = ""
    try:
        import inteligencia as _I
        cta = _I.cta_para_tema(tema)
    except Exception:
        pass

    return {
        "prompt": prompt,
        "fala": fala,
        "cenario": cenario,
        "fonte": fonte,
        "score": score,
        "iteracoes": iteracoes,
        "cta": cta,
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
       - "RECAPTCHA": reCAPTCHA bloqueando (sessao em cooldown 2h)

    A deteccao e feita por marcador especial no stderr/stdout de gera_auto.py.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [
        sys.executable,  # mesmo venv que rodou o cron (D:\veo\venv) — sem hardcode
        os.path.join(BASE, "gera_auto.py"),
        prompt,
        out_path,
    ]
    if foto and not os.environ.get("VEO_SKIP_PHOTO"):
        cmd.append(foto)
    # Timeout DINAMICO: base 20min, esticado quando a maquina esta apertada
    # (CPU/RAM sob carga fazem o Veo renderizar mais devagar). Subiu de 12min
    # pra 20min pois 'Novo projeto' pode demorar 60s+ com retries.
    try:
        tmo = recursos.timeout_dinamico(1200)
    except Exception:
        tmo = 1200
    # AT-12 (16/10): o worker so desiste em config.GEN_TIMEOUT_S + 120 (gera_auto.py, deadline da espera); matar antes
    # (1200 s) cortava geracao que ainda ia sair e contava como falha da conta. Timeout = deadline do worker + 60 s.
    try:
        import config as _cfg_veo
        tmo = max(tmo, int(_cfg_veo.GEN_TIMEOUT_S) + 120 + 60)
    except Exception:
        tmo = max(tmo, 1980)
    log(f"CMD: python gera_auto.py ... (timeout={tmo}s, {recursos.nivel_carga() if hasattr(recursos,'nivel_carga') else '?'})")
    # AT-12: a saida inteira do worker (prompt final, saldo, foto anexada) ia fora; agora vai para logs\worker_*.log
    _wlog = os.path.join(BASE, "logs", f"worker_{os.environ.get('FLOW_SESSION', 'sessao')}_"
                                       f"{datetime.datetime.now():%Y%m%d_%H%M%S}.log")

    def _gravar_worker(saida, erro, rc):
        try:
            with open(_wlog, "w", encoding="utf-8") as _f:
                _f.write(f"rc={rc}\n--- stdout ---\n{saida or ''}\n--- stderr ---\n{erro or ''}\n")
        except Exception:
            pass
    # 23/10 (dona): maquina da etapa fica reservada pelo Veo ENQUANTO a geracao durar (login do TikTok pula; o
    # vitrine.py deveria pular tambem — ver docs\CONTINUAR_DAQUI.md). Solta no fim, deu certo ou nao.
    _maq_res = [m for m in os.environ.get("VEO_MAQUINAS", "").split(",") if m and m != "pc1"]
    if _maq_res:
        _reservar_notebooks(minutos=tmo / 60 + 5, maquinas=_maq_res)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=tmo,
                                encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired as _te:
        if _maq_res:
            _reservar_notebooks(minutos=0, maquinas=_maq_res)
        _gravar_worker(_te.stdout if isinstance(_te.stdout, str) else (_te.stdout or b"").decode("utf-8", "replace"),
                       _te.stderr if isinstance(_te.stderr, str) else (_te.stderr or b"").decode("utf-8", "replace"),
                       "TIMEOUT")
        log(f"[gerar] TIMEOUT {tmo}s - marcando falha de sessao (log: {os.path.basename(_wlog)})")
        return False
    _gravar_worker(result.stdout, result.stderr, result.returncode)
    if _maq_res:
        _reservar_notebooks(minutos=0, maquinas=_maq_res)
    # 23/10 (dona: "abriu login, fecha o que tiver e considera como nao feito"): o login fechou este Chrome
    # (maquina_remota.ceder_veo) = nao e falha da conta — volta pra cadeia e vai pra outra maquina
    _ced = os.path.join(BASE, "logs", "veo_cedido_login.json")
    try:
        with open(_ced, encoding="utf-8") as _f:
            _cd = json.load(_f)
        if _cd.get("maquina") in _maq_res and time.time() - float(_cd.get("ts", 0)) < tmo + 600:
            os.remove(_ced)
            log(f"[gerar] {_cd['maquina']}: Chrome fechado pro login da dona — nao conta como falha, refaz noutra maquina")
            return "MAQUINA_OCUPADA"
    except (OSError, ValueError):
        pass
    # 23/10 (dona): controle de creditos por conta — o worker ja le o saldo no menu do Flow; aqui guarda, desconta o
    # custo do video que saiu e tira a conta (< VEO_CREDITO_MINIMO) ate renovar. Reprova do porteiro tambem gastou.
    try:
        _out_cr = (result.stdout or "") + (result.stderr or "")
        _c = creditos_contas.anotar_uso(
            os.environ.get("FLOW_SESSION", ""), _out_cr,
            gerou=result.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 100_000,
            sem_credito=result.returncode == 2 or "CREDITOS_ESGOTADOS" in _out_cr)
        if _c.get("saldo") is not None:
            log(f"[creditos] {os.environ.get('FLOW_SESSION', '')}: saldo {_c['saldo']}{' (estimado)' if _c.get('estimado') else ''}"
                f", hoje {_c.get('videos_hoje', 0)} video(s){' — FORA ate ' + str(_c['renova_em'])[5:16] if _c.get('renova_em') else ''}")
    except Exception as _e:
        log(f"[creditos] nao anotei ({type(_e).__name__}: {_e})")
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
    # Exit code 4 = Flow recusou por politica (pessoas famosas/direitos autorais).
    # NAO gastou credito. cron deve escalonar: trocar prompt -> trocar foto -> isolar.
    if result.returncode == 4 or "DIREITOS_AUTORAIS" in output:
        log("[gerar] DIREITOS AUTORAIS detectado (sem gasto de credito)")
        return "COPYRIGHT_BLOCKED"
    # Exit code 7 = reCAPTCHA Enterprise bloqueando. Cooldown longo (2h).
    if result.returncode == 7 or "RECAPTCHA_BLOQUEIO" in output:
        log("[gerar] RECAPTCHA Enterprise detectado — sessao precisa de cooldown longo")
        return "RECAPTCHA"
    # Exit code 3 = conta deslogada no Google/Flow ou bloqueada por idade: insistir nao adianta.
    if result.returncode == 3 or "SESSAO_EXPIRADA" in output:
        log("[gerar] SESSAO_EXPIRADA — conta deslogada ou bloqueada no Flow")
        return "SESSAO"
    # 23/10: conta "so notebook" e a maquina foi pega pelo postador entre a escolha e a abertura (16:12, 4 falhas +
    # 30 min de castigo a toa). Nada foi pedido no Flow: devolve o prompt pra fila sem penalizar a conta.
    # 23/10 (cadeia, cadeia_veo.py): maquina que falhou/estava ocupada fica de castigo (o x200ma comia ~7 min por ciclo)
    _vistas = cadeia_veo.anotar_maquinas(output)
    if "SO_NOTEBOOK:" in output:
        _sess = os.environ.get("FLOW_SESSION", "")
        if "age-restricted" in output:  # Flow bloqueado por idade nessa conta: nao insiste (so a dona resolve)
            marcar_conta_fora(_sess, "Flow bloqueado por idade (age-restricted)", horas=72)
        elif "SessaoExpiradaError" in output and not _vistas:  # deslogada em todas as maquinas tentadas
            marcar_conta_fora(_sess, "deslogada nas maquinas", horas=6)
        elif not _vistas:  # sem motivo claro: 15 min fora so p/ a cadeia nao repetir a mesma conta neste ciclo
            marcar_conta_fora(_sess, "nao abriu nas maquinas (sem motivo na saida)", horas=0.25)
        elif "SessaoExpiradaError" in output:
            # 24/10: uma maquina ocupada (castigada acima) + a conta DESLOGADA na outra. Nao e "deslogada em todas" (6 h),
            # mas sem marcar nada a cadeia escolhia a mesma conta de novo no mesmo ciclo (a de mais credito)
            marcar_conta_fora(_sess, "deslogada numa das maquinas (a outra estava ocupada)", horas=0.25)
        log(f"[gerar] maquinas da etapa ocupadas/fora na hora de abrir ({_vistas or 'conta'}) — "
            f"nada pedido ao Flow, segue a cadeia")
        return "MAQUINA_OCUPADA"
    if result.returncode != 0:
        log(f"ERRO gera_auto exit={result.returncode}: {result.stderr[-300:]}")
        return False
    return os.path.exists(out_path) and os.path.getsize(out_path) > 100_000


# Acima deste valor duas falas sao "a mesma coisa dita com outras palavras".
# Calibrado em 16/10/2026 sobre as 132 falas ja geradas (beta + experimental):
# entre falas DIFERENTES a semelhanca tem mediana 0,12 e p95 0,35; os pares que
# um humano chamaria de repetidos ficam em 0,82-0,89 (ex.: "Tudo o que te
# ensinaram sobre isso e uma mentira" x "Tudo o que te contaram sobre isso e
# mentira"). 0,62 pega os repetidos de verdade sem barrar tema parecido.
LIMIAR_FALA_REPETIDA = float(os.environ.get("VEO_LIMIAR_REPETIDA", "0.62"))


def fala_repetida(fala, limiar=None, max_itens=500):
    """A fala nova ja foi dita? Devolve o item parecido ou None. (item AT-04)

    Compara com TODO o historico do cache, nao so com o mesmo tema — repetir a
    mesma frase em canais diferentes e o padrao que o YouTube le como conteudo
    produzido em massa.
    """
    fala = (fala or "").strip()
    if not fala:
        return None
    lim = LIMIAR_FALA_REPETIDA if limiar is None else float(limiar)
    try:
        from conferir_fala import semelhanca
    except Exception:
        return None  # sem o modulo, nao atrapalha a producao
    try:
        cache = load_cache()
    except Exception:
        cache = []
    # falas de antes (importadas da experimental em 16/10): ficam num arquivo
    # proprio, SEM caminho de video, para nenhum postador confundir com fila.
    historicas = []
    try:
        _hp = os.path.join(BASE, "logs", "falas_historicas.json")
        if os.path.exists(_hp):
            with open(_hp, encoding="utf-8") as _f:
                historicas = (json.load(_f) or {}).get("falas") or []
    except Exception:
        pass
    melhor = None
    # So conta o que virou VIDEO: a FALHA TOTAL registra a formula com video_path None e devolve o prompt pra fila; sem
    # este corte o proximo ciclo achava a propria fala (semelhanca 1,0) e descartava o prompt ja pago (16/10, 3.3).
    # As historicas nao tem video_path (arquivo so de memoria) e contam sempre.
    feitos = [it for it in list(cache or [])[-max_itens:] if it.get("video_path")]
    for item in feitos + list(historicas):
        antiga = (item.get("fala") or "").strip()
        if not antiga:
            continue
        s = semelhanca(fala, antiga)
        if s >= lim and (melhor is None or s > melhor["semelhanca"]):
            melhor = {"fala": antiga, "semelhanca": round(s, 3),
                      "id": item.get("id"), "ts": item.get("ts")}
    return melhor


def sem_repetir(formula, canal, voltas=2):
    """Devolve uma formula cuja fala nao repete o historico (item AT-04).

    Se a fala repete, pede outra ate `voltas` vezes; se ainda assim repetir,
    devolve a ultima com aviso — nunca trava a producao por isto.
    Tem que ser usada em TODO ponto que monta prompt (inicio do ciclo, troca de
    prompt dentro da escada de tentativas e enchimento da fila): com a checagem
    so no inicio, a troca de prompt da escada passava direto pelo dedupe.
    """
    if not isinstance(formula, dict):
        return formula
    for _ in range(max(0, int(voltas))):
        rep = fala_repetida(formula.get("fala"))
        if not rep:
            return formula
        log(f"[repetida] a fala nova se parece {rep['semelhanca']} com a de "
            f"{rep.get('ts') or 'antes'}: {rep['fala'][:60]!r} — pedindo outra")
        try:
            nova = montar_prompt(canal)
        except Exception as e:  # noqa: BLE001
            log(f"[repetida] nao consegui outra fala ({str(e)[:60]}); seguindo com esta")
            return formula
        if not isinstance(nova, dict) or not nova.get("fala"):
            log("[repetida] a nova formula veio vazia; seguindo com a anterior")
            return formula
        formula = nova
    if fala_repetida(formula.get("fala")):
        log("[repetida] continuou parecida depois das tentativas; seguindo assim mesmo")
    return formula


# validar_video(path) daqui foi REMOVIDA em 16/10 (BX-04): obsoleta desde a Onda 1, ninguem chamava (grep em todos os
# projetos) e lia mensagem de erro do ffprobe como "tem audio". O porteiro usa `from validar_video import validar`.


def run():
    # FASE 14: Verifica se sistema esta pausado
    # 23/10: pausa por carga = falta RAM NESTE PC p/ abrir Chrome; com notebook livre o Chrome abre la (so notebook)
    # 23/10 (cadeia de alternativas): pausa MANUAL da dona e de BLOQUEIO param aqui (a cadeia nao fura); a de CARGA so
    # tira o PC1 da cadeia (notebooks/desktop/PC2 seguem)
    global _MOTIVO
    _MOTIVO = "ciclo sem video (ver cron_gerar_llm.log)"
    # 24/10: a reserva "veo" dos notebooks e DESTE ciclo; o worker (gera_auto) e a foto na hora herdam isto e nao pulam a
    # maquina reservada pra eles mesmos (maquina_remota.tentativas). So aqui dentro: o MS Energy importa este modulo e,
    # com isto no import, pegaria o notebook reservado pro Veo.
    os.environ["MAQUINA_VEZ_DE"] = "veo"
    os.environ.pop("VEO_SO_NOTEBOOK", None)
    os.environ.pop("VEO_MAQUINAS", None)
    os.environ.pop("FLOW_NOTEBOOKS", None)
    _carga_pc1 = False
    # 01/11: a pausa "disco_baixo" só saía pelo monitor_recursos.py, que não roda agendado -> o Veo ficou parado com
    # 11 GB livres. Pausa de carga POR DISCO + disco já ok = tira a pausa aqui (as outras pausas seguem iguais).
    try:
        if sistema_pausado() and _pausa_por_carga():
            with open(os.path.join(BASE, "logs", "PAUSE_SYSTEM"), "r", encoding="utf-8") as _f:
                _mot = json.load(_f).get("motivo")
            import recursos as _rec
            if _mot == "disco_baixo" and _rec.disco_ok():
                os.remove(os.path.join(BASE, "logs", "PAUSE_SYSTEM"))
                log(f"[pause] disco voltou ({_rec.disco_livre_gb():.0f} GB) — tirei a pausa de disco baixo")
    except Exception as _e:  # noqa: BLE001
        log(f"[pause] não conferi a pausa de disco ({type(_e).__name__})")
    if sistema_pausado():
        if not _pausa_por_carga():
            log("[pause] sistema pausado (manual da dona ou bloqueio), abortando — a cadeia nao fura essa pausa")
            _MOTIVO = None if _tipo_pausa() != "bloqueio" else f"pausa de bloqueio ({_tipo_pausa(motivo=True)})"
            return "PAUSA"
        _carga_pc1 = True
        log("[pause] PC1 pausado por carga — o PC1 sai da cadeia; seguem notebooks/desktop/PC2")

    # FLAG: cron_video desligado = nao gera novos videos.
    # (Util pra: parar geracao mas manter pos-producao rodando no backlog.)
    try:
        from pos_producao.flags import is_on as _flag_on
        if not _flag_on("cron_video"):
            log("[flag] cron_video OFF - pulando geracao")
            return "FLAG_OFF"
    except Exception:
        pass

    # GUARDA DE CREDITO (bug 2026-07-26): se TODAS as contas estao sem credito,
    # nao adianta montar prompt (gasta LLM) nem abrir Chrome (timeout de 24min).
    # Pula o ciclo inteiro ate o reset diario (meia-noite BR). O loop .bat espera
    # 30s e chama de novo; ate renovar, cada ciclo custa ~0 (so este cheque).
    esgotadas, renova = todas_sessoes_esgotadas()
    if esgotadas:
        log(f"[creditos] TODAS as contas sem credito — pulando ciclo (renova {renova or 'meia-noite'})")
        _MOTIVO = f"todas as contas do Flow sem credito (renova {renova or 'meia-noite'})"
        return "NO_ACCOUNTS"
    try:  # 23/10 (dona): 1 linha por dia no resumo de avisos com os creditos por conta
        creditos_contas.resumo_do_dia(SESSOES, lambda t: __import__("sys").path.insert(0, r"D:\video-fila")
                                      or __import__("avisos").enviar(t + _linha_funil(), "veo", importante=False))
    except Exception as _e:
        log(f"[creditos] resumo do dia nao saiu ({type(_e).__name__})")

    # Tier 1: fecha o loop de aprendizado — atualiza views reais 1x/hora.
    # No-op ate haver posted_url no cache ou YOUTUBE_API_KEY (custo ~0).
    _auto_fetch_metricas()

    # GUARDA DE CARGA (bug 2026-07-26): se a maquina esta afogada, NAO abre
    # Chrome (ele crasha sob carga). Em vez de queimar timeout, pausa ate o
    # recurso voltar — o monitor_recursos.py religa quando aliviar/de madrugada.
    # SKIP_RESOURCE_CHECK=1: Chrome ja esta aberto (modo paralelo), pula guarda.
    _modo_paralelo = os.environ.get("SKIP_RESOURCE_CHECK") == "1"
    _pc1_ram = True
    if _modo_paralelo:
        log("[carga] SKIP_RESOURCE_CHECK=1 — Chrome pre-aberto, pulando guarda")
    elif not _carga_pc1:
        try:
            import recursos
            if not recursos.disco_ok():
                log(f"[carga] disco baixo ({recursos.disco_livre_gb():.0f}GB) - pausando ate liberar")
                pausar_sistema(motivo="disco_baixo", ate_recurso=True)
                _MOTIVO = "disco baixo no PC1"
                return False
            _pc1_ram = recursos.slots_por_recurso() >= 1
            log(f"[carga] {recursos.resumo()}{'' if _pc1_ram else ' - sem RAM p/ Chrome aqui: PC1 fora da cadeia'}")
        except Exception as e:
            log(f"[carga] checagem falhou (seguindo): {str(e)[:80]}")

    # CADEIA DE ALTERNATIVAS (23/10, cadeia_veo.py): notebooks -> desktop sem chamada -> PC2/PC1 o mais livre. Montada
    # ANTES do prompt (nada livre = nao gasta LLM). No modo paralelo a conta vem fixa das env vars (sem cadeia).
    etapas = []
    if not _modo_paralelo:
        etapas, _fora = cadeia_veo.cadeia(pausa_carga=_carga_pc1, pc1_tem_ram=_pc1_ram)
        log(f"[cadeia] {cadeia_veo.resumo(etapas, _fora)}")
        if not etapas:
            _MOTIVO = "nenhuma maquina serve: " + "; ".join(f"{n}: {m}" for n, m in _fora)
            if not _pc1_ram and not _carga_pc1:  # comportamento antigo: PC1 sem RAM e nada mais = pausa de carga
                pausar_sistema(motivo="carga_critica", ate_recurso=True)
            return False
        if any(m in cadeia_veo.NOTEBOOKS + ("desktop",) for _n, ms in etapas for m in ms):
            # 12/11 (dona: "2 notebooks só pra Flow + pc2 + sti + desktop e sai 1 capa a cada 10 h"): o Veo reservava
            # TODAS as máquinas do Flow de todas as contas por 12 min a cada ciclo (as capas e imagens nunca achavam
            # vez). Agora só a máquina da 1ª etapa escolhida. VEO_RESERVA_SO_ETAPA=0 volta ao antigo.
            if os.environ.get("VEO_RESERVA_SO_ETAPA", "1") != "0":
                _reservar_notebooks(maquinas=[m for m in etapas[0][1] if m != "pc1"][:1])
            else:
                _reservar_notebooks()  # o login do TikTok nao pega o notebook entre a escolha e a abertura (~7 min)

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
        if foto and os.path.normcase(foto) in _fotos_com_marca():  # enfileirado antes do separador de 16/10
            foto = escolher_foto(canal)
            log(f"[fila] a foto do item tinha marca de IA - trocada por {os.path.basename(foto) if foto else 'NENHUMA'}")
            if not foto:
                log("ERRO: nenhuma foto LIMPA (sem marca de IA) - nao gera")
                return False
        elif foto and "fotos_na_hora" not in str(foto) and os.path.exists(foto):
            try:  # 24/10: item enfileirado antes do revisor de rosto pode trazer foto antiga com outro rosto
                import foto_na_hora
                if not foto_na_hora.rosto_ok(foto, FOTOS_DIR):
                    foto = escolher_foto(canal)
                    log(f"[fila] a foto do item nao passou no revisor de rosto - trocada por "
                        f"{os.path.basename(foto) if foto else 'NENHUMA'}")
            except Exception:
                pass
    else:
        formula = montar_prompt(canal_escolhido := escolher_canal_inteligente(CANAIS))
        canal = canal_escolhido
        foto = escolher_foto(canal)
        if not foto:
            log("ERRO: nenhuma foto LIMPA (sem marca de IA) encontrada - nao gera para nao gastar credito a toa")
            return False
        # FASE 15: Foto inteligente (considera matches historicos)
        if formula.get("cenario"):
            foto_inteligente = escolher_foto_inteligente(foto, formula["cenario"])
            if foto_inteligente != foto:
                log(f"[match] usando foto inteligente: {os.path.basename(foto_inteligente)}")
                foto = foto_inteligente

    # ---- JA DISSEMOS ISSO? (item AT-04 de docs\PLANO_MELHORIAS_VEO.md) -------
    # Ate 15/10 a unica defesa contra repetir era mandar as ultimas 10 falas DO
    # MESMO TEMA no prompt pedindo "nao repita" — nada comparava de verdade, e
    # nada cruzava temas. "Shorts de IA muito parecidos entre si" esta na lista
    # de causas da suspensao dos 22 canais (SPAM_BANIMENTO_2026-09-04.md).
    # Aqui a fala nova e comparada com TODO o historico antes de gastar credito.
    # Se repetir, pede outra; se insistir, deixa passar com aviso (nunca trava).
    formula = sem_repetir(formula, canal)

    prompt = formula["prompt"]
    fala = formula["fala"]
    fonte = formula["fonte"]
    score = formula["score"]
    iteracoes = formula["iteracoes"]

    # FOTO NA HORA (24/10, dono): a foto sorteada nao combinava com o cenario do prompt. O Flow cria a foto do dono ja
    # no cenario, a partir das fotos-base de fundo branco; o revisor de rosto (foto_na_hora.revisar) so deixa passar o
    # rosto dele. Falhou/reprovou = segue com a foto antiga. VEO_FOTO_NA_HORA=0 desliga.
    if foto and "fotos_na_hora" in str(foto) and os.path.exists(foto):
        # 24/10: prompt que voltou da fila ja tem a foto aprovada dele (nao gasta 1-6 min refazendo)
        log(f"[foto_na_hora] reaproveitando a foto aprovada do item da fila: {os.path.basename(foto)}")
    elif not os.environ.get("VEO_SKIP_PHOTO"):
        try:
            import foto_na_hora
            # 24/10: so as maquinas que a cadeia liberou (notebook sem telao, desktop sem chamada, PC1 so sem pausa de
            # carga). Sem isso o Flow abriu Chrome no PC1 em pausa de carga (teste das 15:24). Modo paralelo: sem cadeia.
            _maqs_foto = list(dict.fromkeys(m for _n, ms in etapas for m in ms)) if etapas else None
            _fh = foto_na_hora.gerar(formula.get("cenario") or "", prompt, tag=_slug_tema(canal), maquinas=_maqs_foto)
            if _fh:
                log(f"[foto_na_hora] foto no cenario aprovada pelo revisor de rosto: {os.path.basename(_fh)}")
                foto = _fh
            else:
                log("[foto_na_hora] sem foto aprovada - usando a foto antiga")
        except Exception as e:
            log(f"[foto_na_hora] erro ({str(e)[:100]}) - usando a foto antiga")
        # a foto leva ate ~7 min; somada ao roteiro do agente passava da reserva de 12 min feita no comeco do ciclo e o
        # login do TikTok podia pegar o notebook antes do Veo abrir o Chrome: renova a reserva aqui
        if etapas and any(m in cadeia_veo.NOTEBOOKS + ("desktop",) for _n, ms in etapas for m in ms):
            if os.environ.get("VEO_RESERVA_SO_ETAPA", "1") != "0":  # 12/11: só a máquina da 1ª etapa
                _reservar_notebooks(maquinas=[m for m in etapas[0][1] if m != "pc1"][:1])
            else:
                _reservar_notebooks()
    # sem foto valida no disco (a do item da fila sumiu na limpeza, ou nenhuma antiga passou no revisor): sorteia uma
    # conferida; nenhuma = nao gera (sem foto o Veo faria texto->video com uma pessoa qualquer, nao o dono)
    if not foto or not os.path.exists(foto):
        foto = escolher_foto(canal)
        if not foto:
            log("ERRO: nenhuma foto do dono disponivel (na hora falhou e nenhuma antiga passou) - nao gera")
            _MOTIVO = "sem foto do dono (foto na hora falhou e nenhuma antiga passou no revisor de rosto)"
            return False
        log(f"[foto] foto de reserva conferida: {os.path.basename(foto)}")

    # RESILIENCIA (pedido Haylla 2026-07-29): escada de tentativas.
    #   falhou TENTATIVAS_POR_PROMPT vezes no mesmo prompt -> troca o PROMPT (mesma conta)
    #   trocou PROMPTS_POR_CONTA prompts e ainda falhou     -> troca a CONTA
    #   creditos esgotados                                  -> troca de CONTA na hora
    # Antes so trocava de conta a cada falha e nunca regenerava o prompt (e tinha
    # um bug: usava 'motivo' indefinido -> NameError na 1a falha generica).
    try:
        _score_num = float(score)
    except (TypeError, ValueError):
        _score_num = 7.0
    TENTATIVAS_POR_PROMPT = 2
    # video fraco (score baixo) nao vale queimar varias contas nem regenerar muito.
    PROMPTS_POR_CONTA = 2 if _score_num >= 5.5 else 1
    MAX_CONTAS = min(3, len(SESSOES)) if _score_num >= 5.5 else 1
    CAP_POR_CONTA = TENTATIVAS_POR_PROMPT * PROMPTS_POR_CONTA
    max_tentativas = CAP_POR_CONTA * MAX_CONTAS

    tentativas = []
    sessao = None
    tentativas_na_conta = 0
    # Quantos videos o PORTEIRO reprovou neste ciclo. Conta separada das falhas de
    # geracao: video ruim nao e culpa da conta, e insistir custa credito (cada
    # volta e uma geracao paga).
    reprovas_porteiro = 0
    MAX_REPROVAS_PORTEIRO = int(os.environ.get("VEO_MAX_REPROVAS", "2"))
    _modo_paralelo = os.environ.get("SKIP_RESOURCE_CHECK") == "1"
    if _modo_paralelo:
        _fs = os.environ.get("FLOW_SESSION", "")
        _fp = os.environ.get("FLOW_PORT", "")
        _ff = os.environ.get("FLOW_PROFILE", "")
        if _fs and _fp:
            sessao = {"session": _fs, "port": _fp, "profile": _ff}
            log(f"[paralelo] conta fixa das env vars: {_fs} porta {_fp}")
            MAX_CONTAS = 1
            max_tentativas = CAP_POR_CONTA
    _ocupadas_n = 0
    etapa_i = 0  # posicao na cadeia (cadeia_veo): sem credito troca a CONTA; maquina ocupada/sem conta troca a ETAPA
    tentativa_n = -1
    while tentativa_n + 1 < max_tentativas:  # era for/range: maquina ocupada (nada pedido ao Flow) nao gasta tentativa
        tentativa_n += 1
        # (re)escolhe conta na 1a vez ou quando esgotou as tentativas desta conta
        if sessao is None or (tentativas_na_conta >= CAP_POR_CONTA and not _modo_paralelo):
            if sessao is not None and tentativas_na_conta >= CAP_POR_CONTA:
                # abandona a conta apos CAP falhas (ja trocou prompt): cooldown curto
                log(f"[resiliencia] {CAP_POR_CONTA} falhas na conta {sessao['session']} — trocando de CONTA")
                registrar_falha_sessao(sessao["session"], "falhas repetidas apos trocar prompt")
                _st = load_sessoes_status()
                _inf = _st.get(sessao["session"], {})
                _inf["cooldown_until"] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat(timespec="seconds")
                _st[sessao["session"]] = _inf
                save_sessoes_status(_st)
            sessao = None
            while etapas and etapa_i < len(etapas):
                _aplicar_etapa(etapas[etapa_i])
                sessao = escolher_sessao(etapas[etapa_i])
                if sessao is not None:
                    break
                etapa_i += 1  # nenhuma conta com credito/logada nas maquinas desta etapa: proxima maquina
            if not etapas:
                sessao = escolher_sessao()
            if sessao is None:
                # Todas as contas esgotaram. Preserva o prompt na fila e sai sem martelar.
                log("[creditos] sem conta disponivel — preservando prompt na fila")
                _MOTIVO = ("nenhuma conta com credito/livre em nenhuma etapa da cadeia ("
                           + " -> ".join(n for n, _m in etapas) + "); ver [pool] no log")
                try:
                    import fila
                    _it = item_fila if item_fila else {"formula": formula, "foto": foto, "canal": canal, "tentativas": 0}
                    fila.enfileirar(_it["formula"], foto or _it["foto"], _it["canal"], prioridade=True)
                except Exception:
                    pass
                return "NO_ACCOUNTS"
            tentativas.append(sessao["session"])
            aplicar_sessao(sessao)
            tentativas_na_conta = 0

        # troca o PROMPT a cada TENTATIVAS_POR_PROMPT falhas na mesma conta
        if tentativas_na_conta > 0 and tentativas_na_conta % TENTATIVAS_POR_PROMPT == 0:
            log(f"[resiliencia] {TENTATIVAS_POR_PROMPT} falhas no prompt — trocando o PROMPT (conta {sessao['session']})")
            try:
                formula = sem_repetir(montar_prompt(canal), canal)
                prompt = formula["prompt"]; fala = formula["fala"]
                fonte = formula["fonte"]; score = formula["score"]; iteracoes = formula["iteracoes"]
            except Exception as e:
                log(f"[resiliencia] regen de prompt falhou ({str(e)[:60]}) — mantendo prompt anterior")
        tentativas_na_conta += 1

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = canal["nome"].replace(" ", "_").lower()[:15]
        out_name = f"{slug}_{ts}.mp4"
        out_path = os.path.join(VIDEOS_DIR, out_name)

        log(f"=== GERANDO === Canal: {canal['nome']} | Tema: {canal['tema']} | Fonte: {fonte} | Score={score}/10 | Sessao={sessao['session']} (tentativa {tentativa_n+1})")
        log(f"Foto: {os.path.basename(foto)}")
        log(f"Fala: {fala}")
        log(f"Prompt: {prompt[:150]}...")

        try:  # 24/10: o funil mede se a foto no cenario rende mais que a antiga (placar veo_foto do postador)
            _fpc = os.path.join(BASE, "logs", "veo_foto_por_clipe.json")
            _d = json.load(open(_fpc, encoding="utf-8")) if os.path.exists(_fpc) else {}
            # ficha do clipe pro funil (o Veo nao tem postar.json): foto, fonte do prompt e faixa da nota do critico
            _d[os.path.splitext(out_name)[0]] = {
                "foto": "na_hora" if "fotos_na_hora" in str(foto) else "antiga",
                "fonte": str(fonte or "?"),
                "nota": f"{int(float(score))}" if str(score).replace(".", "", 1).isdigit() else "?"}
            for _k in list(_d)[:-3000]:  # o medidor so precisa dos ultimos dias; nao deixa o arquivo crescer pra sempre
                del _d[_k]
            # troca atomica: o medidor do postador (outro processo) le este arquivo e um json pela metade fazia o video
            # ficar marcado como foto "antiga" pra sempre
            with open(_fpc + ".tmp", "w", encoding="utf-8") as _f:
                json.dump(_d, _f, ensure_ascii=False, indent=0)
            os.replace(_fpc + ".tmp", _fpc)
        except Exception:
            pass
        ok = gerar_video(prompt, foto, out_path)
        # Caso 0a (23/10, cadeia): maquinas da etapa ocupadas/fora na hora de abrir — NADA foi pedido ao Flow. Antes o
        # ciclo inteiro abortava aqui (18:52-22:40 de 23/10 em loop). Agora: tira da etapa as maquinas de castigo e,
        # se nao sobrar nenhuma, passa pra proxima etapa; nao conta tentativa nem castiga a conta.
        if ok == "MAQUINA_OCUPADA" and etapas:
            _n, _ms = etapas[etapa_i]
            _ms = [m for m in _ms if m == "pc1" or not (cadeia_veo.castigo(m) or _em_login(m))]
            if _ms:
                etapas[etapa_i] = (_n, _ms)
            else:
                etapa_i += 1
            sessao = None
            tentativas_na_conta = 0
            _ocupadas_n += 1
            if _ocupadas_n <= 3 * len(etapas) + 3:  # teto: nunca fica girando no mesmo ciclo
                max_tentativas += 1
            if etapa_i >= len(etapas):
                _MOTIVO = "maquinas da cadeia ocupadas/fora na hora de abrir (ver [cadeia] no log)"
            continue
        if ok == "MAQUINA_OCUPADA":
            ok = "PAUSED"  # sem cadeia (modo paralelo): comportamento antigo
        # Caso 0: sistema pausou no meio → devolve o prompt pra fila e sai limpo
        if ok == "PAUSED":
            try:
                import fila
                _it = item_fila if item_fila else {"formula": formula, "foto": foto, "canal": canal, "tentativas": 0}
                fila.enfileirar(_it["formula"], foto or _it["foto"], _it["canal"], prioridade=True)
            except Exception:
                pass
            log("[pause] abortando ciclo (prompt preservado na fila)")
            return False
        # Caso 1: creditos esgotados → marca EXHAUSTED + FORCA troca de conta
        if isinstance(ok, tuple) and ok[0] == "NO_CREDITS":
            padrao_achou = ok[1] if len(ok) > 1 else ""
            log(f"[CREDITOS] {sessao['session']} SEM CREDITOS! padrao='{padrao_achou}'")
            marcar_creditos_esgotados(sessao["session"], padrao_texto=padrao_achou)
            sessao = None  # forca escolher_sessao() no topo do loop (troca de CONTA)
            continue
        # Caso 1b: reCAPTCHA Enterprise → cooldown 15min + troca de conta
        if ok == "RECAPTCHA":
            log(f"[RECAPTCHA] {sessao['session']} bloqueada por reCAPTCHA — cooldown 15min")
            from datetime import datetime as _dt, timedelta as _td
            _status = load_sessoes_status()
            _s = sessao["session"]
            if _s not in _status:
                _status[_s] = {"status": "ok", "failures": 0}
            _status[_s]["cooldown_until"] = (_dt.now() + _td(minutes=15)).isoformat()
            _status[_s]["motivo"] = "reCAPTCHA Enterprise"
            save_sessoes_status(_status)
            sessao = None
            continue
        # Caso 1c: conta deslogada/bloqueada → 6 h fora do rodizio + troca de conta
        if ok == "SESSAO":
            marcar_conta_fora(sessao["session"], "login caiu ou conta bloqueada no Flow", horas=6)
            sessao = None
            continue
        if ok:
            # ================= PORTEIRO (16/10/2026) =========================
            # Itens AT-02 e AT-01 de docs\PLANO_MELHORIAS_VEO.md. Antes disto, a
            # unica conferencia vinha DEPOIS de copiar o mp4, gerar 3 thumbs e
            # escrever o postar.json — e so olhava dimensao e codec de audio. Um
            # video mudo, de 4 s, no formato errado ou falando outra coisa entrava
            # no cache como SUCESSO e virava "formula vencedora" para replicar.
            # Agora nada e registrado, copiado ou publicado antes de passar aqui.
            _reprovado = None

            # 1) o arquivo presta? (9:16, duracao, audio, sem preto/congelado,
            #    e decodifica de verdade). VEO_VALIDAR=0 desliga tudo; VEO_VALIDAR_IMAGEM=0 so a de
            #    preto/congelado (a decodificacao continua: e ela que pega arquivo quebrado).
            if os.environ.get("VEO_VALIDAR", "1") != "0":
                try:
                    from validar_video import validar as _validar, resumo as _resumo_val
                    # a duracao vem do que foi PEDIDO ao Flow (FLOW_DURATION=8S),
                    # nao de um 8 cravado aqui
                    _dur_pedida = float(re.sub(r"[^\d.]", "",
                                               os.environ.get("FLOW_DURATION", "8")) or 8)
                    _v = _validar(out_path, duracao_esperada=_dur_pedida,
                                  checar_imagem=os.environ.get("VEO_VALIDAR_IMAGEM", "1") != "0")
                    log(f"[validacao] {_resumo_val(_v)}")
                    if not _v.get("ok"):
                        _reprovado = "; ".join(_v.get("problemas") or ["reprovado"])
                except Exception as _e:
                    # a conferencia nunca pode derrubar a producao: sem ela, segue
                    log(f"[validacao] nao rodou (seguindo): {str(_e)[:80]}")

            # 2) falou o que pedimos, em portugues? (ffprobe nao ouve o idioma)
            #    VEO_CONFERIR_FALA=0 desliga. Custo medido em 16/10: ~6 s pelo
            #    Groq (whisper-large-v3) e ~15-22 s no modelo local de reserva.
            if not _reprovado and os.environ.get("VEO_CONFERIR_FALA", "1") != "0":
                try:
                    from conferir_fala import conferir as _conferir
                    _c = _conferir(out_path, fala)
                    log(f"[fala] {_c.get('motivo')}")
                    if _c.get("ok") is False:
                        _reprovado = _c.get("motivo")
                    # ok=None (nao deu para transcrever) NAO reprova: so fica no log
                except Exception as _e:
                    log(f"[fala] nao rodou (seguindo): {str(_e)[:80]}")

            # 3) 24/10 (dono: "prioridade nunca mudar o rosto"): o Veo pode deformar o rosto no meio do clipe; 3 quadros
            #    contra as fotos-base (foto_na_hora.revisar_video). VEO_CONFERIR_ROSTO=0 desliga; revisor fora = segue.
            if not _reprovado and os.environ.get("VEO_CONFERIR_ROSTO", "1") != "0":
                try:
                    import foto_na_hora
                    _okr, _notas, _mr = foto_na_hora.revisar_video(out_path)
                    log(f"[rosto] {_mr} {_notas}")
                    if not _okr:
                        _reprovado = _mr
                except Exception as _e:
                    log(f"[rosto] nao rodou (seguindo): {str(_e)[:80]}")

            if _reprovado:
                log(f"REPROVADO: {_reprovado}")
                _MOTIVO = f"porteiro reprovou o video ({str(_reprovado)[:120]})"
                reprovas_porteiro += 1
                # Tira o arquivo da pasta de producao. Ela e varrida pelo
                # worker_noite e pelo cron_video_watcher (glob *.mp4), entao um
                # reprovado esquecido aqui vira COMPLETO e chega ao TikTok.
                try:
                    import shutil as _sh
                    _rej_dir = os.path.join(VIDEOS_DIR, "rejeitados")
                    os.makedirs(_rej_dir, exist_ok=True)
                    _base = os.path.basename(out_path)
                    _dst = os.path.join(_rej_dir, _base)
                    if os.path.exists(_dst):  # nome repetido nao pode sobrescrever
                        _dst = os.path.join(
                            _rej_dir, f"{os.path.splitext(_base)[0]}_"
                                      f"{datetime.datetime.now():%H%M%S}{os.path.splitext(_base)[1]}")
                    # o motivo primeiro: se o move falhar, o registro ja existe
                    with open(_dst + ".motivo.txt", "w", encoding="utf-8") as _f:
                        _f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\n"
                                 f"canal: {canal['nome']}\nfala pedida: {fala}\nmotivo: {_reprovado}\n")
                    _sh.move(out_path, _dst)
                except Exception as _e:
                    log(f"[rejeitado] nao movi o arquivo: {str(_e)[:60]}")
                    # No Windows o shutil.move copia e so depois apaga: com o
                    # arquivo presa por antivirus/player, a copia vai para
                    # rejeitados e o ORIGINAL fica na pasta de producao. Entao
                    # garante a saida daqui, nem que seja renomeando.
                    try:
                        if os.path.exists(out_path):
                            os.replace(out_path, out_path + ".reprovado")
                            log("[rejeitado] renomeado para .reprovado (fora do glob *.mp4)")
                    except Exception as _e2:
                        log(f"[rejeitado] ATENCAO: o arquivo reprovado CONTINUA em "
                            f"{VIDEOS_DIR} ({str(_e2)[:50]}) — apague na mao")
                # A CONTA FUNCIONOU: quem falhou foi o video. Marca sucesso da
                # sessao para a reprova nao virar "falha de conta" la embaixo
                # (isso tirava do rodizio uma conta boa e podia pausar o sistema).
                registrar_sucesso_sessao(sessao["session"])
                if reprovas_porteiro >= MAX_REPROVAS_PORTEIRO:
                    # 2 videos ruins seguidos = o problema e o prompt ou o modelo,
                    # nao a sorte. Parar aqui vale mais que gastar ate 12 geracoes
                    # pagas num ciclo que nao publica nada.
                    log(f"[porteiro] {reprovas_porteiro} videos reprovados neste ciclo — "
                        f"encerrando (o proximo ciclo comeca com outro prompt)")
                    return False
                # tenta de novo: a escada troca o PROMPT a cada TENTATIVAS_POR_PROMPT
                continue
            # ============== fim do porteiro; daqui pra baixo o video presta ====

            registrar_sucesso_sessao(sessao["session"])
            cadeia_veo.registrar_sucesso()  # zera o "sem gerar ha N h"
            _MOTIVO = None
            # ...resto do codigo
            save_hist()
            video_id = registrar_formula(
                canal["nome"], canal["tema"], fala, formula["cenario"],
                prompt, foto, out_path, score, iteracoes, fonte
            )
            log(f"[cache] id={video_id} salvo para analise de viralizacao")

            # Copia MP4 pra materiais (redundancia pro postador)
            try:
                import shutil as _sh
                _mat_dir = os.path.join(r"D:\hipercool-materiais\veo\cron_shorts")
                os.makedirs(_mat_dir, exist_ok=True)
                _mat_dst = os.path.join(_mat_dir, os.path.basename(out_path))
                if not os.path.exists(_mat_dst):
                    _sh.copy2(out_path, _mat_dst)
                    log(f"[materiais] copiado -> {_mat_dst}")
            except Exception as _e:
                log(f"[materiais] falha ao copiar: {_e}")

            # Tier 2/3: guarda CTA + familia de gancho no cache.
            # CTA -> postador usa na legenda. hook_family -> A/B aprende depois
            # (quando metricas chegarem) qual abertura performa por canal.
            try:
                _cta = formula.get("cta")
                _hook_fam = None
                try:
                    import inteligencia as _I
                    _hook_fam = _I.classificar_gancho(fala)
                except Exception:
                    pass
                if _cta or _hook_fam:
                    cache = load_cache()
                    for item in cache:
                        if item["id"] == video_id:
                            if _cta:
                                item["cta"] = _cta
                            if _hook_fam:
                                item["hook_family"] = _hook_fam
                            save_cache(cache)
                            break
            except Exception as e:
                log(f"[meta] cta/hook nao salvos (seguindo): {str(e)[:60]}")

            # FASE 10: Gera 3 thumbnails A/B test
            thumbs = {}
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

            # FECHA O CICLO: gera postar.json ao lado do mp4 (titulo/descricao/
            # tags via LLM + CTA + thumbnail A). O postador le esse doc e posta
            # sem adivinhar. Sem isso o video fica orfao. Falha nao bloqueia.
            try:
                from publicar import gerar_postar_json
                _thumb_capa = thumbs.get("A") if isinstance(thumbs, dict) else None
                _pj = gerar_postar_json(
                    out_path, canal["nome"], canal["tema"], fala,
                    cta=formula.get("cta") or "", thumb=_thumb_capa,
                    extra={"video_id": video_id, "score": score, "fonte": fonte},
                )
                if _pj:
                    log(f"[publicar] postar.json gerado: {_pj}")
            except Exception as e:
                log(f"[publicar] postar.json nao gerado (seguindo): {str(e)[:80]}")

            # (a conferencia de verdade ja aconteceu no PORTEIRO, antes de
            #  registrar e copiar. Aqui so o tamanho, para o log.)
            size_kb = os.path.getsize(out_path) // 1024
            log(f"SUCESSO: {out_name} ({size_kb}KB)")
            avisar_desktop("Veo: video pronto", f"{canal['nome']} - {out_name}")

            # POS-PRODUCAO (incremental): se flag pos_video ON, roda o pipeline
            # no video recem-gerado. Falha nao bloqueia o ciclo.
            try:
                from pos_producao.flags import is_on as _flag_on
                if _flag_on("pos_video"):
                    from pos_producao.runner import run_one as _run_one
                    log("[pos] rodando pipeline no video recem-gerado")
                    # passa fala+tema+canal pra os plugins saberem o que narrar
                    _meta_extra = {
                        "fala": fala,
                        "tema": canal.get("tema"),
                        "canal_nome": canal.get("nome"),
                        "cenario_en": formula.get("cenario") if formula else None,
                    }
                    _run_one(out_path, meta_extra=_meta_extra)
                else:
                    log("[pos] flag pos_video OFF - pulando pos-producao")
            except Exception as e:
                log(f"[pos] pipeline nao rodou (seguindo): {str(e)[:100]}")

            return True
        else:
            # Falha: registra e tenta proxima
            if ok == "COPYRIGHT_BLOCKED":
                # Recusa por politica NAO conta como cooldown de sessao —
                # a sessao pode estar saudavel; o problema e o PROMPT+FOTO.
                # Apenas logamos e seguimos para a proxima sessao pra
                # confirmar se o bloqueio se repete (persistente = problema
                # do par, nao da conta).
                log(f"[DIREITOS] {sessao['session']} recussou politica "
                    f"(foto={os.path.basename(foto) if foto else '?'}); "
                    f"tentando proxima sessao pra confirmar persistencia")
                sessao_que_bloqueou = sessao["session"]
                try:
                    _escal, acao = _tratar_bloqueio_direitos(foto, prompt, sessao_que_bloqueou)
                except Exception as _e:
                    log(f"[DIREITOS] erro no escalonamento: {_e}")
                    _escal, acao = False, "manter"
                if _escal:
                    if acao == "trocar_prompt":
                        # prompt reformulado ja foi salvo em formula; sai do loop
                        # (a foto vai para a lista de 'quentes' mas mantem-se viva).
                        log("[DIREITOS] escalando: novo prompt sera usado no proximo ciclo")
                        # Nao re-enfileira este prompt — a fila ja esta vazia
                        # e o proximo run() vai chamar montar_prompt() de novo.
                        return False  # sai limpo, deixa o ciclo principal recomecar
                    if acao == "isolar_foto":
                        # Foto foi movida para fotos_bloqueadas/. Tenta novamente
                        # com a nova foto (escolher_foto ja vai ignorar bloqueada).
                        log("[DIREITOS] escalando: foto isolada, novo par foto+prompt no proximo ciclo")
                        return False
                # escalonamento ainda em avaliacao (1a ocorrencia): confirma em
                # OUTRA conta se persiste (forca troca de conta).
                sessao = None
                continue
            # Falha generica: registra e deixa a ESCADA no topo do loop decidir
            # (troca prompt apos TENTATIVAS_POR_PROMPT, troca conta apos CAP).
            # NAO poe cooldown aqui (era prematuro) nem usa 'motivo' (bug: era
            # indefinido -> NameError). O cooldown/troca de conta vem do topo.
            log(f"[sessao] {sessao['session']} falhou (tentativa {tentativas_na_conta}/{CAP_POR_CONTA} nesta conta)")
            registrar_falha_sessao(sessao["session"], "gerar_video falhou")
            _MOTIVO = (f"geracao falhou na conta {sessao['session']} ({os.environ.get('VEO_MAQUINAS') or 'pc1'}): "
                       f"timeout/imagem no lugar de video/erro — ver logs\\worker_{sessao['session']}_*.log")
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
        if foto:
            _it = dict(_it, foto=foto)  # 24/10: leva a foto aprovada junto (nao refaz no proximo ciclo)
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
        if r is not True and r != "FLAG_OFF" and _MOTIVO:  # 23/10: N horas sem video = 1 aviso a dona com o motivo
            try:
                cadeia_veo.registrar_falha(_MOTIVO)
            except Exception as _e:
                log(f"[cadeia] registro de falha nao gravou ({_e})")
        # exit code 6 = nenhuma conta com credito. O loop .bat espera MAIS
        # (15min) em vez de martelar de 30 em 30s ate a meia-noite (bug 2026-07-26).
        if r == "NO_ACCOUNTS":
            sys.exit(6)
    elif cmd == "loop":
        import time as _t
        _max_loop = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        _ok = 0; _fail = 0
        for _i in range(_max_loop):
            log(f"[loop] === ciclo {_i+1}/{_max_loop} (ok={_ok} fail={_fail}) ===")
            r = run()
            if r is not True and r != "FLAG_OFF" and _MOTIVO:
                try:
                    cadeia_veo.registrar_falha(_MOTIVO)
                except Exception:
                    pass
            if r is True:
                _ok += 1
            elif r == "NO_ACCOUNTS":
                log(f"[loop] sem contas — parando (ok={_ok} fail={_fail})")
                break
            elif r == "FLAG_OFF":
                log(f"[loop] flag cron_video OFF — parando")
                break
            else:
                _fail += 1
            if pausado_sem_notebook():
                log(f"[loop] sistema pausado — parando (ok={_ok} fail={_fail})")
                break
            _t.sleep(5)
        log(f"[loop] FIM: {_ok} videos gerados, {_fail} falhas em {_i+1} ciclos")
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
                    formula = sem_repetir(montar_prompt(canal), canal)
                    foto = escolher_foto(canal)
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
        # AT-03 (16/10): metricas vem do Studio pelo navegador (sem chave de API, proibida pelo dono)
        print("metricas: rode D:\\postador-de-videos\\bin\\metricas_rede.py (Studio pelo navegador; preenche o cache)")
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