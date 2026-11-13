# -*- coding: utf-8 -*-
"""shorts_a_cada_2h.py — Shorts do cap 1 no Manhwa Noturno, 1 a cada 2 h (dono, 16/10 15h: "um a cada 2h sendo o
primeiro agora").

Depois o dono mudou: "basta 2 hoje, os outros 3 posta amanhã durante o dia todo" -> AGENDA (16/10: 2, com 2 h
entre eles; 17/10: 3, a partir das 10h, 5 h entre eles = ~10h, ~15h, ~20h).

Roda pela tarefa agendada HipercoolShorts2h (a cada 20 min). Sobe 1 Short quando a agenda do dia ainda tem vaga e o
último vídeo do canal (qualquer projeto, pelo ledger do postador) é mais velho que o intervalo do dia — o tempo conta
dos uploads reais, mesmo que um atrase ou que o lancamento_pt poste no canal. Cada vez sobe NO MÁXIMO 1 Short pelo caminho normal
(postar_hipercool --no-completo --max-novos 1: análise do vídeo pronto, SEO, capa 9:16, descrição com o link do
completo, ledger). Os cortes são os 5 de "Área de trabalho\\Hipercool\\SHORTS NOVOS (ver como ficaram)", copiados
para workspace/shorts/the-inheritor-cap1 com meta_shorts.json apontando pro completo das 10:15 — o cortar_shorts
reaproveita e não corta de novo.

- Espera até ESPERA_MAX outro upload do hipercool terminar (o Chrome do postador é um só); senão, próxima rodada.
- Terminou os 5: grava pt_shorts_ok no estado da fila e desliga a própria tarefa.

  python bin/shorts_a_cada_2h.py          (uma rodada; log em logs/shorts_2h.log)
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fila  # noqa: E402  (importa o sem_janela: filhos sem janela na tela)

TAREFA = "HipercoolShorts2h"
CHAVE = "<SEGREDO_REMOVIDO>"
VIDEO = "hipercool_the-inheritor-cap-tulo-1_20261016_1015_NORMAL_CENSURADO_ULTIMO.mp4"
LOG = fila.PROJECT / "logs" / "shorts_2h.log"
ESTADO_POSTAGEM = fila.PROJECT / "workspace" / "postagens" / f"{Path(VIDEO).stem}__ManhwaNoturno.json"
ESPERA_MAX = timedelta(minutes=15)
# dono, 16/10 15h: "basta 2 hoje, os outros 3 posta amanhã durante o dia todo".
# dia: (Shorts no máximo naquele dia, não antes desta hora, tempo mínimo desde o último vídeo do canal)
AGENDA = {"2026-10-16": (2, 0, timedelta(minutes=115)),
          "2026-10-17": (2, 10, timedelta(hours=5))}  # ~10h e ~15h: partes 3 e 4 (a 5 ficou em PULAR)
AGENDA_PADRAO = (3, 10, timedelta(hours=5))
# 17/10 07h: a análise passou a achar nudez nos painéis 10, 68/69 e 102-105 do cap 1 (corrigir_pendentes). A
# parte 5 (295-434 s) tem 68/69 e 102-105: NÃO sobe — fica pro dono. Partes 3 e 4 estão limpas.
# (A parte 1, já no ar desde 16/10, tem o painel 10: avisado ao dono.)
PULAR = {"part_05"}
META_SHORTS = fila.PROJECT / "workspace" / "shorts" / "the-inheritor-cap1" / "meta_shorts.json"
FALHAS = ("cota", "limite", "suspenso", "parado", "morto", "reservado", "timeout", "erro", "nao_aprovado")


def diz(msg, telegram=False):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(linha + "\n")
    if telegram:
        fila.avisar(f"Shorts Manhwa Noturno: {msg}")


def desligar_tarefa():
    subprocess.run(["schtasks", "/Change", "/TN", TAREFA, "/DISABLE"], capture_output=True, text=True)


def _ultimo_upload():
    """Último upload no canal pt (qualquer projeto, pelo ledger do postador), com fuso; None se nunca."""
    politica = fila._politica()
    canal, _err = politica.achar_canal(fila.cfg().get("canal_pt", ""))
    if not canal:
        return None
    ups = fila._uploads_canal(canal["id"])
    return ups[-1] if ups else None


def _shorts_hoje():
    """Shorts deste capítulo que subiram hoje no Manhwa Noturno (estado do postar_hipercool)."""
    if not ESTADO_POSTAGEM.exists():
        return 0
    est = json.loads(ESTADO_POSTAGEM.read_text(encoding="utf-8"))
    hoje = datetime.now().date().isoformat()
    return sum(1 for k, v in est.items()
               if k.startswith("part_") and (v or {}).get("status") == "ok" and (v.get("em") or "")[:10] == hoje)


def _outros_uploads():
    """Alguém usando o Chrome do postador agora? Só o upload e o Studio contam: o postar_hipercool passa ~30 min
    na análise do vídeo pronto (16:9 das línguas) sem tocar no Chrome."""
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "@(Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Where-Object "
                        "{ $_.CommandLine -match 'youtube_web_poster\\.py|youtube_studio_extras\\.py' }).Count"],
                       capture_output=True, text=True)
    return (r.stdout or "0").strip() not in ("", "0")


def main():
    e = fila.ler_estado().get(CHAVE, {})
    if e.get("pt_shorts_ok"):
        diz("os Shorts do cap 1 já estão todos no ar; desligando a tarefa")
        desligar_tarefa()
        return
    # Os Shorts foram cortados do completo QUE ESTÁ NO AR (VIDEO). O estado da fila pode apontar pra um re-render
    # (17/10: corrigir_pendentes refez o cap 1 pra cobrir painéis), e isso não muda os cortes já feitos.
    video = next(fila.VIDEOS.rglob(VIDEO), None)
    if not video:
        diz(f"o completo {VIDEO} sumiu; nada postado — conferir antes")
        return
    feitos = json.loads(ESTADO_POSTAGEM.read_text(encoding="utf-8")) if ESTADO_POSTAGEM.exists() else {}
    pendentes = [k for k in sorted(json.loads(META_SHORTS.read_text(encoding="utf-8")))
                 if k.startswith("part_") and (feitos.get(k) or {}).get("status") != "ok"]
    if not pendentes or pendentes[0] in PULAR:
        diz(f"próximo Short seria {pendentes[0] if pendentes else '-'}, que está em PULAR (painel que a análise "
            "marcou como nudez); parando aqui e desligando a tarefa — o dono decide", telegram=True)
        desligar_tarefa()
        return

    agora = datetime.now()
    maximo, hora_ini, intervalo = AGENDA.get(agora.date().isoformat(), AGENDA_PADRAO)
    if _shorts_hoje() >= maximo or agora.hour < hora_ini:
        return  # cota do dia da agenda cheia ou cedo demais (rodada de 20 min: sem linha no log)
    ultimo = _ultimo_upload()
    if ultimo and datetime.now(ultimo.tzinfo) - ultimo < intervalo:
        return  # ainda não deu o intervalo desde o último vídeo do canal

    limite = datetime.now() + ESPERA_MAX
    while _outros_uploads():
        if datetime.now() > limite:
            diz("outro upload do hipercool está usando o Chrome; fica pra próxima rodada (20 min)")
            return
        time.sleep(30)

    resumo, saida = fila._postar(video, ["--no-completo", "--max-novos", "1"])
    if not resumo:
        diz(f"postar_hipercool sem RESUMO: {saida[-300:]}", telegram=True)
        return
    postou = [p for p in resumo.split(", ") if p.endswith("=ok")]
    urls = [ln.split("ok — ", 1)[1].strip() for ln in saida.splitlines() if ": ok — " in ln]
    if postou:
        diz(f"{postou[0].split('=')[0]} no ar {urls[-1] if urls else ''} ({resumo})", telegram=True)
    else:
        diz(f"nada subiu nesta rodada ({resumo})", telegram="=ja" not in resumo)
    if "faltam=" not in resumo and not any(f"={s}" in resumo for s in FALHAS):
        est = fila.ler_estado()
        est.setdefault(CHAVE, {})["pt_shorts_ok"] = datetime.now().isoformat(timespec="seconds")
        fila.gravar_estado(est)
        diz("os 5 Shorts do cap 1 estão no ar; tarefa desligada", telegram=True)
        desligar_tarefa()


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:  # noqa: BLE001
        diz(f"erro: {str(ex)[:300]}", telegram=True)
