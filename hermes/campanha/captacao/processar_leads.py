#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
processar_leads.py — captação do Hermes Call: transforma uma lista BRUTA de empresas numa
lista LIMPA e pronta para o Hermes discar.

O que faz (sem internet, sem raspar nada; só lê os arquivos que você já tem):
  1. lê um ou mais CSV de leads, em qualquer formato de colunas (descobre sozinho qual é
     telefone, nome, cidade, site, segmento…);
  2. arruma o telefone para o padrão do WhatsApp (+55 DDD 9XXXXXXXX), separando fixo de celular;
  3. tira repetidos (mesmo telefone) e junta o que cada linha trazia de informação;
  4. tira quem está na lista de BLOQUEIO (quem pediu pra não ligar, ou já foi contatado);
  5. dá uma nota A/B/C a cada empresa pelos sinais que aparecem nos dados (segmento-alvo,
     tem site, porte, já usa automação…), e explica o porquê;
  6. gera dois arquivos:
       - pronto-hermes.csv  (telefone,nome) — é o que entra no Hermes (coluna "numbers"/"names");
       - leads-completo.csv (tudo + nota + segmento + motivo) — é o que vira o CRM.
  e um resumo na tela.

Uso:
  python processar_leads.py entrada1.csv [entrada2.csv ...] [--saida PASTA]
                            [--segmento imobiliaria] [--bloqueio bloqueio.csv]
                            [--so-celular] [--so-nota AB]

Nada é enviado a lugar nenhum. Nenhum número é discado aqui — isto só PREPARA a lista.
"""
import csv
import sys
import os
import re
import argparse
import unicodedata
from collections import defaultdict, Counter

# ----------------------------------------------------------------------------- utilidades

def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))

def chave_coluna(nome):
    return re.sub(r"[^a-z0-9]", "", sem_acento(str(nome)).lower())

# Nomes de coluna que cada campo aceita (procura por "contém", então "telefone 1",
# "fone_celular", "WhatsApp" etc. caem todos em telefone).
COLUNAS = {
    "telefone": ["telefone", "fone", "celular", "whatsapp", "whats", "tel", "contato", "mobile", "phone"],
    "nome":     ["nome", "empresa", "razaosocial", "fantasia", "razao", "cliente", "estabelecimento", "name", "company"],
    "cidade":   ["cidade", "municipio", "city", "localidade"],
    "uf":       ["uf", "estado", "state"],
    "site":     ["site", "website", "url", "pagina", "web"],
    "email":    ["email", "mail", "email"],
    "segmento": ["segmento", "ramo", "categoria", "nicho", "setor", "atividade", "tipo"],
    "obs":      ["obs", "observacao", "nota", "descricao", "detalhe", "sobre"],
    "porte":    ["porte", "tamanho", "funcionarios", "colaboradores", "size", "employees"],
    "nivel":    ["nivel", "nível"],
}

def mapear_colunas(cabecalho):
    """Descobre qual coluna do arquivo é cada campo. Devolve {campo: indice}."""
    chaves = [chave_coluna(c) for c in cabecalho]
    mapa = {}
    for campo, aliases in COLUNAS.items():
        for i, k in enumerate(chaves):
            if i in mapa.values():
                continue
            if any(a in k for a in aliases):
                mapa[campo] = i
                break
    return mapa

# ------------------------------------------------------------------------- telefone (Brasil)

DDDS_VALIDOS = {
    11,12,13,14,15,16,17,18,19, 21,22,24,27,28, 31,32,33,34,35,37,38,
    41,42,43,44,45,46,47,48,49, 51,53,54,55, 61,62,63,64,65,66,67,68,69,
    71,73,74,75,77,79, 81,82,83,84,85,86,87,88,89, 91,92,93,94,95,96,97,98,99,
}

def normalizar_telefone(bruto):
    """
    Devolve (e164, tipo) ou (None, motivo).
      e164: '+5591988887777'    tipo: 'celular' | 'fixo'
    Regras do Brasil: celular tem 9 dígitos começando em 9; fixo tem 8.
    Acrescenta o 9 em celular antigo (8 dígitos começando em 6-9) quando faltar.
    """
    if not bruto:
        return None, "vazio"
    d = re.sub(r"\D", "", str(bruto))
    # tira 55 do começo (DDI) e 0 de operadora
    if d.startswith("55") and len(d) >= 12:
        d = d[2:]
    d = d.lstrip("0")
    if len(d) < 10:
        return None, "curto"
    if len(d) > 11:
        # pode ter vindo colado com outra coisa; pega os 11 últimos
        d = d[-11:]
    ddd = int(d[:2])
    if ddd not in DDDS_VALIDOS:
        return None, "ddd invalido"
    resto = d[2:]
    if len(resto) == 9:
        if resto[0] != "9":
            return None, "9 digitos sem comecar em 9"
        return f"+55{ddd}{resto}", "celular"
    if len(resto) == 8:
        if resto[0] in "9876":   # era celular antigo sem o 9
            return f"+55{ddd}9{resto}", "celular"
        return f"+55{ddd}{resto}", "fixo"  # fixo (2-5)
    return None, "tamanho estranho"

# -------------------------------------------------------------------------------- pontuação

# Sinais que puxam a nota pra cima. Procurados no texto de nome+segmento+obs+site (sem acento).
SINAIS_AUTOMACAO = ["automa", "n8n", "zapier", "make", "rpa", "chatbot", "bot ", "crm",
                    "rd station", "hubspot", "pipedrive", "integra"]
SINAIS_VOLUME = ["ecommerce", "e-commerce", "loja online", "televendas", "call center",
                "cobranca", "sdr", "equipe de venda", "franquia", "filiais", "filial", "estabeleciment"]
SINAIS_PORTE_ALTO = ["ltda", "s.a", "s/a", " sa ", "grupo", "matriz", "ramo de volume"]

def pontuar(lead, segmento_alvo):
    """Devolve (nota 'A'/'B'/'C', pontos int, motivos list).

    A nota separa leads DENTRO de um mesmo ramo, então o que pesa é o que diferencia uma
    empresa da outra (site, e-mail, porte, capital, filiais, automação) — não o nome (quase
    todas têm) nem o ramo (quando a lista já vem de um ramo só, é igual para todas).
    """
    texto = sem_acento(" ".join([
        lead.get("nome",""), lead.get("segmento",""), lead.get("obs",""), lead.get("site","")
    ]).lower())
    pts = 0
    motivos = []

    if lead.get("tipo") == "celular":
        pts += 2; motivos.append("tem celular/WhatsApp")
    else:
        motivos.append("só telefone fixo (WhatsApp improvável)")

    if segmento_alvo and segmento_alvo in sem_acento(lead.get("segmento","").lower()):
        pts += 1; motivos.append(f"segmento-alvo ({segmento_alvo})")

    if lead.get("site"):
        pts += 2; motivos.append("tem site")
    if lead.get("email"):
        pts += 1; motivos.append("tem e-mail")

    if any(s in texto for s in SINAIS_AUTOMACAO):
        pts += 3; motivos.append("já menciona automação/CRM")
    if any(s in texto for s in SINAIS_VOLUME):
        pts += 2; motivos.append("sinal de volume/filiais")
    if sem_acento(lead.get("nivel","").lower()) == "caro":
        pts += 2; motivos.append("perfil de volume (plano maior)")
    if any(s in texto for s in SINAIS_PORTE_ALTO) or _porte_grande(lead.get("porte","")):
        pts += 2; motivos.append("sinal de porte")
    cap = _capital(lead.get("obs",""))
    if cap >= 500_000:
        pts += 2; motivos.append(f"capital alto")
    elif cap >= 100_000:
        pts += 1

    nota = "A" if pts >= 7 else "B" if pts >= 4 else "C"
    # O Hermes liga por WhatsApp. Fixo quase nunca tem WhatsApp e o pré-filtro do Hermes
    # pula quem não tem — então fixo nunca é "ligar primeiro" (nota A), por mais pontos que faça.
    if lead.get("tipo") != "celular" and nota == "A":
        nota = "B"
        motivos.append("rebaixado p/ B: é fixo (o Hermes liga por WhatsApp)")
    return nota, pts, motivos

def _porte_grande(valor):
    v = sem_acento(str(valor).lower())
    if "medio" in v or "grande" in v or "demais" in v:
        return True
    m = re.search(r"\d+", v)
    return bool(m) and int(m.group()) >= 10

def _capital(obs):
    """Lê 'capital R$ 1.000.000' do texto de observação (vem do CNPJ). 0 se não achar."""
    m = re.search(r"capital[^\d]*([\d.]+)", sem_acento(str(obs).lower()))
    if not m:
        return 0.0
    try:
        return float(m.group(1).replace(".", ""))
    except ValueError:
        return 0.0

# ----------------------------------------------------------------------------------- núcleo

def ler_csv(caminho):
    """Lê um CSV tolerando ; ou , e acentos (utf-8 ou latin-1)."""
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(caminho, encoding=enc, newline="") as f:
                amostra = f.read(4096); f.seek(0)
                sep = ";" if amostra.count(";") > amostra.count(",") else ","
                linhas = list(csv.reader(f, delimiter=sep))
            if linhas:
                return linhas
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    return []

def carregar_bloqueio(caminho):
    """Lê uma lista de telefones a NUNCA discar (opt-out, já contatado). Qualquer formato."""
    bloqueados = set()
    if not caminho or not os.path.exists(caminho):
        return bloqueados
    for linha in ler_csv(caminho):
        for celula in linha:
            e164, _ = normalizar_telefone(celula)
            if e164:
                bloqueados.add(e164)
    return bloqueados

def processar(arquivos, segmento_alvo, bloqueio, so_celular, so_nota):
    por_telefone = {}       # e164 -> lead juntado
    descartes = Counter()
    total_linhas = 0

    for arq in arquivos:
        linhas = ler_csv(arq)
        if not linhas:
            print(f"  aviso: {arq} vazio ou ilegível", file=sys.stderr); continue
        mapa = mapear_colunas(linhas[0])
        if "telefone" not in mapa:
            print(f"  aviso: {arq} — não achei coluna de telefone (cabeçalho: {linhas[0]})", file=sys.stderr)
            continue
        for linha in linhas[1:]:
            total_linhas += 1
            def val(campo):
                i = mapa.get(campo)
                return (linha[i].strip() if i is not None and i < len(linha) else "")
            e164, tipo = normalizar_telefone(val("telefone"))
            if not e164:
                descartes[f"telefone {tipo}"] += 1; continue
            if e164 in bloqueio:
                descartes["na lista de bloqueio"] += 1; continue
            lead = {
                "telefone": e164, "tipo": tipo,
                "nome": val("nome"), "cidade": val("cidade"), "uf": val("uf"),
                "site": val("site"), "email": val("email"),
                "segmento": val("segmento") or segmento_alvo or "", "obs": val("obs"),
                "porte": val("porte"), "nivel": val("nivel"), "origem": os.path.basename(arq),
            }
            if e164 in por_telefone:
                # repetido: completa os campos vazios com o que a outra linha tinha
                antigo = por_telefone[e164]
                for k, v in lead.items():
                    if not antigo.get(k) and v:
                        antigo[k] = v
                descartes["repetido (juntado)"] += 1
            else:
                por_telefone[e164] = lead

    leads = list(por_telefone.values())
    for lead in leads:
        lead["nota"], lead["pontos"], motivos = pontuar(lead, sem_acento((segmento_alvo or "").lower()))
        lead["motivo"] = "; ".join(motivos)

    if so_celular:
        antes = len(leads); leads = [l for l in leads if l["tipo"] == "celular"]
        descartes["fixo (--so-celular)"] += antes - len(leads)
    if so_nota:
        notas = set(so_nota.upper()); antes = len(leads)
        leads = [l for l in leads if l["nota"] in notas]
        descartes[f"nota fora de {so_nota.upper()}"] += antes - len(leads)

    # ordem: A antes de B antes de C; dentro da nota, mais pontos primeiro
    leads.sort(key=lambda l: (l["nota"], -l["pontos"]))
    return leads, descartes, total_linhas

# ------------------------------------------------------------------------------------ saída

CAMPOS_COMPLETO = ["telefone","nome","nota","pontos","nivel","tipo","segmento","cidade","uf",
                   "site","email","porte","obs","origem","motivo"]

def gravar(leads, pasta):
    os.makedirs(pasta, exist_ok=True)
    pronto = os.path.join(pasta, "pronto-hermes.csv")
    completo = os.path.join(pasta, "leads-completo.csv")
    with open(pronto, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["telefone", "nome"])
        for l in leads:
            w.writerow([l["telefone"], l["nome"]])
    with open(completo, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_COMPLETO, extrasaction="ignore")
        w.writeheader()
        for l in leads:
            w.writerow(l)
    return pronto, completo

def resumo(leads, descartes, total_linhas, pronto, completo):
    print("\n" + "=" * 60)
    print(f"LINHAS LIDAS: {total_linhas}")
    print(f"LEADS PRONTOS: {len(leads)}")
    notas = Counter(l["nota"] for l in leads)
    print(f"  nota A (ligar primeiro): {notas['A']}")
    print(f"  nota B: {notas['B']}")
    print(f"  nota C (deixar por último): {notas['C']}")
    cel = sum(1 for l in leads if l["tipo"] == "celular")
    print(f"  com celular/WhatsApp: {cel}   só fixo: {len(leads)-cel}")
    if descartes:
        print("DESCARTES / AJUSTES:")
        for motivo, n in descartes.most_common():
            print(f"  {n:>6}  {motivo}")
    print("ARQUIVOS GERADOS:")
    print(f"  {pronto}   <- importe no Hermes (telefone + nome)")
    print(f"  {completo}   <- lista rica para o CRM")
    print("=" * 60)
    print("Confira a lista antes de discar. Só telefone comercial público; quem pedir, sai na hora.")

def main():
    ap = argparse.ArgumentParser(description="Captação do Hermes: limpa e pontua leads.")
    ap.add_argument("arquivos", nargs="+", help="CSV(s) de leads brutos")
    ap.add_argument("--saida", default="saida", help="pasta de saída (padrão: ./saida)")
    ap.add_argument("--segmento", default="", help="segmento-alvo (ex.: imobiliaria) — pontua mais quem bate")
    ap.add_argument("--bloqueio", default="", help="CSV de telefones a NUNCA discar (opt-out/já contatado)")
    ap.add_argument("--so-celular", action="store_true", help="descarta telefone fixo")
    ap.add_argument("--so-nota", default="", help="mantém só estas notas (ex.: AB)")
    args = ap.parse_args()

    bloqueio = carregar_bloqueio(args.bloqueio)
    if bloqueio:
        print(f"lista de bloqueio: {len(bloqueio)} número(s) que não serão discados")
    leads, descartes, total = processar(args.arquivos, args.segmento, bloqueio, args.so_celular, args.so_nota)
    if not leads:
        print("Nenhum lead válido. Confira se o CSV tem uma coluna de telefone.", file=sys.stderr)
        sys.exit(1)
    pronto, completo = gravar(leads, args.saida)
    resumo(leads, descartes, total, pronto, completo)

if __name__ == "__main__":
    main()
