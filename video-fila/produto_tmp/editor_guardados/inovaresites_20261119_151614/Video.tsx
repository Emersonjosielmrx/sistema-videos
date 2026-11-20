import React from 'react';
import {
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {
  BRIEFING,
  CORES,
  FPS,
  PALAVRAS_CENA0,
  PALAVRAS_CENA1,
  PALAVRAS_CENA2,
  PALAVRAS_CENA3,
  TOTAL_FRAMES,
} from './constants';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#0F0913',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio principal contínuo */}
      <Audio src={staticFile('narracao.mp3')} volume={1} />

      {/* Trilha de fundo com ducking automático */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          if (f < 15) return interpolate(f, [0, 15], [0, 0.1]);
          if (f > TOTAL_FRAMES - 20) {
            return interpolate(f, [TOTAL_FRAMES - 20, TOTAL_FRAMES], [0.22, 0]);
          }
          if (f >= 775) {
            return 0.22;
          }
          return 0.1;
        }}
      />

      {/* CENA 0: Pergunta / Gancho Inicial (0.0s a 4.81s) */}
      <Sequence from={0} durationInFrames={144}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 1: Dono 1 - O Problema (4.46s a 12.49s) */}
      <Sequence from={134} durationInFrames={241}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 2: Dono 2 - Como Funciona (12.14s a 18.50s) */}
      <Sequence from={364} durationInFrames={191}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 3: Dono 3 - O Resultado (18.15s a 25.43s) */}
      <Sequence from={544} durationInFrames={215}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 4: Cartão Final (24.83s a 29.77s) - Transição suave cobrindo final de Cena 3 */}
      <Sequence from={745} durationInFrames={TOTAL_FRAMES - 745}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Karaokê Dinâmico centralizado na base segura (y = 1560) */}
      {/* Sincronização estrita por cena: nunca vaza texto para a cena seguinte nem para o cartão final */}
      {frame < 134 && (
        <Karaoke
          palavras={PALAVRAS_CENA0}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          base={360}
          tamanho={46}
          maxLetras={36}
        />
      )}

      {frame >= 134 && frame < 364 && (
        <Karaoke
          palavras={PALAVRAS_CENA1}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          base={360}
          tamanho={46}
          maxLetras={36}
        />
      )}

      {frame >= 364 && frame < 544 && (
        <Karaoke
          palavras={PALAVRAS_CENA2}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          base={360}
          tamanho={46}
          maxLetras={36}
        />
      )}

      {frame >= 544 && frame < 765 && (
        <Karaoke
          palavras={PALAVRAS_CENA3}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          base={360}
          tamanho={46}
          maxLetras={36}
        />
      )}

      {/* Barra de Progresso no topo (y = 150) */}
      <ProgressBar />
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainVideo}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
