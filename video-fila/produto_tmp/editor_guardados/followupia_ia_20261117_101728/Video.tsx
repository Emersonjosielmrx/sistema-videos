import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import briefing from '../../../trabalhos/followupia_ia_20261117_101728/public/briefing.json';
import {Karaoke} from '../../lib/karaoke';
import {ProgressBar} from './ProgressBar';
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Dono} from './Cena1Dono';
import {Cena2Veo} from './Cena2Veo';
import {Cena3Dono} from './Cena3Dono';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont();

const FPS = 30;
const DURACAO_S = briefing.duracao_s; // 31.51s
const TOTAL_FRAMES = Math.ceil(DURACAO_S * FPS); // 946 frames

// Frame markers based on briefing scene timing
const F_CENA0_INI = 0;
const F_CENA1_INI = Math.round(briefing.cenas[1].ini * FPS); // 132 (4.39s)
const F_CENA2_INI = Math.round(briefing.cenas[2].ini * FPS); // 367 (12.22s)
const F_CENA3_INI = Math.round(briefing.cenas[3].ini * FPS); // 592 (19.73s)
const F_CENA4_INI = Math.round(briefing.cenas[4].ini * FPS); // 827 (27.56s)

const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Background music volume calculation:
  // ~0.10 with narration, with subtle fade-in and fade-out
  const trilhaVolume = interpolate(
    frame,
    [0, 15, durationInFrames - 30, durationInFrames],
    [0, 0.1, 0.1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Filter out final card scene (cena 4) and insert quebraApos at scene and semantic boundaries
  const palavrasKaraoke = briefing.palavras
    .filter((p) => p.cena !== 4)
    .map((p, idx, arr) => {
      const isEndOfScene = idx === arr.length - 1 || arr[idx + 1].cena !== p.cena;
      // Break between "desatenção" and "e" in scene 3 to keep sentences clean
      const isSemanticBreak = p.p.toLowerCase().includes('desatenção');
      return {
        ...p,
        quebraApos: isEndOfScene || isSemanticBreak || undefined,
      };
    });

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', fontFamily}}>
      {/* 1. Global Narration Audio */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Background Track with Ducked Volume */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* 3. Scene Sequences */}
      {/* Cena 0: Pergunta (0.0s - 4.39s) */}
      <Sequence
        from={F_CENA0_INI}
        durationInFrames={F_CENA1_INI - F_CENA0_INI + 8}
      >
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono 1 - O Problema (4.39s - 12.22s) */}
      <Sequence
        from={F_CENA1_INI}
        durationInFrames={F_CENA2_INI - F_CENA1_INI + 8}
      >
        <Cena1Dono fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Veo - A Solução / Mockup WhatsApp (12.22s - 19.73s) */}
      <Sequence
        from={F_CENA2_INI}
        durationInFrames={F_CENA3_INI - F_CENA2_INI + 8}
      >
        <Cena2Veo fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono 2 - O Resultado (19.73s - 27.56s) */}
      <Sequence
        from={F_CENA3_INI}
        durationInFrames={F_CENA4_INI - F_CENA3_INI + 8}
      >
        <Cena3Dono fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (27.56s - 31.51s) */}
      <Sequence
        from={F_CENA4_INI}
        durationInFrames={durationInFrames - F_CENA4_INI}
      >
        <Cena4Cartao fontFamily={fontFamily} />
      </Sequence>

      {/* 4. Top Progress Bar (y=152) */}
      <ProgressBar cor={briefing.cores.destaque} altura={8} y={152} />

      {/* 5. Synchronized Karaoke Subtitles (Cenas 0 a 3, disappears when Scene 4 begins) */}
      {frame < F_CENA4_INI && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={briefing.cores.destaque}
          textoDestaque={briefing.cores.texto_sobre_marca}
          tamanho={46}
          base={360}
        />
      )}
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={Main}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
