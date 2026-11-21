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
import {PALAVRAS_KARAOKE} from './palavras';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const DURACAO_S = 35.03;
const TOTAL_FRAMES = Math.ceil(DURACAO_S * 30); // 1051 frames

const MainContent: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Curva de volume da trilha musical conforme manual do editor
  // ~0.10 com fala, ~0.22 sem fala, com fade-in e fade-out
  const getTrilhaVolume = (f: number) => {
    if (f < 10) {
      return interpolate(f, [0, 10], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    if (f < 990) {
      return 0.1;
    }
    if (f < 1020) {
      return interpolate(f, [990, 1020], [0.1, 0.22], {
        extrapolateRight: 'clamp',
      });
    }
    return interpolate(f, [1020, 1051], [0.22, 0.0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  };

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio contínuo oficial de ponta a ponta */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* Cenas com transições calculadas pelos tempos oficiais do briefing */}

      {/* Cena 0: Pergunta (0.00s a 6.92s) */}
      <Sequence from={0} durationInFrames={208}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono - O Problema (6.57s a 14.76s) */}
      <Sequence from={197} durationInFrames={246}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Veo - Como Funciona (14.41s a 23.61s) */}
      <Sequence from={432} durationInFrames={276}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono - O Resultado (23.26s a 31.44s) */}
      <Sequence from={698} durationInFrames={245}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final CTA (31.09s a 35.03s) */}
      <Sequence from={933} durationInFrames={durationInFrames - 933}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso Fina no Topo (Safe Zone: y >= 150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 3,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          overflow: 'hidden',
          zIndex: 95,
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${((frame + 1) / durationInFrames) * 100}%`,
            background: 'linear-gradient(90deg, #1F93FF, #60A5FA)',
            borderRadius: 3,
            boxShadow: '0 0 10px rgba(31, 147, 255, 0.7)',
          }}
        />
      </div>

      {/* Legenda Karaokê Oficial (ativa exclusivamente nas cenas 0 a 3, 100% desligada no CTA final) */}
      {frame < 933 && (
        <Karaoke
          palavras={PALAVRAS_KARAOKE}
          fontFamily={fontFamily}
          destaque="#1F93FF"
          textoDestaque="#FFFFFF"
          tamanho={46}
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
      component={MainContent}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
