#!/usr/bin/env python3
"""For each subsystem, list which backend routes the frontend actually hits."""
import os, re, json

CLIENT = r"d:\hipercool-refactor\client\src"

path_pat = re.compile(r'/(?:api|recordings|chat)\b[A-Za-z0-9_/${}.\-*]*')
calls = set()
for root, _, files in os.walk(CLIENT):
    for f in files:
        if not (f.endswith(".ts") or f.endswith(".tsx")): continue
        src = open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
        for m in path_pat.finditer(src):
            raw = m.group(0).split("?")[0]
            n = re.sub(r"\$\{[^}]*\}", "*", raw)
            n = re.sub(r"\*+", "*", n).rstrip("/")
            calls.add(n)

areas = {
    "billing":   re.compile(r"^/api/billing"),
    "billing_webhook": re.compile(r"^/api/billing/webhook$"),
    "agenda":    re.compile(r"^/api/agenda"),
    "chat-control": re.compile(r"^/api/chat-control"),
    "chatwoot":  re.compile(r"^/api/chatwoot"),
    "stage-action": re.compile(r"^/api/crm/stage-action"),
    "channels":  re.compile(r"^/api/sessions/[^/]+/channels"),
    "admin-list": re.compile(r"^/api/admin-list"),
    "eleven":    re.compile(r"^/api/settings/eleven"),
    "garimpo":   re.compile(r"^/api/settings/garimpo"),
    "rag":       re.compile(r"^/api/rag"),
    "calls/bridge": re.compile(r"^/api/calls/[^/]+/bridge"),
    "diagnostics": re.compile(r"^/api/diagnostics"),
    "agent-profiles": re.compile(r"^/api/agent-profiles"),
    "ai-test":   re.compile(r"^/api/ai/test"),
    "users/prefs": re.compile(r"^/api/users/me/preferences"),
    "followup":  re.compile(r"^/api/followup"),
    "catalog":   re.compile(r"^/api/catalog"),
}
for k, pat in areas.items():
    used = sorted(c for c in calls if pat.match(c))
    print(f"=== {k} (frontend refs: {len(used)}) ===")
    for c in used: print(" ", c)
    print()
