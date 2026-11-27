import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  // Background camera motion (push-in contínuo)
  const bgScale = interpolate(frame, [0, durationInFrames], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, durationInFrames], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Fade out no final para transição suave com Cena 1
  const opacity = interpolate(
    frame,
    [durationInFrames - 12, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Animações dos elementos
  // 1. Badge superior "PERGUNTA FREQUENTE" (~0.15s / frame 5)
  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. Linha 1 "CANSADO DE PAGAR" (~0.32s / frame 10)
  const line1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // 3. Linha 2 de destaque "VÁRIOS PROFISSIONAIS?" (~1.25s / frame 38)
  const line2Spring = spring({
    frame: frame - 38,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 4. Card secundário "SÓ PARA APRESENTAR SEU PRODUTO?" (~2.5s / frame 75)
  const cardSpring = spring({
    frame: frame - 75,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Micro-dinâmica contínua
  const floatOffset = Math.sin(frame / 12) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        opacity,
      }}
    >
      {/* Background Photo com push-in */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu protetor de contraste (opaco e escuro para legibilidade perfeita) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(17, 24, 39, 0.88) 0%, rgba(17, 24, 39, 0.55) 45%, rgba(17, 24, 39, 0.92) 100%)',
        }}
      />

      {/* Vignette decorativa */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          boxShadow: 'inset 0 0 140px rgba(0, 0, 0, 0.75)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo na Safe Zone (y: 150 a 1580, laterais: 60px) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
        }}
      >
        {/* Badge superior */}
        <div
          style={{
            opacity: badgeSpring,
            transform: `scale(${badgeSpring})`,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 30,
            background: 'rgba(17, 24, 39, 0.95)',
            border: '1.5px solid rgba(245, 158, 11, 0.45)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
            marginBottom: 40,
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#F59E0B',
              boxShadow: '0 0 10px #F59E0B',
            }}
          />
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#F59E0B',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            PERGUNTA FREQUENTE
          </span>
        </div>

        {/* Bloco Cinético Central */}
        <div
          style={{
            marginTop: 30,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            transform: `translateY(${floatOffset}px)`,
          }}
        >
          {/* Linha 1: CANSADO DE PAGAR */}
          <div
            style={{
              opacity: line1Spring,
              transform: `scale(${interpolate(line1Spring, [0, 1], [0.85, 1])}) translateY(${interpolate(
                line1Spring,
                [0, 1],
                [30, 0]
              )}px)`,
              background: 'rgba(17, 24, 39, 0.95)',
              padding: '14px 34px',
              borderRadius: 22,
              border: '1.5px solid rgba(255, 255, 255, 0.12)',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.75)',
            }}
          >
            <span
              style={{
                fontSize: 54,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '-0.5px',
                textTransform: 'uppercase',
              }}
            >
              CANSADO DE PAGAR
            </span>
          </div>

          {/* Linha 2 de destaque: VÁRIOS PROFISSIONAIS? */}
          <div
            style={{
              opacity: line2Spring,
              transform: `scale(${interpolate(line2Spring, [0, 1], [0.8, 1])}) translateY(${interpolate(
                line2Spring,
                [0, 1],
                [35, 0]
              )}px)`,
              background: '#F59E0B',
              padding: '16px 38px',
              borderRadius: 24,
              boxShadow: '0 20px 50px rgba(245, 158, 11, 0.45)',
            }}
          >
            <span
              style={{
                fontSize: 60,
                fontWeight: 900,
                color: '#121216',
                letterSpacing: '-1px',
                textTransform: 'uppercase',
              }}
            >
              VÁRIOS PROFISSIONAIS?
            </span>
          </div>

          {/* Card Secundário: SÓ PARA APRESENTAR SEU PRODUTO? */}
          <div
            style={{
              marginTop: 10,
              opacity: cardSpring,
              transform: `scale(${interpolate(cardSpring, [0, 1], [0.9, 1])}) translateY(${interpolate(
                cardSpring,
                [0, 1],
                [25, 0]
              )}px)`,
              background: 'rgba(17, 24, 39, 0.94)',
              padding: '14px 30px',
              borderRadius: 20,
              border: '1.5px solid rgba(245, 158, 11, 0.35)',
              boxShadow: '0 12px 32px rgba(0, 0, 0, 0.65)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              maxWidth: 900,
            }}
          >
            <span style={{fontSize: 34}}>🎯</span>
            <span
              style={{
                fontSize: 34,
                fontWeight: 700,
                color: '#F3F4F6',
                textAlign: 'center',
              }}
            >
              Só para apresentar seu produto?
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
