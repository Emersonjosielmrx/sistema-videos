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
import {BRIEFING, CENAS_CONFIG, PALAVRAS_KARAOKE} from './constants';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont('normal', {
  weights: ['400', '600', '700', '800', '900'],
});

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Volume da música de fundo (trilha) com fade-in e fade-out suaves
  const trilhaVolume = interpolate(
    frame,
    [0, 20, durationInFrames - 30, durationInFrames],
    [0, 0.1, 0.1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: BRIEFING.cores.fundo_escuro,
        fontFamily,
      }}
    >
      {/* Narração Completa */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha Sonora com volume calibrado */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* CENA 0: Pergunta / Dor (0.0s - 5.05s) */}
      <Sequence
        from={CENAS_CONFIG[0].from}
        durationInFrames={CENAS_CONFIG[0].durationInFrames}
        name="Cena0_Pergunta"
      >
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 1: Dono - O Problema (4.7s - 12.88s) */}
      <Sequence
        from={CENAS_CONFIG[1].from}
        durationInFrames={CENAS_CONFIG[1].durationInFrames}
        name="Cena1_Problema"
      >
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 2: Conversa - Como Funciona (12.53s - 21.38s) */}
      <Sequence
        from={CENAS_CONFIG[2].from}
        durationInFrames={CENAS_CONFIG[2].durationInFrames}
        name="Cena2_ComoFunciona"
      >
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 3: Dono - O Resultado (21.03s - 28.74s) */}
      <Sequence
        from={CENAS_CONFIG[3].from}
        durationInFrames={CENAS_CONFIG[3].durationInFrames}
        name="Cena3_Resultado"
      >
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 4: Cartão Final / CTA (28.39s - 32.23s) */}
      <Sequence
        from={CENAS_CONFIG[4].from}
        durationInFrames={CENAS_CONFIG[4].durationInFrames}
        name="Cena4_CartaoFinal"
      >
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso Superior (Fixa em y=152) */}
      <ProgressBar />

      {/* Legenda Karaokê Oficial (Cenas 0 a 3, não aparece no cartão final) */}
      <Karaoke
        palavras={PALAVRAS_KARAOKE}
        fontFamily={fontFamily}
        destaque={BRIEFING.cores.destaque}
        textoDestaque="#FFFFFF"
        tamanho={46}
        base={360}
      />
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainVideo}
      fps={BRIEFING.fps}
      width={1080}
      height={1920}
      durationInFrames={BRIEFING.duracao_frames}
    />
  );
};
