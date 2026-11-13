"""login_em_lote.py — login Google de MUITAS contas de uma vez numa máquina Windows da casa (PC2...). Dona 26/10/2026:
"vai fechando conforme eu for logando e abrindo novas" — o jeito padrão de logar contas (bem mais rápido que uma por
uma: ~50 contas em ~1 h). Doc: docs\\NETBOOKS_POSTAGEM.md, seção "Login em lote".

    python bin\\netbooks\\login_em_lote.py <maquina> [N=10]   # monitor: mantém N janelas de login na tela
    python bin\\netbooks\\login_em_lote.py <maquina> estado

Como funciona:
- abre N janelas (Chrome SEM porta de controle, perfil próprio, e-mail já no campo, depois do login vai pro YouTube);
- um vigia DENTRO da sessão da tela (PowerShell por schtasks /it) lê o título de cada janela a cada 6 s;
- título "YouTube" = logada: fecha pela janela (o Chrome grava os cookies), abre a próxima na hora e confere pela
  própria rede (conferir_logins._um) — uma por volta, sem parar de abrir/fechar;
- a dona fechou a janela sem chegar no YouTube (conta com erro): confere uma vez; não logou = "falhas", não reabre;
- segura a vez da máquina ("login google lote (dona)") — o tiktok_notebooks e o telão esperam.
"""
import json
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote

sys.path[:0] = [str(Path(__file__).resolve().parent.parent), str(Path(__file__).resolve().parent)]
import maquina_remota as mr  # noqa: E402
import conferir_logins as cl  # noqa: E402
import logar_lista  # noqa: E402

VEZ = "login google lote (dona)"
# dona 12/11: contas novas entram em UMA máquina por dia (muitos logins da mesma conta em IPs/aparelhos novos bloqueiam).
# Registro de onde/quando cada uma entrou: config/contas_novas_rodizio.json. As outras contas não têm limite.
CONTAS_NOVAS = {"emersonjosiel2035", "emersonjosiel2034", "inovaremanhwaverse7", "inovaremanhwaverse8",
                "inovaremanhwaverse9"}
RODIZIO = mr.ROOT / "config" / "contas_novas_rodizio.json"


def _rodizio():
    try:
        return json.loads(RODIZIO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _conta_kaggle(p):
    """12/11 (dona: "é só usar o proxy daqui pra frente e não deixar isso acontecer mais"): conta do Kaggle (kaggle_pool)
    NUNCA loga o Google pela internet de casa — o 2º banimento (09/11) foi conta do Kaggle aparecendo em outros IPs. O
    login em lote abre o Chrome SEM proxy; essas contas logam só no PC1, pelo IP fixo delas (cofre + ponte rnprmtfo)."""
    try:
        pool = json.loads(Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json").read_text(encoding="utf-8"))
        nomes = {str(c.get("cofre") or "").split("@")[0].lower() for c in pool.get("contas", [])}
        nomes |= {str(c.get("username") or "").lower() for c in pool.get("contas", [])}
        # conta reservada pro Kaggle no cofre (kaggle_proxy) antes de entrar no pool (ex.: 2036–2038 durante o cadastro)
        try:
            reg = json.loads(Path(r"D:\logins-google\cofre\contas.json").read_text(encoding="utf-8")).get("contas", {})
            nomes |= {e.split("@")[0].lower() for e, d in reg.items() if isinstance(d, dict) and d.get("kaggle_proxy")}
        except (OSError, ValueError):
            pass
        return p.lower().split("@")[0] in nomes
    except (OSError, ValueError):
        return True  # na dúvida, não loga pela casa


def _nova_bloqueada(p, maquina):
    """True = conta nova que já entrou HOJE em outra máquina (a de hoje pode repetir/terminar)."""
    if _conta_kaggle(p):
        return True
    if p not in CONTAS_NOVAS:
        return False
    hoje = time.strftime("%Y-%m-%d")
    return any(m != maquina and d == hoje for m, d in _rodizio().get(p, {}).items())


def _nova_registrar(p, maquina):
    if p in CONTAS_NOVAS:
        r = _rodizio()
        r.setdefault(p, {})[maquina] = time.strftime("%Y-%m-%d")
        RODIZIO.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W = r"C:\postador-worker"

# título de cada janela de login (só a sessão da tela enxerga) + fecha as pedidas pelo PC1
VIGIA_PS = r"""
$dir = 'C:\postador-worker'
# dona 26/10: som desligado durante os logins (volta como estava no fim)
$antes = $null
try {
Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume { int a0(); int a1(); int a2(); int a3(); int a4(); int a5(); int a6(); int a7(); int a8();
  int a9(); int a10(); int SetMute([MarshalAs(UnmanagedType.Bool)] bool m, Guid g); int GetMute(out bool m); }
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice { int Activate(ref Guid id, int ctx, IntPtr p, out IAudioEndpointVolume v); }
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator { int f(); int GetDefaultAudioEndpoint(int flow, int role, out IMMDevice d); }
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDE { }
public class Som {
  static IAudioEndpointVolume V() { IMMDevice d; ((IMMDeviceEnumerator)(new MMDE())).GetDefaultAudioEndpoint(0, 1, out d);
    IAudioEndpointVolume v; Guid g = typeof(IAudioEndpointVolume).GUID; d.Activate(ref g, 23, IntPtr.Zero, out v); return v; }
  public static bool Mudo { get { bool m; V().GetMute(out m); return m; } set { V().SetMute(value, Guid.Empty); } }
}
"@
$antes = [Som]::Mudo; [Som]::Mudo = $true
} catch { "sem som: $_" | Out-File "$dir\vigia_erro.txt" }
while (-not (Test-Path "$dir\monitor_parar.txt")) {
  "login" | Out-File C:\vitrine\login.txt -ErrorAction SilentlyContinue
  $linhas = @("#|" + [DateTimeOffset]::Now.ToUnixTimeSeconds())
  Get-CimInstance Win32_Process -Filter "name='chrome.exe'" | Where-Object { $_.CommandLine -like '*postador-worker\perfis\*' -and $_.CommandLine -notlike '*--type=*' -and $_.CommandLine -notlike '*remote-debugging*' } | ForEach-Object {
    $perfil = ($_.CommandLine -split 'perfis\\')[1].Split('"')[0].Split(' ')[0]
    $t = ''; try { $t = (Get-Process -Id $_.ProcessId).MainWindowTitle } catch {}
    $linhas += "$perfil|$($_.ProcessId)|$t"
  }
  $linhas | Out-File "$dir\janelas.tmp" -Encoding UTF8
  Move-Item "$dir\janelas.tmp" "$dir\janelas.txt" -Force
  if (Test-Path "$dir\fechar_pedido.txt") {
    foreach ($p in (Get-Content "$dir\fechar_pedido.txt")) {
      foreach ($l in $linhas) { $c = $l.Split('|'); if ($c[0] -eq $p.Trim()) { try { (Get-Process -Id ([int]$c[1])).CloseMainWindow() | Out-Null } catch {} } }
    }
    Remove-Item "$dir\fechar_pedido.txt" -Force
  }
  Start-Sleep 6
}
Remove-Item "$dir\monitor_parar.txt" -Force
Remove-Item C:\vitrine\login.txt -Force -ErrorAction SilentlyContinue
if ($antes -eq $false) { try { [Som]::Mudo = $false } catch {} }
"""

# o painel de avisos (telão, kiosk) cobre a tela: traz as janelas de login pra frente
FRENTE_PS = r"""
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W { [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); }
"@
$ids = (Get-CimInstance Win32_Process -Filter "name='chrome.exe'" | Where-Object { $_.CommandLine -like '*postador-worker*' -and $_.CommandLine -notlike '*--type=*' }).ProcessId
foreach ($i in $ids) { $p = Get-Process -Id $i; if ($p.MainWindowHandle -ne 0) {
  [W]::ShowWindow($p.MainWindowHandle,3) | Out-Null; [W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
  (New-Object -ComObject WScript.Shell).AppActivate($i) | Out-Null } }
"""


class Lote:
    def __init__(self, maquina):
        if maquina not in mr.MAQUINAS:
            raise SystemExit(f"{maquina}: máquina desconhecida ({', '.join(mr.MAQUINAS)})")
        self.m, self.host, self.r = maquina, mr.MAQUINAS[maquina]["ssh"], mr.Remoto(maquina)
        self.win = self.r.win
        self.est_arq = mr.ROOT / "config" / f"login_em_lote_{maquina}.json"

    def ssh(self, cmd, timeout=90):
        # 02/11: o ssh do DESKTOP cai no PowerShell — "a & b", "2>nul" e "(echo ...) > x" são do cmd e lá davam erro
        # calado (o vigia/janelas nunca subiam e o lote ficou 5 h esperando sem abrir nada). Esses vão num .bat.
        if self.win and any(s in cmd for s in (" & ", "2>nul", "(echo")):
            self.enviar("@echo off\r\n" + cmd + "\r\n", "lote_cmd.bat")
            cmd = f"{W}\\lote_cmd.bat"
        try:
            r = self.r._ssh(cmd, timeout=timeout)
        except subprocess.TimeoutExpired:
            return ""
        return (r.stdout or b"").decode("utf-8-sig", errors="replace").replace("\x00", "")

    def janelas(self):
        """Texto "#|<hora>" + "perfil|pid|título" (Windows: o vigia da tela grava; Linux: o chrome_conta lê na hora)."""
        return self.ssh(f"type {W}\\janelas.txt" if self.win else f"{self.r.run} janelas")

    def pedir_fechar(self, perfis):
        if self.win:
            self.ssh("(" + " & ".join(f"echo {p}" for p in perfis) + f") > {W}\\fechar_pedido.txt")
        else:
            for p in perfis:
                self.ssh(f"{self.r.run} fechar_janela {p}")

    def enviar(self, texto, nome, enc="ascii"):
        loc = Path(tempfile.gettempdir()) / f"lote_{nome}"
        loc.write_text(texto, encoding=enc)
        subprocess.run(["scp", "-q", str(loc), f"{self.host}:C:/postador-worker/{nome}"], timeout=60)
        loc.unlink()

    def tarefa(self, nome, acao):
        """Roda na sessão da TELA (pelo ssh as janelas não aparecem). No PC2 os cmdlets de tarefa do PowerShell dão
        "Classe inválida" (WMI quebrado): schtasks /it, como o plano B do chrome_conta._lancar."""
        self.ssh(f'schtasks /create /tn {nome} /tr "{acao}" /sc once /st 00:00 /it /f & schtasks /run /tn {nome}')

    def ler(self):
        try:
            return json.loads(self.est_arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"feitas": [], "puladas": [], "falhas": [], "lote": [], "verificar": []}

    def gravar(self, est):
        self.est_arq.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def contas():
        """Lista da dona (logar_lista) na ordem dela, depois os outros perfis conhecidos (menos Instagram)."""
        vistos, out = set(), []
        for e in logar_lista.CONTAS:
            p = e.split("@")[0].lower()
            vistos.add(p)
            out.append((p, e))
        for p, info in sorted(mr._mapa_perfis().items()):
            if not p.startswith("ig_") and p not in vistos:
                out.append((p, info.get("email") or f"{p}@gmail.com"))
        return out

    def abrir(self, p, e, k):
        """Abre a janela de login; False = a máquina está sem RAM pra mais uma (tenta de novo na próxima volta).
        Antes de cada uma: fecha o que não precisa e limpa a RAM (chrome_conta liberar; dona 26/10 "sempre")."""
        url = f"https://accounts.google.com/ServiceLogin?Email={quote(e)}&continue=https%3A%2F%2Fwww.youtube.com%2F"
        x, y = 40 + 60 * (k % 10), 20 + 40 * (k % 10)
        if not self.win:
            return "PRONTO_LOGIN" in self.ssh(f"{self.r.run} login_janela {p} {x % 300} {y % 200} '{url}'")
        self.ssh(f"{self.r.run} liberar")
        # .bat com "start": Chrome aberto por PowerShell dentro de tarefa morre quando a tarefa acaba; no .bat % = %%
        self.enviar(f'@echo off\r\nstart "" "{CHROME}" "--user-data-dir={W}\\perfis\\{p}" --no-first-run '
                    f'--no-default-browser-check --disable-sync --window-size=1000,800 '
                    f'--window-position={x},{y} "{url.replace("%", "%%")}"\r\n', "um.bat")
        self.tarefa("PostadorUm", f"{W}\\um.bat")
        self.ssh("schtasks /run /tn PostadorFrente")
        return True

    def verificar(self, est, p):
        res = cl._um(p, self.m, ["google", "youtube"])
        for rede, ok in res.items():
            if ok is not None:
                for _ in range(10):  # outro processo gravando o netbooks_logins.json: Acesso negado
                    try:
                        cl._marcar(p, self.m, rede, bool(ok))
                        break
                    except PermissionError:
                        time.sleep(2)
        mr.log(f"login em lote {self.m}: {p} -> {res}")
        if res.get("google"):
            est["feitas"].append(p)
            est["falhas"] = [x for x in est["falhas"] if x != p]
        else:
            est["falhas"] = sorted(set(est["falhas"]) | {p})
        print(f"{time.strftime('%H:%M')} {p}: google={res.get('google')!r} youtube={res.get('youtube')!r}", flush=True)

    def monitor(self, n, so=None):
        est = self.ler()
        todas = self.contas()
        if so:  # 01/11 dona: logar só estas contas (as deslogadas do Flow), não a lista toda
            alvo = {p.lower() for p in so}
            todas = [(p, e) for p, e in todas if p in alvo]
        mr.ocupar(self.m, VEZ, 30)  # antes de tudo: o tiktok_notebooks/telão/Veo não entram no meio
        if self.win:
            self.enviar(VIGIA_PS, "vigia.ps1")
            self.enviar(FRENTE_PS, "frente.ps1")
            ps = "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File"
            self.ssh(f"schtasks /create /tn PostadorFrente /tr \"{ps} {W}\\frente.ps1\" /sc once /st 00:00 /it /f")
            self.ssh(f"del {W}\\monitor_parar.txt {W}\\janelas.txt 2>nul")
            self.tarefa("PostadorVigiaLogin", f"{ps} {W}\\vigia.ps1")
        else:  # dona 26/10: som desligado durante os logins (o vigia do Windows faz o mesmo na tela)
            self.ssh(f"{self.r.run} som mudo")
        for porta in (self.r.porta, 0):  # Chrome de postagem/conferência que sobrou: fecha normal antes do lote
            self.ssh(f"{self.r.run} fechar {porta}", timeout=240)
        abertos_em, k, sumiu, batida, adiou = {}, len(est.get("lote", [])), Counter(), None, Counter()
        while True:
            mr.ocupar(self.m, VEZ, 30)
            txt = self.janelas()
            nova = next((x.strip()[2:] for x in txt.splitlines() if x.startswith("#|")), None)
            if not nova or nova == batida:  # vigia subindo (o PowerShell do PC2 leva ~1 min) ou parado: não decide
                time.sleep(10)
                continue
            batida = nova
            jan = {}
            for linha in txt.splitlines():
                c = linha.strip().split("|", 2)
                if len(c) == 3 and c[0] != "#":
                    jan[c[0].lower()] = c[2]
            logadas = [p for p in est.get("lote", []) if "youtube" in jan.get(p, "").lower()]
            if logadas:
                self.pedir_fechar(logadas)
                for _ in range(20):
                    time.sleep(3)
                    txt = self.janelas()
                    if not any(linha.startswith(p + "|") for p in logadas for linha in txt.splitlines()):
                        break
            for p in list(est.get("lote", [])):
                fechada = p not in jan and time.time() - abertos_em.get(p, 0) > 90
                if p in logadas or fechada:
                    if fechada and p not in logadas:
                        sumiu[p] += 1
                        if sumiu[p] < 2:  # leitura falha às vezes: só conta na 2ª vez seguida
                            continue
                    est["lote"].remove(p)
                    est.setdefault("verificar", []).append(p)
                    self.gravar(est)
                else:
                    sumiu[p] = 0
            fora = set(est["feitas"]) | set(est["puladas"]) | set(est["falhas"]) | set(est.get("lote", [])) \
                | set(est.get("verificar", []))
            ja_logadas = {p for p, v in mr._logins().items()
                          if isinstance((v or {}).get(self.m), dict) and v[self.m].get("google")}
            pend = [(p, e) for p, e in todas if p not in fora and p not in ja_logadas and not _nova_bloqueada(p, self.m)]
            while len(est.setdefault("lote", [])) < n and pend:
                p, e = pend[0]
                if not self.abrir(p, e, k):
                    if not est["lote"] and not est.get("verificar"):
                        print(f"{time.strftime('%H:%M')} {self.m} sem RAM nem pra 1 janela — parei", flush=True)
                        pend = []
                    break  # sem RAM pra mais uma: espera as da tela fecharem
                pend.pop(0)
                k += 1
                est["lote"].append(p)
                _nova_registrar(p, self.m)
                abertos_em[p] = time.time()
                self.gravar(est)
                print(f"{time.strftime('%H:%M')} ABRIU {e}", flush=True)
                time.sleep(4)
            if est.get("verificar"):  # uma por volta, pra não parar de abrir/fechar janelas enquanto confere
                p = est["verificar"][0]
                try:
                    self.verificar(est, p)
                except (RuntimeError, subprocess.TimeoutExpired) as erro:  # perfil ainda preso: confere depois
                    adiou[p] += 1
                    print(f"{time.strftime('%H:%M')} {p}: conferência falhou ({adiou[p]}/3): {erro}", flush=True)
                    est["verificar"].remove(p)
                    if adiou[p] < 3:
                        est["verificar"].append(p)
                    else:
                        est["falhas"] = sorted(set(est["falhas"]) | {p})
                    self.gravar(est)
                    time.sleep(10)
                    continue
                est["verificar"].remove(p)
                self.gravar(est)
                continue
            if not est["lote"] and not pend:
                break
            time.sleep(15)
        if self.win:
            self.ssh(f"echo x > {W}\\monitor_parar.txt")
        else:
            self.ssh(f"{self.r.run} som volta")
        mr.liberar(self.m, quem=VEZ)
        print(f"FIM: feitas {len(est['feitas'])}/{len(todas)} | puladas {est['puladas']} | "
              f"não logaram {est['falhas']}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(1)
    lt = Lote(a[0])
    if a[1:2] == ["estado"]:
        e = lt.ler()
        print(f"feitas {len(e['feitas'])}/{len(lt.contas())} | na tela: {e.get('lote')} | puladas: {e['puladas']} | "
              f"não logaram: {e['falhas']}")
    else:  # notebook (1,8 GB): 2 janelas + a conferência; PC com RAM: 10
        # login_em_lote.py <maq> [N] [so=perfil1,perfil2,...]  -> só essas contas
        so = next((x[3:].split(",") for x in a[1:] if x.startswith("so=")), None)
        nums = [x for x in a[1:] if x.isdigit()]
        lt.monitor(int(nums[0]) if nums else (10 if lt.win else 2), so=so)
