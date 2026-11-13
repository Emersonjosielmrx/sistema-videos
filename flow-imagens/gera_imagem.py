# -*- coding: utf-8 -*-
"""Gerador de IMAGEM pelo Google Flow (dono 22/10/2026: "fazer um gerador igual ao do Veo 3 mas sendo foto, que la no
Flow tem os modelos mais atuais"). Mesmo caminho do D:\\veo\\beta\\gera_auto.py (contas de contas.py, Chrome de cada
conta, trava da porta, checagem de login/credito, envio de imagem de referencia), so que o painel "Configuracoes do
agente" fica no bloco de IMAGEM e o que se baixa e a imagem.

Modelos no painel (22/10): "Nano Banana Pro", "Nano Banana 2 Lite", "Nano Banana 2.1" (padrao = 2.1, o mais novo).

    python gera_imagem.py "prompt" saida.png [--ref foto.jpg ...] [--formato 9:16] [--modelo "Nano Banana Pro"]
                          [--quantidade 2] [--conta mundosolar]

Como biblioteca: from gera_imagem import gerar_imagem -> lista de arquivos salvos (levanta se nenhuma conta deu).
Log de cada geracao em logs\\geracoes.jsonl (conta, modelo, creditos antes/depois, arquivos).
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

VEO = r"D:\veo\beta"
sys.path.insert(0, VEO)
BASE = Path(__file__).resolve().parent
LOG = BASE / "logs" / "geracoes.jsonl"
FORA = BASE / "logs" / "contas_fora.json"
FALHOU_LOG = BASE / "logs" / "pedidos_falhos.jsonl"  # D35: um registro por pedido que nenhuma conta entregou
FORA_S = 3 * 3600
FORMATOS = ("16:9", "4:3", "1:1", "3:4", "9:16")
MODELOS = ("Nano Banana Pro", "Nano Banana 2 Lite", "Nano Banana 2.1")
CREDITO_MINIMO = 5
ESPERA_S = 150  # Nano Banana entrega em 40-60 s; 22/10 a seebotsia ficou 2x 300 s sem nada (prova em logs\falhas)
FALHAS = BASE / "logs" / "falhas"
_RE_REPETIR = re.compile(r"high demand|alta demanda|try again later|tente novamente mais tarde|algo deu errado|"
                         r"something went wrong", re.I)
_RE_RECUSA = re.compile(r"might violate our policies|violate our policies|pode violar nossas pol[ií]ticas|"
                        r"viola(r)? nossas pol[ií]ticas", re.I)
_RE_BOTAO_REPETIR =re.compile(r"^\s*(Try again|Tentar novamente|Tente novamente)\s*$", re.I)


def _conta_ctx(sessao):
    """gera_auto le FLOW_SESSION/FLOW_PORT na importacao; aqui so precisamos das funcoes que recebem a pagina."""
    from contas import PORT_MAP, PROFILE_MAP
    os.environ["FLOW_SESSION"] = sessao
    os.environ["FLOW_PORT"] = PORT_MAP[sessao]
    # 25/10 22:20: o _ensure_chrome_running dá preferência ao FLOW_PROFILE do ambiente; o Veo tinha deixado o de
    # outra conta (so_notebook/en1653964) -> Chrome da seebotsia abriu com a pasta errada e falhou
    os.environ["FLOW_PROFILE"] = PROFILE_MAP[sessao]
    import gera_auto
    return gera_auto, int(PORT_MAP[sessao])


def garantir_modo_imagem(page, g, formato, quantidade, modelo, log=print):
    """Bloco 'Padrao da geracao de imagens' do painel do agente: formato, quantidade, modelo; 'Confirmar antes de
    gerar' = Nunca; Salvar. True se o modelo ficou confirmado."""
    page.locator(g._BTN_AJUSTES).last.click(timeout=8000)
    page.wait_for_timeout(1500)
    dd = page.get_by_text(re.compile(r"Nano Banana")).last
    dd.wait_for(state="visible", timeout=8000)
    for rotulo in (formato, f"x{quantidade}"):  # o bloco de imagem vem antes do seletor de modelo de imagem
        try:
            dd.locator(f"xpath=preceding::*[normalize-space(.)='{rotulo}'][1]").click(timeout=4000, force=True)
        except Exception as e:  # noqa: BLE001
            log(f"[imagem] AVISO: nao cliquei '{rotulo}' ({type(e).__name__})")
    try:
        page.locator("mat-radio-button, [role=radio]").filter(has_text=re.compile(r"^\s*(Nunca|Never)")).first.click(
            timeout=4000)
    except Exception as e:  # noqa: BLE001
        log(f"[imagem] AVISO: nao marquei 'Nunca' ({type(e).__name__})")
    atual = (dd.inner_text() or "").strip()
    if not re.search(re.escape(modelo) + r"\s*$", atual.replace("arrow_drop_down", "").strip()):
        dd.click(timeout=5000)
        page.wait_for_timeout(1000)
        page.locator("[role=menuitem], [role=option], mat-option").filter(
            has_text=re.compile(re.escape(modelo) + r"\s*$")).first.click(timeout=5000)
        page.wait_for_timeout(800)
        atual = (page.get_by_text(re.compile(r"Nano Banana")).last.inner_text() or "").strip()
    page.locator("button").filter(has_text=re.compile(r"^\s*(Salvar|Save)\s*$")).last.click(timeout=5000)
    page.wait_for_timeout(1500)
    atual = atual.replace("arrow_drop_down", "").replace("🍌", "").strip()
    log(f"[imagem] ajustes: {formato}, x{quantidade}, modelo '{atual}'")
    return atual.endswith(modelo)


def _imagens(page, g):
    """{chave: item} so das imagens da grade (sem <video>)."""
    return {k: v for k, v in g.midias(page).items() if v["tag"] == "IMG"}


def _baixar(page, src, destino, log=print):
    """Imagem em tamanho cheio com os cookies da sessao: tenta o endereco sem o sufixo de tamanho e com =s0."""
    base = src.split("=")[0]
    for url in (base + "=s0", base, src):
        try:
            r = page.request.get(url, timeout=120000)
            tipo, corpo = r.headers.get("content-type", ""), r.body()
        except Exception as e:  # noqa: BLE001
            log(f"  download falhou: {type(e).__name__}")
            continue
        if r.ok and tipo.startswith("image/") and len(corpo) > 30_000:
            from PIL import Image
            import io
            im = Image.open(io.BytesIO(corpo))
            destino.parent.mkdir(parents=True, exist_ok=True)
            if destino.suffix.lower() in (".jpg", ".jpeg"):
                im.convert("RGB").save(destino, quality=95)
            else:
                im.save(destino)
            log(f"OK imagem salva: {destino} ({im.size[0]}x{im.size[1]}, {len(corpo) // 1024} KB)")
            return True
    return False


def _igual_a_referencia(arq, refs):
    """A grade mostra tambem a foto enviada: diferenca media < 4 (0..255) em 64x64 = e ela, nao a gerada."""
    from PIL import Image, ImageChops, ImageStat
    a = Image.open(arq).convert("L").resize((64, 64))
    for r in refs:
        b = Image.open(r).convert("L").resize((64, 64))
        if ImageStat.Stat(ImageChops.difference(a, b)).mean[0] < 4:
            return True
    return False


def _maquinas_flow(sessao):
    """Notebooks (X200MA/Acer) onde a conta foi ativada pro Flow (postador\\bin\\maquina_remota.py ativar). Dono 23/10:
    "videos Veo e imagens rodando nos notebooks" (o PC1 ficava sem memoria com os Chromes do Flow). FLOW_NOTEBOOKS=0
    desliga."""
    if os.environ.get("FLOW_NOTEBOOKS", "1") == "0":
        return []
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import maquina_remota
        import contas
        return maquina_remota.maquinas_flow(contas.perfil_notebook(sessao))
    except Exception:  # noqa: BLE001
        return []


def _criar_projeto(page, log, g):
    """Conta sem projeto salvo cai na pagina inicial do Flow: 'Novo projeto' (mesmo jeito do gera_auto)."""
    g._passar_boas_vindas(page, log)  # conta nova: janela 'Sair/Avancar' cobria o botao (23/10)
    page.evaluate("""() => { for (const b of document.querySelectorAll('button, a, [role=button]')) {
        const t = (b.innerText || '').trim();
        if (t.includes('Novo projeto') || t.includes('New project') || t === 'Create') { b.click(); return t; } }
        return null; }""")
    page.wait_for_timeout(6000)
    page.evaluate("""() => { for (const b of document.querySelectorAll('button')) { if (!b.offsetParent) continue;
        const t = (b.innerText || '').trim(); if (['Concluir', 'Done', 'Criar', 'Create'].includes(t)) { b.click(); return t; } }
        return null; }""")
    page.wait_for_timeout(3000)
    log(f"[imagem] projeto novo: {page.url[-40:]}")


def _refs_so_pela_tela(refs, sessao, log):
    """13/11: imagem COM foto de referência não vai pelo pedido novo por HTTP (flow_gerar.imagem_beluga). Ele sobe as
    fotos pro projeto mas NÃO as liga ao pedido (a captura de 12/11 era de pedido só de texto; o campo das referências
    não foi mapeado) — a imagem sai com o rosto de outra pessoa. Medido em logs\\foto_na_hora.jsonl: até 11/11 a foto
    do dono passava no revisor de rosto 54-100% das vezes (nota mediana 0,60-0,69); desde 12/11 12h, 3-6% (nota
    0,18-0,22) — 241 fotos reprovadas em 2 dias, Veo/Advance/Globo/MS/produto parados nisso. Com referência = TELA
    (que anexa de verdade). Sem referência (capas só de texto) segue por HTTP. FLOW_HTTP_COM_REFS=1 religa (só depois
    de mapear o campo com uma captura da tela anexando foto)."""
    if refs and os.environ.get("FLOW_HTTP_COM_REFS") != "1":
        log(f"[imagem] {sessao}: pedido com {len(refs)} foto(s) de referência -> pela tela (o HTTP novo não anexa)")
        return True
    return False


def _gerar_http(sessao, prompt, saidas, refs, formato, modelo, log):
    """29/10 (dona: "faça" — navegador sem navegador na produção): pede ao agente do Flow por HTTP
    (D:\\projeto-navegador-sem-navegador\\services\\veo_flow\\flow_gerar.py; o Chrome só fabrica o token do
    reCAPTCHA, sem clicar na tela). So 1 imagem por pedido. Falhou = None e segue a tela como antes.
    Desligar: variavel FLOW_HTTP=0."""
    if os.environ.get("FLOW_HTTP") == "0" or len(saidas) != 1:
        return None
    if _refs_so_pela_tela(refs, sessao, log):
        return None
    try:  # 12/11: mesmo interruptor do remoto (config.FLOW_HTTP_REMOTO, desligado enquanto o HTTP volta vazio)
        sys.path.insert(0, VEO)
        import cadeia_veo
        if not cadeia_veo.http_remoto_ligado(sessao, "imagem"):
            return None
    except Exception:  # noqa: BLE001
        pass
    nsn = r"D:\projeto-navegador-sem-navegador"
    if nsn not in sys.path:
        sys.path.append(nsn)  # no fim (regra 23/10)
    try:
        from services.veo_flow.flow_gerar import FlowGerador
        with FlowGerador(sessao, log=log) as fg:
            r = fg.imagem(prompt, saidas[0], refs=refs, formato=formato, modelo=modelo)
        arqs = [Path(x) for x in r["arquivos"] if Path(x).exists() and Path(x).stat().st_size > 5000]
        if arqs and not (refs and _igual_a_referencia(arqs[0], refs)):
            log(f"[imagem] {sessao}: gerada por HTTP (sem clicar na tela) em {r['segundos']} s")
            _log({"conta": sessao, "via": "http", "saida": str(arqs[0]), "segundos": r["segundos"]})
            return arqs
        log(f"[imagem] {sessao}: HTTP entregou arquivo invalido -> tela")
    except Exception as e:  # noqa: BLE001
        log(f"[imagem] {sessao}: HTTP falhou ({type(e).__name__}: {str(e)[:150]}) -> tela")
    return None


class _DeslogadaNasMaquinas(RuntimeError):
    """Conta so-notebook com o Flow pedindo login em todas as maquinas dela (D36): sai do sorteio por FORA_S."""


class _PediuSemArquivo(RuntimeError):
    """O Flow aceitou o pedido por HTTP (credito gasto) e o arquivo nao veio: nao repetir na tela nem em outra maquina."""


class _RecusadoInseguro(RuntimeError):
    """01/11: o Flow recusou o prompt por HTTP (PUBLIC_ERROR_UNSAFE_GENERATION). A tela da mesma conta recusa igual e
    gastava ~5 min ocupando a maquina; a recusa varia entre contas (a capa B aprovada saiu na 2a conta): vai pra proxima
    conta, sem tirar esta da fila."""


def _gerar_http_remoto(rem, sessao, prompt, saidas, refs, formato, modelo, log):
    """29/10 (D30): a imagem e pedida por HTTP NA maquina `rem` (maquina_remota.Remoto ja aberto no perfil), com o Chrome
    de la so para o token (Remoto.nsn_flow_imagem). Mesmos interruptores do video (cadeia_veo.http_remoto_ligado:
    FLOW_HTTP_REMOTO, FLOW_HTTP=0, contas.SEM_HTTP). Devolve a lista de arquivos, ou None = segue o Chrome de la."""
    if len(saidas) != 1:
        return None
    if _refs_so_pela_tela(refs, sessao, log):
        return None
    try:
        sys.path.insert(0, VEO)
        import cadeia_veo
        if not cadeia_veo.http_remoto_ligado(sessao, "imagem"):
            return None
        url = _load_proj_map_sessao(sessao)
        if not url:
            log(f"[imagem] {sessao}: sem projeto salvo — o Chrome do {rem.nome} cria; proxima vez e HTTP")
            return None
        if not cadeia_veo._FLOW_PRONTO.setdefault(rem.nome, rem.nsn_flow_pronto()):
            return None
        log(f"[imagem] {sessao}: pedindo por HTTP no {rem.nome} (Chrome so para o token)")
        r = rem.nsn_flow_imagem(sessao, url, prompt, saidas[0], refs=refs, formato=formato, modelo=modelo,
                                fechar_chrome=getattr(__import__("config"), "FLOW_HTTP_FECHAR_CHROME", True), log_fn=log,
                                fabrica=getattr(rem, "fabrica", None))
    except Exception as e:  # noqa: BLE001
        log(f"[imagem] {rem.nome}: HTTP falhou antes de pedir ({type(e).__name__}: {str(e)[:120]}) -> tela")
        return None
    if r.get("ok"):
        arq = Path(saidas[0])
        if refs and _igual_a_referencia(arq, refs):
            log(f"[imagem] {sessao}: HTTP no {rem.nome} devolveu a propria referencia -> tela")
            return None
        log(f"[imagem] {sessao}: gerada por HTTP no {rem.nome} — Chrome aberto {r.get('chrome_s')} s, total {r.get('total_s')} s")
        _log({"conta": sessao, "via": f"http:{rem.nome}", "saida": str(arq), "segundos": r.get("segundos"),
              "chrome_s": r.get("chrome_s")})
        return [arq]
    if r.get("pediu"):
        raise _PediuSemArquivo(f"HTTP no {rem.nome}: {r.get('msg')}")
    if "UNSAFE_GENER" in str(r.get("msg")):  # a msg pode vir cortada
        raise _RecusadoInseguro(f"Flow recusou o prompt no {rem.nome} (unsafe) - proxima conta")
    if getattr(rem, "fabrica", None):
        _fabrica_falhou(rem, r)
        return None
    log(f"[imagem] {sessao}: {r.get('msg')} -> Chrome do {rem.nome}")
    return None


# 02/11 (dona: "deixando fabricando os tokens"): nestas máquinas roda o fabrica_tokens.py (tarefa FabricaTokens): o
# Chrome da conta fica QUENTE no Flow e cada imagem só pede token (~0,4 s) em vez de abrir/fechar Chrome (~40-80 s).
# Falhou antes de pedir = caminho antigo (porta extra, Chrome por imagem). Desligar: tirar a máquina daqui.
FABRICA = {"desktop", "pc2"}
_fabrica_fora = {}  # maquina -> até quando não tentar (fora do ar)


class _FabricaLogin(RuntimeError):
    pass


def _fabrica_falhou(rem, r):
    msg = str(r.get("msg"))
    rem.fabrica_msg = msg
    if "FabricaFora" in msg:  # fora do ar: pede pra tarefa subir e não tenta por 3 min
        _fabrica_fora[rem.nome] = time.time() + 180
        try:
            rem._ssh("schtasks /run /tn FabricaTokens", timeout=30)
        except Exception:  # noqa: BLE001
            pass
    if r.get("login"):
        raise _FabricaLogin(f"Flow pediu login no {rem.nome} (fábrica)")


def _pela_fabrica(maquina_remota, m, perfil, sessao, prompt, saidas, refs, formato, modelo, log):
    if _fabrica_fora.get(m, 0) > time.time():
        return None
    med = _medida_recente(m)
    if med and med["ram_mb"] < RAM_MIN_MB // 2 and med["cpu"] >= 95:
        return None
    rem = maquina_remota.Remoto(m)
    rem.fabrica = perfil
    log(f"[imagem] {sessao}: Chrome quente da fábrica no {m}")
    feito = _gerar_http_remoto(rem, sessao, prompt, saidas, refs, formato, modelo, log)
    if not feito and "FabricaFora" not in getattr(rem, "fabrica_msg", "FabricaFora"):
        # a fábrica está no ar e disse não (perfil aberto por outro pedido, demorou...): abrir o MESMO perfil pelo
        # caminho antigo só trava a fábrica na próxima vez — vai pra próxima máquina/conta
        return "PULAR"
    if feito:
        try:
            q = json.loads(QUENTES_ARQ.read_text("utf-8")) if QUENTES_ARQ.exists() else {}
        except (OSError, ValueError):
            q = {}
        q = {s: t for s, t in q.items() if time.time() - t < QUENTE_S}
        q[sessao] = time.time()
        try:
            QUENTES_ARQ.write_text(json.dumps(q), "utf-8")
        except OSError:
            pass
    return feito


QUENTES_ARQ = Path(__file__).parent / "logs" / "fabrica_quentes.json"
QUENTE_S = 15 * 60  # a fábrica fecha a conta parada há 20 min


def _contas_do_kaggle():
    """10/11 (2º banimento do Kaggle, 09/11): as 6 contas 'inovaremanhwaverse-<idioma>' tinham IP exclusivo no Kaggle mas
    a MESMA conta Google gerava 44-130 imagens no Flow por pc2/desktop/acer/x200ma (IPs de casa com dezenas de contas) —
    ligou a família toda. Conta Google que está no pool do Kaggle (viva ou banida) não entra no Flow.
    FLOW_SEM_CONTA_KAGGLE=0 desliga."""
    if os.environ.get("FLOW_SEM_CONTA_KAGGLE", "1") == "0":  # 10/11 dona: banidas ficam no Flow; só as VIVAS do Kaggle saem
        return set()
    try:
        pool = json.loads(Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {str(c.get("cofre") or "").split("@")[0].lower() for c in pool.get("contas", [])
            if c.get("cofre") and not c.get("banida") and c.get("ativa", True) is not False}


_QUENTES_VIVAS = {"em": 0, "contas": set()}


def _contas_quentes():
    """Contas com Chrome QUENTE na fábrica. 12/11: o arquivo local só tinha 2 contas de dias atrás (só grava quando a
    imagem SAI); a fábrica do PC2 tinha 8 quentes e o sorteio abria conta nova (fecha uma quente, reCAPTCHA não carrega,
    'falhou fabrica' 554x/200 pedidos). Agora pergunta à fábrica (/estado, porta 9399) a cada 2 min.
    FABRICA_QUENTES_VIVAS=0 volta ao arquivo."""
    try:
        q = json.loads(QUENTES_ARQ.read_text("utf-8"))
        arq = {s for s, t in q.items() if time.time() - t < QUENTE_S}
    except (OSError, ValueError):
        arq = set()
    if os.environ.get("FABRICA_QUENTES_VIVAS", "1") == "0":
        return arq
    if time.time() - _QUENTES_VIVAS["em"] > 120:
        vivas = set()
        try:
            sys.path.insert(0, r"D:\postador-de-videos\bin")
            import maquina_remota
            for m in FABRICA:
                try:
                    r = maquina_remota.Remoto(m)._ssh(
                        "powershell -NoProfile -Command \"(Invoke-WebRequest -UseBasicParsing "
                        "http://127.0.0.1:9399/estado -TimeoutSec 8).Content\"", timeout=25)
                    out = (r.stdout or b"").decode("utf-8", "replace") if isinstance(r.stdout, bytes) else (r.stdout or "")
                    vivas |= {s.lower() for s in (json.loads(out.strip() or "{}").get("contas") or {})}
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            vivas = set()
        _QUENTES_VIVAS.update(em=time.time(), contas=vivas)
    return arq | _QUENTES_VIVAS["contas"]


def _load_proj_map_sessao(sessao):
    try:
        with open(os.path.join(VEO, "logs", "flow_projetos.json"), encoding="utf-8") as f:
            url = json.load(f).get(sessao)
        return url if url and "/project/" in url else None
    except Exception:  # noqa: BLE001
        return None


_RE_MAQ_PULADA = re.compile(r"^\s+(x200ma|acer|desktop|pc2)\b:? ?(.*)")


def _maquina_pronta(maquina_remota, m):
    """29/10 (D35): o mesmo filtro que o maquina_remota.tentativas aplica na hora de abrir (vez de outro, telão, câmera,
    Chrome ocupado). O maquina_livre sozinho não olha telão nem a vez: o acer passando vídeo entrava como livre e as 2
    contas do pedido batiam nele (~15 de 28 erros do foto_na_hora em 29/10)."""
    if maquina_remota.reservado(m, os.environ.get("MAQUINA_VEZ_DE") or None):
        return False
    return maquina_remota.maquina_livre(m) and not maquina_remota.exibindo(m)


# 29/10 23h (D36, dona: "se dá navegador roda nos notebooks, se der erro nos notebooks aí roda no navegador do PC2... e
# se não o desktop"; o PC1 é o failback final). Só nas imagens: o ORDEM_NAVEGADOR (global, D31) não muda.
# 12/11 (dona: "temos 2 notebooks só pra flow + pc2 + sti + desktop, não faz sentido 1 capa a cada 10 h"): o STI (i5,
# 16 GB, Mint) entrou na ordem logo depois dos notebooks; antes ele não constava aqui e nunca era visto como livre
ORDEM_IMAGENS = ("x200ma", "acer", "sti", "pc2", "desktop")
# PC2 aguenta vários Chromes juntos ("nem precisa ser um por vez como é nos notebooks"): a imagem usa as portas extras do
# chrome_conta (cada uma com o seu ocupado_<porta>), sem disputar a 9460 do Veo/postagem nem as 9461+ do TikTok em lote.
PC2_PORTAS = range(9470, 9476)
# 01/11 21h (dona: "os notebooks só um por vez está correto, mas o desktop, o PC2 e esse podem fazer vários"): o desktop
# também usa portas extras (4 núcleos, ~3 GB livres = 3 Chromes de imagem; o Chrome fica aberto só ~80 s pro token)
# 12/11: o STI (i5, 16 GB) também abre vários Chromes de imagem (como o PC2), nas mesmas portas extras 9470+; assim não
# disputa a 9460 com o TikTok/Veo (era 'OCUPADO' toda hora). FLOW_STI_EXTRA=0 tira.
PORTAS_EXTRA = {"pc2": PC2_PORTAS, "desktop": range(9470, 9473),
                **({"sti": range(9470, 9474)} if os.environ.get("FLOW_STI_EXTRA", "1") != "0" else {})}
# 01/11 23h30 (dona: "testa até X Chromes começar a falhar; 3 não falha põe 4... falhou, reduz; sempre dinâmico"):
# quantas portas extras cada máquina usa vem de logs\capacidade.json. 3 imagens seguidas OK = +1 vaga; falha de
# capacidade (Chrome não abriu, pouca RAM, travou) = -1 e esse número vira o teto por 2 h; depois tenta subir de novo.
# 9470–9479: as 9461–9469 são do TikTok em lote no PC2 (chrome_conta aceita extra até 9479).
CAP_ARQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "capacidade.json")
CAP_INICIO = {"pc2": 6, "desktop": 3}
CAP_MAX, CAP_SOBE_APOS, CAP_TETO_S = 10, 3, 2 * 3600
_FALHA_CAPACIDADE = ("porta de controle", "POUCA_RAM", "TimeoutError", "TargetClosedError", "não respondeu",
                     "sem resposta", "túnel")


def _cap_mexer(maquina, fn):
    from filelock import FileLock
    with FileLock(CAP_ARQ + ".lock", timeout=30):
        try:
            with open(CAP_ARQ, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            d = {}
        e = d.setdefault(maquina, {"limite": CAP_INICIO.get(maquina, 1), "ok": 0, "teto": None, "teto_ate": 0})
        r = fn(e)
        with open(CAP_ARQ, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        return r


def cap_limite(maquina):
    return _cap_mexer(maquina, lambda e: e["limite"])


# dona 01/11: "ponha um monitoramento de RAM e CPU... se a CPU estiver livre põe mais; se limpar a RAM fica mais livre"
CPU_MAX, RAM_MIN_MB = 75, 900
MONITOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "monitor_maquinas.jsonl")
_MED_PS = ("$c=[int](Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average; "
           "$r=[int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1024); "
           "$n=(Get-Process chrome -EA 0).Count; 'MED ' + $c + ' ' + $r + ' ' + $n")


def medir(maquina, liberar=False):
    """{'cpu': %, 'ram_mb': livre, 'chromes': n} da máquina (1 ssh); liberar=True limpa a RAM lá antes
    (chrome_conta liberar). Grava em logs\\monitor_maquinas.jsonl. None se não respondeu."""
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import maquina_remota
        rem = maquina_remota.Remoto(maquina)
        if liberar:
            rem._ssh(f"{rem.run} liberar", timeout=90)
        if not maquina_remota.MAQUINAS.get(maquina, {}).get("win"):
            # 12/11: STI (Linux) — a mesma medida pelo /proc (o _ps_enc é PowerShell, só Windows)
            r = rem._ssh("python3 -c \"import time;f=lambda:[int(x) for x in open('/proc/stat').readline().split()[1:]];"
                         "a=f();time.sleep(2);b=f();d=[y-x for x,y in zip(a,b)];"
                         "m={l.split(':')[0]:int(l.split()[1]) for l in open('/proc/meminfo')};"
                         "import subprocess;n=subprocess.run(['pgrep','-c','chrome'],capture_output=True,text=True).stdout.strip() or '0';"
                         "print('MED',round(100*(1-(d[3]+d[4])/max(sum(d),1))),m['MemAvailable']//1024,n)\"", timeout=60)
        else:
            r = rem._ps_enc(_MED_PS, timeout=60)
        txt = (r.stdout or b"").decode("utf-8", "replace") if isinstance(r.stdout, bytes) else str(r.stdout or "")
        m = re.search(r"MED (\d+) (\d+) (\d+)", txt)
        if not m:
            return None
        d = {"cpu": int(m[1]), "ram_mb": int(m[2]), "chromes": int(m[3])}
    except Exception:  # noqa: BLE001
        return None
    with open(MONITOR, "a", encoding="utf-8") as f:
        f.write(json.dumps({"quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "maquina": maquina, "liberou": liberar,
                            "limite": cap_limite(maquina), **d}) + "\n")
    return d


def _medida_recente(maquina, idade_s=60):
    """Última medida de até 1 min (vários pedidos juntos não medem cada um por ssh); senão mede agora."""
    try:
        with open(MONITOR, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 20000))
            linhas = f.read().decode("utf-8", "replace").splitlines()
        for ln in reversed(linhas):
            try:
                j = json.loads(ln)
            except ValueError:
                continue
            if j.get("maquina") == maquina:
                quando = datetime.strptime(j["quando"], "%Y-%m-%dT%H:%M:%S").timestamp()
                if time.time() - quando < idade_s:
                    return j
                break
    except OSError:
        pass
    return medir(maquina)


def cap_ok(maquina):
    def f(e):
        e["ok"] += 1
        teto = e["teto"] if e.get("teto_ate", 0) > time.time() else None
        return e["ok"] >= CAP_SOBE_APOS and e["limite"] < CAP_MAX and (teto is None or e["limite"] + 1 < teto)
    if not _cap_mexer(maquina, f):
        return
    med = medir(maquina)
    if med and med["ram_mb"] < RAM_MIN_MB:
        med = medir(maquina, liberar=True)  # limpa a RAM lá e confere de novo
    if not med or med["cpu"] > CPU_MAX or med["ram_mb"] < RAM_MIN_MB:
        print(f"  capacidade {maquina}: não sobe agora ({med or 'sem medida'})", flush=True)
        return

    def sobe(e):
        e["limite"], e["ok"] = min(CAP_MAX, e["limite"] + 1), 0
        return e["limite"]
    novo = _cap_mexer(maquina, sobe)
    print(f"  capacidade {maquina}: subiu para {novo} Chromes de imagem (cpu {med['cpu']}%, "
          f"RAM livre {med['ram_mb']} MB)", flush=True)


def cap_falha(maquina, motivo):
    if not any(s in str(motivo) for s in _FALHA_CAPACIDADE):
        return  # falha da conta/prompt, não da máquina
    def f(e):
        e["teto"], e["teto_ate"] = e["limite"], time.time() + CAP_TETO_S
        e["limite"], e["ok"] = max(1, e["limite"] - 1), 0
        return e["limite"]
    novo = _cap_mexer(maquina, f)
    print(f"  capacidade {maquina}: falhou ({str(motivo)[:60]}) -> {novo} Chromes de imagem", flush=True)
PC2_RAM_MIN_MB = 2500
# o PC2 entra mesmo quando a cadeia do Veo não o passou em `maquinas` (a porta extra não toca na 9460 que o Veo usa)
PC2_SEMPRE = os.environ.get("FLOW_IMAGEM_PC2_SEMPRE", "1") != "0"


def _pc2_pronto(maquina_remota, nome="pc2"):
    """PC2 (ou o STI, 12/11) aceita mais um Chrome de imagem? (responde, sem login aberto pela dona, RAM livre). Devolve
    o perfil aberto na 9460 (pra não abrir o mesmo perfil duas vezes) ou None se não dá."""
    if "login" in maquina_remota.reservado(nome).lower():
        return None
    try:
        r = maquina_remota.Remoto(nome)
        txt = r._txt(r._ssh(f"{r.run} estado", timeout=20))
        j = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        if j.get("chrome") and int(j.get("ram_livre_mb") or 0) >= PC2_RAM_MIN_MB:
            return ((j.get("aberto") or {}).get("perfil") or "").lower()
    except Exception:  # noqa: BLE001
        pass
    return None


def _abrir_pc2_extra(maquina_remota, perfil, log, nome="pc2"):
    """Chrome do perfil numa porta extra livre do PC2/desktop (Remoto pronto, como o do tentativas) ou None."""
    # dona 01/11: conferir RAM/CPU antes de pôr mais. CPU no máximo (o PC2 a 100% derrubava os Chromes: "não está aberto",
    # ECONNRESET) = não manda agora; pouca RAM = limpa lá e confere de novo
    med = _medida_recente(nome)
    if med and med["ram_mb"] < RAM_MIN_MB:
        med = medir(nome, liberar=True)
    if med and (med["cpu"] >= 95 or med["ram_mb"] < RAM_MIN_MB // 2):
        log(f"  {nome}: sem folga agora (cpu {med['cpu']}%, RAM livre {med['ram_mb']} MB) — próxima máquina")
        return None
    rem = maquina_remota.Remoto(nome)
    portas = range(9470, 9470 + cap_limite(nome))  # dinâmico (capacidade.json)
    for p in portas:
        rem.porta = p
        try:
            rem.abrir(perfil, sem_espera=True)
            return rem
        except Exception as e:  # noqa: BLE001
            if "OCUPADO" in str(e):
                continue  # essa porta está com outro pedido: tenta a próxima
            log(f"  {nome} (porta {p}): {' '.join(str(e).split())[-120:]}")
            cap_falha(nome, e)
            return None
    log(f"  {nome}: portas de imagem {portas[0]}-{portas[-1]} todas ocupadas")
    return None


def _gerar_na_conta(sessao, prompt, saidas, refs, formato, modelo, log, maquinas=None, ruins=None):
    """Conta ativada nos notebooks: gera pelo Chrome LOGADO de la (um falhou = o outro); depois este PC.
    maquinas: so essas (ex.: as que a cadeia do Veo liberou); "pc1" fora da lista = nunca abre Chrome neste PC.
    ruins: {maquina: motivo} do pedido inteiro (D35): maquina pulada ou que falhou nao entra na proxima conta, e o
    motivo vai na mensagem de erro (antes era sempre "maquinas ocupadas ou fora").
    D36: uma maquina por vez na ORDEM_IMAGENS (notebooks -> PC2 -> desktop); no PC2, porta extra (varios juntos)."""
    from filelock import FileLock, Timeout
    g, porta = _conta_ctx(sessao)
    ruins = {} if ruins is None else ruins
    falhas = {}  # maquina -> tipo do erro desta conta (D36)
    maqs = sorted((m for m in _maquinas_flow(sessao)
                   if (maquinas is None or m in maquinas or (m == "pc2" and PC2_SEMPRE)) and m not in ruins),
                  key=lambda m: (0 if m in FABRICA and _fabrica_fora.get(m, 0) < time.time() else 1,
                                 ORDEM_IMAGENS.index(m) if m in ORDEM_IMAGENS else 9))
    if maqs:
        import maquina_remota
        import contas
        perfil = contas.perfil_notebook(sessao).lower()

        def log_maq(msg):  # o tentativas avisa por aqui quando pula uma maquina (telao, vez, sem resposta, OCUPADO)
            mp = _RE_MAQ_PULADA.match(str(msg))
            if mp:
                ruins.setdefault(mp[1], " ".join(mp[2].split())[:70])
            log(msg)
        for m in maqs:
            if m in ruins:
                continue
            if m in FABRICA:
                try:
                    feito = _pela_fabrica(maquina_remota, m, perfil, sessao, prompt, saidas, refs, formato, modelo, log)
                except _FabricaLogin:
                    falhas[m] = "SessaoExpiradaError"
                    continue
                if feito == "PULAR":
                    falhas[m] = "fabrica"
                    continue
                if feito:
                    return feito
            ordem = None
            if m in PORTAS_EXTRA:
                rem = _abrir_pc2_extra(maquina_remota, perfil, log_maq, m)
            else:
                ordem = maquina_remota.tentativas([m], perfil, log_fn=log_maq)
                rem = next(ordem)
            try:
                if rem is None:
                    continue
                # 29/10 (D30): primeiro por HTTP la (Chrome so para o token); falhou antes de pedir = a tela de la
                feito = _gerar_http_remoto(rem, sessao, prompt, saidas, refs, formato, modelo, log)
                if feito:
                    if m in PORTAS_EXTRA:
                        cap_ok(m)
                    return feito
                log(f"[imagem] gerando pelo Chrome do notebook {rem.nome}")
                # foto de referencia: com connect_over_cdp o Playwright TRANSFERE o arquivo pela conexao (o
                # youtube_web_poster usa rem.enviar so pra video grande); caminho de la quebrava (teste 23/10)
                return _gerar_na_pagina(g, sessao, rem.porta_local, prompt, saidas, refs, refs, formato,
                                        modelo, log, onde=rem.nome)
            except Exception as e:  # noqa: BLE001
                if type(e).__name__ == "DireitosAutoraisError" or isinstance(e, (_PediuSemArquivo, _RecusadoInseguro)):
                    raise
                falhas[m] = type(e).__name__
                if m in PORTAS_EXTRA:
                    cap_falha(m, f"{type(e).__name__}: {e}")
                if m not in PORTAS_EXTRA:  # PC2/desktop tem varias portas: a falha e da conta, a proxima pode usar
                    ruins[m] = f"falhou {type(e).__name__}"
                log(f"[imagem] {m} falhou ({type(e).__name__}: {str(e)[:120]}) — proximo")
            finally:
                if ordem is not None:
                    ordem.close()
                elif rem is not None:
                    rem.fechar()
    import contas
    if contas.so_notebook(sessao):  # logada so nas maquinas (23/10): aqui o Chrome abriria deslogado
        if maqs and all(falhas.get(m) == "SessaoExpiradaError" for m in maqs):
            # D36: deslogada do Flow em TODAS as maquinas dela (ex.: maiteanajessicajesus no PC2, 29/10 23h). Com
            # "ocupada" ela nunca saia do sorteio e gastava a vez do pedido toda hora: agora fica de fora (FORA_S)
            raise _DeslogadaNasMaquinas(f"Flow pediu login em {', '.join(maqs)}")
        motivo = "; ".join([f"{m} {ruins[m]}" for m in _maquinas_flow(sessao) if m in ruins] +
                           [f"{m} falhou {t}" for m, t in falhas.items() if m not in ruins])
        raise RuntimeError(f"conta ocupada (so notebook: {motivo or 'maquinas ocupadas ou fora'})")
    if maquinas is not None and "pc1" not in maquinas:  # 24/10: PC1 em carga/sem RAM (cadeia do Veo) = nada de Chrome aqui
        raise RuntimeError("conta ocupada (PC1 fora da lista de maquinas permitidas)")
    feito = _gerar_http(sessao, prompt, saidas, refs, formato, modelo, log)
    if feito:
        return feito
    trava = FileLock(os.path.join(VEO, "logs", f".cdp_lock_{porta}"), timeout=120)
    try:
        trava.acquire()
    except Timeout:
        raise RuntimeError("conta ocupada (o Veo esta usando)")
    # quem abre fecha (dono 22/10: o Chrome do Flow ficava aberto ocupando memoria); abrir so depois da trava
    abri = g._ensure_chrome_running(porta, log) == "novo"
    try:
        return _gerar_na_pagina(g, sessao, porta, prompt, saidas, refs, refs, formato, modelo, log, onde="PC1")
    finally:
        if abri:
            g.fechar_chrome(porta, log)
        trava.release()


def _gerar_na_pagina(g, sessao, porta, prompt, saidas, refs, refs_no_chrome, formato, modelo, log, onde):
    """Tudo no Chrome da porta CDP (deste PC ou do notebook pelo tunel): abrir o projeto, pedir, esperar e baixar."""
    from playwright.sync_api import sync_playwright
    import flow_bot
    if True:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = b.contexts[0]
            page = next((x for x in ctx.pages if "flow" in x.url), None) or (ctx.pages[0] if ctx.pages else ctx.new_page())
            proj = g._load_proj_map().get(sessao) or g._FLOW_HOME
            page.goto(proj, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(8000)
            g._dismiss_changelog_overlay(page, log)
            if g._is_login_page(page)[0]:
                raise g.SessaoExpiradaError("login pedido")
            if "/project/" not in page.url:
                _criar_projeto(page, log, g)
                if "/project/" not in page.url:
                    raise RuntimeError("conta sem projeto e o 'Novo projeto' nao abriu")
                g._save_proj_url(sessao, page.url)
            esgotado, padrao = g._creditos_esgotados(page)
            if esgotado:
                raise g.CreditosEsgotadosError(padrao)
            saldo = g._ler_saldo_creditos(page, log=log)
            if saldo is not None and saldo < CREDITO_MINIMO:
                raise g.CreditosEsgotadosError(f"saldo {saldo}")
            g._fechar_menu_conta(page, log)
            g.nova_sessao(page, log)
            try:  # 22/10: na canalalucinaai o botao de ajustes nao aparece; o pedido ja cita modelo e formato
                if not garantir_modo_imagem(page, g, formato, len(saidas), modelo, log):
                    log(f"[imagem] AVISO: o painel nao confirmou '{modelo}' — o pedido tambem cita o modelo")
            except Exception as e:  # noqa: BLE001
                log(f"[imagem] AVISO: painel de ajustes falhou ({type(e).__name__}) — sigo, o pedido cita modelo/formato")
                try:
                    page.keyboard.press("Escape")
                except Exception:  # noqa: BLE001
                    pass
            g._dismiss_changelog_overlay(page, log)
            for r, r_chrome in zip(refs, refs_no_chrome):
                g._subir_imagem(page, r, log=log, caminho_no_chrome=r_chrome)
            if refs:
                page.wait_for_timeout(4000)  # a foto enviada tambem entra na grade: tem que estar no "antes"
            antes = set(_imagens(page, g))
            pedido = (f"Generate {len(saidas)} still image{'s' if len(saidas) > 1 else ''} (NOT a video) with {modelo}, "
                      f"aspect ratio {formato}" + (", using the attached image(s) as reference" if refs else "")
                      + f". {prompt}")
            box, bsel = flow_bot._find_first(page, flow_bot.PROMPT_SELECTORS, timeout=20000)
            if not box:
                raise RuntimeError("caixa de pedido nao achada")
            caixa = page.locator(bsel).last
            caixa.click(timeout=8000, force=True)
            page.wait_for_timeout(500)
            if bsel in ("textarea", "input[type='text']"):
                caixa.fill(pedido, timeout=30000)
            else:
                page.keyboard.type(pedido)
            page.wait_for_timeout(800)
            enviar = page.locator("button").filter(has_text=re.compile(r"^\s*arrow_forward\s*$")).last
            try:
                enviar.wait_for(state="visible", timeout=8000)
            except Exception:
                _prova(page, sessao, log)  # 23/10: conta nova sem o botao de enviar
                raise
            for _ in range(20):
                if enviar.is_enabled():
                    break
                page.wait_for_timeout(1000)
            try:
                enviar.click(timeout=8000)
            except Exception:
                _prova(page, sessao, log)
                raise
            log("[imagem] pedido enviado: " + pedido[:160])
            page.wait_for_timeout(3000)
            if " ".join(pedido.split())[:40] in " ".join(g._texto_caixa(page).split()):
                raise RuntimeError("o pedido ficou na caixa (envio nao aconteceu)")

            t0, n_aprov, salvas, tentadas = time.time(), 0, [], set()
            repeticoes = 0
            while time.time() - t0 < ESPERA_S and len(salvas) < len(saidas):
                page.wait_for_timeout(5000)
                corpo = page.evaluate("() => document.body.innerText") or ""
                n_aprov = g._aprovar_se_pedir(page, n_aprov, log)
                # 22/10 (prova em logs\falhas): "The agent is experiencing high demand. Please try again later." + botão
                # "Try again" — esperar parado não resolve; o Veo já repete assim no "Algo deu errado"
                if _RE_REPETIR.search(corpo) and repeticoes < 3:
                    botao = page.locator("button").filter(has_text=_RE_BOTAO_REPETIR).last
                    try:
                        if botao.count() and botao.is_visible():
                            repeticoes += 1
                            botao.click(timeout=5000)
                            log(f"[imagem] Flow ocupado/erro — 'tentar novamente' ({repeticoes}/3)")
                            t0 = time.time()
                            page.wait_for_timeout(4000)
                            continue
                    except Exception:  # noqa: BLE001
                        pass
                # 23/10 (prova em logs\falhas): "This generation might violate our policies" não casava com o
                # _tem_recusa_direitos do Veo -> esperava 150 s e tirava a conta da lista à toa
                if time.time() - t0 > 15 and (g._tem_recusa_direitos(corpo) or _RE_RECUSA.search(corpo)):
                    raise g.DireitosAutoraisError("Flow recusou o pedido por politica")
                novas = {k: v for k, v in _imagens(page, g).items() if k not in antes and k not in tentadas}
                if novas and time.time() - t0 > 12:
                    page.wait_for_timeout(4000)  # a miniatura aparece antes do arquivo final
                    for k, it in novas.items():
                        if len(salvas) >= len(saidas):
                            break
                        tentadas.add(k)
                        alvo = saidas[len(salvas)]
                        if _baixar(page, it["src"], alvo, log):
                            if _igual_a_referencia(alvo, refs):
                                log("  era a propria foto de referencia (envio) — descartada")
                                alvo.unlink()
                                continue
                            salvas.append(alvo)
            depois = g._ler_saldo_creditos(page, log=log)
            _log({"conta": sessao, "onde": onde, "modelo": modelo, "formato": formato, "prompt": prompt,
                  "refs": [str(r) for r in refs],
                  "creditos_antes": saldo, "creditos_depois": depois, "arquivos": [str(s) for s in salvas],
                  "segundos": int(time.time() - t0)})
            if not salvas:
                _prova(page, sessao, log)  # pergunta do agente? recusa com outra frase? geração parada?
                raise RuntimeError(f"nenhuma imagem nova em {ESPERA_S}s")
            return salvas


def _prova(page, sessao, log):
    """Print + texto da tela em logs\\falhas (o porquê de uma falha, pra conferir depois)."""
    try:
        FALHAS.mkdir(parents=True, exist_ok=True)
        nome = f"{datetime.now():%Y%m%d_%H%M%S}_{sessao}"
        page.screenshot(path=str(FALHAS / f"{nome}.png"))
        (FALHAS / f"{nome}.txt").write_text((page.evaluate("() => document.body.innerText") or "")[-3000:], "utf-8")
        log(f"[imagem] prova da falha em logs\\falhas\\{nome}.*")
    except Exception:  # noqa: BLE001
        pass


def _ler_fora():
    """{conta: ate_quando} — conta que falhou fica FORA_S fora da lista (nao vale quando a conta e pedida com --conta)."""
    try:
        return json.loads(FORA.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _log(reg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    reg["quando"] = datetime.now().isoformat(timespec="seconds")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")


def gerar_imagem(prompt, saida, refs=(), formato="9:16", modelo="Nano Banana 2.1", quantidade=1, conta=None,
                 log=print, max_contas=None, maquinas=None):
    """Tenta conta por conta (as do Veo, em ordem; ou so a pedida) ate uma entregar. Devolve a lista de arquivos.
    max_contas: no maximo N contas (cada falha pode custar ate 5 min; o cliente.py dos outros projetos usa 3).
    maquinas: None = como sempre; lista (ex.: ["x200ma", "acer"]) = so essas maquinas, e as contas do PC1 so entram
    se "pc1" estiver nela (24/10: a foto na hora do Veo abriu Chrome no PC1 em pausa de carga e podia usar o desktop
    com o dono em chamada; a cadeia do Veo ja sabe quem esta livre e passa a lista)."""
    from contas import CONTAS
    assert formato in FORMATOS and modelo in MODELOS and 1 <= quantidade <= 4
    saida = Path(saida)
    saidas = [saida] if quantidade == 1 else [saida.with_name(f"{saida.stem}_{i}{saida.suffix}")
                                              for i in range(1, quantidade + 1)]
    fora = _ler_fora()
    reserva_pc1 = set()  # D36: contas do PC1 que ficam com a última tentativa do pedido
    if conta:
        contas = [conta]
    else:
        # 23/10 ("use o Veo em todas as contas"): contas so-notebook PRIMEIRO (tira o Chrome do PC1), mas so se
        # alguma maquina esta livre agora — senao iriam gastar as tentativas a toa; depois as do PC1
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        pc2_aberto = None
        try:
            import maquina_remota
            livres = {m for m in ("x200ma", "acer", "sti", "desktop")
                      if (maquinas is None or m in maquinas) and _maquina_pronta(maquina_remota, m)}
            if maquinas is None or "pc2" in maquinas or PC2_SEMPRE:  # D36: porta extra, não depende da 9460
                pc2_aberto = _pc2_pronto(maquina_remota)
                if pc2_aberto is not None:
                    livres.add("pc2")
            # 12/11: STI pelas portas extras (como o PC2) — livre mesmo com a 9460 ocupada pelo TikTok/Veo
            if "sti" in PORTAS_EXTRA and (maquinas is None or "sti" in maquinas) and "sti" not in livres:
                if _pc2_pronto(maquina_remota, "sti") is not None:
                    livres.add("sti")
        except Exception:  # noqa: BLE001
            livres = set()
        ativas = [c for c in CONTAS if fora.get(c["session"], 0) < time.time()
                  and c["session"].lower() not in _contas_do_kaggle()]
        import contas as _cm
        nb = [c["session"] for c in ativas if c.get("notebook") and livres & set(_maquinas_flow(c["session"]))
              and not (pc2_aberto and _cm.perfil_notebook(c["session"]).lower() == pc2_aberto
                       and livres & set(_maquinas_flow(c["session"])) == {"pc2"})]
        import random
        random.shuffle(nb)  # espalha o uso entre as contas (cada uma tem o credito dela)
        # D36: na ordem da dona — conta com notebook livre primeiro, depois PC2, depois desktop (sorteio dentro de cada)
        nb.sort(key=lambda s: min(ORDEM_IMAGENS.index(m) for m in livres & set(_maquinas_flow(s))))
        # 02/11: conta com Chrome QUENTE na fábrica de tokens vai na frente (só token, sem abrir Chrome)
        quentes = _contas_quentes()
        nb.sort(key=lambda s: (0 if s in quentes else 1, 0 if FABRICA & set(_maquinas_flow(s)) else 1))
        pc1 = [c["session"] for c in ativas if not c.get("notebook")] if maquinas is None or "pc1" in maquinas else []
        # sem PC1 permitido: ate 2 contas de notebook (uma falha = outra), senao a unica tentativa seria a 1a sorteada.
        # D35: a lista vai inteira e o laco abaixo conta so as tentativas de verdade (conta cujas maquinas ja foram
        # puladas/falharam neste pedido nao gasta a vez da 2a)
        if pc1 or maquinas is None:
            # D36: o PC1 é o failback final — antes era 1 conta das máquinas e logo as do PC1 (o Chrome abria aqui
            # com o PC2 parado). Agora as das máquinas primeiro; o PC1 só depois que elas deram não.
            contas = nb + pc1
            if pc1 and nb:
                max_contas = max(max_contas or 0, 3)  # 2 nas máquinas + a última vez guardada pro PC1
                reserva_pc1 = set(pc1)
        else:
            contas = nb
            max_contas = max_contas or 2
    # 29/10 (D33, dona: "subir os tetos com monitor de banimento, principalmente imagens"): teto de imagens por conta
    # por dia e quantas contas um pedido tenta vêm da rampa (postador config\tetos.json via bin\tetos.py). Conta no
    # teto do dia sai da lista (espalha entre as contas); max_contas só SOBE pela rampa (o pedido manda o mínimo).
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import tetos as _tetos
        if _tetos.ligado():
            cheias = []
            for s in list(contas):
                lim = _tetos.teto("imagens", s)
                if lim is not None and _tetos.imagens_hoje(s) >= int(lim):
                    cheias.append(f"{s}={lim}")
                    contas.remove(s)
            if cheias:
                log(f"[imagem] no teto do dia (tetos.json): {', '.join(cheias)}")
            mc = _tetos.teto("imagens", None, chave="<SEGREDO_REMOVIDO>")
            if mc:
                max_contas = max(int(max_contas or 0), int(mc)) if max_contas else max_contas
    except Exception as e:  # noqa: BLE001  (teto nunca para a geração)
        log(f"[imagem] tetos.json nao lido ({type(e).__name__}) — segue sem teto")
    erros = []
    ruins = {}  # D35: {maquina: motivo} pulada/falhou neste pedido -> a proxima conta vai para outra maquina
    t0 = time.time()
    import contas as _contas_mod
    for sessao in contas:
        if max_contas and len(erros) >= max_contas:
            break
        if reserva_pc1 and sessao not in reserva_pc1 and max_contas and len(erros) >= max_contas - 1:
            continue  # D36: a última tentativa é do PC1 (failback final)
        if ruins and not conta and _contas_mod.so_notebook(sessao):
            restam = [m for m in _maquinas_flow(sessao) if (maquinas is None or m in maquinas or
                                                             (m == "pc2" and PC2_SEMPRE)) and m not in ruins]
            if not restam:
                continue  # todas as maquinas dela ja deram nao neste pedido: nao gasta tentativa
        log(f"=== conta {sessao}")
        try:
            return _gerar_na_conta(sessao, prompt, saidas, [str(r) for r in refs], formato, modelo, log, maquinas,
                                   ruins)
        except Exception as e:  # noqa: BLE001
            erros.append(f"{sessao}: {type(e).__name__}: {str(e)[:200]}")
            log("  falhou -> " + erros[-1])
            if type(e).__name__ == "DireitosAutoraisError":
                break  # o pedido e o problema, nao a conta
            if "ocupada" not in str(e) and not isinstance(e, _RecusadoInseguro):  # 22/10: seebotsia gastou 5 min sem entregar; nao insistir nela a cada imagem
                fora = _ler_fora()
                longo = type(e).__name__ in ("SessaoExpiradaError", "CreditosEsgotadosError", "_DeslogadaNasMaquinas")
                fora[sessao] = time.time() + (FORA_S if longo else 20 * 60)  # "alta demanda" passa logo
                FORA.write_text(json.dumps(fora, indent=1), "utf-8")
    try:  # D35: a falha de qualquer chamador (Veo, cliente.py, produtos) fica medida; geracoes.jsonl segue so com acertos
        reg = {"erros": erros, "maquinas": maquinas, "ruins": ruins, "livres": sorted(livres) if not conta else None,
               "s": round(time.time() - t0), "quando": datetime.now().isoformat(timespec="seconds")}
        with FALHOU_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass
    raise RuntimeError("nenhuma conta gerou a imagem: " + " | ".join(erros))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("saida")
    ap.add_argument("--ref", nargs="*", default=[])
    ap.add_argument("--formato", default="9:16", choices=FORMATOS)
    ap.add_argument("--modelo", default="Nano Banana 2.1", choices=MODELOS)
    ap.add_argument("--quantidade", type=int, default=1)
    ap.add_argument("--conta")
    ap.add_argument("--max-contas", type=int)
    ap.add_argument("--maquinas", help="so estas maquinas, separadas por virgula (ex.: x200ma,acer); sem pc1 = nada no PC1")
    a = ap.parse_args()
    print(gerar_imagem(a.prompt, a.saida, a.ref, a.formato, a.modelo, a.quantidade, a.conta, max_contas=a.max_contas,
                       maquinas=[m.strip() for m in a.maquinas.split(",") if m.strip()] if a.maquinas else None))
