# -*- coding: utf-8 -*-
"""formatos_voz.py — TESTE de formatos com várias vozes no mesmo Short (dono 23/10/2026, ver
D:\\video-fila\\IDEIAS_FORMATOS_COM_VOZES.md): duplas, transmissão do Galvão, Show do Milhão, jornal, escolinha...

  python formatos_voz.py testar <formato> <historia.txt> [nome]   roteiro (IA) + vozes + microcortes -> amostra
  python formatos_voz.py lista                                       formatos disponíveis

1) roteiro: a IA do recapd (claude_client, venv do recapd) reescreve a história como DIÁLOGO, em JSON
   [{"voz": ..., "fala": ..., "estilo": normal|grito|pergunta|calmo}], com os bordões de cada voz (linguagem_v2.json).
2) vozes: cada fala na voz de quem fala — base Kokoro (homem) ou Francisca (mulher/criança) -> RVC (voz_clonada.converter)
   com entonação por estilo (APPLIO_F0_ESCALA / APPLIO_F0_FINAL_ST).
3) microcortes (narracao_curva, comum): pausa > 0,07 s sai; a fala não acelera.
Saída: amostras_voz\\formatos\\<formato>_<nome>.mp3 + _roteiro.txt. Nada aqui mexe na produção.
"""
import asyncio
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais")
VOZES = RAIZ / "models" / "rvc" / "vozes"
OUT = RAIZ / "amostras_voz" / "formatos"
TMP = RAIZ / "python" / "tmp" / "formatos"
VENV_RECAPD = Path(r"D:\recapd-ambientes\producao\venv\Scripts\python.exe")
RECAPD_BIN = Path(r"D:\recapd-ambientes\producao\bin")
FRANCISCA = "pt-BR-FranciscaNeural"

# voz: (base, semitons do personagem) — o que foi aprovado nas amostras de 22-23/10
VOZ = {"galvao_bueno": ("K", 1), "professor_girafales": ("K", 0), "silvio_santos": ("K", 3), "cid_moreira": ("F", -3),
       "faustao": ("K", 0), "chaves_chapolin": ("K", 4), "quico": ("K", 0), "chiquinha": ("F", 0), "seu_madruga": ("K", 0),
       "joao_grilo": ("K", 2), "chico_selton": ("K", 1), "gru_hassum": ("K", 0), "pato_donald": ("K", 0), "goku": ("K", 1), "vegeta": ("K", 0), "wolverine_bardavid": ("K", 0)}
ESTILO = {"normal": (1.5, 0.0, 1.03, 0), "grito": (1.85, 0.0, 1.08, 1), "pergunta": (1.6, 2.0, 1.03, 0),
          "calmo": (1.2, -1.5, 0.97, 0)}  # (faixa de entonação, fim de frase st, velocidade Kokoro, semitons a mais)

REGRAS = """Escreva em português do Brasil, falado, para um Short de 40 a 60 segundos (110 a 160 palavras no total).
Conte os FATOS da história abaixo (pode cortar detalhe), do começo ao fim, com gancho no início.
Cada fala tem no máximo 22 palavras. Bordão: NO MÁXIMO 2 por personagem no vídeo inteiro, e só quando a situação
pede (um bordão colado sem sentido estraga a piada). O jeito de falar do personagem vale mais que o bordão.
Sem palavrão pesado, sem política, sem pedir like/inscrição, sem citar emissora, marca ou pessoa real.
Responda SÓ um JSON: [{"voz": "<uma das vozes do elenco>", "fala": "...", "estilo": "normal|grito|pergunta|calmo"}]"""

FORMATOS = {
    "transmissao": ("Transmissão esportiva", ["galvao_bueno", "professor_girafales"],
                    "Galvão Bueno narra a história como se fosse um JOGO ao vivo (lance a lance, empolgação crescendo, "
                    "'olha o que ele fez!', 'haja coração!'); o Professor Girafales é o comentarista que dá a opinião "
                    "técnica entre os lances e o Galvão chama ele de 'Professor'."),
    "show_do_milhao": ("Show do Milhão", ["silvio_santos"],
                       "Silvio Santos apresenta a história como no programa dele ('Ma oê!', 'Está certo disso?') e PARA no "
                       "gancho com uma pergunta ao público de casa: o que vai acontecer? Termina dizendo que a resposta vem "
                       "no próximo vídeo."),
    "jornal": ("Jornal", ["cid_moreira", "faustao"],
               "Cid Moreira apresenta como telejornal, sério, abre com 'Boa noite.'; chama um repórter 'ao vivo' (o "
               "Faustão, empolgado e exagerado) que conta a parte mais louca; o Cid fecha com 'Boa noite.'."),
    "videocassetadas": ("Videocassetadas", ["faustao"],
                        "Faustão comenta a história como nas Videocassetadas, zoando cada falha do vilão ou dos "
                        "personagens com 'Errou!', 'Ô loco, meu!', 'Essa fera aí, meu!'."),
    "escolinha": ("Escolinha", ["professor_girafales", "chaves_chapolin", "quico", "chiquinha"],
                  "O Professor Girafales dá uma AULA sobre a história e faz perguntas; Chaves responde errado e "
                  "engraçado, Quico se gaba e chama os outros de gentalha, Chiquinha faz 'pois é, pois é, pois é'. "
                  "O professor perde a paciência ('Silêncio!') e explica o certo."),
    "tribunal": ("Tribunal", ["professor_girafales", "joao_grilo", "chico_selton"],
                 "Um julgamento sobre a história: o Professor Girafales é o juiz, João Grilo é o advogado esperto que "
                 "defende o protagonista, Chicó é a testemunha que exagera tudo ('Não sei, só sei que foi assim'). "
                 "Falar de sertanejo nos dois (cabra, home, oxe, num, vixe, arretado)."),
    "joao_chico": ("João Grilo e Chicó", ["joao_grilo", "chico_selton"],
                   "Chicó conta a história exagerando e mentindo, João Grilo desmascara. Falar de sertanejo de verdade "
                   "(cabra, home, oxe, num, abestado, vixe, arretado, pisa), nada de português correto demais. "
                   "Chicó fecha com 'Não sei, só sei que foi assim.'."),
    "chaves_quico": ("Chaves e Quico", ["chaves_chapolin", "quico"],
                     "Chaves conta a história do jeito dele (confuso, 'foi sem querer querendo', 'isso, isso, isso!'), "
                     "Quico interrompe se gabando ('o meu é melhor'), chama de gentalha e chora pra mamãe."),
    "chaves_chiquinha": ("Chaves e Chiquinha", ["chaves_chapolin", "chiquinha"],
                         "Chaves e Chiquinha contam a história juntos; Chiquinha se faz de esperta e chora fingido "
                         "pra conseguir as coisas, 'pois é, pois é, pois é'; Chaves 'ninguém tem paciência comigo'."),
    "trio_chaves": ("Trio Chaves, Quico e Chiquinha", ["chaves_chapolin", "quico", "chiquinha"],
                    "Os três contam a história discutindo entre si como na vila: Quico se gaba, Chiquinha provoca, Chaves "
                    "se confunde. Termina numa briguinha engraçada."),
    "madruga_chaves": ("Seu Madruga e Chaves", ["seu_madruga", "chaves_chapolin"],
                       "Seu Madruga tenta contar a história e o Chaves fica atrapalhando; Seu Madruga perde a paciência."),
    "fofoca": ("Fofoca", ["chiquinha", "quico"],
               "Chiquinha e Quico contam a história como FOFOCA da vila, baixinho, 'você não sabe da maior!', "
               "exagerando e se escandalizando."),
    "batalha": ("Batalha de narradores", ["cid_moreira", "faustao", "silvio_santos"],
                "Silvio abre explicando a batalha; Cid Moreira conta a primeira metade (sério), Faustão conta a segunda "
                "(zoeira); Silvio fecha pedindo pro público votar nos comentários: Cid ou Faustão?"),
    "cameo_interrupcao": ("Narrador + participação especial + interrupção", ["chico_selton", "pato_donald", "galvao_bueno", "cid_moreira"],
                          "Chicó narra sozinho; no meio, quando o vilão trapaceia, o Pato Donald interrompe furioso "
                          "('Ei! Ei! Isso não é justo!'); no clímax entra o Galvão com UMA frase só; e o vídeo fecha com o "
                          "Cid dizendo só 'Boa noite.' (encerramento assinado)."),
}


# Fonte única (dono 23/10): a produção (recapd config/formatos_voz.json) manda nas regras, vozes, estilos e formatos.
CONFIG = Path("D:/recapd-ambientes/producao/config/formatos_voz.json")
if CONFIG.exists():
    _c = json.loads(CONFIG.read_text(encoding="utf-8"))
    REGRAS = _c["regras"]
    VOZ = {v: (x["base"], x["st"]) for v, x in _c["vozes"].items()}
    ESTILO = {k: (x["f0_escala"], x["final_st"], x["velocidade"], x["st"]) for k, x in _c["estilos"].items()}
    FORMATOS = {k: (x["nome"], x["elenco"], x["como"]) for k, x in _c["formatos"].items()}


def _bordoes(voz):
    try:
        g = json.loads((VOZES / voz / "linguagem_v2.json").read_text(encoding="utf-8"))
        b = g.get("bordoes_iconicos") or g.get("bordoes") or []
        fora = {x.lower() for x in g.get("bordoes_estranhos") or []}
        return [x for x in b if x.lower() not in fora][:5]
    except (OSError, ValueError):
        return []


def roteiro(formato, historia):
    nome, elenco, como = FORMATOS[formato]
    vozes = "\n".join(f"- {v}" + (f" (bordões: {'; '.join(_bordoes(v))})" if _bordoes(v) else "") for v in elenco)
    prompt = f"FORMATO: {nome}\n{como}\n\nELENCO (use exatamente estes nomes em \"voz\"):\n{vozes}\n\n{REGRAS}\n\nHISTÓRIA:\n{historia}"
    cod = ("import sys, json; sys.path.insert(0, r'%s'); import claude_client; "
           "print(claude_client.generate_text(sys.stdin.read(), max_tokens=2500, temperature=0.7, timeout=240))") % RECAPD_BIN
    r = subprocess.run([str(VENV_RECAPD), "-c", cod], input=prompt, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300, env=dict(os.environ, PYTHONUTF8="1"))
    m = re.search(r"\[.*\]", r.stdout or "", re.S)
    if not m:
        raise RuntimeError(f"a IA não devolveu o roteiro: {(r.stdout or r.stderr)[-300:]}")
    falas = [f for f in json.loads(m.group(0)) if f.get("voz") in elenco and f.get("fala", "").strip()]
    if not falas:
        raise RuntimeError("roteiro vazio")
    return falas


def _f0_base(motor, cache={}):
    if motor not in cache:
        sys.path.insert(0, str(RAIZ / "bin"))
        import voz_clonada as vc
        nome = "2_edge_francisca" if motor == "F" else "1_kokoro"
        cache[motor] = vc.tom_medio(vc.AMOSTRAS / "_bases" / f"{nome}.wav")
    return cache[motor]


def _base(motor, texto, vel, rate, destino):
    sys.path.insert(0, str(RAIZ / "bin"))
    import voz_clonada as vc
    if motor == "K":
        vc._base_tts("kokoro:pm_alex", texto, destino, vel)
        return
    import edge_tts
    mp3 = destino.with_suffix(".mp3")
    for t in range(3):
        try:
            asyncio.run(edge_tts.Communicate(texto, FRANCISCA, rate=f"{rate:+d}%").save(str(mp3)))
            break
        except Exception:  # noqa: BLE001
            if t == 2:
                raise
            time.sleep(3)
    vc._rodar([vc.FFMPEG, "-v", "error", "-y", "-i", mp3, destino])
    mp3.unlink()


def render(formato, falas, nome):
    sys.path.insert(0, str(RAIZ / "bin"))
    sys.path.insert(0, str(RECAPD_BIN))
    import voz_clonada as vc
    import narracao_curva
    import librosa
    import numpy as np
    import soundfile as sf
    pasta = TMP / f"{formato}_{nome}"
    pasta.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    blocos, linhas = [], []
    for i, f in enumerate(falas):
        voz = f["voz"]
        motor, st = VOZ.get(voz, ("K", 0))
        esc, fim, vel, st_e = ESTILO.get(f.get("estilo", "normal"), ESTILO["normal"])
        alvo = float((VOZES / voz / "f0.txt").read_text().strip())
        tom = max(-24, min(24, round(12 * math.log2(alvo / _f0_base(motor))) + st + st_e))
        b, s = pasta / f"{i:02d}_base.wav", pasta / f"{i:02d}_voz.wav"
        _base(motor, f["fala"], vel, int(round((vel - 1) * 100)), b)
        os.environ["APPLIO_F0_ESCALA"] = str(esc)
        os.environ["APPLIO_F0_FINAL_ST"] = str(fim)
        vc.converter(voz, b, s, tom, index_rate=0.7)
        y, _sr = librosa.load(str(s), sr=44100, mono=True)
        y, _ = librosa.effects.trim(y, top_db=40)
        blocos += [y, np.zeros(int(0.3 * 44100), dtype=np.float32)]
        linhas.append(f"{voz.upper()} ({f.get('estilo', 'normal')}): {f['fala']}")
        print(f"[{formato} {i + 1}/{len(falas)}] {voz} tom {tom:+d}", flush=True)
    bruto = pasta / "_bruto.wav"
    sf.write(str(bruto), np.concatenate(blocos), 44100, subtype="PCM_16")
    narracao_curva.microcortes(bruto)
    mp3 = OUT / f"{formato}_{nome}.mp3"
    vc._rodar([vc.FFMPEG, "-v", "error", "-y", "-i", bruto, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ac", "1",
               "-codec:a", "libmp3lame", "-b:a", "192k", mp3])
    (OUT / f"{formato}_{nome}_roteiro.txt").write_text(f"{FORMATOS[formato][0]}\n\n" + "\n".join(linhas) + "\n",
                                                        encoding="utf-8")
    for p in pasta.glob("*.wav"):
        p.unlink()
    return mp3


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2 or sys.argv[1] == "lista":
        for k, (n, e, _c) in FORMATOS.items():
            print(f"{k:20s} {n}  ({', '.join(e)})")
        sys.exit(0)
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)  # produção tem a vez
    _cmd, formato, arq = sys.argv[1:4]
    nome = sys.argv[4] if len(sys.argv) > 4 else time.strftime("%Y%m%d_%H%M")
    t0 = time.time()
    falas = roteiro(formato, Path(arq).read_text(encoding="utf-8"))
    print(f"roteiro {formato}: {len(falas)} falas", flush=True)
    mp3 = render(formato, falas, nome)
    print(f"{formato}: PRONTO {mp3} ({time.time() - t0:.0f} s)", flush=True)
