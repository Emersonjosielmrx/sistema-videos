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

  // Background smooth push-in
  const bgScale = interpolate(frame, [0, 119], [1.06, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Logo entrance
  const logoSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  // Tagline entrance
  const taglineSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  // Feature badge entrance
  const featureSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  // CTA Button entrance and pulse
  const buttonSpring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 10, mass: 0.4},
  });
  const buttonPulse = 1 + 0.035 * Math.sin(frame * 0.16);

  // Shimmer offset across button
  const shimmerPos = interpolate(frame % 50, [0, 50], [-200, 900]);

  // Handle entrance
  const handleSpring = spring({
    frame: frame - 30,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Background with blur and slow push-in */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(16px)',
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

      {/* Dark overlay with brand tint */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 45%, rgba(31,41,55,0.85) 0%, rgba(15,23,42,0.95) 100%)',
        }}
      />

      {/* Subtle warm amber ambient glow behind button */}
      <div
        style={{
          position: 'absolute',
          top: 900,
          left: 200,
          width: 680,
          height: 300,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(245,158,11,0.25) 0%, rgba(245,158,11,0) 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* Brand Header (y=260) */}
      <div
        style={{
          position: 'absolute',
          top: 260,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
          opacity: Math.min(1, Math.max(0, logoSpring)),
          transform: `scale(${0.9 + 0.1 * Math.min(1, Math.max(0, logoSpring))})`,
        }}
      >
        {/* Logo Icon */}
        <div
          style={{
            width: 110,
            height: 110,
            borderRadius: 32,
            background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow:
              '0 12px 35px rgba(245, 158, 11, 0.5), 0 0 25px rgba(245, 158, 11, 0.3)',
          }}
        >
          <span style={{fontSize: 56}}>📅</span>
        </div>

        {/* Brand Name */}
        <h1
          style={{
            margin: 0,
            fontSize: 64,
            fontWeight: 900,
            color: '#FFFFFF',
            letterSpacing: '3px',
            textTransform: 'uppercase',
            textShadow: '0 4px 20px rgba(0,0,0,0.9)',
          }}
        >
          Inovare Agenda
        </h1>
      </div>

      {/* Tagline (y=530) */}
      <div
        style={{
          position: 'absolute',
          top: 530,
          left: 60,
          right: 60,
          textAlign: 'center',
          opacity: Math.min(1, Math.max(0, taglineSpring)),
          transform: `translateY(${(1 - Math.min(1, Math.max(0, taglineSpring))) * 20}px)`,
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: 42,
            fontWeight: 700,
            color: '#E5E7EB',
            lineHeight: 1.35,
            textShadow: '0 4px 16px rgba(0,0,0,0.95)',
            textWrap: 'balance',
          }}
        >
          Agendamentos automáticos com inteligência artificial no seu WhatsApp
        </p>
      </div>

      {/* Feature pill (y=710) */}
      <div
        style={{
          position: 'absolute',
          top: 710,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.min(1, Math.max(0, featureSpring)),
          transform: `scale(${0.92 + 0.08 * Math.min(1, Math.max(0, featureSpring))})`,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 24,
            background: 'rgba(31, 41, 55, 0.90)',
            border: '2px solid rgba(245, 158, 11, 0.65)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
          }}
        >
          <span style={{fontSize: 32}}>⚡</span>
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FCD34D',
              letterSpacing: '0.5px',
            }}
          >
            Trabalha 24h a partir de R$ 199
          </span>
        </div>
      </div>

      {/* Giant Pulsing Action Button (y=920) */}
      <div
        style={{
          position: 'absolute',
          top: 920,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.min(1, Math.max(0, buttonSpring)),
          transform: `scale(${buttonPulse * (0.9 + 0.1 * Math.min(1, Math.max(0, buttonSpring)))})`,
        }}
      >
        <div
          style={{
            position: 'relative',
            width: 860,
            height: 120,
            borderRadius: 60,
            background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
            boxShadow:
              '0 16px 45px rgba(245, 158, 11, 0.55), 0 0 30px rgba(245, 158, 11, 0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18,
            overflow: 'hidden',
          }}
        >
          {/* Shimmer light reflection effect */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: shimmerPos,
              width: 160,
              height: '100%',
              background:
                'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.45) 50%, rgba(255,255,255,0) 100%)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />

          <span style={{fontSize: 44}}>💬</span>
          <span
            style={{
              fontSize: 50,
              fontWeight: 900,
              color: '#121216',
              letterSpacing: '2px',
              textTransform: 'uppercase',
            }}
          >
            Chame no Direct
          </span>
          <span style={{fontSize: 44, color: '#121216', fontWeight: 900}}>➔</span>
        </div>
      </div>

      {/* Instagram Handle Badge (y=1160) */}
      <div
        style={{
          position: 'absolute',
          top: 1160,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.min(1, Math.max(0, handleSpring)),
          transform: `scale(${0.92 + 0.08 * Math.min(1, Math.max(0, handleSpring))})`,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '14px 32px',
            borderRadius: 30,
            background: 'rgba(31, 41, 55, 0.88)',
            border: '2px solid rgba(255, 255, 255, 0.25)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
          }}
        >
          {/* Instagram SVG icon */}
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
            <rect
              x="2"
              y="2"
              width="20"
              height="20"
              rx="6"
              stroke="#F59E0B"
              strokeWidth="2.5"
            />
            <circle cx="12" cy="12" r="4.5" stroke="#F59E0B" strokeWidth="2.5" />
            <circle cx="17.5" cy="6.5" r="1.5" fill="#F59E0B" />
          </svg>
          <span
            style={{
              fontSize: 44,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '1px',
            }}
          >
            @inovareagenda
          </span>
        </div>
      </div>
    </div>
  );
};
