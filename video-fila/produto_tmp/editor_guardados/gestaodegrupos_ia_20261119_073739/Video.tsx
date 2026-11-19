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
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Constantes do vídeo baseadas no briefing
const TOTAL_DURATION_S = 32.03;
const TOTAL_FRAMES = Math.ceil(TOTAL_DURATION_S * 30); // 961 frames

// Definição dos frames exatos de cada cena
const C0_START = 0;
const C0_DURATION = Math.round(5.7 * 30); // 171

const C1_START = Math.round(5.35 * 30); // 161
const C1_DURATION = Math.round((13.53 - 5.35) * 30); // 245

const C2_START = Math.round(13.18 * 30); // 395
const C2_DURATION = Math.round((20.61 - 13.18) * 30); // 223

const C3_START = Math.round(20.26 * 30); // 608
const C3_DURATION = Math.round((28.44 - 20.26) * 30); // 245

const C4_START = Math.round(28.09 * 30); // 843
const C4_DURATION = TOTAL_FRAMES - C4_START; // 118

// Palavras filtradas e estruturadas para o Karaokê (apenas cenas 0 a 3, proibido na cena 4)
const rawPalavras = [
  {p: 'Seu', ini: 0.318, fim: 0.607, cena: 0},
  {p: 'grupo', ini: 0.619, fim: 0.919, cena: 0},
  {p: 'de', ini: 0.931, fim: 1.027, cena: 0},
  {p: 'WhatsApp', ini: 1.039, fim: 1.628, cena: 0, quebraApos: true},
  {p: 'responde', ini: 1.64, fim: 2.133, cena: 0},
  {p: 'do', ini: 2.145, fim: 2.253, cena: 0},
  {p: 'jeito', ini: 2.265, fim: 2.59, cena: 0},
  {p: 'certo', ini: 2.602, fim: 3.01, cena: 0, quebraApos: true},
  {p: 'para', ini: 3.022, fim: 3.167, cena: 0},
  {p: 'a', ini: 3.179, fim: 3.215, cena: 0},
  {p: 'sua', ini: 3.227, fim: 3.443, cena: 0},
  {p: 'comunidade?', ini: 3.455, fim: 4.236, cena: 0, quebraApos: true},
  {p: 'Cada', ini: 6.388, fim: 6.988, cena: 1, quebraAntes: true},
  {p: 'comunidade', ini: 6.988, fim: 7.768, cena: 1},
  {p: 'tem', ini: 7.768, fim: 8.008, cena: 1},
  {p: 'o', ini: 8.008, fim: 8.208, cena: 1},
  {p: 'seu', ini: 8.208, fim: 8.428, cena: 1},
  {p: 'jeito', ini: 8.428, fim: 8.748, cena: 1},
  {p: 'de', ini: 8.748, fim: 9.028, cena: 1},
  {p: 'falar,', ini: 9.028, fim: 9.328, cena: 1, quebraApos: true},
  {p: 'e', ini: 10.548, fim: 10.608, cena: 1, quebraAntes: true},
  {p: 'uma', ini: 10.608, fim: 10.808, cena: 1},
  {p: 'resposta', ini: 10.808, fim: 11.308, cena: 1},
  {p: 'padrão', ini: 11.308, fim: 12.048, cena: 1, quebraApos: true},
  {p: 'não', ini: 12.048, fim: 12.528, cena: 1},
  {p: 'serve', ini: 12.528, fim: 12.848, cena: 1},
  {p: 'para', ini: 12.848, fim: 13.128, cena: 1},
  {p: 'todo', ini: 13.128, fim: 13.328, cena: 1},
  {p: 'mundo.', ini: 13.328, fim: 13.328, cena: 1, quebraApos: true},
  {p: 'Com', ini: 13.674, fim: 13.806, cena: 2, quebraAntes: true},
  {p: 'o', ini: 13.818, fim: 13.854, cena: 2},
  {p: 'prompt', ini: 13.866, fim: 14.203, cena: 2},
  {p: 'dinâmico', ini: 14.215, fim: 14.804, cena: 2, quebraApos: true},
  {p: 'o', ini: 14.864, fim: 14.936, cena: 2},
  {p: 'bot', ini: 14.948, fim: 15.225, cena: 2},
  {p: 'adapta', ini: 15.237, fim: 15.693, cena: 2},
  {p: 'o', ini: 15.705, fim: 15.765, cena: 2},
  {p: 'tom', ini: 15.777, fim: 15.982, cena: 2},
  {p: 'de', ini: 15.994, fim: 16.114, cena: 2},
  {p: 'voz', ini: 16.126, fim: 16.366, cena: 2, quebraApos: true},
  {p: 'e', ini: 16.378, fim: 16.511, cena: 2},
  {p: 'as', ini: 16.547, fim: 16.607, cena: 2},
  {p: 'orientações', ini: 16.619, fim: 17.376, cena: 2},
  {p: 'conforme', ini: 17.388, fim: 17.905, cena: 2, quebraApos: true},
  {p: 'o', ini: 17.917, fim: 17.953, cena: 2},
  {p: 'contexto', ini: 17.965, fim: 18.434, cena: 2},
  {p: 'da', ini: 18.446, fim: 18.554, cena: 2},
  {p: 'comunidade', ini: 18.566, fim: 19.311, cena: 2, quebraApos: true},
  {p: 'Hoje', ini: 20.557, fim: 21.377, cena: 3, quebraAntes: true},
  {p: 'o', ini: 21.377, fim: 21.677, cena: 3},
  {p: 'bot', ini: 21.677, fim: 21.897, cena: 3},
  {p: 'fala', ini: 21.897, fim: 22.237, cena: 3},
  {p: 'com', ini: 22.237, fim: 22.557, cena: 3},
  {p: 'cada', ini: 22.557, fim: 22.777, cena: 3},
  {p: 'comunidade', ini: 22.777, fim: 23.537, cena: 3},
  {p: 'do', ini: 23.537, fim: 23.757, cena: 3},
  {p: 'jeito', ini: 23.757, fim: 24.117, cena: 3},
  {p: 'certo,', ini: 24.117, fim: 24.517, cena: 3, quebraApos: true},
  {p: 'e', ini: 24.977, fim: 25.057, cena: 3, quebraAntes: true},
  {p: 'eu', ini: 25.057, fim: 25.357, cena: 3},
  {p: 'não', ini: 25.357, fim: 25.637, cena: 3},
  {p: 'preciso', ini: 25.637, fim: 25.917, cena: 3, quebraApos: true},
  {p: 'ajustar', ini: 25.917, fim: 26.797, cena: 3},
  {p: 'nada', ini: 26.797, fim: 27.097, cena: 3},
  {p: 'na', ini: 27.097, fim: 27.317, cena: 3},
  {p: 'mão.', ini: 27.317, fim: 27.477, cena: 3, quebraApos: true},
  {p: 'Chame', ini: 28.584, fim: 28.933, cena: 4, quebraAntes: true},
  {p: 'a', ini: 28.945, fim: 29.005, cena: 4},
  {p: 'gente', ini: 29.017, fim: 29.341, cena: 4},
  {p: 'no', ini: 29.353, fim: 29.449, cena: 4},
  {p: 'direct.', ini: 29.462, fim: 30.075, cena: 4, quebraApos: true},
] as PalavraK[];

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Controle de Volume da Trilha
  // Volume mais baixo durante falas (~0.08 a 0.10) e sutilmente mais alto no cartão final e transições
  const trilhaVolume = interpolate(
    frame,
    [0, 20, 140, 160, 380, 400, 590, 610, 830, 850, 930, 960],
    [0, 0.09, 0.09, 0.13, 0.09, 0.12, 0.09, 0.12, 0.1, 0.18, 0.18, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  // Progresso do vídeo (Barra superior y = 150)
  const progressPercent = Math.min(100, (frame / durationInFrames) * 100);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* 1. Áudios do Projeto */}
      <Audio src={staticFile('narracao.mp3')} volume={1} />
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* 2. Cenas em Sequência */}
      {/* Cena 0 — Pergunta / Gancho */}
      <Sequence from={C0_START} durationInFrames={C0_DURATION}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1 — O Problema (Dono 1) */}
      <Sequence from={C1_START} durationInFrames={C1_DURATION}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2 — Como Funciona (Conversa WhatsApp) */}
      <Sequence from={C2_START} durationInFrames={C2_DURATION}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3 — O Resultado (Dono 2) */}
      <Sequence from={C3_START} durationInFrames={C3_DURATION}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4 — Cartão Final (CTA) */}
      <Sequence from={C4_START} durationInFrames={C4_DURATION}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* 3. Barra de Progresso Fina no Topo (y = 150, dentro da Safe Zone) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          borderRadius: 3,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progressPercent}%`,
            background: 'linear-gradient(90deg, #14B8A6 0%, #2DD4BF 100%)',
            boxShadow: '0 0 10px #14B8A6',
            borderRadius: 3,
          }}
        />
      </div>

      {/* 4. Legenda Karaokê Oficial (Sincronizada em todas as cenas, inclusive no CTA falado da cena 4) */}
      <Karaoke
        palavras={rawPalavras}
        fontFamily={fontFamily}
        destaque="#14B8A6"
        textoDestaque="#111827"
        tamanho={46}
        base={360}
        maxLetras={32}
        pausaQuebra={0.65}
      />
    </AbsoluteFill>
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
