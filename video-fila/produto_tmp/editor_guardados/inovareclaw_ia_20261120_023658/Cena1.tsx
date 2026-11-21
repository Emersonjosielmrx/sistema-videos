import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {ChamferRibbon} from './ChamferRibbon';

type CenaProps = {
  fontFamily: string;
};

export const Cena1: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Rebaixamento generoso do enquadramento para garantir mais de 20% de respiro acima da cabeça (headroom seguro)
  // Punch-in dinâmico de 1.15x centralizado no rosto na virada da frase ("Eu pedia, ela respondia") aos ~9.76s (frame 147)
  const isPunchIn = frame >= 147;
  const videoScale = isPunchIn
    ? interpolate(frame, [147, 246], [1.16, 1.21], {extrapolateRight: 'clamp'})
    : interpolate(frame, [0, 147], [1.0, 1.05], {extrapolateRight: 'clamp'});

  // Offset Y ampliado para 80px/90px garantindo que o topo da cabeça e cabelo nunca encostem nos cards
  const videoTranslateY = isPunchIn ? 80 : 90;

  // Entrada do badge no topo (0.2s)
  const ribbonSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Card A (0.5s -> frame 15)
  const cardASpring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Transição sincronizada com a locução: o Card B só entra exatamente quando a locução inicia
  // a frase "e o trabalho continuava comigo" aos 11.66s (~frame 204 de Cena 1), eliminando concorrência aos 11.39s
  const cardBSwitch = interpolate(frame, [204, 214], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Saída suave no final da cena
  const sceneOpacity = interpolate(frame, [236, 246], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#0B0D13'}}>
      {/* Vídeo do Dono em Tela Cheia com rebaixamento de enquadramento e punch-in dinâmico */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: '50% 36%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </AbsoluteFill>

      {/* Gradiente escuro no topo para proteger leitura (sem escurecer o rosto) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 380,
          background: 'linear-gradient(180deg, rgba(11, 13, 19, 0.85) 0%, rgba(11, 13, 19, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Gradiente sutil na base para proteger karaokê */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 380,
          background: 'linear-gradient(0deg, rgba(11, 13, 19, 0.85) 0%, rgba(11, 13, 19, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Informativo (y = 155) — Exclusivo na faixa livre superior */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${interpolate(ribbonSpring, [0, 1], [-30, 0])}px)`,
          opacity: ribbonSpring,
          zIndex: 20,
        }}
      >
        <ChamferRibbon
          step="01"
          title="O PROBLEMA"
          fontFamily={fontFamily}
          accentColor="#EF4444"
          bgColor="#0F172A"
        />
      </div>

      {/* Card Dinâmico no Topo (y = 205) — Totalmente livre do cabelo do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 205,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 20,
        }}
      >
        {/* Bloco 1 (Fase A: "IA que só escrevia texto") — Desliza para cima com fade */}
        <div
          style={{
            position: 'absolute',
            width: '100%',
            maxWidth: 960,
            background: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 20,
            padding: '12px 24px',
            border: '1.5px solid rgba(239, 68, 68, 0.4)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.75)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 4,
            transform: `translateY(${interpolate(cardASpring, [0, 1], [20, 0]) - interpolate(cardBSwitch, [0, 1], [0, 30])}px)`,
            opacity: interpolate(cardASpring, [0, 1], [0, 1]) * (1 - cardBSwitch),
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 42,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 0.5,
              textAlign: 'center',
            }}
          >
            A IA SÓ ESCREVE TEXTO?
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#CBD5E1',
              textAlign: 'center',
            }}
          >
            Você pedia • Ela respondia • O trabalho continuava
          </div>
        </div>

        {/* Bloco 2 (Fase B: "O trabalho continuava comigo") — Desliza de baixo para cima com fade */}
        <div
          style={{
            position: 'absolute',
            width: '100%',
            maxWidth: 960,
            background: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 20,
            padding: '12px 24px',
            border: '1.5px solid rgba(245, 158, 11, 0.5)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.75)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 4,
            transform: `translateY(${interpolate(cardBSwitch, [0, 1], [30, 0])}px)`,
            opacity: cardBSwitch,
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 44,
              fontWeight: 900,
              color: '#FCD34D',
              letterSpacing: 0.5,
              textAlign: 'center',
            }}
          >
            O TRABALHO CONTINUAVA COMIGO
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#E2E8F0',
              textAlign: 'center',
            }}
          >
            Sem execução autônoma, nada saía do papel
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
