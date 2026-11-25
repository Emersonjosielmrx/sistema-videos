"""fish_http.py — Fish Audio por HTTP puro, no molde do gemini-argo e do projeto-navegador-sem-navegador.

COMO FUNCIONA (18/11/2026, medido):
- A GERAÇÃO é HTTP puro (`requests` comum serve; roda no python da produção) pela ponte do IP fixo da conta:
  POST https://api.fish.audio/task {type:tts, stream:true, model, parameters:{text,...}, recaptcha} -> o MP3 direto.
  Auth = `Authorization: Bearer <localStorage.token>` (não é cookie).
- O POST /task exige reCAPTCHA Enterprise (sem ele: 400 "Missing reCAPTCHA Enterprise"). Quem fabrica o token é a
  `fabrica_fish.py` (Chrome QUENTE da conta, fora da tela, pela ponte do IP dela, com reserva de tokens prontos).
  Este cliente sobe a fábrica sozinho se ela não responder. O 1º token de um Chrome frio leva 10-40 s; aquecido, ~1 s.
- Saldo: GET /wallet/<workspace>/package (HTTP puro, não gasta).

MELHORIAS sobre o fish_audio.py (que clica na tela; continua como reserva):
- Falas em PARALELO (FISH_PARALELO, padrão 3), nova tentativa em erro de rede/token, ordem preservada.
- CACHE por (voz, texto, velocidade): a mesma fala nunca é paga duas vezes (cache\\<sha1>.mp3).
- Velocidade da fala (`velocidade`, ex. 1.15) — parâmetro prosody.speed da API, testado.
- Saldo REAL lido no fim e gravado no creditos.json (a estimativa por caracteres virava erro com o tempo).
- `gerar_roteiro(falas, saida, email=None, voz=None, juntar=True)` mantém a mesma assinatura de antes.

Regras do COMO_OPERAR.md: conta nunca do Kaggle e só do pool do Fish (a fábrica usa fish_audio.checar_conta);
1 crédito por caractere; sem rodízio de contas grátis para somar cota.

    python fish_http.py "Primeira fala." "Segunda fala." -o PASTA [--velocidade 1.15] [--conta E] [--voz ID]
    python fish_http.py -f roteiro.txt -o PASTA
    python fish_http.py --saldo [--conta E]
    python fish_http.py --estado            (contas quentes na fábrica)
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import fish_audio as fa  # dividir(), CONTA_PADRAO, VOZ_PADRAO (sem efeito colateral no import)

API = "https://api.fish.audio"
FABRICA = f"http://127.0.0.1:{os.environ.get('FISH_FABRICA_PORTA', '9397')}"
PARALELO = int(os.environ.get("FISH_PARALELO", "3"))
CACHE = AQUI / "cache"
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
PYW = Path(sys.executable).with_name("pythonw.exe")


class SemCredito(RuntimeError):
    pass


class PrecisaLogin(RuntimeError):
    pass


# ---------------------------------------------------------------- fábrica de tokens
# 25/11 dona ("todos workers"; "loga os Fish nos outros"): conta cujo dono é OUTRA máquina (sessoes_remotas\donos.json)
# usa a fábrica DAQUELA máquina (fabrica_fish_linux.py, porta 9397 lá) por túnel ssh — o Chrome do reCAPTCHA roda lá,
# não no PC1. A geração (HTTP leve) segue saindo pela ponte rnprmtfo-N da conta = o MESMO IP fixo. Fábrica remota fora
# = a conta NÃO cai pro Chrome do PC1 (1 conta = 1 máquina): falha e o rodízio passa pra próxima. FISH_REMOTA=0 desliga.
_TUNEIS = {}
_FORA = {}  # máquina -> quando falhou (5 min sem tentar de novo)


def _dono(email):
    if os.environ.get("FISH_REMOTA", "1") == "0" or not email:
        return None
    try:
        d = json.loads((AQUI / "sessoes_remotas" / "donos.json").read_text("utf-8"))
    except (OSError, ValueError):
        return None
    m = (d.get(str(email).lower()) or {}).get("maquina")
    return m if m and m != os.environ.get("FISH_MAQUINA", "pc1") else None


def _base(email=None):
    """URL da fábrica que serve a conta: a local, ou a da máquina dona por túnel (sobe o túnel se preciso)."""
    maq = _dono(email)
    if not maq:
        return FABRICA
    t = _TUNEIS.get(maq)
    if t and t[0].poll() is None:
        return f"http://127.0.0.1:{t[1]}"
    if time.time() - _FORA.get(maq, 0) < 300:  # máquina fora há < 5 min: nem tenta (cada fala esperaria o ssh de novo)
        raise RuntimeError(f"fábrica do Fish na máquina {maq} fora (há {int(time.time() - _FORA[maq])} s)")
    import socket
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        porta = so.getsockname()[1]
    proc = subprocess.Popen(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "-o", "ExitOnForwardFailure=yes",
                             "-o", "ServerAliveInterval=15",
                             "-N", "-L", f"{porta}:127.0.0.1:9397", maq],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
    for _ in range(30):
        time.sleep(0.5)
        if proc.poll() is not None:  # ssh caiu (máquina fora/sem rota): não espera os 30 ciclos
            break
        try:
            if requests.get(f"http://127.0.0.1:{porta}/estado", timeout=5).ok:
                _TUNEIS[maq] = (proc, porta)
                return f"http://127.0.0.1:{porta}"
        except requests.RequestException:
            pass
    proc.kill()
    _FORA[maq] = time.time()
    raise RuntimeError(f"fábrica do Fish na máquina {maq} não responde (a conta {email} é de lá — não abro no PC1)")


def _fab(rota, timeout=180, **q):
    r = requests.get(f"{_base(q.get('conta'))}{rota}", params=q, timeout=timeout)
    d = r.json()
    if r.status_code == 401:
        raise PrecisaLogin(d.get("erro"))
    if r.status_code == 403:
        raise SystemExit(d.get("erro"))
    if r.status_code != 200:
        raise RuntimeError(f"fábrica {rota}: {d.get('erro')}")
    return d


def _fabrica_no_ar():
    try:
        return requests.get(f"{FABRICA}/estado", timeout=10).ok  # 3 s cortava a fábrica ocupada abrindo Chrome
    except requests.RequestException:
        return False


def subir_fabrica():
    """Sobe a fabrica_fish.py oculta (pythonw, sem janela) se não estiver no ar."""
    if _fabrica_no_ar():
        return
    py = str(PYW if PYW.exists() else sys.executable)
    subprocess.Popen([py, str(AQUI / "fabrica_fish.py")], cwd=str(AQUI), creationflags=0x08000000,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        time.sleep(0.5)
        if _fabrica_no_ar():
            return
    avisar("Fish Audio: a fábrica de tokens (fabrica_fish.py) não subiu — a narração dos Shorts foi para a voz "
           "reserva (p3). O que fazer: ver D:\\hipercool-materiais\\comum\\fish_audio\\fabrica_fish.log.",
           chave="<SEGREDO_REMOVIDO>")
    raise RuntimeError("a fabrica_fish.py não subiu (ver fabrica_fish.log)")


# ---------------------------------------------------------------- cliente
class FishHTTP:
    def __init__(self, email=None, voz=None):
        self.email = (email or fa.CONTA_PADRAO).lower()
        self.voz = voz or fa.VOZ_PADRAO
        remota = _dono(self.email)
        if not remota:
            subir_fabrica()
        ses = _fab("/sessao", conta=self.email)   # abre/aquece o Chrome da conta na fábrica (daqui ou da dona)
        self.workspace = ses["workspace"]
        self.ip_n = ses.get("ip_n")
        self.s = requests.Session()
        proxy = ses["proxy"]
        if remota:  # o proxy que a fábrica de lá devolve é a ponte DE LÁ; aqui usa a ponte local do MESMO rnprmtfo-N
            proxy = f"http://127.0.0.1:{fa._subir_ponte(int(self.ip_n))}"
        self.s.proxies = {"http": proxy, "https": proxy}   # IP fixo da conta, nunca a casa
        self.s.headers.update({"Authorization": f"Bearer {ses['token']}", "Origin": "https://fish.audio",
                               "Referer": "https://fish.audio/",
                               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                             "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"})

    def saldo(self):
        """(restantes, total) lidos da API — não gasta."""
        r = self.s.get(f"{API}/wallet/{self.workspace}/package", timeout=30)
        if r.status_code != 200:
            return None
        d = r.json()
        return d.get("balance"), d.get("total")

    def _chave(self, texto, velocidade):
        return hashlib.sha1(f"{self.voz}|{velocidade}|{texto}".encode("utf-8")).hexdigest()

    def gerar(self, texto, destino, velocidade=None, tentativas=3):
        """Gera UMA fala (até ~500 caracteres no grátis) em `destino`. Devolve "cache" ou "gerado"."""
        CACHE.mkdir(exist_ok=True)
        cache = CACHE / f"{self._chave(texto, velocidade)}.mp3"
        if cache.exists() and cache.stat().st_size > 2000:
            shutil.copyfile(cache, destino)
            os.utime(cache)  # usado agora: a limpeza tira os mais velhos primeiro
            return "cache"
        if not velocidade or abs(float(velocidade) - 1) <= 0.01:
            # já gerada antes nesta conta (cache local limpo, outra máquina/chat): baixa do histórico, não paga
            try:
                import sessoes_fish
                url = sessoes_fish.do_historico(self.email, self.voz, texto)
                if url:
                    r = self.s.get(url, timeout=60, headers={"Authorization": None})  # CDN: sem login, mas pelo IP da conta
                    if r.status_code == 200 and len(r.content) > 2000:
                        tmp = cache.with_suffix(f".{os.getpid()}.tmp")
                        tmp.write_bytes(r.content)
                        tmp.replace(cache)
                        shutil.copyfile(cache, destino)
                        return "historico"
            except Exception:  # noqa: BLE001 — histórico é economia, não requisito
                pass
        params = {"text": texto, "model_id": self.voz, "format": "mp3", "latency": "balanced",
                  "backend": "drama-3", "normalize": False}
        if velocidade and abs(float(velocidade) - 1) > 0.01:
            params["prosody"] = {"speed": float(velocidade), "volume": 0}
        erro = None
        for k in range(tentativas):
            tok = _fab("/token", conta=self.email)["token"]
            try:
                r = self.s.post(f"{API}/task", timeout=180, json={
                    "type": "tts", "stream": True, "model": self.voz, "latency": "balanced", "parameters": params,
                    "recaptcha": tok, "format": "mp3", "backend": "drama-3"})
            except requests.RequestException as e:
                erro = f"rede: {str(e)[:120]}"
                time.sleep(2 * (k + 1))
                continue
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and ("audio" in ct or "octet" in ct) and len(r.content) > 2000:
                tmp = cache.with_suffix(f".{os.getpid()}.tmp")
                tmp.write_bytes(r.content)
                tmp.replace(cache)
                shutil.copyfile(cache, destino)
                return "gerado"
            txt = r.text[:200]
            if r.status_code in (402,) or "credit" in txt.lower() or "balance" in txt.lower():
                raise SemCredito(f"{self.email}: sem crédito ({txt})")
            if r.status_code == 401:
                raise PrecisaLogin(f"{self.email}: sessão do Fish vencida ({txt})")
            erro = f"HTTP {r.status_code}: {txt}"   # 400 reCAPTCHA recusado / 429 / 5xx: tenta de novo com token novo
            time.sleep(2 * (k + 1))
        raise RuntimeError(f"fala não saiu em {tentativas} tentativas ({erro})")

    def fechar(self):
        """Compatível com o cliente antigo (fish_lote chama). NÃO fecha o Chrome: ele fica quente na fábrica para o
        próximo roteiro e a própria fábrica fecha depois de 15 min parado. Para fechar já: soltar()."""
        self.s.close()

    def soltar(self):
        """Fecha agora o Chrome desta conta na fábrica."""
        if _dono(self.email) or _fabrica_no_ar():
            _fab("/soltar", conta=self.email)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()


CACHE_MAX_MB = int(os.environ.get("FISH_CACHE_MB", "500"))


def limpar_cache(max_mb=CACHE_MAX_MB):
    """Cache passou de max_mb: apaga os MP3 usados há mais tempo até ficar em 80% do teto. Devolve MB liberados.
    Apagar não perde nada: a fala ainda é recuperada do histórico do Fish (sem pagar) enquanto estiver nas 20 últimas."""
    if not CACHE.exists():
        return 0
    arqs = sorted(CACHE.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
    total = sum(p.stat().st_size for p in arqs)
    if total <= max_mb * 1024 * 1024:
        return 0
    alvo, livre = max_mb * 1024 * 1024 * 0.8, 0
    for p in arqs:
        if total - livre <= alvo:
            break
        try:
            tam = p.stat().st_size
            p.unlink()
            livre += tam
        except OSError:
            pass
    return round(livre / 1024 / 1024, 1)


def avisar(texto, chave):
    """Falha do Fish que caiu para o p3: vai para o RESUMO do Telegram (não sai na hora; repetido dentro de 12 h não
    repete). Regra da dona: na hora só erro que ninguém consertou — aqui o p3 já narrou, então é resumo."""
    try:
        sys.path.append(r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "fish", importante=False, chave=f"fish-{chave}", html_ok=False)
    except Exception:  # noqa: BLE001 — aviso é informação, não requisito
        pass


def aquecer(email):
    """Pede à fábrica para abrir a conta e encher a reserva de tokens EM SEGUNDO PLANO (não espera)."""
    try:
        if _dono(email):
            import threading
            threading.Thread(target=lambda: _fab("/sessao", timeout=300, conta=email), daemon=True).start()
            return
        subir_fabrica()
        requests.get(f"{FABRICA}/aquecer", params={"conta": email}, timeout=10)
    except Exception:  # noqa: BLE001 — aquecer é adiantamento, não requisito
        pass


def preaquecer(precisa=450):
    """Chame NO INÍCIO do vídeo (antes do roteiro/imagens): sobe a fábrica e aquece a conta que vai ser usada, em
    segundo plano. Os ~40 s de abrir o Chrome passam enquanto a produção faz o resto; quando a narração chegar, o
    token já está pronto (~2 s por fala). Não espera nada e nunca levanta. Devolve o e-mail escolhido (ou None)."""
    try:
        import creditos
        esc = creditos.escolher(precisa)
        if not esc:
            return None
        import threading
        threading.Thread(target=aquecer, args=(esc[0],), daemon=True).start()
        return esc[0]
    except Exception:  # noqa: BLE001
        return None


def gerar_frases(frases, voz=None, velocidade=None, paralelo=None, log=print, contas_excluir=()):
    """ROTAÇÃO entre contas: frases = [(i, texto, destino_mp3)]. Gera em paralelo na conta de mais crédito; quando o
    saldo dela não cobre o que falta, AQUECE a próxima em segundo plano e troca sem esperar o Chrome abrir.
    Saldo das contas = creditos.json (estimado) + leitura real por HTTP SÓ da conta que vai ser usada (sem Chrome).
    Devolve {i: destino} das frases que saíram. Nunca levanta (o que não sair fica para o p3 de quem chamou).

    Uso pelo fish_lote (ou qualquer um): feitos = fish_http.gerar_frases([(0, "fala", "x.mp3"), ...])"""
    import creditos
    import sessoes_fish
    voz = voz or fa.VOZ_PADRAO
    faltam = [(i, str(t).replace("﻿", "").strip(), d) for i, t, d in frases if t and str(t).strip()]
    feitos, tentadas = {}, set(contas_excluir)

    def escolher(precisa):
        esc = creditos.escolher(min(precisa, 450), excluir=tentadas)
        if not esc:
            return None
        email = esc[0]
        if esc[1] is None:  # renovou / nunca leu: lê o saldo real por HTTP (sem Chrome) antes de confiar
            try:
                sessoes_fish.saldo(email)
            except Exception:  # noqa: BLE001 — sem sessão guardada: a fábrica abre e grava ao usar
                pass
        return email

    email = escolher(sum(len(t) for _, t, _ in faltam))
    while faltam and email:
        tentadas.add(email)
        try:
            f = FishHTTP(email, voz)
        except SystemExit as e:  # Kaggle / fora do pool
            creditos.marcar(email, logado=False, erro=str(e)[:120])
            log(f"[fish] {email}: recusada ({str(e)[:80]})")
            email = escolher(sum(len(t) for _, t, _ in faltam))
            continue
        except PrecisaLogin as e:
            creditos.marcar(email, logado=False, erro="deslogada")
            log(f"[fish] {email}: deslogada — próxima ({str(e)[:80]})")
            email = escolher(sum(len(t) for _, t, _ in faltam))
            continue
        except Exception as e:  # noqa: BLE001
            log(f"[fish] {email}: não abriu ({type(e).__name__}: {str(e)[:100]}) — próxima")
            email = escolher(sum(len(t) for _, t, _ in faltam))
            continue

        # quanto ESTA conta cobre: pega as frases que cabem no saldo estimado (1 crédito por caractere)
        est = creditos.estimado(creditos.carregar().get(email, {}))
        lote, soma = [], 0
        for item in faltam:
            if est is not None and soma + len(item[1]) + 20 > est:
                break
            lote.append(item)
            soma += len(item[1])
        if not lote:
            creditos.marcar(email, restantes=est or 0)
            email = escolher(sum(len(t) for _, t, _ in faltam))
            continue
        proxima = None
        if len(lote) < len(faltam):  # não cobre tudo: a próxima conta já vai aquecendo enquanto esta gera
            resto = sum(len(t) for i, t, _ in faltam if (i, t) not in {(x[0], x[1]) for x in lote})
            esc = creditos.escolher(min(resto, 450), excluir=tentadas)
            if esc:
                proxima = esc[0]
                aquecer(proxima)
                log(f"[fish] {email} cobre {len(lote)}/{len(faltam)} frases — aquecendo {proxima} em paralelo")

        sem_credito = {"v": False}

        def uma(item):
            i, txt, dest = item
            if sem_credito["v"]:
                return i, None
            t0 = time.time()
            try:
                origem = f.gerar(txt, dest, velocidade=velocidade)
                if origem == "gerado":
                    creditos.gastar(email, len(txt))
                log(f"[fish] frase {i} ok ({origem}) em {time.time() - t0:.1f}s ({email})")
                return i, dest
            except SemCredito:
                sem_credito["v"] = True
                creditos.marcar(email, restantes=0, gasto_desde_leitura=0, lido_em=time.strftime("%Y-%m-%dT%H:%M"))
                log(f"[fish] {email}: sem crédito — próxima conta")
            except PrecisaLogin:
                sem_credito["v"] = True
                creditos.marcar(email, logado=False, erro="sessão vencida")
                sessoes_fish.marcar(email, morta=True)
            except Exception as e:  # noqa: BLE001
                log(f"[fish] frase {i} falhou ({str(e)[:120]})")
            return i, None

        with ThreadPoolExecutor(max_workers=max(1, paralelo or PARALELO)) as ex:
            for i, dest in ex.map(uma, lote):
                if dest:
                    feitos[i] = dest
        f.fechar()
        sessoes_fish.saldo_em_fundo(email)  # saldo real em segundo plano: quem chamou já segue montando
        faltam = [x for x in faltam if x[0] not in feitos]
        if not faltam:
            break
        email = proxima if proxima and proxima not in tentadas else escolher(sum(len(t) for _, t, _ in faltam))
    if faltam:
        log(f"[fish] {len(faltam)} frase(s) sem conta com crédito — ficam para o p3")
        motivo = "nenhuma conta do Fish com crédito ou logada" if not feitos else "crédito acabou no meio do roteiro"
        avisar(f"Fish Audio: {len(faltam)} de {len(frases)} falas foram narradas pela voz reserva (p3) — {motivo}. "
               f"Contas tentadas: {', '.join(sorted(tentadas)) or 'nenhuma'}. O que fazer: logar mais contas do pool "
               f"(login_fish.py) ou esperar a renovação do crédito.", chave="<SEGREDO_REMOVIDO>")
    try:
        limpar_cache()
    except Exception:  # noqa: BLE001
        pass
    return feitos


def gerar_roteiro(falas, saida, email=None, voz=None, juntar=True, velocidade=None, paralelo=None):
    """Gera as falas (corta as longas em frases) em saida/fala_NN.mp3, junta em fish_tudo.mp3 e grava
    relatorio.json. Devolve o relatório. Mesma assinatura de antes (+ velocidade/paralelo opcionais)."""
    import creditos
    falas = [str(x).replace("﻿", "").strip() for x in falas]  # BOM de arquivo não vira fala nem gasta crédito
    pedacos = [p for f in falas if f for p in fa.dividir(f)]
    if not pedacos:
        raise SystemExit("nenhuma fala")
    out = Path(saida)
    out.mkdir(parents=True, exist_ok=True)
    f = FishHTTP(email, voz)
    rel = {"conta": f.email, "voz": f.voz, "velocidade": velocidade, "falas": [None] * len(pedacos)}
    parar = {"motivo": None}
    t_ini = time.time()

    def uma(i):
        txt = pedacos[i]
        if parar["motivo"]:
            return {"i": i, "texto": txt, "chars": len(txt), "ok": False, "erro": parar["motivo"]}
        t0 = time.time()
        try:
            origem = f.gerar(txt, out / f"fala_{i:02d}.mp3", velocidade=velocidade)
            if origem == "gerado":
                creditos.gastar(f.email, len(txt))
            r = {"i": i, "texto": txt, "chars": len(txt), "gerar_s": round(time.time() - t0, 1), "ok": True,
                 "origem": origem}
        except (SemCredito, PrecisaLogin) as e:
            parar["motivo"] = str(e)
            r = {"i": i, "texto": txt, "chars": len(txt), "ok": False, "erro": str(e)}
        except Exception as e:  # noqa: BLE001
            r = {"i": i, "texto": txt, "chars": len(txt), "ok": False, "erro": str(e)[:200],
                 "gerar_s": round(time.time() - t0, 1)}
        print(f"fala {i}: {'OK' if r['ok'] else 'FALHOU'} {r.get('origem', '')} em {r.get('gerar_s', 0)}s | "
              f"{txt[:60]}{'' if r['ok'] else ' | ' + r['erro'][:120]}", flush=True)
        return r

    try:
        with ThreadPoolExecutor(max_workers=max(1, paralelo or PARALELO)) as ex:
            for r in ex.map(uma, range(len(pedacos))):
                rel["falas"][r["i"]] = r
    finally:
        rel["total_s"] = round(time.time() - t_ini, 1)
        try:
            sal = f.saldo()
            if sal:
                rel["saldo"] = {"restantes": sal[0], "total": sal[1]}
                creditos.marcar(f.email, restantes=sal[0], total=sal[1], logado=True, erro=None,
                                gasto_desde_leitura=0, lido_em=time.strftime("%Y-%m-%dT%H:%M"))
        except Exception:  # noqa: BLE001 — saldo é informação, não requisito
            pass
        (out / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")

    partes = [out / f"fala_{i:02d}.mp3" for i, r in enumerate(rel["falas"]) if r and r["ok"]]
    if juntar and partes:
        lista = out / "_lista.txt"
        lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in partes), encoding="utf-8")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                        "-af", "apad=pad_dur=0.25", str(out / "fish_tudo.mp3")], check=False,
                       creationflags=0x08000000)
        lista.unlink()
    ok = sum(1 for r in rel["falas"] if r and r["ok"])
    print(f"PRONTO: {ok}/{len(pedacos)} falas em {rel['total_s']}s -> {out} | saldo {rel.get('saldo')}", flush=True)
    if parar["motivo"]:
        print("PAROU:", parar["motivo"], flush=True)
    return rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("falas", nargs="*")
    ap.add_argument("-f", "--arquivo")
    ap.add_argument("-o", "--saida")
    ap.add_argument("--voz", default=fa.VOZ_PADRAO)
    ap.add_argument("--conta", default=fa.CONTA_PADRAO)
    ap.add_argument("--velocidade", type=float)
    ap.add_argument("--paralelo", type=int)
    ap.add_argument("--saldo", action="store_true")
    ap.add_argument("--estado", action="store_true")
    a = ap.parse_args()
    if a.estado:
        print(json.dumps(_fab("/estado") if _fabrica_no_ar() else {"fabrica": "fora do ar"}, indent=1))
        return
    if a.saldo:
        print(FishHTTP(a.conta, a.voz).saldo())
        return
    if not a.saida:
        ap.error("-o/--saida é obrigatório para gerar")
    falas = list(a.falas)
    if a.arquivo:
        falas += [l.strip() for l in Path(a.arquivo).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    # 18/11 (pedido do chat da produção): geração pela linha de comando (testes) respeita a mesma trava do
    # fish_lote — uma geração por vez neste PC. Só aqui: as funções de biblioteca não travam, porque o fish_lote
    # já segura a trava e chama o FishHTTP por dentro (travar de novo = esperar por si mesmo).
    import fish_lote
    if not fish_lote._travar(prazo=600):
        raise SystemExit("outra geração do Fish ocupando há 10 min (_em_uso.lock) — tente depois")
    try:
        gerar_roteiro(falas, a.saida, email=a.conta, voz=a.voz, velocidade=a.velocidade, paralelo=a.paralelo)
    finally:
        fish_lote._soltar()


if __name__ == "__main__":
    main()
