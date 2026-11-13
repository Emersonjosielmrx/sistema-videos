"""01/11 dona: efeitos VISUAIS dos edits parceiros (Noctryxae, Kuroroox, GOJO, Dr1zzy) — lista
D:\\video-fila\\linhas\\VISUAL\\VISUAL_MELHORIAS.md (decupagem da claude-15/78). Entram na MESMA passada final da legenda
(fx_subtitles.burn_subtitles_ass), ANTES do texto (a legenda não treme nem dá zoom), nos momentos que a narração marca:
  # V-01 combo de impacto (flash 2 quadros + zoom 100→122% voltando + shake que decai + RGB split) SÓ no golpe decisivo
  # V-12 micro punch 100→106% em 2 quadros (sem flash/shake/RGB) nas outras palavras pesadas — o V-01 cheio em toda
         palavra pesada cansava (no teste de 60 s eram 9 combos); agora 1 combo a cada >= 20 s, o resto vira micro punch
  # V-02 flash branco de 2 quadros NO LUGAR DO FADE na troca de cena (início de cada frase, no máx. 1 a cada 12 s)
  # V-03 negativo de 2 quadros antes da revelação ("na verdade", "traição", "revelou"...)
  # V-04 jump cut em 3 degraus 100→120→140% no gancho (primeiro 0,4 s)
  # V-05 letterbox que fecha (10% da altura) e abre com flash na tensão (cartão de alerta / "de repente")
  # V-06 speed ramp no despertar: zoom lento (+3% em 1,2 s) que dispara (+18% nos últimos ~0,27 s = 8 quadros a 30 fps)
  # V-07 glow pulsante no poder (despertou, aura, transformou...): só as partes claras do quadro (olhos/aura/magia)
         viram bloom em screen na luminância, pulsando
  # V-08 grade de pretos esmagados + saturação no trecho de tensão
  # V-10 glitch RGB 0,15 s quando o cartão de SISTEMA/status entra (o som vem do fx_detect: glitch_sistema.wav)
  # V-11 brasas/faíscas subindo em modo adição (~40%, 3 s) no despertar e no triunfo — partículas desenhadas aqui mesmo
         (geq), sem arquivo de overlay: vai igual pro Kaggle
  # V-13 ondulação de calor/energia (warp ripple senoidal via displace, 0,40 s) logo depois do impacto V-01 e na aura V-07
  # V-14 dupla exposição (rastro fantasma/silhueta ~30% em memória, morte ou promessa, 1,2 s)
  # V-15 corte mascarado seguindo o golpe (feixe diagonal luminoso atravessando o quadro no sentido da espada/golpe, 0,22 s)
  # V-16 tela dividida na diagonal no confronto (fenda diagonal branca + contraste alto nos lados opostos, 1,2 s)
  # V-17 micro-corte de 4 quadros (0,13 s) para detalhe/olho antes do golpe decisivo (zoom 2,3x na faixa superior + tarjas)
ANIME_FX_VISUAL=0 desliga tudo; cada um tem a sua chave (ANIME_FX_V02=0 etc.)."""
import os
import re

_REVELA = re.compile(r"^(revel\w*|verdade|trai(u|ção|cao|dor\w*)|descobr\w*|identidade|segredo|mentira|enganad\w*|"
                     r"farsa|disfar\w*)[.,!?…]*$", re.I)
_TENSAO = re.compile(r"^(repente|silêncio|silencio|sombra\w*|perigo|ameaça\w*|amea[çc]a|cuidado|espreit\w*|"
                     r"emboscada|cerco|aproxim\w*)[.,!?…]*$", re.I)
_PODER = re.compile(r"^(despert\w*|poder(es|oso|osa)?|aura|energia|transform\w*|brilh\w*|ascend\w*|evolu\w*|"
                    r"liberou|selo|mana|chamas|relâmpago\w*|olhos)[.,!?…]*$", re.I)
# golpe decisivo (V-01 cheio): só verbo de golpe/fim de luta; o resto das palavras pesadas é micro punch (V-12)
_GOLPE = re.compile(r"^(golpe\w*|esmag\w*|explod\w*|explos\w*|destru\w*|aniquil\w*|decapit\w*|massacr\w*|"
                    r"mat(ou|aram)|derrot\w*|venceu)[.,!?…]*$", re.I)
# V-14 + aprendizado edd839f7: lembrança, morte ou promessa -> DUPLA EXPOSIÇÃO (cena anterior fica como
# fantasma/silhueta por cima da nova por ~1,2 s, com leve desfoque e brilho)
_MEMORIA = re.compile(r"^(lembr\w*|recordou|recorda\w*|mem[óo]ria\w*|passado|inf[âa]ncia|antigamente|"
                      r"flashback|morr(eu|eram)|morte|promess\w*|promet\w*|juro|jurou|adeus|despedi\w*)[.,!?…]*$", re.I)
# V-15: golpe cortante / espada -> corte mascarado diagonal seguindo o traço da lâmina
_CORTE_GOLPE = re.compile(r"^(espad\w*|l[âa]mina\w*|cort(ou|e|ando|ada)|fati\w*|rasg\w*|decapit\w*|"
                          r"golpe\w*|ataq\w*|investi\w*)[.,!?…]*$", re.I)
# V-16: confronto / duelo entre rivais -> tela dividida na diagonal com linha branca
_CONFRONTO = re.compile(r"^(confront\w*|duel\w*|contra|versus|frente|encar\w*|rival|rivais|inimig\w*|"
                        r"oponente\w*|batalh\w*)[.,!?…]*$", re.I)


def _liga(chave):
    return os.environ.get(chave, "1") != "0"


def _janelas(ts, larg, gap):
    out = []
    for t in sorted(ts):
        if not out or t - out[-1] >= gap:
            out.append(t)
    return out


def momentos(todas, marcas, pesada=None, dur=None, cenas=None):
    """todas = [(ini, fim, palavra)], marcas = [(t, tipo, rótulo)], cenas = início de cada frase/clipe (trocas de
    cena) -> dict de listas de tempos por efeito."""
    fim = dur or (todas[-1][1] if todas else 0)
    golpe = [float(a) for a, _b, w in todas if _GOLPE.match(w)]
    golpe += [float(t) for t, tp, _r in marcas if tp == "triunfo"]
    pesadas = [float(t) for t, tp, _r in marcas if tp in ("alerta", "legenda_criativa_enfase")]
    if pesada:
        pesadas += [float(a) for a, _b, w in todas if pesada(w)]
    imp = [t for t in _janelas(golpe, 0.5, 20.0) if 1.0 < t < fim - 1]
    micro = [t for t in _janelas(pesadas + golpe, 0.2, 2.5) if 1.0 < t < fim - 1 and all(abs(t - i) > 1.0 for i in imp)]
    rev = [float(a) for a, _b, w in todas if _REVELA.match(w)]
    ten = [float(t) for t, tp, _r in marcas if tp == "alerta"] + [float(a) for a, _b, w in todas if _TENSAO.match(w)]
    pod = [float(a) for a, _b, w in todas if _PODER.match(w)]
    sist = [float(t) for t, tp, _r in marcas if tp == "sistema"]
    brasa = pod + [float(t) for t, tp, _r in marcas if tp == "triunfo"]
    poder = [t for t in _janelas(pod, 1.6, 30.0) if 1.5 < t < fim - 2]
    ocupado = imp + micro + rev + poder
    trocas = [t for t in _janelas([float(c) for c in (cenas or [])], 0.1, 12.0)
              if 2.0 < t < fim - 1 and all(abs(t - o) > 1.5 for o in ocupado)]
    # V-13: ondulação de calor/energia logo após o impacto V-01 (+0,12 s) e junto do despertar/aura V-07
    ondula = _janelas([t + 0.12 for t in imp] + poder, 0.45, 18.0)
    # V-15: corte mascarado diagonal seguindo o golpe
    corte_g = [float(a) for a, _b, w in todas if _CORTE_GOLPE.match(w)]
    slash = [t for t in _janelas(corte_g, 0.25, 22.0) if 1.0 < t < fim - 1]
    # V-16: tela dividida na diagonal no confronto
    conf = [float(a) for a, _b, w in todas if _CONFRONTO.match(w)]
    confronto = [t for t in _janelas(conf, 1.2, 35.0) if 1.5 < t < fim - 2]
    # V-17: micro-corte de 4 quadros (0,13 s) para detalhe (olho) logo antes do golpe decisivo (t - 0,15 s)
    olho = [round(t - 0.15, 2) for t in imp if t > 1.5]
    return {"poder": poder[:60],
            "impacto": imp[:200],
            "micro": micro[:600],
            "revela": [t for t in _janelas(rev, 0.1, 25.0) if 1.0 < t < fim - 1][:80],
            "tensao": [t for t in _janelas(ten, 2.0, 40.0) if 2.0 < t < fim - 3][:60],
            "sistema": [t for t in _janelas(sist, 0.2, 5.0) if 0.5 < t < fim - 1][:80],
            "brasa": [t for t in _janelas(brasa, 3.0, 45.0) if 1.0 < t < fim - 3.5][:40],
            "memoria": [t for t in _janelas([float(a) for a, _b, w in todas if _MEMORIA.match(w)], 1.2, 30.0)
                        if 1.0 < t < fim - 2][:40],
            "ondula": [t for t in ondula if 1.0 < t < fim - 1][:60],
            "slash": slash[:60],
            "confronto": confronto[:40],
            "olho": olho[:60],
            "troca": trocas[:400]}


def recortar(m, ini, fim, folga=3.0):
    """02/11: só os momentos dentro de [ini-folga, fim+folga]. Num longo de 1 h o filtro com TODOS os efeitos passava
    de 190 mil caracteres (o scale eval=frame reavalia tudo a cada quadro): no PC deu "Cannot allocate memory" e a
    passada caiu pra sem efeitos. Cada fatia da legenda (fx_subtitles._queima_em_fatias) e cada bloco usa só os seus."""
    return {k: [t for t in v if ini - folga <= t <= fim + folga] for k, v in m.items()}


def _soma(termos, padrao="0"):
    return "+".join(termos) if termos else padrao


def _en(ts, d, antes=0.0):
    return "+".join(f"between(t,{t - antes:.2f},{t + d:.2f})" for t in ts)


def filtro(m, W, H):
    """Cadeia ffmpeg (sem rótulos de entrada/saída) aplicada no quadro já em W x H. '' = nada a fazer."""
    if not _liga("ANIME_FX_VISUAL") or not m:
        return ""
    imp, rev, ten = m.get("impacto", []), m.get("revela", []), m.get("tensao", [])
    micro = m.get("micro", []) if _liga("ANIME_FX_V12") else []
    pod = m.get("poder", [])
    partes = []
    # zoom: V-01 punch (sobe em 0,07 s, volta em 0,2 s) + V-12 micro punch (sobe em 0,07 s, volta em 0,13 s) + V-04
    # degraus no gancho + V-06 rampa (lenta 1,2 s e dispara nos últimos 0,27 s, volta em 0,25 s)
    z = [f"0.22*between(t,{t:.2f},{t + 0.27:.2f})*if(lt(t-{t:.2f},0.07),(t-{t:.2f})/0.07,1-(t-{t + 0.07:.2f})/0.2)"
         for t in imp]
    z += [f"0.06*between(t,{t:.2f},{t + 0.20:.2f})*if(lt(t-{t:.2f},0.07),(t-{t:.2f})/0.07,1-(t-{t + 0.07:.2f})/0.13)"
          for t in micro]
    if _liga("ANIME_FX_V06"):
        for t in pod:
            a = t - 1.47  # a rampa termina no instante da palavra de poder
            z.append(f"between(t,{a:.2f},{t:.2f})*if(lt(t,{t - 0.27:.2f}),0.03*(t-{a:.2f})/1.2,"
                     f"0.03+0.18*(t-{t - 0.27:.2f})/0.27)"
                     f"+between(t,{t:.2f},{t + 0.25:.2f})*0.21*(1-(t-{t:.2f})/0.25)")
    z.append("0.2*between(t,0.13,0.27)+0.4*between(t,0.27,0.40)")  # V-04
    # V-17 micro-corte de 4 quadros (0,13 s) para detalhe (olho) antes do golpe decisivo: zoom rápido (1,38x) focado
    # na faixa central/olhos com tarjas dramáticas, voltando seco no instante do golpe
    olho = m.get("olho", []) if _liga("ANIME_FX_V17") else []
    for t in olho:
        z.append(f"0.38*between(t,{t:.2f},{t + 0.13:.2f})")
    zexp = "1+" + _soma(z)
    sx = _soma([f"14*sin((t-{t:.2f})*60)*exp(-(t-{t:.2f})*9)*between(t,{t:.2f},{t + 0.4:.2f})" for t in imp])
    sy_terms = [f"10*cos((t-{t:.2f})*47)*exp(-(t-{t:.2f})*9)*between(t,{t:.2f},{t + 0.4:.2f})" for t in imp]
    for t in olho:
        sy_terms.append(f"(-0.02*{H})*between(t,{t:.2f},{t + 0.13:.2f})")
    sy = _soma(sy_terms)
    partes.append(f"scale=w='trunc({W}*({zexp})/2)*2':h='trunc({H}*({zexp})/2)*2':eval=frame:flags=bicubic")
    partes.append(f"crop={W}:{H}:x='(iw-{W})/2+({sx})':y='clip((ih-{H})/2+({sy}),0,ih-{H})'")
    # V-01 RGB split nos 0,15 s do impacto + V-10 glitch na entrada do cartão de sistema
    rgb = list(imp) + (m.get("sistema", []) if _liga("ANIME_FX_V10") else [])
    if rgb:
        partes.append(f"rgbashift=rh=6:bh=-6:rv=2:bv=-2:enable='{_en(rgb, 0.15)}'")
    # V-08 grade esmagada nos 2,5 s de tensão
    if ten:
        partes.append(f"eq=contrast=1.35:saturation=1.3:brightness=-0.03:enable='{_en(ten, 2.5)}'")
    # V-07 glow: cópia só com os claros (contraste alto puxado pra baixo) + blur, somada em screen SÓ na luminância,
    # pulsando ~1,7 Hz; enable = fora da janela não custa o blur. Testado 01/11 (cor média do quadro):
    #  - screen em todos os planos = quadro roxo; - o rgbashift (V-01/V-10) deixa o quadro em RGB planar, então c0 era o
    #    VERDE (quadro verde) -> format=yuv420p antes; - c1/c2 "normal" com opacity 0 = cor da 2ª entrada (cinza):
    #    opacity 1 mantém a cor da cena
    if pod and _liga("ANIME_FX_V07"):
        en = _en(pod, 1.6)
        partes.append(f"format=yuv420p,split=2[fxa][fxb];[fxb]eq=contrast=3.0:brightness='-0.55+0.10*sin(t*11)':saturation=1.6:"
                      f"eval=frame:enable='{en}',gblur=sigma=16:enable='{en}'[fxg];"
                      f"[fxa][fxg]blend=c0_mode=screen:c0_opacity=0.6:c1_mode=normal:c2_mode=normal:c1_opacity=1:c2_opacity=1:enable='{en}'")
    # V-11 brasas: pontos laranja subindo (sementes fixas por coluna) somados na luminância/cor em ~40%, 3 s
    brasa = m.get("brasa", []) if _liga("ANIME_FX_V11") else []
    if brasa:
        en = _en(brasa, 3.0)
        # cada pixel acende se cair numa "brasa": grade de 22 px com fase pseudo-aleatória por coluna, subindo 260 px/s
        # (1º teste: pontos de 3 px a cada 5 células = invisível no 1080p; agora 7 px, ~1 a cada 4 células, com halo)
        cel = max(24, int(min(W, H) / 30))
        lum = (f"if(lt(mod(X+37*floor((Y+260*T)/{cel}),{cel * 4}),7)*lt(mod(Y+260*T+19*floor(X/{cel}),{cel * 2}),7)"
               f",255,0)")
        # soma SÓ na luminância (c0), mesma regra do V-07: faíscas claras sobre a cena, cor da cena intacta
        partes.append(f"format=yuv420p,split=2[fxc][fxd];[fxd]geq=lum='{lum}':cb=128:cr=128:enable='{en}',"
                      f"gblur=sigma=4:enable='{en}'[fxe];"
                      f"[fxc][fxe]blend=c0_mode=addition:c0_opacity=0.9:c1_mode=normal:c2_mode=normal:c1_opacity=1:c2_opacity=1:enable='{en}'")
    # V-14 + aprendizado edd839f7: dupla exposição de memória/morte/promessa — mistura dos últimos ~0,6 s (rastro
    # fantasma/silhueta a ~30% sobre o quadro atual) + leve desfoque e brilho, por 1,2 s
    mem = m.get("memoria", []) if (_liga("ANIME_FX_MEMORIA") and _liga("ANIME_FX_V14")) else []
    if mem:
        en = _en(mem, 1.2)
        partes.append(f"tmix=frames=18:weights='1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 6':enable='{en}',"
                      f"gblur=sigma=1.5:enable='{en}',eq=brightness=0.05:saturation=0.85:enable='{en}'")
    # V-13 ondulação de calor/energia (warp ripple sutil): mapa de deslocamento senoidal animado (displace) por 0,40 s
    ond = m.get("ondula", []) if _liga("ANIME_FX_V13") else []
    if ond:
        en = _en(ond, 0.40)
        partes.append(f"format=yuv420p,split=3[fxw0][fxwx][fxwy];"
                      f"[fxwx]geq=lum='128+6*sin(Y/22+T*26)*cos(X/30-T*18)':cb=128:cr=128:enable='{en}'[fxmx];"
                      f"[fxwy]geq=lum='128+6*cos(X/22+T*22)*sin(Y/30+T*20)':cb=128:cr=128:enable='{en}'[fxmy];"
                      f"[fxw0][fxmx][fxmy]displace=edge=smear:enable='{en}'")
    # V-15 corte mascarado seguindo o golpe (slash wipe diagonal luminoso atravessando a tela em 0,22 s)
    sl = m.get("slash", []) if _liga("ANIME_FX_V15") else []
    if sl:
        en = _en(sl, 0.22)
        prog = "+".join(f"between(T,{t:.2f},{t + 0.22:.2f})*((T-{t:.2f})/0.22)" for t in sl)
        faixa = f"abs((X/{W}+Y/{H})*0.5-({prog}))"
        lum_s = f"if(lt({faixa},0.045),255,if(lt({faixa},0.11),150,0))"
        partes.append(f"format=yuv420p,split=2[fxs0][fxs1];"
                      f"[fxs1]geq=lum='{lum_s}':cb=128:cr=128:enable='{en}',gblur=sigma=5:enable='{en}'[fxs2];"
                      f"[fxs0][fxs2]blend=c0_mode=screen:c0_opacity=0.85:c1_mode=normal:c2_mode=normal:"
                      f"c1_opacity=1:c2_opacity=1:enable='{en}'")
    # V-16 tela dividida na diagonal no confronto (linha diagonal branca central + contraste nos lados opostos, 1,2 s)
    cf = m.get("confronto", []) if _liga("ANIME_FX_V16") else []
    if cf:
        en = _en(cf, 1.2)
        diag = f"abs(X/{W}+Y/{H}-1.0)"
        lum_c = f"if(lt({diag},0.014),255,0)"
        partes.append(f"format=yuv420p,split=2[fxcf0][fxcf1];"
                      f"[fxcf1]geq=lum='{lum_c}':cb=128:cr=128:enable='{en}'[fxcf2];"
                      f"[fxcf0][fxcf2]blend=c0_mode=screen:c0_opacity=0.95:c1_mode=normal:c2_mode=normal:"
                      f"c1_opacity=1:c2_opacity=1:enable='{en}',"
                      f"eq=contrast=1.22:saturation=1.20:enable='{en}'")
    # V-17 tarjas de foco no olho (fecha em cima e embaixo durante os 4 quadros do close antes do golpe)
    if olho:
        en_o = _en(olho, 0.13)
        partes.append(f"drawbox=x=0:y=0:w=iw:h={int(H * 0.18)}:color=black:t=fill:enable='{en_o}'")
        partes.append(f"drawbox=x=0:y={H - int(H * 0.18)}:w=iw:h={int(H * 0.18)}:color=black:t=fill:enable='{en_o}'")
    # V-03 negativo de 2 quadros logo antes da revelação
    # ("negate=enable": com "negate:enable" o ffmpeg 8 não acha a opção e a passada da legenda inteira falha)
    if rev:
        partes.append(f"negate=enable='{_en(rev, -0.01, antes=0.08)}'")
    # V-05 letterbox: barra fixa 10% ligada só na janela (o drawbox não recalcula a altura por quadro)
    if ten:
        en = _en(ten, 2.1)
        partes.append(f"drawbox=x=0:y=0:w=iw:h={int(H * 0.10)}:color=black:t=fill:enable='{en}'")
        partes.append(f"drawbox=x=0:y={H - int(H * 0.10)}:w=iw:h={int(H * 0.10)}:color=black:t=fill:enable='{en}'")
    # flash branco de 2 quadros: V-01 no impacto, V-05 quando o letterbox abre, V-04 entre os degraus do gancho,
    # V-02 na troca de cena (no lugar do fade)
    fl = imp + [t + 2.1 for t in ten] + [0.13, 0.27] + (m.get("troca", []) if _liga("ANIME_FX_V02") else [])
    partes.append(f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.85:t=fill:enable='{_en(fl, 0.06)}'")
    return ",".join(partes)
