# -*- coding: utf-8 -*-
"""Peças comuns aos fluxos de painel administrativo (Comanda e Vitrine de Imóveis)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\fluxos-n8n\novos")
from n8nlib import Fluxo  # noqa: E402

AQUI = Path(__file__).parent
PG = {"postgres": {"id": "iG55YIDJm3Q0HLuz", "name": "Postgres apps_aulas (painéis das aulas)"}}
ROTEADOR = {"openAiApi": {"id": "9L3A8W0GrI5kEyTG", "name": "roteador 20128 (rápido)"}}
ROTEADOR_URL = "http://157.173.207.22:20128/v1/chat/completions"
IP = "($json.headers['x-real-ip'] || String($json.headers['x-forwarded-for'] || '').split(',')[0] || '').trim()"


def pagina(arquivo, **troca):
    """Lê a página HTML, põe o CSS e o JS comuns. Vai direto no 📤 (sem Code: resposta rápida)."""
    t = Path(arquivo).read_text(encoding="utf-8")
    css = (AQUI / "estilo.css").read_text(encoding="utf-8").replace("__COR__", troca.pop("cor", "#C2410C"))
    t = t.replace("__CSS__", css).replace("__BASE__", (AQUI / "base.js").read_text(encoding="utf-8"))
    for k, v in troca.items():
        t = t.replace(f"__{k}__", v)
    # o 📤 trata o texto como expressão só se começar com "="; {{ }} no HTML não aparece nas nossas páginas
    assert "{{" not in t, f"{arquivo}: tem '{{{{' (o n8n tentaria avaliar)"
    return t


def postgres(f, nome, sql, parametros, pos, sempre=True):
    """Executa SQL com parâmetros ($1, $2...) — o valor nunca é colado no SQL (sem injeção)."""
    return f.no(nome, "n8n-nodes-base.postgres", 2.6, {
        "operation": "executeQuery", "query": sql,
        "options": {"queryReplacement": parametros}}, pos, PG, alwaysOutputData=sempre)


def ia_http(f, nome, corpo_expr, pos, tempo=120000):
    """Chamada direta ao roteador de IA (formato OpenAI) pelo nó HTTP, com a credencial do roteador."""
    return f.no(nome, "n8n-nodes-base.httpRequest", 4.2, {
        "method": "POST", "url": ROTEADOR_URL, "authentication": "predefinedCredentialType", "nodeCredentialType": "openAiApi",
        "sendBody": True, "specifyBody": "json", "jsonBody": corpo_expr,
        "options": {"timeout": tempo, "response": {"response": {"neverError": True}}}}, pos, ROTEADOR,
        onError="continueRegularOutput", retryOnFail=True, maxTries=2, waitBetweenTries=2000)


def para_arquivo(f, nome, campo, mime_expr, pos):
    return f.no(nome, "n8n-nodes-base.convertToFile", 1.1, {
        "operation": "toBinary", "sourceProperty": campo, "binaryPropertyName": "data",
        "options": {"mimeType": mime_expr, "fileName": "imagem"}}, pos)


def switch(f, nome, regras, pos):
    """regras = [(nome_saida, expressao_booleana)]; a última saída é o 'resto' (fallback)."""
    import uuid
    valores = []
    for rotulo, expr in regras:
        valores.append({"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                                       "conditions": [{"id": str(uuid.uuid5(uuid.NAMESPACE_URL, f.nome + nome + rotulo)), "leftValue": expr,
                                                       "rightValue": "", "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                                       "combinator": "and"}, "renameOutput": True, "outputKey": rotulo})
    return f.no(nome, "n8n-nodes-base.switch", 3.2, {"rules": {"values": valores}, "options": {"fallbackOutput": "extra", "renameFallbackOutput": "resto"}}, pos)


def grava(f, pasta, nome_arq):
    caminho = Path(pasta) / nome_arq
    f.grava(caminho)
    js = json.loads(caminho.read_text(encoding="utf-8"))
    print(f"{caminho.name}: {len(js['nodes'])} nós")
    return caminho
