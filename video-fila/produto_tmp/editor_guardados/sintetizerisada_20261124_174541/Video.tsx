import React from 'react';
import {
  AbsoluteFill,
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
import {KARAOKE_PALAVRAS} from './palavras';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  ignoreTooManyRequestsWarning: true,
});

const DURATION_IN_FRAMES = 977; // Math.ceil(32.54 * 30)

const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Curva de volume da trilha musical (volume ~0.10 com fala, ~0.20 sem fala, fade in/out)
  const getTrilhaVolume = (f: number) => {
    // Fade in nos primeiros 15 frames
    const fadeIn = interpolate(f, [0, 15], [0, 1], {
      extrapolateRight: 'clamp',
    });
    // Fade out nos últimos 25 frames
    const fadeOut = interpolate(
      f,
      [durationInFrames - 25, durationInFrames],
      [1, 0],
      {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      }
    );

    // Na cena 4 (após o fim da fala aos ~30.6s / frame 918), a trilha sobe suavemente
    const baseVol = interpolate(f, [900, 930], [0.1, 0.22], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });

    return baseVol * fadeIn * fadeOut;
  };

  // Progresso do vídeo no topo (y = 150)
  const progressPercent = Math.min(100, ((frame + 1) / durationInFrames) * 100);

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A'}}>
      {/* Áudio Oficial da Narração (voz pronta sem cortes) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha de Fundo com volume dinâmico e ducking */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* CENA 0: Pergunta (0.0s a 5.29s) */}
      <Sequence from={0} durationInFrames={159}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 1: Dono 1 (4.94s a 12.97s, overlap com Cena 0 de 11 frames) */}
      <Sequence from={148} durationInFrames={241}>
        <div
          style={{
            width: '100%',
            height: '100%',
            opacity: interpolate(frame - 148, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena1 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* CENA 2: Conversa WhatsApp (12.62s a 21.22s, overlap de 10 frames) */}
      <Sequence from={379} durationInFrames={258}>
        <div
          style={{
            width: '100%',
            height: '100%',
            opacity: interpolate(frame - 379, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena2 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* CENA 3: Dono 3 (20.87s a 28.90s, overlap de 11 frames) */}
      <Sequence from={626} durationInFrames={241}>
        <div
          style={{
            width: '100%',
            height: '100%',
            opacity: interpolate(frame - 626, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena3 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* CENA 4: Cartão Final CTA (28.55s a 32.54s) */}
      <Sequence from={857} durationInFrames={120}>
        <div
          style={{
            width: '100%',
            height: '100%',
            opacity: interpolate(frame - 857, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena4 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Barra de Progresso Fina no Topo Seguro (y = 150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 3,
          backgroundColor: 'rgba(255, 255, 255, 0.16)',
          zIndex: 80,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${progressPercent}%`,
            height: '100%',
            backgroundColor: '#FFA94D',
            borderRadius: 3,
            boxShadow: '0 0 10px #FFA94D',
          }}
        />
      </div>

      {/* Legenda Karaokê Oficial (Cenas 0 a 3, não aparece no cartão final) */}
      <Karaoke
        palavras={KARAOKE_PALAVRAS}
        fontFamily={fontFamily}
        destaque="#FFA94D"
        textoDestaque="#0F172A"
        tamanho={46}
        base={360}
      />
    </AbsoluteFill>
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
      durationInFrames={DURATION_IN_FRAMES}
    />
  );
};
