#!/usr/bin/env python3
"""coletor_vps.py — fontes da própria VPS para o Painel de Clientes (hermes-prod, cron a cada 5 min, root).

Só LÊ e grava JSON em /opt/painel-clientes/servidor/dados/fontes (o painel importa quando o arquivo muda):
  - loja_<id>.json: pedidos e mensagens de WhatsApp recebidas da loja no acai-lojas (banco aberto SOMENTE LEITURA
    por `docker exec acai-lojas node`, com o node:sqlite do próprio contêiner — não toca nos arquivos da loja).
  - visitas.json: páginas abertas e pessoas por dia de cada site, do log /var/log/nginx/painel_visitas.log (formato
    painel_visitas, com host e IP real do Traefik; ligado pelo publicar.py). Robôs e /api/ ficam de fora.
Só biblioteca padrão. Log curto em /opt/painel-clientes/coletor_vps.log.
"""
import json
import re
import subprocess
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

BASE = Path("/opt/painel-clientes")
DADOS = BASE / "servidor" / "dados"
FONTES = DADOS / "fontes"
CONFIG = DADOS / "clientes.json"
LOG_VISITAS = Path("/var/log/nginx/painel_visitas.log")
LOG = BASE / "coletor_vps.log"
WA_LOJA = Path("/opt/acai-lojas/servidor/dados/whatsapp")
ROBO = re.compile(r"bot|crawl|spider|slurp|facebookexternalhit|facebot|whatsapp|telegram|preview|curl|python|wget|"
                  r"headless|monitor|uptime|httpclient|okhttp|go-http|lighthouse|pingdom", re.I)

NODE = r"""
const {DatabaseSync} = require('node:sqlite');
const db = new DatabaseSync('/app/dados/acai.db', {readOnly: true});
const loja = process.env.LOJA;
const desde = new Date(Date.now() - 400 * 864e5).toISOString();
const itens = (s) => { try { return JSON.parse(s || '[]').map(i => `${i.qntd || 1}x ${i.name}`).join(', '); } catch (e) { return ''; } };
const pedidos = db.prepare(`SELECT id, criado_em, nome, telefone, total, status, forma_pagamento, cupom, desconto, itens,
  tipo_entrega, avaliacao, origem FROM pedidos WHERE loja = ? AND criado_em >= ? ORDER BY id`).all(loja, desde)
  .map(p => ({...p, itens: itens(p.itens)}));
let mensagens = [];
try {
  mensagens = db.prepare(`SELECT m.id, m.telefone, m.texto, m.em, c.nome FROM mensagens m LEFT JOIN conversas c
    ON c.loja = m.loja AND c.telefone = m.telefone WHERE m.loja = ? AND m.de_mim = 0 AND m.em >= ?
    ORDER BY m.id DESC LIMIT 5000`).all(loja, desde);
} catch (e) {}
const n = (s) => { try { return db.prepare(s).get(loja).n; } catch (e) { return null; } };
process.stdout.write(JSON.stringify({loja, pedidos, mensagens,
  clientes: n('SELECT COUNT(*) n FROM clientes WHERE loja = ?'), conversas: n('SELECT COUNT(*) n FROM conversas WHERE loja = ?')}));
"""


def log(m):
    try:
        if LOG.exists() and LOG.stat().st_size > 2_000_000:
            LOG.write_text(LOG.read_text(encoding="utf-8", errors="replace")[-400_000:], encoding="utf-8")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%d/%m %H:%M:%S}] {m}\n")
    except OSError:
        pass


def gravar(nome, dados):
    FONTES.mkdir(parents=True, exist_ok=True)
    tmp = FONTES / (nome + ".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    tmp.chmod(0o644)
    tmp.replace(FONTES / nome)


def lojas():
    try:
        cl = json.loads(CONFIG.read_text(encoding="utf-8")).get("clientes") or []
    except (OSError, ValueError):
        return []
    return sorted({c["loja"] for c in cl if c.get("loja") and c.get("ativo", True)})


def coletar_loja(loja):
    r = subprocess.run(["docker", "exec", "-i", "-e", f"LOJA={loja}", "acai-lojas", "node",
                        "--disable-warning=ExperimentalWarning", "-"], input=NODE.encode(), capture_output=True,
                       timeout=90)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or b"").decode(errors="replace")[-300:])
    d = json.loads(r.stdout.decode("utf-8"))
    pasta = WA_LOJA / loja
    d["whatsapp_conectado"] = (pasta / "creds.json").exists() if pasta.exists() else False
    d["gerado_em"] = datetime.now().astimezone().isoformat(timespec="seconds")
    gravar(f"loja_{loja}.json", d)
    return f"{loja}: {len(d['pedidos'])} pedidos, {len(d['mensagens'])} mensagens"


def _pagina(caminho):
    # só a vitrine conta: o painel da loja (/admin) é a própria loja trabalhando, não visita de cliente
    if caminho.startswith(("/api/", "/r/", "/css/", "/js/", "/img/", "/fonts/", "/admin")):
        return False
    final = caminho.rsplit("/", 1)[-1]
    return caminho.endswith("/") or final.endswith(".html") or "." not in final


def casa():
    """IP + navegador de quem entrou no painel (o app.py grava em dados/casa.json): é a casa, não visita de cliente."""
    try:
        return set((json.loads((DADOS / "casa.json").read_text(encoding="utf-8")).get("navegadores") or {}).keys())
    except (OSError, ValueError):
        return set()


def coletar_visitas():
    dias = {}
    unicos = {}
    lidos = fora = 0
    da_casa = casa()
    for arq in (LOG_VISITAS.with_name(LOG_VISITAS.name + ".1"), LOG_VISITAS):
        if not arq.exists():
            continue
        with open(arq, encoding="utf-8", errors="replace") as f:
            for ln in f:
                p = ln.rstrip("\n").split("\t")
                if len(p) < 8:
                    continue
                quando, host, xff, metodo, uri, status, _ref, ua = p[:8]
                if metodo != "GET" or status not in ("200", "304") or ROBO.search(ua):
                    continue
                u = urllib.parse.urlsplit(uri)
                if not _pagina(u.path):
                    continue
                dia, host = quando[:10], host.lower().split(":")[0]
                ip = (xff.split(",")[0].strip() if xff and xff != "-" else "")
                if f"{ip}\t{ua[:200]}" in da_casa:
                    fora += 1
                    continue
                v = dias.setdefault(dia, {}).setdefault(host, {"paginas": 0, "visitantes": 0, "codigos": {}})
                v["paginas"] += 1
                k = (dia, host, ip, ua)
                if k not in unicos:
                    unicos[k] = 1
                    v["visitantes"] += 1
                    q = urllib.parse.parse_qs(u.query)
                    cod = (q.get("c") or q.get("utm_campaign") or [""])[0][:40]
                    if cod:
                        v["codigos"][cod] = v["codigos"].get(cod, 0) + 1
                lidos += 1
    antigo = {}
    try:
        antigo = json.loads((FONTES / "visitas.json").read_text(encoding="utf-8")).get("dias") or {}
    except (OSError, ValueError):
        pass
    antigo.update(dias)  # os dias que estão nos logs atuais são recontados inteiros; os mais velhos ficam
    gravar("visitas.json", {"gerado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
                            "dias": dict(sorted(antigo.items())[-800:])})
    return f"visitas: {lidos} páginas lidas em {len(dias)} dia(s), {fora} da casa fora"


def main():
    resumo = []
    for loja in lojas():
        try:
            resumo.append(coletar_loja(loja))
        except Exception as e:  # noqa: BLE001
            resumo.append(f"{loja}: ERRO {type(e).__name__}: {str(e)[:200]}")
    try:
        resumo.append(coletar_visitas())
    except Exception as e:  # noqa: BLE001
        resumo.append(f"visitas: ERRO {type(e).__name__}: {e}")
    log(" | ".join(resumo))
    if "--ver" in sys.argv:
        print("\n".join(resumo))


if __name__ == "__main__":
    main()
