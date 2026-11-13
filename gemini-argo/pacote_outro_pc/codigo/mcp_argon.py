#!/usr/bin/env python3
r"""MCP (stdio) com a ferramenta ask_argon: pergunta ao Gemini 4 Argon pelo gemini_proxy.py (porta 20140).

Passa pelo proxy para usar a mesma fila e o mesmo limite de Chrome abertos.
Registro: claude mcp add --scope user gemini-argon -- python -I D:\gemini-argo\mcp_argon.py
"""
import json
import sys
import urllib.request

PROXY = "http://127.0.0.1:20140/v1/chat/completions"

TOOLS = [{
    "name": "ask_argon",
    "description": ("Pergunta ao Gemini 4 Argon (Google, raciocínio Alto). Use em tarefas difíceis: "
                    "arquitetura, depuração complicada, matemática, revisão crítica, segunda opinião. "
                    "Demora de 1 a 5 min. Mande o contexto todo na pergunta: ele não vê os arquivos."),
    "inputSchema": {
        "type": "object",
        "properties": {"question": {"type": "string", "description": "Pergunta completa, com o contexto necessário"}},
        "required": ["question"],
    },
}]


def enviar(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def perguntar(texto):
    corpo = json.dumps({"model": "gemini-4-argon", "messages": [{"role": "user", "content": texto}]}).encode()
    req = urllib.request.Request(PROXY, data=corpo, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"], False
    except urllib.error.HTTPError as e:
        return f"Erro do Argon: {e.read().decode(errors='replace')[:500]}", True
    except Exception as e:
        return f"Proxy do Argon fora do ar ({e}). Rode: python -I D:\\gemini-argo\\manter_tunnel.py", True


def tratar(req):
    metodo, rid = req.get("method", ""), req.get("id")
    if metodo == "initialize":
        versao = req.get("params", {}).get("protocolVersion", "2024-11-05")
        enviar({"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": versao,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "gemini-argon", "version": "1.1.0"}}})
    elif metodo == "tools/list":
        enviar({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}})
    elif metodo == "tools/call":
        p = req.get("params", {})
        if p.get("name") != "ask_argon":
            enviar({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "ferramenta desconhecida"}})
            return
        texto, erro = perguntar(p.get("arguments", {}).get("question", ""))
        enviar({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": texto}], "isError": erro}})
    elif metodo == "ping":
        enviar({"jsonrpc": "2.0", "id": rid, "result": {}})
    elif rid is not None:
        enviar({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"método desconhecido: {metodo}"}})


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue
        try:
            tratar(json.loads(linha))
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    main()
