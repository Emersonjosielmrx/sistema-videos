import React from 'react';
import {
  Composition,
  Sequence,
  Audio,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import briefing from '../../../trabalhos/futebolcom_ia2_20261120_135351/public/briefing.json';

import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Dono} from './Cena1Dono';
import {Cena2Conversa} from './Cena2Conversa';
import {Cena3Dono} from './Cena3Dono';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont();

// Prepara as palavras para o Karaoke:
// 1. Remove palavras da cena 4 (cartão final não tem legenda).
// 2. Marca quebra de bloco entre falas de cenas diferentes (nunca mistura cenas).
const palavrasKaraoke = briefing.palavras
  .filter((p) => p.cena !== 4)
  .map((p, idx, arr) => ({
    ...p,
    quebraApos: idx < arr.length - 1 && arr[idx + 1].cena !== p.cena,
  }));

const Main: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#000000',
        overflow: 'hidden',
      }}
    >
      {/* 1. Áudio completo da narração sincronizada */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha sonora de apoio com fade in/out e ducking */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          const fadeIn = interpolate(f, [0, 20], [0, 0.11], {
            extrapolateRight: 'clamp',
          });
          const fadeOut = interpolate(f, [860, 901], [1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return fadeIn * fadeOut;
        }}
      />

      {/* 3. Cenas com sequências e transições suaves */}
      {/* Cena 0: Pergunta (0.00s a 4.59s = 138 frames) */}
      <Sequence from={0} durationInFrames={138}>
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono - O Problema (4.24s a 12.27s = 241 frames) */}
      <Sequence from={127} durationInFrames={241}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(
              frame - 127,
              [0, 8],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
            ),
          }}
        >
          <Cena1Dono fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 2: Conversa WhatsApp com IA (11.92s a 18.85s = 208 frames) */}
      <Sequence from={358} durationInFrames={208}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(
              frame - 358,
              [0, 10],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
            ),
            transform: `scale(${interpolate(
              frame - 358,
              [0, 12],
              [0.96, 1.0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
            )})`,
          }}
        >
          <Cena2Conversa fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 3: Dono - O Resultado (18.50s a 26.51s = 240 frames) */}
      <Sequence from={555} durationInFrames={240}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(
              frame - 555,
              [0, 8],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
            ),
          }}
        >
          <Cena3Dono fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 4: Cartão Final de Conversão (26.16s a 30.01s = 116 frames) */}
      <Sequence from={785} durationInFrames={116}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(
              frame - 785,
              [0, 8],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
            ),
          }}
        >
          <Cena4Cartao fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* 4. Barra de Progresso Fina no Topo (Safe Zone: y >= 150) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 5,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          borderRadius: 3,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${Math.min(100, (frame / 900) * 100)}%`,
            backgroundColor: '#E11D48',
            boxShadow: '0 0 10px #E11D48',
          }}
        />
      </div>

      {/* 5. Karaokê Oficial (Cenas 0 a 3, base y <= 1490, safe zone do Reels) — Desmontado estritamente no Cartão Final */}
      {frame < 780 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#E11D48"
          textoDestaque="#FFFFFF"
          base={430}
          tamanho={46}
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
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(30.01 * 30)}
    />
  );
};
