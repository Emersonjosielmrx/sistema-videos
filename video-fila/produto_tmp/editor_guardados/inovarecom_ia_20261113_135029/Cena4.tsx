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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous background zoom
  const bgScale = interpolate(frame, [0, 117], [1.04, 1.20], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Staggered entrances
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const badgeSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const phraseSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const buttonSpring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 11, stiffness: 140},
  });

  const handleSpring = spring({
    frame: frame - 13,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Cyclic heartbeat animation on CTA Button (Solves Problem 19: pulsação cíclica heartbeat)
  const cycle = frame % 30;
  const heartbeat =
    cycle < 6
      ? 1.0 + Math.sin((cycle / 6) * Math.PI) * 0.08
      : cycle < 12
      ? 1.0 + Math.sin(((cycle - 6) / 6) * Math.PI) * 0.04
      : 1.0;
  const shadowGlow = 0.4 + Math.sin(frame / 6) * 0.25;

  // Active continuous diagonal sheen beam sweeping smoothly every 30 frames
  const shimmerProgress = (frame % 30) / 30;
  const shimmerX = interpolate(shimmerProgress, [0, 1], [-260, 780]);

  // Floating micro-motion for brand icon
  const logoFloat = Math.sin(frame / 12) * 5;

  // Subtle animated radial center position
  const radialCenterY = 48 + Math.sin(frame / 18) * 6;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#061D0F',
        fontFamily,
      }}
    >
      {/* Background Image with continuous zoom & blur */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(24px)',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Dynamic shifting radial brand veil (Solves Problem 19: gradiente animado sutil) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at 50% ${radialCenterY}%, rgba(10, 84, 44, 0.85) 0%, rgba(6, 36, 18, 0.96) 60%, rgba(3, 16, 7, 0.98) 100%)`,
        }}
      />

      {/* Floating brand energy particles (Solves Problem 19: partículas em movimento contínuo) */}
      {[0, 1, 2, 3, 4, 5].map((k) => {
        const floatX = 140 + ((k * 170) % 800);
        const floatY = 450 + Math.sin(frame / 10 + k * 1.4) * 45;
        const op = 0.18 + 0.12 * Math.cos(frame / 8 + k);
        return (
          <div
            key={k}
            style={{
              position: 'absolute',
              left: floatX,
              top: floatY,
              width: 110,
              height: 110,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(37, 211, 102, 0.35) 0%, transparent 70%)',
              opacity: op,
              pointerEvents: 'none',
            }}
          />
        );
      })}

      {/* Structured Layout Container spanning y=320 to y=1400 (strictly within y=150 to y=1580 safe zone) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Top Block: Logo, Brand Name & Value Proposition (y ≈ 340 to 760) */}
        <div
          style={{
            position: 'absolute',
            top: 340,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 20,
          }}
        >
          {/* Brand Logo & Title */}
          <div
            style={{
              opacity: logoSpring,
              transform: `scale(${0.85 + logoSpring * 0.15}) translateY(${(1 - logoSpring) * 20 + logoFloat}px)`,
              display: 'flex',
              alignItems: 'center',
              gap: 18,
            }}
          >
            <div
              style={{
                width: 76,
                height: 76,
                borderRadius: 22,
                backgroundColor: '#25D366',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 35px rgba(37, 211, 102, 0.65)',
              }}
            >
              <svg
                width="44"
                height="44"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#121216"
                strokeWidth="2.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
              </svg>
            </div>
            <span
              style={{
                fontSize: 78,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textShadow: '0 4px 24px rgba(0,0,0,0.85)',
              }}
            >
              HERMES CALL
            </span>
          </div>

          {/* Value Prop Pill */}
          <div
            style={{
              opacity: badgeSpring,
              transform: `translateY(${(1 - badgeSpring) * 20}px)`,
            }}
          >
            <div
              style={{
                padding: '12px 32px',
                borderRadius: 30,
                backgroundColor: 'rgba(37, 211, 102, 0.18)',
                border: '2px solid rgba(37, 211, 102, 0.65)',
                boxShadow: '0 6px 24px rgba(0, 0, 0, 0.45)',
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#25D366',
                  letterSpacing: 1.5,
                }}
              >
                LIGAÇÕES WHATSAPP COM IA 24H
              </span>
            </div>
          </div>

          {/* 1 phrase describing product */}
          <div
            style={{
              marginTop: 10,
              opacity: phraseSpring,
              transform: `translateY(${(1 - phraseSpring) * 20}px)`,
              maxWidth: 880,
            }}
          >
            <span
              style={{
                fontSize: 40,
                fontWeight: 600,
                color: '#F1F5F9',
                lineHeight: 1.35,
                textShadow: '0 2px 14px rgba(0,0,0,0.8)',
              }}
            >
              Atenda, ligue e venda pelo WhatsApp sem sobrecarregar sua equipe.
            </span>
          </div>
        </div>

        {/* Middle Block: CTA Button with Heartbeat Pulse & Shimmer (y ≈ 1040 to 1160) */}
        <div
          style={{
            position: 'absolute',
            top: 1040,
            opacity: buttonSpring,
            transform: `scale(${buttonSpring * heartbeat}) translateY(${(1 - buttonSpring) * 30}px)`,
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              padding: '28px 72px',
              borderRadius: 60,
              background: 'linear-gradient(135deg, #25D366 0%, #1EBE5D 100%)',
              boxShadow: `0 18px 50px rgba(37, 211, 102, ${shadowGlow}), 0 4px 16px rgba(0,0,0,0.5)`,
              display: 'flex',
              alignItems: 'center',
              gap: 20,
            }}
          >
            <svg
              width="44"
              height="44"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#121216"
              strokeWidth="2.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>

            <span
              style={{
                fontSize: 48,
                fontWeight: 900,
                color: '#121216',
                letterSpacing: 2,
              }}
            >
              CHAME NO DIRECT
            </span>

            {/* Continuous Diagonal Shimmer Beam */}
            <div
              style={{
                position: 'absolute',
                top: -30,
                bottom: -30,
                left: shimmerX,
                width: 90,
                background:
                  'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.75) 50%, rgba(255,255,255,0) 100%)',
                transform: 'skewX(-28deg)',
                pointerEvents: 'none',
                boxShadow: '0 0 20px rgba(255,255,255,0.6)',
              }}
            />
          </div>
        </div>

        {/* Lower Block: Official Instagram Handle @inovarecom.ia (Solves Problem 1: positioned between y=1250 and y=1350) */}
        <div
          style={{
            position: 'absolute',
            top: 1260,
            opacity: handleSpring,
            transform: `translateY(${(1 - handleSpring) * 20}px)`,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '14px 36px',
            borderRadius: 30,
            backgroundColor: 'rgba(8, 38, 18, 0.85)',
            border: '2px solid rgba(37, 211, 102, 0.5)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span
            style={{
              fontSize: 44,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textShadow: '0 3px 12px rgba(0,0,0,0.85)',
            }}
          >
            @inovarecom.ia
          </span>
        </div>
      </div>
    </div>
  );
};
