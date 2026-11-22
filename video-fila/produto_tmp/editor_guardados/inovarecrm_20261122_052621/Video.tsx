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
import {Karaoke, PalavraK} from '../../lib/karaoke';
import briefing from './briefing.json';

import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont('normal', {
  weights: ['400', '600', '700', '800', '900'],
});

// Componente que aplica transição suave (crossfade) no início da cena
const SceneWrapper: React.FC<{
  children: React.ReactNode;
  fadeInFrames?: number;
}> = ({children, fadeInFrames = 8}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, fadeInFrames], [0, 1], {
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'absolute',
        top: 0,
        left: 0,
        opacity,
      }}
    >
      {children}
    </div>
  );
};

// Preparação das palavras do Karaokê:
// 1. Remove palavras do cartão final (cena 4) pois lá não tem legenda
// 2. Insere quebra de fala forçada na transição entre cenas
const palavrasKaraoke: PalavraK[] = briefing.palavras
  .filter((w) => w.cena !== 4)
  .map((w, idx, arr) => {
    const isLastOfScene =
      idx < arr.length - 1 && arr[idx + 1].cena !== w.cena;
    return {
      p: w.p,
      ini: w.ini,
      fim: w.fim,
      quebraApos: isLastOfScene,
    };
  });

const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Volume da trilha: fade-in inicial de 0.5s (15 frames), volume constante de 0.10 com fala, fade-out final de 1.5s (45 frames)
  const trilhaVolume = (f: number) => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.10], {extrapolateRight: 'clamp'});
    }
    if (f > durationInFrames - 45) {
      return interpolate(f, [durationInFrames - 45, durationInFrames], [0.10, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    return 0.10;
  };

  // Barra de progresso contínua no topo (y = 152)
  const progressPercent = (frame / (durationInFrames - 1)) * 100;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: '#0F172A',
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio Principal (Voz de Locução + Fala do Dono) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha Sonora com Mixagem Adequada */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Cenas com Respeito Rigoroso ao Briefing */}
      {/* Cena 0: Pergunta e Gancho (0.00s a 4.79s -> frames 0 a 144) */}
      <Sequence from={0} durationInFrames={144}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono - O Problema (4.44s a 12.45s -> frames 133 a 374) */}
      <Sequence from={133} durationInFrames={241}>
        <SceneWrapper fadeInFrames={8}>
          <Cena1 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 2: Solução com Veo / B-Roll (12.10s a 19.27s -> frames 363 a 578) */}
      <Sequence from={363} durationInFrames={215}>
        <SceneWrapper fadeInFrames={8}>
          <Cena2 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 3: Dono - O Resultado (18.92s a 27.10s -> frames 568 a 813) */}
      <Sequence from={568} durationInFrames={245}>
        <SceneWrapper fadeInFrames={8}>
          <Cena3 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 4: Cartão Final de Conversão (26.75s a 30.69s -> frames 803 a 921) */}
      <Sequence from={803} durationInFrames={118}>
        <SceneWrapper fadeInFrames={8}>
          <Cena4 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Legenda Karaokê Oficial: APENAS durante as Cenas 0 a 3 (frame < 803), NUNCA no Cartão Final */}
      {frame < 803 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#0284C7"
          textoDestaque="#FFFFFF"
          base={360}
          tamanho={46}
        />
      )}

      {/* Barra de Progresso Fina no Topo (y = 152, dentro da Safe Zone >= 150) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 4,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          borderRadius: 2,
          overflow: 'hidden',
          zIndex: 100,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progressPercent}%`,
            background: 'linear-gradient(90deg, #0284C7 0%, #38BDF8 100%)',
            boxShadow: '0 0 8px #38BDF8',
          }}
        />
      </div>
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoSegundos = briefing.duracao_s; // 30.69
  const totalFrames = Math.ceil(duracaoSegundos * 30); // 921

  return (
    <Composition
      id="Main"
      component={Main}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={totalFrames}
    />
  );
};
