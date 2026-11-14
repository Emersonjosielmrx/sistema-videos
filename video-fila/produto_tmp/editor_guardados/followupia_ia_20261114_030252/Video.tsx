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
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import briefing from '../../../trabalhos/followupia_ia_20261114_030252/public/briefing.json';

const {fontFamily} = loadFont();

// Preparar palavras para o Karaokê (apenas cenas 0 a 3, garantindo quebra entre falas)
const palavrasFiltradas: PalavraK[] = briefing.palavras
  .filter((w) => (w as any).cena < 4)
  .map((w, idx, arr) => {
    const cenaAtual = (w as any).cena;
    const cenaAnterior = idx > 0 ? (arr[idx - 1] as any).cena : cenaAtual;
    return {
      p: w.p,
      ini: w.ini,
      fim: w.fim,
      quebraAntes: idx > 0 && cenaAtual !== cenaAnterior,
    };
  });

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Volume dinâmico da trilha sonora com fade-in e fade-out
  const trilhaVolume = (() => {
    // Fade in inicial
    if (frame < 15) {
      return interpolate(frame, [0, 15], [0, 0.10], {extrapolateRight: 'clamp'});
    }
    // Fade out final
    if (frame > 905) {
      return interpolate(frame, [905, 928], [0.14, 0], {extrapolateRight: 'clamp'});
    }
    // CTA final sem voz intensa
    if (frame > 870) {
      return 0.15;
    }
    // Padrão com narração
    return 0.10;
  })();

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Áudio: Narração completa do início ao fim */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Áudio: Trilha sonora de fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Cenas com sobreposição para transições suaves */}
      {/* Cena 0: Pergunta (0.00s a 5.29s -> frames 0 a 159) */}
      <Sequence from={0} durationInFrames={159}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono (4.94s a 12.66s -> frames 148 a 380) */}
      <Sequence from={148} durationInFrames={232}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Conversa WhatsApp (12.31s a 21.25s -> frames 369 a 638) */}
      <Sequence from={369} durationInFrames={269}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado (20.90s a 27.32s -> frames 627 a 820) */}
      <Sequence from={627} durationInFrames={193}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (26.97s a 30.91s -> frames 809 a 928) */}
      <Sequence from={809} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso Fina no Topo (y >= 150) */}
      <ProgressBar cor="#4ECDC4" />

      {/* Karaokê Dinâmico Oficial (apenas cenas 0 a 3, base y=1560) */}
      <Sequence from={0} durationInFrames={809}>
        <Karaoke
          palavras={palavrasFiltradas}
          fontFamily={fontFamily}
          destaque="#4ECDC4"
          textoDestaque="#111827"
          tamanho={46}
          base={360}
          maxLetras={30}
        />
      </Sequence>
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoSegundos = briefing.duracao_s; // 30.91
  const duracaoFrames = Math.ceil(duracaoSegundos * 30); // 928

  return (
    <Composition
      id="Main"
      component={MainVideo}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={duracaoFrames}
    />
  );
};
