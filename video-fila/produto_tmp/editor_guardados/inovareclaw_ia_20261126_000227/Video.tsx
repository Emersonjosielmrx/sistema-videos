import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import {DADOS_VIDEO, PALAVRAS_KARAOKE} from './dados';

const {fontFamily} = loadFont();

// Função de ducking suave para a trilha musical
const getTrilhaVolume = (frame: number): number => {
  const t = frame / 30;
  // Fade in inicial e fade out final
  if (t < 0.4) {
    return interpolate(t, [0, 0.4], [0, 0.18], {extrapolateRight: 'clamp'});
  }
  if (t > 32.3) {
    return interpolate(t, [32.3, 33.34], [0.18, 0], {extrapolateRight: 'clamp'});
  }

  // Intervalos de fala (volume reduz para ~0.10) vs pausas (~0.20)
  const isFala =
    (t >= 0.3 && t <= 5.15) ||
    (t >= 7.0 && t <= 13.8) ||
    (t >= 15.1 && t <= 21.6) ||
    (t >= 22.7 && t <= 28.95) ||
    (t >= 29.8 && t <= 31.4);

  return isFala ? 0.1 : 0.2;
};

// Barra de progresso no topo (y=160)
const BarraProgresso: React.FC<{frame: number; totalFrames: number}> = ({
  frame,
  totalFrames,
}) => {
  const progresso = Math.min(100, Math.max(0, (frame / totalFrames) * 100));

  return (
    <div
      style={{
        position: 'absolute',
        top: 158,
        left: 70,
        right: 90,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        borderRadius: 3,
        overflow: 'hidden',
        zIndex: 100,
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
      }}
    >
      <div
        style={{
          width: `${progresso}%`,
          height: '100%',
          background: 'linear-gradient(90deg, #7C3AED 0%, #A78BFA 100%)',
          borderRadius: 3,
          boxShadow: '0 0 10px rgba(124, 58, 237, 0.8)',
        }}
      />
    </div>
  );
};

// Wrapper para transição com fade suave
const CenaFade: React.FC<{
  children: React.ReactNode;
  durationInFrames: number;
  fadeInFrames?: number;
  fadeOutFrames?: number;
}> = ({children, durationInFrames, fadeInFrames = 10, fadeOutFrames = 10}) => {
  const frame = useCurrentFrame();

  const opacityIn =
    fadeInFrames > 0
      ? interpolate(frame, [0, fadeInFrames], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 1;

  const opacityOut =
    fadeOutFrames > 0
      ? interpolate(
          frame,
          [durationInFrames - fadeOutFrames, durationInFrames],
          [1, 0],
          {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
        )
      : 1;

  const opacity = Math.min(opacityIn, opacityOut);

  return (
    <AbsoluteFill style={{opacity, backgroundColor: '#0B0D13'}}>
      {children}
    </AbsoluteFill>
  );
};

export const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13', overflow: 'hidden'}}>
      {/* Trilha Sonora com Ducking */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => getTrilhaVolume(f)}
      />

      {/* Narração Completa */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Cena 0: Pergunta (0.00s a 6.59s = 198 frames) */}
      <Sequence from={0} durationInFrames={198}>
        <CenaFade durationInFrames={198} fadeInFrames={0} fadeOutFrames={11}>
          <Cena0 fontFamily={fontFamily} />
        </CenaFade>
      </Sequence>

      {/* Cena 1: Dono 1 - O Problema (6.24s a 14.42s = frames 187 a 433, dur 246) */}
      <Sequence from={187} durationInFrames={246}>
        <CenaFade durationInFrames={246} fadeInFrames={11} fadeOutFrames={11}>
          <Cena1 fontFamily={fontFamily} />
        </CenaFade>
      </Sequence>

      {/* Cena 2: Dono 2 - Como Funciona (14.07s a 22.25s = frames 422 a 668, dur 246) */}
      <Sequence from={422} durationInFrames={246}>
        <CenaFade durationInFrames={246} fadeInFrames={11} fadeOutFrames={11}>
          <Cena2 fontFamily={fontFamily} />
        </CenaFade>
      </Sequence>

      {/* Cena 3: Dono 3 - O Resultado (21.90s a 29.74s = frames 657 a 892, dur 235) */}
      <Sequence from={657} durationInFrames={235}>
        <CenaFade durationInFrames={235} fadeInFrames={11} fadeOutFrames={10}>
          <Cena3 fontFamily={fontFamily} />
        </CenaFade>
      </Sequence>

      {/* Cena 4: Cartão Final CTA (29.39s a 33.34s = frames 882 a 1001, dur 119) */}
      <Sequence from={882} durationInFrames={119}>
        <CenaFade durationInFrames={119} fadeInFrames={10} fadeOutFrames={0}>
          <Cena4 fontFamily={fontFamily} />
        </CenaFade>
      </Sequence>

      {/* Barra de Progresso Fina no Topo */}
      <BarraProgresso frame={frame} totalFrames={durationInFrames} />

      {/* Legenda Karaokê pronta (apenas até frame 881, proibida no cartão final) */}
      {frame < 882 && (
        <Karaoke
          palavras={PALAVRAS_KARAOKE}
          fontFamily={fontFamily}
          destaque="#7C3AED"
          textoDestaque="#FFFFFF"
          tamanho={46}
          base={360}
          maxLetras={42}
        />
      )}
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoPrincipal}
      fps={DADOS_VIDEO.fps}
      width={1080}
      height={1920}
      durationInFrames={DADOS_VIDEO.totalFrames}
    />
  );
};
