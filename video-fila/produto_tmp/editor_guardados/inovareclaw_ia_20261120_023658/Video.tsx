import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {DADOS, KARAOKE_PALAVRAS} from './dados';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Volume da trilha: volume ~0.10 com fala, fade in nos primeiros 15 frames, fade out nos últimos 30 frames
  const trilhaVolume = (f: number) => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    if (f > 944) {
      return interpolate(f, [944, 974], [0.1, 0], {extrapolateRight: 'clamp'});
    }
    return 0.1;
  };

  // Barra de progresso contínua no topo (y >= 150)
  const progressPercent = Math.min(100, Math.max(0, (frame / DADOS.totalFrames) * 100));

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13'}}>
      {/* Áudio Oficial do Vídeo (Narração e Trilha de Fundo) */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Sequência de Cenas */}
      {/* Cena 0: Pergunta (0.0s - 5.19s) */}
      <Sequence from={0} durationInFrames={156}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Problema - Dono (4.84s - 13.03s) */}
      <Sequence from={145} durationInFrames={246}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Como Funciona - Conversa (12.68s - 21.02s) */}
      <Sequence from={380} durationInFrames={251}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado - Dono (20.67s - 28.85s) */}
      <Sequence from={620} durationInFrames={246}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final (28.5s - 32.44s) */}
      <Sequence from={855} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso Fina no Topo (y = 152) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 6,
          background: 'rgba(255, 255, 255, 0.15)',
          borderRadius: 3,
          overflow: 'visible',
          zIndex: 80,
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            width: `${progressPercent}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #7C3AED, #A78BFA)',
            borderRadius: 3,
            position: 'relative',
            boxShadow: '0 0 10px rgba(124, 58, 237, 0.8)',
          }}
        >
          {/* Ponto indicador brilhante na ponta da barra */}
          <div
            style={{
              position: 'absolute',
              right: -4,
              top: -3,
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#FFFFFF',
              boxShadow: '0 0 10px #A78BFA, 0 0 4px #FFFFFF',
            }}
          />
        </div>
      </div>

      {/* Karaokê Dinâmico (Ancorado pela base em y=1560) — Exibido estritamente até o fim da Cena 3 (frame 855) */}
      {frame < 855 && (
        <Karaoke
          palavras={KARAOKE_PALAVRAS}
          fontFamily={fontFamily}
          destaque="#7C3AED"
          textoDestaque="#FFFFFF"
          base={360}
          tamanho={46}
          maxLetras={40}
        />
      )}
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
      durationInFrames={DADOS.totalFrames}
    />
  );
};
