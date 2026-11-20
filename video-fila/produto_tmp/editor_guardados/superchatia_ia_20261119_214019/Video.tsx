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
import {briefing, palavrasKaraoke} from './briefingData';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Volume da trilha com ducking profissional
  // ~0.10 com fala, ~0.20 no cartão final / pausas, fade in no início e fade out no fim
  const getTrilhaVolume = (f: number) => {
    // Fade in inicial (0 a 30 frames)
    if (f < 30) {
      return interpolate(f, [0, 30], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    // Fade out final (últimos 40 frames)
    if (f > durationInFrames - 40) {
      return interpolate(f, [durationInFrames - 40, durationInFrames], [0.2, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    // Cartão final (frame 943 em diante)
    if (f >= 943) {
      return 0.2;
    }
    // Durante a narração
    return 0.1;
  };

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#000000',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio Oficial: Narração completa sem cortes */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha de fundo com volume ducking */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* Barra de Progresso Fina no Topo (y = 148) */}
      <ProgressBar destaque={briefing.cores.destaque} />

      {/* Sequências de Cenas */}
      {/* Cena 0: Pergunta (0.0s a 4.56s | frames 0 a 137, corte exato para a Cena 1 sem sobreposição) */}
      <Sequence from={0} durationInFrames={137}>
        <Cena0 fontFamily={fontFamily} destaque={briefing.cores.destaque} />
      </Sequence>

      {/* Cena 1: Dono - O Problema (4.56s a 12.74s | frames 137 a 382) */}
      <Sequence from={137} durationInFrames={245}>
        <Cena1 fontFamily={fontFamily} destaque={briefing.cores.destaque} />
      </Sequence>

      {/* Cena 2: Conversa - Como Funciona (12.39s a 23.94s | frames 372 a 718) */}
      <Sequence from={372} durationInFrames={346}>
        <Cena2 fontFamily={fontFamily} destaque={briefing.cores.destaque} />
      </Sequence>

      {/* Cena 3: Dono - O Resultado (23.59s a 31.43s | frames 708 a 943) */}
      <Sequence from={708} durationInFrames={235}>
        <Cena3 fontFamily={fontFamily} destaque={briefing.cores.destaque} />
      </Sequence>

      {/* Cena 4: Cartão Final CTA (31.43s a 35.37s | frames 943 a 1062) */}
      <Sequence from={943} durationInFrames={119}>
        <Cena4
          fontFamily={fontFamily}
          destaque={briefing.cores.destaque}
          arroba={briefing.arroba}
        />
      </Sequence>

      {/* Karaokê Dinâmico Centralizado (ativo até frame 943; no cartão final não mostra legenda conforme EDITOR.md) */}
      {frame < 943 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={briefing.cores.destaque}
          textoDestaque="#FFFFFF"
          tamanho={44}
          base={450}
          maxLetras={28}
          pausaQuebra={0.65}
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
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
