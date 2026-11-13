"""variantes.py — testes A/B/C/D… dos Shorts (Cortes), 30/10/2026.

Pedido da dona (30/10): "toda coisa que eu mudar e for uma coisa subjetiva, você cria uma variante, assim produzimos
vídeos A B C D E de vários e vemos qual se dá melhor".

Como funciona
- Cada teste tem uma chave em bin\\cortes_ajustes.json:
    "ab"  -> 2 braços (A, B);  "abc" -> 3 braços (A, B, C);  "abcd" -> 4 … (sorteio estável por vídeo)
    ["x", "y", "z"]  -> braços com nome (sorteia entre os nomes)
    "A" / "B" / "lateral" / qualquer valor fixo -> SEM teste: todo vídeo recebe esse valor
- O sorteio é md5(prefixo + id do vídeo-fonte) % N: o mesmo vídeo cai sempre no mesmo braço. Com 2 braços é idêntico
  ao sorteio antigo do anime_auto.fazer_short (ímpar = B), então os testes T3–T9 em andamento não mudam.
- O braço vai numa env (CORTES_*) que o código do efeito lê; o anime_publish grava no postar.json (campo próprio +
  dicionário "variantes"); bin\\placar_variantes.py junta com as views e diz se já dá pra decidir (FABLE D1/D3).

Ligar um teste novo com N braços
1. Registrar aqui em TESTES: prefixo (2-3 letras, NUNCA reaproveitar), env, campo do postar.json.
2. No código do efeito, ler a env: os.environ.get("CORTES_X") == "B" / "C" … (sem env = comportamento atual).
3. Em cortes_ajustes.json pôr "x": "abc" (+ linha no "historico"). Para fechar: "x": "B" (o vencedor).
Mudar o número de braços de um teste em andamento muda o sorteio dos vídeos NOVOS (os já feitos ficam como estão).
"""
import hashlib
import json
import os
from pathlib import Path

AJUSTES = Path(__file__).resolve().parent / "cortes_ajustes.json"

# chave em cortes_ajustes.json -> como sortear e onde gravar. "por": "video" (id do vídeo-fonte) ou "canal" (id do
# canal: o braço vale pro canal inteiro — usado quando o efeito é do agendamento, não do vídeo).
TESTES = {
    # T3 (27/10): palavra de impacto no centro x de lado. "ab" sorteia entre os nomes (ímpar = lateral, como antes)
    "legenda_impacto": dict(prefixo="leg", env="CORTES_LEGENDA_ESTILO", campo="legenda_estilo", padrao="centro",
                            nomes=["centro", "lateral"]),
    "gancho_meio": dict(prefixo="gm", env="CORTES_GANCHO_MEIO", campo="gancho_meio"),  # T4 frase de expectativa
    "gancho_remotion": dict(prefixo="gr", env="CORTES_GANCHO_REMOTION", campo="gancho_remotion"),  # T5
    "fx_choque": dict(prefixo="fc", env="CORTES_FX_CHOQUE", campo="fx_choque"),  # T6
    "mascote": dict(prefixo="ms", env="CORTES_MASCOTE", campo="mascote"),  # T7
    "curto": dict(prefixo="ct", env="CORTES_CURTO", campo="curto"),  # T8 (Fable D3)
    "fala_rapida": dict(prefixo="fr", env="CORTES_FALA_RAPIDA", campo="fala_rapida"),  # T9 (Fable D16)
    # 30/10 mudanças subjetivas da sessão de melhorias (docs\MELHORIAS_SHORTS_2026-10-30.md) viradas em teste:
    # T10 saudação na 1ª fala: A = tira "E aí, galera"/"Minha gente" (30/10), B = mantém (como era antes)
    "saudacao": dict(prefixo="sd", env="CORTES_SAUDACAO", campo="saudacao"),
    # T11 "NINGUÉM ESPERAVA" no título/gancho: A = liberado (texto antigo), B = proibido (30/10)
    "ninguem_esperava": dict(prefixo="ne", env="CORTES_NINGUEM_ESPERAVA", campo="ninguem_esperava"),
    # T12 horário 15-21 h de Brasília: A = ordem normal (antes de 30/10), B = vai pro fim da fila (30/10).
    # Por CANAL (parceiro_diario._ordem_horarios); o placar recalcula o braço pelo canal do ledger.
    # T13 (13/11, pesquisador): forma da 1ª frase do roteiro — anime_script._ABERTURAS. "fato" = como sempre.
    "abertura": dict(prefixo="abt", env="CORTES_ABERTURA", campo="abertura", padrao="fato",
                     nomes=["fato", "pergunta", "contraste", "custo"]),
    "horario_fraco": dict(prefixo="hf", env=None, campo="horario_fraco", por="canal"),
}

_LETRAS = "ABCDEFGHIJ"


def ajustes():
    try:
        return json.loads(AJUSTES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def opcoes(valor, nomes=None):
    """Lista de braços se o valor é um teste ("ab", "abc", lista), senão None (valor fixo)."""
    if isinstance(valor, (list, tuple)):
        return [str(v) for v in valor] if len(valor) >= 2 else None
    if isinstance(valor, str) and 2 <= len(valor) <= len(_LETRAS) and valor == "abcdefghij"[:len(valor)]:
        if nomes and len(nomes) == len(valor):
            return list(nomes)
        return list(_LETRAS[:len(valor)])
    return None


def sortear(prefixo, chave, bracos):
    """Braço estável: md5(prefixo + chave) % N. Com N = 2 é o sorteio antigo (ímpar = 2º braço)."""
    return bracos[int(hashlib.md5((prefixo + str(chave)).encode()).hexdigest(), 16) % len(bracos)]


def braco(nome_teste, chave, aj=None, padrao=None):
    """Braço do teste `nome_teste` para o vídeo (ou canal) `chave`. Lê cortes_ajustes.json se `aj` não vier.
    Teste fora do registro usa o próprio nome como prefixo. Valor fixo (sem teste) volta como está."""
    aj = ajustes() if aj is None else aj
    t = TESTES.get(nome_teste, {})
    valor = aj.get(nome_teste, t.get("padrao", "ab") if padrao is None else padrao)
    ops = opcoes(valor, t.get("nomes"))
    if not ops:
        return valor
    return sortear(t.get("prefixo", nome_teste), chave, ops)


def aplicar(video_id, aj=None):
    """anime_auto.fazer_short: sorteia todos os testes por vídeo e põe cada braço na sua env. Devolve {teste: braço}."""
    aj = ajustes() if aj is None else aj
    feito, sorteados = {}, []
    for nome, t in TESTES.items():
        if t.get("por", "video") != "video" or not t.get("env"):
            continue
        valor = aj.get(nome, t.get("padrao", "ab"))
        b = braco(nome, video_id, aj)
        os.environ[t["env"]] = "" if b is None else str(b)
        feito[nome] = b
        if opcoes(valor, t.get("nomes")):
            sorteados.append(nome)
    # só os SORTEADOS vão pro dicionário "variantes" do postar.json (valor fixo não é teste e não entra no placar)
    os.environ["CORTES_VARIANTES"] = ",".join(sorteados)
    return feito


def do_ambiente():
    """anime_publish: {teste: braço} dos testes SORTEADOS para este vídeo (env CORTES_VARIANTES do fazer_short)."""
    lista = os.environ.get("CORTES_VARIANTES")
    nomes = [n for n in lista.split(",") if n] if lista is not None else list(TESTES)
    return {n: os.environ[TESTES[n]["env"]] for n in nomes
            if n in TESTES and TESTES[n].get("env") and os.environ.get(TESTES[n]["env"])}


if __name__ == "__main__":  # python variantes.py <id> [<id> ...] — mostra os braços de cada vídeo
    import sys
    aj = ajustes()
    for vid in sys.argv[1:] or ["dQw4w9WgXcQ"]:
        print(vid, {n: braco(n, vid, aj) for n in TESTES})
