import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena4CartaoProps {
  fontFamily: string;
  marca: string;
  arroba: string;
  titulo: string;
}

export const Cena4Cartao: React.FC<Cena4CartaoProps> = ({
  fontFamily,
  marca,
  arroba,
  titulo,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous background push & pan
  const bgScale = interpolate(frame, [0, 120], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 120], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Entrance spring for card elements
  const mainEntrance = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Continuous CTA button pulse (1.00 to 1.07) until the very last frame
  const buttonPulse = 1.035 + Math.sin(frame / 5) * 0.035;

  // Shimmer effect across the button
  const shimmerPos = interpolate(frame % 45, [0, 30], [-100, 200], {
    extrapolateRight: 'clamp',
  });

  // Subtle floating motion
  const floatY = Math.sin(frame / 10) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#111827',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Background Image with motion */}
      <img
        src={staticFile('img_4.jpg')}
        alt=""
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          filter: 'blur(16px)',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
        }}
      />

      {/* Dark Slate Overlay with radial vignette */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 40%, rgba(17, 24, 39, 0.85) 0%, rgba(10, 14, 23, 0.96) 85%)',
        }}
      />

      {/* Ambient glowing orb in brand turquoise */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: '50%',
          transform: 'translateX(-50%)',
          width: 600,
          height: 600,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(78, 205, 196, 0.22) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* Safe Zone Content (Evenly distributed between y=190 and y=1440) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 60,
          right: 60,
          bottom: 480,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 32,
          opacity: mainEntrance,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Brand Header */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14,
          }}
        >
          {/* Logo Badge */}
          <div
            style={{
              width: 86,
              height: 86,
              borderRadius: 26,
              backgroundColor: 'rgba(78, 205, 196, 0.16)',
              border: '3px solid #4ECDC4',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 30px rgba(78, 205, 196, 0.4)',
            }}
          >
            <span style={{fontSize: 48}}>🤖</span>
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: 74,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -1,
              textAlign: 'center',
              textShadow: '0 4px 20px rgba(0, 0, 0, 0.8)',
            }}
          >
            {marca}
          </h1>

          <span
            style={{
              fontSize: 34,
              fontWeight: 700,
              color: '#94A3B8',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            Automação de Vendas no WhatsApp
          </span>
        </div>

        {/* Value Proposition Card */}
        <div
          style={{
            width: '100%',
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(78, 205, 196, 0.35)',
            borderRadius: 28,
            padding: '32px 36px',
            boxShadow: '0 16px 40px rgba(0, 0, 0, 0.6)',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
          }}
        >
          <div
            style={{
              fontSize: 42,
              fontWeight: 800,
              color: '#FFFFFF',
              textAlign: 'center',
              lineHeight: 1.25,
              textWrap: 'balance',
            }}
          >
            {titulo}
          </div>

          <div
            style={{
              width: '100%',
              height: 2,
              backgroundColor: 'rgba(255, 255, 255, 0.12)',
            }}
          />

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 34, color: '#4ECDC4'}}>✓</span>
              <span style={{fontSize: 34, fontWeight: 700, color: '#F1F5F9'}}>
                Recupera leads inativos automaticamente
              </span>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 34, color: '#4ECDC4'}}>✓</span>
              <span style={{fontSize: 34, fontWeight: 700, color: '#4ECDC4'}}>
                A partir de R$ 199 • A IA nunca desiste
              </span>
            </div>
          </div>
        </div>

        {/* CTA Area (Button + Handle) */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 20,
            marginTop: 8,
          }}
        >
          {/* Main Pulsing CTA Button */}
          <div
            style={{
              width: '100%',
              height: 120,
              backgroundColor: '#4ECDC4',
              borderRadius: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${buttonPulse})`,
              boxShadow:
                '0 16px 44px rgba(78, 205, 196, 0.45), 0 0 20px rgba(78, 205, 196, 0.3)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer light sweep */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 80,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent)',
                transform: `translateX(${shimmerPos}%) skewX(-20deg)`,
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontSize: 52,
                fontWeight: 900,
                color: '#111827',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              Chame no Direct
            </span>
          </div>

          {/* Official Handle (Displayed from frame 0 of final card) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 34px',
              borderRadius: 24,
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '2px solid rgba(255, 255, 255, 0.22)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
            }}
          >
            <span style={{fontSize: 34}}>💬</span>
            <span
              style={{
                fontSize: 40,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1,
              }}
            >
              {arroba}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
