// Transições de RASGO com raio / fogo / glitch (28/10, dona: "os efeitos de choque e fogo como o manhwa-react usa
// para dividir a tela, só que para transicionar a tela, dando choque, para aparecer a próxima, ou para impactos").
// Porte do D:\manhwa-react\mr\divider.py (raio serpenteando com brilho, línguas de fogo, glitch; borda de papel
// rasgado) desenhado por quadro em SVG — sem arquivo de vídeo, qualquer cor.
// Uso:
//   import {TransitionSeries, linearTiming} from '@remotion/transitions';
//   import {rasgo, RaioImpacto} from '../../lib/transicoes';
//   <TransitionSeries.Transition presentation={rasgo({estilo: 'raio', cor: '#00d1ff'})}
//     timing={linearTiming({durationInFrames: 16})} />
//   <RaioImpacto em={quadro} estilo="raio" cor="#ffc83d" />   // choque atravessando a tela num impacto
import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, random, useCurrentFrame} from 'remotion';
import type {TransitionPresentation, TransitionPresentationComponentProps} from '@remotion/transitions';

export type EstiloRasgo = 'raio' | 'fogo' | 'glitch';
const W = 1080, H = 1920;

/** Borda de papel rasgado: deslocamento y (px) em cada x, fixo pela semente. */
const borda = (semente: string, amp = 34) => {
  const pts: [number, number][] = [];
  let x = 0, y = 0;
  let k = 0;
  while (x < W) {
    pts.push([x, y]);
    x += 6 + 10 * random(`bx${semente}${k}`);
    y += (random(`by${semente}${k}`) - 0.5) * amp * 0.45;
    y = Math.max(-amp, Math.min(amp, y));
    k++;
  }
  pts.push([W, y]);
  return pts;
};

const raios = (y0: number, f: number, amp: number, seg: number, sem: string) => {
  const pts: string[] = [];
  let x = 0, k = 0;
  while (x <= W) {
    pts.push(`${x.toFixed(0)},${(y0 + (random(`r${sem}${f}${k}`) - 0.5) * 2 * amp).toFixed(0)}`);
    x += seg * (0.5 + random(`s${sem}${f}${k}`));
    k++;
  }
  return pts.join(' ');
};

/** A faixa do efeito desenhada ao longo da linha y (com a borda rasgada). `f` = quadro (anima o efeito). */
export const Faixa: React.FC<{y: number; estilo: EstiloRasgo; cor: string; f: number; semente?: string;
  forca?: number}> = ({y, estilo, cor, f, semente = 'a', forca = 1}) => {
  const b = useMemo(() => borda(semente), [semente]);
  if (estilo === 'raio') {
    const pisca = 0.7 + 0.3 * Math.sin(f * 2.3);
    return (
      <svg width={W} height={H} style={{position: 'absolute', inset: 0, overflow: 'visible', pointerEvents: 'none'}}>
        <g style={{filter: `drop-shadow(0 0 8px ${cor}) drop-shadow(0 0 26px ${cor})`}} opacity={pisca * forca}>
          {[0, 1, 2].map((i) => (
            <polyline key={i} points={raios(y, f, 26 + 22 * i, 28 + 14 * i, `${semente}${i}`)} fill="none"
              stroke={cor} strokeWidth={7 - 2 * i} strokeLinejoin="round" />
          ))}
          <polyline points={raios(y, f + 999, 12, 30, `${semente}w`)} fill="none" stroke="#fff" strokeWidth={3} />
          {[0, 1, 2, 3, 4].map((i) => {
            const x0 = random(`gx${semente}${f}${i}`) * W;
            return <polyline key={`g${i}`} fill="none" stroke={cor} strokeWidth={2}
              points={[0, 1, 2, 3].map((k) => `${x0 + (random(`gk${f}${i}${k}`) - 0.5) * 60 * (k + 1)},${y + (random(`gy${f}${i}${k}`) - 0.5) * 120}`).join(' ')} />;
          })}
        </g>
      </svg>
    );
  }
  if (estilo === 'fogo') {
    const linguas = 34;
    return (
      <svg width={W} height={H} style={{position: 'absolute', inset: 0, overflow: 'visible', pointerEvents: 'none'}}>
        <defs>
          <linearGradient id={`fg${semente}`} x1="0" y1="1" x2="0" y2="0">
            <stop offset="0" stopColor="#fff3b0" />
            <stop offset="0.25" stopColor="#ffb800" />
            <stop offset="0.6" stopColor="#ff4d00" />
            <stop offset="1" stopColor={cor} stopOpacity={0} />
          </linearGradient>
        </defs>
        <g style={{filter: 'drop-shadow(0 0 14px #ff6a00) blur(0.6px)'}} opacity={forca}>
          {Array.from({length: linguas}).map((_, k) => {
            const cx = (k + random(`fx${semente}${k}`)) * (W / linguas);
            const yb = y + b[Math.min(b.length - 1, Math.round((cx / W) * (b.length - 1)))][1];
            const h = (60 + 90 * random(`fh${semente}${k}`)) * (0.7 + 0.3 * Math.sin(f * (0.25 + 0.2 * random(`ff${k}`)) + k));
            const w = 22 + 40 * random(`fw${semente}${k}`);
            const dx = 10 * Math.sin(f / 4 + k);
            return <path key={k} fill={`url(#fg${semente})`}
              d={`M${cx - w / 2},${yb} Q${cx - w / 3 + dx},${yb - h * 0.55} ${cx + dx * 1.6},${yb - h} Q${cx + w / 3 + dx},${yb - h * 0.5} ${cx + w / 2},${yb} Z`} />;
          })}
          <polyline points={b.map(([x, dy]) => `${x},${y + dy}`).join(' ')} fill="none" stroke="#ffd27a" strokeWidth={5}
            style={{filter: 'drop-shadow(0 0 10px #ff6a00)'}} />
        </g>
      </svg>
    );
  }
  // glitch
  const blocos = Array.from({length: 9}).map((_, i) => ({
    x: random(`bx${f}${i}`) * (W - 80), w: 40 + random(`bw${f}${i}`) * 260,
    y: y + (random(`byy${f}${i}`) - 0.5) * 140, h: 4 + random(`bh${f}${i}`) * 14,
    c: [cor, '#ffffff', '#ff005a', '#00ffe6'][Math.floor(random(`bc${f}${i}`) * 4)],
  }));
  return (
    <svg width={W} height={H} style={{position: 'absolute', inset: 0, overflow: 'visible', pointerEvents: 'none'}}>
      <g style={{filter: `drop-shadow(0 0 10px ${cor})`}} opacity={forca}>
        <polyline points={b.map(([x, dy]) => `${x},${y + dy + (random(`go${f}${Math.floor(x / 120)}`) < 0.2 ? 10 : 0)}`).join(' ')}
          fill="none" stroke={cor} strokeWidth={6} />
        {blocos.map((q, i) => <rect key={i} x={q.x} y={q.y} width={q.w} height={q.h} fill={q.c} />)}
      </g>
    </svg>
  );
};

// ───────────── transição (TransitionSeries) ─────────────
type PropsRasgo = {estilo?: EstiloRasgo; cor?: string; direcao?: 'desce' | 'sobe'};

const RasgoComp: React.FC<TransitionPresentationComponentProps<PropsRasgo>> = (
  {children, presentationDirection, presentationProgress, passedProps}) => {
  const f = useCurrentFrame();
  const {estilo = 'raio', cor = '#00d1ff', direcao = 'desce'} = passedProps;
  const b = useMemo(() => borda('t'), []);
  if (presentationDirection === 'exiting') {
    // a cena que sai treme no começo (o choque) e segue por baixo
    const k = Math.max(0, 1 - presentationProgress * 3);
    return <AbsoluteFill style={{transform: `translate(${(random(`ex${f}`) - 0.5) * 30 * k}px, ${(random(`ey${f}`) - 0.5) * 20 * k}px)`}}>
      {children}</AbsoluteFill>;
  }
  // a cena que entra aparece do lado de cá do rasgo, que atravessa a tela
  const p = interpolate(presentationProgress, [0, 1], [0, 1]);
  const y = direcao === 'desce' ? -80 + p * (H + 160) : H + 80 - p * (H + 160);
  const poli = direcao === 'desce'
    ? [`0px 0px`, `${W}px 0px`, ...b.slice().reverse().map(([x, dy]) => `${x}px ${y + dy}px`)]
    : [`0px ${H}px`, `${W}px ${H}px`, ...b.slice().reverse().map(([x, dy]) => `${x}px ${y + dy}px`)];
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{clipPath: `polygon(${poli.join(', ')})`}}>{children}</AbsoluteFill>
      <Faixa y={y} estilo={estilo} cor={cor} f={f} semente="t" />
      {presentationProgress < 0.12 && <AbsoluteFill style={{background: '#fff', opacity: 0.5 * (1 - presentationProgress / 0.12)}} />}
    </AbsoluteFill>
  );
};

export const rasgo = (props: PropsRasgo = {}): TransitionPresentation<PropsRasgo> => ({component: RasgoComp, props});

// ───────────── impacto ─────────────
/** Choque atravessando a tela no quadro `em` (palavra de impacto): a faixa corta a tela em `y`, pisca e some. */
export const RaioImpacto: React.FC<{em: number; n?: number; y?: number; estilo?: EstiloRasgo; cor?: string}> = (
  {em, n = 12, y = 960, estilo = 'raio', cor = '#ffc83d'}) => {
  const f = useCurrentFrame();
  const d = f - em;
  if (d < 0 || d > n) return null;
  const forca = d < 2 ? 1 : interpolate(d, [2, n], [1, 0]);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {d < 2 && <AbsoluteFill style={{background: cor, opacity: 0.25, mixBlendMode: 'screen'}} />}
      <Faixa y={y} estilo={estilo} cor={cor} f={f} semente={`i${em}`} forca={forca} />
    </AbsoluteFill>
  );
};
