#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""politica.py — regras de postagem compartilhadas por TODOS os postadores.

Fonte única de verdade para:
  - canais bloqueados (suspensos / token morto / desativados) -> config/canais_status.json
  - limites de volume e espaçamento                           -> config/politica.json
  - aprovação humana dos vídeos                               -> config/aprovacoes.json
  - registro de uploads (quantos por canal/dia)               -> logs/uploads_ledger.jsonl
  - parada geral quando o YouTube suspende um canal           -> config/PARADO.json
  - canais reservados a um projeto (fora da rotação)          -> config/canais_reservados.json

O youtube_poster.py consulta este módulo antes de CADA upload, então qualquer
script que chame o poster (postar_tudo_hoje, postar_pos_final, agendar_vo3,
scripts manuais...) fica sujeito às mesmas regras.

Uso (linha de comando):
  python bin/politica.py              # status: uploads de hoje, bloqueios, parada
  python bin/politica.py --retomar    # remove a parada geral (depois de revisar o motivo)
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
CONFIG_DIR = ROOT / "config"
POLITICA_FILE = CONFIG_DIR / "politica.json"
STATUS_FILE = CONFIG_DIR / "canais_status.json"
APROV_FILE = CONFIG_DIR / "aprovacoes.json"
PARADO_FILE = CONFIG_DIR / "PARADO.json"
RESERVA_FILE = CONFIG_DIR / "canais_reservados.json"
CADASTRO_FILE = CONFIG_DIR / "canais.json"  # cadastro único (bin/canais.py): dono, alimentadores, max_dia, fuso
PROJETO_ANTIGO = {"recapd": "parceiro"}    # canais_reservados chamava o parceiro pelo nome da pasta
MIN_AGENDA_MIN = 25  # dono 21/10: nem emergência abre na hora; a verificação de direitos leva ~10 min DEPOIS do upload (medido) — com 25 o bloqueio vem antes de abrir (não vira strike)
ESPERA_TRAVA_S = 2400  # youtube_web_poster.Trava espera até 40 min (fila de senhas 02/11) pelo Chrome livre
LIBERA_RESERVA = "23:00"  # hora daqui: a vaga de UPLOAD guardada pro dono e não usada no dia passa pro alimentador
REDE_FILE = CONFIG_DIR / "rede_canais.json"
PROJETO_REDE = "manhwa-react"  # dono dos canais ativos da rede (mr/rede.py agenda neles)
LEDGER_FILE = ROOT / "logs" / "uploads_ledger.jsonl"
POSTER = BIN / "youtube_poster.py"
POSTER_WEB = BIN / "youtube_web_poster.py"  # mesmo CLI, sobe pelo YouTube Studio no Chrome (sem Data API)
NAVEGADOR_FILE = CONFIG_DIR / "youtube_navegador.json"
CREDS_FILE = Path(os.environ.get(
    "YT_CREDS_FILE", r"D:\credenciais-canais\youtube_canais.json"))

PADRAO = {
    "max_uploads_por_canal_dia": 3,
    "max_uploads_total_dia": 12,
    "intervalo_min_horas_mesmo_canal": 2,
    "exigir_aprovacao_humana": True,
    "parar_tudo_ao_detectar_suspensao": True,
}

LISTAS_BLOQUEIO = ("suspensos", "token_morto", "desativados")


# ─────────────────────────── utilidades ────────────────────────────────────
def norm(nome):
    """Normaliza nome de canal: sem espaços nas pontas/duplicados, sem caixa.
    (Os nomes no youtube_canais.json têm espaços sobrando, ex. 'fake News ia '.)"""
    return " ".join(str(nome or "").split()).casefold()


def ler_json(path, default):
    # 03/11: no Windows quem lê no instante do os.replace do gravar_json leva "Permission denied" (13) — o arquivo
    # está bom, é só a troca atômica. Antes caía no padrão (rampa sem degrau extra naquela leitura). 3 tentativas.
    import time as _t
    for tentativa in range(3):
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError:
            return default
        except PermissionError as e:
            if tentativa < 2:
                _t.sleep(0.3)
                continue
            print(f"  ! politica: {Path(path).name} ilegível ({e}) — usando padrão", file=sys.stderr)
            return default
        except ValueError as e:
            # 12/11 (auditoria): JSON quebrado = quase sempre arquivo pego NO MEIO de uma gravação não atômica. Devolver
            # o padrão ({}) fazia o próximo gravador salvar {} por cima — apagava TODAS as contas (incidente 28/10,
            # maquina_remota.py:995). Agora relê; se continuar quebrado e o arquivo tiver conteúdo, ERRO (quem grava
            # não pode seguir com {}), em vez de padrão silencioso.
            if tentativa < 2:
                _t.sleep(0.5)
                continue
            try:
                tam = Path(path).stat().st_size
            except OSError:
                tam = 0
            if tam > 2 and default in ({}, []):
                raise RuntimeError(f"politica: {Path(path).name} com JSON quebrado ({e}) — não devolvo vazio "
                                   "(gravar por cima apagaria tudo)") from e
            print(f"  ! politica: {Path(path).name} ilegível ({e}) — usando padrão", file=sys.stderr)
            return default
        except Exception as e:
            print(f"  ! politica: {Path(path).name} ilegível ({e}) — usando padrão", file=sys.stderr)
            return default
    return default


def gravar_json(path, obj, indent=2):
    """Grava JSON de forma atômica (tmp + replace) — nunca deixa arquivo pela metade."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # 01/11: tmp por processo/thread — com um ".tmp" só, dois gravando juntos (login em lote + Veo + capas no
    # notebooks_reservados.json) trocavam o tmp um do outro e o Windows dava "Acesso negado" no replace
    import threading
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=indent), encoding="utf-8")
    for i in range(20):  # leitor segurando o destino por um instante (Windows não troca arquivo aberto)
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i == 19:
                tmp.unlink(missing_ok=True)
                raise
            __import__("time").sleep(0.1 + 0.05 * i)


def agora():
    return datetime.now().astimezone()


# Piso de seguranca que o json NAO consegue afrouxar (dono, 16/10; item AB-02 de D:\veo\docs\PLANO_MELHORIAS_VEO.md):
# em 14/10 o json foi a 10/50/0 h e em 16/10 o Veo subiu 8 por canal ate o uploadLimitExceeded. Pode apertar, nunca
# afrouxar: max_* acima do piso (ou null/0 = sem teto) vira o piso; intervalo abaixo vira o piso.
#
# 16/10 (noite), ordem do dono: "o limite de upload deve ser por canal e nunca coletivo".
# max_uploads_total_dia saiu do piso (None = sem teto coletivo). O que segura o
# uploadLimitExceeded e o limite POR CANAL mais a 1 h entre videos do mesmo canal: esse erro e
# da CONTA do YouTube, nao de uma cota compartilhada. O teto coletivo era da epoca em que tudo
# subia pela API e os canais dividiam a mesma cota de projeto; agora a API esta proibida
# (proibido_postar_por_api) e cada canal entra pelo proprio perfil de navegador.
# Em 16/10 o teto de 20 travou o dia: Veo e ManhwaReact usaram 16 vagas ate as 14 h e o canal
# novo do hipercool nao postou o quarto video mesmo tendo vaga propria.
PISO = {"max_uploads_por_canal_dia": 4, "max_uploads_total_dia": None, "intervalo_min_horas_mesmo_canal": 1}


def politica():
    cfg = dict(PADRAO)
    cfg.update(ler_json(POLITICA_FILE, {}))
    for k in ("max_uploads_por_canal_dia", "max_uploads_total_dia"):
        if PISO[k] is None:          # sem piso: o json manda (e pode nem ter teto)
            continue
        if not cfg.get(k) or cfg[k] > PISO[k]:
            cfg[k] = PISO[k]
    if (cfg.get("intervalo_min_horas_mesmo_canal") or 0) < PISO["intervalo_min_horas_mesmo_canal"]:
        cfg["intervalo_min_horas_mesmo_canal"] = PISO["intervalo_min_horas_mesmo_canal"]
    return cfg


# ─────────────────────────── canais ────────────────────────────────────────
def carregar_creds():
    return json.loads(CREDS_FILE.read_text(encoding="utf-8"))


def token_hash(canal):
    """Impressão digital da credencial. Se o token for renovado (relogin), o hash
    muda e o bloqueio por 'token_morto' deixa de valer sozinho."""
    raw = f"{canal.get('clientId', '')}|{canal.get('refresh_token', '')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _status():
    st = ler_json(STATUS_FILE, {})
    for k in LISTAS_BLOQUEIO:
        st.setdefault(k, [])
    return st


def _entrada_bate(entrada, canal):
    if isinstance(entrada, str):
        entrada = {"nome": entrada}
    if entrada.get("id"):
        if entrada["id"] != canal.get("id"):
            return False
    elif norm(entrada.get("nome")) != norm(canal.get("nome")):
        return False
    th = entrada.get("token_hash")
    return not th or th == token_hash(canal)


def motivo_bloqueio(canal, status=None):
    """None se o canal pode postar; senão 'suspensos' / 'token_morto' / 'desativados' / 'pausados'."""
    st = status or _status()
    for lista in LISTAS_BLOQUEIO:
        if any(_entrada_bate(e, canal) for e in st[lista]):
            return lista
    rc = rede_do_cred(canal.get("id"))
    if rc and rc.get("status") == "suspenso":
        return "suspensos"
    if rc and rc.get("status") == "pausado":
        return "pausados"
    return None


# ─────────────────────────── rede de canais (config/rede_canais.json) ───────
_REDE_CACHE = {}


def rede():
    """Mapa da rede: {'padrao': {...}, 'canais': [...], 'a_verificar': {...}}.
    11/11: o painel chamava isto ~130 mil vezes por montagem (rede_do_cred por registro × canal) e cada chamada lia e
    interpretava o JSON do disco: 144 s de CPU a cada 2 min, travando o painel. Agora relê só quando o arquivo muda
    (data de modificação + tamanho); devolve cópia para ninguém alterar o guardado sem querer."""
    import copy
    return copy.deepcopy(_rede_leitura())


def _rede_leitura():
    """Mapa da rede guardado, SEM cópia: só para leitura interna (rede_do_cred roda ~130 mil vezes no painel).
    Relê o arquivo quando a data de modificação ou o tamanho mudam."""
    try:
        st = Path(REDE_FILE).stat()
        marca = (st.st_mtime_ns, st.st_size)
    except OSError:
        return ler_json(REDE_FILE, {"canais": []})
    if _REDE_CACHE.get("marca") != marca:
        _REDE_CACHE["dados"] = ler_json(REDE_FILE, {"canais": []})
        _REDE_CACHE["marca"] = marca
    return _REDE_CACHE["dados"]


def rede_do_cred(cred_id, mapa=None):
    """Entrada da rede (canal real) que usa esta credencial, ou None (cópia rasa: quem chama pode mexer nela)."""
    if not cred_id:
        return None
    for c in (mapa or _rede_leitura()).get("canais", []):
        if cred_id in (c.get("creds") or []):
            return dict(c) if mapa is None else c
    return None


def creds_mesmo_canal(cred_id, mapa=None):
    """Todas as credenciais do mesmo canal real (aliases). Ex.: ManhwaReact = i5r + manhwareact_ia."""
    rc = rede_do_cred(cred_id, mapa)
    return set(rc["creds"]) if rc else {cred_id}


def marcar_canal(canal, lista, motivo):
    """Adiciona o canal a uma lista de bloqueio (idempotente)."""
    st = _status()
    if any(_entrada_bate(e, canal) for e in st[lista]):
        return
    entrada = {"nome": canal.get("nome", "").strip(), "id": canal.get("id"),
               "motivo": motivo, "em": agora().isoformat(timespec="seconds")}
    if lista == "token_morto":
        entrada["token_hash"] = token_hash(canal)
    st[lista].append(entrada)
    gravar_json(STATUS_FILE, st)


FONTES_CADASTRO = [NAVEGADOR_FILE, REDE_FILE, RESERVA_FILE, BIN / "canais.py",
                   Path(r"D:\recapd-ambientes\producao\config\parceiro.json"),
                   Path(r"D:\hipercool-videos\config\fila.json")]


def cadastro():
    """{chave: canal} do cadastro único config/canais.json. Se algum arquivo de origem mudou depois dele, refaz antes
    (bin/canais.py gerar): parceiro ganhando um destino novo não pode ficar barrado como 'reservado' até alguém
    lembrar de refazer. Decisões do dono ficam em canais.DECISOES, então refazer não perde nada."""
    try:
        m = CADASTRO_FILE.stat().st_mtime if CADASTRO_FILE.exists() else 0
        if any(f.exists() and f.stat().st_mtime > m for f in FONTES_CADASTRO):
            import importlib.util
            spec = importlib.util.spec_from_file_location("canais_cadastro", BIN / "canais.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            gravar_json(CADASTRO_FILE, mod.gerar())
    except Exception as e:  # noqa: BLE001 — sem refazer, vale o cadastro que existe
        print(f"  ! politica: não refez canais.json ({type(e).__name__}: {str(e)[:120]})", file=sys.stderr)
    return ler_json(CADASTRO_FILE, {}).get("canais", {})


def cadastro_do_canal(canal, cad=None):
    """Entrada do cadastro único deste canal (por qualquer credencial dele), ou {}."""
    ids = creds_mesmo_canal(canal.get("id")) | {canal.get("id")}
    for x in (cad if cad is not None else cadastro()).values():
        if ids & set(x.get("creds") or []):
            return x
    return {}


def estado_do_cadastro(x, creds=None):
    """'ativo' ou o motivo do bloqueio (suspensos/token_morto/desativados/pausados) — calculado na hora, nunca
    guardado no cadastro (foto velha: em 18/10 o inovare_eng foi religado no rede_canais e o cadastro ainda dizia pausado)."""
    creds = creds if creds is not None else {c["id"]: c for c in carregar_creds()}
    for cid in x.get("creds") or []:
        if cid in creds:
            return motivo_bloqueio(creds[cid]) or "ativo"
    return "sem credencial"


def _reservas():
    """{id do canal: projeto dono}: cadastro único primeiro, depois canais_reservados.json e a rede."""
    out = {}
    for x in cadastro().values():
        if x.get("dono"):
            for cid in x.get("creds") or []:
                out[cid] = x["dono"]
    res = ler_json(RESERVA_FILE, {})
    for proj, ids in res.items():
        if not proj.startswith("_") and isinstance(ids, list):
            for cid in ids:
                out.setdefault(cid, PROJETO_ANTIGO.get(proj, proj))
    # canais da rede (rede_canais.json) e credenciais ainda nao identificadas ficam fora dos pools
    mapa = rede()
    for c in mapa.get("canais", []):
        for cid in c.get("creds") or []:
            out.setdefault(cid, PROJETO_REDE)
    for cid in mapa.get("a_verificar", {}):
        if not cid.startswith("_"):
            out.setdefault(cid, "a_verificar")
    return out


def reservado_para(canal, reservas=None):
    """Projeto dono do canal, ou None. Canal reservado não entra nos pools/rotação
    dos postadores e só aceita upload com --projeto igual ao dono."""
    return (reservas if reservas is not None else _reservas()).get(canal.get("id"))


def canais_ativos():
    st, res = _status(), _reservas()
    return [c for c in carregar_creds()
            if c.get("tem_upload") and not motivo_bloqueio(c, st)
            and not reservado_para(c, res)]


def eh_manga(nome):
    n = norm(nome)
    return "manga" in n or "manhwa" in n or "anime" in n


def carregar_pools():
    """(canais_ia, canais_manga) — só nomes de canais ATIVOS."""
    vivos = [c["nome"] for c in canais_ativos()]
    return ([n for n in vivos if not eh_manga(n)],
            [n for n in vivos if eh_manga(n)])


def filtrar_ativos(nomes):
    """Mantém só os nomes (de um postar.json, por ex.) que são canais ativos."""
    ativos = {norm(c["nome"]): c["nome"] for c in canais_ativos()}
    return [ativos[norm(n)] for n in (nomes or []) if norm(n) in ativos]


def achar_canal(nome_ou_id, canais=None):
    """Acha o canal por id ou nome exato (normalizado). Match parcial só se for
    ÚNICO — evita postar no canal errado ('inovare' casa com uns 15 canais)."""
    canais = canais if canais is not None else carregar_creds()
    alvo = norm(nome_ou_id)
    if not alvo:
        return None, "nome do canal vazio"
    por_id = [c for c in canais if c.get("id") == nome_ou_id]
    if por_id:
        return por_id[0], None
    exatos = [c for c in canais if norm(c["nome"]) == alvo]
    if len(exatos) == 1:
        return exatos[0], None
    if len(exatos) > 1:
        ids = ", ".join(c["id"] for c in exatos)
        return None, f"nome '{nome_ou_id}' é ambíguo ({len(exatos)} canais) — use o id: {ids}"
    parciais = [c for c in canais if alvo in norm(c["nome"])]
    if len(parciais) == 1:
        return parciais[0], None
    if parciais:
        nomes = "; ".join(c["nome"].strip() for c in parciais[:6])
        return None, f"'{nome_ou_id}' casa com {len(parciais)} canais ({nomes}) — use o nome exato ou o id"
    return None, f"canal não encontrado: {nome_ou_id}"


# ─────────────────────────── parada geral ──────────────────────────────────
def parada_ativa():
    return ler_json(PARADO_FILE, None)


def ativar_parada(motivo, canal_nome=None):
    gravar_json(PARADO_FILE, {
        "desde": agora().isoformat(timespec="seconds"),
        "motivo": motivo,
        "canal": (canal_nome or "").strip() or None,
        "como_retomar": "revise o motivo e rode: python bin/politica.py --retomar",
    })


def retomar():
    if PARADO_FILE.exists():
        PARADO_FILE.unlink()
        return True
    return False


# ─────────────────────────── registro de uploads ───────────────────────────
def _ler_ledger():
    if not LEDGER_FILE.exists():
        return []
    out = []
    for linha in LEDGER_FILE.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(linha))
        except Exception:
            continue
    return out


def _dt(s):
    if not s:
        return None
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.astimezone()


def registrar_upload(canal, video_id, arquivo, publish_at=None, projeto=None, tipo=None):
    """projeto/tipo/caminho desde 18/10: sem eles não dava pra saber quem postou o quê (cota por projeto,
    desempenho por projeto/tipo, mesmo vídeo em dois projetos). 'arquivo' segue só o nome (quem procura por nome)."""
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    reg = {
        "ts": agora().isoformat(timespec="seconds"),
        "canal_id": canal.get("id"),
        "canal": canal.get("nome", "").strip(),
        "video_id": video_id,
        "arquivo": Path(arquivo).name,
        "caminho": str(Path(arquivo).resolve()),
        "publish_at": publish_at,
        "projeto": projeto,
        "tipo": tipo,
        "script": Path(sys.argv[0]).name,
    }
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    # 22/10 (P03): upload que ENTROU zera o cooldown de "limite diário" do canal
    try:
        lim = ler_json(LIMITE_DIARIO_FILE, {})
        if canal.get("id") in lim:
            lim.pop(canal["id"], None)
            gravar_json(LIMITE_DIARIO_FILE, lim)
    except Exception:  # noqa: BLE001 — limpeza do cooldown nunca derruba o registro do upload
        pass


def _do_canal(reg, canal):
    """O registro do ledger e deste canal? Credenciais-alias do mesmo canal real contam juntas."""
    if reg.get("canal_id"):
        return reg["canal_id"] in creds_mesmo_canal(canal.get("id"))
    return norm(reg.get("canal")) == norm(canal.get("nome"))


def uploads_hoje(canal=None, ledger=None):
    hoje = agora().date()
    regs = ledger if ledger is not None else _ler_ledger()
    return sum(1 for r in regs
               if _dt(r["ts"]).date() == hoje and (canal is None or _do_canal(r, canal)))


RAMPA_FILE = CONFIG_DIR / "rampa_canais.json"


def _extra_rampa(canal):
    """Degraus EXTRAS de upload do canal (bin/rampa_canais.py, dono 22/10: canal com o limite da conta
    desbloqueado e rendendo bem sobe de 4 pra 5+, um degrau por vez; pegou 'limite diário' = desce)."""
    try:
        c = (ler_json(RAMPA_FILE, {}).get("canais") or {}).get(canal.get("id")) or {}
        # 29/10 dona: canal LIBERADO no YouTube sobe até +8; e +1 vaga no dia em que o YouTube parou de entregar o
        # último vídeo (views das últimas 6 h caíram — rampa_canais.bonus_estagnacao, registrado em logs)
        extra = max(0, min(8 if c.get("liberado") else 4, int(c.get("extra", 0))))
        import rampa_canais
        return extra + rampa_canais.bonus_estagnacao(canal.get("id"))
    except Exception:  # noqa: BLE001
        return 0


def teto_canal(canal, cfg=None, cad=None):
    """Máximo de vídeos que ABREM por dia no canal (dia de lá): o da política + a rampa do canal (22/10),
    apertado pelo max_dia do cadastro (nunca afrouxa). O de UPLOAD por dia segue a mesma soma (cota_restante)."""
    extra = _extra_rampa(canal)
    teto = (cfg or politica())["max_uploads_por_canal_dia"] + extra
    m = cadastro_do_canal(canal, cad).get("max_dia")
    # 23/10 (dono: "sobe a rampa de 4 pra 5 mas não faz nos dias seguintes"): o max_dia do cadastro (3 em 19 canais)
    # cortava o teto e o degrau da rampa nunca valia. O degrau soma também ao max_dia (a rampa só sobe com dados).
    return min(teto, int(m) + extra) if m else teto


def _reserva(canal, projeto, x=None):
    """Vagas por dia guardadas pro DONO quando quem posta é alimentador 'livre' (cadastro reserva_dono): o react da
    rede sobe poucas horas antes de abrir, e o parceiro programando a semana inteira tomaria o dia dele."""
    if not projeto or _modo(canal, projeto) != "livre":
        return 0
    return int((x or cadastro_do_canal(canal)).get("reserva_dono") or 0)


def _hora_local(canal, x=None):
    try:
        from zoneinfo import ZoneInfo
        return agora().astimezone(ZoneInfo((x or cadastro_do_canal(canal)).get("fuso") or "America/Sao_Paulo"))
    except Exception:  # noqa: BLE001 (sem tzdata no Python de quem chamou)
        return agora()


BLOQUEADOS_FILE = CONFIG_DIR / "bloqueados.json"
_bloq_cache = (None, set())


def bloqueados():
    """ids dos vídeos que o Studio mostra "Bloqueado"/direitos (config/bloqueados.json, avisos_studio.py, 21/10).
    Não abrem: não ocupam a vaga de PUBLICAÇÃO do dia (o upload em si continua contando)."""
    global _bloq_cache
    try:
        mt = BLOQUEADOS_FILE.stat().st_mtime
    except OSError:
        return set()
    if _bloq_cache[0] != mt:
        _bloq_cache = (mt, set(ler_json(BLOQUEADOS_FILE, {})))
    return _bloq_cache[1]


def canal_vazio_hoje(canal, regs=None):
    """Nada subido nem publicando hoje (dia de lá) neste canal — regra 'nunca sem postagem' passa na frente."""
    hoje = _hora_local(canal).date()
    tz = _hora_local(canal).tzinfo
    bloq = bloqueados()
    for r in (regs if regs is not None else _ler_ledger()):
        if _do_canal(r, canal) and r.get("video_id") not in bloq:
            t = _dt(r.get("publish_at")) or _dt(r["ts"])
            if t and t.astimezone(tz).date() == hoje:
                return False
    return True


def pode_postar(canal, projeto, regs=None, cad=None):
    """None se este projeto pode subir neste canal agora; senão (codigo, mensagem).
    Canal sem dono: livre. Dono: sempre. Alimentador 'livre': divide o teto. 'sobra': só com o canal vazio no dia ou
    depois de libera_as (hora de lá), quando a janela do dono acabou. Outro projeto: reservado."""
    dono = reservado_para(canal)
    if not dono or projeto == dono:
        return None
    x = cadastro_do_canal(canal, cad)
    modo = (x.get("alimentadores") or {}).get(projeto)
    if modo == "livre":
        return None
    if modo == "sobra":
        if canal_vazio_hoje(canal, regs):
            return None
        libera = x.get("libera_as")
        local = _hora_local(canal, x)
        abertos_hoje = sum(1 for t in _publicacoes(canal, regs) if t.astimezone(local.tzinfo).date() == local.date())
        if libera and local.strftime("%H:%M") >= libera and abertos_hoje < teto_canal(canal, cad=cad):
            return None
        return "cota_diaria", f"vaga do dono ({dono}) até {libera or 'o fim do dia'} — {projeto} só pega a sobra"
    return "reservado", f"canal '{canal['nome'].strip()}' é reservado ao projeto {dono}"


def cota_restante(canal, projeto=None):
    """Quantos uploads ainda cabem hoje neste canal (teto do canal e teto global). Com projeto: 0 se ele não pode
    postar aqui agora (reservado ou vaga do dono)."""
    cfg = politica()
    regs = _ler_ledger()
    if projeto and pode_postar(canal, projeto, regs):
        return 0
    livre = cfg["max_uploads_por_canal_dia"] + _extra_rampa(canal) - uploads_hoje(canal, regs)
    res = _reserva(canal, projeto)
    if res and agora().strftime("%H:%M") < LIBERA_RESERVA:  # depois disso a vaga de upload do dono que sobrou é livre
        dono, hoje = reservado_para(canal), agora().date()
        do_dono = sum(1 for r in regs if _dt(r["ts"]).date() == hoje and _do_canal(r, canal) and r.get("projeto") == dono)
        livre -= max(res - do_dono, 0)
    if cfg.get("max_uploads_total_dia"):
        livre = min(livre, cfg["max_uploads_total_dia"] - uploads_hoje(None, regs))
    return max(0, livre)


def _publicacoes(canal, regs=None):
    """Quando cada vídeo do canal abre (publish_at, ou a hora do upload), de TODOS os projetos. Bloqueado no Studio não
    abre: fica de fora."""
    bloq = bloqueados()
    # 13/11: SIMULADOS = horários ocupados só de mentira (ensaio do parceiro_diario: {id do canal: [datetime]}). O
    # ensaio não grava no ledger, então todo vídeo simulado recebia o MESMO horário livre (6 no mesmo minuto) e a
    # agenda do ensaio não servia pra conferir nada. Vazio na postagem de verdade.
    return [t for t in (_dt(r.get("publish_at")) or _dt(r["ts"])
                        for r in (regs if regs is not None else _ler_ledger())
                        if _do_canal(r, canal) and r.get("video_id") not in bloq) if t] + list(
        SIMULADOS.get(canal.get("id"), []))


SIMULADOS = {}


def _slots_canal(x):
    """Horários preferidos do canal no cadastro (parceiro + rede); sem eles, o pico do hipercool de hora em hora."""
    hs = sorted(set((x.get("horarios_parceiro") or []) + (x.get("horarios_rede") or [])))
    pico = x.get("pico_hipercool")
    if not hs and pico:
        hs = [f"{h:02d}:00" for h in range(int(pico[0]), int(pico[1]) + 1)]
    return hs


def horario_publicacao(canal, pedido=None, projeto=None):
    """Agenda ÚNICA do canal (18/10): horário efetivo de publicação respeitando, com os vídeos de TODOS os projetos,
    (1) o intervalo mínimo entre vídeos do canal e (2) o teto por DIA DE PUBLICAÇÃO (dia de lá; teto_canal) — dia cheio
    passa pro 1º horário do canal no dia seguinte. Com projeto alimentador 'livre', o dia guarda reserva_dono vagas
    pro dono (o react sobe poucas horas antes de abrir; o parceiro programa 7 dias). Cada projeto continua propondo a
    hora; quem decide é aqui. Retorna None = pode publicar já; senão um datetime futuro."""
    cfg = politica()
    horas = cfg.get("intervalo_min_horas_mesmo_canal") or 0
    base = _dt(pedido) if isinstance(pedido, str) else pedido
    alvo = base or agora()
    bloq = bloqueados()
    regs = [r for r in _ler_ledger() if _do_canal(r, canal) and r.get("video_id") not in bloq]
    ocupados = _publicacoes(canal, regs)
    x = cadastro_do_canal(canal)
    tz = _hora_local(canal, x).tzinfo
    teto = teto_canal(canal, cfg)
    res = _reserva(canal, projeto, x)
    dono = reservado_para(canal) if res else None
    do_dono = [t for t in (_dt(r.get("publish_at")) or _dt(r["ts"]) for r in regs if r.get("projeto") == dono) if t] \
        if res else []
    gap = timedelta(hours=horas)
    for _ in range(40):
        # Longe do VIZINHO mais proximo, nao depois do ULTIMO agendado (16/10): a rede agenda o Veo ate 2 dias a frente,
        # e "depois do ultimo" empurrava o react de hoje para depois de amanha.
        perto = [t for t in ocupados if abs(alvo - t) < gap] if horas else []
        if perto:
            alvo = max(perto) + gap
            continue
        dia = alvo.astimezone(tz).date()
        n_dia = sum(1 for t in ocupados if t.astimezone(tz).date() == dia)
        guardado = max(res - sum(1 for t in do_dono if t.astimezone(tz).date() == dia), 0)
        if n_dia + guardado < teto:
            break
        prox = (alvo.astimezone(tz) + timedelta(days=1)).replace(second=0, microsecond=0)
        slots = _slots_canal(x)
        if slots:
            hh, mm = (int(v) for v in slots[0].split(":"))
            prox = prox.replace(hour=hh, minute=mm)
        alvo = prox
    if alvo <= agora() + timedelta(minutes=5):
        return None
    return alvo


def _modo(canal, projeto):
    """Como este projeto entra no canal: None (canal sem dono ou projeto é o dono), 'livre', 'sobra' ou 'reservado'."""
    dono = reservado_para(canal)
    if not dono or projeto == dono:
        return None
    return (cadastro_do_canal(canal).get("alimentadores") or {}).get(projeto) or "reservado"


def horario_obrigatorio(canal, pedido=None, projeto=None, tipo=None):
    """Como horario_publicacao, mas nunca 'já': no mínimo agora + MIN_AGENDA_MIN (regra do dono, 18/10).
    Em 17-18/10 dez uploads do hipercool (public sem publish_at) abriram na hora, sem a checagem de direitos.
    Alimentador 'sobra' pega a vaga que sobrou HOJE (agora+11), nunca um horário de amanhã (que é do dono)."""
    minimo = agora() + timedelta(minutes=MIN_AGENDA_MIN)
    if projeto and _modo(canal, projeto) == "sobra":
        pedido = None
    base = _dt(pedido) if isinstance(pedido, str) else pedido
    base = max(base, minimo) if base else minimo
    if tipo == "completo":
        return horario_longo(canal, base) or base
    return horario_publicacao(canal, base, projeto) or base


def horario_longo(canal, base):
    """04/11 dona: "os vídeos longos seguem outra linha — têm que ter um espaço de prioridade todo dia". O longo NÃO
    disputa o teto diário com os Shorts (os de parceiro programam 7 dias e o longo ia parar 2-3 dias à frente): cada
    canal tem LONGOS_POR_DIA vagas só de longo por dia (politica.json "longos_por_dia_canal", padrão 2), e o longo só
    fica a intervalo_min_horas_mesmo_canal de distância de QUALQUER vídeo do canal. None = pode já."""
    cfg = politica()
    gap = timedelta(hours=cfg.get("intervalo_min_horas_mesmo_canal") or 0)
    por_dia = int(cfg.get("longos_por_dia_canal") or 2)
    bloq = bloqueados()
    regs = [r for r in _ler_ledger() if _do_canal(r, canal) and r.get("video_id") not in bloq]
    ocupados = _publicacoes(canal, regs)
    longos = [t for t in (_dt(r.get("publish_at")) or _dt(r["ts"]) for r in regs if r.get("tipo") == "completo") if t]
    tz = _hora_local(canal, cadastro_do_canal(canal)).tzinfo
    alvo = base
    for _ in range(60):
        perto = [t for t in ocupados if abs(alvo - t) < gap] if gap else []
        if perto:
            alvo = max(perto) + gap
            continue
        dia = alvo.astimezone(tz).date()
        if sum(1 for t in longos if t.astimezone(tz).date() == dia) < por_dia:
            break
        alvo = (alvo.astimezone(tz) + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    return None if alvo <= agora() + timedelta(minutes=5) else alvo


def agenda_minima(video=None):
    """Horário mais cedo aceitável p/ publicar (dono 21/10): agora + MIN_AGENDA_MIN (+ duração se for longo > 3 min),
    arredondado pra cima em 15 min. A checagem de direitos termina ~10 min DEPOIS do upload."""
    dur = 0.0
    if video:
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(video)], capture_output=True, text=True, timeout=60)
            dur = float(r.stdout.strip())
        except (ValueError, OSError, subprocess.SubprocessError):
            dur = 0.0
    dt = agora() + timedelta(minutes=MIN_AGENDA_MIN + (dur / 60 if dur > 180 else 0))
    dt = dt.replace(second=0, microsecond=0)
    resto = (-dt.minute) % 15
    return dt + timedelta(minutes=resto)


def rfc3339(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


# ─────────────────────────── aprovação humana ──────────────────────────────
def _chave(arquivo):
    return str(Path(arquivo).resolve()).casefold()


def status_aprovacao(arquivo, aprov=None):
    """'aprovado' / 'rejeitado' / None. Se o arquivo mudou de tamanho depois da
    decisão (re-render), a decisão é descartada e precisa revisar de novo."""
    aprov = aprov if aprov is not None else ler_json(APROV_FILE, {})
    d = aprov.get(_chave(arquivo))
    if not d:
        return None
    try:
        if d.get("tamanho") and d["tamanho"] != Path(arquivo).stat().st_size:
            return None
    except OSError:
        return None
    return d.get("status")


def aprovado(arquivo, aprov=None):
    if not politica().get("exigir_aprovacao_humana"):
        return True
    return status_aprovacao(arquivo, aprov) == "aprovado"


def marcar_aprovacao(arquivo, status, nota=""):
    aprov = ler_json(APROV_FILE, {})
    aprov[_chave(arquivo)] = {
        "arquivo": str(Path(arquivo).resolve()),
        "status": status,
        "tamanho": Path(arquivo).stat().st_size,
        "em": agora().isoformat(timespec="seconds"),
        "nota": nota,
    }
    gravar_json(APROV_FILE, aprov)


# ─────────────────────────── checagem e erros ──────────────────────────────
def _postagem_desligada(projeto):
    """Motivo se a postagem deste projeto está desligada no controle único (D:\\video-fila\\controle.py), senão None."""
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import controle
        ok, motivo = controle.ligado(projeto or "postador", "postagem")
        return None if ok else motivo
    except Exception:  # noqa: BLE001 — sem o controle, vale o resto da política
        return None


LIMITE_DIARIO_FILE = CONFIG_DIR / "limite_diario.json"
ADVERTENCIAS_FILE = CONFIG_DIR / "advertencias_upload.json"


def marcar_advertencias(canal_id):
    """O Studio recusou uploads por "Muitos avisos"/diretrizes da comunidade: aguarda 24 h.
    Não confundir com erro genérico nem com advertência de direitos autorais detectada no conteúdo."""
    data = ler_json(ADVERTENCIAS_FILE, {})
    d = data.get(canal_id) or {}
    ate = agora() + timedelta(hours=24)
    data[canal_id] = {"ate": ate.isoformat(timespec="seconds"), "vezes": int(d.get("vezes", 0)) + 1}
    gravar_json(ADVERTENCIAS_FILE, data)
    return ate


def em_advertencias(canal):
    """Até quando o canal está em espera após o bloqueio de uploads por muitos avisos."""
    d = ler_json(ADVERTENCIAS_FILE, {}).get(canal.get("id")) or {}
    ate = _dt(d.get("ate") or "")
    return ate if ate and ate > agora() else None


def eh_advertencias(texto):
    """Reconhece somente o bloqueio de envio por muitos avisos da comunidade."""
    low = (texto or "").lower()
    aviso = any(k in low for k in ("muitos avisos", "many warnings", "too many warnings"))
    bloqueio = any(k in low for k in ("não é possível enviar", "nao e possivel enviar", "unable to upload",
                                      "cannot upload", "can't upload", "upload blocked"))
    diretrizes = any(k in low for k in ("diretrizes da comunidade", "community guidelines"))
    return aviso or (bloqueio and diretrizes)


def marcar_limite_diario(canal_id):
    """O YouTube recusou com "limite diário de envios da conta": o canal espera 24 h SEM nenhuma nova
    tentativa (dona, 22/10: "se der o aviso de 24h tem que esperar e não ficar tentando" — o ForjaReact
    ficou bloqueado justamente pelas 199 tentativas em 4 dias, cada uma reenviando o arquivo inteiro)."""
    data = ler_json(LIMITE_DIARIO_FILE, {})
    d = data.get(canal_id) or {}
    ate = agora() + timedelta(hours=24)
    # 13/11 22h40 (Medieval 4 no Fio da Meada: 11 envios em 24 h, 7 deles entre 04:52 e 05:28 — Shorts agendados): o
    # limite do YouTube é de envios em 24 h CORRIDAS; a espera fixa de 24 h deixava a série parada até 22:28 do dia
    # seguinte, mas às ~05:30 já saem 7 envios da janela. Fim da espera = quando sair da janela o envio que deixa o
    # canal abaixo de LIMITE_ENVIOS_24H (7), + 30 min de folga; nunca depois das 24 h. Continua 1 tentativa por espera.
    # LIMITE_JANELA_REAL=0 volta as 24 h fixas.
    if os.environ.get("LIMITE_JANELA_REAL", "1") != "0":
        try:
            import youtube_web_poster as _yw
            slug = _yw.entrada_do_cred(canal_id)[0]
            lim = int(os.environ.get("LIMITE_ENVIOS_24H", "7"))
            if slug:
                corte = agora() - timedelta(hours=24)
                envios = []
                for l in (ROOT / "logs" / "youtube_http.log").read_text(encoding="utf-8", errors="ignore") \
                        .splitlines()[-4000:]:
                    m = re.match(r"\[(\d\d)/(\d\d) (\d\d):(\d\d):(\d\d)\] (\S+): subiu", l)
                    if m and m.group(6) == slug:
                        t = agora().replace(month=int(m.group(2)), day=int(m.group(1)), hour=int(m.group(3)),
                                            minute=int(m.group(4)), second=int(m.group(5)), microsecond=0)
                        if t >= corte:
                            envios.append(t)
                envios.sort()
                if len(envios) >= lim:
                    # sai da janela o envio na posição (n - lim): depois dele sobram lim-1 -> 1 vaga livre
                    livre = envios[len(envios) - lim] + timedelta(hours=24, minutes=30)
                    if agora() + timedelta(hours=1) < livre < ate:
                        ate = livre
        except Exception:  # noqa: BLE001
            pass
    data[canal_id] = {"ate": ate.isoformat(timespec="seconds"), "vezes": int(d.get("vezes", 0)) + 1}
    gravar_json(LIMITE_DIARIO_FILE, data)
    try:  # rampa (22/10): pegou o limite = o degrau extra do canal desce na hora
        import rampa_canais
        rampa_canais.descer(canal_id)
    except Exception:  # noqa: BLE001
        pass
    return ate


def em_limite_diario(canal):
    """Até quando o canal está em cooldown do "limite diário" (datetime), ou None. Upload ok zera (registrar_upload)."""
    d = ler_json(LIMITE_DIARIO_FILE, {}).get(canal.get("id")) or {}
    ate = _dt(d.get("ate") or "")
    return ate if ate and ate > agora() else None


def segurando_viral(canal):
    """30/10 dona ("vídeo ainda viralizando + postar outro = o primeiro para"): motivo se o canal segura envios agora
    (rampa_canais.segurar_viral), senão None. Falhou a leitura = não segura."""
    try:
        import rampa_canais
        return rampa_canais.segurar_viral(canal.get("id"))
    except Exception:  # noqa: BLE001
        return None


def checar_upload(canal, arquivo, projeto=None, tipo=None):
    """None se o upload pode seguir; senão (codigo, mensagem)."""
    if tipo == "completo":
        return _checar_longo(canal, arquivo, projeto)
    p = parada_ativa()
    if p:
        return "parado", f"parada geral desde {p.get('desde')}: {p.get('motivo')}"
    desligada = _postagem_desligada(projeto)
    if desligada:
        return "parado", desligada
    m = motivo_bloqueio(canal)
    if m:
        return "canal_bloqueado", f"canal '{canal['nome'].strip()}' está em {m}"
    ate = em_limite_diario(canal)
    if ate:  # 22/10 (P03): não reenvia o arquivo só pra ver o mesmo "limite diário" do Studio
        return "limite", f"canal no limite diário de envios do YouTube — sem novo envio até {ate:%d/%m %H:%M}"
    ate_aviso = em_advertencias(canal)
    if ate_aviso:
        return "advertencias", f"canal bloqueado por muitos avisos — sem novo envio até {ate_aviso:%d/%m %H:%M}"
    veto = pode_postar(canal, projeto)
    if veto:
        return veto
    if cota_restante(canal, projeto) <= 0:
        cfg = politica()
        return "cota_diaria", (f"cota do dia esgotada (máx {cfg['max_uploads_por_canal_dia']} uploads/canal hoje, "
                               f"{cfg.get('max_uploads_total_dia')}/dia no total)")
    viral = segurando_viral(canal)
    if viral:
        return "cota_diaria", viral
    if not aprovado(arquivo):
        return "nao_aprovado", f"'{Path(arquivo).name}' não foi aprovado — rode bin/aprovar.py"
    return None


def _checar_longo(canal, arquivo, projeto=None):
    """04/11 dona ("os longos seguem outra linha, espaço de prioridade todo dia"; "se estão decolando, poste
    programado"): o longo tem as MESMAS travas de segurança (parada, canal bloqueado, limite do YouTube, avisos,
    aprovação), mas NÃO a cota diária dos Shorts nem a espera do viral — ele sai programado (horario_longo)."""
    p = parada_ativa()
    if p:
        return "parado", f"parada geral desde {p.get('desde')}: {p.get('motivo')}"
    desligada = _postagem_desligada(projeto)
    if desligada:
        return "parado", desligada
    m = motivo_bloqueio(canal)
    if m:
        return "canal_bloqueado", f"canal '{canal['nome'].strip()}' está em {m}"
    ate = em_limite_diario(canal)
    if ate:
        return "limite", f"canal no limite diário de envios do YouTube — sem novo envio até {ate:%d/%m %H:%M}"
    ate_aviso = em_advertencias(canal)
    if ate_aviso:
        return "advertencias", f"canal bloqueado por muitos avisos — sem novo envio até {ate_aviso:%d/%m %H:%M}"
    veto = pode_postar(canal, projeto)
    if veto:
        return veto
    if not aprovado(arquivo):
        return "nao_aprovado", f"'{Path(arquivo).name}' não foi aprovado — rode bin/aprovar.py"
    return None


def classificar_erro(texto):
    low = (texto or "").lower()
    if eh_advertencias(texto):
        return "advertencias"
    if "suspended" in low:
        return "suspenso"
    if "uploadlimitexceeded" in low or "quotaexceeded" in low or "ratelimitexceeded" in low:
        return "limite"
    if any(k in low for k in ("invalid_grant", "unauthorized_client", "invalid_client",
                              "accessnotconfigured", "has not been used in project")):
        return "morto"
    return "erro"


def tratar_erro(canal, classe, texto):
    """Efeitos colaterais de um erro do YouTube: marca canal e/ou para tudo."""
    if classe == "advertencias":
        marcar_advertencias(canal["id"])
    elif classe == "suspenso":
        marcar_canal(canal, "suspensos", (texto or "")[:200])
        if politica().get("parar_tudo_ao_detectar_suspensao"):
            ativar_parada(f"YouTube suspendeu '{canal['nome'].strip()}'", canal["nome"])
    elif classe == "morto":
        marcar_canal(canal, "token_morto", (texto or "")[:200])


# ─────────────────────────── helper p/ os scripts de fila ──────────────────
def _usar_navegador(cred_id):
    """O canal desta credencial (ou de um alias dela) está marcado "usar": true em youtube_navegador.json?"""
    mapa = ler_json(NAVEGADOR_FILE, {}).get("canais", {})
    ids = creds_mesmo_canal(cred_id)
    return any(e.get("usar") and ids & set(e.get("creds", [])) for e in mapa.values())


def _dims_video(arq):
    """03/11 03h: com a CPU do PC1 em 100% o ffprobe passou de 120 s e o Short (1080x1920 de verdade) foi dado como
    "abaixo de 1080p" e NÃO subiu. Agora: 3 tentativas de 120 s; o ffprobe só lê o cabeçalho, a demora é fila de CPU."""
    import subprocess as _sp
    ultimo = None
    for _ in range(3):
        try:
            r = _sp.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                         "-of", "csv=p=0:s=x", str(arq)], capture_output=True, text=True, timeout=120,
                        creationflags=getattr(_sp, "CREATE_NO_WINDOW", 0))
            w, h = (int(x) for x in r.stdout.strip().split("x")[:2])
            return w, h
        except (_sp.TimeoutExpired, ValueError) as e:
            ultimo = e
    raise ultimo


def garantir_1080(arquivo):
    """REGRA da dona (31/10): nenhum vídeo sai com menos de 1080p (lado menor >= 1080), de nenhum projeto.
    Abaixo disso faz o upscale (spline + nitidez leve: VMAF 99,6 x render nativo) num arquivo irmão <nome>_1080p.mp4
    (reaproveitado nas novas tentativas) e devolve o caminho dele. Não deu = levanta (o vídeo NÃO sobe).
    Usada por postar_youtube, youtube_web_poster, youtube_poster e pelos posters de TikTok/Instagram/Facebook/Kwai."""
    import subprocess as _sp
    arquivo = Path(arquivo)
    w, h = _dims_video(arquivo)
    if min(w, h) >= 1080:
        return arquivo
    alvo = arquivo.with_name(arquivo.stem + "_1080p.mp4")
    if alvo.exists() and alvo.stat().st_mtime >= arquivo.stat().st_mtime:
        try:
            if min(_dims_video(alvo)) >= 1080:
                _herdar_aprovacao(arquivo, alvo)
                return alvo
        except Exception:  # noqa: BLE001 — arquivo pela metade: refaz
            pass
    escala = ("scale=-2:1080:flags=spline,unsharp=5:5:0.6" if w >= h
              else "scale=1080:-2:flags=spline,unsharp=5:5:0.6")
    tmp = alvo.with_suffix(".tmp.mp4")
    if _upscale_celular(arquivo, tmp, escala):
        tmp.replace(alvo)
        _herdar_aprovacao(arquivo, alvo)
        return alvo
    # 05/11 (pesquisador area_desempenho_gpu, ideia ffmpeg-qsv-lite): chip de vídeo da Intel (QSV) primeiro — medido no
    # PC1 (i5-8365U): 6,7 s x 10,5 s do libx264, SSIM 0,985 entre os dois. Falhou (máquina sem QSV) = libx264 como antes.
    r = _sp.run(["ffmpeg", "-y", "-v", "error", "-i", str(arquivo), "-vf", escala, "-c:v", "h264_qsv", "-global_quality",
                 "22", "-c:a", "copy", "-movflags", "+faststart", str(tmp)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                creationflags=getattr(_sp, "CREATE_NO_WINDOW", 0))
    if r.returncode != 0 or not tmp.exists():
        r = _sp.run(["ffmpeg", "-y", "-v", "error", "-i", str(arquivo), "-vf", escala, "-c:v", "libx264", "-preset",
                     "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(tmp)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    creationflags=getattr(_sp, "CREATE_NO_WINDOW", 0))
    if r.returncode != 0:  # 03/11: o log só mostrava o comando cortado — agora mostra o motivo do ffmpeg
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg rc={r.returncode}: {(r.stderr or '').strip()[-300:]}")
    if min(_dims_video(tmp)) < 1080:
        raise RuntimeError(f"upscale não chegou a 1080p: {tmp}")
    tmp.replace(alvo)
    _herdar_aprovacao(arquivo, alvo)
    return alvo


CELULARES = ("s20ultra", "s20", "a3", "g20")  # a3 = Redmi A3 (04/11 20h): 1080p de 8 s em 10 s; g20 = Moto G20: encode 6 s mas Wi-Fi lento (92 s ida+volta)  # 04/11 dona: "tente usar os telefones … usa o máximo que dá" (Termux, ssh porta 8022)
_CEL_VEZ = Path(r"D:\postador-de-videos\logs\celular_vez.txt")


def _upscale_celular(arquivo, tmp, escala):
    """04/11: o upscale p/ 1080p (ffmpeg puro) vai pros Galaxy S20 — chip de vídeo (h264_mediacodec, ~3x tempo real;
    medido: 8 s de 720p -> 1080p em 11 s com ida e volta) e libera a CPU do PC1. Revezamento entre os dois; celular
    fora/erro = próximo; nenhum = False (o PC1 faz como antes). CELULAR_UPSCALE=0 desliga."""
    import os as _os
    import subprocess as _sp
    import uuid
    if _os.environ.get("CELULAR_UPSCALE", "1") == "0":
        return False
    try:
        vez = int(_CEL_VEZ.read_text().strip() or 0)
    except (OSError, ValueError):
        vez = 0
    sem = getattr(_sp, "CREATE_NO_WINDOW", 0)
    for i in range(len(CELULARES)):
        cel = CELULARES[(vez + i) % len(CELULARES)]
        nome = f"up_{uuid.uuid4().hex[:10]}"
        try:
            if cel == "a3":  # celular de uso da dona, sempre fora da tomada: < 30% sem carregador = não usa
                b = _sp.run(["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", cel, "termux-battery-status"],
                            capture_output=True, text=True, timeout=40, creationflags=sem).stdout
                import json as _js
                b = _js.loads(b or "{}")
                if b.get("plugged") == "UNPLUGGED" and int(b.get("percentage") or 0) < 30:
                    continue
            ok = _sp.run(["scp", "-q", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", str(arquivo), f"{cel}:{nome}.in.mp4"],
                         capture_output=True, timeout=300, creationflags=sem).returncode == 0
            if ok:
                r = _sp.run(["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", cel,
                             f'ffmpeg -y -v error -i {nome}.in.mp4 -vf "{escala},format=nv12" -c:v h264_mediacodec '
                             f'-b:v 10M -c:a copy -movflags +faststart {nome}.mp4; rc=$?; rm -f {nome}.in.mp4; exit $rc'],
                            capture_output=True, text=True, timeout=900, creationflags=sem)
                ok = r.returncode == 0 and _sp.run(
                    ["scp", "-q", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", f"{cel}:{nome}.mp4", str(tmp)],
                    capture_output=True, timeout=300, creationflags=sem).returncode == 0
                _sp.run(["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", cel, f"rm -f {nome}.mp4"],
                        capture_output=True, timeout=60, creationflags=sem)
            if ok and tmp.exists() and min(_dims_video(tmp)) >= 1080:
                try:
                    _CEL_VEZ.write_text(str((vez + i + 1) % len(CELULARES)))
                except OSError:
                    pass
                return True
        except Exception:  # noqa: BLE001 — celular fora/lento: tenta o outro ou o PC1
            pass
        tmp.unlink(missing_ok=True)
    return False


def _herdar_aprovacao(original, copia):
    """01/11: a cópia em 1080p é o MESMO vídeo — herda a aprovação humana do original (senão checar_upload barrava
    tudo com "corte_01_1080p.mp4 não foi aprovado")."""
    st = status_aprovacao(original)
    if st and status_aprovacao(copia) != st:
        marcar_aprovacao(copia, st, nota=f"herdado de {Path(original).name} (upscale 1080p)")


def postar_youtube(canal_nome, arquivo, titulo, descricao, tags,
                   privacy="public", publish_at=None, projeto=None,
                   categoria=None, idioma=None, sintetico=False, thumbnail=None, playlist=None, tipo=None):
    """Chama o youtube_poster.py e devolve (status, info).

    projeto = quem está postando de verdade (hipercool, parceiro, manhwa-react...), NÃO o dono do canal: a reserva e a
    vaga do dono vêm do cadastro (config/canais.json). tipo = short/completo/compilado/react/veo/historias... (ledger).

    thumbnail (jpg/png ate 2 MB) e playlist (nome; cria se nao existir) so valem no upload pelo navegador;
    se falharem o video sobe assim mesmo (o aviso fica no log do youtube_web_poster).

    status: ok | limite | advertencias | cota | morto | suspenso | parado | nao_aprovado | reservado | timeout | erro
    info:   url (ok) ou mensagem curta.
    Quem chama deve: bloquear o canal em limite/cota/morto, PARAR TUDO em
    suspenso/parado e NÃO repetir o item no mesmo dia em timeout.
    """
    canal, err = achar_canal(canal_nome)
    if not canal:
        return "erro", err
    # 30/10: canal JÁ em espera não chama o poster — a recusa da checagem prévia voltava como STATUS: limite e o
    # marcar_limite_diario abaixo empurrava a espera +24 h a cada tentativa (a rede tenta de hora em hora: ManhwaReact
    # re-marcado 189 vezes, Manhwa Noturno 200; os canais nunca saíam do "limite").
    ate0 = em_limite_diario(canal)
    if ate0:
        return "limite", f"canal no limite diário de envios do YouTube — sem novo envio até {ate0:%d/%m %H:%M}"
    ate_aviso0 = em_advertencias(canal)
    if ate_aviso0:
        return "advertencias", f"canal bloqueado por muitos avisos — sem novo envio até {ate_aviso0:%d/%m %H:%M}"
    try:  # 31/10 REGRA da dona: nada sobe com menos de 1080p
        arquivo = garantir_1080(arquivo)
    except Exception as e:  # noqa: BLE001
        return "erro", f"vídeo abaixo de 1080p e o upscale falhou ({type(e).__name__}: {str(e)[:150]}) — não sobe"
    tags_str = ",".join(tags) if isinstance(tags, (list, tuple)) else str(tags or "")
    try:  # 23/10: indicação do canal parceiro da dupla (config/indicacoes.json); falhar aqui nunca impede o upload
        import indicacoes
        descricao = indicacoes.na_descricao(canal["id"], descricao, titulo)
    except Exception:  # noqa: BLE001
        pass
    poster = POSTER
    if _usar_navegador(canal["id"]):  # canal marcado em config/youtube_navegador.json: sobe pelo Studio
        poster = POSTER_WEB
    elif politica().get("proibido_postar_por_api"):
        # ORDEM DO DONO (16/10): upload por API está PROIBIDO — tudo pelo navegador. Em 16/10 oito
        # vídeos do ManhwaReact-ia subiram pela API sem ninguém notar. Em vez de subir assim, o
        # postador recusa e diz o que fazer: pôr o canal em config/youtube_navegador.json.
        return "erro", (f"{canal['id']}: upload por API está proibido. Marque \"usar\": true em "
                        f"config/youtube_navegador.json pra este canal e rode de novo.")
    cmd = [sys.executable, str(poster),
           "--video", str(arquivo), "--titulo", titulo, "--descricao", descricao or "",
           "--tags", tags_str, "--canal", canal["id"], "--privacy", privacy]
    if publish_at:
        cmd += ["--publish-at", publish_at]
    if projeto:
        cmd += ["--projeto", projeto]
    if tipo:
        cmd += ["--tipo", str(tipo)]
    if categoria:
        cmd += ["--categoria", str(categoria)]
    if idioma:
        cmd += ["--idioma", idioma]
    if sintetico:
        cmd += ["--sintetico"]
    if poster == POSTER_WEB:
        if thumbnail:
            cmd += ["--thumbnail", str(thumbnail)]
        if playlist:
            cmd += ["--playlist", playlist]
    try:
        mb = Path(arquivo).stat().st_size / 1e6
    except OSError:
        mb = 0
    timeout = int(600 + 3 * mb)  # ~2,7 Mbps no pior caso; 2,4 GB -> ~2h
    if poster == POSTER_WEB:
        timeout += ESPERA_TRAVA_S  # 18/10: ForjaReact deu "timeout" sem abrir o Chrome, esperando a trava
        try:  # 23/10: canal nos notebooks tenta até 2 máquinas antes do PC1 (+ envio do arquivo por ssh e abrir o Chrome)
            import youtube_web_poster as _yw
            if (_yw.entrada_do_cred(canal.get("id"))[1] or {}).get("maquina"):
                timeout += int(600 + 3 * mb) + int(600 + mb) + 300
        except Exception:  # noqa: BLE001
            pass
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return "timeout", f"sem resposta em {timeout}s"
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"^STATUS: (\w+)\s*(.*)$", out, re.MULTILINE)
    if m:
        status, info = m.group(1), m.group(2).strip()
        if status == "limite":  # 22/10 (P03): espera 24 h sem nova tentativa (checar_upload passa a vetar)
            ate = marcar_limite_diario(canal["id"])
            info = f"{info} — canal em espera de 24 h (até {ate:%d/%m %H:%M}), sem reenvio"
        elif status == "advertencias":
            ate = marcar_advertencias(canal["id"])
            info = f"{info} — canal em espera de 24 h (até {ate:%d/%m %H:%M}), sem reenvio"
        return status, info
    # poster antigo/sem linha STATUS: cai na heurística
    if "POSTADO:" in out or "AGENDADO:" in out:
        url = next((t for t in out.split() if "youtu.be/" in t), None)
        return "ok", url
    status = classificar_erro(out)
    if status == "limite":
        ate = marcar_limite_diario(canal["id"])
        return status, f"{out.strip()[-240:]} — canal em espera de 24 h (até {ate:%d/%m %H:%M})"
    if status == "advertencias":
        ate = marcar_advertencias(canal["id"])
        return status, f"{out.strip()[-240:]} — canal em espera de 24 h (até {ate:%d/%m %H:%M})"
    return status, out.strip()[-300:]


# ─────────────────────────── CLI ───────────────────────────────────────────
def _cli_status():
    cfg = politica()
    print("=== POLÍTICA DE POSTAGEM ===")
    for k, v in cfg.items():
        if not k.startswith("_"):
            print(f"  {k}: {v}")
    p = parada_ativa()
    print()
    if p:
        print(f"*** PARADA GERAL ATIVA desde {p['desde']} — {p['motivo']}")
        print("    Nenhum upload sai até rodar: python bin/politica.py --retomar\n")
    else:
        print("Parada geral: não\n")
    regs = _ler_ledger()
    st = _status()
    res = _reservas()
    creds = carregar_creds()
    ativos = [c for c in creds if c.get("tem_upload") and not motivo_bloqueio(c, st)]
    livres = [c for c in ativos if not reservado_para(c, res)]
    print(f"Canais ativos ({len(livres)}) — uploads hoje / cota restante:")
    for c in livres:
        print(f"  {c['nome'].strip()[:40]:40} {uploads_hoje(c, regs)} / {cota_restante(c)}")
    reservados = [c for c in creds if reservado_para(c, res)]
    if reservados:
        print(f"\nCanais reservados a projetos ({len(reservados)}) — fora da rotação:")
        for c in reservados:
            bloq = motivo_bloqueio(c, st)
            print(f"  {c['nome'].strip()[:40]:40} [{reservado_para(c, res)}] "
                  + (f"BLOQUEADO: {bloq}" if bloq else f"{uploads_hoje(c, regs)} / {cota_restante(c)}"))
    print(f"\nTotal hoje: {uploads_hoje(None, regs)} (teto {cfg.get('max_uploads_total_dia')})")
    for lista in LISTAS_BLOQUEIO:
        bloq = [c for c in creds if motivo_bloqueio(c, st) == lista]
        print(f"Bloqueados em {lista}: {len(bloq)}")
    aprov = ler_json(APROV_FILE, {})
    n_ap = sum(1 for d in aprov.values() if d.get("status") == "aprovado")
    n_rj = sum(1 for d in aprov.values() if d.get("status") == "rejeitado")
    print(f"Aprovações registradas: {n_ap} aprovados, {n_rj} rejeitados"
          f" (pendentes: python bin/aprovar.py --listar)")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--retomar", action="store_true",
                    help="remove a parada geral (config/PARADO.json)")
    args = ap.parse_args()
    if args.retomar:
        p = parada_ativa()
        if not p:
            print("Não há parada geral ativa.")
            return
        print(f"Parada ativa desde {p['desde']}: {p['motivo']}")
        if input("Revisou o motivo e quer voltar a postar? [s/N] ").strip().lower() == "s":
            retomar()
            print("OK — postagem liberada.")
        else:
            print("Mantida a parada.")
        return
    _cli_status()


if __name__ == "__main__":
    main()
