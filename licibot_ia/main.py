"""
LiciBot-IA · main.py
  python main.py --scan                 varredura completa (filtro -> enriquecimento -> IA -> aviso)
  python main.py --scan --sem-ia        só os estágios 1 e 2 (não gasta modelo)
  python main.py --scan --max-paginas 5 varredura curta (teste)
  python main.py --stats                estatísticas e as melhores oportunidades abertas
  python main.py --export-ranking-cnaes ranking de CNAEs em CSV
  python main.py --ver <numeroControlePNCP>   tudo que o robô sabe de um edital (JSON)
  python main.py --reanalisar           devolve à fila da IA os que falharam
  python main.py --resultados           coleta o preço vencedor dos que já fecharam (aprende o desconto)
  python main.py --teste-filtro "texto do objeto"
Feito para cron: trava de execução única, log em arquivo, código de saída 0 mesmo sem oportunidades.
"""

import argparse
import csv
import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

import database as db
from config import (BASE, DIAS_COLETA_RESULTADO, LLM_MAX_TENTATIVAS, LLM_PARALELO, LOG_PATH,
                    IA_MAX_POR_VARREDURA, PNCP_PARALELO)

log = logging.getLogger("licibot")


def configurar_log(verboso: bool) -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    arq = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    arq.setFormatter(fmt)
    tela = logging.StreamHandler(sys.stdout)
    tela.setFormatter(logging.Formatter("%(message)s"))
    raiz = logging.getLogger()
    raiz.setLevel(logging.DEBUG if verboso else logging.INFO)
    raiz.addHandler(arq)
    raiz.addHandler(tela)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


class Trava:
    """Impede duas varreduras ao mesmo tempo (cron sobrepondo). Funciona em Linux e Windows."""

    def __init__(self, caminho: Path):
        self.caminho = caminho
        self.fd = None

    def __enter__(self):
        self.fd = open(self.caminho, "a+")
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.fd.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.fd.close()
            print("outra varredura já está rodando; saindo.")
            raise SystemExit(0)
        return self

    def __exit__(self, *exc):
        self.fd.close()


# ═════════════════════════════════════════════════════════════════════════════

def _desde_incremental(completa: bool) -> datetime | None:
    """Leitura incremental = só o publicado/alterado desde a última leitura que deu certo (com 2 h de folga).
    Completa: pedida, 1ª vez, última completa há mais de 20 h, ou incremental falhou. None = completa."""
    if completa:
        return None
    ult = db.ultima_leitura_ok()
    ult_completa = db.ultima_leitura_ok(so_completa=True)
    if not ult or not ult_completa:
        return None
    if datetime.now() - datetime.fromisoformat(ult_completa) > timedelta(hours=20):
        return None
    return datetime.fromisoformat(ult) - timedelta(hours=2)


def estagio1(max_paginas: int | None, completa: bool = False) -> dict[str, int]:
    from pncp_client import buscar_propostas_abertas
    desde = None if max_paginas else _desde_incremental(completa)
    if desde is None:
        log.info("▶ Estágio 1: lendo TODAS as contratações com proposta aberta no PNCP (leitura completa)")
    else:
        log.info("▶ Estágio 1: lendo só o que foi publicado/alterado no PNCP desde %s", desde.strftime("%d/%m %H:%M"))
    t = time.time()
    contagem = {"novo": 0, "alterado": 0, "igual": 0, "revogados": 0}
    trava = threading.Lock()

    def gravar(p):
        r = db.salvar_proposta(p)
        with trava:
            contagem[r] += 1

    def revogar(numero, motivo):
        if db.marcar_revogado(numero, motivo):
            with trava:
                contagem["revogados"] += 1

    _, cont = buscar_propostas_abertas(max_paginas, ao_aprovar=gravar, ao_revogar=revogar, desde=desde)
    cont["tipo_leitura"] = "completa" if desde is None else "incremental"
    if contagem["revogados"]:
        log.info("  %s edital(is) que já estavam na fila foram revogados/suspensos pelo órgão", contagem["revogados"])
    novos, alterados = contagem["novo"], contagem["alterado"]
    log.info("  %s lidas, %s passaram no filtro (%s novas, %s alteradas pelo órgão), %s fecham em menos de "
             "24 h, %s revogadas/suspensas, %s páginas falharam — %.0f s", cont["lidos"], cont["filtrados"], novos,
             alterados, cont["prazo_curto"], cont["fechados"], cont["paginas_falhas"], time.time() - t)
    return {**cont, "novos": novos}


def estagio2() -> int:
    from pncp_client import PNCPErro, enriquecer
    pend = db.listar_por_status("novo")
    if not pend:
        return 0
    log.info("▶ Estágio 2: itens e documentos de %s edital(is)", len(pend))

    def um(e):
        try:
            r = enriquecer(e)
        except PNCPErro as err:
            log.warning("  %s: PNCP falhou (%s); tenta na próxima varredura", e["numero_controle"], err)
            return
        except Exception as err:   # anexo esquisito não pode derrubar a varredura
            log.exception("  %s: erro inesperado ao ler documentos", e["numero_controle"])
            db.atualizar_edital(e["numero_controle"], {"ultimo_erro": f"{type(err).__name__}: {err}"[:500]})
            return
        if r.get("revogado"):
            db.atualizar_edital(e["numero_controle"], {"status": "revogado", "ultimo_erro": r["revogado"]})
            log.info("  %s: %s no PNCP", e["numero_controle"], r["revogado"])
            return
        db.salvar_itens(e["numero_controle"], r["itens"])
        db.atualizar_edital(e["numero_controle"], {
            "texto_docs": r["texto_docs"], "docs_lidos": r["docs_lidos"], "exclusivo_me_epp": r["exclusivo_me_epp"],
            "qtd_itens": r["qtd_itens"], "valor_estimado": r["valor_estimado"], "status": "enriquecido",
            "ultimo_erro": "documento de revogação/suspensão publicado" if r["aviso_revogacao"] else None})
        log.info("  %s: %s itens, %s caracteres de documentos", e["numero_controle"], r["qtd_itens"],
                 len(r["texto_docs"]))

    with ThreadPoolExecutor(PNCP_PARALELO) as ex:
        list(ex.map(um, pend))
    return len(pend)


def estagio3() -> dict[str, int]:
    from ai_analyzer import InfraIA, analisar
    pend = db.listar_por_status("enriquecido")
    if not pend:
        return {"analisados": 0, "falhas_ia": 0, "tokens": 0}
    from ai_analyzer import MODELOS_GRATIS, cadeia_atual, pre_nota
    # 1º o que fecha antes da próxima varredura (senão vence na fila), depois a melhor pré-nota
    limite = (datetime.now() + timedelta(hours=30)).strftime("%Y-%m-%d %H:%M:%S")
    pend.sort(key=lambda e: (e["data_encerramento"] > limite, -pre_nota(e)))
    if IA_MAX_POR_VARREDURA and len(pend) > IA_MAX_POR_VARREDURA:
        log.info("  fila da IA: %s; analisando as %s com melhor pré-nota (o resto na próxima)",
                 len(pend), IA_MAX_POR_VARREDURA)
        pend = pend[:IA_MAX_POR_VARREDURA]
    log.info("▶ Estágio 3: %s edital(is), modelos grátis em cadeia: %s (%s por vez)", len(pend),
             " → ".join(MODELOS_GRATIS[m]["nome"] for m in cadeia_atual()), LLM_PARALELO)
    descontos = db.descontos_historicos()
    res = {"analisados": 0, "falhas_ia": 0, "tokens": 0}
    infra_seguidas = [0]   # todos os modelos grátis fora: 5 seguidas = para e deixa a fila para a próxima

    def um(e):
        if infra_seguidas[0] >= 5:
            return None
        t = time.time()
        try:
            campos = analisar(e, db.itens_de(e["numero_controle"]), descontos)
            infra_seguidas[0] = 0
        except Exception as err:   # AnaliseFalhou, InfraIA ou resposta inesperada do modelo
            if isinstance(err, InfraIA):
                infra_seguidas[0] += 1
            n = e["tentativas_ia"] + (0 if isinstance(err, InfraIA) else 1)
            db.atualizar_edital(e["numero_controle"], {
                "tentativas_ia": n, "ultimo_erro": str(err)[:500],
                "status": "sem_analise" if n >= LLM_MAX_TENTATIVAS else "enriquecido"})
            log.warning("  %s: IA falhou (%s/%s): %s", e["numero_controle"], n, LLM_MAX_TENTATIVAS, err)
            return None
        db.atualizar_edital(e["numero_controle"], campos)
        log.info("  %s → %s nota %.0f líquido R$ %.0f (%s, %.0f s)", e["numero_controle"], campos["carteira"],
                 campos["nota_final"], campos["margem_estimada"], campos["modelo_ia"], time.time() - t)
        return campos["tokens_ia"]

    with ThreadPoolExecutor(LLM_PARALELO) as ex:
        for f in as_completed([ex.submit(um, e) for e in pend]):
            tok = f.result()
            if tok is None:
                res["falhas_ia"] += 1
            else:
                res["analisados"] += 1
                res["tokens"] += tok
    if infra_seguidas[0] >= 5:
        log.warning("Todos os modelos grátis falharam 5 vezes seguidas; o resto da fila fica para a próxima varredura.")
        from notifier import aviso_sem_credito
        aviso_sem_credito("todos os modelos grátis fora (Sonnet web, Genspark, Argon e Gemini)",
                          len(db.listar_por_status("enriquecido")))
    return res


def avisar(forcar: bool = False) -> int:
    """Oportunidades novas nos filtros do painel + lembretes de prazo + resumo diário.
    No horário silencioso não manda nada (forcar=True = botão "Avisar agora" do painel)."""
    from config import avisos
    from notifier import aviso_lembretes, aviso_resumo, em_silencio, notificar, passa_filtros
    cfg = avisos()
    if em_silencio(cfg) and not forcar:
        log.info("Horário silencioso (%sh–%sh): avisos ficam para depois.", cfg["silencio_de"], cfg["silencio_ate"])
        return 0

    lembretes = db.lembretes_prazo()
    if lembretes and aviso_lembretes(lembretes):
        db.marcar_lembrados([e["numero_controle"] for e in lembretes])

    candidatos = db.para_notificar(0)
    lista = [e for e in candidatos if passa_filtros(e, cfg)]
    fora = [e["numero_controle"] for e in candidatos if not passa_filtros(e, cfg)]
    if fora:  # fora dos filtros: marca para não ficar sendo reavaliado a cada varredura
        db.marcar_notificados(fora, valor=2)
    enviados = 0
    lista.sort(key=lambda e: -(e.get("nota_final") or 0))
    # acúmulo (ex.: 1ª vez que o Telegram é ligado): manda só as melhores e dá as outras por vistas,
    # em vez de 10 por hora durante o dia inteiro; o painel mostra todas
    excesso = lista[cfg["max_por_aviso"]:] if len(lista) > 2 * cfg["max_por_aviso"] else []
    lista = lista[:cfg["max_por_aviso"]]       # sem acúmulo, o resto sai na próxima rodada
    if lista:
        if notificar(lista, a_mais=len(excesso)):
            db.marcar_notificados([e["numero_controle"] for e in lista + excesso])
            enviados = len(lista)
        else:
            log.info("nenhum canal de aviso recebeu (Telegram configurado?); ficam pendentes para a próxima")
    else:
        log.info("Nada novo nos filtros de aviso (%s fora dos filtros).", len(fora))

    if datetime.now().hour >= int(cfg["hora_resumo"]):
        abertas = [e for e in db.abertas_analisadas() if passa_filtros({**e, "nota_final": 999}, cfg)]
        aviso_resumo({"abertas": len(abertas),
                      "fecha_48h": sum(1 for e in abertas if e["data_encerramento"] <=
                                       (datetime.now() + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")),
                      "participar": sum(1 for e in abertas if e.get("decisao") == "participar"),
                      "fila": len(db.listar_por_status("enriquecido")),
                      "top": sorted(abertas, key=lambda e: -(e["nota_final"] or 0))})
    return enviados


def coletar_resultados() -> int:
    from pncp_client import PNCPErro, resultados_itens
    pend = db.pendentes_resultado(DIAS_COLETA_RESULTADO)
    feitos = 0
    for e in pend:
        itens = db.itens_de(e["numero_controle"])
        try:
            res = resultados_itens(e["cnpj_orgao"], e["ano_compra"], e["sequencial_compra"],
                                   [i["numero_item"] for i in itens])
        except PNCPErro as err:
            log.warning("resultado %s: %s", e["numero_controle"], err)
            continue
        for n, r in res.items():
            db.salvar_resultado_item(e["numero_controle"], n, r["valor"], r["porte"], r["tipo"])
        # sem resultado publicado ainda: tenta de novo nas próximas, até 60 dias depois de fechar
        if res or e["data_encerramento"] < (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S"):
            db.atualizar_edital(e["numero_controle"], {"resultado_coletado": 1})
        feitos += bool(res)
    if pend:
        log.info("Resultados coletados de %s licitação(ões) encerrada(s).", feitos)
    return feitos


def cmd_scan(args) -> None:
    with Trava(BASE / ".licibot.lock"):
        eid = db.abrir_execucao()
        dados = {}
        try:
            exp = db.expirar_vencidos()
            if exp:
                log.info("%s edital(is) venceram antes da análise.", exp)
            c1 = estagio1(args.max_paginas, completa=getattr(args, "completa", False))
            dados.update(lidos=c1["lidos"], filtrados=c1["filtrados"], novos=c1["novos"])
            if c1["paginas_falhas"] == 0 and c1["lidos"] > 0 and not args.max_paginas:
                dados["leitura"] = c1["tipo_leitura"]       # só leitura sem falha conta como ponto de partida
            estagio2()
            if not args.sem_ia:
                dados.update(estagio3())
                dados["notificados"] = avisar()
            coletar_resultados()
            liberados = db.limpar_texto_encerrados()
            if liberados:
                log.info("Limpeza: texto de %s edital(is) encerrados apagado (itens e análise ficam).", liberados)
        except Exception as err:
            dados["erro"] = f"{type(err).__name__}: {err}"[:500]
            log.exception("varredura quebrou")
            try:
                from notifier import aviso_erro
                aviso_erro(dados["erro"])
            except Exception:
                log.exception("não consegui avisar o erro")
            raise
        finally:
            db.fechar_execucao(eid, dados)


def _brl(v) -> str:
    return "—" if v is None else f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cmd_stats() -> None:
    s = db.estatisticas()
    print(f"\n{'═' * 72}\n  LiciBot-IA — estatísticas\n{'═' * 72}")
    print("  Por situação: " + ", ".join(f"{k} {v}" for k, v in sorted(s["por_status"].items())))
    print("  Por gaveta:   " + ", ".join(f"{r['gaveta']} {r['n']}" for r in s["por_gaveta"]))
    print(f"  Tokens gastos na IA: {s['tokens']:,}".replace(",", "."))
    if s["descontos"]:
        print("  Desconto real dos vencedores: " + ", ".join(
            f"{g} {d['mediana']:.0%} ({d['n']} itens)" for g, d in s["descontos"].items()))
    if s["por_carteira"]:
        print(f"\n  {'Carteira':<12} {'Qtd':>4} {'Estimado':>18} {'Líquido':>16} {'Nota':>5}")
        for r in s["por_carteira"]:
            print(f"  {r['carteira'] or '?':<12} {r['n']:>4} {_brl(r['valor']):>18} {_brl(r['margem']):>16} "
                  f"{r['nota'] or 0:>5}")
    if s["abertas"]:
        print("\n  Melhores ainda abertas:")
        for r in s["abertas"]:
            print(f"  {r['nota_final']:>4.0f} {r['carteira']:<11} {_brl(r['margem_estimada']):>14}  fecha "
                  f"{r['data_encerramento'][:16]}  {r['uf']}/{r['municipio']}  {(r['objeto_compra'] or '')[:60]}")
            print(f"       {r['numero_controle']}")
    if s["execucoes"]:
        print("\n  Últimas varreduras:")
        for x in s["execucoes"]:
            print(f"  {x['inicio']} → {x['fim'] or 'rodando'}  lidas {x['lidos']} filtro {x['filtrados']} "
                  f"novas {x['novos']} IA {x['analisados']} (falhas {x['falhas_ia']}) avisos {x['notificados']}"
                  f"{'  ERRO ' + x['erro'] if x['erro'] else ''}")
    print()


def cmd_ranking(saida: str) -> None:
    rows = db.ranking_cnaes()
    if not rows:
        print("Ainda não há edital analisado com CNAE. Rode --scan primeiro.")
        return
    with open(saida, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rows)
    print(f"Ranking salvo em {saida} ({len(rows)} CNAEs)\n")
    print(f"  {'CNAE':<11} {'Oport.':>6} {'Estimado':>16} {'Líquido':>16} {'Nota':>5}  Descrição")
    for r in rows:
        print(f"  {r['cnae_codigo']:<11} {r['total_oportunidades']:>6} {_brl(r['valor_total']):>16} "
              f"{_brl(r['margem_total']):>16} {r['nota_media']:>5}  {r['cnae_descricao'][:50]}")


def main() -> None:
    p = argparse.ArgumentParser(description="LiciBot-IA — monitor de licitações do PNCP com análise por IA",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("--scan", action="store_true")
    p.add_argument("--sem-ia", action="store_true", help="no --scan, para antes do estágio 3")
    p.add_argument("--max-paginas", type=int, help="limita páginas por modalidade (teste)")
    p.add_argument("--completa", action="store_true", help="no --scan, força a leitura completa do PNCP")
    p.add_argument("--stats", action="store_true")
    p.add_argument("--export-ranking-cnaes", nargs="?", const="ranking_cnaes.csv", metavar="ARQ")
    p.add_argument("--ver", metavar="NUMERO_PNCP")
    p.add_argument("--reanalisar", action="store_true")
    p.add_argument("--resultados", action="store_true")
    p.add_argument("--avisos", action="store_true", help="só avisos (lembretes de prazo, resumo, pendentes); o cron roda de hora em hora")
    p.add_argument("--teste-filtro", metavar="TEXTO")
    p.add_argument("-v", "--verboso", action="store_true")
    a = p.parse_args()

    if not any([a.scan, a.stats, a.export_ranking_cnaes, a.ver, a.reanalisar, a.resultados, a.teste_filtro, a.avisos]):
        p.print_help()
        return

    configurar_log(a.verboso)
    db.init_db()

    if a.teste_filtro:
        from pncp_client import classificar
        g, m = classificar(a.teste_filtro)
        print(f"gaveta: {g or 'DESCARTADO'}  casou: {m}")
    if a.reanalisar:
        print(f"{db.resetar_sem_analise()} edital(is) voltaram para a fila da IA.")
    if a.scan:
        cmd_scan(a)
    if a.resultados:
        coletar_resultados()
    if a.avisos:
        print(f"{avisar()} aviso(s) de oportunidade enviado(s)")
    if a.stats:
        cmd_stats()
    if a.export_ranking_cnaes:
        cmd_ranking(a.export_ranking_cnaes)
    if a.ver:
        print(db.exportar_json(a.ver))


if __name__ == "__main__":
    main()
