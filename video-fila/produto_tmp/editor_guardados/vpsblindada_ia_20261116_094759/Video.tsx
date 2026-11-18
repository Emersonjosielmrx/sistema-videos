import React from 'react';
import {
  Audio,
  Composition,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {BRIEFING, PALAVRAS_KARAOKE} from './data';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Controle dinâmico de volume da trilha musical (ducking com fala)
const getTrilhaVolume = (frame: number): number => {
  // Fade out nos últimos 35 frames do vídeo
  if (frame > 912) {
    return Math.max(0, (947 - frame) / 35) * 0.22;
  }
  // Trechos onde há voz ativa (volume mais baixo da música)
  const intervalDeVoz = [
    [9, 104], // Cena 0: 0.318s a 3.443s
    [137, 361], // Cena 1: 4.576s a 12.016s
    [382, 565], // Cena 2: 12.729s a 18.835s
    [620, 823], // Cena 3: 20.678s a 27.418s
    [843, 888], // Cena 4: 28.094s a 29.585s
  ];
  const comVoz = intervalDeVoz.some(([ini, fim]) => frame >= ini - 4 && frame <= fim + 4);
  return comVoz ? 0.10 : 0.22;
};

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: BRIEFING.cores.fundo_escuro,
        fontFamily,
        overflow: 'hidden',
      }}
    >
      {/* Áudio: Narração completa (voz da narradora + voz do dono) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Áudio: Trilha sonora de fundo com ducking */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* Sequências de Cenas */}
      {/* Cena 0: Pergunta (0.00s a 4.91s) */}
      <Sequence from={0} durationInFrames={147}>
        <Cena0 />
      </Sequence>

      {/* Cena 1: Dono 1 - O problema (4.56s a 12.59s) */}
      <Sequence from={137} durationInFrames={241}>
        <Cena1 />
      </Sequence>

      {/* Cena 2: Veo - Como funciona (12.24s a 20.12s) */}
      <Sequence from={367} durationInFrames={237}>
        <Cena2 />
      </Sequence>

      {/* Cena 3: Dono 3 - O resultado (19.77s a 27.95s) */}
      <Sequence from={593} durationInFrames={246}>
        <Cena3 />
      </Sequence>

      {/* Cena 4: Cartão final com CTA (27.60s a 31.55s) */}
      <Sequence from={828} durationInFrames={119}>
        <Cena4 />
      </Sequence>

      {/* Barra de progresso contínua no topo (y=155) */}
      <ProgressBar />

      {/* Karaokê oficial da biblioteca (ativo nas cenas 0 a 3, desligado no cartão final) */}
      {frame < 828 && (
        <Karaoke
          palavras={PALAVRAS_KARAOKE}
          fontFamily={fontFamily}
          destaque={BRIEFING.cores.destaque}
          textoDestaque="#FFFFFF"
          tamanho={46}
          base={420}
          maxLetras={28}
          pausaQuebra={0.6}
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
      durationInFrames={BRIEFING.totalFrames}
    />
  );
};
