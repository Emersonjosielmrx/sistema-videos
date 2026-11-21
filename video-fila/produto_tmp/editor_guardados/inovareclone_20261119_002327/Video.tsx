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
import {CORES, TOTAL_FRAMES} from './constants';
import {ProgressBar} from './ProgressBar';
import {PALAVRAS_KARAOKE} from './palavras';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Volume da trilha de fundo com fade in, volume com fala e fade out no CTA
  const getTrilhaVolume = (f: number) => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.10], {extrapolateRight: 'clamp'});
    }
    if (f >= 850 && f < 920) {
      return interpolate(f, [850, 880], [0.10, 0.18], {
        extrapolateRight: 'clamp',
      });
    }
    if (f >= 920) {
      return interpolate(f, [920, 951], [0.18, 0], {
        extrapolateRight: 'clamp',
      });
    }
    return 0.10;
  };

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: CORES.fundoEscuro,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* ÁUDIO GLOBAL */}
      {/* 1. Narração completa com voz do dono e locução */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha sonora de fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume(frame)} />

      {/* CENAS DO VÍDEO (respeitando ini e fim com transições) */}
      {/* Cena 0: Pergunta (0.0s a 4.43s | Frames 0 a 133) */}
      <Sequence from={0} durationInFrames={133}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono 1 - O Problema (4.08s a 12.26s | Frames 122 a 368) */}
      <Sequence from={122} durationInFrames={246}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Veo - Como Funciona (11.91s a 20.30s | Frames 357 a 609) */}
      <Sequence from={357} durationInFrames={252}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono 3 - O Resultado (19.95s a 28.13s | Frames 599 a 844) */}
      <Sequence from={599} durationInFrames={246}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final CTA (27.78s a 31.72s | Frames 833 a 952) */}
      <Sequence from={833} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* ELEMENTOS GLOBAIS DE SOBREPOSIÇÃO */}
      {/* Barra de Progresso no Topo (y >= 150) */}
      <ProgressBar />

      {/* Karaokê Oficial (apenas cenas 0 a 3, não exibido no cartão final) */}
      {frame < 833 && (
        <Karaoke
          palavras={PALAVRAS_KARAOKE}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          base={360}
          tamanho={46}
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
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
