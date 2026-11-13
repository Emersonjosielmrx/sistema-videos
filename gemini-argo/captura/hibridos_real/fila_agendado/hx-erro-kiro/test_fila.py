"""Testes para pode_postar() - verifica todas as regras e o bug de vídeos agendados."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fila import pode_postar

def test_canal_parado_sem_videos():
    """Canal vazio: deve subir já."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    pode, motivo = pode_postar(info, [], agora_la=agora)
    assert pode, f"Esperava True, got {motivo}"
    assert "parado" in motivo
    print("✓ Canal vazio: sai já")

def test_canal_parado_ultimo_video_antigo():
    """Último vídeo há mais de 24h: deve subir já."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ultimo = agora - timedelta(hours=25)
    pode, motivo = pode_postar(info, [ultimo], agora_la=agora)
    assert pode, f"Esperava True, got {motivo}"
    assert "parado" in motivo
    print("✓ Canal parado (>24h): sai já")

def test_intervalo_minimo_nao_respeitado():
    """Último vídeo há 1h (< 2h de intervalo): não deve subir."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ultimo = agora - timedelta(hours=1)
    pode, motivo = pode_postar(info, [ultimo], agora_la=agora)
    assert not pode, f"Esperava False, got {motivo}"
    assert "último há" in motivo
    assert "1.0 h" in motivo
    print("✓ Intervalo mínimo não respeitado: não sobe")

def test_intervalo_minimo_respeitado():
    """Último vídeo há 3h (> 2h), no pico: deve subir."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ultimo = agora - timedelta(hours=3)
    pode, motivo = pode_postar(info, [ultimo], agora_la=agora)
    assert pode, f"Esperava True, got {motivo}"
    assert "pico" in motivo
    print("✓ Intervalo respeitado + pico: sobe")

def test_teto_dia_atingido():
    """Já subiram 3 vídeos hoje (max_dia=3): não deve subir."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ups = [
        datetime(2026, 10, 27, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
        datetime(2026, 10, 27, 14, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
        datetime(2026, 10, 27, 17, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
    ]
    pode, motivo = pode_postar(info, ups, agora_la=agora)
    assert not pode, f"Esperava False, got {motivo}"
    assert "3 hoje" in motivo
    print("✓ Teto do dia atingido: não sobe")

def test_fora_do_pico():
    """Fora do horário de pico: não deve subir."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 15, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ultimo = agora - timedelta(hours=3)
    pode, motivo = pode_postar(info, [ultimo], agora_la=agora)
    assert not pode, f"Esperava False, got {motivo}"
    assert "fora do pico" in motivo
    print("✓ Fora do pico: não sobe")

def test_bug_video_agendado_futuro():
    """BUG ORIGINAL: vídeo agendado no futuro não deve bloquear canal parado."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    # Último vídeo publicado há 30h (canal parado), mas tem um agendado daqui a 6 dias
    ultimo_real = agora - timedelta(hours=30)
    agendado_futuro = agora + timedelta(days=6)
    pode, motivo = pode_postar(info, [ultimo_real, agendado_futuro], agora_la=agora)
    assert pode, f"Esperava True (canal parado), got {motivo}"
    assert "parado" in motivo
    print("✓ BUG FIXADO: vídeo agendado no futuro não bloqueia 'canal parado'")

def test_video_agendado_conta_no_teto():
    """Vídeo agendado para hoje deve contar no teto do dia."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ups = [
        datetime(2026, 10, 27, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),  # publicado
        datetime(2026, 10, 27, 14, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),  # publicado
        datetime(2026, 10, 27, 23, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),  # agendado pra hoje
    ]
    pode, motivo = pode_postar(info, ups, agora_la=agora)
    assert not pode, f"Esperava False (teto), got {motivo}"
    assert "3 hoje" in motivo
    print("✓ Vídeo agendado conta no teto do dia")

def test_video_agendado_nao_afeta_intervalo():
    """Vídeo agendado no futuro não deve bloquear por intervalo."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ultimo_real = agora - timedelta(hours=3)  # há 3h (> 2h de intervalo)
    agendado_futuro = agora + timedelta(hours=2)  # daqui a 2h
    pode, motivo = pode_postar(info, [ultimo_real, agendado_futuro], agora_la=agora)
    assert pode, f"Esperava True, got {motivo}"
    assert "pico" in motivo
    print("✓ Vídeo agendado no futuro não bloqueia por intervalo")

def test_teto_customizado():
    """Teto customizado via parâmetro deve sobrescrever max_dia."""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22], "max_dia": 3}
    agora = datetime(2026, 10, 27, 19, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    ups = [
        datetime(2026, 10, 27, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
        datetime(2026, 10, 27, 14, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
    ]
    # Com max_dia=3, ainda poderia subir 1. Mas teto=2 bloqueia
    pode, motivo = pode_postar(info, ups, agora_la=agora, teto=2)
    assert not pode, f"Esperava False, got {motivo}"
    assert "2 hoje" in motivo
    print("✓ Teto customizado funciona")

def test_config_customizada():
    """Configurações customizadas por língua (intervalo_h, parado_h)."""
    info = {"fuso": "Asia/Tokyo", "pico": [18, 23], "intervalo_h": 4, "parado_h": 48}
    agora = datetime(2026, 10, 27, 20, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
    # Último há 30h: com parado_h=48, não está parado ainda
    ultimo = agora - timedelta(hours=30)
    pode, motivo = pode_postar(info, [ultimo], agora_la=agora)
    assert pode, f"Esperava True (intervalo 30h > 4h), got {motivo}"
    assert "pico" in motivo

    # Último há 3h: com intervalo_h=4, ainda não pode
    ultimo2 = agora - timedelta(hours=3)
    pode2, motivo2 = pode_postar(info, [ultimo2], agora_la=agora)
    assert not pode2, f"Esperava False (3h < 4h), got {motivo2}"
    assert "último há 3.0 h" in motivo2
    print("✓ Configurações customizadas por língua funcionam")

if __name__ == "__main__":
    print("=== Testando fila.py ===\n")
    test_canal_parado_sem_videos()
    test_canal_parado_ultimo_video_antigo()
    test_intervalo_minimo_nao_respeitado()
    test_intervalo_minimo_respeitado()
    test_teto_dia_atingido()
    test_fora_do_pico()
    test_bug_video_agendado_futuro()
    test_video_agendado_conta_no_teto()
    test_video_agendado_nao_afeta_intervalo()
    test_teto_customizado()
    test_config_customizada()
    print("\n✅ Todos os testes passaram!")
