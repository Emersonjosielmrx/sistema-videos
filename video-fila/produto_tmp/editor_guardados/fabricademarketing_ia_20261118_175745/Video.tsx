import React from 'react';
import {Audio, Composition, Sequence, staticFile} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import briefing from './briefing.json';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  subsets: ['latin'],
  ignoreTooManyRequestsWarning: true,
});

// Prepare words for Karaoke: scenes 0, 1, 2, 3 (exclude scene 4)
const palavrasKaraoke: PalavraK[] = briefing.palavras
  .filter((w) => w.cena < 4)
  .map((w, idx, arr) => {
    const isEndOfCena = idx + 1 < arr.length && arr[idx + 1].cena !== w.cena;
    return {
      p: w.p,
      ini: w.ini,
      fim: w.fim,
      quebraApos: isEndOfCena,
    };
  });

const MainVideo: React.FC = () => {
  const getTrilhaVolume = (f: number) => {
    // Fade in at the start
    if (f < 20) {
      return (f / 20) * 0.1;
    }
    // After voice ends in the final scene, boost volume slightly, then fade out at the very end
    if (f > 855) {
      if (f > 895) {
        return Math.max(0, ((912 - f) / 17) * 0.22);
      }
      return 0.22;
    }
    return 0.1;
  };

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
      {/* Background Audio & Narration */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* Persistent Safe-Zone Progress Bar */}
      <ProgressBar />

      {/* Video Scenes with smooth agency transitions */}
      <Sequence from={0} durationInFrames={148}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={137} durationInFrames={230}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={356} durationInFrames={233}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={578} durationInFrames={226}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={793} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Dynamic Synced Karaoke (excluded from final card) */}
      <Karaoke
        palavras={palavrasKaraoke}
        fontFamily={fontFamily}
        destaque="#F472B6"
        textoDestaque="#111827"
        tamanho={46}
        base={360}
      />
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoSegundos = briefing.duracao_s || 30.38;
  const durationInFrames = Math.ceil(duracaoSegundos * 30);

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
