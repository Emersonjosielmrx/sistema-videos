#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar-whatsapp.py — confere, ANTES de ligar, quais números da lista têm WhatsApp.

Por quê: na campanha espaçada (48/dia) cada número sem WhatsApp gasta uma vaga do dia e
~11 min de linha — o pré-filtro automático do Hermes só roda no modo imediato. Nos dados
de 14-15/10, 11% da lista não tinha WhatsApp.

O que faz: lê pronto-hermes.csv (telefone,nome), pergunta ao Hermes em lotes de 50 com
pausa de 10 s (POST /api/sessions/{sid}/contacts/check-batch) e grava:
  - pronto-hermes-validado.csv  (telefone,nome) só quem TEM WhatsApp -> é o que entra na campanha
  - sem-whatsapp.csv            (telefone,nome) quem não tem -> não discar (e vale pra lista de bloqueio)

Uso (de dentro da VPS, ou por túnel SSH — a porta 8080 não é pública):
  export HERMES_API_KEY=...        (Linux)   /   set HERMES_API_KEY=...   (Windows)
  python validar-whatsapp.py --sid 8653 --entrada saida/pronto-hermes.csv --saida saida/pronto-hermes-validado.csv

A chave vem SÓ da variável de ambiente HERMES_API_KEY (nunca de arquivo nem de argumento).
Só biblioteca padrão do Python. O progresso mostra os telefones mascarados.

Limite: no máximo ~300 números por dia (--max, padrão 300), com as pausas, pra consulta
não dar cara de robô. Rode de novo no dia seguinte: o script pula quem já está nos
arquivos de saída e continua de onde parou.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

LOTE = 50       # números por chamada à API (a rota aceita até 100)
PAUSA_S = 10    # segundos entre um lote e outro
MAX_DIA = 300   # teto sugerido por dia


def mascarar(tel):
    """Só os 4 últimos dígitos aparecem nas mensagens."""
    d = "".join(ch for ch in tel if ch.isdigit())
    if not d:
        return "?"
    return "*" * max(len(d) - 4, 0) + d[-4:]


def ler_entrada(caminho):
    """Lê telefone,nome (com ou sem cabeçalho). Devolve [(telefone, nome)] sem repetidos."""
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        linhas = [l for l in csv.reader(f) if l]
    if not linhas:
        return []
    cab = [c.strip().lower() for c in linhas[0]]
    tem_cab = "telefone" in cab or "nome" in cab
    itel = cab.index("telefone") if "telefone" in cab else 0
    inome = cab.index("nome") if "nome" in cab else (1 if len(cab) > 1 else None)
    vistos, out = set(), []
    for l in (linhas[1:] if tem_cab else linhas):
        tel = l[itel].strip() if itel < len(l) else ""
        if not tel or tel in vistos:
            continue
        vistos.add(tel)
        nome = l[inome].strip() if inome is not None and inome < len(l) else ""
        out.append((tel, nome))
    return out


def ja_feitos(*arquivos):
    """Telefones que já estão nos arquivos de saída (pra continuar de onde parou)."""
    s = set()
    for a in arquivos:
        if not os.path.exists(a):
            continue
        with open(a, encoding="utf-8-sig", newline="") as f:
            for i, l in enumerate(csv.reader(f)):
                if not l or not l[0].strip():
                    continue
                if i == 0 and l[0].strip().lower() == "telefone":
                    continue
                s.add(l[0].strip())
    return s


def abrir_saida(caminho):
    """Abre pra acrescentar; cabeçalho só quando o arquivo é novo."""
    novo = not os.path.exists(caminho) or os.path.getsize(caminho) == 0
    f = open(caminho, "a", encoding="utf-8-sig" if novo else "utf-8", newline="")
    w = csv.writer(f)
    if novo:
        w.writerow(["telefone", "nome"])
        f.flush()
    return f, w


def checar_lote(api, sid, chave, numeros):
    url = "%s/api/sessions/%s/contacts/check-batch" % (api.rstrip("/"), sid)
    req = urllib.request.Request(
        url, data=json.dumps({"numbers": numeros}).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": chave})
    with urllib.request.urlopen(req, timeout=120) as r:
        try:
            resp = json.load(r)
        except ValueError:
            raise RuntimeError("a resposta do Hermes não é JSON (endereço errado? túnel apontando para outro serviço?)")
    if not isinstance(resp, dict) or not isinstance(resp.get("alive"), list) or not isinstance(resp.get("dead"), list):
        raise RuntimeError("a resposta do Hermes veio num formato inesperado")
    return resp


def main():
    ap = argparse.ArgumentParser(description="Confere no WhatsApp a lista antes de ligar (via API do Hermes).")
    ap.add_argument("--api", default="http://127.0.0.1:8080", help="endereço do Hermes (padrão: http://127.0.0.1:8080)")
    ap.add_argument("--sid", required=True, help="id da sessão/linha no Hermes (ex.: 8653)")
    ap.add_argument("--entrada", default="pronto-hermes.csv", help="CSV telefone,nome (padrão: pronto-hermes.csv)")
    ap.add_argument("--saida", default="pronto-hermes-validado.csv", help="CSV só com quem tem WhatsApp")
    ap.add_argument("--max", type=int, default=MAX_DIA, help="máximo de números nesta rodada (padrão: %d)" % MAX_DIA)
    a = ap.parse_args()

    chave = os.environ.get("HERMES_API_KEY", "").strip()
    if not chave:
        print("erro: defina a variável de ambiente HERMES_API_KEY com a chave da API do Hermes "
              "(a chave nunca vai em arquivo nem em argumento).", file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(a.entrada):
        print("erro: não achei a entrada %s" % a.entrada, file=sys.stderr)
        sys.exit(2)

    sem_wa = os.path.join(os.path.dirname(a.saida) or ".", "sem-whatsapp.csv")
    lista = ler_entrada(a.entrada)
    feitos = ja_feitos(a.saida, sem_wa)
    pendentes = [(t, n) for t, n in lista if t not in feitos]
    hoje = pendentes[:max(a.max, 0)]
    print("lista: %d números | já conferidos antes: %d | a conferir agora: %d"
          % (len(lista), len(lista) - len(pendentes), len(hoje)))
    if len(pendentes) > len(hoje):
        print("aviso: ficam %d para outro dia (teto de %d por rodada, pra não dar cara de robô). "
              "Rode de novo amanhã: o script continua de onde parou." % (len(pendentes) - len(hoje), a.max))
    if not hoje:
        print("nada a conferir.")
        return

    f_ok, w_ok = abrir_saida(a.saida)
    f_nao, w_nao = abrir_saida(sem_wa)
    vivos = mortos = 0
    total_lotes = (len(hoje) + LOTE - 1) // LOTE
    try:
        for i in range(0, len(hoje), LOTE):
            if i:
                print("  pausa de %d s..." % PAUSA_S)
                time.sleep(PAUSA_S)
            lote = hoje[i:i + LOTE]
            try:
                resp = checar_lote(a.api, a.sid, chave, [t for t, _ in lote])
            except urllib.error.HTTPError as e:
                corpo = e.read()[:200].decode("utf-8", "replace")
                print("erro: o Hermes respondeu HTTP %d: %s" % (e.code, corpo), file=sys.stderr)
                if e.code in (401, 403):
                    print("  a chave HERMES_API_KEY não foi aceita.", file=sys.stderr)
                elif e.code == 404:
                    print("  sessão não encontrada: confira o --sid (e se a chave é da conta dona da linha).", file=sys.stderr)
                elif e.code == 502:
                    print("  a consulta ao WhatsApp falhou neste lote (nada foi gravado dele); espere um pouco e rode de novo.", file=sys.stderr)
                elif e.code == 503:
                    print("  a linha não está pareada/conectada no Hermes agora.", file=sys.stderr)
                break
            except RuntimeError as e:
                print("erro: %s" % e, file=sys.stderr)
                break
            except (urllib.error.URLError, OSError) as e:
                print("erro: não consegui falar com %s: %s" % (a.api, e), file=sys.stderr)
                print("  rode de dentro da VPS ou abra um túnel SSH (a porta 8080 não é pública).", file=sys.stderr)
                break
            vivos_lote = set(resp.get("alive") or [])
            mortos_lote = set(resp.get("dead") or [])
            faltando = [t for t, _ in lote if t not in vivos_lote and t not in mortos_lote]
            if faltando:
                # Só grava quem o Hermes disse que checou; número que não voltou fica para a próxima rodada.
                print("aviso: %d número(s) do lote não voltaram na resposta e NÃO foram gravados (rode de novo depois)."
                      % len(faltando), file=sys.stderr)
            sem_wa_lote = []
            for t, n in lote:
                if t in mortos_lote:
                    w_nao.writerow([t, n])
                    mortos += 1
                    sem_wa_lote.append(mascarar(t))
                elif t in vivos_lote:
                    w_ok.writerow([t, n])
                    vivos += 1
            f_ok.flush()
            f_nao.flush()
            print("lote %d/%d: %d números -> %d com WhatsApp, %d sem%s"
                  % (i // LOTE + 1, total_lotes, len(lote), len(lote) - len(sem_wa_lote), len(sem_wa_lote),
                     (" (" + ", ".join(sem_wa_lote[:5]) + (", ..." if len(sem_wa_lote) > 5 else "") + ")") if sem_wa_lote else ""))
    except KeyboardInterrupt:
        print("\ninterrompido: o que já foi conferido está salvo; rode de novo pra continuar.")
    finally:
        f_ok.close()
        f_nao.close()

    print("\nresumo: %d conferidos | %d com WhatsApp -> %s | %d sem WhatsApp -> %s"
          % (vivos + mortos, vivos, a.saida, mortos, sem_wa))
    if vivos + mortos:
        print("sem WhatsApp: %.0f%% da rodada (cada um desses teria gastado uma vaga do dia na campanha)."
              % (100.0 * mortos / (vivos + mortos)))


if __name__ == "__main__":
    main()
