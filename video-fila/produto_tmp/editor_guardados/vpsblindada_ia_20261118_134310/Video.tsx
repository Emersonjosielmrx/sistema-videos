import React from 'react';
import {
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import briefing from '../../../trabalhos/vpsblindada_ia_20261118_134310/public/briefing.json';

import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Duração total em frames: 31.04 s * 30 fps = 932 frames
const DURACAO_FRAMES = Math.ceil(briefing.duracao_s * 30);

// Todas as palavras sincronizadas para o Karaokê, incluindo Cena 4 conforme feedback da revisão
const palavrasKaraoke = briefing.palavras as PalavraK[];

export const VideoConteudo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0A0F1D',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* 1. Áudio da Narração Oficial Completa */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha Sonora com Ducking e Fades */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          const fadeIn = interpolate(f, [0, 15], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const fadeOut = interpolate(
            f,
            [durationInFrames - 20, durationInFrames],
            [1, 0],
            {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }
          );
          // Volume sutil com voz (~0.10) e sobe no cartão final (~0.20)
          const baseVol = interpolate(f, [0, 137, 810, 835], [0.1, 0.09, 0.09, 0.2], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return baseVol * fadeIn * fadeOut;
        }}
      />

      {/* 3. Barra de Progresso no Topo (y=150) */}
      <ProgressBar destaque="#0EA5E9" />

      {/* 4. Cenas com Sequências e Overlaps Exatos do Briefing */}

      {/* Cena 0 (0.00s a 4.93s = 148 frames) */}
      <Sequence from={0} durationInFrames={148}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono 1 (4.58s a 11.78s = 216 frames, inicia no frame 137) */}
      <Sequence from={137} durationInFrames={216}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Dono 2 (11.43s a 19.61s = 245 frames, inicia no frame 343) */}
      <Sequence from={343} durationInFrames={245}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono 3 (19.26s a 27.45s = 246 frames, inicia no frame 578) */}
      <Sequence from={578} durationInFrames={246}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final (27.10s a 31.04s = 119 frames, inicia no frame 813) */}
      <Sequence from={813} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* 5. Karaokê Oficial Sincronizado para todo o vídeo (incluindo Cena 4) */}
      <Karaoke
        palavras={palavrasKaraoke}
        fontFamily={fontFamily}
        destaque="#0EA5E9"
        textoDestaque="#FFFFFF"
        base={380}
        tamanho={46}
      />
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoConteudo}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={DURACAO_FRAMES}
    />
  );
};
