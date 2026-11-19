import React from 'react';
import {
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {Karaoke} from '../../lib/karaoke';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import {
  CORES,
  fontFamily,
  PALAVRAS_CENA_0,
  PALAVRAS_CENA_1,
  PALAVRAS_CENA_2,
  PALAVRAS_CENA_3,
} from './constants';
import {ProgressBar} from './ProgressBar';

const DURACAO_S = 30.41;
const FPS = 30;
const TOTAL_FRAMES = Math.ceil(DURACAO_S * FPS); // 913 frames

const MainContent: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: CORES.fundoEscuro,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* 1. Áudio da Narração completa */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha Sonora de Fundo com ducking refinado */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          // Fade in no início
          if (f < 15) {
            return interpolate(f, [0, 15], [0, 0.1]);
          }
          // Fade out nos últimos 15 frames
          if (f > TOTAL_FRAMES - 15) {
            return interpolate(f, [TOTAL_FRAMES - 15, TOTAL_FRAMES], [0.15, 0]);
          }
          // Pausa entre a pergunta e a fala do dono (frames 115 a 195)
          if (f >= 115 && f <= 195) {
            return interpolate(
              f,
              [115, 135, 175, 195],
              [0.1, 0.18, 0.18, 0.1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
            );
          }
          // Pausa no início do cartão final (frames 790 a 810)
          if (f >= 790 && f <= 810) {
            return interpolate(f, [790, 800, 810], [0.1, 0.16, 0.1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
          }
          // Cartão final após a locução (frames 860 em diante)
          if (f >= 860) {
            return 0.18;
          }
          return 0.1;
        }}
      />

      {/* 3. Barra de progresso no topo (y >= 150) */}
      <ProgressBar />

      {/* 4. Sequência de Cenas */}
      {/* Cena 0: Pergunta (0.00s a 5.27s | frames 0 a 158) */}
      <Sequence from={0} durationInFrames={158}>
        <Cena0 />
      </Sequence>

      {/* Cena 1: Dono - O problema (4.92s a 12.64s | frames 148 a 380) */}
      <Sequence from={148} durationInFrames={232}>
        <Cena1 />
      </Sequence>

      {/* Cena 2: Conversa - Como funciona (12.29s a 19.14s | frames 369 a 575) */}
      <Sequence from={369} durationInFrames={206}>
        <Cena2 />
      </Sequence>

      {/* Cena 3: Dono / Avatar IA - O resultado (18.79s a 26.82s | frames 564 a 805) */}
      <Sequence from={564} durationInFrames={241}>
        <Cena3 />
      </Sequence>

      {/* Cena 4: Cartão Final - CTA (26.47s a 30.41s | frames 794 a 913) */}
      <Sequence from={794} durationInFrames={119}>
        <Cena4 />
      </Sequence>

      {/* 5. Karaokê isolado por cena (SEM vazamento entre cenas e NADA no Cartão Final) */}
      {/* Karaokê Cena 0 (0.0s a 4.5s | frames 0 a 135) */}
      {frame >= 0 && frame < 135 && (
        <Karaoke
          palavras={PALAVRAS_CENA_0}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          base={340}
        />
      )}

      {/* Karaokê Cena 1 (6.6s a 12.2s | frames 198 a 366) */}
      {frame >= 198 && frame < 366 && (
        <Karaoke
          palavras={PALAVRAS_CENA_1}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          base={340}
        />
      )}

      {/* Karaokê Cena 2 (12.5s a 18.5s | frames 375 a 555) */}
      {frame >= 375 && frame < 555 && (
        <Karaoke
          palavras={PALAVRAS_CENA_2}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          base={340}
        />
      )}

      {/* Karaokê Cena 3 (18.8s a 26.3s | frames 564 a 790) */}
      {frame >= 564 && frame < 790 && (
        <Karaoke
          palavras={PALAVRAS_CENA_3}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          base={340}
        />
      )}

      {/* CENA 4 (Cartão Final): frames 794 a 913 — NENHUM KARAOKÊ (conforme regra estrita) */}
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainContent}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
