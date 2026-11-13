#!/usr/bin/env python3
"""postar-fila.py — Posta no YouTube os vídeos de UM DIA da fila (respeita cota).

Lê uma fila JSON (gerada por montar-fila.py) e, pra cada item cujo `upload_dia`
== o dia pedido e que ainda NÃO foi postado, faz o upload agendado (privado +
publishAt). É IDEMPOTENTE: grava o status de volta na fila a cada item, então
pode rodar de novo sem repostar o que já subiu. É isso que o CRON de amanhã roda.

⚠️ COTA: YouTube deixa ~6 uploads por dia por canal. A fila já respeita isso
(montar-fila distribui). NÃO tente subir tudo de uma vez.

Uso:
    # posta o que é de HOJE:
    python bin/postar-fila.py --plano workspace/postagem/fila_meek_caps234.json

    # posta o que é de um dia específico (o cron de amanhã usa isto):
    python bin/postar-fila.py --plano .../fila.json --dia 2026-07-02

    # simula sem postar:
    python bin/postar-fila.py --plano .../fila.json --dry-run
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
BRT = timezone(timedelta(hours=-3))
POSTER = PROJECT / "bin" / "youtube_poster.py"
# pausa entre uploads pra não estourar o rateLimitExceeded da API (muitos canais
# compartilham o mesmo projeto). Ajustável por env POSTAR_SLEEP_S.
SLEEP_S = float(os.environ.get("POSTAR_SLEEP_S", "4"))


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def salvar(plano_path, fila):
    Path(plano_path).write_text(json.dumps(fila, ensure_ascii=False, indent=2),
                                encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Posta os vídeos de um dia da fila")
    ap.add_argument("--plano", required=True, help="fila JSON (montar-fila.py)")
    ap.add_argument("--dia", help="YYYY-MM-DD; default = hoje (BRT)")
    ap.add_argument("--dry-run", action="store_true", help="não posta, só mostra")
    args = ap.parse_args()

    plano_path = Path(args.plano)
    if not plano_path.exists():
        print(f"ERRO: fila não encontrada: {plano_path}", file=sys.stderr)
        sys.exit(1)

    fila = json.loads(plano_path.read_text(encoding="utf-8"))
    dia = args.dia or datetime.now(BRT).strftime("%Y-%m-%d")
    itens = fila.get("itens", [])

    # catch-up: posta tudo VENCIDO ou de hoje (upload_dia <= dia). Assim, o que
    # falhou/ficou pra trás sobe automaticamente no próximo dia. Futuro fica pra frente.
    do_dia = [it for it in itens if it.get("upload_dia", "9999-99-99") <= dia]
    pendentes = [it for it in do_dia if it.get("status") != "ok"]

    log(f"Fila: {plano_path.name} | dia alvo (<=): {dia}")
    log(f"  itens vencidos/hoje: {len(do_dia)} | pendentes: {len(pendentes)} | "
        f"já postados: {len(do_dia) - len(pendentes)}")

    if not pendentes:
        log("Nada pendente pra este dia. ✓")
        return

    ok = 0
    for it in pendentes:
        pub_brt = (datetime.fromisoformat(it["publish_at"].replace("Z", "+00:00"))
                   .astimezone(BRT).strftime("%d/%m %H:%M"))
        log(f"  → [{it.get('canal_nome', it['canal'])}] {it['titulo'][:55]}")
        log(f"      arquivo: {Path(it['arquivo']).name}")
        log(f"      publica: {pub_brt} BRT")

        if not Path(it["arquivo"]).exists():
            log(f"      ✗ ARQUIVO SUMIU — pulando")
            it["status"] = "erro"
            it["erro"] = "arquivo não encontrado"
            salvar(plano_path, fila)
            continue

        if args.dry_run:
            log("      (dry-run, não postado)")
            continue

        cmd = [
            sys.executable, str(POSTER),
            "--video", it["arquivo"],
            "--titulo", it["titulo"],
            "--descricao", it["descricao"],
            "--tags", ",".join(it["tags"]),
            "--canal", it["canal"],
            "--privacy", "private",
            "--publish-at", it["publish_at"],
        ]
        try:
            r = subprocess.run(cmd, check=True, capture_output=True, text=True,
                               timeout=900)
            saida = r.stdout.strip()
            it["status"] = "ok"
            it["resultado"] = saida
            it["postado_em"] = datetime.now(BRT).isoformat()
            ok += 1
            log(f"      ✓ {saida}")
        except subprocess.CalledProcessError as e:
            erro = (e.stderr or e.stdout or str(e)).strip()
            it["status"] = "erro"
            it["erro"] = erro[:500]
            log(f"      ✗ ERRO: {erro[:200]}")
        except Exception as e:  # noqa
            it["status"] = "erro"
            it["erro"] = str(e)[:500]
            log(f"      ✗ ERRO: {e}")
        salvar(plano_path, fila)  # grava depois de CADA item (resumível)
        time.sleep(SLEEP_S)       # ritmo p/ não estourar rateLimitExceeded

    restantes = [it for it in itens
                 if it.get("upload_dia", "9999-99-99") <= dia and it.get("status") != "ok"]
    log(f"\n{'=' * 60}")
    log(f"{'✅' if not restantes else '⚠️'} Até {dia}: {ok} postados agora, "
        f"{len(restantes)} ainda pendentes (erro/limite — roda de novo amanhã).")
    # aviso sobre dias futuros
    outros = sorted({it['upload_dia'] for it in itens
                     if it.get('status') != 'ok' and it.get('upload_dia', '') > dia})
    if outros:
        log(f"Dias futuros na fila: {', '.join(outros)}")


if __name__ == "__main__":
    main()
