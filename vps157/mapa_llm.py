import collections
import datetime
import json
import re
import sqlite3
import sys

DB_URI = "file:/opt/omniroute/data/storage.sqlite?mode=ro"

def mask_sensitive(s):
    if not s or s == "-":
        return "-"
    s = str(s).strip()
    if "@" in s:
        parts = s.split("@")
        user = parts[0]
        domain = parts[1]
        masked_user = user[:2] + "***" + user[-1:] if len(user) > 3 else "***"
        return f"{masked_user}@{domain}"
    if len(s) > 24 and any(s.startswith(p) for p in ("sk-", "ghp_", "omni-", "key-", "Bearer ")):
        return s[:6] + "..." + s[-4:]
    if len(s) > 32 and re.match(r"^[0-9a-fA-F\-]{30,}$", s):
        return s[:6] + "..." + s[-4:]
    return s

def clean_str(s, max_len=90):
    if not s:
        return "-"
    s = " ".join(str(s).split())
    s = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL]', s)
    s = re.sub(r'(sk-[a-zA-Z0-9_-]{15,})', r'\1'[:6] + '...', s)
    if len(s) > max_len:
        return s[:max_len-3] + "..."
    return s

def main():
    con = sqlite3.connect(DB_URI, uri=True, timeout=30)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    row = cur.execute("SELECT min(timestamp), max(timestamp), count(*) FROM call_logs WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')").fetchone()
    ts_min, ts_max, total_3d = row[0], row[1], row[2]

    row_24h = cur.execute("SELECT count(*) FROM call_logs WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-24 hours')").fetchone()
    total_24h = row_24h[0]

    out = {}
    out["info"] = {
        "ts_min": ts_min,
        "ts_max": ts_max,
        "total_calls_3d": total_3d,
        "total_calls_24h": total_24h
    }

    cur.execute("""
        SELECT 
            coalesce(requested_model, '(vazio)') as req_model,
            count(*) as total,
            sum(case when status = 200 then 1 else 0 end) as ok_count,
            round(100.0 * sum(case when status = 200 then 1 else 0 end) / count(*), 1) as pct_ok,
            round(avg(case when status = 200 then duration else null end) / 1000.0, 2) as avg_dur_s,
            round(avg(case when status = 200 and ttft_ms > 0 then ttft_ms else null end) / 1000.0, 2) as avg_ttft_s
        FROM call_logs
        WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')
        GROUP BY req_model
        ORDER BY total DESC
        LIMIT 40
    """)
    models_summary = []
    for r in cur.fetchall():
        m_dict = dict(r)
        req_m = m_dict["req_model"]
        
        cur_err = con.cursor()
        cur_err.execute("""
            SELECT coalesce(error_summary, 'status ' || status) as err, count(*) as err_count
            FROM call_logs
            WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')
              AND coalesce(requested_model, '(vazio)') = ?
              AND status != 200
            GROUP BY err
            ORDER BY err_count DESC
            LIMIT 3
        """, (req_m,))
        errs = []
        for er in cur_err.fetchall():
            err_text = clean_str(er[0], 90)
            errs.append(f"{er[1]}x: {err_text}")
        m_dict["top_errors"] = errs
        models_summary.append(m_dict)
    out["models_top40"] = models_summary

    cur.execute("""
        SELECT 
            coalesce(api_key_name, '(sem nome)') as key_name,
            coalesce(requested_model, '(vazio)') as req_model,
            count(*) as total,
            sum(case when status = 200 then 1 else 0 end) as ok_count,
            round(100.0 * sum(case when status = 200 then 1 else 0 end) / count(*), 1) as pct_ok
        FROM call_logs
        WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')
        GROUP BY key_name, req_model
        ORDER BY total DESC
        LIMIT 30
    """)
    keys_models = []
    for r in cur.fetchall():
        kd = dict(r)
        kd["key_name"] = mask_sensitive(kd["key_name"])
        keys_models.append(kd)
    out["keys_models_top30"] = keys_models

    cur.execute("""
        SELECT count(distinct session_tag) as distinct_sessions
        FROM call_logs
        WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')
          AND session_tag is not null AND session_tag != ''
    """)
    distinct_sessions = cur.fetchone()[0]
    out["distinct_sessions"] = distinct_sessions

    cur.execute("""
        SELECT 
            session_tag,
            count(*) as total,
            sum(case when status = 200 then 1 else 0 end) as ok_count,
            round(100.0 * sum(case when status = 200 then 1 else 0 end) / count(*), 1) as pct_ok
        FROM call_logs
        WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')
          AND session_tag is not null AND session_tag != ''
        GROUP BY session_tag
        ORDER BY total DESC
        LIMIT 10
    """)
    top_sessions = []
    for r in cur.fetchall():
        sd = dict(r)
        stag = sd["session_tag"]
        cur_m = con.cursor()
        cur_m.execute("""
            SELECT requested_model, count(*) as c
            FROM call_logs
            WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')
              AND session_tag = ?
            GROUP BY requested_model
            ORDER BY c DESC
            LIMIT 1
        """, (stag,))
        m_row = cur_m.fetchone()
        sd["top_model"] = m_row[0] if m_row else "-"
        sd["top_model_count"] = m_row[1] if m_row else 0
        sd["session_tag"] = mask_sensitive(stag)
        top_sessions.append(sd)
    out["top10_sessions"] = top_sessions

    cur.execute("""
        SELECT 
            substr(timestamp, 1, 13) || ':00' as hora_utc,
            count(*) as total,
            sum(case when status = 200 then 1 else 0 end) as ok_count,
            round(100.0 * sum(case when status = 200 then 1 else 0 end) / count(*), 1) as pct_ok
        FROM call_logs
        WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-24 hours')
        GROUP BY hora_utc
        ORDER BY hora_utc ASC
    """)
    hourly = [dict(r) for r in cur.fetchall()]
    out["hourly_24h"] = hourly

    cur.execute("SELECT name, data FROM combos ORDER BY name")
    combos_list = []
    for r in cur.fetchall():
        c_name = r["name"]
        try:
            c_data = json.loads(r["data"] or "{}")
        except Exception:
            c_data = {}
        models = c_data.get("models", [])
        num_steps = len(models)
        distinct_models = []
        for m in models:
            m_id = m.get("model") or m.get("id") or m.get("providerId") or str(m)
            if m_id not in distinct_models:
                distinct_models.append(m_id)
        combos_list.append({
            "name": c_name,
            "steps_count": num_steps,
            "models_order": distinct_models
        })
    out["combos"] = combos_list

    cur.execute("""
        SELECT provider, model, status, count(*) as c
        FROM usage_history 
        WHERE success = 0 AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')
        GROUP BY 1, 2, 3
        ORDER BY c DESC
        LIMIT 10
    """)
    out["top_provider_failures"] = [dict(r) for r in cur.fetchall()]

    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()