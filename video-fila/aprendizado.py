# -*- coding: utf-8 -*-
"""aprendizado.py — aprender com os vídeos dos parceiros (dono 20/10).

Quando o Cortes baixa o vídeo de um parceiro (D:\\recapd-ambientes\\producao\\workspace\\anime\\<id>_<título>\\source.mp4,
PC1), este estudo pega a pasta (sem baixar de novo — yt-dlp sem rajada), tira quadros + a fala (legenda/roteiro que o
pipeline já gerou) e pergunta a 2 modelos o que o parceiro faz que NÓS ainda não fazemos: efeito, transição, trilha,
som, piada, jeito de falar, gíria, visual. Os 2 modelos são comparados (aprovados por modelo, `placar`) por 1-2
semanas pra ficar com o melhor: Claude Sonnet pelo gateway (OmniRoute) e Gemini (gemini_llm do hipercool).

- acervo:  D:\\video-fila\\aprendizado\\acervo.jsonl (achado + vídeo/url/tempo + modelo + status pendente/aprovado/
           reprovado) e o trecho (mp4, ou mp3 pra som/trilha/fala) em aprendizado\\trechos\\.
- Telegram: pelo portão avisos.py, 1 mensagem por achado bom (nota >= NOTA_MIN) + o trecho; o dono RESPONDE à
           mensagem com "sim" (aprova) ou "não" (reprova) — notificar_telegram.responder chama responder() daqui.
- Regra: sessão que mexer na produção lê `python D:\\video-fila\\aprendizado.py aprovados` e avalia o que aplicar
           (memória feedback-aprendizado-parceiros); aplicado = `marcar <id> aplicado`.

    python aprendizado.py rodada            1 vídeo novo (o VigiaVideos chama a cada 30 min)
    python aprendizado.py rodada --pasta X  estuda essa pasta (teste)
    python aprendizado.py aprovados         gera aprendizado\\PARA_IMPLEMENTAR.md e mostra o topo (aprovados + candidatos)
    python aprendizado.py placar            aprovados x reprovados por modelo
    python aprendizado.py marcar <id[,id2...]> aplicado|aprovado|reprovado [--motivo "..."]

Dono 22/10 ("não sabia que tinha que responder; se eu demorar o sistema mesmo vê o que pode implementar e deixa
documentado, e quem for mexer é obrigado a ler, já que o vigia e a IA são fracos"): achado sem resposta em 24 h com
nota >= 7 vira "candidato" (o sistema decide). PARA_IMPLEMENTAR.md junta os parecidos (o mesmo truque visto em vários
vídeos pesa mais) e é refeito a cada rodada. Quem avalia e aplica é a SESSÃO que for mexer na produção (modelo forte),
nunca o vigia nem a IA do painel; aplicou ou descartou = marcar (o descartado não volta a ser sugerido).
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — 29/10 (dona): nenhum processo filho (yt-dlp, ssh, ffmpeg) abre janela
import argparse
import base64
import hashlib
import json
import re
import unicodedata
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):  # pythonw (NotificarTelegram) não tem stdout
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path(__file__).resolve().parent
PASTA = BASE / "aprendizado"
ACERVO = PASTA / "acervo.jsonl"
FEITOS = PASTA / "feitos.json"
TRECHOS = PASTA / "trechos"
WORK = Path(r"D:\recapd-ambientes\producao\workspace\anime")
ASSETS = Path(r"D:\hipercool-materiais\assets")
HIPER_BIN = Path(r"D:\hipercool-videos\bin")
GATEWAY = Path(r"D:\hipercool-videos\secrets\claude_proxy.json")
MODELO_CLAUDE = "kr/claude-sonnet-4.5"
RESERVAS_GATEWAY = ("agy/gemini-3.8-flash-high",)  # o outro modelo da comparação já é o Gemini direto (_gemini)
MAX_IDADE_H = 72
QUADROS = 10
NOTA_MIN = 7
MAX_TELEGRAM = 3
TIPOS = ("efeito", "transição", "trilha", "som", "piada", "jeito_de_falar", "gíria", "visual", "outro")
SO_AUDIO = ("trilha", "som", "jeito_de_falar", "gíria", "piada")


def log(msg):
    print(f"[{datetime.now():%d/%m %H:%M:%S}] aprendizado: {msg}", flush=True)


def _ler_json(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar_json(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def acervo():
    out = []
    try:
        for ln in ACERVO.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
    except OSError:
        pass
    return out


def _gravar_acervo(itens):
    PASTA.mkdir(parents=True, exist_ok=True)
    tmp = ACERVO.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in itens), encoding="utf-8")
    tmp.replace(ACERVO)


# ─── o que estudar ──────────────────────────────────────────────────────────────
def candidatos():
    feitos = _ler_json(FEITOS, {})
    limite = time.time() - MAX_IDADE_H * 3600
    ps = []
    for d in WORK.iterdir() if WORK.exists() else []:
        mp4 = d / "source.mp4"
        if d.is_dir() and d.name not in feitos and mp4.exists() and mp4.stat().st_mtime >= limite:
            ps.append(d)
    return sorted(ps, key=lambda d: -(d / "source.mp4").stat().st_mtime)


def _fala(d):
    """Texto falado: legenda .vtt (sem tempos) ou roteiro.txt; '' se não há."""
    for v in sorted(d.glob("*.vtt")):
        linhas = [ln.strip() for ln in v.read_text(encoding="utf-8", errors="replace").splitlines()]
        txt = [re.sub(r"<[^>]+>", "", ln) for ln in linhas if ln and "-->" not in ln and not ln.isdigit()
               and not ln.startswith(("WEBVTT", "Kind:", "Language:"))]
        unicos = [t for i, t in enumerate(txt) if t and (i == 0 or t != txt[i - 1])]
        if unicos:
            return " ".join(unicos)[:6000]
    r = d / "roteiro.txt"
    return r.read_text(encoding="utf-8", errors="replace")[:6000] if r.exists() else ""


def _duracao(mp4):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                           capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except (ValueError, OSError, subprocess.SubprocessError):
        return 0.0


def _quadros(mp4, tmp):
    """[(segundo, bytes jpg)] espalhados pelo vídeo."""
    dur = _duracao(mp4)
    if dur <= 0:
        return []
    out = []
    for i in range(QUADROS):
        t = dur * (i + 0.5) / QUADROS
        f = tmp / f"q{i:02d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1",
                        "-vf", "scale='if(gt(iw,ih),640,-2)':'if(gt(iw,ih),-2,640)'", "-q:v", "4", str(f)],
                       capture_output=True, timeout=60)
        if f.exists():
            out.append((round(t, 1), f.read_bytes()))
    return out


def _inventario():
    """O que já temos (pra o modelo só trazer o que falta): pastas de assets com quantidade e exemplos + módulos fx."""
    partes = []
    for d in sorted(p for p in ASSETS.iterdir() if p.is_dir() and not p.name.startswith(("_", "models", "stress"))):
        arqs = [f.stem for f in d.rglob("*") if f.is_file()]
        if arqs:
            partes.append(f"{d.name} ({len(arqs)}): " + ", ".join(sorted(set(arqs))[:12]))
    fx = sorted(f.stem for f in HIPER_BIN.glob("*.py") if re.match(r"(fx_|styled_|elemental_|panel_fx|efeito)", f.stem))
    partes.append("módulos de efeito/transição: " + ", ".join(fx))
    return "\n".join(partes)[:3500]


PERGUNTA = """Você estuda um vídeo curto de um canal PARCEIRO pra nossa produção de vídeos (YouTube Shorts/TikTok em
português). Recebe {n} quadros (cada um com o segundo do vídeo) e a fala do vídeo.
Liste SÓ o que esse vídeo faz que NÓS ainda não fazemos e vale copiar: efeito, transição, trilha, som, piada,
jeito_de_falar, gíria, visual (legenda, enquadramento, cor, texto na tela), outro. Ignore o que é comum ou o que já
temos (lista abaixo). Seja concreto (o que acontece, em que segundo) e diga como aplicar na nossa produção.
Máximo 5 achados; nenhum é melhor que um achado fraco.

O QUE JÁ TEMOS:
{inventario}

FALA DO VÍDEO:
{fala}

Responda SÓ JSON: {{"achados": [{{"tipo": "efeito|transição|trilha|som|piada|jeito_de_falar|gíria|visual|outro",
"descricao": "o que é, curto", "inicio": segundo, "fim": segundo, "por_que_novo": "...", "como_aplicar": "...",
"nota": 0-10 (quanto vale pra nós)}}]}}"""


def _json(txt):
    m = re.search(r"\{.*\}", txt or "", re.S)
    return json.loads(m.group(0)) if m else None


def _claude(quadros, pergunta):
    c = _ler_json(GATEWAY, {})
    conteudo = []
    for t, b in quadros:
        conteudo.append({"type": "text", "text": f"Quadro no segundo {t}:"})
        conteudo.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()}})
    conteudo.append({"type": "text", "text": pergunta})
    erro = None
    try:  # 26/10 conta-gota: sem Kiro pros robôs (ia_reserva.kiro_para_robos)
        import ia_reserva
        kiro = ia_reserva.kiro_para_robos()
    except Exception:  # noqa: BLE001
        kiro = False
    for modelo in ((MODELO_CLAUDE,) if kiro else ()) + RESERVAS_GATEWAY:  # 23/10: reserva Gemini 3.8 do Antigravity
        corpo = {"model": modelo, "max_tokens": 2000, "temperature": 0.3,
                 "messages": [{"role": "user", "content": conteudo}]}
        req = urllib.request.Request(c["base_url"].rstrip("/") + "/v1/chat/completions", data=json.dumps(corpo).encode(),
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + c["auth_token"]})
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                msg = json.loads(r.read())["choices"][0]["message"]["content"]
            IA_USADA["claude-sonnet"] = NOMES_IA.get(modelo, modelo)
            return _json(msg if isinstance(msg, str) else "".join(p.get("text", "") for p in msg))
        except Exception as e:  # noqa: BLE001 — sem crédito (401) / fora: próximo modelo
            erro = e
    raise erro


def _gemini(quadros, pergunta):
    if str(HIPER_BIN) not in sys.path:
        sys.path.append(str(HIPER_BIN))
    import gemini_llm
    IA_USADA["gemini"] = f"Gemini {gemini_llm.MODEL.removeprefix('gemini-')} (chave de API)"
    tempos = ", ".join(f"imagem {i + 1} = segundo {t}" for i, (t, _) in enumerate(quadros))
    return _json(gemini_llm.describe_images([b for _, b in quadros], f"({tempos})\n\n" + pergunta,
                                            max_tokens=2500, temperature=0.3))


MODELOS = (("claude-sonnet", _claude), ("gemini", _gemini))
# 31/10 (dona: "aprendizado usa qual IA? me diga, porque também podemos desativar"): o nome "claude-sonnet" ficou da
# 1ª versão; com o Kiro fora dos robôs (26/10) quem responde é o Gemini 3.8 Flash do Antigravity
NOMES_IA = {MODELO_CLAUDE: "Claude Sonnet 4.5 (Kiro)", "agy/gemini-3.8-flash-high": "Gemini 3.8 Flash (Antigravity)"}
IA_USADA = {}


# ─── trecho e Telegram ─────────────────────────────────────────────────────────
def _cortar(mp4, a, aid):
    try:
        ini = max(0.0, float(a.get("inicio") or 0))
        fim = float(a.get("fim") or ini + 6)
    except (TypeError, ValueError):
        ini, fim = 0.0, 6.0
    dur = min(max(fim - ini, 3.0), 12.0)
    TRECHOS.mkdir(parents=True, exist_ok=True)
    audio = a.get("tipo") in SO_AUDIO
    out = TRECHOS / f"{aid}.{'mp3' if audio else 'mp4'}"
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, ini - 0.5):.2f}", "-t", f"{dur + 1:.2f}", "-i", str(mp4)]
    cmd += (["-vn", "-c:a", "libmp3lame", "-q:a", "4"] if audio else
            ["-vf", "scale='if(gt(iw,ih),854,-2)':'if(gt(iw,ih),-2,854)'", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "28", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart"])
    subprocess.run(cmd + [str(out)], capture_output=True, timeout=180)
    return out if out.exists() and out.stat().st_size > 1000 else None


def _avisar(item):
    sys.path.insert(0, str(BASE)) if str(BASE) not in sys.path else None
    import avisos
    from html import escape as e
    # 31/10 (dona: "eu acabo não aprovando nada, é bom ele aprovar sozinho"): o que sai aqui já entra aprovado
    texto = (f"<b>Aprendizado (parceiro)</b> — {e(item['tipo'])} · nota {item.get('nota')}\n"
             f"IA: {e(item.get('ia') or item['modelo'])}\n"
             f"{e(item['descricao'])}\n<b>Por que é novo:</b> {e(item.get('por_que_novo') or '')}\n"
             f"<b>Como aplicar:</b> {e(item.get('como_aplicar') or '')}\n"
             f"Vídeo: {e(item['url'])} (seg {item.get('inicio')}-{item.get('fim')})\n"
             f"✅ <i>Aprovado sozinho (entra em PARA_IMPLEMENTAR.md). Se não quiser, responda NÃO. id {item['id']}</i>")
    mid = avisos.enviar(texto, "aprendizado", importante=True, chave="<SEGREDO_REMOVIDO>" + item["id"])
    if mid and item.get("trecho"):
        avisos.enviar_arquivo(item["trecho"], f"trecho do achado {item['id']}", "aprendizado", responder_a=mid)
    return mid


# ─── rodada ────────────────────────────────────────────────────────────────────
def estudar(d):
    mp4 = d / "source.mp4"
    vid = d.name.split("_", 1)[0]
    url = f"https://www.youtube.com/watch?v={vid}"
    fala = _fala(d)
    with tempfile.TemporaryDirectory(prefix="aprendizado_") as tmp:
        quadros = _quadros(mp4, Path(tmp))
    if not quadros:
        return [], "sem quadros"
    pergunta = PERGUNTA.format(n=len(quadros), inventario=_inventario(), fala=fala or "(sem fala)")
    novos, erros = [], []
    for nome, f in MODELOS:
        try:
            r = f(quadros, pergunta) or {}
        except Exception as ex:  # noqa: BLE001  (um modelo fora não impede o outro)
            erros.append(f"{nome}: {type(ex).__name__} {str(ex)[:100]}")
            continue
        for a in (r.get("achados") or [])[:5]:
            if not isinstance(a, dict) or not a.get("descricao"):
                continue
            aid = hashlib.md5(f"{vid}|{nome}|{a['descricao']}".encode()).hexdigest()[:8]
            item = {"id": aid, "em": datetime.now().isoformat(timespec="seconds"), "modelo": nome, "video": d.name,
                    "url": url, "pasta": str(d), "tipo": a.get("tipo") if a.get("tipo") in TIPOS else "outro",
                    "descricao": a["descricao"], "inicio": a.get("inicio"), "fim": a.get("fim"),
                    "por_que_novo": a.get("por_que_novo"), "como_aplicar": a.get("como_aplicar"),
                    "nota": a.get("nota"), "status": "pendente", "ia": IA_USADA.get(nome, nome)}
            try:
                bom = float(item["nota"] or 0) >= NOTA_MIN
            except (TypeError, ValueError):
                bom = False
            if bom:
                t = _cortar(mp4, a, aid)
                item["trecho"] = str(t) if t else None
            novos.append(item)
    return novos, "; ".join(erros)


def rodada(pasta=None):
    """1 vídeo por vez; outra rodada viva (o Gemini às vezes leva 10 min) = sai."""
    import msvcrt
    PASTA.mkdir(parents=True, exist_ok=True)
    trava = open(PASTA / "rodada.lock", "a+b")
    try:
        trava.seek(0)
        msvcrt.locking(trava.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        log("outra rodada em andamento — saindo")
        trava.close()
        return 0
    try:
        return _rodada(pasta)
    finally:
        trava.close()


JA_TEMOS = PASTA / "ja_temos.json"  # memória do que já existe (dono 21/10): o filtro não manda de novo
MAX_DIA = 5
_RUIM = [
    (re.compile(r"marca d.?[aá]gua|watermark|logotipo|logomarca|logo do canal|@\w|nome do canal|assinatura do canal", re.I),
     "marca/logo do parceiro (não é técnica pra copiar)"),
    (re.compile(r"esc?atol[oó]gic|coc[oô]|defec|xixi|mij|peid|fezes|privada|banheiro|cal[çc]a suja|pel[eé] pra nadar|"
                r"pel[eé] para nadar|tomar leite|xuto|sexual|sexo|nud|pelad|calcinha|bunda|peit", re.I),
     "humor escatológico/sexual (derruba a monetização)"),
]


def _conserta(s):
    """Texto com acento quebrado (Ã¡, Ã£ — utf-8 lido como latin-1, comum no Gemini) volta ao normal."""
    if not isinstance(s, str) or "Ã" not in s:
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def _palavras(s):
    s = unicodedata.normalize("NFKD", str(s or "").lower()).encode("ascii", "ignore").decode()
    return {w for w in re.findall(r"[a-z]{4,}", s)}


def _parecido(a, b):
    pa, pb = _palavras(a), _palavras(b)
    # sobre a descrição menor: "Linha do tempo no topo" x "Linha do tempo horizontal persistente no topo..."
    return len(pa) >= 2 and len(pb) >= 2 and len(pa & pb) / min(len(pa), len(pb)) >= 0.6


def _barrado(item, outros, temos):
    texto = " ".join(str(item.get(k) or "") for k in ("descricao", "por_que_novo", "como_aplicar"))
    for rx, motivo in _RUIM:
        if rx.search(texto):
            return motivo
    for t in temos:
        if _parecido(item["descricao"], t.get("descricao")):
            return f"já existe: {t.get('descricao')[:80]} ({t.get('origem', 'memória')})"
    for o in outros:
        if o["id"] != item["id"] and _parecido(item["descricao"], o.get("descricao")):
            return f"repetido de {o['id']} ({o.get('status')})"
    return None


def _lembrar(item, origem):
    temos = _ler_json(JA_TEMOS, [])
    if not any(_parecido(item["descricao"], t.get("descricao")) for t in temos):
        temos.append({"descricao": item["descricao"], "origem": origem, "em": datetime.now().isoformat(timespec="seconds")})
        _gravar_json(JA_TEMOS, temos)


def _mandados_hoje(itens):
    hoje = datetime.now().date().isoformat()
    return sum(1 for i in itens if i.get("mensagem") and str(i.get("em", ""))[:10] == hoje)


def _filtrar(novos, itens):
    """Conserta o texto e marca 'descartado' (com o motivo) o que não presta ou já existe."""
    temos = _ler_json(JA_TEMOS, [])
    aceitos = []
    for n in novos:
        for k in ("descricao", "por_que_novo", "como_aplicar", "tipo"):
            n[k] = _conserta(n.get(k))
        motivo = _barrado(n, itens + aceitos, temos)
        if motivo:
            n["status"], n["motivo"] = "descartado", motivo
        else:
            aceitos.append(n)
    return novos


def _rodada(pasta):
    alvo = [Path(pasta)] if pasta else candidatos()[:1]
    if not alvo:
        log("nada novo pra estudar")
        return 0
    d = alvo[0]
    log(f"estudando {d.name}")
    novos, erros = estudar(d)
    itens = acervo()
    ja = {i["id"] for i in itens}
    novos = _filtrar([n for n in novos if n["id"] not in ja], itens)
    feitos = _ler_json(FEITOS, {})
    feitos[d.name] = {"em": datetime.now().isoformat(timespec="seconds"), "achados": len(novos), "erros": erros}
    _gravar_json(FEITOS, feitos)
    mapa = _ler_json(PASTA / "mensagens.json", {})

    def nota(n):
        try:
            return float(n.get("nota") or 0)
        except (TypeError, ValueError):
            return 0.0
    # dono 19/10: menos mensagens — no máximo MAX_TELEGRAM por vídeo, os de nota maior (o resto fica no acervo)
    vaga = max(0, MAX_DIA - _mandados_hoje(itens))  # dono 21/10: no máximo MAX_DIA por dia, os melhores
    bons = (n for n in novos if n["status"] == "pendente" and nota(n) >= NOTA_MIN)
    for n in sorted(bons, key=nota, reverse=True)[:min(MAX_TELEGRAM, vaga)]:
        if True:
            mid = _avisar(n)
            if mid:
                n["mensagem"] = mid
                mapa[str(mid)] = n["id"]
                n.update(status="aprovado", decidido_em=datetime.now().isoformat(timespec="seconds"),
                         motivo="aprovado sozinho (dona 31/10: ela não precisa responder)")
    todos = itens + novos
    promover(todos)
    _gravar_acervo(todos)
    _gravar_json(PASTA / "mensagens.json", mapa)
    try:
        documento(todos)
    except Exception as ex:  # noqa: BLE001  (o documento nunca derruba a rodada)
        log(f"PARA_IMPLEMENTAR.md não foi gerado: {ex}")
    log(f"{len(novos)} achado(s) ({sum(1 for n in novos if n.get('mensagem'))} no Telegram)"
        + (f" | erros: {erros}" if erros else ""))
    return len(novos)


def marcar(aid, status, motivo=None):
    itens = acervo()
    achou = None
    for i in itens:
        if i["id"] == aid:
            i["status"] = status
            i["decidido_em"] = datetime.now().isoformat(timespec="seconds")
            if motivo:
                i["motivo"] = motivo
            achou = i
    if achou:
        _gravar_acervo(itens)
    return achou


# ─── sem resposta do dono: o sistema decide e documenta (dono 22/10) ──────────
ESPERA_DONO_H = 24  # dono 22/10 não sabia que tinha de responder; até 5 mensagens/dia: 1 dia basta
DOC = PASTA / "PARA_IMPLEMENTAR.md"
DOC_TOPO = 40


def _nota(i):
    try:
        return float(i.get("nota") or 0)
    except (TypeError, ValueError):
        return 0.0


def promover(itens):
    """Pendente há mais de 48 h, nota >= NOTA_MIN e sem resposta = 'candidato'. Devolve quantos promoveu."""
    limite = (datetime.now() - timedelta(hours=ESPERA_DONO_H)).isoformat(timespec="seconds")
    n = 0
    for i in itens:
        if i.get("status") == "pendente" and str(i.get("em") or "") < limite and _nota(i) >= NOTA_MIN:
            i.update(status="candidato", decidido_em=datetime.now().isoformat(timespec="seconds"),
                     motivo=f"sem resposta do dono em {ESPERA_DONO_H} h, nota {i.get('nota')}")
            n += 1
    return n


def _grupos(itens):
    """Junta os achados parecidos; o mesmo truque visto em mais vídeos vem primeiro (sinal mais forte que 1 nota)."""
    grupos = []
    for i in sorted(itens, key=_nota, reverse=True):
        for g in grupos:
            if _parecido(i["descricao"], g[0]["descricao"]):
                g.append(i)
                break
        else:
            grupos.append([i])
    return sorted(grupos, key=lambda g: (-len({x.get("video") for x in g}), -max(_nota(x) for x in g)))


def documento(itens=None):
    """Refaz aprendizado\\PARA_IMPLEMENTAR.md. Devolve (aprovados, grupos de candidatos)."""
    itens = acervo() if itens is None else itens
    aprov = [i for i in itens if i.get("status") == "aprovado"]
    grupos = _grupos([i for i in itens if i.get("status") == "candidato"])

    def bloco(n, g):
        p = g[0]
        vids = len({x.get("video") for x in g})
        ex = "; ".join(f"{x['url']} seg {x.get('inicio')}" + (f" (trecho {Path(x['trecho']).name})" if x.get("trecho") else "")
                       for x in g[:3])
        return (f"### {n}. [{p['tipo']}] {p['descricao']}\n"
                f"- visto em {vids} vídeo(s) · nota máx. {max(_nota(x) for x in g):g} · modelos: "
                f"{', '.join(sorted({x['modelo'] for x in g}))}\n"
                f"- como aplicar: {p.get('como_aplicar') or '—'}\n- por que é novo: {p.get('por_que_novo') or '—'}\n"
                f"- exemplos: {ex}\n- ids: {','.join(x['id'] for x in g)}\n")
    linhas = [
        "# Aprendizado com os parceiros — PARA IMPLEMENTAR (refeito a cada rodada; não editar à mão)",
        "",
        f"Atualizado {datetime.now():%d/%m/%Y %H:%M}. Gerado por D:\\video-fila\\aprendizado.py.",
        "",
        "OBRIGATÓRIO (dona 01/11): ninguém implanta isto sozinho — o chat que for melhorar vídeo analisa estes itens",
        "ANTES de editar e marca cada um. Passo a passo: D:\\video-fila\\aprendizado\\LEIA_ANTES_DE_MELHORAR.md",
        "",
        "REGRA (dono 22/10): toda sessão que for mexer na produção dos vídeos LÊ isto antes, avalia e decide. Quem avalia",
        "é a sessão (modelo forte), nunca o vigia nem a IA do painel. Para cada grupo: aplicar (testando num vídeo real,",
        "com backup) ou descartar com motivo. Depois:",
        "    python D:\\video-fila\\aprendizado.py marcar <ids do grupo> aplicado --motivo \"onde/como\"",
        "    python D:\\video-fila\\aprendizado.py marcar <ids do grupo> reprovado --motivo \"por que não serve\"",
        "(aplicado/reprovado entram no ja_temos.json: o estudo não sugere parecido de novo).",
        f"Candidato = o dono não respondeu em {ESPERA_DONO_H} h e a nota era >= 7: é sugestão, não ordem. Cuidado com o que já existe",
        "na produção, com humor/visual que derruba monetização e com marca do parceiro (não copiar marca).",
        "",
        f"## A. Aprovados (pela dona ou sozinho: os melhores de cada dia, nota >= {NOTA_MIN}) ({len(aprov)})",
        "",
    ]
    linhas += [bloco(n, [i]) for n, i in enumerate(aprov, 1)] or ["(nenhum)", ""]
    linhas += [f"## B. Candidatos (sem resposta em {ESPERA_DONO_H} h): {len(grupos)} grupo(s), os {DOC_TOPO} mais fortes",
               ""]
    linhas += [bloco(n, g) for n, g in enumerate(grupos[:DOC_TOPO], 1)]
    if len(grupos) > DOC_TOPO:
        linhas += [f"(+ {len(grupos) - DOC_TOPO} grupo(s) mais fracos: vistos em 1 vídeo só; ficam no acervo.jsonl)"]
    DOC.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return aprov, grupos


def responder(message_id, texto):
    """Chamado pelo notificar_telegram.responder quando o dono responde a uma mensagem. True se era do aprendizado."""
    aid = _ler_json(PASTA / "mensagens.json", {}).get(str(message_id))
    if not aid:
        return False
    t = texto.strip().lower()
    status = ("aprovado" if re.match(r"^(sim|s|aprova|aprovar|aprovado|ok|bom|👍)", t) else
              "reprovado" if re.match(r"^(n[aã]o|n|reprova|reprovar|reprovado|ruim|👎)", t) else None)
    sys.path.insert(0, str(BASE)) if str(BASE) not in sys.path else None
    import avisos
    if not status:
        avisos.enviar("Não entendi: responda SIM ou NÃO.", "aprendizado", importante=True, html_ok=False,
                      chave=f"aprendizado:nao-entendi:{message_id}:{t[:20]}", responder_a=message_id)
        return True
    i = marcar(aid, status)
    if i:  # aprovado = vai ser aplicado; reprovado = o dono não quer — nos dois casos o filtro não manda parecido de novo
        _lembrar(i, f"{status} pelo dono")
    avisos.enviar(f"{'Aprovado' if status == 'aprovado' else 'Reprovado'}: {i['descricao'] if i else aid}",
                  "aprendizado", importante=True, html_ok=False, chave=f"aprendizado:decidido:{aid}:{status}",
                  responder_a=message_id)
    return True


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("rodada")
    r.add_argument("--pasta")
    sub.add_parser("aprovados")
    sub.add_parser("placar")
    sub.add_parser("limpar", help="passa o filtro (21/10) nos pendentes antigos: conserta acento, descarta lixo/repetido")
    m = sub.add_parser("marcar")
    m.add_argument("id", help="um id ou vários separados por vírgula (o grupo inteiro do PARA_IMPLEMENTAR.md)")
    m.add_argument("status", choices=["aprovado", "reprovado", "aplicado", "pendente", "candidato"])
    m.add_argument("--motivo")
    a = ap.parse_args()
    if a.cmd == "rodada":
        rodada(a.pasta)
    elif a.cmd == "aprovados":
        itens = acervo()
        if promover(itens):
            _gravar_acervo(itens)
        aprov, grupos = documento(itens)
        print(f"{len(aprov)} aprovado(s) pelo dono e {len(grupos)} grupo(s) de candidatos (sem resposta em "
              f"{ESPERA_DONO_H} h). LEIA: {DOC}")
        for i in aprov:
            print(f"  APROVADO {i['id']} [{i['tipo']}] {i['descricao'][:110]}")
        for g in grupos[:15]:
            print(f"  {len({x.get('video') for x in g})} vídeo(s) [{g[0]['tipo']}] {g[0]['descricao'][:110]}")
    elif a.cmd == "placar":
        pl = {}
        for i in acervo():
            pl.setdefault(i["modelo"], {}).setdefault(i["status"], 0)
            pl[i["modelo"]][i["status"]] += 1
        print(json.dumps(pl, ensure_ascii=False, indent=1))
    elif a.cmd == "marcar":
        for aid in [x.strip() for x in a.id.split(",") if x.strip()]:
            i = marcar(aid, a.status, a.motivo)
            if i and a.status in ("aplicado", "reprovado"):  # não sugerir parecido de novo
                _lembrar(i, f"{a.status} pela sessão" + (f": {a.motivo}" if a.motivo else ""))
            print(f"{aid}: {'ok' if i else 'id não achado'}")
        documento()
    elif a.cmd == "limpar":
        itens = acervo()
        outros = [i for i in itens if i["status"] != "pendente"]
        pend = _filtrar([i for i in itens if i["status"] == "pendente"], outros)
        _gravar_acervo(outros + pend)
        for i in pend:
            print(("DESCARTADO " + i.get("motivo", "") if i["status"] == "descartado" else "fica") + f" | [{i['tipo']}] {i['descricao'][:90]}")
        print("ficaram:", sum(1 for i in pend if i["status"] == "pendente"), "| descartados:", sum(1 for i in pend if i["status"] == "descartado"))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
