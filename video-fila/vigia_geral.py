"""vigia_geral.py — o VIGIA ÚNICO dos projetos de vídeo (dono, 17/10/2026: "esse agente tem que gerenciar e acompanhar
todos os projetos de vídeo"; 19/10: "um vigia só"). Roda as checagens daqui (outros projetos) E as do hipercool
(D:\\hipercool-videos\\bin\\vigia_agente.py, carregado pelo caminho; a tarefa HipercoolVigia foi desligada em 19/10).
Cada lado chama o agente com as regras, o cwd e o diário dele; no fim sai UMA mensagem por rodada, só se algo quebrou
ou foi consertado (pelo portão de avisos). O vigia_agente segue sendo usado pelo vigia_telegram (perguntas do dono).

Vigia: recap de anime (turno da noite), Shorts do parceiro (produção/postagem), historias-em-frames e a fila de render
entre projetos (D:\\video-fila). Tarefa agendada `VigiaVideos`, a cada 20 min, sem janela.
  1. checagem BARATA em Python (sem modelo): log parado com processo rodando, erro novo nos logs, vez de render
     presa. Tudo bem = 1 linha em vigia_geral.log, nenhum token.
  2. problema NOVO ou ronda de 12 h -> Claude Code headless com Gemini (26/10, dono: "vigiar com o Gemini, não vai
     consertar, vai apenas avisar e deixar documentado") investiga, escreve em VIGIA_DIARIO.md e avisa. Não edita nada,
     a não ser na categoria de problema em que o gemini_aprendiz.py já o liberou (acertou as propostas).
     Antes (Kiro, consertando) os dois vigias gastaram 37% do Kiro de 18 a 26/10 (D:\\informacoes_omniroute\\gasto_kiro).

    python vigia_geral.py [--forcar | --so-checar]
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — 29/10 (dona): nenhum processo filho (yt-dlp, ssh, ffmpeg) abre janela
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG = BASE / "vigia_geral.log"
ESTADO = BASE / "estado" / "vigia_estado.json"
TRAVA = BASE / "estado" / "vigia_agente.lock"
DIARIO = BASE / "VIGIA_DIARIO.md"
CLAUDE = Path(r"D:\hipercool-videos\tools\claude\claude.exe")
PROXY = Path(r"D:\hipercool-videos\secrets\claude_proxy.json")
RECAPD = Path(r"D:\recapd-ambientes\producao")

# (rótulo, arquivo de log, trecho da linha de comando do processo que escreve nele)
LOGS = [
    ("parceiro-render", None, "anime_auto.py"),       # o log do dia é achado na hora (_parceiro_AAAAMMDD.log)
    ("parceiro-producao", RECAPD / "logs" / "parceiro_producao.log", None),
    ("parceiro-postar", RECAPD / "logs" / "parceiro_postar.log", None),
    ("anime-noturno", RECAPD / "workspace" / "anime_nightshift.log", "anime_night_shift.py"),
    ("anime-supervisor", RECAPD / "logs" / "cron_anime_noturno.log", None),
]
PARADO_MIN = 45
RONDA_H = 12              # 26/10: era 6 (e 4 no hipercool) — ronda sem problema quase sempre dava "OK, nada a fazer"
AGENTE_TIMEOUT_MIN = 40
# 26/10 (dono): vigias só com Gemini (grátis no gateway), nunca Kiro; ordem = mais rápido primeiro (ia_reserva: 11 s x 48 s)
VIGIA_MODELOS = ["antigravity/gemini-3-flash", "agy/gemini-3.8-flash-high"]
VIGIA_MAX_TURNS = 25
REPETIDO_H = 6            # mesmo problema já investigado há menos disto = só log, sem agente nem aviso de novo
# Ferramentas de escrita bloqueadas no claude.exe: o vigia só lê (Bash fica para ler logs/processos)
SEM_ESCRITA = ["--disallowedTools", "Edit", "Write", "NotebookEdit"]
# o claude.exe usa o modelo "haiku" para o título da sessão; sem isto ia pro kr/claude-haiku-4.5 (Kiro)
SEM_KIRO_ENV = {"ANTHROPIC_DEFAULT_HAIKU_MODEL": VIGIA_MODELOS[0], "ANTHROPIC_SMALL_FAST_MODEL": VIGIA_MODELOS[0]}
# O modo (só aviso, ou conserto liberado para a categoria em que o Gemini já acertou) e as lições vêm do
# gemini_aprendiz.py (dono 26/10: "aprendizado pro Gemini com base no que o Kiro passou, pra logo ele resolver também")
ERRO = re.compile(r"Traceback|\bERROR\b|FALHOU|\[X\]|rc=[1-9]", re.I)
# capa IA 403 "Verify your account": a capa normal entra no lugar (o agente julgou cosmético em toda rodada de 19/10 e
# cada rodada virava agente + mensagem repetida). A conta do gateway de imagem precisa ser verificada pelo dono.
RUIDO = re.compile(r"Proxy falhou|edge-tts err|retentando|tentativa \d|capa IA: gateway HTTP 403"
                   # 22/10 (medido: 35 das 63 chamadas do agente em 48 h, quase todas "OK, nada a fazer", gastando o
                   # crédito do Kiro): capa recusada pelo filtro = Short sem capa (defeito visual não trava; a taxa fica
                   # na Saúde do painel); legenda do YouTube com 429/"not a bot" passa sozinha; a pausa do yt-dlp é a
                   # trava automática do ytdlp_vez (o agente não pode mexer em opção/cookie do yt-dlp)
                   r"|capa IA: (reserva também não gerou|todas as tentativas reprovadas)"
                   r"|legenda YT \([\w-]+\) falhou: .*(HTTP Error 429|Too Many Requests|not a bot)"
                   r"|yt-dlp em pausa", re.I)
# com a pausa do yt-dlp ligada (IP barrado) o download falha de propósito: essas linhas não são problema novo
PAUSA_YT = re.compile(r"yt-dlp em pausa|confirm you.re not a bot", re.I)
FALHA_POR_PAUSA = re.compile(r"\[auto\] download falhou|\[fetch\] download( \([^)]*\))? falhou: .*not a bot", re.I)
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
PY_POST = Path(r"D:\veo\venv\Scripts\python.exe")
PARCEIRO_DIARIO = RECAPD / "bin" / "parceiro_diario.py"


def _relançar_producao():
    """Relança a produção do parceiro em background se nenhum python anime_auto.py estiver rodando."""
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                            "ForEach-Object { $_.CommandLine }"],
                           capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace",
                           creationflags=_SEM_JANELA)
        if any("anime_auto.py" in l and "--fonte" in l for l in (r.stdout or "").splitlines()):
            log("produção: anime_auto.py já está rodando, não relança")
            return
    except Exception:  # noqa: BLE001
        return
    log("produção: relançando parceiro_diario.py producao em background")
    try:
        subprocess.Popen([str(PY_POST), "-X", "utf8", str(PARCEIRO_DIARIO), "producao"],
                         cwd=str(RECAPD), creationflags=_SEM_JANELA,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:  # noqa: BLE001
        log(f"relançar falhou: {e}")


def _relançar_postagem():
    """Dono 18/10: nenhum canal fica sem postagem. A postagem pula sozinha se outra estiver subindo."""
    log("postagem: relançando parceiro_diario.py postar em background")
    try:
        with open(RECAPD / "logs" / "parceiro_postar.log", "a", encoding="utf-8") as fh:
            fh.write(f"[{datetime.now():%d/%m/%Y %H:%M:%S}] ===== postar (relançada pelo vigia) =====\n")
            subprocess.Popen([str(PY_POST), "-X", "utf8", str(PARCEIRO_DIARIO), "postar"], cwd=str(RECAPD),
                             env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"),
                             creationflags=_SEM_JANELA, stdout=fh, stderr=subprocess.STDOUT)
    except Exception as e:  # noqa: BLE001
        log(f"relançar postagem falhou: {e}")


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar(e):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")


def _processos():
    ps = ("Get-CimInstance Win32_Process -Filter \"Name like 'python%' or Name like 'ffmpeg%'\" | "
          "ForEach-Object { $_.CommandLine }")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60,
                           creationflags=_SEM_JANELA, encoding="utf-8", errors="replace")
        return (r.stdout or "").splitlines()
    except subprocess.TimeoutExpired:
        log("[!] PowerShell travou (timeout 60s em _processos); retornando lista vazia")
        return []
    except Exception as e:
        log(f"[!] _processos falhou: {type(e).__name__}: {e}")
        return []


def checar(est):
    problemas = []
    procs = _processos()
    offs = est.setdefault("offsets", {})
    hoje = RECAPD / "workspace" / "anime" / f"_parceiro_{datetime.now():%Y%m%d}.log"
    for rotulo, arq, proc in LOGS:
        arq = arq or hoje
        if not arq.exists():
            continue
        if proc and any(proc in p for p in procs):
            # o turno da noite não escreve no log dele enquanto renderiza: vale também a pasta de trabalho mais nova
            # (17/10: 1ª checagem acusou 416 min "parado" com um longo de 400+ trechos andando normal)
            ws = [d for d in (RECAPD / "workspace" / "anime").glob("*/*") if d.is_dir()]
            ultimo = max([arq.stat().st_mtime] + [d.stat().st_mtime for d in ws])
            parado = (time.time() - ultimo) / 60
            if parado > PARADO_MIN:
                problemas.append(f"{rotulo}: {proc} rodando mas {arq.name} sem escrever há {parado:.0f} min (travado?)")
        tam, chave = arq.stat().st_size, str(arq)
        ini = offs.get(chave, tam)
        ini = 0 if tam < ini else ini
        if tam > ini:
            with open(arq, "rb") as f:
                f.seek(ini)
                novo = f.read().decode("utf-8", "replace")
            ruins = [l.strip() for l in novo.splitlines() if ERRO.search(l) and not RUIDO.search(l)]
            if PAUSA_YT.search(novo):
                ruins = [l for l in ruins if not FALHA_POR_PAUSA.search(l)]
            if ruins:
                problemas.append(f"{rotulo} ({arq}): " + " | ".join(r[:160] for r in ruins[-3:]))
        offs[chave] = tam
    try:  # vez de render presa (o fila_render libera morto/vencido; aqui só o que ficou estranho)
        sys.path.insert(0, str(BASE))
        import fila_render
        for p in (BASE / "estado" / "esperando").glob("*.json"):
            d = json.loads(p.read_text(encoding="utf-8"))
            if time.time() - d["desde"] > 3 * 3600:
                problemas.append(f"fila de render: {d['projeto']} ({d['rotulo']}) esperando a vez há "
                                 f"{(time.time() - d['desde']) / 3600:.1f} h")
    except Exception as e:  # noqa: BLE001
        problemas.append(f"fila de render ilegível: {e}")
    est["ultima_checagem"] = time.time()
    # produção parada: se nenhum Short novo nas últimas 5h, alerta e tenta relançar
    try:
        shorts_dir = Path(r"D:\hipercool-materiais\animes recap\shorts")
        if shorts_dir.exists():
            recentes = [d for d in shorts_dir.iterdir() if d.is_dir()
                        and time.time() - d.stat().st_mtime < 5 * 3600]
            if not recentes:
                problemas.append("produção: nenhum Short novo nas últimas 5h — pode estar parada")
                _relançar_producao()
    except Exception as e:  # noqa: BLE001
        pass
    # postagem parada: a tarefa roda a cada 30 min; log sem escrever há 75 min = tarefa parou
    postlog = RECAPD / "logs" / "parceiro_postar.log"
    if postlog.exists() and time.time() - postlog.stat().st_mtime > 75 * 60:
        problemas.append(f"postagem: {postlog.name} sem escrever há {(time.time() - postlog.stat().st_mtime) / 60:.0f} min "
                         "(tarefa ParceiroKaijinre-Postagem parou?)")
        _relançar_postagem()
    # controlador parado >30 min = nada é produzido (dono 19/10: "deve ter um controlador geral")
    try:
        import controle as _ctrl
        import controlador
        ok_ctrl, _ = _ctrl.ligado("controlador", "producao")
        if ok_ctrl:
            est_ctrl = controlador._ler_estado()
            ult = max(filter(None, (est_ctrl.get("ultima_rodada"), est_ctrl.get("inicio_rodada"))), default=None)
            if ult:
                from datetime import datetime as _dt_cls
                delta = (datetime.now() - _dt_cls.fromisoformat(ult)).total_seconds()
                if delta > 30 * 60:
                    problemas.append(f"controlador: última rodada há {delta / 60:.0f} min (parado?)")
    except Exception:  # noqa: BLE001
        pass
    problemas.extend(_recap_longo(procs))
    problemas.extend(_comum_mexido())
    problemas.extend(_modelos_mortos(est))
    # 20/10 ~12h o D: encheu (Errno 28) e a produção do parceiro parou sem ninguém saber
    import shutil
    for disco, minimo_gb in (("D:\\", 8), ("C:\\", 5)):
        try:
            livre = shutil.disk_usage(disco).free / 1e9
            if livre < minimo_gb:
                problemas.append(f"disco {disco[:2]} com só {livre:.1f} GB livres (mínimo {minimo_gb}): a produção "
                                 "para quando encher")
        except OSError:
            pass
    return problemas


def _recap_longo(procs):
    """Recap LONGO nas GPUs do Kaggle (dona 26/10: "tem que manter funcionando sem você no chat"). Lê o status.json que a
    central da VPS hermes-prod (/opt/recap_central/vps_central.py, cron 5 min) publica e confere o alimentador do PC1.
    Conserto sozinho: alimentador morto = religa a tarefa RecapAlimentar. O resto vira problema pro agente, com os
    comandos na mensagem: `ssh hermes-prod "cd /opt/recap_central && venv/bin/python vps_central.py contas"` (estado das
    contas), `... vps_central.py liberar <conta>` (re-testar conta), log em /opt/recap_central/central.log; fila no
    manhwa-drive:colab_recap/fila; código do PC em D:\\recapd-ambientes\\producao\\colab (subir pra VPS com scp)."""
    import urllib.request
    probs = []
    batida = RECAPD / "colab" / "alimentar_estado.json"  # o alimentador regrava a cada volta (~2 min + preparo)
    parado_min = (time.time() - batida.stat().st_mtime) / 60 if batida.exists() else 0
    if not any("cliente.py alimentar" in p for p in procs):
        probs.append("recap longo: alimentador (cliente.py alimentar) não está rodando no PC1 — religando RecapAlimentar")
        subprocess.run(["schtasks", "/Run", "/TN", "RecapAlimentar"], capture_output=True, creationflags=_SEM_JANELA)
    elif parado_min > 40:
        # 26/10: ficou 3 h vivo mas travado (rede sem resposta dentro do yt-dlp) e as 4 GPUs paradas sem pedido
        probs.append(f"recap longo: alimentador travado ({parado_min:.0f} min sem dar a volta) — reiniciado")
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | Where-Object { $_.CommandLine "
                        "-match 'cliente.py alimentar' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; "
                        "Start-Sleep 3; Start-ScheduledTask -TaskName RecapAlimentar"],
                       capture_output=True, creationflags=_SEM_JANELA, timeout=60)
    try:
        pag = (BASE / "estado" / "recap_longo_pagina.txt").read_text(encoding="utf-8").strip()
        with urllib.request.urlopen(f"https://produtos.opus-sem-limites.com.br/{pag}/status.json", timeout=20) as r:
            st = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return probs + [f"recap longo: status da VPS ilegível ({type(e).__name__}: {str(e)[:100]})"]
    try:
        quando = datetime.strptime(f"{datetime.now().year}/{st['atualizado']}", "%Y/%d/%m %H:%M")
        if (datetime.now() - quando).total_seconds() > 20 * 60:
            probs.append(f"recap longo: central da VPS sem atualizar desde {st['atualizado']} (cron recap-central parado?)")
    except (KeyError, ValueError):
        pass
    gpus = st.get("gpus", [])
    sem = [g for g in gpus if not g.get("conta")]
    if gpus and sem:
        probs.append(f"recap longo: {len(sem)} de {len(gpus)} GPUs sem conta ({sem[0].get('status')}); "
                     f"contas verificadas: {st.get('verificadas')} de {st.get('contas')}")
    erros = [p["titulo"][:60] for p in st.get("pedidos", []) if p.get("situacao") == "erro"]
    if erros:
        probs.append(f"recap longo: {len(erros)} pedido(s) com erro na fila: {'; '.join(erros[:3])}")
    return probs


PASTAS_MODELOS = [r"D:\hipercool-videos\bin", r"D:\recapd-ambientes\producao\bin", r"D:\manhwa-react\mr",
                  r"D:\postador-de-videos\bin", r"D:\veo\beta", r"D:\video-fila", r"D:\hipercool-materiais\bin"]
ARQS_MODELOS = [r"D:\postador-de-videos\secrets\claude_proxy.json", r"D:\postador-de-videos\secrets\omniroute.json",
                r"D:\manhwa-react\config.json"]
# 26/10: falsos alarmes que chamavam o agente em toda rodada — "kr/claude-sonnet" é prefixo num startswith (painel_ia) e
# "kr/claude-opus-4.8" é só o padrão do claude_client do postador quando falta ANTHROPIC_MODEL
MODELOS_IGNORAR = {"kr/claude-sonnet", "kr/claude-opus-4.8"}


def _modelos_mortos(est):
    """1x/dia: nome de modelo do gateway escrito no código/config que saiu do catálogo (/v1/models). 16/10 dois saíram
    e o postador passou 4 dias levando 400 em toda chamada sem ninguém saber (achado 20/10)."""
    import re
    import urllib.request
    if time.time() - est.get("modelos_conferidos", 0) < 20 * 3600:
        return []  # 26/10: avisa só na rodada em que conferiu (antes repetia a lista guardada em TODA rodada)
    try:
        c = json.loads(Path(r"D:\postador-de-videos\secrets\claude_proxy.json").read_text(encoding="utf-8"))
        req = urllib.request.Request(c["base_url"].rstrip("/") + "/v1/models",
                                     headers={"Authorization": "Bearer " + c["auth_token"]})
        ids = {m["id"] for m in json.loads(urllib.request.urlopen(req, timeout=60).read())["data"]}
    except Exception:  # noqa: BLE001  (gateway fora: tenta na próxima rodada)
        return []
    usados = {}
    arqs = [Path(a) for a in ARQS_MODELOS] + [f for p in PASTAS_MODELOS for f in Path(p).glob("*.py")
                                               if not f.name.startswith(("_", "test", "fix_", "patch_"))]
    for f in arqs:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in re.findall(r"[\"']((?:kr|kiro|antigravity|agy)/[\w.\-]+)[\"']", t):
            usados.setdefault(m, f.name)
    mortos = [f"modelo {m} (em {arq}) não existe mais no gateway" for m, arq in sorted(usados.items())
              if m not in ids and m not in MODELOS_IGNORAR]
    est["modelos_conferidos"] = time.time()
    est["modelos_mortos"] = mortos
    return mortos


def _comum_mexido():
    """Cópia de módulo COMUM mudada num projeto e não subida: os outros projetos não recebem o conserto (20/10 o
    edge_tts_engine do recapd ficou diferente e ninguém viu)."""
    try:
        import importlib.util
        s = importlib.util.spec_from_file_location("recursos_comum", r"D:\hipercool-materiais\bin\recursos.py")
        rec = importlib.util.module_from_spec(s)
        s.loader.exec_module(rec)
        reg = rec._ler_registro()
    except Exception as e:  # noqa: BLE001
        return [f"código comum: não deu pra conferir ({type(e).__name__})"]
    saida = []
    for nome, info in reg.items():
        fonte = rec.COMUM / nome
        if not fonte.exists():
            continue
        h = rec._hash(fonte)
        for p in info.get("projetos", []):
            c = rec._copia(p, nome)
            if c.exists() and rec._hash(c) != h:
                saida.append(f"código comum: {nome} mudado em {p} sem subir — rode "
                             f"python D:\\hipercool-materiais\\bin\\recursos.py subir {nome} --de {p}")
    return saida


PROMPT = """Você é o VIGIA dos projetos de vídeo deste PC FORA do hipercool, rodando sozinho, sem ninguém olhando.
Outro agente mais forte vai revisar tudo o que você fizer.

MOTIVO DESTA CHAMADA:
{motivo}

PROJETOS (leia o CLAUDE.md/LEIA de cada um que for mexer):
- Recap de anime + Shorts do parceiro: D:\\recapd-ambientes\\producao (bin/anime_auto.py, bin/parceiro_diario.py,
  config/parceiro.json; logs em logs/ e workspace/anime/_parceiro_*.log, workspace/anime_nightshift.log).
  Progresso e regras: D:\\manhwa-react\\MELHORIAS_APLICADAS_E_PENDENTES.md (seções do parceiro e da narração).
- historias-em-frames: D:\\historias-em-frames (PARADO de propósito pelo dono; só olhe, não religue).
- Fila de render entre projetos: D:\\video-fila (fila_render.py, fila.json). Diário: D:\\video-fila\\VIGIA_DIARIO.md.

SEU TRABALHO: investigar o motivo e DOCUMENTAR. Se você pode ou não consertar está no MODO, no fim deste pedido.

REGRAS DURAS:
- NUNCA mexa em D:\\hipercool-videos (tem vigia próprio) nem no D:\\postador-de-videos ou D:\\manhwa-react\\mr (são
  da outra sessão). NUNCA ligue/desligue nada que o dono desligou: config ligado=false, *DESLIGAD*.json, tarefas
  agendadas desabilitadas, historias parado. (17/10: o vigia do hipercool religou uma fila desligada de propósito.)
- Antes de editar QUALQUER arquivo, copie o original para D:\\video-fila\\vigia_backups\\{hora}\\ (mesmo nome).
- NUNCA apague vídeos, pastas de D:\\hipercool-materiais, workspace, caches, roteiros. Nada de limpeza de disco.
- REGRA DO DONO (18/10): nenhum canal fica 1 dia sem postagem. Se a postagem do parceiro estiver parada ou um canal
  sem post hoje tiver Short pronto, AVISE (STATUS: REVISAR) dizendo o canal e que o comando é
  `D:\\veo\\venv\\Scripts\\python.exe bin\\parceiro_diario.py postar` — não rode você mesmo.
- Fora isso, NUNCA mexa em canais, credenciais, horários de postagem, cota, nem publique por outro caminho.
- NUNCA mate pythonw (nem aqui nem no pc2). Só mate um python/ffmpeg se PROVAR que está travado (log parado e sem
  CPU) e diga qual.
- Render pesado é pela fila (D:\\video-fila): não lance render por fora dela.
- Vozes: só a Antonio é proibida (Francisca e Isabella liberadas pelo dono em 16/10; a Francisca é a BASE da voz
  clonada — não é erro); não troque a voz de nada.
- yt-dlp barrado ("Sign in to confirm you're not a bot", HTTP 429): é o YouTube barrando o IP da casa POR VOLUME de
  pedidos e passa sozinho. NÃO rode yt-dlp em sequência pra testar (cada pedido alonga o bloqueio) e NÃO mexa em
  opções/cookies do yt-dlp por causa disso (21/10: um vigia pôs --js-runtimes node, o seguinte tirou, os dois achando
  que era a causa — não era). A pausa automática fica em D:\\video-fila\\ytdlp_pausa.json (ytdlp_vez.pausar/pausado);
  pausa ativa = STATUS: OK (esperando passar).
- Conserto pequeno e cirúrgico. Sem git push, sem instalar pacote.

RASTRO OBRIGATÓRIO: ACRESCENTE ao fim de D:\\video-fila\\VIGIA_DIARIO.md:
## {hora} — <resumo em 1 linha>
- Motivo / O que achei (trecho de log) / Causa provável / CONSERTO PROPOSTO / O que fez (só se liberado; backup)
- Estado: RESOLVIDO | PRECISA REVISÃO | NADA A FAZER
"""


def chamar_agente(motivo, avisar=True, conserta=False):
    """(status, detalhe, log do agente, texto) ou None se outro já está rodando. conserta=False = só aviso (Gemini em
    treinamento, ferramentas de escrita bloqueadas); True = categoria liberada pelo gemini_aprendiz."""
    if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < AGENTE_TIMEOUT_MIN * 60 + 120:
        log("agente já rodando — pulo")
        return None
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    TRAVA.write_text(str(os.getpid()))
    hora = datetime.now().strftime("%Y%m%d_%H%M")
    cfg = json.loads(PROXY.read_text(encoding="utf-8"))
    env = dict(os.environ, ANTHROPIC_BASE_URL=cfg["base_url"], ANTHROPIC_AUTH_TOKEN=cfg["auth_token"],
               PYTHONUTF8="1", PATH=r"D:\hipercool-materiais\bin" + os.pathsep + os.environ.get("PATH", ""),
               **SEM_KIRO_ENV)
    env.pop("ANTHROPIC_API_KEY", None)
    saida = BASE / "logs" / f"vigia_agente_{hora}.log"
    saida.parent.mkdir(exist_ok=True)
    try:  # dono 21/10 ("o vigia aprende"): casos parecidos já vistos vão junto (base_consertos; vazio se nada parecido)
        import base_consertos
        parecidos = base_consertos.bloco_prompt(motivo)
    except Exception:  # noqa: BLE001
        parecidos = ""
    if parecidos:
        log(f"base de consertos: {parecidos.count(chr(10))} caso(s) parecido(s) no prompt")
    import ia_reserva
    import gemini_aprendiz
    texto = ""
    try:
        for modelo in VIGIA_MODELOS:  # 26/10: só Gemini (antes ia_reserva.modelos(cfg["modelo"]) = Kiro primeiro)
            log(f"chamando agente ({modelo}, {'CONSERTO LIBERADO' if conserta else 'só aviso'}): {motivo[:200]}")
            prompt = (PROMPT.format(motivo=motivo + (f"\n\n{parecidos}" if parecidos else ""), hora=hora)
                      + gemini_aprendiz.bloco(motivo, conserta))
            try:
                r = subprocess.run([str(CLAUDE), "-p", prompt, "--model", modelo, "--output-format", "text",
                                    "--max-turns", str(VIGIA_MAX_TURNS), "--dangerously-skip-permissions",
                                    *([] if conserta else SEM_ESCRITA)],
                                   cwd=r"D:\recapd-ambientes\producao", env=env, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=AGENTE_TIMEOUT_MIN * 60,
                                   creationflags=_SEM_JANELA)
                texto = (r.stdout or "") + ("\n[stderr]\n" + r.stderr if r.stderr else "")
            except subprocess.TimeoutExpired as e:
                texto = (e.stdout if isinstance(e.stdout, str) else "") + f"\n[vigia] passou de {AGENTE_TIMEOUT_MIN} min"
                break
            if not ia_reserva.falhou_sem_trabalhar(texto):
                break
            ia_reserva.marcar(modelo)
            log(f"modelo {modelo} recusado pelo gateway ({' '.join(texto.split())[:150]}): fica fora 1 h, vai o próximo")
    finally:
        TRAVA.unlink(missing_ok=True)
    saida.write_text(texto, encoding="utf-8")
    # o modelo às vezes põe a linha em negrito/markdown: procura em qualquer lugar (no hipercool isso virou "sem STATUS")
    m = re.findall(r"STATUS:\**[ \t]*(OK|NADA A FAZER|CONSERTEI|REVISAR)[ \t]*[-—]?[ \t]*(.*)", texto)  # [ \t]: sem pular de linha
    status, detalhe = m[-1] if m else ("REVISAR", "agente não devolveu STATUS (ver log)")
    if status == "CONSERTEI" and not conserta:  # em treinamento não existe conserto: a ferramenta estava bloqueada
        status = "REVISAR"
    log(f"agente terminou: {status} {detalhe[:200]} -> {saida.name}")
    if status != "OK" and avisar:
        _avisar([("outros projetos", status, detalhe, motivo, "D:\\video-fila\\VIGIA_DIARIO.md")])
    return status, detalhe, saida.name, texto


def _escalar(est, lado, motivo, detalhe, texto):
    """26/10 (dono: "Gemini pra coisas menores, Kiro apenas para as correções"): problema real que o Gemini achou
    (REVISAR com conserto proposto) vira pedido de CONSERTO na IA do painel, que usa o Kiro (ia_reserva conserto=True),
    aplica com backup + Desfazer e avisa. No máximo consertos_kiro_por_dia; o conserto vira gabarito do aprendizado.
    Devolve o id do pedido ou None."""
    import gemini_aprendiz
    import ia_reserva
    cg = ia_reserva._conta_gota()
    proposta = gemini_aprendiz._proposta(texto)
    if not cg.get("vigia_chama_conserto", True) or not proposta or re.match(r"(?i)nenhum", proposta):
        return None
    hoje = datetime.now().strftime("%Y-%m-%d")
    feitos = [t for t in est.get("escalados", []) if t.startswith(hoje)]
    if len(feitos) >= int(cg.get("consertos_kiro_por_dia", 6)):
        log(f"conserto pro Kiro: limite do dia ({len(feitos)}) — fica só o aviso")
        return None
    projeto = "hipercool" if lado == "hipercool" else (
        "cortes" if re.search(r"(?i)recap|parceiro|anime", motivo) else "geral")
    try:
        import painel_ia
        job = painel_ia.pedir("consertar", f"Conserte (achado pelo vigia): {detalhe[:600]}", projeto=projeto,
                              contexto=f"MOTIVO DO VIGIA:\n{motivo[:2500]}\n\nDIAGNÓSTICO DO GEMINI (vigia em "
                                       f"treinamento; confira antes de seguir):\n{proposta}",
                              origem="vigia", auto_aplicar=True)
    except Exception as e:  # noqa: BLE001
        log(f"[!] conserto pro Kiro não abriu: {type(e).__name__}: {e}")
        return None
    est["escalados"] = feitos + [f"{hoje} {job['id']}"]
    log(f"conserto pro Kiro aberto no painel: {job['id']} ({projeto})")
    return job["id"]


def _com_caso(detalhe, cid, status, conserta):
    """Aviso do Telegram leva o nº do caso do aprendizado, pro dono dar a nota da proposta."""
    if status == "REVISAR" and not conserta:
        return f"{detalhe} [Gemini em treino, caso #{cid}: responda 'gemini certo {cid}' ou 'gemini errado {cid}']"
    return f"{detalhe} [caso #{cid}]"


def _novos(est, problemas):
    """26/10: só os problemas que NÃO foram investigados nas últimas REPETIDO_H horas (cada um pela categoria, sem
    números). Antes comparava a lista inteira e um alarme fixo misturado com outro novo chamava o agente toda rodada."""
    import gemini_aprendiz
    agora = time.time()
    vistos = {k: t for k, t in est.get("investigados", {}).items() if agora - t < REPETIDO_H * 3600}
    novos = [p for p in problemas if gemini_aprendiz.categoria(p) not in vistos]
    for p in novos:
        vistos[gemini_aprendiz.categoria(p)] = agora
    est["investigados"] = vistos
    return novos


def _avisar(resultados):
    """UMA mensagem por rodada com o que quebrou/consertou (dono 19/10: um vigia só; prioridade dele no Telegram é
    saber se quebrou e se consertou). Tudo OK = nada."""
    ruins = [r for r in resultados if r[1] != "OK"]
    if not ruins:
        return
    try:
        sys.path.append(r"D:\hipercool-videos\bin")  # append: nunca na frente dos módulos daqui
        import notificar
        titulo = "Vigia: " + ", ".join(f"{nome} {status}" for nome, status, *_ in ruins)
        texto = "\n\n".join(f"[{nome}] {status}: {detalhe[:300]}\nMotivo: {motivo[:250]}\nRastro: {rastro}"
                            for nome, status, detalhe, motivo, rastro in ruins)
        nivel = "erro" if any(r[1] != "CONSERTEI" for r in ruins) else "aviso"
        notificar.aviso(titulo, texto, nivel=nivel)
    except Exception as e:  # noqa: BLE001
        log(f"[!] Telegram falhou: {e}")


def _hipercool():
    """vigia_agente.py do hipercool carregado pelo caminho: o vigia ÚNICO (19/10) roda as checagens e o agente dele
    (regras, diário e cwd próprios) — a tarefa HipercoolVigia foi desligada. None se não carregou."""
    import importlib.util
    hb = r"D:\hipercool-videos\bin"
    try:
        spec = importlib.util.spec_from_file_location("vigia_agente_hipercool", Path(hb) / "vigia_agente.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        if sys.path and sys.path[0] == hb:  # ele se põe na frente do path: volta pro fim (módulos daqui primeiro)
            sys.path.pop(0)
            sys.path.append(hb)
        return m
    except Exception as e:  # noqa: BLE001
        log(f"[!] vigia do hipercool não carregou: {e}")
        return None


# dono 20/10 ("um vigia só"): rodavam em tarefas próprias (AnimeRecapMonitor 1 h, VigiaMelhorias 1x/dia 09:07),
# agora o VigiaVideos dispara com o mesmo comando. Os avisos deles já passam pelo portão avisos.py.
# VozClonadaVigia continua tarefa própria: 10 min (este roda a cada 20) e reinicia o treino no Python das vozes.
SUBVIGIAS = [
    ("anime_monitor", 3600, None,
     ["wscript.exe", r"D:\rodar_oculto.vbs", r"D:\recapd-ambientes\producao\cron_anime_monitor.bat"]),
    ("vigia_melhorias", 24 * 3600, 9,
     [r"D:\manhwa-react\.venv\Scripts\pythonw.exe", r"D:\postador-de-videos\bin\vigia_melhorias.py"]),
    # comentário (pergunta da descrição) nos Shorts do parceiro/anime já abertos, 3 por rodada (21/10)
    # Studio pelo navegador (21/10): bloqueados (avisos_studio, 4 canais em rodízio), comentários/inscritos dos canais
    # sem token (sem_token) e comentário nos Shorts (extras_ledger) — UMA DEPOIS DA OUTRA: rodando juntas disputavam a
    # trava do Chrome com a postagem, estouravam o prazo e (morto o dono) a trava ficou presa 09:24-10:54
    # 04/11: o extras_ledger (A/B das capas + comentário fixado) era o ÚLTIMO da fila e o avisos_studio (até 30 min por
    # canal no Studio) não deixava ele rodar — 01:06→09:31 sem acabamento nenhum. Agora ele vai PRIMEIRO.
    ("studio", 3600, 8,
     ["cmd.exe", "/c",
      r"D:\manhwa-react\.venv\Scripts\python.exe D:\postador-de-videos\bin\extras_ledger.py >> "
      r"D:\postador-de-videos\logs\extras_ledger.log 2>&1 & "
      r"D:\manhwa-react\.venv\Scripts\python.exe D:\postador-de-videos\bin\sem_token.py >> "
      r"D:\postador-de-videos\logs\sem_token.log 2>&1 & "
      r"D:\manhwa-react\.venv\Scripts\python.exe D:\postador-de-videos\bin\avisos_studio.py >> "
      r"D:\postador-de-videos\logs\avisos_studio.log 2>&1"]),
    # aprendizado com os vídeos dos parceiros (dono 20/10): 1 vídeo já baixado pelo Cortes por vez, nunca baixa de novo
    ("aprendizado", 1800, None,
     ["cmd.exe", "/c", r"D:\hipercool-videos\venv\Scripts\python.exe D:\video-fila\aprendizado.py rodada >> "
      r"D:\video-fila\logs\aprendizado.log 2>&1"]),
    # P04 (22/10): login de cada canal pelo navegador conferido 1x por dia ANTES do pico (04-08 h; fora da janela ou
    # já feito hoje o script sai na hora); problema = aviso importante pro dono logar de novo
    ("checar_canais", 3600, 4,
     ["cmd.exe", "/c", r"D:\manhwa-react\.venv\Scripts\python.exe D:\postador-de-videos\bin\checar_canais_diario.py >> "
      r"D:\postador-de-videos\logs\checar_canais_saida.log 2>&1"]),
    # 22/10 (dono: "limpezas periódicas pra nunca parar por falta de espaço; na dúvida, Drive"): faxina determinística
    # (SEM agente: o Kiro já apagou coisa sem conferir o Drive). Drive = confere tamanho+md5 NO DRIVE antes de apagar.
    # 22/10 (dono: "detectar quando estamos fazendo teste e manter os dois rodando; pausar só se for dar erro"):
    # guarda viva o tempo todo — cada execução dura 39 min e a trava impede duas ao mesmo tempo
    ("guarda_testes", 20 * 60, None,
     ["cmd.exe", "/c", r"D:\veo\venv\Scripts\python.exe D:\video-fila\guarda_testes.py --rodar 39 >> "
      r"D:\video-fila\logs\guarda_testes_saida.log 2>&1"]),
    # 22/10 (dono: "pelo Telegram eu falando pra corrigir; todos os bots respondem sobre seus temas"): atendente
    # dos 6 bots temáticos -> IA do painel (pergunta só lê; conserto propõe e só aplica com o "aplicar" do dono)
    ("bots_conversa", 20 * 60, None,
     ["cmd.exe", "/c", r"D:\veo\venv\Scripts\python.exe D:\video-fila\bots_conversa.py --rodar 39 >> "
      r"D:\video-fila\logs\bots_conversa_saida.log 2>&1"]),
    # 22/10 (dono: "abrir o YouTube e mostrar o vídeo quando sair e fechar sozinho"): alimenta os TELÕES (notebooks
    # .125 e X200MA) com cada vídeo que entra no ar; quem toca é o ~/vitrine/player.py de cada um
    ("vitrine", 20 * 60, None,
     ["cmd.exe", "/c", r"D:\veo\venv\Scripts\python.exe D:\video-fila\vitrine.py --rodar 39 >> "
      r"D:\video-fila\logs\vitrine_saida.log 2>&1"]),
    # 23/10 (dona: "o login do TikTok você pode fazer entre uma ação e outra do notebook estando livre"): 1 conta por
    # rodada, só com notebook livre; pediu código do e-mail = janela fica na tela + aviso no Telegram (a dona digita)
    ("tiktok_notebooks", 20 * 60, 7,
     ["cmd.exe", "/c", r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe "
      r"D:\postador-de-videos\bin\netbooks\tiktok_notebooks.py >> D:\postador-de-videos\logs\tiktok_notebooks.log 2>&1"]),
    # 23/10 (dona: "testando nos vídeos reais devagar e põe o vigia pra ir avaliando"): teste gradual de formatos e
    # vozes (recapd bin\anime_testes.py) — reconfere o áudio que ficou sem conferir, relatório, aviso de promovido/pausado
    ("avaliar_testes_voz", 3 * 3600, None,
     ["cmd.exe", "/c", r"D:\recapd-ambientes\producao\venv\Scripts\python.exe D:\video-fila\avaliar_testes_voz.py >> "
      r"D:\video-fila\logs\avaliar_testes_voz_saida.log 2>&1"]),
    # 23/10 (dona: "fica procurando melhorias e correções e faz; só as críticas me pergunta, pelo Telegram"): motor das
    # melhorias contínuas, vivo o tempo todo como o bots_conversa (liga/para pelo Telegram: "melhorias ligar/parar")
    ("melhoria_continua", 20 * 60, None,
     ["cmd.exe", "/c", r"D:\veo\venv\Scripts\python.exe D:\video-fila\melhoria_continua.py --rodar 39 >> "
      r"D:\video-fila\logs\melhoria_continua_saida.log 2>&1"]),
    ("faxina", 6 * 3600, None,
     ["cmd.exe", "/c", r"D:\veo\venv\Scripts\python.exe D:\video-fila\faxina.py >> "
      r"D:\video-fila\logs\faxina.log 2>&1"]),
    # 23/10 (dona): resumo do dia dos notebooks no Telegram (Chrome aberto, o que ficou no PC1, likes, vigia, logins)
    # 23/10 (dona): faxina diária do disco — só cache/temporário, nunca perfil nem login (faxina_disco.py)
    ("faxina_disco", 24 * 3600, 4,
     ["cmd.exe", "/c", r"D:\veo\venv\Scripts\python.exe D:\video-fila\faxina_disco.py >> "
      r"D:\video-fila\logs\faxina_disco_saida.log 2>&1"]),
    ("resumo_notebooks", 24 * 3600, 21,
     ["cmd.exe", "/c", r"D:\veo\venv\Scripts\python.exe D:\video-fila\resumo_notebooks.py >> "
      r"D:\video-fila\logs\resumo_notebooks_saida.log 2>&1"]),
]


GUARDIAO_GB = 10  # D: abaixo disto = roda as limpezas seguras (máx. 1x/h)
GUARDIAO_CRITICO_GB = 5  # abaixo disto o aviso do guardião vira problema (agente + Telegram)


def _guardiao_disco(est):
    """Guardião do disco (21/10). 20/10 o D: chegou a 520 MB (parceiro parado) e uma sessão improvisou limpeza que
    apagou painéis e o venv. Aqui só LISTA BRANCA de rotinas que já existem e conferem antes de apagar:
    backup_drive (rclone moveto confere tamanho+md5 no Drive antes de tirar do PC; leva só o já postado), cache do
    Chrome e trechos do aprendizado > 7 dias (arquivos nossos). Nunca junção, venv, panels, fila de postagem."""
    import shutil
    import subprocess
    livre = shutil.disk_usage("D:\\").free / 1e9
    if livre >= GUARDIAO_GB or time.time() - est.get("guardiao_ultimo", 0) < 3600:
        return None
    est["guardiao_ultimo"] = time.time()
    feito = []
    corte = time.time() - 7 * 86400
    for f in (BASE / "aprendizado" / "trechos").glob("*"):
        try:
            if f.is_file() and f.stat().st_mtime < corte:
                f.unlink()
                feito.append(f.name)
        except OSError:
            pass
    for cmd in (["wscript.exe", r"D:\rodar_oculto.vbs", r"D:\manhwa-react\scripts\backup_drive.bat"],
                [r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe",
                 r"D:\video-fila\limpar_cache_chrome.py"]):
        try:
            subprocess.Popen(cmd, creationflags=0x08000000 | 0x01000000, close_fds=True)
        except OSError:
            try:
                subprocess.Popen(cmd, creationflags=0x08000000, close_fds=True)
            except OSError as e:
                log(f"guardião: não disparou {cmd[-1]} ({e})")
    msg = (f"guardião do disco: D: com {livre:.1f} GB — disparei backup_drive + cache do Chrome"
           + (f", apaguei {len(feito)} trecho(s) velho(s) do aprendizado" if feito else ""))
    log(msg)
    return msg


def _studio_rodando():
    """04/11: o Python do vigia (Python313) NÃO tem psutil — a 1ª versão falhava calada e às 10:15 entrou outra fila em
    paralelo. Lista de processos pelo PowerShell (oculto)."""
    import subprocess
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
                            "ForEach-Object { $_.CommandLine }"],
                           capture_output=True, text=True, timeout=60, creationflags=0x08000000)
        return any(s in r.stdout for s in ("avisos_studio.py", "sem_token.py", "extras_ledger.py"))
    except Exception:  # noqa: BLE001
        return True  # na dúvida não dispara outra fila (a próxima volta tenta de novo)


def _subvigias(est):
    import subprocess
    feitos = est.setdefault("subvigias", {})
    agora = time.time()
    for nome, intervalo, hora_min, cmd in SUBVIGIAS:
        if agora - feitos.get(nome, 0) < intervalo - 300 or (hora_min is not None and datetime.now().hour < hora_min):
            continue
        if nome == "studio" and _studio_rodando():
            # 04/11: a fila das 08:15 ainda rodava às 09:16 e outra entrou em paralelo (disputando o Chrome do Studio)
            log("subvigia studio: a fila anterior ainda está rodando — não disparo outra")
            continue
        for flags in (0x08000000 | 0x01000000, 0x08000000):  # sem janela + fora do job da tarefa (senão morre junto)
            try:
                subprocess.Popen(cmd, creationflags=flags, close_fds=True)
                feitos[nome] = agora
                log(f"subvigia {nome}: disparado")
                break
            except OSError as e:
                erro = e
        else:
            log(f"subvigia {nome}: não disparou ({erro})")


def _consertar_problemas_do_painel():
    """Dono 24/10: 'essas tarefas já devem se consertar só pelo vigia; só deve aparecer as que não consertar'. Aperta
    o 'corrigir todos com a IA' do painel :8790: 1 conserto por problema (backup + Desfazer), e o próprio painel pula
    problema com pedido em andamento ou de menos de 6 h — não repete à toa nem gasta crédito em dobro."""
    import urllib.request
    try:
        req = urllib.request.Request("http://127.0.0.1:8790/api/ia_corrigir_todos", data=b'{"ensaio": false}', method="POST",
                                     headers={"Content-Type": "application/json", "X-Painel": "1"})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode("utf-8"))
        if d.get("criados"):
            log("consertos pedidos pelo vigia: " + " | ".join(c["titulo"] for c in d["criados"]))
    except Exception as e:  # noqa: BLE001
        log(f"[!] pedir consertos ao painel: {type(e).__name__}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forcar", action="store_true")
    ap.add_argument("--so-checar", action="store_true")
    a = ap.parse_args()
    if not DIARIO.exists():
        DIARIO.write_text("# Diário do vigia geral\n\nIntervenções do vigia_geral.py (Sonnet do Kiro pelo proxy). "
                          "Revisar o que estiver PRECISA REVISÃO.\n", encoding="utf-8")
    est = _estado()
    problemas = checar(est)
    try:  # 24/10 (dono): o vigia confere se a troca de PC feita no kanban do painel funcionou mesmo
        import transferencias
        problemas += transferencias.conferir()
    except Exception as e:  # noqa: BLE001
        log(f"[!] conferir trocas de PC: {type(e).__name__}: {e}")
    if not a.so_checar:
        # 26/10 (dono: vigia não conserta, só avisa): parou de apertar o "corrigir todos com a IA" do painel
        # (_consertar_problemas_do_painel). O botão no painel continua para o dono usar à mão.
        _subvigias(est)
        g = _guardiao_disco(est)
        # 22/10: o guardião já age sozinho a partir de 10 GB; virar "problema" chamava o agente (crédito do Kiro) pra
        # algo resolvido. Só vira problema com o disco em perigo de verdade.
        import shutil as _sh
        if g and _sh.disk_usage("D:\\").free / 1e9 < GUARDIAO_CRITICO_GB:
            problemas.append(g)
    ronda = time.time() - est.get("ultima_ronda", 0) > RONDA_H * 3600
    _gravar(est)
    log("outros projetos: " + ("ok" if not problemas else "PROBLEMAS: " + " || ".join(problemas)))
    va = _hipercool()
    prob_h, ronda_h = [], False
    if va:
        est_h = va._estado()
        prob_h = va.checar(est_h)
        ronda_h = time.time() - est_h.get("ultima_ronda", 0) > RONDA_H * 3600  # 26/10: 12 h (o dele diz 4)
        try:
            va._gravar_estado(est_h)
        except Exception as e:  # noqa: BLE001
            log(f"[!] hipercool: erro ao gravar estado ({type(e).__name__}): {e}")
        log(f"hipercool: " + ("ok" if not prob_h else "PROBLEMAS: " + " || ".join(prob_h)))
    if a.so_checar:
        return
    import gemini_aprendiz
    try:  # aprendizado do Gemini: o que apareceu (pra saber se voltou), notas que já dá pra dar, lições 1x/dia
        gemini_aprendiz.ver_problemas(problemas + prob_h)
        gemini_aprendiz.avaliar()
        gemini_aprendiz.destilar()
    except Exception as e:  # noqa: BLE001  (o aprendizado nunca derruba o vigia)
        log(f"[!] gemini_aprendiz: {type(e).__name__}: {e}")
    resultados = []
    if problemas and not a.forcar:
        n = len(problemas)
        problemas = _novos(est, problemas)
        if len(problemas) < n:
            log(f"outros projetos: {n - len(problemas)} problema(s) já investigado(s) há menos de {REPETIDO_H} h — fora do agente")
    _gravar(est)  # o _novos grava no est; sem isto o _estado() abaixo perderia
    if problemas or ronda or a.forcar:
        motivo = ("\n".join(f"- {p}" for p in problemas) if problemas else
                  "- Ronda de rotina: confira se a produção do parceiro e o turno da noite do anime estão andando de "
                  "verdade e só documente o que achar.")
        conserta = gemini_aprendiz.pode_consertar(motivo)
        r = chamar_agente(motivo, avisar=False, conserta=conserta)
        jid = None
        if r:
            cid = gemini_aprendiz.registrar("outros projetos", motivo, r[0], r[3], conserta)
            est = _estado()
            if r[0] == "REVISAR" and not conserta:
                jid = _escalar(est, "outros projetos", motivo, r[1], r[3])
                _gravar(est)
            resultados.append(("outros projetos", r[0], _com_caso(r[1], cid, r[0], conserta)
                               + (f" -> conserto com o Kiro aberto no painel ({jid})" if jid else ""), motivo,
                               "D:\\video-fila\\VIGIA_DIARIO.md"))
        est = _estado()
        est["ultima_ronda"] = time.time()
        _gravar(est)
    if va and prob_h and not a.forcar:
        est_h = va._estado()
        n = len(prob_h)
        prob_h = _novos(est_h, prob_h)
        if len(prob_h) < n:
            log(f"hipercool: {n - len(prob_h)} problema(s) já investigado(s) há menos de {REPETIDO_H} h — fora do agente")
        va._gravar_estado(est_h)
    if va and (prob_h or ronda_h or a.forcar):
        motivo = ("\n".join(f"- {p}" for p in prob_h) if prob_h else
                  "- Ronda de rotina (nenhum erro achado pela checagem automática): confira se a fila está "
                  "andando de verdade (capítulo novo saindo, nada parado há horas) e só documente o que achar.")
        conserta = gemini_aprendiz.pode_consertar(motivo)
        base = va.PROMPT if conserta else va.PROMPT.replace("STATUS: CONSERTEI - <o que, em 1 linha>\n", "")
        # o PROMPT dele passa por .format(motivo, hora): chaves das lições precisam ir dobradas
        va.PROMPT = base + gemini_aprendiz.bloco(motivo, conserta).replace("{", "{{").replace("}", "}}")
        r = va.chamar_agente(motivo, avisar=False, max_turns=VIGIA_MAX_TURNS, modelos=VIGIA_MODELOS,
                             extra_args=[] if conserta else SEM_ESCRITA)
        if r:
            st = "REVISAR" if r[0] == "CONSERTEI" and not conserta else r[0]
            cid = gemini_aprendiz.registrar("hipercool", motivo, st, r[2], conserta)
            jid = None
            if st == "REVISAR" and not conserta:
                e_g = _estado()  # o limite diário de consertos é um só (estado do vigia geral)
                jid = _escalar(e_g, "hipercool", motivo, r[1], r[2])
                _gravar(e_g)
            resultados.append(("hipercool", st, _com_caso(r[1], cid, st, conserta)
                               + (f" -> conserto com o Kiro aberto no painel ({jid})" if jid else ""), motivo,
                               "D:\\hipercool-videos\\docs\\VIGIA_DIARIO.md"))
        est_h = va._estado()
        est_h["ultima_ronda"] = time.time()
        va._gravar_estado(est_h)
    _avisar(resultados)


if __name__ == "__main__":
    main()
