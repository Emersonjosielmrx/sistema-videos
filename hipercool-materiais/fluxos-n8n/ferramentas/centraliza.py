# -*- coding: utf-8 -*-
r"""Junta numa pasta só os fluxos n8n espalhados pelo disco D:\ e monta o índice.

    python centraliza.py                 varre o D:\ inteiro (~20 min neste PC) e atualiza a biblioteca
    python centraliza.py --manifesto m.json   usa um manifesto já pronto (saída do varre_n8n)

O que faz:
- acha todo JSON com "nodes" + "connections" de nós n8n (também dentro de listas/exports com "data"/"workflow");
- tira as cópias iguais (mesmos nós e ligações = mesmo fluxo, mesmo que o arquivo tenha outro nome);
- separa por assunto em biblioteca\<assunto>\; quando o mesmo fluxo tem várias versões, a mais nova fica na pasta e
  as outras vão para biblioteca\<assunto>\_versoes\;
- grava INDICE.md (para ler) e indice.json (para scripts) com: de onde veio, quantos nós, o que precisa para rodar
  (Redis, Postgres, WhatsApp, IA...), se precisa instalar algo no servidor e se tem chave escrita dentro do fluxo.

Os arquivos originais NÃO são mexidos (os geradores dos projetos leem de lá). Esta pasta é a cópia central.
"""
import hashlib
import json
import os
import re
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

CENTRAL = Path(__file__).resolve().parents[1]
BIBLIOTECA = CENTRAL / "biblioteca"
RAIZ = "D:\\"
PULA_DIR = {"node_modules", ".git", "site-packages", "$RECYCLE.BIN", "System Volume Information", "SteamLibrary",
            "__pycache__", ".venv", "venv", "env", "caches", ".cache", "dist-packages", "Lib", "_recuperacao de HD"}
EXT = {".json", ".txt", ".n8n", ".bak"}
MAX = 30 * 1024 * 1024

# assunto: (regex no nome do fluxo ou no caminho, em ordem — o 1º que bater vence)
ASSUNTOS = [
    ("anuncio-video", r"an[uú]ncio"),
    ("livros", r"revis[aã]o de livro|farael"),
    ("hermes-ligacoes-telegram", r"hermes|liga[cç][aã]o|call"),
    ("monitoramento-e-avisos", r"vps|autocura|jarvis|backup|monitor|radar|not[ií]cias|tratamento de erros"),
    ("whatsapp-atendimento", r"atendimento|secretaria|whats|wuzapi|evolution|disparo|folow|follow|remarketing|"
                             r"vitrine|cartucho|agendamento|advogado|imoveis|im[oó]veis|edson|ajuda humana|"
                             r"conversas anteriores|elefante|presenca|desligamento|transcreve|analiza|macro|teste gratis"),
    ("video-e-imagem", r"v[ií]deo|video|reels|youtube|anime|viral|imagem|sensura|censura|shorts|cortes|recap"),
    ("paginas-e-apps", r"landing|p[aá]gina|app do neg|pwa|site|comunidade|backend|painel|financeiro|kg estrat"),
]
DONO_CREDENCIAL = re.compile(r"(?i)(sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}|\b\d{8,10}:[A-Za-z0-9_-]{35}\b|"
                             r"EAA[A-Za-z0-9]{40,}|ghp_[A-Za-z0-9]{30,}|xox[bp]-[A-Za-z0-9-]{20,}|"
                             r"\"(?:x-api-key|apikey|api_key|token|authorization)\"\s*,?\s*\"value\"\s*:\s*\"(?!=)(?!\{\{)[^\"]{16,}\")")


def fluxos_do(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get("nodes"), list) and isinstance(obj.get("connections"), dict):
            yield obj
        elif isinstance(obj.get("data"), (dict, list)):
            yield from fluxos_do(obj["data"])
        elif isinstance(obj.get("workflow"), dict):
            yield from fluxos_do(obj["workflow"])
    elif isinstance(obj, list):
        for x in obj[:500]:
            if isinstance(x, dict):
                yield from fluxos_do(x)


def ler_fluxos(p):
    """[(índice, fluxo)] de um arquivo; [] se não for fluxo n8n."""
    try:
        tam = os.path.getsize(p)
        if tam < 200 or tam > MAX:
            return []
        b = open(p, "rb").read()
        if b'"nodes"' not in b or b'"connections"' not in b:
            return []
        obj = json.loads(b.decode("utf-8-sig", errors="replace"))
    except (OSError, ValueError):
        return []
    out = []
    for i, w in enumerate(fluxos_do(obj)):
        nos = [n for n in w["nodes"] if isinstance(n, dict)]
        if nos and any("n8n" in str(n.get("type", "")) for n in nos):
            out.append((i, w))
    return out


def varrer():
    achados = []
    for pasta, dirs, arqs in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if d not in PULA_DIR and not d.startswith("tmp_hf")]
        if Path(pasta).resolve().is_relative_to(CENTRAL):  # não indexa a própria biblioteca
            dirs[:] = []
            continue
        for a in arqs:
            if os.path.splitext(a)[1].lower() in EXT:
                p = os.path.join(pasta, a)
                achados += [{"arquivo": p, "indice": i} for i, _ in ler_fluxos(p)]
    return achados


def assinatura(w):
    nos = [n for n in w["nodes"] if isinstance(n, dict)]
    canon = json.dumps({"nodes": nos, "connections": w["connections"]}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(canon.encode()).hexdigest()[:12]


def assunto_de(nome, caminho):
    """Assunto pelo nome do fluxo; só quando o nome não diz nada, pelo caminho de onde ele veio."""
    for alvo in (nome.lower(), caminho.lower()):
        for a, rx in ASSUNTOS:
            if re.search(rx, alvo):
                return a
    return "outros"


def nome_base(nome):
    """Nome sem ' copy', '(1)', ' - ok', datas soltas: junta as versões do mesmo fluxo."""
    n = re.sub(r"\s*\(\d+\)\s*$", "", nome.strip())
    n = re.sub(r"(?i)\s+copy(\s*\d+)?\b", "", n)
    n = re.sub(r"(?i)\s*-\s*ok(\s*-.*)?$", "", n)
    return re.sub(r"\s+", " ", n).strip().lower()


def nome_arquivo(nome):
    n = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", nome)
    n = "".join(ch for ch in n if ord(ch) < 0x2000 or 0x2010 <= ord(ch) <= 0x2027)  # tira emoji, mantém acento e "·"
    n = re.sub(r"\s+", " ", n).strip(" .-·")
    return (n[:110] or "sem nome").rstrip(" .")


def requisitos(w):
    """O que o fluxo precisa para rodar e se pede algo instalado no servidor."""
    tipos = [str(n.get("type", "")) for n in w["nodes"] if isinstance(n, dict)]
    texto = json.dumps(w, ensure_ascii=False)
    precisa, instalar = set(), set()
    mapa = {"redis": "Redis", "postgres": "Postgres", "mySql": "MySQL", "supabase": "Supabase", "telegram": "Telegram",
            "googleSheets": "Google Planilhas", "googleDrive": "Google Drive", "gmail": "Gmail",
            "lmChatOpenAi": "IA (OpenAI/roteador)", "openAi": "IA (OpenAI/roteador)", "lmChatGoogleGemini": "Gemini",
            "agent": "Agente de IA", "youTube": "YouTube (OAuth)", "facebookGraphApi": "Facebook/Instagram Graph",
            "httpRequest": "HTTP", "ftp": "FTP/SFTP", "ssh": "SSH", "executeCommand": "Comando no servidor",
            "readWriteFile": "Arquivo no disco do servidor", "readBinaryFile": "Arquivo no disco do servidor",
            "writeBinaryFile": "Arquivo no disco do servidor", "localFileTrigger": "Pasta no servidor"}
    for t in tipos:
        curto = t.split(".")[-1]
        for k, v in mapa.items():
            if curto == k or curto.startswith(k):
                precisa.add(v)
        if not (t.startswith("n8n-nodes-base.") or t.startswith("@n8n/")):
            instalar.add(f"nó da comunidade {t}")
        if curto in ("executeCommand",):
            instalar.add("programa no servidor (Execute Command)")
        if curto in ("readWriteFile", "readBinaryFile", "writeBinaryFile", "localFileTrigger"):
            instalar.add("arquivos no disco do servidor")
    if re.search(r"video-oficina|:8000/videos", texto):
        instalar.add("video-oficina (servidor de vídeo próprio)")
    if re.search(r"(?i)evolution|/message/sendText|wuzapi|/chat/send", texto):
        precisa.add("WhatsApp (Evolution/WuzAPI)")
    if re.search(r"(?i)localhost|127\.0\.0\.1|host\.docker\.internal", texto):
        instalar.add("serviço local (localhost) no servidor")
    for dom, nome in (("json2video", "JSON2Video"), ("shotstack", "Shotstack"), ("verygoodffmpeg", "Very Good FFmpeg"),
                      ("translate_tts", "voz Google Tradutor"), ("wsrv.nl", "wsrv.nl"), ("pollinations", "Pollinations"),
                      ("elevenlabs", "ElevenLabs"), ("catbox", "catbox"), (":20128", "roteador OmniRoute"),
                      ("api.cloudflare.com", "Cloudflare Workers AI"), ("generativelanguage", "Gemini API"),
                      ("graph.facebook.com", "Graph API (Instagram/Facebook)"), ("api.telegram.org", "Telegram API")):
        if dom in texto:
            precisa.add(nome)
    chave = bool(DONO_CREDENCIAL.search(texto))
    return sorted(precisa), sorted(instalar), chave


def main():
    if "--manifesto" in sys.argv:
        itens = json.load(open(sys.argv[sys.argv.index("--manifesto") + 1], encoding="utf-8"))
    else:
        t0 = time.time()
        itens = varrer()
        print(len(itens), "fluxos achados em", round(time.time() - t0), "s")

    distintos = {}  # hash -> registro
    for it in itens:
        lidos = dict(ler_fluxos(it["arquivo"]))
        w = lidos.get(it.get("indice", 0))
        if not w:
            continue
        h = assinatura(w)
        mod = os.path.getmtime(it["arquivo"])
        reg = distintos.get(h)
        if reg:
            reg["copias"].append(it["arquivo"])
            if mod > reg["mod"]:
                reg.update(mod=mod)
            continue
        nome = str(w.get("name") or Path(it["arquivo"]).stem)
        precisa, instalar, chave = requisitos(w)
        distintos[h] = {"hash": h, "nome": nome, "fluxo": w, "origem": it["arquivo"], "copias": [], "mod": mod,
                        "nos": len(w["nodes"]), "assunto": assunto_de(nome, it["arquivo"]), "base": nome_base(nome),
                        "precisa": precisa, "instalar": instalar, "chave_no_fluxo": chave}

    if BIBLIOTECA.exists():
        shutil.rmtree(BIBLIOTECA)
    grupos = defaultdict(list)
    for r in distintos.values():
        grupos[(r["assunto"], r["base"])].append(r)
    indice = []
    usados = set()
    for (assunto, _), regs in sorted(grupos.items()):
        regs.sort(key=lambda r: r["mod"], reverse=True)
        for k, r in enumerate(regs):
            pasta = BIBLIOTECA / assunto / ("_versoes" if k else "")
            nome = nome_arquivo(r["nome"])
            if k:
                nome += " · " + time.strftime("%Y-%m-%d %H%M", time.localtime(r["mod"])) + " · " + r["hash"][:6]
            destino = pasta / (nome + ".json")
            n = 2
            while str(destino).lower() in usados:
                destino = pasta / f"{nome} ({n}).json"
                n += 1
            usados.add(str(destino).lower())
            pasta.mkdir(parents=True, exist_ok=True)
            destino.write_text(json.dumps(r["fluxo"], ensure_ascii=False, indent=1), encoding="utf-8")
            indice.append({k2: r[k2] for k2 in ("hash", "nome", "assunto", "nos", "precisa", "instalar",
                                                "chave_no_fluxo", "origem", "copias")}
                          | {"arquivo": str(destino.relative_to(CENTRAL)), "versao_antiga": bool(k),
                             "modificado": time.strftime("%Y-%m-%d %H:%M", time.localtime(r["mod"]))})

    (CENTRAL / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    escrever_md(indice)
    print(len(indice), "fluxos distintos;", sum(not x["versao_antiga"] for x in indice), "atuais")


def escrever_md(indice):
    atuais = [x for x in indice if not x["versao_antiga"]]
    linhas = ["# Índice da biblioteca de fluxos n8n", "",
              f"Gerado por `ferramentas\\centraliza.py` em {time.strftime('%d/%m/%Y %H:%M')}. "
              f"{len(atuais)} fluxos atuais + {len(indice) - len(atuais)} versões antigas (em `_versoes`).", "",
              "Legenda: **n8n puro** = roda num n8n comum só com credenciais (nada para instalar no servidor). "
              "⚠️ chave = tem chave/token escrito dentro do fluxo (trocar por credencial antes de passar adiante).", ""]
    por_assunto = defaultdict(list)
    for x in atuais:
        por_assunto[x["assunto"]].append(x)
    for assunto in sorted(por_assunto):
        linhas += [f"## {assunto} ({len(por_assunto[assunto])})", "",
                   "| Fluxo | Nós | Precisa | Instalar no servidor | Veio de |", "|---|---|---|---|---|"]
        for x in sorted(por_assunto[assunto], key=lambda x: x["nome"].lower()):
            inst = ", ".join(x["instalar"]) or "**n8n puro**"
            origem = x["origem"].replace("|", "/")
            extra = f" (+{len(x['copias'])} cópia{'s' if len(x['copias']) > 1 else ''})" if x["copias"] else ""
            nome = x["nome"].replace("|", "/") + (" ⚠️ chave" if x["chave_no_fluxo"] else "")
            linhas.append(f"| [{nome}]({x['arquivo'].replace(chr(92), '/').replace(' ', '%20')}) | {x['nos']} | "
                          f"{', '.join(x['precisa']) or '-'} | {inst} | `{origem}`{extra} |")
        linhas.append("")
    (CENTRAL / "INDICE.md").write_text("\n".join(linhas), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
