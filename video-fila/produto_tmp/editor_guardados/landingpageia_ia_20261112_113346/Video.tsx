import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import briefing from '../../../trabalhos/landingpageia_ia_20261112_113346/public/briefing.json';
import {Cena0Pergunta} from './Cena0Pergunta';
import {CenaDonoHUD} from './CenaDonoHUD';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont('normal', {
  weights: ['700', '800', '900'],
  subsets: ['latin'],
});

const DURACAO_S = briefing.duracao_s; // 31.78s
const FPS = 30;
const DURATION_FRAMES = Math.ceil(DURACAO_S * FPS); // 954 frames

// Filtra as palavras para não exibir legenda Karaokê no cartão final (cena 4)
// e adiciona quebraForcada na troca de cenas para nunca misturar fim de uma fala com início de outra.
const palavrasKaraoke: PalavraK[] = briefing.palavras
  .filter((w) => w.cena !== 4)
  .map((w, idx, arr) => ({
    p: w.p,
    ini: w.ini,
    fim: w.fim,
    quebraAntes:
      (idx > 0 && arr[idx - 1].cena !== w.cena) ||
      (w.cena === 0 && w.p === 'sem') ||
      (w.cena === 2 && (w.p === 'com' || w.p === 'e' || w.p === 'para' || w.p === 'visita')) ||
      (w.cena === 3 && (w.p === 'página' || w.p === 'pronta' || (w.p === 'uma' && w.ini > 24))),
  }));

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;

  // Top progress bar inside safe zone (y = 140..146)
  const progressPct = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', fontFamily}}>
      {/* Full voiceover audio */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Background music with ducking and fade in/out */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          const sec = f / fps;
          const fadeIn = interpolate(sec, [0, 0.8], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const fadeOut = interpolate(sec, [DURACAO_S - 1.2, DURACAO_S], [1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const baseVol = sec > 27.84 ? 0.16 : 0.09;
          return baseVol * fadeIn * fadeOut;
        }}
      />

      {/* Cena 0: Pergunta (0.00s - 5.17s) */}
      <Sequence from={0} durationInFrames={Math.ceil(5.17 * fps)}>
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono 1 - O Problema (4.82s - 12.85s) */}
      <Sequence
        from={Math.round(4.82 * fps)}
        durationInFrames={Math.ceil((12.85 - 4.82) * fps)}
      >
        <CenaDonoHUD
          cenaN={1}
          videoSrc="dono_1.mp4"
          duracaoCena={12.85 - 4.82}
          fontFamily={fontFamily}
        />
      </Sequence>

      {/* Cena 2: Dono 2 - Como Funciona (12.50s - 20.52s) */}
      <Sequence
        from={Math.round(12.5 * fps)}
        durationInFrames={Math.ceil((20.52 - 12.5) * fps)}
      >
        <CenaDonoHUD
          cenaN={2}
          videoSrc="dono_2.mp4"
          duracaoCena={20.52 - 12.5}
          fontFamily={fontFamily}
        />
      </Sequence>

      {/* Cena 3: Dono 3 - O Resultado (20.17s - 28.19s) */}
      <Sequence
        from={Math.round(20.17 * fps)}
        durationInFrames={Math.ceil((28.19 - 20.17) * fps)}
      >
        <CenaDonoHUD
          cenaN={3}
          videoSrc="dono_3.mp4"
          duracaoCena={28.19 - 20.17}
          fontFamily={fontFamily}
        />
      </Sequence>

      {/* Cena 4: Cartão Final (27.84s - 31.78s) */}
      <Sequence
        from={Math.round(27.84 * fps)}
        durationInFrames={Math.ceil((31.78 - 27.84) * fps)}
      >
        <Cena4Cartao fontFamily={fontFamily} />
      </Sequence>

      {/* Top Progress Bar (y=142, x=60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 142,
          left: 60,
          right: 60,
          height: 6,
          background: 'rgba(255, 255, 255, 0.18)',
          borderRadius: 99,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progressPct}%`,
            height: '100%',
            background: '#F59E0B',
          }}
        />
      </div>

      {/* Legenda Karaokê (oculta no cartão final t >= 27.84s) */}
      {t < 27.84 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={briefing.cores.destaque}
          textoDestaque={briefing.cores.texto_sobre_marca}
          tamanho={42}
          base={360}
          maxLetras={34}
        />
      )}
    </AbsoluteFill>
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
      durationInFrames={DURATION_FRAMES}
    />
  );
};
