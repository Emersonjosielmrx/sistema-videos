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
import {PALAVRAS} from './palavras';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  ignoreTooManyRequestsWarning: true,
});

const DURACAO_S = 32.9;
const TOTAL_FRAMES = Math.ceil(DURACAO_S * 30); // 987 frames

const Main: React.FC = () => {
  const frame = useCurrentFrame();

  // Volume da trilha sonora dinâmico:
  // ~0.10 com fala, ~0.20 sem fala no final, fade in e fade out
  const trilhaVolume = (f: number) => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.10], {extrapolateRight: 'clamp'});
    }
    if (f >= 15 && f < 870) {
      return 0.10;
    }
    if (f >= 870 && f < 930) {
      return interpolate(f, [870, 930], [0.10, 0.20], {extrapolateRight: 'clamp'});
    }
    if (f >= 930 && f < 970) {
      return 0.20;
    }
    return interpolate(f, [970, TOTAL_FRAMES], [0.20, 0], {
      extrapolateRight: 'clamp',
    });
  };

  // Progresso do vídeo (barra fina no topo em y = 150)
  const progressPercent = Math.min(100, Math.max(0, (frame / TOTAL_FRAMES) * 100));

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#0B0D13',
        overflow: 'hidden',
      }}
    >
      {/* Áudio: Narração completa montada */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Áudio: Trilha sonora de fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Cena 0: Pergunta / Gancho (0.0s a 5.22s) */}
      <Sequence from={0} durationInFrames={157}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Problema (4.87s a 12.61s) */}
      <Sequence from={146} durationInFrames={232}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Como Funciona / WhatsApp (12.26s a 21.65s) */}
      <Sequence from={368} durationInFrames={282}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado (21.30s a 29.30s) */}
      <Sequence from={639} durationInFrames={240}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (28.95s a 32.90s) */}
      <Sequence from={868} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Legenda Karaokê (apenas durante as cenas 0 a 3, oculta no cartão final) */}
      <Sequence from={0} durationInFrames={868}>
        <Karaoke
          palavras={PALAVRAS}
          fontFamily={fontFamily}
          destaque="#F59E0B"
          textoDestaque="#121216"
          tamanho={46}
          base={360}
          maxLetras={32}
        />
      </Sequence>

      {/* Barra de Progresso Fina no Topo (y = 150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          background: 'rgba(255, 255, 255, 0.15)',
          borderRadius: 3,
          overflow: 'hidden',
          zIndex: 100,
        }}
      >
        <div
          style={{
            width: `${progressPercent}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #F59E0B, #FBBF24)',
            boxShadow: '0 0 10px rgba(245, 158, 11, 0.8)',
            borderRadius: 3,
          }}
        />
      </div>
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={Main}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
