# -*- coding: utf-8 -*-
"""studio_extras_historias.py — Acabamento no YouTube Studio DEPOIS do upload (historias-em-frames).

Roda DEPOIS que postar_historias.py já subiu os vídeos. Adiciona:
- Comentário fixado: "🔔 Ative o sino para mais histórias! 💬 Comente qual história você quer ouvir!"

Uso:
  python bin/studio_extras_historias.py --canal <id|nome> --max 3

Lê logs/videos_postados.json e workspace/extras_pendentes.json (estado das ações).
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT = Path(__file__).resolve().parent.parent
POSTADOR_BIN = Path(r"D:\postador-de-videos\bin")
sys.path.insert(0, str(POSTADOR_BIN))

try:
    import youtube_studio_extras as yx
except ImportError:
    print("ERRO: youtube_studio_extras não encontrado em D:\\postador-de-videos\\bin")
    sys.exit(1)

POSTADOS_LOG = PROJECT / "logs/videos_postados.json"
EXTRAS_STATE = PROJECT / "workspace/extras_pendentes.json"
EXTRAS_INTERVALO_H = 3  # Retry a cada 3h se pendente
EXTRAS_MAX_AVISOS = 5  # Desiste após 5 avisos


def log(msg):
    print(f"[{datetime.utcnow().isoformat(timespec='seconds')}Z] {msg}", flush=True)


def _vid(url):
    """Extrai video ID da URL do YouTube."""
    import re
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def carregar_estado():
    """Carrega extras_pendentes.json (estado: o que fazer no Studio)."""
    try:
        return json.loads(EXTRAS_STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def salvar_estado(estado):
    """Salva extras_pendentes.json."""
    EXTRAS_STATE.parent.mkdir(parents=True, exist_ok=True)
    EXTRAS_STATE.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def _extra_pendente(p, agora):
    """Checa se uma ação extra precisa ser executada/retentada."""
    st = p.get("status") or ""
    if st in ("ok", "ja") or (st.startswith("aviso") and p.get("tentativas", 0) >= EXTRAS_MAX_AVISOS):
        return False
    if st.startswith("bloqueado"):
        import re
        m = re.search(r"até (\d{4}-\d{2}-\d{2})", st)
        return bool(m) and agora.date().isoformat() >= m.group(1)
    em = p.get("em")
    return not em or (agora - datetime.fromisoformat(em)).total_seconds() >= EXTRAS_INTERVALO_H * 3600


def adicionar_extras(video_path, url, canal):
    """Registra extras para um vídeo recém-postado.

    Args:
        video_path: Path do vídeo local
        url: URL do vídeo no YouTube
        canal: Nome do canal
    """
    vid = _vid(url)
    if not vid:
        return

    estado = carregar_estado()
    if vid in estado and all(p.get("status") in ("ok", "ja") for p in estado[vid].get("extras", {}).values()):
        return  # Já completo

    # Detecta categoria pelo nome do arquivo
    nome = Path(video_path).stem.lower()
    if "terror" in nome or "medo" in nome or "assustador" in nome:
        categoria = "terror"
    elif "superacao" in nome or "motivacao" in nome or "inspiracao" in nome:
        categoria = "superacao"
    else:
        categoria = "terror"  # Fallback padrão

    # Comentário fixado diferente por categoria
    if categoria == "terror":
        texto_comentario = "🔔 Ative o sino para mais histórias de TERROR! 💬 Comente qual história assustadora você quer ouvir! 😱"
    else:
        texto_comentario = "🔔 Ative o sino para mais histórias de SUPERAÇÃO! 💬 Comente sua história para inspirar outras pessoas! 💪"

    extras = {
        "comentario": {"texto": texto_comentario}
    }

    # Teste A/B de capa: se o .capa.json tem variantes, registra pra testar no Studio
    capa_json = Path(video_path).with_suffix(".capa.json")
    if not capa_json.exists():
        # Procura no diretório do vídeo
        for f in Path(video_path).parent.glob("*.capa.json"):
            capa_json = f
            break
    if capa_json.exists():
        try:
            cd = json.loads(capa_json.read_text(encoding="utf-8"))
            variantes = cd.get("variantes", [])
            if len(variantes) >= 2:
                extras["teste_ab_capa"] = {
                    "capa_json": str(capa_json),
                    "capas": [v.get("arquivo") for v in variantes if v.get("arquivo")],
                }
        except (OSError, ValueError):
            pass

    estado[vid] = {
        "video_path": str(video_path),
        "url": url,
        "canal": canal,
        "categoria": categoria,
        "postado_em": datetime.utcnow().isoformat(timespec="seconds"),
        "extras": extras
    }
    salvar_estado(estado)
    log(f"  ✓ Extras registrados para {vid} ({categoria}): {', '.join(extras.keys())}")


def rodar_extras(canal, max_videos=3):
    """Executa extras pendentes no Studio.

    Args:
        canal: Nome do canal
        max_videos: Máximo de vídeos a processar

    Returns:
        Número de vídeos processados
    """
    estado = carregar_estado()
    agora, feitos = datetime.now(), 0

    # Ordena por data de postagem (mais recentes primeiro)
    items = sorted(
        [(vid, data) for vid, data in estado.items() if isinstance(data, dict) and data.get("canal") == canal],
        key=lambda x: x[1].get("postado_em", ""),
        reverse=True
    )

    for vid, data in items:
        if feitos >= max_videos:
            break

        ex = data.get("extras", {})
        fazer = {a: p for a, p in ex.items() if _extra_pendente(p, agora)}
        if not fazer:
            continue

        # Monta kwargs para youtube_studio_extras
        kw = {}
        if "comentario" in fazer:
            kw["comentario"] = fazer["comentario"]["texto"]
        if "teste_ab_capa" in fazer:
            capas = fazer["teste_ab_capa"].get("capas", [])
            capas_existentes = [c for c in capas if Path(c).exists()]
            if len(capas_existentes) >= 2:
                kw["ab"] = capas_existentes

        log(f"Processando {vid} (canal={canal}): {', '.join(fazer.keys())}")

        try:
            res = yx.rodar(canal, vid, **kw)
            feitos += 1

            # Atualiza status de cada ação
            for a, p in fazer.items():
                chave = "<SEGREDO_REMOVIDO>" if a == "teste_ab_capa" else a  # nome da ação no RESULTADO do youtube_studio_extras
                p["status"] = res.get(chave) or "aviso: " + str(res.get("erro") or "sem resposta")[:150]
                p["em"] = agora.isoformat(timespec="seconds")
                p["tentativas"] = p.get("tentativas", 0) + 1

            # Registra no Thompson das capas se o teste A/B foi aceito
            if "teste_ab_capa" in fazer and res.get("teste_ab") == "ok":
                cj = fazer["teste_ab_capa"].get("capa_json")
                if cj:
                    try:
                        from capa_ia_historias import registrar_teste
                        registrar_teste(cj)
                    except Exception:  # noqa: BLE001
                        pass

            log(f"  Resultado: " + ", ".join(f"{a}={p['status']}" for a, p in fazer.items()))
            salvar_estado(estado)

        except Exception as e:
            log(f"  ERRO ao processar {vid}: {e}")
            for a, p in fazer.items():
                p["status"] = f"erro: {str(e)[:100]}"
                p["em"] = agora.isoformat(timespec="seconds")
                p["tentativas"] = p.get("tentativas", 0) + 1
            salvar_estado(estado)

    return feitos


def main():
    parser = argparse.ArgumentParser(description="Acabamento no YouTube Studio para histórias")
    parser.add_argument("--canal", required=True, help="Nome ou ID do canal")
    parser.add_argument("--max", type=int, default=3, help="Máximo de vídeos a processar (padrão: 3)")
    args = parser.parse_args()

    n = rodar_extras(args.canal, max_videos=args.max)
    log(f"RESUMO: {n} vídeo(s) processado(s)")


if __name__ == "__main__":
    main()
