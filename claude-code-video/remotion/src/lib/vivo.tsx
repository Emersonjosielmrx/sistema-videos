// Efeitos VIVOS (28/10) — incorporados do historias-em-frames (Python/ffmpeg) para o Remotion.
// O gerar.py prepara cada foto (camadas.py) e o briefing traz em cenas[i].vivo:
//   profundidade (img_N_prof.png), camadas [img_N.jpg, img_N_meio.png, img_N_perto.png],
//   recorte (img_N_recorte.png, do tamanho da tela), fundo_limpo (img_N_limpo.jpg = a foto SEM o assunto),
//   assunto_caixa [x0, y0, x1, y1] (onde o assunto está).
// Uso: import {RecorteVivo, Camadas25D, Profundidade, Impacto, Onda, Ambiente} from '../../lib/vivo';
import React, {useEffect, useMemo, useState} from 'react';
import {AbsoluteFill, continueRender, delayRender, Img, interpolate, random, useCurrentFrame,
  useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import * as THREE from 'three';
import {Curvas} from './efeitos';

const trava = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
type Filhos = {children?: React.ReactNode};

// ───────────────────────── recorte vivo ─────────────────────────
export type ComoRecorte = 'flutuar' | 'balancar' | 'respirar' | 'entrarLado' | 'saltar' | 'aproximar' | 'recuar'
  | 'impacto' | 'cair' | 'quicar' | 'medo' | 'batida' | 'girar' | 'inclinar' | 'andar' | 'fantasma' | 'clones';

/** O assunto recortado se mexe sobre o FUNDO LIMPO (sem ele — nunca aparece rosto duplicado).
 *  `em` = quadro do impacto/entrada (relativo à cena). `caixa` = assunto_caixa do briefing (eixo do movimento). */
export const RecorteVivo: React.FC<{fundo: string; recorte: string; dur: number; como?: ComoRecorte; em?: number;
  caixa?: number[] | null; desfoque?: number; escurecer?: number; contorno?: string; holofote?: boolean;
  lado?: 1 | -1}> = ({fundo, recorte, dur, como = 'flutuar', em = 0, caixa, desfoque = 10, escurecer = 0.18,
  contorno, holofote = false, lado = 1}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const cx = caixa ? (caixa[0] + caixa[2]) / 2 : 540;
  const baseY = caixa ? caixa[3] : 1920;
  const p = interpolate(f, [0, dur], [0, 1], trava);
  const pe = interpolate(f - em, [0, 18], [0, 1], {...trava, easing: Curvas.backOut});
  let x = 0, y = 0, s = 1, r = 0, ry = 0, sx = 1, sy = 1, op = 1;
  let fundoS = 1.04 + 0.08 * p;  // o fundo sempre anda devagar
  const dEm = f - em;
  const choque = dEm >= 0 && dEm < 16 ? Math.exp(-dEm / 4) : 0;
  switch (como) {
    case 'flutuar': y = 14 * Math.sin(t * 1.2); break;
    case 'balancar': x = 26 * Math.sin(t * 1.1); y = 8 * Math.sin(t * 2.2); r = 1.5 * Math.sin(t * 1.1); break;
    case 'respirar': s = 1 + 0.025 * Math.sin(t * 2.4); break;
    case 'entrarLado': x = (1 - pe) * -1200 * lado; y = 6 * Math.sin(t * 1.3); break;
    case 'saltar': s = 0.82 + 0.18 * pe + 0.03 * Math.sin(t * 2); y = (1 - pe) * 260; fundoS += 0.04 * pe; break;
    case 'aproximar': s = 1 + 0.22 * Curvas.power2InOut(p); fundoS = 1.04 + 0.06 * p; break;
    case 'recuar': s = 1.16 - 0.2 * Curvas.power2InOut(p); fundoS = 1.12 - 0.05 * p; break;
    case 'impacto':
      s = 1 + 0.12 * choque; x = (random(`ix${f}`) - 0.5) * 50 * choque; y = (random(`iy${f}`) - 0.5) * 40 * choque;
      fundoS += 0.05 * choque; break;
    case 'cair': y = interpolate(f - em, [0, 22], [-1400, 0], {...trava, easing: Curvas.bounceOut}); break;
    case 'quicar': {
      const c = ((f - em) % 30 + 30) % 30 / 30;
      const alt = Math.sin(Math.PI * c);
      y = -110 * alt; sx = c < 0.12 || c > 0.88 ? 1.12 : 1 - 0.05 * alt; sy = c < 0.12 || c > 0.88 ? 0.88 : 1 + 0.06 * alt;
      break;
    }
    case 'medo': x = (random(`mx${f}`) - 0.5) * 9; y = (random(`my${f}`) - 0.5) * 5; s = 1 - 0.02 * p; break;
    case 'batida': { const c = t % 0.9; s = 1 + 0.06 * Math.exp(-c * 18) + 0.04 * Math.exp(-Math.max(0, c - 0.22) * 18) * (c > 0.22 ? 1 : 0); break; }
    case 'girar': ry = 22 * Math.sin(t * 1.4) * lado; s = 1.02; break;
    case 'inclinar': r = 6 * Math.sin(t * 1.2); break;
    case 'andar': x = interpolate(p, [0, 1], [-140, 140]) * lado; y = -10 * Math.abs(Math.sin(t * 5)); break;
    case 'fantasma': case 'clones': x = 26 * Math.sin(t * 1.1); y = 8 * Math.sin(t * 2.2); break;
  }
  const filtro = [contorno && `drop-shadow(0 0 6px ${contorno}) drop-shadow(0 0 18px ${contorno})`,
    'drop-shadow(0 28px 36px rgba(0,0,0,0.55))'].filter(Boolean).join(' ');
  const corpo = (dx: number, dy: number, sc: number, o: number, k: string) => (
    <Img key={k} src={recorte} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: o,
      transformOrigin: `${cx}px ${baseY}px`, filter: filtro,
      transform: `perspective(1400px) translate(${x + dx}px, ${y + dy}px) rotate(${r}deg) rotateY(${ry}deg) scale(${s * sc}) scaleX(${sx}) scaleY(${sy})`}} />
  );
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
      <Img src={fundo} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${fundoS})`,
        filter: `blur(${desfoque}px) brightness(${1 - escurecer})`}} />
      {holofote && <AbsoluteFill style={{background: `radial-gradient(ellipse 46% 40% at ${cx / 10.8}% ${(baseY - 500) / 19.2}%, transparent 30%, rgba(0,0,0,0.72) 100%)`}} />}
      {como === 'clones' && [-1, 1].map((l) => corpo(l * 300, 40, 0.78, 0.55, `c${l}`))}
      {como === 'fantasma' && [3, 2, 1].map((k) => {
        const tt = t - k * 0.08;
        return corpo(26 * Math.sin(tt * 1.1) - x, 8 * Math.sin(tt * 2.2) - y, 1, 0.18 * (4 - k), `g${k}`);
      })}
      {corpo(0, 0, 1, op, 'principal')}
    </AbsoluteFill>
  );
};

// ───────────────────────── camadas 2.5D (CSS, leve) ─────────────────────────
export type Mov25 = 'orbita' | 'empurrar' | 'flutuar' | 'varrer';
const mov = (m: Mov25, s: number, t: number, p: number) => {
  // porte do _camera_expr do parallax_engine (velocidade s por camada), amplitudes para 1080x1920
  if (m === 'orbita') return {x: s * 22 * Math.sin((2 * Math.PI * t) / 9), y: s * 12 * Math.cos((2 * Math.PI * t) / 9), z: 1.08};
  if (m === 'empurrar') return {x: 0, y: -s * 6 * p, z: 1.04 + s * 0.06 * p};
  if (m === 'varrer') return {x: s * 34 * (2 * p - 1), y: s * 6 * Math.sin((2 * Math.PI * t) / 11), z: 1.08};
  return {x: s * 18 * Math.sin((2 * Math.PI * t) / 8), y: s * 10 * Math.sin((2 * Math.PI * t) / 11), z: 1.07};
};

/** Foto em 3 camadas de profundidade que andam em velocidades diferentes (longe devagar, perto rápido). */
export const Camadas25D: React.FC<{camadas: string[]; dur: number; movimento?: Mov25; forca?: number}> = (
  {camadas, dur, movimento = 'flutuar', forca = 1}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = interpolate(f, [0, dur], [0, 1], {...trava, easing: Curvas.sineInOut});
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
      {camadas.map((src, i) => {
        const m = mov(movimento, [0.5, 1.1, 2.0][i] * forca, f / fps, p);
        return <Img key={i} src={src} style={{position: 'absolute', inset: 0, width: '100%', height: '100%',
          objectFit: 'cover', transform: `translate(${m.x}px, ${m.y}px) scale(${m.z + 0.015 * i})`}} />;
      })}
    </AbsoluteFill>
  );
};

// ───────────────────────── profundidade por pixel (WebGL) ─────────────────────────
const FRAG = `
uniform sampler2D uImg; uniform sampler2D uProf; uniform vec2 uCam; uniform float uZoom; uniform float uFoco;
varying vec2 vUv;
void main() {
  vec2 c = (vUv - 0.5) / uZoom + 0.5;
  float d = texture2D(uProf, c).r;
  vec2 uv = c + uCam * (d - uFoco);
  d = texture2D(uProf, uv).r;            // 2ª passada: a borda do objeto perto não "rasga"
  uv = c + uCam * (d - uFoco);
  gl_FragColor = texture2D(uImg, clamp(uv, 0.001, 0.999));
}`;
const VERT = `varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

const useTextura = (src: string) => {
  const [h] = useState(() => delayRender(`textura ${src}`));
  const [t, setT] = useState<THREE.Texture | null>(null);
  useEffect(() => {
    new THREE.TextureLoader().load(src, (x) => {
      x.colorSpace = THREE.NoColorSpace; // valores crus: o shader devolve a cor como está na foto
      x.minFilter = THREE.LinearFilter;
      setT(x);
      continueRender(h);
    }, undefined, () => continueRender(h));
  }, [src]); // eslint-disable-line react-hooks/exhaustive-deps
  return t;
};

/** 2.5D DE VERDADE: cada pixel anda conforme a profundidade dele (câmera entrando numa cena 3D).
 *  forca 0.02–0.05 (mais que isso estica a borda). foco 0.5 = o meio fica parado, perto anda mais. */
export const Profundidade: React.FC<{src: string; profundidade: string; dur: number; movimento?: Mov25;
  forca?: number; foco?: number}> = ({src, profundidade, dur, movimento = 'orbita', forca = 0.035, foco = 0.45}) => {
  const f = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const img = useTextura(src);
  const prof = useTextura(profundidade);
  const mat = useMemo(() => (img && prof ? new THREE.ShaderMaterial({vertexShader: VERT, fragmentShader: FRAG,
    uniforms: {uImg: {value: img}, uProf: {value: prof}, uCam: {value: new THREE.Vector2()}, uZoom: {value: 1.06},
      uFoco: {value: foco}}}) : null), [img, prof, foco]);
  if (!mat) return null;
  const t = f / fps;
  const p = interpolate(f, [0, dur], [0, 1], {...trava, easing: Curvas.sineInOut});
  const cam = movimento === 'orbita' ? [Math.sin((2 * Math.PI * t) / 7), Math.cos((2 * Math.PI * t) / 7) * 0.6]
    : movimento === 'varrer' ? [2 * p - 1, 0.15 * Math.sin(t)]
    : movimento === 'empurrar' ? [0.1 * Math.sin(t), -0.6 * p]
    : [Math.sin((2 * Math.PI * t) / 8), 0.6 * Math.sin((2 * Math.PI * t) / 11)];
  mat.uniforms.uCam.value.set(cam[0] * forca, cam[1] * forca * (width / height) * 1.4);
  mat.uniforms.uZoom.value = 1.06 + (movimento === 'empurrar' ? 0.14 * p : 0.03 * p);
  return (
    <AbsoluteFill>
      <ThreeCanvas width={width} height={height} style={{position: 'absolute', inset: 0}} gl={{preserveDrawingBuffer: true}}>
        <mesh material={mat} frustumCulled={false}>
          <planeGeometry args={[2, 2]} />
        </mesh>
      </ThreeCanvas>
    </AbsoluteFill>
  );
};

// ───────────────────────── impacto ─────────────────────────
/** Pancada de câmera no quadro `em` (a palavra de impacto): soco de zoom, tremor que morre, cor separando e
 *  flash. Envolve a cena inteira. Vários impactos: em={[30, 95]}. */
export const Impacto: React.FC<Filhos & {em: number | number[]; forca?: number; flash?: boolean; cor?: boolean}> = (
  {em, forca = 1, flash = true, cor = true, children}) => {
  const f = useCurrentFrame();
  const ems = Array.isArray(em) ? em : [em];
  const d = Math.min(...ems.map((e) => (f >= e ? f - e : 999)));
  const k = d < 18 ? Math.exp(-d / 4.5) * forca : 0;
  const x = (random(`kx${f}`) - 0.5) * 60 * k;
  const y = (random(`ky${f}`) - 0.5) * 44 * k;
  const s = 1 + 0.1 * (d < 3 ? interpolate(d, [0, 2], [1, 0.7]) : 0.7 * Math.exp(-(d - 2) / 5)) * (d < 18 ? forca : 0);
  const sep = cor && d < 6 ? (6 - d) * 3 * forca : 0;
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `translate(${x}px, ${y}px) scale(${s}) rotate(${(random(`kr${f}`) - 0.5) * 2 * k}deg)`,
        filter: sep ? `drop-shadow(${sep}px 0 0 rgba(255,0,60,0.55)) drop-shadow(${-sep}px 0 0 rgba(0,220,255,0.55))` : undefined}}>
        {children}
      </AbsoluteFill>
      {flash && d < 3 && <AbsoluteFill style={{background: '#fff', opacity: [0.75, 0.35, 0.1][d] * Math.min(1, forca),
        pointerEvents: 'none'}} />}
    </AbsoluteFill>
  );
};

/** Onda de choque: anel que se abre a partir de (x, y) no quadro `em` (soco, explosão, revelação). */
export const Onda: React.FC<{em: number; x?: number; y?: number; cor?: string}> = ({em, x = 540, y = 900, cor = '#fff'}) => {
  const f = useCurrentFrame();
  const d = f - em;
  if (d < 0 || d > 20) return null;
  const r = interpolate(d, [0, 20], [40, 1300], {...trava, easing: Curvas.expoOut});
  return <div style={{position: 'absolute', left: x - r, top: y - r, width: r * 2, height: r * 2, borderRadius: '50%',
    border: `${interpolate(d, [0, 20], [26, 2], trava)}px solid ${cor}`, opacity: interpolate(d, [0, 20], [0.9, 0], trava),
    boxShadow: `0 0 40px ${cor}`, pointerEvents: 'none'}} />;
};

// ───────────────────────── ambiente vivo ─────────────────────────
export type Clima = 'poeira' | 'neve' | 'chuva' | 'brasas' | 'nevoa' | 'raios' | 'vinheta';

/** Coisa viva na tela por cima da foto. SÓ se a fala/cena fala disso (no historias-em-frames saiu neve
 *  numa sala ensolarada): neve = inverno/neve; chuva = chuva/tempestade; brasas = fogo/guerra/inferno;
 *  nevoa = névoa/mistério/terror; raios = sol/janela/igreja/revelação; poeira = qualquer (sutil). */
export const Ambiente: React.FC<{tipo: Clima; qtd?: number; cor?: string; forca?: number}> = (
  {tipo, qtd, cor, forca = 1}) => {
  const f = useCurrentFrame();
  const n = qtd ?? ({poeira: 40, neve: 90, chuva: 120, brasas: 45, nevoa: 4, raios: 5, vinheta: 0} as const)[tipo];
  if (tipo === 'vinheta') {
    const a = 0.55 + 0.12 * Math.sin(f / 20);
    return <AbsoluteFill style={{background: `radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,${a * forca}) 100%)`, pointerEvents: 'none'}} />;
  }
  if (tipo === 'nevoa') {
    return (
      <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'screen'}}>
        {Array.from({length: n}).map((_, i) => (
          <div key={i} style={{position: 'absolute', left: -400 + ((f * (0.6 + i * 0.3) + i * 500) % 1900) - 500,
            top: 300 + i * 380, width: 1600, height: 700, borderRadius: '50%', opacity: 0.22 * forca,
            background: `radial-gradient(ellipse, ${cor ?? '#cfd8e3'} 0%, transparent 70%)`, filter: 'blur(30px)'}} />
        ))}
      </AbsoluteFill>
    );
  }
  if (tipo === 'raios') {
    return (
      <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'screen', overflow: 'hidden'}}>
        {Array.from({length: n}).map((_, i) => (
          <div key={i} style={{position: 'absolute', left: 120 + i * 190, top: -300, width: 90 + 40 * random(`rw${i}`),
            height: 2600, transformOrigin: 'top center', transform: `rotate(${18 + 4 * Math.sin(f / 50 + i)}deg)`,
            background: `linear-gradient(${cor ?? 'rgba(255,236,190,0.55)'}, transparent 80%)`,
            opacity: (0.25 + 0.2 * Math.sin(f / 30 + i * 1.7)) * forca, filter: 'blur(14px)'}} />
        ))}
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden'}}>
      {Array.from({length: n}).map((_, i) => {
        const rx = random(`ax${tipo}${i}`), ry = random(`ay${tipo}${i}`), rv = random(`av${tipo}${i}`);
        if (tipo === 'chuva') {
          const y = ((ry * 2200 + f * (38 + 20 * rv)) % 2300) - 200;
          return <div key={i} style={{position: 'absolute', left: rx * 1180 - 50 - y * 0.12, top: y, width: 3,
            height: 70 + 50 * rv, background: cor ?? 'rgba(200,220,255,0.55)', transform: 'rotate(7deg)'}} />;
        }
        if (tipo === 'brasas') {
          const y = 2000 - ((ry * 2100 + f * (3 + 4 * rv)) % 2200);
          const x = rx * 1080 + 40 * Math.sin(f / 18 + i);
          const tam = 5 + 9 * rv;
          return <div key={i} style={{position: 'absolute', left: x, top: y, width: tam, height: tam, borderRadius: '50%',
            background: cor ?? '#ffb347', boxShadow: `0 0 ${tam * 2}px ${cor ?? '#ff6a00'}`,
            opacity: (0.5 + 0.5 * Math.sin(f / 6 + i)) * forca}} />;
        }
        const neve = tipo === 'neve';
        const y = ((ry * 2100 + f * (neve ? 2.5 + 3 * rv : 0.5 + rv)) % 2100) - 100;
        const x = rx * 1080 + (neve ? 30 : 60) * Math.sin(f / (neve ? 25 : 60) + i);
        const tam = neve ? 6 + 10 * rv : 3 + 5 * rv;
        return <div key={i} style={{position: 'absolute', left: x, top: y, width: tam, height: tam, borderRadius: '50%',
          background: cor ?? (neve ? '#ffffff' : 'rgba(255,240,210,0.8)'), filter: neve ? 'blur(1px)' : undefined,
          opacity: (neve ? 0.85 : 0.35 + 0.3 * Math.sin(f / 15 + i)) * forca}} />;
      })}
    </AbsoluteFill>
  );
};
