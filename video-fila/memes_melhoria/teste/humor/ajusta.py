# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    if b.strip() in s and a not in s:
        return  # já aplicado
    assert s.count(a) == 1, ("ancora", a[:80], s.count(a))
    s = s.replace(a, b)
rep('''    cada, cada_temp = _num("HUMOR_CADA", 20), _num("HUMOR_TEMPERO_CADA", 25)''',
    '''    # 26/11 (teste em 2 roteiros reais): com 20/25 saiu 1 reação a cada ~37 frases (~3,5 min). Com o teto de começo
    # repetido, 14/20 fica ~1 a cada 2 min sem cansar (os de referência reagem bem mais: 1 a cada 3-5 frases).
    cada, cada_temp = _num("HUMOR_CADA", 14), _num("HUMOR_TEMPERO_CADA", 20)''')
rep('''        j = _json(resp)
        if not j or not isinstance(j.get("ops"), list):
            recusa("resposta sem JSON")
            continue''', '''        j = _json(resp)
        if not j or not isinstance(j.get("ops"), list):  # 26/11: 1 de cada ~4 blocos vinha sem JSON — tenta 1x mais
            try:
                j = _json(gerar(_prompt(bloco, ini, perfil, gag, ja, max_ops, max_temp, viradas < max_viradas, gastas)
                                + "\\nIMPORTANTE: responda APENAS o JSON, começando com { e terminando com }.", _SISTEMA))
            except Exception:  # noqa: BLE001
                j = None
        if not j or not isinstance(j.get("ops"), list):
            recusa("resposta sem JSON")
            continue''')
rep('''def _cena_triste(frases, i):
    viz = " ".join(frases[max(0, i - 1): i + 2])''', '''_RX_FIGURADO = re.compile(r"(?i)\\b(morr\\w*|mat\\w*) (de|a) (medo|rir|vergonha|saudade|fome|sono|curiosidade|"
                          r"t[eé]dio|inveja|raiva|calor|frio|ci[uú]mes?)\\b")


def _cena_triste(frases, i):
    viz = _RX_FIGURADO.sub(" ", " ".join(frases[max(0, i - 1): i + 2]))''')
rep('''    out_f, out_t = [], []
    for i, (f, t) in enumerate(zip(frases, tempos)):
        if i in temperar:
            f = _temperar(f, *temperar[i])''', '''    try:
        from viralizador import anti_ban
    except Exception:  # noqa: BLE001
        def anti_ban(x):
            return x
    out_f, out_t = [], []
    for i, (f, t) in enumerate(zip(frases, tempos)):
        if i in temperar:
            f = anti_ban(_temperar(f, *temperar[i]))''')
rep('''        for s in inserir.get(i, []):
            out_f.append(s)''', '''        for s in inserir.get(i, []):
            out_f.append(anti_ban(s))''')
rep('''Densidade (padrão, por frase de roteiro ~5-6 s): 1 reação a cada HUMOR_CADA=20 frases (~1 a cada 2 min) e 1 tempero a
cada HUMOR_TEMPERO_CADA=25.''', '''Densidade (padrão, por frase de roteiro ~5-6 s): até 1 reação a cada HUMOR_CADA=14 frases (~1 a cada 2 min na prática)
e 1 tempero a cada HUMOR_TEMPERO_CADA=20.''')
compile(s, p, "exec")
open(p, "w", encoding="utf-8").write(s)
print("ajustes ok")
