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
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Problema} from './Cena1Problema';
import {Cena2Conversa} from './Cena2Conversa';
import {Cena3Resultado} from './Cena3Resultado';
import {Cena4Cartao} from './Cena4Cartao';
import briefing from '../../../trabalhos/disparoemmassa_ia_20261118_102227/public/briefing.json';

const {fontFamily} = loadFont();

// Durations & Timings in frames (at 30 fps)
// Total duration: 31.53 s -> 946 frames
// Cena 0: 0.00s to 4.21s -> frames 0 to 127
// Cena 1: 3.86s to 11.89s -> frames 116 to 357 (from 116, dur 242)
// Cena 2: 11.54s to 20.50s -> frames 346 to 615 (from 346, dur 270)
// Cena 3: 20.15s to 27.93s -> frames 604 to 838 (from 604, dur 235)
// Cena 4: 27.58s to 31.53s -> frames 827 to 946 (from 827, dur 120)

// Pre-process karaoke words strictly partitioned by scene so no subtitle ever bleeds into another scene
const palavrasCena0: PalavraK[] = (briefing.palavras as any[]).filter((p) => p.cena === 0);
const palavrasCena1: PalavraK[] = (briefing.palavras as any[]).filter((p) => p.cena === 1);
const palavrasCena2: PalavraK[] = (briefing.palavras as any[]).filter((p) => p.cena === 2);
const palavrasCena3: PalavraK[] = (briefing.palavras as any[]).filter((p) => p.cena === 3);

export const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Top progress bar (y=150 in safe zone)
  const progressPercent = Math.min(100, (frame / durationInFrames) * 100);

  // Background music volume calculation
  const trilhaVolume = (f: number) => {
    // Fade in over first 15 frames
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.1]);
    }
    // Fade out over last 20 frames
    if (f > durationInFrames - 20) {
      return interpolate(f, [durationInFrames - 20, durationInFrames], [0.1, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    // Normal talking volume
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
      {/* Audio Tracks */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Scene Sequences */}
      <Sequence from={0} durationInFrames={127}>
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={116} durationInFrames={242}>
        <Cena1Problema fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={346} durationInFrames={270}>
        <Cena2Conversa fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={604} durationInFrames={235}>
        <Cena3Resultado fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={827} durationInFrames={120}>
        <Cena4Cartao fontFamily={fontFamily} />
      </Sequence>

      {/* Top Progress Bar (y=150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 4,
          borderRadius: 2,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          overflow: 'hidden',
          zIndex: 85,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progressPercent}%`,
            backgroundColor: '#22C55E',
            boxShadow: '0 0 8px #22C55E',
          }}
        />
      </div>

      {/* Official Karaoke Subtitles strictly partitioned by scene */}
      {frame >= 0 && frame < 116 && (
        <Karaoke
          palavras={palavrasCena0}
          fontFamily={fontFamily}
          destaque="#22C55E"
          textoDestaque="#111827"
          tamanho={44}
          base={360}
        />
      )}
      {frame >= 116 && frame < 346 && (
        <Karaoke
          palavras={palavrasCena1}
          fontFamily={fontFamily}
          destaque="#22C55E"
          textoDestaque="#111827"
          tamanho={44}
          base={360}
        />
      )}
      {frame >= 346 && frame < 604 && (
        <Karaoke
          palavras={palavrasCena2}
          fontFamily={fontFamily}
          destaque="#22C55E"
          textoDestaque="#111827"
          tamanho={44}
          base={360}
        />
      )}
      {frame >= 604 && frame < 827 && (
        <Karaoke
          palavras={palavrasCena3}
          fontFamily={fontFamily}
          destaque="#22C55E"
          textoDestaque="#111827"
          tamanho={44}
          base={360}
        />
      )}
    </div>
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
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
