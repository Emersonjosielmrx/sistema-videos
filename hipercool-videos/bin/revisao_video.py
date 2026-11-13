# -*- coding: utf-8 -*-
"""revisao_video.py — ANÁLISE do vídeo censurado PRONTO, antes de postar (16/10/2026).

Por quê: em 16/10 o canal pt levou advertência do YouTube ("Nudez e conteúdo sexual", 90 dias) pelo compilado
caps 1-11, que tinha painel sem censura e mosaico no lugar errado. A censura é feita painel a painel
(censura_visual) e ninguém assistia o vídeo final. Esta análise faz o papel de quem assiste:

  1. tira 2 quadros por segundo do arquivo FINAL (o mesmo que vai subir) e descarta os repetidos;
  2. pergunta ao Gemini (visão, proxy), quadro a quadro e em resolução cheia, se aparece mamilo, genitália ou
     nádegas à mostra — sem mosaico ou com mosaico fraco demais (exposto(): 3 opiniões, basta 1 sim). Quadro
     marcado = PROBLEMA, sem segunda conferência: o painel com vazamento pode ficar só 1 s na tela (cap 10
     panel_027) e nos testes ele não marcou nada limpo;
  3. grava o veredito ao lado do vídeo (<video>.revisao.json) com o tamanho e a data do arquivo, e os quadros
     reprovados numa folha (<video>.revisao.jpg) pro dono olhar só o que deu problema.

Desde 16/10 (tarde) só vão ao Gemini os quadros de painel com risco (_com_risco), com o mapa clip->painel do meta
posto no tempo real pelos cortes de cena do próprio vídeo (_alinhar). Sem mapa confiável ou sem a pasta dos
painéis, olha todos os quadros como antes.

O postar_hipercool só posta vídeo com veredito "ok" para AQUELE arquivo (aprovado()). Falha de rede/cota vira
"incompleto" e também não posta: nunca aprova no escuro. Reprovado: a fila põe o painel do trecho em
censura_visual.forcar_fosco() e renderiza de novo (uma vez); se continuar, avisa o dono no Telegram.

Testado em 16/10 em trechos reais: pegou os 4 vazamentos conhecidos (cap 10 aos 158 s e 160-166 s, compilado
caps 1-3 aos 900-911 s, cap 3 hindi aos 33-35 s) e outros 2 que a censura por painel nunca pegaria (cap 3
panel_048 de corpo inteiro com score 0,16; cap 10 aos 32-35 s); 60 s de trecho com mosaico bom passaram.

  python bin/revisao_video.py <video.mp4> [--forcar]   (--forcar: refaz mesmo com veredito gravado)
"""
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

_BIN = Path(__file__).resolve().parent
_TRAVA_MODULO = threading.Lock()
sys.path.insert(0, str(_BIN))
from hp_common import PROJECT_DIR, log  # noqa: E402


def modulo(nome):
    """Módulo DESTE projeto carregado pelo caminho do arquivo. O D:\\postador-de-videos\\bin tem cópias antigas de
    22 módulos com o mesmo nome (claude_client, censura_visual, ...) e o postar_hipercool põe essa pasta na FRENTE
    do sys.path: depois dele, `import claude_client` traz a cópia velha (achado em 16/10 no teste da fila)."""
    chave = f"hipercool_{nome}"
    with _TRAVA_MODULO:  # as 6 threads da análise chamam juntas: sem trava uma pegava o módulo pela metade
        m = sys.modules.get(chave)
        if m is None:
            spec = importlib.util.spec_from_file_location(chave, _BIN / f"{nome}.py")
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            sys.modules[chave] = m  # só depois de carregado inteiro
    return m

VERSAO = 2  # muda quando o critério muda -> veredito antigo deixa de valer
CACHE = PROJECT_DIR / "workspace" / "cache" / "revisao"
PASSO_S = 0.5         # 2 quadros por segundo: com 1/s o cap 10 panel_027 (~1 s na tela) escapava (16/10)
GAP_MAX_S = 3.0       # quadro "repetido" ainda entra se o último analisado tem mais que isso
DIF_MIN = 3.0         # diferença média (0-255, miniatura 48x48) abaixo disso = mesmo quadro
LADO_PX = 1280        # resolução do quadro analisado: em 960 px o mamilo pequeno no canto escapava (16/10)
TRABALHADORES = 6
OPINIOES = 3          # o modelo oscila no mesmo quadro: nádegas nuas sairam "não, não, sim" (16/10); basta 1 sim
MARGEM_S = 0.6        # quadro a menos disso de um trecho com risco também é olhado (transição, corte do mapa)
SCORE_LIMPO = 0.10    # painel abaixo disso no Sightengine, fora da censura e sem nada exposto na visão = limpo
CASADO_MIN = 0.6      # fração dos cortes do mapa achados no vídeo pra confiar no mapa e pular os limpos
PANELS = Path(r"D:\hipercool-materiais\panels")
# Gemini do proxy (os mesmos da localização da censura). Uma pergunta por quadro: o filtro do Google recusa
# qualquer pedido com vários quadros numerados na mesma imagem (testado 16/10).
MODELOS = ["antigravity/gemini-3-flash", "antigravity/gemini-3.5-flash-lite", "antigravity/gemini-3.8-flash-tiered",
           "antigravity/gemini-3.1-flash-lite"]

# Vocabulário de moderação, igual ao do censura_visual. Palavras anatômicas mais diretas, ou um campo de texto
# livre na resposta ("o_que": "<parte exposta>"), fazem o filtro do Google recusar o PEDIDO inteiro (16/10).
_CRITERIO = (
    "Conta como EXPOSTO só se dá pra ver, SEM mosaico/pixelado/borrão por cima: mamilos, genitália ou nádegas "
    "DESCOBERTOS. Também conta como EXPOSTO quando o mosaico/borrão é fraco ou pequeno demais e ainda dá pra "
    "reconhecer o mamilo (a mancha rosada redonda) ou a forma da genitália. NÃO conta: parte bem coberta por "
    "mosaico, pixelado ou borrão forte, roupa, cabelo, mão, braço, sombra, balão ou fora do quadro; decote; seio "
    "de lado sem mamilo; costas nuas; peito de HOMEM (mamilo masculino não conta); personagem vestido(a), mesmo "
    "de roupa justa; roupa íntima; figurinha/meme de desenho sem nudez; corpo sem essas partes à mostra."
)
PROMPT_UM = (
    "Você é um moderador de conteúdo conferindo um quadro da versão censurada de um vídeo de manhwa (personagens "
    "adultos) antes de ir pro YouTube.\n" + _CRITERIO + "\n"
    'Responda só JSON: {"exposto":true|false}'
)


# ─── pergunta ao Gemini ──────────────────────────────────────────────────────
def _jpeg(img):
    """bytes JPEG de um caminho ou dos próprios bytes."""
    return Path(img).read_bytes() if isinstance(img, (str, Path)) else img


def _uma_opiniao(img_bytes, tentativas=3):
    """True/False do modelo, ou None (sem resposta, recusa, JSON quebrado)."""
    claude_client = modulo("claude_client")
    for k in range(tentativas):
        resp = claude_client._post([{"role": "user", "content": [claude_client._img_block(img_bytes),
                                                                 {"type": "text", "text": PROMPT_UM}]}],
                                   max_tokens=80, temperature=0.1, so=MODELOS, timeout=120)
        d = claude_client._extract_json(resp) if resp and "could not be submitted" not in resp else None
        if isinstance(d, dict) and isinstance(d.get("exposto"), bool):
            return d["exposto"]
        time.sleep(2 * (k + 1))
    return None


def exposto(img, vezes=OPINIOES):
    """Tem mamilo/genitália/nádegas à mostra (sem mosaico, ou com mosaico fraco)? True se ALGUMA das `vezes`
    opiniões diz que sim (o modelo oscila no mesmo quadro: a 2ª pega o que a 1ª deixa passar), False se todas
    dizem não, None se nenhuma respondeu. Cache pelo md5 da imagem: rever o mesmo painel/quadro não gasta de novo.
    Usado aqui (quadros do vídeo) e no censura_visual (painel antes e depois do mosaico)."""
    b = _jpeg(img)
    CACHE.mkdir(parents=True, exist_ok=True)
    cf = CACHE / f"{hashlib.md5(b + PROMPT_UM.encode('utf-8')).hexdigest()}_x{vezes}.json"
    try:
        return json.loads(cf.read_text(encoding="utf-8"))["exposto"]
    except (OSError, ValueError, KeyError):
        pass
    votos = []
    for _ in range(vezes):
        v = _uma_opiniao(b)
        if v is not None:
            votos.append(v)
            if v:
                break  # um sim já basta
    res = any(votos) if votos else None
    if res is not None:
        cf.write_text(json.dumps({"exposto": res, "votos": votos}), encoding="utf-8")
    return res


def expostos(imgs, vezes=OPINIOES):
    """{img: True/False/None} em paralelo."""
    imgs = list(imgs)
    with ThreadPoolExecutor(TRABALHADORES) as ex:
        return dict(zip(imgs, ex.map(lambda i: exposto(i, vezes), imgs)))


# ─── quadros ─────────────────────────────────────────────────────────────────
def _ffmpeg():
    return shutil.which("ffmpeg") or "ffmpeg"


def _duracao(mp4):
    r = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(mp4)], capture_output=True, text=True, timeout=60)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _quadros(mp4, tmp):
    """([(t, Path)], cortes) numa leitura só do vídeo. Quadros: ~1 por PASSO_S, t = tempo REAL do quadro (o filtro
    fps entregava o conteúdo até 0,25 s depois do segundo anotado), sem os repetidos, lado maior LADO_PX.
    cortes: segundos das trocas de cena, pra pôr o mapa clip->painel do meta no tempo real (_alinhar)."""
    import cv2
    import numpy as np
    sel = f"select='isnan(prev_selected_t)+gte(t-prev_selected_t,{PASSO_S})'"
    esc = f"scale='if(gt(iw,ih),{LADO_PX},-2)':'if(gt(iw,ih),-2,{LADO_PX})'"
    grafo = (f"[0:v]split=2[a][b];[a]{sel},showinfo@q,{esc}[q];"
             f"[b]scale=270:-2,select='gt(scene,0.30)',showinfo@c[c]")
    r = subprocess.run([_ffmpeg(), "-hide_banner", "-v", "info", "-i", str(mp4), "-filter_complex", grafo,
                        "-map", "[q]", "-fps_mode", "vfr", "-q:v", "2", str(tmp / "q_%05d.jpg"),
                        "-map", "[c]", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    # vídeo sem nenhuma troca de cena (Veo de 1 take): a saída dos cortes fica vazia e o ffmpeg dá erro mesmo com os
    # quadros todos tirados (20/10) — aí vale, com cortes = []
    sem_cortes = "out#1/null" in r.stderr and "Nothing was written" in r.stderr and any(tmp.glob("q_*.jpg"))
    if r.returncode != 0 and not sem_cortes:
        raise RuntimeError(f"ffmpeg dos quadros falhou: {r.stderr[-400:]}")
    tq, cortes = [], []
    for linha in r.stderr.splitlines():
        m = re.search(r"pts_time:\s*([0-9.]+)", linha)
        if m and "showinfo@q" in linha:
            tq.append(float(m.group(1)))
        elif m and "showinfo@c" in linha:
            cortes.append(float(m.group(1)))
    arqs = sorted(tmp.glob("q_*.jpg"))
    if len(tq) != len(arqs):  # não deu pra ler o tempo de cada quadro: conta antiga
        tq = [k * PASSO_S for k in range(len(arqs))]
    out, ultimo, t_ult = [], None, -99.0
    for t, f in zip(tq, arqs):
        im = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
        mini = cv2.resize(im, (48, 48), interpolation=cv2.INTER_AREA).astype(np.float32)
        if ultimo is not None and float(np.abs(mini - ultimo).mean()) < DIF_MIN and t - t_ult < GAP_MAX_S:
            continue
        out.append((t, f))
        ultimo, t_ult = mini, t
    return out, cortes


# ─── qual painel estava na tela ──────────────────────────────────────────────
def _segmentos(meta):
    """[(ini, fim, [painéis])] na linha do tempo do meta. Vertical: clip_paineis + acabamento.fronteiras/duracoes
    (clip sem painel — abertura, meme — fica com []). 16:9 (capNN.json): momentos_tempo, com os vizinhos apagados
    em "tira"/"duo" (foi um vizinho que vazou no compilado caps 1-3, 15:10). [] se o meta não diz."""
    meta = meta or {}
    acab = meta.get("acabamento") or {}
    nomes = meta.get("clip_paineis")
    if nomes:
        return [(a, a + d, [nomes[k]] if k < len(nomes) and nomes[k] else [])
                for k, (a, d) in enumerate(zip(acab.get("fronteiras") or [], acab.get("duracoes") or []))]
    tempos = meta.get("momentos_tempo") or []
    out = []
    for k, (a, b, nome, lay) in enumerate(tempos):
        viz = {"tira": (k - 1, k + 1), "duo": (k - 1,)}.get(lay, ())
        out.append((a, b, [nome] + [tempos[j][2] for j in viz if 0 <= j < len(tempos)]))
    return out


def _alinhar(segs, cortes):
    """(segmentos no tempo REAL do vídeo, quantos inícios casaram com um corte). O meta guarda a duração planejada
    de cada clip, mas clip curto sai mais curto no arquivo: no cap 1 de 16/10 o mapa ficou 2,3 s adiantado no fim e
    a análise forçou fosco em painéis vestidos em vez do que aparecia. Cada início de clip vai pro corte de cena real
    mais perto do esperado (com o desvio acumulado até ali); sem corte perto, segue o desvio anterior."""
    if not segs or not cortes:
        return segs, 0
    inis, desvio, casados = [], 0.0, 0
    for k, (a, _b, _n) in enumerate(segs):
        esperado = a + desvio
        perto = [c for c in cortes if esperado - 0.9 <= c <= esperado + 0.4] if k else []
        if perto:
            c = min(perto, key=lambda c: abs(c - esperado))
            desvio, casados = c - a, casados + 1
        inis.append(a + desvio)
    fim = segs[-1][1] + desvio
    return [(inis[k], inis[k + 1] if k + 1 < len(inis) else fim, segs[k][2]) for k in range(len(segs))], casados


def _paineis_seg(segs, t, tol):
    """Painéis dos segmentos que cobrem o segundo t (± tol, pro quadro colado num corte)."""
    return sorted({n for a, b, ns in segs if a - tol <= t < b + tol for n in ns})


def _pasta_paineis(mp4):
    """Pasta dos painéis pelo caminho do vídeo (.../<obra>/capNN/<idioma>/... ou .../longo/<obra>/capNN.mp4). As
    línguas usam os mesmos painéis e a mesma censura do pt."""
    p = Path(mp4)
    m = re.search(r"[\\/]longo[\\/]([^\\/]+)[\\/]cap(\d+)\.mp4$", str(p), re.I)
    if m:
        obra, n = m.group(1), int(m.group(2))
    else:
        k = next((i for i in range(1, len(p.parts)) if re.fullmatch(r"cap\d+", p.parts[i], re.I)), None)
        if k is None:
            return None
        obra, n = p.parts[k - 1], int(p.parts[k][3:])
    d = PANELS / f"{obra}-cap{n:02d}"
    return d if d.is_dir() else None


def _com_risco(meta, pasta, nomes):
    """Painéis que precisam ser olhados quadro a quadro. Limpo = score do Sightengine (cache) abaixo de SCORE_LIMPO,
    fora da lista da censura e dos forçados, e a MESMA pergunta desta análise, feita na imagem original, diz que
    não há nada exposto (a censura já perguntou isso de todo painel de score baixo: vem do cache). Recorte, zoom e
    parallax de um painel limpo não mostram o que ele não tem. Sem score ou sem resposta = com risco."""
    cv = modulo("censura_visual")
    c = meta.get("censura") or {}
    lista = {x.get("painel") for x in (c.get("paineis") or []) + (c.get("conferir") or [])}
    risco, perguntar = set(), []
    for n in nomes:
        p = pasta / n
        if n in lista or not p.exists():
            risco.add(n)
            continue
        try:
            sf = cv.CACHE_DIR / f"{hashlib.md5(p.read_bytes()).hexdigest()}.json"
            s = cv._score_ponderado(json.loads(sf.read_text(encoding="utf-8")).get("nudity", {}))
        except (OSError, ValueError):
            s = None
        if s is None or s >= SCORE_LIMPO or cv.forcado(p):
            risco.add(n)
        else:
            perguntar.append(p)
    for p, v in expostos(perguntar).items():
        if v is not False:
            risco.add(Path(p).name)
    return risco


# ─── veredito ────────────────────────────────────────────────────────────────
def _arq_veredito(mp4):
    mp4 = Path(mp4)
    return mp4.with_name(mp4.stem + ".revisao.json")


def _assinatura(mp4):
    try:
        st = Path(mp4).stat()
        return {"tamanho": st.st_size, "mtime": round(st.st_mtime, 1)}
    except FileNotFoundError:
        return None  # arquivo foi movido para o Drive ou apagado


def ler(mp4):
    try:
        return json.loads(_arq_veredito(mp4).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def aprovado(mp4):
    """(True, "") se o veredito gravado é "ok" deste MESMO arquivo e desta versão do critério; senão (False, motivo)."""
    v = ler(mp4)
    if not v:
        return False, "sem análise do vídeo pronto"
    if v.get("versao") != VERSAO:
        return False, "análise feita com critério antigo"
    assinatura_atual = _assinatura(mp4)
    if assinatura_atual is None:
        # arquivo não existe mais (movido pro Drive após backup) — aceita a análise gravada
        return v.get("status") == "ok", f"arquivo no Drive, análise: {v.get('status', 'desconhecido')}"
    if {k: v.get(k) for k in ("tamanho", "mtime")} != assinatura_atual:
        return False, "o arquivo mudou depois da análise"
    if v.get("status") != "ok":
        n = len(v.get("problemas") or [])
        return False, f"análise {v.get('status')}" + (f": {n} trecho(s) com nudez sem censura" if n else "")
    return True, ""


def revisar(mp4, meta=None, forcar=False):
    """Analisa o vídeo e grava <video>.revisao.json. Devolve o veredito (dict)."""
    mp4 = Path(mp4)
    if not forcar and aprovado(mp4)[0]:
        return ler(mp4)
    if meta is None:  # vertical: <video>.meta.json; capítulo do 16:9: capNN.json
        for mf in (mp4.with_suffix(".meta.json"), mp4.with_suffix(".json")):
            try:
                meta = json.loads(mf.read_text(encoding="utf-8"))
                break
            except (OSError, ValueError):
                continue
    t0 = time.time()
    tmp = Path(tempfile.mkdtemp(prefix="revisao_"))
    try:
        qs, cortes = _quadros(mp4, tmp)
        segs, casados = _alinhar(_segmentos(meta), cortes)
        confiavel = bool(segs) and casados >= CASADO_MIN * (len(segs) - 1)
        pasta = _pasta_paineis(mp4)
        modo, risco, alvo = "inteiro", set(), qs
        if confiavel and pasta:
            # 16/10: olhar os 727 quadros do cap 1 levava 18 min; os de painel limpo não podem mostrar nudez
            risco = _com_risco(meta or {}, pasta, sorted({n for _a, _b, ns in segs for n in ns}))
            olhar = [(a - MARGEM_S, b + MARGEM_S) for a, b, ns in segs if not ns or set(ns) & risco]
            fim_mapa = segs[-1][1]
            alvo = [(t, f) for t, f in qs if t >= fim_mapa or any(a <= t <= b for a, b in olhar)]
            modo = "filtrado"
        log(f"  revisão: {mp4.name} — {len(alvo)} de {len(qs)} quadros ({modo}; {len(risco)} painéis com risco; "
            f"mapa casado em {casados}/{max(len(segs) - 1, 0)} cortes)")
        votos = expostos([f for _t, f in alvo])
        sem_resposta = [t for t, f in alvo if votos[f] is None]
        problemas = []
        pasta_q = mp4.with_name(mp4.stem + ".revisao")
        if pasta_q.exists():
            shutil.rmtree(pasta_q, ignore_errors=True)  # quadros de uma análise anterior deste arquivo
        for t, f in alvo:
            if not votos[f]:
                continue
            pasta_q.mkdir(exist_ok=True)
            dest = pasta_q / f"{int(t // 60):02d}m{t % 60:04.1f}s.jpg"
            shutil.copy2(f, dest)
            problemas.append({"t": round(t, 2), "paineis": _paineis_seg(segs, t, 0.12 if confiavel else 1.0),
                              "quadro": str(dest)})
        status = "reprovado" if problemas else ("incompleto" if sem_resposta else "ok")
        v = {"versao": VERSAO, "arquivo": mp4.name, **_assinatura(mp4), "status": status, "modo": modo,
             "quadros": len(alvo), "quadros_total": len(qs), "paineis_risco": sorted(risco),
             "mapa_casado": [casados, max(len(segs) - 1, 0)], "problemas": problemas,
             "paineis": sorted({n for p in problemas for n in p["paineis"]}),
             "sem_resposta_em_s": sem_resposta[:50], "duracao_s": round(_duracao(mp4), 1),
             "levou_s": round(time.time() - t0), "em": datetime.now().isoformat(timespec="seconds")}
        if problemas:
            _folha_problemas(mp4, problemas)
        _arq_veredito(mp4).write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"  revisão: {status.upper()} — {len(problemas)} quadro(s) com nudez, {len(sem_resposta)} sem resposta "
            f"({v['levou_s']} s)")
        return v
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _folha_problemas(mp4, problemas):
    """<video>.revisao.jpg: os quadros reprovados lado a lado, com o segundo de cada um (pro dono olhar)."""
    import cv2
    import numpy as np
    ims = []
    for p in problemas[:12]:
        im = cv2.imread(p["quadro"])
        if im is None:
            continue
        h, w = im.shape[:2]
        im = cv2.resize(im, (int(w * 640 / h), 640))
        cv2.rectangle(im, (0, 0), (im.shape[1], 44), (0, 0, 0), -1)
        cv2.putText(im, f"{int(p['t'] // 60)}:{p['t'] % 60:04.1f} {' '.join(p.get('paineis') or [])}", (8, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        ims.append(im)
    if ims:
        cv2.imwrite(str(mp4.with_name(mp4.stem + ".revisao.jpg")), np.hstack(ims))


def liberar(mp4, quem="dono"):
    """O dono olhou os quadros reprovados (<video>.revisao.jpg) e decidiu que é engano: grava veredito "ok" pra
    este arquivo, guardando o que a análise tinha achado."""
    v = ler(mp4) or {}
    v.update({"versao": VERSAO, "arquivo": Path(mp4).name, **_assinatura(mp4), "status": "ok",
              "liberado_por": quem, "liberado_em": datetime.now().isoformat(timespec="seconds"),
              "status_da_analise": v.get("status")})
    _arq_veredito(mp4).write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    return v


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="análise do vídeo censurado pronto (nudez sem censura)")
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--forcar", action="store_true", help="refaz mesmo com veredito gravado")
    ap.add_argument("--liberar", action="store_true", help="o dono conferiu os quadros e libera (engano da análise)")
    a = ap.parse_args()
    if a.liberar:
        for v in a.videos:
            r = liberar(v)
            print(json.dumps({k: r[k] for k in ("arquivo", "status", "status_da_analise")}, ensure_ascii=False))
        return
    for v in a.videos:
        r = revisar(v, forcar=a.forcar)
        print(json.dumps({"arquivo": r["arquivo"], "status": r["status"], "quadros": r["quadros"],
                          "segundos": [p["t"] for p in r["problemas"]], "paineis": r["paineis"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
