import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import briefing from '../../../trabalhos/vpsblindada_ia_20261117_122241/public/briefing.json';

const {fontFamily} = loadFont();

const FPS = 30;
const DURACAO_S = 28.97;
const TOTAL_FRAMES = Math.ceil(DURACAO_S * FPS); // 870 frames

// Filtra palavras para o Karaokê não aparecer na cena do cartão final (cena 4)
// e adiciona quebras semânticas precisas para evitar palavras órfãs e recortes incompletos
const palavrasKaraoke: PalavraK[] = (briefing.palavras as PalavraK[])
  .filter((p: any) => (p as any).cena !== 4)
  .map((p: any) => {
    const w: PalavraK = {...p};
    if (w.p === 'descobre' && (p as any).cena === 0) w.quebraAntes = true;
    if (w.p === 'Um' && (p as any).cena === 1) w.quebraAntes = true;
    if (w.p === 'minha' && (p as any).cena === 1) w.quebraAntes = true;
    if (w.p === 'quando' && (p as any).cena === 1) w.quebraAntes = true;
    if (w.p === 'A' && (p as any).cena === 2) w.quebraAntes = true;
    if (w.p === 'que' && (p as any).cena === 2) w.quebraAntes = true;
    if (w.p === 'e' && w.ini > 15.5 && (p as any).cena === 2) w.quebraAntes = true;
    if (w.p === 'Agora' && (p as any).cena === 3) w.quebraAntes = true;
    if (w.p === 'conto' && (p as any).cena === 3) w.quebraAntes = true;
    if (w.p === 'robô' && (p as any).cena === 3) w.quebraAntes = true;
    return w;
  });

const VideoContent: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Trilha sonora de fundo:
  // Volume ~0.10 durante a fala, ~0.22 no final sem fala, com fade in e fade out
  const trilhaVolume = interpolate(
    frame,
    [0, 15, 26 * FPS, 27.5 * FPS, durationInFrames - 15, durationInFrames],
    [0, 0.1, 0.1, 0.22, 0.22, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  return (
    <AbsoluteFill style={{backgroundColor: '#0B1120'}}>
      {/* Áudio Oficial: Narração completa (voz + dono) */}
      <Audio src={staticFile('narracao.mp3')} volume={1} />

      {/* Áudio Oficial: Trilha de fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Cenas com tempos exatos do briefing */}
      {/* Cena 0: Pergunta (0.00s a 4.86s | frames 0 a 146) */}
      <Sequence from={0} durationInFrames={146}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono - O Problema (4.51s a 12.21s | frames 135 a 366) */}
      <Sequence from={135} durationInFrames={231}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Conversa - Como Funciona (11.86s a 18.92s | frames 356 a 568) */}
      <Sequence from={356} durationInFrames={212}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono - O Resultado (18.57s a 25.37s | frames 557 a 761) */}
      <Sequence from={557} durationInFrames={204}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final - CTA (25.02s a 28.97s | frames 751 a 119) */}
      <Sequence from={751} durationInFrames={durationInFrames - 751}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Karaokê Oficial de Alto Contraste ancorado pela base em y=1550 (Safe Zone: base=370, y <= 1580) */}
      {/* Desaparece rigorosamente no cartão final (frame 751 em diante) */}
      {frame < 751 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#0EA5E9"
          textoDestaque="#0B1120"
          tamanho={46}
          base={370}
          maxLetras={40}
        />
      )}

      {/* Barra de Progresso Fina no Topo (Safe Zone: y=150) */}
      <ProgressBar color="#0EA5E9" />
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoContent}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
