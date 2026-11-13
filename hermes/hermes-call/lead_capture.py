#!/usr/bin/env python3
"""
Captação de Leads B2B via dados públicos abertos — Hermes Call v3.

ZERO API KEY. Usa fontes abertas pra montar listas de leads (nome, telefone, ramo)
por região e segmento, prontas pra virar campanha no Hermes.

FONTES:
- Overpass API (OpenStreetMap): negócios locais com telefone (lojas, clínicas,
  escritórios, instaladoras...) por área geográfica + categoria. Sem key, sem limite
  prático. É a fonte principal (tem telefone direto).
- BrasilAPI (CNPJ): enriquece um CNPJ com razão social, CNAE, endereço, telefone.
  Keyless. Usado pra complementar, não pra buscar em massa.

FLUXO:
  1) Busca negócios numa bbox (região) filtrando por tags OSM (shop/amenity/office).
  2) Extrai nome + telefone + categoria + endereço.
  3) Normaliza o telefone pro formato do WhatsApp (55DDDNUMERO).
  4) Deduplica e (opcional) cria uma lista no Hermes via /api/contact-lists.

USO:
  # 1) Descobrir a bbox de uma cidade (usa Nominatim, 1 req/s):
  python lead_capture.py --geocode "Goiânia, GO"

  # 2) Captar negócios de um segmento numa bbox:
  python lead_capture.py --bbox -16.75,-49.35,-16.60,-49.20 \
      --categories "shop=solar,office=energy_supplier,craft=electrician" \
      --out leads_solar_goiania.json

  # 3) Captar E já criar a lista no Hermes:
  python lead_capture.py --bbox ... --categories ... \
      --server https://hermescall.opus-sem-limites.com.br --token <JWT> \
      --list-name "Solar Goiânia (OSM)"

CATEGORIAS ÚTEIS (tags OSM):
  Energia solar / elétrica: shop=solar, office=energy_supplier, craft=electrician
  Comércio geral:           shop=* (com phone)
  Serviços:                 office=*, amenity=* (clinic, dentist...)
  Construção:               craft=*, shop=doityourself, shop=hardware
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request

# Espelhos da Overpass (o principal costuma estar ocupado; tenta em ordem).
OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
NOMINATIM = "https://nominatim.openstreetmap.org/search"
UA = "HermesLeadCapture/1.0 (contato via painel Hermes)"


def http_post_form(url, data, timeout=90):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def http_get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def geocode(place):
    """Descobre a bbox de uma cidade/lugar via Nominatim. Respeita 1 req/s."""
    q = urllib.parse.urlencode({"q": place, "format": "json", "limit": 1})
    time.sleep(1.1)  # cortesia com o Nominatim
    res = http_get_json(f"{NOMINATIM}?{q}")
    if not res:
        print(f"[geocode] nada encontrado pra {place!r}")
        return None
    bb = res[0]["boundingbox"]  # [south, north, west, east]
    # Overpass usa (south,west,north,east)
    south, north, west, east = float(bb[0]), float(bb[1]), float(bb[2]), float(bb[3])
    print(f"[geocode] {place} -> bbox {south},{west},{north},{east}")
    print(f"          nome: {res[0].get('display_name','')}")
    return (south, west, north, east)


def build_query(bbox, categories, limit):
    """Monta a query Overpass QL. categories: lista de 'key=value'."""
    south, west, north, east = bbox
    b = f"({south},{west},{north},{east})"
    parts = []
    for cat in categories:
        if "=" in cat:
            k, v = cat.split("=", 1)
            # só queremos os que têm telefone (senão não serve pra ligar)
            parts.append(f'node["{k}"="{v}"]["phone"]{b};')
            parts.append(f'node["{k}"="{v}"]["contact:phone"]{b};')
        else:
            parts.append(f'node["{cat}"]["phone"]{b};')
    q = f"[out:json][timeout:60];({''.join(parts)});out body {limit};"
    return q


def normalize_phone_br(raw):
    """Converte telefone OSM (+55 62 3333-4444, (62)99999-8888...) pra 55DDDNUMERO.

    Retorna None se não parecer um número BR discável (fixo ou celular).
    """
    if not raw:
        return None
    # pega só o primeiro número se vier vários separados por ; ou ,
    raw = re.split(r"[;,/]", raw)[0]
    digits = re.sub(r"\D", "", raw)
    # remove 55 do início pra padronizar e recolocar
    if digits.startswith("55") and len(digits) >= 12:
        digits = digits[2:]
    # agora digits deve ser DDD(2) + numero(8 ou 9)
    if len(digits) == 10 or len(digits) == 11:  # DDD + 8/9 dígitos
        return "55" + digits
    return None  # formato inesperado -> descarta


def overpass_query(query):
    """Tenta os espelhos da Overpass em ordem até um responder."""
    last = None
    for ep in OVERPASS_ENDPOINTS:
        try:
            txt = http_post_form(ep, {"data": query})
            if txt.lstrip().startswith("{"):
                return json.loads(txt)
            last = f"{ep}: resposta não-JSON (provável servidor ocupado)"
            print(f"[overpass] {last[:80]}")
        except Exception as e:
            last = f"{ep}: {e}"
            print(f"[overpass] falhou {last[:80]}")
        time.sleep(2)
    raise RuntimeError(f"Overpass indisponível em todos os espelhos. Último: {last}")


def capture(bbox, categories, limit):
    """Executa a busca e devolve leads normalizados + deduplicados."""
    q = build_query(bbox, categories, limit)
    print(f"[overpass] query:\n{q}\n")
    data = overpass_query(q)
    seen = set()
    leads = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        phone_raw = tags.get("phone") or tags.get("contact:phone")
        phone = normalize_phone_br(phone_raw)
        if not phone or phone in seen:
            continue
        seen.add(phone)
        # categoria: primeira tag conhecida
        cat = ""
        for k in ("shop", "amenity", "office", "craft"):
            if k in tags:
                cat = f"{k}={tags[k]}"
                break
        addr = " ".join(filter(None, [
            tags.get("addr:street", ""), tags.get("addr:housenumber", ""),
            tags.get("addr:city", ""),
        ]))
        leads.append({
            "name": tags.get("name", "(sem nome)"),
            "phone": phone,
            "phone_raw": phone_raw,
            "category": cat,
            "address": addr.strip(),
            "website": tags.get("website") or tags.get("contact:website", ""),
        })
    return leads


def create_list_in_hermes(server, token, list_name, phones):
    """Cria uma lista de contatos no Hermes com os telefones captados."""
    url = server.rstrip("/") + "/api/contact-lists"
    body = json.dumps({"name": list_name, "phones": phones}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token,
        "User-Agent": UA,
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode()


def main():
    ap = argparse.ArgumentParser(description="Captação de leads B2B (dados públicos, keyless)")
    ap.add_argument("--geocode", help="descobre a bbox de uma cidade e sai (ex: 'Goiânia, GO')")
    ap.add_argument("--bbox", help="south,west,north,east (ex: -16.75,-49.35,-16.60,-49.20)")
    ap.add_argument("--categories", default="shop=solar,office=energy_supplier,craft=electrician",
                    help="tags OSM key=value separadas por vírgula")
    ap.add_argument("--limit", type=int, default=200, help="máx de resultados")
    ap.add_argument("--out", help="salva os leads num JSON")
    ap.add_argument("--server", default="", help="base do Hermes (pra criar a lista)")
    ap.add_argument("--token", default="", help="JWT do dono (pra criar a lista)")
    ap.add_argument("--list-name", default="", help="nome da lista a criar no Hermes")
    args = ap.parse_args()

    if args.geocode:
        bb = geocode(args.geocode)
        if bb:
            print(f"\nUse: --bbox {bb[0]},{bb[1]},{bb[2]},{bb[3]}")
        return 0

    if not args.bbox:
        print("Erro: informe --bbox (ou use --geocode pra descobrir).")
        return 1

    bbox = tuple(float(x) for x in args.bbox.split(","))
    if len(bbox) != 4:
        print("Erro: --bbox precisa de 4 números: south,west,north,east")
        return 1

    cats = [c.strip() for c in args.categories.split(",") if c.strip()]
    leads = capture(bbox, cats, args.limit)
    print(f"\n=== {len(leads)} leads captados (com telefone BR válido) ===")
    for l in leads[:20]:
        print(f"  {l['phone']}  {l['name'][:35]:35}  {l['category']:22}  {l['address'][:30]}")
    if len(leads) > 20:
        print(f"  ... e mais {len(leads)-20}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=2)
        print(f"\n[out] salvo em {args.out}")

    if args.server and args.token and args.list_name:
        phones = [l["phone"] for l in leads]
        if not phones:
            print("[hermes] nenhum telefone pra criar lista.")
            return 0
        try:
            st, resp = create_list_in_hermes(args.server, args.token, args.list_name, phones)
            print(f"[hermes] lista '{args.list_name}' criada -> HTTP {st}: {resp[:200]}")
        except Exception as e:
            print(f"[hermes] falha ao criar lista: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
