# -*- coding: utf-8 -*-
"""MS Energy — shorts Veo 3.1 para uma empresa REAL de energia solar no Para (objetivo: pedidos de orcamento).

Pipeline (refeito em 22/10/2026, analise em docs\\ANALISE_CAMPANHA.md):
  1. roteiro_ms   — pauta real (duvidas de quem pensa em instalar), sem prometer "zerar", sem numero, sem concessionaria
  2. Veo 3.1 Fast — escada de contas/creditos do Veo principal; 1o quadro = foto REAL de instalacao do Instagram da
                    empresa (ou consultor(a) gerado(a) pelo Veo); a voz e a do proprio Veo
  3. qa_ms        — trava: comecou na foto? ficou na mesma cena? faixa preta? texto/deformacao? a fala bate?
  4. montagem_ms  — frase no topo + legenda da fala + cartao com logo/WhatsApp (sem efeitos de meme)
  5. qa_ms final  — duracao com cartao, audio; reprovado vai para videos\\_revisar, nunca para a fila
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DIR_PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIR_PROJETO / "bin"))

_VEO_BETA = Path(r"D:\veo\beta")
sys.path.insert(0, str(_VEO_BETA))

# Pool de contas compartilhado com o Veo principal (fonte única: contas.py)
from contas import SESSOES
# Gerenciamento de sessões do orquestrador Veo
from cron_gerar_video_llm import (
    load_sessoes_status, save_sessoes_status,
    escolher_sessao, aplicar_sessao,
    registrar_falha_sessao, registrar_sucesso_sessao,
    marcar_creditos_esgotados, marcar_conta_fora,
)
import recursos

DIR_VIDEOS = DIR_PROJETO / "videos" / "shorts_veo"
DIR_REVISAR = DIR_PROJETO / "videos" / "_revisar"
DIR_TMP = DIR_PROJETO / "cache" / "tmp_veo"
DIR_CACHE_VEO = DIR_PROJETO / "cache" / "veo_clips"
DIR_REPROVADOS = DIR_CACHE_VEO / "reprovados"

GERA_AUTO = Path(r"D:\veo\beta\gera_auto.py")
# venv proprio do Veo (o antigo D:\hipercool-videos\venv foi apagado em 2026-10).
VEO_PYTHON = Path(r"D:\veo\venv\Scripts\python.exe")
if not VEO_PYTHON.exists():
    VEO_PYTHON = Path(r"D:\veo\beta\venv\Scripts\python.exe")

_FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"

TIPO_COM_FOTO = "com_foto"
TIPO_CRIATIVO = "criativo"

# Resiliência: mesmos parâmetros do Veo principal
TENTATIVAS_POR_PROMPT = 2
MAX_CONTAS = min(3, len(SESSOES))
CAP_POR_CONTA = TENTATIVAS_POR_PROMPT * 2
# clipe reprovado na trava gasta credito (22/10: o pool tem so 3 contas): no maximo 2 por short; foto real
# reprovada passa a apresentador, que o Veo faz bem (com foto de instalacao ele inventava placas)
MAX_QA_FALHAS = 2


def _dur(path):
    try:
        r = subprocess.run(
            [_FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=20)
        return float(r.stdout.strip())
    except Exception:
        return None


def _tem_audio(path):
    try:
        r = subprocess.run(
            [_FFPROBE, "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=20)
        return "audio" in r.stdout
    except Exception:
        return False


def gerar_video_robusto(prompt, foto, out_path, log=print):
    """Gera 1 clipe via gera_auto.py — lógica copiada do cron_gerar_video_llm.gerar_video().

    Retorna:
      True                    — vídeo gerado com sucesso
      False                   — falha genérica
      ("NO_CREDITS", padrao)  — créditos esgotados
      "COPYRIGHT_BLOCKED"     — bloqueio por direitos autorais
      "PAUSED"                — sistema pausado
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [
        str(VEO_PYTHON),
        str(GERA_AUTO),
        prompt,
        str(out_path),
    ]
    if foto:
        cmd.append(str(foto))

    # 01/11 (dona: solar > produtos > entretenimento; "o PC2 e o desktop estão livres, por que não usa ao máximo?"):
    # a reserva "veo" do Veo de entretenimento não barra mais o Reel do cliente (antes: horas de "notebooks ocupados").
    # Reserva de outro dono (login da dona, telão, câmera) continua valendo.
    os.environ["MAQUINA_VEZ_DE"] = "veo"
    try:
        tmo = recursos.timeout_dinamico(720)
    except Exception:
        tmo = 2400 if foto else 1200

    log(f"  [VEO] gerando (timeout={tmo}s, foto={'SIM' if foto else 'NAO'})...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=tmo,
                                encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        log(f"  [VEO] TIMEOUT ({tmo}s)")
        return "TRAVOU"

    if result.returncode == 5:
        log("  [VEO] sistema pausado")
        return "PAUSED"

    if result.returncode == 2:
        output = (result.stdout or "") + (result.stderr or "")
        log("  [VEO] exit=2 → CRÉDITOS ESGOTADOS")
        import re as _re
        m = _re.search(r"padrao='([^']*)'", output)
        padrao = m.group(1) if m else "no_credits"
        return ("NO_CREDITS", padrao)

    output = (result.stdout or "") + (result.stderr or "")
    if "CREDITOS_ESGOTADOS" in output:
        log("  [VEO] marcador CREDITOS_ESGOTADOS detectado")
        import re as _re
        m = _re.search(r"padrao='([^']*)'", output)
        padrao = m.group(1) if m else ""
        return ("NO_CREDITS", padrao)

    if result.returncode == 4 or "DIREITOS_AUTORAIS" in output:
        log("  [VEO] DIREITOS AUTORAIS / COPYRIGHT BLOQUEADO")
        return "COPYRIGHT_BLOCKED"

    if result.returncode == 3 or "SESSAO_EXPIRADA" in output:
        motivo = [ln.strip() for ln in output.splitlines()
                  if any(k in ln for k in ("[notebook]", "SESSAO_EXPIRADA", "[http]", "login"))][-4:]
        log("  [VEO] exit=3 → conta deslogada ou bloqueada no Flow | " + " / ".join(m[:140] for m in motivo))
        return "SESSAO"

    if result.returncode == 7 or "RECAPTCHA_BLOQUEIO" in output:
        log("  [VEO] exit=7 → reCAPTCHA bloqueando a conta")
        return "RECAPTCHA"

    if "SO_NOTEBOOK:" in output:
        # 25/10 22:0x: conta que só existe nos notebooks e as máquinas estavam ocupadas postando -> nada foi pedido
        # ao Flow; não é falha da conta (antes repetia 4x na mesma conta e o teste do clone acabava sem vídeo)
        log("  [VEO] máquinas dos notebooks ocupadas — troco de conta sem castigo")
        return "MAQUINA_OCUPADA"

    if result.returncode != 0:
        # o gera_auto escreve o passo a passo no stdout; o stderr so tem o traceback
        stdout_tail = (result.stdout or "")[-700:]
        stderr_tail = result.stderr[-1500:] if result.stderr else ""
        log(f"  [VEO] FALHOU (exit={result.returncode}):\n{stdout_tail}\n{stderr_tail}")
        if "nada comecou a gerar" in output:
            return "TRAVOU"
        return False

    if os.path.exists(out_path) and os.path.getsize(out_path) > 100_000:
        dur = _dur(out_path)
        has_audio = _tem_audio(out_path)
        # ffprobe pode estourar o prazo com a RAM baixa e devolver None; o clipe está pronto do mesmo jeito
        dur_txt = f"{dur:.1f}s" if dur else "?s"
        log(f"  [VEO] OK: {Path(out_path).name} ({dur_txt}, audio={'SIM' if has_audio else 'NAO'})")
        return True

    log("  [VEO] arquivo não gerado ou muito pequeno")
    return False


def _guardar_reprovado(clip, roteiro, qa, n):
    """Clipe reprovado fica como prova (ultimos 40), com o motivo ao lado."""
    DIR_REPROVADOS.mkdir(parents=True, exist_ok=True)
    destino = DIR_REPROVADOS / f"{Path(clip).stem}_r{n}.mp4"
    shutil.move(str(clip), str(destino))
    destino.with_suffix(".json").write_text(json.dumps(
        {"motivos": qa["motivos"], "medidas": qa["medidas"], "roteiro": roteiro}, ensure_ascii=False, indent=1),
        "utf-8")
    velhos = sorted(DIR_REPROVADOS.glob("*.mp4"), key=lambda p: p.stat().st_mtime)[:-40]
    for v in velhos:
        v.unlink(missing_ok=True)
        v.with_suffix(".json").unlink(missing_ok=True)


def _marca_pendente(clip):
    return clip.with_name(clip.stem + ".pendente.json")


def _empresa_atual():
    """Qual empresa está rodando o pipeline agora (reel_advance/reel_globo trocam roteiro_ms.EMPRESA; padrão = MS)."""
    try:
        import roteiro_ms
        ig = str(getattr(roteiro_ms, "INSTAGRAM", "") or "").strip().lower()  # @ da conta: único por empresa
        nome = str(roteiro_ms.EMPRESA).split(",")[0].split("(")[0].split("|")[0].strip()[:40]
        return f"{nome} {ig}".strip()
    except Exception:  # noqa: BLE001
        return "?"


def _clipe_pendente(log):
    """03/11: o etapa.py corta a rodada aos 150 min e 2 vezes (02/11 14:41, 03/11 06:04) cortou logo depois do Veo
    entregar o clipe — crédito gasto e clipe esquecido no cache. Devolve (clip, roteiro, timestamp) do clipe que saiu
    do Veo e não chegou a ser montado (até 24 h), ou None.
    04/11 (dona: "foi postado no Insta da Globo conteúdo da Advance"): o cache é o MESMO das 3 empresas e o reaproveito
    não olhava de quem era o clipe — a Globo publicou 2 reels com o Luiz da Advance (03/11 09:28 DfR4fkZu9kI e 21:21
    DfTKW4-s-CD). Agora a marca leva a empresa e SÓ a mesma empresa reaproveita; marca sem empresa (antiga) não vale."""
    limite = datetime.datetime.now().timestamp() - 24 * 3600
    eu = _empresa_atual()
    for marca in sorted(DIR_CACHE_VEO.glob("solar_*.pendente.json"), reverse=True):
        clip = marca.with_name(marca.name.replace(".pendente.json", ".mp4"))
        try:
            roteiro = json.loads(marca.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            marca.unlink(missing_ok=True)
            continue
        if roteiro.get("_empresa") != eu:
            if not roteiro.get("_empresa"):
                marca.unlink(missing_ok=True)  # marca antiga sem dona: não dá pra saber de quem é — descarta
            continue  # clipe de OUTRA empresa: nunca reaproveita (fica pra dona dele)
        try:
            valido = marca.stat().st_mtime >= limite and clip.exists() and \
                (not roteiro.get("quadro") or Path(roteiro["quadro"]).exists())
        except Exception:  # noqa: BLE001
            valido = False
        marca.unlink(missing_ok=True)  # usa 1 vez só: se esta rodada morrer também, não entra em laço
        if valido:
            log(f"  [PENDENTE] reaproveito o clipe {clip.name} (saiu do Veo e a rodada anterior não montou)")
            return clip, roteiro, clip.stem.replace("solar_", "")
    return None


def gerar_short_veo(output_dir=None, tipo=TIPO_CRIATIVO, log=print):
    """Pipeline completo. tipo: 'com_foto' = foto real de instalacao do Instagram; 'criativo' = consultor(a) do Veo.
    Devolve o caminho do short aprovado, None (nada foi para a fila) ou "SEM_CONTA"."""
    import montagem_ms
    import qa_ms
    import roteiro_ms

    output_dir = Path(output_dir) if output_dir else DIR_VIDEOS
    for pasta in (output_dir, DIR_TMP, DIR_CACHE_VEO, DIR_REVISAR):
        pasta.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    tipo_ms = "foto_real" if tipo == TIPO_COM_FOTO else "apresentador"

    log(f"{'=' * 50}")
    log(f"  MS Energy — Short Veo 3.1 [{tipo_ms.upper()}]")
    log(f"  Pipeline: roteiro_ms → Veo 3.1 → trava → montagem_ms → trava final")
    log(f"{'=' * 50}")

    pend = _clipe_pendente(log)
    if pend:
        timestamp = pend[2]
    # sem conta livre nao vale gastar LLM (antes rodavam a cada 60 s mesmo sem conta)
    if not pend and escolher_sessao() is None:
        log("  [STOP] sem conta livre (esgotadas, em cooldown ou em uso pelo Veo)")
        return "SEM_CONTA"

    fotos_tentadas = set()

    def novo_roteiro(t):
        foto = None
        if t == "foto_real":
            foto = roteiro_ms.escolher_foto(evitar=fotos_tentadas)
            if foto is None:
                log("  [FOTO] sem foto real disponivel — vai de apresentador")
            else:
                fotos_tentadas.add(foto[0])
                log(f"  [FOTO] {foto[0]} ({foto[1].get('permalink')})")
        return roteiro_ms.gerar(t if foto else "apresentador", foto, log=log)

    qa, qa_falhas, gerou = None, 0, False
    sessao, contas_usadas, tentativas_na_conta = None, [], 0
    if pend:
        clip, roteiro = pend[0], pend[1]
        qa = qa_ms.checar_clipe(clip, roteiro, log=log)
        gerou = qa["ok"]
        if not gerou:
            qa_falhas = 1
            _guardar_reprovado(clip, roteiro, qa, qa_falhas)
            return None
    else:
        log("\n  [FASE 1] Roteiro MS Energy...")
        roteiro = novo_roteiro(tipo_ms)

        log("\n  [FASE 2] Clipe Veo 3.1 + trava de qualidade...")
        sessao = escolher_sessao()
        if sessao is None:
            log("  [STOP] sem conta disponível (todas em cooldown/esgotadas)")
            return "SEM_CONTA"
        aplicar_sessao(sessao)
        contas_usadas = [sessao["session"]]
        clip = DIR_CACHE_VEO / f"solar_{timestamp}.mp4"

    # 31/10 (dona): clone em 2-3 cenas/ambientes (escritório, painéis, inversor...) — cenas_veo.py; não saiu = clipe
    # único como antes
    if not gerou and roteiro.get("clone_bases") and os.environ.get("MS_MULTICENA", "1") != "0":
        try:
            import cenas_veo
            multi = cenas_veo.gerar_clipes(roteiro, timestamp, log)
        except Exception as e:  # noqa: BLE001
            log(f"  [CENAS] falhou ({type(e).__name__}: {str(e)[:150]}) — clipe único")
            multi = None
        if multi:
            clip, gerou = multi["clip"], True
            qa = {"ok": True, "motivos": [], "medidas": multi["medidas"], "palavras": multi["palavras"]}
            roteiro["prompt_veo"] = multi["prompts"]
            roteiro["cenas"] = len(multi["prompts"])

    max_tentativas = 0 if gerou else CAP_POR_CONTA * MAX_CONTAS + MAX_QA_FALHAS
    tentativa_n, espera_maq = -1, 0
    while tentativa_n + 1 < max_tentativas:
        tentativa_n += 1
        # Troca de CONTA se atingiu o cap desta conta
        if sessao is None or tentativas_na_conta >= CAP_POR_CONTA:
            if sessao is not None:
                log(f"  [resiliencia] {CAP_POR_CONTA} falhas na conta {sessao['session']} — trocando de CONTA")
                registrar_falha_sessao(sessao["session"], "falhas repetidas MS Energy")
                _st = load_sessoes_status()
                _inf = _st.get(sessao["session"], {})
                _inf["cooldown_until"] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat(timespec="seconds")
                _st[sessao["session"]] = _inf
                save_sessoes_status(_st)
            sessao = escolher_sessao()
            if sessao is None:
                log("  [STOP] sem conta disponível — todas bloqueadas")
                return None
            contas_usadas.append(sessao["session"])
            aplicar_sessao(sessao)
            tentativas_na_conta = 0

        tentativas_na_conta += 1
        log(f"  === tentativa {tentativa_n + 1} | conta={sessao['session']} | try_conta={tentativas_na_conta}/{CAP_POR_CONTA} ===")
        ok = gerar_video_robusto(roteiro["prompt_veo"], roteiro.get("quadro"), str(clip), log=log)

        if ok == "PAUSED":
            log("  [STOP] sistema pausado")
            return None
        if ok == "MAQUINA_OCUPADA":
            tentativas_na_conta -= 1  # nada foi pedido: não conta como tentativa
            # 01/11: com os notebooks ocupados pelos outros robôs, as 14 tentativas acabavam em 14 min sem pedir nada ao
            # Flow (Advance 16h e Globo 17h sem Reel). Cliente (solar) espera a vez: até 45 min sem gastar tentativa
            if espera_maq < 45 * 60:
                tentativa_n -= 1
                espera_maq += 90
            import time as _t
            _t.sleep(90)
            sessao = None
            continue
        if isinstance(ok, tuple) and ok[0] == "NO_CREDITS":
            padrao = ok[1] if len(ok) > 1 else ""
            log(f"  [CREDITOS] {sessao['session']} SEM CREDITOS (padrao='{padrao}')")
            marcar_creditos_esgotados(sessao["session"], padrao_texto=padrao)
            sessao = None
            continue
        if ok == "SESSAO":
            marcar_conta_fora(sessao["session"], "login caiu ou conta bloqueada no Flow", horas=6)
            sessao = None
            continue
        if ok == "RECAPTCHA":
            marcar_conta_fora(sessao["session"], "reCAPTCHA Enterprise", horas=0.25)
            sessao = None
            continue
        if ok == "TRAVOU":
            # 22/10: a mesma conta travou 24 min e a escada insistia nela ate 4x (o prazo da rotina e 150 min)
            log(f"  [sessao] {sessao['session']} travou no Flow — trocando de conta")
            marcar_conta_fora(sessao["session"], "Flow travado (nada gerou no prazo)", horas=1)
            sessao = None
            continue
        if ok == "COPYRIGHT_BLOCKED":
            log(f"  [DIREITOS] bloqueio na conta {sessao['session']} — roteiro/foto novos")
            if roteiro["tipo"] == "apresentador":
                sessao = None
            roteiro = novo_roteiro(roteiro["tipo"])
            continue
        if ok is True:
            registrar_sucesso_sessao(sessao["session"])
            # 04/11: a marca leva a EMPRESA dona do clipe (só ela reaproveita — ver _clipe_pendente)
            _marca_pendente(clip).write_text(json.dumps({**roteiro, "_empresa": _empresa_atual()}, ensure_ascii=False,
                                                        default=str), "utf-8")
            qa = qa_ms.checar_clipe(clip, roteiro, log=log)
            if qa["ok"]:
                gerou = True
                break
            _marca_pendente(clip).unlink(missing_ok=True)
            tentativas_na_conta -= 1  # reprovado na qualidade nao e falha da conta
            qa_falhas += 1
            _guardar_reprovado(clip, roteiro, qa, qa_falhas)
            if qa_falhas >= MAX_QA_FALHAS:
                log(f"  [STOP] clipe reprovado {qa_falhas}x na trava de qualidade — nada vai para a fila")
                return None
            roteiro = novo_roteiro("apresentador")
            continue

        log(f"  [sessao] {sessao['session']} falhou (tentativa {tentativas_na_conta}/{CAP_POR_CONTA} nesta conta)")
        registrar_falha_sessao(sessao["session"], "gerar_video falhou MS Energy")
        if tentativas_na_conta % TENTATIVAS_POR_PROMPT == 0:
            roteiro = novo_roteiro(roteiro["tipo"])

    if not gerou:
        log("  [STOP] todas as tentativas esgotadas")
        return None

    log("\n  [FASE 3] Montagem (frase no topo + legenda + cartão da marca)...")
    stem = f"ms_energy_solar_{timestamp}"
    output_path = output_dir / f"{stem}.mp4"
    fundo = roteiro.get("quadro")
    if not fundo:
        foto_fundo = roteiro_ms.escolher_foto()
        fundo = roteiro_ms.quadro_916(foto_fundo[0], float((foto_fundo[1].get("visao") or {}).get("foco_x") or 0.5)) \
            if foto_fundo else None
    ok_m, info = montagem_ms.montar(clip, roteiro, qa["palavras"], output_path, foto_fundo=fundo, log=log)
    if not ok_m:
        # 23/10 00:12: ffmpeg "Cannot allocate memory" num pico de memoria do PC jogou fora um clipe que ja tinha
        # gastado credito do Veo -> espera a memoria aliviar e tenta mais 1x
        import time as _t
        log("  [MONTAGEM] falhou — espero 90 s e tento de novo (pico de memória?)")
        _t.sleep(90)
        ok_m, info = montagem_ms.montar(clip, roteiro, qa["palavras"], output_path, foto_fundo=fundo, log=log)
    _marca_pendente(clip).unlink(missing_ok=True)
    if not ok_m:
        log("  [STOP] montagem falhou — nada vai para a fila")
        return None
    _nivelar_audio(output_path, log)
    final = qa_ms.checar_final(output_path, log=log)

    sidecar_data = {
        "titulo": roteiro["titulo"],
        "descricao": roteiro["legenda_insta"],
        "legenda_insta": roteiro["legenda_insta"],
        "legenda_tiktok": roteiro["legenda_tiktok"],
        "hashtags": roteiro["hashtags"],
        "tags": roteiro["hashtags"],
        "pipeline": "ms_v2",
        "tipo": "ms_v2",
        "tipo_video": roteiro["tipo"],
        "pauta": roteiro["pauta"],
        "fala": roteiro["fala_final"],
        "gancho_tela": roteiro["gancho_tela"],
        "estilo": roteiro.get("estilo"),
        "cenas": roteiro.get("cenas", 1),
        "cenario": roteiro.get("cenario"),
        "roteiro_fonte": roteiro["fonte"],
        "foto_usada": roteiro.get("foto"),
        "foto_permalink": roteiro.get("foto_permalink"),
        "prompt_veo": roteiro["prompt_veo"],
        "legendas": info["legendas"],
        "legenda_estilo": info.get("legenda_estilo"),
        "layout": info.get("layout"),
        "legenda_video": info.get("legenda_versao"),  # "legenda_versao" é do texto do Insta (legenda_empresa)
        "legenda_mix": info.get("legenda_mix"),
        "sfx": info.get("sfx", 0),
        "qa_clipe": qa["medidas"],
        "qa_final": final,
        "reprovados_qa": qa_falhas,
        "duracao_s": _dur(output_path),
        "tem_audio_nativo": _tem_audio(output_path),
        "sessao_usada": sessao["session"] if sessao else None,
        "contas_tentadas": contas_usadas,
        "gerado_em": datetime.datetime.now().isoformat(),
        # 04/11 (dona: "nunca mais conteúdo de uma empresa no Insta da outra"): dono do vídeo — trava_empresa.conferir
        # recusa postar em outra empresa
        "_empresa": _empresa_atual(),
    }
    if not final["ok"]:
        destino = DIR_REVISAR / output_path.name
        shutil.move(str(output_path), str(destino))
        sidecar_data["revisar_motivos"] = final["motivos"]
        destino.with_suffix(".json").write_text(json.dumps(sidecar_data, ensure_ascii=False, indent=2), "utf-8")
        log(f"  [STOP] short reprovado na trava final ({'; '.join(final['motivos'])}) → {destino}")
        return None

    output_path.with_suffix(".json").write_text(json.dumps(sidecar_data, ensure_ascii=False, indent=2), "utf-8")
    roteiro_ms.registrar(roteiro, stem)
    log(f"\n  Short aprovado: {output_path} ({sidecar_data['duracao_s']:.1f}s)")
    _limpar_tmp()
    return output_path


def _nivelar_audio(mp4, log=print):
    """Volume no padrão dos outros projetos (−14 LUFS, pico −1,5 dB) pelo master_loudness COMUM. 21/10: o MS Energy
    saía a −12,9 LUFS com pico +0,2 dBFS (estourando); o montar_final do Veo não nivela. Falhou = fica como estava."""
    try:
        sys.path.insert(0, r"D:\hipercool-materiais\comum")
        import master_loudness as ml
        m = ml.measure_pass(mp4, -14, -1.5)
        tmp = Path(mp4).with_name(Path(mp4).stem + "_nivel.mp4")
        ml.apply_pass(mp4, tmp, -14, -1.5, m)
        if tmp.exists() and tmp.stat().st_size > 10_000:
            tmp.replace(mp4)
            log(f"  [AUDIO] nivelado: {m.get('input_i')} → −14 LUFS (pico {m.get('input_tp')} → −1,5)")
    except Exception as e:  # noqa: BLE001
        log(f"  [AUDIO] nivelamento falhou ({type(e).__name__}: {str(e)[:120]}) — vídeo segue como saiu")


def _limpar_tmp():
    for pasta in (DIR_TMP, DIR_PROJETO / "cache" / "tmp_montagem"):
        if pasta.exists():
            shutil.rmtree(pasta, ignore_errors=True)


def _video_real(output_dir):
    """Reel com video real do Google Fotos (video_real_ms.py, sem Veo). None se nao saiu."""
    try:
        import video_real_ms
        return video_real_ms.gerar_short_real(output_dir)
    except Exception as e:  # noqa: BLE001
        print(f"  [VIDEO REAL] falhou: {type(e).__name__}: {str(e)[:200]}")
        return None


def main():
    parser = argparse.ArgumentParser(description="MS Energy — Shorts Veo 3.1")
    parser.add_argument("--output", "-o", default=str(DIR_VIDEOS))
    parser.add_argument("--lote", "-n", type=int, default=1)
    parser.add_argument("--tipo", choices=["com_foto", "criativo", "misto", "video_real"], default="misto",
                        help="com_foto=foto real de instalacao do Instagram, criativo=consultor(a) do Veo, "
                             "video_real=trechos de video real do Google Fotos (sem Veo), misto=alterna")
    args = parser.parse_args()

    # 22/10 (dono "faça"): video real entra no misto — 1o short dos dias pares; e cobre o dia quando o Veo nao tem conta
    dia_real = datetime.date.today().toordinal() % 2 == 0
    for i in range(args.lote):
        if args.tipo == "misto":
            tipo_este = ("video_real" if dia_real else TIPO_COM_FOTO) if i % 2 == 0 else TIPO_CRIATIVO
        else:
            tipo_este = args.tipo
        if args.lote > 1:
            print(f"\n{'=' * 50}")
            print(f"  Short {i + 1}/{args.lote} [{tipo_este.upper()}]")
            print(f"{'=' * 50}")
        if tipo_este == "video_real":
            if _video_real(args.output) or args.tipo == "video_real":
                continue
            tipo_este = TIPO_COM_FOTO  # nao saiu: o dia nao fica sem o short
        r = gerar_short_veo(output_dir=args.output, tipo=tipo_este)
        if r == "SEM_CONTA":
            if _video_real(args.output):
                continue
            sys.exit(6)  # run_loop_ms_energy.bat espera 15 min com rc=6


if __name__ == "__main__":
    main()
