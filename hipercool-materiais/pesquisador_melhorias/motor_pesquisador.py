r"""motor_pesquisador.py - pesquisa de melhorias AUTÔNOMA com o Sonnet 5.5 web, sem chat e sem Opus (dona 04/11/2026).

Roda pela tarefa do Windows "MotorPesquisador" (a cada 15 min, oculta). Cada chamada faz NO MÁXIMO uma pesquisa:
  python motor_pesquisador.py volta     # confere tudo e, se pode, faz 1 pesquisa
  python motor_pesquisador.py status    # placar de hoje e dos últimos 7 dias + recomendação
  python motor_pesquisador.py ligar | desligar
  python motor_pesquisador.py teto N    # muda à mão quantas por dia (o motor também ajusta sozinho)

Antes de pesquisar: motor ligado? já tem uma rodando? chegou no teto do dia? passou o intervalo? há contas do
Sonnet web prontas (D:\sonnet web\monitor_sonnet.json, tarefa MonitorSonnet)? Se faltar cota, só espera a próxima volta:
assim ele pesquisa sempre que os tokens voltam.
Durante: claude.exe -p com cw/claude-sonnet-5-5 pelo OmniRoute, só ferramentas de leitura. A resposta BRUTA é gravada
na hora (nada fica só na memória).
Depois: classifica (ok / sem_cota_no_meio / incompleta / timeout / erro), confere cada repo na API do GitHub (404 sai),
procura no NOSSO código se já usamos (arquivo:linha), grava CATALOGO_DESCOBERTAS.md e o registro. Área com falha NÃO
é marcada: volta na próxima. Nunca implanta nada.
Ajuste sozinho (1x por dia): dia anterior com falha de cota/timeout -> teto -25%; dia cheio sem falha -> teto +25%.
Painel legível por qualquer chat: PAINEL_PESQUISADOR.md (reescrito a cada volta).
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import pesquisador as q  # noqa: E402

ESTADO = BASE / "motor_estado.json"
REGISTRO = BASE / "motor_registro.jsonl"
LOG = BASE / "motor_pesquisador.log"
PAINEL = BASE / "PAINEL_PESQUISADOR.md"
CATALOGO = BASE / "CATALOGO_DESCOBERTAS.md"
MONITOR_SONNET = Path(r"D:\sonnet web\monitor_sonnet.json")
REPROVADOS = BASE / "reprovados.json"  # dona 04/11: o que os chats reprovam vira aprendizado do motor
IMPLANTADOS = BASE / "implantados.json"  # dona 04/11: o que os chats implantaram (onde) -> não pesquisar de novo
CHATS = BASE / "chats_linhas.json"      # linha -> nome do chat aberto (ListAgents); o cobrador manda para ele
ENTREGAS = BASE / "ENTREGAS"            # dona 04/11: todo achado chega ao chat da linha (caixa de entrada por linha)
# área -> linha(s) dona(s). 1ª regra que casar com "id nome" da área vale; sem regra = CURTOS + LONGOS.
ROTAS = [  # a ORDEM importa (04/11: "animar imagem/painel" caía em CAPAS por causa de "imagem")
    # 07/11 chat dos LONGOS: o longo é RECAP 16:9 de 1-3 h com voz RVC no Kaggle; efeitos/transições/áudio do longo
    # estão CONGELADOS pela dona (04/11). Por isso efeito, transição, mixagem, reenquadramento, imagem e vídeo IA
    # NUNCA vão para LONGOS — mesmo com "longo"/"longform" no nome.
    (r"geracao_video|video_ia|veo|comfy|hunyuan|minimax|wan2|ltx|first_last|animacao_paineis|painel|mascote|avatar|"
     r"live2d|lip", ["VEO_HIPERCOOL"]),
    (r"capa|miniatura|thumb|geracao_imagem|imagem|lora|upscale_rosto|rosto_upscale", ["CAPAS"]),
    # 08/11 chat dos LONGOS: LONGOS recebe SÓ fontes de recap 1-3 h, política do YouTube e distribuição/impressões
    # de vídeo longo (antes da regra dos curtos, para a "ponte Short->longo" ir para os longos).
    # Voz, roteiro, título, avatar, facecam, legenda, tradução, SEO etc. vão só para CURTOS (regra padrão).
    (r"^area_longos\b|distribu|impress|playlist|serie|canal_novo|recursos_avancados|yt_|politica|sintetic|"
     r"reutiliz|spam|metadado|fonte_recap|fontes_recap|recap_fonte|recap_ingles|ponte_short_longo", ["LONGOS"]),
    (r"efeito|transic|zoom|whip|shader|light_leak|motion_blur|glitch|reverb|limiter|loud|mixag|mix_|duck|"
     r"beat|trilha|sfx|reenquadr|9_16|916|crop|legenda|corte|highlight|viral|gancho|hook|tiktok|shorts|reels",
     ["CURTOS"]),
]
LINHAS = ["CURTOS", "LONGOS", "CAPAS", "VEO_HIPERCOOL"]

MODELO = "cw/claude-sonnet-5-5"
OMNIROUTE = "http://157.173.207.22:20133"
CHAVE = "<SEGREDO_REMOVIDO>"  # mesma do sentinela_disparo.py
# 04/11: config LIMPA e separada. Com ~\.claude-vscode a pesquisa carregava o CLAUDE.md global da dona (regra "leia o
# painel"), os agentes e ferramentas como Monitor/Cron/SendMessage -> o Sonnet se distraía e estourava 25 min.
CFG_CLAUDE = Path(r"D:\tmp\motor_pesquisador\cfg_limpo")
TEMP_D = Path(r"D:\tmp\motor_pesquisador\temp")
TIMEOUT_S = 25 * 60          # Sonnet levou 7,5–13 min nas rodadas medidas; 25 min = travou
PAUSA_MIN = 2                # entre o FIM de uma pesquisa e o início da próxima (tem cota = emenda)
MIN_PRONTAS = 5              # contas do Sonnet web prontas para começar (de ~45; cada conta volta em ~5 min, não 5 h)
# teto/dia é só trava de segurança (dona 04/11: "não precisa ficar 5 h fora, só até os tokens voltarem"):
# medido no monitor: contas do plano grátis voltam em 3–10 min, não em 5 h. O OmniRoute troca de conta no 429.
# sem cota -> espera a hora de volta do MonitorSonnet; o teto só sobe quando é batido sem falha de cota
TETO_INICIAL, TETO_MAX = 48, 200
PASTAS_CODIGO = [r"D:\recapd-ambientes\producao\bin", r"D:\hipercool-videos\bin", r"D:\video-fila",
                 r"D:\hipercool-materiais\comum", r"D:\claude-code-video", r"D:\fluxia"]
EXT_CODIGO = {".py", ".ts", ".tsx", ".js", ".mjs", ".json", ".bat", ".ps1"}
EXT_DOC = {".md", ".txt"}
PULAR = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build", "caixa", "referencias", "saida",
         "out", "tmp", "cache", "modelos", "assets", "logs",
         # 04/11: vocabulário do whisper (models\), bundle do remotion e backups do painel davam falso USA/CITADO
         "models", "build_bundle", "trabalhos", "estado", "public"}
GENERICOS = {"skills", "agent", "agents", "video", "voice", "audio", "studio", "tools", "toolkit", "server", "client",
              "plugin", "plugins", "editor", "engine", "models", "model", "awesome", "python", "speech", "subtitle",
              "subtitles", "captions", "motion", "render", "remote", "concat", "yutu", "piper", "amphion",
              # palavras comuns em português/código que davam falso "USA" (04/11: prosodia -> anime_tts.py)
              "prosodia", "narrador", "legenda", "roteiro", "cortes", "vozes", "efeitos", "clipes", "studio",
              # 04/11 2ª leva de falso USA: nomes que são palavras comuns em código/efeitos
              "impact", "reframe", "sound", "woosh", "foley", "cadence", "match-cut", "see-through", "additive",
              "supervision", "blur", "glide", "seam", "vasy", "teres", "dropsync", "bandit", "essentia",
              "madmom", "unisal", "capite", "kugiri", "remocn", "lygia", "audiocraft"}
ERRO_COTA = re.compile(r"rate.?limit|usage limit|\b429\b|overloaded|quota|out of credits|limite de uso|"
                       r"credit balance|exceeded", re.I)

INSTRUCOES = """
VOCÊ RODA SOZINHO (sem pessoa olhando). Regras:
- Só LEITURA: não crie, edite nem apague arquivos; não instale nada; não rode nada que mude o sistema.
- Para pesquisar use a ferramenta Bash/PowerShell com python ou curl, por exemplo:
  python -c "import json,urllib.request,urllib.parse;q=urllib.parse.quote('tts voice cloning pushed:>2026-06-01');print([ (r['full_name'],r['stargazers_count'],r['pushed_at'][:10]) for r in json.load(urllib.request.urlopen(urllib.request.Request('https://api.github.com/search/repositories?sort=stars&per_page=15&q='+q,headers={'User-Agent':'x'})))['items']])"
  e leia READMEs com python/curl em https://raw.githubusercontent.com/<dono>/<repo>/HEAD/README.md
- Tema de POLÍTICA/REGRA de plataforma (YouTube etc.): a fonte é a página OFICIAL (support.google.com/youtube,
  blog.youtube), não o GitHub. Leia com python/curl (ex.: urllib + remover tags HTML), cite o link exato e a data, e
  separe o que está escrito na página do que é interpretação. Nesses temas, item da lista = regra/página, não repo.
- Use SÓ as ferramentas que você já tem (Read, Grep, Glob, Bash, PowerShell). NÃO procure nem carregue outras
  ferramentas (nada de WebFetch/WebSearch/ToolSearch): a internet é pelo python/curl no Bash.
  A busca do GitHub aceita ~10 consultas por minuto: espere ~7 s entre buscas.
- NUNCA rode comando em segundo plano (run_in_background) nem fique esperando comando: cada comando termina sozinho
  em menos de 60 s (use timeout=20 no urllib). Não leia painel/catálogo: a lista do que já conhecemos está acima.
  Você tem ~20 min no total: faça ~10–15 buscas e escreva a resposta.
- Só cite repositório que você abriu de verdade nesta pesquisa. Marque NAO-COMERCIAL quando a licença do código OU dos
  pesos não permitir uso comercial. Diga o que é medido e o que é estimativa.
- FILTROS OBRIGATÓRIOS (04/11: o chat das capas reprovou 7 de 13 achados por isto). Antes de citar, confira e escreva:
  1) licença dos PESOS (model card no Hugging Face), não só do código: pesos não comerciais = descartar; confira
     também os modelos que ele baixa por padrão (detector de rosto InsightFace/SCRFD, MMS, YOLO AGPL...).
     Repositório SEM LICENÇA, GPL ou AGPL = descartar (04/11: os chats reprovaram todos);
  2) roda na T4 (Turing): sem bf16, sem fp8, sem FlashAttention-2 — se exige Ampere/Ada, descartar ou dizer como contornar;
  3) para os PCs: só citar como "roda nos PCs" se couber em ~4 GB de RAM e sem GPU dedicada.
  O que falhar num filtro vai numa linha "DESCARTADOS:" no fim, com o motivo (não na lista principal).
- Para saber se já usamos algo, pode olhar (Read/Grep) as pastas: """ + ", ".join(PASTAS_CODIGO) + "\n"


def log(msg):
    linha = f"{datetime.now():%d/%m %H:%M:%S} {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def estado():
    e = q._ler_json(str(ESTADO), {})
    e.setdefault("ligado", True)
    e.setdefault("teto_dia", TETO_INICIAL)
    e.setdefault("ajustado_em", str(date.today()))
    return e


def salvar_estado(e):
    q._gravar_json(str(ESTADO), e)


def registros(dias=7):
    out = []
    if REGISTRO.exists():
        corte = str(date.today() - timedelta(days=dias))
        for l in REGISTRO.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if r.get("dia", "") >= corte:
                out.append(r)
    return out


def registrar(r):
    r.setdefault("dia", str(date.today()))
    with open(REGISTRO, "a", encoding="utf-8") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")


def cota_sonnet():
    """(prontas, total, visto) do MonitorSonnet; None se o arquivo não existe."""
    d = q._ler_json(str(MONITOR_SONNET), {}).get("ultimo")
    if not d:
        return None
    return d.get("prontas", 0), d.get("total", 0), d.get("visto", "")


def carga_pc():
    """Motivo para NÃO pesquisar agora (CPU média >= 90% em 3 amostras ou disco C: < 1 GB); None se está tudo bem."""
    import shutil
    try:
        # 10/11: era 2 GB e parou o motor 10 h; os temporários dele agora vão para o D: (TEMP_D)
        if shutil.disk_usage("C:\\").free < 1024 ** 3:
            return "disco C: com menos de 1 GB"
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "(Get-Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 2 -MaxSamples 3)"
                            ".CounterSamples | Measure-Object CookedValue -Average | ForEach-Object { [int]$_.Average }"],
                           capture_output=True, timeout=40, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        cpu = int((r.stdout or b"0").decode("cp850", "ignore").strip().splitlines()[-1])
        return f"CPU {cpu}%" if cpu >= 90 else None
    except Exception:  # noqa: BLE001 — medir falhou não impede a pesquisa
        return None


def hora_volta():
    """Hora local (sem fuso) em que a 1ª conta limitada do Sonnet web volta, segundo o MonitorSonnet; None se nenhuma."""
    v = q._ler_json(str(MONITOR_SONNET), {}).get("ultimo", {}).get("volta")
    if not v:
        return None
    try:
        from datetime import timezone
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone(timedelta(hours=1)))  # antigos sem fuso = hora da VPS (CET)
        return d.astimezone().replace(tzinfo=None)
    except ValueError:
        return None


def vivo(pid):
    # 05/11: com text=True e -X utf8 a resposta do tasklist com acento ("INFORMAÇÕES: Nenhuma tarefa") não decodificava,
    # stdout vinha None e TODA volta quebrava -> motor parado 6 h. Agora lê bytes e ignora o que não decodifica.
    try:
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, timeout=30,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return str(pid) in (r.stdout or b"").decode("cp850", errors="ignore")
    except Exception:  # noqa: BLE001
        return False


# ------------------------------------------------------------------ aprendizado com o que os chats reprovaram

def reprovados():
    return q._ler_json(str(REPROVADOS), [])


def reprovar(repo, motivo, quem):
    """Registra que um chat reprovou um achado: entra no aprendizado do pedido e é marcado no catálogo."""
    repo = re.sub(r"^(https?://)?(www\.)?github\.com/", "", repo.strip()).strip("/")
    lista = reprovados()
    lista = [r for r in lista if r["repo"].lower() != repo.lower()]
    lista.append({"repo": repo, "motivo": motivo.strip(), "quem": quem, "data": str(date.today())})
    q._gravar_json(str(REPROVADOS), lista)
    if repo.lower() not in {c.lower() for c in q._conhecidos()}:
        with open(q.CONHECIDOS, "a", encoding="utf-8") as f:
            f.write(f"{repo}  # REPROVADO {date.today()} {quem}\n")
    if CATALOGO.exists():
        texto = CATALOGO.read_text(encoding="utf-8")
        texto = re.sub(r"^- \[[^\]]*\] (github\.com/" + re.escape(repo) + r")\b",
                       lambda m: f"- [REPROVADO por {quem}: {motivo.strip()}] {m.group(1)}", texto, flags=re.M | re.I)
        CATALOGO.write_text(texto, encoding="utf-8")
    return repo


def implantados():
    return q._ler_json(str(IMPLANTADOS), [])


def implantar(repo, onde, quem):
    """Registra que um chat IMPLANTOU um achado (ou a ideia dele): o motor não pesquisa de novo a mesma coisa."""
    repo = re.sub(r"^(https?://)?(www\.)?github\.com/", "", repo.strip()).strip("/")
    lista = [r for r in implantados() if r["repo"].lower() != repo.lower()]
    lista.append({"repo": repo, "onde": onde.strip(), "quem": quem, "data": str(date.today())})
    q._gravar_json(str(IMPLANTADOS), lista)
    if CATALOGO.exists():
        texto = CATALOGO.read_text(encoding="utf-8")
        texto = re.sub(r"^- \[[^\]]*\] (github\.com/" + re.escape(repo) + r")\b",
                       lambda m: f"- [IMPLANTADO por {quem}: {onde.strip()}] {m.group(1)}", texto, flags=re.M | re.I)
        CATALOGO.write_text(texto, encoding="utf-8")
    return repo


def chats_linhas():
    return q._ler_json(str(CHATS), {})


def registrar_chat(linha, nome):
    linha = linha.upper()
    if linha not in LINHAS:
        raise SystemExit(f"linha inválida: {linha} (use {', '.join(LINHAS)})")
    d = chats_linhas()
    # guarda o id do histórico: se o nome for reaproveitado por outro chat, o cobrador percebe e não manda
    sid = None
    try:
        import cobrador
        sid = (cobrador.sessoes().get(nome) or {}).get("sid")
    except Exception:  # noqa: BLE001
        pass
    if not sid:
        raise SystemExit(f"não achei um chat aberto chamado {nome} (use o nome exato que o ListAgents mostra)")
    d[linha] = {"nome": nome, "sid": sid, "desde": datetime.now().isoformat(timespec="minutes")}
    q._gravar_json(str(CHATS), d)


def orientacao():
    """12/11 dona: "procura muita coisa que não usamos, aí é lixo; oriente o que ele pode pesquisar e o que não".
    orientacao.json: foco (vai na frente, na ordem), nao_pesquisar (área pulada/recusada) e texto (vai em todo pedido).
    PESQUISADOR_ORIENTACAO=0 desliga."""
    if os.environ.get("PESQUISADOR_ORIENTACAO", "1") == "0":
        return {"foco": [], "nao": None, "texto": ""}
    try:
        o = json.loads((BASE / "orientacao.json").read_text(encoding="utf-8"))
        return {"foco": [re.compile(x, re.I) for x in o.get("foco", [])],
                "nao": re.compile("|".join(o["nao_pesquisar"]), re.I) if o.get("nao_pesquisar") else None,
                "texto": o.get("texto", "")}
    except (OSError, ValueError, re.error) as e:
        log(f"orientacao.json ilegível ({e}) — motor segue sem orientação")
        return {"foco": [], "nao": None, "texto": ""}


def area_serve(o, a):
    """(serve, posição no foco). Foco ganha do 'não pesquisar' (ex.: 'legenda_traduz' x 'tts')."""
    t = f"{a.get('id', '')} {a.get('nome', '')}"
    for i, rx in enumerate(o["foco"]):
        if rx.search(t):
            return True, i
    if o["nao"] is not None and o["nao"].search(t):
        return False, 999
    return True, len(o["foco"])


def lixo_automatico(c):
    """12/11: motivo pelo qual o repo nem vai para a caixa dos chats (ou ""). Medido nos 1196 reprovados com ficha:
    94 eram sem licença/GPL, 12 arquivados, 54 parados há mais de 18 meses. Estrelas NÃO filtram (os 4 implantados
    tinham 0 a 5). PESQUISADOR_FILTRO_AUTO=0 desliga."""
    if os.environ.get("PESQUISADOR_FILTRO_AUTO", "1") == "0" or not c:
        return ""
    lic = str(c.get("licenca") or "")
    if lic in ("SEM LICENÇA", "NOASSERTION") or "GPL" in lic.upper():
        return f"licença {lic}"
    if c.get("arquivado"):
        return "arquivado"
    push = str(c.get("push") or "")
    if re.match(r"\d{4}-\d{2}", push) and push < str(date.today() - timedelta(days=548)):
        return f"parado desde {push}"
    return ""


def aprendizado_texto():
    """Bloco que vai em todo pedido: o que já foi IMPLANTADO (não pesquisar de novo) e os motivos de reprovação."""
    out = ""
    imp = implantados()
    if imp:
        out += ("\nJÁ IMPLANTADO nos nossos projetos (não traga de novo nem alternativa para a mesma função, a não ser que "
                "seja claramente melhor e diga por quê):\n" + "".join(f"- {r['repo']}: {r['onde']}\n" for r in imp[-30:]))
    lista = reprovados()
    if lista:
        grupos = {}
        for r in lista:
            grupos.setdefault(r["motivo"].lower(), []).append(r["repo"])
        linhas = sorted(grupos.items(), key=lambda g: -len(g[1]))[:25]
        out += ("\nAPRENDIZADO — os chats dos projetos AVALIARAM e REPROVARAM estes achados. Não traga de novo nem coisas "
                "do mesmo tipo (mesmo motivo):\n" + "".join(f"- {mot} (ex.: {', '.join(rs[:4])})\n" for mot, rs in linhas))
    return out


# ------------------------------------------------------------------ entrega aos chats das linhas

def linhas_da_area(texto):
    t = texto.lower()
    for rx, linhas in ROTAS:
        if re.search(rx, t):
            return linhas
    return ["CURTOS"]  # 08/11: sem regra = só CURTOS (LONGOS só recebe o que casa explicitamente)


def secoes_catalogo():
    """[(cabeçalho, chave, título, linhas_de_itens)] do CATALOGO_DESCOBERTAS.md."""
    if not CATALOGO.exists():
        return []
    out, atual = [], None
    for l in CATALOGO.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## (.+?) — (.+?) \(`([^`]+)`", l)
        if m:
            atual = [l[3:].strip(), m.group(3), m.group(2), []]
            out.append(atual)
        elif atual and l.startswith("- ["):
            atual[3].append(l)
        elif atual and l.startswith("Resposta bruta:"):
            atual.append(l)
    return out


def entregar_pendentes():
    """Põe na caixa de cada linha (ENTREGAS/<LINHA>.md) toda seção do catálogo ainda não entregue, sem os reprovados."""
    ENTREGAS.mkdir(exist_ok=True)
    e = estado()
    feitas = set(e.get("entregues", []))
    novas = 0
    for sec in secoes_catalogo():
        cab, chave, titulo, itens = sec[:4]
        if cab in feitas:
            continue
        bruta = sec[4] if len(sec) > 4 else ""
        bons = [i for i in itens if not i.startswith("- [REPROVADO")]
        for linha in linhas_da_area(f"{chave} {titulo}"):
            arq = ENTREGAS / f"{linha}.md"
            if not arq.exists():
                arq.write_text(
                    f"# Caixa de entrada do pesquisador — linha {linha}\n\n"
                    "O motor (MotorPesquisador) põe aqui TODO achado novo desta linha. O chat desta linha, ao abrir:\n"
                    "1. avalia cada bloco [ ] PENDENTE seguindo video-fila\\aprendizado\\LEIA_ANTES_DE_MELHORAR.md;\n"
                    "2. troca [ ] PENDENTE por [x] AVALIADO <data> — X aplicados, Y reprovados, Z deixados;\n"
                    "3. cada reprovado: `python D:\\hipercool-materiais\\pesquisador_melhorias\\motor_pesquisador.py "
                    "reprovar dono/repo \"motivo\" <linha>` (vira aprendizado do motor).\n"
                    "Item com [USA em ...] já existe no nosso código: só olhe se trouxer versão/ideia nova.\n",
                    encoding="utf-8")
            with open(arq, "a", encoding="utf-8") as f:
                f.write(f"\n## [ ] PENDENTE — {cab}\n{bruta}\n" + ("\n".join(bons) if bons else
                        "- (todos os itens desta pesquisa foram reprovados)") + "\n")
        feitas.add(cab)
        novas += 1
    e = estado()
    e["entregues"] = sorted(feitas)
    salvar_estado(e)
    return novas


def pendentes_por_linha():
    out = {}
    for linha in LINHAS:
        arq = ENTREGAS / f"{linha}.md"
        out[linha] = arq.read_text(encoding="utf-8").count("## [ ] PENDENTE") if arq.exists() else 0
    return out


# ------------------------------------------------------------------ escolha do tema

def proximo_tema(falhas_hoje):
    cfg = q._ler_json(q.CONFIG, None)
    hist = q._ler_json(q.HISTORICO, {})
    # 05/11 (chat dos longos): 112 de 474 áreas eram voz/TTS/RVC/iGPU (testes de voz PAUSADOS pela dona) e só 4 de
    # distribuição, que é o gargalo real. Ordem: prioridade 1 primeiro, família de voz por último, depois a mais antiga.
    voz = re.compile(r"tts|rvc|f0|pitch|voz|vozes|intel_uhd|directml|igpu|gguf|destilacao|cuda_graphs|cache_embedding|"
                     r"cache_frases|^vc_|onnx|prosod|ptbr_g2p|nao_verbais|deesser|chatterbox|kokoro|piper|xtts|"
                     r"cosyvoice|sovits|f5_|paraling|fala|sala_ir|edicao_fala|g2p|homograf|ptbr_normal")

    hoje_s = str(date.today())

    def chave_ordem(t):
        ultima, tipo, x = t
        # 06/11: prioridade 1 furava a fila SEMPRE ("sessão de visualização" saiu 4x ok, a última com 0 novos).
        # Agora só fura enquanto não foi pesquisada nos últimos 2 dias.
        prio = x.get("prioridade") == 1 and (not ultima or ultima < str(date.today() - timedelta(days=2)))
        foco = area_serve(ori, x)[1] if tipo == "area" else len(ori["foco"])
        return (0 if prio else 1, foco, 1 if tipo == "area" and voz.search(x["id"]) else 0, ultima)

    # 06/11: área com "fora_da_fila" (o chat da linha disse que não serve) nunca mais é pesquisada
    ori = orientacao()
    temas = [(hist.get(f"area:{a['id']}", ""), "area", a) for a in cfg["areas"]
             if not a.get("fora_da_fila") and area_serve(ori, a)[0]]
    temas += [(hist.get(f"projeto:{p['id']}", ""), "projeto", p) for p in cfg["projetos"]]
    temas.sort(key=chave_ordem)
    for _, tipo, t in temas:
        chave = f"{tipo}_{t['id']}"
        if falhas_hoje.get(chave, 0) >= 2:
            continue  # falhou 2x hoje: deixa para amanhã
        if tipo == "area":
            texto = q._pedido(cfg, f"área {t['nome']}", t["nome"], t["subtemas"], chave=chave)
        else:
            areas = {a["id"]: a for a in cfg["areas"]}
            subt = [f"{areas[i]['nome']}: " + "; ".join(areas[i]["subtemas"][:3]) for i in t["areas_chave"] if i in areas]
            docs = "".join(f"- {d}\n" for d in t.get("docs", []))
            extra = (f"PROJETO: {t['nome']} — pasta {t['pasta']}. Antes de pesquisar, LEIA o CLAUDE.md/README da pasta "
                     f"e estes docs:\n{docs or '- (achar na pasta)'}\n")
            texto = q._pedido(cfg, f"projeto {t['nome']}", f"o projeto {t['nome']} especificamente",
                              subt + ["gargalos e defeitos que você notar no pipeline lido"], extra, chave=chave)
        # 05/11: 3 pesquisas voltaram "sem web" em segundos — o Sonnet achou que não tinha ferramenta ("rode no harness
        # com Bash"). Agora o pedido ABRE dizendo que ele tem o Bash e deve começar buscando.
        abre = ("VOCÊ ESTÁ NO CLAUDE CODE E TEM AGORA as ferramentas Bash, Read, Grep e Glob. Não peça para rodarem por "
                "você: comece JÁ rodando a 1ª busca na API do GitHub com o Bash (exemplo no fim) e só escreva a resposta "
                "depois de pesquisar.\n\n")
        return chave, t["nome"], abre + texto + "\n" + ori["texto"] + "\n" + aprendizado_texto() + INSTRUCOES
    return None


# ------------------------------------------------------------------ rodar o Sonnet

def claude_exe():
    import glob
    return max(glob.glob(os.path.expanduser(
        r"~\.vscode\extensions\anthropic.claude-code-*-win32-x64\resources\native-binary\claude.exe")), default=None)


def rodar_sonnet(pedido, saida):
    exe = claude_exe()
    if not exe:
        return "erro", "claude.exe não achado"
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(CFG_CLAUDE), ANTHROPIC_BASE_URL=OMNIROUTE, ANTHROPIC_API_KEY=CHAVE,
               ANTHROPIC_AUTH_TOKEN=CHAVE, ANTHROPIC_MODEL=MODELO, ANTHROPIC_SMALL_FAST_MODEL=MODELO,
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
               # 06/11: timeouts vinham de comando em 2º plano ("background_tasks_changed") — agora desligado de verdade,
               # e cada comando do Bash morre em 90 s (uma busca no GitHub leva ~5 s)
               CLAUDE_CODE_DISABLE_BACKGROUND_TASKS="1", BASH_DEFAULT_TIMEOUT_MS="90000", BASH_MAX_TIMEOUT_MS="90000",
               TEMP=str(TEMP_D), TMP=str(TEMP_D))  # 10/11: temporários no D:, o C: vive perto de 1 GB
    CFG_CLAUDE.mkdir(parents=True, exist_ok=True)
    TEMP_D.mkdir(parents=True, exist_ok=True)
    # avisos do Claude (stderr) vão para .err: no mesmo arquivo eles empurravam o "WEB: SIM" para fora do início.
    # stream-json: cada passo (ferramenta, texto) é gravado na hora em .eventos.jsonl -> se morrer no meio, sabemos onde.
    with open(str(saida) + ".eventos.jsonl", "wb") as f, open(str(saida) + ".err", "wb") as ferr:
        p = subprocess.Popen([exe, "-p", "--model", MODELO, "--output-format", "stream-json", "--verbose",
                              # 04/11: SEM WebFetch/ToolSearch — o Sonnet tentava carregar a WebFetch (ferramenta
                              # "deferida") e o proxy claude-web quebrava ("stream protocol error") no 3º passo, sempre
                              "--allowedTools", "Read,Grep,Glob,Bash,PowerShell",
                              "--disallowedTools", "Edit,Write,NotebookEdit,Agent,Task,WebFetch,WebSearch,ToolSearch,"
                              "Monitor,CronCreate,CronDelete,CronList,ScheduleWakeup,SendMessage,ListAgents,Workflow,"
                              "Skill,EnterWorktree,ExitWorktree,TaskStop,ReportFindings",
                              "--settings", '{"disableAllHooks": true}', "--strict-mcp-config"],
                             env=env, cwd=r"D:\tmp\motor_pesquisador", stdin=subprocess.PIPE, stdout=f,
                             stderr=ferr, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        e = estado()
        e["em_andamento"]["pid"] = p.pid
        salvar_estado(e)
        # 06/11: o motor ficou preso 37 min (o Claude já tinha morrido): communicate() esperava o stdin/fds e o
        # p.wait() depois do taskkill não tinha limite. Agora: escreve o pedido, fecha o stdin e espera com prazo;
        # todo wait tem limite e o taskkill mata a árvore inteira.
        try:
            p.stdin.write(pedido.encode("utf-8"))
            p.stdin.close()
        except OSError:
            pass
        try:
            p.wait(timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            # 06/11: com capture_output o próprio taskkill travava (neto segurando o pipe) e o TimeoutExpired dele
            # derrubava a volta inteira sem registrar. Sem captura e protegido.
            try:
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, timeout=60,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except Exception:  # noqa: BLE001
                pass
            try:
                p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                pass
            return "timeout", extrair(saida)
    return p.returncode, extrair(saida)


def extrair(saida):
    """Lê o .eventos.jsonl: grava o texto final em <saida> e devolve dados do andamento (para o monitor)."""
    ev = Path(str(saida) + ".eventos.jsonl")
    info = {"ferramentas": 0, "passos": 0, "api_s": None, "fim": None, "erro_api": None}
    textos, final = [], None
    if ev.exists():
        for l in ev.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                d = json.loads(l)
            except ValueError:
                continue
            if d.get("type") == "assistant":
                info["passos"] += 1
                for c in d.get("message", {}).get("content", []):
                    if c.get("type") == "tool_use":
                        info["ferramentas"] += 1
                    elif c.get("type") == "text" and c.get("text"):
                        textos.append(c["text"])
            elif d.get("type") == "result":
                final = d.get("result")
                info["fim"] = d.get("subtype")
                info["api_s"] = round((d.get("duration_api_ms") or 0) / 1000)
                if d.get("is_error"):
                    info["erro_api"] = str(final)[:300]
    texto = final if final and len(final) > 200 else "\n\n".join(textos)
    Path(saida).write_text(texto or "", encoding="utf-8")
    return info


def classificar(codigo, texto):
    tem_fim = "AREAS_NOVAS:" in texto
    tem_web = bool(re.search(r"WEB:\s*SIM", texto[:400], re.I))
    if codigo == "timeout":
        # 06/11: pesquisa boa cortada pelo tempo — se o texto parcial já cita 5+ repositórios, aproveita
        return "parcial" if len(q._repos_do_texto(texto)) >= 5 else "timeout"
    if not tem_fim and re.search(r"stream protocol error|API Error: (5\d\d|Connection)|ECONNRESET|socket hang up", texto):
        return "erro_proxy"  # falha do OmniRoute/claude-web, não da cota: tenta de novo na próxima volta
    if not tem_fim and ERRO_COTA.search(texto[-3000:]):
        return "sem_cota_no_meio"
    if codigo != 0 and not tem_fim:
        return "erro"
    if not tem_fim or len(texto) < 800:
        return "incompleta"
    if not tem_web:
        return "sem_web"  # respondeu de memória: vale só como pista
    return "ok"


# ------------------------------------------------------------------ conferência no nosso código

def indice_codigo():
    arqs = []
    for raiz in PASTAS_CODIGO:
        for d, subs, fs in os.walk(raiz):
            subs[:] = [s for s in subs if s.lower() not in PULAR and not s.startswith(".")]
            for n in fs:
                ext = os.path.splitext(n)[1].lower()
                if ext in EXT_CODIGO or ext in EXT_DOC:
                    p = os.path.join(d, n)
                    try:
                        if os.path.getsize(p) < 1_500_000:
                            arqs.append(p)
                    except OSError:
                        pass
            if len(arqs) > 30000:
                break
    return arqs


def onde_usamos(repos, arqs):
    """repo -> ('USA'|'CITADO', 'arquivo:linha') ou None. Casa 'dono/repo' ou o nome do repo (>= 5 letras, não
    genérico) inteiro, também com '-' trocado por '_' ou sem separador (kokoro-onnx = kokoro_onnx = kokoroonnx)."""
    pad = {}
    for r in repos:
        dono, nome = r.lower().split("/", 1)
        termos = [re.escape(r.lower())]
        if len(nome) >= 5 and nome not in GENERICOS:
            for v in {nome, nome.replace("-", "_"), re.sub(r"[-_.]", "", nome)}:
                termos.append(r"(?<![a-z0-9])" + re.escape(v) + r"(?![a-z0-9])")
        pad[r] = re.compile("|".join(termos))
    achou = {}
    for p in arqs:
        if len(achou) == len(repos):
            break
        try:
            texto = open(p, encoding="utf-8", errors="ignore").read().lower()
        except OSError:
            continue
        cod = os.path.splitext(p)[1].lower() in EXT_CODIGO
        for r, rx in pad.items():
            if r in achou and achou[r][0] == "USA":
                continue
            m = rx.search(texto)
            if m:
                linha = texto.count("\n", 0, m.start()) + 1
                tipo = "USA" if cod else "CITADO"
                if r not in achou or tipo == "USA":
                    achou[r] = (tipo, f"{p}:{linha}")
    return achou


def pos_pesquisa(chave, titulo, arq):
    texto = Path(arq).read_text(encoding="utf-8", errors="replace")
    conhecidos = {c.lower() for c in q._conhecidos()}
    citados = q._repos_do_texto(texto)
    cache = q._ler_json(q.CACHE, {})
    existem = []
    for r in citados:
        c = cache.get(r.lower())
        if not c or c.get("ok") is None:
            c = q._api(r)
            c["data"] = str(date.today())
            if c.get("ok") is not None:
                cache[r.lower()] = c
            time.sleep(1.2)
        if c.get("ok"):
            existem.append(c.get("nome") or r)
    q._gravar_json(q.CACHE, cache)
    novos = [r for r in existem if r.lower() not in conhecidos]
    descartados = [(r, lixo_automatico(cache.get(r.lower()))) for r in novos]
    descartados = [(r, m) for r, m in descartados if m]
    if descartados:  # entram no ja_conhecidos (não voltam), mas não ocupam o catálogo nem os chats
        with open(q.CONHECIDOS, "a", encoding="utf-8") as f:
            f.write("\n".join(f"{r}  # motor {date.today()} {chave} DESCARTE AUTO: {m}" for r, m in descartados) + "\n")
        registrar({"evento": "descarte_auto", "chave": chave, "repos": [f"{r} ({m})" for r, m in descartados]})
        fora = {r for r, _ in descartados}
        novos = [r for r in novos if r not in fora]
    uso = onde_usamos(novos, indice_codigo()) if novos else {}
    # catálogo: só o que existe e é novo para o pesquisador
    linhas = [f"\n## {datetime.now():%Y-%m-%d %H:%M} — {titulo} (`{chave}`, Sonnet 5.5 web)\n",
              f"Resposta bruta: `{arq}`\n"]
    for r in novos:
        c = cache.get(r.lower(), {})
        st = uso.get(r)
        situ = f"{st[0]} em {st[1]}" if st else "INÉDITO"
        linhas.append(f"- [{situ}] github.com/{r} — ★{c.get('estrelas')}, push {c.get('push')}, {c.get('licenca')}"
                      f"{' ARQUIVADO' if c.get('arquivado') else ''} — {c.get('descricao', '')}")
    if not novos:
        linhas.append("- (nada novo: tudo já estava no ja_conhecidos)")
    if not CATALOGO.exists():
        CATALOGO.write_text("# Catálogo de descobertas do motor (só repos que EXISTEM, novos para o pesquisador)\n\n"
                            "INÉDITO = não achado no nosso código; USA = aparece em código nosso; CITADO = só em doc.\n"
                            "Quem implanta é o chat do projeto, seguindo video-fila\\aprendizado\\LEIA_ANTES_DE_MELHORAR.md.\n",
                            encoding="utf-8")
    with open(CATALOGO, "a", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    # crescer: só os que existem entram no ja_conhecidos (404 não)
    if novos:
        with open(q.CONHECIDOS, "a", encoding="utf-8") as f:
            f.write("\n".join(f"{r}  # motor {date.today()} {chave}" for r in novos) + "\n")
    antes_ids = {a["id"] for a in q._ler_json(q.CONFIG, None)["areas"]}
    q.cmd_areas_novas([arq])
    ori = orientacao()
    if ori["nao"] is not None:  # 12/11: área nova fora da orientação não entra (2547 das 2579 áreas vieram daqui)
        cfg = q._ler_json(q.CONFIG, None)
        novas = [a for a in cfg["areas"] if a["id"] not in antes_ids]
        ficam = [a for a in novas if area_serve(ori, a)[0]][:3]
        if len(ficam) != len(novas):
            ids_ficam = {a["id"] for a in ficam}
            cfg["areas"] = [a for a in cfg["areas"] if a["id"] in antes_ids or a["id"] in ids_ficam]
            q._gravar_json(q.CONFIG, cfg)
            log(f"áreas novas: {len(novas)} sugeridas, {len(ficam)} dentro da orientação")
    ha = q._ler_json(q.HIST_AREAS, {})
    h = ha.setdefault(chave, {"rodadas": [], "repos": []})
    h["rodadas"].append(f"motor_{date.today()}")
    h["repos"] += [r for r in existem if r not in h["repos"]]
    q._gravar_json(q.HIST_AREAS, ha)
    q.cmd_marcar([chave])
    return {"citados": len(citados), "existem": len(existem), "novos": len(novos),
            "ineditos": sum(1 for r in novos if r not in uso), "ja_usamos": sum(1 for r in novos if r in uso)}


# ------------------------------------------------------------------ ajuste sozinho e painel

def ajustar(e):
    hoje = str(date.today())
    if e.get("ajustado_em") == hoje:
        return
    ontem = str(date.today() - timedelta(days=1))
    rs = [r for r in registros(2) if r.get("dia") == ontem and r.get("status")]
    falhas_cota = sum(1 for r in rs if r["status"] == "sem_cota_no_meio")
    feitas = len(rs)
    antes = e["teto_dia"]
    # falta de cota NÃO baixa o teto: ela já faz o motor esperar a hora de volta. O teto só sobe se travou o dia.
    if feitas >= antes and not falhas_cota:
        e["teto_dia"] = min(TETO_MAX, int(antes * 1.25) + 1)
        motivo = f"ontem bateu o teto ({feitas}) sem falha de cota"
    else:
        motivo = f"ontem {feitas} pesquisa(s), {falhas_cota} sem cota no meio; teto mantido"
    e["ajustado_em"] = hoje
    registrar({"evento": "ajuste_teto", "de": antes, "para": e["teto_dia"], "motivo": motivo})
    log(f"teto {antes} -> {e['teto_dia']} ({motivo})")


def resumo_texto():
    e = estado()
    rs = [r for r in registros(7) if r.get("status")]
    hoje = str(date.today())
    cota = cota_sonnet()
    out = [f"# Painel do Pesquisador automático (Sonnet 5.5 web) — {datetime.now():%d/%m %H:%M}\n",
           "Gerado por `motor_pesquisador.py` a cada volta (tarefa MotorPesquisador, 5 em 5 min). Não editar à mão.\n",
           f"- Motor: **{'LIGADO' if e['ligado'] else 'DESLIGADO'}** | teto hoje: **{e['teto_dia']}** pesquisas"
           f" | contas Sonnet web prontas agora: **{cota[0]}/{cota[1]}** (MonitorSonnet {cota[2]})" if cota else
           f"- Motor: {'LIGADO' if e['ligado'] else 'DESLIGADO'} | teto {e['teto_dia']} | MonitorSonnet sem dados",
           f"- Rodando agora: {e['em_andamento']['tema']} desde {e['em_andamento']['inicio']}" if e.get("em_andamento")
           else "- Rodando agora: nada",
           f"- Próxima pesquisa: **às {e['esperar_ate'][11:16]}** (sem cota; hora de volta das contas pelo MonitorSonnet)"
           if e.get("esperar_ate") else "- Próxima pesquisa: assim que a atual terminar (+2 min), enquanto houver cota",
           "- Caixas das linhas (blocos PENDENTES de avaliação): "
           + " | ".join(f"**{k}** {v}" for k, v in pendentes_por_linha().items()) + " — pasta `ENTREGAS\\`",
           "- Chats das linhas (o CobradorPesquisador manda os pendentes de hora em hora): "
           + (" | ".join(f"{k}: {v['nome']}" for k, v in chats_linhas().items()) or "nenhum registrado"),
           "- Cobrança por linha: " + (" | ".join(
               f"**{k}** {v.get('situacao', '?')}" for k, v in q._ler_json(str(BASE / "cobrador_estado.json"), {}).items())
               or "ainda não rodou"),
           f"- Implantados pelos chats: **{len(implantados())}** — `implantados.json`",
           f"- Reprovados pelos chats (viram aprendizado do pedido): **{len(reprovados())}** — `reprovados.json`; "
           "para registrar: `python motor_pesquisador.py reprovar dono/repo \"motivo\" chat`", "",
           "| dia | pesquisas | ok | sem cota no meio | timeout | incompleta/erro | min médios | repos novos | inéditos |",
           "|---|---|---|---|---|---|---|---|---|"]
    for i in range(6, -1, -1):
        d = str(date.today() - timedelta(days=i))
        rd = [r for r in rs if r["dia"] == d]
        if not rd:
            continue
        ok = [r for r in rd if r["status"] == "ok"]
        cont = lambda *s: sum(1 for r in rd if r["status"] in s)  # noqa: E731
        med = round(sum(r.get("duracao_s", 0) for r in rd) / len(rd) / 60, 1)
        out.append(f"| {d} | {len(rd)} | {len(ok)} | {cont('sem_cota_no_meio')} | {cont('timeout')} | "
                   f"{cont('incompleta', 'erro', 'erro_proxy', 'sem_web', 'interrompida', 'esgotado')} | {med} | "
                   f"{sum(r.get('novos', 0) for r in ok)} | {sum(r.get('ineditos', 0) for r in ok)} |")
    hj = [r for r in rs if r["dia"] == hoje]
    sem_cota = [r for r in hj if r["status"] == "sem_cota_no_meio"]
    tempo = [r for r in hj if r["status"] == "timeout"]
    if sem_cota:
        rec = f"COTA: {len(sem_cota)} pesquisa(s) hoje acabaram sem cota no meio — o motor espera a hora de volta das contas."
    elif tempo:
        rec = (f"TEMPO: {len(tempo)} pesquisa(s) passaram de 25 min (não é cota). Ver o .eventos.jsonl delas: em geral "
               "o Sonnet ficou esperando comando em segundo plano.")
    elif hj and len(hj) >= e["teto_dia"]:
        rec = "AUMENTAR: bateu o teto sem falha — o motor sobe o teto amanhã."
    else:
        rec = "MANTER: abaixo do teto e sem falha de cota."
    out += ["", f"**Recomendação:** {rec}", "",
            "Últimas pesquisas:"]
    for r in rs[-8:][::-1]:
        out.append(f"- {r.get('inicio', '')} {r.get('tema', '')}: **{r['status']}** em {round(r.get('duracao_s', 0) / 60, 1)} min"
                   f", {r.get('novos', 0)} novos ({r.get('ineditos', 0)} inéditos)"
                   f"{' — ' + r['obs'] if r.get('obs') else ''}")
    out += ["", "Achados: `CATALOGO_DESCOBERTAS.md` | registro: `motor_registro.jsonl` | log: `motor_pesquisador.log`"]
    return "\n".join(out) + "\n"


def painel():
    PAINEL.write_text(resumo_texto(), encoding="utf-8")


# ------------------------------------------------------------------ volta

def volta(agora=False):
    e = estado()
    ajustar(e)
    salvar_estado(e)
    try:
        if not e["ligado"]:
            return
        if e.get("em_andamento"):
            em = e["em_andamento"]
            ini = datetime.fromisoformat(em["inicio"])
            if em.get("pid") and vivo(em["pid"]) and datetime.now() - ini < timedelta(seconds=TIMEOUT_S + 300):
                return  # ainda pesquisando
            registrar({"inicio": em["inicio"], "tema": em["tema"], "status": "interrompida",
                       "duracao_s": int((datetime.now() - ini).total_seconds()),
                       "obs": "processo sumiu (PC desligou/reiniciou ou foi morto); tema volta na fila"})
            e["em_andamento"] = None
            salvar_estado(e)
        hoje = [r for r in registros(1) if r.get("dia") == str(date.today()) and r.get("status")]
        # 06/11: 53 erros 500 do OmniRoute de madrugada gastaram o teto todo. Falha de proxy não conta no teto.
        if len([r for r in hoje if r["status"] not in ("erro_proxy", "interrompida")]) >= e["teto_dia"]:
            return
        # recuo: 3+ falhas de proxy seguidas -> espera 15, 30, 60 min (não martelar o OmniRoute caído)
        seguidas = 0
        for r in reversed(hoje):
            if r["status"] != "erro_proxy":
                break
            seguidas += 1
        if seguidas >= 3 and not agora:
            espera = min(60, 15 * 2 ** (seguidas // 3 - 1))
            ult_fim = datetime.fromisoformat(hoje[-1]["inicio"]) + timedelta(seconds=hoje[-1].get("duracao_s", 0))
            if datetime.now() - ult_fim < timedelta(minutes=espera):
                return
        agora_dt = datetime.now()
        # cota acabou antes: só volta na hora que o MonitorSonnet disse (sem esperar 5 h à toa nem tentar antes)
        if e.get("esperar_ate") and not agora:
            if agora_dt < datetime.fromisoformat(e["esperar_ate"]):
                return
            e["esperar_ate"] = None
            salvar_estado(e)
        if hoje and not agora:
            fim = max(datetime.fromisoformat(r["inicio"]) + timedelta(seconds=r.get("duracao_s", 0)) for r in hoje)
            if agora_dt - fim < timedelta(minutes=PAUSA_MIN):
                return
        # 06/11: com o PC1 a 100% de CPU o Bash do Claude não rodava nem um curl (4 timeouts, "sem_web" após 11 min).
        # PC sufocado = espera 15 min em vez de gastar a pesquisa.
        carga = carga_pc()
        if carga and not agora:
            e["esperar_ate"] = (agora_dt + timedelta(minutes=15)).isoformat(timespec="minutes")
            salvar_estado(e)
            log(f"PC sobrecarregado ({carga}); próxima tentativa às {e['esperar_ate'][11:16]}")
            return
        cota = cota_sonnet()
        # pico do claude.ai (seg–sex 10h–16h de Brasília): gasta mais rápido, mas como cada conta volta em ~5 min
        # (medido no monitor_sonnet.log: 3–10 min, não 5 h), só exigimos +50% em vez de 2x
        pico = agora_dt.weekday() < 5 and 10 <= agora_dt.hour < 16
        minimo = int(MIN_PRONTAS * (1.5 if pico else 1))
        if cota and cota[0] < minimo:
            volta_em = hora_volta() or (agora_dt + timedelta(minutes=15))
            e["esperar_ate"] = max(volta_em, agora_dt + timedelta(minutes=5)).isoformat(timespec="minutes")
            salvar_estado(e)
            log(f"sem cota: {cota[0]}/{cota[1]} contas prontas (mín. {minimo}{' no pico' if pico else ''}); "
                f"próxima pesquisa às {e['esperar_ate'][11:16]} (volta das contas pelo MonitorSonnet)")
            return
        falhas = {}
        for r in hoje:
            # só falhas das últimas 3 h travam o tema (04/11: falhas de manhã, já consertadas, prendiam o roteiro o dia todo)
            if r["status"] != "ok" and agora_dt - datetime.fromisoformat(r["inicio"]) < timedelta(hours=3):
                falhas[r["tema"]] = falhas.get(r["tema"], 0) + 1
        tema = proximo_tema(falhas)
        if not tema:
            log("nenhum tema disponível")
            return
        chave, titulo, pedido = tema
        pasta = BASE / "rodadas" / f"motor_{date.today()}" / "respostas"
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta.parent / "pedidos").mkdir(exist_ok=True)
        (pasta.parent / "pedidos" / f"{chave}.md").write_text(pedido, encoding="utf-8")
        arq = pasta / f"{chave}__sonnet_{datetime.now():%H%M}.md"
        inicio = datetime.now()
        e["em_andamento"] = {"tema": chave, "inicio": inicio.isoformat(timespec="seconds"), "arquivo": str(arq)}
        salvar_estado(e)
        log(f"começando {chave} ({titulo}); contas prontas {cota[0] if cota else '?'}")
        painel()
        for tentativa in range(1, 4):
            t0 = datetime.now()
            codigo, info = rodar_sonnet(pedido, arq)
            texto = arq.read_text(encoding="utf-8", errors="replace") if arq.exists() else ""
            err = Path(str(arq) + ".err")
            avisos = err.read_text(encoding="utf-8", errors="replace") if err.exists() else ""
            extra = (info.get("erro_api") or "") + "\n" + avisos[-2000:]
            status = classificar(codigo, texto + ("\n" + extra if info.get("erro_api") or codigo != 0 else ""))
            # erro do proxy logo no começo: é intermitente (04/11 testado), tenta de novo na mesma volta
            if status == "erro_proxy" and (datetime.now() - t0).total_seconds() < 90 and tentativa < 3:
                log(f"{chave}: erro do proxy na tentativa {tentativa}, de novo em 30 s")
                time.sleep(30)
                continue
            break
        if status == "ok":
            err.unlink(missing_ok=True)
        dur = int((datetime.now() - inicio).total_seconds())
        reg = {"inicio": inicio.isoformat(timespec="seconds"), "tema": chave, "status": status, "duracao_s": dur,
               "tentativas": tentativa, "ferramentas": info.get("ferramentas"), "passos": info.get("passos"),
               "api_s": info.get("api_s"), "codigo": str(codigo), "bytes": len(texto),
               "contas_prontas_antes": cota[0] if cota else None, "arquivo": str(arq)}
        # 08/11: "sem_web" depois de pesquisar de verdade (5+ ferramentas) = tema ESGOTADO (nada passou nos filtros),
        # não falha. Marca como pesquisado para não repetir na volta seguinte.
        if status == "sem_web" and (info.get("ferramentas") or 0) >= 5:
            status = "esgotado"
            reg["status"] = status
            q.cmd_marcar([chave])
        if status in ("ok", "parcial"):
            reg.update(pos_pesquisa(chave, titulo, str(arq)))
        else:
            reg["obs"] = (f"parou no passo {info.get('passos')} ({info.get('ferramentas')} ferramentas). "
                          + re.sub(r"\s+", " ", (texto[-200:] + " " + (info.get("erro_api") or ""))).strip())
            arq.rename(arq.with_name(arq.stem + "_FALHA.md"))
        depois = cota_sonnet()
        reg["contas_prontas_depois"] = depois[0] if depois else None
        e = estado()
        e["em_andamento"] = None
        if status == "sem_cota_no_meio":
            volta_em = hora_volta() or (datetime.now() + timedelta(minutes=30))
            e["esperar_ate"] = max(volta_em, datetime.now() + timedelta(minutes=5)).isoformat(timespec="minutes")
            reg["obs"] = (reg.get("obs") or "") + f" | próxima às {e['esperar_ate'][11:16]} (volta da cota)"
        salvar_estado(e)
        registrar(reg)
        log(f"{chave}: {status} em {dur // 60} min {dur % 60} s"
            + (f", {reg.get('novos')} novos ({reg.get('ineditos')} inéditos)" if status in ("ok", "parcial") else ""))
    finally:
        try:
            n = entregar_pendentes()
            if n:
                log(f"entregue(s) {n} pesquisa(s) nas caixas das linhas (ENTREGAS\\)")
        except Exception as ex:  # noqa: BLE001 — entrega nunca derruba a pesquisa
            log(f"entrega falhou: {ex}")
        painel()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "volta":
        volta(agora="--agora" in sys.argv)
    elif cmd in ("ligar", "desligar"):
        e = estado()
        e["ligado"] = cmd == "ligar"
        salvar_estado(e)
        painel()
        print(f"motor {'LIGADO' if e['ligado'] else 'DESLIGADO'}")
    elif cmd == "implantado" and len(sys.argv) > 3:
        # python motor_pesquisador.py implantado dono/repo "arquivo/função + chave que desliga" [chat]
        repo = implantar(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "chat")
        painel()
        print(f"implantado: {repo} — o motor não pesquisa de novo a mesma coisa; marcado no catálogo")
    elif cmd == "sou" and len(sys.argv) > 3:
        # python motor_pesquisador.py sou CURTOS claude-dc   (o nome que o ListAgents mostra para este chat)
        registrar_chat(sys.argv[2], sys.argv[3])
        painel()
        print(f"{sys.argv[3]} registrado como chat da linha {sys.argv[2].upper()}: o cobrador manda os achados para ele")
    elif cmd == "entregar":
        print(f"{entregar_pendentes()} pesquisa(s) entregue(s); pendentes por linha: {pendentes_por_linha()}")
        painel()
    elif cmd == "reprovar" and len(sys.argv) > 3:
        # python motor_pesquisador.py reprovar dono/repo "motivo" [chat]
        repo = reprovar(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "chat")
        painel()
        print(f"reprovado: {repo} — entra no aprendizado das próximas pesquisas e foi marcado no catálogo")
    elif cmd == "teto" and len(sys.argv) > 2:
        e = estado()
        e["teto_dia"] = max(1, int(sys.argv[2]))
        salvar_estado(e)
        painel()
        print(f"teto = {e['teto_dia']}/dia")
    else:
        print(resumo_texto())


if __name__ == "__main__":
    main()
