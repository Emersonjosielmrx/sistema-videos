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


def generate_metadata(anime, capitulo, formato, video_info, roteiro_path=None):
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

    if not claude_client.is_available():
        print("[metadata] claude_client indisponível — usando placeholder")
        return _placeholder_meta(anime, capitulo, formato, video_info)

    resp = claude_client.generate_text(prompt, max_tokens=2000, temperature=0.7)
    if not resp:
        return _placeholder_meta(anime, capitulo, formato, video_info)

    # Limpa blocos markdown ```json ... ```
    txt = resp.strip()
    txt = re.sub(r"^```(?:json)?\s*", "", txt)
    txt = re.sub(r"\s*```$", "", txt)
    # Extrai primeiro bloco {...}
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    if not m:
        print("[metadata] resposta sem JSON válido, usando placeholder")
        return _placeholder_meta(anime, capitulo, formato, video_info)
    try:
        return json.loads(m.group(0))
    except Exception as e:
        print(f"[metadata] JSON parse falhou: {e}")
        return _placeholder_meta(anime, capitulo, formato, video_info)


def _placeholder_meta(anime, cap, formato, video_info):
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
                "vi": "vietnamita", "en": "inglês"}
_SEM_TEXTO_CAPA = {"hi", "th", "ru", "vi"}


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
                "titulos": pacote["titulos"]}
        nomes_obra = [args.anime] + list(pacote.get("nomes_da_obra") or [])
        print(f"[seo] estilo={pacote['estilo']} | {meta['titulo']}")
    else:
        meta = generate_metadata(args.anime, cap, args.formato, video_info)
        nomes_obra = [args.anime]
        if seo_generator:  # o prompt antigo deixava o nome 1x na descrição/hashtag
            rx = seo_generator._rx_obra(nomes_obra)
            meta = seo_generator._sem_obra(meta, nomes_obra)
            meta["hashtags"] = [h for h in meta.get("hashtags") or [] if not (rx and rx.search(h))]
            if rx and rx.search(meta.get("titulo", "")):
                meta["titulo"] = _placeholder_meta(args.anime, cap, args.formato, video_info)["titulo"]
    meta.setdefault("thumb_texto", "")
    meta.setdefault("tags", [])
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

    meta_path = out_dir / "metadata.json"
    if not args.dry_run:
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[publish] metadata: {meta_path}")

    # 2) copiar vídeo + postar.json ANTES da capa (a capa pode levar minutos; se o anime_auto estourar o tempo,
    #    o vídeo já fica pronto pro postador, só sem capa própria)
    out_video = out_dir / "video.mp4"
    if not args.dry_run:
        shutil.copy2(video, out_video)
        print(f"[publish] vídeo copiado: {out_video}")

    # postar.json — doc PADRÃO que a "cola" de postagem lê (PADRAO_DOC_POSTAGEM.md).
    # Um postar.json = um vídeo, na MESMA pasta do mp4. Assim o postador não adivinha:
    # usa o arquivo apontado + titulo/descricao/tags prontos.
    hashtags = meta.get("hashtags") or []
    descricao = meta.get("descricao", "")
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
        "publish_at": None,
        "privacy": "private",                      # sobe privado; você revisa e publica
        "made_for_kids": False,
        "pronto": False,       # só vira True com a análise do vídeo pronto "ok" (anime_revisao, 16/10)
        "revisao": "pendente",
    }
    postar_path = out_dir / "postar.json"
    if not args.dry_run:
        postar_path.write_text(json.dumps(postar, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[publish] postar.json: {postar_path}")
        if args.anota_postar:
            Path(args.anota_postar).write_text(str(postar_path), encoding="utf-8")

    # 3) capa IA (16:9 no deitado, 9:16 no short) ou quadro do vídeo
    capa_jpg = out_dir / "capa.jpg"
    capa_gerada = False
    # capa IA só para anime/manhwa (os outros nichos usam quadro do próprio vídeo)
    if capa_ia_anime and not args.dry_run and args.midia in ("anime", "manhwa"):
        try:
            capa_gerada = bool(capa_ia_anime.gerar_capa(
                args.anime, cap, str(capa_jpg),
                texto="" if args.idioma in _SEM_TEXTO_CAPA else meta.get("thumb_texto", ""), cena=meta.get("titulo", ""),
                protagonista=(pacote or {}).get("protagonista_visual", ""), generos=(pacote or {}).get("generos"),
                formato="9:16" if args.formato == "short" else "16:9"))
        except Exception as e:  # noqa: BLE001
            print(f"[capa_ia] falhou ({type(e).__name__}: {str(e)[:120]}), usando frame do vídeo")
    if capa_gerada:
        print(f"[publish] capa IA gerada: {capa_jpg}")
        postar["thumb"] = capa_jpg.name  # o postador manda como miniatura (upload pelo navegador)
        try:
            postar["capa_pose"] = json.loads(capa_jpg.with_suffix(".capa.json").read_text(encoding="utf-8"))["pose"]
        except (OSError, ValueError, KeyError):
            pass
        postar_path.write_text(json.dumps(postar, ensure_ascii=False, indent=2), encoding="utf-8")

    # Fallback: extrai frame do vídeo (só referência local; não vai como miniatura)
    if not capa_gerada:
        thumb_png = out_dir / "_thumb_src.png"
        if extract_thumb(video, thumb_png):
            # converte PNG → JPG qualidade 90, redimensiona pra 1280x720
            if not args.dry_run:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(thumb_png),
                     "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
                     "-q:v", "2", str(capa_jpg)],
                    check=True, capture_output=True,
                )
                thumb_png.unlink()
                print(f"[publish] capa (frame): {capa_jpg}")

    # 3b) análise do vídeo pronto (trava de nudez do hipercool): sem "ok" o postar.json fica pronto=False e o
    #     postador não sobe; `python bin/anime_revisao.py --pendentes` refaz os que não fecharam.
    if not args.dry_run:
        try:
            import anime_revisao
            if _eh_parceiro(args):
                # dono 17/10: refação de vídeo de parceiro que JÁ está no YouTube não passa pela trava
                postar.update(revisao="dispensada (fonte de parceiro já no YouTube; dono 17/10)", pronto=True)
                postar_path.write_text(json.dumps(postar, ensure_ascii=False, indent=2), encoding="utf-8")
            elif args.revisao_de:
                anime_revisao.herdar(postar_path, args.revisao_de)
            else:
                anime_revisao.aplicar(postar_path)
        except Exception as e:  # noqa: BLE001
            print(f"[revisao] falhou ({type(e).__name__}: {str(e)[:120]}) — fica pronto=False")

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