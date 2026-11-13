r"""salvar_github.py — cópia SÓ DO CÓDIGO de todos os projetos num repositório do GitHub (13/11, dona: "se é só
isso de MB então põe tudo lá, porque outro agente que só trabalha online vai mexer nele pra melhorar; cria um projeto
e salva").

O que vai: .py .ps1 .bat .sh .vbs .js .ts .tsx .mjs .md .txt .json .yaml .yml .toml .html .css .ipynb (< 2 MB),
espelhando D:\<projeto>\... em <repo>\<projeto>\...
O que NUNCA vai: venv, node_modules, modelos, vídeos/imagens/áudio, workspace, caches, logs, perfis do Chrome, cofre,
secrets, credenciais, tokens, cookies, contas, estado; arquivos com nome de segredo; backups .bak/.bkp.
Segredo DENTRO de arquivo de código (chave de API, token, senha, proxy com senha, cookie): trocado por
"<SEGREDO_REMOVIDO>" na cópia (o original no D: não muda). Depois de montar, uma VARREDURA final recusa o envio se
sobrou qualquer coisa com cara de chave.

Repositório: Emersonjosielmrx/sistema-videos. Pasta de trabalho: D:\github_sistema (fora dos projetos).
Tarefa diária SalvarGithub manda só o que mudou. SALVAR_GITHUB=0 desliga.

GITHUB_PUBLICO=1 (padrão) cria o repositório público; GITHUB_PUBLICO=0, privado. Senha/chave/cookie saem sempre.
GITHUB_LIMPEZA_EXTRA=1 (desligado por padrão) tira também e-mails, IPs, telefones e ids de canal/credencial, e deixa
de fora as listas de contas/perfis e os registros de execução.

    python salvar_github.py --montar      # só monta a cópia e varre (não envia)
    python salvar_github.py               # monta, varre e envia
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

GH = r"D:\tools\gh\gh.exe"
REPO = "Emersonjosielmrx/sistema-videos"  # 13/11: a conta logada (fabricadeautomacoesia não deu permissão)
DESTINO = Path(r"D:\github_sistema")
LOG = Path(r"D:\tmp\salvar_github.log")
PROJETOS = ["recapd-ambientes", "video-fila", "postador-de-videos", "hipercool-materiais", "manhwa-react", "veo",
            "flow-imagens", "logins-google", "claude-code-video", "fluxia", "projeto-navegador-sem-navegador",
            "ms-energy", "hipercool-videos", "historias-em-frames",
            # 13/11 dona ("enviou mesmo TODOS os projetos de vídeo, painel e tudo?"): os que tinham ficado de fora
            "claude-code-video-adicional", "clone-real", "hipercool-motionframes", "hipercool-producao",
            "videos-comentarios", "projeto-joao-lucas-virjao", "recap-longos-prontos", "recap_central_casa",
            "painel-clientes", "landings-produtos", "licibot_ia", "olx-buscas", "roteador-heygen-api", "hermes",
            "claude-comunicacao", "cline-ponte", "gemini-argo", "vps157", "whatsapp-activator2", "projetos-navegador",
            "sentinela"]
# arquivos soltos na raiz do D: (sentinela, monitores, vigia) — vão em "raiz_D/"
RECADOS_RAIZ = ["RECADOS_ENTRE_AGENTES.md", "MELHORIAS_AGENTE_ONLINE.md"]  # 13/11: ver montar()
RAIZ_SOLTOS = ["sentinela_credito.py", "sentinela_disparo.py", "sentinela_vigia.py", "monitor_opus.py",
               "monitor_opus_telegram.py", "checar_opus_telegram.py", "checar_limites_antigravity.py", "rodar_oculto.vbs",
               "ACESSO_VPS_PARA_AGENTES.md", "relatorio_final.md"]
EXT = {".py", ".ps1", ".bat", ".sh", ".vbs", ".js", ".ts", ".tsx", ".mjs", ".md", ".txt", ".json", ".yaml", ".yml",
       ".toml", ".html", ".css", ".ipynb"}
PASTAS_FORA = {"venv", ".venv", "venv_vozes", "node_modules", "__pycache__", ".git", "models", "modelos", "workspace",
               "cache", "caches", "perfis", "perfil", "perfil_navegador", "perfil_chrome", "secrets", "secret",
               "credenciais", "logs", "log", "tmp", "temp", "dados", "videos", "video", "assets", "saida", "out",
               "dist", "build", "shorts", "animes recap", "na_nuvem", "cofre", "juri", "rodadas", "videos laterais",
               "python", "estado", "tokens", "cookies", "sessoes", "sessions", "amostras_voz", "tts_cache", "uv_cache",
               "veo", "limpos", "imagens", "images", "fotos", "trilhas", "overlays", "fonts", "capas", "prints",
               "screenshots", "yt_web", "tiktok_tela", "caixa", "referencias", "trabalhos", "public", "build_bundle",
               "capas_longos_refeitas", "capas_longos_google", "panels", "anime", "fila", "entrada", "usados",
               "kernel_tmp", "kcfg", "reprovadas", "_tmp", "backups", "backup"}
# perfis do Chrome com outro nome (chrome-profiles, chrome_gen_conta5, chrome_profile_3, "User Data"...): em 13/11
# subiram ~1900 arquivos de perfil porque só o nome exato "perfil_chrome" estava na lista
PASTA_PERFIL = re.compile(r"^chrome[-_ ]?(?:profiles?|gen|perfil|perfis|user)|^user data$|^profile \d+$", re.I)
MARCA_PERFIL = {"Local State", "First Run", "Last Version"}  # arquivos que só existem na raiz de um perfil do Chrome
NOME_SEGREDO = re.compile(r"secret|senha|password|token|cookie|credenc|client_oauth|client_secret|\.env$|contas\.json|"
                          r"rclone\.conf|proxies|youtube_canais|instagram_contas|kaggle\.json|apikey|api_key|chave|"
                          r"\.pem$|\.key$|sessao|session|cofre|pool\.json|ledger|_estado\.json|historico", re.I)
# só com GITHUB_LIMPEZA_EXTRA=1: listas de contas/chaves/perfis e registros de execução (têm e-mail de conta, o mapa
# conta -> máquina/perfil e o resultado de cada tentativa) não são código e não vão
NOME_SO_PRIVADO = re.compile(r"(?:contas?|keys?|perfis|providers)\w*\.(?:json|md|txt)$|"
                             r"(?:^|[_-])(?:log|saida|erros?)(?:[_-][\w-]*)?\.txt$|^ACESSO_VPS", re.I)
TAMANHO_MAX = 2_000_000
# conteúdo: o que tem cara de segredo vira <SEGREDO_REMOVIDO>
PADROES = [
    (re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"), "<SEGREDO_REMOVIDO>"),
    # 13/11: sem \b — a chave vinha colada depois de "%3A" (cabeçalho capturado em URL: Api-Key%3AAIza...) e passava
    (re.compile(r"AIza[0-9A-Za-z_-]{30,}"), "<SEGREDO_REMOVIDO>"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "<SEGREDO_REMOVIDO>"),
    (re.compile(r"\bya29\.[0-9A-Za-z_-]{20,}"), "<SEGREDO_REMOVIDO>"),
    (re.compile(r"\b1//0[0-9A-Za-z_-]{20,}"), "<SEGREDO_REMOVIDO>"),
    (re.compile(r"\bGOCSPX-[0-9A-Za-z_-]{10,}"), "<SEGREDO_REMOVIDO>"),
    (re.compile(r"\bxox[abp]-[0-9A-Za-z-]{10,}"), "<SEGREDO_REMOVIDO>"),
    # bot do Telegram. Sem \b: na URL vem colado ("/bot123456:AA...") e o \b não casava -> o token passou em 13/11
    (re.compile(r"(?<!\d)\d{8,10}:AA[0-9A-Za-z_-]{30,}"), "<SEGREDO_REMOVIDO>"),
    # cookie de sessão do Google (valor de SID/__Secure-1PSID) e o cabeçalho SAPISIDHASH capturado
    (re.compile(r"\bg\.a000[0-9A-Za-z_-]{20,}"), "<SEGREDO_REMOVIDO>"),
    (re.compile(r"(SAPISID\w*HASH(?:%20|\s+))\d+_[0-9a-f]{40}"), r"\1<SEGREDO_REMOVIDO>"),
    # 13/11 (chat do D:): linha de cookies.txt (formato Netscape, separado por TAB: domínio, flag, caminho, seguro,
    # validade, NOME, VALOR) colada num .md — a regra acima tirava só o __Secure-1PSID e deixava PSIDTS, SIDCC,
    # PAPISID, SAPISID, HSID, SSID, LOGIN_INFO do mesmo bloco (video-fila\REVISAO_MELHORIAS.md). Todo valor com 12+
    # caracteres numa linha desse formato sai, seja qual for o nome do cookie. Validade 0 (PREF, SOCS: preferência
    # de idioma, não é login) fica.
    (re.compile(r"(?m)^([+ \-]?\.?[\w.-]+\.[a-z]{2,}\t(?:TRUE|FALSE)\t/[^\t\n]*\t(?:TRUE|FALSE)\t[1-9]\d*\t[^\t\n]+\t)"
                r"[^\s<][^\s]{11,}"), r"\1<SEGREDO_REMOVIDO>"),
    # cookie colado em texto: SID=...; sessionid=...  (não mexe em sessionid={variavel} / %s / $VAR)
    (re.compile(r"((?:__Secure-[13]P(?:SID|APISID|SIDTS|SIDCC)|\b(?:SID|HSID|SSID|APISID|SAPISID|sessionid|sid_tt|"
                r"sid_guard|auth_token))=)(?![{$<%\"'])[^;\s\"'&)]{16,}"), r"\1<SEGREDO_REMOVIDO>"),
    (re.compile(r"\bgsk_[0-9A-Za-z]{20,}"), "<SEGREDO_REMOVIDO>"),
    # 13/11: o GitHub barrou o envio por uma chave do Asaas ($aact_...) num fluxo do n8n
    (re.compile(r"\$?aact_[A-Za-z0-9_$:=+/-]{20,}"), "<SEGREDO_REMOVIDO>"),
    (re.compile(r"\b(?:sk|pk|rk)_(?:live|test)_[0-9A-Za-z]{16,}"), "<SEGREDO_REMOVIDO>"),  # Stripe
    (re.compile(r"\bAPP_USR-[0-9A-Za-z-]{20,}"), "<SEGREDO_REMOVIDO>"),  # Mercado Pago
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<SEGREDO_REMOVIDO>"),  # AWS
    (re.compile(r"\bSG\.[0-9A-Za-z_-]{20,}\.[0-9A-Za-z_-]{20,}"), "<SEGREDO_REMOVIDO>"),  # SendGrid
    (re.compile(r"\bEAA[A-Za-z0-9]{40,}"), "<SEGREDO_REMOVIDO>"),  # Facebook/Instagram Graph
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----"), "<SEGREDO_REMOVIDO>"),
    (re.compile(r"\bhf_[0-9A-Za-z]{20,}"), "<SEGREDO_REMOVIDO>"),
    (re.compile(r"\beyJ[0-9A-Za-z_-]{20,}\.[0-9A-Za-z_-]{20,}\.[0-9A-Za-z_-]{10,}"), "<SEGREDO_REMOVIDO>"),  # JWT
    (re.compile(r"(https?://)[^:/\s\"']+:[^@/\s\"']+@"), r"\1<USUARIO>:<SEGREDO_REMOVIDO>@"),  # proxy com senha
    # 13/11 (chat do D:): proxy escrito SEM "http://" — "usuario:senha@IP:porta" ou "usuario:senha@host:porta"
    # (veo\beta\_test_proxy.py levava a senha do Webshare pago, a mesma das contas do Kaggle). Só quando depois do @
    # vem IP ou host COM porta: "nome:texto@" de e-mail/markdown não tem ":porta" e fica.
    (re.compile(r"(?<![\w/@.:-])([A-Za-z][\w.-]{2,}):([^@\s\"'<>/:]{6,})@"
                r"((?:\d{1,3}\.){3}\d{1,3}|[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+):(\d{2,5})\b"),
     r"<USUARIO>:<SEGREDO_REMOVIDO>@\3:\4"),
    (re.compile(r"((?:senha|password|passwd|pwd|token|api_?key|apikey|secret|chave|CHAVE|SENHA|TOKEN|SECRET|"
                r"API_KEY)\w*\s*[=:]\s*[\"'])(?![)\],+.;])[^\"'\s]{6,}([\"'])", re.I), r"\1<SEGREDO_REMOVIDO>\2"),
    (re.compile(r"(\"(?:senha|password|token|api_key|apikey|secret|chave|access_token|refresh_token|client_secret|"
                r"sessionid|sapisid|cookie)\w*\"\s*:\s*\")[^\"]{6,}(\")", re.I), r"\1<SEGREDO_REMOVIDO>\2"),
]
PUBLICO = os.environ.get("GITHUB_PUBLICO", "1") != "0"
# 13/11 dona: "não precisa limpar, só põe logo agora mesmo" — e-mails/IPs ficam; senhas e chaves saem SEMPRE.
LIMPEZA_EXTRA = os.environ.get("GITHUB_LIMPEZA_EXTRA", "0") == "1"
# 13/11 dona: "faz público" — num repositório PÚBLICO também saem e-mails, IPs (Tailscale/VPS), números de telefone e
# os ids de credencial de canal; senão quem achar o código liga as contas entre si (risco de banimento em massa).
PADROES_PUBLICO = [
    # (?<!\\): não começar na letra de um "\n"/"\t" escrito por extenso (JSON) — comia o "n" e deixava "\<EMAIL>" inválido
    (re.compile(r"(?<!\\)[A-Za-z0-9._%+-]+@(?:gmail|hotmail|outlook|yahoo|icloud|proton)\.[A-Za-z.]{2,}", re.I), "<EMAIL>"),
    # (?!git@): não estragar endereço de clone "git@github.com:..."
    (re.compile(r"(?<!\\)\b(?!git@)[A-Za-z0-9._%+-]{3,}@[A-Za-z0-9-]+\.(?:com|com\.br|net|org|io|ia|ai)\b", re.I), "<EMAIL>"),
    (re.compile(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b"), "<IP_TAILSCALE>"),
    (re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"), "<IP>"),
    # qualquer IP público (antes só 157.173/209.x: a VPS de produção e o IP de casa passavam) — ver _troca_ip
    (re.compile(r"(?<![\w.-])(?:\d{1,3}\.){3}\d{1,3}(?![\w.]|-\d)"), None),
    # (?<![\d.]) e (?!\d): sem isso comia pedaço de número comprido (id, epoch em ms) e deixava JSON/Python inválido
    (re.compile(r"(?<![\d.\w])\+?55\s?\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}(?!\d)"), "<TELEFONE>"),
    (re.compile(r"(?<![\d.\w])\(\d{2}\)\s?9?\d{4}[-\s]?\d{4}(?!\d)"), "<TELEFONE>"),  # (91) 99999-9999
    (re.compile(r"\brnprmtfo-\d+\b"), "<PROXY>"),
    # ids de credencial (16 letras/números). Exige minúscula + maiúscula + dígito: sem isso trocava qualquer palavra
    # de 16 letras entre aspas ("backgroundColors") e estragava o código
    (re.compile(r"\b(?=[A-Za-z0-9]{16}[\"'])(?=[A-Za-z0-9]*\d)(?=[A-Za-z0-9]*[a-z])(?=[A-Za-z0-9]*[A-Z])"
                r"[A-Za-z0-9]{16}(?=[\"'])"), "<CRED_ID>"),
    (re.compile(r"\bUC[A-Za-z0-9_-]{22}\b"), "<CANAL_ID>"),
]
IP_LIVRE = re.compile(r"^(?:127\.|10\.|0\.|255\.|169\.254\.|172\.(?:1[6-9]|2\d|3[01])\.|1\.1\.1\.1$|1\.0\.0\.1$|8\.8\.[48]\.[48]$)")
SOBROU_PUBLICO = re.compile(r"[A-Za-z0-9._%+-]+@(?:gmail|hotmail|outlook)\.com|\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])"
                            r"\.\d{1,3}\.\d{1,3}\b|\b157\.173\.\d{1,3}\.\d{1,3}\b", re.I)
SOBROU = re.compile(r"\$?aact_[A-Za-z0-9_$]{20,}|\b(?:sk|pk|rk)_live_[0-9A-Za-z]{16,}|\bAKIA[0-9A-Z]{16}\b|"
                    r"-----BEGIN [A-Z ]*PRIVATE KEY|\bsk-[A-Za-z0-9_-]{12,}|AIza[0-9A-Za-z_-]{30,}|\bgh[pousr]_[A-Za-z0-9]{20,}|\bya29\.|"
                    r"\bGOCSPX-|(?<!\d)\d{8,10}:AA[0-9A-Za-z_-]{30,}|\bg\.a000[0-9A-Za-z_-]{20,}|SAPISID\w*HASH(?:%20|\s+)\d+_[0-9a-f]{40}|\bgsk_[0-9A-Za-z]{20,}|\bhf_[0-9A-Za-z]{20,}|"
                    r"https?://[^:/\s\"']+:[^@/\s\"'<]{4,}@|"
                    # 13/11: a varredura final também barra proxy sem "http://" (usuario:senha@IP:porta)
                    r"(?<![\w/@.:-])[A-Za-z][\w.-]{2,}:[^@\s\"'<>/:]{6,}@(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b")


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _troca_ip(m):
    """IP público vira <IP>. Ficam: rede local/loopback/DNS conhecido e o que é versão, não IP (120.0.0.0 do Chrome)."""
    ip = m.group(0)
    partes = ip.split(".")
    if IP_LIVRE.match(ip) or ip.endswith(".0.0") or any(len(x) > 1 and x[0] == "0" or int(x) > 255 for x in partes):
        return ip
    return "<IP>"


def limpar(txt, extra=None):
    """Devolve o texto sem segredo. extra=True tira também o que identifica conta/máquina (repositório público)."""
    extra = LIMPEZA_EXTRA if extra is None else extra
    for rx, troca in PADROES + (PADROES_PUBLICO if extra else []):
        txt = rx.sub(_troca_ip if troca is None else troca, txt)
    return txt


def _pasta_vai(pai, d):
    if d.lower() in PASTAS_FORA or d.startswith(("_", ".")) or NOME_SEGREDO.search(d) or PASTA_PERFIL.search(d):
        return False
    return not os.path.islink(os.path.join(pai, d))


def _vai(caminho, nome):
    if Path(nome).suffix.lower() not in EXT or ".bak" in nome or ".bkp" in nome or NOME_SEGREDO.search(nome):
        return False
    if LIMPEZA_EXTRA and NOME_SO_PRIVADO.search(nome):
        return False
    try:
        return os.path.getsize(caminho) < TAMANHO_MAX
    except OSError:
        return False


def montar():
    n_arq = n_limpo = 0
    vistos = set()
    for proj in PROJETOS:
        raiz = Path("D:/") / proj
        if not raiz.is_dir():
            continue
        for r, ds, fs in os.walk(raiz):
            if MARCA_PERFIL & set(fs):  # caiu dentro de um perfil do Chrome com nome fora do padrão: não desce
                ds[:] = []
                continue
            ds[:] = [d for d in ds if _pasta_vai(r, d)]
            for f in fs:
                orig = os.path.join(r, f)
                if not _vai(orig, f):
                    continue
                rel = Path(proj) / Path(orig).relative_to(raiz)
                dst = DESTINO / rel
                vistos.add(str(rel).replace("\\", "/"))
                try:
                    txt = Path(orig).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                limpo = limpar(txt)
                n_limpo += limpo != txt
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not dst.exists() or dst.read_text(encoding="utf-8", errors="replace") != limpo:
                    dst.write_text(limpo, encoding="utf-8")
                n_arq += 1
    for nome in RAIZ_SOLTOS:  # 13/11: scripts soltos na raiz do D: (sentinela, monitor do Opus...)
        orig = Path("D:/") / nome
        if not orig.is_file() or not _vai(str(orig), nome):
            continue
        rel = Path("raiz_D") / nome
        vistos.add(str(rel).replace("\\", "/"))
        limpo = limpar(orig.read_text(encoding="utf-8", errors="replace"))
        (DESTINO / rel).parent.mkdir(parents=True, exist_ok=True)
        (DESTINO / rel).write_text(limpo, encoding="utf-8")
        n_arq += 1
    # 13/11 dona ("você mexe aqui e ele lá, sincronizam no GitHub e deixam recados um pro outro por lá"): os recados
    # entre o agente do D: e o agente online ficam no D: (video-fila\agentes) e vão TAMBÉM pra raiz do repositório,
    # onde o agente online procura. Sem isso a limpeza abaixo apagava o recado a cada envio.
    for nome in RECADOS_RAIZ:
        orig = Path(r"D:\video-fila\agentes") / nome
        if orig.is_file():
            vistos.add(nome)
            (DESTINO / nome).write_text(limpar(orig.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
            n_arq += 1
    # o que sumiu do D: sai da cópia também
    for p in list(DESTINO.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            rel = str(p.relative_to(DESTINO)).replace("\\", "/")
            if rel not in vistos and rel not in ("README.md", ".gitignore"):
                p.unlink()
    log(f"montado: {n_arq} arquivos ({n_limpo} com segredo trocado por <SEGREDO_REMOVIDO>)")


def varrer():
    """Recusa o envio se sobrou algo com cara de chave."""
    achados = []
    for p in DESTINO.rglob("*"):
        if p.is_file() and ".git" not in p.parts:
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            m = SOBROU.search(t) or (SOBROU_PUBLICO.search(t) if LIMPEZA_EXTRA else None)
            if m:
                achados.append(f"{p.relative_to(DESTINO)}: {m.group(0)[:12]}…")
    return achados


def readme():
    (DESTINO / "README.md").write_text(
        "# sistema-videos\n\nCópia só do CÓDIGO dos projetos de vídeo (recap de anime/manhwa, Shorts, longos, capas, "
        "postagem no YouTube/TikTok/Instagram, Flow/Veo, Kaggle).\nMídia, modelos, perfis de navegador, logs e "
        "segredos ficam fora. Chave/senha dentro de código aparece como `<SEGREDO_REMOVIDO>`.\n\n"
        "Cada pasta da raiz = um projeto do disco D: da máquina principal. Atualizado sozinho todo dia "
        "(`hipercool-materiais/comum/salvar_github.py`).\n\nComece por:\n"
        "- `recapd-ambientes/` — recap longo (Kaggle), Shorts de parceiro, capas (`producao/colab`, `producao/bin`)\n"
        "- `video-fila/` — controlador das máquinas, painel, vigilância, relatório (`relatorio_ronda.py`)\n"
        "- `postador-de-videos/` — postagem e Studio do YouTube, TikTok, Instagram\n"
        "- `hipercool-materiais/comum/` — código comum e o pesquisador de melhorias\n", encoding="utf-8")
    (DESTINO / ".gitignore").write_text("*.mp4\n*.wav\n*.mp3\n*.png\n*.jpg\n*.pth\n*.onnx\n*.log\n__pycache__/\n"
                                        "venv/\n.venv/\nnode_modules/\n", encoding="utf-8")


def git(*a, ok=False):
    r = subprocess.run(["git", "-C", str(DESTINO), *a], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1800)
    if r.returncode and not ok:
        raise RuntimeError(f"git {' '.join(a)}: {(r.stderr or r.stdout)[-300:]}")
    return r.stdout


def enviar():
    if not (DESTINO / ".git").exists():
        git("init", "-b", "main")
        git("config", "user.name", "sistema-videos")
        git("config", "user.email", "sistema-videos@users.noreply.github.com")
    r = subprocess.run([GH, "repo", "view", REPO], capture_output=True, text=True)
    if r.returncode:
        subprocess.run([GH, "repo", "create", REPO, "--public" if PUBLICO else "--private", "--description",
                        "Código dos projetos de vídeo (sem mídia e sem segredos)"], check=True, capture_output=True)
        log(f"repositório criado ({'PÚBLICO' if PUBLICO else 'privado'}): {REPO}")
    if "origin" not in git("remote", ok=True):
        git("remote", "add", "origin", f"https://github.com/{REPO}.git")
    subprocess.run([GH, "auth", "setup-git"], capture_output=True)
    git("add", "-A")
    if not git("status", "--porcelain").strip():
        log("nada mudou desde o último envio")
        return
    git("commit", "-q", "-m", f"atualização automática {datetime.now():%d/%m/%Y %H:%M}")
    git("push", "-u", "origin", "main")
    log(f"enviado para https://github.com/{REPO}")


def main():
    if os.environ.get("SALVAR_GITHUB", "1") == "0":
        return
    DESTINO.mkdir(exist_ok=True)
    montar()
    readme()
    sobrou = varrer()
    if sobrou:
        log(f"ENVIO BLOQUEADO: {len(sobrou)} arquivo(s) ainda com cara de segredo: " + "; ".join(sobrou[:15]))
        sys.exit(2)
    log("varredura: nenhum segredo aparente")
    if "--montar" not in sys.argv:
        enviar()


if __name__ == "__main__":
    main()
