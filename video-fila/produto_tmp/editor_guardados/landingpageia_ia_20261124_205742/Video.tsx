import React, {useMemo} from 'react';
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
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

// Dados do briefing
import briefing from '../../../trabalhos/landingpageia_ia_20261124_205742/public/briefing.json';

const {fontFamily} = loadFont('normal', {
  weights: ['700', '800', '900'],
  subsets: ['latin'],
  ignoreTooManyRequestsWarning: true,
});

const DURACAO_S = briefing.duracao_s; // 33.67
const TOTAL_FRAMES = Math.ceil(DURACAO_S * 30); // 1011 frames

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Trilha sonora com fade-in e fade-out
  // Volume com fala: ~0.10
  const trilhaVolume = (f: number) => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    if (f > durationInFrames - 30) {
      return interpolate(f, [durationInFrames - 30, durationInFrames], [0.1, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    return 0.1;
  };

  // Preparação das palavras para o Karaokê:
  // 1. Filtrar palavras da cena 4 (no cartão final, nenhuma legenda deve aparecer)
  // 2. Garantir quebra obrigatória entre cenas sucessivas
  const karaokeWords: PalavraK[] = useMemo(() => {
    const rawWords = (briefing.palavras as Array<{
      p: string;
      ini: number;
      fim: number;
      cena: number;
    }>).filter((w) => w.cena < 4);

    return rawWords.map((w, idx) => {
      const isStartOfScene = idx === 0 || rawWords[idx - 1].cena !== w.cena;
      const isEndOfScene =
        idx === rawWords.length - 1 || rawWords[idx + 1].cena !== w.cena;

      // Quebras adicionais para pausas de frase
      const extraQuebraApos =
        w.p.endsWith(',') || w.p.endsWith('.') || w.p.endsWith('?');

      return {
        p: w.p,
        ini: w.ini,
        fim: w.fim,
        quebraAntes: isStartOfScene,
        quebraApos: isEndOfScene || extraQuebraApos,
      };
    });
  }, []);

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#111827',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* 1. Áudios */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* 2. Barra de Progresso no Topo (y=150) */}
      <ProgressBar cor="#F59E0B" />

      {/* 3. Cenas Sequenciais */}
      {/* Cena 0: 0.00s a 5.36s (frames 0 a 161) */}
      <Sequence from={0} durationInFrames={161}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: 5.01s a 13.20s (frames 150 a 396 -> duração: 246) */}
      <Sequence from={150} durationInFrames={246}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: 12.85s a 22.24s (frames 386 a 667 -> duração: 281) */}
      <Sequence from={386} durationInFrames={281}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: 21.89s a 30.07s (frames 657 a 902 -> duração: 245) */}
      <Sequence from={657} durationInFrames={245}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: 29.72s a 33.67s (frames 892 a 1011 -> duração: 119) */}
      <Sequence from={892} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* 4. Legenda Karaokê (centralizada entre y=1320 e y=1580, base padrão 360 -> y=1560) */}
      {/* Ativa somente enquanto houver falas anteriores ao cartão final */}
      {frame < 892 && (
        <Karaoke
          palavras={karaokeWords}
          fontFamily={fontFamily}
          destaque="#F59E0B"
          textoDestaque="#121216"
          base={360}
          tamanho={46}
          maxLetras={28}
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
