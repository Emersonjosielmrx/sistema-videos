#!/usr/bin/env python3
"""So leitura: onde a cota/tempo dos modelos se perde (3 dias). Nao chama provedor nenhum."""
import sqlite3

db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=60)
Q = lambda s, p=(): db.execute(s, p).fetchall()
D3 = "strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')"

print("== por provedor (3 d): tentativas | ok% | falha com >120 s | tokens de entrada em pedido que falhou (M) ==")
for r in Q(f"""SELECT provider, count(*), round(100.0*sum(success)/count(*)),
               sum(success=0 AND latency_ms>120000), round(sum(CASE WHEN success=0 THEN tokens_input ELSE 0 END)/1e6,1)
               FROM usage_history WHERE timestamp>={D3} GROUP BY 1 ORDER BY 2 DESC LIMIT 10"""):
    print("  ", " | ".join(str(x) for x in r))

print("\n== reenvio em rajada: mesmo session_tag + mesmo tokens_in em <60 s (3 d), por modelo pedido ==")
for r in Q(f"""SELECT a.requested_model, count(*) FROM call_logs a JOIN call_logs b
               ON a.session_tag=b.session_tag AND a.tokens_in=b.tokens_in AND a.tokens_in>1000 AND a.id<>b.id
               AND b.timestamp>a.timestamp AND julianday(b.timestamp)-julianday(a.timestamp) < 60.0/86400
               WHERE a.timestamp>={D3} GROUP BY 1 ORDER BY 2 DESC LIMIT 8"""):
    print("  ", " | ".join(str(x) for x in r))

print("\n== contas distintas por hora (ultimas 12 h): hora | claude | antigravity | claude-web | kiro ==")
for r in Q("""SELECT substr(timestamp,1,13),
              count(DISTINCT CASE WHEN provider='claude' THEN connection_id END),
              count(DISTINCT CASE WHEN provider='antigravity' THEN connection_id END),
              count(DISTINCT CASE WHEN provider='claude-web' THEN connection_id END),
              count(DISTINCT CASE WHEN provider='kiro' THEN connection_id END)
              FROM usage_history WHERE timestamp>=strftime('%Y-%m-%dT%H:%M:%S','now','-12 hours') GROUP BY 1 ORDER BY 1"""):
    print("  ", " | ".join(str(x) for x in r))

print("\n== pedidos grandes que falharam (3 d): modelo | tokens_in | s | erro ==")
for r in Q(f"""SELECT requested_model, tokens_in, round(duration/1000.0), substr(coalesce(error_summary,''),1,90)
               FROM call_logs WHERE status<>200 AND timestamp>={D3} ORDER BY tokens_in DESC LIMIT 8"""):
    print("  ", " | ".join(str(x) for x in r))

print("\n== pedidos do Opus pago que falharam depois de >60 s (3 d) por erro ==")
for r in Q(f"""SELECT substr(coalesce(error_summary,''),1,90), count(*), round(avg(duration)/1000.0)
               FROM call_logs WHERE requested_model IN ('opus-auto','cc/claude-opus-5-5','opus-pago-sonnetweb')
               AND status<>200 AND duration>60000 AND timestamp>={D3} GROUP BY 1 ORDER BY 2 DESC LIMIT 6"""):
    print("  ", " | ".join(str(x) for x in r))
