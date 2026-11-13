"""teste_teto_frases_longo.py — teto de frases do roteiro LONGO (LONGOS_MELHORIAS "A FAZER 10/11 (a)").
Não chama IA nem rede: a resposta do modelo é de mentira.   python teste_teto_frases_longo.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anime_script as a  # noqa: E402


def _rodar(dur_min, teto):
    """Roda rewrite_longo_com_tempo com um modelo de mentira; devolve (alvo pedido, prompts, frases, tempos)."""
    dur = dur_min * 60
    cues = [[t, f"fala numero {t} do personagem contando o que aconteceu na cena de agora"] for t in range(0, dur, 4)]
    alvo = max(40, round(dur * 0.99 / 6.6))
    prompts = []

    def falso(prompt, **_k):
        prompts.append(prompt)
        ini = int(re.search(r"só aumentam, entre (\d+) e \d+", prompt).group(1))
        return "\n".join(f"[{ini + k}s] O nosso garoto segue em frente na cena {k}." for k in range(8)) + f"\n[{ini + 8}s] Vazio."

    a.TETO_FRASES_LONGO = teto
    a.claude_client.is_available = lambda: True
    a.claude_client.generate_text = falso
    a._cache_get = lambda *_a, **_k: None
    a._cache_put = lambda *_a, **_k: None
    frases, tempos = a.rewrite_longo_com_tempo(cues, alvo, dur)
    return alvo, prompts, frases, tempos


def test_alvo_com_teto():
    a.TETO_FRASES_LONGO = 1500
    assert a.alvo_com_teto(1952) == (1500, True)      # HZRT, 206 min: era 13 h de render
    assert a.alvo_com_teto(1500) == (1500, False)
    assert a.alvo_com_teto(900) == (900, False)       # longo normal: nada muda
    a.TETO_FRASES_LONGO = 0
    assert a.alvo_com_teto(1952) == (1952, False)     # LONGO_TETO_FRASES=0 desliga


def test_fonte_de_3h_cabe_na_sessao():
    alvo, prompts, frases, tempos = _rodar(206, 1500)
    assert alvo > 1800 and prompts
    blocos = len(prompts)
    assert blocos <= round(1500 / 30) + 1, blocos      # nº de blocos sai do teto, não do alvo original
    assert all("NO MÁXIMO" in p for p in prompts)
    limite = int(prompts[0].split("NO MÁXIMO ")[1].split(" ")[0])
    assert blocos * limite * 24 <= 11.5 * 3600, (blocos, limite)   # o pior caso cabe nas 11,5 h a 24 s/frase
    assert frases and tempos == sorted(tempos) and tempos[-1] > 200 * 60   # ainda cobre o vídeo até o fim
    assert any(f.endswith("Vazio.") and len(f) > 12 for f in frases) and "Vazio." not in frases   # curta gruda, não some


def test_longo_normal_nao_muda():
    _alvo, prompts, frases, _t = _rodar(90, 1500)
    assert frases and not any("NO MÁXIMO" in p for p in prompts)   # segue "sem travas" (dona 04/11)
    _alvo, prompts, _f, _t = _rodar(206, 0)
    assert not any("NO MÁXIMO" in p for p in prompts)              # teto desligado = como era


if __name__ == "__main__":
    falhas = 0
    for nome, f in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                f()
                print(f"ok    {nome}")
            except AssertionError as e:
                falhas += 1
                print(f"FALHA {nome}: {e!r}")
    print("tudo certo" if not falhas else f"{falhas} teste(s) falharam")
    sys.exit(1 if falhas else 0)
