#!/usr/bin/env python3
"""Extract every /api path skeleton referenced ANYWHERE in the frontend.
Broad: matches /api|/recordings|/chat substrings even mid-template-literal."""
import os, re, json

CLIENT = r"d:\hipercool-refactor\client\src"

# Match /api... /recordings... /chat... appearing anywhere, stop at quote, whitespace,
# backtick, comma, paren, or template-literal boundary chars we don't want.
path_pat = re.compile(r'(/(?:api|recordings|chat)\b[A-Za-z0-9_/${}.\-*]*)')

paths = set()
file_to_paths = {}

for root, _, files in os.walk(CLIENT):
    for f in files:
        if not (f.endswith(".ts") or f.endswith(".tsx")):
            continue
        p = os.path.join(root, f)
        with open(p, "r", encoding="utf-8", errors="ignore") as fh:
            src = fh.read()
        for m in path_pat.finditer(src):
            raw = m.group(1)
            raw = raw.split("?")[0]
            norm = re.sub(r"\$\{[^}]*\}", "*", raw)
            # collapse any leftover $ or { from truncated templates
            norm = re.sub(r"[${].*$", "*", norm)
            norm = re.sub(r"\*+", "*", norm)
            norm = norm.rstrip("/")
            # drop trailing '*' that is glued to a segment like /api/logs* -> keep as /api/logs
            norm = re.sub(r"([a-zA-Z0-9_])\*$", r"\1", norm)
            if norm and norm.startswith("/"):
                paths.add(norm)
                file_to_paths.setdefault(p, set()).add(norm)

with open(r"d:\hipercool-refactor\tests\api_calls.txt", "w", encoding="utf-8") as out:
    for p in sorted(paths):
        out.write(p + "\n")
print(f"Distinct /api path-skeletons in frontend: {len(paths)}")

with open(r"d:\hipercool-refactor\tests\api_calls_files.json", "w", encoding="utf-8") as out:
    json.dump({k: sorted(v) for k, v in file_to_paths.items()}, out, indent=2)