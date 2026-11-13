// Kit de câmera e efeitos PRONTOS e testados (26/10, dono: "não tem zooms de câmera nem coisas mais elaboradas").
// O editor monta as cenas com estas peças em vez de reinventar: o movimento sai garantido (> 4% medido).
// Uso: import {FotoViva, Parallax, Camera, Entrar, Flutuar, Pulsar, Tremor, Mergulho, Flash, Particulas,
//        Surgir, Curvas} from '../../lib/efeitos';
// `dur` = duração da cena em quadros (dentro de um <Sequence>, o quadro 0 é o começo da cena).
// (02/11) também: TextoQueCabe (tamanho de fonte calculado pra caber) e BorraoMovimento (motion blur de câmera).
import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, random, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {fitText} from '@remotion/layout-utils';
import {CameraMotionBlur} from '@remotion/motion-blur';

const trava = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

type Filhos = {children?: React.ReactNode};

/** Câmera viva: push-in/pull-out + pan contínuo em `dur` quadros. Envolve qualquer coisa. */
export const Camera: React.FC<Filhos & {dur: number; de?: number; ate?: number; panX?: number; panY?: number}> = (
  {dur, de = 1.0, ate = 1.18, panX = 0, panY = 0, children}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, dur], [0, 1], {...trava, easing: Easing.inOut(Easing.cubic)});
  const s = de + (ate - de) * p;
  return (
    <AbsoluteFill style={{transform: `translate(${panX * p}px, ${panY * p}px) scale(${s})`, transformOrigin: 'center'}}>
      {children}
    </AbsoluteFill>
  );
};

/** Foto em tela cheia com câmera viva. desfoque é limitado a 8 px e escurecer a 0.6 (senão o zoom some). */
export const FotoViva: React.FC<{src: string; dur: number; de?: number; ate?: number; panX?: number; panY?: number;
  escurecer?: number; desfoque?: number}> = ({src, dur, de, ate, panX, panY, escurecer = 0, desfoque = 0}) => (
  <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
    <Camera dur={dur} de={de} ate={ate} panX={panX} panY={panY}>
      <Img src={src} style={{width: '100%', height: '100%', objectFit: 'cover',
        filter: desfoque ? `blur(${Math.min(desfoque, 8)}px)` : undefined}} />
    </Camera>
    {escurecer > 0 && <AbsoluteFill style={{background: `rgba(0,0,0,${Math.min(escurecer, 0.6)})`}} />}
  </AbsoluteFill>
);

/** Profundidade: o fundo anda para um lado e a pessoa recortada (PNG sem fundo) para o outro. */
export const Parallax: React.FC<{fundo: string; frente: string; dur: number; alturaFrente?: number;
  lado?: 'esq' | 'dir' | 'centro'; escurecerFundo?: number}> = (
  {fundo, frente, dur, alturaFrente = 1250, lado = 'centro', escurecerFundo = 0.35}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, dur], [0, 1], {...trava, easing: Easing.inOut(Easing.cubic)});
  const pos = lado === 'esq' ? {left: -40} : lado === 'dir' ? {right: -40} : {left: '50%', marginLeft: -alturaFrente * 0.32};
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <FotoViva src={fundo} dur={dur} ate={1.14} panX={-50} desfoque={5} escurecer={escurecerFundo} />
      <Img src={frente} style={{position: 'absolute', bottom: 0, height: alturaFrente, ...pos,
        transform: `translateX(${40 * p}px) scale(${1 + 0.06 * p})`, transformOrigin: 'bottom center',
        filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.55))'}} />
    </AbsoluteFill>
  );
};

/** Tremor leve (tensão, impacto). forca em px. */
export const Tremor: React.FC<Filhos & {forca?: number; de?: number; ate?: number}> = (
  {forca = 6, de = 0, ate = 99999, children}) => {
  const f = useCurrentFrame();
  const ligado = f >= de && f <= ate;
  const x = ligado ? (random(`x${f}`) - 0.5) * 2 * forca : 0;
  const y = ligado ? (random(`y${f}`) - 0.5) * 2 * forca : 0;
  return <AbsoluteFill style={{transform: `translate(${x}px, ${y}px)`}}>{children}</AbsoluteFill>;
};

/** Flutuar (y ± amp px) — cards e textos que ficam na tela não ficam parados. */
export const Flutuar: React.FC<Filhos & {amp?: number; periodo?: number; atraso?: number}> = (
  {amp = 8, periodo = 70, atraso = 0, children}) => {
  const f = useCurrentFrame();
  return <div style={{transform: `translateY(${Math.sin(((f + atraso) / periodo) * Math.PI * 2) * amp}px)`}}>{children}</div>;
};

/** Pulsar (scale 1 ↔ 1+forca) — botão do cartão final, selo. */
export const Pulsar: React.FC<Filhos & {forca?: number; periodo?: number}> = ({forca = 0.06, periodo = 36, children}) => {
  const f = useCurrentFrame();
  const s = 1 + forca * (0.5 + 0.5 * Math.sin((f / periodo) * Math.PI * 2));
  return <div style={{transform: `scale(${s})`, display: 'inline-block'}}>{children}</div>;
};

/** Entrada com mola no quadro `em` (relativo à cena). */
export const Entrar: React.FC<Filhos & {em?: number; de?: 'baixo' | 'cima' | 'esq' | 'dir' | 'escala'; distancia?: number}> = (
  {em = 0, de = 'baixo', distancia = 140, children}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f - em, fps, config: {damping: 14, stiffness: 140}});
  const d = (1 - s) * distancia;
  const t = de === 'baixo' ? `translateY(${d}px)` : de === 'cima' ? `translateY(${-d}px)`
    : de === 'esq' ? `translateX(${-d}px)` : de === 'dir' ? `translateX(${d}px)` : `scale(${0.4 + 0.6 * s})`;
  return <div style={{transform: t, opacity: interpolate(f - em, [0, 6], [0, 1], trava)}}>{children}</div>;
};

/** Mergulho (zoom-through): nos últimos `n` quadros da cena a câmera mergulha e some — transição para a próxima. */
export const Mergulho: React.FC<Filhos & {dur: number; n?: number}> = ({dur, n = 12, children}) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [dur - n, dur], [1, 3.2], {...trava, easing: Easing.in(Easing.cubic)});
  const o = interpolate(f, [dur - n * 0.5, dur], [1, 0], trava);
  return <AbsoluteFill style={{transform: `scale(${s})`, opacity: o}}>{children}</AbsoluteFill>;
};

/** Flash branco de `n` quadros a partir do quadro `em` (virada, revelação). */
export const Flash: React.FC<{em: number; n?: number; cor?: string}> = ({em, n = 4, cor = '#fff'}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [em, em + 1, em + n], [0, 0.9, 0], trava);
  return <AbsoluteFill style={{background: cor, opacity: o, pointerEvents: 'none'}} />;
};

// ── Curvas do GSAP (28/10) ── o GSAP não roda no Remotion (ele manda no tempo, o Remotion manda no quadro); as
// curvas dele, sim. Uso: interpolate(f, [0, 20], [0, 1], {...trava, easing: Curvas.power4Out}).
const _out = (fn: (t: number) => number) => (t: number) => 1 - fn(1 - t);
const _inOut = (fn: (t: number) => number) => (t: number) => (t < 0.5 ? fn(t * 2) / 2 : 1 - fn((1 - t) * 2) / 2);
const _pow = (n: number) => (t: number) => Math.pow(t, n);
const _expo = (t: number) => (t === 0 ? 0 : Math.pow(2, 10 * (t - 1)));
const _circ = (t: number) => 1 - Math.sqrt(1 - t * t);
const _back = (s: number) => (t: number) => t * t * ((s + 1) * t - s);
const _elasticOut = (amp = 1, per = 0.3) => (t: number) => {
  if (t === 0 || t === 1) return t;
  const a = Math.max(1, amp);
  const s = (per / (2 * Math.PI)) * Math.asin(1 / a);
  return a * Math.pow(2, -10 * t) * Math.sin(((t - s) * (2 * Math.PI)) / per) + 1;
};
const _bounceOut = (t: number) => {
  const n = 7.5625, d = 2.75;
  if (t < 1 / d) return n * t * t;
  if (t < 2 / d) return n * (t -= 1.5 / d) * t + 0.75;
  if (t < 2.5 / d) return n * (t -= 2.25 / d) * t + 0.9375;
  return n * (t -= 2.625 / d) * t + 0.984375;
};
export const Curvas = {
  power1In: _pow(2), power1Out: _out(_pow(2)), power1InOut: _inOut(_pow(2)),
  power2In: _pow(3), power2Out: _out(_pow(3)), power2InOut: _inOut(_pow(3)),
  power3In: _pow(4), power3Out: _out(_pow(4)), power3InOut: _inOut(_pow(4)),
  power4In: _pow(5), power4Out: _out(_pow(5)), power4InOut: _inOut(_pow(5)),
  expoIn: _expo, expoOut: _out(_expo), expoInOut: _inOut(_expo),
  circIn: _circ, circOut: _out(_circ), circInOut: _inOut(_circ),
  backIn: _back(1.70158), backOut: _out(_back(1.70158)), backInOut: _inOut(_back(1.70158 * 1.525)),
  elasticOut: _elasticOut(), elasticIn: _out(_elasticOut()),
  bounceOut: _bounceOut, bounceIn: _out(_bounceOut), bounceInOut: _inOut(_out(_bounceOut)),
  sineInOut: (t: number) => -(Math.cos(Math.PI * t) - 1) / 2,
  /** back com força escolhida (1.7 = padrão do GSAP; 3 = passa bem do ponto) */
  backOutForca: (s: number) => _out(_back(s)),
  /** elastic(amplitude, período) como no GSAP: elastic.out(1, 0.3) */
  elasticOutCom: (amp: number, per: number) => _elasticOut(amp, per),
};

// ── Surgir (28/10, movimentos da legenda caption-fine do Hypit) ── entrada de texto/card no quadro `em`.
export type Movimento = 'fade' | 'pop' | 'mola' | 'quique' | 'elastico' | 'carimbo' | 'inclinar' | 'zoomDesfoque'
  | 'desfoque' | 'virarX' | 'virarY' | 'girar' | 'achatar' | 'esticar' | 'varrerEsq' | 'varrerDir' | 'varrerCima'
  | 'subir' | 'descer' | 'daEsq' | 'daDir';

/** Estado de um movimento em p (0 → 1). Exportado para a legenda e para quem quiser compor. */
export const movimento = (tipo: Movimento, p: number, distancia = 60) => {
  const v = Math.max(0, Math.min(1, p));
  const e = Curvas.power2Out(v);
  const back = Curvas.backOutForca(1.3)(v);
  const esc = (de: number, x: number) => `scale(${de + (1 - de) * x})`;
  const r = (op: number, transform = 'none', filter = 'none', clipPath?: string) => ({opacity: op, transform, filter, clipPath});
  const resto = (1 - e) * distancia;
  switch (tipo) {
    case 'fade': return r(e);
    case 'pop': return r(e, esc(0.6, back));
    case 'mola': return r(1, esc(0.72, v >= 1 ? 1 : 1 - Math.exp(-5 * v) * Math.cos(10 * v)));
    case 'quique': return r(e, esc(0, Curvas.bounceOut(v)));
    case 'elastico': return r(e, esc(0, Curvas.elasticOut(v)));
    case 'carimbo': return r(e, esc(1.35, back));
    case 'inclinar': return r(e, `rotate(${(1 - e) * -8}deg) ${esc(0.94, e)}`);
    case 'zoomDesfoque': return r(e, esc(1.18, e), `blur(${(1 - e) * 18}px)`);
    case 'desfoque': return r(e, esc(0.96, e), `blur(${(1 - e) * 16}px)`);
    case 'virarX': return r(e, `perspective(600px) rotateX(${(1 - e) * 88}deg) ${esc(0.92, e)}`);
    case 'virarY': return r(e, `perspective(600px) rotateY(${(1 - e) * -88}deg) ${esc(0.92, e)}`);
    case 'girar': return r(e, `rotate(${(1 - e) * -180}deg) ${esc(0.55, e)}`);
    case 'achatar': return r(e, `scaleX(${1.28 - 0.28 * back}) scaleY(${0.48 + 0.52 * back})`);
    case 'esticar': return r(e, `scaleX(${0.5 + 0.5 * back}) scaleY(${1.35 - 0.35 * back})`);
    case 'varrerEsq': return r(1, 'none', 'none', `inset(0% 0% 0% ${(1 - e) * 100}%)`);
    case 'varrerDir': return r(1, 'none', 'none', `inset(0% ${(1 - e) * 100}% 0% 0%)`);
    case 'varrerCima': return r(1, 'none', 'none', `inset(${(1 - e) * 100}% 0% 0% 0%)`);
    case 'subir': return r(e, `translateY(${resto}px)`);
    case 'descer': return r(e, `translateY(${-resto}px)`);
    case 'daEsq': return r(e, `translateX(${-resto}px)`);
    case 'daDir': return r(e, `translateX(${resto}px)`);
  }
};

/** Entrada com um dos 21 movimentos, no quadro `em` (relativo à cena), durando `n` quadros. */
export const Surgir: React.FC<Filhos & {como?: Movimento; em?: number; n?: number; distancia?: number;
  inline?: boolean}> = ({como = 'pop', em = 0, n = 10, distancia = 60, inline = false, children}) => {
  const f = useCurrentFrame();
  const m = movimento(como, (f - em) / Math.max(1, n), distancia);
  return (
    <div style={{display: inline ? 'inline-block' : 'block', opacity: f < em ? 0 : m.opacity, transform: m.transform,
      filter: m.filter === 'none' ? undefined : m.filter, clipPath: m.clipPath}}>
      {children}
    </div>
  );
};

/** Partículas subindo devagar (fundo do cartão final / clima). */
export const Particulas: React.FC<{qtd?: number; cor?: string; tamanho?: number}> = ({qtd = 24, cor = '#ffffff', tamanho = 10}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {Array.from({length: qtd}).map((_, i) => {
        const x = random(`px${i}`) * 1080;
        const vel = 1 + random(`pv${i}`) * 2.5;
        const y = 1920 - ((f * vel + random(`py${i}`) * 1920) % 2100);
        const t = tamanho * (0.5 + random(`pt${i}`));
        return <div key={i} style={{position: 'absolute', left: x, top: y, width: t, height: t, borderRadius: '50%',
          background: cor, opacity: 0.25 + 0.35 * random(`po${i}`)}} />;
      })}
    </AbsoluteFill>
  );
};

/** (02/11) Texto que CABE: quebra em até `linhas` linhas equilibradas e escolhe o maior tamanho de fonte que cabe
 *  na `largura` (@remotion/layout-utils fitText), limitado a `max`. Acaba com título estourando a caixa.
 *  `fonte` tem que ser a MESMA família carregada (loadFont) — senão mede com outra letra. */
export const TextoQueCabe: React.FC<{texto: string; largura?: number; linhas?: number; max?: number; fonte?: string;
  peso?: string; altura?: number; style?: React.CSSProperties}> = (
  {texto, largura = 940, linhas = 2, max = 140, fonte = 'Montserrat', peso = '900', altura = 1.05, style}) => {
  const palavras = texto.trim().split(/\s+/);
  let melhor = {tam: 0, partes: [texto]};
  for (let n = 1; n <= Math.min(linhas, palavras.length); n++) {
    // divide as palavras em n linhas de tamanho parecido (por número de letras)
    const alvo = texto.length / n;
    const partes: string[] = [];
    let atual = '';
    for (const w of palavras) {
      if (atual && (atual + ' ' + w).length > alvo * 1.15 && partes.length < n - 1) {
        partes.push(atual);
        atual = w;
      } else {
        atual = atual ? atual + ' ' + w : w;
      }
    }
    partes.push(atual);
    const tam = Math.min(max, ...partes.map((p) => fitText({text: p, withinWidth: largura, fontFamily: fonte,
      fontWeight: peso}).fontSize));
    if (tam > melhor.tam * 1.08) melhor = {tam, partes};  // só aceita mais linhas se a letra crescer de verdade
  }
  return (
    <div style={{width: largura, textAlign: 'center', fontFamily: fonte, fontWeight: peso as React.CSSProperties['fontWeight'],
      fontSize: melhor.tam, lineHeight: altura, whiteSpace: 'nowrap', ...style}}>
      {melhor.partes.map((p, i) => <div key={i}>{p}</div>)}
    </div>
  );
};

/** (02/11) Motion blur de câmera (@remotion/motion-blur): o movimento rápido (chicote, zoom, entrada) borra como
 *  numa câmera de verdade. Envolva SÓ o trecho rápido (um <Sequence>), não a cena inteira: o render da parte
 *  envolvida custa `amostras` vezes mais. */
export const BorraoMovimento: React.FC<Filhos & {angulo?: number; amostras?: number}> = (
  {angulo = 180, amostras = 8, children}) => (
  <CameraMotionBlur shutterAngle={angulo} samples={amostras}>{children}</CameraMotionBlur>
);
