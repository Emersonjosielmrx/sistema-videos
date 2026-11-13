# -*- coding: utf-8 -*-
r"""Conversa com a API do n8n6 (n8n6.inovareinteligenciaartificial.com). Só biblioteca padrão.

    python n8n_servidor.py lista [--ativos]            lista os fluxos do servidor (id, ativo, nós, nome)
    python n8n_servidor.py copia-ativos                baixa todos os fluxos ATIVOS para ..\servidor-n8n6\ + LISTA.md
    python n8n_servidor.py importa <fluxo.json> [--sem-ativar]
                                                       cria (ou atualiza o de mesmo nome) e ativa
    python n8n_servidor.py get <id> [saida.json]       baixa um fluxo
    python n8n_servidor.py execucoes <id> [n]          últimas execuções (status, início, duração) de um fluxo
    python n8n_servidor.py execucao <id_execucao>      detalhe de uma execução (erro e último nó que rodou)

A chave da API é lida de N8N_API_KEY ou de D:\hipercool-materiais\fluxo-anuncio-api\n8n6_chave.txt (não copiar a
chave para outros arquivos). Endereço: N8N_URL (padrão https://n8n6.inovareinteligenciaartificial.com).
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CENTRAL = Path(__file__).resolve().parents[1]
BASE = os.environ.get("N8N_URL", "https://n8n6.inovareinteligenciaartificial.com").rstrip("/") + "/api/v1"
CHAVE = os.environ.get("N8N_API_KEY") or Path(r"D:\hipercool-materiais\fluxo-anuncio-api\n8n6_chave.txt").read_text().strip()
CONFIG_OK = ("executionOrder", "saveManualExecutions", "executionTimeout", "saveDataErrorExecution",
             "saveDataSuccessExecution", "saveExecutionProgress", "timezone", "callerPolicy", "errorWorkflow")


def api(metodo, caminho, corpo=None, tempo=120):
    req = urllib.request.Request(BASE + caminho, method=metodo,
                                 data=json.dumps(corpo).encode() if corpo is not None else None,
                                 headers={"X-N8N-API-KEY": CHAVE, "Content-Type": "application/json",
                                          "Accept": "application/json"})
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, timeout=tempo) as r:
                t = r.read()
                return r.status, json.loads(t) if t else {}
        except urllib.error.HTTPError as e:
            t = e.read()
            if e.code >= 500 and tentativa < 2:
                time.sleep(3 * (tentativa + 1))
                continue
            try:
                return e.code, json.loads(t)
            except ValueError:
                return e.code, {"message": t[:300].decode(errors="ignore")}
        except (urllib.error.URLError, TimeoutError) as e:
            if tentativa == 2:
                return 0, {"message": f"sem conexão: {e}"}
            time.sleep(3 * (tentativa + 1))
    return 0, {"message": "sem resposta"}


def todos(ativos=False):
    out, cursor = [], None
    while True:
        q = "?limit=250" + ("&active=true" if ativos else "") + (f"&cursor={cursor}" if cursor else "")
        st, d = api("GET", "/workflows" + q, tempo=300)
        if st != 200:
            raise SystemExit(f"lista falhou: {st} {d.get('message')}")
        out += d.get("data", [])
        cursor = d.get("nextCursor")
        if not cursor:
            return out


def nome_arquivo(nome):
    n = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", nome)
    n = "".join(ch for ch in n if ord(ch) < 0x2000 or 0x2010 <= ord(ch) <= 0x2027)
    return (re.sub(r"\s+", " ", n).strip(" .-·")[:110] or "sem nome").rstrip(" .")


def importa(arquivo, ativar=True):
    w = json.loads(Path(arquivo).read_text(encoding="utf-8"))
    corpo = {k: w[k] for k in ("name", "nodes", "connections") if k in w}
    corpo["settings"] = {k: v for k, v in (w.get("settings") or {}).items() if k in CONFIG_OK}
    st, lista = api("GET", "/workflows?limit=250&name=" + urllib.parse.quote(w["name"]))
    existe = next((x for x in lista.get("data", []) if x["name"] == w["name"]), None)
    if existe:
        estava_ativo = existe.get("active")
        if estava_ativo:
            api("POST", f"/workflows/{existe['id']}/deactivate")
        st, r = api("PUT", f"/workflows/{existe['id']}", corpo)
        wid = existe["id"]
        if st >= 300 and estava_ativo:  # a atualização falhou: o fluxo antigo volta a funcionar como estava
            api("POST", f"/workflows/{wid}/activate")
    else:
        st, r = api("POST", "/workflows", corpo)
        wid = r.get("id")
    print("salvar:", st, wid, r.get("message", ""))
    if wid and st < 300 and ativar:
        st2, r2 = api("POST", f"/workflows/{wid}/activate")
        print("ativar:", st2, r2.get("active"), r2.get("message", ""))
        if st2 >= 300:
            raise SystemExit(2)
    return wid


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    acao = sys.argv[1] if len(sys.argv) > 1 else "ajuda"
    if acao == "lista":
        for w in sorted(todos("--ativos" in sys.argv), key=lambda x: x.get("updatedAt", ""), reverse=True):
            print(("ON " if w["active"] else "   ") + w["id"], len(w.get("nodes", [])), w.get("updatedAt", "")[:10], w["name"])
    elif acao == "copia-ativos":
        destino = CENTRAL / "servidor-n8n6"
        destino.mkdir(exist_ok=True)
        linhas = ["# Fluxos ATIVOS no n8n6 (cópia)", "",
                  f"Baixados por `ferramentas\\n8n_servidor.py copia-ativos` em {time.strftime('%d/%m/%Y %H:%M')}. "
                  "Cópia de segurança do que está no ar; o que vale é o servidor.", "",
                  "| Fluxo | id | Nós | Atualizado |", "|---|---|---|---|"]
        for w in sorted(todos(True), key=lambda x: x["name"].lower()):
            st, completo = api("GET", f"/workflows/{w['id']}", tempo=300)
            if st != 200:
                print("falhou", w["id"], st)
                continue
            arq = destino / (nome_arquivo(w["name"]) + f" · {w['id']}.json")
            arq.write_text(json.dumps(completo, ensure_ascii=False, indent=1), encoding="utf-8")
            linhas.append(f"| {w['name'].replace('|', '/')} | `{w['id']}` | {len(completo.get('nodes', []))} | "
                          f"{completo.get('updatedAt', '')[:10]} |")
            print("ok", w["id"], w["name"][:80])
        (destino / "LISTA.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    elif acao == "importa":
        importa(sys.argv[2], ativar="--sem-ativar" not in sys.argv)
    elif acao == "get":
        st, r = api("GET", f"/workflows/{sys.argv[2]}")
        saida = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(f"{sys.argv[2]}.json")
        saida.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        print(st, r.get("name"), r.get("active"), "->", saida)
    elif acao == "execucoes":
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        st, r = api("GET", f"/executions?workflowId={sys.argv[2]}&limit={n}")
        for e in r.get("data", []):
            print(e["id"], e.get("status"), e.get("startedAt", "")[:19], e.get("stoppedAt", "")[:19], e.get("mode"))
    elif acao == "execucao":
        st, r = api("GET", f"/executions/{sys.argv[2]}?includeData=true", tempo=300)
        rd = ((r.get("data") or {}).get("resultData") or {})
        print("status:", r.get("status"), "| último nó:", rd.get("lastNodeExecuted"))
        if rd.get("error"):
            print("erro:", json.dumps(rd["error"], ensure_ascii=False)[:1500])
        for nome, execs in (rd.get("runData") or {}).items():
            e = execs[-1]
            erro = e.get("error")
            print(f"  {nome}: {e.get('executionStatus', '')} {e.get('executionTime', '')} ms"
                  + (f" ERRO {json.dumps(erro, ensure_ascii=False)[:400]}" if erro else ""))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
