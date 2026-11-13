"""
LiciBot-IA · pncp_client.py
Cliente da API pública do PNCP (sem login) com retry/backoff e paralelismo limitado.
- Estágio 1: lista TODAS as contratações com proposta aberta (paginando) e filtra por regex.
- Estágio 2: itens completos (paginados), situação atual e texto dos documentos, lidos em memória
  (PDF, ZIP com PDFs/DOCX dentro, DOCX, ODT, TXT; RAR/7z se o bsdtar existir).
- Resultados: preço vencedor de cada item, coletado dias depois do fechamento.
"""

import io
import logging
import os
import random
import re
import shutil
import subprocess
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Iterable
from xml.etree import ElementTree

import httpx
import pymupdf

from config import (ARQUIVO_MAX_MB, DIAS_A_FRENTE, DOCS_POR_EDITAL, GAVETAS, HORAS_MINIMAS_PREPARO, MODALIDADES,
                    NEGATIVOS, OCR_MAX_PAGINAS, DOCS_ATE_VALOR, PNCP_API, PNCP_CONSULTA, PNCP_DELAY, PNCP_PARALELO, TAMANHO_PAGINA, TEXTO_MAX_CHARS,
                    normalizar)

log = logging.getLogger("licibot.pncp")
pymupdf.TOOLS.mupdf_display_errors(False)

_CLIENTE = httpx.Client(
    timeout=httpx.Timeout(90, connect=20),
    follow_redirects=True,
    headers={"User-Agent": "LiciBot-IA/2.0 (monitor de licitacoes; consulta publica)"},
    limits=httpx.Limits(max_connections=PNCP_PARALELO * 2, max_keepalive_connections=PNCP_PARALELO),
)
_TENTATIVAS = 4
_BSDTAR = shutil.which("bsdtar")

# situacaoCompraId do PNCP: 1 divulgada, 2 revogada, 3 anulada, 4 suspensa
SITUACAO_FECHADA = {2: "revogada", 3: "anulada", 4: "suspensa"}
# tipoDocumentoId -> prioridade de leitura (menor = lê antes)
_PRIORIDADE_DOC = {4: 0, 6: 1, 2: 2, 1: 3, 7: 4, 5: 5, 8: 6}


class PNCPErro(RuntimeError):
    pass


class Ritmo:
    """Limitador único para todos os fios. O PNCP devolve 429 quando passa de ~2-3 req/s: a cada 429 o
    intervalo dobra e todos pausam; a cada 20 respostas boas seguidas ele volta a acelerar um pouco."""

    def __init__(self, intervalo: float):
        self.minimo = max(intervalo, 0.2)
        self.intervalo = self.minimo
        self.proximo = 0.0
        self.boas = 0
        self.trava = threading.Lock()

    def esperar(self) -> None:
        with self.trava:
            agora = time.monotonic()
            vez = max(agora, self.proximo)
            self.proximo = vez + self.intervalo
        if vez > agora:
            time.sleep(vez - agora)

    def bloqueado(self, retry_after: float) -> None:
        with self.trava:
            self.intervalo = min(self.intervalo * 2, 8.0)
            self.boas = 0
            self.proximo = max(self.proximo, time.monotonic() + max(retry_after, 30.0))
            log.info("PNCP pediu calma (429): pausa geral e 1 requisição a cada %.1f s", self.intervalo)

    def ok(self) -> None:
        with self.trava:
            self.boas += 1
            if self.boas >= 20 and self.intervalo > self.minimo:
                self.intervalo = max(self.minimo, self.intervalo * 0.8)
                self.boas = 0


RITMO = Ritmo(PNCP_DELAY)
_TENTATIVAS_429 = 8


def _get(url: str, params: dict | None = None, *, aceita_vazio: bool = False) -> httpx.Response | None:
    """GET com ritmo global e backoff. 204/404 com aceita_vazio devolvem None."""
    ultimo = ""
    erros = bloqueios = 0
    while erros < _TENTATIVAS and bloqueios < _TENTATIVAS_429:
        RITMO.esperar()
        try:
            r = _CLIENTE.get(url, params=params)
            if r.status_code == 429:
                bloqueios += 1
                ultimo = "HTTP 429"
                RITMO.bloqueado(float(r.headers.get("retry-after") or 0))
                continue
            if r.status_code in (204, 404) and aceita_vazio:
                RITMO.ok()
                return None
            if r.status_code >= 500:
                erros += 1
                ultimo = f"HTTP {r.status_code}"
                time.sleep(2 ** erros * 2 + random.uniform(0, 1.5))
                continue
            RITMO.ok()
            if r.status_code >= 400:
                raise PNCPErro(f"HTTP {r.status_code} em {url}: {r.text[:200]}")
            return r
        except (httpx.TransportError, httpx.TimeoutException) as e:
            erros += 1
            ultimo = f"{type(e).__name__}: {e}"
            time.sleep(2 ** erros * 2 + random.uniform(0, 1.5))
    raise PNCPErro(f"desistiu em {url}: {ultimo}")


def _json(r: httpx.Response | None, vazio: Any) -> Any:
    """O PNCP às vezes devolve HTML com status 200 (manutenção): vira PNCPErro, não ValueError."""
    if r is None or not r.content:
        return vazio
    try:
        return r.json()
    except ValueError as e:
        raise PNCPErro(f"resposta não-JSON em {r.request.url}: {r.text[:120]!r}") from e


def _num(v: Any) -> float:
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _data(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s[:19])
    except ValueError:
        return None


# ═════════════════════════════════════════════════════════════════════════════
# ESTÁGIO 1
# ═════════════════════════════════════════════════════════════════════════════

def classificar(objeto: str, complemento: str = "") -> tuple[str | None, list[str]]:
    """(gaveta, trechos que casaram) ou (None, []). Negativo só olha o objeto (o complemento traz
    justificativa e lista de secretarias, que gera falso negativo)."""
    obj = normalizar(objeto)
    if any(p.search(obj) for p in NEGATIVOS):
        return None, []
    texto = f"{obj} {normalizar(complemento)}"
    for gaveta, padroes in GAVETAS:
        achados = []
        for p in padroes:
            m = p.search(texto)
            if m:
                achados.append(m.group(0).strip())
        if achados:
            return gaveta, achados
    return None, []


def _proposta_para_linha(x: dict[str, Any], gaveta: str, achados: list[str]) -> dict[str, Any]:
    orgao = x.get("orgaoEntidade") or {}
    uni = x.get("unidadeOrgao") or {}
    amparo = x.get("amparoLegal") or {}
    cnpj, ano, seq = orgao.get("cnpj", ""), x.get("anoCompra"), x.get("sequencialCompra")
    return {
        "numero_controle": x.get("numeroControlePNCP"),
        "cnpj_orgao": cnpj,
        "razao_social": orgao.get("razaoSocial"),
        "poder_id": orgao.get("poderId"),
        "esfera_id": orgao.get("esferaId"),
        "uf": uni.get("ufSigla"),
        "municipio": uni.get("municipioNome"),
        "unidade": uni.get("nomeUnidade"),
        "ano_compra": ano,
        "sequencial_compra": seq,
        "modalidade_id": x.get("modalidadeId"),
        "modalidade_nome": x.get("modalidadeNome"),
        "modo_disputa": x.get("modoDisputaNome"),
        "srp": 1 if x.get("srp") else 0,
        "objeto_compra": x.get("objetoCompra"),
        "info_complementar": x.get("informacaoComplementar"),
        "amparo_legal": amparo.get("nome"),
        "valor_estimado": _num(x.get("valorTotalEstimado")),
        "data_abertura": x.get("dataAberturaProposta"),
        "data_encerramento": (x.get("dataEncerramentoProposta") or "").replace("T", " "),
        "data_publicacao": x.get("dataPublicacaoPncp"),
        "atualizado_pncp": x.get("dataAtualizacaoGlobal") or x.get("dataAtualizacao"),
        "link_sistema": x.get("linkSistemaOrigem") or x.get("linkProcessoEletronico"),
        "link_pncp": f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}",
        "gaveta": gaveta,
        "kw_match": ", ".join(dict.fromkeys(achados))[:300],
    }


def _pagina(modalidade: int, pagina: int, data_final: str) -> dict[str, Any]:
    r = _get(f"{PNCP_CONSULTA}/contratacoes/proposta", {
        "dataFinal": data_final, "codigoModalidadeContratacao": modalidade,
        "pagina": pagina, "tamanhoPagina": TAMANHO_PAGINA}, aceita_vazio=True)
    return _json(r, {"data": [], "totalPaginas": 0, "totalRegistros": 0})


def buscar_propostas_abertas(max_paginas: int | None = None, ao_aprovar=None, ao_revogar=None,
                             desde: datetime | None = None) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Varre todas as páginas de cada modalidade. dataFinal = limite do ENCERRAMENTO da proposta
    (usar 'hoje' só traz o que fecha hoje). ao_aprovar(linha) é chamado na hora para cada aprovado, assim
    uma varredura interrompida não perde o que já leu. Páginas que falharam ganham uma 2ª volta no fim.
    Devolve (aprovados no filtro, contadores)."""
    data_final = (datetime.now() + timedelta(days=DIAS_A_FRENTE)).strftime("%Y%m%d")
    limite_preparo = datetime.now() + timedelta(hours=HORAS_MINIMAS_PREPARO)
    cont = {"lidos": 0, "filtrados": 0, "prazo_curto": 0, "fechados": 0, "paginas_falhas": 0}
    aprovados: dict[str, dict[str, Any]] = {}
    trava = threading.Lock()

    def processar(itens: Iterable[dict[str, Any]]) -> None:
        for x in itens:
            with trava:
                cont["lidos"] += 1
            if x.get("situacaoCompraId") in SITUACAO_FECHADA:
                with trava:
                    cont["fechados"] += 1
                if ao_revogar and x.get("numeroControlePNCP"):
                    ao_revogar(x["numeroControlePNCP"], SITUACAO_FECHADA[x["situacaoCompraId"]])
                continue
            gaveta, achados = classificar(x.get("objetoCompra") or "", x.get("informacaoComplementar") or "")
            if not gaveta:
                continue
            fim = _data(x.get("dataEncerramentoProposta"))
            # sem prazo = não está recebendo proposta (a leitura incremental traz também esses)
            if not fim or fim < limite_preparo:
                with trava:
                    cont["prazo_curto"] += 1
                continue
            linha = _proposta_para_linha(x, gaveta, achados)
            with trava:
                novo = linha["numero_controle"] not in aprovados
                aprovados[linha["numero_controle"]] = linha
            if novo and ao_aprovar:
                ao_aprovar(linha)

    # leitura incremental: só o que foi publicado/alterado (inclui revogação) desde "desde"
    def pagina(mod: int, p: int) -> dict[str, Any]:
        if desde is None:
            return _pagina(mod, p, data_final)
        r = _get(f"{PNCP_CONSULTA}/contratacoes/atualizacao", {
            "dataInicial": desde.strftime("%Y%m%d"), "dataFinal": datetime.now().strftime("%Y%m%d"),
            "codigoModalidadeContratacao": mod, "pagina": p, "tamanhoPagina": TAMANHO_PAGINA}, aceita_vazio=True)
        return _json(r, {"data": [], "totalPaginas": 0, "totalRegistros": 0})

    falhas: list[tuple[int, int]] = []
    for mod in MODALIDADES:
        try:
            primeira = pagina(mod, 1)
        except PNCPErro as e:
            log.error("modalidade %s: primeira página falhou: %s", mod, e)
            cont["paginas_falhas"] += 1
            continue
        total = primeira.get("totalPaginas") or 0
        if max_paginas:
            total = min(total, max_paginas)
        log.info("modalidade %s: %s %s em %s páginas", mod, primeira.get("totalRegistros"),
                 "abertas" if desde is None else f"publicadas/alteradas desde {desde:%d/%m %H:%M}", total)
        processar(primeira.get("data") or [])

        def uma(p: int, mod: int = mod) -> None:
            try:
                processar(pagina(mod, p).get("data") or [])
            except PNCPErro as e:
                log.debug("modalidade %s página %s: %s", mod, p, e)
                with trava:
                    falhas.append((mod, p))

        with ThreadPoolExecutor(PNCP_PARALELO) as ex:
            list(ex.map(uma, range(2, total + 1)))

    if falhas:
        log.info("2ª volta em %s página(s) que falharam", len(falhas))
        for mod, p in sorted(falhas):
            try:
                processar(pagina(mod, p).get("data") or [])
            except PNCPErro as e:
                cont["paginas_falhas"] += 1
                log.warning("modalidade %s página %s ficou sem ler: %s", mod, p, e)

    cont["filtrados"] = len(aprovados)
    return list(aprovados.values()), cont


# ═════════════════════════════════════════════════════════════════════════════
# ESTÁGIO 2
# ═════════════════════════════════════════════════════════════════════════════

def _base(cnpj: str, ano: int, seq: int) -> str:
    return f"{PNCP_API}/orgaos/{cnpj}/compras/{ano}/{seq}"


def situacao_atual(cnpj: str, ano: int, seq: int) -> dict[str, Any]:
    r = _get(_base(cnpj, ano, seq), aceita_vazio=True)
    return _json(r, {})


def buscar_itens(cnpj: str, ano: int, seq: int) -> list[dict[str, Any]]:
    """Sem paginação a API devolve só os 10 primeiros itens; aqui pagina até acabar."""
    itens: list[dict[str, Any]] = []
    pagina, tam = 1, 500
    while True:
        r = _get(f"{_base(cnpj, ano, seq)}/itens", {"pagina": pagina, "tamanhoPagina": tam}, aceita_vazio=True)
        lote = _json(r, [])
        if not isinstance(lote, list) or not lote:
            break
        for it in lote:
            itens.append({
                "numero_item": it.get("numeroItem"),
                "descricao": (it.get("descricao") or "")[:1000],
                "material_ou_servico": it.get("materialOuServico"),
                "valor_unitario": _num(it.get("valorUnitarioEstimado")),
                "valor_total": _num(it.get("valorTotal")),
                "quantidade": _num(it.get("quantidade")),
                "unidade": it.get("unidadeMedida"),
                "tipo_beneficio": it.get("tipoBeneficio"),
                "tipo_beneficio_nome": it.get("tipoBeneficioNome"),
                "criterio_julgamento": it.get("criterioJulgamentoNome"),
                "orcamento_sigiloso": 1 if it.get("orcamentoSigiloso") else 0,
                "situacao": it.get("situacaoCompraItemNome"),
            })
        if len(lote) < tam:
            break
        pagina += 1
    return itens


def buscar_arquivos(cnpj: str, ano: int, seq: int) -> list[dict[str, Any]]:
    r = _get(f"{_base(cnpj, ano, seq)}/arquivos", aceita_vazio=True)
    arqs = _json(r, [])
    if not isinstance(arqs, list):
        return []
    return [{"seq": a.get("sequencialDocumento"), "titulo": a.get("titulo") or "",
             "tipo_id": a.get("tipoDocumentoId"), "tipo": a.get("tipoDocumentoNome") or "",
             "data": a.get("dataPublicacaoPncp") or "", "url": a.get("url") or a.get("uri")}
            for a in arqs if a.get("statusAtivo", True)]


def _baixar(url: str) -> tuple[bytes, str]:
    """Baixa em memória com teto de tamanho. Devolve (conteúdo, nome do arquivo)."""
    limite = ARQUIVO_MAX_MB * 1024 * 1024
    for tentativa in range(_TENTATIVAS):
        RITMO.esperar()
        try:
            with _CLIENTE.stream("GET", url) as r:
                if r.status_code == 429:
                    RITMO.bloqueado(float(r.headers.get("retry-after") or 0))
                    continue
                if r.status_code >= 500:
                    time.sleep(2 ** tentativa * 3)
                    continue
                if r.status_code >= 400:
                    return b"", ""
                nome = ""
                m = re.search(r'filename="?([^";]+)', r.headers.get("content-disposition", ""))
                if m:
                    nome = httpx.URL("http://x/?n=" + m.group(1)).params.get("n", m.group(1))
                buf = io.BytesIO()
                for bloco in r.iter_bytes():
                    buf.write(bloco)
                    if buf.tell() > limite:
                        log.info("arquivo maior que %s MB, cortado: %s", ARQUIVO_MAX_MB, url)
                        return b"", nome
                return buf.getvalue(), nome
        except (httpx.TransportError, httpx.TimeoutException):
            time.sleep(2 ** tentativa * 3)
    raise PNCPErro(f"download falhou depois de {_TENTATIVAS} tentativas: {url}")


def _tessdata() -> str | None:
    if not shutil.which("tesseract"):
        return None
    for raiz in ("/usr/share/tesseract-ocr/5/tessdata", "/usr/share/tesseract-ocr/4.00/tessdata",
                 "/usr/share/tessdata", os.getenv("TESSDATA_PREFIX", "")):
        if raiz and os.path.exists(os.path.join(raiz, "por.traineddata")):
            return raiz
    return None


_TESSDATA = _tessdata()
_OCR_TRAVA = threading.Semaphore(1)   # OCR pesa CPU: um por vez


def _ocr(doc: "pymupdf.Document") -> str:
    """PDF escaneado: OCR em português nas primeiras OCR_MAX_PAGINAS páginas, tudo em memória."""
    if not _TESSDATA:
        return ""
    partes = []
    with _OCR_TRAVA:
        for i, p in enumerate(doc):
            if i >= OCR_MAX_PAGINAS:
                partes.append(f"[OCR feito só nas primeiras {OCR_MAX_PAGINAS} de {len(doc)} páginas]")
                break
            try:
                tp = p.get_textpage_ocr(language="por", dpi=200, full=True, tessdata=_TESSDATA)
                partes.append(p.get_text("text", textpage=tp, sort=True))
            except Exception as e:  # tesseract falhou nesta página
                log.debug("ocr página %s: %s", i, e)
    return "\n".join(partes)


def _texto_pdf(dados: bytes) -> str:
    try:
        with pymupdf.open(stream=dados, filetype="pdf") as doc:
            paginas = [p.get_text("text", sort=True) for p in doc]
            texto = "\n".join(paginas)
            if paginas and len(texto.strip()) < 40 * len(paginas):
                lido = _ocr(doc)
                if len(lido.strip()) > len(texto.strip()):
                    return "[texto obtido por OCR; pode ter erros de leitura]\n" + lido
                return f"[PDF de {len(paginas)} página(s) sem camada de texto (escaneado); conteúdo não lido]"
            return texto
    except Exception as e:  # PDF corrompido/criptografado
        log.debug("pdf ilegível: %s", e)
        return ""


def _texto_xml_office(dados: bytes, membro: str) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            raiz = ElementTree.fromstring(z.read(membro))
    except Exception:
        return ""
    partes = []
    for el in raiz.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag in ("p", "h", "br", "tab", "tr"):
            partes.append("\n")
        if tag in ("t", "span", "s", "p", "h") and el.text:
            partes.append(el.text)
        if el.tail and tag in ("span", "s"):
            partes.append(el.tail)
    return re.sub(r"\n{3,}", "\n\n", "".join(partes))


def _texto_arquivo_compactado(dados: bytes) -> list[tuple[str, bytes]]:
    """RAR/7z via bsdtar (stdin -> stdout), sem gravar em disco."""
    if not _BSDTAR:
        return []
    try:
        nomes = subprocess.run([_BSDTAR, "-tf", "-"], input=dados, capture_output=True, timeout=120).stdout
        saida = []
        for nome in nomes.decode("utf-8", "replace").splitlines():
            if nome.endswith("/"):
                continue
            conteudo = subprocess.run([_BSDTAR, "-xOf", "-", nome], input=dados, capture_output=True,
                                      timeout=120).stdout
            saida.append((nome, conteudo))
        return saida
    except (subprocess.SubprocessError, OSError):
        return []


def extrair_texto(dados: bytes, nome: str = "", profundidade: int = 0) -> str:
    """Descobre o tipo pela assinatura (o PNCP manda tudo como octet-stream)."""
    if not dados or profundidade > 3:
        return ""
    n = nome.lower()
    if dados[:5] == b"%PDF-":
        return _texto_pdf(dados)
    if dados[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(io.BytesIO(dados)) as z:
                membros = z.namelist()
                if "word/document.xml" in membros:
                    return _texto_xml_office(dados, "word/document.xml")
                if "content.xml" in membros and any(m == "mimetype" for m in membros):
                    return _texto_xml_office(dados, "content.xml")
                partes = []
                for m in sorted(membros, key=_ordem_membro):
                    if m.endswith("/"):
                        continue
                    info = z.getinfo(m)
                    if info.file_size > ARQUIVO_MAX_MB * 1024 * 1024:
                        continue
                    try:
                        t = extrair_texto(z.read(m), m, profundidade + 1)
                    except (RuntimeError, NotImplementedError, zipfile.BadZipFile, OSError) as e:
                        partes.append(f"--- {m} --- [não lido: {e}]")   # ZIP com senha / compressão rara
                        continue
                    if t.strip():
                        partes.append(f"--- {m} ---\n{t}")
                return "\n\n".join(partes)
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError):
            return ""
    if dados[:4] == b"Rar!" or dados[:6] == b"7z\xbc\xaf\x27\x1c":
        partes = [f"--- {m} ---\n{t}" for m, c in _texto_arquivo_compactado(dados)
                  if (t := extrair_texto(c, m, profundidade + 1)).strip()]
        return "\n\n".join(partes) if partes else "[arquivo RAR/7z não lido neste servidor]"
    if n.endswith((".txt", ".csv", ".html", ".htm", ".xml")):
        texto = dados.decode("utf-8", "replace")
        return re.sub(r"<[^>]+>", " ", texto) if n.endswith((".html", ".htm")) else texto
    if dados[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "[arquivo .doc antigo (Word 97) não lido]"
    return ""


def _ordem_membro(nome: str) -> tuple[int, str]:
    n = normalizar(nome)
    if "termo de referencia" in n or re.search(r"(^|[^a-z])tr([^a-z]|$)", n):
        return 0, n
    if "edital" in n or "aviso" in n:
        return 1, n
    if "minuta" in n or "contrato" in n:
        return 3, n
    return 2, n


def _ordenar_docs(arqs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def chave(a: dict[str, Any]) -> tuple[int, int, str]:
        t = normalizar(a["titulo"])
        prio = _PRIORIDADE_DOC.get(a["tipo_id"], 7)
        if "referencia" in t:
            prio = min(prio, 0)
        if "minuta" in t or a["tipo_id"] == 3:
            prio = 9
        return prio, 0 if ("retific" in t or "errata" in t) else 1
    # ordenação estável: dentro da mesma prioridade, o documento mais novo vem antes
    return sorted(sorted(arqs, key=lambda a: a["data"], reverse=True), key=chave)


def enriquecer(edital: dict[str, Any]) -> dict[str, Any]:
    """Itens + situação + texto dos documentos mais importantes."""
    cnpj, ano, seq = edital["cnpj_orgao"], edital["ano_compra"], edital["sequencial_compra"]

    sit = situacao_atual(cnpj, ano, seq)
    if sit.get("situacaoCompraId") in SITUACAO_FECHADA:
        return {"revogado": SITUACAO_FECHADA[sit["situacaoCompraId"]]}

    itens = buscar_itens(cnpj, ano, seq)
    arqs = buscar_arquivos(cnpj, ano, seq)

    titulos = " ".join(normalizar(a["titulo"]) for a in arqs)
    aviso_revogacao = bool(re.search(r"\b(revogac|anulac|cancelament|suspens)", titulos))

    partes, lidos, total = [], [], 0
    # pregão grande de produto: só itens e títulos (a IA vê se algum item serve); documento é caro de baixar
    valor = edital.get("valor_estimado") or sum(i["valor_total"] for i in itens)
    ler_docs = edital.get("gaveta") == "solar" or not valor or valor <= DOCS_ATE_VALOR
    for a in (_ordenar_docs(arqs)[:DOCS_POR_EDITAL] if ler_docs else []):
        if not a["url"]:
            continue
        dados, nome = _baixar(a["url"])
        texto = extrair_texto(dados, nome or a["titulo"]).strip()
        lidos.append(f"{a['tipo']}: {a['titulo']} ({len(texto)} car.)")
        if not texto:
            continue
        bloco = f"\n\n===== {a['tipo']} — {a['titulo']} =====\n{texto}"
        partes.append(bloco)
        total += len(bloco)
        if total >= TEXTO_MAX_CHARS:
            break

    texto = "".join(partes).strip()
    if len(texto) > TEXTO_MAX_CHARS:
        texto = texto[:TEXTO_MAX_CHARS] + f"\n\n[TEXTO CORTADO: os documentos tinham {len(texto)} caracteres]"

    valor = edital.get("valor_estimado") or 0
    soma_itens = sum(i["valor_total"] for i in itens)
    if not valor and soma_itens:
        valor = soma_itens

    return {
        "itens": itens,
        "texto_docs": texto,
        "docs_lidos": "\n".join(lidos + ([f"(outros {len(arqs) - len(lidos)} documento(s) não lidos"
                                          + ("" if ler_docs else f"; valor acima de R$ {DOCS_ATE_VALOR:,.0f}: só itens")
                                          + "; títulos: " + "; ".join(a["titulo"] for a in arqs[:12]) + ")"]
                                         if len(arqs) > len(lidos) else [])),
        "exclusivo_me_epp": 1 if any(i["tipo_beneficio"] in (1, 3) for i in itens) else 0,
        "qtd_itens": len(itens),
        "valor_estimado": valor,
        "aviso_revogacao": aviso_revogacao,
    }


# ═════════════════════════════════════════════════════════════════════════════
# Resultado (preço vencedor) — para aprender o desconto real
# ═════════════════════════════════════════════════════════════════════════════

def resultados_itens(cnpj: str, ano: int, seq: int, numeros: list[int]) -> dict[int, dict[str, Any]]:
    out, falhas, consultas = {}, 0, numeros[:30]
    for n in consultas:
        try:
            r = _get(f"{_base(cnpj, ano, seq)}/itens/{n}/resultados", aceita_vazio=True)
        except PNCPErro:
            falhas += 1
            continue
        if r is None or not r.content:
            continue
        try:
            lista = r.json()
        except ValueError:
            continue
        if isinstance(lista, list) and lista:
            v = lista[0]
            out[n] = {"valor": _num(v.get("valorTotalHomologado")),
                      "porte": v.get("porteFornecedorNome"), "tipo": v.get("tipoPessoa")}
    if consultas and falhas == len(consultas):
        raise PNCPErro("todas as consultas de resultado falharam")
    return out
