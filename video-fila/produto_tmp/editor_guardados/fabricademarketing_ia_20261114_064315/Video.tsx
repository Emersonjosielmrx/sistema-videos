import React from 'react';
import {
  Composition,
  Sequence,
  Audio,
  staticFile,
  useCurrentFrame,
  interpolate,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const FPS = 30;
const DURATION_FRAMES = 881; // Math.ceil(29.35 * 30)

// Words from briefing.json for karaoke (scenes 0 to 3 only, scene 4 has no karaoke)
const PALAVRAS_KARAOKE: PalavraK[] = [
  {p: 'Seus', ini: 0.318, fim: 0.607},
  {p: 'seguidores', ini: 0.619, fim: 1.147},
  {p: 'comentam', ini: 1.159, fim: 1.724},
  {p: 'e', ini: 1.736, fim: 1.784},
  {p: 'ficam', ini: 1.796, fim: 2.133},
  {p: 'sem', ini: 2.145, fim: 2.349},
  {p: 'resposta?', ini: 2.349, fim: 4.10, quebraApos: true},
  {p: 'Eu', ini: 4.148, fim: 5.108},
  {p: 'não', ini: 5.108, fim: 5.108},
  {p: 'dava', ini: 5.108, fim: 6.968},
  {p: 'conta', ini: 6.968, fim: 7.508},
  {p: 'de', ini: 7.508, fim: 7.968},
  {p: 'responder', ini: 7.968, fim: 8.668},
  {p: 'todo', ini: 8.668, fim: 9.248},
  {p: 'mundo', ini: 9.248, fim: 9.688},
  {p: 'que', ini: 9.688, fim: 10.048},
  {p: 'comentava', ini: 10.048, fim: 10.548},
  {p: 'nas', ini: 10.548, fim: 10.748},
  {p: 'minhas', ini: 10.748, fim: 11.048},
  {p: 'postagens.', ini: 11.048, fim: 11.648, quebraApos: true},
  {p: 'A', ini: 12.321, fim: 12.429},
  {p: 'ferramenta', ini: 12.441, fim: 12.97},
  {p: 'publica', ini: 12.982, fim: 13.391},
  {p: 'os', ini: 13.403, fim: 13.499},
  {p: 'conteúdos', ini: 13.511, fim: 14.076},
  {p: 'e', ini: 14.088, fim: 14.208},
  {p: 'conta', ini: 14.232, fim: 14.569},
  {p: 'com', ini: 14.581, fim: 14.725},
  {p: 'agente', ini: 14.737, fim: 15.098},
  {p: 'de', ini: 15.11, fim: 15.182},
  {p: 'respostas', ini: 15.194, fim: 15.843},
  {p: 'nos', ini: 15.855, fim: 15.999},
  {p: 'comentários', ini: 16.011, fim: 16.792, quebraApos: true},
  {p: 'Agora', ini: 17.728, fim: 18.288},
  {p: 'não', ini: 18.708, fim: 18.868},
  {p: 'perco', ini: 18.868, fim: 19.548},
  {p: 'o', ini: 19.548, fim: 19.888},
  {p: 'contato', ini: 19.888, fim: 20.228},
  {p: 'comercial', ini: 20.228, fim: 20.828},
  {p: 'de', ini: 20.828, fim: 21.608},
  {p: 'quem', ini: 21.608, fim: 22.028},
  {p: 'demonstra', ini: 22.028, fim: 22.808},
  {p: 'interesse', ini: 22.808, fim: 23.648},
  {p: 'nas', ini: 23.648, fim: 23.888},
  {p: 'minhas', ini: 23.888, fim: 24.188},
  {p: 'publicações.', ini: 24.188, fim: 24.888, quebraApos: true},
];

// Trilha volume ducking function
const getTrilhaVolume = (f: number): number => {
  // Fade in at start
  if (f < 15) return interpolate(f, [0, 15], [0, 0.12]);
  // Fade out at end
  if (f > 855) return interpolate(f, [855, 881], [0.18, 0], {extrapolateRight: 'clamp'});

  // Pause periods (duck trilha up to ~0.18, with speech duck to ~0.09)
  const t = f / 30;
  const isPause =
    (t >= 3.1 && t <= 4.1) ||
    (t >= 11.7 && t <= 12.3) ||
    (t >= 16.8 && t <= 17.7) ||
    (t >= 24.9 && t <= 25.8) ||
    t >= 27.4;

  return isPause ? 0.18 : 0.09;
};

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div style={{position: 'relative', width: 1080, height: 1920, backgroundColor: '#111827'}}>
      {/* Audio Narracao */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Audio Trilha with dynamic ducking and fades */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* Thin Progress Bar at Top (y >= 150) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          width: 960,
          height: 6,
          borderRadius: 3,
          background: 'rgba(255, 255, 255, 0.18)',
          zIndex: 100,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${((frame + 1) / DURATION_FRAMES) * 100}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #F472B6 0%, #DB2777 100%)',
            boxShadow: '0 0 10px rgba(244, 114, 182, 0.8)',
          }}
        />
      </div>

      {/* Cena 0: Pergunta (0.0s - 4.5s | frames 0 - 135) */}
      <Sequence from={0} durationInFrames={135}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(frame, [122, 135], [1, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena0 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 1: O Problema - Dono (4.15s - 12.18s | frames 125 - 366) */}
      <Sequence from={125} durationInFrames={241}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(
              frame - 125,
              [0, 10, 230, 241],
              [0, 1, 1, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
            ),
          }}
        >
          <Cena1 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 2: Como Funciona - Conversa (11.83s - 18.08s | frames 355 - 543) */}
      <Sequence from={355} durationInFrames={188}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(
              frame - 355,
              [0, 10, 178, 188],
              [0, 1, 1, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
            ),
          }}
        >
          <Cena2 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 3: O Resultado - Dono (17.73s - 25.76s | frames 532 - 773) */}
      <Sequence from={532} durationInFrames={241}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(
              frame - 532,
              [0, 10, 230, 241],
              [0, 1, 1, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
            ),
          }}
        >
          <Cena3 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (25.41s - 29.35s | frames 762 - 881) */}
      <Sequence from={762} durationInFrames={119}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(frame - 762, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena4 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Karaoke Caption: only visible while frame < 762 (Scenes 0, 1, 2, 3), NEVER on Cartão Final */}
      {frame < 762 && (
        <Karaoke
          palavras={PALAVRAS_KARAOKE}
          fontFamily={fontFamily}
          destaque="#F472B6"
          textoDestaque="#111827"
          base={360}
          tamanho={44}
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
      durationInFrames={DURATION_FRAMES}
      fps={FPS}
      width={1080}
      height={1920}
    />
  );
};
