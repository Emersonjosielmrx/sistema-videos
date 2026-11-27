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
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {briefingData} from './briefingData';
import {ProgressBar} from './ProgressBar';
import {Scene0_Pergunta} from './Scene0_Pergunta';
import {Scene1_DonoProblema} from './Scene1_DonoProblema';
import {Scene2_Conversa} from './Scene2_Conversa';
import {Scene3_DonoResultado} from './Scene3_DonoResultado';
import {Scene4_CartaoFinal} from './Scene4_CartaoFinal';

const {fontFamily} = loadFont('normal', {
  weights: ['500', '600', '700', '800', '900'],
  subsets: ['latin'],
  ignoreTooManyRequestsWarning: true,
});

// Prepare karaoke words: include scene 4 and apply clean breaks between logical clauses
const karaokePalavras: PalavraK[] = briefingData.palavras.map((w, i, arr) => {
  const prox = arr[i + 1];
  const isCenaChange = prox ? prox.cena !== w.cena : true;
  // Natural rhythmic breaks to avoid orphan words like 'E' and preserve balanced single lines
  const isCustomBreak =
    w.p === 'atende,' ||
    w.p === 'vende' ||
    (w.p === 'loja,' && w.cena === 3) ||
    w.p === 'catálogo';

  return {
    p: w.p,
    ini: w.ini,
    fim: w.fim,
    quebraApos: isCenaChange || isCustomBreak,
  };
});

// Dynamic background music volume curve (~0.10 with speech, ~0.22 without speech, fade in/out)
const getTrilhaVolume = (frame: number): number => {
  // Fade in at start
  if (frame < 15) {
    return interpolate(frame, [0, 15], [0, 0.1]);
  }
  // Fade out at very end
  if (frame > 930) {
    return interpolate(frame, [930, 945], [0.22, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  }
  // Louder at final card after voice ends (~frame 885 to 930)
  if (frame >= 885) {
    return 0.22;
  }
  // Brief speech pauses between scenes
  if (
    (frame >= 115 && frame <= 145) ||
    (frame >= 355 && frame <= 385) ||
    (frame >= 585 && frame <= 615) ||
    (frame >= 815 && frame <= 835)
  ) {
    return 0.16;
  }
  // During normal speech
  return 0.09;
};

const TransitionWrapper: React.FC<{
  children: React.ReactNode;
  durationInFrames: number;
  fadeInFrames?: number;
}> = ({children, fadeInFrames = 10}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, fadeInFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity,
      }}
    >
      {children}
    </div>
  );
};

const Main: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: '#0F172A',
        fontFamily,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Audio Layer */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* Scene 0: Pergunta & Gancho (0.0s - 4.98s | frames 0 - 149) */}
      <Sequence from={0} durationInFrames={149}>
        <Scene0_Pergunta />
      </Sequence>

      {/* Scene 1: O Problema - Dono (4.63s - 12.81s | frames 139 - 384) */}
      <Sequence from={139} durationInFrames={245}>
        <TransitionWrapper durationInFrames={245} fadeInFrames={10}>
          <Scene1_DonoProblema />
        </TransitionWrapper>
      </Sequence>

      {/* Scene 2: Como Funciona - Conversa (12.46s - 20.49s | frames 374 - 615) */}
      <Sequence from={374} durationInFrames={241}>
        <TransitionWrapper durationInFrames={241} fadeInFrames={10}>
          <Scene2_Conversa />
        </TransitionWrapper>
      </Sequence>

      {/* Scene 3: O Resultado - Dono (20.14s - 27.88s | frames 604 - 836) */}
      <Sequence from={604} durationInFrames={232}>
        <TransitionWrapper durationInFrames={232} fadeInFrames={10}>
          <Scene3_DonoResultado />
        </TransitionWrapper>
      </Sequence>

      {/* Scene 4: Cartão Final - CTA (27.53s - 31.47s | frames 826 - 945) */}
      <Sequence from={826} durationInFrames={119}>
        <TransitionWrapper durationInFrames={119} fadeInFrames={10}>
          <Scene4_CartaoFinal />
        </TransitionWrapper>
      </Sequence>

      {/* Persistent UI: Top Progress Bar (y=150) */}
      <ProgressBar />

      {/* Persistent UI: Karaoke Subtitles (Anchor base=360 => y=1560, active strictly during scenes 0-3; hidden on final CTA card) */}
      {frame < 826 && (
        <Karaoke
          palavras={karaokePalavras}
          fontFamily={fontFamily}
          destaque="#A78BFA"
          textoDestaque="#121216"
          tamanho={44}
          maxLetras={38}
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
      component={Main}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(briefingData.duracao_s * 30)}
    />
  );
};
