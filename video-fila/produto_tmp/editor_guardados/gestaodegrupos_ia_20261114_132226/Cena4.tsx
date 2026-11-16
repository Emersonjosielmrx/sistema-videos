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

  // Continuous push-in on background across all 119 frames
  const bgScale = interpolate(frame, [0, 119], [1.05, 1.20], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const logoSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.6},
  });

  const titleSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  const subtitleSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  const buttonSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, mass: 0.7},
  });

  const handleSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Continuous live microanimations retaining attention until the final cut:
  // 1. Slow continuous zoom + float on the avatar logo
  const logoSlowZoom = interpolate(frame, [0, 119], [1.0, 1.10]);
  const logoFloat = Math.sin(frame * 0.1) * 5;

  // 2. Smooth continuous CTA button pulse (1.0 -> 1.04)
  const buttonPulse = 1.0 + Math.sin(frame * 0.22) * 0.04;

  // 3. Ambient ring pulse
  const ringScale = 1.0 + Math.sin(frame * 0.1) * 0.06;

  // 4. Continuous linear sweep shimmer across the CTA button
  const shimmerPos = interpolate(frame, [0, 118], [-200, 950]);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Blurred Photo Background with Continuous Push-in */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(30px)',
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

      {/* Deep Dark Slate / Teal Gradient Veil */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 40%, rgba(20, 184, 166, 0.25) 0%, rgba(17, 24, 39, 0.94) 60%, rgba(15, 23, 42, 0.98) 100%)',
        }}
      />

      {/* Decorative ambient glowing ring with continuous pulse */}
      <div
        style={{
          position: 'absolute',
          top: 380,
          left: '50%',
          width: 520,
          height: 520,
          transform: `translate(-50%, -50%) scale(${ringScale})`,
          borderRadius: '50%',
          border: '1.5px solid rgba(20, 184, 166, 0.25)',
          boxShadow: '0 0 90px rgba(20, 184, 166, 0.2)',
          pointerEvents: 'none',
        }}
      />

      {/* Main Content Area (Safely centered in upper-middle zone, ending well above y=1500) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 60px',
          transform: 'translateY(-150px)',
          zIndex: 10,
        }}
      >
        {/* Floating Logo / Avatar with continuous slow zoom */}
        <div
          style={{
            opacity: logoSpring,
            transform: `scale(${logoSpring * logoSlowZoom}) translateY(${logoFloat}px)`,
            marginBottom: 24,
          }}
        >
          <div
            style={{
              width: 124,
              height: 124,
              borderRadius: 36,
              backgroundColor: '#14B8A6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow:
                '0 0 50px rgba(20, 184, 166, 0.65), 0 15px 30px rgba(0, 0, 0, 0.5)',
              fontSize: 62,
              color: '#FFFFFF',
            }}
          >
            🤖
          </div>
        </div>

        {/* Brand Name */}
        <div
          style={{
            opacity: titleSpring,
            transform: `translateY(${interpolate(titleSpring, [0, 1], [20, 0])}px)`,
            fontSize: 56,
            fontWeight: 900,
            color: '#FFFFFF',
            letterSpacing: -1,
            textAlign: 'center',
            textShadow: '0 4px 20px rgba(0, 0, 0, 0.8)',
            marginBottom: 14,
          }}
        >
          Gestão de Grupos IA
        </div>

        {/* Value Proposition */}
        <div
          style={{
            opacity: subtitleSpring,
            transform: `translateY(${interpolate(subtitleSpring, [0, 1], [15, 0])}px)`,
            fontSize: 38,
            fontWeight: 800,
            color: '#FFFFFF',
            textAlign: 'center',
            textWrap: 'balance',
            lineHeight: 1.3,
            maxWidth: 860,
            textShadow: '0 2px 14px rgba(0, 0, 0, 0.9)',
            marginBottom: 44,
          }}
        >
          Seus grupos de WhatsApp no automático
        </div>

        {/* Mega CTA Button (Continuous smooth pulse + shimmer pass) */}
        <div
          style={{
            opacity: buttonSpring,
            transform: `scale(${buttonSpring * buttonPulse})`,
            marginBottom: 28,
            position: 'relative',
          }}
        >
          <div
            style={{
              width: 820,
              height: 110,
              borderRadius: 999,
              background: 'linear-gradient(90deg, #14B8A6 0%, #0D9488 100%)',
              boxShadow:
                '0 0 50px rgba(20, 184, 166, 0.6), 0 15px 35px rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              color: '#FFFFFF',
              fontSize: 44,
              fontWeight: 900,
              letterSpacing: 2,
              textTransform: 'uppercase',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            {/* Shimmer light bar continuously sweeping across button */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 90,
                transform: 'skewX(-25deg)',
                background:
                  'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.5) 50%, rgba(255,255,255,0) 100%)',
                left: shimmerPos,
              }}
            />
            <span>CHAME NO DIRECT</span>
            <span style={{fontSize: 38}}>➔</span>
          </div>
        </div>

        {/* Social Handle (enters together with logo & button, safe above y=1500) */}
        <div
          style={{
            opacity: handleSpring,
            transform: `translateY(${interpolate(handleSpring, [0, 1], [15, 0])}px)`,
            padding: '14px 34px',
            borderRadius: 999,
            backgroundColor: 'rgba(255, 255, 255, 0.12)',
            border: '1.5px solid rgba(255, 255, 255, 0.25)',
            backdropFilter: 'blur(12px)',
            color: '#F1F5F9',
            fontSize: 38,
            fontWeight: 800,
            letterSpacing: 0.5,
          }}
        >
          @gestaodegrupos.ia
        </div>
      </div>
    </div>
  );
};
