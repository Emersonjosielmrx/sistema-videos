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
import {Karaoke} from '../../lib/karaoke';
import briefing from './briefing.json';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  subsets: ['latin'],
  ignoreTooManyRequestsWarning: true,
});

const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Volume for background track with ducking during speech
  const getTrilhaVolume = (f: number) => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    if (f >= 871 && f < 960) {
      return 0.2;
    }
    if (f >= 960) {
      return interpolate(f, [960, durationInFrames], [0.2, 0], {
        extrapolateRight: 'clamp',
      });
    }
    return 0.1;
  };

  // Only show karaoke during spoken narrative scenes (0 to 3), never on final CTA card
  const palavrasKaraoke = briefing.palavras.filter((p) => p.cena !== 4);

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#111827',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Audio: Narração completa */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Audio: Trilha sonora instrumental com ducking e fade */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* Top Progress Bar strictly in Safe Zone (y=150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 3,
          backgroundColor: 'rgba(255, 255, 255, 0.18)',
          overflow: 'hidden',
          zIndex: 100,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${Math.min(100, (frame / (durationInFrames - 1)) * 100)}%`,
            background: 'linear-gradient(90deg, #F59E0B, #FBBF24)',
            boxShadow: '0 0 12px rgba(245, 158, 11, 0.85)',
          }}
        />
      </div>

      {/* Cena 0: Pergunta (0.0s a 5.31s -> frames 0 a 159) */}
      <Sequence from={0} durationInFrames={159}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Problema (4.96s a 12.68s -> frames 149 a 380, dura 231) */}
      <Sequence from={149} durationInFrames={231}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Como Funciona (12.33s a 21.70s -> frames 370 a 651, dura 281) */}
      <Sequence from={370} durationInFrames={281}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado / Dono (21.35s a 29.38s -> frames 640 a 881, dura 241) */}
      <Sequence from={640} durationInFrames={241}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final CTA (29.03s a 32.97s -> frames 871 a 990, dura 119) */}
      <Sequence from={871} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Karaoke oficial na base (bottom 360 -> y=1560) apenas até o início do cartão final */}
      {frame < 871 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#F59E0B"
          textoDestaque="#121216"
          base={360}
          tamanho={46}
        />
      )}
    </div>
  );
};

export const Raiz = () => {
  return (
    <Composition
      id="Main"
      component={Main}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
