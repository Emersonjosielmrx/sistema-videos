r"""tiktok_pausar_zeradas.py — 11/11 dona ("as 19 contas mortas... tiktok pode ir fazendo", regra 1 conta por IP).

1. Pausa (campo "pausada" em reuso_plataformas.json > tiktok > contas) as contas com TODOS os vídeos em 0 views na
   última leitura (TIKTOK_VISUALIZACOES.md). Não posta mais nelas = não gasta vídeo nem IP.
2. Redistribui os 9 IPs fixos do Webshare grátis (proxy_tiktok.json) entre as contas ATIVAS, as de mais views
   primeiro: as 9 melhores ficam SOZINHAS num IP. As que sobram ficam marcadas "sem_ip_proprio" e também pausadas
   (regra da casa: nunca 2 contas pelo mesmo IP) até haver IP exclusivo (Webshare pago).
   Despausar uma conta: apagar "pausada" dela. Desligar tudo: TIKTOK_PAUSADAS=0 no postar_tiktok_auto.

Só mexe em arquivo de config (não fala com o TikTok). Backup .bkp_<hora> antes de gravar.

    python tiktok_pausar_zeradas.py          # mostra o plano
    python tiktok_pausar_zeradas.py --fazer
"""
import json
import re
import shutil
import sys
import time
from pathlib import Path

RAIZ = Path(r"D:\postador-de-videos")
REUSO = RAIZ / "config" / "reuso_plataformas.json"
MAPA = RAIZ / "config" / "proxy_tiktok.json"
VIEWS = RAIZ / "TIKTOK_VISUALIZACOES.md"
IPS = list(range(1, 11))  # 12/11: 10 IPs (o -10 existe; ver docs\TIKTOK_IPS_COMPARTILHADOS.md)


def ler_views():
    """{conta_cofre: (views, videos_em_0, videos)} da tabela."""
    out = {}
    for l in VIEWS.read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) >= 8 and c[0] and c[0] not in ("Conta (cofre)",) and not c[0].startswith("---"):
            nome = c[0].split(" ")[0]
            try:
                out[nome] = (int(c[4]), int(c[7]), int(c[3]))
            except ValueError:
                pass
    return out


def main(fazer):
    reuso = json.loads(REUSO.read_text(encoding="utf-8"))
    contas = reuso["tiktok"]["contas"]
    mapa = json.loads(MAPA.read_text(encoding="utf-8"))
    v = ler_views()
    ativas, pausar = [], []
    for conta, r in contas.items():
        cof = r.get("cofre") or conta
        vv = v.get(cof) or v.get(conta)
        if vv and vv[0] == 0 and vv[2] > 0:
            pausar.append((conta, "todos os vídeos em 0 views"))
        else:
            ativas.append((conta, vv[0] if vv else -1))
    ativas.sort(key=lambda x: -x[1])
    com_ip = ativas[:len(IPS)]
    sem_ip = ativas[len(IPS):]
    # trocar o IP de conta logada é sinal ruim pro TikTok: quem já usa um IP livre fica nele
    novo, livres = {}, list(IPS)
    for c, _ in com_ip:
        atual = mapa["contas"].get(c)
        if atual in livres:
            novo[c] = atual
            livres.remove(atual)
    for c, _ in com_ip:
        if c not in novo:
            novo[c] = livres.pop(0)
    print(f"{len(contas)} contas | pausar por 0 views: {len(pausar)} | ativas: {len(ativas)}")
    print("IP próprio (1 conta por IP):")
    for c, vv in com_ip:
        print(f"  IP {novo[c]}: {c} ({vv} views){'' if mapa['contas'].get(c) == novo[c] else ' (troca do IP ' + str(mapa['contas'].get(c)) + ')'}")
    print(f"Sem IP próprio (pausadas até ter IP exclusivo): {len(sem_ip)}")
    for c, vv in sem_ip:
        print(f"  {c} ({vv} views)")
    if not fazer:
        return
    h = time.strftime("%Y%m%d_%H%M")
    shutil.copy2(REUSO, REUSO.with_name(REUSO.name + f".bkp_{h}"))
    shutil.copy2(MAPA, MAPA.with_name(MAPA.name + f".bkp_{h}"))
    for c, motivo in pausar:
        contas[c]["pausada"] = f"11/11: {motivo}"
    for c, _ in sem_ip:
        contas[c]["pausada"] = "11/11: sem IP próprio (9 IPs grátis já usados pelas de mais views)"
    for c, _ in com_ip:
        contas[c].pop("pausada", None)
    # pausadas mantêm a entrada antiga (histórico), mas nenhuma ativa divide IP
    mapa["contas"] = {**{k: x for k, x in mapa["contas"].items() if k not in novo}, **novo}
    mapa["_ativas_1_por_ip"] = {"em": h, "contas": novo}
    __import__("politica").gravar_json(REUSO, reuso, indent=1)  # 12/11: atômico (antes write_text direto)
    MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    print("gravado")


def compartilhar(fazer):
    """12/11 (dona escolheu "todas dividindo IP"): TODAS as contas do TikTok voltam a postar pelos 10 IPs grátis.
    - As 10 de mais views ficam 1 por IP (espalhadas: nenhuma boa divide IP com outra boa).
    - As demais completam os IPs, equilibrando quantas contas cada IP tem.
    - Quem já tem IP FICA nele (trocar o IP de conta logada é sinal ruim pro TikTok); só move se o IP for de outra boa.
    - Tira a "pausada" de todas (por 0 views ou por falta de IP). Grava a lista das boas em proxy_tiktok.json
      "_boas" (o vigia_tiktok_ip.py compara as postagens novas delas com a média).
    Desfazer: voltar os .bkp_<hora> de reuso_plataformas.json e proxy_tiktok.json, ou rodar main(--fazer)."""
    from collections import Counter
    reuso = json.loads(REUSO.read_text(encoding="utf-8"))
    contas = reuso["tiktok"]["contas"]
    mapa = json.loads(MAPA.read_text(encoding="utf-8"))
    v = ler_views()
    def views(c):
        r = contas[c]
        vv = v.get(r.get("cofre") or c) or v.get(c)
        return vv[0] if vv else -1
    # 12/11: "boa" = a que está CRESCENDO (views ganhas nos últimos 5 dias, vídeo a vídeo); só o total antigo pegava
    # contas paradas desde 06/11 (fabricadeautomacoes0: 2.902 views e 0 ganho em 6 dias). Total desempata.
    sys.path.insert(0, str(RAIZ / "bin"))
    from datetime import date, timedelta
    import vigia_tiktok_ip as vg
    def cresc(c):
        cof = contas[c].get("cofre")
        return sum(g for g in (vg.ganho(c, date.today() - timedelta(days=i), cof) for i in range(0, 6)) if g)
    ordem = sorted(contas, key=lambda c: (-cresc(c), -views(c)))
    # 12/11: NINGUÉM troca de IP (trocar o IP de conta logada é sinal ruim pro TikTok). Conta sem IP vai pro IP com
    # menos contas (o 10, novo, recebe as sem IP). "Boa" de cada IP = a que mais cresce dentro dele (o vigia protege).
    novo, uso = {}, Counter()
    for c in ordem:
        if mapa["contas"].get(c) in IPS:
            novo[c] = mapa["contas"][c]
            uso[novo[c]] += 1
    for c in ordem:
        if c not in novo:
            novo[c] = min(IPS, key=lambda n: (uso[n], n))
            uso[novo[c]] += 1
    boas = [next(c for c in ordem if novo[c] == n) for n in IPS if any(novo[c] == n for c in ordem)]
    print(f"{len(contas)} contas | boas (1 por IP): {len(boas)}")
    for n in IPS:
        grupo = [c for c, x in novo.items() if x == n]
        boa = next((c for c in grupo if c in boas), "-")
        print(f"  IP {n:2d}: {len(grupo)} contas | boa: {boa} (+{cresc(boa) if boa != '-' else 0} em 6 dias, "
              f"{views(boa) if boa != '-' else ''} no total) | "
              + ", ".join(c for c in grupo if c != boa)[:150])
    mudou = [c for c in novo if mapa["contas"].get(c) not in (None, novo[c])]
    print(f"trocam de IP: {len(mudou)} ({', '.join(mudou)[:200]})")
    print(f"despausar: {sum(1 for c in contas if contas[c].get('pausada'))}")
    if not fazer:
        return
    h = time.strftime("%Y%m%d_%H%M")
    shutil.copy2(REUSO, REUSO.with_name(REUSO.name + f".bkp_{h}"))
    shutil.copy2(MAPA, MAPA.with_name(MAPA.name + f".bkp_{h}"))
    for c in contas:
        contas[c].pop("pausada", None)
    mapa["contas"] = {**mapa["contas"], **novo}
    mapa["_boas"] = {"em": h, "contas": {c: novo[c] for c in boas},
                     "_leia": "12/11: 10 contas de mais views, 1 por IP; o vigia_tiktok_ip.py compara o post novo delas "
                              "com a média e pausa as outras do mesmo IP se cair."}
    mapa.pop("_ativas_1_por_ip", None)
    __import__("politica").gravar_json(REUSO, reuso, indent=1)  # 12/11: atômico (antes write_text direto)
    MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gravado (backup .bkp_{h})")


if __name__ == "__main__":
    if "--compartilhar" in sys.argv:
        compartilhar("--fazer" in sys.argv)
    else:
        main("--fazer" in sys.argv)
