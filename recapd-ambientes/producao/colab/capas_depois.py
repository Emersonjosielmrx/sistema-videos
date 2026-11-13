"""capas_depois.py — gera a capa do longo DEPOIS do envio e aplica no vídeo pelo Studio (05/11/2026).

Dona 05/11 ("resolva o gargalo de postagem"): a preparação de cada longo ficava 1 h+ esperando o Google Flow gerar a
capa (gera_imagem.py nos notebooks, ocupados/instáveis) e só então subia. Agora o postar_longos sobe com
ANIME_CAPA_DEPOIS=1 (o vídeo vai AGENDADO, sem esperar) e registra o pedido em colab\\capas_depois.json; aqui, um por
vez, gera as MESMAS capas do anime_publish (capa_ia_anime.gerar_capa = capa A; capas_ab = B/C do teste) e aplica:
2-3 capas = teste A/B do Studio (--ab), 1 = troca a miniatura (--capa). Depois, se o vídeo está no publicar_ja, abre.
Capa que não sai em CAPA_MAX_TENTATIVAS fica com a miniatura automática do YouTube (aviso no Telegram).

    pythonw capas_depois.py         # tarefa CapasDepois, 10 em 10 min (trava própria: 1 rodada por vez)
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BIN = AQUI.parent / "bin"
FILA = AQUI / "capas_depois.json"
LOG = AQUI / "capas_depois.log"
PY_EXTRAS = r"D:\manhwa-react\.venv\Scripts\python.exe"
EXTRAS = r"D:\postador-de-videos\bin\youtube_studio_extras.py"
CAPA_MAX_TENTATIVAS = 3


def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {m}\n")


def ler():
    try:
        return json.loads(FILA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def gravar(fila):
    FILA.write_text(json.dumps(fila, ensure_ascii=False, indent=1), encoding="utf-8")


def registrar(cred, vid, pasta, params, publicar):
    """Chamado pelo postar_longos depois do envio ok."""
    fila = ler()
    fila.append({"canal": cred, "vid": vid, "pasta": str(pasta), "params": params, "publicar": bool(publicar),
                 "estado": "pendente", "tentativas": 0, "em": datetime.now().isoformat("T", "minutes")})
    gravar(fila)


def _studio(cred, vid, *args, timeout=1800):
    # 07/11 (-gprBunwSXQ): ID que começa com "-" virava opção no argparse ("--video: expected one argument")
    r = subprocess.run([PY_EXTRAS, EXTRAS, "--canal", cred, f"--video={vid}", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout, cwd=str(Path(EXTRAS).parent),
                       creationflags=0x08000000)
    res = [l for l in (r.stdout + r.stderr).splitlines() if "RESULTADO" in l]
    return res[-1][:200] if res else (r.stdout + r.stderr)[-200:]


def _sem_ab(cred):
    """Canal com recursos avançados negados (recursos_negados.json do postador) = o teste A/B não entra."""
    if os.environ.get("CAPAS_DEPOIS_SO_A_SEM_AB", "1") == "0":
        return False
    try:
        mapa = json.loads(Path(r"D:\postador-de-videos\config\youtube_navegador.json").read_text(encoding="utf-8"))
        neg = json.loads(Path(r"D:\postador-de-videos\config\recursos_negados.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    hoje = datetime.now().date().isoformat()
    for slug, e in mapa.get("canais", {}).items():
        if cred in e.get("creds", []):
            x = neg.get(slug)
            return bool(x) and not (x.get("ate") and hoje >= x["ate"])
    return False


def um(item):
    sys.path.insert(0, str(BIN))
    os.chdir(BIN)
    import capa_ia_anime
    p, pasta = item["params"], Path(item["pasta"])
    pasta.mkdir(parents=True, exist_ok=True)
    capa = pasta / "capa.jpg"
    t0 = time.time()
    # 05/11: capa já gerada numa tentativa anterior (só o Studio falhou) = reaproveita, não gasta outra geração.
    # 06/11 (nd67FAr0h14, plantão): o anime_publish com capa depois deixa um QUADRO DO VÍDEO em capa.jpg (fallback,
    # só referência) e aqui ele passava por "capa já gerada" -> subia o quadro como capa A em vez da capa IA. Só
    # reaproveita se tem o capa.capa.json (sinal de que a capa IA saiu); senão gera.
    ja_gerada = capa.exists() and capa.stat().st_size > 20_000 and capa.with_suffix(".capa.json").exists()
    ok = ja_gerada or bool(capa_ia_anime.gerar_capa(p["anime"], p["cap"], str(capa), texto=p.get("texto", ""), cena=p.get("cena", ""),
                                       protagonista=p.get("protagonista", ""), generos=p.get("generos"),
                                       formato=p.get("formato", "16:9"), source_url=p.get("source_url", "")))
    if not ok or not capa.exists():
        return False
    capas = [capa]
    # 07/11 (plantão): nova tentativa só porque o Studio falhou regerava a B/C (~60 min cada vez no Flow). Já gerada
    # (tem o .capa.json) = reaproveita. CAPAS_DEPOIS_REUSAR_AB=0 desliga.
    prontas = [pasta / f"capa_{l}.jpg" for l in "bc"
               if (pasta / f"capa_{l}.jpg").exists() and (pasta / f"capa_{l}.capa.json").exists()]
    if ja_gerada and prontas and os.environ.get("CAPAS_DEPOIS_REUSAR_AB", "1") != "0":
        capas += prontas
    elif _sem_ab(item["canal"]):
        # 11/11 dona: "se naquele canal não pode usar mais de uma capa (recursos banidos), não precisa fazer 3 capas,
        # apenas uma" — B/C gastavam ~60 min de Flow cada e eram jogadas fora. CAPAS_DEPOIS_SO_A_SEM_AB=0 desliga.
        log(f"{item['vid']}: canal sem teste A/B (recursos avançados negados) — só a capa A")
    elif p.get("source_url"):
        try:
            extras = capa_ia_anime.capas_ab(p["source_url"], str(capa), p.get("texto", ""), p.get("cena", ""),
                                            p.get("generos")) or []
            capas += [Path(x) for x in extras if Path(x).exists()]
        except Exception as e:  # noqa: BLE001 — teste A/B é extra
            log(f"{item['vid']}: capas do teste A/B falharam ({type(e).__name__})")
    log(f"{item['vid']}: {len(capas)} capa(s) em {(time.time() - t0) / 60:.0f} min")
    if len(capas) >= 2:
        res = _studio(item["canal"], item["vid"], "--ab", ",".join(str(c) for c in capas[:3]))
        if not re.search(r'"teste_ab": "(ok|ja)', res):  # 05/11: canal sem recursos avançados (A/B negado) = capa A só
            log(f"{item['vid']}: teste A/B não entrou ({res[:120]}) — aplica só a capa A")
            res = _studio(item["canal"], item["vid"], "--capa", str(capa))
    else:
        res = _studio(item["canal"], item["vid"], "--capa", str(capa))
    log(f"{item['vid']}: aplicada no Studio: {res}")
    # 05/11: "aviso: TimeoutError" (fiYW0vWk0Yo) e página de edição que não abriu (pXI9) viravam "feito" sem capa
    if not re.search(r'"(capa|teste_ab)": "(enviada|ok|ja)', res):
        log(f"{item['vid']}: Studio NÃO confirmou a capa — tenta de novo na próxima rodada")
        return False
    if item.get("publicar"):
        log(f"{item['vid']}: público: {_studio(item['canal'], item['vid'], '--visibilidade', 'public')}")
    return True


TAPA_BURACO_MIN = int(os.environ.get("CAPA_TAPA_BURACO_MIN", "30"))


def _capa_reserva(item, usadas):
    """Capa pronta no padrão (capa_b/capa_c com .capa.json, nunca usada no ar) de OUTRO longo da MESMA série
    (postar_longos._serie pelo nome da ficha); sem série = None."""
    try:
        import postar_longos as pl
        est = pl._estado()
        meu = next((x for x in est.get("postados", []) if str(x.get("url", "")).endswith(item["vid"])), None)
        serie = pl._serie(meu["nome"]) if meu else None
        if not serie:
            return None
        for x in est.get("postados", []):
            if pl._serie(x.get("nome", "")) != serie:
                continue
            outro = next((y for y in ler() if str(x.get("url", "")).endswith(y["vid"])), None)
            if not outro:
                continue
            for l in "cb":
                c = Path(outro["pasta"]) / f"capa_{l}.jpg"
                if c.exists() and c.with_suffix(".capa.json").exists() and str(c) not in usadas:
                    return c
    except Exception:  # noqa: BLE001
        return None
    return None


def tapar_buracos():
    """11/11 dona ("as partes 11 e 12 estão sem capa, isso não pode acontecer"): longo pendente há mais de
    TAPA_BURACO_MIN sem capa no ar recebe JÁ uma capa reserva no padrão (da mesma série) pelo Studio; a capa própria
    continua na fila e troca depois. CAPA_TAPA_BURACO=0 desliga."""
    if os.environ.get("CAPA_TAPA_BURACO", "1") == "0":
        return
    fila = ler()
    usadas = {x.get("reserva") for x in fila if x.get("reserva")}
    mudou = False
    for x in fila:
        if x["estado"] != "pendente" or x.get("reserva"):
            continue
        try:
            idade = (datetime.now() - datetime.fromisoformat(x["em"])).total_seconds() / 60
        except ValueError:
            continue
        if idade < TAPA_BURACO_MIN or x.get("refazer"):  # refeitas já têm capa antiga no ar
            continue
        c = _capa_reserva(x, usadas)
        if not c:
            continue
        res = _studio(x["canal"], x["vid"], "--capa", str(c))
        log(f"{x['vid']}: sem capa há {idade:.0f} min — capa reserva da série ({c.parent.name}/{c.name}): {res}")
        if re.search(r'"capa": "(enviada|ok|ja)', res):
            x["reserva"] = str(c)
            usadas.add(str(c))
            mudou = True
    if mudou:  # relê (a rodada pode ter mudado outro item) e só marca a reserva, mantendo a ordem da fila
        marcas = {x["vid"]: x["reserva"] for x in fila if x.get("reserva")}
        atual = ler()
        for y in atual:
            if y["vid"] in marcas:
                y["reserva"] = marcas[y["vid"]]
        gravar(atual)


def _vagas():
    """13/11 dona ("não precisa fazer só 3: cada notebook pequeno faz uma por vez (acer e x200ma); STI, desktop e PC2
    fazem várias; não é pra ter gargalo nunca"): vagas = soma da capacidade de cada máquina do Flow — acer 1 +
    x200ma 1 + o limite dinâmico do STI/desktop/PC2 em flow-imagens\\logs\\capacidade.json (sobe sozinho quando dá
    certo, cai quando falha). CAPAS_VAGAS=N fixa um número."""
    if os.environ.get("CAPAS_VAGAS"):
        return int(os.environ["CAPAS_VAGAS"])
    try:
        cap = json.loads(Path(r"D:\flow-imagens\logs\capacidade.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cap = {}
    return 2 + sum(int((cap.get(m) or {}).get("limite") or 1) for m in ("sti", "desktop", "pc2"))


VAGAS = _vagas()


def _reservar(vid):
    """13/11: reserva o item pra esta vaga (arquivo exclusivo) — 2 vagas nunca fazem a mesma capa. Reserva com mais
    de 3 h = vaga que morreu: libera."""
    r = AQUI / "capas_reservas" / f"{vid}.lock"
    r.parent.mkdir(exist_ok=True)
    try:
        if r.exists() and time.time() - r.stat().st_mtime > 3 * 3600:
            r.unlink()
        fd = os.open(str(r), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return r
    except OSError:
        return None


def rodada():
    """13/11 dona ("por que tem capas pendentes? temos vários computadores"): antes UMA rodada fazia a fila em série
    (20-40 min cada capa = 13 na fila levavam 5-8 h). Agora até CAPAS_VAGAS (3) rodadas ao mesmo tempo, cada uma com a
    sua trava e reservando o item antes de fazer. CAPAS_VAGAS=1 volta ao jeito antigo."""
    import msvcrt
    trava, vaga = None, None
    for i in range(max(1, VAGAS)):
        t = open(AQUI / ("capas_depois.lock" if i == 0 else f"capas_depois_{i}.lock"), "w")
        try:
            msvcrt.locking(t.fileno(), msvcrt.LK_NBLCK, 1)
            trava, vaga = t, i
            break
        except OSError:
            t.close()
    if trava is None:
        return
    if vaga == 0:
        try:
            tapar_buracos()
        except Exception as e:  # noqa: BLE001
            log(f"tapar buracos falhou ({type(e).__name__}: {e})")
    tentados = set()  # 1 tentativa por item por rodada (falhou = próxima rodada, 10 min depois)
    while True:
        fila = ler()
        pend = [x for x in fila if x["estado"] == "pendente" and x["vid"] not in tentados]
        if not pend:
            return
        res = None
        for item in pend:
            tentados.add(item["vid"])
            res = _reservar(item["vid"])
            if res:
                break
        if not res:
            return
        if vaga:
            log(f"{item['vid']}: vaga {vaga + 1} de {VAGAS}")
        try:
            feito = um(item)
        except Exception as e:  # noqa: BLE001
            log(f"{item['vid']}: erro {type(e).__name__}: {str(e)[:200]}")
            feito = False
        finally:
            res.unlink(missing_ok=True)
        _fechar_item(item, feito)


def _fechar_item(item, feito):
    """Grava o resultado do item (lê a fila de novo: outra vaga pode ter gravado no meio)."""
    if True:
        fila = ler()
        for x in fila:
            if x["vid"] == item["vid"]:
                x["tentativas"] = x.get("tentativas", 0) + 1
                if feito:
                    x["estado"] = "feito"
                # 12/11: refeita (capa antiga já no ar) caía em sem_capa a cada 3 rodadas só porque o Flow estava sem
                # máquina; ela tem folga de CAPA_MAX_REFEITA (12) e não avisa no Telegram
                elif x["tentativas"] >= (int(os.environ.get("CAPA_MAX_REFEITA", "12")) if x.get("refazer")
                                         else CAPA_MAX_TENTATIVAS):
                    x["estado"] = "sem_capa"
                    try:
                        sys.path.insert(0, r"D:\video-fila")
                        import avisos
                        avisos.enviar(f"🖼️ Longo {x['vid']} ({x['canal']}) ficou SEM capa gerada depois de "
                                      f"{CAPA_MAX_TENTATIVAS} tentativas — segue com a miniatura do YouTube",
                                      "recap-longo", importante=True, html_ok=False)
                    except Exception:  # noqa: BLE001
                        pass
        gravar(fila)


if __name__ == "__main__":
    rodada()
