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
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Dados brutos das palavras faladas no vídeo (extraídos do briefing)
const PALAVRAS_BRIEFING: (PalavraK & {cena: number})[] = [
  // Cena 0: Pergunta
  {p: 'Passo', ini: 0.318, fim: 0.595, cena: 0},
  {p: 'as', ini: 0.607, fim: 0.679, cena: 0},
  {p: 'rotinas', ini: 0.691, fim: 1.159, cena: 0},
  {p: 'chatas', ini: 1.171, fim: 1.532, cena: 0, quebraApos: true},
  {p: 'da', ini: 1.544, fim: 1.628, cena: 0},
  {p: 'empresa', ini: 1.64, fim: 2.121, cena: 0},
  {p: 'para', ini: 2.133, fim: 2.289, cena: 0},
  {p: 'a', ini: 2.301, fim: 2.313, cena: 0},
  {p: 'IA', ini: 2.325, fim: 3.539, cena: 0},
  {p: 'executar?', ini: 3.551, fim: 4.116, cena: 0, quebraApos: true},

  // Cena 1: O Problema
  {p: 'Eu', ini: 5.228, fim: 5.608, cena: 1},
  {p: 'via', ini: 5.608, fim: 5.808, cena: 1},
  {p: 'a', ini: 5.768, fim: 5.988, cena: 1},
  {p: 'equipe', ini: 5.988, fim: 6.348, cena: 1},
  {p: 'gastar', ini: 6.348, fim: 6.848, cena: 1},
  {p: 'horas', ini: 6.848, fim: 7.208, cena: 1, quebraApos: true},
  {p: 'do', ini: 7.208, fim: 7.468, cena: 1},
  {p: 'expediente', ini: 7.468, fim: 8.088, cena: 1},
  {p: 'em', ini: 8.088, fim: 8.528, cena: 1},
  {p: 'tarefa', ini: 8.528, fim: 9.048, cena: 1},
  {p: 'repetitiva.', ini: 9.048, fim: 10.148, cena: 1, quebraApos: true},
  {p: 'Era', ini: 10.588, fim: 10.728, cena: 1},
  {p: 'tempo', ini: 10.728, fim: 11.088, cena: 1},
  {p: 'que', ini: 11.088, fim: 11.328, cena: 1},
  {p: 'não', ini: 11.328, fim: 11.568, cena: 1},
  {p: 'voltava', ini: 11.568, fim: 12.088, cena: 1, quebraApos: true},
  {p: 'para', ini: 12.088, fim: 12.188, cena: 1},
  {p: 'o', ini: 12.188, fim: 12.388, cena: 1},
  {p: 'negócio.', ini: 12.388, fim: 12.708, cena: 1, quebraApos: true},

  // Cena 2: Como Funciona
  {p: 'Você', ini: 13.401, fim: 13.641, cena: 2},
  {p: 'passa', ini: 13.653, fim: 13.942, cena: 2},
  {p: 'a', ini: 13.954, fim: 13.978, cena: 2},
  {p: 'tarefa', ini: 13.99, fim: 14.435, cena: 2},
  {p: 'para', ini: 14.447, fim: 14.615, cena: 2, quebraLinha: true},
  {p: 'o', ini: 14.627, fim: 14.663, cena: 2},
  {p: 'Inovare', ini: 14.675, fim: 15.12, cena: 2},
  {p: 'Claw.', ini: 15.132, fim: 15.48, cena: 2, quebraApos: true},
  {p: 'Ele', ini: 15.731, fim: 15.875, cena: 2},
  {p: 'executa', ini: 15.887, fim: 16.344, cena: 2},
  {p: 'de', ini: 16.356, fim: 16.452, cena: 2},
  {p: 'forma', ini: 16.464, fim: 16.801, cena: 2},
  {p: 'independente,', ini: 16.813, fim: 17.522, cena: 2, quebraApos: true},
  {p: 'do', ini: 17.546, fim: 17.654, cena: 2},
  {p: 'começo', ini: 17.666, fim: 18.051, cena: 2},
  {p: 'ao', ini: 18.063, fim: 18.147, cena: 2},
  {p: 'fim.', ini: 18.159, fim: 18.459, cena: 2, quebraApos: true},

  // Cena 3: O Resultado
  {p: 'Hoje', ini: 19.901, fim: 20.178, cena: 3},
  {p: 'a', ini: 20.19, fim: 20.214, cena: 3},
  {p: 'rotina', ini: 20.226, fim: 20.61, cena: 3},
  {p: 'chata', ini: 20.622, fim: 20.971, cena: 3},
  {p: 'fica', ini: 20.983, fim: 21.247, cena: 3},
  {p: 'com', ini: 21.259, fim: 21.404, cena: 3},
  {p: 'o', ini: 21.416, fim: 21.452, cena: 3},
  {p: 'agente,', ini: 21.464, fim: 21.968, cena: 3, quebraApos: true},
  {p: 'e', ini: 22.233, fim: 22.305, cena: 3},
  {p: 'minha', ini: 22.317, fim: 22.509, cena: 3},
  {p: 'equipe', ini: 22.521, fim: 22.918, cena: 3},
  {p: 'usa', ini: 22.93, fim: 23.242, cena: 3},
  {p: 'o', ini: 23.254, fim: 23.303, cena: 3},
  {p: 'expediente', ini: 23.315, fim: 23.928, cena: 3},
  {p: 'no', ini: 23.94, fim: 24.036, cena: 3},
  {p: 'que', ini: 24.048, fim: 24.12, cena: 3},
  {p: 'importa.', ini: 24.132, fim: 24.661, cena: 3, quebraApos: true},

  // Cena 4: Cartão Final
  {p: 'Chame', ini: 26.089, fim: 26.438, cena: 4},
  {p: 'a', ini: 26.45, fim: 26.51, cena: 4},
  {p: 'gente', ini: 26.522, fim: 26.846, cena: 4},
  {p: 'no', ini: 26.858, fim: 26.954, cena: 4},
  {p: 'direct.', ini: 26.967, fim: 27.58, cena: 4, quebraApos: true},
];

const MainComposition: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Volume da trilha: ~0.10 durante narração, fade-in no início e fade-out no final
  const trilhaVolume = useMemo(() => {
    // Fade in nos primeiros 30 frames
    const fadeIn = interpolate(frame, [0, 30], [0, 0.10], {extrapolateRight: 'clamp'});
    // Fade out nos últimos 45 frames
    const fadeOut = interpolate(
      frame,
      [durationInFrames - 45, durationInFrames],
      [1, 0],
      {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
    );
    return fadeIn * fadeOut;
  }, [frame, durationInFrames]);

  // Palavras para o Karaokê com quebras exatas e equilibradas por cena e oração
  const karaokePalavras = useMemo(() => {
    return PALAVRAS_BRIEFING.map((w, i, arr) => {
      const isFirstOfScene = i === 0 || arr[i - 1].cena !== w.cena;
      const isLastOfScene = i === arr.length - 1 || arr[i + 1].cena !== w.cena;
      return {
        p: w.p,
        ini: w.ini,
        fim: w.fim,
        quebraAntes: isFirstOfScene || Boolean(w.quebraAntes),
        quebraApos: isLastOfScene || Boolean(w.quebraApos),
        quebraLinha: Boolean(w.quebraLinha),
      };
    });
  }, []);

  // Progresso do vídeo (Barra superior fina em y=150)
  const progressWidth = interpolate(frame, [0, durationInFrames], [0, 1080], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#0B0F19',
        overflow: 'hidden',
      }}
    >
      {/* Áudio: Narração completa do início ao fim */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Áudio: Trilha sonora ambiente com volume equilibrado e fades */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Sequência das Cenas com tempos exatos do briefing */}
      {/* Cena 0: Pergunta (0.00s a 5.58s = 167 frames) */}
      <Sequence from={0} durationInFrames={167}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Problema / Dono (5.23s a 13.26s = 241 frames, from=157) */}
      <Sequence from={157} durationInFrames={241}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Como Funciona / Conversa (12.91s a 19.76s = 206 frames, from=387) */}
      <Sequence from={387} durationInFrames={206}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado (19.41s a 25.95s = 196 frames, from=582) */}
      <Sequence from={582} durationInFrames={196}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (25.60s a 29.54s = 119 frames, from=768) */}
      <Sequence from={768} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso Fina no Topo (y = 150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 0,
          width: progressWidth,
          height: 4,
          background: 'linear-gradient(90deg, #7C3AED, #A855F7, #C084FC)',
          boxShadow: '0 0 10px rgba(168, 85, 247, 0.8)',
          zIndex: 100,
        }}
      />

      {/* Karaokê Dinâmico (Pronto de src/lib/karaoke.tsx) */}
      {/* Ativo em todas as cenas incluindo o encerramento com 'CHAME A GENTE NO DIRECT.' */}
      {frame < 887 && (
        <Karaoke
          palavras={karaokePalavras}
          fontFamily={fontFamily}
          destaque="#7C3AED"
          textoDestaque="#FFFFFF"
          base={360}
          maxLetras={55}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainComposition}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={887}
    />
  );
};
