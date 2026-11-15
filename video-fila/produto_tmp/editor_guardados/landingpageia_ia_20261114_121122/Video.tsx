import React from 'react';
import {
  Composition,
  Sequence,
  Audio,
  staticFile,
  useCurrentFrame,
  interpolate,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import briefingData from './briefing.json';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import {ProgressBar} from './ProgressBar';

const {fontFamily} = loadFont();

const Main: React.FC = () => {
  const frame = useCurrentFrame();

  // Curva de volume inteligente da trilha sonora:
  // ~0.10 com fala, ~0.22 sem fala, fades suaves nas pontas
  const getTrilhaVolume = (f: number) => {
    if (f < 20) {
      return interpolate(f, [0, 20], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    if (f > 910) {
      return interpolate(f, [910, 925], [0.2, 0], {
        extrapolateRight: 'clamp',
      });
    }
    // Outro no cartão final após o término da fala (frame 870+)
    if (f >= 870 && f <= 910) {
      return interpolate(f, [870, 890], [0.1, 0.22], {
        extrapolateRight: 'clamp',
      });
    }
    return 0.1;
  };

  // Palavras para karaokê (sem o cartão final, conforme regra do editor)
  const palavrasKaraoke = briefingData.palavras.filter((p) => p.cena !== 4);

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
      {/* Áudio: Narração completa (voz + dono) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Áudio: Trilha sonora ambiente */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* Cena 0: Pergunta (0.00s a 5.70s | frames 0 a 171) */}
      <Sequence from={0} durationInFrames={171}>
        <Cena0
          fontFamily={fontFamily}
          destaque={briefingData.cores.destaque}
        />
      </Sequence>

      {/* Cena 1: Dono - O Problema (5.35s a 12.98s | frames 160 a 389) */}
      <Sequence from={160} durationInFrames={229}>
        <Cena1
          fontFamily={fontFamily}
          destaque={briefingData.cores.destaque}
        />
      </Sequence>

      {/* Cena 2: Conversa - Como Funciona (12.63s a 19.41s | frames 378 a 582) */}
      <Sequence from={378} durationInFrames={204}>
        <Cena2
          fontFamily={fontFamily}
          destaque={briefingData.cores.destaque}
        />
      </Sequence>

      {/* Cena 3: Dono - O Resultado (19.06s a 27.24s | frames 571 a 817) */}
      <Sequence from={571} durationInFrames={246}>
        <Cena3
          fontFamily={fontFamily}
          destaque={briefingData.cores.destaque}
        />
      </Sequence>

      {/* Cena 4: Cartão Final (26.89s a 30.83s | frames 806 a 925) */}
      <Sequence from={806} durationInFrames={119}>
        <Cena4
          fontFamily={fontFamily}
          destaque={briefingData.cores.destaque}
          marca={briefingData.marca}
          arroba={briefingData.arroba}
        />
      </Sequence>

      {/* Barra de Progresso Fina no Topo (y >= 150) */}
      <ProgressBar color={briefingData.cores.destaque} />

      {/* Karaokê Oficial Sincronizado (oculto no cartão final) */}
      {frame < 806 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={briefingData.cores.destaque}
          textoDestaque="#121216"
          base={360}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoSegundos = briefingData.duracao_s;
  const totalFrames = Math.ceil(duracaoSegundos * 30);

  return (
    <Composition
      id="Main"
      component={Main}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={totalFrames}
    />
  );
};
