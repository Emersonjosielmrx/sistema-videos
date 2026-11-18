import json
import tempfile
import unittest
from pathlib import Path
import postar


class TestPostarEstadoConcorrente(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)
        self.orig_base = postar.BASE
        self.orig_estado = postar.ESTADO
        self.orig_fichas = postar.FICHAS

        postar.BASE = self.tmp_path
        postar.ESTADO = self.tmp_path / "longos_postados.json"
        postar.FICHAS = self.tmp_path / "fichas"
        postar.FICHAS.mkdir()

    def tearDown(self):
        postar.BASE = self.orig_base
        postar.ESTADO = self.orig_estado
        postar.FICHAS = self.orig_fichas
        self._tmpdir.cleanup()

    def test_conserto_03_11_preserva_postados_reprovados_cortes_sem_duplicar(self):
        # Rodada A e Rodada B leem estado inicial
        inicial = {
            "postados": [
                {"nome": "video1", "url": "https://youtu.be/1", "titulo": "Video 1", "canal": "Canal A"}
            ],
            "reprovados": ["rep1"],
            "cortes_postados": ["corte1"],
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        est_a = postar._estado()
        est_b = postar._estado()

        # Rodada A termina primeiro e adiciona video2 (e tenta duplicar video1), rep2, corte2
        est_a["postados"].append(
            {"nome": "video2", "url": "https://youtu.be/2", "titulo": "Video 2", "canal": "Canal A"}
        )
        est_a["reprovados"].append("rep2")
        est_a["cortes_postados"].append("corte2")
        postar._gravar_estado(est_a)

        # Rodada B termina horas depois com a base antiga + video3, rep3, corte3
        est_b["postados"].append(
            {"nome": "video3", "url": "https://youtu.be/3", "titulo": "Video 3", "canal": "Canal B"}
        )
        est_b["reprovados"].append("rep3")
        est_b["cortes_postados"].append("corte3")
        postar._gravar_estado(est_b)

        final = postar._estado()
        nomes_urls = [(p["nome"], p["url"]) for p in final["postados"]]
        self.assertEqual(len(nomes_urls), 3)
        self.assertEqual(
            set(nomes_urls),
            {
                ("video1", "https://youtu.be/1"),
                ("video2", "https://youtu.be/2"),
                ("video3", "https://youtu.be/3"),
            },
        )
        self.assertEqual(final["reprovados"], ["rep1", "rep2", "rep3"])
        self.assertEqual(final["cortes_postados"], ["corte1", "corte2", "corte3"])

    def test_incidente_1_sem_palavrao_nunca_volta_para_reprovados(self):
        # Estado inicial: medieval_p4 está reprovado
        inicial = {
            "postados": [],
            "reprovados": ["medieval_p4", "outro_reprovado"],
            "cortes_postados": [],
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        # Rodada 1 lê o estado de manhã (com medieval_p4 em reprovados)
        est_rodada_antiga = postar._estado()

        # Enquanto a Rodada 1 roda, bipar_palavrao.py cria SEM_PALAVRAO.txt e remove medieval_p4 no arquivo
        ficha_medieval = postar.FICHAS / "medieval_p4"
        ficha_medieval.mkdir(parents=True)
        (ficha_medieval / "SEM_PALAVRAO.txt").write_text("ok", encoding="utf-8")

        est_bipar = postar._estado()
        est_bipar["reprovados"].remove("medieval_p4")
        postar._gravar_estado(est_bipar)
        self.assertNotIn("medieval_p4", postar._estado()["reprovados"])

        # Rodada 1 termina à noite e grava seu estado antigo (que ainda continha medieval_p4 em reprovados)
        postar._gravar_estado(est_rodada_antiga)

        final = postar._estado()
        self.assertNotIn("medieval_p4", final["reprovados"])
        self.assertIn("outro_reprovado", final["reprovados"])
        self.assertNotIn("medieval_p4", est_rodada_antiga["reprovados"])

    def test_incidente_2_presos_nao_somem_com_rodada_antiga(self):
        # Estado inicial de manhã: preso_antigo
        inicial = {
            "postados": [],
            "reprovados": [],
            "cortes_postados": [],
            "presos": {"preso_antigo": {"status": "erro", "motivo": "timeout"}},
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        # Rodada 1 e Rodada 2 começam juntas
        est_1 = postar._estado()
        est_2 = postar._estado()

        # Rodada 2 marca um novo longo preso e grava
        est_2["presos"]["longo_novo"] = {"status": "enviando", "inicio": "14:00"}
        postar._gravar_estado(est_2)

        # Rodada 1 termina depois e grava seu est_1 (que só tinha preso_antigo)
        postar._gravar_estado(est_1)

        final = postar._estado()
        self.assertIn("preso_antigo", final["presos"])
        self.assertIn("longo_novo", final["presos"])
        self.assertEqual(final["presos"]["longo_novo"]["status"], "enviando")

    def test_incidente_3_titulo_nota_perde_para_titulo_real_do_arquivo(self):
        url_jardineiro = "https://youtu.be/jardineiro123"
        inicial = {
            "postados": [
                {
                    "nome": "jardineiro",
                    "url": url_jardineiro,
                    "titulo": "(reposto 03/11 do uploads_ledger...)",
                    "canal": "Canal X",
                }
            ],
            "reprovados": [],
            "cortes_postados": [],
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        # Rodada 1 lê o estado com a nota provisória
        est_1 = postar._estado()

        # Enquanto a Rodada 1 roda, o título é corrigido no arquivo (ou por outra rodada)
        est_2 = postar._estado()
        est_2["postados"][0]["titulo"] = "Por que a academia inteira tremeu..."
        postar._gravar_estado(est_2)

        # Rodada 1 termina depois e grava est_1 (que ainda tinha a nota provisória)
        postar._gravar_estado(est_1)

        final = postar._estado()
        post_jardineiro = next(p for p in final["postados"] if p["url"] == url_jardineiro)
        self.assertEqual(post_jardineiro["titulo"], "Por que a academia inteira tremeu...")

        # E se uma rodada traz um título de verdade NOVO, ele continua valendo sobre o do arquivo
        est_3 = postar._estado()
        est_3["postados"][0]["titulo"] = "Título Real Novo Atualizado pela Rodada"
        postar._gravar_estado(est_3)

        final_2 = postar._estado()
        post_jardineiro_2 = next(p for p in final_2["postados"] if p["url"] == url_jardineiro)
        self.assertEqual(post_jardineiro_2["titulo"], "Título Real Novo Atualizado pela Rodada")

    def test_incidente_3_disco_com_nota_nao_sobrescreve_titulo_real_da_rodada(self):
        # Caso inverso: arquivo no disco tem nota provisória e rodada traz título real
        url_video = "https://youtu.be/vid999"
        inicial = {
            "postados": [
                {
                    "nome": "vid999",
                    "url": url_video,
                    "titulo": "(nota provisoria)",
                    "canal": "Canal Y",
                }
            ],
            "reprovados": [],
            "cortes_postados": [],
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        est_rodada = postar._estado()
        est_rodada["postados"][0]["titulo"] = "Título Real Definido na Rodada"
        postar._gravar_estado(est_rodada)

        final = postar._estado()
        self.assertEqual(final["postados"][0]["titulo"], "Título Real Definido na Rodada")

    def test_incidente_4_presos_soltar_remove_apenas_enviando_e_nao_persiste(self):
        inicial = {
            "postados": [],
            "reprovados": [],
            "cortes_postados": [],
            "presos": {
                "longo_enviando_1": {"status": "enviando"},
                "longo_enviando_2": {"status": "enviando"},
                "longo_com_erro": {"status": "erro", "detalhe": "falha rede"},
            },
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        # Duas rodadas concorrentes leem o estado
        est_1 = postar._estado()
        est_2 = postar._estado()

        # No disco, também existe presos_soltar para longo_enviando_2 e longo_com_erro
        disco_mod = postar._estado()
        disco_mod["presos_soltar"] = ["longo_enviando_2", "longo_com_erro"]
        postar.ESTADO.write_text(json.dumps(disco_mod), encoding="utf-8")

        # Rodada 1 pede para soltar longo_enviando_1 e longo_com_erro
        est_1["presos_soltar"] = ["longo_enviando_1", "longo_com_erro"]
        postar._gravar_estado(est_1)

        # Rodada 2 (que leu lá atrás quando longo_enviando_1 e 2 estavam em presos) grava depois,
        # também informando presos_soltar
        est_2["presos_soltar"] = ["longo_enviando_1", "longo_enviando_2"]
        postar._gravar_estado(est_2)

        texto_gravado = postar.ESTADO.read_text(encoding="utf-8")
        final = json.loads(texto_gravado)

        # presos_soltar não fica gravado no arquivo
        self.assertNotIn("presos_soltar", final)
        self.assertNotIn("presos_soltar", est_1)
        self.assertNotIn("presos_soltar", est_2)

        # Os com status "enviando" foram soltos; o com "erro" permaneceu
        self.assertNotIn("longo_enviando_1", final["presos"])
        self.assertNotIn("longo_enviando_2", final["presos"])
        self.assertIn("longo_com_erro", final["presos"])
        self.assertEqual(final["presos"]["longo_com_erro"]["status"], "erro")


if __name__ == "__main__":
    unittest.main(verbosity=2)
