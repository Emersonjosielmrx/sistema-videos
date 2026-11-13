"""Testes para fila.py cobrindo o bug de horários agendados no futuro e todas as regras de negócio."""
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fila import pode_postar


class TestFila(unittest.TestCase):
    def setUp(self):
        self.tz = ZoneInfo("America/Sao_Paulo")
        self.info = {
            "fuso": "America/Sao_Paulo",
            "pico": [17, 22],
            "intervalo_h": 2,
            "max_dia": 3,
            "parado_h": 24,
        }
        # Horário base: 19:00 (dentro do pico 17h-22h)
        self.agora = datetime(2026, 10, 20, 19, 0, tzinfo=self.tz)

    def test_bug_agendado_futuro_nao_bloqueia_com_tempo_negativo(self):
        """Reproduz o erro do log ('último há -144 h').
        Com post há 3h e Shorts agendado para 144h no futuro, deve permitir postagem."""
        ups = [
            self.agora - timedelta(hours=3),
            self.agora + timedelta(hours=144),
        ]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertTrue(pode)
        self.assertIn("pico", motivo)
        self.assertNotIn("-", motivo)

    def test_canal_parado_com_agendado_futuro(self):
        """Canal parado há mais de 24h deve sair imediatamente, mesmo tendo post futuro agendado
        e mesmo estando fora do horário de pico."""
        agora_fora_pico = self.agora.replace(hour=10)
        ups = [
            agora_fora_pico - timedelta(hours=25),
            agora_fora_pico + timedelta(days=2),
        ]
        pode, motivo = pode_postar(self.info, ups, agora_la=agora_fora_pico)
        self.assertTrue(pode)
        self.assertEqual(motivo, "canal parado, sai já")

    def test_canal_parado_apenas_com_agendados_futuros(self):
        """Canal sem nenhuma postagem passada, apenas agendamento futuro: deve sair já."""
        ups = [self.agora + timedelta(days=3)]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertTrue(pode)
        self.assertEqual(motivo, "canal parado, sai já")

    def test_canal_parado_sem_nenhum_up(self):
        """Canal sem nenhum upload (ups vazio): deve sair já."""
        pode, motivo = pode_postar(self.info, [], agora_la=self.agora)
        self.assertTrue(pode)
        self.assertEqual(motivo, "canal parado, sai já")

    def test_intervalo_minimo_bloqueia_corretamente(self):
        """Último post há 1h (< intervalo_h de 2h): deve bloquear."""
        ups = [self.agora - timedelta(hours=1)]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertFalse(pode)
        self.assertEqual(motivo, "último há 1.0 h")

    def test_intervalo_minimo_com_agendado_futuro(self):
        """Último post há 1h e post agendado no futuro: deve bloquear com tempo positivo do último post."""
        ups = [
            self.agora - timedelta(hours=1),
            self.agora + timedelta(hours=48),
        ]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertFalse(pode)
        self.assertEqual(motivo, "último há 1.0 h")

    def test_teto_do_dia_contando_agendados_de_hoje(self):
        """Teto do dia deve contar posts já feitos hoje + posts agendados para hoje.
        Ex: 2 já publicados hoje + 1 agendado para mais tarde hoje (21h) = 3 hoje."""
        ups = [
            self.agora - timedelta(hours=5),
            self.agora - timedelta(hours=2, minutes=30),
            self.agora.replace(hour=21, minute=30),  # agendado pra hoje à noite
        ]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertFalse(pode)
        self.assertEqual(motivo, "já subiram 3 hoje")

    def test_teto_customizado_via_parametro(self):
        """Parâmetro teto tem precedência sobre max_dia."""
        ups = [
            self.agora - timedelta(hours=5),
            self.agora - timedelta(hours=2, minutes=30),
            self.agora.replace(hour=21, minute=30),
        ]
        # Se teto=4, deve permitir
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora, teto=4)
        self.assertTrue(pode)
        self.assertIn("pico", motivo)

    def test_teto_do_dia_ignora_agendados_de_outros_dias(self):
        """Agendados para amanhã ou dias futuros não devem contar no teto de hoje."""
        ups = [
            self.agora - timedelta(hours=3),
            self.agora + timedelta(days=1),
            self.agora + timedelta(days=2),
        ]
        # Apenas 1 post hoje, max_dia é 3
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertTrue(pode)
        self.assertIn("pico", motivo)

    def test_horario_fora_do_pico(self):
        """Fora do horário de pico (ex: 15h, pico 17h-22h) e sem canal parado: deve bloquear."""
        agora_tarde = self.agora.replace(hour=15, minute=30)
        ups = [agora_tarde - timedelta(hours=4)]
        pode, motivo = pode_postar(self.info, ups, agora_la=agora_tarde)
        self.assertFalse(pode)
        self.assertIn("fora do pico", motivo)


if __name__ == "__main__":
    unittest.main()
