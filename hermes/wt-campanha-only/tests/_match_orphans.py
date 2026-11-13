#!/usr/bin/env python3
"""Cross-reference backend routes vs frontend path references."""
import re, json

ROUTES = r"d:\hipercool-refactor\cmd\server\httpapi.go"
CALLS = r"d:\hipercool-refactor\tests\api_calls.txt"

def norm(path):
    p = re.sub(r"\{[^}]+\}", "*", path)
    p = re.sub(r"\$\{[^}]+\}", "*", p)
    p = p.split("?")[0].rstrip("/")
    return p

def seg_match(a, b):
    sa, sb = a.split("/"), b.split("/")
    if len(sa) != len(sb):
        return False
    for x, y in zip(sa, sb):
        if x == "*" or y == "*":
            continue
        if x != y:
            return False
    return True

# --- backend routes ---
route_pat = re.compile(r'HandleFunc\("([A-Z]+) (/[^"]+)", *s\.([A-Za-z0-9_]+)')
routes = []
with open(ROUTES, encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        m = route_pat.search(line)
        if m:
            method, path, handler = m.groups()
            routes.append({
                "method": method, "path": path, "handler": handler,
                "norm": norm(path), "line": i,
            })

backend_norm = set(r["norm"] for r in routes)

# --- frontend calls ---
front = set()
with open(CALLS, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("/api") or line.startswith("/recordings") or line.startswith("/chat"):
            front.add(norm(line))

# --- BACKEND ORPHANS ---
# A route is orphan if its exact norm path is NOT referenced by the frontend
# AND no other frontend path matches it via seg_match.
orphans = []
for r in routes:
    np = r["norm"]
    if any(seg_match(fp, np) for fp in front):
        continue
    orphans.append(r)

# --- UI BROKEN ---
broken = []
for fp in sorted(front):
    if any(seg_match(fp, np) for np in backend_norm):
        continue
    broken.append(fp)

print("=" * 70)
print(f"BACKEND ORPHANS: {len(orphans)} / {len(routes)} routes")
print("=" * 70)
for r in orphans:
    print(f"{r['method']:7} {r['path']:55} httpapi.go:{r['line']:<5} {r['handler']}")

print()
print("=" * 70)
print(f"UI BROKEN: {len(broken)} / {len(front)} distinct frontend path-skeletons")
print("=" * 70)
for fp in broken:
    print(f"  {fp}")

with open(r"d:\hipercool-refactor\tests\orphans.json", "w", encoding="utf-8") as out:
    json.dump({
        "backend_orphans": orphans,
        "ui_broken": broken,
    }, out, indent=2)
