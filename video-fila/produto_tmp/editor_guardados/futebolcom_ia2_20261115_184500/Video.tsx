import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  interpolate,
  staticFile,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';

import {Karaoke, PalavraK} from '../../lib/karaoke';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Briefing timing and data
const DURATION_S = 32.28;
const TOTAL_FRAMES = Math.ceil(DURATION_S * 30); // 969 frames

// Raw words list from briefing.json with balanced block breaks (`quebraApos`)
// so NO orphan word ('PRATO.', 'SOBRE') ever wraps to a second line without a pill or below y=1580!
const PALAVRAS_KARAOKE: PalavraK[] = [
  // Cena 0
  {p: 'Perdendo', ini: 0.316, fim: 0.745},
  {p: 'vendas', ini: 0.756, fim: 1.138},
  {p: 'porque', ini: 1.15, fim: 1.416, quebraApos: true},
  {p: 'o', ini: 1.427, fim: 1.485},
  {p: 'cliente', ini: 1.497, fim: 1.925},
  {p: 'tem', ini: 1.937, fim: 2.11},
  {p: 'dúvida', ini: 2.122, fim: 2.492, quebraApos: true},
  {p: 'sobre', ini: 2.504, fim: 2.793},
  {p: 'o', ini: 2.805, fim: 2.851},
  {p: 'prato?', ini: 2.863, fim: 3.337, quebraApos: true},

  // Cena 1
  {p: 'No', ini: 4.412, fim: 4.812},
  {p: 'horário', ini: 4.812, fim: 5.152},
  {p: 'de', ini: 5.152, fim: 5.432},
  {p: 'pico', ini: 5.432, fim: 5.652, quebraApos: true},
  {p: 'do', ini: 5.652, fim: 5.852},
  {p: 'delivery,', ini: 5.852, fim: 6.312},
  {p: 'eu', ini: 6.312, fim: 6.592},
  {p: 'não', ini: 6.592, fim: 6.972, quebraApos: true},
  {p: 'conseguia', ini: 6.972, fim: 7.372},
  {p: 'parar', ini: 7.372, fim: 7.752},
  {p: 'tudo', ini: 7.752, fim: 8.252, quebraApos: true},
  {p: 'para', ini: 8.252, fim: 8.672},
  {p: 'detalhar', ini: 8.672, fim: 10.072},
  {p: 'os', ini: 10.072, fim: 10.512, quebraApos: true},
  {p: 'acompanhamentos', ini: 10.512, fim: 11.092, quebraApos: true},
  {p: 'de', ini: 11.092, fim: 11.352},
  {p: 'cada', ini: 11.352, fim: 11.592},
  {p: 'prato.', ini: 11.592, fim: 11.992, quebraApos: true},

  // Cena 2
  {p: 'Se', ini: 12.571, fim: 12.745},
  {p: 'surge', ini: 12.756, fim: 13.057},
  {p: 'alguma', ini: 13.069, fim: 13.381, quebraApos: true},
  {p: 'pergunta', ini: 13.393, fim: 13.902},
  {p: 'sobre', ini: 13.914, fim: 14.192, quebraApos: true},
  {p: 'a', ini: 14.203, fim: 14.238},
  {p: 'refeição,', ini: 14.25, fim: 14.851, quebraApos: true},
  {p: 'o', ini: 15.118, fim: 15.164},
  {p: 'atendimento', ini: 15.175, fim: 15.777},
  {p: 'com', ini: 15.789, fim: 15.905},
  {p: 'IA', ini: 15.916, fim: 17.108, quebraApos: true},
  {p: 'explica', ini: 17.12, fim: 17.537},
  {p: 'na', ini: 17.548, fim: 17.687},
  {p: 'hora', ini: 17.699, fim: 17.965, quebraApos: true},
  {p: 'enquanto', ini: 18.0, fim: 18.37},
  {p: 'o', ini: 18.382, fim: 18.405},
  {p: 'cliente', ini: 18.416, fim: 18.74, quebraApos: true},
  {p: 'escolhe', ini: 18.752, fim: 19.145},
  {p: 'pelo', ini: 19.157, fim: 19.342},
  {p: 'celular.', ini: 19.354, fim: 19.84, quebraApos: true},

  // Cena 3
  {p: 'Agora', ini: 20.764, fim: 21.524},
  {p: 'eu', ini: 21.524, fim: 21.784},
  {p: 'recebo', ini: 21.784, fim: 22.324, quebraApos: true},
  {p: 'o', ini: 22.324, fim: 22.524},
  {p: 'pedido', ini: 22.524, fim: 22.964},
  {p: 'direto', ini: 22.964, fim: 23.444, quebraApos: true},
  {p: 'no', ini: 23.444, fim: 23.544},
  {p: 'WhatsApp', ini: 23.544, fim: 24.164},
  {p: 'com', ini: 24.164, fim: 24.724, quebraApos: true},
  {p: 'o', ini: 24.724, fim: 24.884},
  {p: 'cliente', ini: 24.884, fim: 25.524},
  {p: 'seguro', ini: 25.524, fim: 25.924, quebraApos: true},
  {p: 'da', ini: 25.924, fim: 26.264},
  {p: 'escolha', ini: 26.264, fim: 26.744},
  {p: 'que', ini: 26.744, fim: 26.864},
  {p: 'fez', ini: 26.864, fim: 27.064, quebraApos: true},
  {p: 'no', ini: 27.064, fim: 27.244},
  {p: 'cardápio.', ini: 27.244, fim: 27.864, quebraApos: true},

  // Cena 4 (CTA final)
  {p: 'Chame', ini: 28.923, fim: 29.259, quebraAntes: true},
  {p: 'a', ini: 29.271, fim: 29.328},
  {p: 'gente', ini: 29.34, fim: 29.652},
  {p: 'no', ini: 29.664, fim: 29.757},
  {p: 'direct.', ini: 29.768, fim: 30.358, quebraApos: true},
];

// Dynamic music volume calculation: ducking to 0.10 during voice, 0.22 during gaps
const getTrilhaVolume = (f: number): number => {
  const s = f / 30;

  // Fade in at start (0 to 15 frames)
  let baseVol = 0.22;
  if (f < 15) {
    baseVol = interpolate(f, [0, 15], [0, 0.22], {extrapolateRight: 'clamp'});
  }
  // Fade out at end (last 30 frames: 939 to 969)
  if (f > TOTAL_FRAMES - 30) {
    baseVol = interpolate(f, [TOTAL_FRAMES - 30, TOTAL_FRAMES], [0.22, 0], {
      extrapolateLeft: 'clamp',
    });
  }

  // Voice activity intervals
  const isSpeaking =
    (s >= 0.25 && s <= 3.4) ||
    (s >= 4.35 && s <= 12.1) ||
    (s >= 12.5 && s <= 19.9) ||
    (s >= 20.7 && s <= 28.0) ||
    (s >= 28.8 && s <= 30.4);

  return isSpeaking ? Math.min(baseVol, 0.1) : baseVol;
};

const MainVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: '#000000'}}>
      {/* Audio Tracks */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => getTrilhaVolume(f)}
      />

      {/* Persistent Safe Zone Progress Bar (y=152) */}
      <ProgressBar
        totalFrames={TOTAL_FRAMES}
        corMarca="#E11D48"
        corApoio="#FACC15"
      />

      {/* Cenas com sequências sincronizadas */}
      {/* Cena 0: Pergunta / Gancho (0.00s a 4.76s -> frames 0 a 143) */}
      <Sequence from={0} durationInFrames={143}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono - O Problema (4.41s a 12.43s -> from frame 132, duration 241) */}
      <Sequence from={132} durationInFrames={241}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Conversa - Como Funciona (12.08s a 21.11s -> from frame 362, duration 271) */}
      <Sequence from={362} durationInFrames={271}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono - O Resultado (20.76s a 28.78s -> from frame 623, duration 241) */}
      <Sequence from={623} durationInFrames={241}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (28.43s a 32.28s -> from frame 853, duration 116) */}
      <Sequence from={853} durationInFrames={116}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Karaoke Subtitles: active in Scenes 0 to 3 (hidden in final CTA card per EDITOR.md), anchored at y=1540 (base=380) */}
      <Sequence from={0} durationInFrames={853}>
        <Karaoke
          palavras={PALAVRAS_KARAOKE}
          fontFamily={fontFamily}
          destaque="#E11D48"
          textoDestaque="#FFFFFF"
          tamanho={42}
          base={380}
          maxLetras={24}
        />
      </Sequence>
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
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
