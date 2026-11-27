import React from 'react';
import {
  Audio,
  Composition,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {COLORS} from './types';
import {PALAVRAS_KARAOKE} from './briefingData';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Barra de progresso contínua no topo seguro (y >= 150)
const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = frame / durationInFrames;

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 0,
        width: 1080,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.14)',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          background: `linear-gradient(90deg, ${COLORS.primary} 0%, ${COLORS.accent} 100%)`,
          boxShadow: `0 0 12px ${COLORS.primary}`,
        }}
      />
    </div>
  );
};

// Componente Principal
const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Curva de volume da trilha musical (ducking automático na voz)
  const getTrilhaVolume = (f: number) => {
    // Fade in nos primeiros 15 frames
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.1]);
    }
    // Fade out nos últimos 25 frames
    if (f > durationInFrames - 25) {
      return interpolate(f, [durationInFrames - 25, durationInFrames], [0.18, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    const t = f / 30;
    // Momentos de fala ativa na locução
    const isSpeaking =
      (t >= 0.3 && t <= 3.9) ||
      (t >= 5.4 && t <= 10.2) ||
      (t >= 11.5 && t <= 19.3) ||
      (t >= 20.6 && t <= 26.7) ||
      (t >= 28.0 && t <= 29.5);

    return isSpeaking ? 0.1 : 0.22;
  };

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: '#000000',
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* 1. Áudio da Narração Oficial (do começo ao fim) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha Musical de Fundo com Ducking e Fade in/out */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* 3. Sequências das Cenas (sem repetição de template) */}
      {/* Cena 0: Pergunta (0.0s a 5.31s) */}
      <Sequence from={0} durationInFrames={160}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Problema (4.96s a 11.43s) */}
      <Sequence from={149} durationInFrames={195}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Como Funciona (11.08s a 20.50s) */}
      <Sequence from={332} durationInFrames={284}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado (20.15s a 27.91s) */}
      <Sequence from={604} durationInFrames={234}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final de Agência (27.56s a 31.41s) */}
      <Sequence from={827} durationInFrames={116}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* 4. Barra de Progresso Fina no Topo (y=152) */}
      <ProgressBar />

      {/* 5. Legenda Karaokê Oficial (encerrada antes do Cartão Final) */}
      <Karaoke
        palavras={PALAVRAS_KARAOKE}
        fontFamily={fontFamily}
        destaque={COLORS.primary}
        textoDestaque="#FFFFFF"
        tamanho={46}
        base={360}
      />
    </div>
  );
};

// Exportação da Raiz exigida pelo Remotion
export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainVideo}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(31.41 * 30)}
    />
  );
};
