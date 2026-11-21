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

const {fontFamily} = loadFont();

// Barra de progresso discreta no topo da Safe Zone (y = 152)
const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = frame / durationInFrames;

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 60,
        right: 60,
        height: 5,
        borderRadius: 4,
        background: 'rgba(255, 255, 255, 0.18)',
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          background: 'linear-gradient(90deg, #22C55E, #4ADE80)',
          boxShadow: '0 0 10px rgba(34, 197, 94, 0.8)',
        }}
      />
    </div>
  );
};

// Cálculo dinâmico do volume da trilha musical (ducking durante as falas)
const getTrilhaVolume = (f: number) => {
  const t = f / 30;

  // Fade in nos primeiros 15 frames (0.5s)
  const fadeIn = interpolate(f, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Fade out nos últimos 45 frames (1.5s)
  const fadeOut = interpolate(f, [921, 966], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Intervalos de fala oficial
  const isSpeech =
    (t >= 0.25 && t <= 3.6) ||
    (t >= 5.2 && t <= 11.3) ||
    (t >= 12.0 && t <= 19.6) ||
    (t >= 21.3 && t <= 28.1) ||
    (t >= 28.6 && t <= 30.4);

  const baseVol = isSpeech ? 0.09 : 0.22;
  return baseVol * fadeIn * fadeOut;
};

// Palavras para o Karaokê agrupadas por cena, excluindo o cartão final
const palavrasKaraoke = briefing.palavras
  .filter((p) => p.cena < 4)
  .map((p, i, arr) => ({
    ...p,
    quebraApos: p.cena !== arr[i + 1]?.cena,
  }));

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

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
      {/* Áudio contínuo de Narração Oficial */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha de Fundo com Ducking Inteligente */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* Barra de Progresso Superior */}
      <ProgressBar />

      {/* Cena 0 — Pergunta (0.0s a 4.93s) */}
      <Sequence from={0} durationInFrames={148}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1 — Dono: O Problema (4.58s a 11.97s) */}
      <Sequence from={137} durationInFrames={222}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2 — Conversa: Como Funciona (11.62s a 20.77s) */}
      <Sequence from={349} durationInFrames={274}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3 — Dono: O Resultado (20.42s a 28.61s) */}
      <Sequence from={613} durationInFrames={245}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4 — Cartão Final: CTA (28.26s a 32.20s) */}
      <Sequence from={848} durationInFrames={118}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Karaokê Oficial (ativo nas cenas 0 a 3, base y=1560) */}
      {frame < 848 && (
        <Karaoke
          palavras={palavrasKaraoke}
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
      durationInFrames={966}
    />
  );
};
