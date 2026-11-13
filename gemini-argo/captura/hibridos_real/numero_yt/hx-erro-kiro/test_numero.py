"""Testa _numero com os casos reportados e outros formatos."""
from youtube_http import _numero


def test_casos():
    casos = [
        # Casos reportados (bugs)
        ('3,4 mi de inscritos', 3_400_000, 'Canal com 3.4M inscritos (pt)'),
        ('2.3M views', 2_300_000, 'Vídeo com 2.3M views (en)'),

        # Outros formatos que já funcionavam (regressão)
        ('1,2 mil visualizações', 1_200, 'Formato pt com "mil"'),
        ('12.345 visualizações', 12345, 'Inteiro com ponto separador de milhar'),
        ('12,345 visualizações', 12345, 'Inteiro com vírgula separador de milhar'),
        ('1.234.567 visualizações', 1234567, 'Inteiro com múltiplos pontos'),
        ('5K subscribers', 5_000, 'Formato en com K'),
        ('1.5M views', 1_500_000, 'Formato en com decimal e M'),
        ('2,5 mi', 2_500_000, 'Formato pt com mi'),
        ('10 mil', 10_000, 'Inteiro com mil'),
        ('100', 100, 'Inteiro puro'),
        ('1.000', 1000, 'Mil com ponto'),
        ('1,000', 1000, 'Mil com vírgula'),

        # Edge cases
        ('1.2B views', 1_200_000_000, 'Bilhão en'),
        ('2,3 bi', 2_300_000_000, 'Bilhão pt'),
        ('999.999', 999999, 'Quase milhão com ponto'),
        ('', None, 'String vazia'),
        (None, None, 'None'),
        ('nenhum inscrito', 0, 'Zero explícito'),
    ]

    passou = 0
    falhou = 0

    for entrada, esperado, descricao in casos:
        resultado = _numero(entrada)
        if resultado == esperado:
            print(f"✓ {descricao}")
            print(f"  '{entrada}' → {resultado:,}")
            passou += 1
        else:
            print(f"✗ {descricao}")
            print(f"  '{entrada}' → {resultado:,} (esperado: {esperado:,})")
            falhou += 1

    print(f"\n{'='*60}")
    print(f"Passou: {passou}/{passou+falhou}")
    if falhou > 0:
        print(f"Falhou: {falhou}")
        return False
    else:
        print("Todos os testes passaram! ✓")
        return True


if __name__ == '__main__':
    import sys
    sys.exit(0 if test_casos() else 1)
