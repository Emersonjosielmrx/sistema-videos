import React from 'react';
import {
  Composition,
  AbsoluteFill,
  Sequence,
  Audio,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {BRIEFING, PALAVRAS_KARAOKE} from './constants';
import {TopBar} from './TopBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Volume inteligente da trilha sonora com ducking durante as falas
const getTrilhaVolume = (frame: number): number => {
  // Fade in inicial
  if (frame < 10) return (frame / 10) * 0.18;
  // Cena 0 fala
  if (frame >= 10 && frame < 92) return 0.10;
  // Pausa entre cena 0 e 1
  if (frame >= 92 && frame < 135) return 0.18;
  // Cena 1 fala (Dono)
  if (frame >= 135 && frame < 350) return 0.10;
  // Pausa entre cena 1 e 2
  if (frame >= 350 && frame < 376) return 0.18;
  // Cena 2 fala
  if (frame >= 376 && frame < 612) return 0.10;
  // Pausa entre cena 2 e 3
  if (frame >= 612 && frame < 652) return 0.18;
  // Cena 3 fala (Dono)
  if (frame >= 652 && frame < 864) return 0.10;
  // Pausa entre cena 3 e 4
  if (frame >= 864 && frame < 890) return 0.18;
  // Fala CTA no cartão final
  if (frame >= 890 && frame < 935) return 0.10;
  // Música do encerramento
  if (frame >= 935 && frame < 980) return 0.22;
  // Fade out final
  if (frame >= 980) return Math.max(0, ((994 - frame) / 14) * 0.22);
  return 0.12;
};

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const trilhaVol = getTrilhaVolume(frame);

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13'}}>
      {/* 1. Narração Completa do Começo */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha de Fundo com Ducking */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVol} />

      {/* 3. Barra de Progresso no Topo (Safe Zone y >= 150) */}
      <TopBar fontFamily={fontFamily} />

      {/* 4. Sequência das Cenas */}
      {/* Cena 0: Pergunta (0.0s a 4.55s) */}
      <Sequence from={0} durationInFrames={137}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono - O Problema (4.20s a 12.38s) */}
      <Sequence from={126} durationInFrames={246}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Conversa WhatsApp 3D - A Solução (12.03s a 21.69s) */}
      <Sequence from={361} durationInFrames={290}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono - O Resultado (21.34s a 29.52s) */}
      <Sequence from={640} durationInFrames={246}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final - CTA (29.17s a 33.11s) */}
      <Sequence from={875} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* 5. Legenda Karaokê (Base y=1560 <= 1580; não exibida no cartão final) */}
      {frame < 875 && (
        <Karaoke
          palavras={PALAVRAS_KARAOKE}
          fontFamily={fontFamily}
          destaque={BRIEFING.cores.destaque}
          textoDestaque={BRIEFING.cores.texto_sobre_marca}
          tamanho={46}
          base={360}
          maxLetras={28}
          pausaQuebra={0.6}
        />
      )}
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  const durationInFrames = Math.ceil(BRIEFING.duracao_s * BRIEFING.fps); // 994 frames

  return (
    <Composition
      id="Main"
      component={MainVideo}
      fps={BRIEFING.fps}
      width={1080}
      height={1920}
      durationInFrames={durationInFrames}
    />
  );
};
