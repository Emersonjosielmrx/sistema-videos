"""Testes para _numero do youtube_http.py"""
from youtube_http import _numero


def test_casos():
    casos = [
        # Formato pt-BR com vírgula decimal
        ("3,4 mi de inscritos", 3_400_000),
        ("1,2 mil visualizações", 1_200),
        ("2,5 bi", 2_500_000_000),

        # Formato EN com ponto decimal
        ("2.3M views", 2_300_000),
        ("1.5K", 1_500),
        ("4.7B", 4_700_000_000),

        # Números sem multiplicador (milhares separados)
        ("12.345 visualizações", 12_345),  # pt-BR: ponto como separador de milhar
        ("1.234.567", 1_234_567),  # pt-BR
        ("1,234,567", 1_234_567),  # EN: vírgula como separador de milhar

        # Casos simples
        ("3399999", 3_399_999),
        ("mil", 1_000),
        ("2 mi", 2_000_000),

        # Casos extremos do painel/YouTube
        ("3.399.999 inscritos", 3_399_999),  # painel brasileiro
        ("3,4 mi de inscritos", 3_400_000),  # YouTube português
        ("3.4M subscribers", 3_400_000),     # YouTube inglês
    ]

    falhas = []
    for txt, esperado in casos:
        resultado = _numero(txt)
        if resultado != esperado:
            falhas.append(f"  '{txt}' → {resultado} (esperado {esperado:,})")
        else:
            print(f"✓ '{txt}' → {resultado:,}")

    if falhas:
        print("\n❌ FALHAS:")
        for f in falhas:
            print(f)
        return False
    else:
        print("\n✅ TODOS OS TESTES PASSARAM")
        return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if test_casos() else 1)
