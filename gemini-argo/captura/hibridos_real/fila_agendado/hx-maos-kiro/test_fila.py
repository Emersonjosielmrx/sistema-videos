"""Testes para validar a correção do bug de tempo negativo no fila.py"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fila import pode_postar

def test_caso_bug_agendado_futuro():
    """Caso que causava 'último há -144 h': vídeo agendado 6 dias no futuro"""
    info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
    agora = datetime(2026, 10, 20, 19, 10, tzinfo=ZoneInfo("America/Sao_Paulo"))

    # Último publicado: 3 horas atrás
    ultimo_publicado = agora - timedelta(hours=3)
    # Agendado: 6 dias no futuro (144 horas)
    agendado_futuro = agora + timedelta(hours=144)

    ups = [ultimo_publicado, agendado_futuro]

    pode, motivo = pode_postar(info, ups, agora_la=agora)
    print(f"✓ Bug futuro: {pode} - {motivo}")
    assert pode == True, f"Deveria poder postar (último há 3h), mas retornou: {motivo}"
    assert "último há -" not in motivo, "Não deve ter tempo negativo"

def test_canal_parado_com_agendado_futuro():
    """Canal sem posts há 25h, mas tem agendado futuro - deve liberar"""
    info = {"fuso": "UTC", "pico": [17, 22], "parado_h": 24}
    agora = datetime(2026, 10, 20, 18, 0, tzinfo=ZoneInfo("UTC"))

    ultimo_publicado = agora - timedelta(hours=25)
    agendado_futuro = agora + timedelta(days=3)

    ups = [ultimo_publicado, agendado_futuro]

    pode, motivo = pode_postar(info, ups, agora_la=agora)
    print(f"✓ Canal parado c/ agendado: {pode} - {motivo}")
    assert pode == True, "Canal parado >24h deve liberar"
    assert motivo == "canal parado, sai já"

def test_intervalo_minimo_respeitado():
    """Último post há 1.5h - deve bloquear (intervalo_h padrão = 2)"""
    info = {"fuso": "America/New_York", "pico": [17, 22]}
    agora = datetime(2026, 10, 20, 18, 30, tzinfo=ZoneInfo("America/New_York"))

    ultimo = agora - timedelta(hours=1.5)

    pode, motivo = pode_postar(info, [ultimo], agora_la=agora)
    print(f"✓ Intervalo mínimo: {pode} - {motivo}")
    assert pode == False, "Deve bloquear se último < 2h"
    assert "último há 1.5 h" in motivo

def test_teto_diario_conta_agendados():
    """3 vídeos agendados hoje - deve bloquear (max_dia padrão = 3)"""
    info = {"fuso": "Europe/Paris", "pico": [17, 22]}
    agora = datetime(2026, 10, 20, 19, 0, tzinfo=ZoneInfo("Europe/Paris"))

    # 2 já publicados hoje
    ups = [
        agora - timedelta(hours=5),
        agora - timedelta(hours=3),
    ]
    # 1 agendado para 21h de hoje
    ups.append(agora.replace(hour=21, minute=0))

    pode, motivo = pode_postar(info, ups, agora_la=agora)
    print(f"✓ Teto diário: {pode} - {motivo}")
    assert pode == False, "Deve bloquear ao atingir max_dia"
    assert "já subiram 3 hoje" in motivo

def test_horario_pico():
    """Dentro do pico (19h) com intervalo OK - deve liberar"""
    info = {"fuso": "Asia/Tokyo", "pico": [17, 22]}
    agora = datetime(2026, 10, 20, 19, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

    ultimo = agora - timedelta(hours=3)

    pode, motivo = pode_postar(info, [ultimo], agora_la=agora)
    print(f"✓ Horário pico: {pode} - {motivo}")
    assert pode == True, "Deve liberar no pico com intervalo OK"
    assert "pico" in motivo

def test_fora_horario_pico():
    """Fora do pico (16h, pico 17-22h) - deve bloquear"""
    info = {"fuso": "America/Los_Angeles", "pico": [17, 22]}
    agora = datetime(2026, 10, 20, 16, 30, tzinfo=ZoneInfo("America/Los_Angeles"))

    ultimo = agora - timedelta(hours=3)

    pode, motivo = pode_postar(info, [ultimo], agora_la=agora)
    print(f"✓ Fora do pico: {pode} - {motivo}")
    assert pode == False, "Deve bloquear fora do pico"
    assert "fora do pico" in motivo

def test_apenas_agendados_futuros():
    """Canal só tem agendamentos futuros, nenhum passado - deve liberar se parado"""
    info = {"fuso": "UTC", "pico": [17, 22], "parado_h": 24}
    agora = datetime(2026, 10, 20, 18, 0, tzinfo=ZoneInfo("UTC"))

    # Apenas futuros
    ups = [
        agora + timedelta(days=1),
        agora + timedelta(days=2),
        agora + timedelta(days=3),
    ]

    pode, motivo = pode_postar(info, ups, agora_la=agora)
    print(f"✓ Só futuros: {pode} - {motivo}")
    assert pode == True, "Canal sem passados deve contar como parado"
    assert motivo == "canal parado, sai já"

def test_mix_passados_futuros():
    """Mix de passados (OK) e futuros - deve considerar só os passados"""
    info = {"fuso": "UTC", "pico": [17, 22]}
    agora = datetime(2026, 10, 20, 19, 0, tzinfo=ZoneInfo("UTC"))

    ups = [
        agora - timedelta(hours=4),  # Último passado: 4h atrás
        agora + timedelta(days=1),   # Futuro
        agora + timedelta(days=2),   # Futuro
    ]

    pode, motivo = pode_postar(info, ups, agora_la=agora)
    print(f"✓ Mix passado/futuro: {pode} - {motivo}")
    assert pode == True, "Deve considerar apenas o último passado"
    assert "pico" in motivo

if __name__ == "__main__":
    print("=== Testando correção do fila.py ===\n")

    test_caso_bug_agendado_futuro()
    test_canal_parado_com_agendado_futuro()
    test_intervalo_minimo_respeitado()
    test_teto_diario_conta_agendados()
    test_horario_pico()
    test_fora_horario_pico()
    test_apenas_agendados_futuros()
    test_mix_passados_futuros()

    print("\n✅ Todos os testes passaram! A correção está funcionando.")
