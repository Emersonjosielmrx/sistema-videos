#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
captar_cnpj.py — monta a lista de empresas para a campanha a partir dos DADOS ABERTOS DO CNPJ
(Receita Federal; públicos por lei, publicados todo mês). Só biblioteca padrão do Python.

Fonte: compartilhamento público da Receita
  https://arquivos.receitafederal.gov.br  →  Dados/Cadastros/CNPJ/<AAAA-MM>/
  Estabelecimentos0..9.zip (telefone, atividade, cidade), Empresas0..9.zip (razão social, porte,
  capital), Simples.zip (quem é MEI), Cnaes.zip e Municipios.zip (tabelas).

Três passos:
  1. baixar   python captar_cnpj.py baixar --mes 2026-09 --pasta dados
  2. extrair  python captar_cnpj.py extrair --pasta dados --saida base.csv.gz [--uf PA,AM]
              (lê os ~60 milhões de estabelecimentos e guarda só os dos ramos de segmentos.json,
               ATIVOS e com telefone; junta porte, capital e MEI; separa "barato" e "caro")
  3. fatiar   python captar_cnpj.py fatiar base.csv.gz --segmento imobiliarias --uf PA
                     --nivel barato --limite 300 --saida lista.csv
              (gera a lista no formato do processar_leads.py, que limpa, pontua e gera o
               pronto-hermes.csv)

Regras de proteção (LGPD), ligadas por padrão:
  - MEI fica de fora (o telefone costuma ser o pessoal do dono). --com-mei para incluir.
  - só empresa com situação ATIVA na Receita.
  - a coluna "individual" marca empresário individual, para a dona decidir.
"""
import argparse
import base64
import csv
import gzip
import io
import json
import os
import sys
import time
import urllib.request
import zipfile
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))          # para usar o normalizar_telefone da captação
from processar_leads import normalizar_telefone    # noqa: E402

COMPARTILHAMENTO = "https://arquivos.receitafederal.gov.br/public.php/webdav"
TOKEN_PUBLICO = "<SEGREDO_REMOVIDO>"   # é o próprio link público da Receita, não é senha
csv.field_size_limit(10_000_000)

PORTE = {"00": "nao informado", "01": "microempresa", "03": "pequeno porte", "05": "demais (medio/grande)"}

# ---------------------------------------------------------------------------------- baixar

def arquivos_do_mes():
    return (["Cnaes.zip", "Municipios.zip", "Simples.zip"]
            + [f"Empresas{i}.zip" for i in range(10)]
            + [f"Estabelecimentos{i}.zip" for i in range(10)])

PEDACO = 150 * 1024 * 1024   # a Receita limita a velocidade POR CONEXÃO: arquivo grande vai em pedaços paralelos

def _auth():
    return "Basic " + base64.b64encode(f"{TOKEN_PUBLICO}:".encode()).decode()

def _baixar_pedaco(url, parte, ini, fim):
    """Baixa bytes [ini, fim] para o arquivo 'parte', continuando de onde parou."""
    esperado = fim - ini + 1
    for tentativa in range(6):
        ja = os.path.getsize(parte) if os.path.exists(parte) else 0
        if ja >= esperado:
            return
        req = urllib.request.Request(url, headers={"Authorization": _auth(), "Range": f"bytes={ini + ja}-{fim}"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(parte, "ab") as f:
                while True:
                    bloco = r.read(1 << 20)
                    if not bloco:
                        break
                    f.write(bloco)
        except Exception as e:  # rede caiu: tenta de novo do ponto em que parou
            print(f"    (pedaço {os.path.basename(parte)}: {e}; tentando de novo)", flush=True)
            time.sleep(5 * (tentativa + 1))
    if os.path.getsize(parte) < esperado:
        raise RuntimeError(f"{parte} incompleto")

def baixar(mes, pasta, conexoes=8):
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(pasta, exist_ok=True)
    planos = []   # (nome, destino, total, [(url, parte, ini, fim)])
    for nome in arquivos_do_mes():
        url = f"{COMPARTILHAMENTO}/Dados/Cadastros/CNPJ/{mes}/{nome}"
        destino = os.path.join(pasta, nome)
        req = urllib.request.Request(url, method="HEAD", headers={"Authorization": _auth()})
        with urllib.request.urlopen(req, timeout=60) as r:
            total = int(r.headers.get("Content-Length", 0))
        if os.path.exists(destino) and os.path.getsize(destino) == total:
            print(f"  ok (já baixado) {nome} {total/1e6:.0f} MB"); continue
        partes = [(url, f"{destino}.parte{k:03d}", ini, min(ini + PEDACO, total) - 1)
                  for k, ini in enumerate(range(0, total, PEDACO))]
        planos.append((nome, destino, total, partes))
    tarefas = [p for _, _, _, partes in planos for p in partes]
    total_geral = sum(t for _, _, t, _ in planos)
    print(f"  baixando {len(planos)} arquivo(s), {total_geral/1e9:.2f} GB, em {len(tarefas)} pedaços, {conexoes} conexões...", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=conexoes) as pool:
        for fut in [pool.submit(_baixar_pedaco, *t) for t in tarefas]:
            fut.result()
    # junta os pedaços de cada arquivo
    for nome, destino, total, partes in planos:
        with open(destino + ".novo", "wb") as f:
            for _, parte, _, _ in partes:
                with open(parte, "rb") as p:
                    while True:
                        b = p.read(8 << 20)
                        if not b:
                            break
                        f.write(b)
        if os.path.getsize(destino + ".novo") != total:
            sys.exit(f"PAROU: {nome} ficou com tamanho errado. Rode de novo.")
        os.replace(destino + ".novo", destino)
        for _, parte, _, _ in partes:
            os.remove(parte)
        print(f"  pronto {nome} {total/1e6:.0f} MB")
    print(f"  tudo baixado em {(time.time()-t0)/60:.0f} min")

# --------------------------------------------------------------------------------- leitura

def linhas_zip(caminho):
    """Lê o CSV de dentro do zip da Receita (latin-1, ';', aspas), linha a linha."""
    with zipfile.ZipFile(caminho) as z:
        membro = z.namelist()[0]
        with z.open(membro) as bruto:
            texto = io.TextIOWrapper(bruto, encoding="latin-1", newline="")
            for linha in csv.reader(texto, delimiter=";", quotechar='"'):
                yield linha

def tabela(caminho):
    return {l[0]: l[1] for l in linhas_zip(caminho) if len(l) >= 2}

def carregar_segmentos(caminho, cnaes_oficiais):
    segs = json.load(open(caminho, encoding="utf-8"))
    cnae2seg = {}
    for nome, s in segs.items():
        if nome.startswith("_"):
            continue
        for c in s["cnaes"]:
            if cnaes_oficiais and c not in cnaes_oficiais:
                print(f"  AVISO: CNAE {c} ({nome}) não existe na tabela da Receita — confira segmentos.json")
            cnae2seg[c] = (nome, s["nivel"])
    return segs, cnae2seg

def melhor_telefone(linha):
    """Dos dois telefones do estabelecimento, prefere celular. Devolve (tel, tipo, tel2)."""
    achados = []
    for i_ddd, i_tel in ((21, 22), (23, 24)):
        ddd, tel = linha[i_ddd].strip(), linha[i_tel].strip()
        if tel:
            e164, tipo = normalizar_telefone(ddd + tel)
            if e164 and e164 not in [a[0] for a in achados]:
                achados.append((e164, tipo))
    if not achados:
        return None, None, ""
    achados.sort(key=lambda a: a[1] != "celular")
    return achados[0][0], achados[0][1], (achados[1][0] if len(achados) > 1 else "")

# --------------------------------------------------------------------------------- extrair

CAMPOS_BASE = ["cnpj", "nome", "razao_social", "segmento", "nivel", "motivo_nivel", "cnae", "atividade",
               "uf", "cidade", "bairro", "telefone", "tipo_telefone", "telefone2", "email",
               "porte", "capital_social", "estabelecimentos", "individual", "simples", "inicio_atividade"]

def extrair(pasta, saida, ufs, com_mei, segmentos_json):
    p = lambda n: os.path.join(pasta, n)
    cnaes = tabela(p("Cnaes.zip")) if os.path.exists(p("Cnaes.zip")) else {}
    municipios = tabela(p("Municipios.zip")) if os.path.exists(p("Municipios.zip")) else {}
    segs, cnae2seg = carregar_segmentos(segmentos_json, cnaes)
    print(f"ramos: {len([s for s in segs if not s.startswith('_')])} | atividades (CNAE): {len(cnae2seg)} | UF: {','.join(sorted(ufs)) or 'todas'}")

    # 1) estabelecimentos: filtra ramo + ativo + telefone; conta estabelecimentos por empresa
    tmp = saida + ".parcial.csv"
    estab_por_empresa = Counter()
    candidatos = set()
    lidos = guardados = 0
    t0 = time.time()
    with open(tmp, "w", encoding="utf-8", newline="") as ft:
        wt = csv.writer(ft)
        for i in range(10):
            arq = p(f"Estabelecimentos{i}.zip")
            if not os.path.exists(arq):
                print(f"  aviso: falta {arq}"); continue
            for l in linhas_zip(arq):
                lidos += 1
                if lidos % 5_000_000 == 0:
                    print(f"  {lidos/1e6:.0f} milhões lidos, {guardados} guardados ({time.time()-t0:.0f} s)", flush=True)
                if len(l) < 28 or l[11] not in cnae2seg:
                    continue
                if l[5].strip().lstrip("0") != "2":          # 02 = ATIVA
                    continue
                basico = l[0]
                estab_por_empresa[basico] += 1
                if ufs and l[19] not in ufs:
                    continue
                tel, tipo, tel2 = melhor_telefone(l)
                if not tel:
                    continue
                cnpj = f"{l[0]}{l[1]}{l[2]}"
                wt.writerow([cnpj, basico, l[4].strip(), l[11], l[19], municipios.get(l[20], l[20]),
                             l[17].strip(), tel, tipo, tel2, l[27].strip().lower(), l[10]])
                candidatos.add(basico)
                guardados += 1
    print(f"estabelecimentos: {lidos} lidos, {guardados} do ramo, ativos e com telefone ({time.time()-t0:.0f} s)")

    # 2) empresas: razão social, natureza, capital, porte (só das candidatas)
    empresa = {}
    for i in range(10):
        arq = p(f"Empresas{i}.zip")
        if not os.path.exists(arq):
            continue
        for l in linhas_zip(arq):
            if len(l) >= 6 and l[0] in candidatos:
                try:
                    capital = float(l[4].replace(".", "").replace(",", "."))
                except ValueError:
                    capital = 0.0
                empresa[l[0]] = (l[1].strip(), l[2], capital, l[5])
    print(f"empresas encontradas: {len(empresa)}")

    # 3) simples: quem é MEI
    simples = {}
    if os.path.exists(p("Simples.zip")):
        for l in linhas_zip(p("Simples.zip")):
            if len(l) >= 5 and l[0] in candidatos:
                simples[l[0]] = (l[1], l[4])
    print(f"situação no Simples encontrada: {len(simples)}")

    # 4) junta e classifica
    contagem = Counter()
    with open(tmp, encoding="utf-8", newline="") as ft, gzip.open(saida, "wt", encoding="utf-8", newline="") as fs:
        w = csv.writer(fs)
        w.writerow(CAMPOS_BASE)
        for cnpj, basico, fantasia, cnae, uf, cidade, bairro, tel, tipo, tel2, email, inicio in csv.reader(ft):
            razao, natureza, capital, porte = empresa.get(basico, ("", "", 0.0, "00"))
            op_simples, op_mei = simples.get(basico, ("", ""))
            if op_mei == "S" and not com_mei:
                contagem["fora: MEI"] += 1; continue
            ramo, nivel_ramo = cnae2seg[cnae]
            n_estab = estab_por_empresa[basico]
            motivos = []
            if porte == "05": motivos.append("porte médio/grande")
            if capital >= 500_000: motivos.append(f"capital R$ {capital:,.0f}".replace(",", "."))
            if n_estab >= 3: motivos.append(f"{n_estab} estabelecimentos")
            if nivel_ramo == "caro" and porte in ("03", "05"): motivos.append("ramo de volume")
            nivel = "caro" if motivos else "barato"
            if nivel == "barato":
                motivos.append("pequena empresa" if porte in ("01", "03") else "porte não informado")
            individual = "sim" if natureza == "2135" else ""
            w.writerow([cnpj, fantasia or razao, razao, ramo, nivel, "; ".join(motivos), cnae, cnaes.get(cnae, ""),
                        uf, cidade, bairro, tel, tipo, tel2, email,
                        PORTE.get(porte, porte), f"{capital:.0f}", n_estab, individual,
                        {"S": "sim", "N": "nao"}.get(op_simples, ""), inicio])
            contagem[f"{nivel}"] += 1
            contagem[f"ramo {ramo}"] += 1
    os.remove(tmp)
    print("\nRESULTADO:", saida)
    for k, v in sorted(contagem.items()):
        print(f"  {v:>8}  {k}")

# ---------------------------------------------------------------------------------- fatiar

def fatiar(base, segmentos, ufs, cidades, nivel, so_celular, limite, saida, sem_individual):
    escolhidos = []
    with gzip.open(base, "rt", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if segmentos and r["segmento"] not in segmentos: continue
            if ufs and r["uf"] not in ufs: continue
            if cidades and r["cidade"].upper() not in cidades: continue
            if nivel and r["nivel"] != nivel: continue
            if so_celular and r["tipo_telefone"] != "celular": continue
            if sem_individual and r["individual"] == "sim": continue
            escolhidos.append(r)
    # celular primeiro; depois quem tem e-mail; depois maior capital
    escolhidos.sort(key=lambda r: (r["tipo_telefone"] != "celular", not r["email"], -float(r["capital_social"] or 0)))
    if limite:
        escolhidos = escolhidos[:limite]
    with open(saida, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        # colunas que o processar_leads.py reconhece sozinho
        w.writerow(["Empresa", "Telefone", "Cidade", "UF", "E-mail", "Ramo", "Porte", "Observação", "CNPJ", "Nivel"])
        for r in escolhidos:
            obs = f"{r['atividade']}; {r['motivo_nivel']}"
            w.writerow([r["nome"], r["telefone"], r["cidade"], r["uf"], r["email"], r["segmento"],
                        r["porte"], obs, r["cnpj"], r["nivel"]])
    cel = sum(1 for r in escolhidos if r["tipo_telefone"] == "celular")
    print(f"{len(escolhidos)} empresas em {saida} ({cel} com celular). Próximo passo:")
    print(f"  python ../processar_leads.py {saida} --segmento <ramo> --so-celular --saida saida")

# ------------------------------------------------------------------------------------ main

def lista(s, upper=False):
    v = [x.strip() for x in (s or "").split(",") if x.strip()]
    return set(x.upper() for x in v) if upper else set(v)

def main():
    ap = argparse.ArgumentParser(description="Captação de empresas pelos dados abertos do CNPJ.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baixar"); b.add_argument("--mes", required=True); b.add_argument("--pasta", default="dados")
    b.add_argument("--conexoes", type=int, default=8)
    e = sub.add_parser("extrair"); e.add_argument("--pasta", default="dados"); e.add_argument("--saida", default="base.csv.gz")
    e.add_argument("--uf", default=""); e.add_argument("--com-mei", action="store_true")
    e.add_argument("--segmentos", default=os.path.join(AQUI, "segmentos.json"))
    f = sub.add_parser("fatiar"); f.add_argument("base"); f.add_argument("--segmento", default="")
    f.add_argument("--uf", default=""); f.add_argument("--cidade", default=""); f.add_argument("--nivel", choices=["barato", "caro", ""], default="")
    f.add_argument("--so-celular", action="store_true"); f.add_argument("--sem-individual", action="store_true")
    f.add_argument("--limite", type=int, default=0); f.add_argument("--saida", default="lista.csv")
    a = ap.parse_args()
    if a.cmd == "baixar":
        baixar(a.mes, a.pasta, a.conexoes)
    elif a.cmd == "extrair":
        extrair(a.pasta, a.saida, lista(a.uf, True), a.com_mei, a.segmentos)
    else:
        fatiar(a.base, lista(a.segmento), lista(a.uf, True), lista(a.cidade, True), a.nivel,
               a.so_celular, a.limite, a.saida, a.sem_individual)

if __name__ == "__main__":
    main()
