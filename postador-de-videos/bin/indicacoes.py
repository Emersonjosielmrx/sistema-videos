"""indicacoes.py — um canal indica o canal parceiro da dupla (dona 23/10/2026: "pode fazer a questão das colabs").

Duplas e frases em config/indicacoes.json. Entra em 2 lugares:
  - descrição: politica.postar_youtube (ponto único de todos os projetos), linha antes do bloco de hashtags;
  - comentário fixado: youtube_studio_extras (--comentario), frase no fim do texto.
Sem dupla, idioma diferente de pt, parceiro sem @ ou fora do ar (suspenso/desativado/pausado) = nada muda.
O "vídeo relacionado" do Short NÃO serve: o Studio só lista vídeos do próprio canal.

    python bin\\indicacoes.py            # mostra as duplas e se cada parceiro está valendo agora
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "indicacoes.json"
CANAIS = ROOT / "config" / "canais.json"


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _canais():
    return _ler(CANAIS, {}).get("canais", {})


def _slug_do_cred(cred_id):
    """slug do canal desta credencial (ou de um alias dela)."""
    try:
        import politica
        ids = politica.creds_mesmo_canal(cred_id)
    except Exception:  # noqa: BLE001
        ids = {cred_id}
    for k, c in _canais().items():
        if ids & set(c.get("creds") or []) or cred_id in (k, c.get("slug")) or \
                " ".join(str(cred_id).split()).casefold() == " ".join(str(c.get("nome") or "").split()).casefold():
            return c.get("slug") or k
    return None


def _saudavel(c):
    """Parceiro pode ser indicado: nenhuma credencial dele bloqueada (suspenso/token morto/desativado/pausado)."""
    try:
        import politica
        st = politica._status()
        return not any(politica.motivo_bloqueio({"id": cid, "nome": c.get("nome")}, st) for cid in c.get("creds") or [])
    except Exception:  # noqa: BLE001  sem como conferir = não indica
        return False


def parceiro(cred_ou_slug):
    """{'slug', 'nome', 'handle'} do parceiro valendo agora, ou None."""
    cfg = _ler(CFG, {})
    if not cfg.get("ligado"):
        return None
    slug = _slug_do_cred(cred_ou_slug) or cred_ou_slug
    canais = {(c.get("slug") or k): c for k, c in _canais().items()}
    eu = canais.get(slug)
    if not eu or eu.get("idioma") != "pt":
        return None
    for dupla in cfg.get("duplas") or []:
        if slug in dupla:
            outro = canais.get(next((x for x in dupla if x != slug), ""))
            if outro and outro.get("handle") and outro.get("idioma") == "pt" and _saudavel(outro):
                return {"slug": outro.get("slug"), "nome": outro.get("nome"), "handle": outro["handle"]}
    return None


def _frase(lista, handle, semente):
    if not lista:
        return None
    i = int(hashlib.md5((semente or "").encode()).hexdigest(), 16) % len(lista)  # varia por vídeo, fixa por título
    return lista[i].format(handle=handle)


def na_descricao(cred_ou_slug, descricao, semente=""):
    """Descrição com a linha do parceiro antes do bloco final de hashtags (descrição que termina em #hashtag abre a
    lista de sugestões do Studio e trava o clique). Já indicado ou sem parceiro: devolve igual."""
    p = parceiro(cred_ou_slug)
    descricao = descricao or ""
    if not p or p["handle"].casefold() in descricao.casefold():
        return descricao
    linha = _frase(_ler(CFG, {}).get("frases_descricao"), p["handle"], semente)
    if not linha:
        return descricao
    m = re.search(r"(\n\s*)?((?:#[\wÀ-ɏ]+[ \t]*)+)\s*$", descricao)
    if m:
        corpo, tags = descricao[:m.start()].rstrip(), m.group(2).strip()
        novo = f"{corpo}\n\n{linha}\n\n{tags}" if corpo else f"{linha}\n\n{tags}"
    else:
        novo = f"{descricao.rstrip()}\n\n{linha}" if descricao.strip() else linha
    return novo[:4900] if len(novo) <= 4900 else descricao


def no_comentario(cred_ou_slug, texto, semente=""):
    p = parceiro(cred_ou_slug)
    if not p or not texto or p["handle"].casefold() in texto.casefold():
        return texto
    frase = _frase(_ler(CFG, {}).get("frases_comentario"), p["handle"], semente or texto)
    novo = f"{texto.rstrip()}\n\n{frase}" if frase else texto
    return novo if len(novo) <= 600 else texto


def main():
    cfg = _ler(CFG, {})
    print("ligado" if cfg.get("ligado") else "DESLIGADO")
    for a, b in cfg.get("duplas") or []:
        for x, y in ((a, b), (b, a)):
            p = parceiro(x)
            print(f"  {x:24} -> {p['handle'] if p else f'(nada: {y} sem @, fora do ar ou idioma diferente)'}")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
