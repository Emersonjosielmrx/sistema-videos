import React from 'react';
import {
  Composition,
  Sequence,
  Audio,
  staticFile,
  interpolate,
  useCurrentFrame,
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
  weights: ['500', '600', '700', '800', '900'],
  subsets: ['latin'],
  ignoreTooManyRequestsWarning: true,
});

// Preparação das palavras para o Karaokê (sem cena 4 e com quebras entre cenas)
const rawPalavras = briefing.palavras as Array<{
  p: string;
  ini: number;
  fim: number;
  cena: number;
}>;

const karaokePalavras: PalavraK[] = rawPalavras
  .filter((p) => p.cena < 4) // No cartão final (cena 4), não mostrar legenda
  .map((p, idx, arr) => {
    const isLastOfCena = idx < arr.length - 1 && arr[idx + 1].cena !== p.cena;
    const isFirstOfCena = idx > 0 && arr[idx - 1].cena !== p.cena;
    // Agrupar 'sem fazer o pedido' no segundo bloco da cena 0
    const isSemInCena0 = p.cena === 0 && p.p.toLowerCase().trim() === 'sem';
    return {
      p: p.p,
      ini: p.ini,
      fim: p.fim,
      quebraApos: isLastOfCena,
      quebraAntes: isFirstOfCena || isSemInCena0,
    };
  });

const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const width = interpolate(frame, [0, 925], [0, 1080], {
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        position: 'absolute',
        top: 150,
        left: 0,
        width: `${width}px`,
        height: 6,
        background: 'linear-gradient(90deg, #E11D48, #FACC15)',
        zIndex: 100,
        boxShadow: '0 0 10px rgba(225, 29, 72, 0.8)',
      }}
    />
  );
};

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Curva de volume da trilha musical de fundo
  const trilhaVolume = (f: number) => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    if (f < 860) {
      return 0.1;
    }
    if (f < 900) {
      return interpolate(f, [860, 900], [0.1, 0.15], {
        extrapolateRight: 'clamp',
      });
    }
    return interpolate(f, [900, 925], [0.15, 0], {extrapolateRight: 'clamp'});
  };

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: '#0B0D13',
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio Oficial do Vídeo */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Barra de Progresso Fina no Topo (y >= 150) */}
      <ProgressBar />

      {/* Cenas com Transição Escalonada */}
      {/* Cena 0: 0.00s a 4.26s (128 frames) */}
      <Sequence from={0} durationInFrames={128}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: 3.91s a 11.69s (234 frames) */}
      <Sequence from={117} durationInFrames={234}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: 11.34s a 19.17s (235 frames - corte antes de piscar de olhos) */}
      <Sequence from={340} durationInFrames={235}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: 19.17s a 27.35s (246 frames) */}
      <Sequence from={575} durationInFrames={246}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4 (Cartão Final): 27.00s a 30.85s (116 frames) */}
      <Sequence from={810} durationInFrames={116}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Legenda Karaokê Pronta (apenas durante as falas, desativada no cartão final) */}
      {frame < 810 && (
        <Karaoke
          palavras={karaokePalavras}
          fontFamily={fontFamily}
          destaque="#E11D48"
          textoDestaque="#FFFFFF"
          base={360}
          tamanho={46}
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
