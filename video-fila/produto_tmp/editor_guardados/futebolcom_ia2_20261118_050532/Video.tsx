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
import {Karaoke} from '../../lib/karaoke';
import {PALAVRAS_KARAOKE} from './palavras';
import {CORES} from './types';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Duração total: 29.61s * 30 fps = 888.3 -> 889 frames
const DURATION_IN_FRAMES = 889;

// Envoltório para transição suave com crossfade
const TransitionWrapper: React.FC<{
  children: React.ReactNode;
  durationInFrames: number;
  fadeInFrames?: number;
}> = ({children, durationInFrames, fadeInFrames = 10}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, fadeInFrames], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        inset: 0,
        opacity,
      }}
    >
      {children}
    </div>
  );
};

export const Main: React.FC = () => {
  const frame = useCurrentFrame();

  // Barra de progresso no topo (y = 155, segura dentro de 150 a 1580)
  const progressPercent = interpolate(
    frame,
    [0, DURATION_IN_FRAMES],
    [0, 100],
    {
      extrapolateRight: 'clamp',
    }
  );

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        backgroundColor: CORES.fundoEscuro,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* 1. Áudio da Narração Oficial (do início ao fim) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha Sonora de Fundo com Fade In/Out e volume ajustado */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) =>
          interpolate(
            f,
            [0, 30, DURATION_IN_FRAMES - 45, DURATION_IN_FRAMES],
            [0, 0.1, 0.1, 0],
            {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }
          )
        }
      />

      {/* 3. Sequências das Cenas com Transição Suave */}

      {/* Cena 0: Pergunta / Gancho (0.0s a 4.59s = frames 0 a 138) */}
      <Sequence from={0} durationInFrames={138}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono 1 - O Problema (4.24s a 12.10s = frames 127 a 363, dur 236) */}
      <Sequence from={127} durationInFrames={236}>
        <TransitionWrapper durationInFrames={236} fadeInFrames={11}>
          <Cena1 fontFamily={fontFamily} />
        </TransitionWrapper>
      </Sequence>

      {/* Cena 2: Conversa WhatsApp - Como Funciona (11.75s a 19.28s = frames 352 a 578, dur 226) */}
      <Sequence from={352} durationInFrames={226}>
        <TransitionWrapper durationInFrames={226} fadeInFrames={11}>
          <Cena2 fontFamily={fontFamily} />
        </TransitionWrapper>
      </Sequence>

      {/* Cena 3: Dono 3 - O Resultado (18.93s a 26.12s = frames 568 a 784, dur 216) */}
      <Sequence from={568} durationInFrames={216}>
        <TransitionWrapper durationInFrames={216} fadeInFrames={10}>
          <Cena3 fontFamily={fontFamily} />
        </TransitionWrapper>
      </Sequence>

      {/* Cena 4: Cartão Final - CTA (25.77s a 29.61s = frames 773 a 889, dur 116) */}
      <Sequence from={773} durationInFrames={116}>
        <TransitionWrapper durationInFrames={116} fadeInFrames={11}>
          <Cena4 fontFamily={fontFamily} />
        </TransitionWrapper>
      </Sequence>

      {/* 4. Barra de Progresso Fina no Topo (y = 152 >= 150) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 5,
          borderRadius: 3,
          backgroundColor: 'rgba(255, 255, 255, 0.2)',
          zIndex: 95,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progressPercent}%`,
            backgroundColor: CORES.marca,
            boxShadow: `0 0 10px ${CORES.marca}`,
            borderRadius: 3,
          }}
        />
      </div>

      {/* 5. Legenda Karaokê Oficial (oculta na cena 0 para não disputar atenção com o gancho/cards, e presente nas cenas 1 a 4) */}
      {frame >= 127 && frame < 889 && (
        <Karaoke
          palavras={PALAVRAS_KARAOKE}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          base={360}
          tamanho={46}
          maxLetras={42}
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
      durationInFrames={DURATION_IN_FRAMES}
    />
  );
};
