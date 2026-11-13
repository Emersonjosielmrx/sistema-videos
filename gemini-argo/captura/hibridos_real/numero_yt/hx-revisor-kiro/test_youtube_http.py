"""Testes para _numero() do youtube_http.py"""
from youtube_http import _numero


def test_numero():
    """Testa todos os formatos de números do YouTube"""
    casos = [
        # Casos reportados com problema
        ("3,4 mi de inscritos", 3_400_000, "Canal com 3.4M inscritos (pt-BR)"),
        ("2.3M views", 2_300_000, "Vídeo com 2.3M views (en)"),
        ("3.399.999", 3_399_999, "Número exato sem multiplicador"),

        # Formatos pt-BR com multiplicador
        ("1,2 mil visualizações", 1_200, "1.2k em pt-BR"),
        ("5,7 mi", 5_700_000, "5.7M em pt-BR"),
        ("2,1 bi", 2_100_000_000, "2.1B em pt-BR"),

        # Formatos en com multiplicador
        ("1.2K views", 1_200, "1.2K em inglês"),
        ("5.7M subscribers", 5_700_000, "5.7M em inglês"),
        ("2.1B views", 2_100_000_000, "2.1B em inglês"),

        # Números sem multiplicador (pt-BR)
        ("12.345", 12_345, "Número com separador de milhares pt-BR"),
        ("1.234.567", 1_234_567, "Milhão em pt-BR"),

        # Números sem multiplicador (en)
        ("12,345", 12_345, "Número com separador de milhares en"),
        ("1,234,567", 1_234_567, "Milhão em inglês"),

        # Números redondos
        ("1 mil", 1_000, "1 mil exato"),
        ("2 mi", 2_000_000, "2 mi exato"),
        ("3M", 3_000_000, "3M exato"),
        ("4K", 4_000, "4K exato"),

        # Casos especiais
        ("123", 123, "Número simples"),
        ("nenhum inscrito", 0, "Nenhum"),
        ("sem visualizações", 0, "Sem"),
        ("", None, "String vazia"),
        (None, None, "None"),
    ]

    falhas = []
    for entrada, esperado, desc in casos:
        resultado = _numero(entrada)
        status = "✓" if resultado == esperado else "✗"
        print(f"{status} {desc}")
        print(f"  Entrada: {entrada!r}")
        print(f"  Esperado: {esperado:,} | Obtido: {resultado:,}" if resultado is not None and esperado is not None
              else f"  Esperado: {esperado} | Obtido: {resultado}")

        if resultado != esperado:
            falhas.append((desc, entrada, esperado, resultado))
        print()

    if falhas:
        print(f"\n❌ {len(falhas)} teste(s) falharam:")
        for desc, entrada, esperado, resultado in falhas:
            print(f"  • {desc}: {entrada!r} → esperado {esperado}, obtido {resultado}")
        return False
    else:
        print(f"\n✅ Todos os {len(casos)} testes passaram!")
        return True


if __name__ == "__main__":
    import sys
    sucesso = test_numero()
    sys.exit(0 if sucesso else 1)
