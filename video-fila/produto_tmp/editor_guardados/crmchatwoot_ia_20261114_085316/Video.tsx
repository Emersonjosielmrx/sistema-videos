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
import {Karaoke} from '../../lib/karaoke';
import briefingData from '../../../trabalhos/crmchatwoot_ia_20261114_085316/public/briefing.json';

import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const DURACAO_TOTAL_S = 29.03;
const TOTAL_FRAMES = Math.ceil(DURACAO_TOTAL_S * 30); // 871 frames

// Intervalos de fala para ducking da trilha musical
const SPEECH_INTERVALS = [
  {ini: 0.32, fim: 3.76},
  {ini: 4.87, fim: 11.45},
  {ini: 12.39, fim: 17.72},
  {ini: 19.16, fim: 24.16},
  {ini: 25.58, fim: 27.07},
];

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const timeS = frame / fps;

  // Barra de progresso no topo (y >= 150)
  const progressPercent = interpolate(frame, [0, TOTAL_FRAMES], [0, 100], {
    extrapolateRight: 'clamp',
  });

  // Volume dinâmico da trilha sonora (Ducking de áudio de alta precisão)
  const getTrilhaVolume = (f: number) => {
    const t = f / fps;
    // Fade in no início
    if (t < 0.5) {
      return interpolate(t, [0, 0.5], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    // Fade out no final
    if (t > DURACAO_TOTAL_S - 0.8) {
      return interpolate(t, [DURACAO_TOTAL_S - 0.8, DURACAO_TOTAL_S], [0.2, 0], {
        extrapolateRight: 'clamp',
      });
    }
    // Verifica se está no meio de alguma fala
    const isSpeaking = SPEECH_INTERVALS.some(
      (interval) => t >= interval.ini - 0.1 && t <= interval.fim + 0.15
    );
    return isSpeaking ? 0.1 : 0.22;
  };

  // Timings das cenas em frames
  const fCena0Ini = 0;
  const fCena0Dur = Math.round(5.22 * 30); // 157

  const fCena1Ini = Math.round(4.87 * 30); // 146
  const fCena1Dur = Math.round((12.25 - 4.87) * 30); // 221

  const fCena2Ini = Math.round(11.9 * 30); // 357
  const fCena2Dur = Math.round((19.01 - 11.9) * 30); // 213

  const fCena3Ini = Math.round(18.66 * 30); // 560
  const fCena3Dur = Math.round((25.44 - 18.66) * 30); // 203

  const fCena4Ini = Math.round(25.09 * 30); // 753
  const fCena4Dur = TOTAL_FRAMES - fCena4Ini; // 118

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* 1. Narração Principal completa */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha Musical de fundo com volume balanceado */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => getTrilhaVolume(f)}
      />

      {/* 3. Camadas de Vídeo / Cenas */}
      {/* Cena 0: Pergunta / Gancho */}
      <Sequence from={fCena0Ini} durationInFrames={fCena0Dur}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Dono falando (Vídeo real) */}
      <Sequence from={fCena1Ini} durationInFrames={fCena1Dur}>
        <SceneWrapper>
          <Cena1 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 2: Como Funciona (Mockup 3D de conversa) */}
      <Sequence from={fCena2Ini} durationInFrames={fCena2Dur}>
        <SceneWrapper>
          <Cena2 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 3: O Resultado (Checklist de 3 pilares) */}
      <Sequence from={fCena3Ini} durationInFrames={fCena3Dur}>
        <SceneWrapper>
          <Cena3 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 4: Cartão Final CTA (Minimalista e vivo) */}
      <Sequence from={fCena4Ini} durationInFrames={fCena4Dur}>
        <SceneWrapper>
          <Cena4 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* 4. Barra de Progresso no Topo (Safe Zone y >= 150) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 6,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          borderRadius: 3,
          overflow: 'hidden',
          zIndex: 100,
        }}
      >
        <div
          style={{
            width: `${progressPercent}%`,
            height: '100%',
            backgroundColor: '#1F93FF',
            borderRadius: 3,
            boxShadow: '0 0 10px #1F93FF',
          }}
        />
      </div>

      {/* 5. Legenda Karaokê Oficial (Ativa até o início do Cartão Final) */}
      {frame < fCena4Ini && (
        <Karaoke
          palavras={briefingData.palavras}
          fontFamily={fontFamily}
          destaque="#1F93FF"
          textoDestaque="#FFFFFF"
          base={360}
        />
      )}
    </AbsoluteFill>
  );
};

// Transição de fade suave de 6 frames na entrada de cada cena
const SceneWrapper: React.FC<{children: React.ReactNode}> = ({children}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{opacity}}>
      {children}
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
