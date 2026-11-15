import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import briefing from './briefing.json';
import {THEME} from './theme';
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Desafio} from './Cena1Desafio';
import {Cena2ComoFunciona} from './Cena2ComoFunciona';
import {Cena3Dono} from './Cena3Dono';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont();

const DURATION_FRAMES = Math.ceil(briefing.duracao_s * 30); // 976 frames

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Progress bar calculation
  const progress = interpolate(frame, [0, DURATION_FRAMES - 1], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Filter out final card from karaoke as instructed in EDITOR.md
  const palavrasKaraoke = briefing.palavras.filter((p) => p.cena !== 4);

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.fundoEscuro}}>
      {/* ─── AUDIO ─── */}
      {/* Full master narration (including owner's voice) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Background soundtrack: ducked to ~0.09 during speech, ~0.22 at start/end */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) =>
          interpolate(
            f,
            [0, 10, 20, 915, 930, 960, 976],
            [0, 0.22, 0.09, 0.09, 0.22, 0.22, 0],
            {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }
          )
        }
      />

      {/* ─── SCENE SEQUENCES ─── */}
      {/* Cena 0: Pergunta (0.0s to 6.08s -> frames 0 to 183) */}
      <Sequence from={0} durationInFrames={183}>
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Desafio (5.73s to 12.94s -> frames 172 to 388) */}
      <Sequence from={172} durationInFrames={217}>
        <Cena1Desafio fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Como Funciona (12.59s to 21.24s -> frames 378 to 637) */}
      <Sequence from={378} durationInFrames={260}>
        <Cena2ComoFunciona fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono / Prova (20.89s to 28.92s -> frames 627 to 868) */}
      <Sequence from={627} durationInFrames={242}>
        <Cena3Dono fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (28.57s to 32.52s -> frames 857 to 976) */}
      <Sequence from={857} durationInFrames={119}>
        <Cena4Cartao fontFamily={fontFamily} />
      </Sequence>

      {/* ─── KARAOKE SUBTITLE ─── */}
      {/* Active strictly during scenes 0 to 3 (frames 0 to 857). Never shown on final card! */}
      <Sequence from={0} durationInFrames={857}>
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={THEME.colors.destaque}
          textoDestaque="#FFFFFF"
          base={360}
          tamanho={46}
        />
      </Sequence>

      {/* ─── TOP PROGRESS BAR ─── */}
      {/* Safe zone compliant: positioned at y = 152 */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          height: 4,
          borderRadius: 2,
          backgroundColor: 'rgba(255, 255, 255, 0.16)',
          overflow: 'hidden',
          zIndex: 100,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progress}%`,
            background: `linear-gradient(90deg, ${THEME.colors.marca}, ${THEME.colors.destaqueCyan})`,
            boxShadow: `0 0 10px ${THEME.colors.destaqueCyan}`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainVideo}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={DURATION_FRAMES}
    />
  );
};
