#!/usr/bin/env python3
r"""gemini_midia_http.py — IMAGEM e VÍDEO pelo app gemini.google.com SEM NAVEGADOR (1ª opção do trio).

Trio (dona 13/11/2026): 1º Gemini sem navegador (este módulo) -> 2º Flow sem navegador (HTTP + fábrica de tokens)
-> 3º Flow com navegador (tela). Ligado em:
  - imagem: D:\flow-imagens\cliente.py (gerar) — todos os projetos que pedem imagem passam por lá;
  - vídeo:  D:\veo\beta\gera_auto.py (gerar) — o robô do Veo.
Desligar: GEMINI_MIDIA=0 (tudo), GEMINI_IMAGEM=0 ou GEMINI_VIDEO=0.

Mesmo caminho do Argon (gemini_http.py): POST no StreamGenerate com os cookies cacheados da conta
(cookies/<conta>.json, renovados pelo argon_zelador). Nada de Chrome por pedido.

Como o pedido liga a ferramenta (medido 13/11 + lib HanaokaYuzu/Gemini-API):
  inner[49] = 11 (Criar vídeo) / 14 (Criar imagem); formato em msg[9] = [None*6, [[None, [None, "9:16"]]]];
  inner[45] = 1 = chat temporário (imagem não fica no histórico da conta). Só o texto "Crie um vídeo" NÃO basta.
  Vídeo: responde na hora "I'm generating your video" + c_id; fica pronto NA CONVERSA (batchexecute hNvQHb) em
  ~30-50 s; depois de baixar a conversa é apagada (GzXR5e).

NUNCA GASTA O ARGON: o pedido usa o modelo flash (imagem) / 8c46e95b1a07cecc (vídeo), não o 4 Argon; as cotas de
imagem e vídeo são outras (conferido 13/11: conta que gerou vídeo seguiu com o Argon). Ordem das contas:
  1º as que estão SEM cota de texto do Argon (crédito parado), 2º as que o Argon não está usando agora,
  sempre a que menos gerou hoje. Conta com cookie morto é pulada e avisada ao zelador (marcar_cookies).
FILA PRÓPRIA (midia_contas.json): falha de mídia nunca tira a conta do Argon. No máx. 2 contas por pedido
— nunca varre a lista (regra do IP no CLAUDE.md). 1 pedido por conta por vez (trava por conta).

Uso:
    from gemini_midia_http import gerar_imagem, gerar_video
    ok, detalhe = gerar_imagem("prompt", r"D:\saida\x.jpg", formato="9:16")
    ok, detalhe = gerar_video("prompt", r"D:\saida\x.mp4", formato="9:16", duracao=8)

    python -X utf8 -I gemini_midia_http.py imagem|video "prompt" saida [--formato 9:16] [--conta X]
    python -X utf8 -I gemini_midia_http.py estado
"""
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, r"D:\gemini-argo")
import gemini_http as gh  # sessão/cookies/tokens do Argon

BASE = Path(r"D:\gemini-argo")
ESTADO = BASE / "midia_contas.json"
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
log = logging.getLogger("gemini_midia")
if not log.handlers:
    _h = logging.FileHandler(BASE / "midia.log", encoding="utf-8")
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"))
    log.addHandler(_h)
log.setLevel(logging.INFO)
log.propagate = False  # não mistura com o argon.log

MAX_CONTAS_POR_PEDIDO = 2
ESPERA_FALHA = timedelta(minutes=30)
ESPERA_COTA = timedelta(hours=3)
# 13/11: os que deram certo ficaram prontos em 30-100 s; um ficou 7 min sem entregar e segurou o Flow (fallback).
ESPERA_VIDEO_S = int(os.environ.get("GEMINI_VIDEO_PRAZO_S", "240"))
MODELO_VIDEO = "8c46e95b1a07cecc"
MODELO_IMAGEM = gh.MODELOS["flash"]
FERRAMENTA_VIDEO, FERRAMENTA_IMAGEM = 11, 14
FORMATOS = ("16:9", "9:16", "1:1", "4:3", "3:4")

_trava = threading.RLock()
_travas_conta = {}

_RE_IMG = re.compile(r'https://lh3\.googleusercontent\.com/gg-dl/[A-Za-z0-9_\-]+')
_RE_CID = re.compile(r'\\"(c_[0-9a-f]+)\\",\\"(r_[0-9a-f]+)\\"')
_RE_MP4 = re.compile(r'https://contribution\.usercontent\.google\.com/download\?c=[^"\\]*?filename=video\.mp4[^"\\]*')
_RE_RECUSA = re.compile(r"(não posso|nao posso|can't|cannot|I'm unable|unable to|não consigo|não é possível|"
                        r"políticas|policy|violat)", re.I)
_RE_LIMITE = re.compile(r"(limit resets|more (videos|images) as soon|limite.{0,60}(imagens|vídeos|geraç)|"
                        r"reached.{0,30}limit|atingiu.{0,30}limite)", re.I)
# cotas (batchexecute MyzX6c): [recurso, disponível, limite, usado, [epoch volta, nanos]|null, 1]. Vídeo = 3 e 5.
_RE_COTA = re.compile(r"\[(\d+),(true|false),(\d+),(\d+),(?:\[(\d{10}),\d+\]|null),1\]")
RECURSOS_VIDEO = {3, 5}


class Recusou(Exception):
    pass


class SemCotaMidia(Exception):
    volta = None


class CookieMorto(Exception):
    pass


def ligado(tipo):
    if os.environ.get("GEMINI_MIDIA", "1") == "0":
        return False
    return os.environ.get("GEMINI_IMAGEM" if tipo == "imagem" else "GEMINI_VIDEO", "1") != "0"


# ─────────────────────── fila própria ───────────────────────
def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"contas": {}}


def _gravar(e):
    tmp = ESTADO.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
    for _ in range(20):
        try:
            os.replace(tmp, ESTADO)
            return
        except PermissionError:
            time.sleep(0.1)
    tmp.unlink(missing_ok=True)


def _em_uso_argon():
    """Contas com pedido do Argon em andamento NESTE processo (o proxy roda noutro: lá só o arquivo serve)."""
    try:
        import gemini_argon
        return {a for a, n in gemini_argon._EM_USO.items() if n > 0}
    except Exception:  # noqa: BLE001
        return set()


def candidatas(tipo):
    """Ordem de uso: 1º sem cota de texto do Argon, 2º o resto (fora as que o Argon usa agora); menos usada hoje antes."""
    agora = datetime.now()
    iso = agora.isoformat()
    hoje = iso[:10]
    argon = gh._ler_contas()["contas"]
    with _trava:
        c_est = _ler().get("contas", {})
    ocupadas = _em_uso_argon()
    saida = []
    for c in argon:
        ap = c["apelido"]
        if c.get("bloqueada"):
            continue
        if c.get("cookies_mortos_ate") and iso < c["cookies_mortos_ate"]:
            continue
        arq = gh._arq_cookies(ap)
        if not arq.exists():
            continue
        m = c_est.get(ap, {}).get(tipo, {})
        if m.get("fora_ate") and iso < m["fora_ate"]:
            continue
        sem_texto = bool(c.get("sem_cota_ate") and iso < c["sem_cota_ate"])
        grupo = 0 if sem_texto else (2 if ap in ocupadas else 1)
        usados = m.get("ok_hoje", 0) if m.get("dia") == hoje else 0
        # cookie renovado há pouco primeiro (morre ~2 h depois)
        idade_cookie = time.time() - arq.stat().st_mtime
        saida.append((grupo, usados, idade_cookie, ap))
    saida.sort()
    return [ap for *_x, ap in saida]


def _registrar(ap, tipo, ok, motivo="", espera=None, segundos=None):
    with _trava:
        e = _ler()
        m = e.setdefault("contas", {}).setdefault(ap, {}).setdefault(tipo, {})
        hoje = datetime.now().isoformat()[:10]
        if m.get("dia") != hoje:
            m.update(dia=hoje, ok_hoje=0, falhas_hoje=0)
        if ok:
            m["ok_hoje"] += 1
            m["total_ok"] = m.get("total_ok", 0) + 1
            m.pop("fora_ate", None)
            m["ultimo_ok"] = datetime.now().isoformat(timespec="seconds")
            if segundos:
                m["seg_total"] = round(m.get("seg_total", 0) + segundos, 1)
        else:
            m["falhas_hoje"] += 1
            m["ultimo_erro"] = motivo[:150]
            if espera:
                m["fora_ate"] = (datetime.now() + espera).isoformat(timespec="minutes")
        _gravar(e)


TRAVAS_DIR = BASE / "travas_midia"


def _trava_da(ap):
    """Trava ENTRE PROCESSOS por conta (o robô do Veo roda vários workers; cada um é um processo): 1 pedido de mídia
    por conta por vez. Mesma interface acquire(timeout)/release de um Lock."""
    from filelock import FileLock, Timeout

    class _T:
        def __init__(self, caminho):
            self.fl = FileLock(str(caminho))

        def acquire(self, timeout):
            try:
                self.fl.acquire(timeout=timeout)
                return True
            except Timeout:
                return False

        def release(self):
            self.fl.release()

    TRAVAS_DIR.mkdir(exist_ok=True)
    with _trava:
        if ap not in _travas_conta:
            _travas_conta[ap] = _T(TRAVAS_DIR / f"{ap}.lock")
        return _travas_conta[ap]


# ─────────────────────── HTTP comum ───────────────────────
def _sessao(conta):
    try:
        s = gh._carregar_sessao(conta)
        at, bl, fsid = gh._tokens(conta, s)
        return s, at, bl, fsid
    except (gh.SemCookies, gh.AuthFalhou) as e:
        # cookie morreu: sai da fila do Argon até o zelador renovar (o mesmo que o Argon faria) e daqui também
        try:
            gh.marcar_cookies(conta, False)
        except Exception:  # noqa: BLE001
            pass
        raise CookieMorto(str(e)) from e


def _batch(s, at, bl, fsid, rpc, args, path="/app"):
    url = ("https://gemini.google.com/_/BardChatUi/data/batchexecute"
           f"?rpcids={rpc}&source-path={urllib.parse.quote(path, safe='')}&bl={bl}&f.sid={fsid}&hl=pt"
           f"&_reqid={int(time.time()) % 1000000}&rt=c")
    freq = json.dumps([[[rpc, json.dumps(args), None, "generic"]]])
    r = s.post(url, data={"f.req": freq, "at": at}, timeout=60,
               headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8", "x-same-domain": "1",
                        "Origin": "https://gemini.google.com", "Referer": "https://gemini.google.com/"})
    if r.status_code != 200:
        raise RuntimeError(f"{rpc} HTTP {r.status_code}")
    return r.text


def _desescapar(t):
    return re.sub(r"\\+u0026", "&", re.sub(r"\\+u003d", "=", t))


def _pedido(prompt, ferramenta, modelo_hash, formato=None, temporario=False):
    msg = [prompt, 0, None, None, None, None, 0]
    if formato in FORMATOS:
        msg += [None, None, [None] * 6 + [[None, [None, formato]]]]
    inner = [msg, ["pt"], None] + [None] * 47
    inner[49] = ferramenta
    if temporario:
        inner[45] = 1
    return (json.dumps([None, json.dumps(inner, ensure_ascii=False)], ensure_ascii=False),
            json.dumps([1, None, None, None, modelo_hash]))


def _stream(conta, s, at, bl, fsid, freq, jspb):
    url, headers = gh._url_headers(bl, fsid, "pt", jspb)
    r = s.post(url, data={"f.req": freq, "at": at}, headers=headers, timeout=240)
    gh._salvar_sessao(conta, s)
    if r.status_code != 200:
        if r.status_code in (400, 401, 403):
            gh._cache_tokens.pop(conta, None)
        raise RuntimeError(f"HTTP {r.status_code}")
    return r.text


def _classificar_texto(corpo):
    texto, *_ = gh._parse(corpo)
    texto = texto or ""
    if _RE_LIMITE.search(texto) or _RE_LIMITE.search(corpo):
        raise SemCotaMidia(texto[:150] or "limite")
    if _RE_RECUSA.search(texto):
        raise Recusou(texto[:150])
    raise RuntimeError("sem mídia na resposta: " + texto[:120])


def formato_mais_proximo(aspect):
    proporcoes = {"16:9": 16 / 9, "4:3": 4 / 3, "1:1": 1.0, "3:4": 3 / 4, "9:16": 9 / 16}
    try:
        if isinstance(aspect, (int, float)):
            r = float(aspect)
        else:
            a, b = str(aspect).lower().replace("x", ":").split(":")
            r = float(a) / float(b)
    except Exception:  # noqa: BLE001
        return "9:16"
    return min(proporcoes, key=lambda f: abs(proporcoes[f] - r))


# ─────────────────────── imagem ───────────────────────
def _uma_imagem(conta, prompt, formato, saida):
    s, at, bl, fsid = _sessao(conta)
    freq, jspb = _pedido(prompt, FERRAMENTA_IMAGEM, MODELO_IMAGEM, formato, temporario=True)
    corpo = _stream(conta, s, at, bl, fsid, freq, jspb)
    m = _RE_IMG.search(corpo)
    if not m:
        _classificar_texto(corpo)
    r = s.get(m.group(0) + "=s0", timeout=120)  # =s0 = tamanho cheio (1376x768); sem ele vem 512 px
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image") or len(r.content) < 10_000:
        raise RuntimeError(f"download HTTP {r.status_code} {r.headers.get('content-type')}")
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    if str(saida).lower().endswith(".png"):
        tmp = Path(str(saida) + ".jpg")
        tmp.write_bytes(r.content)
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(tmp), str(saida)], capture_output=True,
                       creationflags=0x08000000, timeout=60)
        tmp.unlink(missing_ok=True)
        if not Path(saida).exists():
            Path(saida).write_bytes(r.content)
    else:
        Path(saida).write_bytes(r.content)
    return len(r.content)


# ─────────────────────── vídeo ───────────────────────
def cota_video(conta):
    """(tem_cota, volta_epoch|None) pela consulta MyzX6c — não gasta nada."""
    s, at, bl, fsid = _sessao(conta)
    t = _batch(s, at, bl, fsid, "MyzX6c", []).replace('\\"', '"')
    voltas, tem = [], True
    for rec, disp, _lim, _uso, volta in _RE_COTA.findall(t):
        if int(rec) in RECURSOS_VIDEO and disp == "false":
            tem = False
            if volta:
                voltas.append(int(volta))
    return tem, (max(voltas) if voltas else None)


def _dimensoes(arq):
    ffprobe = str(Path(FFMPEG).with_name("ffprobe")) if os.sep in FFMPEG else "ffprobe"
    try:
        r = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", str(arq)], capture_output=True, text=True, timeout=30,
                           creationflags=0x08000000)
        w, h = r.stdout.strip().split(",")[:2]
        return int(w), int(h)
    except Exception:  # noqa: BLE001
        return None, None


def _cortar(origem, destino, duracao):
    """Corta no tempo pedido (o Gemini entrega 10 s; o robô do Veo valida ~8 s ±1). Sem reencodar quando der."""
    r = subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(origem), "-t", str(duracao), "-c", "copy",
                        "-movflags", "+faststart", str(destino)], capture_output=True, creationflags=0x08000000,
                       timeout=120)
    if r.returncode != 0 or not Path(destino).exists() or Path(destino).stat().st_size < 100_000:
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(origem), "-t", str(duracao), "-c:v", "libx264",
                        "-crf", "17", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", str(destino)],
                       capture_output=True, creationflags=0x08000000, timeout=300)
    return Path(destino).exists() and Path(destino).stat().st_size > 100_000


def _um_video(conta, prompt, formato, saida, duracao):
    tem, volta = cota_video(conta)
    if not tem:
        e = SemCotaMidia("cota de vídeo esgotada" + (f", volta {datetime.fromtimestamp(volta):%d/%m %H:%M}"
                                                       if volta else ""))
        e.volta = volta
        raise e
    s, at, bl, fsid = _sessao(conta)
    # 13/11: no vídeo o campo de formato sozinho NÃO deixa vertical (chef saiu 1280x720); com "vertical" no texto saiu
    # 720x1280 (tartaruga). Manda os dois.
    texto = prompt
    if formato == "9:16" and not re.search(r"\b(vertical|9:16|portrait|retrato)\b", prompt, re.I):
        texto = f"{prompt}. Vertical 9:16 portrait video."
    freq, jspb = _pedido(texto, FERRAMENTA_VIDEO, MODELO_VIDEO, formato)
    corpo = _stream(conta, s, at, bl, fsid, freq, jspb)
    m = _RE_CID.search(corpo)
    if not ("video_generation" in corpo and m):
        _classificar_texto(corpo)
    cid = m.group(1)
    log.info("vídeo disparado %s conversa %s", conta, cid)
    t0 = time.time()
    t = ""
    try:
        while time.time() - t0 < ESPERA_VIDEO_S:
            time.sleep(10)
            t = _desescapar(_batch(s, at, bl, fsid, "hNvQHb", [cid, 10, None, 1, [0], [4, 12], None, 1],
                                   path=f"/app/{cid[2:]}"))
            mp4 = _RE_MP4.search(t)
            if mp4:
                v = s.get(mp4.group(0), timeout=180)
                if v.status_code != 200 or "video" not in v.headers.get("content-type", "") or len(v.content) < 100_000:
                    raise RuntimeError(f"download HTTP {v.status_code} {v.headers.get('content-type')}")
                Path(saida).parent.mkdir(parents=True, exist_ok=True)
                bruto = Path(str(saida) + ".gemini.mp4")
                bruto.write_bytes(v.content)
                larg, alt = _dimensoes(bruto)
                if formato == "9:16" and larg and alt and larg > alt:
                    bruto.unlink(missing_ok=True)
                    raise RuntimeError(f"veio horizontal ({larg}x{alt}) e pediram 9:16")
                ok = _cortar(bruto, saida, duracao) if duracao else bruto.replace(saida) or True
                bruto.unlink(missing_ok=True)
                if not ok:
                    raise RuntimeError("corte do vídeo falhou")
                gh._salvar_sessao(conta, s)
                return Path(saida).stat().st_size, time.time() - t0
            if _RE_LIMITE.search(t):
                try:
                    _, volta = cota_video(conta)
                except Exception:  # noqa: BLE001
                    volta = None
                e = SemCotaMidia("limite de vídeo atingido na geração")
                e.volta = volta
                raise e
            if _RE_RECUSA.search(t) and "generating your video" not in t:
                raise Recusou("recusado durante a geração")
        # prova do motivo antes de apagar a conversa (o que o Gemini escreveu no turno)
        textos = re.findall(r'\[\\?"rc_[0-9a-f]+\\?",\[\\?"([^"\\]{5,300})', t)
        log.warning("vídeo sem entrega %s %s: %s", conta, cid, " | ".join(textos[:3]) or t[-400:])
        raise RuntimeError(f"vídeo não ficou pronto em {ESPERA_VIDEO_S}s (conversa {cid})")
    finally:
        try:  # não deixa a conversa de geração no histórico da conta
            _batch(s, at, bl, fsid, "GzXR5e", [cid])
        except Exception:  # noqa: BLE001
            pass


# ─────────────────────── laço comum (fila) ───────────────────────
def _gerar(tipo, prompt, saida, formato, conta, executar):
    if not ligado(tipo):
        return False, f"Gemini {tipo} desligado (GEMINI_MIDIA/GEMINI_{tipo.upper()}=0)"
    contas = [conta] if conta else candidatas(tipo)
    if not contas:
        return False, f"nenhuma conta do Gemini pronta para {tipo}"
    ultimo, tentadas = "", 0
    for ap in contas:
        if tentadas >= MAX_CONTAS_POR_PEDIDO:  # no máx. 2 contas de verdade por pedido (regra do IP)
            break
        trava = _trava_da(ap)
        if not trava.acquire(timeout=1 if not conta else 600):
            ultimo = f"{ap} ocupada"
            continue  # ocupada por outro pedido: não conta como tentativa, vai pra próxima livre
        tentadas += 1
        t0 = time.time()
        try:
            n, extra = executar(ap)
            dt = time.time() - t0
            _registrar(ap, tipo, True, segundos=dt)
            log.info("%s OK %s %.0fs %d bytes: %s", tipo, ap, dt, n, prompt[:70])
            return True, f"Gemini {tipo} ({ap}, {dt:.0f}s)"
        except Recusou as e:
            _registrar(ap, tipo, False, f"recusa: {e}")
            log.info("%s recusado %s: %s", tipo, ap, e)
            return False, f"Gemini recusou o prompt: {e}"
        except SemCotaMidia as e:
            espera = (datetime.fromtimestamp(e.volta + 60) - datetime.now()) if e.volta else ESPERA_COTA
            _registrar(ap, tipo, False, f"cota: {e}", espera)
            ultimo = f"{ap}: {e}"
        except CookieMorto as e:
            _registrar(ap, tipo, False, f"cookie: {e}", ESPERA_FALHA)
            ultimo = f"{ap}: cookie morto (zelador renova)"
        except Exception as e:  # noqa: BLE001
            _registrar(ap, tipo, False, str(e), ESPERA_FALHA)
            ultimo = f"{ap}: {str(e)[:120]}"
        finally:
            trava.release()
        log.warning("%s falhou %s: %s", tipo, ap, ultimo)
    return False, ultimo


def gerar_imagem(prompt, saida, formato="16:9", conta=None):
    """1 imagem por HTTP (~12-20 s). (ok, detalhe). Nunca levanta."""
    formato = formato_mais_proximo(formato)
    return _gerar("imagem", prompt, saida, formato, conta, lambda ap: (_uma_imagem(ap, prompt, formato, saida), 0))


def gerar_video(prompt, saida, formato="9:16", conta=None, duracao=8):
    """1 vídeo por HTTP (~1 min), cortado em `duracao` s (None = 10 s inteiro). (ok, detalhe). Nunca levanta."""
    formato = "9:16" if formato_mais_proximo(formato) in ("9:16", "3:4") else "16:9"
    return _gerar("video", prompt, saida, formato, conta, lambda ap: _um_video(ap, prompt, formato, saida, duracao))


def tem_conta_video():
    """Há conta do Gemini pronta para vídeo (cookie vivo e fora de espera)? Só lê arquivos, sem rede.
    Usado pelo robô do Veo para decidir se roda o ciclo quando o Flow inteiro está sem crédito."""
    try:
        return bool(ligado("video") and candidatas("video"))
    except Exception:  # noqa: BLE001
        return False


def estado():
    e = _ler()
    linhas = []
    for ap, m in sorted(e.get("contas", {}).items()):
        for tipo, d in m.items():
            media = (d.get("seg_total", 0) / d["total_ok"]) if d.get("total_ok") else 0
            linhas.append(f"{ap:30} {tipo:7} ok_hoje={d.get('ok_hoje', 0)} falhas={d.get('falhas_hoje', 0)} "
                          f"media={media:.0f}s fora_ate={d.get('fora_ate', '-')} {d.get('ultimo_erro', '')[:50]}")
    fila = {t: candidatas(t)[:5] for t in ("imagem", "video")}
    return "\n".join(linhas or ["(nenhum uso ainda)"]) + f"\npróximas da fila: {fila}"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["imagem", "video", "estado", "tem-video"])
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("saida", nargs="?")
    ap.add_argument("--formato", default="16:9")
    ap.add_argument("--conta")
    ap.add_argument("--duracao", type=float, default=8)
    a = ap.parse_args()
    if a.acao == "estado":
        print(estado())
        return
    if a.acao == "tem-video":
        tem = tem_conta_video()
        print("SIM" if tem else "NAO")
        sys.exit(0 if tem else 1)
    if a.acao == "video":
        ok, det = gerar_video(a.prompt, a.saida, a.formato, a.conta, a.duracao or None)
    else:
        ok, det = gerar_imagem(a.prompt, a.saida, a.formato, a.conta)
    print(("OK: " if ok else "FALHOU: ") + det)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
