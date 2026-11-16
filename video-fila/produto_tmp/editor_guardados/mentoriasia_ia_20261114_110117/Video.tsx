import React from 'react';
import {
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import briefing from '../../../trabalhos/mentoriasia_ia_20261114_110117/public/briefing.json';
import {Karaoke} from '../../lib/karaoke';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import {ProgressBar} from './ProgressBar';
import {COLORS, fontFamily} from './theme';

const TOTAL_FRAMES = Math.ceil(briefing.duracao_s * 30); // 954 frames (31.79s)

// Filtra as palavras para não exibir no cartão final (Cena 4)
const palavrasSemCartao = briefing.palavras.filter((p) => p.cena !== 4);

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        backgroundColor: COLORS.fundoEscuro,
        overflow: 'hidden',
      }}
    >
      {/* 1. Áudio da Narração (voz inteira do vídeo do início ao fim) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha Sonora de Fundo (fade in, volume suave com voz e aumento no final) */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          // Fade-in inicial
          if (f < 15) {
            return interpolate(f, [0, 15], [0, 0.1]);
          }
          // Volume durante a narração
          if (f < 890) {
            return 0.1;
          }
          // Subida após o término da fala
          if (f < 935) {
            return interpolate(f, [890, 935], [0.1, 0.22]);
          }
          // Fade-out final
          return interpolate(f, [935, TOTAL_FRAMES], [0.22, 0], {
            extrapolateRight: 'clamp',
          });
        }}
      />

      {/* 3. Cenas com Transição */}
      {/* Cena 0: Pergunta (0.0s a 4.74s -> frames 0 a 142) */}
      <Sequence from={0} durationInFrames={142}>
        <Cena0 />
      </Sequence>

      {/* Cena 1: Dono - A Situação (4.39s a 12.57s -> frames 132 a 377) */}
      <Sequence from={132} durationInFrames={246}>
        <div
          style={{
            width: 1080,
            height: 1920,
            opacity: interpolate(frame - 132, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena1 />
        </div>
      </Sequence>

      {/* Cena 2: Conversa - WhatsApp & Entregáveis (12.22s a 20.37s -> frames 367 a 611) */}
      <Sequence from={367} durationInFrames={245}>
        <div
          style={{
            width: 1080,
            height: 1920,
            opacity: interpolate(frame - 367, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena2 />
        </div>
      </Sequence>

      {/* Cena 3: Dono - O Resultado (20.02s a 28.2s -> frames 601 a 846) */}
      <Sequence from={601} durationInFrames={246}>
        <div
          style={{
            width: 1080,
            height: 1920,
            opacity: interpolate(frame - 601, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena3 />
        </div>
      </Sequence>

      {/* Cena 4: Cartão Final (27.85s a 31.79s -> frames 836 a 954) */}
      <Sequence from={836} durationInFrames={118}>
        <div
          style={{
            width: 1080,
            height: 1920,
            opacity: interpolate(frame - 836, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena4 />
        </div>
      </Sequence>

      {/* 4. Barra de Progresso Global (y=155) */}
      <ProgressBar totalFrames={TOTAL_FRAMES} />

      {/* 5. Legenda Karaokê Oficial (apenas durante as cenas com fala 0 a 3, NÃO no cartão final) */}
      {frame < 836 && (
        <Karaoke
          palavras={palavrasSemCartao}
          fontFamily={fontFamily}
          destaque={COLORS.marca}
          textoDestaque="#FFFFFF"
          tamanho={46}
          base={360}
          maxLetras={32}
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
