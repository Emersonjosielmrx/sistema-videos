"""teste_salvar_github.py — confere a limpeza de segredos do salvar_github.py (não toca no D: nem na rede).

    python teste_salvar_github.py        (ou: pytest teste_salvar_github.py)

Os segredos de mentira são montados por pedaços de propósito: se estivessem inteiros aqui, a própria limpeza os
trocaria na cópia do GitHub e o teste de lá deixaria de testar alguma coisa.
"""
import ast
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import salvar_github as sg  # noqa: E402

TG = "8123456789" + ":AA" + "h" * 33          # token de bot do Telegram
COOKIE = "g.a" + "000" + "x" * 60             # valor de cookie de sessão do Google
HASH = "1793126687_" + "ab" * 20              # SAPISIDHASH
MAIL = "fulano.teste" + "@" + "gmail.com"


def sem(txt, pedaco, extra=False):
    limpo = sg.limpar(txt, extra=extra)
    assert pedaco not in limpo, f"sobrou {pedaco[:14]}… em: {limpo[:120]}"
    return limpo


def test_telegram_colado_na_url():
    # foi assim que o token vazou em 13/11: "/bot<numero>:AA..." — o \b antigo não casava depois de "bot"
    sem(f'"url": "https://api.telegram.org/bot{TG}/sendMessage"', TG)
    sem(f"TOKEN {TG}", TG)
    assert sg.SOBROU.search(f"/bot{TG}/x"), "a varredura final também tem de pegar"


def test_cookie_google():
    sem(f"__Secure-1PSID={COOKIE}; outro=1", COOKIE)
    sem(f"valor solto {COOKIE}", COOKIE)
    sem(f"Authorization%3ASAPISIDHASH%20{HASH}", HASH)
    sem(f"SAPISIDHASH {HASH}", HASH)
    assert sg.SOBROU.search(COOKIE) and sg.SOBROU.search("SAPISIDHASH " + HASH)


def test_cookie_em_texto():
    sem("Cookie: sessionid=" + "a1b2c3d4" * 4 + "; x=1", "a1b2c3d4" * 4)
    # variável no lugar do valor: o código fica como está
    for ok in ('f"sessionid={self.sessao_atual_do_canal}"', 'h = "SID=%s" % valor_do_cookie_inteiro'):
        assert sg.limpar(ok) == ok


def test_senha_nao_quebra_codigo():
    # antes: split("auth_token=")[1].split(";") virava split("auth_token="<SEGREDO_REMOVIDO>";") -> erro de sintaxe
    codigo = 'x = h.split("auth_token=")[1].split(";")[0]\n'
    assert sg.limpar(codigo) == codigo
    ast.parse(sg.limpar(codigo))
    limpo = sem('senha = "' + "Abc12345" + 'xyz"\n', "Abc12345")
    ast.parse(limpo)


def test_publico_tira_conta_e_maquina():
    sem(f'"conta": "{MAIL}"', MAIL, extra=True)
    assert MAIL in sg.limpar(f'"conta": "{MAIL}"', extra=False)  # repositório privado: e-mail fica
    for ip in ("62.171.128.241", "191.36.139.246", "157.173.207.22", "192.168.0.10", "100.108.160.85"):
        sem(f"ssh root@host # {ip}", ip, extra=True)
        sem(f'"ip": "{ip}:8080"', ip, extra=True)
    for tel in ("+55 91 98888-7777", "5591988887777", "(91) 98888-7777"):
        sem(f'"fone": "{tel}"', tel, extra=True)


def test_publico_nao_estraga_o_que_nao_e_segredo():
    for ok in ("Chrome/120.0.0.0 Safari/537.36",             # versão, não IP
               'host = "127.0.0.1"', "0.0.0.0:8000", "dns 8.8.8.8", "10.0.0.5",
               "git clone git@github.com:dono/repo.git",      # endereço de clone
               '"ts": 1755123456789012',                      # número comprido que começa parecido com telefone
               '"id": 4551234567890123456',
               "style = 'backgroundColors'",                  # palavra de 16 letras entre aspas
               "pacote-1.22.333.4.tar",
               '"texto": "linha um\\n' + MAIL.split("@")[0] + ' sem arroba"'):
        assert sg.limpar(ok, extra=True) == ok, ok
    # e-mail logo depois de um "\\n" escrito por extenso: o "\\n" tem de sobrar inteiro (senão o JSON fica inválido)
    limpo = sem('{"t": "oi\\n' + MAIL + '\\ntchau"}', MAIL, extra=True)
    assert json.loads(limpo)["t"] == "oi\n<EMAIL>\ntchau", limpo
    sem('"url": "http://62.171.128.241:20128/v1"', "62.171.128.241", extra=True)  # IP dentro de URL
    sem("credentials: {id: 'Xa9X1e7LqM2uL5zU'}", "Xa9X1e7LqM2uL5zU", extra=True)  # id de credencial do n8n


def test_perfil_do_chrome_fica_fora(tmp_path=None):
    for d in ("chrome-profiles", "chrome_gen_conta5", "chrome_profile_3", "User Data", "Profile 104", "perfil_chrome"):
        assert not sg._pasta_vai(".", d), d
    for d in ("bin", "producao", "chromakey", "profiles_de_cor"):
        assert sg._pasta_vai(".", d), d


def test_cookies_txt_colado_sai_inteiro():
    """13/11 (chat do D:): bloco de cookies.txt colado num .md — todo valor de cookie sai, não só o __Secure-1PSID.
    Valores abaixo são inventados."""
    T = "\t"
    linhas = [f"+.youtube.com{T}TRUE{T}/{T}TRUE{T}1766016857{T}__Secure-1PSIDTS{T}sidts-AAAAbbbbCCCCdddd1111_2222-eeee",
              f".youtube.com{T}TRUE{T}/{T}FALSE{T}1766016857{T}SIDCC{T}AKEyXzAAAAbbbbCCCCdddd1111eeee2222",
              f".google.com{T}TRUE{T}/{T}TRUE{T}1766016857{T}__Secure-3PAPISID{T}aaaaBBBBccccDDDD/eeeeFFFFgggg1111"]
    limpo = sg.limpar("\n".join(linhas))
    for parte in ("sidts-AAAA", "AKEyXzAAAA", "aaaaBBBB"):
        assert parte not in limpo, limpo
    assert limpo.count("<SEGREDO_REMOVIDO>") == 3, limpo
    assert "__Secure-1PSIDTS" in limpo and "SIDCC" in limpo  # o NOME do cookie fica (ajuda quem lê o documento)
    # valor curto e sem cara de segredo fica (PREF, SOCS) e texto comum com TAB não é tocado
    curtos = f".youtube.com{T}TRUE{T}/{T}FALSE{T}0{T}PREF{T}hl=en&tz=UTC"
    assert sg.limpar(curtos) == curtos
    tabela = f"canal{T}TRUE{T}views{T}1200{T}observação bem comprida aqui"
    assert sg.limpar(tabela) == tabela


def test_proxy_sem_http_perde_a_senha():
    """13/11 (chat do D:): "usuario:senha@IP:porta" sem http:// na frente (veo/beta/_test_proxy.py) levava a senha.
    Valores inventados."""
    for txt in ('PROXY_RAW = "<USUARIO>:<SEGREDO_REMOVIDO>@45.39.15.202:6632"',
                "proxy = '<USUARIO>:<SEGREDO_REMOVIDO>@p.exemplo.io:80'"):
        limpo = sg.limpar(txt)
        assert "s3nh4Invent4da" not in limpo and "outraSenhaFalsa99" not in limpo, limpo
        assert "<SEGREDO_REMOVIDO>@" in limpo, limpo
        assert not sg.SOBROU.search(limpo), limpo
    # o que NÃO é proxy fica igual: e-mail em texto, horário, rótulo com dois-pontos, URL comum
    for ok in ("Reunião: amanha@10:30 no escritório", "def f(a: int, b: str) -> None:", 'x = {"hora": "21:05", "canal": "@leielucroia"}',
               "ssh usuario@servidor.exemplo.com -p 2222", "https://www.youtube.com/@canal/shorts"):
        assert sg.limpar(ok, extra=False) == ok, (ok, sg.limpar(ok, extra=False))
    assert sg.SOBROU.search('p = "<USUARIO>:<SEGREDO_REMOVIDO>@45.39.15.202:6632"')  # a varredura final barra


def test_listas_de_conta_so_em_privado():
    antes = sg.LIMPEZA_EXTRA
    arq = str(Path(__file__))  # qualquer arquivo pequeno que exista
    try:
        fora = ("02_CONTAS_GOOGLE.md", "kiro_contas_unica.json", "gemini_keys_master_list.json", "desktop_perfis.txt",
                "kaggle_massa_log_20261024_131030.txt", "gemini_massa_saida.txt", "kaggle_terminar_erros.txt",
                "ACESSO_VPS_PARA_AGENTES.md")
        dentro = ("fx_clips.py", "contas.py", "LEIA.md", "catalogo.json", "dialogo.txt", "monkey.py")
        sg.LIMPEZA_EXTRA = True
        assert not any(sg._vai(arq, n) for n in fora), [n for n in fora if sg._vai(arq, n)]
        assert all(sg._vai(arq, n) for n in dentro), [n for n in dentro if not sg._vai(arq, n)]
        sg.LIMPEZA_EXTRA = False
        assert all(sg._vai(arq, n) for n in fora[:7])
        # nome de segredo não vai nunca, público ou privado
        assert not any(sg._vai(arq, n) for n in ("cookies.json", "client_secret.json", "rclone.conf", ".env", "x.bak.py"))
    finally:
        sg.LIMPEZA_EXTRA = antes


if __name__ == "__main__":
    falhas = 0
    for nome, f in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                f()
                print(f"ok    {nome}")
            except AssertionError as e:
                falhas += 1
                print(f"FALHA {nome}: {e}")
    print("tudo certo" if not falhas else f"{falhas} teste(s) falharam")
    sys.exit(1 if falhas else 0)
