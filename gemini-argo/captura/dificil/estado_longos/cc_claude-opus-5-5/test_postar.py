"""Testes dos 4 incidentes (INCIDENTES.md) + garantias de 03/11, simulando duas rodadas concorrentes.
Rodar: python -m unittest -v test_postar"""
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

import postar

AQUI = Path(__file__).parent


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.orig = (postar.BASE, postar.ESTADO, postar.FICHAS)
        postar.BASE, postar.ESTADO, postar.FICHAS = d, d / "longos_postados.json", d / "fichas"

    def tearDown(self):
        postar.BASE, postar.ESTADO, postar.FICHAS = self.orig
        self.tmp.cleanup()

    def escrever(self, dados):
        postar.ESTADO.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    def ler(self):
        return json.loads(postar.ESTADO.read_text(encoding="utf-8"))

    def mexer_no_arquivo(self, f):
        """Outra rodada / bipar_palavrao / edição à mão: lê o arquivo cru, muda e grava direto."""
        d = self.ler()
        f(d)
        self.escrever(d)


class Incidente1Reprovado(Base):
    def test_bipar_libera_e_rodada_antiga_nao_volta_reprovado(self):
        self.escrever({"postados": [], "reprovados": ["Medieval Parte 4", "Outro"]})
        a = postar._estado()  # rodada A lê com a Parte 4 reprovada
        # bipar_palavrao: cria SEM_PALAVRAO.txt e tira dos reprovados
        (postar.FICHAS / "Medieval Parte 4").mkdir(parents=True)
        (postar.FICHAS / "Medieval Parte 4" / "SEM_PALAVRAO.txt").write_text("ok")
        self.mexer_no_arquivo(lambda d: d["reprovados"].remove("Medieval Parte 4"))
        a["postados"].append({"nome": "X", "url": "u1", "titulo": "T", "canal": "c"})
        postar._gravar_estado(a)
        self.assertEqual(self.ler()["reprovados"], ["Outro"])

    def test_duas_rodadas_antigas_com_dict_simples(self):
        self.escrever({"postados": [], "reprovados": ["M4"]})
        a = json.loads(postar.ESTADO.read_text(encoding="utf-8"))  # dict comum, sem memória do lido
        b = postar._estado()
        (postar.FICHAS / "M4").mkdir(parents=True)
        (postar.FICHAS / "M4" / "SEM_PALAVRAO.txt").write_text("ok")
        self.mexer_no_arquivo(lambda d: d["reprovados"].remove("M4"))
        postar._gravar_estado(b)
        postar._gravar_estado(a)
        self.assertEqual(self.ler()["reprovados"], [])

    def test_reprovado_sem_ficha_liberada_continua(self):
        self.escrever({"postados": [], "reprovados": ["R"]})
        a, b = postar._estado(), postar._estado()
        b["reprovados"].append("R2")
        postar._gravar_estado(b)
        postar._gravar_estado(a)
        self.assertEqual(self.ler()["reprovados"], ["R", "R2"])


class Incidente2Presos(Base):
    def test_preso_de_outra_rodada_nao_some(self):
        self.escrever({"postados": [], "reprovados": [], "presos": {"P1": {"status": "erro"}}})
        a = postar._estado()  # leu de manhã
        b = postar._estado()
        b["presos"]["P2"] = {"status": "enviando"}
        postar._gravar_estado(b)
        postar._gravar_estado(a)  # grava o "presos" de manhã
        self.assertEqual(set(self.ler()["presos"]), {"P1", "P2"})

    def test_cada_rodada_marca_um_preso(self):
        self.escrever({"postados": [], "reprovados": []})
        a, b = postar._estado(), postar._estado()
        a.setdefault("presos", {})["PA"] = {"status": "enviando"}
        b.setdefault("presos", {})["PB"] = {"status": "erro"}
        postar._gravar_estado(a)
        postar._gravar_estado(b)
        self.assertEqual(self.ler()["presos"], {"PA": {"status": "enviando"}, "PB": {"status": "erro"}})

    def test_rodada_antiga_nao_rebaixa_status_atualizado(self):
        self.escrever({"postados": [], "reprovados": [], "presos": {"P": {"status": "enviando"}}})
        a, b = postar._estado(), postar._estado()
        b["presos"]["P"] = {"status": "erro", "msg": "quota"}
        postar._gravar_estado(b)
        postar._gravar_estado(a)
        self.assertEqual(self.ler()["presos"]["P"], {"status": "erro", "msg": "quota"})

    def test_dict_simples_nao_apaga_presos(self):
        self.escrever({"postados": [], "reprovados": [], "presos": {}})
        a = {"postados": [], "reprovados": []}  # rodada antiga que nem conhecia "presos"
        b = postar._estado()
        b["presos"]["P"] = {"status": "enviando"}
        postar._gravar_estado(b)
        postar._gravar_estado(a)
        self.assertIn("P", self.ler()["presos"])


class Incidente3Titulo(Base):
    NOTA = "(reposto 03/11 do uploads_ledger...)"
    REAL = "Por que a academia inteira tremeu..."

    def test_correcao_a_mao_nao_volta_pra_nota(self):
        self.escrever({"postados": [{"nome": "jardineiro", "url": "U", "titulo": self.NOTA, "canal": "c"}],
                       "reprovados": []})
        a = postar._estado()
        self.mexer_no_arquivo(lambda d: d["postados"][0].update(titulo=self.REAL))
        a["postados"].append({"nome": "outro", "url": "U2", "titulo": "T2", "canal": "c"})
        postar._gravar_estado(a)
        ps = self.ler()["postados"]
        self.assertEqual([p["titulo"] for p in ps if p["url"] == "U"], [self.REAL])
        self.assertEqual(len(ps), 2)

    def test_dict_simples_com_nota_perde_para_real(self):
        self.escrever({"postados": [{"nome": "j", "url": "U", "titulo": self.REAL, "canal": "c"}], "reprovados": []})
        a = {"postados": [{"nome": "j", "url": "U", "titulo": self.NOTA, "canal": "c"}], "reprovados": []}
        postar._gravar_estado(a)
        self.assertEqual(self.ler()["postados"], [{"nome": "j", "url": "U", "titulo": self.REAL, "canal": "c"}])

    def test_titulo_real_novo_da_rodada_vale(self):
        self.escrever({"postados": [{"nome": "j", "url": "U", "titulo": self.NOTA, "canal": "c"}], "reprovados": []})
        a, b = postar._estado(), postar._estado()
        a["postados"][0]["titulo"] = self.REAL
        postar._gravar_estado(a)
        postar._gravar_estado(b)  # rodada b ainda com a nota, grava depois
        self.assertEqual(self.ler()["postados"][0]["titulo"], self.REAL)

    def test_titulo_real_novo_da_rodada_vence_titulo_real_antigo(self):
        self.escrever({"postados": [{"nome": "j", "url": "U", "titulo": "Antigo", "canal": "c"}], "reprovados": []})
        a = postar._estado()
        a["postados"][0]["titulo"] = "Novo"
        postar._gravar_estado(a)
        self.assertEqual(self.ler()["postados"][0]["titulo"], "Novo")

    def test_nota_de_outro_nome_mesmo_url(self):
        self.escrever({"postados": [{"nome": "j_velho", "url": "U", "titulo": self.REAL, "canal": "c"}],
                       "reprovados": []})
        a = postar._estado()
        a["postados"].append({"nome": "j", "url": "U", "titulo": self.NOTA, "canal": "c"})
        postar._gravar_estado(a)
        self.assertTrue(all(p["titulo"] == self.REAL for p in self.ler()["postados"]))


class Incidente4Soltar(Base):
    def test_soltar_enviando_marcado_por_outra_rodada(self):
        self.escrever({"postados": [], "reprovados": [], "presos": {}})
        a, b = postar._estado(), postar._estado()
        b["presos"]["S"] = {"status": "enviando"}
        b["presos"]["E"] = {"status": "erro"}
        postar._gravar_estado(b)
        a["presos_soltar"] = ["S", "E"]  # A terminou o envio de S
        postar._gravar_estado(a)
        d = self.ler()
        self.assertEqual(d["presos"], {"E": {"status": "erro"}})
        self.assertNotIn("presos_soltar", d)

    def test_rodada_antiga_nao_ressuscita_preso_solto(self):
        self.escrever({"postados": [], "reprovados": [], "presos": {"S": {"status": "enviando"}}})
        a, b = postar._estado(), postar._estado()  # as duas leram S preso
        b["presos_soltar"] = ["S"]
        postar._gravar_estado(b)
        self.assertNotIn("S", self.ler()["presos"])
        postar._gravar_estado(a)  # A grava o "presos" de manhã
        self.assertNotIn("S", self.ler()["presos"])

    def test_presos_soltar_do_arquivo_e_aplicado(self):
        self.escrever({"postados": [], "reprovados": [], "presos": {"S": {"status": "enviando"},
                                                                     "E": {"status": "erro"}},
                       "presos_soltar": ["S", "E"]})
        a = {"postados": [], "reprovados": []}
        postar._gravar_estado(a)
        d = self.ler()
        self.assertEqual(d["presos"], {"E": {"status": "erro"}})
        self.assertNotIn("presos_soltar", d)

    def test_soltar_nao_solta_quem_virou_erro_em_outra_rodada(self):
        self.escrever({"postados": [], "reprovados": [], "presos": {"S": {"status": "enviando"}}})
        a, b = postar._estado(), postar._estado()
        b["presos"]["S"] = {"status": "erro"}
        postar._gravar_estado(b)
        a["presos_soltar"] = ["S"]
        postar._gravar_estado(a)
        self.assertEqual(self.ler()["presos"], {"S": {"status": "erro"}})

    def test_rodada_pode_marcar_de_novo_depois_de_solto(self):
        self.escrever({"postados": [], "reprovados": [], "presos": {"S": {"status": "enviando"}}})
        a = postar._estado()
        a["presos_soltar"] = ["S"]
        postar._gravar_estado(a)
        a["presos"]["S"] = {"status": "enviando", "vez": 2}  # novo envio na mesma rodada
        postar._gravar_estado(a)
        self.assertEqual(self.ler()["presos"]["S"], {"status": "enviando", "vez": 2})


class Garantias0311(Base):
    def test_nada_se_perde_e_nao_duplica(self):
        self.escrever({"postados": [{"nome": "yKfgs", "url": "F", "titulo": "t", "canal": "Fio da Meada"}],
                       "reprovados": ["R"], "cortes_postados": ["C"]})
        a, b = postar._estado(), postar._estado()
        b["postados"].append({"nome": "N2", "url": "U2", "titulo": "t2", "canal": "c"})
        b["reprovados"].append("R2")
        b["cortes_postados"].append("C2")
        postar._gravar_estado(b)
        a["postados"].append({"nome": "N1", "url": "U1", "titulo": "t1", "canal": "c"})
        postar._gravar_estado(a)
        postar._gravar_estado(a)
        d = self.ler()
        self.assertEqual(sorted(p["nome"] for p in d["postados"]), ["N1", "N2", "yKfgs"])
        self.assertEqual(d["reprovados"], ["R", "R2"])
        self.assertEqual(d["cortes_postados"], ["C", "C2"])

    def test_arquivo_inexistente(self):
        a = postar._estado()
        a["postados"].append({"nome": "N", "url": "U", "titulo": "t", "canal": "c"})
        postar._gravar_estado(a)
        self.assertEqual(len(self.ler()["postados"]), 1)

    def test_threads_concorrentes(self):
        self.escrever({"postados": [], "reprovados": [], "presos": {}})
        def rodada(i):
            for k in range(20):
                e = postar._estado()
                e["postados"].append({"nome": f"n{i}_{k}", "url": f"u{i}_{k}", "titulo": "t", "canal": "c"})
                e["presos"][f"p{i}_{k}"] = {"status": "erro"}
                postar._gravar_estado(e)
        ts = [threading.Thread(target=rodada, args=(i,)) for i in range(2)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        d = self.ler()
        self.assertEqual(len(d["postados"]), 40)
        self.assertEqual(len(d["presos"]), 40)


FILHO = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import postar
d = Path(sys.argv[2]); i = sys.argv[3]
postar.BASE, postar.ESTADO, postar.FICHAS = d, d / "longos_postados.json", d / "fichas"
for k in range(30):
    e = postar._estado()
    e["postados"].append({"nome": f"n{i}_{k}", "url": f"u{i}_{k}", "titulo": "t", "canal": "c"})
    e.setdefault("presos", {})[f"p{i}_{k}"] = {"status": "enviando"}
    postar._gravar_estado(e)
"""


class ProcessosConcorrentes(Base):
    def test_dois_processos(self):
        self.escrever({"postados": [], "reprovados": []})
        ps = [subprocess.Popen([sys.executable, "-c", FILHO, str(AQUI), self.tmp.name, str(i)]) for i in range(2)]
        for p in ps:
            self.assertEqual(p.wait(timeout=120), 0)
        d = self.ler()
        self.assertEqual(len(d["postados"]), 60)
        self.assertEqual(len(d["presos"]), 60)


if __name__ == "__main__":
    unittest.main()
