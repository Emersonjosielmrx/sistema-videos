"""Testes pra fila.py - verifica que o fix não quebra as regras existentes."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fila import pode_postar

def test_canal_parado_sai_ja():
    """Canal sem post há mais de parado_h deve postar imediatamente."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22], "parado_h": 24}
    agora = datetime(2026, 10, 27, 18, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    # Último post há 25 horas
    ups = [agora - timedelta(hours=25)]

    pode, motivo = pode_postar(info, ups, agora)
    assert pode, f"Canal parado deveria postar, mas: {motivo}"
    assert "parado" in motivo.lower()
    print("✓ Canal parado sai já")

def test_intervalo_minimo():
    """Respeita intervalo mínimo entre uploads."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22], "intervalo_h": 2}
    agora = datetime(2026, 10, 27, 18, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    # Último post há 1.5 horas
    ups = [agora - timedelta(hours=1.5)]

    pode, motivo = pode_postar(info, ups, agora)
    assert not pode, f"Deveria respeitar intervalo, mas retornou: {pode}"
    assert "último há" in motivo
    print("✓ Respeita intervalo mínimo")

def test_teto_dia_com_agendados():
    """Teto do dia conta uploads já feitos E agendados pra hoje."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22], "max_dia": 3, "intervalo_h": 2}
    agora = datetime(2026, 10, 27, 18, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    # 2 uploads hoje (1 no passado, 1 agendado pra daqui 2h) + 1 amanhã
    ups = [
        agora - timedelta(hours=3),  # hoje, passado
        agora + timedelta(hours=2),   # hoje, agendado
        agora + timedelta(days=1)     # amanhã, agendado
    ]

    pode, motivo = pode_postar(info, ups, agora)
    assert pode, f"Deveria poder postar (2/3 hoje), mas: {motivo}"
    print("✓ Teto do dia conta agendados pra hoje")

def test_teto_dia_atingido():
    """Não posta se já atingiu max_dia."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22], "max_dia": 3, "intervalo_h": 2}
    agora = datetime(2026, 10, 27, 18, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    # 3 uploads hoje (2 passados, 1 agendado)
    ups = [
        agora - timedelta(hours=6),
        agora - timedelta(hours=3),
        agora + timedelta(hours=2)
    ]

    pode, motivo = pode_postar(info, ups, agora)
    assert not pode, f"Não deveria postar (3/3 hoje), mas retornou: {pode}"
    assert "já subiram 3 hoje" in motivo
    print("✓ Respeita teto do dia")

def test_horario_pico():
    """Só posta no horário de pico."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22], "intervalo_h": 2}
    # Fora do pico (16h)
    agora_fora = datetime(2026, 10, 27, 16, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ups = [agora_fora - timedelta(hours=3)]

    pode, motivo = pode_postar(info, ups, agora_fora)
    assert not pode, f"Não deveria postar fora do pico, mas: {pode}"
    assert "fora do pico" in motivo

    # Dentro do pico (18h)
    agora_dentro = datetime(2026, 10, 27, 18, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    pode, motivo = pode_postar(info, ups, agora_dentro)
    assert pode, f"Deveria postar no pico, mas: {motivo}"
    print("✓ Respeita horário de pico")

def test_bug_agendado_futuro():
    """FIX PRINCIPAL: agendados futuros não bloqueiam intervalo (bug do -144h)."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22], "intervalo_h": 2}
    agora = datetime(2026, 10, 27, 18, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    # Último REAL há 3h, mas tem agendado pra daqui 6 dias
    ups = [
        agora - timedelta(hours=3),      # último real
        agora + timedelta(days=6)        # agendado futuro (bug causava -144h)
    ]

    pode, motivo = pode_postar(info, ups, agora)
    assert pode, f"Deveria poder postar (último há 3h), mas: {motivo}"
    assert "-" not in motivo, f"Motivo tem horas negativas: {motivo}"
    assert "pico" in motivo.lower()
    print("✓ FIX: agendados futuros não quebram cálculo de intervalo")

def test_agendado_futuro_conta_teto():
    """Agendados futuros NÃO contam pro teto do dia (só os de hoje)."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22], "max_dia": 3, "intervalo_h": 2}
    agora = datetime(2026, 10, 27, 18, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    # 2 hoje + 5 agendados pra semana que vem
    ups = [
        agora - timedelta(hours=6),
        agora - timedelta(hours=3),
        agora + timedelta(days=3),
        agora + timedelta(days=4),
        agora + timedelta(days=5),
        agora + timedelta(days=6),
        agora + timedelta(days=7)
    ]

    pode, motivo = pode_postar(info, ups, agora)
    assert pode, f"Deveria poder postar (2/3 hoje), mas: {motivo}"
    print("✓ Agendados futuros não contam no teto do dia")

def test_teto_override():
    """Parâmetro teto sobrescreve max_dia."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22], "max_dia": 3, "intervalo_h": 2}
    agora = datetime(2026, 10, 27, 18, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    # 1 upload hoje
    ups = [agora - timedelta(hours=3)]

    # Com teto=1, não pode mais
    pode, motivo = pode_postar(info, ups, agora, teto=1)
    assert not pode, f"Teto=1 deveria bloquear, mas: {pode}"

    # Com teto=5, pode
    pode, motivo = pode_postar(info, ups, agora, teto=5)
    assert pode, f"Teto=5 deveria permitir, mas: {motivo}"
    print("✓ Parâmetro teto funciona")

def test_canal_vazio():
    """Canal sem uploads deve postar (considera parado)."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 18, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ups = []

    pode, motivo = pode_postar(info, ups, agora)
    assert pode, f"Canal vazio deveria postar, mas: {motivo}"
    print("✓ Canal vazio posta")

def test_cenario_real_bug():
    """Cenário exato do bug: 18/10 19:02 subiu, depois nada por -142h."""
    info = {"fuso": "America/New_York", "pico": [17, 22], "intervalo_h": 2, "max_dia": 3}
    # 18/10 às 19:02 subiu
    ultimo_real = datetime(2026, 10, 18, 19, 2, tzinfo=ZoneInfo("America/New_York"))
    # 18/10 às 21:40 tentou de novo (2h38 depois)
    agora = datetime(2026, 10, 18, 21, 40, tzinfo=ZoneInfo("America/New_York"))
    # Tinha agendado futuro que causou -142h
    agendado_futuro = agora + timedelta(hours=144)

    ups = [ultimo_real, agendado_futuro]

    pode, motivo = pode_postar(info, ups, agora)
    assert pode, f"Deveria poder postar (último há 2.6h, no pico), mas: {motivo}"
    assert "último há" not in motivo or "-" not in motivo
    print("✓ Cenário real do bug corrigido")

if __name__ == "__main__":
    test_canal_parado_sai_ja()
    test_intervalo_minimo()
    test_teto_dia_com_agendados()
    test_teto_dia_atingido()
    test_horario_pico()
    test_bug_agendado_futuro()
    test_agendado_futuro_conta_teto()
    test_teto_override()
    test_canal_vazio()
    test_cenario_real_bug()
    print("\n✅ Todos os testes passaram!")
