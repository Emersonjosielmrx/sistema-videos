import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  // Push-in contínuo no vídeo comercial b-roll
  const videoScale = interpolate(frame, [0, durationInFrames], [1.02, 1.1], {
    extrapolateRight: 'clamp',
  });

  // Fade out nos últimos 10 frames
  const opacity = interpolate(
    frame,
    [durationInFrames - 10, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // 1. Badge superior "COMO FUNCIONA" (~frame 5)
  const headerSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. Card 1: "Landing page pronta" (~14.07s / frame 37)
  const card1Spring = spring({
    frame: frame - 37,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // 3. Card 2: "Vídeo de demonstração" (~15.56s / frame 81)
  const card2Spring = spring({
    frame: frame - 81,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // 4. Card 3: "Comunicação alinhada" (~16.90s / frame 122)
  const card3Spring = spring({
    frame: frame - 122,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // 5. Banner Consolidado: "TUDO EM UMA ESTRUTURA SÓ" (~18.42s / frame 167)
  const bannerSpring = spring({
    frame: frame - 167,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Pulso do banner final
  const bannerPulse = Math.sin((frame - 167) / 8) * 0.03;

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
      {/* Vídeo Comercial (Veo) com zoom constante */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Degradê superior de alto contraste para leitura perfeita */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 900,
          background:
            'linear-gradient(180deg, rgba(17, 24, 39, 0.92) 0%, rgba(17, 24, 39, 0.75) 60%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo na Safe Zone (y: 150 a 1580, laterais: 60px) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          pointerEvents: 'none',
        }}
      >
        {/* Header Badge */}
        <div
          style={{
            opacity: headerSpring,
            transform: `scale(${headerSpring})`,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 30,
            background: 'rgba(17, 24, 39, 0.95)',
            border: '1.5px solid rgba(245, 158, 11, 0.5)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
            marginBottom: 36,
          }}
        >
          <span style={{fontSize: 28}}>⚡</span>
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#F59E0B',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            COMO FUNCIONA
          </span>
        </div>

        {/* Pilha de Cards de Entregáveis (Checklist Animado) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            width: '100%',
            maxWidth: 880,
          }}
        >
          {/* Card 1: Landing page pronta */}
          {frame >= 37 && (
            <div
              style={{
                opacity: card1Spring,
                transform: `translateX(${interpolate(card1Spring, [0, 1], [-40, 0])}px) scale(${interpolate(
                  card1Spring,
                  [0, 1],
                  [0.9, 1]
                )})`,
                background: 'rgba(17, 24, 39, 0.95)',
                border: '1.5px solid rgba(245, 158, 11, 0.35)',
                borderRadius: 20,
                padding: '18px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 10px 28px rgba(0, 0, 0, 0.65)',
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  backgroundColor: '#10B981',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontSize: 26,
                  fontWeight: 900,
                  boxShadow: '0 0 14px rgba(16, 185, 129, 0.5)',
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <span
                style={{
                  fontSize: 40,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Landing Page Pronta
              </span>
            </div>
          )}

          {/* Card 2: Vídeo de demonstração */}
          {frame >= 81 && (
            <div
              style={{
                opacity: card2Spring,
                transform: `translateX(${interpolate(card2Spring, [0, 1], [40, 0])}px) scale(${interpolate(
                  card2Spring,
                  [0, 1],
                  [0.9, 1]
                )})`,
                background: 'rgba(17, 24, 39, 0.95)',
                border: '1.5px solid rgba(245, 158, 11, 0.35)',
                borderRadius: 20,
                padding: '18px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 10px 28px rgba(0, 0, 0, 0.65)',
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  backgroundColor: '#10B981',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontSize: 26,
                  fontWeight: 900,
                  boxShadow: '0 0 14px rgba(16, 185, 129, 0.5)',
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <span
                style={{
                  fontSize: 40,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Vídeo de Demonstração
              </span>
            </div>
          )}

          {/* Card 3: Comunicação */}
          {frame >= 122 && (
            <div
              style={{
                opacity: card3Spring,
                transform: `translateX(${interpolate(card3Spring, [0, 1], [-40, 0])}px) scale(${interpolate(
                  card3Spring,
                  [0, 1],
                  [0.9, 1]
                )})`,
                background: 'rgba(17, 24, 39, 0.95)',
                border: '1.5px solid rgba(245, 158, 11, 0.35)',
                borderRadius: 20,
                padding: '18px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 10px 28px rgba(0, 0, 0, 0.65)',
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  backgroundColor: '#10B981',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontSize: 26,
                  fontWeight: 900,
                  boxShadow: '0 0 14px rgba(16, 185, 129, 0.5)',
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <span
                style={{
                  fontSize: 40,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Comunicação Alinhada
              </span>
            </div>
          )}

          {/* Banner de Consolidação: Tudo em uma estrutura só */}
          {frame >= 167 && (
            <div
              style={{
                marginTop: 10,
                opacity: bannerSpring,
                transform: `scale(${interpolate(bannerSpring, [0, 1], [0.85, 1]) + (frame > 175 ? bannerPulse : 0)})`,
                background: '#F59E0B',
                borderRadius: 22,
                padding: '18px 32px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 14,
                boxShadow: '0 14px 40px rgba(245, 158, 11, 0.5)',
              }}
            >
              <span style={{fontSize: 34}}>💎</span>
              <span
                style={{
                  fontSize: 42,
                  fontWeight: 900,
                  color: '#121216',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Tudo em Uma Estrutura Só
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
