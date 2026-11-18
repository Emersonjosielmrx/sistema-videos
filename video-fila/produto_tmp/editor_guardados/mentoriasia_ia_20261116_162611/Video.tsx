import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {BRIEFING} from './data';
import {ProgressBar} from './ProgressBar';
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Dono} from './Cena1Dono';
import {Cena2Conversa} from './Cena2Conversa';
import {Cena3Dono} from './Cena3Dono';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont('normal', {
  weights: ['400', '600', '700', '800', '900']
});

const MainVideo: React.FC = () => {
  // Palavras para o Karaokê (apenas até a cena 3, pois o cartão final não deve ter karaokê)
  const palavrasKaraoke = BRIEFING.palavras.filter((p) => p.cena < 4);

  return (
    <AbsoluteFill style={{backgroundColor: BRIEFING.cores.fundo_escuro}}>
      {/* 1. Áudio da Locução Completa */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha Sonora de Fundo com volume equilibrado e fade in/out */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) =>
          interpolate(
            f,
            [0, 30, BRIEFING.totalFrames - 45, BRIEFING.totalFrames],
            [0, 0.10, 0.10, 0],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
          )
        }
      />

      {/* 3. Barra de Progresso no Topo (Safe Zone y=155) */}
      <ProgressBar totalFrames={BRIEFING.totalFrames} />

      {/* 4. Cenas em Sequences com tempos precisos do briefing */}
      {/* Cena 0: Pergunta (0.00s a 5.19s -> f=0..156) */}
      <Sequence from={0} durationInFrames={156}>
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono - O Desafio (4.84s a 12.66s -> f=145..380) */}
      <Sequence from={145} durationInFrames={235}>
        <Cena1Dono fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Conversa - Como Funciona (12.31s a 20.84s -> f=369..625) */}
      <Sequence from={369} durationInFrames={256}>
        <Cena2Conversa fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono - O Resultado (20.49s a 27.83s -> f=615..835) */}
      <Sequence from={615} durationInFrames={220}>
        <Cena3Dono fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final - CTA (27.48s a 31.43s -> f=824..943) */}
      <Sequence from={824} durationInFrames={BRIEFING.totalFrames - 824}>
        <Cena4Cartao fontFamily={fontFamily} />
      </Sequence>

      {/* 5. Karaokê sincronizado (ativo ESTRITAMENTE nas cenas 0, 1, 2 e 3 — desativado no cartão final) */}
      <Sequence from={0} durationInFrames={824}>
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={BRIEFING.cores.destaque}
          textoDestaque="#FFFFFF"
          tamanho={44}
          base={360}
          maxLetras={40}
        />
      </Sequence>
    </AbsoluteFill>
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
