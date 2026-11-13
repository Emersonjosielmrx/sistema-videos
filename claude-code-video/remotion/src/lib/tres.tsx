// Peças 3D PRONTAS (28/10) com Three.js pelo @remotion/three (já instalado, nunca tinha sido usado).
// Uso: import {Titulo3D, Particulas3D, Produto360} from '../../lib/tres';
// Cada uma ocupa a tela inteira (1080x1920, fundo transparente): ponha como camada dentro da cena.
// `dur` = duração da cena em quadros. Tudo anda pelo quadro (useCurrentFrame), nada por relógio.
import React, {useEffect, useMemo, useState} from 'react';
import {ThreeCanvas} from '@remotion/three';
import * as THREE from 'three';
import {continueRender, delayRender, interpolate, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {Curvas} from './efeitos';

const trava = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** Quanto vale 1 px da tela em unidades 3D no plano z = 0 (câmera em z, abertura fov). */
const usePx = (z: number, fov: number) => {
  const {height} = useVideoConfig();
  return (2 * z * Math.tan(((fov / 2) * Math.PI) / 180)) / height;
};

const Tela: React.FC<{children: React.ReactNode; z?: number; fov?: number}> = ({children, z = 10, fov = 40}) => {
  const {width, height} = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} style={{position: 'absolute', inset: 0}}
      camera={{position: [0, 0, z], fov}} gl={{alpha: true, antialias: true, preserveDrawingBuffer: true}}>
      {children}
    </ThreeCanvas>
  );
};

/** Texto desenhado num canvas (aceita acento e qualquer fonte já carregada) virando textura. */
const useTexturaTexto = (linhas: string[], fontFamily: string, cor: string, peso: number) => {
  const [h] = useState(() => delayRender('fonte do Titulo3D'));
  const [tex, setTex] = useState<{t: THREE.CanvasTexture; prop: number} | null>(null);
  useEffect(() => {
    let vivo = true;
    document.fonts.load(`${peso} 160px ${fontFamily}`).catch(() => null).then(() => document.fonts.ready).then(() => {
      if (!vivo) return;
      const c = document.createElement('canvas');
      const ctx = c.getContext('2d')!;
      const px = 200;
      ctx.font = `${peso} ${px}px ${fontFamily}`;
      const larg = Math.max(...linhas.map((l) => ctx.measureText(l).width)) + 80;
      c.width = Math.ceil(larg);
      c.height = Math.ceil(linhas.length * px * 1.05 + 60);
      ctx.font = `${peso} ${px}px ${fontFamily}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = cor;
      linhas.forEach((l, i) => ctx.fillText(l, c.width / 2, 30 + px * 1.05 * (i + 0.5)));
      const t = new THREE.CanvasTexture(c);
      t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = 8;
      setTex({t, prop: c.width / c.height});
      continueRender(h);
    });
    return () => {
      vivo = false;
    };
  }, [linhas.join('|'), fontFamily, cor, peso]); // eslint-disable-line react-hooks/exhaustive-deps
  return tex;
};

/** Título 3D com espessura (camadas), entra girando e fica balançando. `texto` aceita '\n' (até 3 linhas).
 *  largura = fração da largura da tela (0.84 = respeita os 60 px de cada lado no balanço); centroY = px do topo. */
export const Titulo3D: React.FC<{texto: string; fontFamily: string; dur: number; cor?: string; corLado?: string;
  largura?: number; centroY?: number; balanco?: number; espessura?: number; peso?: number}> = (
  {texto, fontFamily, dur, cor = '#FFFFFF', corLado = '#C8102E', largura: fr = 0.8, centroY = 600, balanco = 18,
    espessura = 0.22, peso = 900}) => {
  const f = useCurrentFrame();
  const px = usePx(10, 40);
  const largura = fr * 1080 * px;
  const y = (960 - centroY) * px;
  const linhas = useMemo(() => texto.toUpperCase().split('\n'), [texto]);
  const frente = useTexturaTexto(linhas, fontFamily, cor, peso);
  const lado = useTexturaTexto(linhas, fontFamily, corLado, peso);
  const pe = interpolate(f, [0, 22], [0, 1], {...trava, easing: Curvas.backOut});
  const vivo = f / 30;
  const ry = (1 - pe) * -110 + Math.sin(vivo * 1.3) * balanco;
  const rx = (1 - pe) * 30 + Math.sin(vivo * 0.9 + 1) * (balanco * 0.35);
  const s = 0.4 + 0.6 * pe + interpolate(f, [0, dur], [0, 0.08], trava);
  if (!frente || !lado) return null;
  const alt = largura / frente.prop;
  const camadas = 14;
  return (
    <Tela>
      <ambientLight intensity={1} />
      <group position={[0, y, 0]} rotation={[(rx * Math.PI) / 180, (ry * Math.PI) / 180, 0]} scale={s}>
        {Array.from({length: camadas}).map((_, i) => (
          <mesh key={i} position={[0, 0, -(i / camadas) * espessura]}>
            <planeGeometry args={[largura, alt]} />
            <meshBasicMaterial map={i === 0 ? frente.t : lado.t} transparent side={THREE.DoubleSide}
              color={i === 0 ? '#ffffff' : new THREE.Color(1, 1, 1).multiplyScalar(1 - (i / camadas) * 0.45)} />
          </mesh>
        ))}
      </group>
    </Tela>
  );
};

const texturaBolinha = () => {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const ctx = c.getContext('2d')!;
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.35, 'rgba(255,255,255,0.6)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
};

/** Campo de partículas em profundidade: a câmera atravessa (poeira, estrelas, brasas, neve). */
export const Particulas3D: React.FC<{qtd?: number; cor?: string; tamanho?: number; velocidade?: number;
  deriva?: number}> = ({qtd = 1400, cor = '#FFD27A', tamanho = 0.45, velocidade = 0.15, deriva = 0.25}) => {
  const f = useCurrentFrame();
  const fundo = 60;
  const pos = useMemo(() => {
    const a = new Float32Array(qtd * 3);
    for (let i = 0; i < qtd; i++) {
      a[i * 3] = (random(`x${i}`) - 0.5) * 14;
      a[i * 3 + 1] = (random(`y${i}`) - 0.5) * 24;
      a[i * 3 + 2] = -random(`z${i}`) * fundo;
    }
    return a;
  }, [qtd]);
  const atual = useMemo(() => new Float32Array(qtd * 3), [qtd]);
  for (let i = 0; i < qtd; i++) {
    // cada ponto vem na direção da câmera e volta para o fundo quando passa (o campo nunca acaba)
    const z = ((pos[i * 3 + 2] + f * velocidade) % fundo + fundo) % fundo - fundo + 9;
    atual[i * 3] = pos[i * 3] + Math.sin(f / 40 + i) * deriva;
    atual[i * 3 + 1] = pos[i * 3 + 1] + Math.cos(f / 50 + i * 0.7) * deriva;
    atual[i * 3 + 2] = z;
  }
  const mapa = useMemo(texturaBolinha, []);
  return (
    <Tela fov={55}>
      <points key={f}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" count={qtd} array={atual} itemSize={3} />
        </bufferGeometry>
        <pointsMaterial map={mapa} color={cor} size={tamanho} sizeAttenuation transparent depthWrite={false}
          blending={THREE.AdditiveBlending} />
      </points>
    </Tela>
  );
};

/** Foto do produto num cartão 3D que gira (voltas) com sombra e brilho passando. src = staticFile('...').
 *  largura = fração da largura da tela; centroY = px do topo. */
export const Produto360: React.FC<{src: string; dur: number; voltas?: number; largura?: number; centroY?: number;
  corBorda?: string; espessura?: number}> = ({src, dur, voltas = 1, largura: fr = 0.62, centroY = 860,
  corBorda = '#1b1b1f', espessura = 0.12}) => {
  const f = useCurrentFrame();
  const px = usePx(12, 40);
  const largura = fr * 1080 * px;
  const y = (960 - centroY) * px;
  const [h] = useState(() => delayRender('foto do Produto360'));
  const [tex, setTex] = useState<THREE.Texture | null>(null);
  useEffect(() => {
    new THREE.TextureLoader().load(src, (t) => {
      t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = 8;
      setTex(t);
      continueRender(h);
    }, undefined, () => continueRender(h));
  }, [src]); // eslint-disable-line react-hooks/exhaustive-deps
  const mats = useMemo(() => {
    if (!tex) return null;
    const atras = tex.clone();
    atras.wrapS = THREE.RepeatWrapping;
    atras.repeat.x = -1; // costas espelhadas: a foto não aparece ao contrário
    atras.needsUpdate = true;
    const borda = new THREE.MeshStandardMaterial({color: corBorda, metalness: 0.6, roughness: 0.35});
    return [borda, borda, borda, borda,
      new THREE.MeshStandardMaterial({map: tex, roughness: 0.45, metalness: 0.05}),
      new THREE.MeshStandardMaterial({map: atras, roughness: 0.45, metalness: 0.05})];
  }, [tex, corBorda]);
  if (!tex || !mats) return null;
  const img = tex.image as {width: number; height: number};
  const alt = largura * (img.height / img.width);
  const p = interpolate(f, [0, dur], [0, 1], {...trava, easing: Curvas.power2InOut});
  const ry = p * voltas * Math.PI * 2;
  const flut = Math.sin(f / 22) * 0.12;
  const entra = interpolate(f, [0, 14], [0, 1], {...trava, easing: Curvas.backOut});
  return (

    <Tela z={12}>
      <ambientLight intensity={0.85} />
      <directionalLight position={[4, 6, 8]} intensity={1.6} />
      <pointLight position={[-5 + 10 * ((f / 45) % 1), 2, 4]} intensity={18} distance={12} color="#ffffff" />
      <group position={[0, y + flut, 0]} scale={entra}>
        <mesh rotation={[0.08, ry, 0]} material={mats}>
          <boxGeometry args={[largura, alt, espessura]} />
        </mesh>
      </group>
      <mesh position={[0, y - alt / 2 - 0.9, -0.5]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[largura * 0.55 * (0.75 + 0.25 * Math.abs(Math.cos(ry))), 48]} />
        <meshBasicMaterial color="#000000" transparent opacity={0.35 * entra} />
      </mesh>
    </Tela>
  );
};
