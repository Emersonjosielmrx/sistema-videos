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
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Problema} from './Cena1Problema';
import {Cena2ComoFunciona} from './Cena2ComoFunciona';
import {Cena3DonoResultado} from './Cena3DonoResultado';
import {Cena4CartaoFinal} from './Cena4CartaoFinal';

const {fontFamily} = loadFont('normal', {
  weights: ['700', '800', '900'],
  subsets: ['latin'],
});

// Palavras da narração do briefing.json (cenas 0 a 3, agrupadas por fala e excluindo o cartão final)
const rawPalavras: (PalavraK & {cena: number})[] = [
  // Cena 0: Pergunta (0.0s - 4.55s)
  {p: 'Funciona', ini: 0.316, fim: 0.791, cena: 0},
  {p: 'bem', ini: 0.802, fim: 1.034, cena: 0},
  {p: 'para', ini: 1.045, fim: 1.184, cena: 0},
  {p: 'o', ini: 1.196, fim: 1.219, cena: 0},
  {p: 'movimento', ini: 1.231, fim: 1.728, cena: 0},
  {p: 'do', ini: 1.74, fim: 1.821, cena: 0},
  {p: 'almoço', ini: 1.833, fim: 2.249, cena: 0},
  {p: 'no', ini: 2.261, fim: 2.342, cena: 0},
  {p: 'restaurante?', ini: 2.353, fim: 3.117, cena: 0, quebraApos: true},

  // Cena 1: O Problema (4.2s - 10.88s)
  {p: 'No', ini: 4.687, fim: 4.791, cena: 1, quebraAntes: true},
  {p: 'almoço', ini: 4.803, fim: 5.139, cena: 1},
  {p: 'corrido,', ini: 5.15, fim: 5.59, cena: 1, quebraApos: true},
  {p: 'a', ini: 5.648, fim: 5.717, cena: 1},
  {p: 'fila', ini: 5.729, fim: 5.984, cena: 1},
  {p: 'de', ini: 5.995, fim: 6.076, cena: 1},
  {p: 'mensagens', ini: 6.088, fim: 6.62, cena: 1},
  {p: 'crescia,', ini: 6.632, fim: 7.129, cena: 1, quebraApos: true},
  {p: 'e', ini: 7.141, fim: 7.21, cena: 1},
  {p: 'eu', ini: 7.222, fim: 7.338, cena: 1},
  {p: 'não', ini: 7.349, fim: 7.511, cena: 1},
  {p: 'conseguia', ini: 7.523, fim: 7.997, cena: 1},
  {p: 'atender', ini: 8.009, fim: 8.391, cena: 1, quebraApos: true},
  {p: 'todo', ini: 8.484, fim: 8.738, cena: 1},
  {p: 'mundo', ini: 8.75, fim: 9.028, cena: 1},
  {p: 'com', ini: 9.039, fim: 9.201, cena: 1},
  {p: 'calma.', ini: 9.213, fim: 9.606, cena: 1, quebraApos: true},

  // Cena 2: Como Funciona (10.53s - 17.71s)
  {p: 'O', ini: 11.019, fim: 11.1, cena: 2, quebraAntes: true},
  {p: 'cliente', ini: 11.112, fim: 11.494, cena: 2},
  {p: 'abre', ini: 11.505, fim: 11.748, cena: 2},
  {p: 'o', ini: 11.76, fim: 11.783, cena: 2},
  {p: 'cardápio', ini: 11.795, fim: 12.316, cena: 2},
  {p: 'digital', ini: 12.327, fim: 12.79, cena: 2},
  {p: 'no', ini: 12.802, fim: 12.894, cena: 2},
  {p: 'celular,', ini: 12.906, fim: 13.404, cena: 2, quebraApos: true},
  {p: 'vê', ini: 13.519, fim: 13.67, cena: 2},
  {p: 'as', ini: 13.681, fim: 13.809, cena: 2},
  {p: 'fotos', ini: 13.82, fim: 14.167, cena: 2},
  {p: 'dos', ini: 14.179, fim: 14.341, cena: 2},
  {p: 'pratos', ini: 14.353, fim: 14.711, cena: 2, quebraApos: true},
  {p: 'e', ini: 14.723, fim: 14.827, cena: 2},
  {p: 'faz', ini: 14.839, fim: 15.035, cena: 2},
  {p: 'o', ini: 15.047, fim: 15.163, cena: 2},
  {p: 'pedido', ini: 15.174, fim: 15.591, cena: 2},
  {p: 'pelo', ini: 15.603, fim: 15.799, cena: 2},
  {p: 'WhatsApp.', ini: 15.811, fim: 16.459, cena: 2, quebraApos: true},

  // Cena 3: O Resultado (17.36s - 25.55s)
  {p: 'Hoje', ini: 17.824, fim: 18.544, cena: 3, quebraAntes: true},
  {p: 'o', ini: 18.544, fim: 18.684, cena: 3},
  {p: 'cliente', ini: 18.684, fim: 19.184, cena: 3},
  {p: 'escolhe', ini: 19.184, fim: 19.464, cena: 3},
  {p: 'sozinho', ini: 19.464, fim: 19.984, cena: 3},
  {p: 'no', ini: 19.984, fim: 20.124, cena: 3},
  {p: 'celular,', ini: 20.124, fim: 20.704, cena: 3, quebraApos: true},
  {p: 'tira', ini: 21.124, fim: 21.444, cena: 3},
  {p: 'dúvida', ini: 21.584, fim: 21.864, cena: 3},
  {p: 'com', ini: 21.864, fim: 22.084, cena: 3},
  {p: 'a', ini: 22.084, fim: 22.284, cena: 3},
  {p: 'IA', ini: 22.284, fim: 22.664, cena: 3, quebraApos: true},
  {p: 'e', ini: 22.664, fim: 23.604, cena: 3},
  {p: 'o', ini: 23.604, fim: 23.784, cena: 3},
  {p: 'pedido', ini: 23.784, fim: 24.164, cena: 3},
  {p: 'chega', ini: 24.164, fim: 24.484, cena: 3},
  {p: 'pelo', ini: 24.484, fim: 24.724, cena: 3},
  {p: 'WhatsApp.', ini: 24.724, fim: 25.124, cena: 3, quebraApos: true},
];

// Transição de fade suave (10 frames) para sobreposições
const SceneTransition: React.FC<{children: React.ReactNode; isFirst?: boolean}> = ({
  children,
  isFirst = false,
}) => {
  const frame = useCurrentFrame();
  const opacity = isFirst ? 1 : interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  return <div style={{position: 'absolute', inset: 0, opacity}}>{children}</div>;
};

// Barra de Progresso Fina no Topo (y >= 150)
const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = Math.min(1, Math.max(0, frame / durationInFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 60,
        right: 60,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        borderRadius: 999,
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          backgroundColor: '#FACC15',
          boxShadow: '0 0 10px rgba(250, 204, 21, 0.8)',
          borderRadius: 999,
        }}
      />
    </div>
  );
};

export const MainContent: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Controle inteligente de volume da trilha (ducking)
  // ~0.10 com fala, ~0.22 sem fala, fade in/out
  const trilhaVolume = (() => {
    // Fade in no início
    if (frame < 15) {
      return interpolate(frame, [0, 15], [0, 0.10], {extrapolateRight: 'clamp'});
    }
    // Fade out no final
    if (frame > durationInFrames - 22) {
      return interpolate(frame, [durationInFrames - 22, durationInFrames], [0.18, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    // No cartão final após a última fala (~27.2s -> frame 816)
    if (frame > 816) {
      return 0.20;
    }
    // Durante o vídeo com narração
    return 0.10;
  })();

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#0B0D13',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio: Narração completa do início ao fim */}
      <Audio src={staticFile('narracao.mp3')} volume={1.0} />

      {/* Áudio: Trilha sonora de fundo com ducking suave */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Barra de Progresso no Topo (Safe Zone y >= 150) */}
      <ProgressBar />

      {/* CENA 0: Pergunta (0.00s a 4.55s | 137 frames) */}
      <Sequence from={0} durationInFrames={137}>
        <SceneTransition isFirst>
          <Cena0Pergunta fontFamily={fontFamily} />
        </SceneTransition>
      </Sequence>

      {/* CENA 1: O Problema (4.20s a 10.88s | from 126, 200 frames) */}
      <Sequence from={126} durationInFrames={200}>
        <SceneTransition>
          <Cena1Problema fontFamily={fontFamily} />
        </SceneTransition>
      </Sequence>

      {/* CENA 2: Como Funciona (10.53s a 17.71s | from 316, 215 frames) */}
      <Sequence from={316} durationInFrames={215}>
        <SceneTransition>
          <Cena2ComoFunciona fontFamily={fontFamily} />
        </SceneTransition>
      </Sequence>

      {/* CENA 3: O Resultado / Dono (17.36s a 25.55s | from 521, 246 frames) */}
      <Sequence from={521} durationInFrames={246}>
        <SceneTransition>
          <Cena3DonoResultado fontFamily={fontFamily} />
        </SceneTransition>
      </Sequence>

      {/* CENA 4: Cartão Final / CTA (25.20s a 29.05s | from 756, 116 frames) */}
      <Sequence from={756} durationInFrames={116}>
        <SceneTransition>
          <Cena4CartaoFinal fontFamily={fontFamily} />
        </SceneTransition>
      </Sequence>

      {/* Legenda Karaokê Pronta (src/lib/karaoke.tsx)
          Base 420 = distância do fundo até a base da caixa (y = 1920 - 420 = 1500 <= 1560)
          Palavras filtradas e agrupadas por fala; omitida no cartão final (frame >= 756) */}
      {frame < 756 && (
        <Karaoke
          palavras={rawPalavras}
          fontFamily={fontFamily}
          destaque="#E11D48"
          textoDestaque="#FFFFFF"
          tamanho={46}
          base={420}
          maxLetras={40}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainContent}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={872}
    />
  );
};
