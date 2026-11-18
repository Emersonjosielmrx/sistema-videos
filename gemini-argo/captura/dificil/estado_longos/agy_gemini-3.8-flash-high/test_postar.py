import json
import tempfile
import threading
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
        """03/11: postado/reprovado/corte que existe no arquivo nunca se perde, e postado não duplica."""
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

        # Rodada A adiciona video2, rep2, corte2 e tenta duplicar video1
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

    def test_incidente_1_sem_palavrao_nunca_fica_em_reprovados_rodadas_concorrentes(self):
        """1. 13/11 20h45 — Ficha com SEM_PALAVRAO.txt está liberada e nunca pode ficar em reprovados.
        Simula duas rodadas concorrentes: Rodada 1 leu estado com medieval_p4 em reprovados.
        Rodada 2 bipou áudio, criou SEM_PALAVRAO.txt e removeu do arquivo.
        Rodada 1 grava depois: medieval_p4 não pode voltar para reprovados."""
        inicial = {
            "postados": [],
            "reprovados": ["medieval_p4", "outro_reprovado"],
            "cortes_postados": [],
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        # Rodada 1 lê no início (com medieval_p4 nos reprovados)
        est_1 = postar._estado()

        # Rodada 2 concorre: bipar_palavrao cria SEM_PALAVRAO.txt e salva estado sem medieval_p4
        ficha_medieval = postar.FICHAS / "medieval_p4"
        ficha_medieval.mkdir(parents=True)
        (ficha_medieval / "SEM_PALAVRAO.txt").write_text("ok", encoding="utf-8")

        est_2 = postar._estado()
        est_2["reprovados"].remove("medieval_p4")
        postar._gravar_estado(est_2)

        self.assertNotIn("medieval_p4", postar._estado()["reprovados"])

        # Rodada 1 termina horas depois e grava seu estado antigo (que continha medieval_p4)
        postar._gravar_estado(est_1)

        final = postar._estado()
        self.assertNotIn("medieval_p4", final["reprovados"])
        self.assertIn("outro_reprovado", final["reprovados"])
        self.assertNotIn("medieval_p4", est_1["reprovados"])

    def test_incidente_1_ambas_rodadas_tentam_reprovar_ficha_com_sem_palavrao(self):
        """Mesmo se duas rodadas tentarem adicionar ficha liberada a reprovados, ela é filtrada."""
        ficha = postar.FICHAS / "video_liberado"
        ficha.mkdir(parents=True)
        (ficha / "SEM_PALAVRAO.txt").write_text("liberado", encoding="utf-8")

        est_1 = postar._estado()
        est_2 = postar._estado()

        est_1["reprovados"].append("video_liberado")
        est_1["reprovados"].append("video_reprovado_real")
        postar._gravar_estado(est_1)

        est_2["reprovados"].append("video_liberado")
        postar._gravar_estado(est_2)

        final = postar._estado()
        self.assertNotIn("video_liberado", final["reprovados"])
        self.assertIn("video_reprovado_real", final["reprovados"])

    def test_incidente_2_presos_nao_somem_com_rodadas_concorrentes(self):
        """2. 14/11 — Presos não podem sumir quando rodada antiga grava estado que leu antes."""
        inicial = {
            "postados": [],
            "reprovados": [],
            "cortes_postados": [],
            "presos": {"preso_antigo": {"status": "erro", "motivo": "timeout"}},
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        # Rodada 1 lê o estado no início (só conhece preso_antigo)
        est_1 = postar._estado()

        # Rodada 2 concorre: marca novo preso e grava
        est_2 = postar._estado()
        est_2["presos"]["longo_novo"] = {"status": "enviando", "inicio": "14:00"}
        postar._gravar_estado(est_2)

        # Rodada 1 termina depois e grava est_1 (que não tinha longo_novo)
        postar._gravar_estado(est_1)

        final = postar._estado()
        self.assertIn("preso_antigo", final["presos"])
        self.assertIn("longo_novo", final["presos"])
        self.assertEqual(final["presos"]["longo_novo"]["status"], "enviando")

    def test_incidente_2_ambas_rodadas_marcam_presos_distintos(self):
        """Duas rodadas concorrentes marcam presos diferentes; ambos devem persistir."""
        est_1 = postar._estado()
        est_2 = postar._estado()

        est_1["presos"] = {"preso_r1": {"status": "enviando"}}
        postar._gravar_estado(est_1)

        est_2["presos"] = {"preso_r2": {"status": "erro", "motivo": "403"}}
        postar._gravar_estado(est_2)

        final = postar._estado()
        self.assertIn("preso_r1", final["presos"])
        self.assertIn("preso_r2", final["presos"])
        self.assertEqual(final["presos"]["preso_r1"]["status"], "enviando")
        self.assertEqual(final["presos"]["preso_r2"]["status"], "erro")

    def test_incidente_3_titulo_nota_perde_para_titulo_real_do_arquivo(self):
        """3. 14/11 15h20 — Título que começa com "(" é NOTA provisória: perde para título de verdade do arquivo."""
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

        # Rodada 2 concorre e corrige o título no arquivo
        est_2 = postar._estado()
        est_2["postados"][0]["titulo"] = "Por que a academia inteira tremeu..."
        postar._gravar_estado(est_2)

        # Rodada 1 termina depois e grava est_1 (que ainda tinha a nota provisória)
        postar._gravar_estado(est_1)

        final = postar._estado()
        post_jardineiro = next(p for p in final["postados"] if p["url"] == url_jardineiro)
        self.assertEqual(post_jardineiro["titulo"], "Por que a academia inteira tremeu...")

    def test_incidente_3_titulo_real_novo_da_rodada_continua_valendo(self):
        """3. Título de verdade novo (da rodada) continua valendo sobre o título antigo do arquivo."""
        url_video = "https://youtu.be/video_atualizado"
        inicial = {
            "postados": [
                {
                    "nome": "video_atualizado",
                    "url": url_video,
                    "titulo": "Título Anterior do Arquivo",
                    "canal": "Canal Y",
                }
            ],
            "reprovados": [],
            "cortes_postados": [],
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        est_1 = postar._estado()
        est_2 = postar._estado()

        # Rodada 1 define um novo título de verdade
        est_1["postados"][0]["titulo"] = "Novo Título Real Atualizado pela Rodada"
        postar._gravar_estado(est_1)

        final = postar._estado()
        self.assertEqual(final["postados"][0]["titulo"], "Novo Título Real Atualizado pela Rodada")

        # E se arquivo tinha nota provisória, título real da rodada também prevalece
        postar.ESTADO.write_text(json.dumps({
            "postados": [{"nome": "v_nota", "url": "https://youtu.be/nota", "titulo": "(nota antiga)"}],
            "reprovados": [],
            "cortes_postados": []
        }), encoding="utf-8")

        est_rodada = postar._estado()
        est_rodada["postados"][0]["titulo"] = "Título Definitivo"
        postar._gravar_estado(est_rodada)

        final_nota = postar._estado()
        self.assertEqual(final_nota["postados"][0]["titulo"], "Título Definitivo")

    def test_incidente_3_titulo_com_parenteses_no_meio_nao_eh_nota(self):
        """Título com parênteses no meio (não no início) NÃO é nota e não deve ser sobrescrito."""
        url_video = "https://youtu.be/parenteses_no_meio"
        inicial = {
            "postados": [
                {
                    "nome": "vid_par",
                    "url": url_video,
                    "titulo": "Título com Parênteses (Oficial) no Meio",
                    "canal": "Canal Y",
                }
            ],
            "reprovados": [],
            "cortes_postados": [],
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        est = postar._estado()
        # Outra rodada tenta colocar outro título no arquivo
        postar.ESTADO.write_text(json.dumps({
            "postados": [{
                "nome": "vid_par",
                "url": url_video,
                "titulo": "Título de Outra Rodada",
                "canal": "Canal Y"
            }],
            "reprovados": [],
            "cortes_postados": []
        }), encoding="utf-8")

        postar._gravar_estado(est)
        final = postar._estado()
        # Como o título da rodada não era nota, ele continua valendo
        self.assertEqual(final["postados"][0]["titulo"], "Título com Parênteses (Oficial) no Meio")

    def test_incidente_3_nota_com_espacos_iniciais_perde_para_titulo_real(self):
        """Nota provisória com espaços antes de '(' também perde para título real."""
        url_video = "https://youtu.be/nota_espacos"
        inicial = {
            "postados": [
                {
                    "nome": "vid_esp",
                    "url": url_video,
                    "titulo": "   (reposto com espaços)",
                    "canal": "Canal Y",
                }
            ],
            "reprovados": [],
            "cortes_postados": [],
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        est_1 = postar._estado()

        # Arquivo é corrigido com título real
        est_2 = postar._estado()
        est_2["postados"][0]["titulo"] = "Título Real Sem Nota"
        postar._gravar_estado(est_2)

        # Rodada 1 grava
        postar._gravar_estado(est_1)
        final = postar._estado()
        self.assertEqual(final["postados"][0]["titulo"], "Título Real Sem Nota")

    def test_incidente_4_presos_soltar_concorrente(self):
        """4. 16/11 — presos_soltar remove de presos SÓ se status for 'enviando'.
        Preso com 'erro' nunca é solto. presos_soltar não fica gravado no arquivo."""
        inicial = {
            "postados": [],
            "reprovados": [],
            "cortes_postados": [],
            "presos": {
                "longo_enviando_1": {"status": "enviando"},
                "longo_enviando_2": {"status": "enviando"},
                "longo_com_erro": {"status": "erro", "detalhe": "falha na API"},
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

        # Rodada 2 grava depois com sua lista de soltar
        est_2["presos_soltar"] = ["longo_enviando_1", "longo_enviando_2"]
        postar._gravar_estado(est_2)

        final = postar._estado()

        # presos_soltar não fica gravado no arquivo
        self.assertNotIn("presos_soltar", final)
        self.assertNotIn("presos_soltar", est_1)
        self.assertNotIn("presos_soltar", est_2)

        # Status 'enviando' soltos com sucesso
        self.assertNotIn("longo_enviando_1", final["presos"])
        self.assertNotIn("longo_enviando_2", final["presos"])

        # Preso com 'erro' NUNCA é solto
        self.assertIn("longo_com_erro", final["presos"])
        self.assertEqual(final["presos"]["longo_com_erro"]["status"], "erro")

    def test_incidente_4_presos_soltar_vindo_do_arquivo(self):
        """presos_soltar vindo do arquivo em disco também é aplicado e não fica gravado."""
        inicial = {
            "postados": [],
            "reprovados": [],
            "cortes_postados": [],
            "presos": {
                "video_disco_enviando": {"status": "enviando"},
                "video_disco_erro": {"status": "erro"},
            },
            "presos_soltar": ["video_disco_enviando", "video_disco_erro"],
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        # Rodada concorre e grava
        est = postar._estado()
        postar._gravar_estado(est)

        texto_gravado = postar.ESTADO.read_text(encoding="utf-8")
        final = json.loads(texto_gravado)

        self.assertNotIn("presos_soltar", final)
        self.assertNotIn("video_disco_enviando", final.get("presos", {}))
        self.assertIn("video_disco_erro", final.get("presos", {}))

    def test_incidente_2_mescla_detalhes_e_prioridade_erro(self):
        """Se disco tem status 'erro' e rodada antiga leu 'enviando', status 'erro' prevalece."""
        inicial = {
            "postados": [],
            "reprovados": [],
            "cortes_postados": [],
            "presos": {
                "video_critico": {"status": "enviando", "inicio": "08:00"},
            },
        }
        postar.ESTADO.write_text(json.dumps(inicial), encoding="utf-8")

        est_antiga = postar._estado()

        # Rodada mais recente detecta erro fatal e grava
        est_recente = postar._estado()
        est_recente["presos"]["video_critico"] = {
            "status": "erro",
            "motivo": "Crash 500",
            "tentativas": 3,
        }
        postar._gravar_estado(est_recente)

        # Rodada antiga termina e tenta gravar seu estado que ainda tinha 'enviando'
        postar._gravar_estado(est_antiga)

        final = postar._estado()
        preso = final["presos"]["video_critico"]
        self.assertEqual(preso["status"], "erro")
        self.assertEqual(preso["motivo"], "Crash 500")
        self.assertEqual(preso["tentativas"], 3)
        self.assertEqual(preso["inicio"], "08:00")

    def test_concorrencia_real_com_threads(self):
        """Simula múltiplas threads executando _gravar_estado concorrentemente."""
        postar.ESTADO.write_text(
            json.dumps({"postados": [], "reprovados": [], "cortes_postados": [], "presos": {}}),
            encoding="utf-8",
        )

        def worker(thread_id):
            est = postar._estado()
            est.setdefault("postados", [])
            est.setdefault("reprovados", [])
            est.setdefault("cortes_postados", [])
            est.setdefault("presos", {})
            est["postados"].append({
                "nome": f"video_t{thread_id}",
                "url": f"https://youtu.be/t{thread_id}",
                "titulo": f"Titulo Thread {thread_id}",
                "canal": "Geral"
            })
            est["reprovados"].append(f"rep_t{thread_id}")
            est["cortes_postados"].append(f"corte_t{thread_id}")
            est["presos"][f"preso_t{thread_id}"] = {"status": "enviando"}
            postar._gravar_estado(est)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        final = postar._estado()
        self.assertEqual(len(final["postados"]), 10)
        self.assertEqual(len(final["reprovados"]), 10)
        self.assertEqual(len(final["cortes_postados"]), 10)
        self.assertEqual(len(final["presos"]), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
