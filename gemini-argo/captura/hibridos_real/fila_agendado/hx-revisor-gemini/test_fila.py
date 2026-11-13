"""Testes para validar o comportamento de fila.py"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import unittest

from fila import pode_postar


class TestFilaPodePostar(unittest.TestCase):
    def setUp(self):
        self.tz = ZoneInfo("America/Sao_Paulo")
        self.info = {"fuso": "America/Sao_Paulo", "pico": [17, 22]}
        self.agora = datetime(2026, 10, 20, 19, 0, tzinfo=self.tz)

    def test_bug_agendado_no_futuro_nao_trava_canal(self):
        # Vídeo publicado há 3h e um vídeo agendado para daqui a 6 dias (144h)
        ups = [self.agora - timedelta(hours=3), self.agora + timedelta(hours=144)]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertTrue(pode)
        self.assertIn("pico", motivo)
        self.assertNotIn("-", motivo)

    def test_canal_parado_com_agendado_futuro(self):
        # Último publicado há 30h (> 24h) e agendamento futuro
        ups = [self.agora - timedelta(hours=30), self.agora + timedelta(days=2)]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertTrue(pode)
        self.assertEqual(motivo, "canal parado, sai já")

    def test_apenas_agendamentos_futuros_trata_como_canal_parado(self):
        # Apenas agendamento no futuro sem publicações anteriores
        ups = [self.agora + timedelta(days=3)]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertTrue(pode)
        self.assertEqual(motivo, "canal parado, sai já")

    def test_intervalo_minimo_bloqueia(self):
        # Último publicado há 1h (intervalo mínimo padrão é 2h)
        ups = [self.agora - timedelta(hours=1)]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertFalse(pode)
        self.assertEqual(motivo, "último há 1.0 h")

    def test_intervalo_minimo_com_agendado_futuro(self):
        # Publicado há 1h e agendado no futuro: deve bloquear pelo intervalo de 1h sem mostrar horas negativas
        ups = [self.agora - timedelta(hours=1), self.agora + timedelta(hours=100)]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertFalse(pode)
        self.assertEqual(motivo, "último há 1.0 h")

    def test_teto_do_dia_conta_agendados_de_hoje(self):
        # 2 publicados hoje + 1 agendado para mais tarde hoje (21h)
        # Total hoje = 3. Com teto=3 deve bloquear.
        ups = [
            self.agora - timedelta(hours=6),
            self.agora - timedelta(hours=3),
            self.agora.replace(hour=21, minute=0),
        ]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora, teto=3)
        self.assertFalse(pode)
        self.assertEqual(motivo, "já subiram 3 hoje")

        # Com teto=4 deve liberar
        pode4, _ = pode_postar(self.info, ups, agora_la=self.agora, teto=4)
        self.assertTrue(pode4)

    def test_fora_do_pico(self):
        # Às 13h (fora do pico 17h-22h), último publicado há 4h
        agora_almoco = self.agora.replace(hour=13, minute=0)
        ups = [agora_almoco - timedelta(hours=4)]
        pode, motivo = pode_postar(self.info, ups, agora_la=agora_almoco)
        self.assertFalse(pode)
        self.assertIn("fora do pico", motivo)


if __name__ == "__main__":
    unittest.main()
