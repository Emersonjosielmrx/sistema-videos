#!/usr/bin/env python3
# 06/11/2026 dona: "um amigo meu divide as contas e usa elas também — as que ele tentar usar, usaremos primeiro antes
# dele; as que ninguém estiver usando além de nós, deixaremos por último".
#
# Como mede (SÓ LÊ o banco do OmniRoute; NÃO consulta nenhuma conta — regra de nunca varrer contas pelo mesmo IP):
#   queda da semana  = quanto a % da semana caiu na janela (quota_snapshots, que o OmniRoute grava a cada ~5 min)
#   nosso uso        = pedidos que o OmniRoute mandou pela conta na mesma janela (usage_history)
#   queda sem nosso uso (ou bem maior do que o nosso uso explica) = OUTRA PESSOA está usando a conta.
# Ordem nova (prioridade do OmniRoute): 1º as contas com uso alheio (gastamos antes dele), depois as que só nós usamos,
# por último as que ninguém usa. Contas esgotadas ficam onde estão (não respondem mesmo).
# Roda por cron a cada 15 min. Estado/histórico: /opt/omniroute/vigia_uso_alheio.json (o painel mostra).
import datetime, json, sqlite3, sys, urllib.request, http.cookiejar, subprocess

DB = '/opt/omniroute/data/storage.sqlite'
EST = '/opt/omniroute/vigia_uso_alheio.json'
LOG = '/opt/omniroute/vigia_uso_alheio.log'
JANELA_H = 3            # olha as últimas 3 h
PCT_POR_PEDIDO = 0.25   # referência: quanto 1 pedido nosso costuma tirar da semana (recalibrado abaixo pelos dados)
FOLGA_PCT = 2           # queda até 2 pontos além do nosso uso é ruído de medição
PROVS = ('claude',)


def log(m):
    with open(LOG, 'a') as f:
        f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ ') + m + '\n')


def medir(db, prov):
    desde = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=JANELA_H)).strftime('%Y-%m-%dT%H:%M:%S')
    contas = db.execute('SELECT id, coalesce(email,name), is_active, coalesce(priority,999) FROM provider_connections '
                        'WHERE provider=?', (prov,)).fetchall()
    out = []
    for cid, nome, ativa, pri in contas:
        s = db.execute("SELECT remaining_percentage, created_at, next_reset_at FROM quota_snapshots WHERE connection_id=? "
                       "AND window_key LIKE '%7d%' AND created_at>=? ORDER BY id", (cid, desde)).fetchall()
        s = [x for x in s if x[0] is not None]
        nosso = db.execute("SELECT count(*) FROM usage_history WHERE connection_id=? AND timestamp>=?",
                           (cid, desde)).fetchone()[0]
        queda = 0.0
        for a, b in zip(s, s[1:]):  # soma só as quedas (a renovação da semana sobe e não conta)
            if b[0] < a[0]:
                queda += a[0] - b[0]
        resta = s[-1][0] if s else None
        out.append(dict(id=cid, nome=nome, ativa=bool(ativa), pri=pri, nosso=nosso, queda=round(queda, 1),
                        resta=resta, leituras=len(s)))
    # calibra "quanto 1 pedido nosso tira" com as contas que não mostram sinal de outro usuário
    pares = [(c['queda'], c['nosso']) for c in out if c['nosso'] >= 10 and c['queda'] > 0]
    taxa = sorted(q / n for q, n in pares)[len(pares) // 4] if len(pares) >= 3 else PCT_POR_PEDIDO
    for c in out:
        esperado = c['nosso'] * taxa
        alheio = c['queda'] - esperado - FOLGA_PCT
        c['esperado'] = round(esperado, 1)
        c['alheio'] = round(max(0.0, alheio), 1)
        if c['leituras'] < 2:
            c['quem'] = 'sem leitura'
        elif c['alheio'] > 0:
            c['quem'] = 'outra pessoa usando'
        elif c['nosso'] > 0:
            c['quem'] = 'só nós'
        else:
            c['quem'] = 'ninguém'
    return out, taxa


def api_login():
    pw = subprocess.run(['docker', 'exec', 'omniroute', 'printenv', 'INITIAL_PASSWORD'], capture_output=True,
                        text=True).stdout.strip()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.open(urllib.request.Request('http://localhost:20128/api/auth/login', data=json.dumps({'password': pw}).encode(),
                                   headers={'content-type': 'application/json'}), timeout=30)
    return op


def confirmar(contas, anterior):
    """Uso alheio só vale se apareceu também na rodada anterior (a medição tem ruído de 1–3 pontos)."""
    antes = {c['id']: c.get('quem') for c in (anterior or {}).get('contas', [])}
    for c in contas:
        if c['quem'] == 'outra pessoa usando' and antes.get(c['id']) not in ('outra pessoa usando', 'alheio (1ª vez)'):
            c['quem'] = 'alheio (1ª vez)'
        if c['resta'] is not None and c['resta'] <= 0:
            c['quem'] = 'esgotada'


def ordenar(prov, contas, aplicar=True):
    peso = {'outra pessoa usando': 0, 'alheio (1ª vez)': 1, 'só nós': 1, 'ninguém': 2, 'sem leitura': 3, 'esgotada': 4}
    # dentro do grupo "alheio": quem mais está sendo gasto por ele primeiro; nos outros: quem tem mais crédito
    ordem = sorted([c for c in contas if c['ativa']],
                   key=lambda c: (peso[c['quem']], -c['alheio'], -(c['resta'] if c['resta'] is not None else -1)))
    nova = {c['id']: n for n, c in enumerate(ordem, start=1)}
    # só mexe na ordem quando há uso alheio CONFIRMADO e essa conta ainda não está na frente (não briga com o botão
    # "usar primeiro" do painel nem com o rodízio normal)
    alheias = [c for c in ordem if c['quem'] == 'outra pessoa usando']
    if not alheias or all(c['pri'] <= len(alheias) for c in alheias):
        nova = {c['id']: c['pri'] for c in contas}
    mudou = [c for c in ordem if c['pri'] != nova[c['id']]]
    if aplicar and mudou:
        op = api_login()
        for c in mudou:
            req = urllib.request.Request(f'http://localhost:20128/api/providers/{c["id"]}', method='PUT',
                                         data=json.dumps({'priority': nova[c['id']]}).encode(),
                                         headers={'content-type': 'application/json'})
            op.open(req, timeout=30)
        log(f'{prov}: ordem nova — ' + ', '.join(f'{nova[c["id"]]}º {c["nome"].split("@")[0]} ({c["quem"]})'
                                                  for c in ordem[:6]))
    for c in contas:
        c['pri_nova'] = nova.get(c['id'], c['pri'])
    return len(mudou)


def main():
    aplicar = '--simular' not in sys.argv
    db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=10)
    try:
        est = json.load(open(EST))
    except Exception:
        est = {}
    agora = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    for prov in PROVS:
        contas, taxa = medir(db, prov)
        confirmar(contas, est.get(prov))
        n = ordenar(prov, contas, aplicar)
        hist = est.get(prov, {}).get('historico', [])
        for c in contas:
            if c['quem'] == 'outra pessoa usando':
                hist.append({'em': agora, 'nome': c['nome'], 'alheio': c['alheio'], 'nosso': c['nosso']})
        est[prov] = {'em': agora, 'janela_h': JANELA_H, 'pct_por_pedido': round(taxa, 3), 'mudou': n,
                     'contas': contas, 'historico': hist[-300:]}
        print(prov, 'taxa', round(taxa, 3), 'mudou', n)
        for c in sorted(contas, key=lambda c: c['pri_nova']):
            print(f"  {c['pri_nova']:>2} {c['nome'][:34]:34} resta {c['resta']} queda {c['queda']} nosso {c['nosso']} "
                  f"esperado {c['esperado']} alheio {c['alheio']} -> {c['quem']}")
    db.close()
    if aplicar:  # --simular não grava (senão a 1ª detecção já contava como confirmada na rodada seguinte)
        json.dump(est, open(EST, 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main()
