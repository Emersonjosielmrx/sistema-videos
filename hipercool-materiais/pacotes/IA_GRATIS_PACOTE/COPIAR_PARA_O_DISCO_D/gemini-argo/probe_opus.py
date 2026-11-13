#!/usr/bin/env python3
"""Sonda CADA conta antigravity do Opus 4.6 com um "oi" pra saber qual responde de verdade.

Pedido do dono (29/10/2026): mandar um "oi" em cada conta individualmente (nao pela fila, senao
so testaria a primeira) pra ter certeza que responde antes de deixar o chat usar. Assim o 4.6 so
tem no caminho conta comprovadamente viva, e nunca trava carregando pra sempre.

So sonda conta que VOLTOU (dona 29/10: "so precisa ser na hora que aquela conta voltar"):
o reset da cota (next_reset_at, semanal) ja passou, ou a pausa de 504 venceu, e ela ainda nao foi
sondada nesta rodada (estado em probe_opus_estado.json). Conta esgotada ate o reset fica de fora.
O cron de 5 min so le o banco; o "oi" so sai quando alguma conta voltou.
  - reponta o combo _probe_opus pra ESSA conexao e chama "oi" (max_tokens 5, timeout curto);
  - 200  -> viva (o combo_opus_fila.py fixa ela no proximo ciclo);
  - 429  -> sem cota, fica de fora;
  - travou/timeout/504 -> pausa 20 min (rate_limited_until) e e re-sondada quando a pausa vence.
No fim roda o combo_opus_fila.py pra atualizar os combos na hora. Lock pra nao rodar dois juntos.
"""
import sqlite3, json, subprocess, sys, os, time, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

DB = '/opt/omniroute/data/storage.sqlite'
LOG = '/opt/omniroute/probe_opus.log'
LOCK = '/tmp/probe_opus.lock'
ESTADO = '/opt/omniroute/probe_opus_estado.json'
BASE = 'http://localhost:20128'
MODELO = 'claude-opus-4-6-thinking'
COMBO = '_probe_opus'
TIMEOUT = 40   # 29/10 (Fable): 10 s marcava "travou" conta sa (Opus 4.6 com thinking leva 10-30 s mesmo para "oi")
MAX = 6        # 6 x 40 s cabe no cron de 5 min (flock impede sobreposicao)
JA_OK_MIN = 15
VOLTAS = '/opt/omniroute/probe_opus_voltas.json'  # conta -> {"voltou_em", "ultimo", "historico"} (dona: saber a hora exata)


def iso(d):
    return d.strftime('%Y-%m-%dT%H:%M:%S')


def api(m, c, b=None, ck=None, to=30):
    req = urllib.request.Request(
        BASE + c, method=m, data=json.dumps(b).encode() if b is not None else None,
        headers={'Content-Type': 'application/json', 'Origin': BASE, **({'Cookie': ck} if ck else {})})
    with urllib.request.urlopen(req, timeout=to) as r:
        return r.status, json.loads(r.read() or b'{}')


def candidatos():
    agora = datetime.now(timezone.utc)
    db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=30)
    prio, pausa, nome = {}, {}, {}
    for cid, p, rl, em in db.execute(
            "select id,priority,rate_limited_until,coalesce(email,name) from provider_connections "
            "where provider='antigravity' and is_active=1"):
        prio[cid] = p or 999
        pausa[cid] = bool(rl and rl[:19] > iso(agora))
        nome[cid] = (em or '?').split('@')[0]
    ult = {}
    for cid, st in db.execute(
            "select connection_id,status from usage_history where provider='antigravity' "
            "and model=? and timestamp>? order by timestamp", (MODELO, iso(agora - timedelta(minutes=JA_OK_MIN)))):
        ult[cid] = st
    snap = {}
    for cid, ex, nx in db.execute(
            "select s.connection_id,s.is_exhausted,s.next_reset_at from quota_snapshots s join "
            "(select connection_id,max(id) mid from quota_snapshots where provider='antigravity' "
            "and window_key=? group by connection_id) u on s.id=u.mid", (MODELO,)):
        snap[cid] = (ex, nx or '')
    rls = dict(db.execute("select id,coalesce(rate_limited_until,'') from provider_connections "
                          "where provider='antigravity' and is_active=1"))
    estado = carregar_estado()
    cands, marcas = [], {}
    for c in prio:
        if pausa[c] or ult.get(c) == '200':
            continue
        ex, nx = snap.get(c, (0, ''))
        if ex == 1 and nx[:19] > iso(agora):
            continue  # esgotada ate o reset (semanal): nao voltou ainda
        marca = '%s|%s' % (nx, rls.get(c, ''))  # muda quando o reset passa ou a pausa de 504 vence
        if estado.get(c) == marca:
            continue  # ja sondada nesta rodada
        cands.append(c)
        marcas[c] = marca
    cands.sort(key=lambda c: prio[c])
    return cands[:MAX], nome, marcas


def carregar_estado():
    try:
        return json.load(open(ESTADO))
    except (OSError, ValueError):
        return {}


def pausar(cid, minutos=20):
    agora = datetime.now(timezone.utc)
    ate = (agora + timedelta(minutes=minutos)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    db = sqlite3.connect(DB, timeout=30)
    db.execute("update provider_connections set rate_limited_until=? where id=? and "
               "(rate_limited_until is null or rate_limited_until<?)", (ate, cid, ate))
    db.commit()
    db.close()


def main():
    fh_lock = open(LOCK, 'w')
    try:
        import fcntl
        fcntl.flock(fh_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, ImportError):
        return
    cands, nome, marcas = candidatos()
    if not cands:
        return
    estado = carregar_estado()
    if '--semear' in sys.argv:
        estado.update(marcas)
        json.dump(estado, open(ESTADO, 'w'))
        print('semeadas %d contas (sem probe)' % len(marcas))
        return
    senha = subprocess.run(['docker', 'exec', 'omniroute', 'printenv', 'INITIAL_PASSWORD'],
                           capture_output=True, text=True).stdout.strip()
    lreq = urllib.request.Request(
        BASE + '/api/auth/login', method='POST',
        data=json.dumps({'password': senha}).encode(),
        headers={'Content-Type': 'application/json', 'Origin': BASE})
    with urllib.request.urlopen(lreq, timeout=30) as lr:
        cookie = lr.headers.get('Set-Cookie').split(';')[0]
    _, lista = api('GET', '/api/combos', ck=cookie)
    old = next((c for c in lista['combos'] if c['name'] == COMBO), None)
    if old is None:
        api('POST', '/api/combos', {'name': COMBO, 'strategy': 'priority',
            'models': [{'kind': 'model', 'model': 'antigravity/' + MODELO, 'providerId': 'antigravity',
                        'connectionId': cands[0]}]}, ck=cookie)
        _, lista = api('GET', '/api/combos', ck=cookie)
        old = next(c for c in lista['combos'] if c['name'] == COMBO)
    cid_combo = old['id']
    try:
        voltas = json.load(open(VOLTAS))
    except (OSError, ValueError):
        voltas = {}
    vivo, semcota, travou, detalhe = [], [], [], []
    for cid in cands:
        passos = [{'kind': 'model', 'model': 'antigravity/' + MODELO, 'providerId': 'antigravity',
                   'connectionId': cid}]
        api('PUT', '/api/combos/' + cid_combo, {'models': passos}, ck=cookie)
        t0 = time.time()
        try:
            st, _ = api('POST', '/v1/chat/completions',
                        {'model': COMBO, 'messages': [{'role': 'user', 'content': 'oi'}],
                         'max_tokens': 5}, ck=cookie, to=TIMEOUT)
            vivo.append(cid); res = 'viva'
        except urllib.error.HTTPError as e:
            if e.code == 429:
                semcota.append(cid); res = 'sem cota (429)'
            elif e.code in (502, 503, 504):
                travou.append(cid); pausar(cid); res = 'travou (%d)' % e.code
            else:
                semcota.append(cid); res = 'erro %d' % e.code
        except Exception as e:
            travou.append(cid); pausar(cid); res = 'travou (%s)' % type(e).__name__
        estado[cid] = marcas[cid]
        seg = round(time.time() - t0, 1)
        n = nome[cid]
        v = voltas.setdefault(n, {'historico': []})
        agora_s = iso(datetime.now(timezone.utc))
        if res == 'viva' and v.get('ultimo') != 'viva':
            v['voltou_em'] = agora_s  # 29/10 (dona): a hora exata em que a conta voltou a responder o Opus 4.6
            v['historico'] = (v.get('historico') or [])[-9:] + [agora_s]
        v['ultimo'] = res
        v['ultimo_em'] = agora_s
        v['seg'] = seg
        detalhe.append('%s=%s(%.0fs)' % (n, res, seg))
    json.dump(estado, open(ESTADO, 'w'))
    json.dump(voltas, open(VOLTAS, 'w'), ensure_ascii=False, indent=1)
    linha = '%s vivas=%d semcota=%d travou=%d | vivas: %s | pausadas: %s | %s' % (
        iso(datetime.now(timezone.utc)), len(vivo), len(semcota), len(travou),
        ','.join(nome[c] for c in vivo), ','.join(nome[c] for c in travou), ' '.join(detalhe))
    with open(LOG, 'a') as f:
        f.write(linha + '\n')
    print(linha)
    subprocess.run(['python3', '/opt/omniroute/combo_opus_fila.py'])


if __name__ == '__main__':
    main()
