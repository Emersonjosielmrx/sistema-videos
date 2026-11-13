"""Testes para fila.py cobrindo o bug do horário futuro e todas as regras de negócio."""
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fila import pode_postar


class TestFilaPodePostar(unittest.TestCase):
    def setUp(self):
        self.tz = ZoneInfo("America/Sao_Paulo")
        self.info = {
            "fuso": "America/Sao_Paulo",
            "pico": [17, 22],
            "intervalo_h": 2,
            "max_dia": 3,
            "parado_h": 24,
        }
        self.agora = datetime(2026, 10, 20, 19, 0, tzinfo=self.tz)

    def test_bug_agendado_futuro_nao_trava_canal(self):
        """Caso real do log: vídeo publicado há 3h e shorts agendado para 144h no futuro.
        Não deve gerar 'último há -144 h' e deve permitir postagem."""
        ups = [
            self.agora - timedelta(hours=3),
            self.agora + timedelta(hours=144),
        ]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertTrue(pode)
        self.assertIn("pico", motivo)
        self.assertNotIn("-", motivo)

    def test_canal_parado_sem_nenhum_upload(self):
        """Canal sem nenhum vídeo publicado ou agendado."""
        pode, motivo = pode_postar(self.info, [], agora_la=self.agora)
        self.assertTrue(pode)
        self.assertEqual(motivo, "canal parado, sai já")

    def test_canal_parado_apenas_com_agendamento_futuro(self):
        """Canal sem vídeos passados, mas com agendamentos no futuro."""
        ups = [self.agora + timedelta(days=2), self.agora + timedelta(days=5)]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertTrue(pode)
        self.assertEqual(motivo, "canal parado, sai já")

    def test_canal_parado_mais_de_24h(self):
        """Canal com último vídeo publicado há 25h (mesmo fora do pico) sai já."""
        agora_fora_pico = self.agora.replace(hour=14)
        ups = [
            agora_fora_pico - timedelta(hours=25),
            agora_fora_pico + timedelta(days=2),
        ]
        pode, motivo = pode_postar(self.info, ups, agora_la=agora_fora_pico)
        self.assertTrue(pode)
        self.assertEqual(motivo, "canal parado, sai já")

    def test_intervalo_minimo_bloqueia(self):
        """Último vídeo há 1.2h (menor que intervalo_h=2) deve bloquear."""
        ups = [self.agora - timedelta(hours=1.2)]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertFalse(pode)
        self.assertIn("último há 1.2 h", motivo)

    def test_intervalo_minimo_com_agendado_futuro(self):
        """Último vídeo há 1h e outro agendado no futuro deve bloquear pelo intervalo real do último."""
        ups = [
            self.agora - timedelta(hours=1),
            self.agora + timedelta(hours=72),
        ]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertFalse(pode)
        self.assertEqual(motivo, "último há 1.0 h")

    def test_teto_do_dia_com_publicados_e_agendados_de_hoje(self):
        """Teto do dia deve somar o que já foi publicado hoje + o que está agendado pra hoje."""
        ups = [
            self.agora - timedelta(hours=6),
            self.agora - timedelta(hours=3),
            self.agora.replace(hour=21, minute=30),  # agendado pra hoje à noite
        ]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertFalse(pode)
        self.assertEqual(motivo, "já subiram 3 hoje")

    def test_teto_do_dia_customizado(self):
        """Parâmetro teto tem precedência sobre max_dia."""
        ups = [
            self.agora - timedelta(hours=6),
            self.agora - timedelta(hours=3),
            self.agora.replace(hour=21, minute=30),
        ]
        # Com teto=4, deve permitir
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora, teto=4)
        self.assertTrue(pode)
        self.assertIn("pico", motivo)

    def test_teto_do_dia_ignora_agendados_de_outros_dias(self):
        """Vídeos agendados para outros dias não contam no teto de hoje."""
        ups = [
            self.agora - timedelta(hours=3),
            self.agora + timedelta(days=1),
            self.agora + timedelta(days=2),
        ]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertTrue(pode)
        self.assertIn("pico", motivo)

    def test_horario_pico_dentro(self):
        """Dentro do horário de pico (ex: 17h ou 19h)."""
        ups = [self.agora - timedelta(hours=3)]
        pode, motivo = pode_postar(self.info, ups, agora_la=self.agora)
        self.assertTrue(pode)
        self.assertIn("pico", motivo)

    def test_horario_pico_fora(self):
        """Fora do horário de pico (ex: 15h, pico 17h-22h)."""
        agora_fora = self.agora.replace(hour=15)
        ups = [agora_fora - timedelta(hours=3)]
        pode, motivo = pode_postar(self.info, ups, agora_la=agora_fora)
        self.assertFalse(pode)
        self.assertIn("fora do pico", motivo)

    def test_horario_pico_limites(self):
        """Limite inferior [ini: 17h entra; fim: 22h sai)."""
        # 17:00 está no pico (com último upload há 3h, ou seja, 14:00)
        agora_17 = self.agora.replace(hour=17, minute=0)
        pode_17, _ = pode_postar(self.info, [agora_17 - timedelta(hours=3)], agora_la=agora_17)
        self.assertTrue(pode_17)

        # 22:00 está fora do pico
        agora_22 = self.agora.replace(hour=22, minute=0)
        pode_22, motivo_22 = pode_postar(self.info, [agora_22 - timedelta(hours=3)], agora_la=agora_22)
        self.assertFalse(pode_22)
        self.assertIn("fora do pico", motivo_22)


if __name__ == "__main__":
    unittest.main()
