"""ficha_longo.py — o resumo de UM vídeo longo para o Telegram (dona 31/10: "produção deve diferenciar curtos de longos;
de longos deve ter o tempo que vai demorar pra sair, onde será postado, ou se já saiu quanto tempo demorou, e se ele
contém atualizações caso tenhamos atualizado recentemente e quais vão ficar pro próximo vídeo").

Sem IA, só arquivos que já existem:
  tempo      pipeline.log da ficha (1ª linha com data = início) e render.json ("fim"); média dos últimos = previsão
  destino    colab\\longos_postados.json (já postado: canal + link) ou a fila de canais do postar_longos.py (próximo)
  melhorias  linhas\\LONGOS\\melhorador_estado.json: "mudancas" com data ANTES do início do render = entraram neste
             vídeo; depois do início = ficam pro próximo; "propostas" ainda não aplicadas = próximas

    python ficha_longo.py <pasta da ficha | id do vídeo>     # imprime o texto (teste, não manda nada)
"""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
POSTADOS = Path(r"D:\recapd-ambientes\producao\colab\longos_postados.json")
POSTAR = Path(r"D:\recapd-ambientes\producao\colab\postar_longos.py")
MELHORADOR = Path(__file__).resolve().parent / "melhorador_estado.json"
DATA_LOG = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)")


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return padrao


def _local(iso):
    """ISO (com ou sem fuso) -> datetime local sem fuso."""
    d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    return d.astimezone().replace(tzinfo=None) if d.tzinfo else d


def _inicio(ficha):
    """1ª linha com data do pipeline.log (hora do Kaggle = UTC)."""
    try:
        with open(ficha / "pipeline.log", encoding="utf-8", errors="replace") as f:
            for _ in range(200):
                m = DATA_LOG.match(f.readline())
                if m:
                    return datetime.fromisoformat(m.group(1)).replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)
    except OSError:
        pass
    return None


def _fim(ficha):
    r = _ler(ficha / "render.json", {})
    try:
        return _local(r["fim"]) if r.get("fim") else None
    except ValueError:
        return None


def _h(seg):
    seg = int(seg)
    return f"{seg // 3600} h {seg % 3600 // 60:02d} min" if seg >= 3600 else f"{seg // 60} min"


def media_render(n=8):
    """Média (s) dos últimos n longos com início e fim conhecidos."""
    tempos = []
    for f in sorted(FICHAS.glob("*/render.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
        a, b = _inicio(f.parent), _fim(f.parent)
        if a and b and 1800 < (b - a).total_seconds() < 24 * 3600:
            tempos.append((b - a).total_seconds())
        if len(tempos) >= n:
            break
    return sum(tempos) / len(tempos) if tempos else None


def destino(ficha):
    """(texto, link) — já postado ou o próximo canal da fila do postar_longos."""
    for p in _ler(POSTADOS, {}).get("postados", []):
        if p.get("nome") == ficha.name or (p.get("vid") and ficha.name.startswith(p["vid"])):
            return f"postado em {p.get('canal_nome') or p.get('canal')} ({str(p.get('em', ''))[:16].replace('T', ' ')})", p.get("url")
    for p in _ler(POSTADOS, {}).get("reprovados", []) if isinstance(_ler(POSTADOS, {}).get("reprovados"), list) else []:
        if isinstance(p, dict) and p.get("nome") == ficha.name:
            return "NÃO vai subir: reprovado na revisão (" + str(p.get("motivo", ""))[:80] + ")", None
    canais = re.findall(r'\("[^"]+", "([^"]+)"\)', POSTAR.read_text(encoding="utf-8", errors="replace")) if POSTAR.exists() else []
    ja = {p.get("canal_nome") for p in _ler(POSTADOS, {}).get("postados", [])}
    fila = [c for c in canais if c not in ja] or canais
    nota = (_ler(ficha / "nuvem.json", {}).get("postar") or "")
    return (f"vai pra fila do postar_longos (próximo canal: {fila[0]})" if fila else "fila do postar_longos") \
        + (f" — {nota}" if "sem canal" in nota else ""), None


def melhorias(inicio):
    """(entraram, proximas): mudanças do melhorador antes do início = entraram; depois + propostas = próximas."""
    m = _ler(MELHORADOR, {})
    entraram, proximas = [], []
    corte = inicio or datetime.now()
    for x in m.get("mudancas") or []:
        try:
            quando = _local(x["em"])
        except (KeyError, ValueError):
            continue
        txt = str(x.get("depois") or x.get("chave") or "")[:110]
        if quando <= corte and corte - quando <= timedelta(days=4):  # "atualizado recentemente"
            entraram.append(f"{quando:%d/%m} {txt}")
        elif quando > corte:
            proximas.append(f"{quando:%d/%m} {txt} (aplicada depois que este começou)")
    aplicadas = {str(x.get("depois") or "") for x in m.get("mudancas") or []}
    for p in m.get("propostas") or []:
        if p.get("titulo") and p["titulo"] not in aplicadas:
            proximas.append(f"proposta: {p['titulo'][:110]}")
    return entraram[-6:], proximas[:6]


def texto(ficha, pronto=True):
    ficha = Path(ficha)
    nuvem = _ler(ficha / "nuvem.json", {})
    titulo = nuvem.get("titulo_original") or ficha.name
    try:  # nuvem.json às vezes vem com acento quebrado (utf-8 lido como latin-1)
        titulo = titulo.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    ini, fim = _inicio(ficha), _fim(ficha)
    linhas = [f"🎥🎥 <b>VÍDEO LONGO {'PRONTO' if pronto and fim else 'EM PRODUÇÃO'}</b>", f"{titulo[:110]}"]
    if ini and fim:
        linhas.append(f"⏱ Levou {_h((fim - ini).total_seconds())} (começou {ini:%d/%m %H:%M}, ficou pronto {fim:%d/%m %H:%M})")
    elif ini:
        med = media_render()
        linhas.append(f"⏱ Começou {ini:%d/%m %H:%M}" + (f"; previsão de ficar pronto ~{ini + timedelta(seconds=med):%d/%m %H:%M} "
                                                         f"(média dos últimos: {_h(med)})" if med else ""))
    dur = _ler(ficha / "render.json", {}).get("duracao_s") or next(
        (p.get("duracao_s") for p in _ler(POSTADOS, {}).get("postados", []) if p.get("nome") == ficha.name), None)
    if dur:
        linhas.append(f"📏 Duração do vídeo: {_h(dur)}")
    onde, link = destino(ficha)
    linhas.append(f"📍 Onde: {onde}" + (f"\n🔗 {link}" if link else ""))
    entraram, proximas = melhorias(ini)
    if entraram:
        linhas.append("🆕 Atualizações que ENTRARAM neste vídeo:\n" + "\n".join(f"- {x}" for x in entraram))
    if proximas:
        linhas.append("⏭ Ficam pro PRÓXIMO vídeo:\n" + "\n".join(f"- {x}" for x in proximas))
    return "\n".join(linhas)


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    alvo = sys.argv[1] if len(sys.argv) > 1 else None
    pasta = Path(alvo) if alvo and Path(alvo).exists() else next(
        (p for p in sorted(FICHAS.glob(f"{alvo or ''}*/render.json"), key=lambda x: x.stat().st_mtime)[-1:]), None)
    print(texto(pasta.parent if pasta and pasta.name == "render.json" else pasta))
