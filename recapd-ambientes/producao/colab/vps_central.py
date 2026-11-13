"""vps_central.py — central do recap LONGO na VPS hermes-prod (cron 5 min). Dona 25/10/2026: "pode sair daqui (PC), mas
tem que tudo passar pela VPS; a VPS manda pro Kaggle e acompanha; eu vejo só a porcentagem; independente do PC".

25/10 v2 (dona: "rotação entre contas, 4 GPUs simultâneas"): em vez de 1 conta Kaggle, gerencia N SLOTS do pool.
Cada slot mantém 1 GPU rodando; quando a sessão de uma conta acaba, a próxima conta do slot assume. Cada conta tem
seu próprio kernel+dataset no Kaggle (criados sob demanda). 4 slots × 5-6 contas = 23 contas, 690 h/semana de GPU.

O Kaggle rastreia por conta (API key), não por IP de quem chama a API — cada conta é um "usuário" independente
com seu namespace de kernels/datasets. Os kernels rodam na infra do Google, o IP do lançador não aparece no kernel.
"""
import base64
import html
import json
import os
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CFG = json.loads((AQUI / "config.json").read_text(encoding="utf-8"))
POOL = json.loads((AQUI / "kaggle_pool.json").read_text(encoding="utf-8"))
EMPRESA = CFG.get("empresa", "Inovare (recap longo)")
# 26/10: um copyto ficou 31 min a 6 KB/s (conexão parada; a VPS sobe a 9,5 MB/s) e a central inteira travou junto.
# --timeout derruba a conexão ociosa e o rclone refaz; _rcl() põe teto de tempo em cada cópia.
RCLONE = [CFG.get("rclone_bin", "rclone"), "--config", str(AQUI / "rclone.conf"), "--timeout", "60s",
          "--contimeout", "20s",
          # 08/11: a chave pública do rclone (projeto 202264815644) dá 403 "Queries per minute" — menos pedidos/s
          "--tpslimit", "4", "--tpslimit-burst", "4"]


def _rcl(args, teto=1500):
    try:
        return subprocess.run(RCLONE + args, timeout=teto).returncode == 0
    except subprocess.TimeoutExpired:
        print("rclone passou do teto:", " ".join(args[:2]))
        return False
BASE = CFG.get("base", "manhwa-drive:colab_recap")
FILA = CFG.get("fila", f"{BASE}/fila")
KAGGLE = CFG.get("kaggle_bin") or str(AQUI / "venv" / "bin" / "kaggle")  # casa-pc1 (Windows): kaggle.exe do venv
EST = AQUI / "estado.json"
FUSO = timezone(timedelta(hours=-3))
# 29/10 dona: "não misture o lugar de saída — se uma conta está saindo da VPS, a outra sai de outra; cada conta fica
# atrelada àquela VPS ou ao PC, nunca se misturam". Cada conta do pool tem "saida" (máquina que fala com o Kaggle por
# ela, PARA SEMPRE); cada máquina roda esta central só com as contas dela (config.json "saida"). Sem "saida" = hermes-prod.
# A hermes-prod é a principal (repassa pedidos, página de status, avisos); as outras ("so_gpus": true) só mantêm as GPUs
# das contas delas e publicam quem está rodando em gpus_<saida>.json no Drive.
SAIDA = CFG.get("saida", "hermes-prod")
# 02/11 dona: "sempre informo qual está verificada — se não informei, não foi verificada": só lança conta com
# "verificada": true no pool (a central não tem como saber antes de lançar; lançar conta sem telefone/banida pelo
# mesmo IP das boas derrubou 16 contas da hermes-prod em 02/11)
# 04/11 dona ("pause a produção até resolver a postagem"): "pausada": true tira a conta da rodada sem mexer no resto
# (as de longo param; a linha de Shorts continua)
CONTAS = [c for c in POOL["contas"] if c.get("saida", "hermes-prod") == SAIDA and c.get("verificada")
          and not c.get("pausada") and not c.get("banida")]  # 10/11: banida também sai (11 contas de 09/11 contavam)
NUM_GPUS = int((POOL.get("gpus_por_saida") or {}).get(SAIDA, POOL.get("gpus", 4)))


def rc(*a):
    r = subprocess.run(RCLONE + list(a), capture_output=True, text=True, timeout=300)
    return r.stdout if r.returncode == 0 else ""


def ler(remoto):
    try:
        return json.loads(rc("cat", remoto) or "null")
    except ValueError:
        return None


def tg(texto):
    t = CFG["telegram"]
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{t['bot_token']}/sendMessage",
                               data=urllib.parse.urlencode({"chat_id": t["chat_id"], "text": texto}).encode(),
                               timeout=30)
    except Exception:
        pass


def _proxy_fixo(conta):
    """01/11 (dona: contas novas "usando o Webshare"): conta com webshare_ip=N fala com o Kaggle SEMPRE pelo IP fixo N
    do Webshare (usuário '-N' de qualquer conta grátis = mesmo IP) — a saída fixa dela. Sem o campo = direto.
    03/11: aceita também proxy_fixo (ex.: 'http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80', pool de IPs exclusivos da rnprmtfo)."""
    if conta.get("proxy_fixo"):
        p = conta["proxy_fixo"].strip()
        return p if p.startswith("http") else "http://" + p
    ip = conta.get("webshare_ip")
    if not ip:
        return None
    import random
    arq = Path(CFG.get("proxies") or r"D:\postador-de-videos\secrets\proxies.txt")
    linhas = [x.strip() for x in arq.read_text(encoding="utf-8").splitlines() if "-rotate:" in x and "rnprmtfo" not in x]
    # 09/11: conta grátis que respondeu 402 (sem banda) fica fora do sorteio por 6 h (WEBSHARE_PULA_402=0 desliga)
    if os.environ.get("WEBSHARE_PULA_402", "1") != "0":
        try:
            ruins = {k for k, t in json.loads(SEM_BANDA.read_text(encoding="utf-8")).items() if time.time() - t < 6 * 3600}
        except (OSError, ValueError):
            ruins = set()
        linhas = [x for x in linhas if x.split("//", 1)[-1].split("-rotate", 1)[0] not in ruins] or linhas
    p = random.choice(linhas).replace("-rotate:", f"-{ip}:")
    return p if p.startswith("http") else "http://" + p


SEM_BANDA = AQUI / "webshare_sem_banda.json"


def _marcar_sem_banda(proxy):
    conta = proxy.split("//", 1)[-1].split("-", 1)[0]
    if not conta or conta.startswith("rnprmtfo"):
        return
    try:
        d = json.loads(SEM_BANDA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    d[conta] = time.time()
    SEM_BANDA.write_text(json.dumps(d), encoding="utf-8")


IP_USO = AQUI / "ip_uso.json"
IP_TROCA_MIN = 60  # minutos mínimos antes de OUTRA conta falar pelo mesmo IP


def _guarda_ip(conta):
    """03/11 — REGRA DA DONA, VALE ATÉ EM TESTE: nunca 2 contas pelo mesmo IP. Em 02/11 uma medição de cota consultou
    as 25 contas da hermes-prod em sequência pelo mesmo IP, de hora em hora, e as 14 contas verificadas foram banidas
    juntas às 21h. Aqui: cada IP lembra a última conta que falou por ele; outra conta pelo mesmo IP só depois de
    IP_TROCA_MIN (revezamento da linha quando a cota acaba). Devolve None = pode; texto = motivo da recusa."""
    ip = _ip_da_conta(conta)
    try:
        uso = json.loads(IP_USO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        uso = {}
    agora = datetime.now(timezone.utc)
    ult = uso.get(ip) or {}
    if ult.get("conta") and ult["conta"] != conta["username"]:
        try:
            passou = (agora - datetime.fromisoformat(ult["em"])).total_seconds() / 60
        except (ValueError, KeyError):
            passou = 0
        if passou < IP_TROCA_MIN:
            return (f"bloqueado: IP {ip} usado por {ult['conta']} há {passou:.0f} min — outra conta só depois de "
                    f"{IP_TROCA_MIN} min (regra: nunca 2 contas no mesmo IP)")
    uso[ip] = {"conta": conta["username"], "em": agora.isoformat(timespec="seconds")}
    IP_USO.write_text(json.dumps(uso, ensure_ascii=False, indent=1), encoding="utf-8")
    return None


def _chave_saida(c):
    """Identidade do IP de saída da conta: 'ws-N' (Webshare grátis -N), 'px-rnprmtfo-N' (proxy fixo) ou 'vps-<saida>'."""
    if c.get("proxy_fixo"):
        p = c["proxy_fixo"].split("//", 1)[-1].split("@", 1)[0].split(":", 1)[0]
        return f"px-{p}"
    if c.get("webshare_ip"):
        return f"ws-{c['webshare_ip']}"
    return f"vps-{c.get('saida', 'hermes-prod')}"


def _saida_queimada(conta):
    """Motivo de recusa ou ''. Conta das VPS (saída compartilhada de propósito, revezada pela _guarda_ip) não entra no
    teste de repetida; só Webshare/proxy fixo, que deviam ser exclusivos."""
    if conta.get("banida"):
        return f"RECUSADO: {conta.get('username')} está marcada como BANIDA — não fala com o Kaggle (nem status)"
    try:
        contas = json.loads((AQUI / "kaggle_pool.json").read_text(encoding="utf-8"))["contas"]
    except (OSError, ValueError, KeyError):
        return ""
    k = _chave_saida(conta)
    if k.startswith("vps-"):
        return ""
    banidas = [c.get("username") for c in contas if c.get("banida") and _chave_saida(c) == k]
    if banidas:
        return (f"RECUSADO: a saída {k} de {conta.get('username')} já foi da conta BANIDA {banidas[0]} — IP queimado, "
                "trocar por um rnprmtfo livre (INCIDENTE_BANIMENTO_02NOV.md, 2º incidente)")
    outras = [c.get("username") for c in contas if c is not conta and not c.get("banida")
              and c.get("username") != conta.get("username") and _chave_saida(c) == k]
    if outras:
        return f"RECUSADO: a saída {k} de {conta.get('username')} é a mesma de {outras[0]} — 1 conta por IP"
    return ""


def _pela_saida(conta, cmd, minusculo=True):
    """Roda cmd falando com o Kaggle COMO a conta e PELA saída dela (direto ou IP fixo do Webshare). Passa SEMPRE pela
    _guarda_ip: 2ª conta no mesmo IP dentro de IP_TROCA_MIN = recusa (não chega a falar com o Kaggle)."""
    # 03/11 dona ("nunca mais pode acontecer de usar o mesmo IP, nem pra consultas rápidas; garanta que nenhum chat faça
    # isso de novo"): conta SEM Webshare só fala com o Kaggle DA MÁQUINA da saída dela. Rodar isto noutra máquina (PC,
    # outra VPS, script de teste) faria a conta sair pelo IP errado — e a _guarda_ip não percebe (ela conhece o IP pelo
    # nome da saída, não pelo IP real). Recusa antes de falar com o Kaggle.
    # 10/11 (2º banimento, 09/11 14:44, 10 contas): conta nova recebeu o webshare_ip de conta BANIDA em 02/11 (IPs 1,4,5,6)
    # e o Kaggle ligou as duas pelo histórico do IP. Travas ANTES de qualquer contato (KAGGLE_TRAVA_IP_QUEIMADO=0 desliga):
    # 1) conta banida nunca fala com o Kaggle (nem status); 2) saída que já foi de conta banida = queimada; 3) saída
    # repetida por 2 contas vivas no pool = recusa as duas até a dona separar.
    if os.environ.get("KAGGLE_TRAVA_IP_QUEIMADO", "1") != "0":
        motivo = _saida_queimada(conta)
        if motivo:
            print(motivo, flush=True)
            return motivo.lower()
    if not conta.get("webshare_ip") and not conta.get("proxy_fixo") and conta.get("saida", "hermes-prod") != SAIDA:
        motivo = (f"RECUSADO: {conta['username']} é da saída {conta.get('saida')} e esta máquina é {SAIDA} — cada "
                  "conta só fala pelo IP dela (comum\\kaggle_gerente\\INCIDENTE_BANIMENTO_02NOV.md)")
        print(motivo, flush=True)
        return motivo.lower()
    motivo = _guarda_ip(conta)
    if motivo:
        print(motivo, flush=True)
        return motivo
    env = {**os.environ, "KAGGLE_USERNAME": conta["username"],
           "KAGGLE_CONFIG_DIR": str(AQUI / "kcfg" / conta["username"])}
    env.pop("KAGGLE_API_TOKEN", None)
    env.pop("KAGGLE_KEY", None)
    if conta.get("token"):  # 03/11: contas novas vêm com o token novo do Kaggle (KGAT_...), não a chave antiga
        env["KAGGLE_API_TOKEN"] = conta["token"]
        # a CLI com KAGGLE_CONFIG_DIR próprio procura o token no arquivo access_token dessa pasta (como o Kaggle manda:
        # "echo KGAT_... > ~/.kaggle/access_token") — a emerson2033 tinha o push falhando calado só com a variável
        tok = AQUI / "kcfg" / conta["username"] / "access_token"
        tok.parent.mkdir(parents=True, exist_ok=True)
        if not tok.exists() or tok.read_text(encoding="utf-8").strip() != conta["token"]:
            tok.write_text(conta["token"] + "\n", encoding="utf-8")
            try:
                os.chmod(tok, 0o600)
            except OSError:
                pass
    else:
        env["KAGGLE_KEY"] = conta["key"]
    (AQUI / "kcfg" / conta["username"]).mkdir(parents=True, exist_ok=True)
    # 02/11 20h50: no Windows a CLI do Kaggle soltou um byte cp1252 (0x97) — o text=True quebrou a leitura, stdout
    # veio None e a central da casa caía inteira a cada volta (sem repor GPU por horas). utf-8 + replace = nunca quebra.
    txt = dict(capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if not conta.get("webshare_ip") and not conta.get("proxy_fixo"):
        r = subprocess.run(cmd, timeout=300, **txt)
        saida = (r.stdout or "") + (r.stderr or "")
        return saida.lower() if minusculo else saida
    # 02/11: conta grátis do Webshare travou 300 s e derrubou a rodada inteira — tenta outra conta no MESMO IP
    ultimo = ""
    for _ in range(3):
        env.update(HTTPS_PROXY=_proxy_fixo(conta), HTTP_PROXY=env.get("HTTPS_PROXY"))
        env["HTTP_PROXY"] = env["HTTPS_PROXY"]
        try:
            r = subprocess.run(cmd, timeout=60, **txt)  # 09/11: era 120 s x 3 — volta da central levava ~2 h
        except subprocess.TimeoutExpired:
            ultimo = "timeout 60 s"
            continue
        saida = (r.stdout or "") + (r.stderr or "")
        ultimo = " ".join(saida.split())[-220:]
        # "COTA=" na saída = respondeu (24073.0 s contém "407" e era lido como erro de proxy — revisão sonnet 02/11)
        # 09/11: conta grátis do Webshare sem banda responde "402 Payment Required" e a CLI do Kaggle mostra
        # "authentication required" — 10 contas ficaram sem ver o status dos longos. Tenta outra conta grátis no
        # MESMO IP -N (mesma saída; regra 1 conta = 1 IP mantida).
        ruim = "402" in saida or "authentication required" in saida.lower()
        # 10/11: só o 402 do PROXY ("Payment Required" = conta grátis sem banda) marca a conta do Webshare. O
        # "authentication required" é a CLI do Kaggle (token recusado / conta BANIDA) — marcava as 96 contas grátis
        # como sem banda e tirava do ar as contas Kaggle que saem por elas.
        if conta.get("webshare_ip") and ("402 payment required" in saida.lower() or
                                         ("402" in saida and "authentication required" not in saida.lower())):
            _marcar_sem_banda(env.get("HTTPS_PROXY", ""))
        if "COTA=" in (r.stdout or "") or ("proxy" not in saida.lower() and "407" not in saida and not ruim):
            return saida.lower() if minusculo else saida
    # 09/11: grava o motivo real (antes só 'sem resposta' — 10 contas paradas sem saber por quê)
    print(f"  [saída {conta.get('username')}] 3 tentativas falharam; última: {ultimo}", flush=True)
    return "proxy webshare sem resposta"


def kg(conta, *a):
    return _pela_saida(conta, [KAGGLE, *a])


def _erro_auth(saida):
    s = (saida or "").lower()
    return "authentication required" in s or "401" in s and "unauthorized" in s or "permission 'kernels.get' was denied" in s


# ───────── Cota de GPU da semana (02/11, dona: "controle no painel pra saber quantas contas ainda tem"). A API oficial
# (kagglesdk GetAcceleratorQuotaStatistics) responde com a chave da conta, sem navegador; chamada pela saída da conta.
# Achado 02/11: conta nova tem 6 h/semana (revolutionemerson), não 30 — por isso a cota real decide quem lança.
PY = str(Path(KAGGLE).parent / ("python.exe" if os.name == "nt" else "python"))
COTA_CADA_MIN = 60
COTA_MIN_H = 1.5  # menos que isso livre: não lança (com 0,75 h a sessão era 30 min e a linha de Shorts nem começava)
_PY_COTA = (
    "import json,os\n"
    "from kagglesdk import KaggleClient\n"
    "from kagglesdk.kernels.types.kernels_api_service import ApiGetAcceleratorQuotaStatisticsRequest\n"
    "_t = os.environ.get('KAGGLE_API_TOKEN')\n"  # 03/11: token novo (KGAT_) ou chave antiga
    "with (KaggleClient(api_token=_t) if _t else\n"
    "      KaggleClient(username=os.environ['KAGGLE_USERNAME'], password=os.environ['KAGGLE_KEY'])) as k:\n"
    "    r = k.kernels.kernels_api_client.get_accelerator_quota_statistics(ApiGetAcceleratorQuotaStatisticsRequest())\n"
    # NÃO usar r.to_dict(): o TimeDeltaSerializer do kagglesdk usa timedelta.seconds e PERDE OS DIAS (30 h = 1 dia + 6 h
    # virava "21600s" = 6 h; issue #73 do kaggle-sdk-python). total_seconds() direto no objeto.
    "g = r.gpu_quota\n"
    "print('COTA=' + json.dumps({'gpuQuota': {'timeUsed': g.time_used.total_seconds() if g and g.time_used else 0,\n"
    "    'totalTimeAllowed': g.total_time_allowed.total_seconds() if g and g.total_time_allowed else 0},\n"
    "    'quotaRefreshTime': r.quota_refresh_time.isoformat() if r.quota_refresh_time else ''}))\n")


def _horas(x):
    import re
    m = re.match(r"\d+(\.\d+)?", str(x or "0"))  # vem "14738.545.0s" às vezes
    return round(float(m.group()) / 3600, 2) if m else 0.0


def _cota(conta):
    for _ in range(2):  # 02/11: SSLError pelo IP fixo do Webshare deixou a conta "sem medida" e ela foi lançada com 0 h
        out = _pela_saida(conta, [PY, "-c", _PY_COTA], minusculo=False)
        linha = next((l for l in out.splitlines() if l.startswith("COTA=")), None)
        if linha:
            break
    if not linha:
        return {"erro": out.strip().splitlines()[-1][:160] if out.strip() else "sem resposta"}
    d = json.loads(linha[5:])
    g = d.get("gpuQuota") or {}
    total, usadas = _horas(g.get("totalTimeAllowed")), _horas(g.get("timeUsed"))
    if not total:  # resposta sem cota = não sabemos (não marcar "sem cota" até sexta)
        return {"erro": "API respondeu sem totalTimeAllowed"}
    return {"total": total, "usadas": usadas, "livre": round(max(total - usadas, 0), 2),
            "renova": d.get("quotaRefreshTime", "")[:19], "visto": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def _medir_uma(est, c):
    cotas = est.setdefault("cotas", {})
    try:
        r = _cota(c)
    except Exception as e:  # noqa: BLE001 — medir nunca derruba a central
        r = {"erro": f"{type(e).__name__}: {str(e)[:120]}"}
    if "erro" in r:  # guarda o erro e o último valor bom
        cotas[c["username"]] = {**{k: v for k, v in cotas.get(c["username"], {}).items() if k != "erro"}, **r,
                                "tentado": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    else:
        cotas[c["username"]] = r


def medir_cotas(est, forcar=False, teto_s=180):
    """Mede a conta cuja medida tem mais de COTA_CADA_MIN, a mais velha primeiro, até teto_s por volta (revisão sonnet
    02/11: com o Webshare lento, medir todas de uma vez segurava a central > 1 h sem repor GPU)."""
    if est.get("cotas_v") != 2:  # medidas antes de 02/11 12:30 vinham com o bug dos dias (30 h lidas como 6): refaz já
        est["cotas"], est["cotas_v"] = {}, 2
    agora = datetime.now(timezone.utc)
    cotas = est.setdefault("cotas", {})

    def idade(c):
        q = cotas.get(c["username"]) or {}
        t = q.get("tentado") or q.get("visto")
        return (agora - datetime.fromisoformat(t)).total_seconds() if t else 1e12

    fila = sorted((c for c in CONTAS if forcar or idade(c) >= COTA_CADA_MIN * 60), key=idade, reverse=True)
    t0 = time.time()
    for c in fila:
        if not forcar and time.time() - t0 > teto_s:
            break
        _medir_uma(est, c)
    est["cotas_em"] = agora.isoformat(timespec="seconds")


def _livre_h(est, user, agora):
    """Horas de GPU livres na semana (None = não sabemos). Passou da renovação = cota cheia de novo."""
    c = (est.get("cotas") or {}).get(user) or {}
    if "livre" not in c:
        return None
    try:
        if c.get("renova") and agora >= datetime.fromisoformat(c["renova"].replace("Z", "")).replace(tzinfo=timezone.utc):
            return c.get("total")
    except ValueError:
        pass
    return c["livre"]


def _kernel_titulo(conta):
    # 03/11: conta nova (token KGAT_) — o push de "recap-longo" dava 409 (conflito) sem o notebook existir; nome novo
    return "recap-trabalho" if conta.get("token") else "recap-longo"


def _kernel_id(conta):
    return f"{conta['username']}/{_kernel_titulo(conta)}"


def _dataset_id(conta):
    return f"{conta['username']}/recap-worker-conf"


def _garantir_dataset(conta, est):
    """Cria o dataset privado com rclone.conf na conta se não existir ainda. Marca no estado pra não repetir."""
    chave = f"ds2_{conta['username']}"  # 03/11: marca nova (a ds_ antiga ficava True mesmo com a criação falhando)
    if est.get(chave):
        return True
    d = AQUI / "ds_tmp" / conta["username"]
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    partes = []
    for remoto in ("manhwa-drive",):
        txt = subprocess.run(RCLONE + ["config", "show", remoto],
                             capture_output=True, text=True).stdout
        if txt.strip():
            partes.append(txt.strip())
    if not partes:
        return False
    (d / "rclone.conf").write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    ds = _dataset_id(conta)
    (d / "dataset-metadata.json").write_text(json.dumps(
        {"title": "recap-worker-conf", "id": ds, "licenses": [{"name": "CC0-1.0"}]}), encoding="utf-8")
    r = kg(conta, "datasets", "create", "-p", str(d))
    print(f"dataset {conta['username']}: {' '.join(str(r).split())[-200:]}", flush=True)  # 03/11: falha não era vista
    if "already" in r:
        kg(conta, "datasets", "version", "-p", str(d), "-m", "rclone.conf atualizado")
    shutil.rmtree(d, ignore_errors=True)
    ok = any(x in str(r).lower() for x in ("success", "already", "created", "your private dataset"))
    if ok:  # 03/11: só marca feito com confirmação — antes marcava mesmo com erro e nunca mais tentava
        est[chave] = True
    return ok


def _lancar_conta(conta, est, papel=None):
    """Lança o kernel recap-longo nesta conta Kaggle. papel = o trabalho que esta sessão faz (pode ser diferente do papel
    da linha quando outra linha assume o conteúdo de uma linha sem contas)."""
    # 03/11: conta NOVA (token KGAT_) não usa dataset — a criação dele pela CLI nova falha ("dataset slugs and hashlink
    # are all null") e o push que aponta pra ele dá 409. O rclone.conf vai DENTRO do script (kernel privado, mesma
    # exposição do dataset privado) e o trabalhador lê pelo RCLONE_CONF.
    conf_embutido = None
    if conta.get("token"):
        txt = subprocess.run(RCLONE + ["config", "show", "manhwa-drive"], capture_output=True, text=True).stdout.strip()
        if not txt:
            print(f"{conta['username']}: rclone.conf vazio — não lança", flush=True)
            return None
        conf_embutido = base64.b64encode((txt + "\n").encode("utf-8")).decode()
    elif not _garantir_dataset(conta, est):
        # 03/11: sem o dataset (rclone.conf) o push do kernel dá 409 e a sessão não existe — não lança
        print(f"{conta['username']}: dataset não ficou pronto — não lança agora", flush=True)
        return None
    d = AQUI / "kernel_tmp" / conta["username"]
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    trab = CFG["kaggle"].get("trabalhador", "kaggle_trabalhador.py")
    # 26/10: o Kaggle NÃO põe KAGGLE_USERNAME no kernel — as 4 GPUs se chamavam "kaggle" e podiam pegar o mesmo pedido.
    # O nome da conta vai gravado no topo do script (antes dos imports do trabalhador lerem TRAB_NOME).
    codigo = (AQUI / trab).read_text(encoding="utf-8")
    topo = f"import os\nos.environ['TRAB_NOME'] = {conta['username']!r}\n"
    _medir_uma(est, conta)  # cota de agora (a da última hora pode ter 1 h a mais do que sobrou — revisão sonnet 02/11)
    erro_cota = str(((est.get("cotas") or {}).get(conta["username"]) or {}).get("erro", ""))
    if "401" in erro_cota or "bloqueado:" in erro_cota:  # chave recusada ou IP ocupado por outra conta: não lança
        # 02/11 21h: chave recusada pelo Kaggle — push daria o mesmo 401 e a GPU ficaria marcada como "lançada" à toa
        # 10/11: sem marcar, o _escolher pegava A MESMA conta com 401 em toda volta e a fila travava nela (5 contas
        # boas do longo nunca eram tentadas). 401 = descanso de RUIM_TTL_H (pode ser banida: dona confere).
        if "401" in erro_cota:
            est.setdefault("ruins", {})[conta["username"]] = {
                "motivo": "401 ao medir a cota (token recusado / banida?)",
                "em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            print(f"{conta['username']}: 401 na cota — descansa {RUIM_TTL_H} h, próxima conta", flush=True)
        shutil.rmtree(d, ignore_errors=True)
        return None
    livre = _livre_h(est, conta["username"], datetime.now(timezone.utc))
    if livre is not None and livre < COTA_MIN_H:
        shutil.rmtree(d, ignore_errors=True)
        return None
    if conf_embutido:
        topo += ("import base64 as _b64\nfrom pathlib import Path as _P\n"
                 f"_P('/tmp/rclone_in.conf').write_bytes(_b64.b64decode({conf_embutido!r}))\n"
                 "os.environ['RCLONE_CONF'] = '/tmp/rclone_in.conf'\n")
    topo += f"os.environ['TRAB_PAPEL'] = {(papel or _papel(conta))!r}\n"  # 02/11: longo OU curto, nunca os dois
    if livre:  # 02/11: o trabalhador não pega longo que a cota da semana corta no meio (conta nova = 6 h)
        topo += f"os.environ['TRAB_COTA_H'] = {str(livre)!r}\n"
    (d / trab).write_text(topo + codigo, encoding="utf-8")
    kid = _kernel_id(conta)
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": kid, "title": _kernel_titulo(conta), "code_file": trab,
         "language": "python", "kernel_type": "script", "is_private": True,
         "enable_gpu": bool(CFG["kaggle"].get("gpu", True)),
         "enable_internet": True, "dataset_sources": [] if conf_embutido else [_dataset_id(conta)],
         "competition_sources": [], "kernel_sources": []}), encoding="utf-8")
    rp = kg(conta, "kernels", "push", "-p", str(d))
    # 03/11: a emerson2033 (token novo) ficou "lançada" com o notebook inexistente — o push falhava calado
    print(f"push {conta['username']}: {' '.join(str(rp).split())[-200:]}", flush=True)
    shutil.rmtree(d, ignore_errors=True)
    return kid


def manter_baixador(username):
    """03/11: o BAIXADOR do Kaggle (colab\\_kaggle\\baixador\\kaggle_baixador.py: baixa vídeo + legenda do YouTube pelo IP do
    Kaggle e devolve pelo Drive manhwa-drive:baixador) morava na emersonjosiel — banida 02/11 — e todo download voltou pro
    IP de casa (26 bloqueios/estouros em 03/11). Agora numa conta viva, SEMPRE pela saída dela (kg -> _pela_saida ->
    _guarda_ip). Relança se não estiver rodando. Cron da VPS da saída: vps_central.py baixador <conta>."""
    conta = _conta_por_user(username)
    if not conta or conta.get("banida"):
        print(f"baixador: conta {username} fora do pool ou banida", flush=True)
        return
    kid = f"{username}/baixador-yt"
    st = kg(conta, "kernels", "status", kid)
    if "running" in st or "queued" in st:
        print(f"{datetime.now():%d/%m %H:%M} baixador {kid}: rodando", flush=True)
        return
    if "bloqueado" in st or "recusado" in st:
        print(f"{datetime.now():%d/%m %H:%M} baixador {kid}: {st[:200]}", flush=True)
        return
    codigo = (AQUI / "kaggle_baixador.py").read_text(encoding="utf-8")
    topo = "import os\n"
    if conta.get("token"):
        txt = subprocess.run(RCLONE + ["config", "show", "manhwa-drive"], capture_output=True, text=True).stdout.strip()
        if not txt:
            print("baixador: rclone.conf vazio — não lança", flush=True)
            return
        b = base64.b64encode((txt + "\n").encode("utf-8")).decode()
        topo += ("import base64 as _b64\nfrom pathlib import Path as _P\n"
                 f"_P('/tmp/rclone_in.conf').write_bytes(_b64.b64decode({b!r}))\n"
                 "os.environ['RCLONE_CONF'] = '/tmp/rclone_in.conf'\n")
    d = AQUI / "kernel_tmp" / f"{username}_baixador"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    (d / "kaggle_baixador.py").write_text(topo + codigo, encoding="utf-8")
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": kid, "title": "baixador-yt", "code_file": "kaggle_baixador.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": False, "enable_internet": True,
         "dataset_sources": [] if conta.get("token") else [_dataset_id(conta)], "competition_sources": [],
         "kernel_sources": []}), encoding="utf-8")
    rp = kg(conta, "kernels", "push", "-p", str(d))
    shutil.rmtree(d, ignore_errors=True)
    print(f"{datetime.now():%d/%m %H:%M} baixador {kid}: parado ({st.strip()[:80]}) — push: "
          f"{' '.join(str(rp).split())[-200:]}", flush=True)


def _conta_por_user(username):
    for c in CONTAS:
        if c["username"] == username:
            return c
    return None


def _deu_sinal_desde(username, quando_iso):
    """A conta gravou vivo_<username>.json depois de quando_iso? O trabalhador só grava se o kernel rodou de verdade
    (com internet). Sem sinal depois de lançar = kernel caiu no setup = conta sem internet/GPU (telefone não verificado)."""
    if not quando_iso:
        return True
    v = ler(f"{BASE}/vivo_{username}.json")
    if not v or not v.get("em"):
        return False
    try:
        return datetime.fromisoformat(v["em"]) >= datetime.fromisoformat(quando_iso)
    except ValueError:
        return True


RUIM_TTL_H = 12  # re-tenta a conta depois disso (dona verifica o telefone aos poucos; em 12 h a conta volta sozinha)


def _esta_ruim(est, user, agora):
    r = est.get("ruins", {}).get(user)
    if not r:
        return False
    try:
        # 02/11 dona ("por que tentou acessar elas se não estavam verificadas?"): 16 contas da hermes-prod caíram
        # juntas ("sem internet" = telefone não verificado OU banida). Re-tentar a cada 12 h era bater na porta de conta
        # banida pelo mesmo IP das que funcionam: "sem internet" só volta com liberação manual (python vps_central.py
        # liberar <user>). Outros motivos seguem com a re-tentativa de RUIM_TTL_H.
        if "sem internet" in str(r.get("motivo", "")):
            return True
        return (agora - datetime.fromisoformat(r["em"])).total_seconds() / 3600 < RUIM_TTL_H
    except (ValueError, TypeError, KeyError):
        return True


def _ip_da_conta(c):
    if c.get("webshare_ip"):
        return f"webshare-{c['webshare_ip']}"
    if c.get("proxy_fixo"):
        u = c["proxy_fixo"].split("://")[-1].split(":")[0]
        return f"proxy-{u}"
    return f"direto-{c.get('saida', 'hermes-prod')}"


def _papel(c):
    """02/11 22h dona ("um método de divisão pra os vídeos pequenos e longos não se esbarrarem nem competirem pelo mesmo
    Kaggle"; "13 IPs = 13 linhas de produção, 3 ou 4 contas em cada linha pra revezar"): o papel é da LINHA (IP) —
    pool["linhas"]["webshare-3"] = "curto". Toda conta posta naquele IP herda o papel; 1 sessão por linha por vez (o
    _escolher já não deixa 2 no mesmo IP) e, quando a cota de uma acaba, a próxima da mesma linha assume. "papel" na
    própria conta ainda vale (força); sem nada = longo."""
    return c.get("papel") or (POOL.get("linhas") or {}).get(_ip_da_conta(c)) or "longo"


def _candidatas(est, em_uso, agora, papel=None):
    # 02/11 dona (16 contas caíram com 4 sessões no mesmo IP): NUNCA 2 sessões no mesmo IP — IP = Webshare fixo da conta
    # ou, sem ele, o da saída (VPS/casa). Cada IP do Webshare é de UMA conta só no pool.
    ips_em_uso = {_ip_da_conta(c) for c in (_conta_por_user(u) for u in em_uso) if c}
    # 10/11: conta com saída queimada (IP que já foi de conta banida) nunca é candidata — ocupava vaga sem poder falar
    # com o Kaggle (animescomia em ws-3, que foi da emerson2029)
    queimar = os.environ.get("KAGGLE_TRAVA_IP_QUEIMADO", "1") != "0"
    return [c for c in CONTAS if not _esta_ruim(est, c["username"], agora) and c["username"] not in em_uso
            and not (queimar and _saida_queimada(c))
            and _ip_da_conta(c) not in ips_em_uso and (papel is None or _papel(c) == papel)
            and (_livre_h(est, c["username"], agora) is None or _livre_h(est, c["username"], agora) >= COTA_MIN_H)]


def _linhas_livres(est, em_uso, agora, papel):
    """Quantas LINHAS (IPs) deste papel ainda têm conta pronta pra lançar."""
    return len({_ip_da_conta(c) for c in _candidatas(est, em_uso, agora, papel)})


def _escolher(est, em_uso, agora, papel=None):
    """Próxima conta a lançar: não marcada ruim (ou marca já expirada), não em uso por outra GPU, a de uso mais antigo
    primeiro (rodízio justo; nunca usadas têm prioridade). papel = só contas desse papel. None se não há nenhuma."""
    uso = est.get("ultimo_uso", {})
    cand = _candidatas(est, em_uso, agora, papel)
    if not cand:
        return None
    return min(cand, key=lambda c: uso.get(c["username"], ""))


def _trabalho_pendente(papel=None):
    """02/11: pedidos livres nas filas que o Kaggle atende (longo + Shorts + comentários). GPU lançada sem trabalho gasta
    a cota da semana à toa. papel "longo" = só a fila do longo; "curto" = Shorts + comentários. None = não deu pra
    ler o Drive (lança como antes)."""
    total = 0
    # 10/11: fila_treino (retreino de voz) também é trabalho do "curto" — sem isso a central não lançava conta pro treino
    filas = {"longo": (FILA,), "curto": (f"{BASE}/fila_shorts", f"{BASE}/fila_comentarios", f"{BASE}/fila_treino"),
             "treino": (f"{BASE}/fila_treino",)}.get(
        papel, (FILA, f"{BASE}/fila_shorts", f"{BASE}/fila_comentarios", f"{BASE}/fila_treino"))
    for fila in filas:
        try:
            r = subprocess.run(RCLONE + ["lsjson", "-R", "--files-only", "--max-depth", "2", fila],
                               capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            return None
        if r.returncode != 0:
            if "directory not found" in r.stderr.lower():
                continue
            return None
        pastas = {}
        # marca de sessão morta conta como livre (o trabalhador solta ela): longo > 12,5 h, Short/comentário > 2 h
        limite = 45000 if fila == FILA else 7200
        agora = datetime.now(timezone.utc)
        for i in json.loads(r.stdout or "[]"):
            if "/" in i["Path"]:
                p, n = i["Path"].split("/", 1)
                if n.startswith("em_andamento"):
                    try:  # ModTime vem com fuso (VPS em -03) e às vezes com 9 casas de fração
                        s = i["ModTime"].replace("Z", "+00:00")
                        s = s[:19] + s[s.find("+", 19) if "+" in s[19:] else s.rfind("-"):] if len(s) > 25 else s
                        mt = datetime.fromisoformat(s).astimezone(timezone.utc)
                        if (agora - mt).total_seconds() > limite:
                            continue
                    except (ValueError, KeyError):
                        pass
                pastas.setdefault(p, set()).add(n)
        total += sum(1 for a in pastas.values() if "pedido.json" in a and not (
            {"pronto.json", "erro.json"} & a or any(x.startswith("em_andamento") for x in a))
            and ("source.mp4" in a or not fila.endswith("fila_shorts")))  # Short ainda subindo não conta
    return total


def contas_resumo(est, agora):
    """Uma linha por conta desta saída, pro painel: estado, cota da semana e por onde fala com o Kaggle."""
    rodando = {g.get("conta") for g in est.get("gpus", []) if g.get("conta")}
    out = []
    for c in CONTAS:
        u = c["username"]
        q = (est.get("cotas") or {}).get(u) or {}
        r = (est.get("ruins") or {}).get(u)
        # cota acabada vem antes de "ruim": 02/11 staging/bloqueio/revolutionemerson estavam "sem internet" mas tinham
        # gasto as 30 h (a sessão morre logo no começo sem cota e a central lia como telefone não verificado)
        estado = ("rodando" if u in rodando else
                  "sem cota" if "livre" in q and (_livre_h(est, u, agora) or 0) < COTA_MIN_H else
                  "ruim" if _esta_ruim(est, u, agora) else "livre")
        out.append({"conta": u, "saida": SAIDA, "webshare_ip": c.get("webshare_ip"), "estado": estado,
                    "motivo": (r or {}).get("motivo") if estado == "ruim" else
                    "cota da semana acabou (volta sexta 21h)" if estado == "sem cota" else None,
                    "livre_h": _livre_h(est, u, agora), "total_h": q.get("total"), "usadas_h": q.get("usadas"),
                    "renova": q.get("renova"), "cota_visto": q.get("visto"), "cota_erro": q.get("erro")})
    return out


def manter_slots(est):
    """Mantém NUM_GPUS kernels rodando, puxando contas do pool plano. Checa a conta ativa de cada GPU; se o kernel caiu
    em ERRO logo após o lançamento sem nunca dar sinal de vida (telefone não verificado = sem internet/GPU), marca a
    conta como ruim e nunca mais a tenta. Rotaciona para a próxima conta verificada e livre. Retorna resumo por GPU."""
    est.setdefault("ruins", {})
    est.setdefault("ultimo_uso", {})
    gpus = est.setdefault("gpus", [])
    while len(gpus) < NUM_GPUS:
        gpus.append({"conta": None, "lancado_em": None})
    agora = datetime.now(timezone.utc)
    resumos = []
    # 1ª passada: checa quem está ativo, libera quem caiu/terminou, marca ruins
    for g in gpus[:NUM_GPUS]:
        user = g.get("conta")
        if not user:
            continue
        conta = _conta_por_user(user)
        if not conta:
            # 02/11 22h: conta saiu do CONTAS (não verificada / outra saída) mas ficou presa na vaga — 3 de 7 GPUs da
            # hermes-prod seguravam contas "sem internet" e nenhuma conta boa entrava. Solta a vaga.
            g["conta"], g["lancado_em"] = None, None
            g.pop("papel", None)
            continue
        s = kg(conta, "kernels", "status", _kernel_id(conta))
        if "kaggle_api_token=" in s or "api token file" in s:
            # 09/11: a CLI 2.2.5 valida o token KGAT numa chamada extra; quando ela falha pelo proxy, devolve a AJUDA do
            # token (parece "sem token"). Intermitente: tenta 1x de novo (mesma conta, mesmo IP).
            s = kg(conta, "kernels", "status", _kernel_id(conta))
        # 03/11: o status que a central JÁ consulta vai pro log (diagnóstico sem ninguém falar com o Kaggle por fora)
        print(f"status {user} (lançada {str(g.get('lancado_em'))[11:16]}): {' '.join(str(s).split())[-160:]}",
              flush=True)
        if s == "proxy webshare sem resposta" or s.startswith("bloqueado:"):  # não sabemos: não solta a GPU
            # 10/11: 11 contas com token recusado pelo Kaggle (desde 09/11 14:40) ficavam PRESAS nas 14 vagas pra
            # sempre — nenhuma conta boa entrava. Sem resposta há > 3 h desde o lançamento: solta a vaga e põe a
            # conta de descanso (est['ruins'], mesma regra das contas ruins: volta sozinha depois).
            lanc_sr = g.get("lancado_em")
            if s == "proxy webshare sem resposta" and lanc_sr and \
                    (agora - datetime.fromisoformat(lanc_sr)).total_seconds() > 3 * 3600:
                est.setdefault("ruins", {})[user] = {"motivo": "status sem resposta > 3 h (token recusado?)",
                                                     "em": agora.isoformat(timespec="seconds")}
                print(f"{user}: sem resposta há > 3 h — solta a vaga e descansa a conta", flush=True)
                g["conta"], g["lancado_em"] = None, None
                g.pop("papel", None)
            continue
        # 02/11 21h: TODAS as contas passaram a dar 401 ("authentication required" / "permission kernels.get denied")
        # ao mesmo tempo. A central lia isso como "kernel acabou", soltava a GPU e relançava por cima — e marcava conta
        # boa como ruim. Erro de autenticação = não sabemos o estado: mantém a GPU como está e avisa 1x.
        lanc = g.get("lancado_em")
        if ("slug" in s or "not found" in s) and lanc and not _deu_sinal_desde(user, lanc) and \
                (agora - datetime.fromisoformat(lanc)).total_seconds() > 600:
            # 03/11: o notebook NEM EXISTE (push falhou) — a emerson2033 ficou 3 h presa na vaga porque esta resposta
            # ("permission kernels.get denied ... wrong kernel slug") caía no _erro_auth e a vaga nunca soltava
            print(f"{user}: notebook não existe 10 min depois do lançamento — push falhou; solta a vaga", flush=True)
            g["conta"] = None
            g["lancado_em"] = None
            g.pop("papel", None)
            continue
        if _erro_auth(s):
            est.setdefault("auth_401", {})[user] = agora.isoformat(timespec="seconds")
            continue
        if "queued" in s and g.get("lancado_em") and \
                (agora - datetime.fromisoformat(g["lancado_em"])).total_seconds() > \
                float(os.environ.get("KAGGLE_QUEUED_MAX_H", "6")) * 3600:
            # 10/11: inovare/inovareee/mundosolar1995 ficaram 21 h 'queued' (o Kaggle não dá GPU pra conta nova) segurando
            # 3 das vagas. Fila > KAGGLE_QUEUED_MAX_H h: solta a vaga e descansa a conta (RUIM_TTL_H); o kernel em fila
            # fica lá — se o Kaggle der a GPU depois, o trabalhador pega pedido normalmente.
            est.setdefault("ruins", {})[user] = {"motivo": "queued > 6 h (Kaggle não dá GPU)",
                                                 "em": agora.isoformat(timespec="seconds")}
            print(f"{user}: queued há mais de 6 h — solta a vaga", flush=True)
            g["conta"], g["lancado_em"] = None, None
            g.pop("papel", None)
            continue
        if "running" in s or "queued" in s:
            est["ultimo_uso"][user] = agora.isoformat(timespec="seconds")
            continue
        if s.startswith("recusado:"):  # 10/11: saída queimada/repetida — não vai falar com o Kaggle: solta a vaga já
            print(f"{user}: {s[:90]} — solta a vaga", flush=True)
            g["conta"], g["lancado_em"] = None, None
            g.pop("papel", None)
            continue
        if not any(x in s for x in ("complete", "error", "cancel")):
            # 09/11: resposta que não diz o estado (ajuda do token, timeout, texto estranho) caía no 'GPU livre' lá
            # embaixo e a central RELANÇAVA por cima do kernel que ainda rodava (10 contas assim desde 14:44, Kaggle
            # parado em 24). Não sabemos = mantém a vaga, igual ao 'proxy sem resposta'.
            est.setdefault("status_ilegivel", {})[user] = agora.isoformat(timespec="seconds")
            lanc_il = g.get("lancado_em")
            # trava de segurança: ilegível por > 3 h desde o lançamento = solta a vaga (comportamento antigo)
            if not lanc_il or (agora - datetime.fromisoformat(lanc_il)).total_seconds() < 3 * 3600:
                continue
        if "error" in s:
            lancado = g.get("lancado_em")
            if lancado and not _deu_sinal_desde(user, lancado):
                if (agora - datetime.fromisoformat(lancado)).total_seconds() / 60 > 3:
                    motivo = "kernel sem internet (telefone não verificado?)"
                    if conta.get("token"):
                        # 03/11: conta nova — antes de culpar o telefone, o LOG do kernel (mesma conta, mesmo IP dela)
                        saida = AQUI / "kernel_out" / user
                        shutil.rmtree(saida, ignore_errors=True)
                        saida.mkdir(parents=True, exist_ok=True)
                        kg(conta, "kernels", "output", _kernel_id(conta), "-p", str(saida))
                        txt = " ".join(" ".join(p.read_text(encoding="utf-8", errors="replace").split())
                                       for p in saida.glob("*.log"))
                        print(f"log do kernel {user}: {txt[-900:]}", flush=True)
                        if txt and not any(x in txt.lower() for x in ("internet", "name resolution",
                                                                      "temporary failure", "network is unreachable")):
                            motivo = "erro no notebook (ver 'log do kernel' no central.log)"
                    est["ruins"][user] = {"motivo": motivo, "em": agora.isoformat(timespec="seconds")}
            else:  # deu sinal de vida e depois deu erro = erro de render, não é problema da conta
                est.get("ruins", {}).pop(user, None)
        elif "complete" in s:
            lancado = g.get("lancado_em")
            if lancado and not _deu_sinal_desde(user, lancado):
                # 27/10: aulacomia/e4487017/emersonjosiel terminavam logo depois de lançar, sem 1 sinal de vida, e a
                # central relançava a cada 5 min — cota semanal de GPU do Kaggle (30 h) acabou. Descansa e testa depois.
                est["ruins"][user] = {"motivo": "sessão acaba sem trabalhar (cota de GPU da semana?)",
                                      "em": agora.isoformat(timespec="seconds")}
            else:  # sessão acabou de boa: conta é válida, limpa marca antiga
                est.get("ruins", {}).pop(user, None)
        g["conta"] = None  # complete, error ou sumiu: GPU livre pra próxima
        g["lancado_em"] = None
        g.pop("papel", None)
    # 2ª passada: preenche GPUs livres com a próxima conta disponível — só se houver trabalho pra ela (02/11). Kernel
    # lançado há < 10 min ainda está se preparando e vai pegar 1 pedido: desconta (depois disso ele já marcou o
    # pedido, que sai da contagem sozinho — descontar mais seria em dobro).
    # 02/11 22h (divisão longo/curto): trabalho pendente contado POR PAPEL; GPU vaga recebe conta do papel que tem
    # trabalho — longo primeiro (leva horas, é o que mais atrasa), depois curto. Um papel nunca usa conta do outro.
    # 02/11 dona: "se tem 3 pra curto, usar as 3 ao mesmo tempo" e "se as contas de uma linha acabarem, a linha para até
    # ter contas novas e outra linha assume aquele conteúdo". Cada vaga guarda o papel que está fazendo (g["papel"]).
    # Meta de cada papel = nº de linhas dele (curto 3, longo 10). Ordem: papel com mais FALTA em relação à meta e com
    # trabalho na fila vai primeiro; conta da própria linha; sem conta na linha dele → empresta conta de outra linha
    # (1 IP = 1 sessão continua valendo) e lança com o papel do TRABALHO.
    # meta = nº de LINHAS (IPs) de cada papel NESTA saída (casa: 3 longo + 1 curto; prod: 5 longo + 2 curto)
    meta = {p: len({_ip_da_conta(c) for c in CONTAS if _papel(c) == p}) for p in ("longo", "curto")}
    pend = {}
    if any(not g.get("conta") for g in gpus[:NUM_GPUS]):
        for papel in ("longo", "curto"):
            n = _trabalho_pendente(papel)
            if n is not None:
                n -= sum(1 for g in gpus[:NUM_GPUS] if g.get("conta") and g.get("lancado_em") and
                         (g.get("papel") or _papel(_conta_por_user(g["conta"]) or {})) == papel and
                         (agora - datetime.fromisoformat(g["lancado_em"])).total_seconds() < 600)
            pend[papel] = n  # None = não deu pra ler: lança como antes
    # 10/11 (2º banimento): várias contas eram lançadas na MESMA volta, uma atrás da outra — padrão de "um dono, muitas
    # contas". No máximo KAGGLE_LANCA_POR_VOLTA (1) conta nova por volta (~15 min); o resto espera a próxima volta.
    max_lanca = int(os.environ.get("KAGGLE_LANCA_POR_VOLTA", "1"))
    # 10/11 dona: treino de voz tem prioridade e precisa de ~10 contas — com treino na fila lança até 4 por volta
    try:
        if (_trabalho_pendente("treino") or 0) > 0:
            max_lanca = max(max_lanca, int(os.environ.get("KAGGLE_LANCA_TREINO", "4")))
    except Exception:  # noqa: BLE001
        pass
    lancadas = 0
    for g in gpus[:NUM_GPUS]:
        if not g.get("conta") and lancadas >= max_lanca:
            resumos.append(("espera a próxima volta (1 lançamento por volta)", None))
            continue
        if g.get("conta"):
            resumos.append(("rodando", _conta_por_user(g["conta"])))
            continue
        em_uso = {x.get("conta") for x in gpus if x.get("conta")}
        rodando = {p: sum(1 for x in gpus if x.get("conta") and
                          (x.get("papel") or _papel(_conta_por_user(x["conta"]) or {})) == p) for p in meta}
        com_trabalho = [p for p in ("longo", "curto") if (pend.get(p) is None or pend.get(p, 0) > 0)
                        and rodando[p] < meta[p]]  # nunca passa do nº de linhas do papel
        ordem = sorted(com_trabalho, key=lambda p: rodando[p] / max(1, meta[p]))  # o mais abaixo da meta primeiro
        conta, papel_usado = None, None
        for papel in ordem:
            conta = _escolher(est, em_uso, agora, papel)
            if conta is None:
                # linhas deste papel sem conta (cota acabou/ruim): OUTRA linha assume o conteúdo — só nesse caso. Regra
                # "ninguém fica sem produção": empresta linha de um papel que não tem trabalho, ou que continua com pelo
                # menos 1 linha própria depois de emprestar (curto com 1 linha só não empresta a única pro longo)
                for outro in ("longo", "curto"):
                    if outro == papel:
                        continue
                    if outro in com_trabalho and _linhas_livres(est, em_uso, agora, outro) < 2:
                        continue
                    conta = _escolher(est, em_uso, agora, outro)
                    if conta:
                        break
                if conta:
                    print(f"linha {_ip_da_conta(conta)} ({_papel(conta)}) assume trabalho de {papel} — "
                          f"linhas de {papel} sem conta", flush=True)
            if conta:
                papel_usado = papel
                break
        if conta is None:
            resumos.append(("parada: sem trabalho na fila" if not com_trabalho else "sem conta livre/verificada", None))
            continue
        # 10/11: conta que não lança (401/cota) já fica de descanso — tenta a próxima do mesmo papel NA MESMA volta
        lancou = _lancar_conta(conta, est, papel_usado) is not None
        for _ in range(2):
            if lancou:
                break
            em_uso = {x.get("conta") for x in gpus if x.get("conta")}
            outra = _escolher(est, em_uso, agora, papel_usado)
            if not outra or outra["username"] == conta["username"]:
                break
            conta = outra
            lancou = _lancar_conta(conta, est, papel_usado) is not None
        if not lancou:  # remedida na hora: cota acabou/401 — próxima volta
            resumos.append(("sem conta livre/verificada", None))
            continue
        g["conta"] = conta["username"]
        g["papel"] = papel_usado
        g["lancado_em"] = agora.isoformat(timespec="seconds")
        lancadas += 1
        est["ultimo_uso"][conta["username"]] = agora.isoformat(timespec="seconds")
        resumos.append(("lançado", conta))
        if pend.get(papel_usado) is not None:
            pend[papel_usado] -= 1
    return resumos


ENTRADA = AQUI / "entrada"
FILA_SRC = CFG.get("fila_src", "manhwa-drive:colab_recap/fila_src")


def repassar():
    feitos = []
    for d in sorted(ENTRADA.glob("*/enviado.ok")):
        d = d.parent
        pid = d.name
        ped = json.loads((d / "pedido.json").read_text(encoding="utf-8"))
        origem = ped.pop("origem_drive", None)
        if origem:
            ok = _rcl(["moveto", origem, f"{FILA_SRC}/{pid}/source.mp4"])
        else:
            # 08/11: 25 min matava a cópia no meio (403 de cota = rclone esperando) e recomeçava do zero toda rodada:
            # nada chegava ao Kaggle por 22 h. Vídeo de 0,2-1,4 GB ganha até 90 min.
            # 09/11: essa cópia rodava DENTRO da volta — com o Drive dando 403 de cota ela segurava a volta inteira
            # (2h16 numa só) e nenhuma conta era consultada nem lançada. Agora sobe em processo À PARTE (1 por vídeo,
            # marca 'subindo'); a volta segue e o pedido só vai pra fila quando a cópia terminar (source.ok).
            if (d / "source.ok").exists():
                ok = True
            else:
                trava = d / "subindo"
                vivo = trava.exists() and time.time() - trava.stat().st_mtime < 5400
                if not vivo:
                    trava.write_text(str(time.time()))
                    subprocess.Popen(["/bin/sh", "-c",
                                      " ".join(RCLONE + ["copyto", f"'{d / 'source.mp4'}'", f"'{FILA_SRC}/{pid}/source.mp4'"])
                                      + f" && touch '{d / 'source.ok'}'; rm -f '{trava}'"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    print(f"repassar {pid}: source.mp4 subindo em segundo plano", flush=True)
                continue
        if not ok:
            continue
        if (d / "voz").is_dir():  # pedido antigo (voz dentro do pedido)
            _rcl(["copy", str(d / "voz"), f"{FILA_SRC}/{pid}/voz"])
        for v in ped.get("vozes_lista") or []:  # teste de narradores (26/10): todas as vozes do revezamento
            if (AQUI / "vozes" / v).is_dir():
                _rcl(["copy", str(AQUI / "vozes" / v), f"{BASE}/vozes/{v}"])
        if (d / "voz").is_dir():
            pass
        elif ped.get("voz_clonada") and (AQUI / "vozes" / ped["voz_clonada"]).is_dir():
            # 26/10: cache de voz — sobe pro Drive só o que mudou (copy compara tamanho/data); o Kaggle lê de vozes/
            subprocess.run(RCLONE + ["copy", str(AQUI / "vozes" / ped["voz_clonada"]),
                                     f"{BASE}/vozes/{ped['voz_clonada']}"])
            # trabalhador antigo (sessões abertas antes do cache) só lê fila_src/<pid>/voz: cópia do lado do Drive
            _rcl(["copy", f"{BASE}/vozes/{ped['voz_clonada']}", f"{FILA_SRC}/{pid}/voz"])
        for f in d.iterdir():
            if f.is_file() and f.name not in ("source.mp4", "pedido.json", "enviado.ok"):
                _rcl(["copyto", str(f), f"{FILA}/{pid}/{f.name}"])
        (d / "pedido.json").write_text(json.dumps(ped, ensure_ascii=False), encoding="utf-8")
        if subprocess.run(RCLONE + ["copyto", str(d / "pedido.json"), f"{FILA}/{pid}/pedido.json"]).returncode == 0:
            shutil.rmtree(d, ignore_errors=True)
            feitos.append(pid)
    return feitos


def _sinal_min(agora, vivos):
    vals = []
    for v in vivos.values():
        if v.get("em"):
            try:
                vals.append((agora - datetime.fromisoformat(v["em"])).total_seconds() / 60)
            except (ValueError, TypeError):
                pass
    return round(min(vals)) if vals else None


def main():
    est = json.loads(EST.read_text()) if EST.exists() else {"avisados": []}
    # 03/11 (banimento em lote): a medição de hora em hora consultava TODAS as contas da saída de uma vez — na hermes-prod
    # eram 25 contas pelo MESMO IP, o padrão de multi-conta. Agora só mede a conta na hora de lançar (_lancar_conta).
    if CFG.get("medir_todas"):
        medir_cotas(est)
    if CFG.get("so_gpus"):  # central de outra saída: só as GPUs das contas dela
        resumos = manter_slots(est)
        EST.write_text(json.dumps(est))
        tmp = AQUI / f"gpus_{SAIDA}.json"
        tmp.write_text(json.dumps({"saida": SAIDA, "em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                   "gpus": [{"status": st, "conta": c["username"] if c else None}
                                            for st, c in resumos],
                                   "contas": contas_resumo(est, datetime.now(timezone.utc))}))
        _rcl(["copyto", str(tmp), f"{BASE}/gpus_{SAIDA}.json"], teto=300)
        print(datetime.now(FUSO).strftime("%d/%m %H:%M"), SAIDA, [(st, c and c["username"]) for st, c in resumos])
        return
    ENTRADA.mkdir(exist_ok=True)
    # 03/11: as GPUs ANTES do repasse — o upload de um original de 300-400 MB pro Drive (com limite de requisições)
    # prendia a volta inteira por 40+ min e ninguém conferia/lançava sessão nesse tempo
    resumos = manter_slots(est)
    EST.write_text(json.dumps(est))
    for pid in repassar():
        print("repassado pro Kaggle:", pid)
    agora = datetime.now(timezone.utc)
    # progresso/sinal de cada trabalhador: o QUEM dele é o KAGGLE_USERNAME, só das contas que estão rodando/lançadas
    # (lê só essas pra não fazer uma chamada rclone por conta do pool a cada 5 min)
    ativos = {c["username"] for st, c in resumos if c}
    detalhe = contas_resumo(est, agora)
    for saida, g in (POOL.get("gpus_por_saida") or {}).items():  # GPUs das centrais das outras saídas
        if saida != SAIDA:
            outra = ler(f"{BASE}/gpus_{saida}.json") or {}
            detalhe += outra.get("contas") or []
            ativos |= {x["conta"] for x in outra.get("gpus", []) if x.get("conta")}
            resumos += [(x["status"], {"username": x["conta"]} if x.get("conta") else None)
                        for x in outra.get("gpus", [])]
    progs, vivos = {}, {}
    for nome in ativos | {"kaggle"}:  # "kaggle" = trabalhador antigo/genérico
        p = ler(f"{BASE}/progresso_{nome}.json")
        if p:
            progs[nome] = p
        v = ler(f"{BASE}/vivo_{nome}.json")
        if v:
            vivos[nome] = v
    # pedidos na fila
    linhas, avisos = [], []
    pastas = {}
    for i in json.loads(rc("lsjson", "-R", "--files-only", "--max-depth", "2", FILA) or "[]"):
        if "/" in i["Path"]:
            p, n = i["Path"].split("/", 1)
            pastas.setdefault(p, set()).add(n)
    for pid, arqs in sorted(pastas.items()):
        ped = ler(f"{FILA}/{pid}/pedido.json") or {}
        titulo = ped.get("titulo", pid)[:80]
        if "pronto.json" in arqs:
            situ, pct = "pronto (vai pro Drive)", 100
            if pid + ":pronto" not in est["avisados"]:
                avisos.append(f"✅ Recap longo PRONTO: {titulo}")
                est["avisados"].append(pid + ":pronto")
        elif "erro.json" in arqs:
            situ, pct = "erro", 0
            if pid + ":erro" not in est["avisados"]:
                e = ler(f"{FILA}/{pid}/erro.json") or {}
                avisos.append(f"\U0001f534 Recap longo com ERRO: {titulo}\n{str(e.get('error', ''))[:200]}")
                est["avisados"].append(pid + ":erro")
        elif any(a.startswith("em_andamento") for a in arqs):
            prog_pid = None
            for nome, pg in progs.items():
                if pg.get("pid") == pid:
                    prog_pid = pg
                    break
            if prog_pid:
                situ = f"{prog_pid.get('fase', 'renderizando')} ({prog_pid.get('por', '?')})"
                pct = prog_pid.get("pct", 0)
            else:
                situ, pct = "comecando", 1
        else:
            situ, pct = "na fila", 0
        linhas.append((titulo, situ, pct))
    # só alerta "parado" se há vídeo pendente E nenhuma GPU está de fato rodando (status do kernel — não o vivo, que
    # fica velho durante um render longo porque o fazer() não grava vivo enquanto renderiza horas a fio)
    pendente = any(s not in ("pronto (vai pro Drive)", "erro") for _, s, _ in linhas)
    rodando_agora = any(st in ("rodando", "lançado") for st, _ in resumos)
    parado = pendente and not rodando_agora
    if parado and "kaggle_parado" not in est["avisados"]:
        avisos.append("⚠️ Nenhuma GPU do recap longo está rodando, com vídeo na fila (a VPS tenta relançar).")
        est["avisados"].append("kaggle_parado")
    if not parado and "kaggle_parado" in est["avisados"]:
        est["avisados"].remove("kaggle_parado")
    est["avisados"] = est["avisados"][-300:]
    for a in avisos:
        tg(a)
    hora = datetime.now(FUSO).strftime("%d/%m %H:%M")
    # resumo das GPUs pro HTML
    slot_html = ""
    for si, (status, conta) in enumerate(resumos):
        cor = "#34d399" if status == "rodando" else "#fbbf24" if status == "lançado" else "#666"
        nome = conta["username"] if conta else "-"
        slot_html += (f'<span style="display:inline-block;background:#111;border:1px solid {cor};border-radius:8px;'
                      f'padding:4px 10px;margin:3px;font-size:13px">'
                      f'<b style="color:{cor}">GPU {si+1}</b> {html.escape(nome)}: {status}</span>')
    verif = sum(1 for c in CONTAS if not _esta_ruim(est, c["username"], agora))
    corpo = "".join(
        f"<div class=c><b>{html.escape(t)}</b><div class=s>{html.escape(s)} — {p}%</div>"
        f"<div class=b><i style='width:{p}%'></i></div></div>" for t, s, p in linhas) or "<p>Fila vazia.</p>"
    pagina = (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
              f"<meta http-equiv=refresh content=120><meta name=robots content=noindex><title>Recap longo</title>"
              "<style>body{background:#000;color:#eee;font-family:system-ui,sans-serif;max-width:720px;margin:auto;"
              "padding:16px}.c{background:#111;border:1px solid #234;border-radius:12px;padding:12px;margin:10px 0}"
              ".s{color:#9ab;font-size:14px;margin:4px 0}.b{height:10px;background:#222;border-radius:9px;overflow:hidden}"
              ".b i{display:block;height:100%;background:linear-gradient(90deg,#059669,#34d399)}</style>"
              f"<h2>{html.escape(EMPRESA)}</h2>"
              f"<div style='margin:8px 0'>{slot_html}</div>"
              f"<p>{len(resumos)} GPUs · {verif} de {len(CONTAS)} contas em rotação (resto sem telefone verificado) · "
              f"atualizado {hora}</p>{corpo}")
    destino = Path("/var/www/landings/site") / CFG["pagina"]
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "index.html").write_text(pagina, encoding="utf-8")
    (destino / "status.json").write_text(json.dumps(
        {"empresa": EMPRESA, "gpus_total": len(resumos), "contas": len(POOL["contas"]), "verificadas": verif,
         "gpus": [{"gpu": si+1, "status": st, "conta": c["username"] if c else None} for si, (st, c) in enumerate(resumos)],
         "sinal_min": _sinal_min(agora, {**vivos, **progs}),
         "contas_detalhe": detalhe,
         "gpu_livre_h": round(sum(c.get("livre_h") or 0 for c in detalhe if c.get("estado") != "ruim"), 1),
         "atualizado": hora,
         "pedidos": [{"titulo": t, "situacao": s, "pct": p} for t, s, p in linhas]}, ensure_ascii=False),
        encoding="utf-8")
    EST.write_text(json.dumps(est))
    print(hora, f"{NUM_GPUS} GPUs ({verif} contas ok)", len(linhas), "pedidos", len(avisos), "avisos")


def liberar(users):
    """Tira contas da lista de 'ruins' pra serem re-testadas já na próxima passada (use depois de verificar o telefone
    delas no Kaggle). Sem argumento = libera todas. Solta a conta de qualquer GPU (lancado_em zerado) pra ela ser
    RELANÇADA do zero — senão o sistema julga pelo lançamento antigo (que falhou antes de a verificação propagar) e
    re-marca ruim na mesma passada."""
    est = json.loads(EST.read_text()) if EST.exists() else {}
    ruins = est.get("ruins", {})
    alvo = users or list(ruins)
    for u in alvo:
        ruins.pop(u, None)
    for g in est.get("gpus", []):
        if g.get("conta") in alvo:
            g["conta"] = None
            g["lancado_em"] = None
    EST.write_text(json.dumps(est))
    print(f"liberadas: {', '.join(alvo) or '(nenhuma)'}; ainda ruins: {len(ruins)}")


def contas(forcar=False):
    """Lista o estado de cada conta do pool: rodando / ruim (motivo) / sem cota / livre, com as horas de GPU da semana.
    forcar = mede a cota agora (comando "cotas")."""
    est = json.loads(EST.read_text()) if EST.exists() else {}
    if forcar:
        medir_cotas(est, forcar=True)
        EST.write_text(json.dumps(est))
    agora = datetime.now(timezone.utc)
    marca = {"rodando": "[GPU]", "ruim": "[x]  ", "sem cota": "[0h] ", "livre": "[ok] "}
    linhas = contas_resumo(est, agora)
    for c in linhas:
        cota = (f"{c['livre_h']:g} h livres de {c['total_h']:g}" if c.get("livre_h") is not None else
                f"cota ? ({c.get('cota_erro') or 'não medida'})")
        print(f"  {marca[c['estado']]} {c['conta']:<22} {cota}" + (f" — {c['motivo']}" if c.get("motivo") else ""))
    ok = [c for c in linhas if c["estado"] in ("rodando", "livre")]
    print(f"{len(ok)} de {len(CONTAS)} contas utilizáveis · {sum(c.get('livre_h') or 0 for c in ok):.1f} h de GPU livres"
          f" na semana · {NUM_GPUS} GPUs")


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "liberar":
        liberar(sys.argv[2:])
    elif len(sys.argv) >= 2 and sys.argv[1] == "contas":
        contas()
    elif len(sys.argv) >= 2 and sys.argv[1] == "cotas":
        contas(forcar=True)
    elif len(sys.argv) >= 3 and sys.argv[1] == "baixador":
        manter_baixador(sys.argv[2])
    else:
        main()
