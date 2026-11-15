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
import {Karaoke} from '../../lib/karaoke';
import briefing from '../../../trabalhos/disparoemmassa_ia_20261111_135247/public/briefing.json';
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Problema} from './Cena1Problema';
import {Cena2Conversa} from './Cena2Conversa';
import {Cena3Resultado} from './Cena3Resultado';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont('normal', {
  weights: ['700', '800', '900'],
  subsets: ['latin'],
});

const FPS = 30;
const DURACAO_FRAMES = Math.ceil(briefing.duracao_s * FPS); // 897 frames

// Inícios exatos de cada bloco semântico da legenda para zero órfãs/preposições soltas
const INICIOS_BLOCO = new Set([
  2.241, // "sem mandar um por um"
  4.905, // "Eu cansava de passar horas"
  6.299, // "copiando e colando avisos"
  7.778, // "para cada cliente no WhatsApp"
  10.925, // "Com o Disparo em Massa IA"
  13.365, // "eu configuro mensagens personalizadas"
  15.54, // "com envio automático"
  16.778, // "e rotação de números"
  19.417, // "Hoje eu envio campanhas"
  20.727, // "para milhares de contatos no WhatsApp"
  22.782, // "através do disparo em massa inteligente"
]);

const palavrasKaraoke = briefing.palavras
  .filter((w) => w.cena !== 4)
  .map((w) => ({
    ...w,
    quebraAntes: INICIOS_BLOCO.has(w.ini),
  }));

const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;

  const progPct = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateRight: 'clamp',
  });

  const volumeTrilha = (f: number) => {
    const fadeIn = interpolate(f, [0, 20], [0, 0.1], {extrapolateRight: 'clamp'});
    const fadeOut = interpolate(
      f,
      [durationInFrames - 30, durationInFrames],
      [0.1, 0],
      {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
    );
    return Math.min(fadeIn, fadeOut);
  };

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', fontFamily}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volumeTrilha} />

      {/* Cena 0: 0.00s a 4.76s */}
      <Sequence from={0} durationInFrames={Math.ceil(4.76 * FPS)}>
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: 4.41s a 10.78s */}
      <Sequence
        from={Math.floor(4.41 * FPS)}
        durationInFrames={Math.ceil((10.78 - 4.41) * FPS)}
      >
        <Cena1Problema fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: 10.43s a 19.27s */}
      <Sequence
        from={Math.floor(10.43 * FPS)}
        durationInFrames={Math.ceil((19.27 - 10.43) * FPS)}
      >
        <Cena2Conversa
          fontFamily={fontFamily}
          conversa={(briefing.cenas[2].conversa || []) as {de: 'cliente' | 'empresa'; texto: string}[]}
        />
      </Sequence>

      {/* Cena 3: 18.92s a 26.30s */}
      <Sequence
        from={Math.floor(18.92 * FPS)}
        durationInFrames={Math.ceil((26.3 - 18.92) * FPS)}
      >
        <Cena3Resultado fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final 25.95s a 29.90s */}
      <Sequence
        from={Math.floor(25.95 * FPS)}
        durationInFrames={DURACAO_FRAMES - Math.floor(25.95 * FPS)}
      >
        <Cena4Cartao
          fontFamily={fontFamily}
          marca={briefing.marca}
          arroba={briefing.arroba}
        />
      </Sequence>

      {/* Barra de progresso fina no topo dentro da Safe Zone (y=150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          background: 'rgba(255,255,255,0.2)',
          borderRadius: 999,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progPct}%`,
            height: '100%',
            background: briefing.cores.destaque,
            borderRadius: 999,
          }}
        />
      </div>

      {/* Legenda Karaokê (oculta no cartão final t >= 25.95s) */}
      {t < 25.95 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={briefing.cores.destaque}
          textoDestaque={briefing.cores.texto_sobre_marca}
          tamanho={42}
          base={360}
          maxLetras={42}
        />
      )}
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoPrincipal}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={DURACAO_FRAMES}
    />
  );
};
