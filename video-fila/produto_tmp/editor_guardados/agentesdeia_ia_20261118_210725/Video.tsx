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
import {BRIEFING} from './briefingData';
import {ProgressBar} from './ProgressBar';
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Problema} from './Cena1Problema';
import {Cena2ComoFunciona} from './Cena2ComoFunciona';
import {Cena3Resultado} from './Cena3Resultado';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont();

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Background music volume ducking: ~0.10 during speaking, ~0.20 on CTA, fade in at start, fade out at end
  const trackVolume = interpolate(
    frame,
    [0, 20, 827, 850, 930, 946],
    [0, 0.1, 0.1, 0.2, 0.2, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  // Filter out scene 4 so Karaoke NEVER appears on the final CTA card
  const palavrasKaraoke = BRIEFING.palavras.filter((p) => p.cena < 4);

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#111827',
        overflow: 'hidden',
        fontFamily: `${fontFamily}, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`,
      }}
    >
      {/* Full Narration Audio */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Background Track with Ducking and Fade In/Out */}
      <Audio src={staticFile('trilha.mp3')} volume={trackVolume} />

      {/* Global Top Progress Bar */}
      <ProgressBar />

      {/* Scene 0: Pergunta (0.0s – 5.03s) */}
      <Sequence from={0} durationInFrames={151}>
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* Scene 1: O Dono - O Problema (4.68s – 12.86s) */}
      <Sequence from={140} durationInFrames={246}>
        <Cena1Problema fontFamily={fontFamily} />
      </Sequence>

      {/* Scene 2: O Dono - Como Funciona (12.51s – 20.09s) */}
      <Sequence from={375} durationInFrames={228}>
        <Cena2ComoFunciona fontFamily={fontFamily} />
      </Sequence>

      {/* Scene 3: O Dono - O Resultado (19.74s – 27.92s) */}
      <Sequence from={592} durationInFrames={246}>
        <Cena3Resultado fontFamily={fontFamily} />
      </Sequence>

      {/* Scene 4: Cartão Final / CTA (27.57s – 31.52s) */}
      <Sequence from={827} durationInFrames={119}>
        <Cena4Cartao fontFamily={fontFamily} />
      </Sequence>

      {/* Global Karaoke: strictly cuts off before Scene 4 (final card) starts */}
      {frame < 827 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#10B981"
          textoDestaque="#FFFFFF"
          tamanho={44}
          base={445}
          maxLetras={50}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoSegundos = BRIEFING.duracao_s; // 31.52 s
  const durationInFrames = Math.ceil(duracaoSegundos * 30); // 946 frames

  return (
    <Composition
      id="Main"
      component={MainVideo}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={durationInFrames}
    />
  );
};
