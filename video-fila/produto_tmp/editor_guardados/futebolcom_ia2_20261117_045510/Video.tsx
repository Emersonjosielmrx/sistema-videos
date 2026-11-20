import React from 'react';
import {
  Audio,
  Composition,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {getPalavrasFormatadas} from './palavras';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import briefingData from '../../../trabalhos/futebolcom_ia2_20261117_045510/public/briefing.json';

const {fontFamily} = loadFont();

// Configurações e tempos
const DURACAO_TOTAL = 31.39;
const FPS = 30;
const TOTAL_FRAMES = Math.ceil(DURACAO_TOTAL * FPS); // 942 frames

export const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Barra de progresso contínua e fina no topo seguro (y = 154)
  const progresso = interpolate(frame, [0, durationInFrames], [0, 960], {
    extrapolateRight: 'clamp',
  });

  // Volume da trilha com fade in, fade out e ducking durante o vídeo
  const volumeTrilha = interpolate(
    frame,
    [0, 15, durationInFrames - 30, durationInFrames],
    [0, 0.12, 0.12, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: '#000000',
        position: 'relative',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
      }}
    >
      {/* 1. Narração Completa sem cortes */}
      <Audio src={staticFile('narracao.mp3')} volume={1.0} />

      {/* 2. Trilha Sonora de Fundo em volume ideal */}
      <Audio src={staticFile('trilha.mp3')} volume={volumeTrilha} />

      {/* 3. Sequência de Cenas — Tempos rígidos sincronizados com o briefing */}
      {/* Cena 0: 0.0s a 4.15s (125 frames) */}
      <Sequence from={0} durationInFrames={Math.round(4.15 * FPS)}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: 4.15s a 11.98s (235 frames) */}
      <Sequence
        from={Math.round(4.15 * FPS)}
        durationInFrames={Math.round((11.98 - 4.15) * FPS)}
      >
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: 11.98s a 19.71s (232 frames) */}
      <Sequence
        from={Math.round(11.98 * FPS)}
        durationInFrames={Math.round((19.71 - 11.98) * FPS)}
      >
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: 19.71s a 27.54s (235 frames) */}
      <Sequence
        from={Math.round(19.71 * FPS)}
        durationInFrames={Math.round((27.54 - 19.71) * FPS)}
      >
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4 (Cartão Final): 27.54s ao fim (116 frames) */}
      <Sequence
        from={Math.round(27.54 * FPS)}
        durationInFrames={TOTAL_FRAMES - Math.round(27.54 * FPS)}
      >
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* 4. Barra de Progresso no Topo Seguro (y = 152) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          width: 960,
          height: 6,
          backgroundColor: 'rgba(255, 255, 255, 0.2)',
          borderRadius: 3,
          overflow: 'hidden',
          zIndex: 100,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progresso}px`,
            backgroundColor: '#E11D48',
            boxShadow: '0 0 10px #E11D48',
          }}
        />
      </div>

      {/* 5. Karaokê Oficial — Apenas durante as falas das cenas 0 a 3 (frame 0 a 826) */}
      {frame < Math.round(27.54 * FPS) && (
        <Karaoke
          palavras={getPalavrasFormatadas()}
          fontFamily={fontFamily}
          destaque="#E11D48"
          textoDestaque="#FFFFFF"
          tamanho={44}
          base={360}
          maxLetras={32}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={Main}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
