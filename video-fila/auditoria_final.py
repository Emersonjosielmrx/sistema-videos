"""3ª camada das melhorias contínuas (24/10, pedido da dona): o Opus 4.6 do Antigravity como JUIZ FINAL.

Toda aplicação que as camadas 1 e 2 (Kiro + Gemini) aceitaram entra numa fila de auditoria com prioridade (P0/P1/P2).
Quando o Opus está disponível DE VERDADE (sistema da dona D:\\monitor_opus.py: leitura fresca, "funcionando", 3+ contas
com crédito; a dona sem usar o Opus no VS Code; botão da área de trabalho ligado; tetos do dia), um lote de até 4 vai
num processo separado (camada_opus.py: chamada direta à API pela porta 20133, sem ferramentas, com tempo máximo).
O Opus devolve MANTER | DESFAZER | REFAZER | DONA | PRECISO_VER por item, e quem executa é o código (desfaz), o Kiro
(refaz com a crítica, pelo fluxo normal) ou a dona (o que não é arquivo). Se o Opus cair no meio, o que ele já decidiu
vale e o resto volta pra fila. Tudo fica documentado em auditoria_opus\\ e no MELHORIAS_CONTINUAS.md; a lição volta
pras camadas 1 e 2. O Opus nunca roda dentro do passo() (a trava do motor vale 180 s) nem na fila do painel.
Plano completo: revisão de 24/10 (pasta de rascunho da sessão) — resumo no topo do melhoria_continua.py.
"""
import difflib
import json
import re
import secrets
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
PASTA = BASE / "estado" / "opus"
DOCS = BASE / "auditoria_opus"
INDICE = DOCS / "INDICE.md"
MONITOR = Path(r"D:\opus_monitor.json")
VSCODE_PROJETOS = Path(r"C:\Users\Haylla\.claude-vscode\projects")
PYW = Path(r"D:\veo\venv\Scripts\pythonw.exe")
GUARDA = BASE / "config" / "melhoria_guarda.json"
SEM_JANELA = 0x08000000
DESTACADO = 0x00000008 | 0x00000200 | SEM_JANELA  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | sem janela
ESTADOS_FINAIS = ("feito", "dona", "vencido", "nao_auditado")
VEREDITOS = ("MANTER", "DESFAZER", "REFAZER", "DONA", "PRECISO_VER")

# o que no diff costuma esconder os erros de 23-24/10 (linhas mudadas, não o arquivo inteiro)
SINAIS_P0 = [
    (re.compile(r"datetime|timezone|\butc|tzinfo|astimezone|fuso|hor[aá]rio|\bhora_", re.I), "mexe em data/hora/fuso"),
    (re.compile(r"postar_|agend|limite_?di|publish|upload|\bcana(l|is)\b", re.I), "mexe em postagem"),
    (re.compile(r"\block|trava|cooldown|\bram_|mem[oó]ria|\bpausa", re.I), "mexe em trava/pausa/RAM"),
    (re.compile(r"retry|tentativa|while\s+True|\.sleep\(", re.I), "mexe em repetição/laço"),
    (re.compile(r"\bmodel|modelo|api_?key|\bchave|\btoken|gemini-|claude-", re.I), "mexe em modelo/API/chave"),
]
PROTECAO = re.compile(r"#.*\b(nunca|n[aã]o|proteg|trava|bloque|regra|dona|cuidado|importante)\b", re.I)

SISTEMA_JUIZ = """Você é o AUDITOR FINAL (3ª camada) das melhorias contínuas automáticas dos projetos de vídeo da dona.
Duas IAs (Kiro Sonnet 4.5 e Gemini Flash) já procuraram, planejaram, aplicaram e revisaram cada mudança do DOSSIÊ.
Mesmo assim, em 23-24/10, 18 de 26 mudanças aceitas por elas estavam erradas. Você julga cada aplicação e decide.
Você NÃO tem ferramentas: julgue pelo dossiê. Se faltar um dado decisivo, peça com PRECISO_VER (uma vez por item).

CHECKLIST (são os erros reais que já passaram pelas duas IAs):
1. Premissa datada: a "prova" é de antes da última mudança do arquivo, de outro dia, ou de linha sem data? Horário
   com "Z"/UTC está 3 h na frente de Brasília (a linha AGORA do dossiê diz a hora certa).
2. Efeito fora de arquivo: rodou pip, moveu/recortou/apagou mídia, rodou rotina que posta/agenda, parou tarefa, matou
   processo, copiou cookies/login? O desfazer NÃO volta isso: veredito DONA, com os passos em "fora_de_arquivo".
3. Proteção removida: tirou trava, checagem, pausa, limite, regra comentada ("nunca", "não", "trava")?
4. Regra da dona: postagem só agendada e pelo navegador; nunca apagar (mover pro Drive); não mexer em
   login/conta/cookies; não gastar dinheiro; não mexer em config de postagem; mídia/voz/formato só com amostra aprovada.
5. Troca de modelo/API/chave sem uma chamada real que funcionou.
6. Laço/retry que repete comando que cria processo ou gasta crédito; aborto/limite novo sem medir o normal antes.
7. O código novo chega mesmo no caminho que diz consertar? Resolve a causa real ou só o sintoma?
8. Efeito colateral em outro programa que lê/escreve o mesmo arquivo de estado.

VEREDITOS:
- MANTER: está certo (ou o risco é desprezível).
- DESFAZER: está errado e voltar como estava resolve. Exige "prova" (trecho exato do diff/comando/log do dossiê) e
  confiança >= 3.
- REFAZER: a ideia vale mas foi mal feita: desfaz e outra IA refaz seguindo exatamente a instrução em "refazer".
- DONA: precisa de decisão humana (efeito fora de arquivo, regra ambígua, mudança que a própria dona aprovou, risco
  alto sem certeza). Em "por_que", em palavras simples, o que ela precisa decidir; em "fora_de_arquivo", os passos.
- PRECISO_VER: falta um dado decisivo; em "ver", até 3 trechos ("caminho:linha_ini-linha_fim" ou
  "log:caminho:texto a procurar").
Você também pode errar: em dúvida real entre MANTER e DESFAZER, prefira DONA a DESFAZER sem prova.

SAÍDA: para cada item, assim que decidir, um bloco exatamente assim (JSON válido):
<<<AUDITORIA {"job": "<id do item>", "veredito": "MANTER|DESFAZER|REFAZER|DONA|PRECISO_VER", "por_que": "1 a 3 linhas",
"prova": "trecho exato do dossiê ou vazio", "fora_de_arquivo": "passos pra dona ou vazio", "licao": "regra nova pro
agente (só se for um padrão novo; no máximo 1 no lote) ou vazio", "refazer": "instrução exata ou vazio",
"quem_deixou_passar": "buscador|votante|critico|executor|revisor|guarda|ninguem", "confianca": <número de 1 a 5>,
"ver": []} AUDITORIA>>>
Sem texto longo fora dos blocos. Escreva em pt-BR."""

PEDIDO_AUDITOR_RESERVA = """MELHORIA CONTÍNUA — você é o AUDITOR RESERVA: só LÊ, não muda nada. O auditor final (Opus) está
fora do ar há horas e esta aplicação tem sinal de risco alto. Leia o dossiê em {dossie} (abra o arquivo) e julgue a
aplicação {job} pelas regras e pelo checklist que estão no começo dele. Seu veredito NÃO desfaz nada: só avisa a dona.
Antes do veredito escreva uma seção ANÁLISE respondendo item por item o checklist. Termine com o bloco
<<<AUDITORIA {{...}} AUDITORIA>>> no formato do dossiê e, depois dele, STATUS: OK."""


def _m():
    import melhoria_continua
    return melhoria_continua


def _co():
    """camada_opus (o juiz em processo separado). None se ainda não existe: a camada fica parada."""
    try:
        import camada_opus
        return camada_opus
    except Exception:  # noqa: BLE001
        return None


def _agora_txt():
    agora = datetime.now().astimezone()
    return (f"AGORA: {agora:%d/%m/%Y %H:%M} em Brasília (UTC-3) = {datetime.now(timezone.utc):%H:%M} UTC. "
            "Linha de log com 'Z' ou UTC está 3 h na frente de Brasília; linha sem data não prova nada de hoje.")


def padrao(e):
    e.setdefault("auditar", {})          # aplicação -> entrada da fila de auditoria
    e.setdefault("auditoria_dona", {})   # aplicação -> o que a auditoria quer que a dona decida (Telegram)
    o = e.setdefault("opus", {})
    o.setdefault("lote", None)
    o.setdefault("fora_ate", 0)
    o.setdefault("fora_desde_leitura", None)
    o.setdefault("dia", "")
    o.setdefault("chamadas", 0)
    o.setdefault("tokens", 0)
    o.setdefault("horas", [])
    o.setdefault("placar", {})
    o.setdefault("ultimo", None)
    o.setdefault("espera", "")
    hoje = datetime.now().strftime("%Y-%m-%d")
    if o["dia"] != hoje:
        o.update(dia=hoje, chamadas=0, tokens=0)
    o["horas"] = [h for h in o["horas"] if time.time() - h < 3600]
    return e


# ─── fila ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def _diff(ap, contexto=3, limite=60000):
    """(texto, arquivos, linhas mudadas, arquivos que mudaram depois) do backup x arquivo atual."""
    partes, n_lin, depois = [], 0, []
    for orig, info in (ap.get("manifesto") or {}).items():
        try:
            antes = Path(info["backup"]).read_text(encoding="utf-8", errors="replace") if info.get("existia") else ""
        except OSError:
            antes = ""
        try:
            agora = Path(orig).read_text(encoding="utf-8", errors="replace")
        except OSError:
            agora = ""
        linhas = list(difflib.unified_diff(antes.splitlines(True), agora.splitlines(True), "antes/" + Path(orig).name,
                                           "agora/" + Path(orig).name, n=contexto))
        n_lin += sum(1 for ln in linhas if ln[:1] in "+-" and not ln.startswith(("+++", "---")))
        if info.get("depois_sha"):
            import painel_ia
            if painel_ia._sha(orig) != info["depois_sha"]:
                depois.append(orig)
        partes.append(f"### {orig}" + (" (MUDOU DEPOIS desta aplicação)" if orig in depois else "")
                      + f"\n{''.join(linhas) or '(sem diferença)'}")
    return "\n".join(partes)[:limite], len(ap.get("manifesto") or {}), n_lin, depois


def _prioridade(ent, ap):
    """(0|1|2, motivos). 0 = vai na hora; 2 = só se sobrar Opus (vence em opus_validade_h)."""
    m = _m()
    p0, p1 = [], []
    if ap.get("suspeitos") or ap.get("bloqueios"):
        p0.append("a guarda viu comando suspeito/bloqueado")
    vs = [v for v, _mo in (ent.get("revisores") or {}).values()]
    if "DUVIDA" in vs or "dúvida" in (ent.get("nota") or ""):
        p0.append("revisão em dúvida")
    cmds = m._comandos(ap["id"], so_lista=True)
    if not ap.get("manifesto"):
        # 24/10 (achado 29): o append obrigatório no VIGIA_DIARIO e os comandos só de leitura não contam
        reais = []
        try:
            import painel_ia
            for cmd, _saida, _erro in cmds:
                segs = painel_ia._vistas_comando(cmd)["segmentos"]
                if any(s["classe"] in ("outro", "interp") and "VIGIA_DIARIO" not in s["texto"] for s in segs):
                    reais.append(cmd)
        except Exception:  # noqa: BLE001
            reais = cmds
        if reais:
            p0.append("só rodou comandos (nada que o desfazer volte)")
    texto, n_arq, n_lin, _depois = _diff(ap)
    mudadas = "\n".join(ln for ln in texto.splitlines() if ln[:1] in "+-" and not ln.startswith(("+++", "---")))
    for rx, motivo in SINAIS_P0:
        if rx.search(mudadas):
            p0.append(motivo)
    if any(PROTECAO.search(ln) for ln in texto.splitlines() if ln.startswith("-") and not ln.startswith("---")):
        p0.append("tirou linha de proteção comentada")
    if vs.count("APROVADO") < 2:
        p1.append(f"só {vs.count('APROVADO')} revisor(es) aprovou(aram)")
    if ap.get("status_ia") in (None, "REVISAR"):
        p1.append(f"terminou como {ap.get('status_ia')}")
    item = ent.get("item") or {}
    if int(item.get("risco", 0) or 0) >= 3:
        p1.append(f"risco {item.get('risco')}")
    if n_lin > 30:
        p1.append(f"{n_lin} linhas")
    if n_arq > 1:
        p1.append(f"{n_arq} arquivos")
    if any("auditoria Opus" in str(k) for k in item.get("criticas") or []):
        p1.append("é refazimento de uma auditoria")
    if p0:
        return 0, p0 + p1
    if p1:
        return 1, p1
    return 2, ["os revisores aprovaram e é pequena"]


def enfileirar(e, c, ap, nota="", revisores=None, item=None, dona=False):
    """Chamada pelo motor quando aceita uma aplicação (e quando a dona aprova uma pelo Telegram)."""
    padrao(e)
    if not ap or ap["id"] in e["auditar"]:
        return
    ent = {"job": ap["id"], "pai": ap.get("pai"), "projeto": ap.get("projeto"), "entrou": time.time(),
           "nota": nota, "revisores": revisores or {}, "item": item, "dona": bool(dona), "estado": "pendente",
           "tentativas": 0, "modelo_exec": ap.get("modelo")}
    try:
        ent["prio"], ent["motivos"] = _prioridade(ent, ap)
    except Exception as ex:  # noqa: BLE001 — sem prioridade calculada, vai como P1
        ent["prio"], ent["motivos"] = 1, [f"prioridade não calculada ({type(ex).__name__})"]
    e["auditar"][ap["id"]] = ent
    _m().log(f"{ap['id']}: na fila da auditoria final como P{ent['prio']} ({'; '.join(ent['motivos'])[:120]})")


# ─── gatilho ──────────────────────────────────────────────────────────────────────────────────────────────────────
def _leitura():
    """O que o monitor da dona gravou (None se o arquivo não abre ou está cortado)."""
    try:
        return json.loads(MONITOR.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def dona_usando_opus(minutos=20, versao="4-6"):
    """A dona está usando o Opus no VS Code agora? (conversa com o Opus gravada nos últimos `minutos`).
    versao "4-6" = Antigravity (cota da 3ª camada); "5-5" = contas Claude (cota do Opus 5.5) — cotas diferentes."""
    corte = time.time() - minutos * 60
    rx = re.compile(r'"model"\s*:\s*"(?:antigravity/|agy/|cc/|claude/)?claude-opus-' + re.escape(versao))
    try:
        arqs = [p for p in VSCODE_PROJETOS.glob("*/*.jsonl") if p.stat().st_mtime >= corte]
    except OSError:
        return False
    qualquer = re.compile(r'"model"\s*:\s*"([^"]+)"')
    for p in arqs:  # 24/10 (achado 26): lê de trás pra frente (blocos de 1 MB, até 8 MB) e decide pelo ÚLTIMO modelo
        try:
            tam = p.stat().st_size
            with open(p, "rb") as f:
                fim = tam
                while fim > 0 and tam - fim < 8 * 1024 * 1024:
                    ini = max(0, fim - 1024 * 1024)
                    f.seek(ini)
                    bloco = f.read(fim - ini + 2048).decode("utf-8", "replace")  # +2 KB: modelo cortado na borda
                    achados = qualquer.findall(bloco)
                    if achados:
                        if rx.search(f'"model":"{achados[-1]}"'):
                            return True
                        break
                    fim = ini
        except OSError:
            continue
    return False


def disponivel(c, e):
    """(ok, motivo): todas as condições pra mandar um lote ao Opus agora."""
    co = _co()
    if not c.get("opus_camada"):
        return False, "camada desligada na config"
    if co is None:
        return False, "camada_opus.py não está instalado"
    if co.desligada():
        return False, "desligada pelo botão da área de trabalho"
    if co.lote_vivo():
        return False, "já tem um lote rodando"
    o = e["opus"]
    if o["chamadas"] >= int(c["opus_chamadas_dia_max"]):
        return False, f"já fiz {o['chamadas']} chamadas hoje (teto)"
    if o["tokens"] >= int(c["opus_tokens_dia_max"]):
        return False, f"já gastei {o['tokens']} tokens hoje (teto)"
    if len(o["horas"]) >= int(c["opus_chamadas_hora_max"]):
        return False, "teto de chamadas por hora"
    mon = _leitura()
    if not mon or not isinstance(mon.get("leitura"), dict):
        return False, "monitor do Opus sem leitura"
    lei = mon["leitura"]
    try:
        idade = (datetime.now().astimezone() - datetime.fromisoformat(lei["em"])).total_seconds() / 60
    except (KeyError, TypeError, ValueError):
        return False, "leitura do monitor ilegível"
    if idade > float(c["opus_frescor_min"]):
        return False, f"leitura do monitor velha ({idade:.0f} min)"
    if not mon.get("funcionando"):
        return False, "monitor não confirmou que o Opus responde"
    if time.time() < float(o["fora_ate"]) or (o.get("fora_desde_leitura") and lei["em"] <= o["fora_desde_leitura"]):
        return False, "o último lote falhou; espero leitura nova do monitor"
    precisa = int(c["opus_contas_min"])
    if dona_usando_opus(int(c["opus_dona_janela_min"])):
        precisa = int(c["opus_contas_min_dona_usando"])
    if int(lei.get("com_credito") or 0) < precisa:
        return False, f"{lei.get('com_credito')} conta(s) com crédito (preciso de {precisa})"
    m = _m()
    if m._ram_gb() < float(c["opus_ram_min_gb"]):
        return False, "pouca memória livre"
    return True, f"{lei.get('com_credito')} contas com crédito"


def _pendentes(e, c):
    return sorted((x for x in e["auditar"].values()
                   if x["estado"] == "pendente" and int(x["prio"]) <= int(c["opus_prioridade_min"])),
                  key=lambda x: (int(x["prio"]), x["entrou"]))


def _lote_pronto(e, c):
    pend = _pendentes(e, c)
    if not pend:
        return []
    if (any(int(x["prio"]) == 0 for x in pend) or len(pend) >= int(c["opus_lote_max"])
            or time.time() - pend[0]["entrou"] >= float(c["opus_lote_espera_min"]) * 60):
        return pend[:int(c["opus_lote_max"])]
    return []


# ─── dossiê ───────────────────────────────────────────────────────────────────────────────────────────────────────
def _segredos():
    try:
        return [re.compile(r, re.I) for r in json.loads(GUARDA.read_text(encoding="utf-8")).get("segredos", [])]
    except (OSError, ValueError, re.error):
        return [re.compile(r"secrets[\\/]|claude_proxy\.json|monitor_opus\.py|\.env\b|settings_\d", re.I)]


def _erros_novos(ap, limite=15):
    """Linhas de erro dos logs do projeto escritos depois da aplicação (com o nome do log)."""
    import painel_ia
    m = _m()
    pasta = painel_ia.PROJETOS.get(ap.get("projeto"), ("", str(BASE)))[1]
    try:
        desde = datetime.fromisoformat(ap.get("fim") or ap["criado"]).timestamp()
    except (KeyError, ValueError):
        return ""
    achados = []
    for p in m._logs_do_projeto(pasta):
        try:
            if p.stat().st_mtime < desde:
                continue
            with open(p, "rb") as f:
                f.seek(max(0, p.stat().st_size - 200_000))
                linhas = f.read().decode("utf-8", "replace").splitlines()
        except OSError:
            continue
        achados += [f"[{p.name}] {ln.strip()[:220]}" for ln in linhas
                    if re.search(r"Traceback|\bERRO|Error|Exception|FALHA", ln)][-5:]
    return "\n".join(achados[-limite:])


def _pode_ler(caminho, permitidos):
    """24/10 (achado 16): PRECISO_VER só lê arquivo do manifesto do item, os backups e as pastas logs\\ (e nunca o
    estado\\painel_ia\\*.jsonl, que tem o conteúdo dos cookies)."""
    try:
        p = str(Path(caminho).resolve()).lower()
    except (OSError, ValueError):
        return False
    if re.search(r"[\\/]estado[\\/]painel_ia[\\/][^\\/]*\.jsonl$", p):
        return False
    if re.search(r"[\\/]logs?[\\/]", p) or p.endswith(".log"):
        return True
    return any(p == str(Path(x).resolve()).lower() for x in permitidos if x)


def _ler_trechos(pedidos, permitidos=None):
    """PRECISO_VER: até 3 trechos, só leitura, até 4 mil caracteres cada, nunca de arquivo de segredo.
    permitidos=None não limita (teste); o _colher passa o manifesto + backups do item."""
    seg, saida = _segredos(), []
    if not isinstance(pedidos, list):  # 24/10 (achado 23): 'ver' que não é lista travava a camada
        pedidos = [pedidos] if isinstance(pedidos, str) and pedidos.strip() else []
    for ped in pedidos[:3]:
        ped = str(ped).strip()
        try:
            if ped.lower().startswith("log:"):
                # 24/10 (achado 8): o texto procurado pode ter ':' (hora, 'ERRO:')
                mm = re.match(r"^log:\s*([A-Za-z]:[^:]*|[^:]*):(.*)$", ped, re.S | re.I)
                caminho, procura = (mm.group(1).strip(), mm.group(2).strip()) if mm else (ped[4:].strip(), "")
                if any(s.search(caminho) for s in seg):
                    saida.append(f"{ped}: (recusado: arquivo de segredo)")
                    continue
                if permitidos is not None and not _pode_ler(caminho, permitidos):
                    saida.append(f"{ped}: (recusado: só arquivos do item, backups e logs)")
                    continue
                linhas = Path(caminho).read_text(encoding="utf-8", errors="replace").splitlines()
                hits = [ln for ln in linhas if procura.lower() in ln.lower()][-40:]
                saida.append(f"--- {ped}\n" + "\n".join(hits)[:4000])
            else:
                mm = re.match(r"^(.*?):(\d+)(?:-(\d+))?$", ped)
                caminho, ini, fim = (mm.group(1), int(mm.group(2)), int(mm.group(3) or mm.group(2))) if mm else (ped, 1, 120)
                if any(s.search(caminho) for s in seg):
                    saida.append(f"{ped}: (recusado: arquivo de segredo)")
                    continue
                if permitidos is not None and not _pode_ler(caminho, permitidos):
                    saida.append(f"{ped}: (recusado: só arquivos do item, backups e logs)")
                    continue
                linhas = Path(caminho).read_text(encoding="utf-8", errors="replace").splitlines()
                trecho = "\n".join(f"{i}: {ln}" for i, ln in enumerate(linhas[ini - 1:fim], ini))
                saida.append(f"--- {ped}\n{trecho[:4000]}")
        except (OSError, ValueError) as ex:
            saida.append(f"--- {ped}: (não deu pra ler: {type(ex).__name__})")
    return [_limpo(s) for s in saida]


def _bloco_item(n, ent, ap, c):
    import painel_ia
    m = _m()
    pai = painel_ia.ler(ap.get("pai") or "") or {}
    proposta = re.sub(r"\n?STATUS:.*$", "", str(pai.get("resposta") or ""), flags=re.S | re.I).strip()
    revs = "\n".join(f"- {lado}: {v or 'sem resposta'} - {mo}" for lado, (v, mo) in (ent.get("revisores") or {}).items())
    cmds = m._comandos(ap["id"], limite=2000) + ("\n" + m._comandos(pai["id"], limite=1000) if pai.get("id") else "")
    diff, n_arq, n_lin, depois = _diff(ap, contexto=12, limite=8000)
    guarda = json.dumps({"bloqueios": ap.get("bloqueios") or [], "suspeitos": ap.get("suspeitos") or []},
                        ensure_ascii=False)[:1500]
    partes = [f"## ITEM {n} — job {ap['id']} | projeto {ap.get('projeto')} | P{ent['prio']}: {'; '.join(ent['motivos'])}",
              f"Aplicada em {m._quando(ap)} (Brasília) pelo modelo {ap.get('modelo')}"
              + (" | APROVADA PELA PRÓPRIA DONA no Telegram (desfazer só com ela)" if ent.get("dona") else ""),
              "O QUE ERA PRA FAZER (item do backlog):\n" + m._texto_item(ent.get("item")),
              "PROPOSTA DO EXECUTOR (fim):\n" + m._corta(proposta[-2500:], 2500),
              "O QUE ELA DIZ QUE FEZ: " + m._resumo(ap),
              "REVISORES:\n" + (revs or "- (nenhum)") + (f"\nNOTA DO MOTOR: {ent.get('nota')}" if ent.get("nota") else ""),
              "COMANDOS QUE RODARAM (aplicação; depois a proposta):\n" + (cmds.strip() or "(nenhum)"),
              "GUARDA DE COMANDOS: " + guarda,
              f"DIFF ({n_arq} arquivo(s), {n_lin} linhas mudadas; contexto 12 linhas)"
              + (f" — ATENÇÃO, mudaram depois: {', '.join(depois)}" if depois else "") + ":\n" + diff,
              "ERROS NOVOS NOS LOGS DO PROJETO DESDE A APLICAÇÃO:\n" + (_erros_novos(ap) or "(nenhum)")]
    if ent.get("extra"):
        partes.append("TRECHOS QUE VOCÊ PEDIU (PRECISO_VER) — agora DECIDA:\n" + "\n".join(ent["extra"]))
    return "\n\n".join(partes)


_COOKIE_NETSCAPE = re.compile(r"^#?\s*\.?[\w.-]+\.\w+\s+(?:TRUE|FALSE)\s+\S+\s+(?:TRUE|FALSE)\s+\d+\s")


def _limpo(txt):
    """24/10 (achado 16): texto que vai pro Opus/disco sem chave nem linha de cookie, mantendo as linhas e o recuo."""
    co = _co()
    segs = [s for s in (getattr(co, "_SEGREDOS", None) or []) if s]
    saida = []
    for ln in str(txt or "").splitlines():
        if _COOKIE_NETSCAPE.match(ln.lstrip("+- ")):
            saida.append("<linha de cookie tirada>")
            continue
        for s in segs:
            ln = ln.replace(s, "<chave>")
        ln = re.sub(r"(?i)(bearer\s+)[^\s\"',;]+", r"\1<chave>", ln)
        ln = re.sub(r"(?i)(x-api-key[\"']?\s*[:=]\s*[\"']?)[^\s\"',;]+", r"\1<chave>", ln)
        ln = re.sub(r"\b(?:sk|pk|rk)-[A-Za-z0-9_\-]{8,}", "<chave>", ln)
        ln = re.sub(r"(?<![\w/\\.])[A-Za-z0-9_\-+=]{40,}", "<...>", ln)
        saida.append(ln)
    return "\n".join(saida)


def montar_dossie(e, c, ents, titulo="lote"):
    """24/10 (achado 24): cada item tem a sua cota (antes o 4º perdia o fim do DIFF e os ERROS NOVOS em silêncio);
    passa do limite = corta o DIFF do item e escreve [CORTADO: N caracteres]."""
    import painel_ia
    m = _m()
    cab = "\n\n".join([f"# DOSSIÊ DE AUDITORIA — {titulo}", _agora_txt(),
                       "LIÇÕES QUE O AGENTE JÁ SEGUE (pra você saber o que já foi ensinado):\n" + m._licoes(3000)])
    validos = [(ent, painel_ia.ler(ent["job"])) for ent in ents]
    validos = [(ent, ap) for ent, ap in validos if ap]
    maximo = int(c["opus_dossie_max_chars"])
    cota = max(4000, (maximo - len(cab) - 200) // max(1, len(validos)))
    blocos = []
    for n, (ent, ap) in enumerate(validos, 1):
        b = _limpo(_bloco_item(n, ent, ap, c))
        if len(b) > cota:
            i = b.find("\nDIFF (")
            j = b.find("\n\nERROS NOVOS NOS LOGS")
            sobra = len(b) - cota + 40
            if 0 <= i < j and j - i > sobra:
                b = b[:j - sobra] + f"\n[CORTADO: {sobra} caracteres do DIFF]" + b[j:]
            else:
                b = b[:cota - 40] + f"\n[CORTADO: {len(b) - cota + 40} caracteres]"
        blocos.append(b)
    return "\n\n".join([cab] + blocos)[:maximo]


# ─── disparo e colheita ───────────────────────────────────────────────────────────────────────────────────────────
def _disparar(e, c, ents):
    m = _m()
    PASTA.mkdir(parents=True, exist_ok=True)
    lid = f"{datetime.now():%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"  # 2 lotes no mesmo segundo não se misturam
    dossie = PASTA / f"{lid}_dossie.md"
    dossie.write_text(montar_dossie(e, c, ents, f"lote {lid}"), encoding="utf-8")
    pedido = {"id": lid, "modelo": c["opus_modelo"], "base_url": c["opus_base_url"], "system": SISTEMA_JUIZ,
              "dossie": str(dossie), "max_tokens": int(c["opus_max_tokens"]),
              "primeiro_byte_s": float(c["opus_primeiro_byte_s"]), "tempo_max_min": float(c["opus_tempo_max_min"]),
              "jobs": [x["job"] for x in ents], "exigir_modelo": c.get("opus_exigir_modelo", "opus-4-6"),
              "respeitar_botao": True}
    tmp = PASTA / f"{lid}_pedido.json.tmp"
    tmp.write_text(json.dumps(pedido, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(PASTA / f"{lid}_pedido.json")
    py = PYW if PYW.exists() else PYW.with_name("python.exe")
    subprocess.Popen([str(py), str(BASE / "camada_opus.py"), "lote", lid], cwd=str(BASE), creationflags=DESTACADO,
                     close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    lei = (_leitura() or {}).get("leitura") or {}
    e["opus"]["lote"] = {"id": lid, "jobs": pedido["jobs"], "inicio": time.time(), "contas": lei.get("com_credito")}
    e["opus"]["chamadas"] += 1
    e["opus"]["horas"].append(time.time())
    for x in ents:
        x.update(estado="julgando", lote=lid)
    m.log(f"auditoria final: lote {lid} com {len(ents)} aplicação(ões) mandado ao Opus "
          f"({lei.get('com_credito')} contas com crédito)")


def _colher(e, c):
    """Lote terminado (ou cujo processo morreu): distribui os vereditos. Devolve True se colheu."""
    lote = e["opus"].get("lote")
    co = _co()
    if not lote or co is None:
        return False
    m = _m()
    arq = PASTA / f"{lote['id']}.json"
    try:
        res = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        res = None
    if res is None:
        vivo = co.lote_vivo()
        if (vivo and vivo.get("id") == lote["id"]) or time.time() - lote["inicio"] < 90:
            return False  # ainda rodando (ou acabou de ser disparado)
        try:
            texto = (PASTA / f"{lote['id']}.txt").read_text(encoding="utf-8", errors="replace")
        except OSError:
            texto = ""
        res = {"status": "caiu", "vereditos": co.extrair_vereditos(texto), "erro": "o processo morreu sem resultado"}
    status = res.get("status") or "erro"
    e["opus"]["tokens"] += int(res.get("tokens_in") or 0) + int(res.get("tokens_out") or 0)
    e["opus"]["ultimo"] = {"id": lote["id"], "status": status, "fim": datetime.now().strftime("%Y-%m-%d %H:%M"),
                           "segundos": res.get("segundos"), "primeiro_byte_s": res.get("primeiro_byte_s"),
                           "tokens": int(res.get("tokens_in") or 0) + int(res.get("tokens_out") or 0),
                           "decididos": 0, "contas": lote.get("contas")}
    por_job = {}
    for v in res.get("vereditos") or []:
        if isinstance(v, dict) and str(v.get("veredito", "")).upper() in VEREDITOS:
            por_job[str(v.get("job", "")).strip()] = v
    e["opus"]["lote"] = None  # 24/10 (achado 23): zera antes de distribuir; um veredito ruim não trava a camada
    import painel_ia
    for jid in lote["jobs"]:
        ent = e["auditar"].get(jid)
        if not ent:
            continue
        v = por_job.get(jid)
        try:
            if v:
                e["opus"]["ultimo"]["decididos"] += 1
                ver = str(v["veredito"]).upper()
                if ver == "PRECISO_VER" and not ent.get("ver_usado"):
                    ap = painel_ia.ler(jid) or {}
                    man = ap.get("manifesto") or {}
                    permitidos = list(man) + [i.get("backup") for i in man.values() if isinstance(i, dict)]
                    ent.update(estado="pendente", prio=0, ver_usado=True,
                               extra=_ler_trechos(v.get("ver"), permitidos))
                    continue
                if ver == "PRECISO_VER":  # 2ª vez sem decidir: a dona decide
                    v = dict(v, veredito="DONA", por_que=v.get("por_que") or "o auditor não conseguiu decidir")
                ent.update(estado="julgado", veredito=v)
            elif status == "desligado":
                ent["estado"] = "pendente"  # a dona desligou: volta sem gastar tentativa
            else:
                ent["tentativas"] = int(ent.get("tentativas", 0)) + 1
                ent["estado"] = "nao_auditado" if ent["tentativas"] >= int(c["opus_tentativas_max"]) else "pendente"
                if ent["estado"] == "nao_auditado" and int(ent.get("prio", 1)) == 0:  # achado 4: a dona sabe
                    m._avisar(f"Auditoria final: o Opus falhou {ent['tentativas']}x numa melhoria importante em "
                              f"{ent.get('projeto')} ({'; '.join(ent.get('motivos') or [])[:200]}). Um auditor reserva "
                              f"vai olhar; se precisar, confira no painel (aba IA, pedido {jid}).")
        except Exception as ex:  # noqa: BLE001
            m.log(f"{jid}: veredito do Opus não deu pra distribuir ({type(ex).__name__}: {ex})")
            _para_dona(e, ent, v if isinstance(v, dict) else {}, f"veredito ilegível ({type(ex).__name__})")
    if status not in ("terminou", "desligado"):
        lei = (_leitura() or {}).get("leitura") or {}
        e["opus"]["fora_ate"] = time.time() + float(c["opus_fora_min"]) * 60
        e["opus"]["fora_desde_leitura"] = lei.get("em")
    _documentar_lote(lote, res)
    m.log(f"auditoria final: lote {lote['id']} {status} ({e['opus']['ultimo']['decididos']}/{len(lote['jobs'])} "
          f"decididos, {e['opus']['ultimo']['tokens']} tokens)")
    return True


# ─── ação ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def _item_de(ent, ap):
    m = _m()
    item = dict(ent.get("item") or {})
    item.setdefault("titulo", m._resumo(ap)[:200])
    item.setdefault("evidencia", "")
    item.setdefault("arquivos", list(ap.get("manifesto") or {}))
    item.setdefault("impacto", 3)
    item.setdefault("risco", 3)
    item.setdefault("como_conferir", "")
    return item


def _para_dona(e, ent, v, motivo_extra="", quem="Auditoria final (Opus)"):
    """quem (24/10, achado 30) vem por parâmetro: antes ficava em ent['quem'] e a reserva assinava o veredito do Opus.
    enviado=False (achado 1): o bots_conversa reabre o aviso de um job que já tinha sido avisado e marca True."""
    jid = ent["job"]
    v = v if isinstance(v, dict) else {}
    e["auditoria_dona"][jid] = {"veredito": str(v.get("veredito", "DONA")).upper(),
                                "por_que": (str(v.get("por_que") or "") + (f" ({motivo_extra})" if motivo_extra else ""))[:600],
                                "fora_de_arquivo": str(v.get("fora_de_arquivo") or "")[:600],
                                "quem": quem, "enviado": False}
    e["auditoria_dona"] = dict(list(e["auditoria_dona"].items())[-60:])
    e["entregar"].append(jid)
    ent["estado"] = "dona"
    return "mandei pra dona"


def _agir_um(e, c, ent, licoes_lote, avisos):
    import painel_ia
    m = _m()
    v = ent["veredito"]
    ver = str(v.get("veredito", "")).upper()
    ap = painel_ia.ler(ent["job"])
    placar = e["opus"]["placar"].setdefault(ent.get("modelo_exec") or "?", {"mantido": 0, "derrubado": 0})
    if not ap:
        ent["estado"], acao = "feito", "a aplicação sumiu"
    elif ap.get("desfeito_em"):
        ent["estado"], acao = "feito", "já estava desfeita"
    elif ver == "MANTER":
        ent["estado"], acao = "feito", "mantida"
        placar["mantido"] += 1
    elif ver in ("DESFAZER", "REFAZER") and not ap.get("manifesto"):  # achado 31: não tem o que desfazer
        acao = _para_dona(e, ent, v, "não mudou arquivo: só rodou comandos; o que voltar está em fora_de_arquivo")
    elif ver == "DESFAZER":
        try:  # achado 5: confiança "4,5" / "alta" não derruba o item em silêncio
            conf = float(str(v.get("confianca") or 0).replace(",", "."))
        except ValueError:
            conf = 0
        if ent.get("dona"):
            acao = _para_dona(e, ent, v, "a própria dona aprovou essa mudança")
        elif not str(v.get("prova") or "").strip() or conf < 3:
            acao = _para_dona(e, ent, v, "sem prova ou com pouca certeza: não desfiz sozinho")
        elif m._desfazer(ap, f"auditoria final (Opus): {v.get('por_que')}", quem="auditoria final (Opus)"):
            ent["estado"], acao = "feito", "DESFEITA"
            placar["derrubado"] += 1
            e["vigiar"] = [x for x in e["vigiar"] if x.get("job") != ent["job"]]
            avisos.append(f"desfiz uma melhoria em {ap.get('projeto')}: {str(v.get('por_que'))[:160]}")
        else:
            acao = _para_dona(e, ent, v, "não consegui desfazer: o arquivo mudou depois")
    elif ver == "REFAZER":
        item = _item_de(ent, ap)
        n_ref = sum("auditoria Opus" in str(k) for k in item.get("criticas") or [])
        if ent.get("dona") or not c.get("ligado"):
            acao = _para_dona(e, ent, v, "as melhorias estão paradas" if not c.get("ligado") else "a dona aprovou")
        elif n_ref >= int(c["tentativas_max"]) - 1:  # achado 3: teto do desfaz/refaz
            acao = _para_dona(e, ent, v, f"o Opus já mandou refazer {n_ref} vez(es)")
        elif m._desfazer(ap, f"auditoria final (Opus) mandou refazer: {v.get('por_que')}", quem="auditoria final (Opus)"):
            novo = dict(item, tentativa=1, opus=True, projeto=ent["projeto"], ts=time.time(),
                        criticas=(item.get("criticas") or [])
                        + [f"auditoria Opus: {str(v.get('refazer') or v.get('por_que'))[:400]}"])
            # achado 2: sempre no topo do backlog (o e['refazer'] era sobrescrito pela reprovação de outro item)
            bl = m._backlog(c)
            bl.insert(0, novo)
            m._gravar(m.BACKLOG, bl[:int(c["backlog_max"])])
            ent["estado"], acao = "feito", "desfeita e mandada refazer com a crítica"
            placar["derrubado"] += 1
            e["vigiar"] = [x for x in e["vigiar"] if x.get("job") != ent["job"]]
            avisos.append(f"desfiz e mandei refazer uma melhoria em {ap.get('projeto')}: {str(v.get('por_que'))[:160]}")
        else:
            acao = _para_dona(e, ent, v, "não consegui desfazer: o arquivo mudou depois")
    else:  # DONA
        acao = _para_dona(e, ent, v)
    if str(v.get("fora_de_arquivo") or "").strip() and ent["estado"] != "dona" and ap:
        _para_dona(e, ent, v, "mexeu em algo fora de arquivo")
        ent["estado"] = "feito"
    licao = str(v.get("licao") or "").strip()
    if licao and not licoes_lote and licao.lower()[:60] not in m._licoes(20000).lower():
        m._nova_licao(licao, "auditoria Opus")
        licoes_lote.append(licao)
    ent["acao"] = acao
    _documentar_item(e, ent, ap, v, acao)
    return acao


def _agir(e, c):
    """Executa os vereditos (do mais novo pro mais velho: o desfazer anda em pilha). Só sem aplicação em andamento."""
    import painel_ia
    julgados = sorted((x for x in e["auditar"].values() if x["estado"] == "julgado"), key=lambda x: -x["entrou"])
    if not julgados:
        return False
    if [j for j in painel_ia.todos() if j.get("tipo") == "aplicar" and j.get("status") in ("fila", "rodando")] \
            or painel_ia._travas_ocupadas():
        return False
    licoes_lote, avisos = [], []
    for ent in julgados:
        try:
            _agir_um(e, c, ent, licoes_lote, avisos)
        except Exception as ex:  # noqa: BLE001 — um item ruim não trava os outros
            _m().log(f"{ent['job']}: auditoria não conseguiu agir ({type(ex).__name__}: {ex})")
            _para_dona(e, ent, ent.get("veredito") or {}, f"a auditoria não conseguiu agir ({type(ex).__name__})")
    if avisos:
        _m()._avisar("Auditoria final (Opus): " + "; ".join(avisos)[:900]
                     + ". Detalhes em D:\\video-fila\\auditoria_opus\\INDICE.md.")
    return True


def _vencer(e, c):
    agora = time.time()
    for x in e["auditar"].values():
        if x["estado"] != "pendente":
            continue
        idade_h = (agora - x["entrou"]) / 3600
        if (int(x["prio"]) == 2 and idade_h > float(c["opus_validade_h"])) or (int(x["prio"]) == 1 and idade_h > 168):
            x["estado"] = "vencido"
    velhos = [k for k, x in e["auditar"].items() if x["estado"] in ESTADOS_FINAIS and agora - x["entrou"] > 14 * 86400]
    for k in velhos:
        e["auditar"].pop(k, None)


# ─── auditor reserva (Kiro pensando, só avisa a dona) ────────────────────────────────────────────────────────────
def _reserva(e, c):
    """P0 sem Opus há opus_espera_reserva_h (ou que caiu em 2 lotes): um Kiro pensando julga — e só avisa a dona."""
    import painel_ia
    m = _m()
    if not c.get("ligado") or not c.get("opus_camada"):  # 24/10 (achado 7): melhorias paradas = reserva parada
        return False
    if e.get("atual") or [j for j in painel_ia.todos() if j.get("status") in ("fila", "rodando")]:
        return False
    if painel_ia._travas_ocupadas() or m._ram_gb() < float(c["ram_min_gb"]):
        return False
    agora = time.time()
    cand = [x for x in e["auditar"].values() if int(x["prio"]) == 0 and not x.get("reserva_feita")
            and ((x["estado"] == "pendente" and agora - x["entrou"] > float(c["opus_espera_reserva_h"]) * 3600)
                 or x["estado"] == "nao_auditado")]
    if not cand:
        return False
    ent = min(cand, key=lambda x: x["entrou"])
    PASTA.mkdir(parents=True, exist_ok=True)
    dossie = PASTA / f"reserva_{ent['job']}_dossie.md"
    dossie.write_text(SISTEMA_JUIZ + "\n\n" + montar_dossie(e, c, [ent], f"auditoria reserva {ent['job']}"),
                      encoding="utf-8")
    job = m._pedir("pergunta", PEDIDO_AUDITOR_RESERVA.format(dossie=dossie, job=ent["job"]), projeto=ent["projeto"],
                   origem=m.ORIGEM, voltas=c["voltas_leitura"], pensar=bool(c.get("kiro_pensar")))
    ent["reserva_feita"] = True
    e["papeis"][job["id"]] = {"papel": "auditor_reserva", "aplicado": ent["job"], "projeto": ent["projeto"]}
    e["atual"] = job["id"]
    m.log(f"{ent['job']}: P0 sem Opus há horas — auditor reserva (Kiro pensando) -> {job['id']}")
    return True


def terminou_reserva(e, c, atual, papel):
    """O veredito do auditor reserva nunca desfaz: se achar problema, a dona decide; o Opus reaudita quando voltar."""
    co, m = _co(), _m()
    ent = e["auditar"].get(papel["aplicado"])
    vs = co.extrair_vereditos(str(atual.get("resposta") or "")) if co else []
    v = next((x for x in reversed(vs) if str(x.get("job", "")).strip() == papel["aplicado"]), vs[-1] if vs else None)
    if not ent:
        return
    ent["reauditar_opus"] = True
    if ent["estado"] == "nao_auditado":
        ent["estado"] = "pendente"  # o Opus ainda reaudita quando voltar
    if not v:
        m.log(f"{papel['aplicado']}: auditor reserva não respondeu no formato")
        return
    ver = str(v.get("veredito", "")).upper()
    ent["veredito_reserva"] = v
    if ver in ("DESFAZER", "REFAZER", "DONA") or str(v.get("fora_de_arquivo") or "").strip():
        _para_dona(e, ent, v, quem="auditoria reserva (Kiro pensando — o Opus estava fora)")
        ent["estado"] = "pendente"  # continua na fila do Opus
    m._historico(f"- {datetime.now():%Y-%m-%d %H:%M} | {ent['projeto']} | AUDITORIA RESERVA: {ver} - "
                 f"{str(v.get('por_que'))[:160]} | {papel['aplicado']} ({atual['id']})")


# ─── documentação ─────────────────────────────────────────────────────────────────────────────────────────────────
def _documentar_lote(lote, res):
    DOCS.mkdir(parents=True, exist_ok=True)
    try:
        dossie = (PASTA / f"{lote['id']}_dossie.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        dossie = "(sem dossiê)"
    try:
        texto = (PASTA / f"{lote['id']}.txt").read_text(encoding="utf-8", errors="replace")
    except OSError:
        texto = "(sem resposta)"
    linhas = [f"# Auditoria final (Opus) — lote {lote['id']}",
              f"- status: {res.get('status')} | modelo: {res.get('modelo_resposta')} | {res.get('segundos')} s "
              f"(1º byte {res.get('primeiro_byte_s')} s) | tokens: {res.get('tokens_in')} + {res.get('tokens_out')} | "
              f"contas com crédito antes: {lote.get('contas')}" + (f" | erro: {res.get('erro')}" if res.get("erro") else ""),
              "", "## Ações", "(preenchidas abaixo, uma por aplicação)", "", "## Resposta do Opus", "", texto, "",
              "## Dossiê", "", dossie]
    (DOCS / f"{lote['id']}.md").write_text(_limpo("\n".join(linhas)), encoding="utf-8")


def _documentar_item(e, ent, ap, v, acao):
    import painel_ia
    m = _m()
    DOCS.mkdir(parents=True, exist_ok=True)
    ver = str(v.get("veredito", "")).upper()
    linha = (f"- {datetime.now():%Y-%m-%d %H:%M} | {ent['projeto']} | {ent['job']} | P{ent['prio']} | {ver} -> {acao} | "
             f"{str(v.get('por_que') or '')[:200]} | deixou passar: {v.get('quem_deixou_passar') or '?'} | "
             f"confiança {v.get('confianca')} | lote {ent.get('lote')}")
    novo = not INDICE.exists()
    with open(INDICE, "a", encoding="utf-8") as f:
        if novo:
            f.write("# Auditoria final (Opus) — 1 linha por aplicação julgada\n\n")
        f.write(linha + "\n")
    if ent.get("lote"):
        try:
            with open(DOCS / f"{ent['lote']}.md", "a", encoding="utf-8") as f:
                f.write(f"\n- AÇÃO {ent['job']}: {ver} -> {acao}\n")
        except OSError:
            pass
    # "AUDITORIA OPUS" no 3º campo: nunca começar com "revisão" (o pacote de revisão procura essa palavra)
    m._historico(f"- {datetime.now():%Y-%m-%d %H:%M} | {ent['projeto']} | AUDITORIA OPUS: {ver} -> {acao} - "
                 f"{str(v.get('por_que') or '')[:160]} | {ent['job']}")
    if ap:
        try:
            atual = painel_ia.ler(ap["id"]) or ap
            atual["auditoria_opus"] = {"veredito": ver, "acao": acao, "por_que": str(v.get("por_que") or "")[:600],
                                       "lote": ent.get("lote"), "quando": datetime.now().isoformat(timespec="seconds")}
            painel_ia._gravar(atual)
        except Exception:  # noqa: BLE001
            pass


# ─── entrada do motor ─────────────────────────────────────────────────────────────────────────────────────────────
def ciclo(e, c):
    """Chamada em todo passo() do motor (antes do retorno "pedido rodando"). Só lê arquivos e dispara processos."""
    padrao(e)
    _colher(e, c)
    _agir(e, c)
    _vencer(e, c)
    if not [x for x in e["auditar"].values() if x["estado"] == "pendente"]:
        e["opus"]["espera"] = "nada na fila"
        _reserva(e, c)  # 24/10 (achado 4): P0 'nao_auditado' sem outro pendente também chega na reserva
        return
    ok, motivo = disponivel(c, e)
    e["opus"]["espera"] = motivo
    lote = _lote_pronto(e, c) if ok else []
    if lote:
        _disparar(e, c, lote)
    else:
        _reserva(e, c)


def texto_dona(job):
    """Mensagem do Telegram quando a auditoria quer que a dona decida (None = não é caso da auditoria)."""
    import painel_ia
    a = _m()._estado().get("auditoria_dona", {}).get(job.get("id"))
    if not a:
        return None
    proj = painel_ia.PROJETOS.get(job.get("projeto"), (job.get("projeto"),))[0]
    if (painel_ia.ler(job.get("id") or "") or {}).get("desfeito_em"):
        return (f"⚖️ {a.get('quem', 'Auditoria final (Opus)')}: desfiz uma melhoria em {proj}, mas ela tinha mexido "
                f"em algo fora de arquivo, que o desfazer não volta.\n{a['por_que']}\n"
                f"O que precisa de você: {a.get('fora_de_arquivo') or '(veja o motivo acima)'}")
    titulo = {"DESFAZER": "acha que esta melhoria está errada", "REFAZER": "acha que esta melhoria foi mal feita",
              "MANTER": "manteve a melhoria, mas ela mexeu em algo fora de arquivo"}.get(a["veredito"],
                                                                                         "precisa de você")
    return (f"⚖️ {a.get('quem', 'Auditoria final (Opus)')} {titulo} — {proj}\n{a['por_que']}"
            + (f"\nFora de arquivo (o desfazer não volta): {a['fora_de_arquivo']}" if a.get("fora_de_arquivo") else "")
            + "\n➡️ Se quiser voltar como estava, responda esta mensagem com DESFAZER.")


def status_txt(e, c):
    padrao(e)
    co = _co()
    pend = [x for x in e["auditar"].values() if x["estado"] == "pendente"]
    por = {p: sum(1 for x in pend if int(x["prio"]) == p) for p in (0, 1, 2)}
    o = e["opus"]
    ligada = c.get("opus_camada") and co is not None and not co.desligada()
    linha = (f"Auditoria final (Opus): {'LIGADA' if ligada else 'DESLIGADA'} | na fila P0 {por[0]}, P1 {por[1]}, "
             f"P2 {por[2]} | hoje {o['chamadas']} chamada(s), {o['tokens']} tokens")
    if o.get("lote"):
        linha += f" | julgando agora {len(o['lote']['jobs'])}"
    elif o.get("espera"):
        linha += f" | esperando: {o['espera']}"
    if o.get("ultimo"):
        u = o["ultimo"]
        linha += f"\n  último lote {u['fim']}: {u['status']}, {u['decididos']} decidido(s)"
    plac = "; ".join(f"{k}: {v['mantido']} mantidas, {v['derrubado']} derrubadas" for k, v in o["placar"].items())
    if plac:
        linha += f"\n  placar: {plac}"
    return linha
