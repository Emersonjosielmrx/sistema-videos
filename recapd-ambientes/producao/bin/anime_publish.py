#!/usr/bin/env python
"""anime_publish.py — centraliza o vídeo final em D:\\hipercool-materiais\\animes recap\\
e gera metadata viral (título, descrição, tags, capa) automaticamente.

Uso:
  python anime_publish.py --video final_anime_deitado.mp4 --anime "Sem Talento Mágico" \\
                          --cap 1 --formato deitado --shorts auto

Estrutura de saída:
  D:\\hipercool-materiais\\animes recap\\
    shorts\\<slug>_<cap>_<formato>_<YYYYMMDD>/
      video.mp4
      capa.jpg
      metadata.json
    videos laterais\\<slug>_<cap>_<YYYYMMDD>/
      video.mp4
      capa.jpg
      metadata.json

metadata.json schema:
{
  "slug": "sem-talento-magico-cap1",
  "titulo": "...",           # até 100 chars, viral
  "descricao": "...",        # até 5000 chars
  "tags": ["tag1", ...],     # 15-30 tags virais
  "hashtags": ["#...", ...], # 5-10 hashtags curtas
  "capa_conceito": "...",    # prompt pra gerar capa
  "thumb_texto": "...",      # texto curto pra thumbnail (2-4 palavras)
  "ctas": ["inscreva-se", ...],
  "youtube": {
    "category": "Entertainment",
    "made_for_kids": false,
    "language": "pt-BR",
    "publish_at": null,
    "privacy": "private"
  },
  "video": {
    "duration_s": 1072.3,
    "resolution": "1280x720",
    "size_mb": 156.5,
    "source_url": "https://...",
    "anime": "Sem Talento Mágico",
    "capitulo": 1
  },
  "created_at": "2026-07-26T12:00:00"
}
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import claude_client

try:
    import capa_ia_anime
except ImportError:
    capa_ia_anime = None

try:
    import seo_generator  # §1 do MELHORIAS: título/descrição/tags sem o nome da obra + Thompson de estilo
except ImportError:
    seo_generator = None

CENTRAL = Path(r"D:\hipercool-materiais")
ANIMES_RECAP = CENTRAL / "animes recap"

# Slugify aceita só letras/números/hífens
def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s[:80] or "video"


def probe_video(path):
    """Retorna dict com duration_s, resolution, size_mb, codec."""
    p = Path(path)
    out = {
        "path": str(p),
        "size_mb": round(p.stat().st_size / 1_048_576, 2),
    }
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration:stream=codec_name,width,height,r_frame_rate",
             "-of", "json", str(p)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60,
        )
        j = json.loads(r.stdout)
        out["duration_s"] = round(float(j["format"]["duration"]), 2)
        v = next((s for s in j["streams"] if s.get("codec_name") == "h264"), j["streams"][0])
        out["resolution"] = f"{v['width']}x{v['height']}"
        out["fps"] = v.get("r_frame_rate", "0/0")
    except Exception as e:
        print(f"[probe] falhou: {e}")
    return out


def extract_thumb(video, thumb_png, t_s=None):
    """Extrai 1 frame do vídeo pra servir de base da capa."""
    if t_s is None:
        # Default: 1/3 do vídeo (evita tela preta do início)
        try:
            d = probe_video(video)["duration_s"]
            t_s = d / 3 if d > 30 else d / 2
        except Exception:
            t_s = 5.0
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(t_s), "-i", str(video),
             "-frames:v", "1", "-q:v", "2", str(thumb_png)],
            check=True, capture_output=True, timeout=60,
        )
        return True
    except Exception as e:
        print(f"[thumb] falhou: {e}")
        return False


def generate_metadata(anime, capitulo, formato, video_info, roteiro_path=None, roteiro_txt=""):
    """Gera metadata viral via Gemini (mesma base URL/api key do claude_client)."""
    prompt = f"""Você é especialista em YouTube BR para canal de RECAP DE ANIME em português brasileiro.

Gere METADATA VIRAL para o vídeo:
- Anime: {anime}
- Capítulo: {capitulo}
- Formato: {formato}  (deitado = 16:9 principal, shorts = 9:16 vertical)
- Duração: {video_info.get('duration_s', '?')}s
- Resolução: {video_info.get('resolution', '?')}

REGRAS ABSOLUTAS (NUNCA violar):
1. TUDO em PORTUGUÊS BRASILEIRO. Título, descrição, tags — TUDO PT-BR. JAMAIS inglês.
2. **NUNCA** usar o nome real do anime/manhwa no título nem nas tags principais. Isso viola direitos autorais e causa strike. Use descrições genéricas do enredo (ex: "Ele renasceu com poderes divinos", "Órfão que virou o mais forte", "Herói rejeitado surpreende todos"). O nome do anime pode aparecer SOMENTE na descrição (1x) e em hashtags secundárias (abreviado/genérico).
3. TÍTULO: até 100 chars. CLICÁVEL e VIRAL. Use emojis (1-3). Pattern: [EMOJI] [GANCHO DRAMÁTICO EM PT-BR] + [CURIOSIDADE]. Descreva o ENREDO, não o anime. Ex: "⚡ Ele Perdeu TUDO e Renasceu Como o Ser Mais Forte do Mundo!"
4. DESCRIÇÃO: 800-2000 chars EM PT-BR. Estrutura: gancho (1 linha), sinopse curta (2-3 parágrafos com spoilers leves), CTA (inscreva-se/sino), hashtags.
5. TAGS: 15-25 tags EM PT-BR. Misture: gênero (isekai/magia/ação), "recap anime pt-br", "anime recap português", "resumo anime", tags de tendência. NÃO usar o nome do anime como tag principal.
6. HASHTAGS: 5-7 curtas e genéricas (#anime #recap #isekai #magia #ação etc). NÃO incluir o nome do anime.
7. CAPA_CONCEITO: prompt em inglês pra gerar thumbnail viral. Mencione: personagem genérico, pose épica, fundo dramático. NÃO mencionar o nome do anime.
8. THUMB_TEXTO: 2-4 palavras MAIÚSCULAS em PT-BR pra estampar na thumbnail. Máximo 30 chars.
9. CTAS: 3 calls-to-action curtos em PT-BR.

RETORNE JSON PURO (sem markdown) com as chaves: titulo, descricao, tags (array), hashtags (array), capa_conceito, thumb_texto, ctas (array)."""

    # 14/11 (revisão dos Shorts do dia): este reserva escrevia SEMPRE como recap de anime — um dorama sobre uma menina
    # e a mãe saiu "⚡ Ele Foi Traído e Acabou Despertando o Poder Mais Apelado do Mundo!" (20 Shorts desde 06/11,
    # vários postados). Com o roteiro em mãos, o texto sai do QUE O VÍDEO CONTA, seja qual for o assunto.
    # METADATA_RESERVA_ANTIGA=1 volta ao prompt de anime.
    rot = (roteiro_txt or "").strip()
    if rot and os.environ.get("METADATA_RESERVA_ANTIGA") != "1":
        prompt = (
            "Você escreve título e descrição de YouTube Shorts em português do Brasil.\n\n"
            "ROTEIRO NARRADO DO VÍDEO (é a única fonte: não invente nada que não esteja aqui):\n"
            f"<<<\n{rot[:2500]}\n>>>\n\n"
            "REGRAS:\n"
            "1. Tudo em português do Brasil.\n"
            "2. O título descreve o que ACONTECE neste roteiro (quem, o quê), cria curiosidade e NÃO conta o final. "
            "Até 90 caracteres, 2 ou 3 palavras-chave em MAIÚSCULAS, no máximo 1 emoji no fim.\n"
            "3. Confirme no roteiro o gênero de quem age antes de usar ELE/ELA; na dúvida, sujeito neutro.\n"
            "4. Proibido clichê que não esteja no roteiro (traição, renascer, poder apelado, isekai, capítulo). Nunca "
            "cite nome de obra, canal ou criador.\n"
            "5. Descrição: 2 a 4 frases sobre o que o vídeo mostra + 1 pergunta pro público. Tags: 10 a 15, do assunto "
            "real.\n"
            "6. thumb_texto: 2 a 4 palavras MAIÚSCULAS do assunto real. capa_conceito: 1 frase em inglês da cena "
            "principal.\n\n"
            "RETORNE JSON PURO com as chaves: titulo, descricao, tags (array), hashtags (array), capa_conceito, "
            "thumb_texto, ctas (array).")

    if not claude_client.is_available():
        print("[metadata] claude_client indisponível — usando placeholder")
        return _placeholder_meta(anime, capitulo, formato, video_info, rot)

    resp = claude_client.generate_text(prompt, max_tokens=2000, temperature=0.7)
    if not resp:
        return _placeholder_meta(anime, capitulo, formato, video_info, rot)

    # Limpa blocos markdown ```json ... ```
    txt = resp.strip()
    txt = re.sub(r"^```(?:json)?\s*", "", txt)
    txt = re.sub(r"\s*```$", "", txt)
    # Extrai primeiro bloco {...}
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    if not m:
        print("[metadata] resposta sem JSON válido, usando placeholder")
        return _placeholder_meta(anime, capitulo, formato, video_info, rot)
    try:
        return json.loads(m.group(0))
    except Exception as e:
        print(f"[metadata] JSON parse falhou: {e}")
        return _placeholder_meta(anime, capitulo, formato, video_info, rot)


def _placeholder_meta(anime, cap, formato, video_info, roteiro_txt=""):
    # 14/11: sem IA nenhuma, o título vem da 1ª frase do roteiro (o gancho do próprio vídeo), nunca do texto fixo de
    # anime abaixo — que só fica pra quando não há roteiro.
    rot = " ".join((roteiro_txt or "").split())
    if rot and os.environ.get("METADATA_RESERVA_ANTIGA") != "1":
        frase = re.split(r"(?<=[.!?…])\s", rot)[0].strip().rstrip(".")
        if len(frase) > 88:
            frase = frase[:88].rsplit(" ", 1)[0] + "…"
        resumo = rot[:400].rsplit(" ", 1)[0]
        return {"titulo": frase, "descricao": resumo + "…\n\nO que você achou? Comenta aí 👇", "tags": [],
                "hashtags": [], "capa_conceito": "", "thumb_texto": "", "ctas": []}
    return {
        "titulo": f"⚡ Ele Perdeu TUDO e Renasceu no Mundo Mais Perigoso! Capítulo {cap} COMPLETO",
        "descricao": f"Recap completo do capítulo {cap}.\n\n"
                     f"▶ Sinopse, lutas, magia e revelações em um único vídeo.\n\n"
                     f"🔔 Inscreva-se e ative o sino para não perder os próximos!\n\n"
                     f"#anime #recap #isekai #ação",
        "tags": ["recap anime", "anime recap portugues", "anime pt-br",
                 "resumo anime", f"capitulo {cap}", "recap completo",
                 "anime isekai", "anime ação", "anime magia"],
        "hashtags": ["#anime", "#recap", "#isekai", "#ação", "#magia"],
        "capa_conceito": f"Epic anime character chapter {cap}, dramatic pose, dark background, magical effects",
        "thumb_texto": f"CAP {cap} COMPLETO",
        "ctas": ["Inscreva-se no canal!", "Ative o sininho!", "Comente o que achou!"],
    }


_IDIOMA_NOME = {"hi": "hindi", "id": "indonésio", "it": "italiano", "ru": "russo", "th": "tailandês",
                "vi": "vietnamita", "en": "inglês", "fr": "francês"}
_SEM_TEXTO_CAPA = {"hi", "th", "ru", "vi"}


# 22/10 (vigia 8e7f1f, portado de D:\manhwa-react\mr\capa.py GENRE_COLORS/_tratamento): 3 tratamentos da
# MESMA capa, sem gerar imagem nova. A=controle, B=gradiente na cor do gênero, C=escurecida da esquerda.
_CAPA_CORES = {
    "terror": [(20, 0, 0, 220), (80, 0, 0, 200)], "romance": [(150, 0, 80, 200), (80, 0, 50, 220)],
    "misterio": [(0, 20, 50, 220), (0, 50, 80, 200)], "superacao": [(255, 180, 0, 200), (255, 80, 0, 220)],
    "fantasia": [(30, 0, 80, 200), (80, 0, 150, 220)], "comedia": [(0, 100, 0, 180), (0, 60, 0, 200)],
    "drama": [(30, 30, 30, 220), (60, 40, 20, 200)],
}
_CAPA_GENEROS = [
    ("terror", ("terror", "horror", "zumbi", "assombra")),
    ("romance", ("romance", "amor", "casal", "namorad", "casamento", "beijo", "harem", "harém")),
    ("comedia", ("comedia", "comédia", "engraçad", "humor")),
    ("misterio", ("mistério", "misterio", "segredo", "investiga", "detetive")),
    ("superacao", ("superação", "superacao", "mais fraco", "vingança", "renasceu", "humilhad", "rank")),
    ("fantasia", ("fantasia", "magia", "mago", "reencarn", "isekai", "demônio", "demonio", "dragão", "dragao",
                  "sistema", "masmorra", "dungeon", "cavaleiro")),
]


def _tratar_capa(capa_jpg, semente, *textos):
    """Aplica A/B/C NA PRÓPRIA capa e devolve a variante usada. Escolha: Thompson no placar comum
    (capas_variante, alimentado pelo medidor de 48 h) quando já há amostra; senão rodízio determinístico
    (md5 da semente) — o funil explora no começo e usa mais o que rende (dono, 22/10)."""
    # 01/11 dona: "SEMPRE COLORIDAS E NÃO DARK" — a C escurecia até 94% de preto e a B tingia; capa sai como gerada
    import os
    if os.environ.get("CAPA_TRATAMENTO") != "1":
        return "A"
    import hashlib
    from PIL import Image, ImageDraw
    variante = None
    try:
        import random
        import placar_titulos
        tx = {}
        for grupo in ("parceiro", "recapd"):
            for item, (t, v) in placar_titulos.taxas("capas_variante", grupo).items():
                tt, vv = tx.get(item, (0, 0))
                tx[item] = (tt + t, vv + v)
        if sum(t for t, _v in tx.values()) >= 6:
            variante = max("ABC", key=lambda x: random.betavariate(
                tx.get(x, (0, 0))[1] + 1, tx.get(x, (0, 0))[0] - tx.get(x, (0, 0))[1] + 1))
    except Exception:  # noqa: BLE001 — sem placar, segue o rodízio
        variante = None
    if not variante:
        variante = "ABC"[int(hashlib.md5(str(semente).encode()).hexdigest(), 16) % 3]
    if variante == "A":
        return "A"
    t = " ".join(str(x) for x in textos if x).casefold() + " "
    genero = next((g for g, pals in _CAPA_GENEROS if any(p in t for p in pals)), "drama")
    img = Image.open(capa_jpg).convert("RGBA")
    W, H = img.size
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    if variante == "B":  # tinge de leve na cor do gênero (alfa 0.45: tinta forte some com o personagem)
        c1, c2 = _CAPA_CORES[genero]
        for y in range(H):
            f = y / H
            r, g, b, a = (int(x * (1 - f) + z * f) for x, z in zip(c1, c2))
            d.line([(0, y), (W, y)], fill=(r, g, b, int(a * 0.45)))
    else:  # C: escurece da esquerda pra direita (destaca o lado direito, onde costuma estar o rosto)
        for x in range(W):
            d.line([(x, 0), (x, H)], fill=(0, 0, 0, int(240 * x / W)))
    img.alpha_composite(camada)
    img.convert("RGB").save(capa_jpg, quality=92)
    return f"{variante}:{genero}"


def _com_capitulos(descricao, video, roteiro=""):
    """Capítulos do longo (capitulos.json do anime-pipeline, ao lado do vídeo ou do roteiro — dona 25/10) no fim da
    descrição, no formato que o YouTube reconhece (1º em 0:00, 3 ou mais). Sem arquivo = descrição como estava."""
    for pasta in [Path(video).parent] + ([Path(roteiro).parent] if roteiro else []):
        arq = pasta / "capitulos.json"
        if not arq.exists():
            continue
        try:
            caps = json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return descricao
        if len(caps) < 3 or caps[0][0] != 0:
            return descricao

        def _t(s):
            s = int(s)
            return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"
        return descricao.rstrip() + "\n\nCapítulos:\n" + "\n".join(f"{_t(s)} {t}" for s, t in caps)
    return descricao


def _eh_parceiro(args):
    return bool(args.parceiro) or args.midia not in ("anime", None)


def _pasta_saida(base, slug, cap, date, idioma, source_url):
    """<obra>_cap<N>_<data>[_<língua>]. Outra fonte com o mesmo nome no mesmo dia (as "Part N" do parceiro têm
    todas o mesmo nome) ganha -2, -3... em vez de sobrescrever o vídeo da fila; refazer a MESMA fonte reaproveita."""
    suf = f"_{idioma}" if idioma else ""
    for n in range(1, 100):
        d = base / f"{slug}{'' if n == 1 else f'-{n}'}_cap{cap}_{date}{suf}"
        if not d.exists() or not any(d.iterdir()):
            return d
        try:
            fonte = json.loads((d / "metadata.json").read_text(encoding="utf-8"))["video"]["source_url"]
        except (OSError, ValueError, KeyError, TypeError):
            fonte = None
        if source_url and fonte == source_url:
            return d
    return d


def _usados(video):
    try:
        return json.loads((Path(video).parent / "_testes_usados.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _variantes_do_ambiente():
    """30/10: {teste: braço} das envs CORTES_* (bin\\variantes.py); None fora do Short de parceiro (sem env)."""
    try:
        import variantes
        return variantes.do_ambiente() or None
    except Exception:  # noqa: BLE001 — nunca derruba a publicação
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Vídeo final (.mp4)")
    parser.add_argument("--anime", required=True, help="Nome do anime")
    parser.add_argument("--cap", type=int, required=True, help="Número do capítulo")
    parser.add_argument("--formato", choices=["deitado", "short"], required=True)
    parser.add_argument("--source-url", default="", help="URL YouTube de origem")
    parser.add_argument("--roteiro", default="", help="Roteiro .txt (contexto extra)")
    parser.add_argument("--titulo-original", default="", help="Título do vídeo-fonte no YouTube (contexto do SEO)")
    parser.add_argument("--midia", default="anime",
                        help="tipo do conteúdo pro SEO (manhwa, anime, dorama, fatos, esportes, filme_sem_voz, etc.)")
    parser.add_argument("--parceiro", default=None,
                        help="nome do canal PARCEIRO de onde veio (Short refeito): categoria 'parceiro', sem trava")
    parser.add_argument("--idioma", default=None, help="hi/id/it/ru/th/vi/en: versão pro canal da língua (anime_idiomas)")
    parser.add_argument("--revisao-de", default=None,
                        help="postar.json da versão pt: herda a análise do vídeo pronto (mesma imagem, só muda o texto)")
    parser.add_argument("--canal", default=None,
                        help="id da credencial do canal de destino (parceiro: o @ dele já vai gravado no vídeo)")
    parser.add_argument("--anota-postar", default=None,
                        help="arquivo onde gravar o caminho do postar.json gerado (anime_auto -> anime_idiomas)")
    parser.add_argument("--narrador", default=None, help="voz do narrador usada (ex: pt-BR-ThalitaMultilingualNeural)")
    parser.add_argument("--voz-base", default=None, help="base RVC (francisca|kokoro|misto)")
    # 23/10 teste gradual (anime_testes.py): "solo" = controle, "formato:<chave>" / "voz:<nome>" = em teste
    parser.add_argument("--teste-voz", default=None, help="item do teste gradual (o placar de 48 h conta por ele)")
    parser.add_argument("--elenco", default=None, help="vozes que falam no Short, separadas por vírgula")
    parser.add_argument("--sintetico", action="store_true", help="pessoa real no elenco: marca conteúdo alterado")
    parser.add_argument("--segurar", default=None, help="motivo: o Short já nasce segurado (voz em teste que soou mal)")
    parser.add_argument("--sem-qa", action="store_true", help="pula a varredura qa_video (só avisa; longo de parceiro)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    video = Path(args.video).resolve()
    if not video.exists():
        print(f"[erro] vídeo não existe: {video}")
        sys.exit(1)

    slug = slugify(args.anime)
    cap = args.cap
    fmt_folder = "shorts" if args.formato == "short" else "videos laterais"
    date = datetime.now().strftime("%Y%m%d")
    out_dir = _pasta_saida(ANIMES_RECAP / fmt_folder, slug, cap, date, args.idioma, args.source_url)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[publish] alvo: {out_dir}")
    print(f"[publish] vídeo: {video} ({video.stat().st_size/1_048_576:.1f} MB)")

    video_info = probe_video(video)
    print(f"[publish] probe: {video_info.get('duration_s')}s @ {video_info.get('resolution')}")
    # 29/10 (Fable, LONGOS_12): varredura do vídeo INTEIRO sem IA (preto, congelado, mudo, volume) — só avisa e grava
    # qa.json na pasta de saída; não trava (regra da dona: só censura trava). Ver FABLE_DECISOES.md D10.
    qa_res = None
    try:
        if args.sem_qa:  # 01/11 dona: longo de parceiro levava 41 min aqui só pra avisar — nada trava
            raise RuntimeError("pulado (--sem-qa)")
        import qa_video
        qa_res = qa_video.analisar(video, gravar=False)
        print(f"[qa] {qa_video.resumo(qa_res)}")
        (out_dir / "qa.json").write_text(json.dumps(qa_res, ensure_ascii=False, indent=1), encoding="utf-8")
        if qa_res["problemas"]:
            try:
                sys.path.append(r"D:\video-fila")
                import avisos
                avisos.enviar(f"🔎 QA {args.formato} {slug} cap{cap}: {qa_video.resumo(qa_res)}", origem="longo" if
                              args.formato == "deitado" else "cortes", importante=not qa_res["ok"],
                              chave=f"qa:{out_dir.name}")
            except Exception as e:  # noqa: BLE001
                print(f"[qa] aviso não saiu ({type(e).__name__})")
    except Exception as e:  # noqa: BLE001
        print(f"[qa] falhou ({type(e).__name__}: {str(e)[:100]}) — segue")

    # 1) metadata: SEO novo (seo_generator) e, se o LLM falhar, o prompt antigo; nome da obra em lugar nenhum
    pacote = None
    if seo_generator:
        try:
            m_vid = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", args.source_url or "")
            rot = Path(args.roteiro)
            pacote = seo_generator.gerar_seo_anime(
                args.titulo_original or args.anime, video_id=m_vid.group(1) if m_vid else slug,
                nome_obra=args.anime, formato=args.formato, midia=args.midia,
                idioma_nome=_IDIOMA_NOME.get(args.idioma) if args.idioma else None,
                roteiro=rot.read_text(encoding="utf-8", errors="replace") if args.roteiro and rot.is_file() else "")
        except Exception as e:  # noqa: BLE001
            print(f"[seo] falhou ({type(e).__name__}: {str(e)[:120]}) — usando o metadata antigo")
    if pacote:
        meta = {"titulo": pacote["titulo"], "descricao": pacote["descricao"], "tags": pacote["tags"],
                "hashtags": [], "thumb_texto": pacote.get("texto_capa", ""), "ctas": [],
                "capa_conceito": pacote.get("protagonista_visual", ""), "estilo_titulo": pacote["estilo"],
                "titulos": pacote["titulos"], "seo_versao": pacote.get("seo_versao")}
        nomes_obra = [args.anime] + list(pacote.get("nomes_da_obra") or [])
        print(f"[seo] estilo={pacote['estilo']} | {meta['titulo']}")
    else:
        _rot = ""
        try:
            if args.roteiro and Path(args.roteiro).is_file():
                _rot = Path(args.roteiro).read_text(encoding="utf-8", errors="replace")
        except OSError:
            pass
        meta = generate_metadata(args.anime, cap, args.formato, video_info, roteiro_txt=_rot)
        nomes_obra = [args.anime]
        if seo_generator:  # o prompt antigo deixava o nome 1x na descrição/hashtag
            rx = seo_generator._rx_obra(nomes_obra)
            meta = seo_generator._sem_obra(meta, nomes_obra)
            meta["hashtags"] = [h for h in meta.get("hashtags") or [] if not (rx and rx.search(h))]
            if rx and rx.search(meta.get("titulo", "")):
                meta["titulo"] = _placeholder_meta(args.anime, cap, args.formato, video_info)["titulo"]
    meta.setdefault("thumb_texto", "")
    meta.setdefault("tags", [])
    if qa_res:  # 29/10 (Fable): o placar/painel pode cruzar problemas do QA com views
        meta["qa"] = {"ok": qa_res["ok"], "problemas": qa_res["problemas"], "loudness_lufs": qa_res["loudness_lufs"]}
    meta["slug"] = f"{slug}-cap{cap}"
    meta["youtube"] = {
        "category": "Entertainment",
        "made_for_kids": False,
        "language": "pt-BR",
        "publish_at": None,
        "privacy": "private",
    }
    meta["video"] = {
        **video_info,
        "anime": args.anime,
        "capitulo": cap,
        "source_url": args.source_url,
        "formato": args.formato,
    }
    meta["created_at"] = datetime.now().isoformat(timespec="seconds")
    # 12/11 dona ("ainda sai com a palavra completo") + política de spam do YouTube (promessa que o vídeo não entrega):
    # recap/Short cobre PARTE da obra -> nada de "(COMPLETO)", "Capítulo 1 COMPLETO", "RESUMO completo" no título.
    # TITULO_SEM_PROMESSA=0 desliga.
    if os.environ.get("TITULO_SEM_PROMESSA", "1") != "0" and meta.get("titulo"):
        import re as _re
        t0 = meta["titulo"]
        t1 = _re.sub(r"(?i)\s*[\(\[]\s*(completo|completa|final|todos os cap[ií]tulos)\s*[\)\]]", "", t0)
        t1 = _re.sub(r"(?i)\b(no\s+)?resumo\s+complet[oa]\b", "", t1)
        t1 = _re.sub(r"(?i)\s*\b(cap[ií]tulo\s*\d+\s+)?complet[oa]\b", "", t1)
        t1 = _re.sub(r"\s{2,}", " ", t1).strip(" -|")
        if t1 and t1 != t0:
            meta["titulo"] = t1
            print(f"[publish] título sem promessa enganosa: {t0} -> {t1}")

    meta_path = out_dir / "metadata.json"
    if not args.dry_run:
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[publish] metadata: {meta_path}")

    # 2) copiar vídeo + postar.json ANTES da capa (a capa pode levar minutos; se o anime_auto estourar o tempo,
    #    o vídeo já fica pronto pro postador, só sem capa própria)
    out_video = out_dir / "video.mp4"
    if not args.dry_run:
        # 04/11 15:20: gta-rp_cap1 chegou na fila com o mp4 SEM o índice (moov atom not found — vídeo que não abre;
        # o qa.json era de outro arquivo). Vídeo que o ffprobe não lê não entra na fila do postador.
        try:
            _pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  str(video)], capture_output=True, text=True, timeout=60)
            _dur = float((_pr.stdout or "0").strip() or 0)
        except Exception:  # noqa: BLE001
            _dur = 0.0
        if _dur <= 1:
            meta_path.unlink(missing_ok=True)
            raise SystemExit(f"[publish] vídeo QUEBRADO (ffprobe não lê: {video}) — não vai pra fila")
        out_video.unlink(missing_ok=True)
        try:  # 01/11: mesmo disco = link instantâneo (o longo de 2 GB levava minutos copiando)
            os.link(video, out_video)
        except OSError:
            shutil.copy2(video, out_video)
        print(f"[publish] vídeo na pasta: {out_video}")

    # postar.json — doc PADRÃO que a "cola" de postagem lê (PADRAO_DOC_POSTAGEM.md).
    # Um postar.json = um vídeo, na MESMA pasta do mp4. Assim o postador não adivinha:
    # usa o arquivo apontado + titulo/descricao/tags prontos.
    hashtags = meta.get("hashtags") or []
    descricao = meta.get("descricao", "")
    if args.formato == "deitado":
        descricao = _com_capitulos(descricao, video, args.roteiro)
    if hashtags:
        descricao = descricao.rstrip() + "\n\n" + " ".join(hashtags)
    postar = {
        "arquivo": out_video.name,                 # relativo a esta pasta
        # recap de anime -> 'animes' (postar_tudo_hoje); Short do parceiro -> 'parceiro': quem posta é o
        # bin/parceiro_diario.py (1 por canal por dia, canal certo); o postar_tudo_hoje ignora essa categoria
        "categoria": "parceiro" if _eh_parceiro(args) else "animes",
        "midia": args.midia,                       # manhwa / anime / dorama (SEO e narrador por nicho)
        "parceiro": args.parceiro or ("kaijinre" if args.midia == "manhwa" else None),  # canal de origem
        "idioma": args.idioma or "pt",             # canal de destino: pt = Manhwa Noturno; hi/id/it/ru/th/vi/en = inovare_*
        "canal": args.canal,                       # id da credencial do destino (None = o padrão da língua)
        "fonte": args.source_url,                  # a mesma fonte não sai em 2 canais no mesmo dia
        "tipo": "short" if args.formato == "short" else "completo",
        "titulo": meta.get("titulo", "")[:100],
        "descricao": descricao[:5000],
        "tags": meta.get("tags", []),
        "obra": args.anime,                        # interno (nunca vai pro YouTube)
        "cap": cap,
        "estilo_titulo": meta.get("estilo_titulo"),  # pra comparar o CTR por estilo (seo_generator.registrar_resultado)
        "seo_versao": meta.get("seo_versao"),        # 02/11: versão de config/seo_versoes.json (None = padrão)
        "publish_at": None,
        "privacy": "private",                      # sobe privado; você revisa e publica
        "made_for_kids": False,
        "pronto": False,       # a análise (3b, logo abaixo) decide: só "reprovado" (nudez) segura (22/10; regra 18/10)
        "revisao": "pendente",
        "narrador": args.narrador,
        "voz_base": args.voz_base,
        "teste_voz": args.teste_voz,               # tem de estar na 1ª gravação: o medidor olha cada vídeo 1x só
        "cobertura": __import__("os").environ.get("CORTES_COBERTURA_USADA") or None,  # 27/10 teste T2 tarja x delogo
        "legenda_estilo": __import__("os").environ.get("CORTES_LEGENDA_ESTILO") or None,  # 27/10 teste T3 impacto
        "gancho_meio": __import__("os").environ.get("CORTES_GANCHO_MEIO") or None,  # 28/10 teste T4 expectativa
        # 28/10 teste T5: "B" = gancho do Remotion saiu; "A_falhou" = sorteado B mas caiu no ASS; vazio = A
        # (o render roda noutro processo: o que ele usou vem do _testes_usados.json da pasta do vídeo)
        "gancho_remotion": _usados(video).get("gancho_remotion"),
        "fx_choque": _usados(video).get("fx_choque"),  # 28/10 teste T6: estilo do choque/fogo; vazio = A
        "mascote": _usados(video).get("mascote"),  # 28/10 teste T7: B | A_falhou | vazio = A
        "curto": __import__("os").environ.get("CORTES_CURTO") or None,  # 29/10 teste T8 (Fable): B = 4-5 frases
        "fala_rapida": __import__("os").environ.get("CORTES_FALA_RAPIDA") or None,  # 29/10 teste T9 (Fable): B = +15% fala
        # 30/10 variantes (bin\variantes.py): T10 A = tira a saudação da 1ª fala, B = mantém; T11 A = "NINGUÉM
        # ESPERAVA" liberado, B = proibido. "variantes" = todos os braços por vídeo sorteados no fazer_short
        "saudacao": __import__("os").environ.get("CORTES_SAUDACAO") or None,
        "ninguem_esperava": __import__("os").environ.get("CORTES_NINGUEM_ESPERAVA") or None,
        "abertura": __import__("os").environ.get("CORTES_ABERTURA") or None,  # 13/11 teste T13: forma da 1ª frase
        "variantes": _variantes_do_ambiente(),
        "texto_modelo": __import__("os").environ.get("TEXTO_VIDEO_MODELO") or None,  # 27/10 Argon no texto do vídeo
        "elenco": [v for v in (args.elenco or "").split(",") if v] or None,
        "sintetico": bool(args.sintetico),         # parceiro_diario passa pro upload (VIDEO_HAS_ALTERED_CONTENT)
    }
    if args.segurar:  # já na 1ª gravação: nenhum caminho de erro adiante deixa pronto=True (revisão 23/10)
        postar["revisao"] = f"reprovado (segurado): teste de voz — {args.segurar}"[:300]
    postar_path = out_dir / "postar.json"
    if not args.dry_run:
        postar_path.write_text(json.dumps(postar, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[publish] postar.json: {postar_path}")
        if args.anota_postar:
            Path(args.anota_postar).write_text(str(postar_path), encoding="utf-8")

    # 3) capa IA (16:9 no deitado, 9:16 no short) ou quadro do vídeo
    capa_jpg = out_dir / "capa.jpg"
    capa_gerada = False
    # 05/11 dona ("resolva o gargalo de postagem"): cada longo ficava 1 h+ esperando o Flow gerar a capa antes de subir
    # (o Flow vive ocupado/instável nos notebooks). ANIME_CAPA_DEPOIS=1 (postar_longos) = sobe sem esperar; o
    # colab\capas_depois.py gera as MESMAS capas (capa A + teste A/B) e aplica no vídeo pelo Studio quando ficam prontas.
    capa_depois = os.environ.get("ANIME_CAPA_DEPOIS") == "1" and args.midia in ("anime", "manhwa")
    if capa_depois and not args.dry_run:
        postar["capa_depois"] = {
            "anime": args.anime, "cap": cap,
            "texto": "" if args.idioma in _SEM_TEXTO_CAPA else meta.get("thumb_texto", ""), "cena": meta.get("titulo", ""),
            "protagonista": (pacote or {}).get("protagonista_visual", ""), "generos": (pacote or {}).get("generos"),
            "formato": "9:16" if args.formato == "short" else "16:9",
            "source_url": getattr(args, "source_url", "") if args.formato == "deitado" else ""}
        postar_path.write_text(json.dumps(postar, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[publish] capa vai DEPOIS do envio (capas_depois.py)")
    # capa IA só para anime/manhwa (os outros nichos usam quadro do próprio vídeo)
    if capa_ia_anime and not args.dry_run and args.midia in ("anime", "manhwa") and not capa_depois:
        try:
            capa_gerada = bool(capa_ia_anime.gerar_capa(
                args.anime, cap, str(capa_jpg),
                texto="" if args.idioma in _SEM_TEXTO_CAPA else meta.get("thumb_texto", ""), cena=meta.get("titulo", ""),
                protagonista=(pacote or {}).get("protagonista_visual", ""), generos=(pacote or {}).get("generos"),
                formato="9:16" if args.formato == "short" else "16:9",
                # 29/10 dona: longo de parceiro = a capa dele melhorada (o público conhece a obra pelo protagonista)
                source_url=getattr(args, "source_url", "") if args.formato == "deitado" else ""))
        except Exception as e:  # noqa: BLE001
            print(f"[capa_ia] falhou ({type(e).__name__}: {str(e)[:120]}), usando frame do vídeo")
    if capa_gerada:
        print(f"[publish] capa IA gerada: {capa_jpg}")
        postar["thumb"] = capa_jpg.name  # o postador manda como miniatura (upload pelo navegador)
        try:
            postar["capa_pose"] = json.loads(capa_jpg.with_suffix(".capa.json").read_text(encoding="utf-8"))["pose"]
        except (OSError, ValueError, KeyError):
            pass
        # 22/10 (vigia 8e7f1f): a MESMA capa sai num de 3 tratamentos em rodízio determinístico — A controle,
        # B gradiente na cor do gênero, C escurecida da esquerda — sem gastar geração de imagem; a variante
        # fica no postar.json pro placar cruzar variante × views quando as métricas fecharem (fa0246).
        try:
            postar["capa_variante"] = _tratar_capa(capa_jpg, f"{args.anime}|{cap}",
                                                   meta.get("titulo", ""), postar.get("descricao", ""))
        except Exception as e:  # noqa: BLE001 — tratamento é acabamento; a capa A pura já serve
            print(f"[publish] [!] tratamento da capa falhou ({type(e).__name__}: {str(e)[:80]}) — fica a A")
        # 30/10 dona: longo de parceiro sobe com até 3 capas pro teste A/B do Studio (A = capa dele melhorada,
        # B = a mais sensual, C = outra pose), todas com o protagonista dele e a mascote. O extras_ledger monta o
        # teste quando o vídeo abre (campo thumbs_ab, nomes relativos à pasta).
        surl = getattr(args, "source_url", "") if args.formato == "deitado" else ""
        if surl and args.midia in ("anime", "manhwa"):
            try:
                extras = capa_ia_anime.capas_ab(
                    surl, str(capa_jpg), "" if args.idioma in _SEM_TEXTO_CAPA else meta.get("thumb_texto", ""),
                    meta.get("titulo", ""), (pacote or {}).get("generos"))
                if extras:
                    postar["thumbs_ab"] = [capa_jpg.name] + [Path(p).name for p in extras]
                    print(f"[publish] capas do teste A/B: {postar['thumbs_ab']}")
                else:
                    print(f"[publish] [!] capas do teste A/B não geradas (capas_ab retornou lista vazia — "
                          f"verifique se a miniatura {surl} está acessível ou se o gateway de imagem está ativo)")
            except Exception as e:  # noqa: BLE001 — teste A/B é extra; a capa A já sobe
                print(f"[publish] [!] capas do teste A/B falharam ({type(e).__name__}: {str(e)[:80]})")
        postar_path.write_text(json.dumps(postar, ensure_ascii=False, indent=2), encoding="utf-8")

    # Fallback: extrai frame do vídeo (só referência local; não vai como miniatura)
    if not capa_gerada:
        thumb_png = out_dir / "_thumb_src.png"
        if extract_thumb(video, thumb_png):
            # converte PNG → JPG qualidade 90, redimensiona pra 1280x720
            if not args.dry_run:
                r = subprocess.run(
                    ["ffmpeg", "-y", "-i", str(thumb_png),
                     "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
                     "-update", "1", "-q:v", "2", str(capa_jpg)],
                    capture_output=True,
                )
                # 18/10: falha passageira aqui derrubava o publish antes do pronto=True e o Short ficava fora da postagem
                if r.returncode == 0:
                    thumb_png.unlink()
                    print(f"[publish] capa (frame): {capa_jpg}")
                else:
                    err = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()[-3:]
                    print(f"[publish] [!] capa (frame) falhou rc={r.returncode} — segue sem capa: {' | '.join(err)}")

    # 3b) análise do vídeo pronto (trava de nudez do hipercool): sem "ok" o postar.json fica pronto=False e o
    #     postador não sobe; `python bin/anime_revisao.py --pendentes` refaz os que não fecharam.
    if not args.dry_run:
        try:
            import anime_revisao
            if args.segurar:  # 23/10 teste gradual: a conferência do áudio já reprovou — nunca fica pronto=True
                postar.update(revisao=f"reprovado (segurado): teste de voz — {args.segurar}"[:300], pronto=False)
                postar_path.write_text(json.dumps(postar, ensure_ascii=False, indent=2), encoding="utf-8")
            elif _eh_parceiro(args):
                # dono 17/10: refação de vídeo de parceiro que JÁ está no YouTube não passa pela trava
                postar.update(revisao="dispensada (fonte de parceiro já no YouTube; dono 17/10)", pronto=True)
                postar_path.write_text(json.dumps(postar, ensure_ascii=False, indent=2), encoding="utf-8")
            elif args.revisao_de:
                anime_revisao.herdar(postar_path, args.revisao_de)
            else:
                anime_revisao.aplicar(postar_path)
        except Exception as e:  # noqa: BLE001
            # 22/10 (regra do dono 18/10): a ANÁLISE quebrar não segura o vídeo — só nudez confirmada segura.
            # Antes ficava pronto=False pra sempre e o canal perdia o dia.
            postar.update(revisao=f"erro: análise não rodou ({type(e).__name__}: {str(e)[:100]})", pronto=True)
            if args.segurar:  # o áudio já foi reprovado: a regra 18/10 (sobe mesmo assim) não vale pra ele
                postar.update(revisao=f"reprovado (segurado): teste de voz — {args.segurar}"[:300], pronto=False)
            postar_path.write_text(json.dumps(postar, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[revisao] falhou ({type(e).__name__}: {str(e)[:120]}) — o vídeo SOBE mesmo assim (regra 18/10)")
            try:
                anime_revisao._avisar(f"Análise não rodou pro {postar.get('titulo', '?')[:60]} "
                                      f"({type(e).__name__}) — subiu sem análise; conferir depois")
            except Exception:  # noqa: BLE001
                pass

    # 4) resumo
    print()
    print("=" * 60)
    print(f"TÍTULO:    {meta['titulo']}")
    print(f"THUMB:     {meta['thumb_texto']}")
    print(f"TAGS ({len(meta['tags'])}):  {', '.join(meta['tags'][:8])}...")
    print(f"DIR:       {out_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()