# -*- coding: utf-8 -*-
"""Peças para montar fluxos n8n em Python (os geradores dos fluxos novos usam isto).

Cada função devolve o nome do nó; `Fluxo.liga(a, b)` liga a saída de `a` na entrada de `b`.
Os códigos JS dos nós Code ficam em arquivos .js ao lado do gerador (mais fácil de ler e testar).
"""
import json
import uuid
from pathlib import Path

REDIS = {"redis": {"id": "TgnZ028ccZYrorGM", "name": "Redis redis2 (landing pages)"}}


class Fluxo:
    def __init__(self, nome, tempo_max=1500):
        self.nome = nome
        self.nos = []
        self.ligacoes = {}
        self.settings = {"executionOrder": "v1", "saveManualExecutions": True, "executionTimeout": tempo_max,
                         "saveDataErrorExecution": "all", "saveDataSuccessExecution": "all"}

    # ───────── base ─────────
    def no(self, nome, tipo, versao, parametros, pos, credenciais=None, **extra):
        assert all(n["name"] != nome for n in self.nos), f"nó repetido: {nome}"
        n = {"parameters": parametros, "id": str(uuid.uuid5(uuid.NAMESPACE_URL, self.nome + "|" + nome)),
             "name": nome, "type": tipo, "typeVersion": versao, "position": list(pos)}
        if credenciais:
            n["credentials"] = credenciais
        n.update(extra)
        self.nos.append(n)
        return nome

    def liga(self, a, b, saida=0, entrada=0):
        saidas = self.ligacoes.setdefault(a, {"main": []})["main"]
        while len(saidas) <= saida:
            saidas.append([])
        saidas[saida].append({"node": b, "type": "main", "index": entrada})

    def cadeia(self, *nomes):
        for a, b in zip(nomes, nomes[1:]):
            self.liga(a, b)

    def json(self):
        return {"name": self.nome, "nodes": self.nos, "connections": self.ligacoes, "settings": self.settings,
                "pinData": {}, "meta": {"templateCredsSetupCompleted": True}}

    def grava(self, arquivo):
        Path(arquivo).write_text(json.dumps(self.json(), ensure_ascii=False, indent=1), encoding="utf-8")
        return arquivo

    # ───────── nós ─────────
    def webhook(self, nome, caminho, pos, metodo="GET"):
        p = {"path": caminho, "responseMode": "responseNode", "options": {}}
        if metodo != "GET":
            p["httpMethod"] = metodo
        return self.no(nome, "n8n-nodes-base.webhook", 2, p, pos,
                       webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, "webhook|" + caminho + "|" + metodo)))

    def responde(self, nome, corpo, pos, tipo="text/html; charset=UTF-8", status=None, cache="no-store"):
        cab = [{"name": "Content-Type", "value": tipo}, {"name": "Cache-Control", "value": cache},
               {"name": "Access-Control-Allow-Origin", "value": "*"}]
        op = {"responseHeaders": {"entries": cab}}
        if status:
            op["responseCode"] = status
        return self.no(nome, "n8n-nodes-base.respondToWebhook", 1.1,
                       {"respondWith": "text", "responseBody": corpo, "options": op}, pos)

    def responde_json(self, nome, expressao, pos, status=None):
        return self.responde(nome, "={{ JSON.stringify(" + expressao + ") }}", pos,
                             tipo="application/json; charset=UTF-8", status=status)

    def responde_arquivo(self, nome, pos, cache="public, max-age=86400", cabecalhos=None):
        cab = [{"name": "Cache-Control", "value": cache}, {"name": "Access-Control-Allow-Origin", "value": "*"},
               {"name": "Access-Control-Expose-Headers", "value": "*"}]
        cab += [{"name": k, "value": v} for k, v in (cabecalhos or {}).items()]
        return self.no(nome, "n8n-nodes-base.respondToWebhook", 1.1,
                       {"respondWith": "binary", "options": {"responseHeaders": {"entries": cab}}}, pos)

    def codigo(self, nome, js, pos, por_item=False):
        p = {"jsCode": js}
        if por_item:
            p["mode"] = "runOnceForEachItem"
        return self.no(nome, "n8n-nodes-base.code", 2, p, pos)

    def http(self, nome, url, pos, metodo="GET", corpo_json=None, formato="json", tempo=60000, nunca_erro=False,
             cabecalhos=None, continua_no_erro=False):
        p = {"url": url, "options": {"timeout": tempo}}
        if metodo != "GET":
            p["method"] = metodo
        if corpo_json is not None:
            p.update({"sendBody": True, "specifyBody": "json", "jsonBody": corpo_json})
        if cabecalhos:
            p.update({"sendHeaders": True, "headerParameters": {"parameters": [
                {"name": k, "value": v} for k, v in cabecalhos.items()]}})
        resp = {}
        if formato != "json":
            resp["responseFormat"] = formato
        if nunca_erro:
            resp["neverError"] = True
        if resp:
            p["options"]["response"] = {"response": resp}
        extra = {"onError": "continueRegularOutput"} if continua_no_erro else {}
        return self.no(nome, "n8n-nodes-base.httpRequest", 4.2, p, pos, **extra)

    def http_envia_arquivo(self, nome, url, pos, campo="files", binario="data", tempo=60000):
        """POST multipart com o arquivo binário do item (um envio por item). Resposta em texto (campo `data`).
        Envio de arquivo tem que ser por este nó: o httpRequest do Code manda binário como UTF-8 (estraga o arquivo)."""
        p = {"method": "POST", "url": url, "sendBody": True, "contentType": "multipart-form-data",
             "bodyParameters": {"parameters": [{"parameterType": "formBinaryData", "name": campo,
                                                "inputDataFieldName": binario}]},
             "options": {"timeout": tempo, "response": {"response": {"responseFormat": "text", "neverError": True}}}}
        return self.no(nome, "n8n-nodes-base.httpRequest", 4.2, p, pos, onError="continueRegularOutput")

    def redis_grava(self, nome, chave, valor, pos, validade=None):
        p = {"operation": "set", "key": chave, "value": valor, "keyType": "string"}
        if validade:
            p.update({"expire": True, "ttl": validade})
        return self.no(nome, "n8n-nodes-base.redis", 1, p, pos, REDIS)

    def redis_le(self, nome, chave, campo, pos):
        return self.no(nome, "n8n-nodes-base.redis", 1,
                       {"operation": "get", "propertyName": campo, "key": chave, "keyType": "string", "options": {}},
                       pos, REDIS, alwaysOutputData=True)

    def redis_conta(self, nome, chave, pos, validade=3600):
        return self.no(nome, "n8n-nodes-base.redis", 1,
                       {"operation": "incr", "key": chave, "expire": True, "ttl": validade}, pos, REDIS)

    def se(self, nome, expressao, pos):
        """Saída 0 = verdadeiro, 1 = falso. `expressao` = '={{ ... }}' que vale true/false."""
        return self.no(nome, "n8n-nodes-base.if", 2.2, {
            "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                           "conditions": [{"id": str(uuid.uuid5(uuid.NAMESPACE_URL, self.nome + nome)),
                                           "leftValue": expressao, "rightValue": "",
                                           "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                           "combinator": "and"}, "options": {}}, pos)

    def lote(self, nome, pos, tamanho=1):
        """Loop Over Items: saída 0 = terminou (todos os itens), saída 1 = próximo lote (ligar de volta aqui)."""
        return self.no(nome, "n8n-nodes-base.splitInBatches", 3, {"batchSize": tamanho, "options": {}}, pos)

    def espera(self, nome, segundos, pos):
        return self.no(nome, "n8n-nodes-base.wait", 1.1, {"amount": segundos}, pos,
                       webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, self.nome + "|espera|" + nome)))

    def agenda(self, nome, cron, pos):
        return self.no(nome, "n8n-nodes-base.scheduleTrigger", 1.2,
                       {"rule": {"interval": [{"field": "cronExpression", "expression": cron}]}}, pos)

    def manual(self, nome, pos):
        return self.no(nome, "n8n-nodes-base.manualTrigger", 1, {}, pos)

    def nota(self, texto, pos, largura=420, altura=260, cor=None):
        p = {"content": texto, "height": altura, "width": largura}
        if cor:
            p["color"] = cor
        n = sum(1 for x in self.nos if x["type"] == "n8n-nodes-base.stickyNote") + 1
        return self.no(f"Nota {n}", "n8n-nodes-base.stickyNote", 1, p, pos)


def js(pasta, arquivo, **troca):
    """Lê um .js e troca os marcadores __NOME__ (configurações) antes de pôr no nó."""
    t = (Path(pasta) / arquivo).read_text(encoding="utf-8")
    for k, v in troca.items():
        t = t.replace(f"__{k}__", v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
    return t
