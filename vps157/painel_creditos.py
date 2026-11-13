#!/usr/bin/env python3
# 05/11/2026 - Painel de creditos das contas do OmniRoute (VPS 157, porta 20172).
# So LE o banco do OmniRoute (quota_snapshots, que o proprio OmniRoute grava a cada ~5 min).
# NAO consulta nenhuma conta (regra: nunca varrer contas pelo mesmo IP).
# Botao "liberar": desliga e religa UMA conta pela API do OmniRoute (apaga a marcacao velha de "sem credito").
# Acesso: http://157.173.207.22:20172/?k=<CHAVE>   (CHAVE em /opt/omniroute/painel_creditos.chave)
import sqlite3, json, datetime, subprocess, threading, time, urllib.request, http.cookiejar, html, os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB = '/opt/omniroute/data/storage.sqlite'
CHAVE = open('/opt/omniroute/painel_creditos.chave').read().strip()
LOG = '/opt/omniroute/painel_creditos.log'
BR = datetime.timezone(datetime.timedelta(hours=-3))
liberando = {}

def log(m):
    with open(LOG, 'a') as f:
        f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ ') + m + '\n')

def dt(s):
    if not s: return None
    try: return datetime.datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(datetime.timezone.utc)
    except Exception:
        try: return datetime.datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
        except Exception: return None

def janela(k):
    k = (k or '').lower()
    if '7d' in k or 'week' in k: return 'semana'
    if '5h' in k or 'session' in k: return '5h'
    return k

def dados(prov):
    db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=10)
    contas = db.execute("SELECT id, coalesce(email, name, display_name, id), is_active, coalesce(test_status,''), "
                        "coalesce(last_error,''), coalesce(priority, 999) FROM provider_connections WHERE provider=?", (prov,)).fetchall()
    menor_pri = min([c[5] for c in contas if c[2]] or [None])
    snaps = db.execute("SELECT q.connection_id, q.window_key, q.remaining_percentage, q.is_exhausted, q.next_reset_at, q.created_at "
                       "FROM quota_snapshots q JOIN (SELECT max(id) AS mid FROM quota_snapshots WHERE provider=? "
                       "GROUP BY connection_id, window_key) m ON q.id = m.mid", (prov,)).fetchall()
    provs = ['claude', 'antigravity', 'kiro', 'openrouter', 'gemini']
    db.close()
    agora = datetime.datetime.now(datetime.timezone.utc)
    por = {}
    # 09/11 (dona): antigravity mostra a cota do Opus que a conta TEM (5.5 ou 4.6; quem ganhou o 5.5 perdeu o 4.6)
    tres_h = agora - datetime.timedelta(hours=3)
    tem = {}
    for cid, wk, rem, exh, rst, cri in snaps:
        if prov == 'antigravity' and wk in ('claude-opus-5-5-high', 'claude-opus-4-6-thinking') and dt(cri) and dt(cri) > tres_h:
            tem.setdefault(cid, set()).add(wk)
    opus = {cid: ('claude-opus-5-5-high' if 'claude-opus-5-5-high' in w else 'claude-opus-4-6-thinking') for cid, w in tem.items()}
    for cid, wk, rem, exh, rst, cri in snaps:
        if prov == 'antigravity' and wk != opus.get(cid):
            continue  # so a janela do Opus da conta (as do Gemini nao dizem nada do Opus)
        if prov == 'openrouter' and wk == 'credits':
            continue  # 11/11: conta gratis tem 0 de credito pago e aparecia "esgotada"; vale o limite gratis do dia
        j = janela(wk)
        r = dt(rst)
        p = rem if rem is not None else None
        if r and r <= agora: p = 100.0  # ja passou a hora de renovar: volta cheio
        por.setdefault(cid, {})[j] = {'pct': p, 'reset': r, 'quando': dt(cri), 'nome': wk}
    linhas = []
    for cid, nome, ativa, st, err, pri in contas:
        w = por.get(cid, {})
        sem = w.get('semana'); h5 = w.get('5h')
        outros = {k: v for k, v in w.items() if k not in ('semana', '5h')}
        if not sem and not h5 and outros:  # provedores com outras janelas (ex.: modelos do antigravity)
            menor = min(outros.values(), key=lambda v: (v['pct'] if v['pct'] is not None else 999))
            sem = menor
        ps = sem['pct'] if sem else None
        p5 = h5['pct'] if h5 else None
        quando = max([v['quando'] for v in w.values() if v['quando']] or [None], key=lambda x: x or agora - datetime.timedelta(days=99))
        if not ativa: grupo = 3
        elif ps is None and p5 is None: grupo = 2
        elif (ps is None or ps > 0) and (p5 is None or p5 > 0): grupo = 0
        else: grupo = 1
        libera = None
        if grupo == 1:
            cands = [v['reset'] for v in (sem, h5) if v and v['pct'] is not None and v['pct'] <= 0 and v['reset']]
            libera = max(cands) if cands else None
        linhas.append(dict(id=cid, nome=nome, ativa=ativa, st=st, err=err, ps=ps, p5=p5, pri=pri,
                           primeira=bool(ativa and pri == menor_pri),
                           rs=sem['reset'] if sem else None, r5=h5['reset'] if h5 else None,
                           quando=quando, grupo=grupo, libera=libera,
                           modelo={'claude-opus-5-5-high': 'Opus 5.5', 'claude-opus-4-6-thinking': 'Opus 4.6'}.get(
                               opus.get(cid), 'sem Opus (só Gemini)') if prov == 'antigravity' else
                           {'claude': 'Opus 5.5', 'kiro': 'Kiro', 'openrouter': 'grátis do dia'}.get(prov, prov)))
    def chave(l):
        if l['grupo'] == 0: return (0, -(l['ps'] if l['ps'] is not None else 100), -(l['p5'] or 0))
        if l['grupo'] == 1: return (1, l['libera'] or agora + datetime.timedelta(days=30))
        return (l['grupo'], l['nome'])
    linhas.sort(key=chave)
    return linhas, provs

# 11/11 dona: uma aba por fonte que usamos. esc = colunas escondidas na aba; rot = nome da coluna na aba.
CFG = {
    'geral': dict(t='Geral', esc=['p5', 'hist', 'quem', 'uso3h', 'libera'],
                  rot={'nome': 'Fonte', 'modelo': 'Modelo', 'ps': 'Contas prontas', 'taxa': 'Deu certo', 'info': 'Situação'}),
    'opus55': dict(t='Opus 5.5 (todas)', esc=['p5', 'hist', 'quem', 'taxa'],
                   rot={'ps': 'Cota / crédito', 'modelo': 'Fonte', 'info': 'Situação'}),
    'claude': dict(t='Opus 5.5 pago', esc=['taxa', 'info']),
    # 12/11 dona: fila só do Fable 5.2 (mesmas contas cc; a cota é a da conta, os pedidos e falhas são só do Fable)
    'fable': dict(t='Fable 5.2', esc=['hist', 'quem'], rot={'taxa': 'Fable deu certo (24 h)', 'uso3h': 'Pedidos Fable 3h/24h',
                                                           'info': 'Último "sem cota" do Fable'}),
    'ag55': dict(t='Opus 5.5 Antigravity', esc=['p5', 'hist', 'quem', 'info'], rot={'ps': 'Cota do Opus'}),
    'ag46': dict(t='Opus 4.6 Antigravity', esc=['p5', 'hist', 'quem', 'info'], rot={'ps': 'Cota do Opus'}),
    'cw': dict(t='Sonnet web', esc=['ps', 'p5', 'hist', 'quem', 'info'], rot={'modelo': 'Modelo'}),
    'kiro': dict(t='Kiro', esc=['p5', 'hist', 'quem', 'info'], rot={'ps': 'Crédito', 'modelo': 'Modelo'}),
    'gemini': dict(t='Gemini', esc=['p5', 'hist', 'quem', 'info'], rot={'ps': 'Cota da semana', 'modelo': 'Fonte'}),
    'argon': dict(t='Argon', esc=['ps', 'p5', 'hist', 'quem', 'uso3h', 'falhas'],
                  rot={'taxa': 'Deu certo (total)', 'info': 'Situação', 'modelo': 'Fonte'}),
    'genspark': dict(t='Genspark', esc=['p5', 'hist', 'quem', 'uso3h', 'falhas'],
                     rot={'ps': 'Créditos do dia', 'taxa': 'Deu certo (total)', 'info': 'Situação', 'modelo': 'Fonte'}),
    '1min': dict(t='1min', esc=['p5', 'hist', 'quem', 'uso3h', 'falhas'],
                 rot={'ps': 'Saldo (de 265 mil)', 'taxa': 'Deu certo (total)', 'info': 'Situação', 'modelo': 'Fonte'}),
    'openrouter': dict(t='OpenRouter', esc=['p5', 'hist', 'quem', 'info'], rot={'ps': 'Grátis do dia', 'modelo': 'Modelo'}),
}
EXTERNO = '/opt/omniroute/painel_externo.json'  # Argon/Genspark/1min rodam no PC; o painel_externo.py de lá manda a cada 5 min


def isoz(d):
    return d.strftime('%Y-%m-%dT%H:%M:%S')


def uso_conexoes(db, provs, modelo_like=None):
    """Por conexão: (ok 24h, pedidos 24h, pedidos 3h, último ok, último pedido, falhas 24h, último erro real)."""
    agora = datetime.datetime.now(datetime.timezone.utc)
    sql = ("SELECT connection_id, sum(CAST(status AS INTEGER)=200), count(*), sum(timestamp > ?), "
           "max(CASE WHEN CAST(status AS INTEGER)=200 THEN timestamp END), max(timestamp), "
           "sum(CAST(status AS INTEGER) NOT IN (200,429)), "
           "max(CASE WHEN CAST(status AS INTEGER) NOT IN (200,429) THEN timestamp END) FROM usage_history "
           f"WHERE provider IN ({','.join('?' * len(provs))}) AND timestamp > ?")
    par = [isoz(agora - datetime.timedelta(hours=3)), *provs, isoz(agora - datetime.timedelta(days=1))]
    if modelo_like:
        sql += ' AND model LIKE ?'
        par.append(modelo_like)
    return {r[0]: r[1:] for r in db.execute(sql + ' GROUP BY 1', par)}


def linha_uso(c, u, modelo, agora):
    """Conta sem medição de cota (Sonnet web, AI Studio): o estado vem do que os pedidos reais deram."""
    cid, nome, ativa, err, st, pri, rl = c
    ok, tot, u3, ult_ok, ult, falhas, ult_err = u or (0, 0, 0, None, None, 0, None)
    rlf = dt(rl)
    if rlf and rlf <= agora: rlf = None
    if not ativa: g = 3
    elif rlf: g = 1
    elif not tot: g = 2
    elif ult_ok and ult_ok == ult: g = 0
    else: g = 1
    voltou = None
    if ult_err and ult_ok and ult_ok > ult_err:
        voltou = ult_ok
    return dict(id=cid, nome=nome, ativa=bool(ativa), ps=None, p5=None, pri=pri, primeira=False, grupo=g, err=err, st=st,
                rs=None, r5=None, libera=rlf.isoformat() if rlf else None, quando=dt(ult).isoformat() if ult else None,
                liberando=liberando.get(cid), hist=[], uso3h=u3 or 0, uso24h=tot or 0, quem=None, alheio=None,
                modelo=modelo, oi=None, taxa=round(100 * ok / tot) if tot else None, ok=ok or 0, tot=tot or 0,
                falhas=falhas or 0, voltou=voltou)


def conexoes(db, prov):
    return db.execute("SELECT id, coalesce(email, name, display_name, id), is_active, coalesce(last_error,''), "
                      "coalesce(test_status,''), coalesce(priority, 999), rate_limited_until FROM provider_connections "
                      "WHERE provider=?", (prov,)).fetchall()


def ordenar_generico(rows):
    rows.sort(key=lambda r: (r['grupo'], -(r['ps'] if r['ps'] is not None else (r.get('taxa') or 0)), str(r['nome'])))
    return rows


def dados_gemini():
    """Todas as fontes de Gemini: chaves do AI Studio, contas Antigravity (cota Gemini da semana) e Gemini web."""
    agora = datetime.datetime.now(datetime.timezone.utc)
    db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=10)
    rows = []
    u = uso_conexoes(db, ('gemini',))
    rows += [linha_uso(c, u.get(c[0]), 'AI Studio (chave)', agora) for c in conexoes(db, 'gemini')]
    u = uso_conexoes(db, ('gemini-web',))
    rows += [linha_uso(c, u.get(c[0]), 'Gemini web (Pro)', agora) for c in conexoes(db, 'gemini-web')]
    u = uso_conexoes(db, ('antigravity',), 'gemini%')
    sem = {r[0]: r[1:] for r in db.execute(
        "SELECT connection_id, remaining_percentage, next_reset_at, created_at FROM quota_snapshots WHERE id IN "
        "(SELECT max(id) FROM quota_snapshots WHERE provider='antigravity' AND window_key='gemini_weekly' GROUP BY connection_id)")}
    for c in conexoes(db, 'antigravity'):
        r = linha_uso(c, u.get(c[0]), 'Antigravity', agora)
        s = sem.get(c[0])
        if s and r['ativa']:
            p, rst = s[0], dt(s[1])
            if rst and rst <= agora: p = 100.0
            r.update(ps=p, rs=rst.isoformat() if rst else None)
            if p is not None and r['grupo'] != 1:
                r['grupo'] = 0 if p > 0 else 1
            if r['grupo'] == 1 and p is not None and p <= 0 and rst:
                r['libera'] = rst.isoformat()
        rows.append(r)
    db.close()
    return ordenar_generico(rows)


def dados_externo(p):
    try:
        ext = json.load(open(EXTERNO))
    except Exception:
        return [], 'sem dados do PC ainda (o painel_externo.py do PC manda a cada 5 min)'
    em = dt(ext.get('em'))
    idade = (datetime.datetime.now(datetime.timezone.utc) - em).total_seconds() / 60 if em else 999
    nota = ext.get('notas', {}).get(p, '')
    if idade > 15:
        nota = f'ATENÇÃO: dados do PC de {idade:.0f} min atrás (o PC parou de mandar). ' + nota
    padrao = dict(id=None, ativa=True, ps=None, p5=None, pri=0, primeira=False, err='', st='', rs=None, r5=None,
                  libera=None, quando=None, liberando=None, hist=[], uso3h=0, uso24h=0, quem=None, alheio=None, oi=None,
                  taxa=None, ok=0, tot=0, info='', modelo='', falhas=0, voltou=None)
    return ordenar_generico([{**padrao, **r} for r in ext.get(p, [])]), nota


_CACHE_JSON = {}

def dados_json(prov, incluir_hist=True):
    """06/11 dona ("painel muito ruim e pouco interativo"): os dados em JSON para a página nova (desenha no navegador,
    atualiza sem recarregar). Junta: % de cada janela, histórico de 3 dias da semana (1 ponto por hora), nosso uso
    (pedidos 3 h / 24 h) e o veredito do vigia_uso_alheio (quem está usando a conta).
    11/11: uma aba por fonte (CFG)."""
    if prov not in CFG: prov = 'claude'
    ck = (prov, bool(incluir_hist))
    now_ts = time.time()
    hit = _CACHE_JSON.get(ck)
    if hit and (now_ts - hit[0]) < 8.0:
        return hit[1]
    cfg = CFG[prov]
    meta = {'prov': prov, 'titulo': cfg['t'], 'provs': [[k, c['t']] for k, c in CFG.items()], 'esc': cfg['esc'],
            'rot': cfg.get('rot', {}), 'oi': prov in ('claude', 'ag55', 'ag46'), 'nota': '',
            'agora': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if prov == 'opus55':
        contas = []
        for p, fonte in (('claude', 'Opus 5.5 pago (cc)'), ('ag55', 'Antigravity'), ('genspark', 'Genspark'), ('1min', '1min')):
            for c in dados_json(p, incluir_hist=False)['contas']:
                contas.append({**c, 'modelo': fonte, 'id': None, 'oi': None})
        meta['nota'] = 'Todas as contas com Opus 5.5: pago, Antigravity, Genspark e 1min. Os botões ficam na aba de cada fonte.'
        res = {**meta, 'contas': ordenar_generico(contas), 'lida': 'lida', 'vigia_em': None, 'alheio_hist': []}
        _CACHE_JSON[ck] = (now_ts, res)
        return res
    if prov == 'geral':
        contas = []
        for p, c in CFG.items():
            if p in ('geral', 'opus55'):
                continue
            L = dados_json(p, incluir_hist=False)['contas']
            at = [x for x in L if x['ativa']]
            ok = sum(1 for x in at if x['grupo'] == 0)
            lib = sorted(x['libera'] for x in at if x['grupo'] == 1 and x.get('libera'))
            tot = sum(x.get('tot') or x.get('uso24h') or 0 for x in L)
            okp = sum(x.get('ok') or 0 for x in L)
            g = 0 if ok else (1 if at else 3)
            fl = sum(x.get('falhas') or 0 for x in L)
            caidas = [x for x in L if x.get('falhas') and not x.get('voltou')]
            volt = max((x['voltou'] for x in L if x.get('falhas') and x.get('voltou')), default=None)
            contas.append(dict(id=None, nome=c['t'], ativa=bool(at), grupo=g, ps=round(100 * ok / len(at)) if at else 0,
                               p5=None, rs=None, r5=None, pri=0, primeira=False, err='', st='', libera=lib[0] if lib else None,
                               quando=None, liberando=None, hist=[], uso3h=0, uso24h=tot, quem=None, alheio=None, oi=None,
                               taxa=round(100 * okp / tot) if tot and okp else None, ok=okp, tot=tot, modelo='',
                               falhas=fl, voltou=None if caidas else volt,
                               info=f'{ok} prontas de {len(at)} ligadas ({len(L)} no total)' +
                                    (f' · próxima volta {lib[0][5:16].replace("T", " ")} UTC' if not ok and lib else '')))
        meta['nota'] = 'Uma linha por fonte. "Contas prontas" = % das contas ligadas com crédito agora. Clique na aba da fonte para ver as contas.'
        res = {**meta, 'contas': contas, 'lida': 'lida pelo PC', 'vigia_em': None, 'alheio_hist': []}
        _CACHE_JSON[ck] = (now_ts, res)
        return res
    if prov in ('argon', 'genspark', '1min'):
        contas, meta['nota'] = dados_externo(prov)
        res = {**meta, 'contas': contas, 'lida': 'lida pelo PC', 'vigia_em': None, 'alheio_hist': []}
        _CACHE_JSON[ck] = (now_ts, res)
        return res
    if prov in ('cw', 'gemini'):
        if prov == 'gemini':
            contas = dados_gemini()
        else:
            agora = datetime.datetime.now(datetime.timezone.utc)
            db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=10)
            u = uso_conexoes(db, ('claude-web',))
            contas = ordenar_generico([linha_uso(c, u.get(c[0]), 'Sonnet 5.5 web', agora) for c in conexoes(db, 'claude-web')])
            db.close()
        meta['nota'] = 'Sem medição de cota: o estado vem do que os pedidos reais deram nas últimas 24 h.'
        res = {**meta, 'contas': contas, 'lida': 'último pedido', 'vigia_em': None, 'alheio_hist': []}
        _CACHE_JSON[ck] = (now_ts, res)
        return res
    base = 'antigravity' if prov in ('ag55', 'ag46') else 'claude' if prov == 'fable' else prov
    linhas, _ = dados(base)
    if base == 'antigravity':
        linhas = [l for l in linhas if l['modelo'] == ('Opus 5.5' if prov == 'ag55' else 'Opus 4.6')]
    db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=10)
    hist = {}
    if incluir_hist and 'hist' not in cfg.get('esc', []):
        for cid, h, p in db.execute(
                "SELECT connection_id, substr(created_at,1,13), min(remaining_percentage) FROM quota_snapshots "
                "WHERE provider=? AND window_key LIKE '%7d%' AND created_at > ? GROUP BY 1, 2 ORDER BY 2",
                (base, isoz(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)))):
            hist.setdefault(cid, []).append([h, p])
    uso = uso_conexoes(db, (base,), {'ag55': 'claude-opus-5-5%', 'ag46': 'claude-opus-4-6%', 'fable': 'claude-fable%'}.get(prov))
    sem_cota_fable, limite = {}, {}
    if prov == 'fable':
        sem_cota_fable = dict(db.execute(
            "SELECT connection_id, max(timestamp) FROM usage_history WHERE provider='claude' AND model LIKE 'claude-fable%' "
            "AND CAST(status AS INTEGER)=429 AND connection_id IS NOT NULL GROUP BY 1"))
        limite = dict(db.execute("SELECT id, rate_limited_until FROM provider_connections WHERE provider='claude'"))
    db.close()
    try:
        vig = json.load(open('/opt/omniroute/vigia_uso_alheio.json')).get(prov, {})
    except Exception:
        vig = {}
    quem = {c['id']: c for c in vig.get('contas', [])}
    try:
        oi = json.load(open('/opt/omniroute/probe_opus_voltas.json'))
    except Exception:
        oi = {}
    iso = lambda d: d.isoformat() if d else None
    out = []
    for l in linhas:
        v = quem.get(l['id'], {})
        u = uso.get(l['id']) or (0, 0, 0, None, None, 0, None)
        fl = u[5] or 0
        ult_ok = u[3]
        ult_err = u[6]
        voltou = ult_ok if (ult_err and ult_ok and ult_ok > ult_err) else None
        extra = {}
        if prov == 'fable':
            ok, tot = u[0] or 0, u[1] or 0
            s429 = sem_cota_fable.get(l['id'])
            rl = dt(limite.get(l['id']))
            agora = datetime.datetime.now(datetime.timezone.utc)
            info = 'nunca' if not s429 else br(dt(s429)) + (' · já voltou' if ult_ok and ult_ok > s429 else '')
            g, lib = l['grupo'], l['libera']
            if rl and rl > agora and l['ativa']:  # limite curto da conta ("reset after 5m"): volta na hora marcada
                g, lib = 1, max(rl, lib) if lib else rl
                info += f' · limite até {br(rl)}'
            extra = dict(modelo='Fable 5.2', taxa=round(100 * ok / tot) if tot else None, ok=ok, tot=tot, info=info,
                         grupo=g, libera=iso(lib), oi=None)
        out.append({**{k: l[k] for k in ('id', 'nome', 'ativa', 'ps', 'p5', 'pri', 'primeira', 'grupo', 'err', 'st')},
                    'rs': iso(l['rs']), 'r5': iso(l['r5']), 'libera': iso(l['libera']), 'quando': iso(l['quando']),
                    'liberando': liberando.get(l['id']), 'hist': hist.get(l['id'], []),
                    'uso3h': u[2] or 0, 'uso24h': u[1] or 0,
                    'quem': v.get('quem'), 'alheio': v.get('alheio'), 'queda3h': v.get('queda'), 'modelo': l['modelo'],
                    'oi': oi.get(str(l['nome']).split('@')[0]),
                    'falhas': fl, 'voltou': voltou, **extra})
    if prov == 'fable':
        ordenar_generico(out)
    alheio_hist = [h for h in vig.get('historico', [])][-40:]
    res = {**meta, 'contas': out, 'lida': 'lida', 'vigia_em': vig.get('em'), 'alheio_hist': alheio_hist}
    _CACHE_JSON[ck] = (now_ts, res)
    return res


PAGINA_NOVA = r'''<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark light"><meta name="color-scheme" content="dark light"><meta name="color-scheme" content="dark light"><title>Créditos das contas</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root{--bg:0 0% 0%;--fg:0 0% 95%;--card:0 0% 4%;--muted:220 13% 22%;--mfg:220 10% 72%;--border:220 13% 20%;
 --primary:152 70% 45%;--warn:38 92% 55%;--bad:0 72% 55%;--alh:330 80% 65%;--pri2:240 80% 72%;--radius:14px}
:root[data-tema="claro"]{--bg:0 0% 98%;--fg:240 10% 4%;--card:0 0% 100%;--muted:240 5% 94%;--mfg:240 4% 42%;
 --border:240 6% 88%;--primary:152 60% 38%;--alh:330 70% 45%;--pri2:240 60% 50%}
*{box-sizing:border-box}html,body{margin:0}
body{background:hsl(var(--bg));color:hsl(var(--fg));font:14px/1.5 'Plus Jakarta Sans',system-ui,sans-serif;padding:20px 16px 40px;
 background-image:radial-gradient(1200px 500px at 10% -10%,hsl(var(--primary)/.10),transparent 60%),
 radial-gradient(900px 400px at 110% 0,hsl(var(--pri2)/.08),transparent 60%);background-attachment:fixed}
.pg{max-width:1280px;margin:0 auto}
.top{display:flex;justify-content:space-between;align-items:flex-end;gap:14px;flex-wrap:wrap;margin-bottom:18px}
h1{font-size:22px;margin:0;font-weight:800;letter-spacing:-.01em}h1 em{font-style:normal;color:hsl(var(--primary))}
.sub{color:hsl(var(--mfg));font-size:12.5px;margin-top:2px}
.abas{display:flex;gap:6px;flex-wrap:wrap}
.aba{padding:7px 14px;border:1px solid hsl(var(--border));border-radius:999px;color:hsl(var(--fg));text-decoration:none;
 background:hsl(var(--card));font-weight:600;font-size:13px;transition:.15s}
.aba:hover{border-color:hsl(var(--primary)/.6)}.aba.on{background:hsl(var(--primary));border-color:hsl(var(--primary));color:#fff}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:16px}
.card{background:hsl(var(--card));border:1px solid hsl(var(--border));border-radius:var(--radius);padding:14px 16px;position:relative;overflow:hidden}
.card:after{content:"";position:absolute;right:-30px;bottom:-40px;width:110px;height:110px;border-radius:50%;background:hsl(var(--primary)/.07)}
.card b{display:block;font-size:26px;font-weight:800;line-height:1.15;letter-spacing:-.02em}
.card span{color:hsl(var(--mfg));font-size:12px;position:relative}
.card.ok b{color:hsl(var(--primary))}.card.zero b{color:hsl(var(--bad))}.card.alh b{color:hsl(var(--alh))}
.barra{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
input,select,button{font:inherit;font-size:13px;padding:8px 12px;border:1px solid hsl(var(--border));border-radius:10px;
 background:hsl(var(--card));color:hsl(var(--fg))}
#q{flex:1 1 240px;min-width:0}input:focus{outline:2px solid hsl(var(--primary)/.5);outline-offset:1px}
button{cursor:pointer;font-weight:600;transition:.15s}button:hover{border-color:hsl(var(--primary)/.6)}
button.pri{border-color:hsl(var(--primary)/.6);color:hsl(var(--primary))}button.pri:hover{background:hsl(var(--primary));color:#fff}
.chip{padding:7px 13px;border-radius:999px;border:1px solid hsl(var(--border));background:hsl(var(--card));cursor:pointer;
 font-size:12.5px;font-weight:600;user-select:none}
.chip.on{background:hsl(var(--fg));color:hsl(var(--bg));border-color:hsl(var(--fg))}
.lbl{display:flex;align-items:center;gap:6px;color:hsl(var(--mfg));font-size:12.5px}
.lbl input{flex:none;padding:0;width:16px;height:16px;accent-color:hsl(var(--primary))}
.wrap{overflow-x:auto;background:hsl(var(--card));border:1px solid hsl(var(--border));border-radius:var(--radius)}
table{border-collapse:collapse;width:100%}
th,td{padding:11px 14px;border-bottom:1px solid hsl(var(--border)/.7);text-align:left;vertical-align:middle}
tbody tr:last-child td{border-bottom:0}
th{font-size:11.5px;color:hsl(var(--mfg));font-weight:700;text-transform:uppercase;letter-spacing:.04em;cursor:pointer;
 user-select:none;white-space:nowrap;background:hsl(var(--muted)/.35)}
th:hover{color:hsl(var(--fg))}th .s{color:hsl(var(--primary))}
tbody tr{transition:background .12s}tbody tr:hover td{background:hsl(var(--primary)/.05)}
tr.off td{opacity:.5}.n{font-weight:700;min-width:230px;word-break:break-word}.n small{display:block;font-weight:500}
.n small.err{max-width:260px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.b{position:relative;height:20px;width:140px;background:hsl(var(--muted));border-radius:6px;overflow:hidden}
.b i{display:block;height:100%;border-radius:6px}
.b span{position:absolute;left:8px;top:0;font-size:11.5px;line-height:20px;font-weight:800;color:#fff;text-shadow:0 1px 2px #0008}
small{color:hsl(var(--mfg));font-size:11.5px}.err{color:hsl(var(--bad))}.velho{color:hsl(var(--bad));font-weight:700}
.tag{display:inline-block;padding:3px 10px;border-radius:999px;font-size:11.5px;font-weight:700;white-space:nowrap}
.t-alh{background:hsl(var(--alh)/.15);color:hsl(var(--alh))}.t-nos{background:hsl(var(--pri2)/.15);color:hsl(var(--pri2))}
.t-nin,.t-sem{background:hsl(var(--muted));color:hsl(var(--mfg))}.t-esg{background:hsl(var(--bad)/.14);color:hsl(var(--bad))}
.prim{color:hsl(var(--primary));font-weight:800;white-space:nowrap}svg.sp{display:block}
.acs{display:flex;gap:6px;flex-wrap:wrap;align-items:center;min-width:150px}
.foot{margin-top:16px}.hl{background:hsl(var(--card));border:1px solid hsl(var(--border));border-radius:var(--radius);padding:14px 16px}
.hl h3{margin:0 0 6px;font-size:14px;font-weight:800}.hl ul{margin:8px 0 0;padding-left:18px}
.hl li{font-size:12.5px;color:hsl(var(--mfg));margin:2px 0}
.toast{position:fixed;left:50%;bottom:20px;transform:translateX(-50%);background:hsl(var(--primary));color:#fff;padding:11px 16px;
 border-radius:12px;display:none;max-width:min(420px,92vw);font-weight:600;box-shadow:0 10px 30px #0006;z-index:9}
.tema{margin-left:auto}
/* celular: cada conta vira um cartão, sem rolagem lateral */
@media (max-width:820px){
 body{padding:14px 12px 30px}h1{font-size:19px}.cards{grid-template-columns:repeat(2,1fr);gap:8px}.card b{font-size:21px}
 .wrap{background:none;border:0;overflow:visible}table,thead,tbody,tr,td{display:block;width:100%}thead{display:none}
 tbody tr{background:hsl(var(--card));border:1px solid hsl(var(--border));border-radius:var(--radius);margin-bottom:10px;padding:6px 4px}
 td{border:0;padding:6px 12px;display:flex;justify-content:space-between;align-items:center;gap:10px}
 td:before{content:attr(data-r);color:hsl(var(--mfg));font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.03em;flex:none}
 td.n{display:block;font-size:15px;border-bottom:1px solid hsl(var(--border)/.7);padding-bottom:10px;margin-bottom:4px;min-width:0}
 td.n:before{display:none}.n small.err{max-width:100%}
 td>div,td>.b,td>span,td>svg{margin-left:auto;text-align:right}.b{width:120px}.acs{justify-content:flex-end;min-width:0}
 .tema{margin-left:0}
}
@media (min-width:821px){td[data-r="Libera em"] b,td[data-r="Libera em"] small{white-space:nowrap}
 td[data-r="Libera em"] small{display:block}.acs{flex-wrap:nowrap}td[data-r=""]{white-space:nowrap}
 th,td{padding:10px 9px}.b{width:120px}}
td[data-r^="Modelo"] small{display:block}td[data-r="Libera em"]{min-width:118px}
.n .acs{margin-top:7px;min-width:0}.n .acs button{padding:4px 10px;font-size:12px;font-weight:600}
@media (min-width:821px){.n{min-width:190px;max-width:250px}td[data-r="Quem usa"] small{display:block;max-width:140px}.b{width:96px}svg.sp{width:96px}}
@media (min-width:821px) and (max-width:1180px){th[data-k="hist"],td[data-r="3 dias"]{display:none}}

</style></head><body>
<div class="pg"><div class="pg"><div class="pg"><div class="top"><div><h1 id="tit">Créditos das contas</h1><div class="sub" id="sub">carregando…</div></div><div class="abas" id="abas"></div></div>
<div class="cards" id="cards"></div>
<div class="barra"><input id="q" placeholder="buscar conta…">
<span class="chip on" data-f="todas">todas</span><span class="chip" data-f="credito">com crédito</span><span class="chip" data-f="esperando">esperando</span>
<span class="chip" data-f="alheio">usadas por outra pessoa</span><span class="chip" data-f="off">desligadas</span>
<label class="lbl"><input type="checkbox" id="auto" checked> atualizar sozinho (30 s)</label><button class="tema" id="tema">claro / escuro</button></div>
<div class="wrap"><table><thead><tr id="cab"></tr></thead><tbody id="corpo"></tbody></table></div>
<div class="foot"><div class="hl"><h3>Quem está usando (vigia a cada 15 min)</h3><div class="sub">Compara quanto a semana de cada conta caiu nas últimas 3 h com quantos pedidos NÓS fizemos por ela. Caiu mais do que o nosso uso explica = outra pessoa usando: essa conta vai para o começo da fila (gastamos antes dele). As que ninguém mais usa ficam por último. Só lê o banco do OmniRoute, nenhuma conta é consultada.</div><ul id="alh"></ul></div></div>
</div></div></div><div class="toast" id="toast"></div>
<script>
const K=new URLSearchParams(location.search).get('k'),P=new URLSearchParams(location.search).get('p')||'claude';
let D=null,ORD={k:'ordem',d:1},F='todas';
const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const dias=['dom','seg','ter','qua','qui','sex','sáb'];
const br=s=>{if(!s)return'—';const d=new Date(s);return dias[d.getDay()]+' '+d.toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})};
const falta=s=>{if(!s)return'';let m=(new Date(s)-Date.now())/6e4;if(m<=0)return'agora';const h=Math.floor(m/60);return h>=24?`${Math.floor(h/24)}d ${h%24}h`:`${h}h ${String(Math.floor(m%60)).padStart(2,'0')}min`};
const cor=p=>p>30?'hsl(var(--primary))':p>0?'hsl(var(--warn))':'hsl(var(--bad))';
const barra=(p,r)=>p==null?'<small>sem dado</small>':`<div class="b"><i style="width:${Math.max(p,0)}%;background:${cor(p)}"></i><span>${Math.round(p)}%</span></div><small>${r?'volta '+br(r):''}</small>`;
const spark=h=>{if(!h||h.length<2)return'<small>—</small>';const w=96,ht=28,xs=h.map((_,i)=>i*w/(h.length-1)),ys=h.map(x=>ht-2-(x[1]??0)*(ht-4)/100);
 return `<svg class="sp" width="${w}" height="${ht}"><polyline fill="none" stroke="hsl(var(--primary))" stroke-width="1.6" points="${xs.map((x,i)=>x.toFixed(1)+','+ys[i].toFixed(1)).join(' ')}"/></svg><small>3 dias: ${Math.round(h[0][1])}% → ${Math.round(h[h.length-1][1])}%</small>`};
const QUEM={'outra pessoa usando':['t-alh','outra pessoa usando'],'alheio (1ª vez)':['t-alh','talvez outra pessoa'],'só nós':['t-nos','só nós'],'ninguém':['t-nin','ninguém'],'sem leitura':['t-sem','sem leitura'],'esgotada':['t-esg','esgotada']};
const TODAS=[{k:'nome',t:'Conta'},{k:'modelo',t:'Modelo · último oi'},{k:'ps',t:'Semana'},{k:'p5',t:'Janela 5 h'},{k:'hist',t:'Últimos 3 dias',sem:1},{k:'quem',t:'Quem usa'},{k:'taxa',t:'Deu certo (24 h)'},{k:'falhas',t:'Falhas (24 h)'},{k:'info',t:'Situação'},{k:'uso3h',t:'Pedidos 3h/24h'},{k:'libera',t:'Libera em'}];
let COLS=TODAS;
const tx=c=>c.taxa==null?'<small>sem pedidos</small>':`<div class="b"><i style="width:${c.taxa}%;background:${cor(c.taxa)}"></i><span>${c.taxa}%</span></div><small>${c.ok} de ${c.tot}</small>`;
function cab(){$('cab').innerHTML=COLS.map(c=>`<th data-k="${c.k}">${c.t}${ORD.k===c.k?` <span class="s">${ORD.d>0?'▲':'▼'}</span>`:''}</th>`).join('');
 document.querySelectorAll('#cab th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(COLS.find(c=>c.k===k).sem)return;ORD=ORD.k===k?{k,d:-ORD.d}:{k,d:k==='nome'?1:-1};desenhar()})}
function filtro(c){if(F==='credito')return c.grupo===0;if(F==='esperando')return c.grupo===1;if(F==='alheio')return/alheio|outra/.test(c.quem||'');if(F==='off')return!c.ativa;return true}
function desenhar(){if(!D)return;const q=$('q').value.toLowerCase();
 let L=D.contas.filter(c=>filtro(c)&&(!q||c.nome.toLowerCase().includes(q)));
 if(ORD.k!=='ordem')L.sort((a,b)=>{const x=a[ORD.k],y=b[ORD.k];if(x==null)return 1;if(y==null)return-1;return(x>y?1:x<y?-1:0)*ORD.d});
 cab();const ag=Date.now();
 $('corpo').innerHTML=L.map(c=>{const idade=c.quando?(ag-new Date(c.quando))/6e4:null,qm=QUEM[c.quem]||['t-sem',c.quem||'—'];
  const esg=c.grupo===1?`<small class="err">ESGOTADA (${c.ps!=null&&c.ps<=0?'semana':'janela de 5 h'})</small>`:'';
  let ac=c.liberando?`<small style="color:hsl(var(--warn))">${esc(c.liberando)}</small>`:'';
  if(c.ativa&&!c.liberando&&c.id&&D.oi)ac=(c.primeira?'<span class="prim">★ usando primeiro</span> ':`<button class="pri" onclick="acao('priorizar','${c.id}','${esc(c.nome)}')">usar primeiro</button> `)+`<button onclick="acao('liberar','${c.id}','${esc(c.nome)}')">liberar</button>`;
  const lida=D.lida==='lida pelo PC'?'':`${D.prov==='cw'||D.prov==='gemini'?'último pedido':'lida'} ${idade==null?'nunca':idade<1?'agora':idade<120?'há '+Math.round(idade)+' min':'há '+Math.round(idade/60)+' h'}`;
  const cel={nome:`<td class="n" data-r="Conta">${esc(c.nome)}${esg}${c.ativa?`<small>${c.id&&D.oi?'prioridade '+c.pri+' · ':''}<span class="${D.oi&&(idade==null||idade>20)?'velho':''}">${lida}</span></small>`:'<small>desligada</small>'}${c.err&&(c.st!=='active'||!c.ativa)?`<small class="err" title="${esc(c.err)}">${esc(c.err.slice(0,70))}</small>`:''}${ac?`<div class="acs">${ac}</div>`:''}</td>`,
   modelo:`<td data-r="Modelo"><div><b>${esc(c.modelo)}</b>${D.oi?(c.oi?`<small class="${c.oi.ultimo==='viva'?'':'err'}">oi: ${esc(c.oi.ultimo)} ${br(c.oi.ultimo_em+'Z')}</small>`:'<small>sem oi ainda</small>')+(c.oi&&c.oi.voltou_em?`<small>voltou ${br(c.oi.voltou_em+'Z')}</small>`:''):''}</div></td>`,
   ps:`<td data-r="Semana">${barra(c.ps,c.rs)}</td>`,p5:`<td data-r="Janela 5 h">${barra(c.p5,c.r5)}</td>`,hist:`<td data-r="3 dias">${spark(c.hist)}</td>`,
   quem:`<td data-r="Quem usa"><div><span class="tag ${qm[0]}">${esc(qm[1])}</span>${c.alheio?`<small>${c.alheio} pontos a mais que o nosso uso (3 h)</small>`:''}</div></td>`,
   taxa:`<td data-r="Deu certo">${tx(c)}</td>`,falhas:`<td data-r="Falhas">${c.falhas?`<b class="err">${c.falhas}</b>${c.voltou?` <small>voltou ${br(c.voltou)}</small>`:(c.tot?'<small class="err">não voltou ainda</small>':'')}`:'<small>0</small>'}</td>`,info:`<td data-r="Situação"><small>${esc(c.info||'—')}</small></td>`,
   uso3h:`<td data-r="Pedidos 3 h / 24 h"><span><b>${c.uso3h}</b> / ${c.uso24h}</span></td>`,
   libera:`<td data-r="Libera em"><div>${c.grupo===1&&c.libera?`<b>${br(c.libera)}</b> <small>em ${falta(c.libera)}</small>`:'—'}</div></td>`};
  return `<tr class="${c.ativa?'':'off'}">${COLS.map(x=>cel[x.k]).join('')}</tr>`}).join('')||`<tr><td colspan="${COLS.length}"><small>nenhuma conta neste filtro</small></td></tr>`;
 const t=g=>D.contas.filter(c=>c.grupo===g).length,alh=D.contas.filter(c=>c.quem==='outra pessoa usando').length;
 const ativas=D.contas.filter(c=>c.ativa&&c.ps!=null),media=ativas.length?Math.round(ativas.reduce((a,c)=>a+c.ps,0)/ativas.length):0;
 const prox=D.contas.filter(c=>c.grupo===1&&c.libera).sort((a,b)=>a.libera>b.libera?1:-1)[0];
 const esc_=k=>D.esc.includes(k);
 $('cards').innerHTML=`<div class="card ok"><b>${t(0)}</b><span>com crédito agora</span></div><div class="card zero"><b>${t(1)}</b><span>esperando liberar</span></div>
  <div class="card"><b>${t(2)}</b><span>sem leitura / sem uso</span></div>`+(esc_('ps')?'':`<div class="card"><b>${media}%</b><span>média que resta (ativas)</span></div>`)+
  `<div class="card"><b>${prox?falta(prox.libera):'—'}</b><span>próxima a liberar${prox?': '+esc(prox.nome.split('@')[0]):''}</span></div>`+
  (esc_('quem')?'':`<div class="card alh"><b>${alh}</b><span>usadas por outra pessoa agora</span></div>`)+
  (esc_('uso3h')?`<div class="card"><b>${D.contas.length}</b><span>contas</span></div>`:`<div class="card"><b>${D.contas.reduce((a,c)=>a+c.uso3h,0)}</b><span>nossos pedidos nas últimas 3 h</span></div>`)+
  (esc_('falhas')?'':(()=>{const tf=D.contas.reduce((a,c)=>a+(c.falhas||0),0),tv=D.contas.filter(c=>c.falhas&&c.voltou).length,tn=D.contas.filter(c=>c.falhas&&!c.voltou).length;return `<div class="card${tf?' zero':''}"><b>${tf}</b><span>falhas (24 h)${tv?` · ${tv} voltaram`:''}${tn?` · <b class="err">${tn} sem voltar</b>`:''}</span></div>`})());
 $('sub').textContent=`Atualizado ${new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}`+(D.nota?' · '+D.nota:(D.vigia_em?` · o OmniRoute mede cada conta a cada ~5 min · vigia de uso alheio: ${br(D.vigia_em)}`:' · o OmniRoute mede cada conta a cada ~5 min'));
 document.querySelector('.foot').style.display=esc_('quem')?'none':'';
 $('alh').innerHTML=(D.alheio_hist||[]).slice().reverse().slice(0,12).map(h=>`<li>${br(h.em)} — <b>${esc(h.nome)}</b>: ${h.alheio} pontos a mais (nossos pedidos: ${h.nosso})</li>`).join('')||'<li>nenhum uso alheio detectado ainda</li>'}
async function carregar(){try{const r=await fetch(`dados?k=${K}&p=${P}`);D=await r.json();$('tit').innerHTML='Créditos das contas — <em>'+esc(D.titulo)+'</em>';
 COLS=TODAS.filter(c=>!D.esc.includes(c.k)).map(c=>({...c,t:(D.rot||{})[c.k]||c.t}));
 $('abas').innerHTML=D.provs.map(([p,t])=>`<a class="aba${p===D.prov?' on':''}" href="?k=${K}&p=${p}">${esc(t)}</a>`).join('');desenhar()}catch(e){$('sub').textContent='sem conexão com o painel: '+e}}
async function acao(tipo,id,nome){const msg=tipo==='priorizar'?`Usar ${nome} primeiro?`:`Liberar ${nome}?\nDesliga e religa só esta conta (~6 min).`;if(!confirm(msg))return;
 const t=await(await fetch(`${tipo}?k=${K}&id=${id}`,{method:'POST'})).text();const el=$('toast');el.textContent=t;el.style.display='block';setTimeout(()=>el.style.display='none',6000);carregar()}
document.querySelectorAll('.chip').forEach(ch=>ch.onclick=()=>{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));ch.classList.add('on');F=ch.dataset.f;desenhar()});
$('q').oninput=desenhar;try{if(localStorage.tema)document.documentElement.dataset.tema=localStorage.tema}catch(e){}
$('tema').onclick=()=>{const t=document.documentElement.dataset.tema==='claro'?'':'claro';document.documentElement.dataset.tema=t;try{localStorage.tema=t}catch(e){}};try{if(localStorage.tema)document.documentElement.dataset.tema=localStorage.tema}catch(e){}
$('tema').onclick=()=>{const t=document.documentElement.dataset.tema==='claro'?'':'claro';document.documentElement.dataset.tema=t;try{localStorage.tema=t}catch(e){}};try{if(localStorage.tema)document.documentElement.dataset.tema=localStorage.tema}catch(e){}
$('tema').onclick=()=>{const t=document.documentElement.dataset.tema==='claro'?'':'claro';document.documentElement.dataset.tema=t;try{localStorage.tema=t}catch(e){}};carregar();setInterval(()=>{if($('auto').checked)carregar()},30000);
</script></body></html>'''


def br(d, curto=False):
    if not d: return '—'
    d = d.astimezone(BR)
    dias = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']
    return f"{dias[d.weekday()]} {d:%d/%m %H:%M}"

def falta(d):
    if not d: return ''
    s = (d - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    if s <= 0: return 'agora'
    h, m = int(s // 3600), int(s % 3600 // 60)
    return f"{h // 24}d {h % 24}h" if h >= 24 else f"{h}h {m:02d}min"

def barra(p):
    if p is None: return '<span class="nd">sem dado</span>'
    c = 'ok' if p > 30 else ('meio' if p > 0 else 'zero')
    return (f'<div class="b"><div class="f {c}" style="width:{max(p, 0):.0f}%"></div><span>resta {p:.0f}%</span></div>'
            f'<small>usado {100 - p:.0f}%</small>')

def pagina(prov):
    linhas, provs = dados(prov)
    agora = datetime.datetime.now(datetime.timezone.utc)
    nomes_g = {0: 'Com crédito agora', 1: 'Sem crédito — próximas a liberar', 2: 'Sem leitura de crédito', 3: 'Desligadas'}
    tot = {g: sum(1 for l in linhas if l['grupo'] == g) for g in range(4)}
    abas = ''.join(f'<a class="aba{" on" if p == prov else ""}" href="?k={CHAVE}&p={p}">{p}</a>' for p in provs)
    corpo = ''
    g_ant = None
    for l in linhas:
        if l['grupo'] != g_ant:
            g_ant = l['grupo']
            corpo += f'<tr class="g"><td colspan="7">{nomes_g[g_ant]} ({tot[g_ant]})</td></tr>'
        idade = (agora - l['quando']).total_seconds() / 60 if l['quando'] else None
        velho = idade is None or idade > 20
        lib = ''
        if l['grupo'] == 1 and l['libera']:
            lib = f'<b>{br(l["libera"])}</b><br><small>em {falta(l["libera"])}</small>'
        estado = ''
        if l['id'] in liberando: estado = f'<small class="lib">{liberando[l["id"]]}</small>'
        elif l['ativa']:
            if l['primeira']: estado = '<b class="prim">★ usando primeiro</b> '
            else: estado = f'<button class="pri" onclick="priorizar(\'{l["id"]}\',\'{html.escape(l["nome"])}\')">usar primeiro</button> '
            estado += f'<button onclick="liberar(\'{l["id"]}\',\'{html.escape(l["nome"])}\')">liberar</button>'
        if l['ativa']: estado += f'<small>prioridade {l["pri"]}</small>'
        if l['err'] and (l['st'] != 'active' or not l['ativa']): estado += f'<br><small class="err">{html.escape(l["err"][:60])}</small>'
        aviso = ''
        if l['grupo'] == 1:
            qual = 'semana' if (l['ps'] is not None and l['ps'] <= 0) else 'janela de 5 h'
            aviso = f'<small class="err">ESGOTADA ({qual}) — não responde até {br(l["libera"])}</small>'
        corpo += (f'<tr class="g{l["grupo"]}"><td class="n">{html.escape(l["nome"])}{aviso}</td>'
                  f'<td>{barra(l["ps"])}<small>{"volta " + br(l["rs"]) if l["rs"] else ""}</small></td>'
                  f'<td>{barra(l["p5"])}<small>{"volta " + br(l["r5"]) if l["r5"] else ""}</small></td>'
                  f'<td>{lib}</td>'
                  f'<td class="{"velho" if velho else ""}">{"há %d min" % idade if idade is not None else "nunca"}</td>'
                  f'<td>{estado}</td></tr>')
    return f'''<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Créditos OmniRoute</title>
<meta http-equiv="refresh" content="60">
<style>
:root{{--bg:#f6f7f9;--fg:#1c1f24;--card:#fff;--lin:#e3e6ea;--sub:#6b7280;--ok:#22a06b;--meio:#d9a400;--zero:#d64545}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14161a;--fg:#e6e8eb;--card:#1d2026;--lin:#2c3038;--sub:#9aa1ab}}}}
body{{background:var(--bg);color:var(--fg);font:14px system-ui,Segoe UI,sans-serif;margin:0;padding:16px}}
h1{{font-size:18px;margin:0 0 4px}} .sub{{color:var(--sub);margin-bottom:12px}}
.abas{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}}
.aba{{padding:4px 10px;border:1px solid var(--lin);border-radius:14px;color:var(--fg);text-decoration:none}}
.aba.on{{background:var(--fg);color:var(--bg)}}
.wrap{{overflow-x:auto;background:var(--card);border:1px solid var(--lin);border-radius:8px}}
table{{border-collapse:collapse;width:100%;min-width:760px}}
th,td{{padding:7px 10px;border-bottom:1px solid var(--lin);text-align:left;vertical-align:middle}}
th{{font-size:12px;color:var(--sub);font-weight:600}}
tr.g td{{background:var(--bg);font-weight:600;font-size:13px}}
tr.g3,tr.g2{{opacity:.6}} .n{{font-weight:500;word-break:break-all}}
.b{{position:relative;height:16px;width:130px;background:var(--lin);border-radius:3px;overflow:hidden}}
.f{{height:100%}} .f.ok{{background:var(--ok)}} .f.meio{{background:var(--meio)}} .f.zero{{background:var(--zero)}}
.b span{{position:absolute;left:6px;top:0;font-size:11px;line-height:16px;font-weight:600;color:var(--fg)}}
small{{color:var(--sub);display:block}} .velho{{color:var(--zero)}} .err{{color:var(--zero)}} .lib{{color:var(--meio)}} .nd{{color:var(--sub)}}
.prim{{color:var(--ok)}} button.pri{{border-color:var(--ok);color:var(--ok)}}
button{{font:inherit;font-size:12px;padding:3px 9px;border:1px solid var(--lin);border-radius:5px;background:var(--card);color:var(--fg);cursor:pointer}}
</style></head><body>
<h1>Créditos das contas — {html.escape(prov)}</h1>
<div class="sub">Lido agora ({br(agora)}, horário de Brasília) do banco do OmniRoute, que mede cada conta a cada ~5 min.
Página atualiza sozinha a cada 1 min. "Leitura" vermelha = a medição daquela conta está velha (&gt; 20 min).
<b>{tot[0]}</b> com crédito · <b>{tot[1]}</b> esperando · <b>{tot[3]}</b> desligadas</div>
<div class="abas">{abas}</div>
<div class="wrap"><table><tr><th>Conta</th><th>Semana (barra = quanto resta)</th><th>Janela 5 h (barra = quanto resta)</th><th>Libera em</th><th>Leitura</th><th></th></tr>
{corpo}</table></div>
<script>
function priorizar(id,nome){{
 if(!confirm('Usar '+nome+' primeiro?'))return;
 fetch('priorizar?k={CHAVE}&id='+id,{{method:'POST'}}).then(r=>r.text()).then(t=>{{alert(t);location.reload()}});
}}
function liberar(id,nome){{
 if(!confirm('Liberar '+nome+'?\\nDesliga e religa só esta conta (~6 min) para o OmniRoute esquecer o "sem crédito" velho.'))return;
 fetch('liberar?k={CHAVE}&id='+id,{{method:'POST'}}).then(r=>r.text()).then(t=>{{alert(t);location.reload()}});
}}
</script></body></html>'''

def pagina_gemini():
    # Google AI Studio (provider 'gemini', chaves de API): o Google nao informa cota em %, entao mostra o que os
    # pedidos reais deram nas ultimas 24 h (so le usage_history; nao chama nenhuma chave).
    db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=10)
    contas = db.execute("""SELECT p.id, coalesce(p.email,p.name), p.is_active, coalesce(p.last_error,''), coalesce(p.priority,999),
        sum(u.status='200'), sum(u.status='429'), sum(u.status NOT IN ('200','429')), max(CASE WHEN u.status='200' THEN u.timestamp END),
        max(u.timestamp)
        FROM provider_connections p LEFT JOIN usage_history u ON u.connection_id=p.id AND u.timestamp > datetime('now','-1 day')
        WHERE p.provider='gemini' GROUP BY p.id""").fetchall()
    modelos = db.execute("""SELECT model, sum(status='200'), sum(status='429'), sum(status='404'), count(DISTINCT connection_id)
        FROM usage_history WHERE provider='gemini' AND timestamp > datetime('now','-3 days') GROUP BY 1
        ORDER BY 2 DESC, 3""").fetchall()
    provs = [r[0] for r in db.execute("SELECT DISTINCT provider FROM quota_snapshots WHERE created_at > datetime('now','-1 day') ORDER BY 1")]
    db.close()
    provs.append('gemini')
    agora = datetime.datetime.now(datetime.timezone.utc)
    abas = ''.join(f'<a class="aba{" on" if p == "gemini" else ""}" href="?k={CHAVE}&p={p}">{p}</a>' for p in provs)
    def ordem(c):
        ok, cota = c[5] or 0, c[6] or 0
        return (0 if c[2] and c[8] else 1 if c[2] else 2, -(c[8] or ''.__len__()), c[8] or '', -ok)
    contas = sorted(contas, key=lambda c: (0 if c[2] and c[8] else 1 if c[2] else 2, ''.join(chr(255 - ord(x)) for x in (c[8] or ''))))
    linhas = ''
    for cid, nome, ativa, err, pri, ok, cota, outro, ult_ok, ult in contas:
        ok, cota, outro = ok or 0, cota or 0, outro or 0
        tot = ok + cota + outro
        taxa = (100 * ok / tot) if tot else None
        u = dt(ult_ok)
        quando = ''
        if u:
            m = (agora - u).total_seconds() / 60
            quando = f'há {m:.0f} min' if m < 120 else f'há {m / 60:.0f} h'
        bt = (f'<div class="b"><div class="f {"ok" if taxa > 30 else "meio" if taxa > 0 else "zero"}" style="width:{taxa:.0f}%"></div>'
              f'<span>{taxa:.0f}% deu certo</span></div>') if taxa is not None else '<span class=nd>sem pedidos</span>'
        linhas += (f'<tr class="g{0 if ativa else 3}"><td class="n">{html.escape(nome)}</td>'
                   f'<td>{bt}</td>'
                   f'<td>{ok}</td><td>{cota}</td><td>{outro}</td><td>{quando or "—"}</td>'
                   f'<td><small class="err">{html.escape(err[:70])}</small></td></tr>')
    lm = ''
    for mod, ok, cota, sumiu, ncont in modelos:
        if ok: st = '<b style="color:var(--ok)">funciona</b>'
        elif sumiu and not cota: st = '<b class="err">não existe mais p/ contas novas</b>'
        else: st = '<b class="err">sem cota grátis (precisa faturamento)</b>'
        lm += f'<tr><td class="n">{html.escape(mod)}</td><td>{st}</td><td>{ok}</td><td>{cota}</td><td>{sumiu}</td><td>{ncont}</td></tr>'
    css = pagina('claude').split('<style>')[1].split('</style>')[0]
    return f'''<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Créditos OmniRoute</title>
<meta http-equiv="refresh" content="60"><style>{css}</style></head><body>
<h1>Google AI Studio (gemini) — {len(contas)} chaves</h1>
<div class="sub">O Google não informa a cota em %. Esta aba mostra o que os pedidos reais deram nas últimas 24 h
(barra = % de pedidos que deram certo). Nada aqui chama as chaves. Atualizado {br(agora)}.</div>
<div class="abas">{abas}</div>
<div class="wrap"><table><tr><th>Chave</th><th>Deu certo (24 h)</th><th>OK</th><th>Sem cota</th><th>Outros erros</th><th>Último OK</th><th>Último erro</th></tr>
{linhas}</table></div>
<h1 style="margin-top:18px">Modelos nas chaves do AI Studio (3 dias)</h1>
<div class="wrap"><table><tr><th>Modelo</th><th>Situação</th><th>OK</th><th>Sem cota</th><th>Sumiu (404)</th><th>Chaves que tentaram</th></tr>
{lm}</table></div></body></html>'''

def api_login():
    pw = subprocess.run(['docker', 'exec', 'omniroute', 'printenv', 'INITIAL_PASSWORD'], capture_output=True, text=True).stdout.strip()
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.open(urllib.request.Request('http://localhost:20128/api/auth/login', data=json.dumps({'password': pw}).encode(),
                                   headers={'content-type': 'application/json'}), timeout=30)
    return op

def ativar(op, cid, valor):
    req = urllib.request.Request(f'http://localhost:20128/api/providers/{cid}', method='PUT',
                                 data=json.dumps({'isActive': valor}).encode(), headers={'content-type': 'application/json'})
    return op.open(req, timeout=30).status

def liberar(cid, nome):
    try:
        liberando[cid] = 'liberando (desligada)…'
        op = api_login()
        ativar(op, cid, False)
        log(f'liberar {nome}: desligada')
        # o OmniRoute so apaga a marcacao de cota de conta desligada quando ela fica velha (5 min) e a rodada de 60 s passa
        time.sleep(390)
        op = api_login()
        ativar(op, cid, True)
        log(f'liberar {nome}: religada')
        # 09/11: so religar nao bastava (marlucio continuou "sem credito" ate reiniciar o OmniRoute). Limpa os
        # bloqueios temporarios (circuit breakers e lockouts de modelo) pela API, sem reiniciar.
        try:
            r = op.open(urllib.request.Request('http://localhost:20128/api/resilience/reset', method='POST',
                                               data=b'{}', headers={'content-type': 'application/json'}), timeout=30)
            log(f'liberar {nome}: resilience/reset {r.status} {r.read()[:120]!r}')
        except Exception as e:
            log(f'liberar {nome}: resilience/reset falhou {e}')
        liberando[cid] = 'religada — nova leitura em até 5 min'
        time.sleep(300)
    except Exception as e:
        log(f'liberar {nome}: ERRO {e}')
        liberando[cid] = 'ERRO: ' + str(e)[:80]
        time.sleep(600)
    finally:
        liberando.pop(cid, None)

def priorizar(cid):
    # poe a conta em prioridade 1 e empurra as outras do mesmo provedor, mantendo a ordem entre elas (via API do OmniRoute)
    db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    r = db.execute('SELECT provider, coalesce(email,name) FROM provider_connections WHERE id=?', (cid,)).fetchone()
    if not r: db.close(); return 'conta não encontrada'
    prov, nome = r
    outras = [x[0] for x in db.execute('SELECT id FROM provider_connections WHERE provider=? AND id<>? '
                                       'ORDER BY coalesce(priority,999), created_at', (prov, cid))]
    db.close()
    op = api_login()
    def put(i, p):
        req = urllib.request.Request(f'http://localhost:20128/api/providers/{i}', method='PUT',
                                     data=json.dumps({'priority': p}).encode(), headers={'content-type': 'application/json'})
        op.open(req, timeout=30)
    put(cid, 1)
    for n, i in enumerate(outras, start=2): put(i, n)
    log(f'priorizar {prov} {nome}: prioridade 1 ({len(outras)} outras empurradas)')
    return f'{nome} agora é a primeira do {prov}. As outras seguem na mesma ordem depois dela.'

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def ok(self, q):
        return q.get('k', [''])[0] == CHAVE
    def enviar(self, cod, txt, tipo='text/html; charset=utf-8'):
        b = txt.encode()
        self.send_response(cod); self.send_header('content-type', tipo); self.send_header('content-length', str(len(b)))
        self.send_header('cache-control', 'no-store'); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        if not self.ok(q): return self.enviar(403, 'sem acesso')
        try:
            p = q.get('p', ['claude'])[0]
            if u.path.endswith('/modo'):  # 09/11: o vigia do continue (PC) e o melhorador leem daqui
                try: m = open('/opt/omniroute/modo_tokens.json').read()
                except OSError: m = '{"modo": "normal"}'
                return self.enviar(200, m, 'application/json; charset=utf-8')
            if u.path.endswith('/dados'):
                return self.enviar(200, json.dumps(dados_json(p), ensure_ascii=False, default=str),
                                   'application/json; charset=utf-8')
            if u.path.endswith('/externo'):  # 11/11: tabela antiga do AI Studio (detalhe por modelo)
                return self.enviar(200, pagina_gemini())
            if q.get('v', [''])[0] != 'antiga':  # 06/11: página nova; ?v=antiga = a tabela de antes
                return self.enviar(200, PAGINA_NOVA)
            self.enviar(200, pagina_gemini() if p == 'gemini' else pagina(p))
        except Exception as e: self.enviar(500, 'erro: ' + html.escape(str(e)))
    def do_POST(self):
        _CACHE_JSON.clear()
        u = urlparse(self.path); q = parse_qs(u.query)
        if not self.ok(q): return self.enviar(403, 'sem acesso')
        cid = q.get('id', [''])[0]
        if u.path.endswith('/priorizar'):
            try: return self.enviar(200, priorizar(cid), 'text/plain; charset=utf-8')
            except Exception as e: return self.enviar(500, 'erro: ' + str(e)[:200], 'text/plain; charset=utf-8')
        if not u.path.endswith('/liberar'): return self.enviar(403, 'sem acesso')
        db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
        r = db.execute('SELECT coalesce(email,name), is_active FROM provider_connections WHERE id=?', (cid,)).fetchone(); db.close()
        if not r: return self.enviar(404, 'conta não encontrada', 'text/plain; charset=utf-8')
        if not r[1]: return self.enviar(400, 'conta já está desligada', 'text/plain; charset=utf-8')
        if cid in liberando: return self.enviar(200, 'já está liberando', 'text/plain; charset=utf-8')
        if liberando: return self.enviar(429, 'outra conta está sendo liberada; espere terminar (1 por vez)', 'text/plain; charset=utf-8')
        threading.Thread(target=liberar, args=(cid, r[0]), daemon=True).start()
        self.enviar(200, f'Liberando {r[0]}: desliga agora, religa em ~6 min. A nova leitura aparece em até 5 min.', 'text/plain; charset=utf-8')

ThreadingHTTPServer(('0.0.0.0', 20172), H).serve_forever()
