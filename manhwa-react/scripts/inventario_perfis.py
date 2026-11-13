"""inventario_perfis.py - SOMENTE LEITURA. Inventario dos perfis de Chrome (pastas com 'Local State') listados em
work/local_states.txt: tamanho, quanto e cache descartavel, contas, quais sites tem cookie de sessao (so NOME e
validade; nunca o valor) e ultimo uso. Grava work/inventario_perfis.json. Copias temporarias do banco de cookies sao
apagadas no fim."""
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(r"D:\manhwa-react\work")
TMP = WORK / "_inv_tmp"
CACHE = ["Cache", "Code Cache", "GPUCache", "DawnGraphiteCache", "DawnWebGPUCache", "GrShaderCache", "ShaderCache",
         "GraphiteDawnCache", "component_crx_cache", "extensions_crx_cache", "OptGuideOnDeviceModel",
         "optimization_guide_model_store", "Crashpad", "BrowserMetrics", "Safe Browsing", "SODALanguagePacks",
         "screen_ai", "WasmTtsEngine", "OnDeviceHeadSuggestModel", "hyphen-data", "MEIPreload", "ZxcvbnData",
         "Service Worker\\CacheStorage", "Service Worker\\ScriptCache"]
SESSAO = {"google": ("google.com", {"SID", "__Secure-1PSID", "__Secure-3PSID"}),
          "youtube": ("youtube.com", {"LOGIN_INFO", "__Secure-3PSID", "SID"}),
          "tiktok": ("tiktok.com", {"sessionid", "sessionid_ss"}),
          "instagram": ("instagram.com", {"sessionid"}),
          "facebook": ("facebook.com", {"c_user", "xs"})}
EPOCH = datetime(1601, 1, 1)


def tamanho(p):
    t = 0
    for raiz, _, arqs in os.walk(p):
        for a in arqs:
            try:
                t += os.path.getsize(os.path.join(raiz, a))
            except OSError:
                pass
    return t


def cookies(sub):
    db = next((p for p in [sub / "Network" / "Cookies", sub / "Cookies"] if p.exists()), None)
    if not db:
        return None, None
    TMP.mkdir(exist_ok=True)
    cp = TMP / "c.sqlite"
    try:
        shutil.copy2(db, cp)
    except OSError:
        return "em uso", datetime.fromtimestamp(db.stat().st_mtime)
    res = {}
    try:
        con = sqlite3.connect(f"file:{cp}?mode=ro", uri=True)
        for site, (host, nomes) in SESSAO.items():
            q = ",".join("?" * len(nomes))
            row = con.execute(f"select max(expires_utc), count(*) from cookies where host_key like ? and name in ({q})",
                              (f"%{host}", *nomes)).fetchone()
            if row and row[1]:
                exp = EPOCH + timedelta(microseconds=row[0]) if row[0] else None
                res[site] = exp.date().isoformat() if exp else "sessao"
        con.close()
    finally:
        cp.unlink(missing_ok=True)
    return res, datetime.fromtimestamp(db.stat().st_mtime)


def contas(raiz, sub):
    em = set()
    try:
        ls = json.loads((raiz / "Local State").read_text(encoding="utf-8", errors="replace"))
        for k, v in ls.get("profile", {}).get("info_cache", {}).items():
            if k == sub.name and v.get("user_name"):
                em.add(v["user_name"])
    except Exception:  # noqa: BLE001
        pass
    try:
        pr = json.loads((sub / "Preferences").read_text(encoding="utf-8", errors="replace"))
        for a in pr.get("account_info", []) or []:
            if a.get("email"):
                em.add(a["email"])
    except Exception:  # noqa: BLE001
        pass
    return sorted(em)


saida = []
vistos = set()
for linha in (WORK / "local_states.txt").read_text(encoding="utf-8-sig").splitlines():
    raiz = Path(linha.strip())
    if not linha.strip() or not raiz.exists():
        continue
    # junções do cofre (caminho antigo -> cofre\perfis): a mesma pasta apareceria 2x e a migração acharia "cópia"
    real = os.path.normcase(os.path.realpath(raiz))
    if real in vistos or any(os.path.isjunction(p) for p in [raiz, *raiz.parents] if p.exists()):
        continue
    vistos.add(real)
    total = tamanho(raiz)
    cache = sum(tamanho(raiz / c) for c in CACHE if (raiz / c).exists())
    subs = [d for d in raiz.iterdir() if d.is_dir() and (d / "Preferences").exists()]
    for sub in subs:
        cache += sum(tamanho(sub / c) for c in CACHE if (sub / c).exists())
    perfis = []
    for sub in subs:
        ck, uso = cookies(sub)
        perfis.append({"sub": sub.name, "contas": contas(raiz, sub), "sessoes": ck,
                       "ultimo_uso": uso.date().isoformat() if uso else None})
    saida.append({"pasta": str(raiz), "mb": round(total / 1e6), "cache_mb": round(cache / 1e6), "perfis": perfis})
    print(f"{total / 1e6:8.0f} MB (cache {cache / 1e6:6.0f}) {raiz}", flush=True)
shutil.rmtree(TMP, ignore_errors=True)
(WORK / "inventario_perfis.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
print("total", round(sum(s["mb"] for s in saida) / 1e3, 1), "GB; cache", round(sum(s["cache_mb"] for s in saida) / 1e3, 1), "GB")
