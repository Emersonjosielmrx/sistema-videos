# levantamento SO LEITURA dos arquivos que nao sao codigo dentro de D:\sistema (27/11, pedido da dona)
import os, re, time, json
from collections import defaultdict
RAIZ = r"D:\sistema"
PULA = re.compile(r"^(\.?venv.*|site-packages|node_modules|\.git|catalogo|comum|mapa|quarentena|secrets|perfis|cofre.*|"
                  r"Chrome.*|User Data|chromium.*|\.cache|ms-playwright)$", re.I)
COD = (".py", ".pyw", ".bat", ".ps1", ".vbs", ".cmd", ".sh", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs")
agora = time.time()
DIA = 86400
def tipo(f):
    e = os.path.splitext(f)[1].lower()
    if e in (".log", ".out", ".err") or re.search(r"\.log\.\d+$", f): return "log"
    if e in (".pyc", ".pyo"): return "pyc"
    if ".bak" in f.lower() or re.search(r"\.(orig|antes|old)(_|$)", f.lower()): return "backup"
    if e in (".mp4", ".mov", ".webm", ".mkv", ".avi"): return "video"
    if e in (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac"): return "audio"
    if e in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"): return "imagem"
    if e in (".json", ".jsonl", ".csv", ".txt", ".md", ".yaml", ".yml", ".toml", ".ini", ".cfg"): return "dado/texto"
    if e in (".zip", ".tar", ".gz", ".tgz", ".7z", ".rar"): return "pacote"
    if e in (".pt", ".pth", ".onnx", ".bin", ".safetensors", ".ckpt", ".index"): return "modelo"
    return "outro"
def lixo_dir(dp):
    return bool(re.search(r"\\(tmp|temp|_tmp|cache|_cache|__pycache__|teste?s?|_teste?s?|scratch|old|antigo|_antigo|lixo|"
                          r"descart\w*|reprovad\w*|_volta|backup\w*|_bak\w*)(\\|$)", dp, re.I))
tot = defaultdict(lambda: [0, 0])        # tipo -> [n, bytes]
cand = defaultdict(lambda: [0, 0])       # motivo -> [n, bytes]
pastas = defaultdict(lambda: [0, 0])     # pasta (3 niveis) -> bytes candidatos
exemplos = defaultdict(list)
def e_j(p):
    try: return bool(os.stat(p, follow_symlinks=False).st_file_attributes & 0x400)
    except OSError: return False
for dp, dn, fn in os.walk(RAIZ):
    dn[:] = [d for d in dn if not PULA.match(d) and not e_j(os.path.join(dp, d))]
    for f in fn:
        if f.lower().endswith(COD):
            continue
        p = os.path.join(dp, f)
        try:
            st = os.stat(p)
        except OSError:
            continue
        t = tipo(f); idade = (agora - max(st.st_mtime, st.st_atime if False else 0)) / DIA
        tot[t][0] += 1; tot[t][1] += st.st_size
        motivo = None
        if t == "pyc": motivo = "pyc (o Python refaz sozinho)"
        elif t == "log" and idade > 14: motivo = "log com 14+ dias"
        elif t == "backup" and idade > 14: motivo = "backup .bak com 14+ dias"
        elif lixo_dir(dp) and idade > 14: motivo = "pasta tmp/teste/cache/reprovado com 14+ dias"
        elif t in ("video", "audio", "imagem") and idade > 30 and lixo_dir(dp): motivo = "midia de teste 30+ dias"
        elif t == "pacote" and idade > 14: motivo = "pacote zip/tgz 14+ dias"
        if motivo:
            cand[motivo][0] += 1; cand[motivo][1] += st.st_size
            k = "\\".join(os.path.relpath(dp, RAIZ).split("\\")[:4])
            pastas[k][0] += 1; pastas[k][1] += st.st_size
            if len(exemplos[motivo]) < 3: exemplos[motivo].append(os.path.relpath(p, RAIZ)[:130])
GB = 1e9
print("== TUDO que nao e codigo em D:\\sistema (fora venvs/perfis de navegador/segredos):")
for t, (n, b) in sorted(tot.items(), key=lambda x: -x[1][1]):
    print(f"   {t:12} {n:8} arquivos  {b/GB:7.2f} GB")
print(f"   TOTAL        {sum(v[0] for v in tot.values()):8} arquivos  {sum(v[1] for v in tot.values())/GB:7.2f} GB")
print("== CANDIDATOS A LIXO (so lista, nada mexido):")
for m, (n, b) in sorted(cand.items(), key=lambda x: -x[1][1]):
    print(f"   {m:46} {n:7} arq  {b/GB:6.2f} GB   ex.: {exemplos[m][0] if exemplos[m] else ''}")
print(f"   TOTAL CANDIDATOS {sum(v[0] for v in cand.values())} arq  {sum(v[1] for v in cand.values())/GB:.2f} GB")
print("== ONDE esta (top 15 pastas):")
for k, (n, b) in sorted(pastas.items(), key=lambda x: -x[1][1])[:15]:
    print(f"   {b/GB:6.2f} GB {n:6} arq  {k}")
json.dump({"tot": tot, "cand": cand, "pastas": pastas}, open(r"D:\sistema\mapa\nao_codigo_27nov.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
