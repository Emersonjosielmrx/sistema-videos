import React from 'react';
import {
  AbsoluteFill,
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

export const Cena4Cartao: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous subtle zoom on blurred background
  const bgScale = interpolate(frame, [0, 120], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Entrance spring animations
  const brandSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const subtitleSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const badgeSpring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const buttonSpring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const handleSpring = spring({
    frame: frame - 36,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Continuous pulsating scale for CTA button (scale 1.0 to 1.06)
  const buttonPulse =
    1 + 0.04 * Math.sin(((frame - 28) / fps) * Math.PI * 2 * 1.5);
  const activeScale = frame > 28 ? buttonSpring * buttonPulse : buttonSpring;

  // Shimmer effect across the CTA button
  const shimmerPos = interpolate(frame % 45, [0, 45], [-100, 200]);

  // Floating micro-motion
  const floatY = Math.sin(frame / 12) * 5;

  // Pulsing brand aura in center
  const glowPulse = 0.22 + 0.08 * Math.sin(((frame) / fps) * Math.PI * 2);

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', overflow: 'hidden'}}>
      {/* Background Image with blur and deep brand overlay */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(10px)',
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
            background:
              'linear-gradient(180deg, rgba(17,24,39,0.86) 0%, rgba(17,24,39,0.74) 50%, rgba(10,14,24,0.92) 100%)',
          }}
        />
      </div>

      {/* Subtle brand glow in the center */}
      <div
        style={{
          position: 'absolute',
          top: '35%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 650,
          height: 650,
          borderRadius: '50%',
          background: `radial-gradient(circle, rgba(78,205,196,${glowPulse}) 0%, transparent 70%)`,
          pointerEvents: 'none',
        }}
      />

      {/* Main Container - Strictly within Safe Zone y=150 to y=1580 */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          bottom: 240,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Brand Icon & Name */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            transform: `scale(${brandSpring})`,
            opacity: brandSpring,
            marginBottom: 28,
          }}
        >
          <div
            style={{
              width: 110,
              height: 110,
              borderRadius: 32,
              backgroundColor: '#4ECDC4',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 12px 35px rgba(78, 205, 196, 0.45)',
              fontSize: 56,
            }}
          >
            ⚡
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 66,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-1px',
              textTransform: 'uppercase',
              textShadow: '0 4px 25px rgba(0,0,0,0.8)',
            }}
          >
            Follow-up IA
          </div>
        </div>

        {/* Core Value Proposition (from facts) */}
        <div
          style={{
            maxWidth: 880,
            textAlign: 'center',
            marginBottom: 36,
            transform: `scale(${subtitleSpring})`,
            opacity: subtitleSpring,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 42,
              fontWeight: 700,
              color: '#E2E8F0',
              lineHeight: 1.35,
              textWrap: 'balance',
            }}
          >
            Recupere leads inativos e venda no WhatsApp no piloto automático.
          </div>
        </div>

        {/* Fact Card: Pricing & Value */}
        <div
          style={{
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
            marginBottom: 60,
          }}
        >
          <div
            style={{
              padding: '16px 32px',
              backgroundColor: 'rgba(255, 255, 255, 0.08)',
              border: '2px solid rgba(78, 205, 196, 0.4)',
              borderRadius: 24,
              backdropFilter: 'blur(12px)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{fontSize: 32}}>💎</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#4ECDC4',
              }}
            >
              Planos a partir de R$ 199
            </span>
          </div>
        </div>

        {/* Pulsating CTA Button - Exact match to spoken call: "Chame no direct" */}
        <div
          style={{
            transform: `scale(${activeScale})`,
            opacity: buttonSpring,
            marginBottom: 36,
            width: '100%',
            maxWidth: 780,
          }}
        >
          <div
            style={{
              position: 'relative',
              backgroundColor: '#4ECDC4',
              borderRadius: 28,
              padding: '28px 40px',
              textAlign: 'center',
              boxShadow: '0 16px 45px rgba(78, 205, 196, 0.4)',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer light reflection */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 80,
                left: `${shimmerPos}%`,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#121216',
                textTransform: 'uppercase',
                letterSpacing: '1px',
              }}
            >
              Chame no Direct
            </span>
          </div>
        </div>

        {/* Social Handle @followupia.ia */}
        <div
          style={{
            transform: `scale(${handleSpring})`,
            opacity: handleSpring,
          }}
        >
          <div
            style={{
              padding: '12px 28px',
              backgroundColor: 'rgba(17, 24, 39, 0.75)',
              border: '1.5px solid rgba(255, 255, 255, 0.15)',
              borderRadius: 20,
              fontFamily,
              fontSize: 36,
              fontWeight: 800,
              color: '#94A3B8',
              letterSpacing: '0.5px',
            }}
          >
            @followupia.ia
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
