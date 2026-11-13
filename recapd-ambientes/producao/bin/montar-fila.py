#!/usr/bin/env python3
"""montar-fila.py — Constrói a FILA de postagem (quem posta o quê, onde, quando).

Lê um CONFIG JSON simples e gera a fila que o `postar-fila.py` executa. Faz:
  1. Junta, por capítulo: o vídeo COMPLETO + os SHORTS já cortados.
  2. Distribui IGUALMENTE entre os canais (shorts do mesmo cap ficam JUNTOS no
     mesmo canal — senão o CTA "parte X no meu perfil" quebra).
  3. Respeita a COTA (~6 uploads por canal por dia): enche dia por dia. Os
     capítulos COMPLETOS vão pro primeiro dia.
  4. Espalha os horários de publicação ao longo do dia (slots BRT ideais).

Uso:
    python bin/montar-fila.py --config workspace/postagem/config_fila.json

O CONFIG tem este formato (edite os caminhos e rode de novo pra outras obras):
{
  "obra": "The Meek Cat",
  "quota_por_canal_dia": 6,
  "dia_inicio": "2026-07-01",
  "slots_brt": ["10:30","12:00","13:30","15:00","16:30","18:00","19:30","21:00"],
  "canais": ["inovare recap manga", "nova conta de manga br"],
  "caps": [
    {"cap": 2, "completo": "D:/.../cap2_CENSURADO.mp4",
     "shorts_dir": "D:/hipercool-producao/workspace/shorts/the-meek-cat-cap2"}
  ],
  "saida": "workspace/postagem/fila_meek_caps234.json"
}
"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "bin"))
import postagem_meta as PM  # noqa: E402

BRT = timezone(timedelta(hours=-3))


def _brt_to_utc_iso(dia_str, hhmm):
    h, m = map(int, hhmm.split(":"))
    y, mo, d = map(int, dia_str.split("-"))
    dt = datetime(y, mo, d, h, m, tzinfo=BRT)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _pick_slots(n, pool):
    """Escolhe n horários espalhados uniformemente do pool."""
    if n <= 0:
        return []
    if n == 1:
        return [pool[len(pool) // 2]]
    if n >= len(pool):
        return pool[:n] if n <= len(pool) else pool + pool[:(n - len(pool))]
    idx = [round(i * (len(pool) - 1) / (n - 1)) for i in range(n)]
    return [pool[i] for i in idx]


def _shorts_do_cap(shorts_dir):
    """Retorna lista ordenada de arquivos *_parteNN.mp4."""
    d = Path(shorts_dir)
    arquivos = sorted(d.glob("*_parte*.mp4"))
    return arquivos


def main():
    ap = argparse.ArgumentParser(description="Constrói a fila de postagem")
    ap.add_argument("--config", required=True, help="config JSON (ver docstring)")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    obra = cfg["obra"]
    quota = int(cfg.get("quota_por_canal_dia", 6))
    dia0 = cfg["dia_inicio"]
    slots = cfg.get("slots_brt",
                    ["10:30", "12:00", "13:30", "15:00", "16:30",
                     "18:00", "19:30", "21:00"])
    canais = cfg["canais"]
    assert len(canais) >= 1

    # remove slots que já passaram SE dia0 for hoje
    hoje = datetime.now(BRT).strftime("%Y-%m-%d")
    if dia0 == hoje:
        agora = datetime.now(BRT)
        slots = [s for s in slots
                 if datetime.strptime(f"{dia0} {s}", "%Y-%m-%d %H:%M")
                 .replace(tzinfo=BRT) > agora + timedelta(minutes=20)]
        if not slots:  # tudo passou; usa a partir de agora, de hora em hora
            base = (agora + timedelta(minutes=30)).replace(minute=0, second=0)
            slots = [(base + timedelta(hours=i)).strftime("%H:%M") for i in range(8)]

    # 1. blocos (o que precisa ficar junto)
    blocos = []
    for c in cfg["caps"]:
        cap = c["cap"]
        # bloco COMPLETO (1 item)
        blocos.append({
            "tipo": "completo", "cap": cap, "tamanho": 1,
            "itens": [{
                "id": f"cap{cap}_completo", "arquivo": c["completo"],
                "tipo": "completo", "cap": cap, "parte": None,
                "titulo": PM.titulo_completo(obra, cap),
                "descricao": PM.descricao_completo(obra, cap),
                "tags": PM.tags(obra, cap),
            }],
        })
        # bloco SHORTS (N itens, ordem = parte)
        arquivos = _shorts_do_cap(c["shorts_dir"])
        total = len(arquivos)
        if total == 0:
            print(f"⚠️ AVISO: cap {cap} sem shorts em {c['shorts_dir']}",
                  file=sys.stderr)
        itens_short = []
        for i, arq in enumerate(arquivos):
            parte = i + 1
            itens_short.append({
                "id": f"cap{cap}_short_pt{parte:02d}", "arquivo": str(arq),
                "tipo": "short", "cap": cap, "parte": parte,
                "titulo": PM.titulo_short(obra, cap, parte, total),
                "descricao": PM.descricao_short(obra, cap, parte, total),
                "tags": PM.tags(obra, cap),
            })
        if itens_short:
            blocos.append({"tipo": "short", "cap": cap,
                           "tamanho": len(itens_short), "itens": itens_short})

    # 2. distribui blocos entre canais balanceando nº de itens (maiores primeiro)
    canal_itens = {ch: [] for ch in canais}
    for bloco in sorted(blocos, key=lambda b: -b["tamanho"]):
        alvo = min(canais, key=lambda ch: len(canal_itens[ch]))
        canal_itens[alvo].extend(bloco["itens"])

    # 3. dias por canal (completos primeiro → dia0) + 4. horários espalhados
    fila_itens = []
    for ch in canais:
        itens = canal_itens[ch]
        # ordena: completos primeiro, depois shorts por cap/parte
        itens.sort(key=lambda it: (0 if it["tipo"] == "completo" else 1,
                                   it["cap"], it["parte"] or 0))
        # agrupa por dia conforme a cota
        por_dia = {}
        for idx, it in enumerate(itens):
            offset = idx // quota
            dia = (datetime.strptime(dia0, "%Y-%m-%d") +
                   timedelta(days=offset)).strftime("%Y-%m-%d")
            it["upload_dia"] = dia
            por_dia.setdefault(dia, []).append(it)
        # atribui horários espalhados por (canal, dia)
        for dia, grupo in por_dia.items():
            escolhidos = _pick_slots(len(grupo), slots)
            for it, hhmm in zip(grupo, escolhidos):
                it["canal"] = ch
                it["publish_at"] = _brt_to_utc_iso(dia, hhmm)
                it["publish_brt"] = f"{dia} {hhmm}"
                it["status"] = "pendente"
                fila_itens.append(it)

    # ordena a fila por dia/hora pra leitura humana
    fila_itens.sort(key=lambda it: (it["upload_dia"], it["publish_at"]))

    fila = {
        "obra": obra,
        "gerado_em": datetime.now(BRT).isoformat(),
        "quota_por_canal_dia": quota,
        "canais": canais,
        "total_itens": len(fila_itens),
        "itens": fila_itens,
    }

    saida = Path(cfg["saida"])
    if not saida.is_absolute():
        saida = PROJECT / saida
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(fila, ensure_ascii=False, indent=2),
                     encoding="utf-8")

    # resumo legível
    print(f"\n✅ Fila gerada: {saida}")
    print(f"   Total: {len(fila_itens)} vídeos\n")
    dias = sorted({it["upload_dia"] for it in fila_itens})
    for dia in dias:
        do_dia = [it for it in fila_itens if it["upload_dia"] == dia]
        marca = " (HOJE)" if dia == hoje else ""
        print(f"── DIA {dia}{marca} — {len(do_dia)} uploads ──")
        for ch in canais:
            chit = [it for it in do_dia if it["canal"] == ch]
            if chit:
                print(f"   [{ch}] ({len(chit)}):")
                for it in chit:
                    hhmm = it["publish_brt"].split()[1]
                    print(f"      {hhmm}  {it['titulo'][:58]}")
        print()


if __name__ == "__main__":
    main()
