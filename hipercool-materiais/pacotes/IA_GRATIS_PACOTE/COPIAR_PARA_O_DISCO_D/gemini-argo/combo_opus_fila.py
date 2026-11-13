#!/usr/bin/env python3
"""Mantem os combos de Opus fixados SO nas contas antigravity que RESPONDERAM AGORA (cron 2 min).

Pedido do dono (29/10/2026): o Opus nao pode travar carregando pra sempre. Conta que da 504
(trava 160s) ou 429 (sem cota) nunca pode estar no caminho. Entao so entra no combo a conta cujo
ULTIMO resultado no opus-4-6 (ultimos 25 min) foi 200. E cc/claude-opus-5-5 fica SEMPRE como rede
no fim (opus46-direto) ou no inicio (opus-auto), pra nunca ficar sem resposta.

- opus46-direto: [antigravity que responderam 200] + [cc]  (mapeado de antigravity/claude-opus-4-6-thinking)
- opus-auto:     [cc] + [antigravity que responderam 200]
Sem antigravity viva -> so [cc]. Prober (probe_opus.py) e quem gera os 200 quando a cota volta.
--simular mostra sem gravar.
"""
import sqlite3, json, subprocess, sys, urllib.request
from datetime import datetime, timedelta, timezone

DB = '/opt/omniroute/data/storage.sqlite'
LOG = '/opt/omniroute/combo_opus_fila.log'
BASE = 'http://localhost:20128'
MODELO = 'claude-opus-4-6-thinking'
JANELA_MIN = 25
CC_MODEL = 'cc/claude-opus-5-5'


def iso(d):
    return d.strftime('%Y-%m-%dT%H:%M:%S')


def working():
    """Retorna (vivas, rapida):
    vivas  = contas cujo ULTIMO opus-4-6 (ult 25min) foi 200 (respondem de verdade).
    rapida = contas cujo ULTIMO foi 429 (sem cota, mas FALHA RAPIDO) e nao estao pausadas.
    NUNCA inclui conta que travou (504, pausada pelo probe) nem desconhecida -> nunca pendura.
    So entra no combo quem a gente SABE que responde rapido (200 ou 429)."""
    agora = datetime.now(timezone.utc)
    db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=30)
    prio, pausa = {}, {}
    for cid, p, rl in db.execute(
            "select id,priority,rate_limited_until from provider_connections "
            "where provider='antigravity' and is_active=1"):
        prio[cid] = p or 999
        pausa[cid] = bool(rl and rl[:19] > iso(agora))
    ult = {}
    for cid, st in db.execute(
            "select connection_id,status from usage_history where provider='antigravity' "
            "and model=? and timestamp>? order by timestamp", (MODELO, iso(agora - timedelta(minutes=JANELA_MIN)))):
        ult[cid] = st
    vivas = sorted([c for c, s in ult.items() if s == '200' and c in prio and not pausa[c]],
                   key=lambda c: prio[c])
    rapida = sorted([c for c, s in ult.items() if s == '429' and c in prio and not pausa[c]
                     and c not in vivas], key=lambda c: prio[c])[:3]
    # fallback de 1 conta (maior prioridade nao-pausada) so pra nunca deixar o combo vazio
    fallback1 = sorted([c for c in prio if not pausa[c]], key=lambda c: prio[c])[:1]
    return vivas, rapida, fallback1


def api(m, c, b=None, ck=None):
    req = urllib.request.Request(
        BASE + c, method=m, data=json.dumps(b).encode() if b is not None else None,
        headers={'Content-Type': 'application/json', 'Origin': BASE, **({'Cookie': ck} if ck else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.headers.get('Set-Cookie'), json.loads(r.read() or b'{}')


def cc_step(combos):
    for c in combos:
        for m in c['models']:
            if str(m.get('model', '')).startswith('cc/'):
                return {k: m[k] for k in ('kind', 'model', 'providerId') if k in m}
    return {'kind': 'model', 'model': CC_MODEL, 'providerId': 'cc'}


def main():
    vivas, rapida, fallback1 = working()
    if '--simular' in sys.argv:
        print('vivas (200): %d | falha-rapida (429): %d | fallback1: %d' % (len(vivas), len(rapida), len(fallback1)))
        return
    senha = subprocess.run(['docker', 'exec', 'omniroute', 'printenv', 'INITIAL_PASSWORD'],
                           capture_output=True, text=True).stdout.strip()
    ck, _ = api('POST', '/api/auth/login', {'password': senha})
    cookie = ck.split(';')[0]
    _, lista = api('GET', '/api/combos', ck=cookie)
    cc = cc_step(lista['combos'])

    def passos(cids):
        return [{'kind': 'model', 'model': 'antigravity/' + MODELO, 'providerId': 'antigravity',
                 'connectionId': c} for c in cids]
    viv = passos(vivas)
    # opus46-direto: SO antigravity (nunca cc). Vivas + falha-rapida (429), nunca 504/desconhecida.
    # Combo nao pode ficar vazio (API recusa): se nao houver nenhuma, usa a de 429 mais prioritaria;
    # se nem isso, mantem o que ja esta (fallback do fallback) pra nao quebrar o PUT.
    direto = viv + passos(rapida)
    if not direto:
        direto = passos(fallback1)
    # opus-auto: cc primeiro + antigravity vivas (o "auto" pode usar qualquer um).
    alvos = {'opus46-direto': direto, 'opus-auto': [cc] + viv}
    mudou = False
    for nome, novos in alvos.items():
        atual = next((c for c in lista['combos'] if c['name'] == nome), None)
        if atual is None:
            continue
        antes = [(m.get('model'), m.get('connectionId')) for m in atual['models']]
        if antes == [(m.get('model'), m.get('connectionId')) for m in novos]:
            continue
        api('PUT', '/api/combos/' + atual['id'], {'models': novos}, ck=cookie)
        mudou = True
    if mudou:
        with open(LOG, 'a') as fh:
            fh.write('%s vivas=%d rapida=%d\n' % (iso(datetime.now(timezone.utc)), len(vivas), len(rapida)))


if __name__ == '__main__':
    main()
