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

export const Cena3Resultado: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Scene fade in / out
  const sceneOpacity = interpolate(
    frame,
    [0, 10, 224, 234],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Gentle push-in camera zoom on the video (scale 1.02 to 1.07)
  const videoScale = interpolate(frame, [0, 234], [1.02, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Top pill entrance
  const pillSpring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.6},
  });

  // Headline 1: "RELACIONAMENTO ATIVO" (speech starts at 21.13s -> frame 29)
  const headline1Spring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Headline 2: "ENVIO AUTOMÁTICO NO WHATSAPP" (speech shifts at 23.43s -> frame 98)
  const isSecondPart = frame >= 98;
  const headline2Spring = spring({
    frame: frame - 98,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Benefit Pill 1: "Rotação de instâncias" (speech at ~23.43s = frame 98)
  const benefit1Spring = spring({
    frame: frame - 98,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 200},
  });

  // Benefit Pill 2: "Mensagens personalizadas" (speech at ~24.89s = frame 142)
  const benefit2Spring = spring({
    frame: frame - 142,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 200},
  });

  // Pulsing green dot
  const greenPulse = 1 + Math.sin(frame / 7) * 0.08;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        opacity: sceneOpacity,
      }}
    >
      {/* Background Video of Presenter behind store counter (hair starts at y=550) */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${videoScale})`,
          transformOrigin: 'center 45%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Top Protective Gradient: guarantees high contrast without darkening presenter */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(to bottom, rgba(17, 24, 39, 0.9) 0%, rgba(17, 24, 39, 0.6) 65%, transparent 100%)',
          pointerEvents: 'none',
          zIndex: 10,
        }}
      />

      {/* Top Header Section (y=190, respiro 40px da barra em y=150; presenter head is at y=550) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 20,
        }}
      >
        {/* Pill Badge */}
        <div
          style={{
            opacity: pillSpring,
            transform: `translateY(${(1 - pillSpring) * -15}px)`,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 26px',
            borderRadius: 999,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '1.5px solid rgba(34, 197, 94, 0.45)',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.6)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#22C55E',
              boxShadow: '0 0 10px #22C55E',
              transform: `scale(${greenPulse})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#86EFAC',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </span>
        </div>

        {/* Dynamic Headline synced with speech */}
        <div style={{height: 56, display: 'flex', alignItems: 'center'}}>
          {!isSecondPart ? (
            <div
              style={{
                opacity: Math.max(0, headline1Spring),
                transform: `translateY(${(1 - headline1Spring) * 15}px)`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 46,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '-0.02em',
                  textShadow: '0 3px 14px rgba(0,0,0,0.95)',
                }}
              >
                Relacionamento Ativo
              </span>
            </div>
          ) : (
            <div
              style={{
                opacity: Math.max(0, headline2Spring),
                transform: `translateY(${(1 - headline2Spring) * 15}px)`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 46,
                  fontWeight: 900,
                  color: '#22C55E',
                  textTransform: 'uppercase',
                  letterSpacing: '-0.02em',
                  textShadow: '0 3px 14px rgba(0,0,0,0.95)',
                }}
              >
                Envio Automático no WhatsApp
              </span>
            </div>
          )}
        </div>

        {/* Floating Feature Pills (from facts) */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: 14,
            marginTop: 4,
          }}
        >
          {frame >= 98 && (
            <div
              style={{
                opacity: Math.max(0, benefit1Spring),
                transform: `scale(${0.9 + benefit1Spring * 0.1})`,
                backgroundColor: 'rgba(17, 24, 39, 0.92)',
                border: '1.5px solid rgba(34, 197, 94, 0.5)',
                padding: '8px 20px',
                borderRadius: 999,
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                boxShadow: '0 4px 18px rgba(0, 0, 0, 0.5)',
              }}
            >
              <span style={{fontSize: 28, color: '#22C55E'}}>✓</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Rotação de instâncias
              </span>
            </div>
          )}

          {frame >= 142 && (
            <div
              style={{
                opacity: Math.max(0, benefit2Spring),
                transform: `scale(${0.9 + benefit2Spring * 0.1})`,
                backgroundColor: 'rgba(17, 24, 39, 0.92)',
                border: '1.5px solid rgba(34, 197, 94, 0.5)',
                padding: '8px 20px',
                borderRadius: 999,
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                boxShadow: '0 4px 18px rgba(0, 0, 0, 0.5)',
              }}
            >
              <span style={{fontSize: 28, color: '#22C55E'}}>✓</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Mensagens personalizadas
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
