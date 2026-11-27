import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Scene4_CartaoFinal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background camera push-in
  const bgScale = interpolate(frame, [0, 119], [1.06, 1.22], {
    extrapolateRight: 'clamp',
  });

  // Continuous slow zoom-in on the entire card content to eliminate static appearance (0.96 to 1.07)
  const cardZoom = interpolate(frame, [0, 119], [0.96, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const cardSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const btnSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Continuous active scale pulse on the logo robot icon (breathing dynamics)
  const logoPulse = 1.0 + Math.sin(frame * 0.16) * 0.07;
  const logoGlowSpread = 25 + Math.sin(frame * 0.16) * 15;

  // Dynamic button scale bounce (heartbeat pulse) & micro-floating motion
  const btnBounce = 1.0 + Math.sin(frame * 0.20) * 0.045;
  const arrowX = Math.sin(frame * 0.25) * 6;
  const floatY = Math.sin(frame * 0.08) * 6;
  const glowX = Math.sin(frame * 0.07) * 40;
  const glowY = Math.cos(frame * 0.06) * 30;

  // Vivid cyclic shimmer light sweep crossing the CTA button every 28 frames
  const shimmerPos = interpolate(frame % 28, [0, 28], [-60, 160]);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
      }}
    >
      {/* Blurred background with continuous zoom */}
      <div
        style={{
          position: 'absolute',
          inset: -20,
          transform: `scale(${bgScale})`,
          filter: 'blur(20px)',
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
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(11, 14, 23, 0.88)',
          }}
        />
      </div>

      {/* Floating brand ambient glow with active motion */}
      <div
        style={{
          position: 'absolute',
          top: 380 + glowY,
          left: 180 + glowX,
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: 'rgba(167, 139, 250, 0.28)',
          filter: 'blur(100px)',
          pointerEvents: 'none',
        }}
      />

      {/* Central Content Container: Perfectly centered vertically in Safe Zone (y=320 to 1230), leaving balanced breathing room */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: 65,
          right: 65,
          transform: `scale(${cardZoom}) translateY(${floatY}px)`,
          transformOrigin: '50% 50%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 46,
          zIndex: 10,
        }}
      >
        {/* Category Pill */}
        <div
          style={{
            opacity: logoSpring,
            transform: `translateY(${(1 - logoSpring) * -20}px)`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 28px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            border: '1.5px solid rgba(167, 139, 250, 0.4)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span style={{fontSize: 24}}>⚡</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#DDD6FE',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Automação para sua loja
          </span>
        </div>

        {/* Brand Icon + Name with continuous breathing scale pulse */}
        <div
          style={{
            opacity: logoSpring,
            transform: `scale(${0.9 + logoSpring * 0.1}) scale(${logoPulse})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <div
            style={{
              width: 130,
              height: 130,
              borderRadius: 36,
              backgroundColor: '#A78BFA',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 70,
              color: '#121216',
              boxShadow: `0 16px 40px rgba(167, 139, 250, 0.6), 0 0 ${logoGlowSpread}px rgba(167, 139, 250, 0.5)`,
            }}
          >
            🤖
          </div>
          <div
            style={{
              fontSize: 88,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -1,
              textShadow: '0 8px 30px rgba(167, 139, 250, 0.45)',
            }}
          >
            Vitrine IA
          </div>
        </div>

        {/* Value Proposition Card */}
        <div
          style={{
            opacity: cardSpring,
            transform: `translateY(${(1 - cardSpring) * 25}px)`,
            width: '100%',
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            border: '1.5px solid rgba(167, 139, 250, 0.35)',
            borderRadius: 28,
            padding: '36px 40px',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
            textAlign: 'center',
            boxShadow: '0 24px 60px rgba(0, 0, 0, 0.75)',
          }}
        >
          <div
            style={{
              fontSize: 50,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.25,
              textWrap: 'balance',
            }}
          >
            Bot com todo o conhecimento da sua loja.
          </div>
          <div
            style={{
              fontSize: 44,
              fontWeight: 800,
              color: '#A78BFA',
              lineHeight: 1.2,
            }}
          >
            Atende, recomenda e vende.
          </div>
        </div>

        {/* CTA Button (scale bounce cíclico + continuous vivid shimmer sweep) */}
        <div
          style={{
            opacity: btnSpring,
            transform: `scale(${btnBounce})`,
            width: '100%',
            position: 'relative',
            overflow: 'hidden',
            backgroundColor: '#A78BFA',
            borderRadius: 24,
            padding: '28px 40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            boxShadow:
              '0 20px 50px rgba(167, 139, 250, 0.65), 0 0 35px rgba(167, 139, 250, 0.5)',
          }}
        >
          {/* Shimmer light bar passing across from left to right */}
          <div
            style={{
              position: 'absolute',
              top: -20,
              bottom: -20,
              left: `${shimmerPos}%`,
              width: '45%',
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.75) 50%, transparent 100%)',
              transform: 'skewX(-25deg)',
              boxShadow: '0 0 25px rgba(255, 255, 255, 0.8)',
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              fontSize: 52,
              fontWeight: 900,
              color: '#121216',
              textTransform: 'uppercase',
              letterSpacing: 1,
            }}
          >
            Chame no direct
          </span>
          <span
            style={{
              fontSize: 44,
              color: '#121216',
              fontWeight: 900,
              transform: `translateX(${arrowX}px)`,
              display: 'inline-block',
            }}
          >
            ➜
          </span>
        </div>

        {/* Official Account Handle (Visível e destacado) */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            backgroundColor: 'rgba(30, 41, 59, 0.94)',
            border: '1.5px solid rgba(255, 255, 255, 0.16)',
            borderRadius: 999,
            padding: '16px 36px',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span style={{fontSize: 32}}>📸</span>
          <span
            style={{
              fontSize: 42,
              fontWeight: 800,
              color: '#F8FAFC',
              letterSpacing: 0.5,
            }}
          >
            @vitrineia_inovare
          </span>
        </div>
      </div>
    </div>
  );
};
