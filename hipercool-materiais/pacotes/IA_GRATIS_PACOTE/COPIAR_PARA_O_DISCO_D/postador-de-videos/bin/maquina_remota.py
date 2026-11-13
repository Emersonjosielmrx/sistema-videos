# -*- coding: utf-8 -*-
r"""maquina_remota.py SUBSTITUTO (versão do pacote).

No PC original este módulo abria o Chrome das contas em OUTRAS máquinas (PC2, notebooks) por SSH. Aqui tudo roda
NESTE PC: o "Remoto" abre o Chrome da conta pelo cofre local (D:\logins-google\cofre.py). Assim o claude_criar.py,
o pegar_cookies.py, o lote_contas.py e o zelador_sonnet.py funcionam sem mudar nada (eles pedem "pc2"; aqui "pc2" =
este computador).
"""
import sys

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402


def maquina_livre(*_a, **_k):
    return True


def _logins():
    """{apelido: {"pc2": {"google": True/False}}} a partir do cadastro do cofre (contas.json)."""
    try:
        reg = cofre._ler()["contas"]
    except Exception:  # noqa: BLE001
        return {}
    return {email.split("@")[0]: {"pc2": {"google": d.get("google") == "vivo"}} for email, d in reg.items()}


class Remoto:
    def __init__(self, nome="pc2"):
        self.nome = nome
        self.porta = None  # o código antigo às vezes troca a porta; aqui o cofre decide
        self._proc = None
        self._conta = None

    def vivo(self):
        return True

    def abrir(self, perfil, url="about:blank", sem_espera=True, **_k):
        porta, proc = cofre.abrir(perfil, url=url, visivel=True)
        self._proc, self._conta = proc, perfil
        return porta

    def fechar(self):
        if self._conta:
            cofre.fechar(self._proc, None, self._conta)
            self._proc = self._conta = None
