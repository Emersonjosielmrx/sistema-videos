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
import {PALAVRAS_VIDEO} from './palavras';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Trilha sonora ducking calculation
const getTrilhaVolume = (frame: number): number => {
  // Fade out no encerramento (últimos 15 frames)
  if (frame >= 929) {
    return interpolate(frame, [929, 944], [0.22, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  }

  // Encerramento / CTA após a fala (frame 885 a 929): música sobe para dar impacto
  if (frame >= 885) {
    return interpolate(frame, [885, 900], [0.09, 0.22], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  }

  // Intervalos de fala (em frames a 30fps)
  const falas = [
    [9, 110], // Cena 0
    [166, 342], // Cena 1
    [369, 562], // Cena 2
    [614, 806], // Cena 3
    [839, 885], // Cena 4
  ];

  const emFala = falas.some(([ini, fim]) => frame >= ini - 4 && frame <= fim + 4);
  return emFala ? 0.09 : 0.18;
};

// Transições suaves entre cenas com opacidade
const CenaWrapper: React.FC<{
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
        opacity,
      }}
    >
      {children}
    </div>
  );
};

export const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const volumeTrilha = getTrilhaVolume(frame);

  // Palavras para o Karaokê (apenas cenas 0 a 3; cena 4 é o Cartão Final sem karaokê)
  const palavrasKaraoke = PALAVRAS_VIDEO.filter((p) => p.cena < 4);

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
      {/* 1. Áudios: Narração completa contínua + Trilha com Ducking */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio
        src={staticFile('trilha.mp3')}
        volume={() => volumeTrilha}
      />

      {/* 2. Barra de Progresso no Topo (Safe Zone: y=155) */}
      <ProgressBar cor="#14B8A6" />

      {/* 3. Cenas com tempos exatos do briefing */}
      {/* Cena 0: Pergunta (0.00s a 5.12s -> frames 0 a 153) */}
      <Sequence from={0} durationInFrames={153}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono - O problema (4.77s a 12.17s -> frames 143 a 365, dur: 222) */}
      <Sequence from={143} durationInFrames={222}>
        <CenaWrapper durationInFrames={222} fadeInFrames={10}>
          <Cena1 fontFamily={fontFamily} />
        </CenaWrapper>
      </Sequence>

      {/* Cena 2: Veo - Como funciona (11.82s a 20.02s -> frames 354 a 600, dur: 246) */}
      <Sequence from={354} durationInFrames={246}>
        <CenaWrapper durationInFrames={246} fadeInFrames={11}>
          <Cena2 fontFamily={fontFamily} />
        </CenaWrapper>
      </Sequence>

      {/* Cena 3: Dono - O resultado (19.67s a 27.85s -> frames 590 a 835, dur: 245) */}
      <Sequence from={590} durationInFrames={245}>
        <CenaWrapper durationInFrames={245} fadeInFrames={10}>
          <Cena3 fontFamily={fontFamily} />
        </CenaWrapper>
      </Sequence>

      {/* Cena 4: Cartão Final (27.50s a 31.44s -> frames 825 a 944, dur: 119) */}
      <Sequence from={825} durationInFrames={119}>
        <CenaWrapper durationInFrames={119} fadeInFrames={10}>
          <Cena4 fontFamily={fontFamily} />
        </CenaWrapper>
      </Sequence>

      {/* 4. Karaokê Dinâmico Oficial (Base rigorosamente acima de y=1540: base=390 -> base em y=1530) */}
      <Sequence from={0} durationInFrames={825}>
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#14B8A6"
          textoDestaque="#FFFFFF"
          tamanho={42}
          base={390}
          maxLetras={40}
        />
      </Sequence>
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoSegundos = 31.44;
  const fps = 30;
  const duracaoQuadros = Math.ceil(duracaoSegundos * fps); // 944 quadros

  return (
    <Composition
      id="Main"
      component={Main}
      fps={fps}
      width={1080}
      height={1920}
      durationInFrames={duracaoQuadros}
    />
  );
};
