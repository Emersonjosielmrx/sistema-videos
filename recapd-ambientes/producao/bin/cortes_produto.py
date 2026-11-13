# -*- coding: utf-8 -*-
"""cortes_produto.py — trecho curto de um produto NOSSO no meio do Short de parceiro (dono 26/10/2026: "inserir
pequenos cortes dos meus produtos de IA nos vídeos... em lugares estratégicos que não atrapalhem, nem no final nem no
começo, e o próprio narrador pode fazer uma piada positiva com o produto; testar se não cai a audiência; muito
cuidado porque já tivemos banimento").

Como: 3 s do meio de uma cena de demonstração de um Reel do produto (produto_fila\\<conta>\\_postados; tipo
"conversa"/"veo"; sem cena marcada = 40-55% do Reel, longe da pergunta e do cartão final), sem o áudio dele, entram num
corte de cena a 55-65% do Short, com 1 frase positiva do narrador (só o NOME do produto) e o nome na tela.
SEGURANÇA (o banimento de 16/10 foi número de WhatsApp na tela): a fala passa por regex (sem número/URL/@/telefone) e
os quadros do trecho pela checagem de contato do comercial_veo; qualquer dúvida = o Short segue SEM produto.
Só nas cópias de TikTok/Insta, montado na hora (regra "YouTube NUNCA" do comercial_veo) — teste A/B (TESTES.md).

    python cortes_produto.py testar <pasta do Short> [produto_id]   # monta em D:\\hipercool-materiais\\cortes_teste_produto
"""
import json
import logging
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
FILA = Path(r"D:\video-fila\produto_fila")
PRODUTOS = Path(r"D:\veo\beta\pos_producao\assets\produtos.json")
SAIDA_TESTE = Path(r"D:\hipercool-materiais\cortes_teste_produto")
FONTE = Path(r"D:\hipercool-materiais\assets\fonts")
CLIPE_S = 3.0
FALA_PROIBIDA = re.compile(r"\d|https?:|www\.|\.com|@|whats\s*app|zap|telefone|ligue|link|direct|dm\b|cupom|grátis|"
                           r"desconto|promo", re.I)


def _probe(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", str(mp4)], capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    s = (d.get("streams") or [{}])[0]
    return int(s.get("width", 0)), int(s.get("height", 0)), float((d.get("format") or {}).get("duration", 0))


def clipes():
    """[(mp4, ini, fim, produto_id)] de demonstração dos Reels de produto já postados."""
    out = []
    for js in FILA.glob("*/_postados/*.json"):
        mp4 = js.with_suffix(".mp4")
        if not mp4.exists():
            continue
        try:
            m = json.loads(js.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        cenas = [c for c in m.get("cenas") or [] if c.get("tipo") in ("conversa", "veo")
                 and float(c.get("fim", 0)) - float(c.get("ini", 0)) >= CLIPE_S + 0.5]
        if cenas:
            c = cenas[0]
            meio = (float(c["ini"]) + float(c["fim"])) / 2
        else:
            dur = float(m.get("duracao_s") or _probe(mp4)[2] or 0)
            if dur < 12:
                continue
            meio = dur * 0.475
        out.append((mp4, round(meio - CLIPE_S / 2, 2), round(meio + CLIPE_S / 2, 2), m.get("produto")))
    return out


def _produto(pid):
    for p in json.loads(PRODUTOS.read_text(encoding="utf-8")).get("produtos", []):
        if p.get("id") == pid:
            return p
    return None


def fala(titulo_short, produto):
    """1 frase curta e positiva do narrador ligando a história ao produto (só o nome). None se não passar no filtro."""
    import claude_client
    pedido = (f"Um Short de recap tem o título: \"{titulo_short}\". No meio dele, por 3 segundos, aparece o nosso "
              f"produto \"{produto['nome']}\" ({produto.get('cta_curto') or produto.get('descricao', '')}).\n"
              "Escreva UMA frase falada do narrador (máx. 7 palavras, português do Brasil, tom de piada leve e "
              "POSITIVA) ligando o momento da história ao produto, citando só o NOME do produto. Proibido: número, "
              "preço, link, @, telefone, WhatsApp, 'link na bio', promessa de resultado, desconto. Responda só a frase.")
    for _ in range(2):
        try:
            bruto = claude_client.generate_text(pedido) or ""
        except Exception as e:  # noqa: BLE001 — IA fora: tenta de novo / sem fala, nunca derruba o produto
            logging.info(f"[produto] fala: IA falhou ({type(e).__name__}) — tenta de novo")
            continue
        # 13/11: resposta vazia derrubava aqui ([0] de lista vazia: 101 "IndexError" no tiktok_auto.log) e o produto
        # inteiro saía do Short sem a 2ª tentativa. Agora: 1ª linha não vazia; nenhuma = tenta de novo.
        t = next((x.strip().strip('"').strip() for x in bruto.splitlines() if x.strip().strip('"').strip()), "")
        if t and len(t.split()) <= 11 and produto["nome"].split()[0].lower() in t.lower() and not FALA_PROIBIDA.search(t):
            return t
        logging.info(f"[produto] fala recusada pelo filtro: {t!r}")
    return None


def _corte(mp4, dur):
    """Corte de cena entre 55% e 65% do Short (mais perto de 60%); sem corte = 60%."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{dur * 0.55:.2f}", "-t", f"{dur * 0.10:.2f}", "-i", str(mp4),
                        "-vf", "select='gt(scene,0.30)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    ts = [dur * 0.55 + float(m) for m in re.findall(r"pts_time:([\d.]+)", r.stderr or "")]
    return min(ts, key=lambda t: abs(t - dur * 0.6)) if ts else dur * 0.6


def _narrador(short_mp4, origem=None):
    """(narrador clonado, voz base) do Short, do postar.json ao lado do vídeo (ou da pasta de origem)."""
    for pasta in (Path(short_mp4).parent, Path(origem).parent if origem else None):
        try:
            p = json.loads((pasta / "postar.json").read_text(encoding="utf-8"))
            if p.get("narrador"):
                return p["narrador"], p.get("voz_base") or "francisca"
        except (OSError, ValueError, TypeError):
            continue
    return None, None


def _falar(frase, wav, narrador, base, tmp, log):
    """A frase na voz do NARRADOR CLONADO do Short (mesma do vídeo, sem a abertura do personagem); sem narrador ou
    falhou = Francisca do edge (base do clone)."""
    import os
    # 26/10: o clone na hora da POSTAGEM travou >10 min carregando o modelo no PC1 — só com CORTES_PRODUTO_CLONE=1
    if narrador and os.environ.get("CORTES_PRODUTO_CLONE") == "1":
        antes = {k: os.environ.get(k) for k in ("VOZ_CLONADA", "VOZ_CLONADA_BASE", "VOZ_CLONADA_VERSAO")}
        try:
            os.environ.update(VOZ_CLONADA=narrador, VOZ_CLONADA_BASE=base, VOZ_CLONADA_VERSAO="2")
            import anime_tts
            d = tmp / "clone"
            anime_tts.preparar_clone([frase], d, [], abertura=False)
            if (d / "audio_0.wav").exists():
                import shutil
                shutil.copy2(d / "audio_0.wav", wav)
                return True
        except Exception as e:  # noqa: BLE001
            log(f"  produto: voz clonada ({narrador}) falhou ({type(e).__name__}: {str(e)[:100]}) — Francisca")
        finally:
            for k, v in antes.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    import edge_tts_engine
    return edge_tts_engine.speak(frase, voice="pt-BR-FranciscaNeural", out_wav=str(wav), rate="+12%")


def montar(short_mp4, saida, produto_id=None, titulo="", log=print, origem=None):
    """Monta o Short com o produto no meio. Devolve {"arquivo", "produto", "fala", "em_s", "voz"} ou None."""
    cs = clipes()
    if produto_id:
        cs = [c for c in cs if c[3] == produto_id]
    if not cs:
        log("  produto: nenhum Reel de produto com trecho de demonstração")
        return None
    mp4_p, ini, fim, pid = random.choice(cs)
    produto = _produto(pid)
    if not produto:
        return None
    W, H, dur = _probe(short_mp4)
    t = _corte(short_mp4, dur)
    tmp = Path(tempfile.mkdtemp(prefix="cortes_produto_"))
    voz = tmp / "fala.wav"
    narrador, base = _narrador(short_mp4, origem)
    frase = None
    for _ in range(3):  # dono: "poucos segundos num vídeo de 1 minuto a pessoa pode parar o vídeo" -> fala <= 3,8 s
        f = fala(titulo, produto)
        if f and _falar(f, voz, narrador, base, tmp, log):
            adur = _probe_audio(voz)
            if adur <= 3.8:
                frase = f
                break
            log(f"  produto: fala de {adur:.1f}s passa de 3,8 s — outra")
    if not frase:
        log("  produto: sem fala curta e segura — segue sem")
        return None
    vdur = max(CLIPE_S, adur + 0.3)
    fonte = next(FONTE.glob("*Bold*.ttf"), None) or next(FONTE.glob("*.ttf"), None)
    ff = str(fonte).replace("\\", "/").replace(":", "\\:") if fonte else ""
    # o Reel tem legenda própria (da narração DELE): barra escura por cima da faixa dela com a frase do NOSSO narrador
    pal = re.sub(r"['%:\\]", "", frase).split()
    meio = (len(pal) + 1) // 2
    l1, l2 = " ".join(pal[:meio]), " ".join(pal[meio:])
    fs = int(H * 0.034)
    clip = tmp / "clip.mp4"
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
          f"drawbox=x=0:y=ih*0.655:w=iw:h=ih*0.16:color=0x14232e@1:t=fill,"
          f"drawtext=fontfile='{ff}':text='{l1}':fontsize={fs}:fontcolor=white:borderw=4:bordercolor=black:"
          f"x=(w-text_w)/2:y=h*0.675,"
          f"drawtext=fontfile='{ff}':text='{l2}':fontsize={fs}:fontcolor=0xFFD400:borderw=4:bordercolor=black:"
          f"x=(w-text_w)/2:y=h*0.675+{int(fs * 1.25)}")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(ini), "-t", f"{vdur:.2f}",
                    "-i", str(mp4_p), "-i", str(voz), "-vf", vf, "-map", "0:v", "-map", "1:a", "-af",
                    f"apad,atrim=0:{vdur:.2f},aresample=44100", "-ac", "2", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "20", "-c:a", "aac", "-shortest", str(clip)], check=True)
    import comercial_veo_seguro as cvs  # checagem de contato (mesma pergunta do comercial_veo)
    bom, motivo = cvs.seguro(clip)
    if not bom:
        log(f"  produto DESCARTADO pela checagem de contato ({motivo}) — segue sem")
        return None
    fc = (f"[0:v]trim=0:{t:.2f},setpts=PTS-STARTPTS,fps=30,setsar=1[a];[0:a]atrim=0:{t:.2f},asetpts=PTS-STARTPTS,"
          f"aresample=44100[aa];[1:v]setpts=PTS-STARTPTS,fps=30,setsar=1[p];[1:a]asetpts=PTS-STARTPTS[pa];"
          f"[0:v]trim={t:.2f},setpts=PTS-STARTPTS,fps=30,setsar=1[b];[0:a]atrim={t:.2f},asetpts=PTS-STARTPTS,"
          f"aresample=44100[ba];[a][aa][p][pa][b][ba]concat=n=3:v=1:a=1[v][au]")
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(short_mp4), "-i", str(clip),
                    "-filter_complex", fc, "-map", "[v]", "-map", "[au]", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "20", "-c:a", "aac", "-movflags", "+faststart", str(saida)], check=True)
    log(f"  produto: {pid} aos {t:.1f}s ({vdur:.1f}s): «{frase}»")
    return {"arquivo": str(saida), "produto": pid, "fala": frase, "em_s": round(t, 2), "voz": narrador or "francisca"}


def _probe_audio(wav):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                       capture_output=True, text=True)
    return float((r.stdout or "0").strip() or 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(sys.argv) >= 4 and sys.argv[1] == "reuso":  # o postador chama: reuso <entrada.mp4> <saida.mp4> [título]
        r = montar(Path(sys.argv[2]), Path(sys.argv[3]), None, sys.argv[4] if len(sys.argv) > 4 else "",
                   log=lambda m: print(m, file=sys.stderr), origem=sys.argv[5] if len(sys.argv) > 5 else None)
        print("PRODUTO: " + json.dumps(r, ensure_ascii=False))
    elif len(sys.argv) >= 3 and sys.argv[1] == "testar":
        pasta = Path(r"D:\hipercool-materiais\animes recap\shorts") / sys.argv[2]
        try:
            tit = json.loads((pasta / "postar.json").read_text(encoding="utf-8")).get("titulo", "")
        except (OSError, ValueError):
            tit = ""
        r = montar(pasta / "video.mp4", SAIDA_TESTE / f"{sys.argv[2]}__produto.mp4",
                   sys.argv[3] if len(sys.argv) > 3 else None, tit)
        print(json.dumps(r, ensure_ascii=False))
