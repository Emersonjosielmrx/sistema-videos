# -*- coding: utf-8 -*-
"""metrics_analyzer.py — Parseia pipeline_metrics.jsonl e gera relatórios rápidos.

Uso:
    python bin/metrics_analyzer.py                    # resumo geral
    python bin/metrics_analyzer.py --genero superacao  # filtrado por gênero
    python bin/metrics_analyzer.py --recent 10         # últimos 10 vídeos
    python bin/metrics_analyzer.py --pivot steps       # tabela pivô de tempos por etapa
    python bin/metrics_analyzer.py --hw                # só métricas de hardware
    python bin/metrics_analyzer.py --fail              # só falhas
"""
import json, sys, argparse
from pathlib import Path
from collections import defaultdict

METRICS = Path(__file__).resolve().parent.parent / "logs" / "pipeline_metrics.jsonl"

def load(recent=None, genero=None, failed_only=False):
    records = []
    if not METRICS.exists():
        print(f"  Nenhum arquivo de métricas encontrado em {METRICS}"); sys.exit(0)
    with open(METRICS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except: continue
            if genero and r.get("genero") != genero: continue
            if failed_only and r.get("status") == "ok": continue
            records.append(r)
    if recent: records = records[-recent:]
    return records

def fmt(s):
    if s is None: return "N/A"
    if isinstance(s, float): return f"{s:.1f}"
    return str(s)

def report_summary(records):
    ok = [r for r in records if r.get("status") == "ok"]
    fail = [r for r in records if r.get("status") != "ok"]
    print(f"\n{'='*60}")
    print(f" RESUMO GERAL — {len(records)} vídeos")
    print(f"{'='*60}")
    print(f"  OK:       {len(ok)}")
    print(f"  Falhas:   {len(fail)}")
    print(f"  Taxa OK:  {len(ok)/len(records)*100:.0f}%" if records else "  Taxa OK: N/A")
    if ok:
        avg_el = sum(r.get("elapsed_s", 0) for r in ok) / len(ok)
        avg_dur = sum(r.get("video_duration_s", 0) or r.get("extra", {}).get("video_duration_s", 0) for r in ok) / len(ok)
        print(f"  Temp méd: {avg_el/60:.1f} min (geração)")
        print(f"  Duração:  {avg_dur:.0f}s (vídeo)")
    print()

def report_by_genre(records):
    by_g = defaultdict(list)
    for r in records: by_g[r.get("genero","?")].append(r)
    print(f"{'='*60}")
    print(" POR GÊNERO")
    print(f"{'='*60}")
    print(f"  {'Gênero':<15} {'OK':>4} {'Fail':>5} {'Taxa':>6} {'Tmp méd(min)':>13} {'Duração':>9}")
    print(f"  {'-'*15} {'-'*4} {'-'*5} {'-'*6} {'-'*13} {'-'*9}")
    for g, rs in sorted(by_g.items(), key=lambda x: -len(x[1])):
        ok = sum(1 for r in rs if r.get("status") == "ok")
        fails = len(rs) - ok
        rate = ok/len(rs)*100 if rs else 0
        avg_t = sum(r.get("elapsed_s",0) for r in rs if r.get("status")=="ok")
        avg_t = avg_t/ok/60 if ok else 0
        avg_d = sum(r.get("video_duration_s",0) or r.get("extra",{}).get("video_duration_s",0) for r in rs if r.get("status")=="ok")
        avg_d = avg_d/ok if ok else 0
        print(f"  {g:<15} {ok:>4} {fails:>5} {rate:>5.0f}% {avg_t:>13.1f} {avg_d:>9.0f}s")
    print()

def report_steps(records):
    ok = [r for r in records if r.get("status") == "ok"]
    if not ok: print("  Sem vídeos OK para análise de etapas."); return
    steps = defaultdict(list)
    for r in ok:
        for s, t in r.get("steps_s", {}).items():
            steps[s].append(t)
    print(f"{'='*60}")
    print(" TEMPO POR ETAPA (média em segundos)")
    print(f"{'='*60}")
    print(f"  {'Etapa':<20} {'Média':>8} {'Min':>8} {'Max':>8} {'Total':>8}")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    total_avg = 0
    for s, ts in sorted(steps.items(), key=lambda x: -sum(x[1])):
        avg = sum(ts)/len(ts)
        mn, mx = min(ts), max(ts)
        total_avg += avg
        print(f"  {s:<20} {avg:>8.1f} {mn:>8.1f} {mx:>8.1f} {len(ts):>8}x")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    print(f"  {'TOTAL':<20} {total_avg:>8.1f} {'':>8} {'':>8} {'':>8}")
    print()

def report_hw(records):
    print(f"{'='*60}")
    print(" HARDWARE (picos por vídeo)")
    print(f"{'='*60}")
    print(f"  {'Gênero':<15} {'RAM%':>6} {'RAM(GB)':>8} {'CPU%':>6} {'DiscoGB':>8} {'Tmp':>8}")
    print(f"  {'-'*15} {'-'*6} {'-'*8} {'-'*6} {'-'*8} {'-'*8}")
    for r in records[-20:]:
        hw = r.get("hw", {})
        print(f"  {r.get('genero','?'):<15} {hw.get('ram_pct','?'):>6} "
              f"{hw.get('ram_used_gb','?'):>8} {hw.get('cpu_pct','?'):>6} "
              f"{hw.get('disk_free_gb','?'):>8} {r.get('elapsed_s',0)/60:>7.1f}m")
    print()

def report_failures(records):
    fails = [r for r in records if r.get("status") != "ok"]
    if not fails:
        print("  Nenhuma falha registrada.\n"); return
    print(f"{'='*60}")
    print(f" FALHAS ({len(fails)} total)")
    print(f"{'='*60}")
    for r in fails[-15:]:
        print(f"  [{r.get('ts','?')}] {r.get('genero','?')} — {r.get('status','?')}")
        if r.get("error"): print(f"    Erro: {r['error'][:120]}")
        c = r.get("counters", {})
        if c: print(f"    Counters: {c}")
        ev = r.get("events", [])
        for e in ev[:3]: print(f"    Evento: {e}")
    print()

def report_api(records):
    print(f"{'='*60}")
    print(" EVENTOS DE API (fallback, 402, 429, proxy)")
    print(f"{'='*60}")
    tot_pol = sum(r.get("counters",{}).get("img_pollinations",0) for r in records)
    tot_402 = sum(r.get("counters",{}).get("api_402",0) for r in records)
    tot_429 = sum(r.get("counters",{}).get("api_429",0) for r in records)
    tot_proxy = sum(r.get("counters",{}).get("proxy_fail",0) for r in records)
    tot_q = sum(r.get("counters",{}).get("quarantine",0) for r in records)
    print(f"  img_pollinations:  {tot_pol:>5}x (fallback de imagem)")
    print(f"  api_402:          {tot_402:>5}x (erro de pagamento)")
    print(f"  api_429:          {tot_429:>5}x (rate limit)")
    print(f"  proxy_fail:       {tot_proxy:>5}x (proxy Webshare falhou)")
    print(f"  quarantine:       {tot_q:>5}x (vídeos em quarantine)")
    print()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--genero"); ap.add_argument("--recent", type=int)
    ap.add_argument("--fail", action="store_true")
    ap.add_argument("--steps", action="store_true")
    ap.add_argument("--hw", action="store_true")
    ap.add_argument("--api", action="store_true")
    args = ap.parse_args()
    records = load(recent=args.recent, genero=args.genero, failed_only=args.fail)
    if not records: print("  Nenhuma métrica encontrada."); return
    report_summary(records)
    if args.steps: report_steps(records)
    if args.hw: report_hw(records)
    if args.fail: report_failures(records)
    if args.api: report_api(records)
    if not any([args.steps, args.hw, args.fail, args.api]):
        report_by_genre(records)
        report_api(records)
        report_failures(records)

if __name__ == "__main__": main()
