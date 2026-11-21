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
import {Karaoke} from '../../lib/karaoke';
import briefing from '../../../trabalhos/sintetizerisada_20261120_174409/public/briefing.json';

import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const DURATION_SECONDS = 35.43;
const TOTAL_FRAMES = Math.ceil(DURATION_SECONDS * 30); // 1063 frames

// Karaoke word preparation with semantic grouping and clean line breaks
const rawWords = briefing.palavras;
const palavrasKaraoke: Array<{
  p: string;
  ini: number;
  fim: number;
  cena: number;
  quebraAntes?: boolean;
  quebraApos?: boolean;
  quebraLinha?: boolean;
}> = [];

for (let i = 0; i < rawWords.length; i++) {
  const w = rawWords[i];

  // Exclude scene 4 words so Karaoke never renders on the final card
  if (w.cena === 4) {
    continue;
  }

  // Semantic grouping for Cena 1: combine "o" and "horário" so "O" is not highlighted alone
  if (w.cena === 1 && w.p === 'o' && i + 1 < rawWords.length && rawWords[i + 1].p === 'horário') {
    palavrasKaraoke.push({
      p: 'o horário',
      ini: w.ini,
      fim: rawWords[i + 1].fim,
      cena: 1,
    });
    i++; // skip next word
    continue;
  }

  const copy = {...w};

  // Scene 0: Add question mark to initial question and break before "e você acorda..."
  if (copy.cena === 0 && copy.p === 'vago') {
    copy.p = 'vago?';
  }
  if (copy.cena === 0 && copy.p === 'e' && Math.abs(copy.ini - 1.961) < 0.05) {
    copy.quebraAntes = true;
  }

  // Scene 1: Restructure grouping into 4 clean, complete phrases (fixes orphan 'DA' in q04)
  // Block 1: EU ACORDAVA COM MENSAGENS
  // Block 2: DE CANCELAMENTO DA MADRUGADA
  if (copy.cena === 1 && copy.p === 'de' && Math.abs(copy.ini - 6.592) < 0.05) {
    copy.quebraAntes = true;
  }
  if (copy.cena === 1 && copy.p === 'e' && Math.abs(copy.ini - 8.372) < 0.05) {
    copy.quebraAntes = true;
  }
  if (copy.cena === 1 && copy.p === 'Ninguém') {
    copy.quebraAntes = true;
  }

  // Scene 2: Natural breaks for WhatsApp actions
  if (copy.cena === 2 && copy.p === 'reagenda') {
    copy.quebraAntes = true;
  }
  if (copy.cena === 2 && copy.p === 'sem' && Math.abs(copy.ini - 19.574) < 0.05) {
    copy.quebraAntes = true;
  }

  // Scene 3: Clean transitions
  if (copy.cena === 3 && copy.p === 'e' && Math.abs(copy.ini - 25.455) < 0.05) {
    copy.quebraAntes = true;
  }
  if (copy.cena === 3 && copy.p === 'Eu' && Math.abs(copy.ini - 28.224) < 0.05) {
    copy.quebraAntes = true;
  }

  palavrasKaraoke.push(copy);
}

export const MainComponent: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Progress Bar Width (x=60 to 1020, total width 960px)
  const progressWidth = interpolate(frame, [0, durationInFrames - 1], [0, 960], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Background Audio */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) =>
          interpolate(f, [0, 30, TOTAL_FRAMES - 45, TOTAL_FRAMES], [0, 0.1, 0.1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })
        }
      />

      {/* Cena 0: Pergunta (0.00s to 5.24s) -> from 0, duration 157 frames */}
      <Sequence from={0} durationInFrames={157}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono (4.89s to 12.91s) -> from 147, duration 241 frames */}
      <Sequence from={147} durationInFrames={241}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Conversa (12.56s to 23.13s) -> from 377, duration 317 frames */}
      <Sequence from={377} durationInFrames={317}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Resultado (22.78s to 31.79s) -> from 683, duration 271 frames */}
      <Sequence from={683} durationInFrames={271}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final (31.44s to 35.43s) -> from 943, duration 120 frames */}
      <Sequence from={943} durationInFrames={120}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Karaoke Subtitles (active scenes 0 to 3, hidden in scene 4) */}
      <Sequence from={0} durationInFrames={943}>
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#FFA94D"
          textoDestaque="#1F2937"
          base={460}
          maxLetras={56}
          tamanho={42}
        />
      </Sequence>

      {/* Thin Top Progress Bar at y=150 */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          width: 960,
          height: 6,
          backgroundColor: 'rgba(255, 255, 255, 0.18)',
          borderRadius: 3,
          overflow: 'hidden',
          zIndex: 100,
        }}
      >
        <div
          style={{
            width: progressWidth,
            height: '100%',
            backgroundColor: '#FFA94D',
            borderRadius: 3,
            boxShadow: '0 0 10px #FFA94D',
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
      component={MainComponent}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
