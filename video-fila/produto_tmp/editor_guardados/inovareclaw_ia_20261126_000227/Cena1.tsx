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

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const time = frame / fps;

  // Câmera contínua com push-in de 1.02 a 1.08 (movimento contínuo ≥ 4%)
  const videoScale = interpolate(frame, [0, 250], [1.02, 1.08], {
    extrapolateRight: 'clamp',
  });
  const videoTranslateY = interpolate(frame, [0, 250], [0, -10], {
    extrapolateRight: 'clamp',
  });

  // Microdinâmica constante
  const pulseScale = 1 + Math.sin(frame / 12) * 0.012;

  // Entrada do badge de rótulo (frame 0)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada da 1ª parte: "Muito dono de negócio quer usar IA" (7.086s - 6.24s = 0.846s = frame ~25)
  const part1Spring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 13, stiffness: 125},
  });

  // Entrada da 2ª parte: "mas trava na ideia de que precisa programar" (10.966s - 6.24s = 4.726s = frame ~142)
  const part2Spring = spring({
    frame: frame - 142,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const isPart2 = frame >= 142;

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13', overflow: 'hidden'}}>
      {/* Vídeo do apresentador em tela cheia com push-in */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: 'center 40%',
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
        {/* Vinheta superior e inferior para contraste e proteção do texto */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(11, 13, 19, 0.78) 0%, rgba(11, 13, 19, 0) 30%, rgba(11, 13, 19, 0) 70%, rgba(11, 13, 19, 0.88) 100%)',
            pointerEvents: 'none',
          }}
        />
      </AbsoluteFill>

      {/* Faixa superior estritamente na Safe Zone (y 160 a 420), livre da cabeça do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 70,
          right: 90,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
        }}
      >
        {/* Badge do Rótulo "01 • O PROBLEMA" */}
        <div
          style={{
            opacity: interpolate(badgeSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(badgeSpring, [0, 1], [-15, 0])}px) scale(${pulseScale})`,
            background: 'rgba(11, 13, 19, 0.94)',
            border: '2px solid rgba(124, 58, 237, 0.65)',
            borderRadius: 999,
            padding: '8px 24px',
            boxShadow: '0 6px 20px rgba(124, 58, 237, 0.3)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: 6,
              background: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#F87171',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            01 • O Problema
          </span>
        </div>

        {/* Card Dinâmico no topo com box protetor escuro opaco ≥ 85% */}
        {!isPart2 ? (
          <div
            style={{
              width: '100%',
              opacity: interpolate(part1Spring, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(part1Spring, [0, 1], [25, 0])}px)`,
              background: 'rgba(11, 13, 19, 0.92)',
              borderRadius: 24,
              border: '2px solid rgba(255, 255, 255, 0.12)',
              padding: '20px 28px',
              boxShadow: '0 12px 35px rgba(0, 0, 0, 0.65)',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
            }}
          >
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 26,
                background: 'rgba(124, 58, 237, 0.25)',
                border: '1.5px solid #7C3AED',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
                flexShrink: 0,
              }}
            >
              🏢
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.25,
                textWrap: 'balance',
              }}
            >
              Quer usar IA no seu negócio...
            </div>
          </div>
        ) : (
          <div
            style={{
              width: '100%',
              opacity: interpolate(part2Spring, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(part2Spring, [0, 1], [25, 0])}px)`,
              background: 'rgba(11, 13, 19, 0.92)',
              borderRadius: 24,
              border: '2px solid rgba(239, 68, 68, 0.5)',
              padding: '20px 28px',
              boxShadow: '0 12px 35px rgba(239, 68, 68, 0.2)',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
            }}
          >
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 26,
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1.5px solid #EF4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
                flexShrink: 0,
              }}
            >
              ⚠️
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <div
                style={{
                  fontFamily,
                  fontSize: 42,
                  fontWeight: 900,
                  color: '#FECACA',
                  lineHeight: 1.2,
                  textWrap: 'balance',
                }}
              >
                ...mas trava na ideia de saber programar!
              </div>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
