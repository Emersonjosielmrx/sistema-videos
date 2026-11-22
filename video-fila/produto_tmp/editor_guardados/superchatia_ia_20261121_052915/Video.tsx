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
import {Karaoke} from '../../lib/karaoke';
import {briefing} from './briefing';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Palavras filtradas para o Karaokê (sem legenda no cartão final e quebras por cena)
const palavrasKaraoke = briefing.palavras
  .filter((p) => p.cena !== 4)
  .map((p, idx, arr) => {
    const next = arr[idx + 1];
    return {
      ...p,
      quebraApos: Boolean(p.quebraApos || (next && next.cena !== p.cena)),
      quebraAntes: Boolean(p.quebraAntes || (idx > 0 && arr[idx - 1].cena !== p.cena)),
    };
  });

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Volume da trilha: ~0.10 com fala, fade in no início e fade out no final
  const trilhaVolume = interpolate(
    frame,
    [0, 15, durationInFrames - 30, durationInFrames],
    [0, 0.10, 0.10, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Barra de progresso no topo (y=150)
  const progressPercent = Math.min(100, (frame / durationInFrames) * 100);

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13'}}>
      {/* Áudio: Narração completa contínua desde o frame 0 */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Áudio: Trilha sonora de fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Cena 0: Pergunta (0.00s a 5.63s -> frames 0 a 169) */}
      <Sequence from={0} durationInFrames={169}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Problema (5.28s a 12.34s -> frames 158 a 370) */}
      <Sequence from={158} durationInFrames={212}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Como Funciona (11.99s a 21.19s -> frames 360 a 635) */}
      <Sequence from={360} durationInFrames={276}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado (20.84s a 28.87s -> frames 625 a 866) */}
      <Sequence from={625} durationInFrames={241}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (28.52s a 32.47s -> frames 856 a 975) */}
      <Sequence from={856} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Legenda Karaokê Oficial (y=1560 na base) — estritamente oculta no cartão final */}
      {frame < 856 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#5B6CFF"
          textoDestaque="#FFFFFF"
          tamanho={46}
          base={360}
        />
      )}

      {/* Barra de progresso contínua no topo da Safe Zone (y=150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 3,
          background: 'rgba(255, 255, 255, 0.15)',
          overflow: 'hidden',
          zIndex: 100,
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progressPercent}%`,
            background: 'linear-gradient(90deg, #5B6CFF 0%, #8B98FF 100%)',
            boxShadow: '0 0 10px rgba(91, 108, 255, 0.8)',
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  const duracaoSegundos = briefing.duracao_s; // 32.47 s
  const durationInFrames = Math.ceil(duracaoSegundos * 30); // 975 frames

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
