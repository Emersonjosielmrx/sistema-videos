r"""corrigir_titulo_generico.py — Shorts na FILA (ainda não postados) com o título genérico de recap de anime (14/11/2026).

Por quê: quando o gerador de SEO falhava, o metadata de reserva (anime_publish.generate_metadata) escrevia sempre como
recap de anime: um dorama sobre mãe e filha saiu "⚡ Ele Foi Traído e Acabou Despertando o Poder Mais Apelado do Mundo!"
e um vídeo de ciência sobre ventilador, "Ele Perdeu TUDO e Renasceu no Mundo Mais Perigoso! Capítulo 1 COMPLETO".
O gerador foi consertado em 14/11 (usa o roteiro); este script arruma os que JÁ estavam na fila.

O que faz: acha fichas de parceiro sem posted_url/agendado_para cujo título bate com o texto genérico, OUVE a narração
do vídeo (Whisper local, o mesmo do conferir_audio) e gera título/descrição/tags a partir do que se ouve. Guarda o
texto antigo em "titulo_generico_antes". Nunca mexe em vídeo já postado ou agendado. Sem transcrição = não mexe.

    python corrigir_titulo_generico.py            # ensaio: mostra o que mudaria
    python corrigir_titulo_generico.py --fazer
"""
import json
import re
import subprocess
import sys
from pathlib import Path

SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")
BIN = Path(r"D:\recapd-ambientes\producao\bin")
sys.path.insert(0, str(BIN))
RX = re.compile(r"Ele Perdeu TUDO e Renasceu|Ele Foi Tra[ií]do e (Acabou|Acordou|Jogado)|Poder Mais Apel", re.I)
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def candidatos():
    out = []
    for pj in sorted(SHORTS.glob("*/postar.json")):
        try:
            d = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if d.get("categoria") != "parceiro" or (d.get("idioma") or "pt") != "pt":
            continue  # só pt: nas outras línguas o título é traduzido por outro caminho
        if d.get("posted_url") or d.get("agendado_para") or d.get("timeout_em"):
            continue
        if d.get("seo_versao") is None and not d.get("estilo_titulo") and RX.search(str(d.get("titulo") or "")):
            out.append((pj, d))
    return out


def ouvir(video):
    """Narração do vídeo em texto. "" se não deu. 1º o Groq (Whisper large-v3, o mesmo da conferência de áudio); sem
    ele, o Whisper local "small". O "tiny" NÃO serve aqui: no ensaio de 14/11 ele ouviu "Grapéia", "fiscaria" e trocou
    mãe por pai — e o erro ia direto pro título."""
    mp3 = video.with_name("_titulo_ouvir.mp3")
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-b:a",
                        "48k", str(mp3)], check=True, timeout=180, creationflags=_SEM_JANELA)
        try:
            import monitor_bordoes
            txt = (monitor_bordoes._transcrever(mp3) or "").strip()
            if len(txt.split()) >= 12:
                return txt
        except Exception:  # noqa: BLE001
            pass
        r = subprocess.run([sys.executable, str(BIN / "_whisper_sub.py"), str(mp3), "small"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=900, creationflags=_SEM_JANELA)
        return (r.stdout or "").splitlines()[0].strip() if r.returncode == 0 and (r.stdout or "").strip() else ""
    except Exception as e:  # noqa: BLE001
        print(f"   não ouvi ({type(e).__name__})")
        return ""
    finally:
        mp3.unlink(missing_ok=True)


def _norm(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def _fora_do_ouvido(titulo, ouvido):
    """Palavras em MAIÚSCULAS do título (4+ letras) cujo radical não aparece no texto ouvido."""
    base = _norm(ouvido)
    fora = []
    # palavras de chamada que todo título usa e não são "assunto": não precisam estar no áudio
    comuns = {"ACONTECE", "ACONTECEU", "VEJA", "ENTENDA", "DESCUBRA", "MOTIVO", "VERDADE", "SEGREDO", "INCRIVEL",
              "INCRÍVEL", "NINGUEM", "NINGUÉM", "ESPERAVA", "TUDO", "NADA", "ISSO", "ESSE", "ESSA", "FAZ", "FEZ",
              "COMO", "QUANDO", "PORQUE", "QUAL", "QUEM", "MUNDO", "HOJE", "AGORA", "SEMPRE", "NUNCA", "MUITO"}
    for w in re.findall(r"\b[A-ZÀ-Ý]{4,}\b", titulo):
        if w in comuns:
            continue
        raiz = _norm(w)[:max(4, len(w) - 2)]  # tolera plural/conjugação: "SALVAR" casa com "salvou"
        if raiz not in base:
            fora.append(w)
    return fora


def main():
    fazer = "--fazer" in sys.argv
    import anime_publish
    n = 0
    for pj, d in candidatos():
        pasta = pj.parent
        video = pasta / (d.get("arquivo") or "video.mp4")
        print(f"\n{pasta.name}\n   antes: {d.get('titulo')}")
        if not video.exists():
            print("   vídeo não está no PC (reserva no Drive) — fica pra quando voltar")
            continue
        texto = ouvir(video)
        if len(texto.split()) < 12:
            print(f"   transcrição curta demais ({len(texto.split())} palavras) — não mexo")
            continue
        meta = anime_publish.generate_metadata(d.get("obra") or pasta.name, d.get("cap") or 1, "short", {},
                                               roteiro_txt=texto)
        titulo = str(meta.get("titulo") or "").strip()
        if not titulo or RX.search(titulo):
            print("   título novo não saiu — não mexo")
            continue
        print(f"   ouvido: {texto[:150]}…\n   depois: {titulo}")
        # palavra em DESTAQUE (MAIÚSCULAS) no título tem de estar no que se ouviu: o gerador às vezes troca quem é
        # quem ("PAI" num vídeo de mãe e filha) ou cria palavra ("FISCARIA"). Fora do ouvido = não grava.
        estranhas = _fora_do_ouvido(titulo, texto)
        if estranhas:
            print(f"   [!] destaque do título que não está no que se ouve: {estranhas} — não gravo (conferir à mão)")
            continue
        if not fazer:
            continue
        d["titulo_generico_antes"] = d.get("titulo")
        d["titulo"] = titulo[:100]
        if meta.get("descricao"):
            d["descricao"] = str(meta["descricao"])
        if meta.get("tags"):
            d["tags"] = [str(x) for x in meta["tags"]][:20]
        tmp = pj.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(pj)
        n += 1
    print(f"\n{'corrigidos' if fazer else 'ensaio — corrigiria'}: {n if fazer else 'ver acima'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
