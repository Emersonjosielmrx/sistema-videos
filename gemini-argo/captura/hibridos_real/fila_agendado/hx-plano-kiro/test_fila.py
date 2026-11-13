"""Testes para fila.py — verifica todas as regras de postagem."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fila import pode_postar

def test_canal_parado_sem_uploads():
    """Canal sem uploads: sobe já."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    pode, motivo = pode_postar(info, [], agora)
    assert pode, f"Canal vazio deveria postar, mas: {motivo}"
    assert "parado" in motivo.lower()
    print(f"✓ Canal vazio: {motivo}")

def test_canal_parado_ultimo_muito_antigo():
    """Canal com último upload há mais de 24h: sobe já."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ultimo = agora - timedelta(hours=25)
    pode, motivo = pode_postar(info, [ultimo], agora)
    assert pode, f"Canal parado (25h) deveria postar, mas: {motivo}"
    assert "parado" in motivo.lower()
    print(f"✓ Canal parado 25h: {motivo}")

def test_bug_agendado_futuro():
    """BUG PRINCIPAL: Canal com upload passado + agendado futuro.
    Deve considerar só o passado pra 'canal parado' e 'intervalo'."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    # Upload real há 3 horas (dentro do parado_h=24)
    ultimo_real = agora - timedelta(hours=3)
    # Agendado pro futuro (amanhã)
    agendado_futuro = agora + timedelta(hours=24)

    pode, motivo = pode_postar(info, [ultimo_real, agendado_futuro], agora)
    # Último real há 3h > intervalo 2h, no pico, então DEVE POSTAR
    assert pode, f"Deveria postar (último real há 3h, no pico), mas: {motivo}"
    print(f"✓ Bug agendado futuro corrigido: {motivo}")

def test_intervalo_minimo():
    """Último upload há 1h: não sobe (intervalo 2h)."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ultimo = agora - timedelta(hours=1)
    pode, motivo = pode_postar(info, [ultimo], agora)
    assert not pode, f"Não deveria postar (intervalo 1h < 2h), mas postou: {motivo}"
    assert "último há 1.0 h" in motivo
    print(f"✓ Intervalo 1h bloqueado: {motivo}")

def test_intervalo_ok():
    """Último upload há 2.5h, no pico: sobe."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ultimo = agora - timedelta(hours=2.5)
    pode, motivo = pode_postar(info, [ultimo], agora)
    assert pode, f"Deveria postar (2.5h > 2h, no pico), mas: {motivo}"
    print(f"✓ Intervalo 2.5h ok: {motivo}")

def test_teto_diario():
    """3 uploads hoje: não sobe (max_dia=3)."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    hoje_9h = agora.replace(hour=9)
    hoje_13h = agora.replace(hour=13)
    # Último há 3h (passa o intervalo de 2h)
    hoje_16h = agora.replace(hour=16)
    pode, motivo = pode_postar(info, [hoje_9h, hoje_13h, hoje_16h], agora)
    assert not pode, f"Não deveria postar (3 uploads hoje), mas: {motivo}"
    assert "já subiram 3 hoje" in motivo
    print(f"✓ Teto diário (3/3): {motivo}")

def test_teto_com_agendado_hoje():
    """Teto conta também agendados pra hoje (no futuro)."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    hoje_9h = agora.replace(hour=9)
    # Último passado há 3h (passa intervalo)
    hoje_16h = agora.replace(hour=16)
    # Agendado pra hoje às 21h (futuro)
    hoje_21h = agora.replace(hour=21)
    pode, motivo = pode_postar(info, [hoje_9h, hoje_16h, hoje_21h], agora)
    assert not pode, f"Não deveria postar (2 passados + 1 agendado hoje = 3), mas: {motivo}"
    assert "já subiram 3 hoje" in motivo
    print(f"✓ Teto inclui agendado hoje: {motivo}")

def test_fora_pico():
    """Fora do horário de pico: não sobe."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 15, 30, tzinfo=ZoneInfo("America/Sao_Paulo"))  # 15:30
    ultimo = agora - timedelta(hours=3)
    pode, motivo = pode_postar(info, [ultimo], agora)
    assert not pode, f"Não deveria postar (fora do pico 17-22h), mas: {motivo}"
    assert "fora do pico" in motivo.lower()
    print(f"✓ Fora do pico: {motivo}")

def test_pico_borda_inicio():
    """17h exato: dentro do pico."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 17, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ultimo = agora - timedelta(hours=3)
    pode, motivo = pode_postar(info, [ultimo], agora)
    assert pode, f"17h deveria estar no pico [17, 22), mas: {motivo}"
    print(f"✓ Pico 17h (início): {motivo}")

def test_pico_borda_fim():
    """22h exato: fora do pico (intervalo [17, 22))."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 22, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ultimo = agora - timedelta(hours=3)
    pode, motivo = pode_postar(info, [ultimo], agora)
    assert not pode, f"22h deveria estar fora do pico [17, 22), mas: {motivo}"
    print(f"✓ Pico 22h (fim, fora): {motivo}")

def test_teto_customizado():
    """Teto customizado via parâmetro sobrescreve max_dia."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22], "max_dia": 3}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    hoje_9h = agora.replace(hour=9)
    hoje_13h = agora.replace(hour=13)
    # Teto=2: já tem 2, não sobe
    pode, motivo = pode_postar(info, [hoje_9h, hoje_13h], agora, teto=2)
    assert not pode, f"Teto=2, já tem 2, não deveria postar: {motivo}"
    print(f"✓ Teto customizado (2): {motivo}")

def test_cenario_real_log():
    """Simula o cenário do log: último real em 18/10, agendado no futuro.
    Em 20/10 às 19h deveria detectar canal parado (último há 49h > 24h)."""
    info = {"fuso": "UTC", "pico": [17, 22]}
    # Agora: 2026-10-20 19:10 UTC
    agora = datetime(2026, 10, 20, 19, 10, tzinfo=ZoneInfo("UTC"))
    # Último upload real: 2026-10-18 19:02 (há ~48h)
    ultimo_real = datetime(2026, 10, 18, 19, 2, tzinfo=ZoneInfo("UTC"))
    # Agendado futuro (ex: 2026-10-24)
    agendado = datetime(2026, 10, 24, 20, 0, tzinfo=ZoneInfo("UTC"))

    pode, motivo = pode_postar(info, [ultimo_real, agendado], agora)
    # Canal há 48h sem upload real > 24h: canal parado, DEVE POSTAR
    assert pode, f"Canal parado (48h > 24h) deveria postar, mas: {motivo}"
    assert "parado" in motivo.lower()
    print(f"✓ Cenário real do log: {motivo}")

if __name__ == "__main__":
    test_canal_parado_sem_uploads()
    test_canal_parado_ultimo_muito_antigo()
    test_bug_agendado_futuro()
    test_intervalo_minimo()
    test_intervalo_ok()
    test_teto_diario()
    test_teto_com_agendado_hoje()
    test_fora_pico()
    test_pico_borda_inicio()
    test_pico_borda_fim()
    test_teto_customizado()
    test_cenario_real_log()
    print("\n🎉 TODOS OS TESTES PASSARAM")
