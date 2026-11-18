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
import briefing from '../../../trabalhos/disparoemmassa_ia_20261117_083738/public/briefing.json';
import {Karaoke} from '../../lib/karaoke';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Palavras filtradas: NÃO exibir legenda no cartão final (Cena 4)
const palavrasKaraoke = briefing.palavras.filter((p: any) => p.cena !== 4);

const MainComposition: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        backgroundColor: '#111827',
        fontFamily,
        overflow: 'hidden',
      }}
    >
      {/* 1. Trilha Sonora de fundo (fade in no início e fade out no fim) */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) =>
          interpolate(f, [0, 15, 900, 963], [0, 0.1, 0.1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })
        }
      />

      {/* 2. Narração completa em sincronia absoluta */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 3. Sequências Visuais por Cena */}

      {/* Cena 0: Pergunta (0.00s a 5.22s | frames 0 a 157) */}
      <Sequence from={0} durationInFrames={157}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Dono / O Problema (4.87s a 13.05s | frames 146 a 392) */}
      <Sequence from={146} durationInFrames={246}>
        <div
          style={{
            width: '100%',
            height: '100%',
            opacity: interpolate(frame - 146, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena1 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 2: Conversa WhatsApp / Como Funciona (12.70s a 20.68s | frames 381 a 620) */}
      <Sequence from={381} durationInFrames={239}>
        <div
          style={{
            width: '100%',
            height: '100%',
            opacity: interpolate(frame - 381, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena2 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 3: O Dono / O Resultado (20.33s a 28.51s | frames 610 a 855) */}
      <Sequence from={610} durationInFrames={245}>
        <div
          style={{
            width: '100%',
            height: '100%',
            opacity: interpolate(frame - 610, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena3 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (28.16s a 32.11s | frames 845 a 964) */}
      <Sequence from={845} durationInFrames={119}>
        <div
          style={{
            width: '100%',
            height: '100%',
            opacity: interpolate(frame - 845, [0, 12], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena4 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* 4. Barra de Progresso no Topo (y=150) */}
      <ProgressBar />

      {/* 5. Karaokê Oficial (apenas até o início do cartão final no frame 845) */}
      <Sequence from={0} durationInFrames={845}>
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#22C55E"
          textoDestaque="#111827"
          base={360}
        />
      </Sequence>
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainComposition}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
