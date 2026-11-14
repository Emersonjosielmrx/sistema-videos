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
import {Karaoke} from '../../lib/karaoke';
import {briefing} from './briefingData';
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Dono} from './Cena1Dono';
import {Cena2Conversa} from './Cena2Conversa';
import {Cena3Dono} from './Cena3Dono';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont();

// Volume dinâmico da trilha sonora (0.10 com fala, 0.18 no final, fade in/out)
const getTrilhaVolume = (f: number): number => {
  if (f < 15) {
    return interpolate(f, [0, 15], [0, 0.1], {extrapolateRight: 'clamp'});
  }
  if (f > 890) {
    return interpolate(f, [890, 905], [0.18, 0], {extrapolateRight: 'clamp'});
  }
  if (f > 845) {
    return interpolate(f, [845, 870], [0.1, 0.18], {extrapolateRight: 'clamp'});
  }
  return 0.1;
};

// Componente Principal de Composição
const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Barra de Progresso no Topo (Safe Zone: y >= 150)
  const progressPercent = Math.min(100, Math.max(0, (frame / (905 - 1)) * 100));

  // Palavras para o Karaokê (excluindo estritamente a cena 4 do cartão final)
  const karaokePalavras = briefing.palavras.filter((p) => p.cena !== 4);

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio Oficial do Vídeo (Voz Completa Montada) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha Sonora com Mixagem e Fades Automáticos */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => getTrilhaVolume(f)}
      />

      {/* CENA 0: Pergunta e Gancho (0.00s a 5.00s -> frames 0 a 150) */}
      <Sequence from={0} durationInFrames={150}>
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 1: O Problema - Dono (4.65s a 12.68s -> frames 140 a 381) */}
      <Sequence from={140} durationInFrames={241}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(frame - 140, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena1Dono fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* CENA 2: Como Funciona - WhatsApp (12.33s a 18.87s -> frames 370 a 567) */}
      <Sequence from={370} durationInFrames={197}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(frame - 370, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena2Conversa fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* CENA 3: O Resultado - Dono (18.52s a 26.55s -> frames 556 a 798) */}
      <Sequence from={556} durationInFrames={242}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(frame - 556, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena3Dono fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* CENA 4: Cartão Final - CTA (26.20s a 30.14s -> frames 786 a 905) */}
      <Sequence from={786} durationInFrames={120}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(frame - 786, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <Cena4Cartao fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Barra de Progresso Fina no Topo (y = 165 >= 150) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 3,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          zIndex: 80,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${progressPercent}%`,
            height: '100%',
            backgroundColor: '#0EA5E9',
            boxShadow: '0 0 10px rgba(14, 165, 233, 0.8)',
          }}
        />
      </div>

      {/* Legenda Karaokê Oficial (Exibida estritamente nas cenas com fala, oculta no cartão final) */}
      {frame < 786 && (
        <Karaoke
          palavras={karaokePalavras}
          fontFamily={fontFamily}
          destaque="#0EA5E9"
          textoDestaque="#0F172A"
          tamanho={46}
          base={360}
        />
      )}
    </div>
  );
};

// Export da Raiz com a Composição Oficial
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
