import React from 'react';
import {
  Audio,
  Composition,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {briefing} from './briefing';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont('normal', {
  weights: ['400', '700', '800', '900'],
  subsets: ['latin'],
});

// Wrapper com fade suave entre cenas para transições fluidas
const SceneWrapper: React.FC<{
  children: React.ReactNode;
  fadeIn?: boolean;
}> = ({children, fadeIn = true}) => {
  const frame = useCurrentFrame();
  const opacity = fadeIn
    ? interpolate(frame, [0, 8], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        opacity,
      }}
    >
      {children}
    </div>
  );
};

export const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Volume da trilha: volume ~0.10 com fala, fade in nos primeiros 0.5s, fade out no final
  const trilhaVolume = () => {
    const fadeIn = interpolate(frame, [0, 15], [0, 0.1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    const fadeOut = interpolate(frame, [910, 933], [0.1, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    return Math.min(fadeIn, fadeOut);
  };

  // Palavras para Karaokê:
  // Cenas 0 a 3: ativas estritamente até o corte para o cartão final (frame < 817)
  const palavrasCenas0a3 = briefing.palavras
    .filter((p) => p.cena < 4)
    .map((p, i, arr) => ({
      p: p.p,
      ini: p.ini,
      fim: p.fim,
      quebraAntes: i > 0 && p.cena !== arr[i - 1].cena,
      quebraApos: i < arr.length - 1 && p.cena !== arr[i + 1].cena,
    }));

  // Cena 4: 'Chame a gente no direct' sincronizada a partir do frame 817 até o final
  const palavrasCena4 = briefing.palavras
    .filter((p) => p.cena === 4)
    .map((p, i, arr) => ({
      p: p.p,
      ini: p.ini,
      fim: p.fim,
      quebraAntes: i > 0 && p.cena !== arr[i - 1].cena,
    }));

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: '#0F0205',
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* 1. Áudios Oficiais */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume()} />

      {/* 2. Cenas em Sequência com tempos exatos do briefing */}

      {/* Cena 0: Pergunta (0.00s a 5.10s) */}
      <Sequence from={0} durationInFrames={153}>
        <SceneWrapper fadeIn={false}>
          <Cena0 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 1: Dono da Empresa (4.75s a 12.78s) */}
      <Sequence from={143} durationInFrames={241}>
        <SceneWrapper fadeIn={true}>
          <Cena1 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 2: Conversa 3D WhatsApp + IA (12.43s a 20.57s) */}
      <Sequence from={373} durationInFrames={244}>
        <SceneWrapper fadeIn={true}>
          <Cena2 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 3: O Resultado / Checklist (20.22s a 27.60s) */}
      <Sequence from={606} durationInFrames={222}>
        <SceneWrapper fadeIn={true}>
          <Cena3 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (27.25s a 31.10s) */}
      <Sequence from={817} durationInFrames={116}>
        <SceneWrapper fadeIn={true}>
          <Cena4 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* 3. Barra de Progresso no topo (y = 150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 3,
          backgroundColor: 'rgba(255, 255, 255, 0.16)',
          overflow: 'hidden',
          zIndex: 99,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${Math.min(100, (frame / 933) * 100)}%`,
            backgroundColor: '#E11D48',
            boxShadow: '0 0 12px #E11D48',
          }}
        />
      </div>

      {/* 4. Legenda Karaokê Pronta: Cenas 0 a 3 cortam exatamente aos 27.25s (frame 817) */}
      {frame < 817 && (
        <Karaoke
          palavras={palavrasCenas0a3}
          fontFamily={fontFamily}
          destaque={briefing.cores.destaque}
          textoDestaque={briefing.cores.texto_sobre_marca}
          tamanho={46}
          base={360}
        />
      )}

      {/* 5. Legenda Karaokê da Cena 4: 'CHAME A GENTE NO DIRECT' sincronizada */}
      {frame >= 817 && (
        <Karaoke
          palavras={palavrasCena4}
          fontFamily={fontFamily}
          destaque={briefing.cores.destaque}
          textoDestaque={briefing.cores.texto_sobre_marca}
          tamanho={46}
          base={360}
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
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
